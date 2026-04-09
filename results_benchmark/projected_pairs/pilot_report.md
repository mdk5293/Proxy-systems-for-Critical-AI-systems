# Pilot Projected Pair Run

- Pairs generated: 6
- Target uncertain selected: 0
- Target uncertain required: 4
- API requests: 15
- API latency p95 (ms): 570.5
- Total retries: 0
- Go/No-Go: NO-GO

## Decision Gates
- agreement_pearson: pass
- agreement_spearman: pass
- equivalence_or_directionality: pass
- uncertain_pair_coverage: fail
- api_health: pass

## Step-load benchmark
- workers=1: throughput=1.18 req/s, p95=882.6ms

## Important
- `GITHUB_TOKEN` is not set. Search API is heavily rate-limited and pilot is not representative.
