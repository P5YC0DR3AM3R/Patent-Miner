<<<<<<< HEAD
**Edit a file, create a new file, and clone from Bitbucket in under 2 minutes**

When you're done, you can delete the content in this README and update the file with details for others getting started with your repository.

*We recommend that you open this README in another tab as you perform the tasks below. You can [watch our video](https://youtu.be/0ocf7u76WSo) for a full demo of all the steps in this tutorial. Open the video in a new tab to avoid leaving Bitbucket.*

---

## Edit a file

You’ll start by editing this README file to learn how to edit a file in Bitbucket.

1. Click **Source** on the left side.
2. Click the README.md link from the list of files.
3. Click the **Edit** button.
4. Delete the following text: *Delete this line to make a change to the README from Bitbucket.*
5. After making your change, click **Commit** and then **Commit** again in the dialog. The commit page will open and you’ll see the change you just made.
6. Go back to the **Source** page.

---

## Create a file

Next, you’ll add a new file to this repository.

1. Click the **New file** button at the top of the **Source** page.
2. Give the file a filename of **contributors.txt**.
3. Enter your name in the empty file space.
4. Click **Commit** and then **Commit** again in the dialog.
5. Go back to the **Source** page.

Before you move on, go ahead and explore the repository. You've already seen the **Source** page, but check out the **Commits**, **Branches**, and **Settings** pages.

---

## Clone a repository

Use these steps to clone from SourceTree, our client for using the repository command-line free. Cloning allows you to work on your files locally. If you don't yet have SourceTree, [download and install first](https://www.sourcetreeapp.com/). If you prefer to clone from the command line, see [Clone a repository](https://confluence.atlassian.com/x/4whODQ).

1. You’ll see the clone button under the **Source** heading. Click that button.
2. Now click **Check out in SourceTree**. You may need to create a SourceTree account or log in.
3. When you see the **Clone New** dialog in SourceTree, update the destination path and name if you’d like to and then click **Clone**.
4. Open the directory you just created to see your repository’s files.

Now that you're more familiar with your Bitbucket repository, go ahead and add a new file locally. You can [push your change back to Bitbucket with SourceTree](https://confluence.atlassian.com/x/iqyBMg), or you can [add, commit,](https://confluence.atlassian.com/x/8QhODQ) and [push from the command line](https://confluence.atlassian.com/x/NQ0zDQ).
=======
# 🔬 Patent Miner - Enterprise Patent Discovery & Analytics System

A complete end-to-end system for discovering expired patents, analyzing opportunities, and generating actionable intelligence with an interactive Streamlit dashboard.

---

## 📋 Quick Start

### 1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

### 2. **Configure API Key**
```bash
# Edit .env file and add your PatentsView API key
PATENTSVIEW_API_KEY=your_api_key_here
```

Get a free API key at: https://www.patentsview.org/api/

### 3. **Run Patent Discovery**
Open `Patent_Miner.ipynb` and run the cells to discover patents.

### 4. **View Analytics Dashboard**
```bash
streamlit run streamlit_app.py
```

The dashboard will open at `http://localhost:8501`

---

## 🎯 What's Included

### Core Modules

| File | Purpose |
|------|---------|
| `patent_discovery.py` | API client & patent discovery logic |
| `patent_miner_config.py` | Configuration & defaults |
| `streamlit_app.py` | Interactive analytics dashboard |
| `display_results.py` | CLI results viewer |
| `brand_intelligence.py` | GTM strategy generator |
| `Patent_Miner.ipynb` | Lean runner notebook |

### Data Structure

```
patent_intelligence_vault/
├── patent_discoveries_<timestamp>.json    # Raw API results
├── discovery_diagnostics_<timestamp>.json # Query logs & errors
├── checkpoint_analysis_*.json             # Historical snapshots
├── brand_intelligence_*.json              # GTM strategies
└── action_plan_*.json                     # Strategic plans
```

---

## 🔍 Discovery Pipeline

### Configuration

Edit `patent_miner_config.py` to customize searches:

```python
DEFAULT_CONFIG = {
    "patent_search": {
        "keywords": ["portable", "sensor"],          # Search terms
        "filing_date_start": "1975-01-01",           # Expand to 1975
        "filing_date_end": "2005-12-31",             # Up to 2005
        "assignee_type": "individual",               # Individual inventors
        "num_results": 500,                          # Max results
        "require_likely_expired": True,              # Expired patents only
    },
    "output_dir": "./patent_intelligence_vault/",
}
```

### Run Discovery

**Option A: Lean Runner (Notebook)**
```
Open Patent_Miner.ipynb → Run all cells
```

**Option B: Direct Script**
```bash
python temp_patent_miner.py
```

### Output Files

- **`patent_discoveries_*.json`** - Patent metadata & details
- **`discovery_diagnostics_*.json`** - API logs, errors, performance metrics

---

## 📊 Streamlit Analytics Dashboard

### Features

**Overview Tab**
- Patent count & filing date range
- Assignee type distribution
- Patent type breakdown
- Filing timeline chart
- Assignee distribution pie chart

**Opportunities Tab**
- Patents ranked by opportunity score
- Adjustable display count (top N)
- Quick-view summaries

**Details Tab**
- Deep-dive into individual patents
- Full title, abstract, filing dates
- Link to USPTO patent page
- Opportunity score calculation

**Data Export Tab**
- Download as CSV or JSON
- Full patent dataset with all fields
- Timestamped exports

### Launch Dashboard

```bash
streamlit run streamlit_app.py
```

Navigate to `http://localhost:8501` in your browser.

---

## 🔐 Security & Environment Setup

### .env File (Local Only)

```
PATENTSVIEW_API_KEY=your_api_key_here
```

**Never commit .env to version control!** It's in `.gitignore`.

### Team Sharing

1. Copy `.env.example` to `.env`
2. Share `.env.example` with team (no secrets)
3. Each team member adds their own API key

---

## 📈 Data Analysis Workflow

### Step 1: Discover Patents
Run discovery to fetch patents from PatentsView API.

### Step 2: View Analytics
Launch Streamlit dashboard to analyze results.

### Step 3: Export Data
Download patent data as CSV or JSON for further analysis.

### Step 4: Generate Intelligence
Use `brand_intelligence.py` or `display_results.py` for additional insights.

---

## 🛠️ Advanced Usage

### Custom Search Queries

Modify search keywords in `patent_miner_config.py`:

```python
"keywords": ["wearable", "IoT", "sensor", "wireless"],
```

### Filter by Date Range

```python
"filing_date_start": "1975-01-01",
"filing_date_end": "2000-12-31",
```

### Change Assignee Type

```python
"assignee_type": "organization",  # Instead of "individual"
```

### Increase Results

```python
"num_results": 1000,  # Get more results (max ~10,000 practical limit)
```

---

## 🐛 Troubleshooting

### "No API key found"
- Check `.env` file exists in project root
- Verify `PATENTSVIEW_API_KEY=value` is set
- Run `python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('PATENTSVIEW_API_KEY'))"`

### "No patent discoveries found"
- Run the discovery pipeline first
- Check `patent_intelligence_vault/` directory was created
- Review `discovery_diagnostics_*.json` for errors

### "Streamlit app won't start"
- Install streamlit: `pip install streamlit`
- Verify requirements: `pip install -r requirements.txt`
- Check Python version (3.8+)

### API Rate Limiting
- PatentsView API has rate limits
- Increase `retry_backoff_seconds` in config if needed
- Reduce `num_results` or split searches

---

## 📚 File Reference

### Patent Data Schema

```json
{
  "patent_number": "5865762",
  "title": "Module for recording the instantaneous heart rate...",
  "abstract": "The invention relates to a portable module...",
  "filing_date": "1997-07-17",
  "patent_date": "1999-02-02",
  "assignee_type": "5",
  "patent_type": "utility",
  "source_provider": "patentsview_patentsearch",
  "link": "https://patents.google.com/patent/5865762"
}
```

### Opportunity Score Calculation

Patents are scored 1-10 based on:
- **Patent age** (older = more likely expired) - 30%
- **Title complexity** - 20%
- **Abstract detail level** - 30%
- **Patent type** (utility patents scored higher) - 10%
- **Baseline score** - 10%

---

## 🚀 Deployment

### Local Development
```bash
streamlit run streamlit_app.py
```

### Cloud Deployment (Streamlit Cloud)
1. Push code to GitHub
2. Go to https://streamlit.io/cloud
3. Connect GitHub repository
4. Set `.env` variables in Streamlit Cloud settings
5. Deploy

### Docker Deployment
Create `Dockerfile`:
```dockerfile
FROM python:3.10
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["streamlit", "run", "streamlit_app.py"]
```

---

## 📝 License & Attribution

- **Patent Data:** PatentsView (USPTO)
- **API:** https://www.patentsview.org/api/
- **Framework:** Streamlit, Plotly, Pandas

---

## 🤝 Contributing

To add features:
1. Create a feature branch
2. Update relevant modules
3. Test with sample data
4. Submit pull request

---

## 📞 Support

For issues:
1. Check `.gitignore` includes `.env`
2. Review `discovery_diagnostics_*.json` for API errors
3. Verify PatentsView API key is valid
4. Check `requirements.txt` all packages installed

---

**Last Updated:** February 2026  
**Version:** 2.0 - Complete Analytics Edition
>>>>>>> 47b84b3 (Initial commit: Patent Miner complete analytics system)
