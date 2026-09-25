"""Evaluate documented pin and geometry constraints without treating failures as exclusions."""


UNSUPPORTED_CHOICES = (
    ("integer_mac", "element_op", ("absolute_difference",), "VecDotAcc expresses products; absolute difference has no unit operation contract"),
    ("multi_term_fused_dot", "term_source", ("fp_operands",), "VecDotAcc supplies products; a sum of floating operands has no unit operation contract"),
    ("fused_two_term_dot", "second_op", ("add_subtract_pair", "both"), "VecDotAcc supplies dot2; an add/subtract pair requires a control absent from the unit"),
)


FUSED_FMA_FAMILIES = ("classic_fma", "reduced_latency_fma", "multipath_fma", "bridge_fma")


_ALGORITHM_LEVEL: dict = {}


def _algorithm_level_families() -> frozenset:
    """The families under the fp_fma slot's space, at any depth, that
    change the computed function (the truncated, logarithmic and
    approximate-compressor multipliers, the approximate adders), which an
    exact slot drops (modules.alu.exact_only)."""
    if "fp_fma" not in _ALGORITHM_LEVEL:
        from chialu.spaces.fp_spaces import fp_fma_space
        names = set()

        def walk(space, depth=0):
            if depth > 8:
                return
            for f in space.families:
                if f.algorithm_level:
                    names.add(f.name)
                for sub in f.components.values():
                    walk(sub, depth + 1)
        walk(fp_fma_space(16))
        _ALGORITHM_LEVEL["fp_fma"] = frozenset(names)
    return _ALGORITHM_LEVEL["fp_fma"]


def own_reason(family, pins, width=None, kind=None):
    for selected_family, pin, values, explanation in UNSUPPORTED_CHOICES:
        if family == selected_family and pins.get(pin) in values:
            return f"unsupported {family}.{pin}={pins[pin]!r}: {explanation}"
    if kind == "fp_fma" and family in FUSED_FMA_FAMILIES:
        approximate = _algorithm_level_families()
        for key, value in pins.items():
            if key.endswith(".family") and value in approximate:
                return (f"fp_spaces.fp_fma_space: the ALU's exact fp_fma slot drops the algorithm-level family "
                        f"{value} at {key} (modules.alu.exact_only); it changes the computed function")
    if kind == "fp_fma" and family == "reduced_latency_fma" and pins.get("rounding_position") == "fused_with_cpa_dual_sum" \
            and pins.get("sharing") == "shared_across_formats":
        return ("fp_spaces.fp_fma_space: reduced_latency_fma.rounding_position fused_with_cpa_dual_sum rounds for the "
                "mode's format inside the window adder; one datapath shared across formats has no one format to "
                "round for, so the fused rounding takes sharing dedicated_per_mode")
    if kind == "fp_fma" and family == "bridge_fma" and pins.get("composition_style") == "cascade_mul_then_add":
        return ("fp_spaces.fp_fma_space: bridge_fma.composition_style cascade_mul_then_add rounds the product before "
                "the add under its own fixed cascade_product_rounding, which is neither the one rounding the mode's "
                "fadd, fsub and fmul promise nor the mode's rounding that fma_contract sequential rounds the product "
                "under (chialu.behavior_rules removes the member from the ALU's slot)")
    if kind == "fp_fma" and family in FUSED_FMA_FAMILIES and width is not None \
            and pins.get("multiplier.family") == "recursive_karatsuba":
        # the significand multiplier's width is the float format's significand (the fp kinds' width names the
        # format, characterize.FP_FORMATS); the karatsuba split needs 4 bits, its three-way split 5
        from chialu.characterize import FP_FORMATS
        from chialu.verify.formats import parse_format
        if width in FP_FORMATS:
            sw = parse_format(FP_FORMATS[width]).man_bits + 1
            need = 5 if pins.get("multiplier.split_kind") == "three_way" else 4
            if sw < need:
                return (f"mul_spaces: recursive_karatsuba needs {need} bits for its "
                        f"{pins.get('multiplier.split_kind', 'two_way')} split; the {FP_FORMATS[width]} significand "
                        f"multiplier has {sw}")
    if family == "approximate_truncated":
        lower = pins.get("lower_part_width", 4)
        if width is not None and not 1 <= lower < width:
            return "approximate_truncated requires both an actual lower region and an upper region"
        if pins.get("lower_scheme", "truncate_constant") == "speculative_segments" and \
                not 1 <= pins.get("speculation_window", 4) <= lower:
            return "approximate_truncated: the whole speculation window must fit in the lower region"
    if family == "parallel_prefix" and pins.get("valency", 2) > 2 and pins.get("topology", "sklansky") not in (
            "sklansky", "kogge_stone", "brent_kung"):
        return "adder_spaces._parallel_prefix: valency above 2 requires sklansky, kogge_stone or brent_kung"
    if family == "sparse_prefix_hybrid" and pins.get("valency", 2) > 2 and pins.get("tree_topology", "sklansky") not in (
            "sklansky", "kogge_stone"):
        return "adder_spaces.cpa_space: sparse prefix valency above 2 requires sklansky or kogge_stone"
    if family == "butterfly_network" and width is not None and width & (width - 1):
        return "shifter_spaces: butterfly_network requires a power-of-two width"
    if family == "end_around_carry" and pins.get("modulus") == "generic_p_correction" and width is not None:
        if not 1 < pins.get("modulus_value", (1 << width) - 1) < 1 << width:
            return "adder_spaces.cpa_space: generic modulus p must be below 2**W"
    return None


