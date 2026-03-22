# Proxytool: Metadata-Driven Proxy Discovery for Critical AI Systems (CAIS)

Executable research code aligned with:

**Mark Kennedy, Joanna F. DeFranco & Philip A. Laplante**,  
*“Discovering Proxy Systems to Test Critical AI Systems: A Metadata-Driven Software Similarity Approach”* (IEEE Computer, 2026).

This README is the long-form map from **paper → implementation**.
---

## Why this exists

Teams need **safety-oriented evidence** for Critical AI Systems (CAIS), but the real system is often behind **NDAs, export controls, or operational secrecy**. You still have to argue that an **open-source proxy** is a plausible **behavioral stand-in** for the CAIS you cannot inspect.

**“Pick a similar GitHub repo” is not a strategy**—it is a guess. Stars, topics, and vague similarity do not answer: *Does this proxy match the risk and validation dimensions we care about?* You also need more than a leaderboard: a bridge from **ranked repos** to **what we would actually test**.

This project implements **multi-signal similarity**, **explicit taxonomy alignment** (NIST-style CAIS dimensions), and a path from **ranking → scenario-backed test planning**—so the story can survive review, not just look good on a chart.

---

## What this repository is

This is an **executable extension of the paper**, not a one-page demo. The main artifact is **`proxytool.ipynb`**: one notebook that wires the full loop:

**config → data pull → features → similarity → validation → plots → test plans.**

Outputs include `results_plots/`, `validation_results.csv`, and (when you run those cells) structured proxy test plans.

---

## Paper figures → code (Figures 2 & 3)

### Figure 2 — Six-step pipeline (end-to-end in `proxytool.ipynb`)

| Step | What happens | Primary symbols / entry points |
|------|----------------|--------------------------------|
| 1 | Anchor per-domain CAIS profiles (NIST 5D–style dimensions) | `CAIS_DOMAIN_CONFIGS` |
| 2 | Discover or fix candidate sets | GitHub discovery via `DISCOVERY_QUERIES`; `run_discover_and_compare(...)` |
| 3 | Extract **behavioral fingerprints** from **public Git metadata** (not proprietary source) | Four indicator families (below) |
| 4 | Normalize + weight features | `CAIS_WEIGHTS`, tuning helpers such as `tune_weights` |
| 5 | Score + rank | Weighted vectors + **cosine similarity** |
| 6 | Validate taxonomy alignment | Overall vs taxonomy-restricted similarity; `compare_taxonomy_vs_standalone(...)`, `_taxonomy_similarity_report(...)` |

![Figure 2: Six-step proxy discovery pipeline](assets/figure2.png)

### Figure 3 — Similarity → taxonomy validation → proxy selection → test campaigns

- **Failure-mode scenarios per domain:** `CAIS_TEST_SCENARIOS`
- **Structured plans:** `plan_proxy_tests(...)`, `print_proxy_test_plan(...)`

The notebook turns ranked proxies into **scenario-backed test campaign sketches** mapped to **indicator families**—the paper’s safety loop, operationalized in code.

![Figure 3: Similarity → taxonomy validation → proxy test planning](assets/figure3.png)

---

## The 11 CAIS domains (`CAIS_DOMAIN_CONFIGS`)

Each domain is a separate **world**: its own anchor repo, candidate set, expected high-similarity proxies, controls, and NIST-style profile. The same pipeline is stress-tested across heterogeneous, high-stakes settings—not a single vertical toy example.

| # | Domain key | Intuition |
|---|------------|-----------|
| 1 | `autonomous_driving` | Road autonomy / perception–planning style systems |
| 2 | `medical_ai` | Clinical / imaging ML style stacks |
| 3 | `robotics` | ROS-class navigation & integration ecosystems |
| 4 | `aerial_autonomy` | PX4 / flight-stack style autonomy |
| 5 | `financial_risk` | Credit / risk-scoring ML (high-stakes decisions) |
| 6 | `industrial_robotics` | Arms, motion, industrial automation stacks |
| 7 | `recommender_systems` | Large-scale ranking / recsys codebases |
| 8 | `security_identity` | IAM / auth / identity-heavy systems |
| 9 | `content_moderation` | Moderation / policy-enforcement style ML |
| 10 | `public_sector_fairness` | Fairness / public-sector ML risk framing |
| 11 | `cybersecurity_threat_detection` | IDS / SIEM / threat-detection style systems |

