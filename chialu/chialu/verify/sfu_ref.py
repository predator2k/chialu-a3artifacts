"""chialu.VecSFU on modes (docs/formats-and-options.md section 5): the
port layout, the slot table semantics and the exact reference of one
vector.

A mode is {count, format} over floats, custom floats, posits and blocks.
`functions` are the named fixed functions (fn_sel 0..F-1), the
reconfigurable slots follow (fn_sel F..F+R-1). A slot holds one table of
`segments` entries loaded through tbl_we[slot] / tbl_addr / tbl_data on
posedge clk (the datapath itself stays combinational); entry k holds the
coefficients c0 | c1 << w | c2 << 2w (pwq only) in the mode's widest
format. Segment k covers the patterns whose value-ordered index u (the
format's index shifted to 0..2^w-1) satisfies floor(u * K / 2^w) == k,
x_k is the value of the first pattern of the segment, and the slot
computes c0 + c1 (x - x_k) [+ c2 (x - x_k)^2] exactly, rounded once.
"""
from __future__ import annotations

from fractions import Fraction

from chialu.verify.alu_ref import _read, default_sr_bits
from chialu.verify.formats import (NAN, NAR, NINF, PINF, BlockFormat,
                                    FloatFormat, PositFormat, Special,
                                    X87Format, _mask, parse_format)
from chialu.verify.rounding import Rounder, flag_word, is_subnormal

FUNCTIONS = ("none", "exp2", "exp", "log2", "log", "sin", "cos", "tanh",
             "sigmoid", "recip", "rsqrt", "sqrt", "gelu", "silu", "erf",
             "softplus", "softmax", "layernorm")
VECTOR_FNS = ("softmax", "layernorm")
SFU_DEFAULTS = {"rounding": ["RNE"], "daz_in": [False], "ftz_out": [False],
                "flags": [], "reconfig_slots": 0, "slots": [],
                "nan_payload": "canonical", "invalid_result": "saturate",
                "nan_to_int": "zero", "minmax_nan": "propagate",
                "tininess": "after", "int_div_zero": "riscv",
                "zero_sign": "positive", "quire_overflow": "wrap",
                "block_scale_rounding": "nearest",
                "block_element_overflow": "saturate", "sr_compare": "gt",
                "check_flags": False}
SFU_RUNTIME = ("rounding", "daz_in", "ftz_out")


def normalize_sfu_spec(spec: dict) -> dict:
    out = dict(spec)
    for k, v in SFU_DEFAULTS.items():
        out.setdefault(k, list(v) if isinstance(v, list) else v)
    for k in SFU_RUNTIME:
        if not isinstance(out[k], (list, tuple)):
            out[k] = [out[k]]
        out[k] = list(out[k])
    out["functions"] = [f for f in (out.get("functions") or []) if f != "none"]
    modes = [(int(m["count"]), parse_format(str(m["format"]))) for m in out["modes"]]
    if not out.get("sr_bits"):
        out["sr_bits"] = default_sr_bits(modes)
    return out


def validate_sfu_modes(modes, spec):
    for n, f in modes:
        base = f.elem if isinstance(f, BlockFormat) else f
        if not isinstance(base, (FloatFormat, X87Format, PositFormat)):
            raise ValueError(f"{f.name}: SFU modes are floats, custom floats, posits "
                             f"or blocks of float elements")
        if isinstance(f, BlockFormat) and spec.get("slots"):
            raise ValueError(f"{f.name}: reconfigurable slots take scalar modes")
    if not spec.get("functions") and not spec.get("slots"):
        raise ValueError("no fixed functions and no reconfigurable slots")


def n_results(count, fmt) -> int:
    return count * (fmt.size if isinstance(fmt, BlockFormat) else 1)


def coeff_words(slot) -> int:
    return 3 if slot["approx"] == "pwq" else 2


