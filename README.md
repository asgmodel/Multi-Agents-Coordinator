# Multi Agents Coordinator

A lightweight, **local-first coordination sidecar** that plans AI engineering roles, distributes tasks, and tracks verification across independently managed GitHub projects. It does **not** automatically spawn AI workers or modify your linked projects.

## Install the skill directly from GitHub

Use the [skills CLI](https://skills.sh/) to install the standards-compliant skill:

```bash
npx skills add asgmodel/Multi-Agents-Coordinator --skill multi-agent-project-coordinator
```

Alternatively, specify the full GitHub URL:

```bash
npx skills add https://github.com/asgmodel/Multi-Agents-Coordinator --skill multi-agent-project-coordinator
```

Discover available skills without installation:

```bash
npx skills add asgmodel/Multi-Agents-Coordinator --list
```

The skill definition is at [skills/multi-agent-project-coordinator/SKILL.md](skills/multi-agent-project-coordinator/SKILL.md). Being installable does **not** guarantee immediate appearance in the public [skills.sh](https://skills.sh/) ranking or directory; their external index is controlled by that service.

## Install the task coordinator CLI from GitHub

Python 3.10+ and Git are required. Clone this public repository:

```bash
git clone https://github.com/asgmodel/Multi-Agents-Coordinator.git
cd Multi-Agents-Coordinator
python -m pip install -e .
agentsctl validate
```

Or install the CLI directly without cloning:

```bash
python -m pip install "git+https://github.com/asgmodel/Multi-Agents-Coordinator.git@main"
```

> The direct pip command installs the command-line program, not the skills.sh skill; use the relevant command for the capability you need.

## Quick start

```bash
agentsctl init --project demo --repo owner/your-project
agentsctl add --project demo --id B01 --title "Backend API pagination" --priority P1 --accept "Paginated API works"
agentsctl add --project demo --id F01 --title "Frontend React pagination" --priority P1 --depends B01 --accept "UI loads next page"
agentsctl dispatch --project demo               # Preview only
agentsctl dispatch --project demo --apply       # Assign tasks in local JSON; owner-approved
agentsctl report --project demo
agentsctl validate
```

An approved, reviewed task may be marked DONE only with tests, independent review, owner approval and evidence:

```bash
agentsctl update --project demo --id B01 --status DONE --tests-passed --owner-approved --reviewer AI-04 --evidence "PR #1 and passing tests"
```

For each project the local task registry lives at `tasks/<project>/tasks.json`. It contains current task state, dependencies, evidence and the last action, not duplicate event logs.

## Project Git branch policy

**All edits to this coordinator repository are made on `main`.** The repository does not require `dev`, `tester` or employee branches. The four `.github/agents/*.agent.md` files define proposed agent responsibilities, not Git branches or autonomously running models. Other GitHub projects keep their own independent branch policies.

The owner must authorize actions against other repositories, any model/API spending, secrets changes, merging and deployment. `agents/team.json` is the team roster, `agents/branch-policy.json` is this repository's branch policy, and `AGENTS.md` supplies shared rules.

## Tests

```bash
python -m unittest discover -s tests -v
agentsctl validate
```

GitHub Actions checks the Python tests and skill discovery on pushes to `main`. If CI is pending, do not interpret a commit as verification.
