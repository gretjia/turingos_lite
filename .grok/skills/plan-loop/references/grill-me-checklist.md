# Grill Me Checklist (PlanLoop Step 2)

Socratic intent extraction. **Do not skip.** First user input is always incomplete.

## Exit criteria

**Machine exit:** set `grill_me.complete: true` in PlanCapsule only when ALL below are true.

Grill Me completes when ALL are true:
- [ ] Problem statement is one sentence, falsifiable
- [ ] Desired final state is concrete (not "make it better")
- [ ] Explicit out-of-scope list exists
- [ ] Success metrics are measurable
- [ ] User confirmed no hidden constraints (budget, timeline, risk tolerance)
- [ ] Ambiguous terms defined (e.g. "fast", "simple", "done")

## Question bank (pick 5–8 per round)

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

**Verification**
- What E2E certification proves success?
- What would make you reject the plan even if code "works"?

**Risk**
- What is the highest-risk irreversible action?
- `high_risk: true` for TuringLoop?

## Output (append to PlanCapsule)

```yaml
grill_me:
  round: 1
  complete: true
  problem_statement: ""
  desired_final_state: ""
  out_of_scope: []
  success_metrics: []
  constraints: []
  open_questions: []   # empty when complete
```

## Re-Grill (on rejection)

User objects → capture **specific objections** → re-Grill only disputed areas → return to Research (Step 3), not full restart from scratch unless §0 changed.