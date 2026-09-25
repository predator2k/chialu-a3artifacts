"""The composer over the toy domain: the unit slot's omitted options,
the seeds table's line column, the feedback summary, the tactic under
the operator and the focus, and the tried values of the archive."""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

from adir.cli import do_check, do_seeds  # noqa: E402
from adir.composer import _feedback, system_text  # noqa: E402
from adir.instance import load  # noqa: E402
from adir.prompts import choose_tactic, tactic_menu, unexplored_values  # noqa: E402

YAML = HERE / "toy_run.yaml"


class FakeArchive:
    def __init__(self, records):
        self._records = records

    def records(self):
        return self._records


class Composer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="adir_prompt_"))
        cls.inst = load(YAML, run_dir_override=str(cls.tmp))
        do_check(cls.inst, cls.tmp, quiet=True)
        cls.records = do_seeds(cls.inst, cls.tmp, quiet=True)
        cls.archive = cls.inst.archive(cls.tmp)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_prompt_omit(self):
        text = system_text(self.inst, self.records)
        self.assertIn("`lanes_outer` is fixed to 1", text)
        self.inst.elaboration.info["prompt_omit"] = ["lanes_outer"]
        try:
            text = system_text(self.inst, self.records)
            self.assertNotIn("`lanes_outer` is fixed", text)
            self.assertIn("1 further option is fixed at a value that does not apply", text)
            self.assertIn("`lanes` is fixed to 2", text)
        finally:
            self.inst.elaboration.info.pop("prompt_omit")

    def test_seeds_table_lines(self):
        text = system_text(self.inst, self.records)
        self.assertIn("| seed | declared decisions | domain lines |", text)
        self.assertIn("| `baseline` |", text)
        self.assertIn("1 NOTE |", text)                       # the first seed: its line count per kind
        self.assertIn("1 of 1 differ from `baseline`", text)  # the second seed's NOTE line differs

    def test_feedback_summary(self):
        table = {f"m{i}": {"area": i * 1.5, "delay": i * 10} for i in range(40)}
        rec = {"feedback": {"attribution": table, "detail": "x\n" * 300}}
        summary = _feedback(rec, "summary")
        self.assertTrue(any("a table of 40 entries" in s for s in summary), summary)
        self.assertTrue(any("... (truncated)" in s and len(s) < 500 for s in summary), summary)
        full = _feedback(rec, "full")
        self.assertTrue(any('"m39"' in s for s in full), full)
        self.assertEqual(_feedback(rec, "none"), [])

    def test_tried_values_count_the_default(self):
        # a record that declares nothing stood at every default: the default is tried
        recs = [{"candidate_id": "a", "declarations": {"vars": {}}, "measurements": {}}]
        out = unexplored_values(self.inst, FakeArchive(recs))
        self.assertTrue(any("`algo`: no candidate has tried small" in s for s in out), out)
        # a completed declaration (decl.*) is what counts, not the VAR lines
        recs = [{"candidate_id": "b", "declarations": {"vars": {}},
                 "measurements": {"declaration": {"value": {"decl.algo": "small", "ok": True}}}}]
        out = unexplored_values(self.inst, FakeArchive(recs))
        self.assertTrue(any("`algo`: no candidate has tried fast" in s for s in out), out)
        # the focus restricts the variables
        out = unexplored_values(self.inst, FakeArchive(recs), names=["algo.k"])
        self.assertFalse(any("`algo`" in s for s in out), out)

    def test_tactic_under_operator_and_focus(self):
        recs = [{"candidate_id": "a", "declarations": {"vars": {}}, "measurements": {}}]
        self.inst.search.setdefault("tactics", {})["sources"] = ["unexplored_values"]
        try:
            menu = tactic_menu(self.inst, FakeArchive(recs), None)
            self.assertIn("unexplored_values", menu)
            self.assertEqual(tactic_menu(self.inst, FakeArchive(recs), None, operator="local"), {})
            import random
            tid, text = choose_tactic(self.inst, FakeArchive(recs), None, random.Random(0), operator="local")
            self.assertIsNone(tid)
            tid, text = choose_tactic(self.inst, FakeArchive(recs), None, random.Random(0),
                                      operator="structural", focus_vars=["algo"])
            self.assertTrue(tid.startswith("unexplored_values:"))
            self.assertIn("`algo`", text)
        finally:
            self.inst.search["tactics"].pop("sources")


if __name__ == "__main__":
    unittest.main()


class Sidecars(unittest.TestCase):
    """One sidecar per call, taken by the evaluator of the call's program."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="adir_side_"))
        cls.inst = load(YAML, run_dir_override=str(cls.tmp))
        do_check(cls.inst, cls.tmp, quiet=True)
        cls.records = do_seeds(cls.inst, cls.tmp, quiet=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_take_by_parent(self):
        import time
        from adir.composer import program_path
        from adir.prompts import pending_sidecars, take_sidecar, write_sidecar
        run = self.tmp
        ids = [r["candidate_id"] for r in self.records]
        p1 = program_path(run, ids[1], ".py").read_text()
        write_sidecar(run, {"parent_id": ids[0], "tactic_id": "a", "time": time.time()})
        write_sidecar(run, {"parent_id": ids[1], "tactic_id": "b", "time": time.time()})
        self.assertEqual(len(pending_sidecars(run)), 2)
        child = p1.replace("return helper(x)", "return helper(x) + 0")     # an edit inside small's region
        self.assertIn("+ 0", child)
        side = take_sidecar(run, child, self.inst)
        self.assertEqual(side["parent_id"], ids[1])
        self.assertEqual(len(pending_sidecars(run)), 1)
        self.assertEqual(take_sidecar(run)["parent_id"], ids[0])
        self.assertEqual(take_sidecar(run), {})
