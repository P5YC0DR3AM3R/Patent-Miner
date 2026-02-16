#!/usr/bin/env python3
"""Patent discovery utilities for Patent Miner."""

from __future__ import annotations

import copy
import os
import re
import shlex
import time
import warnings
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


DEFAULT_PATENT_SEARCH_CONFIG: Dict[str, Any] = {
    "provider": "patentsview_patentsearch",
    "api_url": "https://search.patentsview.org/api/v1/patent/",
    "api_key_env": "PATENTSVIEW_API_KEY",
    "keywords": ["portable", "sensor"],
    "filing_date_start": "1995-01-01",
    "filing_date_end": "2005-12-31",
    "assignee_type": "individual",
    "num_results": 500,
    "require_likely_expired": True,
    "allow_legacy_scrape_fallback": False,
    "timeout_seconds": 20,
    "max_retries": 3,
    "retry_backoff_seconds": 1.5,
    "per_page": 100,
}


ASSIGNEE_TYPE_CODE_MAP: Dict[str, List[str]] = {
    "individual": ["4", "5", "14", "15"],
    "organization": ["2", "3", "12", "13"],
}


@dataclass
class PatentDiscoveryError(Exception):
    """Typed exception for discovery failures."""

    code: str
    message: str
    diagnostics: Optional[Dict[str, Any]] = None

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"


def _iso_date(value: Optional[str]) -> Optional[date]:
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def parse_legacy_search_query(search_query: str) -> Tuple[Dict[str, Any], List[str]]:
    """Best-effort parser for legacy query strings."""

    parsed: Dict[str, Any] = {
        "keywords": [],
        "filing_date_start": None,
        "filing_date_end": None,
        "assignee_type": None,
        "require_likely_expired": None,
    }
    parse_warnings: List[str] = []

    if not search_query or not isinstance(search_query, str):
        parse_warnings.append("Legacy search_query is empty or invalid.")
        return parsed, parse_warnings

    try:
        tokens = shlex.split(search_query)
    except ValueError:
        tokens = search_query.split()
        parse_warnings.append("Legacy search_query could not be tokenized with shlex; used split().")

    keyword_parts: List[str] = []

    for token in tokens:
        if token.startswith("status:"):
            status_value = token.split(":", 1)[1].strip().lower()
            if status_value == "expired":
                parsed["require_likely_expired"] = True
            else:
                parse_warnings.append(f"Unsupported status filter in legacy query: {token}")
            continue

        if token.startswith("filing_date:"):
            date_range = token.split(":", 1)[1].strip()
            match = re.match(r"^(\d{4})-(\d{4})$", date_range)
            if match:
                parsed["filing_date_start"] = f"{match.group(1)}-01-01"
                parsed["filing_date_end"] = f"{match.group(2)}-12-31"
            else:
                parse_warnings.append(f"Unsupported filing_date format in legacy query: {token}")
            continue

        if token.startswith("assignee_type:"):
            assignee_type = token.split(":", 1)[1].strip().lower()
            if assignee_type in ASSIGNEE_TYPE_CODE_MAP:
                parsed["assignee_type"] = assignee_type
            else:
                parse_warnings.append(f"Unsupported assignee_type in legacy query: {assignee_type}")
            continue

        if ":" in token:
            parse_warnings.append(f"Unrecognized legacy filter token ignored: {token}")
            continue

        clean = token.strip()
        if clean:
            keyword_parts.append(clean)

    if keyword_parts:
        # Preserve quoted phrase behavior by treating each tokenized phrase as one keyword.
        parsed["keywords"] = keyword_parts

    return parsed, parse_warnings


