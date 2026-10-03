from pathlib import Path
import csv
import math
import random
import statistics

from scipy.stats import (
    fisher_exact,
    mannwhitneyu,
    spearmanr,
)

ROOT = Path(".")

INPUT = (
    ROOT
    / "resubmission/results/cais_proxy_fitness/"
      "cais_proxy_fitness_candidate_summary.csv"
)

OUT = (
    ROOT
    / "resubmission/results/cais_proxy_fitness/"
      "cais_proxy_fitness_analysis.txt"
)

BOOTSTRAPS = 10000
SEED = 5293


def read_rows():
    with INPUT.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as fh:
        rows = list(csv.DictReader(fh))

    for r in rows:
        r["candidate_rank"] = int(
            r["candidate_rank"]
        )
        r["metamatch_score"] = float(
            r["metamatch_score"]
        )
        r["fitness_pct"] = float(
            r["fitness_pct"]
        )

        redux = (
            r["redux_metadata_pct"]
            .strip()
        )

        r["redux_metadata_pct"] = (
            float(redux)
            if redux
            else None
        )

        r["adequate"] = (
            r["scenario_adequate"]
            .strip()
            .lower()
            == "true"
        )

    return rows


def mean(values):
    return (
        statistics.mean(values)
        if values
        else float("nan")
    )


def median(values):
    return (
        statistics.median(values)
        if values
        else float("nan")
    )


def pct(n, d):
    return 100.0 * n / d


def percentile(values, q):
    values = sorted(values)

    if not values:
        return float("nan")

    k = (len(values) - 1) * q
    f = math.floor(k)
    c = math.ceil(k)

    if f == c:
        return values[f]

    return (
        values[f] * (c - k)
        + values[c] * (k - f)
    )


def bootstrap_anchor_cluster(
    rows,
    stat_func,
    n=BOOTSTRAPS
):
    rng = random.Random(SEED)

    anchors = sorted({
        r["anchor_slug"]
        for r in rows
    })

    by_anchor = {
        a: [
            r for r in rows
            if r["anchor_slug"] == a
        ]
        for a in anchors
    }

    values = []

    for _ in range(n):
        sampled = []

        for _ in anchors:
            a = rng.choice(anchors)
            sampled.extend(by_anchor[a])

        try:
            value = stat_func(sampled)
        except Exception:
            continue

        if value is None:
            continue

        if isinstance(value, float):
            if math.isnan(value):
                continue

        values.append(value)

    return (
        percentile(values, 0.025),
        percentile(values, 0.975),
    )


def adequacy_difference(rows):
    top = [
        r for r in rows
        if r["candidate_group"]
        == "framework_top5"
    ]

    controls = [
        r for r in rows
        if r["candidate_group"]
        == "lower_rank_control"
    ]

    if not top or not controls:
        return float("nan")

    top_rate = mean([
        1.0 if r["adequate"] else 0.0
        for r in top
    ])

    control_rate = mean([
        1.0 if r["adequate"] else 0.0
        for r in controls
    ])

    return 100.0 * (
        top_rate - control_rate
    )


def fitness_difference(rows):
    top = [
        r["fitness_pct"]
        for r in rows
        if r["candidate_group"]
        == "framework_top5"
    ]

    controls = [
        r["fitness_pct"]
        for r in rows
        if r["candidate_group"]
        == "lower_rank_control"
    ]

    if not top or not controls:
        return float("nan")

    return mean(top) - mean(controls)


def metamatch_fitness_rho(rows):
    result = spearmanr(
        [
            r["metamatch_score"]
            for r in rows
        ],
        [
            r["fitness_pct"]
            for r in rows
        ],
    )

    return float(result.statistic)


def rank_fitness_rho(rows):
    result = spearmanr(
        [
            r["candidate_rank"]
            for r in rows
        ],
        [
            r["fitness_pct"]
            for r in rows
        ],
    )

    return float(result.statistic)


