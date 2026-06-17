"""
Real TUI E2E: Textual Pilot clicks buttons (User-Simulator layer).

Unlike unit tests that call _facilitator_run() directly, these exercise
the same code path as a human clicking MCQ + Send.
"""
from __future__ import annotations

import asyncio
import os

import pytest

from turingos.events import make_event, PROJECT_READY, SYSTEM_BOOTSTRAPPED
from turingos.micro.git_tape import MicroGitTape
from turingos.micro.rtool import MicroRtool
from turingos.micro.wtool import append as wtool_append
from turingos.tui.app import TuiApp
from turingos.tui.widgets import VibeComposerPane


@pytest.fixture
def e2e_data(tmp_path):
    d = tmp_path / "tui_e2e"
    d.mkdir()
    os.environ["TURINGOS_DATA_DIR"] = str(d)
    return d


E2E_SIZE = (160, 56)


async def _pilot_click_choice(app: TuiApp, pilot, choice_id: str) -> None:
    """Click MCQ button; fall back to message dispatch if off-screen."""
    sel = f"#mcq-{choice_id}"
    ch = next(
        (c for c in app.facilitator_turn.get("choices", []) if c.get("id") == choice_id),
        {"id": choice_id},
    )
    composer = app.query_one("#center-pane", VibeComposerPane)
    if choice_id.startswith("cfg_input"):
        composer.post_message(composer.ChoiceSelected(choice_id, ch))
    else:
        try:
            await pilot.click(sel)
        except Exception:
            composer.post_message(composer.ChoiceSelected(choice_id, ch))
    await _wait_facilitator_idle(app, pilot)


async def _wait_facilitator_idle(app: TuiApp, pilot) -> None:
    """Wait for async facilitator + MCQ mount (choices_ready guard)."""
    async with app._facilitator_lock:
        pass
    composer = app.query_one("#center-pane", VibeComposerPane)
    for _ in range(60):
        if composer._choices_ready:
            break
        await pilot.pause(0.05)
    await pilot.pause(0.15)


def _boot_tape(pid: str, data_dir) -> None:
    gt = MicroGitTape(pid, data_dir=data_dir)
    gt.init()
    wtool_append(pid, make_event(SYSTEM_BOOTSTRAPPED, {}), data_dir=data_dir)
    wtool_append(pid, make_event(PROJECT_READY, {}), data_dir=data_dir)


def test_pilot_boot_shows_cognition(e2e_data):
    pid = "e2e_boot"
    _boot_tape(pid, e2e_data)

    async def drive():
        app = TuiApp(project_id=pid, data_dir=e2e_data, force_mock_facilitator=True)
        async with app.run_test(size=E2E_SIZE) as pilot:
            await _wait_facilitator_idle(app, pilot)
            assert "项目认知" in app.facilitator_turn.get("summary", "")

    asyncio.run(drive())


def test_pilot_config_api_key_panel_visible(e2e_data):
    """Clicking API Key MCQ must reveal inline input below choices."""
    pid = "e2e_cfg_key"
    _boot_tape(pid, e2e_data)

    async def drive():
        app = TuiApp(project_id=pid, data_dir=e2e_data, force_mock_facilitator=True)
        async with app.run_test(size=E2E_SIZE) as pilot:
            await _wait_facilitator_idle(app, pilot)
            await _pilot_click_choice(app, pilot, "ai_setup")
            await _wait_facilitator_idle(app, pilot)
            await _pilot_click_choice(app, pilot, "skill_openai")
            await _wait_facilitator_idle(app, pilot)
            await _pilot_click_choice(app, pilot, "cfg_input_base")
            await _wait_facilitator_idle(app, pilot)
            composer = app.query_one("#center-pane", VibeComposerPane)
            cfg_inp = composer.query_one("#config-input")
            cfg_inp.value = "https://api.deepseek.com/v1"
            await pilot.click("#config-input-btn")
            await _wait_facilitator_idle(app, pilot)
            await _pilot_click_choice(app, pilot, "cfg_input_key")
            await _wait_facilitator_idle(app, pilot)
            panel = composer.query_one("#config-input-panel")
            assert panel.display is True
            assert composer.query_one("#config-input").password is True

    asyncio.run(drive())


def test_pilot_click_ai_setup_opens_wizard(e2e_data):
    pid = "e2e_cfg"
    _boot_tape(pid, e2e_data)

    async def drive():
        app = TuiApp(project_id=pid, data_dir=e2e_data, force_mock_facilitator=True)
        async with app.run_test(size=E2E_SIZE) as pilot:
            await _wait_facilitator_idle(app, pilot)
            await _pilot_click_choice(app, pilot, "ai_setup")
            await _wait_facilitator_idle(app, pilot)
            assert app.facilitator_turn.get("wizard_mode")
            assert any(
                c["id"] == "skill_openai"
                for c in app.facilitator_turn.get("choices", [])
            )

    asyncio.run(drive())


def test_pilot_send_project_question_chat_reply(e2e_data):
    pid = "e2e_chat"
    _boot_tape(pid, e2e_data)

    async def drive():
        app = TuiApp(project_id=pid, data_dir=e2e_data, force_mock_facilitator=True)
        async with app.run_test(size=E2E_SIZE) as pilot:
            await _wait_facilitator_idle(app, pilot)
            inp = app.query_one("#center-pane #vibe-input")
            inp.value = "这个项目的主要结构是什么？README 讲了什么？"
            await pilot.click("#transcribe-btn")
            await _wait_facilitator_idle(app, pilot)
            assert app.facilitator_turn.get("turn_type") == "chat"
            thread = app.query_one("#center-pane #chat-thread")
            assert len(thread.children) >= 2

    asyncio.run(drive())


def test_pilot_deepseek_token_auto_setup(e2e_data):
    pid = "e2e_deepseek"
    _boot_tape(pid, e2e_data)

    async def drive():
        app = TuiApp(project_id=pid, data_dir=e2e_data, force_mock_facilitator=True)
        async with app.run_test(size=E2E_SIZE) as pilot:
            await _wait_facilitator_idle(app, pilot)
            inp = app.query_one("#center-pane #vibe-input")
            inp.value = "我从 deepseek 官网取得了 api key: sk-fake1234567890abcdef"
            await pilot.click("#transcribe-btn")
            await _wait_facilitator_idle(app, pilot)
            assert app.facilitator_turn.get("turn_type") == "chat"
            assert "DeepSeek" in app.facilitator_turn.get("summary", "")
            assert app.facilitator_turn.get("setup_result", {}).get("provider") == "deepseek"

    asyncio.run(drive())


def test_pilot_full_submit_approve_flow(e2e_data):
    pid = "e2e_flow"
    _boot_tape(pid, e2e_data)
    r = MicroRtool(pid, data_dir=e2e_data)
    pre = r.read_tip()

    async def drive():
        app = TuiApp(project_id=pid, data_dir=e2e_data, force_mock_facilitator=True)
        async with app.run_test(size=E2E_SIZE) as pilot:
            await _wait_facilitator_idle(app, pilot)
            await _pilot_click_choice(app, pilot, "explore")
            await _wait_facilitator_idle(app, pilot)
            await _pilot_click_choice(app, pilot, "submit")
            await _wait_facilitator_idle(app, pilot)
            assert app.facilitator_turn.get("turn_type") == "propose"
            app._approve_proposals()
            await _wait_facilitator_idle(app, pilot)
            assert app.facilitator_turn.get("turn_type") == "enrich"

    asyncio.run(drive())
    assert r.read_tip() != pre