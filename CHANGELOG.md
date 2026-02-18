# Changelog

Date: 2026-02-18

## File-by-File Significant Changes

- `.env`
  - Replaced plaintext API secret with placeholder value.

- `.gitignore`
  - Added `firebase-debug.log` to prevent accidental log leakage.

- `firebase-debug.log`
  - Redacted local debug content to non-sensitive placeholder text.

- `requirements.txt`
  - Reduced to baseline runtime dependencies and switched to `~=` pins.

- `requirements-optional.txt`
  - Added optional dependency group for crew and local-model workflows.

- `summarization_config.py`
  - Added shared summarization prompt template and environment-based model-path resolution.

- `patent_summarizer.py`
  - Removed hardcoded workstation paths.
  - Adopted shared summarization config.
  - Added graceful behavior when optional model runtime is missing.

- `generate_summaries.py`
  - Removed duplicate prompt/model constants.
  - Adopted shared summarization config and optional dependency checks.

- `patent_discovery.py`
  - Hardened fallback search request by using parameterized query encoding (`params=`).

- `run_crew_analysis.py`
  - Refactored into canonical CLI entrypoint with `main()` and consistent error handling.

- `execute_crew_analysis.py`
  - Converted to backward-compatible wrapper that delegates to `run_crew_analysis.main`.

- `expired_patent_analysis_crew.py`
  - Removed unused import.
  - Replaced placeholder markdown section with concrete crew summary output.
  - Standardized financial terminology to full-form Net Present Value naming.

- `run_expired_patent_analysis.py`
  - Removed unused import and added empty-result guard for average score.
  - Renamed financial field usage to full-form names (`net_present_value_*`, `internal_rate_percent`).
  - Updated report wording to full-form Net Present Value labels.

- `patent_analysis_framework.py`
  - **Business logic changed**: rebuilt financial engine to scenario-based cash-flow modeling.
  - Added tax, depreciation, maintenance capital, overhead, working capital, churn/refund, and customer acquisition assumptions.
  - Added capped growth assumptions and scenario discount rates (12% / 10% / 8%).
  - Replaced proxy return metric with cash-flow-based internal rate computation.
  - Renamed exported financial fields and CSV column to full-form Net Present Value naming.
  - Added UTF-8 explicit read for discovery input in runner path.

- `streamlit_app.py`
  - Rebuilt tab/navigation hierarchy to implemented two-level structure.
  - Added mobile-first design tokens, responsive breakpoints, and touch-target-safe controls.
  - Removed dynamic unsafe HTML rendering for data fields.
  - Added optional access-code gate via `PATENT_MINER_ACCESS_CODE`.
  - Standardized financial labels to full-form Net Present Value terminology.
  - Fixed corrupted page icon string.

- `tests/test_streamlit_data_flow.py`
  - Updated navigation expectations to new top-level tabs.
  - Updated precomputed fixture to current scoring contract (`SCORING_VERSION` and required viability components).

- `brand_intelligence.py`
  - Replaced hardcoded checkpoint file with auto-discovery + optional env override.
  - Removed random sampling and random risk assignment; outputs are now deterministic.
  - Cleared lint issues from unnecessary formatting.

- `display_results.py`
  - Replaced hardcoded checkpoint file with auto-discovery + optional env override.
  - Added empty-data guard and denominator safety for averages.
  - Cleared lint issues from unnecessary formatting.

- `docker-compose.yml`
  - Restricted local dashboard host exposure to loopback (`127.0.0.1:8501:8501`).

- `run_dashboard.sh`
  - Explicitly binds Streamlit to localhost for local execution.

- `README.md`
  - Rewritten to reflect current architecture, navigation, setup, optional dependencies, and run/test commands.

- `TAB_STRUCTURE.md`
  - Replaced proposal with implemented old-to-new tab map and rationale.

- `SECURITY_AUDIT.md`
  - Replaced pre-refactor findings with resolved/mitigated status and remediation evidence.

- `CODE_AUDIT.md`
  - Replaced pre-refactor findings with resolved status and validation outcomes.

- `FINANCIAL_AUDIT.md`
  - Replaced pre-refactor findings with updated financial assumptions, replacement values, and rationale.

- `FILE_INVENTORY.md`
  - Updated inventory count and added newly introduced files/artifacts.

- `EXPIRED_PATENT_ANALYSIS_GUIDE.md`
- `EXPIRED_PATENT_BI_IMPLEMENTATION.md`
- `STREAMLIT_BI_TAB_GUIDE.md`
  - Normalized terminology to full-form Net Present Value naming.

- `patent_intelligence_vault/*.md`, `patent_intelligence_vault/*.json`, `patent_intelligence_vault/*.csv`
  - Updated historical artifact terminology to full-form Net Present Value naming.

- `patent_intelligence_vault/patent_analysis_results_20260217_221146.json`
- `patent_intelligence_vault/patent_rankings_20260217_221146.csv`
- `patent_intelligence_vault/EXPIRED_PATENT_REPORT_20260217_221146.md`
  - Added fresh outputs generated after financial model refactor.