def unsupported_report(width=16):
    """Preserve excluded domains even after they leave the current public product."""
    from chialu.spaces.fma_dot_spaces import UNSUPPORTED_DOT_CHOICES
    from chialu.spaces.sfu_spaces import UNSUPPORTED_SFU_CHOICES
    from chialu.variant_contracts import family_schemas
    records = []
    exclusions = [("dot", path, exclusion) for path, exclusion in UNSUPPORTED_DOT_CHOICES.items()]
    exclusions += [("sfu", f"{family}.{pin}", {"values": [value], "reason": reason})
                   for family, fields in UNSUPPORTED_SFU_CHOICES.items()
                   for pin, values in fields.items() for value, reason in values.items()]
    for kind, path, exclusion in exclusions:
        family, pin = path.split(".", 1)
        for product in family_schemas(kind, family, width):
            axis = next((axis for axis in product.axes if axis.name == pin), None)
            values = exclusion.get("values")
            if values is None:
                lo, hi, step = exclusion["range"]
                values = range(lo, hi + 1, step)
            present = [value for value in values if axis is not None and axis.domain.contains(value)]
            records.append({"kind": kind, "schema": product.fingerprint, "family": family, "pin": pin,
                            "removed_domain": {key: value for key, value in exclusion.items() if key != "reason"},
                            "reason": exclusion["reason"], "declared_combinations": str(product.count),
                            "excluded_in_current_product": str(product.count // axis.count * len(present)) if axis else "0",
                            "removed_from_current_product": not present})
    return {"scope": "excluded operation and sequential domains", "width": width,
            "choices": records}


def reason(family, pins, width=None, kind=None):
    """Check root geometry and all geometry-independent nested constraints;
    `kind` is the structure kind the root family serves, for a rule that
    holds in one kind's slot alone."""
    invalid = own_reason(family, pins, width, kind)
    if invalid:
        return invalid
    for key, child in pins.items():
        if key.endswith(".family"):
            prefix = key[:-len("family")]
            child_pins = {k[len(prefix):]: v for k, v in pins.items() if k.startswith(prefix)}
            invalid = own_reason(child, child_pins)
            if invalid:
                return f"{prefix}{invalid}"
    return None


if __name__ == "__main__":
    import argparse
    import json
    from pathlib import Path
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--width", type=int, default=16)
    parser.add_argument("--out")
    args = parser.parse_args()
    report = json.dumps(unsupported_report(args.width), indent=2) + "\n"
    if args.out:
        Path(args.out).write_text(report)
    print(report, end="")
