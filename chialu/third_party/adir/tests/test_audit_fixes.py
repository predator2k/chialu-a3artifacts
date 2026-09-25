"""The fixes of the 2026-09-25 audit (audit_full/report.md): history per
parent lineage and duplicate submissions (#1), the backend's metrics
whitelist (#2), seed-relative screens per lineage and no feasible record
without goal values (#3), opencode's tool-output directory (#4), DeepSeek's
402 (#5), ray infrastructure failures (#6), session recovery from the call
directory (#11), no ray retry of an agent call (#13), the worker
environment (#17) and the submission note (#21)."""
from __future__ import annotations

import json
import os
import random
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

from adir.cli import do_check, do_seeds  # noqa: E402
from adir.composer import (MARK_ATTEMPTS, MARK_CURRENT, MARK_END_BACKEND, MARK_INSPIRATIONS,  # noqa: E402
                           compose, filter_metrics)
from adir.instance import load  # noqa: E402

YAML = HERE / "toy_run.yaml"

# a History entry as SkyDiscover printed it in exp9 (fp_alu_cmp_hf best_of_n r3), cut short
EXP9_ATTEMPT = (
    "### Attempt 1\n"
    "- Changes: Change 1: Near `logic zero_f; assign zero_f = (sigf_f == 0) && !st...` (3→3 lines)\n"
    "- Metrics: combined_score: 1.2526, candidate_id: 4f33782ba042, feasible: 1.0000, fidelity_level: 1.0000, "
    "declaration.decl.core.fp_adder.m0.sig_adder.chunk_width_bits: 1.0000, "
    "declaration.decl.core.fp_adder.m0.align.shifter.stage_radix: 2.0000, "
    "declaration.decl.core.rounder.m0.exp_adder.chunk_width_bits: 1.0000, declaration.ok: 1.0000, "
    "fault.sites: 12.0000, yosys_stat.cells: 33224.0000, conformance.pass: 1.0000, "
    "conformance.mismatch_count: 0.0000, measure.area: 5528.8100, synth_ppa.repeats: 3.0000, "
    "goal.1: 5528.8100, goal.2: 3609.0100\n"
    "- Outcome: Improvement in combined_score\n")

HISTORY_REPLY = """Shrink it.

<<<<<<< SEARCH
    return y * 2 + 1
=======
    return y * 2
>>>>>>> REPLACE

<<<<<<< HISTORY compute
replaced:
    return y * 2 + 1
with:
    return y * 2
why: SIBLING_A_EDIT drops the increment
>>>>>>> HISTORY
"""


def _backend_user(parent_id: str, attempts: str = "No previous attempts yet.", tail: str = "") -> str:
    return (f"{MARK_CURRENT}\ncandidate_id: {parent_id}\n{MARK_INSPIRATIONS}\n\n{MARK_ATTEMPTS}\n{attempts}\n"
            f"{MARK_END_BACKEND}\n{tail}")


class _Run(unittest.TestCase):
    backend = None

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="adir_audit_"))
        kw = {"search_override": {"backend": self.backend}} if self.backend else {}
        self.inst = load(YAML, run_dir_override=str(self.tmp), **kw)
        self.inst.search["context"] = {"programs": 1}
        do_check(self.inst, self.tmp, quiet=True)
        self.seeds = do_seeds(self.inst, self.tmp, quiet=True)
        self.env = mock.patch.dict(os.environ, {"ADIR_HISTORY_NOTES": "1"})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)


