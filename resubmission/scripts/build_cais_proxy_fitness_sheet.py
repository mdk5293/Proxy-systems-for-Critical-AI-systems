from pathlib import Path
import csv
import json

ROOT = Path(".")

RUBRIC_PATH = ROOT / "resubmission/protocol/cais_proxy_fitness_rubrics.json"

QUERYV2_REDUX = ROOT / "results_benchmark/queryv2_redux"
ANCHORSV2_REDUX = ROOT / "results_benchmark/anchorsv2_redux"

QUERYV2_ARCHIVE = (
    ROOT
    / "runs/experiments/penalty300_min700_cap22_queryv2/manual-ml-py"
)

ANCHORSV2_ARCHIVE = (
    ROOT
    / "runs/experiments/penalty300_min700_cap22_anchorsv2/manual-ml-py"
)

OUT_DIR = ROOT / "resubmission/results/cais_proxy_fitness"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_CSV = OUT_DIR / "cais_proxy_fitness_scoring_blank.csv"


def load_rubrics():
    with RUBRIC_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def archive_for(anchor_slug: str) -> Path:
    """
    Use the frozen queryv2 winner archive whenever available.
    mlflow-mlflow is an anchorsv2-only addition.
    """
    query_path = QUERYV2_ARCHIVE / anchor_slug / "30_Matches.csv"

    if query_path.exists():
        return query_path

    anchor_path = ANCHORSV2_ARCHIVE / anchor_slug / "30_Matches.csv"

    if anchor_path.exists():
        return anchor_path

    raise FileNotFoundError(
        f"No frozen 30_Matches.csv found for {anchor_slug}"
    )


def redux_for(anchor_slug: str) -> Path:
    """
    Prefer queryv2 REDUX output when available.
    """
    q = QUERYV2_REDUX / f"{anchor_slug}.csv"

    if q.exists():
        return q

    a = ANCHORSV2_REDUX / f"{anchor_slug}.csv"

    if a.exists():
        return a

    raise FileNotFoundError(
        f"No REDUX candidate CSV found for {anchor_slug}"
    )


def read_csv(path: Path):
    with path.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as fh:
        return list(csv.DictReader(fh))


def read_top5(anchor_slug: str):
    path = redux_for(anchor_slug)
    rows = read_csv(path)

    if len(rows) < 5:
        raise RuntimeError(
            f"{anchor_slug} has fewer than five REDUX rows"
        )

    return path, rows[:5]


def read_controls(anchor_slug: str, selected_repos: set[str]):
    """
    Select the last two distinct ranked repositories from the frozen
    MetaMatch candidate archive that are not already in the selected top-5.

    Selection is based solely on frozen retrieval rank and is performed
    before CAIS fitness scoring.
    """
    path = archive_for(anchor_slug)
    rows = read_csv(path)

    ranked = []

    for row in rows:
        repo = row.get("CandidateRepo", "").strip()

        if not repo:
            continue

        try:
            rank = int(row.get("Rank", ""))
        except ValueError:
            continue

        ranked.append((rank, row))

    ranked.sort(key=lambda x: x[0], reverse=True)

    controls = []
    seen = set(selected_repos)

    for rank, row in ranked:
        repo = row["CandidateRepo"].strip()

        if repo.lower() in {x.lower() for x in seen}:
            continue

        if repo.lower() in {
            c["CandidateRepo"].strip().lower()
            for c in controls
        }:
            continue

        controls.append(row)
        seen.add(repo)

        if len(controls) == 2:
            break

    if len(controls) != 2:
        raise RuntimeError(
            f"Could not find two distinct controls for {anchor_slug}"
        )

    return path, controls


rubric_doc = load_rubrics()

output_rows = []

for anchor in rubric_doc["anchors"]:
    anchor_slug = anchor["anchor_slug"]

    redux_path, selected = read_top5(anchor_slug)

    selected_names = {
        r.get("candidate_repo", "").strip()
        for r in selected
    }

    archive_path, controls = read_controls(
        anchor_slug,
        selected_names
    )

    candidates = []

    for row in selected:
        candidates.append({
            "candidate_repo": row.get(
                "candidate_repo", ""
            ).strip(),
            "candidate_url": row.get(
                "candidate_url", ""
            ).strip(),
            "candidate_rank": row.get(
                "rank", ""
            ).strip(),
            "candidate_group": "framework_top5",
            "metamatch_score": row.get(
                "metamatch_score", ""
            ).strip(),
            "redux_metadata_pct": row.get(
                "metadata_pct", ""
            ).strip(),
            "source_file": str(redux_path).replace("\\", "/")
        })

    for row in controls:
        candidates.append({
            "candidate_repo": row.get(
                "CandidateRepo", ""
            ).strip(),
            "candidate_url": row.get(
                "CandidateUrl", ""
            ).strip(),
            "candidate_rank": row.get(
                "Rank", ""
            ).strip(),
            "candidate_group": "lower_rank_control",
            "metamatch_score": row.get(
                "Score", ""
            ).strip(),
            "redux_metadata_pct": "",
            "source_file": str(archive_path).replace("\\", "/")
        })

    if len(candidates) != 7:
        raise RuntimeError(
            f"{anchor_slug}: expected 7 candidates, got {len(candidates)}"
        )

    for candidate in candidates:
        for req in anchor["requirements"]:
            output_rows.append({
                "anchor_slug": anchor_slug,
                "anchor_role": anchor["role"],
                "candidate_repo": candidate["candidate_repo"],
                "candidate_url": candidate["candidate_url"],
                "candidate_rank": candidate["candidate_rank"],
                "candidate_group": candidate["candidate_group"],
                "metamatch_score": candidate["metamatch_score"],
                "redux_metadata_pct": candidate["redux_metadata_pct"],
                "candidate_source_file": candidate["source_file"],
                "requirement_id": req["id"],
                "requirement_name": req["name"],
                "critical": req["critical"],
                "requirement_description": req["description"],
                "fitness_score_0_1_2": "",
                "evidence_source": "",
                "evidence_note": "",
                "reviewer_or_labeler": "",
                "scored_date": ""
            })


fieldnames = [
    "anchor_slug",
    "anchor_role",
    "candidate_repo",
    "candidate_url",
    "candidate_rank",
    "candidate_group",
    "metamatch_score",
    "redux_metadata_pct",
    "candidate_source_file",
    "requirement_id",
    "requirement_name",
    "critical",
    "requirement_description",
    "fitness_score_0_1_2",
    "evidence_source",
    "evidence_note",
    "reviewer_or_labeler",
    "scored_date"
]


with OUT_CSV.open(
    "w",
    encoding="utf-8",
    newline=""
) as fh:
    writer = csv.DictWriter(
        fh,
        fieldnames=fieldnames
    )
    writer.writeheader()
    writer.writerows(output_rows)


print("Wrote:", OUT_CSV)
print("rows=", len(output_rows))
print("anchors=", len(rubric_doc["anchors"]))
print("repositories=", len(output_rows) // 6)
print(
    "framework_top5=",
    sum(
        1
        for r in output_rows[::6]
        if r["candidate_group"] == "framework_top5"
    )
)
print(
    "controls=",
    sum(
        1
        for r in output_rows[::6]
        if r["candidate_group"] == "lower_rank_control"
    )
)
