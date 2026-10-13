#!/usr/bin/env python3
"""Check dependency manifests for unpinned / range-specified versions and missing lockfiles.

Manifests found (recursively, skipping node_modules/.venv/.git): requirements*.txt, package.json,
pyproject.toml. Application mode (default) expects exact pins or a lockfile; library mode accepts
ranges (libraries should not over-constrain consumers) and only reports them as info.

Usage:
  dependency_pin_check.py PATH [PATH ...] [--mode app|library] [--json]
Exit codes: 0 no errors, 1 errors, 2 unreadable input.

Scope: version-specifier hygiene only. It does not detect vulnerable, malicious or abandoned
packages, does not resolve transitive dependencies and does not verify lockfile integrity.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from collections import Counter
from pathlib import Path

SKIP = {"node_modules", ".venv", "venv", ".git", "__pycache__", "dist", "build"}
NPM_LOCKS = ("package-lock.json", "npm-shrinkwrap.json", "yarn.lock", "pnpm-lock.yaml", "bun.lockb", "bun.lock")
PY_LOCKS = ("poetry.lock", "uv.lock", "pdm.lock", "Pipfile.lock", "pylock.toml")
SEMVER_EXACT = re.compile(r"^v?\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
PEP508 = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)\s*(\[[^\]]*\])?\s*(.*)$")
COMMIT = re.compile(r"[@#][0-9a-f]{40}\b")


def _finding(fid: str, severity: str, rule: str, message: str) -> dict:
    return {"id": fid, "severity": severity, "rule": rule, "message": message}


def pep508_pinned(spec: str) -> tuple[bool, str]:
    """Return (exact_pin, specifier) for the version part of a PEP 508 string."""
    spec = spec.split(";", 1)[0].strip()
    if "@" in spec and not spec.startswith(("==", "===")):
        return bool(COMMIT.search(spec)), spec  # direct reference: pinned only with a commit hash
    parts = [p.strip() for p in spec.split(",") if p.strip()]
    exact = len(parts) == 1 and re.fullmatch(r"===?\s*[^*\s]+", parts[0]) is not None
    return exact, spec


def check_requirements(path: Path, mode: str) -> tuple[list[dict], int]:
    findings: list[dict] = []
    text = path.read_text(encoding="utf-8").replace("\\\n", " ")
    count = 0
    hashed = 0
    for n, line in enumerate(text.splitlines(), 1):
        line = re.sub(r"(^|\s)#.*$", "", line).strip()
        if not line:
            continue
        loc = f"{path.as_posix()}:{n}"
        if line.startswith(("-r", "-c", "--requirement", "--constraint")):
            findings.append(_finding(loc, "info", "included-file", f"includes another file ({line}); check it too"))
            continue
        if line.startswith(("--index-url", "--extra-index-url", "-i ", "--find-links", "-f ")):
            continue
        count += 1
        hashed += "--hash=" in line
        if line.startswith(("-e", "--editable")) or "git+" in line or "://" in line:
            if not COMMIT.search(line):
                sev = "error" if mode == "app" else "warning"
                findings.append(_finding(loc, sev, "unpinned-vcs", "VCS/URL dependency without a full commit hash"))
            continue
        m = PEP508.match(line.split("--hash", 1)[0])
        if not m:
            findings.append(_finding(loc, "error", "unparseable-requirement", f"cannot parse '{line}'"))
            continue
        exact, spec = pep508_pinned(m.group(3))
        if not exact:
            sev = "error" if mode == "app" else "info"
            what = f"specifier '{spec}'" if spec else "no version specifier"
            findings.append(_finding(loc, sev, "unpinned-dependency", f"{m.group(1)}: {what}; pin with == in applications"))
    if count and not hashed and mode == "app":
        findings.append(_finding(path.as_posix(), "info", "no-hashes",
                                 "no --hash entries; consider hash-checking mode for integrity"))
    return findings, count


def _lock_present(directory: Path, names: tuple[str, ...]) -> str | None:
    for name in names:
        if (directory / name).is_file():
            return name
    return None


def check_package_json(path: Path, mode: str) -> tuple[list[dict], int]:
    findings: list[dict] = []
    data = json.loads(path.read_text(encoding="utf-8"))
    lock = _lock_present(path.parent, NPM_LOCKS)
    count = 0
    for section in ("dependencies", "devDependencies", "optionalDependencies"):
        for name, ver in (data.get(section) or {}).items():
            count += 1
            loc = f"{path.as_posix()}:{section}.{name}"
            v = str(ver).strip()
            if v.startswith(("file:", "link:", "workspace:")):
                findings.append(_finding(loc, "info", "local-dependency", f"local reference '{v}'"))
                continue
            if v.startswith("npm:"):
                v = v.rsplit("@", 1)[-1]
            if any(v.startswith(p) for p in ("git", "http", "github:")) or "/" in v:
                if not COMMIT.search(v):
                    findings.append(_finding(loc, "error" if mode == "app" else "warning", "unpinned-vcs",
                                             f"'{v}' without a full commit hash"))
                continue
            if SEMVER_EXACT.match(v):
                continue
            if mode == "library":
                findings.append(_finding(loc, "info", "range-specifier", f"range '{v}' (normal for libraries)"))
            elif lock:
                findings.append(_finding(loc, "warning", "range-specifier", f"range '{v}'; resolved by {lock}, "
                                         "but exact pins make upgrades explicit"))
            else:
                findings.append(_finding(loc, "error", "unpinned-dependency", f"range '{v}' with no lockfile"))
    if count and not lock:
        findings.append(_finding(path.as_posix(), "error" if mode == "app" else "warning", "missing-lockfile",
                                 f"no lockfile next to package.json (expected one of {', '.join(NPM_LOCKS[:4])})"))
    return findings, count


def _pinned_requirements_lock(directory: Path) -> str | None:
    for req in sorted(directory.glob("requirements*.txt")):
        f, n = check_requirements(req, "app")
        if n and not any(x["rule"] in {"unpinned-dependency", "unpinned-vcs"} for x in f):
            return req.name
    return None


def check_pyproject(path: Path, mode: str) -> tuple[list[dict], int]:
    findings: list[dict] = []
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    deps: list[tuple[str, str]] = []
    project = data.get("project", {})
    deps += [("project.dependencies", d) for d in project.get("dependencies", [])]
    for grp, items in (project.get("optional-dependencies") or {}).items():
        deps += [(f"project.optional-dependencies.{grp}", d) for d in items]
    poetry = data.get("tool", {}).get("poetry", {})
    groups = {"tool.poetry.dependencies": poetry.get("dependencies", {})}
    for g, body in (poetry.get("group") or {}).items():
        groups[f"tool.poetry.group.{g}.dependencies"] = body.get("dependencies", {})
    for sect, body in groups.items():
        for name, ver in body.items():
            if name.lower() == "python":
                continue
            v = ver if isinstance(ver, str) else (ver.get("version", "") if isinstance(ver, dict) else "")
            deps.append((sect, f"{name}=={v}" if SEMVER_EXACT.match(v or "") else f"{name} {v}".strip()))
    lock = _lock_present(path.parent, PY_LOCKS) or _pinned_requirements_lock(path.parent)
    for sect, d in deps:
        m = PEP508.match(d)
        if not m:
            findings.append(_finding(f"{path.as_posix()}:{sect}", "error", "unparseable-requirement", f"cannot parse '{d}'"))
            continue
        exact, spec = pep508_pinned(m.group(3).replace("^", "~=").replace("*", ""))
        loc = f"{path.as_posix()}:{sect}.{m.group(1)}"
        if exact:
            continue
        if not spec:
            findings.append(_finding(loc, "warning" if mode == "app" else "info", "no-version-constraint",
                                     f"{m.group(1)} has no version constraint"))
        elif mode == "app" and not lock:
            findings.append(_finding(loc, "warning", "range-specifier", f"{m.group(1)} '{spec}' with no lockfile"))
        else:
            findings.append(_finding(loc, "info", "range-with-lockfile" if lock else "range-specifier",
                                     f"{m.group(1)} '{spec}'" + (f" resolved by {lock}" if lock else "")))
    if deps and not lock:
        findings.append(_finding(path.as_posix(), "error" if mode == "app" else "warning", "missing-lockfile",
                                 f"no lockfile ({', '.join(PY_LOCKS[:3])} or fully pinned requirements.txt)"))
    return findings, len(deps)


def find_manifests(paths: list[Path]) -> list[Path]:
    out: list[Path] = []
    for p in paths:
        if p.is_file():
            out.append(p)
            continue
        if not p.is_dir():
            raise OSError(f"{p} does not exist")
        for q in sorted(p.rglob("*")):
            if q.is_file() and not set(q.parts) & SKIP and (
                    q.name in ("package.json", "pyproject.toml") or re.fullmatch(r"requirements.*\.txt", q.name)):
                out.append(q)
    return out


def check(paths: list[Path], mode: str = "app") -> dict:
    findings: list[dict] = []
    manifests = find_manifests(paths)
    total = 0
    for m in manifests:
        try:
            if m.name == "package.json":
                f, n = check_package_json(m, mode)
            elif m.name == "pyproject.toml":
                f, n = check_pyproject(m, mode)
            else:
                f, n = check_requirements(m, mode)
        except (json.JSONDecodeError, tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
            f, n = [_finding(m.as_posix(), "error", "unreadable-manifest", str(exc))], 0
        findings += f
        total += n
    if not manifests:
        findings.append(_finding("-", "warning", "no-manifests", "no requirements*.txt, package.json or pyproject.toml found"))
    sev = Counter(x["severity"] for x in findings)
    summary = {"mode": mode, "manifests": [m.as_posix() for m in manifests], "dependencies": total,
               "errors": sev.get("error", 0), "warnings": sev.get("warning", 0), "info": sev.get("info", 0)}
    return {"findings": findings, "summary": summary}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Check dependency pinning and lockfiles.")
    ap.add_argument("paths", type=Path, nargs="+")
    ap.add_argument("--mode", choices=["app", "library"], default="app")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        result = check(args.paths, args.mode)
    except OSError as exc:
        print(f"cannot read: {exc}", file=sys.stderr)
        return 2
    s = result["summary"]
    failed = s["errors"] > 0
    result["passed"] = not failed
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for f in result["findings"]:
            print(f"{f['severity'].upper():8} {f['id']:<60} {f['rule']:<22} {f['message']}")
        print(f"\n{'FAIL' if failed else 'PASS'}: {s['dependencies']} dependencies in {len(s['manifests'])} manifest(s); "
              f"{s['errors']} errors, {s['warnings']} warnings")
        print("Scope: specifier hygiene only; not vulnerability, licence or supply-chain integrity scanning.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
