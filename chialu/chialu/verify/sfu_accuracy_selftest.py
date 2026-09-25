"""Exercise YAML accuracy priority and complete-domain SFU error reporting."""
from copy import deepcopy
from itertools import product
from pathlib import Path
import tempfile

from adir.domains import Set
from adir.instance import Instance, _bind_variables
from adir.variables import _topological

from chialu.modules.sfu import VEC_SFU
from chialu.sfu_accuracy import from_bindings
from chialu.targets.derive import spec_from_bindings
from chialu.verify.harness import build_verification
from chialu.verify.sfu_ref import normalize_sfu_spec, sfu_layout
from chialu.verify.sfu_range import complete_plan, result_of


def bound(extra=None):
    instance = Instance()
    instance.template = VEC_SFU
    fixed = {"modes": {"count": 1, "format": "fp8e4m3"}, "functions": "exp2",
             "reconfig_slots": 0, "verify.n_random": 16}
    supplied = {}
    for variable in _topological(VEC_SFU.variables):
        if variable.name == "error_budget":
            continue
        if variable.when and (variable.parent not in fixed or not variable.condition_holds(fixed[variable.parent])):
            continue
        if variable.name not in fixed:
            fixed[variable.name] = [] if isinstance(variable.domain, Set) else variable.domain.default()
        supplied[variable.name] = {"fixed": fixed[variable.name]}
    supplied.update(extra or {})
    _bind_variables(instance, supplied)
    return instance


def check_bindings():
    inst = bound()
    decision = from_bindings(inst.bindings)
    assert decision["mode"] == "search_implementation" and decision["precision_target"] == {"max_ulp": 1.0}, decision
    assert inst.bindings["core.family"].time == "search"
    inst = bound({"error_budget": {"fixed": {"max_ulp": 0.25}}})
    decision = from_bindings(inst.bindings)
    assert decision["budget_applied"] and decision["target_source"] == "user", decision
    assert decision["precision_target"] == {"max_ulp": 0.25}
    inst = bound({"core.family": {"fixed": "direct_lut"}, "error_budget": {"fixed": {"bit_exact": True}}})
    decision = from_bindings(inst.bindings)
    assert decision["mode"] == "report_error" and not decision["budget_applied"], decision
    assert spec_from_bindings("chialu.VecSFU", inst.bindings)["budget"]["bit_exact"] is True
    inst = bound({"core.family": {"search": ["direct_lut"]}})
    assert from_bindings(inst.bindings)["mode"] == "report_error"
    inst = bound({"core.family": {"fixed": "pwl"}})
    decision = from_bindings(inst.bindings)
    assert decision["mode"] == "search_parameters" and "coeff_frac_bits" in decision["unresolved_parameters"], decision
    assert decision["precision_target"] == {"max_ulp": 1.0}
    from chialu.modules.generators import core_family_of
    family, pins = core_family_of(inst.ctx())
    supplied = {"core.family": {"fixed": family}, **{"core." + name: {"fixed": value} for name, value in pins.items()}}
    fixed = bound(supplied)
    decision = from_bindings(fixed.bindings)
    assert decision["mode"] == "report_error", decision
    exact_adder = {**supplied, "core.adder.family": {"fixed": "ripple_carry"},
                   "core.adder.chunk_width_bits": {"search": [1, 2]}}
    decision = from_bindings(bound(exact_adder).bindings)
    assert decision["mode"] == "report_error" and "adder.chunk_width_bits" in decision["unresolved_parameters"], decision
    supplied["core.coeff_frac_bits"] = {"search": [12, 13]}
    decision = from_bindings(bound(supplied).bindings)
    assert decision["mode"] == "search_parameters" and decision["unresolved_accuracy_parameters"] == ["coeff_frac_bits"], decision
    shared = bound({"core.family": {"fixed": "direct_lut"}, "functions": {"runtime": ["exp2", "log2"]}})
    decision = from_bindings(shared.bindings)
    assert decision["mode"] == "report_error" and decision["unresolved_parameters"] == ["sharing"], decision


