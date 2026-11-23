---
name: multi-agent-project-coordinator
description: Plan and coordinate a small AI engineering team across GitHub projects, triage and assign tasks, and require evidence and owner approval before integration. Use for orchestrating AI coding agents, GitHub branch workflows, project task dispatch, and multi-agent delivery reviews.
---

# Multi-Agent Project Coordinator

## When to use

Use when a project owner wants to form or coordinate AI engineering roles, break down work, assign tasks, or safely coordinate changes across GitHub repositories.
This skill is an *instruction set*, not a daemon, autonomous LLM worker, or authorization to modify target repositories.

## Workflow

1. **Discover:** Ask for or inspect the target repository, product scope, technology, environment, budgets, and risks. Do not invent repository access, credentials, or model runtime.
2. **Propose:** Recommend the smallest useful team: 1–2 agents for small projects, 3–4 for typical apps, 5–8 only when separate specialties justify them. Explain assignments and ask the owner to approve team scope, permissions, and expenses.
3. **Configure:** Read `agents/team.json` and `agents/branch-policy.json` in this coordinator repository as the authoritative team and workflow definitions. Preserve existing target project settings.
4. **Register and plan:** For each target project, record a single `tasks/<project>/tasks.json`, with task ID, priority, assignee, dependencies, acceptance criteria, evidence, and last update. Do not duplicate task records or infer derived dependencies.
5. **Preview dispatch:** Use `agentsctl dispatch --project <slug>` to **propose** assignments. Only after approval, `agentsctl dispatch --project <slug> --apply` makes local JSON assignments. Neither command executes agents or changes GitHub projects.
6. **Coordinate work:** Human- or tool-invoked developers change only approved paths, run tests, and submit PRs to `tester`. Treat role definitions under `.github/agents/` as instructions, not live workers.
7. **Review and integrate:** Verify PR, test evidence, dependencies, and security. Require explicit owner authorization before merge/deploy/delete/force-push. Mark DONE only after independent review, passed tests, approval, and evidence.
8. **Report:** Show PLANNED, NOT TESTED and VERIFIED accurately; summarize progress, risks, blockers, cost, and next approval.

## CLI quick start

From the coordinator repository after `python -m pip install -e .`:

```bash
agentsctl init --project demo --repo owner/target-repo
agentsctl add --project demo --id B01 --title 'Backend API pagination' --priority P1 --accept 'Paginated response verified'
agentsctl dispatch --project demo
agentsctl report --project demo
agentsctl validate
```

Only use `--apply` after owner approval. Verify project branch names: this coordinator uses `main`, `tester`, `dev`, `AI-01` to `AI-04`, and `Multi-Agents-Coordinator`; target repositories may differ. Never commit secrets or misrepresent automated execution.
