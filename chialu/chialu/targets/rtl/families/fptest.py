"""The float library against the engine: for a format, an engine package
(the engine's V/X declarations, unpack, add/mul/lt/eq, pack) and a
testbench that feeds random and special operand patterns through the
unpacker, runs the engine function and the library module on the same
X values, packs both results under every rounding mode and compares
the patterns and flags (an X of equal value and sticky packs alike).

    python3 -m chialu.targets.rtl.families.fptest [--formats fp16,bf16,fp8e4m3] [--sr] [--only add_two_path]
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from chialu.targets.rtl.engine import FW, Conventions, Engine
from chialu.targets.rtl.families import fp as FP
from chialu.targets.rtl.families import library_text
from chialu.verify.formats import parse_format

N_RANDOM = 1500
SIM_TIMEOUT = 7200


def engine_for(fmt, sr: bool, sr_bits: int = 8, tight: bool = False):
    """The engine of a format: the exact X, or the guard-round-sticky X of
    the unit option x_form (a unit without conversion targets)."""
    return Engine("t", fmt, sr_bits, sr, targets=[] if tight else [fmt], conv=Conventions(), tight=tight)


def package(e, fmt) -> str:
    return "\n".join([
        "package tpkg;",
        e.vdecl(), e.rup_fn(), e.arith(), e.fma_fn(),
        e.unpack_float(fmt, "s"), e.pack_float(fmt, "s"),
        "endpackage",
    ])


def _tb_head(e, fmt, sr_bits):
    W, XT, VW = fmt.width, e.XT, e.VW
    return f"""
module tb;
  import tpkg::*;
  logic [{W-1}:0] pa, pb; logic [{VW}:0] ua, ub; logic [{XT-1}:0] xa, xb; logic daz;
  integer i, errs = 0, tests = 0;
  logic [2:0] rnd; logic ftz; logic [{sr_bits-1}:0] word;
  assign ua = t_unpack_s(pa, daz); assign ub = t_unpack_s(pb, daz);
  assign xa = t_x(ua[{VW-1}:0]); assign xb = t_x(ub[{VW-1}:0]);
  function automatic [{W-1}:0] special(input integer k);
    case (k % 8)
      0: special = 0;                                    // +0
      1: special = {W}'d1;                               // smallest subnormal
      2: special = {W}'d{fmt._max_finite_bits()};        // max finite
      3: special = {W}'d{(fmt.emax_code << fmt.man_bits) if fmt.has_inf else fmt._max_finite_bits()};  // inf
      4: special = {W}'d{fmt.encode_special(__import__('chialu.verify.formats', fromlist=['NAN']).NAN) if fmt.has_nan else 0};
      5: special = {W}'d{1 << fmt.man_bits};             // 1.0 * 2^(1-bias): the smallest normal
      6: special = {W}'d{(fmt.bias << fmt.man_bits)};    // 1.0
      default: special = {W}'d{(1 << (fmt.man_bits + fmt.exp_bits)) if fmt.signed else 0};  // -0
    endcase
  endfunction
