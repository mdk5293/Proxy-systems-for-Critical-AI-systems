\# Repository-Disjoint Holdout Evaluation Protocol



\## Purpose



This holdout evaluation is designed to assess whether the observed performance of

MetaMatch and REDUX generalizes beyond repositories used during method development,

configuration selection, or the existing labeled benchmark.



The holdout is constructed before examining method scores for the selected pairs.



\## Independence Requirement



A repository is ineligible for the holdout if that repository identity appears in:



1\. MetaMatch tuning or winner-selection artifacts.

2\. REDUX configuration/tuning artifacts used to select reported settings.

3\. The existing v2 labeled benchmark.

4\. Any benchmark pair used directly to select the final reported configuration.



Repository identity is evaluated by normalized repository owner/name.



Forks, mirrors, renamed repositories, or equivalent repository identities are treated

as overlapping when the relationship is known.



\## Target Cohort



Target size: 20–24 labeled pairs.



The intended cohort should contain examples from the following categories:



\- known\_match

\- known\_related

\- known\_non\_match



Target-uncertain pairs are not used for the primary classification metrics because

they do not have a defensible binary/related ground-truth interpretation.



The final class distribution will be reported explicitly.



\## Labeling Procedure



Labels must be assigned before MetaMatch or REDUX scores are inspected.



\### known\_match



Use only pairs for which there is strong external evidence of repository identity,

official mirroring, direct lineage, or another documented relationship that supports

a high-confidence match designation.



\### known\_related



Use repositories that have a documented functional, ecosystem, architectural, or

domain relationship but are not identity-equivalent.



\### known\_non\_match



Use repositories selected as plausible hard negatives rather than arbitrary trivial

unrelated pairs. They should be sufficiently substantive to provide a meaningful

test of discrimination.



\## Label Evidence



Each pair must record:



\- repository A

\- repository B

\- assigned label

\- label rationale

\- evidence type

\- evidence source

\- date of evidence review

\- repository-overlap check result



Where feasible, labels should be independently reviewed by a second evaluator.



\## Score Blindness



Repository-pair labels and inclusion decisions must be finalized before viewing the

new MetaMatch or REDUX scores.



No pair may be removed because its score is unexpected or reduces performance.



Exclusions after scoring are permitted only for predeclared technical reasons such

as repository unavailability, API failure, or insufficient evidence, and every such

exclusion must be documented.



\## Primary Evaluation



Primary evaluation will report:



\- cohort composition

\- precision

\- recall

\- F1

\- confusion matrix

\- 95% stratified bootstrap confidence intervals



Strict evaluation:

\- positive = known\_match

\- negative = known\_non\_match



Lenient evaluation:

\- positive = known\_match + known\_related

\- negative = known\_non\_match



The threshold used for the existing benchmark will remain fixed for the holdout.

It will not be retuned using holdout results.



\## Secondary Analysis



Where appropriate, results may also report:



\- method-specific errors

\- false-positive and false-negative examples

\- score distributions

\- agreement between scoring approaches



These analyses are secondary and will not be used to alter the frozen primary

evaluation rules.



\## Interpretation



The holdout evaluates generalization of repository-relatedness and software-similarity

scoring to previously unseen repository identities.



Successful holdout performance does not by itself establish scenario-specific CAIS

proxy fitness. Proxy fitness requires separate task/domain validation.



