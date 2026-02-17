# Patent Miner V3 🚀

**An end-to-end AI-powered patent discovery and business intelligence platform** that transforms expired patents into actionable commercialization opportunities.

> **Live Demo:** [Deployed on Render](https://patent-miner.onrender.com) | **GitHub:** [Repository](https://github.com/micahread/patent-miner)

---

## 🎯 What This Project Demonstrates

This is a **production-grade, full-stack AI application** showcasing expertise across the entire modern development lifecycle—from data engineering and machine learning to enterprise UI/UX and cloud deployment.

### **Core Skills & Technologies Showcased**

#### **1. Advanced AI/ML Engineering**
- **Multi-Pass Hybrid Retrieval Pipeline:** Custom-built semantic search combining TF-IDF, keyword expansion, and title prioritization
- **Deterministic Scoring Framework:** 9-dimension viability model (market demand, build feasibility, marketability, viral potential, ease of use, real-world impact, etc.)
- **Multi-Agent AI System:** Crew.AI integration with 4 specialized agent personas for qualitative patent analysis
- **Financial Modeling:** DCF-based NPV calculations with scenario planning (optimistic/base/pessimistic)

#### **2. Enterprise Software Architecture**
- **Modular Design:** Clean separation of concerns (discovery, scoring, analysis, presentation)
- **Backward Compatibility:** Additive schema design preserving legacy workflows
- **Comprehensive Testing:** Unit tests for retrieval, scoring, schema validation, and data flow
- **Version Control:** Git-based workflow with branch management and deployment automation

#### **3. Data Engineering & Pipeline Design**
- **API Integration:** PatentsView RESTful API with rate limiting, error handling, and fallback logic
- **Data Transformation:** JSON/CSV export pipelines with configurable filtering and aggregation
- **Caching Strategy:** Smart invalidation logic to balance performance and freshness
- **Schema Evolution:** Versioned scoring models with auto-migration for legacy data

#### **4. Full-Stack Web Development**
- **Frontend:** Streamlit dashboard with enterprise-grade CSS (gradients, shadows, responsive design)
- **Interactive Visualizations:** Plotly line charts, KPI cards, multi-tab navigation
- **UX Design:** Kid-friendly enterprise aesthetic with accessibility-first design
- **State Management:** Efficient caching and session handling for 186+ patent datasets

#### **5. Business Intelligence & Analytics**
- **7-Dimension Deterministic Framework:** Scientific robustness, manufacturing feasibility, modernization potential, strategic fit, financial attractiveness, legal risk, ESG impact
- **Portfolio Analysis:** Aggregated NPV, tier-based recommendations, risk/reward matrices
- **Executive Reporting:** Auto-generated markdown reports with actionable next steps
- **Data Storytelling:** Concise summaries translating technical metrics into business value

#### **6. Cloud & DevOps**
- **Containerization:** Docker-based deployment with multi-stage builds
- **Platform-as-a-Service:** Render deployment with auto-scaling and environment management
- **CI/CD:** Git-triggered deployments from GitHub with zero-downtime updates
- **Environment Configuration:** .env-based secrets management and multi-environment support

#### **7. Product Thinking & Domain Expertise**
- **Problem Discovery:** Identified gap in expired patent commercialization (untapped $19.4M portfolio NPV)
- **User-Centered Design:** Simplified complex data into "Marketability Snapshot" cards with plain-language captions
- **Iterative Development:** Evolved from 19-patent proof-of-concept to 186-patent production system
- **Stakeholder Communication:** Translated technical capabilities into executive-ready business intelligence

---

## 💼 Why This Matters to Employers/Partners

### **Proven Ability to Ship Production AI**
- **From idea to deployment in weeks:** This isn't a tutorial project—it's a live, functional SaaS-style application handling real patent data
- **Handles ambiguity:** Built custom retrieval/scoring logic when off-the-shelf solutions didn't exist
- **Delivers business value:** Generated $19.4M portfolio valuation from 186 expired patents with tier-based recommendations

### **Full-Stack Versatility**
- **Backend:** Python data pipelines, API integrations, financial modeling
- **Frontend:** Modern web UI with enterprise styling and interactive analytics
- **Infrastructure:** Docker, cloud deployment, version control, automated testing

### **Rapid Learning & Adaptation**
- **Integrated 5+ technologies:** PatentsView API, Crew.AI, Streamlit, Plotly, Docker, Render
- **Overcame real blockers:** Fixed deployment issues, resolved dataset mismatches, improved scoring accuracy
- **Iterated based on feedback:** Added marketability metrics, simplified language, enhanced navigation

### **Attention to Detail**
- **User experience:** Removed cluttered UI elements, added color-coded badges, improved chart readability
- **Code quality:** Modular functions, type hints, comprehensive docstrings, DRY principles
- **Documentation:** Clear README, deployment guides, analysis methodology explanations

---

## 🏆 Key Achievements

| Metric | Result |
|--------|--------|
| **Patents Analyzed** | 186 expired patents (1970-2012 filing range) |
| **Portfolio NPV** | $19.4M base case, $27.8M optimistic |
| **Tier 1 Recommendations** | 4 patents ready for immediate implementation |
| **Discovery Accuracy** | 9x dataset expansion (19→186 patents) via keyword optimization |
| **UI Modernization** | Enterprise-grade redesign with gradient backgrounds, rounded corners, accessibility focus |
| **Deployment Uptime** | Live production app on Render with auto-scaling |

---

## 🚀 Quick Start

1. Install dependencies.
```bash
pip install -r requirements.txt
```

2. Set your PatentsView API key.
```bash
cp .env.example .env
# edit .env
PATENTSVIEW_API_KEY=your_api_key_here
```

3. Run discovery.
```bash
python temp_patent_miner.py
```

4. Launch dashboard.
```bash
streamlit run streamlit_app.py
```

5. (Optional) Run Business Intelligence analysis.
```bash
python run_expired_patent_analysis.py
```

---

## 📊 What Sets This Apart from Tutorial Projects

### **Real-World Complexity**
- **No toy datasets:** Integrated live PatentsView API with 186 real expired patents
- **Production deployment:** Not localhost—live on Render with public URL
- **Edge case handling:** Backward compatibility for legacy data, auto-migration for new metrics

### **Business-Driven Development**
- **Started with a problem:** "How do I find commercializable expired patents?"
- **Delivered measurable value:** $19.4M portfolio NPV with actionable tier-based recommendations
- **Iterated with user feedback:** Simplified UI, added marketability metrics, improved navigation

### **Technical Sophistication**
- **Custom algorithms:** Built retrieval pipeline from scratch (not just API wrappers)
- **Multi-agent AI:** Integrated Crew.AI for qualitative analysis (4 specialized personas)
- **Financial modeling:** DCF calculations with scenario planning—not just simple averages

---

## 🛠️ Technical Deep Dive

### **Architecture Overview**
```
┌─────────────────────────────────────────────────────────────────┐
│                     Patent Miner V3 Pipeline                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Discovery Layer (patent_discovery.py)                       │
│     ├─ Multi-pass retrieval (strict → expanded → fallback)      │
│     ├─ Deduplication & candidate pooling                        │
│     └─ API integration (PatentsView)                            │
│                                                                  │
│  2. Scoring Layer (viability_scoring.py)                        │
│     ├─ 9-dimension viability scorecard                          │
│     ├─ Marketability, viral potential, ease of use              │
│     └─ Deterministic term-matching (explainable)                │
│                                                                  │
│  3. Analysis Layer (patent_analysis_framework.py)               │
│     ├─ 7-dimension BI framework                                 │
│     ├─ DCF financial modeling (NPV, IRR, payback)               │
│     └─ Crew.AI multi-agent qualitative analysis                 │
│                                                                  │
│  4. Presentation Layer (streamlit_app.py)                       │
│     ├─ Executive KPI dashboard                                  │
│     ├─ Interactive filtering & drill-downs                      │
│     ├─ Marketability snapshot cards                             │
│     └─ Export (CSV/JSON/Markdown)                               │
│                                                                  │
│  5. Deployment Layer (Docker + Render)                          │
│     ├─ Containerized app                                        │
│     ├─ Auto-deploy from GitHub                                  │
│     └─ Environment-based configuration                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### **Scoring Methodology (v2.1.0)**

#### **Viability Components (Weighted Blend)**
| Component | Weight | Description |
|-----------|--------|-------------|
| Market Demand | 20% | Evidence of automation, real-time, safety, efficiency needs |
| Build Feasibility | 18% | Inverse of complexity (low penalty for standard equipment) |
| Competition Headroom | 12% | Lower for crowded "system/platform" terms; bonus for individual inventors |
| Differentiation Potential | 12% | Portable, wireless, adaptive, predictive capabilities |
| Commercial Readiness | 10% | Prototype/production keywords + expiration confidence |
| **Marketability** | 10% | Consumer-facing, portable, smart device indicators |
| **Viral Potential** | 8% | Network effects, community, sharing mechanisms |
| **Ease of Use** | 5% | Simple, automatic, compact, hands-free design |
| **Real-World Impact** | 5% | Solves safety, health, environmental, efficiency problems |

**Total Viability Score = Σ(component × weight)** → 0-10 scale

#### **Opportunity Score (Final Ranking)**
```
Opportunity = (Retrieval × 0.35) + (Viability × 0.45) + (Expiration × 0.20)
```

---

## 📁 Core Files & Responsibilities

1. Hybrid retrieval pipeline (multi-pass):
- `strict_intent`
- `expanded_synonyms`
- `title_priority`
- `broad_fallback`

2. Deterministic viability scorecard:
- `market_demand`
- `build_feasibility`
- `competition_headroom`
- `differentiation_potential`
- `commercial_readiness`

3. Explainable ranking output:
- `retrieval_scorecard`
- `viability_scorecard`
- `opportunity_score_v2`
- `market_domain`
- `explanations`

4. Legibility-first UI with segmented in-body tabs:
- `Executive View`
- `Opportunity Ranking`
- `Patent Details`
- `Score Explainability`
- `Export`

## Core Files


| File | Purpose | Key Capabilities |
|------|---------|------------------|
| `patent_discovery.py` | Discovery orchestration | Multi-pass retrieval, deduplication, API integration, reranking |
| `viability_scoring.py` | Scoring engine | 9-dimension viability model, marketability metrics, explainable logic |
| `patent_analysis_framework.py` | Business intelligence | 7-dimension BI framework, DCF modeling, tier recommendations |
| `streamlit_app.py` | User interface | Interactive dashboard, visualizations, marketability snapshots |
| `run_expired_patent_analysis.py` | Analysis pipeline | Orchestrates BI framework + Crew.AI, generates reports |
| `patent_miner_config.py` | Configuration | Search parameters, weights, API settings |
| `scoring_utils.py` | Utility functions | Tokenization, TF-IDF, cosine similarity |

---

## 🧪 Testing & Quality Assurance

```bash
python -m unittest discover -s tests -p 'test_*.py'
```

**Test Coverage:**
- ✅ `test_retrieval_v2.py` – Multi-pass retrieval logic
- ✅ `test_viability_scoring.py` – Scoring calculations and edge cases
- ✅ `test_schema_compat.py` – Backward compatibility validation
- ✅ `test_streamlit_data_flow.py` – UI data loading and caching

---

## 📈 Evolution & Iteration History

### **V1.0** (Proof of Concept)
- Basic PatentsView API integration
- Simple keyword search
- 19 patents discovered
- CSV export only

### **V2.0** (Hybrid Retrieval)
- Multi-pass retrieval pipeline
- TF-IDF semantic similarity
- 167 patents discovered (9x improvement)
- Streamlit dashboard with charts

### **V3.0** (Enterprise BI) ← **Current**
- 9-dimension viability scoring
- Crew.AI multi-agent analysis
- 186 patents with 1970-2012 filing range
- Marketability metrics (viral potential, ease of use, real-world impact)
- $19.4M portfolio NPV analysis
- Production deployment on Render

---

## 🌟 Sample Outputs

### **Marketability Snapshot (Patent Details View)**
```
┌─────────────────────────────────────────────────────────────┐
│  🚀 Marketability Snapshot                                  │
├─────────────────────────────────────────────────────────────┤
│  Marketability: 7.2/10     Viral Impact: 6.8/10             │
│  How easy to sell          Built-in sharing/network effects │
│                                                              │
│  Ease of Use: 7.5/10       Real-World Need: 8.1/10          │
│  Simple for everyday users Solves a meaningful problem      │
└─────────────────────────────────────────────────────────────┘
```

### **Executive Summary (BI Report)**
```
Total Patents Analyzed: 186
High-Potential Candidates (Tier 1): 4 patents
Further Investigation (Tier 2): 182 patents
Average Integrated Score: 6.85/10

Portfolio NPV (Base): $19,400,000
Portfolio NPV (Optimistic): $27,800,000
Top Patent: US3930752 (Score: 6.97/10)
```

---


`patent_miner_config.py` - Customize search parameters:

```python
"keywords": ["portable", "sensor", "wireless", "IoT", "smart", "connected"],
"filing_date_start": "1970-01-01",
"filing_date_end": "2012-12-31",
"num_results": 500,

"retrieval_v2": {
  "enabled": True,
  "max_expanded_keywords": 24,
  "fallback_relax_assignee": True,
},

"scoring_weights": {
  "retrieval": 0.35,
  "viability": 0.45,
  "expiration": 0.20,
}
```

**Tunable Viability Weights:** Adjust in `viability_scoring.py`:
```python
DEFAULT_VIABILITY_COMPONENT_WEIGHTS = {
    "market_demand": 0.20,
    "marketability": 0.10,
    "viral_potential": 0.08,
    "ease_of_use": 0.05,
    "real_world_impact": 0.05,
    # ... 9 total dimensions
}
```

---

## 📦 Output Schema (Backward-Compatible)

Each discovered patent includes legacy fields **plus** V3 enhancements:

```json
{
  "patent_number": "US3930752",
  "title": "Portable environmental sensor system",
  "abstract": "A wireless sensor for monitoring air quality...",
  "filing_date": "1974-01-15",
  "patent_date": "1976-01-06",
  "assignee_type": "4",
  "patent_type": "utility",
  "link": "https://patents.google.com/patent/US3930752",
  
  "retrieval_scorecard": {
    "title_exact_match": 8.5,
    "query_coverage": 7.8,
    "semantic_similarity": 7.2,
    "expiration_confidence": 9.1,
    "pass_diversity": 7.5,
    "total": 7.9
  },
  
  "viability_scorecard": {
    "market_demand": 7.4,
    "build_feasibility": 6.9,
    "competition_headroom": 6.7,
    "differentiation_potential": 7.2,
    "commercial_readiness": 7.8,
    "marketability": 7.1,
    "viral_potential": 6.8,
    "ease_of_use": 7.5,
    "real_world_impact": 8.1,
    "total": 7.2
  },
  
  "opportunity_score_v2": 7.4,
  "market_domain": "environmental_monitoring",
  "scoring_version": "v2.1.0",
  
  "explanations": {
    "retrieval": "Retrieval based on title match, keyword coverage...",
    "viability": "Market demand 7.4/10, easy to build 6.9/10...",
    "opportunity": "Blended score from retrieval=7.9, viability=7.2..."
  }
}
```

---

## 🚢 Deployment

### **Docker Build**
```bash
docker build -t patent-miner .
docker run -p 8501:8501 patent-miner
```

### **Render Deployment** (Current Production)
1. Connected to GitHub repository
2. Auto-deploys on commits to `main` branch
3. Environment variables managed via Render dashboard
4. Live URL: `https://patent-miner.onrender.com`

---

## 🤝 Skills Translation for Employers/Partners

### **If You Need Someone Who Can...**

✅ **Build production AI/ML pipelines**
→ *I built a custom hybrid retrieval system from scratch and deployed it to production*

✅ **Turn messy data into business insights**
→ *I transformed raw patent metadata into a $19.4M portfolio valuation with actionable recommendations*

✅ **Ship full-stack applications**
→ *I designed the backend API integration, scoring algorithms, and frontend dashboard—then deployed it to the cloud*

✅ **Communicate technical concepts to non-technical stakeholders**
→ *I distilled complex scoring dimensions into simple "Marketability Snapshot" cards with plain-language captions*

✅ **Work independently and iterate quickly**
→ *I went from initial concept to production deployment, solving blockers like API limitations, UI redesigns, and deployment issues along the way*

✅ **Write clean, maintainable code**
→ *Modular architecture, comprehensive tests, type hints, version control, and detailed documentation*

---

## 📚 Learn More

- **Full Analysis Guide:** [EXPIRED_PATENT_ANALYSIS_GUIDE.md](EXPIRED_PATENT_ANALYSIS_GUIDE.md)
- **Business Intelligence Implementation:** [EXPIRED_PATENT_BI_IMPLEMENTATION.md](EXPIRED_PATENT_BI_IMPLEMENTATION.md)
- **Deployment Guide:** [DEPLOY.md](DEPLOY.md)
- **Discovery Setup:** [DISCOVERY_SETUP.md](DISCOVERY_SETUP.md)

---

## 📞 Contact

**Developer:** Micah Read   
**LinkedIn:** https://www.linkedin.com/in/micahread/  
**GitHub:** https://github.com/p5yc0dr3am3r/  
**Email:** micahreadmgmt@gmail.com

*This project represents the first fully deployed AI application in my portfolio, demonstrating end-to-end capability from problem discovery to production deployment.*

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🙏 Acknowledgments

- **PatentsView API:** Public patent data source
- **Streamlit:** Rapid UI prototyping framework
- **Crew.AI:** Multi-agent orchestration (optional enhancement)
- **Plotly:** Interactive visualizations
- **Render:** Cloud deployment platform

---

**Built with ❤️ by Micah Read** | *Transforming AI concepts into production reality*

---

**Built with ❤️ by Micah Read** | *Transforming AI concepts into production reality*