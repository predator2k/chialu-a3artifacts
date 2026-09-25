// ADIR-MEMBER packages
// alu_core_m0_pkg: the exact-arithmetic functions of mode 0 (1xfp16)
package alu_core_m0_pkg;

  // ---- m0: V = {special[1:0], sign, exp[13] (signed), sig[11]}
  //           X = {special[1:0], sign, exp[13] (signed), sig[26], sticky}
  localparam int m0_SW = 11, m0_EW = 13, m0_XW = 26;
  localparam int m0_VW = 27, m0_XT = 43;
  function automatic [26:0] m0_mkv(input [1:0] sp, input s, input signed [12:0] e, input [10:0] sig);
    m0_mkv = {sp, s, e, sig};
  endfunction
  function automatic [42:0] m0_mkx(input [1:0] sp, input s, input signed [12:0] e, input [25:0] sig, input st);
    m0_mkx = {sp, s, e, sig, st};
  endfunction
  function automatic [42:0] m0_x(input [26:0] v);   // widen V to X
    m0_x = {v[26:26-1], v[26-2], v[26-3 -: 13], {{(26-11){1'b0}}, v[10:0]}, 1'b0};
  endfunction
  // normalize: leading one at bit XW-1 (zero stays zero)
  function automatic [42:0] m0_norm(input [42:0] x);
    logic [25:0] s; logic signed [12:0] e; integer k;
    s = x[26:1]; e = x[26+13:26+1];
    if (s != 0) begin
      for (k = 16; k >= 1; k = k / 2) begin
        if (k < 26) begin
          if (s[25 -: 1] == 1'b0 && (s >> (26 - k)) == 0) begin
            s = s << k; e = e - k;
          end
        end
      end
    end
    m0_norm = {x[42:42-1], x[42-2], e, s, x[0]};
  endfunction

  function automatic m0_rup(input [2:0] rnd, input s, input inexact, input [26:0] rest, input [26:0] halfv,
                             input st, input lsb, input [26+8:0] fint, input [7:0] word);
    logic gt_half, half_eq;
    gt_half = rest > halfv; half_eq = (rest == halfv) && (halfv != 0);
    case (rnd)
      3'd0: m0_rup = gt_half || (half_eq && (st || lsb));
      3'd1: m0_rup = 1'b0;
      3'd2: m0_rup = inexact && s;
      3'd3: m0_rup = inexact && !s;
      3'd4: m0_rup = inexact && (0 ? (fint >= word) : (fint > word));
      default: m0_rup = inexact;   // 5: away from zero
    endcase
  endfunction

  // a +/- b on X (normalized inputs); specials: nan wins, inf-inf = nan
  function automatic [42:0] m0_add(input [42:0] a, input [42:0] b, input sub);
    logic [42:0] na, nb, big, sml; logic [1:0] spa, spb; logic sa, sb, sr, sw;
    logic signed [12:0] ea, eb, d; logic [26:0] ms, mb, r; logic st, stb; integer sh;
    na = m0_norm(a); nb = m0_norm(b);
    spa = na[42:42-1]; spb = nb[42:42-1];
    sa = na[42-2]; sb = nb[42-2] ^ sub;
    if (spa == 2'd1 || spb == 2'd1) m0_add = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 && spb == 2'd2) m0_add = (sa == sb) ? m0_mkx(2'd2, sa, 0, 0, 1'b0) : m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m0_add = m0_mkx(2'd2, sa, 0, 0, 1'b0);
    else if (spb == 2'd2) m0_add = m0_mkx(2'd2, sb, 0, 0, 1'b0);
    else if (na[26:1] == 0 && !na[0]) m0_add = {nb[42:42-1], sb, nb[42-3:0]};
    else if (nb[26:1] == 0 && !nb[0]) m0_add = na;
    else begin
      ea = na[26+13:26+1]; eb = nb[26+13:26+1];
      // order by magnitude (both normalized): larger exponent, then sig
      if (ea > eb || (ea == eb && na[26:1] >= nb[26:1])) begin big = na; sml = nb; sw = 1'b0; end
      else begin big = nb; sml = na; sw = 1'b1; end
      d = big[26+13:26+1] - sml[26+13:26+1];
      ms = {1'b0, sml[26:1]}; stb = sml[0];
      if (d > 26 + 1) begin stb = stb | (ms != 0); ms = 0; end
      else begin
        for (sh = 0; sh < 26 + 2; sh = sh + 1) begin
          if (sh < d) begin stb = stb | ms[0]; ms = ms >> 1; end
        end
      end
      mb = {1'b0, big[26:1]}; st = big[0] | stb;
      if ((sw ? sb : sa) == (sw ? sa : sb)) begin
        r = mb + ms;
        sr = sw ? sb : sa;
      end else begin
        // subtract: the sticky of the smaller operand borrows one lsb
        r = mb - ms - (stb ? 1'b1 : 1'b0);
        sr = sw ? sb : sa;
        if (r == 0 && !st) sr = 1'b0;
      end
      if (r[26]) begin st = st | r[0]; r = r >> 1; m0_add = m0_mkx(2'd0, sr, big[26+13:26+1] + 1, r[25:0], st); end
      else m0_add = m0_mkx(2'd0, sr, big[26+13:26+1], r[25:0], st);
    end
  endfunction
  function automatic [42:0] m0_mul(input [42:0] a, input [42:0] b);
    logic [42:0] na, nb; logic [1:0] spa, spb; logic s; logic [2*26-1:0] pr; logic st; integer k;
    na = m0_norm(a); nb = m0_norm(b);
    spa = na[42:42-1]; spb = nb[42:42-1]; s = na[42-2] ^ nb[42-2];
    if (spa == 2'd1 || spb == 2'd1) m0_mul = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 || spb == 2'd2) begin
      if ((spa == 2'd0 && na[26:1] == 0 && !na[0]) || (spb == 2'd0 && nb[26:1] == 0 && !nb[0]))
        m0_mul = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
      else m0_mul = m0_mkx(2'd2, s, 0, 0, 1'b0);
    end else begin
      pr = na[26:1] * nb[26:1];
      st = na[0] | nb[0];
      // keep the top XW bits of the product, the rest folds into sticky
      st = st | (pr[25:0] != 0);
      m0_mul = m0_mkx(2'd0, s, na[26+13:26+1] + nb[26+13:26+1] + 26, pr[2*26-1:26], st);
    end
  endfunction
  // restoring division (a << XW) / dv of two XW-bit significands with dv
  // normalized (dv >= 2^(XW-1)): {q[XW:0], r[XW:0]}, XW+1 quotient bits.
  // The first step compares a itself (the partial remainder after the
  // dividend's top XW bits: with dv normalized no earlier step can
  // subtract, so those steps are omitted), then one step per zero bit
  // shifted in. Every step assigns r and q unconditionally (a ternary on
  // the compare): the loop unrolls into straight-line logic rather than
  // a chain of if/else switches in one process, which yosys's latch
  // analysis (proc_dlatch) never finishes on
  function automatic [2*26+1:0] m0_udiv(input [25:0] a, input [25:0] dv);
    logic [26+1:0] r; logic [26:0] q; logic ge; integer i;
    r = {2'b0, a}; q = 0;
    for (i = 26; i >= 0; i = i - 1) begin
      ge = (r >= {2'b0, dv});
      r = ge ? r - {2'b0, dv} : r;
      q = {q[25:0], ge};
      if (i > 0) r = {r[26:0], 1'b0};
    end
    m0_udiv = {q, r[26:0]};
  endfunction
  // the exact product: {special[1:0], sign, exp[EW], sig[2XW]} (no sticky)
  function automatic [2*26+13+2:0] m0_mulx(input [42:0] a, input [42:0] b);
    logic [42:0] na, nb; logic [1:0] spa, spb, sp; logic s; logic [2*26-1:0] pr;
    na = m0_norm(a); nb = m0_norm(b);
    pr = na[26:1] * nb[26:1];
    spa = na[42:42-1]; spb = nb[42:42-1]; s = na[42-2] ^ nb[42-2];
    if (spa == 2'd1 || spb == 2'd1) sp = 2'd1;
    else if (spa == 2'd2 || spb == 2'd2)
      sp = ((spa == 2'd0 && na[26:1] == 0) || (spb == 2'd0 && nb[26:1] == 0)) ? 2'd1 : 2'd2;
    else sp = 2'd0;
    m0_mulx = {sp, s, na[26+13:26+1] + nb[26+13:26+1], pr};
  endfunction
  function automatic [42:0] m0_div(input [42:0] a, input [42:0] b);
    logic [42:0] na, nb; logic [1:0] spa, spb; logic s; logic [2*26+1:0] qr; logic [26:0] q, r;
    na = m0_norm(a); nb = m0_norm(b);
    spa = na[42:42-1]; spb = nb[42:42-1]; s = na[42-2] ^ nb[42-2];
    if (spa == 2'd1 || spb == 2'd1) m0_div = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 && spb == 2'd2) m0_div = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m0_div = m0_mkx(2'd2, s, 0, 0, 1'b0);
    else if (spb == 2'd2) m0_div = m0_mkx(2'd0, s, 0, 0, 1'b0);
    else if (nb[26:1] == 0 && !nb[0]) begin
      if (na[26:1] == 0 && !na[0]) m0_div = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
      else m0_div = m0_mkx(2'd2, s, 0, 0, 1'b0);
    end else if (na[26:1] == 0 && !na[0]) m0_div = m0_mkx(2'd0, s, 0, 0, 1'b0);
    else begin
      qr = m0_udiv(na[26:1], nb[26:1]);     // both normalized: nonzero finite
      q = qr[2*26+1:26+1]; r = qr[26:0];
      // q < 2^(XW+1): drop one bit when it carries
      if (q[26]) m0_div = m0_mkx(2'd0, s, na[26+13:26+1] - nb[26+13:26+1] - 26 + 1, q[26:1], (r != 0) | q[0] | na[0] | nb[0]);
      else m0_div = m0_mkx(2'd0, s, na[26+13:26+1] - nb[26+13:26+1] - 26, q[25:0], (r != 0) | na[0] | nb[0]);
    end
  endfunction
  function automatic [42:0] m0_sqrt(input [42:0] a);
    logic [42:0] na; logic [1:0] spa; logic signed [12:0] e; logic [26:0] m; logic [2*26+3:0] rad;
    logic [26+2:0] rem, trial; logic [26:0] root; logic ge; integer i;
    na = m0_norm(a); spa = na[42:42-1];
    if (spa == 2'd1) m0_sqrt = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m0_sqrt = na[42-2] ? m0_mkx(2'd1, 1'b0, 0, 0, 1'b0) : na;
    else if (na[26:1] == 0 && !na[0]) m0_sqrt = na;
    else if (na[42-2]) m0_sqrt = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else begin
      e = na[26+13:26+1];
      // value = m * 2^e with e even; radicand = m * 2^(2K): root = sqrt(m) * 2^K, XW+1 bits
      if (e[0]) begin m = {na[26:1], 1'b0}; e = e - 1; end
      else m = {1'b0, na[26:1]};
      rad = {{(26+3){1'b0}}, m} << 26;
      rem = 0; root = 0;
      for (i = 26; i >= 0; i = i - 1) begin
        rem = {rem[26:0], rad[2*i +: 2]};
        trial = {root, 2'b01};
        ge = (rem >= trial);                  // unconditional assignments, as in udiv
        rem = ge ? rem - trial : rem;
        root = {root[25:0], ge};
      end
      m0_sqrt = m0_mkx(2'd0, 1'b0, (e >>> 1) - 13 + 1, root[26:1], (rem != 0) | root[0] | na[0]);
    end
  endfunction
  // X ordering treats NaN as unordered and compares finite values by sign and magnitude
  function automatic m0_lt(input [42:0] a, input [42:0] b);
    logic [42:0] na, nb; logic za, zb, sa, sb, mag_lt; logic signed [12:0] ea, eb;
    na = m0_norm(a); nb = m0_norm(b);
    za = (na[26:1] == 0) && !na[0]; zb = (nb[26:1] == 0) && !nb[0];
    sa = na[42-2] && !za; sb = nb[42-2] && !zb;
    if (na[42:42-1] == 2'd1 || nb[42:42-1] == 2'd1) m0_lt = 1'b0;
    else if (na[42:42-1] == 2'd2 || nb[42:42-1] == 2'd2) begin
      if (na[42:42-1] == 2'd2 && nb[42:42-1] == 2'd2) m0_lt = na[42-2] && !nb[42-2];
      else if (na[42:42-1] == 2'd2) m0_lt = na[42-2];
      else m0_lt = !nb[42-2];
    end else if (za && zb) m0_lt = 1'b0;
    else if (sa != sb) m0_lt = sa;
    else begin
      ea = na[26+13:26+1]; eb = nb[26+13:26+1];
      if (za) mag_lt = 1'b1; else if (zb) mag_lt = 1'b0;
      else mag_lt = (ea < eb) || (ea == eb && (na[26:1] < nb[26:1] || (na[26:1] == nb[26:1] && !na[0] && nb[0])));
      m0_lt = sa ? !mag_lt && !(za && zb) && !m0_eq(na, nb) : mag_lt;
    end
  endfunction
  function automatic m0_eq(input [42:0] a, input [42:0] b);
    logic [42:0] na, nb; logic za, zb;
    na = m0_norm(a); nb = m0_norm(b);
    za = (na[26:1] == 0) && !na[0]; zb = (nb[26:1] == 0) && !nb[0];
    if (na[42:42-1] == 2'd1 || nb[42:42-1] == 2'd1) m0_eq = 1'b0;
    else if (na[42:42-1] == 2'd2 || nb[42:42-1] == 2'd2)
      m0_eq = (na[42:42-1] == nb[42:42-1]) && (na[42-2] == nb[42-2]);
    else if (za || zb) m0_eq = za && zb;
    else m0_eq = (na[42-2] == nb[42-2]) && (na[26+13:26+1] == nb[26+13:26+1]) && (na[26:1] == nb[26:1]) && (na[0] == nb[0]);
  endfunction

  // fp16 pattern -> V (bit VW = denormal-read flag returned beside)
  function automatic [27:0] m0_unpack_s(input [15:0] b, input daz);
    logic [4:0] e; logic [9:0] m; logic [10:0] sig; logic signed [12:0] ex; logic den, s;
    e = b[14:10]; m = b[9:0]; s = b[15]; den = 1'b0; sig = 0; ex = 0;
    if ((e == 5'd31 && m != 0)) m0_unpack_s = {1'b0, m0_mkv(2'd1, 1'b0, 0, 0)};
    else if ((e == 5'd31 && m == 0)) m0_unpack_s = {1'b0, m0_mkv(2'd2, s, 0, 0)};
    else begin
    if (e == 0) begin sig = {{(11-10){1'b0}}, m}; ex = -24; if (m != 0) den = 1'b1; if (daz && m != 0) sig = 0; end
    else begin sig = {{(11-10-1){1'b0}}, 1'b1, m}; ex = e - 25; end
      m0_unpack_s = {den, m0_mkv(2'd0, s, ex, sig)};
    end
  endfunction

  // X -> fp16 (fp16): sign(1) exp 5 man 10, top field 30, max finite 15'd31743
  function automatic [10+16-1:0] m0_pack_fp16(input [42:0] x0, input [2:0] rnd, input [7:0] word, input ftz);
    logic [42:0] x; logic [1:0] sp; logic s; logic signed [12:0] e, eu, biased; logic [25:0] sig;
    logic st, inexact, up, upn, half_eq, gt_half, tiny, ovf, unf, carry_n, to_inf; integer sh, shn, sht;
    logic [26:0] keep, rest, keepn, restn, halfv, halfn; logic [26+8:0] fint, fintn; logic [10-1:0] fl;
    logic [16+13:0] code; logic [16:0] mag; logic [16-1:0] outb;
    x = m0_norm(x0); sp = x[42:42-1]; s = x[42-2] & 1; sig = x[26:1]; st = x[0]; e = x[26+13:26+1];
    fl = 0; outb = 0;
    if (sp == 2'd1) begin fl[5] = 1'b1; outb = 16'd32256; end
    else if (sp == 2'd2) begin
      outb = {s, 15'd31744}; if (!1) begin fl[4] = 1'b1; fl[2] = 1'b1; end
    end else if (sig == 0 && !st) begin outb = 1 ? 0 : {s, {15{1'b0}}}; end
    else begin
      if (sig == 0) begin sig = 1 << 25; e = e - (2*26-1); end // normalize the lone sticky's tiny value
      eu = e + 25;                 // exponent of the leading one
      biased = eu + 15;
      shn = 26 - 1 - 10;           // bits dropped at the normal precision
      sh = (biased >= 1) ? shn : shn + (1 - biased);
      sht = sh;
      if (sh > 26 + 1) sh = 26 + 1;
      keep = {1'b0, sig} >> sh; rest = {1'b0, sig} & ((sh > 26) ? {(26+1){1'b1}} : ({1'b0, {26{1'b1}}} >> (26 - sh)));
      halfv = (sh == 0) ? 0 : ({{26{1'b0}}, 1'b1} << (sh - 1));
      keepn = {1'b0, sig} >> shn; restn = {1'b0, sig} & ({1'b0, {26{1'b1}}} >> (26 - shn));
      halfn = (shn == 0) ? 0 : ({{26{1'b0}}, 1'b1} << (shn - 1));
      inexact = (rest != 0) | st;
      fint = (sht - 8 > 26) ? 0 : (sht >= 8) ? (rest >> (sht - 8)) : (rest << (8 - sht));
      fintn = (shn >= 8) ? (restn >> (shn - 8)) : (restn << (8 - shn));
      up = m0_rup(rnd, s, inexact, rest, halfv, st, keep[0], fint, word);
      upn = m0_rup(rnd, s, (restn != 0) | st, restn, halfn, st, keepn[0], fintn, word);
      carry_n = ((keepn + upn) == ({{26{1'b0}}, 1'b1} << (10 + 1)));
      mag = keep + up;
      if (biased < 1) biased = 0;
      code = (biased < 1) ? mag : ((biased << 10) + mag - ({{(16+13){1'b0}}, 1'b1} << 10));
      tiny = 0 ? (eu < -14) : ((eu < -14) && !(eu == -14 - 1 && carry_n) && !(eu + 15 == 0 && carry_n));
      ovf = (code > 15'd31743);
      if (ovf) begin
        to_inf = 1 && (rnd == 3'd0 || (rnd == 3'd3 && !s) || (rnd == 3'd2 && s) || rnd == 3'd5 || (rnd == 3'd4 && (eu > 15 || up)));
        outb = to_inf ? {s, 15'd31744} : {s, 15'd31743};
        fl[2] = 1'b1; fl[4] = 1'b1;
      end else begin
        outb = {s, code[14:0]};
        if (inexact) fl[4] = 1'b1;
        if (tiny && inexact) fl[3] = 1'b1;
        if (ftz && code[15-1:10] == 0 && code[9:0] != 0) begin
          outb = {s, {15{1'b0}}}; fl[4] = 1'b1; fl[3] = 1'b1;
        end

      end
    end
    m0_pack_fp16 = {fl, outb};
  endfunction
endpackage
// ADIR-MEMBER top
// EVOLVE-BLOCK-START
// ADIR-DECL v1
// STRUCTURE m0.l0.fp_adder kind=fp_adder slot=fp_adder mode=0 lane=0 width=16 format=fp16 ops=fadd,fsub sv=alu_core_u_m0_l0_fp_adder
// STRUCTURE m0.l0.unpacker kind=unpacker slot=unpacker mode=0 lane=0 width=16 format=fp16 ops=fadd,fsub,fmul sv=alu_core_u_m0_l0_unpacker
// STRUCTURE m0.l0.rounder kind=rounder slot=rounder mode=0 lane=0 width=16 format=fp16 ops=fadd,fsub,fmul sv=alu_core_u_m0_l0_rounder
// STRUCTURE m0.l0.fp_fma kind=fp_fma slot=fp_fma mode=0 lane=0 width=16 format=fp16 ops=fadd,fsub,fmul
// STRUCTURE m0.l0.fp_multiplier kind=fp_multiplier slot=fp_multiplier mode=0 lane=0 width=16 format=fp16 ops=fmul sv=alu_core_u_m0_l0_fp_multiplier
// ADIR-END
module alu_core (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [1:0] op,
  output logic [15:0] y,
  output logic [3:0] flags
);
  // alu_core: behavioral reference derived from the instance (modes 1xfp16; ops fadd, fsub, fmul). Every (mode, op) pair computes the verify layer's exact semantics.
  // HIERARCHY: 4 physical structure modules instantiated by alu_core, built from 4 lane modules (one per mode and kind, parameter LANE) and 1 packages of engine functions (one per mode); a float mode's datapath is split into an unpacker (the xa/xb/den buses), the arithmetic and converter structures (unrounded results on the x bus) and a rounder (y and the flags); 0 misc lane modules and 0 block-conversion group modules
  // UNIT m0.l0.fp_adder module=alu_core_u_m0_l0_fp_adder kind=fp_adder members=m0.l0.fp_adder
  // UNIT m0.l0.unpacker module=alu_core_u_m0_l0_unpacker kind=unpacker members=m0.l0.unpacker
  // UNIT m0.l0.rounder module=alu_core_u_m0_l0_rounder kind=rounder members=m0.l0.rounder
  // UNIT m0.l0.fp_multiplier module=alu_core_u_m0_l0_fp_multiplier kind=fp_multiplier members=m0.l0.fp_multiplier
  // // STRUCTURE m0.l0.fp_adder kind=fp_adder slot=fp_adder mode=0 lane=0 width=16 format=fp16 ops=fadd,fsub sv=alu_core_u_m0_l0_fp_adder
  // // STRUCTURE m0.l0.unpacker kind=unpacker slot=unpacker mode=0 lane=0 width=16 format=fp16 ops=fadd,fsub,fmul sv=alu_core_u_m0_l0_unpacker
  // // STRUCTURE m0.l0.rounder kind=rounder slot=rounder mode=0 lane=0 width=16 format=fp16 ops=fadd,fsub,fmul sv=alu_core_u_m0_l0_rounder
  // // STRUCTURE m0.l0.fp_fma kind=fp_fma slot=fp_fma mode=0 lane=0 width=16 format=fp16 ops=fadd,fsub,fmul
  // // STRUCTURE m0.l0.fp_multiplier kind=fp_multiplier slot=fp_multiplier mode=0 lane=0 width=16 format=fp16 ops=fmul sv=alu_core_u_m0_l0_fp_multiplier
  // LIBRARY: fam_adder_ripple_carry, fam_adder_ripple_chunk, fam_count_lzd_pair_cell_binary_count_vflat_w11, fam_count_lzd_pair_cell_binary_count_vflat_w26, fam_fp_add_single_path_x26e13s11_p9d459d224988, fam_fp_mul_sig_mul_then_round_x26e13s11_pbd766efe148c, fam_fp_round_dedicated_per_op_increment_adder_fp16_x26e13s11_pd77ccc5b5c45, fam_fp_unpack_per_unit_unpack_fp16_x26e13s11_p9bfe39588414, fam_incr_prefix_and, fam_mul_behavioral_star_w11_u_pfc463c41, fam_shift_barrel_mux_tree, fam_shift_keep_mask, fam_shift_stage (chialu.targets.rtl.families: the modules of the declared families the lane modules instantiate; their text follows the generated modules)
  logic [2:0] rnd_sel;
  logic [2:0] rnd;
  logic daz;
  logic ftz;
  logic dual;
  logic [15:0] y_m0_m0_l0_fp_adder;
  logic [9:0] fl_m0_m0_l0_fp_adder;
  logic [42:0] x_m0_m0_m0_l0_fp_adder;
  logic [42:0] xa_m0_m0_m0_l0_unpacker;
  logic [42:0] xb_m0_m0_m0_l0_unpacker;
  logic dena_m0_m0_m0_l0_unpacker;
  logic denb_m0_m0_m0_l0_unpacker;
  logic [15:0] y_m0_m0_l0_rounder;
  logic [9:0] fl_m0_m0_l0_rounder;
  logic [15:0] y_m0_m0_l0_fp_multiplier;
  logic [9:0] fl_m0_m0_l0_fp_multiplier;
  logic [42:0] x_m0_m0_m0_l0_fp_multiplier;
  logic [15:0] y_m0;
  logic [9:0] fl_m0;
  logic [42:0] x_m0;
  logic [42:0] xa_m0;
  logic [42:0] xb_m0;
  logic dena_m0;
  logic denb_m0;
  logic [9:0] fl_all;
  assign rnd_sel = 3'd0;
  assign rnd = rnd_sel;
  assign daz = 1'b0;
  assign ftz = 1'b0;
  assign dual = 1'b0;
  assign y_m0 = y_m0_m0_l0_fp_adder | y_m0_m0_l0_rounder | y_m0_m0_l0_fp_multiplier;
  assign fl_m0 = fl_m0_m0_l0_fp_adder | fl_m0_m0_l0_rounder | fl_m0_m0_l0_fp_multiplier;
  assign x_m0 = x_m0_m0_m0_l0_fp_adder | x_m0_m0_m0_l0_fp_multiplier;
  assign xa_m0 = xa_m0_m0_m0_l0_unpacker;
  assign xb_m0 = xb_m0_m0_m0_l0_unpacker;
  assign dena_m0 = dena_m0_m0_m0_l0_unpacker;
  assign denb_m0 = denb_m0_m0_m0_l0_unpacker;
  alu_core_u_m0_l0_fp_adder u_m0_l0_fp_adder (.a(a), .b(b), .op(op), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_m0_l0_fp_adder), .fl_m0(fl_m0_m0_l0_fp_adder), .xa_m0(xa_m0), .xb_m0(xb_m0), .dena_m0(dena_m0), .denb_m0(denb_m0), .x_m0(x_m0_m0_m0_l0_fp_adder));
  alu_core_u_m0_l0_unpacker u_m0_l0_unpacker (.a(a), .b(b), .op(op), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .xa_m0(xa_m0_m0_m0_l0_unpacker), .xb_m0(xb_m0_m0_m0_l0_unpacker), .dena_m0(dena_m0_m0_m0_l0_unpacker), .denb_m0(denb_m0_m0_m0_l0_unpacker));
  alu_core_u_m0_l0_rounder u_m0_l0_rounder (.a(a), .b(b), .op(op), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_m0_l0_rounder), .fl_m0(fl_m0_m0_l0_rounder), .xa_m0(xa_m0), .xb_m0(xb_m0), .dena_m0(dena_m0), .denb_m0(denb_m0), .x_m0(x_m0));
  alu_core_u_m0_l0_fp_multiplier u_m0_l0_fp_multiplier (.a(a), .b(b), .op(op), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_m0_l0_fp_multiplier), .fl_m0(fl_m0_m0_l0_fp_multiplier), .xa_m0(xa_m0), .xb_m0(xb_m0), .dena_m0(dena_m0), .denb_m0(denb_m0), .x_m0(x_m0_m0_m0_l0_fp_multiplier));
  assign y = y_m0;
  assign fl_all = fl_m0;
  assign flags[0] = fl_all[0];
  assign flags[1] = fl_all[2];
  assign flags[2] = fl_all[3];
  assign flags[3] = fl_all[4];
endmodule
// EVOLVE-BLOCK-END

module alu_core_m0_fp_adder #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [1:0] op,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m0,
  output logic [9:0] fl_m0,
  input  logic [42:0] xa_m0,
  input  logic [42:0] xb_m0,
  input  logic [0:0] dena_m0,
  input  logic [0:0] denb_m0,
  output logic [42:0] x_m0
);
  // alu_core_m0_fp_adder: lane LANE of mode 0 (fp16) for the fp_adder ops fadd, fsub; the result buses are the mode's, with only this lane's bits written
  import alu_core_m0_pkg::*;
  logic d_m0;
  logic [15:0] m0_aLANE;
  logic [15:0] m0_bLANE;
  logic [27:0] m0_uaLANE;
  logic [27:0] m0_ubLANE;
  logic [42:0] m0_xa [0:0];
  logic m0_dena [0:0];
  logic [42:0] m0_xb [0:0];
  logic m0_denb [0:0];
  logic [42:0] m0_fa_xaLANE;
  logic [42:0] m0_fa_xbLANE;
  logic m0_fa_subLANE;
  logic [42:0] m0_fa_yLANE;
  logic [25:0] m0_o0t0_LANE;
  logic [42:0] m0_o0t0_LANE_x;
  logic [42:0] m0_o0t0_LANE_z;
  logic [25:0] m0_o1t0_LANE;
  logic [42:0] m0_o1t0_LANE_x;
  logic [42:0] m0_o1t0_LANE_z;
  assign m0_aLANE = a[(LANE*16) +: 16];
  assign m0_bLANE = b[(LANE*16) +: 16];
  // structure core.unpacker.m0: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp16_x26e13s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp16_x26e13s11_p9bfe39588414 u_m0_unpack_aLANE (.b(m0_aLANE), .daz(daz), .u(m0_uaLANE));
  // structure core.unpacker.m0: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp16_x26e13s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp16_x26e13s11_p9bfe39588414 u_m0_unpack_bLANE (.b(m0_bLANE), .daz(daz), .u(m0_ubLANE));
  assign m0_xa[LANE] = m0_x(m0_uaLANE[26:0]);
  assign m0_dena[LANE] = m0_uaLANE[27];
  assign m0_xb[LANE] = m0_x(m0_ubLANE[26:0]);
  assign m0_denb[LANE] = m0_ubLANE[27];
  // structure core.fp_adder.m0: family single_path realized by the library module fam_fp_add_single_path_x26e13s11_p9d459d224988
  fam_fp_add_single_path_x26e13s11_p9d459d224988 u_m0_faddLANE (.xa(m0_fa_xaLANE), .xb(m0_fa_xbLANE), .sub(m0_fa_subLANE), .y(m0_fa_yLANE));
  always_comb begin
    y_m0 = '0; d_m0 = '0; fl_m0 = '0;
    m0_fa_xaLANE = 'x; m0_fa_xbLANE = 'x; m0_fa_subLANE = 'x; m0_o0t0_LANE = 'x; m0_o0t0_LANE_x = 'x; m0_o0t0_LANE_z = 'x;
    m0_o1t0_LANE = 'x; m0_o1t0_LANE_x = 'x; m0_o1t0_LANE_z = 'x;
    x_m0 = '0;
    case (op)
      2'd0: begin
        m0_fa_xaLANE = m0_xa[LANE]; m0_fa_xbLANE = m0_xb[LANE]; m0_fa_subLANE = 1'b0; m0_o0t0_LANE_x = m0_fa_yLANE;
        m0_o0t0_LANE_z = { m0_o0t0_LANE_x[42:41], (m0_o0t0_LANE_x[42:41] == 2'd0 && m0_o0t0_LANE_x[26:0] == 0) ? (((m0_xa[LANE][42:41] == 2'd0 && m0_xa[LANE][26:0] == 0) && (m0_xb[LANE][42:41] == 2'd0 && m0_xb[LANE][26:0] == 0)) ? ((rnd == 3'd2) ? (m0_aLANE[15] | (m0_bLANE[15] ^ 1'b0)) : (m0_aLANE[15] & (m0_bLANE[15] ^ 1'b0))) : ((rnd == 3'd2) ? 1'b1 : 1'b0)) : m0_o0t0_LANE_x[40], m0_o0t0_LANE_x[39:0] };
        x_m0[LANE*43 +: 43] = m0_o0t0_LANE_z;
      end
      2'd1: begin
        m0_fa_xaLANE = m0_xa[LANE]; m0_fa_xbLANE = m0_xb[LANE]; m0_fa_subLANE = 1'b1; m0_o1t0_LANE_x = m0_fa_yLANE;
        m0_o1t0_LANE_z = { m0_o1t0_LANE_x[42:41], (m0_o1t0_LANE_x[42:41] == 2'd0 && m0_o1t0_LANE_x[26:0] == 0) ? (((m0_xa[LANE][42:41] == 2'd0 && m0_xa[LANE][26:0] == 0) && (m0_xb[LANE][42:41] == 2'd0 && m0_xb[LANE][26:0] == 0)) ? ((rnd == 3'd2) ? (m0_aLANE[15] | (m0_bLANE[15] ^ 1'b1)) : (m0_aLANE[15] & (m0_bLANE[15] ^ 1'b1))) : ((rnd == 3'd2) ? 1'b1 : 1'b0)) : m0_o1t0_LANE_x[40], m0_o1t0_LANE_x[39:0] };
        x_m0[LANE*43 +: 43] = m0_o1t0_LANE_z;
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m0_fp_multiplier #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [1:0] op,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m0,
  output logic [9:0] fl_m0,
  input  logic [42:0] xa_m0,
  input  logic [42:0] xb_m0,
  input  logic [0:0] dena_m0,
  input  logic [0:0] denb_m0,
  output logic [42:0] x_m0
);
  // alu_core_m0_fp_multiplier: lane LANE of mode 0 (fp16) for the fp_multiplier ops fmul; the result buses are the mode's, with only this lane's bits written
  import alu_core_m0_pkg::*;
  logic d_m0;
  logic [15:0] m0_aLANE;
  logic [15:0] m0_bLANE;
  logic [27:0] m0_uaLANE;
  logic [27:0] m0_ubLANE;
  logic [42:0] m0_xa [0:0];
  logic m0_dena [0:0];
  logic [42:0] m0_xb [0:0];
  logic m0_denb [0:0];
  logic [42:0] m0_fm_xaLANE;
  logic [42:0] m0_fm_xbLANE;
  logic [42:0] m0_fm_yLANE;
  logic [25:0] m0_o2t0_LANE;
  logic [42:0] m0_o2t0_LANE_x;
  logic [42:0] m0_o2t0_LANE_z;
  assign m0_aLANE = a[(LANE*16) +: 16];
  assign m0_bLANE = b[(LANE*16) +: 16];
  // structure core.unpacker.m0: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp16_x26e13s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp16_x26e13s11_p9bfe39588414 u_m0_unpack_aLANE (.b(m0_aLANE), .daz(daz), .u(m0_uaLANE));
  // structure core.unpacker.m0: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp16_x26e13s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp16_x26e13s11_p9bfe39588414 u_m0_unpack_bLANE (.b(m0_bLANE), .daz(daz), .u(m0_ubLANE));
  assign m0_xa[LANE] = m0_x(m0_uaLANE[26:0]);
  assign m0_dena[LANE] = m0_uaLANE[27];
  assign m0_xb[LANE] = m0_x(m0_ubLANE[26:0]);
  assign m0_denb[LANE] = m0_ubLANE[27];
  // structure core.fp_multiplier.m0: family sig_mul_then_round realized by the library module fam_fp_mul_sig_mul_then_round_x26e13s11_pbd766efe148c
  fam_fp_mul_sig_mul_then_round_x26e13s11_pbd766efe148c u_m0_fmulLANE (.xa(m0_fm_xaLANE), .xb(m0_fm_xbLANE), .y(m0_fm_yLANE));
  always_comb begin
    y_m0 = '0; d_m0 = '0; fl_m0 = '0;
    m0_fm_xaLANE = 'x; m0_fm_xbLANE = 'x; m0_o2t0_LANE = 'x; m0_o2t0_LANE_x = 'x; m0_o2t0_LANE_z = 'x;
    x_m0 = '0;
    case (op)
      2'd2: begin
        m0_fm_xaLANE = m0_xa[LANE]; m0_fm_xbLANE = m0_xb[LANE]; m0_o2t0_LANE_x = m0_fm_yLANE;
        m0_o2t0_LANE_z = { m0_o2t0_LANE_x[42:41], (m0_o2t0_LANE_x[42:41] == 2'd0 && m0_o2t0_LANE_x[26:0] == 0) ? (m0_aLANE[15] ^ m0_bLANE[15]) : m0_o2t0_LANE_x[40], m0_o2t0_LANE_x[39:0] };
        x_m0[LANE*43 +: 43] = m0_o2t0_LANE_z;
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m0_rounder #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [1:0] op,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m0,
  output logic [9:0] fl_m0,
  input  logic [42:0] xa_m0,
  input  logic [42:0] xb_m0,
  input  logic [0:0] dena_m0,
  input  logic [0:0] denb_m0,
  input  logic [42:0] x_m0
);
  // alu_core_m0_rounder: lane LANE of mode 0 (fp16) for the rounder ops fadd, fsub, fmul; the result buses are the mode's, with only this lane's bits written
  import alu_core_m0_pkg::*;
  logic d_m0;
  logic [15:0] m0_aLANE;
  logic [15:0] m0_bLANE;
  logic [27:0] m0_uaLANE;
  logic [27:0] m0_ubLANE;
  logic [42:0] m0_xa [0:0];
  logic m0_dena [0:0];
  logic [42:0] m0_xb [0:0];
  logic m0_denb [0:0];
  logic [42:0] m0_rd_xLANE_fadd;
  logic [7:0] m0_rd_wLANE_fadd;
  logic [9:0] m0_rd_flLANE_fadd;
  logic [15:0] m0_rd_bLANE_fadd;
  logic [42:0] m0_rd_xLANE_fmul;
  logic [7:0] m0_rd_wLANE_fmul;
  logic [9:0] m0_rd_flLANE_fmul;
  logic [15:0] m0_rd_bLANE_fmul;
  logic [42:0] m0_rd_xLANE_fsub;
  logic [7:0] m0_rd_wLANE_fsub;
  logic [9:0] m0_rd_flLANE_fsub;
  logic [15:0] m0_rd_bLANE_fsub;
  logic [25:0] m0_o0t0_LANE;
  logic [42:0] m0_o0t0_LANE_x;
  logic [42:0] m0_o0t0_LANE_z;
  logic [25:0] m0_o1t0_LANE;
  logic [42:0] m0_o1t0_LANE_x;
  logic [42:0] m0_o1t0_LANE_z;
  logic [25:0] m0_o2t0_LANE;
  logic [42:0] m0_o2t0_LANE_x;
  logic [42:0] m0_o2t0_LANE_z;
  assign m0_aLANE = a[(LANE*16) +: 16];
  assign m0_bLANE = b[(LANE*16) +: 16];
  // structure core.unpacker.m0: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp16_x26e13s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp16_x26e13s11_p9bfe39588414 u_m0_unpack_aLANE (.b(m0_aLANE), .daz(daz), .u(m0_uaLANE));
  // structure core.unpacker.m0: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp16_x26e13s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp16_x26e13s11_p9bfe39588414 u_m0_unpack_bLANE (.b(m0_bLANE), .daz(daz), .u(m0_ubLANE));
  assign m0_xa[LANE] = m0_x(m0_uaLANE[26:0]);
  assign m0_dena[LANE] = m0_uaLANE[27];
  assign m0_xb[LANE] = m0_x(m0_ubLANE[26:0]);
  assign m0_denb[LANE] = m0_ubLANE[27];
  // structure core.rounder.m0: family dedicated_per_op realized by the library module fam_fp_round_dedicated_per_op_increment_adder_fp16_x26e13s11_pd77ccc5b5c45 (fadd)
  fam_fp_round_dedicated_per_op_increment_adder_fp16_x26e13s11_pd77ccc5b5c45 u_m0_roundLANE_fadd (.x(m0_rd_xLANE_fadd), .rnd(rnd), .word(m0_rd_wLANE_fadd), .ftz(ftz), .fl(m0_rd_flLANE_fadd), .bits(m0_rd_bLANE_fadd));
  // structure core.rounder.m0: family dedicated_per_op realized by the library module fam_fp_round_dedicated_per_op_increment_adder_fp16_x26e13s11_pd77ccc5b5c45 (fmul)
  fam_fp_round_dedicated_per_op_increment_adder_fp16_x26e13s11_pd77ccc5b5c45 u_m0_roundLANE_fmul (.x(m0_rd_xLANE_fmul), .rnd(rnd), .word(m0_rd_wLANE_fmul), .ftz(ftz), .fl(m0_rd_flLANE_fmul), .bits(m0_rd_bLANE_fmul));
  // structure core.rounder.m0: family dedicated_per_op realized by the library module fam_fp_round_dedicated_per_op_increment_adder_fp16_x26e13s11_pd77ccc5b5c45 (fsub)
  fam_fp_round_dedicated_per_op_increment_adder_fp16_x26e13s11_pd77ccc5b5c45 u_m0_roundLANE_fsub (.x(m0_rd_xLANE_fsub), .rnd(rnd), .word(m0_rd_wLANE_fsub), .ftz(ftz), .fl(m0_rd_flLANE_fsub), .bits(m0_rd_bLANE_fsub));
  always_comb begin
    y_m0 = '0; d_m0 = '0; fl_m0 = '0;
    m0_rd_xLANE_fadd = 'x; m0_rd_wLANE_fadd = 'x; m0_rd_xLANE_fmul = 'x; m0_rd_wLANE_fmul = 'x; m0_rd_xLANE_fsub = 'x; m0_rd_wLANE_fsub = 'x;
    m0_o0t0_LANE = 'x; m0_o0t0_LANE_x = 'x; m0_o0t0_LANE_z = 'x; m0_o1t0_LANE = 'x; m0_o1t0_LANE_x = 'x; m0_o1t0_LANE_z = 'x;
    m0_o2t0_LANE = 'x; m0_o2t0_LANE_x = 'x; m0_o2t0_LANE_z = 'x;
    case (op)
      2'd0: begin
        m0_o0t0_LANE_z = x_m0[LANE*43 +: 43];
        m0_rd_xLANE_fadd = m0_o0t0_LANE_z; m0_rd_wLANE_fadd = 8'd0; m0_o0t0_LANE = {m0_rd_flLANE_fadd, m0_rd_bLANE_fadd};
        y_m0[((LANE*16)+0) +: 16] = (m0_o0t0_LANE_z[42:41] == 2'd1) ? (((m0_xa[LANE][42:41] == 2'd1) || (m0_xb[LANE][42:41] == 2'd1)) ? 16'd32256 : 16'd32256) : ((m0_o0t0_LANE_z[42:41] == 2'd0 && m0_o0t0_LANE_z[26:0] == 0) ? {m0_o0t0_LANE_z[40], 15'd0} : m0_o0t0_LANE[15:0]);
        fl_m0[(0+LANE)*10 +: 10] = (((m0_xa[LANE][42:41] == 2'd1) || (m0_xb[LANE][42:41] == 2'd1)) ? (((10'd1 << 5) | (((m0_xa[LANE][42:41] == 2'd1) && !m0_aLANE[9]) || ((m0_xb[LANE][42:41] == 2'd1) && !m0_bLANE[9]) ? (10'd1 << 0) : 10'd0)) | (m0_dena[LANE] | m0_denb[LANE] ? (10'd1 << 6) : 10'd0)) : (m0_o0t0_LANE[25:16] | ((((m0_xa[LANE][42:41] == 2'd1) && !m0_aLANE[9]) || ((m0_xb[LANE][42:41] == 2'd1) && !m0_bLANE[9]) || ((m0_o0t0_LANE_z[42:41] == 2'd1) && !((m0_xa[LANE][42:41] == 2'd1) || (m0_xb[LANE][42:41] == 2'd1)))) ? (10'd1 << 0) : 10'd0) | (m0_dena[LANE] | m0_denb[LANE] ? (10'd1 << 6) : 10'd0)));
      end
      2'd1: begin
        m0_o1t0_LANE_z = x_m0[LANE*43 +: 43];
        m0_rd_xLANE_fsub = m0_o1t0_LANE_z; m0_rd_wLANE_fsub = 8'd0; m0_o1t0_LANE = {m0_rd_flLANE_fsub, m0_rd_bLANE_fsub};
        y_m0[((LANE*16)+0) +: 16] = (m0_o1t0_LANE_z[42:41] == 2'd1) ? (((m0_xa[LANE][42:41] == 2'd1) || (m0_xb[LANE][42:41] == 2'd1)) ? 16'd32256 : 16'd32256) : ((m0_o1t0_LANE_z[42:41] == 2'd0 && m0_o1t0_LANE_z[26:0] == 0) ? {m0_o1t0_LANE_z[40], 15'd0} : m0_o1t0_LANE[15:0]);
        fl_m0[(0+LANE)*10 +: 10] = (((m0_xa[LANE][42:41] == 2'd1) || (m0_xb[LANE][42:41] == 2'd1)) ? (((10'd1 << 5) | (((m0_xa[LANE][42:41] == 2'd1) && !m0_aLANE[9]) || ((m0_xb[LANE][42:41] == 2'd1) && !m0_bLANE[9]) ? (10'd1 << 0) : 10'd0)) | (m0_dena[LANE] | m0_denb[LANE] ? (10'd1 << 6) : 10'd0)) : (m0_o1t0_LANE[25:16] | ((((m0_xa[LANE][42:41] == 2'd1) && !m0_aLANE[9]) || ((m0_xb[LANE][42:41] == 2'd1) && !m0_bLANE[9]) || ((m0_o1t0_LANE_z[42:41] == 2'd1) && !((m0_xa[LANE][42:41] == 2'd1) || (m0_xb[LANE][42:41] == 2'd1)))) ? (10'd1 << 0) : 10'd0) | (m0_dena[LANE] | m0_denb[LANE] ? (10'd1 << 6) : 10'd0)));
      end
      2'd2: begin
        m0_o2t0_LANE_z = x_m0[LANE*43 +: 43];
        m0_rd_xLANE_fmul = m0_o2t0_LANE_z; m0_rd_wLANE_fmul = 8'd0; m0_o2t0_LANE = {m0_rd_flLANE_fmul, m0_rd_bLANE_fmul};
        y_m0[((LANE*16)+0) +: 16] = (m0_o2t0_LANE_z[42:41] == 2'd1) ? (((m0_xa[LANE][42:41] == 2'd1) || (m0_xb[LANE][42:41] == 2'd1)) ? 16'd32256 : 16'd32256) : ((m0_o2t0_LANE_z[42:41] == 2'd0 && m0_o2t0_LANE_z[26:0] == 0) ? {m0_o2t0_LANE_z[40], 15'd0} : m0_o2t0_LANE[15:0]);
        fl_m0[(0+LANE)*10 +: 10] = (((m0_xa[LANE][42:41] == 2'd1) || (m0_xb[LANE][42:41] == 2'd1)) ? (((10'd1 << 5) | (((m0_xa[LANE][42:41] == 2'd1) && !m0_aLANE[9]) || ((m0_xb[LANE][42:41] == 2'd1) && !m0_bLANE[9]) ? (10'd1 << 0) : 10'd0)) | (m0_dena[LANE] | m0_denb[LANE] ? (10'd1 << 6) : 10'd0)) : (m0_o2t0_LANE[25:16] | ((((m0_xa[LANE][42:41] == 2'd1) && !m0_aLANE[9]) || ((m0_xb[LANE][42:41] == 2'd1) && !m0_bLANE[9]) || ((m0_o2t0_LANE_z[42:41] == 2'd1) && !((m0_xa[LANE][42:41] == 2'd1) || (m0_xb[LANE][42:41] == 2'd1)))) ? (10'd1 << 0) : 10'd0) | (m0_dena[LANE] | m0_denb[LANE] ? (10'd1 << 6) : 10'd0)));
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m0_unpacker #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [1:0] op,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [42:0] xa_m0,
  output logic [42:0] xb_m0,
  output logic [0:0] dena_m0,
  output logic [0:0] denb_m0
);
  // alu_core_m0_unpacker: lane LANE of mode 0 (fp16) for the unpacker ops ; the result buses are the mode's, with only this lane's bits written
  import alu_core_m0_pkg::*;
  logic [15:0] y_m0;
  logic d_m0;
  logic [9:0] fl_m0;
  logic [15:0] m0_aLANE;
  logic [15:0] m0_bLANE;
  logic [27:0] m0_uaLANE;
  logic [27:0] m0_ubLANE;
  logic [42:0] m0_xa [0:0];
  logic m0_dena [0:0];
  logic [42:0] m0_xb [0:0];
  logic m0_denb [0:0];
  assign m0_aLANE = a[(LANE*16) +: 16];
  assign m0_bLANE = b[(LANE*16) +: 16];
  // structure core.unpacker.m0: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp16_x26e13s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp16_x26e13s11_p9bfe39588414 u_m0_unpack_aLANE (.b(m0_aLANE), .daz(daz), .u(m0_uaLANE));
  // structure core.unpacker.m0: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp16_x26e13s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp16_x26e13s11_p9bfe39588414 u_m0_unpack_bLANE (.b(m0_bLANE), .daz(daz), .u(m0_ubLANE));
  assign m0_xa[LANE] = m0_x(m0_uaLANE[26:0]);
  assign m0_dena[LANE] = m0_uaLANE[27];
  assign m0_xb[LANE] = m0_x(m0_ubLANE[26:0]);
  assign m0_denb[LANE] = m0_ubLANE[27];
  always_comb begin
    xa_m0 = '0; dena_m0 = '0; xb_m0 = '0; denb_m0 = '0;
    xa_m0[LANE*43 +: 43] = m0_xa[LANE];
    dena_m0[LANE] = m0_dena[LANE];
    xb_m0[LANE*43 +: 43] = m0_xb[LANE];
    denb_m0[LANE] = m0_denb[LANE];
  end
endmodule
// ADIR-MEMBER m0_l0_fp_adder
// EVOLVE-BLOCK-START
module alu_core_u_m0_l0_fp_adder (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [1:0] op,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m0,
  output logic [9:0] fl_m0,
  input  logic [42:0] xa_m0,
  input  logic [42:0] xb_m0,
  input  logic [0:0] dena_m0,
  input  logic [0:0] denb_m0,
  output logic [42:0] x_m0
);
  // alu_core_u_m0_l0_fp_adder: physical structure `m0.l0.fp_adder` (kind fp_adder, slot fp_adder); realizes m0.l0.fp_adder: fp_adder, mode 0 lane 0, fp16, ops fadd, fsub
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [15:0] y_m0_l0;
  logic [9:0] fl_m0_l0;
  logic [42:0] x_m0_l0;
  alu_core_m0_fp_adder #(.LANE(0)) u_m0_l0 (.a(a), .b(b), .op(op), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_l0), .fl_m0(fl_m0_l0), .xa_m0(xa_m0), .xb_m0(xb_m0), .dena_m0(dena_m0), .denb_m0(denb_m0), .x_m0(x_m0_l0));
  assign y_m0 = y_m0_l0;
  assign fl_m0 = fl_m0_l0;
  assign x_m0 = x_m0_l0;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m0_l0_unpacker
// EVOLVE-BLOCK-START
module alu_core_u_m0_l0_unpacker (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [1:0] op,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [42:0] xa_m0,
  output logic [42:0] xb_m0,
  output logic [0:0] dena_m0,
  output logic [0:0] denb_m0
);
  // alu_core_u_m0_l0_unpacker: physical structure `m0.l0.unpacker` (kind unpacker, slot unpacker); realizes m0.l0.unpacker: unpacker, mode 0 lane 0, fp16, ops fadd, fsub, fmul
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [42:0] xa_m0_l0;
  logic [42:0] xb_m0_l0;
  logic dena_m0_l0;
  logic denb_m0_l0;
  alu_core_m0_unpacker #(.LANE(0)) u_m0_l0 (.a(a), .b(b), .op(op), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .xa_m0(xa_m0_l0), .xb_m0(xb_m0_l0), .dena_m0(dena_m0_l0), .denb_m0(denb_m0_l0));
  assign xa_m0 = xa_m0_l0;
  assign xb_m0 = xb_m0_l0;
  assign dena_m0 = dena_m0_l0;
  assign denb_m0 = denb_m0_l0;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m0_l0_rounder
// EVOLVE-BLOCK-START
module alu_core_u_m0_l0_rounder (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [1:0] op,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m0,
  output logic [9:0] fl_m0,
  input  logic [42:0] xa_m0,
  input  logic [42:0] xb_m0,
  input  logic [0:0] dena_m0,
  input  logic [0:0] denb_m0,
  input  logic [42:0] x_m0
);
  // alu_core_u_m0_l0_rounder: physical structure `m0.l0.rounder` (kind rounder, slot rounder); realizes m0.l0.rounder: rounder, mode 0 lane 0, fp16, ops fadd, fsub, fmul
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [15:0] y_m0_l0;
  logic [9:0] fl_m0_l0;
  alu_core_m0_rounder #(.LANE(0)) u_m0_l0 (.a(a), .b(b), .op(op), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_l0), .fl_m0(fl_m0_l0), .xa_m0(xa_m0), .xb_m0(xb_m0), .dena_m0(dena_m0), .denb_m0(denb_m0), .x_m0(x_m0));
  assign y_m0 = y_m0_l0;
  assign fl_m0 = fl_m0_l0;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m0_l0_fp_fma
// m0.l0.fp_fma: realized inline in the top (member top)
// ADIR-MEMBER m0_l0_fp_multiplier
// EVOLVE-BLOCK-START
module alu_core_u_m0_l0_fp_multiplier (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [1:0] op,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m0,
  output logic [9:0] fl_m0,
  input  logic [42:0] xa_m0,
  input  logic [42:0] xb_m0,
  input  logic [0:0] dena_m0,
  input  logic [0:0] denb_m0,
  output logic [42:0] x_m0
);
  // alu_core_u_m0_l0_fp_multiplier: physical structure `m0.l0.fp_multiplier` (kind fp_multiplier, slot fp_multiplier); realizes m0.l0.fp_multiplier: fp_multiplier, mode 0 lane 0, fp16, ops fmul
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [15:0] y_m0_l0;
  logic [9:0] fl_m0_l0;
  logic [42:0] x_m0_l0;
  alu_core_m0_fp_multiplier #(.LANE(0)) u_m0_l0 (.a(a), .b(b), .op(op), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_l0), .fl_m0(fl_m0_l0), .xa_m0(xa_m0), .xb_m0(xb_m0), .dena_m0(dena_m0), .denb_m0(denb_m0), .x_m0(x_m0_l0));
  assign y_m0 = y_m0_l0;
  assign fl_m0 = fl_m0_l0;
  assign x_m0 = x_m0_l0;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER library
// ---- the family library modules the lane modules instantiate (chialu/targets/rtl/families; fixed text, replaced by editing the instances)
// The carry-propagate adder families of chiALU as parametric SystemVerilog.
// Every module has the one interface
//   #(parameter int W) (input [W-1:0] a, b, input cin, output [W-1:0] s, output cout)
// and computes s = a + b + cin exactly (cout the carry out of bit W-1), so the
// lane module of a seed can put any of them behind its add/sub/neg/abs/saturate
// ops. The family names are chialu/spaces/adder_spaces.py's; the parameters
// are the pins of a family's design choices the registry (families/__init__.py)
// maps. The blocked families (carry_skip, carry_select, carry_increment,
// sparse_prefix_hybrid), the end-around-carry, the truncated and the
// FPGA-chain families are generated by families/adder_ext.py around the
// library modules their slots name; the prefix families by families/prefix.py.

// ---------------------------------------------------------------- ripple_carry
// one full adder per bit, the carry rippling; CHUNK > 1 breaks the chain into
// chunks with an explicit carry wire between them (the chunk_width_bits choice).
// FORM is the full adder's logic: 0 generate_propagate (s = p ^ c, c' = g | p c),
// 1 two_half_adders_or (two half adders, the carries ORed), 2 xor_majority
// (s = a ^ b ^ c, c' = majority), 3 half_sum_mux_carry (c' = p ? c : a).
module fam_adder_ripple_carry #(parameter int W = 16, parameter int CHUNK = 1, parameter int FORM = 0)
  (input logic [W-1:0] a, input logic [W-1:0] b, input logic cin,
   output logic [W-1:0] s, output logic cout);
  localparam int BLOCKS = (W + CHUNK - 1) / CHUNK;
  logic [BLOCKS:0] block_carry;
  assign block_carry[0] = cin;
  for (genvar block_index = 0; block_index < BLOCKS; block_index = block_index + 1) begin : chunk
    localparam int LO = block_index * CHUNK;
    localparam int BW = LO + CHUNK > W ? W - LO : CHUNK;
    (* keep_hierarchy = "yes" *) fam_adder_ripple_chunk #(.W(BW), .FORM(FORM)) u_chunk(
      .a(a[LO +: BW]), .b(b[LO +: BW]), .cin(block_carry[block_index]),
      .s(s[LO +: BW]), .cout(block_carry[block_index+1]));
  end
  assign cout = block_carry[BLOCKS];
endmodule



module fam_adder_ripple_chunk #(parameter int W = 1, parameter int FORM = 0)
  (input logic [W-1:0] a, input logic [W-1:0] b, input logic cin,
   output logic [W-1:0] s, output logic cout);
  logic [W:0] c;
  assign c[0] = cin;
  genvar i;
  generate
    for (i = 0; i < W; i = i + 1) begin : fa
      if (FORM == 1) begin : two_ha
        wire s1 = a[i] ^ b[i];
        wire c1 = a[i] & b[i];
        wire c2 = s1 & c[i];
        assign s[i] = s1 ^ c[i];
        assign c[i+1] = c1 | c2;
      end else if (FORM == 2) begin : maj
        assign s[i] = a[i] ^ b[i] ^ c[i];
        assign c[i+1] = (a[i] & b[i]) | (a[i] & c[i]) | (b[i] & c[i]);
      end else if (FORM == 3) begin : muxc
        wire p = a[i] ^ b[i];
        assign s[i] = p ^ c[i];
        assign c[i+1] = p ? c[i] : a[i];
      end else begin : gp
        wire g = a[i] & b[i];
        wire p = a[i] ^ b[i];
        assign s[i] = p ^ c[i];
        assign c[i+1] = g | (p & c[i]);
      end
    end
  endgenerate
  assign cout = c[W];
endmodule


// lzd_cell_tree (pair_cell, binary_count, valid flags flat): the leading zeros of a 11-bit word
module fam_count_lzd_pair_cell_binary_count_vflat_w11 (input logic [10:0] a, output logic [3:0] n);
  logic v0_0; assign v0_0 = a[10] | a[9];
  logic p0_0; assign p0_0 = ~a[10];
  logic v0_1; assign v0_1 = a[8] | a[7];
  logic p0_1; assign p0_1 = ~a[8];
  logic v0_2; assign v0_2 = a[6] | a[5];
  logic p0_2; assign p0_2 = ~a[6];
  logic v0_3; assign v0_3 = a[4] | a[3];
  logic p0_3; assign p0_3 = ~a[4];
  logic v0_4; assign v0_4 = a[2] | a[1];
  logic p0_4; assign p0_4 = ~a[2];
  logic v0_5; assign v0_5 = a[0] | 1'b0;
  logic p0_5; assign p0_5 = ~a[0];
  logic v0_6; assign v0_6 = 1'b0 | 1'b0;
  logic p0_6; assign p0_6 = ~1'b0;
  logic v0_7; assign v0_7 = 1'b0 | 1'b0;
  logic p0_7; assign p0_7 = ~1'b0;
  logic v1_0; assign v1_0 = a[10] | a[9] | a[8] | a[7];
  logic [1:0] p1_0; assign p1_0 = v0_0 ? {1'b0, p0_0} : {1'b1, p0_1};
  logic v1_1; assign v1_1 = a[6] | a[5] | a[4] | a[3];
  logic [1:0] p1_1; assign p1_1 = v0_2 ? {1'b0, p0_2} : {1'b1, p0_3};
  logic v1_2; assign v1_2 = a[2] | a[1] | a[0] | 1'b0;
  logic [1:0] p1_2; assign p1_2 = v0_4 ? {1'b0, p0_4} : {1'b1, p0_5};
  logic v1_3; assign v1_3 = 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [1:0] p1_3; assign p1_3 = v0_6 ? {1'b0, p0_6} : {1'b1, p0_7};
  logic v2_0; assign v2_0 = a[10] | a[9] | a[8] | a[7] | a[6] | a[5] | a[4] | a[3];
  logic [2:0] p2_0; assign p2_0 = v1_0 ? {1'b0, p1_0} : {1'b1, p1_1};
  logic v2_1; assign v2_1 = a[2] | a[1] | a[0] | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [2:0] p2_1; assign p2_1 = v1_2 ? {1'b0, p1_2} : {1'b1, p1_3};
  logic v3_0; assign v3_0 = a[10] | a[9] | a[8] | a[7] | a[6] | a[5] | a[4] | a[3] | a[2] | a[1] | a[0] | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [3:0] p3_0; assign p3_0 = v2_0 ? {1'b0, p2_0} : {1'b1, p2_1};
  assign n = v3_0 ? p3_0 : 4'd11;
endmodule



// lzd_cell_tree (pair_cell, binary_count, valid flags flat): the leading zeros of a 26-bit word
module fam_count_lzd_pair_cell_binary_count_vflat_w26 (input logic [25:0] a, output logic [4:0] n);
  logic v0_0; assign v0_0 = a[25] | a[24];
  logic p0_0; assign p0_0 = ~a[25];
  logic v0_1; assign v0_1 = a[23] | a[22];
  logic p0_1; assign p0_1 = ~a[23];
  logic v0_2; assign v0_2 = a[21] | a[20];
  logic p0_2; assign p0_2 = ~a[21];
  logic v0_3; assign v0_3 = a[19] | a[18];
  logic p0_3; assign p0_3 = ~a[19];
  logic v0_4; assign v0_4 = a[17] | a[16];
  logic p0_4; assign p0_4 = ~a[17];
  logic v0_5; assign v0_5 = a[15] | a[14];
  logic p0_5; assign p0_5 = ~a[15];
  logic v0_6; assign v0_6 = a[13] | a[12];
  logic p0_6; assign p0_6 = ~a[13];
  logic v0_7; assign v0_7 = a[11] | a[10];
  logic p0_7; assign p0_7 = ~a[11];
  logic v0_8; assign v0_8 = a[9] | a[8];
  logic p0_8; assign p0_8 = ~a[9];
  logic v0_9; assign v0_9 = a[7] | a[6];
  logic p0_9; assign p0_9 = ~a[7];
  logic v0_10; assign v0_10 = a[5] | a[4];
  logic p0_10; assign p0_10 = ~a[5];
  logic v0_11; assign v0_11 = a[3] | a[2];
  logic p0_11; assign p0_11 = ~a[3];
  logic v0_12; assign v0_12 = a[1] | a[0];
  logic p0_12; assign p0_12 = ~a[1];
  logic v0_13; assign v0_13 = 1'b0 | 1'b0;
  logic p0_13; assign p0_13 = ~1'b0;
  logic v0_14; assign v0_14 = 1'b0 | 1'b0;
  logic p0_14; assign p0_14 = ~1'b0;
  logic v0_15; assign v0_15 = 1'b0 | 1'b0;
  logic p0_15; assign p0_15 = ~1'b0;
  logic v1_0; assign v1_0 = a[25] | a[24] | a[23] | a[22];
  logic [1:0] p1_0; assign p1_0 = v0_0 ? {1'b0, p0_0} : {1'b1, p0_1};
  logic v1_1; assign v1_1 = a[21] | a[20] | a[19] | a[18];
  logic [1:0] p1_1; assign p1_1 = v0_2 ? {1'b0, p0_2} : {1'b1, p0_3};
  logic v1_2; assign v1_2 = a[17] | a[16] | a[15] | a[14];
  logic [1:0] p1_2; assign p1_2 = v0_4 ? {1'b0, p0_4} : {1'b1, p0_5};
  logic v1_3; assign v1_3 = a[13] | a[12] | a[11] | a[10];
  logic [1:0] p1_3; assign p1_3 = v0_6 ? {1'b0, p0_6} : {1'b1, p0_7};
  logic v1_4; assign v1_4 = a[9] | a[8] | a[7] | a[6];
  logic [1:0] p1_4; assign p1_4 = v0_8 ? {1'b0, p0_8} : {1'b1, p0_9};
  logic v1_5; assign v1_5 = a[5] | a[4] | a[3] | a[2];
  logic [1:0] p1_5; assign p1_5 = v0_10 ? {1'b0, p0_10} : {1'b1, p0_11};
  logic v1_6; assign v1_6 = a[1] | a[0] | 1'b0 | 1'b0;
  logic [1:0] p1_6; assign p1_6 = v0_12 ? {1'b0, p0_12} : {1'b1, p0_13};
  logic v1_7; assign v1_7 = 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [1:0] p1_7; assign p1_7 = v0_14 ? {1'b0, p0_14} : {1'b1, p0_15};
  logic v2_0; assign v2_0 = a[25] | a[24] | a[23] | a[22] | a[21] | a[20] | a[19] | a[18];
  logic [2:0] p2_0; assign p2_0 = v1_0 ? {1'b0, p1_0} : {1'b1, p1_1};
  logic v2_1; assign v2_1 = a[17] | a[16] | a[15] | a[14] | a[13] | a[12] | a[11] | a[10];
  logic [2:0] p2_1; assign p2_1 = v1_2 ? {1'b0, p1_2} : {1'b1, p1_3};
  logic v2_2; assign v2_2 = a[9] | a[8] | a[7] | a[6] | a[5] | a[4] | a[3] | a[2];
  logic [2:0] p2_2; assign p2_2 = v1_4 ? {1'b0, p1_4} : {1'b1, p1_5};
  logic v2_3; assign v2_3 = a[1] | a[0] | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [2:0] p2_3; assign p2_3 = v1_6 ? {1'b0, p1_6} : {1'b1, p1_7};
  logic v3_0; assign v3_0 = a[25] | a[24] | a[23] | a[22] | a[21] | a[20] | a[19] | a[18] | a[17] | a[16] | a[15] | a[14] | a[13] | a[12] | a[11] | a[10];
  logic [3:0] p3_0; assign p3_0 = v2_0 ? {1'b0, p2_0} : {1'b1, p2_1};
  logic v3_1; assign v3_1 = a[9] | a[8] | a[7] | a[6] | a[5] | a[4] | a[3] | a[2] | a[1] | a[0] | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [3:0] p3_1; assign p3_1 = v2_2 ? {1'b0, p2_2} : {1'b1, p2_3};
  logic v4_0; assign v4_0 = a[25] | a[24] | a[23] | a[22] | a[21] | a[20] | a[19] | a[18] | a[17] | a[16] | a[15] | a[14] | a[13] | a[12] | a[11] | a[10] | a[9] | a[8] | a[7] | a[6] | a[5] | a[4] | a[3] | a[2] | a[1] | a[0] | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [4:0] p4_0; assign p4_0 = v3_0 ? {1'b0, p3_0} : {1'b1, p3_1};
  assign n = v4_0 ? p4_0 : 5'd26;
endmodule


// fp significand adder (single_path): 1 path; operands ordered by magnitude before one shifter; align full_align on a barrel_mux_tree shifter, sticky by or_tree_shifted_out; significand adder ripple_carry; leading zeros by lza (lzd_cell_tree, single_indicator); normalize coarse_fine on a barrel_mux_tree shifter; exponent path on ripple_carry adders; subnormals as stored; window of 15 guard bits below the larger operand's lsb (the significands are the unpacker's: 11 stored bits)
module fam_fp_add_single_path_x26e13s11_p9d459d224988 (
  input logic [42:0] xa,
  input logic [42:0] xb,
  input logic sub,
  output logic [42:0] y
);
  logic [1:0] a_sp; assign a_sp = xa[42:41];
  logic a_s; assign a_s = xa[40];
  logic signed [12:0] a_e; assign a_e = $signed(xa[39:27]);
  logic [25:0] a_sig; assign a_sig = xa[26:1];
  logic a_st; assign a_st = xa[0];
  logic a_z; assign a_z = (a_sp == 2'd0) && (a_sig == 0) && !a_st;
  logic [42:0] xbs; assign xbs = {xb[42:41], xb[40] ^ sub, xb[39:0]};
  logic [1:0] b_sp; assign b_sp = xbs[42:41];
  logic b_s; assign b_s = xbs[40];
  logic signed [12:0] b_e; assign b_e = $signed(xbs[39:27]);
  logic [25:0] b_sig; assign b_sig = xbs[26:1];
  logic b_st; assign b_st = xbs[0];
  logic b_z; assign b_z = (b_sp == 2'd0) && (b_sig == 0) && !b_st;
  logic signed [13:0] eax; assign eax = $signed({a_e[12], a_e});
  logic signed [13:0] ebx; assign ebx = $signed({b_e[12], b_e});
  logic [13:0] d_nb; assign d_nb = ~(ebx);
  logic signed [13:0] d;
  // the exponent difference
  fam_adder_ripple_carry #(.W(14), .CHUNK(1), .FORM(0)) u1 (.a(eax), .b(d_nb), .cin(1'b1), .s(d), .cout());
  logic signed [13:0] zero_x; assign zero_x = 14'sd0;
  logic [13:0] dn_nb; assign dn_nb = ~(d);
  logic signed [13:0] dn;
  // the difference negated
  fam_adder_ripple_carry #(.W(14), .CHUNK(1), .FORM(0)) u2 (.a(zero_x), .b(dn_nb), .cin(1'b1), .s(dn), .cout());
  logic a_big; assign a_big = (d > 0) || (d == 0 && a_sig >= b_sig);
  logic [13:0] dabs; assign dabs = a_big ? d : dn;
  logic signed [12:0] e_big; assign e_big = a_big ? a_e : b_e;
  logic s_big; assign s_big = a_big ? a_s : b_s;
  logic eff_sub; assign eff_sub = a_s ^ b_s;
  logic [25:0] big_sig; assign big_sig = a_big ? a_sig : b_sig;
  logic [25:0] sml_sig; assign sml_sig = a_big ? b_sig : a_sig;
  logic big_st; assign big_st = a_big ? a_st : b_st;
  logic sml_st; assign sml_st = a_big ? b_st : a_st;
  logic [26:0] mb; assign mb = {1'b0, big_sig[10:0], 15'd0};
  logic [26:0] ms0; assign ms0 = {1'b0, sml_sig[10:0], 15'd0};
  logic far_f; assign far_f = 1'b1 && (dabs > 26);
  logic [4:0] amt_f; assign amt_f = (!(1'b1) || far_f) ? 5'd0 : dabs[4:0];
  logic [26:0] mssh_f;
  logic stk0_f;
  // align: the operand shifted right by the exponent difference
  fam_shift_barrel_mux_tree #(.W(27), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u3 (.a(ms0), .amt(amt_f), .op(3'd1), .y(mssh_f), .sticky());
  assign stk0_f = |(ms0 & ((3'd1 == 3'd0) ? ~({27{1'b1}} >> amt_f) : ~({27{1'b1}} << amt_f)));
  logic [26:0] m_f; assign m_f = far_f ? 27'd0 : mssh_f;
  logic stk_f; assign stk_f = far_f ? (sml_sig != 0) : stk0_f;
  logic stb_f; assign stb_f = sml_st | stk_f;
  logic [26:0] ms_f; assign ms_f = m_f;
  logic [26:0] bop_f; assign bop_f = eff_sub ? ~ms_f : ms_f;
  logic cin_f; assign cin_f = eff_sub ? ~stb_f : 1'b0;
  logic co_f;
  logic [26:0] r_f;
  // add: the significand adder (ripple_carry)
  fam_adder_ripple_carry #(.W(27), .CHUNK(1), .FORM(0)) u4 (.a(mb), .b(bop_f), .cin(cin_f), .s(r_f), .cout(co_f));
  logic st_f; assign st_f = big_st | stb_f;
  logic ovf_f; assign ovf_f = r_f[26];
  logic [25:0] sig0_f; assign sig0_f = ovf_f ? r_f[26:1] : r_f[25:0];
  logic st0_f; assign st0_f = st_f | (ovf_f & r_f[0]);
  logic signed [12:0] e0n_f_c; assign e0n_f_c = -13'sd15;
  logic signed [12:0] e0n_f;
  // normalize: the window's exponent origin
  fam_adder_ripple_carry #(.W(13), .CHUNK(1), .FORM(0)) u5 (.a(e_big), .b(e0n_f_c), .cin(1'b0), .s(e0n_f), .cout());
  logic signed [12:0] e0o_f_c; assign e0o_f_c = -13'sd14;
  logic signed [12:0] e0o_f;
  // normalize: the window's exponent origin after a carry out
  fam_adder_ripple_carry #(.W(13), .CHUNK(1), .FORM(0)) u6 (.a(e_big), .b(e0o_f_c), .cin(1'b0), .s(e0o_f), .cout());
  logic signed [12:0] e0_f; assign e0_f = ovf_f ? e0o_f : e0n_f;
  logic [26:0] t_f0; assign t_f0 = mb ^ bop_f;
  logic [26:0] g_f0; assign g_f0 = mb & bop_f;
  logic [26:0] z_f0; assign z_f0 = ~mb & ~bop_f;
  logic [26:0] f_f0;
  assign f_f0[0] = (t_f0[1] & ((g_f0[0] & ~1'b0) | (z_f0[0] & ~1'b0))) | (~t_f0[1] & ((z_f0[0] & ~1'b0) | (g_f0[0] & ~1'b0)));
  assign f_f0[1] = (t_f0[2] & ((g_f0[1] & ~z_f0[0]) | (z_f0[1] & ~g_f0[0]))) | (~t_f0[2] & ((z_f0[1] & ~z_f0[0]) | (g_f0[1] & ~g_f0[0])));
  assign f_f0[2] = (t_f0[3] & ((g_f0[2] & ~z_f0[1]) | (z_f0[2] & ~g_f0[1]))) | (~t_f0[3] & ((z_f0[2] & ~z_f0[1]) | (g_f0[2] & ~g_f0[1])));
  assign f_f0[3] = (t_f0[4] & ((g_f0[3] & ~z_f0[2]) | (z_f0[3] & ~g_f0[2]))) | (~t_f0[4] & ((z_f0[3] & ~z_f0[2]) | (g_f0[3] & ~g_f0[2])));
  assign f_f0[4] = (t_f0[5] & ((g_f0[4] & ~z_f0[3]) | (z_f0[4] & ~g_f0[3]))) | (~t_f0[5] & ((z_f0[4] & ~z_f0[3]) | (g_f0[4] & ~g_f0[3])));
  assign f_f0[5] = (t_f0[6] & ((g_f0[5] & ~z_f0[4]) | (z_f0[5] & ~g_f0[4]))) | (~t_f0[6] & ((z_f0[5] & ~z_f0[4]) | (g_f0[5] & ~g_f0[4])));
  assign f_f0[6] = (t_f0[7] & ((g_f0[6] & ~z_f0[5]) | (z_f0[6] & ~g_f0[5]))) | (~t_f0[7] & ((z_f0[6] & ~z_f0[5]) | (g_f0[6] & ~g_f0[5])));
  assign f_f0[7] = (t_f0[8] & ((g_f0[7] & ~z_f0[6]) | (z_f0[7] & ~g_f0[6]))) | (~t_f0[8] & ((z_f0[7] & ~z_f0[6]) | (g_f0[7] & ~g_f0[6])));
  assign f_f0[8] = (t_f0[9] & ((g_f0[8] & ~z_f0[7]) | (z_f0[8] & ~g_f0[7]))) | (~t_f0[9] & ((z_f0[8] & ~z_f0[7]) | (g_f0[8] & ~g_f0[7])));
  assign f_f0[9] = (t_f0[10] & ((g_f0[9] & ~z_f0[8]) | (z_f0[9] & ~g_f0[8]))) | (~t_f0[10] & ((z_f0[9] & ~z_f0[8]) | (g_f0[9] & ~g_f0[8])));
  assign f_f0[10] = (t_f0[11] & ((g_f0[10] & ~z_f0[9]) | (z_f0[10] & ~g_f0[9]))) | (~t_f0[11] & ((z_f0[10] & ~z_f0[9]) | (g_f0[10] & ~g_f0[9])));
  assign f_f0[11] = (t_f0[12] & ((g_f0[11] & ~z_f0[10]) | (z_f0[11] & ~g_f0[10]))) | (~t_f0[12] & ((z_f0[11] & ~z_f0[10]) | (g_f0[11] & ~g_f0[10])));
  assign f_f0[12] = (t_f0[13] & ((g_f0[12] & ~z_f0[11]) | (z_f0[12] & ~g_f0[11]))) | (~t_f0[13] & ((z_f0[12] & ~z_f0[11]) | (g_f0[12] & ~g_f0[11])));
  assign f_f0[13] = (t_f0[14] & ((g_f0[13] & ~z_f0[12]) | (z_f0[13] & ~g_f0[12]))) | (~t_f0[14] & ((z_f0[13] & ~z_f0[12]) | (g_f0[13] & ~g_f0[12])));
  assign f_f0[14] = (t_f0[15] & ((g_f0[14] & ~z_f0[13]) | (z_f0[14] & ~g_f0[13]))) | (~t_f0[15] & ((z_f0[14] & ~z_f0[13]) | (g_f0[14] & ~g_f0[13])));
  assign f_f0[15] = (t_f0[16] & ((g_f0[15] & ~z_f0[14]) | (z_f0[15] & ~g_f0[14]))) | (~t_f0[16] & ((z_f0[15] & ~z_f0[14]) | (g_f0[15] & ~g_f0[14])));
  assign f_f0[16] = (t_f0[17] & ((g_f0[16] & ~z_f0[15]) | (z_f0[16] & ~g_f0[15]))) | (~t_f0[17] & ((z_f0[16] & ~z_f0[15]) | (g_f0[16] & ~g_f0[15])));
  assign f_f0[17] = (t_f0[18] & ((g_f0[17] & ~z_f0[16]) | (z_f0[17] & ~g_f0[16]))) | (~t_f0[18] & ((z_f0[17] & ~z_f0[16]) | (g_f0[17] & ~g_f0[16])));
  assign f_f0[18] = (t_f0[19] & ((g_f0[18] & ~z_f0[17]) | (z_f0[18] & ~g_f0[17]))) | (~t_f0[19] & ((z_f0[18] & ~z_f0[17]) | (g_f0[18] & ~g_f0[17])));
  assign f_f0[19] = (t_f0[20] & ((g_f0[19] & ~z_f0[18]) | (z_f0[19] & ~g_f0[18]))) | (~t_f0[20] & ((z_f0[19] & ~z_f0[18]) | (g_f0[19] & ~g_f0[18])));
  assign f_f0[20] = (t_f0[21] & ((g_f0[20] & ~z_f0[19]) | (z_f0[20] & ~g_f0[19]))) | (~t_f0[21] & ((z_f0[20] & ~z_f0[19]) | (g_f0[20] & ~g_f0[19])));
  assign f_f0[21] = (t_f0[22] & ((g_f0[21] & ~z_f0[20]) | (z_f0[21] & ~g_f0[20]))) | (~t_f0[22] & ((z_f0[21] & ~z_f0[20]) | (g_f0[21] & ~g_f0[20])));
  assign f_f0[22] = (t_f0[23] & ((g_f0[22] & ~z_f0[21]) | (z_f0[22] & ~g_f0[21]))) | (~t_f0[23] & ((z_f0[22] & ~z_f0[21]) | (g_f0[22] & ~g_f0[21])));
  assign f_f0[23] = (t_f0[24] & ((g_f0[23] & ~z_f0[22]) | (z_f0[23] & ~g_f0[22]))) | (~t_f0[24] & ((z_f0[23] & ~z_f0[22]) | (g_f0[23] & ~g_f0[22])));
  assign f_f0[24] = (t_f0[25] & ((g_f0[24] & ~z_f0[23]) | (z_f0[24] & ~g_f0[23]))) | (~t_f0[25] & ((z_f0[24] & ~z_f0[23]) | (g_f0[24] & ~g_f0[23])));
  assign f_f0[25] = (t_f0[26] & ((g_f0[25] & ~z_f0[24]) | (z_f0[25] & ~g_f0[24]))) | (~t_f0[26] & ((z_f0[25] & ~z_f0[24]) | (g_f0[25] & ~g_f0[24])));
  assign f_f0[26] = (1'b0 & ((g_f0[26] & ~z_f0[25]) | (z_f0[26] & ~g_f0[25]))) | (~1'b0 & ((z_f0[26] & ~z_f0[25]) | (g_f0[26] & ~g_f0[25])));
  logic [25:0] fw_f0; assign fw_f0 = ovf_f ? f_f0[26:1] : f_f0[25:0];
  logic [25:0] fws_f; assign fws_f = fw_f0;
  logic [4:0] lzp_f;
  // normalize: leading zeros of the indicator string
  fam_count_lzd_pair_cell_binary_count_vflat_w26 u7 (.a(fws_f), .n(lzp_f));
  logic [4:0] lzs_f; assign lzs_f = (!eff_sub || fws_f == 0) ? 5'd0 : lzp_f[4:0];
  logic fz_f; assign fz_f = fws_f == 0;
  logic [4:0] cshift_f; assign cshift_f = {lzs_f[4:2], 2'd0};
  logic [4:0] fshift_f; assign fshift_f = {{(5-2){1'b0}}, lzs_f[1:0]};
  logic [25:0] sigc_f;
  // normalize: the coarse normalize stage (multiples of 4)
  fam_shift_barrel_mux_tree #(.W(26), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u8 (.a(sig0_f), .amt(cshift_f), .op(3'd0), .y(sigc_f), .sticky());
  logic [25:0] sign_f;
  // normalize: the fine normalize stage
  fam_shift_barrel_mux_tree #(.W(26), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u9 (.a(sigc_f), .amt(fshift_f), .op(3'd0), .y(sign_f), .sticky());
  logic signed [12:0] lzx_f; assign lzx_f = $signed({{(13-5){1'b0}}, lzs_f});
  logic [12:0] en_f_nb; assign en_f_nb = ~(lzx_f);
  logic signed [12:0] en_f;
  // normalize: the exponent lowered by the normalize count
  fam_adder_ripple_carry #(.W(13), .CHUNK(1), .FORM(0)) u10 (.a(e0_f), .b(en_f_nb), .cin(1'b1), .s(en_f), .cout());
  logic fix_f; assign fix_f = ~sign_f[25] && (sign_f != 0);
  logic [25:0] sigf_f; assign sigf_f = fix_f ? {sign_f[24:0], 1'b0} : sign_f;
  logic signed [12:0] enm_f_c; assign enm_f_c = -13'sd1;
  logic signed [12:0] enm_f;
  // normalize: the exponent of the corrected position
  fam_adder_ripple_carry #(.W(13), .CHUNK(1), .FORM(0)) u11 (.a(en_f), .b(enm_f_c), .cin(1'b0), .s(enm_f), .cout());
  logic signed [12:0] ef_f; assign ef_f = fix_f ? enm_f : en_f;
  logic zero_f; assign zero_f = (sigf_f == 0) && !st0_f;
  logic sr_f; assign sr_f = zero_f ? 1'b0 : s_big;
  logic [42:0] y_f; assign y_f = {2'd0, sr_f, ef_f, sigf_f, st0_f};
  logic both_inf; assign both_inf = (a_sp == 2'd2) && (b_sp == 2'd2);
  logic [42:0] y_sp; assign y_sp = (a_sp == 2'd1 || b_sp == 2'd1) ? {2'd1, 1'b0, 13'sd0, 26'd0, 1'b0} : both_inf ? ((a_s == b_s) ? {2'd2, a_s, 13'sd0, 26'd0, 1'b0} : {2'd1, 1'b0, 13'sd0, 26'd0, 1'b0}) : (a_sp == 2'd2) ? {2'd2, a_s, 13'sd0, 26'd0, 1'b0} : (b_sp == 2'd2) ? {2'd2, b_s, 13'sd0, 26'd0, 1'b0} : a_z ? xbs : b_z ? xa : y_f;
  assign y = y_sp;
endmodule

// fp significand multiplier (sig_mul_then_round): behavioral_star over the 11-bit significands, the exact product in the X field, the exponent sum on a ripple_carry adder
module fam_fp_mul_sig_mul_then_round_x26e13s11_pbd766efe148c (
  input logic [42:0] xa,
  input logic [42:0] xb,
  output logic [42:0] y
);
  logic [1:0] a_sp; assign a_sp = xa[42:41];
  logic a_s; assign a_s = xa[40];
  logic signed [12:0] a_e; assign a_e = $signed(xa[39:27]);
  logic [25:0] a_sig; assign a_sig = xa[26:1];
  logic a_st; assign a_st = xa[0];
  logic a_z; assign a_z = (a_sp == 2'd0) && (a_sig == 0) && !a_st;
  logic [1:0] b_sp; assign b_sp = xb[42:41];
  logic b_s; assign b_s = xb[40];
  logic signed [12:0] b_e; assign b_e = $signed(xb[39:27]);
  logic [25:0] b_sig; assign b_sig = xb[26:1];
  logic b_st; assign b_st = xb[0];
  logic b_z; assign b_z = (b_sp == 2'd0) && (b_sig == 0) && !b_st;
  logic s; assign s = a_s ^ b_s;
  logic [10:0] sa; assign sa = a_sig[10:0];
  logic [10:0] sb; assign sb = b_sig[10:0];
  logic [21:0] p;
  // the significand product (behavioral_star)
  fam_mul_behavioral_star_w11_u_pfc463c41 u1 (.a(sa), .b(sb), .p(p));
  logic signed [12:0] e;
  // the exponent sum
  fam_adder_ripple_carry #(.W(13), .CHUNK(1), .FORM(0)) u2 (.a(a_e), .b(b_e), .cin(1'b0), .s(e), .cout());
  logic st; assign st = a_st | b_st;
  logic [42:0] y_fin; assign y_fin = {2'd0, s, e, {{(26-22){1'b0}}, p}, st};
  logic [42:0] y_sp; assign y_sp = (a_sp == 2'd1 || b_sp == 2'd1) ? {2'd1, 1'b0, 13'sd0, 26'd0, 1'b0} : (a_sp == 2'd2 || b_sp == 2'd2) ? (((a_sp == 2'd0 && a_z) || (b_sp == 2'd0 && b_z)) ? {2'd1, 1'b0, 13'sd0, 26'd0, 1'b0} : {2'd2, s, 13'sd0, 26'd0, 1'b0}) : y_fin;
  assign y = y_sp;
endmodule

// fp rounder (dedicated_per_op, rounding increment_adder, leading zeros lzd_cell_tree, shifts barrel_mux_tree, exponent ripple_carry / prefix_and_incrementer): X -> fp16 pattern and flags
module fam_fp_round_dedicated_per_op_increment_adder_fp16_x26e13s11_pd77ccc5b5c45 (
  input logic [42:0] x,
  input logic [2:0] rnd,
  input logic [7:0] word,
  input logic ftz,
  output logic [9:0] fl,
  output logic [15:0] bits
);
  logic [1:0] x_sp; assign x_sp = x[42:41];
  logic x_s; assign x_s = x[40];
  logic signed [12:0] x_e; assign x_e = $signed(x[39:27]);
  logic [25:0] x_sig; assign x_sig = x[26:1];
  logic x_st; assign x_st = x[0];
  logic x_z; assign x_z = (x_sp == 2'd0) && (x_sig == 0) && !x_st;
  logic s; assign s = x_s & 1'd1;
  logic lone; assign lone = (x_sig == 0) && x_st;
  logic [25:0] sig_in; assign sig_in = lone ? 26'd1 : x_sig;
  logic signed [12:0] e_lone_c; assign e_lone_c = -13'sd26;
  logic signed [12:0] e_lone;
  // the exponent of a lone sticky's unit
  fam_adder_ripple_carry #(.W(13), .CHUNK(1), .FORM(0)) u1 (.a(x_e), .b(e_lone_c), .cin(1'b0), .s(e_lone), .cout());
  logic signed [12:0] e_in; assign e_in = lone ? e_lone : x_e;
  logic [4:0] lz;
  // the normalizer's leading-zero count
  fam_count_lzd_pair_cell_binary_count_vflat_w26 u2 (.a(sig_in), .n(lz));
  logic [4:0] lzs; assign lzs = (sig_in == 0) ? 5'd0 : lz[4:0];
  logic [25:0] sig;
  // the normalizer's left shift
  fam_shift_barrel_mux_tree #(.W(26), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u3 (.a(sig_in), .amt(lzs), .op(3'd0), .y(sig), .sticky());
  logic signed [12:0] lzx; assign lzx = $signed({{(13-5){1'b0}}, lzs});
  logic [12:0] e_nb; assign e_nb = ~(lzx);
  logic signed [12:0] e;
  // the exponent lowered by the normalize count
  fam_adder_ripple_carry #(.W(13), .CHUNK(1), .FORM(0)) u4 (.a(e_in), .b(e_nb), .cin(1'b1), .s(e), .cout());
  logic normal; assign normal = e >= -13'sd39;
  logic signed [13:0] shc; assign shc = -14'sd24;
  logic signed [13:0] ex; assign ex = $signed({e[12], e});
  logic [13:0] shsub_nb; assign shsub_nb = ~(ex);
  logic signed [13:0] shsub;
  // the subnormal result's extra right shift
  fam_adder_ripple_carry #(.W(14), .CHUNK(1), .FORM(0)) u5 (.a(shc), .b(shsub_nb), .cin(1'b1), .s(shsub), .cout());
  logic signed [13:0] sht; assign sht = normal ? 14'sd15 : shsub;
  logic signed [13:0] sh; assign sh = (sht > 14'sd27) ? 14'sd27 : sht;
  logic [4:0] sha; assign sha = sh[4:0];
  logic [26:0] sigw; assign sigw = {1'b0, sig};
  logic [4:0] shk; assign shk = (sh > 14'sd26) ? 5'd26 : sha;
  logic [26:0] keep;
  // the right shift to the kept bits
  fam_shift_barrel_mux_tree #(.W(27), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u6 (.a(sigw), .amt(shk), .op(3'd1), .y(keep), .sticky());
  // the mask of the dropped positions
  logic [26:0] restmask;
  assign restmask[0] = (sha > 0);
  assign restmask[1] = (sha > 1);
  assign restmask[2] = (sha > 2);
  assign restmask[3] = (sha > 3);
  assign restmask[4] = (sha > 4);
  assign restmask[5] = (sha > 5);
  assign restmask[6] = (sha > 6);
  assign restmask[7] = (sha > 7);
  assign restmask[8] = (sha > 8);
  assign restmask[9] = (sha > 9);
  assign restmask[10] = (sha > 10);
  assign restmask[11] = (sha > 11);
  assign restmask[12] = (sha > 12);
  assign restmask[13] = (sha > 13);
  assign restmask[14] = (sha > 14);
  assign restmask[15] = (sha > 15);
  assign restmask[16] = (sha > 16);
  assign restmask[17] = (sha > 17);
  assign restmask[18] = (sha > 18);
  assign restmask[19] = (sha > 19);
  assign restmask[20] = (sha > 20);
  assign restmask[21] = (sha > 21);
  assign restmask[22] = (sha > 22);
  assign restmask[23] = (sha > 23);
  assign restmask[24] = (sha > 24);
  assign restmask[25] = (sha > 25);
  assign restmask[26] = (sha > 26);
  logic [26:0] rest; assign rest = sigw & restmask;
  // the half position (one below the kept lsb)
  logic [26:0] halfv;
  assign halfv[0] = (sha == 1);
  assign halfv[1] = (sha == 2);
  assign halfv[2] = (sha == 3);
  assign halfv[3] = (sha == 4);
  assign halfv[4] = (sha == 5);
  assign halfv[5] = (sha == 6);
  assign halfv[6] = (sha == 7);
  assign halfv[7] = (sha == 8);
  assign halfv[8] = (sha == 9);
  assign halfv[9] = (sha == 10);
  assign halfv[10] = (sha == 11);
  assign halfv[11] = (sha == 12);
  assign halfv[12] = (sha == 13);
  assign halfv[13] = (sha == 14);
  assign halfv[14] = (sha == 15);
  assign halfv[15] = (sha == 16);
  assign halfv[16] = (sha == 17);
  assign halfv[17] = (sha == 18);
  assign halfv[18] = (sha == 19);
  assign halfv[19] = (sha == 20);
  assign halfv[20] = (sha == 21);
  assign halfv[21] = (sha == 22);
  assign halfv[22] = (sha == 23);
  assign halfv[23] = (sha == 24);
  assign halfv[24] = (sha == 25);
  assign halfv[25] = (sha == 26);
  assign halfv[26] = (sha == 27);
  logic [26:0] keepn; assign keepn = sigw >> 15;
  logic [26:0] restn; assign restn = sigw & ({1'b0, {26{1'b1}}} >> 11);
  logic [26:0] halfn; assign halfn = {26'd0, 1'b1} << 14;
  logic inexact; assign inexact = (rest != 0) | x_st;
  logic [34:0] restw; assign restw = {rest, 8'd0};
  logic [5:0] fsh; assign fsh = sht[5:0];
  logic [34:0] fint0;
  // the dropped bits aligned to the stochastic word
  fam_shift_barrel_mux_tree #(.W(35), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u7 (.a(restw), .amt(fsh), .op(3'd1), .y(fint0), .sticky());
  logic [34:0] fint; assign fint = (sht > 14'sd34) ? 35'd0 : fint0;
  logic [34:0] fintn; assign fintn = restn >> 7;
  logic gt_half; assign gt_half = rest > halfv;
  logic half_eq; assign half_eq = (rest == halfv) && (halfv != 0);
  logic up; assign up = (rnd == 3'd0) ? (gt_half || (half_eq && (x_st || keep[0]))) : (rnd == 3'd1) ? 1'b0 : (rnd == 3'd2) ? (inexact && s) : (rnd == 3'd3) ? (inexact && !s) : (rnd == 3'd4) ? (inexact && (0 ? (fint >= word) : (fint > word))) : inexact;
  logic gt_halfn; assign gt_halfn = restn > halfn;
  logic half_eqn; assign half_eqn = (restn == halfn) && (halfn != 0);
  logic upn; assign upn = (rnd == 3'd0) ? (gt_halfn || (half_eqn && (x_st || keepn[0]))) : (rnd == 3'd1) ? 1'b0 : (rnd == 3'd2) ? (((restn != 0) | x_st) && s) : (rnd == 3'd3) ? (((restn != 0) | x_st) && !s) : (rnd == 3'd4) ? (((restn != 0) | x_st) && (0 ? (fintn >= word) : (fintn > word))) : ((restn != 0) | x_st);
  logic rounded; assign rounded = x_sp == 2'd3;
  logic upr; assign upr = rounded ? 1'b0 : up;
  logic inexact_r; assign inexact_r = rounded | inexact;
  logic carry_n; assign carry_n = upn && (&keepn[10:0]);
  logic [26:0] mag;
  logic [26:0] mag0;
  // the rounding increment (prefix_and_incrementer)
  fam_incr_prefix_and #(.W(27), .STRUCTURE(0), .B(4), .TOPO(0)) u8 (.a(keep), .cin(upr), .s(mag0), .cout());
  assign mag = mag0;
  logic signed [12:0] bfield_c; assign bfield_c = 13'sd40;
  logic signed [12:0] bfield;
  // the biased exponent field
  fam_adder_ripple_carry #(.W(13), .CHUNK(1), .FORM(0)) u9 (.a(e), .b(bfield_c), .cin(1'b0), .s(bfield), .cout());
  logic [12:0] bfu; assign bfu = bfield;
  logic [12:0] efield;
  // the exponent field incremented on a rounding carry (prefix_and_incrementer)
  fam_incr_prefix_and #(.W(13), .STRUCTURE(0), .B(4), .TOPO(0)) u10 (.a(bfu), .cin(mag[11]), .s(efield), .cout());
  logic [29:0] code; assign code = normal ? {{(30-13-10){1'b0}}, efield, mag[9:0]} : {{(30-27){1'b0}}, mag};
  logic tiny; assign tiny = (e < -13'sd39) && !(e == -13'sd40 && carry_n) && !(e == -13'sd40 && carry_n);
  logic ovf; assign ovf = code > 30'd31743;
  logic to_inf; assign to_inf = 1 && (rnd == 3'd0 || (rnd == 3'd3 && !s) || (rnd == 3'd2 && s) || rnd == 3'd5 || (rnd == 3'd4 && (e > -13'sd10 || up)));
  logic ftz_hit; assign ftz_hit = ftz && code[14:10] == 0 && (code[9:0] != 0);
  logic is_zero; assign is_zero = (x_sig == 0) && (!x_st || rounded);
  logic tiny_r; assign tiny_r = rounded ? x_st : tiny;
  logic [9:0] fl_fin; assign fl_fin = ovf ? ((1 << 2) | (1 << 4)) : ((inexact_r ? (1 << 4) : 0) | ((tiny_r && inexact_r) ? (1 << 3) : 0) | (ftz_hit ? ((1 << 4) | (1 << 3)) : 0));
  logic [15:0] bits_fin; assign bits_fin = ovf ? (to_inf ? {s, 15'd31744} : {s, 15'd31743}) : (ftz_hit ? {s, 15'd0} : {s, code[14:0]});
  logic [9:0] fl_zero; assign fl_zero = rounded ? ((1 << 4) | (1 << 3)) : 10'd0;
  assign fl = (x_sp == 2'd1) ? (1 << 5) : (x_sp == 2'd2) ? 0 : is_zero ? fl_zero : fl_fin;
  assign bits = (x_sp == 2'd1) ? 16'd32256 : (x_sp == 2'd2) ? {s, 15'd31744} : is_zero ? (rounded ? {s, 15'd0} : 16'd0) : bits_fin;
endmodule

// fp unpacker (per_unit_unpack): fp16 pattern -> V; the fields split, the specials decoded, the hidden one restored, a subnormal normalized in the unpacker
module fam_fp_unpack_per_unit_unpack_fp16_x26e13s11_p9bfe39588414 (
  input logic [15:0] b,
  input logic daz,
  output logic [27:0] u
);
  logic [4:0] e; assign e = b[14:10];
  logic [9:0] mant; assign mant = b[9:0];
  logic s; assign s = b[15];
  logic nan; assign nan = (e == 5'd31 && mant != 0);
  logic inf; assign inf = (e == 5'd31 && mant == 0);
  logic sub_; assign sub_ = (e == 0);
  logic den; assign den = sub_ && (mant != 0);
  logic [10:0] sig0; assign sig0 = sub_ ? {{(11-10){1'b0}}, mant} : {{(11-10-1){1'b0}}, 1'b1, mant};
  logic [10:0] sig1; assign sig1 = (sub_ && daz) ? 11'd0 : sig0;
  logic signed [12:0] ex0; assign ex0 = sub_ ? -13'sd24 : $signed({{(13-5){1'b0}}, e}) - 13'sd25;
  logic [3:0] lz;
  // the subnormal's leading-zero count
  fam_count_lzd_pair_cell_binary_count_vflat_w11 u1 (.a(sig1), .n(lz));
  logic [3:0] lzs; assign lzs = (sig1 == 0) ? 4'd0 : lz[3:0];
  logic [10:0] sign;
  // the subnormal normalized
  fam_shift_barrel_mux_tree #(.W(11), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u2 (.a(sig1), .amt(lzs), .op(3'd0), .y(sign), .sticky());
  logic signed [12:0] exn; assign exn = ex0 - $signed({{(13-4){1'b0}}, lz});
  logic [26:0] v_nan; assign v_nan = {2'd1, 1'b0, 13'sd0, 11'd0};
  logic [26:0] v_inf; assign v_inf = {2'd2, s, 13'sd0, 11'd0};
  logic [26:0] v_fin; assign v_fin = {2'd0, s, exn, sign};
  assign u = nan ? {1'b0, v_nan} : inf ? {1'b0, v_inf} : {den, v_fin};
endmodule



// ------------------------------------------------------------ prefix_and_incrementer
// s = a + cin: the carry into bit i is cin AND every lower bit, a prefix AND
// (STRUCTURE 0 a ripple AND chain, 1 a prefix AND tree of topology TOPO, 2
// select blocks of B bits whose block carry is the AND of the block)
module fam_incr_prefix_and #(parameter int W = 16, parameter int STRUCTURE = 1, parameter int B = 4, parameter int TOPO = 0)
  (input logic [W-1:0] a, input logic cin, output logic [W-1:0] s, output logic cout);
  // STRUCTURE: 0 ripple_and_chain, 1 prefix_and_tree (TOPO: 0 sklansky, 1 brent_kung, 2 kogge_stone),
  // 2 select_blocks of B bits
  logic [W:0] c;
  assign c[0] = cin;
  genvar i, l;
  generate
    if (STRUCTURE == 0) begin : ripple
      for (i = 0; i < W; i = i + 1) begin : ch
        assign c[i+1] = c[i] & a[i];
      end
    end else if (STRUCTURE == 1) begin : tree
      localparam int L = (W <= 1) ? 1 : $clog2(W);
      if (TOPO == 2) begin : kogge_stone
        // p[l][i]: AND of a[i] down to a[i - 2^l + 1]
        logic [W-1:0] p [0:L];
        for (i = 0; i < W; i = i + 1) begin : leaf
          assign p[0][i] = a[i];
        end
        for (l = 0; l < L; l = l + 1) begin : lvl
          for (i = 0; i < W; i = i + 1) begin : pos
            if (i >= (1 << l)) begin : comb
              assign p[l+1][i] = p[l][i] & p[l][i - (1 << l)];
            end else begin : keep
              assign p[l+1][i] = p[l][i];
            end
          end
        end
        for (i = 0; i < W; i = i + 1) begin : cy
          assign c[i+1] = cin & p[L][i];
        end
      end else if (TOPO == 1) begin : brent_kung
        // an up-sweep over the odd positions of each level, then a down-sweep filling the rest
        logic [W-1:0] p [0:2*L];
        for (i = 0; i < W; i = i + 1) begin : leaf
          assign p[0][i] = a[i];
        end
        for (l = 0; l < L; l = l + 1) begin : up
          for (i = 0; i < W; i = i + 1) begin : pos
            if (((i + 1) % (2 << l)) == 0) begin : comb
              assign p[l+1][i] = p[l][i] & p[l][i - (1 << l)];
            end else begin : keep
              assign p[l+1][i] = p[l][i];
            end
          end
        end
        for (l = 0; l < L; l = l + 1) begin : down
          localparam int D = 1 << (L - 1 - l);
          for (i = 0; i < W; i = i + 1) begin : pos
            if (((i + 1) % (2 * D)) == D && (i + 1) > D) begin : comb
              assign p[L+l+1][i] = p[L+l][i] & p[L+l][i - D];
            end else begin : keep
              assign p[L+l+1][i] = p[L+l][i];
            end
          end
        end
        for (i = 0; i < W; i = i + 1) begin : cy
          assign c[i+1] = cin & p[2*L][i];
        end
      end else begin : sklansky
        logic [W-1:0] p [0:L];           // p[l][i]: AND of a[i] down to a[i - 2^l + 1]
        for (i = 0; i < W; i = i + 1) begin : leaf
          assign p[0][i] = a[i];
        end
        for (l = 0; l < L; l = l + 1) begin : lvl
          for (i = 0; i < W; i = i + 1) begin : pos
            if ((i / (1 << l)) % 2 == 1) begin : comb   // the upper half of every block takes the lower half's end
              assign p[l+1][i] = p[l][i] & p[l][(i / (1 << l)) * (1 << l) - 1];
            end else begin : keep
              assign p[l+1][i] = p[l][i];
            end
          end
        end
        for (i = 0; i < W; i = i + 1) begin : cy
          assign c[i+1] = cin & p[L][i];
        end
      end
    end else begin : blocks
      localparam int NB = (W + B - 1) / B;
      logic [NB:0] bc;                  // the carry into each block
      assign bc[0] = cin;
      for (i = 0; i < NB; i = i + 1) begin : blk
        localparam int LO = i * B;
        localparam int HI = (LO + B - 1 < W - 1) ? LO + B - 1 : W - 1;
        logic all1;
        assign all1 = &a[HI:LO];
        assign bc[i+1] = bc[i] & all1;
        genvar j;
        for (j = LO; j <= HI; j = j + 1) begin : bit_
          if (j == LO) begin : first
            assign c[j+1] = bc[i] & a[j];
          end else begin : rest
            assign c[j+1] = c[j] & a[j];
          end
        end
      end
    end
  endgenerate
  assign s = a ^ c[W-1:0];
  assign cout = c[W];
endmodule



// behavioral_star: p = a * b, the structure left to synthesis
module fam_mul_behavioral_star_w11_u_pfc463c41 (input logic [10:0] a, input logic [10:0] b, output logic [21:0] p);
  assign p = a * b;
endmodule




// -------------------------------------------------------------- barrel_mux_tree
// ceil(AW / K) stages of 2^K:1 muxes (RADIX_LOG2 = K; 0 selects one full-width
// stage of W:1 muxes). DIR: 0 mirrored_datapath (a left and a right datapath,
// the result selected by the direction), 1 data_reversal (a right operation is
// a left one on the reversed word), 2 amount_negation (one left rotator; a right
// operation rotates by W - amt, a shift merges the fill through the keep mask).
// ORDER: 0 small_shift_first, 1 large_shift_first. ONE_HOT: the stages' select
// encoding.
module fam_shift_barrel_mux_tree #(parameter int W = 16, parameter int RADIX_LOG2 = 1, parameter int ONE_HOT = 0,
                                   parameter int DIR = 1, parameter int ORDER = 0, parameter int STICKY = 0)
  (input logic [W-1:0] a, input logic [$clog2(W)-1:0] amt, input logic [2:0] op, output logic [W-1:0] y, output logic sticky);
  localparam int AW = $clog2(W);
  localparam int K = (RADIX_LOG2 == 0 || RADIX_LOG2 > AW) ? AW : RADIX_LOG2;
  localparam int NS = (AW + K - 1) / K;
  wire right = (op == 3'd1) || (op == 3'd2) || (op == 3'd4);
  wire rot = (op == 3'd3) || (op == 3'd4);
  wire arith = (op == 3'd2);
  wire fill = arith & a[W-1];
  logic [W-1:0] mask;
  fam_shift_keep_mask #(.W(W), .STICKY(STICKY)) u_mask (.a(a), .amt(amt), .right(right), .rot(rot), .mask(mask), .sticky(sticky));
  genvar s, i;
  generate
    if (DIR == 1) begin : reversed
      logic [W-1:0] rev_in, x, back;
      for (i = 0; i < W; i = i + 1) begin : rv
        assign rev_in[i] = a[W-1-i];
      end
      assign x = right ? rev_in : a;
      logic [W-1:0] st [0:NS];
      assign st[0] = x;
      for (s = 0; s < NS; s = s + 1) begin : stage
        localparam int G = ORDER ? (NS - 1 - s) : s;          // the digit this stage consumes
        localparam int KB = (G * K + K <= AW) ? K : AW - G * K;
        fam_shift_stage #(.W(W), .K(KB), .SH(G * K), .RIGHT(0), .ONE_HOT(ONE_HOT))
          u (.x(st[s]), .digit(amt[G*K +: KB]), .rot(rot), .fill(fill), .y(st[s+1]));
      end
      for (i = 0; i < W; i = i + 1) begin : rb
        assign back[i] = st[NS][W-1-i];
      end
      assign y = right ? back : st[NS];
    end else if (DIR == 0) begin : mirrored
      logic [W-1:0] lft [0:NS];
      logic [W-1:0] rgt [0:NS];
      assign lft[0] = a;
      assign rgt[0] = a;
      for (s = 0; s < NS; s = s + 1) begin : stage
        localparam int G = ORDER ? (NS - 1 - s) : s;
        localparam int KB = (G * K + K <= AW) ? K : AW - G * K;
        fam_shift_stage #(.W(W), .K(KB), .SH(G * K), .RIGHT(0), .ONE_HOT(ONE_HOT))
          ul (.x(lft[s]), .digit(amt[G*K +: KB]), .rot(rot), .fill(1'b0), .y(lft[s+1]));
        fam_shift_stage #(.W(W), .K(KB), .SH(G * K), .RIGHT(1), .ONE_HOT(ONE_HOT))
          ur (.x(rgt[s]), .digit(amt[G*K +: KB]), .rot(rot), .fill(fill), .y(rgt[s+1]));
      end
      assign y = right ? rgt[NS] : lft[NS];
    end else begin : negated
      // one left rotator; a right operation is a left rotation by W - amt, and a shift takes
      // its fill through the keep mask (zero and overflow flags fall out of the mask)
      logic [AW-1:0] lamt;
      assign lamt = right ? (W - amt) : amt;
      logic [W-1:0] st [0:NS];
      assign st[0] = a;
      for (s = 0; s < NS; s = s + 1) begin : stage
        localparam int G = ORDER ? (NS - 1 - s) : s;
        localparam int KB = (G * K + K <= AW) ? K : AW - G * K;
        fam_shift_stage #(.W(W), .K(KB), .SH(G * K), .RIGHT(0), .ONE_HOT(ONE_HOT))
          u (.x(st[s]), .digit(lamt[G*K +: KB]), .rot(1'b1), .fill(1'b0), .y(st[s+1]));
      end
      assign y = (st[NS] & mask) | ({W{fill}} & ~mask);
    end
  endgenerate
endmodule



// ----------------------------------------------------------- the keep mask
// mask[i] = 1 where a shift keeps the input bit that lands at i (a rotate keeps
// every bit): the thermometer of the amount for the direction. sticky is the OR
// of the input bits a shift moves out (the low amt bits of a right shift, the
// top amt bits of a left one; none for a rotate), read through the mask of the
// opposite direction, in parallel with the datapath.
module fam_shift_keep_mask #(parameter int W = 16, parameter int STICKY = 1)
  (input logic [W-1:0] a, input logic [$clog2(W)-1:0] amt, input logic right, input logic rot,
   output logic [W-1:0] mask, output logic sticky);
  logic [W-1:0] kept_in;
  genvar i;
  generate
    for (i = 0; i < W; i = i + 1) begin : mk
      assign mask[i] = rot | (right ? (i < W - amt) : (i >= amt));
      assign kept_in[i] = rot | (right ? (i >= amt) : (i < W - amt));
    end
  endgenerate
  assign sticky = STICKY ? |(a & ~kept_in) : 1'b0;
endmodule

// The shifter families of chiALU. One interface:
//   #(parameter int W) (input [W-1:0] a, input [AW-1:0] amt, input [2:0] op, output [W-1:0] y)
// op: 0 shl, 1 shr_logical, 2 shr_arith, 3 rol, 4 ror; amt is below W.
// Every family has `output sticky`, the OR of the bits a shift moves out (0 for a rotate), built
// when STICKY = 1 (the sticky_collect choice; an alignment shifter asks for it) and tied to 0
// otherwise; a consumer that does not collect it leaves the port unconnected.

// ------------------------------------------------------------------ one mux stage
// One stage of a shifter: the K-bit digit of the amount selects among R = 2^K
// candidates, candidate d being the input displaced by d * 2^SH to the left
// (RIGHT = 0) or to the right (RIGHT = 1), the vacated bits taken from the
// other end under `rot` or from `fill`. ONE_HOT = 1 decodes the digit to R
// select lines and forms the mux as an AND-OR (the select_encoding choice);
// ONE_HOT = 0 indexes the candidates by the binary digit.
module fam_shift_stage #(parameter int W = 16, parameter int K = 1, parameter int SH = 0,
                         parameter int RIGHT = 0, parameter int ONE_HOT = 0)
  (input logic [W-1:0] x, input logic [K-1:0] digit, input logic rot, input logic fill, output logic [W-1:0] y);
  localparam int R = 1 << K;
  localparam int D = 1 << SH;
  logic [W*R-1:0] cand;                       // candidate d at [d*W +: W]
  genvar d, i;
  generate
    for (d = 0; d < R; d = d + 1) begin : c
      for (i = 0; i < W; i = i + 1) begin : b
        localparam int S = d * D;             // the displacement of this candidate
        if (S >= W) begin : far
          // a displacement past the word: a rotate wraps it (mod W), a shift clears the word
          localparam int IDX = ((RIGHT ? (i + S) : (i - S)) % W + W) % W;
          assign cand[d*W + i] = rot ? x[IDX] : fill;
        end else if (RIGHT) begin : r
          if (i + S < W) begin : in_
            assign cand[d*W + i] = x[i + S];
          end else begin : out_
            assign cand[d*W + i] = rot ? x[i + S - W] : fill;
          end
        end else begin : l
          if (i >= S) begin : in_
            assign cand[d*W + i] = x[i - S];
          end else begin : out_
            assign cand[d*W + i] = rot ? x[W - S + i] : fill;
          end
        end
      end
    end
    if (ONE_HOT) begin : onehot
      logic [R-1:0] sel;
      for (d = 0; d < R; d = d + 1) begin : dec
        assign sel[d] = (digit == d);
      end
      for (i = 0; i < W; i = i + 1) begin : orb
        logic [R-1:0] t;
        for (d = 0; d < R; d = d + 1) begin : and_
          assign t[d] = sel[d] & cand[d*W + i];
        end
        assign y[i] = |t;
      end
    end else begin : binary
      assign y = cand[digit*W +: W];
    end
  endgenerate
endmodule
