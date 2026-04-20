#!/usr/bin/env python3
"""Apply REDUX_2 notebook transforms (default: proxytool_REDUX_2.ipynb).

Patch scoring helpers and ``_method_score_percent_for_target`` are loaded from
``scripts/patch_redux2_parity.py`` so re-running this script stays aligned with the canonical patch cell.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_NB = REPO_ROOT / "proxytool_REDUX_2.ipynb"


def _load_redux2_patch_assets() -> tuple[str, str]:
    """``(benchmark_helpers, _method_score_percent_for_target block)`` from patch_redux2_parity.py."""
    import importlib.util

    mod_path = REPO_ROOT / "scripts" / "patch_redux2_parity.py"
    spec = importlib.util.spec_from_file_location("_redux2_parity_assets", mod_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {mod_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.HELPERS.strip() + "\n", mod.NEW_METHOD.strip() + "\n"

BUILD_TABLE_NEW = r'''def build_argument_table(
    pair_defs: List[Tuple[str, str, str]],
    known_similarity_pct: float,
    token: Optional[str] = None,
    max_commits: int = 150,
    metadata_windows: Optional[List[int]] = None,
    metadata_weights: Optional[str] = None,
    metadata_extra_candidates: Optional[List[str]] = None,
    metadata_scoring_mode: str = "family_cosine",
    family_score_norm: str = "raw_cosine",
    normalization_mode: str = "global_minmax",
    pairwise_scoring: bool = True,
    include_alt_metadata: bool = False,
    reporting_mode: str = "rank_pct",
) -> pd.DataFrame:
    """Build a table: Test, Known similarity, Metadata, Code centric, Dynamic, Cross language.

    REDUX_2: family cosine + ``rank_pct`` metadata by default; optional ``metadata_extra_candidates``
    widens the metadata candidate pool. Override ``reporting_mode`` for raw or contrastive tables.
    """
    rows = []
    for test_name, query_url, target_url in pair_defs:
        scores = _method_score_percent_for_target(
            query_url,
            target_url,
            token=token,
            max_commits=max_commits,
            metadata_windows=metadata_windows or [50, 150],
            metadata_weights=metadata_weights,
            metadata_extra_candidates=metadata_extra_candidates,
            include_alt_metadata=include_alt_metadata,
            normalization_mode=normalization_mode,
            pairwise_scoring=pairwise_scoring,
            metadata_scoring_mode=metadata_scoring_mode,
            family_score_norm=family_score_norm,
            reporting_mode=reporting_mode,
        )
        rows.append({
            "Test": test_name,
            "Known similarity": f"{known_similarity_pct:.0f}%",
            "Metadata": scores["Metadata"],
            "Code centric": scores["Code centric"],
            "Dynamic": scores["Dynamic"],
            "Cross language": scores["Cross language"],
            "Query": query_url,
            "Target": target_url,
        })
    return pd.DataFrame(rows)
'''

CUSTOM30_NEW = r'''def build_custom_30_table(
    pairs_path: str = "30_Pairs.json",
    metadata_weights: Optional[str] = None,
    metadata_windows: Optional[List[int]] = None,
    max_commits: int = 150,
    clear_cache_first: bool = False,
    label: str = "Custom 30-pair cohort",
    metadata_scoring_mode: str = "family_cosine",
    family_score_norm: str = "raw_cosine",
    reporting_mode: str = "contrastive",
) -> pd.DataFrame:
    """Custom 30-pair table; REDUX_2 defaults align with strict metadata protocol."""
    if clear_cache_first and "CACHE_DIR" in globals():
        shutil.rmtree(CACHE_DIR, ignore_errors=True)
        CACHE_DIR.mkdir(exist_ok=True)
        print(f"Cleared cache: {CACHE_DIR}")

    pairs = _load_custom_pairs(pairs_path)
    repo_urls = _collect_pair_repo_urls(pairs)
    if not repo_urls:
        raise ValueError("Global min-max requires non-empty RepoA/RepoB entries in pairs file.")

    if GLOBAL_NORMALIZER is None:
        fit_global_normalizer(
            repo_urls,
            metrics=CAIS_METRICS,
            token=github_token,
            max_commits=max_commits,
            strategy="minmax",
        )

    rows = []
    for p in pairs:
        ra = str(p.get("RepoA", "")).strip()
        rb = str(p.get("RepoB", "")).strip()
        if not ra or not rb:
            raise ValueError(f"pair ID {p.get('ID')!r}: RepoA and RepoB must be non-empty")

        qurl = _canonical_github_repo_url(ra)
        turl = _canonical_github_repo_url(rb)

        scores = _method_score_percent_for_target(
            qurl,
            turl,
            token=github_token,
            max_commits=max_commits,
            metadata_windows=metadata_windows or [50, 150],
            metadata_weights=metadata_weights or CAIS_WEIGHTS_STRICT,
            normalization_mode="global_minmax",
            pairwise_scoring=True,
            metadata_scoring_mode=metadata_scoring_mode,
            family_score_norm=family_score_norm,
            reporting_mode=reporting_mode,
        )

        rows.append({
            "ID": p["ID"],
            "Domain": p.get("Domain", ""),
            "Test": f"{p['ID']}: {ra} vs {rb}",
            "Metadata": scores["Metadata"],
            "Code centric": scores["Code centric"],
            "Dynamic": scores["Dynamic"],
            "Cross language": scores["Cross language"],
            "Query": qurl,
            "Target": turl,
            "TestGroup": label,
        })

    table = pd.DataFrame(rows)
    avg = {
        "ID": "",
        "Domain": "",
        "Test": "Average",
        "Metadata": round(table["Metadata"].mean(), 1),
        "Code centric": round(table["Code centric"].mean(), 1),
        "Dynamic": round(table["Dynamic"].mean(), 1),
        "Cross language": round(table["Cross language"].mean(), 1),
        "Query": "",
        "Target": "",
        "TestGroup": label,
    }
    return pd.concat([table, pd.DataFrame([avg])], ignore_index=True)


# A/B: explicit legacy vs strict-default calls (same helper; different kwargs)
table_custom_30_weighted = build_custom_30_table(
    pairs_path="30_Pairs.json",
    metadata_weights=CAIS_WEIGHTS_STRICT,
    metadata_windows=[50, 150],
    max_commits=150,
    clear_cache_first=False,
    label="Custom 30-pair cohort (weighted cosine, raw reporting)",
    metadata_scoring_mode="weighted_cosine",
    family_score_norm="raw_cosine",
    reporting_mode="raw",
)

table_custom_30_family = build_custom_30_table(
    pairs_path="30_Pairs.json",
    metadata_weights=CAIS_WEIGHTS_STRICT,
    metadata_windows=[50, 150],
    max_commits=150,
    clear_cache_first=False,
    label="Custom 30-pair cohort (family cosine, contrastive)",
    metadata_scoring_mode="family_cosine",
    family_score_norm="raw_cosine",
    reporting_mode="contrastive",
)

SCORE_COLS = ["Metadata", "Code centric", "Dynamic", "Cross language"]
'''

DEFAULT_NEGS = """DEFAULT_METADATA_HARD_NEGATIVES = [
    \"https://github.com/django/django\",
    \"https://github.com/facebook/react\",
    \"https://github.com/tensorflow/tensorflow\",
    \"https://github.com/vim/vim\",
]

