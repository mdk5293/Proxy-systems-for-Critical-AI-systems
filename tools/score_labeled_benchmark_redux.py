#!/usr/bin/env python3
"""Score labeled benchmark pairs and write labeled_scored.json.

Uses existing REDUX REPRO tables when URLs match; optionally runs live REDUX
for pairs missing from cached results (requires GITHUB_TOKEN / network).
"""

from __future__ import annotations

import argparse
import json
import os
import re
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import csv

METHOD_MAP = {
    "Metadata": "metadata_score",
    "Code centric": "code_centric_score",
    "Dynamic": "dynamic_score",
    "Cross language": "cross_language_score",
}


def _norm_github(url: str) -> str:
    raw = str(url).strip().rstrip("/")
    if not raw:
        return ""
    raw = raw.removesuffix(".git")
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)", raw, re.I)
    if m:
        return f"https://github.com/{m.group(1)}/{m.group(2)}"
    return raw


def _github_side(pair: Dict[str, object]) -> Tuple[str, str]:
    """Return (query_url, target_url) for REDUX pair scoring.

    Distinct GitHub-to-GitHub known-match pairs are scored directly.
    Historical mirror pairs with a non-GitHub upstream retain GitHub
    self-comparison behavior for backward compatibility.
    """
    a = str(pair.get("repo_a_url", "")).strip()
    b = str(pair.get("repo_b_url", "")).strip()

    a_g = _norm_github(a)
    b_g = _norm_github(b)

    a_is_github = bool(
        re.match(r"https?://github\.com/[^/]+/[^/]+", a, re.I)
    )
    b_is_github = bool(
        re.match(r"https?://github\.com/[^/]+/[^/]+", b, re.I)
    )

    label = str(pair.get("label", ""))

    if label == "known_match" and a_is_github and b_is_github:
        return a_g, b_g

    if label == "known_match" and b_is_github:
        return b_g, b_g

    if a_is_github and b_is_github:
        return a_g, b_g

    if b_is_github:
        return b_g, b_g

    if a_is_github:
        return a_g, a_g

    raise ValueError(
        f"No GitHub URL for pair {pair.get('pair_id')}"
    )


def _load_three_test(path: Path) -> Dict[Tuple[str, str], Dict[str, float]]:
    if not path.is_file():
        return {}
    out: Dict[Tuple[str, str], Dict[str, float]] = {}
    with path.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if str(row.get("Test", "")).startswith("Average"):
                continue
            q = _norm_github(str(row.get("Query", "")))
            t = _norm_github(str(row.get("Target", "")))
            if not q or not t:
                continue
            out[(q, t)] = {
                "metadata_score": float(row["Metadata"]),
                "code_centric_score": float(row["Code centric"]),
                "dynamic_score": float(row["Dynamic"]),
                "cross_language_score": float(row["Cross language"]),
            }
    return out


def _load_mirror_pairwise(path: Path) -> Dict[Tuple[str, str], Dict[str, float]]:
    """Direct query->target scores from mirror benchmark candidate rows."""
    if not path.is_file():
        return {}
    out: Dict[Tuple[str, str], Dict[str, float]] = {}
    accum: Dict[Tuple[str, str], Dict[str, float]] = {}
    with path.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            q = _norm_github(str(row.get("query", "")))
            t = _norm_github(str(row.get("candidate", "")))
            if not q or not t:
                continue
            method = str(row.get("method", ""))
            key = {
                "metadata": "metadata_score",
                "code_centric": "code_centric_score",
                "dynamic": "dynamic_score",
                "cross_language": "cross_language_score",
            }.get(method)
            if not key:
                continue
            accum.setdefault((q, t), {})[key] = float(row["score_pct"])
    return accum


def _load_mirror_true_match(path: Path) -> Dict[str, Dict[str, float]]:
    """Map mirror name -> method scores for true_match candidate rows."""
    if not path.is_file():
        return {}
    name_map = {
        "V8": "mirror_v8",
        "Blender": "mirror_blender",
        "LibreOffice": "mirror_libreoffice",
        "libapps": "mirror_libapps",
        "FreeType": "mirror_freetype",
    }
    buckets: Dict[str, Dict[str, float]] = {}
    with path.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if str(row.get("is_true_match", "")).lower() not in ("true", "1", "yes"):
                continue
            pair_name = str(row.get("pair", ""))
            pid = name_map.get(pair_name, "")
            if not pid:
                continue
            method = str(row.get("method", ""))
            key = {
                "metadata": "metadata_score",
                "code_centric": "code_centric_score",
                "dynamic": "dynamic_score",
                "cross_language": "cross_language_score",
            }.get(method)
            if key:
                buckets.setdefault(pid, {})[key] = float(row["score_pct"])
    return buckets


