import json
import os
import unittest
from pathlib import Path
from unittest import mock

from patent_discovery import discover_patents, expand_keywords_for_v2


class FakeResponse:
    def __init__(self, status_code=200, json_data=None, headers=None):
        self.status_code = status_code
        self._json_data = json_data if json_data is not None else {}
        self.headers = headers or {}

    def json(self):
        return self._json_data


def load_fixture():
    fixture_path = Path("tests/fixtures/patent_candidates_fixture.json")
    with fixture_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def ndcg_at_k(ordered_patent_numbers, relevance_map, k=10):
    ranked = ordered_patent_numbers[:k]

    def dcg(values):
        total = 0.0
        for idx, rel in enumerate(values):
            total += (2**rel - 1) / __import__("math").log2(idx + 2)
        return total

    gains = [relevance_map.get(pid, 0) for pid in ranked]
    ideal = sorted(relevance_map.values(), reverse=True)[:k]
    denom = dcg(ideal)
    if denom == 0:
        return 0.0
    return dcg(gains) / denom


class RetrievalV2Tests(unittest.TestCase):
    def setUp(self):
        self.fixture = load_fixture()
        self.relevance_map = {
            candidate["patent_id"]: candidate["relevance"]
            for candidate in self.fixture["candidates"]
        }

    def _response_for_ids(self, patent_ids):
        lookup = {candidate["patent_id"]: candidate for candidate in self.fixture["candidates"]}
        patents = [lookup[pid] for pid in patent_ids]
        return FakeResponse(200, {"patents": patents, "total_hits": len(patents)})

    def test_keyword_expansion_emits_sensor_synonyms(self):
        expanded = expand_keywords_for_v2(["portable", "sensor"], max_expanded_keywords=24)
        self.assertIn("portable", expanded)
        self.assertIn("sensor", expanded)
        self.assertIn("mobile", expanded)
        self.assertIn("detector", expanded)

    def test_multi_pass_recall_is_at_least_2x_single_pass_baseline(self):
        baseline_config = {
            "patent_search": {
                "keywords": self.fixture["query_keywords"],
                "num_results": 8,
                "per_page": 50,
                "require_likely_expired": False,
                "enable_v2_pipeline": False,
                "retrieval_v2": {"enabled": False},
            }
        }

        strict_response = self._response_for_ids(["US100", "US101", "US102"])

        with mock.patch.dict(os.environ, {"PATENTSVIEW_API_KEY": "ok"}, clear=True):
            with mock.patch("patent_discovery.requests.Session.post", return_value=strict_response):
                baseline_patents, baseline_diag = discover_patents(baseline_config)

        v2_config = {
            "patent_search": {
                "keywords": self.fixture["query_keywords"],
                "num_results": 8,
                "per_page": 50,
                "require_likely_expired": False,
                "enable_v2_pipeline": True,
            }
        }

        v2_responses = [
            self._response_for_ids(["US100", "US101", "US102"]),
            self._response_for_ids(["US101", "US103", "US104", "US106"]),
            self._response_for_ids(["US102", "US104", "US109"]),
            self._response_for_ids(["US105", "US106", "US107", "US108", "US109"]),
        ]

        with mock.patch.dict(os.environ, {"PATENTSVIEW_API_KEY": "ok"}, clear=True):
            with mock.patch("patent_discovery.requests.Session.post", side_effect=v2_responses):
                _, v2_diag = discover_patents(v2_config)

        baseline_count = len(baseline_patents)
        self.assertGreaterEqual(v2_diag["deduped_count"], baseline_count * 2)
        self.assertIn("strict_intent", v2_diag["pass_counts"])
        self.assertIn("broad_fallback", v2_diag["pass_counts"])

    def test_dedup_and_ranking_prioritize_exact_intent_matches(self):
        config = {
            "patent_search": {
                "keywords": self.fixture["query_keywords"],
                "num_results": 10,
                "per_page": 50,
                "require_likely_expired": False,
                "enable_v2_pipeline": True,
            }
        }

        responses = [
            self._response_for_ids(["US100", "US101", "US102"]),
            self._response_for_ids(["US101", "US103", "US104", "US106"]),
            self._response_for_ids(["US102", "US104", "US109"]),
            self._response_for_ids(["US105", "US106", "US107", "US108", "US109"]),
        ]

        with mock.patch.dict(os.environ, {"PATENTSVIEW_API_KEY": "ok"}, clear=True):
            with mock.patch("patent_discovery.requests.Session.post", side_effect=responses):
                patents, _ = discover_patents(config)

        patent_numbers = [patent["patent_number"] for patent in patents]
        self.assertEqual(len(patent_numbers), len(set(patent_numbers)))
        self.assertEqual(patent_numbers[0], "US102")

    def test_ndcg_improves_over_raw_single_pass_order(self):
        config = {
            "patent_search": {
                "keywords": self.fixture["query_keywords"],
                "num_results": 10,
                "per_page": 50,
                "require_likely_expired": False,
                "enable_v2_pipeline": True,
            }
        }

        strict_raw_order = ["US100", "US101", "US102", "US103", "US104"]
        responses = [
            self._response_for_ids(strict_raw_order),
            self._response_for_ids(["US103", "US104", "US105", "US106"]),
            self._response_for_ids(["US102", "US104", "US106", "US109"]),
            self._response_for_ids(["US105", "US106", "US107", "US108", "US109"]),
        ]

        with mock.patch.dict(os.environ, {"PATENTSVIEW_API_KEY": "ok"}, clear=True):
            with mock.patch("patent_discovery.requests.Session.post", side_effect=responses):
                ranked_patents, _ = discover_patents(config)

        baseline_ndcg = ndcg_at_k(strict_raw_order, self.relevance_map, k=10)
        ranked_numbers = [patent["patent_number"] for patent in ranked_patents]
        v2_ndcg = ndcg_at_k(ranked_numbers, self.relevance_map, k=10)

        self.assertGreaterEqual(v2_ndcg - baseline_ndcg, 0.15)


if __name__ == "__main__":
    unittest.main()
