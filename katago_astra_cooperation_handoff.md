# Handoff — KataGo × GPT-6 Astra cooperation for an edge Go AI

**Prepared:** 2026-11-06  
**Next-session focus:** Decide how to combine KataGo and GPT-6 Astra in a research-backed, experimentally testable Go-AI training pipeline, then translate that design into a realistic five-day implementation/evaluation plan.  
**Status:** Architecture discussion only. No training runs, code, datasets, deployments, experimental results, or finalized checkpoint decisions have been produced in this conversation.

## User goal and fixed constraints

- Build an original, modern **19×19 Go AI**, not merely deploy stock KataGo. Bootstrap from KataGo data/checkpoints is allowed; training from scratch via self-play is **not** required.
- **Training:** one NVIDIA **L40S, 48 GB VRAM**.
- **Inference:** offline/edge on **Apple M4, 16 GB unified memory**. Cloud teacher usage during training is acceptable; the **deployed** model must be able to operate locally.
- **Schedule:** **five days** to get a working research prototype, so avoid reproducing expensive full-scale research training.
- User is concerned about *what counts as cutting-edge research*, not just getting a KataGo clone working. They previously questioned choices among KataGo checkpoints `tf2-b10c384`, `tf3-b10c512`, and `kata1-tf3-b11c768-s12382M-d6533M`; this question was not definitively resolved here.
- User requested explanation of the LoGos paper in **zh-HK** and discussed Astra/KataGo cooperation in English and Cantonese; technical follow-up may use zh-HK unless the user asks otherwise.

## Central conclusion so far

Do **not** frame the choice as “KataGo *or* Astra.” Use **role-specialized teachers**:

1. **KataGo — numerical chess/Go strength teacher**: source of trustworthy relative move-quality information, search-derived policy/visit targets, value/winrate, score/score lead, ownership, principal variations, and calibrated engine analysis (subject to limits of visits and settings).
2. **GPT-6 Astra — research, reasoning, and data-selection collaborator**: propose hard positions, discover failure modes, curate candidate curricula, propose controlled experiments, and produce natural-language commentary **grounded in KataGo analysis**. Use Astra to help build and debug tools/code where useful.
3. **Rules engine + KataGo — verifier**: reject illegal board states and moves; use sufficiently strong, uniform engine analysis before treating Astra suggestions as examples or claims about move quality.
4. **Student — lightweight board neural net** for M4 inference, not a language model by default. A commentary decoder is optional and separate; prose from Astra cannot simply be plugged into numeric prediction-head losses.

**Hypothesis, not established fact:** Astra-guided example selection might train the student more efficiently than random/stratified sampling or standard uncertainty sampling. This needs a controlled ablation, and may fail to show a gain.

## Evidence and correct interpretation

**LoGos research** — *Mixing Expert Knowledge: Bring Human Thoughts Back To the Game of Go*:
- Paper: https://arxiv.org/html/2601.16447v1
- GitHub (previously referenced): https://github.com/Entarochuan/InternGo-LoGos
- Public dataset/model links mentioned previously (re-verify existence, access, license, and exact contents before use): https://huggingface.co/datasets/YichuanMa/Expert-Go-SFT-100K and https://huggingface.co/YichuanMa/LoGos-7B
- Earlier discussion summarized its approach as millions of KataGo-annotated positions, structured expert reasoning + general CoT cold-start SFT, then KataGo-guided GRPO of a Qwen-derived LLM. The reported ~88% on KataGo-Bench is **candidate-move agreement**, **not** a direct 19×19 match-win rate over KataGo.
- Earlier discussion cited a human evaluation with very different numbers for move correctness (~96.5%) and commentary/explanation correctness (~55.6%) on its specific sample. The lesson is that a plausible explanation is not automatically a faithful tactical explanation; verify wording and measurement details against the paper.
- Its multi-GPU training scale is impractical for this one-L40S/five-day project. Borrow *methods* rather than its entire LLM training recipe.

