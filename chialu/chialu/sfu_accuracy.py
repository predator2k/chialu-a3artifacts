"""Select SFU parameter search or error reporting from the user's bindings."""
from copy import deepcopy

DEFAULT_TARGET = {"max_ulp": 1.0}


def _arithmetic_variation(space, prefix, bindings):
    """Whether unresolved component choices can change their arithmetic contract."""
    binding = bindings.get(prefix + ".family")
    known, selected = fixed_value(binding)
    candidates = [family for family in space.families if
                  (family.name == selected if known else binding is not None and binding.domain.contains(family.name))]
    if not candidates:
        return True
    for family in candidates:
        values, unresolved = {}, []
        for name in family.design_choices:
            bound = bindings.get(prefix + "." + name)
            fixed, value = fixed_value(bound)
            if fixed:
                values[name] = value
            else:
                unresolved.append(name)
                if bound is not None:
                    values[name] = bound.domain.default()
        inactive = _known_inactive(family.name, values, unresolved) if known else {}
        changes_value = family.algorithm_level or family.name == "end_around_carry"
        if changes_value and (not known or any(name not in inactive for name in unresolved)):
            return True
        for slot, child in family.components.items():
            if any(slot == key or slot.startswith(key + ".") for key in inactive):
                continue
            if _arithmetic_variation(child, prefix + "." + slot, bindings):
                return True
    return False


def _known_inactive(family, values, unresolved, functions=()):
    """Project an inactive branch only when its controlling values are fixed."""
    from chialu.active_variants import Reads
    from chialu.variant_contracts import inactive_parameters
    from chialu.targets.rtl.families.sfu import sfu_active_parameters
    reads = Reads(values)
    inactive = dict(inactive_parameters(family, reads))
    inactive.update(sfu_active_parameters(family, reads, functions))
    if reads.reads & set(unresolved):
        inactive = {}
    for selector, selected in values.items():
        if not selector.endswith(".family") or selector.count(".") != 1 or selector in unresolved:
            continue
        prefix = selector[:-len("family")]
        child = {key[len(prefix):]: value for key, value in values.items()
                 if key.startswith(prefix) and key != selector}
        pending = {key[len(prefix):] for key in unresolved if key.startswith(prefix)}
        inactive.update({prefix + key: reason for key, reason in _known_inactive(selected, child, pending).items()})
    # Function selection alone determines whether this slot is present.
    if functions and not set(functions) & {"sin", "cos"}:
        inactive.update({key: "the named functions use no trigonometric argument reducer"
                         for key in values if key.startswith("range_reducer.")})
    return inactive


def fixed_value(binding):
    if binding is None:
        return False, None
    if binding.time == "fixed":
        return True, binding.value
    if binding.time == "search":
        from chialu.variants import Axis
        try:
            axis = Axis(binding.variable.name, binding.domain)
            if axis.count == 1:
                return True, axis.at(0)
        except ValueError:
            pass
    return False, None


def from_bindings(bindings):
    """Preserve the distinction between user constraints and a trial's default values."""
    budget_fixed, budget = fixed_value(bindings.get("error_budget"))
    if budget is not None and not isinstance(budget, dict):
        raise ValueError("SFU error_budget must be one metric-to-bound mapping or null")
    specified, family = fixed_value(bindings.get("core.family"))
    specified = specified and family is not None
    fixed, unresolved, domains, values = {}, [], {}, {}
    if specified:
        tree = getattr(bindings, "tree", None)
        def visit(name, value):
            for variable in tree.children_of(name):
                if not variable.condition_holds(value):
                    continue
                binding = bindings.get(variable.name)
                known, choice = fixed_value(binding)
                pin = variable.name[len("core."):]
                if known:
                    fixed[pin] = values[pin] = choice
                    visit(variable.name, choice)
                else:
                    unresolved.append(pin)
                    if binding is not None and binding.time == "search":
                        domains[pin] = binding.domain.to_json()
                        values[pin] = binding.domain.default()
        if tree is not None:
            visit("core.family", family)
        else:
            for name, binding in bindings.items():
                if not name.startswith("core.") or name == "core.family":
                    continue
                known, choice = fixed_value(binding)
                if known:
                    fixed[name[5:]] = values[name[5:]] = choice
                else:
                    unresolved.append(name[5:])
            # A plain mapping cannot prove that omitted architecture parameters are fixed.
            unresolved.append("<unresolved family schema>")
        from chialu.modules.common import vals
        inactive = _known_inactive(family, values, unresolved, vals(bindings, "functions"))
        unresolved = [pin for pin in unresolved if not any(pin == key or pin.startswith(key + ".") for key in inactive)]
    structural = ["sharing"]
    if specified and getattr(bindings, "tree", None) is not None:
        from chialu.spaces.sfu_spaces import sfu_approx_space
        declared = sfu_approx_space().family(family)
        for slot, space in declared.components.items():
            if slot in ("adder", "multiplier", "shifter", "lzc", "address_adder", "final_adder") \
                    and not _arithmetic_variation(space, "core." + slot, bindings):
                structural.append(slot)
    accuracy_unresolved = [pin for pin in unresolved if not any(pin == key or pin.startswith(key + ".") for key in structural)]
    mode = "search_implementation" if not specified else "search_parameters" if accuracy_unresolved else "report_error"
    return {"mode": mode, "implementation_specified": bool(specified), "family": family if specified else None,
            "fixed_pins": fixed, "unresolved_parameters": sorted(unresolved),
            "unresolved_accuracy_parameters": sorted(accuracy_unresolved),
            "structural_parameters": structural,
            "parameter_domains": domains, "user_target": deepcopy(budget) if budget_fixed else None,
            "precision_target": deepcopy(budget if budget is not None else DEFAULT_TARGET),
            "target_source": "user" if budget is not None else "default",
            "budget_applied": mode != "report_error"}


def mode_of(spec):
    mode = (spec.get("sfu_accuracy") or {}).get("mode", "search_implementation")
    if mode not in ("search_implementation", "search_parameters", "report_error"):
        raise ValueError(f"unknown SFU accuracy mode {mode!r}")
    return mode


def report_fixed(spec):
    return spec.get("unit") == "vec_sfu" and mode_of(spec) == "report_error"
