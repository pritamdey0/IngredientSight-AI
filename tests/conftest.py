"""Shared pytest setup: make the project importable and load the dataset once."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend import data_layer  # noqa: E402  (path set up above)


@pytest.fixture(scope="session", autouse=True)
def dataset():
    """The real reference dataset; tests fail loudly when it is missing."""
    return data_layer.load()
