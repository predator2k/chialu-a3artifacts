"""Check conversion-only modes in the seed, Python golden and template bindings."""
from pathlib import Path
import tempfile

from chialu.verify.alu_ref import alu_layout, normalize_spec
from chialu.verify.variant_selftest import check_seed
from chialu.targets.rtl.alu_seed import structure_manifest


def main():
    target = normalize_spec({"unit": "alu", "dut_name": "alu_core", "check_en": False,
                             "modes": [{"format": "int8", "count": 1, "ops": ["add"]},
                                       {"format": "fp16", "count": 1, "ops": ["cvt(int8)"]}],
                             "ops": ["add", "cvt(int8)"]})
    assert alu_layout(target)["legal"] == {(0, "add"), (1, "cvt(int8)")}
    manifest = structure_manifest(target)
    structures = {(st.mode, st.kind) for st in manifest}
    assert (0, "adder") in structures and (1, "converter") in structures
    assert (0, "converter") not in structures and (1, "fp_adder") not in structures
    from chialu.modules.alu import _validate_mode, spec_from_bindings
    for mode in target["modes"]:
        _validate_mode(mode)
    from adir.variables import Binding
    bindings = {"modes": Binding(None, "runtime", members=target["modes"]),
                "ops": Binding(None, "runtime", members=target["ops"]),
                "check_en": Binding(None, "fixed", value=False)}
    assert spec_from_bindings(bindings)["modes"] == target["modes"]
    for operations in ([], ["fmul"], ["not_in_global_list"]):
        bad = dict(target, modes=[dict(target["modes"][0], ops=operations), target["modes"][1]])
        try:
            normalize_spec(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid per-mode operation mask accepted: {operations}")
    out = Path(tempfile.mkdtemp(prefix="chialu-mode-ops-"))
    result = check_seed(target, {"core.adder.m0": ("ripple_carry", {}),
                                 "core.converter.m1.int8_twos_complement": ("shift_round_convert", {})}, out, 64, 43)
    assert result["pass"], result
    print(f"PASS mode masks, converter-only generation, Python golden and template preservation: {out}")


if __name__ == "__main__":
    main()
