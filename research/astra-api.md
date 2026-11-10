# Astra API evidence for the five-day Go experiment

Retrieved: 2026-11-10 (Asia/Hong_Kong). Research only: no API keys inspected, account settings changed, paid inference requested, or pipeline executed.

Question: What verified Astra API contract and no-API fallback can the plan rely on?

## Evidence-supported answer

The exact requested model is documented as `gpt-6-astra`. Its page lists that same identifier as its current snapshot, rather than a separate dated snapshot. It supports Responses, Chat Completions and Batch; text/image inputs, text output, structured outputs and function calling. Its supported `reasoning.effort` values are `low`, `medium`, `high`, `xhigh`, and `max`. The documented limits are a 1,050,000-token context, 922,000 maximum input tokens and 128,000 maximum output tokens. These are provider ceilings, not sensible experiment allocations. [GPT-6 Astra model](https://developers.openai.com/api/docs/models/gpt-6-astra)

The exact model can therefore remain the proposed C-arm selector; there is no documentation-based need to substitute another model. This does **not** establish the user's API entitlement, billing capacity, project restrictions, latency, or Go-curation quality. API access follows the organization/project associated with the key; enabling Astra in a ChatGPT workspace does not itself grant API access. [Workspace availability](https://learn.chatgpt.com/docs/enterprise/workspace-model-availability#gpt-6-astra-in-enterprise)

## Documented interface and validation boundary

A minimal prospective integration can use `POST https://api.openai.com/v1/responses`, `model: "gpt-6-astra"`, bounded `input`, and `text.format` with `type: "json_schema"`, a schema name, `strict: true`, and the schema. The official guide demonstrates this endpoint/model pairing. All object fields must be required; nullable unions can represent optional values, and objects require `additionalProperties: false`. A strict schema controls representation, not factual Go correctness. Completion, refusal and incomplete/truncated output must be handled before accepting a proposal. [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs)

`max_output_tokens` bounds generated tokens including non-visible tokens; it is not a visible-JSON word budget. The response usage object provides `input_tokens`, `input_tokens_details.cached_tokens`, `output_tokens`, `output_tokens_details.reasoning_tokens`, and `total_tokens`. Do not add reasoning tokens to `output_tokens` again. [Token counting](https://developers.openai.com/api/docs/guides/token-counting#understand-output-token-counts), [reasoning usage](https://developers.openai.com/api/docs/guides/reasoning#managing-the-context-window)

The model guide explicitly excludes `none` effort for Astra. No temperature/seed determinism guarantee was established in this research. For replay, save accepted proposals and execute their deterministic selectors locally; do not claim that rerunning an LLM call reproduces its original text. Record the returned model identifier, request parameters and timestamps because the retrieved model page supplies no separately dated snapshot. [GPT-6 guide](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6-astra)

## Current published token prices

USD per million tokens, as retrieved; refresh before committing a spending budget. These are published prices, not an account invoice or evidence that the user can access a service tier.

| Standard processing | Input | Output | Cached input | 30-minute cache write | 12-hour cache write |
| --- | ---: | ---: | ---: | ---: | ---: |
| Input context ≤272K tokens | $10 | $50 | $1 | $12.50 | $25 |
| Input context >272K tokens | $20 | $75 | $2 | $25 | $50 |

Batch/Flex prices are half Standard; Fast prices are twice Standard; the pricing table also lists regional processing uplifts. Caching has write costs as well as read discounts, so a ledger cannot assume every non-cached input token costs exactly the simple input rate. [API pricing](https://developers.openai.com/api/docs/pricing#astra)

For illustration only, an uncached short-context Standard request with 10,000 input tokens and 4,000 **total** output tokens costs $0.30 before any applicable cache-write, regional, tool or other charges. This is arithmetic from the table, not a proposed user-approved cap. The experiment should reserve the worst permitted request cost before dispatch, account for retries and pending requests, and reconcile actual usage with the chosen pricing mode. Initial synchronous text-only requests without hosted tools make that ledger simpler; the human must choose the service tier, caching policy and caps.

Rate limits vary by model and apply at organization/project levels. Requests, tokens and batch queue capacity can independently bind; public documentation does not reveal this account's remaining capacity. Provider spend alerts merely notify. Configured hard spend limits can stop requests, but enforcement is delayed enough that recorded spend may slightly exceed the limit. A strict experiment cap therefore also needs a local reservation ledger and bounded retry/concurrency policy. [Rate limits](https://developers.openai.com/api/docs/guides/rate-limits#how-do-these-rate-limits-work), [spend limits](https://developers.openai.com/api/docs/guides/spend-limits)

## Minimal proposal contract for a later human decision

This is a recommended **design option**, not an adopted or implemented JSON schema. It deliberately selects from existing legal histories rather than generating boards or numerical training labels.

The input envelope should identify immutable candidate-pool and development-report hashes, a versioned feature catalogue, permitted predicates, per-feature provenance/cost, allowed count bounds, fixed teacher identity/settings, and the disjoint validation measurements. Only development evidence is included. Give B the same eligible information and account for teacher-derived features in both arms.

The output could contain these required fields:

| Field | Meaning and local acceptance check |
| --- | --- |
| `schema_version`, `proposal_id` | Recognized contract version and unique proposal identity. |
| `pool_hash`, `development_report_hash` | Exactly the manifests supplied to this request. |
| `predicates` | Bounded list of allowed feature/operator/value objects; feature definitions are versioned and executable by an existing selector. No arbitrary code strings. |
| `selection_count` | Integer within the caller's remaining label budget and actual eligible pool size. |
| `ranking_rule`, `tie_break_seed` | Allowlisted deterministic ordering and reproducible tie-breaking. |
| `required_teacher_features` | Which additional analyses the rule would need; an empty list is explicit. Local code computes their real cost before approval. |
| `motivation` | Short hypothesis explaining the proposed failure category; never a label. |
| `validation_measurement_ids` | Existing development measurements allowed for this proposal, with an explicit expected direction. The sealed final test is unavailable. |

Require bounded list/string sizes and full application validation. Enumerate these failure modes **before** any isolated implementation/testing: unknown feature/operator; stale manifest; illegal or missing history; candidate count underflow; duplicate selections; hidden teacher-analysis cost; B/C information asymmetry; final-test leakage; incomplete/refused response; unsupported schema; rate-limit or access error; retry overspend; and nondeterministic selector replay. A later E2E artifact should link the request/response and usage, accepted predicate object, validation result, selected position IDs and hashes, seed, feature provenance, and cost ledger. No such artifact exists yet.

The caller, not Astra, should compute candidate legality, exact selected IDs/count, cost consumption and target correctness. This keeps the API a proposal source. Rejecting one proposal should consume its already-incurred API cost without consuming unapproved teacher-label budget.

## What remains for an authorized preflight and decision

The documentation investigation is complete enough to frame the API decision, while these implementation prerequisites remain unverified:

1. Authorized API organization/project, key availability, exact model entitlement and acceptable data handling.
2. Chosen request count, input/output token caps, total USD cap, service tier, caching policy, concurrency and retry limits. The user has not supplied a spend cap in this session.
3. One bounded exact-model structured-output request using the final schema, with observed status, latency, usage fields and any refusal/incomplete handling.
4. Local predicate validation and replay against a small known pool; an accepted JSON document alone cannot satisfy this gate.

If access, cost or reliability fails, the plan may continue with A/B plus unchanged deployment baselines and report **Astra's marginal value untested**. Previously saved, provenance-complete Astra proposals could support a clearly labelled replay experiment only if permitted and uncontaminated. A different model requires a new named arm and human agreement; it must not be reported as Astra. Choosing between these branches belongs to the later HITL experiment-contract ticket.

## Research-method trade-offs actually made

- Used official public documentation without authenticated requests. This establishes a documented interface and prices while leaving account entitlement and empirical response behavior unknown; it incurred no inference spend.
- Scoped the evidence to Astra and the smallest text/structured-output selection interface. This avoids accidental model substitution and unnecessary tool dependencies, while leaving richer board-image and interactive tool workflows unexplored.
- Proposed selector replay as the reproducibility boundary because no dated snapshot or generation determinism was established. This supports repeatable selected data but does not reproduce the original model's proposal-generation process.

The full generated Responses method-reference fetch returned a skeletal page, so detailed claims above rely on fetched guides with concrete examples instead of treating a search-result excerpt as complete API evidence. All remaining schema choices and caps are proposals for review, not provider guarantees or implemented contracts.
