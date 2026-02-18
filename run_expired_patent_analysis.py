#!/usr/bin/env python3
"""
Expired Patent Business Intelligence Report Generator
Integrates crew.ai multi-agent analysis with deterministic framework.

Produces comprehensive ranking, recommendations, and executive summary.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Try to import crew components; will gracefully degrade if not available
try:
    from expired_patent_analysis_crew import ExpiredPatentAnalysisCrew
    CREW_AVAILABLE = True
except ImportError:
    CREW_AVAILABLE = False
    print("⚠️  CrewAI not available; will use framework-only analysis")

from patent_analysis_framework import (
    PatentAnalysisFramework,
    run_framework_analysis,
)


def generate_markdown_report(
    results: list,
    patents: list,
    json_export: Path,
    csv_export: Path,
    crew_result: Optional[Dict[str, Any]] = None,
) -> Path:
    """
    Generate comprehensive markdown report from analysis results.
    """

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = Path("./patent_intelligence_vault/") / (
        f"EXPIRED_PATENT_REPORT_{timestamp}.md"
    )

    # Calculate statistics
    tier_1_count = sum(
        1 for r in results if r.strategic_assessment.recommendation_tier == 1
    )
    tier_2_count = sum(
        1 for r in results if r.strategic_assessment.recommendation_tier == 2
    )
    avg_score = sum(r.integrated_score for r in results) / len(results)

    # Get top recommendations
    tier_1_results = [
        r
        for r in results
        if r.strategic_assessment.recommendation_tier == 1
    ][:5]
    tier_2_results = [
        r
        for r in results
        if r.strategic_assessment.recommendation_tier == 2
    ][:5]

    md_report = f"""# Expired Patent Business Intelligence Report

**Report Generated:** {datetime.now().isoformat()}  
**Dataset Size:** {len(patents)} patents  
**Report ID:** `{timestamp}`

---

## Executive Summary

This report presents a comprehensive analysis of {len(patents)} expired patents using a multi-dimensional framework combining technical robustness, manufacturing feasibility, financial attractiveness, and strategic alignment.

### Key Findings

- **Total Patents Analyzed:** {len(patents)}
- **High-Potential Candidates (Tier 1):** {tier_1_count} patents recommended for immediate implementation or pilot projects
- **Further Investigation Required (Tier 2):** {tier_2_count} patents requiring additional R&D or FTO analysis
- **Average Integrated Score:** {avg_score:.2f}/10.0

### Investment Opportunity Summary

The analysis identifies significant economic opportunity through reviving expired technologies:

- **Top Tier 1 Patent:** {tier_1_results[0].title if tier_1_results else "N/A"}
  - Score: {tier_1_results[0].integrated_score:.2f}/10.0
  - NPV (Base): ${tier_1_results[0].financial_metrics.npv_base:,.0f}

- **Estimated Portfolio NPV:** ${sum(r.financial_metrics.npv_base for r in results if r.financial_metrics):,.0f}
- **Primary Opportunity Themes:** {", ".join(set(r.technology_theme for r in results[:5]))}

---

## Analysis Methodology

### Scoring Framework

This report employs a transparent, weighted scoring model across seven dimensions:

| Dimension | Weight | Scale |
|-----------|--------|-------|
| Scientific Robustness | 15% | 1-10 (1=weak, 10=foundational) |
| Manufacturing Feasibility (Today) | 20% | 1-10 (1=specialized, 10=standard) |
| Modernization Potential | 15% | 1-10 (1=incompatible, 10=native fit) |
| Strategic/Market Fit | 20% | 1-10 (1=poor, 10=excellent) |
| Financial Attractiveness | 20% | Based on NPV trajectory |
| Legal/IP Risk (inverted) | 5% | Low/Medium/High → numeric |
| ESG/Sustainability Impact | 5% | Low/Medium/High → numeric |

**Integrated Score = Σ(dimension_score × weight)**

### Scoring Rubric

