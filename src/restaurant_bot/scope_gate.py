import threading

from transformers import pipeline

from restaurant_bot.config import MODEL_NAME

_LABELS = ["a restaurant, food, or ordering topic", "a topic unrelated to a restaurant or menu"]

_classifier = None
_classifier_lock = threading.Lock()
_gate_enabled = True


def _get_classifier():
    global _classifier
    if _classifier is None:
        with _classifier_lock:
            if _classifier is None:
                _classifier = pipeline("zero-shot-classification", model=MODEL_NAME)
    return _classifier


def is_in_scope(text: str) -> bool:
    #Muli_label=false means the scores are normalized to sum to 1. If 'true', the scores are independent and can sum to more than 1.
    result = _get_classifier()(
        text, _LABELS, multi_label=False, hypothesis_template="This text is about {}."
    )
    print(f"Text: {text} | Scores: {result['scores']}")
    return result["labels"][0] == _LABELS[0]


def set_gate_enabled(enabled: bool) -> None:
    global _gate_enabled
    _gate_enabled = enabled


def is_gate_enabled() -> bool:
    return _gate_enabled
