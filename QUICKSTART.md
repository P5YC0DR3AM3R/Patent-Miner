# Patent Miner - Quick Start Guide

## ⚡ 5-Minute Setup

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Set API Key
Create `.env` file:
```
PATENTSVIEW_API_KEY=your_api_key_here
```

Get free API key: https://www.patentsview.org/api/

### Step 3: Run Patent Discovery
Open `Patent_Miner.ipynb` and run all cells.
This discovers patents from 1975-2005.

### Step 4: Launch Analytics Dashboard
```bash
streamlit run streamlit_app.py
```

Dashboard opens at: http://localhost:8501/

---

## 📊 Dashboard Features

### Overview Tab
- Total patents discovered
- Filing date range
- Distribution charts

### Opportunities Tab
- Patents ranked by opportunity score
- Adjustable top N display
- Quick-view summaries

### Details Tab
- Deep-dive patent information
- Full abstract & metadata
- Link to USPTO

### Data Export Tab
- Download as CSV
- Download as JSON
- Full dataset preview

---

## 🔍 What Gets Discovered?

**Search Criteria:**
- Keywords: "portable", "sensor"
- Filing dates: 1975 to 2005
- Assignees: Individuals only
- Status: Expired patents only
- Max results: 500

**Output:**
- `patent_discoveries_<timestamp>.json` - Raw patent data
- `discovery_diagnostics_<timestamp>.json` - Query logs

---

## 💡 Next Steps

1. **Analyze Results**
   - Use Streamlit dashboard to explore
   - Export data for further analysis

2. **Generate Intelligence**
   - Run `python brand_intelligence.py` for GTM strategies
   - Run `python display_results.py` for CLI view

3. **Customize Search**
   - Edit `patent_miner_config.py` to change keywords/dates
   - Re-run discovery to get new results

---

## 🐛 Troubleshooting

**"No patents found"**
- Check API key in `.env`
- Verify internet connection
- Check `discovery_diagnostics_*.json` for errors

**"Streamlit won't start"**
```bash
pip install --upgrade streamlit
streamlit run streamlit_app.py
```

**"Module not found"**
```bash
pip install -r requirements.txt --force-reinstall
```

---

## 📚 File Structure

```
Patent Miner/
├── Patent_Miner.ipynb              # Lean runner notebook
├── streamlit_app.py                # Analytics dashboard
├── patent_discovery.py             # API client
├── patent_miner_config.py          # Configuration
├── brand_intelligence.py           # GTM generator
├── display_results.py              # CLI viewer
├── requirements.txt                # Dependencies
├── .env                            # API key (local only)
├── .env.example                    # Template for team
├── .gitignore                      # Excludes .env
├── README.md                       # Full documentation
├── QUICKSTART.md                   # This file
└── patent_intelligence_vault/      # Output folder
    ├── patent_discoveries_*.json
    └── discovery_diagnostics_*.json
```

---

## 🎯 Common Tasks

### Run Discovery Only (No UI)
```bash
python temp_patent_miner.py
```

### View Results in Terminal
```bash
python display_results.py
```

### Generate Brand Strategy
```bash
python brand_intelligence.py
```

### Launch Streamlit Dashboard
```bash
streamlit run streamlit_app.py
# OR
bash run_dashboard.sh
```

---

## 📖 For More Details

See `README.md` for comprehensive documentation.

---

**Ready to discover patents? Run these 3 commands:**

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
# Then open Patent_Miner.ipynb in a notebook editor
```

Enjoy! 🚀
