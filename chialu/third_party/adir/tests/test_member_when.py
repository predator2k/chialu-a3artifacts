"""Member conditions (design section 3.4): a member admissible under a
sibling's value, at the loader, the lazy bindings, the declaration
check, the prompt and the numeric backends, over the toy `Cond`
template."""
from __future__ import annotations

import random
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

from adir import BindError  # noqa: E402
from adir.backends.numeric import _prune, grid_declarations, sample_declaration  # noqa: E402
from adir.cli import do_check, do_seeds  # noqa: E402
from adir.composer import _structural, system_text  # noqa: E402
from adir.declaration import Declaration, check_declaration  # noqa: E402
from adir.domains import Enum  # noqa: E402
from adir.instance import load, template_identity  # noqa: E402
from adir.prompts import unexplored_values  # noqa: E402
from adir.variables import (ABSENT, OPEN, Binding, Bindings, Variable, VariableTree, _topological,  # noqa: E402
                            bind_variables, default_under, member_exclusions, space_json)

YAML = HERE / "toy_cond.yaml"


class FakeArchive:
    def __init__(self, records):
        self._records = records

    def records(self):
        return self._records


def _decl(**vars_):
    return Declaration(vars=dict(vars_), present=True)


class Templates(unittest.TestCase):
    """The variable and the tree: normalization, expansion, order, and
    the conditions the tree refuses."""

    def test_normalized_and_expanded(self):
        v = Variable("lane.*.lz", Enum(("single", "dual")), {"fixed", "search"}, indexed_by="lanes",
                     member_when={"dual": ("lane.*.order", "each")})
        self.assertEqual(v.member_when, {"dual": ("lane.*.order", ("each",), "")})
        self.assertEqual(v.siblings, ["lane.*.order"])
        l1 = v.expand(["l0", "l1"])[1]
        self.assertEqual(l1.name, "lane.l1.lz")
        self.assertEqual(l1.member_when["dual"][0], "lane.l1.order")

    def test_refused_forms(self):
        with self.assertRaises(BindError) as cm:
            Variable("a", Enum(("p", "q")), member_when={"z": ("b", ("x",))})
        self.assertIn("outside", str(cm.exception))
        with self.assertRaises(BindError) as cm:
            Variable("a", Enum(("p", "q")), member_when={"p": ("b", ("x",)), "q": ("b", ("y",))})
        self.assertIn("`when`", str(cm.exception))
        with self.assertRaises(BindError):
            Variable("a", Enum(("p", "q")), member_when={"p": ("b", ())})

    def test_order_and_cycle(self):
        b = Variable("b", Enum(("x", "y")), {"fixed", "search"})
        a = Variable("a", Enum(("p", "q")), {"fixed", "search"}, member_when={"q": ("b", ("x",))})
        self.assertEqual([v.name for v in _topological([a, b])], ["b", "a"])
        b2 = Variable("b", Enum(("x", "y")), {"fixed", "search"}, member_when={"y": ("a", ("p",))})
        with self.assertRaises(BindError) as cm:
            VariableTree([a, b2], {}, {"a": {"search": "all"}, "b": {"search": "all"}})
        self.assertIn("cycle", str(cm.exception))

    def test_tree_refuses_unknown_and_static_on_indexed(self):
        a = Variable("a", Enum(("p", "q")), {"fixed", "search"}, member_when={"q": ("nowhere", ("x",))})
        with self.assertRaises(BindError) as cm:
            VariableTree([a], {}, {"a": {"search": "all"}})
        self.assertIn("not a variable", str(cm.exception))
        s = Variable("s", Enum(("p", "q")), {"fixed", "search"}, member_when={"q": ("lane.*.o", ("x",))})
        o = Variable("lane.*.o", Enum(("x", "y")), {"fixed", "search"}, indexed_by="lanes")
        with self.assertRaises(BindError) as cm:
            VariableTree([s, o], {"lanes": ["l0"]}, {"s": {"search": "all"}, "lane.*": {"search": "all"}})
        self.assertIn("static", str(cm.exception))


