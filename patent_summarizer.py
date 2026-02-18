#!/usr/bin/env python3
"""Local Mistral-based patent summarizer using GPT4All SDK."""

from __future__ import annotations

from typing import Any, Dict

import streamlit as st

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


@st.cache_resource(show_spinner=False)
def _load_model():
    """Load the GGUF model once per Streamlit session."""
    import os
    from gpt4all import GPT4All

    full_path = os.path.join(MODEL_DIR, MODEL_FILENAME)
    if not os.path.exists(full_path):
        return None

    # model_name = filename, model_path = directory containing it
    model = GPT4All(
        model_name=MODEL_FILENAME,
        model_path=MODEL_DIR,
        allow_download=False,
        verbose=False,
    )
    return model


def summarize_patent(patent: Dict[str, Any]) -> str:
    """Generate a plain-English summary for a patent dict.

    Returns the summary string, or an error message string if the model
    is unavailable or generation fails.
    """
    model = _load_model()
    if model is None:
        return (
            f"⚠️ Model not found at: {MODEL_DIR}/{MODEL_FILENAME}. "
            "Check that the file exists and the path is correct."
        )

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
        return f"⚠️ Summary generation failed: {exc}"
