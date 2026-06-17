"""Provider auto-setup skill tests."""
import sys
from types import SimpleNamespace

from turingos.facilitator.provider_setup import (
    apply_provider_config,
    auto_setup_turn,
    detect_provider_id,
    extract_api_token,
    is_project_question,
    is_provider_paste,
    parse_provider_paste,
    test_openai_compatible as probe_openai_compatible,
)
from turingos.facilitator.facilitate import facilitate_turn

DEEPSEEK_V4_SAMPLE = '''
client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=[{"role": "user", "content": "pong"}],
    extra_body={"thinking": {"type": "disabled"}},
)
base_url = "https://api.deepseek.com/chat/completions"
Authorization: Bearer sk-test123456789012345678901234
'''

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


def test_parse_deepseek_v4_thinking_paste():
    parsed = parse_provider_paste(DEEPSEEK_V4_SAMPLE)
    assert parsed["parsed"]
    assert parsed["provider_id"] == "deepseek"
    assert parsed["base_url"] == "https://api.deepseek.com"
    assert parsed["model"] == "deepseek-v4-flash"
    assert parsed["thinking"] is False
    assert parsed["extra_body"] == {"thinking": {"type": "disabled"}}


def test_apply_deepseek_v4_thinking_modes(monkeypatch):
    saved = {}

    def save_meta_config(**kw):
        saved["meta"] = kw

    def load_meta_config():
        return {
            "base_url": saved["meta"]["base_url"],
            "model": saved["meta"]["model"],
            "api_key": "stored",
            "extra_body": saved["meta"].get("extra_body"),
        }

    monkeypatch.setattr(
        "turingos.facilitator.provider_setup.save_meta_config",
        save_meta_config,
    )
    monkeypatch.setattr(
        "turingos.facilitator.provider_setup.load_meta_config",
        load_meta_config,
    )

    cfg = apply_provider_config(
        "deepseek",
        "sk-test123456789012345678901234",
        model="deepseek-v4-pro",
        thinking=True,
    )
    assert cfg["model"] == "deepseek-v4-pro"
    assert cfg["extra_body"] == {"thinking": {"type": "enabled"}}

    cfg = apply_provider_config(
        "deepseek",
        "sk-test123456789012345678901234",
        model="deepseek-v4-flash",
        thinking=False,
    )
    assert cfg["model"] == "deepseek-v4-flash"
    assert cfg["extra_body"] == {"thinking": {"type": "disabled"}}


def test_thinking_probe_allocates_reasoning_budget(monkeypatch):
    calls = []

    class FakeCompletions:
        def create(self, **kwargs):
            calls.append(kwargs)
            msg = SimpleNamespace(content="pong", reasoning_content="checked")
            choice = SimpleNamespace(message=msg)
            return SimpleNamespace(choices=[choice])

    class FakeOpenAI:
        def __init__(self, **_kwargs):
            self.chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=FakeOpenAI))
    res = probe_openai_compatible({
        "base_url": "https://api.deepseek.com",
        "api_key": "sk-test123456789012345678901234",
        "model": "deepseek-v4-pro",
        "extra_body": {"thinking": {"type": "enabled"}},
    })

    assert res["ok"]
    assert res["has_reasoning"]
    assert calls[0]["max_tokens"] == 256
    assert calls[0]["extra_body"] == {"thinking": {"type": "enabled"}}


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
    assert turn["turn_type"] == "clarify"
    assert "确认保存" in turn.get("summary", "")
    assert turn.get("config_draft", {}).get("api_key", "").startswith("nvapi-")


def test_not_project_question_short():
    assert not is_project_question("hi")


def test_wizard_api_key_not_hijacked_by_auto_setup():
    """Regression: typing sk- in wizard config field must stay in wizard."""
    draft = {
        "target_id": "worker_api_deepseek",
        "kind": "worker",
        "title": "Worker API — DeepSeek",
        "skill_id": "setup-worker-api-openai",
        "step": "api_key",
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "api_key": None,
    }
    turn = facilitate_turn(
        user_text="sk-test123456789012345678901234",
        config_draft=draft,
        selected_choice_id="cfg_input",
        select_action="config_input",
        force_mock=True,
    )
    assert turn.get("turn_type") == "clarify"
    assert "步骤" in turn.get("summary", "")
    assert turn.get("setup_result") is None
