"""Check IEEE exact-zero signs through behavioral and selected-family ALU seeds."""
from pathlib import Path
import tempfile

from chialu.verify.alu_ref import normalize_spec
from chialu.verify.variant_selftest import check_seed


def main():
    directory = Path(tempfile.mkdtemp(prefix="chialu-float-seed-"))
    selections = {"core.fp_adder.m0": ("single_path", {}),
                  "core.fp_multiplier.m0": ("sig_mul_then_round", {}),
                  "core.rounder.m0": ("dedicated_per_op", {}),
                  "core.unpacker.m0": ("shared_per_lane", {})}
    count = 0
    for fmt in ("fp8e4m3", "fp16", "bf16", "fp32"):
        spec = normalize_spec({"unit": "alu", "dut_name": "alu_core", "check_en": False,
                               "modes": [{"format": fmt, "count": 1}], "ops": ["fadd", "fsub", "fmul"],
                               "rounding": ["RNE", "RDN"]})
        for family_mode, families in (("behavioral", {}), ("library", selections)):
            result = check_seed(spec, families, directory / fmt / family_mode, 32, 1)
            assert result["pass"] is True, (fmt, family_mode, result)
            count += 1
            print(fmt, family_mode, "PASS", flush=True)
    print(f"PASS {count} float seeds against Python golden, including negative zero ({directory})")


if __name__ == "__main__":
    main()
