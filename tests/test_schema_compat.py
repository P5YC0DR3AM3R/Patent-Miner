import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from patent_discovery import discover_patents
from streamlit_app import PatentAnalyzer


class FakeResponse:
    def __init__(self, status_code=200, json_data=None, headers=None):
        self.status_code = status_code
        self._json_data = json_data if json_data is not None else {}
        self.headers = headers or {}

    def json(self):
        return self._json_data


class SchemaCompatibilityTests(unittest.TestCase):
    def test_discovery_includes_legacy_and_v2_fields(self):
        config = {
            "patent_search": {
                "keywords": ["portable", "sensor"],
                "filing_date_start": "1995-01-01",
                "filing_date_end": "2005-12-31",
                "num_results": 2,
                "per_page": 50,
                "require_likely_expired": False,
                "enable_v2_pipeline": True,
            }
        }

        payload = {
            "patents": [
                {
                    "patent_id": "US501",
                    "patent_title": "Portable Sensor Device",
                    "patent_abstract": "A compact sensing apparatus.",
                    "patent_date": "2000-01-01",
                    "patent_type": "utility",
                    "application": [{"filing_date": "1998-01-01"}],
                    "assignees": [{"assignee_type": "4"}],
                },
                {
                    "patent_id": "US502",
                    "patent_title": "Wireless Monitoring Device",
                    "patent_abstract": "A remote sensor and telemetry unit.",
                    "patent_date": "2001-01-01",
                    "patent_type": "utility",
                    "application": [{"filing_date": "1999-01-01"}],
                    "assignees": [{"assignee_type": "4"}],
                },
            ],
            "total_hits": 2,
        }
        responses = [FakeResponse(200, payload) for _ in range(4)]

        with mock.patch.dict(os.environ, {"PATENTSVIEW_API_KEY": "ok"}, clear=True):
            with mock.patch("patent_discovery.requests.Session.post", side_effect=responses):
                patents, diagnostics = discover_patents(config)

        self.assertGreaterEqual(len(patents), 1)
        patent = patents[0]

        # Legacy keys
        self.assertIn("patent_number", patent)
        self.assertIn("title", patent)
        self.assertIn("abstract", patent)
        self.assertIn("filing_date", patent)

        # V2 extension keys
        self.assertIn("retrieval_scorecard", patent)
        self.assertIn("viability_scorecard", patent)
        self.assertIn("opportunity_score_v2", patent)
        self.assertIn("market_domain", patent)
        self.assertIn("explanations", patent)

        self.assertIn("pass_counts", diagnostics)
        self.assertIn("deduped_count", diagnostics)
        self.assertIn("ranking_version", diagnostics)
        self.assertIn("scoring_version", diagnostics)

    def test_legacy_discovery_file_still_loads_in_analyzer(self):
        legacy_payload = [
            {
                "patent_number": "US777",
                "title": "Legacy Portable Detection Device",
                "abstract": "Legacy output without v2 scorecards.",
                "filing_date": "1997-02-01",
                "patent_date": "1999-06-01",
                "assignee_type": "4",
                "patent_type": "utility",
                "link": "https://patents.google.com/patent/US777",
                "source_provider": "patentsview_patentsearch",
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir)
            file_path = vault / "patent_discoveries_20260101_000000.json"
            file_path.write_text(json.dumps(legacy_payload), encoding="utf-8")

            analyzer = PatentAnalyzer(vault_dir=str(vault))
            enriched = analyzer.get_enriched_patents()

        self.assertEqual(len(enriched), 1)
        self.assertIn("retrieval_scorecard", enriched[0])
        self.assertIn("viability_scorecard", enriched[0])
        self.assertIn("opportunity_score_v2", enriched[0])


if __name__ == "__main__":
    unittest.main()
