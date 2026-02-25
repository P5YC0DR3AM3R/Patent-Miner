# Enterprise Dark Mode Redesign — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform Patent Miner from a light-theme Streamlit dashboard with poor readability and monotonous charts into an enterprise-grade dark mode experience with appropriate chart types, uniform buttons, and sidebar navigation.

**Architecture:** Single-file overhaul of `streamlit_app.py`. Rewrite CSS injection function for dark theme. Convert top-tab navigation to sidebar radio. Replace all `px.line` charts with semantically correct chart types using Plotly's `graph_objects` for radar/area-band charts. Add `plotly.graph_objects` import alongside existing `plotly.express`.

**Tech Stack:** Streamlit, Plotly Express + Graph Objects, Pandas, Python 3.10+

**Design doc:** `docs/plans/2026-02-25-enterprise-dark-mode-redesign.md`

---

### Task 1: Add imports and shared Plotly dark template config

**Files:**
- Modify: `streamlit_app.py:1-35` (imports and constants)

**Step 1: Add `plotly.graph_objects` import**

At line 12, after `import plotly.express as px`, add:

```python
import plotly.graph_objects as go
```

**Step 2: Add Plotly dark template constant**

After `FALLBACK_SEARCH_CONFIG` (line 65), add:

```python
PM_COLORS = ["#6366f1", "#22d3ee", "#10b981", "#f59e0b", "#f43f5e", "#a78bfa", "#67e8f9"]

PM_DARK_LAYOUT = dict(
    paper_bgcolor="#12121a",
    plot_bgcolor="#12121a",
    font=dict(color="#e2e8f0", size=13, family="-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"),
    colorway=PM_COLORS,
    hoverlabel=dict(bgcolor="#1a1a2e", font_size=13, bordercolor="#6366f1"),
    xaxis=dict(gridcolor="#1e293b", zerolinecolor="#1e293b"),
    yaxis=dict(gridcolor="#1e293b", zerolinecolor="#1e293b"),
    margin=dict(l=40, r=40, t=40, b=40),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#94a3b8")),
)
```

**Step 3: Replace `VIEW_TABS` with sidebar navigation map**

Replace the `VIEW_TABS` list (lines 28-35) with:

```python
NAV_OPTIONS = {
    "Dashboard": "dashboard",
    "Rankings": "rankings",
    "Patent Explorer": "explorer",
    "Score Analysis": "scores",
    "Business Intel": "bi",
    "Export": "export",
}
```

**Step 4: Commit**

```bash
git add streamlit_app.py
git commit -m "refactor: add plotly dark template and sidebar nav constants"
```

---

### Task 2: Rewrite `_inject_ui_css()` with dark theme

**Files:**
- Modify: `streamlit_app.py:133-647` (the entire `_inject_ui_css` function)

**Step 1: Replace the full `_inject_ui_css` function**

Replace the function body (lines 133-647) with the dark mode CSS. Key changes:

- `:root` variables use dark palette (`--pm-bg-deep: #0a0a0f`, `--pm-surface: #12121a`, `--pm-text: #e2e8f0`)
- `html, body` background: `#0a0a0f` (solid dark, no gradient)
- `.pm-card`: glassmorphism (`rgba(255,255,255,0.03)`, `backdrop-filter: blur(12px)`, border `rgba(99,102,241,0.15)`)
- `.pm-card *` text: `#e2e8f0` (not `#1a1a1a`)
- All `[data-testid="metric-container"]`: dark surface background, light text
- Buttons: 4 variant classes via role-based gradient system
  - `.stButton > button`: indigo gradient (`#6366f1 → #4f46e5`)
  - `.stDownloadButton > button`: emerald gradient (`#10b981 → #059669`)
  - All share: `border-radius: 12px`, `transition: 0.25s cubic-bezier(0.34,1.56,0.64,1)`
  - Hover: `translateY(-2px)` + intensified glow shadow
  - Active: `scale(0.98)` snap-back
- Tabs (`.stTabs`): dark surface, indigo active indicator, light text
- DataFrames: dark background, light text
- Sidebar: dark gradient background
- Info/Warning/Error boxes: dark variants with left accent border
- Inputs: dark backgrounds with subtle borders
- Add `@keyframes fadeIn` and `@keyframes fadeInUp` for content transitions
- Add `.pm-card-emerald`, `.pm-card-amber`, `.pm-card-rose` for score-colored borders
- Expander styling: dark background, visible header (remove `display: none` on summary)

