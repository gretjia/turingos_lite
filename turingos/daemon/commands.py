"""Daemon command handlers (Phase 10). All mutations via wtool (enforces predicate kernel + scale + dual-tape + FC-A).
CLI delegates here. Supports: boot, new, adopt, intent, capsule, dispatch, observe, approve, reject, replay, audit, get_state.
"""
import os
from pathlib import Path
from typing import Any

from ..micro.git_tape import MicroGitTape
from ..micro.wtool import append as wtool_append
from ..micro.reducer import reduce_state
from ..micro.rtool import MicroRtool
from ..events import make_event, SYSTEM_BOOTSTRAPPED, INTENT_CAPTURED, HUMAN_DECISION, MACRO_ACTION_AUTHORIZATION, FAILURE_NODE
from ..workers.registry import get_worker
from ..macro.observer import import_macro_observation
from ..project.new import create_new_project
from ..project.adopt import adopt_project
from ..capsule.compiler import compile_work_capsule


DEFAULT_PID = "demo_app"


def _pid(params: dict) -> str:
    return params.get("project_id") or params.get("pid") or DEFAULT_PID


def _data_dir(params: dict) -> Path | None:
    dd = params.get("data_dir")
    if dd:
        return Path(dd)
    env = os.environ.get("TURINGOS_DATA_DIR")
    return Path(env) if env else None


def cmd_boot(params: dict) -> dict:
    pid = _pid(params)
    dd = _data_dir(params)
    gt = MicroGitTape(pid, data_dir=dd)
    tip = gt.init()
    mid = wtool_append(pid, make_event(SYSTEM_BOOTSTRAPPED, {"boot": "daemon", "project_id": pid}), data_dir=dd, source="turingos:daemon", issuer="daemon")
    return {"tip": tip, "event": mid, "project_id": pid}


def cmd_new(params: dict) -> dict:
    name = params.get("name") or params.get("project_id") or "unnamed"
    dd = _data_dir(params)
    return create_new_project(name, data_dir=dd)


def cmd_adopt(params: dict) -> dict:
    path = params.get("path", ".")
    dd = _data_dir(params)
    return adopt_project(path, data_dir=dd)


def cmd_intent(params: dict) -> dict:
    pid = _pid(params)
    task = params.get("task", "")
    dd = _data_dir(params)
    mid = wtool_append(pid, make_event(INTENT_CAPTURED, {"task": task}), data_dir=dd, source="turingos:daemon", issuer="user")
    return {"event": mid, "project_id": pid}


def cmd_capsule(params: dict) -> dict:
    pid = _pid(params)
    cid = params.get("capsule") or params.get("capsule_id") or "wc_daemon"
    dd = _data_dir(params)
    cap = compile_work_capsule(
        pid,
        cid,
        mission=params.get("mission"),
        atom=params.get("atom"),
        law=params.get("law"),
        allowed=params.get("allowed"),
        forbidden=params.get("forbidden"),
        known_failures=params.get("known_failures"),
        output_contract=params.get("output_contract"),
        macro_completion_contract=params.get("macro_completion_contract") or f"macro:git:{pid}:HEAD:success on {cid}",
        data_dir=dd,
    )
    # Append via wtool (predicate gate) for visibility in tape (optional for pre-dispatch; dispatch flow also builds)
    ev = make_event("WorkCapsuleBuilt", {"capsule_id": cid, "contract": cap.get("macro_completion_contract"), "capsule_hash": cap.get("capsule_hash")})
    mid = wtool_append(pid, ev, data_dir=dd, source="turingos:daemon:capsule", issuer="compiler")
    cap["event"] = mid
    return cap


def cmd_dispatch(params: dict) -> dict:
    pid = _pid(params)
    capsule = params.get("capsule") or params.get("capsule_id") or "wc_000001"
    worker = params.get("worker", "fake_command")
    dd = _data_dir(params)
    w = get_worker(worker)
    rec = w.run(pid, capsule, worker)
    state = reduce_state(pid, data_dir=dd)
    return {"rec": rec, "state": state, "project_id": pid}


