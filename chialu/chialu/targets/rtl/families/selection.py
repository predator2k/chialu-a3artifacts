"""Reject explicit seed selections whose generated modules never enter the seed hierarchy."""
from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass, field
from functools import wraps
import inspect
import re
import hashlib

from . import fidelity


_trace = ContextVar("family_generation_trace", default=None)


class SelectionError(ValueError):
    pass


class SelectedPins(dict):
    def __init__(self, owner, pins):
        super().__init__(pins or {})
        self.owner = owner


def copy_pins(pins, **updates):
    copied = SelectedPins(pins.owner, pins) if isinstance(pins, SelectedPins) else dict(pins or {})
    copied.update(updates)
    return copied


def track_factory(function, fixed_family=None):
    signature = inspect.signature(function)

    @wraps(function)
    def tracked(*args, **kwargs):
        trace = _trace.get()
        arguments = signature.bind(*args, **kwargs).arguments
        family = fixed_family or arguments.get("family")
        supplied = arguments.get("pins")
        owner = getattr(supplied, "owner", None)
        pins = dict(supplied or {})
        geometry = {key: value for key, value in arguments.items()
                    if key not in ("family", "pins", "name")
                    and isinstance(value, (str, int, bool))}
        for key in ("fmt", "geom", "dg"):
            value = arguments.get(key)
            if value is not None:
                geometry[key] = {k: v for k, v in vars(value).items()
                                 if isinstance(v, (str, int, bool))} if hasattr(value, "__dict__") else str(value)
        with fidelity.location(owner or "", family or function.__name__, geometry):
            result = function(*args, **kwargs)
        if trace is None:
            return result
        if family and result is None and owner is not None and function.__name__ not in (
                "popcount_module", "lzc_module", "tzc_module"):
            trace.failed.append((owner, family, function.__name__))
        if family and result is not None:
            name = result.name if hasattr(result, "name") else result[0]
            register_origin(owner, family, pins, name, parameters=getattr(result, "params", None))
        return result

    return tracked


def register_origin(owner, family, pins, module_name, text=None, parameters=None):
    """Record a generated component before a structural sharing transform replaces it."""
    trace = _trace.get()
    if trace is not None:
        record = (owner, family, dict(pins or {}), module_name)
        if record not in trace.generated:
            trace.generated.append(record)
        if text is not None:
            trace.origin_hashes[module_name] = hashlib.sha256(text.encode()).hexdigest()
        if parameters:
            trace.parameters.append((owner, family, dict(pins or {}), module_name, dict(parameters)))


def reachable_modules(text, top):
    """Follow instantiations among emitted module definitions, excluding comments."""
    text = re.sub(r"/\*.*?\*/|//[^\n]*", "", text, flags=re.S)
    modules = dict(re.findall(r"\bmodule\s+(\w+)\b(.*?)\bendmodule\b", text, flags=re.S))
    if top not in modules:
        raise SelectionError(f"seed top {top!r} is absent")
    patterns = {name: re.compile(r"\b" + re.escape(name) + r"\s*(?:#\s*\(.*?\)\s*)?\w+\s*\(", re.S)
                for name in modules}
    reached, pending = set(), [top]
    while pending:
        name = pending.pop()
        if name in reached:
            continue
        reached.add(name)
        pending += [child for child, pattern in patterns.items() if child not in reached and pattern.search(modules[name])]
    return reached


def physical_witness_exists(text, witness, reachable):
    """Accept a reachable module or an instance path starting at a reachable module."""
    parts = witness.split(".")
    if parts[0] not in reachable:
        return False
    source = re.sub(r"/\*.*?\*/|//[^\n]*", "", text, flags=re.S)
    modules = dict(re.findall(r"\bmodule\s+(\w+)\b(.*?)\bendmodule\b", source, flags=re.S))
    parent = parts[0]
    for instance in parts[1:]:
        match = re.search(r"\b(\w+)\s*(?:#\s*\(.*?\)\s*)?" + re.escape(instance) + r"\s*\(",
                          modules.get(parent, ""), flags=re.S)
        if match is None or match[1] not in modules:
            return False
        parent = match[1]
    return True


def instantiated_parameters(text, name, reachable):
    """Read named parameter overrides on reachable instances of a static library module."""
    source = re.sub(r"/\*.*?\*/|//[^\n]*", "", text, flags=re.S)
    modules = dict(re.findall(r"\bmodule\s+(\w+)\b(.*?)\bendmodule\b", source, flags=re.S))
    pattern = re.compile(r"\b" + re.escape(name) + r"\s*(?:#\s*\((.*?)\)\s*)?\w+\s*\(", re.S)
    found = []
    for parent in reachable:
        for match in pattern.finditer(modules.get(parent, "")):
            found.append(dict(re.findall(r"\.(\w+)\s*\(\s*([^()]+?)\s*\)", match[1] or "")))
    return found


