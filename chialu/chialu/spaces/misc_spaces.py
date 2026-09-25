"""The architecture space of the logic slot (and, or, xor, not, fabs,
fneg), an op class the seed used to keep inline in the top. A slot makes
its structures physical: groupable across lanes and modes, given a family
by the planner or the discover agent, and rewritten by a structure worker.
The converter slot reuses fp_spaces.fp_cvt_space, the comparator slots
adder_spaces.comparator_space and fp_spaces.fp_cmp_space."""
from __future__ import annotations

from adir import Bool, Enum
from adir.spaces import Family, Space


def logic_space() -> Space:
    """and / or / xor / not and the float sign ops fabs / fneg. The sign ops
    stay the lane's (a sign-bit mask on the float path), so the families
    differ in where the gate row sits: per lane, or one full-width row."""
    return Space(families=[
        Family(
            "lane_replicated_gates", behavior="neutral",
            mutations=("merge_lane_gate_rows",),
            doc="one gate row per lane and mode (the seed's shape)"),
        Family(
            "wide_gate_row", behavior="neutral",
            design_choices={"not_via_xor": Bool()},
            mutations=("fold_not_into_xor_with_ones",),
            doc="one full-width bitwise row serves every lane configuration "
                "(bitwise ops are lane-agnostic); the packed-logic ops of SIMD "
                "ISAs; not_via_xor folds the not into the xor row with ones"),
        Family(
            "alu_pg_fused", behavior="neutral",
            mutations=("take_logic_from_adder_pg",),
            doc="and = generate, xor = propagate, or = p|g taken from the "
                "adder's first stage (the 74181-style ALU); the logic class "
                "costs a few muxes on the shared adder"),
    ], free_form_allowed=True)


# the form of a float mode's X, the unrounded value between the producers and the rounder: the exact result (the
# multiplier's 2p-bit product, the adder's full window; the stochastic mode and the converters need it) or the
# guard-round-sticky form of a hardware unit's raw result (HardFloat's RawFloat, FPnew's rounding input): p + 3
# significand bits with the sticky, and an exponent of exp_bits + 3, which every producer, the comparator and the
# rounder inherit. The form is the unit option `x_form` of chialu.ALU (docs/formats-and-options.md section 3.9),
# so every rule about it depends on the YAML alone (docs/behav_checker_plan.md); it was a rounder choice before
X_FORM = Enum(("exact", "guard_round_sticky"))


def rounder_space() -> Space:
    """The rounder of a float mode: one normalize-and-round path per
    structure, or one shared per lane or across formats. The families are
    sharing patterns of one datapath (the seed wires the sharing); the
    datapath's components are the slots: the leading-zero counter and the
    shifters of the normalization and the kept-bit shift, the rounding
    family of the `round` slot (its increment, compound select, injection
    or flagged prefix), the exponent adder that lowers the exponent by the
    count and the exponent incrementer a rounding carry-out drives. The
    form of the X the rounder packs is the unit option `x_form`."""
    from chialu.spaces.adder_spaces import incrementer_space
    from chialu.spaces.arith_spaces import cpa_space, shifter_space
    from chialu.spaces.fp_spaces import rounding_space
    from chialu.spaces.shift_simd_spaces import lzc_space

    def slots():
        return {"lzc": lzc_space(), "shifter": shifter_space(), "round": rounding_space(),
                "exp_adder": cpa_space(), "exp_incrementer": incrementer_space()}

    return Space(families=[
        Family(
            "dedicated_per_op", behavior="neutral",
            components=slots(),
            mutations=("merge_rounders_of_a_lane",),
            doc="one normalize-and-round path per op class and lane (the seed's "
                "shape: every arithmetic structure packs its own result)"),
        Family(
            "shared_per_lane", behavior="neutral",
            components=slots(),
            mutations=("fold_increment_into_compound_adder",),
            doc="one normalizer and rounder per lane serves every rounding op of the "
                "lane (add, mul, div, sqrt, conversions), selected by the op; the "
                "arithmetic structures deliver unrounded results"),
        Family(
            "shared_across_formats", behavior="neutral",
            components=slots(),
            mutations=("widen_rounder_to_largest_format", "share_lzc_with_converter"),
            doc="one rounder at the widest format's precision serves every float mode "
                "and lane; the mode selects the significand and exponent widths"),
    ], free_form_allowed=True)


def unpacker_space() -> Space:
    """The operand decode of a float mode: field split, exponent bias,
    hidden bit, special-case detection (zero, denormal, inf, NaN); a
    subnormal normalized in the unpacker (denormal_handling in_unpack:
    the lzc and shifter slots) or left as stored for the datapath. The
    families are sharing patterns of one decoder (the seed wires the
    sharing)."""
    from chialu.spaces.arith_spaces import shifter_space
    from chialu.spaces.shift_simd_spaces import lzc_space

    def slots():
        return {"lzc": lzc_space(), "shifter": shifter_space()}

    return Space(families=[
        Family(
            "per_unit_unpack", behavior="neutral",
            design_choices={"denormal_handling": Enum(("in_unpack", "in_datapath"))},
            components=slots(),
            mutations=("share_unpack_across_units",),
            doc="every arithmetic structure decodes its own operands (the seed's "
                "shape); the copies are identical logic on identical inputs"),
        Family(
            "shared_per_lane", behavior="neutral",
            design_choices={"denormal_handling": Enum(("in_unpack", "in_datapath"))},
            components=slots(),
            mutations=("merge_special_detection", "share_unpack_across_lanes"),
            doc="one operand decoder per lane feeds every structure of the lane "
                "(the unpacked value bus replaces the raw operand at the "
                "structures' inputs)"),
        Family(
            "shared_across_formats", behavior="neutral",
            design_choices={"denormal_handling": Enum(("in_unpack", "in_datapath"))},
            components=slots(),
            mutations=("widen_unpack_to_largest_format",),
            doc="one decoder at the widest format serves every float mode; the "
                "mode selects the field boundaries"),
    ], free_form_allowed=True)
