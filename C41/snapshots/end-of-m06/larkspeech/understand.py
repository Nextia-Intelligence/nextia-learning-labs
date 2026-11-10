"""From transcript to decision: the call reason (rules, a classifier, a recorded LLM), the summary check and the
compliance check (the recording notice)."""
import difflib
import json
from pathlib import Path

from larkspeech.compare import normalise

REASONS = ["order_status", "return_refund", "damaged_item", "billing", "product_question", "account_change",
           "cancel_order"]

# Keyword rules: the first reason whose words appear in the caller's turns wins (in this order).
RULES = [
    ("cancel_order", ["cancel", "annuler", "annulation"]),
    ("billing", ["charged", "charge", "twice", "payment", "card", "bill", "débité", "paiement", "facture", "carte",
                 "deux fois"]),
    ("damaged_item", ["damaged", "broken", "cracked", "abîmé", "cassé", "brisé", "endommagé", "fissuré"]),
    ("return_refund", ["return", "refund", "money back", "send it back", "retourner", "rembours", "retour"]),
    ("account_change", ["address", "account", "email", "adresse", "compte", "courriel"]),
    ("order_status", ["where", "arrived", "delivery", "tracking", "track", "où", "arrivé", "livraison", "suivi"]),
    ("product_question", ["how", "set up", "setup", "question", "comment", "installer", "installation"]),
]


def rule_reason(caller_text, language="en"):
    t = " " + normalise(caller_text, "basic", language) + " "
    for reason, words in RULES:
        if any(f" {w}" in t for w in words):
            return reason
    return "product_question"


class ReasonClassifier:
    """TF-IDF of words and word pairs + logistic regression, trained on the train calls' transcripts."""

    def fit(self, texts, labels):
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        self.vec = TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)
        self.lr = LogisticRegression(max_iter=2000, C=10.0)
        self.lr.fit(self.vec.fit_transform([normalise(t, "basic") for t in texts]), labels)
        return self

    def predict(self, texts):
        return list(self.lr.predict(self.vec.transform([normalise(t, "basic") for t in texts])))


def load_llm(data, name):
    """Recorded LLM answers: recordings/llm/<name>.jsonl, one per call (`answer` is the parsed JSON)."""
    p = Path(data) / "recordings/llm" / f"{name}.jsonl"
    return {r["call_id"]: r for r in (json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x)}


NOTICE = {"en": "this call is recorded for quality and training",
          "fr": "cet appel est enregistré pour la qualité et la formation"}
NOTICE_WORDS = {"en": {"recorded", "quality", "training"}, "fr": {"enregistré", "enregistrés", "qualité", "formation"}}


def notice_exact(agent_text, language):
    return NOTICE[language] in normalise(agent_text, "basic", language)


def notice_fuzzy(agent_text, language, threshold=0.6):
    """True when a window of the agent's words is close to the notice (difflib ratio), or when the key words of
    the notice are all there in any order ("calls may be recorded for training and quality")."""
    words = normalise(agent_text, "basic", language).split()
    key = NOTICE_WORDS[language]
    if language == "en" and {"recorded", "quality", "training"} <= set(words):
        return True
    if language == "fr" and {"qualité", "formation"} <= set(words) and set(words) & {"enregistré", "enregistrés"}:
        return True
    n = len(NOTICE[language].split())
    target = NOTICE[language]
    best = max((difflib.SequenceMatcher(None, " ".join(words[i:i + n]), target).ratio()
                for i in range(max(1, len(words) - n + 1))), default=0)
    return best >= threshold and bool(set(words) & key)
