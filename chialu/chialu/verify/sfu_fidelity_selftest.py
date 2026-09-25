"""Exercise SFU resource sharing against Python values and the mathematical golden."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile
from bisect import bisect_right
from fractions import Fraction

from chialu.targets.rtl.families import sfu as SF
from chialu.targets.rtl.families.sfu_sharing import SharedNet
from chialu.targets.rtl.families.sfutest import geom_of
from chialu.verify.formats import parse_format


def check_segments():
    """Every argument code selects its actual interval for every segment count."""
    total = 0
    core = SF.core_of("exp2c")
    for segmenter in ("uniform_high_bit_decode", "hierarchical", "nonuniform", "power_of_two"):
        counts = range(2, 12) if segmenter == "power_of_two" else range(2, 65)
        if segmenter == "nonuniform":
            counts = (3, 5, 12, 24, 48, 64)
        for count in counts:
            net = SF.Net("index", "segment index")
            u = net.port_in("u", 10)
            pe = SF.PolyEngine(net, core, 10, 12, K=count, segmenter=segmenter,
                               boundary_search="analytic_curvature")
            seg = pe._segments()
            if seg.K != count:
                raise AssertionError((segmenter, count, seg.K))
            index, local, bits = pe._index(u, seg)
            net.port_out("index", index)
            net.port_out("local", local)
            for value in range(1024):
                actual = net.run({"u": value})
                expected = bisect_right(seg.starts, value) - 1
                if actual["index"] != expected:
                    raise AssertionError((segmenter, count, value, expected, actual["index"]))
                total += 1
    return total


def check_block_tails():
    """Cross-check block tail representatives with directly computed values."""
    import mpmath
    from chialu.verify.sfu_ref import block_tail_surrogate
    from chialu.verify.rounding import Rounder, ROUNDINGS
    mp = mpmath.mp.clone()
    mp.prec = 16384
    def exact(fn, x):
        t = mp.mpf(x.numerator) / x.denominator
        if fn == "exp2":
            v = mp.power(2, t)
        elif fn == "exp":
            v = mp.exp(t)
        elif fn == "sigmoid":
            v = mp.exp(t) / (1 + mp.exp(t)) if t < 0 else 1 / (1 + mp.exp(-t))
        elif fn == "softplus":
            v = max(t, 0) + mp.log1p(mp.exp(-abs(t)))
        elif fn == "gelu":
            v = t * mp.erfc(-t / mp.sqrt(2)) / 2
        elif fn == "silu":
            v = t * (mp.exp(t) / (1 + mp.exp(t)) if t < 0 else 1 / (1 + mp.exp(-t)))
        else:
            v = getattr(mp, fn)(t)
        sign, mantissa, exponent, _ = v._mpf_
        return (-1 if sign else 1) * Fraction(int(mantissa)) * Fraction(2) ** int(exponent)
    checks = 0
    for fname in ("blksfp8e4m3efp8e4m3s2", "blksfp16efp8e4m3s2"):
        fmt = parse_format(fname)
        maximum = fmt.scale.max_finite() * fmt.elem.max_finite()
        for fn in ("exp2", "exp", "sigmoid", "softplus", "tanh", "erf", "gelu", "silu"):
            magnitude = 64 if fn in ("erf", "gelu") else 1024
            for x in (Fraction(-magnitude), Fraction(magnitude)):
                surrogate = block_tail_surrogate(fn, fmt, x)
                if surrogate is None:
                    raise AssertionError((fname, fn, x, "test did not reach the tail"))
                truth = exact(fn, x)
                for partner in (Fraction(0), Fraction(1), maximum / 4, exact(fn, x - 3)):
                    for mode in ROUNDINGS:
                        for word in ((0, 127, 255) if mode == "SR" else (0,)):
                            r = Rounder(mode, 8)
                            actual = r.block(fmt, [surrogate, partner], [word, word])
                            expected = r.block(fmt, [truth, partner], [word, word])
                            if actual != expected:
                                raise AssertionError((fname, fn, x, mode, word, actual, expected))
                            checks += 1
    return checks


def check_root_fit():
    """Check the root fit's centre, expansion and error without constructing a Net."""
    import mpmath as mp
    degree = 8
    with mp.workprec(240):
        centre = mp.mpf(3) / 8
        power = mp.mpf(1) / 2
        # Analytic derivatives of sqrt(1+4t), independent of mpmath.diff.
        local = [mp.binomial(power, k) * 4 ** k * (1 + 4 * centre) ** (power - k)
                 for k in range(degree + 1)]
        expanded = [sum(local[k] * mp.binomial(k, j) * (-centre) ** (k - j)
                        for k in range(j, degree + 1)) for j in range(degree + 1)]
        generated = SF._fit_poly(lambda t: mp.sqrt(1 + 4 * t), 0.0, 0.75, degree, "taylor")
        relative = max(abs(mp.mpf(given) - want) / max(mp.mpf(1), abs(want))
                       for given, want in zip(generated, expanded))
        if relative >= mp.mpf(2) ** -48:
            raise AssertionError(f"the generated Taylor coefficients disagree with analytic derivatives: {relative}")
        maximum = mp.mpf(0)
        point = None
        for i in range(4097):
            t = mp.mpf(3) * i / (4 * 4096)
            actual = sum(mp.mpf(coefficient) * t ** k for k, coefficient in enumerate(generated))
            direct = sum(coefficient * (t - centre) ** k for k, coefficient in enumerate(local))
            if abs(actual - direct) > mp.mpf(2) ** -45:
                raise AssertionError("expansion about zero changed the polynomial's centre")
            error = abs(actual - mp.sqrt(1 + 4 * t))
            if error > maximum:
                maximum, point = error, t
        return {"domain": [0, 0.75], "centre": 0.375, "function": "sqrt(1+4*t)",
                "degree": degree, "analytic_coefficient_relative_error": float(relative),
                "maximum_sampled_absolute_error": float(maximum), "worst_t": float(point),
                "samples": 4097, "net_constructed": False}


