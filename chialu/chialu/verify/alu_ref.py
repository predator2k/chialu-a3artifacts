"""The exact reference of chialu.ALU over every family, op and option
(docs/formats-and-options.md sections 3 and 4): one vector of one
(mode, op) pair in, the expected y, d and flags words out. Every value
is an exact rational; rounding, SR words, daz_in/ftz_out, the flags and
the convention options go through chialu.verify.rounding.Rounder.
"""
from __future__ import annotations

from fractions import Fraction
from math import isqrt

from chialu.verify.formats import (NAN, NAR, NINF, PINF, BCDFormat,
                                    BlockFormat, FixedFormat, FloatFormat,
                                    IntFormat, PositFormat, ScaledIntFormat,
                                    Special, X87Format, _mask)
from chialu.verify.ops import _fp2, _sqrt_frac
from chialu.verify.rounding import (Rounder, flag_word, float_core,
                                     is_subnormal)

UNARY = {"neg", "abs", "not", "popcount", "clz", "ctz", "fabs", "fneg",
         "fsqrt"}
ARITH_EXACT = {"add": lambda a, b: a + b, "sub": lambda a, b: a - b,
               "adc": lambda a, b: a + b + 1, "sbb": lambda a, b: a - b - 1,
               "neg": lambda a, b: -a, "abs": lambda a, b: abs(a),
               "add_sat": lambda a, b: a + b, "sub_sat": lambda a, b: a - b,
               "mul": lambda a, b: a * b, "mul_sat": lambda a, b: a * b,
               "mul_high": lambda a, b: a * b, "mul_wide": lambda a, b: a * b}
FLOAT_ARITH = {"fadd", "fsub", "fmul", "fdiv", "fsqrt"}
# the fused multiply-add ops of the RISC-V F extension (HardFloat's MulAddRecFN op codes 0..3, FPnew's FMADD and
# FNMSUB with op_mod): (the product negated, the addend negated) for d = (-1)^np * a * b + (-1)^nc * c; they read a
# third operand c and round once under fma_contract fused, or round the product first under sequential
FUSED_OPS = {"fmadd": (0, 0), "fmsub": (0, 1), "fnmsub": (1, 0), "fnmadd": (1, 1)}


def family_of(fmt) -> str:
    if isinstance(fmt, BlockFormat):
        return "block"
    if isinstance(fmt, PositFormat):
        return "posit"
    if isinstance(fmt, (FloatFormat, X87Format)):
        return "float"
    if isinstance(fmt, FixedFormat):
        return "fixed"
    return "integer"


def is_cvt(op):
    return op.startswith("cvt(")


def cvt_target(op):
    from chialu.verify.formats import parse_format
    return parse_format(op[4:-1]) if is_cvt(op) else None


def _pattern_int(fmt):
    """The integer format whose patterns a fixed-point format shares."""
    if isinstance(fmt, FixedFormat):
        return IntFormat(fmt.width, fmt.encoding)
    return fmt


def _sign_of(fmt, bits):
    if isinstance(fmt, X87Format):
        return (bits >> 79) & 1
    core, _ = float_core(fmt)
    return (bits >> (core.width - 1)) & 1 if core.signed else 0


# ------------------------------------------------------------ integers --

def _int_flags(op, fmt, pa, pb, exact, res_val):
    """carry (unsigned carry/borrow on the patterns), int_overflow (two's
    complement overflow on the patterns), overflow (the exact value is
    outside the format), div_zero."""
    fl = set()
    w = fmt.width
    if isinstance(fmt, BCDFormat):
        top = 10 ** fmt.digits
        if op in ("add", "adc"):
            fl |= {"carry"} if (fmt.decode(pa) + fmt.decode(pb) + (op == "adc")) >= top else set()
        elif op in ("sub", "sbb"):
            fl |= {"carry"} if fmt.decode(pa) < fmt.decode(pb) + (op == "sbb") else set()
        if exact is not None and not (0 <= exact <= fmt.max_int):
            fl |= {"overflow", "int_overflow"}
        return fl
    m = _mask(w)
    if op in ("add", "adc"):
        fl |= {"carry"} if (pa + pb + (op == "adc")) > m else set()
    elif op in ("sub", "sbb"):
        fl |= {"carry"} if pa < pb + (op == "sbb") else set()
    elif op == "neg":
        fl |= {"carry"} if pa != 0 else set()
    if op in ARITH_EXACT:
        tw = IntFormat(w, "twos_complement")
        sa, sb = tw.decode(pa), tw.decode(pb)
        s_exact = ARITH_EXACT[op](sa, sb)
        if not (tw.min_int <= s_exact <= tw.max_int):
            fl.add("int_overflow")
        if exact is not None and not (fmt.min_int <= exact <= fmt.max_int):
            fl.add("overflow")
    if op in ("div", "quot") and exact is not None \
            and not (fmt.min_int <= exact <= fmt.max_int):
        fl |= {"overflow", "int_overflow"}
    return fl


def _eac(w, s):
    """The end-around-carry adder's pattern for a ones' complement sum."""
    m = _mask(w)
    if s == 0:
        return 0
    r = s % m
    return r if r else m


def int_op(op, fmt, pa, pb, conv, rounder, word=None):
    """One integer or BCD op on patterns; returns (bits, w_out, flags)."""
    from chialu.verify.ops import int_ref
    w = fmt.width
    zero_sign = conv.get("zero_sign", "positive")
    div_zero = conv.get("int_div_zero", "riscv")
    fl = set()
    a = fmt.decode(pa)
    b = fmt.decode(pb)
    if op in ("div", "quot", "rem", "mod"):
        floor_q = _floor_division(op, conv.get("quotient_semantics") or ["truncate_zero"])
        if b == 0:
            fl.add("div_zero")
            if div_zero == "zero":
                return 0, w, fl
            if op in ("div", "quot"):
                return _mask(w), w, fl            # all ones (all nines for BCD)
            return pa, w, fl
        if floor_q:
            q = a // b
        else:
            q = abs(a) // abs(b)
            q = -q if (a < 0) != (b < 0) else q
        if op in ("div", "quot"):
            fl |= _int_flags(op, fmt, pa, pb, q, None)
            return fmt.encode(fmt.wrap(q)), w, fl
        r = a - b * q
        if zero_sign == "preserve" and r == 0 and fmt.encoding in ("ones_complement", "sign_magnitude"):
            return _signed_zero(fmt, (pa >> (w - 1)) ^ (pb >> (w - 1))), w, fl
        return fmt.encode(r), w, fl
    if op == "mul_wide":
        of = (BCDFormat(2 * w) if isinstance(fmt, BCDFormat)
              else IntFormat(2 * w, fmt.encoding))
        r = int_ref(op, fmt, pa, pb, out_fmt=of)
        if zero_sign == "preserve" and a * b == 0 and fmt.encoding in ("ones_complement", "sign_magnitude"):
            r = _signed_zero(of, (pa >> (w - 1)) ^ (pb >> (w - 1)))
        return r, 2 * w, fl
    exact = ARITH_EXACT[op](a, b) if op in ARITH_EXACT else None
    if op in ("min", "max"):                   # the chosen operand's pattern, ties to a
        return (pa if (a <= b if op == "min" else a >= b) else pb), w, fl
    r = int_ref(op, fmt, pa, pb)
    fl |= _int_flags(op, fmt, pa, pb, exact, None)
    if fmt.encoding in ("ones_complement", "sign_magnitude") and zero_sign == "preserve":
        r = _preserve_zero(op, fmt, pa, pb, r, exact)
    return r, w, fl


