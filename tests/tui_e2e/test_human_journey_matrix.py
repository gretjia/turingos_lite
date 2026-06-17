"""
Strict human journey matrix — full UX coverage, zero source bypass.

Each test simulates a real user: scroll, click MCQ, type keys, click Send/Approve.
Fails loudly when UX blocks humans (off-screen buttons, silent no-ops, missing panels).
"""
from __future__ import annotations

import os

import pytest

from turingos.micro.rtool import MicroRtool
from tests.tui_e2e.human_simulator import (
    HumanDriver,
    boot_project,
    run_human_journey,
    TERMINAL_SIZES,
)
from tests.tui_e2e.journey_matrix import (
    BOOT_MCQS,
    CONFIG_MENU_MCQS,
    DEEPSEEK_TOKEN_MSG,
    NVIDIA_PASTE_SHORT,
    PROJECT_QUESTION,
    WORKER_API_MCQ_IDS,
    WORKER_BUNDLE_MCQS,
)


@pytest.fixture
def human_data(tmp_path):
    d = tmp_path / "human_e2e"
    d.mkdir()
    os.environ["TURINGOS_DATA_DIR"] = str(d)
    return d


# ── Boot & main flow ─────────────────────────────────────────────────────────

def test_human_j01_boot_cognition(human_data):
    async def journey(h: HumanDriver):
        h.assert_turn_contains("项目认知")
        for cid in ("explore", "task", "ai_setup"):
            h.assert_mcq_present(cid)

    run_human_journey(journey, human_data, "hj01")


def test_human_j02_project_question_chat(human_data):
    async def journey(h: HumanDriver):
        await h.type_and_send(PROJECT_QUESTION)
        h.assert_turn_type("chat")
        thread = h.app.query_one("#center-pane #chat-thread")
        assert len(thread.children) >= 2, h.journal.dump()

    run_human_journey(journey, human_data, "hj02")


def test_human_j03_deepseek_paste_auto_setup(human_data):
    async def journey(h: HumanDriver):
        await h.type_and_send(DEEPSEEK_TOKEN_MSG)
        h.assert_turn_type("chat")
        assert "DeepSeek" in h.app.facilitator_turn.get("summary", "")
        assert h.app.facilitator_turn.get("setup_result", {}).get("provider") == "deepseek"

    run_human_journey(journey, human_data, "hj03")


def test_human_j04_explore_submit_approve_enrich(human_data):
    async def journey(h: HumanDriver):
        await h.click_mcq("explore")
        await h.click_mcq("submit")
        h.assert_turn_type("propose")
        await h.click_approve()
        h.assert_turn_type("enrich")
        await h.click_mcq("skip")
        h.assert_turn_contains("项目认知")

    pre = MicroRtool("hj04", data_dir=human_data).read_tip()
    run_human_journey(journey, human_data, "hj04")
    assert MicroRtool("hj04", data_dir=human_data).read_tip() != pre


# ── Config menu (all 3 entries) ──────────────────────────────────────────────

@pytest.mark.parametrize("entry_id", CONFIG_MENU_MCQS)
def test_human_j10_config_menu_entry(human_data, entry_id: str):
    async def journey(h: HumanDriver):
        await h.click_mcq("ai_setup")
        h.assert_turn_contains("配置")
        await h.click_mcq(entry_id)
        if entry_id == "skill_worker":
            h.assert_mcq_present("worker_api_deepseek")
        elif entry_id == "skill_nvidia":
            h.assert_turn_contains("Facilitator")
        else:
            h.assert_turn_contains("Meta AI")

    run_human_journey(journey, human_data, f"hj10_{entry_id}")


# ── Meta AI wizard (human clicks only) ───────────────────────────────────────

def test_human_j11_meta_wizard_preset_path(human_data):
    async def journey(h: HumanDriver):
        await h.click_mcq("ai_setup")
        await h.click_mcq("skill_openai")
        await h.click_mcq("preset_openai")
        h.assert_turn_contains("步骤 2/3")

    run_human_journey(journey, human_data, "hj11")


def test_human_j12_meta_api_key_panel_via_click(human_data):
    """Regression: cfg_input_key must open visible panel without post_message."""
    async def journey(h: HumanDriver):
        await h.click_mcq("ai_setup")
        await h.click_mcq("skill_openai")
        await h.click_mcq("preset_openai")
        await h.click_mcq("cfg_input_key")
        h.assert_panel_visible()

    run_human_journey(journey, human_data, "hj12")


# ── Facilitator NVIDIA wizard ──────────────────────────────────────────────────

def test_human_j13_facilitator_nvidia_preset(human_data):
    async def journey(h: HumanDriver):
        await h.click_mcq("ai_setup")
        await h.click_mcq("skill_nvidia")
        await h.click_mcq("preset_nvidia_fac")
        h.assert_turn_contains("步骤 2/3")

    run_human_journey(journey, human_data, "hj13")