class Lineage(_Run):
    """#1: a call sees only the history of its parent's ancestors."""

    def test_siblings_do_not_share_history(self):
        from adir.backends.skydiscover import record_history
        from adir.composer import lineage_index, note_effect
        seed = self.seeds[0]["candidate_id"]
        # sibling A: a call on the seed, its note filed, its candidate evaluated
        _, _, side_a = compose(self.inst, self.tmp, _backend_user(seed), random.Random(0))
        entries = record_history(self.tmp, HISTORY_REPLY, parent_id=side_a["parent_id"])
        self.assertEqual(entries, [{"region": "compute", "edit": 1}])
        text = (self.tmp / "history" / "compute.md").read_text()
        self.assertIn(f"; parent {seed})", text)                  # the parent is in the entry's heading
        rec_a = dict(self.seeds[0], candidate_id="cand_a", parent_id=seed, is_seed=False, seed_name=None)
        self.inst.archive(self.tmp).append(rec_a)
        note_effect(self.tmp, entries, "(candidate cand_a, from seed) measured", candidate_id="cand_a",
                    parent_id=seed)
        self.assertEqual(lineage_index(self.tmp)["compute#1"], {"parent": seed, "candidate": "cand_a"})
        # sibling B: another call on the seed sees nothing of A's edit, in the prompt or its directory
        _, user_b, side_b = compose(self.inst, self.tmp, _backend_user(seed), random.Random(1))
        self.assertNotIn("SIBLING_A_EDIT", user_b)
        ws_b = Path(side_b["workspace"])
        hist_b = list((ws_b / "history").glob("*.md")) if (ws_b / "history").is_dir() else []
        self.assertFalse(any("SIBLING_A_EDIT" in f.read_text() for f in hist_b), hist_b)
        # A's child sees it, with its effect
        _, user_c, side_c = compose(self.inst, self.tmp, _backend_user("cand_a"), random.Random(2))
        self.assertIn("SIBLING_A_EDIT", user_c)
        copied = (Path(side_c["workspace"]) / "history" / "compute.md").read_text()
        self.assertIn("SIBLING_A_EDIT", copied)
        self.assertIn("effect of edit 1: (candidate cand_a", copied)

    def test_legacy_entry_attributed_by_effect_line(self):
        """A history written before lineage.json: the effect line names the candidate."""
        from adir.composer import lineage_history
        text = ("\n## edit 1 (2026-09-25 00:37:01)\n\nwhy: A\n\n## edit 2 (2026-09-25 00:38:01)\n\nwhy: B\n"
                "\neffect of edit 2: (candidate bbb, from seed:x) measured\n"
                "\neffect of edit 1: (candidate aaa, from seed:x) measured\n")
        self.assertEqual([n for n, _ in lineage_history("compute", text, {"aaa", "seed:x"}, {})], [1])
        self.assertEqual([n for n, _ in lineage_history("compute", text, {"seed:x"}, {})], [])

    def test_duplicate_marked(self):
        """A program byte-identical to an evaluated one is evaluated (cache) and marked, with feedback."""
        from adir.evaluate_entry import evaluate_program
        seed_prog = (self.tmp / "programs" / "seed_baseline.py").read_text()
        p = self.tmp / "sub.py"
        p.write_text(seed_prog)
        r1 = evaluate_program(self.tmp, p)
        recs = self.inst.archive(self.tmp).records()
        self.assertEqual(recs[-1]["duplicate_of"], "seed:baseline")
        self.assertIn("duplicate", r1["artifacts"])
        n = len(recs)
        evaluate_program(self.tmp, p)
        self.assertEqual(len(self.inst.archive(self.tmp).records()), n + 1)   # one submission, one record


class Metrics(unittest.TestCase):
    """#2: the backend's History shows the goal, the score, feasibility and conformance alone, every method."""

    def test_filter(self):
        inst = load(YAML, run_dir_override=tempfile.mkdtemp(prefix="adir_audit_m_"))
        out = filter_metrics(inst, EXP9_ATTEMPT)
        for gone in ("declaration.decl", "declaration.ok", "fault.", "yosys_stat", "synth_ppa", "mismatch_count",
                     "candidate_id", "fidelity_level"):
            self.assertNotIn(gone, out)
        for kept in ("combined_score: 1.2526", "feasible: 1.0000", "conformance.pass: 1.0000",
                     "measure.area: 5528.8100", "goal.1: 5528.8100", "goal.2: 3609.0100", "- Changes:"):
            self.assertIn(kept, out)
        listed = "Metrics:\n  - declaration.decl.algo: 1\n  - measure.area: 3\n  - e.g.: prose stays\n"
        out = filter_metrics(inst, listed)
        self.assertNotIn("declaration.decl", out)
        self.assertIn("measure.area: 3", out)
        self.assertIn("e.g.: prose stays", out)

    def test_every_method(self):
        for backend in ("best_of_n", "beam_search", "adaevolve"):
            tmp = Path(tempfile.mkdtemp(prefix=f"adir_audit_{backend}_"))
            try:
                inst = load(YAML, run_dir_override=str(tmp), search_override={"backend": backend})
                inst.search["context"] = {"programs": 1}
                do_check(inst, tmp, quiet=True)
                seeds = do_seeds(inst, tmp, quiet=True)
                tail = "## Sibling context\n- Metrics: declaration.decl.algo: 1.0000, goal.1: 3.0000\n"
                _, user, _ = compose(inst, tmp, _backend_user(seeds[0]["candidate_id"], EXP9_ATTEMPT, tail),
                                     random.Random(0))
                self.assertIn("## History", user, backend)
                self.assertNotIn("declaration.decl", user, backend)
                self.assertIn("goal.1: 5528.8100", user, backend)
            finally:
                shutil.rmtree(tmp, ignore_errors=True)


