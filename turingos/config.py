"""Configuration management for TuringOS Lite (Software 3.0 harness style).

In the spirit of Karpathy's Software 3.0:
- User "programs" at high level via intent/success criteria and env/CLI.
- The harness (TuringOS) manages details securely with durable memory (Micro Tape for declarations),
  feedback loops (verify on load/use), context minimization (TUI shows status, never secrets),
  and OS-secure storage for capabilities (API keys as "keys to model utilities").
- Secrets never in plaintext files or logs; metadata + audit events in sovereign Micro state.
- Env vars as primary "English program" input for fluidity (CI, vibe, overrides).
- OS keychain for persisted secrets (like modern password managers in the agent OS).
- Non-secrets in XDG JSON.
- First-run/onboarding as guided loop with verification.
- Record config declarations as replayable Micro events (without secrets) for agency memory.

This follows best practices from tools like Aider (env + .env + config), Continue (secure secrets),
while advancing toward 3.0: the harness brokers secure access to model "utilities" without user
ever handling raw strings in code/context.

Usage:
- Primary: set env vars (TURINGOS_META_BASE_URL, TURINGOS_META_API_KEY, TURINGOS_META_MODEL).
- Persist securely: `turing config meta` (uses keyring for key).
- Load: get_meta_config() prefers env > keyring + json metadata.
- In future Meta proposer: load here, pass only at runtime via whitebox adapter (never to capsules/logs).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

try:
    import keyring
except ImportError:
    keyring = None  # graceful: env vars only if keyring not installed

from turingos.core import ids  # for scale if needed in future events
from turingos.micro.wtool import append as wtool_append
from turingos.events import make_event, META_AI_CONFIGURED, META_AI_REVOKED

XDG_DATA_HOME = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
CONFIG_DIR = XDG_DATA_HOME / "turingos" / "config"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

META_CONFIG_FILE = CONFIG_DIR / "meta_ai.json"
FACILITATOR_CONFIG_FILE = CONFIG_DIR / "facilitator_ai.json"
KEYRING_SERVICE = "turingos"
KEYRING_USERNAME = "meta_ai"
KEYRING_FACILITATOR_USERNAME = "facilitator_ai"


def _get_meta_config_path() -> Path:
    return META_CONFIG_FILE


def _apply_facilitator_env_extras(cfg: dict[str, Any]) -> None:
    """NVIDIA Diffusion Gemma and other facilitator knobs."""
    if os.environ.get("TURINGOS_FACILITATOR_TEMPERATURE"):
        cfg["temperature"] = float(os.environ["TURINGOS_FACILITATOR_TEMPERATURE"])
    if os.environ.get("TURINGOS_FACILITATOR_TOP_P"):
        cfg["top_p"] = float(os.environ["TURINGOS_FACILITATOR_TOP_P"])
    if os.environ.get("TURINGOS_FACILITATOR_MAX_TOKENS"):
        cfg["max_tokens"] = int(os.environ["TURINGOS_FACILITATOR_MAX_TOKENS"])
    stream = os.environ.get("TURINGOS_FACILITATOR_STREAM", "").lower()
    if stream in ("1", "true", "yes"):
        cfg["stream"] = True
    if os.environ.get("TURINGOS_FACILITATOR_EXTRA_BODY"):
        try:
            cfg["extra_body"] = json.loads(os.environ["TURINGOS_FACILITATOR_EXTRA_BODY"])
        except Exception:
            pass
    elif "nvidia.com" in (cfg.get("base_url") or ""):
        cfg.setdefault("extra_body", {"chat_template_kwargs": {"enable_thinking": True}})
    base = cfg.get("base_url") or ""
    if "nvidia.com" in base:
        cfg["provider"] = "nvidia"


def load_facilitator_config() -> dict[str, Any]:
    """Facilitator AI (fast MCQ co-pilot). Separate from Meta/Work AI."""
    env_base = os.environ.get("TURINGOS_FACILITATOR_BASE_URL")
    env_key = os.environ.get("TURINGOS_FACILITATOR_API_KEY")
    env_model = os.environ.get("TURINGOS_FACILITATOR_MODEL")

    if env_base or env_key or env_model:
        cfg: dict[str, Any] = {
            "base_url": env_base or "https://integrate.api.nvidia.com/v1",
            "api_key": env_key,
            "model": env_model or "google/diffusiongemma-26b-a4b-it",
            "source": "env",
        }
        _apply_facilitator_env_extras(cfg)
        return cfg

    meta: dict[str, Any] = {
        "base_url": "https://integrate.api.nvidia.com/v1",
        "model": "google/diffusiongemma-26b-a4b-it",
        "source": "persisted",
        "temperature": 1.0,
        "top_p": 0.95,
        "max_tokens": 4096,
    }
    if FACILITATOR_CONFIG_FILE.exists():
        try:
            data = json.loads(FACILITATOR_CONFIG_FILE.read_text())
            meta.update({k: v for k, v in data.items() if k in ("base_url", "model", "temperature", "top_p", "max_tokens")})
        except Exception:
            pass
    if keyring:
        try:
            meta["api_key"] = keyring.get_password(KEYRING_SERVICE, KEYRING_FACILITATOR_USERNAME)
        except Exception:
            meta["api_key"] = None
    else:
        meta["api_key"] = None
    if not meta.get("api_key"):
        fallback = load_meta_config()
        if fallback.get("api_key"):
            meta["api_key"] = fallback["api_key"]
            if meta.get("source") == "persisted" and not FACILITATOR_CONFIG_FILE.exists():
                meta["base_url"] = fallback.get("base_url", meta["base_url"])
    _apply_facilitator_env_extras(meta)
    return meta


def _apply_meta_env_extras(cfg: dict[str, Any]) -> None:
    """Optional provider-specific knobs (NVIDIA Nemotron, etc.) via env."""
    if os.environ.get("TURINGOS_META_TEMPERATURE"):
        cfg["temperature"] = float(os.environ["TURINGOS_META_TEMPERATURE"])
    if os.environ.get("TURINGOS_META_TOP_P"):
        cfg["top_p"] = float(os.environ["TURINGOS_META_TOP_P"])
    if os.environ.get("TURINGOS_META_MAX_TOKENS"):
        cfg["max_tokens"] = int(os.environ["TURINGOS_META_MAX_TOKENS"])
    stream = os.environ.get("TURINGOS_META_STREAM", "").lower()
    if stream in ("1", "true", "yes"):
        cfg["stream"] = True
    if os.environ.get("TURINGOS_META_EXTRA_BODY"):
        try:
            cfg["extra_body"] = json.loads(os.environ["TURINGOS_META_EXTRA_BODY"])
        except Exception:
            pass
    base = cfg.get("base_url") or ""
    if "nvidia.com" in base and "provider" not in cfg:
        cfg["provider"] = "nvidia"


def load_meta_config() -> dict[str, Any]:
    """Load Meta AI (Facilitator/proposer) config.

    Returns dict with base_url, model, and api_key (fetched securely).
    Prefers environment variables (for 3.0 fluidity/overrides/CI).
    Falls back to persisted metadata (JSON) + keyring secret.
    Never returns a key if not available; caller should handle.

    This is the harness "capability broker" load path.
    """
    # Env override (primary, as in current best-practice tools and Karpathy fluidity)
    env_base = os.environ.get("TURINGOS_META_BASE_URL")
    env_key = os.environ.get("TURINGOS_META_API_KEY")
    env_model = os.environ.get("TURINGOS_META_MODEL")

    if env_base or env_key or env_model:
        cfg: dict[str, Any] = {
            "base_url": env_base or "https://api.openai.com/v1",
            "api_key": env_key,
            "model": env_model or "gpt-4o-mini",
            "source": "env",
        }
        _apply_meta_env_extras(cfg)
        return cfg

    # Persisted metadata
    meta: dict[str, Any] = {
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
        "source": "persisted",
    }
    if META_CONFIG_FILE.exists():
        try:
            data = json.loads(META_CONFIG_FILE.read_text())
            meta.update({k: v for k, v in data.items() if k in ("base_url", "model")})
        except Exception:
            pass  # fall back to defaults; errors surfaced as FailureNodes upstream

    # Secret from keyring (never in file) -- best practice for 3.0 harness (secure substrate)
    if keyring:
        try:
            key = keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
            meta["api_key"] = key
        except Exception:
            meta["api_key"] = None
    else:
        meta["api_key"] = None  # keyring unavailable; rely on env only

    return meta


def save_meta_config(base_url: str | None = None, api_key: str | None = None, model: str | None = None) -> None:
    """Persist Meta AI config securely.

    - Non-secrets (base_url, model) -> XDG JSON (0600).
    - Secret (api_key) -> OS keychain only.
    - Records a lightweight declaration event in Micro Tape (sovereign replayable memory, no secret).
    - Surgical: only what is needed; caller (CLI/TUI) decides what to pass.
    """
    # Load existing to merge
    existing = {}
    if META_CONFIG_FILE.exists():
        try:
            existing = json.loads(META_CONFIG_FILE.read_text())
        except Exception:
            pass

    updated = {**existing}
    if base_url is not None:
        updated["base_url"] = base_url
    if model is not None:
        updated["model"] = model

    # Write non-secret metadata (restrictive perms)
    META_CONFIG_FILE.write_text(json.dumps(updated, indent=2))
    try:
        META_CONFIG_FILE.chmod(0o600)
    except Exception:
        pass  # best effort on platforms without chmod

    # Secret to keyring (the secure substrate) -- only if available
    if api_key is not None and keyring:
        keyring.set_password(KEYRING_SERVICE, KEYRING_USERNAME, api_key)
    elif api_key is not None:
        # Fallback note (user should use env); do not write secret to file
        pass

    # Record declaration in Micro state (for 3.0 audit/replay/sovereignty).
    # Never include the secret; only metadata + "securely_stored" flag.
    # This makes config changes first-class agency events (part of Micro Tape).
    try:
        # Use a lightweight project if not in one (for global config declaration).
        # In real use, this would be called in context of a pid.
        # For now, use a sentinel; real flows will scope it.
        pid = "global"  # or derive from context in caller
        event = make_event(
            META_AI_CONFIGURED,
            {
                "base_url": updated.get("base_url"),
                "model": updated.get("model"),
                "key_securely_stored": api_key is not None or bool(keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)),
                "source": "config_command",
            },
        )
        wtool_append(pid, event)
    except Exception:
        # Config save must not fail the user; logging of meta config is failure-handled upstream.
        pass


def clear_meta_secret() -> None:
    """Revoke the stored key (rotation/revocation flow). Records event."""
    if keyring:
        try:
            keyring.delete_password(KEYRING_SERVICE, KEYRING_USERNAME)
        except Exception:
            pass  # idempotent

    try:
        pid = "global"
        event = make_event(META_AI_REVOKED, {"source": "config_command"})
        wtool_append(pid, event)
    except Exception:
        pass


def get_meta_api_key() -> str | None:
    """Convenience: just the secret (env > keyring)."""
    cfg = load_meta_config()
    return cfg.get("api_key")
