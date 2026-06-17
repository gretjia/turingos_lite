"""Facilitator v2: MCQ, other freeform, project brief, simulated user journeys."""
import asyncio
import os

import pytest

from turingos.events import make_event, SYSTEM_BOOTSTRAPPED, PROJECT_READY
from turingos.facilitator.facilitate import facilitate_turn, mock_enrich_turn
from turingos.facilitator.project_brief import build_project_brief
from turingos.facilitator.schema import OTHER_CHOICE, SUBMIT_CHOICE, ensure_standard_choices
from turingos.micro.git_tape import MicroGitTape
from turingos.micro.rtool import MicroRtool
from turingos.micro.wtool import append as wtool_append
from turingos.tui.app import TuiApp


@pytest.fixture
def data_dir(tmp_path):
    d = tmp_path / "fac_v2"
    d.mkdir()
    return d


def test_choices_always_include_submit_and_other():
    choices = [{"id": "a", "label": "A"}]
    out = ensure_standard_choices(choices)
    ids = [c["id"] for c in out]
    assert "submit" in ids
    assert "other" in ids
    assert out[-1]["id"] == "other"
    assert OTHER_CHOICE["input_prompt"] in str(out[-1].get("input_prompt", ""))


def test_boot_turn_clarify(data_dir):
    os.environ["TURINGOS_DATA_DIR"] = str(data_dir)
    brief = build_project_brief("p1", data_dir=data_dir)
    turn = facilitate_turn(boot=True, project_brief=brief, force_mock=True)
    assert turn["turn_type"] == "clarify"
    assert turn["summary"]
    ids = {c["id"] for c in turn["choices"]}
    assert "submit" in ids and "other" in ids


def test_existing_project_user_message_clarify(data_dir):
    msg = (
        "This is an already existed project. It has GitHub and local Macro Git. "
        "Learn project history and macro structure. Let me know when ready."
    )
    brief = {"project_id": "turingoslite", "has_git": True}
    turn = facilitate_turn(user_text=msg, project_brief=brief, force_mock=True)
    assert turn["turn_type"] == "clarify"
    assert "other" in {c["id"] for c in turn["choices"]}


def test_submit_produces_proposals(data_dir):
    brief = {"project_id": "p", "has_git": True, "macro_head": "macro:git:p:abc"}
    turn = facilitate_turn(
        user_text="explore project",
        selected_choice_id="submit",
        select_action="propose",
        project_brief=brief,
        force_mock=True,
    )
    assert turn["turn_type"] == "propose"
    assert len(turn["proposals"]) >= 1
    types = {p["event_type"] for p in turn["proposals"]}
    assert "IntentCaptured" in types


def test_other_freeform_then_clarify(data_dir):
    turn = facilitate_turn(
        user_text="I also need OAuth support",
        selected_choice_id="other",
        select_action="freeform",
        project_brief={"project_id": "p"},
        force_mock=True,
    )
    assert turn["turn_type"] == "clarify"
    assert "OAuth" in turn["summary"] or "补充" in turn["summary"]


def test_enrich_after_approve():
    turn = mock_enrich_turn("μ:abc123")
    assert turn["turn_type"] == "enrich"
    assert any(c["id"] == "url" for c in turn["choices"])
    assert any(c["id"] == "other" for c in turn["choices"])


def test_simulated_user_full_flow_tui(data_dir):
    """Simulate: boot MCQ → existing project text → explore → submit → approve → enrich skip."""
    os.environ["TURINGOS_DATA_DIR"] = str(data_dir)
    pid = "sim_user"
    gt = MicroGitTape(pid, data_dir=data_dir)
    gt.init()
    wtool_append(pid, make_event(SYSTEM_BOOTSTRAPPED, {"b": 1}), data_dir=data_dir)
    wtool_append(pid, make_event(PROJECT_READY, {"n": pid}), data_dir=data_dir)
    r = MicroRtool(pid, data_dir=data_dir)
    pre = r.read_tip()

    async def drive():
        app = TuiApp(project_id=pid, data_dir=data_dir, force_mock_facilitator=True)
        async with app.run_test() as pilot:
            await pilot.pause(1.0)
            assert app.facilitator_turn.get("turn_type") == "clarify"
            assert "other" in {c["id"] for c in app.facilitator_turn.get("choices", [])}

            inp = app.query_one("#center-pane #vibe-input")
            inp.value = (
                "existing project with GitHub and Macro Git — learn history first"
            )
            await pilot.click("#transcribe-btn")
            await pilot.pause(0.8)
            assert app.facilitator_turn["turn_type"] == "clarify"

            await app._facilitator_run(selected_choice_id="explore")
            assert app.facilitator_turn["turn_type"] == "clarify"

            await app._facilitator_run(
                selected_choice_id="submit",
                select_action="propose",
                user_text=inp.value,
            )
            assert app.facilitator_turn["turn_type"] == "propose"
            assert app.pending_proposals

            await pilot.press("A")
            await pilot.pause(0.5)
            assert app.facilitator_turn.get("turn_type") == "enrich"

            await app._facilitator_run(selected_choice_id="skip", select_action="skip")
            await pilot.pause(0.3)
            await pilot.press("q")
            await pilot.pause()

    asyncio.run(drive())
    assert r.read_tip() != pre


def test_project_brief_fields(data_dir):
    os.environ["TURINGOS_DATA_DIR"] = str(data_dir)
    brief = build_project_brief("turingoslite", data_dir=data_dir)
    assert "project_id" in brief
    assert "config_status" in brief
    assert "has_git" in brief