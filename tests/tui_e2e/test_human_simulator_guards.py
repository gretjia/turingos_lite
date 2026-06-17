"""Ensure legacy e2e tests are classified; human matrix is the UX gate."""
from __future__ import annotations

import pathlib


def test_pilot_journeys_documents_bypass_risk():
    """Legacy pilot_journeys uses post_message fallback — not the UX gate."""
    text = (pathlib.Path(__file__).parent / "test_pilot_journeys.py").read_text()
    assert "post_message" in text or "_pilot_click_choice" in text
    assert "Unlike unit tests" in text


def test_run_test_includes_human_matrix():
    script = (pathlib.Path(__file__).parent.parent.parent / "run_test.sh").read_text()
    assert "test_human_journey_matrix.py" in script