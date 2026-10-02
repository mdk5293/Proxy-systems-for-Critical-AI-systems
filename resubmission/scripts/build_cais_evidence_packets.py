from pathlib import Path
import csv
import json
import subprocess

ROOT = Path(".")

SCORING_CSV = (
    ROOT
    / "resubmission/results/cais_proxy_fitness/"
      "cais_proxy_fitness_scoring_blank.csv"
)

RUBRIC_JSON = (
    ROOT
    / "resubmission/protocol/cais_proxy_fitness_rubrics.json"
)

OUT_DIR = (
    ROOT
    / "resubmission/results/cais_proxy_fitness/evidence_packets"
)

OUT_DIR.mkdir(parents=True, exist_ok=True)


def gh_json(repo: str):
    cmd = [
        "gh",
        "repo",
        "view",
        repo,
        "--json",
        "nameWithOwner,url,description,repositoryTopics"
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    if result.returncode != 0:
        return {
            "nameWithOwner": repo,
            "url": f"https://github.com/{repo}",
            "description": "",
            "repositoryTopics": [],
            "_error": result.stderr.strip()
        }

    return json.loads(result.stdout)


def gh_readme(repo: str):
    cmd = [
        "gh",
        "api",
        f"repos/{repo}/readme",
        "-H",
        "Accept: application/vnd.github.raw+json"
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    if result.returncode != 0:
        return (
            "README retrieval failed: "
            + result.stderr.strip()
        )

    return result.stdout or ""


with RUBRIC_JSON.open(
    "r",
    encoding="utf-8"
) as fh:
    rubric_doc = json.load(fh)

rubrics = {
    a["anchor_slug"]: a
    for a in rubric_doc["anchors"]
}


with SCORING_CSV.open(
    "r",
    encoding="utf-8-sig",
    newline=""
) as fh:
    rows = list(csv.DictReader(fh))


pairs = {}

for row in rows:
    key = (
        row["anchor_slug"],
        row["candidate_repo"]
    )

    if key not in pairs:
        pairs[key] = row


print("anchor-candidate pairs=", len(pairs))


for i, ((anchor, repo), row) in enumerate(
    sorted(pairs.items()),
    start=1
):
    print(
        f"[{i}/{len(pairs)}] "
        f"{anchor} -> {repo}"
    )

    meta = gh_json(repo)

    if not isinstance(meta, dict):
        meta = {
            "nameWithOwner": repo,
            "url": f"https://github.com/{repo}",
            "description": "",
            "repositoryTopics": [],
            "_error": "GitHub metadata response was empty or invalid"
        }

    readme = gh_readme(repo)

    rubric = rubrics[anchor]

    safe_anchor = anchor.replace("/", "-")
    safe_repo = repo.replace("/", "-")

    out = (
        OUT_DIR
        / f"{safe_anchor}__{safe_repo}.md"
    )

    topics = []

    for t in (meta.get("repositoryTopics") or []):

        if isinstance(t, dict):
            topics.append(
                t.get("name", "")
            )
        else:
            topics.append(str(t))

    with out.open(
        "w",
        encoding="utf-8"
    ) as fh:

        fh.write(
            f"# CAIS Proxy-Fitness Evidence Packet\n\n"
        )

        fh.write(
            f"- Anchor: `{anchor}`\n"
        )
        fh.write(
            f"- Candidate: `{repo}`\n"
        )

        fh.write(
            f"- Repository URL: "
            f"{meta.get('url', '')}\n\n"
        )

        fh.write("## Repository metadata\n\n")

        fh.write(
            f"Description: "
            f"{meta.get('description') or ''}\n\n"
        )

        fh.write(
            "Topics: "
            + ", ".join(
                t for t in topics if t
            )
            + "\n\n"
        )

        if meta.get("_error"):
            fh.write(
                f"Metadata retrieval error: "
                f"{meta['_error']}\n\n"
            )

        fh.write(
            "## Frozen rubric\n\n"
        )

        for req in rubric["requirements"]:
            fh.write(
                f"### {req['id']} — "
                f"{req['name']}\n\n"
            )

            fh.write(
                f"Critical: "
                f"{req['critical']}\n\n"
            )

            fh.write(
                f"{req['description']}\n\n"
            )

            fh.write(
                "Score: \n\n"
            )

            fh.write(
                "Evidence source: \n\n"
            )

            fh.write(
                "Evidence note: \n\n"
            )

        fh.write(
            "## Retrieved README\n\n"
        )

        fh.write(readme)


print(
    "Wrote evidence packets to:",
    OUT_DIR
)
