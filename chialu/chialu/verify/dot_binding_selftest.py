"""Exercise ADIR's two binding phases for a frozen dot architecture and budget."""
from pathlib import Path
import tempfile

from adir.domains import Set
from adir.instance import Instance, _bind_variables
from adir.variables import _topological
from chialu.modules.dot import VEC_DOT_ACC, spec_from_bindings
from chialu.modules import generators
from chialu.verify.variant_selftest import check_seed


def bindings_for(architecture, *, budget=None):
    instance = Instance()
    instance.template = VEC_DOT_ACC
    fixed = {"modes": {"elements": 4, "format_ab": "fp4e2m1", "format_c": "fp4e2m1", "format_d": "fp4e2m1"},
             "dot_contract": "architecture", "dot_architecture": architecture, "error_budget": budget,
             "accumulate": True}
    if architecture["family"] == "mixed_precision_cascade_fma":
        fixed["modes"]["elements"] = 1
    specifications = {}
    for variable in _topological(VEC_DOT_ACC.variables):
        if variable.when and (variable.parent not in fixed or not variable.condition_holds(fixed[variable.parent])):
            continue
        if variable.name not in fixed:
            fixed[variable.name] = [] if isinstance(variable.domain, Set) else variable.domain.default()
        specifications[variable.name] = {"fixed": fixed[variable.name]}
    specifications["core.*"] = {"search": "all"}
    return instance, specifications


def main():
    out = Path(tempfile.mkdtemp(prefix="chialu-dot-binding-"))
    architecture = {"family": "tensor_core_mixed_precision_mac", "pins": {"dot_width_per_pe": 4}}
    instance, specifications = bindings_for(architecture)
    _bind_variables(instance, specifications)
    target = spec_from_bindings(instance.bindings)
    target["dut_name"] = "dot_core"
    assert target.get("budget") is None
    assert target["dot_architecture"]["pins"]["subnormal_support"] is True
    selected = generators.core_family_of(instance.ctx())
    result = check_seed(target, selected, out / "tensor", 32, 97)
    assert result["pass"], result
    conflict, supplied = bindings_for(architecture)
    supplied["core.dot_width_per_pe"] = {"fixed": 8}
    try:
        _bind_variables(conflict, supplied)
    except ValueError:
        pass
    else:
        raise AssertionError("a core choice changed the frozen architecture contract")
    expansion = {"family": "mixed_precision_cascade_fma", "pins": {
        "two_term_expansion_output": True, "error_term_ops": "both"}}
    instance, specifications = bindings_for(expansion, budget={"max_ulp": 2})
    _bind_variables(instance, specifications)
    interface = "\n".join(instance.elaboration.info["interface"])
    assert all(name in interface for name in ("d_error", "d_add_error", "d_mul_error"))
    assert spec_from_bindings(instance.bindings)["budget"] == {"max_ulp": 2}
    print(f"PASS ADIR architecture binding, no-budget mode, contract conflict and expansion ports; {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