def sfu_layout(spec: dict) -> dict:
    from chialu.verify.ports import Port
    spec = normalize_sfu_spec(spec)
    modes = [(int(m["count"]), parse_format(str(m["format"]))) for m in spec["modes"]]
    fns = list(spec["functions"])
    slots = list(spec.get("slots") or [])
    total = len(fns) + len(slots)
    x_w = max(n * f.width for n, f in modes)
    w_max = max(f.width for _, f in modes)
    v_max = max(n_results(n, f) for n, f in modes)
    sr = "SR" in spec["rounding"]
    sr_bits = int(spec["sr_bits"])
    flags = list(spec.get("flags") or ())
    core_in = []
    if slots:
        core_in.append(Port("clk", "in", 1))
    core_in.append(Port("x", "in", x_w))
    if total > 1:
        core_in.append(Port("fn_sel", "in", max(1, (total - 1).bit_length())))
    if len(modes) > 1:
        core_in.append(Port("mode", "in", max(1, (len(modes) - 1).bit_length())))
    if sr:
        core_in.append(Port("sr_rnd", "in", v_max * sr_bits))
    controls = {}
    for name in SFU_RUNTIME:
        vals = list(spec.get(name) or [])
        if len(vals) > 1:
            core_in.append(Port(f"{name}_sel", "in", max(1, (len(vals) - 1).bit_length())))
            controls[name] = vals
    tbl = {}
    if slots:
        seg_max = max(s["segments"] for s in slots)
        cw = max(coeff_words(s) for s in slots) * w_max
        tbl = {"addr_w": max(1, (seg_max - 1).bit_length()), "data_w": cw, "w_max": w_max}
        core_in.append(Port("tbl_we", "in", len(slots)))
        core_in.append(Port("tbl_addr", "in", tbl["addr_w"]))
        core_in.append(Port("tbl_data", "in", cw))
    core_out = [Port("y", "out", x_w)]
    if flags:
        core_out.append(Port("flags", "out", v_max * len(flags)))
    return {"modes": modes, "functions": fns, "slots": slots, "total": total,
            "core_in": core_in, "core_out": core_out, "x_w": x_w, "w_max": w_max,
            "v_max": v_max, "sr": sr, "sr_bits": sr_bits, "controls": controls,
            "flags": flags, "tbl": tbl}


# ------------------------------------------------------------ slots --

def value_index(fmt, bits) -> int:
    """The value-ordered index of a pattern shifted to 0..2^w-1."""
    w = fmt.width
    core = fmt.core if isinstance(fmt, X87Format) else fmt
    if isinstance(fmt, PositFormat):
        return (fmt.index(bits) + (1 << (w - 1))) & _mask(w)
    if getattr(core, "signed", True):
        # sign-magnitude patterns: negatives reversed below the positives
        top = 1 << (w - 1)
        if bits & top:
            return (top - 1) - (bits & (top - 1))
        return top + bits
    return bits & _mask(w)


def segment_of(fmt, bits, K) -> int:
    return (value_index(fmt, bits) * K) >> fmt.width


