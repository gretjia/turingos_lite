"""Vibe TUI widgets: projection panes + composer (FC-A10 projection-only)."""
from __future__ import annotations

import json

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Input, Label, Markdown, ProgressBar, Static, TextArea, Tree
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget


class VibeInput(TextArea):
    """Multi-line NL composer; not auto-focused so legacy hotkeys reach the App."""

    ALLOW_MAXIMIZE = False

    def __init__(self, *args, **kwargs) -> None:
        self._placeholder = ""
        super().__init__(*args, **kwargs)

    def on_focus(self, _event) -> None:
        pass

    @property
    def value(self) -> str:
        return self.text

    @value.setter
    def value(self, text: str) -> None:
        self.text = text

    @property
    def placeholder(self) -> str:
        return self._placeholder

    @placeholder.setter
    def placeholder(self, text: str) -> None:
        self._placeholder = text


class TopBar(Horizontal):
    """Agency health, autonomy slider label, goal, model indicator."""

    autonomy = reactive(50)
    goal = reactive("Explore Software 3.0 agency")
    model_label = reactive("local-mock")
    health = reactive("OK")

    def compose(self) -> ComposeResult:
        yield Label("Agency: ", id="health-prefix")
        yield Label("OK", id="health-val")
        yield Label("  Autonomy: ", id="auto-prefix")
        yield Label("50%", id="auto-val")
        yield Label("  Goal: ", id="goal-prefix")
        yield Static(self.goal, id="goal-display")
        yield Label("  Model: ", id="model-prefix")
        yield Label("local-mock", id="model-val")
        yield Button("Voice", id="voice-btn", variant="default")
        yield Button("⌘K", id="palette-btn", variant="primary")

    def watch_autonomy(self, val: int) -> None:
        try:
            self.query_one("#auto-val", Label).update(f"{val}%")
        except Exception:
            pass

    def watch_goal(self, val: str) -> None:
        try:
            self.query_one("#goal-display", Static).update(val)
        except Exception:
            pass

    def watch_model_label(self, val: str) -> None:
        try:
            self.query_one("#model-val", Label).update(val)
        except Exception:
            pass

    def watch_health(self, val: str) -> None:
        try:
            self.query_one("#health-val", Label).update(val)
        except Exception:
            pass


class CapsulesPane(Vertical):
    """Left pane: micro state tree + capsule cards."""

    def compose(self) -> ComposeResult:
        yield Static("[bold]Capsules[/] • Micro State", classes="pane-title")
        yield Tree("Micro State", id="state-tree")
        yield Static("", id="caps-cards")

    def update_projection(self, projection: dict) -> None:
        tree = self.query_one("#state-tree", Tree)
        tree.clear()
        root = tree.root
        root.expand()
        root.add_leaf(f"tape_tip: {projection.get('tape_tip', '—')}")
        root.add_leaf(f"accepted: {projection.get('accepted_head', '—')}")
        root.add_leaf(f"status: {projection.get('project_status', '—')}")
        caps = projection.get("open_capsules", [])
        cap_node = root.add("open_capsules", expand=True)
        for c in caps:
            cap_node.add_leaf(c)
        cards = self.query_one("#caps-cards", Static)
        if caps:
            lines = [f"[green]●[/] {c}" for c in caps]
            cards.update("\n".join(lines))
        else:
            cards.update("[dim]no open capsules[/]")


