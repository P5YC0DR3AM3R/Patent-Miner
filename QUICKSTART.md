# Patent Miner V3 - Quick Start

## 1) Install

```bash
pip install -r requirements.txt
```

## 2) Configure API key

```bash
cp .env.example .env
# edit .env and set:
PATENTSVIEW_API_KEY=your_api_key_here
```

Get a free key: https://www.patentsview.org/api/

## 3) Run discovery

```bash
python temp_patent_miner.py
```

Output files are written to `patent_intelligence_vault/`:
- `patent_discoveries_<timestamp>.json`
- `discovery_diagnostics_<timestamp>.json`

## 4) Launch dashboard

```bash
streamlit run streamlit_app.py
```

Open `http://localhost:8501`.

## Dashboard Map (V3)

- `Executive View`: key metrics + timeline + domain mix
- `Opportunity Ranking`: top candidates with “why ranked” summaries
- `Patent Details`: deep dive on a selected patent
- `Score Explainability`: retrieval vs viability vs total comparison
- `Export`: CSV/JSON download

## V3 Defaults

`patent_miner_config.py` enables:
- Hybrid multi-pass retrieval (`enable_v2_pipeline=True`)
- Viability scorecards (`viability_v2.enabled=True`)
- Opportunity blend weights (`scoring_weights`)

## Run tests

```bash
python -m unittest discover -s tests -p 'test_*.py'
```

If `dotenv` or `streamlit` imports fail, re-run:

```bash
pip install -r requirements.txt
```
