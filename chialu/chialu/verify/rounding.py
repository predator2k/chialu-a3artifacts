"""Rounding with the unit options (docs/formats-and-options.md sections
3.1, 3.2, 3.8, 3.9): the four IEEE modes, stochastic rounding from a
random word, daz_in / ftz_out, the flags a rounding raises, and the
block quantizer of section 2.6. Everything computes on exact rationals.

PRBS31 is the verification-side random source of `sr_rnd` (x^31 + x^28
+ 1, ITU-T O.150); the words it produces are part of the vector plan.
"""
from __future__ import annotations

from fractions import Fraction
from math import floor

from chialu.verify.formats import (NAN, NAR, NINF, PINF, BlockFormat,
                                    FloatFormat, IntFormat, PositFormat,
                                    ScaledIntFormat, Special, X87Format,
                                    _mask, _round_int)

ROUNDINGS = ("RNE", "RTZ", "RDN", "RUP", "SR")


class PRBS31:
    """Fibonacci LFSR x^31 + x^28 + 1; `word(n)` returns n output bits,
    first bit most significant."""

    def __init__(self, seed: int):
        self.state = (int(seed) & 0x7FFFFFFF) or 1

    def bit(self) -> int:
        s = self.state
        fb = ((s >> 30) ^ (s >> 27)) & 1
        self.state = ((s << 1) | fb) & 0x7FFFFFFF
        return fb

    def word(self, n: int) -> int:
        w = 0
        for _ in range(n):
            w = (w << 1) | self.bit()
        return w


def is_subnormal(fmt, bits) -> bool:
    """A nonzero pattern with a zero exponent field (floats only)."""
    if isinstance(fmt, X87Format):
        fmt, bits = fmt.core, fmt._to_core(bits)
    if not isinstance(fmt, FloatFormat) or fmt.exp_only:
        return False
    _s, e, m = fmt._fields(bits & _mask(fmt.width))
    return e == 0 and m != 0


def float_core(fmt):
    """(core FloatFormat, to_bits) so fp80 rounds through its core."""
    if isinstance(fmt, X87Format):
        return fmt.core, fmt._from_core
    return fmt, (lambda b: b)


def round_int_sr(q: Fraction, word: int, sr_bits: int, compare: str) -> int:
    """Stochastic rounding of q to an integer: away from zero when the
    first sr_bits bits of the fraction exceed (or equal, `ge`) the word."""
    if q.denominator == 1:
        return int(q)
    mag = abs(q)
    lo = floor(mag)
    f_int = floor((mag - lo) * (1 << sr_bits))
    up = f_int > word if compare == "gt" else f_int >= word
    m = lo + 1 if up else lo
    return m if q > 0 else -m


