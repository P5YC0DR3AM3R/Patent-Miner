import json
import tempfile
import unittest
from pathlib import Path

from streamlit_app import PatentAnalyzer, VIEW_TABS


class StreamlitDataFlowTests(unittest.TestCase):
    def test_analyzer_uses_precomputed_v2_scorecards(self):
        payload = [
            {
                "patent_number": "US901",
                "title": "Portable Sensor Array",
                "abstract": "Precomputed v2 data",
                "filing_date": "1998-01-01",
                "patent_date": "2000-01-01",
                "assignee_type": "4",
                "patent_type": "utility",
                "link": "https://patents.google.com/patent/US901",
                "source_provider": "patentsview_patentsearch",
                "retrieval_scorecard": {
                    "title_exact_match": 9.0,
                    "query_coverage": 8.0,
                    "semantic_similarity": 7.5,
                    "expiration_confidence": 9.5,
                    "pass_diversity": 8.0,
                    "total": 8.2,
                },
                "viability_scorecard": {
                    "market_demand": 7.1,
                    "build_feasibility": 6.8,
                    "competition_headroom": 6.5,
                    "differentiation_potential": 7.2,
                    "commercial_readiness": 8.0,
                    "total": 7.1,
                },
                "opportunity_score_v2": 7.49,
                "opportunity_score": 7.49,
                "market_domain": "environmental_monitoring",
                "explanations": {
                    "retrieval": "Precomputed",
                    "viability": "Precomputed",
                    "opportunity": "Precomputed",
                },
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir)
            (vault / "patent_discoveries_20260101_000001.json").write_text(
                json.dumps(payload),
                encoding="utf-8",
            )

            analyzer = PatentAnalyzer(vault_dir=str(vault))
            enriched = analyzer.get_enriched_patents()

        self.assertEqual(len(enriched), 1)
        self.assertEqual(enriched[0]["opportunity_score_v2"], 7.49)
        self.assertIn("retrieval_scorecard", enriched[0])
        self.assertIn("viability_scorecard", enriched[0])

    def test_legacy_payload_gets_v2_fallback_enrichment(self):
        payload = [
            {
                "patent_number": "US902",
                "title": "Portable Gas Detection Apparatus",
                "abstract": "Legacy payload for fallback testing",
                "filing_date": "1997-03-01",
                "patent_date": "2000-09-01",
                "assignee_type": "4",
                "patent_type": "utility",
                "link": "https://patents.google.com/patent/US902",
                "source_provider": "patentsview_patentsearch",
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir)
            (vault / "patent_discoveries_20260101_000002.json").write_text(
                json.dumps(payload),
                encoding="utf-8",
            )

            analyzer = PatentAnalyzer(vault_dir=str(vault))
            enriched = analyzer.get_enriched_patents()

        self.assertEqual(len(enriched), 1)
        self.assertIn("retrieval_scorecard", enriched[0])
        self.assertIn("viability_scorecard", enriched[0])
        self.assertIn("opportunity_score_v2", enriched[0])

    def test_segmented_navigation_labels_are_stable(self):
        self.assertEqual(
            VIEW_TABS,
            [
                "Executive View",
                "Opportunity Ranking",
                "Patent Details",
                "Score Explainability",
                "Export",
            ],
        )

        source = Path("streamlit_app.py").read_text(encoding="utf-8")
        self.assertIn("st.tabs(VIEW_TABS)", source)


if __name__ == "__main__":
    unittest.main()
