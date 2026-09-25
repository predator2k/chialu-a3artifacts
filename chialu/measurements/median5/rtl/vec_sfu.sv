// sfu_core: behavioral seed derived from the instance (chialu.VecSFU): ROM or piecewise-linear evaluators for the named functions, table evaluators for the slots.
// core.family: direct_lut (sharing=datapath_per_fn)
// LIBRARY: fam_sfu_control_table_341a0dcdce69c940, fam_sfu_control_table_341a0dcdce69c940_data, fam_sfu_control_table_3d69fad249f84812, fam_sfu_control_table_3d69fad249f84812_data, fam_sfu_control_table_4b616625bc5f9d45, fam_sfu_control_table_4b616625bc5f9d45_data, fam_sfu_control_table_f0aa8ac8e4624d36, fam_sfu_control_table_f0aa8ac8e4624d36_data (chialu.targets.rtl.families: the modules of the declared family the lanes instantiate; their text follows the generated module)
// EVOLVE-BLOCK-START
// ADIR-DECL v1
// ADIR-END
module sfu_core (
  input  logic [31:0] x,
  input  logic [1:0] fn_sel,
  output logic [31:0] y
);
  logic [2:0] rnd; assign rnd = 3'd0;
  logic daz; assign daz = 1'b0;
  logic ftz; assign ftz = 1'b0;

  // ---- m0: V = {special[1:0], sign, exp[12] (signed), sig[4]}
  //           X = {special[1:0], sign, exp[12] (signed), sig[14], sticky}
  localparam int m0_SW = 4, m0_EW = 12, m0_XW = 14;
  localparam int m0_VW = 19, m0_XT = 30;
  function automatic [18:0] m0_mkv(input [1:0] sp, input s, input signed [11:0] e, input [3:0] sig);
    m0_mkv = {sp, s, e, sig};
  endfunction
  function automatic [29:0] m0_mkx(input [1:0] sp, input s, input signed [11:0] e, input [13:0] sig, input st);
    m0_mkx = {sp, s, e, sig, st};
  endfunction
  function automatic [29:0] m0_x(input [18:0] v);   // widen V to X
    m0_x = {v[18:18-1], v[18-2], v[18-3 -: 12], {{(14-4){1'b0}}, v[3:0]}, 1'b0};
  endfunction
  // normalize: leading one at bit XW-1 (zero stays zero)
  function automatic [29:0] m0_norm(input [29:0] x);
    logic [13:0] s; logic signed [11:0] e; integer k;
    s = x[14:1]; e = x[14+12:14+1];
    if (s != 0) begin
      for (k = 8; k >= 1; k = k / 2) begin
        if (k < 14) begin
          if (s[13 -: 1] == 1'b0 && (s >> (14 - k)) == 0) begin
            s = s << k; e = e - k;
          end
        end
      end
    end
    m0_norm = {x[29:29-1], x[29-2], e, s, x[0]};
  endfunction

  function automatic m0_rup(input [2:0] rnd, input s, input inexact, input [14:0] rest, input [14:0] halfv,
                             input st, input lsb, input [14+8:0] fint, input [7:0] word);
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
  function automatic [29:0] m0_add(input [29:0] a, input [29:0] b, input sub);
    logic [29:0] na, nb, big, sml; logic [1:0] spa, spb; logic sa, sb, sr, sw;
    logic signed [11:0] ea, eb, d; logic [14:0] ms, mb, r; logic st, stb; integer sh;
    na = m0_norm(a); nb = m0_norm(b);
    spa = na[29:29-1]; spb = nb[29:29-1];
    sa = na[29-2]; sb = nb[29-2] ^ sub;
    if (spa == 2'd1 || spb == 2'd1) m0_add = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 && spb == 2'd2) m0_add = (sa == sb) ? m0_mkx(2'd2, sa, 0, 0, 1'b0) : m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m0_add = m0_mkx(2'd2, sa, 0, 0, 1'b0);
    else if (spb == 2'd2) m0_add = m0_mkx(2'd2, sb, 0, 0, 1'b0);
    else if (na[14:1] == 0 && !na[0]) m0_add = {nb[29:29-1], sb, nb[29-3:0]};
    else if (nb[14:1] == 0 && !nb[0]) m0_add = na;
    else begin
      ea = na[14+12:14+1]; eb = nb[14+12:14+1];
      // order by magnitude (both normalized): larger exponent, then sig
      if (ea > eb || (ea == eb && na[14:1] >= nb[14:1])) begin big = na; sml = nb; sw = 1'b0; end
      else begin big = nb; sml = na; sw = 1'b1; end
      d = big[14+12:14+1] - sml[14+12:14+1];
      ms = {1'b0, sml[14:1]}; stb = sml[0];
      if (d > 14 + 1) begin stb = stb | (ms != 0); ms = 0; end
      else begin
        for (sh = 0; sh < 14 + 2; sh = sh + 1) begin
          if (sh < d) begin stb = stb | ms[0]; ms = ms >> 1; end
        end
      end
      mb = {1'b0, big[14:1]}; st = big[0] | stb;
      if ((sw ? sb : sa) == (sw ? sa : sb)) begin
        r = mb + ms;
        sr = sw ? sb : sa;
      end else begin
        // subtract: the sticky of the smaller operand borrows one lsb
        r = mb - ms - (stb ? 1'b1 : 1'b0);
        sr = sw ? sb : sa;
        if (r == 0 && !st) sr = 1'b0;
      end
      if (r[14]) begin st = st | r[0]; r = r >> 1; m0_add = m0_mkx(2'd0, sr, big[14+12:14+1] + 1, r[13:0], st); end
      else m0_add = m0_mkx(2'd0, sr, big[14+12:14+1], r[13:0], st);
    end
  endfunction
  function automatic [29:0] m0_mul(input [29:0] a, input [29:0] b);
    logic [29:0] na, nb; logic [1:0] spa, spb; logic s; logic [2*14-1:0] pr; logic st; integer k;
    na = m0_norm(a); nb = m0_norm(b);
    spa = na[29:29-1]; spb = nb[29:29-1]; s = na[29-2] ^ nb[29-2];
    if (spa == 2'd1 || spb == 2'd1) m0_mul = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 || spb == 2'd2) begin
      if ((spa == 2'd0 && na[14:1] == 0 && !na[0]) || (spb == 2'd0 && nb[14:1] == 0 && !nb[0]))
        m0_mul = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
      else m0_mul = m0_mkx(2'd2, s, 0, 0, 1'b0);
    end else begin
      pr = na[14:1] * nb[14:1];
      st = na[0] | nb[0];
      // keep the top XW bits of the product, the rest folds into sticky
      st = st | (pr[13:0] != 0);
      m0_mul = m0_mkx(2'd0, s, na[14+12:14+1] + nb[14+12:14+1] + 14, pr[2*14-1:14], st);
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
  function automatic [2*14+1:0] m0_udiv(input [13:0] a, input [13:0] dv);
    logic [14+1:0] r; logic [14:0] q; logic ge; integer i;
    r = {2'b0, a}; q = 0;
    for (i = 14; i >= 0; i = i - 1) begin
      ge = (r >= {2'b0, dv});
      r = ge ? r - {2'b0, dv} : r;
      q = {q[13:0], ge};
      if (i > 0) r = {r[14:0], 1'b0};
    end
    m0_udiv = {q, r[14:0]};
  endfunction
  // the exact product: {special[1:0], sign, exp[EW], sig[2XW]} (no sticky)
  function automatic [2*14+12+2:0] m0_mulx(input [29:0] a, input [29:0] b);
    logic [29:0] na, nb; logic [1:0] spa, spb, sp; logic s; logic [2*14-1:0] pr;
    na = m0_norm(a); nb = m0_norm(b);
    pr = na[14:1] * nb[14:1];
    spa = na[29:29-1]; spb = nb[29:29-1]; s = na[29-2] ^ nb[29-2];
    if (spa == 2'd1 || spb == 2'd1) sp = 2'd1;
    else if (spa == 2'd2 || spb == 2'd2)
      sp = ((spa == 2'd0 && na[14:1] == 0) || (spb == 2'd0 && nb[14:1] == 0)) ? 2'd1 : 2'd2;
    else sp = 2'd0;
    m0_mulx = {sp, s, na[14+12:14+1] + nb[14+12:14+1], pr};
  endfunction
  function automatic [29:0] m0_div(input [29:0] a, input [29:0] b);
    logic [29:0] na, nb; logic [1:0] spa, spb; logic s; logic [2*14+1:0] qr; logic [14:0] q, r;
    na = m0_norm(a); nb = m0_norm(b);
    spa = na[29:29-1]; spb = nb[29:29-1]; s = na[29-2] ^ nb[29-2];
    if (spa == 2'd1 || spb == 2'd1) m0_div = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 && spb == 2'd2) m0_div = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m0_div = m0_mkx(2'd2, s, 0, 0, 1'b0);
    else if (spb == 2'd2) m0_div = m0_mkx(2'd0, s, 0, 0, 1'b0);
    else if (nb[14:1] == 0 && !nb[0]) begin
      if (na[14:1] == 0 && !na[0]) m0_div = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
      else m0_div = m0_mkx(2'd2, s, 0, 0, 1'b0);
    end else if (na[14:1] == 0 && !na[0]) m0_div = m0_mkx(2'd0, s, 0, 0, 1'b0);
    else begin
      qr = m0_udiv(na[14:1], nb[14:1]);     // both normalized: nonzero finite
      q = qr[2*14+1:14+1]; r = qr[14:0];
      // q < 2^(XW+1): drop one bit when it carries
      if (q[14]) m0_div = m0_mkx(2'd0, s, na[14+12:14+1] - nb[14+12:14+1] - 14 + 1, q[14:1], (r != 0) | q[0] | na[0] | nb[0]);
      else m0_div = m0_mkx(2'd0, s, na[14+12:14+1] - nb[14+12:14+1] - 14, q[13:0], (r != 0) | na[0] | nb[0]);
    end
  endfunction
  function automatic [29:0] m0_sqrt(input [29:0] a);
    logic [29:0] na; logic [1:0] spa; logic signed [11:0] e; logic [14:0] m; logic [2*14+3:0] rad;
    logic [14+2:0] rem, trial; logic [14:0] root; logic ge; integer i;
    na = m0_norm(a); spa = na[29:29-1];
    if (spa == 2'd1) m0_sqrt = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m0_sqrt = na[29-2] ? m0_mkx(2'd1, 1'b0, 0, 0, 1'b0) : na;
    else if (na[14:1] == 0 && !na[0]) m0_sqrt = na;
    else if (na[29-2]) m0_sqrt = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else begin
      e = na[14+12:14+1];
      // value = m * 2^e with e even; radicand = m * 2^(2K): root = sqrt(m) * 2^K, XW+1 bits
      if (e[0]) begin m = {na[14:1], 1'b0}; e = e - 1; end
      else m = {1'b0, na[14:1]};
      rad = {{(14+3){1'b0}}, m} << 14;
      rem = 0; root = 0;
      for (i = 14; i >= 0; i = i - 1) begin
        rem = {rem[14:0], rad[2*i +: 2]};
        trial = {root, 2'b01};
        ge = (rem >= trial);                  // unconditional assignments, as in udiv
        rem = ge ? rem - trial : rem;
        root = {root[13:0], ge};
      end
      m0_sqrt = m0_mkx(2'd0, 1'b0, (e >>> 1) - 7 + 1, root[14:1], (rem != 0) | root[0] | na[0]);
    end
  endfunction
  // X ordering treats NaN as unordered and compares finite values by sign and magnitude
  function automatic m0_lt(input [29:0] a, input [29:0] b);
    logic [29:0] na, nb; logic za, zb, sa, sb, mag_lt; logic signed [11:0] ea, eb;
    na = m0_norm(a); nb = m0_norm(b);
    za = (na[14:1] == 0) && !na[0]; zb = (nb[14:1] == 0) && !nb[0];
    sa = na[29-2] && !za; sb = nb[29-2] && !zb;
    if (na[29:29-1] == 2'd1 || nb[29:29-1] == 2'd1) m0_lt = 1'b0;
    else if (na[29:29-1] == 2'd2 || nb[29:29-1] == 2'd2) begin
      if (na[29:29-1] == 2'd2 && nb[29:29-1] == 2'd2) m0_lt = na[29-2] && !nb[29-2];
      else if (na[29:29-1] == 2'd2) m0_lt = na[29-2];
      else m0_lt = !nb[29-2];
    end else if (za && zb) m0_lt = 1'b0;
    else if (sa != sb) m0_lt = sa;
    else begin
      ea = na[14+12:14+1]; eb = nb[14+12:14+1];
      if (za) mag_lt = 1'b1; else if (zb) mag_lt = 1'b0;
      else mag_lt = (ea < eb) || (ea == eb && (na[14:1] < nb[14:1] || (na[14:1] == nb[14:1] && !na[0] && nb[0])));
      m0_lt = sa ? !mag_lt && !(za && zb) && !m0_eq(na, nb) : mag_lt;
    end
  endfunction
  function automatic m0_eq(input [29:0] a, input [29:0] b);
    logic [29:0] na, nb; logic za, zb;
    na = m0_norm(a); nb = m0_norm(b);
    za = (na[14:1] == 0) && !na[0]; zb = (nb[14:1] == 0) && !nb[0];
    if (na[29:29-1] == 2'd1 || nb[29:29-1] == 2'd1) m0_eq = 1'b0;
    else if (na[29:29-1] == 2'd2 || nb[29:29-1] == 2'd2)
      m0_eq = (na[29:29-1] == nb[29:29-1]) && (na[29-2] == nb[29-2]);
    else if (za || zb) m0_eq = za && zb;
    else m0_eq = (na[29-2] == nb[29-2]) && (na[14+12:14+1] == nb[14+12:14+1]) && (na[14:1] == nb[14:1]) && (na[0] == nb[0]);
  endfunction

  // fp8e4m3 pattern -> V (bit VW = denormal-read flag returned beside)
  function automatic [19:0] m0_unpack_s(input [7:0] b, input daz);
    logic [3:0] e; logic [2:0] m; logic [3:0] sig; logic signed [11:0] ex; logic den, s;
    e = b[6:3]; m = b[2:0]; s = b[7]; den = 1'b0; sig = 0; ex = 0;
    if ((e == 4'd15 && m == {3{1'b1}})) m0_unpack_s = {1'b0, m0_mkv(2'd1, 1'b0, 0, 0)};
    else if (1'b0) m0_unpack_s = {1'b0, m0_mkv(2'd2, s, 0, 0)};
    else begin
    if (e == 0) begin sig = {{(4-3){1'b0}}, m}; ex = -9; if (m != 0) den = 1'b1; if (daz && m != 0) sig = 0; end
    else begin sig = {{(4-3-1){1'b0}}, 1'b1, m}; ex = e - 10; end
      m0_unpack_s = {den, m0_mkv(2'd0, s, ex, sig)};
    end
  endfunction

  // X -> fp8e4m3 (fp8e4m3): sign(1) exp 4 man 3, top field 15, max finite 7'd126
  function automatic [10+8-1:0] m0_pack_fp8e4m3(input [29:0] x0, input [2:0] rnd, input [7:0] word, input ftz);
    logic [29:0] x; logic [1:0] sp; logic s; logic signed [11:0] e, eu, biased; logic [13:0] sig;
    logic st, inexact, up, upn, half_eq, gt_half, tiny, ovf, unf, carry_n, to_inf; integer sh, shn, sht;
    logic [14:0] keep, rest, keepn, restn, halfv, halfn; logic [14+8:0] fint, fintn; logic [10-1:0] fl;
    logic [8+12:0] code; logic [8:0] mag; logic [8-1:0] outb;
    x = m0_norm(x0); sp = x[29:29-1]; s = x[29-2] & 1; sig = x[14:1]; st = x[0]; e = x[14+12:14+1];
    fl = 0; outb = 0;
    if (sp == 2'd1) begin fl[5] = 1'b1; outb = 8'd127; end
    else if (sp == 2'd2) begin
      outb = {s, 7'd126}; if (!0) begin fl[4] = 1'b1; fl[2] = 1'b1; end
    end else if (sig == 0 && !st) begin outb = 1 ? 0 : {s, {7{1'b0}}}; end
    else begin
      if (sig == 0) begin sig = 1 << 13; e = e - (2*14-1); end // normalize the lone sticky's tiny value
      eu = e + 13;                 // exponent of the leading one
      biased = eu + 7;
      shn = 14 - 1 - 3;           // bits dropped at the normal precision
      sh = (biased >= 1) ? shn : shn + (1 - biased);
      sht = sh;
      if (sh > 14 + 1) sh = 14 + 1;
      keep = {1'b0, sig} >> sh; rest = {1'b0, sig} & ((sh > 14) ? {(14+1){1'b1}} : ({1'b0, {14{1'b1}}} >> (14 - sh)));
      halfv = (sh == 0) ? 0 : ({{14{1'b0}}, 1'b1} << (sh - 1));
      keepn = {1'b0, sig} >> shn; restn = {1'b0, sig} & ({1'b0, {14{1'b1}}} >> (14 - shn));
      halfn = (shn == 0) ? 0 : ({{14{1'b0}}, 1'b1} << (shn - 1));
      inexact = (rest != 0) | st;
      fint = (sht - 8 > 14) ? 0 : (sht >= 8) ? (rest >> (sht - 8)) : (rest << (8 - sht));
      fintn = (shn >= 8) ? (restn >> (shn - 8)) : (restn << (8 - shn));
      up = m0_rup(rnd, s, inexact, rest, halfv, st, keep[0], fint, word);
      upn = m0_rup(rnd, s, (restn != 0) | st, restn, halfn, st, keepn[0], fintn, word);
      carry_n = ((keepn + upn) == ({{14{1'b0}}, 1'b1} << (3 + 1)));
      mag = keep + up;
      if (biased < 1) biased = 0;
      code = (biased < 1) ? mag : ((biased << 3) + mag - ({{(8+12){1'b0}}, 1'b1} << 3));
      tiny = 0 ? (eu < -6) : ((eu < -6) && !(eu == -6 - 1 && carry_n) && !(eu + 7 == 0 && carry_n));
      ovf = (code > 7'd126);
      if (ovf) begin
        to_inf = 0 && (rnd == 3'd0 || (rnd == 3'd3 && !s) || (rnd == 3'd2 && s) || rnd == 3'd5 || (rnd == 3'd4 && (eu > 8 || up)));
        outb = to_inf ? {s, 7'd126} : {s, 7'd126};
        fl[2] = 1'b1; fl[4] = 1'b1;
      end else begin
        outb = {s, code[6:0]};
        if (inexact) fl[4] = 1'b1;
        if (tiny && inexact) fl[3] = 1'b1;
        if (ftz && code[7-1:3] == 0 && code[2:0] != 0) begin
          outb = {s, {7{1'b0}}}; fl[4] = 1'b1; fl[3] = 1'b1;
        end

      end
    end
    m0_pack_fp8e4m3 = {fl, outb};
  endfunction

  logic [31:0] y_m0; logic [39:0] fl_m0;
  logic [19:0] m0_u0; assign m0_u0 = m0_unpack_s(x[0 +: 8], daz);
  logic [29:0] m0_x0; assign m0_x0 = m0_x(m0_u0[18:0]);
  logic m0_den0; assign m0_den0 = m0_u0[19];
  logic [19:0] m0_u1; assign m0_u1 = m0_unpack_s(x[8 +: 8], daz);
  logic [29:0] m0_x1; assign m0_x1 = m0_x(m0_u1[18:0]);
  logic m0_den1; assign m0_den1 = m0_u1[19];
  logic [19:0] m0_u2; assign m0_u2 = m0_unpack_s(x[16 +: 8], daz);
  logic [29:0] m0_x2; assign m0_x2 = m0_x(m0_u2[18:0]);
  logic m0_den2; assign m0_den2 = m0_u2[19];
  logic [19:0] m0_u3; assign m0_u3 = m0_unpack_s(x[24 +: 8], daz);
  logic [29:0] m0_x3; assign m0_x3 = m0_x(m0_u3[18:0]);
  logic m0_den3; assign m0_den3 = m0_u3[19];
  // structure core: family direct_lut realized by the library module fam_sfu_control_table_4b616625bc5f9d45 (exp2)
  logic [7:0] m0_f0_0_yb;
  logic [9:0] m0_f0_0_flags;
  fam_sfu_control_table_4b616625bc5f9d45 u_m0_f0_0 (.x(x[0 +: 8]), .rnd(rnd), .daz(daz), .ftz(ftz), .word(8'd0), .y(m0_f0_0_yb), .flags(m0_f0_0_flags));
  logic [7:0] m0_f0_1_yb;
  logic [9:0] m0_f0_1_flags;
  fam_sfu_control_table_4b616625bc5f9d45 u_m0_f0_1 (.x(x[8 +: 8]), .rnd(rnd), .daz(daz), .ftz(ftz), .word(8'd0), .y(m0_f0_1_yb), .flags(m0_f0_1_flags));
  logic [7:0] m0_f0_2_yb;
  logic [9:0] m0_f0_2_flags;
  fam_sfu_control_table_4b616625bc5f9d45 u_m0_f0_2 (.x(x[16 +: 8]), .rnd(rnd), .daz(daz), .ftz(ftz), .word(8'd0), .y(m0_f0_2_yb), .flags(m0_f0_2_flags));
  logic [7:0] m0_f0_3_yb;
  logic [9:0] m0_f0_3_flags;
  fam_sfu_control_table_4b616625bc5f9d45 u_m0_f0_3 (.x(x[24 +: 8]), .rnd(rnd), .daz(daz), .ftz(ftz), .word(8'd0), .y(m0_f0_3_yb), .flags(m0_f0_3_flags));
  // structure core: family direct_lut realized by the library module fam_sfu_control_table_3d69fad249f84812 (recip)
  logic [7:0] m0_f1_0_yb;
  logic [9:0] m0_f1_0_flags;
  fam_sfu_control_table_3d69fad249f84812 u_m0_f1_0 (.x(x[0 +: 8]), .rnd(rnd), .daz(daz), .ftz(ftz), .word(8'd0), .y(m0_f1_0_yb), .flags(m0_f1_0_flags));
  logic [7:0] m0_f1_1_yb;
  logic [9:0] m0_f1_1_flags;
  fam_sfu_control_table_3d69fad249f84812 u_m0_f1_1 (.x(x[8 +: 8]), .rnd(rnd), .daz(daz), .ftz(ftz), .word(8'd0), .y(m0_f1_1_yb), .flags(m0_f1_1_flags));
  logic [7:0] m0_f1_2_yb;
  logic [9:0] m0_f1_2_flags;
  fam_sfu_control_table_3d69fad249f84812 u_m0_f1_2 (.x(x[16 +: 8]), .rnd(rnd), .daz(daz), .ftz(ftz), .word(8'd0), .y(m0_f1_2_yb), .flags(m0_f1_2_flags));
  logic [7:0] m0_f1_3_yb;
  logic [9:0] m0_f1_3_flags;
  fam_sfu_control_table_3d69fad249f84812 u_m0_f1_3 (.x(x[24 +: 8]), .rnd(rnd), .daz(daz), .ftz(ftz), .word(8'd0), .y(m0_f1_3_yb), .flags(m0_f1_3_flags));
  // structure core: family direct_lut realized by the library module fam_sfu_control_table_f0aa8ac8e4624d36 (rsqrt)
  logic [7:0] m0_f2_0_yb;
  logic [9:0] m0_f2_0_flags;
  fam_sfu_control_table_f0aa8ac8e4624d36 u_m0_f2_0 (.x(x[0 +: 8]), .rnd(rnd), .daz(daz), .ftz(ftz), .word(8'd0), .y(m0_f2_0_yb), .flags(m0_f2_0_flags));
  logic [7:0] m0_f2_1_yb;
  logic [9:0] m0_f2_1_flags;
  fam_sfu_control_table_f0aa8ac8e4624d36 u_m0_f2_1 (.x(x[8 +: 8]), .rnd(rnd), .daz(daz), .ftz(ftz), .word(8'd0), .y(m0_f2_1_yb), .flags(m0_f2_1_flags));
  logic [7:0] m0_f2_2_yb;
  logic [9:0] m0_f2_2_flags;
  fam_sfu_control_table_f0aa8ac8e4624d36 u_m0_f2_2 (.x(x[16 +: 8]), .rnd(rnd), .daz(daz), .ftz(ftz), .word(8'd0), .y(m0_f2_2_yb), .flags(m0_f2_2_flags));
  logic [7:0] m0_f2_3_yb;
  logic [9:0] m0_f2_3_flags;
  fam_sfu_control_table_f0aa8ac8e4624d36 u_m0_f2_3 (.x(x[24 +: 8]), .rnd(rnd), .daz(daz), .ftz(ftz), .word(8'd0), .y(m0_f2_3_yb), .flags(m0_f2_3_flags));
  // structure core: family direct_lut realized by the library module fam_sfu_control_table_341a0dcdce69c940 (sigmoid)
  logic [7:0] m0_f3_0_yb;
  logic [9:0] m0_f3_0_flags;
  fam_sfu_control_table_341a0dcdce69c940 u_m0_f3_0 (.x(x[0 +: 8]), .rnd(rnd), .daz(daz), .ftz(ftz), .word(8'd0), .y(m0_f3_0_yb), .flags(m0_f3_0_flags));
  logic [7:0] m0_f3_1_yb;
  logic [9:0] m0_f3_1_flags;
  fam_sfu_control_table_341a0dcdce69c940 u_m0_f3_1 (.x(x[8 +: 8]), .rnd(rnd), .daz(daz), .ftz(ftz), .word(8'd0), .y(m0_f3_1_yb), .flags(m0_f3_1_flags));
  logic [7:0] m0_f3_2_yb;
  logic [9:0] m0_f3_2_flags;
  fam_sfu_control_table_341a0dcdce69c940 u_m0_f3_2 (.x(x[16 +: 8]), .rnd(rnd), .daz(daz), .ftz(ftz), .word(8'd0), .y(m0_f3_2_yb), .flags(m0_f3_2_flags));
  logic [7:0] m0_f3_3_yb;
  logic [9:0] m0_f3_3_flags;
  fam_sfu_control_table_341a0dcdce69c940 u_m0_f3_3 (.x(x[24 +: 8]), .rnd(rnd), .daz(daz), .ftz(ftz), .word(8'd0), .y(m0_f3_3_yb), .flags(m0_f3_3_flags));
  always_comb begin
    y_m0 = '0; fl_m0 = '0;
    case (fn_sel)
      2'd0: begin
        y_m0[0 +: 8] = m0_f0_0_yb;
        fl_m0[0 +: 10] = m0_f0_0_flags;
        y_m0[8 +: 8] = m0_f0_1_yb;
        fl_m0[10 +: 10] = m0_f0_1_flags;
        y_m0[16 +: 8] = m0_f0_2_yb;
        fl_m0[20 +: 10] = m0_f0_2_flags;
        y_m0[24 +: 8] = m0_f0_3_yb;
        fl_m0[30 +: 10] = m0_f0_3_flags;
      end
      2'd1: begin
        y_m0[0 +: 8] = m0_f1_0_yb;
        fl_m0[0 +: 10] = m0_f1_0_flags;
        y_m0[8 +: 8] = m0_f1_1_yb;
        fl_m0[10 +: 10] = m0_f1_1_flags;
        y_m0[16 +: 8] = m0_f1_2_yb;
        fl_m0[20 +: 10] = m0_f1_2_flags;
        y_m0[24 +: 8] = m0_f1_3_yb;
        fl_m0[30 +: 10] = m0_f1_3_flags;
      end
      2'd2: begin
        y_m0[0 +: 8] = m0_f2_0_yb;
        fl_m0[0 +: 10] = m0_f2_0_flags;
        y_m0[8 +: 8] = m0_f2_1_yb;
        fl_m0[10 +: 10] = m0_f2_1_flags;
        y_m0[16 +: 8] = m0_f2_2_yb;
        fl_m0[20 +: 10] = m0_f2_2_flags;
        y_m0[24 +: 8] = m0_f2_3_yb;
        fl_m0[30 +: 10] = m0_f2_3_flags;
      end
      2'd3: begin
        y_m0[0 +: 8] = m0_f3_0_yb;
        fl_m0[0 +: 10] = m0_f3_0_flags;
        y_m0[8 +: 8] = m0_f3_1_yb;
        fl_m0[10 +: 10] = m0_f3_1_flags;
        y_m0[16 +: 8] = m0_f3_2_yb;
        fl_m0[20 +: 10] = m0_f3_2_flags;
        y_m0[24 +: 8] = m0_f3_3_yb;
        fl_m0[30 +: 10] = m0_f3_3_flags;
      end
      default: ;
    endcase
  end
  logic [39:0] fl_all;
  assign y = y_m0; assign fl_all = fl_m0;
endmodule
// EVOLVE-BLOCK-END
// ---- the family library modules the lanes instantiate (chialu/targets/rtl/families; fixed text, replaced by editing the instances)


module fam_sfu_control_table_341a0dcdce69c940(input [7:0] x, input [2:0] rnd, input daz, ftz,
    input [7:0] word, output [7:0] y, output [9:0] flags);
  wire denormal = (x[3 +: 4] == 0 && x[2:0] != 0);
  wire [7:0] operand = daz && denormal ? {x[7], {7{1'b0}}} : x;
  wire [143:0] data;
  fam_sfu_control_table_341a0dcdce69c940_data table_data(.address(operand), .data(data));
  reg [17:0] result;
  always @* begin
    case (rnd)
      3'd0: result = data[0 +: 18];
      3'd1: result = data[18 +: 18];
      3'd2: result = data[36 +: 18];
      3'd3: result = data[54 +: 18];
      default: begin
        if ({1'b0,word} < data[126 +: 9]) result = data[72 +: 18];
        else if ({1'b0,word} < data[135 +: 9]) result = data[90 +: 18];
        else result = data[108 +: 18];
      end
    endcase
  end
  wire flush = ftz && (result[3 +: 4] == 0 && result[2:0] != 0);
  assign y = flush ? {result[7], {7{1'b0}}} : result[7:0];
  assign flags = result[8 +: 10] | (denormal ? 10'd64 : 10'd0) | (flush ? 10'd24 : 10'd0);
endmodule


// direct_lut independently evaluated control records at 128/256 working bits
module fam_sfu_control_table_341a0dcdce69c940_data (
  input logic [7:0] address,
  output logic [143:0] data
);
  logic [143:0] rom1_t [0:255];
  initial begin rom1_t[0]=144'd11172150686325201629382558150916668037005360; rom1_t[1]=144'd11150459014667058209001163126695045745348656; rom1_t[2]=144'd11150629155850518678232894813998761629454384; rom1_t[3]=144'd11150799297033979147464626501302477513560112; rom1_t[4]=144'd11150969438217439616696358188606193397665840; rom1_t[5]=144'd11151139579400900085928089875909909281771568; rom1_t[6]=144'd11151309720584360555159821563213625165877296; rom1_t[7]=144'd11151479861767821024391553250517341049983024; rom1_t[8]=144'd11151650002951281493623284937821056934088752; rom1_t[9]=144'd11151820144134741962855016625124772818194480; rom1_t[10]=144'd11151990285318202432086748312428488702300208; rom1_t[11]=144'd11152160426501662901318479999732204586405936; rom1_t[12]=144'd11152330567685123370550211687035920470511664; rom1_t[13]=144'd11152500708868583839781943374339636354617392; rom1_t[14]=144'd11152670850052044309013675061643352238723120; rom1_t[15]=144'd11152840991235504778245406748947068122828848; rom1_t[16]=144'd11153011132418965247477138436250784006934576; rom1_t[17]=144'd11153351414785886185940601810858215775146032; rom1_t[18]=144'd11153691697152807124404065185465647543357488; rom1_t[19]=144'd11154031979519728062867528560073079311568944; rom1_t[20]=144'd11154372261886649001330991934680511079780400; rom1_t[21]=144'd11154712544253569939794455309287942847991856; rom1_t[22]=144'd11155052826620490878257918683895374616203312; rom1_t[23]=144'd11155393108987411816721382058502806384414768; rom1_t[24]=144'd11155733391354332755184845433110238152626224; rom1_t[25]=144'd11156413956088174632111772182325101689049136; rom1_t[26]=144'd11157094520822016509038698931539965225472048; rom1_t[27]=144'd11157775085555858385965625680754828761894960; rom1_t[28]=144'd11158455650289700262892552429969692298317872; rom1_t[29]=144'd11159136215023542139819479179184555834740784; rom1_t[30]=144'd11159816779757384016746405928399419371163696; rom1_t[31]=144'd11160497344491225893673332677614282907586608; rom1_t[32]=144'd11161177909225067770600259426829146444009520; rom1_t[33]=144'd11162539038692751524454112925258873516855345; rom1_t[34]=144'd11163900168160435278307966423688600589701169; rom1_t[35]=144'd11165261297628119032161819922118327662546993; rom1_t[36]=144'd11166622427095802786015673420548054735392817; rom1_t[37]=144'd11167983556563486539869526918977781808238641; rom1_t[38]=144'd11169344686031170293723380417407508881084465; rom1_t[39]=144'd11170620744907123812961368072185378011877425; rom1_t[40]=144'd11171981874374807566815221570615105084723249; rom1_t[41]=144'd11152926062151754804464460989259693859016753; rom1_t[42]=144'd11155563250495392077556302142467290062655537; rom1_t[43]=144'd11158200438839029350648143295674886266294321; rom1_t[44]=144'd11160837627182666623739984448882482469933105; rom1_t[45]=144'd11163474815526303896831825602090078673571890; rom1_t[46]=144'd11166026933278210935307800911645816935157810; rom1_t[47]=144'd11168664121621848208399642064853413138796594; rom1_t[48]=144'd11171216239373755246875617374409151400382514; rom1_t[49]=144'd11154542403719149053769100415305762552156210; rom1_t[50]=144'd11159476498039502661489319347113523191222322; rom1_t[51]=144'd11164410592359856269209538278921283830288435; rom1_t[52]=144'd11169174545496749407698025523425328585248819; rom1_t[53]=144'd11152160427475222276128045189714507968811059; rom1_t[54]=144'd11156669168836924710768934903262978897612851; rom1_t[55]=144'd11161177910198627145409824616811449826414643; rom1_t[56]=144'd11165516510376869110818982643056204871110708; rom1_t[57]=144'd11152075357208011833115367742723417820893236; rom1_t[58]=144'd11159816781055463183159159515042490547703860; rom1_t[59]=144'd11167132851944263360123622069102273564250165; rom1_t[60]=144'd11152075357532531624718556139384185615028277; rom1_t[61]=144'd11158370581320568986292628569621673326940213; rom1_t[62]=144'd11164070310966494705555640094296155444482102; rom1_t[63]=144'd11169344687653769251739322400711347851759670; rom1_t[64]=144'd11152330569632242120169342067000527235321910; rom1_t[65]=144'd11160667487621805112524194744882605556502582; rom1_t[66]=144'd11167473134960223881793462237031240920731703; rom1_t[67]=144'd11151139581672538627150408652535283840716855; rom1_t[68]=144'd11155563252442510827175432522431896827465783; rom1_t[69]=144'd11159136217295180681041797955809930393686071; rom1_t[70]=144'd11161858476230548188749504952669384539377720; rom1_t[71]=144'd11164070311615534288762016887617691032752184; rom1_t[72]=144'd11165856794041869215695199604306707815862328; rom1_t[73]=144'd11168238770610315784939443226558730193342520; rom1_t[74]=144'd11169770041261460008025028412292173150294072; rom1_t[75]=144'd11170705817770492588799552692462610512875576; rom1_t[76]=144'd11171216241320873996494747754373758165192760; rom1_t[77]=144'd11171556523687794934958211128981189933404216; rom1_t[78]=144'd11171811735462985638805808659936763759562808; rom1_t[79]=144'd11171896806054715873421674503588621701615672; rom1_t[80]=144'd11171981876646446108037540347240479643668536; rom1_t[81]=144'd11172066947238176342653406190892337585721400; rom1_t[82]=144'd11172066947238176342653406190892337585721400; rom1_t[83]=144'd11172066947238176342653406190892337585721400; rom1_t[84]=144'd11172066947238176342653406190892337585721400; rom1_t[85]=144'd11172066947238176342653406190892337585721400; rom1_t[86]=144'd11172066947238176342653406190892337585721400; rom1_t[87]=144'd11172066947238176342653406190892337585721400; rom1_t[88]=144'd11172066947238176342653406190892337585721400; rom1_t[89]=144'd11172066947238176342653406190892337585721400; rom1_t[90]=144'd11172066947238176342653406190892337585721400; rom1_t[91]=144'd11172066947238176342653406190892337585721400; rom1_t[92]=144'd11172066947238176342653406190892337585721400; rom1_t[93]=144'd11172066947238176342653406190892337585721400; rom1_t[94]=144'd11172066947238176342653406190892337585721400; rom1_t[95]=144'd11172066947238176342653406190892337585721400; rom1_t[96]=144'd11172066947238176342653406190892337585721400; rom1_t[97]=144'd11172066947238176342653406190892337585721400; rom1_t[98]=144'd11172066947238176342653406190892337585721400; rom1_t[99]=144'd11172066947238176342653406190892337585721400; rom1_t[100]=144'd11172066947238176342653406190892337585721400; rom1_t[101]=144'd11172066947238176342653406190892337585721400; rom1_t[102]=144'd11172066947238176342653406190892337585721400; rom1_t[103]=144'd11172066947238176342653406190892337585721400; rom1_t[104]=144'd11172066947238176342653406190892337585721400; rom1_t[105]=144'd11172066947238176342653406190892337585721400; rom1_t[106]=144'd11172066947238176342653406190892337585721400; rom1_t[107]=144'd11172066947238176342653406190892337585721400; rom1_t[108]=144'd11172066947238176342653406190892337585721400; rom1_t[109]=144'd11172066947238176342653406190892337585721400; rom1_t[110]=144'd11172066947238176342653406190892337585721400; rom1_t[111]=144'd11172066947238176342653406190892337585721400; rom1_t[112]=144'd11172066947238176342653406190892337585721400; rom1_t[113]=144'd11172066947238176342653406190892337585721400; rom1_t[114]=144'd11172066947238176342653406190892337585721400; rom1_t[115]=144'd11172066947238176342653406190892337585721400; rom1_t[116]=144'd11172066947238176342653406190892337585721400; rom1_t[117]=144'd11172066947238176342653406190892337585721400; rom1_t[118]=144'd11172066947238176342653406190892337585721400; rom1_t[119]=144'd11172066947238176342653406190892337585721400; rom1_t[120]=144'd11172066947238176342653406190892337585721400; rom1_t[121]=144'd11172066947238176342653406190892337585721400; rom1_t[122]=144'd11172066947238176342653406190892337585721400; rom1_t[123]=144'd11172066947238176342653406190892337585721400; rom1_t[124]=144'd11172066947238176342653406190892337585721400; rom1_t[125]=144'd11172066947238176342653406190892337585721400; rom1_t[126]=144'd11172066947238176342653406190892337585721400; rom1_t[127]=144'd11172153453505464629770016477283648626499967; rom1_t[128]=144'd11172150686325201629382558150916668037005360; rom1_t[129]=144'd11171811732866827305980301486650621406482480; rom1_t[130]=144'd11171471450499906367516838112043189638271024; rom1_t[131]=144'd11171131168132985429053374737435757870059568; rom1_t[132]=144'd11170790885766064490589911362828326101848112; rom1_t[133]=144'd11170450603399143552126447988220894333636656; rom1_t[134]=144'd11170110321032222613662984613613462565425200; rom1_t[135]=144'd11169770038665301675199521239006030797213744; rom1_t[136]=144'd11169429756298380736736057864398599029002288; rom1_t[137]=144'd11169089473931459798272594489791167260790832; rom1_t[138]=144'd11168749191564538859809131115183735492579376; rom1_t[139]=144'd11168408909197617921345667740576303724367920; rom1_t[140]=144'd11168068626830696982882204365968871956156464; rom1_t[141]=144'd11167728344463776044418740991361440187945008; rom1_t[142]=144'd11167388062096855105955277616754008419733552; rom1_t[143]=144'd11167047779729934167491814242146576651522096; rom1_t[144]=144'd11166707497363013229028350867539144883310640; rom1_t[145]=144'd11166026932629171352101424118324281346887728; rom1_t[146]=144'd11165346367895329475174497369109417810464816; rom1_t[147]=144'd11164665803161487598247570619894554274041904; rom1_t[148]=144'd11163985238427645721320643870679690737618992; rom1_t[149]=144'd11163304673693803844393717121464827201196080; rom1_t[150]=144'd11162624108959961967466790372249963664773168; rom1_t[151]=144'd11161943544226120090539863623035100128350256; rom1_t[152]=144'd11161262979492278213612936873820236591927344; rom1_t[153]=144'd11159901850024594459759083375390509519081519; rom1_t[154]=144'd11158540720556910705905229876960782446235695; rom1_t[155]=144'd11157179591089226952051376378531055373389871; rom1_t[156]=144'd11155818461621543198197522880101328300544047; rom1_t[157]=144'd11154457332153859444343669381671601227698223; rom1_t[158]=144'd11153096202686175690489815883241874154852399; rom1_t[159]=144'd11151735073218491936635962384812147082006575; rom1_t[160]=144'd11172152015233748244439042494775183529480239; rom1_t[161]=144'd11169429755973860945132869467737831234867247; rom1_t[162]=144'd11166707497038493437425162470878377089175599; rom1_t[163]=144'd11163985238103125929717455474018922943483951; rom1_t[164]=144'd11161348049759488656625614320811326739845167; rom1_t[165]=144'd11158625790824121148917907323951872594153518; rom1_t[166]=144'd11155903531888753641210200327092418448461870; rom1_t[167]=144'd11153266343545116368118359173884822244823086; rom1_t[168]=144'd11150544084609748860410652177025368099131438; rom1_t[169]=144'd11166962708489164349669571605173183121199150; rom1_t[170]=144'd11161688331801889803485889298757990713921582; rom1_t[171]=144'd11156328884522885022686341148690940364591149; rom1_t[172]=144'd11151054507835610476502658842275747957313581; rom1_t[173]=144'd11167643272898486434993309957727278863487021; rom1_t[174]=144'd11162453966802942123425493494963944398262317; rom1_t[175]=144'd11157264660707397811857677032200609933037612; rom1_t[176]=144'd11152075354611853500289860569437275467812908; rom1_t[177]=144'd11163730025354375851060292753081045734920236; rom1_t[178]=144'd11153776766121938401003989045813666514735147; rom1_t[179]=144'd11165686648639651455622018760413010608001067; rom1_t[180]=144'd11156158742365865178645044271404921098080298; rom1_t[181]=144'd11168493977842229406342403204263554901610538; rom1_t[182]=144'd11159391424527094302444757933514755101954089; rom1_t[183]=144'd11150459012395419667778844350069671186403369; rom1_t[184]=144'd11163559883197356007018995875795026468409385; rom1_t[185]=144'd11165261294707440907733124352171417515331624; rom1_t[186]=144'd11155818458700865073768827310154418153328678; rom1_t[187]=144'd11170280458645965375259643937648732714045477; rom1_t[188]=144'd11165006081634171037472773234572772512632868; rom1_t[189]=144'd11161858469415632565082548622793260862541859; rom1_t[190]=144'd11160667480806889488857238415006481879666721; rom1_t[191]=144'd11161433115807941808796842611212435564007457; rom1_t[192]=144'd11155988597612687001778240220832759478489119; rom1_t[193]=144'd11154797608354904342346553219724444907343900; rom1_t[194]=144'd11165771713714545232983681860831816049758234; rom1_t[195]=144'd11158625783360165942044574200754213329047575; rom1_t[196]=144'd11153436476291062255667192548008575481417748; rom1_t[197]=144'd11162453958040907750139406785123213956616210; rom1_t[198]=144'd11150544074549635320711811880541566480945167; rom1_t[199]=144'd11166962697455491435161166118707078120607756; rom1_t[200]=144'd11154882672780758536501839526821714760830985; rom1_t[201]=144'd6974429387883754553095538690860230452189190; rom1_t[202]=144'd7849380423180176756129324571517353978501123; rom1_t[203]=144'd3704060629024784602615306707122785832409090; rom1_t[204]=144'd2964541974789336533230378730241202671851521; rom1_t[205]=144'd8543471380133602850109217022424274704537601; rom1_t[206]=144'd10332931277179086756907198953875810887407616; rom1_t[207]=144'd3137235275677193011834852946852057245030400; rom1_t[208]=144'd11023364199661670899274386032354868588451840; rom1_t[209]=144'd959598268566646076960947861212181676693504; rom1_t[210]=144'd10018340228960679147435309129305141175916544; rom1_t[211]=144'd8406507727447923880625169457552713100302336; rom1_t[212]=144'd11169600546845944203943048903415801332111360; rom1_t[213]=144'd11160838275897730038508867007274433300666368; rom1_t[214]=144'd11171046746905358192412768245497386347010048; rom1_t[215]=144'd11156074322760836900020379762770388545705984; rom1_t[216]=144'd11152586428499897280769880173044212921538560; rom1_t[217]=144'd11154202769742771738471331202429513820542976; rom1_t[218]=144'd11168919982112102327016122154200937795688448; rom1_t[219]=144'd11163050111282716138521378942222739794040832; rom1_t[220]=144'd11158541369921013703880489228674268865239040; rom1_t[221]=144'd11155478828618725257709318857207382951335936; rom1_t[222]=144'd11153862487375850800007867827822082052331520; rom1_t[223]=144'd11154032628559311269239599515125797936437248; rom1_t[224]=144'd11155989252169106665404513919118530603653120; rom1_t[225]=144'd11158116016962362530801160010414979154974720; rom1_t[226]=144'd11167643923236148807778134499423068664895488; rom1_t[227]=144'd11160838275897730038508867007274433300666368; rom1_t[228]=144'd11160327852347348630813671945363285648349184; rom1_t[229]=144'd11167303640869227869314671124815636896684032; rom1_t[230]=144'd11155734040393915961556916388162956777494528; rom1_t[231]=144'd11168664770336911623168524623245363969529856; rom1_t[232]=144'd11165687299626353411613220095430335997679616; rom1_t[233]=144'd11166197723176734819308415157341483649996800; rom1_t[234]=144'd11171982523414390773187292525667823709591552; rom1_t[235]=144'd11155563899210455492325184700859240893388800; rom1_t[236]=144'd11157350381636790419258367417548257676498944; rom1_t[237]=144'd11162539687732334730826183880311592141723648; rom1_t[238]=144'd11165347017259432473149756720822904229468160; rom1_t[239]=144'd11165347017259432473149756720822904229468160; rom1_t[240]=144'd11152331216724706576922282642088639095379968; rom1_t[241]=144'd11161774052406762619283391287444870663247872; rom1_t[242]=144'd11172152664597851242419024212971539593697280; rom1_t[243]=144'd11172152664597851242419024212971539593697280; rom1_t[244]=144'd11172152664597851242419024212971539593697280; rom1_t[245]=144'd11172152664597851242419024212971539593697280; rom1_t[246]=144'd11172152664597851242419024212971539593697280; rom1_t[247]=144'd11172152664597851242419024212971539593697280; rom1_t[248]=144'd11172152664597851242419024212971539593697280; rom1_t[249]=144'd11172152664597851242419024212971539593697280; rom1_t[250]=144'd11172152664597851242419024212971539593697280; rom1_t[251]=144'd11172152664597851242419024212971539593697280; rom1_t[252]=144'd11172152664597851242419024212971539593697280; rom1_t[253]=144'd11172152664597851242419024212971539593697280; rom1_t[254]=144'd11172152664597851242419024212971539593697280; rom1_t[255]=144'd11172153453505464629770016477283648626499967; end
  logic [143:0] rom1; assign rom1 = rom1_t[address];
  assign data = rom1;
endmodule



module fam_sfu_control_table_3d69fad249f84812(input [7:0] x, input [2:0] rnd, input daz, ftz,
    input [7:0] word, output [7:0] y, output [9:0] flags);
  wire denormal = (x[3 +: 4] == 0 && x[2:0] != 0);
  wire [7:0] operand = daz && denormal ? {x[7], {7{1'b0}}} : x;
  wire [143:0] data;
  fam_sfu_control_table_3d69fad249f84812_data table_data(.address(operand), .data(data));
  reg [17:0] result;
  always @* begin
    case (rnd)
      3'd0: result = data[0 +: 18];
      3'd1: result = data[18 +: 18];
      3'd2: result = data[36 +: 18];
      3'd3: result = data[54 +: 18];
      default: begin
        if ({1'b0,word} < data[126 +: 9]) result = data[72 +: 18];
        else if ({1'b0,word} < data[135 +: 9]) result = data[90 +: 18];
        else result = data[108 +: 18];
      end
    endcase
  end
  wire flush = ftz && (result[3 +: 4] == 0 && result[2:0] != 0);
  assign y = flush ? {result[7], {7{1'b0}}} : result[7:0];
  assign flags = result[8 +: 10] | (denormal ? 10'd64 : 10'd0) | (flush ? 10'd24 : 10'd0);
endmodule


// direct_lut independently evaluated control records at 128/256 working bits
module fam_sfu_control_table_3d69fad249f84812_data (
  input logic [7:0] address,
  output logic [143:0] data
);
  logic [143:0] rom1_t [0:255];
  initial begin rom1_t[0]=144'd11172152539333211683588303083900772548089470; rom1_t[1]=144'd11172152373179078382755843993587661950948478; rom1_t[2]=144'd11172150709690626624812122710491949214728312; rom1_t[3]=144'd11164835966087774104892924883469712365195379; rom1_t[4]=144'd11172150707094468291986615537205806861647984; rom1_t[5]=144'd11167728364259483332213233187668275630182509; rom1_t[6]=144'd11164835963491615772067417710183570012115051; rom1_t[7]=144'd11153436503875244541938206264173837982896233; rom1_t[8]=144'd11172150704498309959161108363919664508567656; rom1_t[9]=144'd11155137914736289859445957947228693441548390; rom1_t[10]=144'd11167728361663324999387726014382133277102181; rom1_t[11]=144'd11164155396486135353918172184343331916746852; rom1_t[12]=144'd11164835960895457439241910536897427659034723; rom1_t[13]=144'd11168749207790528439968550948222125199331426; rom1_t[14]=144'd11153436501279086209112699090887695629815905; rom1_t[15]=144'd11161943560127589879096095059412722040967265; rom1_t[16]=144'd11172150701902151626335601190633522155487328; rom1_t[17]=144'd11155137912140131526620450773942551088468062; rom1_t[18]=144'd11167728359067166666562218841095990924021853; rom1_t[19]=144'd11164155393889977021092665011057189563666524; rom1_t[20]=144'd11164835958299299106416403363611285305954395; rom1_t[21]=144'd11168749205194370107143043774935982846251098; rom1_t[22]=144'd11153436498682927876287191917601553276735577; rom1_t[23]=144'd11161943557531431546270587886126579687886937; rom1_t[24]=144'd11172150699305993293510094017347379802407000; rom1_t[25]=144'd11155137909543973193794943600656408735387734; rom1_t[26]=144'd11167728356471008333736711667809848570941525; rom1_t[27]=144'd11164155391293818688267157837771047210586196; rom1_t[28]=144'd11164835955703140773590896190325142952874067; rom1_t[29]=144'd11168749202598211774317536601649840493170770; rom1_t[30]=144'd11153436496086769543461684744315410923655249; rom1_t[31]=144'd11161943554935273213445080712840437334806609; rom1_t[32]=144'd11172150696709834960684586844061237449326672; rom1_t[33]=144'd11155137906947814860969436427370266382307406; rom1_t[34]=144'd11167728353874850000911204494523706217861197; rom1_t[35]=144'd11164155388697660355441650664484904857505868; rom1_t[36]=144'd11164835953106982440765389017039000599793739; rom1_t[37]=144'd11168749200002053441492029428363698140090442; rom1_t[38]=144'd11153436493490611210636177571029268570574921; rom1_t[39]=144'd11161943552339114880619573539554294981726281; rom1_t[40]=144'd11172150694113676627859079670775095096246344; rom1_t[41]=144'd11155137904351656528143929254084124029227078; rom1_t[42]=144'd11167728351278691668085697321237563864780869; rom1_t[43]=144'd11164155386101502022616143491198762504425540; rom1_t[44]=144'd11164835950510824107939881843752858246713411; rom1_t[45]=144'd11168749197405895108666522255077555787010114; rom1_t[46]=144'd11153436490894452877810670397743126217494593; rom1_t[47]=144'd11161943549742956547794066366268152628645953; rom1_t[48]=144'd11172150691517518295033572497488952743166016; rom1_t[49]=144'd11155137901755498195318422080797981676146750; rom1_t[50]=144'd11167728348682533335260190147951421511700541; rom1_t[51]=144'd11164155383505343689790636317912620151345212; rom1_t[52]=144'd11164835947914665775114374670466715893633083; rom1_t[53]=144'd11168749194809736775841015081791413433929786; rom1_t[54]=144'd11153436488298294544985163224456983864414265; rom1_t[55]=144'd11161943547146798214968559192982010275565625; rom1_t[56]=144'd11172150688921359962208065324202810390085688; rom1_t[57]=144'd11155137899159339862492914907511839323066422; rom1_t[58]=144'd11167728346086375002434682974665279158620213; rom1_t[59]=144'd11164155380909185356965129144626477798264884; rom1_t[60]=144'd11164835945318507442288867497180573540552755; rom1_t[61]=144'd11168749192213578443015507908505271080849458; rom1_t[62]=144'd11153436485702136212159656051170841511333937; rom1_t[63]=144'd11161943544550639882143052019695867922485297; rom1_t[64]=144'd11172150686325201629382558150916668037005360; rom1_t[65]=144'd11155137896563181529667407734225696969986094; rom1_t[66]=144'd11167728343490216669609175801379136805539885; rom1_t[67]=144'd11164155378313027024139621971340335445184556; rom1_t[68]=144'd11164835942722349109463360323894431187472427; rom1_t[69]=144'd11168749189617420110190000735219128727769130; rom1_t[70]=144'd11153436483105977879334148877884699158253609; rom1_t[71]=144'd11161943541954481549317544846409725569404969; rom1_t[72]=144'd11172150683729043296557050977630525683925032; rom1_t[73]=144'd11155137893967023196841900560939554616905766; rom1_t[74]=144'd11167728340894058336783668628092994452459557; rom1_t[75]=144'd11164155375716868691314114798054193092104228; rom1_t[76]=144'd11164835940126190776637853150608288834392099; rom1_t[77]=144'd11168749187021261777364493561932986374688802; rom1_t[78]=144'd11153436480509819546508641704598556805173281; rom1_t[79]=144'd11161943539358323216492037673123583216324641; rom1_t[80]=144'd11172150681132884963731543804344383330844704; rom1_t[81]=144'd11155137891370864864016393387653412263825438; rom1_t[82]=144'd11167728338297900003958161454806852099379229; rom1_t[83]=144'd11164155373120710358488607624768050739023900; rom1_t[84]=144'd11164835937530032443812345977322146481311771; rom1_t[85]=144'd11168749184425103444538986388646844021608474; rom1_t[86]=144'd11153436477913661213683134531312414452092953; rom1_t[87]=144'd11161943536762164883666530499837440863244313; rom1_t[88]=144'd11172150678536726630906036631058240977764376; rom1_t[89]=144'd11155137888774706531190886214367269910745110; rom1_t[90]=144'd11167728335701741671132654281520709746298901; rom1_t[91]=144'd11164155370524552025663100451481908385943572; rom1_t[92]=144'd11164835934933874110986838804036004128231443; rom1_t[93]=144'd11168749181828945111713479215360701668528146; rom1_t[94]=144'd11153436475317502880857627358026272099012625; rom1_t[95]=144'd11161943534166006550841023326551298510163985; rom1_t[96]=144'd11172150675940568298080529457772098624684048; rom1_t[97]=144'd11155137886178548198365379041081127557664782; rom1_t[98]=144'd11167728333105583338307147108234567393218573; rom1_t[99]=144'd11164155367928393692837593278195766032863244; rom1_t[100]=144'd11164835932337715778161331630749861775151115; rom1_t[101]=144'd11168749179232786778887972042074559315447818; rom1_t[102]=144'd11153436472721344548032120184740129745932297; rom1_t[103]=144'd11161943531569848218015516153265156157083657; rom1_t[104]=144'd11172150673344409965255022284485956271603720; rom1_t[105]=144'd2441527978778971626566263053202906796529671; rom1_t[106]=144'd8894132361192747448387315649967043712129030; rom1_t[107]=144'd9117017311201443588292676906554358995621894; rom1_t[108]=144'd7411777299968889475321801619681635646838789; rom1_t[109]=144'd10297626982909119795675666710378111011133445; rom1_t[110]=144'd6362261409468466465721739375429711645644805; rom1_t[111]=144'd5929422238745031502256287589396227581548548; rom1_t[112]=144'd11172150672046330798842268697842885095063556; rom1_t[113]=144'd6189738249115030873142620052801037368301572; rom1_t[114]=144'd8889793760040946108168592433739985285027843; rom1_t[115]=144'd10118808598443127049919286560851181227743235; rom1_t[116]=144'd11164836594358090648665660818716161810634755; rom1_t[117]=144'd9418167204952913515708158958768895581231106; rom1_t[118]=144'd3182662972310177879913590250265733889529858; rom1_t[119]=144'd5926529837977163942110472111911521963481090; rom1_t[120]=144'd11172150671397291215635891904521349506793474; rom1_t[121]=144'd8672438397521158319365024395301682650814466; rom1_t[122]=144'd8898470959748390455780531692907959786149890; rom1_t[123]=144'd7065965343287406595414393588236030025406465; rom1_t[124]=144'd7411777298670810308909048033038564470298625; rom1_t[125]=144'd9413148039716309881768885786648509205977089; rom1_t[126]=144'd11153437134741719418536449372706429781415937; rom1_t[127]=144'd11172153453505464629770016477283648626499967; rom1_t[128]=144'd11172152580871745008796417856479050197374718; rom1_t[129]=144'd11172152414717611707963958766165939600233726; rom1_t[130]=144'd11172150751229159950020237483070226864013560; rom1_t[131]=144'd11164836007626307430101039638033660224475379; rom1_t[132]=144'd11172150748633001617194730309784084510933232; rom1_t[133]=144'd11167728405798016657421347942232223489462509; rom1_t[134]=144'd11164836005030149097275532464747517871395051; rom1_t[135]=144'd11153436545413777867146321018737785842176233; rom1_t[136]=144'd11172150746036843284369223136497942157852904; rom1_t[137]=144'd11155137956274823184654072701792641300828390; rom1_t[138]=144'd11167728403201858324595840768946081136382181; rom1_t[139]=144'd11164155438024668679126286938907279776026852; rom1_t[140]=144'd11164836002433990764450025291461375518314723; rom1_t[141]=144'd11168749249329061765176665702786073058611426; rom1_t[142]=144'd11153436542817619534320813845451643489095905; rom1_t[143]=144'd11161943601666123204304209813976669900247265; rom1_t[144]=144'd11172150743440684951543715963211799804772576; rom1_t[145]=144'd11155137953678664851828565528506498947748062; rom1_t[146]=144'd11167728400605699991770333595659938783301853; rom1_t[147]=144'd11164155435428510346300779765621137422946524; rom1_t[148]=144'd11164835999837832431624518118175233165234395; rom1_t[149]=144'd11168749246732903432351158529499930705531098; rom1_t[150]=144'd11153436540221461201495306672165501136015577; rom1_t[151]=144'd11161943599069964871478702640690527547166937; rom1_t[152]=144'd11172150740844526618718208789925657451692248; rom1_t[153]=144'd11155137951082506519003058355220356594667734; rom1_t[154]=144'd11167728398009541658944826422373796430221525; rom1_t[155]=144'd11164155432832352013475272592334995069866196; rom1_t[156]=144'd11164835997241674098799010944889090812154067; rom1_t[157]=144'd11168749244136745099525651356213788352450770; rom1_t[158]=144'd11153436537625302868669799498879358782935249; rom1_t[159]=144'd11161943596473806538653195467404385194086609; rom1_t[160]=144'd11172150738248368285892701616639515098611920; rom1_t[161]=144'd11155137948486348186177551181934214241587406; rom1_t[162]=144'd11167728395413383326119319249087654077141197; rom1_t[163]=144'd11164155430236193680649765419048852716785868; rom1_t[164]=144'd11164835994645515765973503771602948459073739; rom1_t[165]=144'd11168749241540586766700144182927645999370442; rom1_t[166]=144'd11153436535029144535844292325593216429854921; rom1_t[167]=144'd11161943593877648205827688294118242841006281; rom1_t[168]=144'd11172150735652209953067194443353372745531592; rom1_t[169]=144'd11155137945890189853352044008648071888507078; rom1_t[170]=144'd11167728392817224993293812075801511724060869; rom1_t[171]=144'd11164155427640035347824258245762710363705540; rom1_t[172]=144'd11164835992049357433147996598316806105993411; rom1_t[173]=144'd11168749238944428433874637009641503646290114; rom1_t[174]=144'd11153436532432986203018785152307074076774593; rom1_t[175]=144'd11161943591281489873002181120832100487925953; rom1_t[176]=144'd11172150733056051620241687270067230392451264; rom1_t[177]=144'd11155137943294031520526536835361929535426750; rom1_t[178]=144'd11167728390221066660468304902515369370980541; rom1_t[179]=144'd11164155425043877014998751072476568010625212; rom1_t[180]=144'd11164835989453199100322489425030663752913083; rom1_t[181]=144'd11168749236348270101049129836355361293209786; rom1_t[182]=144'd11153436529836827870193277979020931723694265; rom1_t[183]=144'd11161943588685331540176673947545958134845625; rom1_t[184]=144'd11172150730459893287416180096781088039370936; rom1_t[185]=144'd11155137940697873187701029662075787182346422; rom1_t[186]=144'd11167728387624908327642797729229227017900213; rom1_t[187]=144'd11164155422447718682173243899190425657544884; rom1_t[188]=144'd11164835986857040767496982251744521399832755; rom1_t[189]=144'd11168749233752111768223622663069218940129458; rom1_t[190]=144'd11153436527240669537367770805734789370613937; rom1_t[191]=144'd11161943586089173207351166774259815781765297; rom1_t[192]=144'd11172150727863734954590672923494945686290608; rom1_t[193]=144'd11155137938101714854875522488789644829266094; rom1_t[194]=144'd11167728385028749994817290555943084664819885; rom1_t[195]=144'd11164155419851560349347736725904283304464556; rom1_t[196]=144'd11164835984260882434671475078458379046752427; rom1_t[197]=144'd11168749231155953435398115489783076587049130; rom1_t[198]=144'd11153436524644511204542263632448647017533609; rom1_t[199]=144'd11161943583493014874525659600973673428684969; rom1_t[200]=144'd11172150725267576621765165750208803333210280; rom1_t[201]=144'd11155137935505556522050015315503502476185766; rom1_t[202]=144'd11167728382432591661991783382656942311739557; rom1_t[203]=144'd11164155417255402016522229552618140951384228; rom1_t[204]=144'd11164835981664724101845967905172236693672099; rom1_t[205]=144'd11168749228559795102572608316496934233968802; rom1_t[206]=144'd11153436522048352871716756459162504664453281; rom1_t[207]=144'd11161943580896856541700152427687531075604641; rom1_t[208]=144'd11172150722671418288939658576922660980129952; rom1_t[209]=144'd11155137932909398189224508142217360123105438; rom1_t[210]=144'd11167728379836433329166276209370799958659229; rom1_t[211]=144'd11164155414659243683696722379331998598303900; rom1_t[212]=144'd11164835979068565769020460731886094340591771; rom1_t[213]=144'd11168749225963636769747101143210791880888474; rom1_t[214]=144'd11153436519452194538891249285876362311372953; rom1_t[215]=144'd11161943578300698208874645254401388722524313; rom1_t[216]=144'd11172150720075259956114151403636518627049624; rom1_t[217]=144'd11155137930313239856399000968931217770025110; rom1_t[218]=144'd11167728377240274996340769036084657605578901; rom1_t[219]=144'd11164155412063085350871215206045856245223572; rom1_t[220]=144'd11164835976472407436194953558599951987511443; rom1_t[221]=144'd11168749223367478436921593969924649527808146; rom1_t[222]=144'd11153436516856036206065742112590219958292625; rom1_t[223]=144'd11161943575704539876049138081115246369443985; rom1_t[224]=144'd11172150717479101623288644230350376273969296; rom1_t[225]=144'd11155137927717081523573493795645075416944782; rom1_t[226]=144'd11167728374644116663515261862798515252498573; rom1_t[227]=144'd11164155409466927018045708032759713892143244; rom1_t[228]=144'd11164835973876249103369446385313809634431115; rom1_t[229]=144'd11168749220771320104096086796638507174727818; rom1_t[230]=144'd11153436514259877873240234939304077605212297; rom1_t[231]=144'd11161943573108381543223630907829104016363657; rom1_t[232]=144'd11172150714882943290463137057064233920888968; rom1_t[233]=144'd2441528020317504951774377807766854655809671; rom1_t[234]=144'd8894132402731280773595430404530991571409030; rom1_t[235]=144'd9117017352739976913500791661118306854901894; rom1_t[236]=144'd7411777341507422800529916374245583506118789; rom1_t[237]=144'd10297627024447653120883781464942058870413445; rom1_t[238]=144'd6362261451006999790929854129993659504924805; rom1_t[239]=144'd5929422280283564827464402343960175440828548; rom1_t[240]=144'd11172150713584864124050383470421162744348804; rom1_t[241]=144'd6189738290653564198350734807364985227581572; rom1_t[242]=144'd8889793801579479433376707188303933144307843; rom1_t[243]=144'd10118808639981660375127401315415129087023235; rom1_t[244]=144'd11164836635896623973873775573280109669914755; rom1_t[245]=144'd9418167246491446840916273713332843440511106; rom1_t[246]=144'd3182663013848711205121705004829681748809858; rom1_t[247]=144'd5926529879515697267318586866475469822761090; rom1_t[248]=144'd11172150712935824540844006677099627156078722; rom1_t[249]=144'd8672438439059691644573139149865630510094466; rom1_t[250]=144'd8898471001286923780988646447471907645429890; rom1_t[251]=144'd7065965384825939920622508342799977884686465; rom1_t[252]=144'd7411777340209343634117162787602512329578625; rom1_t[253]=144'd9413148081254843206977000541212457065257089; rom1_t[254]=144'd11153437176280252743744564127270377640695937; rom1_t[255]=144'd11172153453505464629770016477283648626499967; end
  logic [143:0] rom1; assign rom1 = rom1_t[address];
  assign data = rom1;
endmodule



module fam_sfu_control_table_4b616625bc5f9d45(input [7:0] x, input [2:0] rnd, input daz, ftz,
    input [7:0] word, output [7:0] y, output [9:0] flags);
  wire denormal = (x[3 +: 4] == 0 && x[2:0] != 0);
  wire [7:0] operand = daz && denormal ? {x[7], {7{1'b0}}} : x;
  wire [143:0] data;
  fam_sfu_control_table_4b616625bc5f9d45_data table_data(.address(operand), .data(data));
  reg [17:0] result;
  always @* begin
    case (rnd)
      3'd0: result = data[0 +: 18];
      3'd1: result = data[18 +: 18];
      3'd2: result = data[36 +: 18];
      3'd3: result = data[54 +: 18];
      default: begin
        if ({1'b0,word} < data[126 +: 9]) result = data[72 +: 18];
        else if ({1'b0,word} < data[135 +: 9]) result = data[90 +: 18];
        else result = data[108 +: 18];
      end
    endcase
  end
  wire flush = ftz && (result[3 +: 4] == 0 && result[2:0] != 0);
  assign y = flush ? {result[7], {7{1'b0}}} : result[7:0];
  assign flags = result[8 +: 10] | (denormal ? 10'd64 : 10'd0) | (flush ? 10'd24 : 10'd0);
endmodule


// direct_lut independently evaluated control records at 128/256 working bits
module fam_sfu_control_table_4b616625bc5f9d45_data (
  input logic [7:0] address,
  output logic [143:0] data
);
  logic [143:0] rom1_t [0:255];
  initial begin rom1_t[0]=144'd11172150688921359962208065324202810390085688; rom1_t[1]=144'd11150544087854946776442536143633046040481848; rom1_t[2]=144'd11150799299630137480290133674588619866640440; rom1_t[3]=144'd11151054511405328184137731205544193692799032; rom1_t[4]=144'd11151309723180518887985328736499767518957624; rom1_t[5]=144'd11151479864363979357217060423803483403063352; rom1_t[6]=144'd11151735076139170061064657954759057229221944; rom1_t[7]=144'd11151990287914360764912255485714631055380536; rom1_t[8]=144'd11152245499689551468759853016670204881539128; rom1_t[9]=144'd11152500711464742172607450547625778707697720; rom1_t[10]=144'd11152670852648202641839182234929494591803448; rom1_t[11]=144'd11152926064423393345686779765885068417962040; rom1_t[12]=144'd11153181276198584049534377296840642244120632; rom1_t[13]=144'd11153436487973774753381974827796216070279224; rom1_t[14]=144'd11153691699748965457229572358751789896437816; rom1_t[15]=144'd11153946911524156161077169889707363722596408; rom1_t[16]=144'd11154117052707616630308901577011079606702136; rom1_t[17]=144'd11154627476257998038004096638922227259019320; rom1_t[18]=144'd11155137899808379445699291700833374911336504; rom1_t[19]=144'd11155563252767030618778620919092664621600824; rom1_t[20]=144'd11156073676317412026473815981003812273918008; rom1_t[21]=144'd11156584099867793434169011042914959926235192; rom1_t[22]=144'd11157094523418174841864206104826107578552376; rom1_t[23]=144'd11157519876376826014943535323085397288816696; rom1_t[24]=144'd11158030299927207422638730384996544941133880; rom1_t[25]=144'd11159051147027970238029120508818840245768248; rom1_t[26]=144'd11159986923537002818803644788989277608349752; rom1_t[27]=144'd11161007770637765634194034912811572912984120; rom1_t[28]=144'd11162028617738528449584425036633868217618489; rom1_t[29]=144'd11163049464839291264974815160456163522252857; rom1_t[30]=144'd11164070311940054080365205284278458826887225; rom1_t[31]=144'd11165091159040816895755595408100754131521593; rom1_t[32]=144'd11166112006141579711145985531923049436155961; rom1_t[33]=144'd11168153700343105341926765779567640045424697; rom1_t[34]=144'd11170280465136361207323411870864088596746297; rom1_t[35]=144'd11150629158771196802661590383945671776669753; rom1_t[36]=144'd11152755923564452668058236475242120327991353; rom1_t[37]=144'd11154882688357708533454882566538568879312953; rom1_t[38]=144'd11157094523742694633467394501486875372687417; rom1_t[39]=144'd11159306359127680733479906436435181866061881; rom1_t[40]=144'd11161518194512666833492418371383488359436346; rom1_t[41]=144'd11166026935874369268133308084931959288238138; rom1_t[42]=144'd11170705818419532172005929485784146101145658; rom1_t[43]=144'd11153691700398005040435949152073325484707898; rom1_t[44]=144'd11158455653534898178924436396577370239668282; rom1_t[45]=144'd11163474818446982021260521172036988820787259; rom1_t[46]=144'd11168493983359065863596605947496607401906235; rom1_t[47]=144'd11151905218296189905105954832045076495732795; rom1_t[48]=144'd11157179594983464451289637138460268903010363; rom1_t[49]=144'd11168068630724934482120465125898085485776956; rom1_t[50]=144'd11157690018858365650588020597032184349462588; rom1_t[51]=144'd11169599901700598496809238708292296236863549; rom1_t[52]=144'd11160242136934792480667184303248690405183549; rom1_t[53]=144'd11151394795719367872220324960116232225820734; rom1_t[54]=144'd11165006090396205410758859944413502954278975; rom1_t[55]=144'd11157349737465004086934122412407055963656255; rom1_t[56]=144'd11172150691517518295033572497488952743166016; rom1_t[57]=144'd11166112008737738043971492705209191789236289; rom1_t[58]=144'd11161518197108825166317925544669630712516674; rom1_t[59]=144'd11158455656131056511749943569863512592748610; rom1_t[60]=144'd11157179597579622784115144311746411256090691; rom1_t[61]=144'd11157690021454523983413527770318326702542916; rom1_t[62]=144'd11160242139530950813492691476534832758263877; rom1_t[63]=144'd11165006092992363743584367117699645307359303; rom1_t[64]=144'd11172150694113676627859079670775095096246344; rom1_t[65]=144'd11161518199704983499143432717955773065597002; rom1_t[66]=144'd11157179600175781116940651485032553609171019; rom1_t[67]=144'd11160242142127109146318198649820975111344205; rom1_t[68]=144'd11172150696709834960684586844061237449326672; rom1_t[69]=144'd11161518202301141831968939891241915418677330; rom1_t[70]=144'd11157179602771939449766158658318695962251347; rom1_t[71]=144'd11160242144723267479143705823107117464424533; rom1_t[72]=144'd11172150699305993293510094017347379802407000; rom1_t[73]=144'd11157179605368097782591665831604838315331675; rom1_t[74]=144'd11172150701902151626335601190633522155487328; rom1_t[75]=144'd11157179607964256115417173004890980668412003; rom1_t[76]=144'd11172150704498309959161108363919664508567656; rom1_t[77]=144'd11157179610560414448242680178177123021492331; rom1_t[78]=144'd11172150707094468291986615537205806861647984; rom1_t[79]=144'd11157179613156572781068187351463265374572659; rom1_t[80]=144'd11172150709690626624812122710491949214728312; rom1_t[81]=144'd11172152373179078382755843993587661950948478; rom1_t[82]=144'd11172152373179078382755843993587661950948478; rom1_t[83]=144'd11172152373179078382755843993587661950948478; rom1_t[84]=144'd11172152373179078382755843993587661950948478; rom1_t[85]=144'd11172152373179078382755843993587661950948478; rom1_t[86]=144'd11172152373179078382755843993587661950948478; rom1_t[87]=144'd11172152373179078382755843993587661950948478; rom1_t[88]=144'd11172152373179078382755843993587661950948478; rom1_t[89]=144'd11172152373179078382755843993587661950948478; rom1_t[90]=144'd11172152373179078382755843993587661950948478; rom1_t[91]=144'd11172152373179078382755843993587661950948478; rom1_t[92]=144'd11172152373179078382755843993587661950948478; rom1_t[93]=144'd11172152373179078382755843993587661950948478; rom1_t[94]=144'd11172152373179078382755843993587661950948478; rom1_t[95]=144'd11172152373179078382755843993587661950948478; rom1_t[96]=144'd11172152373179078382755843993587661950948478; rom1_t[97]=144'd11172152373179078382755843993587661950948478; rom1_t[98]=144'd11172152373179078382755843993587661950948478; rom1_t[99]=144'd11172152373179078382755843993587661950948478; rom1_t[100]=144'd11172152373179078382755843993587661950948478; rom1_t[101]=144'd11172152373179078382755843993587661950948478; rom1_t[102]=144'd11172152373179078382755843993587661950948478; rom1_t[103]=144'd11172152373179078382755843993587661950948478; rom1_t[104]=144'd11172152373179078382755843993587661950948478; rom1_t[105]=144'd11172152373179078382755843993587661950948478; rom1_t[106]=144'd11172152373179078382755843993587661950948478; rom1_t[107]=144'd11172152373179078382755843993587661950948478; rom1_t[108]=144'd11172152373179078382755843993587661950948478; rom1_t[109]=144'd11172152373179078382755843993587661950948478; rom1_t[110]=144'd11172152373179078382755843993587661950948478; rom1_t[111]=144'd11172152373179078382755843993587661950948478; rom1_t[112]=144'd11172152373179078382755843993587661950948478; rom1_t[113]=144'd11172152373179078382755843993587661950948478; rom1_t[114]=144'd11172152373179078382755843993587661950948478; rom1_t[115]=144'd11172152373179078382755843993587661950948478; rom1_t[116]=144'd11172152373179078382755843993587661950948478; rom1_t[117]=144'd11172152373179078382755843993587661950948478; rom1_t[118]=144'd11172152373179078382755843993587661950948478; rom1_t[119]=144'd11172152373179078382755843993587661950948478; rom1_t[120]=144'd11172152373179078382755843993587661950948478; rom1_t[121]=144'd11172152373179078382755843993587661950948478; rom1_t[122]=144'd11172152373179078382755843993587661950948478; rom1_t[123]=144'd11172152373179078382755843993587661950948478; rom1_t[124]=144'd11172152373179078382755843993587661950948478; rom1_t[125]=144'd11172152373179078382755843993587661950948478; rom1_t[126]=144'd11172152373179078382755843993587661950948478; rom1_t[127]=144'd11172153453505464629770016477283648626499967; rom1_t[128]=144'd11172150688921359962208065324202810390085688; rom1_t[129]=144'd11171641594279525169574076972633047875457080; rom1_t[130]=144'd11171131170729143761878881910721900223139896; rom1_t[131]=144'd11170705817770492588799552692462610512875576; rom1_t[132]=144'd11170195394220111181104357630551462860558392; rom1_t[133]=144'd11169770041261460008025028412292173150294072; rom1_t[134]=144'd11169259617711078600329833350381025497976888; rom1_t[135]=144'd11168834264752427427250504132121735787712568; rom1_t[136]=144'd11168323841202046019555309070210588135395384; rom1_t[137]=144'd11167898488243394846475979851951298425131064; rom1_t[138]=144'd11167388064693013438780784790040150772813880; rom1_t[139]=144'd11166962711734362265701455571780861062549560; rom1_t[140]=144'd11166452288183980858006260509869713410232376; rom1_t[141]=144'd11166026935225329684926931291610423699968056; rom1_t[142]=144'd11165601582266678511847602073351133989703736; rom1_t[143]=144'd11165091158716297104152407011439986337386552; rom1_t[144]=144'd11164665805757645931073077793180696627122232; rom1_t[145]=144'd11163730029248613350298553513010259264540728; rom1_t[146]=144'd11162794252739580769524029232839821901959224; rom1_t[147]=144'd11161858476230548188749504952669384539377720; rom1_t[148]=144'd11161007770313245842590846516150805118849079; rom1_t[149]=144'd11160071993804213261816322235980367756267575; rom1_t[150]=144'd11159136217295180681041797955809930393686071; rom1_t[151]=144'd11158200440786148100267273675639493031104567; rom1_t[152]=144'd11157349734868845754108615239120913610575927; rom1_t[153]=144'd11155563252442510827175432522431896827465783; rom1_t[154]=144'd11153776770016175900242249805742880044355639; rom1_t[155]=144'd11151990287589840973309067089053863261245495; rom1_t[156]=144'd11171981876321926316434351950579711849533495; rom1_t[157]=144'd11170195393895591389501169233890695066423351; rom1_t[158]=144'd11168408911469256462567986517201678283313207; rom1_t[159]=144'd11166707499634651770250669644164519442255927; rom1_t[160]=144'd11165006087800047077933352771127360601198647; rom1_t[161]=144'd11161518193539107458682853181401184977031223; rom1_t[162]=144'd11158115369869898074048219435326867294916662; rom1_t[163]=144'd11154712546200688689413585689252549612802102; rom1_t[164]=144'd11151394793123209539394817786830089872740406; rom1_t[165]=144'd11169940181795880894050383306274353446129718; rom1_t[166]=144'd11166622428718401744031615403851893706068022; rom1_t[167]=144'd11163389746232652828628713345081291908059190; rom1_t[168]=144'd11160242134338634147841677129962548052103221; rom1_t[169]=144'd11153946910550596786267604699725060340191285; rom1_t[170]=144'd11169599899104440163983731535006153883783221; rom1_t[171]=144'd11163559887091593506257256635724239998029877; rom1_t[172]=144'd11157690016262207317762513423746041996382260; rom1_t[173]=144'd11151905216024551363883636055419701936787508; rom1_t[174]=144'd11168068628128776149294957952611943132696628; rom1_t[175]=144'd11162539039666310899263678115241176899260468; rom1_t[176]=144'd11157179592387306118464129965174126549930035; rom1_t[177]=144'd11168493980762907530771098774210465048825907; rom1_t[178]=144'd11158455650938739846098929223291227886587954; rom1_t[179]=144'd11170705815823373839180422312498003748065330; rom1_t[180]=144'd11161518191916508500666911198097346006356018; rom1_t[181]=144'd11152755920968294335232729301955977974911025; rom1_t[182]=144'd11166112003545421378320478358636907083075633; rom1_t[183]=144'd11158030297331049089813223211710402588053552; rom1_t[184]=144'd11172150686325201629382558150916668037005360; rom1_t[185]=144'd11165006085203888745107845597841218248118319; rom1_t[186]=144'd11160242131742475815016169956676405699022893; rom1_t[187]=144'd11157690013666048984937006250459899643301932; rom1_t[188]=144'd11157179589791147785638622791887984196849707; rom1_t[189]=144'd11158455648342581513273422050005085533507626; rom1_t[190]=144'd11161518189320350167841404024811203653275690; rom1_t[191]=144'd11166112000949263045494971185350764729995305; rom1_t[192]=144'd11172150683729043296557050977630525683925032; rom1_t[193]=144'd11160242129146317482190662783390263345942565; rom1_t[194]=144'd11157179587194989452813115618601841843769379; rom1_t[195]=144'd11161518186724191835015896851525061300195362; rom1_t[196]=144'd11172150681132884963731543804344383330844704; rom1_t[197]=144'd11160242126550159149365155610104120992862237; rom1_t[198]=144'd11157179584598831119987608445315699490689051; rom1_t[199]=144'd11161518184128033502190389678238918947115034; rom1_t[200]=144'd11172150678536726630906036631058240977764376; rom1_t[201]=144'd11157179582002672787162101272029557137608723; rom1_t[202]=144'd11172150675940568298080529457772098624684048; rom1_t[203]=144'd11157179579406514454336594098743414784528395; rom1_t[204]=144'd11172150673344409965255022284485956271603720; rom1_t[205]=144'd7324239661078479293535887787300088173565958; rom1_t[206]=144'd11172150672046330798842268697842885095063556; rom1_t[207]=144'd9240709950603645344952048386373503358081027; rom1_t[208]=144'd11172150671397291215635891904521349506793474; rom1_t[209]=144'd11172150671072771424032703507860581712658433; rom1_t[210]=144'd11161263628856381211592918592016592656144384; rom1_t[211]=144'd11155819110985646196177504598297684364761088; rom1_t[212]=144'd11153096852050278688469797601438230219069440; rom1_t[213]=144'd11151735722582594934615944103008503146223616; rom1_t[214]=144'd11151055157848753057689017353793639609800704; rom1_t[215]=144'd11150714875481832119225553979186207841589248; rom1_t[216]=144'd11150544734298371649993822291882491957483520; rom1_t[217]=144'd11172152664597851242419024212971539593697280; rom1_t[218]=144'd11172152664597851242419024212971539593697280; rom1_t[219]=144'd11172152664597851242419024212971539593697280; rom1_t[220]=144'd11172152664597851242419024212971539593697280; rom1_t[221]=144'd11172152664597851242419024212971539593697280; rom1_t[222]=144'd11172152664597851242419024212971539593697280; rom1_t[223]=144'd11172152664597851242419024212971539593697280; rom1_t[224]=144'd11172152664597851242419024212971539593697280; rom1_t[225]=144'd11172152664597851242419024212971539593697280; rom1_t[226]=144'd11172152664597851242419024212971539593697280; rom1_t[227]=144'd11172152664597851242419024212971539593697280; rom1_t[228]=144'd11172152664597851242419024212971539593697280; rom1_t[229]=144'd11172152664597851242419024212971539593697280; rom1_t[230]=144'd11172152664597851242419024212971539593697280; rom1_t[231]=144'd11172152664597851242419024212971539593697280; rom1_t[232]=144'd11172152664597851242419024212971539593697280; rom1_t[233]=144'd11172152664597851242419024212971539593697280; rom1_t[234]=144'd11172152664597851242419024212971539593697280; rom1_t[235]=144'd11172152664597851242419024212971539593697280; rom1_t[236]=144'd11172152664597851242419024212971539593697280; rom1_t[237]=144'd11172152664597851242419024212971539593697280; rom1_t[238]=144'd11172152664597851242419024212971539593697280; rom1_t[239]=144'd11172152664597851242419024212971539593697280; rom1_t[240]=144'd11172152664597851242419024212971539593697280; rom1_t[241]=144'd11172152664597851242419024212971539593697280; rom1_t[242]=144'd11172152664597851242419024212971539593697280; rom1_t[243]=144'd11172152664597851242419024212971539593697280; rom1_t[244]=144'd11172152664597851242419024212971539593697280; rom1_t[245]=144'd11172152664597851242419024212971539593697280; rom1_t[246]=144'd11172152664597851242419024212971539593697280; rom1_t[247]=144'd11172152664597851242419024212971539593697280; rom1_t[248]=144'd11172152664597851242419024212971539593697280; rom1_t[249]=144'd11172152664597851242419024212971539593697280; rom1_t[250]=144'd11172152664597851242419024212971539593697280; rom1_t[251]=144'd11172152664597851242419024212971539593697280; rom1_t[252]=144'd11172152664597851242419024212971539593697280; rom1_t[253]=144'd11172152664597851242419024212971539593697280; rom1_t[254]=144'd11172152664597851242419024212971539593697280; rom1_t[255]=144'd11172153453505464629770016477283648626499967; end
  logic [143:0] rom1; assign rom1 = rom1_t[address];
  assign data = rom1;
endmodule



module fam_sfu_control_table_f0aa8ac8e4624d36(input [7:0] x, input [2:0] rnd, input daz, ftz,
    input [7:0] word, output [7:0] y, output [9:0] flags);
  wire denormal = (x[3 +: 4] == 0 && x[2:0] != 0);
  wire [7:0] operand = daz && denormal ? {x[7], {7{1'b0}}} : x;
  wire [143:0] data;
  fam_sfu_control_table_f0aa8ac8e4624d36_data table_data(.address(operand), .data(data));
  reg [17:0] result;
  always @* begin
    case (rnd)
      3'd0: result = data[0 +: 18];
      3'd1: result = data[18 +: 18];
      3'd2: result = data[36 +: 18];
      3'd3: result = data[54 +: 18];
      default: begin
        if ({1'b0,word} < data[126 +: 9]) result = data[72 +: 18];
        else if ({1'b0,word} < data[135 +: 9]) result = data[90 +: 18];
        else result = data[108 +: 18];
      end
    endcase
  end
  wire flush = ftz && (result[3 +: 4] == 0 && result[2:0] != 0);
  assign y = flush ? {result[7], {7{1'b0}}} : result[7:0];
  assign flags = result[8 +: 10] | (denormal ? 10'd64 : 10'd0) | (flush ? 10'd24 : 10'd0);
endmodule


// direct_lut independently evaluated control records at 128/256 working bits
module fam_sfu_control_table_f0aa8ac8e4624d36_data (
  input logic [7:0] address,
  output logic [143:0] data
);
  logic [143:0] rom1_t [0:255];
  initial begin rom1_t[0]=144'd11172152539333211683588303083900772548089470; rom1_t[1]=144'd11157179605368097782591665831604838315331675; rom1_t[2]=144'd11172150699305993293510094017347379802407000; rom1_t[3]=144'd11151735085550244017557121457921323259138133; rom1_t[4]=144'd11157179602771939449766158658318695962251347; rom1_t[5]=144'd11152926072860907927369678079065031065473106; rom1_t[6]=144'd11155478190288295174242464991960001532923985; rom1_t[7]=144'd11162368907893924386524409931099727045070929; rom1_t[8]=144'd11172150696709834960684586844061237449326672; rom1_t[9]=144'd11152160436561776441017320296216006204592207; rom1_t[10]=144'd11157094530557610257134350831362999049523278; rom1_t[11]=144'd11164410601121890642495624988762014271934542; rom1_t[12]=144'd11151735082954085684731614284635180906057805; rom1_t[13]=144'd11162368906595845220111656344456655868530765; rom1_t[14]=144'd11152415647363407770055352637189276648345676; rom1_t[15]=144'd11165261306390153405447906631959058104193100; rom1_t[16]=144'd11157179600175781116940651485032553609171019; rom1_t[17]=144'd11164835953106982440765389017039000599793739; rom1_t[18]=144'd11152926070264749594544170905778888712392778; rom1_t[19]=144'd11164410599823811476082871402118943095394378; rom1_t[20]=144'd11155478187692136841416957818673859179843657; rom1_t[21]=144'd11169429764411375526815767780917793882378313; rom1_t[22]=144'd11162368905297766053698902757813584691990601; rom1_t[23]=144'd11156073681509728692124830327576096980078664; rom1_t[24]=144'd11172150694113676627859079670775095096246344; rom1_t[25]=144'd11152160433965618108191813122929863851511879; rom1_t[26]=144'd11157094527961451924308843658076856696442950; rom1_t[27]=144'd11164410598525732309670117815475871918854214; rom1_t[28]=144'd11151735080357927351906107111349038552977477; rom1_t[29]=144'd11162368903999686887286149171170513515450437; rom1_t[30]=144'd11152415644767249437229845463903134295265348; rom1_t[31]=144'd11165261303793995072622399458672915751112772; rom1_t[32]=144'd11157179597579622784115144311746411256090691; rom1_t[33]=144'd11164835950510824107939881843752858246713411; rom1_t[34]=144'd11152926067668591261718663732492746359312450; rom1_t[35]=144'd11164410597227653143257364228832800742314050; rom1_t[36]=144'd11155478185095978508591450645387716826763329; rom1_t[37]=144'd11169429761815217193990260607631651529297985; rom1_t[38]=144'd11162368902701607720873395584527442338910273; rom1_t[39]=144'd11156073678913570359299323154289954626998336; rom1_t[40]=144'd11172150691517518295033572497488952743166016; rom1_t[41]=144'd11152160431369459775366305949643721498431551; rom1_t[42]=144'd11157094525365293591483336484790714343362622; rom1_t[43]=144'd11164410595929573976844610642189729565773886; rom1_t[44]=144'd11151735077761769019080599938062896199897149; rom1_t[45]=144'd11162368901403528554460641997884371162370109; rom1_t[46]=144'd11152415642171091104404338290616991942185020; rom1_t[47]=144'd11165261301197836739796892285386773398032444; rom1_t[48]=144'd11157179594983464451289637138460268903010363; rom1_t[49]=144'd11164835947914665775114374670466715893633083; rom1_t[50]=144'd11152926065072432928893156559206604006232122; rom1_t[51]=144'd11164410594631494810431857055546658389233722; rom1_t[52]=144'd11155478182499820175765943472101574473683001; rom1_t[53]=144'd11169429759219058861164753434345509176217657; rom1_t[54]=144'd11162368900105449388047888411241299985829945; rom1_t[55]=144'd11156073676317412026473815981003812273918008; rom1_t[56]=144'd11172150688921359962208065324202810390085688; rom1_t[57]=144'd11152160428773301442540798776357579145351223; rom1_t[58]=144'd11157094522769135258657829311504571990282294; rom1_t[59]=144'd11164410593333415644019103468903587212693558; rom1_t[60]=144'd11151735075165610686255092764776753846816821; rom1_t[61]=144'd11162368898807370221635134824598228809289781; rom1_t[62]=144'd11152415639574932771578831117330849589104692; rom1_t[63]=144'd11165261298601678406971385112100631044952116; rom1_t[64]=144'd11157179592387306118464129965174126549930035; rom1_t[65]=144'd11164835945318507442288867497180573540552755; rom1_t[66]=144'd11152926062476274596067649385920461653151794; rom1_t[67]=144'd11164410592035336477606349882260516036153394; rom1_t[68]=144'd11155478179903661842940436298815432120602673; rom1_t[69]=144'd11169429756622900528339246261059366823137329; rom1_t[70]=144'd11162368897509291055222381237955157632749617; rom1_t[71]=144'd11156073673721253693648308807717669920837680; rom1_t[72]=144'd11172150686325201629382558150916668037005360; rom1_t[73]=144'd11152160426177143109715291603071436792270895; rom1_t[74]=144'd11157094520172976925832322138218429637201966; rom1_t[75]=144'd11164410590737257311193596295617444859613230; rom1_t[76]=144'd11151735072569452353429585591490611493736493; rom1_t[77]=144'd11162368896211211888809627651312086456209453; rom1_t[78]=144'd11152415636978774438753323944044707236024364; rom1_t[79]=144'd11165261296005520074145877938814488691871788; rom1_t[80]=144'd11157179589791147785638622791887984196849707; rom1_t[81]=144'd11164835942722349109463360323894431187472427; rom1_t[82]=144'd11152926059880116263242142212634319300071466; rom1_t[83]=144'd11164410589439178144780842708974373683073066; rom1_t[84]=144'd11155478177307503510114929125529289767522345; rom1_t[85]=144'd11169429754026742195513739087773224470057001; rom1_t[86]=144'd11162368894913132722396874064669015279669289; rom1_t[87]=144'd11156073671125095360822801634431527567757352; rom1_t[88]=144'd11172150683729043296557050977630525683925032; rom1_t[89]=144'd11152160423580984776889784429785294439190567; rom1_t[90]=144'd11157094517576818593006814964932287284121638; rom1_t[91]=144'd11164410588141098978368089122331302506532902; rom1_t[92]=144'd11151735069973294020604078418204469140656165; rom1_t[93]=144'd11162368893615053555984120478025944103129125; rom1_t[94]=144'd11152415634382616105927816770758564882944036; rom1_t[95]=144'd11165261293409361741320370765528346338791460; rom1_t[96]=144'd11157179587194989452813115618601841843769379; rom1_t[97]=144'd11164835940126190776637853150608288834392099; rom1_t[98]=144'd11152926057283957930416635039348176946991138; rom1_t[99]=144'd11164410586843019811955335535688231329992738; rom1_t[100]=144'd11155478174711345177289421952243147414442017; rom1_t[101]=144'd11169429751430583862688231914487082116976673; rom1_t[102]=144'd11162368892316974389571366891382872926588961; rom1_t[103]=144'd11156073668528937027997294461145385214677024; rom1_t[104]=144'd11172150681132884963731543804344383330844704; rom1_t[105]=144'd11152160420984826444064277256499152086110239; rom1_t[106]=144'd11157094514980660260181307791646144931041310; rom1_t[107]=144'd11164410585544940645542581949045160153452574; rom1_t[108]=144'd11151735067377135687778571244918326787575837; rom1_t[109]=144'd11162368891018895223158613304739801750048797; rom1_t[110]=144'd11152415631786457773102309597472422529863708; rom1_t[111]=144'd11165261290813203408494863592242203985711132; rom1_t[112]=144'd11157179584598831119987608445315699490689051; rom1_t[113]=144'd11164835937530032443812345977322146481311771; rom1_t[114]=144'd11152926054687799597591127866062034593910810; rom1_t[115]=144'd11164410584246861479129828362402088976912410; rom1_t[116]=144'd11155478172115186844463914778957005061361689; rom1_t[117]=144'd11169429748834425529862724741200939763896345; rom1_t[118]=144'd11162368889720816056745859718096730573508633; rom1_t[119]=144'd11156073665932778695171787287859242861596696; rom1_t[120]=144'd11172150678536726630906036631058240977764376; rom1_t[121]=144'd11152160418388668111238770083213009733029911; rom1_t[122]=144'd11157094512384501927355800618360002577960982; rom1_t[123]=144'd11164410582948782312717074775759017800372246; rom1_t[124]=144'd11151735064780977354953064071632184434495509; rom1_t[125]=144'd11162368888422736890333106131453659396968469; rom1_t[126]=144'd11152415629190299440276802424186280176783380; rom1_t[127]=144'd11172153453505464629770016477283648626499967; rom1_t[128]=144'd11172152580871745008796417856479050197374718; rom1_t[129]=144'd11172153453505464629770016477283648626499967; rom1_t[130]=144'd11172153453505464629770016477283648626499967; rom1_t[131]=144'd11172153453505464629770016477283648626499967; rom1_t[132]=144'd11172153453505464629770016477283648626499967; rom1_t[133]=144'd11172153453505464629770016477283648626499967; rom1_t[134]=144'd11172153453505464629770016477283648626499967; rom1_t[135]=144'd11172153453505464629770016477283648626499967; rom1_t[136]=144'd11172153453505464629770016477283648626499967; rom1_t[137]=144'd11172153453505464629770016477283648626499967; rom1_t[138]=144'd11172153453505464629770016477283648626499967; rom1_t[139]=144'd11172153453505464629770016477283648626499967; rom1_t[140]=144'd11172153453505464629770016477283648626499967; rom1_t[141]=144'd11172153453505464629770016477283648626499967; rom1_t[142]=144'd11172153453505464629770016477283648626499967; rom1_t[143]=144'd11172153453505464629770016477283648626499967; rom1_t[144]=144'd11172153453505464629770016477283648626499967; rom1_t[145]=144'd11172153453505464629770016477283648626499967; rom1_t[146]=144'd11172153453505464629770016477283648626499967; rom1_t[147]=144'd11172153453505464629770016477283648626499967; rom1_t[148]=144'd11172153453505464629770016477283648626499967; rom1_t[149]=144'd11172153453505464629770016477283648626499967; rom1_t[150]=144'd11172153453505464629770016477283648626499967; rom1_t[151]=144'd11172153453505464629770016477283648626499967; rom1_t[152]=144'd11172153453505464629770016477283648626499967; rom1_t[153]=144'd11172153453505464629770016477283648626499967; rom1_t[154]=144'd11172153453505464629770016477283648626499967; rom1_t[155]=144'd11172153453505464629770016477283648626499967; rom1_t[156]=144'd11172153453505464629770016477283648626499967; rom1_t[157]=144'd11172153453505464629770016477283648626499967; rom1_t[158]=144'd11172153453505464629770016477283648626499967; rom1_t[159]=144'd11172153453505464629770016477283648626499967; rom1_t[160]=144'd11172153453505464629770016477283648626499967; rom1_t[161]=144'd11172153453505464629770016477283648626499967; rom1_t[162]=144'd11172153453505464629770016477283648626499967; rom1_t[163]=144'd11172153453505464629770016477283648626499967; rom1_t[164]=144'd11172153453505464629770016477283648626499967; rom1_t[165]=144'd11172153453505464629770016477283648626499967; rom1_t[166]=144'd11172153453505464629770016477283648626499967; rom1_t[167]=144'd11172153453505464629770016477283648626499967; rom1_t[168]=144'd11172153453505464629770016477283648626499967; rom1_t[169]=144'd11172153453505464629770016477283648626499967; rom1_t[170]=144'd11172153453505464629770016477283648626499967; rom1_t[171]=144'd11172153453505464629770016477283648626499967; rom1_t[172]=144'd11172153453505464629770016477283648626499967; rom1_t[173]=144'd11172153453505464629770016477283648626499967; rom1_t[174]=144'd11172153453505464629770016477283648626499967; rom1_t[175]=144'd11172153453505464629770016477283648626499967; rom1_t[176]=144'd11172153453505464629770016477283648626499967; rom1_t[177]=144'd11172153453505464629770016477283648626499967; rom1_t[178]=144'd11172153453505464629770016477283648626499967; rom1_t[179]=144'd11172153453505464629770016477283648626499967; rom1_t[180]=144'd11172153453505464629770016477283648626499967; rom1_t[181]=144'd11172153453505464629770016477283648626499967; rom1_t[182]=144'd11172153453505464629770016477283648626499967; rom1_t[183]=144'd11172153453505464629770016477283648626499967; rom1_t[184]=144'd11172153453505464629770016477283648626499967; rom1_t[185]=144'd11172153453505464629770016477283648626499967; rom1_t[186]=144'd11172153453505464629770016477283648626499967; rom1_t[187]=144'd11172153453505464629770016477283648626499967; rom1_t[188]=144'd11172153453505464629770016477283648626499967; rom1_t[189]=144'd11172153453505464629770016477283648626499967; rom1_t[190]=144'd11172153453505464629770016477283648626499967; rom1_t[191]=144'd11172153453505464629770016477283648626499967; rom1_t[192]=144'd11172153453505464629770016477283648626499967; rom1_t[193]=144'd11172153453505464629770016477283648626499967; rom1_t[194]=144'd11172153453505464629770016477283648626499967; rom1_t[195]=144'd11172153453505464629770016477283648626499967; rom1_t[196]=144'd11172153453505464629770016477283648626499967; rom1_t[197]=144'd11172153453505464629770016477283648626499967; rom1_t[198]=144'd11172153453505464629770016477283648626499967; rom1_t[199]=144'd11172153453505464629770016477283648626499967; rom1_t[200]=144'd11172153453505464629770016477283648626499967; rom1_t[201]=144'd11172153453505464629770016477283648626499967; rom1_t[202]=144'd11172153453505464629770016477283648626499967; rom1_t[203]=144'd11172153453505464629770016477283648626499967; rom1_t[204]=144'd11172153453505464629770016477283648626499967; rom1_t[205]=144'd11172153453505464629770016477283648626499967; rom1_t[206]=144'd11172153453505464629770016477283648626499967; rom1_t[207]=144'd11172153453505464629770016477283648626499967; rom1_t[208]=144'd11172153453505464629770016477283648626499967; rom1_t[209]=144'd11172153453505464629770016477283648626499967; rom1_t[210]=144'd11172153453505464629770016477283648626499967; rom1_t[211]=144'd11172153453505464629770016477283648626499967; rom1_t[212]=144'd11172153453505464629770016477283648626499967; rom1_t[213]=144'd11172153453505464629770016477283648626499967; rom1_t[214]=144'd11172153453505464629770016477283648626499967; rom1_t[215]=144'd11172153453505464629770016477283648626499967; rom1_t[216]=144'd11172153453505464629770016477283648626499967; rom1_t[217]=144'd11172153453505464629770016477283648626499967; rom1_t[218]=144'd11172153453505464629770016477283648626499967; rom1_t[219]=144'd11172153453505464629770016477283648626499967; rom1_t[220]=144'd11172153453505464629770016477283648626499967; rom1_t[221]=144'd11172153453505464629770016477283648626499967; rom1_t[222]=144'd11172153453505464629770016477283648626499967; rom1_t[223]=144'd11172153453505464629770016477283648626499967; rom1_t[224]=144'd11172153453505464629770016477283648626499967; rom1_t[225]=144'd11172153453505464629770016477283648626499967; rom1_t[226]=144'd11172153453505464629770016477283648626499967; rom1_t[227]=144'd11172153453505464629770016477283648626499967; rom1_t[228]=144'd11172153453505464629770016477283648626499967; rom1_t[229]=144'd11172153453505464629770016477283648626499967; rom1_t[230]=144'd11172153453505464629770016477283648626499967; rom1_t[231]=144'd11172153453505464629770016477283648626499967; rom1_t[232]=144'd11172153453505464629770016477283648626499967; rom1_t[233]=144'd11172153453505464629770016477283648626499967; rom1_t[234]=144'd11172153453505464629770016477283648626499967; rom1_t[235]=144'd11172153453505464629770016477283648626499967; rom1_t[236]=144'd11172153453505464629770016477283648626499967; rom1_t[237]=144'd11172153453505464629770016477283648626499967; rom1_t[238]=144'd11172153453505464629770016477283648626499967; rom1_t[239]=144'd11172153453505464629770016477283648626499967; rom1_t[240]=144'd11172153453505464629770016477283648626499967; rom1_t[241]=144'd11172153453505464629770016477283648626499967; rom1_t[242]=144'd11172153453505464629770016477283648626499967; rom1_t[243]=144'd11172153453505464629770016477283648626499967; rom1_t[244]=144'd11172153453505464629770016477283648626499967; rom1_t[245]=144'd11172153453505464629770016477283648626499967; rom1_t[246]=144'd11172153453505464629770016477283648626499967; rom1_t[247]=144'd11172153453505464629770016477283648626499967; rom1_t[248]=144'd11172153453505464629770016477283648626499967; rom1_t[249]=144'd11172153453505464629770016477283648626499967; rom1_t[250]=144'd11172153453505464629770016477283648626499967; rom1_t[251]=144'd11172153453505464629770016477283648626499967; rom1_t[252]=144'd11172153453505464629770016477283648626499967; rom1_t[253]=144'd11172153453505464629770016477283648626499967; rom1_t[254]=144'd11172153453505464629770016477283648626499967; rom1_t[255]=144'd11172153453505464629770016477283648626499967; end
  logic [143:0] rom1; assign rom1 = rom1_t[address];
  assign data = rom1;
endmodule

