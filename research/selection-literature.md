# Evidence for Astra-guided Go position selection

Retrieved and assessed: **2026-11-10 (Asia/Hong_Kong)**.
Research question: **What evidence supports an Astra selection experiment beyond competent automated baselines?**
Status: source investigation complete; no training, match evaluation, or independent reproduction was performed. Final experiment choices remain with the human-in-the-loop contract ticket.

The four papers justify a testable selection hypothesis and several evaluation precautions. None establishes that Astra improves 19×19 Go continuation learning, and this bounded reading cannot establish novelty. The useful experimental question remains whether C improves on a credible B under the same information and declared compute budgets.

## Source evidence and transfer limits

### Accelerating Self-Play Learning in Go

**Verified source:** David J. Wu, [arXiv:1902.10565v5](https://arxiv.org/html/1902.10565v5), revised 2020-11-09; full HTML methods, ablations and appendices accessed. The record describes an AAAI20-RLG workshop presentation.

The paper studies self-play, combining search-budget randomization, policy-target pruning, global context and auxiliary learning targets. Its ablations support retaining useful native supervision rather than stripping a continuation model to a minimal policy/value imitation objective. It evaluates both fixed-search and fixed-time matches. The main run used roughly 27 V100s over 19 days; its reported speedup is a comparison between training systems, not an expected speedup for this sprint. Its historical architecture and recipe do not establish compatibility of current checkpoints. **Inference:** preserve the current native recipe until a specific change is justified; use the paper to motivate budget accounting and whole-engine evaluation, not to promise a five-day replication. Relevant sections: 3–5, especially 5.1–5.2.

### Move Quality Beyond Arena: Pure Distillation for Small Go Networks

**Verified source:** Taiki Kojima, [Research Square v1](https://www.researchsquare.com/article/rs-9749016/v1), posted 2026-05-19; [exact primary PDF](https://assets-eu.researchsquare.com/files/rs-9749016/v1_covered_f5cf1016-f8c0-4fc4-8fd8-248b4132ca5e.pdf). This is a preprint; no peer-reviewed publication was established. Full text and relevant tables were read, with PDF pages 7–9 visually checked.

The study distils a KataGo teacher into a roughly seven-million-parameter custom student. Its diagnostic set contains 100 positions; reported top-one agreement rises from 10% to 16% in the deeper-label step. This is teacher agreement, not Elo. Arena results were compromised by a 150-move cap and 90–100% unfinished games. Crucially, Table 1 initializes the deeper-label model from its predecessor: the comparison also adds continuation training, so it does not isolate label depth under matched initialization. Policy-target construction is insufficiently specified to serve as our tensor contract. **Inference:** use oracle agreement as a diagnostic, retain valid completed-game evaluation, and rerun any depth comparison from a common checkpoint. Native KataGo compatibility and reported speedups from its custom Python search do not transfer automatically. Relevant sections: 3.2–3.4, 4, 5.1–5.3, 6.5 and Appendix A.4.

### From Selection to Generation: A Survey of LLM-based Active Learning

**Verified source:** Xia et al., [ACL 2025 paper](https://aclanthology.org/2025.acl-long.708/) and [full PDF](https://aclanthology.org/2025.acl-long.708.pdf), proceedings pages 14552–14569. This is a published survey, primary evidence for its taxonomy rather than an independent reproduction of the surveyed methods.

It separates querying—selection or generation—from annotation, and catalogues conventional uncertainty, disagreement and diversity-based approaches alongside LLM methods. It treats LLM querying expense as part of the stopping budget. Those distinctions fit a numerical Go teacher with an LLM selector. They do not validate LLM Go labels or establish a Go-specific advantage. **Inference:** an executable selector over a common legal pool is an appropriate narrow hypothesis; a conventional baseline deserves uncertainty/error information and diversity control rather than being deliberately weak. A language-model-generated position would introduce an additional validity and distribution problem, so retaining the agreed real-history pool isolates selection. Relevant sections: 2–6 and Appendix B.

### Regret-Guided Search Control for Efficient Learning in AlphaZero

**Verified source:** Tsai et al., [arXiv:2602.20809v1](https://arxiv.org/html/2602.20809v1), submitted 2026-02-24; its arXiv record states acceptance at ICLR 2026. Full methods, experiments and appendices accessed.

RGSC uses outcome-based regret, learned ranking and a prioritized buffer to choose self-play restart states. Experiments include 9×9 Go, 10×10 Othello and 11×11 Hex, not 19×19 Go. The reported trained-model improvement against KataGo is tied to a specified 9×9 opponent/evaluation, not general KataGo strength. Appendix A reports about 150 A6000 GPU-hours per training run and additional compute overhead; neither is a direct L40S estimate. **Inference:** prioritize-error ideas can inform a cheap baseline, but teacher–student disagreement is not the paper’s outcome-defined regret. Reproducing RGSC would change architecture and data generation, crossing this effort’s agreed boundary. Relevant sections: 3, 4.2–4.3, A.1–A.3.

## Candidate comparisons for the contract ticket

These are proposals for a controlled experiment, not decisions already made or source-proven best settings.

| Candidate | Why it is informative | Contract required before comparing |
| --- | --- | --- |
| Random/stratified A | Measures the value of ordinary continuation and pool coverage | Same initialization, legal pool, train steps and label settings |
| Student uncertainty plus diversity B | A cheap selection baseline that avoids selecting near-duplicate positions only | Define uncertainty on legal actions, cap game-level redundancy, measure screening overhead |
| Teacher–student disagreement plus diversity B | Directly targets errors if teacher screening is affordable | Make screening evidence equally available to C and charge every teacher query |
| Astra executable filters C | Tests whether structured hypotheses improve selection using the same development evidence | Freeze features, proposal schema, selection amount, iteration schedule, deterministic replay and API cap |

Choose a single credible primary B before final evaluation. Extra baselines can be developmental diagnostics if the budget supports them; the report does not require a large benchmark suite. If the available pool lacks terminal outcomes, describe any error proxy by its actual definition rather than calling it RGSC regret. One-shot subset selection and an adaptive multi-round curriculum answer different questions; choose one explicitly.

## Falsification and reporting conditions

The handoff already requires the central comparison C versus B. Make its failure conditions concrete in the eventual plan:

- C beating A alone does not demonstrate Astra’s marginal value.
- Better agreement with the labeling teacher alone does not establish stronger offline play. Keep the teacher-relative diagnostic and independent, equal-M4-wall-clock game result separate.
- Identical selected-example counts do not demonstrate matched compute. Screening, label depth, rejected queries, retries and proposal calls enter the relevant ledgers.
- C with extra feature access, extra tuning, a different starting checkpoint or more training cannot isolate the selector effect.
- A match budget unable to distinguish the preregistered meaningful effect yields an inconclusive result; it does not justify a positive claim.
- If C fails the full-cost comparison despite a matched-label/train improvement, report the narrower selection result and the overhead separately.

Use these conditions to define rejection/stop criteria before implementation. This research ticket adds no numerical threshold, batch recipe, API budget or final model choice.

## Access, reproducibility and remaining limits

The browser retriever could not open the Research Square DOI/native page. A read-only HTTP request retrieved the native page, whose embedded metadata linked the exact PDF above. That primary PDF was downloaded (521,403 bytes), text-extracted and selectively rendered using the bundled runtime. Its SHA-256 is `e6bb3a4a614050f706c9ef477743a17cf93dfa411c607a7269f712d01570c0fa`. No secondary synopsis supplies the findings above. Executable artifacts were not verified; no downstream claim relies on their availability.

Repeat this investigation by opening the versioned links, checking the named sections and visually comparing the distillation paper’s Table 1 with its label-depth comparison. No source PDF is redistributed in this report. All numerical results above are author-reported, not project measurements.

The remaining uncertainties are experimental: whether a competent selector improves this pretrained student, whether Astra adds anything beyond it, which targets/pool preserve validity, and whether the measured cost and evaluation precision fit the execution window. None is resolved by citation alone.

## Actual research-method trade-offs

1. Bounded the literature investigation to the four requested works and their relevant methods/ablations. This gives a useful frontier quickly but supports no exhaustive novelty or state-of-the-art claim.
2. Used source inspection rather than reproducing the papers. That preserves the planning boundary and compute budget, leaving reported effects and throughput unvalidated on this hardware.
3. Fetched a small primary PDF after browser extraction failed and visually verified its decisive tables. This adds a reproducible source check without installing tools or relying on a secondary summary; it does not validate the claimed released code or data.
