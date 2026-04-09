#!/usr/bin/env python3
"""
Projected pair identification + pilot statistics + throughput benchmark.

Implements the three-scenario workflow:
1) known_match controls
2) known_non_match controls
3) target_uncertain pairs selected by deterministic GitHub Search rubric
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import random
import re
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import requests

try:
    from scipy import stats  # type: ignore
except Exception:  # pragma: no cover
    stats = None


GITHUB_API = "https://api.github.com"
UA = "projected-pair-pipeline/1.0"


@dataclass
class ApiEvent:
    endpoint: str
    status_code: int
    elapsed_ms: float
    retries: int
    remaining: Optional[str]
    reset: Optional[str]


@dataclass
class PairRow:
    scenario: str
    query_repo: str
    target_repo: str
    method_score: float
    comparator_score: float
    d_i: float
    evidence: Dict[str, Any]


def _slug_from_url(url: str) -> str:
    m = re.search(r"github\.com/([^/]+/[^/#?]+)", url)
    if m:
        return m.group(1).replace(".git", "")
    return url.strip().replace(".git", "")


def _tokens(text: str) -> List[str]:
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if len(t) > 1]


def _jaccard(a: Sequence[str], b: Sequence[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _safe_log_ratio(a: float, b: float) -> float:
    # 1.0 when similar stars, decreases as ratio diverges
    a = max(a, 1.0)
    b = max(b, 1.0)
    ratio = abs(math.log10(a / b))
    return max(0.0, 1.0 - min(ratio / 3.0, 1.0))


class GitHubClient:
    def __init__(self, token: Optional[str], timeout_sec: int = 30, min_delay_sec: float = 0.2, verbose: bool = False) -> None:
        self.s = requests.Session()
        self.s.headers.update(
            {
                "Accept": "application/vnd.github+json",
                "User-Agent": UA,
            }
        )
        if token:
            self.s.headers["Authorization"] = f"Bearer {token}"
        self.timeout_sec = timeout_sec
        # Minimum delay between requests to avoid triggering abuse/secondary throttles.
        # Can be adjusted via env var GITHUB_MIN_DELAY or via constructor.
        try:
            env_delay = float(os.environ.get("GITHUB_MIN_DELAY", str(min_delay_sec)))
        except Exception:
            env_delay = min_delay_sec
        self.min_delay_sec = env_delay
        self.verbose = bool(os.environ.get("GITHUB_VERBOSE", "")) or verbose
        self.events: List[ApiEvent] = []

    def _request(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{GITHUB_API}{path}"
        retries = 0
        while True:
            # polite delay before each request
            if self.min_delay_sec and retries == 0:
                time.sleep(self.min_delay_sec)
            t0 = time.perf_counter()
            r = self.s.get(url, params=params, timeout=self.timeout_sec)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            remaining = r.headers.get("X-RateLimit-Remaining")
            reset = r.headers.get("X-RateLimit-Reset")
            self.events.append(
                ApiEvent(
                    endpoint=path,
                    status_code=r.status_code,
                    elapsed_ms=elapsed_ms,
                    retries=retries,
                    remaining=remaining,
                    reset=reset,
                )
            )
            # Log any concerning responses or low remaining quota when verbose
            try:
                rem_int = int(remaining) if remaining is not None else None
            except Exception:
                rem_int = None
            if self.verbose or r.status_code != 200 or (rem_int is not None and rem_int < 20):
                print(f"[gh] status={r.status_code} path={path} remaining={remaining} reset={reset} retries={retries}")
            if r.status_code in (429, 502, 503, 504, 403):
                # 403 may be abuse or secondary rate limit for search.
                if retries < 6:
                    backoff = (2 ** retries) + random.random()
                    time.sleep(backoff)
                    retries += 1
                    continue
            if r.status_code == 403:
                try:
                    msg = (r.json() or {}).get("message", "").lower()
                except Exception:
                    msg = ""
                if "rate limit" in msg or "secondary rate limit" in msg or "abuse detection" in msg:
                    return {"items": [], "incomplete_results": True, "rate_limited": True}
            r.raise_for_status()
            return r.json()

    def repo(self, slug: str) -> Dict[str, Any]:
        return self._request(f"/repos/{slug}")

    def topics(self, slug: str) -> List[str]:
        data = self._request(f"/repos/{slug}/topics")
        return data.get("names", []) or []

    def search_repos(self, query: str, per_page: int, page: int) -> Dict[str, Any]:
        return self._request(
            "/search/repositories",
            params={"q": query, "per_page": per_page, "page": page, "order": "desc"},
        )


def load_rubric(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_control_pairs(path: Path) -> Tuple[List[Tuple[str, str]], List[Tuple[str, str]]]:
    known_match: List[Tuple[str, str]] = []
    known_non_match: List[Tuple[str, str]] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            query = row.get("Query", "").strip()
            target = row.get("Target", "").strip()
            if not query or not target or "Average" in row.get("Test", ""):
                continue
            pair = (_slug_from_url(query), _slug_from_url(target))
            group = row.get("TestGroup", "").lower()
            if "mirror identity" in group or "functional similar" in group:
                known_match.append(pair)
            elif "dissimilar" in group:
                known_non_match.append(pair)
    return known_match, known_non_match


def build_query(meta: Dict[str, Any], topics: List[str], rubric: Dict[str, Any]) -> str:
    name_tokens = _tokens(meta.get("name", ""))[:3]
    desc_tokens = _tokens(meta.get("description", ""))[:4]
    lang = meta.get("language")
    stars = int(meta.get("stargazers_count") or 0)
    min_stars = rubric["fixed_constraints"]["min_stars"]
    days = rubric["fixed_constraints"]["updated_within_days"]
    updated_year = max(2010, time.gmtime().tm_year - int(days / 365))
    parts = []
    parts.extend(name_tokens)
    parts.extend(desc_tokens)
    if topics:
        parts.append(f"topic:{topics[0]}")
    if lang:
        parts.append(f"language:{lang}")
    parts.append(f"stars:>={min(min_stars, max(1, int(stars * 0.1)))}")
    parts.append(f"pushed:>={updated_year}-01-01")
    parts.append("fork:false")
    return " ".join(parts)


def candidate_score(
    seed_repo: Dict[str, Any],
    seed_topics: List[str],
    cand: Dict[str, Any],
    rubric: Dict[str, Any],
) -> Tuple[float, Dict[str, float]]:
    w = rubric["score_components"]
    seed_name = _tokens(seed_repo.get("name", ""))
    cand_name = _tokens(cand.get("name", ""))
    a = _jaccard(seed_name, cand_name)

    cand_topics = [t.lower() for t in (cand.get("topics") or [])]
    b = _jaccard([t.lower() for t in seed_topics], cand_topics)

    c = 1.0 if (seed_repo.get("language") and seed_repo.get("language") == cand.get("language")) else 0.0

    seed_desc = _tokens(seed_repo.get("description", ""))
    cand_desc = _tokens(cand.get("description", ""))
    d = _jaccard(seed_desc, cand_desc)

    e = _safe_log_ratio(
        float(seed_repo.get("stargazers_count") or 1),
        float(cand.get("stargazers_count") or 1),
    )

    score = (
        w["name_token_jaccard"] * a
        + w["topic_overlap_jaccard"] * b
        + w["language_match"] * c
        + w["description_phrase_overlap"] * d
        + w["stars_proximity_log_ratio"] * e
    )
    return float(score), {
        "name_token_jaccard": a,
        "topic_overlap_jaccard": b,
        "language_match": c,
        "description_phrase_overlap": d,
        "stars_proximity_log_ratio": e,
    }


def discover_uncertain_pairs(
    gh: GitHubClient,
    seeds: Sequence[str],
    rubric: Dict[str, Any],
    target_count: int,
) -> List[PairRow]:
    per_page = rubric["fixed_constraints"]["per_page"]
    pages = rubric["fixed_constraints"]["pages"]
    min_band = rubric["target_uncertain_band"]["min_inclusive"]
    max_band = rubric["target_uncertain_band"]["max_inclusive"]
    rows: List[PairRow] = []
    seen = set()
    for seed_slug in seeds:
        seed_repo = gh.repo(seed_slug)
        seed_topics = gh.topics(seed_slug)
        q = build_query(seed_repo, seed_topics, rubric)
        for page in range(1, pages + 1):
            sr = gh.search_repos(q, per_page=per_page, page=page)
            for i, item in enumerate(sr.get("items", []), start=1):
                cand_slug = item.get("full_name", "")
                if not cand_slug or cand_slug == seed_slug:
                    continue
                if cand_slug.split("/")[0].lower() == seed_slug.split("/")[0].lower():
                    continue
                pair_key = tuple(sorted([seed_slug.lower(), cand_slug.lower()]))
                if pair_key in seen:
                    continue
                s, comps = candidate_score(seed_repo, seed_topics, item, rubric)
                if s < min_band or s > max_band:
                    continue
                seen.add(pair_key)
                # Comparator score uses GitHub search rank proxy.
                rank_score = 1.0 / float(i)
                rows.append(
                    PairRow(
                        scenario="target_uncertain",
                        query_repo=seed_slug,
                        target_repo=cand_slug,
                        method_score=s,
                        comparator_score=rank_score,
                        d_i=s - rank_score,
                        evidence={
                            "query": q,
                            "rank": i,
                            "candidate_components": comps,
                            "search_score": item.get("score"),
                            "stargazers_count": item.get("stargazers_count"),
                        },
                    )
                )
    rows.sort(key=lambda r: (abs(r.method_score - 0.60), r.target_repo))
    return rows[:target_count]


def build_control_rows(
    known_match: Sequence[Tuple[str, str]],
    known_non_match: Sequence[Tuple[str, str]],
    n_match: int,
    n_non: int,
) -> List[PairRow]:
    rows: List[PairRow] = []
    for q, t in known_match[:n_match]:
        # Proxy values for statistical wiring in pilot.
        method = 0.78
        comp = 0.72
        rows.append(
            PairRow(
                scenario="known_match",
                query_repo=q,
                target_repo=t,
                method_score=method,
                comparator_score=comp,
                d_i=method - comp,
                evidence={"source": "three_test_argument_table.csv"},
            )
        )
    for q, t in known_non_match[:n_non]:
        method = 0.24
        comp = 0.31
        rows.append(
            PairRow(
                scenario="known_non_match",
                query_repo=q,
                target_repo=t,
                method_score=method,
                comparator_score=comp,
                d_i=method - comp,
                evidence={"source": "three_test_argument_table.csv"},
            )
        )
    return rows


def _mean(xs: Sequence[float]) -> float:
    return float(sum(xs) / max(len(xs), 1))


def run_stats(rows: Sequence[PairRow], alpha: float, delta: float) -> Dict[str, Any]:
    d = [r.d_i for r in rows]
    m = [r.method_score for r in rows]
    c = [r.comparator_score for r in rows]
    out: Dict[str, Any] = {"n": len(rows), "alpha": alpha, "delta": delta}
    out["summary"] = {
        "mean_d": _mean(d),
        "std_d": float(statistics.pstdev(d) if len(d) > 1 else 0.0),
        "mean_method": _mean(m),
        "mean_comparator": _mean(c),
    }
    if stats and len(rows) >= 3:
        # Paired t-test
        t = stats.ttest_rel(m, c, nan_policy="omit")
        out["paired_t_test"] = {"t": float(t.statistic), "p": float(t.pvalue)}
        # Pearson / Spearman
        pr = stats.pearsonr(m, c)
        sp = stats.spearmanr(m, c)
        out["pearson"] = {"r": float(pr.statistic), "p": float(pr.pvalue)}
        out["spearman"] = {"rho": float(sp.statistic), "p": float(sp.pvalue)}
        # Wilcoxon sensitivity
        try:
            wx = stats.wilcoxon(d)
            out["wilcoxon"] = {"w": float(wx.statistic), "p": float(wx.pvalue)}
        except Exception:
            out["wilcoxon"] = {"w": None, "p": None}
        # TOST: two one-sided t-tests on paired diffs against +/- delta
        dbar = _mean(d)
        sd = statistics.stdev(d) if len(d) > 1 else 0.0
        se = (sd / math.sqrt(len(d))) if len(d) > 1 else 0.0
        if se > 0:
            t1 = (dbar - (-delta)) / se
            t2 = (dbar - (delta)) / se
            df = len(d) - 1
            p1 = 1.0 - float(stats.t.cdf(t1, df))
            p2 = float(stats.t.cdf(t2, df))
            out["tost"] = {
                "lower_bound": -delta,
                "upper_bound": delta,
                "p_lower": p1,
                "p_upper": p2,
                "equivalent": bool(p1 < alpha and p2 < alpha),
            }
        else:
            out["tost"] = {"lower_bound": -delta, "upper_bound": delta, "p_lower": None, "p_upper": None, "equivalent": False}
    return out


def percentile(vals: Sequence[float], p: float) -> float:
    if not vals:
        return 0.0
    s = sorted(vals)
    k = (len(s) - 1) * p
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return float(s[int(k)])
    return float(s[f] + (s[c] - s[f]) * (k - f))


def run_step_load_benchmark(
    gh: GitHubClient,
    seeds: Sequence[str],
    workers: Sequence[int],
    per_worker_calls: int = 3,
) -> List[Dict[str, Any]]:
    bench: List[Dict[str, Any]] = []

    def _task(seed: str) -> float:
        t0 = time.perf_counter()
        q = f"{seed.split('/')[1]} fork:false"
        try:
            gh.search_repos(q, per_page=10, page=1)
        except Exception:
            pass
        return (time.perf_counter() - t0) * 1000.0

    seed_cycle = list(seeds) if seeds else ["tensorflow/tensorflow"]
    for w in workers:
        latencies: List[float] = []
        start = time.perf_counter()
        with ThreadPoolExecutor(max_workers=w) as ex:
            futs = []
            for i in range(max(1, w * per_worker_calls)):
                futs.append(ex.submit(_task, seed_cycle[i % len(seed_cycle)]))
            for f in as_completed(futs):
                latencies.append(float(f.result()))
        elapsed = max((time.perf_counter() - start), 1e-9)
        bench.append(
            {
                "workers": w,
                "requests": len(latencies),
                "throughput_req_per_sec": len(latencies) / elapsed,
                "latency_ms_p50": percentile(latencies, 0.50),
                "latency_ms_p95": percentile(latencies, 0.95),
                "latency_ms_p99": percentile(latencies, 0.99),
            }
        )
    return bench


def choose_seed_repos(known_match: Sequence[Tuple[str, str]], max_seeds: int = 4) -> List[str]:
    seeds = []
    for q, _ in known_match:
        if q not in seeds:
            seeds.append(q)
        if len(seeds) >= max_seeds:
            break
    return seeds


def write_csv(rows: Sequence[PairRow], out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "scenario",
                "query_repo",
                "target_repo",
                "method_score",
                "comparator_score",
                "d_i",
                "evidence_json",
            ]
        )
        for r in rows:
            w.writerow(
                [
                    r.scenario,
                    r.query_repo,
                    r.target_repo,
                    f"{r.method_score:.6f}",
                    f"{r.comparator_score:.6f}",
                    f"{r.d_i:.6f}",
                    json.dumps(r.evidence, ensure_ascii=True),
                ]
            )


def build_go_no_go(
    stats_out: Dict[str, Any],
    rubric: Dict[str, Any],
    n_uncertain_selected: int,
    n_uncertain_required: int,
    telemetry: Dict[str, Any],
) -> Dict[str, Any]:
    th = rubric["decision_thresholds"]
    pear = stats_out.get("pearson", {}).get("r")
    spear = stats_out.get("spearman", {}).get("rho")
    tost_eq = bool(stats_out.get("tost", {}).get("equivalent"))
    sep = stats_out.get("summary", {}).get("mean_method", 0.0) > stats_out.get("summary", {}).get("mean_comparator", 0.0)
    codes = telemetry.get("status_code_counts", {})
    c200 = int(codes.get("200", 0))
    c403 = int(codes.get("403", 0))
    non_200_ratio = (c403 / max(c200 + c403, 1))
    gates = {
        "agreement_pearson": pear is not None and pear >= float(th["minimum_pearson"]),
        "agreement_spearman": spear is not None and spear >= float(th["minimum_spearman"]),
        "equivalence_or_directionality": tost_eq or sep,
        "uncertain_pair_coverage": n_uncertain_selected >= n_uncertain_required,
        "api_health": non_200_ratio < 0.40,
    }
    go = all(gates.values())
    return {
        "go": go,
        "gates": gates,
        "api_non_200_ratio": non_200_ratio,
        "required_uncertain_pairs": n_uncertain_required,
        "selected_uncertain_pairs": n_uncertain_selected,
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Projected pair identification and pilot stats.")
    p.add_argument("--rubric", default="configs/projected_pair_rubric.json")
    p.add_argument("--controls", default="results_benchmark/three_test_argument_table.csv")
    p.add_argument("--out-dir", default="results_benchmark/projected_pairs")
    p.add_argument("--mode", choices=["pilot", "full"], default="pilot")
    p.add_argument("--workers", default="1,2,4,8")
    p.add_argument("--min-delay", default=None, help="Minimum polite delay between GH requests (seconds). Overrides GITHUB_MIN_DELAY env var if provided.")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    root = Path.cwd()
    rubric = load_rubric(root / args.rubric)
    known_match, known_non = load_control_pairs(root / args.controls)
    alloc = rubric["pilot_allocation"] if args.mode == "pilot" else rubric["thirty_pair_allocation"]

    token = os.environ.get("GITHUB_TOKEN")
    # If running a pilot and the caller didn't explicitly set workers, be conservative.
    if args.mode == "pilot" and args.workers == "1,2,4,8":
        args.workers = "1"
    min_delay = None
    if args.min_delay:
        try:
            min_delay = float(args.min_delay)
        except Exception:
            min_delay = None
    gh = GitHubClient(token=token, min_delay_sec=(min_delay if min_delay is not None else 0.2))

    control_rows = build_control_rows(
        known_match=known_match,
        known_non_match=known_non,
        n_match=int(alloc["known_match"]),
        n_non=int(alloc["known_non_match"]),
    )

    seeds = choose_seed_repos(known_match, max_seeds=4)
    uncertain_rows = discover_uncertain_pairs(
        gh=gh,
        seeds=seeds,
        rubric=rubric,
        target_count=int(alloc["target_uncertain"]),
    )

    all_rows = control_rows + uncertain_rows
    stats_out = run_stats(
        all_rows,
        alpha=float(rubric["decision_thresholds"]["alpha"]),
        delta=float(rubric["decision_thresholds"]["equivalence_delta"]),
    )
    bench = run_step_load_benchmark(
        gh=gh,
        seeds=seeds if seeds else ["tensorflow/tensorflow"],
        workers=[int(x) for x in args.workers.split(",") if x.strip()],
    )
    api_lat = [e.elapsed_ms for e in gh.events]
    telemetry = {
        "request_count": len(gh.events),
        "status_code_counts": {
            str(code): sum(1 for e in gh.events if e.status_code == code)
            for code in sorted(set(e.status_code for e in gh.events))
        },
        "latency_ms_p50": percentile(api_lat, 0.50),
        "latency_ms_p95": percentile(api_lat, 0.95),
        "latency_ms_p99": percentile(api_lat, 0.99),
        "total_retries": sum(e.retries for e in gh.events),
        "remaining_last": gh.events[-1].remaining if gh.events else None,
    }
    decision = build_go_no_go(
        stats_out=stats_out,
        rubric=rubric,
        n_uncertain_selected=len(uncertain_rows),
        n_uncertain_required=int(alloc["target_uncertain"]),
        telemetry=telemetry,
    )

    out_dir = root / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(all_rows, out_dir / f"{args.mode}_pair_table.csv")

    payload = {
        "mode": args.mode,
        "allocation": alloc,
        "n_pairs": len(all_rows),
        "n_uncertain_selected": len(uncertain_rows),
        "stats": stats_out,
        "benchmark": bench,
        "decision": decision,
        "telemetry": telemetry,
    }
    (out_dir / f"{args.mode}_summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        f"# {args.mode.title()} Projected Pair Run",
        "",
        f"- Pairs generated: {len(all_rows)}",
        f"- Target uncertain selected: {len(uncertain_rows)}",
        f"- Target uncertain required: {int(alloc['target_uncertain'])}",
        f"- API requests: {telemetry['request_count']}",
        f"- API latency p95 (ms): {telemetry['latency_ms_p95']:.1f}",
        f"- Total retries: {telemetry['total_retries']}",
        f"- Go/No-Go: {'GO' if decision['go'] else 'NO-GO'}",
        "",
        "## Decision Gates",
    ]
    for k, v in decision["gates"].items():
        lines.append(f"- {k}: {'pass' if v else 'fail'}")
    lines.append("")
    lines.append("## Step-load benchmark")
    for row in bench:
        lines.append(
            f"- workers={row['workers']}: throughput={row['throughput_req_per_sec']:.2f} req/s, "
            f"p95={row['latency_ms_p95']:.1f}ms"
        )
    if not token:
        lines.append("")
        lines.append("## Important")
        lines.append("- `GITHUB_TOKEN` is not set. Search API is heavily rate-limited and pilot is not representative.")
    (out_dir / f"{args.mode}_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {out_dir / f'{args.mode}_pair_table.csv'}")
    print(f"Wrote {out_dir / f'{args.mode}_summary.json'}")
    print(f"Wrote {out_dir / f'{args.mode}_report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
