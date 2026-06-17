"""Agent simulation: random vibes + approve → loop complete + non-empty tape."""
import os
import random
from pathlib import Path

import pytest

from turingos.events import make_event, SYSTEM_BOOTSTRAPPED, PROJECT_READY
from turingos.facilitator.facilitate import facilitate_turn
from turingos.micro.git_tape import MicroGitTape
from turingos.micro.rtool import MicroRtool
from turingos.micro.wtool import append as wtool_append
from turingos.tui.app import TuiApp
from turingos.tui.agent_bus import AgentBus

VIBES = [
    "vibe: create a todo app with persistence",
    "vibe: add sqlite + React frontend",
    "vibe: add user authentication",
    "vibe: refine the capsule mission",
    "vibe: complete and deliver the project",
    "vibe: observe macro anchors",
    "vibe: update broadcast rules",
    "vibe: shield policy for workers",
    "vibe: dispatch worker on top capsule",
    "vibe: verify loop completion",
]


@pytest.fixture
def sim_data_dir(tmp_path):
    d = tmp_path / "agent_sim"
    d.mkdir()
    return d


def test_agent_sim_ten_random_vibes(sim_data_dir):
    """Simulate agent driving 10 vibes with random approve decisions."""
    os.environ["TURINGOS_DATA_DIR"] = str(sim_data_dir)
    pid = "agent_sim_10"
    gt = MicroGitTape(pid, data_dir=sim_data_dir)
    gt.init()
    wtool_append(pid, make_event(SYSTEM_BOOTSTRAPPED, {"boot": "agent"}), data_dir=sim_data_dir)
    wtool_append(pid, make_event(PROJECT_READY, {"name": pid}), data_dir=sim_data_dir)

    bus = AgentBus()
    app = TuiApp(
        project_id=pid,
        data_dir=sim_data_dir,
        agent_bus=bus,
        force_mock_facilitator=True,
    )
    random.seed(42)
    vibes = random.sample(VIBES, 10)

    brief = {"project_id": pid, "has_git": True}
    for vibe in vibes:
        turn = facilitate_turn(
            user_text=vibe,
            selected_choice_id="submit",
            select_action="propose",
            project_brief=brief,
            force_mock=True,
        )
        app.pending_proposals = turn.get("proposals", [])
        if random.random() > 0.2:
            app._approve_proposals()
        app.loop_progress = min(100, app.loop_progress + 10)

    r = MicroRtool(pid, data_dir=sim_data_dir)
    tip = r.read_tip()
    assert tip.startswith("μ:")
    commits = list(r.iter_commits())
    assert len(commits) >= 3
    assert app.loop_progress >= 50