"""Check signed exponent-only formats through the engine and four rounder circuits."""
import argparse
from fractions import Fraction
from itertools import product
import json
from pathlib import Path
import tempfile


def check(format_name, sr_bits, compare, root):
    from chialu.targets.rtl.engine import Engine, Conventions, FW, FLAG_ORDER
    from chialu.targets.rtl import families as FAM
    from chialu.targets.rtl.families.fp import Geom
    from chialu.targets.rtl.families.selftest import run_case
    from chialu.verify.engine_ref import x_ref
    from chialu.verify.family_ref import Port
    from chialu.verify.family_tb import emit_text, pack_ports
    from chialu.verify.formats import NAN, PINF, NINF, Special, parse_format
    from chialu.verify.rounding import ROUNDINGS, Rounder, flag_word
    from chialu.verify.tb_gen import write_hex
    fmt = parse_format(format_name)
    engine = Engine("q", fmt, sr_bits, True, conv=Conventions(sr_compare=compare))
    geometry = Geom.of_engine(engine)
    families = ("increment_adder", "compound_adder_select", "flagged_prefix", "injection")
    modules = [FAM.fp_module("rounder", "shared_per_lane", {"round.family": family}, geometry,
                             fmt=fmt, tokens=engine.tokens) for family in families]
    assert all(modules), (format_name, modules)
    values = {Fraction(0), fmt.min_positive() / 8, fmt.max_finite() * 4}
    for bits in range(1 << fmt.exp_bits):
        value = fmt.decode(bits)
        if not isinstance(value, Special):
            values.update((value, value * Fraction(5, 4), value * Fraction(3, 2), value * Fraction(7, 4)))
    if fmt.signed:
        values |= {-value for value in values}
    values = sorted(values) + [PINF] + ([NINF] if fmt.signed else []) + ([NAN] if fmt.has_nan else [])
    word_width = fmt.width + FW
    inputs = [Port("x", "input", engine.XT), Port("rnd", "input", 3),
              Port("word", "input", sr_bits), Port("ftz", "input", 1)]
    outputs = [Port("engine_result", "output", word_width)] + [Port("result" + str(i), "output", word_width) for i in range(4)]
    declarations = ", ".join(f"{port.direction} wire [{port.width-1}:0] {port.name}" for port in inputs + outputs)
    source = f"module exp_round_dut({declarations});\n"
    source += engine.vdecl() + engine.rup_fn() + engine.arith() + engine.pack_float(fmt, "value")
    source += "assign engine_result = q_pack_value(x,rnd,word,ftz);\n"
    dependencies = {}
    for i, module in enumerate(modules):
        source += f"{module.name} r{i}(.x(x),.rnd(rnd),.word(word),.ftz(ftz),.fl(result{i}[{fmt.width} +: {FW}]),.bits(result{i}[{fmt.width-1}:0]));\n"
        dependencies.update(FAM.module_texts(module.name, module.text))
    source += "endmodule\n" + "\n".join(dependencies.values())
    vectors, expected = [], []
    for value, (mode, rounding), word, ftz in product(values, enumerate(ROUNDINGS), (0, 1 << (sr_bits - 1), (1 << sr_bits) - 1), (False, True)):
        vector = {"x": x_ref(value, engine.XW, engine.EW), "rnd": mode, "word": word, "ftz": int(ftz)}
        bits, flags = Rounder(rounding, sr_bits, compare, ftz=ftz).float(fmt, value, word)
        packed = bits | (flag_word(flags, FLAG_ORDER) << fmt.width)
        vectors.append(pack_ports(vector, inputs))
        expected.append(pack_ports({port.name: packed for port in outputs}, outputs))
    tag = f"{format_name}_{sr_bits}_{compare}"
    directory = Path(root) / tag
    directory.mkdir(parents=True, exist_ok=True)
    write_hex(directory / "vectors.hex", vectors, sum(port.width for port in inputs))
    write_hex(directory / "expected.hex", expected, sum(port.width for port in outputs))
    result = run_case("", tag, emit_text("exp_round_dut", {}, inputs + outputs, len(vectors)), Path(root), source)
    return {"format": format_name, "sr_bits": sr_bits, "sr_compare": compare, "vectors": len(vectors),
            "rounder_families": list(families), "pass": result.endswith(": PASS"), "detail": result}