def _seedrel_yaml(tmp: Path) -> Path:
    """The toy run with two seeds of different size, the goal behind a screen relative to `seed.`."""
    d = yaml.safe_load(YAML.read_text())
    a = d["adir"]
    a["search"]["seeds"]["generated"] = ["small", "fast"]          # the first seed is the smaller one
    a["evaluate"]["nodes"]["slow"]["when"] = ["check.pass", "measure.area le 1.2 * seed.measure.area"]
    a["goal"] = {"minimize": "slow.blob_bytes", "score": {"rule": "ratio_to_seed", "infeasible": "slack"}}
    f = tmp / "toy_seedrel.yaml"
    f.write_text(yaml.safe_dump(d, sort_keys=False))
    return f


class SeedScreens(unittest.TestCase):
    """#3: every seed is its own reference, a child its lineage's seed's; no feasible record without a goal."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="adir_audit_seed_"))
        self.inst = load(_seedrel_yaml(self.tmp), run_dir_override=str(self.tmp / "run"))
        do_check(self.inst, self.tmp / "run", quiet=True)
        self.seeds = do_seeds(self.inst, self.tmp / "run", quiet=True)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _child(self, parent_id, program):
        from adir.evaluate import candidate_from_program, evaluate_candidate, load_seed_values
        run = self.tmp / "run"
        cand = candidate_from_program(self.inst, program, parent_id=parent_id)
        return evaluate_candidate(self.inst, run, cand, seed_values=load_seed_values(run),
                                  archive=self.inst.archive(run))

    def test_multi_seed(self):
        areas = [r["measurements"]["measure"]["value"]["area"] for r in self.seeds]
        self.assertGreater(areas[1], 1.2 * areas[0])        # the second seed fails a screen against the first
        for r in self.seeds:
            self.assertIsNotNone(r["goal_values"][0], r["candidate_id"])
            self.assertTrue(r["feasible"], r["candidate_id"])
            self.assertNotIn("slow", r["skipped"])
        run = self.tmp / "run"
        fast = (run / "programs" / "seed_fast.py").read_text()
        # a child of the larger seed is screened against that seed, not the first
        rec = self._child("seed:fast", fast.replace("return z + 3", "return z + 2"))
        self.assertIsNotNone(rec["goal_values"][0])
        self.assertTrue(rec["feasible"])
        # a candidate without a lineage: the largest seed values
        rec = self._child(None, fast.replace("return z + 3", "return z + 4"))
        self.assertIsNotNone(rec["goal_values"][0])
        # a child of the small seed with the large body: screened out, so not feasible, and it says why
        rec = self._child("seed:small", fast.replace("return z + 3", "return z + 5"))
        self.assertIsNone(rec["goal_values"][0])
        self.assertFalse(rec["feasible"])
        self.assertIn("slow", rec["goal_unmeasured"])


class Billing(unittest.TestCase):
    """#5"""

    def test_402(self):
        from adir.backends.skydiscover import is_billing_error
        for t in ("APIError: 402 Insufficient Balance", "InvalidRequestError: Insufficient Balance",
                  '{"error": {"message": "Insufficient Balance", "code": 402}}', "HTTP 402 Payment Required",
                  "BillingError: no credit", "exceed your available credits"):
            self.assertTrue(is_billing_error(t), t)
        for t in ("RuntimeError: opencode call failed (rc 1)", "timeout after 1200 s", "pid=34021 died",
                  "RateLimitError: 429"):
            self.assertFalse(is_billing_error(t), t)


def _ray_like(name: str):
    """An exception class named as ray names a RayTaskError over a cause."""
    return type(name, (RuntimeError,), {})


