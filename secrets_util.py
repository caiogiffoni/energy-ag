"""Credentials: Robocorp Vault secret ``secrets`` first, then environment."""

from __future__ import annotations

import os
from typing import Any

VAULT_SECRET_NAME = "secrets"

_vault: Any | None = None
_vault_attempted = False


def _load_vault_secret() -> Any | None:
    global _vault, _vault_attempted
    if _vault_attempted:
        return _vault
    _vault_attempted = True
    try:
        from robocorp import vault

        _vault = vault.get_secret(VAULT_SECRET_NAME)
    except Exception:
        _vault = None
    return _vault


def secret_or_env(key: str, default: str | None = None) -> str | None:
    """Prefer key from Vault secret ``secrets``; otherwise ``os.environ`` (and optional default)."""
    vault_obj = _load_vault_secret()
    if vault_obj is not None:
        if hasattr(vault_obj, "get"):
            raw = vault_obj.get(key)
        else:
            try:
                raw = vault_obj[key]
            except KeyError:
                raw = None
        if raw is not None and str(raw).strip() != "":
            return str(raw)
    return os.environ.get(key, default)