**GoBench** — https://rolandgao.com/blog/gobench/
- The user's quoted report, dated 2026-11-03, gives tool-free 9×9 benchmark Elo: GPT-6 Astra max reasoning **2567 ±140**, KataGo “fastest” **3329 ±31**, KataGo “strongest” **4423 ±35**.
- These are **benchmark-specific 9×9** Elo numbers, not human ranks and **not** a direct 19×19 comparison or evaluation of tool-assisted Astra. Treat as externally reported, **not independently reproduced** in this conversation.
- They favor KataGo as direct move-quality teacher, but do **not** answer whether Astra is useful for curation, explanation, coding, or hypothesis generation.

**KataGo machine-readable analysis**:
- https://github.com/lightvector/KataGo/blob/master/docs/Analysis_Engine.md
- https://github.com/lightvector/KataGo
- Distinguish **pre-search `policy`** from **search-derived `moveInfos[].visits`** and move values; also inspect root `winrate`, `rawWinrate`, `scoreLead`, and `ownership` if enabled. Check score/winrate perspective, board dimensions, komi, rules, resign/pass handling, validity masks, network output versions, and whether a field is available for the selected analysis settings.
- Astra can output JSON, but valid JSON with numerical probabilities is not evidence of accuracy or calibration. A prose answer such as “D4 develops influence” is not equivalent to a 362-entry distribution and spatial ownership targets.

## Proposed student and objectives (not committed)

- Input: explicit 19×19 board features (plus rules, side to move, history/ko info where required), **not just the textual move transcript**; LoGos highlighted sequential-context issues with long move histories.
- Example output heads: **362 policy logits** (361 intersections + pass), **value**, **score**, **361-cell ownership**. Loss candidate: policy cross-entropy/KL + value BCE/regression + score Huber + spatial ownership loss, balanced by calibrated weights. This is a design proposal, not a reported LoGos architecture.
- Teacher target choices must be made explicitly: raw policy vs normalized MCTS visits; search budgets; score/value perspectives and player-to-move normalization; ownership conventions; legal mask and pass; opening/midgame/endgame stratification.
- M4 deployment likely requires a compact inference architecture and possible quantization; choose **MLX vs Core ML** only after benchmarking relevant actual workload, throughput, search integration, model footprint, and latency. No validated M4 measurements exist yet.
- Avoid placing a large autoregressive LLM on *every* MCTS node; keep any optional commentary assistant outside the tight Go-search inference loop.

## Most valuable controlled experiment

Compare all three, holding training steps/model architecture and teacher labeling budget equal (and using disjoint positions/games for testing):

| Arm | Position selection | Decision labels | Question |
|---|---|---|---|
| **A: Baseline** | Random/stratified Go positions | KataGo | What can ordinary distillation do? |
| **B: Automated active learning** | High student uncertainty, teacher-student disagreement, etc. | KataGo | Does standard curation help? |
| **C: Astra-guided active selection** | Astra identifies failure categories, candidate position filters/curriculum, then rules validation | KataGo | Does Astra add measurable gain beyond B? |

Measure **19×19 head-to-head strength** under controlled rules/komi/time or visit budgets; policy KL/top-k agreement; value calibration and score MAE; tactical held-outs; catastrophic illegal-move rate; and **actual M4 inference/search latency and peak memory**. GoBench 9×9 and LoGos top-k alone are insufficient. Use a held-out test corpus with game-level splits to prevent leakage. Capture teacher analysis budget/cost, Astra token cost, and experiment seed variance.

Astra's ideal workflow: **student error report → Astra proposes a difficulty category or selection rule → legal positions selected/generated → KataGo analyzes → accepted examples enter training → held-out evaluation**. Candidate diagrams/explanations/variations are **proposals**, not labels until validated. As a lower-risk role, Astra can also read engine PVs and help generate commentary, but explanations need additional verification if used as ground truth.

