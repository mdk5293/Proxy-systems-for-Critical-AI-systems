# Pilot Projected Pair Run

- Pairs generated: 10
- Target uncertain selected: 4
- Target uncertain required: 4
- API requests: 73
- API latency p95 (ms): 681.4
- Total retries: 84
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
- discover_uncertain_pairs: 219537.1 ms
- stats: 12.4 ms
- step_load_benchmark: 69775.9 ms

## Step-load benchmark
- workers=1: throughput=1.64 req/s, p95=666.0ms
- workers=2: throughput=0.09 req/s, p95=50561.8ms

## Important
- `GITHUB_TOKEN` is not set. Search API is heavily rate-limited and pilot is not representative.
