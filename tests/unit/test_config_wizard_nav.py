"""Config wizard + turn history navigation."""
import asyncio
import os

import pytest

from turingos.facilitator.config_wizard import run_config_wizard
from turingos.tui.app import TuiApp


@pytest.fixture
def data_dir(tmp_path):
    d = tmp_path / "cfg_nav"
    d.mkdir()
    return d


def test_worker_picker_includes_api_providers():
    turn, draft = run_config_wizard(selected_choice_id="skill_worker")
    assert draft is None
    ids = {c["id"] for c in turn["choices"]}
    assert "worker_api_deepseek" in ids
    assert "worker_api_nvidia" in ids
    assert "worker_api_openai" in ids
    assert "worker_api_custom" in ids
    assert "worker_codex" in ids


def test_worker_api_deepseek_starts_wizard():
    turn, draft = run_config_wizard(selected_choice_id="worker_api_deepseek")
    assert draft is not None
    assert draft["kind"] == "worker"
    assert draft["step"] == "base_url"
    assert "deepseek" in draft["base_url"].lower()


def test_bearer_token_in_base_url_step_goes_to_api_key():
    """Regression: pasting Bearer nvapi- in URL step must not corrupt base_url."""
    turn, draft = run_config_wizard(selected_choice_id="worker_api_custom")
    assert draft and draft["step"] == "base_url"
    token = "Bearer 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"
    turn2, draft2 = run_config_wizard(
        config_draft=draft,
        select_action="config_input",
        user_text=token,
        choice={"config_field": "base_url"},
    )
    assert draft2["step"] == "model"
    assert draft2["base_url"].startswith("https://")
    assert draft2["api_key"].startswith("nvapi-")
    assert "Bearer" not in draft2["base_url"]
    assert "步骤 3/3" in turn2["summary"]


def test_cfg_save_worker_shows_connectivity_success():
    draft = {
        "target_id": "worker_api_deepseek",
        "kind": "worker",
        "title": "Worker API — DeepSeek",
        "skill_id": "setup-worker-api-openai",
        "provider_id": "deepseek",
        "step": "confirm",
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "api_key": "sk-test123456789012345678901234",
    }
    turn, out = run_config_wizard(
        config_draft=draft,
        selected_choice_id="cfg_save",
        select_action="cfg_save",
    )
    assert out is None
    assert turn["turn_type"] == "chat"
    assert "已保存并测试通过" in turn["summary"]
    assert turn["setup_result"]["ok"]
    assert "继续项目流程" in turn["choices"][0]["label"]


def test_meta_wizard_step_flow():
    turn, draft = run_config_wizard(selected_choice_id="skill_openai")
    assert draft and draft["step"] == "base_url"
    assert "API Key" not in turn["summary"] or "步骤 1" in turn["summary"]

    draft_key = {**draft, "step": "api_key"}
    _, draft2 = run_config_wizard(
        config_draft=draft_key,
        select_action="config_input",
        user_text="sk-test-12345678",
        choice={"config_field": "api_key"},
    )
    assert draft2["api_key"] == "sk-test-12345678"
    assert draft2["step"] == "model"


def test_turn_history_back_forward(data_dir):
    os.environ["TURINGOS_DATA_DIR"] = str(data_dir)

    async def drive():
        app = TuiApp(project_id="nav_test", data_dir=data_dir, force_mock_facilitator=True)
        async with app.run_test() as pilot:
            async with app._facilitator_lock:
                pass
            await app._facilitator_run(selected_choice_id="ai_setup")
            assert app.facilitator_turn.get("wizard_mode")
            first_summary = app.facilitator_turn.get("summary", "")
            await app._facilitator_run(selected_choice_id="skill_openai", choice={})
            second_summary = app.facilitator_turn.get("summary", "")
            assert "步骤 1/3" in second_summary
            assert len(app.turn_history) >= 2
            app._navigate_turn_history(-1)
            assert app.facilitator_turn.get("summary") == first_summary
            app._navigate_turn_history(1)
            assert app.facilitator_turn.get("summary") == second_summary

    asyncio.run(drive())