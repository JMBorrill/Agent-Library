"""Repository path helpers."""
from __future__ import annotations

import os
from pathlib import Path


def repo_root() -> Path:
    """Return the library root.

    Resolution order: ``AGENTLIB_ROOT``; the library checkout containing this
    package; ``./.agent-library`` in the current directory (vendored install);
    finally the package parent.
    """
    env = os.environ.get("AGENTLIB_ROOT")
    if env:
        return Path(env).resolve()
    package_parent = Path(__file__).resolve().parents[1]
    if (package_parent / "catalog").is_dir() or (package_parent / "skills").is_dir():
        return package_parent  # running from a checkout of the library
    vendored = Path.cwd() / ".agent-library"
    if (vendored / "catalog").is_dir():
        return vendored  # consuming repository with `agentlib install --components catalog`
    return package_parent


def catalog_dir(root: Path | None = None) -> Path:
    return (root or repo_root()) / "catalog"


def load_catalog(name: str, root: Path | None = None) -> dict:
    """Load ``catalog/<name>.json``."""
    import json

    path = catalog_dir(root) / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))
