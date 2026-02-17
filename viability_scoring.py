#!/usr/bin/env python3
"""Deterministic market viability scoring for Patent Miner."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, Tuple

from scoring_utils import clamp, tokenize_text

SCORING_VERSION = "v2.0.0"

DEFAULT_VIABILITY_COMPONENT_WEIGHTS: Dict[str, float] = {
    "market_demand": 0.28,
    "build_feasibility": 0.22,
    "competition_headroom": 0.18,
    "differentiation_potential": 0.18,
    "commercial_readiness": 0.14,
}

DEFAULT_OPPORTUNITY_WEIGHTS: Dict[str, float] = {
    "retrieval": 0.35,
    "viability": 0.45,
    "expiration": 0.20,
}

# Terms chosen for deterministic, explainable domain assignment.
MARKET_DOMAIN_TAXONOMY: Dict[str, Tuple[str, ...]] = {
    "healthcare_wearables": (
        "patient",
        "vital",
        "temperature",
        "heart",
        "physiological",
        "biometric",
        "wearable",
        "monitoring",
        "medical",
    ),
    "industrial_safety": (
        "gas",
        "toxic",
        "hazard",
        "osha",
        "industrial",
        "safety",
        "detector",
        "monitor",
        "compliance",
    ),
    "environmental_monitoring": (
        "air",
        "water",
        "environment",
        "quality",
        "pollution",
        "climate",
        "portable",
        "sensor",
    ),
    "precision_agriculture": (
        "soil",
        "moisture",
        "crop",
        "field",
        "agriculture",
        "irrigation",
        "farm",
        "ph",
    ),
    "consumer_iot": (
        "wireless",
        "network",
        "mobile",
        "app",
        "connected",
        "smart",
        "remote",
    ),
}

DEMAND_TERMS = {
    "automation",
    "real",
    "time",
    "safety",
    "health",
    "monitoring",
    "compliance",
    "efficiency",
    "predictive",
}

COMPLEXITY_TERMS = {
    "spectrometry",
    "chromatography",
    "calibration",
    "biochemical",
    "electrode",
    "multivariate",
    "algorithm",
    "multiplex",
}

COMPETITION_TERMS = {
    "system",
    "method",
    "platform",
    "network",
    "module",
    "device",
}

DIFFERENTIATION_TERMS = {
    "portable",
    "wireless",
    "integrated",
    "adaptive",
    "real",
    "time",
    "autonomous",
    "predictive",
}

READINESS_TERMS = {
    "prototype",
    "deployment",
    "production",
    "manufacturing",
    "kit",
    "portable",
    "apparatus",
}


def _iso_date(value: str | None) -> date | None:
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _compose_patent_text(patent: Dict[str, Any]) -> str:
    title = patent.get("title") or patent.get("patent_title") or ""
    abstract = patent.get("abstract") or patent.get("patent_abstract") or ""
    return f"{title} {abstract}"


def expiration_confidence_score(patent: Dict[str, Any], as_of_date: date | None = None) -> float:
    """Estimate confidence (0-10) that a patent is expired and actionable."""

    current = as_of_date or date.today()
    filing_date = _iso_date(str(patent.get("filing_date") or ""))
    grant_date = _iso_date(str(patent.get("patent_date") or ""))
    patent_type = str(patent.get("patent_type") or "").lower()

    if filing_date:
        age_years = max(0.0, (current - filing_date).days / 365.0)
        return round(clamp((age_years / 20.0) * 10.0), 3)

    if grant_date:
        threshold = 15.0 if patent_type == "design" else 20.0
        age_years = max(0.0, (current - grant_date).days / 365.0)
        return round(clamp((age_years / threshold) * 10.0), 3)

    return 2.0


def classify_market_domain(patent: Dict[str, Any]) -> Tuple[str, Dict[str, int]]:
    """Classify market domain and return per-domain match counts."""

    text = _compose_patent_text(patent)
    tokens = tokenize_text(text)
    token_set = set(tokens)

    scores: Dict[str, int] = {}
    for domain, terms in MARKET_DOMAIN_TAXONOMY.items():
        scores[domain] = sum(1 for term in terms if term in token_set)

    best_domain = max(scores, key=scores.get) if scores else "general_sensors"
    if scores.get(best_domain, 0) == 0:
        best_domain = "general_sensors"

    return best_domain, scores


def _component_score(tokens: set[str], positive_terms: set[str], baseline: float, scale: float) -> float:
    hits = sum(1 for term in positive_terms if term in tokens)
    return clamp(baseline + (hits * scale))


def compute_viability_scorecard(
    patent: Dict[str, Any],
    weights: Dict[str, float] | None = None,
    as_of_date: date | None = None,
) -> Dict[str, Any]:
    """Compute deterministic viability components and weighted total."""

    used_weights = dict(DEFAULT_VIABILITY_COMPONENT_WEIGHTS)
    if isinstance(weights, dict):
        used_weights.update({k: float(v) for k, v in weights.items() if k in used_weights})

    text = _compose_patent_text(patent)
    tokens = set(tokenize_text(text))

    market_domain, domain_hits = classify_market_domain(patent)

    market_demand = _component_score(tokens, DEMAND_TERMS, baseline=4.5, scale=0.8)

    complexity_penalty = _component_score(tokens, COMPLEXITY_TERMS, baseline=0.0, scale=0.9)
    build_feasibility = clamp(8.8 - complexity_penalty)

    competition_pressure = _component_score(tokens, COMPETITION_TERMS, baseline=0.0, scale=0.7)
    assignee_type = str(patent.get("assignee_type") or "")
    individual_bonus = 0.8 if assignee_type in {"4", "5", "14", "15"} else 0.0
    competition_headroom = clamp(7.0 - competition_pressure + individual_bonus)

    differentiation_potential = _component_score(tokens, DIFFERENTIATION_TERMS, baseline=4.2, scale=0.7)

    readiness_signal = _component_score(tokens, READINESS_TERMS, baseline=3.8, scale=0.6)
    expiration_signal = expiration_confidence_score(patent, as_of_date=as_of_date)
    commercial_readiness = clamp((readiness_signal * 0.6) + (expiration_signal * 0.4))

    components = {
        "market_demand": round(market_demand, 3),
        "build_feasibility": round(build_feasibility, 3),
        "competition_headroom": round(competition_headroom, 3),
        "differentiation_potential": round(differentiation_potential, 3),
        "commercial_readiness": round(commercial_readiness, 3),
    }

    total = sum(components[name] * used_weights[name] for name in used_weights)
    components["total"] = round(clamp(total), 3)

    return {
        "market_domain": market_domain,
        "domain_hits": domain_hits,
        "weights": used_weights,
        "components": components,
        "summary": (
            f"Domain={market_domain}; demand={components['market_demand']:.1f}, "
            f"feasibility={components['build_feasibility']:.1f}, "
            f"headroom={components['competition_headroom']:.1f}."
        ),
    }


def compute_opportunity_score_v2(
    retrieval_total: float,
    viability_total: float,
    expiration_confidence: float,
    scoring_weights: Dict[str, float] | None = None,
) -> float:
    """Blend retrieval, viability, and expiration confidence into final 0-10 score."""

    used_weights = dict(DEFAULT_OPPORTUNITY_WEIGHTS)
    if isinstance(scoring_weights, dict):
        for key in used_weights:
            if key in scoring_weights:
                used_weights[key] = float(scoring_weights[key])

    score = (
        retrieval_total * used_weights["retrieval"]
        + viability_total * used_weights["viability"]
        + expiration_confidence * used_weights["expiration"]
    )
    return round(clamp(score), 3)
