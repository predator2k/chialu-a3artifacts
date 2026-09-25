"""The posit library against the engine: for a posit format, an engine
package (the engine's V/X declarations, unpack_posit, add/mul/div/sqrt,
pack_posit, and the packs of the conversion targets) and testbenches that
compare the library modules with the engine's functions bit for bit:
the decoders over every pattern (random at 32 bits), the encoders over
every pattern's X under two rounding modes and both ftz values plus
random sums, products and quotients under every mode, the X arithmetic
of the posit unit (the float library's adder, multiplier, divider and
square root on posit X values) after packing, the boundary converters
against the target's pack, and the PLAM multiplier within its 1/9
relative error bound.

    python3 -m chialu.targets.rtl.families.posittest [--formats posit8_0,posit8_1,posit16_1,posit16_2,posit32_2] [--only decode]
"""
from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from chialu.targets.rtl.engine import FW, Conventions, Engine, fmt_tag
from chialu.targets.rtl.families import fp as FP
from chialu.targets.rtl.families import posit as PS
from chialu.targets.rtl.families import library_text
from chialu.targets.rtl.families.fptest import run_case
from chialu.verify.formats import FloatFormat, PositFormat, parse_format

N_RANDOM = 3000
CVT_PAIRS = {"posit16_1": ("fp16", "fp32"), "posit8_0": ("fp8e4m3", "fp16"), "posit16_2": ("bf16",), "posit32_2": ("fp32",)}
FROM_FLOAT = {"posit16_1": ("fp16", "fp32"), "posit8_0": ("fp16",)}


def engine_for(fmt, targets=(), sr_bits: int = 8):
    return Engine("t", fmt, sr_bits, False, targets=[fmt] + list(targets), conv=Conventions())


def package(e, fmt, targets=()) -> str:
    parts = ["package tpkg;", e.vdecl(), e.rup_fn(), e.arith()]
    parts.append(e.unpack_posit(fmt, "s") if isinstance(fmt, PositFormat) else e.unpack_float(fmt, "s"))
    parts.append(e.pack_posit(fmt, "s") if isinstance(fmt, PositFormat) else e.pack_float(fmt, "s"))
    for t in targets:
        parts.append(e.pack_posit(t, fmt_tag(t)) if isinstance(t, PositFormat) else e.pack_float(t, fmt_tag(t)))
    parts.append("endpackage")
    return "\n".join(parts)


def _head(e, fmt, sr_bits=8):
    W, XT, VW = fmt.width, e.XT, e.VW
    n = fmt.width
    return f"""
module tb;
  import tpkg::*;
  logic [{W-1}:0] pa, pb; logic [{VW}:0] ua, ub; logic [{XT-1}:0] xa, xb; logic daz;
  longint i; integer errs = 0, tests = 0;
  logic [2:0] rnd; logic ftz; logic [{sr_bits-1}:0] word;
  assign ua = t_unpack_s(pa, daz); assign ub = t_unpack_s(pb, daz);
  assign xa = t_x(ua[{VW-1}:0]); assign xb = t_x(ub[{VW-1}:0]);
  function automatic [{W-1}:0] special(input integer k);
    case (k % 8)
      0: special = 0;                                     // zero
      1: special = {W}'d1;                                // minpos
      2: special = {W}'d{(1 << (n - 1)) - 1};             // maxpos
      3: special = {W}'d{1 << (n - 1)};                   // NaR
      4: special = {W}'d{(1 << (n - 1)) + 1};             // -maxpos
      5: special = {W}'d{(1 << n) - 1};                   // -minpos
      6: special = {W}'d{1 << (n - 2)};                   // 1.0
      default: special = {W}'d{(1 << n) - (1 << (n - 2))};  // -1.0
    endcase
  endfunction
"""


def tb_decode(e, fmt, module):
    W, VW = fmt.width, e.VW
    exhaustive = W <= 16
    loop = f"for (i = 0; i < {1 << W}; i = i + 1) begin pa = i[{W-1}:0]; daz = i[3];" if exhaustive else \
        f"for (i = 0; i < {8 * N_RANDOM}; i = i + 1) begin pa = $urandom; daz = i[3]; if (i % 8 == 3) pa = special(i / 8);"
    return _head(e, fmt) + f"""
  logic [{VW}:0] ul;
  {module} dut (.b(pa), .daz(daz), .u(ul));
  initial begin
    {loop}
      #1; tests = tests + 1;
      if (ua !== ul) begin errs = errs + 1; if (errs < 6) $display("MISMATCH b=%h ref=%h lib=%h", pa, ua, ul); end
    end
    if (errs == 0) $display("PASS %0d", tests); else $display("FAIL %0d of %0d", errs, tests);
    $finish;
  end
endmodule
"""


