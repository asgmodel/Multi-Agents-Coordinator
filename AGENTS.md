# Multi Agents Coordinator operating rules

- This repository is an independent sidecar; linked projects cannot be modified without owner authorization.
- **Commit all changes to this repository only on `main`**. Do not create `tester`, `dev`, agent or task branches here.
- Read `agents/team.json` for the team and `agents/branch-policy.json` for this repository's Git rules; do not repeat their configuration in project task records.
- Give every target project exactly one `tasks/<slug>/tasks.json`. Keep unique tasks and nonduplicated dependencies; update only current state, evidence and last action.
- Sequence: Discover → Propose → Approve → Assign → Implement → Test → Review → Verify → Report.
- Agent Markdown files are *roles*, not autonomously running processes or activated models.
- Apply each target project's own branch and review policies; never silently switch their branch structure.
- Do not merge, deploy, force-push, delete branches, modify secrets or use paid models without owner permission.
- Require passed tests, independent review, explicit owner approval and evidence to mark a task DONE.
