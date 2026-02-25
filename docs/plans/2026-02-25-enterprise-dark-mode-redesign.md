# Patent Miner V3 — Enterprise Dark Mode Redesign

**Date:** 2026-02-25
**Status:** Approved
**File modified:** `streamlit_app.py` (single file)

## Context

Patent Miner is a Streamlit dashboard for patent discovery and business intelligence. The current UI suffers from poor readability (gray text on light backgrounds), monotonous charts (every chart is `px.line`), flat tab navigation (11 targets), and inconsistent button styling. The goal is an enterprise-grade dark mode overhaul with progressive disclosure for both executive and analyst audiences.

## Design Decisions

### 1. Color System

| Token | Value | Purpose |
|-------|-------|---------|
| `--bg-deep` | `#0a0a0f` | Page background |
| `--bg-surface` | `#12121a` | Cards, panels |
| `--bg-elevated` | `#1a1a2e` | Hover states, modals |
| `--accent` | `#6366f1` | Primary actions (indigo) |
| `--cyan` | `#22d3ee` | Data highlights, links |
| `--emerald` | `#10b981` | Positive values, downloads |
| `--amber` | `#f59e0b` | Warnings, mid-range |
| `--rose` | `#f43f5e` | Red flags, low scores |
| `--text` | `#e2e8f0` | Primary text (~15:1 contrast) |
| `--text-muted` | `#94a3b8` | Secondary labels |
| `--glow-accent` | `0 0 20px rgba(99,102,241,0.25)` | Card/button glow |
| `--glass` | `rgba(255,255,255,0.03)` + `backdrop-filter: blur(12px)` | Glassmorphism |

### 2. Navigation

Replace 6 flat top tabs with sidebar radio navigation using icons. BI sub-tabs remain as tabs (appropriate for drill-down level). Re-enable sidebar settings (text size, density).

Sidebar structure:
- Dashboard (was Executive View)
- Rankings (was Opportunity Ranking)
- Patent Explorer (was Patent Details)
- Score Analysis (was Score Explainability)
- Business Intel (was Business Intelligence)
- Export

### 3. Uniform Button System

| Role | Gradient | Glow Color | Use |
|------|----------|------------|-----|
| Primary | `#6366f1 → #4f46e5` | Indigo | Main actions |
| Download | `#10b981 → #059669` | Emerald | CSV/JSON export |
| Generate | `#22d3ee → #0891b2` | Cyan | AI summary |
| Ghost | Transparent + border | Subtle indigo | Secondary |

Shared: `border-radius: 12px`, `transition: 0.25s cubic-bezier(0.34,1.56,0.64,1)`, hover lift + glow, active snap-back.

### 4. Chart Replacements

| Location | Current | New | Rationale |
|----------|---------|-----|-----------|
| Executive: Domain Distribution | `px.line` | Horizontal bar with gradient | Correct for category comparison |
| Patent Details: Score Breakdown | `px.line` | Radar/spider chart | Shows multi-dimensional profile |
| BI Financial: NPV Distribution | `px.line` | Area chart with gradient fill | Shows distribution shape |
| Score Explainability: Comparison | `px.line` | Grouped bar chart | Clear side-by-side |
| BI Themes: Technology Distribution | `px.line` | Treemap | Shows hierarchy + proportion |
| BI Themes: Manufacturing Feasibility | `px.line` | Horizontal bar, score-colored | Intuitive reading |
| BI Financial: NPV Uncertainty | multi-line | Area band (fill between) | Visual uncertainty range |

All charts share a Plotly dark template: `paper_bgcolor=#12121a`, `plot_bgcolor=#12121a`, `font.color=#e2e8f0`, `colorway=[#6366f1, #22d3ee, #10b981, #f59e0b, #f43f5e]`.

### 5. Card & Metric Components

Glassmorphism cards with score-colored left borders:
- Score >= 7: emerald border + green glow
- Score 4-7: amber border
- Score < 4: rose border

### 6. Animation System

| Element | Trigger | Effect |
|---------|---------|--------|
| Cards | Hover | `translateY(-4px)` + glow intensify |
| Buttons | Hover | `translateY(-2px)` + shadow expand |
| Buttons | Click | `scale(0.98)` snap-back |
| Sidebar items | Hover | Left border slide-in |
| Tab content | Mount | `fadeIn 0.3s ease` |
| Charts | Load | `fadeInUp 0.4s ease` |

### 7. Unchanged

- All Python business logic (scoring, data loading, enrichment)
- Streamlit framework
- Plotly charting library
- Data structures and patent analysis pipeline
- Banner content
- BI sub-tab structure