def check_scalar_tails():
    """Cross-check scalar tail boundaries against direct 4096-bit evaluations."""
    import mpmath as mp
    from math import isqrt
    from chialu.verify.formats import PositFormat, X87Format, Special, _floor_log2
    from chialu.verify.rounding import Rounder, ROUNDINGS
    from chialu.verify.sfu_ref import resolve
    from functools import lru_cache
    @lru_cache(maxsize=None)
    def direct(fn, value):
        with mp.workprec(4096):
            x = mp.mpf(value.numerator) / value.denominator
            if fn == "softplus":
                result = max(x, 0) + mp.log1p(mp.exp(-abs(x)))
            elif fn == "sigmoid":
                result = mp.exp(x) / (1 + mp.exp(x)) if x < 0 else 1 / (1 + mp.exp(-x))
            elif fn == "gelu":
                result = x * mp.erfc(-x / mp.sqrt(2)) / 2
            elif fn == "silu":
                result = x * (mp.exp(x) / (1 + mp.exp(x)) if x < 0 else 1 / (1 + mp.exp(-x)))
            elif fn == "exp2":
                result = mp.power(2, x)
            else:
                result = getattr(mp, fn)(x)
            sign, mantissa, exponent, _ = result._mpf_
            exact = Fraction(int(mantissa)) * Fraction(2) ** int(exponent)
            return -exact if sign else exact
    total = 0
    for fname in ("fp8e4m3", "fp16", "fp64", "fp80", "fp128", "posit8_0", "posit32_2"):
        fmt = parse_format(fname)
        core = fmt.core if isinstance(fmt, X87Format) else fmt
        posit = isinstance(core, PositFormat)
        minimum = core.decode(1) if posit else core.min_positive()
        maximum = core.decode((1 << (core.width - 1)) - 1) if posit else core.max_finite()
        precision = core.width if posit else core.man_bits + 1
        count = 0
        for sr_bits in (1, 8, 32):
            low = max(1, -_floor_log2(minimum * Fraction(2) ** -(sr_bits + 32)) + 4)
            high = max(1, _floor_log2(maximum) + 4)
            relative = 2 * precision + sr_bits + 32
            thresholds = {"exp2": (high, -low), "exp": (high, -low),
                          "softplus": (relative, -low), "sigmoid": (relative, -low),
                          "tanh": ((relative + 3) // 2, -((relative + 3) // 2)),
                          "erf": (isqrt(relative) + 1, -(isqrt(relative) + 1)),
                          "gelu": (isqrt(2 * relative) + 1, -(isqrt(2 * low) + 1)),
                          "silu": (relative, -2 * low)}
            for fn, boundaries in thresholds.items():
                candidates = {Fraction(boundary) + delta for boundary in boundaries
                              for delta in (Fraction(-1, 2), Fraction(0), Fraction(1, 2))}
                if fn == "softplus" and fname in ("fp64", "fp80", "fp128"):
                    candidates.add(Fraction(-10000))
                values = {fmt.decode(fmt.round(value, "RNE")) for value in candidates}
                for value in values:
                    if isinstance(value, Special):
                        continue
                    truth = direct(fn, value)
                    for mode in ROUNDINGS:
                        for compare in (("gt", "ge") if mode == "SR" else ("gt",)):
                            words = (0, (1 << sr_bits) // 2, (1 << sr_bits) - 1) if mode == "SR" else (0,)
                            for word in words:
                                r = Rounder(mode, sr_bits, compare)
                                expected = r.scalar(fmt, truth, word)
                                actual = resolve(fmt, ("irr", fn, value), r, word)
                                if actual != expected:
                                    raise AssertionError((fname, fn, str(value), mode, sr_bits, compare, word, actual, expected))
                                count += 1
        total += count
        print(f"PASS scalar tails {fname}: {count} rounding/threshold comparisons", flush=True)
    return total


def check_coefficient_precision():
    """Verify stable coefficient bits beyond binary64 for every fitting basis."""
    import mpmath as mp
    checks = []
    for basis in ("taylor", "chebyshev", "minimax_remez"):
        first = SF._fit_poly(mp.exp, Fraction(0), Fraction(1, 16), 4, basis, precision=320)
        second = SF._fit_poly(mp.exp, Fraction(0), Fraction(1, 16), 4, basis, precision=512)
        quantized = [SF._quantize(value, 128) for value in first]
        if quantized != [SF._quantize(value, 128) for value in second]:
            raise AssertionError((basis, "128-bit coefficient rounding is not stable"))
        changed = sum(value != SF._quantize(float(original), 128) for value, original in zip(quantized, first))
        if changed != len(first):
            raise AssertionError((basis, "fixture does not exercise coefficient bits beyond binary64"))
        checks.append({"basis": basis, "fraction_bits": 128, "working_precisions": [320, 512],
                       "coefficients_beyond_binary64": changed})
    for construction in ("pade", "orthogonal", "minimax_remez"):
        results = []
        for precision in (256, 384):
            token = SF._fit_precision.set(precision)
            try:
                p, q = SF.RationalEngine("rational_approximation", {})._fit(
                    mp.exp, Fraction(0), Fraction(1, 4), 2, 2, construction, False)
                results.append([SF._quantize(value, 112) for value in p + q])
            finally:
                SF._fit_precision.reset(token)
        if results[0] != results[1]:
            raise AssertionError((construction, "112-bit rational coefficients are not stable"))
        checks.append({"construction": construction, "fraction_bits": 112, "working_precisions": [256, 384]})
    return checks


def check_polynomial_contracts(work):
    """Simulate evaluator cores against independently implemented algorithms."""
    import random
    from chialu.verify.sfu_algorithm import PolynomialContract
    from chialu.targets.rtl.families.selftest import run_case
    cases = [("piecewise_poly", {"segments": 4, "degree": 3, "evaluator.family": evaluator}, "exp2c")
             for evaluator in ("horner", "estrin", "parallel_monomial", "factored", "coefficient_adapted",
                               "shift_add_coeff", "fma_based")]
    cases += [("pwl", {"segments": 24, "slope_encoding": encoding, "x_frac_bits": 12}, "exp2c")
              for encoding in ("plain", "power_of_two", "signed_po2_pair", "csd")]
    cases += [("single_poly", {"degree": 8, "evaluator.family": "parallel_monomial"}, "sqrtc"),
              ("piecewise_poly", {"segments": 12, "degree": 2, "segmenter.family": "hierarchical"}, "recipc"),
              ("pwl_residual_lut", {"residual_bits": 5}, "exp2c")]
    results = []
    for ci, (family, pins, core_name) in enumerate(cases):
        directory = work / f"core_{ci}"
        directory.mkdir(parents=True, exist_ok=True)
        core = SF.core_of(core_name)
        fraction = 18
        width = fraction + (1 if core.L == 2 else 0)
        net = SF.Net(f"polynomial_{ci}", "standalone selected evaluator")
        u = net.port_in("u", width)
        evaluate = SF.poly_engine(family, pins)
        out = evaluate(net, core, u, fraction, 18, core_name)
        net.port_out("y", out)
        manifest = net.algorithm_contracts[-1]
        contract = PolynomialContract(manifest)
        rng = random.Random(100 + ci)
        inputs = {0, (1 << width) - 1, (1 << width) // 2}
        for boundary in manifest["starts"] + manifest["ends"]:
            source = boundary << manifest["input_shift"]
            for delta in (-1, 0, 1):
                if 0 <= source + delta < 1 << width:
                    inputs.add(source + delta)
        inputs.update(rng.randrange(1 << width) for _ in range(256))
        lines = [f"module tb; logic [{width-1}:0] u; logic [{out.w-1}:0] y;",
                 f"{net.name} dut(.u(u), .y(y)); integer errors; initial begin errors=0;"]
        count = 0
        for value in sorted(inputs):
            expected = contract.evaluate(value)
            lines.append(f"u={width}'d{value}; #1; if(y !== {out.w}'d{expected}) begin errors=errors+1; "
                         f'$display("FAIL u=%d got=%d expected={expected}",u,y); end')
            count += 1
        lines += ['if(errors==0) $display("PASS"); else $display("FAIL %0d",errors); $finish; end endmodule']
        result = run_case("", net.name, "\n".join(lines), directory, net.render())
        item = dict(contract.report(), pins=pins, pass_=result.endswith(": PASS"), detail=result, vectors=count)
        (directory / "contract.json").write_text(json.dumps(manifest, indent=2) + "\n")
        results.append(item)
        print(json.dumps(item), flush=True)
    (work / "algorithm-contracts.json").write_text(json.dumps(results, indent=2) + "\n")
    if not all(item["pass_"] for item in results):
        raise AssertionError("a polynomial RTL did not implement its independent algorithm contract")
    return sum(item["vectors"] for item in results)


def simulate_shared(net, fmt, functions, work):
    from chialu.targets.rtl.families.selftest import run_case
    geometry = geom_of(fmt)
    width = geometry.XT
    lines = [f"module tb; logic [{width-1}:0] x, y; logic inv, dz; logic [{net.sw-1}:0] fn_sel;",
             f"{net.name} dut(.x(x), .y(y), .inv(inv), .dz(dz), .fn_sel(fn_sel));",
             "integer errors; initial begin errors = 0;"]
    vectors = 0
    for fi, function in enumerate(functions):
        for pattern in range(1 << fmt.width):
            if not fmt.valid(pattern):
                continue
            value = SF.x_of_bits(fmt, pattern, geometry)
            expected = net.nets[fi].run({"x": value})
            lines += [f"fn_sel={net.sw}'d{fi}; x={width}'d{value}; #1;",
                      f"if (y !== {width}'d{expected['y']} || inv !== 1'b{expected['inv']} || dz !== 1'b{expected['dz']}) begin",
                      f'$display("MISMATCH {function} x={pattern} y=%h inv=%h dz=%h", y, inv, dz); errors=errors+1; end']
            vectors += 1
    lines += ['if (errors == 0) $display("PASS"); else $display("FAIL %0d", errors); $finish; end endmodule']
    result = run_case("", net.name, "\n".join(lines), work, net.render())
    return {"pass": result.endswith(": PASS"), "detail": result, "vectors": vectors, "sharing": net.stats}


def check_promoted_sharing(work):
    """Signed 8/12-bit resources retain their individual wrap points when shared."""
    from chialu.targets.rtl.families.selftest import run_case
    nets = []
    for width, coefficient in ((8, 3), (12, -3)):
        net = SF.Net(f"signed{width}", "signed promotion fixture")
        net.stage = "evaluator0"
        x = net.port_in("x", 16)
        operand = net.as_signed(net.bits(x, width - 1))
        product = net.mul(operand, net.const(coefficient, width, True))
        output = net.add(product, net.const(-7, product.w, True))
        net.port_out("y", net.trunc(output, 16))
        net.port_out("inv", net.const(0, 1))
        net.port_out("dz", net.const(0, 1))
        nets.append(net)
    shared = SharedNet("signed_promoted", nets, "shared_evaluator")
    tb = ["module tb; logic [15:0] x, y; logic inv, dz, fn_sel;",
          "signed_promoted dut(.x(x), .y(y), .inv(inv), .dz(dz), .fn_sel(fn_sel));",
          "integer errors; initial begin errors=0;"]
    for fi, (width, coefficient) in enumerate(((8, 3), (12, -3))):
        for x in range(1 << 12):
            value = x & ((1 << width) - 1)
            if value >> (width - 1):
                value -= 1 << width
            expected = (value * coefficient - 7) & 65535
            tb.append(f"fn_sel=1'b{fi}; x=16'd{x}; #1; if(y !== 16'd{expected}) errors=errors+1;")
    tb += ['if(errors==0) $display("PASS"); else $display("FAIL %0d",errors); $finish; end endmodule']
    result = run_case("", shared.name, "\n".join(tb), work, shared.render())
    if not result.endswith(": PASS"):
        raise AssertionError(result)
    return 8192


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", default=None)
    parser.add_argument("--bound", action="store_true")
    parser.add_argument("--segments-only", action="store_true")
    parser.add_argument("--block-tails-only", action="store_true")
    parser.add_argument("--promotion-only", action="store_true")
    parser.add_argument("--root-fit-only", action="store_true")
    parser.add_argument("--polynomial-contracts-only", action="store_true")
    parser.add_argument("--scalar-tails-only", action="store_true")
    parser.add_argument("--coefficient-precision-only", action="store_true")
    args = parser.parse_args(argv)
    if args.segments_only:
        print(f"PASS {check_segments()} segment selections, including every count from 2 through 64")
        return 0
    if args.block_tails_only:
        print(f"PASS {check_block_tails()} block tail quantizations against 16384-bit direct evaluation")
        return 0
    if args.root_fit_only:
        print(json.dumps(check_root_fit(), indent=2))
        return 0
    if args.scalar_tails_only:
        print(f"PASS {check_scalar_tails()} scalar tail comparisons against 4096-bit direct evaluation")
        return 0
    if args.coefficient_precision_only:
        print(json.dumps(check_coefficient_precision(), indent=2))
        return 0
    work = Path(args.work or tempfile.mkdtemp(prefix="chialu-sfu-fidelity-"))
    work.mkdir(parents=True, exist_ok=True)
    if args.promotion_only:
        print(f"PASS {check_promoted_sharing(work)} signed promoted-resource vectors")
        return 0
    if args.polynomial_contracts_only:
        print(f"PASS {check_polynomial_contracts(work)} independent polynomial-contract vectors")
        return 0
    fmt = parse_format("fp8e4m3")
    geometry = geom_of(fmt)
    functions = ("exp2", "exp")
    pins = {"segments": 16, "degree": 2, "basis": "chebyshev", "guard_bits": 4}
    if args.bound:
        pins.update({"adder.family": "ripple_carry", "multiplier.family": "direct_pp_parallel",
                     "shifter.family": "barrel_mux_tree", "lzc.family": "lzd_cell_tree"})
    nets = [SF.sfu_sv(function, fmt, geometry, "piecewise_poly", pins)[2] for function in functions]
    report = []
    from chialu.eda import conformance
    from chialu.targets.derive import verify_files
    from chialu.targets.rtl.sfu_seed import sfu_ref_module
    for strategy in ("shared_range_reduction", "shared_evaluator", "fully_shared_rom_evaluator"):
        case_dir = work / strategy
        case_dir.mkdir(exist_ok=True)
        net = SharedNet(f"shared_{strategy}", nets, strategy)
        result = simulate_shared(net, fmt, functions, case_dir)
        result["strategy"] = strategy
        spec = {"unit": "vec_sfu", "dut_name": "sfu_core", "modes": [{"count": 1, "format": fmt.name}],
                "functions": list(functions), "n_random": 256, "budget": {"max_ulp": 1}}
        files = verify_files(spec, case_dir / "golden")
        rtl = sfu_ref_module(spec, family=("piecewise_poly", dict(pins, sharing=strategy)))
        (case_dir / "seed.sv").write_text(rtl)
        (case_dir / "fidelity.json").write_text(json.dumps(rtl.fidelity, indent=2) + "\n")
        result["mathematical_golden"] = conformance(rtl, files)
        report.append(result)
        print(json.dumps(result), flush=True)
    (work / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return 0 if all(r["pass"] and r["mathematical_golden"]["pass"] for r in report) else 1


if __name__ == "__main__":
    raise SystemExit(main())