Full CSS is ~500 lines. The key structural change from current: every `#ffffff` or `#f0f5ff` becomes `#12121a` or `#0a0a0f`, every `#1a1a1a` text color becomes `#e2e8f0`, and the `--pm-text: #a0a0a0` (the readability killer) becomes `--pm-text: #e2e8f0`.

**Step 2: Commit**

```bash
git add streamlit_app.py
git commit -m "style: rewrite CSS to enterprise dark mode theme"
```

---

### Task 3: Convert navigation from tabs to sidebar radio

**Files:**
- Modify: `streamlit_app.py:929-935` (`render_sidebar_controls`)
- Modify: `streamlit_app.py:1928-1964` (`main`)
- Modify: `tests/test_streamlit_data_flow.py:104-118` (update navigation test)

**Step 1: Rewrite `render_sidebar_controls` to include navigation**

Replace the function (lines 929-935) with:

```python
def render_sidebar_controls() -> Dict[str, Any]:
    """Sidebar: navigation + display settings."""
    with st.sidebar:
        st.markdown(
            "<div style='padding:1rem 0 1.5rem;'>"
            "<h2 style='color:#e2e8f0;margin:0;font-size:1.4em;'>Patent Miner</h2>"
            "<p style='color:#94a3b8;margin:0.2rem 0 0;font-size:0.85em;'>Intelligence Platform</p>"
            "</div>",
            unsafe_allow_html=True,
        )
        page = st.radio(
            "Navigation",
            list(NAV_OPTIONS.keys()),
            label_visibility="collapsed",
        )
        st.divider()
        text_size = st.selectbox("Text Size", list(TEXT_SIZE_OPTIONS.keys()), index=1)
        density = st.selectbox("Density", list(DENSITY_OPTIONS.keys()), index=0)
        show_advanced = st.toggle("Show Advanced Details", value=True)

    return {
        "page": NAV_OPTIONS[page],
        "text_size": text_size,
        "density": density,
        "show_advanced": show_advanced,
    }
```

**Step 2: Rewrite `main()` to use page routing instead of tabs**

Replace `main()` (lines 1928-1968) with:

```python
def main() -> None:
    """Main Streamlit app entrypoint."""
    controls = render_sidebar_controls()
    _inject_ui_css(controls["text_size"], controls["density"])

    render_banner()
    analyzer = get_analyzer()

    if not analyzer.patents:
        st.error("No patent data available. Run the discovery pipeline first.")
        st.stop()

    render_header(analyzer)

    page = controls["page"]
    if page == "dashboard":
        render_executive_view(analyzer, show_advanced=controls["show_advanced"])
    elif page == "rankings":
        render_opportunity_ranking(analyzer, show_advanced=controls["show_advanced"])
    elif page == "explorer":
        render_patent_details(analyzer, show_advanced=controls["show_advanced"])
    elif page == "scores":
        render_score_explainability(analyzer)
    elif page == "bi":
        render_business_intelligence(analyzer)
    elif page == "export":
        render_export(analyzer)

    render_footer()
```

**Step 3: Update navigation test**

In `tests/test_streamlit_data_flow.py`, replace `test_segmented_navigation_labels_are_stable` (lines 104-118):

```python
def test_sidebar_navigation_labels_are_stable(self):
    from streamlit_app import NAV_OPTIONS
    self.assertEqual(
        list(NAV_OPTIONS.keys()),
        ["Dashboard", "Rankings", "Patent Explorer", "Score Analysis", "Business Intel", "Export"],
    )
    source = Path("streamlit_app.py").read_text(encoding="utf-8")
    self.assertIn("st.radio(", source)
```

**Step 4: Run tests**

```bash
cd "/Volumes/Elements/Manual Library/Patent Miner"
python -m pytest tests/test_streamlit_data_flow.py -v
```

Expected: All tests pass.

**Step 5: Commit**

```bash
git add streamlit_app.py tests/test_streamlit_data_flow.py
git commit -m "feat: replace flat tabs with sidebar radio navigation"
```

