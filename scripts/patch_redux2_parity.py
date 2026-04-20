#!/usr/bin/env python3
"""Patch proxytool_REDUX_2.ipynb: benchmark parity + metadata discrimination."""

from __future__ import annotations

import json
from pathlib import Path

NB = Path(__file__).resolve().parent.parent / "proxytool_REDUX_2.ipynb"

HELPERS = '''
def validate_pair_alignment(pair: Dict[str, object], token: Optional[str] = None) -> Dict[str, object]:
    """
    Alignment guardrail using git ls-remote for any upstream host.
    Strict mode: both resolve to same SHA.
    Fallback: if both sides respond but HEAD differs (mirror lag),
    include with 'documentation_backed' status when official_mirror_claim is True.
    """
    ref = str(pair.get("alignment_ref", "HEAD"))
    upstream_url = str(pair.get("upstream_url", ""))
    mirror_url = str(pair.get("mirror_url", ""))
    official = bool(pair.get("official_mirror_claim", False))

    print(f"  [{pair.get('name')}] resolving mirror ref '{ref}'...")
    mirror_sha = _resolve_ref(mirror_url, ref, token=token)
    if not mirror_sha:
        return {
            "include": False,
            "status": "excluded_unresolved_mirror_ref",
            "reason": f"Mirror ref '{ref}' could not be resolved",
            "mirror_sha": None, "upstream_sha": None,
        }

    print(f"  [{pair.get('name')}] resolving upstream ref '{ref}'...")
    upstream_sha = _resolve_ref(upstream_url, ref, token=token)
    if not upstream_sha:
        return {
            "include": False,
            "status": "excluded_unresolved_upstream_ref",
            "reason": f"Upstream ref '{ref}' unresolvable via API and git ls-remote",
            "mirror_sha": mirror_sha, "upstream_sha": None,
        }

    if upstream_sha == mirror_sha:
        print(f"  [{pair.get('name')}] aligned: {upstream_sha[:12]}")
        return {
            "include": True,
            "status": "aligned_strict_sha_match",
            "reason": f"Exact SHA match at ref '{ref}'",
            "mirror_sha": mirror_sha, "upstream_sha": upstream_sha,
        }

    if official:
        print(f"  [{pair.get('name')}] SHA differs (mirror lag) but official_mirror_claim=True -> included")
        return {
            "include": True,
            "status": "aligned_documentation_backed",
            "reason": f"SHA mismatch (mirror lag) but official_mirror_claim=True; "
                      f"upstream={upstream_sha[:12]} mirror={mirror_sha[:12]}",
            "mirror_sha": mirror_sha, "upstream_sha": upstream_sha,
        }

    return {
        "include": False,
        "status": "excluded_ref_mismatch",
        "reason": f"SHA mismatch and no official_mirror_claim: "
                  f"upstream={upstream_sha[:12]} mirror={mirror_sha[:12]}",
        "mirror_sha": mirror_sha, "upstream_sha": upstream_sha,
    }


def _as_rank_dict(ranked: List[Tuple[str, float]]) -> Dict[str, Tuple[int, float]]:
    return {repo: (i + 1, score) for i, (repo, score) in enumerate(ranked)}


def _filter_metadata_pool_urls(query_url: str, target_url: str, urls: List[str]) -> List[str]:
    """Drop hard-negative URLs that duplicate query or target GitHub slugs (avoids pool distortion)."""
    q = (_repo_slug(query_url) or "").lower()
    t = (_repo_slug(target_url) or "").lower()
    out: List[str] = []
    for u in urls:
        s = (_repo_slug(u) or "").lower()
        if s and s in (q, t):
            continue
        out.append(u)
    return out


def _metadata_rank_pct_display(
    ranked: List[Tuple[str, float]],
    target_url: str,
) -> float:
    """Map target's rank in descending similarity to a 0–100 display score (best rank => 100)."""
    if not ranked:
        return 0.0
    ranked = sorted(ranked, key=lambda x: x[1], reverse=True)
    urls = [u for u, _ in ranked]
    if target_url not in urls:
        return 0.0
    idx = urls.index(target_url)
    n = len(urls)
    if n <= 1:
        return float(round(max(0.0, min(1.0, ranked[0][1])) * 100.0, 2))
    return float(round(100.0 * (1.0 - idx / (n - 1)), 2))


'''

