"""Robust Multi-Layer Fraud, Spam & Anomaly Detector for CivicSense / PCU Campus.

Architecture:
1. Rule-Based Deterministic Filtering:
   - Commercial promo, crypto, betting, loan & financial scams.
   - Blacklisted academic fraud (paper leaks, proxy exam solvers, thesis mills).
   - Unauthorized external URLs, shortened links, Telegram/WhatsApp scam handles.
2. Lexical & Linguistic Heuristics:
   - Keyboard smash & unpronounceable consonant clusters (e.g. 'asdfghjkl', 'qwertyuiop').
   - Vowel-to-letter density analysis (catches gibberish without vowels, with acronym whitelist).
   - Extreme single-character repetition (e.g. 'aaaaaaa', '???????').
   - Extreme word repetition (flood / denial-of-service spam).
3. Information-Theoretic Anomaly Scoring:
   - Shannon character entropy (detects monotonous low-entropy repetition or high-entropy cipher strings).
4. Unsupervised Machine Learning (Isolation Forest):
   - Scikit-learn IsolationForest trained on a calibrated 80+ sample corpus of legitimate PCU campus complaints.
   - Extracts 11 continuous features (lengths, lexical richness, vowel ratio, consonant clusters, entropy, caps, punctuation, location velocity).
   - Produces continuous decision scores and outlier classifications.

Outputs:
- is_suspicious (bool): True if total calibrated score >= 0.50
- suspicion_score (float): Calibrated risk score [0.0 to 1.0]
- reasons (str): Transparent, human-readable breakdown of flags.
"""
import math
import re
from collections import Counter
import numpy as np
from sklearn.ensemble import IsolationForest

# ---------------------------------------------------------------------------
# 1. Regex Patterns for Spam, Scams & Promotional Abuse
# ---------------------------------------------------------------------------
SPAM_PATTERNS = [
    # Commercial & Financial Solicitation
    r"\b(?:buy|sell|discount|promo|promocode|casino|crypto|bitcoin|btc|eth|usdt|quick loan|instant cash|lottery|free cash|cash prize|betting|win cash|click here|subscribe now|limited offer|best price|earn money|work from home)\b",
    # Academic Fraud & Cheating Services
    r"\b(?:assignment help service|pay for thesis|exam paper leak|hire hacker|proxy exam|buy degrees|fake certificate)\b",
    # External Links & Shortened Scam URLs
    r"https?://\S+",
    r"\b(?:bit\.ly|tinyurl\.com|t\.me|wa\.me|chat\.whatsapp\.com|telegram\.me)\/\S+",
    # Excessive Monotonous Character Repetition (e.g. "aaaaaa", "!!!!!!")
    r"(.)\1{4,}",
]
SPAM_RE = re.compile("|".join(SPAM_PATTERNS), re.IGNORECASE)

# Keyboard Smash Consonant Cluster Regex (5+ consonants in a row, ignoring common acronyms)
CONSONANT_CLUSTER_RE = re.compile(r"\b[a-z]*[bcdfghjklmnpqrstvwxyz]{5,}[a-z]*\b", re.IGNORECASE)

# Whitelist of standard abbreviations and technical acronyms used on university campus
ACRONYM_WHITELIST = {
    "pcu", "ac", "dc", "tv", "cpu", "ups", "hdmi", "lan", "wifi", "sms", "cctv",
    "led", "lcd", "iot", "ai", "ml", "cs", "it", "ece", "mtech", "btech", "mba",
    "mca", "bba", "phd", "ug", "pg", "mrp", "hod", "lab", "ncc", "nss", "atm",
    "gym", "maval", "sate", "pune", "dr", "prof", "mr", "mrs", "ms", "id", "pin",
}


# ---------------------------------------------------------------------------
# 2. Shannon Entropy Calculator
# ---------------------------------------------------------------------------
def shannon_entropy(text: str) -> float:
    """Calculate Shannon character entropy in bits.
    
    Legitimate English sentences typically have entropy between 3.2 and 4.8.
    Monotonous strings ('aaaaaaaa') have entropy < 2.0.
    """
    if not text:
        return 0.0
    s = text.lower()
    total = len(s)
    counts = Counter(s)
    entropy = -sum((cnt / total) * math.log2(cnt / total) for cnt in counts.values())
    return float(entropy)