def _floor_division(op, qs) -> bool:
    """Section 3.5: with truncate_zero alone every division op truncates;
    with floor alone every one floors; with both provisioned quot and rem
    truncate while div and mod floor (the opcode selects)."""
    qs = list(qs)
    if qs == ["floor"]:
        return True
    if len(qs) > 1:
        return op in ("div", "mod")
    return False


def _signed_zero(fmt, sign):
    if not sign:
        return 0
    return _mask(fmt.width) if fmt.encoding == "ones_complement" else 1 << (fmt.width - 1)


def _preserve_zero(op, fmt, pa, pb, r, exact):
    """zero_sign: preserve — the sign a zero result carries: the
    end-around-carry adder's pattern (ones' complement add/sub/adc/sbb),
    operand a's sign (sign-magnitude add/sub/adc/sbb), the complement of
    a (neg), the XOR of the signs (mul, mul_high, mul_sat, div, rem, mod)."""
    w = fmt.width
    sa, sb = pa >> (w - 1), pb >> (w - 1)
    if op in ("add", "sub", "adc", "sbb"):
        if exact != 0:
            return r
        if fmt.encoding == "ones_complement":
            m = _mask(w)
            s = {"add": pa + pb, "sub": pa + (~pb & m),
                 "adc": pa + pb + 1, "sbb": pa + (~pb & m) + (~1 & m)}[op]
            return _eac(w, s)
        return _signed_zero(fmt, sa)
    if op == "neg":
        if exact != 0:
            return r
        return _signed_zero(fmt, 1 - sa) if fmt.encoding == "sign_magnitude" \
            else (~pa) & _mask(w)
    if op in ("mul", "mul_high", "mul_sat") and exact == 0:
        return _signed_zero(fmt, sa ^ sb)
    return r


# --------------------------------------------------------------- fixed --

def fixed_op(op, fmt: FixedFormat, pa, pb, conv, ctrl, rounder, word=None):
    """Section 4.2: pattern ops share the integer semantics; mul, div and
    the conversions round the fraction under `rounding`."""
    w, F = fmt.width, fmt.frac_bits
    pint = _pattern_int(fmt)
    fl = set()
    if op in ("mul", "mul_sat"):
        a, b = pint.decode(pa), pint.decode(pb)
        q = Fraction(a * b, 1 << F)
        i = rounder.to_int(q, word)
        if i != q:
            fl.add("inexact")
        j = pint.saturate(i) if op == "mul_sat" else pint.wrap(i)
        if j != i:
            fl |= {"overflow", "inexact"}
        fl |= _int_flags("mul", pint, pa, pb, i, None) - {"overflow"} | (
            {"overflow"} if not (pint.min_int <= i <= pint.max_int) else set())
        return pint.encode(j), w, fl
    if op == "mul_wide":
        r, wo, fl = int_op("mul_wide", pint, pa, pb, conv, rounder, word)
        return r, wo, fl
    if op in ("div", "quot"):
        a, b = pint.decode(pa), pint.decode(pb)
        if b == 0:
            fl.add("div_zero")
            if conv.get("int_div_zero", "riscv") == "zero":
                return 0, w, fl
            return _mask(w), w, fl
        q = Fraction(a * (1 << F), b)
        i = rounder.to_int(q, word)
        if i != q:
            fl.add("inexact")
        j = pint.saturate(i)
        if j != i:
            fl |= {"overflow", "inexact"}
        return pint.encode(j), w, fl
    if op in ("rem", "mod"):
        return int_op(op, pint, pa, pb, conv, rounder, word)
    return int_op(op, pint, pa, pb, conv, rounder, word)


# ------------------------------------------------------------- floats --

def _read(fmt, bits, daz):
    """(value, zero-sign bit, denormal flag) of one float operand."""
    core, _ = float_core(fmt)
    v = fmt.decode(bits)
    s = _sign_of(fmt, bits)
    den = is_subnormal(fmt, bits)
    if daz and den:
        v = Fraction(0)
    return v, s, den


def _is_snan(fmt, bits) -> bool:
    """A signalling NaN pattern of a float format: a NaN whose quiet bit
    (the significand's top bit) is clear. IEEE 754 raises the invalid
    flag for a signalling NaN operand alone; a quiet NaN operand
    propagates without a flag. Posits, integers, formats without a NaN
    and formats whose NaN is one pattern (fp8e4m3) have no signalling
    NaN."""
    if isinstance(fmt, X87Format):
        core, bits = fmt.core, fmt._to_core(bits)
    elif isinstance(fmt, FloatFormat):
        core = fmt
    else:
        return False
    if not core.has_nan or core.man_bits == 0:
        return False
    _s, e, m = core._fields(bits & _mask(core.width))
    if e != core.emax_code or m == 0:
        return False
    if not core.has_inf:
        # a format without infinities (fp8e4m3) keeps finite values in its top exponent field: its one
        # NaN pattern is the all-ones significand, which is quiet, and every other pattern there is a number
        return False
    return not (m >> (core.man_bits - 1)) & 1


def _nan_result(fmt, conv, nan_operands, invalid_sign=0, invalid_op=True):
    """The pattern of a NaN result: canonical or the first NaN operand's
    pattern; formats without NaN apply invalid_result."""
    core, to_bits = float_core(fmt)
    fl = {"nan"} if core.has_nan else set()
    if core.has_nan:
        if conv.get("nan_payload", "canonical") == "propagate" and nan_operands:
            return nan_operands[0], fl
        return to_bits(core.encode_special(NAN)), fl
    fl |= {"inexact", "invalid"}
    if conv.get("invalid_result", "saturate") == "zero":
        return 0, fl
    return to_bits(((invalid_sign << (core.width - 1)) if core.signed else 0)
                   | core._max_finite_bits()), fl


def _exact_sqrt(x: Fraction):
    n, d = x.numerator, x.denominator
    r = isqrt(n * d)
    if r * r == n * d:
        return Fraction(r, d)
    return None


