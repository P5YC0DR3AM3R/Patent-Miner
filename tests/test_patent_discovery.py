import json
import os
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

import requests

import temp_patent_miner
from patent_discovery import (
    PatentDiscoveryError,
    build_patentsearch_payload,
    discover_patents,
    is_likely_expired,
    normalize_patent_record,
    parse_legacy_search_query,
)


class FakeResponse:
    def __init__(self, status_code=200, json_data=None, headers=None):
        self.status_code = status_code
        self._json_data = json_data if json_data is not None else {}
        self.headers = headers or {}

    def json(self):
        return self._json_data


def make_config(**overrides):
    base = {
        "patent_search": {
            "provider": "patentsview_patentsearch",
            "api_url": "https://search.patentsview.org/api/v1/patent/",
            "api_key_env": "PATENTSVIEW_API_KEY",
            "keywords": ["portable", "sensor"],
            "filing_date_start": "1995-01-01",
            "filing_date_end": "2005-12-31",
            "assignee_type": "individual",
            "num_results": 5,
            "require_likely_expired": False,
            "allow_legacy_scrape_fallback": False,
            "per_page": 2,
            "max_retries": 2,
            "timeout_seconds": 2,
            "retry_backoff_seconds": 0.01,
            "enable_v2_pipeline": False,
            "retrieval_v2": {"enabled": False},
        },
        "output_dir": "./patent_intelligence_vault/",
    }

    for key, value in overrides.items():
        if key == "patent_search":
            base["patent_search"].update(value)
        else:
            base[key] = value
    return base


