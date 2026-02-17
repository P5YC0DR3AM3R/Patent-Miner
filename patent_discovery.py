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

from scoring_utils import clamp, term_coverage, tfidf_cosine_similarity, tokenize_text
from viability_scoring import (
    SCORING_VERSION,
    compute_opportunity_score_v2,
    compute_viability_scorecard,
    expiration_confidence_score,
)

# Load environment variables from .env file
load_dotenv()

RANKING_VERSION = "v2.0.0"

DEFAULT_RETRIEVAL_SCORE_WEIGHTS: Dict[str, float] = {
    "title_exact_match": 0.24,
    "query_coverage": 0.20,
    "semantic_similarity": 0.30,
    "expiration_confidence": 0.16,
    "pass_diversity": 0.10,
}

# Deterministic keyword expansion map used by retrieval v2.
KEYWORD_EXPANSION_MAP: Dict[str, List[str]] = {
    "portable": ["mobile", "handheld", "wearable", "compact"],
    "sensor": ["detector", "monitor", "transducer", "probe"],
    "wireless": ["rf", "radio", "remote", "bluetooth"],
    "vital": ["physiological", "biometric", "health"],
    "water": ["aqueous", "h2o", "liquid"],
    "gas": ["vapor", "fume", "air"],
    "soil": ["agriculture", "crop", "field"],
    "temperature": ["thermal", "heat"],
    "monitor": ["tracking", "diagnostic", "measurement"],
    "device": ["apparatus", "instrument", "system"],
}

