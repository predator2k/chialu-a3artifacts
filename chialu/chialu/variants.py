"""Index complete family pin products without sampling or materializing the product."""
from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
import hashlib
import json
from math import prod

from adir import Range


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class Axis:
    name: str
    domain: object

    @property
    def count(self):
        if isinstance(self.domain, Range):
            if self.domain.is_int:
                return (self.domain.hi - self.domain.lo) // self.domain.step + 1
            return self.domain.count()
        if not self.domain.finite():
            raise ValueError(f"{self.name}: the domain is not enumerable")
        return len(self.domain.members())

    def at(self, ordinal):
        if not 0 <= ordinal < self.count:
            raise IndexError(ordinal)
        if isinstance(self.domain, Range):
            return self.domain.lo + ordinal * self.domain.step if self.domain.is_int else self.domain._at(ordinal)
        return self.domain.members()[ordinal]

    def rank(self, value):
        if isinstance(self.domain, Range) and self.domain.is_int:
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"{self.name}: an integer is required")
            ordinal, remainder = divmod(value - self.domain.lo, self.domain.step)
            if remainder or not 0 <= ordinal < self.count:
                raise ValueError(f"{self.name}={value!r} is outside {self.domain.describe()}")
            return ordinal
        if not self.domain.contains(value):
            raise ValueError(f"{self.name}={value!r} is outside {self.domain.describe()}")
        if isinstance(self.domain, Range):
            return int(round((value - self.domain.lo) / self.domain.step))
        return self.domain.members().index(value)


@dataclass(frozen=True)
class Slot:
    name: str
    families: tuple

    @cached_property
    def count(self):
        return sum(f.count for f in self.families)

    def at(self, ordinal):
        if not 0 <= ordinal < self.count:
            raise IndexError(ordinal)
        for family in self.families:
            if ordinal < family.count:
                return family, family.at(ordinal)
            ordinal -= family.count
        raise AssertionError("slot ordinal exceeds its count")

    def rank(self, family_name, pins):
        offset = 0
        for family in self.families:
            if family.name == family_name:
                return offset + family.rank(pins)
            offset += family.count
        raise ValueError(f"{self.name}: unknown family {family_name!r}")


@dataclass(frozen=True)
class FamilyProduct:
    """Represent a family's own choices and the complete products of its slots."""
    name: str
    axes: tuple[Axis, ...]
    slots: tuple[Slot, ...]

    @cached_property
    def count(self):
        return prod(a.count for a in self.axes) * prod(s.count for s in self.slots)

    @cached_property
    def fingerprint(self):
        description = {"family": self.name, "axes": [(a.name, a.domain.to_json()) for a in self.axes],
                       "slots": [(s.name, [f.fingerprint for f in s.families]) for s in self.slots]}
        return hashlib.sha256(canonical(description).encode()).hexdigest()

    def at(self, ordinal):
        """Return the complete binding at a mixed-radix ordinal."""
        if not 0 <= ordinal < self.count:
            raise IndexError(ordinal)
        dimensions = self.axes + self.slots
        indices = [0] * len(dimensions)
        for i in reversed(range(len(dimensions))):
            ordinal, indices[i] = divmod(ordinal, dimensions[i].count)
        pins = {}
        for dimension, index in zip(dimensions, indices):
            if isinstance(dimension, Axis):
                pins[dimension.name] = dimension.at(index)
            else:
                family, children = dimension.at(index)
                pins[dimension.name + ".family"] = family.name
                pins.update({dimension.name + "." + key: value for key, value in children.items()})
        return pins

    def rank(self, pins):
        """Validate a complete binding and return its unique ordinal."""
        remaining = dict(pins)
        ordinal = 0
        for axis in self.axes:
            if axis.name not in remaining:
                raise ValueError(f"{self.name}: missing {axis.name}")
            ordinal = ordinal * axis.count + axis.rank(remaining.pop(axis.name))
        for slot in self.slots:
            key = slot.name + ".family"
            if key not in remaining:
                raise ValueError(f"{self.name}: missing {key}")
            family = remaining.pop(key)
            prefix = slot.name + "."
            child = {k[len(prefix):]: remaining.pop(k) for k in list(remaining) if k.startswith(prefix)}
            ordinal = ordinal * slot.count + slot.rank(family, child)
        if remaining:
            raise ValueError(f"{self.name}: unknown or inactive pins {sorted(remaining)}")
        return ordinal

    def complete(self, overrides):
        """Fill omitted choices from their domains and reject unknown or inactive pins."""
        remaining = dict(overrides)
        pins = {a.name: remaining.pop(a.name, a.at(0)) for a in self.axes}
        for slot in self.slots:
            key = slot.name + ".family"
            name = remaining.pop(key, slot.families[0].name)
            family = next((f for f in slot.families if f.name == name), None)
            if family is None:
                raise ValueError(f"{self.name}: {key}={name!r} is not in the slot")
            prefix = slot.name + "."
            supplied = {k[len(prefix):]: remaining.pop(k) for k in list(remaining) if k.startswith(prefix)}
            pins[key] = name
            pins.update({prefix + k: v for k, v in family.complete(supplied).items()})
        if remaining:
            raise ValueError(f"{self.name}: unknown or inactive pins {sorted(remaining)}")
        self.rank(pins)
        return pins

    @cached_property
    def own_count(self):
        return prod(a.count for a in self.axes)

    def own_at(self, ordinal):
        return FamilyProduct(self.name, self.axes, ()).at(ordinal)

    def ordinals(self, start=0, stop=None, shard=0, shards=1):
        """Iterate a complete shard by arithmetic progression, with no scan of other shards."""
        stop = self.count if stop is None else min(stop, self.count)
        if start < 0 or stop < start or shards < 1 or not 0 <= shard < shards:
            raise ValueError("invalid ordinal interval or shard")
        ordinal = start + (shard - start) % shards
        while ordinal < stop:
            yield ordinal
            ordinal += shards