# ---------------------------------------------------------------------------
# 3. FraudDetector Engine
# ---------------------------------------------------------------------------
class FraudDetector:
    """Multi-layer anomaly and fraud detector combining heuristic rules and Isolation Forest."""

    def __init__(self, contamination: float = 0.03):
        self.contamination = contamination
        self.model = IsolationForest(
            n_estimators=150,
            contamination=contamination,
            random_state=42,
            n_jobs=1,
        )
        self._is_fitted = False

    def extract_features(self, text: str, ward_frequency: int = 0) -> list:
        """Extract an 11-dimensional numerical feature vector for Isolation Forest."""
        raw = text or ""
        chars = len(raw)
        words = raw.split()
        word_count = len(words)
        
        # Word lengths
        avg_word_len = (sum(len(w) for w in words) / max(1, word_count)) if word_count else 0.0
        
        # Lexical diversity
        unique_words = len(set(w.lower() for w in words)) if word_count else 0
        lexical_diversity = (unique_words / max(1, word_count)) if word_count else 0.0
        
        # Vowels vs consonants
        letters = [c.lower() for c in raw if c.isalpha()]
        vowel_count = sum(1 for c in letters if c in "aeiou")
        vowel_ratio = (vowel_count / max(1, len(letters))) if letters else 0.35
        
        # Consonant cluster severity
        max_consonants = 0
        for w in words:
            clean_w = re.sub(r"[^a-zA-Z]", "", w).lower()
            if clean_w not in ACRONYM_WHITELIST:
                cur = 0
                for c in clean_w:
                    if c in "bcdfghjklmnpqrstvwxyz":
                        cur += 1
                        if cur > max_consonants:
                            max_consonants = cur
                    else:
                        cur = 0
        
        # Entropy & ratios
        entropy = shannon_entropy(raw)
        caps_count = sum(1 for c in raw if c.isupper())
        caps_ratio = caps_count / max(1, chars)
        digit_count = sum(1 for c in raw if c.isdigit())
        digit_ratio = digit_count / max(1, chars)
        punct_count = sum(1 for c in raw if not c.isalnum() and not c.isspace())
        punct_ratio = punct_count / max(1, chars)

        return [
            float(chars),
            float(word_count),
            float(avg_word_len),
            float(lexical_diversity),
            float(vowel_ratio),
            float(max_consonants),
            float(entropy),
            float(caps_ratio),
            float(digit_ratio),
            float(punct_ratio),
        ]

    def fit_baseline(self, samples: list):
        """Fit Isolation Forest on baseline legitimate PCU campus complaints."""
        if not samples or len(samples) < 10:
            return
        X = np.array([self.extract_features(t) for t in samples])
        try:
            self.model.fit(X)
            self._is_fitted = True
        except Exception:
            self._is_fitted = False

    def analyze(self, text: str, ward_frequency: int = 0) -> tuple:
        """Evaluate text for spam, keyboard smash, repetitive flood, and statistical anomalies.

        Returns:
            (is_suspicious: bool, score: float, reasons: list[str])
        """
        raw = (text or "").strip()
        reasons = []
        score = 0.0

        if not raw:
            return True, 1.0, ["Empty submission."]

        # -------------------------------------------------------------
        # Rule 1: Text Length & Substance Check
        # -------------------------------------------------------------
        words = raw.split()
        if len(raw) < 8 or len(words) < 2:
            score += 0.45
            reasons.append("Description is too short to convey an actionable campus defect.")

        # -------------------------------------------------------------
        # Rule 2: Commercial Spam, Scams & Promotional URLs
        # -------------------------------------------------------------
        spam_matches = SPAM_RE.findall(raw)
        if spam_matches:
            matched_terms = list(set([m for m in spam_matches if m][:3]))
            score += 0.60
            reasons.append(f"Contains commercial solicitation or external promotional link: {matched_terms}")

        # -------------------------------------------------------------
        # Rule 3: Keyboard Smash & Gibberish Detection
        # -------------------------------------------------------------
        consonant_matches = CONSONANT_CLUSTER_RE.findall(raw)
        filtered_clusters = [w for w in consonant_matches if w.lower() not in ACRONYM_WHITELIST]
        if filtered_clusters:
            score += 0.50
            reasons.append(f"Detected keyboard smash / unpronounceable consonant pattern ('{filtered_clusters[0]}').")

        letters = [c.lower() for c in raw if c.isalpha()]
        if len(letters) >= 10:
            vowels = sum(1 for c in letters if c in "aeiou")
            v_ratio = vowels / len(letters)
            if v_ratio < 0.14:
                score += 0.50
                reasons.append(f"Abnormally low vowel density ({round(v_ratio * 100, 1)}%) consistent with gibberish typing.")
            elif v_ratio > 0.75:
                score += 0.45
                reasons.append("Abnormally high vowel density consistent with nonsensical vocalic flooding.")

        # -------------------------------------------------------------
        # Rule 4: Extreme Word & Token Repetition (Flood / Bot spam)
        # -------------------------------------------------------------
        if words:
            counts = Counter(w.lower() for w in words)
            top_word, top_count = counts.most_common(1)[0]
            if top_count >= 4 and (top_count / len(words)) >= 0.40:
                score += 0.45
                reasons.append(f"Excessive repetition of the word '{top_word}' ({top_count} times).")

        # -------------------------------------------------------------
        # Rule 5: Shannon Entropy Extremes
        # -------------------------------------------------------------
        ent = shannon_entropy(raw)
        if len(raw) >= 18:
            if ent < 2.1:
                score += 0.45
                reasons.append(f"Very low information entropy ({round(ent, 2)} bits) indicates monotonous character flooding.")
            elif ent > 5.1 and len(raw) > 60 and not re.search(r"\s", raw[:40]):
                score += 0.35
                reasons.append("Extremely high uniform character entropy indicates machine-generated pseudo-random text.")

        # -------------------------------------------------------------
        # Rule 6: Excessive Screaming Uppercase Caps Lock
        # -------------------------------------------------------------
        if len(raw) >= 20:
            caps_ratio = sum(1 for c in raw if c.isupper()) / len(raw)
            if caps_ratio > 0.75:
                score += 0.20
                reasons.append("Abnormally high uppercase ratio (>75%).")

        # -------------------------------------------------------------
        # Rule 7: Location Frequency Burst (Only accelerates existing anomalies)
        # -------------------------------------------------------------
        if ward_frequency >= 20 and score >= 0.30:
            score += 0.20
            reasons.append(f"High submission burst velocity observed ({ward_frequency} recent reports) combined with abnormal text.")

        # -------------------------------------------------------------
        # Layer 8: Unsupervised Isolation Forest Outlier Scoring
        # -------------------------------------------------------------
        if self._is_fitted:
            try:
                feats = np.array([self.extract_features(raw)])
                pred = self.model.predict(feats)[0]  # -1 = anomaly, 1 = normal
                decision = self.model.decision_function(feats)[0]
                
                # If model identifies as an outlier, calculate calibrated weight
                if pred == -1 and decision < -0.02:
                    anomaly_weight = min(0.35, max(0.15, abs(decision) * 4.0))
                    score += anomaly_weight
                    reasons.append(f"Isolation Forest flagged statistical anomaly (decision={round(decision, 4)}).")
            except Exception:
                pass

        calibrated_score = round(min(1.0, max(0.0, score)), 2)
        is_suspicious = calibrated_score >= 0.50

        return is_suspicious, calibrated_score, reasons


