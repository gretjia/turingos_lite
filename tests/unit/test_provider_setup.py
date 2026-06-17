"""Provider auto-setup skill tests."""
from turingos.facilitator.provider_setup import (
    auto_setup_turn,
    detect_provider_id,
    extract_api_token,
    is_project_question,
)
from turingos.facilitator.facilitate import facilitate_turn


def test_detect_deepseek_token():
    t = "deepseek api sk-abc123456789012345678901234"
    assert extract_api_token(t)
    assert detect_provider_id(t) == "deepseek"


def test_auto_setup_turn_mock():
    turn = auto_setup_turn(
        "我从 deepseek 官网取得了 api: sk-test123456789012345678901234",
        force_mock_test=True,
    )
    assert turn
    assert turn["turn_type"] == "chat"
    assert turn["setup_result"]["provider"] == "deepseek"
    assert turn["setup_result"]["ok"]


def test_project_question_via_facilitate():
    turn = facilitate_turn(
        user_text="这个项目的 git 历史是什么？",
        project_brief={"project_id": "p", "has_git": True},
        force_mock=True,
    )
    assert turn["turn_type"] == "chat"
    assert "项目认知" in turn["summary"]


def test_not_project_question_short():
    assert not is_project_question("hi")