class Infrastructure(_Run):
    """#6: ray's own failures are retried, then raised, then the candidate re-evaluated -- never its hard fail."""

    def test_detection(self):
        from adir.nodes import infra_detail, is_infra_error
        self.assertTrue(is_infra_error(_ray_like("RayTaskError(OwnerDiedError)")("ray::conformance() died")))
        self.assertTrue(is_infra_error(_ray_like("WorkerCrashedError")("x")))
        self.assertTrue(is_infra_error(_ray_like("ActorDiedError")("x")))
        wrapped = RuntimeError("outer")
        wrapped.__cause__ = _ray_like("OwnerDiedError")("inner")
        self.assertTrue(is_infra_error(wrapped))
        self.assertFalse(is_infra_error(_ray_like("RayTaskError(ValueError)")("bad width")))
        self.assertFalse(is_infra_error(RuntimeError("yosys: syntax error")))
        self.assertTrue(infra_detail({"ok": False, "detail": "RayTaskError(OwnerDiedError): lost"}))
        self.assertFalse(infra_detail({"ok": False, "detail": "syntax error"}))

    def test_retried_then_raised(self):
        from adir.nodes import Executor, InfrastructureError
        calls = []

        def remote(**kw):
            calls.append(kw)
            if len(calls) < 3:
                raise _ray_like("RayTaskError(WorkerCrashedError)")("worker died")
            return {"ok": True}
        ex = Executor(None)
        with mock.patch.dict(os.environ, {"ADIR_RAY_INFRA_BACKOFF_S": "0"}), \
                mock.patch("adir.nodes.ray_get", lambda r: r):
            self.assertEqual(ex._ray_call("n", remote, {"a": 1}), {"ok": True})
            self.assertEqual(len(calls), 3)

            def dead(**kw):
                raise _ray_like("RayTaskError(OwnerDiedError)")("owner died")
            with self.assertRaises(InfrastructureError):
                ex._ray_call("n", dead, {})

            def bad(**kw):
                raise ValueError("the node's own error")
            with self.assertRaises(ValueError):
                ex._ray_call("n", bad, {})

    def test_graph_raises_and_entry_reevaluates(self):
        from adir import evaluate_entry
        from adir.evaluate import candidate_from_program, evaluate_candidate
        from adir.nodes import Executor, InfrastructureError

        class Broken(Executor):
            def run(self, spec, kwargs):
                if spec.name.endswith("measure"):
                    raise InfrastructureError("measure: ray failed 3 time(s): OwnerDiedError")
                return super().run(spec, kwargs)
        prog = (self.tmp / "programs" / "seed_baseline.py").read_text().replace("return y * 2 + 1", "return y * 2")
        cand = candidate_from_program(self.inst, prog, parent_id="seed:baseline")
        with self.assertRaises(InfrastructureError):
            evaluate_candidate(self.inst, self.tmp, cand, executor=Broken(None, workers=2))
        n = len(self.inst.archive(self.tmp).records())
        attempts = []

        def always_broken(*a, **k):
            attempts.append(1)
            raise InfrastructureError("synth: ray failed 3 time(s): RayTaskError(OwnerDiedError)")
        p = self.tmp / "sub.py"
        p.write_text(prog)
        with mock.patch.object(evaluate_entry, "evaluate_candidate", always_broken), \
                mock.patch.object(evaluate_entry.time, "sleep", lambda s: None), \
                mock.patch.dict(os.environ, {"ADIR_INFRA_REEVALUATE": "2"}):
            evaluate_entry.evaluate_program(self.tmp, p)
        self.assertEqual(len(attempts), 3)
        rec = self.inst.archive(self.tmp).records()[-1]
        self.assertEqual(len(self.inst.archive(self.tmp).records()), n + 1)
        self.assertFalse(rec["hard_fail"])
        self.assertFalse(rec["feasible"])
        self.assertEqual(rec["not_evaluated"], "infrastructure")


FAKE_OPENCODE = r'''#!{python}
import json, os, sys, time
wd = {wd!r}
if sys.argv[1] == "session":
    if os.getcwd() != wd:
        print("[]")
    else:
        rows = [{{"id": f"ses_pad{{i}}", "directory": "/elsewhere/" + "x" * 200, "created": 0}} for i in range(600)]
        rows.append({{"id": "ses_mine", "directory": wd, "created": int(time.time() * 1000)}})
        print(json.dumps(rows))
elif sys.argv[1] == "export":
    print(json.dumps({{"id": sys.argv[2], "cwd": os.getcwd()}}))
'''


