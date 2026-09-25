"""The point enumeration behind the synthesis database: the variants of
a kind at a width (`variants`), the library module of one point
(`realize`), the top that instantiates it for a standalone synthesis
(`wrapper`) and the geometry helpers the database keys a row by.

`chialu.synthdb` measures and stores the rows:

    python3 -m chialu.synthdb build --pdk nangate45 [--kinds adder,shifter] [--widths 8,16,32]

This module carried a second command line of its own until 2026-09-17.
It wrote `chialu/synth/<pdk>.jsonl`, one level above the sharded
directory `synthdb.load` reads, and its row key was
`(pdk, kind, family, variant, width, clock_ps, effort)` with no flow
fingerprint, so a rerun after a flow change found every row present and
synthesized nothing. Neither the rows nor the key are recoverable, so
the command line is gone and `synthdb build` is the one way to measure.
"""
from __future__ import annotations

import re
from pathlib import Path

from chialu.targets.rtl import families as FAM

KINDS = ("adder", "incrementer", "lzc", "shifter", "comparator", "bitcount", "multiplier", "divider", "logic", "fp_adder", "fp_multiplier", "fp_fma",
         "fp_comparator", "fp_divider", "fp_sqrt", "rounder", "unpacker", "posit_unit", "sd_adder", "rns_adder", "rns_multiplier", "rns_comparator",
         "bcd_adder", "bcd_multiplier", "bcd_divider", "sfu", "dot", "checker")
# the special-function kind: (format, functions) per width; the variant label carries the function
SFU_POINTS = {8: ("fp8e4m3", ("exp2", "recip")), 16: ("fp16", ("exp2", "recip", "rsqrt", "sigmoid")), 32: ("fp32", ("exp2", "recip"))}
SFU_VARIANTS = [
    ("direct_lut", {}, "table"), ("compressed_lut", {}, "base_delta"),
    ("bipartite", {}, "-"), ("stam", {}, "t2"), ("multipartite", {"tables": 3}, "t3"),
    ("add_table_add", {}, "o1_c4"), ("pwl", {}, "s8"), ("pwl", {"segments": 16, "slope_encoding": "power_of_two"}, "s16_po2"),
    ("pwl_residual_lut", {}, "r2"),
    ("piecewise_poly", {}, "s4_d1"), ("piecewise_poly", {"segments": 16, "degree": 2, "guard_bits": 3}, "s16_d2"),
    ("piecewise_poly", {"segments": 16, "degree": 2, "guard_bits": 3, "evaluator.family": "estrin"}, "s16_d2_estrin"),
    ("piecewise_poly", {"segments": 16, "degree": 2, "guard_bits": 3, "segmenter.family": "nonuniform", "segmenter.addressing": "priority_encoder"}, "s16_d2_nonuni"),
    ("single_poly", {}, "d2"), ("rational_approximation", {}, "r1_1"), ("lut_plus_poly", {}, "i5_d1"),
    ("table_factor_refinement", {}, "f8_s1"), ("region_dependent", {}, "r2"), ("mixed_degree", {}, "d2"),
    ("gpu_multifunction_interpolator", {}, "d1"), ("logarithmic_converters", {}, "mitchell"),
    ("logarithmic_converters", {"correction": "pwl_correction", "regions": 4, "lns_full_alu": True}, "pwl4_lns"),
    ("cordic", {}, "n16"), ("redundant_high_radix_cordic", {}, "cs_double"),
    ("digit_recurrence_exp_log", {}, "r2"), ("newton_raphson", {}, "s1"), ("goldschmidt", {}, "s1"),
    ("sigmoid_tanh_pwl", {}, "s3"), ("transformer_activation_lut", {}, "ipoly"),
    # the arithmetic slots bound to library families (the multiplies, adds, variable shifts and leading-zero counts)
    ("piecewise_poly", {"segments": 16, "degree": 2, "guard_bits": 3, "multiplier.family": "booth_recoded_parallel",
                        "adder.family": "parallel_prefix", "adder.topology": "kogge_stone", "shifter.family": "barrel_mux_tree",
                        "lzc.family": "lzd_cell_tree"}, "s16_d2_lib"),
    ("cordic", {"multiplier.family": "direct_pp_parallel", "adder.family": "carry_select", "shifter.family": "funnel",
                "lzc.family": "prefix_lzc"}, "n16_lib"),
]
SFU_FN_OF = {"newton_raphson": ("recip", "rsqrt", "sigmoid"), "goldschmidt": ("recip", "rsqrt"),
             "sigmoid_tanh_pwl": ("sigmoid",), "transformer_activation_lut": ("sigmoid",),
             "digit_recurrence_exp_log": ("exp2",), "direct_lut": ("exp2", "recip", "rsqrt", "sigmoid"),
             "compressed_lut": ("exp2", "recip", "rsqrt", "sigmoid")}
FP_FORMATS = {16: "fp16", 32: "fp32", 8: "fp8e4m3", 64: "fp64"}     # the float format a width names by default
# the kinds whose point names the float format it is measured at (the `_fmt` condition pin)
FP_DB_KINDS = ("fp_adder", "fp_multiplier", "fp_fma", "fp_comparator", "fp_divider", "fp_sqrt", "rounder", "unpacker")
POSIT_FORMATS = {8: "posit8_0", 16: "posit16_1", 32: "posit32_2"}   # the posit format a width names for the posit unit


def posit_geom(width: int):
    """(format, engine geometry, engine) of the posit unit at a width, or
    None at a width without a posit format."""
    from chialu.targets.rtl.engine import Conventions, Engine
    from chialu.targets.rtl.families.fp import Geom
    from chialu.verify.formats import parse_format
    if width not in POSIT_FORMATS:
        return None
    fmt = parse_format(POSIT_FORMATS[width])
    e = Engine("c", fmt, 8, False, targets=[fmt], conv=Conventions())
    return fmt, Geom.of_engine(e), e
# the dot-accumulate geometry a width names: (format_ab, format_c, format_d, elements)
DOT_GEOMS = {8: ("int8", "int32", "int32", 4), 16: ("fp16", "fp32", "fp32", 4), 32: ("fp32", "fp32", "fp32", 1)}


