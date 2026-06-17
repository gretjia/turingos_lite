"""turingos/tui/app.py: Software 3.0 Vibe TUI (FC-A10 projection-only).

Layout: TopBar + Left(Capsules) | Center(Vibe Composer) | Right(Next+Evidence).
All reads via reducer + rtool. Dispatches via wtool (predicate enforced).
Supports headless agent mode and mock/real Facilitator transcription.
"""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Input, Label, ListItem, ListView, Static

from turingos.config import load_facilitator_config, load_meta_config, save_meta_config
from turingos.events import make_event
from turingos.facilitator.facilitate import facilitate_turn, mock_enrich_turn
from turingos.facilitator.project_brief import build_project_brief, format_project_cognition
from turingos.facilitator.schema import append_nav_choices
from turingos.micro.reducer import reduce_state
from turingos.micro.rtool import MicroRtool
from turingos.micro.wtool import append as wtool_append
from turingos.tui.agent_bus import GLOBAL_BUS, AgentBus
from turingos.tui.widgets import (
    CapsulesPane,
    DeliveryBanner,
    EvidencePane,
    NextActionPane,
    TopBar,
    VibeComposerPane,
    VibeInput,
)


class CommandPalette(ModalScreen[str]):
    """Cmd+K fuzzy command palette."""

    BINDINGS = [("escape", "dismiss", "Close")]

    COMMANDS = [
        ("Transcribe vibe", "transcribe"),
        ("Approve proposal", "approve"),
        ("Replay tape", "replay"),
        ("Set autonomy 0%", "auto_0"),
        ("Set autonomy 50%", "auto_50"),
        ("Set autonomy 100%", "auto_100"),
        ("Help", "help"),
        ("Quit", "quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Label("Command Palette (type to filter)")
        yield Input(placeholder="Search commands…", id="palette-filter")
        yield ListView(
            *[ListItem(Label(label), id=cmd_id) for label, cmd_id in self.COMMANDS],
            id="palette-list",
        )

    def on_input_changed(self, event: Input.Changed) -> None:
        filt = event.value.lower()
        lv = self.query_one("#palette-list", ListView)
        for item in lv.children:
            label = item.query_one(Label).renderable
            text = str(label).lower()
            item.display = filt in text or filt == ""

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        cmd_id = event.item.id or ""
        self.dismiss(cmd_id)


class TuiApp(App):
    """Software 3.0 Vibe TUI. Projection-only; dispatch via pred+wtool."""

    CSS = """
    Screen { background: #0d1117; }
    .pane-title { color: #8b949e; padding: 0 1; height: 1; }
    .vibe-title { color: #58a6ff; text-style: bold; }
    #top-bar { height: 3; padding: 0 1; background: #161b22; border-bottom: solid #30363d; }
    #main-grid { height: 1fr; }
    #left-pane { width: 30%; border-right: solid #30363d; padding: 0 1; }
    #center-pane { width: 40%; border-right: solid #30363d; padding: 0 1; }
    #right-col { width: 30%; }
    #next-pane { height: 50%; border-bottom: solid #30363d; padding: 0 1; }
    #evidence-pane { height: 50%; padding: 0 1; }
    #autonomy-row { height: 1; margin: 0 1; }
    #delivery-banner { display: none; height: 5; background: #0d2818; border: solid #238636; margin: 0 1; padding: 1; text-align: center; }
    Button.success { background: #238636; }
    Button.error { background: #da3633; }
    #composer-row { height: auto; min-height: 8; }
    #vibe-input { width: 1fr; height: 7; min-height: 5; border: solid #30363d; }
    #chat-thread { height: 10; max-height: 12; border: solid #30363d; padding: 0 1; margin: 0 0 1 0; }
    #composer-hint { height: 1; margin-bottom: 1; }
    #config-input-panel { height: auto; border: solid #388bfd; padding: 1; margin: 1 0; background: #161b22; }
    #config-input-row { height: auto; min-height: 3; }
    #config-input { width: 1fr; height: 3; min-height: 3; border: solid #58a6ff; }
    #config-input-hint { height: auto; min-height: 1; margin-bottom: 1; }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("?", "help", "Help", priority=True),
        Binding("r", "replay", "Replay", priority=True),
        Binding("i", "intent", "Intent", priority=True),
        Binding("n", "next", "Next", priority=True),
        Binding("A", "approve", "Approve", priority=True),
        Binding("c", "capsule", "Capsule", priority=True),
        Binding("d", "dispatch", "Dispatch", priority=True),
        Binding("w", "worker", "Worker", priority=True),
        Binding("o", "observe", "Observe", priority=True),
        Binding("p", "predicate", "Predicate", priority=True),
        Binding("v", "view", "View", priority=True),
        Binding("f", "fail", "Fail", priority=True),
        Binding("b", "broadcast", "Broadcast", priority=True),
        Binding("s", "shield", "Shield", priority=True),
        Binding("m", "macro", "Macro", priority=True),
        Binding("x", "cancel", "Cancel", priority=True),
        Binding("enter", "enter_action", "Enter/Act", priority=True),
        Binding("ctrl+k", "palette", "Palette", priority=True),
    ]

    def __init__(
        self,
        project_id: str = "demo_app",
        data_dir: Path | None = None,
        *,
        headless: bool = False,
        agent_bus: AgentBus | None = None,
        force_mock_facilitator: bool = False,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.project_id = project_id
        self.data_dir = data_dir
        self.headless = headless
        self.agent_bus = agent_bus or GLOBAL_BUS
        self.force_mock_facilitator = force_mock_facilitator
        self.last_action = "init"
        self.autonomy = 50
        self.current_goal = "Explore Software 3.0 agency"
        self.pending_proposals: list[dict] = []
        self.facilitator_turn: dict = {}
        self.session_turns: list[dict] = []
        self.project_brief: dict = {}
        self.awaiting_freeform = False
        self.awaiting_config_field: str | None = None
        self.config_draft: dict | None = None
        self.turn_history: list[dict] = []
        self.history_index: int = -1
        self.refine_context: str | None = None
        self.loop_progress = 0
        self.delivered = False
        self._agent_task: asyncio.Task | None = None
        self._boot_done = False
        self._facilitator_lock = asyncio.Lock()
        self._last_user_message = ""

    def _get_projection(self) -> dict:
        return reduce_state(self.project_id, data_dir=self.data_dir)

    def _get_rtool(self) -> MicroRtool:
        return MicroRtool(self.project_id, data_dir=self.data_dir)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield TopBar(id="top-bar")
        with Horizontal(id="autonomy-row"):
            yield Label("Autonomy:")
            yield Button("−", id="auto-dec")
            yield Static("50%", id="auto-display")
            yield Button("+", id="auto-inc")
        with Container(id="main-grid"):
            with Horizontal():
                yield CapsulesPane(id="left-pane")
                yield VibeComposerPane(id="center-pane")
                with Container(id="right-col"):
                    yield NextActionPane(id="next-pane")
                    yield EvidencePane(id="evidence-pane")
        yield DeliveryBanner("", id="delivery-banner")
        yield Footer()

    def key_q(self) -> None:
        self.action_quit()

    def key_question_mark(self) -> None:
        self.action_help()

    def key_r(self) -> None:
        self.action_replay()

    def key_i(self) -> None:
        self.action_intent()

    def key_n(self) -> None:
        self.action_next()

    def key_upper_a(self) -> None:
        self.action_approve()

    def key_c(self) -> None:
        self.action_capsule()

    def key_d(self) -> None:
        self.action_dispatch()

    def key_w(self) -> None:
        self.action_worker()

    def key_o(self) -> None:
        self.action_observe()

    def key_p(self) -> None:
        self.action_predicate()

    def key_v(self) -> None:
        self.action_view()

    def key_f(self) -> None:
        self.action_fail()

    def key_b(self) -> None:
        self.action_broadcast()

    def key_s(self) -> None:
        self.action_shield()

    def key_m(self) -> None:
        self.action_macro()

    def key_x(self) -> None:
        self.action_cancel()

    def key_enter(self) -> None:
        self.action_enter_action()

    def on_mount(self) -> None:
        self._check_first_time_meta_setup()
        self.project_brief = build_project_brief(
            self.project_id, data_dir=self.data_dir
        )
        self._sync_model_label()
        self._set_autonomy(self.autonomy)
        self.set_interval(0.5, self._poll_agent_bus)
        self.refresh_projection()
        self._blur_inputs()
        if not self.headless:
            asyncio.create_task(self._facilitator_boot())

    def _blur_inputs(self) -> None:
        """Blur NL inputs so legacy hotkeys (A/r/…) reach App key handlers."""
        for sel in ("#goal-input", "#vibe-input", "#palette-filter"):
            try:
                w = self.query_one(sel)
                if hasattr(w, "blur"):
                    w.blur()
            except Exception:
                pass
        if self.headless:
            self._agent_task = asyncio.create_task(self._headless_agent_loop())

    def _sync_model_label(self) -> None:
        cfg = load_facilitator_config()
        label = cfg.get("model", "mock")
        if not cfg.get("api_key") or self.force_mock_facilitator:
            label = "mock"
        try:
            self.query_one("#top-bar", TopBar).model_label = label
        except Exception:
            pass

    def _check_first_time_meta_setup(self) -> None:
        cfg = load_meta_config()
        if not cfg.get("api_key"):
            self.last_action = (
                "FIRST SETUP: Configure Facilitator via `turing config --meta` or env vars.\n"
                "Mock transcriber active until configured."
            )
            base = os.environ.get("TURINGOS_META_BASE_URL")
            key = os.environ.get("TURINGOS_META_API_KEY")
            model = os.environ.get("TURINGOS_META_MODEL")
            if base or model:
                save_meta_config(base_url=base, api_key=key, model=model)
                self.last_action = f"Meta metadata persisted. Model: {model or 'default'}"
        else:
            self.last_action = "Facilitator ready"

    def refresh_projection(self) -> None:
        q = self._get_projection()
        r = self._get_rtool()
        try:
            self.query_one("#left-pane", CapsulesPane).update_projection(q)
        except Exception:
            pass
        ev_lines = []
        for oid in list(r.iter_commits())[-8:]:
            try:
                n = r.load_node(oid)
                eid = n.get("event_id", "")
                et = n.get("event_type", "")
                ev_lines.append(f"{eid}:{et}")
            except Exception:
                pass
        cognition = format_project_cognition(self.project_brief)
        ev_display = [
            "[bold]项目认知 (Facilitator)[/]",
            cognition,
            "—",
            "[bold]Micro events[/]",
            *ev_lines,
        ]
        try:
            self.query_one("#evidence-pane", EvidencePane).update_evidence(ev_display)
        except Exception:
            pass
        tt = self.facilitator_turn.get("turn_type", "")
        next_text = f"last: {self.last_action}\nmode: {tt or '—'}"
        if self.pending_proposals:
            next_text += f"\n[pending {len(self.pending_proposals)} proposals — Approve]"
        elif tt == "clarify":
            nav = ""
            if self.history_index > 0:
                nav += " ←退回"
            if self.history_index < len(self.turn_history) - 1:
                nav += " 下一题→"
            if self.config_draft:
                next_text += f"\n[配置向导 {self.config_draft.get('step', '?')}{nav}]"
            else:
                next_text += f"\n[pick choice; submit→Approve; other→输入{nav}]"
        elif tt == "enrich":
            next_text += "\n[optional enrich — skip continues with cognition report]"
        try:
            self.query_one("#next-pane", NextActionPane).update_action(
                next_text, self.loop_progress
            )
        except Exception:
            pass
        if q.get("project_status") == "delivered" or self.delivered:
            self._show_delivery()

    def _show_delivery(self) -> None:
        artifact = self._artifact_path()
        try:
            banner = self.query_one("#delivery-banner", DeliveryBanner)
            banner.show_delivered(str(artifact) if artifact.exists() else "")
        except Exception:
            pass

    def _artifact_path(self) -> Path:
        base = self.data_dir or Path(
            os.environ.get("TURINGOS_DATA_DIR", Path.home() / ".local/share/turingos")
        )
        return Path(base) / "projects" / self.project_id / "delivered.json"

    def _write_artifact(self) -> None:
        path = self._artifact_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        q = self._get_projection()
        path.write_text(json.dumps({"status": "delivered", "projection": q}, indent=2))

    def _dispatch(self, event_type: str, payload: dict | None = None) -> str:
        ev = make_event(event_type, payload or {})
        mid = wtool_append(self.project_id, ev, data_dir=self.data_dir)
        self.last_action = f"{event_type}->{mid}"
        self.loop_progress = min(100, self.loop_progress + 15)
        self.refresh_projection()
        return mid

    def _should_auto_approve(self) -> bool:
        return self.autonomy >= 100 and bool(self.pending_proposals)

    def _snapshot_turn(self, turn: dict) -> dict:
        return {
            "turn": dict(turn),
            "config_draft": dict(self.config_draft) if self.config_draft else None,
        }

    def _push_turn_history(self, turn: dict) -> None:
        snap = self._snapshot_turn(turn)
        if self.history_index < len(self.turn_history) - 1:
            self.turn_history = self.turn_history[: self.history_index + 1]
        self.turn_history.append(snap)
        self.history_index = len(self.turn_history) - 1

    def _restore_history_index(self, index: int) -> None:
        if index < 0 or index >= len(self.turn_history):
            return
        snap = self.turn_history[index]
        self.history_index = index
        self.config_draft = (
            dict(snap["config_draft"]) if snap.get("config_draft") else None
        )
        self._apply_facilitator_turn(snap["turn"], record_history=False)

    def _navigate_turn_history(self, delta: int) -> None:
        target = self.history_index + delta
        if 0 <= target < len(self.turn_history):
            self._restore_history_index(target)
            self.last_action = f"nav:{'back' if delta < 0 else 'forward'} → {target + 1}/{len(self.turn_history)}"
            self.refresh_projection()

    def _turn_with_nav(self, turn: dict) -> dict:
        if turn.get("turn_type") != "clarify":
            return dict(turn)
        out = dict(turn)
        can_back = self.history_index > 0
        can_forward = self.history_index < len(self.turn_history) - 1
        out["choices"] = append_nav_choices(
            turn.get("choices") or [],
            can_back=can_back,
            can_forward=can_forward,
        )
        return out

    def _apply_facilitator_turn(
        self, turn: dict, *, record_history: bool = True, user_message: str = "",
    ) -> None:
        if turn.get("config_draft") is not None:
            self.config_draft = dict(turn["config_draft"])
        elif not turn.get("wizard_mode") and turn.get("turn_type") != "enrich":
            if turn.get("turn_type") == "clarify" and not self.config_draft:
                pass
        if "config_draft" not in turn and turn.get("turn_type") == "clarify":
            if not turn.get("wizard_mode") and record_history:
                self.config_draft = None

        self.facilitator_turn = turn
        if record_history:
            self._push_turn_history(turn)
            self.session_turns.append({
                "turn_type": turn.get("turn_type"),
                "summary": turn.get("summary", "")[:300],
                "skill_id": turn.get("skill_id"),
            })
        try:
            composer = self.query_one("#center-pane", VibeComposerPane)
            composer.render_turn(
                self._turn_with_nav(turn),
                user_message=user_message or self._last_user_message,
            )
            if user_message or turn.get("turn_type") == "chat":
                self._last_user_message = ""
        except Exception:
            pass
        if turn.get("turn_type") == "propose":
            self.pending_proposals = turn.get("proposals", [])
        elif turn.get("turn_type") != "enrich":
            self.pending_proposals = []

    async def _facilitator_run(
        self,
        *,
        user_text: str = "",
        selected_choice_id: str | None = None,
        select_action: str | None = None,
        boot: bool = False,
        choice: dict | None = None,
    ) -> None:
        async with self._facilitator_lock:
            composer = self.query_one("#center-pane", VibeComposerPane)
            composer.render_turn({
                "turn_type": "clarify",
                "summary": "*Facilitator 思考中…*",
                "choices": [],
                "proposals": [],
            })
            turn = await asyncio.to_thread(
                facilitate_turn,
                user_text=user_text,
                selected_choice_id=selected_choice_id,
                select_action=select_action,
                project_brief=self.project_brief,
                session_turns=self.session_turns,
                boot=boot,
                force_mock=self.force_mock_facilitator
                or not load_facilitator_config().get("api_key"),
                config_draft=self.config_draft,
                choice=choice,
            )
            if selected_choice_id == "cfg_save" or select_action == "cfg_save":
                self.project_brief = build_project_brief(
                    self.project_id, data_dir=self.data_dir
                )
                self.config_draft = None
                self._sync_model_label()
            elif turn.get("config_draft") is None and turn.get("wizard_mode"):
                if selected_choice_id in ("cfg_back_menu", "ai_setup") or select_action == "cfg_back_menu":
                    self.config_draft = None
            if not self.awaiting_config_field:
                try:
                    self.query_one("#center-pane", VibeComposerPane).hide_config_input()
                except Exception:
                    pass
            self._apply_facilitator_turn(turn, user_message=user_text)
            self.last_action = f"facilitator:{turn.get('turn_type')}"
            if user_text and turn.get("setup_result", {}).get("ok"):
                self.project_brief = build_project_brief(
                    self.project_id, data_dir=self.data_dir
                )
                self._sync_model_label()
            self.refresh_projection()
            if turn.get("turn_type") == "propose" and self._should_auto_approve():
                self._approve_proposals()

    async def _facilitator_boot(self) -> None:
        if self._boot_done:
            return
        self._boot_done = True
        await self._facilitator_run(boot=True)

    def _approve_proposals(self) -> None:
        if not self.pending_proposals:
            self.last_action = "approve: no pending proposals (pick「可以提交」first)"
            self.refresh_projection()
            return
        last_mid = ""
        for p in self.pending_proposals:
            last_mid = self._dispatch(p["event_type"], p.get("payload", {}))
        if any(
            p.get("payload", {}).get("status") == "delivered"
            or p.get("payload", {}).get("capsule_id") == "wc_delivered"
            for p in self.pending_proposals
        ):
            self.delivered = True
            self._write_artifact()
            self._show_delivery()
        self.pending_proposals = []
        self.refine_context = None
        self.last_action = f"approved & dispatched {last_mid}"
        enrich = mock_enrich_turn(last_mid)
        self._apply_facilitator_turn(enrich)
        self.refresh_projection()

    def on_vibe_composer_pane_choice_selected(
        self, event: VibeComposerPane.ChoiceSelected
    ) -> None:
        ch = event.choice
        action = ch.get("select_action")
        if event.choice_id == "nav_back" or action == "nav_back":
            self._navigate_turn_history(-1)
            return
        if event.choice_id == "nav_forward" or action == "nav_forward":
            self._navigate_turn_history(1)
            return
        if action == "config_input" or ch.get("config_field"):
            field = ch.get("config_field") or "api_key"
            self.awaiting_config_field = field
            prompt = ch.get(
                "input_prompt",
                "粘贴 API Key，然后点保存（keyring 安全存储）",
            )
            try:
                composer = self.query_one("#center-pane", VibeComposerPane)
                composer.show_config_input(field=field, prompt=prompt)
                self.last_action = f"config input: {field} — use panel below MCQ"
                self.refresh_projection()
            except Exception:
                pass
            return
        if event.choice_id == "other" or action == "freeform":
            self.awaiting_freeform = True
            try:
                inp = self.query_one("#center-pane #vibe-input", VibeInput)
                inp.placeholder = ch.get(
                    "input_prompt", "你还有什么其他需求？请在下方输入。"
                )
                self.last_action = "awaiting freeform input — type and Transcribe"
                self.refresh_projection()
            except Exception:
                pass
            return
        if event.choice_id == "submit" or action == "propose":
            summary = self.facilitator_turn.get("summary", "")
            asyncio.create_task(self._facilitator_run(
                user_text=summary,
                selected_choice_id="submit",
                select_action="propose",
            ))
            return
        if action == "skip" or event.choice_id == "skip":
            asyncio.create_task(self._facilitator_run(
                selected_choice_id="skip",
                select_action="skip",
            ))
            return
        asyncio.create_task(self._facilitator_run(
            user_text="",
            selected_choice_id=event.choice_id,
            select_action=action,
            choice=ch,
        ))

    def on_vibe_composer_pane_config_input_pressed(
        self, event: VibeComposerPane.ConfigInputPressed
    ) -> None:
        text = event.text.strip()
        if not text:
            return
        self.awaiting_config_field = event.field
        try:
            composer = self.query_one("#center-pane", VibeComposerPane)
            composer.query_one("#config-input", Input).value = ""
        except Exception:
            pass
        asyncio.create_task(self._facilitator_run(
            user_text=text,
            selected_choice_id="cfg_input",
            select_action="config_input",
        ))
        self.awaiting_config_field = None
        try:
            self.query_one("#center-pane", VibeComposerPane).hide_config_input()
        except Exception:
            pass

    def on_vibe_composer_pane_transcribe_pressed(
        self, event: VibeComposerPane.TranscribePressed
    ) -> None:
        text = event.text.strip()
        if not text and not self.awaiting_freeform and not self.awaiting_config_field:
            return
        self._last_user_message = text
        try:
            inp = self.query_one("#center-pane #vibe-input", VibeInput)
            inp.value = ""
        except Exception:
            pass
        from turingos.facilitator.provider_setup import is_provider_paste

        if self.config_draft and is_provider_paste(text):
            asyncio.create_task(self._facilitator_run(user_text=text))
            self.awaiting_config_field = None
            try:
                self.query_one("#center-pane", VibeComposerPane).hide_config_input()
            except Exception:
                pass
            return
        if self.awaiting_config_field or self.config_draft:
            asyncio.create_task(self._facilitator_run(
                user_text=text,
                selected_choice_id="cfg_input",
                select_action="config_input",
            ))
            self.awaiting_config_field = None
            try:
                self.query_one("#center-pane", VibeComposerPane).hide_config_input()
            except Exception:
                pass
            return
        asyncio.create_task(self._facilitator_run(
            user_text=text,
            selected_choice_id="other" if self.awaiting_freeform else None,
            select_action="freeform" if self.awaiting_freeform else None,
        ))
        self.awaiting_freeform = False

    def on_vibe_composer_pane_approve_pressed(
        self, _event: VibeComposerPane.ApprovePressed
    ) -> None:
        self._approve_proposals()

    def on_vibe_composer_pane_refine_pressed(
        self, _event: VibeComposerPane.RefinePressed
    ) -> None:
        try:
            inp = self.query_one("#center-pane #vibe-input", VibeInput)
            self.refine_context = (
                f"Previous: {json.dumps(self.pending_proposals)[:500]}"
            )
            inp.placeholder = "Refine your vibe…"
            self.last_action = "refine mode — edit input and transcribe again"
            self.refresh_projection()
        except Exception:
            pass

    def on_vibe_composer_pane_reject_pressed(
        self, _event: VibeComposerPane.RejectPressed
    ) -> None:
        self.pending_proposals = []
        self.refine_context = None
        self.facilitator_turn = {}
        self.pending_proposals = []
        try:
            composer = self.query_one("#center-pane", VibeComposerPane)
            composer.render_turn({
                "turn_type": "clarify",
                "summary": "已取消。",
                "choices": [],
                "proposals": [],
            })
        except Exception:
            pass
        self.last_action = "session rejected"
        self._boot_done = False
        self.session_turns = []
        self.turn_history = []
        self.history_index = -1
        self.config_draft = None
        asyncio.create_task(self._facilitator_run(boot=True))
        self.refresh_projection()

    def on_evidence_pane_replay_pressed(self, _event: EvidencePane.ReplayPressed) -> None:
        self.action_replay()

    def on_next_action_pane_loop_pressed(
        self, event: NextActionPane.LoopPressed
    ) -> None:
        self.last_action = f"loop:{event.loop}"
        self.loop_progress = min(100, self.loop_progress + 10)
        if event.loop == "execute" and self.pending_proposals:
            if self.autonomy >= 50 or self.headless:
                self._approve_proposals()
        self.refresh_projection()

    def _set_autonomy(self, val: int) -> None:
        self.autonomy = max(0, min(100, val))
        try:
            self.query_one("#top-bar", TopBar).autonomy = self.autonomy
            self.query_one("#auto-display", Static).update(f"{self.autonomy}%")
        except Exception:
            pass
        self.last_action = f"autonomy:{self.autonomy}%"
        self.refresh_projection()

    def on_button_pressed(self, event) -> None:
        bid = getattr(event.button, "id", None)
        if bid == "palette-btn":
            self.action_palette()
        elif bid == "auto-inc":
            self._set_autonomy(self.autonomy + 10)
        elif bid == "auto-dec":
            self._set_autonomy(self.autonomy - 10)

    def _poll_agent_bus(self) -> None:
        for ev in self.agent_bus.drain():
            self._handle_agent_event(ev)

    def _handle_agent_event(self, ev: dict) -> None:
        et = ev.get("event_type") or ev.get("type", "")
        if et == "IntentCaptured" or ev.get("action") == "vibe":
            text = ev.get("payload", {}).get("task") or ev.get("text", "")
            try:
                asyncio.get_running_loop()
                asyncio.create_task(self._facilitator_run(user_text=text))
            except RuntimeError:
                turn = facilitate_turn(
                    user_text=text,
                    project_brief=self.project_brief,
                    force_mock=True,
                )
                self._apply_facilitator_turn(turn)
                self.refresh_projection()
        elif et == "HumanDecision" or ev.get("action") == "approve":
            self._approve_proposals()
        elif ev.get("action") == "set_goal":
            self.current_goal = ev.get("goal", self.current_goal)
            try:
                self.query_one("#top-bar", TopBar).goal = self.current_goal
            except Exception:
                pass
        elif ev.get("action") == "set_autonomy":
            self.autonomy = int(ev.get("value", self.autonomy))
            self._set_autonomy(int(ev.get("value", self.autonomy)))

    async def _headless_agent_loop(self) -> None:
        while True:
            await asyncio.sleep(0.2)

    def get_projections(self) -> dict:
        """Agent API: read all projections."""
        return {
            "state": self._get_projection(),
            "pending_proposals": self.pending_proposals,
            "facilitator_turn": self.facilitator_turn,
            "autonomy": self.autonomy,
            "goal": self.current_goal,
            "last_action": self.last_action,
            "delivered": self.delivered,
        }

    def action_palette(self) -> None:
        def on_done(cmd: str | None) -> None:
            if cmd == "transcribe":
                try:
                    t = self.query_one("#center-pane #vibe-input", VibeInput).value
                    asyncio.create_task(self._do_transcribe(t))
                except Exception:
                    pass
            elif cmd == "approve":
                self._approve_proposals()
            elif cmd == "replay":
                self.action_replay()
            elif cmd == "auto_0":
                self.autonomy = 0
            elif cmd == "auto_50":
                self.autonomy = 50
            elif cmd == "auto_100":
                self.autonomy = 100
            elif cmd == "help":
                self.action_help()
            elif cmd == "quit":
                self.exit()

        self.push_screen(CommandPalette(), on_done)

    def action_quit(self) -> None:
        self.exit()

    def action_help(self) -> None:
        self.last_action = (
            "help: vibe composer + autonomy slider + loop buttons + palette (ctrl+k); "
            "legacy hotkeys i/A/r/d still work"
        )
        self.refresh_projection()

    def action_replay(self) -> None:
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
        lines = ["REPLAY (Micro Tape + anchors):"] + (nodes[-12:] if nodes else ["empty"])
        try:
            self.query_one("#evidence-pane", EvidencePane).update_evidence(lines)
        except Exception:
            pass
        self.last_action = "replay"
        self.refresh_projection()

    def action_intent(self) -> None:
        self._dispatch("IntentCaptured", {"task": "from-tui-i"})

    def action_next(self) -> None:
        self.last_action = "next-view"
        self.refresh_projection()

    def action_approve(self) -> None:
        if self.pending_proposals:
            self._approve_proposals()
        else:
            self._dispatch("HumanDecision", {"decision": "approve", "from": "tui-A"})

    def action_capsule(self) -> None:
        self.last_action = "capsule-view"
        self.refresh_projection()

    def action_dispatch(self) -> None:
        q = self._get_projection()
        caps = q.get("open_capsules", [])
        cid = caps[0] if caps else "from-tui-d"
        self._dispatch("WorkerDispatchPrepared", {"capsule_id": cid})

    def action_worker(self) -> None:
        self.last_action = "worker-view"
        self.refresh_projection()

    def action_observe(self) -> None:
        self._dispatch(
            "MacroObservationImported",
            {
                "capsule_id": "from-tui-o",
                "obs": {"macro_ref": f"macro:git:{self.project_id}:from-tui-o"},
            },
        )

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
        if self.pending_proposals:
            self._approve_proposals()
        elif caps:
            self._dispatch("WorkerDispatchPrepared", {"capsule_id": caps[0]})
        else:
            self.action_replay()

    @classmethod
    def run_headless(
        cls,
        project_id: str = "demo_app",
        data_dir: Path | None = None,
        *,
        agent_script: bool = False,
        force_mock: bool = True,
    ) -> "TuiApp":
        """Headless mode for agent-driven flows (no display)."""
        app = cls(
            project_id=project_id,
            data_dir=data_dir,
            headless=True,
            force_mock_facilitator=force_mock,
        )
        if agent_script:
            app.run(headless=True)
        return app