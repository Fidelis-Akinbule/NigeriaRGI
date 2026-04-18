# NigeriaRGI — Regional Growth Intelligence Platform

**A full end-to-end BI & predictive analytics platform simulating telecom operations across 12 Nigerian states.**

Built by **Fidelis Akinbule** (Lagos, Nigeria) to demonstrate every requirement of a Regional BI & Analytics leadership role at a Nigerian telecom operator.

---

## 🔴 Live Demo

**[→ Open the Live Dashboard](https://nigeriargi-hv7avwbkxycrxkzvc4irsm.streamlit.app/)**

No login required. Explore all 5 pages. Data covers 41 LGAs across 12 states over 90 days.

---

## What This Project Demonstrates

Every module maps directly to a specific job description requirement. Nothing is built for its own sake.

| JD Requirement | Module | Deliverable |
|---|---|---|
| Automated data pipelines | Module 1 | SQLite DB generated from Python — 3,690 rows × 42 columns |
| Single version of truth | Module 1 | Flat `master_table` — all modules read from one source |
| State/LGA/cluster/site analytics | Module 2 | 12 SQL queries across revenue, subscribers, QoE, site economics |
| Power BI dashboards | Module 3 | 5-page Streamlit + Plotly dashboard (live URL above) |
| Replace static reporting with predictive insights | Module 4 | Churn risk model (AUC 0.989) + site profitability forecast (R² 0.83) |
| GTM strategies + GC opportunity mapping | Module 5 | Composite GTM score across 41 LGAs, top 10 priority targets |
| External data integration | All modules | NBS population, income index, POI counts, road density |
| Power BI competency | Power BI | State-level summary CSV + DAX measures |

---

## Repository Structure

```
NigeriaRGI/
├── module1_pipeline/
│   └── generate_data.py          # Automated data pipeline → nigeria_rgi.db
│
├── module2_analytics/
│   ├── queries.sql               # 12 named SQL queries across 6 analytical sections
│   ├── analytics.py              # Executes queries, produces charts + business narrative
│   └── charts/                   # 9 output charts (gitignored output folder)
│
├── module3_dashboard/
│   ├── app.py                    # Streamlit entry point — sidebar, filters, routing
│   ├── utils/
│   │   ├── data_loader.py        # Environment-aware loader (local DB / cloud CSV)
│   │   └── metrics.py            # All computed measures — DAX equivalent
│   └── pages/
│       ├── page1_command_centre.py   # Regional health snapshot
│       ├── page2_revenue.py          # Revenue & ARPU deep dive
│       ├── page3_subscribers.py      # Subscriber health & churn risk
│       ├── page4_qoe.py              # Network quality & QoE
│       └── page5_gtm.py              # Growth opportunity & GTM
│
├── module4_models/
│   ├── churn_model.py            # Logistic regression — AUC 0.989
│   ├── site_profitability.py     # Gradient boosting — R² 0.83
│   └── outputs/                  # 8 model evaluation charts
│
├── module5_gtm/
│   ├── gtm_scoring.py            # Composite GTM scoring — 41 LGAs ranked
│   └── outputs/                  # Ranking table CSV + 4 charts
│
├── powerbi/
│   └── nigeria_rgi_summary.csv   # State-level aggregation for Power BI Service
│
├── data/
│   └── processed/
│       └── master_table.csv      # Master table for Streamlit Cloud
│
├── requirements.txt
├── runtime.txt
└── .vscode/settings.json
```

---

## Dashboard Pages

| Page | What It Shows | Why It Matters to a Hiring Manager |
|---|---|---|
| 🏠 Regional Command Centre | KPI cards, revenue by state, QoE compliance, early warning panel | Leadership sees region health in 30 seconds |
| 💰 Revenue & ARPU Deep Dive | Stacked revenue by state, ARPU benchmarks, VAS share, top 10 LGAs | Replaces five Excel files in five inboxes |
| 👥 Subscriber Health & Churn Risk | Active subs, penetration gaps, churn risk flag table, scatter | Proactive retention — before it becomes the CFO's problem |
| 📶 Network Quality & QoE | NCC compliance, MOS scores, drop call rates, MOS→ARPU link | Connects network root causes to commercial outcomes |
| 🚀 Growth Opportunity & GTM | GTM score ranking, whitespace map, POI scatter, site profitability | Tells the field team where to go tomorrow |

---

## Predictive Models

### Churn Risk Model (`module4_models/churn_model.py`)
- **Algorithm:** Logistic Regression with `class_weight="balanced"`
- **Target:** Engineered churn risk label — bottom 20th percentile on both `subs_7d_change` AND `arpu_7d_change`
- **Features:** 7-day subscriber change, 7-day ARPU change, MOS score, drop call rate, income index, penetration rate, congestion, download speed
- **Results:** ROC-AUC **0.989** | Recall on at-risk class: **96%**
- **Business use:** Deploy retention offers to flagged LGAs within 48 hours of signal activation

### Site Profitability Forecast (`module4_models/site_profitability.py`)
- **Algorithm:** Gradient Boosting Regressor
- **Target:** `site_profit_proxy` — daily revenue minus daily opex per site (₦ NGN)
- **Features:** Site count, congestion, download speed, MOS score, monthly opex, population, penetration, income index, POI total, drop call rate, urban flag
- **Results:** R² **0.83** | MAE ₦1,343,734/site/day | CV R² 0.837 ± 0.016
- **Business use:** Identify infrastructure ROI leaders and flag loss-making sites for opex renegotiation

---

## GTM Opportunity Scoring (`module5_gtm/gtm_scoring.py`)

Composite score across all 41 LGAs. Methodology:

| Component | Weight | Rationale |
|---|---|---|
| Whitespace flag | 30% | High population + low penetration = unmet demand |
| Income index | 25% | Revenue potential of the market |
| POI density | 20% | Commercial footfall and distribution anchor points |
| Penetration gap | 15% | Bigger gap = bigger incremental opportunity |
| Site profit proxy | 10% | Existing infrastructure economics |

**Top 10 Priority Targets:** Sagamu, Nnewi North, Ogbomoso, Ife Central, Ilorin East (whitespace-flagged) + Alimosho, Port Harcourt, Surulere, Ikeja, Lekki (high-income, high-POI).

---

## Data Architecture

- **Grain:** One row per LGA per day
- **Coverage:** 41 LGAs × 90 days = 3,690 rows × 42 columns
- **States:** Lagos, Ogun, Oyo, Osun, Ondo, Ekiti, Kwara, Edo, Delta, Rivers, Anambra, Enugu
- **KPI benchmarks:** Grounded in NCC 2024 QoS reports, NBS population figures, MTN/Airtel ARPU data (post-2025 tariff hike)
- **Single source of truth:** All modules read from `master_table` only

---

## Technical Stack

| Layer | Technology |
|---|---|
| Data pipeline | Python, SQLite, Pandas, NumPy |
| Analytics | SQL, Matplotlib, Seaborn |
| Dashboard | Streamlit, Plotly |
| Deployment | Streamlit Cloud (free tier, live URL) |
| Predictive models | Scikit-learn (Logistic Regression, Gradient Boosting) |
| Supplementary BI | Power BI Service (DAX measures, 3-page report) |
| Version control | Git, GitHub |
| Environment | Ubuntu 24.04, Python 3.12 |

---

## Local Setup


# Clone the repo
git clone git@github.com:Fidelis-Akinbule/NigeriaRGI.git
cd NigeriaRGI

# Activate your Python environment
source /path/to/your/venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Generate the database
python module1_pipeline/generate_data.py

# Run analytics
python module2_analytics/analytics.py

# Launch dashboard
streamlit run module3_dashboard/app.py

# Run models
python module4_models/churn_model.py
python module4_models/site_profitability.py

# Run GTM scoring
python module5_gtm/gtm_scoring.py


---

## About

Built by **Fidelis Akinbule** — Lagos, Nigeria.
Data science professional with expertise in BI architecture, predictive analytics, and regional market intelligence for the Nigerian telecoms sector.

[GitHub](https://github.com/Fidelis-Akinbule) · [LinkedIn](https://linkedin.com/in/Fidelis-Akinbule)
