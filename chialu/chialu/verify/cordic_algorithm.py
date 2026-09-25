"""Independent fixed-point contracts for CORDIC micro-rotation chains."""
import hashlib
import json
from fractions import Fraction
from functools import lru_cache


def _series_bounds(value, precision, hyperbolic=False):
    total = Fraction(0)
    power = value
    square = value * value
    for term in range(2 * precision + 64):
        total += power / (2 * term + 1) * (1 if hyperbolic or term % 2 == 0 else -1)
        power *= square
        following = power / (2 * term + 3)
        if hyperbolic:
            low, high = total, total + following / (1 - square)
        else:
            next_sum = total + following * (-1 if term % 2 == 0 else 1)
            low, high = min(total, next_sum), max(total, next_sum)
        if high - low < Fraction(1, 1 << precision):
            return low, high
    raise ValueError("CORDIC angle series did not establish its requested precision")


@lru_cache(maxsize=8192)
def angle_constant(coordinate, fraction_bits, shift):
    """Round an elementary angle using rational bounds rather than the generator's mpmath call."""
    if coordinate == "linear":
        return (1 << fraction_bits) >> shift
    if coordinate == "hyperbolic" and shift == 0:
        raise ValueError("atanh(1) is not a finite CORDIC angle")
    precision = fraction_bits + 8
    while precision <= 4 * fraction_bits + 256:
        if coordinate == "circular" and shift == 0:
            # tan(4 atan(1/5) - atan(1/239)) = 1, and the angle is in
            # (0, pi/2), so this gives pi/4 with fast rational bounds.
            al, ah = _series_bounds(Fraction(1, 5), precision + 3)
            bl, bh = _series_bounds(Fraction(1, 239), precision + 3)
            low, high = 4 * al - bh, 4 * ah - bl
        else:
            low, high = _series_bounds(Fraction(1, 1 << shift), precision, coordinate == "hyperbolic")
        lower = (low * (1 << fraction_bits) + Fraction(1, 2)) // 1
        upper = (high * (1 << fraction_bits) + Fraction(1, 2)) // 1
        if lower == upper:
            return int(lower)
        precision *= 2
    raise ValueError("CORDIC angle rounding is undecided")


def signed(value, width):
    value &= (1 << width) - 1
    return value - (1 << width) if value >> (width - 1) else value


def signed_digit_add(positive, negative, add_positive, add_negative, width):
    """Normalize radix-two signed digits with transfers chosen from the lower digits."""
    if positive & negative or add_positive & add_negative:
        raise ValueError("each signed-digit position must contain at most one nonzero sign")
    result_positive = result_negative = transfer = 0
    for position in range(width):
        digit = ((positive >> position) & 1) - ((negative >> position) & 1) \
                + ((add_positive >> position) & 1) - ((add_negative >> position) & 1)
        lower_negative = position > 0 and bool(((negative | add_negative) >> (position - 1)) & 1)
        outgoing = 1 if digit == 2 or (digit == 1 and not lower_negative) else \
                   -1 if digit == -2 or (digit == -1 and lower_negative) else 0
        result = digit - 2 * outgoing + transfer
        if result not in (-1, 0, 1):
            raise ValueError("signed-digit transfer did not normalize its output")
        result_positive |= int(result == 1) << position
        result_negative |= int(result == -1) << position
        transfer = outgoing
    return result_positive, result_negative


