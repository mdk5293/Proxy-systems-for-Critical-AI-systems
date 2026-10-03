\# Robustness and Ablation Protocol



\## Purpose



This experiment evaluates whether the framework's reported behavior depends

materially on particular feature families, parameter choices, commit-history

windows, normalization choices, thresholds, or metadata availability.



The experiment is intended to characterize robustness and failure modes.

It is not intended to identify a new parameter configuration after observing

test results.



\## Evaluation Principle



All robustness conditions are defined before executing the experiment.



The existing reported configuration remains the reference configuration.

No robustness result will be used to retune the reference configuration or

replace an unfavorable result.



\## Evaluation Outputs



Each condition will be compared with the frozen reference configuration using,

where applicable:



\- pair-level classification performance

\- precision

\- recall

\- F1

\- accuracy

\- ranking stability

\- Spearman rank correlation

\- top-k candidate overlap

\- scenario/candidate selection stability

\- failure count

\- missing-value behavior



Results will be reported as sensitivity analysis rather than as additional

parameter tuning.



\## Part A: Feature-Family Ablation



Evaluate the reference configuration and variants in which one feature family

at a time is removed.



The exact feature families will be derived from the implemented scoring code

before execution and recorded in the experiment manifest.



No new feature family or compensating weight will be introduced during an

ablation run.



\## Part B: Weight Perturbation



For each implemented feature family, evaluate moderate perturbations around

the frozen reference weight.



Planned perturbation:



\- reference weight

\- -20 percent

\- +20 percent



Weights will not be optimized against the evaluation benchmark.



If the implementation requires normalization after perturbation, the same

normalization rule will be applied consistently to every condition.



\## Part C: Commit-History Window Sensitivity



Evaluate the implemented code/dynamic-history components using frozen history

windows of:



\- 50 commits

\- 150 commits

\- the currently reported/default configuration or blend



The same repository population will be used in each condition.



\## Part D: Normalization Sensitivity



Evaluate the normalization strategy or strategies already supported by the

implementation.



The available strategies will be identified from source code before execution.

Unsupported normalization methods will not be introduced solely for this

experiment.



\## Part E: Threshold Sensitivity



Evaluate classification/decision behavior around the frozen threshold.



At minimum, report the frozen threshold plus reasonable lower and upper

sensitivity points that do not require model retuning.



The exact thresholds will be frozen in the experiment manifest before

execution.



\## Part F: Missing Metadata / API-Dependent Fields



Evaluate controlled missingness for metadata or API-dependent fields used by

the framework.



At minimum:



\- reference data availability

\- removal of one API-dependent field/family at a time where feasible

\- combined missing-metadata condition where supported



Missingness must be simulated consistently across the evaluation population.



\## Dataset Separation



Robustness experiments use the already frozen evaluation artifacts and do not

alter benchmark labels, holdout membership, CAIS rubrics, or candidate

selection after results are observed.



The repository-disjoint holdout remains separate from any development or

parameter-selection data.



\## Interpretation



Robustness is supported when conclusions remain qualitatively stable across

reasonable perturbations.



A degradation under an ablation is interpreted as evidence that the removed

feature contributes useful information.



A large change under a small parameter perturbation is interpreted as a

sensitivity or limitation rather than hidden through retuning.



The experiment does not establish universal robustness outside the tested

conditions.