class PatentDiscoveryTests(unittest.TestCase):
    def test_build_payload_from_structured_config(self):
        payload = build_patentsearch_payload(
            {
                "keywords": ["portable sensor"],
                "filing_date_start": "1995-01-01",
                "filing_date_end": "2005-12-31",
                "assignee_type": "individual",
                "per_page": 50,
            }
        )

        self.assertIn("q", payload)
        self.assertIn("f", payload)
        self.assertEqual(payload["o"]["per_page"], 50)
        self.assertIn("application.filing_date", json.dumps(payload))
        self.assertIn("assignees.assignee_type", json.dumps(payload))
        self.assertIn("patent_title", json.dumps(payload))
        self.assertIn("patent_abstract", json.dumps(payload))

    def test_missing_api_key_raises_classified_error(self):
        config = make_config()
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(PatentDiscoveryError) as ctx:
                discover_patents(config)
        self.assertEqual(ctx.exception.code, "missing_api_key")
        self.assertIn("PATENTSVIEW_API_KEY", ctx.exception.message)

    def test_auth_failure_raises_classified_error(self):
        config = make_config()
        with mock.patch.dict(os.environ, {"PATENTSVIEW_API_KEY": "bad-key"}, clear=True):
            with mock.patch(
                "patent_discovery.requests.Session.post",
                return_value=FakeResponse(401, {"error": True}),
            ):
                with self.assertRaises(PatentDiscoveryError) as ctx:
                    discover_patents(config)

        self.assertEqual(ctx.exception.code, "auth_failed")
        self.assertEqual(ctx.exception.diagnostics["http_status"], 401)

    def test_empty_result_set_raises_zero_results(self):
        config = make_config()
        with mock.patch.dict(os.environ, {"PATENTSVIEW_API_KEY": "ok"}, clear=True):
            with mock.patch(
                "patent_discovery.requests.Session.post",
                return_value=FakeResponse(200, {"patents": [], "total_hits": 0}),
            ):
                with self.assertRaises(PatentDiscoveryError) as ctx:
                    discover_patents(config)

        self.assertEqual(ctx.exception.code, "zero_results")
        self.assertEqual(ctx.exception.diagnostics["raw_count"], 0)
        self.assertEqual(ctx.exception.diagnostics["filtered_count"], 0)

    def test_normalize_record_handles_missing_fields(self):
        record = normalize_patent_record({"patent_id": None, "patent_title": None, "application": []})
        self.assertEqual(record["patent_number"], "")
        self.assertEqual(record["title"], "")
        self.assertEqual(record["abstract"], "")
        self.assertEqual(record["link"], "")
        self.assertIn("source_provider", record)

    def test_is_likely_expired_edge_cases(self):
        as_of = date(2026, 2, 13)

        self.assertTrue(
            is_likely_expired({"filing_date": "2006-02-13", "patent_date": None, "patent_type": "utility"}, as_of)
        )
        self.assertFalse(
            is_likely_expired({"filing_date": "2007-01-01", "patent_date": None, "patent_type": "utility"}, as_of)
        )
        self.assertFalse(
            is_likely_expired({"filing_date": None, "patent_date": "2012-03-01", "patent_type": "design"}, as_of)
        )
        self.assertTrue(
            is_likely_expired({"filing_date": None, "patent_date": "2000-03-01", "patent_type": "design"}, as_of)
        )

    def test_single_page_success(self):
        config = make_config(patent_search={"num_results": 2, "per_page": 100})
        response = FakeResponse(
            200,
            {
                "patents": [
                    {
                        "patent_id": "US123",
                        "patent_title": "Portable Sensor Device",
                        "patent_abstract": "An abstract.",
                        "patent_date": "2000-01-01",
                        "application": [{"filing_date": "1998-01-01"}],
                        "assignees": [{"assignee_type": "4"}],
                    },
                    {
                        "patent_id": "US124",
                        "patent_title": "Wireless Sensor Device",
                        "patent_abstract": "Another abstract.",
                        "patent_date": "2001-01-01",
                        "application": [{"filing_date": "1999-01-01"}],
                        "assignees": [{"assignee_type": "4"}],
                    },
                ],
                "total_hits": 2,
            },
        )

        with mock.patch.dict(os.environ, {"PATENTSVIEW_API_KEY": "ok"}, clear=True):
            with mock.patch("patent_discovery.requests.Session.post", return_value=response):
                patents, diagnostics = discover_patents(config)

        self.assertEqual(len(patents), 2)
        self.assertEqual(diagnostics["raw_count"], 2)
        self.assertEqual(diagnostics["filtered_count"], 2)
        self.assertIn("patent_number", patents[0])

    def test_multi_page_and_result_cap(self):
        config = make_config(patent_search={"num_results": 3, "per_page": 2})

        page1 = FakeResponse(
            200,
            {
                "patents": [
                    {"patent_id": "US1", "patent_title": "A", "application": [{"filing_date": "1998-01-01"}], "patent_date": "2000-01-01"},
                    {"patent_id": "US2", "patent_title": "B", "application": [{"filing_date": "1998-01-01"}], "patent_date": "2000-01-01"},
                ],
                "total_hits": 5,
            },
        )
        page2 = FakeResponse(
            200,
            {
                "patents": [
                    {"patent_id": "US3", "patent_title": "C", "application": [{"filing_date": "1998-01-01"}], "patent_date": "2000-01-01"},
                    {"patent_id": "US4", "patent_title": "D", "application": [{"filing_date": "1998-01-01"}], "patent_date": "2000-01-01"},
                ],
                "total_hits": 5,
            },
        )

        with mock.patch.dict(os.environ, {"PATENTSVIEW_API_KEY": "ok"}, clear=True):
            with mock.patch(
                "patent_discovery.requests.Session.post",
                side_effect=[page1, page2],
            ) as mocked_post:
                patents, _ = discover_patents(config)

        self.assertEqual(len(patents), 3)
        self.assertEqual(mocked_post.call_count, 2)

    def test_retry_then_success_after_timeout(self):
        config = make_config(patent_search={"num_results": 1, "per_page": 1, "max_retries": 3})

        timeout_exc = requests.Timeout("timeout")
        success_response = FakeResponse(
            200,
            {
                "patents": [
                    {
                        "patent_id": "US777",
                        "patent_title": "Recovered Patent",
                        "patent_abstract": "Recovered",
                        "patent_date": "2000-01-01",
                        "application": [{"filing_date": "1999-01-01"}],
                    }
                ],
                "total_hits": 1,
            },
        )

        with mock.patch.dict(os.environ, {"PATENTSVIEW_API_KEY": "ok"}, clear=True):
            with mock.patch("patent_discovery.time.sleep", return_value=None):
                with mock.patch(
                    "patent_discovery.requests.Session.post",
                    side_effect=[timeout_exc, success_response],
                ) as mocked_post:
                    patents, _ = discover_patents(config)

        self.assertEqual(len(patents), 1)
        self.assertEqual(mocked_post.call_count, 2)

    def test_legacy_query_parser(self):
        parsed, warnings_list = parse_legacy_search_query(
            'status:expired filing_date:1995-2005 "portable sensor" assignee_type:individual'
        )
        self.assertTrue(parsed["require_likely_expired"])
        self.assertEqual(parsed["filing_date_start"], "1995-01-01")
        self.assertEqual(parsed["filing_date_end"], "2005-12-31")
        self.assertEqual(parsed["assignee_type"], "individual")
        self.assertIn("portable sensor", parsed["keywords"])
        self.assertEqual(warnings_list, [])

    def test_notebook_is_valid_json(self):
        notebook_path = Path("Patent_Miner.ipynb")
        with notebook_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        self.assertEqual(payload["nbformat"], 4)
        self.assertIn("cells", payload)
        self.assertGreaterEqual(len(payload["cells"]), 2)

    def test_script_and_notebook_parity_with_mocked_api(self):
        notebook_path = Path("Patent_Miner.ipynb")
        notebook_json = json.loads(notebook_path.read_text(encoding="utf-8"))
        code_blob = "\n".join(
            "".join(cell.get("source", []))
            for cell in notebook_json.get("cells", [])
            if cell.get("cell_type") == "code"
        )
        self.assertIn("from patent_discovery import PatentDiscoveryError, discover_patents", code_blob)
        self.assertIn("from patent_miner_config import DEFAULT_CONFIG, build_config", code_blob)

        response = FakeResponse(
            200,
            {
                "patents": [
                    {
                        "patent_id": "US901",
                        "patent_title": "Portable Sensor Array",
                        "patent_abstract": "A",
                        "patent_date": "2000-01-01",
                        "application": [{"filing_date": "1998-01-01"}],
                        "assignees": [{"assignee_type": "4"}],
                    },
                    {
                        "patent_id": "US902",
                        "patent_title": "Portable Sensor Hub",
                        "patent_abstract": "B",
                        "patent_date": "2001-01-01",
                        "application": [{"filing_date": "1999-01-01"}],
                        "assignees": [{"assignee_type": "4"}],
                    },
                ],
                "total_hits": 2,
            },
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            script_config = {
                "output_dir": tmpdir,
                "patent_search": {
                    "num_results": 2,
                    "per_page": 100,
                    "require_likely_expired": False,
                    "enable_v2_pipeline": False,
                    "retrieval_v2": {"enabled": False},
                },
            }

            with mock.patch.dict(os.environ, {"PATENTSVIEW_API_KEY": "ok"}, clear=True):
                with mock.patch(
                    "patent_discovery.requests.Session.post",
                    side_effect=[response, response],
                ):
                    script_patents, _ = temp_patent_miner.run_discovery(script_config)
                    module_patents, _ = discover_patents(script_config)

        self.assertEqual(len(script_patents), len(module_patents))


if __name__ == "__main__":
    unittest.main()
