# BestPractice Alignment Pass (v1.3)

Lightweight, pluggable sub-tool — **not** a loop node. Call at high-leverage points only.

## Invocation

```text
fresh_bp(topic, context)     # smart default: search → summarize → delta → apply decision
force_alignment(topic)       # explicit override (any loop position)
```

**Tools:** `WebSearch` / `WebFetch` → 3-bullet summary → delta vs current approach → apply/skip decision → optional `rule_candidate`.

## Output format (always minimal)

```yaml
alignment_pass:
  topic: ""
  triggered_by: "plan|simplify|ipqc|reflect|mini_recovery|force"
  summary_bullets: ["", "", ""]
  delta_vs_current: ""       # one line
  apply_decision: apply|skip|defer
  rule_candidate: ""         # empty if skip
  sources: []                # URLs only, no full page dump
```

**Context discipline:** Never paste full fetch bodies into TaskCapsule. Summarize to ≤3 bullets.

## Trigger matrix

| Loop point | Default | Karpathy reason |
|------------|---------|-----------------|
| Step 2 PLAN | **mandatory** | Baseline scaffolding — most leverage |
| Step 3 IMPLEMENT | off | Pure execution; avoid distraction |
| Step 4 SIMPLIFY | **mandatory** | Fresh elegance patterns post-complexity |
| Step 5 VERIFY/IPQC | on issue | Quality alignment when scan finds gaps |
| Step 6 REFLECT | **mandatory** | Meta-learning; upgrade `rules_learned` |
| Step 7 SHIP | off | Closure only |
| Step 8 HANDOFF | optional | Replay context if rules changed |
| Mini-Recovery RCA | **mandatory** | Fresh remedies after failure |

## `frontier_mode`

| mode | behavior |
|------|----------|
| `auto` (default) | Mandatory points always run; optional points run when `failure_rate > 0`, `high_risk`, long ETA (>300 steps), or IPQC issue |
| `force` | `fresh_bp` at every mandatory point + any `force_alignment(topic)` calls |
| `off` | Skip all alignment passes (Charter/TuringOS rules still apply) |

## Topic selection

Use `alignment_topics` from TaskCapsule when set; else infer from task:

- Code style → `python_elegance`, `repo_conventions`
- Agent harness → `agentic_loop`, `software_3_0_harness`
- TUI/UX → `textual_tui`, `human_sim_testing`
- API/workers → `llm_tool_loop`, `agent_sandbox`

## Apply decision rules

- **apply** — concrete delta changes plan, simplify target, or fix strategy; record in capsule notes
- **skip** — already aligned or off-topic; do not bloat scope
- **defer** — interesting but out of atom scope; add to `open_risks` or next atom