---

## What the notebook actually does

The workflow is **layered**: shallow smoke tests or deep research runs.

- **Static vs discovery paths** — Fixed candidate lists (reproducible) or GitHub discovery per domain.
- **Multi-domain sweeps** — e.g. `run_all_domain_suites`, `run_discover_and_compare` across configured domains.
- **Weight learning** — `tune_weights(...)` per domain to search family-level weights against expected proxy lists.
- **Taxonomy vs standalone** — `compare_taxonomy_vs_standalone`: A/B between taxonomy-augmented metric bundles and a baseline set (the paper’s “does taxonomy help?” claim in code).
- **Separation analysis** — `domain_vs_control_analysis`: do domain peers separate from controls (sanity check that signal isn’t random).
- **Baseline triangulation** — `side_by_side_comparison`, `deep_code_similarity`, `code_clone_similarity`, `dynamic_behavior_similarity`: metadata similarity vs lightweight public-metadata baselines.
- **Method agreement** — `correlate_methods`: Spearman correlations across Metadata / CodeClone / Behavioral / DeepCode.
- **Safety-loop artifacts** — `plan_proxy_tests`, `print_proxy_test_plan`: ranked proxies → scenario-backed sketches (Figure 3).
- **Reporting** — Plots under `results_plots/`; `validation_results.csv` for tabular outcomes and regression-style checks.

Together, this is **repeatable experiments, ablations, and cross-domain checks** on top of the paper.

---

## Four indicator families (“metadata-only” signals)

What public metadata is actually measuring:

1. **Commit semantics** — Intent/sentiment; optional **sentence-transformer** embeddings when `sentence-transformers` is installed.
2. **Contributor behavior** — Collaboration / authorship-style signals from commit history.
3. **File change histories** — Co-change + churn from commit numstat and file-graph-style signals.
4. **Temporal evolution** — Development rhythm, cadence, burstiness.

---

## Taxonomy + metrics (not “just embeddings”)

- **`CAIS_METRICS`** bundles the paper’s indicator families with explicit **NIST 5D** taxonomy dimensions (environment, purpose, operational O1–O5, algorithm, language) so similarity is not only “commit-text similarity.”
- The evaluation path contrasts **taxonomy-augmented similarity** vs **standalone** metric sets—i.e. the paper’s accuracy claims, expressed as runnable comparisons.

---

## Baselines & robustness checks

- **Domain vs control** — Quantify separation between domain peers and controls (not isolated high scores).
- **Side-by-side comparison** — Metadata similarity vs code-structure / behavioral / deep-readme+tree style baselines.
- **Rank correlations across methods** — `correlate_methods` (Spearman): when different views agree or diverge.

---

## Tech stack

- Python, **GitHub REST API**, `requests`
- Feature normalization + **weighted cosine similarity**
- **matplotlib**, **scipy** (rank correlations)
- **sentence-transformers**, **vaderSentiment** (optional / graceful fallback)
- Historical note: a **CLI** (`proxytool.py`) and **PowerShell** harness were used in some workflows for batch plots; the canonical path today is the notebook—check the repo for what is currently tracked.

---

## Optional “meta” tooling

- **`scripts/proxy_doc_analyzer.py`** — PDF/taxonomy-driven gap notes vs the implementation (research hygiene, traceability). Generated notes may live under `analysis/` locally (often gitignored).

---

## Proof points

| Artifact | Role |
|----------|------|
| `proxytool.ipynb` | Full pipeline: discovery → evaluation → test-plan output |
| `README.md` | Paper ↔ code mapping (this file) |
| `results_plots/` | Saved figures for comparisons and talks |
| `validation_results.csv` | Summarized runs across domains / settings |