def dot_geom(width: int):
    """The DotGeom (families/dot.py) of the dot kind at a width, or None."""
    from chialu.targets.rtl.families import dot
    from chialu.verify.formats import parse_format
    g = DOT_GEOMS.get(width)
    if g is None:
        return None
    fab, fc, fd, n = g
    return dot.geom_of(parse_format(fab), parse_format(fc), parse_format(fd), n, True)


def parse_geom_tag(tag: str) -> tuple:
    """(XW, EW, SW) of a geometry tag `x<XW>e<EW>s<SW>` (families/fp.py Geom.tag)."""
    m = re.fullmatch(r"x(\d+)e(\d+)s(\d+)", str(tag))
    if not m:
        raise ValueError(f"not a geometry tag: {tag!r}")
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def fp_geoms_of(fmt_name: str) -> list:
    """[None, ...] the geometries a format's points are measured at: its
    own (None), and every union geometry a run file's float modes
    compute at when one of their kinds shares a datapath
    (`synthdb.seed_geoms`) that is wider than the format's own.
    `CHIALU_FP_GEOMS` narrows or replaces the list (a comma list of
    tags, `own` for the format's own alone)."""
    import os
    want = [x.strip() for x in (os.environ.get("CHIALU_FP_GEOMS") or "").split(",") if x.strip()]
    if want == ["own"]:
        return [None]
    tags = want
    if not tags:
        try:
            from chialu.synthdb import seed_geoms
            tags = list(seed_geoms())
        except Exception:  # noqa: BLE001 - no run files to harvest from
            tags = []
    own = fp_geom(0, fmt_name)[1]
    out = [None]
    for tag in tags:
        try:
            XW, EW, SW = parse_geom_tag(tag)
        except ValueError:
            continue
        if (XW, EW, SW) != (own.XW, own.EW, own.SW) and XW >= own.XW and EW >= own.EW and SW >= own.SW:
            if tag not in out:
                out.append(tag)
    return out


def fp_geom(width: int, fmt_name: str | None = None, geom: str | None = None):
    """(format, engine geometry, engine) of a float kind: the named
    format, else the one the width names by default. fp16 and bf16 are
    both 16 bits and share nothing of their geometry, so a float point
    names its format (the `_fmt` condition pin) and a row is keyed by
    it. `geom` is a geometry tag wider than the format's own, which a
    datapath shared among formats computes at (the seed's union
    geometry, alu_seed); the engine is widened to it."""
    from chialu.targets.rtl.engine import Conventions, Engine
    from chialu.targets.rtl.families.fp import Geom
    from chialu.verify.formats import parse_format
    fmt = parse_format(fmt_name or FP_FORMATS.get(width, "fp16"))
    e = Engine("c", fmt, 8, False, targets=[fmt], conv=Conventions())
    g = Geom.of_engine(e)
    if geom:
        XW, EW, SW = parse_geom_tag(geom)
        g = Geom(max(g.XW, XW), max(g.EW, EW), max(g.SW, SW), g.sr_bits, g.tight, g.sr)
    return fmt, g, e


def fp_formats_of(width: int) -> list:
    """The float formats a point of a float kind is measured at, at a
    width: the format the width names by default and every float format
    of that width the run files' structures are built at
    (`synthdb.seed_formats`), narrowed by `CHIALU_FP_FORMATS` when it is
    set (a comma list, for a build of one format)."""
    import os
    from chialu.verify.formats import FloatFormat, parse_format
    want = [x.strip() for x in (os.environ.get("CHIALU_FP_FORMATS") or "").split(",") if x.strip()]
    names = list(want)
    if not names:
        default = FP_FORMATS.get(width)
        names = [default] if default else []
        try:
            from chialu.synthdb import seed_formats
            names += [n for n in seed_formats() if n not in names]
        except Exception:  # noqa: BLE001 - no run files to harvest from
            pass
    out = []
    for name in names:
        try:
            fmt = parse_format(name)
        except ValueError:
            continue
        if isinstance(fmt, FloatFormat) and int(fmt.width) == int(width) and fmt.name not in out:
            out.append(fmt.name)
    return out


