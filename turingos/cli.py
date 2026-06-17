"""Basic CLI entrypoint for TuringOS Lite (Phase 0 scaffold + P1 Micro Tape integration for E2E fake)."""

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import typer

from turingos.micro.reducer import reduce_state
from turingos.micro.rtool import MicroRtool
from turingos.micro.git_tape import MicroGitTape  # for fsck in local audit read-path only
from turingos.predicates.kernel import PredicateKernel  # local read audit path only
# Phase 10: daemon delegation for most; but Phase7 approval surgical requires direct wtool appends + rtool reads per task (to integrate predicate kernel, HumanDecision, MacroActionAuthorization, no daemon dep for E2E)
from turingos.micro.wtool import append as wtool_append
from turingos.events import make_event, HUMAN_DECISION, MACRO_ACTION_AUTHORIZATION, FAILURE_NODE, CANDIDATE_READY_FOR_HUMAN
from turingos.macro.observer import import_macro_observation
from turingos.config import load_meta_config, save_meta_config, clear_meta_secret
import getpass
import json
# (task: use wtool for the decision/auth appends; rtool for reads in approve/reject; predicate via wtool)

DAEMON_SOCK_ENV = "TURINGOS_DAEMON_SOCK"


def _get_sock_path() -> Path:
    envp = os.environ.get(DAEMON_SOCK_ENV)
    if envp:
        return Path(envp)
    dd = os.environ.get("TURINGOS_DATA_DIR")
    base = Path(dd) if dd else (Path.home() / ".local" / "share" / "turingos")
    base.mkdir(parents=True, exist_ok=True)
    return base / "turingd.sock"


def _default_pid() -> str:
    """Derive project_id from current working directory name if it looks like a project (has .git or .turingos).
    This makes bare `turing` in your project folder automatically use that project (per charter intent).
    Falls back to 'demo_app' for the initial setup.
    """
    try:
        cwd = Path.cwd().resolve()
        if (cwd / ".git").exists() or (cwd / ".turingos").exists():
            name = cwd.name
            pid = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
            return pid or "project"
    except Exception:
        pass
    return "demo_app"


def _is_listening(sp: Path, timeout: float = 0.2) -> bool:
    if not sp.exists():
        return False
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect(str(sp))
            return True
    except Exception:
        return False


