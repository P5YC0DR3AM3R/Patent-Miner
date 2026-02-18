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

from financial_mcp_stack import FinancialMCPStack, MacroSignals


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
    benchmark_industry: str = ""
    benchmark_market_revenues_musd: float = 0.0
    benchmark_cost_of_capital: float = 0.0


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
    market_size_serviceable: float = 0.0
    product_value_estimate: float = 0.0
    risk_adjusted_npv_p10: float = 0.0
    risk_adjusted_npv_p90: float = 0.0
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

    def __init__(
        self,
        output_dir: str = "./patent_intelligence_vault/",
        mcp_stack: Optional[FinancialMCPStack] = None,
    ):
        """Initialize framework."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[PatentAnalysisResult] = []
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.mcp_stack = mcp_stack or FinancialMCPStack(
            cache_path=self.output_dir / "financial_mcp_snapshot.json"
        )
        self._macro_signals_cache: Optional[MacroSignals] = None

    def _macro_signals(self) -> MacroSignals:
        if self._macro_signals_cache is None:
            self._macro_signals_cache = self.mcp_stack.get_macro_signals()
        return self._macro_signals_cache

    @staticmethod
    def _safe_filing_year(patent: Dict[str, Any]) -> int:
        filing = str(patent.get("filing_date", "2000-01-01"))
        try:
            return int(filing[:4])
        except (TypeError, ValueError):
            return 2000

    @staticmethod
    def _estimate_internal_rate_percent(cash_flows: List[float]) -> float:
        """Compute IRR with bounded bisection for deterministic stability."""
        if len(cash_flows) < 2:
            return 0.0
        if cash_flows[0] >= 0.0:
            return 0.0
        if all(cf <= 0 for cf in cash_flows[1:]):
            return 0.0

        low = -0.95
        high = 2.00

        def npv(rate: float) -> float:
            return sum(cf / ((1.0 + rate) ** i) for i, cf in enumerate(cash_flows))

        low_npv = npv(low)
        high_npv = npv(high)
        if low_npv * high_npv > 0:
            return 0.0

        for _ in range(80):
            mid = (low + high) / 2.0
            mid_npv = npv(mid)
            if abs(mid_npv) < 1e-6:
                return mid * 100.0
            if low_npv * mid_npv < 0:
                high = mid
                high_npv = mid_npv
            else:
                low = mid
                low_npv = mid_npv
        return ((low + high) / 2.0) * 100.0

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
        filing_year = self._safe_filing_year(patent)
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
        self,
        patent: Dict[str, Any],
        patent_type: str,
        theme: str = "enabling_technology",
    ) -> ManufacturingProfile:
        """Estimate manufacturing requirements using industry benchmarks + macro signals."""

        abstract = patent.get("abstract", "").lower()
        title = patent.get("title", "").lower()
        combined = f"{title} {abstract}"

        profile = ManufacturingProfile()

        # Material inference
        material_keywords = {
            "metal": ["aluminum", "steel", "copper", "titanium", "iron", "alloy"],
            "polymer": ["plastic", "polymer", "resin", "polyester", "polyethylene"],
            "ceramic": ["ceramic", "glass", "silicon", "oxide"],
            "electronic": ["circuit", "pcb", "semiconductor", "electronic"],
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
            "automation": ["automation", "controller", "plc", "scada"],
        }
        for equip, keywords in equipment_keywords.items():
            if any(kw in combined for kw in keywords):
                profile.required_equipment.append(equip)

        complexity_index = 1.0
        if any(word in combined for word in ["complex", "multistep", "sequential", "sensitive"]):
            profile.process_complexity = "high"
            complexity_index = 1.35
        elif any(word in combined for word in ["simple", "straightforward", "single-step"]):
            profile.process_complexity = "low"
            complexity_index = 0.80

        macro = self._macro_signals()
        industry_name = self.mcp_stack.resolve_industry(
            theme=theme,
            patent_type=patent_type,
            text=combined,
        )
        benchmark = self.mcp_stack.get_industry_benchmark(industry_name)

        filing_year = self._safe_filing_year(patent)
        profile.trl_estimate = 7 if filing_year > 2000 else 6

        # Capex scales with benchmark capex intensity and complexity.
        capex_intensity = abs(float(benchmark.net_capex_to_revenue))
        capex_intensity = np.clip(capex_intensity, 0.015, 0.18)

        market_revenue_usd = max(benchmark.revenues_musd * 1_000_000.0, 80_000_000.0)
        pilot_revenue_target = market_revenue_usd * 0.00002  # 0.002% pilot scale
        capital_productivity = np.clip(float(benchmark.sales_to_invested_capital), 1.0, 4.5)

        base_capex_mid = max(
            35_000.0,
            pilot_revenue_target / capital_productivity,
        )
        base_capex_mid *= (1.0 + capex_intensity * 2.0)

        equipment_factor = 1.0 + (0.10 * len(profile.required_equipment))
        material_factor = 1.0 + (0.06 * len(profile.required_materials))
        inflation_factor = 1.0 + np.clip(macro.producer_price_inflation, -0.03, 0.15)
        wage_factor = 1.0 + np.clip(macro.manufacturing_wage_growth * 0.5, -0.02, 0.08)

        capex_mid = (
            base_capex_mid
            * complexity_index
            * equipment_factor
            * material_factor
            * inflation_factor
            * wage_factor
        )

        if patent_type == "apparatus":
            capex_mid *= 1.15
        elif patent_type == "process":
            capex_mid *= 1.05

        profile.capex_low = capex_mid * 0.70
        profile.capex_high = capex_mid * 1.55

        opex_base_rate = 0.08 + (0.03 if profile.process_complexity == "high" else 0.01)
        profile.opex_annual_change = capex_mid * opex_base_rate * inflation_factor

        if "continuous" in combined or "flow" in combined:
            profile.production_type = "continuous"
        elif "batch" in combined:
            profile.production_type = "batch"
        else:
            profile.production_type = "hybrid" if profile.process_complexity == "high" else "batch"

        profile.modernization_timeline_months = int(
            np.clip(
                11
                + (3 if profile.process_complexity == "high" else 0)
                - (profile.trl_estimate - 6) * 2
                + len(profile.required_equipment),
                4,
                20,
            )
        )

        if profile.process_complexity == "high":
            profile.critical_bottlenecks.append("Tight process window during scale-up")
        if len(profile.required_materials) >= 3:
            profile.critical_bottlenecks.append("Multi-material supply qualification")
        if macro.manufacturing_capacity_utilization > 0.82:
            profile.critical_bottlenecks.append("Capacity constraints in manufacturing market")

        profile.benchmark_industry = benchmark.industry_name
        profile.benchmark_market_revenues_musd = benchmark.revenues_musd
        profile.benchmark_cost_of_capital = benchmark.cost_of_capital

        return profile

    def estimate_financial_metrics(
        self,
        patent: Dict[str, Any],
        manufacturing_profile: ManufacturingProfile,
    ) -> FinancialMetrics:
        """Estimate financial metrics with benchmark-driven DCF scenarios."""
        title = str(patent.get("title", "")).lower()
        abstract = str(patent.get("abstract", "")).lower()
        combined = f"{title} {abstract}"

        benchmark = self.mcp_stack.get_industry_benchmark(
            manufacturing_profile.benchmark_industry or "Total  Market (without financials)"
        )
        macro = self._macro_signals()

        years = 10
        capex_mid = (manufacturing_profile.capex_low + manufacturing_profile.capex_high) / 2.0
        maintenance_capex_rate = 0.02

        discount_rate_base = np.clip(
            (benchmark.cost_of_capital * 0.75) + (macro.risk_free_rate * 0.25),
            0.06,
            0.20,
        )
        tax_rate = np.clip(benchmark.tax_rate, 0.10, 0.35)
        operating_margin_base = np.clip(benchmark.operating_margin, 0.05, 0.40)

        innovation_margin_uplift = 0.02
        if any(word in combined for word in ["automation", "efficiency", "predictive"]):
            innovation_margin_uplift += 0.01
        if any(word in combined for word in ["premium", "accuracy", "quality"]):
            innovation_margin_uplift += 0.01
        operating_margin_base = np.clip(operating_margin_base + innovation_margin_uplift, 0.06, 0.50)

        market_growth_base = np.clip(
            0.35 * macro.real_gdp_growth
            + 0.25 * macro.inflation_rate
            + 0.40 * max(benchmark.net_capex_to_revenue, 0.01),
            0.01,
            0.16,
        )

        sales_to_capital = np.clip(benchmark.sales_to_invested_capital, 0.9, 4.5)
        working_capital_ratio = np.clip(benchmark.non_cash_working_capital_to_revenue, 0.02, 0.30)
        annual_opex_change = manufacturing_profile.opex_annual_change

        market_size_total = max(benchmark.revenues_musd * 1_000_000.0, 250_000_000.0)
        serviceable_share = np.clip(
            0.0008
            + 0.0006 * len(manufacturing_profile.required_equipment)
            + 0.0004 * len(manufacturing_profile.required_materials)
            + (0.0015 if "wireless" in combined or "sensor" in combined else 0.0)
            + (0.0010 if "medical" in combined or "health" in combined else 0.0),
            0.001,
            0.04,
        )
        serviceable_market = market_size_total * serviceable_share

        revenue_capacity_year1 = capex_mid * sales_to_capital
        year1_revenue = np.clip(
            min(serviceable_market * 0.18, revenue_capacity_year1 * 1.10),
            capex_mid * 0.40,
            serviceable_market,
        )

        process_or_method = "method" in combined or "process" in combined
        annual_cost_savings = year1_revenue * (0.20 if process_or_method else 0.10)
        annual_revenue_uplift = year1_revenue * (0.18 if not process_or_method else 0.10)

        initial_working_capital = working_capital_ratio * year1_revenue * 0.5

        def scenario_cash_flow(
            growth_rate: float,
            operating_margin: float,
            discount_rate: float,
            capex_multiplier: float,
            savings_multiplier: float,
            revenue_multiplier: float,
        ) -> Tuple[float, List[float]]:
            initial_investment = (capex_mid * capex_multiplier) + initial_working_capital
            cash_flows = [-initial_investment]
            prev_revenue = 0.0

            for year in range(1, years + 1):
                adoption = np.clip(0.35 + (0.085 * year), 0.25, 1.00)
                revenue = (
                    year1_revenue
                    * revenue_multiplier
                    * ((1.0 + growth_rate) ** (year - 1))
                    * adoption
                )
                savings = (
                    annual_cost_savings
                    * savings_multiplier
                    * ((1.0 + growth_rate * 0.35) ** (year - 1))
                )
                opex_drag = annual_opex_change * ((1.0 + macro.inflation_rate) ** (year - 1))

                ebit = (revenue * operating_margin) + savings - opex_drag
                taxes = max(0.0, ebit) * tax_rate
                nopat = ebit - taxes

                delta_revenue = max(0.0, revenue - prev_revenue)
                growth_capex = delta_revenue / sales_to_capital
                maintenance_capex = initial_investment * maintenance_capex_rate
                delta_working_capital = working_capital_ratio * delta_revenue
                depreciation = (initial_investment / 7.0) if year <= 7 else 0.0

                free_cash_flow = (
                    nopat
                    + depreciation
                    - growth_capex
                    - maintenance_capex
                    - delta_working_capital
                )
                cash_flows.append(free_cash_flow)
                prev_revenue = revenue

            npv_value = sum(
                cf / ((1.0 + discount_rate) ** idx)
                for idx, cf in enumerate(cash_flows)
            )
            return npv_value, cash_flows

        npv_base, base_cash_flows = scenario_cash_flow(
            growth_rate=market_growth_base,
            operating_margin=operating_margin_base,
            discount_rate=discount_rate_base,
            capex_multiplier=1.00,
            savings_multiplier=1.00,
            revenue_multiplier=1.00,
        )
        npv_optimistic, _ = scenario_cash_flow(
            growth_rate=min(0.22, market_growth_base * 1.30),
            operating_margin=min(0.58, operating_margin_base + 0.03),
            discount_rate=max(0.055, discount_rate_base - 0.015),
            capex_multiplier=0.88,
            savings_multiplier=1.20,
            revenue_multiplier=1.18,
        )
        npv_pessimistic, _ = scenario_cash_flow(
            growth_rate=max(0.003, market_growth_base * 0.60),
            operating_margin=max(0.03, operating_margin_base - 0.04),
            discount_rate=min(0.26, discount_rate_base + 0.020),
            capex_multiplier=1.20,
            savings_multiplier=0.80,
            revenue_multiplier=0.82,
        )

        # Deterministic Monte Carlo envelope around base-case assumptions.
        patent_seed = sum(ord(ch) for ch in str(patent.get("patent_number", ""))) + years
        rng = np.random.default_rng(patent_seed)
        simulations = 200
        mc_npvs: List[float] = []
        for _ in range(simulations):
            sampled_growth = np.clip(rng.normal(market_growth_base, 0.015), 0.0, 0.25)
            sampled_margin = np.clip(rng.normal(operating_margin_base, 0.025), 0.03, 0.60)
            sampled_discount = np.clip(rng.normal(discount_rate_base, 0.012), 0.05, 0.30)
            sampled_capex_mult = np.clip(rng.normal(1.0, 0.10), 0.75, 1.35)
            sampled_savings_mult = np.clip(rng.normal(1.0, 0.12), 0.65, 1.40)
            sampled_revenue_mult = np.clip(rng.normal(1.0, 0.12), 0.65, 1.45)
            sampled_npv, _ = scenario_cash_flow(
                growth_rate=sampled_growth,
                operating_margin=sampled_margin,
                discount_rate=sampled_discount,
                capex_multiplier=sampled_capex_mult,
                savings_multiplier=sampled_savings_mult,
                revenue_multiplier=sampled_revenue_mult,
            )
            mc_npvs.append(sampled_npv)

        p10_npv = float(np.percentile(mc_npvs, 10))
        p90_npv = float(np.percentile(mc_npvs, 90))

        cumulative = 0.0
        payback_years = 999.0
        for idx, cf in enumerate(base_cash_flows[1:], start=1):
            cumulative += cf
            if cumulative + base_cash_flows[0] >= 0:
                payback_years = float(idx)
                break

        irr_percent = max(-95.0, min(300.0, self._estimate_internal_rate_percent(base_cash_flows)))

        terminal_revenue_year5 = year1_revenue * ((1.0 + market_growth_base) ** 4)
        product_value_estimate = terminal_revenue_year5 * np.clip(benchmark.ev_to_sales, 0.4, 10.0)
        cost_approach_value = capex_mid * 1.25
        income_approach_value = max(npv_base, 0.0)

        valuation_mid = max(
            0.0,
            (0.55 * income_approach_value)
            + (0.30 * product_value_estimate)
            + (0.15 * cost_approach_value),
        )
        valuation_low = max(0.0, min(npv_pessimistic, p10_npv, valuation_mid * 0.65))
        valuation_high = max(npv_optimistic, p90_npv, valuation_mid * 1.35)

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
            market_size_serviceable=serviceable_market,
            product_value_estimate=product_value_estimate,
            risk_adjusted_npv_p10=p10_npv,
            risk_adjusted_npv_p90=p90_npv,
            key_assumptions={
                "benchmark_industry": benchmark.industry_name,
                "wacc_base": discount_rate_base,
                "tax_rate": tax_rate,
                "operating_margin_base": operating_margin_base,
                "growth_rate_base": market_growth_base,
                "serviceable_market_share": serviceable_share,
                "serviceable_market_usd": serviceable_market,
                "market_size_total_usd": market_size_total,
                "sales_to_invested_capital": sales_to_capital,
                "non_cash_working_capital_ratio": working_capital_ratio,
                "net_capex_ratio_benchmark": benchmark.net_capex_to_revenue,
                "evaluation_period_years": years,
                "capex_estimate_mid": capex_mid,
                "macro_signals_as_of": macro.as_of,
                "valuation_sources": {
                    "income_approach_npv": income_approach_value,
                    "market_approach_ev_sales": product_value_estimate,
                    "cost_approach_replacement": cost_approach_value,
                },
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
            "financial_attractiveness": float(
                np.clip(
                    5.0
                    + (
                        np.sign(result.financial_metrics.npv_base)
                        * np.log1p(abs(result.financial_metrics.npv_base) / 1_000_000.0)
                        * 2.0
                    ),
                    0.0,
                    10.0,
                )
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

        npv_spread = max(
            1.0,
            abs(
                result.financial_metrics.risk_adjusted_npv_p90
                - result.financial_metrics.risk_adjusted_npv_p10
            ),
        )
        spread_ratio = npv_spread / max(1.0, abs(result.financial_metrics.npv_base))
        confidence_level = float(np.clip(0.88 - min(0.45, spread_ratio * 0.18), 0.45, 0.92))

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
                patent, ptype, theme
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
                "NPV_P10": round(r.financial_metrics.risk_adjusted_npv_p10, 0)
                if r.financial_metrics
                else None,
                "NPV_P90": round(r.financial_metrics.risk_adjusted_npv_p90, 0)
                if r.financial_metrics
                else None,
                "Product_Value_Estimate": round(r.financial_metrics.product_value_estimate, 0)
                if r.financial_metrics
                else None,
                "Serviceable_Market_Size": round(r.financial_metrics.market_size_serviceable, 0)
                if r.financial_metrics
                else None,
                "Benchmark_Industry": (
                    r.manufacturing_profile.benchmark_industry
                    if r.manufacturing_profile
                    else None
                ),
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
