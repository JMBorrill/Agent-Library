"""Test helpers: load skill scripts by path (skill dirs contain hyphens) and run CLIs."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / ".claude" / "skills"

try:  # optional, used to validate script JSON output against published schemas
    import jsonschema  # type: ignore
except ImportError:  # pragma: no cover
    jsonschema = None


def skill_path(skill: str, *parts: str) -> Path:
    return SKILLS.joinpath(skill, *parts)


def load_script(skill: str, script: str):
    """Import .claude/skills/<skill>/scripts/<script>.py as a module."""
    path = skill_path(skill, "scripts", f"{script}.py")
    mod_name = f"skill_{skill.replace('-', '_')}_{script}"
    spec = importlib.util.spec_from_file_location(mod_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(module)  # type: ignore[union-attr]
    finally:
        sys.path.remove(str(path.parent))
    return module


def run_cli(skill: str, script: str, *args: str) -> subprocess.CompletedProcess:
    path = skill_path(skill, "scripts", f"{script}.py")
    return subprocess.run([sys.executable, "-I", str(path), *map(str, args)],
                          capture_output=True, text=True, cwd=ROOT, timeout=120)


def run_json(skill: str, script: str, *args: str) -> tuple[int, dict]:
    proc = run_cli(skill, script, *args, "--json")
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:  # pragma: no cover - surfaced as test failure
        raise AssertionError(f"invalid JSON from {script}: {exc}\nSTDOUT:{proc.stdout}\nSTDERR:{proc.stderr}")
    return proc.returncode, data


def assert_schema(testcase, instance, schema_path: Path) -> None:
    if jsonschema is None:
        testcase.skipTest("jsonschema not installed")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    jsonschema.validate(instance, schema)


def rules(findings: list[dict], severity: str | None = None) -> set[str]:
    return {f["rule"] for f in findings if severity is None or f["severity"] == severity}