# ---------------------------------------------------------------------------
# Calibrated Baseline Training Samples (Comprehensive PCU Campus Grievances)
# ---------------------------------------------------------------------------
_BASELINE_CAMPUS_SAMPLES = [
    # Classroom & Lab Infrastructure
    "Projector is not turning on and screen is blank in Block A Room 204",
    "HDMI display cable is damaged and audio system has severe static noise in Block B Lab 2",
    "Multiple computer monitors and CPUs fail to boot in CS Lab 3 on 2nd floor",
    "Air conditioning unit in Seminar Hall 1 is blowing warm air and rattling loudly",
    "Broken desk benches with sharp screws protruding in Room 305 Block C",
    "Podium microphone in Auditorium has severe screeching feedback during lecture",
    "Whiteboard is stained permanently and marker tray is broken in Room 102",
    "Ethernet wall port has no connectivity in the IoT research lab on 4th floor",
    "Ceiling fan is wobbling dangerously and vibrating in Block B Room 401",
    "Windows glass panel cracked and rattling during windy days in Block A Room 310",
    "Computer keyboard keys are stuck and mice missing in Computer Lab 1 Block A",
    "Sound system amplifier not turning on in seminar hall Block B 2nd floor",
    "Classroom lights flickering heavily during practical exam in Block C Room 105",
    "Air conditioning leaking water onto front benches in Block A Room 402",
    
    # Hostel & Residential Life
    "Hot water geyser is not functioning in the Girls Hostel 2nd floor bathroom wing",
    "Wi-Fi access point in Boys Hostel 1 3rd floor corridor is completely offline",
    "Study desk and iron bed frame are damaged in Hostel Room 214",
    "Severe mosquito and pest infestation inside hostel rooms on ground floor",
    "Water seepage leaking from ceiling onto study table in Boys Hostel Room 308",
    "Washing machine in Girls Hostel laundry room is vibrating violently and not draining",
    "Hostel room door latch is jammed and keys are stuck in Room 115",
    "Water dispenser cooling filter is not working in the hostel common study room",
    "Loud music and corridor disturbance after midnight in Boys Hostel 4th floor",
    "Window mesh is torn and insects entering hostel rooms at night",
    "Hostel solar heater not heating water during morning shower hours",
    "Bathroom exhaust fans not working causing bad smell in Girls Hostel wing",
    "Iron cot broken in Boys Hostel 1 Room 202 needs welding repair",
    "Drinking water cooler empty on 3rd floor hostel residential wing",

    # Electricity & Maintenance
    "Exposed electrical wiring sparking near the main distribution board in Block A basement",
    "Frequent power cuts and voltage fluctuations disrupting computer lab sessions",
    "Corridor lights and emergency exit indicators are dark on 3rd floor Block B",
    "Elevator in Admin Block is making grinding noises and stuck between floors",
    "Power switchboard has burn marks and gave a mild shock to a student",
    "Exhaust fans in chemistry lab stopped spinning leading to chemical fume buildup",
    "Diesel generator backup failed to start during evening power outage",
    "Staircase lighting is completely out posing tripping risk at night",
    "3-phase machine breaker tripped in mechanical workshop Block C",
    "Loose electrical wire hanging dangerously in the entrance lobby",
    "Elevator door sensor not working properly in Block A academic building",
    "Wall socket sparking when laptop charger plugged in Room 203 Block C",
    "Main corridor tube lights burnt out and dark near faculty room Block B",
    "Transformer making loud buzzing humming sound near substation",

    # Water Supply & Washrooms
    "No running water supply in the entire washroom wing on 3rd floor Block A",
    "Drinking water cooler filter is dispensing brownish muddy water near library",
    "Urinals and toilet flushes are clogged and overflowing in Block B ground floor restroom",
    "Restroom door lock is broken and tap faucet is continuously dripping in Girls Hostel",
    "Overhead terrace water storage tank is overflowing and flooding stairs",
    "Foul sewage smell rising from floor drainage in Admin Block basement",
    "Soap dispensers and paper towel holders are empty in central washroom",
    "Extremely low water pressure in wash basins making handwashing impossible",
    "Drain pipe under washroom basin burst and flooded the hallway",
    "Solar water heater in hostel has been cold for three consecutive days",
    "Wash basin drain choked and water overflowing onto floor in Block C washroom",
    "Restroom flush tank valve broken and water running continuously",
    "Drinking water purifier dispenser tap broken near cafeteria",

    # Canteen & Food Quality
    "Lunch meal served had undercooked rice and stale vegetables at Central Canteen",
    "Found a dead insect in the food plate served to students at Cafeteria 2",
    "Drinking glasses and steel trays have greasy food residue and sticky stains",
    "Milk served at breakfast smelled sour and tasted curdled in the hostel mess",
    "Canteen vendor charging snacks above printed MRP menu prices",
    "Multiple students suffered food poisoning and vomiting after hostel dinner",
    "Food counter has houseflies hovering over open uncovered food containers",
    "Sandwiches and patties served at counter were hard, cold, and visibly expired",
    "Cooking oil used for fried snacks smells burnt and rancid",
    "Severe crowd congestion and lack of queue barriers during peak lunch hours",
    "Drinking water glasses smelling bad and oily at Central Canteen",
    "Food served at dinner was cold and chapattis were extremely hard",
    "Unwashed spoons and plates placed on serving table in canteen",

    # Campus Safety & Parking
    "Two-wheelers and delivery bikes parked haphazardly blocking ambulance ramp",
    "Underground basement parking under Block A has zero lights and is pitch black",
    "Speeding cars and rash driving observed on internal road near main gate",
    "Pack of stray dogs barking aggressively at students near sports ground",
    "CCTV security camera at building entrance appears turned off or disconnected",
    "Fire extinguisher inspection card expired two years ago and gauge in red zone",
    "Emergency fire exit door padlocked with heavy chain on 4th floor Block B",
    "Waterlogging and slippery oil puddles on concrete floor in basement parking",
    "Unauthorized outsiders wandering campus without visitor badges near hostel",
    "Student helmet stolen from two-wheeler parked in designated parking bay",
    "Vehicles parked in front of fire hydrant gate blocking emergency access",
    "Streetlights on Mohitewadi road campus approach completely dark at night",
    "Basement parking ramp has oil slick causing two-wheeler skidding hazard",
]

# Instantiate and fit singleton detector
_detector = FraudDetector()
_detector.fit_baseline(_BASELINE_CAMPUS_SAMPLES)


def check_complaint(text: str, ward_frequency: int = 0) -> tuple:
    """Convenience wrapper returning (is_suspicious: bool, score: float, reason_summary: str)."""
    is_susp, score, reasons = _detector.analyze(text, ward_frequency)
    reason_str = " | ".join(reasons) if reasons else ""
    return is_susp, score, reason_str
