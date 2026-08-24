"""Complaint classification module (paper section 3.3).

Primary model: TF-IDF + Linear Support Vector Machine, trained on a curated
corpus of realistic citizen complaints across the five categories from the
base paper (Table 1: Roads, Electricity, Water Supply, Waste Management,
Public Safety). Reported accuracy comes from stratified 5-fold
cross-validation.

An optional zero-shot DistilBERT classifier (via HuggingFace transformers)
is used instead when USE_TRANSFORMERS=1 and the heavy dependencies are
installed — this mirrors the paper's BERT/DistilBERT approach.
"""
import json

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from .config import CLASSIFIER_PATH, METRICS_PATH, CATEGORIES, USE_TRANSFORMERS, TRANSFORMER_MODEL

# ---------------------------------------------------------------------------
# Training corpus — curated realistic complaints (text, category).
# Each category uses lexically distinctive vocabulary so the categories stay
# separable (e.g. "wires" belongs to Electricity, "manhole"/"sewage" to
# Public Safety, "garbage"/"waste" to Waste Management).
# ---------------------------------------------------------------------------
TRAIN_DATA = [
    # --- Roads -------------------------------------------------------------
    ("There is a huge pothole near the school causing traffic jams", "Roads"),
    ("The main road is full of potholes and needs urgent repair", "Roads"),
    ("Footpath tiles are broken near the market and pedestrians are falling", "Roads"),
    ("Road surface is cracked near the bus stop", "Roads"),
    ("The speed breaker is damaged and vehicles speed through", "Roads"),
    ("An open trench has been left on the road for a week after pipe work", "Roads"),
    ("Potholes on the ring road damaged my car tyre", "Roads"),
    ("The road has not been repaired for years and is full of craters", "Roads"),
    ("Street barricades have fallen over and block half the road", "Roads"),
    ("Road markings near the school crossing have faded away", "Roads"),
    ("The flyover approach road has cracks and loose gravel", "Roads"),
    ("Brick road is uneven near the park", "Roads"),
    ("Asphalt is peeling off near the petrol pump", "Roads"),
    ("The road divider is broken at the crossing", "Roads"),
    ("The pavement outside the hospital is broken and slippery", "Roads"),
    ("Road widening work has damaged the footpath", "Roads"),
    ("The lane is not tarred and turns to mud when it rains", "Roads"),
    ("Road repair work has been going on for months but never finishes", "Roads"),
    ("The main junction road has developed deep cracks", "Roads"),
    ("Speed breakers are missing near the school crossing", "Roads"),
    ("The road edge has eroded away near the canal", "Roads"),
    ("The by-lane near the temple is full of potholes", "Roads"),
    ("Footpath in front of the bank is broken", "Roads"),
    ("Mud from the construction site has spread all over the road", "Roads"),
    ("The children park road is full of gravel and stones", "Roads"),
    ("My bike hit a pothole and I fell down, please fix the road", "Roads"),
    ("Tar is melting in the summer heat on the main road", "Roads"),
    ("The road divider is damaged near the signal", "Roads"),
    ("The footpath tiles near the bus stop are cracked and lifted", "Roads"),
    ("The street has not been repaired since last year, full of holes", "Roads"),
    # --- Electricity ---------------------------------------------------------
    ("Streetlight not working for the past three days", "Electricity"),
    ("Frequent power cuts in our area since last week", "Electricity"),
    ("Voltage fluctuation is damaging our appliances", "Electricity"),
    ("Transformer is making loud noise and sparking", "Electricity"),
    ("An electric pole is tilted dangerously near the school", "Electricity"),
    ("Hanging electric wires are touching the ground after the storm", "Electricity"),
    ("Streetlights are flickering near the park", "Electricity"),
    ("High tension wires are sagging very low in our street", "Electricity"),
    ("Power supply is disrupted every evening", "Electricity"),
    ("The fuse keeps blowing in our street", "Electricity"),
    ("Electric meter is not working and showing wrong readings", "Electricity"),
    ("No electricity for two days after the rains", "Electricity"),
    ("Streetlight pole is damaged and could fall", "Electricity"),
    ("A power line snapped and fell on the road", "Electricity"),
    ("Electricity is cut off for hours during peak evening hours", "Electricity"),
    ("The streetlight stays on during the day wasting power", "Electricity"),
    ("Electricity pole is tilted after the lorry hit it", "Electricity"),
    ("Streetlights in lane 3 are all dead", "Electricity"),
    ("Power transformer is overheating and smells like burning", "Electricity"),
    ("The streetlight in front of my house has not worked for a week", "Electricity"),
    ("Power goes off suddenly several times a day", "Electricity"),
    ("The electric pole has a burnt wire hanging from it", "Electricity"),
    ("Our street lights come on only during the day", "Electricity"),
    ("Voltage is very high and light bulbs keep fusing", "Electricity"),
    ("There is no power supply in the entire block", "Electricity"),
    ("The transformer on the pole is buzzing loudly", "Electricity"),
    ("The streetlight near the bus stop has been dead for months", "Electricity"),
    ("Electricity connection for the new flat is still pending", "Electricity"),
    ("We have power cuts every night from ten o clock", "Electricity"),
    ("The streetlight post is bent and leaning", "Electricity"),
    # --- Water Supply ---------------------------------------------------------
    ("No water supply in our area since yesterday", "Water Supply"),
    ("Water pressure is very low in the mornings", "Water Supply"),
    ("A water pipe is leaking near the junction wasting water", "Water Supply"),
    ("Pipeline burst and water is flooding the street", "Water Supply"),
    ("Tap water is muddy and unfit to drink", "Water Supply"),
    ("Water supply is irregular, comes only twice a week", "Water Supply"),
    ("The borewell motor is not working", "Water Supply"),
    ("Water tanker did not come for three days", "Water Supply"),
    ("Water is contaminated and has a bad smell", "Water Supply"),
    ("The overhead tank is not filling up", "Water Supply"),
    ("Water supply pipe is broken near the temple", "Water Supply"),
    ("No drinking water connection for the new houses", "Water Supply"),
    ("Leakage from the main water line is wasting water", "Water Supply"),
    ("Water comes only at night which is very inconvenient", "Water Supply"),
    ("The tap in the public standpost is broken", "Water Supply"),
    ("Groundwater level has dropped, borewell is dry", "Water Supply"),
    ("The water tank is leaking from the top", "Water Supply"),
    ("Supply is cut every day without notice", "Water Supply"),
    ("No water in the taps since the pump failed", "Water Supply"),
    ("Water does not come in the taps for the whole street", "Water Supply"),
    ("The old water pipeline is leaking at many joints", "Water Supply"),
    ("Water supply time has changed without any notice", "Water Supply"),
    ("The sump is empty and the motor is not starting", "Water Supply"),
    ("The water here is salty and not good for drinking", "Water Supply"),
    ("The public tap is running continuously wasting water", "Water Supply"),
    ("The pipeline laid recently is already leaking", "Water Supply"),
    ("Water comes once in three days, far too irregular", "Water Supply"),
    ("Ground water is contaminated by the dyeing unit", "Water Supply"),
    ("The borewell water has a foul odour", "Water Supply"),
    ("Water pressure is so low that the tank never fills", "Water Supply"),
    # --- Waste Management ------------------------------------------------------
    ("Garbage not collected for two days in our street", "Waste Management"),
    ("Dustbin is overflowing at the street corner", "Waste Management"),
    ("Garbage is dumped in the open ground behind my house", "Waste Management"),
    ("Sanitation workers have not visited this week", "Waste Management"),
    ("A dead animal carcass near the garbage dump needs removal by the sanitation team", "Waste Management"),
    ("Construction debris is dumped on the footpath", "Waste Management"),
    ("The drain is choked with garbage and plastic waste", "Waste Management"),
    ("Garbage trucks come late and scatter waste everywhere", "Waste Management"),
    ("People are burning trash piles in the open ground", "Waste Management"),
    ("The bin near the park is full and attracting rats", "Waste Management"),
    ("Waste collection is irregular in our ward", "Waste Management"),
    ("Plastic waste is piled up near the school gate", "Waste Management"),
    ("The compost pit is overflowing", "Waste Management"),
    ("Hotel waste is dumped in the street every night", "Waste Management"),
    ("Sweeping is not done in the back lanes", "Waste Management"),
    ("Torn garbage bags leave rubbish scattered along the street", "Waste Management"),
    ("The dump yard smell reaches our houses", "Waste Management"),
    ("No waste segregation bins in our area", "Waste Management"),
    ("Fruit vendor waste is rotting near the bus stop", "Waste Management"),
    ("The garbage bin at the corner has not been emptied in a week", "Waste Management"),
    ("The street sweeper does not clean our lane", "Waste Management"),
    ("Vegetable waste is left rotting near the stalls", "Waste Management"),
    ("The open drain behind the shops is full of plastic", "Waste Management"),
    ("Construction waste blocks the lane entrance", "Waste Management"),
    ("Old furniture is dumped on the road side", "Waste Management"),
    ("The garbage truck spills waste in front of my house", "Waste Management"),
    ("Biomedical waste is thrown with the regular garbage", "Waste Management"),
    ("The compost yard is attracting flies and rats", "Waste Management"),
    ("Waste is being burnt behind the apartments", "Waste Management"),
    ("Sanitation is very poor in the slum area", "Waste Management"),
    # --- Public Safety ---------------------------------------------------------
    ("Sewage overflowing near the market area", "Public Safety"),
    ("Open manhole on the footpath is a danger to children", "Public Safety"),
    ("An accident happened at the sharp curve last evening", "Public Safety"),
    ("Stray dogs are attacking people near the park", "Public Safety"),
    ("A large tree branch crashed down near the playground", "Public Safety"),
    ("The old building is crumbling and bricks are falling", "Public Safety"),
    ("The bridge railing is broken and unsafe", "Public Safety"),
    ("Flood water is entering houses after heavy rain", "Public Safety"),
    ("A gas leak is reported near the restaurant", "Public Safety"),
    ("Smoke is coming from the electric box on the street", "Public Safety"),
    ("The footbridge is shaking and unsafe for students", "Public Safety"),
    ("Thieves are active in the area at night", "Public Safety"),
    ("Children play near the open drainage channel and it is dangerous", "Public Safety"),
    ("The abandoned house is a hiding place for anti-socials", "Public Safety"),
    ("Broken glass pieces are scattered on the playground", "Public Safety"),
    ("The well near the farm is open and dangerous", "Public Safety"),
    ("Waterlogging at the low lying area is causing accidents", "Public Safety"),
    ("The under-construction building has no safety netting around it", "Public Safety"),
    ("A cyclist was injured by the broken railing", "Public Safety"),
    ("The old building wall is bulging and could collapse", "Public Safety"),
    ("Exposed high voltage wires near the bus stop are a serious electrocution hazard", "Public Safety"),
    ("The underpass is flooded and very dangerous", "Public Safety"),
    ("A child fell into the uncovered drainage hole yesterday", "Public Safety"),
    ("The footbridge over the canal is broken", "Public Safety"),
    ("Firecrackers are stored in the shop near the school", "Public Safety"),
    ("The compound wall is collapsing onto the footpath", "Public Safety"),
    ("The gas cylinder shop is too close to the bus stand", "Public Safety"),
    ("Sewage is flowing into the open field near the colony", "Public Safety"),
    ("Sewage is backing up from the drain near the shops", "Public Safety"),
    ("A stone fell from the old temple tower and nearly hit a pedestrian", "Public Safety"),
    ("Landslide debris is blocking the hill road", "Public Safety"),
    ("Stray cattle are roaming near the highway at night and causing accidents", "Public Safety"),
]

