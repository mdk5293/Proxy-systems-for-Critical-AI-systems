from pathlib import Path
import csv

ROOT = Path(".")

BLANK = (
    ROOT
    / "resubmission/results/cais_proxy_fitness/"
      "cais_proxy_fitness_scoring_blank.csv"
)

SCORING_DIR = (
    ROOT
    / "resubmission/results/cais_proxy_fitness/anchor_scoring"
)

OUT_DETAIL = (
    ROOT
    / "resubmission/results/cais_proxy_fitness/"
      "cais_proxy_fitness_scored_all.csv"
)

OUT_SUMMARY = (
    ROOT
    / "resubmission/results/cais_proxy_fitness/"
      "cais_proxy_fitness_candidate_summary.csv"
)

ANCHORS = [
    "apache-airflow",
    "huggingface-transformers",
    "ray-project-ray",
    "mlflow-mlflow",
    "ultralytics-yolov5",
    "serengil-deepface",
    "OpenBB-finance-OpenBB",
    "onnx-onnx",
]


def read_csv(path):
    with path.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as fh:
        return list(csv.DictReader(fh))


# ---------------------------------------------------------
# Read frozen population/metadata
# ---------------------------------------------------------

blank_rows = read_csv(BLANK)

frozen = {}

for row in blank_rows:
    key = (
        row["anchor_slug"],
        row["candidate_repo"],
        row["requirement_id"],
    )

    if key in frozen:
        raise RuntimeError(
            f"Duplicate frozen row: {key}"
        )

    frozen[key] = row


# ---------------------------------------------------------
# Read all completed scoring files
# ---------------------------------------------------------

scored = {}

for anchor in ANCHORS:
    path = (
        SCORING_DIR
        / f"{anchor}_scoring_completed.csv"
    )

    if not path.exists():
        raise RuntimeError(
            f"Missing scoring file: {path}"
        )

    rows = read_csv(path)

    print(
        anchor,
        "rows=",
        len(rows)
    )

    for row in rows:
        key = (
            row["anchor_slug"],
            row["candidate_repo"],
            row["requirement_id"],
        )

        if key in scored:
            raise RuntimeError(
                f"Duplicate scored row: {key}"
            )

        scored[key] = row


# ---------------------------------------------------------
# Validate scored population
# ---------------------------------------------------------

if set(scored) != set(frozen):
    missing = set(frozen) - set(scored)
    extra = set(scored) - set(frozen)

    raise RuntimeError(
        "Scored population does not match frozen population.\n"
        f"Missing={len(missing)}\n"
        f"Extra={len(extra)}"
    )


valid_scores = {"0", "1", "2"}

for key, row in scored.items():
    score = row[
        "fitness_score_0_1_2"
    ].strip()

    if score not in valid_scores:
        raise RuntimeError(
            f"Invalid score {score!r}: {key}"
        )

    if not row[
        "evidence_source"
    ].strip():
        raise RuntimeError(
            f"Missing evidence source: {key}"
        )

    if not row[
        "evidence_note"
    ].strip():
        raise RuntimeError(
            f"Missing evidence note: {key}"
        )


# ---------------------------------------------------------
# Merge frozen metadata back into scored rows
# ---------------------------------------------------------

detail_rows = []

for key in sorted(scored):
    base = frozen[key]
    score = scored[key]

    detail_rows.append({
        "anchor_slug":
            base["anchor_slug"],
        "anchor_role":
            base["anchor_role"],
        "candidate_repo":
            base["candidate_repo"],
        "candidate_url":
            base["candidate_url"],
        "candidate_rank":
            base["candidate_rank"],
        "candidate_group":
            base["candidate_group"],
        "metamatch_score":
            base["metamatch_score"],
        "redux_metadata_pct":
            base["redux_metadata_pct"],
        "candidate_source_file":
            base["candidate_source_file"],
        "requirement_id":
            base["requirement_id"],
        "requirement_name":
            base["requirement_name"],
        "critical":
            base["critical"],
        "requirement_description":
            base["requirement_description"],
        "fitness_score_0_1_2":
            score["fitness_score_0_1_2"],
        "evidence_source":
            score["evidence_source"],
        "evidence_note":
            score["evidence_note"],
        "reviewer_or_labeler":
            score["reviewer_or_labeler"],
        "scored_date":
            score["scored_date"],
    })


