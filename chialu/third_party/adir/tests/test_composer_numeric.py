"""Instruction evolution through the composer with stub clients, and
the SMAC3 and NSGA-II backends over the numeric toy run file. The
optimizer tests skip without their packages."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import tempfile
import unittest
from pathlib import Path


import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

try:
    import skydiscover  # noqa: F401
    HAS_SD = True
except ImportError:
    HAS_SD = False
try:
    import smac  # noqa: F401
    HAS_SMAC = True
except ImportError:
    HAS_SMAC = False
try:
    import pymoo  # noqa: F401
    HAS_PYMOO = True
except ImportError:
    HAS_PYMOO = False

from adir import BindError  # noqa: E402
from adir.cli import do_check, do_run, do_seeds  # noqa: E402
from adir.instance import load  # noqa: E402

YAML = HERE / "toy_run.yaml"
NUMERIC = HERE / "toy_numeric.yaml"

DIFF = """Shorter body.

<<<<<<< SEARCH
    return y * 2 + 1
=======
    return y * 2
>>>>>>> REPLACE
"""


class Stub:
    def __init__(self, spec, role):
        self.spec, self.role, self.calls = spec, role, []

    async def generate(self, system, messages, **kw):
        user = messages[0]["content"]
        self.calls.append((system, user))
        if self.role == "strategy":
            return "```\nPrefer the shortest body; drop temporaries.\n```"
        if "return y * 2 + 1" in user.split("## Context programs")[0]:
            return DIFF
        return "no change"


def _write(tmp: Path, mutate) -> Path:
    doc = yaml.safe_load(YAML.read_text())
    mutate(doc["adir"])
    p = tmp / "run.yaml"
    p.write_text(yaml.safe_dump(doc, sort_keys=False))
    return p


@unittest.skipUnless(HAS_SD, "skydiscover is not installed")
class Instructions(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="adir_ins_"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_instruction_evolution(self):
        from adir.backends import skydiscover as sd

        def mut(a):
            a["search"]["instructions"] = {"enabled": True, "seed": "Keep the helper untouched.",
                                           "propose": {"role": "strategy", "every": 2,
                                                       "from": ["feedback", "declarations", "metrics"]},
                                           "select": "ucb", "window": 20, "max_chars": 300}
        inst = load(_write(self.tmp, mut), run_dir_override=str(self.tmp / "run"))
        run = inst.run_dir
        do_check(inst, run, quiet=True)
        do_seeds(inst, run, quiet=True)
        stubs = []

        def clients(spec, role):
            c = Stub(spec, role)
            stubs.append(c)
            return c
        sd.run(inst, run, iterations=6, clients=clients)
        rows = [json.loads(l) for l in (run / "instructions.jsonl").read_text().splitlines()]
        self.assertTrue(any(r["source"] == "seed" for r in rows))
        self.assertTrue(any(r["source"] == "proposed" for r in rows), rows)
        proposed = [r for r in rows if r["source"] == "proposed"][0]
        self.assertIn("shortest body", proposed["text"])
        strategy_calls = [c for c in stubs if c.role == "strategy" and c.calls]
        self.assertTrue(strategy_calls)
        self.assertIn("## Recent iterations", strategy_calls[0].calls[0][1])
        recs = [r for r in inst.archive(run).records() if not r["is_seed"]]
        used = {r.get("instruction_id") for r in recs}
        self.assertTrue(any(u for u in used), "an instruction id lands in the records")
        solution_calls = [c for c in stubs if c.role == "solution" and c.calls]
        self.assertTrue(any("## Guidance" in u for _, u in solution_calls[0].calls))
        self.assertTrue((run / "prompt_sample.md").is_file())

    def test_bind_checks(self):
        def bad(mut, needle):
            with self.assertRaises(BindError) as cm:
                load(_write(self.tmp, mut), run_dir_override=str(self.tmp / "run"))
            self.assertIn(needle, str(cm.exception))
        bad(lambda a: a["search"]["prompts"]["variants"].__setitem__("bogus", [1]), "unknown knob")
        bad(lambda a: a["search"]["prompts"]["variants"].__setitem__("show", ["everything"]), "not one of")
        bad(lambda a: a["search"]["prompts"]["sources"].append("nope"), "not a registered PromptSource")
        bad(lambda a: a["search"].__setitem__("instructions", {"enabled": True, "propose": {"role": "guide"}}),
            "needs the model role")
        bad(lambda a: a["search"].__setitem__("operators", "domain"), "a mapping")
        bad(lambda a: a.__setitem__("knowledge", {"root": "x"}), "a string")
        bad(lambda a: a.__setitem__("task", {"context": "missing.md"}), "no file")


class Numeric(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="adir_num_"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _run(self, backend, iterations=8):
        inst = load(NUMERIC, run_dir_override=str(self.tmp / backend),
                    search_override={"backend": backend})
        run = inst.run_dir
        do_check(inst, run, quiet=True)
        do_seeds(inst, run, quiet=True)
        res = do_run(inst, run, iterations=iterations)
        recs = inst.archive(run).records()
        children = [r for r in recs if not r["is_seed"]]
        self.assertGreaterEqual(len(children), iterations // 2, res)
        self.assertTrue(all(r["declarations"]["vars"].get("algo") in ("fast", "small") for r in children))
        for r in children:
            v = r["declarations"]["vars"]
            self.assertEqual("algo.k" in v, v.get("algo") == "fast", "the conditional child follows its parent")
        return res, children

    @unittest.skipUnless(HAS_SMAC, "smac is not installed")
    def test_smac(self):
        res, children = self._run("smac")
        self.assertEqual(res["stopped_by"], "iterations")

    @unittest.skipUnless(HAS_PYMOO, "pymoo is not installed")
    def test_nsga2(self):
        res, children = self._run("nsga2", iterations=12)
        self.assertGreaterEqual(res["iterations"], 8)

    def test_backend_override_check(self):
        inst = load(NUMERIC, run_dir_override=str(self.tmp / "x"), search_override={"backend": "grid"})
        self.assertEqual(inst.backend, "grid")


if __name__ == "__main__":
    unittest.main()


class MalformedProgram(unittest.TestCase):
    """A program the parser refuses becomes a hard-failure record with
    the reason as feedback, not an evaluator exception."""

    def test_record(self):
        import shutil
        import tempfile
        from adir.cli import do_check, do_seeds
        from adir.evaluate_entry import evaluate_program
        from adir.instance import load
        tmp = Path(tempfile.mkdtemp(prefix="adir_bad_"))
        try:
            inst = load(YAML, run_dir_override=str(tmp))
            do_check(inst, tmp, quiet=True)
            do_seeds(inst, tmp, quiet=True)
            bad = tmp / "bad.py"
            bad.write_text("def f(x):\n    return x\n")
            from unittest import mock
            from adir.errors import BindError
            # the toy artifact is not a family; a family's lost member markers are the case
            with mock.patch("adir.evaluate_entry.candidate_from_program",
                            side_effect=BindError("program", "member markers [] do not match the members")):
                r = evaluate_program(tmp, bad)
            self.assertEqual(r["metrics"]["combined_score"], 0.0)
            self.assertEqual(r["metrics"]["feasible"], 0)
            self.assertIn("error_message", r["metrics"])
            recs = inst.archive(tmp).records()
            last = recs[-1]
            self.assertTrue(last["hard_fail"])
            self.assertIn("program", last["feedback"])
            self.assertTrue((tmp / "programs" / f"{last['candidate_id']}.py").is_file())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class DecisionsOnly(unittest.TestCase):
    """An undeclared active decision stands at its default; the `kinds`
    depth lists top-level decisions only; `show: path` names the program
    file instead of inlining it."""

    def setUp(self):
        import tempfile
        self.tmp = Path(tempfile.mkdtemp(prefix="adir_dec_"))
        from adir.instance import load
        self.inst = load(YAML, run_dir_override=str(self.tmp))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_defaults_fill(self):
        from adir.declaration import Declaration, check_declaration
        decl = Declaration(vars={"algo": "fast"}, present=True)      # algo.k exists under fast
        outs = check_declaration(self.inst, decl, self.inst.ctx(declaration=decl))
        self.assertTrue(outs["ok"], outs["detail"])
        self.assertEqual(outs["decl.algo"], "fast")
        self.assertIn("algo.k", outs["defaulted"])
        self.assertEqual(outs["decl.algo.k"], self.inst.bindings["algo.k"].domain.default())
        self.assertIn("at defaults", outs["detail"])

    def test_kinds_depth(self):
        from adir.composer import _decision_lines
        lines = _decision_lines(self.inst, "kinds")
        text = "\n".join(lines)
        self.assertIn("`lane.*.style` (2 instances): x, y", text)
        self.assertNotIn("* under ", text, "the kinds depth lists no choices under a member")
        self.assertIn("1 choice under its members", text)
        self.assertLess(len(lines), 12, lines)

    def test_show_path(self):
        import random
        from adir.cli import do_check, do_seeds
        from adir.composer import compose, MARK_CURRENT, MARK_INSPIRATIONS, MARK_ATTEMPTS, MARK_END_BACKEND
        inst = self.inst
        inst.search["context"] = {"programs": 1}     # show defaults to path
        do_check(inst, self.tmp, quiet=True)
        do_seeds(inst, self.tmp, quiet=True)
        seeds = [r for r in inst.archive(self.tmp).records() if r["is_seed"]]
        fake = (f"{MARK_CURRENT}\ncandidate_id: {seeds[0]['candidate_id']}\n{MARK_INSPIRATIONS}\n"
                f"candidate_id: {seeds[1]['candidate_id']}\n{MARK_ATTEMPTS}\nNo previous attempts yet.\n{MARK_END_BACKEND}\n")
        _, user, side = compose(inst, self.tmp, fake, random.Random(0))
        self.assertIn("The program is the file `", user)
        self.assertIn("mutable regions: `compute` (lines ", user)
        self.assertNotIn("EVOLVE-BLOCK", user, "the program text is not inlined under show: path")
        self.assertEqual(side["prompt_config"]["show"], "path")


class Discover(unittest.TestCase):
    """`seeds.discover: N` asks the discover role for plans, keeps the
    ones `plan_seed` accepts and runs them as seeds; a candidate whose
    declaration asks for a replan is re-rendered through `replan`."""

    def setUp(self):
        import tempfile
        self.tmp = Path(tempfile.mkdtemp(prefix="adir_disc_"))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_discover_and_replan(self):
        import json
        from adir.cli import do_check, do_seeds
        from adir.instance import load
        from adir.evaluate import replan_program
        from adir.errors import BindError
        inst = load(YAML, run_dir_override=str(self.tmp))
        inst.search["seeds"]["discover"] = 2
        inst.search["models"]["discover"] = {"agent": "claude", "model": "m"}
        asked = {}

        def ask(system, user):
            asked["system"], asked["user"] = system, user
            return ("Two plans.\n```json\n" + json.dumps({"plans": {
                "wide_k": {"algo": "fast", "k": 5, "why": "a wider k"},
                "tiny": {"algo": "small", "why": "the small body"},
                "bad": {"algo": "nope", "why": "rejected"},
                "baseline": {"algo": "fast", "k": 2, "why": "a taken name"}}}) + "\n```\n")
        do_check(inst, self.tmp, quiet=True)
        recs = do_seeds(inst, self.tmp, quiet=True, discover_ask=ask)
        self.assertIn("## The plan grammar", asked["user"])
        self.assertIn("Propose exactly 2 plans", asked["user"])
        self.assertTrue(asked["system"].startswith("## Conduct"), "the system text opens with the conduct: no title, no role in the toy")
        names = [r["seed_name"] for r in recs]
        self.assertIn("wide_k", names)
        self.assertIn("tiny", names)
        self.assertNotIn("bad", names)
        d = json.loads((self.tmp / "discovered.json").read_text())
        self.assertEqual(set(d["plans"]), {"wide_k", "tiny"})
        self.assertIn("bad", d["rejected"])
        self.assertIn("baseline", d["rejected"])
        wide = next(r for r in recs if r["seed_name"] == "wide_k")
        self.assertEqual(wide["declarations"]["vars"]["algo.k"], 5)
        # a replan: the candidate keeps its block, the body is re-rendered
        base = next(r for r in recs if r["seed_name"] == "baseline")
        parent_program = (self.tmp / "programs" / "seed_baseline.py").read_text()
        program = parent_program.replace("# NOTE seed baseline", "# NOTE replan\n# VAR algo.k=7").replace("# VAR algo.k=2\n", "")
        new = replan_program(inst, program, base, parent_program)
        self.assertIsNotNone(new)
        self.assertIn("z = y * 4", new, "the fast body of the plan replaced the parent's body")
        self.assertIn("VAR algo.k=7", new, "the candidate's declarations stay")
        self.assertIn("NOTE replanned", new)
        self.assertIsNone(replan_program(inst, parent_program, base, parent_program))
        # the bind check
        inst.search["models"].pop("discover")
        with self.assertRaises(BindError):
            from adir.instance import _bind_search
            _bind_search(inst, {"search": inst.search})


class AgentDirectory(unittest.TestCase):
    """The prompts name the agent's directory alone: per call a directory
    with copies of the knowledge base, the parent's program and the
    context programs, and the long sections of the prompt as files under
    `context/`; every prompt is logged by default; the discover role can
    author the task brief."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="adir_ws_"))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_workspace_and_logging(self):
        import random
        from adir.cli import do_check, do_seeds
        from adir.composer import compose, agent_dir, MARK_CURRENT, MARK_INSPIRATIONS, MARK_ATTEMPTS, MARK_END_BACKEND
        from adir.instance import load
        inst = load(YAML, run_dir_override=str(self.tmp))
        inst.search["context"] = {"programs": 1}
        inst.search["prompts"].pop("log", None)               # the default
        self.assertEqual(inst.agent_dir, self.tmp / "agent")
        do_check(inst, self.tmp, quiet=True)
        do_seeds(inst, self.tmp, quiet=True)
        seeds = [r for r in inst.archive(self.tmp).records() if r["is_seed"]]
        fake = (f"{MARK_CURRENT}\ncandidate_id: {seeds[0]['candidate_id']}\n{MARK_INSPIRATIONS}\n"
                f"candidate_id: {seeds[1]['candidate_id']}\n{MARK_ATTEMPTS}\nNo previous attempts yet.\n{MARK_END_BACKEND}\n")
        system, user, side = compose(inst, self.tmp, fake, random.Random(0))
        from adir.confine import SUBMISSION_NOTE
        self.assertIn(SUBMISSION_NOTE, system)             # one prompt, one submission, one evaluation
        ws = Path(side["workspace"])
        self.assertTrue(ws.is_dir() and ws.parent == agent_dir(inst))
        prog = ws / "program.py"
        self.assertTrue(prog.is_file() and not prog.is_symlink(), "the program is a copy, not a link")
        self.assertEqual(prog.read_text(), (self.tmp / "programs" / "seed_baseline.py").read_text())
        ctx = ws / "context" / f"{seeds[1]['candidate_id']}.py"
        self.assertTrue(ctx.is_file() and not ctx.is_symlink(), "a context program is a copy, not a link")
        self.assertIn("The program is the file `program.py`", user)
        self.assertIn(f"This call's directory is `{ws}`", user)
        self.assertNotIn(str(self.tmp / "programs"), user, "the run directory is not named")
        # the long sections are files of the directory, indexed in the prompt
        self.assertIn(f"`context/{seeds[1]['candidate_id']}.md`", user)
        self.assertTrue((ws / "context" / f"{seeds[1]['candidate_id']}.md").is_file())
        self.assertIn("`context/parent.md`", user)
        self.assertIn("Declarations:", (ws / "context" / "parent.md").read_text())
        self.assertIn("## Files of this call", system)
        self.assertIn("`context/decisions.md`", system)
        self.assertIn("## The decisions open to you", (ws / "context" / "decisions.md").read_text())
        self.assertNotIn("## The decisions open to you", system, "the decisions are a file, not inline text")
        self.assertIn("`context/seeds.md`", system)
        self.assertNotIn("## Seeds", system)
        self.assertTrue(Path(side["prompt_file"]).is_file(), "prompts are logged by default")
        self.assertIn("# System", Path(side["prompt_file"]).read_text())

    def test_role_and_task_script(self):
        """The system text opens with the role (a file or a script named
        in the run file), then the conduct, then the task (a script that
        renders from the instance); a missing file or script is a bind
        error."""
        from adir.composer import system_text
        from adir.errors import BindError
        from adir.instance import load, _bind_knowledge_and_task
        inst = load(YAML, run_dir_override=str(self.tmp))
        role = self.tmp / "role.md"
        role.write_text("# Role\n\nYou design boxes and you read every number.\n")
        script = self.tmp / "task_gen.py"
        script.write_text("def render(instance):\n"
                          "    return '# A box\\n\\nA box of ' + str(len(instance.bindings)) + ' bindings.\\n'\n")
        _bind_knowledge_and_task(inst, {"role": {"file": str(role)}, "task": {"script": str(script)}})
        text = system_text(inst)
        self.assertTrue(text.startswith("## Your role\n\nYou design boxes"), text[:80])
        heads = [l for l in text.splitlines() if l.startswith("## ")]
        self.assertEqual(heads[:3], ["## Your role", "## Conduct", "## Task"])
        self.assertIn("A box of", text)
        self.assertNotIn("# A box", text, "the script's own heading is dropped; the section has one")
        self.assertNotIn("toy.Box", text.split("## Task")[0])
        self.assertEqual(system_text(inst), text, "the same system text for every call")
        with self.assertRaises(BindError):
            _bind_knowledge_and_task(inst, {"role": {"file": str(self.tmp / "missing.md")}})
        with self.assertRaises(BindError):
            _bind_knowledge_and_task(inst, {"task": {"script": str(self.tmp / "missing.py")}})
        with self.assertRaises(BindError):
            _bind_knowledge_and_task(inst, {"task": {"script": "not-a-script"}})

    def test_take_sidecar_prefers_newest_answered(self):
        """Among pending sidecars the newest answered call is the one
        whose program the evaluator holds; unanswered calls are still in
        flight and an older answered one produced no program."""
        import json
        import time
        from adir.prompts import take_sidecar, mark_answered, pending_sidecars
        calls = self.tmp / "calls"
        calls.mkdir()
        now = time.time()
        old_unanswered = calls / "1-a.json"
        old_unanswered.write_text(json.dumps({"parent_id": "p1", "tactic_id": "t:1", "time": now - 300}))
        old_answered = calls / "2-b.json"
        old_answered.write_text(json.dumps({"parent_id": "p1", "tactic_id": "t:2", "time": now - 200}))
        mark_answered(old_answered)
        new_answered = calls / "3-c.json"
        new_answered.write_text(json.dumps({"parent_id": "p2", "tactic_id": "t:3", "time": now - 100}))
        time.sleep(0.01)
        mark_answered(new_answered)
        newest_unanswered = calls / "4-d.json"
        newest_unanswered.write_text(json.dumps({"parent_id": "p3", "tactic_id": "t:4", "time": now}))
        self.assertEqual(len(pending_sidecars(self.tmp)), 4)
        side = take_sidecar(self.tmp)
        self.assertEqual(side["tactic_id"], "t:3")
        self.assertFalse(new_answered.exists())
        self.assertTrue(old_unanswered.exists() and old_answered.exists() and newest_unanswered.exists())
        side = take_sidecar(self.tmp)
        self.assertEqual(side["tactic_id"], "t:2", "the next evaluation takes the remaining answered call")
        side = take_sidecar(self.tmp)
        self.assertEqual(side["tactic_id"], "t:1", "without an answered call, the oldest pending one")

    def test_task_brief(self):
        from adir.cli import do_check, do_seeds
        from adir.composer import system_text
        from adir.instance import load
        from adir.errors import BindError
        inst = load(YAML, run_dir_override=str(self.tmp))
        inst.task["author"] = "discover"
        inst.task_text = "# Task\n\nThe author's notes.\n"
        inst.search["models"]["discover"] = {"agent": "claude", "model": "m"}
        asked = {}

        def ask(system, user):
            asked["user"] = user
            return "Sure.\n## Objective\nShrink the box.\n## The unit\nTwo lanes.\n## What varies\nk.\n## What the evaluation rewards and rejects\nArea; a failing check.\n## Pitfalls\nNone.\n## Where to start\nk=3.\n"
        do_check(inst, self.tmp, quiet=True)
        do_seeds(inst, self.tmp, quiet=True, discover_ask=ask)
        self.assertIn("The author's notes.", asked["user"])
        self.assertIn("## Objective", asked["user"])
        brief = (self.tmp / "task_brief.md").read_text()
        self.assertTrue(brief.startswith("## Objective"))
        self.assertNotIn("Sure.", brief)
        self.assertIn("Shrink the box.", system_text(inst))
        self.assertTrue((self.tmp / "task_brief_prompt.md").is_file())
        inst.search["models"].pop("discover")
        with self.assertRaises(BindError):
            from adir.instance import _bind_search
            _bind_search(inst, {"search": inst.search})
