# Patent Detail Summary with Local Mistral Model

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a plain-English AI summary paragraph to the Patent Details tab, with the patent title and Justia link prominently at the top, powered by the local `mistral-7b-openorca.Q4_0.gguf` model via the GPT4All Python SDK.

**Architecture:** A new `patent_summarizer.py` module loads the GGUF model once via `@st.cache_resource` and exposes a `summarize_patent()` function. `render_patent_details()` in `streamlit_app.py` is updated to (1) show a title+link header block at the top, and (2) render a "Generate Summary" button that calls the summarizer and caches the result in `st.session_state`. The summary paragraph appears above the existing Retrieval/Viability/Opportunity cards under "Detailed Analysis".

**Tech Stack:** Python 3, Streamlit, `gpt4all>=2.0.0` Python SDK, `mistral-7b-openorca.Q4_0.gguf` at `/Volumes/Elements/A003/Downloads/Capstone/CAPSTONE_UPDATED/mistral-7b-openorca.Q4_0.gguf`

---

## Task 1: Install GPT4All Python SDK

**Files:**
- Modify: `requirements.txt`

**Step 1: Add gpt4all to requirements.txt**

Open `requirements.txt` and add this line under `# LLM Support`:
```
gpt4all>=2.0.0
```

**Step 2: Install it**

```bash
cd "/Volumes/Elements/Patent Miner"
pip install "gpt4all>=2.0.0"
```

Expected output: `Successfully installed gpt4all-...`

**Step 3: Verify the import works**

```bash
python3 -c "from gpt4all import GPT4All; print('OK')"
```

Expected: `OK`

**Step 4: Commit**

```bash
git add requirements.txt
git commit -m "feat: add gpt4all dependency for local patent summarization"
```

---

## Task 2: Create `patent_summarizer.py`

**Files:**
- Create: `patent_summarizer.py`

**Step 1: Write the module**

Create `/Volumes/Elements/Patent Miner/patent_summarizer.py` with this exact content:

```python
#!/usr/bin/env python3
"""Local Mistral-based patent summarizer using GPT4All SDK."""

from __future__ import annotations

from typing import Any, Dict

import streamlit as st

MODEL_PATH = (
    "/Volumes/Elements/A003/Downloads/Capstone/"
    "CAPSTONE_UPDATED/mistral-7b-openorca.Q4_0.gguf"
)

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

    if not os.path.exists(MODEL_PATH):
        return None

    # allow_download=False ensures it uses the local file only
    model = GPT4All(model_name=MODEL_PATH, allow_download=False, verbose=False)
    return model


def summarize_patent(patent: Dict[str, Any]) -> str:
    """Generate a plain-English summary for a patent dict.

    Returns the summary string, or an error message string if the model
    is unavailable or generation fails.
    """
    model = _load_model()
    if model is None:
        return (
            f"⚠️ Model not found at: {MODEL_PATH}. "
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
```

**Step 2: Verify the module imports cleanly (model load is deferred, so this is fast)**

```bash
cd "/Volumes/Elements/Patent Miner"
python3 -c "import patent_summarizer; print('import OK')"
```

Expected: `import OK`

**Step 3: Commit**

```bash
git add patent_summarizer.py
git commit -m "feat: add patent_summarizer module with local Mistral/GPT4All integration"
```

---

## Task 3: Update `render_patent_details()` — Title/Link Header Block

**Files:**
- Modify: `streamlit_app.py:996-1029`

**Step 1: Locate the function**

Open `streamlit_app.py`. Find `render_patent_details()` at line ~996. The current code after the selectbox looks like:

```python
    selected_label = st.selectbox("Select patent", list(options.keys()))
    patent = enriched[options[selected_label]]

    left, right = st.columns([1, 2])
    with left:
        st.metric("Opportunity Score", ...
```

**Step 2: Insert the title+link header block**

Replace this exact block:

```python
    selected_label = st.selectbox("Select patent", list(options.keys()))
    patent = enriched[options[selected_label]]

    left, right = st.columns([1, 2])
```

With:

