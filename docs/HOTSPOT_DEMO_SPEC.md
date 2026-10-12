# Demo Decision-Support Data in CivicSense

## Purpose
This section documents the demo dataset shipped with CivicSense and the two
decision-support cards it feeds:

1. **Fraud Alerts** (`templates/index.html`)
2. **Incident Hotspots** (`templates/index.html`)

These are not production fraud-detection precision claims. They are synthetic
demo rows that make the dashboard, weekly digest, and project report show
realistic signal: coordinated-looking fraudulent filings for Fraud Alerts, and
related but distinct safety complaints for Incident Hotspots.

---

## Where the data comes from
- Source: `civic_sense/seed_data.py`
- Entry point: `seed_if_empty()` in `civic_sense/seed_data.py`
- Persistence: SQLite complaints table at `data/civicsense.db`
- Related pipeline: `app.py` startup loads the trained classifier and seeds
  complaints only when the database is empty.
- Related APIs:
  - `POST /api/complaints` saves a complaint and computes fraud fields.
  - `GET /api/stats` returns aggregate complaint statistics.
  - `GET /api/complaints/<id>` returns a stored row.

---

## Scenario counts
On a fresh database, `seed_if_empty()` inserts approximately **180 realistic
base complaints plus**:

| Scenario | Label (stored in `scenario`) | Ward | Category | Purpose |
|---|---|---|---|---|
| Fraud alert | `fraud_alert` | `Hinjewadi` | `Roads` | Flood of near-identical generic complaints |
| Incident hotspot | `incident_hotspot` | `Wakad` | `Public Safety` | Related-but-distinct safety complaint cluster |

Rows are also marked with:

- `is_duplicate` and `duplicate_of` for the duplicate-detection stage.
- `fraud_score`, `fraud_level`, and `fraud_explanation` for the fraud-risk card.
- `cluster_id` for the incident-hotspot grouping.
- `priority_score`, `priority_breakdown`, `cluster_id`, and `xai_explanation`
  for priority and XAI display.

---

## Fraud Alerts scenario
The fraud scenario is a short burst of near-identical, short, generic reports
submitted from the same ward within a narrow time window.

Key parameters (from `civic_sense/seed_data.py`):

- `FRAUD_SCENARIO_COUNT = 7`
- `FRAUD_SCENARIO_WARD = "Hinjewadi"`
- `FRAUD_SCENARIO_START_HOURS_AGO = 1.25`
- `_FRAUD_SPAM_TEMPLATES` contains short repetitive texts such as:
  - `"Please fix this issue immediately"`
  - `"Need urgent attention please"`
  - `"Immediate action required please"`
  - `"Please attend to this ASAP"`
  - etc.

Rationale:
- Repeated identical text triggers the fraud detector's semantic-similarity
  signal.
- One ward in a ~1.5-hour window triggers the submission-frequency / flood
  signal.
- Short and generic text triggers the pattern-analysis signal.

Expected dashboard effect:
- Rows in the Fraud Alerts table can appear with `fraud_level` set to `Medium`
  on a clean seed, depending on thresholds in `FREQ_THRESHOLD` and
  `SIM_THRESHOLD` in `civic_sense/fraud_detector.py`.
- The dashboard card only shows `fraud_level == 'High'`, so a clean seed
  may show a Medium risk summary even if individual rows are Medium.

Implementation notes:
- Each generated row runs through:
  1. `classify_text()`
  2. `find_duplicate()`
  3. `similar_complaints()`
  4. `analyze_fraud_risk()`
  5. `generate_fraud_explanation()`
  6. `database.insert_complaint()`

---

## Incident Hotspots scenario
The incident-hotspot scenario injects a small cluster of distinct-but-related
safety complaints about one underlying incident in one ward and one category.

Key parameters (from `civic_sense/seed_data.py`):

