# Financial Audit

Date: 2026-02-18  
Scope: financial assumptions, formulas, scenario modeling, and financial labels across code, UI, docs, and generated outputs.

## Flagged Figures, Issues, and Replacements

1. File: `patent_analysis_framework.py:370`  
   Flagged figure: simplistic legacy cash-flow linkage to capex.  
   Issue: investment amount alone is not a defensible proxy for annual economic benefit.  
   Replacement: market-profile assumptions now drive annual savings and revenue uplift with domain-calibrated rates (`savings_rate`, `revenue_rate`).  
   Rationale: ties value creation to demand and operational context instead of capex size.

2. File: `patent_analysis_framework.py:456`  
   Flagged issue: incomplete free-cash-flow treatment in prior model.  
   Replacement: annual free cash flow now includes operating expense change, overhead allocation, maintenance capital, tax, depreciation effect, churn/refund drag, customer acquisition cost, and working-capital delta.  
   Rationale: reflects standard operating valuation components and removes optimistic bias.

3. File: `patent_analysis_framework.py:425`, `patent_analysis_framework.py:431`, `patent_analysis_framework.py:437`  
   Flagged figure: single discount-rate assumption in prior implementation.  
   Replacement: scenario rates are now conservative `12%`, base `10%`, optimistic `8%`.  
   Rationale: aligns with the 8-12% defensible range and introduces risk sensitivity.

4. File: `patent_analysis_framework.py:445`  
   Flagged figure: unconstrained growth risk in projections.  
   Replacement: scenario growth is capped (`growth_rate_cap = 0.12`) and base growth is bounded by domain profiles.  
   Rationale: prevents unrealistic expansion trajectories.

5. File: `patent_analysis_framework.py:340`  
   Flagged issue: non-financial proxy used for return metric in prior implementation.  
   Replacement: internal rate now computed from full cash-flow arrays via bounded bisection (`estimate_internal_rate_percent`).  
   Rationale: mathematically correct return metric based on discounted cash flows.

6. File: `patent_analysis_framework.py:302`  
   Flagged figure: coarse capex buckets in prior implementation.  
   Replacement: capex/opex now scale by complexity, equipment intensity, and material intensity (`estimate_manufacturing_profile`).  
   Rationale: increases dispersion realism across different patent types.

7. File: `patent_analysis_framework.py:412`  
   Flagged omission: missing tax/depreciation/maintenance/working-capital assumptions in prior model.  
   Replacement values:  
   - tax rate `25%`  
   - depreciation `7 years`  
   - maintenance capital `2%` of capex annually  
   - working capital rate `5%`  
   - overhead rate `12%`  
   Rationale: baseline business-case assumptions commonly used in operating valuation.

8. Files: `run_expired_patent_analysis.py`, `streamlit_app.py`, `patent_analysis_framework.py`, `expired_patent_analysis_crew.py`, docs and vault exports  
   Flagged issue: abbreviation-only financial labeling.  
   Replacement: all labels and keys now use full-form `Net Present Value` naming (`net_present_value_base`, `Net_Present_Value_Base`, UI labels with full text).  
   Rationale: terminology consistency and explicit metric meaning.

9. File: `README.md`  
   Flagged issue: static portfolio totals and stale fixed claims in prior documentation.  
   Replacement: README now documents workflow and commands without fixed portfolio total claims.  
   Rationale: avoids stale numbers and keeps docs aligned with generated outputs.

## Financial Output Refresh

A fresh analysis run was generated after refactor:
- `patent_intelligence_vault/patent_analysis_results_20260217_221146.json`
- `patent_intelligence_vault/patent_rankings_20260217_221146.csv`
- `patent_intelligence_vault/EXPIRED_PATENT_REPORT_20260217_221146.md`

These outputs reflect the refactored scenario model and full-form naming.

## Coverage Statement

All files in `FILE_INVENTORY.md` were reviewed for financial content.  
Files not listed above did not contain materially actionable financial assumptions or formulas in this pass.
