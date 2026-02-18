# Financial Viability Model (MCP Stack)

Date: 2026-02-18

## Online valuation reference used

Primary methodology reference:
- WIPO: *IP Valuation in Uncertain Times* (edition 2024)  
  https://www.wipo.int/edocs/pubdocs/en/wipo_pub_1094.pdf

This reference describes a multi-method IP valuation structure:
- Income approach (discounted cash-flow / NPV)
- Market approach (comparables and multiples)
- Cost approach (replacement/reproduction economics)
- Scenario and uncertainty handling for valuation ranges

## Live data sources wired into the stack

Industry benchmark layer (Damodaran datasets):
- Cost of capital by industry:  
  https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/wacc.html
- Margins by industry:  
  https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/margin.html
- Cash-flow drivers by industry:  
  https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/cfbasics.html
- EV/Sales and P/S by industry:  
  https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/psdata.html
- Industry market cap / EV / revenue aggregates:  
  https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/DollarUS.html

Macro/manufacturing signal layer (FRED series):
- `DGS10` (10y Treasury proxy for risk-free)
- `CPIAUCSL` (inflation)
- `PPIACO` (producer-price trend)
- `CES3000000008` (manufacturing wages)
- `CUMFNS` (manufacturing capacity utilization)
- `GDPC1` (real GDP trend)

## Model structure implemented

1. Resolve patent -> benchmark industry.
2. Build manufacturing profile from patent text + macro/industry intensities.
3. Build 10-year free-cash-flow scenarios (optimistic, base, pessimistic):
   - Revenue growth and adoption ramp
   - Operating margin and tax
   - Growth capex + maintenance capex
   - Working capital delta
   - Additional annual opex drag
4. Discount cash flows with benchmarked cost of capital (macro-adjusted).
5. Compute:
   - NPV (`npv_pessimistic`, `npv_base`, `npv_optimistic`)
   - IRR (`irr_percent`) via bounded bisection
   - Payback
   - Market/product value estimate (EV/Sales-based)
6. Run deterministic Monte Carlo envelope to generate risk-adjusted NPV band:
   - `risk_adjusted_npv_p10`
   - `risk_adjusted_npv_p90`

## Outputs now exposed in BI

- Base/optimistic/pessimistic NPV
- Product value estimate
- Serviceable market estimate
- Risk-adjusted NPV confidence band (P10/P90)
- Benchmark industry used for each patent
