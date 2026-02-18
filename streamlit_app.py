#!/usr/bin/env python3
"""Patent Miner Analytics Dashboard - legibility-first V3 UI."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

from patent_discovery import rerank_patent_candidates_v2
from viability_scoring import (
    SCORING_VERSION,
    compute_opportunity_score_v2,
    compute_viability_scorecard,
    expiration_confidence_score,
)
from patent_summarizer import summarize_patent

# Load environment variables
load_dotenv()

VIEW_TABS = [
    "Executive View",
    "Opportunity Ranking",
    "Patent Details",
    "Score Explainability",
    "💼 Business Intelligence",
    "Export",
]

REQUIRED_VIABILITY_KEYS = {
    "market_demand",
    "build_feasibility",
    "competition_headroom",
    "differentiation_potential",
    "commercial_readiness",
    "marketability",
    "viral_potential",
    "ease_of_use",
    "real_world_impact",
    "total",
}

TEXT_SIZE_OPTIONS = {
    "Standard": 16,
    "Large": 18,
    "XL": 20,
}

DENSITY_OPTIONS = {
    "Comfortable": 1.15,
    "Spacious": 1.3,
}

FALLBACK_SEARCH_CONFIG = {
    "keywords": ["portable", "sensor"],
    "retrieval_v2": {"max_expanded_keywords": 24},
    "scoring_weights": {"retrieval": 0.35, "viability": 0.45, "expiration": 0.20},
}

st.set_page_config(
    page_title="Patent Miner Analytics",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)


def get_justia_url(patent_number: str) -> str:
    """Generate Justia Patents URL for a given patent number."""
    clean_number = str(patent_number).strip().replace(',', '').replace(' ', '')
    return f"https://patents.justia.com/patent/{clean_number}"


def _inject_ui_css(text_size_label: str, density_label: str) -> None:
    """Apply dynamic CSS for enterprise-level kid-friendly design."""

    base_font = max(22, TEXT_SIZE_OPTIONS.get(text_size_label, 18) + 6)  # Boost font size
    density = DENSITY_OPTIONS.get(density_label, 1.15)
    heading_scale = 1.4 if base_font <= 22 else 1.5

    st.markdown(
        f"""
        <style>
        :root {{
            --pm-font-size: {base_font}px;
            --pm-line-height: {density + 0.2};
            --pm-heading-scale: {heading_scale};
            --pm-card-pad: {1.5 if density < 1.2 else 1.8}rem;
            --pm-gap: {1.2 if density < 1.2 else 1.4}rem;
            --pm-surface: #f0f5ff;
            --pm-border: #e0e8f5;
            --pm-accent: #0066ff;
            --pm-accent-secondary: #ff6b9d;
            --pm-accent-tertiary: #00d4aa;
            --pm-text: #a0a0a0;
            --pm-muted: #808080;
            --pm-shadow: 0 8px 24px rgba(0, 102, 255, 0.12);
            --pm-shadow-hover: 0 12px 32px rgba(0, 102, 255, 0.18);
        }}

        *:not([data-testid="stIconMaterial"]) {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif !important;
        }}

        html, body, [class*="css"]  {{
            font-size: var(--pm-font-size);
            line-height: var(--pm-line-height);
            color: var(--pm-text);
            background: linear-gradient(135deg, #f0f5ff 0%, #e6f2ff 50%, #f5e6ff 100%);
        }}

        /* Except for specific elements that should stay light/white */
        .stButton > button,
        .stDownloadButton > button {{
            color: white !important;
        }}

        .main {{
            background: transparent;
        }}

        /* ── Dataframe column-header popup menus ──────────────────────────────
           Confirmed via live DOM inspection: the popup is [data-testid="stDataFrameColumnMenu"]
           with data-baseweb="popover". It has transparent background and 24px font
           inherited from html/body, causing text overlap on whatever is behind it.
           Stable classes: e1gsdy3y0 (container), e1gsdy3y1 (menu items), e1gsdy3y3 (header). */
        [data-testid="stDataFrameColumnMenu"],
        [data-testid="stDataFrameColumnMenu"] * {{
            font-size: 14px !important;
            line-height: 1.5 !important;
            color: #1a1a1a !important;
            background-color: #ffffff !important;
            font-weight: 400 !important;
        }}

        /* Inner container — needs solid white background */
        [data-testid="stDataFrameColumnMenu"] .e1gsdy3y0 {{
            background: #ffffff !important;
            border-radius: 8px !important;
            box-shadow: 0 4px 16px rgba(0,0,0,0.15) !important;
            padding: 4px 0 !important;
        }}

        /* Menu item rows */
        [data-testid="stDataFrameColumnMenu"] .e1gsdy3y1 {{
            background: #ffffff !important;
            color: #1a1a1a !important;
            font-size: 14px !important;
            padding: 8px 16px !important;
            line-height: 1.5 !important;
            white-space: nowrap !important;
            cursor: pointer !important;
        }}

        [data-testid="stDataFrameColumnMenu"] .e1gsdy3y1:hover {{
            background: #f0f5ff !important;
        }}

        /* Column header row inside popup */
        [data-testid="stDataFrameColumnMenu"] .e1gsdy3y3 {{
            background: #ffffff !important;
            padding: 8px 12px !important;
        }}

        .main .block-container {{
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1400px;
        }}

        h1, h2, h3 {{
            letter-spacing: -0.03em;
            line-height: 1.15;
            font-weight: 800;
            color: var(--pm-text);
        }}

        h1 {{ 
            font-size: calc(var(--pm-font-size) * var(--pm-heading-scale) * 1.8);
            margin-bottom: 1.2rem;
            background: linear-gradient(135deg, var(--pm-accent) 0%, var(--pm-accent-secondary) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        h2 {{ 
            font-size: calc(var(--pm-font-size) * var(--pm-heading-scale) * 1.4);
            margin-top: 1.5rem;
            margin-bottom: 1rem;
            color: var(--pm-accent);
        }}
        h3 {{ 
            font-size: calc(var(--pm-font-size) * var(--pm-heading-scale) * 1.1);
            color: var(--pm-accent-secondary);
        }}

        .pm-card {{
            background: linear-gradient(135deg, #ffffff 0%, #f8fbff 100%);
            border: 2px solid var(--pm-border);
            border-radius: 24px;
            padding: var(--pm-card-pad);
            margin-bottom: var(--pm-gap);
            box-shadow: var(--pm-shadow);
            transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
            backdrop-filter: blur(10px);
            color: #1a1a1a !important;
        }}

        .pm-card * {{
            color: #1a1a1a !important;
        }}

        .pm-card:hover {{
            box-shadow: var(--pm-shadow-hover);
            transform: translateY(-4px);
            border-color: var(--pm-accent);
        }}

        .pm-muted {{ 
            color: var(--pm-muted);
            font-size: 0.92em;
            font-weight: 500;
        }}

        /* Streamlit Metrics */
        .metric-card, [data-testid="metric-container"] {{
            background: linear-gradient(135deg, #ffffff 0%, #f8fbff 100%) !important;
            border: 2px solid var(--pm-border) !important;
            border-radius: 20px !important;
            padding: 1.8rem !important;
            box-shadow: var(--pm-shadow) !important;
            transition: all 0.3s ease !important;
            color: #1a1a1a !important;
        }}

        [data-testid="metric-container"] * {{
            color: #1a1a1a !important;
        }}

        [data-testid="metric-container"]:hover {{
            box-shadow: var(--pm-shadow-hover) !important;
            transform: translateY(-4px) !important;
        }}

        /* Buttons */
        .stButton > button {{
            border-radius: 16px !important;
            padding: 0.8rem 2rem !important;
            font-size: calc(var(--pm-font-size) * 0.95) !important;
            font-weight: 700 !important;
            border: none !important;
            background: linear-gradient(135deg, var(--pm-accent) 0%, #0052cc 100%) !important;
            color: white !important;
            box-shadow: 0 6px 20px rgba(0, 102, 255, 0.3) !important;
            transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
            cursor: pointer !important;
            height: auto !important;
            letter-spacing: 0.5px !important;
        }}

        .stButton > button:hover {{
            box-shadow: 0 10px 28px rgba(0, 102, 255, 0.4) !important;
            transform: translateY(-3px) !important;
            background: linear-gradient(135deg, #0052cc 0%, var(--pm-accent) 100%) !important;
        }}

        .stButton > button:active {{
            transform: translateY(-1px) !important;
        }}

        /* Download Buttons */
        .stDownloadButton > button {{
            border-radius: 16px !important;
            padding: 0.8rem 2rem !important;
            font-size: calc(var(--pm-font-size) * 0.95) !important;
            font-weight: 700 !important;
            border: none !important;
            background: linear-gradient(135deg, var(--pm-accent-tertiary) 0%, #00a887 100%) !important;
            color: white !important;
            box-shadow: 0 6px 20px rgba(0, 212, 170, 0.3) !important;
            transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
            cursor: pointer !important;
            height: auto !important;
        }}

        .stDownloadButton > button:hover {{
            box-shadow: 0 10px 28px rgba(0, 212, 170, 0.4) !important;
            transform: translateY(-3px) !important;
        }}

        /* Tabs */
        /* Hide Streamlit deploy button and menu */
        [data-testid="stToolbar"] {{
            display: none !important;
        }}

        /* Hide top menu bar */
        header {{
            display: none !important;
        }}

        [data-testid="stHeader"] {{
            display: none !important;
        }}

        .stApp > header {{
            display: none !important;
        }}

        .stTabs [role="tablist"] {{
            gap: 0.8rem;
            border-bottom: 3px solid var(--pm-border);
            padding-bottom: 1rem;
        }}

        .stTabs [role="tab"] {{
            background: linear-gradient(135deg, #ffffff 0%, #f8fbff 100%);
            border: 2px solid var(--pm-border);
            border-bottom: 3px solid transparent;
            border-radius: 16px 16px 0 0;
            padding: 0.9rem 1.8rem;
            font-weight: 700;
            font-size: calc(var(--pm-font-size) * 0.95);
            color: #1a1a1a !important;
            transition: all 0.3s ease;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            cursor: pointer;
        }}

        .stTabs [role="tab"]:hover {{
            background: linear-gradient(135deg, #f0f5ff 0%, #e6f2ff 100%);
            color: #1a1a1a !important;
            box-shadow: 0 6px 16px rgba(0, 102, 255, 0.1);
            transform: translateY(-2px);
        }}

        .stTabs [aria-selected="true"] {{
            background: linear-gradient(135deg, #ffffff 0%, #f0f5ff 100%);
            color: #1a1a1a !important;
            border-color: var(--pm-accent);
            border-bottom-color: var(--pm-accent);
            box-shadow: 0 8px 20px rgba(0, 102, 255, 0.3);
        }}

        .stTabs [role="tab"] * {{
            color: #1a1a1a !important;
        }}

        .stTabs [aria-selected="true"] * {{
            color: #1a1a1a !important;
        }}

        /* Data Frames & Tables */
        .stDataFrame, .stTable {{
            border: 2px solid var(--pm-border);
            border-radius: 18px;
            padding: 0.5rem;
            box-shadow: var(--pm-shadow);
            overflow: hidden;
            color: #1a1a1a !important;
        }}

        .stDataFrame * , .stTable * {{
            color: #1a1a1a !important;
        }}

        /* Inputs */
        .stSelectbox, .stSlider, .stTextInput {{
            font-size: calc(var(--pm-font-size) * 0.95) !important;
        }}

        .stSelectbox > div > div, .stTextInput > div > div {{
            border-radius: 14px !important;
            border: 2px solid var(--pm-border) !important;
            padding: 0.9rem 1.2rem !important;
            background: white !important;
            color: #1a1a1a !important;
            transition: all 0.3s ease !important;
        }}

        .stSelectbox > div > div *, .stTextInput > div > div * {{
            color: #1a1a1a !important;
        }}

        .stSelectbox > div > div:hover, .stTextInput > div > div:hover {{
            border-color: var(--pm-accent) !important;
            box-shadow: 0 4px 12px rgba(0, 102, 255, 0.1) !important;
        }}

        .stSelectbox > div > div:focus-within, .stTextInput > div > div:focus-within {{
            border-color: var(--pm-accent) !important;
            box-shadow: 0 0 0 3px rgba(0, 102, 255, 0.1) !important;
        }}

        /* Info/Warning/Error boxes */
        .stInfo {{
            background: linear-gradient(135deg, #e6f2ff 0%, #f0f5ff 100%) !important;
            border-left: 4px solid var(--pm-accent) !important;
            border-radius: 14px !important;
            padding: 1.2rem 1.6rem !important;
            box-shadow: var(--pm-shadow) !important;
            font-size: calc(var(--pm-font-size) * 0.95) !important;
            color: #1a1a1a !important;
        }}

        .stInfo * {{
            color: #1a1a1a !important;
        }}

        .stSuccess {{
            background: linear-gradient(135deg, #e6ffe6 0%, #f0fff0 100%) !important;
            border-left: 4px solid var(--pm-accent-tertiary) !important;
            border-radius: 14px !important;
            padding: 1.2rem 1.6rem !important;
            box-shadow: var(--pm-shadow) !important;
            font-size: calc(var(--pm-font-size) * 0.95) !important;
            color: #1a1a1a !important;
        }}

        .stSuccess * {{
            color: #1a1a1a !important;
        }}

        .stWarning {{
            background: linear-gradient(135deg, #fff5e6 0%, #fffbf0 100%) !important;
            border-left: 4px solid #ff9500 !important;
            border-radius: 14px !important;
            padding: 1.2rem 1.6rem !important;
            box-shadow: var(--pm-shadow) !important;
            font-size: calc(var(--pm-font-size) * 0.95) !important;
            color: #1a1a1a !important;
        }}

        .stWarning * {{
            color: #1a1a1a !important;
        }}

        .stError {{
            background: linear-gradient(135deg, #ffe6e6 0%, #fff0f0 100%) !important;
            border-left: 4px solid #ff4757 !important;
            border-radius: 14px !important;
            padding: 1.2rem 1.6rem !important;
            box-shadow: var(--pm-shadow) !important;
            font-size: calc(var(--pm-font-size) * 0.95) !important;
            color: #1a1a1a !important;
        }}

        .stError * {{
            color: #1a1a1a !important;
        }}

        /* Divider */
        hr {{
            border: none;
            height: 2px;
            background: linear-gradient(90deg, transparent 0%, var(--pm-border) 50%, transparent 100%);
            margin: 2rem 0 !important;
        }}

        /* Sidebar */
        .css-1d391kg {{
            background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
            border-right: 2px solid var(--pm-border);
        }}

        .css-1d391kg * {{
            color: #1a1a1a !important;
        }}

        /* Headers in sidebar */
        .sidebar-header {{
            font-size: calc(var(--pm-font-size) * 1.1);
            font-weight: 800;
            color: #808080 !important;
            margin-bottom: 1.2rem;
        }}

        /* Sidebar labels and text */
        .css-1d391kg label,
        .css-1d391kg h3,
        .css-1d391kg .stMarkdown {{
            color: #1a1a1a !important;
        }}

        /* Expander - hide headers completely in BI sections */
        [data-testid="stExpander"] {{
            border: none !important;
            margin-bottom: 0.5rem !important;
        }}
        
        [data-testid="stExpander"] details {{
            border: 1px solid var(--pm-border) !important;
            border-radius: 12px !important;
            padding: 0.5rem !important;
            background: white !important;
            color: #1a1a1a !important;
        }}

        [data-testid="stExpander"] details * {{
            color: #1a1a1a !important;
        }}
        
        [data-testid="stExpander"] summary {{
            display: none !important;
            height: 0 !important;
            padding: 0 !important;
            margin: 0 !important;
            overflow: hidden !important;
            visibility: hidden !important;
        }}
        
        .streamlit-expanderHeader {{
            display: none !important;
            height: 0 !important;
            padding: 0 !important;
            margin: 0 !important;
            overflow: hidden !important;
            visibility: hidden !important;
        }}

        .streamlit-expanderHeader:hover {{
            display: none !important;
        }}
        
        [data-testid="stExpander"] [data-testid="stExpanderDetails"] {{
            padding: 0.5rem !important;
        }}

        /* Plotly Charts */
        .plotly-container {{
            border-radius: 18px !important;
            overflow: hidden;
            box-shadow: var(--pm-shadow);
        }}

        /* General Text */
        p {{
            font-size: var(--pm-font-size);
            line-height: var(--pm-line-height);
            color: var(--pm-text);
            margin-bottom: 1rem;
        }}

        /* Caption */
        .stCaption {{
            font-size: calc(var(--pm-font-size) * 0.85);
            color: var(--pm-muted);
            font-weight: 500;
        }}

        /* Links */
        a {{
            color: var(--pm-accent) !important;
            text-decoration: none !important;
            font-weight: 600 !important;
            transition: all 0.2s ease !important;
        }}

        a:hover {{
            color: var(--pm-accent-secondary) !important;
            text-decoration: underline !important;
        }}

        /* Toggle Switch */
        .stCheckbox > label > div {{
            border-radius: 12px !important;
        }}

        /* Minor Improvements */
        .stMetricDelta {{
            font-size: calc(var(--pm-font-size) * 0.9) !important;
        }}

        /* Responsive */
        @media (max-width: 768px) {{
            .main .block-container {{
                padding: 1rem;
            }}
            
            .stTabs [role="tab"] {{
                padding: 0.7rem 1.2rem;
                font-size: calc(var(--pm-font-size) * 0.85);
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


class PatentAnalyzer:
    """Load and present patent discoveries with compatibility-aware enrichment."""

    def __init__(self, vault_dir: str = "./patent_intelligence_vault/"):
        self.vault_dir = Path(vault_dir)
        self.vault_dir.mkdir(parents=True, exist_ok=True)
        self.patents: List[Dict[str, Any]] = []
        self.loaded_filename = ""
        self._enriched_cache: List[Dict[str, Any]] = []
        self.load_latest_discoveries()

    def load_latest_discoveries(self) -> bool:
        """Load the patent discoveries file with the MOST patents."""

        discovery_files = sorted(
            self.vault_dir.glob("patent_discoveries_*.json"),
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )

        if not discovery_files:
            st.warning("No patent discoveries found. Run the discovery first.")
            return False

        try:
            # ALWAYS find and load the file with the most patents
            largest_file = None
            largest_count = 0
            
            for f in discovery_files:
                with f.open("r") as handle:
                    test_data = json.load(handle)
                if len(test_data) > largest_count:
                    largest_file = f
                    largest_count = len(test_data)
            
            # Load the largest dataset
            with largest_file.open("r") as handle:
                data = json.load(handle)
            
            self.patents = data
            self.loaded_filename = largest_file.name
            self._enriched_cache = []  # CLEAR CACHE
            
            # Show info about loaded dataset
            timestamp = largest_file.stem.split('_')[-2:]
            st.info(f"📊 Loaded {len(self.patents)} patents from {largest_file.name}")
            
            return True
        except Exception as exc:
            st.error(f"Error loading discoveries: {exc}")
            return False

    def _score_legacy_patents(self, patents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Backfill V2 scorecards when older discovery artifacts are loaded."""

        if not patents:
            return []

        fallback_records: List[Dict[str, Any]] = []
        for patent in patents:
            pat = dict(patent)
            pat.setdefault("_retrieval_pass_hits", ["single_pass"])
            fallback_records.append(pat)

        ranked = rerank_patent_candidates_v2(fallback_records, FALLBACK_SEARCH_CONFIG)

        enriched: List[Dict[str, Any]] = []
        for patent in ranked:
            patent_copy = dict(patent)
            if "viability_scorecard" not in patent_copy:
                viability = compute_viability_scorecard(patent_copy)
                patent_copy["viability_scorecard"] = viability["components"]
                patent_copy["market_domain"] = viability["market_domain"]
                patent_copy["scoring_version"] = SCORING_VERSION
                patent_copy.setdefault("explanations", {})
                patent_copy["explanations"].setdefault("viability", viability["summary"])

            retrieval_total = patent_copy.get("retrieval_scorecard", {}).get("total", 0.0)
            viability_total = patent_copy.get("viability_scorecard", {}).get("total", 0.0)
            expiration_total = expiration_confidence_score(patent_copy)

            if "opportunity_score_v2" not in patent_copy:
                patent_copy["opportunity_score_v2"] = compute_opportunity_score_v2(
                    retrieval_total=float(retrieval_total),
                    viability_total=float(viability_total),
                    expiration_confidence=float(expiration_total),
                    scoring_weights=FALLBACK_SEARCH_CONFIG["scoring_weights"],
                )

            patent_copy["opportunity_score"] = float(patent_copy.get("opportunity_score_v2", 0.0))
            patent_copy["score_components"] = patent_copy.get("viability_scorecard", {})

            patent_copy.setdefault("explanations", {})
            patent_copy["explanations"].setdefault(
                "retrieval",
                "Legacy artifact backfilled with deterministic retrieval scoring.",
            )
            patent_copy["explanations"].setdefault(
                "opportunity",
                (
                    f"Blended score from retrieval={retrieval_total:.2f}, "
                    f"viability={viability_total:.2f}, expiration={expiration_total:.2f}."
                ),
            )

            enriched.append(patent_copy)

        return sorted(enriched, key=lambda row: row.get("opportunity_score_v2", 0.0), reverse=True)

    def get_enriched_patents(self) -> List[Dict[str, Any]]:
        """Return patents with v2 retrieval/viability scorecards available."""

        # Don't use cache if patents were just reloaded
        if self._enriched_cache and len(self._enriched_cache) == len(self.patents):
            return self._enriched_cache

        if not self.patents:
            return []

        has_v2_scores = all(
            "retrieval_scorecard" in patent and "viability_scorecard" in patent
            for patent in self.patents
        )

        if has_v2_scores:
            enriched = [dict(patent) for patent in self.patents]
            for patent in enriched:
                viability = patent.get("viability_scorecard", {})
                needs_refresh = (
                    not REQUIRED_VIABILITY_KEYS.issubset(set(viability))
                    or patent.get("scoring_version") != SCORING_VERSION
                )

                if needs_refresh:
                    refreshed = compute_viability_scorecard(patent)
                    viability = refreshed["components"]
                    patent["viability_scorecard"] = viability
                    patent["market_domain"] = refreshed["market_domain"]
                    patent["scoring_version"] = SCORING_VERSION
                    patent.setdefault("explanations", {})
                    patent["explanations"]["viability"] = refreshed["summary"]

                retrieval_total = patent.get("retrieval_scorecard", {}).get("total", 0.0)
                viability_total = viability.get("total", 0.0)
                expiration_total = expiration_confidence_score(patent)

                if "opportunity_score_v2" not in patent or needs_refresh:
                    patent["opportunity_score_v2"] = compute_opportunity_score_v2(
                        retrieval_total=float(retrieval_total),
                        viability_total=float(viability_total),
                        expiration_confidence=float(expiration_total),
                    )

                patent["opportunity_score"] = float(patent.get("opportunity_score_v2", 0.0))
                patent["score_components"] = viability

            enriched.sort(key=lambda row: row.get("opportunity_score_v2", 0.0), reverse=True)
            self._enriched_cache = enriched
            return enriched

        self._enriched_cache = self._score_legacy_patents(self.patents)
        return self._enriched_cache

    def get_statistics(self) -> Dict[str, Any]:
        """Calculate analytics statistics."""

        enriched = self.get_enriched_patents()
        if not enriched:
            return {}

        df = pd.DataFrame(enriched)
        filing_dates = pd.to_datetime(df.get("filing_date"), errors="coerce")
        filing_dates = filing_dates.dropna()

        if filing_dates.empty:
            date_range = "Unknown"
        else:
            date_range = f"{filing_dates.min().date()} to {filing_dates.max().date()}"

        avg_opportunity = float(df.get("opportunity_score_v2", pd.Series(dtype=float)).mean() or 0.0)

        return {
            "total_patents": len(df),
            "date_range": date_range,
            "avg_opportunity": round(avg_opportunity, 2),
            "assignee_types": df.get("assignee_type", pd.Series(dtype=str)).value_counts().to_dict(),
            "patent_types": df.get("patent_type", pd.Series(dtype=str)).value_counts().to_dict(),
            "domains": df.get("market_domain", pd.Series(dtype=str)).value_counts().to_dict(),
        }

    def get_patents_by_year(self) -> pd.DataFrame:
        """Get yearly patent distribution."""

        df = pd.DataFrame(self.get_enriched_patents())
        if df.empty:
            return pd.DataFrame({"year": [], "count": []})

        df["filing_date"] = pd.to_datetime(df.get("filing_date"), errors="coerce")
        df = df.dropna(subset=["filing_date"])
        if df.empty:
            return pd.DataFrame({"year": [], "count": []})

        df["year"] = df["filing_date"].dt.year
        return df.groupby("year").size().reset_index(name="count")

    def get_domain_distribution(self) -> pd.DataFrame:
        """Get market domain distribution."""

        df = pd.DataFrame(self.get_enriched_patents())
        if df.empty:
            return pd.DataFrame({"market_domain": [], "count": []})

        dist = df.get("market_domain", pd.Series(dtype=str)).fillna("unknown").value_counts().reset_index()
        dist.columns = ["market_domain", "count"]
        return dist

    def load_analysis_results(self) -> Dict[str, Any] | None:
        """Load the latest expired patent analysis results."""

        analysis_files = sorted(
            self.vault_dir.glob("patent_analysis_results_*.json"),
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )

        if not analysis_files:
            return None

        try:
            with analysis_files[0].open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except Exception:
            return None

    def load_rankings_csv(self) -> pd.DataFrame | None:
        """Load the latest patent rankings CSV."""

        ranking_files = sorted(
            self.vault_dir.glob("patent_rankings_*.csv"),
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )

        if not ranking_files:
            return None

        try:
            return pd.read_csv(ranking_files[0])
        except Exception:
            return None

    def load_markdown_report_path(self) -> Path | None:
        """Get the latest markdown report file path."""

        report_files = sorted(
            self.vault_dir.glob("EXPIRED_PATENT_REPORT_*.md"),
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )

        return report_files[0] if report_files else None


@st.cache_resource
def get_analyzer() -> PatentAnalyzer:
    """Cache analyzer to avoid reloads on every interaction."""

    return PatentAnalyzer()


def render_header(analyzer: PatentAnalyzer) -> None:
    """Render page title and data status."""

    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("Patent Miner V3")
        st.caption("Hybrid retrieval + deterministic market viability scoring")
    with col2:
        if st.button("Refresh Data", use_container_width=True):
            st.cache_resource.clear()
            st.rerun()

    


def render_sidebar_controls() -> Dict[str, Any]:
    """Return default settings without rendering controls."""
    return {
        "text_size": "Large",
        "density": "Comfortable",
        "show_advanced": True,
    }


def render_executive_view(analyzer: PatentAnalyzer, show_advanced: bool) -> None:
    """Executive summary tab."""

    stats = analyzer.get_statistics()
    if not stats:
        st.info("No summary available.")
        return

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Patents", f"{stats['total_patents']:,}")
    with col2:
        st.metric("Average Opportunity", f"{stats['avg_opportunity']:.2f}/10")
    with col3:
        st.metric("Assignee Types", len(stats["assignee_types"]))
    with col4:
        st.metric("Market Domains", len(stats["domains"]))

    domain_dist = analyzer.get_domain_distribution()
    if not domain_dist.empty:
        fig = px.line(
            domain_dist.sort_values('count', ascending=False),
            x="market_domain",
            y="count",
            title="Domain Distribution",
            markers=True,
            line_shape="linear"
        )
        fig.update_traces(line=dict(color="#00d4aa", width=3), marker=dict(size=8))
        fig.update_layout(height=360, hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No market domain distribution available.")

    if show_advanced:
        st.subheader("Domain Counts")
        st.dataframe(
            pd.DataFrame(
                [{"domain": domain, "count": count} for domain, count in stats["domains"].items()]
            ),
            use_container_width=True,
            hide_index=True,
        )


def render_opportunity_ranking(analyzer: PatentAnalyzer, show_advanced: bool) -> None:
    """Ranking table tab with concise readability-first summaries."""

    enriched = analyzer.get_enriched_patents()
    if not enriched:
        st.info("No patent data available.")
        return

    max_display = min(75, len(enriched))
    top_n = st.slider("Show top patents", min_value=5, max_value=max_display, value=min(20, max_display))

    rows: List[Dict[str, Any]] = []
    for patent in enriched[:top_n]:
        patent_num = patent.get("patent_number", "N/A")
        justia_url = get_justia_url(patent_num)
        rows.append(
            {
                "Patent #": patent_num,
                "Title": patent.get("title", ""),
                "Justia Link": justia_url,
                "Score": f"{patent.get('opportunity_score_v2', 0.0):.2f}",
                "Domain": patent.get("market_domain", "unknown"),
                "Filed": str(patent.get("filing_date") or "")[:10],
                "Why Ranked": patent.get("explanations", {}).get("opportunity", ""),
            }
        )

    df_display = pd.DataFrame(rows)
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Justia Link": st.column_config.LinkColumn(
                "🔗 Justia",
                display_text="View",
                width="small"
            )
        }
    )

    if show_advanced:
        st.subheader("Advanced Retrieval Signals")
        advanced_rows = []
        for patent in enriched[:top_n]:
            retrieval = patent.get("retrieval_scorecard", {})
            advanced_rows.append(
                {
                    "Patent #": patent.get("patent_number", "N/A"),
                    "Retrieval Total": retrieval.get("total", 0.0),
                    "Exact Match": retrieval.get("title_exact_match", 0.0),
                    "Coverage": retrieval.get("query_coverage", 0.0),
                    "Semantic": retrieval.get("semantic_similarity", 0.0),
                    "Passes": ", ".join(patent.get("_retrieval_pass_hits", [])),
                }
            )
        st.dataframe(pd.DataFrame(advanced_rows), use_container_width=True, hide_index=True)


def render_patent_details(analyzer: PatentAnalyzer, show_advanced: bool) -> None:
    """Detailed patent inspection tab."""

    enriched = analyzer.get_enriched_patents()
    if not enriched:
        st.info("No patent data available.")
        return

    options = {
        f"{patent.get('patent_number', 'N/A')} | {str(patent.get('title', ''))[:70]}": idx
        for idx, patent in enumerate(enriched[:200])
    }

    selected_label = st.selectbox("Select patent", list(options.keys()))
    patent = enriched[options[selected_label]]

    # ── Title + Link Header ───────────────────────────────────────────────────
    patent_num = patent.get("patent_number", "N/A")
    patent_title = patent.get("title") or "Untitled"
    justia_url = get_justia_url(patent_num) if patent_num != "N/A" else None
    link_html = (
        f"<a href='{justia_url}' target='_blank' "
        f"style='color:#0066ff;font-weight:700;text-decoration:none;font-size:0.95em;'>"
        f"🔗 {patent_num}</a>"
        if justia_url else f"<span style='color:#0066ff;font-weight:700;'>{patent_num}</span>"
    )
    st.markdown(
        f"""<div class='pm-card' style='margin-bottom:1rem;'>
        <div style='font-size:0.9em;color:#808080;margin-bottom:0.3rem;'>Patent Number</div>
        <div style='font-size:1.3em;font-weight:800;color:#1a1a1a;margin-bottom:0.5rem;'>
            {link_html}
        </div>
        <div style='font-size:1.05em;font-weight:600;color:#1a1a2e;line-height:1.4;'>
            {patent_title}
        </div>
        </div>""",
        unsafe_allow_html=True,
    )

    left, right = st.columns([1, 2])
    with left:
        st.metric("Opportunity Score", f"{patent.get('opportunity_score_v2', 0.0):.2f}/10")
        st.metric("Patent Number", patent.get("patent_number", "N/A"))
        st.metric("Filed", str(patent.get("filing_date") or "N/A")[:10])
        st.metric("Issued", str(patent.get("patent_date") or "N/A")[:10])
        st.metric("Domain", patent.get("market_domain", "unknown"))

    with right:
        abstract = patent.get("abstract") or "No abstract available."
        st.markdown(
            f"<div class='pm-card'><strong>Abstract</strong><br>"
            f"<span style='line-height:1.6;'>{abstract}</span></div>",
            unsafe_allow_html=True,
        )

    viability = patent.get("viability_scorecard", {})
    st.subheader("🚀 Marketability Snapshot")
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Marketability", f"{viability.get('marketability', 0.0):.1f}/10")
        st.caption("How easy this is to sell")
    with m2:
        st.metric("Viral Impact", f"{viability.get('viral_potential', 0.0):.1f}/10")
        st.caption("Built-in sharing/network effects")
    with m3:
        st.metric("Ease of Use", f"{viability.get('ease_of_use', 0.0):.1f}/10")
        st.caption("Simple for everyday users")
    with m4:
        st.metric("Real-World Need", f"{viability.get('real_world_impact', 0.0):.1f}/10")
        st.caption("Solves a meaningful problem")

    if show_advanced:
        st.subheader("Scoring Rationale")
        explanations = patent.get("explanations", {})
        retrieval = patent.get("retrieval_scorecard", {})

        scores = {
            "Retrieval": float(retrieval.get("total", 0.0)),
            "Viability": float(viability.get("total", 0.0)),
            "Expiration": float(retrieval.get("expiration_confidence", 0.0)),
            "Opportunity": float(patent.get("opportunity_score_v2", 0.0)),
        }

        st.markdown("**Score Breakdown**")
        chart_data = pd.DataFrame({
            "Component": list(scores.keys()),
            "Score": list(scores.values())
        })
        fig = px.line(
            chart_data,
            x="Component",
            y="Score",
            title="",
            markers=True,
            line_shape="spline"
        )
        fig.update_traces(line=dict(color="#0066ff", width=4), marker=dict(size=12))
        fig.update_yaxes(range=[0, 10])
        fig.update_layout(
            showlegend=False,
            hovermode="x unified",
            margin=dict(l=40, r=40, t=20, b=40),
            font=dict(size=14),
            height=300
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("**Detailed Analysis**")

        # ── AI Plain-English Summary ──────────────────────────────────────────
        summary_key = f"summary_{patent.get('patent_number', 'unknown')}"
        if summary_key not in st.session_state:
            st.session_state[summary_key] = None

        if st.session_state[summary_key] is None:
            if st.button("🤖 Generate Plain-English Summary", key=f"btn_{summary_key}"):
                with st.spinner("Generating summary with local Mistral model…"):
                    st.session_state[summary_key] = summarize_patent(patent)
                st.rerun()
        else:
            st.markdown(
                f"""<div class='pm-card' style='border-left:4px solid #0066ff;margin-bottom:1rem;'>
                <div style='font-size:0.85em;font-weight:700;color:#0066ff;
                            text-transform:uppercase;letter-spacing:0.05em;
                            margin-bottom:0.6rem;'>
                    🤖 AI Use-Case Summary
                </div>
                <div style='color:#1a1a2e;font-size:1em;line-height:1.7;'>
                    {st.session_state[summary_key]}
                </div>
                </div>""",
                unsafe_allow_html=True,
            )
            if st.button("↺ Regenerate", key=f"regen_{summary_key}"):
                st.session_state[summary_key] = None
                st.rerun()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(
                f"""<div class='pm-card' style='color: #1a1a2e;'>
                <strong style='font-size: 1.2em; color: #0066ff;'>🔍 Retrieval</strong>
                <br><br>
                <span style='color: #1a1a2e; font-size: 0.95em; line-height: 1.6;'>
                {explanations.get('retrieval', 'No data')}
                </span>
                </div>""",
                unsafe_allow_html=True
            )

        with col2:
            st.markdown(
                f"""<div class='pm-card' style='color: #1a1a2e;'>
                <strong style='font-size: 1.2em; color: #00d4aa;'>✅ Viability</strong>
                <br><br>
                <span style='color: #1a1a2e; font-size: 0.95em; line-height: 1.6;'>
                {explanations.get('viability', 'No data')}
                </span>
                </div>""",
                unsafe_allow_html=True
            )

        with col3:
            st.markdown(
                f"""<div class='pm-card' style='color: #1a1a2e;'>
                <strong style='font-size: 1.2em; color: #ff6b9d;'>⭐ Opportunity</strong>
                <br><br>
                <span style='color: #1a1a2e; font-size: 0.95em; line-height: 1.6;'>
                {explanations.get('opportunity', 'No data')}
                </span>
                </div>""",
                unsafe_allow_html=True
            )


def render_score_explainability(analyzer: PatentAnalyzer) -> None:
    """Explainability tab with component comparison."""

    enriched = analyzer.get_enriched_patents()
    if not enriched:
        st.info("No patent data available.")
        return

    top_n = min(30, len(enriched))
    selected = enriched[:top_n]

    score_rows: List[Dict[str, Any]] = []
    for patent in selected:
        retrieval = patent.get("retrieval_scorecard", {})
        viability = patent.get("viability_scorecard", {})
        patent_num = patent.get("patent_number", "N/A")
        score_rows.append(
            {
                "Patent #": patent_num,
                "Justia Link": get_justia_url(patent_num) if patent_num != "N/A" else "",
                "Retrieval": retrieval.get("total", 0.0),
                "Viability": viability.get("total", 0.0),
                "Opportunity": patent.get("opportunity_score_v2", 0.0),
            }
        )

    score_df = pd.DataFrame(score_rows)
    st.dataframe(
        score_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Justia Link": st.column_config.LinkColumn(
                "🔗 Justia",
                display_text="View",
                width="small"
            )
        }
    )

    chart_df = score_df.melt(id_vars=["Patent #"], value_vars=["Retrieval", "Viability", "Opportunity"])
    fig = px.line(
        chart_df,
        x="Patent #",
        y="value",
        color="variable",
        title="Score Component Comparison (Top Candidates)",
        markers=True,
        line_shape="spline"
    )
    fig.update_layout(height=420, hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)


def render_export(analyzer: PatentAnalyzer) -> None:
    """Export tab with CSV/JSON downloads."""

    enriched = analyzer.get_enriched_patents()
    if not enriched:
        st.info("No data to export.")
        return

    export_df = pd.DataFrame(enriched)

    csv_buffer = export_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download CSV",
        data=csv_buffer,
        file_name=f"patents_export_v3_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
    )

    json_data = json.dumps(enriched, indent=2, default=str)
    st.download_button(
        label="Download JSON",
        data=json_data,
        file_name=f"patents_export_v3_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json",
    )

    preview_cols = [
        col for col in ["patent_number", "title", "market_domain", "opportunity_score_v2"] if col in export_df.columns
    ]
    st.dataframe(export_df[preview_cols], use_container_width=True, hide_index=True)


def render_business_intelligence(analyzer: PatentAnalyzer) -> None:
    """Business Intelligence analysis tab with rankings and recommendations."""

    analysis_results = analyzer.load_analysis_results()
    rankings_df = analyzer.load_rankings_csv()
    report_path = analyzer.load_markdown_report_path()

    if analysis_results is None and rankings_df is None:
        st.info("📊 No Business Intelligence analysis available yet. Run `python run_expired_patent_analysis.py` to generate.")
        return

    # ===== EXECUTIVE SUMMARY SECTION =====
    st.header("📊 Expired Patent Business Intelligence")

    # Full Report Link
    if report_path:
        with open(report_path, "r") as f:
            report_content = f.read()
        
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"**📄 Full Report:** `{report_path.name}`")
        with col2:
            st.download_button(
                "📥 Download Report",
                data=report_content,
                file_name=report_path.name,
                mime="text/markdown",
            )

    st.divider()

    if analysis_results:
        dataset_size = analysis_results.get("dataset_size", 0)
        
        # Parse tier counts from patents data
        patents_data = analysis_results.get("patents", [])
        tier_counts = {
            1: sum(1 for p in patents_data if p.get("strategic_assessment", {}).get("recommendation_tier") == 1),
            2: sum(1 for p in patents_data if p.get("strategic_assessment", {}).get("recommendation_tier") == 2),
            3: sum(1 for p in patents_data if p.get("strategic_assessment", {}).get("recommendation_tier") == 3),
        }

        # Calculate financial metrics
        total_npv = sum(p.get("financial_metrics", {}).get("npv_base", 0) for p in patents_data)
        avg_score = sum(p.get("integrated_score", 0) for p in patents_data) / len(patents_data) if patents_data else 0

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📁 Total Patents", f"{dataset_size:,}")
        with col2:
            st.metric("🎯 Tier 1 (Ready)", f"{tier_counts[1]} patents")
        with col3:
            st.metric("🔍 Tier 2 (Investigate)", f"{tier_counts[2]} patents")
        with col4:
            st.metric("💰 Portfolio NPV", f"${total_npv:,.0f}")

        st.markdown(f"**Average Integrated Score:** {avg_score:.2f}/10.0")

    # ===== TAB SECTION WITHIN BI TAB =====
    bi_subtabs = st.tabs(["Rankings", "Financial", "Themes & Risk", "Recommendations", "Detailed View"])

    with bi_subtabs[0]:  # Rankings
        st.subheader("🏆 Patent Rankings by Tier")
        
        if rankings_df is not None:
            # Show tier breakdown
            tier_filter = st.selectbox("Filter by Recommendation Tier:", ["All", "Tier 1 (Ready)", "Tier 2 (Investigate)", "Tier 3 (Monitor)"])
            
            if tier_filter == "All":
                display_df = rankings_df.copy()
            elif tier_filter == "Tier 1 (Ready)":
                display_df = rankings_df[rankings_df["Recommendation_Tier"] == 1]
            elif tier_filter == "Tier 2 (Investigate)":
                display_df = rankings_df[rankings_df["Recommendation_Tier"] == 2]
            else:
                display_df = rankings_df[rankings_df["Recommendation_Tier"] == 3]

            if not display_df.empty:
                # Clean Patent_Number column
                display_df = display_df.copy()
                if 'Patent_Number' in display_df.columns:
                    display_df['Patent_Number'] = display_df['Patent_Number'].astype(str).str.strip()
                    # Add Justia link column
                    display_df['Justia_Link'] = display_df['Patent_Number'].apply(get_justia_url)
                
                # Format display columns - showing all top 50 patents
                display_cols = ["Rank", "Patent_Number", "Title", "Justia_Link", "Integrated_Score", "Confidence", 
                               "Technology_Theme", "Recommendation_Tier"]
                available_cols = [c for c in display_cols if c in display_df.columns]
                
                # Display top 50 with clickable Justia links
                st.dataframe(
                    display_df[available_cols].head(50),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Rank": st.column_config.NumberColumn("Rank", width="small"),
                        "Patent_Number": st.column_config.TextColumn("Patent #", width="small"),
                        "Integrated_Score": st.column_config.NumberColumn("Score", format="%.2f"),
                        "Justia_Link": st.column_config.LinkColumn(
                            "🔗 Justia",
                            display_text="View",
                            width="small"
                        )
                    }
                )
                
                st.caption(f"Showing top 50 of {len(display_df)} patents in this tier")

                # Download ranking CSV
                csv_data = display_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "📥 Download Full Rankings (CSV)",
                    data=csv_data,
                    file_name=f"business_intelligence_rankings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                )
            else:
                st.info(f"No patents found for {tier_filter}.")

    with bi_subtabs[1]:  # Financial
        st.subheader("💰 Financial Analysis")
        
        if rankings_df is not None and "NPV_Base" in rankings_df.columns:
            # Financial metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_npv = rankings_df["NPV_Base"].sum()
                st.metric("Total Portfolio NPV", f"${total_npv:,.0f}")
            
            with col2:
                avg_npv = rankings_df["NPV_Base"].mean()
                st.metric("Average NPV", f"${avg_npv:,.0f}")
            
            with col3:
                positive_npv = (rankings_df["NPV_Base"] > 0).sum()
                st.metric("Positive NPV Patents", f"{positive_npv}/{len(rankings_df)}")

            # NPV Distribution Chart
            st.subheader("NPV Distribution")
            npv_sorted = rankings_df.sort_values('NPV_Base').reset_index(drop=True)
            npv_sorted['index'] = range(len(npv_sorted))
            npv_chart = px.line(
                npv_sorted,
                x="index",
                y="NPV_Base",
                title="Patent NPV Distribution",
                markers=True,
                line_shape="spline"
            )
            npv_chart.update_traces(line=dict(color="#0066ff", width=3), marker=dict(size=6))
            npv_chart.update_xaxes(title="Patent Index (sorted by NPV)")
            npv_chart.update_yaxes(title="NPV (Base Case)")
            npv_chart.update_layout(height=350, hovermode="x unified")
            st.plotly_chart(npv_chart, use_container_width=True)

            # Top Financial Performers
            st.subheader("🏅 Top Financial Performers (NPV Base)")
            top_financial = rankings_df.nlargest(10, "NPV_Base")[
                ["Rank", "Patent_Number", "Title", "NPV_Base", "Recommendation_Tier"]
            ].copy()
            # Clean Patent_Number column
            if 'Patent_Number' in top_financial.columns:
                top_financial['Patent_Number'] = top_financial['Patent_Number'].astype(str).str.strip()
                # Add Justia link
                top_financial['Justia_Link'] = top_financial['Patent_Number'].apply(get_justia_url)
            # Reorder columns
            top_financial = top_financial[["Rank", "Patent_Number", "Title", "Justia_Link", "NPV_Base", "Recommendation_Tier"]]
            st.dataframe(
                top_financial,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Justia_Link": st.column_config.LinkColumn(
                        "🔗 Justia",
                        display_text="View",
                        width="small"
                    )
                }
            )

    with bi_subtabs[2]:  # Themes & Risk
        st.subheader("🔬 Technology Themes & Risk Assessment")
        
        if rankings_df is not None:
            # Technology Theme Distribution
            if "Technology_Theme" in rankings_df.columns:
                col1, col2 = st.columns(2)
                
                with col1:
                    theme_counts = rankings_df["Technology_Theme"].value_counts().reset_index()
                    theme_counts.columns = ["Technology_Theme", "count"]
                    theme_counts = theme_counts.sort_values('count', ascending=False)
                    fig_theme = px.line(
                        theme_counts,
                        x="Technology_Theme",
                        y="count",
                        title="Distribution by Technology Theme",
                        markers=True,
                        line_shape="linear"
                    )
                    fig_theme.update_traces(line=dict(color="#ff6b9d", width=3), marker=dict(size=8))
                    fig_theme.update_layout(height=350, hovermode="x unified")
                    st.plotly_chart(fig_theme, use_container_width=True)
                
                with col2:
                    st.markdown("**Theme Breakdown:**")
                    for theme, count in theme_counts.items():
                        st.write(f"- {theme}: {count} patents")

            # Manufacturing Feasibility
            if "Manufacturing_Feasibility" in rankings_df.columns:
                st.subheader("Manufacturing Feasibility Scores")
                feas_sorted = rankings_df.sort_values('Manufacturing_Feasibility').reset_index(drop=True)
                feas_sorted['index'] = range(len(feas_sorted))
                feasibility_chart = px.line(
                    feas_sorted,
                    x="index",
                    y="Manufacturing_Feasibility",
                    title="Manufacturing Feasibility Distribution (1-10)",
                    markers=True,
                    line_shape="spline"
                )
                feasibility_chart.update_traces(line=dict(color="#00d4aa", width=3), marker=dict(size=6))
                feasibility_chart.update_xaxes(title="Patent Index (sorted by Feasibility)")
                feasibility_chart.update_yaxes(title="Manufacturing Feasibility Score")
                feasibility_chart.update_layout(height=300, hovermode="x unified")
                st.plotly_chart(feasibility_chart, use_container_width=True)

            # Risk Indicators
            st.subheader("⚠️ Risk Indicators")
            if "Red_Flags" in rankings_df.columns:
                flagged = rankings_df[rankings_df["Red_Flags"].notna() & (rankings_df["Red_Flags"] != "")]
                st.metric("Patents with Red Flags", f"{len(flagged)}/{len(rankings_df)}")
                
                if not flagged.empty:
                    st.markdown("")
                    st.write("**Patents Requiring Further Investigation:**")
                    st.markdown("")
                    for idx, row in flagged.iterrows():
                        # Ensure patent number is clean string
                        patent_num = str(row['Patent_Number']).strip()
                        justia_url = get_justia_url(patent_num)
                        
                        st.markdown(f"""<div style='background: #fff5e6; border: 2px solid #ff9500; border-radius: 12px; 
                                    padding: 1rem; margin-bottom: 0.8rem;'>
                                    <strong style='color: #ff9500;'>⚠️ <a href='{justia_url}' target='_blank' style='color: #ff9500; text-decoration: none;'>{patent_num}</a></strong><br>
                                    <span style='color: #606060;'>{row['Title'][:80]}...</span>
                                    </div>""", unsafe_allow_html=True)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Rank:** {row['Rank']}")
                        with col2:
                            st.write(f"**Score:** {row['Integrated_Score']:.2f}/10")
                        st.write(f"**Red Flags:** {row['Red_Flags']}")
                        st.markdown("---")

    with bi_subtabs[3]:  # Recommendations
        st.subheader("✅ Actionable Recommendations")
        
        if rankings_df is not None:
            # Group by tier
            tier_1_df = rankings_df[rankings_df["Recommendation_Tier"] == 1]
            tier_2_df = rankings_df[rankings_df["Recommendation_Tier"] == 2]
            tier_3_df = rankings_df[rankings_df["Recommendation_Tier"] == 3]

            # Tier 1 Recommendations
            if not tier_1_df.empty:
                st.markdown("")
                st.markdown("### 🎯 **Tier 1: Immediate Implementation**")
                st.markdown(
                    "These patents are ready for pilot projects or phased implementation. "
                    "High technical merit, strong financial case, and manageable risk."
                )
                st.markdown("")
                
                for idx, patent in tier_1_df.head(5).iterrows():
                    # Ensure patent number is clean string
                    patent_num = str(patent['Patent_Number']).strip()
                    justia_url = get_justia_url(patent_num)
                    
                    # Create a bordered container for each patent
                    st.markdown(f"""<div style='background: white; border: 2px solid #e0e8f5; border-radius: 12px; 
                                padding: 1.2rem; margin-bottom: 1rem; box-shadow: 0 4px 12px rgba(0,0,0,0.05);'>
                                <strong style='color: #0066ff; font-size: 1.1em;'>✅ <a href='{justia_url}' target='_blank' style='color: #0066ff; text-decoration: none;'>{patent_num}</a></strong><br>
                                <span style='color: #606060;'>{patent['Title'][:100]}...</span><br>
                                <span style='color: #00d4aa; font-weight: 600;'>Score: {patent['Integrated_Score']:.2f}</span> | 
                                <a href='{justia_url}' target='_blank' style='color: #0066ff; text-decoration: none;'>🔗 View on Justia</a>
                                </div>""", unsafe_allow_html=True)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Integrated Score", f"{patent['Integrated_Score']:.2f}/10")
                    with col2:
                        st.metric("Manufacturing Feasibility", f"{patent['Manufacturing_Feasibility']:.1f}/10" if "Manufacturing_Feasibility" in patent else "N/A")
                    with col3:
                        st.metric("NPV (Base)", f"${patent['NPV_Base']:,.0f}" if "NPV_Base" in patent else "N/A")
                    
                    st.markdown("**Recommended Next Steps:**")
                    st.markdown("1. Conduct detailed FTO analysis")
                    st.markdown("2. Perform lab validation trials")
                    st.markdown("3. Benchmark against current production")
                    st.markdown("4. Plan pilot project scope & budget")
                    st.markdown("---")

            # Tier 2 Recommendations
            if not tier_2_df.empty:
                st.markdown("")
                st.divider()
                st.markdown("")
                st.markdown("### 🔍 **Tier 2: Further Investigation Required**")
                st.markdown(
                    "These patents show promise but require additional R&D, FTO analysis, or validation."
                )
                st.markdown("")
                
                # Create clean copy of dataframe for display
                tier_2_summary = tier_2_df[["Patent_Number", "Title", "Integrated_Score", "Technology_Theme"]].head(10).copy()
                # Ensure Patent_Number is clean string
                tier_2_summary['Patent_Number'] = tier_2_summary['Patent_Number'].astype(str).str.strip()
                # Add Justia link
                tier_2_summary['Justia_Link'] = tier_2_summary['Patent_Number'].apply(get_justia_url)
                # Reorder columns
                tier_2_summary = tier_2_summary[["Patent_Number", "Title", "Justia_Link", "Integrated_Score", "Technology_Theme"]]
                st.dataframe(
                    tier_2_summary,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Justia_Link": st.column_config.LinkColumn(
                            "🔗 Justia",
                            display_text="View",
                            width="small"
                        )
                    }
                )
                
                st.markdown("**Common Investigation Areas:**")
                st.markdown("- Detailed engineering feasibility assessment")
                st.markdown("- Freedom to operate analysis")
                st.markdown("- Regulatory and compliance review")
                st.markdown("- Market opportunity validation")

            # Tier 3 Overview
            if not tier_3_df.empty:
                st.markdown("")
                st.divider()
                st.markdown("")
                st.markdown("### 📋 **Tier 3: Monitor or Defer**")
                st.metric("Patents in Tier 3", len(tier_3_df))
                st.markdown("These patents have technical or financial concerns. Review if circumstances change or market evolves.")

    with bi_subtabs[4]:  # Detailed View
        st.subheader("🔬 Detailed Patent Analysis")
        
        if analysis_results is not None and patents_data:
            # Select a patent
            patent_options = {
                f"{p['patent_number']}: {p['title'][:60]}...": idx 
                for idx, p in enumerate(patents_data[:100])
            }
            
            selected_patent_label = st.selectbox("Select patent for detailed view:", list(patent_options.keys()))
            selected_idx = patent_options[selected_patent_label]
            patent = patents_data[selected_idx]
            
            # Display Justia link for selected patent
            patent_num = patent.get('patent_number', 'N/A')
            if patent_num != 'N/A':
                justia_url = get_justia_url(patent_num)
                st.markdown(f"[View {patent_num} on Justia Patents 🔗]({justia_url})", unsafe_allow_html=True)

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Integrated Score", f"{patent.get('integrated_score', 0):.2f}/10")
            with col2:
                st.metric("Ranking Position", f"#{patent.get('ranking_position', 'N/A')}")
            with col3:
                tier = patent.get("strategic_assessment", {}).get("recommendation_tier", "N/A")
                st.metric("Tier", f"Tier {tier}" if tier != "N/A" else "N/A")
            with col4:
                st.metric("Confidence", f"{patent.get('confidence_level', 0)*100:.0f}%")

            # Technical Scores
            st.subheader("📊 Technical Scores (1-10 scale)")
            tech_scores = patent.get("technical_scores", {})
            if tech_scores:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Scientific Robustness", f"{tech_scores.get('scientific_robustness', 0):.1f}")
                with col2:
                    st.metric("Manufacturing Feasibility", f"{tech_scores.get('manufacturing_feasibility_current', 0):.1f}")
                with col3:
                    st.metric("Modernization Potential", f"{tech_scores.get('modernization_potential', 0):.1f}")
                with col4:
                    st.metric("Technical Risk (Inverted)", f"{tech_scores.get('technical_implementation_risk_inverted', 0):.1f}")

            # Financial Metrics
            st.subheader("💰 Financial Metrics")
            fin_metrics = patent.get("financial_metrics", {})
            if fin_metrics:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("NPV (Base)", f"${fin_metrics.get('npv_base', 0):,.0f}")
                with col2:
                    st.metric("Payback Period", f"{fin_metrics.get('payback_period_years', 0):.1f} years")
                with col3:
                    st.metric("IRR", f"{fin_metrics.get('irr_percent', 0):.1f}%")

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("NPV (Optimistic)", f"${fin_metrics.get('npv_optimistic', 0):,.0f}")
                with col2:
                    st.metric("NPV (Pessimistic)", f"${fin_metrics.get('npv_pessimistic', 0):,.0f}")
                with col3:
                    st.metric("Annual Cost Savings", f"${fin_metrics.get('annual_cost_savings', 0):,.0f}")

            # Manufacturing Profile
            st.subheader("🏭 Manufacturing Profile")
            mfg_profile = patent.get("manufacturing_profile", {})
            if mfg_profile:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("TRL Estimate", f"{mfg_profile.get('trl_estimate', 0)}/9")
                with col2:
                    st.metric("Production Type", mfg_profile.get('production_type', 'N/A').title())
                with col3:
                    st.metric("Modernization Timeline", f"~{mfg_profile.get('modernization_timeline_months', 0)} months")

                st.write(f"**Capex Range:** ${mfg_profile.get('capex_low', 0):,.0f} - ${mfg_profile.get('capex_high', 0):,.0f}")
                st.write(f"**Annual Opex Change:** ${mfg_profile.get('opex_annual_change', 0):,.0f}")

            # Strategic Assessment
            st.subheader("🎯 Strategic Assessment")
            strat = patent.get("strategic_assessment", {})
            if strat:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Strategic Fit", f"{strat.get('strategic_fit_score', 0):.1f}/10")
                with col2:
                    st.metric("Competitive Advantage", f"{strat.get('competitive_advantage_potential', 0):.1f}/10")
                with col3:
                    st.metric("Market Opportunity", strat.get('market_size_opportunity', 'N/A').title())

            # Red Flags
            if patent.get("red_flags"):
                st.subheader("⚠️ Red Flags")
                for flag in patent["red_flags"]:
                    st.warning(f"• {flag}")

            # Key Insights
            if patent.get("key_insights"):
                st.subheader("💡 Key Insights")
                for insight in patent["key_insights"]:
                    st.info(f"• {insight}")

            # Patent Metadata
            st.subheader("📄 Patent Metadata")
            st.write(f"**Patent Number:** {patent.get('patent_number', 'N/A')}")
            st.write(f"**Title:** {patent.get('title', 'N/A')}")
            st.write(f"**Technology Theme:** {patent.get('technology_theme', 'N/A')}")
            st.write(f"**Patent Type:** {patent.get('patent_type_classified', 'N/A')}")
            st.write(f"**Filing Date:** {patent.get('filing_date', 'N/A')}")
            st.write(f"**Patent Date:** {patent.get('patent_date', 'N/A')}")

            if patent.get("abstract"):
                st.subheader("📋 Abstract")
                st.write(patent["abstract"])



def render_footer() -> None:
    """Render footer metadata."""

    st.divider()
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.caption("Patent Miner V3 - Hybrid Retrieval + Viability Intelligence")
    with col2:
        st.caption(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    with col3:
        st.caption("Data: PatentsView")


def render_banner() -> None:
    """Render top advertising banner with contact links."""
    
    st.markdown("""
        <div style='background: linear-gradient(135deg, #0066ff 0%, #00d4aa 100%); 
                    padding: 1rem 2rem; 
                    border-radius: 12px; 
                    margin-bottom: 1.5rem;
                    box-shadow: 0 8px 24px rgba(0, 102, 255, 0.3);
                    text-align: center;'>
            <h3 style='color: white !important; margin: 0; padding: 0; font-size: 1.8em; font-weight: 800;'>
                🆓 FREE Patent Miner from Micah Read MGMT
            </h3>
            <div style='margin-top: 0.8rem;'>
                <a href='https://www.linkedin.com/in/micahread/' target='_blank' 
                   style='color: white !important; text-decoration: none; margin: 0 1rem; font-weight: 600; font-size: 1.1em;'>
                    💼 LinkedIn
                </a>
                <span style='color: white; opacity: 0.5;'>|</span>
                <a href='https://github.com/p5yc0dr3am3r/' target='_blank' 
                   style='color: white !important; text-decoration: none; margin: 0 1rem; font-weight: 600; font-size: 1.1em;'>
                    🔧 GitHub
                </a>
                <span style='color: white; opacity: 0.5;'>|</span>
                <a href='mailto:micahreadmgmt@gmail.com' 
                   style='color: white !important; text-decoration: none; margin: 0 1rem; font-weight: 600; font-size: 1.1em;'>
                    📧 Email
                </a>
            </div>
        </div>
    """, unsafe_allow_html=True)


def main() -> None:
    """Main Streamlit app entrypoint."""

    controls = render_sidebar_controls()
    _inject_ui_css(controls["text_size"], controls["density"])

    # Render advertising banner at the top
    render_banner()

    analyzer = get_analyzer()
    render_header(analyzer)

    if not analyzer.patents:
        st.error("No patent data available. Run the discovery pipeline first.")
        st.stop()

    tab_exec, tab_rank, tab_details, tab_explain, tab_bi, tab_export = st.tabs(VIEW_TABS)

    with tab_exec:
        render_executive_view(analyzer, show_advanced=controls["show_advanced"])

    with tab_rank:
        render_opportunity_ranking(analyzer, show_advanced=controls["show_advanced"])

    with tab_details:
        render_patent_details(analyzer, show_advanced=controls["show_advanced"])

    with tab_explain:
        render_score_explainability(analyzer)

    with tab_bi:
        render_business_intelligence(analyzer)

    with tab_export:
        render_export(analyzer)

    render_footer()


if __name__ == "__main__":
    main()
