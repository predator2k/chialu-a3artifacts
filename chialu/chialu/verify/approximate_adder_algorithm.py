"""Independent integer contracts for explicitly selected approximate adders.

These contracts assume exact child adders/incrementers. They do not certify
an arbitrary nested approximation or a complete ALU's operation routing.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class TruncatedAdder:
    width: int
    lower_width: int
    scheme: str
    window: int = 0
    correction: bool = False

    @classmethod
    def from_pins(cls, width, pins):
        lower = int(pins.get("lower_part_width", 4))
        scheme = pins.get("lower_scheme", "truncate_constant")
        if not 1 <= lower < width:
            raise ValueError("both lower and upper regions must exist without clipping")
        if scheme not in ("truncate_constant", "or_gates", "segmented_subadders", "speculative_segments"):
            raise ValueError("unknown lower scheme")
        correction = pins.get("correction", "none")
        if correction not in ("none", "configurable_stages"):
            raise ValueError("unknown correction")
        if scheme != "speculative_segments":
            if any(key == "correction" or key == "speculation_window" or key.startswith("correction_incrementer.") for key in pins):
                raise ValueError("speculation controls require speculative_segments")
            window = 0
        else:
            window = int(pins.get("speculation_window", 4))
            if not 1 <= window <= lower:
                raise ValueError("the whole speculation window must fit in the lower region")
        # A child with a different arithmetic contract cannot acquire an
        # exact-child proof merely by satisfying the same port list.
        if pins.get("upper_adder.family", "ripple_carry") not in (
                "ripple_carry", "manchester_carry_chain", "carry_lookahead", "parallel_prefix", "conditional_sum"):
            raise ValueError("this contract requires an exact binary upper adder")
        if pins.get("correction_incrementer.family", "prefix_and_incrementer") != "prefix_and_incrementer":
            raise ValueError("this contract requires an exact incrementer")
        return cls(width, lower, scheme, window, correction == "configurable_stages")

    def evaluate(self, a, b, cin):
        if not 0 <= a < 1 << self.width or not 0 <= b < 1 << self.width or cin not in (0, 1):
            raise ValueError("input outside the contracted ports")
        unit = 1 << self.lower_width
        au, al = divmod(a, unit)
        bu, bl = divmod(b, unit)
        exact_carry, lower_sum = divmod(al + bl + cin, unit)
        if self.scheme == "truncate_constant":
            lower_sum, predicted = unit - 1, 0
        elif self.scheme == "or_gates":
            lower_sum, predicted = al | bl, int(al >= unit // 2 and bl >= unit // 2)
        elif self.scheme == "segmented_subadders":
            predicted = 0
        else:
            discarded_unit = 1 << (self.lower_width - self.window)
            predicted = (al // discarded_unit + bl // discarded_unit) // (1 << self.window)
        carry = exact_carry if self.correction else predicted
        total = (au + bu + carry) * unit + lower_sum
        cout, result = divmod(total, 1 << self.width)
        return {"s": result, "cout": cout}
