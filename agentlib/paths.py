"""Repository path helpers."""
from __future__ import annotations

import os
from pathlib import Path


def repo_root() -> Path:
    """Return the library root.

    ``AGENTLIB_ROOT`` overrides discovery (useful when the package is installed
    elsewhere). Otherwise the parent of the package directory is used.
    """
    env = os.environ.get("AGENTLIB_ROOT")
    if env:
        return Path(env).resolve()
    return Path(__file__).resolve().parents[1]


def catalog_dir(root: Path | None = None) -> Path:
    return (root or repo_root()) / "catalog"


def load_catalog(name: str, root: Path | None = None) -> dict:
    """Load ``catalog/<name>.json``."""
    import json

    path = catalog_dir(root) / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))
