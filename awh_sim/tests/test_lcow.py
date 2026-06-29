"""Unit tests for the economics module (runnable now — no heavy deps)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "economics"))
from lcow import crf  # noqa: E402


def test_crf_known_value():
    # i=0.08, n=15 -> CRF ~= 0.11683 (project_inputs.yaml economics)
    assert abs(crf(0.08, 15) - 0.11683) < 1e-4


def test_crf_zero_interest_limit():
    # As i -> 0, CRF -> 1/n
    assert abs(crf(1e-9, 10) - 0.1) < 1e-3