class IndexSets(unittest.TestCase):
    """A child indexed over a smaller set than its indexed parent."""

    def test_child_outside_its_set_is_not_a_child(self):
        fma = Variable("fma.*.family", Enum(("separate", "fused")), {"fixed", "search"}, indexed_by="fmas")
        add = Variable("add.*.family", Enum(("ripple", "prefix")), {"fixed", "search"}, indexed_by="adders",
                       when=("fma.*.family", ("separate",)))
        tree = VariableTree([fma, add], {"fmas": ["m0", "m1", "m2"], "adders": ["m0", "m1"]},
                            {"fma.*": {"search": "all"}, "add.*": {"search": "all"}})
        self.assertEqual([c.name for c in tree.children_of("fma.m0.family")], ["add.m0.family"])
        self.assertEqual(tree.children_of("fma.m2.family"), [])
        b = Bindings(tree)
        for ix in ("m0", "m1", "m2"):
            b.materialize(f"fma.{ix}.family")
        b.bind_defaults()                  # m2 has no adder to bind, and says nothing about it
        self.assertIn("add.m1.family", b)
        self.assertNotIn("add.m2.family", b)


class Loader(unittest.TestCase):
    """A fixed or runtime binding of a conditioned member against the
    sibling's binding."""

    def setUp(self):
        self.mul = Variable("mul", Enum(("separate", "fused")), {"fixed", "search"})
        self.unpack = Variable("unpack", Enum(("in_unpack", "in_datapath")), {"fixed", "search", "runtime"},
                               member_when={"in_datapath": ("mul", ("fused",), "needs normalized operands")})

    def test_fixed_member_under_fixed_sibling(self):
        ok = bind_variables([self.unpack, self.mul], {"mul": {"fixed": "fused"}, "unpack": {"fixed": "in_datapath"}})
        self.assertEqual(ok["unpack"].value, "in_datapath")
        with self.assertRaises(BindError) as cm:
            bind_variables([self.unpack, self.mul], {"mul": {"fixed": "separate"}, "unpack": {"fixed": "in_datapath"}})
        text = str(cm.exception)
        self.assertIn("mul is one of ['fused']", text)
        self.assertIn("it is 'separate'", text)
        self.assertIn("needs normalized operands", text)

    def test_fixed_member_under_searched_or_absent_sibling(self):
        ok = bind_variables([self.unpack, self.mul], {"mul": {"search": "all"}, "unpack": {"fixed": "in_datapath"}})
        self.assertEqual(ok["unpack"].value, "in_datapath")        # open: the search decides
        gate = Variable("gate", Enum(("off", "on")), {"fixed"})
        mul = Variable("mul", Enum(("separate", "fused")), {"fixed", "search"}, when=("gate", "on"))
        with self.assertRaises(BindError) as cm:
            bind_variables([self.unpack, mul, gate], {"gate": {"fixed": "off"}, "mul*": {"search": "all"},
                                                       "unpack": {"fixed": "in_datapath"}})
        self.assertIn("mul does not exist here", str(cm.exception))

    def test_runtime_sibling_and_runtime_member(self):
        mode = Variable("mode", Enum(("x", "y")), {"fixed", "runtime"})
        pack = Variable("pack", Enum(("a", "b")), {"fixed", "search"}, member_when={"b": ("mode", ("x",))})
        with self.assertRaises(BindError) as cm:
            bind_variables([pack, mode], {"mode": {"runtime": ["x", "y"]}, "pack": {"fixed": "b"}})
        self.assertIn("selected at run time", str(cm.exception))
        ok = bind_variables([pack, mode], {"mode": {"fixed": "x"}, "pack": {"fixed": "b"}})
        self.assertEqual(ok["pack"].value, "b")
        # the conditioned variable provisioned at run time: every member must be admissible
        with self.assertRaises(BindError) as cm:
            bind_variables([self.unpack, self.mul], {"mul": {"fixed": "separate"}, "unpack": {"runtime": "all"}})
        self.assertIn("runtime:", str(cm.exception))

    def test_lookup_states(self):
        var = self.unpack
        self.assertEqual(member_exclusions(var, None, lambda n: ("search", OPEN)), {})
        self.assertIn("in_datapath", member_exclusions(var, None, lambda n: ("search", ABSENT)))
        self.assertIn("in_datapath", member_exclusions(var, None, lambda n: ("absent", None)))
        self.assertEqual(member_exclusions(var, None, lambda n: ("runtime", ["fused"])), {})
        self.assertEqual(default_under(var, None, lambda n: ("fixed", "separate")), "in_unpack")
        first = Variable("first", Enum(("cond", "plain")), {"search"}, member_when={"cond": ("mul", ("fused",))})
        self.assertEqual(default_under(first, None, lambda n: ("fixed", "separate")), "plain")
        self.assertEqual(default_under(first, None, lambda n: ("fixed", "fused")), "cond")


