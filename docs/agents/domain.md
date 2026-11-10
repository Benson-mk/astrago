# Domain docs

This repository has one domain context.

Before exploring the codebase, read the root [GLOSSARY.md](../../GLOSSARY.md). Read ADRs under `docs/adr/` that affect the area being changed. If a glossary or ADR directory is absent, proceed silently; domain-modeling creates terms and decisions lazily when they are resolved.

Use the glossary's canonical terms in issues, hypotheses, designs and tests. If a needed concept is absent, reconsider whether it belongs to this domain or record the gap for domain-modeling.

When a proposal contradicts an existing ADR, identify the ADR and explain why it should be reconsidered rather than silently overriding it.

The layout is one root `GLOSSARY.md` and one `docs/adr/` directory when needed. No context map or per-package glossary is required for this repository.
