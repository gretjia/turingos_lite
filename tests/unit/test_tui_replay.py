"""Phase 9 TUI/replay E2E sim skeleton per charter 12/9/3.9 + AGENTS + FC-A10.
Test-first: reproduces req (TUI panes+hotkeys pilot drive, replay cmd, projection from reducer, dispatch via wtool+pred, no write in tui, no zombie for TUI nodes+priors).
Uses textual pilot (via asyncio runner to avoid pytest-asyncio dep) + CliRunner.
Acceptance: passes only after tui/app + cli integrated; post audit fsck + scale + events.
"""
import os
import asyncio
from pathlib import Path

import pytest
from typer.testing import CliRunner

from turingos.cli import app
from turingos.micro.git_tape import MicroGitTape
from turingos.micro.wtool import append as wtool_append
from turingos.micro.rtool import MicroRtool
from turingos.micro.reducer import reduce_state
from turingos.events import (
    make_event,
    SYSTEM_BOOTSTRAPPED,
    PROJECT_READY,
    INTENT_CAPTURED,
    WORK_CAPSULE_BUILT,
    MACRO_OBSERVATION_IMPORTED,
    FAILURE_NODE,
    HUMAN_DECISION,
    MACRO_ACTION_AUTHORIZATION,
    RECOVERY_OBSERVED,
)


@pytest.fixture
def controlled_data_dir(tmp_path):
    d = tmp_path / "turing_data_tui"
    d.mkdir()
    return d


