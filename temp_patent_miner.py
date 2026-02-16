#!/usr/bin/env python3
"""Patent Miner discovery runner (API-first)."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Tuple

from patent_discovery import (
    PatentDiscoveryError,
    discover_patents,
    save_discovery_diagnostics,
)
from patent_miner_config import DEFAULT_CONFIG, build_config


def run_discovery(config: Dict[str, Any] | None = None) -> Tuple[list[dict], dict]:
    """Run patent discovery and persist primary artifacts."""

    cfg = build_config(config or DEFAULT_CONFIG)
    output_dir = cfg.get("output_dir", "./patent_intelligence_vault/")
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    search_cfg = cfg.get("patent_search", {})

    print("=" * 80)
    print("PATENT MINER ENTERPRISE - DISCOVERY")
    print("=" * 80)
    print(f"Provider: {search_cfg.get('provider', 'patentsview_patentsearch')}")
    print(f"Keywords: {search_cfg.get('keywords', [])}")
    print(f"Requested results: {search_cfg.get('num_results', 0)}")

    try:
        patents, diagnostics = discover_patents(cfg)
    except PatentDiscoveryError as exc:
        diagnostics = exc.diagnostics or {
            "provider": search_cfg.get("provider", "patentsview_patentsearch"),
            "status": "failed",
            "errors": [str(exc)],
        }
        diagnostics_path = save_discovery_diagnostics(output_dir, diagnostics, timestamp)

        print("\n[DISCOVERY FAILED]")
        print(f"Code: {exc.code}")
        print(f"Reason: {exc.message}")
        print(f"Diagnostics: {diagnostics_path}")

        raise

    discoveries_path = Path(output_dir) / f"patent_discoveries_{timestamp}.json"
    with open(discoveries_path, "w", encoding="utf-8") as handle:
        json.dump(patents, handle, indent=2, ensure_ascii=False)

    diagnostics_path = save_discovery_diagnostics(output_dir, diagnostics, timestamp)

    print("\n[DISCOVERY COMPLETE]")
    print(f"Found patents: {len(patents)}")
    print(f"Discoveries file: {discoveries_path}")
    print(f"Diagnostics file: {diagnostics_path}")

    return patents, diagnostics


def main() -> int:
    """CLI entrypoint."""

    try:
        run_discovery()
    except PatentDiscoveryError:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