def redux_fitness_rho(rows):
    rows = [
        r for r in rows
        if r[
            "redux_metadata_pct"
        ] is not None
    ]

    if len(rows) < 3:
        return float("nan")

    result = spearmanr(
        [
            r["redux_metadata_pct"]
            for r in rows
        ],
        [
            r["fitness_pct"]
            for r in rows
        ],
    )

    return float(result.statistic)


rows = read_rows()

top = [
    r for r in rows
    if r["candidate_group"]
    == "framework_top5"
]

controls = [
    r for r in rows
    if r["candidate_group"]
    == "lower_rank_control"
]

redux_rows = [
    r for r in rows
    if r["redux_metadata_pct"]
    is not None
]


# ---------------------------------------------------------
# Basic counts
# ---------------------------------------------------------

overall_adequate = sum(
    r["adequate"]
    for r in rows
)

top_adequate = sum(
    r["adequate"]
    for r in top
)

control_adequate = sum(
    r["adequate"]
    for r in controls
)


# ---------------------------------------------------------
# Group comparisons
# ---------------------------------------------------------

top_fitness = [
    r["fitness_pct"]
    for r in top
]

control_fitness = [
    r["fitness_pct"]
    for r in controls
]

mw = mannwhitneyu(
    top_fitness,
    control_fitness,
    alternative="two-sided",
)

fisher = fisher_exact([
    [
        top_adequate,
        len(top) - top_adequate
    ],
    [
        control_adequate,
        len(controls)
        - control_adequate
    ]
])


# ---------------------------------------------------------
# Correlations
# ---------------------------------------------------------

mm_rho = spearmanr(
    [
        r["metamatch_score"]
        for r in rows
    ],
    [
        r["fitness_pct"]
        for r in rows
    ],
)

rank_rho = spearmanr(
    [
        r["candidate_rank"]
        for r in rows
    ],
    [
        r["fitness_pct"]
        for r in rows
    ],
)

redux_rho = spearmanr(
    [
        r["redux_metadata_pct"]
        for r in redux_rows
    ],
    [
        r["fitness_pct"]
        for r in redux_rows
    ],
)


# ---------------------------------------------------------
# Cluster bootstrap CIs
# ---------------------------------------------------------

adequacy_ci = bootstrap_anchor_cluster(
    rows,
    adequacy_difference
)

fitness_ci = bootstrap_anchor_cluster(
    rows,
    fitness_difference
)

mm_rho_ci = bootstrap_anchor_cluster(
    rows,
    metamatch_fitness_rho
)

rank_rho_ci = bootstrap_anchor_cluster(
    rows,
    rank_fitness_rho
)

redux_rho_ci = bootstrap_anchor_cluster(
    redux_rows,
    redux_fitness_rho
)


# ---------------------------------------------------------
# Anchor-level summaries
# ---------------------------------------------------------

anchors = sorted({
    r["anchor_slug"]
    for r in rows
})

anchor_lines = []

for anchor in anchors:
    subset = [
        r for r in rows
        if r["anchor_slug"] == anchor
    ]

    a_top = [
        r for r in subset
        if r["candidate_group"]
        == "framework_top5"
    ]

    a_control = [
        r for r in subset
        if r["candidate_group"]
        == "lower_rank_control"
    ]

    anchor_lines.append(
        (
            anchor,
            mean([
                r["fitness_pct"]
                for r in a_top
            ]),
            sum(
                r["adequate"]
                for r in a_top
            ),
            mean([
                r["fitness_pct"]
                for r in a_control
            ]),
            sum(
                r["adequate"]
                for r in a_control
            ),
        )
    )


# ---------------------------------------------------------
# Output
# ---------------------------------------------------------

lines = []

lines.append(
    "CAIS PROXY-FITNESS VALIDATION"
)
lines.append("=" * 60)
lines.append("")

lines.append(
    f"Total candidates: {len(rows)}"
)
lines.append(
    f"Framework top-5 candidates: "
    f"{len(top)}"
)
lines.append(
    f"Lower-ranked baselines: "
    f"{len(controls)}"
)
lines.append(
    f"Candidates with REDUX score: "
    f"{len(redux_rows)}"
)
lines.append("")

