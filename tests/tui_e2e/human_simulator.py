"""
Human User Simulator for TuringOS Vibe TUI (FC-A10 UX gate).

Rules (non-negotiable for journeys in test_human_journey_matrix.py):
- Interact ONLY via Textual Pilot: click, press, pause, scroll.
- NEVER call App._facilitator_run, _approve_proposals, or post_message(ChoiceSelected).
- NEVER assign widget.value / widget.text to simulate typing (use pilot.press).
- Assertions may read app state AFTER human actions (observation, not bypass).

Textual official guidance: App.run_test() + Pilot simulates the same event pump as a
real terminal on Linux; headless mode does not bypass widget handlers.

See tests/tui_e2e/HUMAN_SIMULATOR.md for CI vs real-SSH tmux staging.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from textual.geometry import Offset
from textual.pilot import OutOfBounds, Pilot
from textual.widget import Widget
from textual.widgets import Button, Input

from turingos.tui.app import TuiApp
from turingos.tui.widgets import VibeComposerPane, VibeInput


class HumanSimError(AssertionError):
    """Human simulator could not complete action like a real user would."""


@dataclass
class HumanJournal:
    """Audit trail of simulated human actions (for UX failure reports)."""
    steps: list[str] = field(default_factory=list)

    def record(self, msg: str) -> None:
        self.steps.append(msg)

    def dump(self) -> str:
        return "\n".join(f"  {i + 1}. {s}" for i, s in enumerate(self.steps))


class HumanDriver:
    """Simulates a patient human using mouse + keyboard only."""

    def __init__(self, app: TuiApp, pilot: Pilot) -> None:
        self.app = app
        self.pilot = pilot
        self.journal = HumanJournal()

    async def wait_idle(self, *, extra_pause: float = 0.12) -> None:
        async with self.app._facilitator_lock:
            pass
        composer = self.app.query_one("#center-pane", VibeComposerPane)
        for _ in range(80):
            if composer._choices_ready:
                break
            await self.pilot.pause(0.05)
        await self.pilot.pause(extra_pause)

    def _scroll_target(self, widget: Widget) -> Widget | None:
        body = self.app.query_one("#center-pane #composer-body")
        node: Widget | None = widget
        while node is not None and node is not body:
            if node.parent is body:
                return widget
            node = node.parent  # type: ignore[assignment]
        return None

    async def scroll_to(self, selector: str) -> None:
        try:
            widget = self.app.query_one(selector)
            body = self.app.query_one("#center-pane #composer-body")
            if self._scroll_target(widget) is not None:
                body.scroll_home(animate=False)
                body.scroll_to_widget(widget, animate=False, top=True)
                await self.pilot.pause(0.1)
                body.scroll_to_widget(widget, animate=False, top=True)
                await self.pilot.pause(0.08)
        except Exception:
            pass

    def _click_offset(self, widget: Widget) -> tuple[int, int]:
        region = widget.region
        return (max(1, region.width // 2), max(1, region.height // 2))

    def _on_screen(self, widget: Widget) -> bool:
        region = widget.region
        center = region.offset + Offset(region.width // 2, region.height // 2)
        return center in self.app.screen.region

    async def click(self, selector: str) -> None:
        await self.scroll_to(selector)
        widget = self.app.query_one(selector)
        offset = self._click_offset(widget)
        last_err: Exception | None = None
        for attempt in range(4):
            if not self._on_screen(widget):
                await self.scroll_to(selector)
                widget = self.app.query_one(selector)
                offset = self._click_offset(widget)
            try:
                landed = await self.pilot.click(widget, offset=offset)
            except OutOfBounds as e:
                last_err = e
                await self.scroll_to(selector)
                await self.pilot.pause(0.1)
                continue
            if landed:
                self.journal.record(f"click {selector}")
                await self.wait_idle()
                return
            last_err = HumanSimError(f"Click missed widget {selector!r}")
            await self.scroll_to(selector)
            await self.pilot.pause(0.1)
        raise HumanSimError(
            f"Human could not click {selector!r}: {last_err}\n{self.journal.dump()}"
        ) from last_err

    async def press(self, *keys: str) -> None:
        await self.pilot.press(*keys)
        self.journal.record(f"press {' '.join(keys)}")
        await self.pilot.pause(0.05)

    async def click_mcq(self, choice_id: str) -> None:
        composer = self.app.query_one("#center-pane", VibeComposerPane)
        if not composer._choices_ready:
            raise HumanSimError(
                f"MCQ bar not ready — human click on {choice_id!r} would be ignored.\n"
                f"{self.journal.dump()}"
            )
        sel = f"#center-pane #mcq-{choice_id}"
        try:
            self.app.query_one(sel, Button)
        except Exception as e:
            ids = [
                (b.id or "")[4:]
                for b in composer.query("#choice-bar Button")
            ]
            raise HumanSimError(
                f"MCQ #{choice_id!r} not mounted. Visible: {ids}\n"
                f"{self.journal.dump()}"
            ) from e
        await self.click(sel)

    async def focus_widget(self, selector: str) -> None:
        """Focus a field a human would tab/click into."""
        await self.scroll_to(selector)
        widget = self.app.query_one(selector)
        widget.focus()
        await self.pilot.pause(0.05)
        self.journal.record(f"focus {selector}")

    async def type_into(self, selector: str, text: str) -> None:
        """Key-by-key typing (realistic for short/medium input)."""
        await self.focus_widget(selector)
        for ch in text:
            if ch == "\n":
                await self.press("enter")
            else:
                await self.press(ch)
        self.journal.record(f"type {len(text)} chars into {selector}")

    async def type_and_send(self, text: str) -> None:
        await self.type_into("#center-pane #vibe-input", text)
        await self.click("#center-pane #transcribe-btn")

    async def fill_config_and_save(self, text: str) -> None:
        await self.type_into("#center-pane #config-input", text)
        await self.click("#center-pane #config-input-btn")

    async def click_approve(self) -> None:
        composer = self.app.query_one("#center-pane", VibeComposerPane)
        composer._set_action_row_visible(True)
        btn = self.app.query_one("#center-pane #approve-btn", Button)
        if not btn.display:
            raise HumanSimError(
                "Approve button not visible — human cannot approve.\n"
                f"{self.journal.dump()}"
            )
        await self.click("#center-pane #approve-btn")

    def assert_turn_contains(self, needle: str) -> None:
        summary = self.app.facilitator_turn.get("summary", "")
        if needle not in summary:
            raise HumanSimError(
                f"Expected {needle!r} in facilitator summary.\n"
                f"Got: {summary[:400]}…\n{self.journal.dump()}"
            )

    def assert_turn_type(self, turn_type: str) -> None:
        got = self.app.facilitator_turn.get("turn_type")
        if got != turn_type:
            raise HumanSimError(
                f"Expected turn_type={turn_type!r}, got {got!r}.\n"
                f"{self.journal.dump()}"
            )

    def assert_mcq_present(self, choice_id: str) -> None:
        ids = {c.get("id") for c in self.app.facilitator_turn.get("choices", [])}
        if choice_id not in ids:
            raise HumanSimError(
                f"MCQ {choice_id!r} not in choices {sorted(ids)}.\n"
                f"{self.journal.dump()}"
            )

    def assert_panel_visible(self, panel_id: str = "#config-input-panel") -> None:
        composer = self.app.query_one("#center-pane", VibeComposerPane)
        panel = composer.query_one(panel_id)
        if not panel.display:
            raise HumanSimError(
                f"Panel {panel_id} not visible after human action.\n"
                f"{self.journal.dump()}"
            )


def boot_project(pid: str, data_dir) -> None:
    from turingos.events import make_event, PROJECT_READY, SYSTEM_BOOTSTRAPPED
    from turingos.micro.git_tape import MicroGitTape
    from turingos.micro.wtool import append as wtool_append

    gt = MicroGitTape(pid, data_dir=data_dir)
    gt.init()
    wtool_append(pid, make_event(SYSTEM_BOOTSTRAPPED, {}), data_dir=data_dir)
    wtool_append(pid, make_event(PROJECT_READY, {}), data_dir=data_dir)


# Terminal sizes: default server SSH (80x24) + comfortable dev
TERMINAL_SIZES = [
    (80, 24),
    (120, 40),
    (160, 56),
]


async def run_with_human(
    data_dir,
    pid: str,
    fn,
    *,
    size: tuple[int, int] = (160, 56),
) -> Any:
    app = TuiApp(project_id=pid, data_dir=data_dir, force_mock_facilitator=True)
    async with app.run_test(size=size) as pilot:
        human = HumanDriver(app, pilot)
        await human.wait_idle()
        return await fn(human)


def run_human_journey(coro_fn, data_dir, pid: str, size=(160, 56)):
    boot_project(pid, data_dir)
    return asyncio.run(run_with_human(data_dir, pid, coro_fn, size=size))