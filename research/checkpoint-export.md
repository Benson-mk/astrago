# Which KataGo checkpoints and native M4 paths can support a training round trip?

Research date: 2026-11-10 (Asia/Hong_Kong). This is documentation/source/HTTP-metadata evidence, not an executed compatibility test. No weights or datasets were downloaded, no training or engine build ran, and no M4 performance was measured. The ticket can resolve the source-support question while the deployment contract retains its empirical gates.

## Answer

All three proposed families have exact entries with separately published inference artifacts and raw-checkpoint archives. The native upstream Metal backend documents transformer support. A plausible continuation → export → M4 path therefore exists, but the downloaded checkpoint contents, optimizer compatibility, numerical parity, peak memory and equal-time playing strength remain unverified. No model is selected as the best student or deployment model.

## Candidate identities and availability

The [official network index](https://katagotraining.org/networks/) identifies these candidates. It calls the largest candidate the current latest and strongest confidently rated network at retrieval time; that is a site ranking, not an M4 wall-clock result. The raw-checkpoint download is a ZIP, while the directly playable artifact is `.bin.gz`.

| Candidate | Inference artifact bytes | Raw ZIP bytes | Publication evidence |
|---|---:|---:|---|
| `kata1-tf2-b10c384-s2941M-d5872M` | 38,245,507 | 76,304,582 | Listed; both URLs returned HTTP 200 to HEAD |
| `kata1-tf3-b10c512-s3203M-d5937M` | 94,281,753 | 185,791,167 | Listed; both URLs returned HTTP 200 to HEAD |
| `kata1-tf3-b11c768-s12382M-d6533M` | 262,041,254 | 524,218,627 | Listed; both URLs returned HTTP 200 to HEAD |

Exact published URLs, extracted from the index rather than guessed:

- Small: [inference](https://media.katagotraining.org/uploaded/networks/models/kata1/kata1-tf2-b10c384-s2941M-d5872M.bin.gz), [raw archive](https://media.katagotraining.org/uploaded/networks/zips/kata1/kata1-tf2-b10c384-s2941M-d5872M.zip).
- Medium: [inference](https://media.katagotraining.org/uploaded/networks/models/kata1/kata1-tf3-b10c512-s3203M-d5937M.bin.gz), [raw archive](https://media.katagotraining.org/uploaded/networks/zips/kata1/kata1-tf3-b10c512-s3203M-d5937M.zip).
- Large: [inference](https://media.katagotraining.org/uploaded/networks/models/kata1/kata1-tf3-b11c768-s12382M-d6533M.bin.gz), [raw archive](https://media.katagotraining.org/uploaded/networks/zips/kata1/kata1-tf3-b11c768-s12382M-d6533M.zip).

HEAD checks establish reachability and reported compressed size, not a content hash or a valid archive. No SHA-256 of any model is claimed. Before use, download into approved storage, hash the actual bytes, list archive contents, identify its checkpoint/config files and preserve the original archive. The sizes exclude extracted checkpoints, dependencies, training state, conversion caches and datasets.

The [architecture specification](https://github.com/lightvector/KataGo/blob/d91ea855110dae533f0aada947b2b7d78cc8a4e1/docs/NetworkArchitectures.md) describes these as model-format version 17 transformer/nested-bottleneck networks. It maps small/medium/large to training configurations `b10c384h6nbttflrs-fson-silu-rsnh`, `b10c512h8nbt3tflrs-fson-silu-rsnh`, and `b11c768h12nbt3tflrs-fson-silu`. Listed parameter counts are 10,545,753 / 28,537,801 / 70,442,025. These are useful identities, not process-memory estimates. Its Elo comparisons use equal visits; its cost ratios are approximate and hardware dependent. The small exported model’s base name may omit suffixes, so a shortened display name is insufficient evidence of its training configuration.

## Source and package identity

The [GitHub commit API](https://api.github.com/repos/lightvector/KataGo/commits/master) returned source commit `d91ea855110dae533f0aada947b2b7d78cc8a4e1`, with committer date `2026-09-28T00:12:18Z`. Relevant files were opened at that immutable revision. It is the research source snapshot, not a claim that it is the selected production release.

The [release page](https://github.com/lightvector/KataGo/releases/tag/v1.18.2) identifies v1.18.2 as the current release; its change is CUDA focused and it points other backend binary users to the prior release. The [v1.17.0 release](https://github.com/lightvector/KataGo/releases/tag/v1.17.0) documents the introduction of transformer support, including Metal/Core ML, plus Mac memory fixes. An older pre-transformer binary is consequently not a valid substitute merely because it runs a convolutional network.

[Homebrew’s formula page](https://formulae.brew.sh/formula/katago) currently lists 1.18.2 revision 2 and Apple Silicon Sequoia bottles. This is distribution availability, not proof of the actual installed binary’s source or compatibility. Record the formula/bottle identity and `katago version` at execution. Do not assume a Homebrew build and the researched master commit contain identical fixes. If choosing a tagged engine, inspect the trainer/exporter and native backend at that same tag before pinning the final plan.

## Training and export contract

The [checkpoint loader](https://github.com/lightvector/KataGo/blob/d91ea855110dae533f0aada947b2b7d78cc8a4e1/python/katago/train/load_model.py) builds the network from embedded `config`, otherwise from adjacent `model.config.json`, and loads the `model` state. SWA is a separate state: requesting it fails when `swa_model` is absent. It removes known wrapper prefixes and historical auxiliary buffers. This does not prove that any unopened ZIP contains every needed state or that it can resume an optimizer. Preserve and inspect both regular and SWA weights before deciding which initialization the arms share.

The [training entry point](https://github.com/lightvector/KataGo/blob/d91ea855110dae533f0aada947b2b7d78cc8a4e1/python/train.py) provides `-initial-checkpoint`, `-pos-len`, `-batch-size`, `-samples-per-epoch`, and `-max-epochs-this-instance`. A populated training directory can select its own saved checkpoint rather than the requested initial file, so each experimental arm needs a fresh, auditable directory. Current imports include PyTorch, NumPy and the repository’s Muon implementation; an unverified `pip install torch` is not a complete environment lock. The final recipe must choose optimizer/state reset, learning-rate interpretation, averaging and mixed precision explicitly and equally across arms.

The actual [exporter](https://github.com/lightvector/KataGo/blob/d91ea855110dae533f0aada947b2b7d78cc8a4e1/python/export_model_pytorch.py) is `python/export_model_pytorch.py`, not the `export_model.py` name still mentioned by overview documentation. It loads on CPU, accepts `-use-swa`, and writes a `.bin`; the [self-play wrapper](https://github.com/lightvector/KataGo/blob/d91ea855110dae533f0aada947b2b7d78cc8a4e1/python/selfplay/export_model_for_selfplay.sh) subsequently gzips it. Use a direct one-shot export for a pilot: the wrapper also moves/removes intermediate training directories and is unnecessary for preserving an immutable starting point.

Source-verified syntax only; not run, paths deliberately supplied by the later pilot:

```sh
python3 export_model_pytorch.py \
  -checkpoint "$CHECKPOINT" -export-dir "$EXPORT_DIR" \
  -model-name "$MODEL_NAME" -filename-prefix model
```

Add `-use-swa` only when that is the declared state being compared. The exporter enforces attention-logit bounds and rejects several experimental attention/FFN variants. Optional pruning and version-changing flags exist; this report recommends leaving them outside the initial unchanged round trip. A training configuration’s existence does not imply it can be exported.

## Native Apple execution

The [compilation guide](https://github.com/lightvector/KataGo/blob/d91ea855110dae533f0aada947b2b7d78cc8a4e1/Compiling.md) documents `USE_BACKEND=METAL` with AppleClang/Swift, CMake, Ninja, protobuf, abseil and libzip. Its CLI-tools setup is relevant: absence of the full Xcode application alone is not evidence that native compilation is impossible. Actual tool versions and SDK compatibility still need a build or bottle check. Public distributed-training support is unnecessary for this local experiment.

The [Metal backend source](https://github.com/lightvector/KataGo/blob/d91ea855110dae533f0aada947b2b7d78cc8a4e1/cpp/neuralnet/metalbackend.cpp) contains MPSGraph GPU execution and native Core ML conversion for CPU/ANE execution. The MPSGraph path reports FP32; Core ML can use FP16 or demote some transformer configurations to FP32. Thus neither “Metal” nor a requested precision proves pure FP16 execution or ANE residency. Record the selected mode and effective precision. No Python Core ML conversion stack is intrinsically required for this native path.

The [native converter API](https://github.com/lightvector/KataGo/blob/d91ea855110dae533f0aada947b2b7d78cc8a4e1/cpp/external/katagocoreml/include/katagocoreml/KataGoConverter.hpp) accepts `.bin`/`.bin.gz` and declares model versions 8–17 supported. That establishes a version-level path for these three families, not a successful transformation of their exact weights. Runtime conversion, temporary storage, batch size, search state and caches all need measurement. A model fitting in weight memory is insufficient.

## Proposed Day-1 gate for the later plan

Before designing any isolated test, enumerate these failure modes: wrong checkpoint or regular/SWA state; incompatible feature/model version; silently changed initialization; invalid target tensors or perspectives; unchanged weights accidentally re-exported after training; wrong Apple execution mode; numerical drift/nonfinite outputs; memory growth, conversion failure, illegal moves or inability to finish a game.

The following is a proposed E2E gate, not a claimed result or chosen numerical tolerance:

1. Freeze the source, dependency lock, candidate ZIP/inference hashes, extracted config and declared regular/SWA state. Reserve storage before download. Keep the original bytes read-only and perform any migration on a copy.
2. Choose one candidate for a bounded path smoke test; the smallest is a scheduling suggestion, not the final student choice. Load a small legal fixture set spanning opening, capture/ko, pass and late-game histories under the agreed rules/komi. Freeze these fixtures before conversion work.
3. Export unchanged weights and compare like-for-like network outputs across Python, the native reference backend and M4. Fix symmetry, input history and output perspective; compare declared logits/probabilities rather than conflating them. Record absolute/relative errors and finite-value checks against tolerances agreed in the deployment-contract ticket. Do not use stochastic searched moves as the sole parity assertion. The [raw-NN GTP interface](https://github.com/lightvector/KataGo/blob/d91ea855110dae533f0aada947b2b7d78cc8a4e1/docs/GTP_Extensions.md) is a source-backed observation path; confirm its precise output interpretation before implementing the comparator.
4. Complete a legal 19×19 game on the actual Mac using the unchanged export. Capture SGF, commands/config, backend and conversion logs, memory trace and elapsed timing; successful startup alone does not pass.
5. After the separate target-format gate passes, perform a deliberately bounded continuation update in a fresh training directory. Prove actual parameter/output change, save the resulting checkpoint, export the declared updated state, and repeat the same parity and legal-game checks. Comparing this updated export only with the original baseline would test learning differences, not export parity; compare it with its own updated Python state.
6. Only then benchmark all three unchanged candidates at the agreed equal wall-clock move time. A completed smoke test does not establish which model is strongest at the operating point or how many training/evaluation hours are feasible.
7. Package a repeatable manifest, source/dependency identities, fixture hashes, raw outputs, parity result, SGFs, timing/memory logs and exact reproduction command. If either round trip fails, stop extended training and retain a known-good unchanged-engine fallback. Diagnose before relaxing tolerances or bypassing exporter guards.

No hardcoded parity tolerances, batch sizes, learning rates, trial duration, memory ceiling or model winner are selected here; these belong to the human deployment/budget decisions and measured pilot.

## Licenses and remaining limits

The [network license](https://katagotraining.org/network_license/) explicitly covers official kata1 files and checkpoints, permits use/modification/distribution, and requires retention of its copyright and permission notice. These three names are neither g170 nor externally attributed extra-network exceptions. The [engine license](https://github.com/lightvector/KataGo/blob/d91ea855110dae533f0aada947b2b7d78cc8a4e1/LICENSE) is permissive for its own code but identifies bundled components with separate licenses. Preserve both engine and weight notices and review dependencies actually packaged; neither license establishes rights to an arbitrary training dataset.

The essential unresolved facts are ZIP contents and actual hashes; chosen source/tag and dependency compatibility; raw versus SWA relationship to the released inference file; optimizer continuation semantics; runtime Mac parity/precision/memory; L40S training/label throughput; and equal-time playing strength. They are empirical or contract decisions, not grounds to declare the source path unavailable.

## Actual research-method trade-offs

- Checked publication and reachability using source text and HEAD requests instead of downloading/loading weights. This keeps planning bounded and avoids consuming scarce local storage, at the cost of leaving hashes, ZIP contents and loadability unverified.
- Used a pinned upstream source snapshot for precise implementation claims while checking the current Homebrew/release route separately. This exposes documented versus installed-version differences but leaves final source/package reconciliation to the deployment-contract ticket; it does not silently treat master and the bottle as identical.
- Preferred actual exporter/loader code over stale overview filenames. This improves command accuracy while requiring more source inspection and retaining the distinction between inspected syntax and an executed command.
