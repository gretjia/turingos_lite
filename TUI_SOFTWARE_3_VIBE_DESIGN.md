# TUI for Human Vibe Coders in TuringOS Lite — Software 3.0 Design
**Branch**: tui-vibe-redesign (isolated worktree at `.turingos/worktrees/tui-vibe-redesign`)

**Implementation spec**: [TURINGOS_LITE_TUI_VIBE_MODULE_SPEC_FOR_GROK_BUILD.md](./TURINGOS_LITE_TUI_VIBE_MODULE_SPEC_FOR_GROK_BUILD.md) (v1.0 build executed 2026-06-17)
**Date**: 2026-06-17
**Author framing**: Deep research + design as if I am Andrej Karpathy (drawing directly from Sequoia Ascent 2026, YC AI Startup School talk on Software 3.0, vibe coding blog, X posts, and the integrated RESEARCH_KARPATKY... synthesis already in the repo). 

This document lives **only in this worktree** for focused discussion, prototyping, and iteration without touching main. The goal is to turn the current "not even Software 1.0 operational" TUI into something at least as fluid and delightful as Grok Build TUI or opencode for a human "vibe coder", while deeply embodying Software 3.0 / Karpathy philosophy and the TuringOS charter invariants. Future-proofed for AGI-era agents that may drive or inhabit the "human" role.

---

## 1. Clarification of Your Vision (Do I Understand?)

**Yes — here's my precise reading, stated back so you can correct:**

You designed the **Facilitator AI** (called "Meta AI" in the code/charter — the configurable OpenAI-compatible control/proposer model) specifically as a *quick-response transcriber*. Ideally a fast, low-latency, locally-inferenced model (small, snappy, via Ollama/vLLM or any compatible endpoint). 

Its sole job in the human loop: take *every* piece of raw human natural language intent ("vibe") and transcribe/compile it into *machine (TuringOS) readable action items* — formal, typed, scale-named Micro events and structures (IntentCaptured, WorkCapsuleBuilt with visible capsule + private contract hints, HumanDecision, MacroActionAuthorization, WorkerDispatchPrepared, etc.).

The human should *never* have to speak "TuringOS dialect" directly or memorize hotkeys/payload schemas for normal flow. The human vibes in English. The Facilitator does the heavy lifting of making it precise, compliant, and useful for the dual-tape system.

The **TUI** is the primary "human operating surface" for this transcription + the rich, calm projection of agency state. It must feel *at least* as operational, discoverable, and delightful for a human as:
- Grok Build TUI (rich mouse-interactive fullscreen, streaming, tool blocks, parallel views, model switching in-UI, ER diagrams, etc.).
- opencode (TUI with switchable agents via Tab (build vs plan/read-only), leader keys, permission prompts, LSP, good terminal UX, usable inside tmux, multi-surface).

Current TUI (4 plain Static panes + 20+ cryptic single-letter hotkeys that dispatch *hardcoded dummy payloads*) is not usable for humans. It doesn't even reach Software 1.0 productivity. "Ugly/fast/calm" was the Phase 9 surgical min — now we stretch the craft while staying true to the spirit.

**Non-negotiables from charter (FC-A10 + product boundary):**
- TUI is **projection only**. It reads via reducer + rtool (Micro Tape + declared Macro anchors). It *never* writes truth directly.
- All changes go through typed Micro events, Micro Predicate Kernel, wtool appends (or daemon), proper authorization for irreversible Macro actions.
- "Ugly, fast, and calm": No chat wall. No IDE clone. No dashboard bloat. No magic "verified". No hidden source of truth. *Only law, capsule, receipt, failure, evidence, and next sovereign action.*
- Every object names its scale (μ:, macro:git:, etc.). Forbidden language in UI/logs.
- The user (human today, higher agents tomorrow) manages *agency*, not model sessions.

