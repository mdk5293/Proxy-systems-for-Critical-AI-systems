# Full Projected Pair Run

- Pairs generated: 30
- Target uncertain selected: 10
- Target uncertain required: 10
- API requests: 79
- API latency p95 (ms): 643.0
- Total retries: 105
- Authenticated: no
- Go/No-Go: NO-GO

## Decision Gates
- agreement_pearson: fail
- agreement_spearman: fail
- equivalence_or_directionality: pass
- uncertain_pair_coverage: pass
- api_health: pass

## Timing by stage
- control_rows: 0.0 ms
- discover_uncertain_pairs: 218263.9 ms
- stats: 15.7 ms
- step_load_benchmark: 70291.2 ms

## Step-load benchmark
- workers=1: throughput=1.54 req/s, p95=657.9ms
- workers=2: throughput=0.09 req/s, p95=67322.4ms

## Important
- `GITHUB_TOKEN` is not set. Search API is heavily rate-limited and pilot is not representative.
