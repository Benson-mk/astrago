# Admission failure scenarios for issue #14

Specified before runtime implementation. The sole E2E seam is the public
`tools/campaign.py` CLI, confirmed by the operator on 2026-11-11. Synthetic
rejection records are never real development fixtures or native-success evidence.

| Failure | Required observable outcome |
| --- | --- |
| Runtime requested without separate campaign instruction | Reject before acquisition, build or replay; preserve existing H0 and stop |
| Missing, skipped, extra or out-of-range archive | Reject; begin November 6 and expand descending only through November 1 while declared score-free counts fall short |
| Wrong/missing rules, komi, size, handicap, setup, origin or ancestry | Reason-coded source exclusion with original bytes retained |
| Malformed SGF, illegal move, nonalternating move, move after native terminal | Native exclusion; never use tolerant replay or score estimates as termination |
| SGF branch handling silently selects longest branch | Reject verification; main line is first child in recorded order |
| Positive training start index with full ordinary history | Do not mistake training start metadata for missing history |
| Full histories differ but visible board agrees | Distinct candidate identities; board-only manifests rejected |
| Rotated/reflected duplicate | One complete-game identity with source orientation aliases; colors never exchanged |
| Verified ancestor relationship | Same family; unresolved ancestor excluded; shared openings never join families |
| Duplicate candidate across splits | Sealed wins over development over training; retain exclusion counts and aliases |
| Input order changes or offline replay | Same canonical identities, assignments and exclusion counts; changed retained evidence fails |
| Required counts cannot fit bounded source range/capacity | Incomplete gate with exact shortfalls; no model-score-based expansion |
| Fewer than 32 playable development histories or coverage absent | Exact unavailable categories; no sealed or fabricated fixtures |
| Selector/debug consumer requests sealed data | Deny through the registered consumer gateway; evaluator evidence stays outside consumer inputs |
| Same OS identity used for evaluator and consumer | Use the explicitly approved workflow gateway and record os_unreadability=false; never claim an OS security boundary |
| Source/manifest changes after sealing | Reject; no untouched-seal claim |
| Failed/interrupted replay or missing software/config identity | Failed/inconclusive artifact with measured attempts, never a passing native gate |
| Unknown acquisition/billing cost | Explicit unknown, never zero |

Required fixture coverage: opening, quiet midgame, capture/atari, immediate ko,
legal later recapture, identical stones with different history/legal context,
single pass, late endgame, seki, both players and asymmetric coordinates. Two-pass
termination is a separate development terminal check. No-result probability and
perspective checks belong to the downstream target gate, not invented SGF labels.

All outputs must state continuation-disjointness only. No fresh GPU/Astra
bit-identity claim follows from deterministic offline replay.

## User-approved single-account workflow revision (2026-11-11)

Before implementing the revised access boundary, exercise these runner E2E cases:
registered training/development references succeed; the same training ID may be
read for A and B; a supplied raw/all-source/sealed path is denied before reading
it; a sealed ID or split is denied; an altered registered export is denied;
evaluation is denied without an implemented final model/configuration freeze;
any supplied arm-state reference is rejected at this data-only boundary, including
B state presented for A. Every request retains an immutable allow/deny record.
Legacy OS-access receipts cannot become workflow passes. Same-account direct file
reads or code/registration changes remain possible and are not OS isolation.

Archive-prefix continuation: an insufficient supplied prefix with approved dates
remaining must retain native evidence and name the next date without producing
sources-frozen.json, split inventory or public exports. A fresh immutable attempt
may include that next archive; no provisional split may guide expansion.

A workflow receipt with correct event hashes but a denial attached to the wrong
probe case must fail before fixture review. A software revision needs a fresh
probe for advancement; offline historical verification uses the retained software
identity. Ordinary new access records must not invalidate an earlier artifact.
