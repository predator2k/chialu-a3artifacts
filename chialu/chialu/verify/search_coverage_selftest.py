"""The reference microarchitectures are declarations of the plain search target."""
import random
from pathlib import Path

import yaml
from adir.backends.numeric import sample_declaration
from adir.declaration import Declaration, check_declaration
from adir.instance import Instance, _bind_variables
from chialu.front_seeds import declared, plan_of
from chialu.modules.alu import ALU
from chialu.modules.generators import spec_of
from chialu.targets.rtl.alu_seed import structure_manifest

ROOT = Path(__file__).resolve().parents[2]


def bind(target, overrides=None):
    inst = Instance()
    inst.template = ALU
    specs = yaml.safe_load((ROOT / target).read_text())["adir"]["variables"]
    _bind_variables(inst, {**specs, **(overrides or {})})
    return inst


def main():
    inst = bind("targets/eval/fp_alu_cmp.yaml")
    searched = {v.name for v in inst.searched()}
    assert searched == {v.name for v in inst.variable_order() if inst.bindings[v.name].time == "search"}
    assert searched == {p["name"] for p in inst.space["hyperparameters"] if p["binding_time"] == "search"}
    assert "x_form" in searched
    manifest = structure_manifest(spec_of(inst.ctx()))
    for reference in ("hardfloat", "fpnew"):
        fixed = yaml.safe_load((ROOT / f"targets/eval/fp_alu_cmp_{reference}.yaml").read_text())["adir"]["variables"]
        values = {k: v["fixed"] for k, v in fixed.items() if "fixed" in v and (k.startswith("core.") or k == "x_form") and k != "core.family"}
        assert set(values) <= searched, set(values) - searched
        result = check_declaration(inst, Declaration(vars=values, present=True), inst.ctx())
        assert result["ok"], result["detail"]
        record = {"measurements": {"declaration": {"value": result}}}
        assert declared(record)["x_form"] == "guard_round_sticky"
        plan = plan_of(record, manifest, 1)
        assert plan["options"] == {"x_form": "guard_round_sticky"}
        assert spec_of(inst.ctx(), values)["x_form"] == "guard_round_sticky"
        print(reference, len(values), "reference choices reachable")
    rng, seen, forms = random.Random(91), set(), set()
    for _ in range(64):
        values = sample_declaration(inst, rng)
        seen.update(values)
        forms.add(values["x_form"])
        for mode in range(3):
            prefix = f"core.fp_adder.m{mode}"
            if prefix + ".close_path_trigger" in values:
                assert values[prefix + ".family"] == "two_path"
            if prefix + ".far_align.family" in values:
                assert values[prefix + ".family"] in ("two_path", "delay_optimized_unified")
    for tail in ("close_path_trigger", "path_threshold", "path_select_point", "far_align.family",
                 "far_align.shifter.family", "near_lz.family", "close_norm.family"):
        assert any(f"core.fp_adder.m{mode}.{tail}" in seen for mode in range(3)), tail
    assert forms == {"exact", "guard_round_sticky"}
    # The compact representation cannot retain all stochastic rounding bits.
    from adir.errors import BindError
    try:
        bind("targets/eval/fp_alu_cmp.yaml", {"rounding": {"runtime": ["RNE", "SR"]}})
    except BindError as error:
        assert "no_sr" in str(error)
    else:
        raise AssertionError("compact X admitted with stochastic rounding")
    from chialu.plans import replan
    text, values, lines = inst.template.plan_seed(inst.ctx(), "exact", {})
    old = Declaration(vars=values, lines=lines, present=True)
    new = Declaration(vars={**values, "x_form": "guard_round_sticky"}, lines=lines, present=True)
    changed = replan(inst.ctx(), new, old)
    assert changed is not None and changed[0] != text and not changed[3]
    assert changed[1]["x_form"] == "guard_round_sticky"
    for target in ("targets/int_subword_alu.yaml", "targets/eval/fp_alu_cmp_hf.yaml", "targets/eval/fp_alu_cmp_plans.yaml"):
        other = bind(target)
        print(target, len(other.searched()), "searched variables")
    # Training and NSGA-II inference must see the same X-form feature.
    from unittest.mock import patch
    from adir.registry import underlying
    from chialu import eda
    from chialu.surrogate_features import features
    from chialu.surrogate_seeds import surrogate_numeric_file
    import tempfile
    with patch.object(eda, "estimate", lambda *a, **kw: {}):
        for form in forms:
            f = features({}, {"x_form": form}, "unshared", None, {}, {})
            assert f[f"OH__x_form__{form}"] == 1.0
    seen_values = []
    def capture(files, values, *args):
        seen_values.append(values)
        return {"OH__x_form__guard_round_sticky": 1.0}
    with patch.object(eda, "_surrogate_parts", return_value=({"names": ["OH__x_form__guard_round_sticky"]}, {})), \
         patch("chialu.surrogate_features.features", capture), \
         patch("chialu.surrogate_seeds.predict", return_value={"area_um2": [1.0], "delay_ps": [2.0]}):
        result = underlying(eda.surrogate)({}, {}, "unused", x_form="guard_round_sticky")
        assert result["ok"] and seen_values[0]["x_form"] == "guard_round_sticky", result
    with tempfile.TemporaryDirectory() as directory:
        numeric = Path(directory) / "fp.numeric.yaml"
        numeric.write_text((ROOT / "targets/eval/fp_alu_cmp.numeric.yaml").read_text())
        generated = surrogate_numeric_file(numeric, Path(directory) / "model.pkl", {})
        inputs = yaml.safe_load(generated.read_text())["adir"]["evaluate"]["nodes"]["surrogate"]["inputs"]
        assert inputs["x_form"] == "decl.x_form"
    print("fp_alu_cmp", len(searched), "searched variables; sampler covers the missing branches and both X forms")


if __name__ == "__main__":
    main()
