"""ADIR over the toy domain: binding, the declaration block, the
expression language, seeds and candidates through the graph, the
numeric backend, the sub-instance node, the report and the CLI."""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))          # the toy domain
sys.path.insert(0, str(HERE.parent))   # the package

from adir import BindError, UNDECIDED  # noqa: E402
from adir import expr as X  # noqa: E402
from adir.cli import do_check, do_seeds, main as cli_main  # noqa: E402
from adir.declaration import parse_block, render_block  # noqa: E402
from adir.evaluate import candidate_from_program, evaluate_candidate, load_seed_values, seed_programs_of  # noqa: E402
from adir.instance import load  # noqa: E402
from adir.nodes import Executor  # noqa: E402

YAML = HERE / "toy_run.yaml"


class Load(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="adir_"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_bind(self):
        inst = load(YAML, run_dir_override=str(self.tmp))
        names = sorted(b.name for b in inst.bindings.values())
        self.assertIn("lane.l0.style", names)
        self.assertIn("lane.l1.style", names)
        self.assertEqual(inst.bindings["cfg.a"].value, 3)      # from the preset
        self.assertEqual(inst.bindings["mode"].members, ["a", "b"])
        self.assertEqual(sorted(v.name for v in inst.searched()),
                         ["algo", "algo.k", "lane.l0.style", "lane.l1.style"])
        conds = {c["child"]: c for c in inst.space["conditions"]}
        self.assertEqual(conds["algo.k"]["values"], ["fast"])
        self.assertEqual(inst.graph.active[0], "declaration")
        self.assertIn("heldout", inst.graph.active)
        self.assertTrue(inst.hashes["unit_id"] and inst.hashes["space_hash"])
        self.assertEqual(inst.artifacts["harness"].text, "print('harness for 2 lanes')\n")

    def test_errors(self):
        import yaml
        doc = yaml.safe_load(YAML.read_text())

        def bad(mut, needle):
            d = json.loads(json.dumps(doc))
            mut(d["adir"])
            p = self.tmp / "bad.yaml"
            p.write_text(yaml.safe_dump(d, sort_keys=False))
            with self.assertRaises(BindError) as cm:
                load(p, run_dir_override=str(self.tmp))
            self.assertIn(needle, str(cm.exception))

        bad(lambda a: a["variables"].pop("algo"), "unbound")
        bad(lambda a: a["variables"].__setitem__("lanes", {"search": [1, 2]}), "not admitted")
        bad(lambda a: a["variables"].__setitem__("mode", {"runtime": ["a"]}), "one member")
        bad(lambda a: a["variables"].__setitem__("accuracy", {"fixed": "approximate"}), "satisfies")
        bad(lambda a: a["evaluate"]["nodes"]["check"]["inputs"].__setitem__("bogus", 1), "not a parameter")
        bad(lambda a: a["evaluate"]["feedback"].append("heldout.area"), "report_only")
        bad(lambda a: a["constraints"].append({"metric": "nowhere.x", "le": 1}), "unknown name")
        bad(lambda a: a["evaluate"]["nodes"]["check"]["inputs"].__setitem__("text", "archive.check.pass"),
            "when")
        bad(lambda a: a["evaluate"]["nodes"]["measure"].__setitem__("map_over", {"lanes": [1, 2]}),
            "also under inputs")


class Declaration(unittest.TestCase):
    def test_roundtrip(self):
        text = render_block({"algo": "fast", "algo.k": 3}, [("NOTE", ["hello", "x=1"])], "#")
        d = parse_block("# header\n" + text + "def f(): pass\n")
        self.assertTrue(d.present)
        self.assertEqual(d.vars, {"algo": "fast", "algo.k": 3})
        self.assertEqual(d.lines, [("NOTE", ["hello", "x=1"])])
        self.assertFalse(parse_block("nothing").present)


class Expressions(unittest.TestCase):
    def test_values(self):
        env = {"a": 4, "b": 2, "m": {"x": 1, "y": 3}, "n": {"x": 2, "y": 4},
               "iv": {"mean": 1.0, "lo": 0.9, "hi": 1.1, "n": 5}, "u": UNDECIDED,
               "w": {"x": 1, "y": 3}}
        ev = lambda s: X.evaluate(X.parse(s), env.__getitem__)
        self.assertEqual(ev("a / b + 1"), 3)
        self.assertEqual(ev("m * n"), {"x": 2, "y": 12})
        self.assertEqual(ev("m / 2"), {"x": 0.5, "y": 1.5})
        self.assertAlmostEqual(ev("geomean(n)"), (2 * 4) ** 0.5)
        self.assertEqual(ev("sum(m)"), 4)
        self.assertEqual(ev("min(m)"), 1)
        self.assertEqual(ev("max(a, b)"), 4)
        self.assertEqual(ev("quantile(n, 0.5)"), 3)
        self.assertEqual(ev("wmean(m, w)"), (1 * 1 + 3 * 3) / 4)
        self.assertIs(ev("a + u"), UNDECIDED)
        self.assertTrue(ev("a ge b"))
        self.assertTrue(ev("iv le 1.2"))
        self.assertFalse(ev("iv le 1.0"))
        self.assertTrue(ev("m le 5"))
        self.assertEqual(X.references(X.parse("geomean(gem5.ipc) / seed.x.y")), ["gem5.ipc", "seed.x.y"])
        with self.assertRaises(X.ParseError):
            X.parse("foo(1)")


class Run(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="adir_"))
        self.inst = load(YAML, run_dir_override=str(self.tmp))
        do_check(self.inst, self.tmp, quiet=True)
        self.records = do_seeds(self.inst, self.tmp, quiet=True)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _eval(self, program, **meta):
        cand = candidate_from_program(self.inst, program, **meta)
        return evaluate_candidate(self.inst, self.tmp, cand, seed_values=load_seed_values(self.tmp),
                                  archive=self.inst.archive(self.tmp), executor=Executor(self.tmp / "cache"),
                                  seed_programs=seed_programs_of(self.tmp))

    def test_seeds(self):
        self.assertEqual([r["seed_name"] for r in self.records], ["baseline", "small"])
        r0 = self.records[0]
        self.assertTrue(r0["feasible"], r0)
        self.assertAlmostEqual(r0["score"]["combined_score"], 1.0)
        self.assertIn("curve", r0["measurements"])
        self.assertEqual(set(r0["measurements"]["curve"]["value"]["cycles"]), {"1", "2", "4"})
        self.assertIn("slow", r0["measurements"])
        self.assertNotIn("heldout", r0["measurements"])
        # a `when` holds on what a constraint row `eq: true` accepts: the aggregates
        # return numbers, so `min` over a mapping of booleans is 1, not True
        from adir.graph import holds
        self.assertTrue(holds(True)); self.assertTrue(holds(1)); self.assertTrue(holds(1.0))
        self.assertFalse(holds(False)); self.assertFalse(holds(0)); self.assertFalse(holds(2))
        self.assertFalse(holds("yes")); self.assertFalse(holds(UNDECIDED))
        # a transient output travels the graph and leaves its size, not its bytes,
        # in the record: `slow` saw all 4096 of them, `measure`'s record did not
        self.assertEqual(r0["measurements"]["slow"]["value"]["blob_bytes"], 4096)
        self.assertEqual(r0["measurements"]["measure"]["value"]["blob"], "<transient: 4096 bytes>")
        self.assertEqual(r0["measurements"]["measure"]["value"]["delay"], 94)
        seed_values = json.loads((self.tmp / "seeds" / "seed_values.json").read_text())
        self.assertEqual(seed_values["measure"]["blob"], "<transient: 4096 bytes>")
        self.assertNotIn("b" * 64, (self.tmp / "results_db.jsonl").read_text())
        self.assertEqual(r0["declarations"]["vars"]["algo"], "fast")
        self.assertTrue((self.tmp / "seeds" / "seed_values.json").is_file())
        self.assertTrue((self.tmp / "problem.md").read_text().count("baseline") >= 1)
        self.assertTrue((self.tmp / "skydiscover.yaml").is_file())
        self.assertTrue((self.tmp / "evaluator.py").is_file())
        program = (self.tmp / "seeds" / "baseline" / "program.py").read_text()
        self.assertIn("EVOLVE-BLOCK-START", program)
        self.assertIn("ADIR-DECL v1", program)
        self.assertLess(program.index("EVOLVE-BLOCK-START"), program.index("ADIR-DECL v1"))
        # small: algo.k inactive, no VAR for it, still feasible
        r1 = self.records[1]
        self.assertTrue(r1["feasible"], r1)
        self.assertNotIn("algo.k", r1["declarations"]["vars"])
        self.assertGreater(r1["score"]["combined_score"], 1.0)

    def test_candidates(self):
        program = (self.tmp / "seeds" / "baseline" / "program.py").read_text()
        better = program.replace("    y = helper(x)\n    return y * 2 + 1\n", "    return x\n")
        r = self._eval(better, iteration=1)
        self.assertTrue(r["feasible"], r)
        self.assertGreater(r["score"]["combined_score"], 1.0)
        # a change outside the block: evolve_bounds
        outside = program.replace("def helper(x):\n    return x + 1", "def helper(x):\n    return x")
        r = self._eval(outside, iteration=2)
        self.assertTrue(r["hard_fail"])
        self.assertIn("evolve_bounds", r["stderr"])
        # a broken program: check fails, measure skipped, score 0
        broken = program.replace("return y * 2 + 1", "syntax_error")
        r = self._eval(broken, iteration=3)
        self.assertTrue(r["hard_fail"])
        self.assertEqual(r["score"]["combined_score"], 0.0)
        self.assertIn("measure", r["skipped"])
        # a declaration that changes a variable
        switched = program.replace("VAR lane.l0.style=x", "VAR lane.l0.style=y")
        r = self._eval(switched, iteration=4)
        self.assertTrue(r["feasible"])
        self.assertEqual(r["declarations"]["vars"]["lane.l0.style"], "y")
        # a declaration outside the domain
        bad = program.replace("VAR lane.l0.style=x", "VAR lane.l0.style=z")
        r = self._eval(bad, iteration=5)
        self.assertTrue(r["hard_fail"])
        # screened: a large program fails the `when` of slow; slow is UNDECIDED
        big = program.replace("    return y * 2 + 1\n", "    return y * 2 + 1  " + "#" * 400 + "\n")
        r = self._eval(big, iteration=6)
        self.assertIn("slow", r["skipped"])
        self.assertNotIn("slow", r["measurements"])
        from adir.evaluate import backend_result
        br = backend_result(self.inst, r)
        self.assertIn("combined_score", br["metrics"])
        self.assertEqual(br["metrics"]["candidate_id"], r["candidate_id"])
        self.assertIn("check.detail", br["artifacts"])
        self.assertIn("VAR algo=", br["artifacts"]["declarations"])

    def test_report(self):
        from adir.report import report
        s = report(self.inst, self.tmp)
        self.assertEqual(s["records"], 2)
        self.assertTrue(s["front"])
        self.assertIn("heldout.area", next(iter(s["report_values"].values())))
        self.assertTrue((self.tmp / "report.md").is_file())


