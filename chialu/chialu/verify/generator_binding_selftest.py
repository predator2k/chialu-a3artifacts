"""Real ADIR binding-to-RTL checks for active decisions and core selection."""
from pathlib import Path
import tempfile

from adir.domains import Set
from adir.instance import Instance, _bind_variables
from adir.variables import _topological
from chialu.modules import generators
from chialu.modules.alu import ALU
from chialu.modules.sfu import VEC_SFU
from chialu.targets import derive
from chialu.eda import conformance


def bind(template, fixed, dynamic, runtime=None):
    fixed, runtime = dict(fixed), dict(runtime or {})
    instance = Instance()
    instance.template = template
    specifications = {}
    for variable in _topological(template.variables):
        if variable.when and (variable.parent not in fixed or not variable.condition_holds(fixed[variable.parent])):
            continue
        if variable.name in runtime:
            specifications[variable.name] = {"runtime": runtime[variable.name]}
            continue
        if variable.name not in fixed:
            fixed[variable.name] = [] if isinstance(variable.domain, Set) else variable.domain.default()
        specifications[variable.name] = {"fixed": fixed[variable.name]}
    specifications.update({"core.*": {"search": "all"}}, **dynamic)
    _bind_variables(instance, specifications)
    return instance


def expect_error(function, needle):
    try:
        function()
    except ValueError as error:
        assert needle in str(error), error
    else:
        raise AssertionError(f"explicit inactive decision was accepted: {needle}")


def verify(instance, directory):
    text = generators.core_seed(instance.ctx())
    spec = dict(generators.spec_of(instance.ctx()), n_random=32, seed=91)
    files = derive.verify_files(spec, directory)
    result = conformance(text, files)
    assert result["pass"], result
    (directory / "seed.sv").write_text(text)
    return text


def main():
    directory = Path(tempfile.mkdtemp(prefix="chialu-generator-binding-"))
    fixed = {"modes": {"count": 1, "format": "int8"}, "check_en": False}
    dynamic = {"core.adder.m0.family": {"fixed": "parallel_prefix"},
               "core.adder.m0.topology": {"fixed": "brent_kung"},
               "core.logic.m0.family": {"fixed": "alu_pg_fused"}}
    alu = bind(ALU, fixed, dynamic, {"ops": ["add", "sub", "and", "or", "xor"]})
    text = verify(alu, directory / "alu")
    assert "alu_pg_fused" in text and "brent_kung" in text
    baseline, declared, structures = generators.seed(alu.ctx(), "baseline")
    assert "alu_pg_fused" in baseline and any(any(token.startswith("group=") for token in tokens) for _, tokens in structures)

    fixed = {"modes": {"count": 1, "format": "fp16"}, "functions": "exp2", "error_budget": None,
             "reconfig_slots": 0, "check_en": False}
    dynamic = {"core.family": {"fixed": "pwl"},
               "core.segments": {"fixed": 8}}
    sfu = bind(VEC_SFU, fixed, dynamic)
    family, pins = generators.core_family_of(sfu.ctx())
    assert not any(key.startswith("range_reducer.") for key in pins)
    declared = generators.declared_vars(sfu.ctx(), "baseline", decisions_only=False)
    assert not any(key.startswith("core.range_reducer.") for key in declared)
    text = generators.core_seed(sfu.ctx())
    assert f"core.family: {family}" in text
    expect_error(lambda: generators.core_family_of(sfu.ctx(), {"core.range_reducer.family": "range_reduction"}),
                 "core.range_reducer.family")
    invalid = bind(VEC_SFU, fixed, {**dynamic, "core.range_reducer.family": {"fixed": "range_reduction"}})
    expect_error(lambda: generators.core_family_of(invalid.ctx()), "core.range_reducer.family")
    direct = bind(VEC_SFU, {**fixed, "modes": {"count": 1, "format": "fp8e4m3"}},
                  {"core.family": {"fixed": "direct_lut"}})
    assert "core.family: direct_lut" in verify(direct, directory / "sfu")
    automatic = bind(VEC_SFU, fixed, {"core.family": {"fixed": "pwl"}})
    assert generators.core_family_of(automatic.ctx())[1]["segments"] == 8
    assert generators.declared_vars(automatic.ctx(), "baseline", decisions_only=False)["core.segments"] == 8
    narrowed = bind(VEC_SFU, fixed, {"core.family": {"fixed": "pwl"}, "core.segments": {"search": [1, 16]}})
    assert generators.core_family_of(narrowed.ctx())[1]["segments"] == 16
    expect_error(lambda: generators.core_family_of(automatic.ctx(), {"core.segments": 1}), "segments=1")
    invalid = bind(VEC_SFU, fixed, {"core.family": {"fixed": "pwl"}, "core.segments": {"fixed": 1}})
    expect_error(lambda: generators.core_family_of(invalid.ctx()), "segments=1")
    from chialu.verify.alu_ref import normalize_spec
    from chialu.verify.variant_selftest import check_seed
    spec = normalize_spec({"unit": "alu", "dut_name": "alu_core", "modes": [{"count": 1, "format": "fp16"}, {"count": 1, "format": "bf16"}],
                           "ops": ["fadd", "fmul"], "sr_bits": 1, "rounding": ["RNE", "SR"]})
    result = check_seed(spec, {f"core.rounder.m{index}": ("shared_across_formats", {}) for index in range(2)},
                        directory / "scalar_rounder_word", 48, 99)
    assert result["pass"], result
    print(f"PASS ADIR ALU/SFU generation, baseline PG sharing, explicit inactive decisions; {directory}")


if __name__ == "__main__":
    main()
