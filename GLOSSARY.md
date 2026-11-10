# AstraGo research

A controlled study of selecting Go positions for a pretrained student, with offline play as its deployment setting.

## Language

**Teacher**: The frozen expert Go model and declared analysis settings used to supply numerical supervision. Its estimates are evidence with bounded search, not ground truth.
_Avoid_: Astra as numerical teacher

**Student**: The shared pretrained Go model whose continuation learning is compared across selection arms.

**Selector**: A method that chooses legal positions from the common candidate pool under a declared information and cost budget.

**Astra proposal**: A reproducible selection rule or curriculum suggested from allowed development evidence. It is neither a numerical label nor proof of move quality.

**Development set**: Positions available for diagnosing errors, designing selection and tuning the experiment before the final evaluation.

**Sealed test set**: Held-out games and their positions reserved for final evaluation, inaccessible to selection and tuning.

**Matched-budget comparison**: A comparison that equalizes the declared teacher-labeling and training budgets across arms.

**Full-cost comparison**: A comparison that also accounts for screening, selection, API use, data movement and evaluation.

**Deployment success**: A tested Go engine that plays locally within the agreed M4 time and memory limits.

**Research success**: An interpretable controlled result about Astra’s marginal selection value, including a well-supported null or inconclusive result.
_Avoid_: Claiming novelty from an inherited architecture