#### Scientific Robustness
- **1-2:** Weak theoretical basis; limited citations; narrow impact
- **3-4:** Sound principles; moderate citations; incremental novelty
- **5-6:** Solid foundation; good citation history; clear technical contribution
- **7-8:** Strong fundamentals; highly cited; influenced later work
- **9-10:** Foundational; seminal work; extensive impact on field

#### Manufacturing Feasibility
- **1-2:** Requires highly specialized equipment; exotic materials; yield unpredictable
- **3-4:** Specialized equipment; difficult sourcing; complex control
- **5-6:** Standard equipment; available materials; moderate process complexity
- **7-8:** Common equipment; commodity materials; well-understood process
- **9-10:** Off-the-shelf equipment; standard materials; simple, repeatable process

#### Modernization Potential
- **1-2:** Requires fundamental redesign; incompatible with modern tech
- **3-4:** Significant adaptation needed; partial legacy compatibility
- **5-6:** Moderate updates required; can integrate with modern systems
- **7-8:** Minor updates needed; readily compatible with current tech
- **9-10:** Native compatibility; natural fit with Industry 4.0, automation, IoT

---

## Top Ranked Patents

### Tier 1: Immediate Implementation Candidates

Tier 1 patents combine high technical merit, manufacturing feasibility, strategic alignment, and strong financial metrics. These are ready for pilot projects or phased implementation.

{"".join([f'''
#### {i+1}. **{result.title}**

**Patent Number:** {result.patent_number}  
**Score:** {result.integrated_score:.2f}/10.0 | **Confidence:** {result.confidence_level*100:.0f}%  
**Technology Theme:** {result.technology_theme.replace("_", " ").title()}  
**Recommendation:** Tier 1 - Implementation Ready

**Technical Profile:**
- Scientific Robustness: {result.technical_score.scientific_robustness:.1f}/10
- Manufacturing Feasibility: {result.technical_score.manufacturing_feasibility_current:.1f}/10
- Modernization Potential: {result.technical_score.modernization_potential:.1f}/10
- TRL Estimate: {result.manufacturing_profile.trl_estimate}/9

**Financial Metrics:**
- NPV (Base Case): ${result.financial_metrics.npv_base:,.0f}
- NPV (Optimistic): ${result.financial_metrics.npv_optimistic:,.0f}
- Payback Period: {result.financial_metrics.payback_period_years:.1f} years
- ROI: {result.financial_metrics.irr_percent:.1f}%

**Strategic Assessment:**
- Strategic Fit: {result.strategic_assessment.strategic_fit_score:.1f}/10
- Market Opportunity: {result.strategic_assessment.market_size_opportunity.upper()}
- Competitive Advantage: {result.strategic_assessment.competitive_advantage_potential:.1f}/10
- ESG Benefit: {result.strategic_assessment.esg_sustainability_benefit.upper()}

**Key Insights:**
- Capex Range: ${result.manufacturing_profile.capex_low:,.0f} - ${result.manufacturing_profile.capex_high:,.0f}
- Modernization Timeline: ~{result.manufacturing_profile.modernization_timeline_months} months
- Production Type: {result.manufacturing_profile.production_type.title()}

**Next Steps:**
{chr(10).join([f"  1. {step}" for step in result.strategic_assessment.next_steps[:3]])}

**Derivative IP Opportunities:**
{chr(10).join([f"  - {opp}" for opp in result.strategic_assessment.derivative_ip_opportunities[:2]])}

''' for i, result in enumerate(tier_1_results)])}

### Tier 2: Further Investigation Required

Tier 2 patents show promise but require additional R&D, FTO analysis, or validation before implementation.

{"".join([f'''
- **{result.patent_number}:** {result.title}
  - Score: {result.integrated_score:.2f}/10 | Action: {result.strategic_assessment.next_steps[0]}
''' for i, result in enumerate(tier_2_results[:3])])}

---

## Detailed Analysis Sections

### Data Classification Summary

Patents have been classified across the following technology themes:

