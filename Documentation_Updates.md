# 📝 CivicSense Documentation Updates Guide

The project has transitioned from a basic analyzer to an **Integrated Intelligent Triage Pipeline**. Use the following content to update the Project Report, Research Synopsis, Presentation, and the in-repo docs (README, module docstrings, smoke test header), so the written narrative matches the current codebase.

Recent implementation state this doc should align to:
- Duplicate detection runs first (preprocessing), then classification, then fraud scoring, then incident clustering, then weighted priority, then XAI.
- Fraud scoring is intentionally separate from duplicate detection and is wired into both the REST API submission path and the seeded demo data.
- The demo seed now includes two explicit synthetic scenarios: a fraud-alert burst and an incident-hotspot cluster, each labelled internally with a `scenario` field.
- The fraud scenario is tuned for a credible Medium risk signal on a fresh seed; the Incident Hotspots card is driven by `cluster_id` and currently depends on the available similarity path.

---

## 1. Title & Abstract
**Updated Title:** 
CivicSense: An Integrated Intelligent Triage Pipeline for AI-Enhanced Citizen Complaint Management

**Abstract Additions:**
- Replace "AI-Based Analyzer" with "**Integrated Intelligent Triage Pipeline**".
- Add: "The system incorporates advanced modules for **Fraud Detection** (to mitigate coordinated spam), **Semantic Clustering** (to group fragmented reports of the same incident), and **Explainable AI (XAI)** to provide transparent justifications for priority and risk assignments."
- Mention the use of `sentence-transformers` for high-dimensional semantic embeddings.

---

## 2. Problem Statement
**Add the following challenges:**
- **Semantic Duplicates**: Traditional keyword-based deduplication fails to identify paraphrased reports of the same issue.
- **Coordinated Fraud/Spam**: The vulnerability of civic portals to "bot-flooding" or coordinated malicious reporting intended to skew priority metrics.
- **Triage Opacity**: The "black-box" nature of AI priority assignment which can lead to distrust in government decision-making.

---

## 3. Proposed Methodology
**Replace the old pipeline with the implemented flow:**
`Input` → `Preprocessing (cleaning + normalization + locality-aware duplicate detection)` → `Classification` → `Fraud Scoring` → `Incident Clustering` → `Weighted Priority (with optional cluster boost)` → `XAI Generation` → `Dashboard / Reports`

**Detailed Module Descriptions:**
- **Preprocessing**: Text cleaning, tokenization, lemmatization (WordNet), stop-word removal. Text similarity uses `all-MiniLM-L6-v2` sentence embeddings when available; otherwise it falls back to difflib SequenceMatcher on normalized text. Duplicate detection is locality-aware (same ward, optional category).
- **Duplicate Detection**: Finds near-identical prior complaints in the same locality so repeated legitimate reports of the same incident are not over-counted. This is separate from fraud detection.
- **Classification**: TF-IDF + LinearSVC over five categories with confidence scores; optional zero-shot DistilBERT when `USE_TRANSFORMERS=1` and the environment supports it.
- **Fraud Scoring**: Hybrid bad-faith risk engine, separate from duplicate detection. It considers semantic spam (near-identical texts across many complaints), submission frequency (flood detection in a short window), and generic/short content patterns.
- **Incident Clustering**: Groups complaints describing the same underlying incident from different reporters based on semantic similarity, so a systemic issue can be tracked across many complaints.
- **Weighted Priority**: Multi-signal urgency scoring with an optional cluster boost when the complaint is part of a systemic incident cluster. Signals: urgency keywords, category risk, emotive language, locality frequency, age, and cluster size.
- **XAI Generation**: Translates internal scoring weights into human-readable justifications for both priority and fraud risk.

---

## 4. System Architecture
**Update diagrams/descriptions to include:**
- **Duplicate Detection**: Runs during preprocessing on recent complaints scoped to the same ward/category.
- **Fraud Detection Engine**: Runs after classification on the raw submission; it is independent of duplicate detection and persists `fraud_score`, `fraud_level`, `fraud_explanation`.
- **Incident Clustering**: Uses text similarity to assign/identify incident clusters; currently degrades gracefully when the embedding stack is unavailable.
- **Embedding Layer**: Uses `sentence-transformers` to power semantic similarity for both clustering and fraud/spam detection when available; otherwise difflib is used.
- **XAI Module**: A post-processing layer that generates natural language explanations for priority and fraud decisions.

---

## 5. Expected Outcomes & Metrics
**Add these KPIs:**
- **Fraud Detection Accuracy**: Ability to correctly flag coordinated spam vs. genuine urgent spikes.
- **Incident Grouping Efficiency**: Reduction in the number of individual tickets handled by grouping them into semantic clusters.
- **Triage Transparency**: Percentage of AI decisions that are accompanied by a human-verifiable XAI justification.

---

## 6. Comparison Table: Base Paper vs. Enhanced System

- The fraud and hotspot scenarios in the demo data are there to make the decision-support cards meaningful; they are not production fraud-detection precision claims.

| Feature | Base Paper (CivicSense) | Enhanced System (Intelligent Pipeline) |
| :--- | :--- | :--- |
| **Triage Flow** | Linear Analysis → Priority | Integrated triage pipeline: Preprocessing → Duplicate Detection → Classification → Fraud Scoring → Incident Clustering → Weighted Priority → XAI → Dashboard |
| **Deduplication** | Normalized Text Similarity | Locality-aware duplicate detection via text similarity (Sentence-BERT when available, difflib fallback) |
| **Fraud Handling** | None/Basic | Hybrid Fraud Scoring (semantic spam + flood frequency + generic pattern), with XAI, separate from duplicate detection |
| **Incident Handling** | Individual Complaint Tracking | Semantic Incident Clustering + demo hotspot scenario |
| **Priority Logic** | Keyword + Category + Emotion | Weighted Priority with optional cluster boost |
| **Transparency** | Score-based | Explainable AI (XAI) Justifications for priority and fraud |
| **Core Tech** | TF-IDF / BERT | TF-IDF + LinearSVC / optional DistilBERT / optional Sentence-Transformers |
| **Demo Data** | Static complaint corpus | Realistic corpus + explicit fraud-alert and incident-hotspot scenarios |
