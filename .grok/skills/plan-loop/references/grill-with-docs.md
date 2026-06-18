# Grill-with-docs (PlanLoop Step 1 — mandatory start)

PlanLoop **starts here**. Combines Matt Pocock's `/grilling` + `/domain-modeling` (from `.agents/skills/`), overlaid with TuringOS `grill-me-checklist.md` exit criteria.

**Do not skip.** No research, debate, or Canonical Proposal until `grill_with_docs.complete: true`.

---

## Orchestrator MUST

1. Run a **grilling session** (interview) — one question at a time
2. Run **domain modeling inline** — write glossary + ADRs as terms/decisions crystallize
3. Satisfy **grill-me-checklist.md** machine exit before leaving Step 1
4. Explore codebase when a question is answerable from the repo (Charter, `architecture/`, existing atoms)

Optional external skills (if installed): `/grill-with-docs`, `/grilling`, `/domain-modeling` — same behavior; this file is the canonical PlanLoop spec.

---

## Grilling rules (from `/grilling`)

Interview relentlessly about every aspect of the plan until shared understanding. Walk each branch of the design tree; resolve dependencies between decisions one-by-one. **Provide your recommended answer** with each question.

- **One question at a time.** Wait for user feedback before the next. Multiple questions at once is bewildering.
- If answerable from codebase → explore first, then ask only what remains ambiguous.
- On re-Grill (user rejection): grill **only disputed areas**, not full restart unless §0 changed.

---

## Domain modeling rules (from `/domain-modeling`)

Actively sharpen the **plan's** domain model during the grill. Challenge terms, invent edge-case scenarios, write decisions the moment they crystallize.

### Plan-scoped doc layout (TuringOS default)

Create lazily under the plan folder (set `proposal_path` stem early, e.g. `plans/PL-YYYYMMDD-slug/`):

```
plans/PL-YYYYMMDD-slug/
├── CONTEXT.md          # ubiquitous language for THIS plan only
└── adr/
    ├── 0001-....md
    └── 0002-....md
```

`CONTEXT.md` is **glossary only** — no implementation details, not a spec scratch pad.

On **approval (Step 6)**, promote cross-cutting terms/ADRs to repo `docs/adr/` or `architecture/` only if user agrees.

### During the session

| Action | When |
|--------|------|
| Challenge glossary conflicts | User term conflicts with `CONTEXT.md` |
| Sharpen fuzzy language | "account", "done", "agent" overloaded |
| Stress-test scenarios | Boundaries between Micro/Macro, Facilitator/Worker, etc. |
| Cross-reference code | User claim contradicts repo |
| Update `CONTEXT.md` inline | Term resolved — do not batch |
| Offer ADR | All three true: hard to reverse, surprising without context, real trade-off |

### CONTEXT.md format

```md
# {Plan Title}

{One sentence: what this plan changes and why.}

## Language

**Micro Tape**:
Private agency Git at `~/.local/share/turingos/projects/<id>/micro.git`; Intent/Capsule/Receipt objects.
_Avoid_: micro repo, agent db

**Macro Tape**:
User project `.git`; code/world only.
_Avoid_: main repo (without scale prefix)
```

Rules: opinionated canonical term + `_Avoid_` aliases; 1–2 sentence definitions; **plan-specific** terms only (not generic programming).

### ADR format (`plans/.../adr/NNNN-slug.md`)

```md
# {Short title}

{1–3 sentences: context, decision, why.}
```

Number sequentially. Optional: Status, Considered Options, Consequences — only when they add value.

---

## TuringOS grill exit (from `grill-me-checklist.md`)

Set `grill_with_docs.complete: true` only when ALL:

- [ ] `problem_statement` — one sentence, falsifiable
- [ ] `desired_final_state` — concrete (not "make it better")
- [ ] `out_of_scope` — explicit list
- [ ] `success_metrics` — measurable
- [ ] User confirmed hidden constraints (budget, timeline, risk)
- [ ] Ambiguous terms defined in `CONTEXT.md`
- [ ] Charter invariants acknowledged (dual tapes, predicate gate, projection TUI, capsules)
- [ ] `open_questions` empty

Append to PlanCapsule:

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
  open_questions: []
```

---

## Question bank (pick 5–8 per round; one at a time)

**Intent** — What does "done" look like (one command / one screenshot)? Who consumes the outcome? What must not change?

**Scope** — Out of scope? Greenfield vs surgical? One atom vs multi-phase? Deadline?

**Constraints** — Charter invariants? Forbidden files? Autonomy tier for `/TuringLoop`?

**Domain** — Micro vs Macro for this work? What is a Capsule vs Contract vs Receipt here? Name the scale on every object.

**Verification** — What E2E certification proves success? What would make you reject the plan if code "works"?

**Risk** — Highest-risk irreversible action? `high_risk: true` for execute phase?

---

## Re-Grill (on Step 6 rejection)

User objections → update `user_objections` → re-grill **only** disputed areas → refresh `CONTEXT.md`/ADRs as needed → return to **Step 2 Research**, not full Step 1 unless §0-level intent changed.