| Theme | Count | Avg Score |
|-------|-------|-----------|
{chr(10).join([f"| {theme.replace('_', ' ').title()} | {count} | {score:.2f} |" for theme, count, score in [(t, len([r for r in results if r.technology_theme == t]),
sum(r.integrated_score for r in results if r.technology_theme == t) / max(1, len([r for r in results if r.technology_theme == t]))) for t in set(r.technology_theme for r in results)] if count > 0])}

### Financial Summary

| Metric | Value |
|--------|-------|
| Total Portfolio NPV (Base) | ${sum(r.financial_metrics.npv_base for r in results if r.financial_metrics):,.0f} |
| Total Portfolio NPV (Optimistic) | ${sum(r.financial_metrics.npv_optimistic for r in results if r.financial_metrics):,.0f} |
| Average Annual Cost Savings | ${sum(r.financial_metrics.annual_cost_savings for r in results if r.financial_metrics) / len(results):,.0f} |
| Average Payback Period | {sum(r.financial_metrics.payback_period_years for r in results if r.financial_metrics) / len(results):.1f} years |

---

## Risk Assessment & Compliance

### Legal & IP Risk
All patents in this dataset are **expired** and no longer enforceable in their original jurisdictions. However:
- **Further FTO Analysis Recommended:** For {sum(1 for r in results if "high" in r.red_flags)} patents with potential blocking technology concerns
- **Regulatory Review Required:** For {sum(1 for r in results if r.strategic_assessment.regulatory_risk == "high")} patents in regulated sectors

### ESG & Sustainability

| Benefit Level | Count | Representative Technology |
|---------------|-------|---------------------------|
| High | {sum(1 for r in results if r.strategic_assessment.esg_sustainability_benefit == "high")} | {next((r.technology_theme for r in results if r.strategic_assessment.esg_sustainability_benefit == "high"), "N/A")} |
| Medium | {sum(1 for r in results if r.strategic_assessment.esg_sustainability_benefit == "medium")} | {next((r.technology_theme for r in results if r.strategic_assessment.esg_sustainability_benefit == "medium"), "N/A")} |
| Low | {sum(1 for r in results if r.strategic_assessment.esg_sustainability_benefit == "low")} | {next((r.technology_theme for r in results if r.strategic_assessment.esg_sustainability_benefit == "low"), "N/A")} |

---

## Actionable Recommendations

### Immediate Actions (Month 1-2)

1. **Validate Top 3 Tier-1 Patents**
   - Literature review and freedom-to-operate (FTO) analysis
   - Preliminary cost-benefit validation
   - Equipment supplier outreach

2. **Regulatory Screening**
   - Identify sector-specific compliance requirements
   - Assess potential regulatory tailwinds (e.g., green credentials, safety modernization)

3. **Resource Planning**
   - Estimate pilot project budgets and timelines
   - Identify required cross-functional team composition
   - Establish success metrics and go/no-go decision points

### Medium-Term Execution (Quarter 2-3)

- **Pilot Projects:** Launch proof-of-concept on Tier 1 candidates
- **Detailed Engineering:** Modernization assessment and detailed design
- **Patent Applications:** Prepare derivative IP applications on improvements

### Long-Term Portfolio Strategy (Year 1-2)

- **Scale Implementation:** Transition successful pilots to production
- **Licensing Opportunities:** Evaluate technology transfer and licensing partnerships
- **Continuous Monitoring:** Track Tier 2 and Tier 3 patents for changing circumstances

---

## Data & Assumptions

### Key Assumptions

- **Discount Rate (WACC):** Industry-specific benchmarked cost of capital (Damodaran) blended with current macro risk-free rate.
- **Evaluation Period:** 10 years with scenario-based growth/margin/discount adjustments.
- **Macro Inputs:** Current inflation, producer-price trend, manufacturing wages, and capacity-utilization indicators (FRED).
- **Market Inputs:** Industry revenues and valuation multiples (EV/Sales) from public market comparables.
- **Production Volume:** Serviceable market sizing and adoption ramp calibrated by patent complexity and equipment profile.