class Recover(unittest.TestCase):
    """#11: the session list runs in the call directory, its output through a file."""

    def test_list_from_work_dir(self):
        from adir.backends.skydiscover import recover_opencode_session
        tmp = Path(tempfile.mkdtemp(prefix="adir_audit_rec_"))
        try:
            wd = tmp / "call"
            wd.mkdir()
            b = tmp / "opencode"
            b.write_text(FAKE_OPENCODE.format(python=sys.executable, wd=str(wd.resolve())))
            b.chmod(0o755)

            class Node:
                opencode_bin = str(b)

                def _extract_from_export(self, export):
                    return "reply", {"output_tokens": 5}, f"transcript {export['cwd']}", None
            rec = recover_opencode_session(Node(), wd, time.time() - 60)
            self.assertIsNotNone(rec)
            self.assertEqual(rec["session_id"], "ses_mine")        # found past 64 KiB of list output
            self.assertEqual(rec["transcript"], f"transcript {wd.resolve()}")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class AgentCall(unittest.TestCase):
    """#13: an agent call goes to ray with its retries off; #4: the permission block."""

    def test_no_ray_retry(self):
        from adir.backends import skydiscover as sd
        from adir.nodes import CLUSTER
        seen = {}

        class Handle:
            def chia_remote(self, llm, user):
                seen["user"] = user
                return type("R", (), {"success": True, "result": "ok", "usage": {}, "returncode": 0,
                                      "session_id": "s", "stream_result": ""})()

        class Prompt:
            def options(self, **kw):
                seen["options"] = kw
                return Handle()

            def chia_remote(self, *a):
                raise AssertionError("dispatched without options")

        class LLM:
            prompt = Prompt()
        agent = sd.AgentLLM({"agent": "claude", "model": "m"}, None, None)
        with mock.patch.object(agent, "_make", lambda *a, **k: LLM()), \
                mock.patch.dict(CLUSTER, {"connected": True}), mock.patch("adir.nodes.ray_get", lambda r: r):
            self.assertEqual(agent._call("sys", "hello"), "ok")
        self.assertEqual(seen["options"]["max_retries"], 0)
        self.assertEqual(seen["user"], "hello")

    def test_permissions(self):
        from adir.backends.skydiscover import opencode_permissions
        perm = opencode_permissions({"XDG_DATA_HOME": "/d/share", "HOME": "/h"})
        ext = perm["external_directory"]
        self.assertEqual(ext["*"], "deny")
        self.assertEqual(ext["/d/share/opencode/tool-output/*"], "deny")
        self.assertEqual(list(ext)[-1].endswith("tool-output/*"), True)     # last: suppresses opencode's allow
        for tool in ("read", "glob", "grep", "list"):
            self.assertEqual(perm[tool]["*/opencode/tool-output/*"], "deny")
            self.assertEqual(list(perm[tool])[0], "*")
        for k in ("edit", "bash", "webfetch", "task", "doom_loop"):
            self.assertEqual(perm[k], "deny")


class Environment(unittest.TestCase):
    """#17 and #21"""

    def test_worker_env(self):
        from adir.cli import worker_env
        env = worker_env({"OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX": "393216", "OPENCODE_CONFIG_CONTENT": "{}",
                          "ADIR_UNIT_HIERARCHY_NOTE": "1", "ADIR_AGENT_ROOT": "/w", "ADIR_HISTORY_NOTES": "1",
                          "ADIR_RAY_SCHEDULING": "SPREAD", "ANTHROPIC_API_KEY": "k", "PATH": "/bin",
                          "ADIR_EMPTY": ""})
        self.assertEqual(set(env), {"OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX", "OPENCODE_CONFIG_CONTENT",
                                    "ADIR_UNIT_HIERARCHY_NOTE", "ADIR_AGENT_ROOT", "ADIR_HISTORY_NOTES",
                                    "ADIR_RAY_SCHEDULING", "ANTHROPIC_API_KEY"})

    def test_opencode_roles_env(self):
        from adir.cli import set_opencode_roles_env
        inst = mock.Mock()
        inst.search = {"models": {"solution": {"agent": "opencode", "provider": "deepseek", "model": "deepseek-flash",
                                               "max_output_tokens": 393216}}}
        with mock.patch.dict(os.environ, {}, clear=False):
            set_opencode_roles_env(inst)
            self.assertEqual(os.environ["OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX"], "393216")
            self.assertIn("deepseek/deepseek-flash", os.environ["OPENCODE_CONFIG_CONTENT"])

    def test_submission_note(self):
        from adir.confine import SUBMISSION_NOTE, UNIT_HIERARCHY_NOTE, with_submission_note
        self.assertNotIn("edit", SUBMISSION_NOTE)
        self.assertEqual(SUBMISSION_NOTE, "Each submission is synthesized and verified once by the harness after "
                                          "you finish; you cannot run synthesis, simulation or any tool yourself.")
        with mock.patch.dict(os.environ, {"ADIR_UNIT_HIERARCHY_NOTE": "1"}):
            self.assertIn(UNIT_HIERARCHY_NOTE, with_submission_note("sys"))


if __name__ == "__main__":
    unittest.main()
