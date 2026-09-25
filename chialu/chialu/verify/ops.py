"""Frozen exact reference semantics for every chiALU op, defined over
formats — never over microarchitecture.

Integer ops (per int_encoding ring):
  add/sub wrap in the encoding's ring (twos: mod 2^w; ones: mod 2^w-1;
  sign_magnitude: magnitude wraps, sign follows the exact result; BCD:
  mod 10^d). add_sat/sub_sat/mul_sat clamp. adc = a+b+1, sbb = a-b-1
  (frozen convention: the template has no carry port). div/quot =
  truncated quotient, rem = sign of dividend, mod = sign of divisor;
  division by zero: quotient = all-ones pattern, rem/mod = a (RISC-V
  convention). Shifts take the amount as b mod width; shr_arith copies
  the encoding's sign. cmp -> {bit2:gt, bit1:eq, bit0:lt}. cvt_resize =
  value resize into the output width. popcount/clz/ctz/not/neg/abs are
  unary (b ignored where unused).

Float and posit ops (fadd..fcvt) are `alu_ref`'s, which this module
calls rather than repeating, so one reference covers each op. fcmp keeps
this module's result encoding {bit3:unordered, bit2:gt, bit1:eq,
bit0:lt}. fmin/fmax propagate a NaN operand, which is alu_ref's
`minmax_nan` default. fcvt converts to the signed integer of the output
width under `rounding`, and saturates.

SFU functions are correctly rounded via adaptive-precision mpmath
(elementwise); softmax/layernorm are vector-level, faithfully computed
at >= 4x working precision.

Dot/FMA is `dot_ref`'s under the fused contract, which this module calls
rather than repeating: exact sum of products (+C) then ONE rounding into
the accumulator format ("exact_then_round" golden); int combos are exact
in the wide accumulator by construction; the quire is exact fixed point.
"""

from __future__ import annotations

from fractions import Fraction

from chialu.verify.formats import (NAN, NAR, NINF, PINF, BCDFormat,
                                    FloatFormat, IntFormat, PositFormat,
                                    ScaledIntFormat, Special)

# ------------------------------------------------------------ integers --

INT_UNARY = {"neg", "abs", "not", "popcount", "clz", "ctz", "cvt_resize"}


def cvt_ref(fmt, a_bits, target, rounding="RNE", nan_to_int="zero"):
    """cvt(<format>): the value of a re-encoded in `target` — integer and
    fixed targets round under `rounding` and saturate, float targets
    round; NaN and NaR to an integer give `nan_to_int`."""
    from chialu.verify.formats import (BlockFormat, FloatFormat, IntFormat,
                                        PositFormat, ScaledIntFormat,
                                        X87Format, _round_int)
    v = fmt.decode(a_bits)
    if isinstance(target, BlockFormat) or isinstance(fmt, BlockFormat):
        raise ValueError("cvt to or from a block format: not implemented")
    if isinstance(target, (FloatFormat, X87Format, PositFormat)):
        if isinstance(v, Special):
            if v is NAR or v is NAN:
                return target.encode_special(NAN) if getattr(target, "has_nan", False) \
                    else (target._nar if isinstance(target, PositFormat)
                          else target._max_finite_bits())
            return target.round(v, rounding)
        return target.round(v, rounding)
    # integer or fixed target
    if isinstance(v, Special):
        if v is NAR or v is NAN:
            return {"zero": target.encode(0),
                    "max": target.encode(target.max_int),
                    "min": target.encode(target.min_int)}[nan_to_int]
        return target.encode(target.max_int if v is PINF else target.min_int)
    if isinstance(target, ScaledIntFormat):
        return target.round(v, rounding)          # rounds and saturates
    i = _round_int(v, rounding)
    return target.encode(target.saturate(i))


