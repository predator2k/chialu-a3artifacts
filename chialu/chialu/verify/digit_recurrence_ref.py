"""Independent integer contract for real exponential/logarithm digit recurrence.

Logarithmic constants are rounded from rational atanh-series enclosures,
independently of the RTL generator's mpmath evaluation. The state recurrence
uses Python integers and contains no Net or generator callbacks.
"""
from fractions import Fraction
from functools import lru_cache
import hashlib
import json

from chialu.verify.cordic_algorithm import _series_bounds


@lru_cache(maxsize=16384)
def _log_bounds(value, precision):
    if value <= 0:
        raise ValueError("a real logarithm needs a positive factor")
    ratio = (value - 1) / (value + 1)
    if ratio == 0:
        return Fraction(0), Fraction(0)
    low, high = _series_bounds(abs(ratio), precision + 2, hyperbolic=True)
    return (2 * low, 2 * high) if ratio > 0 else (-2 * high, -2 * low)


@lru_cache(maxsize=16384)
def logarithm_constant(value, fraction_bits, base2=False, reciprocal=False):
    """Nearest integer with ties toward +infinity, established by rational bounds."""
    precision = fraction_bits + 12
    while precision <= 4 * fraction_bits + 256:
        low, high = _log_bounds(Fraction(value), precision)
        if reciprocal:
            low, high = 1 / high, 1 / low
        elif base2:
            denominator_low, denominator_high = _log_bounds(Fraction(2), precision)
            if low >= 0:
                low, high = low / denominator_high, high / denominator_low
            else:
                low, high = low / denominator_low, high / denominator_high
        lower = (low * (1 << fraction_bits) + Fraction(1, 2)) // 1
        upper = (high * (1 << fraction_bits) + Fraction(1, 2)) // 1
        if lower == upper:
            return int(lower)
        precision *= 2
    raise ValueError("log-factor rounding is undecided")


def _signed(value, width):
    value &= (1 << width) - 1
    return value - (1 << width) if value >> (width - 1) else value


def _align(value, source, target):
    return value << (target - source) if target >= source else value >> (source - target)


def _round_scaled(value, fraction_bits, shift):
    remainder = fraction_bits - shift
    return (value + (1 << (remainder - 1))) >> remainder if remainder > 0 else value << -remainder


def _exp_bounds(value, precision):
    """Positive exponential series with a geometric upper bound on its tail."""
    if not 0 <= value < 1:
        raise ValueError("the reduced exponential argument must be in [0,1)")
    total = term = Fraction(1)
    for k in range(1, 2 * precision + 64):
        term = term * value / k
        total += term
        following = term * value / (k + 1)
        remainder = following / (1 - value / (k + 2))
        if remainder < Fraction(1, 1 << precision):
            return total, total + remainder
    raise ValueError("exponential series did not reach its requested enclosure")


@lru_cache(maxsize=16384)
def mathematical_bounds(core, value, input_fraction, precision):
    argument = Fraction(value, 1 << input_fraction)
    ln2_low, ln2_high = _log_bounds(Fraction(2), precision + 4)
    if core == "exp2c":
        lower, _ = _exp_bounds(argument * ln2_low, precision + 4)
        _, upper = _exp_bounds(argument * ln2_high, precision + 4)
        return lower, upper
    if core != "log2c":
        raise ValueError("unknown mathematical core")
    lower, upper = _log_bounds(Fraction(3, 4) + argument, precision + 4)
    return (lower / ln2_high, upper / ln2_low) if lower >= 0 else (lower / ln2_low, upper / ln2_high)


def _fraction_record(value):
    return {"numerator": str(value.numerator), "denominator": str(value.denominator)}