NEW_METHOD = '''
def _method_score_percent_for_target(
    query_url: str,
    target_url: str,
    token: Optional[str] = None,
    max_commits: int = 150,
    metadata_windows: Optional[List[int]] = None,
    metadata_weights: Optional[str] = None,
    metadata_extra_candidates: Optional[List[str]] = None,
    include_alt_metadata: bool = False,
    normalization_mode: str = "global_minmax",
    pairwise_scoring: bool = True,
    metadata_scoring_mode: str = "family_cosine",
    family_score_norm: str = "raw_cosine",
    reporting_mode: str = "rank_pct",
) -> Dict[str, float]:
    """Return method similarity percentages for one query->target pair.

    ``reporting_mode``:
    - ``rank_pct`` (default): one metadata call on ``{target} + extras + hard negatives`` (filtered),
      then display **rank percentile** among that pool (reduces permissive absolute cosines).
    - ``contrastive``: raw target score vs ``[target]+extras``, then `_contrastive_adjust` vs hard negatives.
    - ``raw``: single-candidate metadata score for target only.
    """
    token = token or github_token
    active_weights = metadata_weights or CAIS_WEIGHTS_STRICT

    hard_negatives_default = [
        "https://github.com/django/django",
        "https://github.com/facebook/react",
        "https://github.com/tensorflow/tensorflow",
        "https://github.com/vim/vim",
    ]

    if reporting_mode == "rank_pct":
        extras = list(metadata_extra_candidates or [])
        extras = _filter_metadata_pool_urls(query_url, target_url, extras)
        negs = _filter_metadata_pool_urls(query_url, target_url, list(hard_negatives_default))
        pool = sorted(dict.fromkeys([target_url] + extras + negs))
        meta_ranked = _metadata_similarity(
            query_url,
            pool,
            token=token,
            max_commits=max_commits,
            windows=metadata_windows or [50, 150],
            weights=active_weights,
            normalization_mode=normalization_mode,
            pairwise_scoring=pairwise_scoring,
            scoring_mode=metadata_scoring_mode,
            family_score_norm=family_score_norm,
        )
        meta_pct = _metadata_rank_pct_display(meta_ranked or [], target_url)
    else:
        meta_candidates = [target_url]
        if metadata_extra_candidates:
            for u in metadata_extra_candidates:
                u = str(u).strip()
                if u and u not in meta_candidates:
                    meta_candidates.append(u)
        meta_candidates = sorted(dict.fromkeys(meta_candidates))
        meta_candidates = _filter_metadata_pool_urls(query_url, target_url, meta_candidates)
        if not meta_candidates:
            meta_candidates = [target_url]

        meta_ranked = _metadata_similarity(
            query_url,
            meta_candidates,
            token=token,
            max_commits=max_commits,
            windows=metadata_windows or [50, 150],
            weights=active_weights,
            normalization_mode=normalization_mode,
            pairwise_scoring=pairwise_scoring,
            scoring_mode=metadata_scoring_mode,
            family_score_norm=family_score_norm,
        )
        score_map = {u: float(s) for u, s in (meta_ranked or [])}
        meta_score = float(score_map.get(target_url, 0.0))

        if reporting_mode == "contrastive":
            hn = _filter_metadata_pool_urls(query_url, target_url, list(hard_negatives_default))
            neg_ranked = _metadata_similarity(
                query_url,
                hn,
                token=token,
                max_commits=max_commits,
                windows=metadata_windows or [50, 150],
                weights=active_weights,
                normalization_mode=normalization_mode,
                pairwise_scoring=pairwise_scoring,
                scoring_mode=metadata_scoring_mode,
                family_score_norm=family_score_norm,
            )
            neg_scores = [float(s) for _, s in (neg_ranked or [])]
            meta_score = _contrastive_adjust(meta_score, neg_scores)
        meta_pct = round(float(meta_score) * 100.0, 2)

    result = {"Metadata": float(meta_pct)}

    if include_alt_metadata:
        meta_mimic_ranked = _metadata_similarity(
            query_url,
            [target_url],
            token=token,
            max_commits=max_commits,
            windows=metadata_windows or [50, 150],
            weights=CAIS_WEIGHTS_MIMIC,
            normalization_mode=normalization_mode,
            pairwise_scoring=pairwise_scoring,
            scoring_mode=metadata_scoring_mode,
            family_score_norm=family_score_norm,
        )
        mimic_map = {u: float(s) for u, s in (meta_mimic_ranked or [])}
        meta_mimic_score = float(mimic_map.get(target_url, 0.0))
        result["Metadata Mimic"] = round(meta_mimic_score * 100.0, 2)

    cc_ranked = code_clone_similarity(query_url, [target_url], token=token)
    cc_score = float(cc_ranked[0][1]) if cc_ranked else 0.0
    result["Code centric"] = round(cc_score * 100.0, 2)

    dyn_ranked = dynamic_behavior_similarity(query_url, [target_url], token=token)
    dyn_score = float(dyn_ranked[0][1]) if dyn_ranked else 0.0
    result["Dynamic"] = round(dyn_score * 100.0, 2)

    xl_ranked = deep_code_similarity(query_url, [target_url], token=token)
    xl_score = float(xl_ranked[0][1]) if xl_ranked else 0.0
    result["Cross language"] = round(xl_score * 100.0, 2)

    fam_raw = getattr(_metadata_similarity, "last_family_detail", {})
    result["metadata_family_raw"] = fam_raw.get(target_url, {})
    result["api_fail_count"] = API_FAIL_COUNT
    result["cc_coverage"] = BASELINE_COVERAGE.get(target_url, {}).get("cc_coverage", np.nan)
    result["dyn_coverage"] = BASELINE_COVERAGE.get(target_url, {}).get("dyn_coverage", np.nan)

    return result
'''.strip(
    "\n"
)


