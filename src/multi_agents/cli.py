"""Command-line entrypoint for project sidecar coordination."""
import argparse
import json
from pathlib import Path
import sys

from . import core


def parser():
    p = argparse.ArgumentParser(prog="agentsctl", description="Multi-project agent task sidecar")
    sub = p.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("init", help="Register a repository (no remote changes)")
    i.add_argument("--project", required=True)
    i.add_argument("--repo", required=True)
    a = sub.add_parser("add", help="Create one unique task")
    a.add_argument("--project", required=True)
    a.add_argument("--id", required=True)
    a.add_argument("--title", required=True)
    a.add_argument("--owner")
    a.add_argument("--priority", choices=sorted(core.PRIORITIES), default="P1")
    a.add_argument("--depends", action="append", default=[])
    a.add_argument("--accept", action="append", default=[])
    a.add_argument("--scope", default="")
    u = sub.add_parser("update", help="Update a task and its latest action")
    u.add_argument("--project", required=True)
    u.add_argument("--id", required=True)
    u.add_argument("--status", choices=sorted(core.STATUSES))
    u.add_argument("--owner")
    u.add_argument("--note", default="")
    u.add_argument("--blocker")
    u.add_argument("--clear-blockers", action="store_true")
    u.add_argument("--artifact")
    u.add_argument("--evidence")
    u.add_argument("--tests-passed", action="store_true")
    u.add_argument("--owner-approved", action="store_true")
    u.add_argument("--reviewer")
    d = sub.add_parser("dispatch", help="Propose assignments; --apply modifies local JSON")
    d.add_argument("--project", required=True)
    d.add_argument("--apply", action="store_true")
    r = sub.add_parser("report")
    r.add_argument("--project", required=True)
    v = sub.add_parser("validate")
    v.add_argument("--project", help="Omit for every project")
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.cmd == "init":
            value = core.init(args.project, args.repo)
        elif args.cmd == "add":
            value = core.add(args.project, args.id, args.title, args.owner, args.priority,
                             args.depends, args.accept, args.scope)
        elif args.cmd == "update":
            value = core.update(args.project, args.id, status=args.status, owner=args.owner,
                                note=args.note, blocker=args.blocker, clear_blockers=args.clear_blockers,
                                artifact=args.artifact, evidence=args.evidence,
                                tests_passed=args.tests_passed, owner_approved=args.owner_approved,
                                reviewer=args.reviewer)
        elif args.cmd == "dispatch":
            value = {"proposals": core.dispatch(args.project, args.apply), "applied": args.apply}
        elif args.cmd == "report":
            value = core.report(args.project)
        else:
            value = core.validate(core.load(args.project)) if args.project else core.validate_all()
            if value:
                print(json.dumps({"valid": False, "errors": value}, ensure_ascii=False, indent=2))
                return 1
            value = {"valid": True}
        print(json.dumps(value, ensure_ascii=False, indent=2))
        return 0
    except (core.Invalid, FileNotFoundError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
