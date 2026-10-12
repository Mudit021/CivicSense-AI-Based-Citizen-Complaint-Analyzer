# 🏙️ CivicSense — Integrated Intelligent Triage Pipeline

An enhanced implementation of the base paper *"CivicSense: AI-Based Citizen Complaint Analyzer"* (Aakash P, Chandru T, Kiruba Wesley). This system evolves the basic analyzer into an **Integrated Intelligent Triage Pipeline**, incorporating Fraud Detection, Semantic Clustering, and Explainable AI (XAI).

The system turns unstructured citizen complaints into structured, prioritized,
summarized governance intelligence through an advanced AI pipeline:

```
Input → Preprocessing → Duplicate Detection → Classification →
Fraud Scoring → Incident Clustering → Weighted Priority → XAI Generation → Dashboard
```

## ✨ Features

| Stage | Implementation |
|---|---|
| **1. Data collection** | Web intake form + REST API (`POST /api/complaints`) simulating mobile apps, web portals, email and call centres; central SQLite database (PostgreSQL/MongoDB in production) |
| **2. Preprocessing** | Text cleaning, tokenization, lemmatization (WordNet), stop-word removal. Text similarity uses `sentence-transformers` (`all-MiniLM-L6-v2`) when available, otherwise a difflib fallback |
| **3. Duplicate Detection** | Locality-aware duplicate detection (same ward, optional category) based on text similarity, so repeated legitimate reports of the same incident are not over-counted |
| **4. Fraud Scoring** | Hybrid bad-faith risk engine, separate from duplicate detection. Signals: semantic spam (near-identical texts across many complaints), submission frequency (flood detection in a short window), and generic/short content patterns |
| **5. Classification** | TF-IDF + LinearSVC over five categories (Roads, Electricity, Water Supply, Waste Management, Public Safety) with confidence scores — optional zero-shot DistilBERT (`USE_TRANSFORMERS=1`) when the environment supports it |
| **6. Weighted Priority** | Multi-signal urgency scoring: urgency keywords, category risk, emotive language, locality frequency, age, and optional cluster boost → High / Medium / Low |
| **7. XAI Generation** | Explainable AI providing human-readable justifications for both fraud risk and priority scores, ensuring transparency in government triage |
| **8. Reports & Dashboard** | Officer dashboard (category mix, priority donut, daily inflow, locality hotspots), weekly digest generation, **PDF & Excel export** |

## 🧭 Current verified state

This repository has been verified end to end on the current environment:

- Core dependencies (`flask`, `scikit-learn`, `pandas`, `nltk`, `reportlab`, `openpyxl`) are installed and importable.
- `python smoke_test.py` runs the real pipeline through the Flask test client and prints `ALL SMOKE TESTS PASSED` (all checks pass, exit code `0`).
- `python app.py` starts the server on `http://127.0.0.1:5000`; every page returns HTTP 200 and the REST API returns the classified category, priority and fraud level.
- On a fresh seed the dashboard's decision-support cards are **populated**: Fraud Alerts shows the highest-risk filings (High and Medium) and Incident Hotspots shows each incident cluster with its size.
- Incident clustering works with or without the transformer stack: it uses sentence-transformer embeddings when available and otherwise falls back to difflib similarity, so the Incident Hotspots card is populated in either case.

### Environment limitation (do not change just one package)

The installed PyTorch (`2.2.0`) is below the minimum the current `transformers`/`sentence-transformers` releases expect (`2.5+`), so `import sentence_transformers` fails at import time. The app degrades gracefully: text similarity falls back to difflib, classification stays on sklearn TF-IDF + LinearSVC, and the smoke suite still passes.

If you want the embedding-based semantic clustering and the transformer classifier back, upgrade **both** PyTorch and the ML packages together — do not upgrade only `transformers`/`sentence-transformers`, or imports will break in the same way. Until then those paths remain optional, as marked in `requirements.txt`.

## 🚀 Quick start

The fast path does everything for you (install deps, fetch NLTK data, start the app):

```bash
./run.sh          # install + run the app
./run.sh test     # install + run the end-to-end smoke suite
```

Or do it manually:

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
2. Seeds ~180 realistic complaints — plus a fraud-alert burst and an incident-hotspot
   cluster — all processed through the live pipeline, so every chart, card and digest
   is instantly populated.

Run the end-to-end test suite with:

```bash
python smoke_test.py
```

The suite starts from a clean database, so its seeded counts are reproducible.

## 🔌 REST API

