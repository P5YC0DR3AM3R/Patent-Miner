import json
import unittest
from pathlib import Path

from viability_scoring import (
    classify_market_domain,
    compute_opportunity_score_v2,
    compute_viability_scorecard,
    expiration_confidence_score,
)


def load_fixture_candidates():
    fixture_path = Path("tests/fixtures/patent_candidates_fixture.json")
    with fixture_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)["candidates"]


class ViabilityScoringTests(unittest.TestCase):
    def setUp(self):
        self.candidates = load_fixture_candidates()

    def test_viability_components_are_within_bounds(self):
        for candidate in self.candidates:
            scorecard = compute_viability_scorecard(candidate)
            components = scorecard["components"]
            for name, value in components.items():
                self.assertGreaterEqual(value, 0.0, f"{name} below 0 for {candidate['patent_id']}")
                self.assertLessEqual(value, 10.0, f"{name} above 10 for {candidate['patent_id']}")

    def test_domain_classification_is_deterministic(self):
        sample = next(item for item in self.candidates if item["patent_id"] == "US104")
        domain_one, hits_one = classify_market_domain(sample)
        domain_two, hits_two = classify_market_domain(sample)

        self.assertEqual(domain_one, domain_two)
        self.assertEqual(hits_one, hits_two)

    def test_expected_mixed_domain_assignments(self):
        wearable = next(item for item in self.candidates if item["patent_id"] == "US104")
        soil = next(item for item in self.candidates if item["patent_id"] == "US105")

        wearable_domain, _ = classify_market_domain(wearable)
        soil_domain, _ = classify_market_domain(soil)

        self.assertEqual(wearable_domain, "healthcare_wearables")
        self.assertEqual(soil_domain, "precision_agriculture")

    def test_opportunity_score_is_stable_and_reproducible(self):
        patent = next(item for item in self.candidates if item["patent_id"] == "US102")
        viability = compute_viability_scorecard(patent)
        expiration = expiration_confidence_score(patent)

        first = compute_opportunity_score_v2(
            retrieval_total=7.2,
            viability_total=viability["components"]["total"],
            expiration_confidence=expiration,
        )
        second = compute_opportunity_score_v2(
            retrieval_total=7.2,
            viability_total=viability["components"]["total"],
            expiration_confidence=expiration,
        )

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
