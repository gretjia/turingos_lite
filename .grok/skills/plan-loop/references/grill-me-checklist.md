# Grill Me Checklist (PlanLoop Step 1 — grill-with-docs exit)

Socratic intent extraction + domain glossary. **Do not skip.** First user input is always incomplete.

**Full Step 1 spec:** `grill-with-docs.md` (grilling + `CONTEXT.md` + plan ADRs).

## Exit criteria

**Machine exit:** set `grill_with_docs.complete: true` in PlanCapsule only when ALL below are true.

Grill-with-docs completes when ALL are true:
- [ ] Problem statement is one sentence, falsifiable
- [ ] Desired final state is concrete (not "make it better")
- [ ] Explicit out-of-scope list exists
- [ ] Success metrics are measurable
- [ ] User confirmed no hidden constraints (budget, timeline, risk tolerance)
- [ ] Ambiguous terms defined in `CONTEXT.md` (not just in chat)
- [ ] Charter invariants acknowledged (dual tapes, predicate gate, projection TUI, capsules)
- [ ] `open_questions` empty

## Question bank (pick 5–8 per round; one at a time)

**Intent**
- What does "done" look like in one screenshot / one command output?
- Who is the user of this outcome — you, an agent, end users?
- What must **not** change?

**Scope**
- What is explicitly out of scope for this plan?
- Is this greenfield, refactor, or surgical fix?
- One atom or multi-phase? Hard deadline?

**Constraints**
- Charter invariants to preserve? (dual tapes, predicate gate, projection TUI)
- Files/areas forbidden to touch?
- Autonomy tier expectation (human-in-loop vs full auto)?

**Domain**
- Micro vs Macro for this work? Capsule vs Contract vs Receipt?
- Name the scale on every object (see `CONTEXT.md` updates inline)

**Verification**
- What E2E certification proves success?
- What would make you reject the plan even if code "works"?

**Risk**
- What is the highest-risk irreversible action?
- `high_risk: true` for TuringLoop?

## Output (append to PlanCapsule)

```yaml
grill_with_docs:
  round: 1
  complete: true
  context_path: "plans/PL-YYYYMMDD-slug/CONTEXT.md"
  adrs: ["plans/PL-YYYYMMDD-slug/adr/0001-....md"]
  problem_statement: ""
  desired_final_state: ""
  out_of_scope: []
  success_metrics: []
  constraints: []
  open_questions: []   # empty when complete
```

## Re-Grill (on Step 5 rejection)

User objects → capture **specific objections** → re-grill only disputed areas → refresh `CONTEXT.md`/ADRs as needed → return to **Step 2 Research**, not full Step 1 unless §0-level intent changed.