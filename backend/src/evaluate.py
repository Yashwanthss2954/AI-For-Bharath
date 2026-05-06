from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"


def compute_metrics(scored: pd.DataFrame, labels: pd.DataFrame) -> dict:
    merged = scored.merge(labels, on=["left_record_id", "right_record_id"], how="inner")
    if merged.empty:
        return {
            "labeled_pairs": 0,
            "precision": None,
            "recall": None,
            "false_merge_rate": None,
            "auto_link_rate": float((scored["decision"] == "auto_link").mean()) if not scored.empty else 0.0,
            "review_rate": float((scored["decision"] == "review").mean()) if not scored.empty else 0.0,
        }

    pred_positive = merged["decision"] == "auto_link"
    actual_positive = merged["is_match"].astype(int) == 1

    tp = int((pred_positive & actual_positive).sum())
    fp = int((pred_positive & ~actual_positive).sum())
    fn = int((~pred_positive & actual_positive).sum())

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    false_merge_rate = fp / (tp + fp) if (tp + fp) else 0.0

    return {
        "labeled_pairs": int(len(merged)),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "false_merge_rate": round(false_merge_rate, 4),
        "auto_link_rate": round(float((scored["decision"] == "auto_link").mean()), 4) if not scored.empty else 0.0,
        "review_rate": round(float((scored["decision"] == "review").mean()), 4) if not scored.empty else 0.0,
    }


def main() -> None:
    scored_file = OUT / "scored_pairs.csv"
    labels_file = OUT / "pair_labels.csv"

    if not scored_file.exists():
        raise SystemExit("Missing output/scored_pairs.csv. Run pipeline first.")

    scored = pd.read_csv(scored_file)

    if not labels_file.exists():
        print("No output/pair_labels.csv found. Metrics requiring labels are skipped.")
        metrics = compute_metrics(scored, pd.DataFrame(columns=["left_record_id", "right_record_id", "is_match"]))
    else:
        labels = pd.read_csv(labels_file)
        metrics = compute_metrics(scored, labels)

    print("UBID Evaluation Metrics")
    for key, value in metrics.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
