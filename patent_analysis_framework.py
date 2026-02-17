#!/usr/bin/env python3
"""
Comprehensive Expired Patent Analysis Framework
Structured scoring, financial modeling, and integrated ranking.

This module provides:
- Deterministic technical and financial scoring
- Multi-method valuation
- Risk assessment and ESG evaluation
- Weighted integrated ranking
- Actionable recommendations
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


@dataclass
class TechnicalScore:
    """Technical assessment dimensions."""

    scientific_robustness: float  # 1-10
    manufacturing_feasibility_current: float  # 1-10
    modernization_potential: float  # 1-10
    technical_implementation_risk_inverted: float  # 1-10 (10=low risk)


@dataclass
class ManufacturingProfile:
    """Manufacturing requirements and capabilities."""

    required_materials: List[str] = field(default_factory=list)
    required_equipment: List[str] = field(default_factory=list)
    process_complexity: str = "medium"  # low, medium, high
    trl_estimate: int = 6
    capex_low: float = 0.0
    capex_high: float = 0.0
    opex_annual_change: float = 0.0
    production_type: str = "batch"  # batch, continuous, hybrid
    modernization_timeline_months: int = 12
    critical_bottlenecks: List[str] = field(default_factory=list)


@dataclass
class FinancialMetrics:
    """Financial evaluation and valuation outputs."""

    npv_base: float
    npv_optimistic: float
    npv_pessimistic: float
    payback_period_years: float
    irr_percent: float
    annual_cost_savings: float
    annual_revenue_uplift: float
    valuation_low: float
    valuation_mid: float
    valuation_high: float
    key_assumptions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategicAssessment:
    """Strategic fit and market positioning."""

    strategic_fit_score: float  # 1-10
    competitive_advantage_potential: float  # 1-10
    market_size_opportunity: str  # small, medium, large
    legal_ip_risk: str  # low, medium, high
    regulatory_risk: str  # low, medium, high
    esg_sustainability_benefit: str  # low, medium, high
    recommendation_tier: int  # 1, 2, or 3
    next_steps: List[str] = field(default_factory=list)
    derivative_ip_opportunities: List[str] = field(default_factory=list)


@dataclass
class PatentAnalysisResult:
    """Comprehensive analysis result for a single patent."""

    patent_number: str
    title: str
    abstract: str
    filing_date: str
    patent_date: str
    assignee_type: str
    cpc_codes: List[str] = field(default_factory=list)
    technology_theme: str = "uncategorized"
    patent_type_classified: str = "product"
    technical_score: Optional[TechnicalScore] = None
    manufacturing_profile: Optional[ManufacturingProfile] = None
    financial_metrics: Optional[FinancialMetrics] = None
    strategic_assessment: Optional[StrategicAssessment] = None
    integrated_score: float = 0.0
    ranking_position: Optional[int] = None
    confidence_level: float = 0.5  # 0-1
    red_flags: List[str] = field(default_factory=list)
    key_insights: List[str] = field(default_factory=list)


class PatentAnalysisFramework:
    """Deterministic analytical framework for expired patents."""

    # Scoring rubric (displayed once for consistency)
    SCORING_RUBRIC = {
        "scientific_robustness": {
            "1-2": "Weak theoretical basis; limited citations; narrow impact",
            "3-4": "Sound principles; moderate citations; incremental novelty",
            "5-6": "Solid foundation; good citation history; clear technical contribution",
            "7-8": "Strong fundamentals; highly cited; influenced later work",
            "9-10": "Foundational; seminal work; extensive impact on field",
        },
        "manufacturing_feasibility": {
            "1-2": "Requires highly specialized equipment; exotic materials; yield unpredictable",
            "3-4": "Specialized equipment; difficult sourcing; complex control",
            "5-6": "Standard equipment; available materials; moderate process complexity",
            "7-8": "Common equipment; commodity materials; well-understood process",
            "9-10": "Off-the-shelf equipment; standard materials; simple, repeatable process",
        },
        "modernization_potential": {
            "1-2": "Requires fundamental redesign; incompatible with modern tech",
            "3-4": "Significant adaptation needed; partial legacy compatibility",
            "5-6": "Moderate updates required; can integrate with modern systems",
            "7-8": "Minor updates needed; readily compatible with current tech",
            "9-10": "Native compatibility; natural fit with Industry 4.0, automation, IoT",
        },
    }

    def __init__(self, output_dir: str = "./patent_intelligence_vault/"):
        """Initialize framework."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[PatentAnalysisResult] = []
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def classify_patent(
        self, patent: Dict[str, Any]
    ) -> Tuple[str, str, List[str]]:
        """
        Classify patent by technology theme and type.

        Returns: (technology_theme, patent_type, cpc_codes)
        """
        title = patent.get("title", "").lower()
        abstract = patent.get("abstract", "").lower()
        combined_text = f"{title} {abstract}"

        # Simple heuristic classification
        themes = {
            "sensors": ["sensor", "detector", "monitor", "measure"],
            "materials": ["material", "alloy", "polymer", "composite", "coating"],
            "process": ["method", "process", "reaction", "synthesis", "treatment"],
            "control_systems": ["control", "feedback", "regulation", "automation"],
            "apparatus": ["device", "apparatus", "instrument", "equipment"],
            "wireless": ["wireless", "radio", "transmit", "receiver", "communication"],
            "energy": ["energy", "power", "battery", "fuel", "motor"],
        }

        detected_themes = []
        for theme, keywords in themes.items():
            if any(kw in combined_text for kw in keywords):
                detected_themes.append(theme)

        theme = detected_themes[0] if detected_themes else "enabling_technology"

        # Patent type classification
        if (
            "method" in combined_text
            or "process" in combined_text
            or "comprises" in abstract
        ):
            patent_type = "process"
        elif "apparatus" in combined_text or "device" in combined_text:
            patent_type = "apparatus"
        else:
            patent_type = "product"

        return theme, patent_type, detected_themes

    def score_technical_dimensions(
        self,
        patent: Dict[str, Any],
        theme: str,
        patent_type: str,
    ) -> TechnicalScore:
        """
        Score technical dimensions using deterministic heuristics.
        """
        abstract = patent.get("abstract", "")
        title = patent.get("title", "")
        combined = f"{title} {abstract}".lower()

        # Robustness indicators
        robustness = 5.0
        if len(abstract) > 800:
            robustness += 1.5
        if "comprise" in combined or "comprising" in combined:
            robustness += 0.5
        if "advantage" in combined or "improvement" in combined:
            robustness += 0.5
        robustness = min(10.0, robustness)

        # Manufacturing feasibility signals
        feasibility = 5.0
        if "temperature" in combined and "pressure" in combined:
            feasibility += 1.0  # Controlled process parameters
        if "sensor" in theme:
            feasibility += 1.5  # Electronics generally scalable
        if "apparatus" in patent_type:
            feasibility += 0.5
        if any(word in combined for word in ["complex", "difficult", "challenging"]):
            feasibility -= 1.0
        feasibility = np.clip(feasibility, 1.0, 10.0)

        # Modernization potential: newer tech more integrable
        modernization = 6.0
        filing_year = int(patent.get("filing_date", "2000-01-01")[:4])
        if filing_year > 1990:
            modernization += 1.5
        if "automatic" in combined or "digital" in combined or "electronic" in combined:
            modernization += 1.5
        if "wireless" in combined or "network" in combined:
            modernization += 1.0
        modernization = np.clip(modernization, 1.0, 10.0)

        # Technical risk (inverted)
        risk_inverted = 7.0
        if "simple" in combined or "straightforward" in combined:
            risk_inverted += 1.5
        if any(
            word in combined
            for word in ["hazardous", "complex", "sensitive", "unstable"]
        ):
            risk_inverted -= 2.0
        risk_inverted = np.clip(risk_inverted, 1.0, 10.0)

        return TechnicalScore(
            scientific_robustness=robustness,
            manufacturing_feasibility_current=feasibility,
            modernization_potential=modernization,
            technical_implementation_risk_inverted=risk_inverted,
        )

    def estimate_manufacturing_profile(
        self, patent: Dict[str, Any], patent_type: str
    ) -> ManufacturingProfile:
        """Estimate manufacturing requirements and constraints."""

        abstract = patent.get("abstract", "").lower()
        title = patent.get("title", "").lower()
        combined = f"{title} {abstract}"

        profile = ManufacturingProfile()

        # Material inference
        material_keywords = {
            "metal": ["aluminum", "steel", "copper", "titanium", "iron", "alloy"],
            "polymer": [
                "plastic",
                "polymer",
                "resin",
                "polyester",
                "polyethylene",
            ],
            "ceramic": ["ceramic", "glass", "silicon", "oxide"],
        }
        for material_class, keywords in material_keywords.items():
            if any(kw in combined for kw in keywords):
                profile.required_materials.append(material_class)

        # Equipment inference
        equipment_keywords = {
            "reactor": ["reaction", "reactor", "synthesis", "mix"],
            "sensor": ["sensor", "detector", "measurement"],
            "pcb_assembly": ["circuit", "board", "electronics", "electronic"],
            "coating": ["coat", "deposit", "layer", "spray"],
        }
        for equip, keywords in equipment_keywords.items():
            if any(kw in combined for kw in keywords):
                profile.required_equipment.append(equip)

        # Process complexity
        if any(word in combined for word in ["complex", "multistep", "sequential"]):
            profile.process_complexity = "high"
        elif any(word in combined for word in ["simple", "straightforward"]):
            profile.process_complexity = "low"

        # TRL estimate (assuming disclosed but unlicensed)
        filing_year = int(patent.get("filing_date", "2000-01-01")[:4])
        if filing_year > 2000:
            profile.trl_estimate = 7
        else:
            profile.trl_estimate = 6

        # Capex estimation (rough)
        if "apparatus" in patent_type:
            profile.capex_low = 50000
            profile.capex_high = 500000
        else:
            profile.capex_low = 25000
            profile.capex_high = 250000

        # Production type
        if "continuous" in combined or "flow" in combined:
            profile.production_type = "continuous"
        elif "batch" in combined:
            profile.production_type = "batch"

        profile.modernization_timeline_months = 12 - (2 * (profile.trl_estimate - 5))
        profile.modernization_timeline_months = max(3, profile.modernization_timeline_months)

        return profile

    def estimate_financial_metrics(
        self,
        patent: Dict[str, Any],
        manufacturing_profile: ManufacturingProfile,
    ) -> FinancialMetrics:
        """
        Estimate financial metrics using deterministic models.
        Assumes 10-year evaluation period, 8% WACC.
        """
        capex_mid = (manufacturing_profile.capex_low
                     + manufacturing_profile.capex_high) / 2
        annual_opex = manufacturing_profile.opex_annual_change
        annual_cost_savings = capex_mid * 0.15  # Assume 15% annual savings on capex
        annual_revenue_uplift = capex_mid * 0.10  # Assume 10% revenue uplift on capex

        # DCF calculation (simplified)
        wacc = 0.08
        years = 10
        discount_factors = [1 / ((1 + wacc) ** y) for y in range(1, years + 1)]
        annual_cf = annual_cost_savings + annual_revenue_uplift

        npv_base = -capex_mid + sum(
            annual_cf * discount_factors[i] for i in range(years)
        )
        npv_optimistic = -capex_mid * 0.8 + sum(
            (annual_cf * 1.5) * discount_factors[i] for i in range(years)
        )
        npv_pessimistic = -capex_mid * 1.2 + sum(
            (annual_cf * 0.5) * discount_factors[i] for i in range(years)
        )

        # Payback period
        if annual_cf > 0:
            payback_years = capex_mid / annual_cf
        else:
            payback_years = 999

        # IRR calculation (approximate)
        if npv_base > 0:
            irr_percent = (annual_cf / capex_mid) * 100
        else:
            irr_percent = 0

        # Valuation (income approach average)
        valuation_mid = max(npv_base, 0)
        valuation_low = valuation_mid * 0.5
        valuation_high = valuation_mid * 2.0

        return FinancialMetrics(
            npv_base=npv_base,
            npv_optimistic=npv_optimistic,
            npv_pessimistic=npv_pessimistic,
            payback_period_years=payback_years,
            irr_percent=irr_percent,
            annual_cost_savings=annual_cost_savings,
            annual_revenue_uplift=annual_revenue_uplift,
            valuation_low=valuation_low,
            valuation_mid=valuation_mid,
            valuation_high=valuation_high,
            key_assumptions={
                "wacc": wacc,
                "evaluation_period_years": years,
                "capex_estimate_mid": capex_mid,
            },
        )

    def assess_strategic_fit(
        self,
        patent: Dict[str, Any],
        technical_score: TechnicalScore,
    ) -> StrategicAssessment:
        """Assess strategic fit and recommendations."""

        abstract = patent.get("abstract", "").lower()
        combined = f"{patent.get('title', '')} {abstract}".lower()

        strategic_fit = (
            technical_score.manufacturing_feasibility_current
            + technical_score.modernization_potential
        ) / 2
        strategic_fit = np.clip(strategic_fit, 1.0, 10.0)

        competitive_advantage = technical_score.scientific_robustness * 0.7
        competitive_advantage = np.clip(competitive_advantage, 1.0, 10.0)

        # Market opportunity heuristics
        if any(word in combined for word in ["wireless", "sensor", "iot"]):
            market_opportunity = "large"
        elif any(word in combined for word in ["specialty", "niche", "rare"]):
            market_opportunity = "small"
        else:
            market_opportunity = "medium"

        # Risk assessment
        legal_ip_risk = "low"  # Patent is expired
        if any(word in combined for word in ["hazardous", "toxic", "dangerous"]):
            regulatory_risk = "high"
        elif any(word in combined for word in ["medical", "pharmaceutical", "food"]):
            regulatory_risk = "high"
        else:
            regulatory_risk = "low"

        # ESG benefit
        if any(word in combined for word in ["energy", "efficient", "green", "clean"]):
            esg_benefit = "high"
        elif any(word in combined for word in ["waste", "emission", "reduction"]):
            esg_benefit = "medium"
        else:
            esg_benefit = "low"

        # Recommendation tier
        if strategic_fit > 7.0 and legal_ip_risk == "low":
            recommendation_tier = 1
        elif strategic_fit > 5.0:
            recommendation_tier = 2
        else:
            recommendation_tier = 3

        next_steps = [
            "Conduct detailed FTO analysis",
            "Perform lab validation trials",
            "Benchmark against current production",
        ]

        derivative_ip = [
            "Improved process control or automation",
            "Modernized material substitutions",
            "System integration and hybrid approaches",
        ]

        return StrategicAssessment(
            strategic_fit_score=strategic_fit,
            competitive_advantage_potential=competitive_advantage,
            market_size_opportunity=market_opportunity,
            legal_ip_risk=legal_ip_risk,
            regulatory_risk=regulatory_risk,
            esg_sustainability_benefit=esg_benefit,
            recommendation_tier=recommendation_tier,
            next_steps=next_steps,
            derivative_ip_opportunities=derivative_ip,
        )

    def compute_integrated_score(
        self, result: PatentAnalysisResult
    ) -> Tuple[float, float]:
        """
        Compute weighted integrated score and confidence level.

        Weights:
        - Scientific Robustness: 15%
        - Manufacturing Feasibility: 20%
        - Modernization Potential: 15%
        - Strategic/Market Fit: 20%
        - Financial Attractiveness: 20%
        - IP/Legal Risk (inverted): 5%
        - ESG/Sustainability: 5%

        Returns: (integrated_score, confidence_level)
        """
        if not all(
            [
                result.technical_score,
                result.manufacturing_profile,
                result.financial_metrics,
                result.strategic_assessment,
            ]
        ):
            return 0.0, 0.3

        weights = {
            "scientific_robustness": 0.15,
            "manufacturing_feasibility": 0.20,
            "modernization_potential": 0.15,
            "strategic_fit": 0.20,
            "financial_attractiveness": 0.20,
            "legal_risk_inverted": 0.05,
            "esg_sustainability": 0.05,
        }

        # Normalize components to 0-10 scale
        scores = {
            "scientific_robustness": result.technical_score.scientific_robustness,
            "manufacturing_feasibility": (
                result.technical_score.manufacturing_feasibility_current
            ),
            "modernization_potential": result.technical_score.modernization_potential,
            "strategic_fit": result.strategic_assessment.strategic_fit_score,
            "financial_attractiveness": min(
                10.0,
                max(
                    0.0,
                    (result.financial_metrics.npv_base / 100000) + 5,
                ),
            ),
            "legal_risk_inverted": 10.0
            if result.strategic_assessment.legal_ip_risk == "low"
            else 5.0,
            "esg_sustainability": (
                9.0
                if result.strategic_assessment.esg_sustainability_benefit == "high"
                else (
                    6.0
                    if result.strategic_assessment.esg_sustainability_benefit == "medium"
                    else 3.0
                )
            ),
        }

        integrated_score = sum(
            scores[dim] * weights[dim] for dim in weights.keys()
        )

        # Confidence based on data completeness
        confidence_level = 0.75

        return np.clip(integrated_score, 0.0, 10.0), confidence_level

    def analyze_patent_dataset(
        self, patents: List[Dict[str, Any]]
    ) -> List[PatentAnalysisResult]:
        """Analyze complete patent dataset."""

        print(f"\nAnalyzing {len(patents)} patents...")
        self.results = []

        for i, patent in enumerate(patents, 1):
            result = PatentAnalysisResult(
                patent_number=patent.get("patent_number", f"UNKNOWN_{i}"),
                title=patent.get("title", ""),
                abstract=patent.get("abstract", ""),
                filing_date=patent.get("filing_date", ""),
                patent_date=patent.get("patent_date", ""),
                assignee_type=patent.get("assignee_type", ""),
            )

            # Classification
            theme, ptype, cpc = self.classify_patent(patent)
            result.technology_theme = theme
            result.patent_type_classified = ptype
            result.cpc_codes = cpc

            # Technical scoring
            result.technical_score = self.score_technical_dimensions(
                patent, theme, ptype
            )

            # Manufacturing profile
            result.manufacturing_profile = self.estimate_manufacturing_profile(
                patent, ptype
            )

            # Financial metrics
            result.financial_metrics = self.estimate_financial_metrics(
                patent, result.manufacturing_profile
            )

            # Strategic assessment
            result.strategic_assessment = self.assess_strategic_fit(
                patent, result.technical_score
            )

            # Integrated score and confidence
            result.integrated_score, result.confidence_level = (
                self.compute_integrated_score(result)
            )

            # Identify red flags
            if result.technical_score.technical_implementation_risk_inverted < 4:
                result.red_flags.append("High technical implementation risk")
            if result.strategic_assessment.regulatory_risk == "high":
                result.red_flags.append("Significant regulatory hurdles")
            if result.financial_metrics.npv_base < 0:
                result.red_flags.append("Negative NPV in base scenario")

            self.results.append(result)

            if (i) % 10 == 0:
                print(f"  ✓ Processed {i}/{len(patents)} patents")

        # Rank results
        self.results.sort(
            key=lambda r: r.integrated_score, reverse=True
        )
        for idx, result in enumerate(self.results, 1):
            result.ranking_position = idx

        print(f"\n✓ Analysis complete. {len(self.results)} patents ranked.")

        return self.results

    def export_results_json(self) -> Path:
        """Export results to JSON."""

        output = {
            "timestamp": self.timestamp,
            "dataset_size": len(self.results),
            "scoring_rubric": self.SCORING_RUBRIC,
            "patents": [
                {
                    "patent_number": r.patent_number,
                    "title": r.title,
                    "ranking_position": r.ranking_position,
                    "integrated_score": r.integrated_score,
                    "confidence_level": r.confidence_level,
                    "technology_theme": r.technology_theme,
                    "patent_type": r.patent_type_classified,
                    "technical_scores": (
                        asdict(r.technical_score) if r.technical_score else {}
                    ),
                    "manufacturing_profile": (
                        asdict(r.manufacturing_profile) if r.manufacturing_profile else {}
                    ),
                    "financial_metrics": (
                        asdict(r.financial_metrics)
                        if r.financial_metrics
                        else {}
                    ),
                    "strategic_assessment": (
                        asdict(r.strategic_assessment)
                        if r.strategic_assessment
                        else {}
                    ),
                    "red_flags": r.red_flags,
                    "key_insights": r.key_insights,
                }
                for r in self.results
            ],
        }

        output_path = self.output_dir / f"patent_analysis_results_{self.timestamp}.json"
        with open(output_path, "w") as f:
            json.dump(output, f, indent=2)

        print(f"Results exported to: {output_path}")
        return output_path

    def export_results_csv(self) -> Path:
        """Export rankings to CSV for easy review."""

        df_data = [
            {
                "Rank": r.ranking_position,
                "Patent_Number": r.patent_number,
                "Title": r.title,
                "Integrated_Score": round(r.integrated_score, 2),
                "Confidence": round(r.confidence_level, 2),
                "Technology_Theme": r.technology_theme,
                "Scientific_Robustness": round(
                    r.technical_score.scientific_robustness, 1
                )
                if r.technical_score
                else None,
                "Manufacturing_Feasibility": round(
                    r.technical_score.manufacturing_feasibility_current, 1
                )
                if r.technical_score
                else None,
                "Modernization_Potential": round(
                    r.technical_score.modernization_potential, 1
                )
                if r.technical_score
                else None,
                "Strategic_Fit": round(r.strategic_assessment.strategic_fit_score, 1)
                if r.strategic_assessment
                else None,
                "NPV_Base": round(r.financial_metrics.npv_base, 0)
                if r.financial_metrics
                else None,
                "Recommendation_Tier": r.strategic_assessment.recommendation_tier
                if r.strategic_assessment
                else None,
                "Red_Flags": "; ".join(r.red_flags),
            }
            for r in self.results
        ]

        df = pd.DataFrame(df_data)
        output_path = self.output_dir / f"patent_rankings_{self.timestamp}.csv"
        df.to_csv(output_path, index=False)

        print(f"CSV export: {output_path}")
        return output_path