def main(argv=None):
    from chialu.verify.formats import parse_format, Special
    from chialu.verify.rounding import Rounder
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out")
    parser.add_argument("--formats", default="fps1e2m0,fps1e2m0N,fps1e2m0I,e8m0")
    parser.add_argument("--seeds-only", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.out or tempfile.mkdtemp(prefix="chialu-exponent-rounder-"))
    root.mkdir(parents=True, exist_ok=True)
    for name in ("fps0e2m0NI", "fps1e2m0NI"):
        try:
            parse_format(name)
        except ValueError as error:
            assert "distinct encodings" in str(error)
        else:
            raise AssertionError("an exponent-only pattern aliases both NaN and infinity")
    results = []
    for format_name in args.formats.split(","):
        fmt = parse_format(format_name)
        for bits in range(1 << fmt.width):
            value = fmt.decode(bits)
            if not isinstance(value, Special):
                assert fmt.round(value) == bits
        assert "inexact" in Rounder().float(fmt, Fraction(0))[1]
        if fmt.signed:
            assert fmt.decode(fmt.round(-1)) == -1
            assert fmt.decode(fmt.round(Fraction(-3, 2), "RDN")) == -2
            assert fmt.decode(fmt.round(Fraction(-3, 2), "RUP")) == -1
        for sr_bits, compare in (() if args.seeds_only else product((1, 8), ("gt", "ge"))):
            result = check(format_name, sr_bits, compare, root)
            results.append(result)
            print(json.dumps(result), flush=True)
            (root / "report.json").write_text(json.dumps(results, indent=2) + "\n")
        from chialu.verify.alu_ref import normalize_spec
        from chialu.verify.dot_ref import normalize_dot_spec
        from chialu.verify.sfu_ref import normalize_sfu_spec
        from chialu.verify.variant_selftest import check_seed
        options = {"rounding": ["RNE", "RTZ", "RDN", "RUP", "SR"], "sr_bits": 2,
                   "flags": ["invalid", "overflow", "underflow", "inexact", "nan", "denormal", "div_zero"]}
        alu = normalize_spec({"unit": "alu", "dut_name": "alu_core", "modes": [{"count": 1, "format": format_name}],
                              "ops": ["fadd", "fsub", "fmul", "fabs", "fneg"], **options})
        dot = normalize_dot_spec({"unit": "vec_dot_acc", "dut_name": "dot_core", "modes": [{"elements": 2,
            "format_ab": format_name, "format_c": format_name, "format_d": format_name}], **options})
        sfu = normalize_sfu_spec({"unit": "vec_sfu", "dut_name": "sfu_core", "modes": [{"count": 1, "format": format_name}],
            "functions": ["exp2", "log2", "tanh"], "sfu_accuracy": {"mode": "report_error", "family": "direct_lut"}, **options})
        for kind, spec, selections in (("alu", alu, {"core.fp_adder.m0": ("single_path", {}),
                "core.fp_multiplier.m0": ("sig_mul_then_round", {}),
                "core.rounder.m0": ("shared_per_lane", {"round.family": "injection"})}),
                ("dot", dot, ("pairwise_tree", {})), ("sfu", sfu, ("direct_lut", {}))):
            try:
                result = check_seed(spec, selections, root / f"{format_name}_{kind}", 64, 73)
            except (ValueError, AssertionError) as error:
                result = {"pass": False, "detail": f"{type(error).__name__}: {error}"}
            result.update(format=format_name, unit=kind)
            results.append(result)
            print(json.dumps({key: result.get(key) for key in ("format", "unit", "pass", "detail")}), flush=True)
            (root / "report.json").write_text(json.dumps(results, indent=2) + "\n")
    return 0 if all(result["pass"] for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
