#!/usr/bin/env python3
"""MCP-style market and financial benchmark stack for patent valuation.

This module assembles a live data stack from public sources and provides:
- Macro signals (rates, inflation, manufacturing utilization)
- Industry benchmarks (WACC, margins, EV/Sales, capex intensity, market size)
- Deterministic industry resolution for patent themes

Primary sources:
- Damodaran industry datasets: cost of capital, margins, valuation multiples,
  cash-flow structure, and industry dollar aggregates.
- FRED series: treasury yield, inflation, producer prices, manufacturing wages,
  capacity utilization, and real GDP.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

import pandas as pd


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _normalized_label(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())


def _parse_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    text = str(value).strip()
    if not text:
        return default
    text = text.replace(",", "")
    if text in {"-", "nan", "None"}:
        return default
    try:
        return float(text)
    except ValueError:
        return default


def _parse_ratio(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    text = str(value).strip()
    if not text:
        return default
    text = text.replace(",", "")
    if text.endswith("%"):
        return _parse_float(text[:-1], default=default * 100.0) / 100.0
    return _parse_float(text, default=default)


def _parse_money_musd(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    text = str(value).strip()
    if not text:
        return default
    text = text.replace("$", "").replace(",", "").replace("(", "-").replace(")", "")
    return _parse_float(text, default=default)


def _find_column(columns: Iterable[str], choices: Iterable[Iterable[str]]) -> Optional[str]:
    normalized = {col: _normalized_label(col) for col in columns}
    for pattern_parts in choices:
        parts = tuple(_normalized_label(part) for part in pattern_parts)
        for col, norm in normalized.items():
            if all(part in norm for part in parts):
                return col
    return None


@dataclass
class MacroSignals:
    as_of: str
    risk_free_rate: float
    inflation_rate: float
    producer_price_inflation: float
    manufacturing_wage_growth: float
    manufacturing_capacity_utilization: float
    real_gdp_growth: float
    source_urls: Dict[str, str]


@dataclass
class IndustryBenchmark:
    industry_name: str
    number_of_firms: int
    beta: float
    cost_of_capital: float
    tax_rate: float
    operating_margin: float
    net_margin: float
    ev_to_sales: float
    price_to_sales: float
    non_cash_working_capital_to_revenue: float
    net_capex_to_revenue: float
    sales_to_invested_capital: float
    market_cap_musd: float
    enterprise_value_musd: float
    revenues_musd: float
    source_urls: Dict[str, str]


DAMODARAN_URLS = {
    "wacc": "https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/wacc.html",
    "margin": "https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/margin.html",
    "cashflow": "https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/cfbasics.html",
    "multiples": "https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/psdata.html",
    "dollar": "https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/DollarUS.html",
}

FRED_SERIES = {
    "risk_free_rate": "DGS10",
    "cpi": "CPIAUCSL",
    "ppi": "PPIACO",
    "manufacturing_wages": "CES3000000008",
    "manufacturing_capacity_utilization": "CUMFNS",
    "real_gdp": "GDPC1",
}

FRED_URL_TEMPLATE = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"

THEME_TO_INDUSTRY = {
    "sensors": "Electronics (General)",
    "materials": "Chemical  (Specialty)",
    "process": "Machinery",
    "control_systems": "Software  (System & Application)",
    "apparatus": "Electrical Equipment",
    "wireless": "Telecom  (Wireless)",
    "energy": "Green  & Renewable Energy",
}

KEYWORD_TO_INDUSTRY = {
    "medical": "Healthcare Products",
    "patient": "Healthcare Products",
    "pharma": "Drugs (Pharmaceutical)",
    "wireless": "Telecom  (Wireless)",
    "network": "Software  (System & Application)",
    "iot": "Electronics (General)",
    "sensor": "Electronics (General)",
    "detector": "Electronics (General)",
    "polymer": "Chemical  (Specialty)",
    "coating": "Chemical  (Specialty)",
    "alloy": "Metals  & Mining",
    "crop": "Farming/Agriculture",
    "soil": "Farming/Agriculture",
    "agriculture": "Farming/Agriculture",
    "water": "Environmental  & Waste Services",
    "waste": "Environmental  & Waste Services",
    "emission": "Environmental  & Waste Services",
    "battery": "Green  & Renewable Energy",
    "power": "Power",
}

DEFAULT_MACRO_SIGNALS = MacroSignals(
    as_of=datetime.utcnow().strftime("%Y-%m-%d"),
    risk_free_rate=0.040,
    inflation_rate=0.028,
    producer_price_inflation=0.025,
    manufacturing_wage_growth=0.030,
    manufacturing_capacity_utilization=0.760,
    real_gdp_growth=0.021,
    source_urls={
        "note": "fallback_defaults",
    },
)

DEFAULT_INDUSTRY_BENCHMARKS = {
    "Electronics (General)": IndustryBenchmark(
        industry_name="Electronics (General)",
        number_of_firms=100,
        beta=1.15,
        cost_of_capital=0.095,
        tax_rate=0.21,
        operating_margin=0.12,
        net_margin=0.08,
        ev_to_sales=2.8,
        price_to_sales=2.4,
        non_cash_working_capital_to_revenue=0.10,
        net_capex_to_revenue=0.04,
        sales_to_invested_capital=2.5,
        market_cap_musd=1_500_000.0,
        enterprise_value_musd=1_900_000.0,
        revenues_musd=900_000.0,
        source_urls={"note": "fallback_defaults"},
    ),
    "Chemical  (Specialty)": IndustryBenchmark(
        industry_name="Chemical  (Specialty)",
        number_of_firms=80,
        beta=1.05,
        cost_of_capital=0.090,
        tax_rate=0.22,
        operating_margin=0.14,
        net_margin=0.09,
        ev_to_sales=2.3,
        price_to_sales=1.9,
        non_cash_working_capital_to_revenue=0.14,
        net_capex_to_revenue=0.05,
        sales_to_invested_capital=1.8,
        market_cap_musd=800_000.0,
        enterprise_value_musd=1_050_000.0,
        revenues_musd=620_000.0,
        source_urls={"note": "fallback_defaults"},
    ),
    "Healthcare Products": IndustryBenchmark(
        industry_name="Healthcare Products",
        number_of_firms=90,
        beta=1.00,
        cost_of_capital=0.087,
        tax_rate=0.20,
        operating_margin=0.16,
        net_margin=0.10,
        ev_to_sales=3.2,
        price_to_sales=2.9,
        non_cash_working_capital_to_revenue=0.12,
        net_capex_to_revenue=0.03,
        sales_to_invested_capital=2.2,
        market_cap_musd=1_200_000.0,
        enterprise_value_musd=1_450_000.0,
        revenues_musd=780_000.0,
        source_urls={"note": "fallback_defaults"},
    ),
    "Environmental  & Waste Services": IndustryBenchmark(
        industry_name="Environmental  & Waste Services",
        number_of_firms=40,
        beta=0.95,
        cost_of_capital=0.082,
        tax_rate=0.24,
        operating_margin=0.11,
        net_margin=0.07,
        ev_to_sales=2.0,
        price_to_sales=1.8,
        non_cash_working_capital_to_revenue=0.11,
        net_capex_to_revenue=0.06,
        sales_to_invested_capital=1.6,
        market_cap_musd=250_000.0,
        enterprise_value_musd=320_000.0,
        revenues_musd=190_000.0,
        source_urls={"note": "fallback_defaults"},
    ),
    "Farming/Agriculture": IndustryBenchmark(
        industry_name="Farming/Agriculture",
        number_of_firms=30,
        beta=0.92,
        cost_of_capital=0.080,
        tax_rate=0.19,
        operating_margin=0.09,
        net_margin=0.05,
        ev_to_sales=1.4,
        price_to_sales=1.2,
        non_cash_working_capital_to_revenue=0.15,
        net_capex_to_revenue=0.04,
        sales_to_invested_capital=1.5,
        market_cap_musd=140_000.0,
        enterprise_value_musd=190_000.0,
        revenues_musd=160_000.0,
        source_urls={"note": "fallback_defaults"},
    ),
    "Machinery": IndustryBenchmark(
        industry_name="Machinery",
        number_of_firms=70,
        beta=1.08,
        cost_of_capital=0.088,
        tax_rate=0.23,
        operating_margin=0.10,
        net_margin=0.06,
        ev_to_sales=1.9,
        price_to_sales=1.7,
        non_cash_working_capital_to_revenue=0.13,
        net_capex_to_revenue=0.05,
        sales_to_invested_capital=1.9,
        market_cap_musd=500_000.0,
        enterprise_value_musd=670_000.0,
        revenues_musd=440_000.0,
        source_urls={"note": "fallback_defaults"},
    ),
    "Total  Market (without financials)": IndustryBenchmark(
        industry_name="Total  Market (without financials)",
        number_of_firms=1_000,
        beta=1.05,
        cost_of_capital=0.089,
        tax_rate=0.22,
        operating_margin=0.11,
        net_margin=0.07,
        ev_to_sales=2.1,
        price_to_sales=1.9,
        non_cash_working_capital_to_revenue=0.12,
        net_capex_to_revenue=0.05,
        sales_to_invested_capital=1.9,
        market_cap_musd=25_000_000.0,
        enterprise_value_musd=31_000_000.0,
        revenues_musd=14_000_000.0,
        source_urls={"note": "fallback_defaults"},
    ),
}


class FinancialMCPStack:
    """Live market-data stack with caching and deterministic fallbacks."""

    def __init__(
        self,
        cache_path: str | Path = "./patent_intelligence_vault/financial_mcp_snapshot.json",
        cache_ttl_hours: int = 24,
        use_network: bool = True,
    ) -> None:
        self.cache_path = Path(cache_path)
        self.cache_ttl = timedelta(hours=cache_ttl_hours)
        self.use_network = use_network
        self._snapshot: Optional[Dict[str, Any]] = None
        self._industry_index: Dict[str, str] = {}

    def resolve_industry(self, theme: str, patent_type: str, text: str) -> str:
        """Resolve patent metadata/text to the nearest available benchmark industry."""
        self._ensure_snapshot_loaded()
        normalized_text = (text or "").lower()

        for keyword, industry in KEYWORD_TO_INDUSTRY.items():
            if keyword in normalized_text:
                return self._coerce_industry(industry)

        theme_industry = THEME_TO_INDUSTRY.get(theme)
        if theme_industry:
            return self._coerce_industry(theme_industry)

        if patent_type == "process":
            return self._coerce_industry("Machinery")
        if patent_type == "apparatus":
            return self._coerce_industry("Electrical Equipment")

        return self._coerce_industry("Total  Market (without financials)")

    def get_macro_signals(self) -> MacroSignals:
        """Return macroeconomic signals used in valuation assumptions."""
        self._ensure_snapshot_loaded()
        payload = self._snapshot.get("macro_signals", {}) if self._snapshot else {}
        if not payload:
            return DEFAULT_MACRO_SIGNALS
        return MacroSignals(**payload)

    def get_industry_benchmark(self, industry_name: str) -> IndustryBenchmark:
        """Return market/valuation benchmark for an industry, with fallback routing."""
        self._ensure_snapshot_loaded()
        if not self._snapshot:
            return DEFAULT_INDUSTRY_BENCHMARKS["Total  Market (without financials)"]

        benchmarks = self._snapshot.get("industry_benchmarks", {})
        if not benchmarks:
            return DEFAULT_INDUSTRY_BENCHMARKS["Total  Market (without financials)"]

        resolved_name = self._coerce_industry(industry_name)
        payload = benchmarks.get(resolved_name)
        if payload:
            return IndustryBenchmark(**payload)

        fallback_name = self._coerce_industry("Total  Market (without financials)")
        fallback_payload = benchmarks.get(fallback_name)
        if fallback_payload:
            return IndustryBenchmark(**fallback_payload)
        return DEFAULT_INDUSTRY_BENCHMARKS["Total  Market (without financials)"]

    def _coerce_industry(self, requested_name: str) -> str:
        key = _normalized_label(requested_name)
        if key in self._industry_index:
            return self._industry_index[key]

        if "totalmarketwithoutfinancials" in self._industry_index:
            return self._industry_index["totalmarketwithoutfinancials"]

        if self._industry_index:
            return next(iter(self._industry_index.values()))

        return "Total  Market (without financials)"

    def _ensure_snapshot_loaded(self) -> None:
        if self._snapshot is not None:
            return
        cached = self._load_cached_snapshot()
        if cached is not None:
            self._snapshot = cached
        else:
            self._snapshot = self._build_snapshot()
            self._write_snapshot(self._snapshot)
        self._industry_index = {
            _normalized_label(name): name
            for name in self._snapshot.get("industry_benchmarks", {}).keys()
        }

    def _load_cached_snapshot(self) -> Optional[Dict[str, Any]]:
        if not self.cache_path.exists():
            return None
        try:
            payload = json.loads(self.cache_path.read_text(encoding="utf-8"))
            timestamp = datetime.fromisoformat(payload.get("fetched_at"))
        except Exception:
            return None

        if datetime.utcnow() - timestamp > self.cache_ttl:
            return None
        return payload

    def _write_snapshot(self, snapshot: Dict[str, Any]) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")

    def _build_snapshot(self) -> Dict[str, Any]:
        warnings = []
        macro = DEFAULT_MACRO_SIGNALS
        industries = {
            name: benchmark
            for name, benchmark in DEFAULT_INDUSTRY_BENCHMARKS.items()
        }

        if self.use_network:
            try:
                macro = self._fetch_macro_signals()
            except Exception as exc:
                warnings.append(f"macro_fetch_failed: {exc}")

            try:
                network_industries = self._fetch_industry_benchmarks()
                if network_industries:
                    industries = network_industries
            except Exception as exc:
                warnings.append(f"industry_fetch_failed: {exc}")

        return {
            "fetched_at": datetime.utcnow().isoformat(),
            "macro_signals": asdict(macro),
            "industry_benchmarks": {
                name: asdict(benchmark)
                for name, benchmark in industries.items()
            },
            "warnings": warnings,
        }

    def _fetch_macro_signals(self) -> MacroSignals:
        def fetch_series(series_id: str) -> pd.Series:
            url = FRED_URL_TEMPLATE.format(series_id=series_id)
            df = pd.read_csv(url)
            value_col = series_id
            if value_col not in df.columns:
                raise KeyError(f"FRED response missing {series_id}")
            series = pd.to_numeric(df[value_col], errors="coerce").dropna()
            if series.empty:
                raise ValueError(f"FRED series empty: {series_id}")
            series.index = range(len(series))
            return series

        risk_free = fetch_series(FRED_SERIES["risk_free_rate"]).iloc[-1] / 100.0
        cpi_series = fetch_series(FRED_SERIES["cpi"])
        ppi_series = fetch_series(FRED_SERIES["ppi"])
        wages_series = fetch_series(FRED_SERIES["manufacturing_wages"])
        capacity_series = fetch_series(FRED_SERIES["manufacturing_capacity_utilization"])
        gdp_series = fetch_series(FRED_SERIES["real_gdp"])

        inflation_rate = (cpi_series.iloc[-1] / cpi_series.iloc[-13]) - 1.0
        producer_inflation = (ppi_series.iloc[-1] / ppi_series.iloc[-13]) - 1.0
        wage_growth = (wages_series.iloc[-1] / wages_series.iloc[-13]) - 1.0
        gdp_growth = (gdp_series.iloc[-1] / gdp_series.iloc[-5]) - 1.0
        capacity_util = capacity_series.iloc[-1] / 100.0

        return MacroSignals(
            as_of=datetime.utcnow().strftime("%Y-%m-%d"),
            risk_free_rate=_clamp(risk_free, 0.01, 0.12),
            inflation_rate=_clamp(inflation_rate, -0.02, 0.12),
            producer_price_inflation=_clamp(producer_inflation, -0.05, 0.18),
            manufacturing_wage_growth=_clamp(wage_growth, -0.03, 0.15),
            manufacturing_capacity_utilization=_clamp(capacity_util, 0.40, 0.95),
            real_gdp_growth=_clamp(gdp_growth, -0.08, 0.12),
            source_urls={
                name: FRED_URL_TEMPLATE.format(series_id=series_id)
                for name, series_id in FRED_SERIES.items()
            },
        )

    def _fetch_industry_benchmarks(self) -> Dict[str, IndustryBenchmark]:
        wacc = pd.read_html(DAMODARAN_URLS["wacc"], header=0)[0]
        margin = pd.read_html(DAMODARAN_URLS["margin"], header=1)[0]
        cashflow = pd.read_html(DAMODARAN_URLS["cashflow"], header=0)[0]
        multiples = pd.read_html(DAMODARAN_URLS["multiples"], header=0)[0]
        dollar = pd.read_html(DAMODARAN_URLS["dollar"], header=0)[0]

        for frame in (wacc, margin, cashflow, multiples, dollar):
            frame.columns = [str(col).strip() for col in frame.columns]

        wacc_industry_col = _find_column(wacc.columns, [("industry", "name")])
        margin_industry_col = _find_column(margin.columns, [("industry", "name")])
        cashflow_industry_col = _find_column(cashflow.columns, [("industry", "name")])
        multiples_industry_col = _find_column(multiples.columns, [("industry", "name")])
        dollar_industry_col = _find_column(dollar.columns, [("industry", "name")])

        if not all(
            [
                wacc_industry_col,
                margin_industry_col,
                cashflow_industry_col,
                multiples_industry_col,
                dollar_industry_col,
            ]
        ):
            raise KeyError("Unable to identify industry name columns in Damodaran datasets")

        frames = []
        for frame, col in (
            (wacc, wacc_industry_col),
            (margin, margin_industry_col),
            (cashflow, cashflow_industry_col),
            (multiples, multiples_industry_col),
            (dollar, dollar_industry_col),
        ):
            scoped = frame.copy()
            scoped["industry_key"] = scoped[col].map(_normalized_label)
            frames.append(scoped)

        wacc, margin, cashflow, multiples, dollar = frames

        merged = wacc.merge(margin, on="industry_key", how="left", suffixes=("", "_margin"))
        merged = merged.merge(cashflow, on="industry_key", how="left", suffixes=("", "_cashflow"))
        merged = merged.merge(multiples, on="industry_key", how="left", suffixes=("", "_multiples"))
        merged = merged.merge(dollar, on="industry_key", how="left", suffixes=("", "_dollar"))

        col_map = {
            "industry_name": _find_column(merged.columns, [("industry", "name"), ("industry", "name", "dollar")]),
            "number_of_firms": _find_column(merged.columns, [("number", "of", "firms")]),
            "beta": _find_column(merged.columns, [("beta",)]),
            "cost_of_capital": _find_column(merged.columns, [("cost", "of", "capital")]),
            "wacc_tax_rate": _find_column(merged.columns, [("tax", "rate")]),
            "effective_tax_rate": _find_column(merged.columns, [("effective", "tax", "rate")]),
            "operating_margin": _find_column(
                merged.columns,
                [("pre", "tax", "operating", "margin", "adjusted", "leases"),
                 ("pre", "tax", "lease", "adjusted", "margin")],
            ),
            "net_margin": _find_column(merged.columns, [("net", "margin")]),
            "ev_to_sales": _find_column(merged.columns, [("ev", "sales")]),
            "price_to_sales": _find_column(merged.columns, [("price", "sales")]),
            "non_cash_wc": _find_column(
                merged.columns, [("non", "cash", "working", "capital"), ("working", "capital")]
            ),
            "net_capex_to_revenue": _find_column(merged.columns, [("net", "cap", "ex"), ("cap", "ex", "revenues")]),
            "sales_to_invested_capital": _find_column(merged.columns, [("sales", "invested", "capital")]),
            "market_cap": _find_column(merged.columns, [("market", "cap"), ("market", "cap", "dollar")]),
            "enterprise_value": _find_column(
                merged.columns,
                [("enteprise", "value"), ("enterprise", "value")],
            ),
            "revenues": _find_column(merged.columns, [("revenues",)]),
        }

        source_urls = dict(DAMODARAN_URLS)
        benchmarks: Dict[str, IndustryBenchmark] = {}
        for _, row in merged.iterrows():
            industry_name = str(row.get(col_map["industry_name"], "")).strip()
            if not industry_name:
                continue

            tax_rate = _parse_ratio(
                row.get(col_map["effective_tax_rate"]),
                default=_parse_ratio(row.get(col_map["wacc_tax_rate"]), default=0.22),
            )

            benchmark = IndustryBenchmark(
                industry_name=industry_name,
                number_of_firms=int(_parse_float(row.get(col_map["number_of_firms"]), default=0)),
                beta=_parse_float(row.get(col_map["beta"]), default=1.0),
                cost_of_capital=_parse_ratio(row.get(col_map["cost_of_capital"]), default=0.09),
                tax_rate=_clamp(tax_rate, 0.01, 0.45),
                operating_margin=_parse_ratio(row.get(col_map["operating_margin"]), default=0.10),
                net_margin=_parse_ratio(row.get(col_map["net_margin"]), default=0.06),
                ev_to_sales=_parse_float(row.get(col_map["ev_to_sales"]), default=2.0),
                price_to_sales=_parse_float(row.get(col_map["price_to_sales"]), default=1.8),
                non_cash_working_capital_to_revenue=_parse_ratio(
                    row.get(col_map["non_cash_wc"]), default=0.10
                ),
                net_capex_to_revenue=_parse_ratio(
                    row.get(col_map["net_capex_to_revenue"]), default=0.04
                ),
                sales_to_invested_capital=_parse_float(
                    row.get(col_map["sales_to_invested_capital"]), default=1.8
                ),
                market_cap_musd=_parse_money_musd(row.get(col_map["market_cap"]), default=0.0),
                enterprise_value_musd=_parse_money_musd(
                    row.get(col_map["enterprise_value"]), default=0.0
                ),
                revenues_musd=_parse_money_musd(row.get(col_map["revenues"]), default=0.0),
                source_urls=source_urls,
            )
            benchmarks[industry_name] = benchmark

        if not benchmarks:
            raise ValueError("No Damodaran industry benchmarks were parsed")
        return benchmarks

