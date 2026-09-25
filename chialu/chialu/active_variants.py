"""Index conditional active pin products before geometry and semantic legality checks."""
from dataclasses import dataclass
from functools import cached_property
import hashlib
from itertools import product as cartesian
from math import prod

from chialu.variant_contracts import active_binding, inactive_parameters
from chialu.variants import FamilyProduct, canonical


class Reads(dict):
    def __init__(self, values):
        super().__init__(values)
        self.reads = set()

    def get(self, key, default=None):
        self.reads.add(key)
        return super().get(key, default)

    def __getitem__(self, key):
        self.reads.add(key)
        return super().__getitem__(key)

    def __iter__(self):
        return super().__iter__()

    def items(self):
        self.reads.update(super().keys())
        return super().items()

    def values(self):
        self.reads.update(super().keys())
        return super().values()


@dataclass(frozen=True)
class Branch:
    fixed: dict
    axes: tuple
    slots: tuple

    @property
    def own_count(self):
        return prod(axis.count for axis in self.axes)

    @property
    def count(self):
        return self.own_count * prod(slot.count for slot in self.slots)


class ActiveSlot:
    def __init__(self, slot, cache):
        self.name = slot.name
        self.families = tuple(compile_active(family, cache) for family in slot.families)

    @cached_property
    def count(self):
        return sum(family.count for family in self.families)

    def at(self, ordinal):
        if not 0 <= ordinal < self.count:
            raise IndexError(ordinal)
        for family in self.families:
            if ordinal < family.count:
                return family, family.at(ordinal)
            ordinal -= family.count
        raise AssertionError("active slot ordinal exceeded its domain")

    def rank(self, name, pins):
        offset = 0
        for family in self.families:
            if family.name == name:
                return offset + family.rank(pins)
            offset += family.count
        raise ValueError(f"{self.name}: unknown family {name!r}")