lines.append(
    "OVERALL ADEQUACY"
)
lines.append("-" * 60)

lines.append(
    f"Overall: "
    f"{overall_adequate}/{len(rows)} "
    f"({pct(overall_adequate, len(rows)):.1f}%)"
)

lines.append(
    f"Framework top-5: "
    f"{top_adequate}/{len(top)} "
    f"({pct(top_adequate, len(top)):.1f}%)"
)

lines.append(
    f"Lower-ranked baselines: "
    f"{control_adequate}/{len(controls)} "
    f"({pct(control_adequate, len(controls)):.1f}%)"
)

lines.append(
    f"Adequacy-rate difference: "
    f"{adequacy_difference(rows):.1f} percentage points"
)

lines.append(
    f"Cluster-bootstrap 95% CI: "
    f"[{adequacy_ci[0]:.1f}, "
    f"{adequacy_ci[1]:.1f}]"
)

lines.append(
    f"Fisher exact p: "
    f"{fisher.pvalue:.4f}"
)

lines.append("")
lines.append(
    "FITNESS SCORE COMPARISON"
)
lines.append("-" * 60)

lines.append(
    f"Top-5 mean fitness: "
    f"{mean(top_fitness):.1f}%"
)

lines.append(
    f"Top-5 median fitness: "
    f"{median(top_fitness):.1f}%"
)

lines.append(
    f"Baseline mean fitness: "
    f"{mean(control_fitness):.1f}%"
)

lines.append(
    f"Baseline median fitness: "
    f"{median(control_fitness):.1f}%"
)

lines.append(
    f"Mean fitness difference: "
    f"{fitness_difference(rows):.1f} points"
)

lines.append(
    f"Cluster-bootstrap 95% CI: "
    f"[{fitness_ci[0]:.1f}, "
    f"{fitness_ci[1]:.1f}]"
)

lines.append(
    f"Mann-Whitney U p: "
    f"{mw.pvalue:.4f}"
)

lines.append("")
lines.append(
    "ASSOCIATION WITH FITNESS"
)
lines.append("-" * 60)

lines.append(
    f"MetaMatch score vs fitness "
    f"(n={len(rows)}): "
    f"Spearman rho="
    f"{mm_rho.statistic:.3f}, "
    f"p={mm_rho.pvalue:.4f}, "
    f"95% cluster-bootstrap CI "
    f"[{mm_rho_ci[0]:.3f}, "
    f"{mm_rho_ci[1]:.3f}]"
)

lines.append(
    f"MetaMatch rank vs fitness "
    f"(n={len(rows)}): "
    f"Spearman rho="
    f"{rank_rho.statistic:.3f}, "
    f"p={rank_rho.pvalue:.4f}, "
    f"95% cluster-bootstrap CI "
    f"[{rank_rho_ci[0]:.3f}, "
    f"{rank_rho_ci[1]:.3f}]"
)

lines.append(
    f"REDUX metadata score vs fitness "
    f"(n={len(redux_rows)}): "
    f"Spearman rho="
    f"{redux_rho.statistic:.3f}, "
    f"p={redux_rho.pvalue:.4f}, "
    f"95% cluster-bootstrap CI "
    f"[{redux_rho_ci[0]:.3f}, "
    f"{redux_rho_ci[1]:.3f}]"
)

lines.append("")
lines.append(
    "ANCHOR-LEVEL SUMMARY"
)
lines.append("-" * 60)

for (
    anchor,
    top_mean,
    top_ok,
    control_mean,
    control_ok,
) in anchor_lines:

    lines.append(
        f"{anchor}: "
        f"top5 mean={top_mean:.1f}%, "
        f"adequate={top_ok}/5; "
        f"baseline mean={control_mean:.1f}%, "
        f"adequate={control_ok}/2"
    )


text = "\n".join(lines)

OUT.write_text(
    text,
    encoding="utf-8"
)

print(text)
print()
print("Wrote:", OUT)
