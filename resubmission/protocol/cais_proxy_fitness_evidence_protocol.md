\# CAIS Proxy-Fitness Evidence Collection Protocol



\## Purpose



This protocol defines how public repository evidence is collected and used

for CAIS proxy-fitness scoring.



The evidence procedure is identical for framework-selected candidates and

lower-ranked baselines.



\## Evidence Order



For every candidate repository, evidence is reviewed in the following order:



1\. GitHub repository description and topics

2\. Primary README

3\. Documentation linked directly from the repository

4\. Repository documentation folders

5\. Public examples, tests, configuration, or architecture material when

&#x20;  the preceding sources do not resolve a rubric requirement



The same evidence hierarchy is applied regardless of candidate rank,

MetaMatch score, REDUX score, or candidate group.



\## Scoring Rule



Each predeclared requirement is scored:



\- 0 = no evidence of support

\- 1 = partial or indirect support

\- 2 = strong or direct support



A score must be justified by repository evidence.



Absence of evidence is not converted into positive evidence through

inference from repository similarity, programming language, stars,

MetaMatch rank, REDUX score, or repository popularity.



\## Evidence Recording



For each nonzero score record:



\- evidence URL or repository-relative source

\- concise evidence note

\- score

\- labeler



For a zero score, record either:



\- "No supporting evidence found under evidence protocol", or

\- a source demonstrating that the requirement is outside the repository's

&#x20; documented function.



\## Blinding to Framework Scores



Rubric scoring should be performed without using MetaMatch score or REDUX

metadata percentage as evidence.



Candidate rank and candidate group are retained in the frozen dataset for

later analysis, but are not criteria for assigning rubric scores.



\## Consistency



The evaluator must not:



\- replace a candidate because it scores poorly

\- add a new candidate after scoring begins

\- redefine rubric requirements after observing candidate results

\- search more deeply for one candidate solely because its initial evidence

&#x20; is unfavorable

\- infer CAIS fitness directly from MetaMatch or REDUX similarity



\## Ambiguous Cases



When evidence is ambiguous:



\- prefer score 1 over score 2 when there is indirect but plausible support

\- prefer score 0 when no repository evidence supports the requirement

\- record the ambiguity explicitly in the evidence note



\## Second Review



Where feasible, ambiguous cases and critical-requirement scores should

receive a second review.



Disagreements should be retained and reconciled transparently rather than

silently overwritten.



