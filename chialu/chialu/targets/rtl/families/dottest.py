"""The dot-accumulate library's harness: every family's module at a few
mode geometries against the seed's exact semantics (the engine's exact
products summed in the fixed-point frame, normalized to X), under
Verilator.

    python3 -m chialu.targets.rtl.families.dottest [--only <substring>] [--jobs 8] [--geoms int8,fp16,...]

A module whose pins keep the sum exact must match bit for bit (the frame
value for an integer d, the X for a float d); a module whose pins round a
partial result (a per-level truncation, a faithful contract, the tensor
core's partial-sum rounding, a chunked accumulation) is checked within a
ulp bound on the packed d.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from chialu.targets.rtl.engine import FORCE_NONE, FW
from chialu.targets.rtl.families import dot as DOT
from chialu.verify.formats import BlockFormat, FloatFormat, parse_format

N_RANDOM = 300

GEOMS = {
    "int8": ("int8", "int32", "int32", 4, True),
    "fp16": ("fp16", "fp32", "fp32", 4, True),
    "fp32fma": ("fp32", "fp32", "fp32", 1, True),
    "bf16": ("bf16", "fp32", "fp32", 2, True),
    "fp8": ("fp8e4m3", "fp16", "fp16", 4, True),
    "fp16noc": ("fp16", None, "fp32", 4, False),
    "fx": ("fxs1i7f8", "fxs1i15f16", "fxs1i15f16", 2, True),
}


def spec_of(fab, fc, fd, n, acc) -> dict:
    return {"unit": "vec_dot_acc", "accumulate": acc,
            "modes": [{"elements": n, "format_ab": fab, "format_c": fc or fd, "format_d": fd}],
            "rounding": ["RNE"], "daz_in": [False], "ftz_out": [False], "flags": [], "sr_bits": 8,
            "dot_contract": "fused", "check_sr": [True], "overflow": "wrap"}


def gen_of(fab, fc, fd, n, acc):
    from chialu.targets.rtl.dot_seed import DotModeGen
    from chialu.verify import dot_ref as D
    spec = D.normalize_dot_spec(spec_of(fab, fc, fd, n, acc))
    lay = D.dot_layout(spec)
    return DotModeGen(spec, lay, 0, FORCE_NONE)


def package(g) -> str:
    return "\n".join(["package tpkg;", g.lib_text(), g._acc_to_x(), g._x_to_acc_term(), "endpackage"])


def cases(geom_names) -> list:
    """[(geometry name, family, pins, bound)]: bound None for an exact
    module, else the ulp bound of the packed d."""
    out = []
    for gname in geom_names:
        fab, fc, fd, n, acc = GEOMS[gname]
        fmt = parse_format(fab)
        is_int = gname in ("int8", "fx")
        is_fma = n == 1
        common = [("pairwise_tree", {}, None), ("pairwise_tree", {"accum.family": "binary_tree", "accum.cpa.family": "parallel_prefix", "accum.cpa.topology": "sklansky"}, None),
                  ("pairwise_tree", {"accum.family": "csa_tree", "accum.compressor": "4:2"}, None),
                  ("pairwise_tree", {"accum.family": "csa_tree", "accum.compressor": "7:3", "mul.family": "direct_pp_parallel"}, None),
                  ("fused_csa", {}, None), ("fused_csa", {"compressor": "4:2", "final_cpa.family": "carry_select"}, None),
                  ("integer_mac", {}, None), ("integer_mac", {"array_style": "simd_packed_dot", "accumulation_mode": "sum_together"}, None),
                  ("kulisch_long_accumulator", {}, None),
                  ("kulisch_long_accumulator", {"organization": "segmented_lazy_carry", "carry_resolution": "carry_save_deferred"}, None),
                  ("kulisch_long_accumulator", {"organization": "banked_sub_adders", "carry_resolution": "periodic_sweep"}, None),
                  ("kulisch_long_accumulator", {"organization": "two_speed", "carry_resolution": "immediate"}, None),
                  ("bf16_fma_datapath", {}, None), ("fp8_training_datapath", {}, None),
                  ("tensor_core_mixed_precision_mac", {}, 8 if not is_int else None),
                  ("multi_precision_simd_fma", {}, None)]
        if is_int:
            common.append(("integer_mac", {"array_style": "composable_submultiplier", "scalability_levels": 1}, None))
            common.append(("integer_mac", {"array_style": "composable_submultiplier", "scalability_levels": 2, "accumulation_mode": "sum_together"}, None))
            common.append(("multi_term_fused_dot", {}, None))
        else:
            # the streaming accumulator's window_bits (33 by default) truncates below the largest term: bounded
            common += [("streaming_accurate_accumulator", {}, 8),
                       ("streaming_accurate_accumulator", {"approach": "tree_reduce_with_refinement", "in_loop_normalization": True}, 8),
                       ("streaming_accurate_accumulator", {"window_bits": 256}, 8),
                       ("pairwise_tree", {"per_level_truncation": True}, 8),
                       # a chunk sum rounded to fp16 loses (man_d - 10) bits of a wider d: the bound follows (the fp8
                       # geometry alone: fp16 products overflow an fp16 chunk)
                       *([("fp8_training_datapath", {"chunk_based_accumulation": True, "accumulate_precision": "fp16"},
                           (2 << max(0, parse_format(fd).man_bits - 10)) + 8)] if fab.startswith("fp8") else []),
                       # four partial sums truncated toward zero: up to four ulps of the partials each
                       ("tensor_core_mixed_precision_mac", {"alignment_target": "pairwise_sequential", "partial_sum_rounding": "truncate_toward_zero"}, 32)]
            for strat in ("per_level", "single_wide_window", "two_stage_coarse_fine", "max_exponent_tree",
                          "pairwise_difference_reuse", "exponent_sorted_realignment_lines"):
                common.append(("multi_term_fused_dot", {"alignment_strategy": strat}, None))
            common += [("multi_term_fused_dot", {"sign_handling": "dual_reduction_positive_pair_select", "reduction.family": "csa_tree",
                                                 "cancellation_handling": "detect_and_bypass_smallest_operand", "normalize_before_add": True}, None),
                       ("multi_term_fused_dot", {"alignment_strategy": "max_exponent_tree", "lza.family": "lza", "reduction.family": "binary_tree"}, None),
                       # the realignment lines with the anticipator, and with the dual reduction and the cancellation bypass
                       ("multi_term_fused_dot", {"alignment_strategy": "exponent_sorted_realignment_lines", "lza.family": "lza",
                                                 "reduction.family": "csa_tree", "align.shifter.family": "barrel_mux_tree"}, None),
                       ("multi_term_fused_dot", {"alignment_strategy": "exponent_sorted_realignment_lines",
                                                 "sign_handling": "dual_reduction_positive_pair_select", "normalization_deferral": "final_only"}, None),
                       ("multi_term_fused_dot", {"alignment_strategy": "exponent_sorted_realignment_lines",
                                                 "cancellation_handling": "detect_and_bypass_smallest_operand"}, None),
                       ("multi_term_fused_dot", {"rounding_contract": "faithful", "guard_bits_per_level": 4}, 8)]
            if n == 2:
                common += [("fused_two_term_dot", {}, None), ("fused_two_term_dot", {"dual_path_add": True}, None)]
            if acc:
                # the bounded alignment (exact: the products in their band, the addend in the near window or the far word)
                ba = {"align.family": "bounded_align"}
                common += [("pairwise_tree", dict(ba), None),
                           ("pairwise_tree", dict(ba, **{"align.sticky_method": "or_tree_shifted_out", "align.shifter.family": "barrel_mux_tree",
                                                          "lza.family": "lza", "accum.family": "binary_tree"}), None),
                           ("pairwise_tree", dict(ba, **{"align.sticky_method": "trailing_zero_compare", "align.bound": 5,
                                                          "accum.family": "csa_tree", "norm_shifter.family": "funnel"}), None),
                           ("fused_csa", dict(ba), None),
                           ("fused_csa", dict(ba, **{"compressor": "4:2", "lza.family": "lza", "align.sticky_method": "or_tree_shifted_out"}), None),
                           ("integer_mac", dict(ba), None),
                           ("kulisch_long_accumulator", dict(ba, organization="segmented_lazy_carry", carry_resolution="carry_save_deferred"), None),
                           ("bf16_fma_datapath", dict(ba), None), ("fp8_training_datapath", dict(ba), None),
                           ("multi_precision_simd_fma", dict(ba), None),
                           ("multi_term_fused_dot", dict(ba, alignment_strategy="single_wide_window",
                                                         sign_handling="dual_reduction_positive_pair_select"), None),
                           ("multi_term_fused_dot", dict(ba, alignment_strategy="single_wide_window",
                                                         cancellation_handling="detect_and_bypass_smallest_operand"), None)]
        if is_fma:
            common = [c for c in common if c[0] not in ("fused_csa",)]
            common += [("classic_fma", {}, None), ("classic_fma", {"negation_handling": "dual_adder", "lza.family": "lzc_after_add"}, None),
                       ("classic_fma", {"negation_handling": "complement_recode", "multiplier.family": "booth_recoded_parallel", "cpa.family": "parallel_prefix"}, None),
                       ("reduced_latency_fma", {}, None), ("reduced_latency_fma", {"normalize_before_add": True}, None),
                       # the fused rounding leaves with the ROUNDED code: the packed results through the library rounder are compared
                       ("reduced_latency_fma", {"rounding_position": "fused_with_cpa_dual_sum"}, "pack"),
                       ("multipath_fma", {}, None), ("multipath_fma", {"path_count": 3, "path_select_criterion": "cancellation_estimate"}, None),
                       ("multipath_fma", {"path_count": 5, "path_select_criterion": "both"}, None),
                       # the bridge composes the library fp adder, whose window keeps fewer bits than the engine's X below
                       # the larger operand (the sticky covers them): the packed results are compared
                       ("bridge_fma", {}, "pack"), ("bridge_fma", {"composition_style": "cascade_mul_then_add"}, "seq"),
                       ("mixed_precision_cascade_fma", {}, "pack"), ("mixed_precision_cascade_fma", {"exact_product_preserved": False}, "seq")]
        # a truncating pin's error follows the operands' precision: on a wider destination the ulp bound
        # scales by the precision gap
        fdf = parse_format(fd)
        scale = 1 << max(0, getattr(fdf, "man_bits", 0) - getattr(fmt, "man_bits", 0)) if isinstance(fmt, FloatFormat) and isinstance(fdf, FloatFormat) else 1
        for fam, pins, bound in common:
            out.append((gname, fam, pins, bound * scale if isinstance(bound, int) else bound))
    return out


def tb_text(g, dg, module, info, bound, fab, fc, fd, n, acc, is_int) -> str:
    e = g.eng
    p = g.p
    XT, VW, XW, EW, AW = e.XT, e.VW, e.XW, e.EW, g.AW
    wab, wc, wd = parse_format(fab).width, (parse_format(fc).width if acc else 0), parse_format(fd).width
    top = 2 * XW + EW + 2
    fdf = parse_format(fd)
    conns = []
    if is_int and dg.intg:
        conns += [".a(a_bus)", ".b(b_bus)"] + ([".c(c_pat)"] if acc else [])
    else:
        conns += [".xa(xa_bus)", ".xb(xb_bus)"] + ([".xc(xc)"] if acc else [])
    if info.get("rnd"):
        conns += [".rnd(rnd)"] + ([".word(word)"] if info.get("rnd") and "word" in module_ports(module) else [])
    out_acc = dg.out == "acc"
    conns.append(".acc(acc_l)" if out_acc else ".y(y_l)")
    unpack_ab = f"{p}_unpack_ab"
    L = [f"module tb;", "  import tpkg::*;",
         f"  logic [{n*wab-1}:0] a_bus, b_bus; logic [{max(wc,1)-1}:0] c_pat; logic [{n*XT-1}:0] xa_bus, xb_bus; logic [{XT-1}:0] xc;",
         f"  logic signed [{AW-1}:0] acc_l, acc_r, tmax, tv; logic [{XT-1}:0] y_l, y_r; logic [2:0] rnd; logic [7:0] word; logic [{FW+wd-1}:0] pk_l, pk_r, pk_t;",
         "  integer i, t, errs = 0, tests = 0, skipped = 0; logic bad;",
         f"  logic [{top}:0] pr;",
         f"  {module} dut ({', '.join(conns)});"]
    for t in range(n):
        L.append(f"  assign xa_bus[{t*XT} +: {XT}] = {p}_x({unpack_ab}(a_bus[{t*wab} +: {wab}], 1'b0));")
        L.append(f"  assign xb_bus[{t*XT} +: {XT}] = {p}_x({unpack_ab}(b_bus[{t*wab} +: {wab}], 1'b0));")
    if acc:
        L.append(f"  assign xc = {p}_x({p}_unpack_c(c_pat, 1'b0));")
    else:
        L.append(f"  assign xc = {p}_mkx(2'd0, 1'b0, 0, 0, 1'b0);")
    L += ["  task check; begin",
          "    #2;",
          f"    acc_r = {p}_termx(xc); bad = (xc[{XT-1}:{XT-2}] != 2'd0); tmax = (acc_r < 0) ? -acc_r : acc_r;",
          f"    for (t = 0; t < {n}; t = t + 1) begin",
          f"      pr = {p}_mulx(xa_bus[t*{XT} +: {XT}], xb_bus[t*{XT} +: {XT}]);",
          f"      if (pr[{top}:{top-1}] != 2'd0) bad = 1'b1;",
          f"      else begin tv = {p}_term(pr[{top-2}], pr[{top-3}:{2*XW}], pr[{2*XW-1}:0]); acc_r = acc_r + tv; if (tv < 0) tv = -tv; if (tv > tmax) tmax = tv; end",
          "    end",
          f"    y_r = {p}_acc2x(acc_r);",
          "    if (bad) skipped = skipped + 1;",
          "    else begin tests = tests + 1;"]
    rounder_text = ""
    if bound == "pack" and not out_acc:
        # the library fp adder's window keeps fewer bits below the larger operand than the engine's X (the
        # sticky covers them): the packed results under every rounding mode are compared; a value that leaves
        # already rounded (the ROUNDED code) packs through the library rounder, as the seed does
        if info.get("rounded"):
            from chialu.targets.rtl.families import fp as FP
            from chialu.targets.rtl.families.fp import Geom
            rn, rounder_text = FP.round_sv(fdf, Geom.of_engine(e), "dedicated_per_op", {}, e.tokens)
            L.insert(4, f"  logic [{FW-1}:0] fl_l; logic [{wd-1}:0] bits_l;\n  {rn} u_rnd (.x(y_l), .rnd(rnd), .word(word), .ftz(1'b0), .fl(fl_l), .bits(bits_l));")
            L.append(f"      pk_l = {{fl_l, bits_l}}; pk_r = {p}_pack_d(y_r, rnd, word, 1'b0);")
            L.append(f"      if (pk_l[{wd-1}:0] !== pk_r[{wd-1}:0]) begin errs = errs + 1; if (errs < 5) $display(\"MISMATCH a=%h b=%h c=%h pk_l=%h pk_r=%h y_l=%h y_r=%h\", a_bus, b_bus, c_pat, pk_l, pk_r, y_l, y_r); end")
        else:
            # a zero result's sign is the seed's rule (applied after the module): the two zeros compare equal
            L.append(f"      pk_l = {p}_pack_d(y_l, rnd, word, 1'b0); pk_r = {p}_pack_d(y_r, rnd, word, 1'b0);")
            L.append(f"      if (pk_l !== pk_r && !((pk_l[{wd-2}:0] == 0) && (pk_r[{wd-2}:0] == 0))) begin errs = errs + 1; if (errs < 5) $display(\"MISMATCH a=%h b=%h c=%h pk_l=%h pk_r=%h y_l=%h y_r=%h\", a_bus, b_bus, c_pat, pk_l, pk_r, y_l, y_r); end")
    elif bound is None or bound == "seq" or bound == "pack":
        if out_acc:
            L.append("      if (acc_l !== acc_r) begin errs = errs + 1; if (errs < 5) $display(\"MISMATCH a=%h b=%h c=%h acc_l=%h acc_r=%h\", a_bus, b_bus, c_pat, acc_l, acc_r); end")
        else:
            if bound == "seq":
                # the sequential cascade: the product rounded to d, then the add; compare after the pack
                L.append(f"      pk_t = {p}_pack_d({p}_mul(xa_bus[{XT-1}:0], xb_bus[{XT-1}:0]), rnd, word, 1'b0);")
                L.append(f"      pk_r = {p}_pack_d({p}_add(xc, {p}_x({p}_unpack_c(pk_t[{wd-1}:0], 1'b0)), 1'b0), rnd, word, 1'b0);")
                L.append(f"      pk_l = {p}_pack_d(y_l, rnd, word, 1'b0);")
                L.append("      if (pk_l !== pk_r) begin errs = errs + 1; if (errs < 5) $display(\"MISMATCH a=%h b=%h c=%h rnd=%0d pk_l=%h pk_r=%h y_l=%h\", a_bus, b_bus, c_pat, rnd, pk_l, pk_r, y_l); end")
            else:
                L.append("      if (y_l !== y_r) begin errs = errs + 1; if (errs < 5) $display(\"MISMATCH a=%h b=%h c=%h y_l=%h y_r=%h acc_r=%h\", a_bus, b_bus, c_pat, y_l, y_r, acc_r); end")
    else:
        # a bounded module: the packed d within `bound` ulps (a sign-magnitude index difference)
        L.append(f"      pk_l = {p}_pack_d(y_l, rnd, word, 1'b0); pk_r = {p}_pack_d(y_r, rnd, word, 1'b0);")
        L.append(f"      if (pk_l[{FW+wd-1}:{wd}] != pk_r[{FW+wd-1}:{wd}] && 0) ;")
        # a result at the format's top (an overflow to infinity or the largest finite value, which a partial
        # rounding decides differently from the exact sum) has no ulp distance: skipped
        E = getattr(fdf, "exp_bits", 8)
        L.append(f"      if (pk_r[{wd-2}:{wd-1-E}] == {{{E}{{1'b1}}}} || pk_l[{wd-2}:{wd-1-E}] == {{{E}{{1'b1}}}} || pk_r[{wd-2}:{wd-1-E}] == {{{{({E}-1){{1'b1}}}}, 1'b0}}) skipped = skipped + 1;")
        # a cancellation (the exact sum below an eighth of the largest term) leaves a partial rounding's error
        # unbounded in ulps of d: skipped
        L.append(f"      else if (((acc_r < 0) ? -acc_r : acc_r) < (tmax >>> 3)) skipped = skipped + 1;")
        L.append(f"      else if (ulpdiff(pk_l[{wd-1}:0], pk_r[{wd-1}:0]) > {bound}) begin errs = errs + 1; if (errs < 5) $display(\"BOUND a=%h b=%h c=%h pk_l=%h pk_r=%h\", a_bus, b_bus, c_pat, pk_l, pk_r); end")
    L += ["    end", "  end endtask"]
    if bound not in (None, "seq"):
        sgn = 1 if getattr(fdf, "signed", True) else 0
        q = chr(39)
        idx_expr = f"b[{wd-1}] ? -longint{q}(b[{wd-2}:0]) : longint{q}(b[{wd-2}:0])" if sgn else f"longint{q}(b)"
        L += [f"  function automatic longint idx(input [{wd-1}:0] b);",
              f"    idx = {idx_expr};",
              "  endfunction",
              f"  function automatic longint ulpdiff(input [{wd-1}:0] x, input [{wd-1}:0] y);",
              "    ulpdiff = (idx(x) > idx(y)) ? idx(x) - idx(y) : idx(y) - idx(x);",
              "  endfunction"]
    L += ["  initial begin", "    rnd = 3'd0; word = 8'd0;",
          f"    for (i = 0; i < {N_RANDOM}; i = i + 1) begin",
          "      a_bus = {$urandom, $urandom, $urandom, $urandom, $urandom, $urandom, $urandom, $urandom}; b_bus = {$urandom, $urandom, $urandom, $urandom, $urandom, $urandom, $urandom, $urandom};",
          "      c_pat = {$urandom, $urandom, $urandom};"]
    if not is_int and isinstance(parse_format(fab), FloatFormat) and bound in (None, "seq", "pack"):
        # cancellation cases for the exact modules: equal products with opposite signs, c near the products (a
        # truncating module's error under a cancellation is unbounded in ulps of d, so the bounded cases take
        # the plain random operands)
        L += [f"      if (i % 5 == 1) begin b_bus[{wab} +: {wab}] = b_bus[{wab-1}:0] ^ ({wab}'d1 << {wab-1}); a_bus[{wab} +: {wab}] = a_bus[{wab-1}:0]; end" if n >= 2 else "",
              f"      if (i % 7 == 2) c_pat = 0;",
              f"      if (i % 11 == 3) begin a_bus = 0; end",
              f"      if (i % 13 == 4) c_pat = c_pat >> {max(wc, 1) // 2};"]
        fcf = parse_format(fc) if acc else None
        if acc and isinstance(fcf, FloatFormat) and getattr(fcf, "exp_bits", 0) > 0:
            # the smallest products (the band's lsb, random signs) with the addend's exponent around the band's bottom:
            # a cancellation down to the addend's bits below the products, and the addend just above them
            band_lo = dg.band[0]
            Ec, Mc, bias_c = fcf.exp_bits, fcf.man_bits, fcf.bias
            f0 = max(1, band_lo - 4 + bias_c)
            ones = int("0" * (wab - 1) + "1", 2)
            sign_mask = sum(1 << (wab * k + wab - 1) for k in range(n))
            L.append(f"      if (i % 17 == 5) begin a_bus = {{{n}{{{wab}'d{ones}}}}} ^ ({{$urandom, $urandom, $urandom, $urandom}} & {n*wab}'h{sign_mask:x}); "
                     f"b_bus = {{{n}{{{wab}'d{ones}}}}} ^ ({{$urandom, $urandom, $urandom, $urandom}} & {n*wab}'h{sign_mask:x}); "
                     f"c_pat = {{c_pat[{wc-1}], {Ec}'d{f0} + {Ec}'($urandom % 8), c_pat[{Mc-1}:0]}}; end")
    # the five rounding modes of a unit without SR (the library rounders take the SR word only under an SR geometry)
    L += ["      rnd = (i % 5); if (rnd == 4) rnd = 5; word = $urandom;", "      check;", "    end",
          "    if (errs == 0) $display(\"PASS %0d (skipped %0d)\", tests, skipped); else $display(\"FAIL %0d of %0d\", errs, tests);",
          "    $finish;", "  end", "endmodule"]
    return "\n".join(x for x in L if x != "") + ("\n" + rounder_text if rounder_text else "")


def module_ports(text: str) -> str:
    return text.split(");", 1)[0]


def run_case(pkg: str, name: str, text: str, tb: str, work: Path) -> str:
    d = work / name
    d.mkdir(parents=True, exist_ok=True)
    from chialu.targets.rtl.families import library_text
    from chialu.targets.rtl.families import library_closure
    (d / "all.sv").write_text(pkg + "\n" + library_closure(text + "\n" + tb) + "\n" + text + "\n" + tb)
    srcs = ["all.sv"]
    # Verilator reads the generated SystemVerilog as written, so nothing is converted
    from chialu.verify import simulate as SIM
    r = subprocess.run(["verilator", *SIM.VERILATOR_FLAGS, "-j", str(SIM.VERILATOR_JOBS),
                        "--top-module", "tb", "-Mdir", "obj_sim", "-o", "sim", *srcs],
                       cwd=d, capture_output=True, text=True, timeout=900)
    if r.returncode:
        return f"{name}: COMPILE FAIL {r.stderr.strip()[:400]}"
    try:
        r = subprocess.run(["./obj_sim/sim"], cwd=d, capture_output=True, text=True, timeout=900)
    except subprocess.TimeoutExpired:
        return f"{name}: SIM TIMEOUT"
    out = r.stdout.strip().splitlines()
    marks = [l for l in out if "PASS" in l or "FAIL" in l]
    verdict = marks[-1] if marks else (out[-1] if out else f"no output (rc {r.returncode}: {(r.stderr or '')[-200:]})")
    if "PASS" not in verdict:
        return f"{name}: {verdict}; " + " | ".join(out[:3])
    return f"{name}: PASS"


def run_architecture_case(label, spec, selection, work):
    """Check a partial-rounding family against its independent Python contract."""
    from chialu.verify.variant_selftest import check_seed
    try:
        result = check_seed(spec, selection, work / label, N_RANDOM, 71)
    except Exception as error:
        return f"{label}: FAIL {type(error).__name__}: {error}"
    return f"{label}: PASS" if result.get("pass") else f"{label}: FAIL {result.get('detail')}"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None)
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--geoms", default=",".join(GEOMS))
    args = ap.parse_args(argv)
    if not shutil.which("verilator"):
        print("verilator not on PATH")
        return 2
    work = Path(tempfile.mkdtemp(prefix="chialu_dot_"))
    jobs = []
    gens = {}
    for gname, fam, pins, bound in cases(args.geoms.split(",")):
        fab, fc, fd, n, acc = GEOMS[gname]
        label = f"{gname}_{fam}_" + "_".join(f"{k.split('.')[-1]}{v}" for k, v in pins.items())[:80]
        label = label.replace(":", "").replace("/", "")
        if args.only and args.only not in label:
            continue
        if bound == "seq":
            # cascade_product_rounding is a fixed architectural boundary,
            # whereas the final result follows the runtime rounding port.
            # The legacy SV oracle used the runtime mode for both rounds.
            from chialu.verify.dot_ref import normalize_dot_spec
            target = spec_of(fab, fc, fd, n, acc)
            target.update(dut_name="dot_core", check_en=False, dot_contract="architecture",
                          dot_architecture={"family": fam, "pins": dict(pins)},
                          rounding=["RNE", "RTZ", "RDN", "RUP", "SR"],
                          flags=["invalid", "overflow", "underflow", "inexact", "denormal"])
            jobs.append((label, None, (normalize_dot_spec(target), (fam, pins)), None))
            continue
        if gname not in gens:
            gens[gname] = gen_of(fab, fc, fd, n, acc)
        g = gens[gname]
        dg = DOT.geom_of(parse_format(fab), parse_format(fc) if acc else None, parse_format(fd), n, acc)
        try:
            name, text, info = DOT.dot_sv(dg, fam, pins, block=isinstance(parse_format(fab), BlockFormat))
        except ValueError as e:
            print(f"  --   {label}: no module ({e})")
            continue
        is_int = dg.intg is not None
        tb = tb_text(g, dg, name, info, bound, fab, fc, fd, n, acc, is_int)
        jobs.append((label, package(g), text, tb))
    results = []
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futs = [pool.submit(run_architecture_case, label, text[0], text[1], work) if pkg is None
                else pool.submit(run_case, pkg, label, text, tb, work) for label, pkg, text, tb in jobs]
        for f in futs:
            r = f.result()
            print(("  ok   " if r.endswith("PASS") else "  FAIL ") + r, flush=True)
            results.append(r)
    n_ok = sum(1 for r in results if r.endswith("PASS"))
    print(f"[dot harness] {n_ok}/{len(results)} pass ({work})")
    return 0 if n_ok == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
