# Legal data and teacher-target evidence for AstraGo

Retrieved and inspected: 2026-11-10 (Asia/Hong_Kong). Research ticket: **Which legal data and teacher targets can enter KataGo continuation training?**

The evidence supports using KataGo’s native training format as the reference contract. Analysis JSON is useful teacher evidence, but it is not that format: a single analysis response does not supply all native outcome, continuation, auxiliary, weighting and provenance fields. Choosing archived labels versus a bounded reanalysis/conversion path remains a human decision. No data shard, model, converter, training run or E2E test was executed in this research.

## Source pin and evidence quality

Code findings below were checked in small source files fetched directly at KataGo commit `d91ea855110dae533f0aada947b2b7d78cc8a4e1`, rather than relying only on searchable documentation. They describe that revision, not every historical archive. Sources are linked at this immutable revision. The archive website and its rights statements are mutable observations as of retrieval.

The executable writer and reader take precedence over stale comments. For example, the header calls global-target channels 68–79 unused, but the writer fills 68–69 with adjudication/feature-rule flags. Its comment for the future-position weight names C1–C2, whereas the writer and loss use spatial C2–C3. A converter copied from comments alone could therefore be wrong. [Writer](https://github.com/lightvector/KataGo/blob/d91ea855110dae533f0aada947b2b7d78cc8a4e1/cpp/dataio/trainingwrite.cpp#L543), [header](https://github.com/lightvector/KataGo/blob/d91ea855110dae533f0aada947b2b7d78cc8a4e1/cpp/dataio/trainingwrite.h#L185), [loss](https://github.com/lightvector/KataGo/blob/d91ea855110dae533f0aada947b2b7d78cc8a4e1/python/katago/train/metrics_pytorch.py#L580).

## Available data and rights

The archive supplies training SGFs, rating SGFs and training NPZ tensors separately. Its README explicitly warns that training SGFs contain only a small fraction of training information. NPZ includes packed spatial features, global features, policy, global targets, score distribution and spatial targets; the README’s source references are historical, so they are not a complete current-format specification. [Archive README](https://katagoarchive.org/kata1/README.txt).

Directory metadata lists daily archives, including `2026-11-06npzs.tgz` at approximately 1.3G and several September 2026 archives near 4–5G. These are listing sizes, not measured download or extraction costs. Availability of the index does not verify archive integrity, actual row contents, throughput, or a workable legal-history join. [Training-data directory](https://katagoarchive.org/kata1/trainingdata/index.html).

The `kata1` disclaimer provides data freely for download with an as-is disclaimer; the site’s generated-data policy also describes public free download/use. These statements support availability, but do not constitute a named MIT license for every archive or imported corpus. Preserve the statements and exact data origin; check separate terms for external data rather than extending the engine license by assumption. [Archive disclaimer](https://katagoarchive.org/kata1/DISCLAIMER.txt), [generated-data policy](https://katagotraining.org/privacy/).

Official network/checkpoint files have their own permissive license and required notices, with exceptions for older g170 and externally attributed networks. Engine code has an MIT-style license with separately licensed dependencies. Data, weights and source therefore need separate provenance records. [Network license](https://katagotraining.org/network_license/), [engine license](https://github.com/lightvector/KataGo/blob/d91ea855110dae533f0aada947b2b7d78cc8a4e1/LICENSE).

## Distinct contracts that must not be conflated

### Analysis response

The API’s `policy` is pre-search, ordered from A19 across rows, with pass last and illegal entries marked `-1`. `visits` counts a child node; `edgeVisits` may differ because of transpositions or weightless exploration. Symmetry-pruned moves may copy another move’s results. Scalar/ownership perspective follows `reportAnalysisWinratesAs`; fix it explicitly. `scoreLead` estimates the lead needed to equalize the game, while `scoreSelfplay` estimates final self-play score. Ownership is a prediction, not a final-board outcome. Pair responses by query ID and turn; reject errors, handle warnings, and require the final `isDuringSearch=false` response. Real move histories retain ko/superko information better than fabricated placement orders. [Analysis protocol](https://github.com/lightvector/KataGo/blob/d91ea855110dae533f0aada947b2b7d78cc8a4e1/docs/Analysis_Engine.md).

### Native search-target extraction

`Play::extractPolicyTarget` calls `getPlaySelectionValues` with direct-policy fallback disabled, asserts root symmetry pruning is disabled, rescales large values and rounds into `int16`. Thus normalizing JSON `visits` or `edgeVisits` defines a distillation target, but does **not** prove equivalence to native self-play targets. Extraction also obtains separate win/loss/no-result/expected-score values and optional per-move Q targets. [Search-to-target extraction](https://github.com/lightvector/KataGo/blob/d91ea855110dae533f0aada947b2b7d78cc8a4e1/cpp/program/play.cpp#L813).

`getPlaySelectionValues` starts from search weights and can adjust them; policy surprise is a divergence between those normalized selection values and the policy used by the search. It is not automatically the same quantity as student-versus-teacher raw-policy KL. Name the precise distribution whenever it is used as a selector feature or evaluation metric. [Search result extraction](https://github.com/lightvector/KataGo/blob/d91ea855110dae533f0aada947b2b7d78cc8a4e1/cpp/search/searchresults.cpp#L64).

### Serialized tensors and loss semantics

For the pinned 19×19 writer, these are the essential arrays; model-specific metadata/Q requirements are additional:

| Array | Representation and meaning |
| --- | --- |
| `binaryInputNCHWPacked` | `uint8` spatial feature bits; N×C×46 bytes, decoded to NCHW with padding removed |
| `globalInputNC` | Floating global features; rules/komi/history state, not arbitrary metadata |
| `policyTargetsNCMove` | `int16`, N×2×362; current-turn and next-turn policy, including pass |
| `globalTargetsNC` | Floating row/target weights, outcomes, TD values/scores, lead and metadata; 80 channels, format marker C63=3 |
| `scoreDistrN` | `int8` mass totaling 100 across half-point score bins when applicable |
| `valueTargetsNCHW` | `int8`, N×5×19×19; ownership, seki-related difference, two future boards, scoring |

Global C0–3 contain result probabilities and score; C4–19 contain different TD/immediate estimates. Weights C25–29, C33–35 and C24 determine which targets contribute. C41–46 encode a shared game identifier. [Format declarations](https://github.com/lightvector/KataGo/blob/d91ea855110dae533f0aada947b2b7d78cc8a4e1/cpp/dataio/trainingwrite.h#L185).

The writer converts white-relative internal values to the row’s player-to-move perspective. Final-board targets depend on actual endings; absent targets receive zero weights plus specific finite dummy distributions. Side positions use a distinct path without fabricated future outcomes. Preserve these conventions rather than setting every missing tensor to zero. [Writer and side-position path](https://github.com/lightvector/KataGo/blob/d91ea855110dae533f0aada947b2b7d78cc8a4e1/cpp/dataio/trainingwrite.cpp#L543).

The reader pads older global-target widths to 80, unpacks bits, applies history transforms and jointly augments spatial inputs/targets. Q fields are required according to model version/configuration. It drops incomplete final batches and initializes augmentation randomness from OS entropy; a declared experiment seed alone does not establish replayability. Validate the chosen archive against the actual loader. [PyTorch reader](https://github.com/lightvector/KataGo/blob/d91ea855110dae533f0aada947b2b7d78cc8a4e1/python/katago/train/data_processing_pytorch.py#L28).

The loss normalizes both policy channels, uses three-way value probabilities, scales score-distribution mass by 1/100 and scoring maps by 1/120, and applies distinct head weights. Its `policymask` is the on-board mask plus pass, **not** a full legality mask. A zero-weight all-zero policy can still cause division by zero during normalization. Changing auxiliary supervision or disabling heads is a recipe change, to be held common across arms. [PyTorch losses](https://github.com/lightvector/KataGo/blob/d91ea855110dae533f0aada947b2b7d78cc8a4e1/python/katago/train/metrics_pytorch.py#L580).

Model version, input-feature version and archive-format version are separate. At the pin, model versions 8–17 map to input version 7. [Version mapping](https://github.com/lightvector/KataGo/blob/d91ea855110dae533f0aada947b2b7d78cc8a4e1/cpp/neuralnet/modelversion.cpp#L35).

V7 input generation includes side-relative stones, liberties, ko/superko/encore state, history, ladders, territory and global rule/komi/pass information. Replaying a validated history through the native rules/features code is the reference for newly labeled positions; a diagram alone is insufficient to reconstruct all of this. The feature representation is not a lossless complete game-history container. [Native V7 features](https://github.com/lightvector/KataGo/blob/d91ea855110dae533f0aada947b2b7d78cc8a4e1/cpp/neuralnet/nninputs.cpp#L2302).

## Failure modes to specify before implementation or isolated tests

These are proposed failure cases, not tests already run:

1. A different ko history, side to move, komi, handicap, suicide rule or encore phase receives the same identity or features.
2. A19/T1 orientation, a reflection/transpose, or the final pass entry is wrong; inputs and targets receive different augmentations.
3. Black/white conversion flips value but not score/ownership, or interprets no-result as a loss/draw.
4. Partial/failed analysis becomes a label; a warning silently changes rules; duplicate or out-of-order responses overwrite a different turn.
5. Illegal `-1` policy entries are treated as probabilities, missing moves disappear, or copied symmetry results inflate a search distribution.
6. `visits`, `edgeVisits`, policy prior and native adjusted target are called the same distribution; teacher screening is omitted from cost.
7. Predicted ownership/lead is written into a final-outcome channel, or missing next-move/future-board data is presented as observed.
8. Dummy targets divide by zero before their zero weight is applied; integer scaling truncates a soft target; header comments override executable semantics.
9. An archive/model/version mismatch passes superficial shape checks but changes history, auxiliary heads or rule adjudication.
10. Positions from a game, fork lineage, duplicate record or symmetry-equivalent held-out history cross split boundaries; Astra receives sealed-test summaries.
11. Shard truncation, shuffling or OS-seeded augmentation changes arm exposure while nominal examples/seeds appear equal.
12. Historical archive labels from heterogeneous teachers are described as labels from the newly frozen teacher; reanalysis changes selected labels only in one arm.

## Proposed E2E gate and repeatable evidence

Before long training, the eventual execution plan should require a small, version-pinned fixture corpus of legal full histories covering ordinary play, captures, ko/superko, passes, ending/scoring, asymmetric positions and every permitted rules branch. Freeze expected legality and coordinate/perspective invariants before writing conversion code.

Replay those histories through the native engine, preserve raw final analysis, serialize the chosen targets, load them with the real training reader/loss, and inspect per-head weights and finite values. Compare newly serialized samples with native-writer reference output where semantics are meant to match. If the chosen distillation contract intentionally differs, record that difference explicitly and validate it against its own stated definition rather than claiming native parity. Apply a bounded short update, export and complete the unchanged-and-updated native M4 gate defined by the deployment ticket. Never substitute successful JSON parsing for this chain.

The gate artifact should contain source revision, hashes of checkpoint/config/fixtures/shards, frozen split manifest, complete commands, raw engine responses, conversion audit, per-head numerical comparisons, training/export logs, and the legal-game SGF/result. A replay command must regenerate the comparisons without using final-test data. Tolerances and the allowed update budget remain decisions for the contract tickets, not invented pass criteria in this report.

For leakage, group by source game **before** selecting rows or creating augmentations, and retain source lineage for forks/reanalysis. The native game ID helps group rows, but does not prove all related games have a common ancestor ID. Audit duplicate complete histories and symmetry-equivalent state/history identities across splits. The API’s symmetry hash excludes full superko information, so it is an additional diagnostic, not a sufficient canonical identity. A pretrained student may already have seen historical public games; call an archive-derived holdout continuation-disjoint unless pretraining exclusion can also be established.

For capacity, the shuffler has a metadata-based resource estimate and approximate per-row storage constants, but its file-hash filtering does not enforce game-family splits. Account for archive plus extracted NPZ plus shuffle generations, float32 expansion/prefetch, checkpoints and logs; measure the selected sample before extrapolating. These estimates do not establish feasibility on the current machines. [Shuffler](https://github.com/lightvector/KataGo/blob/d91ea855110dae533f0aada947b2b7d78cc8a4e1/python/shuffle.py#L1163).

## Decisions still needed and bounded conclusions

- Choose a small, rights-checked archive subset with known generation versions, or an SGF-backed pool that can actually be replayed and joined to provenance. The existence of both archive types does not prove a lossless join.
- Choose whether the study tests selection over existing native labels, selection for new frozen-teacher reanalysis, or a documented combination. These answer different cost/learning questions.
- Freeze raw-policy versus specified search-derived labels and every missing-head treatment. Native data reuse is the lower-conversion-risk candidate; a single-response custom converter needs additional validation.
- Specify split-family identity, holdout contamination limits, determinism/exposure accounting and total screening cost before implementation.

This research resolves what the inspected sources establish and what contract decisions remain. It does not resolve data choice, certify archive rights beyond the published statements, certify download integrity, prove loader/checkpoint compatibility, or report training performance.

## Actual research trade-offs

1. Used pinned executable source alongside documentation: more inspection time, but stale comments and search-index rendering did not silently define the format.
2. Inspected source and archive metadata only: avoided large data/model downloads and unapproved workloads, leaving integrity, actual shard schema, throughput and runtime parity for the execution gates.
3. Kept existing-native-label and new-teacher-label routes open: avoided prematurely changing the experimental question, at the cost of leaving a consequential data/target choice for the human contract ticket.
