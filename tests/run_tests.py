"""Convenience runner for NMPI automated tests.

Run from the project root:
    python tests/run_tests.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[1]
    sys.exit(pytest.main(["-q", str(project_root / "tests")]))