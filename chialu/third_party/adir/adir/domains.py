"""Variable domains (design section 3.1): bool, a numeric range on a
grid, an enum of library objects, subsets of an enum, and a validated
record. A domain answers membership, narrowing (`search: [...]`,
`search: {min, max, step}`), enumeration where finite, a JSON form for
`space.json`, and sampling for a numeric backend."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any, Callable, Optional

from .errors import BindError

_EPS = 1e-9


class Domain:
    kind = ""

    def contains(self, v) -> bool:
        raise NotImplementedError

    def finite(self) -> bool:
        return False

    def members(self) -> list:
        raise BindError("", f"{self.describe()} is not finite")

    def describe(self) -> str:
        return self.kind

    def to_json(self) -> dict:
        raise NotImplementedError

    def sample(self, rng: random.Random):
        return rng.choice(self.members())

    def default(self):
        """The member an undeclared active variable takes: the first
        member of a finite domain, the low end of a range."""
        if self.finite():
            return self.members()[0]
        lo = getattr(self, "lo", None)
        return lo

    def exclusion_reason(self, v):
        """Why a value the domain once held is excluded, or None: the
        domain library's checks remove a member with a reason, which the
        loader and the declaration check report beside `outside`."""
        return None

    def outside_detail(self, values) -> str:
        """`: <reason>` for the excluded values among `values`, or ''."""
        whys = [f"{v!r}: {w}" for v in values for w in [self.exclusion_reason(v)] if w]
        return ": " + "; ".join(whys) if whys else ""

    def narrow(self, spec, path: str = "") -> "Domain":
        """The narrowed domain of a `search` binding: `all`, a list of
        members, or `{min, max, step}` inside a range."""
        if spec is None or spec == "all":
            return self
        if isinstance(spec, (list, tuple)):
            if not spec:
                raise BindError(path, "search: an empty domain")
            bad = [v for v in spec if not self.contains(v)]
            if bad:
                raise BindError(path, f"search: {bad!r} outside {self.describe()}{self.outside_detail(bad)}")
            return Enum(tuple(spec))
        if isinstance(spec, dict) and isinstance(self, Range) \
                and set(spec) <= {"min", "max", "step"}:
            lo = spec.get("min", self.lo)
            hi = spec.get("max", self.hi)
            step = spec.get("step", self.step)
            sub = Range(lo, hi, step)
            if lo < self.lo - _EPS or hi > self.hi + _EPS:
                raise BindError(path, f"search: {sub.describe()} outside {self.describe()}")
            if not self.contains(lo):
                raise BindError(path, f"search: min {lo!r} is not on the grid of {self.describe()}")
            if step is not None and abs((step / self.step) - round(step / self.step)) > _EPS:
                raise BindError(path, f"search: step {step!r} is not a multiple of {self.step!r}")
            return sub
        raise BindError(path, f"search: cannot narrow {self.describe()} with {spec!r}")


@dataclass(frozen=True)
class Bool(Domain):
    kind = "bool"

    def contains(self, v):
        return isinstance(v, bool)

    def finite(self):
        return True

    def members(self):
        return [False, True]

    def describe(self):
        return "bool"

    def to_json(self):
        return {"type": "categorical", "choices": [False, True]}


@dataclass(frozen=True)
class Range(Domain):
    """lo to hi by step; integers when every bound is an int."""
    lo: float
    hi: float
    step: float = 1

    def __post_init__(self):
        if self.step is None or self.step <= 0:
            raise BindError("", f"range step must be positive (got {self.step!r})")
        if self.hi < self.lo:
            raise BindError("", f"range {self.lo}..{self.hi} is empty")

    @property
    def is_int(self):
        return all(isinstance(x, int) and not isinstance(x, bool)
                   for x in (self.lo, self.hi, self.step))

    @property
    def kind(self):
        return "int_range" if self.is_int else "float_range"

    def count(self) -> int:
        return int(math.floor((self.hi - self.lo) / self.step + _EPS)) + 1

    def contains(self, v):
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            return False
        if v < self.lo - _EPS or v > self.hi + _EPS:
            return False
        k = (v - self.lo) / self.step
        return abs(k - round(k)) < 1e-6

    def finite(self):
        return self.count() <= 1_000_000

    def members(self):
        if not self.finite():
            raise BindError("", f"{self.describe()} has too many members to enumerate")
        return [self._at(i) for i in range(self.count())]

    def _at(self, i):
        v = self.lo + i * self.step
        if self.is_int:
            return int(round(v))
        return round(v, 10)

    def describe(self):
        return f"{self.lo}..{self.hi} by {self.step}"

    def to_json(self):
        return {"type": "uniform_int" if self.is_int else "uniform_float",
                "lower": self.lo, "upper": self.hi, "step": self.step}

    def sample(self, rng):
        return self._at(rng.randrange(self.count()))


@dataclass(frozen=True)
class Enum(Domain):
    """A finite set of library objects. `fields` maps a member to a
    mapping of named fields (`vars.mix.weights`), or is a callable
    member -> mapping. `excluded` holds the (member, reason) pairs a
    domain check removed from the members: they are outside the domain,
    and the reason is reported where a binding or a declaration names
    one."""
    members_: tuple
    fields: Any = None
    excluded: tuple = ()
    kind = "enum"

    def contains(self, v):
        return any(v == m for m in self.members_)

    def exclusion_reason(self, v):
        for m, why in self.excluded:
            if v == m:
                return why
        return None

    def without(self, reasons) -> "Enum":
        """The enum less the members `reasons` maps to a reason; the
        remaining members keep their order, so the default is the first
        of them."""
        gone = list(reasons.items()) if isinstance(reasons, dict) else list(reasons)
        names = [m for m, _ in gone]
        kept = tuple(m for m in self.members_ if not any(m == g for g in names))
        if not kept:
            raise BindError("", f"every member of {self.describe()} is excluded")
        return Enum(kept, self.fields, tuple(self.excluded) + tuple((m, w) for m, w in gone if self.contains(m)))

    def finite(self):
        return True

    def members(self):
        return list(self.members_)

    def describe(self):
        ms = [repr(m) for m in self.members_[:8]]
        if len(self.members_) > 8:
            ms.append("...")
        return "enum[" + ", ".join(ms) + "]"

    def to_json(self):
        return {"type": "categorical", "choices": list(self.members_)}

    def field_of(self, member, name):
        if self.fields is None:
            raise BindError("", f"{member!r} has no fields")
        rec = self.fields(member) if callable(self.fields) else self.fields.get(member)
        if rec is None or name not in rec:
            raise BindError("", f"{member!r} has no field {name!r}")
        return rec[name]


@dataclass(frozen=True)
class Set(Domain):
    """Subsets of a base domain. A `runtime` binding on a Set provisions
    base members; a `fixed` binding is one subset (a list)."""
    base: Domain
    kind = "set"

    def contains(self, v):
        return isinstance(v, (list, tuple)) and all(self.base.contains(x) for x in v)

    def describe(self):
        return f"set of {self.base.describe()}"

    def to_json(self):
        return {"type": "set", "base": self.base.to_json()}

    def narrow(self, spec, path=""):
        if spec is None or spec == "all":
            return self
        raise BindError(path, "search over a set domain is not supported; search the base")


@dataclass(frozen=True)
class Struct(Domain):
    """A record validated by a function that raises on a bad value (a
    `{count, format}` mode record); never finite."""
    validate: Callable[[Any], None]
    doc: str = "record"
    kind = "struct"

    def contains(self, v):
        try:
            self.validate(v)
        except Exception:  # noqa: BLE001
            return False
        return True

    def describe(self):
        return self.doc

    def to_json(self):
        return {"type": "struct", "doc": self.doc}


def sample_from_json(hp: dict, rng: random.Random):
    """A member of a `space.json` hyperparameter (the numeric backends)."""
    t = hp["type"]
    if t == "categorical":
        return rng.choice(hp["choices"])
    if t in ("uniform_int", "uniform_float"):
        r = Range(hp["lower"], hp["upper"], hp.get("step", 1))
        return r.sample(rng)
    raise BindError("", f"cannot sample a {t} hyperparameter")