def _round_bounds(rounder, fmt, lo_hi_fn, word, zero_sign):
    """Round an irrational result from (lo, hi) bounds refined until the
    rounding is decided; the flags carry inexact."""
    prec = fmt.width + 32
    while True:
        lo, hi = lo_hi_fn(prec)
        b1, f1 = rounder.scalar(fmt, lo, word, zero_sign)
        b2, f2 = rounder.scalar(fmt, hi, word, zero_sign)
        if b1 == b2 and f1 == f2:
            return b1, f1 | {"inexact"}
        prec *= 2
        if prec > 1 << 16:
            raise ArithmeticError("rounding undecided")


def _fp2_signed(op, va, sa, vb, sb):
    """_fp2 with the sign of an infinite product or quotient taken from
    the operand sign bits (a zero operand's sign is not in its value)."""
    r = _fp2(op, va, vb)
    if op in ("fmul", "fdiv") and r in (PINF, NINF):
        return NINF if (sa ^ sb) else PINF
    return r


def _sum_special(prod, addend):
    """The exact sum of two values that may be infinite: the infinity, NAN
    for opposite infinities, else the rational sum."""
    inf_p, inf_c = prod in (PINF, NINF), addend in (PINF, NINF)
    if inf_p and inf_c:
        return prod if prod is addend else NAN
    if inf_p:
        return prod
    if inf_c:
        return addend
    return prod + addend


def fused_op(op, fmt, pa, pb, pc, conv, ctrl, rounder, word=None, contract="fused"):
    """Section 4.3's fused multiply-add ops on floats: d = (-1)^np * a * b +
    (-1)^nc * c, the exact product and sum rounded once (`contract`
    fused), or the product rounded to the format, read back as an operand
    (daz applies) and added under a second rounding (`sequential`, what a
    separate multiplier then adder and the cascade bridge compute).
    Invalid: a signalling NaN operand, inf * 0, and an infinite product
    against the opposite infinite addend; a NaN result carries the first
    NaN operand's payload in the order a, b, c under nan_payload
    propagate. The sign of an exact zero result follows IEEE 754 section
    6.3 for the sum of the (signed) product and the addend: the common
    sign when both are zero with one sign, else +0, or -0 under RDN."""
    core, to_bits = float_core(fmt)
    w = fmt.width
    daz = ctrl.get("daz_in", False)
    neg_p, neg_c = FUSED_OPS[op]
    va, sa, da = _read(fmt, pa, daz)
    vb, sb, db = _read(fmt, pb, daz)
    vc, sc, dc = _read(fmt, pc, daz)
    fl = {"denormal"} if (da or db or dc) else set()
    nan_ops = [p for p, v in ((pa, va), (pb, vb), (pc, vc)) if v is NAN]
    if nan_ops:
        if any(_is_snan(fmt, p) for p in nan_ops):
            fl.add("invalid")
        b, f2 = _nan_result(fmt, conv, nan_ops)
        return b, w, fl | f2
    ps = sa ^ sb ^ neg_p                     # the product's sign bit, a zero product's included
    cs = sc ^ neg_c
    inf_a, inf_b, inf_c = va in (PINF, NINF), vb in (PINF, NINF), vc in (PINF, NINF)
    if (inf_a and vb == 0) or (inf_b and va == 0):
        fl.add("invalid")
        b, f2 = _nan_result(fmt, conv, [], invalid_sign=ps)
        return b, w, fl | f2
    if inf_a or inf_b:
        prod = NINF if ps else PINF
    else:
        prod = -va * vb if neg_p else va * vb
    addend = (NINF if cs else PINF) if inf_c else (-vc if neg_c else vc)
    zero_prod, zero_addend = prod == 0, addend == 0
    if contract == "sequential" and not isinstance(prod, Special):
        # the product rounded to the format (its zero keeps the product's sign), then read back as the adder's
        # operand: flush-to-zero and denormals-are-zero act on it as on any result and operand
        if not core.signed and prod < 0:
            fl.add("invalid")
            b, f2 = _nan_result(fmt, conv, [], invalid_sign=1)
            return b, w, fl | f2
        pbits, pf = rounder.float(fmt, prod, word, ps)
        fl |= pf
        prod, ps, _den = _read(fmt, pbits, daz)
        zero_prod = prod == 0
    r = _sum_special(prod, addend)
    if r is NAN:
        fl.add("invalid")
        b, f2 = _nan_result(fmt, conv, [], invalid_sign=0)
        return b, w, fl | f2
    zs = 0
    if not isinstance(r, Special) and r == 0:
        if zero_prod and zero_addend:
            zs = (ps & cs) if rounder.mode != "RDN" else (ps | cs)
        else:
            zs = 1 if rounder.mode == "RDN" else 0
    if not core.signed and ((r is NINF) or (not isinstance(r, Special) and r < 0)):
        fl.add("invalid")
        b, f2 = _nan_result(fmt, conv, [], invalid_sign=1)
        return b, w, fl | f2
    b, f2 = rounder.float(fmt, r, word, zs)
    return b, w, fl | f2