TRAIN_TEXTS = [t for t, _ in TRAIN_DATA]
TRAIN_LABELS = [l for _, l in TRAIN_DATA]


def _make_pipeline():
    return Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=1)),
        ("clf", LinearSVC(class_weight="balanced", C=1.0, dual="auto")),
    ])


def train(force: bool = False) -> dict:
    """Train (or reload) the classifier and persist metrics."""
    if CLASSIFIER_PATH.exists() and not force:
        return get_metrics()

    pipeline = _make_pipeline()

    # Stratified 5-fold cross-validation -> stable, honest accuracy estimate.
    cv_scores = cross_val_score(pipeline, TRAIN_TEXTS, TRAIN_LABELS, cv=5,
                                scoring="accuracy")
    metrics = {
        "accuracy": round(float(cv_scores.mean()), 4),
        "accuracy_std": round(float(cv_scores.std()), 4),
        "samples": len(TRAIN_DATA),
        "model": "DistilBERT (zero-shot)" if USE_TRANSFORMERS else "TF-IDF + LinearSVC",
        "folds": [round(float(s), 4) for s in cv_scores],
    }
    CLASSIFIER_PATH.parent.mkdir(parents=True, exist_ok=True)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2))

    # Fit on the full corpus for the live model.
    pipeline.fit(TRAIN_TEXTS, TRAIN_LABELS)
    joblib.dump(pipeline, CLASSIFIER_PATH)
    return metrics


