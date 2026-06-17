"""Provider auto-setup skill tests."""
from turingos.facilitator.provider_setup import (
    auto_setup_turn,
    detect_provider_id,
    extract_api_token,
    is_project_question,
    is_provider_paste,
    parse_provider_paste,
)
from turingos.facilitator.facilitate import facilitate_turn

NVIDIA_SAMPLE = '''
invoke_url = "https://integrate.api.nvidia.com/v1/chat/completions"
headers = {
"Authorization": "Bearer nvapi-test1234567890abcdefghijklmnop",
}
payload = {
"model": "google/diffusiongemma-26b-a4b-it",
"max_tokens": 4096,
"temperature": 1.00,
"top_p": 0.95,
"chat_template_kwargs": {"enable_thinking":True},
}
response = requests.post(invoke_url, headers=headers, json=payload)
'''


def test_detect_deepseek_token():
    t = "deepseek api sk-abc123456789012345678901234"
    assert extract_api_token(t)
    assert detect_provider_id(t) == "deepseek"


def test_parse_nvidia_paste():
    parsed = parse_provider_paste(NVIDIA_SAMPLE)
    assert parsed["parsed"]
    assert parsed["provider_id"] == "nvidia"
    assert parsed["api_key"].startswith("nvapi-")
    assert parsed["base_url"] == "https://integrate.api.nvidia.com/v1"
    assert parsed["model"] == "google/diffusiongemma-26b-a4b-it"
    assert parsed["thinking"] is True
    assert parsed["temperature"] == 1.0
    assert parsed["top_p"] == 0.95
    assert parsed["max_tokens"] == 4096


def test_is_provider_paste_nvidia_code():
    assert is_provider_paste(NVIDIA_SAMPLE)


def test_auto_setup_turn_mock():
    turn = auto_setup_turn(
        "我从 deepseek 官网取得了 api: sk-test123456789012345678901234",
        force_mock_test=True,
    )
    assert turn
    assert turn["turn_type"] == "chat"
    assert turn["setup_result"]["provider"] == "deepseek"
    assert turn["setup_result"]["ok"]


def test_auto_setup_nvidia_paste_mock():
    turn = auto_setup_turn(NVIDIA_SAMPLE, role="facilitator", force_mock_test=True)
    assert turn
    assert turn["turn_type"] == "chat"
    assert turn["setup_result"]["provider"] == "nvidia"
    assert turn["setup_result"]["ok"]
    assert "diffusiongemma" in turn["summary"]
    assert "Thinking" in turn["summary"] or "开启" in turn["summary"]
    assert "继续项目流程" in turn["summary"]


def test_project_question_via_facilitate():
    turn = facilitate_turn(
        user_text="这个项目的 git 历史是什么？",
        project_brief={"project_id": "p", "has_git": True},
        force_mock=True,
    )
    assert turn["turn_type"] == "chat"
    assert "项目认知" in turn["summary"]


def test_nvidia_paste_via_facilitate_in_wizard():
    draft = {
        "target_id": "skill_nvidia",
        "kind": "facilitator",
        "title": "Facilitator",
        "step": "api_key",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "model": "google/diffusiongemma-26b-a4b-it",
        "api_key": None,
    }
    turn = facilitate_turn(
        user_text=NVIDIA_SAMPLE,
        config_draft=draft,
        selected_choice_id="cfg_input",
        select_action="config_input",
        force_mock=True,
    )
    assert turn["turn_type"] == "chat"
    assert turn["setup_result"]["ok"]


def test_not_project_question_short():
    assert not is_project_question("hi")