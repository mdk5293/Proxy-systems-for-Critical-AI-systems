#!/usr/bin/env python3
"""Build the frozen repository exclusion list for the repository-disjoint holdout."""

from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path.cwd()

BENCHMARK = ROOT / "configs" / "labeled_benchmark_pairs_v2.json"

WINNER_DIR = (
    ROOT
    / "runs"
    / "experiments"
    / "penalty300_min700_cap22_queryv2"
    / "manual-ml-py"
)

OUTPUT = (
    ROOT
    / "resubmission"
    / "protocol"
    / "holdout_excluded_repositories.csv"
)

SUMMARY = (
    ROOT
    / "resubmission"
    / "protocol"
    / "holdout_exclusion_summary.txt"
)


def normalize_repo(value: str) -> str:
    """
    Normalize repository references for identity comparison.

    GitHub URLs become owner/repository.
    Other hosts are retained as host/path so non-GitHub benchmark
    identities are still recorded.
    """
    if not value:
        return ""

    value = value.strip()

    # Remove common git suffix and trailing slash.
    value = re.sub(r"\.git$", "", value, flags=re.IGNORECASE)
    value = value.rstrip("/")

    # Already owner/repo.
    if "://" not in value and value.count("/") == 1:
        return value.lower()

    try:
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

    except Exception:
        pass

    return value.lower()


def extract_anchor_identity(payload: dict, source_path: Path) -> str:
    """
    Read an anchor repository identity from the historical anchor_repo.json.
    Supports several field names because the archived manifests vary slightly.
    """
    candidate_keys = (
        "full_name",
        "FullName",
        "repo",
        "Repo",
        "repository",
        "Repository",
        "slug",
        "Slug",
        "url",
        "Url",
        "html_url",
        "HtmlUrl",
    )

    for key in candidate_keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            normalized = normalize_repo(value)
            if normalized:
                return normalized

    # Directory naming convention is owner-repo, but may contain hyphens
    # inside either owner or repository. Do not attempt to infer owner/repo
    # from the directory unless the JSON itself provides no usable identity.
    raise ValueError(
        f"Could not determine anchor repository from {source_path}"
    )


def main() -> int:
    exclusions: dict[str, set[str]] = defaultdict(set)
    reasons: dict[str, set[str]] = defaultdict(set)

    #
    # 1. Existing v2 labeled benchmark
    #
    benchmark_payload = json.loads(
        BENCHMARK.read_text(encoding="utf-8")
    )

    benchmark_repos: set[str] = set()

    for pair in benchmark_payload["pairs"]:
        for field in ("repo_a_url", "repo_b_url"):
            repo = normalize_repo(str(pair.get(field, "")))

            if not repo:
                continue

            benchmark_repos.add(repo)
            exclusions[repo].add("v2_labeled_benchmark")
            reasons[repo].add(
                "Repository appears in the existing v2 labeled evaluation benchmark."
            )

    #
    # 2. MetaMatch winner-selection anchors
    #
    anchor_repos: set[str] = set()

    anchor_files = sorted(
        WINNER_DIR.glob("*/anchor_repo.json")
    )

    if not anchor_files:
        raise RuntimeError(
            f"No anchor_repo.json files found below {WINNER_DIR}"
        )

    for path in anchor_files:
        payload = json.loads(
            path.read_text(encoding="utf-8-sig")
        )

        repo = extract_anchor_identity(payload, path)

        anchor_repos.add(repo)
        exclusions[repo].add("metamatch_winner_selection_anchor")
        reasons[repo].add(
            "Repository served as an anchor in the MetaMatch experiment "
            "used to select the reported winning configuration."
        )

    #
    # Produce exclusion CSV.
    #
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    rows = []

    for repo in sorted(exclusions):
        rows.append(
            {
                "repository": repo,
                "exclusion_source": "; ".join(
                    sorted(exclusions[repo])
                ),
                "reason": " ".join(
                    sorted(reasons[repo])
                ),
            }
        )

    with OUTPUT.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "repository",
                "exclusion_source",
                "reason",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    #
    # Summary statistics.
    #
    overlap = benchmark_repos & anchor_repos
    union = benchmark_repos | anchor_repos

    summary_lines = [
        "Repository-disjoint holdout exclusion audit",
        "============================================",
        "",
        f"v2 benchmark pairs: {len(benchmark_payload['pairs'])}",
        f"unique repository identities in v2 benchmark: {len(benchmark_repos)}",
        f"MetaMatch winner-selection anchor files: {len(anchor_files)}",
        f"unique MetaMatch winner-selection anchors: {len(anchor_repos)}",
        f"benchmark/tuning-anchor overlap: {len(overlap)}",
        f"total unique excluded repository identities: {len(union)}",
        "",
        "Repositories appearing in both benchmark and winner-selection anchors:",
    ]

    if overlap:
        summary_lines.extend(
            f"  - {repo}"
            for repo in sorted(overlap)
        )
    else:
        summary_lines.append("  (none)")

    SUMMARY.write_text(
        "\n".join(summary_lines) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {OUTPUT}")
    print(f"Wrote {SUMMARY}")
    print()
    print("\n".join(summary_lines))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
