"""Simulate block quantization at overflow, invalid and signed-value boundaries."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from fractions import Fraction
from itertools import product
import json
from pathlib import Path
import tempfile


def check(case):
    from chialu.targets.rtl.engine import Conventions, Engine, FLAG_ORDER, FW
    from chialu.targets.rtl.families.selftest import run_case
    from chialu.verify.engine_ref import x_ref
    from chialu.verify.family_ref import Port
    from chialu.verify.family_tb import emit_text, pack_ports
    from chialu.verify.formats import NAN, PINF, NINF, Special, parse_format
    from chialu.verify.rounding import Rounder, ROUNDINGS, flag_word
    from chialu.verify.tb_gen import write_hex
    format_name, scale_rounding, invalid, overflow, root = case
    fmt = parse_format(format_name)
    options = {"block_scale_rounding": scale_rounding, "invalid_result": invalid, "block_element_overflow": overflow}
    engine = Engine("q", fmt, 8, True, conv=Conventions.from_spec(options))
    maximum = fmt.elem.max_finite() if hasattr(fmt.elem, "max_finite") else Fraction(fmt.elem.max_int)
    values = [[Fraction(0), Fraction(0)], [4 * fmt.scale.max_finite() * maximum, Fraction(0)],
              [NAN, Fraction(1)], [PINF, Fraction(1)], [NINF, Fraction(1)],
              [-3 * maximum, 2 * maximum], [maximum, -maximum],
              [fmt.scale.min_positive() / 8, -fmt.scale.min_positive() / 8]]
    inputs = [Port("xs", "input", 2 * engine.XT), Port("rnd", "input", 3),
              Port("words", "input", 16), Port("ftz", "input", 1)]
    output_width = fmt.width + 2 * FW
    ports = inputs + [Port("result", "output", output_width)]
    source = f"module quant_dut(input [{2*engine.XT-1}:0] xs, input [2:0] rnd, input [15:0] words, input ftz, output [{output_width-1}:0] result);\n"
    source += engine.vdecl() + engine.rup_fn() + engine.arith() + engine.quant_block(fmt, "block")
    source += "assign result = q_quant_block(xs,rnd,words,ftz); endmodule\n"
    vectors, expected = [], []
    for pair, (mode, rounding), words, ftz in product(values, enumerate(ROUNDINGS), ((0, 0), (128, 64), (255, 255)), (False, True)):
        encoded = [x_ref(value, engine.XW, engine.EW) for value in pair]
        assert all(isinstance(value, Special) or not (bits & 1) for value, bits in zip(pair, encoded))
        vector = {"xs": encoded[0] | (encoded[1] << engine.XT), "rnd": mode,
                  "words": words[0] | (words[1] << 8), "ftz": int(ftz)}
        bits, flags = Rounder(rounding, 8, ftz=ftz).block(fmt, pair, words, options)
        combined_flags = flag_word(flags[0], FLAG_ORDER) | (flag_word(flags[1], FLAG_ORDER) << FW)
        vectors.append(pack_ports(vector, inputs))
        expected.append(bits | (combined_flags << fmt.width))
    tag = f"{format_name}_{scale_rounding}_{invalid}_{overflow}"
    directory = Path(root) / tag
    directory.mkdir(parents=True, exist_ok=True)
    write_hex(directory / "vectors.hex", vectors, sum(port.width for port in inputs))
    write_hex(directory / "expected.hex", expected, output_width)
    verdict = run_case("", tag, emit_text("quant_dut", {}, ports, len(vectors)), Path(root), source)
    return {"format": format_name, "options": options, "vectors": len(vectors), "pass": verdict.endswith(": PASS"), "detail": verdict}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out")
    parser.add_argument("--jobs", type=int, default=2)
    args = parser.parse_args(argv)
    root = Path(args.out or tempfile.mkdtemp(prefix="chialu-block-quantizer-"))
    root.mkdir(parents=True, exist_ok=True)
    formats = ["blksfp8e4m3efp4e2m1s2", "blksfp16eint4s2", "blksfp32euint4s2",
               "blksfp8e4m3efps0e4m3Ns2", "blksfp8e4m3efps0e4m3s2", "blkse8m0efp8e4m3s2"]
    cases = [(fmt, scale, invalid, overflow, str(root)) for fmt, scale, invalid, overflow in
             product(formats, ("nearest", "up"), ("saturate", "zero"), ("saturate", "inf"))]
    results = []
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        for result in pool.map(check, cases):
            results.append(result)
            print(json.dumps(result), flush=True)
            (root / "report.json").write_text(json.dumps(results, indent=2) + "\n")
    return 0 if all(result["pass"] for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
