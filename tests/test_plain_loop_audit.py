"""plain_loop against the 2026-09-25 audit: the shared opencode tool-output directory is denied (#4),
a 402 / 'Insufficient Balance' refusal stops the loop as billing (#5), a stalled call's session is found
from the call's own directory without pipe truncation (#11), and a failed call keeps the CHIA node's
attempts, session ids and usage (#12, #13)."""
import json
import os
import stat
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "harness"))

pytest.importorskip("chia.models.opencode")
import plain_loop  # noqa: E402
from chia.models.opencode import BillingError, OpenCodeLLM  # noqa: E402


def _agent():
    return plain_loop.Agent("opencode", "deepseek", "deepseek-flash", "high", 60)


# ------------------------------------------------------------------ #4 tool-output directory

def test_tool_output_denied_in_the_agent_permissions(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "share"))
    ws = tmp_path / "ws"
    ws.mkdir()
    node = _agent().llm._make(plain_loop.SYSTEM_TEXT, str(ws))
    plain_loop._allow_writes(node, "opencode")
    glob = str(tmp_path / "share" / "opencode" / "tool-output" / "*")
    for perm in (node.config, node._build_config([])["permission"]):
        ext = list(perm["external_directory"].items())
        assert ext[0] == ("*", "deny") and ext[-1] == (glob, "deny")
        assert perm["read"]["*opencode/tool-output/*"] == "deny"
        assert perm["edit"] == "allow" and perm["task"] == "deny" and perm["bash"] == "deny"
        assert all(v == "deny" for v in perm["external_directory"].values())   # no outside path allowed
        assert perm["glob"]["*/opencode/tool-output/*"] == "deny"               # ADIR's file-tool rules kept


def test_tool_output_fallback_without_chia_helper(tmp_path, monkeypatch):
    import chia.models.opencode as oc
    monkeypatch.delattr(oc, "deny_tool_output")
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "share"))
    cfg = plain_loop._tool_output_denied({"external_directory": "deny", "edit": "allow"})
    assert list(cfg["external_directory"].items()) == [
        ("*", "deny"), (str(tmp_path / "share" / "opencode" / "tool-output" / "*"), "deny")]
    assert cfg["read"]["*opencode/tool-output"] == "deny"


# ------------------------------------------------------------------ #5 billing

@pytest.mark.parametrize("text", [
    "BillingError: billing_error on 7f3a: Insufficient Balance",
    'UnknownOpenCodeError: {"name":"APIError","data":{"message":"Insufficient Balance","statusCode":402}}',
    '{"error":{"message":"Insufficient Balance","type":"unknown_error","code":"invalid_request_error"}}',
    "AI_APICallError: HTTP 402 Payment Required",
    'error event: {"name": "APIError", "data": {"statusCode": 402, "message": ""}}',
    "openrouter: This request requires more credits: exceed your available credits",
])
def test_billing_payloads_stop_the_loop(text):
    assert plain_loop.is_billing(text)


@pytest.mark.parametrize("text", ["", "UnknownOpenCodeError: doom_loop", "syntax error at line 402",
                                  "wrote 4020 bytes", "TimeoutExpired: timed out after 402.5 s"])
def test_non_billing_payloads(text):
    assert not plain_loop.is_billing(text)


def test_loop_uses_the_billing_check():
    src = (HERE.parent / "harness" / "plain_loop.py").read_text()
    assert 'if res.status != "ok" and is_billing(res.stderr):' in src and "stopped_by_billing" in src


def test_billing_error_from_the_node_is_a_billing_stop(tmp_path, monkeypatch):
    a = _agent()
    err = BillingError("node", 0, "Insufficient Balance")
    err.attempts = [{"attempt": 1, "session_id": "ses_b", "usage": {"cost_usd": 0.001}, "error_type": "BillingError"}]
    err.usage = {"cost_usd": 0.001}

    class Node:
        config = {}

        def prompt(self, user):
            raise err

    monkeypatch.setattr(a.llm, "_make", lambda system, wd: Node())
    monkeypatch.setattr("adir.backends.skydiscover.set_opencode_env", lambda spec: None)
    res = a._call("s", "u", tmp_path)
    assert res.status == "failed" and plain_loop.is_billing(res.stderr)
    assert res.session_id == "ses_b" and res.usage == {"cost_usd": 0.001} and res.attempts == err.attempts


# ------------------------------------------------------------------ #12/#13 attempts of a failed call

def test_failed_result_keeps_attempts_and_reason(tmp_path, monkeypatch):
    a = _agent()
    attempts = [{"attempt": 1, "session_id": "ses_1", "usage": {"cost_usd": 0.01}, "error_type": "UnknownOpenCodeError",
                 "error": "doom_loop"}]
    res_obj = SimpleNamespace(success=False, result="", stream_result="t", usage={"cost_usd": 0.01},
                              session_id="ses_1", returncode=-1, attempts=attempts,
                              stderr="attempt 1 of 1 (last): UnknownOpenCodeError: doom_loop")

    class Node:
        config = {}

        def prompt(self, user):
            return res_obj

    monkeypatch.setattr(a.llm, "_make", lambda system, wd: Node())
    monkeypatch.setattr("adir.backends.skydiscover.set_opencode_env", lambda spec: None)
    res = a._call("s", "u", tmp_path)
    assert res.status == "failed" and "doom_loop" in res.stderr
    assert res.attempts == attempts and res.session_id == "ses_1" and res.usage == {"cost_usd": 0.01}


# ------------------------------------------------------------------ #11 session recovery

def test_recover_runs_in_the_call_dir_and_reads_past_64k(tmp_path, monkeypatch):
    import subprocess
    real_run = subprocess.run
    stdouts = []

    def spy(cmd, **kw):                             # opencode cuts a piped stdout at 64 KiB: a file it must be
        stdouts.append(hasattr(kw.get("stdout"), "write") and not kw.get("capture_output"))
        return real_run(cmd, **kw)

    monkeypatch.setattr(subprocess, "run", spy)
    wd = tmp_path / "calls" / "call_3"
    wd.mkdir(parents=True)
    log = tmp_path / "cwds"
    export = {"info": {}, "messages": [{"info": {"role": "assistant", "tokens": {"input": 7, "output": 2},
                                                  "cost": 0.004}, "parts": [{"type": "text", "text": "partial"}]}]}
    fake = tmp_path / "opencode"
    fake.write_text(f"""#!{sys.executable}
import json, os, sys
open({str(log)!r}, "a").write(os.getcwd() + "\\n")
if sys.argv[1:3] == ["session", "list"]:
    wd = os.getcwd()
    # a list well past 64 KiB, the call's session last (a pipe would cut it off)
    others = [{{"id": "ses_other%d" % i, "directory": "/elsewhere/%d" % i, "created": 10**13, "title": "x" * 200}}
              for i in range(600)]
    print(json.dumps(others + [{{"id": "ses_mine", "directory": wd, "created": 10**13}}]))
elif sys.argv[1] == "export":
    print(json.dumps({json.dumps(export)!r} and json.loads({json.dumps(export)!r})))
""")
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    node = OpenCodeLLM(opencode_bin=str(fake))
    rec = plain_loop.recover_opencode_session(node, wd, since_s=0)
    assert rec is not None and rec["session_id"] == "ses_mine"
    assert rec["reply"] == "partial" and rec["usage"]["cost_usd"] == pytest.approx(0.004)
    cwds = log.read_text().split()
    assert cwds == [str(wd.resolve())] * 2          # both `session list` and `export` ran in the call's directory
    assert stdouts == [True, True]
