"""completion_contract.py (P5): Macro Completion Contract (charter 3.10, FC-A08, 3.5).
Declared in capsule BEFORE dispatch (P4 compiler). Observer + predicate verify.
Scale named (macro:*) only. Never accepts bare git oid as truth. Min pure funcs.
"""

def validate_macro_completion_contract(contract: str | None) -> bool:
    """Daily gate helper (exercised by predicate _macro_completion_contract_present + observer).
    Must name scale: starts with 'macro:' ."""
    if not contract or not isinstance(contract, str):
        return False
    return contract.strip().startswith("macro:")


def parse_macro_completion_contract(contract: str) -> dict:
    """Min parse for evidence (project/ref/condition)."""
    if not validate_macro_completion_contract(contract):
        return {"valid": False, "raw": contract or ""}
    parts = [p for p in contract.strip().split(":", 4)]
    return {
        "valid": True,
        "raw": contract,
        "scale": parts[0] + ":" + parts[1] if len(parts) > 1 else parts[0],
        "project_id": parts[2] if len(parts) > 2 else "",
        "ref": parts[3] if len(parts) > 3 else "",
        "condition": parts[4] if len(parts) > 4 else "",
    }


def make_completion_contract(project_id: str, ref: str, condition: str = "success on intent (via MacroObservationImported)") -> str:
    """Factory for pre-dispatch declaration (used by capsules/observer tests)."""
    pid = project_id or "demo_app"
    r = ref or "HEAD"
    return f"macro:git:{pid}:{r}:{condition}"
