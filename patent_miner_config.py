#!/usr/bin/env python3
"""Shared configuration for Patent Miner discovery pipeline."""

from __future__ import annotations

import copy
import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from patent_discovery import DEFAULT_PATENT_SEARCH_CONFIG

# Load environment variables from .env file
load_dotenv()


DEFAULT_CONFIG: Dict[str, Any] = {
    "patent_search": {
        **DEFAULT_PATENT_SEARCH_CONFIG,
        "api_key_env": os.getenv("PATENT_SEARCH_API_KEY_ENV", "PATENTSVIEW_API_KEY"),
        "keywords": ["portable", "sensor"],
        "filing_date_start": "1975-01-01",
        "filing_date_end": "2005-12-31",
        "assignee_type": "individual",
        "num_results": 500,
        "require_likely_expired": True,
        "allow_legacy_scrape_fallback": False,
    },
    "output_dir": "./patent_intelligence_vault/",
}


def build_config(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create a deep-copied runtime config with optional overrides."""

    cfg = copy.deepcopy(DEFAULT_CONFIG)
    if not overrides:
        return cfg

    for key, value in overrides.items():
        if key == "patent_search" and isinstance(value, dict):
            cfg["patent_search"].update(value)
        else:
            cfg[key] = value
    return cfg