class ActiveProduct:
    def __init__(self, raw, cache):
        self.raw = raw
        self.name = raw.name
        self.axes = raw.axes
        self.slots = tuple(ActiveSlot(slot, cache) for slot in raw.slots)

    @cached_property
    def branches(self):
        defaults = {axis.name: axis.at(0) for axis in self.axes}
        controls = set()
        while True:
            observed = set(controls)
            selected = [axis for axis in self.axes if axis.name in controls]
            if prod(axis.count for axis in selected) > 1_000_000:
                raise ValueError(f"{self.name}: activity depends on a large value domain; an explicit interval partition is required")
            cases = []
            for indices in cartesian(*(range(axis.count) for axis in selected)):
                fixed = {axis.name: axis.at(index) for axis, index in zip(selected, indices)}
                values = Reads({**defaults, **fixed})
                inactive = inactive_parameters(self.name, values)
                observed.update(values.reads & defaults.keys())
                cases.append((fixed, inactive))
            if observed == controls:
                break
            controls = observed
        branches = {}
        for fixed, inactive in cases:
            nested = [key for key in inactive if "." in key]
            if nested:
                raise ValueError(f"{self.name}: nested activity must be described on its local family: {nested}")
            kept = {key: value for key, value in fixed.items() if key not in inactive}
            axes = tuple(axis for axis in self.axes if axis.name not in controls and axis.name not in inactive)
            slots = tuple(slot for slot in self.slots if slot.name not in inactive)
            key = canonical([kept, [axis.name for axis in axes], [slot.name for slot in slots]])
            branches[key] = Branch(kept, axes, slots)
        return tuple(branches.values())

    @cached_property
    def count(self):
        return sum(branch.count for branch in self.branches)

    @cached_property
    def own_count(self):
        return sum(branch.own_count for branch in self.branches)

    @cached_property
    def fingerprint(self):
        shape = [self.raw.fingerprint, "conditional-active-v1",
                 [[branch.fixed, [axis.name for axis in branch.axes], [slot.name for slot in branch.slots]]
                  for branch in self.branches],
                 [[slot.name, [family.fingerprint for family in slot.families]] for slot in self.slots]]
        return hashlib.sha256(canonical(shape).encode()).hexdigest()

    def at(self, ordinal):
        if not 0 <= ordinal < self.count:
            raise IndexError(ordinal)
        for branch in self.branches:
            if ordinal < branch.count:
                break
            ordinal -= branch.count
        dimensions = branch.axes + branch.slots
        indices = [0] * len(dimensions)
        for index in reversed(range(len(dimensions))):
            ordinal, indices[index] = divmod(ordinal, dimensions[index].count)
        pins = dict(branch.fixed)
        for dimension, index in zip(dimensions, indices):
            if isinstance(dimension, ActiveSlot):
                family, child = dimension.at(index)
                pins[dimension.name + ".family"] = family.name
                pins.update({dimension.name + "." + key: value for key, value in child.items()})
            else:
                pins[dimension.name] = dimension.at(index)
        canonical_pins = active_binding(self.raw, pins)
        if canonical_pins != pins:
            raise ValueError(f"{self.name}: activity rule changes its own controller; projection is not canonical")
        return pins

    def rank(self, pins):
        for axis in self.axes:
            if axis.name in pins:
                axis.rank(pins[axis.name])
        offset = 0
        failures = []
        for branch in self.branches:
            if any(pins.get(key) != value for key, value in branch.fixed.items()):
                offset += branch.count
                continue
            remaining = dict(pins)
            for key in branch.fixed:
                remaining.pop(key)
            ordinal = 0
            try:
                for axis in branch.axes:
                    ordinal = ordinal * axis.count + axis.rank(remaining.pop(axis.name))
                for slot in branch.slots:
                    name = remaining.pop(slot.name + ".family")
                    prefix = slot.name + "."
                    child = {key[len(prefix):]: remaining.pop(key) for key in list(remaining) if key.startswith(prefix)}
                    ordinal = ordinal * slot.count + slot.rank(name, child)
                if remaining:
                    raise ValueError(f"unknown or inactive pins: {sorted(remaining)}")
                return offset + ordinal
            except (KeyError, ValueError) as error:
                failures.append(str(error))
            offset += branch.count
        raise ValueError(f"{self.name}: not a complete active binding; " + "; ".join(dict.fromkeys(failures)))

    def complete(self, pins=None):
        result = active_binding(self.raw, pins)
        self.rank(result)
        return result

    ordinals = FamilyProduct.ordinals


def compile_active(raw, cache=None):
    cache = {} if cache is None else cache
    key = raw.fingerprint
    if key not in cache:
        cache[key] = ActiveProduct(raw, cache)
    return cache[key]


def catalog(kinds=None, families=None, width=16):
    """Keep each declared schema while removing only its inactive axes."""
    from chialu.variants import Entry, catalog as raw_catalog
    cache = {}
    for entry in raw_catalog(kinds, families, width):
        yield Entry(entry.kind, compile_active(entry.product, cache), entry.opener)


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kinds")
    ap.add_argument("--families")
    ap.add_argument("--width", type=int, default=16)
    ap.add_argument("--ordinal", type=int)
    args = ap.parse_args(argv)
    if args.width < 1:
        ap.error("--width must be positive")
    entries = list(catalog(args.kinds.split(",") if args.kinds else None,
                           args.families.split(",") if args.families else None, args.width))
    if not entries:
        ap.error("the requested scope contains no family schemas")
    for raw, available in ((args.kinds, {entry.kind for entry in entries}),
                           (args.families, {entry.product.name for entry in entries})):
        if raw and set(raw.split(",")) - available:
            ap.error(f"requested names are absent: {sorted(set(raw.split(',')) - available)}")
    for entry in entries:
        product = entry.product
        result = {"entry": entry.id, "kind": entry.kind, "family": product.name,
                  "raw_count": str(product.raw.count), "active_count": str(product.count),
                  "scope": "conditional active bindings before semantic and geometry legality"}
        if args.ordinal is not None:
            if not 0 <= args.ordinal < product.count:
                ap.error(f"{entry.kind}/{product.name}: ordinal is outside 0..{product.count-1}")
            result.update(ordinal=str(args.ordinal), pins=product.at(args.ordinal))
        print(canonical(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
