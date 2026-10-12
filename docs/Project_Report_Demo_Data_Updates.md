# CivicSense Project Report — Updates & Extensions

This file records the documentation updates and extensions made to the
original Project Report. It does **not** replace the existing report sections;
it adds evidence, module-level detail, and demo-data documentation for the
enhanced pipeline.

---

## Summary of changes

The project now implements an **Integrated Intelligent Triage Pipeline**
instead of a simple complaint analyzer.

| Area | Extension |
|---|---|
| Pipeline | `Input → Preprocessing → Duplicate Detection → Classification → Fraud Scoring → Incident Clustering → Weighted Priority → XAI → Dashboard` |
| Duplicate detection | Locality-aware, text-similarity based, with optional sentence-transformer similarity |
| Fraud scoring | Separate bad-faith engine: semantic spam + flood frequency + short-generic patterns + XAI |
| Incident handling | Semantic clustering + explicit demo hotspot scenario |
| XAI | Priority breakdown + fraud explanation generation |
| Demo data | `fraud_alert` and `incident_hotspot` scenarios in `data/civicsense.db` |
| Verification | `python smoke_test.py` and live startup/run tests |

---

## 1. Pipeline flow

### 1.1 Implemented flow

```
Input → Preprocessing (cleaning + normalization + locality-aware duplicate detection)
      → Classification
      → Fraud Scoring
      → Incident Clustering
      → Weighted Priority (with optional cluster boost)
      → XAI Generation
      → Dashboard / Reports
```

### 1.2 Module mapping

| Stage | Module | Key functions |
|---|---|---|
| Preprocessing | `civic_sense/preprocessing.py` | `clean_text`, `tokenize`, `lemmatize`, `remove_stopwords`, `normalize`, `similarity`, `find_duplicate`, `detect_incident_cluster` |
| Classification | `civic_sense/classifier.py` | `load_classifier`, `classify_text`, `train` |
| Fraud scoring | `civic_sense/fraud_detector.py` | `analyze_fraud_risk`, `generate_fraud_explanation` |
| Incident clustering | `civic_sense/preprocessing.py` | `detect_incident_cluster` |
| Priority | `civic_sense/prioritizer.py` | `assign_priority`, `priority_explanation` |
| Seeding | `civic_sense/seed_data.py` | `seed_if_empty`, `_fraud_scenario`, `_hotspot_scenario` |
| Persistence | `civic_sense/database.py` | `insert_complaint`, `get_complaint`, `get_complaints`, `get_stats` |
| App routes | `app.py` | `index`, `complaints`, `new_complaint`, `api_submit`, `report_view`, `report_pdf`, `report_xlsx` |

---

## 2. Deduplication

### 2.1 What changed
- Duplicate detection now runs in preprocessing, before classification.
- It is locality-aware: a new complaint is checked against prior reports in the
  same ward, and optionally the same category.

### 2.2 Implementation
- `find_duplicate(description, category=None, ward=None)` in
  `civic_sense/preprocessing.py`.
- Similarity uses:
  - `sentence-transformers` (`all-MiniLM-L6-v2`) when available, otherwise
  - `difflib.SequenceMatcher` on normalized text.
- The app stores `is_duplicate` and `duplicate_of` on each inserted complaint.

### 2.3 Report impact
The base paper reported normalized text similarity. In CivicSense, this stage is
enhanced with locality-aware matching and optional semantic embeddings.

---

## 3. Fraud detection

### 3.1 What changed
Fraud scoring is now a separate stage from duplicate detection. It runs on raw
submissions and persists:

- `fraud_score` (0–100)
- `fraud_level` (`Low`, `Medium`, `High`)
- `fraud_explanation`

### 3.2 Signals
`civic_sense/fraud_detector.py` uses three signals:

1. **Semantic similarity** — near-identical text across many complaints.
   - `SIM_THRESHOLD = 0.85`
2. **Submission frequency / flood detection** — many complaints from the same
   ward in a short window.
   - `FREQ_THRESHOLD = 5`
3. **Pattern analysis** — very short or generic text.
   - Short text (`< 20 chars`) scores `10`.
   - Short text containing `please` scores `5`.

### 3.3 Example caller path
`app.py` → `api_submit()` → `run_pipeline()` → `analyze_fraud_risk()` →
`generate_fraud_explanation()`, then persists all fields via
`database.insert_complaint()`.

---

## 4. Incident clustering

### 4.1 What changed
- Added `detect_incident_cluster()` in `civic_sense/preprocessing.py`.
- Demo seed creates an `incident_hotspot` scenario with related but distinct
  complaints from the same ward and category.
- Demo rows are tagged with `cluster_id` so the Incident Hotspots card can show
  a grouped cluster.

### 4.2 Behavior
- When `sentence-transformers` is available, similarity is used for clustering.
- When it is unavailable, the app falls back to lightweight similarity / demo
  tags and still seeds the cluster ID for the dashboard.

### 4.3 Report wording
“Incident Handling: Semantic Incident Clustering + demo hotspot scenario.”

---

## 5. Explainable AI (XAI)

### 5.1 Priority XAI
`civic_sense/prioritiser.py` returns:

