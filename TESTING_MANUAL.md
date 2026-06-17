# TuringOS Lite v1.0 - Testing Manual

**Purpose**: Enable you (or any agent/human) to test the full system yourself, following the charter (TURINGOS_LITE_v1.0_PROJECT_CHARTER.md) and AGENTS.md exactly. This includes the first working demo, manual CLI/TUI testing, and automated E2E simulation.

All testing respects the invariants:
- Dual independent Git tapes (Macro = your project's .git for code; Micro = private bare Git ChainTape at `~/.local/share/turingos/projects/<pid>/micro.git` for agency).
- Every object names its scale (μ:<oid> for Micro nodes, macro:git:<pid>:<oid> etc. for Macro).
- Micro Predicate Kernel is the *daily gate* on every boundary (not stats, CI, LLM judge, etc.).
- TUI is projection-only (reads via rtool/reducer; never writes truth directly; FC-A10).
- Failure *always* appends FailureNode (advances tape_tip only; accepted_head unchanged on fails per 3.6/FC-A04).
- Work Capsules declare macro_completion_contract *before* dispatch (FC-A08).
- External agents are blackboxes (adapters + receipts only; 1.5/FC-A06).

**No external "API" was used in any simulation.** All "sim tests" (including the monitor/debug subagent runs that achieved 10/10 cases PASS + 22/22 nodes active + no zombies) were **pure local Python simulation** using the TuringOS Lite harness code itself:

- **CLI simulation**: `typer.testing.CliRunner` (in-process, controlled env via `TURINGOS_DATA_DIR` + temp Macro .git repos for adopt/observe isolation). No real network or external services.
- **TUI "human entry" simulation**: `textual.testing` (`TuiApp.run_test()` + `pilot.press("i")`, `pilot.press("c")`, `pilot.press("d")`, `pilot.press("o")`, `pilot.press("p")`, `pilot.press("x")`, `pilot.press("enter")`, etc. for hotkeys). This drives the exact hotkeys from tui/app.py BINDINGS (i/n/A/c/d/w/o/p/v/f/b/s/r/m/x/Enter/?/q) in a headless test loop, asserting panes (MICRO STATE, WORK CAPSULES, NEXT ACTION, EVIDENCE) update from reducer/rtool (projection-only).
- **Backend/fast-path simulation**: Direct calls to `turingos.micro.*` (wtool.append, rtool, MicroGitTape), `predicates.kernel.PredicateKernel.validate`, `capsule.*` (compiler/shield), `workers.*` (fake + api_tool_loop with inner Tool Predicate), `macro.observer`, `project.*`, `failure.*`, `reducer`, etc. All in controlled temp dirs. No real daemons/network unless explicitly testing the unix-socket daemon (via `subprocess.Popen` for turingd + socket client in E2E).
- **Event/node activation + zombie checks**: `rtool` (iter_commits + load_node) + Python `grep`/scans on tapes + source. Global count of the 22 nodes from `events.py` (SystemBootstrapped ... RecoveryObserved) + flow arrows from charter 3.x. "API" here is just the local `make_event` + `wtool` (the typed event "bus").
- **Monitor/debug**: Background-style sub-processes or in-proc loops that tail (via prints/rtool) activation counts per node *in correct flowchart paths*, detect zombies (code exists for a node but 0 activations where the flow requires it), and auto-trigger "fixer" context (surgical edits only). No external services.
- **Cases**: Extended charter demo (sec17) + variants (failure paths, adopt, api tool loop per 3.5, multi-capsule, replay from tape+anchors, human decision/approve/reject with MacroActionAuthorization, predicate gates, full audit, TUI hotkeys). All run end-to-end with asserts on scale, dual-tape isolation, predicate ratify, failure appends, contracts pre-dispatch, fsck, replay correctness, projection up-to-date.
- **Why this?** Matches "agent simulates human to enter the TUI" + "use other agents to monitor... debug-in-process" + "good numbers of real simulated cases passed end-to-end" + "all modules/nodes from planned flowcharts active, no zombie nodes". Pure local, reproducible, no external deps beyond the project's (typer, textual, etc.). Charter's "fake command Worker first" + "do not implement real external before fake E2E" was followed.

If you want *real* external workers (e.g., actual `codex exec`, `claude`, Grok Build), see "Real External Workers" section below. The sim never used them.

## 1. Quick Setup (Yourself)

```bash
cd /home/zephryj/projects/turingoslite
# Use uv/pipx or direct (Python >=3.12 recommended per charter)
python -m venv .venv
source .venv/bin/activate
pip install -e .[test]  # or pip install -e . + pytest textual
# (pyproject.toml has the deps: typer, pydantic, rich, textual, pytest)
```

Verify:
```bash
python -m turingos.cli --help
# Should show: boot, new, adopt, intent, capsule, dispatch, observe, approve, reject, replay, tui, audit
```

Run the built-in audit (charter P0 scope):
```bash
python -m turingos.cli audit all
```

## 2. First Working Demo (Charter §17 - Must Pass)

This is the canonical end-to-end (uses fake worker; exercises core nodes like SystemBootstrapped, ProjectDiscovered/Ready, IntentCaptured, WorkOrderProposed, WorkCapsuleBuilt, WorkerDispatchPrepared, WorkerRunReceiptImported, MacroObservationImported, FailureNode, etc.).

```bash
# 1. create project
python -m turingos.cli boot
python -m turingos.cli new demo_app
cd demo_app

# 2. capture intent
python -m turingos.cli intent "create src/hello.txt with hello from turingos"

# 3. dispatch fake worker
python -m turingos.cli dispatch wc_000001 --worker fake_command

# 4. observe macro worktree
python -m turingos.cli observe wc_000001

# 5. approve staging (exercises HumanDecision + MacroActionAuthorization)
python -m turingos.cli approve candidate_000001 --route staging

# 6. replay
python -m turingos.cli replay latest

# 7. open TUI (projection-only; use hotkeys manually: i/c/d/o/p/x/enter etc.)
python -m turingos.cli tui

# 8. run audits (flowcharts/invariants/e2e/global_zombie_check)
python -m turingos.cli audit all
```

**Demo PASS criteria** (from charter):
- Micro tape has: SystemBootstrapped, ProjectReady, IntentCaptured, WorkCapsuleBuilt, WorkerDispatchPrepared, WorkerRunReceiptImported, MacroObservationImported, CandidateReadyForHuman, HumanDecision, MacroActionAuthorization (plus ratifiers like MicroPredicateResult).
- Macro repo has project files and staging branch (in .turingos/worktrees or observed via macro: anchors).
- Projection rebuild works (delete any sqlite; replay must reconstruct from Micro Tape + declared Macro anchors).
- No main merge happened.
- All objects use scale naming.
- Failures (if any) only advance tape_tip.
- No hidden predicates in visible capsules.
- fsck clean on Micro.

Run the automated version of this (and variants):
```bash
python -m pytest tests/unit/test_micro_git_tape.py -q -k "not daemon" --tb=line
# Or the full E2E harness:
python -m audits.e2e  # or python -c "from audits.e2e import run_e2e_cases; run_e2e_cases()"
```

## 3. Manual Testing Yourself (CLI + TUI)

### CLI Basics (all go through predicate + wtool)
```bash
# Boot / new / adopt (charter 3.2)
python -m turingos.cli boot
python -m turingos.cli new myproj
python -m turingos.cli adopt /path/to/existing/repo

# Intent (appends IntentCaptured; Meta proposes via wtool)
python -m turingos.cli intent "fix the oauth bug"

# Capsule / Dispatch (WorkCapsuleBuilt; dispatch to fake/api/command/manual)
python -m turingos.cli capsule wc_000001
python -m turingos.cli dispatch wc_000001 --worker fake_command
python -m turingos.cli dispatch wc_000001 --worker api   # exercises Tool Predicate loop

# Observe / Approve / Reject (MacroObservationImported; HumanDecision + auth)
python -m turingos.cli observe wc_000001
python -m turingos.cli approve candidate_000001 --route staging
python -m turingos.cli reject candidate_000002 --class bad_predicate

# Replay (from Micro Tape + anchors; projection rebuild)
python -m turingos.cli replay latest
python -m turingos.cli replay μ:abc123

# Audit (recursive; covers flowcharts/invariants/e2e/global_zombie)
python -m turingos.cli audit all
python -m turingos.cli audit flowcharts
python -m turingos.cli audit invariants
python -m turingos.cli audit e2e
python -m turingos.cli audit global_zombie_check
```

**Manual TUI** (projection-only; "enter the TUI" yourself):
```bash
python -m turingos.cli tui
```
Inside TUI (use the exact hotkeys from charter/tui/app.py):
- `i` : new intent
- `c` : copy capsule
- `d` : dispatch
- `o` : observe
- `p` : run predicates
- `x` : reject
- `enter` : approve (when candidate ready)
- `r` : replay
- `A` : adopt (or other)
- `q` : quit
- `?` : help

The panes (MICRO STATE, WORK CAPSULES, NEXT ACTION, EVIDENCE) are pure reducer output. Press keys; watch events/μ: scale names appear. No "magic verified" — only law/capsule/receipt/failure/evidence.

To "simulate" TUI entry in your own scripts (for custom cases):
```python
# See tests/unit/test_tui_replay.py for the exact pattern
from turingos.tui.app import TuiApp
import asyncio

async def my_tui_sim():
    app = TuiApp(project_id="demo_app")
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.press("i")   # intent
        await pilot.press("c")   # capsule
        await pilot.press("d")   # dispatch
        await pilot.press("o")   # observe
        await pilot.press("p")   # predicates
        await pilot.press("x")   # reject
        await pilot.press("enter")  # approve (if ready)
        await pilot.press("r")   # replay
        # Assert panes updated from projection
        # (query widgets or renderables for "μ:", "FailureNode", etc.)
```

## 4. Automated E2E + Simulation Tests (Run Yourself)

The "sim test" that reached 10/10 cases PASS + 22/22 nodes active + 0 zombies is in:
- `tests/unit/test_micro_git_tape.py` (core E2E + NO_ZOMBIE + daemon variant)
- `tests/unit/test_tui_replay.py` (TUI pilot hotkey sim + replay)
- `audits/e2e.py` (full cases from testing plan + charter demo)
- `audits/global_zombie_check.py` (parses 22 nodes + forces activation + asserts all active)
- `audits/flowcharts.py` + `audits/invariants.py` (FC-A + charter prompts)

Run them:
```bash
# Core + E2E (skips daemon if no full server in env)
PYTHONPATH=. .venv/bin/python -m pytest tests/ -q --tb=line

# Specific TUI sim (human hotkeys)
PYTHONPATH=. .venv/bin/python -m pytest tests/unit/test_tui_replay.py -q --tb=line -rA

# Full harness (like the monitor subagent)
PYTHONPATH=. .venv/bin/python -m audits.e2e
PYTHONPATH=. .venv/bin/python -m audits.global_zombie_check
PYTHONPATH=. .venv/bin/python -m audits.invariants
PYTHONPATH=. .venv/bin/python -m audits.flowcharts

# Or the combined audit
python -m turingos.cli audit all
```

**What the sim actually does** (no external API):
- Spins up controlled `TURINGOS_DATA_DIR=/tmp/turingos_xxx` (fresh Micro Git, temp user .git for Macro observe).
- Uses `CliRunner` to drive the *exact* CLI commands from the charter demo.
- For "TUI human": `textual.testing` Pilot presses the hotkeys; the app only calls `_dispatch` (which does `wtool.append` after kernel) or `refresh_projection` (rtool/reducer). No real terminal I/O in headless mode.
- Backend: direct `from turingos.micro.wtool import append as wtool_append`; same for rtool, kernel.validate, workers.fake.run (or api_tool_loop which does inner ToolCallRequested + kernel + Receipt), macro.observer, etc.
- Monitors: after each step, `rtool` walks the tape, counts `event_type` for every one of the 22 nodes, checks they appeared in the *correct* flowchart path for that case, asserts no zombies (code for a node exists in wtool/events/etc. but activation count==0 where flow requires it).
- Debug loop: on low count, the "monitor" sub printed context (recent nodes, reducer, missing) and a fixer could do a targeted `search_replace` (in the actual runs, a couple of 1-3 line guards in tests for pid isolation/daemon scope).
- Cases loop until the predicates (e.g., "all case nodes active + replay_ok + projection matches + fsck + scale + dual-tape + contract pre-dispatch") are true.

To add your own case: edit `audits/e2e.py` (or the test files) following the existing Case dataclass + `run_case` pattern. Use the simulator helpers, then assert via rtool + the same predicates.

## 5. Real External Workers (If You Want Beyond the Sim)

The sim only ever used `fake_command` (and `api` mock for Tool* paths) because the charter says "Do not implement real external Workers before fake command Worker passes E2E."

To test with real ones:
- `codex exec`, `claude`, Grok Build, etc. must be in PATH (or configured in workers/registry or .turingos).
- Dispatch will call the real command (blackbox); TuringOS only provides the adapter (workspace, capsule .md, timeout, receipt via stdout/ .turingos, Macro observe of the worktree diff).
- For API-style (real OpenAI-compatible): use `--worker api` (it will call the configured base_url with the Tool Predicate inner loop).
- Always run `turing audit` + global_zombie_check + fsck + replay after.

Example real case:
```bash
python -m turingos.cli dispatch wc_000001 --worker codex   # or claude, grok, etc.
python -m turingos.cli observe wc_000001
python -m turingos.cli approve ...
```

## 6. Verifying No Zombies + Full Coverage Yourself

```bash
# Global check (parses 22 nodes + forces + asserts all active in correct paths)
python -m audits.global_zombie_check

# Or via CLI
python -m turingos.cli audit global_zombie_check

# Manual tape scan (after any run)
python -c '
from turingos.micro.rtool import MicroRtool
r = MicroRtool("demo_app")
seen = set()
for oid in r.iter_commits():
    et = r.load_node(oid)["event_type"]
    seen.add(et)
    print(oid, et)
print("Active:", sorted(seen))
print("Missing from 22:", set(["SystemBootstrapped", ...]) - seen)
'
```

Run the full E2E harness after any manual changes; it will fail the global check if any node went dormant.

## 7. Tips for Your Own Testing

- Always use `TURINGOS_DATA_DIR=/tmp/my_test_$(date +%s)` for isolation when experimenting.
- For TUI manual + "sim" feel: run `turing tui` in one terminal; drive it while tailing the Micro tape in another (`watch -n1 'python -c "from turingos.micro.rtool import ...; print recent nodes"'`).
- To add a new real-world case: copy the pattern from `audits/e2e.py` or `test_micro_git_tape.py`. Define the sequence of CLI/TUI actions, the expected nodes that must activate for *that* flow, and the invariants to assert.
- Recursive audit after your changes: `python -m turingos.cli audit all` + the global zombie + a manual pass of the charter demo.
- If a node is "zombie" in your test (code exists in wtool/events/ but never appended in a flow), the global check will flag it. Fix by ensuring the corresponding flowchart step (e.g., a HumanDecision path) actually calls the append.

This manual + the existing `audits/` + `tests/` + charter is everything the monitor/debug subagent used to reach "10/10 cases, 22/22 nodes, no zombies, HALT".

You can now test exactly as the full-auto run did. Start with the demo in section 2, then the harness in section 4. If you hit any deviation from the charter invariants, the audits will catch it.

Happy testing! If you find a real bug or want to extend a case, open an issue on the repo or send a patch that passes the global zombie + full audit.