def tb_encode(e, fmt, module):
    W, XT, XW, EW = fmt.width, e.XT, e.XW, e.EW
    exhaustive = W <= 16
    loop = f"for (i = 0; i < {1 << W}; i = i + 1) begin pa = i[{W-1}:0]; #1; xr = xa;" if exhaustive else \
        f"for (i = 0; i < {4 * N_RANDOM}; i = i + 1) begin pa = $urandom; if (i % 8 == 3) pa = special(i / 8); #1; xr = xa;"
    return _head(e, fmt) + f"""
  logic [{XT-1}:0] xr; logic [{FW+W-1}:0] pr, pl; logic [{FW-1}:0] fl_l; logic [{W-1}:0] bits_l; logic sub;
  {module} dut (.x(xr), .rnd(rnd), .word(word), .ftz(ftz), .fl(fl_l), .bits(bits_l));
  task check(input integer nr); begin
    for (int r = 0; r < nr; r = r + 1) begin
      rnd = (nr == 2) ? (r ? 3'd4 : 3'd0) : r[2:0]; word = $urandom;
      for (int f = 0; f < 2; f = f + 1) begin
        ftz = f; #1;
        pr = t_pack_s(xr, rnd, word, ftz); pl = {{fl_l, bits_l}}; tests = tests + 1;
        if (pr !== pl) begin errs = errs + 1; if (errs < 6) $display("MISMATCH x=%h rnd=%0d ftz=%b ref=%h lib=%h", xr, rnd, ftz, pr, pl); end
      end
    end
  end endtask
  initial begin
    daz = 0;
    // every pattern's own X packs back to the pattern
    {loop}
      check(2);
    end
    // the X values of sums, products and quotients, and a few made specials
    for (i = 0; i < {N_RANDOM}; i = i + 1) begin
      pa = $urandom; pb = $urandom; sub = $urandom;
      if (i % 8 == 3) pa = special(i / 8);
      if (i % 8 == 7) pb = special(i / 8 + 3);
      #1;
      case (i % 6)
        0: xr = t_add(xa, xb, sub);
        1: xr = t_mul(xa, xb);
        2: xr = t_div(xa, xb);
        3: xr = t_add(t_mul(xa, xb), xb, sub);
        4: xr = {{2'd0, pa[0], xa[{XW+EW}:{XW+1}], {XW}'d0, 1'b1}};      // a lone sticky
        default: xr = t_sqrt(xa);
      endcase
      check(6);
    end
    xr = {{2'd2, 1'b0, {EW}'sd0, {XW}'d0, 1'b0}}; check(6);        // an infinity packs to NaR
    xr = {{2'd3, 1'b0, {EW}'sd0, {XW}'d0, 1'b0}}; check(6);
    if (errs == 0) $display("PASS %0d", tests); else $display("FAIL %0d of %0d", errs, tests);
    $finish;
  end
endmodule
"""


def tb_plam(e, fmt, module):
    XT, XW, EW = e.XT, e.XW, e.EW
    top = min(XW, 24)
    return _head(e, fmt) + f"""
  logic [{XT-1}:0] yl, yr, nl, nr; real rl, rr, ratio, err, worst = 0.0;
  logic signed [{EW-1}:0] el, er; integer d;
  {module} dut (.xa(xa), .xb(xb), .y(yl));
  function automatic real top_real(input [{XW-1}:0] sig);
    top_real = $itor(sig[{XW-1}:{XW-top}]);
  endfunction
  initial begin
    daz = 0;
    for (i = 0; i < {N_RANDOM}; i = i + 1) begin
      pa = $urandom; pb = $urandom;
      if (i % 8 == 3) pa = special(i / 8);
      if (i % 8 == 7) pb = special(i / 8 + 3);
      #1;
      yr = t_mul(xa, xb); tests = tests + 1;
      if (yr[{XT-1}:{XT-2}] != 2'd0 || yl[{XT-1}:{XT-2}] != 2'd0 || yr[{XW}:1] == 0 || yl[{XW}:1] == 0) begin
        // specials and zeros agree exactly (the sticky and exponent of a zero are free)
        if (yr[{XT-1}:{XT-2}] !== yl[{XT-1}:{XT-2}] || (yr[{XT-1}:{XT-2}] == 2'd0 && (yr[{XW}:1] == 0) != (yl[{XW}:1] == 0)) || (yr[{XT-1}:{XT-2}] != 2'd1 && yr[{XT-3}] !== yl[{XT-3}])) begin
          errs = errs + 1; if (errs < 6) $display("SPECIAL MISMATCH a=%h b=%h ref=%h lib=%h", xa, xb, yr, yl);
        end
      end else begin
        nl = t_norm(yl); nr = t_norm(yr);
        el = nl[{XW+EW}:{XW+1}]; er = nr[{XW+EW}:{XW+1}]; d = el - er;
        rl = top_real(nl[{XW}:1]); rr = top_real(nr[{XW}:1]);
        ratio = rl / rr * (2.0 ** d);
        err = (ratio > 1.0) ? ratio - 1.0 : 1.0 - ratio;
        if (err > worst) worst = err;
        if (err > 0.1112 || nl[{XT-3}] !== nr[{XT-3}]) begin errs = errs + 1; if (errs < 6) $display("BOUND a=%h b=%h ref=%h lib=%h err=%f", xa, xb, yr, yl, err); end
      end
    end
    if (errs == 0) $display("PASS %0d worst %f", tests, worst); else $display("FAIL %0d of %0d", errs, tests);
    $finish;
  end
endmodule
"""


