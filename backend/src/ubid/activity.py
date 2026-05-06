from __future__ import annotations

import pandas as pd


def map_events_to_ubid(events: pd.DataFrame, master: pd.DataFrame, ubid_map: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    direct = events.merge(master[["record_id", "pan_norm", "gstin_norm"]], on="record_id", how="left")
    linked = direct.merge(ubid_map, on="record_id", how="left")

    matched = linked[linked["ubid"].notna()].copy()
    unmatched = linked[linked["ubid"].isna()].copy()
    return matched, unmatched


def classify_status(events_mapped: pd.DataFrame, reference_date: pd.Timestamp | None = None) -> pd.DataFrame:
    if reference_date is None:
        reference_date = pd.Timestamp.now(tz=None).normalize()

    if events_mapped.empty:
        return pd.DataFrame(columns=["ubid", "status", "reasons"])

    events = events_mapped.copy()
    events["event_ts"] = pd.to_datetime(events["event_ts"], errors="coerce", utc=True).dt.tz_convert(None)

    rows = []
    for ubid, grp in events.groupby("ubid"):
        last_event = grp["event_ts"].max()
        closure = (grp["event_type"].str.lower() == "closure").any()
        recent_180 = (grp["event_ts"] >= (reference_date - pd.Timedelta(days=180))).sum()

        if closure:
            status = "Closed"
            reasons = "closure_event_present"
        elif recent_180 >= 2:
            status = "Active"
            reasons = f"recent_events_180d={int(recent_180)}"
        else:
            days_since_last = int((reference_date - last_event).days) if pd.notna(last_event) else 9999
            if days_since_last > 365:
                status = "Dormant"
                reasons = f"days_since_last_event={days_since_last}"
            else:
                status = "Active"
                reasons = f"days_since_last_event={days_since_last}"

        rows.append({"ubid": ubid, "status": status, "reasons": reasons})

    return pd.DataFrame(rows)
