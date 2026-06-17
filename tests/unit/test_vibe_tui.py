"""Vibe TUI unit tests: composer, autonomy, facilitator mock, layout."""
import asyncio
import os
from pathlib import Path

import pytest

from turingos.events import INTENT_CAPTURED, WORK_CAPSULE_BUILT, HUMAN_DECISION
from turingos.facilitator.facilitate import facilitate_turn, mock_facilitate_turn
from turingos.facilitator.transcribe import mock_transcribe, transcribe_intent
from turingos.micro.git_tape import MicroGitTape
from turingos.micro.rtool import MicroRtool
from turingos.micro.wtool import append as wtool_append
from turingos.events import make_event, SYSTEM_BOOTSTRAPPED, PROJECT_READY
from turingos.tui.app import TuiApp
from turingos.tui.agent_bus import AgentBus


@pytest.fixture
def data_dir(tmp_path):
    d = tmp_path / "vibe_tui_data"
    d.mkdir()
    return d


def test_mock_transcribe_todo_capsule():
    props = mock_transcribe("vibe: create a todo app with persistence", {"project_id": "p1"})
    types = {p["event_type"] for p in props}
    assert INTENT_CAPTURED in types
    assert WORK_CAPSULE_BUILT in types
    assert any("wc_" in p.get("payload", {}).get("capsule_id", "") for p in props)


def test_mock_transcribe_deliver():
    props = mock_transcribe("完成并交付", {"project_id": "p1"})
    assert any(p["event_type"] == HUMAN_DECISION for p in props)


def test_transcribe_force_mock_without_key(data_dir):
    os.environ["TURINGOS_DATA_DIR"] = str(data_dir)
    props = transcribe_intent("explore project history", {"project_id": "x", "has_git": True}, force_mock=True)
    assert len(props) >= 1


def test_autonomy_levels(data_dir):
    os.environ["TURINGOS_DATA_DIR"] = str(data_dir)
    pid = "auto_test"
    gt = MicroGitTape(pid, data_dir=data_dir)
    gt.init()

    app0 = TuiApp(project_id=pid, data_dir=data_dir, force_mock_facilitator=True)
    app0.autonomy = 0
    app0.pending_proposals = mock_transcribe("todo app", {"project_id": pid})
    assert not app0._should_auto_approve()

    app50 = TuiApp(project_id=pid, data_dir=data_dir, force_mock_facilitator=True)
    app50.autonomy = 50
    app50.pending_proposals = [
        {
            "event_type": WORK_CAPSULE_BUILT,
            "payload": {"capsule_id": "wc_agent_code", "auto_execute": True, "worker": "api"},
        }
    ]
    assert app50._should_auto_approve()

    app50b = TuiApp(project_id=pid, data_dir=data_dir, force_mock_facilitator=True)
    app50b.autonomy = 50
    app50b.pending_proposals = [{"event_type": INTENT_CAPTURED, "payload": {"task": "x"}}]
    assert not app50b._should_auto_approve()

    app100 = TuiApp(project_id=pid, data_dir=data_dir, force_mock_facilitator=True)
    app100.autonomy = 100
    app100.pending_proposals = [{"event_type": WORK_CAPSULE_BUILT, "payload": {"capsule_id": "wc"}}]
    assert app100._should_auto_approve()


def test_vibe_compose_approve_dispatch(data_dir):
    os.environ["TURINGOS_DATA_DIR"] = str(data_dir)
    pid = "vibe_flow"
    gt = MicroGitTape(pid, data_dir=data_dir)
    gt.init()
    wtool_append(pid, make_event(SYSTEM_BOOTSTRAPPED, {"boot": "vibe"}), data_dir=data_dir)
    wtool_append(pid, make_event(PROJECT_READY, {"name": pid}), data_dir=data_dir)
    r = MicroRtool(pid, data_dir=data_dir)
    pre_tip = r.read_tip()

    async def drive():
        app = TuiApp(project_id=pid, data_dir=data_dir, force_mock_facilitator=True)
        async with app.run_test() as pilot:
            await pilot.pause(1.0)
            await app._facilitator_run(
                selected_choice_id="submit", select_action="propose", user_text="create todo"
            )
            assert app.pending_proposals
            app._approve_proposals()
            await pilot.pause(0.5)
            await pilot.press("q")
            await pilot.pause()

    asyncio.run(drive())

    post_tip = r.read_tip()
    assert post_tip != pre_tip


