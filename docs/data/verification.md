# Issue #14 verification ledger

The approved November 6–1 source range is exhausted: all 324,285 SGF records
were excluded, leaving zero admitted families and candidates. The source artifact
is `incomplete`, with `advance: false`. No real development fixture seal,
populated holdout or successful downstream campaign is claimed.

Issue #14 explicitly permits an exact unavailable-category report as an unmet
gate. Its implementation acceptance combines native synthetic diagnostics of the
nonempty transformation mechanics with verification of this actual bounded-empty
outcome. Parent #12's source, fixture and successful-campaign gates remain unmet.
Changing the adopted source/rules contract requires an explicit replan.

## Acceptance evidence

- [x] Supported failure scenarios were recorded before implementation and verified
  through the public campaign-runner CLI; no post-implementation unit tests.
- [x] Actual November 6–1 eligibility/expansion completed; all real records were
  excluded by native board-size or exact rules/komi checks. Separate native
  synthetic diagnostics cover ordinary-origin admission, setup, illegal moves
  and post-terminal rejection. Every real exclusion is retained.
- [x] Full colored-history spatial identity, provenance and ancestry/family mechanics
  verified by native synthetic diagnostics; actual source inventory is empty.
- [x] Frozen hash-order split and duplicate priority verified on nonempty synthetic
  histories; two real offline replays reproduce identical empty inventories and exclusions.
- [x] Exact unavailable-category fallback verified: 0/32 playable histories,
  all twelve categories unavailable and zero terminal fixtures; fixture gate remains unmet.
- [x] Actual registered consumer access and original-archive denials verified,
  with synthetic sealed-ID/altered-export checks under the approved workflow boundary.
- [x] Source, extraction, native, exclusion and storage evidence retained; only
  continuation-disjointness is claimed, with unknown pretraining exposure.
- [x] Content-addressed E2E evidence retains inputs, outputs, software/configuration,
  commands, costs and the exact incomplete outcome; deterministic offline checks pass.

## Real source outcome

Archives were acquired in descending order only after the preceding unassigned
prefix reported insufficient score-free eligibility. No model scores guided
expansion. The original H0 remains `2026-11-11T08:02:12.601447+00:00`; the stopped
native parent was preserved. The approved execution comprised acquisition,
native build/replay and access/E2E checks. No inference, training or evaluation
was run.

| Cumulative dates | Records | Board-size exclusions | Exact rules/komi exclusions | Eligible families/candidates | Stage seconds | Campaign snapshot bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| November 6–5 | 111,703 | 44,073 | 67,630 | 0 / 0 | 1,752.053 | 19,190,934,271 |
| November 6–4 | 167,746 | 65,865 | 101,881 | 0 / 0 | 2,643.104 | 23,931,468,102 |
| November 6–3 | 224,229 | 88,136 | 136,093 | 0 / 0 | 3,552.787 | 30,363,103,702 |
| November 6–2 | 277,174 | 108,934 | 168,240 | 0 / 0 | 4,543.922 | 38,445,748,265 |
| November 6–1 | 324,285 | 127,489 | 196,796 | 0 / 0 | 5,385.214 | 48,072,705,015 |

Stage seconds precede final artifact packaging. Prefix storage includes retained
prior attempts. Acquisitions retain URL/date, original bytes, SHA-256, retrieval
time and measured duration; terms/README/disclaimer evidence is retained too.
Billing remains unknown, not zero. Final artifact size is 944,699,100 bytes;
its data-stage snapshot including the empty public export is 9,034,677,536 bytes.
The final post-E2E inventory measured **48,790,112,341 bytes** (45.44 GiB),
below the **53,687,091,200-byte (50 GiB)** ceiling. This snapshot includes
ancillary E2E/access/export evidence and precedes writing the small evidence index.

The metadata-only November 6 screen was not admission evidence. Apparent matching
legacy rules omit adopted Chinese fields `whiteHandicapBonus=N` and
`friendlyPassOk=true`; pinned native parsing preserves that distinction. Rules
were not relaxed to manufacture an eligible corpus.

| Required capacity | Observed | Required floor |
| --- | ---: | ---: |
| Training candidates | 0 | 2,304 |
| Development candidates | 0 | 384 |
| Development families | 0 | 96 |
| Sealed candidates | 0 | 384 |
| Sealed families | 0 | 96 |

These are declared feasibility floors, not a frozen production workload N.
Playable development histories are **0 of 32**, with **zero eligible terminal
checks**. All twelve categories are unavailable: opening, quiet midgame,
capture/atari, immediate ko, later legal recapture, same stones with different
history, single pass, late endgame, seki, Black to move, White to move and
asymmetric coordinates. No sealed or fabricated history fills these gaps.