def test_human_j14_nvidia_paste_in_composer(human_data):
    async def journey(h: HumanDriver):
        await h.type_and_send(NVIDIA_PASTE_SHORT)
        h.assert_turn_type("chat")
        assert "NVIDIA" in h.app.facilitator_turn.get("summary", "")

    run_human_journey(journey, human_data, "hj14")


# ── Worker picker: every API provider + bundles ───────────────────────────────

@pytest.mark.parametrize("worker_id", WORKER_API_MCQ_IDS)
def test_human_j20_worker_api_provider_clickable(human_data, worker_id: str):
    async def journey(h: HumanDriver):
        await h.click_mcq("ai_setup")
        await h.click_mcq("skill_worker")
        h.assert_turn_contains("Worker")
        await h.click_mcq(worker_id)
        h.assert_turn_contains("步骤 1/3")

    run_human_journey(journey, human_data, f"hj20_{worker_id}")


@pytest.mark.parametrize("bundle_id", WORKER_BUNDLE_MCQS)
def test_human_j21_worker_bundle_docs(human_data, bundle_id: str):
    async def journey(h: HumanDriver):
        await h.click_mcq("ai_setup")
        await h.click_mcq("skill_worker")
        await h.click_mcq(bundle_id)
        h.assert_turn_contains("Worker")

    run_human_journey(journey, human_data, f"hj21_{bundle_id}")


def test_human_j22_worker_deepseek_full_wizard(human_data):
    async def journey(h: HumanDriver):
        await h.click_mcq("ai_setup")
        await h.click_mcq("skill_worker")
        await h.click_mcq("worker_api_deepseek")
        await h.click_mcq("preset_deepseek_deepseek-chat")
        await h.click_mcq("cfg_input_key")
        h.assert_panel_visible()
        await h.fill_config_and_save("sk-test123456789012345678901234")
        h.assert_turn_contains("步骤 3/3")
        await h.click_mcq("cfg_input_model")
        h.assert_panel_visible()
        await h.fill_config_and_save("deepseek-chat")
        await h.click_mcq("cfg_save")
        h.assert_turn_contains("Worker API 已保存")

    run_human_journey(journey, human_data, "hj22")


# ── Small terminal (SSH 80x24) — catches off-screen UX bugs ───────────────────

@pytest.mark.parametrize("size", [(80, 24), (120, 40)])
def test_human_j30_small_terminal_worker_list(human_data, size):
    """On a narrow SSH session, human must still reach Worker API options."""
    async def journey(h: HumanDriver):
        await h.click_mcq("ai_setup")
        await h.click_mcq("skill_worker")
        h.assert_mcq_present("worker_api_custom")
        await h.click_mcq("worker_api_deepseek")
        h.assert_turn_contains("步骤")

    boot_project(f"hj30_{size[0]}x{size[1]}", human_data)
    import asyncio
    from turingos.tui.app import TuiApp

    async def run():
        app = TuiApp(
            project_id=f"hj30_{size[0]}x{size[1]}",
            data_dir=human_data,
            force_mock_facilitator=True,
        )
        async with app.run_test(size=size) as pilot:
            h = HumanDriver(app, pilot)
            await h.wait_idle()
            await journey(h)

    asyncio.run(run())


# ── Guard: no bypass in human test sources ────────────────────────────────────

def test_human_simulator_source_has_no_bypass():
    """Meta-test: human journey files must not cheat."""
    import ast
    import pathlib

    root = pathlib.Path(__file__).parent
    forbidden_calls = {"post_message", "_facilitator_run", "_approve_proposals"}
    forbidden_attrs = {"value", "text"}
    targets = list(root.glob("test_human*.py"))
    violations: list[str] = []

    class BypassVisitor(ast.NodeVisitor):
        def __init__(self, fname: str) -> None:
            self.fname = fname

        def visit_Call(self, node: ast.Call) -> None:
            if isinstance(node.func, ast.Name) and node.func.id in forbidden_calls:
                violations.append(f"{self.fname}:{node.lineno}: calls {node.func.id}()")
            elif isinstance(node.func, ast.Attribute) and node.func.attr in forbidden_calls:
                violations.append(
                    f"{self.fname}:{node.lineno}: calls .{node.func.attr}()"
                )
            self.generic_visit(node)

        def visit_Assign(self, node: ast.Assign) -> None:
            if isinstance(node.value, ast.Constant):
                self.generic_visit(node)
                return
            for target in node.targets:
                if isinstance(target, ast.Attribute) and target.attr in forbidden_attrs:
                    violations.append(
                        f"{self.fname}:{node.lineno}: assigns .{target.attr}"
                    )
            self.generic_visit(node)

    for path in targets:
        tree = ast.parse(path.read_text())
        BypassVisitor(path.name).visit(tree)

    assert not violations, "Human sim bypass detected:\n" + "\n".join(violations)