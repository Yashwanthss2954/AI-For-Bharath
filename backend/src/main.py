from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.ubid.activity import classify_status, map_events_to_ubid
from src.ubid.pipeline import Thresholds, build_ubids, link_records, preprocess_master


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "output"


def ensure_sample_data() -> None:
    DATA.mkdir(parents=True, exist_ok=True)

    master_file = DATA / "master_records.csv"
    events_file = DATA / "events.csv"

    if not master_file.exists():
        pd.DataFrame(
            [
                {"record_id": "SHP-1", "business_name": "ABC Engineering Pvt Ltd", "address": "Peenya Indl Area Phase 2", "pincode": "560058", "pan": "ABCDE1234F", "gstin": "29ABCDE1234F1Z5"},
                {"record_id": "FAC-9", "business_name": "A B C Engineering Private Limited", "address": "Peenya Industrial Area II", "pincode": "560058", "pan": "ABCDE1234F", "gstin": ""},
                {"record_id": "LAB-4", "business_name": "Shakti Foods", "address": "Yeshwanthpur Main Road", "pincode": "560022", "pan": "AAACX1111L", "gstin": "29AAACX1111L1Z2"},
                {"record_id": "KSP-7", "business_name": "Shakthi Foods", "address": "Yeshwanthpur Rd", "pincode": "560022", "pan": "", "gstin": "29AAACX1111L1Z2"},
                {"record_id": "LAB-8", "business_name": "ABC Engg Works", "address": "Peenya Phase II", "pincode": "560058", "pan": "", "gstin": ""},
                {"record_id": "SHP-3", "business_name": "Nova Metals", "address": "Bommasandra", "pincode": "560099", "pan": "AABCN2222K", "gstin": ""},
            ]
        ).to_csv(master_file, index=False)

    if not events_file.exists():
        pd.DataFrame(
            [
                {"event_id": "E1", "record_id": "SHP-1", "event_type": "inspection", "event_ts": "2026-03-01"},
                {"event_id": "E2", "record_id": "FAC-9", "event_type": "filing", "event_ts": "2026-01-15"},
                {"event_id": "E3", "record_id": "LAB-4", "event_type": "renewal", "event_ts": "2025-11-20"},
                {"event_id": "E4", "record_id": "KSP-7", "event_type": "inspection", "event_ts": "2024-01-10"},
                {"event_id": "E5", "record_id": "SHP-3", "event_type": "closure", "event_ts": "2025-05-30"},
            ]
        ).to_csv(events_file, index=False)


def run() -> None:
    ensure_sample_data()
    OUT.mkdir(parents=True, exist_ok=True)

    master = pd.read_csv(DATA / "master_records.csv")
    events = pd.read_csv(DATA / "events.csv")

    master_pp = preprocess_master(master)
    scored_pairs, review_queue = link_records(master_pp, Thresholds())
    ubid_registry, ubid_map = build_ubids(master_pp, scored_pairs)

    events_mapped, unmatched_events = map_events_to_ubid(events, master_pp, ubid_map)
    status = classify_status(events_mapped)

    scored_pairs.to_csv(OUT / "scored_pairs.csv", index=False)
    review_queue.to_csv(OUT / "review_queue.csv", index=False)
    ubid_registry.to_csv(OUT / "ubid_registry.csv", index=False)
    ubid_map.to_csv(OUT / "ubid_record_map.csv", index=False)
    events_mapped.to_csv(OUT / "events_mapped.csv", index=False)
    unmatched_events.to_csv(OUT / "events_unmatched.csv", index=False)
    status.to_csv(OUT / "ubid_activity_status.csv", index=False)

    print("Pipeline complete. Outputs written to ./output")


if __name__ == "__main__":
    run()
