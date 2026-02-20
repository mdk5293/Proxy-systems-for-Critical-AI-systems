# PDF-to-Recommendations Analysis

## Context and sources analyzed
- `A_Taxonomy_of_Critical_AI_System_Characteristics_for_Use_in_Proxy_System_Testing.pdf`
- `IEEE PROOF Computer Software Column - v2.pdf`
- `NIST.CSWP.31.pdf`
- Implementation analyzed: `proxytool.ipynb`

## Coverage matrix by taxonomy dimension

| Dimension | Doc signal score | Code coverage score | Gap |
|---|---:|---:|---:|
| `physical_environment` | 1.00 | 0.00 | 1.00 |
| `application_purpose` | 0.89 | 0.00 | 0.89 |
| `operational_characteristics` | 0.94 | 0.00 | 0.94 |
| `ai_ml_algorithms` | 0.77 | 0.00 | 0.77 |
| `development_techniques` | 0.87 | 1.00 | 0.00 |
| `proxy_vnv_process` | 1.00 | 0.25 | 0.75 |

## Prioritized improvizations
- **P1** `physical_environment` (gap=1.00): Increase coverage depth for `physical_environment` signals and normalize feature naming across metrics.
  - Doc evidence: `IEEE PROOF Computer Software Column - v2.pdf` page 5 matched `land`
  - Code evidence: no direct signal found in current implementation.
- **P1** `operational_characteristics` (gap=0.94): Add an operational-characteristics metric family (risk markers, safety/criticality, failure-mode mentions, and runtime constraints), then include it in ALL_METRICS.
  - Doc evidence: `A_Taxonomy_of_Critical_AI_System_Characteristics_for_Use_in_Proxy_System_Testing.pdf` page 3 matched `operational characteristics`
  - Code evidence: no direct signal found in current implementation.
- **P1** `application_purpose` (gap=0.89): Increase coverage depth for `application_purpose` signals and normalize feature naming across metrics.
  - Doc evidence: `A_Taxonomy_of_Critical_AI_System_Characteristics_for_Use_in_Proxy_System_Testing.pdf` page 2 matched `application purpose`
  - Code evidence: no direct signal found in current implementation.
- **P1** `ai_ml_algorithms` (gap=0.77): Increase coverage depth for `ai_ml_algorithms` signals and normalize feature naming across metrics.
  - Doc evidence: `A_Taxonomy_of_Critical_AI_System_Characteristics_for_Use_in_Proxy_System_Testing.pdf` page 3 matched `algorithm`
  - Code evidence: no direct signal found in current implementation.
- **P1** `proxy_vnv_process` (gap=0.75): Add explicit proxy V&V process outputs (phase coverage, use/misuse-case traceability, and criticality indicators) to align with NIST CSWP-31.
  - Doc evidence: `NIST.CSWP.31.pdf` page 3 matched `five-phase process`
  - Code evidence: no direct signal found in current implementation.

## Next implementation steps (manual)
- Implement P1 items first, then rerun this analyzer to quantify gap reduction.
- Keep metric names consistent to improve registry discoverability and report explainability.
- Add tests/notebook checks that verify new metric keys appear in `ALL_METRICS` outputs.
