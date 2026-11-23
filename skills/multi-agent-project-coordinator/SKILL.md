---
name: multi-agent-project-coordinator
description: Plan and coordinate AI engineering teams across GitHub projects, assign and track tasks, collect verification evidence and require approval for changes to linked repositories. Use for multi-agent GitHub coordination and engineering workflow management.
---

# Multi-Agent Project Coordinator

## Scope

A repository-installable skill for human-directed agent coordination. Agent definitions alone **do not** launch autonomous workers. The coordinator repository's **only editing branch is `main`**. Linked target projects have separate branch policies that must be discovered before changing them.

## Procedure

1. **Discover:** Inspect the target project repository, goal, stack, integrations, risks, budgets and permissions. Do not assume credentials or paid tool access.
2. **Propose a team:** Recommend 1–2 agents for small projects, 3–4 for typical apps, and 5–8 only if separate specialties justify the extra coordination. Present model/provider choices as proposed until configured; request owner approval of team, costs and access.
3. **Configure:** Treat `agents/team.json` and `agents/branch-policy.json` as authoritative. Follow `AGENTS.md`. Keep the coordinator repository's edits on **main only**, and preserve each target repository's existing branches.
4. **Plan:** Register a target project once and store its tasks in one `tasks/<project>/tasks.json`. Each task has unique ID, priority, owner, dependencies, acceptance, artifacts, evidence and the latest action.
5. **Assign:** `agentsctl dispatch --project <slug>` shows a proposal. Only after owner approval use `agentsctl dispatch --project <slug> --apply` to assign records. Neither command calls models or changes GitHub.
6. **Implement and review:** An explicitly authorized worker can implement a task in a target project following that project's permissions, testing and review practices. Do not automatically commit or merge to target projects, deploy or remove branches.
7. **Verify:** Mark DONE only with passing tests, a reviewer other than the author, explicit owner approval, supporting evidence, completed dependencies and resolved blockers.
8. **Report:** Show PLANNED / IN_PROGRESS / IN_REVIEW / BLOCKED / DONE accurately and distinguish NOT TESTED from VERIFIED.

## Install from GitHub

```bash
npx skills add asgmodel/Multi-Agents-Coordinator --skill multi-agent-project-coordinator
```

The CLI can be installed separately via `python -m pip install "git+https://github.com/asgmodel/Multi-Agents-Coordinator.git@main"`.

## Task CLI

```bash
agentsctl init --project demo --repo owner/project
agentsctl add --project demo --id B01 --title "Backend API" --priority P1
agentsctl dispatch --project demo
agentsctl report --project demo
agentsctl validate
```

Never claim that agents, integration, deployment, or CI have been run just because this skill is present.
