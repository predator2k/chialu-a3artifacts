"""Numerical error model and budget verdicts.

compare() scores one (expected, got) pair over a format; ErrorReport
aggregates the approximate-computing metrics the ADIR vocabulary names
(ArithmeticError.{max_ulp, max_abs, error_rate, med, nmed, mred,
error_bias}); Budget turns a module's constraint list into a verdict
over a report.

Frozen metric definitions (over the DECODED values; specials compare
for identity, and any special mismatch counts as wrong with no
distance contribution):
  error_rate  wrong pairs / total pairs (bitwise inequality)
  max_ulp     max |index(got) - index(exp)| (format-ordered distance)
  max_abs     max |got - exp|  (WCE)
  med         mean |got - exp|
  nmed        med / max representable magnitude of the output format
  mred        mean of |got - exp| / max(|exp|, 1 ulp at exp)
  error_bias  mean (got - exp), sign-preserving

An integer output in two's complement or unsigned encoding (a fixed-point
one included) wraps modulo 2^w, so its distance is the shorter way round
that ring: an approximate adder that drops a carry into bit 4 of a
16-bit sum is 16 away from the exact result whether or not the exact
sum wrapped past the sign. Sign-magnitude and ones'-complement outputs,
floats, posits and decimals keep the plain value distance.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction

from chialu.verify.formats import Special


@dataclass
class PairScore:
    exact: bool
    ulp: int = 0
    abs_err: Fraction = Fraction(0)
    rel_err: Fraction = Fraction(0)
    signed_err: Fraction = Fraction(0)
    special_mismatch: bool = False


def compare(fmt, exp_bits, got_bits) -> PairScore:
    if exp_bits == got_bits:
        return PairScore(exact=True)
    try:
        ev, gv = fmt.decode(exp_bits), fmt.decode(got_bits)
    except ValueError:
        # undecodable pattern (e.g. invalid BCD digit) = wrong output
        return PairScore(exact=False, special_mismatch=True)
    if isinstance(ev, list) or isinstance(gv, list):
        # a block pattern: element lists compare whole (no distance)
        return PairScore(exact=(ev == gv), special_mismatch=(ev != gv))
    if isinstance(ev, Special) or isinstance(gv, Special):
        # NaN-vs-NaN with different payloads is still a match
        if isinstance(ev, Special) and isinstance(gv, Special) \
           and ev.name == gv.name:
            return PairScore(exact=True)
        return PairScore(exact=False, special_mismatch=True)
    d = gv - ev
    ulp = abs(fmt.index(got_bits) - fmt.index(exp_bits))
    if ring_modulus(fmt) is not None:
        n = 1 << fmt.width
        ulp = min(ulp, n - ulp)
        m = ring_modulus(fmt)
        d = (d + m / 2) % m - m / 2
    denom = max(abs(ev), fmt.ulp_at(exp_bits))
    return PairScore(exact=False, ulp=ulp, abs_err=abs(d),
                     rel_err=abs(d) / denom, signed_err=d)


def ring_modulus(fmt):
    """The value modulus of a wrapping integer output (2^w scaled by the
    format's ulp), or None for a format whose distance is the plain
    value difference."""
    from chialu.verify.formats import IntFormat
    if isinstance(fmt, IntFormat) and getattr(fmt, "encoding", None) in ("twos_complement", "unsigned"):
        return Fraction(1 << fmt.width) * Fraction(fmt.ulp_at(0))
    return None


@dataclass
class ErrorReport:
    n: int = 0
    n_wrong: int = 0
    n_special_mismatch: int = 0
    max_ulp: int = 0
    max_abs: Fraction = Fraction(0)
    _sum_abs: Fraction = Fraction(0)
    _sum_rel: Fraction = Fraction(0)
    _sum_signed: Fraction = Fraction(0)
    out_max_mag: Fraction = Fraction(1)
    worst: list = field(default_factory=list)   # (tag, exp, got) samples

    def add_values(self, exp_val, got_val, ulp, tag=""):
        """Score one decoded pair (Fraction | Special) with the given ulp
        (block elements, whose spacing depends on the scale)."""
        if isinstance(exp_val, Special) or isinstance(got_val, Special):
            same = (isinstance(exp_val, Special) and isinstance(got_val, Special)
                    and exp_val.name == got_val.name)
            s = PairScore(exact=same, special_mismatch=not same)
        elif exp_val == got_val:
            s = PairScore(exact=True)
        else:
            d = got_val - exp_val
            s = PairScore(exact=False, ulp=int(abs(d) / ulp) if ulp else 0,
                          abs_err=abs(d), rel_err=abs(d) / max(abs(exp_val), ulp),
                          signed_err=d)
        return self._record(s, exp_val, got_val, tag)

    def add(self, fmt, exp_bits, got_bits, tag=""):
        s = compare(fmt, exp_bits, got_bits)
        return self._record(s, exp_bits, got_bits, tag)

    def _record(self, s, exp_bits, got_bits, tag=""):
        self.n += 1
        if not s.exact:
            self.n_wrong += 1
            if s.special_mismatch:
                self.n_special_mismatch += 1
            else:
                self.max_ulp = max(self.max_ulp, s.ulp)
                self.max_abs = max(self.max_abs, s.abs_err)
                self._sum_abs += s.abs_err
                self._sum_rel += s.rel_err
                self._sum_signed += s.signed_err
            if len(self.worst) < 16:
                self.worst.append((tag, exp_bits, got_bits))
        return s

    # -- metric views (ADIR ArithmeticError names) --
    @property
    def bit_exact(self):
        return self.n_wrong == 0

    @property
    def error_rate(self):
        return Fraction(self.n_wrong, self.n) if self.n else Fraction(0)

    @property
    def med(self):
        return self._sum_abs / self.n if self.n else Fraction(0)

    @property
    def nmed(self):
        return self.med / self.out_max_mag if self.out_max_mag else self.med

    @property
    def mred(self):
        return self._sum_rel / self.n if self.n else Fraction(0)

    @property
    def error_bias(self):
        return self._sum_signed / self.n if self.n else Fraction(0)

    def metric(self, name):
        return {"bit_exact": self.bit_exact, "max_ulp": self.max_ulp,
                "max_abs": self.max_abs, "error_rate": self.error_rate,
                "med": self.med, "nmed": self.nmed, "mred": self.mred,
                "error_bias": self.error_bias}[name]

    def summary(self):
        def f(x):
            return float(x) if isinstance(x, Fraction) else x
        return {k: f(self.metric(k)) for k in
                ("bit_exact", "max_ulp", "max_abs", "error_rate", "med",
                 "nmed", "mred", "error_bias")} | {
                "n": self.n, "n_wrong": self.n_wrong,
                "n_special_mismatch": self.n_special_mismatch}


class Budget:
    """Verdicts from ADIR constraints over Functionality/ArithmeticError.

    Constraints on other objectives (synthesizable, area...) are outside
    this layer and ignored here.
    """

    def __init__(self, bounds):
        self.bounds = bounds        # list[(metric_name, op, bound)]

    @classmethod
    def from_constraints(cls, constraints):
        bounds = []
        for c in constraints or []:
            obj = c.metric.objective
            if obj == "Functionality" and c.metric.name == "bit_exact":
                bounds.append(("bit_exact", "==", True))
            elif obj == "ArithmeticError":
                bounds.append((c.metric.name, c.op, c.bound))
        return cls(bounds)

    @classmethod
    def exact(cls):
        return cls([("bit_exact", "==", True)])

    def verdict(self, report: ErrorReport):
        violations = []
        distances = {"max_ulp", "max_abs", "med", "nmed", "mred", "error_bias"}
        if report.n_special_mismatch and any(name in distances for name, _, _ in self.bounds):
            violations.append(f"{report.n_special_mismatch} special-value mismatches have no finite numerical error bound")
        for name, op, bound in self.bounds:
            v = report.metric(name)
            ok = {"<=": lambda: v <= bound, ">=": lambda: v >= bound,
                  "==": lambda: v == bound}[op]()
            if not ok:
                fv = float(v) if isinstance(v, Fraction) else v
                violations.append(f"ArithmeticError.{name} {op} {bound}: "
                                  f"measured {fv}")
        return (not violations), violations
