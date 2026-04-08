# Pilot Projected Pair Run

- Pairs generated: 6
- Target uncertain selected: 0
- Target uncertain required: 4
- API requests: 189
- API latency p95 (ms): 424.3
- Total retries: 304
- Go/No-Go: NO-GO

## Decision Gates
- agreement_pearson: pass
- agreement_spearman: pass
- equivalence_or_directionality: pass
- uncertain_pair_coverage: fail
- api_health: fail

## Step-load benchmark
- workers=1: throughput=0.16 req/s, p95=15935.5ms
- workers=2: throughput=0.15 req/s, p95=17672.8ms
- workers=4: throughput=0.66 req/s, p95=17585.7ms
- workers=8: throughput=0.54 req/s, p95=17993.3ms

## Important
- `GITHUB_TOKEN` is not set. Search API is heavily rate-limited and pilot is not representative.
