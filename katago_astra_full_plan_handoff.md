# Handoff — KataGo × GPT-6 Astra: complete five-day plan

**Prepared:** 2026-11-06  
**Next session:** Produce a detailed five-day implementation and evaluation plan; do not represent the plan as an already implemented system.

## 1. Context and existing artifact

Read the previously uploaded **`katago_astra_cooperation_handoff.md`** before proceeding. That source contains the initial cooperation rationale, literature links (LoGos, GoBench), three-arm experiment, initial deployment outline, and unresolved decisions. Retrieve it from conversation files by filename; do not assume an earlier container path will survive into a future session. Avoid reproducing that earlier artifact's full literature review or evidence summaries. The previous attachment itself was not altered.

**User-confirmed constraints:** Build an original, modern **19×19 Go AI research prototype** in **five days**, using one **NVIDIA L40S (48 GB VRAM)** for training and an **Apple M4 (16 GB unified memory)** for *offline* local inference. Bootstrapping from KataGo datasets and weights is allowed: training purely from scratch is not necessary. Cloud tools, including GPT-6 Astra, may be used during development/training, not for deployed gameplay. The user cares about what, if anything, is genuinely research-oriented rather than merely repackaging KataGo.

**Status:** Architecture discussion only. No code, downloaded dataset, trained weights, exports, Mac benchmarks, matches, or proven Astra benefit have been produced in this conversation. The user asked for a full-plan handoff, not to start building or training. Models, API details, search budgets, and expected strengths remain provisional.

## 2. Most recent cooperation decision

**Endorsed research hypothesis:** Astra-guided data curation/curriculum might improve Go student learning efficiency over both random sampling and ordinary automated active learning. That is **not established** and could fail. The goal is to test it, not assert that Astra already contributes superior Go knowledge.

**Proposed components:**

- **KataGo:** frozen expert *numerical* supervision for suitable positions (search-derived choices, value/score/ownership where well defined), with explicitly fixed rules and search settings. Engine estimates are not infallible or automatically calibrated truths.
- **GPT-6 Astra:** research and data-selection collaborator. Analyze *development-set* student errors and propose **executable, reproducible selection filters/curricula**. It may assist coding and propose positions or patterns, but its prose and generated numerical probabilities are not automatically authoritative Go labels.
- **Rules/position validator:** reject illegal histories, wrong rules, missing side-to-move/komi/ko metadata, and invalid candidate continuations.
- **Student and search:** native board network plus search, deployed on M4 without Astra/cloud access. Reuse KataGo's tested rules/search and native Mac backend during this sprint rather than designing new MCTS/rules/MLX software.

**Working research description:** *Astra-guided active data selection for KataGo-supervised training of an edge Go engine.* Modern transformer features inherited from KataGo do **not** themselves constitute our new contribution. Demonstrated gain must come from a measured experiment.

Astra proposals should not just say “improve life and death.” Each must specify reproducible predicates on an existing, legal position pool, selection amount, teacher-analysis needed, motivation, and disjoint validation measurement. Prefer real move histories over fabricated board diagrams for the five-day implementation. Put bounds on Astra calls and costs; ensure its selection operations are code-verifiable. Reserve a final test set unseen by Astra.

## 3. Model decision: revisit, don't choose only by parameter count

Earlier default `tf2-b10c384` was revised: M4 16 GB alone does **not** require that small model. Three baseline candidates must be benchmarked on the actual M4 at equal time per move before final choice.

| Candidate | Provisional role |
| --- | --- |
| `kata1-tf3-b11c768-s12382M-d6533M` | Frozen teacher, unchanged model baseline, and **possible best edge deployment** |
| `tf3-b10c512` | Provisional medium-size student; exact source checkpoint not yet fixed |
| `tf2-b10c384` | Small/fast baseline and possible latency-critical student |

Do not imply the medium model has been proven optimal. Larger models may win despite slower inference; the best choice depends on complete M4 search latency, strength, and memory. Suggested but **not user-confirmed** operating points: 0.25, 1, and 3 seconds per move on 19×19. Verify raw training checkpoint availability, revision identity, licenses and compatibility with training/export scripts. Any “latest/strongest” statement must be rechecked at planning time.

Do **not** assume pure FP16, forced Neural Engine, or quantization is safe just because weight storage fits. Start with the validated native KataGo Metal/Core ML execution path and verify numerical outputs. Quantization and new backends are optional, not critical-path requirements.

## 4. Blocking Day-1 deployment gate

The initial handoff deferred M4 export to Day 5. The latest review explicitly **overrides** that: verify training-to-M4 round-trip **on Day 1**, before extended training.

