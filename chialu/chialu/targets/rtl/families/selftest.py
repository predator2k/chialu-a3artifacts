"""Verify the family library over the synthesis database's points.

    python3 -m chialu.targets.rtl.families.selftest --cases space --kinds adder,multiplier --widths 8,16
    python3 -m chialu.targets.rtl.families.selftest --cases space --all
    python3 -m chialu.targets.rtl.families.selftest --cases curated --widths 8,16,12
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from functools import partial
from pathlib import Path

from chialu.targets.rtl.families import HERE, library_text, prefix

N_RANDOM = 3000
STIMULUS_SEED = 1


def prefix_specs(w):
    """The named topologies and every Harris (l, f) point of the width."""
    L = max(1, (w - 1).bit_length())
    out = list(prefix.NAMED)
    out += [f"harris:l{l}f{f}" for l in range(L) for f in range(L - l)]
    out += [f"knowles:{','.join(str(2 ** max(0, j - 2)) for j in range(L, 0, -1))}"]
    return out


def prefix_cases(w):
    """(module name, generated text, flagged) per spec and variant, plus
    an edited Kogge-Stone (PrefixRL moves) and an arrival-driven graph,
    the radix-3 and radix-4 graphs, the Ling groups and sum recoveries,
    the flag options."""
    out = []
    for spec in prefix_specs(w):
        for ling in (False, True):
            for flagged in (False, True):
                name, text, _ = prefix.adder_sv(w, spec, ling=ling, flagged=flagged)
                out.append((name, text, flagged))
    for spec in ("sklansky", "kogge_stone", "brent_kung"):
        for val in (3, 4):
            name, text, _ = prefix.adder_sv(w, spec, valency=val)
            out.append((name, text, False))
    for grp in (2, 3, 4):
        for rec in ("xor_correction", "late_select_mux"):
            name, text, _ = prefix.adder_sv(w, "kogge_stone", ling=True, ling_group=grp, sum_recovery=rec)
            out.append((name, text, False))
    name, text, _ = prefix.adder_sv(w, "sklansky", ling=True, sum_recovery="late_select_mux")
    out.append((name, text, False))
    for impl in ("flag_row", "dual_carry_tree"):
        for late in (False, True):
            for outs in ("sum_sum1", "sum_sum1_summinus1"):
                name, text, _ = prefix.adder_sv(w, "sklansky", flagged=True, flag_impl=impl, late_cin=late, flag_outputs=outs)
                out.append((name, text, True))
    edits = f"remove {w - 1} 0; remove {w // 2} 0; add {w - 2} 1; add {w - 1} 0"
    name, text, _ = prefix.adder_sv(w, "kogge_stone", edits=edits, name=f"fam_prefix_edited_w{w}")
    out.append((name, text, False))
    arrival = [abs(i - w // 2) // 2 for i in range(w)]
    spec = "arrival:" + ",".join(str(w // 4 - a if w // 4 - a > 0 else 0) for a in arrival)
    name, text, _ = prefix.adder_sv(w, spec, name=f"fam_prefix_arrival_w{w}")
    out.append((name, text, False))
    return out


def adder_cases(w):
    out = [("fam_adder_ripple_carry", {"W": w, "CHUNK": c, "FORM": f}) for c in (1, 4) for f in (0, 1, 2, 3)]
    out += [("fam_adder_manchester_carry_chain", {"W": w, "SEG": 4, "VARSKIP": v}) for v in (0, 1)]
    out += [("fam_adder_carry_lookahead", {"W": w, "G": g, "INTER": it, "LEVELS": 1}) for g in (2, 4, 5) for it in (0, 1, 2)]
    out += [("fam_adder_carry_lookahead", {"W": w, "G": 2, "INTER": it, "LEVELS": lv}) for it in (0, 1) for lv in (2, 3)]
    out += [("fam_adder_conditional_sum", {"W": w, "BASE": b, "RADIX": r}) for b in (1, 2, 3) for r in (2, 4)]
    return out


def mul_cases(w):
    """(module name, text, signed) of the multiplier families: the tree
    families over the reduction families, geometries and cells, the
    hybrid final adder, the array in both signed schemes, Booth radix 4,
    8 and 16 with every hard-multiple and sign-extension form, the 2-bit
    groups, Karatsuba in its three splits, each signed and unsigned."""
    from chialu.targets.rtl.families import mul
    cases = []
    for geometry in mul.GEOMETRIES:
        for counter in ("3_2", "4_2"):
            cases.append(("direct_pp_parallel", {"reduction.geometry": geometry, "reduction.counter_kind": counter,
                                                 "reduction.cpa.adder.family": "parallel_prefix", "reduction.cpa.adder.topology": "sklansky"}))
    cases += [("direct_pp_parallel", {"reduction.counter_kind": c}) for c in ("5_2", "7_3")]
    cases += [("direct_pp_parallel", {"reduction.family": "compressor_4_2_tree", "reduction.compressor_kind": c}) for c in mul.COMPRESSORS]
    cases += [("direct_pp_parallel", {"reduction.family": "tiled_cpa_reduction_tree", "reduction.adder_width": aw}) for aw in (2, 8, "full_width")]
    cases += [("direct_pp_parallel", {"reduction.family": "tiled_cpa_reduction_tree", "reduction.adder_width": 4,
                                      "reduction.carry_assimilation": asm, "reduction.terminal_reduction": term})
              for asm, term in (("extra_counter_row", "3_2_counter"), ("staggered_tiling", "compressor_4_2"), ("terminal_compressor", "compressor_9_2"))]
    # staggered_tiling opens every odd level with an adder_width // 2 tile, one bit at widths 2 and 3
    cases += [("direct_pp_parallel", {"reduction.family": "tiled_cpa_reduction_tree", "reduction.adder_width": aw,
                                      "reduction.carry_assimilation": "staggered_tiling"}) for aw in (2, 3)]
    cases += [("direct_pp_parallel", {"reduction.cpa.family": "hybrid_arrival_driven", "reduction.cpa.region_adder_mix": mix}) for mix in mul.HYBRID_MIX]
    cases += [("direct_pp_parallel", {"reduction.cpa.family": "hybrid_arrival_driven", "reduction.cpa.arrival_model": "uniform",
                                      "reduction.cpa.boundary_search": "delay_bound_boundary_enumeration", "reduction.cpa.region_count": 4})]
    cases += [("direct_pp_parallel", {"signed_scheme": "sign_extension"}),
              ("direct_pp_parallel", {"group_bits": 2}), ("direct_pp_parallel", {"group_bits": 2, "hard_multiple_adder.family": "parallel_prefix"}),
              ("direct_pp_parallel", {"group_bits": 2, "signed_scheme": "sign_extension"})]
    for radix in (4, 8, 16):
        cases += [("booth_recoded_parallel", {"booth_radix": radix, "hard_multiple_gen": gen}) for gen in ("cpa_precompute", "partially_redundant", "specialized_3m_cpa")]
        cases += [("booth_recoded_parallel", {"booth_radix": radix, "sign_extension": se, "negative_pp_encoding": ne})
                  for se, ne in (("full_extension", "ones_complement_plus_neg_bit"), ("roorda_compact", "ones_complement_plus_neg_bit"),
                                 ("prevention_constant", "twos_complement_row"), ("roorda_compact", "twos_complement_row"))]
    cases += [("booth_recoded_parallel", {"booth_radix": 8, "reduction.geometry": "wallace", "reduction.cpa.adder.family": "carry_select",
                                          "hard_multiple_adder.family": "parallel_prefix"})]
    cases += [("carry_save_array", {"cpa.adder.family": "ripple_carry"}), ("carry_save_array", {"signed_scheme": "pezaris_negative_weight"}),
              ("carry_save_array", {"cpa.family": "hybrid_arrival_driven"})]
    cases += [("recursive_karatsuba", {"split_kind": sk, "base_multiplier": bm}) for sk, bm in
              (("two_way", "direct_tree"), ("two_way", "array"), ("two_way", "booth_tree"), ("three_way", "direct_tree"), ("rectangular", "array"))]
    cases += [("recursive_karatsuba", {"recursion_depth": 2}), ("recursive_karatsuba", {"recursion_depth": 2, "split_kind": "three_way", "adder.family": "parallel_prefix"})]
    out, seen = [], set()
    for signed in (False, True):
        for fam, pins in cases:
            name, text, _ = mul.mul_sv(w, signed, fam, dict(pins))
            if name in seen:
                continue
            seen.add(name)
            out.append((name, text, signed))
    return out


def mul_ext_cases(w):
    """(module name, text, signed, bench) of the extension multiplier
    families: the exact ones (behavioral_star, the squarers, the
    segmented grids, the redundant binary trees) against a * b, the
    approximate ones under an error bound (a relative bound for the
    logarithmic and window families, an absolute one in units of 2^w
    for the truncated and inexact-compressor families)."""
    from chialu.targets.rtl.families import mul_ext
    exact = [("behavioral_star", {}, "star"), ("squarer", {}, "sq_sym"), ("squarer", {"folding_scheme": "booth_folding"}, "sq_booth"),
             ("squarer", {"folding_scheme": "divide_and_conquer"}, "sq_dc"),
             ("squarer", {"folding_scheme": "divide_and_conquer", "cross.family": "booth_recoded_parallel", "pre_adder.family": "parallel_prefix"}, "sq_dc_booth"),
             ("segmented_grid", {}, "grid_cpa"), ("segmented_grid", {"merge_form": "carry_save_tree"}, "grid_cst"),
             ("segmented_grid", {"merge_form": "shift_add_tree", "seg_w": 6, "num_seg": 3}, "grid_tree6"),
             ("segmented_grid", {"segment_shape": "rectangular"}, "grid_rect"), ("segmented_grid", {"recursion_depth": 2}, "grid_d2"),
             ("segmented_grid", {"segment.family": "booth_recoded_parallel", "merge_adder.family": "carry_select"}, "grid_booth"),
             ("redundant_binary_multiplier", {}, "rb"), ("redundant_binary_multiplier", {"rbnb_converter": "on_the_fly"}, "rb_otf"),
             ("redundant_binary_multiplier", {"booth_radix": 2}, "rb_booth2"),
             ("redundant_binary_multiplier", {"booth_radix": 4, "rbnb_converter": "carry_select"}, "rb_booth"),
             ("redundant_binary_multiplier", {"rb_encoding": "sign_magnitude_2bit"}, "rb_sm"),
             ("redundant_binary_multiplier", {"rb_encoding": "np_coding", "booth_radix": 4}, "rb_np")]
    rel = [("logarithmic_mitchell", {}, "log", 0.12, 0.05), ("logarithmic_mitchell", {"correction_scheme": "combet_error_terms"}, "log_combet", 0.12, 0.03),
           ("logarithmic_mitchell", {"correction_scheme": "operand_decomposition"}, "log_od", 0.12, 0.03),
           ("logarithmic_mitchell", {"correction_scheme": "nearest_one_rounding"}, "log_nor", 0.15, 0.05),
           ("logarithmic_mitchell", {"exact_msb_hybrid": True}, "log_hyb", 0.12, 0.03),
           ("logarithmic_mitchell", {"lod.family": "prefix_lzc", "normalize_shifter.family": "funnel", "antilog_shifter.family": "butterfly_network",
                                     "log_adder.family": "parallel_prefix"}, "log_slots", 0.12, 0.05),
           ("approximate_compressor", {"technique": "dynamic_segment"}, "ac_drum", 0.07, 0.02),
           ("approximate_compressor", {"technique": "dynamic_segment", "lod.family": "priority_encoder", "normalize_shifter.family": "masked_merged",
                                       "core.family": "booth_recoded_parallel"}, "ac_drum_slots", 0.07, 0.02)]
    absu = [("truncated_fixed_width", {}, "trunc", 2.5, 0.6),
            ("truncated_fixed_width", {"correction_scheme": "data_dependent", "output_rounding": "round_to_nearest", "extra_columns_kept": 3}, "trunc_dd", 2.0, 0.6),
            ("truncated_fixed_width", {"correction_scheme": "variable_mmse", "output_rounding": "force_lsb_one_jamming"}, "trunc_mmse", 2.0, 0.6),
            ("truncated_fixed_width", {"kept_tree.family": "compressor_4_2_tree"}, "trunc_42", 2.5, 0.6),
            ("truncated_fixed_width", {"kept_tree.family": "tiled_cpa_reduction_tree"}, "trunc_tiled", 2.5, 0.6),
            ("approximate_compressor", {}, "ac_ud", 4.0, 0.5), ("approximate_compressor", {"technique": "approximate_compressor"}, "ac", 1.0, 0.2),
            ("approximate_compressor", {"technique": "configurable_error_recovery", "error_recovery_stages": 2, "unbiased_error": True}, "ac_rec", 1.0, 0.2)]
    out = []
    for signed in (False, True):
        sg = "s" if signed else "u"
        for fam, pins, tag in exact:
            n, t, _ = mul_ext.mul_ext_sv(w, signed, fam, pins, name=f"fam_mul_{tag}_w{w}_{sg}")
            out.append((n, t, signed, ("exact",)))
        for fam, pins, tag, mx, mn in rel:
            n, t, _ = mul_ext.mul_ext_sv(w, signed, fam, pins, name=f"fam_mul_{tag}_w{w}_{sg}")
            out.append((n, t, signed, ("rel", mx, mn)))
        for fam, pins, tag, mx, mn in absu:
            n, t, _ = mul_ext.mul_ext_sv(w, signed, fam, pins, name=f"fam_mul_{tag}_w{w}_{sg}")
            out.append((n, t, signed, ("abs", mx, mn)))
    return out


def adder_ext_cases(w):
    """(module name, text, bench) of the generated adder families: the
    end-around-carry adders over the three moduli, recirculations and
    two topologies against the modular reference, the truncated adders
    under an absolute bound, the block-composed adders with library
    blocks against a + b + cin."""
    from chialu.targets.rtl.families import adder_ext
    out = []
    for modulus in ("mod_2n_minus_1", "mod_2n_plus_1_diminished_one", "generic_p_correction"):
        # generic-p corrects by a complete conditional subtraction (no recirculation choice) and its modulus
        # lies in the space's Range(3, 4095)
        generic = modulus == "generic_p_correction"
        pval = min((1 << w) - 3, 4093) if generic else (1 << w) - 3
        for recirc in (("none",) if generic else ("two_pass_prefix", "cyclic_prefix_level", "select_based")):
            for topo in ("kogge_stone", "brent_kung"):
                pins = {"modulus": modulus, "topology": topo}
                if generic:
                    # only generic-p reads a modulus value: the others' is fixed by the word width, and
                    # validate_pins refuses an inactive pin (alu_contracts.end_around_carry)
                    pins["modulus_value"] = pval
                else:
                    pins["recirculation"] = recirc
                mtag = {"mod_2n_minus_1": "m1", "mod_2n_plus_1_diminished_one": "p1", "generic_p_correction": "gp"}[modulus]
                n, t = adder_ext.adder_ext_sv(w, "end_around_carry", pins, name=f"fam_adder_eac_{mtag}_{recirc[:5]}_{topo[:4]}_w{w}")
                out.append((n, t, ("eac", modulus, pval)))
    for scheme in ("truncate_constant", "or_gates", "segmented_subadders", "speculative_segments"):
        for corr in ("none", "configurable_stages"):
            pins = {"lower_part_width": w // 2, "lower_scheme": scheme, "correction": corr, "upper_adder.family": "carry_lookahead"}
            n, t = adder_ext.adder_ext_sv(w, "approximate_truncated", pins, name=f"fam_adder_trunc_{scheme[:6]}_{corr[:4]}_w{w}")
            out.append((n, t, ("trunc", w // 2)))
    for fam in ("carry_skip", "carry_select", "carry_increment"):
        for bfam in ("ripple_carry", "carry_lookahead", "parallel_prefix", "conditional_sum"):
            pins = {"block_width": 4, "block_adder.family": bfam}
            if bfam == "parallel_prefix":           # the only block family with a topology; validate_pins refuses it elsewhere
                pins["block_adder.topology"] = "sklansky"
            n, t = adder_ext.adder_ext_sv(w, fam, pins, name=f"fam_adder_{fam}_blk_{bfam[:6]}_w{w}")
            out.append((n, t, ("exact",)))
    # the sizing rules, skip levels and gates, select sources and duplications, increment levels
    for rule in ("trapezoidal_variable", "dp_optimized"):
        for lv in (1, 2, 3):
            for gate in ("mux", "and_or_bypass"):
                n, t = adder_ext.adder_ext_sv(w, "carry_skip", {"block_sizing": rule, "skip_levels": lv, "skip_gate": gate},
                                              name=f"fam_adder_skip_{rule[:4]}_l{lv}_{gate[:3]}_w{w}")
                out.append((n, t, ("exact",)))
    for rule in ("square_root_ramp", "delay_balanced_dp", "delay_matched_doubling"):
        for dup in ("full_duplicate", "shared_add_one"):
            for src in ("rippled_block_carries", "lookahead_tree"):
                n, t = adder_ext.adder_ext_sv(w, "carry_select", {"block_sizing": rule, "duplication": dup, "select_source": src,
                                                                  "add_one.structure": "ripple_and_chain"},
                                              name=f"fam_adder_sel_{rule[:5]}_{dup[:4]}_{src[:4]}_w{w}")
                out.append((n, t, ("exact",)))
    for rule in ("uniform", "variable_ramp"):
        for lv in (1, 2):
            for inter in ("rippled", "lookahead_tree"):
                n, t = adder_ext.adder_ext_sv(w, "carry_increment", {"block_sizing": rule, "increment_levels": lv, "intergroup_carry": inter,
                                                                     "increment_stage.structure": "prefix_and_tree"},
                                              name=f"fam_adder_inc_{rule[:4]}_l{lv}_{inter[:4]}_w{w}")
                out.append((n, t, ("exact",)))
    for sp in (1, 2):
        for style in ("carry_select", "conditional_sum", "ripple_precompute"):
            for topo, val in (("sklansky", 2), ("kogge_stone", 3), ("han_carlson", 2)):
                n, t = adder_ext.adder_ext_sv(w, "sparse_prefix_hybrid", {"log2_sparsity": sp, "sum_block_style": style, "tree_topology": topo, "valency": val},
                                              name=f"fam_adder_sparse_s{sp}_{style[:4]}_{topo[:4]}{val}_w{w}")
                out.append((n, t, ("exact",)))
    # the prefix overlay needs two chain segments at least
    n, t = adder_ext.adder_ext_sv(w, "fpga_carry_chain", {"prefix_over_chain": True, "chain_segment_length": min(8, w // 2)},
                                  name=f"fam_adder_fpga_overlay_w{w}")
    out.append((n, t, ("exact",)))
    return out


def approx_cases(w):
    """(module name, text, bench) of the approximate-unit families: the
    adders under an absolute bound in units of 2^(w/2), the multipliers
    under a relative or absolute bound (relf: relative over products of
    at least 2^(w+2)), the dividers under a relative bound with one unit
    (or the pruned depth) of slack."""
    from chialu.targets.rtl.families import approx
    adders = [("segmented_carry_speculative", {"sub_adder_width": "W2"}, "seg", 2.0, 0.6),
              ("segmented_carry_speculative", {"sub_adder_width": "W2", "carry_in_scheme": "carry_select_speculation", "correction": "error_reduction_stage"}, "seg_csel_err", 2.0, 0.6),
              ("segmented_carry_speculative", {"sub_adder_width": "W2", "carry_in_scheme": "carry_cut_back", "correction": "sign_repair"}, "seg_cut_sign", 2.0, 0.6),
              ("lower_part_approximate", {}, "lpa_or", 2.0, 0.6), ("lower_part_approximate", {"lower_cell": "xor_xnor_axa", "carry_to_upper": "msb_and"}, "lpa_axa", 2.0, 0.6),
              ("lower_part_approximate", {"lower_cell": "approx_mirror_ama", "carry_to_upper": "window_speculation"}, "lpa_ama", 2.0, 0.6),
              ("lower_part_approximate", {"lower_cell": "inexact_cell_inxa"}, "lpa_inxa", 2.0, 0.6), ("lower_part_approximate", {"lower_cell": "reverse_carry_rcpa"}, "lpa_rcpa", 2.0, 0.6),
              ("accuracy_configurable", {}, "acc", 8.0, 3.0)]
    muls = [("truncated_fixed_width", {"correction": "min_max"}, "trunc_mm", "abs", 2.5, 0.6), ("truncated_fixed_width", {"correction": "linear_regression"}, "trunc_lr", "abs", 2.5, 0.6),
            ("dynamic_segment", {}, "ds", "rel", 0.07, 0.02),
            ("dynamic_segment", {"segment_select": "dynamic_leading_one_rounded", "unbiasing": "round_and_correct", "small_operand_fallback": True}, "ds_round", "rel", 0.1, 0.03),
            ("dynamic_segment", {"segment_width": "WM2", "segment_select": "static_msb_or_lsb", "unbiasing": "poc_cascade_fill"}, "ds_static", "abs", 8.0, 2.0),
            ("operand_rounding", {}, "roba", "rel", 0.13, 0.04), ("operand_rounding", {"rounding": "nearest_pow2", "bias_correction": True}, "roba_p2", "rel", 1.0, 0.35),
            ("logarithmic", {}, "lg", "rel", 0.12, 0.05), ("logarithmic", {"base": "mitchell_unbiased", "correction": "piecewise_terms"}, "lg_unb", "rel", 0.2, 0.06),
            ("logarithmic", {"mantissa_adder": "truncated"}, "lg_trunc", "relf", 0.13, 0.05), ("logarithmic", {"correction": "iterative_residual", "iterations": 2}, "lg_it2", "rel", 0.12, 0.02),
            ("logarithmic", {"base": "double_sided", "mantissa_adder": "set_one_soa"}, "lg_ds", "relf", 0.15, 0.05),
            ("logarithmic", {"correction": "operand_decomposition"}, "lg_od", "rel", 0.12, 0.03), ("logarithmic", {"correction": "near_zero_bias_coefficients"}, "lg_nzb", "rel", 0.2, 0.05),
            ("pp_perforation", {}, "perf", "abs", 3.5, 2.0), ("pp_perforation", {"correction": "constant"}, "perf_c", "abs", 3.5, 2.0),
            ("pp_perforation", {"correction": "error_correction_vector"}, "perf_ecv", "abs", 3.5, 2.0),
            ("pp_perforation", {"correction": "probabilistic_compensation", "perforated_rows": 3}, "perf_pc", "abs", 8.0, 3.0),
            ("approximate_compressor_tree", {}, "act", "abs", 6.0, 2.0),
            ("approximate_compressor_tree", {"compressor": "yang_inexact", "error_recovery": "compensation_module"}, "act_or", "abs", 6.0, 1.2),
            ("approximate_compressor_tree", {"compressor": "esposito_unbiased", "error_recovery": "or_based"}, "act_unb", "abs", 6.0, 2.0),
            ("approximate_booth", {}, "abooth", "abs", 2.0, 0.5), ("approximate_booth", {"encoder": "abe2"}, "abooth2", "abs", 2.0, 0.5),
            ("approximate_booth", {"radix": 8, "encoder": "truncated_hard_multiple"}, "abooth8", "abs", 2.0, 0.5)]
    divs = [("approximate_recurrence", {}, "arec", 1.0, 0.08), ("approximate_recurrence", {"cell": "axsc2"}, "arec2", 1.0, 0.08),
            ("approximate_recurrence", {"cell": "axsc3"}, "arec3", 1.0, 0.08), ("approximate_recurrence", {"adaptive_pruning": True, "replaced_depth": 2}, "arec_p", 1.0, 0.08),
            ("approximate_functional", {}, "afun", 0.15, 0.03), ("approximate_functional", {"method": "divisor_round_pow2_lut"}, "afun_lut", 0.15, 0.03),
            ("approximate_functional", {"method": "dynamic_segment_exact_core"}, "afun_ds", 0.2, 0.05),
            ("approximate_functional", {"method": "log_subtract_corrected", "bias_correction": True}, "afun_log", 0.3, 0.08),
            ("approximate_functional", {"method": "iterative_quasi_convergence"}, "afun_gs", 0.1, 0.02)]
    out = []
    for fam, pins, tag, mx, mn in adders:
        pins = {k: (w // 2 if v == "W2" else v) for k, v in pins.items()}
        n, t = approx.approx_sv("adder", fam, pins, w, name=f"fam_adder_{tag}_w{w}")
        out.append((n, t, ("add", mx, mn)))
    for signed in (False, True):
        for fam, pins, tag, kind, mx, mn in muls:
            pins = {k: (w - 2 if v == "WM2" else v) for k, v in pins.items()}
            n, t = approx.approx_sv("multiplier", fam, pins, w, signed, name=f"fam_mul_{tag}_w{w}_{'s' if signed else 'u'}")
            out.append((n, t, ("mul", signed, kind, mx, mn)))
    for fam, pins, tag, mx, mn in divs:
        n, t = approx.approx_sv("divider", fam, pins, w, name=f"fam_div_{tag}_w{w}")
        slack = (1 << int(pins.get("replaced_depth", 4))) if (pins.get("adaptive_pruning") or pins.get("cell", "axsc1") != "axsc3") and fam == "approximate_recurrence" else 1
        out.append((n, t, ("div", mx, mn, slack)))
    return out


def subword_cases(w):
    """(module name, text, bench) of the unit-level sharing modules: the
    twin-precision multiplier over the packings w, w/2 and w/4 against
    the per-lane products, the partitioned adder over the same packings
    against the per-lane sums."""
    from chialu.targets.rtl.families import subword
    lws = [w, w // 2, w // 4] if w >= 8 else [w, w // 2]
    out = []
    for sgs, tag in (([True] * len(lws), "s"), ([False] * len(lws), "u"), ([True, False] + [True] * (len(lws) - 2), "m")):
        n, t = subword.twin_precision_sv(w, lws, sgs, {"lane_cpa.family": "carry_lookahead"} if tag == "m" else {}, name=f"fam_mul_twin_{tag}_w{w}")
        out.append((n, t, ("twin", lws, sgs)))
    for mech in ("carry_kill_gate", "carry_select_mux", "guard_bit_insertion"):
        mtag = {"carry_kill_gate": "kill", "carry_select_mux": "select", "guard_bit_insertion": "guard"}[mech]
        n, t = subword.partitioned_adder_sv(w, lws, {"boundary_mechanism": mech}, name=f"fam_add_part_{mtag}_w{w}",
                                            segment=("carry_lookahead", {}))
        out.append((n, t, ("part", lws)))
    return out


def redundant_cases(w):
    """(module name, text, bench) of the core-family lane modules
    (families/redundant.py): the signed-digit, hybrid and carry-save
    adders of a redundant_internal core over their pins, and the RNS
    adder, multiplier and comparator of an rns_internal core under each
    channels family; a bench per interface (the adder, multiplier and
    comparator benches)."""
    from chialu.targets.rtl.families import redundant as R
    out = []
    for r in (2, 4, 8, 16):
        for red in ("minimal", "intermediate", "maximal"):
            for enc, conv, sch in (("sign_magnitude", "cpa", "carry_free"), ("twos_complement", "on_the_fly", "carry_free"),
                                   ("borrow_save", "cpa", "two_stage_limited_carry"), ("one_hot", "on_the_fly", "two_stage_limited_carry")):
                if red != "minimal" and enc not in ("sign_magnitude", "one_hot"):
                    continue
                pins = {"radix": r, "redundancy": red, "digit_encoding": enc, "final_conversion": conv, "addition_scheme": sch,
                        "cpa.family": "parallel_prefix", "cpa.topology": "sklansky"}
                n, text = R.representation_adder_sv(w, "generalized_signed_digit", pins)
                out.append((n, text, ("adder",)))
    # the interior adder spans a run of sd_position_spacing - 1 bits, and the last run is shorter where the spacing
    # does not divide the width: carry_select (a block adder) has no module at those runs, so the cases stay
    # with the ripple and prefix interiors
    for d, uni, ia in ((1, True, "ripple"), (3, True, "ripple"), (4, False, "ripple"), (8, True, "prefix"), (8, False, "prefix")):
        n, text = R.representation_adder_sv(w, "hybrid_signed_digit", {"sd_position_spacing": d, "spacing_uniform": uni, "interior_adder": ia})
        out.append((n, text, ("adder",)))
    for comp, corr in (("3_2", False), ("4_2", True), ("5_3", False), ("7_3", True)):
        n, text = R.representation_adder_sv(w, "carry_save_datapath", {"compressor": comp, "carry_overflow_correction": corr, "assimilator.family": "ripple_carry"})
        out.append((n, text, ("adder",)))
    rns = [("rns_channel_arithmetic", {"modulus_form": f, "pow2_plus_1_encoding": e, "multiplier_reduction": mr}, f"chan_{f[:6]}_{e[:3]}_{mr[:4]}")
           for f, e, mr in (("pow2", "normal", "rom"), ("pow2_plus_1", "diminished_one", "csa_with_periodic_folding"),
                            ("pow2_minus_1", "normal", "booth_modular"), ("generic", "normal", "iterative_carry_save_msd_estimate"))]
    rns += [("rns_forward_converter", {"implementation": im, "chunk_bits": cb, "final_reduction": fr, "moduli_count": mc}, f"fwd_{im[:5]}_c{cb}_m{mc}")
            for im, cb, fr, mc in (("rom_per_chunk", 4, "modular_adder", 3), ("segmented_rom_modular_add", 2, "rom", 4),
                                   ("periodic_csa_moma", 4, "modular_adder", 5), ("channel_modular_mac", 3, "modular_adder", 3))]
    rns += [("rns_reverse_converter", {"algorithm": al, "implementation": im, "moduli_count": mc}, f"rev_{al}_{im[:3]}_m{mc}")
            for al, im, mc in (("crt", "rom", 3), ("crt", "adder_based", 4), ("mixed_radix", "rom", 5), ("new_crt_i", "adder_based", 3), ("new_crt_ii", "rom", 4))]
    for fam, pins, tag in rns:
        for kind, sg in (("adder", False), ("multiplier", True), ("multiplier", False)):
            if fam == "rns_forward_converter" and kind != "adder":
                continue
            n, text = R.rns_sv(kind, w, fam, pins, sg, name=f"fam_rns_{kind[:3]}_{tag}_w{w}{'s' if sg else 'u'}")
            out.append((n, text, (kind, sg)))
    for meth, ex in (("rom_mrc", "exact"), ("crt_fraction_estimate", "exact"), ("crt_fraction_estimate", "approximate_with_correction"), ("diagonal_function", "exact")):
        for sg in (True, False):
            n, text = R.rns_sv("comparator", w, "rns_scaling_comparison", {"method": meth, "exactness": ex}, sg,
                               name=f"fam_rns_cmp_{meth[:6]}_{ex[:3]}_w{w}{'s' if sg else 'u'}")
            out.append((n, text, ("comparator", sg)))
    return out


def div_cases(w):
    """(module name, text, N, D, Q, S) of the divider families: the digit
    recurrences (restoring, nonperforming, nonrestoring, SRT radix 2
    carry-save and assimilated, radix-4 and radix-16 stages by table and
    by comparators in their encodings and foldings, the overlapped
    radix-32, the shared recurrence speculated, on-line at both radices),
    the functional dividers over every seed family and the three final
    roundings, the prescaled recurrences, each at the integer geometry
    and a few at the float significand geometry (the dividend shifted by
    the width, one more quotient bit)."""
    from chialu.targets.rtl.families import div
    ds = "digit_select."
    fams = [("restoring_nonrestoring", {"style": "restoring"}, "rest"),
            ("restoring_nonrestoring", {"style": "nonperforming"}, "nonperf"),
            ("restoring_nonrestoring", {"style": "nonrestoring", "residual_adder.family": "carry_lookahead"}, "nonrest_cla"),
            ("srt_radix2", {}, "srt2_cs"),
            ("srt_radix2", {"residual_form": "twos_complement_cpa", "quotient_conversion": "separate_positive_negative"}, "srt2_cpa"),
            ("srt_radix2", {ds + "family": "comparator_digit_selection", ds + "symmetry_folding": True}, "srt2_cmp_fold"),
            ("srt_high_radix", {"radix": 4}, "srt4"),
            ("srt_high_radix", {"radix": 4, "digit_redundancy": "maximal", ds + "digit_encoding": "gray", ds + "folding": "signed_magnitude"}, "srt4_max_gray_fold"),
            ("srt_high_radix", {"radix": 8, "residual_form": "irredundant", ds + "digit_encoding": "line"}, "srt8_irr_line"),
            ("srt_high_radix", {"radix": 16, ds + "family": "comparator_digit_selection"}, "srt16_cmp"),
            ("srt_high_radix", {"radix": 4, ds + "family": "comparator_digit_selection", ds + "residual_input": "redundant_two_word",
                                ds + "output_encoding": "one_hot", ds + "speculative_candidate_residuals": True}, "srt4_cmp_red_oh"),
            ("srt_high_radix", {"radix": 32, "overlapped_stages": 2, ds + "digit_encoding": "choose_highest"}, "srt32_ov2"),
            ("newton_raphson", {}, "nr"),
            ("newton_raphson", {"seed.family": "bipartite_rom", "iteration_order": 3, "iter_mult.family": "direct_pp_parallel"}, "nr_bip3"),
            ("newton_raphson", {"seed.family": "symmetric_bipartite", "final_round.family": "exclusion_zone_proof"}, "nr_sym_excl"),
            ("newton_raphson", {"seed.family": "multipartite", "seed.tables": 3, "seed.input_bits": 7}, "nr_multi"),
            ("newton_raphson", {"seed.family": "operand_modification_multiply", "seed.input_bits": 4}, "nr_opmod"),
            ("newton_raphson", {"seed.family": "magic_constant_bit_seed", "final_round.quotient_candidates": 2}, "nr_magic"),
            ("goldschmidt", {"seed.family": "poly_seed", "seed.degree": 2, "final_round.family": "extra_precision_quotient"}, "gs_poly_extra"),
            ("goldschmidt", {"iterations": 2, "truncated_intermediate_multiplies": False, "final_round.product_bits": "low_bits_sufficient"}, "gs2_round_low"),
            ("direct_polynomial", {"approximator.degree": 2, "approximator.input_bits": 6}, "poly"),
            ("direct_polynomial", {"composition": "polynomial_plus_iteration", "approximator.slope_encoding": "booth_radix8_decoded"}, "poly_it_booth"),
            ("prescaled_very_high_radix", {"bits_per_iteration": 4, "seed.family": "bipartite_rom"}, "presc4"),
            ("svoboda_tung", {"radix": 16}, "svob16"),
            ("svoboda_tung", {"radix": 8, "msd_recoding": "two_digit_recode"}, "svob8_rec"),
            ("online_msdf", {}, "online"),
            ("online_msdf", {"radix": 4}, "online4")]
    if w <= 12:
        # the speculated radix-16 recurrence is 32 selections per iteration: it simulates slowly above 12 bits
        fams.append(("digit_recurrence_sqrt_combined", {"radix": 16, "speculation_between_subiterations": True,
                                                        "on_the_fly_conversion": False}, "drc16_spec"))
    out = []
    for fam, pins, tag in fams:
        name, text = div.div_sv(w, w, w, fam, pins, name=f"fam_div_{tag}_w{w}")
        out.append((name, text, w, w, w, 0))
    for fam, pins, tag in (("restoring_nonrestoring", {}, "rest"), ("srt_radix2", {}, "srt2"), ("srt_high_radix", {}, "srt4"),
                           ("newton_raphson", {}, "nr"), ("goldschmidt", {}, "gs"),
                           ("prescaled_very_high_radix", {}, "presc")) + ((("online_msdf", {}, "online"),) if w <= 12 else ()):
        name, text = div.div_sv(w, w, w + 1, fam, pins, name=f"fam_divs_{tag}_w{w}", S=w)
        out.append((name, text, w, w, w + 1, w))
    return out


def sqrt_cases(w):
    """(module name, text, normalized) of the square roots: the restoring
    recurrence, the SRT recurrences (radix 2, 4, 16 and 64, by table and
    by comparators, the root on the fly or as Q+ - Q-) and the
    functional families, over a normalized and an arbitrary radicand."""
    from chialu.targets.rtl.families import div
    ds = "digit_select."
    # the recurrence roots of an unnormalized radicand and the bipartite seed simulate slowly (the per-stage
    # tables and the de-scaled root's square), so those run at the smaller widths
    slow = w > 12
    out = []
    for fam, pins, tag in (("restoring_nonrestoring", {}, "rest"),
                           ("digit_recurrence_sqrt_combined", {}, "dr"),
                           ("digit_recurrence_sqrt_combined", {"radix": 4, "on_the_fly_conversion": False}, "dr4_qpn"),
                           ("digit_recurrence_sqrt_combined", {"radix": 16, ds + "family": "comparator_digit_selection"}, "dr16_cmp"),
                           ("digit_recurrence_sqrt_combined", {"radix": 64}, "dr64"),
                           ("srt_high_radix", {"radix": 4, "digit_redundancy": "maximal"}, "srt4_max"),
                           ("newton_raphson", {}, "nr"), ("goldschmidt", {}, "gs"),
                           ("direct_polynomial", {"approximator.degree": 2}, "poly"),
                           ("newton_raphson", {"seed.family": "bipartite_rom", "iter_mult.family": "direct_pp_parallel"}, "nr_bip")):
        for norm in (False, True):
            if norm and fam == "restoring_nonrestoring":
                continue
            if slow and (tag == "nr_bip" or (not norm and tag in ("dr", "dr4_qpn", "dr64"))):
                continue
            name, text = div.sqrt_sv(w, fam, pins, name=f"fam_sqrt_{tag}_w{w}_{'n' if norm else 'u'}", normalized=norm)
            out.append((name, text, norm))
    return out


def shifter_cases(w):
    out = [("fam_shift_barrel_mux_tree", {"W": w, "RADIX_LOG2": rl, "ONE_HOT": oh, "DIR": d, "ORDER": o})
           for d in (0, 1, 2) for rl, oh, o in ((1, 0, 0), (2, 1, 0), (3, 0, 1), (0, 0, 0))]
    out += [("fam_shift_funnel", {"W": w, "RADIX_LOG2": rl, "AMT_PRE": pre}) for rl in (1, 2) for pre in (0, 1)]
    out += [("fam_shift_masked_merged", {"W": w, "MASKGEN": mg, "MERGE": me, "R_RADIX_LOG2": 1 + me, "R_ONE_HOT": me, "R_ORDER": 0})
            for mg in (0, 1, 2) for me in (0, 1)]
    if w & (w - 1) == 0:
        out += [("fam_shift_butterfly_network", {"W": w, "NETWORK": nw}) for nw in (0, 1)]
    return out


def cmp_cases(w):
    """The comparator modules: [(module, params)] of the parametric prefix
    comparator, and [(module, params, text)] of the generated subtractor
    comparators over two adder families."""
    out = [("fam_cmp_prefix_comparator", {"W": w, "SIGNED": s, "STRUCTURE": st, "RADIX": r}) for s in (0, 1) for st in (0, 1) for r in (2, 3, 4)]
    from chialu.targets.rtl.families import comparator_module
    for s in (0, 1):
        for fam, pins in (("ripple_carry", {}), ("parallel_prefix", {"subtractor.topology": "sklansky"}), ("carry_lookahead", {"zero_detect": "operand_xnor"})):
            m = comparator_module("subtractor_comparator", dict(pins, **{"subtractor.family": fam}), w, bool(s))
            out.append((m.name, {"SIGNED": s}, m.text))
    return out


def logic_cases(w):
    return [("fam_logic_gate_row", {"W": w, "NOT_VIA_XOR": n}) for n in (0, 1)]


def incr_cases(w):
    return [("fam_incr_prefix_and", {"W": w, "STRUCTURE": st, "B": 4, "TOPO": 0}) for st in (0, 2)] + \
           [("fam_incr_prefix_and", {"W": w, "STRUCTURE": 1, "B": 4, "TOPO": t}) for t in (0, 1, 2)]


def count_cases(w):
    """[(module, kind, text)] of the generated bit-count modules over their
    choices (families/count.py)."""
    from chialu.targets.rtl.families import count as C
    cases = []
    for shape in ("balanced_tree", "wallace_style", "linear_chain"):
        for prim in ("full_adder_3_2", "compressor_4_2", "counter_7_3", "lut_rom"):
            cases.append(("popcount_counter_tree", "pop", {"tree_shape": shape, "counter_primitive": prim}))
    cases.append(("popcount_counter_tree", "pop", {"final_adder.family": "parallel_prefix", "final_adder.topology": "sklansky"}))
    # the end-around-carry final adder enters through its binary decode (a modular sum would miscount)
    cases.append(("popcount_counter_tree", "pop", {"final_adder.family": "end_around_carry"}))
    cases.append(("popcount_counter_tree", "pop", {"tree_shape": "wallace_style", "final_adder.family": "end_around_carry",
                                                   "final_adder.modulus": "mod_2n_plus_1_diminished_one", "final_adder.recirculation": "select_based"}))
    cases.append(("prefix_lzc", "lz", {"counter.final_adder.family": "end_around_carry"}))
    for prim in ("pair_cell", "nibble_cell"):
        for form in ("binary_count", "one_hot_shift_controls"):
            cases.append(("lzd_cell_tree", "lz", {"block_primitive": prim, "output_form": form, "valid_flag_propagation": prim == "pair_cell"}))
    for topo in ("kogge_stone", "sklansky", "brent_kung"):
        for cf in ("popcount_of_complement", "lookahead_flags"):
            cases.append(("prefix_lzc", "lz", {"prefix_topology": topo, "count_form": cf}))
    for G, lv, form in ((4, 1, "direct_binary"), (4, 2, "one_hot_then_encode"), (8, 3, "direct_binary"), (4, 3, "one_hot_then_encode")):
        cases.append(("priority_encoder", "lz", {"lookahead_group": G, "levels": lv, "output_form": form}))
    for st in ("reverse_then_lzd", "isolate_then_encode", "debruijn_multiply_index"):
        for iso in ("twos_complement_and", "ripple_kill_chain"):
            cases.append(("trailing_zero", "tz", {"strategy": st, "isolate_circuit": iso}))
    cases.append(("trailing_zero", "tz", {"strategy": "reverse_then_lzd", "lzd.family": "prefix_lzc"}))
    out, seen = [], set()
    for fam, kind, pins in cases:
        name, text = C.count_sv(fam, w, pins)
        if name in seen:
            continue
        seen.add(name)
        out.append((name, kind, text))
    return out


def bcd_cases(w):
    """(module name, text, kind) of the decimal families at w / 4 digits:
    the four adder families over their digit codes, corrections, carry
    schemes, subtraction forms, digit sets and conversions, the parallel
    multiplier over its recodings, internal codes, generation styles and
    trees, the dividers over their digit sets and final roundings (the
    redundant recurrences and the Newton dividers at two and four digits
    only: their prescaling and iteration multipliers simulate slowly)."""
    from chialu.targets.rtl.families import decimal
    D = w // 4
    adders = [("bcd_direct_addition", {}, "dir"),
              ("bcd_direct_addition", {"correction_placement": "postsum_plus6", "carry_scheme": "digit_group_lookahead"}, "dir_post_grp"),
              ("bcd_direct_addition", {"correction_placement": "direct_decimal_carry_logic", "carry_scheme": "full_lookahead"}, "dir_dcl_full"),
              ("bcd_direct_addition", {"digit_code": "excess3", "carry_scheme": "full_lookahead"}, "dir_xs3"),
              ("bcd_direct_addition", {"subtraction": "nines_complement_end_around_carry"}, "dir_eac"),
              ("bcd_direct_addition", {"subtraction": "direct_borrow_subtracter", "digit_adder.family": "carry_lookahead"}, "dir_borrow"),
              ("bcd_direct_addition", {"complement_generation": "trailing_zero_scan"}, "dir_scan"),
              ("bcd_direct_addition", {"complement_generation": "nines_digitwise_plus_one", "subtraction": "nines_complement_end_around_carry"}, "dir_dw_eac"),
              ("speculative_decimal_addition", {}, "spec"),
              ("speculative_decimal_addition", {"recovery": "dual_path_select", "speculation_target": "both", "carry_network.family": "carry_lookahead"}, "spec_dual"),
              ("speculative_decimal_addition", {"fused_ieee_rounding": True, "carry_network.topology": "brent_kung"}, "spec_fused"),
              ("redundant_decimal_addition", {}, "red_svob"),
              ("redundant_decimal_addition", {"digit_set": "rbcd_m7_p7", "operands_redundant": "both", "final_conversion": "on_the_fly"}, "red_rbcd"),
              ("redundant_decimal_addition", {"digit_set": "maximally_redundant_m9_p9", "operands_redundant": "both"}, "red_max"),
              ("redundant_decimal_addition", {"digit_set": "overloaded_0_15", "final_conversion": "on_the_fly"}, "red_odds"),
              ("decimal_multioperand_addition", {}, "mop_csa"),
              ("decimal_multioperand_addition", {"correction_placement": "at_root"}, "mop_root"),
              ("decimal_multioperand_addition", {"reduction_style": "binary_tree_then_convert"}, "mop_bin"),
              ("decimal_multioperand_addition", {"reduction_style": "decimal_compressors", "compressor_arity": "4_to_2", "root_adder.family": "parallel_prefix"}, "mop_42"),
              ("decimal_multioperand_addition", {"reduction_style": "signed_digit_binary_compressors"}, "mop_4221")]
    muls = [("parallel_decimal_multiplication", {}, "sd_lin"),
            ("parallel_decimal_multiplication", {"multiplier_recoding": "none", "reduction_tree.family": "csa_tree", "reduction_tree.compressor": "7:3"}, "none_73"),
            ("parallel_decimal_multiplication", {"multiplier_recoding": "radix4_radix5_split", "reduction_tree.family": "binary_tree"}, "split_bt"),
            ("parallel_decimal_multiplication", {"internal_digit_code": "bcd4221", "reduction_tree.family": "csa_tree"}, "c4221"),
            ("parallel_decimal_multiplication", {"internal_digit_code": "bcd5211", "reduction_tree.family": "csa_tree", "reduction_tree.compressor": "4:2"}, "c5211"),
            ("parallel_decimal_multiplication", {"internal_digit_code": "xs3_odds", "multiplier_recoding": "radix4_radix5_split"}, "xs3"),
            ("parallel_decimal_multiplication", {"internal_digit_code": "sd_m8_p8_posibit_negabit", "reduction_tree.family": "csa_tree"}, "sd8"),
            ("parallel_decimal_multiplication", {"pp_generation": "digit_by_digit", "final_adder.family": "parallel_prefix"}, "dbd"),
            ("parallel_decimal_multiplication", {"pp_generation": "digit_by_digit", "internal_digit_code": "bcd4221", "multiplier_recoding": "none"}, "dbd_4221")]
    divs = [("decimal_digit_recurrence", {}, "rec", False),
            ("decimal_digit_recurrence", {"digit_split": "radix2_times_radix5"}, "rec_split", False)]
    if D <= 4:
        # the prescaled recurrences and the Newton dividers chain several products: an event simulator re-evaluates the
        # chain per settling event, so they take a light vector set
        divs += [("decimal_digit_recurrence", {"quotient_digit_set": "redundant_m7_p7"}, "rec_m7", True),
                 ("decimal_digit_recurrence", {"quotient_digit_set": "minimally_redundant_m5_p5", "divisor_prescaling": True}, "rec_m5", True),
                 ("decimal_newton", {}, "nr", True),
                 ("decimal_newton", {"seed_digits": 3, "iterations": 2, "final_round.family": "exclusion_zone_proof"}, "nr_excl", True)]
    out = []
    for fam, pins, tag in adders:
        n, t = decimal.bcd_adder_sv(D, fam, pins, name=f"fam_bcd_{tag}_d{D}")
        out.append((n, t, "adder"))
    for fam, pins, tag in muls:
        n, t = decimal.bcd_mul_sv(D, fam, pins, name=f"fam_bcd_mul_{tag}_d{D}")
        out.append((n, t, "mul"))
    for fam, pins, tag, light in divs:
        n, t = decimal.bcd_div_sv(D, fam, pins, name=f"fam_bcd_div_{tag}_d{D}")
        out.append((n, t, "div_light" if light else "div"))
    return out


def _bench(module, params, adapter):
    from chialu.verify.family_tb import emit
    return emit(module, params, adapter, N_RANDOM, STIMULUS_SEED)


def tb_mul(module, w, signed):
    from chialu.verify.family_ref import golden
    return _bench(module, {}, golden("multiplier", "behavioral_star", {"_signed": signed}, w))


def tb_mul_bound(module, w, signed, kind, max_err, mean_err, minimum=0, scale=None):
    from chialu.verify.family_ref import golden, Tolerance
    adapter = golden("multiplier", "behavioral_star", {"_signed": signed}, w)
    adapter.tolerance = Tolerance(max_err, mean_err, ("p",), scale or (1 << w), kind == "rel", signed, minimum)
    return _bench(module, {}, adapter)


def tb_adder(module, params, w, flagged=False):
    from chialu.verify.family_ref import golden
    pins = {"outputs": "sum_sum1_summinus1" if "_flagm" in module else "sum_sum1"}
    adapter = golden("adder", "compound_flagged_prefix" if flagged else "ripple_carry", pins, w)
    return _bench(module, params, adapter)


def tb_eac(module, w, modulus, pmod):
    from chialu.verify.family_ref import golden
    recirculation = "cyclic_prefix_level" if "_cycli_" in module else "two_pass_prefix"
    adapter = golden("adder", "end_around_carry", {"modulus": modulus, "modulus_value": pmod,
                                                 "recirculation": recirculation}, w)
    return _bench(module, {}, adapter)


def tb_add_bound(module, w, k, max_err=2.0, mean_err=0.6, scale=None):
    from chialu.verify.family_ref import golden, Tolerance
    adapter = golden("adder", "ripple_carry", {}, w)
    adapter.tolerance = Tolerance(max_err, mean_err, ("cout", "s"), scale or (1 << k))
    return _bench(module, {}, adapter)


def tb_div(module, N, D, Q, S=0):
    from chialu.verify.family_ref import divider_adapter
    return _bench(module, {}, divider_adapter(N, D, Q, S))


def tb_div_bound(module, N, D, Q, max_rel, mean_rel, slack=1):
    from chialu.verify.family_ref import divider_adapter, Tolerance
    adapter = divider_adapter(N, D, Q)
    adapter.tolerance = Tolerance(max_rel, mean_rel, ("q",), relative=True, slack=slack, unchecked_ports=("r",))
    return _bench(module, {}, adapter)


def tb_sqrt(module, Q, normalized=False):
    from chialu.verify.family_ref import sqrt_adapter
    return _bench(module, {}, sqrt_adapter(Q, normalized))


def tb_twin(module, W, lane_widths, signed):
    from chialu.verify.family_ref import subword_adapter
    return _bench(module, {}, subword_adapter(W, lane_widths, signed))


def tb_part(module, W, lane_widths):
    from chialu.verify.family_ref import subword_adapter
    return _bench(module, {}, subword_adapter(W, lane_widths))


def tb_cmp_plain(module, w, signed):
    from chialu.verify.family_ref import golden
    return _bench(module, {}, golden("comparator", "prefix_comparator", {"_signed": signed}, w))


def tb_cmp(module, params, w):
    from chialu.verify.family_ref import golden
    adapter = golden("comparator", "prefix_comparator", {"_signed": bool(params["SIGNED"])}, w)
    params = {k: v for k, v in params.items() if k != "SIGNED" or module == "fam_cmp_prefix_comparator"}
    return _bench(module, params, adapter)


def tb_shifter(module, params, w):
    from chialu.verify.family_ref import golden
    adapter = golden("shifter", "barrel_mux_tree", {"sticky_collect": bool(params.get("STICKY"))}, w)
    return _bench(module, params, adapter)


def tb_count(module, kind, w):
    from chialu.verify.family_ref import golden
    family = {"pop": "popcount_counter_tree", "lz": "lzd_cell_tree", "tz": "trailing_zero"}[kind]
    return _bench(module, {}, golden("bitcount", family, {}, w))


def tb_incr(module, params, w):
    from chialu.verify.family_ref import golden
    return _bench(module, params, golden("incrementer", "prefix_and_incrementer", {}, w))


def tb_logic(module, params, w):
    from chialu.verify.family_ref import golden
    return _bench(module, params, golden("logic", "wide_gate_row", {}, w))


def tb_bcd_add(module, D):
    from chialu.verify.family_ref import golden
    return _bench(module, {}, golden("bcd_adder", "bcd_direct_addition", {}, 4 * D))


def tb_bcd_mul(module, D):
    from chialu.verify.family_ref import golden
    return _bench(module, {}, golden("bcd_multiplier", "parallel_decimal_multiplication", {}, 4 * D))


def tb_bcd_div(module, D, light=False):
    from chialu.verify.family_ref import golden
    return _bench(module, {}, golden("bcd_divider", "decimal_digit_recurrence", {}, 4 * D))


def run_python_case(lib, name, tb, work, extra=""):
    tb.write(work / name)
    return run_case(lib, name, tb, work, extra)


def python_checks() -> list:
    """The prefix graph's own checks: the compact sequence round-trips
    an exact-split graph, edits keep a graph legal and complete, the
    metrics of the 16-bit named networks are Harris' (levels, size,
    tracks: Kogge-Stone 4/49/8, Sklansky 4/32/1, Brent-Kung 6/26/1,
    Han-Carlson 5/32/4)."""
    out = []
    expect = {"kogge_stone": (4, 49, 8), "sklansky": (4, 32, 1), "brent_kung": (6, 26, 1), "han_carlson": (5, 32, 4)}
    for spec, (lv, sz, tr) in expect.items():
        g = prefix.build(16, spec)
        got = (g.levels(), g.size(), g.tracks())
        out.append(f"prefix_metrics_{spec}: " + ("PASS" if got == (lv, sz, tr) else f"got {got} expected {(lv, sz, tr)}"))
    for n in (8, 16, 24, 33):
        for spec in prefix.NAMED + ("harris:l1f1", "harris:l2f0"):
            g = prefix.build(n, spec)
            if not g.exact_split():          # a Knowles graph with fanout sharing overlaps: no compact notation
                continue
            h = prefix.PrefixGraph.from_sequence(n, g.sequence())
            ok = h.nodes == g.nodes
            out.append(f"prefix_sequence_{spec}_n{n}: " + ("PASS" if ok else "round trip differs"))
        g = prefix.build(n, "brent_kung")
        try:
            prefix.apply_edits(g, f"add {n - 1} 1; remove {n // 2} 0; add {n - 2} 0; remove {n - 1} 0")
            g.validate()
            out.append(f"prefix_edits_n{n}: PASS")
        except ValueError as e:
            out.append(f"prefix_edits_n{n}: {e}")
        for target in (None, n):
            g = prefix.nonuniform_arrival(n, [max(0, n // 4 - abs(i - n // 2) // 2) for i in range(n)], target)
            try:
                g.validate()
                out.append(f"prefix_arrival_n{n}_t{target}: PASS")
            except ValueError as e:
                out.append(f"prefix_arrival_n{n}_t{target}: {e}")
    return out


def run_case(lib: str, name: str, tb: str, work: Path, extra: str = "") -> str:
    """Compile and run one bench: the library modules the bench and the
    generated text reference (transitively), the generated text, the
    bench. `lib` is unused (kept for the callers' signature); the closure
    keeps every compile to what it needs."""
    from chialu.targets.rtl.families import library_closure
    from chialu.verify.sim_artifacts import passing_bench_line
    lib = library_closure(tb + "\n" + extra) + ("\n" + extra if extra else "")
    d = work / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "lib.sv").write_text(lib)
    (d / "tb.sv").write_text(tb)
    srcs = ["lib.sv", "tb.sv"]
    (d / 'actual.hex').unlink(missing_ok=True)
    # the flow's simulator, which reads the SystemVerilog as written (chialu.verify.simulate)
    from chialu.verify import simulate as SIM
    # the compile limit matches a suite worker's Verilator at -j 1 on a loaded host: 300 s failed the wide
    # Kulisch accumulators (a 480-bit binding) under `CHIALU_VERILATOR_JOBS=1 pytest -n 80`
    res = SIM.simulate(srcs[:-1], srcs[-1], d, work="t", compile_timeout=1800, run_timeout=1800)
    if not res.ok and res.phase == "compile":
        return f"{name}: COMPILE FAIL {res.detail[:300]}"
    if not res.ok and "timeout" in res.detail:
        return f"{name}: SIM TIMEOUT (1800 s)"
    out = SIM.bench_lines(res.stdout)
    verdict = out[-1] if out else "no output"
    if not res.ok or not passing_bench_line(verdict):
        return f"{name}: {verdict}; " + " | ".join(out[:2])
    return f"{name}: PASS"


def curated_main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--width", default="8,16,12")
    ap.add_argument("--only", default=None)
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--shard", default=None, help="k/n: the k-th of n interleaved slices of the cases (0-based); "
                                                  "the python checks run in shard 0 alone")
    ap.add_argument("--count", action="store_true", help="print the number of cases and exit")
    args = ap.parse_args(argv)
    if not shutil.which("verilator"):
        print("verilator not on PATH"); return 2
    lib = library_text()
    work = Path(tempfile.mkdtemp(prefix="chialu_families_"))
    jobs = []
    checks = python_checks()
    for w in [int(x) for x in args.width.split(",")]:
        for module, params in adder_cases(w):
            jobs.append((f"{module}_{'_'.join(f'{k}{v}' for k, v in params.items())}", tb_adder(module, params, w)))
        for module, text, flagged in prefix_cases(w):
            jobs.append((module, tb_adder(module, {}, w, flagged), text))
        for module, text, signed in mul_cases(w):
            jobs.append((module, tb_mul(module, w, signed), text))
        for module, params in shifter_cases(w):
            jobs.append((f"{module}_{'_'.join(f'{k}{v}' for k, v in params.items())}", tb_shifter(module, params, w)))
        for case in cmp_cases(w):
            module, params = case[0], case[1]
            jobs.append((f"{module}_{'_'.join(f'{k}{v}' for k, v in params.items())}", tb_cmp(module, params, w), *case[2:]))
        for module, kind, text in count_cases(w):
            jobs.append((module, tb_count(module, kind, w), text))
        for module, params in incr_cases(w):
            jobs.append((f"{module}_{'_'.join(f'{k}{v}' for k, v in params.items())}", tb_incr(module, params, w)))
        for module, params in logic_cases(w):
            jobs.append((f"{module}_{'_'.join(f'{k}{v}' for k, v in params.items())}", tb_logic(module, params, w)))
        # the generated multiplier and adder families at the power-of-two widths (their netlists simulate slowly)
        for module, text, signed, bench in (mul_ext_cases(w) if w & (w - 1) == 0 else []):
            if bench[0] == "exact":
                jobs.append((module, tb_mul(module, w, signed), text))
            else:
                jobs.append((module, tb_mul_bound(module, w, signed, bench[0], bench[1], bench[2]), text))
        for module, text, bench in (approx_cases(w) if w & (w - 1) == 0 else []):
            if bench[0] == "add":
                jobs.append((module, tb_add_bound(module, w, w // 2, bench[1], bench[2]), text))
            elif bench[0] == "mul":
                _k, signed, kind, mx, mn = bench
                tb = tb_mul_bound(module, w, signed, "rel" if kind == "relf" else kind, mx, mn,
                                  minimum=(1 << (w + 2)) if kind == "relf" else 0)
                jobs.append((module, tb, text))
            else:
                jobs.append((module, tb_div_bound(module, w, w, w, bench[1], bench[2], bench[3]), text))
        # the core-family lane modules at 8 and 16 bits (their RNS netlists carry tables)
        for module, text, bench in (redundant_cases(w) if w in (8, 16) else []):
            if bench[0] == "adder":
                jobs.append((module, tb_adder(module, {}, w), text))
            elif bench[0] == "multiplier":
                jobs.append((module, tb_mul(module, w, bench[1]), text))
            else:
                jobs.append((module, tb_cmp_plain(module, w, bench[1]), text))
        for module, text, bench in (subword_cases(w) if w & (w - 1) == 0 and w >= 8 else []):
            if bench[0] == "twin":
                jobs.append((module, tb_twin(module, w, bench[1], bench[2]), text))
            else:
                jobs.append((module, tb_part(module, w, bench[1]), text))
        for module, text, bench in (adder_ext_cases(w) if w & (w - 1) == 0 else []):
            if bench[0] == "eac":
                jobs.append((module, tb_eac(module, w, bench[1], bench[2]), text))
            elif bench[0] == "trunc":
                jobs.append((module, tb_add_bound(module, w, bench[1]), text))
            else:
                jobs.append((module, tb_adder(module, {}, w), text))
        for module, text, N, D, Q, S in div_cases(w):
            jobs.append((module, tb_div(module, N, D, Q, S), text))
        for module, text, norm in sqrt_cases(w):
            jobs.append((module, tb_sqrt(module, w, norm), text))
        # the decimal families at w / 4 digits
        for module, text, kind in (bcd_cases(w) if w % 4 == 0 else []):
            tb = {"adder": tb_bcd_add, "mul": tb_bcd_mul, "div": tb_bcd_div}[kind.split("_")[0]](module, w // 4, *([True] if kind == "div_light" else []))
            jobs.append((module, tb, text))
    if args.only:
        jobs = [j for j in jobs if args.only in j[0]]
    if args.count:
        print(len(jobs))
        return 0
    if args.shard:
        k, n = (int(x) for x in args.shard.split("/"))
        jobs = jobs[k::n]
        if k != 0:
            checks = []
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        results = list(pool.map(lambda j: run_python_case(lib, j[0], j[1], work, *j[2:]), jobs))
    results = checks + results
    fails = [r for r in results if "PASS" not in r]
    for r in fails:
        print("  " + r[:300])
    print(f"[families selftest] {len(results) - len(fails)}/{len(results)} pass ({work})")
    return 1 if fails else 0


def space_points(kinds, widths, sample, seed):
    """Select every family baseline and a seeded sample per kind and width."""
    from chialu import synthdb
    for kind in kinds:
        for width in widths:
            points = synthdb.points(kind, width)
            if sample is not None:
                bases, slots, seen = [], [], set()
                for point in points:
                    family = point[0]
                    if family not in seen:
                        bases.append(point)
                        seen.add(family)
                    else:
                        slots.append(point)
                rng = random.Random(f"{seed}:{kind}:{width}")
                chosen = set(rng.sample(range(len(slots)), min(sample, len(slots))))
                points = bases + [p for i, p in enumerate(slots) if i in chosen]
            for family, pins, label in points:
                yield kind, width, family, pins, label


def space_bench(kind, family, pins, width, module, adapter):
    """Generate the port-driven bench with its deferred Python vectors."""
    return _bench(module.name, module.params, adapter)


def run_space_case(point, work):
    """Realize and simulate one point, recording failures and converter skips."""
    from chialu.characterize import realize
    from chialu.targets.rtl.families import library_closure
    from chialu.verify.family_ref import golden, no_golden_reason
    kind, width, family, pins, label = point
    key = json.dumps([kind, width, family, pins], sort_keys=True)
    name = f"{kind}_{family}_w{width}_" + hashlib.sha256(key.encode()).hexdigest()[:12]
    result = dict(kind=kind, width=width, family=family, pins=pins, label=label, name=name)
    try:
        module = realize(kind, family, pins, width)
    except Exception as error:  # noqa: BLE001 - a point the database offers and the family rejects at this width
        return dict(result, status="rejected", reason=f"{type(error).__name__}: {str(error)[:300]}")
    if module is None:
        return dict(result, status="unrealized")
    try:
        adapter = golden(kind, family, pins, width)
    except Exception as error:  # noqa: BLE001 - the golden model rejects a pins combination the database offers
        return dict(result, status="rejected", reason=f"golden: {type(error).__name__}: {str(error)[:300]}")
    if adapter is None:
        return dict(result, status="no_golden", reason=no_golden_reason(kind, family, pins, width))
    tb = space_bench(kind, family, pins, width, module, adapter)
    size = len((library_closure(tb + "\n" + (module.text or "")) + (module.text or "")).encode())
    try:
        verdict = run_python_case("", name, tb, work, module.text or "")
    except subprocess.TimeoutExpired as error:
        return dict(result, status="fail", size_bytes=size,
                    reason=f"{error.cmd[0]} timeout after {error.timeout}s")
    status = "pass" if verdict.endswith(": PASS") else "fail"
    return dict(result, status=status, size_bytes=size, reason=verdict)


def _worker_vectors(n, seed):
    """Configure each process's vector count and seed."""
    global N_RANDOM, STIMULUS_SEED
    N_RANDOM, STIMULUS_SEED = n, seed


def main(argv=None) -> int:
    global N_RANDOM, STIMULUS_SEED
    from chialu import synthdb
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", choices=("space", "curated"), default="space")
    ap.add_argument("--kinds", help="comma-separated database kinds; an explicit scope defaults to all points")
    ap.add_argument("--widths", "--width", dest="widths", help="comma-separated widths")
    ap.add_argument("--sample", type=int, help="slot points per kind and width, in addition to family baselines")
    ap.add_argument("--all", action="store_true", help="all points; the nightly invocation uses --cases space --all")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--vectors", type=int, default=256, help="random vectors per space point, in addition to corners")
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--only", help="retain curated case names containing this text")
    ap.add_argument("--shard", default=None, help="k/n: the k-th of n interleaved slices of the space points (0-based)")
    ap.add_argument("--count", action="store_true", help="print the number of selected space points and exit")
    args = ap.parse_args(argv)
    if args.jobs < 1 or (args.sample is not None and args.sample < 0):
        ap.error("jobs must be positive and sample must be nonnegative")
    if args.cases == "curated":
        options = ["--width", args.widths or "8,16,12", "--jobs", str(args.jobs)]
        if args.only:
            options += ["--only", args.only]
        return curated_main(options)
    if args.vectors < 1:
        ap.error("vectors must be positive")
    N_RANDOM = args.vectors
    STIMULUS_SEED = args.seed
    for tool in ("verilator",):
        if not shutil.which(tool):
            print(f"{tool} not on PATH")
            return 2
    kinds = args.kinds.split(",") if args.kinds else synthdb.KINDS_WITH_POINTS
    if set(kinds) - set(synthdb.KINDS_WITH_POINTS):
        ap.error("unknown kind")
    widths = [int(w) for w in args.widths.split(",")] if args.widths else synthdb.DENSE_WIDTHS
    if any(w < 4 for w in widths):
        ap.error("widths must be at least 4")
    sample = args.sample
    if sample is None and not (args.all or args.kinds or args.widths):
        sample = 8
    work = Path(tempfile.mkdtemp(prefix="chialu_space_"))
    points = list(space_points(kinds, widths, None if args.all else sample, args.seed))
    if args.count:
        print(len(points))
        return 0
    if args.shard:
        k, n = (int(x) for x in args.shard.split("/"))
        points = points[k::n]
    print(f"[family space] {len(points)} selected points ({work})", flush=True)
    assert len({json.dumps(p[:4], sort_keys=True) for p in points}) == len(points)
    results = []
    with (work / "results.jsonl").open("w") as log, ProcessPoolExecutor(
            max_workers=args.jobs, initializer=_worker_vectors, initargs=(N_RANDOM, STIMULUS_SEED)) as pool:
        for result in pool.map(partial(run_space_case, work=work), points):
            log.write(json.dumps(result) + "\n")
            log.flush()
            results.append(result)
            if result["status"] in ("fail", "skipped", "rejected"):
                print(f"{result['status'].upper()} {result['name']} {result.get('size_bytes', 0)} bytes: {result['reason']}", flush=True)
            if len(results) % 100 == 0:
                print(f"[family space] {len(results)}/{len(points)} complete", flush=True)
    counts = {status: sum(r["status"] == status for r in results)
              for status in ("pass", "fail", "skipped", "unrealized", "no_golden", "rejected")}
    eligible = len(points) - counts["unrealized"] - counts["no_golden"] - counts["rejected"]
    assert eligible == counts["pass"] + counts["fail"] + counts["skipped"]
    print(f"[family space] {counts}; {eligible} eligible cases ({work})")
    return int(bool(counts["fail"]))


if __name__ == "__main__":
    raise SystemExit(main())