**After your next full run**, add 1–2 quantitative bullets (e.g. taxonomy-augmented MRR vs `BASE_METRICS` on a domain; Spearman ρ between Metadata and DeepCode)—reviewers and recruiters scan for numbers.

---

## Research insight

The hardest part is not “compute a similarity score.” It is making the pipeline **CAIS-aligned**: rankings **explainable against taxonomy dimensions**, and ranked proxies connected to **how you will test**. If the proxy story does not connect to test strategy, it will not pass a safety review—even if the leaderboard looks good.

---

## Honest scope (what metadata does and doesn’t do)

The foundation is intentionally honest:

- **Git metadata** captures **development behavior**, not full runtime semantics.
- **Discovery quality** reflects real **GitHub search and API** behavior.
- **Embeddings** use general-purpose sentence models unless you plug in something stronger.

The **LOOKING AHEAD** section below is how we **tighten the science** without pretending runtime behavior was fully measured from metadata alone.

---

## LOOKING AHEAD

This work already shows what metadata-only similarity can do; the exciting part is what comes next—deeper signals, stronger baselines, and real-world CAIS studies.

The foundation is intentionally honest: Git metadata captures development behavior (not full runtime semantics), discovery quality tracks GitHub search and API realities, and embeddings use general-purpose sentence models today—so the roadmap below is how we tighten the science without pretending we already measured everything.

- **Richer dynamic baselines** — where CI and test artifacts are public, layer in pass/fail distributions, coverage overlap, and execution-aware signals alongside Git metadata.
- **Cross-language code understanding** — upgrade the code-centric view with models like CodeBERT / UniXcoder on carefully sampled public files (with clear licensing discipline).
- **Ensemble scoring** — fuse metadata similarity, behavioral signals, and code-centric views into a single multi-view score with explicit uncertainty.
- **Temporal calibration** — track how proxy rankings drift as repositories evolve; refresh rankings and flag when a proxy diverges from the CAIS fingerprint.
- **Industrial & regulated CAIS** — extend the same harness to proprietary or restricted domains (defense, energy, transportation) where only metadata can be shared—exactly where proxy testing matters most.
- **Ground-truth expansion** — grow per-domain validation pairs and rubrics so weight tuning and taxonomy-vs-standalone claims stay statistically grounded as the harness scales.

---

## How to run

1. **GitHub token:** `export GITHUB_TOKEN=...` (or use a `.env` file as described in the notebook; never commit secrets).
2. **Dependencies** (not all required for every cell):
   ```bash
   pip install requests tqdm matplotlib ipython scipy sentence-transformers vaderSentiment
   ```
3. Open and run **`proxytool.ipynb`**.

If `sentence-transformers` is missing, optional embedding cells degrade gracefully.

---

## Repository layout

| Path | Purpose |
|------|---------|
| `proxytool.ipynb` | Canonical research pipeline |
| `scripts/proxy_doc_analyzer.py` | Taxonomy/PDF-oriented analysis helper |
| `assets/` | Paper-related PDFs, figures (`figure1.png`–`figure3.png`), supporting docs |
| `results_plots/` | Curated or regenerated plots (may be gitignored locally) |
| `validation_results.csv` | Tabular evaluation summaries |

---

## References & assets (in `assets/`)

- `Discovering_Proxy_Systems_to_Test_Critical_AI_Systems_A_Metadata-Driven_Software_Similarity_Approach.pdf`
- `IEEE PROOF Computer Software Column - v2.pdf`
- `NIST.CSWP.31.pdf`
- `A_Taxonomy_of_Critical_AI_System_Characteristics_for_Use_in_Proxy_System_Testing.pdf`
- `CAIS-NIST.docx`

---

## Collaboration

If you work on **safety evaluation**, **test strategy**, or **AI governance under source constraints**, feedback and collaboration ideas are welcome. Use the repo’s Issues/Discussions if enabled, or reach out directly.
