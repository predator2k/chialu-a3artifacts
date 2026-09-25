"""Check symbolic golden translation, formal counterexamples and constrained input domains."""
from pathlib import Path
import tempfile

from chialu.targets.rtl import families as FAM
from chialu.targets.rtl.families.selftest import run_python_case
from chialu.verify import family_tb
from chialu.verify.family_ref import golden, Adapter
from chialu.verify.formal import prove
from chialu.verify.symbolic import compile_reference


def main():
    directory = Path(tempfile.mkdtemp(prefix="chialu-formal-test-"))
    cases = [("adder", "ripple_carry", {}, 8, FAM.adder_module("ripple_carry", {}, 8)),
             ("adder", "ripple_carry", {}, 32, FAM.adder_module("ripple_carry", {}, 32)),
             ("incrementer", "prefix_and_incrementer", {}, 16, FAM.incrementer_module("prefix_and_incrementer", {}, 16)),
             ("comparator", "prefix_comparator", {}, 4, FAM.comparator_module("prefix_comparator", {}, 4, True)),
             ("multiplier", "behavioral_star", {}, 4, FAM.mul_module("behavioral_star", {}, 4, True)),
             ("lzc", "priority_encoder", {}, 8, FAM.lzc_module("priority_encoder", {}, 8))]
    # Every successful symbolic translation is also simulated against Python files.
    for index, (kind, family, pins, width, module) in enumerate(cases):
        adapter = golden(kind, family, pins, width)
        if module is None:
            raise AssertionError((kind, family))
        reference = compile_reference(adapter)
        tb = family_tb.emit("python_golden", {}, adapter, n=512)
        verdict = run_python_case("", f"translation{index}", tb, directory, reference)
        assert verdict.endswith(": PASS"), verdict
        result = prove(module, adapter, directory / str(index))
        assert result["status"] == "proved", result
    adapter = golden("adder", "ripple_carry", {}, 8)
    bad = FAM.Module("bad_add", {}, "module bad_add(input [7:0] a,b,input cin,output [7:0] s,output cout);\n"
                     "assign {cout,s} = {1'b0,a} + {1'b0,b} + cin + 1;\nendmodule\n")
    result = prove(bad, adapter, directory / "mutation")
    assert result["status"] == "failed", result
    assert (directory / "mutation" / "counterexample.vcd").exists()
    undefined = bad._replace(name="undefined_add", text=bad.text.replace("bad_add", "undefined_add").replace(
        "{1'b0,a} + {1'b0,b} + cin + 1", "9'bx"))
    assert prove(undefined, adapter, directory / "undefined")["status"] != "proved"
    invalid = Adapter(adapter.ports, lambda v: {"s": 1 << 1000, "cout": 0})
    assert prove(bad, invalid, directory / "invalid")["status"] == "unproved"
    print(f"PASS {len(cases)} Python translations and formal proofs; mutation rejected ({directory})")


if __name__ == "__main__":
    main()