def variants(kind: str, width: int) -> list:
    """[(family, pins, variant label)] the library realizes for a kind at
    a width: every parameter variant of every family with a module, the
    prefix families at every named topology and Harris (l, f) point."""
    L = max(1, (width - 1).bit_length())
    out = []
    if kind == "adder":
        out += [("ripple_carry", {"chunk_width_bits": c}, f"chunk{c}") for c in (1, 4)]
        out += [("manchester_carry_chain", {"chain_segment_length": 4}, "seg4")]
        out += [("carry_lookahead", {"group_size": 4, "intergroup_carry": ic}, f"g4_{ic}") for ic in ("ripple", "lookahead")]
        out += [("carry_skip", {"block_width": b}, f"b{b}") for b in (4,)]
        out += [("carry_select", {}, "b4")]
        out += [("conditional_sum", {}, "-")]
        out += [("carry_increment", {"block_width": 4}, "b4")]
        for topo in ("kogge_stone", "sklansky", "brent_kung", "ladner_fischer", "han_carlson", "knowles_mixed"):
            out.append(("parallel_prefix", {"topology": topo}, topo))
        for l in range(L):
            for f in range(L - l):
                out.append(("parallel_prefix", {"topology": "harris", "log2_sparsity": l, "fanout_cap": 2 ** f + 1},
                            f"harris_l{l}f{f}"))
        out += [("ling_prefix", {"topology": t}, t) for t in ("kogge_stone", "sklansky", "han_carlson")]
        out += [("compound_flagged_prefix", {"topology": t}, t) for t in ("kogge_stone", "brent_kung")]
        out += [("sparse_prefix_hybrid", {"log2_sparsity": sp, "sum_block_style": st}, f"sp{sp}_{st}")
                for sp in (1, 2, 3) for st in ("carry_select", "ripple_precompute")]
        out += [("prefix_synthesis_nonuniform_arrival", {"arrival_profile": pr}, pr) for pr in FAM.ARRIVAL_PROFILES]
        out += [("end_around_carry", {"recirculation": rc, "topology": "kogge_stone"}, rc) for rc in ("two_pass_prefix", "cyclic_prefix_level", "select_based")]
        out += [("approximate_truncated", {"lower_scheme": ls, "lower_part_width": max(2, width // 2)}, ls) for ls in ("truncate_constant", "or_gates", "speculative_segments")]
        out += [("carry_select", {"block_adder.family": "carry_lookahead"}, "b4_cla_blocks"),
                ("carry_skip", {"block_adder.family": "parallel_prefix", "block_adder.topology": "sklansky"}, "b4_prefix_blocks")]
        out += [("segmented_carry_speculative", {"carry_in_scheme": cs}, cs) for cs in ("propagate_window", "carry_select_speculation")]
        out += [("lower_part_approximate", {"lower_cell": lc}, lc) for lc in ("or_gate", "approx_mirror_ama")]
        out += [("accuracy_configurable", {}, "mid_mode")]
    elif kind == "multiplier":
        for sg in ("s", "u"):
            for geometry in ("dadda", "wallace"):
                for counter in ("3_2", "4_2"):
                    red = {"reduction.geometry": geometry, "reduction.counter_kind": counter, "_signed": sg == "s"}
                    out.append(("direct_pp_parallel", red, f"{geometry}_{counter}_{sg}"))
                    out.append(("booth_recoded_parallel", dict(red, booth_radix=4), f"booth4_{geometry}_{counter}_{sg}"))
            out.append(("booth_recoded_parallel", {"booth_radix": 8, "_signed": sg == "s"}, f"booth8_dadda_3_2_{sg}"))
            out.append(("booth_recoded_parallel", {"booth_radix": 16, "_signed": sg == "s"}, f"booth16_dadda_3_2_{sg}"))
            out.append(("booth_recoded_parallel", {"booth_radix": 8, "hard_multiple_gen": "partially_redundant", "_signed": sg == "s"}, f"booth8_partred_{sg}"))
            out.append(("booth_recoded_parallel", {"booth_radix": 4, "reduction.cpa.family": "hybrid_arrival_driven",
                                                   "_signed": sg == "s"}, f"booth4_dadda_arrival_cpa_{sg}"))
            out += [("direct_pp_parallel", {"reduction.geometry": g, "_signed": sg == "s"}, f"{g}_3_2_{sg}") for g in ("reduced_area", "balanced_delay", "tdm_arrival_driven")]
            out += [("direct_pp_parallel", {"reduction.counter_kind": c, "_signed": sg == "s"}, f"dadda_{c}_{sg}") for c in ("5_2", "7_3")]
            out += [("direct_pp_parallel", {"reduction.family": "compressor_4_2_tree", "reduction.compressor_kind": c, "_signed": sg == "s"}, f"c42tree_{c}_{sg}")
                    for c in ("4_2", "stacking_6_3")]
            out += [("direct_pp_parallel", {"reduction.family": "tiled_cpa_reduction_tree", "reduction.adder_width": aw, "_signed": sg == "s"}, f"tiled_{aw}_{sg}")
                    for aw in (4, "full_width")]
            out.append(("direct_pp_parallel", {"group_bits": 2, "_signed": sg == "s"}, f"groups2_{sg}"))
            out.append(("carry_save_array", {"_signed": sg == "s"}, f"array_{sg}"))
            out.append(("carry_save_array", {"signed_scheme": "pezaris_negative_weight", "_signed": sg == "s"}, f"array_pezaris_{sg}"))
            out += [("recursive_karatsuba", {"recursion_depth": d, "_signed": sg == "s"}, f"karatsuba_d{d}_{sg}") for d in (1, 2)]
            out.append(("recursive_karatsuba", {"split_kind": "three_way", "_signed": sg == "s"}, f"karatsuba3_{sg}"))
            out.append(("behavioral_star", {"_signed": sg == "s"}, f"star_{sg}"))
            out += [("squarer", {"folding_scheme": fs, "_signed": sg == "s"}, f"{fs}_{sg}") for fs in ("basic_symmetry", "booth_folding", "divide_and_conquer")]
            out += [("segmented_grid", {"merge_form": mf, "_signed": sg == "s"}, f"{mf}_{sg}") for mf in ("cpa", "carry_save_tree", "shift_add_tree")]
            out.append(("segmented_grid", {"segment_shape": "rectangular", "_signed": sg == "s"}, f"rect_{sg}"))
            out += [("redundant_binary_multiplier", {"rbnb_converter": cv, "_signed": sg == "s"}, f"{cv}_{sg}") for cv in ("cpa", "on_the_fly")]
            out.append(("redundant_binary_multiplier", {"booth_radix": 4, "_signed": sg == "s"}, f"booth4_cpa_{sg}"))
            out.append(("redundant_binary_multiplier", {"booth_radix": 2, "_signed": sg == "s"}, f"booth2_cpa_{sg}"))
            out += [("truncated_fixed_width", {"correction_scheme": cs, "_signed": sg == "s"}, f"{cs}_{sg}") for cs in ("constant", "data_dependent")]
            out += [("logarithmic_mitchell", {"correction_scheme": cs, "_signed": sg == "s"}, f"{cs}_{sg}") for cs in ("none", "combet_error_terms", "operand_decomposition")]
            out += [("approximate_compressor", {"technique": tq, "_signed": sg == "s"}, f"{tq}_{sg}") for tq in ("underdesigned_pp_block", "approximate_compressor", "dynamic_segment")]
            out += [("dynamic_segment", {"_signed": sg == "s"}, f"drum_{sg}"), ("operand_rounding", {"_signed": sg == "s"}, f"roba_{sg}"),
                    ("logarithmic", {"correction": "operand_decomposition", "_signed": sg == "s"}, f"od_{sg}"),
                    ("pp_perforation", {"correction": "constant", "_signed": sg == "s"}, f"rows2_{sg}"),
                    ("approximate_compressor_tree", {"_signed": sg == "s"}, f"design1_{sg}"), ("approximate_booth", {"_signed": sg == "s"}, f"abe1_{sg}")]
    elif kind == "divider":
        out += [("restoring_nonrestoring", {"style": st}, st) for st in ("restoring", "nonrestoring")]
        out += [("srt_radix2", {}, "carry_save"), ("srt_radix2", {"residual_form": "twos_complement_cpa"}, "cpa")]
        out += [("srt_high_radix", {"radix": 4}, "r4_qds"), ("srt_high_radix", {"radix": 4, "digit_select.family": "comparator_digit_selection"}, "r4_cmp")]
        out += [("newton_raphson", {}, "rom6"), ("newton_raphson", {"seed.family": "bipartite_rom", "seed.input_bits": 8}, "bipartite8"),
                ("newton_raphson", {"final_round.family": "exclusion_zone_proof"}, "exclusion"),
                ("goldschmidt", {}, "rom6"), ("direct_polynomial", {"approximator.degree": 2, "approximator.input_bits": 6}, "poly2"),
                ("prescaled_very_high_radix", {}, "b8"), ("svoboda_tung", {}, "r4"), ("online_msdf", {}, "d4"),
                ("approximate_recurrence", {}, "axsc1_d4"), ("approximate_functional", {}, "trunc_recip")]
    elif kind == "fp_divider":
        out += [("sig_div_then_round", {"sig_div.family": f}, f) for f in ("restoring_nonrestoring", "srt_radix2", "srt_high_radix", "newton_raphson", "goldschmidt")]
    elif kind == "fp_sqrt":
        out += [("sig_sqrt_then_round", {"sig_sqrt.family": f}, f) for f in ("digit_recurrence_sqrt_combined", "newton_raphson", "goldschmidt")]
    elif kind == "fp_adder":
        out += [("single_path", {}, "default"), ("single_path", {"lz.family": "lzc_after_add"}, "lzc"),
                ("single_path", {"subnormal_representation": "pseudo_normalized_wide_exponent"}, "prenorm"),
                ("single_path", {"operand_order": "shift_each_operand", "lz.string_form": "dual_pos_neg_strings"}, "dual_lza"),
                ("two_path", {}, "default"), ("two_path", {"near_lz.family": "lzc_after_add", "path_select_point": "late_result_mux"}, "lzc_late"),
                ("delay_optimized_unified", {}, "default"),
                ("delay_optimized_unified", {"subtraction_style": "ones_complement_end_around"}, "eac"),
                ("low_power_gated", {}, "default"), ("low_power_gated", {"datapath_partitions": 3}, "three")]
    elif kind == "fp_multiplier":
        out += [("sig_mul_then_round", {}, "direct"), ("sig_mul_then_round", {"sig_mul.family": "booth_recoded_parallel"}, "booth4"),
                ("round_fused_in_reduction", {}, "fused")]
    elif kind == "fp_fma":
        # the fused multiply-add of a float mode (separate_multiplier_and_adder is the fp_adder's and the
        # fp_multiplier's own modules, so it has no row of its own)
        out += [("classic_fma", {}, "eac"),
                ("classic_fma", {"negation_handling": "dual_adder", "lza.family": "lzc_after_add"}, "dual_lzc"),
                ("classic_fma", {"negation_handling": "complement_recode", "multiplier.family": "booth_recoded_parallel"}, "recode_booth4"),
                ("classic_fma", {"subnormal_representation": "pseudo_normalized_wide_exponent"}, "prenorm"),
                ("reduced_latency_fma", {}, "default"),
                ("reduced_latency_fma", {"normalize_before_add": True, "add_skip_for_pure_addition": True}, "prenorm_skip"),
                ("reduced_latency_fma", {"rounding_position": "fused_with_cpa_dual_sum"}, "fused_round"),
                ("multipath_fma", {}, "two_path"),
                ("multipath_fma", {"path_count": 3, "negation_handling": "dual_adder"}, "three_path"),
                ("multipath_fma", {"path_count": 5, "path_select_criterion": "both"}, "five_path"),
                ("bridge_fma", {}, "bridge_reuse")]
    elif kind == "fp_comparator":
        out += [("integer_compare_on_bits", {}, "-"), ("dedicated_magnitude_comparator", {}, "-")]
    elif kind == "rounder":
        out += [("dedicated_per_op", {}, "increment"), ("shared_per_lane", {"round.family": "compound_adder_select"}, "compound"),
                ("dedicated_per_op", {"round.family": "injection"}, "injection"), ("dedicated_per_op", {"round.family": "flagged_prefix"}, "flagged")]
    elif kind == "unpacker":
        out += [("per_unit_unpack", {}, "stored"), ("shared_per_lane", {"denormal_handling": "in_unpack"}, "normalized")]
    elif kind == "sd_adder":
        # the representation slot of a redundant_internal core: the lane's adder
        out += [("generalized_signed_digit", {"radix": r, "redundancy": red, "digit_encoding": enc, "final_conversion": conv,
                                              "addition_scheme": sch, "cpa.family": "parallel_prefix", "cpa.topology": "sklansky"},
                 f"r{r}_{red[:3]}_{enc[:4]}_{conv[:3]}_{sch[:2]}")
                for r, red, enc, conv, sch in ((2, "minimal", "sign_magnitude", "cpa", "two_stage_limited_carry"),
                                               (2, "minimal", "borrow_save", "on_the_fly", "two_stage_limited_carry"),
                                               (4, "minimal", "sign_magnitude", "cpa", "two_stage_limited_carry"),
                                               (4, "maximal", "twos_complement", "cpa", "carry_free"),
                                               (8, "intermediate", "sign_magnitude", "on_the_fly", "carry_free"),
                                               (16, "maximal", "one_hot", "cpa", "carry_free"))]
        out += [("hybrid_signed_digit", {"sd_position_spacing": d, "spacing_uniform": True, "interior_adder": ia}, f"d{d}_{ia[:4]}")
                for d, ia in ((2, "ripple"), (4, "carry_select"), (4, "prefix"), (8, "prefix"))]
        out += [("carry_save_datapath", {"compressor": c, "assimilator.family": "parallel_prefix", "assimilator.topology": "kogge_stone"}, c)
                for c in ("3_2", "4_2", "5_3", "7_3")]
    elif kind in ("rns_adder", "rns_multiplier", "rns_comparator") and width <= 32:
        # the channels slot of an rns_internal core: the lane's adder, multiplier or comparator (a 64-bit
        # lane needs a 130-bit dynamic range: beyond the table and ladder budget)
        if kind == "rns_comparator":
            out += [("rns_scaling_comparison", {"method": m_, "exactness": ex}, f"{m_[:8]}_{ex[:3]}")
                    for m_, ex in (("rom_mrc", "exact"), ("crt_fraction_estimate", "exact"), ("crt_fraction_estimate", "approximate_with_correction"), ("diagonal_function", "exact"))]
        else:
            out += [("rns_channel_arithmetic", {"modulus_form": f, "pow2_plus_1_encoding": e, "multiplier_reduction": mr}, f"{f[:6]}_{e[:3]}_{mr[:4]}")
                    for f, e, mr in (("pow2", "normal", "rom"), ("pow2", "normal", "csa_with_periodic_folding"), ("pow2_plus_1", "diminished_one", "booth_modular"),
                                     ("pow2_minus_1", "normal", "csa_with_periodic_folding"), ("generic", "normal", "iterative_carry_save_msd_estimate"))]
            out += [("rns_forward_converter", {"implementation": im, "chunk_bits": 4, "moduli_count": mc}, f"{im[:8]}_m{mc}")
                    for im, mc in (("rom_per_chunk", 3), ("segmented_rom_modular_add", 4), ("periodic_csa_moma", 3), ("channel_modular_mac", 3))]
            out += [("rns_reverse_converter", {"algorithm": al, "implementation": im, "moduli_count": mc}, f"{al}_{im[:3]}_m{mc}")
                    for al, im, mc in (("crt", "rom", 3), ("crt", "adder_based", 3), ("mixed_radix", "rom", 3), ("new_crt_i", "adder_based", 3), ("new_crt_ii", "rom", 4))]
    elif kind == "posit_unit":
        # the decoder and encoder of the width's posit format (none at 64 bits)
        if width in POSIT_FORMATS:
            for regime in ("lzc_plus_shifter", "two_stage_masked_decode"):
                for rep in ("sign_magnitude", "twos_complement"):
                    out.append(("posit_adder_multiplier", {"regime_decode": regime, "internal_representation": rep},
                                f"{regime[:3]}_{rep[:4]}"))
            out.append(("posit_ieee_interop", {"interop_style": "boundary_converters"}, "lzc_sign"))
    elif kind == "logic":
        out += [("lane_replicated_gates", {}, "-")]
    elif kind == "dot":
        if width not in DOT_GEOMS:
            return []
        n = DOT_GEOMS[width][3]
        out += [("pairwise_tree", {}, "chain"), ("pairwise_tree", {"accum.family": "binary_tree"}, "binary_tree"),
                ("pairwise_tree", {"accum.family": "csa_tree", "accum.compressor": "4:2"}, "csa_4_2"),
                ("pairwise_tree", {"align.family": "bounded_align"}, "band_chain"),
                ("fused_csa", {}, "csa_3_2"), ("fused_csa", {"compressor": "4:2"}, "csa_4_2"),
                ("fused_csa", {"align.family": "bounded_align"}, "band_csa_3_2"),
                ("integer_mac", {}, "systolic"), ("integer_mac", {"array_style": "simd_packed_dot"}, "simd_packed"),
                ("integer_mac", {"array_style": "composable_submultiplier"}, "composable"),
                ("kulisch_long_accumulator", {}, "monolithic"),
                ("kulisch_long_accumulator", {"organization": "segmented_lazy_carry", "carry_resolution": "carry_save_deferred"}, "segmented_deferred"),
                ("kulisch_long_accumulator", {"organization": "banked_sub_adders"}, "banked"),
                ("streaming_accurate_accumulator", {}, "window"),
                ("streaming_accurate_accumulator", {"approach": "tree_reduce_with_refinement"}, "tree_refine"),
                ("tensor_core_mixed_precision_mac", {}, "pe_rne"),
                ("bf16_fma_datapath", {}, "default"), ("fp8_training_datapath", {}, "default"),
                ("multi_precision_simd_fma", {}, "twin")]
        if n >= 2:
            out += [("multi_term_fused_dot", {"alignment_strategy": st}, st)
                    for st in ("per_level", "single_wide_window", "two_stage_coarse_fine", "max_exponent_tree",
                               "pairwise_difference_reuse", "exponent_sorted_realignment_lines")]
            out += [("multi_term_fused_dot", {"sign_handling": "dual_reduction_positive_pair_select"}, "dual_sign"),
                    ("multi_term_fused_dot", {"rounding_contract": "faithful", "guard_bits_per_level": 4}, "faithful_g4")]
        if n == 2:
            out += [("fused_two_term_dot", {}, "dot2")]
        if n == 1:
            out += [("classic_fma", {"negation_handling": ng}, ng) for ng in ("end_around_carry", "dual_adder", "complement_recode")]
            out += [("classic_fma", {"lza.family": "lzc_after_add"}, "lzc_after_add"),
                    ("reduced_latency_fma", {}, "post_cpa"), ("reduced_latency_fma", {"normalize_before_add": True}, "prenorm"),
                    ("reduced_latency_fma", {"rounding_position": "fused_with_cpa_dual_sum"}, "fused_round"),
                    ("multipath_fma", {}, "2paths"), ("multipath_fma", {"path_count": 3}, "3paths"),
                    ("multipath_fma", {"path_count": 5, "path_select_criterion": "both"}, "5paths"),
                    ("bridge_fma", {}, "bridge"), ("bridge_fma", {"composition_style": "cascade_mul_then_add"}, "cascade"),
                    ("mixed_precision_cascade_fma", {}, "exact_product")]
    elif kind == "shifter":
        out += [("barrel_mux_tree", {"direction_handling": d}, d) for d in ("data_reversal", "mirrored_datapath", "amount_negation")]
        out += [("barrel_mux_tree", {"stage_radix": r}, f"radix{r}") for r in (4, 8)]
        out += [("barrel_mux_tree", {"select_encoding": "one_hot_decoded"}, "one_hot"), ("barrel_mux_tree", {"stage_order": "large_shift_first"}, "large_first")]
        out += [("funnel", {}, "-"), ("funnel", {"amount_preprocess": "ones_complement_for_right"}, "ones_complement"),
                ("masked_merged", {}, "-"), ("masked_merged", {"mask_generator": "lut"}, "lut"), ("butterfly_network", {}, "-"),
                ("butterfly_network", {"network": "butterfly"}, "butterfly")]
    elif kind == "comparator":
        out += [("prefix_comparator", {"structure": st, "radix": r}, f"{st}_r{r}") for st in ("msb_first_prefix", "tree_reduction") for r in (2, 4)]
        out += [("subtractor_comparator", {"subtractor.family": f}, f"sub_{f}") for f in ("ripple_carry", "parallel_prefix")]
    elif kind == "bitcount":
        out += [("popcount_counter_tree", {"tree_shape": sh}, sh) for sh in ("balanced_tree", "linear_chain", "wallace_style")]
        out += [("popcount_counter_tree", {"tree_shape": "wallace_style", "counter_primitive": cp}, f"wallace_{cp}") for cp in ("compressor_4_2", "counter_7_3", "lut_rom")]
        out += [("lzd_cell_tree", {}, "pair"), ("lzd_cell_tree", {"block_primitive": "nibble_cell"}, "nibble"),
                ("lzd_cell_tree", {"output_form": "one_hot_shift_controls"}, "one_hot"),
                ("prefix_lzc", {}, "ks_popcount"), ("prefix_lzc", {"count_form": "lookahead_flags"}, "ks_flags"),
                ("priority_encoder", {"lookahead_group": 4}, "g4"), ("priority_encoder", {"lookahead_group": 4, "levels": 2}, "g4_l2")]
        out += [("trailing_zero", {"strategy": st}, st) for st in ("reverse_then_lzd", "isolate_then_encode", "debruijn_multiply_index")]
    # the decimal families at width / 4 digits (a width that is no multiple of 4 has no BCD format)
    elif kind == "bcd_adder" and width % 4 == 0:
        out += [("bcd_direct_addition", {"correction_placement": cp, "carry_scheme": cs}, f"{cp.split('_')[0]}_{cs.split('_')[0]}")
                for cp in ("presum_plus6", "postsum_plus6", "direct_decimal_carry_logic") for cs in ("ripple", "digit_group_lookahead", "full_lookahead")]
        out += [("bcd_direct_addition", {"digit_code": "excess3"}, "excess3"),
                ("bcd_direct_addition", {"subtraction": "nines_complement_end_around_carry"}, "eac"),
                ("bcd_direct_addition", {"subtraction": "direct_borrow_subtracter"}, "borrow"),
                ("bcd_direct_addition", {"complement_generation": "trailing_zero_scan"}, "scan"),
                ("speculative_decimal_addition", {}, "late_correction"),
                ("speculative_decimal_addition", {"recovery": "dual_path_select"}, "dual_path"),
                ("speculative_decimal_addition", {"speculation_target": "both"}, "both_targets"),
                ("redundant_decimal_addition", {}, "svoboda_one_cpa"),
                ("redundant_decimal_addition", {"digit_set": "rbcd_m7_p7", "operands_redundant": "both", "final_conversion": "on_the_fly"}, "rbcd_both_otf"),
                ("redundant_decimal_addition", {"digit_set": "maximally_redundant_m9_p9"}, "max_one_cpa"),
                ("redundant_decimal_addition", {"digit_set": "overloaded_0_15"}, "odds_cpa"),
                ("decimal_multioperand_addition", {}, "csa_per_level"),
                ("decimal_multioperand_addition", {"reduction_style": "binary_tree_then_convert"}, "binary_columns"),
                ("decimal_multioperand_addition", {"reduction_style": "decimal_compressors", "compressor_arity": "4_to_2"}, "compressor_42"),
                ("decimal_multioperand_addition", {"reduction_style": "signed_digit_binary_compressors"}, "code_4221")]
    elif kind == "bcd_multiplier" and width % 4 == 0 and width <= 32:
        out += [("parallel_decimal_multiplication", {"multiplier_recoding": rc, "internal_digit_code": cd, "reduction_tree.family": tr}, f"{rc[:5]}_{cd}_{tr[:6]}")
                for rc in ("sd_radix10_m5_p5", "radix4_radix5_split", "none") for cd in ("bcd8421", "bcd4221") for tr in ("linear_chain", "csa_tree")]
        out += [("parallel_decimal_multiplication", {"internal_digit_code": cd, "reduction_tree.family": "csa_tree"}, f"sd_{cd}_csa")
                for cd in ("bcd5211", "xs3_odds", "sd_m8_p8_posibit_negabit")]
        out += [("parallel_decimal_multiplication", {"pp_generation": "digit_by_digit"}, "digit_by_digit"),
                ("parallel_decimal_multiplication", {"reduction_tree.family": "binary_tree"}, "binary_tree")]
    elif kind == "bcd_divider" and width % 4 == 0 and width <= 32:
        out += [("decimal_digit_recurrence", {}, "compare_0_9"),
                ("decimal_digit_recurrence", {"digit_split": "radix2_times_radix5"}, "compare_split")]
        if width <= 16:
            out += [("decimal_digit_recurrence", {"quotient_digit_set": "redundant_m7_p7"}, "srt_m7_prescaled"),
                    ("decimal_digit_recurrence", {"quotient_digit_set": "minimally_redundant_m5_p5"}, "srt_m5_prescaled"),
                    ("decimal_newton", {}, "seed2"),
                    ("decimal_newton", {"seed_digits": 3}, "seed3"),
                    ("decimal_newton", {"final_round.family": "exclusion_zone_proof"}, "exclusion")]
    elif kind == "sfu":
        point = SFU_POINTS.get(width)
        if point:
            fmt, fns = point
            for family, pins, label in SFU_VARIANTS:
                if family in ("direct_lut", "compressed_lut") and width > 12:
                    continue                         # the value tables serve formats of at most 12 bits
                for fn in fns:
                    if fn not in SFU_FN_OF.get(family, fns):
                        continue
                    out.append((family, dict(pins, _fn=fn, _fmt=fmt), f"{label}@{fn}"))
    return out


def realize(kind: str, family: str, pins: dict, width: int):
    """The library Module of a variant, or None."""
    if kind == "lzc":
        return FAM.lzc_module(family, pins, width)
    if kind == "incrementer":
        return FAM.incrementer_module(family, pins, width)
    if kind == "rotator":
        return FAM.shifter_module(family, pins, width)
    if kind == "adder":
        return FAM.adder_module(family, pins, width)
    if kind == "shifter":
        return FAM.shifter_module(family, pins, width)
    if kind == "comparator":
        return FAM.comparator_module(family, pins, width, True)
    if kind == "multiplier":
        return FAM.mul_module(family, pins, width, bool(pins.get("_signed", True)))
    if kind == "divider":
        return FAM.div_module(family, pins, width, width, width)
    if kind == "logic":
        return FAM.logic_module(family, pins, width)
    if kind == "dot":
        dg = dot_geom(width)
        return FAM.dot_module(dg, family, pins) if dg is not None else None
    if kind in FP_DB_KINDS:
        fmt, g, e = fp_geom(width, (pins or {}).get("_fmt"), (pins or {}).get("_geom"))
        return FAM.fp_module(kind, family, pins, g, fmt=fmt, M=fmt.man_bits, bias=fmt.bias, tokens=e.tokens)
    if kind == "bitcount":
        for fn in (FAM.popcount_module, FAM.lzc_module, FAM.tzc_module):
            m = fn(family, pins, width)
            if m:
                return m
    if kind == "sd_adder":
        from chialu.targets.rtl.families import redundant
        try:
            n, t = redundant.representation_adder_sv(width, family, pins)
        except ValueError:
            return None
        return FAM.Module(n, {}, t)
    if kind in ("rns_adder", "rns_multiplier", "rns_comparator"):
        from chialu.targets.rtl.families import redundant
        try:
            n, t = redundant.rns_sv(kind[4:], width, family, pins, True)
        except ValueError:
            return None
        return FAM.Module(n, {}, t)
    if kind == "posit_unit":
        pg = posit_geom(width)
        if pg is None:
            return None
        fmt, g, e = pg
        return FAM.posit_module("unit", family, pins, fmt, g, tokens=e.tokens)
    if kind == "bcd_adder":
        return FAM.bcd_adder_module(family, pins, width // 4)
    if kind == "bcd_multiplier":
        return FAM.bcd_mul_module(family, pins, width // 4)
    if kind == "bcd_divider":
        return FAM.bcd_div_module(family, pins, width // 4)
    if kind == "sfu":
        from chialu.targets.rtl.engine import Conventions, Engine
        from chialu.targets.rtl.families.fp import Geom
        from chialu.verify.formats import parse_format
        fmt = parse_format(pins["_fmt"])
        e = Engine("c", fmt, 8, False, targets=[fmt], conv=Conventions())
        p = {k: v for k, v in pins.items() if not k.startswith("_")}
        return FAM.sfu_module(pins["_fn"], fmt, Geom.of_engine(e), family, p)
    if kind == "checker":
        # the checker of one int mode at the width over the database's shared op set (alu_checker.CHAR_OPS)
        from chialu.targets.rtl.alu_checker import checker_point_module
        try:
            return checker_point_module(family, pins, width)
        except ValueError:
            return None
    return None


def wrapper(kind: str, module, width: int, pins: dict | None = None) -> str:
    """A top `chr_top` instantiating the module with its parameters, so
    synthesis measures the parameterized instance."""
    ps = ", ".join(f".{k}({v})" for k, v in module.params.items())
    inst = f"{module.name} " + (f"#({ps}) " if ps else "")
    aw = max(1, (width - 1).bit_length())
    nw = width.bit_length()
    if kind == "adder" and module.name.endswith("_flag"):
        ports = (f"input [{width-1}:0] a, input [{width-1}:0] b, input cin, output [{width-1}:0] s, output cout, "
                 f"output [{width-1}:0] s1")
        body = f"{inst}u (.a(a), .b(b), .cin(cin), .s(s), .cout(cout), .s1(s1));"
    elif kind == "adder":
        ports = f"input [{width-1}:0] a, input [{width-1}:0] b, input cin, output [{width-1}:0] s, output cout"
        body = f"{inst}u (.a(a), .b(b), .cin(cin), .s(s), .cout(cout));"
    elif kind == "shifter":
        ports = f"input [{width-1}:0] a, input [{aw-1}:0] amt, input [2:0] op, output [{width-1}:0] y"
        body = f"{inst}u (.a(a), .amt(amt), .op(op), .y(y));"
    elif kind == "comparator":
        ports = f"input [{width-1}:0] a, input [{width-1}:0] b, output lt, output eq"
        body = f"{inst}u (.a(a), .b(b), .lt(lt), .eq(eq));"
    elif kind == "multiplier":
        ports = f"input [{width-1}:0] a, input [{width-1}:0] b, output [{2*width-1}:0] p"
        body = f"{inst}u (.a(a), .b(b), .p(p));"
    elif kind == "divider":
        ports = f"input [{width-1}:0] a, input [{width-1}:0] b, output [{width-1}:0] q, output [{width-1}:0] r"
        body = f"{inst}u (.a(a), .b(b), .q(q), .r(r));"
    elif kind == "incrementer":
        ports = f"input [{width-1}:0] a, input cin, output [{width-1}:0] s, output cout"
        body = f"{inst}u (.a(a), .cin(cin), .s(s), .cout(cout));"
    elif kind == "rotator":
        ports = f"input [{width-1}:0] a, input [{aw-1}:0] amt, input [2:0] op, output [{width-1}:0] y"
        body = f"{inst}u (.a(a), .amt(amt), .op(op), .y(y));"
    elif kind == "logic":
        ports = f"input [{width-1}:0] a, input [{width-1}:0] b, input [1:0] op, output [{width-1}:0] y"
        body = f"{inst}u (.a(a), .b(b), .op(op), .y(y));"
    elif kind in ("sd_adder", "rns_adder"):
        ports = f"input [{width-1}:0] a, input [{width-1}:0] b, input cin, output [{width-1}:0] s, output cout"
        body = f"{inst}u (.a(a), .b(b), .cin(cin), .s(s), .cout(cout));"
    elif kind == "rns_multiplier":
        ports = f"input [{width-1}:0] a, input [{width-1}:0] b, output [{2*width-1}:0] p"
        body = f"{inst}u (.a(a), .b(b), .p(p));"
    elif kind == "rns_comparator":
        ports = f"input [{width-1}:0] a, input [{width-1}:0] b, output lt, output eq"
        body = f"{inst}u (.a(a), .b(b), .lt(lt), .eq(eq));"
    elif kind == "checker":
        from chialu.targets.rtl.alu_checker import checker_point_ports
        plist = checker_point_ports(width)
        ports = ", ".join(f"{'input' if d == 'in' else 'output'} [{w-1}:0] {n}" for n, d, w in plist)
        body = f"{inst}u (" + ", ".join(f".{n}({n})" for n, _d, _w in plist) + ");"
    elif kind == "posit_unit":
        fmt, g, e = posit_geom(width)
        from chialu.targets.rtl.engine import FW
        XT, VW, W = g.XT, g.VW, fmt.width
        ports = (f"input [{W-1}:0] b, input daz, output [{VW}:0] u, input [{XT-1}:0] x, input [2:0] rnd, input [7:0] word, input ftz, "
                 f"output [{FW-1}:0] fl, output [{W-1}:0] bits")
        body = f"{inst}uu (.b(b), .daz(daz), .u(u), .x(x), .rnd(rnd), .word(word), .ftz(ftz), .fl(fl), .bits(bits));"
    elif kind == "bcd_adder":
        ports = f"input [{width-1}:0] a, input [{width-1}:0] b, input sub, input cin, output [{width-1}:0] s, output cout"
        body = f"{inst}u (.a(a), .b(b), .sub(sub), .cin(cin), .s(s), .cout(cout));"
    elif kind == "bcd_multiplier":
        ports = f"input [{width-1}:0] a, input [{width-1}:0] b, output [{2*width-1}:0] p"
        body = f"{inst}u (.a(a), .b(b), .p(p));"
    elif kind == "bcd_divider":
        ports = f"input [{width-1}:0] a, input [{width-1}:0] b, output [{width-1}:0] q, output [{width-1}:0] r"
        body = f"{inst}u (.a(a), .b(b), .q(q), .r(r));"
    elif kind == "dot":
        dg = dot_geom(width)
        text = module.text or ""
        header = text[text.find("\nmodule "):].split(");", 1)[0]          # the port list alone (not the header comment)
        n, XT, AW = dg.n, dg.g.XT, dg.AW
        if dg.intg:
            W, _sg, _F, Wc = dg.intg[0], dg.intg[1], dg.intg[2], dg.intg[3]
            ports = f"input [{n*W-1}:0] a, input [{n*W-1}:0] b, input [{Wc-1}:0] c"
            conns = ".a(a), .b(b), .c(c)"
        else:
            ports = f"input [{n*XT-1}:0] xa, input [{n*XT-1}:0] xb, input [{XT-1}:0] xc"
            conns = ".xa(xa), .xb(xb), .xc(xc)"
        if re.search(r"\brnd\b", header):
            ports += ", input [2:0] rnd"
            conns += ", .rnd(rnd)"
        if re.search(r"\bword\b", header):
            ports += f", input [{dg.g.sr_bits-1}:0] word"
            conns += ", .word(word)"
        if dg.out == "acc":
            ports += f", output signed [{AW-1}:0] acc"
            conns += ", .acc(acc)"
        else:
            ports += f", output [{XT-1}:0] y"
            conns += ", .y(y)"
        body = f"{inst}u ({conns});"
    elif kind in FP_DB_KINDS:
        fmt, g, e = fp_geom(width, (pins or {}).get("_fmt"), (pins or {}).get("_geom"))
        XT, VW, W = g.XT, g.VW, fmt.width
        if kind == "fp_adder":
            ports = f"input [{XT-1}:0] xa, input [{XT-1}:0] xb, input sub, output [{XT-1}:0] y"
            body = f"{inst}u (.xa(xa), .xb(xb), .sub(sub), .y(y));"
        elif kind == "fp_fma":
            # the fused multiply-add serving the mode's adder, its multiplier and the fused ops under the op code
            # fop (fp.FMA_OP_CODES); reduced_latency_fma's fused rounding reads the rounding mode
            header = (module.text or "")[(module.text or "").find("\nmodule "):].split(");", 1)[0]
            rnd = bool(re.search(r"\brnd\b", header))
            ports = (f"input [{XT-1}:0] xa, input [{XT-1}:0] xb, input [{XT-1}:0] xc, input [2:0] fop, "
                     + ("input [2:0] rnd, " if rnd else "") + f"output [{XT-1}:0] y")
            body = f"{inst}u (.xa(xa), .xb(xb), .xc(xc), .fop(fop){', .rnd(rnd)' if rnd else ''}, .y(y));"
        elif kind == "fp_multiplier":
            fused = "fused" in module.name
            ports = f"input [{XT-1}:0] xa, input [{XT-1}:0] xb, input [2:0] rnd, output [{XT-1}:0] y"
            body = f"{inst}u (.xa(xa), .xb(xb){', .rnd(rnd)' if fused else ''}, .y(y));"
        elif kind == "fp_comparator":
            ports = f"input [{XT-1}:0] xa, input [{XT-1}:0] xb, output lt, output eq"
            body = f"{inst}u (.xa(xa), .xb(xb), .lt(lt), .eq(eq));"
        elif kind == "fp_divider":
            ports = f"input [{XT-1}:0] xa, input [{XT-1}:0] xb, output [{XT-1}:0] y"
            body = f"{inst}u (.xa(xa), .xb(xb), .y(y));"
        elif kind == "fp_sqrt":
            ports = f"input [{XT-1}:0] xa, output [{XT-1}:0] y"
            body = f"{inst}u (.xa(xa), .y(y));"
        elif kind == "rounder":
            from chialu.targets.rtl.engine import FW
            ports = f"input [{XT-1}:0] x, input [2:0] rnd, input [7:0] word, input ftz, output [{FW-1}:0] fl, output [{W-1}:0] bits"
            body = f"{inst}u (.x(x), .rnd(rnd), .word(word), .ftz(ftz), .fl(fl), .bits(bits));"
        else:
            ports = f"input [{W-1}:0] b, input daz, output [{VW}:0] u"
            body = f"{inst}uu (.b(b), .daz(daz), .u(u));"
    elif kind == "sfu":
        from chialu.targets.rtl.families.sfu import PATTERN_FAMILIES
        if any(module.name.startswith(f"fam_sfu_{f}_") for f in PATTERN_FAMILIES):
            W = int(module.text.split("input logic [")[1].split(":")[0]) + 1
            ports = f"input [{W-1}:0] x, output [{W-1}:0] y"
            body = f"{inst}u (.x(x), .y(y));"
        else:
            XT = int(module.text.split("input logic [")[1].split(":")[0]) + 1
            ports = f"input [{XT-1}:0] x, output [{XT-1}:0] y, output inv, output dz"
            body = f"{inst}u (.x(x), .y(y), .inv(inv), .dz(dz));"
    else:
        ports = f"input [{width-1}:0] a, output [{nw-1}:0] n"
        body = f"{inst}u (.a(a), .n(n));"
    return f"module chr_top ({ports});\n  {body}\nendmodule\n"