## Preliminary five-day sequence (draft, not a promise)

1. **Day 1:** verify available KataGo nets and API; build reproducible rules-validated position extraction and structured-label pipeline; create held-out test sets.
2. **Day 2:** train/evaluate compact board-network baseline on the L40S; benchmark data throughput.
3. **Day 3:** collect student errors, select matched-size B and C training subsets; use Astra selectively for hypotheses/filters, not millions of long CoT generations.
4. **Day 4:** run paired/controlled A/B/C tests and 19×19 match evaluation within compute limits; establish whether Astra adds value.
5. **Day 5:** export/quantize the best candidate and profile **real** M4 16 GB local inference, memory, and game-search throughput; report limitations and follow-up work.

If five days are too restrictive for statistically useful Elo differences, prioritize a reproducible end-to-end demonstration plus honest uncertainty instead of asserting state-of-the-art strength.

## Decisions still open for the next agent

- Which exact KataGo teacher checkpoint(s), training dataset(s), and license/compliance terms? Compare previously mentioned TF2/TF3 checkpoints by expected strength, analysis throughput on L40S, and available binaries/compatibility; no checkpoint selected.
- What student backbone and size will satisfy M4 16 GB **with MCTS and search state**, not merely fit the weights?
- What labeling/search budget per position, and how are teacher policy/value/ownership targets defined and normalized?
- How much inference compute will the student receive per move (visits, latency target)? Which rulesets/komi/9×9 vs 19×19 evaluation settings?
- Does Astra get **board+candidate analysis** as input, or only aggregated student failure summaries? Define JSON schemas, prompts, request/token budget, and how selection proposals are automatically verified.
- Can we isolate a true marginal improvement of Astra curation over cheaper baselines under the one-GPU / five-day constraint?
- What does “cutting-edge” mean operationally: novel training technique, actual competitive playing strength, sample efficiency, or edge search performance? Avoid equating one research-inspired idea with proven novelty.

## Suggested skills for the next agent

The currently discoverable Skill catalog does **not** include a dedicated KataGo/Go-ML engineering skill. Call the Skill tool **if preparing an artifact**, as follows:

- **`artifact-template-system-design`** (`skills://plugins/openai-templates/artifact-template-system-design`) — for a formal KataGo→Astra→student pipeline architecture/specification.
- **`artifact-template-experiment-analysis`** (`skills://plugins/openai-templates/artifact-template-experiment-analysis`) — for an A/B/C methodology, measurement, and ablation report once experiments exist.
- **`artifact-template-project-tracker`** (`skills://plugins/openai-templates/artifact-template-project-tracker`) — if the user asks for a tracked five-day execution plan.

For code, research and benchmark verification, use normal source/documentation and execution tools; do not pretend a dedicated Go-engine skill exists. Only invoke template skills when those particular artifact types are requested.

## Suggested next response

Lead with a concrete, testable **KataGo × Astra co-teaching architecture** and identify the *minimum experiment that would justify Astra's API cost*. Explain in zh-HK if convenient. Do not claim implementation has happened. If proceeding to implementation, start by verifying KataGo outputs/checkpoint compatibility, selecting an edge-sized student, and specifying exact datasets, schemas, metrics, and compute budgets before training.

## References (do not duplicate original material)

- LoGos paper: https://arxiv.org/html/2601.16447v1
- LoGos code: https://github.com/Entarochuan/InternGo-LoGos
- GoBench results: https://rolandgao.com/blog/gobench/
- KataGo analysis API: https://github.com/lightvector/KataGo/blob/master/docs/Analysis_Engine.md
- KataGo source: https://github.com/lightvector/KataGo
- GPT-6 Astra API documentation referenced in conversation: https://developers.openai.com/api/docs/models/gpt-6-astra

_No secrets, user identifiers, API keys, or personally identifiable information are included._
