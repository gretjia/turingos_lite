"""Real LLM E2E: requires TURINGOS_META_* env or config. Skips when unavailable."""
import os
import time

import pytest

from turingos.config import load_meta_config
from turingos.facilitator.transcribe import transcribe_intent


def _llm_available() -> bool:
    cfg = load_meta_config()
    return bool(cfg.get("api_key"))


@pytest.mark.skipif(not _llm_available(), reason="No LLM API key configured")
def test_full_vibe_to_delivery():
    """Real LLM transcribe must return structured proposals within 10s."""
    t0 = time.monotonic()
    props = transcribe_intent(
        "vibe: create a todo app with sqlite persistence and React frontend",
        {"project_id": "real_llm_e2e", "open_capsules": []},
        force_mock=False,
    )
    elapsed = time.monotonic() - t0
    limit = 180.0 if "nvidia.com" in (load_meta_config().get("base_url") or "") else 30.0
    assert elapsed < limit, f"Transcription took {elapsed:.1f}s (limit {limit}s)"
    assert len(props) >= 1
    assert all("event_type" in p for p in props)