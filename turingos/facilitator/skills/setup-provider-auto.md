# Skill: setup-provider-auto (Software 3.0)

**Trigger:** User pastes API token + mentions provider (DeepSeek / OpenAI / NVIDIA / …).

**Harness does (user does NOT):**
1. `detect_provider_id()` from token prefix + keywords
2. `apply_provider_config()` → keyring + metadata JSON
3. `test_openai_compatible()` — ping completion
4. On FAIL → `fetch_docs_excerpt(docs_url)` from provider_registry

**Thinking mode:** Read `provider_registry.PROVIDER_PROFILES[pid].models` and
`extra_body_default` / `thinking_toggle` (e.g. NVIDIA `enable_thinking`).

**Worker OAuth vs API:** Use `WORKER_PROFILES` — Codex/Claude = OAuth+CLI;
`api_worker` = keyring API path.

**Industry refs:** OpenCode `/connect` + auth.json; OpenClaw `skills.entries`;
Hermes `~/.hermes/skills/` + env injection.