"""Encode engine ports and reference their format-level results in Python."""
from fractions import Fraction

from chialu.verify import ops
from chialu.verify.family_ref import ROUNDING, ValueFormat, _fields, round_ref, unpack_ref
from chialu.verify.formats import FloatFormat, PositFormat, Special, NAN, NAR, PINF, NINF, _floor_log2


def x_ref(value, xw, ew):
    """Encode an exact dyadic value into X, retaining discarded information as sticky."""
    if value in (NAN, NAR):
        return _fields(1, 0, 0, 0, xw, ew) << 1
    if value in (PINF, NINF):
        return _fields(2, int(value is NINF), 0, 0, xw, ew) << 1
    if value == 0:
        return 0
    exponent = _floor_log2(abs(value)) - xw + 1
    scaled = abs(value) / Fraction(2) ** exponent
    significand = int(scaled)
    return (_fields(0, int(value < 0), exponent, significand, xw, ew) << 1) | int(scaled != significand)


def binary_ref(op, fmt, a, b, mode, word=0, ftz=False, zero_positive=True):
    """Reference arithmetic through fp_ref and its exact-value helper for SR and RAZ.

    The engine's add and mul are value-level: they carry no IEEE 754 zero-sign
    rule (RDN's -0 on cancellation, the sign of +0 + -0), which their callers
    apply (alu_float's zero-sign rule, dot_seed's chain). With zero_positive
    (the ZERO_POSITIVE token of the default zero_sign convention), the packer
    writes every exact zero as +0; a nonzero result rounded to zero keeps its sign."""
    if zero_positive and isinstance(fmt, FloatFormat):
        exact = ops._fp2(op, fmt.decode(a), fmt.decode(b))
        if not isinstance(exact, Special) and exact == 0:
            return 0
    if mode in ROUNDING[:4] or isinstance(fmt, PositFormat):
        return ops.fp_ref(op, fmt, a, b, mode, ftz=ftz)
    value = ops._fp2(op, fmt.decode(a), fmt.decode(b))
    return round_ref(fmt, value, mode, word, ftz=ftz)


def probe_value(fmt, bits):
    """Choose a value below, at or above the midpoint after a representable magnitude."""
    value = fmt.decode(bits)
    if isinstance(value, Special):
        return value
    if value == 0:
        return fmt.decode(1) / 2
    magnitude = ops.cvt_ref(ValueFormat(abs(value)), 0, fmt)
    following = fmt.decode(magnitude + 1)
    if isinstance(following, Special):
        step = abs(value) if isinstance(fmt, PositFormat) else Fraction(2) ** (_floor_log2(abs(value)) - fmt.man_bits)
    else:
        step = following - abs(value)
    fraction = Fraction(7 + bits % 3, 16)
    return value + (-step if value < 0 else step) * fraction
