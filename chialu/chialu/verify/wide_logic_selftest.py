"""Verify a single wide gate row across packings and both unary result layouts."""
from pathlib import Path
import tempfile

from chialu.verify.alu_ref import normalize_spec
from chialu.verify.elaboration import elaborate
from chialu.verify.variant_selftest import check_seed


def main():
    out = Path(tempfile.mkdtemp(prefix="chialu-wide-logic-"))
    total = 0
    for encoding in ("int8", "int8_sm", "int8_ones"):
        for wide_result in (False, True):
            for xor_not in (False, True):
                modes = [{"format": encoding, "count": 2}, {"format": "int16", "count": 1},
                         {"format": "int8", "count": 1}]
                target = normalize_spec({"unit": "alu", "dut_name": "alu_core", "check_en": False,
                                         "modes": modes, "unary_dual": [False, True],
                                         "ops": ["and", "or", "xor", "not"] + (["mul_wide"] if wide_result else [])})
                selections = {f"core.logic.m{index}": ("wide_gate_row", {"not_via_xor": xor_not})
                              for index in range(len(modes))}
                directory = out / encoding / f"wide{int(wide_result)}_xor{int(xor_not)}"
                result = check_seed(target, selections, directory, 64, 31)
                assert result["pass"], result
                hierarchy = elaborate((directory / "seed.sv").read_text(), "alu_core", directory / "elaboration")
                rows = [instance for instance in hierarchy if instance["module"] == "fam_logic_gate_row"]
                assert len(rows) == 1 and rows[0]["parameters"]["W"] == 32, rows
                assert rows[0]["parameters"]["NOT_VIA_XOR"] == int(xor_not)
                total += 1
                print(encoding, wide_result, xor_not, "PASS", flush=True)
    print(f"PASS {total} gate-row targets, one physical row each: {out}")


if __name__ == "__main__":
    main()
