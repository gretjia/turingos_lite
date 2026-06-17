"""Define all planned events from charter 7.2 (as consts + maker). Used for validation, no zombies for P1 subset."""

# Full list per task / charter 7.2
ALL_EVENT_TYPES = [
    "SystemBootstrapped",
    "ProjectDiscovered",
    "ProjectReady",
    "IntentCaptured",
    "WorkOrderProposed",
    "WorkCapsuleBuilt",
    "WorkerDispatchPrepared",
    "WorkerRunStarted",
    "WorkerRunReceiptImported",
    "ToolCallRequested",
    "ToolCallDenied",
    "ToolCallReceipt",
    "MacroObservationImported",
    "MicroPredicateResult",
    "FailureNode",
    "CandidateReadyForHuman",
    "HumanDecision",
    "MacroActionAuthorization",
    "OutsideGovernanceObserved",
    "BroadcastRuleUpdated",
    "ShieldRuleUpdated",
    "RecoveryObserved",
    "MetaAIConfigured",
    "MetaAIRevoked",
]

# Named for direct use / clarity (strings are canonical)
SYSTEM_BOOTSTRAPPED = "SystemBootstrapped"
PROJECT_DISCOVERED = "ProjectDiscovered"
PROJECT_READY = "ProjectReady"
INTENT_CAPTURED = "IntentCaptured"
WORK_ORDER_PROPOSED = "WorkOrderProposed"
WORK_CAPSULE_BUILT = "WorkCapsuleBuilt"
WORKER_DISPATCH_PREPARED = "WorkerDispatchPrepared"
WORKER_RUN_STARTED = "WorkerRunStarted"
WORKER_RUN_RECEIPT_IMPORTED = "WorkerRunReceiptImported"
TOOL_CALL_REQUESTED = "ToolCallRequested"
TOOL_CALL_DENIED = "ToolCallDenied"
TOOL_CALL_RECEIPT = "ToolCallReceipt"
MACRO_OBSERVATION_IMPORTED = "MacroObservationImported"
MICRO_PREDICATE_RESULT = "MicroPredicateResult"
FAILURE_NODE = "FailureNode"
CANDIDATE_READY_FOR_HUMAN = "CandidateReadyForHuman"
HUMAN_DECISION = "HumanDecision"
MACRO_ACTION_AUTHORIZATION = "MacroActionAuthorization"
OUTSIDE_GOVERNANCE_OBSERVED = "OutsideGovernanceObserved"
BROADCAST_RULE_UPDATED = "BroadcastRuleUpdated"
SHIELD_RULE_UPDATED = "ShieldRuleUpdated"
RECOVERY_OBSERVED = "RecoveryObserved"
META_AI_CONFIGURED = "MetaAIConfigured"
META_AI_REVOKED = "MetaAIRevoked"

# State events that advance accepted_head (per 3.6 + A02: state transitions; failures/obs do not)
# Chosen per task: failures + obs never advance accepted; the P1 exercised state ones do.
ACCEPTED_STATE_EVENTS = {
    SYSTEM_BOOTSTRAPPED,
    PROJECT_READY,
    INTENT_CAPTURED,
    WORK_ORDER_PROPOSED,
    WORK_CAPSULE_BUILT,
    WORKER_DISPATCH_PREPARED,
    WORKER_RUN_RECEIPT_IMPORTED,
    CANDIDATE_READY_FOR_HUMAN,
    HUMAN_DECISION,
    MACRO_ACTION_AUTHORIZATION,
    MICRO_PREDICATE_RESULT,
    BROADCAST_RULE_UPDATED,
    SHIELD_RULE_UPDATED,
    RECOVERY_OBSERVED,
    META_AI_CONFIGURED,
    META_AI_REVOKED,
}

def make_event(event_type: str, payload: dict | None = None, **extra) -> dict:
    """Factory: returns event dict for wtool.append. Validates against charter list."""
    if event_type not in ALL_EVENT_TYPES:
        raise ValueError(f"Unknown Micro event_type per charter 7.2: {event_type}")
    ev = {
        "event_type": event_type,
        "payload": payload or {},
    }
    ev.update(extra)
    return ev
