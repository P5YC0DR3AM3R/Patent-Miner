#!/usr/bin/env python3
"""
Pre-generate plain-English AI summaries for all patents using the local Mistral model.

Usage:
    python3 generate_summaries.py

Reads all patents from the largest patent_discoveries_*.json file in the vault,
runs each one through the local Mistral GGUF model, and writes results to:
    patent_intelligence_vault/patent_summaries.json

Re-running is safe — existing summaries are preserved and only missing ones
are generated (unless --force is passed to regenerate all).

Options:
    --force     Regenerate all summaries even if already cached
    --limit N   Only generate for the first N patents (default: all)
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

VAULT_DIR = Path("./patent_intelligence_vault")
SUMMARIES_FILE = VAULT_DIR / "patent_summaries.json"

MODEL_DIR = "/Volumes/Elements/A003/Downloads/Capstone/CAPSTONE_UPDATED"
MODEL_FILENAME = "mistral-7b-openorca.Q4_0.gguf"

SUMMARY_PROMPT_TEMPLATE = """<|im_start|>system
You are a patent analyst who explains patents in plain English for business people.
<|im_end|>
<|im_start|>user
In 2-3 sentences, explain what this patent does and its most likely real-world use case. Avoid legal or technical jargon. Be specific and concrete.

Patent title: {title}
Abstract: {abstract}
<|im_end|>
<|im_start|>assistant
"""


def load_model():
    """Load the GGUF model. Exits with error if not found."""
    import os
    full_path = os.path.join(MODEL_DIR, MODEL_FILENAME)
    if not os.path.exists(full_path):
        print(f"ERROR: Model not found at {full_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading model: {MODEL_FILENAME} ...")
    from gpt4all import GPT4All
    model = GPT4All(
        model_name=MODEL_FILENAME,
        model_path=MODEL_DIR,
        allow_download=False,
        verbose=False,
    )
    print("Model loaded.\n")
    return model


def load_largest_discoveries() -> list:
    """Load patents from the largest discoveries JSON in the vault."""
    files = sorted(
        VAULT_DIR.glob("patent_discoveries_*.json"),
        key=lambda x: x.stat().st_size,
        reverse=True,
    )
    if not files:
        print("ERROR: No patent_discoveries_*.json found in vault.", file=sys.stderr)
        sys.exit(1)

    chosen = files[0]
    print(f"Loading patents from: {chosen.name}")
    patents = json.loads(chosen.read_text())
    print(f"Found {len(patents)} patents.\n")
    return patents


def load_existing_summaries() -> dict:
    """Load previously generated summaries if the file exists."""
    if SUMMARIES_FILE.exists():
        data = json.loads(SUMMARIES_FILE.read_text())
        print(f"Loaded {len(data)} existing summaries from {SUMMARIES_FILE.name}")
        return data
    return {}


def save_summaries(summaries: dict) -> None:
    """Write summaries dict to the JSON cache file."""
    VAULT_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARIES_FILE.write_text(json.dumps(summaries, indent=2, ensure_ascii=False))


def generate_summary(model, patent: dict) -> str:
    """Run the model on a single patent dict. Returns summary string."""
    title = patent.get("title") or "Unknown title"
    abstract = (patent.get("abstract") or "No abstract available.")[:800]
    prompt = SUMMARY_PROMPT_TEMPLATE.format(title=title, abstract=abstract)
    try:
        with model.chat_session():
            response = model.generate(
                prompt,
                max_tokens=256,
                temp=0.3,
                top_p=0.9,
                repeat_penalty=1.1,
            )
        return response.strip()
    except Exception as exc:
        return f"[Generation failed: {exc}]"


def main() -> None:
    parser = argparse.ArgumentParser(description="Pre-generate patent summaries.")
    parser.add_argument("--force", action="store_true", help="Regenerate all summaries")
    parser.add_argument("--limit", type=int, default=0, help="Limit to first N patents (0 = all)")
    args = parser.parse_args()

    patents = load_largest_discoveries()
    if args.limit > 0:
        patents = patents[: args.limit]
        print(f"Limiting to first {args.limit} patents.\n")

    existing = {} if args.force else load_existing_summaries()

    # Determine which patents still need summaries
    todo = [p for p in patents if str(p.get("patent_number", "")) not in existing]
    already_done = len(patents) - len(todo)

    if already_done:
        print(f"Skipping {already_done} already-cached summaries.")
    print(f"Generating summaries for {len(todo)} patents...\n")

    if not todo:
        print("Nothing to do. All summaries already generated.")
        print(f"Cache file: {SUMMARIES_FILE}")
        return

    model = load_model()
    summaries = dict(existing)  # start from existing cache

    total = len(todo)
    for i, patent in enumerate(todo, 1):
        patent_num = str(patent.get("patent_number", f"unknown_{i}"))
        title = (patent.get("title") or "")[:60]
        print(f"[{i:3d}/{total}] {patent_num}  {title}")

        t0 = time.time()
        summary = generate_summary(model, patent)
        elapsed = time.time() - t0

        summaries[patent_num] = summary
        print(f"         {elapsed:.1f}s  →  {summary[:80]}...")

        # Save after every patent so progress survives interruption
        save_summaries(summaries)

    print(f"\nDone. {len(summaries)} total summaries saved to {SUMMARIES_FILE}")


if __name__ == "__main__":
    main()
