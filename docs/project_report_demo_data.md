# 10. Demo Decision-Support Data in CivicSense

## 10.1 Purpose

This section documents the demo dataset shipped with CivicSense and the two
decision-support cards it feeds:

1. **Fraud Alerts** (`templates/index.html`)
2. **Incident Hotspots** (`templates/index.html`)

These are not production fraud-detection precision claims. They are synthetic
demo rows that make the dashboard, weekly digest, and project report show
realistic signal:

- **Fraud Alerts**: a coordinated-looking burst of fraudulent-looking filings.
- **Incident Hotspots**: related but distinct citizen complaints that belong to
  the same underlying incident.

---

## 10.2 Where the data comes from

| Item | Value |
|---|---|
| Source module | `civic_sense/seed_data.py` |
| Entry point | `seed_if_empty()` |
| Persistence | `data/civicsense.db` (SQLite) |
| Startup behavior | `app.py` seeds complaints only when the database is empty |
| Related API | `POST /api/complaints`, `GET /api/stats`, `GET /api/complaints/<id>` |

Every seeded complaint is processed through the live pipeline:

1. `classify_text()`
2. `find_duplicate()`
3. `similar_complaints()`
4. `analyze_fraud_risk()`
5. `generate_fraud_explanation()`
6. `database.insert_complaint()`

---

## 10.3 Scenario counts

On a fresh database, `seed_if_empty()` inserts approximately **180 realistic
base complaints plus**:

| Scenario | Label in `scenario` | Ward | Category | Purpose |
|---|---|---|---|---|
| Fraud alert | `fraud_alert` | `Hinjewadi` | `Roads` | Short burst of near-identical generic complaints |
| Incident hotspot | `incident_hotspot` | `Wakad` | `Public Safety` | Related-but-distinct safety complaint cluster |

Rows are additionally marked with:

- `is_duplicate` and `duplicate_of` for duplicate detection.
- `fraud_score`, `fraud_level`, `fraud_explanation` for risk scoring.
- `cluster_id` for incident grouping.
- `priority_score`, `priority_breakdown`, and `xai_explanation` for priority / XAI.

---

## 10.4 Fraud Alerts scenario

### Configuration

From `civic_sense/seed_data.py`:

```python
FRAUD_SCENARIO_COUNT = 7
FRAUD_SCENARIO_WARD = "Hinjewadi"
FRAUD_SCENARIO_START_HOURS_AGO = 1.25
_FRAUD_SPAM_TEMPLATES = [
    "Please fix this issue immediately",
    "Need urgent attention please",
    "Kindly look into this matter",
    "Immediate action required please",
    "Need help asap please",
    "Please attend to this ASAP",
    "Attention required urgently",
    "Please resolve this issue",
]
```

### Rationale

- Repeated near-identical text triggers the **semantic similarity** signal.
- One ward in a ~1.5-hour window triggers the **submission frequency / flood**
  signal.
- Short and generic text triggers the **pattern analysis** signal.

### Effect on the dashboard

- Rows with `fraud_level == "High"` appear in the Fraud Alerts card.
- A clean seed may produce `Medium` rows rather than `High` rows, depending on
  thresholds in `civic_sense/fraud_detector.py`:

```python
FREQ_THRESHOLD = 5
SIM_THRESHOLD = 0.85
```

---

## 10.5 Incident Hotspots scenario

### Configuration

From `civic_sense/seed_data.py`:

```python
HOTSPOT_SCENARIO_COUNT_WORDS = 8
HOTSPOT_SCENARIO_SPREAD_HOURS = 6
HOTSPOT_SCENARIO_WARD = "Wakad"
HOTSPOT_SCENARIO_CATEGORY = "Public Safety"
```

Templates are near-paraphrases of one incident:

- A tree fell on the road.
- A fallen branch blocked traffic.
- Debris from a fallen tree is on the road.
- The roadside tree lost a large branch.
- A tree near the location caused a road blockage.

### Purpose

- Keep the rows **distinct** so they are not treated as duplicates.
- Make the **Incident Hotspots** card show a representative cluster.
- Use `cluster_id` for grouping so the dashboard can show aggregate size.

---

## 10.6 Dashboard display mapping

### Fraud Alerts

Template logic in `templates/index.html`:

```jinja
{% set fraud_list = [] %}
{% for c in recent %}
  {% if c.fraud_level == 'High' %}
    {% set _ = fraud_list.append(c) %}
  {% endif %}
{% endfor %}
```

- Matches `fraud_level == "High"`.
- Shows ID, Title, Risk badge, and Fraud Score.

### Incident Hotspots

Template logic in `templates/index.html`:

```jinja
{% for c in recent %}
  {% if c.cluster_id %}
    {% set _ = clusters.append({'id': c.cluster_id, 'title': c.title, 'count': 1}) %}
  {% endif %}
{% endfor %}
```

- Matches `cluster_id` present on recent complaints.
- Groups rows by cluster ID and shows size.

---

## 10.7 Verification checklist

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

## 10.8 Intent and use in the report

For the Project Report, this section maps to:

- **Problem statement**: semantic duplicates, coordinated fraud/flooding, and
  triage opacity.
- **Methodology**: preprocessing, duplicate detection, classification, fraud
  scoring, incident clustering, weighted priority, and XAI.
- **Architecture**: app routes, `civic_sense` modules, database, and
  decision-support dashboard.
- **Demo/Implementation**: the two explicit synthetic scenarios above.
- **Limitations**: the clean seed may not generate `High` fraud rows; hotspot
  clustering depends on similarity availability; the data are synthetic and not
  production precision claims.
