# AstraGo research

A controlled study of selecting Go positions for a pretrained student, with offline play as its deployment setting.

## Language

**Teacher**: The frozen expert Go model and declared analysis settings used to supply numerical supervision. Its estimates are evidence with bounded search, not ground truth.
_Avoid_: Astra as numerical teacher

**Student**: A Go model initialized from the common pretrained checkpoint and continued within one selection arm.

**Selection arm**: An experimental condition defined by a position-selection method and the student learning from its selections.

**Selector**: A method that chooses legal positions from the common candidate pool under a declared information and cost budget.

**Selection round**: One cycle of choosing training positions and continuing an arm's student on selected data.

**Adaptive curriculum**: A sequence of position selections informed by feedback from the student's learning.

**Cumulative training set**: The union of an arm's selected positions across its selection rounds.

**Game family**: A source game together with its duplicate records and related variations or descendants. Shared opening moves alone do not establish a common family.

**Search-policy target**: A move distribution formed by normalizing the frozen teacher's search edge visits, including pass. It is the study's declared distillation target, not a claim of equivalence to native self-play targets.

**Raw-value target**: The frozen teacher network's pre-search win, loss and no-result probabilities for a position, expressed from the player-to-move perspective.

**Astra proposal**: A structured position-selection specification suggested from allowed development evidence. It is neither a numerical label nor proof of move quality.

**Development set**: Positions available for diagnosing errors, designing selection and tuning the experiment before the final evaluation.

**Sealed test set**: Held-out games and their positions reserved for final evaluation, inaccessible to selection and tuning.

**Continuation-disjoint holdout**: A held-out set whose games and related variations are excluded from continuation training and selection or tuning. It makes no claim that the pretrained student has never encountered those games.

**Pretraining-clean holdout**: A held-out set with evidence that its games and related variations were absent from the student's pretraining data, in addition to being continuation-disjoint.

**Matched-budget comparison**: A comparison that equalizes the declared teacher-labeling and training budgets across arms.

**Full-cost comparison**: A comparison that also accounts for screening, selection, API use, data movement and evaluation.

**Deployment success**: A tested Go engine that plays locally within the agreed M4 time and memory limits.

**Research success**: An interpretable controlled result about Astra’s marginal selection value, including a well-supported null or inconclusive result.
_Avoid_: Claiming novelty from an inherited architecture