def replace_def_block(src: str, fname: str, replacement: str) -> str:
    anchor = f"def {fname}("
    start = src.find(anchor)
    if start < 0:
        raise ValueError(f"missing {anchor}")
    chunk = src[start:]
    lines = chunk.split("\n")
    end_line = len(lines)
    for k in range(1, len(lines)):
        ln = lines[k]
        if ln.startswith("def ") and (not ln[:1].isspace()):
            end_line = k
            break
    tail = "\n".join(lines[end_line:])
    body = replacement.strip() + "\n"
    if tail:
        if not tail.endswith("\n"):
            tail += "\n"
        return src[:start] + body + tail
    return src[:start] + body


def to_lines(text: str) -> list[str]:
    if not text.endswith("\n"):
        text += "\n"
    return [ln + "\n" for ln in text.splitlines()]


def main() -> None:
    nb = json.loads(NB.read_text(encoding="utf-8"))

    # 1) Patch cell 04d42f36
    for c in nb["cells"]:
        if c.get("id") != "04d42f36":
            continue
        src = "".join(c.get("source", []))
        if "def validate_pair_alignment" not in src:
            src = src.replace("def run_known_pair_benchmark", HELPERS.strip() + "\n\n\ndef run_known_pair_benchmark", 1)
        oldq = (
            "        query = upstream\n"
            "        true_match = mirror\n"
            "        candidates = sorted(list(dict.fromkeys([true_match] + negatives)))\n"
        )
        newq = (
            "        true_match = mirror\n"
            "        if not _github_slug_from_url(upstream) and _github_slug_from_url(mirror):\n"
            "            query = mirror\n"
            "        else:\n"
            "            query = upstream\n"
            "        candidates = sorted(list(dict.fromkeys([true_match] + negatives)))\n"
        )
        if oldq in src:
            src = src.replace(oldq, newq, 1)
        src = replace_def_block(src, "_method_score_percent_for_target", NEW_METHOD)
        c["source"] = to_lines(src)
        break
    else:
        raise SystemExit("patch cell 04d42f36 not found")

    # 2) Markdown duplicate cells: f4c223a1 (legacy contrastive), 32cc69ca (duplicate _method)
    md_legacy = (
        "## Legacy `_contrastive_adjust` (removed)\n\n"
        "This cell previously defined a **different** `_contrastive_adjust(query, candidate, ...)` signature, "
        "which collided with the patch cell’s `_contrastive_adjust(raw_score, neg_scores)`.\n\n"
        "Run the **patch cell** `04d42f36` for the canonical implementation.\n"
    )
    md_method = (
        "## Duplicate `_method_score_percent_for_target` (disabled)\n\n"
        "This cell duplicated the scoring helper and could overwrite the patch cell if run later.\n\n"
        "Use definitions from patch cell **`04d42f36`** only.\n"
    )
    for c in nb["cells"]:
        if c.get("id") == "f4c223a1":
            c["cell_type"] = "markdown"
            c["source"] = [md_legacy]
            c.pop("outputs", None)
            c["execution_count"] = None
        if c.get("id") == "32cc69ca":
            c["cell_type"] = "markdown"
            c["source"] = [md_method]
            c.pop("outputs", None)
            c["execution_count"] = None

    # 3) build_argument_table default reporting_mode -> rank_pct
    for c in nb["cells"]:
        if c.get("id") != "8f09e6c0":
            continue
        s = "".join(c.get("source", []))
        s = s.replace(
            '    reporting_mode: str = "contrastive",\n',
            '    reporting_mode: str = "rank_pct",\n',
        )
        s = s.replace(
            "contrastive reporting (less permissive on unrelated pairs). Override\n"
            "    ``reporting_mode`` / ``metadata_scoring_mode`` for legacy weighted-cosine tables.",
            "``rank_pct`` metadata reporting by default (rank within target+extras+filtered hard negatives). Override\n"
            "    ``reporting_mode`` (``raw`` / ``contrastive`` / ``rank_pct``) or ``metadata_scoring_mode`` for legacy tables.",
        )
        c["source"] = to_lines(s)
        break

    # 4) table_test3: add metadata_weights=MIMIC
    for c in nb["cells"]:
        s = "".join(c.get("source", []))
        if "table_test3 = build_argument_table(" not in s or "metadata_weights=CAIS_WEIGHTS_MIMIC" in s:
            continue
        old = (
            "table_test3 = build_argument_table(\n"
            "    known_dissimilar_pairs,\n"
            "    known_similarity_pct=0.0,\n"
            "    metadata_extra_candidates=DEFAULT_METADATA_HARD_NEGATIVES,\n"
        )
        new = (
            "table_test3 = build_argument_table(\n"
            "    known_dissimilar_pairs,\n"
            "    known_similarity_pct=0.0,\n"
            "    metadata_weights=CAIS_WEIGHTS_MIMIC,\n"
            "    metadata_extra_candidates=DEFAULT_METADATA_HARD_NEGATIVES,\n"
        )
        if old in s:
            c["source"] = to_lines(s.replace(old, new, 1))
        break

    # 5) Intro cell: update stale wording about contrastive default
    for c in nb["cells"]:
        s = "".join(c.get("source", []))
        if not s.startswith("# proxytool_REDUX_2"):
            continue
        s = s.replace(
            'Defaults: `metadata_scoring_mode="family_cosine"`, `metadata_windows=[50, 150]`, `family_score_norm="raw_cosine"`, `reporting_mode="contrastive"`.',
            'Defaults: `metadata_scoring_mode="family_cosine"`, `metadata_windows=[50, 150]`, `family_score_norm="raw_cosine"`, `reporting_mode="rank_pct"` (rank within pooled negatives).',
        )
        s = s.replace(
            'build_argument_table(..., reporting_mode="raw", metadata_scoring_mode="weighted_cosine")',
            'build_argument_table(..., reporting_mode="raw" or "contrastive", metadata_scoring_mode="weighted_cosine")',
        )
        c["source"] = [s] if s.endswith("\n") else [s + "\n"]
        break

    NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    print("Wrote", NB)


if __name__ == "__main__":
    main()
