"""Check infinity-only rounding against explicitly enumerated finite neighbours."""
from bisect import bisect_left
from fractions import Fraction
from itertools import product
import argparse
import json
from pathlib import Path
import tempfile


def neighbours(fmt):
    from chialu.verify.formats import Special
    return sorted((fmt.decode(bits), bits) for bits in range(1 << (fmt.width - int(fmt.signed)))
                  if not isinstance(fmt.decode(bits), Special))


def reference(fmt, value, mode, word, sr_bits, compare):
    from chialu.verify.formats import PINF, NINF, Special, _floor_log2
    if isinstance(value, Special):
        return fmt.encode_special(value)
    negative = value < 0
    magnitude = abs(value)
    points = neighbours(fmt)
    values = [point[0] for point in points]
    at = bisect_left(values, magnitude)
    sign = int(negative) << (fmt.width - 1) if fmt.signed else 0
    if at < len(values) and values[at] == magnitude:
        return sign | points[at][1]
    low, low_bits = points[at - 1]
    if at == len(points):
        quantum = Fraction(2) ** (_floor_log2(low) - fmt.man_bits)
        high, high_bits = low + quantum, fmt.encode_special(PINF)
    else:
        high, high_bits = points[at]
        exponent = max(1 - fmt.bias, _floor_log2(low) if low else 1 - fmt.bias)
        quantum = Fraction(2) ** (exponent - fmt.man_bits)
    direction = {"RDN": "RUP", "RUP": "RDN"}.get(mode, mode) if negative else mode
    if direction in ("RTZ", "RDN"):
        bits = low_bits
    elif direction == "RUP":
        bits = high_bits
    elif mode == "SR":
        threshold = ((magnitude - low) * (1 << sr_bits) / (high - low)) // 1
        up = threshold > word if compare == "gt" else threshold >= word
        bits = high_bits if up else low_bits
    else:
        distance_low, distance_high = magnitude - low, high - magnitude
        up = distance_high < distance_low or (distance_high == distance_low and int(low / quantum) % 2 == 1)
        bits = high_bits if up else low_bits
    return sign | bits