---

### Task 4: Overhaul Executive View charts

**Files:**
- Modify: `streamlit_app.py:938-981` (`render_executive_view`)

**Step 1: Replace domain distribution line chart with horizontal bar**

Replace the `px.line` chart (lines 958-968) with:

```python
fig = px.bar(
    domain_dist.sort_values("count", ascending=True),
    y="market_domain",
    x="count",
    orientation="h",
    title="Domain Distribution",
)
fig.update_traces(
    marker=dict(
        color=domain_dist.sort_values("count", ascending=True)["count"],
        colorscale=[[0, "#6366f1"], [0.5, "#22d3ee"], [1, "#10b981"]],
        line=dict(width=0),
        cornerradius=6,
    )
)
fig.update_layout(**PM_DARK_LAYOUT, height=max(300, len(domain_dist) * 40), showlegend=False)
fig.update_yaxes(title="")
fig.update_xaxes(title="Count")
```

**Step 2: Add a donut chart for assignee type distribution**

After the domain bar chart, within the `if show_advanced:` block, add an assignee type donut alongside the domain counts table:

```python
if show_advanced:
    col_table, col_donut = st.columns([1, 1])
    with col_table:
        st.subheader("Domain Counts")
        st.dataframe(
            pd.DataFrame([{"domain": d, "count": c} for d, c in stats["domains"].items()]),
            use_container_width=True,
            hide_index=True,
        )
    with col_donut:
        if stats["assignee_types"]:
            assignee_df = pd.DataFrame(
                [{"type": k, "count": v} for k, v in stats["assignee_types"].items()]
            )
            fig_donut = px.pie(
                assignee_df, names="type", values="count",
                title="Assignee Types", hole=0.5,
                color_discrete_sequence=PM_COLORS,
            )
            fig_donut.update_layout(**PM_DARK_LAYOUT, height=350, showlegend=True)
            st.plotly_chart(fig_donut, use_container_width=True)
```

**Step 3: Commit**

```bash
git add streamlit_app.py
git commit -m "feat: executive view — horizontal bar + donut charts"
```

---

### Task 5: Overhaul Patent Details score breakdown chart

**Files:**
- Modify: `streamlit_app.py:1126-1147` (score breakdown in `render_patent_details`)

**Step 1: Replace score breakdown line chart with radar chart**

Replace the `px.line` chart (lines 1126-1147) with a `go.Scatterpolar` radar:

```python
categories_radar = list(scores.keys())
values_radar = list(scores.values())

fig = go.Figure()
fig.add_trace(go.Scatterpolar(
    r=values_radar + [values_radar[0]],
    theta=categories_radar + [categories_radar[0]],
    fill="toself",
    fillcolor="rgba(99, 102, 241, 0.15)",
    line=dict(color="#6366f1", width=2),
    marker=dict(size=8, color="#6366f1"),
    name="Scores",
))
fig.update_layout(
    polar=dict(
        bgcolor="#12121a",
        radialaxis=dict(visible=True, range=[0, 10], gridcolor="#1e293b", tickfont=dict(color="#94a3b8")),
        angularaxis=dict(gridcolor="#1e293b", tickfont=dict(color="#e2e8f0", size=13)),
    ),
    paper_bgcolor="#12121a",
    font=dict(color="#e2e8f0"),
    showlegend=False,
    height=350,
    margin=dict(l=60, r=60, t=30, b=30),
)
st.plotly_chart(fig, use_container_width=True)
```

**Step 2: Commit**

```bash
git add streamlit_app.py
git commit -m "feat: patent details — radar chart for score breakdown"
```

---

### Task 6: Overhaul Score Explainability chart

**Files:**
- Modify: `streamlit_app.py:1260-1271` (`render_score_explainability`)

**Step 1: Replace comparison line chart with grouped bar chart**

Replace the `px.line` chart (lines 1260-1271) with:

```python
fig = px.bar(
    chart_df,
    x="Patent #",
    y="value",
    color="variable",
    barmode="group",
    title="Score Component Comparison (Top Candidates)",
    color_discrete_sequence=PM_COLORS[:3],
)
fig.update_traces(marker=dict(cornerradius=4, line=dict(width=0)))
fig.update_layout(**PM_DARK_LAYOUT, height=420, hovermode="x unified")
st.plotly_chart(fig, use_container_width=True)
```

