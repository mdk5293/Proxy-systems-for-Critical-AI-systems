from pathlib import Path
import csv
import sys

ROOT = Path(".")

SOURCE = (
    ROOT
    / "resubmission/results/cais_proxy_fitness/"
      "cais_proxy_fitness_scoring_blank.csv"
)

OUT_DIR = (
    ROOT
    / "resubmission/results/cais_proxy_fitness/anchor_scoring"
)

OUT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: python prepare_cais_anchor_scoring.py <anchor_slug>"
        )

    anchor = sys.argv[1]

    with SOURCE.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as fh:
        rows = list(csv.DictReader(fh))

    selected = [
        r for r in rows
        if r["anchor_slug"] == anchor
    ]

    if not selected:
        raise RuntimeError(
            f"No scoring rows found for anchor: {anchor}"
        )

    # Intentionally omit rank, group, MetaMatch score,
    # REDUX score, and source classification during scoring.
    fields = [
        "anchor_slug",
        "anchor_role",
        "candidate_repo",
        "candidate_url",
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

    out = OUT_DIR / f"{anchor}_scoring_blinded.csv"

    with out.open(
        "w",
        encoding="utf-8",
        newline=""
    ) as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=fields
        )
        writer.writeheader()

        for row in selected:
            writer.writerow({
                key: row.get(key, "")
                for key in fields
            })

    candidate_count = len({
        r["candidate_repo"]
        for r in selected
    })

    requirement_count = len({
        r["requirement_id"]
        for r in selected
    })

    print("Wrote:", out)
    print("rows=", len(selected))
    print("candidates=", candidate_count)
    print("requirements=", requirement_count)


if __name__ == "__main__":
    main()
