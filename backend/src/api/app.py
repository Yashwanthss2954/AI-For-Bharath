from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.ubid.pipeline import build_ubids, preprocess_master


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "output"
DECISIONS_FILE = OUT_DIR / "reviewer_decisions.csv"


class ReviewDecisionRequest(BaseModel):
    left_record_id: str = Field(min_length=1)
    right_record_id: str = Field(min_length=1)
    decision: Literal["merge", "reject"]
    reviewer: str = Field(min_length=1)
    notes: str = ""


def _pair_key(left_id: str, right_id: str) -> str:
    a, b = sorted([left_id, right_id])
    return f"{a}||{b}"


def _ensure_outputs_exist() -> None:
    required = [
        OUT_DIR / "scored_pairs.csv",
        OUT_DIR / "review_queue.csv",
        OUT_DIR / "ubid_registry.csv",
        OUT_DIR / "ubid_record_map.csv",
        OUT_DIR / "ubid_activity_status.csv",
        DATA_DIR / "master_records.csv",
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Pipeline outputs not found. Run python -m src.main first.",
                "missing": missing,
            },
        )


def _load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _get_effective_ubid_views() -> tuple[pd.DataFrame, pd.DataFrame]:
    reviewed_registry = OUT_DIR / "ubid_registry_reviewed.csv"
    reviewed_map = OUT_DIR / "ubid_record_map_reviewed.csv"
    if reviewed_registry.exists() and reviewed_map.exists():
        return pd.read_csv(reviewed_registry), pd.read_csv(reviewed_map)
    return pd.read_csv(OUT_DIR / "ubid_registry.csv"), pd.read_csv(OUT_DIR / "ubid_record_map.csv")


def _latest_decisions() -> pd.DataFrame:
    decisions = _load_csv(DECISIONS_FILE)
    if decisions.empty:
        return decisions

    decisions["pair_key"] = decisions.apply(lambda r: _pair_key(r["left_record_id"], r["right_record_id"]), axis=1)
    decisions = decisions.sort_values("decision_ts").drop_duplicates(subset=["pair_key"], keep="last")
    return decisions


def _recompute_reviewed_ubids() -> None:
    master = preprocess_master(pd.read_csv(DATA_DIR / "master_records.csv"))
    scored = pd.read_csv(OUT_DIR / "scored_pairs.csv")
    decisions = _latest_decisions()

    base_auto = scored[scored["decision"] == "auto_link"].copy()
    base_auto["pair_key"] = base_auto.apply(lambda r: _pair_key(r["left_record_id"], r["right_record_id"]), axis=1)

    if not decisions.empty:
        rejects = decisions[decisions["decision"] == "reject"]["pair_key"].tolist()
        base_auto = base_auto[~base_auto["pair_key"].isin(rejects)].copy()

        merges = decisions[decisions["decision"] == "merge"].copy()
        if not merges.empty:
            merge_rows = pd.DataFrame(
                {
                    "left_record_id": merges["left_record_id"],
                    "right_record_id": merges["right_record_id"],
                    "score": 1.0,
                    "decision": "auto_link",
                    "why": "manual_review_merge",
                    "pair_key": merges["pair_key"],
                }
            )
            base_auto = pd.concat([base_auto, merge_rows], ignore_index=True)
            base_auto = base_auto.drop_duplicates(subset=["pair_key"], keep="last")

    ubid_registry, ubid_map = build_ubids(master, base_auto.drop(columns=["pair_key"], errors="ignore"))
    ubid_registry.to_csv(OUT_DIR / "ubid_registry_reviewed.csv", index=False)
    ubid_map.to_csv(OUT_DIR / "ubid_record_map_reviewed.csv", index=False)


app = FastAPI(title="UBID Hackathon API", version="0.1.0")

# Configure CORS for production deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://*.onrender.com",  # Allow all Render static sites
    ],
    allow_origin_regex=r"https://.*\.onrender\.com",  # Regex pattern for Render domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "timestamp_utc": datetime.now(timezone.utc).isoformat()}


