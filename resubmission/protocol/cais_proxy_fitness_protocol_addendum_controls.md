\# CAIS Proxy-Fitness Protocol Addendum: Lower-Ranked Baselines



\## Purpose



This addendum clarifies the operational definition of the two comparison

repositories added for each anchor in the CAIS proxy-fitness validation.



\## Baseline Selection



For each anchor, the evaluation population contains:



\- the five framework-selected repositories from the frozen REDUX bridge; and

\- the final two distinct ranked repositories available in the corresponding

&#x20; frozen MetaMatch `30\_Matches.csv` candidate pool.



The lower-ranked repositories are selected solely from frozen retrieval rank

before CAIS fitness scoring.



No repository is selected, removed, or replaced based on its REDUX score,

rubric score, or expected downstream result.



\## Interpretation



These repositories are lower-ranked baselines, not presumed negative examples.



A lower-ranked baseline may still prove suitable under the independent CAIS

proxy-fitness rubric. Such a result is retained and interpreted as a boundary

case rather than treated as an error in the evaluation population.



Comparisons therefore test whether framework-selected top-ranked candidates

tend to have greater scenario-specific proxy fitness than repositories farther

down the same frozen retrieval pool.



\## Population



Eight anchors are evaluated.



Each anchor contributes:



\- 5 framework-selected candidates

\- 2 lower-ranked baselines

\- 7 repositories total



Across eight anchors, the frozen evaluation population contains 56

anchor-candidate observations.



Each candidate is evaluated against six predeclared anchor-specific

requirements, producing 336 requirement-level scoring rows.