def compile_family(family, cache=None, ancestors=()):
    """Compile a finite family tree; a cycle is an error rather than a depth cutoff."""
    cache = {} if cache is None else cache
    if id(family) in ancestors:
        raise ValueError(f"recursive family {family.name} has no finite complete pin product")
    if id(family) not in cache:
        path = ancestors + (id(family),)
        axes = tuple(Axis(name, domain) for name, domain in family.design_choices.items())
        if any(a.count < 1 for a in axes):
            raise ValueError(f"{family.name}: an empty choice domain cannot be covered")
        for name, space in family.components.items():
            if space.forbidden:
                raise ValueError(f"{family.name}.{name}: forbidden predicates need an explicit legality evaluator")
            if not space.families:
                raise ValueError(f"{family.name}.{name}: an empty slot cannot be covered")
            if len({f.name for f in space.families}) != len(space.families):
                raise ValueError(f"{family.name}.{name}: duplicate family names make bindings ambiguous")
        slots = tuple(Slot(name, tuple(compile_family(f, cache, path) for f in space.families))
                      for name, space in family.components.items())
        cache[id(family)] = FamilyProduct(family.name, axes, slots)
    return cache[id(family)]


@dataclass(frozen=True)
class Entry:
    kind: str
    product: FamilyProduct
    opener: str

    @property
    def id(self):
        return f"{self.kind}/{self.product.name}/{self.product.fingerprint}"


def root_spaces(width=16):
    """Open the unit-template spaces without discarding schemas that share family names."""
    from collections import defaultdict
    from chialu.modules.alu import core_families, core_slots
    from chialu.verify.alu_ref import OPS, op_class
    from chialu.verify.formats import parse_format
    from chialu.spaces.checker_spaces import checker_space
    from chialu.spaces.fma_dot_spaces import dot_acc_space
    from chialu.spaces.sfu_spaces import sfu_approx_space
    operations = list(OPS) + ["cvt(fp32)"]
    classes = {op_class(op) for op in operations}
    modes = lambda *formats: [(f"m{i}", parse_format(fmt)) for i, fmt in enumerate(formats)]
    configurations = [
        ("int", modes(f"int{width}"), {"int"}, False, False),
        ("approx", modes(f"int{width}"), {"int"}, True, False),
        ("bcd", modes(f"int{width}"), {"int"}, False, True),
        ("float", modes("fp16"), {"float"}, False, False),
        ("posit", modes("posit16_1"), {"posit"}, False, False),
        ("block", modes("blksfp8e4m3efp4e2m1s16"), {"block"}, False, False),
        ("multi", modes(f"int{width}", f"int{max(1, width//2)}"), {"int"}, False, False),
    ]
    out = defaultdict(list)
    for label, mode_list, format_families, approximate, decimal in configurations:
        slots = core_slots(mode_list, operations, classes, format_families, approximate, decimal, width)
        for kind, space in slots.items():
            out[kind].append((space, f"chialu.ALU ({label})"))
        for core in core_families(slots):
            for kind, space in core.components.items():
                if kind not in slots:
                    out[kind].append((space, f"chialu.ALU core.family={core.name}"))
    out["dot"].append((dot_acc_space(width), "chialu.VecDotAcc core"))
    out["sfu"].append((sfu_approx_space(True), "chialu.VecSFU core"))
    out["checker"].append((checker_space(), "checker.family of a checked unit"))
    return out


def catalog(kinds=None, families=None, width=16):
    """Keep every distinct root schema, including definitions that share a family name."""
    seen, cache = set(), {}
    spaces_by_kind = root_spaces(width)
    for kind, spaces in spaces_by_kind.items():
        if kinds and kind not in kinds:
            continue
        for space, opener in spaces:
            if space.forbidden:
                raise ValueError(f"{kind}: forbidden predicates need an explicit legality evaluator")
            for family in space.families:
                if families and family.name not in families:
                    continue
                product = compile_family(family, cache)
                entry = Entry(kind, product, opener)
                if entry.id not in seen:
                    seen.add(entry.id)
                    yield entry


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kinds")
    ap.add_argument("--families")
    ap.add_argument("--ordinal", type=int)
    ap.add_argument("--width", type=int, default=16)
    ap.add_argument("--json")
    args = ap.parse_args(argv)
    entries = list(catalog(args.kinds.split(",") if args.kinds else None,
                           args.families.split(",") if args.families else None, args.width))
    records = []
    for entry in entries:
        record = {"id": entry.id, "kind": entry.kind, "family": entry.product.name,
                  "schema_hash": entry.product.fingerprint, "raw_combinations": str(entry.product.count),
                  "opener": entry.opener}
        if args.ordinal is not None:
            record["pins"] = entry.product.at(args.ordinal)
        records.append(record)
        print(canonical(record), flush=True)
    if args.json:
        from pathlib import Path
        Path(args.json).write_text(json.dumps({"scope": "complete declared pin products before semantic legality checks",
                                             "entries": records, "raw_combinations": str(sum(e.product.count for e in entries))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
