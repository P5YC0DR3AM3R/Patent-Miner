# Code Audit

Date: 2026-02-18  
Scope: full repository review using `FILE_INVENTORY.md` and post-refactor validation (`ruff check .`, `python -m unittest discover -s tests -p 'test_*.py'`).

## Findings by File and Resolution

1. `streamlit_app.py`  
   Issue: monolithic legacy layout, duplicate rendering paths, inconsistent navigation labels, unsafe dynamic HTML patterns.  
   Resolution: fully restructured navigation, unified ranking/financial/review flows, removed dynamic raw HTML data rendering, added reusable helpers (`PatentAnalyzer`, `get_numeric_metric`), and mobile-first styling tokens.

2. `tests/test_streamlit_data_flow.py`  
   Issue: navigation contract assertions did not match current UI and precomputed scorecard fixture was missing required v2.1 fields.  
   Resolution: updated tab expectations and fixture metadata (`scoring_version`, expanded viability components) to align with current analyzer behavior.

3. `execute_crew_analysis.py` and `run_crew_analysis.py`  
   Issue: duplicate runner logic and redundant entrypoints.  
   Resolution: `run_crew_analysis.py` is now canonical CLI entrypoint with `main()`. `execute_crew_analysis.py` is a backward-compatible wrapper calling the same function.

4. `patent_analysis_framework.py`  
   Issue: outdated financial field names and coarse financial assumptions in the prior model; minor lint and file I/O quality issues.  
   Resolution: financial model rebuilt with scenario-based cash-flow mechanics and full-form field names, UTF-8-safe file read on discovery import, and lint cleanup.

5. `run_expired_patent_analysis.py`  
   Issue: unused import and missing empty-result guard for average score.  
   Resolution: removed unused import and added safe average guard (`0.0` on empty results).

6. `expired_patent_analysis_crew.py`  
   Issue: placeholder markdown section in generated report output.  
   Resolution: replaced placeholder block with concrete, traceable summary content derived from captured crew output.

7. `display_results.py`  
   Issue: hardcoded checkpoint filename, divide-by-zero risk, and avoidable formatting lint issues.  
   Resolution: latest-checkpoint auto-discovery + optional override, denominator guard, and lint cleanup.

8. `brand_intelligence.py`  
   Issue: hardcoded checkpoint filename, nondeterministic random outputs, and lint issues.  
   Resolution: latest-checkpoint auto-discovery + optional override, deterministic competitor/brand generation, deterministic trademark-risk scoring, and lint cleanup.

9. `generate_summaries.py`, `patent_summarizer.py`, `summarization_config.py`  
   Issue: duplicated prompt/model config and hardcoded absolute paths.  
   Resolution: centralized shared summarization config and environment-driven model location resolution.

10. `requirements.txt` and `requirements-optional.txt`  
    Issue: mixed baseline and optional stacks increased runtime surface and maintenance overhead.  
    Resolution: base dependencies split from optional AI stacks with clearer installation contract.

11. `docker-compose.yml` and `run_dashboard.sh`  
    Issue: broad default exposure for local dashboard serving.  
    Resolution: loopback-only bindings for local runs.

## Verification

- `ruff check .` -> all checks passed.  
- `python -m unittest discover -s tests -p 'test_*.py'` -> 25 tests passed.

## Coverage Statement

All files in `FILE_INVENTORY.md` were reviewed.  
Files not listed in findings above are acceptable as-is for code quality in this refactor pass.
