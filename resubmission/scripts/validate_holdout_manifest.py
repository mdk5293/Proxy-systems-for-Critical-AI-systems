#!/usr/bin/env python3
"""Validate repository-disjoint holdout manifest before any scoring."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from urllib.parse import urlparse


ALLOWED_LABELS = {
    "known_match",
    "known_related",
    "known_non_match",
}


def normalize_repo(value: str) -> str:
    if not value:
        return ""

    value = value.strip()
    value = re.sub(r"\.git$", "", value, flags=re.IGNORECASE)
    value = value.rstrip("/")

    if "://" not in value and value.count("/") == 1:
        return value.lower()

    parsed = urlparse(value)

    host = parsed.netloc.lower()
    path = parsed.path.strip("/")
    path = re.sub(r"\.git$", "", path, flags=re.IGNORECASE)

    if host in {"github.com", "www.github.com"}:
        parts = path.split("/")
        if len(parts) >= 2:
            return f"{parts[0]}/{parts[1]}".lower()

    if host:
        return f"{host}/{path}".lower()

    return value.lower()


def truthy(value: str) -> bool:
    return str(value).strip().lower() in {
        "true",
        "yes",
        "1",
        "y",
    }


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--manifest",
        default=(
            "resubmission/protocol/"
            "repository_disjoint_holdout_manifest.csv"
        ),
    )

    parser.add_argument(
        "--exclusions",
        default=(
            "resubmission/protocol/"
            "holdout_excluded_repositories.csv"
        ),
    )

    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    exclusions_path = Path(args.exclusions)

    with exclusions_path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as fh:
        excluded = {
            normalize_repo(row["repository"])
            for row in csv.DictReader(fh)
        }

    with manifest_path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as fh:
        rows = list(csv.DictReader(fh))

    errors: list[str] = []
    warnings: list[str] = []

    seen_pair_ids: set[str] = set()
    repo_usage: dict[str, list[str]] = {}

    counts = {
        label: 0
        for label in ALLOWED_LABELS
    }

    for i, row in enumerate(rows, start=2):
        pair_id = row.get("pair_id", "").strip()
        label = row.get("label", "").strip()

        repo_a = normalize_repo(
            row.get("repo_a", "")
        )
        repo_b = normalize_repo(
            row.get("repo_b", "")
        )

        if not pair_id:
            errors.append(
                f"Row {i}: missing pair_id"
            )

        if pair_id in seen_pair_ids:
            errors.append(
                f"Row {i}: duplicate pair_id {pair_id}"
            )

        seen_pair_ids.add(pair_id)

        if label not in ALLOWED_LABELS:
            errors.append(
                f"Row {i}: invalid label {label!r}"
            )
        else:
            counts[label] += 1

        if not repo_a or not repo_b:
            errors.append(
                f"Row {i}: missing repository identity"
            )
            continue

        if repo_a == repo_b:
            errors.append(
                f"Row {i}: repository self-pair {repo_a}"
            )

        if repo_a in excluded:
            errors.append(
                f"Row {i}: repo_a is excluded: {repo_a}"
            )

        if repo_b in excluded:
            errors.append(
                f"Row {i}: repo_b is excluded: {repo_b}"
            )

        for repo in (repo_a, repo_b):
            repo_usage.setdefault(
                repo,
                [],
            ).append(pair_id)

        if not row.get(
            "label_rationale",
            "",
        ).strip():
            errors.append(
                f"Row {i}: missing label_rationale"
            )

        if not row.get(
            "evidence_type",
            "",
        ).strip():
            errors.append(
                f"Row {i}: missing evidence_type"
            )

        if not row.get(
            "evidence_source",
            "",
        ).strip():
            errors.append(
                f"Row {i}: missing evidence_source"
            )

        if not truthy(
            row.get("label_finalized", "")
        ):
            warnings.append(
                f"Row {i}: label is not finalized"
            )

    repeated = {
        repo: pair_ids
        for repo, pair_ids in repo_usage.items()
        if len(pair_ids) > 1
    }

    for repo, pair_ids in sorted(
        repeated.items()
    ):
        warnings.append(
            "Repository reused across holdout pairs: "
            f"{repo} -> {', '.join(pair_ids)}"
        )

    print(
        f"Holdout pairs: {len(rows)}"
    )

    for label in sorted(counts):
        print(
            f"{label}: {counts[label]}"
        )

    print(
        f"Unique holdout repositories: "
        f"{len(repo_usage)}"
    )

    print(
        f"Repositories reused across pairs: "
        f"{len(repeated)}"
    )

    if warnings:
        print("\nWARNINGS")
        print("--------")
        for item in warnings:
            print(f"- {item}")

    if errors:
        print("\nERRORS")
        print("------")
        for item in errors:
            print(f"- {item}")

        return 1

    print(
        "\nPASS: no holdout repository "
        "appears in the frozen exclusion set."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
