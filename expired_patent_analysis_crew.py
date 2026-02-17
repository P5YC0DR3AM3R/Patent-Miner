#!/usr/bin/env python3
"""
Expired Patent Business Intelligence Pipeline
Multi-agent crew for comprehensive patent analysis, ranking, and recommendations.

Uses crew.ai to orchestrate:
- Patent Analyst: Technical classification and robustness assessment
- Manufacturing Engineer: Feasibility and modernization evaluation
- IP Finance Specialist: Economic valuation and financial metrics
- Technology Strategist: Market fit, competitive advantage, and recommendations
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from crewai import Agent, Crew, Task
from langchain_openai import ChatOpenAI

# Import existing Patent Miner utilities
from patent_miner_config import build_config


class ExpiredPatentAnalysisCrew:
    """Orchestrates multi-agent analysis of expired patents."""

    def __init__(self, api_key: str | None = None, model: str = "gpt-4"):
        """Initialize crew with LLM configuration."""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.llm = ChatOpenAI(
            model_name=model,
            api_key=self.api_key,
            temperature=0.3,
            max_tokens=4096,
        )
        self.crew = None
        self.output_dir = "./patent_intelligence_vault/"
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

    def create_agents(self) -> Dict[str, Agent]:
        """Create specialized agent roles for patent analysis."""

        patent_analyst = Agent(
            role="Senior Patent Analyst",
            goal="Perform rigorous technical classification, extract core innovation, assess scientific robustness, and evaluate manufacturing feasibility of expired patents.",
            backstory=(
                "Expert patent analyst with 15+ years of experience in technology classification, "
                "patent citation analysis, and technical due diligence. Specializes in identifying "
                "foundational vs incremental innovations and assessing the scientific quality and "
                "durability of disclosed technologies."
            ),
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
        )

        manufacturing_engineer = Agent(
            role="Manufacturing Process Engineer",
            goal="Evaluate technical feasibility of manufacturing, identify required equipment and materials, assess scale-up considerations, and estimate modernization requirements for integrating expired patents with current technology.",
            backstory=(
                "Seasoned manufacturing engineer with expertise in process design, scale-up, "
                "equipment selection, and process intensification. Has led successful adoption "
                "of legacy technologies in modern facilities and understands TRL progression, "
                "critical failure modes, and integration challenges."
            ),
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
        )

        finance_specialist = Agent(
            role="Corporate Finance & IP Valuation Specialist",
            goal="Perform comprehensive financial evaluation of expired patents, including capex/opex estimation, revenue impact modeling, NPV analysis, and multi-perspective technology valuation.",
            backstory=(
                "IP valuation expert and corporate finance professional with 12+ years conducting "
                "technology assessments, licensing negotiations, and technology transfer valuations. "
                "Skilled in DCF modeling, scenario analysis, and applying cost, income, and market "
                "approaches to technology IP."
            ),
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
        )

        tech_strategist = Agent(
            role="Technology Strategist",
            goal="Assess market dynamics, competitive positioning, strategic fit with company capabilities, identify opportunities for derivative IP creation, and develop actionable implementation recommendations.",
            backstory=(
                "Strategic advisor focused on technology roadmapping and market positioning. "
                "Understands emerging trends, competitive landscapes, and how legacy technologies "
                "can create competitive advantage through strategic deployment and modernization. "
                "Expert in identifying second-order effects and derivative patent opportunities."
            ),
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
        )

        return {
            "patent_analyst": patent_analyst,
            "manufacturing_engineer": manufacturing_engineer,
            "finance_specialist": finance_specialist,
            "tech_strategist": tech_strategist,
        }

    def create_tasks(
        self, agents: Dict[str, Agent], patent_data: List[Dict[str, Any]]
    ) -> List[Task]:
        """Create analysis tasks for each agent."""

        patent_summary = json.dumps(patent_data[:5], indent=2)  # Include first 5 for context
        dataset_size = len(patent_data)

        task_classification = Task(
            description=(
                f"You are analyzing a dataset of {dataset_size} expired patents.\n\n"
                "STEP 1: DATA CLEANING & CLASSIFICATION\n"
                "1. Identify and flag potential duplicates or related patent families.\n"
                "2. Classify each patent by type (Process, Product, System, Enabling Technology).\n"
                "3. Assign CPC/IPC technology themes (e.g., Materials, Sensors, Control Systems, Manufacturing).\n"
                "4. Map to target applications and industries.\n\n"
                "STEP 2: TECHNICAL ASSESSMENT\n"
                "1. Extract core innovation and scientific principle for each patent family.\n"
                "2. Score SCIENTIFIC ROBUSTNESS (1-10):\n"
                "   - Consider: claim breadth, citation count, foundational nature, influence on later work.\n"
                "3. Assess technical novelty indicators (citation patterns, family size, longevity).\n"
                "4. Identify core vs incremental innovations.\n\n"
                "STEP 3: MANUFACTURING FEASIBILITY (TODAY)\n"
                "1. Score MANUFACTURING FEASIBILITY (1-10):\n"
                "   - Consider: equipment availability, material cost/regulatory status, process complexity, yield predictability.\n"
                "2. Identify critical materials and equipment needed.\n"
                "3. Flag process-window tightness and scale-up risk.\n\n"
                "STEP 4: IMPLEMENTATION RISK\n"
                "1. Estimate TRL (Technology Readiness Level 1-9) for current deployment.\n"
                "2. Score TECHNICAL RISK (inverted: 10=low risk, 1=high risk).\n"
                "3. Flag potential blocking patents or FTO concerns.\n\n"
                f"SAMPLE PATENTS:\n{patent_summary}\n\n"
                "Produce a JSON output with:\n"
                "{\n"
                '  "classification": [...],\n'
                '  "technical_scores": {\n'
                '    "patent_id": {\n'
                '      "scientific_robustness": X,\n'
                '      "manufacturing_feasibility": X,\n'
                '      "trl_estimate": X,\n'
                '      "technical_risk_inverted": X,\n'
                '      "key_materials": [...],\n'
                '      "required_equipment": [...],\n'
                '      "core_innovation": "...",\n'
                '      "fto_concerns": "..."\n'
                '    }\n'
                '  }\n'
                "}\n"
            ),
            agent=agents["patent_analyst"],
            expected_output="Comprehensive technical classification and scoring analysis",
        )

        task_manufacturing = Task(
            description=(
                "MODERNIZATION & MANUFACTURING INTEGRATION ASSESSMENT\n\n"
                "For each patent analyzed:\n"
                "1. Score MODERNIZATION POTENTIAL (1-10):\n"
                "   - Integration with modern automation, process control, IoT/data systems.\n"
                "   - Substitution opportunities for obsolete materials/equipment.\n"
                "   - Process intensification and energy efficiency improvements.\n\n"
                "2. SCALE-UP ANALYSIS:\n"
                "   - Batch vs continuous production suitability.\n"
                "   - Identify critical bottlenecks and scale constraints.\n"
                "   - Modularity and flexibility for different capacity levels.\n\n"
                "3. CAPEX ESTIMATION:\n"
                "   - Equipment retrofit or new build cost ranges.\n"
                "   - Integration complexity and timeline.\n"
                "   - Risk factors and contingencies.\n\n"
                "4. OPEX IMPACT:\n"
                "   - Raw material cost changes (vs baseline).\n"
                "   - Energy and utility consumption trends.\n"
                "   - Labor and maintenance requirements.\n\n"
                "Produce JSON with:\n"
                "{\n"
                '  "manufacturing_assessment": {\n'
                '    "patent_id": {\n'
                '      "modernization_potential": X,\n'
                '      "capex_estimate_low": $,\n'
                '      "capex_estimate_high": $,\n'
                '      "opex_annual_change": $,\n'
                '      "production_type": "batch|continuous|hybrid",\n'
                '      "scale_bottlenecks": [...],\n'
                '      "modernization_timeline_months": X,\n'
                '      "key_risks": [...]\n'
                '    }\n'
                '  }\n'
                "}\n"
            ),
            agent=agents["manufacturing_engineer"],
            expected_output="Manufacturing feasibility and capex/opex analysis",
        )

        task_financial = Task(
            description=(
                "FINANCIAL & ECONOMIC VALUATION\n\n"
                "For each patent or patent family:\n"
                "1. COST ANALYSIS:\n"
                "   - Capex ranges (low, mid, high scenarios).\n"
                "   - Annual opex changes and drivers.\n"
                "   - Regulatory and compliance costs.\n\n"
                "2. REVENUE & VALUE IMPACT:\n"
                "   - Cost savings per unit (vs current production).\n"
                "   - Pricing and premium potential (quality/performance uplift).\n"
                "   - Volume expansion or capacity increase potential.\n"
                "   - Licensing revenue opportunity.\n\n"
                "3. VALUATION (MULTI-PERSPECTIVE):\n"
                "   - Income Approach: NPV of cost savings or revenue gains (10-year DCF, 8% WACC).\n"
                "   - Cost Approach: reproduction cost of developing equivalent technology independently.\n"
                "   - Market Approach: comparable licensing terms or technology transaction prices.\n\n"
                "4. KEY METRICS:\n"
                "   - NPV (base, optimistic, pessimistic scenarios).\n"
                "   - Payback period (years).\n"
                "   - IRR or ROI.\n"
                "   - Sensitivity analysis: commodity prices, demand growth, capex overruns.\n\n"
                "Produce JSON with:\n"
                "{\n"
                '  "financial_analysis": {\n'
                '    "patent_id": {\n'
                '      "npv_base": $,\n'
                '      "npv_optimistic": $,\n'
                '      "npv_pessimistic": $,\n'
                '      "payback_period_years": X,\n'
                '      "irr": X%,\n'
                '      "cost_savings_annual": $,\n'
                '      "revenue_uplift_annual": $,\n'
                '      "valuation_low": $,\n'
                '      "valuation_mid": $,\n'
                '      "valuation_high": $,\n'
                '      "key_assumptions": {...}\n'
                '    }\n'
                '  }\n'
                "}\n"
            ),
            agent=agents["finance_specialist"],
            expected_output="Comprehensive financial valuation and scenario analysis",
        )

        task_strategy = Task(
            description=(
                "STRATEGIC FIT, MARKET OPPORTUNITY & RECOMMENDATIONS\n\n"
                "1. MARKET CONTEXT:\n"
                "   - Target product/application market size and growth trends.\n"
                "   - Commoditization vs differentiation potential.\n"
                "   - Geographic and industry applicability.\n\n"
                "2. STRATEGIC ALIGNMENT:\n"
                "   - Fit with cost leadership, premium, sustainability, or speed-to-market strategies.\n"
                "   - Support for process optimization vs new product creation vs market expansion.\n"
                "   - Alignment with technology roadmap and competitive positioning.\n\n"
                "3. FREEDOM & OPTION VALUE:\n"
                "   - Advantages of expired patent (royalty-free, low enforcement risk).\n"
                "   - Opportunity to develop derivative improvements as new IP.\n"
                "   - Licensing or partnership potential.\n\n"
                "4. RISK ASSESSMENT:\n"
                "   - Legal/IP risk (active improvement patents, FTO gaps).\n"
                "   - Regulatory/compliance headwinds or tailwinds.\n"
                "   - ESG impact (energy, emissions, waste, sustainability benefit).\n\n"
                "5. TIERED RECOMMENDATIONS:\n"
                "   - TIER 1: Immediate implementation or pilot projects.\n"
                "   - TIER 2: Further R&D or detailed FTO analysis.\n"
                "   - TIER 3: Monitor or deprioritize.\n\n"
                "For each Tier 1/2 candidate:\n"
                "   - Next steps and timeline.\n"
                "   - Data/validation required.\n"
                "   - Derivative IP opportunities.\n\n"
                "Produce JSON with:\n"
                "{\n"
                '  "strategic_assessment": {\n'
                '    "patent_id": {\n'
                '      "strategic_fit_score": X,\n'
                '      "competitive_advantage_potential": X,\n'
                '      "market_opportunity": "low|medium|high",\n'
                '      "legal_ip_risk": "low|medium|high",\n'
                '      "regulatory_risk": "low|medium|high",\n'
                '      "esg_benefit": "low|medium|high",\n'
                '      "recommendation_tier": "1|2|3",\n'
                '      "next_steps": [...],\n'
                '      "derivative_ip_opportunities": [...]\n'
                '    }\n'
                '  },\n'
                '  "executive_summary": "...",\n'
                '  "top_3_recommendations": [...]\n'
                "}\n"
            ),
            agent=agents["tech_strategist"],
            expected_output="Strategic recommendations and tiered action plan",
        )

        task_integrated_report = Task(
            description=(
                "INTEGRATED RANKING & EXECUTIVE REPORT\n\n"
                "Using all previous analyses, create unified ranking:\n\n"
                "1. INTEGRATED SCORING FRAMEWORK:\n"
                "   Weights:\n"
                "   - Scientific Robustness: 15%\n"
                "   - Manufacturing Feasibility: 20%\n"
                "   - Modernization Potential: 15%\n"
                "   - Strategic/Market Fit: 20%\n"
                "   - Financial Attractiveness: 20%\n"
                "   - IP/Legal Risk (inverted): 5%\n"
                "   - ESG/Sustainability: 5%\n\n"
                "2. FINAL RANKING TABLE:\n"
                "   - Rank, Patent ID, Technology, Total Score, Top 3 Factors, Red Flags, Recommendation\n\n"
                "3. EXECUTIVE SUMMARY (500-750 words):\n"
                "   - Overview of dataset and analysis approach\n"
                "   - Top tier recommendations with expected economic impact\n"
                "   - Key technical and legal caveats\n"
                "   - Immediate action items\n\n"
                "4. ACTION PLAN (Tier 1 & Tier 2):\n"
                "   - Pilot projects and validation requirements\n"
                "   - Risk mitigation strategies\n"
                "   - Timeline and resource estimates\n\n"
                "Output comprehensive JSON report ready for export to markdown/PDF.\n"
            ),
            agent=agents["tech_strategist"],
            expected_output="Integrated final ranking report and executive summary",
        )

        return [
            task_classification,
            task_manufacturing,
            task_financial,
            task_strategy,
            task_integrated_report,
        ]

    def analyze_patents(self, patent_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute crew analysis pipeline on patent dataset."""

        if not patent_data:
            raise ValueError("No patent data provided for analysis")

        print("\n" + "=" * 80)
        print("EXPIRED PATENT BUSINESS INTELLIGENCE ANALYSIS")
        print("=" * 80)
        print(f"Analyzing {len(patent_data)} patents...")
        print(f"Starting crew execution at {datetime.now().isoformat()}\n")

        agents = self.create_agents()
        tasks = self.create_tasks(agents, patent_data)

        self.crew = Crew(
            agents=list(agents.values()),
            tasks=tasks,
            verbose=True,
            max_iter=2,
        )

        result = self.crew.kickoff()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = Path(self.output_dir) / f"expired_patent_analysis_{timestamp}.json"

        analysis_output = {
            "timestamp": timestamp,
            "dataset_size": len(patent_data),
            "analysis_result": str(result),
            "crew_tasks_count": len(tasks),
        }

        with open(report_path, "w") as f:
            json.dump(analysis_output, f, indent=2)

        print(f"\n✓ Analysis complete. Report saved to: {report_path}")

        return analysis_output

    def generate_markdown_report(
        self, analysis_result: Dict[str, Any]
    ) -> str:
        """Convert analysis result to markdown report."""

        timestamp = analysis_result.get("timestamp", "unknown")
        report_md = f"""# Expired Patent Business Intelligence Report

**Generated:** {datetime.now().isoformat()}  
**Dataset Size:** {analysis_result.get('dataset_size')} patents  
**Analysis ID:** `{timestamp}`

## Executive Summary

[Detailed analysis from crew to follow]

## Analysis Components

1. **Classification & Technical Assessment**
2. **Manufacturing Feasibility & Modernization**
3. **Financial Valuation**
4. **Strategic Fit & Recommendations**
5. **Integrated Ranking & Action Plan**

---

## Detailed Analysis Results

```json
{json.dumps(analysis_result, indent=2)}
```

"""
        return report_md


