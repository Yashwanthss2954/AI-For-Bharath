from __future__ import annotations

import re
from rapidfuzz import fuzz


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    v = value.lower().strip()
    v = re.sub(r"[^a-z0-9\s]", " ", v)
    v = re.sub(r"\b(private limited|pvt ltd|pvt\. ltd\.|ltd|llp)\b", " ", v)
    v = re.sub(r"\s+", " ", v).strip()
    return v


def normalize_pan(value: str | None) -> str:
    if not value:
        return ""
    v = value.strip().upper()
    return v if re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", v) else ""


def normalize_gstin(value: str | None) -> str:
    if not value:
        return ""
    v = value.strip().upper()
    return v if re.match(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$", v) else ""


def name_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return fuzz.token_set_ratio(a, b) / 100.0


def address_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return fuzz.partial_ratio(a, b) / 100.0
