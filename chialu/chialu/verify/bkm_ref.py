"""Independent integer BKM E-mode contract with rational constant enclosures."""
from fractions import Fraction
from functools import lru_cache
import hashlib
import json

from chialu.verify.cordic_algorithm import _series_bounds
from chialu.verify.digit_recurrence_ref import _log_bounds, _exp_bounds, _signed, _fraction_record


@lru_cache(maxsize=4096)
def pi_bounds(precision):
    a, b = _series_bounds(Fraction(1, 5), precision + 6)
    c, d = _series_bounds(Fraction(1, 239), precision + 6)
    return 16 * a - 4 * d, 16 * b - 4 * c


def atan_bounds(value, precision):
    if not -1 <= value <= 1:
        raise ValueError("BKM factors require atan arguments in [-1,1]")
    if value == 0:
        return Fraction(0), Fraction(0)
    if abs(value) == 1:
        low, high = pi_bounds(precision + 2)
        low, high = low / 4, high / 4
    else:
        low, high = _series_bounds(abs(value), precision)
    return (low, high) if value > 0 else (-high, -low)


def nearest_from_bounds(bounds, fraction_bits):
    precision = fraction_bits + 12
    while precision <= 4 * fraction_bits + 256:
        low, high = bounds(precision)
        low = (low * (1 << fraction_bits) + Fraction(1, 2)) // 1
        high = (high * (1 << fraction_bits) + Fraction(1, 2)) // 1
        if low == high:
            return int(low)
        precision *= 2
    raise ValueError("a BKM constant's rounding could not be established")


@lru_cache(maxsize=16384)
def complex_log_constant(index, dx, dy, fraction_bits, radix=2):
    a, b = Fraction(1) + Fraction(dx, radix ** index), Fraction(dy, radix ** index)
    def real_bounds(precision):
        low, high = _log_bounds(a * a + b * b, precision + 1)
        return low / 2, high / 2
    real = nearest_from_bounds(real_bounds, fraction_bits)
    imag = nearest_from_bounds(lambda precision: atan_bounds(b / a, precision), fraction_bits)
    return real, imag


def trig_bounds(argument, precision, cosine=False):
    """Alternating Taylor bounds for arguments between zero and pi/2."""
    term = Fraction(1) if cosine else argument
    total = term
    for step in range(2 * precision + 64):
        first = 2 * step + (1 if cosine else 2)
        term = term * argument * argument / (first * (first + 1))
        following = total + (-term if step % 2 == 0 else term)
        low, high = min(total, following), max(total, following)
        if high - low < Fraction(1, 1 << precision):
            return low, high
        total = following
    raise ValueError("sine/cosine series did not establish its requested precision")


@lru_cache(maxsize=8192)
def mathematical_pair(value, fraction_bits, precision):
    low, high = pi_bounds(precision + 6)
    low, high = low * value / (2 << fraction_bits), high * value / (2 << fraction_bits)
    sin_low, _ = trig_bounds(low, precision + 4)
    _, sin_high = trig_bounds(high, precision + 4)
    cos_low, _ = trig_bounds(high, precision + 4, cosine=True)
    _, cos_high = trig_bounds(low, precision + 4, cosine=True)
    return {"sin": (sin_low, sin_high), "cos": (cos_low, cos_high)}