def tb_xarith(e, fmt, module, op):
    """The float library's X modules on posit X values: the result packed
    into the posit format equals the engine function's."""
    W, XT = fmt.width, e.XT
    if op == "add":
        inst = f"{module} dut (.xa(xa), .xb(xb), .sub(sub), .y(yl));"
        ref = "t_add(xa, xb, sub)"
    elif op == "mul":
        inst = f"{module} dut (.xa(xa), .xb(xb), .y(yl));"
        ref = "t_mul(xa, xb)"
    elif op == "div":
        inst = f"{module} dut (.xa(xa), .xb(xb), .y(yl));"
        ref = "t_div(xa, xb)"
    else:
        inst = f"{module} dut (.xa(xa), .y(yl));"
        ref = "t_sqrt(xa)"
    return _head(e, fmt) + f"""
  logic sub; logic [{XT-1}:0] yl, yr; logic [{FW+W-1}:0] pr, pl;
  {inst}
  initial begin
    daz = 0; rnd = 0; word = 0; ftz = 0;
    for (i = 0; i < {N_RANDOM}; i = i + 1) begin
      pa = $urandom; pb = $urandom; sub = $urandom;
      if (i % 8 == 3) pa = special(i / 8);
      if (i % 8 == 7) pb = special(i / 8 + 3);
      #1;
      yr = {ref}; tests = tests + 1;
      pr = t_pack_s(yr, rnd, word, ftz); pl = t_pack_s(yl, rnd, word, ftz);
      if (pr !== pl) begin errs = errs + 1; if (errs < 6) $display("MISMATCH a=%h b=%h ref=%h lib=%h (x %h vs %h)", pa, pb, pr, pl, yr, yl); end
    end
    if (errs == 0) $display("PASS %0d", tests); else $display("FAIL %0d of %0d", errs, tests);
    $finish;
  end
endmodule
"""


def tb_cvt(e, src, tgt, module):
    """The boundary converter: a decoded `src` value into `tgt` against the
    engine's pack of the target."""
    W, XT, TW = src.width, e.XT, tgt.width
    ttag = fmt_tag(tgt)
    exhaustive = W <= 16
    loop = f"for (i = 0; i < {1 << W}; i = i + 1) begin pa = i[{W-1}:0];" if exhaustive else \
        f"for (i = 0; i < {4 * N_RANDOM}; i = i + 1) begin pa = $urandom; if (i % 8 == 3) pa = special(i / 8);"
    return _head(e, src) + f"""
  logic [{FW+TW-1}:0] pr, pl; logic [{FW-1}:0] fl_l; logic [{TW-1}:0] bits_l;
  {module} dut (.x(xa), .rnd(rnd), .word(word), .ftz(ftz), .fl(fl_l), .bits(bits_l));
  initial begin
    daz = 0;
    {loop}
      rnd = i % 6; word = $urandom; ftz = i[7]; #1;
      pr = t_pack_{ttag}(xa, rnd, word, ftz); pl = {{fl_l, bits_l}}; tests = tests + 1;
      if (pr !== pl) begin errs = errs + 1; if (errs < 6) $display("MISMATCH b=%h rnd=%0d ref=%h lib=%h", pa, rnd, pr, pl); end
    end
    if (errs == 0) $display("PASS %0d", tests); else $display("FAIL %0d of %0d", errs, tests);
    $finish;
  end
endmodule
"""


