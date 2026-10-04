"""Test package for SHEAR.

The project was renamed from SEMIROH, and its environment variables moved
from ``SEMIROH_*`` to ``SHEAR_*``. A stale ``SEMIROH_*`` variable would be
ignored silently (a mutation campaign would skip, a replay would run the
default seeds), so it fails here instead.
"""

import os

_STALE = sorted(name for name in os.environ if name.startswith("SEMIROH_"))

if _STALE:
    raise RuntimeError(
        "environment variables were renamed to SHEAR_*: "
        + ", ".join(_STALE)
    )
