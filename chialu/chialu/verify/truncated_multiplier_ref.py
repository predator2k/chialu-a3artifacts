"""Independent integer contract for a compensated fixed-width multiplier.

The result is a 2W-bit product word whose low W bits are zero. Thus the
retained W-bit high half is still scaled by 2**W; it is not a W-bit
integer result. No RTL, netlist, reducer, or generated expression is read.
"""
from fractions import Fraction
from functools import lru_cache
import random


DEFAULTS = {"extra_columns_kept": 2, "correction_scheme": "constant", "output_rounding": "truncate"}
SCHEMES = ("none", "constant", "data_dependent", "variable_mmse")
OUTPUT_ROUNDING = ("truncate", "round_to_nearest", "force_lsb_one_jamming")
APPROXIMATE_FAMILIES = frozenset(("truncated_fixed_width", "logarithmic_mitchell", "approximate_compressor",
    "approximate_truncated", "segmented_carry_speculative", "lower_part_approximate", "accuracy_configurable",
    "dynamic_segment", "operand_rounding", "logarithmic", "pp_perforation", "approximate_compressor_tree", "approximate_booth"))
UNCOMPOSED = {"approximate_nested_arithmetic": "the selected nested approximate arithmetic needs its own independent composition contract",
              "nonbinary_nested_adder": "an end-around adder is not the binary weighted sum assumed by this contract"}


def require_exact_reducers(pins):
    for path, family in pins.items():
        if not path.endswith(".family"):
            continue
        if family in APPROXIMATE_FAMILIES:
            raise ValueError(f"uncovered component contract {path}={family}: {UNCOMPOSED['approximate_nested_arithmetic']}")
        if family == "end_around_carry":
            raise ValueError(f"uncovered component contract {path}={family}: {UNCOMPOSED['nonbinary_nested_adder']}")


def output_equivalence(pins):
    """An algebraic equivalence of legal choices, without dropping either.

    At k=0 every retained or correction term is divisible by 2**W.
    Adding 2**(W-1) and clearing the low W bits cannot change that word.
    This describes the algorithm; RTL conformance is checked separately.
    """
    if pins.get("extra_columns_kept", 2) == 0 and pins.get("output_rounding", "truncate") == "round_to_nearest":
        return {"output_rounding": "truncate"}
    return {}


def _low_triangle(a, b, first):
    """The omitted unsigned contribution, using truncated shifted rows."""
    return sum(((a >> i) & 1) * (b & ((1 << (first-i))-1)) * (1 << i) for i in range(first))


def _column(a, b, column, width, signed=False):
    if column < 0:
        return []
    return [(((a >> i) & 1) & ((b >> (column-i)) & 1)) ^ int(signed and ((i == width-1) != (column-i == width-1)))
            for i in range(max(0, column-width+1), min(width-1, column)+1)]


def _second_pairs(a, b, first, width):
    column = _column(a, b, first-2, width)
    return sum(column[index] * column[index+1] for index in range(0, len(column)-1, 2))


@lru_cache(maxsize=256)
def calibration_units(width, first):
    """The declared 4096-pair, seed-1 least-squares intercept, in 2**first units.

    The fit uses unsigned uniform operands even for a signed circuit.
    Evaluate its arithmetic residual exactly, rather than replaying gates.
    """
    if first == 0:
        return 0
    rng = random.Random(1)
    residual = 0
    for _ in range(4096):
        a, b = rng.randrange(1 << width), rng.randrange(1 << width)
        estimate = sum(_column(a, b, first-1, width)) + _second_pairs(a, b, first, width)
        residual += _low_triangle(a, b, first) - (estimate << first)
    return max(0, round(Fraction(residual, 4096 * (1 << first))))


def configuration(width, pins):
    """Validate a canonical algorithm binding before evaluating operands."""
    if isinstance(width, bool) or not isinstance(width, int) or width < 1:
        raise ValueError("multiplier width must be a positive integer")
    require_exact_reducers(pins)
    if "correction" in pins:
        raise ValueError("uncovered legacy truncated multiplier correction contract; use the declared correction_scheme family")
    keep = pins.get("extra_columns_kept", min(width, DEFAULTS["extra_columns_kept"]))
    if isinstance(keep, bool) or not isinstance(keep, int) or not 0 <= keep <= 4 or keep > width:
        raise ValueError(f"extra_columns_kept={keep} cannot be constructed at width {width}")
    scheme = pins.get("correction_scheme", DEFAULTS["correction_scheme"])
    rounding = pins.get("output_rounding", DEFAULTS["output_rounding"])
    if scheme not in SCHEMES or rounding not in OUTPUT_ROUNDING:
        raise ValueError(f"unknown truncated multiplier algorithm {scheme}/{rounding}")
    return keep, scheme, rounding


def product(width, signed, pins, a, b):
    """Return the compensated, output-quantized 2W-bit product pattern."""
    keep, scheme, rounding = configuration(width, pins)
    mask = (1 << width)-1
    a, b = a & mask, b & mask
    first = width-keep
    omitted = _low_triangle(a, b, first)
    va = a-(1 << width) if signed and a >> (width-1) else a
    vb = b-(1 << width) if signed and b >> (width-1) else b
    if signed and first == width:
        # Only the last omitted diagonal can contain Baugh-Wooley sign
        # terms. Its complemented cross terms replace two ordinary bits.
        for i, j in ((0, width-1), (width-1, 0)) if width > 1 else ():
            omitted += (1-2*(((a >> i) & 1) & ((b >> j) & 1))) << (width-1)
    total = va*vb-omitted
    dynamic = 0
    if scheme in ("data_dependent", "variable_mmse") and first:
        dynamic = sum(_column(a, b, first-1, width, signed))
        if scheme == "variable_mmse":
            dynamic += _second_pairs(a, b, first, width)
        total += dynamic << first
    if scheme == "constant":
        mean = sum(Fraction((column+1) << column, 4) for column in range(first))
        total += round(mean / (1 << first)) << first
    elif scheme == "variable_mmse":
        total += calibration_units(width, first) << first
    # data_dependent's nonnegative residual-mean constant is zero: the
    # first omitted diagonal's doubled weight already exceeds that mean.
    if rounding == "round_to_nearest":
        total += 1 << (width-1)  # midpoint ties round upward in this child contract
    result = total & ((1 << (2*width))-1) & ~mask
    if rounding == "force_lsb_one_jamming":
        result |= 1 << width  # unconditional jamming, including an all-zero product
    return result
