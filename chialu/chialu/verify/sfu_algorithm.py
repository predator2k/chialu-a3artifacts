"""Independent integer contracts for polynomial SFU evaluators.

The input is a coefficient/segmentation manifest, not a Net, Verilog text
or a generator callback. Coefficient provenance is preserved and hashed;
the separate mathematical SFU reference checks fitting quality and the
complete function's range reduction and reconstruction.
"""
from __future__ import annotations

from bisect import bisect_right
from fractions import Fraction
from functools import cached_property
import hashlib
import json
import math


def _align(value, source, target):
    return value << (target - source) if target >= source else value >> (source - target)


class PolynomialContract:
    def __init__(self, manifest):
        self.data = dict(manifest)
        if self.data.get("kind") != "segmented_polynomial":
            raise ValueError("not a polynomial algorithm contract")
        for key in ("starts", "ends", "shifts", "coefficients", "coefficient_fraction_bits"):
            if not self.data.get(key):
                raise ValueError(f"missing polynomial contract {key}")
        if len(self.data["starts"]) != len(self.data["coefficients"]):
            raise ValueError("coefficient rows and intervals differ")

    @property
    def sha256(self):
        return hashlib.sha256(json.dumps(self.data, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    @property
    def semantic_sha256(self):
        semantic = {key: value for key, value in self.data.items() if key not in ("input", "output")}
        return hashlib.sha256(json.dumps(semantic, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    def _argument(self, value):
        d = self.data
        if not 0 <= value < 1 << d["source_width"]:
            raise ValueError("input does not fit the source argument width")
        if d["smooth_root"]:
            unit = 1 << d["source_fraction_bits"]
            if value >= unit:
                value = 2 * value - unit
        return value >> d["input_shift"]

    @cached_property
    def _adapted(self):
        d = self.data
        fractional = d["coefficient_fraction_bits"]
        degree = len(fractional) - 1
        raw = [[Fraction(c, 1 << f) for c, f in zip(row, fractional)] for row in d["coefficients"]]
        shifts, transformed = [], []
        for row in raw:
            actual_degree = max((i for i, c in enumerate(row) if c), default=0)
            shift = row[actual_degree - 1] / (actual_degree * row[actual_degree]) if actual_degree else Fraction(0)
            shifts.append(shift)
            transformed.append([sum((row[j] * math.comb(j, i) * (-shift) ** (j - i)
                                      for j in range(i, degree + 1)), Fraction(0))
                                for i in range(degree + 1)])
        integer_bits = max((max(0, abs(s.numerator).bit_length() - s.denominator.bit_length() + 1)
                            for s in shifts), default=0)
        fraction = d["working_fraction_bits"] + (degree + 1) * integer_bits + 12
        return fraction, [round(s * (1 << fraction)) for s in shifts], \
            [[round(c * (1 << fraction)) for c in row] for row in transformed]

    def evaluate(self, source):
        d = self.data
        u = self._argument(int(source))
        segment = bisect_right(d["starts"], u) - 1
        if segment < 0 or u >= d["ends"][-1]:
            raise ValueError("argument is outside the contracted partition")
        local = (u - d["starts"][segment]) << d["shifts"][segment]
        ft = d["local_fraction_bits"]
        local = _align(local, d["fraction_bits"], ft)
        coefficients = d["coefficients"][segment]
        fractions = d["coefficient_fraction_bits"]
        working = d["working_fraction_bits"]
        degree = len(coefficients) - 1
        evaluator = d["evaluator"]
        encoding = d["encoding"]
        if evaluator == "coefficient_adapted":
            fraction, shifts, rows = self._adapted
            variable = _align(local, ft, fraction) + shifts[segment]
            square = variable * variable >> fraction
            row = rows[segment]
            def series(indices):
                if not indices:
                    return 0
                result = row[indices[-1]]
                for i in reversed(indices[:-1]):
                    result = row[i] + (result * square >> fraction)
                return result
            result = series(list(range(0, degree + 1, 2))) + \
                (variable * series(list(range(1, degree + 1, 2))) >> fraction)
            result >>= fraction - working
        elif evaluator == "estrin":
            c = [_align(value, frac, working) for value, frac in zip(coefficients, fractions)]
            square = local * local >> ft
            pairs = [c[i] + (c[i + 1] * local >> ft) if i + 1 <= degree else c[i]
                     for i in range(0, degree + 1, 2)]
            result = pairs[-1]
            for pair in reversed(pairs[:-1]):
                result = pair + (result * square >> ft)
        elif evaluator in ("parallel_monomial", "shift_add_coeff") or (
                evaluator == "horner" and degree <= 1 and encoding in ("csd", "po2_pair", "power_of_two")):
            result = _align(coefficients[0], fractions[0], working)
            power = local
            for i in range(1, degree + 1):
                if i > 1:
                    power = power * local >> ft
                coefficient = coefficients[i]
                if encoding == "power_of_two" or evaluator == "shift_add_coeff":
                    if coefficient:
                        shift = abs(coefficient).bit_length() - 1 - fractions[i]
                        magnitude = power << shift if shift >= 0 else power >> -shift
                        term = -magnitude if coefficient < 0 else magnitude
                        result += _align(term, ft, working)
                else:
                    result += _align(coefficient * power, fractions[i] + ft, working)
        elif evaluator == "factored":
            narrow_bits = min(ft, max(2, (ft + 1) // 2 + 2))
            narrow = local >> (ft - narrow_bits)
            result = _align(coefficients[degree], fractions[degree], working)
            for i in range(degree - 1, 0, -1):
                result = _align(coefficients[i], fractions[i], working) + (result * narrow >> narrow_bits)
            if degree:
                result = _align(coefficients[0], fractions[0], working) + (result * local >> ft)
        elif evaluator in ("horner", "fma_based"):
            result = _align(coefficients[degree], fractions[degree], working)
            fraction = working
            for i in range(degree - 1, -1, -1):
                product = result * local
                if evaluator == "fma_based":
                    fraction += ft
                    result = _align(coefficients[i], fractions[i], fraction) + product
                else:
                    result = _align(coefficients[i], fractions[i], working) + (product >> ft)
            result >>= fraction - working
        else:
            raise ValueError(f"unsupported polynomial evaluator contract {evaluator!r}")
        maximum = (1 << d["output_width"]) - 1
        result = min(maximum, max(0, result >> (working - d["output_fraction_bits"])))
        if d.get("residual"):
            table = d["residual"]
            address = u >> max(0, d["input_width"] - table["index_bits"])
            result = min(maximum, max(0, result + table["values"][address]))
        return result

    def report(self):
        return {"kind": self.data["kind"], "family": self.data["family"], "core": self.data["core"],
                "coefficient_source": self.data["coefficient_source"], "manifest_sha256": self.sha256,
                "semantic_sha256": self.semantic_sha256, "primitive_assumption": self.data.get("primitive_assumption"),
                "reference": "independent integer polynomial contract; no Net callbacks or Verilog evaluation"}
