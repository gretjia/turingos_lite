# Adversarial Debate Roles (PlanLoop Step 4)

Multi-perspective collision before canonical summary. Use subagents or explicit persona switches.

## Roles (minimum 3)

| Role | Mandate | Must produce |
|------|---------|--------------|
| **Advocate** | Best case for proposed approach | Recommended architecture + why |
| **Skeptic** | Find blind spots, failure modes, scope creep | Top 5 risks + kill criteria |
| **Minimalist** | Karpathy simplicity pass | What to cut; 50-line alternative |
| **Verifier** (optional) | Eval-first | Shipgate + acceptance per atom draft |

## Debate rules

1. Advocate proposes **one** primary path (not a menu of equals).
2. Skeptic must cite **concrete** failure scenarios (not generic "might break").
3. Minimalist must name files/LOC budget if applicable.
4. Debate stops when Advocate + Skeptic agree on **residual risks** list (may be non-empty).
5. No implementation code in this step — plan only.

## Output (append to PlanCapsule)

```yaml
adversarial_debate:
  advocate_summary: ""
  skeptic_risks: []
  minimalist_cuts: []
  residual_risks: []      # accepted, tracked in §0 or atoms
  consensus_approach: ""    # one paragraph
```

## Anti-patterns (forbidden)

- Merging Research + Debate into one shallow pass
- Skipping Skeptic ("we already thought of everything")
- Multiple equally-weighted options without a default recommendation