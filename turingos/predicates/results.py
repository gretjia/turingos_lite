"""Phase 2: MicroPredicateResult outcome object (in-mem). Used by kernel; distinct from tape event."""

from typing import List, Optional


class MicroPredicateResult:
    """Return type for PredicateKernel.validate(event, context).
    passed=True means all P0 predicates satisfied for the transition.
    failed lists the predicate names that did not hold (for FailureNode + logs).
    """

    def __init__(self, passed: bool, failed: Optional[List[str]] = None, details: Optional[dict] = None):
        self.passed = passed
        self.failed = failed or []
        self.details = details or {}

    def __repr__(self) -> str:
        return f"MicroPredicateResult(passed={self.passed}, failed={self.failed})"
