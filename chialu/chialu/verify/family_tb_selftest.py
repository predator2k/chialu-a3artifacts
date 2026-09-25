"""Check file ordering, wide outputs, numerical bounds and rejection of corrupted results."""
from pathlib import Path
import tempfile

from chialu.targets.rtl.families.selftest import run_case
from chialu.verify.family_ref import golden, Tolerance, Port
from chialu.verify.family_tb import emit, emit_text, pack_ports
from chialu.verify.tb_gen import write_hex


def main():
    work = Path(tempfile.mkdtemp(prefix="chialu_family_tb_"))
    for width in (8, 64, 512):
        adapter = golden("adder", "ripple_carry", {}, width)
        vectors = adapter.stimulus(19, 71)
        assert vectors == adapter.stimulus(19, 71)
        assert vectors != adapter.stimulus(19, 72)
        assert len(vectors) == len(adapter.stimulus(0, 71)) + 19
        name = f"word_{width}"
        text = f"module {name}(input [{width-1}:0] a, b, input cin, output [{width-1}:0] s, output cout); assign {{cout, s}} = {{1'b0,a}} + b + cin; endmodule"
        bench = emit(name, {}, adapter, 19, 71)
        bench.write(work / name)
        assert run_case("", name, bench, work, text).endswith(": PASS")
        expected = work / name / "expected.hex"
        rows = expected.read_text().splitlines()
        rows[0] = f"{int(rows[0],16) ^ (1 << width):x}"
        expected.write_text("\n".join(rows) + "\n")
        assert "PASS" not in run_case("", name, bench, work, text)
        print(f"PASS {width}-bit vectors and expected-file mutation", flush=True)
    adapter = golden("multiplier", "behavioral_star", {"_signed": False}, 8)
    adapter.domains = {"a": 16, "b": 16}
    adapter.tolerance = Tolerance(1, 1, ("p",))
    for error in (1, 2):
        name = f"bound_{error}"
        text = f"module {name}(input [7:0] a,b, output [15:0] p); assign p = a*b+{error}; endmodule"
        bench = emit(name, {}, adapter, 19, 71)
        bench.write(work / name)
        verdict = run_case("", name, bench, work, text)
        assert verdict.endswith(": PASS") == (error == 1), verdict
    name = "mean_equality"
    directory = work / name
    directory.mkdir()
    ports = [Port("a", "input", 4), Port("y", "output", 4)]
    write_hex(directory / "vectors.hex", range(5), 4)
    write_hex(directory / "expected.hex", range(5), 4)
    text = "module mean_equality(input [3:0] a, output [3:0] y); assign y = a + (a < 3); endmodule"
    bench = emit_text(name, {}, ports, 5, Tolerance(1, 0.6, ("y",)))
    assert run_case("", name, bench, work, text).endswith(": PASS")
    adapter = golden("adder", "ripple_carry", {}, 8)
    adapter.domains = {"a": 64, "b": 64}
    adapter.tolerance = Tolerance(1, 1, ("s",))
    name = "bad_carry"
    text = "module bad_carry(input [7:0] a,b, input cin, output [7:0] s, output cout); assign s=a+b+cin; assign cout=1'b1; endmodule"
    bench = emit(name, {}, adapter, 19, 71)
    bench.write(work / name)
    assert "PASS" not in run_case("", name, bench, work, text)
    print("PASS maximum and mean bounds, exact side outputs and one-unit excess", flush=True)
    for kind, family in (("shifter", "barrel_mux_tree"), ("bcd_adder", "bcd_direct_addition")):
        adapter = golden(kind, family, {"sticky_collect": True}, 8)
        for vector in adapter.stimulus(19, 71):
            expected = adapter.expect(vector)
            assert set(expected) == {p.name for p in adapter.ports if p.direction == "output"}
            assert pack_ports(expected, [p for p in adapter.ports if p.direction == "output"]) >= 0
    print(f"PASS ({work})")


if __name__ == "__main__":
    main()
