"""EDA-free self-test of the verification layer: builds bundles across
the parameter dimensions (encodings, floats, posit, BCD, approximate,
multi-lane, multi-function SFU, dot combos incl. the quire, iterative
protocol), emulates a perfect DUT from the expected values, and checks
that the budget machinery passes clean dumps and rejects corrupted
ones.

    python3 -m chialu.verify.selftest [out_dir]
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from chialu.verify.harness import build_verification

SPECS = [
    {"unit": "alu", "modes": [{"count": 1, "format": "int16"}], "n_random": 24,
     "ops": ["add", "sub", "mul", "mul_wide", "div", "rem", "mod",
             "min", "max", "cmp", "shl", "shr_arith", "and", "xor",
             "popcount", "clz", "add_sat", "cvt(int8)", "cvt(uint32)"]},
    {"unit": "alu", "modes": [{"count": 1, "format": "int12_ones"}], "n_random": 16,
     "ops": ["add", "sub", "neg", "abs"]},
    {"unit": "alu", "modes": [{"count": 1, "format": "int12_sm"}], "n_random": 16,
     "ops": ["add", "sub", "min", "max"]},
    {"unit": "alu", "modes": [{"count": 1, "format": "bcd4"}], "n_random": 16,
     "ops": ["add", "sub", "mul", "div"]},
    {"unit": "alu", "modes": [{"count": 1, "format": "int32"}, {"count": 2, "format": "int16"},
                              {"count": 4, "format": "int8"}], "n_random": 12,
     "ops": ["add", "mul"]},
    {"unit": "alu", "modes": [{"count": 1, "format": "fp16"}], "n_random": 24,
     "ops": ["fadd", "fsub", "fmul", "fdiv", "fsqrt", "fcmp", "fmin",
             "fmax", "fabs", "fneg", "cvt(int16)", "cvt(bf16)"]},
    {"unit": "alu", "modes": [{"count": 1, "format": "posit16_1"}], "n_random": 16,
     "ops": ["fadd", "fmul", "fabs"]},
    {"unit": "alu", "modes": [{"count": 1, "format": "int16"}, {"count": 1, "format": "fp16"}],
     "n_random": 12, "ops": ["add", "mul", "fadd", "fmul"]},
    {"unit": "alu", "modes": [{"count": 1, "format": "int16"}], "n_random": 16,
     "ops": ["add", "mul"], "accuracy": "approximate",
     "budget": {"mred": 0.02, "error_rate": 0.6}},
    {"unit": "alu", "modes": [{"count": 1, "format": "fxs1i7f8"}, {"count": 2, "format": "fxs0i4f4"}],
     "n_random": 12, "ops": ["add", "sub_sat", "mul", "mul_wide", "mul_sat", "div", "rem",
                             "mod", "shl", "cmp", "cvt(int8)", "cvt(fp16)", "cvt(fxs1i3f4)"],
     "rounding": ["RNE", "RTZ", "RDN", "RUP"], "quotient_semantics": ["truncate_zero", "floor"],
     "flags": ["inexact", "overflow", "carry", "int_overflow", "div_zero"]},
    {"unit": "alu", "modes": [{"count": 1, "format": "blksfps0e8m0Nefp4e2m1s32"},
                              {"count": 2, "format": "blksfp8e4m3efp4e2m1s16"},
                              {"count": 32, "format": "fp16"}],
     "n_random": 6, "ops": ["fadd", "fmul", "fdiv", "fsqrt", "fmin", "fcmp", "fabs", "fneg",
                            "cvt(blksfps0e8m0Nefp4e2m1s32)", "cvt(fp16)", "cvt(bf16)"],
     "rounding": ["SR"], "sr_bits": 4, "flags": ["invalid", "inexact", "overflow", "nan"],
     "unary_dual": [True]},
    {"unit": "alu", "modes": [{"count": 1, "format": "fp32"}, {"count": 2, "format": "fp16"},
                              {"count": 4, "format": "fp8e4m3"}],
     "n_random": 10, "ops": ["fadd", "fsub", "fmul", "fdiv", "fsqrt", "fmax", "fabs", "cvt(int16)",
                             "cvt(posit16_1)", "cvt(fp64)"],
     "rounding": ["RNE", "SR"], "daz_in": [False, True], "ftz_out": [False, True],
     "unary_dual": [False, True], "flags": ["invalid", "div_zero", "overflow", "underflow",
                                            "inexact", "nan", "denormal", "unordered"],
     "nan_payload": "propagate", "minmax_nan": "number", "tininess": "before"},
    {"unit": "alu", "modes": [{"count": 1, "format": "fp80"}, {"count": 1, "format": "posit32_2"},
                              {"count": 2, "format": "fps0e4m3NI"}],
     "n_random": 8, "ops": ["fadd", "fmul", "fdiv", "fsqrt", "fcmp", "fmin", "fneg", "cvt(int32)",
                            "cvt(fxs1i15f16)"],
     "rounding": ["RUP"], "flags": ["invalid", "inexact", "overflow", "underflow", "nan"]},
    {"unit": "alu", "modes": [{"count": 1, "format": "int8_ones"}, {"count": 1, "format": "int8_sm"},
                              {"count": 1, "format": "bcd3"}],
     "n_random": 12, "ops": ["add", "sub", "adc", "sbb", "neg", "abs", "mul", "mul_high", "mul_wide",
                             "div", "mod", "min", "cvt(int12)"],
     "zero_sign": "preserve", "int_div_zero": "zero", "unary_dual": [True],
     "flags": ["carry", "int_overflow", "overflow", "div_zero"]},
    {"unit": "alu", "modes": [{"count": 1, "format": "uint8"}], "n_random": 4, "exhaustive": True,
     "ops": ["popcount", "clz", "ctz", "not", "cvt(fp8e5m2)", "cvt(uint4)"]},
    {"unit": "vec_sfu", "modes": [{"count": 2, "format": "fp16"}], "n_random": 10,
     "functions": ["exp2", "recip", "tanh"], "flags": ["inexact", "invalid", "div_zero", "overflow"]},
    {"unit": "vec_sfu", "modes": [{"count": 1, "format": "fp8e4m3"}], "n_random": 12,
     "functions": ["sigmoid"], "exhaustive": True},
    {"unit": "vec_sfu", "modes": [{"count": 1, "format": "posit16_1"}, {"count": 2, "format": "posit8_0"}],
     "n_random": 8, "functions": ["sqrt", "recip"], "flags": ["invalid", "nan", "inexact"]},
    {"unit": "vec_sfu", "modes": [{"count": 4, "format": "fp16"}], "n_random": 6,
     "functions": ["softmax", "layernorm"], "rounding": ["RNE", "RTZ"]},
    {"unit": "vec_sfu", "modes": [{"count": 1, "format": "fp16"}], "n_random": 8,
     "functions": ["log2"], "variable_latency_max": 40},
    {"unit": "vec_sfu", "modes": [{"count": 2, "format": "bf16"}, {"count": 1, "format": "fp32"}], "n_random": 8,
     "functions": ["exp", "gelu"], "slots": [{"approx": "pwl", "segments": 16}, {"approx": "pwq", "segments": 8}],
     "rounding": ["SR"], "sr_bits": 5, "flags": ["inexact", "invalid", "denormal"], "daz_in": [False, True]},
    {"unit": "vec_sfu", "modes": [{"count": 1, "format": "fp16"}], "n_random": 4,
     "functions": [], "slots": [{"approx": "pwl", "segments": 64}]},
    {"unit": "vec_sfu", "modes": [{"count": 1, "format": "blksfps0e8m0Nefp8e4m3s32"}, {"count": 2, "format": "blksfp8e4m3efp4e2m1s16"}],
     "n_random": 4, "functions": ["sigmoid", "recip", "softmax"], "flags": ["inexact", "invalid", "overflow"]},
    {"unit": "vec_dot_acc", "n_random": 20, "accumulate": True,
     "modes": [{"elements": 4, "format_ab": "int8", "format_c": "int32", "format_d": "int32"},
               {"elements": 2, "format_ab": "int16", "format_c": "int32", "format_d": "int32"}],
     "flags": ["overflow", "inexact"]},
    {"unit": "vec_dot_acc", "n_random": 12, "accumulate": True, "latency_cycles": 3,
     "modes": [{"elements": 2, "format_ab": "fp16", "format_c": "fp32", "format_d": "fp32"}],
     "dot_contract": "sequential", "rounding": ["RNE", "RTZ"], "flags": ["inexact", "overflow", "invalid"]},
    {"unit": "vec_dot_acc", "n_random": 10, "accumulate": False,
     "modes": [{"elements": 4, "format_ab": "fp8e4m3", "format_d": "fp16"},
               {"elements": 8, "format_ab": "fp4e2m1", "format_d": "fp8e4m3"}],
     "rounding": ["SR"], "sr_bits": 4},
    {"unit": "vec_dot_acc", "n_random": 8, "accumulate": True,
     "modes": [{"elements": 2, "format_ab": "posit16_1", "format_c": "quire16_1", "format_d": "quire16_1"}]},
    {"unit": "vec_dot_acc", "n_random": 6, "accumulate": True,
     "modes": [{"elements": 2, "format_ab": "blksfps0e8m0Nefp4e2m1s32", "format_c": "fp16", "format_d": "fp16"}],
     "daz_in": [False, True], "flags": ["inexact", "denormal"]},
    {"unit": "vec_dot_acc", "n_random": 6, "accumulate": True,
     "modes": [{"elements": 4, "format_ab": "int8", "format_c": "fxs1i15f16", "format_d": "blksfp8e4m3efp4e2m1s16"}],
     "overflow": "saturate", "flags": ["inexact", "overflow"]},
    {"unit": "vec_dot_acc", "n_random": 10, "accumulate": True,
     "modes": [{"elements": 3, "format_ab": "fxs1i3f4", "format_c": "fxs1i7f8", "format_d": "fxs1i7f8"}],
     "overflow": "saturate", "rounding": ["RNE", "SR"], "sr_bits": 6, "flags": ["inexact", "overflow", "carry"]},
]


def run(out_root):
    failures = []
    for i, spec in enumerate(SPECS):
        tag = f"{spec['unit']}#{i}"
        d = Path(out_root) / f"case{i:02d}_{spec['unit']}"
        try:
            v = build_verification(spec, d, emit_stub=True)
        except Exception as e:
            failures.append(f"{tag}: build raised {type(e).__name__}: {e}")
            continue
        out_w = v.out_w
        digits = (out_w + 3) // 4
        # perfect-DUT dump must pass
        clean = d / "dump_clean.hex"
        clean.write_text("".join(f"{e & ((1 << out_w) - 1):0{digits}x}\n"
                                 for e in v.expected))
        ok, viol, rep = v.check(clean)
        if not ok:
            failures.append(f"{tag}: clean dump rejected: {viol} "
                            f"{rep.summary()}")
        # corrupted dump must fail an exact budget; for the approximate
        # case a massive corruption must blow the mred budget
        bad = d / "dump_bad.hex"
        lines = clean.read_text().split()
        flip = max(1, len(lines) // 3)
        for j in range(flip):
            lines[j * 3 % len(lines)] = \
                f"{(int(lines[j * 3 % len(lines)], 16) ^ ((1 << out_w) - 1)):0{digits}x}"
        bad.write_text("\n".join(lines) + "\n")
        ok2, _viol2, rep2 = v.check(bad)
        if ok2:
            failures.append(f"{tag}: corrupted dump accepted "
                            f"({rep2.summary()})")
        # freeze reproducibility
        v2 = build_verification(dict(spec), Path(str(d) + "_re"))
        f1 = (d / "freeze.json").read_text()
        f2 = (Path(str(d) + "_re") / "freeze.json").read_text()
        import json
        if json.loads(f1)["vector_sha256"] != json.loads(f2)["vector_sha256"]:
            failures.append(f"{tag}: freeze hash not reproducible")
        print(f"  {tag}: {len(v.vecs)} vectors, out_w={out_w}, "
              f"budget={v.budget.bounds}, "
              f"{'ok' if not any(tag in f for f in failures) else 'FAIL'}")
    return failures


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp(
        prefix="chialu_verify_selftest_")
    print(f"[selftest] building {len(SPECS)} bundles under {out}")
    failures = run(out)
    if failures:
        print("\n[selftest] FAILURES:")
        for f in failures:
            print("  -", f)
        return 1
    print(f"[selftest] all {len(SPECS)} cases pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
