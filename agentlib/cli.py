"""Command-line interface: ``python -m agentlib <command>``.

Core commands: ``validate``, ``registry``, ``eval``, ``install``, ``list``.
Framework modules in :mod:`agentlib.frameworks` that define
``register(subparsers)`` add their own commands automatically.
"""
from __future__ import annotations

import argparse
import importlib
import json
import pkgutil
import sys
from dataclasses import asdict
from pathlib import Path

from agentlib import __version__
from agentlib.paths import repo_root


def _cmd_validate(args) -> int:
    from agentlib.validate import CHECKS, validate_all

    issues = validate_all(Path(args.root) if args.root else None, args.only or None)
    errors = [i for i in issues if i.level == "error"]
    warnings = [i for i in issues if i.level == "warning"]
    for i in issues:
        print(i, file=sys.stderr if i.level == "error" else sys.stdout)
    checks = args.only or list(CHECKS)
    print(f"Checked: {', '.join(checks)}. {len(errors)} error(s), {len(warnings)} warning(s).")
    if errors or (args.strict and warnings):
        return 1
    return 0


def _cmd_registry(args) -> int:
    from agentlib.registry import build_registry, write_registry

    root = Path(args.root) if args.root else repo_root()
    if args.write:
        print(f"wrote {write_registry(root)}")
        return 0
    current_path = root / "registry.json"
    fresh = build_registry(root)
    if args.check:
        if not current_path.is_file() or json.loads(current_path.read_text()) != fresh:
            print("registry.json is stale; run `python -m agentlib registry --write`", file=sys.stderr)
            return 1
        print("registry.json is up to date")
        return 0
    print(json.dumps(fresh, indent=2))
    return 0


def _cmd_list(args) -> int:
    from agentlib.registry import build_registry

    reg = build_registry(repo_root())
    kinds = [args.kind] if args.kind else ["skills", "agents", "commands", "workflows", "catalogs"]
    for kind in kinds:
        print(f"\n{kind.upper()}")
        for entry in reg[kind]:
            name = entry.get("name") or entry.get("id")
            desc = entry.get("description") or entry.get("title") or f"{entry.get('items', '')} items"
            print(f"  {name:38} {desc[:100]}")
    return 0


def _cmd_eval(args) -> int:
    from agentlib.evals import runner
    from agentlib.evals.spec import load_suite

    root = repo_root()
    if args.mode == "grade":
        if not (args.skill and args.case and args.output):
            print("grade mode needs --skill, --case and --output", file=sys.stderr)
            return 2
        suite = load_suite(root / "evals" / args.skill / "cases.yaml")
        case = next((c for c in suite.cases if c.id == args.case), None)
        if case is None:
            print(f"unknown case {args.case}", file=sys.stderr)
            return 2
        result = runner.grade_file(case, Path(args.output))
        result.skill = args.skill
        results = [result]
    else:
        suites = runner.discover_suites(root, args.skill and [args.skill])
        if not suites:
            print("no evaluation suites found", file=sys.stderr)
            return 1
        results = []
        for suite in suites:
            if args.mode == "offline":
                results += runner.run_offline(suite)
            else:
                results += runner.run_live(suite, root, args.model, Path(args.out_dir))
    print(runner.summarise(results))
    if args.json:
        Path(args.json).write_text(json.dumps([asdict(r) for r in results], indent=2), encoding="utf-8")
    return 0 if all(r.passed for r in results) else 1


def _cmd_install(args) -> int:
    from agentlib.install import install

    report = install(Path(args.target), components=args.components, skills=args.skill or None,
                     dry_run=args.dry_run, force=args.force)
    print(report)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="agentlib", description="Professional agent library tooling")
    p.add_argument("--version", action="version", version=f"agentlib {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    v = sub.add_parser("validate", help="validate skills, agents, workflows, catalogs, evals, registry")
    v.add_argument("--only", action="append", help="run only this check (repeatable)")
    v.add_argument("--strict", action="store_true", help="treat warnings as errors")
    v.add_argument("--root", help="library root (default: auto)")
    v.set_defaults(func=_cmd_validate)

    r = sub.add_parser("registry", help="print, write or check registry.json")
    g = r.add_mutually_exclusive_group()
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    r.add_argument("--root")
    r.set_defaults(func=_cmd_registry)

    ls = sub.add_parser("list", help="list library components")
    ls.add_argument("kind", nargs="?", choices=["skills", "agents", "commands", "workflows", "catalogs"])
    ls.set_defaults(func=_cmd_list)

    e = sub.add_parser("eval", help="run skill evaluation suites")
    e.add_argument("--mode", choices=["offline", "live", "grade"], default="offline")
    e.add_argument("--skill")
    e.add_argument("--case")
    e.add_argument("--output", help="output file to grade (grade mode)")
    e.add_argument("--model", default=None)
    e.add_argument("--out-dir", default="evals/results")
    e.add_argument("--json", help="write machine-readable results here")
    e.set_defaults(func=_cmd_eval)

    i = sub.add_parser("install", help="install skills/agents/commands into another repository")
    i.add_argument("target", help="path to the target repository root")
    i.add_argument("--components", nargs="+", default=["skills", "agents", "commands"],
                   choices=["skills", "agents", "commands", "workflows", "templates", "catalog"])
    i.add_argument("--skill", action="append", help="install only this skill (repeatable); dependencies follow")
    i.add_argument("--dry-run", action="store_true")
    i.add_argument("--force", action="store_true", help="overwrite files that differ")
    i.set_defaults(func=_cmd_install)

    import agentlib.frameworks as fw

    for mod in pkgutil.iter_modules(fw.__path__):
        module = importlib.import_module(f"agentlib.frameworks.{mod.name}")
        if hasattr(module, "register"):
            module.register(sub)
    return p


def main(argv: list[str] | None = None) -> int:
    import os

    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "command", None) == "eval" and args.model is None:
        from agentlib.evals.runner import DEFAULT_MODEL

        args.model = os.environ.get("AGENTLIB_EVAL_MODEL", DEFAULT_MODEL)
    return int(args.func(args) or 0)


if __name__ == "__main__":
    sys.exit(main())