def _resolve_patent_search_config(config: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """Resolve structured config and include best-effort legacy compatibility."""

    resolved = copy.deepcopy(DEFAULT_PATENT_SEARCH_CONFIG)
    warnings_list: List[str] = []

    structured = config.get("patent_search")
    if isinstance(structured, dict):
        resolved.update(structured)

    legacy_query = config.get("search_query")
    if isinstance(legacy_query, str) and legacy_query.strip():
        warnings.warn(
            "CONFIG['search_query'] is deprecated; use CONFIG['patent_search'] structured fields.",
            DeprecationWarning,
            stacklevel=2,
        )
        warnings_list.append(
            "search_query is deprecated; parsed best-effort into patent_search config."
        )
        parsed, parse_warnings = parse_legacy_search_query(legacy_query)
        warnings_list.extend(parse_warnings)

        # Only fill values that were not explicitly set in structured config.
        if "patent_search" not in config:
            resolved.update({k: v for k, v in parsed.items() if v is not None and v != []})
        else:
            if not resolved.get("keywords") and parsed.get("keywords"):
                resolved["keywords"] = parsed["keywords"]
            if not resolved.get("filing_date_start") and parsed.get("filing_date_start"):
                resolved["filing_date_start"] = parsed["filing_date_start"]
            if not resolved.get("filing_date_end") and parsed.get("filing_date_end"):
                resolved["filing_date_end"] = parsed["filing_date_end"]
            if not resolved.get("assignee_type") and parsed.get("assignee_type"):
                resolved["assignee_type"] = parsed["assignee_type"]

    resolved["num_results"] = int(resolved.get("num_results") or 100)
    resolved["timeout_seconds"] = int(resolved.get("timeout_seconds") or 20)
    resolved["max_retries"] = int(resolved.get("max_retries") or 3)
    resolved["retry_backoff_seconds"] = float(resolved.get("retry_backoff_seconds") or 1.5)
    resolved["per_page"] = max(1, min(1000, int(resolved.get("per_page") or 100)))

    keywords = resolved.get("keywords") or []
    if isinstance(keywords, str):
        resolved["keywords"] = [keywords]
    elif isinstance(keywords, list):
        resolved["keywords"] = [str(k).strip() for k in keywords if str(k).strip()]
    else:
        resolved["keywords"] = []

    return resolved, warnings_list


def _base_diagnostics(search_config: Dict[str, Any], warnings_list: Optional[List[str]] = None) -> Dict[str, Any]:
    return {
        "provider": search_config.get("provider", "patentsview_patentsearch"),
        "status": "pending",
        "http_status": None,
        "raw_count": 0,
        "filtered_count": 0,
        "query_summary": {
            "keywords": search_config.get("keywords", []),
            "filing_date_start": search_config.get("filing_date_start"),
            "filing_date_end": search_config.get("filing_date_end"),
            "assignee_type": search_config.get("assignee_type"),
            "num_results": search_config.get("num_results"),
            "require_likely_expired": bool(search_config.get("require_likely_expired", True)),
        },
        "errors": [],
        "next_actions": [],
        "warnings": list(warnings_list or []),
    }


def build_patentsearch_payload(config: Dict[str, Any]) -> Dict[str, Any]:
    """Compile structured config into PatentSearch API request payload."""

    filters: List[Dict[str, Any]] = []

    for keyword in config.get("keywords", []):
        filters.append(
            {
                "_or": [
                    {"_text_all": {"patent_title": keyword}},
                    {"_text_all": {"patent_abstract": keyword}},
                ]
            }
        )

    filing_start = config.get("filing_date_start")
    filing_end = config.get("filing_date_end")
    if filing_start:
        filters.append({"_gte": {"application.filing_date": filing_start}})
    if filing_end:
        filters.append({"_lte": {"application.filing_date": filing_end}})

    assignee_type = (config.get("assignee_type") or "").strip().lower()
    if assignee_type in ASSIGNEE_TYPE_CODE_MAP:
        filters.append({"assignees.assignee_type": ASSIGNEE_TYPE_CODE_MAP[assignee_type]})
    elif assignee_type:
        filters.append({"assignees.assignee_type": [assignee_type]})

    if not filters:
        q: Dict[str, Any] = {"_gte": {"patent_date": "1900-01-01"}}
    elif len(filters) == 1:
        q = filters[0]
    else:
        q = {"_and": filters}

    payload: Dict[str, Any] = {
        "q": q,
        "f": [
            "patent_id",
            "patent_title",
            "patent_abstract",
            "patent_date",
            "patent_type",
            "application.filing_date",
            "assignees.assignee_type",
        ],
        "s": [{"patent_date": "asc"}, {"patent_id": "asc"}],
        "o": {
            "page": 1,
            "per_page": max(1, min(1000, int(config.get("per_page") or 100))),
        },
    }
    return payload


def _extract_response_items(body: Dict[str, Any]) -> List[Dict[str, Any]]:
    if isinstance(body.get("patents"), list):
        return [item for item in body["patents"] if isinstance(item, dict)]

    list_candidates = [
        value
        for key, value in body.items()
        if key not in {"error", "count", "total_hits"} and isinstance(value, list)
    ]
    if len(list_candidates) == 1:
        return [item for item in list_candidates[0] if isinstance(item, dict)]

    raise ValueError("Unable to determine response data key for patent records.")


def fetch_patents_patentsview(config: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Fetch raw patent records from PatentsView PatentSearch API."""

    search_config, warnings_list = _resolve_patent_search_config(config)
    diagnostics = _base_diagnostics(search_config, warnings_list)

    api_key_env = search_config.get("api_key_env") or "PATENTSVIEW_API_KEY"
    api_key = os.getenv(api_key_env)
    if not api_key:
        diagnostics["status"] = "failed"
        diagnostics["errors"].append(f"Missing API key in environment variable: {api_key_env}")
        diagnostics["next_actions"].append(f"Set `{api_key_env}` before running discovery.")
        raise PatentDiscoveryError(
            code="missing_api_key",
            message=f"Environment variable `{api_key_env}` is required.",
            diagnostics=diagnostics,
        )

    payload = build_patentsearch_payload(search_config)
    api_url = search_config.get("api_url") or DEFAULT_PATENT_SEARCH_CONFIG["api_url"]

    requested = int(search_config.get("num_results") or 100)
    per_page = int(payload["o"]["per_page"])
    timeout_seconds = int(search_config.get("timeout_seconds") or 20)
    max_retries = max(1, int(search_config.get("max_retries") or 3))
    backoff_seconds = float(search_config.get("retry_backoff_seconds") or 1.5)

    session = requests.Session()
    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    all_records: List[Dict[str, Any]] = []
    page = 1
    total_hits: Optional[int] = None

    while len(all_records) < requested:
        payload["o"]["page"] = page
        payload["o"]["per_page"] = per_page

        response: Optional[requests.Response] = None
        last_error: Optional[Exception] = None

        for attempt in range(1, max_retries + 1):
            try:
                response = session.post(api_url, headers=headers, json=payload, timeout=timeout_seconds)
                break
            except requests.RequestException as exc:
                last_error = exc
                if attempt == max_retries:
                    diagnostics["status"] = "failed"
                    diagnostics["errors"].append(f"Transport error after {max_retries} attempts: {exc}")
                    diagnostics["next_actions"].append("Validate network access and PatentsView endpoint reachability.")
                    raise PatentDiscoveryError(
                        code="transport_error",
                        message="Failed to reach PatentsView API after retries.",
                        diagnostics=diagnostics,
                    ) from exc
                time.sleep(backoff_seconds * attempt)

        if response is None:
            diagnostics["status"] = "failed"
            diagnostics["errors"].append(f"Unexpected empty response state: {last_error}")
            raise PatentDiscoveryError(
                code="transport_error",
                message="Request did not produce a response.",
                diagnostics=diagnostics,
            )

        diagnostics["http_status"] = response.status_code

        if response.status_code in (401, 403):
            diagnostics["status"] = "failed"
            diagnostics["errors"].append(f"Authentication/authorization failed with HTTP {response.status_code}.")
            diagnostics["next_actions"].append("Verify `X-Api-Key` value and API key activation status.")
            raise PatentDiscoveryError(
                code="auth_failed",
                message="PatentsView API rejected the API key.",
                diagnostics=diagnostics,
            )

        if response.status_code >= 400:
            status_reason = response.headers.get("X-Status-Reason", "")
            diagnostics["status"] = "failed"
            diagnostics["errors"].append(
                f"HTTP {response.status_code} from PatentsView API. {status_reason}".strip()
            )
            diagnostics["next_actions"].append("Review request payload and query fields against PatentSearch API docs.")
            raise PatentDiscoveryError(
                code="transport_error",
                message=f"PatentsView API returned HTTP {response.status_code}.",
                diagnostics=diagnostics,
            )

        try:
            body = response.json()
        except ValueError as exc:
            diagnostics["status"] = "failed"
            diagnostics["errors"].append("Response body was not valid JSON.")
            diagnostics["next_actions"].append("Retry request and inspect raw response text for diagnostics.")
            raise PatentDiscoveryError(
                code="schema_error",
                message="PatentsView response could not be parsed as JSON.",
                diagnostics=diagnostics,
            ) from exc

        if body.get("error"):
            diagnostics["status"] = "failed"
            diagnostics["errors"].append("PatentsView response included error=true.")
            diagnostics["next_actions"].append("Check q/f/s/o payload and key headers.")
            raise PatentDiscoveryError(
                code="schema_error",
                message="PatentsView response signaled API-level error.",
                diagnostics=diagnostics,
            )

        try:
            page_items = _extract_response_items(body)
        except ValueError as exc:
            diagnostics["status"] = "failed"
            diagnostics["errors"].append(str(exc))
            diagnostics["next_actions"].append("Confirm response key for endpoint /api/v1/patent/.")
            raise PatentDiscoveryError(
                code="schema_error",
                message="Could not locate patent array in response.",
                diagnostics=diagnostics,
            ) from exc

        if total_hits is None:
            total_hits_raw = body.get("total_hits")
            if isinstance(total_hits_raw, int):
                total_hits = total_hits_raw

        if not page_items:
            break

        all_records.extend(page_items)

        if len(all_records) >= requested:
            break

        if total_hits is not None and len(all_records) >= total_hits:
            break

        page += 1

    limited = all_records[:requested]
    diagnostics["raw_count"] = len(limited)
    diagnostics["status"] = "ok"
    return limited, diagnostics


def normalize_patent_record(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize PatentsView record into internal shape."""

    patent_number = raw.get("patent_id") or raw.get("patent_number") or ""
    title = raw.get("patent_title") or ""
    abstract = raw.get("patent_abstract") or ""
    patent_date = raw.get("patent_date") or None

    filing_date: Optional[str] = None
    application = raw.get("application")
    if isinstance(application, list) and application:
        first = application[0]
        if isinstance(first, dict):
            filing_date = first.get("filing_date")
    elif isinstance(application, dict):
        filing_date = application.get("filing_date")

    assignee_type: Optional[str] = None
    assignees = raw.get("assignees")
    if isinstance(assignees, list) and assignees:
        first_assignee = assignees[0]
        if isinstance(first_assignee, dict):
            assignee_type = first_assignee.get("assignee_type")

    link = f"https://patents.google.com/patent/{patent_number}" if patent_number else ""

    return {
        "patent_number": patent_number,
        "title": title,
        "abstract": abstract,
        "link": link,
        "patent_date": patent_date,
        "filing_date": filing_date,
        "assignee_type": assignee_type,
        "source_provider": "patentsview_patentsearch",
        "patent_type": raw.get("patent_type"),
    }


def is_likely_expired(record: Dict[str, Any], as_of_date: date) -> bool:
    """Heuristic for likely expiration, based on filing or grant age."""

    filing = _iso_date(record.get("filing_date"))
    grant = _iso_date(record.get("patent_date"))
    patent_type = (record.get("patent_type") or "").lower()

    if filing:
        return (as_of_date - filing).days >= 20 * 365

    # Conservative fallback when filing date is missing.
    if grant:
        if patent_type == "design":
            # Design patents generally expire sooner than utility patents.
            return (as_of_date - grant).days >= 15 * 365
        return (as_of_date - grant).days >= 20 * 365

    return False


def _legacy_scrape_google(query: str, num_results: int) -> List[Dict[str, Any]]:
    """Legacy fallback scraper. Kept only for explicit troubleshooting."""

    url = f"https://patents.google.com/?q={query.replace(' ', '+')}&num={num_results}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    results: List[Dict[str, Any]] = []

    for item in soup.select("search-result-item"):
        title_el = item.select_one("h3, h4")
        title = title_el.get_text(strip=True) if title_el else ""

        abstract_el = item.select_one(".abstract, .description")
        abstract = abstract_el.get_text(strip=True) if abstract_el else ""

        link = ""
        link_el = item.select_one("a[href*='/patent/']")
        if link_el:
            href = link_el.get("href", "")
            link = f"https://patents.google.com{href}" if href.startswith("/") else href

        patent_num = ""
        if link:
            match = re.search(r"/patent/([A-Z]{2}\d+[A-Z]?\d?)", link)
            if match:
                patent_num = match.group(1)

        if title:
            results.append(
                {
                    "patent_number": patent_num,
                    "title": title,
                    "abstract": abstract,
                    "link": link,
                    "patent_date": None,
                    "filing_date": None,
                    "assignee_type": None,
                    "source_provider": "legacy_google_scrape_fallback",
                    "patent_type": None,
                }
            )

    return results[:num_results]


def discover_patents(config: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Discover patents and return normalized records + diagnostics."""

    search_config, warnings_list = _resolve_patent_search_config(config)

    try:
        raw_records, diagnostics = fetch_patents_patentsview(config)
    except PatentDiscoveryError as exc:
        diagnostics = exc.diagnostics or _base_diagnostics(search_config, warnings_list)

        if search_config.get("allow_legacy_scrape_fallback"):
            diagnostics["warnings"].append(
                "Legacy scrape fallback enabled. This path is unsupported and brittle."
            )
            legacy_query = config.get("search_query")
            if not legacy_query:
                legacy_query = " ".join(search_config.get("keywords", [])) or "portable sensor"
            try:
                fallback = _legacy_scrape_google(legacy_query, int(search_config.get("num_results") or 100))
            except Exception as fallback_exc:
                diagnostics["errors"].append(f"Legacy fallback failed: {fallback_exc}")
                diagnostics["status"] = "failed"
                raise PatentDiscoveryError(
                    code=exc.code,
                    message=exc.message,
                    diagnostics=diagnostics,
                ) from fallback_exc

            if fallback:
                diagnostics["provider"] = "legacy_google_scrape_fallback"
                diagnostics["status"] = "fallback"
                diagnostics["raw_count"] = len(fallback)
                diagnostics["filtered_count"] = len(fallback)
                diagnostics["next_actions"].append(
                    "Switch fallback off after troubleshooting and use PatentsView API as primary source."
                )
                return fallback, diagnostics

        raise exc

    normalized = [normalize_patent_record(item) for item in raw_records]

    if search_config.get("require_likely_expired", True):
        today = date.today()
        filtered = [r for r in normalized if is_likely_expired(r, today)]
    else:
        filtered = normalized

    diagnostics["raw_count"] = len(normalized)
    diagnostics["filtered_count"] = len(filtered)

    if not filtered:
        diagnostics["status"] = "failed"
        diagnostics["errors"].append("No patents remained after discovery and expiration filtering.")
        diagnostics["next_actions"].append(
            "Broaden keywords, filing range, or disable `require_likely_expired` for debugging."
        )
        raise PatentDiscoveryError(
            code="zero_results",
            message="No patents found for the configured search.",
            diagnostics=diagnostics,
        )

    diagnostics["status"] = diagnostics.get("status") or "ok"
    return filtered, diagnostics


def save_discovery_diagnostics(output_dir: str, diagnostics: Dict[str, Any], timestamp: str) -> Path:
    """Persist discovery diagnostics to disk."""

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    diagnostics_path = out / f"discovery_diagnostics_{timestamp}.json"
    with open(diagnostics_path, "w", encoding="utf-8") as handle:
        import json

        json.dump(diagnostics, handle, indent=2)
    return diagnostics_path
