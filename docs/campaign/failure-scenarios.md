# Native campaign slice: failure scenarios recorded before runtime implementation

Issue: https://github.com/Benson-mk/astrago/issues/13

The agreed seam is the public `python3 tools/campaign.py` CLI, including its
`verify --offline` operation. Tests retain their invocation, output and an
SHA-256-addressed result. Native success requires actual pinned KataGo; a fake
engine cannot establish success. This slice does not establish full-game,
training-update, M4 deployment or research success.

| Supported failure | Expected externally observable outcome |
| --- | --- |
| Missing explicit execution instruction | No H0, acquisition, build or inference; nonzero exit |
| Repeat start or changed manifest after start | H0 and original manifest unchanged; reject changed inputs |
| Private connection values | Resolve outside public manifests; keep private raw transport logs locally |
| Wrong source revision, dirty upstream, wrong model/config hash | Failed gate; retain originals and diagnostic identity; no advancement |
| Missing provenance, notices, regular state, SWA identity or incompatible architecture | No asset pass |
| Missing compiler, CUDA, PyTorch/BF16 support or CPU reference | Inconclusive/failed runtime gate, unknown charges retained |
| Acquisition/build interruption | Retain attempt, partial bytes/logs and measured wall time; never reuse as a pass |
| Unresolved command variable or missing executable | Reject before subprocess execution; no advancement |
| Native timeout, crash, malformed/error response or illegal move | Failed/inconclusive smoke; preserve transcript; no advancement |
| Native rules/komi differ from Chinese SIMPLE-ko/7.5/empty 19×19 | Failed smoke |
| Changed inputs, changed executable/config or stale report | Offline verification fails; no prior pass reuse |
| Tampered retained evidence | Offline verification fails without invoking runtime or network |
| Replaying valid evidence | Checks deterministic retained identities; never starts/resets H0 |
| Stop before later phases exist | Accurate incomplete/stopped report with existing evidence and unknown costs |

Further inherited failures (loader rounding, RNG/cursor restoration, summed-loss
semantics, pass-feature/cache provenance, duplicate update, cyclic prerequisites,
nonterminal score as completion, cross-family state, omitted opponent cost,
lost API usage and post-test thresholds) belong to later slices. No gate here
claims to cover them.

Storage preflight found during execution: missing/stale coordinator inventory,
less than the adopted 20 GiB coordinator free-space floor, or insufficient
training space for the 50 GiB pilot envelope must block runtime dispatch. Keep
H0 unchanged and record the failed prerequisite; never move bulk downloads to
the Mac as an implicit fallback. This check is specified before its repair.

Setup continuation after an environmental repair: `resume-setup` must reject
missing authorization/evidence, low or stale capacity, unresolved claims/events,
a changed manifest, a native pass, or expiry of the original H0–24 setup window.
An accepted continuation appends a record referencing the latest stop and H0;
no historical stop, failure, original bytes, or clock may be replaced. A later
stop must block dispatch again. This is specified before the resume implementation.

Observed HTTP-client failure: the published archive returns 403 to the default
Python user agent while the same TLS-verified URL returns a ZIP prefix to an
identified AstraGo client. Record request headers with acquisition evidence;
keep source URLs, TLS verification and full-byte/provenance gates unchanged.
The bounded HTTP reproduction was run before changing the downloader.

Private proxy configuration: an authenticated proxy may appear in transport
errors. Public command/error evidence must redact the configured proxy URI,
host and credentials; raw transport settings remain solely in private operator
records. The proxy is supplied outside the public manifest.

Resume-evidence repair: legacy v1 resume bytes remain verifiable, but missing
training-capacity and precise check-time evidence must remain eligibility-
inconclusive and must never reactivate the repaired runner. V2 must retain its
executing software and full contemporaneous capacity/event/report snapshot.
Changed receipt hashes, identities, time arithmetic, H24 eligibility, capacity,
or unresolved-work assertions must fail both state resolution and offline
verification. Historical verification uses the recorded time, not today's age.

Observed original archive layout: each verified ZIP contains a checkpoint named
for its candidate, not `model.ckpt`. Resolve exactly that candidate's `.ckpt`
member; missing or duplicate matches still fail. Preserve original filenames
and bytes rather than renaming or substituting a checkpoint.

Observed format distinction: the adopted b10c384 checkpoint has training config
version 15 with trunk-tip RMSNorm; its official playable header is version 17.
Pinned upstream exporter lines 294–306 explicitly upgrades this configuration
to native format 17. Validate exact candidate training versions, widths and
block counts independently from native headers; require pinned loader success
and retain full config/state identities. Do not infer regular/official equality.

Observed GTP startup failure: pinned KataGo reads `resignThreshold` whenever
`allowResignation` exists, even when false. Supply -1.0 while keeping resignation
disabled. A repair after build but before any smoke pass must explicitly refreeze:
retain old reports and their referenced files in place, use new attempt paths,
require a current-adapter build pass, and reject reuse of the old passing build.
Failed smoke retries retain separate config/stderr/transcripts. No post-smoke
repair or original H0 reset is allowed in this slice.