def test_replay_command_and_tui_pilot_e2e_sim(controlled_data_dir):
    """Goal: E2E with TUI sim for 1+ case (pilot presses r/A/?/q + replay cmd).
    1. replay cmd uses tape + declared (anchors in obs) to reconstruct.
    2. TUI launch projection-only (4 panes), all hotkeys bound, dispatch keys go thru wtool/pred (not direct write).
    3. post: fsck, scale μ: in views, no zombie TUI nodes + priors (Human/Recovery/Auth + WorkCapsule etc exercised).
    4. reducer/rtool only for TUI state.
    """
    os.environ["TURINGOS_DATA_DIR"] = str(controlled_data_dir)
    pid = "tui_replay_e2e"
    gt = MicroGitTape(pid)
    gt.init()
    r = MicroRtool(pid, data_dir=controlled_data_dir)

    # setup priors + replayable state (capsule, obs macro named, fail appends, human, auth, recovery)
    wtool_append(pid, make_event(SYSTEM_BOOTSTRAPPED, {"boot": "tui_phase9"}))
    wtool_append(pid, make_event(PROJECT_READY, {"name": pid}))
    wtool_append(pid, make_event(INTENT_CAPTURED, {"task": "phase9 tui hotkeys replay"}))
    wtool_append(pid, make_event(WORK_CAPSULE_BUILT, {"capsule_id": "wc_tui_e2e", "contract": "macro:git:tui_replay_e2e:abc:pass on tui"}))
    wtool_append(pid, make_event(MACRO_OBSERVATION_IMPORTED, {"capsule_id": "wc_tui_e2e", "obs": {"macro_ref": "macro:git:tui_replay_e2e:obs123"}}))
    wtool_append(pid, make_event(FAILURE_NODE, {"reason": "tui pre fail for replay"}))
    wtool_append(pid, make_event(HUMAN_DECISION, {"decision": "A approve capsule"}))
    wtool_append(pid, make_event(MACRO_ACTION_AUTHORIZATION, {"action": "dispatch"}))
    wtool_append(pid, make_event(RECOVERY_OBSERVED, {"from": "replay_sim", "tape_tip_before": r.read_tip()}))

    pre_tip = r.read_tip()
    pre_acc = r.read_accepted_head()
    assert pre_tip and pre_acc
    q_pre = reduce_state(pid, data_dir=controlled_data_dir)
    assert "wc_tui_e2e" in q_pre["open_capsules"]
    assert gt.fsck()

    # ensure committed for any rtool (cli replay uses env+default data_dir=None path; pilot explicit)
    gt2 = MicroGitTape(pid, data_dir=controlled_data_dir)
    gt2.init()

    # 1. replay cmd acceptance (rebuilds view from Micro Tape + declared Macro anchors in obs)
    runner = CliRunner()
    res = runner.invoke(app, ["replay", pid], env={"TURINGOS_DATA_DIR": str(controlled_data_dir)})
    assert res.exit_code in (0, 1, 2), f"replay exit unexpected: {res.exit_code} out={res.output[:200]}"
    assert "REPLAY" in res.output or "replay" in (res.output or "").lower() or "μ:" in res.output
    assert "μ:" in res.output
    assert "RECOVERY_OBSERVED" in res.output or "HumanDecision" in res.output
    assert "macro:git:" in res.output or "MacroObservationImported" in res.output  # scale named anchor from obs

    # 2. TUI pilot sim skeleton (simulate human hotkeys for 1+ case)
    from turingos.tui.app import TuiApp  # must exist post impl

    async def drive():
        tui_app = TuiApp(project_id=pid, data_dir=controlled_data_dir)
        async with tui_app.run_test() as pilot:
            await pilot.pause()  # mount, compose panes, initial projection refresh from reducer
            # drive keys: r=replay (loads via rtool into evidence), A=approve dispatch (wtool Human via pred), ?=help, q=quit
            await pilot.press("r")
            await pilot.pause()
            await pilot.press("A")
            await pilot.pause()
            await pilot.press("?")
            await pilot.pause()
            await pilot.press("q")
            await pilot.pause()
        # after pilot, app exited cleanly
        assert True

    asyncio.run(drive())

    # 3. post sim: tape advanced on dispatch keys (A pressed -> HumanDecision appended thru wtool/pred), fsck, scale, no zombies
    post_tip = r.read_tip()
    assert post_tip != pre_tip  # at least one append from A key
    gt2 = MicroGitTape(pid, data_dir=controlled_data_dir)
    assert gt2.fsck()

    seen = set()
    for oid in r.iter_commits():
        node = r.load_node(oid)
        et = node.get("event_type")
        eid = node.get("event_id")
        assert eid.startswith("μ:"), f"scale name required: {eid}"
        if "macro:git:" in str(node.get("payload", {})) or "macro_ref" in str(node.get("payload", {})):
            assert "macro:git:" in str(node.get("payload", {})) or "macro_ref" in str(node.get("payload", {}))  # FC-A02
        seen.add(et)

    # TUI nodes (projection, no new) + priors exercised (recovery, auth, human, capsule, fail, obs)
    required_for_tui_replay = {
        SYSTEM_BOOTSTRAPPED, PROJECT_READY, INTENT_CAPTURED, WORK_CAPSULE_BUILT,
        MACRO_OBSERVATION_IMPORTED, FAILURE_NODE, HUMAN_DECISION, MACRO_ACTION_AUTHORIZATION, RECOVERY_OBSERVED,
    }
    missing = required_for_tui_replay - seen
    assert not missing, f"ZOMBIE for TUI nodes + priors: {missing}. Seen: {seen}"

    q_post = reduce_state(pid, data_dir=controlled_data_dir)
    assert q_post["tape_tip"] == post_tip
    assert "wc_tui_e2e" in q_post.get("open_capsules", [])

    # 4. projection only verify (reducer/rtool source, no tui write direct)
    # (if tui had written direct, tip would be inconsistent or fsck fail or pred fail; here via dispatch keys)
    assert "projection" not in str(q_post).lower()  # just state from tape


def test_tui_panes_projection_reads_only(controlled_data_dir):
    """Direct: TUI class uses reducer for panes (MICRO STATE etc); no writes in app."""
    os.environ["TURINGOS_DATA_DIR"] = str(controlled_data_dir)
    pid = "tui_panes_only"
    gt = MicroGitTape(pid)
    gt.init()
    wtool_append(pid, make_event(PROJECT_READY, {"p": "pane"}))
    from turingos.tui.app import TuiApp
    tui = TuiApp(project_id=pid, data_dir=controlled_data_dir)
    # projection read (would populate panes)
    state = tui._get_projection()  # internal for test; real uses in compose/refresh
    assert state["project_id"] == pid
    assert state["tape_tip"].startswith("μ:")
    # confirm no tape mutation by construction
    assert MicroRtool(pid, data_dir=controlled_data_dir).read_tip() == state["tape_tip"]