def float_op(op, fmt, pa, pb, conv, ctrl, rounder, word=None, pc=None, contract="fused"):
    """Section 4.3 on floats and custom floats; returns (bits, w, flags).
    `pc` is the third operand of a fused multiply-add op, `contract` its
    fma_contract."""
    if op in FUSED_OPS:
        return fused_op(op, fmt, pa, pb, pc, conv, ctrl, rounder, word, contract)
    core, to_bits = float_core(fmt)
    w = fmt.width
    daz = ctrl.get("daz_in", False)
    fl = set()
    top = 1 << (core.width - 1)
    if op in ("fabs", "fneg"):
        va = fmt.decode(pa)
        if va is NAN:
            if conv.get("nan_payload", "canonical") == "propagate":
                b = pa if op == "fabs" and not core.signed else (
                    pa & ~top if op == "fabs" else pa ^ top)
                return b & _mask(w), w, {"nan"}
            b, f2 = _nan_result(fmt, conv, [])
            return b, w, f2
        if not core.signed:
            return pa & _mask(w), w, fl
        cb = core.width
        if isinstance(fmt, X87Format):
            return ((pa & ~(1 << 79)) if op == "fabs" else pa ^ (1 << 79)) & _mask(80), w, fl
        return ((pa & ~top) if op == "fabs" else pa ^ top) & _mask(w), w, fl
    va, sa, da = _read(fmt, pa, daz)
    unary = op == "fsqrt"
    if unary:
        vb, sb, db = Fraction(0), 0, False
    else:
        vb, sb, db = _read(fmt, pb, daz)
    if da or (db and not unary):
        fl.add("denormal")
    nan_ops = [p for p, v in ((pa, va), (pb, vb)) if v is NAN and (p is pa or not unary)]
    snan = any(_is_snan(fmt, p) for p in nan_ops)     # IEEE 754: invalid for a signalling NaN alone
    if op == "fcmp":
        if nan_ops:
            return 0, w, fl | {"unordered"} | ({"invalid"} if snan else set())
        key = {PINF: Fraction(10) ** 9999, NINF: -Fraction(10) ** 9999}
        ka, kb = key.get(va, va), key.get(vb, vb)
        return ((4 if ka > kb else 0) | (2 if ka == kb else 0) | (1 if ka < kb else 0)), w, fl
    if op in ("fmin", "fmax"):
        if nan_ops:
            fl.add("unordered")
            if snan:
                fl.add("invalid")
            if conv.get("minmax_nan", "propagate") == "propagate" or len(nan_ops) == 2:
                b, f2 = _nan_result(fmt, conv, nan_ops, invalid_op=False)
                return b, w, fl | f2
            return (pb if va is NAN else pa) & _mask(w), w, fl
        key = {PINF: Fraction(10) ** 9999, NINF: -Fraction(10) ** 9999}
        ka, kb = key.get(va, va), key.get(vb, vb)
        if ka == kb:
            if ka == 0 and sa != sb:           # -0 is below +0
                pick_a = (sa == 1) if op == "fmin" else (sa == 0)
            else:
                pick_a = True
        else:
            pick_a = ka < kb if op == "fmin" else ka > kb
        return (pa if pick_a else pb) & _mask(w), w, fl
    # arithmetic: fadd fsub fmul fdiv fsqrt; a quiet NaN operand propagates without a flag
    if nan_ops:
        if snan:
            fl.add("invalid")
        b, f2 = _nan_result(fmt, conv, nan_ops)
        return b, w, fl | f2
    if op == "fsqrt":
        if va is PINF:
            b, f2 = rounder.float(fmt, PINF, word)
            return b, w, fl | f2
        if va is NINF or (not isinstance(va, Special) and va < 0):
            fl.add("invalid")
            b, f2 = _nan_result(fmt, conv, [], invalid_sign=1)
            return b, w, fl | f2
        if va == 0:
            return to_bits((sa << (core.width - 1)) if core.signed else 0), w, fl
        ex = _exact_sqrt(va)
        if ex is not None:
            b, f2 = rounder.float(fmt, ex, word, 0)
            return b, w, fl | f2
        b, f2 = _round_bounds(rounder, fmt, lambda p: _sqrt_frac(va, p), word, 0)
        return b, w, fl | f2
    r = _fp2_signed(op, va, sa, vb, sb)
    inf_a, inf_b = va in (PINF, NINF), vb in (PINF, NINF)
    if op == "fdiv" and not inf_a and not inf_b and vb == 0 and va != 0:
        fl.add("div_zero")
    if r is NAN:
        fl.add("invalid")
        sign = (sa ^ sb) if op in ("fmul", "fdiv") else 0
        if op == "fdiv" and va == 0 and vb == 0:
            sign = 0
        b, f2 = _nan_result(fmt, conv, [], invalid_sign=sign)
        return b, w, fl | f2
    # the sign of a zero result
    zs = 0
    if op in ("fmul", "fdiv"):
        zs = sa ^ sb
    elif op in ("fadd", "fsub"):
        sb_eff = sb ^ (op == "fsub")
        if va == 0 and vb == 0:
            zs = sa & sb_eff if rounder.mode != "RDN" else sa | sb_eff
        elif not isinstance(r, Special) and r == 0:
            zs = 1 if rounder.mode == "RDN" else 0
    if isinstance(r, Special) and r in (PINF, NINF) and not core.signed and r is NINF:
        fl.add("invalid")
        b, f2 = _nan_result(fmt, conv, [], invalid_sign=1)
        return b, w, fl | f2
    if not isinstance(r, Special) and r < 0 and not core.signed:
        fl.add("invalid")
        b, f2 = _nan_result(fmt, conv, [], invalid_sign=1)
        return b, w, fl | f2
    b, f2 = rounder.float(fmt, r, word, zs)
    return b, w, fl | f2


# --------------------------------------------------------------- posit --

def posit_op(op, fmt: PositFormat, pa, pb, conv, ctrl, rounder, word=None):
    w = fmt.width
    fl = set()
    va, vb = fmt.decode(pa), fmt.decode(pb)
    n = fmt.width
    if op in ("fabs", "fneg"):
        if va is NAR:
            return fmt._nar, w, {"nan"}
        r = abs(va) if op == "fabs" else -va
        return fmt.encode(r), w, fl
    unary = op == "fsqrt"
    if op == "fcmp":
        ia, ib = fmt.index(pa), fmt.index(pb)      # total order, NaR lowest
        return ((4 if ia > ib else 0) | (2 if ia == ib else 0) | (1 if ia < ib else 0)), w, fl
    if op in ("fmin", "fmax"):
        ia, ib = fmt.index(pa), fmt.index(pb)
        pick_a = ia <= ib if op == "fmin" else ia >= ib
        return (pa if pick_a else pb), w, fl
    if va is NAR or (vb is NAR and not unary):
        return fmt._nar, w, fl | {"invalid", "nan"}
    if op == "fsqrt":
        if va < 0:
            return fmt._nar, w, fl | {"invalid", "nan"}
        if va == 0:
            return 0, w, fl
        ex = _exact_sqrt(va)
        if ex is not None:
            b, f2 = rounder.posit(fmt, ex)
            return b, w, fl | f2
        b, f2 = _round_bounds(rounder, fmt, lambda p: _sqrt_frac(va, p), word, 0)
        return b, w, fl | f2
    if op == "fdiv" and vb == 0:
        return fmt._nar, w, fl | {"invalid", "nan"} | ({"div_zero"} if va != 0 else set())
    r = _fp2(op, va, vb)
    b, f2 = rounder.posit(fmt, r)
    return b, w, fl | f2


# --------------------------------------------------------------- block --

def _elem_specials(fmt: BlockFormat, bits):
    """Per-element (value, sign, subnormal) of one block."""
    elems, sb = fmt.split(bits)
    sc = fmt.scale.decode(sb)
    out = []
    for eb in elems:
        v = fmt.elem.decode(eb)
        s = (eb >> (fmt.elem.width - 1)) & 1 if getattr(fmt.elem, "signed", True) else 0
        den = is_subnormal(fmt.elem, eb) if isinstance(fmt.elem, FloatFormat) else False
        out.append((v if isinstance(v, Special) else v * sc, s, den, eb))
    return out


