# Patent Miner Discovery Setup

## API key
Set the PatentsView PatentSearch API key before running discovery.

```bash
export PATENTSVIEW_API_KEY="your_api_key_here"
```

If you use a different environment variable name, set `PATENT_SEARCH_API_KEY_ENV` and update config accordingly.

```bash
export PATENT_SEARCH_API_KEY_ENV="MY_PATENT_KEY_ENV"
export MY_PATENT_KEY_ENV="your_api_key_here"
```

## Structured discovery config
The discovery pipeline now uses structured config under `CONFIG["patent_search"]`.

```python
CONFIG["patent_search"] = {
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
}
```

## Run
Script:

```bash
python temp_patent_miner.py
```

Notebook:
- Open `Patent_Miner.ipynb`
- Run the configuration cell
- Run the discovery cell

## Output artifacts
Discovery writes:
- `patent_intelligence_vault/patent_discoveries_<timestamp>.json`
- `patent_intelligence_vault/discovery_diagnostics_<timestamp>.json`

If discovery fails, diagnostics still gets written and includes:
- `provider`, `status`, `http_status`
- `raw_count`, `filtered_count`
- `query_summary`, `errors`, `next_actions`

## Legacy compatibility
- Legacy `CONFIG["search_query"]` is still parsed best-effort but is deprecated.
- Google scraping fallback is disabled by default and only used when `allow_legacy_scrape_fallback=True`.
