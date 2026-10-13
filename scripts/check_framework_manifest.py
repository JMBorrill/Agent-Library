#!/usr/bin/env python3
"""Backward-compatible manifest check from the starter kit.

Delegates to validate_library.py, which — unlike the original — verifies that every skill named in the
NASA 17-process map, crosswalks and packs actually exists, and that mapped test files exist.
Metadata integrity only; not source or domain correctness.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate_library  # noqa: E402

if __name__ == "__main__":
    sys.exit(validate_library.main(sys.argv[1:]))