```python
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
```

**Step 3: Remove the now-redundant title/link block inside the `right` column**

Find and remove these lines (they're now replaced by the header above):

```python
    with right:
        st.markdown(f"<div class='pm-card'><strong>Title</strong><br>{patent.get('title', 'N/A')}</div>", unsafe_allow_html=True)
        abstract = patent.get("abstract") or "No abstract available."
        st.markdown(f"<div class='pm-card'><strong>Abstract</strong><br>{abstract}</div>", unsafe_allow_html=True)

        # Add patent links
        patent_num = patent.get("patent_number", "N/A")
        if patent_num != "N/A":
            justia_url = get_justia_url(patent_num)
            st.markdown(f"🔗 [View on Justia Patents]({justia_url})")
```

Replace with:

```python
    with right:
        abstract = patent.get("abstract") or "No abstract available."
        st.markdown(
            f"<div class='pm-card'><strong>Abstract</strong><br>"
            f"<span style='line-height:1.6;'>{abstract}</span></div>",
            unsafe_allow_html=True,
        )
```

**Step 4: Reload the Streamlit app and verify the header renders correctly**

Navigate to Patent Details tab, select any patent. You should see a white card at the top with the patent number as a clickable blue link and the full title below it in bold.

**Step 5: Commit**

```bash
git add streamlit_app.py
git commit -m "feat: add patent title+link header block to Patent Details tab"
```

---

## Task 4: Update `render_patent_details()` — AI Summary Block

**Files:**
- Modify: `streamlit_app.py` — inside the `if show_advanced:` block, around line ~1083

**Step 1: Add the import at the top of streamlit_app.py**

Find the existing imports block at the top of the file (around line 16-22). Add:

```python
from patent_summarizer import summarize_patent
```

Place it after the existing local imports:
```python
from viability_scoring import (
    ...
)
from patent_summarizer import summarize_patent  # ← add here
```

**Step 2: Locate the "Detailed Analysis" section**

Find this line inside `render_patent_details()`:

```python
        st.markdown("**Detailed Analysis**")
        col1, col2, col3 = st.columns(3)
```

**Step 3: Insert the AI summary block above the three cards**

Replace:

```python
        st.markdown("**Detailed Analysis**")
        col1, col2, col3 = st.columns(3)
```

With:

```python
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
```

**Step 4: Reload the app and test the button**

1. Navigate to Patent Details tab
2. Select a patent
3. Scroll to "Detailed Analysis"
4. Click "🤖 Generate Plain-English Summary"
5. Spinner should appear for a few seconds (model loading first time ~5-10s)
6. A blue-left-bordered card appears with the plain-English summary
7. A "↺ Regenerate" button appears below it
8. Switch to a different patent — the button reappears (no cached summary for new patent)
9. Switch back to the original patent — summary is still there (cached in session_state)

**Step 5: Commit**

```bash
git add streamlit_app.py
git commit -m "feat: add GPT4All-powered plain-English patent summary to Detailed Analysis"
```

---

## Task 5: Smoke Test End-to-End

**Step 1: Run the app**

```bash
cd "/Volumes/Elements/Patent Miner"
streamlit run streamlit_app.py
```

**Step 2: Full verification checklist**

- [ ] Patent Details tab loads without errors
- [ ] Title/link header card shows patent number as blue clickable link
- [ ] Title appears bold below the number
- [ ] Clicking the link opens Justia in a new tab
- [ ] "Generate Summary" button is visible under "Detailed Analysis"
- [ ] Clicking it shows spinner
- [ ] After generation, a paragraph of plain English appears (not raw prompt text, not an error)
- [ ] "↺ Regenerate" button appears after first generation
- [ ] Switching patents resets to "Generate Summary" button for the new patent
- [ ] Returning to a previously-summarized patent shows cached result (no re-generation)
- [ ] If model file is missing, a clear `⚠️` error message is shown instead of crashing

**Step 3: Final commit**

```bash
git add -A
git commit -m "feat: patent detail summary complete - title header + local Mistral AI summary"
```