def test_agent_bus_drives_flow(data_dir):
    os.environ["TURINGOS_DATA_DIR"] = str(data_dir)
    pid = "agent_bus"
    gt = MicroGitTape(pid, data_dir=data_dir)
    gt.init()
    bus = AgentBus()
    app = TuiApp(project_id=pid, data_dir=data_dir, agent_bus=bus, force_mock_facilitator=True)
    app.project_brief = {"project_id": pid, "has_git": True}
    bus.post({"action": "vibe", "text": "create todo app"})
    app._poll_agent_bus()
    assert app.facilitator_turn.get("turn_type") in ("clarify", "propose")
    turn = facilitate_turn(
        user_text="todo",
        select_action="propose",
        selected_choice_id="submit",
        project_brief=app.project_brief,
        force_mock=True,
    )
    app.pending_proposals = turn.get("proposals", [])
    bus.post({"action": "approve"})
    app._handle_agent_event({"action": "approve"})
    r = MicroRtool(pid, data_dir=data_dir)
    assert r.read_tip().startswith("μ:")


def test_headless_get_projections(data_dir):
    os.environ["TURINGOS_DATA_DIR"] = str(data_dir)
    pid = "headless_proj"
    gt = MicroGitTape(pid, data_dir=data_dir)
    gt.init()
    app = TuiApp(project_id=pid, data_dir=data_dir, headless=True, force_mock_facilitator=True)
    proj = app.get_projections()
    assert "state" in proj
    assert proj["state"]["project_id"] == pid


def test_layout_mode_for_regular_terminal(data_dir):
    os.environ["TURINGOS_DATA_DIR"] = str(data_dir)
    pid = "layout_regular"
    gt = MicroGitTape(pid, data_dir=data_dir)
    gt.init()

    async def drive():
        app = TuiApp(project_id=pid, data_dir=data_dir, force_mock_facilitator=True)
        async with app.run_test(size=(122, 30)) as pilot:
            await pilot.pause(0.2)
            assert app.has_class("focus")
            assert not app.has_class("compact")
            assert not app.has_class("wide")

    asyncio.run(drive())


def test_layout_mode_for_wide_terminal(data_dir):
    os.environ["TURINGOS_DATA_DIR"] = str(data_dir)
    pid = "layout_wide"
    gt = MicroGitTape(pid, data_dir=data_dir)
    gt.init()

    async def drive():
        app = TuiApp(project_id=pid, data_dir=data_dir, force_mock_facilitator=True)
        async with app.run_test(size=(287, 66)) as pilot:
            await pilot.pause(0.2)
            assert app.has_class("wide")
            assert not app.has_class("compact")
            assert not app.has_class("focus")

    asyncio.run(drive())


def test_next_action_buttons_split_for_wide_terminal(data_dir):
    os.environ["TURINGOS_DATA_DIR"] = str(data_dir)
    pid = "layout_loop_controls"
    gt = MicroGitTape(pid, data_dir=data_dir)
    gt.init()

    async def drive():
        app = TuiApp(project_id=pid, data_dir=data_dir, force_mock_facilitator=True)
        async with app.run_test(size=(252, 66)) as pilot:
            await pilot.pause(0.2)
            primary_ids = [button.id for button in app.query("#loop-row-primary Button")]
            action_ids = [button.id for button in app.query("#loop-row-action Button")]
            assert primary_ids == ["loop-goal", "loop-set", "loop-orch"]
            assert action_ids == ["loop-exec", "loop-verify"]

    asyncio.run(drive())


