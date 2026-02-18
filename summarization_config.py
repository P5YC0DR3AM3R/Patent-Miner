#!/usr/bin/env python3
"""Shared configuration for patent plain-English summarization."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Tuple

DEFAULT_MODEL_FILENAME = "mistral-7b-openorca.Q4_0.gguf"
DEFAULT_MODEL_DIR = Path.home() / ".patent-miner" / "models"

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


def resolve_model_location() -> Tuple[Path, str]:
    """Return configured model directory and filename."""

    model_dir = Path(os.getenv("PATENT_SUMMARY_MODEL_DIR", str(DEFAULT_MODEL_DIR))).expanduser()
    model_filename = os.getenv("PATENT_SUMMARY_MODEL_FILENAME", DEFAULT_MODEL_FILENAME).strip() or DEFAULT_MODEL_FILENAME
    return model_dir, model_filename