def component_digit(fraction, index, residual, coordinate, radix=2):
    one = 1 << fraction
    if radix == 4:
        if coordinate not in ("real", "imag"):
            raise ValueError("unknown BKM residual component")
        return max(-2, min(2, (2 * residual * radix ** index + one) // (2 * one)))
    if radix != 2:
        raise ValueError("unknown BKM digit radix")
    if coordinate == "real":
        scaled = residual << (index + 3)
        return -1 if scaled < -4 * one else 1 if scaled >= 3 * one else 0
    if coordinate == "imag":
        scaled = residual << (index + 4)
        return -1 if scaled < -12 * one else 1 if scaled >= 13 * one else 0
    raise ValueError("unknown BKM residual component")


@lru_cache(maxsize=16384)
def first_component_digit(fraction, iterations, residual, coordinate, radix=2):
    # Direct digit scan, independent of the RTL LZC and threshold ROMs.
    return next((index for index in range(1, iterations + 1)
                 if component_digit(fraction, index, residual, coordinate, radix)), iterations + 1)


def zero_threshold(fraction, index, coordinate, negative, radix=2):
    one, scale = 1 << fraction, radix ** index
    if radix == 4:
        return one // (2 * scale) + 1 if negative else -(-one // (2 * scale))
    if radix != 2:
        raise ValueError("unknown BKM threshold radix")
    if coordinate == "real":
        return one // (2 * scale) + 1 if negative else -(-(3 * one) // (8 * scale))
    if coordinate == "imag":
        return (3 * one) // (4 * scale) + 1 if negative else -(-(13 * one) // (16 * scale))
    raise ValueError("unknown BKM zero-digit threshold")


def component_cells(fraction, iterations, coordinate, negative, radix=2):
    """Exact constant-predicate cells across the full signed state word."""
    maximum = (1 << (fraction + 3)) - (0 if negative else 1)
    thresholds = [zero_threshold(fraction, index, coordinate, negative, radix) for index in range(1, iterations + 1)]
    if min(thresholds) < 1 or any(a < b for a, b in zip(thresholds, thresholds[1:])):
        raise ValueError("BKM zero thresholds must be positive and monotone")
    cuts = sorted({0, maximum + 1} | {1 << k for k in range(fraction + 4) if 1 << k <= maximum}
                  | {value for value in thresholds if value <= maximum})
    return list(zip(cuts, cuts[1:]))


def candidate_component_index(fraction, iterations, residual, coordinate, radix=2):
    """Mathematical LZC candidate rule; evaluate() deliberately uses the scan instead."""
    magnitude = abs(residual)
    rb = radix.bit_length() - 1
    base = min(iterations + 1, (max(1, fraction - magnitude.bit_length() - 1) + rb - 1) // rb)
    return next((index for index in range(base, base + 3) if index <= iterations and
                 magnitude >= zero_threshold(fraction, index, coordinate, residual < 0, radix)), iterations + 1)


@lru_cache(maxsize=2048)
def skip_certificate(fraction, iterations, radix=2):
    rows = []
    for coordinate in ("real", "imag"):
        for negative in (False, True):
            cells = component_cells(fraction, iterations, coordinate, negative, radix)
            for low, stop in cells:
                for magnitude in {low, stop - 1}:
                    residual = -magnitude if negative else magnitude
                    direct = first_component_digit(fraction, iterations, residual, coordinate, radix)
                    if candidate_component_index(fraction, iterations, residual, coordinate, radix) != direct:
                        raise ValueError("BKM three-cell leading index differs from direct digit conditions")
            rows.append(dict(coordinate=coordinate, negative=negative, cells=len(cells)))
    return dict(complete=True, scope="BKM simultaneous-zero digit omission over every signed residual pair",
                method="LZC power-of-two strata and exact monotone zero-threshold cells",
                fraction_bits=fraction, state_width=fraction + 4, iterations=iterations,
                signed_residual_pairs=str(1 << (2 * (fraction + 4))), input_words_enumerated=0,
                component_cells=rows,
                combination="min(real_first, imag_first), then max(following); threshold monotonicity proves all following indices",
                zero_update="(0,0) has zero complex logarithm and zero complex product corrections",
                consequence="same finite sequential recurrence and unchanged tail/squaring outputs",
                primitive_assumption="exact integer primitives; approximate children require a composed contract")


@lru_cache(maxsize=2048)
def radix4_convergence_certificate(fraction, iterations):
    """Exact integer residual images; retain the first-stage correlations.

    Each selector cell is an axis-aligned rectangle. Subtracting its fixed
    logarithm is exact, so its translated rectangle encloses every integer
    state in that cell. The first two stages retain the union, because an
    early rectangle hull loses the correlation needed for convergence.
    Subsequent hulls may add unreachable states but cannot lose any.
    """
    if fraction < 10 or not 1 <= iterations <= (fraction + 1) // 2:
        raise ValueError("radix-4 BKM convergence geometry is outside its contract")
    one = 1 << fraction
    pi_eighth = nearest_from_bounds(lambda bits: tuple(v / 8 for v in pi_bounds(bits + 3)), fraction + 4)
    initial = (0, 0, 0, (pi_eighth + 15) // 16 - 1)
    boxes, rows = [initial], []
    for index in range(1, iterations + 1):
        images, scale = [], 4 ** index
        for real_lo, real_hi, imag_lo, imag_hi in boxes:
            for dx in range(-2, 3):
                a = real_lo if dx == -2 else max(real_lo, -(-((2 * dx - 1) * one) // (2 * scale)))
                b = real_hi if dx == 2 else min(real_hi, -(-((2 * dx + 1) * one) // (2 * scale)) - 1)
                if a > b:
                    continue
                for dy in range(-2, 3):
                    c = imag_lo if dy == -2 else max(imag_lo, -(-((2 * dy - 1) * one) // (2 * scale)))
                    d = imag_hi if dy == 2 else min(imag_hi, -(-((2 * dy + 1) * one) // (2 * scale)) - 1)
                    if c > d:
                        continue
                    cr, ci = complex_log_constant(index, dx, dy, fraction, 4)
                    images.append((a - cr, b - cr, c - ci, d - ci))
        rectangle = (min(b[0] for b in images), max(b[1] for b in images),
                     min(b[2] for b in images), max(b[3] for b in images))
        limit = -(-(5 * one) // (8 * scale)) + 2
        if max(map(abs, rectangle)) > limit:
            raise ValueError("radix-4 residual image exceeds its complete convergence enclosure")
        rows.append(dict(index=index, rectangle=list(rectangle), selector_images=len(images), bound=limit))
        boxes = images if index < 2 else [rectangle]
    return dict(complete=True, scope="all integer complex residuals reached by any quarter-angle input width",
                method="exact integer selector-cell images; correlated union through stage two, then conservative rectangle hulls",
                fraction_bits=fraction, radix=4, iterations=iterations, input_words_enumerated=0,
                initial_rectangle=list(initial), stages=rows,
                residual_bound="ceil(5 * 2^F / (8 * 4^index)) + 2 per component",
                constant_source="independently rounded rational ln/atan enclosures",
                primitive_assumption="exact integer primitives; approximate children require a composed contract")


class BkmContract:
    def __init__(self, definition):
        self.definition = dict(definition)
        data = self.definition
        required = {"kind": "complex_bkm_e", "core": "sincos_pair", "state_domain": "complex_bkm",
                    "digit_set": "signed_redundant", "selection": "table_lookup",
                    "angle_divisor": 4}
        for key, value in required.items():
            if data.get(key) != value:
                raise ValueError(f"BKM contract does not implement {key}={data.get(key)}")
        self.radix = data.get("radix")
        if self.radix not in (2, 4):
            raise ValueError("unknown complex BKM radix")
        self.rb, self.alpha, self.dw = (1, 1, 2) if self.radix == 2 else (2, 2, 3)
        if self.radix == 4 and any(data.get(k) != v for k, v in {
                "algorithm_version": "complex_bkm_r4_nearest_rom_v1", "digit_min": -2,
                "digit_max": 2, "digit_width": 3, "radix_bits": 2}.items()):
            raise ValueError("radix-4 BKM requires its explicit signed five-digit contract")
        self.advance = data.get("index_advance", "sequential")
        if self.advance not in ("sequential", "leading_bit_skip"):
            raise ValueError("unknown BKM index advancement")
        version = data.get("schedule_version")
        if (self.advance == "leading_bit_skip" and version != ("complex_bkm_zero_skip_v1" if self.radix == 2 else "complex_bkm_zero_skip_r4_v1")) or \
                (self.advance == "sequential" and version is not None):
            raise ValueError("BKM advancement does not match its versioned schedule")
        if data["normalization"] not in ("multiplicative", "additive") or data["termination"] not in ("iterate_to_full_precision", "linear_extrapolation"):
            raise ValueError("unknown BKM state or termination contract")
        self.fraction = data["output_fraction_bits"] + 10
        self.width = self.fraction + 4
        full = (self.fraction + self.rb - 1) // self.rb
        self.iterations = full if data["termination"] == "iterate_to_full_precision" else (full + 1) // 2 + 1
        if (data["fraction_bits"], data["state_width"], data["iterations"], data["pi_eighth_fraction_bits"]) != \
                (self.fraction, self.width, self.iterations, self.fraction + 4):
            raise ValueError("BKM geometry differs from its precision contract")
        if data["input_width"] != data["input_fraction_bits"]:
            raise ValueError("the BKM argument is not in the quarter-angle domain")
        self.pi_eighth = nearest_from_bounds(lambda bits: tuple(x / 8 for x in pi_bounds(bits + 3)), self.fraction + 4)
        if data["pi_eighth"] != self.pi_eighth:
            raise ValueError("the BKM angle constant differs from its rational enclosure")
        self.constants = {(index, dx, dy): complex_log_constant(index, dx, dy, self.fraction, self.radix)
                          for index in range(1, self.iterations + 1) for dx in range(-self.alpha, self.alpha + 1) for dy in range(-self.alpha, self.alpha + 1)}
        for index in range(1, self.iterations + 1):
            for raw in range(1 << (2 * self.dw)):
                pair = (_signed(raw >> self.dw, self.dw), _signed(raw & ((1 << self.dw) - 1), self.dw))
                expected = self.constants.get((index, *pair), (0, 0))
                actual = (data["real_log_factors"][index - 1][raw], data["imag_log_factors"][index - 1][raw])
                if actual != expected:
                    raise ValueError("a complex log factor differs from independent ln/atan bounds")
        prefix = "slot" if self.advance == "leading_bit_skip" else "iteration"
        labels = ["initial"] + [f"{prefix}_{i}" for i in range(1, self.iterations + 1)] + ["tail", "one_centered_output", "square_1", "square_2"]
        if [state["label"] for state in data["states"]] != labels or any(state["widths"] != [self.width] * 4 for state in data["states"]):
            raise ValueError("BKM state trace omits a recurrence or reconstruction state")
        if len(data["digits"]) != self.iterations or any(len(row["signals"]) != 2 or row.get("slot" if self.advance == "leading_bit_skip" else "index") != index
                for index, row in enumerate(data["digits"], 1)):
            raise ValueError("BKM digit trace does not identify each physical stage")
        if self.advance == "leading_bit_skip":
            fields = ["real_first", "imag_first", "first_nonzero", "following_before", "index", "following_after", "shift"]
            if data.get("physical_stages") != self.iterations or data.get("terminal_index") != self.iterations + 1 or data.get("schedule_fields") != fields:
                raise ValueError("BKM skip schedule geometry or field order changed")
            if len(data.get("schedule", [])) != self.iterations or any(row.get("slot") != index or len(row["signals"]) != 7 or len(row["widths"]) != 7
                    or min(row["widths"]) < (self.iterations + 1).bit_length() or (self.radix == 2 and row["signals"][4] != row["signals"][6])
                    or (self.radix == 4 and row["signals"][4] == row["signals"][6])
                    or row["widths"][4] + self.rb - 1 != row["widths"][6]
                    for index, row in enumerate(data["schedule"], 1)):
                raise ValueError("BKM skip trace omits a live index or shift")


    @property
    def sha256(self):
        return hashlib.sha256(json.dumps(self.definition, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    def evaluate(self, value):
        return self._execute(value, self.advance == "leading_bit_skip")

    def sequential_execution(self, value):
        return self._execute(value, False)

    def skip_certificate(self):
        return skip_certificate(self.fraction, self.iterations, self.radix)

    def convergence_certificate(self):
        if self.radix != 4:
            raise ValueError("this full residual-rectangle certificate is for the radix-4 contract")
        return radix4_convergence_certificate(self.fraction, self.iterations)

    def analytic_error_enclosure(self):
        """Complete, conservative *core* bound, without enumerating input words.

        Product rounding uses an l1 propagation bound; exp/log/squaring use
        complex magnitude. The former bounds the latter. This does not
        certify external argument reduction, reconstruction, or rounding.
        """
        proof = self.convergence_certificate()
        one, count = 1 << self.fraction, self.iterations
        rectangle = proof["stages"][-1]["rectangle"]
        residual = Fraction(max(abs(rectangle[0]), abs(rectangle[1])) + max(abs(rectangle[2]), abs(rectangle[3])), one)
        # Initial pi/8 multiplication: one floor plus a half-unit coefficient
        # error at F+4. Each complex log constant adds <= 1/S in l1.
        exponent_error = Fraction(32 * count + 33, 32 * one)
        # Factor l1 suffix product <= 2 exp(1/3) < 3, at most two floors/stage.
        product_error = Fraction(6 * count, one)
        if residual + exponent_error >= 1 or 4 + product_error >= 8:
            raise ValueError("the BKM analytic envelope cannot establish nonoverflow")
        upper_exp = lambda value: _exp_bounds(value, self.fraction + 24)[1]
        if self.definition["termination"] == "linear_extrapolation":
            error = (product_error * (1 + residual) + 3 *
                     (residual * residual * upper_exp(residual) / 2 + exponent_error * upper_exp(residual + exponent_error))
                     + Fraction(2, one))
        else:
            error = upper_exp(residual + exponent_error) - 1 + product_error
        before_square = error
        for _ in range(2):
            error = error * (2 + error) + Fraction(2, one)
            if 1 + error >= 8:
                raise ValueError("the BKM square envelope cannot establish nonoverflow")
        error += Fraction(1, 1 << self.definition["output_fraction_bits"])
        return dict(complete=True, scope="BKM core pair", whole_seed=False,
                    method="complete residual-cell image and rational complex product/log/square perturbation bounds",
                    inputs=str(1 << self.definition["input_width"]), input_words_enumerated=0,
                    maximum_absolute_error_upper={name: _fraction_record(error) for name in ("sin", "cos")},
                    residual_l1=_fraction_record(residual), exponent_error=_fraction_record(exponent_error),
                    product_rounding_error=_fraction_record(product_error), presquare_error=_fraction_record(before_square),
                    state_nonoverflow=True, contract_sha256=self.sha256,
                    primitive_assumption=self.definition["primitive_assumption"])

    def _execute(self, value, skipping):
        data = self.definition
        if not 0 <= value < 1 << data["input_width"]:
            raise ValueError("input does not fit the BKM port")
        fraction, one = self.fraction, 1 << self.fraction
        additive = data["normalization"] == "additive"
        x, y, er = (0 if additive else one), 0, 0
        ei = value * self.pi_eighth >> (data["input_fraction_bits"] + 4)
        states, digits, indices, omitted, schedule = [(x, y, er, ei)], [], [], [], []
        following = 1
        for physical in range(1, self.iterations + 1):
            index = following if skipping else physical
            while index <= self.iterations:
                dx, dy = component_digit(fraction, index, er, "real", self.radix), component_digit(fraction, index, ei, "imag", self.radix)
                if not skipping or (dx, dy) != (0, 0):
                    break
                omitted.append({"slot": physical, "index": index, "residuals": [er, ei], "digits": [dx, dy]})
                index += 1
            active = index <= self.iterations
            dx, dy = (dx, dy) if active else (0, 0)
            next_following = index + 1 if active else index
            if skipping:
                real_first = first_component_digit(fraction, self.iterations, er, "real", self.radix)
                imag_first = first_component_digit(fraction, self.iterations, ei, "imag", self.radix)
                schedule.append([real_first, imag_first, min(real_first, imag_first), following, index, next_following, self.rb * index])
            if active:
                cr, ci = self.constants[index, dx, dy]
                correction_x = x * dx - y * dy + (one * dx if additive else 0)
                correction_y = y * dx + x * dy + (one * dy if additive else 0)
                x, y = _signed(x + (correction_x >> (self.rb * index)), self.width), _signed(y + (correction_y >> (self.rb * index)), self.width)
                er, ei = _signed(er - cr, self.width), _signed(ei - ci, self.width)
            following = next_following
            states.append((x, y, er, ei)); digits.append((dx, dy)); indices.append(index)
        if data["termination"] == "linear_extrapolation":
            correction_x = x * er - y * ei + (one * er if additive else 0)
            correction_y = y * er + x * ei + (one * ei if additive else 0)
            x, y = _signed(x + (correction_x >> fraction), self.width), _signed(y + (correction_y >> fraction), self.width)
        states.append((x, y, er, ei))
        if additive:
            x = _signed(x + one, self.width)
        states.append((x, y, er, ei))
        for _ in range(2):
            x, y = _signed((x * x - y * y) >> fraction, self.width), _signed((2 * x * y) >> fraction, self.width)
            states.append((x, y, er, ei))
        limit = (1 << (data["output_fraction_bits"] + 1)) - 1
        result = {"sin": max(0, min(limit, y >> 10)), "cos": max(0, min(limit, x >> 10))}
        return {"outputs": result, "states": states, "digits": digits, "indices": indices, "omitted": omitted, "schedule": schedule}

    def error_enclosure(self, max_inputs=65536):
        data = self.definition
        count = 1 << data["input_width"]
        if count > max_inputs:
            return {"complete": False, "scope": "BKM core pair", "inputs_required": count,
                    "reason": "the full-domain limit is exceeded; no sampled bound substituted"}
        errors = {name: [Fraction(0), Fraction(0)] for name in ("sin", "cos")}
        for value in range(count):
            outputs = self.evaluate(value)["outputs"]
            truths = mathematical_pair(value, data["input_fraction_bits"], max(data["output_fraction_bits"] + 14, data["input_fraction_bits"] + 8))
            for name, (low, high) in truths.items():
                actual = Fraction(outputs[name], 1 << data["output_fraction_bits"])
                lower, upper = actual - high, actual - low
                errors[name][0] = max(errors[name][0], lower, -upper)
                errors[name][1] = max(errors[name][1], abs(lower), abs(upper))
        return {"complete": True, "scope": "BKM core pair", "whole_seed": False, "inputs": count,
                "method": "full integer input domain with rational sine/cosine series enclosures",
                "maximum_absolute_error": {name: [_fraction_record(x) for x in values] for name, values in errors.items()},
                "contract_sha256": self.sha256, "primitive_assumption": data["primitive_assumption"]}