TEST3_METADATA_HARD_NEGATIVES = [
    \"https://github.com/django/django\",
    \"https://github.com/facebook/react\",
    \"https://github.com/tensorflow/tensorflow\",
    \"https://github.com/vim/vim\",
    \"https://github.com/keras-team/keras\",
    \"https://github.com/elastic/elasticsearch\",
    \"https://github.com/prometheus/prometheus\",
    \"https://github.com/bitcoin/bitcoin\",
    \"https://github.com/Homebrew/brew\",
    \"https://github.com/golang/go\",
    \"https://github.com/ansible/ansible\",
    \"https://github.com/apache/spark\",
]


"""

TEST_PREFLIGHT_CELL = r'''# --- REDUX_2 preflight (fresh-kernel safety) ---
import inspect

required_symbols = [
    "_metadata_similarity",
    "_method_score_percent_for_target",
    "run_known_pair_benchmark",
    "build_argument_table",
]
missing = [name for name in required_symbols if name not in globals()]
if missing:
    raise RuntimeError(
        "Missing required scoring symbols: " + ", ".join(missing) + ". "
        "Run the full patch cell '# === Reliability + Discrimination Patch Overrides' (id 04d42f36) first."
    )

method_defaults = {
    k: v.default
    for k, v in inspect.signature(_method_score_percent_for_target).parameters.items()
}
if method_defaults.get("metadata_scoring_mode") != "family_cosine" or method_defaults.get("reporting_mode") != "rank_pct":
    raise RuntimeError(
        "_method_score_percent_for_target defaults are not canonical REDUX_2 patch defaults. "
        "Re-run patch cell 04d42f36 to restore canonical definitions."
    )

fit_global_minmax_for_all_benchmark_tables()
if GLOBAL_NORMALIZER is None:
    raise RuntimeError(
        "GLOBAL_NORMALIZER was not fitted. "
        "Run fit_global_minmax_for_all_benchmark_tables() successfully before table tests."
    )
'''

MARKDOWN_EXEC = """## Canonical scoring execution order