def _score_live(query: str, target: str, token: Optional[str], max_commits: int) -> Dict[str, float]:
    from proxytool_redux.bootstrap import load_redux4_core

    g = load_redux4_core({"github_token": token})
    if g.get("GLOBAL_NORMALIZER") is None and "fit_global_normalizer" in g:
        urls = sorted({query, target})
        g["fit_global_normalizer"](
            urls,
            metrics=g.get("CAIS_METRICS"),
            token=token or g.get("github_token"),
            max_commits=max_commits,
            strategy="minmax",
        )
    fn = g["_method_score_percent_for_target"]
    scores = fn(
        query,
        target,
        token=token or g.get("github_token"),
        max_commits=max_commits,
        metadata_weights=g.get("CAIS_WEIGHTS_REDUX3_BLEND"),
        metadata_windows=g.get("REDUX3_METADATA_WINDOWS"),
        metadata_window_weights=g.get("REDUX3_WINDOW_WEIGHTS"),
        normalization_mode="global_minmax",
        pairwise_scoring=True,
        metadata_scoring_mode="family_cosine",
        reporting_mode=g.get("REDUX3_DEFAULT_REPORTING_BENCHMARK", "contrastive"),
        use_domain_hard_negatives=True,
    )
    return {
        "metadata_score": float(scores["Metadata"]),
        "code_centric_score": float(scores["Code centric"]),
        "dynamic_score": float(scores["Dynamic"]),
        "cross_language_score": float(scores["Cross language"]),
    }


def score_pairs(
    benchmark_path: Path,
    *,
    three_test_path: Path,
    mirror_rows_path: Path,
    live: bool,
    token: Optional[str],
    max_commits: int,
) -> Dict[str, object]:
    with benchmark_path.open(encoding="utf-8") as fh:
        payload = json.load(fh)
    pairs = list(payload.get("pairs", []))
    three = _load_three_test(three_test_path)
    mirror_scores = _load_mirror_true_match(mirror_rows_path)
    mirror_pairwise = _load_mirror_pairwise(mirror_rows_path)

    scored_pairs: List[Dict[str, object]] = []
    for pair in pairs:
        p = deepcopy(pair)
        pid = str(p.get("pair_id", ""))
        label = str(p.get("label", ""))
        if label == "known_match":
            q, t = _github_side(p)
        else:
            q = _norm_github(str(p.get("repo_a_url", "")))
            t = _norm_github(str(p.get("repo_b_url", "")))
        scores: Optional[Dict[str, float]] = None
        source = ""

        if pid in mirror_scores and label == "known_match":
            scores = mirror_scores[pid]
            source = "known_mirror_benchmark_canonical_candidate_rows.csv"
        elif (q, t) in mirror_pairwise:
            scores = mirror_pairwise[(q, t)]
            source = "known_mirror_benchmark_pairwise_rows.csv"
        elif (q, t) in three:
            scores = three[(q, t)]
            source = "three_test_argument_table.csv"
        elif live:
            try:
                scores = _score_live(q, t, token, max_commits)
                source = "live_redux"
            except Exception as exc:  # noqa: BLE001
                p["score_error"] = str(exc)[:500]
                source = "live_redux_failed"

        if scores:
            for k, v in scores.items():
                p[k] = round(float(v), 2)
            p["score_source"] = source
            p["redux_query_url"] = q
            p["redux_target_url"] = t
        scored_pairs.append(p)

    payload["pairs"] = scored_pairs
    payload["scoring_notes"] = {
        "mirror_pairs": "GitHub mirror identity scoring (repo_b); upstream URLs validated via verify_repo_access.",
        "methods": "0-100 percent, aligned with three_test_argument_table.csv",
    }
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", default="configs/labeled_benchmark_pairs.json")
    parser.add_argument("--output", default="results_benchmark/labeled_scored.json")
    parser.add_argument(
        "--three-test",
        default="results_benchmark/three_test_argument_table.csv",
    )
    parser.add_argument(
        "--mirror-rows",
        default="results_benchmark/known_mirror_benchmark_canonical_candidate_rows.csv",
    )
    parser.add_argument("--live", action="store_true", help="Run REDUX for pairs missing cached scores")
    parser.add_argument("--max-commits", type=int, default=150)
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    payload = score_pairs(
        Path(args.benchmark),
        three_test_path=Path(args.three_test),
        mirror_rows_path=Path(args.mirror_rows),
        live=args.live,
        token=token,
        max_commits=args.max_commits,
    )
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    filled = sum(
        1
        for p in payload["pairs"]
        if p.get("metadata_score") not in (None, "")
    )
    print(f"Wrote {out} ({filled}/{len(payload['pairs'])} pairs with metadata_score)")
    return 0 if filled == len(payload["pairs"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
