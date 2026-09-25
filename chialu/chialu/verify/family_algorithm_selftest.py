"""The generic family bench must check both algorithm fidelity and error budget."""
from dataclasses import replace
import json
from pathlib import Path
import tempfile

from chialu.targets.rtl.families.adder_ext import approximate_truncated_sv
from chialu.targets.rtl.families.selftest import run_python_case, run_case
from chialu.verify.family_ref import golden
from chialu.verify.family_tb import emit


def main():
    root = Path(tempfile.mkdtemp(prefix="chialu-family-algorithm-"))
    results = []
    bindings = [{"lower_scheme": scheme} for scheme in ("truncate_constant", "or_gates", "segmented_subadders")]
    bindings += [{"lower_scheme": "speculative_segments", "speculation_window": 2, "correction": correction}
                 for correction in ("none", "configurable_stages")]
    for index, pins in enumerate(bindings):
        selected = dict(lower_part_width=4, **pins)
        adapter = golden("adder", "approximate_truncated", selected, 16)
        name = f"approx_{index}"
        source = approximate_truncated_sv(16, selected, name)
        status = run_python_case("", name, emit(name, {}, adapter, 1500, 19), root, source)
        assert status.endswith(": PASS"), status
        results.append(dict(pins=selected, pass_both=True, detail=status))
    # A correct algorithm still fails an incompatible mathematical budget.
    selected = dict(lower_part_width=4, lower_scheme="or_gates")
    adapter = golden("adder", "approximate_truncated", selected, 16)
    adapter.tolerance = replace(adapter.tolerance, max_err=0, mean_err=0)
    source = approximate_truncated_sv(16, selected, "tight_dut")
    status = run_python_case("", "tight_dut", emit("tight_dut", {}, adapter, 1500, 19), root, source)
    assert not status.endswith(": PASS") and ("BOUND" in status or "MEAN" in status), status
    results.append(dict(tight_budget_rejected=True, detail=status))
    # A very loose mathematical budget cannot accept a different algorithm.
    adapter = golden("adder", "approximate_truncated", selected, 16)
    adapter.tolerance = replace(adapter.tolerance, max_err=10**20, mean_err=10**20)
    source = approximate_truncated_sv(16, selected, "original_dut")
    source += "\nmodule mutated_dut(input [15:0] a,b,input cin,output [15:0] s,output cout);\n" \
              "wire [15:0] correct_s; original_dut original(.a(a),.b(b),.cin(cin),.s(correct_s),.cout(cout));\n" \
              "assign s=correct_s ^ 16'd1; endmodule\n"
    bench = emit("mutated_dut", {}, adapter, 1500, 19)
    status = run_python_case("", "mutated_dut", bench, root, source)
    assert not status.endswith(": PASS") and "ALGORITHM" in status, status
    results.append(dict(loose_budget_mutation_rejected=True, detail=status))
    # Missing algorithm words must not be treated as don't-care outputs.
    source = approximate_truncated_sv(16, selected, "missing_dut")
    bench = emit("missing_dut", {}, adapter, 1500, 19)
    bench.write(root / "missing_dut")
    (root / "missing_dut" / "algorithm.hex").write_text("")
    status = run_case("", "missing_dut", bench, root, source)
    assert not status.endswith(": PASS") and "ALGORITHM" in status, status
    results.append(dict(missing_algorithm_rejected=True, detail=status))
    adapter.algorithm = lambda values: {"s": 1 << 16, "cout": 0}
    try:
        adapter.algorithm_expect(dict(a=0, b=0, cin=0))
    except ValueError as error:
        assert "exceeds" in str(error)
    else:
        raise AssertionError("out-of-width algorithm outputs were accepted")
    (root / "report.json").write_text(json.dumps(results, indent=2) + "\n")
    print(f"PASS 5 algorithms, tight-budget gate, loose-budget mutation, missing-file and output-width rejection; {root}")


if __name__ == "__main__":
    main()
