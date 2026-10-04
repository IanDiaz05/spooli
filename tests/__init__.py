"""Characterisation test suite for Spooli.

Ensures the repository root is importable no matter how the tests are
invoked (unittest discovery, package-qualified runs, or direct execution).
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