class DigitRecurrenceContract:
    def __init__(self, definition):
        self.definition = dict(definition)
        data = self.definition
        if data.get("kind") != "digit_recurrence" or data["core"] not in ("exp2c", "log2c"):
            raise ValueError("not a supported real digit-recurrence contract")
        if data["radix"] not in (2, 4, 16):
            raise ValueError("radix must be 2, 4, or 16")
        if data["digit_set"] not in ("nonredundant", "signed_redundant"):
            raise ValueError("unknown digit set")
        if data["selection"] not in ("table_lookup", "rounding_of_scaled_residual"):
            raise ValueError("unknown digit selection")
        if data["termination"] not in ("iterate_to_full_precision", "linear_extrapolation"):
            raise ValueError("unknown termination")
        self.advance = data.get("index_advance", "sequential")
        if self.advance not in ("sequential", "leading_bit_skip"):
            raise ValueError("unknown index advancement")
        self.normalization = data.get("normalization", "multiplicative")
        if self.normalization not in ("multiplicative", "additive"):
            raise ValueError("unknown normalization coordinates")
        expected_origin = "zero_centered_delta" if self.normalization == "additive" else "one_centered_value"
        if data.get("state_origin", expected_origin) != expected_origin:
            raise ValueError("the normalization state has the wrong coordinate origin")
        source_fraction = data["input_fraction_bits"]
        if data["core"] == "log2c" and source_fraction < 2:
            raise ValueError("logarithm input needs an exactly representable quarter offset")
        expected_stop = min(1 << data["input_width"], (1 << source_fraction) if data["core"] == "exp2c"
                            else 3 << (source_fraction - 2))
        if data.get("domain_lo") != 0 or data.get("domain_hi_exclusive") != expected_stop:
            raise ValueError("the manifest changed the core's mathematical input domain")
        self.radix_bits = data["radix"].bit_length() - 1
        self.fraction = data["output_fraction_bits"] + 6
        full = (self.fraction + self.radix_bits - 1) // self.radix_bits
        self.main_stages = full if data["termination"] == "iterate_to_full_precision" else (full + 1) // 2 + 1
        self.convergent_start = data.get("initial_range_convention") == "exp2_convergent_start_v1"
        self.log_start = data.get("initial_range_convention") == "log2_convergent_start_v1"
        if data.get("initial_range_convention") not in (None, "exp2_convergent_start_v1", "log2_convergent_start_v1"):
            raise ValueError("unknown initial range convention")
        self.bootstrap = int((self.convergent_start or self.log_start) and data["digit_set"] == "signed_redundant" and data["radix"] == 16)
        self.stages = self.main_stages + self.bootstrap
        if self.convergent_start or self.log_start:
            if data["core"] != ("log2c" if self.log_start else "exp2c"):
                raise ValueError("the startup version does not match its core")
            expected = {"main_stages": self.main_stages, "bootstrap_indices": [1] if self.bootstrap else [],
                        "startup_table_through_index": 2,
                        "sequential_indices": ([1] if self.bootstrap else []) + list(range(1, self.main_stages + 1)),
                        "initial_product": ("centered_significand_fold_above_one" if data["digit_set"] == "nonredundant" else "centered_significand")
                        if self.log_start else "one" if data["digit_set"] == "nonredundant" else "upper_half_two_lower_half_one"}
            if any(data.get(key) != value for key, value in expected.items()):
                raise ValueError("the startup convention has a different physical schedule or initial value")
            if data["selection"] == "rounding_of_scaled_residual" and self.main_stages < 3:
                raise ValueError("rounded selection must actually execute after table startup")
            if "residual_signals" in data and len(data["residual_signals"]) != self.stages + 2:
                raise ValueError("residual trace must include initialization, every physical stage, and tail")
        if self.log_start and "accumulator_signals" in data and len(data["accumulator_signals"]) != self.stages + 2:
            raise ValueError("log accumulator trace must include initialization, every physical stage, and tail")
        if "state_signals" in data and len(data["state_signals"]) != self.stages + 2:
            raise ValueError("normalization states must include initialization, every stage, and the tail")
        maximum = data["radix"] - 1 if data["digit_set"] == "nonredundant" else max(1, data["radix"] // 2)
        minimum = 0 if data["digit_set"] == "nonredundant" else -maximum
        self.digits = tuple(range(minimum, maximum + 1))
        for key, expected in (("working_fraction_bits", self.fraction), ("stages", self.stages),
                              ("digit_min", minimum), ("digit_max", maximum)):
            if data[key] != expected:
                raise ValueError(f"{key} does not match the selected algorithm")
        self.ln2 = logarithm_constant(Fraction(2), self.fraction + 2)
        self.inv_ln2 = logarithm_constant(Fraction(2), self.fraction + 2, reciprocal=True)
        if data["ln2"] != self.ln2 or data["inv_ln2"] != self.inv_ln2:
            raise ValueError("range/reconstruction constant differs from its rational enclosure")
        self.factors = {(i, digit): logarithm_constant(Fraction(1) + Fraction(digit, data["radix"] ** i),
                                                     self.fraction, base2=data["core"] == "log2c")
                        for i in range(1, self.main_stages + 1) for digit in self.digits}
        expected_tables = [[self.factors[i, digit] for digit in self.digits] for i in range(1, self.main_stages + 1)]
        if data["log_factors"] != expected_tables:
            raise ValueError("log-factor table differs from independently rounded rational bounds")

    def _exp_digit(self, residual, index):
        data = self.definition
        nonredundant = data["digit_set"] == "nonredundant"
        if index <= 2 or data["selection"] == "table_lookup":
            if nonredundant:
                return max(d for d in self.digits if self.factors[index, d] <= residual)
            digit = self.digits[0]
            for candidate in self.digits[1:]:
                if 2 * residual >= self.factors[index, candidate - 1] + self.factors[index, candidate]:
                    digit = candidate
            return digit
        scale = data["radix"] ** index
        rounded = (2 * residual * scale + (1 << self.fraction)) // (2 << self.fraction)
        digit = max(self.digits[0], min(self.digits[-1], rounded))
        if nonredundant and self.factors[index, digit] > residual:
            digit -= 1
        return digit

    def exp_execution(self, value):
        """Versioned folded exponential, with a non-skippable radix16 bootstrap.

        Leading scheduling is an independent scan of exact digit conditions;
        it neither reads Net callbacks nor copies the RTL leading-bit logic.
        """
        data = self.definition
        if not self.convergent_start or not 0 <= value < 1 << data["input_width"]:
            raise ValueError("input is outside the versioned exponential contract")
        one, source = 1 << self.fraction, data["input_fraction_bits"]
        upper = data["digit_set"] == "signed_redundant" and value >= 1 << (source - 1)
        residual = (value - ((1 << source) if upper else 0)) * self.ln2 >> (source + 2)
        additive = self.normalization == "additive"
        state = ((2 if upper else 1) - int(additive)) * one
        states, residuals, selected, indices, skipped, decisions = [state], [residual], [], [], [], []
        following = 1
        for physical in range(self.stages):
            bootstrap = physical < self.bootstrap
            index = 1 if bootstrap else following if self.advance == "leading_bit_skip" else physical - self.bootstrap + 1
            while index <= self.main_stages:
                digit = self._exp_digit(residual, index)
                if bootstrap or self.advance != "leading_bit_skip" or digit:
                    break
                skipped.append((physical, index))
                index += 1
            active = index <= self.main_stages
            digit = digit if active else 0
            decisions.append({"index": index, "residual": residual, "digit": digit, "active": active,
                              "role": "bootstrap" if bootstrap else "main"})
            selected.append(digit); indices.append(index)
            if not bootstrap:
                following = index + 1 if active else index
            if active:
                correction = state * digit + (one * digit if additive else 0)
                state = _signed(state + (correction >> (index * self.radix_bits)), self.fraction + 4)
                residual = _signed(residual - self.factors[index, digit], self.fraction + 3)
            states.append(state); residuals.append(residual)
        if data["termination"] == "linear_extrapolation":
            state += (residual if additive else 0) + (state * residual >> self.fraction)
        states.append(state); residuals.append(residual)
        result = (state + (one if additive else 0)) >> (self.fraction - data["output_fraction_bits"])
        result = max(0, min((1 << (data["output_fraction_bits"] + 1)) - 1, result))
        return dict(result=result, digits=selected, indices=indices, skipped=skipped, decisions=decisions,
                    states=states, residuals=residuals, initial_upper=bool(upper))

    def _log_digit(self, state, index):
        data = self.definition
        one, scale = 1 << self.fraction, data["radix"] ** index
        additive, nonredundant = self.normalization == "additive", data["digit_set"] == "nonredundant"
        if index <= 2 or data["selection"] == "table_lookup":
            if nonredundant:
                if additive:
                    return max(d for d in self.digits if state * (scale + d) + one * d <= 0)
                return max(d for d in self.digits if state * (scale + d) <= one * scale)
            digit = self.digits[-1]
            for candidate in reversed(self.digits[:-1]):
                if additive:
                    hit = state * (2 * scale + 2 * candidate + 1) + one * (2 * candidate + 1) >= 0
                else:
                    hit = state * (2 * scale + 2 * candidate + 1) >= 2 * one * scale
                if hit:
                    digit = candidate
            return digit
        gap = -state if additive else one - state
        digit = max(self.digits[0], min(self.digits[-1], (2 * gap * scale + one) // (2 * one)))
        overshoot = state * (scale + digit) + one * digit > 0 if additive else state * (scale + digit) > one * scale
        if nonredundant and overshoot:
            digit -= 1
        return digit

    def log_execution(self, value):
        """Zero/one-centered product recurrence and independent log accumulator."""
        data = self.definition
        if not self.log_start or not 0 <= value < 1 << data["input_width"]:
            raise ValueError("input is outside the versioned logarithm port")
        one, source = 1 << self.fraction, data["input_fraction_bits"]
        additive = self.normalization == "additive"
        state = _align(value - (1 << (source - 2)), source, self.fraction) + (0 if additive else one)
        halve = data["digit_set"] == "nonredundant" and state > (0 if additive else one)
        if halve:
            state = (state >> 1) - (one >> 1) if additive else state >> 1
        accumulator = one if halve else 0
        centered = lambda state: state if additive else state - one
        states, residuals, accumulators = [state], [centered(state)], [accumulator]
        selected, indices, skipped, decisions = [], [], [], []
        following = 1
        for physical in range(self.stages):
            bootstrap = physical < self.bootstrap
            index = 1 if bootstrap else following if self.advance == "leading_bit_skip" else physical - self.bootstrap + 1
            while index <= self.main_stages:
                digit = self._log_digit(state, index)
                if bootstrap or self.advance != "leading_bit_skip" or digit:
                    break
                skipped.append((physical, index)); index += 1
            active = index <= self.main_stages
            digit = digit if active else 0
            selected.append(digit); indices.append(index)
            decisions.append(dict(index=index, residual=centered(state), digit=digit, active=active,
                                  role="bootstrap" if bootstrap else "main"))
            if not bootstrap:
                following = index + 1 if active else index
            if active:
                correction = state * digit + (one * digit if additive else 0)
                state = _signed(state + (correction >> (index * self.radix_bits)), self.fraction + 3)
                accumulator -= self.factors[index, digit]
            states.append(state); residuals.append(centered(state)); accumulators.append(accumulator)
        if data["termination"] == "linear_extrapolation":
            accumulator += centered(state) * self.inv_ln2 >> (self.fraction + 2)
        states.append(state); residuals.append(centered(state)); accumulators.append(accumulator)
        return dict(result=accumulator >> (self.fraction - data["output_fraction_bits"]), digits=selected,
                    indices=indices, skipped=skipped, decisions=decisions, states=states, residuals=residuals,
                    accumulators=accumulators, initial_halve=bool(halve))

    def log_skip_certificate(self):
        """Certify all LZC/threshold cells, without enumerating input words.

        The zero-digit predicate has one threshold per sign/index. Splitting
        at those thresholds and at powers of two makes both the leading-bit
        candidate and every zero-digit comparison constant on each cell.
        Threshold monotonicity then proves the max(candidate, following)
        rule for every following index, including the terminal sentinel.
        """
        if not self.log_start:
            return dict(complete=False, reason="legacy log startup is outside this skip proof")
        data = self.definition
        one, radix, count = 1 << self.fraction, data["radix"], self.main_stages
        signed = data["digit_set"] == "signed_redundant"
        cells = 0
        for negative in ((False, True) if signed else (False,)):
            thresholds = [0]
            for index in range(1, count + 1):
                scale = radix ** index
                if not signed:
                    threshold = -(-one // (scale + 1))
                elif index <= 2 or data["selection"] == "table_lookup":
                    threshold = -(-one // (2 * scale - 1)) if negative else one // (2 * scale + 1) + 1
                else:
                    threshold = one // (2 * scale) + 1 if negative else max(1, -(-one // (2 * scale)))
                thresholds.append(threshold)
            if any(thresholds[i] < thresholds[i + 1] for i in range(1, count)) or min(thresholds[1:]) < 1:
                raise ValueError("log zero-digit thresholds are not positive and monotone")
            end = one // 2 + 1
            cuts = sorted({0, end} | {1 << k for k in range(self.fraction) if 1 << k < end}
                          | {threshold for threshold in thresholds[1:] if 0 < threshold < end})
            at = lambda index: thresholds[index] if 1 <= index <= count else 0
            for low, stop in zip(cuts, cuts[1:]):
                for magnitude in {low, stop - 1}:
                    raw = self.fraction + (0 if signed else 1) - magnitude.bit_length()
                    if signed:
                        raw = max(1, raw)
                    candidate = min(count + 1, (raw + self.radix_bits - 1) // self.radix_bits)
                    if candidate > 1 and magnitude >= at(candidate - 1):
                        candidate -= 1
                    if magnitude < at(candidate):
                        candidate = candidate + 1 if signed else count + 1
                    centered = magnitude if negative else -magnitude
                    state = centered + (0 if self.normalization == "additive" else one)
                    direct = next((index for index in range(1, count + 1) if self._log_digit(state, index)), count + 1)
                    if candidate != direct:
                        raise ValueError(f"log leading-bit index differs from exact digit scan at magnitude {magnitude}")
                cells += 1
        return dict(complete=True, scope="log leading-bit zero-digit omission for all |gap|<=S/2",
                    method="integer LZC strata and exact zero-threshold cell partition", cells=cells,
                    magnitudes_per_sign=one // 2 + 1, input_words_enumerated=0,
                    following_rule="positive monotone thresholds prove max(first_nonzero, following) for all following indices",
                    bootstrap="fixed index-one stage excluded from skipping", sentinel=count + 1,
                    primitive_assumption="exact LZC, comparison, integer and ROM primitives")

    def log_convergence_certificate(self):
        """Exact interval images of the selected integer product-floor updates."""
        if not self.log_start:
            return dict(complete=False, reason="legacy log start has no convergence certificate")
        data = self.definition
        one, radix = 1 << self.fraction, data["radix"]
        signed = data["digit_set"] == "signed_redundant"
        lower, upper = (3 * one // 4, 3 * one // 2 - 1) if signed else (one // 2, one)
        initial = [lower - one, upper - one]
        schedule = ([(1, "bootstrap")] if self.bootstrap else []) + [(i, "main") for i in range(1, self.main_stages + 1)]
        records = []
        for physical, (index, role) in enumerate(schedule, 1):
            scale = radix ** index
            lookup = index <= 2 or data["selection"] == "table_lookup"
            images = []
            for digit in self.digits:
                low, high = lower, upper
                if lookup and signed:
                    if digit != self.digits[-1]:
                        low = max(low, -(-(2 * one * scale) // (2 * scale + 2 * digit + 1)))
                    if digit != self.digits[0]:
                        high = min(high, -(-(2 * one * scale) // (2 * scale + 2 * digit - 1)) - 1)
                elif lookup:
                    if digit != self.digits[-1]:
                        low = max(low, one * scale // (scale + digit + 1) + 1)
                    if digit != self.digits[0]:
                        high = min(high, one * scale // (scale + digit))
                else:
                    if digit != self.digits[-1]:
                        low = max(low, one - (-(-((2 * digit + 1) * one) // (2 * scale))) + 1)
                    if digit != self.digits[0]:
                        high = min(high, one - (-(-((2 * digit - 1) * one) // (2 * scale))))
                if low > high:
                    continue
                if not lookup and not signed and digit:
                    split = one * scale // (scale + digit)
                    if high > split:
                        images.append([max(low, split + 1) * (scale + digit - 1) // scale,
                                       high * (scale + digit - 1) // scale])
                    high = min(high, split)
                if low <= high:
                    images.append([low * (scale + digit) // scale, high * (scale + digit) // scale])
            if not images:
                raise ValueError("empty logarithm selector interval image")
            before = [lower - one, upper - one]
            lower, upper = min(row[0] for row in images), max(row[1] for row in images)
            if not one // 2 <= lower <= upper <= 3 * one // 2:
                raise ValueError("log interval escaped the complete leading-bit proof's magnitude domain")
            limit = (one + scale - 1) // scale + 3 * physical
            if role == "main" and max(abs(lower - one), abs(upper - one)) > limit:
                raise ValueError(f"log residual convergence fails at index {index}: {lower-one}..{upper-one}, limit {limit}")
            records.append(dict(index=index, role=role, selector="table_lookup" if lookup else data["selection"],
                                input_interval=before, output_interval=[lower - one, upper - one], contraction_limit=limit))
        return dict(complete=True, scope="real logarithm core centered integer state; exact primitives",
                    method="exact selector-region intersection and product-floor interval images", initial_interval=initial,
                    stages=records, input_words_enumerated=0, contract_sha256=self.sha256, whole_seed=False,
                    state_domain_invariant="S/2 <= product <= 3S/2 at every stage",
                    quantization_term="3 times physical stage count in working integer units",
                    skip_certificate=self.log_skip_certificate() if self.advance == "leading_bit_skip" else None,
                    skip_premise="only zero main digits omitted; bootstrap always executed")

    def log_analytic_error_enclosure(self):
        proof = self.log_convergence_certificate()
        if not proof["complete"]:
            return proof
        data = self.definition
        one = 1 << self.fraction
        last = proof["stages"][-1]["output_interval"]
        t = Fraction(max(abs(last[0]), abs(last[1])), one)
        delta = Fraction(3 * (self.stages + 1), one)
        if t >= 1:
            raise ValueError("log residual certificate cannot bound the logarithm away from zero")
        precision = data["output_fraction_bits"] + 24
        ln2_lower, _ = _log_bounds(Fraction(2), precision)
        if data["termination"] == "linear_extrapolation":
            _, perturbation_upper = _log_bounds(1 + delta / (1 - t), precision)
            bound = (perturbation_upper + t * t / (2 * (1 - t))) / ln2_lower
            bound += t / (8 * one) + Fraction(1, one)
        else:
            negative_lower, _ = _log_bounds(1 - t, precision)
            _, positive_upper = _log_bounds(1 + t + delta, precision)
            bound = max(-negative_lower, positive_upper) / ln2_lower
        bound += Fraction(self.stages, 2 * one) + Fraction(1, 1 << data["output_fraction_bits"])
        return dict(complete=True, scope="digit-recurrence logarithm core", whole_seed=False,
                    method="integer product-floor interval certificate plus rational logarithm and rounding bounds",
                    maximum_absolute_error=[_fraction_record(Fraction(0)), _fraction_record(bound)],
                    signed_error=[_fraction_record(-bound), _fraction_record(bound)],
                    input_words_enumerated=0, inputs=data["domain_hi_exclusive"] - data["domain_lo"],
                    factor_suffix_growth_bound=3, initial_normalized_significand_floor_error_in_working_units=1,
                    per_log_constant_error_in_working_units="1/2", contract_sha256=self.sha256,
                    primitive_assumption=data.get("primitive_assumption"))

    def convergence_certificate(self):
        """All-input integer interval proof, independent of the input word count.

        Every selector region is intersected with a residual interval and
        translated by its independently rounded log factor. Taking the hull
        may overapproximate reachability but never discards a residual. Main
        stage envelopes must shrink as radix^-index down to quantization.
        The skip path inherits this proof only when omitted digits are zero.
        This certifies core residual contraction, not a whole-seed ULP bound.
        """
        if self.log_start:
            return self.log_convergence_certificate()
        if not self.convergent_start:
            return {"complete": False, "reason": "legacy start has no convergence certificate"}
        data = self.definition
        signed = data["digit_set"] == "signed_redundant"
        one, radix = 1 << self.fraction, data["radix"]
        divisor = 8 if signed else 4
        extent = (self.ln2 + divisor - 1) // divisor
        lower, upper = (-extent if signed else 0), extent - 1
        initial = [lower, upper]
        records = []
        schedule = ([ (1, "bootstrap") ] if self.bootstrap else []) + [(i, "main") for i in range(1, self.main_stages + 1)]
        for index, role in schedule:
            lookup = index <= 2 or data["selection"] == "table_lookup"
            def boundary(digit):
                if lookup:
                    return (self.factors[index, digit - 1] + self.factors[index, digit] + 1) // 2 if signed else self.factors[index, digit]
                return -(-((2 * digit - 1) * one) // (2 * radix ** index))
            images = []
            for digit in self.digits:
                low = lower if digit == self.digits[0] else max(lower, boundary(digit))
                high = upper if digit == self.digits[-1] else min(upper, boundary(digit + 1) - 1)
                if low > high:
                    continue
                if not lookup and not signed and digit:
                    split = self.factors[index, digit]
                    if low < split:
                        images.append([low - self.factors[index, digit - 1], min(high, split - 1) - self.factors[index, digit - 1]])
                    low = max(low, split)
                if low <= high:
                    images.append([low - self.factors[index, digit], high - self.factors[index, digit]])
            if not images:
                raise ValueError("empty selector interval image")
            before = [lower, upper]
            lower, upper = min(image[0] for image in images), max(image[1] for image in images)
            limit = (one + radix ** index - 1) // radix ** index + 1
            if role == "main" and max(abs(lower), abs(upper)) > limit:
                raise ValueError(f"exp residual convergence fails at index {index}: {lower}..{upper}, limit {limit}")
            records.append(dict(index=index, role=role, selector="table_lookup" if lookup else data["selection"],
                                input_interval=before, output_interval=[lower, upper], contraction_limit=limit))
        return dict(complete=True, scope="real exponential core integer residual; exact primitives",
                    method="exhaustive selector-region integer interval propagation", initial_interval=initial,
                    stages=records, input_words_enumerated=0, contract_sha256=self.sha256,
                    skip_premise="only zero main digits omitted; bootstrap always executed", whole_seed=False)

    def analytic_error_enclosure(self):
        """Conservative core error envelope for every input, without enumeration.

        Positive factor suffix products are <=3 for the declared schedules.
        Each product flooring adds less than 1/S error; each log constant is
        within 1/(2S), and the initial log residual is within 9/(8S).
        Approximate children and surrounding SFU reconstruction are excluded.
        """
        if self.log_start:
            return self.log_analytic_error_enclosure()
        proof = self.convergence_certificate()
        if not proof["complete"]:
            return proof
        data = self.definition
        one = 1 << self.fraction
        last = proof["stages"][-1]["output_interval"]
        t = Fraction(max(abs(last[0]), abs(last[1])), one)
        epsilon = Fraction(4 * self.stages + 9, 8 * one)
        precision = data["output_fraction_bits"] + 24
        _, exp_total = _exp_bounds(t + epsilon, precision)
        product_rounding = Fraction(3 * self.stages, one)
        if data["termination"] == "linear_extrapolation":
            _, exp_residual = _exp_bounds(t, precision)
            bound = product_rounding * (1 + t) + 6 * (t * t * exp_residual / 2 + epsilon * exp_total) + Fraction(1, one)
        else:
            bound = 2 * (exp_total - 1) + product_rounding
        bound += Fraction(1, 1 << data["output_fraction_bits"])
        return dict(complete=True, scope="digit-recurrence exponential core", whole_seed=False,
                    method="integer residual interval certificate plus rational exponential remainder and rounding bounds",
                    maximum_absolute_error=[_fraction_record(Fraction(0)), _fraction_record(bound)],
                    signed_error=[_fraction_record(-bound), _fraction_record(bound)],
                    input_words_enumerated=0, inputs=data["domain_hi_exclusive"] - data["domain_lo"],
                    factor_suffix_growth_bound=3, initial_log_error_in_working_units="9/8",
                    per_log_constant_error_in_working_units="1/2", contract_sha256=self.sha256,
                    primitive_assumption=data.get("primitive_assumption"))

    @property
    def sha256(self):
        return hashlib.sha256(json.dumps(self.definition, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    def evaluate(self, value, trace=False):
        data = self.definition
        if not 0 <= value < 1 << data["input_width"]:
            raise ValueError("input does not fit the contracted port")
        if self.log_start:
            execution = self.log_execution(value)
            return (execution["result"], execution["digits"]) if trace else execution["result"]
        if self.convergent_start:
            execution = self.exp_execution(value)
            return (execution["result"], execution["digits"]) if trace else execution["result"]
        if self.normalization == "additive":
            execution = self.additive_execution(value)
            return (execution["result"], execution["digits"]) if trace else execution["result"]
        if self.advance == "leading_bit_skip":
            result, digits, _, _ = self.skip_execution(value)
            return (result, digits) if trace else result
        fraction, source = self.fraction, data["input_fraction_bits"]
        one = 1 << fraction
        nonredundant = data["digit_set"] == "nonredundant"
        lookup = data["selection"] == "table_lookup"
        selected = []
        if data["core"] == "exp2c":
            residual = value * self.ln2 >> (source + 2)
            result = one
            for stage in range(1, self.stages + 1):
                shift = stage * self.radix_bits
                if lookup and nonredundant:
                    digit = max(d for d in self.digits if self.factors[stage, d] <= residual)
                elif lookup:
                    digit = self.digits[0]
                    for candidate in self.digits[1:]:
                        if 2 * residual >= self.factors[stage, candidate - 1] + self.factors[stage, candidate]:
                            digit = candidate
                else:
                    digit = max(self.digits[0], min(self.digits[-1], _round_scaled(residual, fraction, shift)))
                    if nonredundant and self.factors[stage, digit] > residual:
                        digit -= 1
                selected.append(digit)
                residual = _signed(residual - self.factors[stage, digit], fraction + 3)
                result = _signed(result + (result * digit >> shift), fraction + 4)
            if data["termination"] == "linear_extrapolation":
                result += result * residual >> fraction
            result = max(0, min((1 << (data["output_fraction_bits"] + 1)) - 1,
                                result >> (fraction - data["output_fraction_bits"])))
        else:
            residual = one + _align(value - (1 << (source - 2)), source, fraction)
            result = 0
            if nonredundant and residual > one:
                residual >>= 1
                result = one
            for stage in range(1, self.stages + 1):
                shift = stage * self.radix_bits
                scale = 1 << shift
                if lookup and nonredundant:
                    # Direct integer factor inequality; no copied threshold table.
                    digit = max(d for d in self.digits if residual * (scale + d) <= one * scale)
                elif lookup:
                    digit = self.digits[-1]
                    for candidate in reversed(self.digits[:-1]):
                        if residual * (2 * scale + 2 * candidate + 1) >= 2 * one * scale:
                            digit = candidate
                else:
                    digit = max(self.digits[0], min(self.digits[-1], _round_scaled(one - residual, fraction, shift)))
                    if nonredundant and residual * (scale + digit) > one * scale:
                        digit -= 1
                selected.append(digit)
                result -= self.factors[stage, digit]
                residual = _signed(residual + (residual * digit >> shift), fraction + 3)
            if data["termination"] == "linear_extrapolation":
                result += (residual - one) * self.inv_ln2 >> (fraction + 2)
            result >>= fraction - data["output_fraction_bits"]
        if any(d not in self.digits for d in selected):
            raise AssertionError("selected digit escaped its declared set")
        return (result, selected) if trace else result

    def skip_execution(self, value, *, detail=False):
        """Independent schedule: scan exact digit conditions, never emulate an LZC.

        The residual remains unchanged while scanning zero digits. Recording
        every skipped index establishes the local state-preservation premise
        for equivalence to the sequential recurrence.
        """
        data = self.definition
        if self.advance != "leading_bit_skip":
            raise ValueError("this contract does not select leading-bit advancement")
        if self.log_start:
            execution = self.log_execution(value)
            fields = ("result", "digits", "indices", "skipped", "decisions") if detail else ("result", "digits", "indices", "skipped")
            return tuple(execution[key] for key in fields)
        if self.convergent_start:
            execution = self.exp_execution(value)
            fields = ("result", "digits", "indices", "skipped", "decisions") if detail else ("result", "digits", "indices", "skipped")
            return tuple(execution[key] for key in fields)
        if self.normalization == "additive":
            execution = self.additive_execution(value)
            fields = ("result", "digits", "indices", "skipped", "decisions") if detail else ("result", "digits", "indices", "skipped")
            return tuple(execution[key] for key in fields)
        if not 0 <= value < 1 << data["input_width"]:
            raise ValueError("input does not fit the contracted port")
        fraction, source = self.fraction, data["input_fraction_bits"]
        one = 1 << fraction
        exponential = data["core"] == "exp2c"
        nonredundant = data["digit_set"] == "nonredundant"
        if exponential:
            residual, result = value * self.ln2 >> (source + 2), one
        else:
            residual = one + _align(value - (1 << (source - 2)), source, fraction)
            result = 0
            if nonredundant and residual > one:
                residual >>= 1
                result = one
        following = 1
        selected, indices, skipped = [], [], []
        decisions = []
        for physical in range(self.stages):
            index = following
            while index <= self.stages:
                scale = data["radix"] ** index
                if data["selection"] == "table_lookup":
                    if nonredundant:
                        digit = max(d for d in self.digits if self.factors[index, d] <= residual) if exponential else \
                            max(d for d in self.digits if residual * (scale + d) <= one * scale)
                    elif exponential:
                        digit = self.digits[0]
                        for candidate in self.digits[1:]:
                            if 2 * residual >= self.factors[index, candidate - 1] + self.factors[index, candidate]:
                                digit = candidate
                    else:
                        digit = self.digits[-1]
                        for candidate in reversed(self.digits[:-1]):
                            if residual * (2 * scale + 2 * candidate + 1) >= 2 * one * scale:
                                digit = candidate
                else:
                    magnitude = residual if exponential else one - residual
                    # Exact rational nearest integer, independent of the
                    # generator's variable-shift implementation.
                    rounded = (2 * magnitude * scale + one) // (2 * one)
                    digit = max(self.digits[0], min(self.digits[-1], rounded))
                    overshoot = self.factors[index, digit] > residual if exponential else \
                        residual * (scale + digit) > one * scale
                    if nonredundant and overshoot:
                        digit -= 1
                if digit != 0:
                    break
                skipped.append((physical, index))
                index += 1
            active = index <= self.stages
            indices.append(index)
            selected.append(digit if active else 0)
            decisions.append({"index": index, "residual": residual, "digit": digit if active else 0, "active": active})
            following = index + 1 if active else index
            if not active:
                continue
            shift = index * self.radix_bits
            if exponential:
                residual = _signed(residual - self.factors[index, digit], fraction + 3)
                result = _signed(result + (result * digit >> shift), fraction + 4)
            else:
                result -= self.factors[index, digit]
                residual = _signed(residual + (residual * digit >> shift), fraction + 3)
        if data["termination"] == "linear_extrapolation":
            result += (result * residual >> fraction) if exponential else ((residual - one) * self.inv_ln2 >> (fraction + 2))
        result >>= fraction - data["output_fraction_bits"]
        if exponential:
            result = max(0, min((1 << (data["output_fraction_bits"] + 1)) - 1, result))
        execution = (result, selected, indices, skipped)
        return execution + (decisions,) if detail else execution

    def additive_execution(self, value):
        """Zero-centered affine recurrence; no reconstruction of a normal state in the loop."""
        data = self.definition
        if self.normalization != "additive" or not 0 <= value < 1 << data["input_width"]:
            raise ValueError("input is outside this additive contract")
        if self.log_start:
            return self.log_execution(value)
        if self.convergent_start:
            return self.exp_execution(value)
        fraction, source = self.fraction, data["input_fraction_bits"]
        one = 1 << fraction
        exponential = data["core"] == "exp2c"
        nonredundant = data["digit_set"] == "nonredundant"
        lookup = data["selection"] == "table_lookup"
        skipping = self.advance == "leading_bit_skip"
        accumulator = 0
        if exponential:
            residual, state = value * self.ln2 >> (source + 2), 0
        else:
            state = _align(value - (1 << (source - 2)), source, fraction)
            if nonredundant and state > 0:
                state = (state >> 1) - (one >> 1)
                accumulator = one
        states, selected, indices, skipped, decisions = [state], [], [], [], []
        following = 1
        for physical in range(self.stages):
            index = following if skipping else physical + 1
            while index <= self.stages:
                scale = data["radix"] ** index
                if exponential:
                    if lookup and nonredundant:
                        digit = max(d for d in self.digits if self.factors[index, d] <= residual)
                    elif lookup:
                        digit = self.digits[0]
                        for candidate in self.digits[1:]:
                            if 2 * residual >= self.factors[index, candidate - 1] + self.factors[index, candidate]:
                                digit = candidate
                    else:
                        digit = max(self.digits[0], min(self.digits[-1], (2 * residual * scale + one) // (2 * one)))
                        if nonredundant and self.factors[index, digit] > residual:
                            digit -= 1
                elif lookup and nonredundant:
                    digit = max(d for d in self.digits if state * (scale + d) + one * d <= 0)
                elif lookup:
                    digit = self.digits[-1]
                    for candidate in reversed(self.digits[:-1]):
                        if state * (2 * scale + 2 * candidate + 1) + one * (2 * candidate + 1) >= 0:
                            digit = candidate
                else:
                    digit = max(self.digits[0], min(self.digits[-1], (-2 * state * scale + one) // (2 * one)))
                    if nonredundant and state * (scale + digit) + one * digit > 0:
                        digit -= 1
                if digit != 0 or not skipping:
                    break
                skipped.append((physical, index))
                index += 1
            active = index <= self.stages
            digit = digit if active else 0
            selected.append(digit)
            indices.append(index)
            decisions.append({"index": index, "residual": residual if exponential else state,
                              "digit": digit, "active": active})
            following = index + 1 if active else index
            if active:
                shift = index * self.radix_bits
                # Sum the digit-weighted delta and independent digit bias
                # before flooring, including the partial final radix stage.
                state = _signed(state + ((state * digit + one * digit) >> shift), fraction + (4 if exponential else 3))
                if exponential:
                    residual = _signed(residual - self.factors[index, digit], fraction + 3)
                else:
                    accumulator -= self.factors[index, digit]
            states.append(state)
        if data["termination"] == "linear_extrapolation":
            if exponential:
                state += residual + (state * residual >> fraction)
            else:
                accumulator += state * self.inv_ln2 >> (fraction + 2)
        states.append(state)
        result = (one + state if exponential else accumulator) >> (fraction - data["output_fraction_bits"])
        if exponential:
            result = max(0, min((1 << (data["output_fraction_bits"] + 1)) - 1, result))
        return {"result": result, "digits": selected, "indices": indices, "skipped": skipped,
                "decisions": decisions, "states": states}

    def normalization_states(self, value):
        if self.log_start:
            return self.log_execution(value)["states"]
        if self.convergent_start:
            return self.exp_execution(value)["states"]
        if self.normalization == "additive":
            return self.additive_execution(value)["states"]
        data = self.definition
        _, digits = self.evaluate(value, trace=True)
        indices = self.skip_execution(value)[2] if self.advance == "leading_bit_skip" else range(1, self.stages + 1)
        one = 1 << self.fraction
        exponential = data["core"] == "exp2c"
        if exponential:
            state = one
            residual = value * self.ln2 >> (data["input_fraction_bits"] + 2)
        else:
            source = data["input_fraction_bits"]
            state = one + _align(value - (1 << (source - 2)), source, self.fraction)
            if data["digit_set"] == "nonredundant" and state > one:
                state >>= 1
        states = [state]
        for index, digit in zip(indices, digits):
            if index <= self.stages:
                state = _signed(state + (state * digit >> (index * self.radix_bits)), self.fraction + (4 if exponential else 3))
                if exponential:
                    residual = _signed(residual - self.factors[index, digit], self.fraction + 3)
            states.append(state)
        if exponential and data["termination"] == "linear_extrapolation":
            state += state * residual >> self.fraction
        states.append(state)
        return states

    def error_enclosure(self, max_inputs=65536, precision=None):
        """Enclose the signed and absolute error over the entire contracted core input domain.

        This is an exhaustive finite-domain certificate, not a statistical
        estimate. It makes no whole-seed claim about range reduction,
        reconstruction, exceptional inputs or approximate child components.
        """
        data = self.definition
        first = data.get("domain_lo", 0)
        stop = data.get("domain_hi_exclusive", 1 << data["input_width"])
        count = stop - first
        if count > max_inputs:
            return {"complete": False, "scope": "digit-recurrence core", "inputs_required": count,
                    "reason": "full-domain enumeration exceeds the requested limit; no sampled bound substituted"}
        if count <= 0:
            raise ValueError("the mathematical contract has an empty domain")
        bits = precision or data["output_fraction_bits"] + 12
        signed_low = signed_high = None
        absolute_low = absolute_high = Fraction(0)
        for value in range(first, stop):
            truth_low, truth_high = mathematical_bounds(data["core"], value, data["input_fraction_bits"], bits)
            actual = Fraction(self.evaluate(value), 1 << data["output_fraction_bits"])
            lower, upper = actual - truth_high, actual - truth_low
            signed_low = lower if signed_low is None else min(signed_low, lower)
            signed_high = upper if signed_high is None else max(signed_high, upper)
            absolute_low = max(absolute_low, max(Fraction(0), lower, -upper))
            absolute_high = max(absolute_high, abs(lower), abs(upper))
        return {"complete": True, "scope": "digit-recurrence core", "method": "exhaustive integer input domain with rational series enclosures",
                "inputs": count, "input_range": [first, stop], "contract_sha256": self.sha256,
                "signed_error": [_fraction_record(signed_low), _fraction_record(signed_high)],
                "maximum_absolute_error": [_fraction_record(absolute_low), _fraction_record(absolute_high)],
                "series_precision": bits, "primitive_assumption": data.get("primitive_assumption"),
                "whole_seed": False}
