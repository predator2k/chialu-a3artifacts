"""Retain small corrections when a function approaches a representable value."""
from chialu.verify.formats import _floor_log2


def initial_precision(fn, fmt, value, sr_bits=0):
    precision = fmt.width * 3 + 40
    if value and abs(value) < 1 and fn in ("sin", "cos", "tanh", "exp", "exp2", "sigmoid", "gelu", "silu"):
        # sin(x)-x and tanh(x)-x begin at order x^3; cos(x)-1
        # begins at x^2. Their sign must survive directed rounding.
        precision = max(precision, -2 * _floor_log2(abs(value)) + fmt.width + int(sr_bits) + 64)
    return precision
