# Patent Miner V3

Patent Miner V3 discovers likely expired patents, reranks them with a hybrid retrieval strategy, scores market viability with deterministic evidence components, and presents results in a legibility-first Streamlit dashboard.

## Quick Start

1. Install dependencies.
```bash
pip install -r requirements.txt
```

2. Set your PatentsView API key.
```bash
cp .env.example .env
# edit .env
PATENTSVIEW_API_KEY=your_api_key_here
```

3. Run discovery.
```bash
python temp_patent_miner.py
```

4. Launch dashboard.
```bash
streamlit run streamlit_app.py
```

## What Changed in V3

1. Hybrid retrieval pipeline (multi-pass):
- `strict_intent`
- `expanded_synonyms`
- `title_priority`
- `broad_fallback`

2. Deterministic viability scorecard:
- `market_demand`
- `build_feasibility`
- `competition_headroom`
- `differentiation_potential`
- `commercial_readiness`

3. Explainable ranking output:
- `retrieval_scorecard`
- `viability_scorecard`
- `opportunity_score_v2`
- `market_domain`
- `explanations`

4. Legibility-first UI with segmented in-body tabs:
- `Executive View`
- `Opportunity Ranking`
- `Patent Details`
- `Score Explainability`
- `Export`

## Core Files

- `patent_discovery.py`: discovery, multi-pass retrieval, dedupe, reranking, scoring orchestration.
- `viability_scoring.py`: deterministic viability components and opportunity blending.
- `scoring_utils.py`: tokenization, TF-IDF similarity, sparse cosine helpers.
- `patent_miner_config.py`: default config including V3 controls.
- `streamlit_app.py`: V3 dashboard and legacy artifact compatibility fallback.
- `temp_patent_miner.py`: CLI discovery runner.

## Config (V3)

`patent_miner_config.py` uses these V3 controls under `patent_search`:

```python
"enable_v2_pipeline": True,
"retrieval_v2": {
  "enabled": True,
  "max_expanded_keywords": 24,
  "fallback_relax_assignee": True,
},
"viability_v2": {
  "enabled": True,
  "weights": {},
},
"scoring_weights": {
  "retrieval": 0.35,
  "viability": 0.45,
  "expiration": 0.20,
}
```

## Output Schema (Backwards-Compatible Extension)

Each discovered patent keeps legacy keys and adds V3 fields:

```json
{
  "patent_number": "US1234567",
  "title": "Portable environmental sensor system",
  "abstract": "...",
  "filing_date": "1998-01-01",
  "patent_date": "2000-01-01",
  "assignee_type": "4",
  "patent_type": "utility",
  "source_provider": "patentsview_patentsearch",
  "link": "https://patents.google.com/patent/US1234567",
  "retrieval_scorecard": {
    "title_exact_match": 8.5,
    "query_coverage": 7.8,
    "semantic_similarity": 7.2,
    "expiration_confidence": 9.1,
    "pass_diversity": 7.5,
    "total": 7.9
  },
  "viability_scorecard": {
    "market_demand": 7.4,
    "build_feasibility": 6.9,
    "competition_headroom": 6.7,
    "differentiation_potential": 7.2,
    "commercial_readiness": 7.8,
    "total": 7.2
  },
  "opportunity_score_v2": 7.4,
  "opportunity_score": 7.4,
  "market_domain": "environmental_monitoring",
  "explanations": {
    "retrieval": "...",
    "viability": "...",
    "opportunity": "..."
  }
}
```

Diagnostics (`discovery_diagnostics_*.json`) now include:
- `pass_counts`
- `deduped_count`
- `ranking_version`
- `scoring_version`

## Running Tests

```bash
python -m unittest discover -s tests -p 'test_*.py'
```

Added V3 test modules:
- `tests/test_retrieval_v2.py`
- `tests/test_viability_scoring.py`
- `tests/test_schema_compat.py`
- `tests/test_streamlit_data_flow.py`

## Notes

- No paid external market APIs are required in V3.
- Scoring is deterministic and explainable (no opaque model dependency).
- Existing workflows remain valid because schema changes are additive.
