"""Facilitator v2: MCQ, other freeform, project brief, simulated user journeys."""
import asyncio
import os

import pytest

from turingos.events import make_event, SYSTEM_BOOTSTRAPPED, PROJECT_READY
from turingos.facilitator.config_wizard import run_config_wizard
from turingos.facilitator.facilitate import (
    continue_after_skip_turn,
    facilitate_turn,
    mock_enrich_turn,
)
from turingos.facilitator.project_brief import build_project_brief, format_project_cognition
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
    assert "项目认知" in turn["summary"]
    ids = {c["id"] for c in turn["choices"]}
    assert "submit" in ids and "other" in ids


def test_skip_continue_not_silent(data_dir):
    brief = build_project_brief("omega-wiki", data_dir=data_dir)
    turn = continue_after_skip_turn(brief, session_turns=[])
    assert turn["turn_type"] == "clarify"
    assert "项目认知" in turn["summary"]
    assert "submit" in {c["id"] for c in turn["choices"]}
    assert format_project_cognition(brief) in turn["summary"]


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
        from turingos.tui.widgets import VibeComposerPane

        app = TuiApp(project_id=pid, data_dir=data_dir, force_mock_facilitator=True)
        async with app.run_test() as pilot:
            async with app._facilitator_lock:
                pass
            composer = app.query_one("#center-pane", VibeComposerPane)
            for _ in range(60):
                if composer._choices_ready:
                    break
                await pilot.pause(0.05)

            assert app.facilitator_turn.get("turn_type") == "clarify"
            assert "other" in {c["id"] for c in app.facilitator_turn.get("choices", [])}

            inp = app.query_one("#center-pane #vibe-input")
            inp.value = (
                "existing project with GitHub and Macro Git — learn history first"
            )
            await pilot.click("#transcribe-btn")
            async with app._facilitator_lock:
                pass
            await pilot.pause(0.3)
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

            app._approve_proposals()
            await pilot.pause(0.5)
            assert app.facilitator_turn.get("turn_type") == "enrich"

            await app._facilitator_run(selected_choice_id="skip", select_action="skip")
            await pilot.pause(0.3)
            assert app.facilitator_turn["turn_type"] == "clarify"
            assert "项目认知" in app.facilitator_turn.get("summary", "")
            assert "submit" in {c["id"] for c in app.facilitator_turn.get("choices", [])}
            await pilot.press("q")
            await pilot.pause()

    asyncio.run(drive())
    assert r.read_tip() != pre


def test_config_meta_ai_wizard_steps(data_dir):
    """配置 Meta AI 应进入分步向导，而非跳到无关问答题。"""
    turn, draft = run_config_wizard(selected_choice_id="skill_openai")
    assert draft is not None
    assert draft["step"] == "base_url"
    assert "步骤 1/3" in turn["summary"]
    assert turn.get("wizard_mode")

    draft_key = {**draft, "step": "api_key"}
    _turn2, draft2 = run_config_wizard(
        config_draft=draft_key,
        select_action="config_input",
        user_text="sk-test-key-12345",
        choice={"config_field": "api_key"},
    )
    assert draft2["api_key"] == "sk-test-key-12345"
    assert draft2["step"] == "model"


def test_config_menu_from_facilitate(data_dir):
    turn = facilitate_turn(
        selected_choice_id="ai_setup",
        project_brief={"project_id": "p"},
        force_mock=True,
    )
    assert turn.get("wizard_mode")
    assert any(c["id"] == "skill_openai" for c in turn["choices"])


def test_nav_choices_prepended():
    from turingos.facilitator.schema import append_nav_choices

    out = append_nav_choices([{"id": "a", "label": "A"}], can_back=True, can_forward=True)
    ids = [c["id"] for c in out]
    assert ids[0] == "nav_back"
    assert ids[1] == "nav_forward"
    assert "a" in ids


def test_project_brief_fields(data_dir):
    os.environ["TURINGOS_DATA_DIR"] = str(data_dir)
    brief = build_project_brief("turingoslite", data_dir=data_dir)
    assert "project_id" in brief
    assert "config_status" in brief
    assert "has_git" in brief