def report_spec(**extra):
    return normalize_sfu_spec({"unit": "vec_sfu", "dut_name": "sfu_core",
        "modes": [{"count": 1, "format": "fp4e2m1"}], "functions": ["exp2"],
        "budget": {"max_ulp": 0}, "n_random": 4,
        "sfu_accuracy": {"mode": "report_error", "family": "direct_lut",
                         "user_target": {"max_ulp": 0}, "precision_target": {"max_ulp": 0}}, **extra})


def check_domains(work):
    spec = report_spec(rounding=["RNE", "SR"], sr_bits=1, daz_in=[False, True], ftz_out=[False, True])
    plan, evidence = complete_plan(sfu_layout(spec))
    vectors, metadata, _, _ = plan
    expected = set(product(range(16), ("RNE", "SR"), (False, True), (False, True), range(2)))
    actual = {(m["x"], m["ctrl"]["rounding"], m["ctrl"]["daz_in"], m["ctrl"]["ftz_out"], m["words"][0])
              for m in metadata}
    assert evidence["complete"] and actual == expected and len(vectors) == len(expected)
    modes = report_spec(modes=[{"count": 2, "format": "fp4e2m1"}, {"count": 1, "format": "fp4e2m1"}])
    plan, evidence = complete_plan(sfu_layout(modes))
    assert evidence["complete"] and len(plan[0]) == 512
    assert {v["x"] for v, m in zip(plan[0], plan[1]) if m["mode"] == 1} == set(range(256))
    approximate = report_spec()
    approximate["sfu_accuracy"]["family"] = "pwl"
    ver = build_verification(approximate, work / "report")
    dump = work / "report" / "dump.hex"
    # Deliberately different numerical results test budget priority only;
    # this report does not certify their algorithm or generation fidelity.
    dump.write_text("0\n" * len(ver.expected))
    ok, violations, report = ver.check(dump)
    assert not ok and report.n_wrong and all("algorithm contract" in message for message in violations)
    assert ver.budget.verdict(report) == (True, [])
    result = result_of(ver, report)
    assert result["error_range_complete"] and not result["budget_applied"] and result["error_range"]["max_ulp"] > 0
    for text in ("0\n" * (len(ver.expected) - 1), "0\n" * (len(ver.expected) + 1),
                 "x\n" * len(ver.expected), "-1\n" * len(ver.expected), "10000\n" * len(ver.expected)):
        dump.write_text(text)
        ok, _, report = ver.check(dump)
        assert not ok and not result_of(ver, report)["error_range_complete"]
    sample = build_verification(report_spec(range_max_vectors=1), work / "sample")
    dump.write_text("\n".join(f"{word:x}" for word in sample.expected))
    ok, violations, report = sample.check(dump)
    assert not ok and any("sampled maxima" in message for message in violations)
    assert not result_of(sample, report)["error_range_complete"]
    search = deepcopy(ver.spec)
    search["sfu_accuracy"]["mode"] = "search_parameters"
    checked = build_verification(search, work / "search")
    dump.write_text("0\n" * len(checked.expected))
    assert not checked.check(dump)[0]


def check_rtl(work):
    from chialu.eda import conformance
    from chialu.targets.derive import seed_for, verify_files
    spec = report_spec()
    source = seed_for(spec, family=("direct_lut", {}))
    files = verify_files(spec, work / "rtl")
    result = conformance(source, files)
    assert result["pass"] and result["error_range_complete"], result
    assert result["budget_pass"] is None and result["algorithm_pass"] is True, result
    assert result["error_range"]["max_ulp"] == 0, result
    import re
    source = re.sub(r"\bmodule\s+sfu_core\b", "module original_sfu", source, count=1)
    source += "\nmodule sfu_core(input [3:0] x, output [3:0] y); wire [3:0] correct_y; " \
              "original_sfu original(.x(x),.y(correct_y)); assign y = correct_y ^ 4'd1; endmodule\n"
    mutation = conformance(source, files)
    assert not mutation["pass"] and mutation["algorithm_pass"] is False, mutation
    return result


def main():
    work = Path(tempfile.mkdtemp(prefix="chialu-sfu-accuracy-"))
    check_bindings()
    check_domains(work)
    result = check_rtl(work)
    print(f"PASS SFU YAML priority, full control/random/input products, incomplete-range rejection and LUT RTL: {work}")
    print(result)


if __name__ == "__main__":
    main()
