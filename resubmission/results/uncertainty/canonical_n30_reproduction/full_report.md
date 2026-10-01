# Full Projected Pair Run

- Pairs generated: 30
- Target uncertain selected: 10
- Target uncertain required: 10
- API requests: 53
- API latency p95 (ms): 913.0
- Total retries: 10
- Authenticated: yes
- Go/No-Go: GO

## Decision Gates
- agreement_pearson: pass
- agreement_spearman: pass
- equivalence_or_directionality: pass
- uncertain_pair_coverage: pass
- api_health: pass

## Timing by stage
- control_rows: 0.0 ms
- discover_uncertain_pairs: 71515.6 ms
- stats: 17.6 ms
- step_load_benchmark: 9440.0 ms

## Step-load benchmark
- workers=1: throughput=0.64 req/s, p95=1595.1ms
- workers=2: throughput=1.26 req/s, p95=1717.2ms
