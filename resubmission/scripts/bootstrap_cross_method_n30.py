#!/usr/bin/env python3
"""Stratified bootstrap CIs for the reproduced n=30 cross-method agreement experiment."""

from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path
from typing import Dict, List, Sequence

from scipy.stats import pearsonr, spearmanr


SCENARIOS = (
    "known_match",
    "known_non_match",
    "target_uncertain",
)


def load_rows(path: Path) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []

    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)

        for row in reader:
            rows.append(
                {
                    "scenario": row["scenario"],
                    "method_score": float(row["method_score"]),
                    "comparator_score": float(row["comparator_score"]),
                }
            )

    return rows


def correlations(rows: Sequence[Dict[str, object]]) -> tuple[float, float]:
    method = [float(row["method_score"]) for row in rows]
    comparator = [float(row["comparator_score"]) for row in rows]

    pearson = float(pearsonr(method, comparator).statistic)
    spearman = float(spearmanr(method, comparator).statistic)

    return pearson, spearman


def percentile_ci(
    values: Sequence[float],
    alpha: float = 0.05,
) -> tuple[float, float]:
    xs = sorted(values)

    lo_index = int((alpha / 2) * len(xs))
    hi_index = int((1 - alpha / 2) * len(xs)) - 1

    return xs[lo_index], xs[hi_index]


def bootstrap(
    rows: List[Dict[str, object]],
    n_bootstrap: int,
    seed: int,
) -> tuple[List[float], List[float]]:
    rng = random.Random(seed)

    groups = {
        scenario: [
            row
            for row in rows
            if row["scenario"] == scenario
        ]
        for scenario in SCENARIOS
    }

    for scenario in SCENARIOS:
        if not groups[scenario]:
            raise ValueError(f"No rows found for scenario: {scenario}")

    pearsons: List[float] = []
    spearmans: List[float] = []

    for _ in range(n_bootstrap):
        sample: List[Dict[str, object]] = []

        for scenario in SCENARIOS:
            group = groups[scenario]

            sample.extend(
                group[rng.randrange(len(group))]
                for _ in range(len(group))
            )

        pearson, spearman = correlations(sample)

        pearsons.append(pearson)
        spearmans.append(spearman)

    return pearsons, spearmans


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input",
        default=(
            "resubmission/results/uncertainty/"
            "canonical_n30_reproduction/full_pair_table.csv"
        ),
    )

    parser.add_argument(
        "--output",
        default=(
            "resubmission/results/uncertainty/"
            "canonical_n30_reproduction/"
            "cross_method_bootstrap_ci.csv"
        ),
    )

    parser.add_argument(
        "--n-bootstrap",
        type=int,
        default=10000,
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )

    args = parser.parse_args()

    rows = load_rows(Path(args.input))

    counts = {
        scenario: sum(
            1 for row in rows
            if row["scenario"] == scenario
        )
        for scenario in SCENARIOS
    }

    point_pearson, point_spearman = correlations(rows)

    pearsons, spearmans = bootstrap(
        rows,
        args.n_bootstrap,
        args.seed,
    )

    pearson_lo, pearson_hi = percentile_ci(pearsons)
    spearman_lo, spearman_hi = percentile_ci(spearmans)

    output_rows = [
        {
            "metric": "pearson_r",
            "point_estimate": round(point_pearson, 6),
            "bootstrap_mean": round(
                sum(pearsons) / len(pearsons),
                6,
            ),
            "ci_95_lo": round(pearson_lo, 6),
            "ci_95_hi": round(pearson_hi, 6),
            "n_pairs": len(rows),
            "known_match": counts["known_match"],
            "known_non_match": counts["known_non_match"],
            "target_uncertain": counts["target_uncertain"],
            "n_bootstrap": args.n_bootstrap,
            "seed": args.seed,
        },
        {
            "metric": "spearman_rho",
            "point_estimate": round(point_spearman, 6),
            "bootstrap_mean": round(
                sum(spearmans) / len(spearmans),
                6,
            ),
            "ci_95_lo": round(spearman_lo, 6),
            "ci_95_hi": round(spearman_hi, 6),
            "n_pairs": len(rows),
            "known_match": counts["known_match"],
            "known_non_match": counts["known_non_match"],
            "target_uncertain": counts["target_uncertain"],
            "n_bootstrap": args.n_bootstrap,
            "seed": args.seed,
        },
    ]

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)

    with out.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=list(output_rows[0].keys()),
        )
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
