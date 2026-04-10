# Pilot Projected Pair Run

- Pairs generated: 10
- Target uncertain selected: 4
- Target uncertain required: 4
- API requests: 55
- API latency p95 (ms): 1314.2
- Total retries: 21
- Authenticated: yes
- Go/No-Go: NO-GO

## Decision Gates
- agreement_pearson: fail
- agreement_spearman: fail
- equivalence_or_directionality: pass
- uncertain_pair_coverage: pass
- api_health: pass

## Timing by stage
- control_rows: 0.0 ms
- discover_uncertain_pairs: 89799.1 ms
- stats: 3.6 ms
- step_load_benchmark: 4976.4 ms

## Step-load benchmark
- workers=1: throughput=1.32 req/s, p95=779.3ms
- workers=2: throughput=2.21 req/s, p95=1503.1ms
