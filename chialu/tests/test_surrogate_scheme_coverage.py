"""The surrogate is used only under sharing schemes it was trained on (min_per_scheme rows each)."""
import random

from chialu.surrogate_seeds import fit, scheme_trained


def _data(n):
    rng = random.Random(0)
    feats = [{"a": rng.random(), "b": rng.random()} for _ in range(n)]
    return feats, {"area_um2": [1 + f["a"] for f in feats], "delay_ps": [2 + f["b"] for f in feats]}


def test_bundle_counts_and_refuses_unseen_or_rare_schemes():
    feats, ys = _data(60)
    b = fit(feats, ys, 0, None, ["x"] * 40 + ["y"] * 15 + ["z"] * 5, 20)
    assert b["schemes"] == {"x": 40, "y": 15, "z": 5} and b["min_per_scheme"] == 20
    assert scheme_trained(b, "x")
    assert not scheme_trained(b, "y") and not scheme_trained(b, "z") and not scheme_trained(b, "never")


def test_old_bundles_without_counts_still_load():
    feats, ys = _data(20)
    assert scheme_trained(fit(feats, ys), "anything")


def test_plan_tokens_keep_multiword_rules():
    from chialu.surrogate_features import plan_tokens
    t = plan_tokens("add-none_mul-all_log-per_lane_pair-comparator_fmt-per_mode_sw-rep")
    assert t == {"add": "none", "mul": "all", "log": "per_lane", "pair": "comparator", "fmt": "per_mode", "sw": "rep"}


def test_built_vals_take_the_schemes_component():
    from chialu.surrogate_features import built_vals
    vals = {"core.subword.family": "partitioned_carry_chain", "core.subword.x": 1, "core.adder.m0.family": "a"}
    plan = {"components": {"subword": {"family": "replicated_lanes", "pin": {"y": 2}}}}
    assert built_vals(vals, plan) == {"core.subword.family": "replicated_lanes", "core.subword.y": 2,
                                      "core.adder.m0.family": "a"}
    assert built_vals(vals, None) == vals