DEFAULT_PATENT_SEARCH_CONFIG: Dict[str, Any] = {
    "provider": "patentsview_patentsearch",
    "api_url": "https://search.patentsview.org/api/v1/patent/",
    "api_key_env": "PATENTSVIEW_API_KEY",
    "keywords": ["portable", "sensor"],
    # Broaden filing date range to include older patents (more likely expired)
    "filing_date_start": "1970-01-01",
    "filing_date_end": "2006-12-31",
    "assignee_type": "individual",
    # Increase default result window to surface more candidates
    "num_results": 2000,
    "require_likely_expired": True,
    # Years prior to today to consider a patent "likely expired" (default: 20 years)
    "expired_cutoff_years": 20,
    "allow_legacy_scrape_fallback": False,
    "timeout_seconds": 20,
    "max_retries": 3,
    "retry_backoff_seconds": 1.5,
    "per_page": 200,
    "enable_v2_pipeline": True,
    "retrieval_v2": {
        "enabled": True,
        "max_expanded_keywords": 24,
        "fallback_relax_assignee": True,
        "score_weights": dict(DEFAULT_RETRIEVAL_SCORE_WEIGHTS),
    },
    "viability_v2": {
        "enabled": True,
        "weights": {},
    },
    "scoring_weights": {
        "retrieval": 0.35,
        "viability": 0.45,
        "expiration": 0.20,
    },
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


def _deep_merge_dict(base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge_dict(merged[key], value)
        else:
            merged[key] = value
    return merged


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
        resolved = _deep_merge_dict(resolved, structured)

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

    resolved["num_results"] = max(1, int(resolved.get("num_results") or 100))
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

    retrieval_v2 = resolved.get("retrieval_v2")
    if not isinstance(retrieval_v2, dict):
        retrieval_v2 = {}
    resolved["retrieval_v2"] = _deep_merge_dict(DEFAULT_PATENT_SEARCH_CONFIG["retrieval_v2"], retrieval_v2)

    viability_v2 = resolved.get("viability_v2")
    if not isinstance(viability_v2, dict):
        viability_v2 = {}
    resolved["viability_v2"] = _deep_merge_dict(DEFAULT_PATENT_SEARCH_CONFIG["viability_v2"], viability_v2)

    scoring_weights = resolved.get("scoring_weights")
    if not isinstance(scoring_weights, dict):
        scoring_weights = {}
    resolved["scoring_weights"] = _deep_merge_dict(DEFAULT_PATENT_SEARCH_CONFIG["scoring_weights"], scoring_weights)

    resolved["enable_v2_pipeline"] = bool(
        resolved.get("enable_v2_pipeline", True) and resolved["retrieval_v2"].get("enabled", True)
    )

    return resolved, warnings_list


def _base_diagnostics(search_config: Dict[str, Any], warnings_list: Optional[List[str]] = None) -> Dict[str, Any]:
    return {
        "provider": search_config.get("provider", "patentsview_patentsearch"),
        "status": "pending",
        "http_status": None,
        "raw_count": 0,
        "filtered_count": 0,
        "pass_counts": {},
        "deduped_count": 0,
        "ranking_version": RANKING_VERSION,
        "scoring_version": SCORING_VERSION,
        "query_summary": {
            "keywords": search_config.get("keywords", []),
            "filing_date_start": search_config.get("filing_date_start"),
            "filing_date_end": search_config.get("filing_date_end"),
            "assignee_type": search_config.get("assignee_type"),
            "num_results": search_config.get("num_results"),
            "require_likely_expired": bool(search_config.get("require_likely_expired", True)),
            "enable_v2_pipeline": bool(search_config.get("enable_v2_pipeline", True)),
        },
        "errors": [],
        "next_actions": [],
        "warnings": list(warnings_list or []),
    }


def expand_keywords_for_v2(keywords: List[str], max_expanded_keywords: int = 24) -> List[str]:
    """Expand keyword list with deterministic synonyms for broader recall."""

    expanded: List[str] = []
    seen: set[str] = set()

    def _add(term: str) -> None:
        clean = term.strip().lower()
        if not clean or clean in seen:
            return
        seen.add(clean)
        expanded.append(clean)

    for keyword in keywords:
        base = (keyword or "").strip().lower()
        if not base:
            continue

        _add(base)

        for token in tokenize_text(base):
            _add(token)
            for synonym in KEYWORD_EXPANSION_MAP.get(token, []):
                _add(synonym)

        if len(expanded) >= max_expanded_keywords:
            break

    return expanded[:max_expanded_keywords]


def build_retrieval_passes(search_config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Build retrieval pass definitions for the hybrid semantic+rules strategy."""

    requested = int(search_config.get("num_results") or 100)
    retrieval_cfg = search_config.get("retrieval_v2") or {}
    max_expanded_keywords = int(retrieval_cfg.get("max_expanded_keywords") or 24)

    base_keywords = list(search_config.get("keywords") or [])
    expanded_keywords = expand_keywords_for_v2(base_keywords, max_expanded_keywords=max_expanded_keywords)
    if not expanded_keywords:
        expanded_keywords = ["sensor"]

    strict_cfg = copy.deepcopy(search_config)
    strict_cfg.update(
        {
            "keywords": base_keywords,
            "keyword_fields": ["patent_title", "patent_abstract"],
            "keyword_join": "and",
            "num_results": requested,
        }
    )

    expanded_cfg = copy.deepcopy(search_config)
    expanded_cfg.update(
        {
            "keywords": expanded_keywords,
            "keyword_fields": ["patent_title", "patent_abstract"],
            "keyword_join": "or",
            "num_results": requested,
        }
    )

    title_cfg = copy.deepcopy(search_config)
    title_cfg.update(
        {
            "keywords": expanded_keywords,
            "keyword_fields": ["patent_title"],
            "keyword_join": "or",
            "num_results": max(1, requested // 2),
        }
    )

    fallback_cfg = copy.deepcopy(search_config)
    fallback_cfg.update(
        {
            "keywords": expanded_keywords,
            "keyword_fields": ["patent_title", "patent_abstract"],
            "keyword_join": "or",
            "num_results": requested,
        }
    )

    if retrieval_cfg.get("fallback_relax_assignee", True):
        fallback_cfg["assignee_type"] = ""

    return [
        {"name": "strict_intent", "config": strict_cfg},
        {"name": "expanded_synonyms", "config": expanded_cfg},
        {"name": "title_priority", "config": title_cfg},
        {"name": "broad_fallback", "config": fallback_cfg},
    ]


def build_patentsearch_payload(config: Dict[str, Any]) -> Dict[str, Any]:
    """Compile structured config into PatentSearch API request payload."""

    filters: List[Dict[str, Any]] = []

    keyword_fields = config.get("keyword_fields") or ["patent_title", "patent_abstract"]
    if isinstance(keyword_fields, str):
        keyword_fields = [keyword_fields]
    keyword_fields = [field for field in keyword_fields if isinstance(field, str) and field.strip()]
    if not keyword_fields:
        keyword_fields = ["patent_title", "patent_abstract"]

    keyword_filters: List[Dict[str, Any]] = []
    for keyword in config.get("keywords", []):
        per_field = [{"_text_all": {field: keyword}} for field in keyword_fields]
        if len(per_field) == 1:
            keyword_filters.append(per_field[0])
        else:
            keyword_filters.append({"_or": per_field})

    keyword_join = str(config.get("keyword_join") or "and").lower()
    if keyword_filters:
        if keyword_join == "or":
            filters.append({"_or": keyword_filters})
        else:
            filters.extend(keyword_filters)

    filing_start = config.get("filing_date_start")
    filing_end = config.get("filing_date_end")
    if filing_start:
        filters.append({"_gte": {"application.filing_date": filing_start}})
    if filing_end:
        filters.append({"_lte": {"application.filing_date": filing_end}})

    # If caller wants to prioritize likely-expired patents, add a patent_date cutoff
    # (e.g., patents issued more than `expired_cutoff_years` ago).
    if bool(config.get("require_likely_expired", False)):
        try:
            cutoff_years = int(config.get("expired_cutoff_years", 20))
        except Exception:
            cutoff_years = 20
        try:
            cutoff_year = datetime.now().year - cutoff_years
            cutoff_date = f"{cutoff_year}-01-01"
            filters.append({"_lte": {"patent_date": cutoff_date}})
        except Exception:
            pass

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
    title = raw.get("patent_title") or raw.get("title") or ""
    abstract = raw.get("patent_abstract") or raw.get("abstract") or ""
    patent_date = raw.get("patent_date") or None

    filing_date: Optional[str] = raw.get("filing_date")
    application = raw.get("application")
    if not filing_date and isinstance(application, list) and application:
        first = application[0]
        if isinstance(first, dict):
            filing_date = first.get("filing_date")
    elif not filing_date and isinstance(application, dict):
        filing_date = application.get("filing_date")

    assignee_type: Optional[str] = raw.get("assignee_type")
    assignees = raw.get("assignees")
    if not assignee_type and isinstance(assignees, list) and assignees:
        first_assignee = assignees[0]
        if isinstance(first_assignee, dict):
            assignee_type = first_assignee.get("assignee_type")

    link = raw.get("link") or (f"https://patents.google.com/patent/{patent_number}" if patent_number else "")

    normalized = {
        "patent_number": patent_number,
        "title": title,
        "abstract": abstract,
        "link": link,
        "patent_date": patent_date,
        "filing_date": filing_date,
        "assignee_type": assignee_type,
        "source_provider": raw.get("source_provider") or "patentsview_patentsearch",
        "patent_type": raw.get("patent_type"),
    }

    if "_retrieval_pass_hits" in raw:
        normalized["_retrieval_pass_hits"] = raw.get("_retrieval_pass_hits", [])

    return normalized


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


def _dedupe_and_normalize_records(pass_records: List[Tuple[str, Dict[str, Any]]]) -> List[Dict[str, Any]]:
    deduped: Dict[str, Dict[str, Any]] = {}

    for pass_name, raw in pass_records:
        normalized = normalize_patent_record(raw)
        dedupe_key = normalized.get("patent_number") or f"{normalized.get('title','')}|{normalized.get('filing_date','')}"
        if dedupe_key not in deduped:
            normalized["_retrieval_pass_hits"] = [pass_name]
            deduped[dedupe_key] = normalized
            continue

        existing = deduped[dedupe_key]
        existing_hits = existing.setdefault("_retrieval_pass_hits", [])
        if pass_name not in existing_hits:
            existing_hits.append(pass_name)

        if not existing.get("abstract") and normalized.get("abstract"):
            existing["abstract"] = normalized["abstract"]
        if not existing.get("filing_date") and normalized.get("filing_date"):
            existing["filing_date"] = normalized["filing_date"]

    for record in deduped.values():
        record["_retrieval_pass_hits"] = sorted(set(record.get("_retrieval_pass_hits", [])))

    return list(deduped.values())


def rerank_patent_candidates_v2(
    candidates: List[Dict[str, Any]],
    search_config: Dict[str, Any],
    as_of_date: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """Rerank candidates with deterministic retrieval scorecards."""

    if not candidates:
        return []

    now = as_of_date or date.today()

    base_keywords = [str(k).lower().strip() for k in search_config.get("keywords", []) if str(k).strip()]
    expanded_keywords = expand_keywords_for_v2(
        base_keywords,
        max_expanded_keywords=int((search_config.get("retrieval_v2") or {}).get("max_expanded_keywords") or 24),
    )
    query_text = " ".join(expanded_keywords)

    corpus_docs = [f"{pat.get('title', '')} {pat.get('abstract', '')}" for pat in candidates]

    weights = dict(DEFAULT_RETRIEVAL_SCORE_WEIGHTS)
    retrieval_cfg = search_config.get("retrieval_v2") or {}
    if isinstance(retrieval_cfg.get("score_weights"), dict):
        weights.update({k: float(v) for k, v in retrieval_cfg["score_weights"].items() if k in weights})

    query_terms = tokenize_text(" ".join(base_keywords))
    pass_names = {"strict_intent", "expanded_synonyms", "title_priority", "broad_fallback", "single_pass"}

    ranked: List[Dict[str, Any]] = []
    for patent in candidates:
        title = str(patent.get("title") or "")
        abstract = str(patent.get("abstract") or "")
        title_lower = title.lower()
        doc_text = f"{title} {abstract}"
        doc_tokens = tokenize_text(doc_text)

        exact_hits = sum(1 for keyword in base_keywords if keyword and keyword in title_lower)
        title_exact_match = clamp((exact_hits / max(1, len(base_keywords))) * 10.0)

        coverage = clamp(term_coverage(query_terms, doc_tokens) * 10.0)
        semantic_similarity = clamp(tfidf_cosine_similarity(query_text, doc_text, corpus_docs) * 10.0)
        expiration_conf = expiration_confidence_score(patent, as_of_date=now)

        pass_hits = [hit for hit in patent.get("_retrieval_pass_hits", []) if hit in pass_names]
        pass_diversity = clamp((len(pass_hits) / 4.0) * 10.0)

        total = (
            title_exact_match * weights["title_exact_match"]
            + coverage * weights["query_coverage"]
            + semantic_similarity * weights["semantic_similarity"]
            + expiration_conf * weights["expiration_confidence"]
            + pass_diversity * weights["pass_diversity"]
        )

        scored = patent.copy()
        scored["retrieval_scorecard"] = {
            "title_exact_match": round(title_exact_match, 3),
            "query_coverage": round(coverage, 3),
            "semantic_similarity": round(semantic_similarity, 3),
            "expiration_confidence": round(expiration_conf, 3),
            "pass_diversity": round(pass_diversity, 3),
            "weights": weights,
            "total": round(clamp(total), 3),
        }
        scored["_retrieval_pass_hits"] = pass_hits
        ranked.append(scored)

    ranked.sort(
        key=lambda item: (
            item.get("retrieval_scorecard", {}).get("total", 0.0),
            item.get("patent_date") or "",
            item.get("patent_number") or "",
        ),
        reverse=True,
    )
    return ranked


def _apply_viability_scoring(
    patents: List[Dict[str, Any]],
    search_config: Dict[str, Any],
    as_of_date: Optional[date] = None,
) -> List[Dict[str, Any]]:
    if not patents:
        return []

    viability_cfg = search_config.get("viability_v2") or {}
    viability_weights = viability_cfg.get("weights") if isinstance(viability_cfg, dict) else None

    enriched: List[Dict[str, Any]] = []
    for patent in patents:
        viability = compute_viability_scorecard(patent, weights=viability_weights, as_of_date=as_of_date)
        retrieval_score = patent.get("retrieval_scorecard", {}).get("total", 0.0)
        expiration_score = expiration_confidence_score(patent, as_of_date=as_of_date)
        opportunity = compute_opportunity_score_v2(
            retrieval_total=float(retrieval_score),
            viability_total=float(viability["components"]["total"]),
            expiration_confidence=float(expiration_score),
            scoring_weights=search_config.get("scoring_weights") or {},
        )

        patent_copy = patent.copy()
        patent_copy["viability_scorecard"] = viability["components"]
        patent_copy["market_domain"] = viability["market_domain"]
        patent_copy["opportunity_score_v2"] = opportunity
        patent_copy["opportunity_score"] = opportunity
        patent_copy["scoring_version"] = SCORING_VERSION

        patent_copy["explanations"] = {
            "retrieval": (
                "Retrieval based on title match, keyword coverage, semantic similarity, "
                f"and multi-pass agreement ({', '.join(patent.get('_retrieval_pass_hits', [])) or 'single pass'})."
            ),
            "viability": viability["summary"],
            "opportunity": (
                f"Blended score from retrieval={retrieval_score:.2f}, "
                f"viability={viability['components']['total']:.2f}, "
                f"expiration={expiration_score:.2f}."
            ),
        }
        patent_copy["score_components"] = viability["components"]
        enriched.append(patent_copy)

    enriched.sort(key=lambda row: row.get("opportunity_score_v2", 0.0), reverse=True)
    return enriched


def _discover_raw_records_v2(
    search_config: Dict[str, Any],
    warnings_list: List[str],
) -> Tuple[List[Tuple[str, Dict[str, Any]]], Dict[str, Any]]:
    diagnostics = _base_diagnostics(search_config, warnings_list)

    pass_records: List[Tuple[str, Dict[str, Any]]] = []
    pass_counts: Dict[str, int] = {}

    for idx, pass_spec in enumerate(build_retrieval_passes(search_config)):
        pass_name = pass_spec["name"]
        pass_config = copy.deepcopy(pass_spec["config"])
        pass_wrapper = {"patent_search": pass_config}

        try:
            records, pass_diag = fetch_patents_patentsview(pass_wrapper)
        except PatentDiscoveryError as exc:
            if idx == 0 or exc.code in {"missing_api_key", "auth_failed"}:
                raise
            diagnostics["warnings"].append(
                f"Retrieval pass '{pass_name}' failed with {exc.code}; continuing with available passes."
            )
            pass_counts[pass_name] = 0
            continue

        diagnostics["http_status"] = pass_diag.get("http_status")
        pass_counts[pass_name] = len(records)
        pass_records.extend((pass_name, record) for record in records)

    diagnostics["pass_counts"] = pass_counts
    diagnostics["raw_count"] = len(pass_records)
    diagnostics["status"] = "ok"
    return pass_records, diagnostics


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
        if search_config.get("enable_v2_pipeline", True):
            pass_records, diagnostics = _discover_raw_records_v2(search_config, warnings_list)
            normalized = _dedupe_and_normalize_records(pass_records)
            diagnostics["deduped_count"] = len(normalized)
        else:
            raw_records, diagnostics = fetch_patents_patentsview(config)
            normalized = [normalize_patent_record(item) for item in raw_records]
            for record in normalized:
                record["_retrieval_pass_hits"] = ["single_pass"]
            diagnostics["pass_counts"] = {"single_pass": len(raw_records)}
            diagnostics["deduped_count"] = len(normalized)

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
                diagnostics["deduped_count"] = len(fallback)
                diagnostics["next_actions"].append(
                    "Switch fallback off after troubleshooting and use PatentsView API as primary source."
                )
                return fallback, diagnostics

        raise exc

    today = date.today()

    diagnostics["raw_count"] = len(normalized)

    if search_config.get("require_likely_expired", True):
        filtered = [r for r in normalized if is_likely_expired(r, today)]
    else:
        filtered = normalized

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

    ranked = rerank_patent_candidates_v2(filtered, search_config, as_of_date=today)
    scored = _apply_viability_scoring(ranked, search_config, as_of_date=today)

    requested = int(search_config.get("num_results") or len(scored))
    limited = scored[:requested]

    diagnostics["filtered_count"] = len(limited)
    diagnostics["status"] = diagnostics.get("status") or "ok"

    return limited, diagnostics


def save_discovery_diagnostics(output_dir: str, diagnostics: Dict[str, Any], timestamp: str) -> Path:
    """Persist discovery diagnostics to disk."""

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    diagnostics_path = out / f"discovery_diagnostics_{timestamp}.json"
    with open(diagnostics_path, "w", encoding="utf-8") as handle:
        import json

        json.dump(diagnostics, handle, indent=2)
    return diagnostics_path