def segment_start_value(fmt, k, K):
    """x_k: the value of the first pattern of segment k (None when it is
    a NaN / NaR / infinity)."""
    w = fmt.width
    u = -(-(k << w) // K)                     # ceil(k * 2^w / K)
    # invert value_index
    if isinstance(fmt, PositFormat):
        bits = (u - (1 << (w - 1))) & _mask(w)
    else:
        core = fmt.core if isinstance(fmt, X87Format) else fmt
        top = 1 << (w - 1)
        if getattr(core, "signed", True):
            bits = (u - top) if u >= top else (top | ((top - 1) - u))
        else:
            bits = u
    if not fmt.valid(bits):
        return None
    v = fmt.decode(bits)
    return None if isinstance(v, Special) else v


def slot_eval(slot, fmt, table, x_bits, daz):
    """The exact polynomial of a slot at pattern x_bits with the loaded
    table (list of coefficient pattern tuples). Returns (value|Special,
    flags)."""
    K = slot["segments"]
    fl = set()
    v, s, den = _read(fmt, x_bits, daz) if not isinstance(fmt, PositFormat) else (fmt.decode(x_bits), 0, False)
    if den:
        fl.add("denormal")
    if isinstance(v, Special):
        fl.add("invalid")
        return (NAR if isinstance(fmt, PositFormat) else NAN), fl
    k = segment_of(fmt, x_bits, K)
    xk = segment_start_value(fmt, k, K)
    coeffs = [fmt.decode(c) for c in table[k]]
    if xk is None or any(isinstance(c, Special) for c in coeffs):
        fl.add("invalid")
        return (NAR if isinstance(fmt, PositFormat) else NAN), fl
    d = v - xk
    y = coeffs[0] + coeffs[1] * d
    if len(coeffs) > 2:
        y += coeffs[2] * d * d
    return y, fl


# ------------------------------------------------------------ reference --

def _round_out(fmt, v, rounder, word, zero_sign=0, conv=None, nan_operands=()):
    """One result value into the mode's scalar format with flags."""
    from chialu.verify.alu_ref import _nan_result
    if isinstance(fmt, PositFormat):
        return rounder.posit(fmt, v)
    core = fmt.core if isinstance(fmt, X87Format) else fmt
    if v is NAN or v is NAR:
        b, f = _nan_result(fmt, conv or {}, nan_operands, invalid_sign=0)
        return b, f
    if not core.signed and ((v is NINF) or (not isinstance(v, Special) and v < 0)):
        b, f = _nan_result(fmt, conv or {}, nan_operands, invalid_sign=1)
        return b, f | {"invalid"}
    return rounder.float(fmt, v, word, zero_sign)


def fn_value(fn, fmt, v, sign):
    """The exact function value with its operand flags.

    The value is a Fraction, a Special, ('irr', fn, x) for an irrational
    to be resolved by bounds, or ('zero', sign bit) for a zero whose sign
    a Fraction cannot carry. `resolve` rounds every one of these, so a
    caller that rounds through `resolve` needs no case of its own.
    """
    from chialu.verify.ops import _SFU_DOMAIN_SPECIALS
    fl = set()
    posit = isinstance(fmt, PositFormat)
    nan = NAR if posit else NAN
    if v is NAR or v is NAN:
        return nan, {"invalid"}
    if v in (PINF, NINF):
        at = _SFU_DOMAIN_SPECIALS[fn][0 if v is PINF else 1]
        if at is None:
            return nan, {"invalid"}
        if fn == "recip" and not posit:
            # IEEE 754-2019 section 6.3 gives a quotient the exclusive or
            # of the operand signs, so 1/(-inf) is -0 and 1/(+inf) is +0.
            return ("zero", 1 if v is NINF else 0), fl
        return at, fl
    if fn in ("log", "log2") and v == 0:
        return (NAR if posit else NINF), {"div_zero"}
    if fn in ("log", "log2", "sqrt", "rsqrt") and v < 0:
        return nan, {"invalid"}
    if fn in ("recip", "rsqrt") and v == 0:
        # IEEE 754-2019 section 9.2.1: 1/(-0) and rSqrt(-0) are both -inf.
        return (NAR if posit else (NINF if sign else PINF)), {"div_zero"}
    exact = {("exp2", 0): Fraction(1), ("exp", 0): Fraction(1), ("sin", 0): Fraction(0),
             ("cos", 0): Fraction(1), ("tanh", 0): Fraction(0), ("erf", 0): Fraction(0),
             ("gelu", 0): Fraction(0), ("silu", 0): Fraction(0), ("sqrt", 0): Fraction(0),
             ("sigmoid", 0): Fraction(1, 2)}.get((fn, v))
    if exact is not None:
        return exact, fl
    if fn == "recip":
        return 1 / v, fl
    if fn in ("sqrt", "rsqrt"):
        from chialu.verify.alu_ref import _exact_sqrt
        ex = _exact_sqrt(v)
        if ex is not None:
            return (ex if fn == "sqrt" else 1 / ex), fl
    if fn == "log" and v == 1:
        return Fraction(0), fl
    if fn == "log2" and v.numerator & (v.numerator - 1) == 0 and v.denominator & (v.denominator - 1) == 0:
        return Fraction(v.numerator.bit_length() - v.denominator.bit_length()), fl
    if fn == "exp2" and v.denominator == 1 and abs(v) < 4096:
        return Fraction(2) ** int(v), fl
    return ("irr", fn, v), fl


def resolve(fmt, val, rounder, word, zero_sign=0, conv=None, nan_operands=()):
    """Round a fn_value result into fmt: exact values directly, a signed
    zero under the sign fn_value determined, an irrational through bounds
    refined until the rounding is decided."""
    from chialu.verify.ops import _mp
    if isinstance(val, tuple) and val[0] == "zero":
        return _round_out(fmt, Fraction(0), rounder, word, val[1], conv, nan_operands)
    if not isinstance(val, tuple):
        return _round_out(fmt, val, rounder, word, zero_sign, conv, nan_operands)
    _, fn, x = val
    sur = scalar_tail_surrogate(fn, fmt, x, rounder.sr_bits)
    if sur is not None:
        b, f = _round_out(fmt, sur, rounder, word, zero_sign, conv, nan_operands)
        return b, f | {"inexact"}
    from chialu.verify.sfu_precision import initial_precision
    prec = initial_precision(fn, fmt, x, rounder.sr_bits)
    max_precision = max(1 << 15, 4 * prec)
    while prec < max_precision:
        evaluate = _stable_softplus if fn == "softplus" else lambda v, p: _mp(fn, v, p)
        lo = evaluate(x, prec)
        hi = evaluate(x, prec * 2)
        if isinstance(lo, Special) or isinstance(hi, Special):
            return _round_out(fmt, hi, rounder, word, zero_sign, conv, nan_operands)
        b1, f1 = _round_out(fmt, lo, rounder, word, zero_sign, conv, nan_operands)
        b2, f2 = _round_out(fmt, hi, rounder, word, zero_sign, conv, nan_operands)
        if b1 == b2 and f1 == f2:
            return b1, f1 | {"inexact"}
        prec *= 2
    raise ArithmeticError(f"sfu {fn}: rounding undecided at {x}")


def _stable_softplus(value, precision):
    """Evaluate softplus without losing a representable negative tail to 1+epsilon."""
    import mpmath
    with mpmath.workprec(precision):
        x = mpmath.mpf(value.numerator) / value.denominator
        result = max(x, 0) + mpmath.log1p(mpmath.exp(-abs(x)))
        sign, mantissa, exponent, _ = result._mpf_
        exact = Fraction(int(mantissa)) * Fraction(2) ** int(exponent)
        return -exact if sign else exact


def scalar_tail_surrogate(fn, fmt, x, sr_bits=8):
    """Format-relative scalar tails, preserving the side of each rounding boundary.

    Zero tails use the actual minimum positive value. Unit and linear tails
    use the local relative precision, so cancellation is handled before a
    finite-precision evaluator can mistake 1±epsilon or x±epsilon for exact
    1 or x. This does not alter the legacy functions in verify.ops.
    """
    if isinstance(x, Special):
        return None
    from math import isqrt
    from chialu.verify.formats import _floor_log2
    core = fmt.core if isinstance(fmt, X87Format) else fmt
    if isinstance(core, PositFormat):
        minimum = core.decode(1)
        maximum = core.decode((1 << (core.width - 1)) - 1)
        precision = core.width
    else:
        minimum, maximum = core.min_positive(), core.max_finite()
        precision = core.man_bits + 1
    zero_tiny = minimum * Fraction(2) ** -(int(sr_bits) + 32)
    relative_bits = 2 * precision + int(sr_bits) + 32
    relative_tiny = Fraction(2) ** -relative_bits
    low = max(1, -_floor_log2(zero_tiny) + 4)
    high = max(1, _floor_log2(maximum) + 4)
    huge = maximum * 4
    if fn == "exp2":
        if x > high:
            return huge
        if x < -low:
            return zero_tiny
    if fn == "exp":
        if x > high:
            return huge
        if x < -low:
            return zero_tiny
    if fn == "softplus":
        if x > relative_bits:
            return x + x * relative_tiny
        if x < -low:
            return zero_tiny
    if fn == "sigmoid":
        if x > relative_bits:
            return 1 - relative_tiny
        if x < -low:
            return zero_tiny
    if fn in ("tanh", "erf"):
        threshold = isqrt(relative_bits) + 1 if fn == "erf" else (relative_bits + 3) // 2
        if x > threshold:
            return 1 - relative_tiny
        if x < -threshold:
            return -1 + relative_tiny
    if fn in ("gelu", "silu"):
        positive = isqrt(2 * relative_bits) + 1 if fn == "gelu" else relative_bits
        negative = isqrt(2 * low) + 1 if fn == "gelu" else 2 * low
        if x > positive:
            return x * (1 - relative_tiny)
        if x < -negative:
            return -zero_tiny
    return None


def block_tail_surrogate(fn, fmt, x, sr_bits=8):
    """A tail representative beyond every rounding boundary of a block.

    The range includes the scale as well as the element. Each overflowing
    value is replaced only once its magnitude exceeds the entire block's
    finite range by a conservative margin, so this cannot discard a useful
    ratio between two values that still influence the selected scale.
    Tiny displacements retain which side of zero, one, or x the function
    approaches, including directed and stochastic rounding boundaries.
    """
    if isinstance(x, Special):
        return None
    from math import isqrt
    from chialu.verify.formats import _floor_log2
    maximum = fmt.scale.max_finite() * fmt.elem.max_finite()
    quantum = fmt.scale.min_positive() * fmt.elem.min_positive()
    margin = 4 * (fmt.scale.width + fmt.elem.width) + int(sr_bits) + 64
    tiny = quantum * Fraction(2) ** -margin / max(Fraction(1), maximum, abs(x))
    huge = maximum * 4
    hi = _floor_log2(maximum) + 4
    low = max(1, -_floor_log2(tiny) + 4)
    # 0.7 is above ln(2); the extra factor-of-four margins keep the
    # comparisons away from any representable output boundary.
    if fn == "exp2":
        if x > hi:
            return huge
        if x < -low:
            return tiny
    if fn == "exp":
        if x > max(1, hi) * Fraction(7, 10):
            return huge
        if x < -low * Fraction(7, 10):
            return tiny
    if fn == "softplus":
        if x > low:
            return x + tiny
        if x < -low:
            return tiny
    if fn == "sigmoid":
        if x > low:
            return 1 - tiny
        if x < -low:
            return tiny
    if fn in ("tanh", "erf"):
        threshold = isqrt(low) + 5 if fn == "erf" else low
        if x > threshold:
            return 1 - tiny
        if x < -threshold:
            return -1 + tiny
    if fn in ("gelu", "silu"):
        threshold = isqrt(2 * low) + 8 if fn == "gelu" else 2 * low
        if x > threshold:
            return x * (1 - tiny)
        if x < -threshold:
            return -tiny
    return None


def sfu_expected(spec, lay, mi, fn_idx, x_bits, ctrl, words, tables):
    """Expected (y, flags) of one vector: mode mi, function/slot fn_idx,
    x the packed operand, tables the loaded slot tables."""
    count, fmt = lay["modes"][mi]
    fns, slots = lay["functions"], lay["slots"]
    rounder = Rounder(ctrl.get("rounding", "RNE"), spec["sr_bits"], spec.get("sr_compare", "gt"),
                      spec.get("tininess", "after"), ftz=bool(ctrl.get("ftz_out", False)))
    daz = bool(ctrl.get("daz_in", False))
    words = words or [0] * lay["v_max"]
    names = lay["flags"]
    nf = len(names)
    w = fmt.width
    block = isinstance(fmt, BlockFormat)
    is_slot = fn_idx >= len(fns)
    y = 0
    fw = 0
    if not block:
        vals = []
        for i in range(count):
            xb = (x_bits >> (i * w)) & _mask(w)
            if is_slot:
                slot = slots[fn_idx - len(fns)]
                val, fl = slot_eval(slot, fmt, tables[fn_idx - len(fns)], xb, daz)
                b, f2 = _round_out(fmt, val, rounder, words[i])
                fl |= f2
                y |= (b & _mask(w)) << (i * w)
                if nf:
                    fw |= flag_word(fl, names) << (i * nf)
            else:
                fn = fns[fn_idx]
                v, s, den = _read(fmt, xb, daz) if not isinstance(fmt, PositFormat) else (fmt.decode(xb), 0, False)
                vals.append((v, s, den))
        if not is_slot:
            fn = fns[fn_idx]
            if fn in VECTOR_FNS:
                outs, fls = vector_fn(fn, fmt, [v[0] for v in vals], rounder, words)
                for i, (b, fl) in enumerate(zip(outs, fls)):
                    if vals[i][2]:
                        fl.add("denormal")
                    y |= (b & _mask(w)) << (i * w)
                    if nf:
                        fw |= flag_word(fl, names) << (i * nf)
            else:
                for i, (v, s, den) in enumerate(vals):
                    val, fl = fn_value(fn, fmt, v, s)
                    if den:
                        fl.add("denormal")
                    operands = [(x_bits >> (i * w)) & _mask(w)] if v is NAN else []
                    b, f2 = resolve(fmt, val, rounder, words[i], s if fn in ("sin", "tanh", "erf", "gelu", "silu", "sqrt") else 0,
                                    spec, operands)
                    y |= (b & _mask(w)) << (i * w)
                    if nf:
                        fw |= flag_word(fl | f2, names) << (i * nf)
        return y & _mask(lay["x_w"]), fw
    # block modes: per element, each result block re-quantized
    fn = fns[fn_idx]
    size = fmt.size
    all_vals = []
    for i in range(count):
        bb = (x_bits >> (i * w)) & _mask(w)
        elems, sb = fmt.split(bb)
        sc = fmt.scale.decode(sb)
        for eb in elems:
            v = fmt.elem.decode(eb)
            s = (eb >> (fmt.elem.width - 1)) & 1 if fmt.elem.signed else 0
            den = is_subnormal(fmt.elem, eb)
            if daz and den:
                v = Fraction(0)
            all_vals.append((v if isinstance(v, Special) else v * sc, s, den))
    if fn in VECTOR_FNS:
        # the vector functions reduce over every element of every block; the
        # results are quantized per block
        from chialu.verify.ops import sfu_vector_ref
        elem_vals = [v[0] for v in all_vals]
        wide = FloatFormat("wide", 15, 112, True, True)
        outs_bits = sfu_vector_ref(fn, wide, [wide.round(v, "RNE") if not isinstance(v, Special) else wide.encode_special(NAN if v is NAR else v) for v in elem_vals], "RNE")
        res = [wide.decode(b) for b in outs_bits]
        fls = [set() for _ in res]
        zero_signs = [0 for _ in res]
    else:
        res, fls, zero_signs = [], [], []
        for v, s, den in all_vals:
            val, fl = fn_value(fn, fmt.elem, v, s)
            if den:
                fl.add("denormal")
            zs = 0
            if isinstance(val, tuple) and val[0] == "zero":
                val, zs = Fraction(0), val[1]
            elif isinstance(val, tuple):
                # deep in an asymptote the exact path is intractable: the
                # surrogate sits on the same side of every rounding boundary
                sur = block_tail_surrogate(val[1], fmt, val[2], spec["sr_bits"])
                val = sur if sur is not None else ("irr", val[1], val[2])
                fl.add("inexact")
            res.append(val)
            fls.append(fl)
            zero_signs.append(zs)
    for i in range(count):
        chunk = res[i * size:(i + 1) * size]
        wds = words[i * size:(i + 1) * size]
        sgn = zero_signs[i * size:(i + 1) * size]

        def quant(prec):
            from chialu.verify.ops import _mp
            lo_vals, hi_vals = [], []
            for val in chunk:
                if isinstance(val, tuple):
                    lo_vals.append(_mp(val[1], val[2], prec))
                    hi_vals.append(_mp(val[1], val[2], prec * 2))
                else:
                    lo_vals.append(val)
                    hi_vals.append(val)
            b1, e1 = rounder.block(fmt, lo_vals, wds, spec, sgn)
            b2, e2 = rounder.block(fmt, hi_vals, wds, spec, sgn)
            return (b1, e1) if (b1 == b2 and e1 == e2) else None
        prec = fmt.width + 32
        while True:
            q = quant(prec)
            if q is not None:
                break
            prec *= 2
            if prec > 1 << 15:
                raise ArithmeticError("block sfu rounding undecided")
        bits, ef = q
        y |= (bits & _mask(w)) << (i * w)
        if nf:
            for j in range(size):
                fw |= flag_word(fls[i * size + j] | ef[j], names) << ((i * size + j) * nf)
    return y & _mask(lay["x_w"]), fw


def vector_fn(fn, fmt, vals, rounder, words):
    """softmax / layernorm over the values of a scalar mode, faithful at
    high precision, each result rounded under the unit's rounding."""
    import mpmath
    from chialu.verify.ops import _mpf_to_fraction
    posit = isinstance(fmt, PositFormat)
    if any(isinstance(v, Special) for v in vals):
        nan = NAR if posit else NAN
        outs = [_round_out(fmt, nan, rounder, 0) for _ in vals]
        return [o[0] for o in outs], [o[1] | {"invalid"} for o in outs]
    prec = fmt.width * 8 + 64
    with mpmath.workprec(prec):
        xs = [mpmath.mpf(v.numerator) / mpmath.mpf(v.denominator) for v in vals]
        if fn == "softmax":
            m = max(xs)
            es = [mpmath.exp(x - m) for x in xs]
            s = sum(es)
            ys = [e / s for e in es]
        else:
            n = len(xs)
            mu = sum(xs) / n
            var = sum((x - mu) ** 2 for x in xs) / n
            sd = mpmath.sqrt(var) if var > 0 else mpmath.mpf(1)
            ys = [(x - mu) / sd for x in xs]
        outs = [_round_out(fmt, _mpf_to_fraction(y), rounder, words[i]) for i, y in enumerate(ys)]
    return [o[0] for o in outs], [o[1] | {"inexact"} for o in outs]


def vector_ctrl(spec, meta_ctrl):
    ctrl = {}
    for name in SFU_RUNTIME:
        vals = list(spec.get(name) or [])
        if vals:
            ctrl[name] = vals[0]
    ctrl.update(meta_ctrl or {})
    return ctrl