**Step 2: Commit**

```bash
git add streamlit_app.py
git commit -m "feat: score explainability — grouped bar chart"
```

---

### Task 7: Overhaul BI Financial charts

**Files:**
- Modify: `streamlit_app.py:1456-1484` (NPV distribution + uncertainty band in BI Financial tab)

**Step 1: Replace NPV distribution line chart with area chart**

Replace the NPV distribution `px.line` (lines 1458-1470) with:

```python
npv_chart = px.area(
    npv_sorted,
    x="index",
    y="NPV_Base",
    title="Patent NPV Distribution",
)
npv_chart.update_traces(
    line=dict(color="#6366f1", width=2),
    fillcolor="rgba(99, 102, 241, 0.2)",
    fillgradient=dict(type="vertical", colorscale=[[0, "rgba(99,102,241,0.3)"], [1, "rgba(99,102,241,0.02)"]]),
)
npv_chart.update_xaxes(title="Patent Index (sorted by NPV)")
npv_chart.update_yaxes(title="NPV (Base Case)")
npv_chart.update_layout(**PM_DARK_LAYOUT, height=350, hovermode="x unified")
```

**Step 2: Replace NPV uncertainty band with `go.Scatter` fill-between**

Replace the uncertainty band `px.line` (lines 1477-1484) with:

```python
fig_band = go.Figure()
fig_band.add_trace(go.Scatter(
    x=uncertainty_df["index"], y=uncertainty_df["NPV_P90"],
    mode="lines", line=dict(width=0), showlegend=False, name="P90",
))
fig_band.add_trace(go.Scatter(
    x=uncertainty_df["index"], y=uncertainty_df["NPV_P10"],
    mode="lines", line=dict(width=0), fill="tonexty",
    fillcolor="rgba(99,102,241,0.15)", showlegend=False, name="P10",
))
fig_band.add_trace(go.Scatter(
    x=uncertainty_df["index"], y=uncertainty_df["NPV_Base"],
    mode="lines", line=dict(color="#22d3ee", width=2), name="Base NPV",
))
fig_band.update_layout(
    **PM_DARK_LAYOUT,
    title="Risk-Adjusted NPV Band (P10 / Base / P90)",
    height=320,
    hovermode="x unified",
)
st.plotly_chart(fig_band, use_container_width=True)
```

**Step 3: Commit**

```bash
git add streamlit_app.py
git commit -m "feat: BI financial — area chart + uncertainty band"
```

---

### Task 8: Overhaul BI Themes & Risk charts

**Files:**
- Modify: `streamlit_app.py:1515-1561` (Technology theme + manufacturing feasibility in BI Themes tab)

**Step 1: Replace technology theme line chart with treemap**

Replace the theme `px.line` (lines 1527-1537) with:

```python
fig_theme = px.treemap(
    theme_counts,
    path=["Technology_Theme"],
    values="count",
    title="Distribution by Technology Theme",
    color="count",
    color_continuous_scale=[[0, "#6366f1"], [0.5, "#22d3ee"], [1, "#10b981"]],
)
fig_theme.update_layout(
    paper_bgcolor="#12121a",
    font=dict(color="#e2e8f0"),
    height=400,
    coloraxis_showscale=False,
)
fig_theme.update_traces(
    textinfo="label+value",
    textfont=dict(size=14, color="#e2e8f0"),
    marker=dict(cornerradius=8),
)
st.plotly_chart(fig_theme, use_container_width=True)
```

**Step 2: Replace manufacturing feasibility line chart with horizontal bar**

Replace the feasibility `px.line` (lines 1549-1561) with:

