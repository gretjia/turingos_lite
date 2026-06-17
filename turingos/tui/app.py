"""turingos/tui/app.py: Textual projection-only TUI (FC-A10).
Panes: MICRO STATE / WORK CAPSULES / NEXT ACTION / EVIDENCE.
All reads via reducer + rtool (Micro Tape + declared Macro anchors/obs).
Hotkeys (i/n/A/c/d/w/o/p/v/f/b/s/r/m/x/Enter/?/q) either view-update or _dispatch via wtool (predicate enforced first, never direct write).
Replay key/cmd rebuilds chronological view from tape.
Surgical min for Phase 9. Matches existing style (scale μ:, no magic, reducer as projection).
"""
from pathlib import Path
import os

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static

from turingos.micro.reducer import reduce_state
from turingos.micro.rtool import MicroRtool
from turingos.micro.wtool import append as wtool_append
from turingos.events import make_event
from turingos.config import load_meta_config, save_meta_config


class TuiApp(App):
    """Projection TUI. Ugly/fast/calm. Reads only. Dispatches to pred+wtool."""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("?", "help", "Help"),
        ("r", "replay", "Replay"),
        ("i", "intent", "Intent"),
        ("n", "next", "Next"),
        ("A", "approve", "Approve"),
        ("c", "capsule", "Capsule"),
        ("d", "dispatch", "Dispatch"),
        ("w", "worker", "Worker"),
        ("o", "observe", "Observe"),
        ("p", "predicate", "Predicate"),
        ("v", "view", "View"),
        ("f", "fail", "Fail"),
        ("b", "broadcast", "Broadcast"),
        ("s", "shield", "Shield"),
        ("m", "macro", "Macro"),
        ("x", "cancel", "Cancel"),
        ("enter", "enter_action", "Enter/Act"),
    ]

    def __init__(self, project_id: str = "demo_app", data_dir: Path | None = None, **kwargs):
        super().__init__(**kwargs)
        self.project_id = project_id
        self.data_dir = data_dir
        self.last_action = "init"

    def _get_projection(self) -> dict:
        """Sole source for all panes: reducer projection (never truth)."""
        return reduce_state(self.project_id, data_dir=self.data_dir)

    def _get_rtool(self) -> MicroRtool:
        return MicroRtool(self.project_id, data_dir=self.data_dir)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("MICRO STATE", id="title-micro")
        self.micro = Static("", id="micro-state")
        yield self.micro
        yield Static("WORK CAPSULES", id="title-caps")
        self.caps = Static("", id="work-capsules")
        yield self.caps
        yield Static("NEXT ACTION", id="title-next")
        self.nexta = Static("", id="next-action")
        yield self.nexta
        yield Static("EVIDENCE", id="title-evid")
        self.evid = Static("", id="evidence")
        yield self.evid
        yield Footer()

    def on_mount(self) -> None:
        self._check_first_time_meta_setup()
        self.refresh_projection()

    def _check_first_time_meta_setup(self) -> None:
        """Software 3.0 first-run guidance (Karpathy harness style).
        Meta AI = the configurable OpenAI-compatible control/proposer (Facilitator) model from charter.
        Env vars primary (fluidity, overrides, CI). Persisted secrets ONLY in OS keyring (secure substrate).
        Non-secrets in XDG JSON. Declaration recorded as Micro event (sovereign replayable memory, no secret).
        TUI projection shows status only; never secrets. Use `turing config --meta` for secure interactive set.
        """
        cfg = load_meta_config()
        if not cfg.get("api_key"):
            self.last_action = (
                "FIRST SETUP REQUIRED: Configure Meta AI (the Facilitator AI / proposer from charter).\n"
                "This is your OpenAI-compatible control model (proposes WorkOrders in flows).\n"
                "RECOMMENDED (secure): run `turing config --meta` (uses keyring, never writes key to files).\n"
                "ALTERNATIVE (env, primary for 3.0): \n"
                "  export TURINGOS_META_BASE_URL=https://api.openai.com/v1\n"
                "  export TURINGOS_META_API_KEY=sk-...\n"
                "  export TURINGOS_META_MODEL=gpt-4o\n"
                "Restart `turing` after. Keyring + metadata will be used; env overrides. Press ? for help.\n"
                "Harnesses broker access securely (whitebox adapter at runtime only)."
            )
            # If envs present, persist metadata (key stays in keyring/env; surgical save)
            base = os.environ.get("TURINGOS_META_BASE_URL")
            key = os.environ.get("TURINGOS_META_API_KEY")
            model = os.environ.get("TURINGOS_META_MODEL")
            if base or model:
                save_meta_config(base_url=base, api_key=key, model=model)
                self.last_action = f"Meta AI metadata persisted from env (key via keyring/env). Model: {model or 'default'}"

    def refresh_projection(self) -> None:
        q = self._get_projection()
        r = self._get_rtool()
        self.micro.update(
            f"tape_tip: {q['tape_tip']}\n"
            f"accepted_head: {q['accepted_head']}\n"
            f"status: {q['project_status']}\n"
            f"project: {q['project_id']}"
        )
        caps = q.get("open_capsules", [])
        self.caps.update("open: " + (", ".join(caps) if caps else "[]"))
        self.nexta.update(f"last: {self.last_action}\nSuggested: d/A/r/Enter or ?")
        ev_lines = []
        for oid in list(r.iter_commits())[-6:]:
            try:
                n = r.load_node(oid)
                ev_lines.append(f"{n.get('event_id','')}:{n.get('event_type','')}")
            except Exception:
                pass
        self.evid.update("\n".join(ev_lines) if ev_lines else "no evidence")

    def _dispatch(self, event_type: str, payload: dict | None = None) -> None:
        """Dispatch: use wtool (enforces Micro Predicate Kernel first). TUI never writes truth directly."""
        ev = make_event(event_type, payload or {})
        mid = wtool_append(self.project_id, ev, data_dir=self.data_dir)
        self.last_action = f"{event_type}->{mid}"
        self.refresh_projection()

    def action_quit(self) -> None:
        self.exit()

    def action_help(self) -> None:
        self.last_action = "help: i/n/A/c/d/w/o/p/v/f/b/s/r/m/x/Enter/?/q (dispatch via pred+wtool; r=replay from tape)"
        self.refresh_projection()

    def action_replay(self) -> None:
        """Replay: project from tape (rtool iter + declared anchors in MacroObservationImported)."""
        r = self._get_rtool()
        nodes = []
        for oid in r.iter_commits():
            try:
                n = r.load_node(oid)
                pl = n.get("payload", {})
                anchor = ""
                if "macro_ref" in str(pl) or "macro:git" in str(pl):
                    anchor = " [anchor]"
                nodes.append(f"{n.get('event_id','?')} | {n.get('event_type','?')}{anchor}")
            except Exception:
                pass
        self.evid.update("REPLAY (from Micro Tape + anchors):\n" + ("\n".join(nodes[-12:]) if nodes else "empty"))
        self.last_action = "replay"
        self.refresh_projection()

    def action_intent(self) -> None:
        self._dispatch("IntentCaptured", {"task": "from-tui-i"})

    def action_next(self) -> None:
        self.last_action = "next-view"
        self.refresh_projection()

    def action_approve(self) -> None:
        self._dispatch("HumanDecision", {"decision": "approve", "from": "tui-A"})

    def action_capsule(self) -> None:
        self.last_action = "capsule-view"
        self.refresh_projection()

    def action_dispatch(self) -> None:
        self._dispatch("WorkerDispatchPrepared", {"capsule_id": "from-tui-d"})

    def action_worker(self) -> None:
        self.last_action = "worker-view"
        self.refresh_projection()

    def action_observe(self) -> None:
        self._dispatch("MacroObservationImported", {"capsule_id": "from-tui-o", "obs": {"macro_ref": "macro:git:tui:from-tui-o"}})

    def action_predicate(self) -> None:
        self.last_action = "predicate-view"
        self.refresh_projection()

    def action_view(self) -> None:
        self.refresh_projection()

    def action_fail(self) -> None:
        self._dispatch("FailureNode", {"reason": "tui-f"})

    def action_broadcast(self) -> None:
        self._dispatch("BroadcastRuleUpdated", {"rule": "from-tui-b"})

    def action_shield(self) -> None:
        self._dispatch("ShieldRuleUpdated", {"from": "tui-s"})

    def action_macro(self) -> None:
        self.last_action = "macro-view (anchors declared)"
        self.refresh_projection()

    def action_cancel(self) -> None:
        self.last_action = "cancel/x"
        self.refresh_projection()

    def action_enter_action(self) -> None:
        q = self._get_projection()
        caps = q.get("open_capsules", [])
        if caps:
            self._dispatch("WorkerDispatchPrepared", {"capsule_id": caps[0]})
        else:
            self.action_replay()