def run_expired_patent_analysis(
    patent_discoveries_file: str | None = None,
    output_format: str = "json",
) -> Dict[str, Any]:
    """
    Main entry point: Load patent discoveries and run crew analysis.

    Args:
        patent_discoveries_file: Path to patent_discoveries JSON file.
                                If None, uses latest file in vault.
        output_format: 'json' or 'markdown'

    Returns:
        Analysis results dictionary
    """

    # Find latest discoveries file if not specified
    if not patent_discoveries_file:
        vault_dir = Path("./patent_intelligence_vault/")
        discovery_files = sorted(vault_dir.glob("patent_discoveries_*.json"))
        if not discovery_files:
            raise FileNotFoundError(
                "No patent discovery files found in patent_intelligence_vault/"
            )
        patent_discoveries_file = str(discovery_files[-1])
        print(f"Using latest discoveries file: {patent_discoveries_file}")

    # Load patent data
    with open(patent_discoveries_file, "r") as f:
        patent_data = json.load(f)

    print(f"Loaded {len(patent_data)} patents from {patent_discoveries_file}")

    # Run crew analysis
    crew = ExpiredPatentAnalysisCrew()
    result = crew.analyze_patents(patent_data)

    # Generate markdown report if requested
    if output_format == "markdown":
        md_report = crew.generate_markdown_report(result)
        md_path = Path(crew.output_dir) / result["timestamp"] / "report.md"
        md_path.parent.mkdir(parents=True, exist_ok=True)
        with open(md_path, "w") as f:
            f.write(md_report)
        print(f"Markdown report saved to: {md_path}")

    return result


if __name__ == "__main__":
    result = run_expired_patent_analysis(output_format="json")
    print("\nAnalysis complete!")