```text
official raw checkpoint
  → load training implementation
  → export unchanged model
  → load on M4 native engine
  → compare representative numerical outputs and complete a legal game
  → apply a very short training update
  → export and retest on M4
```

A pretrained model running on the Mac is insufficient to validate the *updated-weights exporter*. Check checkpoint heads/feature encoding/exporter semantics and the native backend. If either export or training-target conversion fails, stop affected training and use a known-good compatible pipeline or unchanged model. Keep the starting checkpoint immutable for rollback.

## 5. Teacher targets and data correctness

KataGo machine-readable analysis distinguishes a **raw pre-search policy** from **search results** such as visits and per-move values. Do not equate a valid JSON analysis response with ready-to-train model tensors. Before writing labels verify:

- Target representation: raw policy vs search-derived policy; search visit normalization; `visits` vs `edgeVisits` and any search filtering.
- Perspective: root side, score/value sign conventions, `scoreLead` vs other score outputs, ownership mapping.
- Board features: side to move, rules, komi, legal mask/pass, ko/superko/history, board dimensions.
- Existing model's target format, feature tensor version, auxiliary heads, loss weights, and export expectations. Preserve its native semantics unless a change is justified and tested.
- Failed/incomplete analyses and label provenance; record teacher network ID, search budget, rules and history for each labeled example.

Use suitable KataGo archived NPZ data for broad coverage when feasible. Preserve game-level splits; avoid data leakage from correlated positions/variations into validation/test. Astra should receive development information only, never the sealed final test dataset. Both training-data access and teacher-labeling budgets must be checked against disk/network/throughput reality.

## 6. Core controlled experiment: A / B / C

Use **one shared pretrained student initialization**, identical core architecture and recipe, comparable train steps, and common candidates/settings. Run short continuation training sequentially on the single L40S as needed; report seed and match uncertainty. The decisive question is **C vs B**, not merely C vs A.

| Arm | Position selection | Labels | Question |
| --- | --- | --- | --- |
| A | Random / stratified baseline | KataGo | Does ordinary continuation help? |
| B | Competent automated selection: uncertainty, disagreement, diversity or error | KataGo | How much can cheap selection improve? |
| C | Astra proposes structured, executable curricula / position filters from same development evidence | KataGo | Is Astra better than B? |

Keep B/C information access equivalent; explicitly account for any teacher analysis used to select candidates. At minimum, compare **matched teacher-labeling and training budgets** to study selection quality, then **complete cost** including screening, teacher compute, Astra calls, I/O, training, and evaluation. Equal example counts alone are not equal compute costs. Do not give C arbitrary extra label budget and call it a curriculum breakthrough.

Metrics: independent 19×19 head-to-head play at equal **M4 wall-clock move time** against unchanged pretrained baselines; paired colors/positions; number of games and uncertainty; policy agreement and KL where appropriate; value/score/ownership quality; tactical/rare-failure positions; illegal move rate; Mac inference/search p50/p95, peak and steady-state memory; total GPU-hours and Astra API expense. Equal-visit strength is diagnostic but not the edge success criterion. If match count is too small, say the result is inconclusive.

**Interpretation:**
- C>A but not B: targeted selection helps, but Astra's added value is not shown.
- C>B on matched label/train budget: evidence for better selection in this particular experiment (subject to uncertainty).
- C>B after including Astra overhead: stronger practical efficiency evidence.
- No gain/inconclusive: report honestly and deploy the strongest well-tested unchanged or modified candidate.

## 7. Revised five-day schedule

| Day | Required goal / exit condition |
| --- | --- |
| **1** | Pin and verify engine/training dependencies, raw checkpoints, dataset sample, licenses; benchmark all unchanged models on M4; validate **unchanged AND short-updated export**; build target-conversion smoke tests; freeze data splits and experiment contract. **No long training before passing these gates.** |
| **2** | Measure baseline L40S throughput and dataset pipeline; establish shared continuation run; collect development-only failure reports; implement automated selection and structured Astra proposal validation. |
| **3** | Create comparable A/B/C candidate selections and bounded KataGo teacher labels; begin controlled training; log all compute, API calls, provenance, and training trajectories. |
| **4** | Complete the available continuation runs and developmental evaluation; profile candidates on M4; avoid uncontrolled architecture/search changes. |
| **5** | Run final independent matches and sustained M4 tests; freeze the deployment choice; package offline engine/model/config; document benchmark uncertainty, research result, costs, limitations, and rollback. |

Five days = up to 120 wall-clock hours, **not** guaranteed usable GPU training time. Exact GPU-hours, batch sizes, data sizes, teacher visits, labels, search budgets and match counts must be set from early measurements. Prefer a reproducible prototype to a grand but incomplete training run.

