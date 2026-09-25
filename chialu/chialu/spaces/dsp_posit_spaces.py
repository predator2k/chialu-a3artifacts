"""Posit-format units (rev 9).

Transcribed from chialu/knowledge/fpga_arith.md after the ASIC scope ruling:
FPGA MAPPING techniques are out of scope, and posit units are format-axis
targets. Rev 8 (new_families/dsp.md): posit_adder_multiplier gains a
divider. The DSP block's own internal ALU organization (`dsp_block_space`:
dsp48_style_slice, variable_precision_dsp, hard_fp_dsp, ai_tensor_block,
multiprecision_block_proposal, embedded_fpu_block) is deferred because no
unit template opens it (docs/deferred-families.md); its definitions are
kept under legacy/knowledge/deferred/spaces_deferred.py.
"""

from adir import Bool, Enum, Range
from adir.spaces import Family, Space
from chialu.spaces.arith_spaces import cpa_space, shifter_space
from chialu.spaces.div_spaces import div_space
from chialu.spaces.shift_simd_spaces import lzc_space

# the decoder's and encoder's own structures: the regime run's leading-zero count and the shifts that move the
# fields past it (the same slots on both families, whose decoder and encoder are one generator)
DECODE_SLOTS = {"lzc": lzc_space(), "shifter": shifter_space()}


def posit_unit_space() -> Space:
    """Posit arithmetic units; regime decode is an LZC application."""
    return Space(families=[
        Family(
            "posit_adder_multiplier", behavior="neutral",
            papers=("gustafson_2017", "chaurasiya_2018", "jaiswal_2018",
                    "jaiswal_2019", "podobas_2018", "zhang_2020",
                    "murillo_2020", "murillo_2022", "uguen_2019",
                    "dedinechin_2019b"),
            design_choices={
                "regime_decode": Enum(("lzc_plus_shifter",
                                             "two_stage_masked_decode")),
                "internal_representation": Enum(("sign_magnitude",
                                                       "twos_complement")),
                "approximation": Enum(("none",
                                             "logarithmic_fraction")),
                "operator_set": Enum(("add_mul", "add_mul_div"))},
            components=dict(DECODE_SLOTS, sig_datapath=cpa_space(),
                            sig_div=div_space()),
            mutations=("share_decode_between_operators",
                       "switch_internal_representation",
                       "approximate_fraction_logarithmically",
                       "compare_against_ieee_same_width",
                       "add_divider_behind_shared_decode"),
            doc="parameterized posit add/mul (Chaurasiya, PACoGen, "
                "PLAM); uguen_2019/dedinechin_2019b are the honest "
                "cost comparisons vs IEEE at equal width"),
        Family(
            "posit_ieee_interop", behavior="neutral",
            papers=("crespo_2022", "tiwari_2021", "carmichael_2019"),
            design_choices={
                "interop_style": Enum(
                    ("boundary_converters", "unified_dual_format_datapath",
                     "isa_posit_replaces_float")),
                "conversion_direction": Enum(("posit_to_ieee",
                                                    "ieee_to_posit",
                                                    "bidirectional")),
                "regime_decode": Enum(("lzc_plus_shifter",
                                             "two_stage_masked_decode")),
                "internal_representation": Enum(("sign_magnitude",
                                                       "twos_complement"))},
            components=dict(DECODE_SLOTS),
            mutations=("add_boundary_converters",
                       "unify_datapaths_over_shared_core",
                       "expose_posit_isa_extension"),
            doc="converters or one dual-format datapath (PERI, Deep "
                "Positron)"),
    ], free_form_allowed=True)