```python
feas_sorted = rankings_df[["Patent_Number", "Manufacturing_Feasibility"]].dropna()
feas_sorted = feas_sorted.sort_values("Manufacturing_Feasibility", ascending=True).tail(20)
feasibility_chart = px.bar(
    feas_sorted,
    y="Patent_Number",
    x="Manufacturing_Feasibility",
    orientation="h",
    title="Manufacturing Feasibility (Top 20)",
)

def score_color(val):
    if val >= 7:
        return "#10b981"
    elif val >= 4:
        return "#f59e0b"
    return "#f43f5e"

feasibility_chart.update_traces(
    marker=dict(
        color=[score_color(v) for v in feas_sorted["Manufacturing_Feasibility"]],
        cornerradius=4,
        line=dict(width=0),
    )
)
feasibility_chart.update_layout(**PM_DARK_LAYOUT, height=max(300, len(feas_sorted) * 28), showlegend=False)
feasibility_chart.update_xaxes(title="Score (1-10)", range=[0, 10])
feasibility_chart.update_yaxes(title="")
st.plotly_chart(feasibility_chart, use_container_width=True)
```

**Step 3: Commit**

```bash
git add streamlit_app.py
git commit -m "feat: BI themes — treemap + score-colored horizontal bars"
```

---

### Task 9: Update banner and HTML cards for dark theme

**Files:**
- Modify: `streamlit_app.py:1895-1925` (`render_banner`)
- Modify: all `st.markdown(...unsafe_allow_html=True)` inline HTML throughout file

**Step 1: Update banner**

The banner gradient is fine (it's already a colored overlay), but update the box-shadow to match the dark theme glow:

```python
box-shadow: 0 8px 32px rgba(99, 102, 241, 0.4);
```

**Step 2: Update all inline HTML cards**

Search for all `style='background: white` or `style='background: #fff` occurrences in HTML strings and replace:
- `background: white` → `background: rgba(255,255,255,0.03)`
- `color: #1a1a1a` → `color: #e2e8f0`
- `color: #606060` → `color: #94a3b8`
- `color: #808080` → `color: #94a3b8`
- `border: 2px solid #e0e8f5` → `border: 1px solid rgba(99,102,241,0.15)`
- `background: #fff5e6` (warning cards) → `background: rgba(245,158,11,0.1)`
- `border: 2px solid #ff9500` → `border: 1px solid rgba(245,158,11,0.3)`

These occur in:
- `render_patent_details` (lines 1069-1078): patent header card
- `render_patent_details` (lines 1162-1174): AI summary card
- `render_patent_details` (lines 1184-1217): explanation cards
- `render_business_intelligence` (lines 1578-1582): red flag warning cards
- `render_business_intelligence` (lines 1618-1624): tier 1 patent cards
- `render_business_intelligence` (lines 1727-1738): BI detailed view header card
- `render_business_intelligence` (lines 1761-1773): BI AI summary card

**Step 3: Commit**

```bash
git add streamlit_app.py
git commit -m "style: update all inline HTML to dark theme colors"
```

---

### Task 10: Run full test suite and verify app launches

**Step 1: Run all tests**

```bash
cd "/Volumes/Elements/Manual Library/Patent Miner"
python -m pytest tests/ -v
```

Expected: All tests pass.

**Step 2: Launch app for visual verification**

```bash
cd "/Volumes/Elements/Manual Library/Patent Miner"
streamlit run streamlit_app.py --server.headless true
```

Verify: App starts without errors.

**Step 3: Final commit if any fixes needed**

```bash
git add streamlit_app.py
git commit -m "fix: resolve any test or startup issues from dark mode overhaul"
```

---

## Summary

| Task | What | Commit message |
|------|------|---------------|
| 1 | Imports + dark template constants | `refactor: add plotly dark template and sidebar nav constants` |
| 2 | Dark mode CSS rewrite | `style: rewrite CSS to enterprise dark mode theme` |
| 3 | Sidebar navigation + test update | `feat: replace flat tabs with sidebar radio navigation` |
| 4 | Executive View charts | `feat: executive view — horizontal bar + donut charts` |
| 5 | Patent Details radar chart | `feat: patent details — radar chart for score breakdown` |
| 6 | Score Explainability grouped bar | `feat: score explainability — grouped bar chart` |
| 7 | BI Financial area + band charts | `feat: BI financial — area chart + uncertainty band` |
| 8 | BI Themes treemap + bars | `feat: BI themes — treemap + score-colored horizontal bars` |
| 9 | Dark theme inline HTML | `style: update all inline HTML to dark theme colors` |
| 10 | Tests + verification | `fix: resolve any test or startup issues` |
