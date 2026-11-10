# Issue tracker: GitHub

All active issues, specs and wayfinder maps live in [Benson-mk/astrago GitHub Issues](https://github.com/Benson-mk/astrago/issues). Use the `gh` CLI with `--repo Benson-mk/astrago` for issue commands and `repos/Benson-mk/astrago/...` for REST calls.

## Current map

[Chart a defensible five-day AstraGo experiment](https://github.com/Benson-mk/astrago/issues/1) and its children are canonical GitHub issues, with native sub-issues and dependencies. Current status, claims, answers and newly surfaced children belong on GitHub.

GitHub is the source of truth for issue history, decisions and current progress. The former local tracker and temporary audit folders are not part of the working tree. Original handoff documents remain in the local source checkout.

GPU connection settings are kept in the ignored root `.gpu-node.json`; private connection information must stay out of commits and public issues.

## Issue operations

- Create: `gh issue create --repo Benson-mk/astrago --title "..." --body-file /path/to/body.md`.
- Read: `gh issue view NUMBER --repo Benson-mk/astrago --json number,title,body,labels,comments,assignees,state`.
- List: `gh issue list --repo Benson-mk/astrago --state open --limit 100 --json number,title,labels,assignees,state`, with appropriate label filters. Paginate REST queries when the result set may exceed a CLI limit.
- Update body: `gh issue edit NUMBER --repo Benson-mk/astrago --body-file /path/to/body.md`.
- Comment: `gh issue comment NUMBER --repo Benson-mk/astrago --body-file /path/to/comment.md`.
- Label: `gh issue edit NUMBER --repo Benson-mk/astrago --add-label "LABEL"` or `--remove-label "LABEL"`.
- Close: `gh issue close NUMBER --repo Benson-mk/astrago`; post the resolution comment first.

Use files containing actual newlines for multiline bodies and comments. When a skill says "publish to the issue tracker", create an issue; when it says "fetch the relevant ticket", read it. Repository setup does not itself authorize posting messages unrelated to the invoked workflow.

**PRs as a request surface: no.**

GitHub shares an issue/PR number space. For an ambiguous reference, resolve with `gh pr view NUMBER --repo Benson-mk/astrago`, falling back to `gh issue view` if it is not a PR.

## Wayfinding operations

- **Map:** one issue labelled `wayfinder:map`; its body contains Destination, Notes, Decisions so far, Not yet specified and Out of scope. Refer to maps/tickets by title-linked names in human-facing text.
- **Children:** separate issues labelled only `wayfinder:research`, `wayfinder:prototype`, `wayfinder:grilling` or `wayfinder:task`, linked as native sub-issues. Create issues before wiring relationships. Create missing `wayfinder:` labels when first needed; the current map already has its required map, research, task and grilling labels.
- **Sub-issue linkage:** obtain the child's numeric database ID with `gh api repos/Benson-mk/astrago/issues/CHILD_NUMBER --jq .id`, then use `gh api --method POST repos/Benson-mk/astrago/issues/MAP_NUMBER/sub_issues -F sub_issue_id=CHILD_DATABASE_ID`. List children with `gh api --paginate repos/Benson-mk/astrago/issues/MAP_NUMBER/sub_issues`. These REST operations work with the installed CLI without requiring newer sub-issue flags.
- **Blocking:** use native issue dependencies: `gh api --method POST repos/Benson-mk/astrago/issues/CHILD_NUMBER/dependencies/blocked_by -F issue_id=BLOCKER_DATABASE_ID`. A database ID is neither an issue number nor a GraphQL node ID. Read a blocker ID with the same issue endpoint above.
- **Frontier:** enumerate the map's children in map order, retain open issues without assignees, and exclude those whose REST `issue_dependencies_summary.blocked_by` is greater than zero. Fetch current issue metadata when needed. If that summary is missing, inspect `GET repos/Benson-mk/astrago/issues/NUMBER/dependencies/blocked_by` and their states; never treat missing metadata as zero blockers.
- **Claim:** first assign the selected issue to the driver using `gh issue edit NUMBER --repo Benson-mk/astrago --add-assignee @me`; then work it. An open, unassigned child is unclaimed. Recheck state/assignees before claiming to avoid stale selections.
- **Resolve:** post the answer as a resolution comment, close the child, then append a title-linked gist to the map's Decisions so far. Link assets rather than copying their contents. HITL decisions require the human exchange; charting resolves research questions only.

If native sub-issues are confirmed unavailable, use a task list in the map and a `Part of` link in each child. If native dependencies are confirmed unavailable, use a `Blocked by:` list of title-linked issues and inspect every blocker's state. Authentication failures and transient errors do not establish that a native feature is unavailable.
