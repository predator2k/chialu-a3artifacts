"""Compute SFU table entries at fixed working precision independently of the checker."""
from fractions import Fraction

import mpmath

from chialu.verify.formats import FloatFormat, PositFormat, Special, NAN, NAR, PINF, NINF


def format_precision(fmt):
    """Return the significand precision used by a format."""
    return fmt.man_bits + 1 if isinstance(fmt, FloatFormat) else fmt.width


def working_precision(fmt):
    return max(80, 2 * format_precision(fmt))


def _entry(fn, fmt, bits, mp):
    value = fmt.decode(bits)
    posit = isinstance(fmt, PositFormat)
    negative = bool(bits >> (fmt.width - 1))
    odd_zero = fn in ("sin", "tanh", "erf", "gelu", "silu", "sqrt")

    def zero(sign=False):
        return (1 << (fmt.width - 1)) if sign and not posit else 0

    def rounded(result):
        if result == 0:
            return zero(negative and odd_zero)
        return fmt.round(result, "RNE")

    if value in (NAN, NAR):
        return fmt.round(NAN)
    if value in (PINF, NINF):
        positive = value is PINF
        if fn in ("sin", "cos") or (not positive and fn in ("log", "log2", "sqrt", "rsqrt")):
            return fmt.round(NAN)
        if fn in ("tanh", "erf"):
            return fmt.round(Fraction(1 if positive else -1))
        if fn == "sigmoid":
            return fmt.round(Fraction(int(positive)))
        if fn in ("recip", "rsqrt") or not positive:
            # IEEE 754-2019 section 6.3 gives a quotient the exclusive or of the operand signs,
            # so 1/(-inf) is -0 and 1/(+inf) is +0; rsqrt reaches this with +inf alone, since a
            # negative operand is invalid above.
            return zero(negative and (odd_zero or fn == "recip"))
        return fmt.round(PINF)
    if value == 0:
        if fn in ("log", "log2"):
            return fmt.round(NAR if posit else NINF)
        if fn in ("recip", "rsqrt"):
            # IEEE 754-2019 section 9.2.1: rSqrt(-0) is -inf, as sqrt(-0) is -0 and 1/(-0) is
            # -inf. The sign of the zero carries into the infinity for both functions.
            return fmt.round(NAR if posit else (NINF if negative else PINF))
    if value < 0 and fn in ("log", "log2", "sqrt", "rsqrt"):
        return fmt.round(NAN)
    x = mp.mpf(value.numerator) / value.denominator
    if fn == "exp2":
        result = mp.power(2, x)
    elif fn == "exp":
        result = mp.exp(x)
    elif fn == "log2":
        result = mp.log(x, 2)
    elif fn == "log":
        result = mp.log(x)
    elif fn in ("sin", "cos", "tanh", "sqrt", "erf"):
        result = getattr(mp, fn)(x)
    elif fn == "recip":
        result = 1 / x
    elif fn == "rsqrt":
        result = 1 / mp.sqrt(x)
    elif fn in ("sigmoid", "silu"):
        probability = mp.exp(x) / (1 + mp.exp(x)) if x < 0 else 1 / (1 + mp.exp(-x))
        result = probability if fn == "sigmoid" else x * probability
    elif fn == "gelu":
        result = x * mp.erfc(-x / mp.sqrt(2)) / 2
    elif fn == "softplus":
        result = max(x, 0) + mp.log1p(mp.exp(-abs(x)))
    else:
        raise ValueError(f"no table function {fn}")
    if mp.isnan(result):
        return fmt.round(NAN)
    if mp.isinf(result):
        return fmt.round(NINF if result < 0 else PINF)
    if result == 0:
        return zero(negative and odd_zero)
    maximum_bits = (1 << (fmt.width - 1)) - 1 if posit else fmt._max_finite_bits()
    maximum = fmt.decode(maximum_bits)
    minimum = fmt.decode(1)
    if abs(result) > 2 * mp.mpf(maximum.numerator) / maximum.denominator:
        return fmt.round((-4 if result < 0 else 4) * maximum)
    if abs(result) < mp.mpf(minimum.numerator) / (2 * minimum.denominator):
        return ((-1 if result < 0 else 1) & ((1 << fmt.width) - 1)) if posit else zero(result < 0)
    sign, mantissa, exponent, _ = result._mpf_
    exact_working_value = Fraction(int(mantissa)) * Fraction(2) ** int(exponent)
    return rounded(-exact_working_value if sign else exact_working_value)


def table_values(fn, fmt, precision=None):
    """Evaluate each entry once at working precision and round once into the output format."""
    mp = mpmath.mp.clone()
    mp.prec = working_precision(fmt) if precision is None else int(precision)
    if mp.prec < 2:
        raise ValueError("working precision must be at least two bits")
    return [_entry(fn, fmt, bits, mp) if fmt.valid(bits) else 0 for bits in range(1 << fmt.width)]
