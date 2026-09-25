"""The SkyDiscover binding over the toy domain: the generated config
loads as a SkyDiscover Config, and a run with a stub model client goes
through SkyDiscover's controller, ADIR's evaluator entry, the prompt
sampling and the archive. Skipped without the skydiscover package."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

try:
    import skydiscover  # noqa: F401
    HAS_SD = True
except ImportError:
    HAS_SD = False

from adir.cli import do_check, do_seeds  # noqa: E402
from adir.instance import load  # noqa: E402

YAML = HERE / "toy_run.yaml"

DIFF = """The body shrinks, so the area falls.

<<<<<<< SEARCH
    return y * 2 + 1
=======
    return y * 2
>>>>>>> REPLACE
"""

DIFF2 = """Drop the temporary.

<<<<<<< SEARCH
    y = helper(x)
    return y * 2
=======
    return helper(x) * 2
>>>>>>> REPLACE
"""


class StubClient:
    """Returns a diff on the seed, then a second diff, then a no-op."""

    def __init__(self, spec, role):
        self.spec = spec
        self.role = role
        self.calls = []

    async def generate(self, system_message, messages, **kwargs):
        user = messages[0]["content"]
        self.calls.append((system_message, user))
        if "return y * 2 + 1" in user:
            return DIFF
        if "    y = helper(x)\n    return y * 2\n" in user:
            return DIFF2
        return "nothing to change\n"


@unittest.skipUnless(HAS_SD, "skydiscover is not installed")
class Binding(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="adir_sd_"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_config_loads(self):
        from skydiscover.config import Config
        inst = load(YAML, run_dir_override=str(self.tmp))
        do_check(inst, self.tmp, quiet=True)
        cfg = Config.from_yaml(self.tmp / "skydiscover.yaml")
        self.assertEqual(cfg.search.type, "adaevolve")
        self.assertEqual(cfg.max_iterations, 5)
        self.assertEqual(cfg.file_suffix, ".py")
        self.assertFalse(cfg.evaluator.cascade_evaluation)
        self.assertEqual(cfg.llm.models[0].name, "test-model")
        self.assertEqual(cfg.search.database.num_islands, 2)
        self.assertTrue(cfg.prompt.system_message.startswith("## Conduct"), "the system text opens with the conduct: no title, no role in the toy")
        self.assertTrue((self.tmp / "prompt_templates" / "diff_user.txt").is_file())

    def test_set_aside_database(self):
        """A database left at db_path is renamed before the controller is
        built; an empty or absent one is left alone."""
        from types import SimpleNamespace
        from adir.backends import skydiscover as sd
        out = self.tmp / "skydiscover"
        db = out / "db"
        cfg = SimpleNamespace(search=SimpleNamespace(database=SimpleNamespace(db_path=str(db))))
        self.assertIsNone(sd.set_aside_database(cfg, out))
        db.mkdir(parents=True)
        self.assertIsNone(sd.set_aside_database(cfg, out), "an empty directory stays")
        (db / "programs.json").write_text("{}")
        moved = sd.set_aside_database(cfg, out)
        self.assertIsNotNone(moved)
        self.assertTrue(moved.name.startswith("db."))
        self.assertTrue((moved / "programs.json").is_file())
        self.assertFalse(db.exists())
        self.assertIsNone(sd.set_aside_database(cfg, out))

    def test_second_run_same_dir(self):
        """`adir run` twice in one run directory: the second run starts
        from the seeds again rather than failing on the database the
        first run persisted."""
        from adir.backends import skydiscover as sd
        inst = load(YAML, run_dir_override=str(self.tmp))
        do_check(inst, self.tmp, quiet=True)
        do_seeds(inst, self.tmp, quiet=True)
        clients = lambda spec, role: StubClient(spec, role)  # noqa: E731
        first = sd.run(inst, self.tmp, iterations=1, clients=clients)
        second = sd.run(inst, self.tmp, iterations=1, clients=clients)
        self.assertGreater(second["records"], first["records"], (first, second))
        seeds = [r for r in inst.archive(self.tmp).records() if r["is_seed"]]
        self.assertEqual(len(seeds), len({r["seed_name"] for r in seeds}),
                         "the backend's evaluation of its initial program adds no second seed row")

    def test_stub_run(self):
        from adir.backends import skydiscover as sd
        inst = load(YAML, run_dir_override=str(self.tmp))
        do_check(inst, self.tmp, quiet=True)
        do_seeds(inst, self.tmp, quiet=True)
        stubs = []

        def clients(spec, role):
            c = StubClient(spec, role)
            stubs.append(c)
            return c
        res = sd.run(inst, self.tmp, iterations=3, clients=clients)
        recs = inst.archive(self.tmp).records()
        children = [r for r in recs if not r["is_seed"]]
        self.assertGreaterEqual(len(children), 1, res)
        self.assertTrue(all(r["iteration"] >= 1 for r in children))
        self.assertTrue(any(r["parent_id"] for r in children), "the sidecar carries the parent")
        called = [c for c in stubs if c.calls]
        self.assertTrue(called, "the stub model was called")
        system, user = called[0].calls[0]
        self.assertTrue(system.startswith("## Conduct"), system[:80])
        self.assertNotIn("# toy.Box", system, "no title: the template's name is not what the model needs first")
        self.assertIn("`context/toy_notes.md`", system, "a static PromptSource is a file of the call directory, indexed in the system text")
        self.assertIn("## Current program", user)
        self.assertIn("EVOLVE-BLOCK", system)
        self.assertIn("## Operator:", user)
        self.assertIn("`context/toy_plan.md`", user, "a per-round PromptSource is a file of the call directory, indexed in the user text")
        calls = [d for d in (self.tmp / "agent").iterdir() if d.is_dir()]
        self.assertTrue(any((d / "context" / "toy_notes.md").is_file() and "## Toy notes" in (d / "context" / "toy_notes.md").read_text()
                            for d in calls), "the static source's file holds its text")
        self.assertTrue(any((d / "context" / "toy_plan.md").is_file() and "## Plan of the parent" in (d / "context" / "toy_plan.md").read_text()
                            for d in calls), "the per-round source's file holds its text")
        self.assertFalse(any(p.is_symlink() for d in calls for p in d.rglob("*")), "the call directories hold copies alone")
        self.assertIn("## Response", user)
        self.assertTrue(all(r.get("prompt_config") for r in children), "every child records its prompt_config")
        knobs = {r["prompt_config"]["operator"] for r in children}
        self.assertTrue(knobs <= {"structural", "local", "free"})
        best = max(children, key=lambda r: r["score"]["combined_score"])
        self.assertGreater(best["score"]["combined_score"], 1.0, "a shorter body scores above the seed")
        summary = json.loads((self.tmp / "summary.json").read_text())
        self.assertGreaterEqual(summary["llm_calls"], 1)
        self.assertTrue((self.tmp / "skydiscover" / "logs").is_dir())


if __name__ == "__main__":
    unittest.main()