"""


def _normalized_check(e, fmt, family: str, pins: dict | None) -> str:
    """The check of a fused multiply-add's normalization promise (a finite
    result leaves with its leading one at the top of the X, or as an exact
    zero, or as a lone sticky), which the seed's rounder relies on under
    normalized_input (fp.fma_normalization); under the anticipator's
    compensation_in_rounding the leading one may sit one position below
    the top, which the rounder's own normalization absorbs. The engine's
    pack normalizes for itself, so the value comparison alone does not see
    a violation. Nothing for a family that promises nothing."""
    promise = FP.fma_normalization(family, pins)
    if promise is None:
        return ""
    XT, XW = e.XT, e.XW
    top = f"yl[{XW}]" if promise == "exact" else f"(yl[{XW}] | yl[{XW-1}])"
    return (f"    if (yl[{XT-1}:{XT-2}] == 2'd0 && yl[{XW}:1] != 0 && !{top}) begin errs = errs + 1; "
            f"if (errs < 5) $display(\"NOT NORMALIZED a=%h b=%h xl=%h\", pa, pb, yl); end\n")


def tb_add(e, fmt, module, sr_bits, family, pins=None, rounder=None):
    """The adder bench; a fused multiply-add in its adder role (mul low)
    takes the rounding mode where its rounding is fused (fma_takes_rnd)
    and then packs through the library `rounder`, as the seed does."""
    W, XT = fmt.width, e.XT
    conn = ", .xc('0), .fop({2'b00, sub})" if family in FP.FMA_FAMILIES else ", .sub(sub)"
    if family in FP.FMA_FAMILIES and FP.fma_takes_rnd(family, pins):
        conn += ", .rnd(rnd)"
    lib_pack = (f"  logic [{FW-1}:0] fl_l; logic [{W-1}:0] bits_l;\n  {rounder} rnd_u (.x(yl), .rnd(rnd), .word(word), .ftz(ftz), .fl(fl_l), .bits(bits_l));"
                if rounder else "")
    pl_expr = "{fl_l, bits_l}" if rounder else "t_pack_s(yl, rnd, word, ftz)"
    return _tb_head(e, fmt, sr_bits) + f"""
  logic sub; logic [{XT-1}:0] yr, yl; logic [{FW+W-1}:0] pr, pl;
  {module} dut (.xa(xa), .xb(xb){conn}, .y(yl));
  assign yr = t_add(xa, xb, sub);
{lib_pack}
  task check; begin
    #1;
{_normalized_check(e, fmt, family, pins)}    for (int r = 0; r < 6; r = r + 1) begin
      if (r == 4 && {int(e.tight)}) continue;   // the stochastic mode needs the exact X
      rnd = r; word = $urandom;
      for (int f = 0; f < 2; f = f + 1) begin
        ftz = f; #1;
        pr = t_pack_s(yr, rnd, word, ftz); pl = {pl_expr}; tests = tests + 1;
        if (pr !== pl) begin errs = errs + 1; if (errs < 5) $display("MISMATCH a=%h b=%h sub=%b rnd=%0d ftz=%b ref=%h lib=%h xr=%h xl=%h", pa, pb, sub, rnd, ftz, pr, pl, yr, yl); end
      end
    end
  end endtask
  initial begin
    daz = 0;
    for (i = 0; i < {N_RANDOM}; i = i + 1) begin
      pa = $urandom; pb = $urandom; sub = $urandom;
      if (i % 4 == 1) pb = {{pa[{W-1}] ^ sub, pa[{W-2}:0]}};                      // equal exponents, opposite effective sign
      if (i % 4 == 2) pb = {{~pa[{W-1}], pa[{W-2}:{fmt.man_bits}] - 1'b1, pb[{fmt.man_bits-1}:0]}};  // exponent difference one
      if (i % 8 == 3) begin pa = special(i / 8); end
      if (i % 8 == 7) begin pb = special(i / 8 + 3); end
      if (i % 16 == 5) daz = 1; else daz = 0;
      check;
    end
    if (errs == 0) $display("PASS %0d", tests); else $display("FAIL %0d of %0d", errs, tests);
    $finish;
  end
endmodule
"""


def tb_fma(e, fmt, module, sr_bits, family, pins=None, rounder=None):
    """The fused multiply-add bench: the four fused ops (fop 3 to 6) on
    three operands against the engine's t_fma, both packed after the
    zero-sign rule the seed applies (IEEE 754 section 6.3 on the sum of
    the signed product and the addend); a variant whose rounding is fused
    takes rnd and packs through the library `rounder`."""
    W, XT, XW, VW = fmt.width, e.XT, e.XW, e.VW
    conn = ", .rnd(rnd)" if FP.fma_takes_rnd(family, pins) else ""
    lib_pack = (f"  logic [{FW-1}:0] fl_l; logic [{W-1}:0] bits_l;\n  {rounder} rnd_u (.x(ylz), .rnd(rnd), .word(word), .ftz(ftz), .fl(fl_l), .bits(bits_l));"
                if rounder else "")
    pl_expr = "{fl_l, bits_l}" if rounder else "t_pack_s(ylz, rnd, word, ftz)"
    sa, sb, sc = (f"pa[{W-1}]", f"pb[{W-1}]", f"pc[{W-1}]") if fmt.signed else ("1'b0", "1'b0", "1'b0")
    one = fmt.bias << fmt.man_bits
    return _tb_head(e, fmt, sr_bits) + f"""
  logic [{W-1}:0] pc; logic [{VW}:0] uc; logic [{XT-1}:0] xc; logic [2:0] fop;
  assign uc = t_unpack_s(pc, daz); assign xc = t_x(uc[{VW-1}:0]);
  logic [{XT-1}:0] yr, yl, yrz, ylz; logic [{FW+W-1}:0] pr, pl; logic np, nc, ps, cs, zs;
  assign np = (fop == 3'd5) || (fop == 3'd6); assign nc = (fop == 3'd4) || (fop == 3'd6);
  assign ps = {sa} ^ {sb} ^ np; assign cs = {sc} ^ nc;
  {module} dut (.xa(xa), .xb(xb), .xc(xc), .fop(fop){conn}, .y(yl));
  assign yr = t_fma(xa, xb, xc, np, nc);
  function automatic xzero(input [{XT-1}:0] x);
    xzero = (x[{XT-1}:{XT-2}] == 2'd0) && (x[{XW}:0] == 0);
  endfunction
  function automatic [{XT-1}:0] zfix(input [{XT-1}:0] x, input s);
    zfix = xzero(x) ? {{x[{XT-1}:{XT-2}], s, x[{XT-4}:0]}} : x;
  endfunction
  // the zero-sign rule on both results (continuous, so a module whose result depends on rnd settles first)
  assign yrz = zfix(yr, zs); assign ylz = zfix(yl, zs);
{lib_pack}
  task check; begin
    #1;
{_normalized_check(e, fmt, family, pins)}    for (int r = 0; r < 6; r = r + 1) begin
      if (r == 4 && {int(e.tight)}) continue;   // the stochastic mode needs the exact X
      rnd = r; word = $urandom;
      zs = ((xzero(xa) || xzero(xb)) && xzero(xc)) ? ((rnd == 3'd2) ? (ps | cs) : (ps & cs)) : (rnd == 3'd2);
      #1;
      for (int f = 0; f < 2; f = f + 1) begin
        ftz = f; #1;
        pr = t_pack_s(yrz, rnd, word, ftz); pl = {pl_expr}; tests = tests + 1;
        if (pr !== pl) begin errs = errs + 1; if (errs < 5) $display("MISMATCH a=%h b=%h c=%h fop=%0d rnd=%0d ftz=%b daz=%b ref=%h lib=%h xr=%h xl=%h", pa, pb, pc, fop, rnd, ftz, daz, pr, pl, yrz, ylz); end
      end
    end
  end endtask
  initial begin
    daz = 0;
    for (i = 0; i < {N_RANDOM}; i = i + 1) begin
      pa = $urandom; pb = $urandom; pc = $urandom; fop = 3'd3 + (i % 4);
      if (i % 8 == 1) begin pb = {W}'d{one}; pc = {{{sa} ^ (fop == 3'd3 || fop == 3'd6), pa[{W-2}:0]}}; end   // the addend cancels the product
      if (i % 8 == 2) begin pb = {W}'d{one}; pc = {{pc[{W-1}], pa[{W-2}:{fmt.man_bits}] - 1'b1, pc[{fmt.man_bits-1}:0]}}; end  // exponent difference one
      if (i % 8 == 3) begin pa = special(i / 8); end
      if (i % 8 == 5) begin pc = special(i / 8 + 5); end
      if (i % 8 == 7) begin pb = special(i / 8 + 3); end
      if (i % 16 == 6) daz = 1; else daz = 0;
      check;
    end
    if (errs == 0) $display("PASS %0d", tests); else $display("FAIL %0d of %0d", errs, tests);
    $finish;
  end
endmodule
"""


def tb_mul(e, fmt, module, sr_bits, fused, rounder=None, extra_conn="", unpacker=None, fma=None):
    """The multiplier bench; `unpacker` names a library unpacker whose
    normalized significands the module reads (the guard-round-sticky X
    keeps the top product bits, which is exact for normalized operands,
    and the ALU's unpacker normalizes a subnormal under that form); `fma`
    is the (family, pins) of a fused multiply-add in its multiplier role,
    which adds its normalization check."""
    W, XT, VW = fmt.width, e.XT, e.VW
    conn = (", .rnd(rnd)" if fused else "") + extra_conn
    lib_pack = (f"  logic [{FW-1}:0] fl_l; logic [{W-1}:0] bits_l;\n  {rounder} rnd_u (.x(yl), .rnd(rnd), .word(word), .ftz(ftz), .fl(fl_l), .bits(bits_l));"
                if rounder else "")
    pl_expr = "{fl_l, bits_l}" if rounder else "t_pack_s(yl, rnd, word, ftz)"
    operands = ""
    xa_in, xb_in = "xa", "xb"
    if unpacker:
        operands = (f"  logic [{VW}:0] una, unb; logic [{XT-1}:0] xna, xnb;\n"
                    f"  {unpacker} u_na (.b(pa), .daz(daz), .u(una));\n  {unpacker} u_nb (.b(pb), .daz(daz), .u(unb));\n"
                    f"  assign xna = t_x(una[{VW-1}:0]); assign xnb = t_x(unb[{VW-1}:0]);")
        xa_in, xb_in = "xna", "xnb"
    return _tb_head(e, fmt, sr_bits) + f"""
  logic [{XT-1}:0] yr, yl; logic [{FW+W-1}:0] pr, pl;
{operands}
  {module} dut (.xa({xa_in}), .xb({xb_in}){conn}, .y(yl));
  assign yr = t_mul(xa, xb);
{lib_pack}
  task check; begin
    #1;
{_normalized_check(e, fmt, *(fma or ("", None)))}    for (int r = 0; r < 6; r = r + 1) begin
      if (r == 4 && {int(e.tight)}) continue;   // the stochastic mode needs the exact X
      rnd = r; word = $urandom; #1;
      for (int f = 0; f < 2; f = f + 1) begin
        ftz = f; #1;
        pr = t_pack_s(yr, rnd, word, ftz); pl = {pl_expr}; tests = tests + 1;
        if (pr !== pl) begin errs = errs + 1; if (errs < 5) $display("MISMATCH a=%h b=%h rnd=%0d ftz=%b ref=%h lib=%h xr=%h xl=%h", pa, pb, rnd, ftz, pr, pl, yr, yl); end
      end
    end
  end endtask
  initial begin
    daz = 0;
    for (i = 0; i < {N_RANDOM}; i = i + 1) begin
      pa = $urandom; pb = $urandom;
      if (i % 8 == 3) pa = special(i / 8);
      if (i % 8 == 7) pb = special(i / 8 + 3);
      check;
    end
    if (errs == 0) $display("PASS %0d", tests); else $display("FAIL %0d of %0d", errs, tests);
    $finish;
  end
endmodule
"""


def tb_div(e, fmt, module, sr_bits):
    W, XT = fmt.width, e.XT
    return _tb_head(e, fmt, sr_bits) + f"""
  logic [{XT-1}:0] yr, yl; logic [{FW+W-1}:0] pr, pl;
  {module} dut (.xa(xa), .xb(xb), .y(yl));
  assign yr = t_div(xa, xb);
  task check; begin
    for (int r = 0; r < 6; r = r + 1) begin
      if (r == 4 && {int(e.tight)}) continue;   // the stochastic mode needs the exact X
      rnd = r; word = $urandom; #1;
      for (int f = 0; f < 2; f = f + 1) begin
        ftz = f; #1;
        pr = t_pack_s(yr, rnd, word, ftz); pl = t_pack_s(yl, rnd, word, ftz); tests = tests + 1;
        if (pr !== pl) begin errs = errs + 1; if (errs < 5) $display("MISMATCH a=%h b=%h rnd=%0d ftz=%b ref=%h lib=%h xr=%h xl=%h", pa, pb, rnd, ftz, pr, pl, yr, yl); end
      end
    end
  end endtask
  initial begin
    daz = 0;
    for (i = 0; i < {N_RANDOM}; i = i + 1) begin
      pa = $urandom; pb = $urandom;
      if (i % 8 == 3) pa = special(i / 8);
      if (i % 8 == 7) pb = special(i / 8 + 3);
      if (i % 16 == 5) daz = 1; else daz = 0;
      check;
    end
    if (errs == 0) $display("PASS %0d", tests); else $display("FAIL %0d of %0d", errs, tests);
    $finish;
  end
endmodule
"""


def tb_sqrt(e, fmt, module, sr_bits):
    W, XT = fmt.width, e.XT
    return _tb_head(e, fmt, sr_bits) + f"""
  logic [{XT-1}:0] yr, yl; logic [{FW+W-1}:0] pr, pl;
  {module} dut (.xa(xa), .y(yl));
  assign yr = t_sqrt(xa);
  task check; begin
    for (int r = 0; r < 6; r = r + 1) begin
      if (r == 4 && {int(e.tight)}) continue;   // the stochastic mode needs the exact X
      rnd = r; word = $urandom; #1;
      for (int f = 0; f < 2; f = f + 1) begin
        ftz = f; #1;
        pr = t_pack_s(yr, rnd, word, ftz); pl = t_pack_s(yl, rnd, word, ftz); tests = tests + 1;
        if (pr !== pl) begin errs = errs + 1; if (errs < 5) $display("MISMATCH a=%h rnd=%0d ftz=%b ref=%h lib=%h xr=%h xl=%h", pa, rnd, ftz, pr, pl, yr, yl); end
      end
    end
  end endtask
  initial begin
    daz = 0; pb = 0;
    for (i = 0; i < {N_RANDOM}; i = i + 1) begin
      pa = $urandom;
      if (i % 8 == 3) pa = special(i / 8);
      if (i % 16 == 5) daz = 1; else daz = 0;
      check;
    end
    if (errs == 0) $display("PASS %0d", tests); else $display("FAIL %0d of %0d", errs, tests);
    $finish;
  end
endmodule
"""


def tb_cmp(e, fmt, module, sr_bits):
    W, XT = fmt.width, e.XT
    return _tb_head(e, fmt, sr_bits) + f"""
  logic lt_r, eq_r, lt_l, eq_l;
  {module} dut (.xa(xa), .xb(xb), .lt(lt_l), .eq(eq_l));
  assign lt_r = t_lt(xa, xb); assign eq_r = t_eq(xa, xb);
  task check; begin
    #1; tests = tests + 1;
    if ({{lt_r, eq_r}} !== {{lt_l, eq_l}}) begin errs = errs + 1; if (errs < 5) $display("MISMATCH a=%h b=%h ref lt=%b eq=%b lib lt=%b eq=%b", pa, pb, lt_r, eq_r, lt_l, eq_l); end
  end endtask
  initial begin
    daz = 0;
    for (i = 0; i < {N_RANDOM}; i = i + 1) begin
      pa = $urandom; pb = $urandom;
      if (i % 4 == 1) pb = pa;
      if (i % 4 == 2) pb = {{~pa[{W-1}], pa[{W-2}:0]}};
      if (i % 8 == 3) pa = special(i / 8);
      if (i % 8 == 7) pb = special(i / 8 + 3);
      check;
    end
    if (errs == 0) $display("PASS %0d", tests); else $display("FAIL %0d of %0d", errs, tests);
    $finish;
  end
endmodule
"""


def tb_round(e, fmt, module, sr_bits, normalized=False):
    """The rounder against the engine's pack over X values that arise in
    the unit: unpacked operands, sums, differences and products;
    `normalized` feeds them with the leading one at the top (the
    normalized_input rounder's contract)."""
    W, XT = fmt.width, e.XT
    dut_in = "t_norm(xr)" if normalized else "xr"
    return _tb_head(e, fmt, sr_bits) + f"""
  logic sub; logic [{XT-1}:0] xr; logic [{FW+W-1}:0] pr, pl; logic [{FW-1}:0] fl_l; logic [{W-1}:0] bits_l;
  {module} dut (.x({dut_in}), .rnd(rnd), .word(word), .ftz(ftz), .fl(fl_l), .bits(bits_l));
  task check; begin
    for (int r = 0; r < 6; r = r + 1) begin
      if (r == 4 && {int(e.tight)}) continue;   // the stochastic mode needs the exact X
      rnd = r; word = $urandom;
      for (int f = 0; f < 2; f = f + 1) begin
        ftz = f; #1;
        pr = t_pack_s(xr, rnd, word, ftz); pl = {{fl_l, bits_l}}; tests = tests + 1;
        if (pr !== pl) begin errs = errs + 1; if (errs < 5) $display("MISMATCH x=%h rnd=%0d ftz=%b ref=%h lib=%h", xr, rnd, ftz, pr, pl); end
      end
    end
  end endtask
  initial begin
    daz = 0;
    for (i = 0; i < {N_RANDOM}; i = i + 1) begin
      pa = $urandom; pb = $urandom; sub = $urandom;
      if (i % 8 == 3) pa = special(i / 8);
      if (i % 8 == 7) pb = special(i / 8 + 3);
      #1;
      case (i % 4)
        0: xr = xa;
        1: xr = t_add(xa, xb, sub);
        2: xr = t_mul(xa, xb);
        default: xr = t_add(t_mul(xa, xb), xb, sub);
      endcase
      check;
    end
    if (errs == 0) $display("PASS %0d", tests); else $display("FAIL %0d of %0d", errs, tests);
    $finish;
  end
endmodule
"""


def tb_unpack(e, fmt, module, sr_bits):
    W, VW = fmt.width, e.VW
    return _tb_head(e, fmt, sr_bits) + f"""
  logic [{VW}:0] ul; logic [{FW+W-1}:0] pr, pl;
  {module} dut (.b(pa), .daz(daz), .u(ul));
  task check; begin
    #1; tests = tests + 1;
    pr = t_pack_s(t_x(ua[{VW-1}:0]), 3'd0, 0, 1'b0); pl = t_pack_s(t_x(ul[{VW-1}:0]), 3'd0, 0, 1'b0);
    if (pr !== pl || ua[{VW}] !== ul[{VW}] || ua[{VW-1}:{VW-2}] !== ul[{VW-1}:{VW-2}]) begin errs = errs + 1; if (errs < 5) $display("MISMATCH b=%h ref=%h lib=%h", pa, ua, ul); end
  end endtask
  initial begin
    for (i = 0; i < {N_RANDOM}; i = i + 1) begin
      pa = $urandom; daz = (i % 3 == 0);
      if (i % 8 == 3) pa = special(i / 8);
      check;
    end
    if (errs == 0) $display("PASS %0d", tests); else $display("FAIL %0d of %0d", errs, tests);
    $finish;
  end
endmodule
"""


def fma_sweep_variants() -> list:
    """[(family, pins)] sweeping the fp_fma slot's fused families one factor
    at a time from each family's defaults: every member of each own choice
    (`sharing` left out, since it leaves the module alone), every family of
    each slot, that family's own choices where the slot's space is not a
    root kind of its own (the align and the lza; a multiplier's, an adder's
    or a shifter's choices are swept under its own kind), and every family
    of a slot's own slots (the align's shifter and tzc, the lza's encoder
    and counter). The algorithm-level multiplier families stay out, as the
    ALU's slot drops them (modules.alu.exact_only). `fptest --fma-sweep`
    runs these in place of the fixed fma variants."""
    from chialu.modules.alu import exact_only
    from chialu.spaces.fp_spaces import fp_fma_space
    from chialu.targets.rtl.families.coverage import ROOT_KINDS, samples, space_kind
    out = []
    for fam in fp_fma_space(11).families:
        if fam.name == "separate_multiplier_and_adder":
            continue
        for choice, dom in fam.design_choices.items():
            if choice == "sharing":
                continue
            out += [(fam.name, {choice: v}) for v in samples(dom)]
        for slot, sub in fam.components.items():
            root = space_kind(sub) in ROOT_KINDS       # the kind of the declared space, before the exact filter
            for f in exact_only(sub).families:
                pins = {f"{slot}.family": f.name}
                out.append((fam.name, dict(pins)))
                if root:
                    continue
                for choice, dom in f.design_choices.items():
                    out += [(fam.name, dict(pins, **{f"{slot}.{choice}": v})) for v in samples(dom)]
                for sslot, ssub in f.components.items():
                    out += [(fam.name, dict(pins, **{f"{slot}.{sslot}.family": ff.name})) for ff in ssub.families]
    return out


def cases(fmt, e, sr_bits, fma_sweep: bool = False):
    """[(name, module text, testbench)] of every fp family variant for a
    format; `fma_sweep` replaces the fixed fma variants by the one-factor
    sweep of fma_sweep_variants (the fp_fma slot's families alone)."""
    g = FP.Geom.of_engine(e)
    out = []
    tokens = Conventions().tokens()

    def fma_cases(fam, pins, n, t):
        """The three benches of a fused multiply-add variant: the adder role, the multiplier role and the four
        fused ops; a variant whose rounding is fused takes `rnd` and packs through the library rounder, as the
        seed does."""
        takes = FP.fma_takes_rnd(fam, pins)
        rn_ = None
        if takes:
            rn_, rt_ = FP.round_sv(fmt, g, "dedicated_per_op", {}, tokens, name=f"fam_fp_round_ref_{g.tag()}")
            t = t + "\n" + rt_
        return [(n, t, tb_add(e, fmt, n, sr_bits, fam, pins, rounder=rn_)),
                (n + "_mul", t, tb_mul(e, fmt, n, sr_bits, takes, rounder=rn_, extra_conn=", .xc('0), .fop(3'd2)",
                                       fma=(fam, pins))),
                (n + "_fma", t, tb_fma(e, fmt, n, sr_bits, fam, pins, rounder=rn_))]

    if fma_sweep:
        for k, (fam, pins) in enumerate(fma_sweep_variants()):
            label = "_".join(f"{key.replace('.', '_')}_{value}" for key, value in sorted(pins.items()))
            try:
                n, t = FP.fma_sv(g, fam, pins, name=f"fam_fp_fma_{fam}_s{k}_{g.tag()}", fmt=fmt)
            except ValueError as error:
                # a variant the generator refuses at this geometry (its message names the rule): reported apart
                # from the passes and the failures
                out.append((f"fam_fp_fma_{fam}_s{k}_{label}_{g.tag()}", None, str(error)))
                continue
            for name, text, tb in fma_cases(fam, pins, n, t):
                out.append((name.replace(n, n + "_" + label, 1), text, tb))
        return out
    for fam, pins in (("per_unit_unpack", {"denormal_handling": "in_datapath"}),
                      ("shared_per_lane", {"denormal_handling": "in_unpack"}),
                      ("shared_per_lane", {"denormal_handling": "in_unpack", "lzc.family": "prefix_lzc", "shifter.family": "barrel_mux_tree"}),
                      ("shared_across_formats", {})):
        n, t = FP.unpack_sv(fmt, g, fam, pins)
        out.append((n, t, tb_unpack(e, fmt, n, sr_bits)))
    add_variants = [
        ("single_path", {}),
        ("single_path", {"subnormal_representation": "pseudo_normalized_wide_exponent", "align.sticky_method": "trailing_zero_compare",
                         "norm.family": "coarse_fine", "norm.coarse_granularity": 8, "sig_adder.family": "carry_select"}),
        ("single_path", {"lz.family": "lzc_after_add", "exp.dual_direction_subtract": True, "align.sticky_method": "precomputed_mask",
                         "norm.family": "single_barrel", "align.shifter.family": "barrel_mux_tree"}),
        ("single_path", {"operand_order": "shift_each_operand", "lz.string_form": "dual_pos_neg_strings", "lz.split_string_select": "true_sign",
                         "lz.indicator_restriction": "positive_result_only"}),
        ("single_path", {"operand_order": "shift_each_operand", "lz.string_form": "dual_pos_neg_strings", "lz.split_string_select": "maximum_count",
                         "lz.correction_scheme": "compensation_in_rounding", "lz.zero_result_detect": "operand_function_or"}),
        ("single_path", {"operand_order": "shift_each_operand", "lz.string_form": "single_indicator", "lz.indicator_restriction": "general"}),
        ("single_path", {"lz.indicator_restriction": "positive_result_only", "lz.encoder.family": "prefix_lzc", "exp.adder.family": "parallel_prefix"}),
        ("two_path", {}),
        ("two_path", {"path_threshold": 2, "close_path_trigger": "exp_diff_and_effective_sub", "path_select_point": "late_result_mux",
                      "near_lz.family": "lzc_after_add", "close_norm.family": "single_barrel", "sig_adder.family": "ripple_carry"}),
        ("two_path", {"path_threshold": 3, "operand_order": "shift_each_operand", "far_align.sticky_method": "trailing_zero_compare"}),
        ("delay_optimized_unified", {}),
        ("delay_optimized_unified", {"path_separation": "nonstandard_unified_rounding", "subtraction_style": "ones_complement_end_around",
                                     "eac_incrementer.structure": "select_blocks"}),
        ("delay_optimized_unified", {"subtraction_style": "ones_complement_end_around", "operand_order": "shift_each_operand"}),
        ("low_power_gated", {}),
        ("low_power_gated", {"datapath_partitions": 2}),
        ("low_power_gated", {"datapath_partitions": 3, "operand_order": "shift_each_operand"}),
        # the unswapped datapath's negation schemes (the variants above take end_around_carry, the default)
        ("single_path", {"operand_order": "shift_each_operand", "negation_handling": "dual_adder"}),
        ("single_path", {"operand_order": "shift_each_operand", "negation_handling": "complement_recode",
                         "lz.string_form": "dual_pos_neg_strings", "lz.split_string_select": "true_sign"}),
        ("two_path", {"operand_order": "shift_each_operand", "negation_handling": "dual_adder", "path_select_point": "late_result_mux"}),
        ("low_power_gated", {"datapath_partitions": 3, "operand_order": "shift_each_operand", "negation_handling": "complement_recode"}),
    ]
    for k, (fam, pins) in enumerate(add_variants):
        n, t = FP.add_sv(g, fam, pins, name=f"fam_fp_add_{fam}_v{k}_{g.tag()}")
        out.append((n, t, tb_add(e, fmt, n, sr_bits, fam)))
    # the fp_fma slot's fused families, serving the adder (the mul port low) and the multiplier (mul high)
    fma_variants = [
        ("classic_fma", {}),
        ("classic_fma", {"negation_handling": "dual_adder", "lza.family": "lzc_after_add", "align.sticky_method": "precomputed_mask",
                         "multiplier.family": "behavioral_star"}),
        ("classic_fma", {"negation_handling": "complement_recode", "cpa.family": "parallel_prefix", "align.shifter.family": "barrel_mux_tree",
                         "multiplier.family": "booth_recoded_parallel"}),
        ("reduced_latency_fma", {"normalize_before_add": True, "add_skip_for_pure_addition": True}),
        # the rounding fused into the window adder's compound sum (the module takes rnd and leaves a normal result
        # rounded, with the ROUNDED code): the packed results through the library rounder are compared; it needs
        # the exact X
        ("reduced_latency_fma", {"rounding_position": "fused_with_cpa_dual_sum"}),
        ("reduced_latency_fma", {"rounding_position": "fused_with_cpa_dual_sum", "normalize_before_add": True,
                                 "negation_handling": "dual_adder", "lza.family": "lzc_after_add"}),
        ("multipath_fma", {"path_count": 3, "negation_handling": "dual_adder"}),
        # the bridge: the library's multiplier and adder composed (bridge_reuse needs the exact X: the product
        # crosses the bridge at twice the significand width), and monolithic_fused, which is classic_fma's text
        ("bridge_fma", {}),
        ("bridge_fma", {"lza.string_form": "dual_pos_neg_strings", "negation_handling": "dual_adder",
                        "multiplier.family": "booth_recoded_parallel"}),
        ("bridge_fma", {"composition_style": "monolithic_fused", "negation_handling": "complement_recode"}),
    ]
    for k, (fam, pins) in enumerate(fma_variants):
        if e.tight and fam == "bridge_fma" and pins.get("composition_style", "bridge_reuse") == "bridge_reuse":
            continue                            # the bridge needs the exact X (fma_sv refuses the tight one)
        if e.tight and FP.fma_takes_rnd(fam, pins):
            continue                            # the fused rounding needs the exact X (fma_sv refuses the tight one)
        n, t = FP.fma_sv(g, fam, pins, name=f"fam_fp_fma_{fam}_v{k}_{g.tag()}", fmt=fmt)
        out += fma_cases(fam, pins, n, t)
    rn, rt = FP.round_sv(fmt, g, "dedicated_per_op", {}, tokens, name=f"fam_fp_round_ref_{g.tag()}")
    for fam, pins in (("sig_mul_then_round", {}), ("sig_mul_then_round", {"sig_mul.family": "booth_recoded_parallel", "exp_adder.family": "parallel_prefix"}),
                      ("round_fused_in_reduction", {}), ("round_fused_in_reduction", {"sticky_method": "input_trailing_zero_count", "lzc.family": "prefix_lzc"})):
        fused = fam == "round_fused_in_reduction"
        if fused and e.tight:
            continue                            # the fused rounding needs the exact X
        n, t = FP.mul_sv(g, fam, pins, M=fmt.man_bits, bias=fmt.bias)
        unp = None
        if e.tight:
            # the tight X's multiplier reads normalized significands: the library unpacker in front of it
            un, ut = FP.unpack_sv(fmt, g, "per_unit_unpack", {"denormal_handling": "in_unpack"}, name=f"fam_fp_unpack_norm_{g.tag()}")
            t, unp = t + "\n" + ut, un
        out.append((n, t + ("\n" + rt if fused else ""), tb_mul(e, fmt, n, sr_bits, fused, rounder=rn if fused else None, unpacker=unp)))
    for fam, pins in (("integer_compare_on_bits", {}), ("integer_compare_on_bits", {"comparator.family": "subtractor_comparator"}),
                      ("dedicated_magnitude_comparator", {}), ("dedicated_magnitude_comparator", {"comparator.family": "prefix_comparator", "comparator.structure": "tree_reduction"})):
        n, t = FP.cmp_sv(g, fam, pins)
        out.append((n, t, tb_cmp(e, fmt, n, sr_bits)))
    div_variants = [("restoring_nonrestoring", {}), ("srt_radix2", {}), ("srt_high_radix", {"sig_div.digit_select.family": "comparator_digit_selection"}),
                    ("newton_raphson", {}), ("goldschmidt", {"sig_div.seed.family": "bipartite_rom"}), ("online_msdf", {}),
                    ("prescaled_very_high_radix", {})]
    if fmt.width <= 8:
        # the exclusion-zone precision (Q + D + 3 fraction bits) simulates slowly at the wider formats
        div_variants.append(("newton_raphson", {"sig_div.final_round.family": "exclusion_zone_proof"}))
    for dfam, dp in div_variants:
        n, t = FP.div_sv(g, "sig_div_then_round", dict(dp, **{"sig_div.family": dfam}),
                         name=f"fam_fp_div_{dfam}_{len(dp)}_{g.tag()}")
        out.append((n, t, tb_div(e, fmt, n, sr_bits)))
    for sfam, sp in (("digit_recurrence_sqrt_combined", {}), ("newton_raphson", {}), ("goldschmidt", {}),
                     ("direct_polynomial", {"sig_sqrt.seed.family": "poly_seed", "sig_sqrt.seed.degree": 2})):
        n, t = FP.sqrt_sv(g, "sig_sqrt_then_round", dict(sp, **{"sig_sqrt.family": sfam}))
        out.append((n, t, tb_sqrt(e, fmt, n, sr_bits)))
    for fam, pins in (("dedicated_per_op", {}), ("shared_per_lane", {"round.family": "compound_adder_select", "lzc.family": "prefix_lzc"}),
                      ("dedicated_per_op", {"round.family": "injection"}), ("dedicated_per_op", {"round.family": "flagged_prefix"}),
                      ("shared_across_formats", {"round.incrementer.structure": "select_blocks", "shifter.family": "barrel_mux_tree",
                                                 "exp_adder.family": "parallel_prefix", "exp_incrementer.structure": "select_blocks"})):
        n, t = FP.round_sv(fmt, g, fam, pins, tokens)
        out.append((n, t, tb_round(e, fmt, n, sr_bits)))
    # the rounder of a mode whose producers normalize (the fused multiply-add): no normalizer of its own
    for fam, pins in (("dedicated_per_op", {}), ("shared_per_lane", {"round.family": "compound_adder_select"})):
        n, t = FP.round_sv(fmt, g, fam, pins, tokens, normalized_input=True)
        out.append((n, t, tb_round(e, fmt, n, sr_bits, normalized=True)))
    return out


def run_case(pkg: str, lib: str, name: str, text: str, tb: str, work: Path) -> str:
    """Compile and run one bench: the package, the library modules the text
    and the bench reference (transitively; `lib` is unused), the text, the
    bench."""
    from chialu.targets.rtl.families import library_closure
    d = work / name
    d.mkdir(parents=True, exist_ok=True)
    if text is None:
        return f"{name}: REFUSED {tb[:400]}"
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
        r = subprocess.run(["./obj_sim/sim"], cwd=d, capture_output=True, text=True, timeout=SIM_TIMEOUT)
    except subprocess.TimeoutExpired:
        return f"{name}: SIM TIMEOUT"
    out = r.stdout.strip().splitlines()
    out = [l for l in out if "$finish called" not in l]
    verdict = out[-1] if out else f"no output (rc {r.returncode}: {(r.stderr or '')[-200:]})"
    if "PASS" not in verdict:
        return f"{name}: {verdict}; " + " | ".join(out[:3])
    return f"{name}: PASS"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--formats", default="fp16,bf16,fp8e4m3")
    ap.add_argument("--sr", action="store_true", help="the stochastic-rounding geometry (wider X)")
    ap.add_argument("--tight", action="store_true", help="the guard-round-sticky X (the unit option x_form guard_round_sticky)")
    ap.add_argument("--only", default=None)
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--fma-sweep", action="store_true",
                    help="the one-factor sweep of the fp_fma slot's fused families (fma_sweep_variants) in place of every case")
    ap.add_argument("--n-random", type=int, default=None, help="random vectors per bench (default 1500)")
    args = ap.parse_args(argv)
    if not shutil.which("verilator"):
        print("verilator not on PATH"); return 2
    if args.n_random:
        global N_RANDOM
        N_RANDOM = args.n_random
    lib = library_text()
    work = Path(tempfile.mkdtemp(prefix="chialu_fptest_"))
    jobs = []
    for fname in args.formats.split(","):
        fmt = parse_format(fname)
        e = engine_for(fmt, args.sr, tight=args.tight)
        pkg = package(e, fmt)
        for name, text, tb in cases(fmt, e, e.sr_bits, fma_sweep=args.fma_sweep):
            if args.only and args.only not in name:
                continue
            jobs.append((pkg, name + "_" + fname, text, tb))
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        results = list(pool.map(lambda j: run_case(j[0], lib, j[1], j[2], j[3], work), jobs))
    refused = [r for r in results if ": REFUSED " in r]
    fails = [r for r in results if "PASS" not in r and r not in refused]
    for r in refused + fails:
        print("  " + r[:400])
    print(f"[fptest] {len(results) - len(fails) - len(refused)}/{len(results)} pass"
          + (f", {len(refused)} refused by the generator's own rules" if refused else "") + f" ({work})")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
