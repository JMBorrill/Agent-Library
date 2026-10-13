"""Shared, dependency-free helpers for the library's own maintenance scripts.

Skill scripts never import from here: each skill must work when copied on its own.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = ROOT / ".claude" / "skills"
AGENTS_DIR = ROOT / ".claude" / "agents"
