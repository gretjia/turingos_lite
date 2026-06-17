# API Key / Secret Management and the Keyring Improvement Decision (2026-06-17)

This captures the conversation triggered by the user's question: "How does program like Open Code save the users' own API? Is there a best practice? Did we follow the best practice for turing"

## Research on "Open Code" and Similar Tools (from web searches)
- **OpenCode** (opencode.ai, the open-source terminal AI coding agent): Config in $HOME/.opencode.json, $XDG_CONFIG_HOME/opencode/.opencode.json, ./.opencode.json. Users put API keys directly in JSON for providers (Claude, GPT, Gemini, etc.). Supports BYOK ("connect any model"). Plaintext JSON storage (common pattern, but criticized).
- **Aider**: Strongly prefers environment variables (OPENAI_API_KEY etc.), .env files (project or user), CLI flags (--openai-api-key), .aider.conf.yml. Special support for OpenAI/Anthropic. "Use environment variables or .env" is the documented recommendation.
- **Continue.dev**: Config in JSON (user/workspace settings). Has dedicated "User Secrets" (encrypted via IDE SecretStorage — OS keychain on macOS/Windows). Explicit "Secure Your Keys" docs warning against hardcoding. Earlier versions had plaintext complaints (GitHub issue #1729).
- Other patterns (Open Interpreter, Claude Code tools, Codex CLI): Env vars primary. Some support .env or per-project config. IDE tools lean on host secure storage.
- General best practices from security discussions, OpenAI guidance, tool maintainers:
  - Environment variables first (standard for CLIs; user-controlled, no app persistence of secrets).
  - .env files (gitignored).
  - For persistence: OS keychain (keyring lib) for secrets; XDG JSON/TOML for non-secrets (0600 perms).
  - Never plaintext keys in JSON that could be synced or world-readable.
  - Warnings, .gitignore for any secret-containing files, support for key rotation/revocation.
  - For BYOK agent tools: app should minimize exposure (load at runtime only, via adapters).
  - Criticisms of common patterns: plaintext JSON in home dir (leaks via backups/sync, readable if perms wrong). "AI coding assistant is leaking secrets" articles call this out.

## Current TuringOS State at Time of Question (from grep on workspace)
- Env vars primary: TURINGOS_META_BASE_URL, TURINGOS_META_API_KEY, TURINGOS_META_MODEL.
- TUI first-run (`tui/app.py`): checks envs, auto-saves *raw key* to plain JSON ~/.local/share/turingos/config/meta_ai.json (if envs present). Shows guidance message.
- Charter reference: "Meta AI as one configurable OpenAI-compatible control model" (the proposer in flows; also called Facilitator in user language).
- No keyring yet; plaintext persist was the shortcut (common but not best practice).
- Config is for the "brain" (Meta AI) that proposes WorkOrders — high sovereignty concern in the dual-tape design.

## The Design Conversation & Karpathy 3.0 Lens
User prompted deep thinking: "I think you need to think about what is the future software 3.0 look like. If you are Karpathy, what would you design this process"

Synthesized Karpathy 3.0 (prompts=programs, English interface, context=RAM, models as utilities, amnesia → external memory, harnesses > models, 4 principles, vibe→agentic engineering, build for agents, partial autonomy + verification loops, typed events, projection, durable Git memory, multi-agent roles, behavioral constraints):

For *this specific process* (storing user's own API for the Meta AI/Facilitator in a sovereign agentic harness):

- User programs at high level: "declare my Meta AI capability" + success criteria ("secure, auditable, revocable, never leaks into my agency memory or worker capsules, easy rotation, works with my personal setup").
- The *harness* (TuringOS) is the 3.0 OS that manages the substrate: secure storage (keychain as "OS password manager"), durable memory (Micro Tape records *declarations* as events like MetaAIConfigured with metadata/hash/"securely_stored" — never the raw secret), feedback loops (verify on load/use; failures as FailureNodes), context min (TUI shows status only, never key; projection via rtool/reducer), behavioral law (AGENTS.md: never log, prefer env for fluidity, keyring for persist, 0600).
- Secrets in the secure OS layer (keyring), not in the agent's "RAM" (context) or "long-term memory" (Micro Tape files). Analogous to how the CPU (model) doesn't hold volatile secrets.
- Env vars as the primary "English program" declaration (fluid, user-controlled, great for vibe coding / CI / overrides — matches "give in to the vibes").
- Persistence (for "set and forget" in a personal harness): metadata in XDG JSON; secret ONLY in keyring. Onboarding as guided loop (TUI surfaces tradeoffs, recommends `turing config --meta` for secure entry via getpass; auto-persist metadata if envs set).
- Multi-agent fit: Meta role consumes the capability via whitebox adapter (key loaded at last moment, passed only to client). Config/Harness role owns the loops. Failure to load → predicate failure in intent flow.
- Sovereignty: User owns the key. Revocation = clear keychain + event. Everything replayable/auditable in Micro without leaking secrets. Future evolution: toward OAuth/scoped/MPC capabilities (harness brokers, user never sees raw key).
- Principles applied: Think Before (surface: plaintext convenience vs keyring security; env fluidity vs persisted UX; exposing secret vs harness managing it). Simplicity First (env primary + small central module). Surgical (only config paths, one CLI command, TUI message). Goal-Driven (criteria = env wins, key never in files/tape/logs/projection/capsules, auditable declarations, works with dual-tape + predicate + projection invariants).
- Aligns with existing TuringOS: dual tapes (Micro owns agency declarations), projection TUI, predicate as law, external blackbox + whitebox boundary, failure loops, scale language.

Tradeoffs surfaced explicitly: convenience of auto-persist from env vs never writing raw key; common practice (OpenCode/Aider JSON) vs stronger (keyring + events).

This directly drove the implementation of the keyring improvement.

## What We Implemented
(See the code changes around 2026-06-17: new turingos/config.py, updates to cli.py (config command + bare turing → TUI), tui/app.py (first-run guidance using load_meta_config, no raw key to JSON), events.py (added MetaAIConfigured/Revoked), pyproject.toml (keyring dep), launcher in ~/.local/bin, README updates, TESTING_MANUAL.md.)

- Env vars remain primary (TURINGOS_META_*).
- Persist: non-secrets to XDG JSON (0600); secret only via keyring.
- CLI: `turing config --meta` (interactive with getpass; set/clear/show; records events).
- TUI: on first mount, shows prominent guidance recommending the CLI for secure set (or envs); uses load_meta_config; auto-persists metadata from env when appropriate (key stays out of file).
- Micro Tape: config changes as typed events (metadata only) for replay/audit/sovereignty.
- Graceful if keyring unavailable (env-only).
- Aligned with 3.0 design above and best practices (env first, keyring for secrets, harness as secure broker).

## Comparison to Best Practice at Decision Time
We moved *from* common-but-weak (plaintext JSON auto-save, like OpenCode) *to* stronger (env primary + keyring + XDG metadata + auditable Micro events), while keeping the ergonomic first-TUI guidance the user asked for. This is better than most tools in the category and directly embodies the Karpathy 3.0 harness principles discussed in the conversation.

This file preserves the "why" and the exact research + thinking that produced the current implementation.