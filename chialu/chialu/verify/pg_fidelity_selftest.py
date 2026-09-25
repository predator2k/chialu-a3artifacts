"""Simulate the shared propagate/generate circuit and automatic partition fusion."""
import argparse
import json
from pathlib import Path
import tempfile

from chialu.verify.alu_ref import normalize_spec
from chialu.verify.variant_selftest import check_seed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out")
    parser.add_argument("--vectors", type=int, default=256)
    args = parser.parse_args()
    out = Path(args.out or tempfile.mkdtemp(prefix="chialu-pg-"))
    records = []
    ops = ["add", "sub", "adc", "sbb", "neg", "abs", "add_sat", "sub_sat", "and", "or", "xor", "not"]
    for fmt in ("int8", "uint8", "int8_sm", "int8_ones", "fxs1i3f4"):
        for family, pins in (("ripple_carry", {"chunk_width_bits": 4}),
                             ("parallel_prefix", {"topology": "sklansky", "valency": 2})):
            target = normalize_spec({"unit": "alu", "dut_name": "alu_core", "check_en": False,
                                     "modes": [{"format": fmt, "count": 2}], "ops": ops,
                                     "unary_dual": True, "flags": ["carry", "overflow", "int_overflow"]})
            selections = {"core.logic.m0": ("alu_pg_fused", {}), "core.adder.m0": (family, pins)}
            result = check_seed(target, selections, out / fmt / family, args.vectors, 17)
            records.append(dict(format=fmt, family=family, **result))
            (out / "report.json").write_text(json.dumps(records, indent=2) + "\n")
            assert result["pass"], records[-1]
            assert any(w["scheme"] == "alu_pg_fused" for w in result["fidelity"]["sharing"])
            print(fmt, family, "PASS", flush=True)
    from chialu.targets.rtl.alu_seed import alu_seed, structure_manifest, default_partition
    fused = alu_seed(target, families=selections, partition=default_partition(structure_manifest(target)))
    assert all(len(unit.members) == 2 for unit in fused.units)
    assert any(w["scheme"] == "alu_pg_fused" for w in fused.fidelity["sharing"])
    from chialu.verify.family_ref import golden
    vectors = golden("multiplier", "squarer", {}, 8).stimulus(32, 1)
    assert any(vector["a"] != vector["b"] for vector in vectors)
    print(f"PASS {len(records)} shared PG seeds, automatic partition fusion and independent multiplier operands: {out}")


if __name__ == "__main__":
    main()
