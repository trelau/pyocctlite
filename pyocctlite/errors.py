"""
Domain errors raised by pyocctlite.
"""

from __future__ import annotations

from pyocctlite._occtlite import IBuildFailed as BuildFailed
from pyocctlite._occtlite import IKindMismatch as KindMismatch

__all__ = ["BuildFailed", "KindMismatch"]