def run_framework_analysis(
    patent_discoveries_file: str | None = None,
) -> Tuple[List[PatentAnalysisResult], Path, Path]:
    """
    Run the comprehensive analysis framework on a patent dataset.

    Args:
        patent_discoveries_file: Path to patent discoveries JSON, or None for latest

    Returns:
        (results_list, json_export_path, csv_export_path)
    """

    # Find latest discoveries if not specified
    if not patent_discoveries_file:
        vault_dir = Path("./patent_intelligence_vault/")
        discovery_files = sorted(vault_dir.glob("patent_discoveries_*.json"))
        if not discovery_files:
            raise FileNotFoundError("No patent discovery files found")
        patent_discoveries_file = str(discovery_files[-1])
        print(f"Using latest discoveries: {patent_discoveries_file}")

    # Load patents
    with open(patent_discoveries_file, "r") as f:
        patents = json.load(f)

    print(f"Loaded {len(patents)} patents")

    # Run analysis
    framework = PatentAnalysisFramework()
    results = framework.analyze_patent_dataset(patents)

    # Export results
    json_path = framework.export_results_json()
    csv_path = framework.export_results_csv()

    return results, json_path, csv_path


if __name__ == "__main__":
    results, json_path, csv_path = run_framework_analysis()
    print(f"\n✓ Framework analysis complete!")
    print(f"  JSON: {json_path}")
    print(f"  CSV:  {csv_path}")
