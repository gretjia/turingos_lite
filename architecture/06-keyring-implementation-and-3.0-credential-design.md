# Keyring Implementation and 3.0 Credential Design (2026-06-17)

This captures the final major design conversation before implementation: the keyring improvement for Meta AI secrets, preceded by the explicit Software 3.0 / Karpathy design exercise.

## Trigger
User: "Yes, I'd like you to implement the keyring based improvement. And before you do, I think you need to think about what is the future software 3.0 look like. If you are Karpathy, what would you design this process"

## Karpathy 3.0 Design for the Process (full synthesis from the sequential-thinking call)
(See the detailed output of the sequential-thinking tool in the session for the complete reasoning. Key points summarized here for the archive:)

In a true Software 3.0 world the user programs the *agentic harness* at high level with intent + success criteria. The harness (TuringOS) is the personal AI OS that:
- Manages low-level details (including secure access to model utilities) via OS primitives (keychain as the "password manager" substrate).
- Uses durable external memory (Micro Tape) for sovereign declarations/config events (metadata + hashes only — raw secrets never enter the agent's memory or context).
- Provides feedback loops (verification on load/use; failures as first-class events).
- Enforces context minimization and behavioral constraints (TUI/CLI never sees or logs the key; AGENTS.md law: "use keyring, prefer env for fluidity, record the declaration as a Micro event").
- Treats the key as a *capability* brokered at the whitebox boundary (loaded at last moment for runtime use only).
- Makes the whole thing auditable/replayable/revocable via the Micro Tape (MetaAIConfigured/Revoked events).

Env vars as the primary "English program" declaration (fluid, user-controlled, 3.0 vibe). Persistence (when desired) uses keyring for secrets + XDG for metadata. Onboarding is a guided verification loop. This is "harnesses matter", "build for agents", "durable memory", and the 4 principles applied to secret handling.

## Comparison to Existing Tools (research at decision time)
- OpenCode: plaintext in .opencode.json (user + project level).
- Aider: env vars + .env + .aider.conf.yml (strongly prefers env).
- Continue.dev: earlier plaintext JSON complaints; evolved toward IDE SecretStorage (keychain-backed).
- General consensus: env vars best for CLIs; keyring for persisted secrets; never raw keys in plain files that can be synced or world-readable. 0600 perms, warnings, .gitignore.

## What Was Implemented (surgical, after the 3.0 thinking)
- New `turingos/config.py`: central loader/saver. Env vars win (primary). Metadata (base_url/model) to XDG JSON (0600). Secret *only* via keyring. `save_meta_config` records MetaAIConfigured (metadata only) in Micro Tape. `clear` records MetaAIRevoked. Graceful if keyring missing.
- Added META_AI_CONFIGURED / META_AI_REVOKED to events.py (ALL + ACCEPTED_STATE).
- CLI: `turing config --meta` (interactive with getpass; set/clear/show; never prints key; calls save + events).
- TUI: `_check_first_time_meta_setup` refactored to use `load_meta_config`. Prominent guidance on first mount recommends the secure CLI path while supporting envs. Message explains the 3.0 harness view.
- Global `turing` (from earlier) + bare turing → TUI still works; first TUI now surfaces the improved guidance.
- Docs updated (README, TESTING_MANUAL.md) to describe the new flow.
- pyproject: keyring dep.

This is the direct result of the "think like Karpathy first" step the user requested. The implementation is the concrete artifact of that 3.0 design conversation.

(Full raw thinking available in the sequential-thinking tool output from the session; the research on OpenCode/Aider/Continue is in the web_search results from the same day.)