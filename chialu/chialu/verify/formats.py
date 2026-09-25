"""Number formats as composable objects (microarchitecture-independent).

Every format implements the same protocol over raw bit patterns:
  decode(bits)  -> Val (Fraction | int | Special)
  encode(val)   -> bits (val must be exactly representable)
  round(real, mode) -> bits (real is Fraction; IEEE-style modes)
  corners()     -> list[bits] (directed patterns for stimulus)
  sample(rng)   -> bits (uniform random pattern, valid for the format)
  index(bits)   -> int monotone in value (ulp distance = index delta)
  ulp_at(bits)  -> Fraction (spacing at that point, for error metrics)
  all_bits()    -> iterator over every pattern (formats <= 16 bits)

Specials are singletons: NAN, PINF, NINF, NAR (posit). BCD rejects
invalid digit patterns at sample time; decode raises on them.
"""

from __future__ import annotations

import re
from fractions import Fraction


class Special:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name


NAN = Special("NaN")
PINF = Special("+Inf")
NINF = Special("-Inf")
NAR = Special("NaR")

ROUND_MODES = ("RNE", "RTZ", "RDN", "RUP", "RNA")


def _mask(w):
    return (1 << w) - 1


class Format:
    name = "format"
    width = 0

    def all_bits(self):
        if self.width > 16:
            raise ValueError(f"{self.name}: {self.width} bits not exhaustible")
        return range(1 << self.width)

    def sample(self, rng):
        return rng.bits(self.width)

    def valid(self, bits):
        return True


# ---------------------------------------------------------------- ints --


