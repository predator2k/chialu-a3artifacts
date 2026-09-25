"""Resolve active architecture parameters without counting inactive Cartesian axes."""
from __future__ import annotations

from functools import lru_cache


def inactive_parameters(family, pins):
    from chialu.targets.rtl.families.alu_contracts import alu_active_parameters
    from chialu.targets.rtl.families.dot import dot_active_parameters
    from chialu.targets.rtl.families import sfu
    result = dict(alu_active_parameters(family, pins))
    result.update(dot_active_parameters(family, pins))
    function = getattr(sfu, "sfu_active_parameters", None)
    if function is not None:
        result.update(function(family, pins))
    return result


def active_binding(product, supplied=None, *, project=False):
    """Fill active defaults; explicit inactive or unknown keys are errors.

    Projection is for interpreting the old raw-product index. A projected raw
    ordinal is not a distinct covered binding when its inactive values differ.
    """
    remaining = dict(supplied or {})
    own = {a.name: remaining.get(a.name, a.at(0)) for a in product.axes}
    for axis in product.axes:
        axis.rank(own[axis.name])
    inactive = inactive_parameters(product.name, {**own, **remaining})
    for key, reason in inactive.items():
        selected = [name for name in remaining if name == key or name.startswith(key + ".")]
        if selected and not project:
            raise ValueError(f"{product.name}.{key}: inactive ({reason}); explicit keys={selected}")
        for name in selected:
            remaining.pop(name)
    result = {}
    for axis in product.axes:
        if axis.name not in inactive:
            result[axis.name] = remaining.pop(axis.name, own[axis.name])
    for slot in product.slots:
        if slot.name in inactive:
            continue
        selector = slot.name + ".family"
        family_name = remaining.pop(selector, slot.families[0].name)
        family = next((f for f in slot.families if f.name == family_name), None)
        if family is None:
            raise ValueError(f"{product.name}.{selector}: unknown family {family_name!r}")
        prefix = slot.name + "."
        child = {name[len(prefix):]: remaining.pop(name) for name in list(remaining) if name.startswith(prefix)}
        result[selector] = family_name
        result.update({prefix + key: value for key, value in active_binding(family, child, project=project).items()})
    if remaining:
        raise ValueError(f"{product.name}: unknown pins {sorted(remaining)}")
    return result


def recursive_inactive_parameters(product, pins, *, functions=()):
    """Return inactive paths of an existing binding, including child families.

    This does not fill defaults or discard values. Callers can distinguish
    generated search defaults from explicit user decisions before projecting.
    """
    own = {axis.name: pins.get(axis.name, axis.at(0)) for axis in product.axes}
    values = {**own, **pins}
    result = dict(inactive_parameters(product.name, values))
    if functions:
        from chialu.targets.rtl.families.sfu import sfu_active_parameters
        result.update(sfu_active_parameters(product.name, values, functions))
    for slot in product.slots:
        if any(slot.name == key or slot.name.startswith(key + ".") for key in result):
            continue
        prefix = slot.name + "."
        selected = pins.get(prefix + "family", slot.families[0].name)
        family = next((f for f in slot.families if f.name == selected), None)
        if family is None:
            continue  # The ordinary schema validator diagnoses unknown families.
        child = {key[len(prefix):]: value for key, value in pins.items()
                 if key.startswith(prefix) and key != prefix + "family"}
        result.update({prefix + key: reason for key, reason in
                       recursive_inactive_parameters(family, child).items()})
    return result


@lru_cache(maxsize=256)
def family_schemas(kind, family, width=16):
    from chialu.variants import compile_family
    aliases = {"fp_sqrt": "fp_divider", "sd_adder": "representation", "rns_adder": "channels",
               "rns_multiplier": "channels", "rns_comparator": "channels",
               "bcd_adder": "adder", "bcd_multiplier": "multiplier", "bcd_divider": "divider"}
    kind = aliases.get(kind, kind)
    from chialu.spaces import adder_spaces as add, mul_spaces as mul, approx_spaces as approx
    from chialu.spaces import decimal_spaces as decimal, shift_simd_spaces as shift
    from chialu.spaces import fp_spaces as fp, misc_spaces as misc, div_spaces as div
    from chialu.spaces import dsp_posit_spaces as posit, redundant_spaces as redundant
    from chialu.spaces.fma_dot_spaces import dot_acc_space
    from chialu.spaces.sfu_spaces import sfu_approx_space
    factories = {
        "adder": (add.cpa_space, approx.approx_adder_space, decimal.decimal_adder_space),
        "multiplier": (lambda: mul.mul_space(width), lambda: approx.approx_mul_space(width), decimal.decimal_mul_space),
        "divider": (div.div_space, approx.approx_div_space, decimal.decimal_div_space),
        "comparator": (add.comparator_space,), "incrementer": (add.incrementer_space,),
        "bitcount": (shift.bitcount_space,), "lzc": (shift.lzc_space,), "shifter": (shift.shifter_space,),
        "rotator": (shift.rotator_space,), "subword": (shift.subword_space,), "logic": (misc.logic_space,),
        "fp_adder": (fp.fp_add_space,), "fp_multiplier": (lambda: fp.fp_mul_space(width),),
        "fp_fma": (lambda: fp.fp_fma_space(width),),
        "fp_comparator": (fp.fp_cmp_space,), "fp_divider": (fp.fp_div_space,),
        "rounder": (misc.rounder_space,), "unpacker": (misc.unpacker_space,), "converter": (fp.fp_cvt_space,),
        "posit_unit": (posit.posit_unit_space,), "representation": (redundant.signed_digit_space,),
        "channels": (redundant.rns_space,), "dot": (lambda: dot_acc_space(width),),
        "sfu": (lambda: sfu_approx_space(True),),
    }
    found = {}
    for factory in factories.get(kind, ()):
        for declared in factory().families:
            if declared.name == family:
                product = compile_family(declared)
                found[product.fingerprint] = product
    return tuple(found.values())


def validate_pins(kind, family, pins, width=16):
    schemas = family_schemas(kind, family, width)
    if not schemas:
        raise ValueError(f"{kind}/{family}: no declared family schema")
    failures = []
    for schema in schemas:
        try:
            validate_partial(schema, pins)
            return schema
        except ValueError as error:
            failures.append(str(error))
    raise ValueError("; ".join(dict.fromkeys(failures)))


def validate_partial(product, supplied):
    """Validate explicit choices without substituting schema defaults for generator defaults."""
    remaining = dict(supplied or {})
    for key, explanation in inactive_parameters(product.name, remaining).items():
        if any(name == key or name.startswith(key + ".") for name in remaining):
            raise ValueError(f"{product.name}.{key}: inactive ({explanation})")
    for axis in product.axes:
        if axis.name in remaining:
            axis.rank(remaining.pop(axis.name))
    for slot in product.slots:
        prefix = slot.name + "."
        selected = remaining.pop(prefix + "family", None)
        child = {key[len(prefix):]: remaining.pop(key) for key in list(remaining) if key.startswith(prefix)}
        if selected is None and not child:
            continue
        candidates = [family for family in slot.families if selected is None or family.name == selected]
        if not candidates:
            raise ValueError(f"{product.name}.{slot.name}: unknown family {selected!r}")
        errors = []
        for family in candidates:
            try:
                validate_partial(family, child)
                break
            except ValueError as error:
                errors.append(str(error))
        else:
            raise ValueError("; ".join(dict.fromkeys(errors)))
    if remaining:
        raise ValueError(f"{product.name}: unknown pins {sorted(remaining)}")