```bash
# Submit a complaint (any channel → portal integration)
curl -X POST http://127.0.0.1:5000/api/complaints \
  -H "Content-Type: application/json" \
  -d '{"description":"Sewage overflowing near the market area","ward":"Wakad","source":"Mobile App"}'

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
| `USE_TRANSFORMERS` | `0` | Set to `1` to use zero-shot DistilBERT for classification (requires a supported `torch` + `transformers` stack) |
| `TRANSFORMER_MODEL` | `distilbert-base-uncased` | HuggingFace model name |

## 🧠 Research extensions included

Beyond the base paper's pipeline, this implementation integrates:

- **Fraud / bad-faith scoring** — separate from duplicate detection. It scores floods, near-identical spam across different reporters, and short/generic content. The demo seed now includes an explicit **fraud-alert scenario**: a tight burst of near-identical, short, generic reports from one ward within a narrow time window, so the Fraud Alerts card has something concrete to show.
- **Incident hotspots / clustering** — semantic similarity is used to group complaints describing the same underlying incident even when they are not near-duplicates. The demo seed now includes an explicit **incident-hotspot scenario**: a cluster of related-but-distinct complaints about one incident in one ward and one category, so the Incident Hotspots card has a representative cluster to display.
- **Explainable AI (XAI) for priority and fraud** — every priority decision exposes a numeric breakdown and sentence-level justification; fraud risk is explained too.
- **Configurable thresholds and weights** — all pipeline knobs (categories, wards, priorities, similarity cutoffs, priority thresholds, fraud thresholds, and the fraud/hotspot seed scenario sizes) live in `civic_sense/config.py`, `civic_sense/fraud_detector.py`, and `civic_sense/seed_data.py`.
- **Demo-data scenarios are documented**: the fraud-alert and incident-hotspot records are generated with an internal `scenario` label so the demo is explainable and the bulk generation stays unambiguous. They are not production fraud-detection precision claims.

## 📁 Project layout

```
app.py                 # Flask application & routes
civic_sense/
  config.py            # paths, categories, thresholds
  database.py          # SQLite persistence (complaints, reports)
  preprocessing.py     # cleaning, tokenization, lemmatization, dedup, clusters
  classifier.py        # TF-IDF + LinearSVC (+ optional DistilBERT)
  prioritizer.py       # explainable High/Medium/Low urgency engine
  summarizer.py        # extractive summaries + weekly digests
  reports.py           # PDF (reportlab) & Excel (openpyxl) export
  seed_data.py         # realistic demo complaint generator
  fraud_detector.py    # independent fraud/spam risk scoring
templates/             # Jinja2 pages (dashboard, complaints, reports…)
static/css/style.css   # self-contained stylesheet (no CDN, works offline)
data/                  # SQLite DB + generated reports (created at runtime)
models/                # trained classifier artifacts (created at runtime)
smoke_test.py          # end-to-end test suite
run.sh                 # one-command setup + run
civic_sense/build_report.py  # regenerates Project_Report.docx from measured data
```

## 📊 Results (vs. base paper)

| Metric | CivicSense (this project) | Base paper |
|---|---|---|
| Classification accuracy | **82.2%** (stratified 5-fold CV on the project's curated corpus) | 93% |
| Priority assignment | Explainable multi-signal scoring (keywords, category risk, emotion, frequency, age, optional cluster boost) | Rule + AI hybrid |
| Fraud detection | Separate spam/flood/pattern risk scoring with XAI; demo seed includes an explicit fraud-alert scenario | Not in base paper |
| Incident hotspots | Incident clustering plus an explicit hotspot scenario in the demo data | Not in base paper |
| Explainability | Priority + fraud XAI | Not in base paper |
| Reports | PDF + Excel weekly digests | PDF/Excel weekly digests |
| Officer time saved | Digest + dashboard (65% claimed in paper) | 65% |

> Note: the paper's 93% is reported on its own dataset. The accuracy shown here is measured by stratified 5-fold cross-validation on this project's curated training corpus, so it is a conservative, reproducible figure. The fraud and hotspot scenarios are demo data injected solely to make decision-support cards meaningful; they are not a claim about fraud-detection precision in production.

> Reproducibility note: the demo seed is deterministic (a fixed random state in `seed_data.py`), so a fresh database always produces the same corpus and the same dashboard counts — 200 complaints, 112 High / 80 Medium / 8 Low, 23 duplicates, 18 clustered records across 11 clusters, and 2 High / 53 Medium fraud scores.

## 📄 Project report

`Project_Report.docx` (at the repository root) is the full written report — 12 numbered sections plus eight appendices. It is generated, not hand-edited:

```bash
python civic_sense/build_report.py   # regenerates Project_Report.docx from measured data
```
