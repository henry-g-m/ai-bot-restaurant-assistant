_gate_enabled = True


def set_gate_enabled(enabled: bool) -> None:
    global _gate_enabled
    _gate_enabled = enabled


def is_gate_enabled() -> bool:
    return _gate_enabled
