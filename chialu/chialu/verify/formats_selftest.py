"""Self-test of the format grammar and families (docs/formats-and-options.md
section 2): aliases equal their grammar forms, corners round-trip, the
special-value rules of every flag variant, fp80's explicit integer bit,
fixed point, generic quires and block quantization. Pure python.

    python3 -m chialu.verify.formats_selftest
"""
import sys
from fractions import Fraction

sys.set_int_max_str_digits(0)

from chialu.verify.formats import (ALIASES, NAN, NINF, PINF, NAR, BlockFormat,
                                    FixedFormat, FloatFormat, IntFormat,
                                    Special, X87Format, make_format,
                                    parse_format)
from chialu.verify.stimulus import Rng


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)


def roundtrip(fmt, pats):
    """decode -> encode restores every valid, non-NaN corner pattern."""
    for b in pats:
        if not fmt.valid(b):
            continue
        v = fmt.decode(b)
        if v is NAN or v is NAR:
            continue
        if isinstance(fmt, BlockFormat):
            continue
        back = fmt.encode(v)
        if v == 0 and back == 0:
            continue                      # -0 decodes to 0 (no signed zero in Fraction)
        if back != b:
            raise AssertionError(f"{fmt.name}: {b:#x} -> {back:#x}")


def main():
    n = 0
    # aliases are their grammar forms
    for alias, gram in ALIASES.items():
        a, g = parse_format(alias), parse_format(gram)
        check((a.width, a.exp_bits, a.man_bits, a.has_inf, a.has_nan, a.signed)
              == (g.width, g.exp_bits, g.man_bits, g.has_inf, g.has_nan, g.signed),
              f"alias {alias} != {gram}")
        check(a.grammar == gram, f"{alias}: grammar {a.grammar} != {gram}")
        n += 1
    # the old factory vocabulary still decodes identically on every pattern
    for old, new in (("fp16", "fps1e5m10NI"), ("bf16", "fps1e8m7NI"),
                     ("fp8e4m3", "fps1e4m3N"), ("fp8e5m2", "fps1e5m2NI"),
                     ("fp4", "fps1e2m1")):
        f_old, f_new = make_format(old), parse_format(new)
        for b in range(1 << f_old.width):
            vo, vn = f_old.decode(b), f_new.decode(b)
            check(vo == vn or (isinstance(vo, Special) and vo is vn),
                  f"{old} vs {new} at {b:#x}: {vo} {vn}")
        n += 1
    # flag variants
    e4 = parse_format("fp8e4m3")
    check(e4.decode(0x7F) is NAN and e4.decode(0x7E) == 448, "e4m3 NaN/max")
    e5 = parse_format("fp8e5m2")
    check(e5.decode(0x7C) is PINF and e5.decode(0x7D) is NAN, "e5m2 inf/NaN")
    f4 = parse_format("fp4e2m1")
    check(f4.decode(0x7) == 6 and f4.max_finite() == 6, "fp4 all finite")
    ionly = parse_format("fps1e5m2I")
    check(ionly.decode(0x7C) is PINF and ionly.decode(0x7D) == Fraction(2) ** 16 * Fraction(5, 4)
          or not isinstance(ionly.decode(0x7D), Special), "I-only top field finite")
    check(ionly.round(Fraction(2) ** 20, "RNE") == 0x7C, "I-only overflow to inf")
    check(ionly.round(Fraction(2) ** 20, "RTZ") == 0x7F, "I-only RTZ saturates")
    n += 1
    # E8M0: no zero, no sign, 0xFF NaN
    e8 = parse_format("e8m0")
    check(e8.width == 8 and not e8.signed and e8.exp_only, "e8m0 layout")
    check(e8.decode(0) == Fraction(2) ** -127 and e8.decode(127) == 1
          and e8.decode(254) == Fraction(2) ** 127 and e8.decode(255) is NAN, "e8m0 values")
    check(e8.round(Fraction(1), "RNE") == 127 and e8.round(Fraction(3), "RTZ") == 128
          and e8.round(Fraction(3), "RUP") == 129, "e8m0 rounding")
    check(e8.round(Fraction(0), "RNE") == 0 and e8.round(Fraction(2) ** 200, "RNE") == 254, "e8m0 clamps")
    n += 1
    # fp80: explicit integer bit
    x = parse_format("fp80")
    one = x.encode(Fraction(1))
    check(one == 0x3FFF8000000000000000, f"fp80 1.0 = {one:#x}")
    check(x.decode(one) == 1 and not x.valid(0x3FFF0000000000000000), "fp80 unnormal invalid")
    check(x.decode(0x7FFF8000000000000000) is PINF, "fp80 inf")
    roundtrip(x, x.corners()); n += 1
    # wide IEEE formats
    for name, w in (("fp64", 64), ("fp128", 128), ("tf32", 19), ("fp6e3m2", 6), ("fp6e2m3", 6)):
        f = parse_format(name); check(f.width == w, f"{name} width {f.width}")
        roundtrip(f, f.corners()); n += 1
    f64 = parse_format("fp64")
    check(f64.decode(f64.encode(Fraction(1, 3) * 0 + Fraction(3, 2))) == Fraction(3, 2), "fp64 1.5")
    check(f64.round(Fraction(1, 3), "RNE") == 0x3FD5555555555555, "fp64 1/3 RNE")
    # custom signless float with NaN and inf
    sl = parse_format("fps0e4m3NI")
    check(sl.width == 7 and sl.decode(0x78) is PINF and sl.decode(0x7C) is NAN, "signless flags")
    roundtrip(sl, sl.corners()); n += 1
    # integers, any width
    for name, w, enc in (("int24", 24, "twos_complement"), ("uint7", 7, "unsigned"),
                         ("int12_ones", 12, "ones_complement"), ("int9_sm", 9, "sign_magnitude")):
        f = parse_format(name); check((f.width, f.encoding) == (w, enc), name)
        roundtrip(f, f.corners()); n += 1
    check(parse_format("bcd4").width == 16 and parse_format("bcd4").max_int == 9999, "bcd4")
    # fixed point
    fx = parse_format("fxs1i7f8")
    check(fx.width == 16 and fx.decode(0x0100) == 1 and fx.decode(0xFF00) == -1
          and fx.encode(Fraction(3, 2)) == 0x0180, "fxs1i7f8 values")
    check(fx.round(Fraction(1, 3), "RNE") == 0x0055 and fx.round(Fraction(200), "RNE") == 0x7FFF, "fxs rounding/sat")
    ux = parse_format("fxs0i0f16")
    check(ux.width == 16 and ux.encoding == "unsigned" and ux.decode(0x8000) == Fraction(1, 2), "fxs0i0f16")
    roundtrip(fx, fx.corners()); roundtrip(ux, ux.corners()); n += 1
    # posit / quire generic
    p = parse_format("posit8_0"); check(p.width == 8 and p.decode(0x80) is NAR, "posit8_0")
    q = parse_format("quire16_1"); check(q.width == 128 and q.frac_bits == 56, "quire16_1")
    q2 = parse_format("quire32_2"); check(q2.width == 16 + 2 * 240 and q2.frac_bits == 240, "quire32_2")
    n += 1
    # block formats
    mx = parse_format("blksfps0e8m0Nefp4e2m1s32")
    check(mx.width == 32 * 4 + 8 and mx.size == 32 and mx.scale.exp_only, "mxfp4 layout")
    vals = [Fraction(k, 2) for k in range(32)]          # 0 .. 15.5
    b = mx.encode(vals)
    dec = mx.decode(b)
    check(mx.split(b)[1] == 128, f"mxfp4 scale field {mx.split(b)[1]} (expect 2^1 -> 128)")
    check(dec[0] == 0 and dec[12] == 6 and dec[31] == 12, f"mxfp4 decode {dec[:4]} .. {dec[31]}")
    # the OCP rule: every element is v / 2 rounded to the fp4 grid, saturated at 6
    exp = [mx.elem.decode(mx.elem.round(min(v / 2, Fraction(6)), "RNE")) * 2 for v in vals]
    check(dec == exp, f"mxfp4 elements {dec[:6]} vs {exp[:6]}")
    nv = parse_format("blksfp8e4m3efp4e2m1s16")
    b2 = nv.encode([Fraction(3)] * 16)
    check(all(d == 3 for d in nv.decode(b2)), f"nvfp4 3.0 blocks {nv.decode(b2)[:3]}")
    mi = parse_format("blksfps0e8m0Neint8s32")
    b3 = mi.encode([Fraction(k) for k in range(-16, 16)])
    check(mi.decode(b3) == [Fraction(k) for k in range(-16, 16)], "mxint8 exact")
    bad = mx.join([0] * 32, 255)
    check(not mx.valid(bad) and mx.decode(bad)[0] is NAN, "NaN scale block invalid")
    roundtrip(mx, mx.corners()); n += 1
    rng = Rng(7)
    for _ in range(50):
        check(mx.valid(mx.sample(rng)) and nv.valid(nv.sample(rng)), "block samples valid")
    for bad in ("fps1e1m3", "uint8_sm", "blksint8efp4e2m1s16", "blksfps0e8m0Nefp4e2m1s1", "fpx"):
        try:
            parse_format(bad); check(False, f"{bad} accepted")
        except ValueError:
            pass
    print(f"[formats_selftest] {n} groups pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