class Rounder:
    """The rounding of one unit: mode (RNE/RTZ/RDN/RUP/SR), the SR
    parameters, the tininess convention and ftz. Every method returns
    (bits, flags) with flags a set of section 3.8 names."""

    def __init__(self, mode="RNE", sr_bits=1, sr_compare="gt",
                 tininess="after", ftz=False):
        assert mode in ROUNDINGS, mode
        self.mode = mode
        self.sr_bits = sr_bits
        self.sr_compare = sr_compare
        self.tininess = tininess
        self.ftz = ftz

    # -- integers ---------------------------------------------------------
    def to_int(self, q: Fraction, word: int | None = None) -> int:
        if self.mode == "SR":
            return round_int_sr(q, word or 0, self.sr_bits, self.sr_compare)
        return _round_int(q, self.mode)

    # -- floats -----------------------------------------------------------
    def _float_bits(self, core: FloatFormat, v: Fraction, word) -> int:
        """Bits of v in `core` (no ftz), directed or stochastic."""
        if self.mode != "SR":
            return core.round(v, self.mode)
        t = core.round(v, "RTZ")
        tv = core.decode(t)
        if isinstance(tv, Special) or tv == v:
            return t
        up = core.round(v, "RUP" if v > 0 else "RDN")
        uv = core.decode(up)
        if up == t:
            return t                              # saturated: no neighbor
        ulp = (abs(uv) - abs(tv)) if not isinstance(uv, Special) else core.ulp_at(t)
        f = (abs(v) - abs(tv)) / ulp
        f_int = floor(f * (1 << self.sr_bits))
        go = f_int > (word or 0) if self.sr_compare == "gt" else f_int >= (word or 0)
        return up if go else t

    def float(self, fmt, v, word=None, zero_sign=0):
        """v is a Fraction or a Special; zero_sign is the sign bit a zero
        result carries. Flags: inexact, overflow, underflow (per the
        tininess convention), nan."""
        core, to_bits = float_core(fmt)
        flags = set()
        if isinstance(v, Special):
            if v is NAN or v is NAR:
                flags.add("nan")
                if not core.has_nan:
                    raise ValueError(f"{fmt.name}: NaN result in a format "
                                     f"without NaN (invalid_result decides)")
                return to_bits(core.encode_special(NAN)), flags
            if v is NINF and not core.signed:
                v = PINF
            if not core.has_inf:
                flags |= {"inexact", "overflow"}
            return to_bits(core.encode_special(v)), flags
        if v == 0:
            b = (zero_sign << (core.width - 1)) if core.signed and not core.exp_only else 0
            if core.exp_only:
                flags.add("inexact")
            return to_bits(b), flags
        if v < 0 and not core.signed:
            raise ValueError(f"{fmt.name}: negative result {v} in an "
                             f"unsigned format")
        bits = self._float_bits(core, v, word)
        r = core.decode(bits)
        inexact = isinstance(r, Special) or r != v
        if inexact:
            flags.add("inexact")
        if not core.exp_only:
            wide = FloatFormat("wide", core.exp_bits + 8, core.man_bits,
                               True, True, core.signed)
            ru = wide.decode(self._float_bits(wide, v, word))
            if not isinstance(ru, Special) and abs(ru) > core.max_finite():
                flags.add("overflow")
            min_normal = Fraction(2) ** (1 - core.bias)
            tiny = abs(v) < min_normal if self.tininess == "before" \
                else (not isinstance(ru, Special) and abs(ru) < min_normal)
            if tiny and inexact:
                flags.add("underflow")
            if self.ftz and is_subnormal(core, bits):
                bits = bits & (1 << (core.width - 1)) if core.signed else 0
                flags |= {"inexact", "underflow"}
        elif isinstance(r, Special) or (abs(r) != abs(v) and abs(r) == core.max_finite()):
            flags.add("overflow")
        return to_bits(bits), flags

    # -- posits -----------------------------------------------------------
    def posit(self, fmt: PositFormat, v):
        flags = set()
        if isinstance(v, Special):
            flags.add("nan")
            return fmt._nar, flags
        bits = fmt.round(v, self.mode)
        r = fmt.decode(bits)
        if r != v:
            flags.add("inexact")
            maxpos = fmt.decode((1 << (fmt.width - 1)) - 1)
            minpos = fmt.decode(1)
            if abs(v) > maxpos:
                flags.add("overflow")
            elif abs(v) < minpos:
                flags.add("underflow")
        return bits, flags

    # -- any scalar format ------------------------------------------------
    def scalar(self, fmt, v, word=None, zero_sign=0, saturate=True):
        """Round v into a scalar format: floats and posits as above,
        integer and fixed formats rounded to their grid then saturated
        (saturate=True) or wrapped. Specials into an integer format are
        the caller's business (nan_to_int)."""
        if isinstance(fmt, (FloatFormat, X87Format)):
            return self.float(fmt, v, word, zero_sign)
        if isinstance(fmt, PositFormat):
            return self.posit(fmt, v)
        flags = set()
        ulp = fmt._scale if isinstance(fmt, ScaledIntFormat) else Fraction(1)
        q = Fraction(v) / ulp
        i = self.to_int(q, word)
        if i != q:
            flags.add("inexact")
        if saturate:
            j = fmt.saturate(i)
        else:
            j = fmt.wrap(i)
        if j != i:
            flags |= {"overflow", "inexact"}
        return IntFormat.encode(fmt, j) if isinstance(fmt, ScaledIntFormat) \
            else fmt.encode(j), flags

    # -- blocks -----------------------------------------------------------
    def block(self, fmt: BlockFormat, values, words=None, conv=None, signs=None):
        """The section 2.6 quantizer: values (Fraction | Special, `size`
        of them) into one block. Returns (bits, [flags per element])."""
        conv = conv or {}
        scale_rounding = conv.get("block_scale_rounding", "nearest")
        elem_overflow = conv.get("block_element_overflow", "saturate")
        invalid_result = conv.get("invalid_result", "saturate")
        words = words or [0] * fmt.size
        assert len(values) == fmt.size, (fmt.name, len(values))
        elem = fmt.elem
        fl = isinstance(elem, FloatFormat)
        negative_invalid = [fl and not elem.signed and
                            (v is NINF or (not isinstance(v, Special) and v < 0)) for v in values]
        values = [NAN if bad else value for value, bad in zip(values, negative_invalid)]
        finite = [abs(v) for v in values if not isinstance(v, Special)]
        amax = max(finite) if finite else Fraction(0)
        emax = elem.max_finite() if fl else Fraction(elem.max_int)
        from chialu.verify.formats import _floor_log2
        if fmt.scale.exp_only:
            if amax == 0:
                sb = 0
            else:
                e = _floor_log2(amax) - _floor_log2(emax)
                sb = fmt.scale.round(Fraction(2) ** e, "RTZ")
        else:
            q = amax / emax if amax > 0 else Fraction(0)
            sb = fmt.scale.round(q, "RNE" if scale_rounding == "nearest" else "RUP")
            if not fmt.scale_valid(sb):
                sb = (fmt.scale.encode(fmt.scale.min_positive()) if fmt.scale.decode(sb) == 0
                      else fmt.scale._max_finite_bits())
        sc = fmt.scale.decode(sb)
        elems, eflags = [], []
        for j, v in enumerate(values):
            fl_j = set()
            if negative_invalid[j]:
                from chialu.verify.alu_ref import _nan_result
                bits, invalid_flags = _nan_result(elem, conv, [], invalid_sign=1)
                elems.append(bits)
                eflags.append(invalid_flags | {"invalid"})
                continue
            if isinstance(v, Special):
                fl_j.add("invalid" if v is NAN or v is NAR else "overflow")
                if fl and elem.has_nan and (v is NAN or v is NAR
                                            or not (elem.has_inf and elem_overflow == "inf")):
                    elems.append(elem.encode_special(NAN))
                    fl_j.add("nan")
                elif fl and elem.has_inf and elem_overflow == "inf" and v in (PINF, NINF):
                    elems.append(elem.encode_special(v))
                elif invalid_result == "zero":
                    elems.append(0)
                    fl_j.add("inexact")
                else:
                    top = elem._max_finite_bits() if fl else elem.encode(elem.min_int if v is NINF else elem.max_int)
                    neg = v is NINF and (fl and elem.signed)
                    elems.append(top | ((1 << (elem.width - 1)) if neg else 0))
                    fl_j.add("inexact")
                eflags.append(fl_j)
                continue
            x = v / sc
            if fl:
                if elem_overflow == "saturate" and abs(x) > emax:
                    x = emax if x > 0 else -emax
                    fl_j |= {"overflow", "inexact"}
                    if not elem.signed and x < 0:
                        raise ValueError(f"{fmt.name}: negative element in "
                                         f"an unsigned element format")
                    eb = elem.encode(x)
                else:
                    zs = signs[j] if signs else 0
                    eb, f2 = self.float(elem, x, words[j], 1 if v < 0 else (zs if v == 0 else 0))
                    fl_j |= f2
                    # ftz applies per element before quantization
            else:
                i = self.to_int(x, words[j])
                if i != x:
                    fl_j.add("inexact")
                j2 = elem.saturate(i)
                if j2 != i:
                    fl_j |= {"overflow", "inexact"}
                eb = elem.encode(j2)
            ev = elem.decode(eb)
            if not isinstance(ev, Special) and ev * sc != v:
                fl_j.add("inexact")
            elems.append(eb)
            eflags.append(fl_j)
        return fmt.join(elems, sb), eflags


def flag_word(flags: set, names) -> int:
    """The flags of one result packed in list order (bit i = names[i])."""
    w = 0
    for i, n in enumerate(names):
        if n in flags:
            w |= 1 << i
    return w