class VibeComposerPane(Vertical):
    """Center: NL composer + streaming preview cards."""

    class TranscribePressed(Message):
        def __init__(self, text: str) -> None:
            self.text = text
            super().__init__()

    class ApprovePressed(Message):
        pass

    class RefinePressed(Message):
        pass

    class RejectPressed(Message):
        pass

    class ChoiceSelected(Message):
        def __init__(self, choice_id: str, choice: dict) -> None:
            self.choice_id = choice_id
            self.choice = choice
            super().__init__()

    class ConfigInputPressed(Message):
        def __init__(self, text: str, field: str) -> None:
            self.text = text
            self.field = field
            super().__init__()

    preview_md = reactive("")
    _choices_ready = True
    _config_input_field: str | None = None

    def compose(self) -> ComposeResult:
        yield Static("★ VIBE COMPOSER", classes="pane-title vibe-title")
        yield Static(
            "[dim]输入区（多行）— 可粘贴 NVIDIA/DeepSeek 官网示例代码整段，点 Send 自动识别[/]",
            id="composer-hint",
        )
        with Horizontal(id="composer-row"):
            yield VibeInput("", id="vibe-input", show_line_numbers=False)
            yield Button("Send", id="transcribe-btn", variant="primary")
        yield VerticalScroll(id="chat-thread")
        yield Markdown("", id="preview-md")
        yield Vertical(id="choice-bar")
        with Vertical(id="config-input-panel"):
            yield Static("", id="config-input-hint")
            with Horizontal(id="config-input-row"):
                yield Input(placeholder="", id="config-input")
                yield Button("保存", id="config-input-btn", variant="primary")
        yield Static("", id="tape-preview")
        with Horizontal(id="action-row"):
            yield Button("Refine", id="refine-btn")
            yield Button("Approve", id="approve-btn", variant="success")
            yield Button("Edit", id="edit-btn")
            yield Button("Reject", id="reject-btn", variant="error")

    def on_mount(self) -> None:
        self.hide_config_input()

    def show_config_input(self, *, field: str, prompt: str) -> None:
        """Reveal inline config field directly under MCQ (wizard api_key etc.)."""
        self._config_input_field = field
        panel = self.query_one("#config-input-panel")
        panel.display = True
        self.query_one("#config-input-hint", Static).update(
            f"[bold #58a6ff]→ {prompt}[/]"
        )
        inp = self.query_one("#config-input", Input)
        inp.password = field == "api_key"
        if field == "api_key":
            inp.placeholder = "粘贴 API Key（keyring 安全存储，不会写入日志）"
        elif field == "base_url":
            inp.placeholder = "https://api.example.com/v1"
        elif field == "model":
            inp.placeholder = "model 名称，例如 deepseek-chat"
        else:
            inp.placeholder = f"输入 {field}"
        inp.value = ""
        self.query_one("#composer-hint", Static).update(
            "[bold]配置向导[/] — 在 MCQ 下方输入框填写后点「保存」"
        )
        self.call_after_refresh(lambda: inp.focus())

    def hide_config_input(self) -> None:
        self._config_input_field = None
        try:
            panel = self.query_one("#config-input-panel")
            panel.display = False
            self.query_one("#config-input", Input).value = ""
        except Exception:
            pass

    def append_chat(self, role: str, content: str) -> None:
        thread = self.query_one("#chat-thread", VerticalScroll)
        label = "You" if role == "user" else "Facilitator"
        color = "#58a6ff" if role == "user" else "#3fb950"
        thread.mount(Static(f"[{color}]{label}:[/] {content[:2000]}"))
        thread.scroll_end(animate=False)

    def render_turn(self, turn: dict, *, user_message: str = "") -> None:
        """Render facilitator clarify / propose / enrich / chat turn."""
        md = self.query_one("#preview-md", Markdown)
        tape = self.query_one("#tape-preview", Static)
        turn_type = turn.get("turn_type", "clarify")
        summary = turn.get("summary", "")
        note = turn.get("facilitator_note", "")
        if user_message:
            self.append_chat("user", user_message)
        if turn_type == "chat":
            self.append_chat("facilitator", summary)
        parts = [f"### Facilitator\n\n{summary}"]
        if note:
            parts.append(f"*{note}*")
        if turn_type == "propose":
            props = turn.get("proposals", [])
            parts.append("\n**Proposal Card**")
            for i, p in enumerate(props, 1):
                et = p.get("event_type", "?")
                pl = p.get("payload", {})
                vis = pl.get("visible_markdown", "")
                parts.append(f"\n**{i}. {et}**")
                if vis:
                    parts.append(vis)
                else:
                    parts.append(f"```\n{json.dumps(pl, indent=2)[:500]}\n```")
            tape.update("[green]Will hit tape:[/] " + ", ".join(
                p["event_type"] for p in props
            ) if props else "")
        elif turn_type == "enrich":
            tape.update(
                "[dim]批准后可选补充 — 点「不需要，继续」查看项目认知并进入下一步[/]"
            )
        elif turn_type == "chat":
            tape.update("[dim]对话模式 — 回复已显示在上方线程；可选 MCQ 继续[/]")
        elif turn.get("wizard_mode"):
            tape.update("[dim]配置向导 — 按步骤输入；可点「退回」返回上一题[/]")
        else:
            tape.update(
                "[dim]选择一项；「我理解对了，可以提交」后出现 Approve；"
                "「← 退回上一题」可回看；「其他需求」在下方输入[/]"
            )
        md.update("\n\n".join(parts))
        self._choices_ready = False
        self._render_choices(turn.get("choices") or [])
        self.call_after_refresh(self._mark_choices_ready)
        self._set_approve_visible(turn_type == "propose")
        if turn_type == "chat":
            self._set_approve_visible(False)

    def _mark_choices_ready(self) -> None:
        self._choices_ready = True

    def _render_choices(self, choices: list[dict]) -> None:
        bar = self.query_one("#choice-bar", Vertical)
        bar.remove_children()
        for ch in choices:
            cid = ch.get("id", "opt")
            label = ch.get("label", cid)
            btn = Button(label, id=f"mcq-{cid}", variant="default")
            btn.can_focus = False
            btn.choice_data = ch  # type: ignore[attr-defined]
            bar.mount(btn)

    def _set_approve_visible(self, visible: bool) -> None:
        try:
            self.query_one("#approve-btn", Button).display = visible
        except Exception:
            pass

    def set_preview(self, proposals: list[dict], streaming: str = "") -> None:
        md = self.query_one("#preview-md", Markdown)
        tape = self.query_one("#tape-preview", Static)
        if streaming:
            md.update(streaming)
            return
        if not proposals:
            md.update("*No proposal yet — transcribe a vibe.*")
            tape.update("")
            return
        parts = ["### Proposal Card\n"]
        for i, p in enumerate(proposals, 1):
            et = p.get("event_type", "?")
            pl = p.get("payload", {})
            vis = pl.get("visible_markdown", "")
            parts.append(f"**{i}. {et}**")
            if vis:
                parts.append(vis)
            else:
                parts.append(f"```\n{json.dumps(pl, indent=2)[:500]}\n```")
        md.update("\n\n".join(parts))
        tape.update(
            "[dim]Will hit tape:[/] "
            + ", ".join(p["event_type"] for p in proposals)
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if not self._choices_ready:
            return
        bid = event.button.id or ""
        if bid.startswith("mcq-"):
            cid = bid[4:]
            ch = getattr(event.button, "choice_data", {"id": cid})
            self.post_message(self.ChoiceSelected(cid, ch))
        elif bid == "transcribe-btn":
            text = self.query_one("#vibe-input", VibeInput).value
            self.post_message(self.TranscribePressed(text))
        elif bid == "config-input-btn":
            field = self._config_input_field or "api_key"
            text = self.query_one("#config-input", Input).value
            self.post_message(self.ConfigInputPressed(text, field))
        elif bid == "approve-btn":
            self.post_message(self.ApprovePressed())
        elif bid == "refine-btn":
            self.post_message(self.RefinePressed())
        elif bid == "reject-btn":
            self.post_message(self.RejectPressed())


class NextActionPane(Vertical):
    """Right-top: next sovereign action + loop buttons."""

    class LoopPressed(Message):
        def __init__(self, loop: str) -> None:
            self.loop = loop
            super().__init__()

    def compose(self) -> ComposeResult:
        yield Static("Next Action + Loop", classes="pane-title")
        yield Static("", id="next-text")
        yield ProgressBar(total=100, show_eta=False, id="loop-progress")
        with Horizontal():
            yield Button("Goal", id="loop-goal")
            yield Button("Set", id="loop-set")
            yield Button("Orchestrate", id="loop-orch")
            yield Button("Execute", id="loop-exec")
            yield Button("Verify", id="loop-verify")

    def update_action(self, text: str, progress: int = 0) -> None:
        self.query_one("#next-text", Static).update(text)
        self.query_one("#loop-progress", ProgressBar).progress = progress

    def on_button_pressed(self, event: Button.Pressed) -> None:
        loop_map = {
            "loop-goal": "goal",
            "loop-set": "set",
            "loop-orch": "orchestrate",
            "loop-exec": "execute",
            "loop-verify": "verify",
        }
        if event.button.id in loop_map:
            self.post_message(self.LoopPressed(loop_map[event.button.id]))


class EvidencePane(VerticalScroll):
    """Right-bottom: append-only evidence timeline + replay."""

    class ReplayPressed(Message):
        pass

    def compose(self) -> ComposeResult:
        yield Static("Evidence Timeline + Failure Log", classes="pane-title")
        yield Static("", id="evidence-log")
        yield Button("Replay", id="replay-btn", variant="default")

    def update_evidence(self, lines: list[str]) -> None:
        log = self.query_one("#evidence-log", Static)
        log.update("\n".join(lines) if lines else "[dim]no evidence[/]")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "replay-btn":
            self.post_message(self.ReplayPressed())


class DeliveryBanner(Static):
    """Full-width delivery success card."""

    def show_delivered(self, artifact_path: str = "") -> None:
        self.update(
            "[bold green on black]  PROJECT DELIVERED  [/]\n"
            f"[green]Micro Tape complete.[/]"
            + (f"\nArtifact: {artifact_path}" if artifact_path else "")
        )
        self.display = True

    def hide(self) -> None:
        self.display = False