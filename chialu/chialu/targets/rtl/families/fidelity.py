"""Record the effective structural choices of a generated seed."""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import asdict, dataclass, field


_audit = ContextVar("rtl_fidelity_audit", default=None)
_location = ContextVar("rtl_fidelity_location", default=("", "", {}))
_partial_binding = ContextVar("rtl_partial_component_binding", default=None)


@dataclass(frozen=True)
class Effect:
    owner: str
    family: str
    pin: str
    requested: object
    effective: object
    geometry: dict
    detail: str
    partial: bool = False


@dataclass
class Audit:
    effects: list[Effect] = field(default_factory=list)
    sharing: list[dict] = field(default_factory=list)

    def __enter__(self):
        self.parent = _audit.get()
        self.token = _audit.set(self)
        return self

    def __exit__(self, *_):
        _audit.reset(self.token)
        if self.parent is not None:
            self.parent.effects.extend(self.effects)
            self.parent.sharing.extend(self.sharing)

    def report(self):
        return {"criterion": "effective structural parameters", "effects": [asdict(e) for e in self.effects],
                "sharing": list(self.sharing)}


@contextmanager
def location(owner="", family="", geometry=None):
    previous = _location.get()
    token = _location.set((owner or previous[0], family, dict(geometry or {})))
    try:
        yield
    finally:
        _location.reset(token)


def _error(key, message):
    from chialu.targets.rtl.families.selection import SelectionError
    owner, family, geometry = _location.get()
    context = "/".join(part for part in (owner, family) if part)
    raise SelectionError(f"{context + ': ' if context else ''}{key}: {message}" +
                         (f"; geometry={geometry}" if geometry else ""))


def effective(pins, key, actual, detail="", geometry=None):
    """Require an explicit request to equal the value used to construct the circuit."""
    if pins is not None and key in pins:
        wanted = pins[key]
        binding = _partial_binding.get()
        owner, family, current_geometry = _location.get()
        partial = bool(wanted != actual and binding and family == binding["family"] == "ripple_carry"
                       and key == "chunk_width_bits" and binding["pins"].get(key) == wanted
                       and 0 < actual < wanted <= max(binding["widths"]))
        if wanted != actual and not partial:
            _error(key, f"requested {wanted!r}, constructed {actual!r}" + (f" ({detail})" if detail else ""))
        audit = _audit.get()
        if audit is not None:
            observed = dict(geometry or current_geometry)
            if binding and family == binding["family"]:
                observed.update(binding_widths=binding["widths"], slot=binding["slot"])
            audit.effects.append(Effect(getattr(pins, "owner", owner), family, key, wanted, actual,
                                        observed, detail, partial))
        if partial:
            return wanted
    return actual


@contextmanager
def component_binding(family, pins, widths, slot):
    """Permit natural ripple tails when the same slot also constructs a full chunk."""
    token = _partial_binding.set({"family": family, "pins": dict(pins), "widths": tuple(widths), "slot": slot})
    try:
        yield
    finally:
        _partial_binding.reset(token)


def inactive(pins, key, reason):
    """Reject an explicit choice that has no structure in the selected configuration."""
    if pins is not None and key in pins:
        _error(key, f"does not take effect: {reason}")


def unsupported(pins, key, reason):
    if pins is not None and key in pins:
        _error(key, f"unsupported: {reason}")


def require(condition, key, reason):
    if not condition:
        _error(key, reason)


def shared(owner, scheme, physical_modules, consumers, detail="", origin_modules=()):
    """Identify the physical modules and consumers that implement requested sharing."""
    modules, consumers = tuple(physical_modules), tuple(consumers)
    if not modules or len(set(consumers)) < 2:
        _error("sharing", "a sharing witness needs a physical module and at least two distinct consumers")
    audit = _audit.get()
    if audit is not None:
        audit.sharing.append({"owner": owner, "scheme": scheme, "physical_modules": modules,
                              "consumers": consumers, "detail": detail,
                              "origin_modules": tuple(origin_modules)})
