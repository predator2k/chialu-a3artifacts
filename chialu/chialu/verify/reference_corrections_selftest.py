"""Check independently established scalar-tail and block-quantizer reference corrections."""
from fractions import Fraction

from chialu.verify.formats import NAN, NINF, PINF, parse_format
from chialu.verify.ops import sfu_ref
from chialu.verify.rounding import ROUNDINGS, Rounder


def main():
    for name in ("fp16", "fp32", "fp64"):
        fmt = parse_format(name)
        value = fmt.round(100)
        assert sfu_ref("softplus", fmt, value, "RNE") == value
        assert sfu_ref("softplus", fmt, value, "RTZ") == value
        assert sfu_ref("softplus", fmt, value, "RUP") == value + 1
    double = parse_format("fp64")
    tiny = double.round(-2048)
    assert sfu_ref("exp", double, tiny, "RNE") == 0
    assert sfu_ref("exp", double, tiny, "RUP") == 1
    assert sfu_ref("exp", double, tiny, "RUP", ftz=True) == 0
    posit = parse_format("posit8_0")
    assert sfu_ref("gelu", posit, posit.round(-14)) == 0xff
    from chialu.verify.sfu_ref import normalize_sfu_spec, sfu_layout, sfu_expected
    for name, fn, value, expected, options in (
            ("fp4e2m1", "sqrt", -1, 0, {"invalid_result": "zero"}),
            ("fp8e4m3", "log2", 1, 0, {}),
            ("fp8e4m3", "log2", 4, 2, {}),
            ("fp8e4m3", "log", 1, 0, {}),
            ("fp8e4m3", "rsqrt", 4, Fraction(1, 2), {})):
        fmt = parse_format(name)
        spec = normalize_sfu_spec({"unit": "vec_sfu", "modes": [{"count": 1, "format": name}],
                                   "functions": [fn], "flags": ["invalid", "inexact"], **options})
        bits, flags = sfu_expected(spec, sfu_layout(spec), 0, 0, fmt.round(value), {"rounding": "RNE"}, None, [])
        assert bits == fmt.round(expected)
        assert flags == (3 if options else 0), (name, fn, flags)
    fmt = parse_format("fp8e5m2")
    spec = normalize_sfu_spec({"unit": "vec_sfu", "modes": [{"count": 1, "format": fmt.name}],
                               "functions": ["exp2"], "nan_payload": "propagate"})
    assert sfu_expected(spec, sfu_layout(spec), 0, 0, 0x7d, {"rounding": "RNE"}, None, [])[0] == 0x7d
    for name, value in (("e8m0", Fraction(2) ** -126), ("fp64", Fraction(2) ** -500)):
        fmt = parse_format(name)
        bits = fmt.round(value)
        for fn in ("sin", "tanh"):
            # For this positive x, 0 < f(x) < x. The correction is much
            # smaller than one representable step, but directed rounding
            # must still distinguish it from exact x.
            assert sfu_ref(fn, fmt, bits, "RTZ") == bits - 1
            spec = normalize_sfu_spec({"unit": "vec_sfu", "modes": [{"count": 1, "format": name}], "functions": [fn]})
            got, _ = sfu_expected(spec, sfu_layout(spec), 0, 0, bits, {"rounding": "RTZ"}, None, [])
            assert got == bits - 1
        one = fmt.round(1)
        assert sfu_ref("cos", fmt, bits, "RDN") == one - 1
    hole = parse_format("fps1e2m1I")
    assert hole.decode(hole.round(Fraction(4), "RTZ")) == 3
    assert hole.decode(hole.round(Fraction(7, 2), "RNE")) == 3
    assert hole.decode(hole.round(Fraction(9, 2), "RNE")) == 6
    assert hole.decode(hole.round(Fraction(-4), "RUP")) == -3
    assert hole.ulp_at(hole._max_finite_bits()) == 2
    assert Rounder("SR", 2).float(hole, Fraction(7), 2)[0] == hole._max_finite_bits()
    from chialu.verify.dot_ref import normalize_dot_spec, dot_layout, dot_expected
    block = parse_format("blkse8m0euint4s2")
    half = parse_format("fp16")
    spec = normalize_dot_spec({"unit": "vec_dot_acc", "modes": [{"format_ab": block.name,
        "format_c": "fp16", "format_d": "fp16", "elements": 1}],
        "rounding": ["RNE", "RTZ", "RDN", "RUP", "SR"], "flags": ["invalid", "inexact"]})
    for value in range(8, 16):
        # Two positive unsigned products cancel a negative addend. The
        # element's high value bit is not a negative sign bit.
        a, b = block.join([value, value], 127), block.join([1, 1], 127)
        for rounding in spec["rounding"]:
            bits, flags = dot_expected(spec, dot_layout(spec), 0, a, b, half.round(-2 * value),
                                       {"rounding": rounding}, [0])
            assert bits == (0x8000 if rounding == "RDN" else 0), (value, rounding, bits)
            assert flags == 0
    checks = 0
    for scale in ("fp8e5m2", "fp16", "fp32"):
        for element in ("fp4e2m1", "int4", "uint4"):
            fmt = parse_format(f"blks{scale}e{element}s2")
            maximum = fmt.elem.max_finite() if hasattr(fmt.elem, "max_finite") else fmt.elem.max_int
            for scale_rounding in ("nearest", "up"):
                values = [4 * fmt.scale.max_finite() * maximum, Fraction(0)]
                for rounding in ROUNDINGS:
                    options = {"block_scale_rounding": scale_rounding}
                    packed, _ = Rounder(rounding, 8).block(fmt, values, [0, 0], options)
                    assert fmt.split(packed)[1] == fmt.scale._max_finite_bits()
                    if rounding != "SR":
                        assert fmt.encode(values, rounding, scale_rounding) == packed
                    checks += 1
            for convention in ("saturate", "zero"):
                for special in (NAN, PINF, NINF):
                    values = [special, Fraction(1)]
                    packed, flags = Rounder().block(fmt, values, conv={"invalid_result": convention})
                    assert fmt.encode(values, invalid_result=convention) == packed
                    got = fmt.split(packed)[0][0]
                    if convention == "zero":
                        assert got == 0
                    elif element == "fp4e2m1":
                        assert got == (fmt.elem._max_finite_bits() | (8 if special is NINF else 0))
                    else:
                        assert got == fmt.elem.encode(fmt.elem.min_int if special is NINF else fmt.elem.max_int)
                    assert ("invalid" if special is NAN else "overflow") in flags[0]
                    checks += 1
    for element in ("fps0e4m3N", "fps0e4m3", "e8m0"):
        fmt = parse_format(f"blksfp8e4m3e{element}s2")
        maximum = fmt.elem.max_finite()
        for convention in ("saturate", "zero"):
            values = [-3 * maximum, 2 * maximum]
            packed, flags = Rounder().block(fmt, values, conv={"invalid_result": convention})
            assert fmt.encode(values, invalid_result=convention) == packed
            assert fmt.scale.decode(fmt.split(packed)[1]) == 2
            assert "invalid" in flags[0] and "overflow" not in flags[0]
            checks += 1
    print(f"PASS scalar entry regressions, GELU preservation and {checks} block reference cases")


if __name__ == "__main__":
    main()
