"""
Domain errors raised by pyocctlite.

Each error subclasses a built-in exception, so callers may catch either the
specific error or its built-in base.
"""
from __future__ import annotations

from pyocctlite._occtlite import IBuildFailed as BuildFailed
from pyocctlite._occtlite import IKindMismatch as KindMismatch

__all__ = ['BuildFailed', 'KindMismatch']
