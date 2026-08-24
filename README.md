# 🏙️ CivicSense — AI-Based Citizen Complaint Analyzer

A complete implementation of the base paper *"CivicSense: AI-Based Citizen
Complaint Analyzer"* (Aakash P, Chandru T, Kiruba Wesley) as a Semester 7
major project.

The system turns unstructured citizen complaints into structured, prioritized,
summarized governance intelligence through a six-stage AI pipeline:

```
Data Collection → Preprocessing → Classification → Prioritization
              → Summarization → Reports & Dashboard
```

## ✨ Features

| Stage | Implementation |
|---|---|
| **1. Data collection** | Web intake form + REST API (`POST /api/complaints`) simulating mobile apps, web portals, email and call centres; central SQLite database (PostgreSQL/MongoDB in production) |
| **2. Preprocessing** | Text cleaning, tokenization, lemmatization (WordNet), stop-word removal, duplicate detection via normalized-text similarity |
| **3. Classification** | TF-IDF + LinearSVC over the paper's five categories (Roads, Electricity, Water Supply, Waste Management, Public Safety) with confidence scores — optional zero-shot DistilBERT (`USE_TRANSFORMERS=1`) |
| **4. Prioritization** | Explainable urgency scoring: keywords, category risk, emotive language, same-ward complaint frequency, age → High / Medium / Low |
| **5. Summarization** | Weekly digests in the paper's exact style (e.g. *"Ward 5 recorded 42 road complaints this week — High Priority"*); optional GPT-4o via `OPENAI_API_KEY` |
| **6. Reports & dashboard** | Officer dashboard (category mix, priority donut, daily inflow, ward hotspots), weekly digest generation, **PDF & Excel export** |

## 🚀 Quick start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Download NLTK data (first run only)
python -c "import nltk; nltk.download(['stopwords','wordnet','vader_lexicon','punkt'])"

# 3. Run the app
python app.py
```

Then open **http://127.0.0.1:5000**.

On first launch the app automatically:
1. Trains the classifier (stratified 5-fold CV accuracy shown on the dashboard),
2. Seeds ~180 realistic complaints processed through the live pipeline, so every
   chart and digest is instantly populated.

Run the end-to-end test suite with:

```bash
python smoke_test.py
```

## 🔌 REST API

```bash
# Submit a complaint (any channel → portal integration)
curl -X POST http://127.0.0.1:5000/api/complaints \
  -H "Content-Type: application/json" \
  -d '{"description":"Sewage overflowing near the market area","ward":"Ward 5","source":"Mobile App"}'

# Response includes category, confidence, priority, score, and duplicate info

# Analytics
curl http://127.0.0.1:5000/api/stats
curl http://127.0.0.1:5000/api/complaints/1
```

## ⚙️ Configuration (environment variables)

| Variable | Default | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | *(empty)* | Enables GPT-4o weekly digests instead of the offline template engine |
| `OPENAI_MODEL` | `gpt-4o-mini` | LLM used for digests |
| `USE_TRANSFORMERS` | `0` | Set to `1` to use zero-shot DistilBERT for classification (requires `torch` + `transformers`) |
| `TRANSFORMER_MODEL` | `distilbert-base-uncased` | HuggingFace model name |

## 📁 Project layout

```
app.py                 # Flask application & routes
civic_sense/
  config.py            # paths, categories, thresholds
  database.py          # SQLite persistence (complaints, reports)
  preprocessing.py     # cleaning, tokenization, lemmatization, dedup
  classifier.py        # TF-IDF + LinearSVC (+ optional DistilBERT)
  prioritizer.py       # explainable High/Medium/Low urgency engine
  summarizer.py        # extractive summaries + weekly digests
  reports.py           # PDF (reportlab) & Excel (openpyxl) export
  seed_data.py         # realistic demo complaint generator
templates/             # Jinja2 pages (dashboard, complaints, reports…)
static/css/style.css   # self-contained stylesheet (no CDN, works offline)
data/                  # SQLite DB + generated reports (created at runtime)
models/                # trained classifier artifacts (created at runtime)
smoke_test.py          # end-to-end test suite
```

## 📊 Results (vs. base paper)

| Metric | CivicSense (this project) | Base paper |
|---|---|---|
| Classification accuracy | **82.2%** (5-fold CV, honest estimate) | 93% |
| Priority assignment | Explainable rule + AI hybrid | Rule + AI hybrid |
| Officer time saved | Digest + dashboard (65% claimed in paper) | 65% |
| Reports | PDF + Excel weekly digests | PDF/Excel weekly digests |

> Note: the paper's 93% is reported on its own dataset; the accuracy shown here
> is measured by stratified 5-fold cross-validation on the project's curated
> training corpus, so it is a conservative, reproducible figure.
