# Project instructions

Always begin by thinking, researching (gathering an abundance of context and understanding what is relevant), planning, confirming the feasibility and optimality of the approach, verifying assumptions and premises, conducting experiments, and identifying potential pitfalls before implementation.

Make technical decisions and navigate trade-offs using common sense, project constraints, and established project rules. Report every actual trade-off upon task completion, once each. The advisor reports additional trade-offs only when distinct from those already recorded.

For technical decisions, choices, and designs, designate an advisor subagent using `gpt-6.1-sol` at `xhigh` reasoning with the `validate-gpt-code-review` skill. The advisor acts as the project's BDFL and critically evaluates decisions, especially common GPT biases.

Consult the advisor early only for a specific unresolved decision whose consequences would be costly to reverse. State the decision and why early consultation is necessary. Otherwise, conduct the review after the task is complete, focusing on egregious technical decisions and GPT-related biases.

- Never write unit tests after writing the code.
- Highly prefer E2E tests as the sole testing mechanism for complex features. Finish E2E tests with a verifiable, repeatable artifact.
- When testing a system in isolation, first write all the ways it could fail, then write the code.

## Agent skills

### Issue tracker

Use GitHub Issues as the sole active tracker. When creating, fetching, claiming, or resolving issues or wayfinder maps, read [docs/agents/issue-tracker.md](docs/agents/issue-tracker.md), including the current map and migration details.

### Triage labels

When assigning triage states, use the canonical mapping in [docs/agents/triage-labels.md](docs/agents/triage-labels.md).

### Domain docs

This is a single-context repository. Before exploring domain behavior or proposing changes, follow [docs/agents/domain.md](docs/agents/domain.md) for the root glossary and relevant ADRs.
