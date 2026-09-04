from __future__ import annotations

from typing import Any

from .preflight_validate import validate_preflight
from .hardware_validate import validate_hardware

def validate_record(record: dict[str, Any], level: str = "phase0") -> list[str]:
    if level not in {"preflight", "hardware", "phase0"}:
        raise ValueError(f"unknown validation level: {level}")
    errors = validate_preflight(record)
    if level == "preflight":
        return errors
    validate_hardware(record, errors)
    if level == "hardware":
        return errors
    review = record.get("review", {})
    if review.get("critical_unresolved") != 0:
        errors.append("independent review has unresolved Critical findings or is missing")
    if review.get("important_unresolved") != 0:
        errors.append("independent review has unresolved Important findings or is missing")
    if not review.get("reviewer") or not review.get("date"):
        errors.append("independent reviewer/date are missing")
    return errors