def check(name, sr_bits, compare, root):
    from chialu.targets.rtl.engine import Engine, Conventions, FW, FLAG_ORDER
    from chialu.targets.rtl import families as FAM
    from chialu.targets.rtl.families.fp import Geom
    from chialu.targets.rtl.families.selftest import run_case
    from chialu.verify.engine_ref import x_ref
    from chialu.verify.family_ref import Port
    from chialu.verify.family_tb import emit_text, pack_ports
    from chialu.verify.formats import PINF, NINF, parse_format
    from chialu.verify.rounding import Rounder, flag_word
    from chialu.verify.tb_gen import write_hex
    fmt = parse_format(name)
    engine = Engine("h", fmt, sr_bits, True, conv=Conventions(sr_compare=compare))
    geometry = Geom.of_engine(engine)
    families = ("increment_adder", "compound_adder_select", "flagged_prefix", "injection")
    modules = [FAM.fp_module("rounder", "shared_per_lane", {"round.family": family}, geometry,
                             fmt=fmt, tokens=engine.tokens) for family in families]
    assert all(modules)
    finite = neighbours(fmt)
    values = {value for value, _ in finite}
    for (low, _), (high, _) in zip(finite, finite[1:]):
        values.update(low + (high - low) * Fraction(numerator, 8) for numerator in range(1, 8))
    maximum = fmt.max_finite()
    step = fmt.ulp_at(fmt._max_finite_bits())
    values.update((maximum + step / 4, maximum + step / 2, maximum + step, maximum * 4))
    if fmt.signed:
        values |= {-value for value in values}
    values = sorted(values) + [PINF] + ([NINF] if fmt.signed else [])
    inputs = [Port("x", "input", engine.XT), Port("rnd", "input", 3), Port("word", "input", sr_bits), Port("ftz", "input", 1)]
    output_width = fmt.width + FW
    outputs = [Port("engine_result", "output", output_width)] + [Port(f"result{i}", "output", output_width) for i in range(4)]
    declarations = ", ".join(f"{port.direction} wire [{port.width-1}:0] {port.name}" for port in inputs + outputs)
    source = f"module hole_dut({declarations});\n" + engine.vdecl() + engine.rup_fn() + engine.arith() + engine.pack_float(fmt, "value")
    source += "assign engine_result = h_pack_value(x,rnd,word,ftz);\n"
    dependencies = {}
    for i, module in enumerate(modules):
        dependencies.update(FAM.module_texts(module.name, module.text))
        source += f"{module.name} r{i}(.x(x),.rnd(rnd),.word(word),.ftz(ftz),.bits(result{i}[{fmt.width-1}:0]),.fl(result{i}[{fmt.width} +: {FW}]));\n"
    source += "endmodule\n" + "\n".join(dependencies.values())
    vectors, expected = [], []
    words = range(1 << sr_bits) if sr_bits <= 3 else (0, 1, (1 << sr_bits) // 4 - 1, (1 << sr_bits) // 4,
             (1 << sr_bits) // 2 - 1, (1 << sr_bits) // 2, 3 * (1 << sr_bits) // 4 - 1, 3 * (1 << sr_bits) // 4, (1 << sr_bits) - 1)
    for value, (mode, rounding), word, ftz in product(values, enumerate(("RNE", "RTZ", "RDN", "RUP", "SR")), words, (False, True)):
        bits, flags = Rounder(rounding, sr_bits, compare, ftz=ftz).float(fmt, value, word)
        independent = reference(fmt, value, rounding, word, sr_bits, compare)
        if ftz and independent & ((1 << fmt.man_bits) - 1) and (independent >> fmt.man_bits) & fmt.emax_code == 0:
            independent &= (1 << (fmt.width - 1)) if fmt.signed else 0
        assert bits == independent, (name, value, rounding, word, bits, independent)
        packed = bits | (flag_word(flags, FLAG_ORDER) << fmt.width)
        vector = {"x": x_ref(value, engine.XW, engine.EW), "rnd": mode, "word": word, "ftz": int(ftz)}
        vectors.append(pack_ports(vector, inputs))
        expected.append(pack_ports({port.name: packed for port in outputs}, outputs))
    tag = f"{name}_{sr_bits}_{compare}"
    directory = Path(root) / tag
    directory.mkdir(parents=True, exist_ok=True)
    write_hex(directory / "vectors.hex", vectors, sum(port.width for port in inputs))
    write_hex(directory / "expected.hex", expected, 5 * output_width)
    verdict = run_case("", tag, emit_text("hole_dut", {}, inputs + outputs, len(vectors)), Path(root), source)
    return {"format": name, "sr_bits": sr_bits, "sr_compare": compare, "vectors": len(vectors),
            "pass": verdict.endswith(": PASS"), "detail": verdict}


def check_block_multipliers(root):
    """Exercise both exponent-only and fractional block-scale feedback."""
    from chialu.verify.alu_ref import normalize_spec
    from chialu.verify.variant_selftest import check_seed
    results = []
    for scale in ("e8m0", "fp8e4m3", "fp16"):
        name = f"blks{scale}efps1e2m1Is2"
        spec = normalize_spec({"unit": "alu", "dut_name": "alu_core", "modes": [{"count": 1, "format": name}],
            "ops": ["fmul"], "rounding": ["RNE", "RTZ", "RDN", "RUP", "SR"], "sr_bits": 2,
            "daz_in": [False, True], "ftz_out": [False, True],
            "flags": ["invalid", "nan", "inexact", "overflow", "underflow", "denormal"]})
        result = check_seed(spec, {"core.fp_multiplier.m0": ("round_fused_in_reduction", {})},
                            root / f"block_{scale}", 128, 29)
        result.update(format=name, family="round_fused_in_reduction", scope="ALU block multiplier seed")
        results.append(result)
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out")
    parser.add_argument("--formats", default="fps1e2m1I,fps0e2m1I,fps1e3m2I")
    parser.add_argument("--sr-bits", default="2,8")
    args = parser.parse_args(argv)
    root = Path(args.out or tempfile.mkdtemp(prefix="chialu-infinity-hole-"))
    root.mkdir(parents=True, exist_ok=True)
    results = []
    for name, sr_bits, compare in product(args.formats.split(","), map(int, args.sr_bits.split(",")), ("gt", "ge")):
        result = check(name, sr_bits, compare, root)
        results.append(result)
        print(json.dumps(result), flush=True)
        (root / "report.json").write_text(json.dumps(results, indent=2) + "\n")
    from chialu.verify.alu_ref import normalize_spec
    from chialu.verify.variant_selftest import check_seed
    for name, family in product(args.formats.split(","), ("sig_mul_then_round", "round_fused_in_reduction")):
        spec = normalize_spec({"unit": "alu", "dut_name": "alu_core", "modes": [{"count": 1, "format": name}],
            "ops": ["fmul"], "rounding": ["RNE", "RTZ", "RDN", "RUP", "SR"], "sr_bits": 2,
            "daz_in": [False, True], "ftz_out": [False, True], "exhaustive": True,
            "flags": ["invalid", "nan", "inexact", "overflow", "underflow", "denormal"]})
        result = check_seed(spec, {"core.fp_multiplier.m0": (family, {})}, root / f"{name}_{family}", 128, 29)
        result.update(format=name, family=family, scope="ALU multiplier seed")
        results.append(result)
        print(json.dumps({key: result.get(key) for key in ("format", "family", "scope", "pass", "detail")}), flush=True)
        (root / "report.json").write_text(json.dumps(results, indent=2) + "\n")
    for result in check_block_multipliers(root):
        results.append(result)
        print(json.dumps({key: result.get(key) for key in ("format", "family", "scope", "pass", "detail")}), flush=True)
        (root / "report.json").write_text(json.dumps(results, indent=2) + "\n")
    return 0 if results and all(result["pass"] for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
