# TestForge (v1.4)

Lightweight verification sub-tool — **not** a loop node. Embedded in VERIFY/IPQC, Mini-Recovery, and REFLECT.

## Invocation

```text
TestForge(mode=standard|ipqc|selfheal, scope=atom|phase|module)
```

Orchestrator calls internally; Verifier subagent executes. No separate Test Loop.

## Modes

| mode | when | commands (TuringOS Lite) |
|------|------|--------------------------|
| `standard` | Step 5 VERIFY (default) | `./run_test.sh`; + `./scripts/run_human_tui_audit.sh` if `human_ux_gate` |
| `ipqc` | Step 5 IPQC tick / mid-implement | Targeted pytest on `allowed_files` + IPQC checklist §3 |
| `selfheal` | Mini-Recovery step 3 | Full acceptance burst + re-run failed journeys; optional `python -m turingos.cli audit all` |

## Scope

| scope | runs |
|-------|------|
| `atom` | TaskCapsule `acceptance_commands` only |
| `phase` | atom + related integration tests |
| `module` | full suite + human matrix (if TUI) |

## `test_mode` (TaskCapsule)

| value | behavior |
|-------|----------|
| `auto_full` (default) | TestForge at VERIFY (standard) + IPQC ticks + selfheal on Mini |
| `ipqc_only` | IPQC-mode tests only at ticks; single standard run at VERIFY |
| `manual_review` | Run tests but Verifier reports for human sign-off before SHIP |

## Output format (always minimal)

```yaml
test_forge:
  mode: standard|ipqc|selfheal
  scope: atom|phase|module
  pass: true|false
  summary: ""              # e.g. "74 unit PASS | 24 journeys PASS"
  delta: ""                # what changed vs last run
  failed_tests: []         # empty on pass
  shipgate_evidence: []    # command + exit code + stdout hash
  rule_candidate: ""       # test best practice for REFLECT
  mini_recovery_triggered: true|false
```

Append to `test_forge_passes[]` in TaskCapsule. **No** full pytest logs in capsule.

## Receipts & Shipgate

Each TestForge run records:
- **Shipgate evidence:** `command`, `exit_code`, `stdout_hash` (sha256 of last 2KB)
- **Micro receipt intent:** log as `test_forge:<mode>:<scope>` in handoff (Worker runs produce real μ: receipts when dispatched)

Failed run → `mini_recovery_triggered: true` → Mini-Recovery (do not SHIP).

## Red-green discipline

1. PLAN defines acceptance **before** implement (predicate first).
2. IMPLEMENT may run partial tests; full TestForge at Step 5.
3. New behavior → add/update test in same atom (red → green).
4. TUI: human journey matrix is UX shipgate — **no bypass** (`HUMAN_SIMULATOR.md`).

## REFLECT extraction (Step 6)

From `test_forge_passes[]`, promote durable rules:
- Flaky patterns → stable selectors / journal asserts
- Bypass anti-patterns → permanent forbid rules
- Missing coverage → next atom acceptance predicate

Merge into `rules_learned` + count in `handoff.test_summary`.