with OUT_DETAIL.open(
    "w",
    encoding="utf-8",
    newline=""
) as fh:
    writer = csv.DictWriter(
        fh,
        fieldnames=list(
            detail_rows[0].keys()
        )
    )

    writer.writeheader()
    writer.writerows(detail_rows)


# ---------------------------------------------------------
# Candidate-level summary
# ---------------------------------------------------------

candidates = {}

for row in detail_rows:
    key = (
        row["anchor_slug"],
        row["candidate_repo"]
    )

    d = candidates.setdefault(
        key,
        {
            "anchor_slug":
                row["anchor_slug"],
            "candidate_repo":
                row["candidate_repo"],
            "candidate_url":
                row["candidate_url"],
            "candidate_rank":
                row["candidate_rank"],
            "candidate_group":
                row["candidate_group"],
            "metamatch_score":
                row["metamatch_score"],
            "redux_metadata_pct":
                row["redux_metadata_pct"],
            "points": 0,
            "max_points": 0,
            "critical_zero": False,
            "requirements_scored": 0,
        }
    )

    value = int(
        row["fitness_score_0_1_2"]
    )

    d["points"] += value
    d["max_points"] += 2
    d["requirements_scored"] += 1

    critical = (
        row["critical"]
        .strip()
        .lower()
        == "true"
    )

    if critical and value == 0:
        d["critical_zero"] = True


summary_rows = []

for key in sorted(candidates):
    d = candidates[key]

    if d[
        "requirements_scored"
    ] != 6:
        raise RuntimeError(
            f"Candidate does not have six "
            f"requirements: {key}"
        )

    fitness_pct = (
        100.0
        * d["points"]
        / d["max_points"]
    )

    adequate = (
        fitness_pct >= 60.0
        and not d["critical_zero"]
    )

    summary_rows.append({
        "anchor_slug":
            d["anchor_slug"],
        "candidate_repo":
            d["candidate_repo"],
        "candidate_url":
            d["candidate_url"],
        "candidate_rank":
            d["candidate_rank"],
        "candidate_group":
            d["candidate_group"],
        "metamatch_score":
            d["metamatch_score"],
        "redux_metadata_pct":
            d["redux_metadata_pct"],
        "points":
            d["points"],
        "max_points":
            d["max_points"],
        "fitness_pct":
            f"{fitness_pct:.1f}",
        "critical_zero":
            str(d["critical_zero"]),
        "scenario_adequate":
            str(adequate),
        "requirements_scored":
            d["requirements_scored"],
    })


with OUT_SUMMARY.open(
    "w",
    encoding="utf-8",
    newline=""
) as fh:
    writer = csv.DictWriter(
        fh,
        fieldnames=list(
            summary_rows[0].keys()
        )
    )

    writer.writeheader()
    writer.writerows(summary_rows)


# ---------------------------------------------------------
# Final validation / counts
# ---------------------------------------------------------

anchors = {
    r["anchor_slug"]
    for r in summary_rows
}

top5 = [
    r
    for r in summary_rows
    if r["candidate_group"]
    == "framework_top5"
]

controls = [
    r
    for r in summary_rows
    if r["candidate_group"]
    == "lower_rank_control"
]

adequate = [
    r
    for r in summary_rows
    if r["scenario_adequate"]
    == "True"
]

print()
print("Wrote:", OUT_DETAIL)
print("Wrote:", OUT_SUMMARY)
print()
print("detail_rows=", len(detail_rows))
print("anchors=", len(anchors))
print("candidates=", len(summary_rows))
print("framework_top5=", len(top5))
print("lower_rank_controls=", len(controls))
print("scenario_adequate=", len(adequate))
print(
    "non_adequate=",
    len(summary_rows) - len(adequate)
)