## Verification and retained artifacts

The final full public-runner suite ran nine tests in 1,244.149 seconds:
**seven passed and two were explicitly skipped**. mypy 1.19.1 passed all nine
Python source/test files. Current local tool sources match the hashes recorded
by the passing bounded-empty E2E.

- Real bounded-empty E2E:
  `9a4e27152b619cde5de1fe342186da11b740495326f170befd90e95b5aed3953`.
  It verifies all six frozen dates, exact shortages/unavailable coverage, two
  identical offline results, actual empty registered reads, original-archive
  path denials and refusal to advance fixture freezing with a genuine receipt.
- Final native synthetic E2E:
  `16578aae39c0d75ea8d95f167cb6c250b51276872bc4da3a6207efdb04408218`.
- Receipt-tampering and ordinary consumer-access cases both passed in the final
  suite; their content-addressed receipts are included in the final evidence index.
- Real receipt-tampering E2E:
  `51854c93bd884989d368942324b87f916b99a656bdb3c35aa6d4f675097601d0`.
- Final content-addressed evidence index (including verified source artifact
  hashes, measured storage, suite output and E2E references):
  `3cce163b58a94423ee3a3945ccdb77e9cbd9acb6ed67dc4317fbdffa6b5b144f`.

The source artifact is
`40fa311e6f6f5303d24a8653ee6908b3d5e1abac683f70fd838d5c9e88521302`.
It retains original SGFs, extraction/native responses, reason-coded exclusions,
empty family/candidate manifests, exact configuration/software identities,
commands and measured costs. Large evidence remains on the training host;
compact evidence is copied to ignored `.local/issue-14/runtime-bounded-verified/`.
Credentials and private connection information are excluded from this commit.

Offline verification checks retained bytes, extraction/native-result consistency,
canonical identities, assignments and exclusions in both input orders. Two real
replays establish the same empty result; they do not establish a populated
holdout or fresh GPU/Astra bit identity. Nonempty native synthetic diagnostics
separately verify legality rejection, first-child mainline, symmetry without
color exchange, ancestry, input order, split priority, board-only rejection and
cross-split rejection. Synthetic cases are never real development fixtures.

The positive retained-corpus E2E remains strict and explicitly skipped because
there is no passing fixture-frozen corpus. The insufficient-prefix case is
explicitly skipped in the final suite to avoid repeating its already retained,
matching-runtime passing run:
`805e3afdebed61bfb7a3cdc8b4757ee59ac224c21e3490007fe9f0063513bfbe`.
Mandatory diagnostics used for the final admission were
`efa4e83b2e867293b84df10fa7938e71dd4d5b3922b2575b5bd15683bb100fde`.

## Isolation and limits

The user explicitly replaced the unavailable separate-account prerequisite with
same-account, auditable runner workflow isolation. Actual registered empty
training/development reads and denied sealed/evaluator/raw-source routes are
checked through the public CLI. Synthetic nonempty access E2E additionally
checks sealed IDs, altered exports and cross-arm/unsupported arm-state requests.
Immutable allow/deny records and exact export registrations support offline audit.

`os_unreadability` is false. Direct filesystem reads and code/registration bypass
remain possible for the same account. No OS isolation or absence-of-bypass claim
is made. Final evaluation stays denied pending its actual model/configuration
freeze. Data is continuation-disjoint only; pretraining exposure is unknown.

## Historical attempts and review

The first build failed because the separate source copy omitted required Git
metadata. The corrected copy built successfully; the failed attempt remains
retained. The historical sudo denial remains a denial, superseded only by the
user-approved workflow contract. The old-code November 6 attempt
`7093117f8944506124049e373aff7b4bf4e24d69394de78f56928cecd9dbfbc2`
prematurely created an empty split and is superseded diagnostic evidence. Only
its score-free shortfall justified expansion. Corrected partial prefixes remain
unassigned and produce no public exports. The SSH interruption was recovered by
inspecting the surviving job, without redispatch or H0 reset; interruption artifact
`d17658d493ba0c74206b1d548ce130d919a7cc54501d53ea4b3c1bd6d3ed4c88`
remains historical evidence.

Standards and Spec reviews closed with zero remaining findings, including the
final bounded-empty E2E. The BDFL advisor independently confirmed the explicit
unavailable-category acceptance fallback and the distinction between completed
implementation verification and the unmet parent campaign gate. Failure scenarios
and runner regressions preceded their corresponding implementation/repairs;
no post-implementation unit tests were added. The fourteen actual trade-offs are
recorded in [README.md](README.md) and were reported to the user; final verification
introduced no additional trade-off.
