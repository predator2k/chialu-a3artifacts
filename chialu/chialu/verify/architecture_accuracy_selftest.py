"""Separate algorithm correctness from a user's mathematical error budget."""
from pathlib import Path
import re
import tempfile

from chialu.verify.errors import Budget, ErrorReport
from chialu.verify.formats import NAN, parse_format


def main():
    fmt = parse_format("fp16")
    report = ErrorReport()
    report.add(fmt, fmt.round(1), fmt.encode_special(NAN))
    assert not Budget([("max_ulp", "<=", 1)]).verdict(report)[0]
    assert Budget([("error_rate", "<=", 1)]).verdict(report)[0]
    from chialu.targets.rtl.families.dot import dot_family_requirements
    from chialu.verify.variant_selftest import check_seed
    from chialu.targets.derive import verify_files
    from chialu.verify.dot_ref import dot_layout
    from chialu.eda import conformance
    out = Path(tempfile.mkdtemp(prefix="chialu-architecture-budget-"))
    family, pins = "bf16_fma_datapath", {"rounding_mode": "round_to_odd"}
    target = dot_family_requirements(family, pins)["spec"]
    target["flags"] = ["invalid", "overflow", "underflow", "inexact", "denormal"]
    strict = dict(target, budget={"max_ulp": 0})
    result = check_seed(strict, (family, pins), out / "tight", 48, 53)
    assert result["algorithm_pass"] is True and result["budget_pass"] is False and result["pass"] is False, result
    loose = dict(target, budget={"max_ulp": 2})
    result = check_seed(loose, (family, pins), out / "loose", 48, 53)
    assert result["algorithm_pass"] is True and result["budget_pass"] is True and result["pass"] is True, result
    source = (out / "loose" / "seed.sv").read_text()
    source = re.sub(r"\bmodule\s+dot_core\b", "module original_dot", source, count=1)
    layout = dot_layout(target)
    ports = layout["core_in"] + layout["core_out"]
    declarations = ", ".join(f"{'input' if port.direction == 'in' else 'output'} wire [{port.width-1}:0] {port.name}" for port in ports)
    connections = ", ".join(f".{port.name}({'correct_d' if port.name == 'd' else port.name})" for port in ports)
    width = layout["d_w"]
    source += f"\nmodule dot_core({declarations}); wire [{width-1}:0] correct_d;\n" \
              f"original_dot original({connections}); assign d = correct_d ^ {width}'d1; endmodule\n"
    mutation_spec = dict(target, n_random=48, seed=53, budget={"max_ulp": 10**20})
    files = verify_files(mutation_spec, out / "mutation")
    assert "expected.hex" in files
    result = conformance(source, files)
    assert result["pass"] is False and result["algorithm_pass"] is False and result["budget_pass"] is None, result
    print(f"PASS algorithm/quality gates, loose-budget mutation rejection and special-value bounds: {out}")


if __name__ == "__main__":
    main()