def test_vibe_input_is_large_enough_for_long_prompts(data_dir):
    os.environ["TURINGOS_DATA_DIR"] = str(data_dir)
    pid = "layout_large_input"
    gt = MicroGitTape(pid, data_dir=data_dir)
    gt.init()

    async def drive():
        app = TuiApp(project_id=pid, data_dir=data_dir, force_mock_facilitator=True)
        async with app.run_test(size=(252, 66)) as pilot:
            await pilot.pause(0.2)
            vibe_input = app.query_one("#center-pane #vibe-input")
            send = app.query_one("#center-pane #transcribe-btn")
            assert vibe_input.region.height >= 8
            assert send.region.height >= 8

    asyncio.run(drive())


def test_loop_goal_keeps_user_in_actionable_conversation(data_dir):
    os.environ["TURINGOS_DATA_DIR"] = str(data_dir)
    pid = "loop_goal_actionable"
    gt = MicroGitTape(pid, data_dir=data_dir)
    gt.init()

    async def drive():
        app = TuiApp(project_id=pid, data_dir=data_dir, force_mock_facilitator=True)
        async with app.run_test(size=(252, 66)) as pilot:
            await pilot.pause(0.2)
            await pilot.click("#right-col #loop-goal")
            assert app.facilitator_turn["turn_type"] == "clarify"
            ids = {c["id"] for c in app.facilitator_turn.get("choices", [])}
            assert {"task", "explore", "other"}.issubset(ids)
            assert "loop:goal" in app.last_action

    asyncio.run(drive())


def test_chinese_vibe_input_round_trip(data_dir):
    os.environ["TURINGOS_DATA_DIR"] = str(data_dir)
    pid = "zh_input_round_trip"
    gt = MicroGitTape(pid, data_dir=data_dir)
    gt.init()

    async def drive():
        from tests.tui_e2e.human_simulator import HumanDriver

        app = TuiApp(project_id=pid, data_dir=data_dir, force_mock_facilitator=True)
        async with app.run_test(size=(160, 48)) as pilot:
            driver = HumanDriver(app, pilot)
            await driver.wait_idle()
            text = "请分析这个项目告诉我下一步应该做什么"
            await driver.type_and_send(text)
            await pilot.pause(0.6)
            chat = app.query_one("#center-pane #chat-thread")
            rendered = "\n".join(str(child.content) for child in chat.children)
            assert text in rendered
            assert app.facilitator_turn.get("turn_type") in ("chat", "clarify", "propose")

    asyncio.run(drive())


def test_layout_mode_updates_after_terminal_resize(data_dir):
    os.environ["TURINGOS_DATA_DIR"] = str(data_dir)
    pid = "layout_resize"
    gt = MicroGitTape(pid, data_dir=data_dir)
    gt.init()

    async def drive():
        app = TuiApp(project_id=pid, data_dir=data_dir, force_mock_facilitator=True)
        async with app.run_test(size=(122, 30)) as pilot:
            await pilot.pause(0.2)
            assert app.has_class("focus")
            await pilot.resize_terminal(287, 66)
            await pilot.pause(0.8)
            assert app.has_class("wide")
            assert not app.has_class("focus")

    asyncio.run(drive())


def test_evidence_pane_uses_compact_summary(data_dir):
    os.environ["TURINGOS_DATA_DIR"] = str(data_dir)
    pid = "evidence_summary"
    gt = MicroGitTape(pid, data_dir=data_dir)
    gt.init()
    wtool_append(pid, make_event(SYSTEM_BOOTSTRAPPED, {"boot": "test"}), data_dir=data_dir)
    wtool_append(pid, make_event(PROJECT_READY, {"name": pid}), data_dir=data_dir)

    async def drive():
        app = TuiApp(project_id=pid, data_dir=data_dir, force_mock_facilitator=True)
        async with app.run_test(size=(287, 66)) as pilot:
            await pilot.pause(0.2)
            app.refresh_projection()
            evidence = str(app.query_one("#evidence-pane #evidence-log").content)
            assert "Project:" in evidence
            assert "Status:" in evidence
            assert "Micro events" in evidence
            assert "README:" not in evidence

    asyncio.run(drive())
