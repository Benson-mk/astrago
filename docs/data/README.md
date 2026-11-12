# Legal family admission (issue #14)

This is the data slice of the adopted campaign runner. The existing native slice
and its stop remain immutable. A separately authorized data execution links its
native artifact and original H0; neither build nor admission creates a new H0.
Original H24 expiry requires an explicit replan. Implementation is not execution
authorization. The native build and synthetic native diagnostics have passed, and the November 6 archive has been acquired. The user subsequently replaced the unavailable separate-account gate with audited runner workflow isolation; see verification.md.

The evaluator runs `data-build` against the existing pristine pinned KataGo tree,
then `data-admit` against locally acquired approved archives. Both require an
explicit execution instruction. Building adds one model-free native command and
an input-consumption check in a separately copied source tree. It neither loads
models nor substitutes Python rules for native legality.

```sh
python3 tools/campaign.py data-plan --output data-plan.json
# Populate the measured values described below before separately authorized work.
python3 tools/campaign.py data-build --source /absolute/pristine/katago \
  --native-parent /absolute/stopped/native-campaign --output /absolute/replay-build \
  --instruction 'The separately granted data execution instruction'
python3 tools/campaign.py data-check-native --native-lock /absolute/replay-build/locks/ACTUAL_SHA256.json \
  --output /absolute/native-checks --instruction 'The separately granted data execution instruction'
python3 tools/campaign.py data-admit --manifest data-plan.json \
  --output /absolute/evaluator/data-run --public-output /absolute/public/data-run \
  --instruction 'The separately granted data execution instruction'
python3 tools/campaign.py data-inputs --run /absolute/evaluator/data-run \
  --split development
python3 tools/campaign.py data-verify --offline \
  --artifact /absolute/evaluator/data-run/artifacts/ACTUAL_SHA256.json
```

The plan deliberately leaves workload sizes unresolved. Set the five required
candidate/family counts from the measured campaign capacity and adopted workload
contract, not model scores. Set `max_storage_bytes` within the 50 GiB ceiling;
`native_parent` is the retained native run directory, `native_replay` the actual
content-addressed build lock path, `native_checks` the passing native diagnostic artifact path, and `isolation` must remain `runner-workflow-v1`.
The approved admission manifest is now `astrago-admission-v2`; old UID manifests
must be regenerated explicitly. Historical OS-probe receipts remain failed or
unverified under their original meaning and cannot satisfy the new gate.

The existing training account runs both evaluator preparation and consumers.
Admission automatically registers each exact public export with its manifest,
artifact, file and payload identities. Consumers use `data-inputs --run RUN
--split training|development`, optionally with `--export-id` when multiple exports
exist, `--purpose training|selection|debugging|tuning`, `--arm A|B|C` and
`--candidate-id`. Supplied input paths, sealed IDs/references, altered exports,
evaluator requests and all arm-state references are rejected. No training or
arm-state loading is implemented by this data boundary. Successful and denied
requests retain immutable content-addressed access records before returning data.

Run `data-check-access --run RUN --output RECEIPT` to exercise actual allowed and
denied gateway operations under that same account; supply this workflow receipt
to fixture freeze. Registration occurs after export/artifact creation to avoid a
circular hash. Registrations and access records are separate immutable records;
later reads append new records rather than changing files in earlier artifacts.
Subsequent evidence snapshots include their existing identities and storage costs.

**This is workflow isolation and auditability, not OS-enforced unreadability.**
The same account can directly read private files, invoke evaluator administrative
commands, modify code or forge registrations outside compliant runner use. Neither
hashes nor role labels prove that no bypass occurred. `data-verify --offline` is an
evaluator integrity operation that intentionally reads private retained evidence;
selection/debugging uses the consumer gateway. Final evaluation remains denied
until an actual final model/configuration freeze and evaluator operation exist.
Development fixture freeze is not permission to open the sealed test.

Each `archives` entry has `date`, `path`, `url`, actual `sha256`, `bytes`,
`retrieved_utc`, and measured `acquisition_seconds`. Entries begin with November 6,
2026 and descend daily no farther than November 1. Supply the corresponding
README, disclaimer and data terms assets in `terms`, with the same fields except
`date`. Source acquisition is an operator prerequisite, not automatic downloading.
Local hashes establish byte identity; origin/rights inspection remains an operator
responsibility. No source publication or license grant is inferred from a URL.

Admission examines the source-origin fields written by the pinned native writer.
Ordinary full histories may have a positive training `startTurnIdx`; this is not
missing earlier history. Unknown origins, forks without established ancestry,
setup edits, illegal moves and moves after native termination are excluded.
The native parser follows the first recorded child, not the longest child. It
retains source result text separately and does not manufacture outcome labels.

Complete-history duplicates are grouped mechanically. Optional `lineage` entries
carry `child_source_id`, `parent_source_id`, named `reviewer`, and a retained
`provenance` trace establishing the source relationship. A shared opening is not
such a trace. The evaluator reviews those source records before admission; links
to missing/excluded parents fail. Unresolved fork origins remain excluded. The
minimum complete-game identity names each connected family.

The frozen source set is chosen using score-free unique prefix and connected-family counts before
the fixed split. An insufficient supplied prefix retains unassigned eligibility and
names the next approved date without freezing sources or exporting a split. Actual useful counts after duplicate priority may still fall
short; the artifact reports that shortfall rather than expanding a frozen pool.
All orientations and original native reports remain private. Public consumers
receive canonical training/development histories and sealed identities only.

The initial development report identifies native atari/ko/pass/player and
same-visible-stone candidates. It remains incomplete until a named evaluator
reviews semantic coverage, including seki and quiet midgame, on real development
histories. Unverified categories are not claimed absent from the archive.