class IntFormat(Format):
    """Fixed-width integer under one of the chiALU encodings."""

    def __init__(self, width, encoding="twos_complement"):
        assert encoding in ("twos_complement", "ones_complement",
                            "sign_magnitude", "unsigned")
        self.width = width
        self.encoding = encoding
        self.name = f"int{width}_{encoding}"

    @property
    def min_int(self):
        w = self.width
        return {"twos_complement": -(1 << (w - 1)),
                "ones_complement": -(_mask(w - 1)),
                "sign_magnitude": -(_mask(w - 1)),
                "unsigned": 0}[self.encoding]

    @property
    def max_int(self):
        w = self.width
        return _mask(w) if self.encoding == "unsigned" else _mask(w - 1)

    def decode(self, bits):
        w, e = self.width, self.encoding
        bits &= _mask(w)
        if e == "unsigned":
            return bits
        s = bits >> (w - 1)
        if e == "twos_complement":
            return bits - (1 << w) if s else bits
        if e == "ones_complement":
            return -((~bits) & _mask(w)) if s else bits
        return -(bits & _mask(w - 1)) if s else bits  # sign_magnitude

    def encode(self, val):
        w, e = self.width, self.encoding
        assert self.min_int <= val <= self.max_int, (self.name, val)
        if e == "unsigned" or val >= 0:
            return val & _mask(w)
        if e == "twos_complement":
            return (val + (1 << w)) & _mask(w)
        if e == "ones_complement":
            return (~(-val)) & _mask(w)
        return (1 << (w - 1)) | (-val)  # sign_magnitude

    def wrap(self, val):
        """Frozen overflow semantics per encoding ring."""
        w, e = self.width, self.encoding
        if e == "unsigned":
            return val & _mask(w)
        if e == "twos_complement":
            v = val & _mask(w)
            return v - (1 << w) if v >> (w - 1) else v
        if e == "ones_complement":       # mod 2^w - 1 residue ring
            m = _mask(w)
            v = val % m
            return v if v <= self.max_int else v - m
        mag = abs(val) & _mask(w - 1)    # sign_magnitude wraps magnitude
        return -mag if (val < 0 and mag) else mag

    def saturate(self, val):
        return max(self.min_int, min(self.max_int, val))

    def round(self, real, mode="RNE"):
        """Integer formats: exact integers wrap; non-integers round
        then wrap (accumulator use). Specials: NaR/NaN -> the min-int
        pattern (the posit-standard quire NaR); +/-Inf clamp."""
        if isinstance(real, Special):
            if real in (NAR, NAN):
                return 1 << (self.width - 1) if self.encoding != "unsigned" \
                    else _mask(self.width)
            return self.encode(self.max_int if real is PINF
                               else self.min_int)
        q = _round_int(Fraction(real), mode)
        return self.encode(self.wrap(q))

    def corners(self):
        w = self.width
        vals = {0, 1, self.max_int, self.min_int, self.max_int - 1,
                self.min_int + 1}
        if self.encoding != "unsigned":
            vals |= {-1}
        for k in range(0, w, max(1, w // 8)):
            vals |= {1 << k if (1 << k) <= self.max_int else self.max_int}
        pats = {self.encode(v) for v in vals}
        pats |= {0x5555555555555555 & _mask(w), 0xAAAAAAAAAAAAAAAA & _mask(w)}
        if self.encoding in ("ones_complement", "sign_magnitude"):
            pats |= {_mask(w) if self.encoding == "ones_complement"
                     else 1 << (w - 1)}   # negative zero pattern
        return sorted(pats)

    def index(self, bits):
        return self.decode(bits)

    def ulp_at(self, bits):
        return Fraction(1)


class BCDFormat(Format):
    """Packed BCD 8421, unsigned, width/4 digits."""
    encoding = "bcd"

    def __init__(self, width):
        assert width % 4 == 0
        self.width = width
        self.digits = width // 4
        self.name = f"bcd{self.digits}"
        self.max_int = 10 ** self.digits - 1
        self.min_int = 0

    def valid(self, bits):
        for i in range(self.digits):
            if (bits >> (4 * i)) & 0xF > 9:
                return False
        return True

    def decode(self, bits):
        v = 0
        for i in reversed(range(self.digits)):
            d = (bits >> (4 * i)) & 0xF
            if d > 9:
                raise ValueError(f"{self.name}: invalid digit {d:#x}")
            v = v * 10 + d
        return v

    def encode(self, val):
        assert 0 <= val <= self.max_int
        bits = 0
        for i in range(self.digits):
            bits |= (val % 10) << (4 * i)
            val //= 10
        return bits

    def wrap(self, val):
        return val % (10 ** self.digits)

    def saturate(self, val):
        return max(0, min(self.max_int, val))

    def corners(self):
        vals = {0, 1, 9, 10, self.max_int, self.max_int - 1,
                10 ** (self.digits - 1), 5 * 10 ** (self.digits - 1)}
        vals |= {int("9" * k) for k in range(1, self.digits + 1)}
        return sorted(self.encode(v) for v in vals)

    def sample(self, rng):
        return self.encode(rng.below(self.max_int + 1))

    def index(self, bits):
        return self.decode(bits)

    def ulp_at(self, bits):
        return Fraction(1)


class ScaledIntFormat(IntFormat):
    """Two's-complement fixed point with frac_bits (quire accumulators)."""

    def __init__(self, width, frac_bits, name=None):
        super().__init__(width, "twos_complement")
        self.frac_bits = frac_bits
        self.name = name or f"fx{width}_{frac_bits}"
        self._scale = Fraction(1, 1 << frac_bits)

    def decode(self, bits):
        return IntFormat.decode(self, bits) * self._scale

    def encode(self, val):
        q = Fraction(val) / self._scale
        assert q.denominator == 1, (self.name, val)
        return IntFormat.encode(self, int(q))

    def round(self, real, mode="RNE"):
        if isinstance(real, Special):
            if real in (NAR, NAN):
                return 1 << (self.width - 1)      # quire NaR pattern
            return IntFormat.encode(self, self.max_int if real is PINF
                                    else self.min_int)
        q = Fraction(real) / self._scale
        i = _round_int(q, mode)
        return IntFormat.encode(self, max(self.min_int, min(self.max_int, i)))

    def ulp_at(self, bits):
        return self._scale

    def index(self, bits):
        return IntFormat.decode(self, bits)

    def corners(self):
        # value-domain corners clash with the scaled encode; corner
        # PATTERNS of the underlying two's-complement word are valid
        return IntFormat(self.width, "twos_complement").corners()


def _floor_log2(v: Fraction) -> int:
    """floor(log2(v)) for a positive Fraction, exact."""
    assert v > 0
    n, d = v.numerator, v.denominator
    e = n.bit_length() - d.bit_length()
    if (n >> e if e >= 0 else n << -e) < d:
        e -= 1
    return e


def _round_int(q: Fraction, mode: str) -> int:
    from math import floor, ceil
    if q.denominator == 1:
        return int(q)
    lo, hi = floor(q), ceil(q)
    if mode == "RTZ":
        return lo if q >= 0 else hi
    if mode == "RDN":
        return lo
    if mode == "RUP":
        return hi
    d = q - lo
    if d < Fraction(1, 2):
        return lo
    if d > Fraction(1, 2):
        return hi
    if mode == "RNA":
        return hi if q > 0 else lo
    return lo if lo % 2 == 0 else hi   # RNE


# -------------------------------------------------------------- floats --


class FloatFormat(Format):
    """Generic IEEE-like binary float: sign, exp_bits, man_bits fraction.

    Flags cover the OCP small-format variants:
      has_inf   fp16/bf16/fp32/fp8e5m2 True; fp8e4m3/fp4e2m1 False
      has_nan   fp4e2m1 False (every pattern is finite)
    Without inf, rounding overflow saturates to max finite (OCP MX).
    fp8e4m3 reserves only S.1111.111 as NaN.
    """

    def __init__(self, name, exp_bits, man_bits, has_inf=True, has_nan=True,
                 signed=True):
        if man_bits == 0 and has_inf and has_nan:
            raise ValueError(f"{name}: a zero-mantissa format has no distinct encodings for both NaN and infinity")
        self.name = name
        self.exp_bits = exp_bits
        self.man_bits = man_bits
        self.signed = signed
        self.width = (1 if signed else 0) + exp_bits + man_bits
        self.bias = (1 << (exp_bits - 1)) - 1
        self.has_inf = has_inf
        self.has_nan = has_nan
        self.emax_code = _mask(exp_bits)
        # man_bits == 0: an exponent-only format (OCP E8M0): 2^(e-bias) for
        # every exponent field, no zero, no subnormals
        self.exp_only = man_bits == 0

    @property
    def grammar(self):
        return (f"fps{1 if self.signed else 0}e{self.exp_bits}m{self.man_bits}"
                f"{'N' if self.has_nan else ''}{'I' if self.has_inf else ''}")

    def _fields(self, bits):
        m = bits & _mask(self.man_bits)
        e = (bits >> self.man_bits) & _mask(self.exp_bits)
        s = (bits >> (self.man_bits + self.exp_bits)) & 1 if self.signed else 0
        return s, e, m

    def _top(self):
        """The largest exponent field a finite value may carry."""
        if self.exp_only:
            return self.emax_code - (1 if (self.has_inf or self.has_nan) else 0)
        if self.has_inf and not self.has_nan:
            return self.emax_code          # m = 0 there is inf, the rest finite
        return self.emax_code - (1 if self.has_inf else 0)

    def decode(self, bits):
        s, e, m = self._fields(bits & _mask(self.width))
        sign = -1 if s else 1
        if e == self.emax_code:
            if self.has_inf and m == 0:
                return PINF if sign > 0 else NINF
            if self.has_inf and self.has_nan:
                return NAN
            if self.has_nan and m == _mask(self.man_bits):
                return NAN                        # single NaN pattern
            # finite values in the top exponent field (N-only, I-only, none)
        if self.exp_only:
            return sign * Fraction(2) ** (e - self.bias)
        if e == 0:
            frac = Fraction(m, 1 << self.man_bits)
            return sign * frac * Fraction(2) ** (1 - self.bias)
        frac = 1 + Fraction(m, 1 << self.man_bits)
        return sign * frac * Fraction(2) ** (e - self.bias)

    def _max_finite_bits(self):
        top = self._top()
        m = _mask(self.man_bits)
        if not self.exp_only and not self.has_inf and self.has_nan \
                and top == self.emax_code:
            m -= 1                                # below the single NaN
        return (top << self.man_bits) | m

    def max_finite(self):
        return self.decode(self._max_finite_bits())

    def min_positive(self):
        """The smallest positive value (subnormal, or 2^-bias exponent-only)."""
        return self.decode(0 if self.exp_only else 1)

    def encode_special(self, val):
        if val is NAN:
            assert self.has_nan, f"{self.name} has no NaN"
            if self.exp_only or not self.has_inf:
                return (self.emax_code << self.man_bits) | _mask(self.man_bits)
            return (self.emax_code << self.man_bits) | (1 << (self.man_bits - 1))
        if val is PINF:
            return (self.emax_code << self.man_bits) if self.has_inf \
                else self._max_finite_bits()
        if val is NINF:
            if not self.signed:
                raise ValueError(f"{self.name}: no negative values")
            top = 1 << (self.width - 1)
            return top | (self.encode_special(PINF) & _mask(self.width - 1))
        raise ValueError(val)

    def round(self, real, mode="RNE", ftz=False):
        """Fraction -> bits under mode; overflow -> inf, or max finite
        when the mode/format never reaches inf (RTZ, directed-away
        side, formats without inf)."""
        if isinstance(real, Special):
            return self.encode_special(real)
        x = Fraction(real)
        if x < 0 and not self.signed:
            raise ValueError(f"{self.name}: negative value {x}")
        if self.exp_only:
            return self._round_exp_only(x, mode)
        if x == 0:
            return 0
        s = 1 if x < 0 else 0
        a = -x if s else x
        top = self._top()
        # binade: e in [1, top] with 2^(e-bias) <= a, else subnormal e=0;
        # a beyond the top binade rounds relative to it and overflows
        e = max(1, min(top, _floor_log2(a) + self.bias))
        binade = Fraction(2) ** (e - self.bias)
        if a < binade:
            e = 0
            step = Fraction(2) ** (1 - self.bias - self.man_bits)
        else:
            step = binade / (1 << self.man_bits)
        # directed modes act on the magnitude with sign folded in
        smode = {"RDN": "RUP", "RUP": "RDN"}.get(mode, mode) if s else mode
        f = _round_int(a / step, smode)
        if e == 0 and f >= (1 << self.man_bits):
            e, f = 1, f                           # exact promotion to normal
        if f >= (2 << self.man_bits):             # carry out of the binade
            e, f = e + 1, 1 << self.man_bits      # power of two: exact
        inf_only = self.has_inf and not self.has_nan   # m = 0 at the top is inf
        if e > top:                              # overflow beyond the finite range
            to_inf = self.has_inf and (mode in ("RNE", "RNA")
                                       or smode == "RUP")
            if to_inf:
                return self.encode_special(NINF if s else PINF)
            return (s << (self.width - 1)) | self._max_finite_bits()
        if e > 0:
            f -= 1 << self.man_bits               # drop hidden bit
        if inf_only and e == self.emax_code and f == 0:
            reserved = self.emax_code << self.man_bits
            low_bits, high_bits = reserved - 1, reserved + 1
            low, high = self.decode(low_bits), self.decode(high_bits)
            if smode in ("RTZ", "RDN"):
                bits = low_bits
            elif smode == "RUP":
                bits = high_bits
            else:
                # The neighbours span three units of the finer binade.
                # The upper neighbour is even on that common grid.
                bits = high_bits if a - low >= high - a else low_bits
            return ((s << (self.width - 1)) if self.signed else 0) | bits
        if ftz and e == 0 and f != 0:
            f = 0
        bits = (e << self.man_bits) | f
        if not self.has_inf and self.has_nan \
           and bits == (self.emax_code << self.man_bits) | _mask(self.man_bits):
            bits -= 1                             # never round into the NaN
        return ((s << (self.width - 1)) if self.signed else 0) | bits

    def _round_exp_only(self, x, mode):
        """Exponent-only formats hold powers of two: nearest by value with
        ties to the even exponent field, or the directed neighbor."""
        if x == 0:
            return 0                              # the smallest scale
        sign = int(x < 0)
        x = abs(x)
        if sign:
            mode = {"RDN": "RUP", "RUP": "RDN"}.get(mode, mode)
        sign_bits = sign << (self.width - 1)
        k = _floor_log2(x)
        lo, hi = Fraction(2) ** k, Fraction(2) ** (k + 1)
        if x == lo:
            e = k
        elif mode in ("RTZ", "RDN"):
            e = k
        elif mode == "RUP":
            e = k + 1
        else:
            d_lo, d_hi = x - lo, hi - x
            e = k if d_lo < d_hi else k + 1 if d_hi < d_lo else \
                (k if (k + self.bias) % 2 == 0 else k + 1)
        code = e + self.bias
        top = self._top()
        if code < 0:
            return sign_bits
        if code > top:
            if self.has_inf and mode in ("RNE", "RNA", "RUP"):
                return self.encode_special(NINF if sign else PINF)
            return sign_bits | top
        return sign_bits | code

    def encode(self, val):
        if isinstance(val, Special):
            return self.encode_special(val)
        b = self.round(val, "RNE")
        assert self.decode(b) == val, (self.name, val)
        return b

    def corners(self):
        mb, eb = self.man_bits, self.exp_bits
        if self.exp_only:
            out = {0, self.bias, self._top(), max(self.bias - 1, 0),
                   min(self.bias + 1, self._top())}
            if self.has_inf or self.has_nan:
                out.add(self.emax_code)
        else:
            top_finite = self._max_finite_bits()
            out = {0, 1, (1 << mb) - 1,                     # 0, subnormal ends
                   (1 << mb) - 2,                           # largest subnormal - ulp
                   1 << mb, (1 << mb) | 1,                  # smallest normal
                   (self.bias << mb),                       # 1.0
                   (self.bias << mb) | 1,                   # 1.0 + ulp
                   (self.bias << mb) - 1,                   # 1.0 - ulp
                   ((self.bias + 1) << mb),                 # 2.0
                   ((self.bias + 1) << mb) | 1,             # 2.0 + ulp
                   top_finite, top_finite - 1}              # largest finite, - ulp
            # a neighbour the format cannot represent drops out
            out = {b for b in out if 0 <= b <= top_finite}
            if self.has_inf:
                out.add(self.emax_code << mb)
            if self.has_nan:
                out.add(self.encode_special(NAN))
        if self.signed:
            half = self.width - 1
            out |= {(1 << half) | b for b in list(out) if b < (1 << half)}
        return sorted(b & _mask(self.width) for b in out)

    def index(self, bits):
        s, _, _ = self._fields(bits)
        mag = bits & _mask(self.width - (1 if self.signed else 0))
        return -mag if s else mag

    def ulp_at(self, bits):
        s, e, m = self._fields(bits)
        if self.exp_only:
            return Fraction(2) ** (min(e, self._top()) - self.bias)
        if e == self.emax_code and self.has_inf:
            e = self._top()                       # I-only formats retain finite values in this binade
        ee = max(e, 1)
        return Fraction(2) ** (ee - self.bias - self.man_bits)


# --------------------------------------------------------------- posit --


class PositFormat(Format):
    """Standard posit(n, es). NaR = 100..0; no inf/nan; clamps at
    minpos/maxpos (never rounds to zero or NaR)."""

    def __init__(self, n, es):
        self.width = n
        self.es = es
        self.name = f"posit{n}_{es}"
        self.useed = Fraction(2) ** (1 << es)
        self._nar = 1 << (n - 1)

    def decode(self, bits):
        n, es = self.width, self.es
        bits &= _mask(n)
        if bits == 0:
            return Fraction(0)
        if bits == self._nar:
            return NAR
        s = bits >> (n - 1)
        if s:
            bits = (-bits) & _mask(n)             # two's complement
        body = bits & _mask(n - 1)
        # regime: run of identical bits after the sign
        first = (body >> (n - 2)) & 1
        run = 0
        for i in range(n - 2, -1, -1):
            if (body >> i) & 1 == first:
                run += 1
            else:
                break
        k = run - 1 if first else -run
        rest_bits = n - 1 - run - 1               # after the terminator
        rest = body & _mask(max(rest_bits, 0)) if rest_bits > 0 else 0
        e_bits = min(es, max(rest_bits, 0))
        e = (rest >> (rest_bits - e_bits)) if e_bits > 0 else 0
        e <<= (es - e_bits)
        f_bits = max(rest_bits - es, 0)
        f = rest & _mask(f_bits) if f_bits > 0 else 0
        val = (self.useed ** k) * (Fraction(2) ** e) \
            * (1 + Fraction(f, 1 << f_bits if f_bits else 1))
        return -val if s else val

    def round(self, real, mode="RNE"):
        """Posit rounding per the standard: the unbounded posit bit string
        of the value, rounded to n bits (nearest, ties to the pattern
        whose last bit is 0), clamped to maxpos/minpos, never to 0 or NaR.
        Non-RNE modes act on the ordered pattern line."""
        if isinstance(real, Special):
            return self._nar
        x = Fraction(real)
        n, es = self.width, self.es
        if x == 0:
            return 0
        s = x < 0
        a = -x if s else x
        maxpos, minpos = (1 << (n - 1)) - 1, 1
        e_unb = _floor_log2(a)
        k = e_unb >> es
        e = e_unb & ((1 << es) - 1)
        if k > n - 2:
            b = maxpos
        elif k < -(n - 2):
            b = minpos
        else:
            frac = a / (Fraction(2) ** e_unb) - 1          # in [0, 1)
            regime = ((1 << (k + 2)) - 2) if k >= 0 else 1
            rl = k + 2 if k >= 0 else -k + 1
            N = Fraction(regime * (1 << es) + e) + frac    # binary point after the es field
            keep_frac = (n - 1) - rl - es                  # fraction bits kept (may be negative)
            scaled = N * (Fraction(2) ** keep_frac)
            topb = int(scaled)                             # floor: scaled >= 0
            rem = scaled - topb
            if mode in ("RTZ", "RDN", "RUP"):
                up = (rem != 0) and (mode == "RUP") != s
            else:
                up = rem > Fraction(1, 2) or (rem == Fraction(1, 2) and (topb & 1))
            b = topb + (1 if up else 0)
            if b > maxpos:
                b = maxpos
            if b < minpos:
                b = minpos
        return ((-b) & _mask(n)) if s else b

    def encode(self, val):
        if val is NAR:
            return self._nar
        b = self.round(val, "RNE")
        assert self.decode(b) == val, (self.name, val)
        return b

    def corners(self):
        n = self.width
        out = {0, self._nar, 1, (1 << (n - 1)) - 1,          # 0 NaR minpos maxpos
               self.round(Fraction(1)), self.round(Fraction(-1)),
               self.round(self.useed), self.round(1 / self.useed),
               self.round(Fraction(1, 2)), self.round(Fraction(4))}
        out |= {(-b) & _mask(n) for b in list(out)}
        return sorted(out)

    def index(self, bits):
        n = self.width
        bits &= _mask(n)
        return bits - (1 << n) if bits >> (n - 1) else bits

    def ulp_at(self, bits):
        i = self.index(bits)
        lo = max(-(1 << (self.width - 1)) + 1, i - 1)
        hi = min((1 << (self.width - 1)) - 1, i + 1)
        vs = [self.decode(k & _mask(self.width)) for k in (lo, hi)
              if self.decode(k & _mask(self.width)) is not NAR]
        vs = [v for v in vs if not isinstance(v, Special)]
        v = self.decode(bits)
        if isinstance(v, Special) or not vs:
            return Fraction(1)
        return max(abs(x - v) for x in vs) or Fraction(1)


# ------------------------------------------------------ fixed / x87 / block --


class FixedFormat(ScaledIntFormat):
    """fxs<S>i<I>f<F>: S sign bit (two's complement) or none, I integer
    bits, F fraction bits; the pattern P encodes P / 2^F."""

    def __init__(self, signed, int_bits, frac_bits):
        super().__init__(signed + int_bits + frac_bits, frac_bits,
                         name=f"fxs{signed}i{int_bits}f{frac_bits}")
        self.signed = bool(signed)
        self.int_bits = int_bits
        if not signed:
            self.encoding = "unsigned"

    def corners(self):
        pats = set(IntFormat(self.width, self.encoding).corners())
        for v in (Fraction(1), Fraction(-1), Fraction(1, 2), self._scale):
            if self.min_int * self._scale <= v <= self.max_int * self._scale:
                pats.add(self.encode(v))
        return sorted(pats)

    def round(self, real, mode="RNE"):
        if isinstance(real, Special):
            if real in (NAR, NAN):
                return (1 << (self.width - 1)) if self.signed else _mask(self.width)
            return IntFormat.encode(self, self.max_int if real is PINF
                                    else self.min_int)
        return ScaledIntFormat.round(self, real, mode)


class X87Format(Format):
    """fp80: x87 double-extended, sign, 15 exponent bits, 64-bit
    significand with an explicit integer bit. Unnormals (integer bit 0
    with a nonzero exponent), pseudo-denormals (integer bit 1 with a zero
    exponent) and pseudo-NaN/inf (integer bit 0 at the top exponent) are
    invalid patterns; they decode as NaN and are never generated."""

    name = "fp80"
    width = 80

    def __init__(self):
        self.core = FloatFormat("fp80core", 15, 63, True, True)
        self.exp_bits, self.man_bits, self.bias = 15, 63, 16383
        self.has_inf = self.has_nan = self.signed = True

    @staticmethod
    def _split(bits):
        return bits >> 79, (bits >> 64) & 0x7FFF, (bits >> 63) & 1, bits & _mask(63)

    def valid(self, bits):
        s, e, j, f = self._split(bits & _mask(80))
        return (j == 0) if e == 0 else (j == 1)

    def _to_core(self, bits):
        s, e, j, f = self._split(bits & _mask(80))
        return (s << 78) | (e << 63) | f

    def _from_core(self, cb):
        s, e, f = cb >> 78, (cb >> 63) & 0x7FFF, cb & _mask(63)
        return (s << 79) | (e << 64) | ((1 if e else 0) << 63) | f

    def decode(self, bits):
        if not self.valid(bits):
            return NAN
        return self.core.decode(self._to_core(bits))

    def encode(self, val):
        return self._from_core(self.core.encode(val))

    def round(self, real, mode="RNE", ftz=False):
        return self._from_core(self.core.round(real, mode, ftz))

    def max_finite(self):
        return self.core.max_finite()

    def corners(self):
        return sorted({self._from_core(c) for c in self.core.corners()})

    def sample(self, rng):
        return self._from_core(rng.bits(79))

    def index(self, bits):
        return self.core.index(self._to_core(bits))

    def ulp_at(self, bits):
        return self.core.ulp_at(self._to_core(bits))


def quire_format(n, es):
    """quire<n>_<es>: the exact accumulator of posit(n, es): 2^(es+1)(n-2)
    fraction bits, as many integer bits, one sign and 15 carry-guard
    bits."""
    frac = (n - 2) << (es + 1)
    return ScaledIntFormat(16 + 2 * frac, frac_bits=frac,
                           name=f"quire{n}_{es}")


class BlockFormat(Format):
    """blks<scale>e<element>s<size>: `size` elements sharing one scale;
    element i is at bits [i*we +: we], the scale above the elements. A
    pattern decodes to a list of `size` values (scale x element); a NaN,
    zero, negative or infinite scale makes every element NaN and is an
    invalid pattern."""

    def __init__(self, scale, elem, size, name):
        self.scale, self.elem, self.size = scale, elem, size
        self.name = name
        self.width = size * elem.width + scale.width

    def split(self, bits):
        we = self.elem.width
        elems = [(bits >> (i * we)) & _mask(we) for i in range(self.size)]
        return elems, (bits >> (self.size * we)) & _mask(self.scale.width)

    def join(self, elems, scale_bits):
        we = self.elem.width
        bits = 0
        for i, eb in enumerate(elems):
            bits |= (eb & _mask(we)) << (i * we)
        return bits | ((scale_bits & _mask(self.scale.width)) << (self.size * we))

    def scale_valid(self, scale_bits):
        v = self.scale.decode(scale_bits)
        return not isinstance(v, Special) and v > 0

    def valid(self, bits):
        _, sb = self.split(bits)
        return self.scale_valid(sb) and all(self.elem.valid(e)
                                            for e in self.split(bits)[0])

    def decode(self, bits):
        elems, sb = self.split(bits)
        if not self.scale_valid(sb):
            return [NAN] * self.size
        sc = self.scale.decode(sb)
        out = []
        for eb in elems:
            v = self.elem.decode(eb)
            out.append(v if isinstance(v, Special) else v * sc)
        return out

    def _elem_max(self):
        return (self.elem.max_finite() if isinstance(self.elem, FloatFormat)
                else Fraction(self.elem.max_int))

    def encode(self, values, mode="RNE", scale_rounding="nearest",
               elem_overflow="saturate", invalid_result="saturate"):
        """The OCP quantization rule, generalized (formats-and-options
        section 2.6): the scale from the block's largest magnitude, every
        element value / scale rounded under `mode` and saturated."""
        assert len(values) == self.size, (self.name, len(values))
        if isinstance(self.elem, FloatFormat) and not self.elem.signed:
            values = [NAN if value is NINF or (not isinstance(value, Special) and value < 0) else value
                      for value in values]
        finite = [abs(v) for v in values if not isinstance(v, Special)]
        amax = max(finite) if finite else Fraction(0)
        emax = self._elem_max()
        if self.scale.exp_only:
            if amax == 0:
                sb = 0
            else:
                e = _floor_log2(amax) - _floor_log2(emax)
                sb = self.scale.round(Fraction(2) ** e, "RTZ")
        else:
            q = amax / emax if amax > 0 else Fraction(0)
            sb = self.scale.round(q, "RNE" if scale_rounding == "nearest"
                                  else "RUP")
            if not self.scale_valid(sb):
                sb = (self.scale.encode(self.scale.min_positive()) if self.scale.decode(sb) == 0
                      else self.scale._max_finite_bits())
        sc = self.scale.decode(sb)
        elems = []
        fl = isinstance(self.elem, FloatFormat)
        for v in values:
            if isinstance(v, Special):
                if fl and self.elem.has_nan and (v is NAN or not (
                        self.elem.has_inf and elem_overflow == "inf")):
                    elems.append(self.elem.encode_special(NAN))
                elif fl and v is not NAN and self.elem.has_inf \
                        and elem_overflow == "inf":
                    elems.append(self.elem.encode_special(v))
                elif invalid_result == "zero":
                    elems.append(0)
                else:
                    top = self.elem._max_finite_bits() if fl \
                        else self.elem.encode(self.elem.min_int if v is NINF else self.elem.max_int)
                    elems.append(top | ((1 << (self.elem.width - 1))
                                        if v is NINF and fl else 0))
                continue
            x = v / sc
            if fl:
                if elem_overflow == "saturate" and abs(x) > emax:
                    x = emax if x > 0 else -emax
                elems.append(self.elem.round(x, mode))
            else:
                i = _round_int(x, mode)
                elems.append(self.elem.encode(self.elem.saturate(i)))
        return self.join(elems, sb)

    def corners(self):
        ec = self.elem.corners()
        if isinstance(self.scale, FloatFormat):
            s_min = 0 if self.scale.exp_only else 1
            s_one = self.scale.encode(Fraction(1))
            s_max = self.scale._max_finite_bits()
        else:
            s_min = s_one = s_max = self.scale.encode(1)
        top = ec[-1]
        out = {self.join([0] * self.size, s_one),
               self.join([top] * self.size, s_max),
               self.join([top] + [0] * (self.size - 1), s_one),
               self.join([ec[i % len(ec)] for i in range(self.size)], s_one),
               self.join([ec[i % len(ec)] for i in range(self.size)], s_min),
               self.join([ec[(i + 1) % len(ec)] for i in range(self.size)], s_max)}
        return sorted(b for b in out if self.valid(b))

    def sample(self, rng):
        we = self.elem.width
        elems = [rng.bits(we) for _ in range(self.size)]
        while True:
            sb = rng.bits(self.scale.width - (1 if getattr(self.scale, "signed", False) else 0))
            if self.scale_valid(sb):
                return self.join(elems, sb)

    def index(self, bits):
        return bits

    def ulp_at(self, bits):
        _, sb = self.split(bits)
        sc = self.scale.decode(sb)
        return (sc if not isinstance(sc, Special) and sc > 0 else Fraction(1)) \
            * (self.elem.ulp_at(0) if isinstance(self.elem, FloatFormat)
               else Fraction(1))


# --------------------------------------------------------------- grammar --

ALIASES = {
    "fp16": "fps1e5m10NI", "bf16": "fps1e8m7NI", "tf32": "fps1e8m10NI",
    "fp32": "fps1e8m23NI", "fp64": "fps1e11m52NI", "fp128": "fps1e15m112NI",
    "fp8e5m2": "fps1e5m2NI", "fp8e4m3": "fps1e4m3N", "fp8": "fps1e4m3N",
    "fp6e3m2": "fps1e3m2", "fp6e2m3": "fps1e2m3", "fp4e2m1": "fps1e2m1",
    "fp4": "fps1e2m1", "e8m0": "fps0e8m0N",
}
_FLOAT_RE = re.compile(r"^fps([01])e(\d+)m(\d+)(N?)(I?)$")
_FIXED_RE = re.compile(r"^fxs([01])i(\d+)f(\d+)$")
_INT_RE = re.compile(r"^(u?)int(\d+)(_ones|_sm)?$")
_BCD_RE = re.compile(r"^bcd(\d+)$")
_POSIT_RE = re.compile(r"^posit(\d+)_(\d+)$")
_QUIRE_RE = re.compile(r"^quire(\d+)_(\d+)$")


def parse_format(name):
    """A Format from a format string of docs/formats-and-options.md:
    int<W>, uint<W>, int<W>_ones, int<W>_sm, bcd<D>, fxs<S>i<I>f<F>,
    fps<S>e<E>m<M>[N][I] and its aliases, fp80, posit<n>_<es>,
    quire<n>_<es>, blks<scale>e<element>s<size>."""
    name = name.strip()
    if name == "fp80":
        return X87Format()
    canon = ALIASES.get(name, name)
    m = _FLOAT_RE.match(canon)
    if m:
        s_, e, mm, n, i = m.groups()
        e, mm = int(e), int(mm)
        if e < 2:
            raise ValueError(f"{name}: at least 2 exponent bits")
        f = FloatFormat(name, e, mm, has_inf=bool(i), has_nan=bool(n),
                        signed=s_ == "1")
        return f
    m = _FIXED_RE.match(name)
    if m:
        return FixedFormat(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    m = _INT_RE.match(name)
    if m:
        u, w, enc = m.groups()
        w = int(w)
        if u:
            if enc:
                raise ValueError(f"{name}: unsigned has no encoding suffix")
            return IntFormat(w, "unsigned")
        return IntFormat(w, {"_ones": "ones_complement",
                             "_sm": "sign_magnitude"}.get(enc, "twos_complement"))
    m = _BCD_RE.match(name)
    if m:
        return BCDFormat(4 * int(m.group(1)))
    m = _POSIT_RE.match(name)
    if m:
        return PositFormat(int(m.group(1)), int(m.group(2)))
    m = _QUIRE_RE.match(name)
    if m:
        return quire_format(int(m.group(1)), int(m.group(2)))
    if name.startswith("blks"):
        rest = name[4:]
        for i, ch in enumerate(rest):
            if ch != "e":
                continue
            left, right = rest[:i], rest[i + 1:]
            mm = re.match(r"^(.+)s(\d+)$", right)
            if not left or not mm:
                continue
            try:
                sc = parse_format(left)
                el = parse_format(mm.group(1))
            except ValueError:
                continue
            if not isinstance(sc, FloatFormat) or isinstance(el, (BlockFormat, X87Format)):
                continue
            size = int(mm.group(2))
            if size < 2:
                raise ValueError(f"{name}: block size >= 2")
            return BlockFormat(sc, el, size, name)
        raise ValueError(f"{name}: not a block format "
                         f"(blks<scale>e<element>s<size>)")
    raise ValueError(f"unknown format {name!r}")


# ------------------------------------------------------------- factory --


_FLOATS = {
    "fp16": ("fp16", 5, 10, True, True),
    "bf16": ("bf16", 8, 7, True, True),
    "fp32": ("fp32", 8, 23, True, True),
    "fp8e5m2": ("fp8e5m2", 5, 2, True, True),
    "fp8e4m3": ("fp8e4m3", 4, 3, False, True),
    "fp8": ("fp8e4m3", 4, 3, False, True),
    "fp4": ("fp4e2m1", 2, 1, False, False),
    "fp4e2m1": ("fp4e2m1", 2, 1, False, False),
}


def make_format(spec, width=None):
    """Factory from chiALU parameter vocabulary.

    spec: 'fp16'|'bf16'|'fp32'|'fp8e4m3'|'fp8e5m2'|'fp4'|
          'posit16_1'|'posit32_2'|'twos_complement'|'ones_complement'|
          'sign_magnitude'|'unsigned'|'bcd_8421'|'int8'|'int32'|
          'quire128'  (int encodings and quire need width/frac context)
    """
    if spec in _FLOATS:
        return FloatFormat(*_FLOATS[spec])
    if spec.startswith("posit"):
        n, es = spec[5:].split("_")
        return PositFormat(int(n), int(es))
    if spec in ("twos_complement", "ones_complement", "sign_magnitude",
                "unsigned"):
        assert width, f"{spec} needs a width"
        return IntFormat(width, spec)
    if spec == "bcd_8421":
        assert width, "bcd_8421 needs a width"
        return BCDFormat(width)
    if spec.startswith("int"):
        return IntFormat(int(spec[3:]), "twos_complement")
    if spec.startswith("quire"):
        nq = int(spec[5:])
        # posit-standard quire for posit(n, es): fixed point whose
        # fraction covers minpos^2 = 2^-(2^(es+1) (n-2)); integer part
        # covers maxpos^2 plus carry guard. posit16_1 -> frac 56,
        # quire128 (sign 1 + carry 15 + int 56 + frac 56).
        n, es = (width or (16, 1)) if isinstance(width, tuple) else (16, 1)
        frac = (n - 2) << (es + 1)
        return ScaledIntFormat(nq, frac_bits=frac, name=spec)
    return parse_format(spec)
