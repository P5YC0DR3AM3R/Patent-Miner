import tempfile
import unittest
from pathlib import Path

from financial_mcp_stack import FinancialMCPStack, IndustryBenchmark, MacroSignals
from patent_analysis_framework import ManufacturingProfile, PatentAnalysisFramework


def _build_benchmark(
    *,
    operating_margin: float,
    ev_to_sales: float,
    cost_of_capital: float,
    sales_to_invested_capital: float,
    net_capex_to_revenue: float,
) -> IndustryBenchmark:
    return IndustryBenchmark(
        industry_name="Electronics (General)",
        number_of_firms=100,
        beta=1.1,
        cost_of_capital=cost_of_capital,
        tax_rate=0.22,
        operating_margin=operating_margin,
        net_margin=max(0.01, operating_margin * 0.65),
        ev_to_sales=ev_to_sales,
        price_to_sales=max(0.5, ev_to_sales - 0.4),
        non_cash_working_capital_to_revenue=0.11,
        net_capex_to_revenue=net_capex_to_revenue,
        sales_to_invested_capital=sales_to_invested_capital,
        market_cap_musd=1_200_000.0,
        enterprise_value_musd=1_600_000.0,
        revenues_musd=850_000.0,
        source_urls={"test": "fixture"},
    )


class StaticMCPStack:
    def __init__(self, benchmark: IndustryBenchmark):
        self._benchmark = benchmark
        self._macro = MacroSignals(
            as_of="2026-02-18",
            risk_free_rate=0.040,
            inflation_rate=0.025,
            producer_price_inflation=0.022,
            manufacturing_wage_growth=0.030,
            manufacturing_capacity_utilization=0.760,
            real_gdp_growth=0.022,
            source_urls={"test": "fixture"},
        )

    def get_macro_signals(self) -> MacroSignals:
        return self._macro

    def resolve_industry(self, theme: str, patent_type: str, text: str) -> str:
        return self._benchmark.industry_name

    def get_industry_benchmark(self, industry_name: str) -> IndustryBenchmark:
        return self._benchmark


class FinancialViabilityModelTests(unittest.TestCase):
    def test_financial_scenarios_remain_ordered(self):
        benchmark = _build_benchmark(
            operating_margin=0.15,
            ev_to_sales=2.8,
            cost_of_capital=0.090,
            sales_to_invested_capital=2.4,
            net_capex_to_revenue=0.045,
        )
        framework = PatentAnalysisFramework(mcp_stack=StaticMCPStack(benchmark))
        patent = {
            "patent_number": "US-TEST-001",
            "title": "Wireless environmental sensor apparatus",
            "abstract": "A sensor device with automation controls for real-time monitoring.",
            "filing_date": "2001-06-01",
        }

        mfg = framework.estimate_manufacturing_profile(
            patent,
            patent_type="apparatus",
            theme="sensors",
        )
        metrics = framework.estimate_financial_metrics(patent, mfg)

        self.assertGreaterEqual(metrics.npv_optimistic, metrics.npv_base)
        self.assertGreaterEqual(metrics.npv_base, metrics.npv_pessimistic)
        self.assertGreater(metrics.market_size_serviceable, 0.0)
        self.assertGreater(metrics.product_value_estimate, 0.0)
        self.assertIn("valuation_sources", metrics.key_assumptions)

    def test_stronger_benchmarks_increase_financial_attractiveness(self):
        strong_framework = PatentAnalysisFramework(
            mcp_stack=StaticMCPStack(
                _build_benchmark(
                    operating_margin=0.24,
                    ev_to_sales=4.1,
                    cost_of_capital=0.075,
                    sales_to_invested_capital=3.1,
                    net_capex_to_revenue=0.030,
                )
            )
        )
        weak_framework = PatentAnalysisFramework(
            mcp_stack=StaticMCPStack(
                _build_benchmark(
                    operating_margin=0.07,
                    ev_to_sales=1.2,
                    cost_of_capital=0.130,
                    sales_to_invested_capital=1.2,
                    net_capex_to_revenue=0.090,
                )
            )
        )

        patent = {
            "patent_number": "US-TEST-002",
            "title": "Automated manufacturing process control method",
            "abstract": "Improves production throughput with predictive controls.",
            "filing_date": "1998-04-12",
        }
        profile = ManufacturingProfile(
            required_materials=["electronic"],
            required_equipment=["automation"],
            process_complexity="medium",
            trl_estimate=7,
            capex_low=120_000.0,
            capex_high=180_000.0,
            opex_annual_change=15_000.0,
            production_type="continuous",
            modernization_timeline_months=8,
            benchmark_industry="Electronics (General)",
        )

        strong = strong_framework.estimate_financial_metrics(patent, profile)
        weak = weak_framework.estimate_financial_metrics(patent, profile)

        self.assertGreater(strong.npv_base, weak.npv_base)
        self.assertGreater(strong.irr_percent, weak.irr_percent)
        self.assertGreater(strong.product_value_estimate, weak.product_value_estimate)

    def test_mcp_stack_fallback_without_network(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = Path(temp_dir) / "snapshot.json"
            stack = FinancialMCPStack(cache_path=cache_path, use_network=False)

            macro = stack.get_macro_signals()
            benchmark = stack.get_industry_benchmark("Unknown Industry")

            self.assertGreater(macro.risk_free_rate, 0.0)
            self.assertTrue(benchmark.industry_name)
            self.assertGreater(benchmark.revenues_musd, 0.0)
            self.assertTrue(cache_path.exists())


if __name__ == "__main__":
    unittest.main()