class CordicRotationContract:
    def __init__(self, definition):
        self.definition = dict(definition)
        if definition.get("kind") != "cordic_rotation":
            raise ValueError("not a CORDIC rotation contract")
        if not all(definition["input_signed"]):
            raise ValueError("this contract requires signed coordinate and residual inputs")
        for shift in set(definition["schedule"]):
            expected = angle_constant(definition["coordinate"],
                                      definition.get("angle_fraction_bits", definition["fraction_bits"]), shift)
            if definition["angles"][shift] != expected:
                raise ValueError(f"elementary angle {shift} differs from the independently rounded contract")

    @property
    def sha256(self):
        return hashlib.sha256(json.dumps(self.definition, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    def evaluate(self, inputs):
        data = self.definition
        x_width, y_width, width = data["input_widths"]
        for name, bits in zip(("x", "y", "z"), (x_width, y_width, width)):
            if not 0 <= inputs[name] < 1 << bits:
                raise ValueError(f"{name} does not fit its contracted port")
        x, y, z = (signed(inputs[name], bits) for name, bits in zip(("x", "y", "z"), (x_width, y_width, width)))
        mode, residual = data["coordinate"], data["residual_arithmetic"]
        vectoring = data["vectoring"]
        if mode == "linear" and not vectoring and residual != "cpa":
            raise ValueError("redundant linear rotation has no verified direction-selection contract")
        double = data["scale_handling"] == "double_rotation"
        fraction = data["fraction_bits"]
        mask = (1 << width) - 1
        sum_word, carry_word = z & mask, 0
        positive, negative = max(z, 0), max(-z, 0)

        def rotate(first, second, first_width, second_width, shift, plus):
            shifted_first, shifted_second = first >> shift, second >> shift
            first_shift_width = max(1, first_width - shift)
            second_shift_width = max(1, second_width - shift)
            direction = 1 if plus else -1
            if mode == "linear":
                next_first, next_first_width = first, first_width
            else:
                next_first = first + (-1 if mode == "circular" else 1) * direction * shifted_second
                next_first_width = max(first_width, second_shift_width) + 1
            next_second = second + direction * shifted_first
            next_second_width = max(second_width, first_shift_width) + 1
            return next_first, next_second, next_first_width, next_second_width

        for shift in data["schedule"]:
            angle = data["angles"][shift]
            zero = False
            double_step = False
            if mode == "linear" or (residual == "cpa" and not double):
                plus = y < 0 if vectoring else z >= 0
            elif residual == "cpa":
                estimate = -y if vectoring else z
                half = 1 << max(0, fraction - shift - 1)
                plus, zero = estimate >= half, -half < estimate < half
                double_step = True
            else:
                low = max(0, fraction - shift - data["estimate_bits"])
                high = min(width - 1, fraction - shift + 3)
                window = high - low + 1
                window_mask = (1 << window) - 1
                if vectoring:
                    estimate = -signed((y >> low) & window_mask, window)
                elif residual == "carry_save":
                    estimate = signed(((sum_word >> low) & window_mask) + ((carry_word >> low) & window_mask), window)
                elif residual == "signed_digit":
                    estimate = signed(((positive >> low) & window_mask) - ((negative >> low) & window_mask), window)
                else:
                    raise ValueError(f"unknown residual arithmetic {residual}")
                half = 1 << max(0, min(data["estimate_bits"] - 1, window - 2))
                if double:
                    plus, zero = estimate >= half, -half < estimate < half
                    double_step = True
                else:
                    plus = estimate >= 0
            if double_step:
                signs = (True, False) if zero else (plus, plus)
                for direction in signs:
                    x, y, x_width, y_width = rotate(x, y, x_width, y_width, shift, direction)
                angle *= 2
            else:
                x, y, x_width, y_width = rotate(x, y, x_width, y_width, shift, plus)
            x_width, y_width = min(x_width, width + 2), min(y_width, width + 2)
            x, y = signed(x, x_width), signed(y, y_width)
            change = 0 if zero else -angle if plus else angle
            if residual == "cpa":
                z = signed(z + change, width)
            elif residual == "carry_save":
                addend = change & mask
                total = sum_word ^ carry_word ^ addend
                carry_word = ((sum_word & carry_word) | (sum_word & addend) | (carry_word & addend)) << 1 & mask
                sum_word = total & mask
            elif residual == "signed_digit":
                positive, negative = signed_digit_add(positive, negative, max(change, 0) & mask, max(-change, 0) & mask, width)
        if residual == "carry_save":
            z = signed(sum_word + carry_word, width)
        elif residual == "signed_digit":
            z = signed(positive - negative, width)
        if [x_width, y_width, width] != data["output_widths"]:
            raise ValueError("CORDIC output widths differ from the declared recurrence")
        return {name: value & ((1 << bits) - 1) for name, value, bits in
                zip(("x", "y", "z"), (x, y, z), data["output_widths"])}

    def report(self):
        return {"kind": "cordic_rotation", "contract_sha256": self.sha256,
                "scope": "micro-rotations and angle constants; argument reduction, gain compensation and output packing need separate contracts",
                "primitive_assumption": "exact integer arithmetic; approximate component compositions need their own contract",
                "reference": "independent integer recurrence and signed-digit transfer model; no Net callbacks"}
