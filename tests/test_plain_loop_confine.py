"""plain_loop's agent: edit only (no bash, no web, no outside paths), a call
directory outside every git repository, and the submission sentence every
method's prompt carries."""
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "harness"))

pytest.importorskip("chia.models.opencode")
import plain_loop  # noqa: E402
from adir.confine import SUBMISSION_NOTE, git_root, with_submission_note  # noqa: E402


def _agent():
    return plain_loop.Agent("opencode", "deepseek", "deepseek-flash", "high", 60)


def test_permissions_edit_only(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    node = _agent().llm._make(plain_loop.SYSTEM_TEXT, str(ws))
    plain_loop._allow_writes(node, "opencode")
    perm = node._build_config([])["permission"]
    assert perm["edit"] == "allow"
    assert perm["bash"] == "deny" and perm["webfetch"] == "deny"
    ext = perm["external_directory"]                  # every outside path, and last the shared tool-output glob
    assert list(ext.items())[0] == ("*", "deny")
    assert list(ext.items())[-1][0].endswith("/opencode/tool-output/*") and list(ext.items())[-1][1] == "deny"


def test_prompt_carries_submission_note():
    system = with_submission_note(plain_loop.SYSTEM_TEXT)
    assert SUBMISSION_NOTE in system
    src = (HERE.parent / "harness" / "plain_loop.py").read_text()
    assert "with_submission_note(SYSTEM_TEXT)" in src and "agent.call(system, user, d)" in src


def test_call_runs_outside_git_and_copies_back(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    (repo / ".git" / "HEAD").write_text("ref: refs/heads/main\n")
    d = repo / "run" / "plain.r1" / "call_1"
    d.mkdir(parents=True)
    (d / "program.sv").write_text("module m; endmodule\n")
    monkeypatch.setenv("ADIR_AGENT_ROOT", str(tmp_path / "agent_ws"))
    seen = {}

    def fake_call(system, user, work_dir):
        seen["dir"] = work_dir
        (work_dir / "candidate.sv").write_text("module m2; endmodule\n")
        return plain_loop.AgentResult(status="ok")

    a = _agent()
    monkeypatch.setattr(a, "_call", fake_call)
    a.call("s", "u", d)
    assert git_root(seen["dir"]) is None and seen["dir"] != d
    assert (seen["dir"] / "program.sv").is_file()
    assert (d / "candidate.sv").read_text() == "module m2; endmodule\n"