### Data Limitations

- Patent abstracts may not fully capture implementation complexity
- Cited data is deterministic and should be validated with domain experts
- Market sizes and growth rates are proxy estimates; detailed market research recommended
- Regulatory environment may vary by jurisdiction

---

## Export Files

- **Full Results (JSON):** `{json_export.name}`
- **Rankings (CSV):** `{csv_export.name}`

The JSON export includes detailed technical scores, financial models, and strategic assessments for each patent. The CSV export provides quick-reference ranking for filtering and comparison.

---

## Document Information

**Methodology:** Multi-dimensional weighted scoring framework with deterministic technical, financial, and strategic assessment components.

**Report Version:** 1.0  
**Last Updated:** {datetime.now().isoformat()}  
**Next Review Recommended:** 90 days

---

*This report is confidential and intended for strategic decision-making regarding intellectual property acquisition and commercialization.*
"""

    with open(report_path, "w") as f:
        f.write(md_report)

    print(f"\n✓ Report generated: {report_path}")
    return report_path


def run_comprehensive_analysis(
    patent_discoveries_file: Optional[str] = None,
    enable_crew: bool = False,
) -> Dict[str, Any]:
    """
    Execute comprehensive expired patent analysis pipeline.

    Args:
        patent_discoveries_file: Path to patent discoveries JSON
        enable_crew: If True and available, run crew.ai analysis additionally

    Returns:
        Analysis summary dictionary
    """

    print("=" * 80)
    print("EXPIRED PATENT BUSINESS INTELLIGENCE ANALYSIS")
    print("=" * 80)

    # Find latest discoveries if not specified
    if not patent_discoveries_file:
        vault_dir = Path("./patent_intelligence_vault/")
        discovery_files = sorted(vault_dir.glob("patent_discoveries_*.json"))
        if not discovery_files:
            raise FileNotFoundError("No patent discovery files found")
        patent_discoveries_file = str(discovery_files[-1])
        print(f"\n✓ Using latest discoveries: {patent_discoveries_file}\n")

    # Load patent data
    with open(patent_discoveries_file, "r") as f:
        patents = json.load(f)

    print(f"✓ Loaded {len(patents)} patents")

    # Run framework analysis
    print("\n" + "-" * 80)
    print("FRAMEWORK ANALYSIS")
    print("-" * 80)

    results, json_export, csv_export = run_framework_analysis(
        patent_discoveries_file
    )

    # Generate markdown report
    report_path = generate_markdown_report(
        results,
        patents,
        json_export,
        csv_export,
    )

    summary = {
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "patents_analyzed": len(patents),
        "tier_1_count": sum(
            1
            for r in results
            if r.strategic_assessment.recommendation_tier == 1
        ),
        "tier_2_count": sum(
            1
            for r in results
            if r.strategic_assessment.recommendation_tier == 2
        ),
        "tier_3_count": sum(
            1
            for r in results
            if r.strategic_assessment.recommendation_tier == 3
        ),
        "top_patent": results[0].patent_number if results else None,
        "top_patent_score": results[0].integrated_score if results else 0,
        "json_export": str(json_export),
        "csv_export": str(csv_export),
        "markdown_report": str(report_path),
    }

    # Optionally run crew analysis if enabled and available
    if enable_crew and CREW_AVAILABLE:
        print("\n" + "-" * 80)
        print("CREW.AI MULTI-AGENT ANALYSIS")
        print("-" * 80)
        try:
            crew = ExpiredPatentAnalysisCrew()
            crew_result = crew.analyze_patents(patents[:50])  # Sample for crew
            summary["crew_analysis"] = str(crew_result)
        except Exception as e:
            print(f"⚠️  Crew analysis failed: {e}")

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"\nSummary:\n{json.dumps(summary, indent=2)}")

    return summary


if __name__ == "__main__":
    enable_crew = "--with-crew" in sys.argv
    result = run_comprehensive_analysis(enable_crew=enable_crew)
    sys.exit(0 if result["status"] == "success" else 1)
