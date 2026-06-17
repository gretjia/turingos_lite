"""Environment config isolation tests."""

from turingos.config import load_worker_config


def test_worker_env_uses_worker_extra_body(monkeypatch):
    monkeypatch.setenv("TURINGOS_WORKER_BASE_URL", "https://api.deepseek.com")
    monkeypatch.setenv("TURINGOS_WORKER_API_KEY", "sk-test123456789012345678901234")
    monkeypatch.setenv("TURINGOS_WORKER_MODEL", "deepseek-v4-flash")
    monkeypatch.setenv(
        "TURINGOS_WORKER_EXTRA_BODY",
        '{"thinking":{"type":"disabled"}}',
    )
    monkeypatch.setenv("TURINGOS_WORKER_MAX_TOKENS", "1024")
    monkeypatch.setenv(
        "TURINGOS_META_EXTRA_BODY",
        '{"thinking":{"type":"enabled"}}',
    )

    cfg = load_worker_config()

    assert cfg["model"] == "deepseek-v4-flash"
    assert cfg["extra_body"] == {"thinking": {"type": "disabled"}}
    assert cfg["max_tokens"] == 1024


def test_worker_env_does_not_inherit_meta_extra_body(monkeypatch):
    monkeypatch.setenv("TURINGOS_WORKER_BASE_URL", "https://api.deepseek.com")
    monkeypatch.setenv("TURINGOS_WORKER_API_KEY", "sk-test123456789012345678901234")
    monkeypatch.setenv("TURINGOS_WORKER_MODEL", "deepseek-v4-flash")
    monkeypatch.setenv(
        "TURINGOS_META_EXTRA_BODY",
        '{"thinking":{"type":"enabled"}}',
    )

    cfg = load_worker_config()

    assert "extra_body" not in cfg
