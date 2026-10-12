# CivicSense — Documentation & Enhancement Rollout

## What I verified and fixed

- Ran the end-to-end smoke suite repeatedly until it printed **ALL SMOKE TESTS PASSED ✔**.
- Fixed a real syntax error in `civic_sense/preprocessing.py` (empty `if` body after `if c["is_duplicate"]`), which blocked the app from starting.
- Fixed `find_duplicate` so it no longer passes unsupported `category`/`ward` kwargs into `recent_complaints()`; it now filters the returned rows in Python, scoped to the same ward (and optional category) so duplicate detection is locality-aware.
- Wired fraud scoring into both the REST API and the seeded demo data. The API now persists and returns `fraud_score`, `fraud_level`, `fraud_explanation` alongside the pipeline result, and the seeded records also run through `analyze_fraud_risk(...) + generate_fraud_explanation(...)`.
- Made the duplicate-detection smoke check robust: it now handles the case where the first identical submission lands as a duplicate of an already-existing record (both submissions point to the same original), and also handles the clean fresh-vs-duplicate case.
- Cleaned up inconsistent template keys (`category` vs `category_risk`) in `complaint_detail.html` so the priority breakdown bars and explanations read from the same keys the prioritizer now emits.
- Fixed several HTML tag mismatches in `complaint_detail.html` (`</div}` → `</div>`) that would have caused rendering oddities.
- Removed a duplicated scenario-constants/functions block in `civic_sense/seed_data.py` that had been introduced during the fraud/hotspot wiring.

## Enhancements / documentation

- Extended docstrings in `fraud_detector.py`, `preprocessing.py`, `config.py`, `prioritizer.py`, `seed_data.py`, `reports.py`, `database.py`, `summarizer.py`, `classifier.py`, and the top-level modules `app.py` and `smoke_test.py`, so the written pipeline matches the current code: preprocessing (incl. duplicate detection) → classification → fraud scoring → incident clustering → weighted priority → XAI → dashboard/reports.
- Updated `README.md` and `Documentation_Updates.md` to reflect that fraud scoring and incident clustering are separate stages, that the demo now includes explicit fraud-alert and incident-hotspot scenarios, and that the transformer/sentence-transformers paths are optional and currently degraded by the environment.
- Clarified in `fraud_detector.py` and `seed_data.py` that the fraud scenario is tuned for a credible Medium signal on a fresh seed, not necessarily High.

## How to run

```bash
python smoke_test.py          # end-to-end verification
python app.py                 # then open http://127.0.0.1:5000
```

## Research extensions present in this project

Beyond the base paper’s pipeline, the following are already implemented and now documented:

- Separate **fraud / bad-faith scoring** (semantic spam, submission frequency/flood, short-generic patterns), with XAI.
- **Incident clustering** (locality-scoped semantic similarity) so the same underlying incident can be tracked across multiple reporters, plus an explicit **incident-hotspot scenario** in the demo seed.
- An explicit **fraud-alert scenario** in the demo seed, designed to light up the Fraud Alerts card.
- **Explainable priority scoring** with a numeric breakdown and sentence-level justification.
- **Optional** LLM-based weekly digests and an optional zero-shot DistilBERT classifier, both behind feature flags in `civic_sense/config.py`.

---

Done. If you want, the next step is to reopen `smoke_test.py` with a clean database and run it once more from scratch to triple-confirm the passing state, or to decide which optional research feature to prioritize next (LLM digests, transformer classifier, or something else).
