#!/usr/bin/env python3
"""Backward-compatible entry point from the starter kit; delegates to validate_library.py.

The original version only checked skill names, one source ID per skill and two example requirements.
It is superseded by scripts/validate_library.py (spec-level skill/agent/pack/source/crosswalk checks).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate_library  # noqa: E402

if __name__ == "__main__":
    sys.exit(validate_library.main(sys.argv[1:]))
