# Verification ledger for issue #13

This file reports implementation evidence, not tracker state. GitHub remains the
sole active issue tracker. The first runtime attempt ended stopped/incomplete; its original evidence is retained locally and on the training role. The completed native slice passed at 11:27 UTC and was stopped at 11:28 UTC within the original H0 window; downstream campaign work remains incomplete.

- [x] Failure scenarios were written before runtime implementation.
- [x] Public CLI E2E exercises missing authorization, H0 idempotence, wrong source
  identity, unavailable runtime, low coordinator capacity, unresolved retry rejection, explicit failed retry, software repair with
  unchanged H0, stopped reporting, offline replay and retained-file tampering.
- [x] E2E produces an SHA-256-addressed machine-readable artifact with call
  inputs/outputs, retained evidence, Python/software identities and measured
  elapsed times. This is an offline E2E result, not a native success artifact.
- [x] Python type checking passes with mypy 1.19.1.
- [x] Actual original/derived identities and compatible regular/SWA states for
  all three adopted models, including their notices.
- [x] Actual pinned CUDA and Eigen builds and complete runtime locks.
- [x] Native request-to-legal-move smoke with retained effective rules/settings.
- [x] Offline replay of the actual native success evidence.

The authorized campaign H0 is 2026-11-11 08:02:12.601447 UTC
(16:02:12.601447 Asia/Hong_Kong). Initial direct-network attempts failed and are
retained. A TLS-verified temporary loopback SSH relay restored source access.
The full-history source fetch exceeded its watchdog; the pinned shallow-fetch
repair preserves its cost and bytes. H0 has not been reset.

First stopped attempt:

- H0 remained unchanged. The stop was recorded at 2026-11-11 08:23:20.175968 UTC.
- Direct HTTPS failed; relayed downloads then suffered TLS/SSH connection resets.
  All nine dispatched child operations have retained terminal results; none is
  unresolved in the stopped cost snapshot.
- Known child-operation durations total 1530.7252070307732 seconds. These overlap
  and must not be interpreted as elapsed campaign time or monetary cost. Billing
  remains unknown. Transport/operator diagnosis is not a complete billed-cost
  measurement.
- The Mac measured 19.47 GiB free before execution and 18.30 GiB at the later
  stop check, below the adopted 20 GiB floor. The early precondition was missed.
  The subsequent code repair blocks low/missing/stale capacity before dispatch;
  it does not certify the earlier attempts as compliant.
- No model provenance, native runtime or native move gate passed. No deployment,
  training, complete-game or research-success claim is made.
- Stopped artifact SHA-256:
  `5ec977fc9a9772b9b26537b4842d7ca1912d5e3a20bf15047e1f98caec87c8b8`.
  Local path: `.local/issue-13/stopped-campaign/artifacts/` followed by that hash
  and `.json`. It was verified by the retained runner remotely and by the repaired
  verifier locally, including physical-event arithmetic.
- At the first stop, native acceptance remained unmet and no complete ticket commit was made.

Review dispositions:

The code-review skill's independent Standards and Spec agents found five
substantive issues. The designated BDFL advisor independently validated them
using validate-gpt-code-review. Repairs retain E2E artifacts even on assertion
failure; block unresolved/concurrent retries before relocating failed files;
check adopted capacity prerequisites; recompute stopped physical-event totals;
and revalidate linked libraries (including ELF interpreter and installed NVIDIA
shared libraries) before smoke/offline pass. The optional repeated-report-read
cleanup was deferred because it had no demonstrated correctness impact.

The unavailable-runtime E2E still reaches the missing-runtime branch before a
capacity check could mask it. A deliberately failed E2E assertion was exercised;
its failed artifact retained inputs/output and survived temporary cleanup.

Setup continuation on 2026-11-11:

The user reported freeing 20 GB. A fresh public coordinator inventory measured
37.51 GiB free, satisfying the original floor. The training role measured
319.66 GiB free and approximately 82 MiB of retained campaign files, with no
outstanding claims. Direct HTTPS remained unavailable; TLS-verified relayed
GitHub and PyPI probes succeeded. The BDFL advisor confirmed that narrowly
resuming reconciled setup under the original authorization does not reset H0 or
relax the adopted experiment. A public `resume-setup` record links the original
stop/H0, user update and capacity evidence. Acquisition/build/native success
remains unverified until actual gate reports pass.