`data-freeze-fixtures --artifact PRIVATE_ARTIFACT --review REVIEW_JSON
--access-receipt CONSUMER_RECEIPT --public-output NEW_PUBLIC_DIRECTORY
--instruction EXECUTION_INSTRUCTION` checks
and freezes that review. The review has schema `astrago-development-review-v1`,
`reviewer`, exactly 32 distinct development candidate IDs in `selected`,
`terminal_sources` containing native two-pass development source IDs, and
`coverage` with every category listed in failure-scenarios.md. Each category has
one or more `{"candidate_id": "…", "evidence": "…"}` assertions. Native
mechanical categories are cross-checked; semantic classifications retain the
reviewer's evidence and are not represented as automatic seki detection. The
same-stone category requires at least two selected histories with matching native
stones. Missing counts, coverage, terminal records or source identities block
freeze; the previous incomplete artifact remains retained.

Offline verification hashes retained files and repeats deterministic admission
identities, fixed family assignment, duplicate exclusions and the fixture report.
It does not rerun native rules, training, GPU inference or Astra requests. Raw
archives/SGFs, patched-source identities, commands, native responses, source cost
metadata, elapsed times and bytes remain in evaluator storage. Unknown monetary
cost stays null. Continuation disjointness does not establish pretraining cleanliness.

Verification:

```sh
python3 -m unittest discover -s tests/e2e -v
python3 -m mypy
# Only after an authorized real admission:
ASTRAGO_ADMISSION_ARTIFACT=/absolute/artifacts/ACTUAL_SHA256.json \
  python3 -m unittest discover -s tests/e2e -p test_admission.py -v
```

The offline E2E retains content-addressed evidence under `.local/issue-14/e2e/`.
The native retained-artifact test skips explicitly without a real artifact.

Actual implementation trade-offs:

1. A linked data-stage artifact preserves the stopped native slice and original
   clock, at the cost of an additional stage and explicit cross-artifact linkage.
2. Model-free native legacy-mode replay avoids model loading for legality, but
   cannot claim producer score equivalence or replace later teacher feature modes.
3. A separate patched source copy preserves pristine upstream evidence, at the
   cost of source storage and another native compilation.
4. Native replay uses one process per SGF, providing process isolation and simple
   retained request/result evidence at the cost of startup overhead.
5. Unsplit unique eligibility thresholds freeze sources before split assignment; this
   avoids split-dependent source changes but can leave post-deduplication capacity
   unmet even when the unsplit counts passed.
6. In-memory full-history JSON keeps transformations directly inspectable, at
   the cost of potentially substantial memory, serialization and prefix work.
7. The operator supplies retained source acquisition metadata. This avoids adding
   a download service, but requires acquisition evidence before admission. The
   original separate-account prerequisite was superseded by the user decision below.

The inherited source range, strict exclusions, exact split, duplicate priority,
continuation-disjoint limitation and evaluator ownership follow the adopted
contracts rather than representing new experimental choices.

8. Named evaluator evidence establishes source ancestry and semantic fixture
   categories that the archive/native rules do not directly certify. This keeps
   those judgments inspectable, but requires manual provenance/Go review; hashes
   certify record integrity, not the truth of an unevidenced assertion.

Final storage checks include the actual serialized artifact index, prior and new
public exports, source originals, build files and inherited native campaign.

Additional actual trade-offs from the user-approved isolation revision:

9. Same-account workflow isolation removes account switching, while allowing
   direct-file/code/registration bypass by that account. Audits show compliant
   runner use, not OS isolation or proof that no bypass occurred.
10. Exact export-byte registration is simple to inspect, but each new export or
    relevant gateway revision needs fresh registration/probe evidence.
11. Separate immutable registration/access records preserve old artifacts, but
    require explicit receipt links, subsequent snapshots and storage accounting.
12. Unsupported arm-state and evaluator routes stay denied, postponing those
    operations until their real state/freeze implementation exists.
13. Versioned workflow schemas preserve old evidence's meaning, at the cost of
    explicit manifest migration rather than accepting old UID manifests.

The selection-arm and holdout contracts remain distinct. A/B/C share the prepared
pretrained initialization, common candidate pool, recipe and matched budgets.
Each later arm retains its own model/optimizer/lookahead/averaging/RNG/recovery
state, selection manifests, exposure cursor and feedback. Overlapping selected
training positions across arms are allowed. Reused teacher labels retain separate
logical arm charges and shared physical-work accounting. This slice supplies the
common allowed data; it does not implement or certify downstream training state.

14. Insufficient archive prefixes remain immutable unassigned attempts. A fresh
    cumulative attempt can add the next approved day, preserving auditability at
    the cost of repeated replay and retained storage; no native-result cache is
    introduced in this slice.

If all six approved archives have actually been examined and the admitted pool
is empty, verify that specific incomplete outcome separately:

```sh
ASTRAGO_BOUNDED_ZERO_ARTIFACT=/absolute/artifacts/ACTUAL_SHA256.json \
  python3 -m unittest discover -s tests/e2e -p test_admission.py -k bounded_empty -v
```

This E2E requires the full bounded source list, exact zero shortfalls, all required
development categories unavailable, no eligible terminal fixtures, two identical
offline replays, and registered empty-export access probes. It also exercises
rejection of every original archive path through the selector gateway. Its passing
verification result explicitly retains an incomplete campaign source gate and an
unpassed fixture seal. Partial prefixes cannot satisfy it. The existing positive
retained-corpus E2E continues to require a passing native/fixture gate.
