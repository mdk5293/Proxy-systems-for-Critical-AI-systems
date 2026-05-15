#!/usr/bin/env python3
"""One-shot notebook updater for REDUX_4 plan (do not run in CI; local maintenance)."""
from __future__ import annotations

import json
import re
from pathlib import Path


def _set_cell_source(cell: dict, text: str) -> None:
    lines = text.splitlines(keepends=True)
    if not lines:
        cell["source"] = []
        return
    if not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    cell["source"] = lines


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    nb_path = root / "proxytool_REDUX_4.ipynb"
    nb = json.loads(nb_path.read_text(encoding="utf-8"))

    # --- Cell 0: intro markdown ---
    c0 = "".join(nb["cells"][0]["source"])
    if "Canonical run sequence" not in c0:
        c0 = (
            c0.rstrip()
            + "\n\n## Canonical run sequence (all cells preserved)\n\n"
            "Run cells **in this order** for authoritative scores (IDs from notebook JSON):\n\n"
            "1. **Imports / deps** — early code cells through `github_token` and `CAIS_METRICS`.\n"
            "2. **Similarity helpers** — `MinMaxNormalizer` cell (`c8d1b5ef`), then optional `ZScoreNormalizer` cell (`dfd540c4` / `c8d1b5ef` chain per your kernel).\n"
            "3. **Weights + REDUX3 defaults** — `CAIS_WEIGHTS` / `REDUX3_*` cell (`9b1faa9e`).\n"
            "4. **Tables helpers** — `build_argument_table` cell (`8f09e6c0`) *definitions* (may run before patch; **patch overrides** domain helpers when executed later).\n"
            "5. **Patch** — entire **Reliability + Discrimination Patch Overrides** code cell (`893d6fab`). "
            "This defines `_metadata_similarity`, `_contrastive_adjust`, `run_known_pair_benchmark`, and **overrides** `_infer_domain_key_from_url` / `_get_domain_hard_negatives`.\n"
            "6. **Preflight** — `redux2-preflight-flow` cell if present.\n"
            "7. **Benchmarks / plots** — `summarize_known_pair_results` cell (`8403232e`) then benchmark execution cells.\n\n"
            "**Archival cell `eadacf38`:** intentionally a no-op; older `FAMILY_FEATURE_PREFIXES` / `_family_cosine_score` lived there and are superseded by the patch cell.\n"
        )
        _set_cell_source(nb["cells"][0], c0 + "\n")

    # --- Cell 1: execution order ---
    c1 = "".join(nb["cells"][1]["source"])
    if "893d6fab" not in c1:
        c1 = c1.replace("04d42f36", "893d6fab")
        c1 = c1.replace(
            "3. **One patch block only**",
            "3. **One patch block only** (cell id `893d6fab` — search `Reliability + Discrimination Patch Overrides`)",
        )
        _set_cell_source(nb["cells"][1], c1)

    # --- Cell 129: archival no-op ---
    archival = '''# --- ARCHIVAL (cell id `eadacf38`) ---
# Earlier versions of `FAMILY_FEATURE_PREFIXES`, `_family_cosine_score`, and related helpers lived here.
# They are **superseded** by the *Reliability + Discrimination Patch Overrides* cell (id `893d6fab`).
# This cell intentionally defines nothing so **Run All** cannot re-bind an obsolete `_family_cosine_score`.
pass
'''
    _set_cell_source(nb["cells"][129], archival)

    # --- Cell 33: Winsorized normalizer after MinMaxNormalizer class ---
    c33 = "".join(nb["cells"][33]["source"])
    if "class MinMaxNormalizerWinsor" not in c33:
        insert = '''

class MinMaxNormalizerWinsor(MinMaxNormalizer):
    """Global min–max fit with per-feature winsorization (clip to quantiles) before min/max.

    Reduces leverage of single outlier repos on a few keys when fitting ``GLOBAL_NORMALIZER``.
    """

    def __init__(self, eps: float = 0.05, q_low: float = 0.05, q_high: float = 0.95):
        super().__init__(eps=eps)
        self.q_low = float(q_low)
        self.q_high = float(q_high)

    def fit(self, vectors: List[Dict[str, float]]):
        import numpy as _np

        keys = sorted({k for v in vectors for k in v})
        self.min = {}
        self.max = {}
        self.constant_keys = set()

        for k in keys:
            vals = [float(v.get(k, 0.0)) for v in vectors]
            if k == "commit_count":
                vals = [math.log(max(val, 1)) for val in vals]
            if len(vals) < 3:
                mn, mx = min(vals), max(vals)
            else:
                lo, hi = float(_np.quantile(vals, self.q_low)), float(_np.quantile(vals, self.q_high))
                clipped = [min(max(v, lo), hi) for v in vals]
                mn, mx = min(clipped), max(clipped)
            self.min[k], self.max[k] = mn, mx
            if mx - mn <= 1e-12:
                self.constant_keys.add(k)

        self.is_fitted = True
        return self

'''
        anchor = "        return out\n    \ndef cosine("
        if anchor not in c33:
            raise RuntimeError("cell 33 anchor not found for MinMaxNormalizer insert")
        c33 = c33.replace("        return out\n    \ndef cosine(", "        return out\n" + insert + "\ndef cosine(")
        _set_cell_source(nb["cells"][33], c33)

    # --- Cell 33 needs List in scope for type hint - check imports in cell ---
    if "from typing import" not in c33 and "List" not in "".join(nb["cells"][32].get("source", [])):
        pass  # List usually imported earlier in notebook

    # --- Cell 38: fit_global_normalizer strategies ---
    c38 = "".join(nb["cells"][38]["source"])
    if "minmax_winsor" not in c38:
        c38 = c38.replace(
            '    if strategy == "minmax":\n        GLOBAL_NORMALIZER = MinMaxNormalizer().fit(vecs)',
            '    if strategy == "minmax":\n        GLOBAL_NORMALIZER = MinMaxNormalizer().fit(vecs)\n'
            '    elif strategy == "minmax_winsor":\n'
            '        GLOBAL_NORMALIZER = MinMaxNormalizerWinsor().fit(vecs)\n'
            '        print(f"Global winsorized min-max normalizer fit on {len(vecs)} repos")',
        )
        c38 = c38.replace(
            '        print(f"Global min-max normalizer fit on {len(vecs)} repos")\n        return GLOBAL_NORMALIZER',
            '        print(f"Global min-max normalizer fit on {len(vecs)} repos")\n        return GLOBAL_NORMALIZER',
        )
        # Fix duplicate return - read file state
        _set_cell_source(nb["cells"][38], c38)

    # Re-read c38 after first replace - may need second pass for elif branch return
    c38 = "".join(nb["cells"][38]["source"])
    if 'elif strategy == "minmax_winsor":' in c38 and "return GLOBAL_NORMALIZER" not in c38.split("minmax_winsor")[1][:400]:
        c38 = c38.replace(
            '        print(f"Global winsorized min-max normalizer fit on {len(vecs)} repos")',
            '        print(f"Global winsorized min-max normalizer fit on {len(vecs)} repos")\n        return GLOBAL_NORMALIZER',
        )
        _set_cell_source(nb["cells"][38], c38)

    # --- Cell 148: header comment only ---
    c148 = "".join(nb["cells"][148]["source"])
    if "Overridden at runtime" not in c148:
        c148 = (
            "# NOTE: `_infer_domain_key_from_url` / `_get_domain_hard_negatives` are **redefined** in patch cell `893d6fab`.\n"
            "# Keep this cell for defaults / `build_argument_table`; run the patch cell so GitHub-topic-aware overrides apply.\n\n"
            + c148.lstrip()
        )
        _set_cell_source(nb["cells"][148], c148)

    # --- Cell 150: patch mega-cell ---
    s150 = "".join(nb["cells"][150]["source"])
    orig = s150

    if "REDUX3_CONTRASTIVE_TEMPERATURE" not in s150:
        s150 = s150.replace(
            "API_FAIL_COUNT = 0\n",
            "API_FAIL_COUNT = 0\n\n# Tunable contrastive sigmoid slope (must match `_contrastive_adjust`).\nREDUX3_CONTRASTIVE_TEMPERATURE = 6.0\n",
        )

    s150 = s150.replace(
        "    return float(1.0 / (1.0 + np.exp(-6.0 * delta)))",
        "    return float(1.0 / (1.0 + np.exp(-float(REDUX3_CONTRASTIVE_TEMPERATURE) * delta)))",
    )

    s150 = s150.replace(
        "    window_weights: Optional[Dict[int, float]] = None,\n):",
        "    window_weights: Optional[Dict[int, float]] = None,\n    apply_post_pool_minmax: bool = True,\n):",
    )
    s150 = s150.replace(
        "    if normalization_mode == \"global_minmax\" and len(averaged) > 1:\n        vals = [s for _, s in averaged]\n        lo, hi = min(vals), max(vals)\n        if hi > lo:\n            averaged = [(c, (s - lo) / (hi - lo)) for c, s in averaged]",
        "    if apply_post_pool_minmax and normalization_mode == \"global_minmax\" and len(averaged) > 1:\n        vals = [s for _, s in averaged]\n        lo, hi = min(vals), max(vals)\n        if hi > lo:\n            averaged = [(c, (s - lo) / (hi - lo)) for c, s in averaged]",
    )

    # RuntimeError id fix
    s150 = s150.replace("id 04d42f36", "id `893d6fab`")

    inject = '''
_REPO_STARS_CACHE: Dict[str, int] = {}
_REPO_TOPICS_CACHE: Dict[str, str] = {}


def _repo_stargazers_count(slug: str, token: Optional[str] = None) -> Optional[int]:
    if slug in _REPO_STARS_CACHE:
        return _REPO_STARS_CACHE[slug]
    try:
        data = _gh_get(f"/repos/{slug}", token)
        n = int(data.get("stargazers_count", 0) or 0)
        _REPO_STARS_CACHE[slug] = n
        return n
    except Exception:
        return None


def _repo_topics_blob(slug: str, token: Optional[str] = None) -> str:
    if slug in _REPO_TOPICS_CACHE:
        return _REPO_TOPICS_CACHE[slug]
    try:
        headers = {"Accept": "application/vnd.github.mercy-preview+json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        r = requests.get(f"{_GH_API}/repos/{slug}/topics", headers=headers, timeout=30)
        if r.status_code != 200:
            _REPO_TOPICS_CACHE[slug] = ""
            return ""
        names = (r.json() or {}).get("names") or []
        blob = " ".join(str(x).lower() for x in names if x)
        _REPO_TOPICS_CACHE[slug] = blob
        return blob
    except Exception:
        _REPO_TOPICS_CACHE[slug] = ""
        return ""


def _infer_domain_key_from_url(repo_url: str, token: Optional[str] = None) -> str:
    """Infer coarse domain bucket using slug heuristics + GitHub topics (when token allows)."""
    slug = (_repo_slug(repo_url) or "").lower()
    topics = _repo_topics_blob(slug, token)
    blob = slug + " " + topics
    for domain, kws in DOMAIN_KEYWORDS.items():
        if any(kw in blob for kw in kws):
            return domain
    return "app"


def _pick_star_matched_urls(
    pool: List[str],
    ref_slug: str,
    token: Optional[str] = None,
    ref_stars: Optional[int] = None,
    band_ratio: float = 0.35,
    max_checks: int = 16,
) -> List[str]:
    """Prefer URLs with stargazer counts within a band of ref_stars (cheap metadata-hard control)."""
    if ref_stars is None or ref_stars <= 0:
        return []
    lo = int(max(10, ref_stars * (1.0 - band_ratio)))
    hi = int(max(lo + 1, ref_stars * (1.0 + band_ratio)))
    out: List[str] = []
    for u in pool:
        if len(out) >= max_checks:
            break
        s = _repo_slug(u)
        if not s or s == ref_slug:
            continue
        sc = _repo_stargazers_count(s, token)
        if sc is None:
            continue
        if lo <= sc <= hi:
            out.append(u)
    return out


METADATA_NEAR_MISS_EXTRA = [
    "https://github.com/apache/spark",
    "https://github.com/pytorch/pytorch",
    "https://github.com/huggingface/transformers",
    "https://github.com/langchain-ai/langchain",
]


def _get_domain_hard_negatives(
    query_url: str,
    target_url: str,
    limit: int = REDUX3_DOMAIN_NEGATIVE_LIMIT,
    token: Optional[str] = None,
) -> List[str]:
    """Domain negatives + optional star-band near-misses + small curated near-miss list."""
    tok = token or github_token
    qd = _infer_domain_key_from_url(query_url, tok)
    td = _infer_domain_key_from_url(target_url, tok)
    pool: List[str] = []
    for k in [qd, td, "ml", "infra", "app", "systems"]:
        pool.extend(DOMAIN_HARD_NEGATIVE_POOLS.get(k, []))
    pool.extend(DEFAULT_METADATA_HARD_NEGATIVES)
    pool.extend(METADATA_NEAR_MISS_EXTRA)
    pool = _filter_metadata_pool_urls(query_url, target_url, pool)
    pool = list(dict.fromkeys(pool))

    ref_slug = (_repo_slug(target_url) or "").lower()
    ref_stars = _repo_stargazers_count(ref_slug, tok) if ref_slug else None
    near = _pick_star_matched_urls(pool, ref_slug, tok, ref_stars=ref_stars)
    merged = near + [u for u in pool if u not in near]
    return merged[: max(1, int(limit))]


def _metadata_similarity_contrastive_table_aligned(
    query: str,
    candidates: List[str],
    *,
    token: Optional[str],
    max_commits: int,
    windows: Optional[List[int]],
    window_weights: Optional[Dict[int, float]],
    weights: Optional[str],
    normalization_mode: str,
    pairwise_scoring: bool,
    family_score_norm: str,
    coverage_penalty_lambda: float,
) -> List[Tuple[str, float]]:
    """Match ``_method_score_percent_for_target(..., reporting_mode='contrastive')`` per candidate."""
    _ms = globals()["_metadata_similarity"]
    out: List[Tuple[str, float]] = []
    wins = windows or REDUX3_METADATA_WINDOWS
    wwg = window_weights or REDUX3_WINDOW_WEIGHTS
    for c in candidates:
        raw_rank = _ms(
            query,
            [c],
            token=token,
            max_commits=max_commits,
            windows=wins,
            weights=weights,
            normalization_mode=normalization_mode,
            pairwise_scoring=pairwise_scoring,
            scoring_mode="family_cosine",
            family_score_norm=family_score_norm,
            coverage_penalty_lambda=coverage_penalty_lambda,
            window_weights=wwg,
            apply_post_pool_minmax=False,
        )
        raw_c = float(raw_rank[0][1]) if raw_rank else 0.0
        hn = _get_domain_hard_negatives(query, c, token=token)
        neg_rank = _ms(
            query,
            hn,
            token=token,
            max_commits=max_commits,
            windows=wins,
            weights=weights,
            normalization_mode=normalization_mode,
            pairwise_scoring=pairwise_scoring,
            scoring_mode="family_cosine",
            family_score_norm=family_score_norm,
            coverage_penalty_lambda=coverage_penalty_lambda,
            window_weights=wwg,
            apply_post_pool_minmax=True,
        )
        neg_scores = [float(s) for _, s in (neg_rank or [])]
        adj = _contrastive_adjust(raw_c, neg_scores)
        out.append((c, float(adj)))
    out.sort(key=lambda x: x[1], reverse=True)
    return out


def _metadata_similarity_rankpct_pool(
    query: str,
    candidates: List[str],
    *,
    token: Optional[str],
    max_commits: int,
    windows: Optional[List[int]],
    window_weights: Optional[Dict[int, float]],
    weights: Optional[str],
    normalization_mode: str,
    pairwise_scoring: bool,
    family_score_norm: str,
    coverage_penalty_lambda: float,
) -> List[Tuple[str, float]]:
    """Map raw pool scores to rank-fraction in [0,1] (same ordering as ``_metadata_rank_pct_display``)."""
    _ms = globals()["_metadata_similarity"]
    ranked = _ms(
        query,
        candidates,
        token=token,
        max_commits=max_commits,
        windows=windows or REDUX3_METADATA_WINDOWS,
        weights=weights,
        normalization_mode=normalization_mode,
        pairwise_scoring=pairwise_scoring,
        scoring_mode="family_cosine",
        family_score_norm=family_score_norm,
        coverage_penalty_lambda=coverage_penalty_lambda,
        window_weights=window_weights or REDUX3_WINDOW_WEIGHTS,
        apply_post_pool_minmax=True,
    )
    ranked = sorted(ranked or [], key=lambda x: x[1], reverse=True)
    urls = [u for u, _ in ranked]
    n = len(urls)
    if n <= 1:
        s0 = float(ranked[0][1]) if ranked else 0.0
        return [(urls[0], max(0.0, min(1.0, s0)))] if urls else []
    out = []
    for idx, u in enumerate(urls):
        frac = float(1.0 - idx / (n - 1))
        out.append((u, frac))
    return out

'''
    anchor_inj = "def _filter_metadata_pool_urls(query_url: str, target_url: str, urls: List[str]) -> List[str]:"
    if "_metadata_similarity_contrastive_table_aligned" not in s150 and anchor_inj in s150:
        s150 = s150.replace(anchor_inj, inject + "\n\n" + anchor_inj)

    # _method_score_percent_for_target: pass token into _get_domain_hard_negatives
    s150 = s150.replace(
        "hard_negatives_default = _get_domain_hard_negatives(query_url, target_url) if use_domain_hard_negatives else list(DEFAULT_METADATA_HARD_NEGATIVES)",
        "hard_negatives_default = (\n            _get_domain_hard_negatives(query_url, target_url, token=token)\n            if use_domain_hard_negatives\n            else list(DEFAULT_METADATA_HARD_NEGATIVES)\n        )",
    )

    # run_known_pair_benchmark signature + body
    if "metadata_reporting_mode" not in s150:
        s150 = s150.replace(
            "def run_known_pair_benchmark(\n    pairs: Optional[List[Dict[str, object]]] = None,\n    token: Optional[str] = None,\n    max_commits: int = 150,\n    save_prefix: str = \"known_mirror_benchmark\",\n    make_plots: bool = True,\n    strict_only: bool = True,\n) -> Dict[str, object]:",
            "def run_known_pair_benchmark(\n    pairs: Optional[List[Dict[str, object]]] = None,\n    token: Optional[str] = None,\n    max_commits: int = 150,\n    save_prefix: str = \"known_mirror_benchmark\",\n    make_plots: bool = True,\n    strict_only: bool = True,\n    metadata_reporting_mode: str = REDUX3_DEFAULT_REPORTING_BENCHMARK,\n    coverage_penalty_lambda: Optional[float] = None,\n) -> Dict[str, object]:",
        )

    # Replace methods dict block - use regex
    pat_methods = re.compile(
        r"    methods = \{\n        \"metadata\": lambda q, c, ms=_msim: ms\(q, c, token=token, max_commits=max_commits, scoring_mode=\"family_cosine\", family_score_norm=\"raw_cosine\"\),\n        \"code_centric\":[\s\S]*?\"cross_language\": lambda q, c: deep_code_similarity\(q, c, token=token\),\n    \}\n",
        re.M,
    )
    new_methods = '''    cov = float(coverage_penalty_lambda) if coverage_penalty_lambda is not None else float(REDUX3_COVERAGE_PENALTY_LAMBDA)

    def _meta_scorer(q: str, cands: List[str], tm: str):
        mode = str(metadata_reporting_mode or REDUX3_DEFAULT_REPORTING_BENCHMARK).lower()
        if mode == "raw":
            return _msim(
                q,
                cands,
                token=token,
                max_commits=max_commits,
                scoring_mode="family_cosine",
                family_score_norm="raw_cosine",
                coverage_penalty_lambda=cov,
                apply_post_pool_minmax=True,
            )
        if mode in ("contrastive", str(REDUX3_DEFAULT_REPORTING_BENCHMARK).lower()):
            return _metadata_similarity_contrastive_table_aligned(
                q,
                cands,
                token=token,
                max_commits=max_commits,
                windows=REDUX3_METADATA_WINDOWS,
                window_weights=REDUX3_WINDOW_WEIGHTS,
                weights=CAIS_WEIGHTS_STRICT,
                normalization_mode="global_minmax",
                pairwise_scoring=True,
                family_score_norm="raw_cosine",
                coverage_penalty_lambda=cov,
            )
        if mode == "rank_pct":
            return _metadata_similarity_rankpct_pool(
                q,
                cands,
                token=token,
                max_commits=max_commits,
                windows=REDUX3_METADATA_WINDOWS,
                window_weights=REDUX3_WINDOW_WEIGHTS,
                weights=CAIS_WEIGHTS_STRICT,
                normalization_mode="global_minmax",
                pairwise_scoring=True,
                family_score_norm="raw_cosine",
                coverage_penalty_lambda=cov,
            )
        raise ValueError(f"Unknown metadata_reporting_mode: {metadata_reporting_mode!r}")

    methods = {
        "metadata": lambda q, c, tm=None: _meta_scorer(q, c, str(tm or "")),
        "code_centric": lambda q, c, tm=None: code_clone_similarity(q, c, token=token),
        "dynamic": lambda q, c, tm=None: dynamic_behavior_similarity(q, c, token=token),
        "cross_language": lambda q, c, tm=None: deep_code_similarity(q, c, token=token),
    }
'''
    s150_new, nsub = pat_methods.subn(new_methods, s150, count=1)
    if nsub != 1:
        raise RuntimeError(f"methods block replace failed (nsub={nsub})")

    s150 = s150_new
    s150 = s150.replace(
        "            ranked = scorer(query, candidates) or []",
        "            ranked = scorer(query, candidates, true_match) or []",
    )

    if s150 == orig and "REDUX3_CONTRASTIVE_TEMPERATURE" in orig:
        pass  # idempotent partial
    _set_cell_source(nb["cells"][150], s150)

    # --- Cell 134: MRR + recall@3 ---
    c134 = "".join(nb["cells"][134]["source"])
    if "mrr" not in c134:
        c134 = c134.replace(
            '    cols = [\n        "method", "n_pairs", "n_candidate_rows", "top1_accuracy", "threshold",\n        "tp", "tn", "fp", "fn", "precision", "recall", "f1", "accuracy",\n    ]',
            '    cols = [\n        "method", "n_pairs", "n_candidate_rows", "top1_accuracy", "mrr", "recall_at_3", "threshold",\n        "tp", "tn", "fp", "fn", "precision", "recall", "f1", "accuracy",\n    ]',
        )
        insert_block = '''
        ranks = g.loc[g[label_col] == 1, "rank"].dropna().astype(float)
        mrr = float((1.0 / ranks).mean()) if len(ranks) else 0.0
        rk3 = g.loc[g[label_col] == 1, "rank"].dropna().astype(float)
        recall_at_3 = float((rk3 <= 3.0).mean()) if len(rk3) else 0.0

'''
        c134 = c134.replace(
            "        else:\n            top1_acc = 0.0\n            n_pairs = int(g[\"pair\"].nunique())\n\n        rows.append({",
            "        else:\n            top1_acc = 0.0\n            n_pairs = int(g[\"pair\"].nunique())\n" + insert_block + "\n        rows.append({",
        )
        c134 = c134.replace(
            '"top1_accuracy": top1_acc, "threshold": round(opt_t, 4),',
            '"top1_accuracy": top1_acc, "mrr": round(mrr, 4), "recall_at_3": round(recall_at_3, 4), "threshold": round(opt_t, 4),',
        )
        _set_cell_source(nb["cells"][134], c134)

    # --- Append appendix cells if missing ---
    tail_id = "redux4-appendix-sweep"
    if not any(tail_id in "".join(c.get("source", [])) for c in nb["cells"]):
        md = {
            "cell_type": "markdown",
            "id": tail_id + "-md",
            "metadata": {},
            "source": [
                "## REDUX_4 Appendix — mini hyperparameter sweep\n\n",
                "Writes `results_benchmark/redux4_mini_sweep.csv` by temporarily mutating `REDUX3_COVERAGE_PENALTY_LAMBDA` "
                "and `REDUX3_CONTRASTIVE_TEMPERATURE` and re-running `run_known_pair_benchmark` with **plots disabled**.\n\n",
                "Requires: weights cell, normalizers, patch cell `893d6fab`, `KNOWN_MIRROR_PAIRS`, `github_token`.\n",
            ],
        }
        code = {
            "cell_type": "code",
            "id": tail_id,
            "metadata": {},
            "outputs": [],
            "execution_count": None,
            "source": [
                "def run_redux4_mini_sweep(\n",
                "    token: Optional[str] = None,\n",
                "    max_commits: int = 150,\n",
                ") -> pd.DataFrame:\n",
                "    \"\"\"Small grid over coverage penalty + contrastive temperature (metadata path only metrics in summary).\"\"\"\n",
                "    import copy\n",
                "\n",
                "    token = token or github_token\n",
                "    base_cov = float(REDUX3_COVERAGE_PENALTY_LAMBDA)\n",
                "    base_temp = float(REDUX3_CONTRASTIVE_TEMPERATURE)\n",
                "    rows = []\n",
                "    for cov in (0.10, 0.15, 0.20, 0.25):\n",
                "        for temp in (4.0, 6.0, 8.0):\n",
                "            globals()[\"REDUX3_COVERAGE_PENALTY_LAMBDA\"] = float(cov)\n",
                "            globals()[\"REDUX3_CONTRASTIVE_TEMPERATURE\"] = float(temp)\n",
                "            out = run_known_pair_benchmark(\n",
                "                token=token,\n",
                "                max_commits=max_commits,\n",
                "                save_prefix=f\"redux4_sweep_cov{cov}_t{temp}\",\n",
                "                make_plots=False,\n",
                "                metadata_reporting_mode=REDUX3_DEFAULT_REPORTING_BENCHMARK,\n",
                "                coverage_penalty_lambda=float(cov),\n",
                "            )\n",
                "            summ = out[\"summary\"]\n",
                "            if summ is None or summ.empty:\n",
                "                rows.append({\"coverage\": cov, \"contrastive_temp\": temp, \"note\": \"empty\"})\n",
                "                continue\n",
                "            meta = summ.loc[summ[\"method\"] == \"metadata\"]\n",
                "            if meta.empty:\n",
                "                rows.append({\"coverage\": cov, \"contrastive_temp\": temp, \"note\": \"no_metadata\"})\n",
                "                continue\n",
                "            r = meta.iloc[0].to_dict()\n",
                "            r[\"coverage\"] = cov\n",
                "            r[\"contrastive_temp\"] = temp\n",
                "            rows.append(r)\n",
                "    globals()[\"REDUX3_COVERAGE_PENALTY_LAMBDA\"] = base_cov\n",
                "    globals()[\"REDUX3_CONTRASTIVE_TEMPERATURE\"] = base_temp\n",
                "    df = pd.DataFrame(rows)\n",
                "    Path(\"results_benchmark\").mkdir(exist_ok=True)\n",
                "    p = Path(\"results_benchmark\") / \"redux4_mini_sweep.csv\"\n",
                "    df.to_csv(p, index=False)\n",
                "    print(\"Saved\", p)\n",
                "    return df\n\n",
                "# Example (uncomment to run; hits GitHub API):\n",
                "# run_redux4_mini_sweep()\n",
            ],
        }
        nb["cells"].extend([md, code])

    nb_path.write_text(json.dumps(nb, indent=1), encoding="utf-8")
    print("Wrote", nb_path)


if __name__ == "__main__":
    main()