def block_op(op, fmt: BlockFormat, pa, pb, conv, ctrl, rounder, words):
    """Section 4.5: fp ops elementwise on the decoded elements, the
    result block re-quantized (fabs/fneg act on the element sign bits,
    fcmp gives per-element flags in the element slots). Returns (bits, w,
    [flags per element])."""
    w = fmt.width
    size = fmt.size
    elem = fmt.elem
    fl_elem = isinstance(elem, FloatFormat)
    daz = ctrl.get("daz_in", False)
    if op in ("fabs", "fneg"):
        elems, sb = fmt.split(pa)
        out, fls = [], []
        for eb in elems:
            v = elem.decode(eb)
            if fl_elem and v is NAN:
                out.append(eb if conv.get("nan_payload") == "propagate"
                           else elem.encode_special(NAN))
                fls.append({"nan"})
                continue
            if fl_elem and elem.signed:
                top = 1 << (elem.width - 1)
                out.append((eb & ~top) if op == "fabs" else eb ^ top)
            elif fl_elem:
                out.append(eb)
            else:
                out.append(elem.encode(elem.wrap(abs(v) if op == "fabs" else -v)))
            fls.append(set())
        return fmt.join(out, sb), w, fls
    ea = _elem_specials(fmt, pa)
    eb_ = _elem_specials(fmt, pb) if op != "fsqrt" else [(Fraction(0), 0, False, 0)] * size
    if op == "fcmp":
        out, fls = [], []
        for (va, _sa, _da, ba), (vb, _sb, _db, bb) in zip(ea, eb_):
            if NAN in (va, vb):
                out.append(0)
                fls.append({"unordered"} | ({"invalid"} if _is_snan(elem, ba) or _is_snan(elem, bb) else set()))
                continue
            key = {PINF: Fraction(10) ** 9999, NINF: -Fraction(10) ** 9999}
            ka, kb = key.get(va, va), key.get(vb, vb)
            out.append((4 if ka > kb else 0) | (2 if ka == kb else 0) | (1 if ka < kb else 0))
            fls.append(set())
        return fmt.join(out, 0), w, fls
    values, fls, signs = [], [], []
    for j, ((va, sa, da, ba), (vb, sb, db, bb)) in enumerate(zip(ea, eb_)):
        f = set()
        if op in ("fmul", "fdiv"):
            signs.append(sa ^ sb)
        elif op == "fsqrt":
            signs.append(sa)
        else:
            sb_eff = sb ^ (op == "fsub")
            both_zero = (not isinstance(va, Special) and not isinstance(vb, Special)
                         and va == 0 and vb == 0)
            signs.append((sa & sb_eff if rounder.mode != "RDN" else sa | sb_eff) if both_zero
                         else (1 if rounder.mode == "RDN" else 0))
        if da or (db and op != "fsqrt"):
            f.add("denormal")
        if daz:
            va = Fraction(0) if da else va
            vb = Fraction(0) if db else vb
        snan = _is_snan(elem, ba) or (op != "fsqrt" and _is_snan(elem, bb))
        if op in ("fmin", "fmax"):
            if NAN in (va, vb):
                f.add("unordered")
                if snan:
                    f.add("invalid")
                if conv.get("minmax_nan", "propagate") == "propagate" or (va is NAN and vb is NAN):
                    values.append(NAN)
                else:
                    values.append(vb if va is NAN else va)
            else:
                key = {PINF: Fraction(10) ** 9999, NINF: -Fraction(10) ** 9999}
                ka, kb = key.get(va, va), key.get(vb, vb)
                pick_a = ka <= kb if op == "fmin" else ka >= kb
                values.append(va if pick_a else vb)
                signs[-1] = sa if pick_a else sb
            fls.append(f)
            continue
        if NAN in (va, vb) and not (op == "fsqrt" and vb is NAN):
            if snan:
                f.add("invalid")
            values.append(NAN)
            fls.append(f)
            continue
        if op == "fsqrt":
            if va is PINF:
                values.append(PINF)
            elif va is NINF or va < 0:
                f.add("invalid")
                values.append(NAN)
            elif va == 0:
                values.append(Fraction(0))
            else:
                ex = _exact_sqrt(va)
                values.append(ex if ex is not None else ("sqrt", va))
                if ex is None:
                    f.add("inexact")
            fls.append(f)
            continue
        r = _fp2_signed(op, va, sa, vb, sb)
        if op == "fdiv" and not isinstance(va, Special) and not isinstance(vb, Special) \
                and vb == 0 and va != 0:
            f.add("div_zero")
        if r is NAN:
            f.add("invalid")
        values.append(r)
        fls.append(f)
    # irrational elements (sqrt): refine until the quantized block is stable
    def quant(prec):
        vals = []
        for v in values:
            if isinstance(v, tuple):
                lo, hi = _sqrt_frac(v[1], prec)
                vals.append((lo, hi))
            else:
                vals.append((v, v))
        lo_vals = [x[0] for x in vals]
        hi_vals = [x[1] for x in vals]
        b1, e1 = rounder.block(fmt, lo_vals, words, conv, signs)
        b2, e2 = rounder.block(fmt, hi_vals, words, conv, signs)
        return (b1, e1) if (b1 == b2 and e1 == e2) else None
    prec = fmt.width + 32
    while True:
        q = quant(prec)
        if q is not None:
            break
        prec *= 2
        if prec > 1 << 16:
            raise ArithmeticError("block rounding undecided")
    bits, eflags = q
    return bits, w, [a | b for a, b in zip(fls, eflags)]


# ------------------------------------------------------------ convert --

def _to_scalar(rounder, tgt, v, word, conv, sign=0, nan_operand=None, snan=False):
    """One value into a scalar target format; returns (bits, flags).
    `snan`: the source is a signalling NaN (invalid under IEEE 754; a
    quiet NaN converts to the target's NaN without a flag)."""
    fl = set()
    if isinstance(tgt, (FloatFormat, X87Format)):
        core, _ = float_core(tgt)
        if v is NAN or v is NAR:
            if snan or v is NAR:
                fl.add("invalid")
            if core.has_nan:
                b, f2 = _nan_result(tgt, conv, [nan_operand] if nan_operand is not None
                                    and getattr(nan_operand, "bit_length", None) else [])
                return b, fl | f2
            b, f2 = _nan_result(tgt, conv, [], invalid_sign=sign)
            return b, fl | f2
        if v is NINF and not core.signed:
            fl.add("invalid")
            b, f2 = _nan_result(tgt, conv, [], invalid_sign=1)
            return b, fl | f2
        if not isinstance(v, Special) and v < 0 and not core.signed:
            fl.add("invalid")
            b, f2 = _nan_result(tgt, conv, [], invalid_sign=1)
            return b, fl | f2
        b, f2 = rounder.float(tgt, v, word, sign)
        return b, fl | f2
    if isinstance(tgt, PositFormat):
        if isinstance(v, Special):
            return tgt._nar, {"invalid", "nan"}
        return rounder.posit(tgt, v)
    # integer or fixed target
    if isinstance(v, Special):
        fl.add("invalid")
        if v is NAN or v is NAR:
            pick = conv.get("nan_to_int", "zero")
            val = {"zero": 0, "max": tgt.max_int, "min": tgt.min_int}[pick]
        else:
            val = tgt.max_int if v is PINF else tgt.min_int
        return IntFormat.encode(tgt, val) if isinstance(tgt, ScaledIntFormat) \
            else tgt.encode(val), fl
    b, f2 = rounder.scalar(tgt, v, word, sign, saturate=True)
    if "overflow" in f2:
        f2.add("invalid")
    return b, fl | f2


