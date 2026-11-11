# Audited native campaign slice

Implements the first public runner boundary for
[Run a pinned native Go engine from an audited campaign manifest](https://github.com/Benson-mk/astrago/issues/13).
The adopted plan and parent contracts remain normative. No API calls, student
updates, complete-game tests or M4 qualification are performed by this slice.

Run `inventory` on the coordinator Mac and transfer its public JSON to the training role. Run the remaining CLI operations **on the training role**. Resolve SSH credentials and the physical
workspace in an ignored private operator record before invoking it. Keep raw
transport diagnostics private. Public manifests contain role-relative paths;
raw native/build evidence should be reviewed before publication.

```sh
# On the coordinator Mac, immediately before runtime dispatch:
python3 tools/campaign.py inventory --output coordinator.json
# Transfer coordinator.json to the training role through private transport.
# On the training role:
python3 tools/campaign.py plan --output draft.json
python3 tools/campaign.py start --manifest draft.json --run campaign \
  --instruction 'Explicit human campaign execution instruction'
python3 campaign/software/campaign.py acquire --run campaign --coordinator-inventory coordinator.json
python3 campaign/software/campaign.py provision --run campaign --coordinator-inventory coordinator.json
python3 campaign/software/campaign.py build --run campaign --coordinator-inventory coordinator.json
python3 campaign/software/campaign.py smoke --run campaign --coordinator-inventory coordinator.json
python3 campaign/software/campaign.py stop --run campaign --reason 'End of native slice'
python3 campaign/software/campaign.py verify --offline --run campaign
```

The instruction is an operator attestation; this CLI cannot authenticate a human.
The calling agent must obtain the separate instruction first. Inventory is a trusted operator measurement; it is not remote machine attestation. `start` records H0
once, before acquisition/builds; repeating an identical start preserves it.
Use the retained runner for the rest of that campaign. A changed manifest or
runner cannot silently reuse earlier passing gates. Failed or interrupted
operations must be inspected; the runner refuses implicit replay.

Runtime dispatch requires a coordinator inventory no older than one hour, at least 20 GiB free on the Mac, and training free space covering the adopted 50 GiB pilot envelope. Refresh and transfer the inventory before a later operation if necessary. The runner also checks existing campaign usage against the 50 GiB project cap; this is a budgeting check, not a filesystem quota.

The training role needs Linux, Python 3 with venv/pip, Git, GCC/G++ 12, an existing
compatible NVIDIA driver/toolkit, apt package metadata, zlib headers and enough
bulk storage. Provisioning creates an isolated environment and retains exact
wheels and distro archives. It does not upgrade drivers or the OS. Missing
prerequisites remain failed/inconclusive gates. `build` verifies actual CUDA/BF16
availability, audits regular/SWA checkpoint tensors, and builds CUDA and Eigen
from the same pristine revision. `smoke` uses the first adopted diagnostic
candidate and one visit: this does not select the student or teacher.

The native controller initializes empty 19×19 Chinese rules, checks returned
SIMPLE-ko rules and 7.5 komi, generates Black's move, undoes it, and asks native
KataGo to play that move again. Successful native replay supplies legality;
Python does not implement Go rules. Raw requests/responses, configuration,
software identities, UTC times and elapsed durations are retained.

Every gate seals an SHA-256-addressed JSON artifact under `artifacts/`. The
artifact indexes retained manifests, software, raw evidence and gate/event
records. Original model/package bytes remain in bulk `inputs/`; their identities
are retained separately. Acquisition verifies downloaded bytes by hashing them;
published URLs are not pre-existing expected hashes. Offline replay verifies
retained deterministic evidence and smoke settings without spawning a runtime
or accessing the network. It does not repeat inference, training or billed work.
Unknown charges remain null; elapsed duration is not a dollar-cost estimate.

Tests run only through the public CLI:

```sh
python3 -m unittest discover -s tests/e2e -v
```

They retain content-addressed call/result evidence in ignored
`.local/issue-13/e2e/`. Native success requires the real runtime execution above;
the offline failure cases cannot certify native compatibility.

Actual implementation trade-offs:

1. Use standard-library Python and plain content-addressed files. This keeps
   offline replay independent of third-party packages, at the cost of explicit
   validation and conservative single-operator recovery.
2. Retain originals in the training role's bulk store and compact evidence
   separately. This respects Mac storage limits, but full byte verification of
   bulk inputs requires access to those retained originals.
3. Start with a one-visit small-candidate smoke and native undo/replay. This
   cheaply proves the request/legal-move boundary, but says nothing about
   strength, complete games, performance, teacher selection or M4 eligibility.
4. Provision in an isolated user-space environment with pinned top-level packages
   and retained resolved dependencies. This avoids OS/driver changes, but can
   fail against existing compilers/toolkits and requires available distribution
   metadata and storage for package archives.

A conclusively failed operation can be repeated with `--retry`; prior costs and
partial originals remain retained. An unresolved dispatch cannot be retried.
When a runner defect is found before any native smoke gate passes, `adopt-runner --reason`
retains a new software snapshot and its reason without changing H0 or the old
snapshot. Use the returned `runner` path for subsequent commands after a repair. A post-build repair requires another build pass tied to the new adapter. Old
report-linked binaries, caches and smoke files remain untouched. Repairs after
a passed native smoke remain rejected.

Additional actual trade-offs:

5. Permit explicit, recorded retries only after completed failures, and runner
   repairs only before a native smoke pass. A post-build repair explicitly
   refreezes the adapter and requires a new build validation with separate
   attempt paths. This supports setup recovery
   without erasing H0, but intentionally restricts later recovery.
6. Use a temporary loopback-only SSH relay when the training role cannot reach
   approved HTTPS sources directly. This restores acquisition without host
   reconfiguration, at the cost of coordinator connectivity during downloads.
   TLS remains verified and transport configuration stays private.
7. Fetch only the pinned source commit. This reduces setup transfer/storage while
   retaining the exact tree and Git identity, but omits upstream history from
   the campaign workspace.

The CLI can also be checked with `mypy==1.19.1` using the root `pyproject.toml`.
Compiler/import checks do not substitute for the native runtime gate. A runtime
failure leaves the issue incomplete; no commit may claim the unrun acceptance
criteria as verified.

After an environmental repair, `resume-setup --run campaign --instruction '…'
--coordinator-inventory coordinator.json` can append a setup-only continuation.
It verifies the retained stopped artifact and refuses native passes, unresolved
claims/dispatches, stale or insufficient capacity, and expiry of the original
H0–24 window. Historical stops remain immutable. The full stopped interval and
all prior costs remain part of this campaign; no new H0 is created. A later stop
blocks work again. A v2 continuation automatically retains its executing software
bundle and capacity measurements. Later `adopt-runner` repairs remain restricted
to setup before a native smoke passes. Artifact replay
instructions select that retained revision rather than the original runner.

8. Explicit setup-only continuation preserves the original clock and evidence,
   but adds a stop/resume transition requiring validation. Restricting it to
   reconciled setup before any native pass excludes broader recovery.

9. Preserve legacy v1 continuation receipts as integrity-verifiable but permanently
   eligibility-inconclusive and inactive. This keeps historical evidence honest,
   at the cost of maintaining two schemas; a fresh v2 receipt qualifies only
   subsequent setup against contemporaneous measurements.
10. Use the operator-supplied authenticated proxy directly from the training role
    after bounded HTTPS probes. This removes the coordinator relay dependency,
    but depends on that proxy's availability and authentication. Git required
    explicit Basic proxy authentication; TLS verification remains enabled.

11. Fully rebuild in separate attempt paths after the observed pre-smoke config
    repair. This provides a fresh runtime lock under the repaired adapter and
    preserves historical report paths, at the cost of repeated compilation and
    additional retained storage instead of relying on binary revalidation alone.