**Stretch goals (your words + Karpathy S3.0):**
- Natural language is the *primary* (ideally only for normal humans) way to express intent.
- Facilitator (quick/local) is the dedicated "vibe → formal" layer.
- The TUI experience should feel like "vibe coding your own agency" — exhilarating, low-friction, exponential leverage.
- Deeply Karpathy: context window as the program/RAM, LLM as new computer/OS/interpreter, agents as kernel, external durable memory (our Micro Tape is *perfect* for anterograde amnesia), partial autonomy ("Iron Man suit" not full robot), loops + verifiable success criteria, build for agents (the TUI surface and projections must be first-class consumable by higher orchestrators), "you can outsource thinking but not understanding" (human vibes/curates the important bits; Facilitator handles transcription).
- Reserve expandability for AGI era: the "human" slot is pluggable; transcription, projections, and dispatch paths should work for agent "vibe coders"; rich observable state; the fast transcriber role can be a small local model swarm or specialized "intent compiler" while heavier models/agents do execution work.

If any of the above is off or missing key nuance (e.g. specific metaphors, how "local" the Facilitator must feel, exact balance between live NL transcription vs pure projection panes, voice input later, etc.), correct me explicitly. This is the foundation for everything that follows.

---

## 2. Research Synthesis (Karpathy Lens + 2026 Context)