@app.get("/review/queue")
def get_review_queue(limit: int = Query(default=50, ge=1, le=500)) -> dict:
    _ensure_outputs_exist()
    queue = pd.read_csv(OUT_DIR / "review_queue.csv")
    decisions = _latest_decisions()

    if not queue.empty:
        queue["pair_key"] = queue.apply(lambda r: _pair_key(r["left_record_id"], r["right_record_id"]), axis=1)

    if not decisions.empty and not queue.empty:
        queue = queue[~queue["pair_key"].isin(decisions["pair_key"])].copy()

    queue = queue.drop(columns=["pair_key"], errors="ignore").head(limit)
    return {"count": int(len(queue)), "items": queue.to_dict(orient="records")}


@app.post("/review/decision")
def submit_review_decision(payload: ReviewDecisionRequest) -> dict:
    _ensure_outputs_exist()

    scored = pd.read_csv(OUT_DIR / "scored_pairs.csv")
    if scored.empty:
        raise HTTPException(status_code=400, detail="No scored pairs found.")

    key = _pair_key(payload.left_record_id, payload.right_record_id)
    scored["pair_key"] = scored.apply(lambda r: _pair_key(r["left_record_id"], r["right_record_id"]), axis=1)

    if key not in set(scored["pair_key"]):
        raise HTTPException(status_code=404, detail="Pair not found in scored pairs.")

    decisions = _load_csv(DECISIONS_FILE)
    new_row = pd.DataFrame(
        [
            {
                "left_record_id": payload.left_record_id,
                "right_record_id": payload.right_record_id,
                "decision": payload.decision,
                "reviewer": payload.reviewer,
                "notes": payload.notes,
                "decision_ts": datetime.now(timezone.utc).isoformat(),
            }
        ]
    )
    decisions = pd.concat([decisions, new_row], ignore_index=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    decisions.to_csv(DECISIONS_FILE, index=False)

    _recompute_reviewed_ubids()
    return {"message": "Decision recorded and UBIDs recomputed.", "pair_key": key}


@app.get("/ubids/search")
def search_ubids(
    ubid: Optional[str] = None,
    pan: Optional[str] = None,
    gstin: Optional[str] = None,
    name: Optional[str] = None,
    pincode: Optional[str] = None,
    source_record_id: Optional[str] = None,
) -> dict:
    _ensure_outputs_exist()
    ubid_registry, ubid_map = _get_effective_ubid_views()
    master = pd.read_csv(DATA_DIR / "master_records.csv")

    df = ubid_registry.copy()

    if ubid:
        df = df[df["ubid"].str.contains(ubid, case=False, na=False)]
    if pan:
        df = df[df["anchor_pan"].str.contains(pan, case=False, na=False)]
    if gstin:
        df = df[df["anchor_gstin"].str.contains(gstin, case=False, na=False)]
    if name:
        df = df[df["business_name"].str.contains(name, case=False, na=False)]
    if pincode:
        df = df[df["pincode"].astype(str) == str(pincode)]

    if source_record_id:
        rows = ubid_map[ubid_map["record_id"].astype(str) == str(source_record_id)]
        allowed = set(rows["ubid"].tolist())
        df = df[df["ubid"].isin(allowed)]

    status = _load_csv(OUT_DIR / "ubid_activity_status.csv")
    if not status.empty:
        df = df.merge(status, on="ubid", how="left")

    # Include source mappings for each UBID in response.
    master_cols = ["record_id", "business_name", "pincode", "pan", "gstin"]
    master_view = master[master_cols].copy()
    merged = ubid_map.merge(master_view, on="record_id", how="left")
    mapping_by_ubid = (
        merged.groupby("ubid")
        .apply(lambda g: g[["record_id", "business_name", "pincode", "pan", "gstin"]].to_dict(orient="records"))
        .to_dict()
    )

    items = []
    for _, row in df.iterrows():
        item = row.to_dict()
        item["source_records"] = mapping_by_ubid.get(row["ubid"], [])
        items.append(item)

    return {"count": len(items), "items": items}


@app.get("/ubids/{ubid}")
def get_ubid(ubid: str) -> dict:
    payload = search_ubids(ubid=ubid)
    if payload["count"] == 0:
        raise HTTPException(status_code=404, detail="UBID not found")
    return payload["items"][0]


@app.get("/activity/status")
def get_activity_status(status: Optional[Literal["Active", "Dormant", "Closed"]] = None) -> dict:
    _ensure_outputs_exist()
    df = _load_csv(OUT_DIR / "ubid_activity_status.csv")
    if df.empty:
        return {"count": 0, "items": []}

    if status:
        df = df[df["status"] == status]

    return {"count": int(len(df)), "items": df.to_dict(orient="records")}