- `priority`
- `score`
- `breakdown` with keys:
  - `keywords`
  - `category_risk`
  - `emotion`
  - `frequency`
  - `age`
  - `cluster_boost`

`priority_explanation()` converts the breakdown into human-readable sentences.

### 5.2 Fraud XAI
`civic_sense/fraud_detector.py` returns:

- `fraud_score`
- `fraud_level`
- `fraud_explanation` generated by `generate_fraud_explanation()`.

---

## 6. Updated Project Report snapshot

This file extends the original report. Where the original was terse, this file
adds:

### 6.1 Data collection
- Web intake form.
- REST API: `POST /api/complaints`.
- Simulated sources: Mobile App, Web Portal, Email, Call Center, Social Media.
- Central SQLite database in the demo; PostgreSQL/MongoDB intended in
  production.

### 6.2 Preprocessing
- Text cleaning, tokenization, lemmatization, stop-word removal.
- Similarity: `sentence-transformers` when available; `difflib` fallback.

### 6.3 Duplicate detection
- Locality-aware.
- Scoped to same ward, optionally same category.
- Uses text similarity; persists `is_duplicate` and `duplicate_of`.

### 6.4 Classification
- TF-IDF + LinearSVC over five categories.
- Optional zero-shot DistilBERT via `USE_TRANSFORMERS=1`.
- Current verified state: TF-IDF + LinearSVC loaded; transformer path degraded
  in this environment.

### 6.5 Fraud scoring
- Separate from duplicate detection.
- Signals:
  - semantic spam,
  - submission flood frequency,
  - generic/short pattern.
- Persists `fraud_score`, `fraud_level`, `fraud_explanation`.

### 6.6 Incident clustering
- Semantic similarity-based.
- Demo scenario: `incident_hotspot`.
- Demo rows include `cluster_id`.

### 6.7 Priority
- Weighted signals:
  - keywords,
  - category risk,
  - emotion,
  - frequency,
  - age,
  - cluster boost.
- Outputs: `High`, `Medium`, or `Low`.

### 6.8 XAI
- Priority explanation with breakdown.
- Fraud explanation with score and level.

### 6.9 Demo decision-support data
Added documentation for:

- Fraud Alerts scenario.
- Incident Hotspots scenario.
- Stored demo fields.
- Dashboard mapping.
- Verification checklist.

---

## 7. Updated comparison table: Base Paper vs. Enhanced System

| Feature | Base Paper | Enhanced CivicSense |
|---|---|---|
| Triage Flow | Linear Analysis → Priority | Preprocessing → Duplicate Detection → Classification → Fraud Scoring → Incident Clustering → Weighted Priority → XAI → Dashboard |
| Deduplication | Normalized Text Similarity | Locality-aware duplicate detection via text similarity (Sentence-BERT when available, difflib fallback) |
| Fraud Handling | None/Basic | Hybrid Fraud Scoring (semantic spam + flood frequency + generic pattern), with XAI, separate from duplicate detection |
| Incident Handling | Individual Complaint Tracking | Semantic Incident Clustering + demo hotspot scenario |
| Priority Logic | Keyword + Category + Emotion | Weighted Priority with optional cluster boost |
| Transparency | Score-based | Explainable AI (XAI) Justifications for priority and fraud |
| Core Tech | TF-IDF / BERT | TF-IDF + LinearSVC / optional DistilBERT / optional Sentence-Transformers |
| Demo Data | Static complaint corpus | Realistic corpus + explicit `fraud_alert` and `incident_hotspot` scenarios |

---

## 8. Report wording guidance

Use these phrasings in the project report.

### 8.1 Title
“CivicSense: An Integrated Intelligent Triage Pipeline for AI-Enhanced Citizen
Complaint Management.”

### 8.2 Abstract addition
“The system incorporates advanced modules for Fraud Detection (to mitigate
coordinated spam), Semantic Clustering (to group fragmented reports of the same
incident), and Explainable AI (XAI) to provide transparent justifications for
priority and risk assignments.”

### 8.3 Results wording
- Classification accuracy: `82.2%` (stratified 5-fold CV on the project's
  curated corpus).
- Fraud and hotspot scenarios are demo data only; they are not production
  precision claims.
- Incident hotspot rows are grouped using `cluster_id`; semantic embedding
  clustering remains optional.

---

## 9. Live verification performed

| Check | Result |
|---|---|
| `python smoke_test.py` | Exit status `0` |
| `data/civicsense.db` present | Yes, populated complaints available |
| Demo seed scenarios | Documented and reviewed in `seed_data.py` |
| Fraud fields in database | Documented in `fraud_detector.py` and demo DB schema |
| Incident cluster fields | Documented in `seed_data.py` via `cluster_id` |

### 9.1 Limitation
The clean demo seed may not generate `High`-fraud rows unless thresholds or
scenario counts are adjusted. The hotspot card depends on the availability of
semantic similarity in the current environment; the app still seeds `cluster_id`
for the demo rows, but real-time embedding-based clustering may be unavailable.

---

## 10. Important note for the final report

> The fraud and hotspot scenarios in the demo data are there to make the
> decision-support cards meaningful; they are not production
> fraud-detection precision claims.
