"""P4 compiler.py: WorkCapsule compiler (visible + private_contract).

Per exact task + charter P4 / 3.3 / 3.7 / 3.8 / 1.5 / FC-A05/08:
- Builds visible capsule md with: mission/atom/law/allowed/forbidden/known_failures/output_contract + macro_completion_contract
- Private (incl full preds/budget/shield) stored in CAS (private_cas/blobs/<sha>) + private_contracts/<id>.json
- Shield Compiler applied (min context, hide predicates) BEFORE writing visible
- Integrates broadcast/variants for failure-driven evolution
- Returns capsule dict for WorkCapsuleBuilt payload (contract always present; scale named)
- Writes visible to <cwd>/.turingos/capsules/<capsule_id>.md (charter layout)
- Always produces Micro typed events on boundaries (caller appends)
Surgical: pure + writes for worker visible / private store; no direct wtool here (callers do).
"""

import hashlib
import json
from pathlib import Path
from typing import Any

from ..core.hashing import payload_hash
from ..micro.git_tape import get_micro_git_dir
from .shield import apply_shield, compile_shield
from .broadcast import broadcast_failure
from .variants import get_shield_variant


def compile_work_capsule(
    project_id: str,
    capsule_id: str,
    mission: str | None = None,
    atom: str | None = None,
    law: str | None = None,
    allowed: list[str] | None = None,
    forbidden: list[str] | None = None,
    known_failures: list[str] | None = None,
    output_contract: str | None = None,
    macro_completion_contract: str | None = None,
    data_dir: Path | None = None,
    **kw: Any,
) -> dict:
    """Main entry: compile Work Capsule for dispatch.
    - Shield applied to produce visible (min + hidden removed).
    - Private contract (with hidden + shield) -> CAS + private_contracts.
    - Visible .md written (worker visible only).
    - Payload for WorkCapsuleBuilt always declares macro_completion_contract (FC-A08).
    - capsule_hash for visible side (predicate stub).
    Returns: dict(capsule_id, visible, visible_path, private_ref, macro_completion_contract, capsule_hash, shield, ...)
    """
    if not capsule_id or not isinstance(capsule_id, str):
        capsule_id = "wc_unknown"
    if not project_id:
        project_id = "demo_app"

    # Defaults per P4 task + charter examples
    mission = mission or "Execute the captured intent as a sovereign Micro agent under TuringOS control."
    atom = atom or "P4-capsule-atom"
    law = law or "AGENTS.md + charter: Micro Predicate Kernel is the only daily gate. Every object names its scale (μ:/macro:). Failure always appends. Visible capsule never leaks hidden predicates (FC-A05)."
    allowed = allowed or ["src/", "tests/", ".turingos/capsules/", "README*"]
    forbidden = forbidden or [".git/", "~/.ssh/", "private_*/", "micro.git/", ".env*"]
    known_failures = known_failures or []
    output_contract = output_contract or "Exit 0 + receipt json + artifacts listed; no direct Macro writes (use observer)."
    macro_completion_contract = macro_completion_contract or "macro:git:demo_app:HEAD:success on intent task (diff/branch/PR as MacroObservationImported only)"

    # 1. Build raw content
    raw = {
        "capsule_id": capsule_id,
        "mission": mission,
        "atom": atom,
        "law": law,
        "allowed": allowed,
        "forbidden": forbidden,
        "known_failures": known_failures,
        "output_contract": output_contract,
        "macro_completion_contract": macro_completion_contract,
        "project_id": project_id,
    }

    # 2. Shield compile + apply (min context + hide)
    shield = compile_shield(known_failures=known_failures)
    visible_md = apply_shield(raw, shield)

    # 3. Write visible capsule (charter 1.2: .turingos/capsules/<id>.md ; projection + worker visible)
    # Use cwd for macro-side visible (tests run in project root; .turingos/capsules gitignored per README)
    vis_root = Path.cwd() / ".turingos" / "capsules"
    vis_root.mkdir(parents=True, exist_ok=True)
    vis_path = vis_root / f"{capsule_id}.md"
    vis_path.write_text(visible_md, encoding="utf-8")

    # 4. Private contract (hidden full details + shield + budget)
    private_contract = {
        "capsule_id": capsule_id,
        "project_id": project_id,
        "full_raw": raw,  # hidden
        "shield": shield,
        "budget": {"max_steps": 50, "max_tokens": 8000, "tokens_used": 0},
        "hidden_predicates": [
            "private_contract_not_worker_visible",
            "budget_not_exceeded",
            "worker_scope_allowed",
        ],
        "private_only_notes": "Do not leak to worker-visible. PredicateKernel enforces.",
    }
    priv_json = json.dumps(private_contract, sort_keys=True, separators=(",", ":"))
    priv_hash = hashlib.sha256(priv_json.encode("utf-8")).hexdigest()

    # Write to private CAS + private_contracts (charter 1.2 layout under micro parent)
    micro_parent = get_micro_git_dir(project_id, data_dir).parent
    cas_blobs = micro_parent / "private_cas" / "blobs"
    cas_blobs.mkdir(parents=True, exist_ok=True)
    (cas_blobs / priv_hash).write_text(priv_json, encoding="utf-8")

    priv_contracts = micro_parent / "private_contracts"
    priv_contracts.mkdir(parents=True, exist_ok=True)
    (priv_contracts / f"{capsule_id}.private.json").write_text(priv_json, encoding="utf-8")

    private_ref = f"cas:sha256:{priv_hash}"

    # 5. Capsule hash (visible side, for _capsule_hash_matches predicate)
    vis_hash = payload_hash({"visible": visible_md, "id": capsule_id})

    # 6. Return for WorkCapsuleBuilt (contract always present; no hidden keys in top payload)
    result = {
        "capsule_id": capsule_id,
        "visible": visible_md,
        "visible_path": str(vis_path),
        "private_ref": private_ref,
        "macro_completion_contract": macro_completion_contract,
        "capsule_hash": vis_hash,
        "output_contract": output_contract,
        "shield": shield,
        "private_ref_cas": private_ref,
    }
    return result


# Convenience: compile then (optionally) trigger broadcast on a failure for loop (used by callers)
def compile_then_broadcast_on_failure(
    project_id: str,
    capsule_id: str,
    failure: dict,
    **compile_kw,
) -> dict:
    """Helper for loops: build capsule, then on provided failure produce broadcast rules/variant.
    Returns capsule + broadcast dict (events inside). Caller does the appends.
    """
    cap = compile_work_capsule(project_id, capsule_id, **compile_kw)
    br = broadcast_failure(failure, pid=project_id)
    return {"capsule": cap, "broadcast": br}