class Instance(unittest.TestCase):
    """The loaded toy instance: the lazy bindings, the declaration check,
    the hash, space.json, the prompt and the numeric backends."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="adir_cond_"))
        cls.inst = load(YAML, run_dir_override=str(cls.tmp))
        do_check(cls.inst, cls.tmp, quiet=True)
        cls.records = do_seeds(cls.inst, cls.tmp, quiet=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def check(self, decl):
        return check_declaration(self.inst, decl, self.inst.ctx(declaration=decl))

    def test_load_and_defaults(self):
        inst = self.inst
        self.assertIsInstance(inst.bindings, Bindings)
        self.assertEqual(inst.bindings["unpack"].domain.members(), ["in_unpack", "in_datapath"])
        # the default of a conditioned variable follows the siblings' defaults
        self.assertEqual(inst.bindings.default_of("first"), "plain")
        self.assertEqual(inst.bindings.default_of("first", {"mul": "fused"}), "cond")
        self.assertEqual(inst.bindings.default_of("unpack"), "in_unpack")
        # the seed declares nothing and its declaration is verified
        self.assertTrue(self.records and self.records[0]["declarations"]["verified"])
        self.assertEqual(self.records[0]["measurements"]["declaration"]["value"]["decl.first"], "plain")

    def test_declaration_check(self):
        r = self.check(_decl(unpack="in_datapath"))
        self.assertFalse(r["ok"])
        self.assertIn("VAR unpack='in_datapath': 'in_datapath' is admissible when mul is one of ['fused']; "
                      "it is 'separate' (a separate multiplier needs normalized operands)", r["detail"])
        r = self.check(_decl(mul="fused", unpack="in_datapath"))
        self.assertTrue(r["ok"], r["detail"])
        self.assertEqual(r["decl.unpack"], "in_datapath")
        self.assertEqual(r["decl.first"], "cond")               # the first member is admissible under fused
        # the default moves off the domain's first member and the output says so
        r = self.check(_decl())
        self.assertTrue(r["ok"], r["detail"])
        self.assertEqual(r["decl.first"], "plain")
        self.assertEqual(r["defaulted_under"]["first"], {"default": "plain", "sibling": "mul", "value": "separate"})
        self.assertIn("first defaults to 'plain' under mul='separate'", r["detail"])
        # a runtime sibling that provisions a disallowed member excludes the member
        r = self.check(_decl(pack="b"))
        self.assertFalse(r["ok"])
        self.assertIn("mode is selected at run time among ['x', 'y']", r["detail"])

    def test_indexed_and_nested(self):
        r = self.check(_decl(**{"lane.l0.lz": "dual"}))
        self.assertFalse(r["ok"])
        self.assertIn("lane.l0.order is one of ['each']; it is 'swap'", r["detail"])
        r = self.check(_decl(**{"lane.l0.order": "each", "lane.l0.lz": "dual", "lane.l0.split": "count"}))
        self.assertTrue(r["ok"], r["detail"])
        self.assertEqual(r["decl.lane.l0.split"], "count")
        self.assertNotIn("decl.lane.l1.split", r)                # the nested choice is inactive under single
        r = self.check(_decl(**{"lane.l1.split": "count"}))
        self.assertFalse(r["ok"])
        self.assertIn("VAR lane.l1.split declared, but inactive", r["detail"])
        # the sibling exists for the first two lanes alone: the last lane loses the member
        r = self.check(_decl(**{"narrow.l0.width": "w", "lane.l0.tail": "wide"}))
        self.assertTrue(r["ok"], r["detail"])
        r = self.check(_decl(**{"lane.l2.tail": "wide"}))
        self.assertFalse(r["ok"])
        self.assertIn("narrow.l2.width does not exist here", r["detail"])

    def test_fixed_member_against_a_declaration(self):
        import yaml
        doc = yaml.safe_load(YAML.read_text())
        doc["adir"]["variables"]["unpack"] = {"fixed": "in_datapath"}
        p = self.tmp / "fixed.yaml"
        p.write_text(yaml.safe_dump(doc, sort_keys=False))
        inst = load(p, run_dir_override=str(self.tmp / "fixed"))      # mul is searched: the fixed member loads
        r = check_declaration(inst, _decl(mul="separate"), inst.ctx())
        self.assertFalse(r["ok"])
        self.assertIn("fixed unpack='in_datapath'", r["detail"])
        r = check_declaration(inst, _decl(mul="fused"), inst.ctx())
        self.assertTrue(r["ok"], r["detail"])

    def test_hash_and_space_json(self):
        unpack = next(t for t in self.inst.tree.templates if t.name == "unpack")
        mul = next(t for t in self.inst.tree.templates if t.name == "mul")
        self.assertEqual(len(template_identity(mul)), 4)
        self.assertEqual(template_identity(unpack)[4], {"member_when": {"in_datapath": ["mul", ["fused"]]}})
        space = space_json(self.inst.variables, self.inst.bindings)
        forbidden = [f for f in space["forbiddens"] if f["clauses"][0]["name"] == "unpack"]
        self.assertEqual(forbidden, [{"type": "AND", "clauses": [
            {"name": "unpack", "type": "EQUALS", "value": "in_datapath"},
            {"name": "mul", "type": "IN", "values": ["separate"]}]}])
        # a run file without conditions keeps a four-field identity per template
        box = load(HERE / "toy_run.yaml", run_dir_override=str(self.tmp / "box"))
        self.assertTrue(all(len(template_identity(t)) == 4 for t in box.tree.templates))

    def test_prompt(self):
        text = system_text(self.inst, self.records)
        self.assertIn("in_datapath (when `mul` is one of [fused])", text)
        self.assertIn("dual (when `lane.*.order` is one of [each])", text)
        self.assertIn("is admissible only while that variable", text)
        parent = {"candidate_id": "p", "declarations": {"vars": {"mul": "separate"}, "lines": []}}
        lines = _structural(self.inst, parent, {"member_focus": "none"}, random.Random(0))
        joined = "\n".join(lines)
        self.assertIn("in_datapath (when `mul` is one of [fused]) (not under the parent's `mul`=separate)", joined)
        self.assertIn("`first`: cond (when `mul` is one of [fused]) (not under the parent's `mul`=separate), "
                      "plain (default)", joined)
        parent = {"candidate_id": "p", "declarations": {"vars": {"mul": "fused"}, "lines": []}}
        joined = "\n".join(_structural(self.inst, parent, {"member_focus": "none"}, random.Random(0)))
        self.assertIn("`first`: cond (default) (when `mul` is one of [fused]), plain", joined)
        recs = [{"candidate_id": "a", "declarations": {"vars": {}}, "measurements": {}}]
        out = unexplored_values(self.inst, FakeArchive(recs))
        self.assertTrue(any("`unpack`: no candidate has tried in_datapath (when `mul` is one of [fused])" in s
                            for s in out), out)

    def test_numeric_backends(self):
        rng = random.Random(1)
        for _ in range(200):
            vals = sample_declaration(self.inst, rng)
            if vals.get("unpack") == "in_datapath":
                self.assertEqual(vals["mul"], "fused")
            if vals.get("first") == "cond":
                self.assertEqual(vals["mul"], "fused")
            for lane in ("l0", "l1", "l2"):
                if vals.get(f"lane.{lane}.lz") == "dual":
                    self.assertEqual(vals[f"lane.{lane}.order"], "each")
                if f"lane.{lane}.split" in vals:          # the nested choice, where a declaration materialized it
                    self.assertEqual(vals.get(f"lane.{lane}.lz"), "dual")
            self.assertNotEqual(vals.get("lane.l2.tail"), "wide")
            self.assertNotEqual(vals.get("pack"), "b")
        repaired = _prune(self.inst, {"mul": "separate", "unpack": "in_datapath", "first": "cond", "pack": "b"})
        self.assertEqual(repaired, {"mul": "separate", "unpack": "in_unpack", "first": "plain", "pack": "a"})
        kept = _prune(self.inst, {"mul": "fused", "unpack": "in_datapath", "first": "cond"})
        self.assertEqual(kept, {"mul": "fused", "unpack": "in_datapath", "first": "cond"})
        for vals in grid_declarations(self.inst, 64):
            if vals.get("unpack") == "in_datapath" or vals.get("first") == "cond":
                self.assertEqual(vals["mul"], "fused")


if __name__ == "__main__":
    unittest.main()
