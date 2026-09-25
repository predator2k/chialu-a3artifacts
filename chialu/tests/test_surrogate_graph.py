"""The GNN surrogate's design graph holds the whole design (chialu.surrogate_graph).

Fast: the space is bound without the full instance load and the graphs are built without the
synthesis database; the database test (the path edges spell the estimate's delay) is marked slow."""
import copy
import json
from pathlib import Path

import pytest

from chialu.surrogate_graph import (Context, Space, build_space, cached_db, completeness, design_graph, path_delay,
                                    plan_leaves, sample_rows, scheme_tokens)

ROOT = Path(__file__).resolve().parents[1]
TARGETS = {"int_subword_alu": "targets/int_subword_alu.numeric.yaml",
           "fp_alu_cmp": "targets/eval/fp_alu_cmp.numeric.yaml"}


@pytest.fixture(scope="module")
def space():
    return Space(build_space([ROOT / f for f in TARGETS.values()], db_families=False))


@pytest.fixture(scope="module")
def designs():
    """A few realized random designs per target (the surrogate's sampler: random scheme, scheme_repair,
    front_seeds.realize), and the first rows of the int dataset where it exists."""
    out = {t: [r for r in sample_rows(ROOT / f, 4, seed=3) if r.get("plan")] for t, f in TARGETS.items()}
    ds = ROOT / "run/int_subword_alu.surrogate2/surrogate/dataset.jsonl"
    if ds.is_file():
        with ds.open() as f:
            out["int_subword_alu"] += [json.loads(next(f)) for _ in range(3)]
    return out


def graphs(space, designs, **kw):
    for t, rows in designs.items():
        ctx = Context(space, t)
        for r in rows:
            yield ctx, r, design_graph(ctx, r["vals"], r["scheme"], r["plan"], with_db=False, with_estimate=False, **kw)


def test_scheme_tokens_keep_underscored_rules():
    assert scheme_tokens("add-none_mul-all_log-per_lane_pair-comparator_sw-pcc") == {
        "add": "none", "mul": "all", "log": "per_lane", "pair": "comparator", "sw": "pcc"}


def test_every_design_is_complete(space, designs):
    n = 0
    for ctx, r, g in graphs(space, designs):
        assert completeness(g, ctx, r["vals"], r["plan"]) == [], r["name"]
        # every declared variable is exactly one node, `check.*` and `x_form` included
        assert set(g.var_node) == set(r["vals"])
        assert all(f"struct:{s.id}" in g.index for s in ctx.manifest)
        n += 1
    assert n >= 6
    assert any(k.startswith("check.") for _c, r, _g in graphs(space, designs) for k in r["vals"])
    assert any("x_form" in r["vals"] for _c, r, _g in graphs(space, designs))


def test_arrays_have_no_unknown_variable(space, designs):
    for ctx, r, g in graphs(space, designs):
        a = g.arrays(space)
        var = [i for i, n in enumerate(g.nodes) if n["type"] in ("slot", "choice")]
        assert a["x_cat"].shape == (len(g.nodes), len(a["cat_fields"]))
        assert a["edge_index"].shape[1] == len(g.edges)
        assert (a["x_cat"][var, 1] > 0).all() and (a["x_cat"][var, 3] > 0).all()     # gpath and value ids


def test_losses_are_reported(space, designs):
    ctx, r, g = next(iter(graphs(space, designs)))
    # a variable node removed from the graph
    name = sorted(r["vals"])[0]
    g2 = copy.deepcopy(g)
    del g2.index[f"var:{name}"]
    g2.nodes[g2.var_node.pop(name)]["type"] = "gone"
    assert any(x.startswith(f"variable dropped: {name}") for x in completeness(g2, ctx, r["vals"], r["plan"]))
    # a plan field the builder does not know
    plan = copy.deepcopy(r["plan"])
    plan["novel"] = {"thing": 1}
    assert "plan entry not encoded: plan.novel.thing" in completeness(g, ctx, r["vals"], plan)
    # a value outside the declared space
    vals = dict(r["vals"])
    k = next(k for k in vals if k.endswith(".family"))
    vals[k] = "no_such_family"
    g3 = design_graph(ctx, vals, r["scheme"], r["plan"], with_db=False, with_estimate=False)
    assert any(x.startswith("value outside the declared space") for x in completeness(g3, ctx, vals, r["plan"]))


def test_plan_leaves_walk_every_field():
    plan = {"why": "x", "structures": {"m0.l0.adder": {"family": "f", "pin": {"a.b": 1, "c": {"d": 2}}}},
            "shared": {"g": {"members": ["x", "y"], "why": "z"}}, "dropped": ["core.adder.m0.k"]}
    assert sorted(plan_leaves(plan)) == ["plan.dropped.core.adder.m0.k", "plan.shared.g.members",
                                         "plan.structures.m0.l0.adder.family", "plan.structures.m0.l0.adder.pin.a.b",
                                         "plan.structures.m0.l0.adder.pin.c.d"]


@pytest.mark.slow
def test_path_edges_spell_the_estimate(space, designs):
    """With the database: the longest mode path over the path edges is the estimate's raw delay."""
    with cached_db():
        for t, rows in designs.items():
            ctx = Context(space, t)
            for r in rows[:2]:
                g = design_graph(ctx, r["vals"], r["scheme"], r["plan"])
                assert completeness(g, ctx, r["vals"], r["plan"]) == []
                assert abs(path_delay(g) - g.meta["estimate"]["raw_delay_ps"]) < 0.5


def test_model_adapter_exports_complete_graphs_without_torch(space, designs, monkeypatch, tmp_path):
    """Training/node graph adapter preserves the complete declared-space vocabulary."""
    import numpy as np
    from chialu import surrogate_graph
    from chialu.surrogate_gnn import graph_input
    from chialu.surrogate_gnn_pack import pack
    original = surrogate_graph.design_graph
    monkeypatch.setattr(surrogate_graph, 'design_graph',
                        lambda *a, **kw: original(*a, **kw, with_db=False, with_estimate=False))
    for target, rows in designs.items():
        ctx = Context(space, target)
        r = rows[0]
        graph = graph_input(space.d, ctx.files, r['vals'], r['scheme'], r['plan'], ctx.est)
        assert graph['meta']['vocab_sizes']['value'] == len(space.vocab['value']) + 1
        pack([graph], np.log([[100, 106]]), tmp_path / 'one.npz')
        with np.load(tmp_path / 'one.npz') as data:
            assert len(data['x_cat']) == len(graph['x_cat'])
            assert data['level'].max() > 0