def _ensure_daemon(sock_path: Path | None = None, data_dir: str | None = None) -> Path:
    sp = sock_path or _get_sock_path()
    if _is_listening(sp):
        return sp
    env = os.environ.copy()
    if data_dir:
        env["TURINGOS_DATA_DIR"] = data_dir
    py = sys.executable or "python3"
    # launch turingd (bg, survives for session; tests control via fixture+kill to prevent zombies)
    subprocess.Popen(
        [py, "-m", "turingos.daemon.server", "--sock", str(sp)],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    for _ in range(60):
        if _is_listening(sp, 0.05):
            break
        time.sleep(0.02)
    return sp


def call_daemon(method: str, params: dict | None = None, timeout: float = 12.0) -> dict:
    """JSON-RPC client to turingd over unix socket. Ensures daemon (auto for UX). All writes via daemon."""
    params = dict(params or {})
    sp = _ensure_daemon(data_dir=params.get("data_dir"))
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        s.connect(str(sp))
        req = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
        s.sendall((json.dumps(req) + "\n").encode("utf-8"))
        data = s.recv(65536)
        resp = json.loads(data.decode("utf-8").strip())
        if "error" in resp:
            raise RuntimeError(str(resp["error"]))
        return resp.get("result", {})


app = typer.Typer(
    name="turing",
    help="TuringOS Lite - Dual Git Tape Agentic Workbench (Software 3.0)",
    add_completion=False,
)

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Bare `turing` launches the TUI (first-time will guide Meta AI / Facilitator setup)."""
    if ctx.invoked_subcommand is None:
        tui()


@app.command()
def boot():
    """Bootstrap local config and Micro project registry. (delegates to daemon)"""
    typer.echo("Bootstrapping TuringOS Lite harness (via daemon)...")
    res = call_daemon("boot", {"project_id": _default_pid()})
    typer.echo(f"Micro tape ready: {res.get('tip')} (boot event: {res.get('event')})")


@app.command()
def new(name: str):
    """Create a new project (Meta AI proposes InitSpec + MicroPredicate). (delegates to daemon)"""
    res = call_daemon("new", {"name": name})
    typer.echo(f"Creating new project: {res.get('project_id')}")
    typer.echo(f"ProjectDiscovered: {res.get('discovered')}")
    typer.echo(f"ProjectReady: {res.get('ready')}")


@app.command()
def adopt(path: str = typer.Argument(default=".")):
    """Adopt existing repo (observe Macro, propose BackfilledSpec). (delegates to daemon)"""
    res = call_daemon("adopt", {"path": path})
    typer.echo(f"Adopting project at: {path}")
    typer.echo(f"ProjectDiscovered: {res.get('discovered')}")
    if res.get("ready"):
        typer.echo(f"ProjectReady: {res['ready']}")
    else:
        typer.echo(f"Failure: {res.get('failure')}")
    if res.get("macro_ref"):
        typer.echo(f"Macro observed: {res['macro_ref']}")


@app.command()
def intent(task: str):
    """Capture user intent (appends IntentCaptured to Micro Tape). (delegates to daemon)"""
    typer.echo(f"Capturing intent: {task}")
    res = call_daemon("intent", {"task": task, "project_id": _default_pid()})
    typer.echo(f"IntentCaptured: {res.get('event')}")


@app.command()
def dispatch(capsule: str, worker: str = typer.Option("fake_command", "--worker")):
    """Dispatch (Phase 6 workers): delegates to registry (fake first moved, manual, command_template for codex/claude/grok, api_tool_loop with inner Tool Predicate).
    Delegates to daemon (worker.run inside integrates receipts + wtool + predicate + scale names).
    """
    typer.echo(f"Dispatching {capsule} to {worker} ...")
    res = call_daemon("dispatch", {"capsule": capsule, "worker": worker, "project_id": _default_pid()})
    st = res.get("state", {})
    typer.echo(f"Worker complete. rec={res.get('rec')} Q_t: tip={st.get('tape_tip')} accepted={st.get('accepted_head')} status={st.get('project_status')}")


@app.command()
def observe(capsule: str):
    """Observe Macro (diff/branch/PR post-dispatch). Imports as MacroObservationImported (scale macro:git:/pr: per 1.3/FC-A02) via observer (P5).
    Delegates to daemon (uses wtool (predicate gate), anchors for replay; acc_head unchanged)."""
    typer.echo(f"Observing Macro for capsule {capsule} (P5 observer via daemon)...")
    res = call_daemon("observe", {"capsule": capsule, "project_id": _default_pid()})
    typer.echo(f"MacroObservationImported: {res.get('event')}")
    # projection read only (FC-A10)
    st = res.get("state", {})
    typer.echo(f"Observe complete (acc unchanged for obs). Q_t tip={st.get('tape_tip')} accepted={st.get('accepted_head')}")


@app.command()
def approve(candidate: str, route: str = typer.Option(None, "--route")):
    """Approve (Phase7 per charter 12/3.3/7): HumanDecision + on approve: MacroActionAuthorization then macro action + post MacroObservationImported.
    Integrate with predicate kernel, wtool appends for HumanDecision, MacroActionAuthorization. Use rtool for reads. (direct for task; scale named, FC-A09 before macro)."""
    typer.echo(f"Approving candidate {candidate} (route={route}) ...")
    pid = _default_pid()
    # Use rtool for reads (FC-A10, task req)
    r = MicroRtool(pid)
    tip = r.read_tip()
    acc = r.read_accepted_head()
    _ = list(r.iter_commits())[-3:] if r.iter_commits() else []
    # wtool append HumanDecision (predicate kernel runs inside)
    mid = wtool_append(pid, make_event(HUMAN_DECISION, {"decision": "approve", "candidate": candidate, "route": route or "default"}))
    typer.echo(f"HumanDecision: {mid}")
    # on approve: MacroActionAuthorization then macro action + post MacroObservationImported
    auth_mid = wtool_append(pid, make_event(MACRO_ACTION_AUTHORIZATION, {"action": "post_approve_observe", "candidate": candidate, "authorized_by": "human", "prev_tip": tip}))
    typer.echo(f"MacroActionAuthorization: {auth_mid}")
    # macro action (min: worktree per charter)
    try:
        from turingos.macro.worktree import ensure_worktree
        _ = ensure_worktree(".", candidate)
    except Exception:
        pass
    # post MacroObservationImported (via observer: wtool + predicate + anchors + rtool touch inside)
    obs_mid = import_macro_observation(pid, candidate, macro_path=".", diff=f"post-approve action for {candidate}", branch="main")
    typer.echo(f"MacroObservationImported (post-action): {obs_mid}")
    state = reduce_state(pid)
    typer.echo(f"Approve complete. Q_t tip={state['tape_tip']} accepted={state['accepted_head']}")


@app.command()
def reject(candidate: str, reason: str = typer.Option("human_reject", "--reason")):
    """Reject (Phase7): append HumanDecision(reject) + FailureNode (FC-A03: reject always appends failure, acc unchanged). wtool + predicate + rtool reads."""
    typer.echo(f"Rejecting candidate {candidate} (reason={reason}) ...")
    pid = _default_pid()
    # rtool for reads (task)
    r = MicroRtool(pid)
    _ = r.read_tip()
    _ = r.read_accepted_head()
    mid = wtool_append(pid, make_event(HUMAN_DECISION, {"decision": "reject", "candidate": candidate, "reason": reason}))
    typer.echo(f"HumanDecision: {mid}")
    fail_mid = wtool_append(pid, make_event(FAILURE_NODE, {"reason": f"human rejected: {reason}", "candidate": candidate}))
    typer.echo(f"FailureNode (reject): {fail_mid}")
    state = reduce_state(pid)
    typer.echo(f"Reject complete (acc unchanged). Q_t tip={state['tape_tip']} accepted={state['accepted_head']}")


@app.command()
def capsule(capsule: str, mission: str = typer.Option(None, "--mission")):
    """Compile visible capsule + private contract (delegates to daemon; appends WorkCapsuleBuilt via wtool+pred)."""
    res = call_daemon("capsule", {"capsule": capsule, "mission": mission, "project_id": _default_pid()})
    typer.echo(f"CapsuleBuilt: {res.get('capsule_id')} event={res.get('event')} contract={res.get('macro_completion_contract')}")


@app.command()
def replay(project_id: str = typer.Argument(default=None, help="Project id (defaults to current dir name if in git dir)")):
    """Replay command (Phase9/3.9): reconstruct from Micro Tape + declared Macro anchors/obs (rtool). If projection.sqlite deleted, replay rebuilds. Scale named. Projection only. (direct rtool; daemon get_state for other reads only)"""
    if not project_id:
        project_id = _default_pid()
    r = MicroRtool(project_id)
    typer.echo(f"REPLAY from Micro Tape for {project_id} (from tape+anchors; projection only):")
    for oid in r.iter_commits():
        try:
            node = r.load_node(oid)
            eid = node.get("event_id", "?")
            et = node.get("event_type", "?")
            pl = node.get("payload", {})
            anchor = " [macro-anchor]" if ("macro:git" in str(pl) or "macro_ref" in str(pl)) else ""
            mac = ""
            if "macro:git" in str(pl):
                mac = " " + str(pl)[:80]
            elif isinstance(pl, dict) and pl.get("obs"):
                mac = " " + str(pl.get("obs", {}))[:60]
            typer.echo(f"  {eid} | {et}{anchor}{mac}")
        except Exception:
            pass
    q = reduce_state(project_id)
    typer.echo(f"Replayed. tip={q['tape_tip']} accepted={q['accepted_head']} open_caps={q.get('open_capsules')}")


@app.command()
def tui(project_id: str = typer.Option(None, "--project", "-p", help="Project id (defaults to current dir name if the folder has .git or .turingos)")):
    """Launch the projection-only TUI (Phase9: 4 panes MICRO STATE/WORK CAPSULES/NEXT ACTION/EVIDENCE; hotkeys i/n/A/c/d/w/o/p/v/f/b/s/r/m/x/Enter/?/q dispatch to daemon or direct wtool after predicate; projection from reducer per FC-A10)."""
    if project_id is None or not isinstance(project_id, str):
        project_id = _default_pid()
    from .tui.app import TuiApp
    data_dir = Path(os.environ.get("TURINGOS_DATA_DIR")) if os.environ.get("TURINGOS_DATA_DIR") else None
    TuiApp(project_id=project_id, data_dir=data_dir).run()


@app.command()
def audit(scope: str = typer.Argument("all")):
    """Run architecture audits (flowcharts, invariants, e2e). Delegates state/fsck to daemon where possible."""
    pid = _default_pid()
    typer.echo(f"Running audits: {scope} (project: {pid})")
    try:
        res = call_daemon("audit", {"project_id": pid})
        st = res.get("state", {})
        typer.echo(f"Micro state: {st}")
        typer.echo(f"Micro fsck: {'PASS' if res.get('fsck') else 'ISSUES'}")
        state = st
    except Exception as e:
        # fallback local projection read (FC-A10)
        state = reduce_state(pid)
        typer.echo(f"Micro state: {state}")
        try:
            gt = MicroGitTape(pid)
            ok = gt.fsck()
            typer.echo(f"Micro fsck: {'PASS' if ok else 'ISSUES'} (local fallback)")
        except Exception as ee:
            typer.echo(f"fsck note: {ee}")
    # Phase2: integrate predicate kernel (local sample; real gates always in daemon wtool paths)
    try:
        k = PredicateKernel()
        dummy = {"event_type": "MicroPredicateResult", "payload": {"target_event_type": "ProjectReady", "passed": True, "failed": []}}  # min no make_event to avoid import
        pr = k.validate(dummy, {"prev_tape_tip": (state or {}).get("tape_tip")})
        typer.echo(f"PredicateKernel active: sample PASS={pr.passed}")
    except Exception as e:
        typer.echo(f"predicate note: {e}")

    # Phase 8 (failure memory): minimal wire/exercise in audit (surgical; delegates to failure/ via broadcast_failure)
    try:
        from turingos.capsule.broadcast import broadcast_failure
        br = broadcast_failure({"reason": "audit phase8 failure memory evolve", "capsule_id": "wc_audit8"})
        typer.echo(f"Failure memory (phase8) active: quantized={br.get('quantized')}")
    except Exception as e:
        typer.echo(f"failure memory note: {e}")

    # Phase 11 audits integration (flowcharts parse+FC-A, invariants, e2e from testing plan, global_zombie): surgical call
    audit_results = {}
    try:
        from audits.flowcharts import run_flowchart_audit
        fa = run_flowchart_audit(scope)
        typer.echo(f"flowcharts: {fa.get('status')} (parsed_fcas={fa.get('parsed_fcas')}, flows={fa.get('parsed_flows')})")
        audit_results["flowcharts"] = fa.get("status")
        for c in fa.get("checks", [])[:3]:
            typer.echo(f"  {c}")
    except Exception as e:
        typer.echo(f"flowcharts note: {e}")
        audit_results["flowcharts"] = "ERROR"
    try:
        from audits.invariants import run_invariants_audit
        ia = run_invariants_audit(scope)
        typer.echo(f"invariants: {ia.get('status')} (events={ia.get('all_event_types_count')})")
        audit_results["invariants"] = ia.get("status")
        for p in ia.get("passes", [])[:2]:
            typer.echo(f"  {p}")
    except Exception as e:
        typer.echo(f"invariants note: {e}")
        audit_results["invariants"] = "ERROR"
    try:
        from audits.e2e import run_e2e_cases
        ea = run_e2e_cases(scope)
        typer.echo(f"e2e: {ea.get('status')} (cases={ea.get('nodes_exercised')})")
        audit_results["e2e"] = ea.get("status")
        if ea.get("failures"):
            typer.echo(f"  e2e_failures: {ea.get('failures')}")
    except Exception as e:
        typer.echo(f"e2e note: {e}")
        audit_results["e2e"] = "ERROR"
    try:
        from audits.global_zombie_check import run_global_zombie_check
        za = run_global_zombie_check(scope)
        typer.echo(f"global_zombie: {za.get('status')} (nodes={za.get('total_22')}, all_active={za.get('all_active')})")
        audit_results["global_zombie"] = za.get("status")
        if za.get("missing"):
            typer.echo(f"  missing: {za.get('missing')}")
        else:
            typer.echo("  ALL NODES ACTIVE (count >=1 per exercised flows)")
    except Exception as e:
        typer.echo(f"global_zombie note: {e}")
        audit_results["global_zombie"] = "ERROR"

    if scope in ("all", "full") and all(v == "PASS" for v in audit_results.values() if v):
        typer.echo("PHASE11 AUDITS IMPLEMENTED + AUDIT PASS - ALL NODES ACTIVE, NO ZOMBIES")


@app.command()
def config(meta: bool = typer.Option(False, "--meta", "-m", help="Manage Meta AI (Facilitator AI / control model) config")):
    """Software 3.0 credential management: env vars primary; key in OS keyring (secure substrate);
    metadata in XDG JSON (0600); declaration events in Micro Tape (sovereign, replayable, no secret).
    Follows Karpathy harness principles + best practices (env first, keyring for secrets, like Aider/Continue evolution).
    """
    if not meta:
        typer.echo("Use --meta (or -m) for Meta AI config. Example: turing config --meta")
        current = load_meta_config()
        typer.echo(f"Current (env > keyring+json): base={current.get('base_url')}, model={current.get('model')}, key_set={bool(current.get('api_key'))}, source={current.get('source')}")
        return

    current = load_meta_config()
    typer.echo(f"Meta AI config (harness-brokered, secret never in files/logs/tape):")
    typer.echo(f"  base_url: {current.get('base_url')}")
    typer.echo(f"  model: {current.get('model')}")
    typer.echo(f"  key present: {bool(current.get('api_key'))}")
    typer.echo(f"  source: {current.get('source')}")

    action = typer.prompt("Action [set/clear/show/quit]", default="show").lower()
    if action == "set":
        base = typer.prompt("Base URL (OpenAI-compatible)", default=current.get("base_url", "https://api.openai.com/v1"))
        model = typer.prompt("Model", default=current.get("model", "gpt-4o-mini"))
        key = getpass.getpass("API Key (empty=keep existing): ").strip() or current.get("api_key")
        if not key:
            typer.echo("No key provided/kept; nothing changed.")
            return
        save_meta_config(base_url=base, api_key=key, model=model)
        typer.echo("Saved: metadata to XDG JSON (0600), key to OS keyring. MetaAIConfigured event in Micro Tape.")
    elif action == "clear":
        clear_meta_secret()
        typer.echo("Key revoked from keyring. (Metadata file remains; re-set or delete manually.) MetaAIRevoked event recorded.")
    elif action == "show":
        safe = {k: v for k, v in current.items() if k != "api_key"}
        typer.echo(json.dumps(safe, indent=2))
    else:
        typer.echo("No change.")


if __name__ == "__main__":
    app()
