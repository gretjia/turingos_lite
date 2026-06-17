# IPQC Scan Checklist (TuringLoop v1.4)

Run at Step 5 (VERIFY/IPQC), at dynamic intervals during implement. Non-blocking unless triggers Mini-Recovery.

**On IPQC tick:** run `TestForge(mode=ipqc, scope=atom)` per `references/test-forge.md`.  
**On any issue:** run `fresh_bp(topic, context)` per `references/best-practice-alignment.md`.

## 1. Consistency
- [ ] Changes trace to TaskCapsule `task_id` / user intent
- [ ] No scope creep outside `allowed_files`
- [ ] Naming matches repo conventions
- [ ] Scale language correct (μ:, macro:git:, macro:pr:) in logs/UI

## 2. Simplicity (Code Simplifier lens)
- [ ] No speculative abstractions
- [ ] Could any changed file be 50% smaller and still pass acceptance?
- [ ] Duplicate paths unified?
- [ ] Comments only where non-obvious

## 3. Test coverage (TestForge lens)
- [ ] Acceptance commands defined before implement
- [ ] TestForge ipqc pass recorded in `test_forge_passes[]`
- [ ] UX changes: human journey matrix updated (no bypass)
- [ ] Kernel vs UX layers both considered
- [ ] Regression: old tests still meaningful (no false positives)

## 4. Regression risk (TuringOS invariants)
- [ ] FC-A10: TUI projection-only (no direct truth writes)
- [ ] Dual tapes not mixed
- [ ] Facilitator proposes; Worker mutates Macro code
- [ ] Failure appends; accepted_head only on accepted events
- [ ] Autonomy gates documented (what auto-approves at tier N)

## IPQC output format
```yaml
ipqc_pass: true|false
issues: []
simplifier_required: true|false
mini_recovery_triggered: true|false
alignment_triggered: true|false
test_forge_triggered: true|false
```