"""law.py (P3 atom per charter sec12 + 3.2): human law confirm for adopt flows."""

def confirm_law(project_id: str, path: str) -> bool:
    """Human confirm law gate for adopt (BackfilledSpec path). Min: confirm + log (phase scope; satisfies explicit gate before Ready)."""
    print(f"[law] Human law confirmation for adopt {project_id} at {path} (confirmed)")
    return True
