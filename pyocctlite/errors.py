"""
Domain errors raised by pyocctlite.
"""

from __future__ import annotations

from pyocctlite._occtlite import BuildFailed, KindMismatch

__all__ = ["BuildFailed", "KindMismatch"]

# tracebacks show the public module, not the C++ layer
BuildFailed.__module__ = __name__
KindMismatch.__module__ = __name__
