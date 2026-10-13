#!/usr/bin/env python3
"""Run every library quality gate in order and summarise. Same commands as CI.

Usage: python3 scripts/run_all_checks.py [--skip-tests]
Exit: 0 all gates pass, 1 any gate fails.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
GATES = [
    ("structure", [PY, "scripts/validate_library.py"]),
    ("router catalogue in sync", [PY, "scripts/build_catalog.py", "--check"]),
    ("unit + fixture tests", [PY, "-m", "unittest", "discover", "-s", "tests", "-t", "."]),
    ("authored demo text: assurance-language screen", [PY, ".claude/skills/independent-review/scripts/claim_check.py",
      *sorted(str(p.relative_to(ROOT)) for d in (ROOT / "examples").iterdir() if d.is_dir()
              for p in (d / "README.md", d / "inputs", d / "review") if p.exists())]),
    ("demo reproduction", [PY, "examples/run_demos.py", "--check"]),
]


def main() -> int:
    skip_tests = "--skip-tests" in sys.argv
    results = []
    for name, cmd in GATES:
        if skip_tests and name.startswith("unit"):
            continue
        if not (ROOT / cmd[1]).exists() and not cmd[1].startswith("-"):
            results.append((name, None))
            continue
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        tail = (p.stdout + p.stderr).strip().splitlines()[-2:]
        results.append((name, p.returncode == 0))
        print(f"[{'PASS' if p.returncode == 0 else 'FAIL'}] {name}: {' | '.join(tail)}")
    for name, ok in results:
        if ok is None:
            print(f"[SKIP] {name}: not present")
    print("\nScope: these gates show structural integrity, reproducible calculations and detection of seeded defects. "
          "They are not evidence of engineering safety, regulatory compliance or professional approval.")
    return 0 if all(ok is not False for _, ok in results) else 1


if __name__ == "__main__":
    sys.exit(main())