def cases(fmt) -> list:
    """[(name, package, module text, testbench)] of every posit variant of a format."""
    out = []
    tokens = Conventions().tokens()
    e = engine_for(fmt)
    g = FP.Geom.of_engine(e)
    pkg = package(e, fmt)
    for regime in ("lzc_plus_shifter", "two_stage_masked_decode"):
        for rep in ("sign_magnitude", "twos_complement"):
            n, t = PS.decode_sv(fmt, g, "posit_adder_multiplier", {"regime_decode": regime, "internal_representation": rep})
            out.append((n, pkg, t, tb_decode(e, fmt, n)))
    for rep in ("sign_magnitude", "twos_complement"):
        n, t = PS.encode_sv(fmt, g, "posit_adder_multiplier", {"internal_representation": rep}, tokens)
        out.append((n, pkg, t, tb_encode(e, fmt, n)))
    n, t = PS.decode_sv(fmt, g, "posit_ieee_interop", {}, name=f"fam_posit_decode_interop_{fmt_tag(fmt)}")
    out.append((n, pkg, t, tb_decode(e, fmt, n)))
    n, t = PS.plam_sv(g)
    out.append((n, pkg, t, tb_plam(e, fmt, n)))
    if fmt.width <= 16:
        # the X arithmetic of the posit unit: the float library on posit X values
        n, t = FP.add_sv(g, "single_path", {"sig_adder.family": "carry_select"}, name=f"fam_posit_xadd_{g.tag()}")
        out.append((n, pkg, t, tb_xarith(e, fmt, n, "add")))
        n, t = FP.mul_sv(g, "sig_mul_then_round", {}, name=f"fam_posit_xmul_{g.tag()}")
        out.append((n, pkg, t, tb_xarith(e, fmt, n, "mul")))
        n, t = FP.div_sv(g, "sig_div_then_round", {"sig_div.family": "restoring_nonrestoring"}, name=f"fam_posit_xdiv_{g.tag()}")
        out.append((n, pkg, t, tb_xarith(e, fmt, n, "div")))
        n, t = FP.sqrt_sv(g, "sig_sqrt_then_round", {"sig_sqrt.family": "digit_recurrence_sqrt_combined"}, name=f"fam_posit_xsqrt_{g.tag()}")
        out.append((n, pkg, t, tb_xarith(e, fmt, n, "sqrt")))
    # the boundary converters out of the posit lane
    for tname in CVT_PAIRS.get(fmt.name, ()):
        tgt = parse_format(tname)
        e2 = engine_for(fmt, [tgt])
        g2 = FP.Geom.of_engine(e2)
        n, t = PS.cvt_sv(fmt, tgt, g2, "posit_ieee_interop", {"interop_style": "boundary_converters"}, e2.tokens)
        out.append((n, package(e2, fmt, [tgt]), t, tb_cvt(e2, fmt, tgt, n)))
    # into the posit format from a float lane
    for sname in FROM_FLOAT.get(fmt.name, ()):
        src = parse_format(sname)
        e3 = engine_for(src, [fmt])
        g3 = FP.Geom.of_engine(e3)
        for rep in ("sign_magnitude", "twos_complement"):
            n, t = PS.cvt_sv(src, fmt, g3, "posit_ieee_interop", {"interop_style": "boundary_converters", "internal_representation": rep},
                             e3.tokens, name=f"fam_posit_cvt_{fmt_tag(src)}_to_{fmt_tag(fmt)}_{rep[:4]}_{g3.tag()}")
            out.append((n, package(e3, src, [fmt]), t, tb_cvt(e3, src, fmt, n)))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--formats", default="posit8_0,posit8_1,posit16_1,posit16_2,posit32_2")
    ap.add_argument("--only", default=None)
    ap.add_argument("--jobs", type=int, default=8)
    args = ap.parse_args(argv)
    if not shutil.which("verilator"):
        print("verilator not on PATH")
        return 2
    lib = library_text()
    work = Path(tempfile.mkdtemp(prefix="chialu_posit_"))
    jobs = []
    for f in args.formats.split(","):
        fmt = parse_format(f)
        for name, pkg, text, tb in cases(fmt):
            if args.only and args.only not in name:
                continue
            jobs.append((pkg, lib, name, text, tb))
    results = []
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        for r in pool.map(lambda j: run_case(j[0], j[1], j[2], j[3], j[4], work), jobs):
            print("  " + ("ok   " if r.endswith("PASS") or " PASS " in r else "FAIL ") + r, flush=True)
            results.append(r)
    n_ok = sum(1 for r in results if r.endswith("PASS") or " PASS " in r)
    print(f"[posit library] {n_ok}/{len(results)} pass ({work})")
    return 0 if n_ok == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
