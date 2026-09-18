import threading

from transformers import pipeline

from restaurant_bot.config import MODEL_NAME

_LABELS = ["ordering food at a restaurant", "something unrelated to ordering food"]

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
    result = _get_classifier()(text, _LABELS, multi_label=False)
    return result["labels"][0] == _LABELS[0]


def set_gate_enabled(enabled: bool) -> None:
    global _gate_enabled
    _gate_enabled = enabled


def is_gate_enabled() -> bool:
    return _gate_enabled