## 8. Required full-plan deliverables for next agent

The next response should construct a **complete executable plan for review**, including:

1. Project objective and separate deployment/research success criteria; intended rule/komi/time operating point with labeled assumptions.
2. Pinned source commits, OS/driver/CUDA assumptions, checkpoint names, hashes/licenses, dependencies, expected workspace layout and reproducible commands (after current verification).
3. Data formats, splits, selection candidate pool, dedup, provenance, storage and I/O feasibility.
4. Teacher search settings, per-position cost/budget, precise target definitions and tensor conversion tests.
5. Astra structured input/output JSON schema, prompts, permissions/validation, request/token/spend caps, audit log, and no-API fallback. Verify model/API availability rather than inventing interfaces.
6. Network choice process, pretrained checkpoint loading, continuation optimizer and batch recipes, safeguards against forgetting, checkpointing and stop conditions.
7. A/B/C controlled variables, scheduling, budgets, measured pilot-to-final extrapolation, reporting uncertainty, seed policy and decision logic.
8. Native M4 export, numerical parity, complete-engine performance testing, offline packaging, rollback.
9. Day-by-day task/acceptance gates, prioritization, blockers, and reduced-scope fallback if experiments cannot finish.

**Unresolved but do not redundantly ask first:** training host OS/drivers, storage/bandwidth, API access and spending cap, preferred move latency, exact rules/komi, and teacher analysis budget. Make explicit provisional defaults and verification steps. The hardware, deadline, and permission to bootstrap have already been answered.

**Out of five-day critical path:** implementing completely new Go rules/MCTS, train-from-scratch AlphaZero, architecture redesign, Gumbel search research, full regret-guided self-play, custom MLX backend, LLM at each MCTS node, aggressive quantization, and polished natural-language commentary. These are possible later research branches.

## 9. References and evidence discipline

Use the original handoff's sources (lines 104–111) and directly verify current primary documents before claiming precise checkpoints, APIs, current results, or compatibility:

- KataGo engine: https://github.com/lightvector/KataGo
- Native analysis protocol: https://github.com/lightvector/KataGo/blob/master/docs/Analysis_Engine.md
- KataGo training network site: https://katagotraining.org/networks/
- KataGo archive: https://katagoarchive.org/
- LoGos paper: https://arxiv.org/html/2601.16447v1
- GoBench: https://rolandgao.com/blog/gobench/
- GPT-6 Astra API page referenced previously: https://developers.openai.com/api/docs/models/gpt-6-astra

The earlier reported GoBench numbers are tool-free **9×9** benchmark-specific Elo, not 19×19 win rates or a tool-assisted Astra evaluation. LoGos candidate-move agreement is not direct match strength. Commentary quality is not guaranteed by plausible prose. Those caveats, prior source claims, checkpoint identities, and licensing all require confirmation where they materially affect the plan. No benchmark or training improvement has been verified in this handoff.

## 10. Suggested skills for the next agent

There is no confirmed dedicated KataGo/Go-ML Skill. For a plain Markdown implementation plan no artifact template is mandatory. When the user **explicitly selects** the corresponding artifact template, call the Skill tool or read:

- **`artifact-template-system-design`** — `skills://plugins/openai-templates/artifact-template-system-design/skill.md` for a selected System Design document.
- **`artifact-template-experiment-analysis`** — `skills://plugins/openai-templates/artifact-template-experiment-analysis/skill.md` for a selected Experiment Analysis report (only report actual results as results).
- **`artifact-template-project-tracker`** — `skills://plugins/openai-templates/artifact-template-project-tracker/skill.md` for a selected Project Tracker spreadsheet.

Respect explicit-selection requirements; do not invoke the document/spreadsheet routers merely because the project involves planning. For code and current verification, use normal development/research tools.

## 11. Suggested first task in next session

> Read this file and `katago_astra_cooperation_handoff(1).md`. Produce a full, verifiable five-day implementation/evaluation plan for L40S training and offline M4 deployment. Treat the three model choices as provisional pending Mac benchmarks. Make Day-1 training/export-to-M4 parity and teacher-target conversion hard gates. Test the marginal value of Astra selection relative to competent automated selection under both matched labeling/training compute and total cost. Give schemas, commands (after verification), proposed budgets, per-day checkpoints, acceptance criteria, fallback plans, and evidence limitations. Present the plan for approval, not as completed work; do not launch training.

---

**Privacy:** No API keys, passwords, private account IDs, or personally identifying information are included. Save in OS temp directory; do not write in the project workspace.
