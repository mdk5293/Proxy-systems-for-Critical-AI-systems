#!/usr/bin/env python3
"""Convert the frozen repository-disjoint holdout manifest to REDUX benchmark JSON."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path.cwd()

INPUT = (
    ROOT
    / "resubmission"
    / "protocol"
    / "repository_disjoint_holdout_manifest.csv"
)

OUTPUT = (
    ROOT
    / "resubmission"
    / "protocol"
    / "repository_disjoint_holdout.json"
)


def main() -> int:
    with INPUT.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as fh:
        rows = list(csv.DictReader(fh))

    if len(rows) != 24:
        raise RuntimeError(
            f"Expected frozen 24-pair holdout; found {len(rows)}"
        )

    pairs = []

    for row in rows:
        pairs.append(
            {
                "pair_id": row["pair_id"],
                "label": row["label"],
                "repo_a_url": row["repo_a"],
                "repo_b_url": row["repo_b"],
                "evidence_type": row["evidence_type"],
                "evidence_note": row["label_rationale"],
                "evidence_source": row["evidence_source"],
                "evidence_review_date": row["evidence_review_date"],
                "label_finalized": (
                    row["label_finalized"].strip().lower()
                    in {"true", "1", "yes", "y"}
                ),
                "notes": row["notes"],
            }
        )

    payload = {
        "benchmark_name": "repository_disjoint_holdout",
        "benchmark_version": "1.0",
        "cohort_rule": {
            "known_match": 8,
            "known_related": 8,
            "known_non_match": 8,
            "repository_reuse": False,
            "repository_disjoint_from_development_and_v2_benchmark": True,
        },
        "pairs": pairs,
    }

    OUTPUT.write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {OUTPUT}")
    print(f"Pairs: {len(pairs)}")

    for label in (
        "known_match",
        "known_related",
        "known_non_match",
    ):
        print(
            f"{label}: "
            f"{sum(p['label'] == label for p in pairs)}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
