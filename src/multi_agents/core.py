"""Local-first, single-file-per-project task coordination. No GitHub writes."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import re
import time

ROOT = Path(__file__).resolve().parents[2]
STATUSES = {"PLANNED", "IN_PROGRESS", "BLOCKED", "IN_REVIEW", "DONE"}
PRIORITIES = {"P0", "P1", "P2"}
SLUG = re.compile(r"^[a-z][a-z0-9-]{0,62}$")
TASK_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")
REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


class Invalid(ValueError):
    """Invalid project, task, or lifecycle change."""


def now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def project_path(project_id: str, root: Path = ROOT) -> Path:
    if not SLUG.fullmatch(project_id):
        raise Invalid("Project id must be a lowercase slug (no slashes).")
    return root / "tasks" / project_id / "tasks.json"


def read_json(path: Path):
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def team(root: Path = ROOT):
    return read_json(root / "agents" / "team.json")["agents"]


def load(project_id: str, root: Path = ROOT):
    path = project_path(project_id, root)
    if not path.is_file():
        raise Invalid(f"Unknown project: {project_id}")
    return read_json(path)


def write(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temp.open("w", encoding="utf-8", newline="\n") as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


@contextmanager
def lock(project_id: str, root: Path = ROOT):
    """Temporary exclusive lock prevents simultaneous CLI writes."""
    path = project_path(project_id, root).with_suffix(".lock")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = None
    for _ in range(60):
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            break
        except FileExistsError:
            time.sleep(0.1)
    if fd is None:
        raise Invalid("Task file is busy; retry. A stale tasks.lock may need removal.")
    try:
        os.close(fd)
        yield
    finally:
        path.unlink(missing_ok=True)


def init(project_id: str, repo: str, root: Path = ROOT):
    if not REPO.fullmatch(repo) or ".." in repo:
        raise Invalid("Repo must be formatted as owner/repository.")
    path = project_path(project_id, root)
    with lock(project_id, root):
        if path.exists():
            raise Invalid("Project already registered; existing data was preserved.")
        data = {"schema_version": 1, "project": {"id": project_id, "repo": repo,
                "default_branch": "main", "integration_branch": "tester"},
                "tasks": [], "last_updated": now()}
        write(path, data)
    return data


def validate(data: dict, root: Path = ROOT) -> list[str]:
    errors = []
    if data.get("schema_version") != 1:
        errors.append("Unsupported schema_version")
    ids = set()
    agents = {a["id"] for a in team(root)}
    tasks = data.get("tasks", [])
    for t in tasks:
        tid = t.get("id", "")
        if not TASK_ID.fullmatch(tid) or tid in ids:
            errors.append(f"Duplicate/invalid task id: {tid}")
        ids.add(tid)
        if t.get("priority") not in PRIORITIES:
            errors.append(f"{tid}: invalid priority")
        if t.get("status") not in STATUSES:
            errors.append(f"{tid}: invalid status")
        if t.get("owner") is not None and t["owner"] not in agents:
            errors.append(f"{tid}: unknown agent")
        deps = t.get("depends_on", [])
        if len(deps) != len(set(deps)) or tid in deps:
            errors.append(f"{tid}: duplicate/self dependency")
        if t.get("status") == "DONE":
            v = t.get("verification", {})
            if not (t.get("owner") and v.get("tests_passed") and v.get("owner_approved") and
                    v.get("reviewer") and v.get("evidence") and not t.get("blockers")):
                errors.append(f"{tid}: DONE requires owner, tests, approval, reviewer, evidence and no blockers")
            if v.get("reviewer") == t.get("owner"):
                errors.append(f"{tid}: self-review is not allowed")
    index = {t.get("id"): t for t in tasks}
    visited, visiting = set(), set()
    def walk(tid):
        if tid in visiting:
            errors.append(f"Dependency cycle at {tid}")
            return
        if tid in visited:
            return
        visiting.add(tid)
        for dep in index[tid].get("depends_on", []):
            if dep not in index:
                errors.append(f"{tid}: missing dependency {dep}")
            else:
                walk(dep)
        visiting.remove(tid)
        visited.add(tid)
    for tid in index:
        walk(tid)
    for t in tasks:
        if t.get("status") == "DONE":
            for dep in t.get("depends_on", []):
                if dep in index and index[dep].get("status") != "DONE":
                    errors.append(f"{t['id']}: DONE before dependency {dep}")
    return list(dict.fromkeys(errors))


def persist(project_id, data, root=ROOT):
    errors = validate(data, root)
    if errors:
        raise Invalid("; ".join(errors))
    data["last_updated"] = now()
    write(project_path(project_id, root), data)


def get_task(data, task_id):
    found = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if not found:
        raise Invalid(f"Unknown task: {task_id}")
    return found


def add(project_id, task_id, title, owner=None, priority="P1", depends=None,
        acceptance=None, scope=None, root=ROOT):
    if not TASK_ID.fullmatch(task_id) or not title.strip():
        raise Invalid("Task ID/title is invalid.")
    with lock(project_id, root):
        data = load(project_id, root)
        if any(t["id"] == task_id for t in data["tasks"]):
            raise Invalid("Duplicate task ID.")
        deps = depends or []
        if len(deps) != len(set(deps)):
            raise Invalid("Duplicate dependencies are not allowed.")
        t = {"id": task_id, "title": title.strip(), "priority": priority,
             "owner": owner, "status": "PLANNED", "depends_on": deps,
             "scope": scope or "", "acceptance": acceptance or [],
             "artifacts": [], "blockers": [],
             "verification": {"tests_passed": False, "owner_approved": False,
                              "reviewer": None, "evidence": []},
             "last_action": {"kind": "created", "note": "", "at": now()},
             "updated_at": now()}
        data["tasks"].append(t)
        persist(project_id, data, root)
    return t


def update(project_id, task_id, *, status=None, owner=None, note="",
           blocker=None, clear_blockers=False, artifact=None, evidence=None,
           tests_passed=False, owner_approved=False, reviewer=None, root=ROOT):
    with lock(project_id, root):
        data = load(project_id, root)
        t = get_task(data, task_id)
        if owner is not None:
            t["owner"] = owner
        if blocker and blocker not in t["blockers"]:
            t["blockers"].append(blocker)
        if clear_blockers:
            t["blockers"] = []
        if artifact and artifact not in t["artifacts"]:
            t["artifacts"].append(artifact)
        v = t["verification"]
        if evidence and evidence not in v["evidence"]:
            v["evidence"].append(evidence)
        if tests_passed:
            v["tests_passed"] = True
        if owner_approved:
            v["owner_approved"] = True
        if reviewer:
            v["reviewer"] = reviewer
        if status:
            if status not in STATUSES:
                raise Invalid("Invalid status.")
            if status == "DONE" and t["blockers"]:
                raise Invalid("Resolve blockers before DONE.")
            t["status"] = status
        t["updated_at"] = now()
        t["last_action"] = {"kind": "updated", "note": note, "at": now()}
        persist(project_id, data, root)
        return t


def dispatch(project_id, apply=False, root=ROOT):
    data = load(project_id, root)
    config = read_json(root / "agents" / "team.json")
    agents = config["agents"]
    counts = {a["id"]: 0 for a in agents}
    for t in data["tasks"]:
        if t["owner"] in counts and t["status"] in {"IN_PROGRESS", "IN_REVIEW"}:
            counts[t["owner"]] += 1
    global_remaining = max(0, config["max_total_parallel_tasks"] -
                           sum(t["status"] in {"IN_PROGRESS", "IN_REVIEW"} for t in data["tasks"]))
    proposals = []
    for t in sorted(data["tasks"], key=lambda x: (x["priority"], x["id"])):
        if len(proposals) >= global_remaining:
            break
        if t["owner"] or t["status"] != "PLANNED" or not ready(t, data):
            continue
        title = (t["title"] + " " + t.get("scope", "")).lower()
        scored = []
        for a in agents:
            if counts[a["id"]] >= a["max_active_tasks"]:
                continue
            keywords = a["keywords"]
            match = sum(1 for k in keywords if (k.lower() in title if not k.isascii()
                      else bool(re.search(r"(?<![a-z0-9])" + re.escape(k.lower()) + r"(?![a-z0-9])", title))))
            scored.append((match, -counts[a["id"]], -a["order"], a["id"]))
        positive = [s for s in scored if s[0] > 0]
        if positive:
            best = max(positive)[-1]
        elif any(s[-1] == "AI-04" for s in scored):
            best = "AI-04"
        else:
            continue
        if best:
            proposals.append({"task": t["id"], "owner": best})
            counts[best] += 1
    if apply and proposals:
        with lock(project_id, root):
            live = load(project_id, root)
            for p in proposals:
                task = get_task(live, p["task"])
                if task["owner"] is not None or task["status"] != "PLANNED" or not ready(task, live):
                    raise Invalid("Tasks changed during dispatch. Review before retrying.")
                task["owner"] = p["owner"]
                task["last_action"] = {"kind": "assigned", "note": "Owner-approved CLI dispatch", "at": now()}
                task["updated_at"] = now()
            persist(project_id, live, root)
    return proposals


def ready(t, data):
    index = {x["id"]: x for x in data["tasks"]}
    return not t["blockers"] and all(index.get(d, {}).get("status") == "DONE" for d in t["depends_on"])


def report(project_id, root=ROOT):
    data = load(project_id, root)
    return {"project": data["project"],
            "summary": {s: sum(t["status"] == s for t in data["tasks"]) for s in sorted(STATUSES)},
            "ready": [t["id"] for t in data["tasks"] if t["status"] == "PLANNED" and ready(t, data)],
            "blocked": [t["id"] for t in data["tasks"] if t["blockers"] or not ready(t, data)],
            "last_updated": data["last_updated"]}


def validate_all(root=ROOT):
    problems = {}
    for path in sorted((root / "tasks").glob("*/tasks.json")):
        errors = validate(read_json(path), root)
        if errors:
            problems[path.parent.name] = errors
    return problems