def int_ref(op, fmt, a_bits, b_bits, out_fmt=None):
    """Reference for one integer/BCD op. Returns output BITS in out_fmt
    (defaults to fmt; mul_wide needs the doubled format)."""
    out = out_fmt or fmt
    w = fmt.width
    if op in ("and", "or", "xor", "not"):          # bitwise: on patterns
        r = {"and": a_bits & b_bits, "or": a_bits | b_bits,
             "xor": a_bits ^ b_bits, "not": ~a_bits}[op]
        return r & ((1 << w) - 1)
    if op == "popcount":
        return bin(a_bits).count("1")
    if op == "clz":
        return w - a_bits.bit_length()
    if op == "ctz":
        return (a_bits & -a_bits).bit_length() - 1 if a_bits else w
    if op in ("shl", "shr_logical", "shr_arith", "rol", "ror"):
        sh = b_bits % w
        m = (1 << w) - 1
        if op == "shl":
            return (a_bits << sh) & m
        if op == "shr_logical":
            return (a_bits & m) >> sh
        if op == "rol":
            return ((a_bits << sh) | (a_bits >> (w - sh))) & m if sh else a_bits
        if op == "ror":
            return ((a_bits >> sh) | (a_bits << (w - sh))) & m if sh else a_bits
        s = (a_bits >> (w - 1)) & 1                # shr_arith on pattern
        fill = ((m << (w - sh)) & m) if s and sh else 0
        return ((a_bits & m) >> sh) | fill

    a, b = fmt.decode(a_bits), fmt.decode(b_bits)
    if op == "add":
        return out.encode(out.wrap(a + b))
    if op == "sub":
        return out.encode(out.wrap(a - b))
    if op == "adc":
        return out.encode(out.wrap(a + b + 1))
    if op == "sbb":
        return out.encode(out.wrap(a - b - 1))
    if op == "add_sat":
        return out.encode(out.saturate(a + b))
    if op == "sub_sat":
        return out.encode(out.saturate(a - b))
    if op == "neg":
        return out.encode(out.wrap(-a))
    if op == "abs":
        return out.encode(out.wrap(abs(a)))
    if op == "mul":
        return out.encode(out.wrap(a * b))
    if op == "mul_wide":
        return out.encode(out.wrap(a * b))         # out is the 2w format
    if op == "mul_high":
        full = a * b
        if isinstance(fmt, BCDFormat):
            return out.encode((full // 10 ** fmt.digits) % 10 ** fmt.digits)
        return out.encode(out.wrap(full >> w))
    if op == "mul_sat":
        return out.encode(out.saturate(a * b))
    if op in ("div", "quot", "rem", "mod"):
        if b == 0:
            if op in ("div", "quot"):
                return (1 << out.width) - 1        # all-ones quotient
            return a_bits                          # rem/mod = dividend
        q = abs(a) // abs(b)
        if (a < 0) != (b < 0):
            q = -q                                 # truncated quotient
        if op in ("div", "quot"):
            return out.encode(out.wrap(q))
        if op == "rem":
            return out.encode(out.wrap(a - b * q))
        return out.encode(out.wrap(a - b * (a // b)))   # floored mod
    if op == "min":
        return out.encode(min(a, b))
    if op == "max":
        return out.encode(max(a, b))
    if op == "cmp":
        return (4 if a > b else 0) | (2 if a == b else 0) | (1 if a < b else 0)
    if op == "cvt_resize":
        return out.encode(out.saturate(a))
    raise ValueError(f"int op {op}")


# -------------------------------------------------------------- floats --


def _fp2(op, fa, fb):
    """Exact rational op with IEEE special propagation. Returns
    Fraction | Special."""
    for x in (fa, fb):
        if x is NAN:
            return NAN
    inf_a = fa in (PINF, NINF)
    inf_b = fb in (PINF, NINF)
    if op in ("fadd", "fsub"):
        if op == "fsub":
            fb = {PINF: NINF, NINF: PINF}[fb] if inf_b else -fb
        if inf_a and inf_b:
            return fa if fa is fb else NAN
        if inf_a:
            return fa
        if inf_b:
            return fb
        return fa + fb
    if op == "fmul":
        if inf_a or inf_b:
            za = fa == 0 if not inf_a else False
            zb = fb == 0 if not inf_b else False
            if za or zb:
                return NAN
            neg = (fa is NINF or (not inf_a and fa < 0)) != \
                  (fb is NINF or (not inf_b and fb < 0))
            return NINF if neg else PINF
        return fa * fb
    if op == "fdiv":
        if inf_a and inf_b:
            return NAN
        if inf_a:
            neg = (fa is NINF) != (not inf_b and fb < 0)
            return NINF if neg else PINF
        if inf_b:
            return Fraction(0)
        if fb == 0:
            if fa == 0:
                return NAN
            return NINF if (fa < 0) else PINF      # sign of 0 not modeled
        return fa / fb
    raise ValueError(op)


def _sqrt_frac(x: Fraction, prec_bits: int) -> tuple:
    """(lo, hi) Fraction bounds on sqrt(x) with 2^-prec relative width."""
    from math import isqrt
    scale = 1 << (2 * prec_bits)
    n = x.numerator * scale
    d = x.denominator
    r = isqrt(n // d)
    lo = Fraction(r, 1 << prec_bits)
    hi = Fraction(r + 1, 1 << prec_bits)
    return lo, hi


def fp_ref(op, fmt, a_bits, b_bits, rounding="RNE", out_fmt=None,
           daz=False, ftz=False):
    """Reference for one float/posit op; returns output bits.

    The arithmetic is `alu_ref`'s under its default conventions, so this
    module holds no second float reference. Two details stay this
    module's own:

    * fcmp reports an unordered pair as bit 3 of the result, where
      alu_ref reports it as the `unordered` flag;
    * `out_fmt` names the integer target of fcvt, and applies to no
      other op.
    """
    from chialu.verify import alu_ref as A
    from chialu.verify.rounding import ROUNDINGS, Rounder
    out = out_fmt or fmt
    posit = isinstance(fmt, PositFormat)
    if out_fmt is not None and out_fmt is not fmt and op != "fcvt":
        raise ValueError(f"fp_ref({op}): out_fmt names the target of fcvt alone")
    mode = rounding
    if posit and mode not in ROUNDINGS:
        # PositFormat.round rounds to nearest under every mode outside
        # the posit standard's set, and Rounder takes that set alone.
        mode = "RNE"
    conv = {k: A.SPEC_DEFAULTS[k] for k in A.CONVENTION_NAMES}
    ctrl = {"daz_in": bool(daz), "ftz_out": bool(ftz)}
    rounder = Rounder(mode, A.default_sr_bits([(1, fmt)]), conv["sr_compare"],
                      conv["tininess"], ftz=bool(ftz) and not posit)
    if op == "fcvt":
        target = IntFormat(out.width, "twos_complement")
        outs, _w, _fl = A.cvt_op(fmt, target, [a_bits], conv, ctrl, rounder,
                                 None, 0)
        return outs[0]
    if posit:
        if op == "fcmp" and (fmt.decode(a_bits) is NAR or fmt.decode(b_bits) is NAR):
            return 0b1000
        bits, _w, _fl = A.posit_op(op, fmt, a_bits, b_bits, conv, ctrl, rounder)
        return bits
    bits, _w, flags = A.float_op(op, fmt, a_bits, b_bits, conv, ctrl, rounder)
    if op == "fcmp" and "unordered" in flags:
        return 0b1000
    return bits


def _daz(fmt: FloatFormat, v: Fraction) -> Fraction:
    if v == 0:
        return v
    min_normal = Fraction(2) ** (1 - fmt.bias)
    return Fraction(0) if abs(v) < min_normal else v


# ----------------------------------------------------------------- sfu --

SFU_UNARY = ("exp2", "exp", "log2", "log", "sin", "cos", "tanh",
             "sigmoid", "recip", "rsqrt", "sqrt", "gelu", "silu", "erf",
             "softplus")
SFU_VECTOR = ("softmax", "layernorm")


def _mp(fn, x, prec):
    import mpmath
    with mpmath.workprec(prec):
        mx = mpmath.mpf(x.numerator) / mpmath.mpf(x.denominator)
        v = {"exp2": lambda t: mpmath.power(2, t), "exp": mpmath.exp,
             "log2": lambda t: mpmath.log(t, 2), "log": mpmath.log,
             "sin": mpmath.sin, "cos": mpmath.cos, "tanh": mpmath.tanh,
             "sigmoid": lambda t: 1 / (1 + mpmath.exp(-t)),
             "rsqrt": lambda t: 1 / mpmath.sqrt(t),
             "sqrt": mpmath.sqrt,
             # erfc retains the negative tail when erf rounds to -1.
             "gelu": lambda t: t / 2 * mpmath.erfc(-t / mpmath.sqrt(2)),
             "silu": lambda t: t / (1 + mpmath.exp(-t)),
             "erf": mpmath.erf,
             "softplus": lambda t: max(t, 0) + mpmath.log1p(mpmath.exp(-abs(t))),
             }[fn](mx)
        return _mpf_to_fraction(v)


def _mpf_to_fraction(v):
    import mpmath
    if not mpmath.isfinite(v):
        if mpmath.isnan(v):
            return NAN
        return PINF if v > 0 else NINF
    sign, man, exp, _bc = mpmath.mpf(v)._mpf_
    if man == 0 and exp == 0:
        return Fraction(0)
    exp = int(exp)
    # an exponent beyond any format's range: a surrogate magnitude on the
    # same side of every boundary (the exact Fraction would be intractable)
    if exp > 1 << 16:
        f = Fraction(2) ** (1 << 16)
    elif exp < -(1 << 16):
        f = Fraction(1, 1 << 16) ** 4096
    else:
        f = Fraction(int(man)) * (Fraction(2) ** exp)
    return -f if sign else f


_SFU_DOMAIN_SPECIALS = {
    # fn -> (value at +inf, value at -inf); None = NaN
    "exp2": (PINF, Fraction(0)), "exp": (PINF, Fraction(0)),
    "log2": (PINF, None), "log": (PINF, None),
    "sin": (None, None), "cos": (None, None),
    "tanh": (Fraction(1), Fraction(-1)),
    "sigmoid": (Fraction(1), Fraction(0)),
    "recip": (Fraction(0), Fraction(0)),
    "rsqrt": (Fraction(0), None), "sqrt": (PINF, None),
    "gelu": (PINF, Fraction(0)), "silu": (PINF, Fraction(0)),
    "erf": (Fraction(1), Fraction(-1)),
    "softplus": (PINF, Fraction(0)),
}


def sfu_ref(fn, fmt, x_bits, rounding="RNE", daz=False, ftz=False):
    """Correctly-rounded elementwise SFU reference (adaptive precision)."""
    posit = isinstance(fmt, PositFormat)
    x = fmt.decode(x_bits)
    if x is NAR or x is NAN:
        return fmt.round(NAR if posit else NAN)
    if x in (PINF, NINF):
        at = _SFU_DOMAIN_SPECIALS[fn][0 if x is PINF else 1]
        return fmt.round(NAN if at is None else at)
    if daz and isinstance(fmt, FloatFormat):
        x = _daz(fmt, x)
    # exact singular points
    if fn in ("log", "log2") and x == 0:
        return fmt.round(NAR if posit else NINF)
    if fn in ("log", "log2", "sqrt", "rsqrt") and x < 0:
        return fmt.round(NAR if posit else NAN)
    if fn in ("recip", "rsqrt") and x == 0:
        return fmt.round(NAR if posit else PINF)
    exact = {("exp2", 0): Fraction(1), ("exp", 0): Fraction(1),
             ("sin", 0): Fraction(0), ("cos", 0): Fraction(1),
             ("tanh", 0): Fraction(0), ("erf", 0): Fraction(0),
             ("gelu", 0): Fraction(0), ("silu", 0): Fraction(0),
             ("sqrt", 0): Fraction(0),
             ("sigmoid", 0): Fraction(1, 2)}.get((fn, x))
    if exact is not None:
        return fmt.round(exact, rounding)
    if fn == "recip":
        return fmt.round(1 / x, rounding) if not isinstance(fmt, FloatFormat) \
            else fmt.round(1 / x, rounding, ftz=ftz)
    sur = _tail_surrogate(fn, fmt, x)
    if sur is not None:
        return fmt.round(sur, rounding) if not isinstance(fmt, FloatFormat) \
            else fmt.round(sur, rounding, ftz=ftz)
    from chialu.verify.sfu_precision import initial_precision
    prec = initial_precision(fn, fmt, x)
    max_precision = max(4096, 4 * prec)
    while prec < max_precision:
        lo = _mp(fn, x, prec)
        hi = _mp(fn, x, prec * 2)
        if isinstance(lo, Special) or isinstance(hi, Special):
            return fmt.round(hi if not isinstance(hi, Special)
                             else (NAR if posit else hi))
        blo = fmt.round(lo, rounding) if not isinstance(fmt, FloatFormat) \
            else fmt.round(lo, rounding, ftz=ftz)
        bhi = fmt.round(hi, rounding) if not isinstance(fmt, FloatFormat) \
            else fmt.round(hi, rounding, ftz=ftz)
        if blo == bhi:
            return blo
        prec *= 2
    raise ArithmeticError(f"sfu_ref({fn}): rounding undecided at {x}")


def _tail_surrogate(fn, fmt, x):
    """Choose a representative using the format's actual range and rounding grid."""
    from chialu.verify.sfu_ref import scalar_tail_surrogate
    return scalar_tail_surrogate(fn, fmt, x)


def sfu_vector_ref(fn, fmt, lane_bits, rounding="RNE"):
    """softmax / layernorm over one lane vector, faithful golden at
    high precision (>= 4x format width)."""
    import mpmath
    prec = fmt.width * 8 + 64
    with mpmath.workprec(prec):
        xs = []
        for b in lane_bits:
            v = fmt.decode(b)
            if isinstance(v, Special):
                return [fmt.round(NAN if not isinstance(fmt, PositFormat)
                                  else NAR)] * len(lane_bits)
            xs.append(mpmath.mpf(v.numerator) / mpmath.mpf(v.denominator))
        if fn == "softmax":
            m = max(xs)
            es = [mpmath.exp(x - m) for x in xs]
            s = sum(es)
            ys = [e / s for e in es]
        else:                                       # layernorm, eps = 0
            n = len(xs)
            mu = sum(xs) / n
            var = sum((x - mu) ** 2 for x in xs) / n
            sd = mpmath.sqrt(var) if var > 0 else mpmath.mpf(1)
            ys = [(x - mu) / sd for x in xs]
        return [fmt.round(_mpf_to_fraction(y), rounding) for y in ys]


# ----------------------------------------------------------- dot / fma --


def dot_ref(elem_fmt, acc_fmt, a_lanes, b_lanes, c_bits=None,
            rounding="RNE"):
    """D = sum(a_i * b_i) + C: exact accumulation, one final rounding.

    The arithmetic is `dot_ref.dot_expected` under the fused contract, so
    this module holds no second dot reference. The mode is built from the
    format objects rather than from their names, because a format a
    caller constructed need not have a name `parse_format` reads back.
    """
    from chialu.verify import dot_ref as D
    from chialu.verify.alu_ref import default_sr_bits
    accumulate = c_bits is not None
    mode = {"elements": len(a_lanes), "fab": elem_fmt,
            "fc": acc_fmt if accumulate else None, "fd": acc_fmt}
    spec = dict(D.DOT_DEFAULTS)
    spec["rounding"] = [rounding]
    spec["accumulate"] = accumulate
    spec["sr_bits"] = default_sr_bits([(1, elem_fmt), (1, acc_fmt)])
    lay = {"modes": [mode], "accumulate": accumulate, "flags": [],
           "d_w": acc_fmt.width,
           "v_max": D.n_outputs(mode) * D.roundings_per_output(mode, spec)}
    w = elem_fmt.width
    a_bits = b_bits = 0
    for i, (ab, bb) in enumerate(zip(a_lanes, b_lanes)):
        a_bits |= (ab & ((1 << w) - 1)) << (i * w)
        b_bits |= (bb & ((1 << w) - 1)) << (i * w)
    d, _flags = D.dot_expected(spec, lay, 0, a_bits, b_bits, c_bits,
                               {"rounding": rounding}, None)
    return d
