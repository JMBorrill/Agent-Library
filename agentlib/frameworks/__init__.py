"""Deterministic framework tools.

Each module covers one source framework and may define ``register(subparsers)``
to contribute a CLI sub-command. Modules must only read catalogs from
``catalog/`` and must not call a model.
"""