- `HOTSPOT_SCENARIO_COUNT_WORDS = 8`
- `HOTSPOT_SCENARIO_SPREAD_HOURS = 6`
- `HOTSPOT_SCENARIO_WARD = "Wakad"`
- `HOTSPOT_SCENARIO_CATEGORY = "Public Safety"`

Templates include near-paraphrases of a single event, for example:

- Tree blocked on the road
- Fallen branch obstructing traffic
- Debris from a fallen tree
- A tree branch fell near the location
- Road blocked by a fallen tree

The scenario is deliberately phrased differently so rows are **not treated as
duplicates** of one another, but semantic similarity can still group them as an
incident for the dashboard.

Implementation notes:
- Rows are inserted with `category = "Public Safety"` and `ward = "Wakad"`.
- On startup, `seed_if_empty()` runs the same pipeline as normal complaints:
  classification, duplicate detection, priority, and fraud scoring.
- `cluster_id` is set to a deterministic demo cluster value so the Incident
  Hotspots card can group the related rows even when the optional
  sentence-transformers similarity path is unavailable.

Behavioral caveat:
- The Incident Hotspots card in `templates/index.html` groups complaints by
  `cluster_id` from a recent batch.
- If semantic clustering is not available (for example, the
  sentence-transformers import fails), the app still sets the demo `cluster_id`,
  but real-time on-the-fly clustering will remain inactive until the embedding
  path is supported again.

---

## Dashboard display mapping
### Fraud Alerts
Template block to verify:

```jinja
{% set fraud_list = [] %}
{% for c in recent %}
  {% if c.fraud_level == 'High' %}{% set _ = fraud_list.append(c) %}{% endif %}
{% endfor %}
```

- Matches `fraud_level == "High"`.
- Shows ID, Title, Risk badge, and Fraud Score.
- No high-risk rows are currently present in the clean demo DB.

Recommended demo verification:
1. Open `http://127.0.0.1:5000/`.
2. Check the Fraud Alerts card.
3. If no rows appear, lower demo fraud thresholds carefully or add more
   `fraud_alert` rows; this is a threshold/demo-data choice, not a pipeline
   defect.

### Incident Hotspots
Template block to verify:

```jinja
{% for c in recent %}
  {% if c.cluster_id %}
    ...
    {% set _ = clusters.append({'id': c.cluster_id, 'title': c.title, 'count': 1}) %}
  {% endif %}
{% endfor %}
```

- Matches `cluster_id` present on recent complaints.
- Groups rows by cluster ID and shows size.
- In the current demo DB, hotspot cluster rows carry `cluster_id`, so these rows
  should appear in the Incident Hotspots card.

---

## Verification checklist
Use this checklist when checking the demo:

- [ ] `python smoke_test.py` still passes.
- [ ] `data/civicsense.db` contains `scenario = "fraud_alert"` rows.
- [ ] `data/civicsense.db` contains `scenario = "incident_hotspot"` rows.
- [ ] Fraud-scoring fields exist on those rows:
  - `fraud_score`
  - `fraud_level`
  - `fraud_explanation`
- [ ] Incident cluster fields exist on those rows:
  - `cluster_id`
- [ ] Dashboard shows the Fraud Alerts card.
- [ ] Dashboard shows the Incident Hotspots card grouped by cluster ID.
- [ ] Weekly digest does not treat scenario rows as real production records.

---

## Intent and use in the report
For the Project Report, this section maps to:

- **Problem statement**: semantic duplicates, coordinated fraud/flooding, and
  triage opacity.
- **Methodology**: preprocessing, duplicate detection, classification, fraud
  scoring, incident clustering, weighted priority, and XAI.
- **Architecture**: app routes, `civic_sense` modules, database, and
  decision-support dashboard.
- **Demo/Implementation**: the two explicit synthetic scenarios above.
- **Limitations**: the current clean demo seed may not generate `High` fraud
  rows; hotspot clustering depends on similarity availability; the data are
  synthetic and not production precision claims.
