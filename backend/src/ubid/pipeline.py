from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import List, Tuple

import networkx as nx
import pandas as pd

from .utils import (
    address_similarity,
    name_similarity,
    normalize_gstin,
    normalize_pan,
    normalize_text,
)


@dataclass
class Thresholds:
    auto_link: float = 0.92
    review_low: float = 0.70


def preprocess_master(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["name_norm"] = out["business_name"].fillna("").map(normalize_text)
    out["addr_norm"] = out["address"].fillna("").map(normalize_text)
    out["pan_norm"] = out["pan"].fillna("").map(normalize_pan)
    out["gstin_norm"] = out["gstin"].fillna("").map(normalize_gstin)
    out["pincode"] = out["pincode"].astype(str)
    return out


def _same_non_empty(a: str, b: str) -> bool:
    return bool(a) and bool(b) and a == b


def score_pair(a: pd.Series, b: pd.Series) -> float:
    pan_match = 1.0 if _same_non_empty(a["pan_norm"], b["pan_norm"]) else 0.0
    gst_match = 1.0 if _same_non_empty(a["gstin_norm"], b["gstin_norm"]) else 0.0
    pin_match = 1.0 if str(a["pincode"]) == str(b["pincode"]) else 0.0
    nm = name_similarity(a["name_norm"], b["name_norm"])
    ad = address_similarity(a["addr_norm"], b["addr_norm"])

    if pan_match or gst_match:
        # Strong ID-based evidence can auto-link when supported by location/text.
        score = 0.55 * max(pan_match, gst_match) + 0.10 * pin_match + 0.20 * nm + 0.15 * ad
    else:
        # No reliable ID: rely on fuzzy evidence and route uncertain cases to review.
        score = 0.25 * pin_match + 0.45 * nm + 0.30 * ad
    return min(1.0, max(0.0, score))


def candidate_pairs(df: pd.DataFrame) -> List[Tuple[int, int]]:
    id_to_idx = {rid: i for i, rid in enumerate(df["record_id"].tolist())}
    pairs = set()

    # Multi-key blocking for hackathon speed and acceptable recall.
    for _, grp in df.groupby("pincode"):
        ids = grp["record_id"].tolist()
        for x, y in combinations(ids, 2):
            pairs.add(tuple(sorted((x, y))))

    for key_col in ["pan_norm", "gstin_norm"]:
        nz = df[df[key_col] != ""]
        for _, grp in nz.groupby(key_col):
            ids = grp["record_id"].tolist()
            for x, y in combinations(ids, 2):
                pairs.add(tuple(sorted((x, y))))

    return [(id_to_idx[x], id_to_idx[y]) for x, y in sorted(pairs)]


def link_records(df: pd.DataFrame, thresholds: Thresholds) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for i, j in candidate_pairs(df):
        a = df.iloc[i]
        b = df.iloc[j]
        score = score_pair(a, b)
        if score >= thresholds.auto_link:
            decision = "auto_link"
        elif score >= thresholds.review_low:
            decision = "review"
        else:
            decision = "no_link"
        rows.append(
            {
                "left_record_id": a["record_id"],
                "right_record_id": b["record_id"],
                "score": round(score, 4),
                "decision": decision,
                "why": f"name={name_similarity(a['name_norm'], b['name_norm']):.2f}, addr={address_similarity(a['addr_norm'], b['addr_norm']):.2f}, pan={int(_same_non_empty(a['pan_norm'], b['pan_norm']))}, gst={int(_same_non_empty(a['gstin_norm'], b['gstin_norm']))}",
            }
        )

    scored = pd.DataFrame(rows)
    review = scored[scored["decision"] == "review"].copy() if not scored.empty else pd.DataFrame()
    return scored, review


def build_ubids(df: pd.DataFrame, scored_pairs: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    g = nx.Graph()
    g.add_nodes_from(df["record_id"].tolist())

    if not scored_pairs.empty:
        for _, row in scored_pairs[scored_pairs["decision"] == "auto_link"].iterrows():
            g.add_edge(row["left_record_id"], row["right_record_id"])

    components = list(nx.connected_components(g))
    ubid_rows = []
    map_rows = []

    for idx, comp in enumerate(components, start=1):
        comp_ids = sorted(comp)
        sub = df[df["record_id"].isin(comp_ids)]

        anchor_pan = next((p for p in sub["pan_norm"].tolist() if p), "")
        anchor_gst = next((g for g in sub["gstin_norm"].tolist() if g), "")

        ubid = f"UBID-{idx:06d}"
        business_name = sub.iloc[0]["business_name"]
        pincode = sub.iloc[0]["pincode"]

        ubid_rows.append(
            {
                "ubid": ubid,
                "business_name": business_name,
                "anchor_pan": anchor_pan,
                "anchor_gstin": anchor_gst,
                "pincode": pincode,
            }
        )

        for rid in comp_ids:
            map_rows.append({"ubid": ubid, "record_id": rid})

    return pd.DataFrame(ubid_rows), pd.DataFrame(map_rows)