1. **Weights & metrics** — run the `CAIS_WEIGHTS` / `CAIS_METRICS` definition cell.
2. **Core similarity helpers** — run the `MinMaxNormalizer` cell (~31), then the cell that adds `ZScoreNormalizer` + global normalizer helpers (~36); the second replaces `MinMaxNormalizer` in-process.
3. **One patch block only** — run the **last** code cell titled *Reliability + Discrimination Patch Overrides* (`id`: `04d42f36`). It defines `_metadata_similarity`, strict `run_known_pair_benchmark`, baselines, and `_method_score_percent_for_target`. Earlier duplicate patch cells are markdown stubs.
4. **Tables** — run `build_argument_table` / `build_custom_30_table` after step 3.

**Legacy benchmark cell** mid-notebook was converted to markdown so it no longer overwrites the strict `run_known_pair_benchmark` (`strict_only`, `candidate_rows` return shape).

**Weight profiles:** one of `CAIS_WEIGHTS`, `CAIS_WEIGHTS_STRICT`, `CAIS_WEIGHTS_MIMIC`, or `CAIS_WEIGHTS_1` per call unless you pass an explicit weight string.

**Metadata modes:** `weighted_cosine` = one cosine on weighted feature vectors; `family_cosine` = cosine per indicator family, then weighted aggregate.
"""


def replace_def_block(src: str, fname: str, replacement: str) -> str:
    """Replace top-level ``def fname(...)`` through the line before the next column-0 ``def``."""
    anchor = f"def {fname}("
    start = src.find(anchor)
    if start < 0:
        raise ValueError(f"not found: {anchor}")
    prefix = src[:start]
    chunk = src[start:]
    lines = chunk.split("\n")
    end_line_idx = len(lines)
    for k in range(1, len(lines)):
        ln = lines[k]
        if ln.startswith("def ") and (not ln[:1].isspace()):
            end_line_idx = k
            break
    tail = "\n".join(lines[end_line_idx:])
    body = replacement.rstrip() + "\n"
    if tail:
        if not tail.endswith("\n"):
            tail += "\n"
        return prefix + body + tail
    return prefix + body


def to_source_lines(text: str) -> list[str]:
    if not text.endswith("\n"):
        text += "\n"
    return [ln + "\n" for ln in text.splitlines()]


def main(nb_path: Path | None = None) -> None:
    out_path = nb_path or DEFAULT_NB
    nb = json.loads(out_path.read_text(encoding="utf-8"))

    already = any(
        "canonical scoring execution order" in "".join(c.get("source", [])).lower()
        for c in nb["cells"][:8]
        if c.get("cell_type") == "markdown"
    )
    if not already:
        nb["cells"].insert(
            1,
            {
                "cell_type": "markdown",
                "id": "redux2-exec-order",
                "metadata": {},
                "source": [MARKDOWN_EXEC],
            },
        )

    patch_header = "# === Reliability + Discrimination Patch Overrides"
    patch_indices = [
        i
        for i, c in enumerate(nb["cells"])
        if c.get("cell_type") == "code" and patch_header in "".join(c.get("source", []))
    ]
    if len(patch_indices) > 1:
        for idx in patch_indices[:-1]:
            nb["cells"][idx] = {
                "cell_type": "markdown",
                "id": str(nb["cells"][idx].get("id", "patch-dup")) + "-disabled",
                "metadata": {},
                "source": [
                    "## Duplicate patch cell disabled\n\n"
                    "Run only the **last** *Reliability + Discrimination Patch Overrides* code cell "
                    "(`04d42f36`) so `_metadata_similarity`, baselines, and `run_known_pair_benchmark` stay consistent.\n"
                ],
            }

    md_legacy_contrastive = (
        "## Legacy `_contrastive_adjust` (removed)\n\n"
        "This cell previously defined a **different** `_contrastive_adjust(query, candidate, ...)` signature, "
        "which collided with the patch cell’s `_contrastive_adjust(raw_score, neg_scores)`.\n\n"
        "Run the **patch cell** `04d42f36` for the canonical implementation.\n"
    )
    md_dup_method = (
        "## Duplicate `_method_score_percent_for_target` (disabled)\n\n"
        "This cell duplicated the scoring helper and could overwrite the patch cell if run later.\n\n"
        "Use definitions from patch cell **`04d42f36`** only.\n"
    )
    for c in nb["cells"]:
        cid = c.get("id")
        if cid == "f4c223a1":
            c["cell_type"] = "markdown"
            c["source"] = [md_legacy_contrastive]
            c.pop("outputs", None)
            c["execution_count"] = None
        elif cid == "32cc69ca":
            c["cell_type"] = "markdown"
            c["source"] = [md_dup_method]
            c.pop("outputs", None)
            c["execution_count"] = None

    benchmark_helpers, method_new = _load_redux2_patch_assets()
    for i, c in enumerate(nb["cells"]):
        if c.get("cell_type") != "code":
            continue
        src = "".join(c.get("source", []))
        if src.strip().startswith("# ─── Benchmark Runner") and "def run_known_pair_benchmark(" in src:
            nb["cells"][i] = {
                "cell_type": "markdown",
                "id": str(c.get("id", "legacy-benchmark")) + "-md",
                "metadata": {},
                "source": [
                    "## Legacy benchmark runner (code removed)\n\n"
                    "The old `run_known_pair_benchmark` here lacked `strict_only` and used a different return shape. "
                    "Use the runner from the patch cell (`04d42f36`).\n"
                ],
            }
            break

    for i, c in enumerate(nb["cells"]):
        if c.get("cell_type") != "code":
            continue
        src = "".join(c.get("source", []))
        if "def build_argument_table(" not in src:
            continue
        if "DEFAULT_METADATA_HARD_NEGATIVES" not in src:
            src = DEFAULT_NEGS + src
        src = replace_def_block(src, "build_argument_table", BUILD_TABLE_NEW)
        nb["cells"][i]["source"] = to_source_lines(src)
        break

    for i, c in enumerate(nb["cells"]):
        if c.get("cell_type") != "code":
            continue
        src = "".join(c.get("source", []))
        if patch_header not in src or "def _method_score_percent_for_target(" not in src:
            continue
        if "def validate_pair_alignment" not in src:
            src = src.replace(
                "def run_known_pair_benchmark",
                benchmark_helpers + "\n\n\ndef run_known_pair_benchmark",
                1,
            )
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
        nb["cells"][i]["source"] = to_source_lines(
            replace_def_block(src, "_method_score_percent_for_target", method_new)
        )
        break

    custom_done = False
    for i, c in enumerate(nb["cells"]):
        if c.get("cell_type") != "code":
            continue
        src = "".join(c.get("source", []))
        if "def build_custom_30_table(" not in src or "def build_custom_30_table_strict" in src:
            continue
        nb["cells"][i]["source"] = to_source_lines(replace_def_block(src, "build_custom_30_table", CUSTOM30_NEW))
        custom_done = True
        break
    if not custom_done:
        print("Warning: build_custom_30_table cell not found")

    for i, c in enumerate(nb["cells"]):
        if c.get("cell_type") != "code":
            continue
        src = "".join(c.get("source", []))
        if "table_test3 = build_argument_table(" not in src:
            continue
        old = (
            "table_test3 = build_argument_table(\n"
            "    known_dissimilar_pairs,\n"
            "    known_similarity_pct=0.0,\n"
        )
        new = (
            "table_test3 = build_argument_table(\n"
            "    known_dissimilar_pairs,\n"
            "    known_similarity_pct=0.0,\n"
            "    metadata_weights=CAIS_WEIGHTS_MIMIC,\n"
            "    metadata_extra_candidates=TEST3_METADATA_HARD_NEGATIVES,\n"
            "    reporting_mode=\"contrastive\",\n"
        )
        if old in src:
            src = src.replace(old, new, 1)
        else:
            src = src.replace("metadata_extra_candidates=DEFAULT_METADATA_HARD_NEGATIVES,", "metadata_extra_candidates=TEST3_METADATA_HARD_NEGATIVES,")
            if "metadata_weights=CAIS_WEIGHTS_MIMIC" not in src and "known_similarity_pct=0.0," in src:
                src = src.replace("    known_similarity_pct=0.0,\n", "    known_similarity_pct=0.0,\n    metadata_weights=CAIS_WEIGHTS_MIMIC,\n", 1)
            if "reporting_mode=\"contrastive\"" not in src and "known_similarity_pct=0.0," in src:
                src = src.replace("    known_similarity_pct=0.0,\n", "    known_similarity_pct=0.0,\n    reporting_mode=\"contrastive\",\n", 1)
        src = src.replace(
            "    metadata_weights=CAIS_WEIGHTS_MIMIC,\n    metadata_extra_candidates=TEST3_METADATA_HARD_NEGATIVES,\n    reporting_mode=\"contrastive\",\n"
            "    metadata_weights=CAIS_WEIGHTS_MIMIC,\n    metadata_extra_candidates=TEST3_METADATA_HARD_NEGATIVES,\n    reporting_mode=\"contrastive\",\n",
            "    metadata_weights=CAIS_WEIGHTS_MIMIC,\n    metadata_extra_candidates=TEST3_METADATA_HARD_NEGATIVES,\n    reporting_mode=\"contrastive\",\n",
        )
        nb["cells"][i]["source"] = to_source_lines(src)
        break

    preflight_present = any(
        c.get("cell_type") == "code"
        and "# --- REDUX_2 preflight (fresh-kernel safety) ---" in "".join(c.get("source", []))
        for c in nb["cells"]
    )
    if not preflight_present:
        insert_idx = None
        for i, c in enumerate(nb["cells"]):
            if c.get("cell_type") != "code":
                continue
            src = "".join(c.get("source", []))
            if "# --- Test 2: Functional-similar pairs (independent histories) ---" in src:
                insert_idx = i
                break
        if insert_idx is not None:
            nb["cells"].insert(
                insert_idx,
                {
                    "cell_type": "code",
                    "id": "redux2-preflight-flow",
                    "metadata": {},
                    "execution_count": None,
                    "outputs": [],
                    "source": to_source_lines(TEST_PREFLIGHT_CELL),
                },
            )

    for i, c in enumerate(nb["cells"]):
        if c.get("cell_type") != "code":
            continue
        src = "".join(c.get("source", []))
        if "def build_custom_30_table_strict(" not in src:
            continue
        if "metadata_extra_candidates" in src:
            break
        old_sig = '''    reporting_mode: str = "contrastive",
) -> pd.DataFrame:'''
        new_sig = '''    reporting_mode: str = "contrastive",
    metadata_extra_candidates: Optional[List[str]] = None,
) -> pd.DataFrame:'''
        if old_sig not in src:
            print("Warning: build_custom_30_table_strict signature not matched; skip strict patch")
            break
        src = src.replace(old_sig, new_sig, 1)
        old_call = '''        scores = _method_score_percent_for_target(
            qurl,
            turl,
            token=github_token,
            max_commits=max_commits,
            metadata_windows=metadata_windows or [50, 150],
            metadata_weights=metadata_weights or CAIS_WEIGHTS_STRICT,
            normalization_mode="global_minmax",
            pairwise_scoring=True,
            metadata_scoring_mode=metadata_scoring_mode,
            family_score_norm=family_score_norm,
            reporting_mode=reporting_mode,
        )'''
        new_call = '''        scores = _method_score_percent_for_target(
            qurl,
            turl,
            token=github_token,
            max_commits=max_commits,
            metadata_windows=metadata_windows or [50, 150],
            metadata_weights=metadata_weights or CAIS_WEIGHTS_STRICT,
            metadata_extra_candidates=metadata_extra_candidates,
            normalization_mode="global_minmax",
            pairwise_scoring=True,
            metadata_scoring_mode=metadata_scoring_mode,
            family_score_norm=family_score_norm,
            reporting_mode=reporting_mode,
        )'''
        if old_call not in src:
            print("Warning: build_custom_30_table_strict call not matched; skip strict patch")
            break
        src = src.replace(old_call, new_call, 1)
        nb["cells"][i]["source"] = to_source_lines(src)
        break

    out_path.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    print("Wrote", out_path)


if __name__ == "__main__":
    p = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_NB
    main(p)