def _decode_scalar(fmt, bits, daz):
    """(value, sign bit, denormal) of one scalar operand of any family."""
    if isinstance(fmt, (FloatFormat, X87Format)):
        return _read(fmt, bits, daz)
    if isinstance(fmt, PositFormat):
        v = fmt.decode(bits)
        return v, (1 if (not isinstance(v, Special) and v < 0) else 0), False
    v = fmt.decode(bits)
    return v, (1 if v < 0 else 0), False


def cvt_op(fmt, tgt, values_bits, conv, ctrl, rounder, words, base):
    """cvt(<target>) over the values of one operand (list of patterns of
    `fmt`). Returns (list of result patterns, result width, list of
    flag sets); scalar to block groups `size` values per block, block
    to scalar expands `size` results per block. `base` is the index of
    the first result (for the SR words)."""
    daz = ctrl.get("daz_in", False)
    src_block = isinstance(fmt, BlockFormat)
    tgt_block = isinstance(tgt, BlockFormat)
    outs, fls = [], []
    if not src_block and not tgt_block:
        for i, pb_ in enumerate(values_bits):
            v, s, den = _decode_scalar(fmt, pb_, daz)
            b, f = _to_scalar(rounder, tgt, v, words[base + i] if words else 0,
                              conv, s, pb_, snan=_is_snan(fmt, pb_))
            if den:
                f.add("denormal")
            outs.append(b)
            fls.append(f)
        return outs, tgt.width, fls
    if src_block and not tgt_block:
        k = 0
        for pb_ in values_bits:
            for v, s, den, _eb in _elem_specials(fmt, pb_):
                if daz and den:
                    v = Fraction(0)
                b, f = _to_scalar(rounder, tgt, v, words[base + k] if words else 0,
                                  conv, s, snan=_is_snan(fmt.elem, _eb))
                if den:
                    f.add("denormal")
                outs.append(b)
                fls.append(f)
                k += 1
        return outs, tgt.width, fls
    # target is a block
    size = tgt.size
    vals = []
    for pb_ in values_bits:
        if src_block:
            for v, s, den, _eb in _elem_specials(fmt, pb_):
                vals.append((Fraction(0) if (daz and den) else v, den, s))
        else:
            v, s, den = _decode_scalar(fmt, pb_, daz)
            vals.append((v, den, s))
    assert len(vals) % size == 0, (fmt.name, tgt.name, len(vals))
    for g in range(len(vals) // size):
        chunk = vals[g * size:(g + 1) * size]
        w_ = words[base + g * size: base + (g + 1) * size] if words else None
        b, ef = rounder.block(tgt, [c[0] for c in chunk], w_, conv, [c[2] for c in chunk])
        for (v, den, _s), f in zip(chunk, ef):
            if den:
                f.add("denormal")
        outs.append(b)
        fls.append(set().union(*ef) if ef else set())
        fls[-1] = ef                     # per element for the flag words
    return outs, tgt.width, fls


# ------------------------------------------------------------- vector --

def n_results(fmt, count, op):
    """Rounded results of one operand set in (count x fmt) under op: the
    V_max term without the dual factor."""
    tgt = cvt_target(op)
    if tgt is not None and isinstance(tgt, BlockFormat):
        if isinstance(fmt, BlockFormat):
            return count * fmt.size
        return count
    if isinstance(fmt, BlockFormat):
        return count * fmt.size
    return count


def alu_expected(modes, mi, op, pairs, ctrl, conv, options, words, layout):
    """Expected (y, d, flags) of one vector.

    modes: [(count, fmt)]; mi: the mode index; pairs: [(a_bits, b_bits)]
    per value; ctrl: the runtime option values of this vector (rounding,
    daz_in, ftz_out, unary_dual, quotient_semantics); conv: the
    convention options; options: {sr_bits, flags (list), tininess};
    words: the sr_rnd words (V_max) or None; layout: {y_w, in_w, d_w,
    dual_in_y}."""
    count, fmt = modes[mi]
    fam = family_of(fmt)
    rounder = Rounder(ctrl.get("rounding", "RNE"), options.get("sr_bits", 1),
                      conv.get("sr_compare", "gt"), conv.get("tininess", "after"),
                      ftz=bool(ctrl.get("ftz_out", False)))
    if fam == "posit":
        rounder.ftz = False
    flag_names = list(options.get("flags") or ())
    dual = bool(ctrl.get("unary_dual", False)) and op in UNARY \
        or (bool(ctrl.get("unary_dual", False)) and is_cvt(op))
    n_first = n_results(fmt, count, op)
    tgt = cvt_target(op)
    results = []            # (bits, w_out) per value, first set then dual set
    flags = []              # flag sets per result index

    def run(values_bits, base):
        outs, fls = [], []
        if tgt is not None:
            o, w_out, f = cvt_op(fmt, tgt, values_bits, conv, ctrl, rounder, words, base)
            for b, fset in zip(o, f):
                outs.append((b, w_out))
                if isinstance(fset, list):
                    fls.extend(fset)
                else:
                    fls.append(fset)
            return outs, fls
        for i, operands in enumerate(values_bits):
            # (a, b) of a binary op, (a, b, c) of a fused multiply-add
            pa, pb = operands[0], operands[1]
            pc = operands[2] if len(operands) > 2 else None
            k = base + i * (fmt.size if fam == "block" else 1)
            word = (words[k] if words else 0)
            if fam == "integer":
                b, w_out, f = int_op(op, fmt, pa, pb, conv, rounder, word)
                fls.append(f)
            elif fam == "fixed":
                b, w_out, f = fixed_op(op, fmt, pa, pb, conv, ctrl, rounder, word)
                fls.append(f)
            elif fam == "float":
                from .reference_underflow import lane_tininess
                rounder.tininess = lane_tininess(conv, fmt.name, i, op, rounder.mode)
                b, w_out, f = float_op(op, fmt, pa, pb, conv, ctrl, rounder, word, pc=pc,
                                       contract=conv.get("fma_contract", "fused"))
                fls.append(f)
            elif fam == "posit":
                b, w_out, f = posit_op(op, fmt, pa, pb, conv, ctrl, rounder, word)
                fls.append(f)
            else:
                ws = words[k:k + fmt.size] if words else None
                b, w_out, f = block_op(op, fmt, pa, pb, conv, ctrl, rounder, ws)
                fls.extend(f)
            outs.append((b, w_out))
        return outs, fls

    if tgt is not None:
        first, f1 = run([operands[0] for operands in pairs], 0)
    else:
        first, f1 = run(pairs, 0)
    results.append(first)
    flags.extend(f1)
    if dual:
        if tgt is not None:
            second, f2 = run([operands[1] for operands in pairs], n_first)
        else:
            second, f2 = run([(operands[1], operands[0]) for operands in pairs], n_first)
        results.append(second)
        flags.extend(f2)
    y = 0
    d = 0
    for i, (b, w_out) in enumerate(first):
        y |= (b & _mask(w_out)) << (i * w_out)
    if dual:
        for i, (b, w_out) in enumerate(results[1]):
            if layout["dual_in_y"]:
                y |= (b & _mask(w_out)) << (layout["y_w"] // 2 + i * w_out)
            else:
                d |= (b & _mask(w_out)) << (i * w_out)
    fw = 0
    if flag_names:
        nf = len(flag_names)
        if conv.get("flag_scope", "per_result") == "per_operation":
            fw = flag_word(set().union(*flags) if flags else set(), flag_names)
        else:
            for k, fset in enumerate(flags):
                fw |= flag_word(fset, flag_names) << (k * nf)
    return y & _mask(layout["y_w"]), d & _mask(max(layout.get("d_w", 0), 1)), fw


# ------------------------------------------------- legality and layout --

OP_CLASSES = {
    "arith":  ("add", "sub", "adc", "sbb", "neg", "abs",
               "add_sat", "sub_sat"),
    "mul":    ("mul", "mul_wide", "mul_high", "mul_sat"),
    "div":    ("div", "quot", "rem", "mod"),
    "select": ("min", "max", "cmp"),
    "shift":  ("shl", "shr_logical", "shr_arith", "rol", "ror"),
    "logic":  ("and", "or", "xor", "not", "popcount", "clz", "ctz"),
    "fp":     ("fadd", "fsub", "fmul", "fdiv", "fsqrt", "fcmp", "fmin",
               "fmax", "fabs", "fneg", "fmadd", "fmsub", "fnmsub", "fnmadd"),
}
OPS = tuple(op for ops in OP_CLASSES.values() for op in ops)
RUNTIME_OPTIONS = ("rounding", "daz_in", "ftz_out", "unary_dual", "accuracy_mode")


def accuracy_budgets(spec: dict) -> list:
    """The budget of each accuracy mode, in mode order: the list a
    runtime-controlled core binds, and the run's single budget repeated
    for a core whose operating point is static."""
    modes = list(spec.get("accuracy_mode") or [0])
    b = spec.get("budget")
    if isinstance(b, (list, tuple)):
        return [dict(x or {}) for x in b][:len(modes)] + [{}] * max(0, len(modes) - len(b))
    one = dict(b or {}) if b else ({} if spec.get("accuracy", "exact") == "approximate"
                                   else {"bit_exact": True})
    return [one for _ in modes]


def checked_modes(spec: dict) -> tuple:
    """The accuracy modes the generated checker checks: the modes whose
    budget is the exact result. A disagreement means a fault in those
    modes alone, since an approximate mode has no unique correct output
    (docs/formats-and-options.md section 3.4)."""
    return tuple(i for i, b in enumerate(accuracy_budgets(spec)) if b.get("bit_exact") is True)


def is_unary(op) -> bool:
    return op in UNARY or is_cvt(op)


def op_class(op: str) -> str:
    if is_cvt(op):
        return "convert"
    for cls, members in OP_CLASSES.items():
        if op in members:
            return cls
    raise ValueError(f"unknown op {op!r}")


def op_legal(op: str, fmt) -> bool:
    """Section 4: which ops a format family takes (BCD excludes the
    pattern ops; fixed point excludes mul_high)."""
    cls = op_class(op)
    fam = family_of(fmt)
    if cls == "convert":
        tgt = cvt_target(op)
        if isinstance(tgt, BlockFormat) and isinstance(fmt, BlockFormat):
            return True
        return True
    if fam == "integer":
        if isinstance(fmt, BCDFormat):
            return cls in ("arith", "mul", "div", "select")
        return cls in ("arith", "mul", "div", "select", "shift", "logic")
    if fam == "fixed":
        if cls == "mul":
            return op != "mul_high"
        return cls in ("arith", "div", "select", "shift", "logic")
    if op in FUSED_OPS:
        # the fused multiply-add reads a third operand through the float datapath's fp_fma structure; the posit
        # unit, the block modes and the x87 extended format have no three-operand path
        return fam == "float" and not isinstance(fmt, X87Format)
    return cls == "fp"


def cvt_count_ok(op, fmt, count) -> bool:
    """A conversion to a block target needs count values per block."""
    tgt = cvt_target(op)
    if tgt is None or not isinstance(tgt, BlockFormat) or isinstance(fmt, BlockFormat):
        return True
    return count % tgt.size == 0


def result_width(op: str, fmt, count: int) -> int:
    """Bits of y one (mode, op) pair uses (the first result set)."""
    w = fmt.width
    if op == "mul_wide":
        return count * 2 * w
    tgt = cvt_target(op)
    if tgt is not None:
        if isinstance(fmt, BlockFormat) and not isinstance(tgt, BlockFormat):
            return count * fmt.size * tgt.width
        if isinstance(tgt, BlockFormat) and not isinstance(fmt, BlockFormat):
            return (count // tgt.size) * tgt.width
        return count * tgt.width
    return count * w


def legal_pairs(modes, ops, mode_ops=None):
    return {(i, op) for i, (n, f) in enumerate(modes) for op in ops
            if (mode_ops is None or mode_ops[i] is None or op in mode_ops[i])
            and op_legal(op, f) and cvt_count_ok(op, f, n)}


def flags_width(v_max: int, flags, flag_scope: str) -> int:
    """The width of the `flags` output: one word of len(flags) bits per
    result under `flag_scope: per_result`, and one word for the whole
    operation under `per_operation`."""
    return len(flags) if flag_scope == "per_operation" else v_max * len(flags)


def alu_layout(spec: dict) -> dict:
    """Ports and packing of a chialu.ALU spec (the single source for the
    template, the harness, the seed and the checker):
      core_in, core_out: the core's ports as (name, width) in order
      chk_extra: inputs only the checker has (check_sr_sel)
      y_w, in_w, d_w, dual_in_y, v_max, legal, modes."""
    from chialu.verify.ports import Port
    from chialu.verify.formats import parse_format
    modes = [(int(m["count"]), parse_format(str(m["format"]))) for m in spec["modes"]]
    ops = list(spec["ops"])
    legal = legal_pairs(modes, ops, [mode.get("ops") for mode in spec["modes"]])
    dual_possible = True in spec.get("unary_dual", [False])
    in_w = max(n * f.width for n, f in modes)
    y_w = max(result_width(op, modes[i][1], modes[i][0]) for i, op in legal)
    unary_w = [result_width(op, modes[i][1], modes[i][0]) for i, op in legal
               if is_unary(op)]
    u_w = max(unary_w) if unary_w else 0
    dual_in_y = dual_possible and bool(unary_w) and y_w >= 2 * u_w
    d_w = u_w if (dual_possible and unary_w and not dual_in_y) else 0
    v_max = max(n_results(modes[i][1], modes[i][0], op)
                * (2 if dual_possible and is_unary(op) else 1)
                for i, op in legal)
    sr = "SR" in spec.get("rounding", ["RNE"])
    sr_bits = int(spec.get("sr_bits") or 1)
    flags = list(spec.get("flags") or ())
    flag_scope = str(spec.get("flag_scope", "per_result"))
    core_in = [Port("a", "in", in_w), Port("b", "in", in_w)]
    if any(op in FUSED_OPS for op in ops):
        core_in.append(Port("c", "in", in_w))        # the fused multiply-add's third operand
    if len(ops) > 1:
        core_in.append(Port("op", "in", max(1, (len(ops) - 1).bit_length())))
    if len(modes) > 1:
        core_in.append(Port("mode", "in", max(1, (len(modes) - 1).bit_length())))
    if sr:
        core_in.append(Port("sr_rnd", "in", v_max * sr_bits))
    controls = {}
    for name in RUNTIME_OPTIONS:
        vals = list(spec.get(name) or [])
        if len(vals) > 1:
            core_in.append(Port(f"{name}_sel", "in", max(1, (len(vals) - 1).bit_length())))
            controls[name] = vals
    chk_extra = []
    if len(spec.get("check_sr") or []) > 1:
        chk_extra.append(Port("check_sr_sel", "in", 1))
    core_out = [Port("y", "out", y_w)]
    if d_w:
        core_out.append(Port("d", "out", d_w))
    if flags:
        core_out.append(Port("flags", "out", flags_width(v_max, flags, flag_scope)))
    return {"modes": modes, "ops": ops, "legal": legal, "core_in": core_in,
            "core_out": core_out, "chk_extra": chk_extra, "y_w": y_w,
            "in_w": in_w, "d_w": d_w, "dual_in_y": dual_in_y, "v_max": v_max,
            "sr": sr, "sr_bits": sr_bits, "controls": controls, "flags": flags,
            "flag_scope": flag_scope}


CONVENTION_NAMES = ("nan_payload", "invalid_result", "nan_to_int", "minmax_nan",
                    "tininess", "int_div_zero", "zero_sign", "quire_overflow",
                    "block_scale_rounding", "block_element_overflow",
                    "sr_compare", "check_flags", "flag_scope", "fma_contract", "underflow_contract")


def conventions_of(spec: dict) -> dict:
    return {k: spec[k] for k in CONVENTION_NAMES if k in spec}


def vector_ctrl(spec: dict, meta_ctrl: dict) -> dict:
    """The option values of one vector: the ETC value of every runtime
    option, overridden by the vector's selections."""
    ctrl = {}
    for name in RUNTIME_OPTIONS + ("quotient_semantics",):
        vals = list(spec.get(name) or [])
        if vals:
            ctrl[name] = vals[0]
    ctrl.update(meta_ctrl or {})
    return ctrl


SPEC_DEFAULTS = {"rounding": ["RNE"], "daz_in": [False], "ftz_out": [False],
                 "unary_dual": [False], "check_sr": [True], "flags": [],
                 "nan_payload": "canonical", "invalid_result": "saturate",
                 "nan_to_int": "zero", "minmax_nan": "propagate",
                 "tininess": "after", "int_div_zero": "riscv",
                 "zero_sign": "positive", "quire_overflow": "wrap",
                 "block_scale_rounding": "nearest",
                 "block_element_overflow": "saturate", "sr_compare": "gt",
                 "check_flags": False, "flag_scope": "per_result", "x_form": "exact",
                 "fma_contract": "fused"}


def default_sr_bits(modes) -> int:
    """The largest mantissa (F for fixed point, the element's for blocks)
    among the modes, at least 1."""
    best = 1
    for _n, f in modes:
        g = f.elem if isinstance(f, BlockFormat) else f
        if isinstance(g, X87Format):
            best = max(best, 63)
        best = max(best, getattr(g, "man_bits", 0), getattr(g, "frac_bits", 0))
    return best


def normalize_spec(spec: dict) -> dict:
    """A spec with every option present as the reference reads it: the
    runtime options as lists, the conventions at their defaults."""
    from chialu.verify.formats import parse_format
    out = dict(spec)
    for k, v in SPEC_DEFAULTS.items():
        out.setdefault(k, list(v) if isinstance(v, list) else v)
    for k in ("rounding", "daz_in", "ftz_out", "unary_dual", "check_sr"):
        if not isinstance(out[k], (list, tuple)):
            out[k] = [out[k]]
        out[k] = list(out[k])
    if "quotient_semantics" in out and not isinstance(out["quotient_semantics"], (list, tuple)):
        out["quotient_semantics"] = [out["quotient_semantics"]]
    if out.get("accuracy_ctl") == "runtime" and not out.get("accuracy_mode"):
        out["accuracy_mode"] = list(range(int(out.get("accuracy_modes") or 2)))
    if out.get("accuracy_mode") is not None:
        out["accuracy_mode"] = [int(m) for m in out["accuracy_mode"]]
    modes = [(int(m["count"]), parse_format(str(m["format"]))) for m in out["modes"]]
    for index, (mode, (count, fmt)) in enumerate(zip(out["modes"], modes)):
        if "ops" not in mode:
            continue
        selected = mode["ops"]
        if not isinstance(selected, (list, tuple)) or not selected or not all(isinstance(op, str) for op in selected):
            raise ValueError(f"mode {index}.ops must be a nonempty list of operation names")
        unknown = set(selected) - set(out["ops"])
        if unknown:
            raise ValueError(f"mode {index}.ops contains operations absent from the global opcode list: {sorted(unknown)}")
        illegal = [op for op in selected if not op_legal(op, fmt) or not cvt_count_ok(op, fmt, count)]
        if illegal:
            raise ValueError(f"mode {index}.ops contains operations incompatible with its format or count: {illegal}")
    if not out.get("sr_bits"):
        out["sr_bits"] = default_sr_bits(modes)
    return out