**Core Karpathy framing (directly from Sequoia Ascent 2026 fireside + YC talk + vibe coding posts + X, cross-referenced with the repo's RESEARCH_KARPATKY... doc):**

- **Software 3.0**: Prompts (natural language / English) *are* programs that program the LLM. The LLM is the new kind of computer. Context window = the program / RAM / state you pack and manipulate. Model weights = the interpreter / CPU / substrate. LLMs are utilities, fabs, OSes, timeshare mainframes. "The hottest new programming language is English."
- **Vibe coding** (coined ~2025, now has Wikipedia page): "Fully give in to the vibes, embrace exponentials, and forget that the code even exists." See stuff, say stuff (declarative), run stuff, Accept All, let it loop. Raises the *floor* — almost anyone can create software by describing what they want. Exhilarating for prototypes/personal tools. Human role shifts to manifestor / orchestrator / curator / verifier.
- **Agentic engineering** (the 2026 evolution he emphasizes): Raises the *ceiling* for professionals. Not blind vibes. Design specs, supervise plans, inspect diffs, write tests, create evaluation loops, manage permissions, isolate work (worktrees!), preserve quality and understanding. "Demo is works.any(), product is works.all()." The scarce skill is no longer typing code or even prompting — it is orchestration, verification, taste, system boundaries, knowing when the model is off the rails, and keeping understanding.
- **LLM psychology / limitations** (critical for TUI design):
  - **Jagged intelligence**: Superhuman in some areas, catastrophically dumb in others (not correlated like human skill). Not smooth.
  - **Anterograde amnesia**: No persistent consolidation beyond the context window. Like the guy in *Memento*. Needs external scratchpads, system-prompt learning, durable memory. (Our Micro Tape + replay + projections + failure memory + broadcast rules are *exactly* the right substrate.)
- **Partial autonomy ("Iron Man suit")**: Not full autonomous robots. Augmentation + some autonomy with human in the loop for understanding/verification. Autonomy sliders. Generation <-> verification loops must be fast and tight. Human outsources thinking but *cannot* outsource understanding.
- **Build for agents**: New category of consumer/manipulator of digital information (besides humans via GUIs and computers via APIs). Agents are "computers... but human-like." Products need agent-native surfaces: Markdown, CLIs, APIs, MCP, structured logs, machine-readable schemas, copy-pasteable instructions, auditable actions, sensors + actuators. "The bottom line is that toolmakers must realize that there is [this] new category..."
- **Command centers**: "tmux grids are awesome, but i feel a need to have a proper 'agent command center' IDE for teams of agents..." The unit of interest becomes the *agent*, not the file. Still programming, but at a higher level.
- **Verifiability explains progress**: LLMs + RL automate what you can *verify* (tests, diffs, benchmarks, predicates, receipts, replay). Traditional software automates what you can *specify*. Loops + success criteria + external memory are the leverage.
- **"You can outsource your thinking, but you can't outsource your understanding."** Human (or higher agent) must retain taste, judgment on what matters, what is suspicious, what tradeoff is acceptable.

**How this maps to TuringOS (already beautifully aligned in the charter + AGENTS.md + research synthesis):**
- Dual independent tapes + Micro Git ChainTape = the durable external memory / scratchpad / agency "program" that survives LLM amnesia. Macro remembers code; Micro remembers agency. Same Git tech.
- Projection-only TUI + reducer/rtool = the "sensors" / observable state / context you can pack for the models without stuffing everything.
- Micro Predicate Kernel + typed events (FC-A01–10) + failure always appends + accepted_head vs tape_tip + capsules + shields + contracts before dispatch = the verifiable loops, gates, and success criteria. Statistical signals are evidence only.
- Work capsules + visible for worker + private micro contract = the "spec" + context minimization.
- External agents (Grok Build, Claude CLI, etc.) as blackboxes with whitebox TuringOS adapters + mandatory receipts = safe use of compound middle blackboxes while retaining sovereignty.
- Meta/Facilitator as the proposer/control model = natural place for the "quick transcriber" role.
- "Ugly/fast/calm" + "user manages agency" + "no chat wall" = calm command center, not polluted session or IDE clone. Substance (law, capsule, receipt, evidence, next sovereign action).

**Current TUI vs target references (Grok Build / opencode level):**
- Current: 4 Static text dumps + hardcoded hotkeys. Zero NL. No facilitator in the loop for transcription. Not discoverable. Not visual. Not "vibe".
- Grok Build TUI: Rich, mouse-interactive, fullscreen; streaming content; rich tool/render blocks (ER diagrams etc.); parallel agent views; in-TUI model switching; good feedback.
- opencode: Excellent terminal TUI; switchable agents (Tab for build vs plan/read-only); leader+key shortcuts; permissioned actions; LSP; works great in tmux; also has web/IDE surfaces. Feels *operational* for humans doing real work.

We can (and must) reach that level of craft/UX while staying radically more principled on sovereignty, memory, and NL-as-first-class-intent.

---

## 3. Proposed TUI Design (Karpathy-Style + Charter-Compliant)

**Guiding principles (as Karpathy would state them):**
- Natural language is the programming interface for the human vibe coder. The Facilitator (fast local model) is the compiler/transpiler from fuzzy English to precise, scale-named, predicate-ready TuringOS action items.
- The TUI is the *agency command center*: rich sensors (beautiful live projections of Micro state + capsules + evidence), actuators (vibe composer → formal dispatch), external durable memory visible (the tape is the point), loops made visible and fast (intent → proposal → vibe confirm → execute → observe/replay/failure memory → broadcast updates).
- Partial autonomy with human (or higher agent) in the verification/understanding loop on the things that matter. Facilitator proposes; human vibes/curates/approves the transcription.
- Build for agents: Everything is structured, observable, replayable, evented. The "human" slot and the transcription surface should be usable by a higher orchestrator in the AGI era. Projections are machine-readable too.
- Calm, fast, substance-over-form ("ugly" in the best sense — no bloat, no fake dashboards). Low cognitive load. Low latency transcription thanks to local Facilitator. Discoverable without memorizing 20 hotkeys.
- External memory + context minimization: Use the existing reducer/rtool as the source of truth for what we show the models. Never pollute the main view with chat walls.
- Loops are first-class: The transcription itself is a mini loop (refine in NL). Failure memory and replay feed better future proposals.

**High-level UX / Information Architecture (Textual-based, full power):**

Use modern Textual (not just Static): Containers (Horizontal/Vertical/Grid), Markdown, Input (for the composer), Button, DataTable or Tree for capsules/state, Log or RichLog for evidence, Screen/Modal for focused views (capsule detail, replay scrubber, Facilitator config/test), Live updates, mouse support, theming (calm dark with subtle semantic colors for states — green for accepted paths, amber for pending human, red for failures, blue for macro anchors).

Suggested layout (resizable/switchable panes, command palette discoverability):

```
+---------------------------------------------------------------------+
| Header: project_id | tape_tip: μ:xxx | accepted: μ:yyy | Facilitator: local-phi3 (snappy) | clock |
+---------------------------------------------------------------------+
| LEFT (Agency State Projection)     | CENTER (Vibe Composer + Proposals)          | RIGHT (Evidence / Replay) |
| - Rich tree or cards of Micro      | Prominent Input: "Type your intent in       | Rich timeline / log of    |
|   state from reducer (tape,        | natural language..."                      | recent μ: nodes + anchors |
|   accepted, status, open           |                                           | (full payload on focus,   |
|   capsules count, etc.)            | On submit (or live/debounced):            | scale names always)       |
| - Visual capsules list (focusable, |   - Call Facilitator (async, streaming    | "REPLAY" mode button that |
|   status colored, scale names)     |     if model supports) with engineered    | rebuilds from tape        |
| - Macro anchors declared           |     prompt (current projection + charter  |                           |
|                                    |     rules + "transcribe to 1+ formal      |                           |
| Click/key to focus a capsule →     |     TuringOS actions. Output structured   |                           |
| opens detail screen.               |     JSON only. Use μ: and macro: names.") |                           |
+------------------------------------+-------------------------------------------+---------------------------+
| BOTTOM / OVERLAY: NEXT SOVEREIGN ACTIONS + Suggestions (Facilitator can also propose "based on current open capsules + last FailureNode...") |
| Hotkey hints (minimal) + Command Palette (Textual-style or custom "/") for power users. "i" still works as shortcut to focus composer. |
+---------------------------------------------------------------------+
```

**The Vibe Composer — the heart of the "transcribe every human intent" vision:**

- Always prominent or one keystroke/command away (e.g. "i" or "/" or Enter in certain contexts focuses it).
- Free-form natural language input. Multi-line support for richer vibes.
- "Transcribe" action (or auto on Enter with confirmation):
  1. Load current projection (sole source).
  2. Call the Facilitator (via existing load_meta_config + openai-compatible client or lightweight httpx). 
     - Use a *fast* model (local preferred: phi-3, llama-3.2-3b, gemma2-2b, etc. via Ollama or vLLM — low latency "quick response AI").
     - Carefully engineered prompt (keep it small for speed + to fit local context):
       ```
       You are the TuringOS Facilitator (quick transcriber).
       Your only job: turn the human's natural language intent into precise, charter-compliant TuringOS machine-readable action items.
       Rules (non-negotiable):
       - Every object MUST name its scale (Micro: μ:<oid>, Macro commit: macro:git:<pid>:<oid>, etc.).
       - TUI is projection only — you only propose; the human confirms and the system dispatches via predicate + wtool.
       - Failures always append. accepted_head only on accepted state events.
       - Output ONLY a JSON array of proposed actions. Each has "event_type" (from the known list) and "payload".
       - For WorkCapsuleBuilt, include "visible_markdown" (what the worker sees) and hints for private contract.
       - Current projection (use this as context, never invent tape state): {json projection + recent evidence summary}
       - Human intent: {nl}
       Known event_types: SystemBootstrapped, IntentCaptured, WorkCapsuleBuilt, ...
       Example output: [{"event_type": "IntentCaptured", "payload": {"task": "..."}}, {"event_type": "WorkCapsuleBuilt", "visible_markdown": "...", ...}]
       ```
  3. Parse/validate the structured proposals (defensive — if bad JSON, show raw + "refine" option).
  4. Render as beautiful preview cards (Markdown-rendered visible capsule, list of events with scale names, "what will happen to tape").
  5. Human vibes:
     - "Approve & Dispatch" → for each proposal, do the real make_event + _dispatch (or the proper path for capsules via compiler if needed). This goes through the existing machinery (predicate, wtool, etc.).
     - "Refine": feed the feedback back to Facilitator in the same session context (multi-turn for this transcription, keeping it scoped — no global chat wall).
     - "Edit structured" (optional power mode): allow light edits to the JSON/payload before approve.
     - "Cancel / new vibe".

This is the direct realization of "facilitate human to transcribe every human intent from natural language only into machine readable action items."

The composer can be conversational *within one intent*: "make the mission more specific: support local script workers with timeout". The fast model keeps a tiny local context for the current transcription only.

Once approved, the formal items land in the Micro Tape (visible in Evidence pane live via refresh), scale names are enforced, projections update.

**Other enhancements to reach Grok Build / opencode operational level (while staying charter-true):**

- **Discoverability**: Add Textual CommandPalette (or simple "/" modal) with fuzzy search for all actions + "vibe: ..." . Hotkeys remain for muscle memory but are no longer the only path. "?" help becomes contextual (shows relevant to current state + composer tips).
- **Rich state projections**: Replace plain Static with Tree (for capsule hierarchy or event history), DataTable (for open capsules with columns: id, status, last event, macro anchors), Markdown for capsule visible text. Color by state/scale. Live auto-refresh on actions (existing refresh_projection + Textual timers or reactive).
- **Capsules as first-class visual objects**: Cards or focused Screen showing visible markdown + status + linked evidence + "suggest dispatch to worker X" (which can prefill the composer).
- **Evidence / Replay**: Upgrade to a scrollable rich log or table. "Replay from here" button that can drive a simulation view. Show full node + payload on selection (with scale names). Support filtering (failures, human decisions, macro anchors).
- **Streaming & feedback**: If the Facilitator call supports streaming (many local + OpenAI compat do), stream the proposal text live into the preview area (feels snappy and "alive", like Grok Build).
- **Facilitator visibility & control**: In header or a small pane: current model (local vs remote), latency hint, "Test local transcriber" button that runs a canned intent. Ties into the existing `turing config --meta` + first-run guidance (make the TUI itself a better place to set/test the quick transcriber).
- **Partial autonomy helpers**: After a dispatch or failure, the Facilitator (or a simple state machine) can offer "suggested next vibe" in the bottom bar, e.g. "Recent FailureNode on capsule wc_foo — want me to propose a recovery intent?"
- **Modes (inspired by opencode Tab / plan vs build, Grok parallel)**: Not full agents yet, but a "Focus mode" (composer + one capsule + minimal chrome) vs "Overview mode" (all panes). Future: a read-only "inspect projection" mode for higher agents.
- **Permissions / confirmations**: For anything that would advance accepted_head or do Macro auth, always explicit human vibe (the preview + approve is that). Failures are cheap to append.
- **Theme & calm**: Keep dark, high contrast, minimal chrome. Use Rich markup for semantic color (μ: in blue, macro: in green, Failure in red). Subtle animations or just fast updates.
- **Keyboard + mouse first class**: Full mouse support for clicking capsules, selecting evidence rows, focusing composer. Keyboard for power (Tab between panes, Enter to approve focused proposal, etc.).
- **Error / jagged handling**: Graceful degradation. If Facilitator call fails or gives bad structure, show the error + "fall back to manual intent" (which can still use a simpler structured form or the old hotkeys). Never let a bad transcription block the human.

**Integration points (reuse, don't reinvent):**
- Existing: `_get_projection`, `_get_rtool`, `refresh_projection`, `_dispatch`, `make_event`, `load_meta_config`/`save...`, all the event types and ACCEPTED_STATE_EVENTS.
- wtool / predicate / capsule compiler / daemon paths remain the *only* way truth is written.
- The Facilitator call is new (add a small helper, e.g. `turingos/facilitator/transcribe.py` or inside tui for now). Keep prompts small, versioned, and auditable (perhaps record a lightweight "FacilitatorTranscriptionProposed" or attach to the resulting event payload as "transcribed_by" meta — without secrets).
- For local speed: the same Meta config already supports any OpenAI-compatible (base_url to http://localhost:11434/v1, model="phi3" or whatever). No code change needed for the config layer; just document and make the TUI surface the "set/test quick transcriber" experience better.

**Future expandability for AGI era (pluggable "human", agent-native):**
- The composer input can accept structured input from higher agents (or the whole transcription surface can be driven by an event/ RPC).
- Projections (the reducer output + rich rendered views) are already machine-readable; expose them more explicitly (e.g. via daemon or a --json view, or MCP-style).
- The Facilitator "transcriber" role is explicitly a separate, fast, local-preferred brain from the execution workers. In AGI future you can have a swarm of small models doing transcription + proposal, with larger ones or external bundles doing the heavy worker execution.
- All actions emit typed events → higher agents can observe, learn from failure memory / broadcast rules, and feed new intents back.
- Replay + external state (the worktree already uses these for Macro) + the design doc itself become context for agents that want to "vibe" improvements to TuringOS.
- The TUI itself can be consumed as a "sensor/actuator" surface by a parent orchestrator (the "human" in the loop becomes the orchestrator's chosen policy for when to require flesh-and-blood vibe vs auto).

**"Ugly/fast/calm" evolved (not violated):**
- Still no chat wall — the NL exchange is scoped, ephemeral for *one* intent transcription, results in formal events that live in the tape.
- Still calm and low-bloat: the visual weight is on the projections, capsules, and evidence — the composer is a tool, not the whole screen.
- Faster in practice for humans because NL + fast local model replaces hunting for the right hotkey + guessing payloads.
- "Ugly" in the Karpathy "substance over form" sense: every pixel serves understanding the agency state or capturing clean intent.

---

## 4. Implementation Sketch & Next Steps (in this worktree)

1. **Stay on `tui-vibe-redesign` branch in this isolated worktree.** All experiments, prototypes, and this doc live here. Merge to main only after review + tests + audit (FC-A10 etc.).

2. **Prototype the Vibe Composer + Facilitator transcription** (start small):
   - Add `async def _transcribe_and_propose(self, nl: str)` in an enhanced TuiApp (or a mixin / separate module `turingos/tui/vibe_composer.py` for cleanliness).
   - Use the existing meta config + a lightweight client (openai lib is already a common dep in this world, or pure httpx + json for minimal).
   - Implement the prompt + JSON parsing + validation (defensive, with scale-name checks).
   - Render proposals as a list of preview widgets (Markdown + approve/refine buttons).
   - On approve: map to real `make_event` + `_dispatch` (or the capsule path). Refresh everything.
   - Wire the existing "i" action (and a new prominent UI element) to focus the composer.

3. **Rich-ify the panes** (incremental, surgical):
   - Replace some Static with Textual Markdown, Tree, DataTable.
   - Add live update hooks.
   - Add a simple command palette or "/" modal.

4. **Facilitator UX niceties**:
   - Header indicator + a "Test transcriber" action that uses a canned intent and shows latency + sample output.
   - Make first-run / config guidance point to using a local fast model for the transcriber role.

5. **Testing & verification (goal-driven)**:
   - Extend `tests/unit/test_tui_replay.py` style with `run_test()` + pilot that types into a composer, mocks the Facilitator response, approves, asserts the correct events were appended with proper scale names and payloads.
   - Manual in the worktree: `TURINGOS_DATA_DIR=... python -m turingos.cli tui` (or the direct app). Set a local Ollama as the Meta env vars. Do real "vibe" sessions: "I want to capture intent to explore adding a script worker. Make a capsule for it with mission about timeout and local execution." Approve. Use replay to see the formal items. Exercise failure paths and see Facilitator suggestions.
   - Audit: the new flows must still pass FC-A10 (projection only), scale naming, predicate gates, etc. No direct writes.

6. **Docs & discussion artifacts** (all in this worktree):
   - This file (evolve it).
   - Example session transcripts (text + screenshots if we capture).
   - Updated TESTING_MANUAL section for the new vibe flow.
   - Any prototype code (e.g. a `vibe_tui_experiment.py` that can be run standalone before merging into app.py).

**Open questions for discussion (please reply with corrections / priorities):**
- How "conversational" should one transcription be? (multi-turn refine with the fast model is powerful but we must keep it scoped.)
- Should the Facilitator also help *propose the next sovereign action* proactively after state changes, or only on explicit human vibe?
- Local model sweet spot for transcription (latency vs quality)? Any preferred prompting tricks or few-shot examples from the charter?
- Do we want a "structured fallback" mode (human can still type JSON-ish if they want) or keep it purely NL + preview?
- Visual style: any strong preferences beyond "calm"? (e.g. specific colors for μ: vs macro: )
- Scope for v1 of this redesign in the worktree: just composer + transcription + richer projection panes? Or also capsule cards, replay enhancements, etc.?
- Integration with existing "hotkey dispatches" — should they prefill the composer with a starter prompt ("approve the top capsule") so everything funnels through the transcription path eventually?

---

This is the starting artifact for our discussion in the separate worktree. I have assumed the role of Karpathy for the synthesis and framing while staying rigorously faithful to the charter invariants (dual tapes, projection-only, predicate gates, scale names, "ugly fast calm", no chat wall, user manages agency).

Next action (when you're ready): tell me what to adjust in the vision clarification or design, and we can either:
- Iterate this doc.
- Start coding a prototype of the Vibe Composer + transcription helper directly in `turingos/tui/` on this branch.
- Add more targeted research (deeper dives on specific Karpathy posts, opencode/Grok Build TUI code patterns if public, local model structured-output reliability, etc.).
- Run a manual "vibe session" simulation in the worktree (even before full wiring, by mocking the Facilitator).

Your move — correct my understanding, set priorities, or say "build the first prototype of the composer in this worktree."

(End of initial design doc. All further work on TUI experiences happens here in the tui-vibe-redesign worktree.)