@dataclass
class SelectionTrace:
    generated: list = field(default_factory=list)
    failed: list = field(default_factory=list)
    origin_hashes: dict = field(default_factory=dict)
    parameters: list = field(default_factory=list)
    audit: fidelity.Audit = field(default_factory=fidelity.Audit)

    def __enter__(self):
        self.token = _trace.set(self)
        self.audit.__enter__()
        return self

    def __exit__(self, *error):
        self.audit.__exit__(*error)
        _trace.reset(self.token)

    def report(self):
        return dict(self.audit.report(), generated=[{"owner": owner, "family": family,
                    "pins": pins, "module": name, "source_sha256": self.origin_hashes.get(name)}
                    for owner, family, pins, name in self.generated])

    def check(self, selections, text, top):
        from chialu.targets.rtl import families as FAM
        if not FAM.LIBRARY_REALIZATION:
            # the render ran without the library (realization: behavioral): no family module was
            # instantiated, by design, so there is no origin to verify against the selections
            return
        reachable = reachable_modules(text, top)
        replacements = {}
        for witness in self.audit.sharing:
            absent = {name for name in witness["physical_modules"]
                      if not physical_witness_exists(text, name, reachable)}
            if absent:
                raise SelectionError(f"sharing {witness['scheme']}: unreachable physical modules {sorted(absent)}")
            for name in witness.get("origin_modules", ()):
                replacements.setdefault(name, set()).update(witness["consumers"])
        missing = []
        for owner, (family, supplied) in selections.items():
            pins = dict(supplied or {})
            rejected = [factory for actual_owner, actual_family, factory in self.failed
                        if actual_owner == owner and actual_family == family]
            if rejected:
                missing.append(f"{owner}: {family} was rejected by {', '.join(sorted(set(rejected)))}")
                continue
            found = [name for actual_owner, actual_family, actual_pins, name in self.generated
                     if actual_owner == owner and actual_family == family
                     and (name in reachable or owner in replacements.get(name, ()))
                     and all(key in actual_pins and actual_pins[key] == value for key, value in pins.items())]
            verified = []
            for name in found:
                requested = [parameters for actual_owner, actual_family, actual_pins, actual_name, parameters in self.parameters
                             if (actual_owner, actual_family, actual_name) == (owner, family, name)
                             and all(actual_pins.get(key) == value for key, value in pins.items())]
                actual = instantiated_parameters(text, name, reachable)
                compact = lambda value: re.sub(r"\s+", "", str(int(value) if isinstance(value, bool) else value))
                if not requested or any(all(key in instance and compact(instance[key]) == compact(value)
                                           for key, value in parameters.items())
                                        for parameters in requested for instance in actual):
                    verified.append(name)
                elif owner in replacements.get(name, ()):
                    verified.append(name)
            found = verified
            if not found:
                missing.append(f"{owner}: {family} with pins {pins!r}")
        if missing:
            raise SelectionError("explicit family was not instantiated with its requested pins: " + "; ".join(missing))


def checked_alu_seed(function):
    signature = inspect.signature(function)

    @wraps(function)
    def checked(*args, **kwargs):
        arguments = signature.bind(*args, **kwargs)
        selections = arguments.arguments.get("families")
        if not selections:
            return function(*args, **kwargs)
        if "core" in selections and selections["core"][0] not in ("unit_per_class", "redundant_internal", "rns_internal"):
            raise SelectionError(f"unknown ALU core family {selections['core'][0]!r}")
        from chialu.variant_contracts import validate_pins
        from chialu.verify.alu_ref import normalize_spec
        from chialu.verify.formats import parse_format
        spec = normalize_spec(arguments.arguments["spec"])
        width = max(parse_format(mode["format"]).width for mode in spec["modes"])
        for owner, (family, pins) in selections.items():
            if owner == "core":
                if pins:
                    raise SelectionError(f"core: {family} has no own pins; bind its component slots separately")
                required_slot = {"redundant_internal": "representation", "rns_internal": "channels"}.get(family)
                if required_slot and "core." + required_slot not in selections:
                    raise SelectionError(f"core: {family} requires an explicit {required_slot} selection")
                continue
            parts = owner.split(".")
            if len(parts) < 2 or parts[0] != "core":
                raise SelectionError(f"invalid selection owner {owner!r}")
            try:
                validate_pins(parts[1], family, pins, width)
            except ValueError as error:
                raise SelectionError(f"{owner}: {error}") from error
        arguments.arguments["families"] = {key: (family, SelectedPins(key, pins))
                                             for key, (family, pins) in selections.items()}
        with SelectionTrace() as trace:
            seed = function(*arguments.args, **arguments.kwargs)
        inline = set()
        for key, (family, pins) in selections.items():
            if family == "replicated_lanes" and key == "core.subword" and not pins and len(arguments.arguments["spec"]["modes"]) > 1:
                inline.add(key)
            if key.startswith("core.fp_fma.") and family == "separate_multiplier_and_adder":
                # the fp_adder's and the fp_multiplier's own modules realize it, under their own owners
                inline.add(key)
        required = {key: value for key, value in selections.items() if key != "core" and key not in inline}
        trace.check(required, seed.text, arguments.arguments.get("name", signature.parameters["name"].default))
        seed.fidelity = trace.report()
        return seed

    return checked


def install(namespace):
    """Record factory results only while an explicit seed selection is checked."""
    fixed = {"twin_precision_module": "twin_precision_subword", "partitioned_adder_module": "partitioned_carry_chain"}
    for name, function in list(namespace.items()):
        if name.endswith("_module") and inspect.isfunction(function) and (
                "family" in inspect.signature(function).parameters or name in fixed):
            if name == "has_module":
                continue
            namespace[name] = track_factory(function, fixed.get(name))
