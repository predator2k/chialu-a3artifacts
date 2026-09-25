"""Search enumeration must open branches beyond the default family."""
import random

from adir.backends.numeric import _prune, _searched, grid_declarations, sample_declaration
from adir.declaration import Declaration, check_declaration
from adir.domains import Enum
from adir.instance import Instance
from adir.registry import Template
from adir.variables import Bindings, Variable, VariableTree


def instance():
    inst = Instance()
    inst.template = Template(name="coverage", variables=[])
    inst.tree = VariableTree([
        Variable("core.*.family", Enum(("single", "two")), ("search",), indexed_by="lanes"),
        Variable("core.*.close.family", Enum(("tree", "linear")), ("fixed", "search"),
                 indexed_by="lanes", when=("core.*.family", "two")),
        Variable("core.*.close.width", Enum((1, 2)), ("search",), indexed_by="lanes",
                 when=("core.*.close.family", "tree")),
    ], {"lanes": ["m0", "m1"]}, {"core.*": {"search": "all"},
                                    "core.m1.close.family": {"fixed": "tree"}})
    inst.bindings = Bindings(inst.tree)
    inst.bindings.bind_defaults()
    return inst


def test_all_enumeration_entry_points_cover_nested_wildcards():
    expected = {"core.m0.family", "core.m1.family", "core.m0.close.family",
                "core.m1.close.family", "core.m0.close.width", "core.m1.close.width"}
    for entry in (lambda i: i.variable_order(), lambda i: i.space, lambda i: i.searched(), _searched):
        inst = instance()
        entry(inst)
        assert {v.name for v in inst.variable_order()} == expected
        assert {p["name"] for p in inst.space["hyperparameters"]} == expected
        assert len(inst.searched()) == 5
        assert {c["child"]: c["parent"] for c in inst.space["conditions"]}["core.m0.close.width"] == "core.m0.close.family"


def test_sampler_and_grid_preserve_ancestor_activity():
    inst, rng, seen = instance(), random.Random(18), set()
    for _ in range(200):
        vals = sample_declaration(inst, rng)
        seen.update(vals)
        for lane in ("m0", "m1"):
            if vals[f"core.{lane}.family"] == "single":
                assert not any(k.startswith(f"core.{lane}.close.") for k in vals)
        assert _prune(inst, vals) == vals
        result = check_declaration(inst, Declaration(vars=vals, present=True), inst.ctx())
        assert result["ok"], result
    assert seen == {v.name for v in inst.searched()}
    grid = grid_declarations(instance(), 100)
    assert any(v.get("core.m0.close.width") == 2 for v in grid)
    assert all("core.m1.close.width" not in v for v in grid if v["core.m1.family"] == "single")


def test_declaration_rejects_child_of_inactive_fixed_parent():
    inst = instance()
    result = check_declaration(inst, Declaration(vars={"core.m1.family": "single", "core.m1.close.width": 2},
                                                present=True), inst.ctx())
    assert not result["ok"]
    assert "core.m1.close.width declared, but inactive" in result["detail"]