def cmd_observe(params: dict) -> dict:
    pid = _pid(params)
    capsule = params.get("capsule") or params.get("capsule_id") or "wc_000001"
    dd = _data_dir(params)
    mid = import_macro_observation(pid, capsule, macro_path=params.get("macro_path", "."), data_dir=dd)
    state = reduce_state(pid, data_dir=dd)
    return {"event": mid, "state": state, "project_id": pid}


def cmd_approve(params: dict) -> dict:
    pid = _pid(params)
    capsule = params.get("capsule") or params.get("capsule_id") or "wc_000001"
    decision = params.get("decision", "approve")
    dd = _data_dir(params)
    # Human decision + explicit MacroActionAuthorization (FC-A09 for irreversible)
    ev1 = make_event(HUMAN_DECISION, {"capsule_id": capsule, "decision": decision, "actor": "human"})
    mid1 = wtool_append(pid, ev1, data_dir=dd, source="turingos:daemon", issuer="human")
    ev2 = make_event(MACRO_ACTION_AUTHORIZATION, {"capsule_id": capsule, "action": "observe_or_next", "authorized": True})
    mid2 = wtool_append(pid, ev2, data_dir=dd, source="turingos:daemon", issuer="human")
    return {"events": [mid1, mid2], "project_id": pid}


def cmd_reject(params: dict) -> dict:
    pid = _pid(params)
    capsule = params.get("capsule") or params.get("capsule_id") or "wc_000001"
    reason = params.get("reason", "rejected by human")
    dd = _data_dir(params)
    ev = make_event(HUMAN_DECISION, {"capsule_id": capsule, "decision": "reject", "reason": reason})
    mid = wtool_append(pid, ev, data_dir=dd, source="turingos:daemon", issuer="human")
    # also explicit failure append for loop
    fail = make_event(FAILURE_NODE, {"reason": reason, "capsule_id": capsule})
    midf = wtool_append(pid, fail, data_dir=dd, source="turingos:daemon", issuer="human")
    return {"events": [mid, midf], "project_id": pid}


def cmd_replay(params: dict) -> dict:
    pid = _pid(params)
    limit = int(params.get("limit", 50))
    dd = _data_dir(params)
    r = MicroRtool(pid, data_dir=dd)
    events = []
    for oid in r.iter_commits()[-limit:]:
        try:
            node = r.load_node(oid)
            events.append({
                "event_id": node.get("event_id"),
                "event_type": node.get("event_type"),
                "payload": node.get("payload"),
                "source": node.get("source"),
            })
        except Exception:
            pass
    return {"events": events, "tip": r.read_tip(), "accepted_head": r.read_accepted_head(), "project_id": pid}


def cmd_audit(params: dict) -> dict:
    pid = _pid(params)
    dd = _data_dir(params)
    state = reduce_state(pid, data_dir=dd)
    gt = MicroGitTape(pid, data_dir=dd)
    fs = gt.fsck() if gt.git_dir.exists() else False
    return {"state": state, "fsck": fs, "project_id": pid}


def cmd_get_state(params: dict) -> dict:
    pid = _pid(params)
    dd = _data_dir(params)
    return reduce_state(pid, data_dir=dd)


# Dispatch table for server
HANDLERS = {
    "boot": cmd_boot,
    "new": cmd_new,
    "adopt": cmd_adopt,
    "intent": cmd_intent,
    "capsule": cmd_capsule,
    "dispatch": cmd_dispatch,
    "observe": cmd_observe,
    "approve": cmd_approve,
    "reject": cmd_reject,
    "replay": cmd_replay,
    "audit": cmd_audit,
    "get_state": cmd_get_state,
}


def dispatch(method: str, params: dict) -> dict:
    if method not in HANDLERS:
        raise KeyError(f"unknown method: {method}")
    return HANDLERS[method](params)