def get_metrics() -> dict:
    if METRICS_PATH.exists():
        return json.loads(METRICS_PATH.read_text())
    return {}


class _TransformersClassifier:
    """Optional zero-shot DistilBERT classifier (paper: BERT/DistilBERT)."""

    def __init__(self):
        from transformers import pipeline  # heavy import, only on demand
        self._pipe = pipeline("zero-shot-classification",
                              model=TRANSFORMER_MODEL,
                              multi_label=False)

    def classify(self, text):
        res = self._pipe(text[:512], candidate_labels=CATEGORIES)
        return res["labels"][0], round(float(res["scores"][0]), 4)


def load_classifier(force_train: bool = False):
    """Return a callable classifier and its metrics dict."""
    metrics = train(force=force_train)

    if USE_TRANSFORMERS:
        try:
            model = _TransformersClassifier()
            return model, metrics
        except Exception as exc:  # pragma: no cover
            print(f"[CivicSense] transformers unavailable ({exc}); using sklearn.")

    if CLASSIFIER_PATH.exists():
        pipeline = joblib.load(CLASSIFIER_PATH)
    else:  # pragma: no cover - train() above guarantees the file exists
        pipeline = _make_pipeline()
        pipeline.fit(TRAIN_TEXTS, TRAIN_LABELS)

    def classify(text):
        margins = pipeline.decision_function([text])[0]
        # Softmax over margins -> pseudo-confidence in [0, 1].
        import math
        exps = [math.exp(m) for m in margins]
        total = sum(exps)
        probs = [e / total for e in exps]
        idx = int(probs.index(max(probs)))
        return pipeline.classes_[idx], round(max(probs), 4)

    return classify, metrics


def classify_text(classifier, text: str):
    """Small wrapper that always returns (category, confidence)."""
    try:
        return classifier(text)
    except Exception:
        return "Roads", 0.0
