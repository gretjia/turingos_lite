"""Facilitator Software 3.0 agent: detect, propose code, whitebox tools."""
import os
from pathlib import Path

import pytest

from turingos.facilitator.agent import (
    agent_proposals_for_code,
    build_tool_plan,
    is_code_task,
    try_agent_turn,
)
from turingos.facilitator.facilitate import facilitate_turn
from turingos.facilitator.project_brief import build_project_brief
from turingos.tools.whitebox import WhiteboxScope, write_file
from turingos.workers.registry import get_worker


@pytest.fixture
def data_dir(tmp_path):
    d = tmp_path / "agent"
    d.mkdir()
    return d


def test_is_code_task_detects_chinese():
    assert is_code_task("帮我在 turingos/cli.py 里添加一个日志")
    assert not is_code_task("这个项目 README 讲了什么")


def test_agent_propose_code_task(data_dir):
    os.environ["TURINGOS_DATA_DIR"] = str(data_dir)
    brief = build_project_brief("p1", cwd=Path(__file__).resolve().parents[2], data_dir=data_dir)
    turn = try_agent_turn(
        user_text="修复 turingos/cli.py 的 help 文本",
        project_brief=brief,
        force_mock=True,
    )
    assert turn
    assert turn["turn_type"] == "propose"
    props = turn["proposals"]
    assert any(p["event_type"] == "WorkCapsuleBuilt" for p in props)
    cap = next(p for p in props if p["event_type"] == "WorkCapsuleBuilt")
    assert cap["payload"].get("auto_execute")
    assert cap["payload"].get("tool_plan")


def test_api_worker_writes_file(data_dir, tmp_path):
    os.environ["TURINGOS_DATA_DIR"] = str(data_dir)
    root = tmp_path / "repo"
    root.mkdir()
    (root / "demo.py").write_text("x = 1\n")
    plan = build_tool_plan("append marker to demo.py", {"cwd": str(root)})
    w = get_worker("api")
    rec = w.run(
        "p1",
        "wc_test",
        tool_plan=plan,
        macro_root=str(root),
        data_dir=data_dir,
    )
    assert rec["tools_executed"] >= 1
    assert "TuringOS agent" in (root / "demo.py").read_text()


def test_whitebox_scope_blocks_escape(tmp_path):
    scope = WhiteboxScope(tmp_path)
    with pytest.raises(PermissionError):
        write_file(scope, "../../etc/passwd", "x")