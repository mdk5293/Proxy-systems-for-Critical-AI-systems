#!/usr/bin/env python3
"""Bootstrap 95% CIs for labeled benchmark F1 using stratified pair-level resampling."""

from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path
from typing import Dict, List, Sequence, Set

from proxytool_redux.benchmark_metrics import compute_pair_classification_metrics


DEFAULT_METHODS = ["metadata", "code_centric", "dynamic", "cross_language"]

STRICT_POSITIVE = {"known_match"}
LENIENT_POSITIVE = {"known_match", "known_related"}
NEGATIVE_LABELS = {"known_non_match"}


def load_pairs(path: Path) -> List[Dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return list(payload.get("pairs", []))


def cohort_rows(
    pairs: Sequence[Dict[str, object]],
    method: str,
    positive_labels: Set[str],
) -> List[Dict[str, object]]:
    """
    Build the exact evaluation cohort for a method.

    Strict:
        known_match + known_non_match

    Lenient:
        known_match + known_related + known_non_match

    target_uncertain and any other labels are excluded.
    """
    key = f"{method}_score"
    allowed_labels = positive_labels | NEGATIVE_LABELS

    rows: List[Dict[str, object]] = []

    for pair in pairs:
        label = str(pair.get("label", ""))

        if label not in allowed_labels:
            continue

        score = pair.get(key)
        if score in (None, ""):
            continue

        rows.append(
            {
                "label": label,
                "score": float(score),
            }
        )

    return rows


def stratified_bootstrap_f1(
    rows: List[Dict[str, object]],
    positive_labels: Set[str],
    threshold: float,
    n: int,
    seed: int,
) -> List[float]:
    """
    Bootstrap F1 while preserving the observed positive/negative class counts.

    This is preferable for the small labeled cohort because an ordinary
    pair-level bootstrap can produce replicates with heavily distorted class
    balance or, in extreme cases, omit one class entirely.
    """
    rng = random.Random(seed)

    positives = [
        row for row in rows
        if str(row["label"]) in positive_labels
    ]
    negatives = [
        row for row in rows
        if str(row["label"]) not in positive_labels
    ]

    if not positives or not negatives:
        return []

    out: List[float] = []

    for _ in range(n):
        positive_sample = [
            positives[rng.randrange(len(positives))]
            for _ in range(len(positives))
        ]

        negative_sample = [
            negatives[rng.randrange(len(negatives))]
            for _ in range(len(negatives))
        ]

        sample = positive_sample + negative_sample

        m = compute_pair_classification_metrics(
            sample,
            score_key="score",
            label_key="label",
            positive_labels=positive_labels,
            threshold=threshold,
        )

        out.append(m.f1)

    return out


def ci(
    values: Sequence[float],
    alpha: float = 0.05,
) -> tuple[float, float, float]:
    if not values:
        return 0.0, 0.0, 0.0

    xs = sorted(values)

    lo_index = int((alpha / 2) * len(xs))
    hi_index = int((1 - alpha / 2) * len(xs)) - 1

    lo = xs[lo_index]
    hi = xs[hi_index]
    mean = sum(xs) / len(xs)

    return mean, lo, hi


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--benchmark",
        default="results_benchmark/labeled_scored_v2.json",
    )

    parser.add_argument(
        "--output",
        default="resubmission/results/uncertainty/labeled_f1_bootstrap_ci.csv",
    )

    parser.add_argument(
        "--threshold",
        type=float,
        default=50.0,
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

    parser.add_argument(
        "--methods",
        nargs="*",
        default=DEFAULT_METHODS,
    )

    args = parser.parse_args()

    pairs = load_pairs(Path(args.benchmark))
    rows_out: List[Dict[str, object]] = []

    for method in args.methods:

        cohorts = (
            (
                "strict",
                STRICT_POSITIVE,
                cohort_rows(
                    pairs,
                    method,
                    STRICT_POSITIVE,
                ),
            ),
            (
                "lenient",
                LENIENT_POSITIVE,
                cohort_rows(
                    pairs,
                    method,
                    LENIENT_POSITIVE,
                ),
            ),
        )

        for name, positive_labels, cohort in cohorts:

            positive_count = sum(
                1
                for row in cohort
                if str(row["label"]) in positive_labels
            )

            negative_count = len(cohort) - positive_count

            f1s = stratified_bootstrap_f1(
                cohort,
                positive_labels,
                args.threshold,
                args.n_bootstrap,
                args.seed,
            )

            mean, lo, hi = ci(f1s)

            rows_out.append(
                {
                    "method": method,
                    "cohort": name,
                    "threshold": args.threshold,
                    "n_pairs": len(cohort),
                    "positive_count": positive_count,
                    "negative_count": negative_count,
                    "f1_mean": round(mean, 4),
                    "f1_ci_lo": round(lo, 4),
                    "f1_ci_hi": round(hi, 4),
                    "n_bootstrap": args.n_bootstrap,
                    "seed": args.seed,
                }
            )

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)

    with out.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as fh:

        writer = csv.DictWriter(
            fh,
            fieldnames=list(rows_out[0].keys()),
        )

        writer.writeheader()
        writer.writerows(rows_out)

    print(f"Wrote {out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