A second stopped artifact retained the failed relayed retries:
`1692a1c1527b7c07d2786550d3ed66fc02767c04318fa28e218a2ce532ccfaf3`.
The legacy v1 continuation is integrity-verifiable but eligibility-inconclusive
and inactive because it lacks complete contemporaneous capacity evidence.
A fresh v2 continuation at 09:38:38.725940 UTC retained capacity measurements,
resolved event/report identities and the executing software bundle, preserving H0.
Its artifact is `ff83e41ae31c3caf315646f34abeb984e54380d916133cd7dbd6b302b8c6b617`.
The focused independent Spec review found no blocker in these v2 repairs.

The user-supplied direct proxy returned HTTP 200 for bounded model, PyPI and
GitHub requests. Git's default authentication negotiation reset connections;
explicit Basic proxy authentication made the read-only pinned-reference probe
succeed. These probes establish transport feasibility, not full asset or native
gate success. Private proxy settings remain outside public evidence.

Actual direct-proxy execution passed acquisition for all three ZIPs and official
playable files, and provisioned the pinned package environment (about 4.11 GB of
retained wheels). PyTorch 2.9.1+cu128 reports CUDA available and BF16 supported.
At that checkpoint the native build remained pending; final results follow below.

Two measured compatibility assumptions were corrected before native builds:
archives contain candidate-named `.ckpt` members, and the small candidate's
training config is version 15 despite its native playable format being 17.
This explicitly corrects plan §2's imprecise uniform version-17 config wording:
checkpoint configuration version and exported native format are distinct.
Pinned upstream `export_model_pytorch.py:294–313` upgrades version-15/16 trunk-tip
RMSNorm models to native format 17. The BDFL advisor independently verified this
mapping. Audits now require exact (width, config version, block count) tuples
(384,15,10), (512,17,10), (768,17,11), full config/tensor identities and pinned
loader compatibility. Original bytes, candidate identities and official native
headers remain unchanged. This does not establish export equivalence or parity.


Final native slice result, 2026-11-11:

- Both Eigen and CUDA builds passed with actual dependency/library locks. All
  three original regular/SWA checkpoints loaded through the pinned source.
- The first smoke failed because pinned KataGo requires `resignThreshold` when
  `allowResignation` is present. The repair adds -1.0 while keeping resignation
  disabled. An explicit pre-smoke refreeze preserved the old report-linked
  files and rebuilt both backends in new attempt directories.
- The final smoke passed at 11:27 UTC. Native replies confirm empty 19×19,
  Chinese AREA/SIMPLE-ko rules and komi 7.5; Black generated **R16**, then native
  undo and `play b R16` succeeded. All eleven GTP requests/replies are retained.
- The end-of-slice stop at 11:28:23.201529 UTC preserves original H0 and all
  failures. Its campaign status is incomplete because downstream work is outside
  this ticket; the native smoke status is pass. Research/deployment success and
  monetary costs remain unknown, not zero.
- The stopped ledger contains no unresolved physical dispatches. Recorded child
  durations total 5805.36526968237 seconds, including prior attempts; overlapping
  durations are not campaign elapsed time or monetary cost.
- Retained-runner `verify --offline` passed on the training role with original
  assets, binaries and linked libraries present. It performed no acquisition or
  inference and reported `native_smoke: pass`.
- Final artifact SHA-256:
  `73985d009e326b104e15b3eed37ce8a092b0fb34cde0ec1d0a82140269261d33`.
  Compact evidence is copied to `.local/issue-13/final-evidence/`; full replay
  requires the training role's retained bulk files and libraries.
- Final public-runner E2E and mypy checks pass. Independent final Spec review
  found no implementation blocker; it requested this final evidence update.
  Final Standards review found no material violation. All 372 indexed compact
  evidence file hashes and the artifact hash were also checked after local copy.

This completes the eight issue-13 acceptance criteria, not the parent campaign,
complete-game, training-update, parity, M4 deployment or research gates.
