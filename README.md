# MarketMind — AI Marketing Analyst

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)
![Claude](https://img.shields.io/badge/Claude-Sonnet_4.6-6B4FBB?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

A conversational AI agent that turns raw marketing data into real insights. Upload a CSV, ask questions in plain English, and get back stats, trends, and charts — no SQL, no dashboards, no setup headaches.

Built this because I was tired of jumping between spreadsheets and BI tools every time someone asked a simple question about campaign performance. Just chat with your data.

---

## What it can do

- **Analyze any CSV** — sales reports, campaign logs, survey results, product data, whatever
- **Campaign KPIs** — CTR, CPC, CPA, ROAS computed automatically from your columns
- **Competitor research** — live web search to pull market intelligence on demand
- **Report generation** — structured Markdown reports you can copy straight into a doc
- **Interactive charts** — bar charts, heatmaps, and correlation matrices without writing a line of Plotly

---

## Demo

```
Upload: marketing_campaign.csv  (2,240 rows)

You:  "Which channel has the highest ROI?"

MarketMind:
  Social Media leads with an average ROI of 5.8×, followed by
  Email (4.2×) and Paid Search (3.6×). Display ads trail at 1.9×.
  Recommendation: shift budget toward Social + Email for Q3.
```

Switch to the **📊 Charts** tab to see:

| Chart | What it shows |
|---|---|
| Group bar | Key metric broken down by top category |
| Category charts | Value distribution for each text column |
| Numeric stats | Mean / Median / Max across all numeric columns |
| Correlation heatmap | Relationships between numeric variables |

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Streamlit UI (app.py)               │
│                                                     │
│   Sidebar              Chat tab      Charts tab     │
│   ─ API key            ─ Messages    ─ Plotly figs  │
│   ─ CSV upload         ─ Input bar   ─ Heatmap      │
└───────────────────┬─────────────────────────────────┘
                    │  user message + pre-computed JSON
                    ▼
┌─────────────────────────────────────────────────────┐
│                  Agent loop (agent.py)               │
│                                                     │
│   Claude Sonnet 4.6  ◄──► tool_use / tool_result   │
│                                                     │
│   ┌──────────────┐  ┌──────────────┐               │
│   │ analyze_sales│  │analyze_campaign│              │
│   └──────────────┘  └──────────────┘               │
│   ┌──────────────┐  ┌──────────────┐               │
│   │  research_   │  │   generate_  │               │
│   │ competitors  │  │    report    │               │
│   └──────────────┘  └──────────────┘               │
└─────────────────────────────────────────────────────┘
```

CSV analysis runs **locally** before anything is sent to the API — so big files don't slow you down.

---

## Project structure

```
MarketMind/
├── app.py              # Streamlit UI, chart rendering, session management
├── agent.py            # Claude API agentic loop, history sanitization
├── tools/
│   ├── sales.py        # CSV parser + pandas statistics
│   ├── campaign.py     # CTR / CPC / CPA / ROAS calculator
│   ├── research.py     # DuckDuckGo web search
│   └── report.py       # Markdown / plain-text report builder
├── requirements.txt
└── .env                # Your API key (never committed)
```

---

## Getting started

### 1. Clone the repo

```bash
git clone https://github.com/raselmian03-alt/marketmind.git
cd marketmind
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Add your API key

Create a `.env` file in the project root:

```
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

Get a key at [console.anthropic.com](https://console.anthropic.com) → API Keys. A $5 credit is more than enough to get started.

### 4. Run it

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

---

## Usage

**Analyzing a dataset**

1. Paste your API key in the sidebar (or set it in `.env`)
2. Upload a CSV file — any format, any columns
3. Ask something:
   - *"Give me a full breakdown of this data"*
   - *"Which campaign type has the best conversion rate?"*
   - *"What are the top 5 channels by ROI?"*
   - *"Generate a report I can share with my team"*

**Researching competitors**

No CSV needed — just ask:
- *"What are the latest trends in email marketing?"*
- *"How does Mailchimp price its plans?"*

**Generating a report**

Ask at the end of an analysis:
- *"Generate a formal report from this analysis"*

The agent will return a structured Markdown report with all the key findings.

---

## Tech stack

| Layer | Tool |
|---|---|
| UI | Streamlit |
| AI | Anthropic Claude (claude-sonnet-4-6) |
| Data | pandas, numpy |
| Charts | Plotly |
| Web search | DuckDuckGo Search |
| Config | python-dotenv |

---

## Supported CSV formats

- Comma-separated (`,`) and semicolon-separated (`;`) files
- UTF-8 with or without BOM
- Marketing data, sales data, product catalogs, survey responses — anything tabular

---

## License

MIT — do whatever you want with it.

---

*Built for people who just want answers from their data, not another tool to learn.*