class Numeric(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="adir_"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_random_backend(self):
        inst = load(HERE / "toy_numeric.yaml", run_dir_override=str(self.tmp))
        self.assertTrue(inst.is_numeric)
        do_check(inst, self.tmp, quiet=True)
        recs = do_seeds(inst, self.tmp, quiet=True)
        self.assertEqual(len(recs), 1)
        from adir.backends import numeric
        res = numeric.run(inst, self.tmp)
        self.assertEqual(res["iterations"], 12)
        arch = inst.archive(self.tmp)
        self.assertEqual(len(arch.records()), 13)
        best = arch.ranked(inst.goal)[0]
        self.assertTrue(best["feasible"])
        # every random declaration respects the condition algo -> algo.k
        for r in arch.records():
            v = r["declarations"]["vars"]
            self.assertEqual("algo.k" in v, v["algo"] == "fast", v)
        self.assertGreaterEqual(len(arch.metric_values("fast_measure.area")), 1)

    def test_subinstance(self):
        inst = load(HERE / "toy_outer.yaml", run_dir_override=str(self.tmp))
        do_check(inst, self.tmp, quiet=True)
        recs = do_seeds(inst, self.tmp, quiet=True)
        r = recs[0]
        self.assertTrue(r["feasible"], r)
        inner = r["measurements"]["inner"]["value"]
        self.assertIn("best", inner)
        self.assertEqual(inner["iterations"], 4)
        from adir.backends import numeric
        res = numeric.run(inst, self.tmp)
        self.assertEqual(res["iterations"], 2)          # the grid over lanes in [1, 2]
        subs = list((self.tmp / "sub").iterdir())
        self.assertEqual(len(subs), 2)                    # cached per binding value


class Cli(unittest.TestCase):
    def test_check(self):
        tmp = Path(tempfile.mkdtemp(prefix="adir_"))
        try:
            rc = cli_main(["check", str(YAML), "--run-dir", str(tmp)])
            self.assertEqual(rc, 0)
            self.assertTrue((tmp / "contract.json").is_file())
            c = json.loads((tmp / "contract.json").read_text())
            self.assertEqual(c["module"], "toy.Box")
            self.assertIn("search_hash", c)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()


class MappedContract(unittest.TestCase):
    """map_over feeding an aggregate into a `when`, a hard row and a goal,
    with `rollback` and `giveup` beside them. The combination is what the
    single-node fixtures never reached: a `when` over `min(<mapped
    boolean>)` never fired, and nothing in the suite would have said so."""

    YAML = str(Path(__file__).resolve().parent / "toy_mapped.yaml")

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="adir_mapped_"))
        self.inst = load(self.YAML, run_dir_override=str(self.tmp))
        do_check(self.inst, self.tmp, quiet=True)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _eval(self, program, **meta):
        cand = candidate_from_program(self.inst, program, **meta)
        return evaluate_candidate(self.inst, self.tmp, cand, seed_values=load_seed_values(self.tmp),
                                  archive=self.inst.archive(self.tmp), executor=Executor(self.tmp / "cache"),
                                  seed_programs=seed_programs_of(self.tmp))

    def test_aggregate_gates_a_when_and_a_hard_row(self):
        recs = do_seeds(self.inst, self.tmp, quiet=True)
        r = recs[0]
        self.assertTrue(r["feasible"], r.get("stderr"))
        # the mapped members are keyed, and `min` over the booleans holds
        self.assertEqual(set(r["measurements"]["curve"]["value"]["cycles"]), {"1", "2", "4"})
        self.assertEqual(set(r["measurements"]["curve"]["value"]["ok"]), {"1", "2", "4"})
        # the `when` over that aggregate fired, so the node behind it ran
        self.assertIn("tail", r["measurements"], r["skipped"])
        self.assertNotIn("tail", r["skipped"])
        for row in r["constraints"]:
            self.assertEqual(row["status"], "satisfied", row)

    def test_rollback_retracts_the_call_s_history(self):
        from adir.backends.skydiscover import record_history
        from adir.composer import retracted_entries
        do_seeds(self.inst, self.tmp, quiet=True)
        reply = ("<<<<<<< HISTORY compute\nreplaced:\na\nwith:\nb\nwhy: t\n>>>>>>> HISTORY")
        noted = record_history(self.tmp, reply)
        self.assertEqual(noted, [{"region": "compute", "edit": 1}])
        good = (self.tmp / "seeds" / "baseline" / "program.py")
        text = good.read_text() if good.is_file() else None
        self.assertIsNotNone(text)
        bad = text.replace("def compute", "does_not_build\ndef compute", 1)
        r = self._eval(bad, meta={"history": noted})
        self.assertFalse(r["feasible"])
        self.assertEqual(r["retracted"], ["compute#1"])
        self.assertEqual(retracted_entries(self.tmp).get("compute"), [1])
        # the retraction is also the edit's effect, in the file the next round reads
        text = (self.tmp / "history" / "compute.md").read_text()
        self.assertRegex(text, r"\neffect of edit 1: \(candidate \w+.*\) retracted -- ")

    def _seed(self):
        recs = do_seeds(self.inst, self.tmp, quiet=True)
        return recs[0], (self.tmp / "seeds" / "baseline" / "program.py").read_text()

    def test_every_evaluated_edit_gets_its_measured_effect(self):
        """The effect is written when the edit is evaluated, whether or not
        the candidate is ever picked as a parent: the edits that made things
        worse are the ones never picked, and the ones a later round most
        needs to see. A single-objective goal over a mapped measurement
        gives the goal against the parent and the change per member."""
        from adir.backends.skydiscover import record_history
        from adir.composer import history_effects
        seed, text = self._seed()
        noted = record_history(self.tmp, "<<<<<<< HISTORY compute\nwhy: a\n>>>>>>> HISTORY")
        record_history(self.tmp, "<<<<<<< HISTORY compute\nwhy: b\n>>>>>>> HISTORY")   # a later entry lands first
        r = self._eval(text.replace("def compute(x):", "def compute(x):\n    # same behaviour", 1),
                       parent_id=seed["candidate_id"],
                       meta={"history": noted})
        self.assertTrue(r["feasible"], r.get("stderr"))
        body = (self.tmp / "history" / "compute.md").read_text()
        eff = history_effects(body)
        self.assertEqual(set(eff), {1})
        self.assertIn(f"from {seed['candidate_id']}", eff[1])
        self.assertIn("geomean(curve.cycles)", eff[1])
        self.assertRegex(eff[1], r"curve\.cycles per member (\w+ [+-]\d+\.\d\d%(, )?)+")
        # the effect line opens no entry, so the numbering of the next note is unchanged
        self.assertEqual(record_history(self.tmp, "<<<<<<< HISTORY compute\nwhy: c\n>>>>>>> HISTORY"),
                         [{"region": "compute", "edit": 3}])

    def test_the_listing_reads_each_effect_by_its_edit_number(self):
        from adir.composer import _history_notes, note_effect
        from adir.backends.skydiscover import record_history
        record_history(self.tmp, "<<<<<<< HISTORY compute\nwhy: first\n>>>>>>> HISTORY")
        record_history(self.tmp, "<<<<<<< HISTORY compute\nwhy: second\n>>>>>>> HISTORY")
        note_effect(self.tmp, [{"region": "compute", "edit": 1}], "(candidate x) worse by a lot")
        lines = "\n".join(_history_notes(self.inst, self.tmp, None, {}))
        self.assertRegex(lines, r"edit 1 .*why: first -- \(candidate x\) worse by a lot")
        self.assertRegex(lines, r"edit 2 .*why: second -- effect: not yet measured")

    def test_the_call_s_directory_holds_the_histories(self):
        """`regions.md` and the prompt point the agent at `history/<region>.md`
        and the agent's file tools reach only its own directory; the file
        has to be there, or every read of it is "File not found"."""
        from adir.backends.skydiscover import record_history
        from adir.composer import call_workspace
        record_history(self.tmp, "<<<<<<< HISTORY compute\nwhy: a\n>>>>>>> HISTORY")
        d = call_workspace(self.inst, self.tmp, "t")
        self.assertIn("why: a", (d / "history" / "compute.md").read_text())

    def test_opencode_output_cap_leaves_room_to_answer(self):
        from adir.backends.skydiscover import OPENCODE_OUTPUT_TOKENS, set_opencode_env
        keep = {k: os.environ.get(k) for k in ("OPENCODE_CONFIG_CONTENT", "OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX")}
        try:
            set_opencode_env({"model": "openrouter/x/y"})
            self.assertEqual(os.environ["OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX"], str(OPENCODE_OUTPUT_TOKENS))
            self.assertGreater(OPENCODE_OUTPUT_TOKENS, 32000)
            set_opencode_env({"model": "openrouter/x/y", "max_output_tokens": 65536})
            self.assertEqual(os.environ["OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX"], "65536")
        finally:
            for k, v in keep.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

    def test_giveup_counts_consecutive_skips_per_member(self):
        from adir.graph import _giveup_counters
        recs = do_seeds(self.inst, self.tmp, quiet=True)
        self.assertTrue(recs[0]["feasible"])
        # `cap: 4` sleeps an order longer than its siblings; whether the tail rule fired
        # or not, a member it gave up on is named in the record and counted, and one it
        # waited for is back at zero
        gave = recs[0].get("gave_up") or {}
        counters = (_giveup_counters(self.tmp) or {}).get("tail") or {}
        for member in gave.get("tail", []):
            self.assertEqual(counters.get(member), 1, counters)
        for member, n in counters.items():
            self.assertLessEqual(n, 1)          # max_skips: 1
