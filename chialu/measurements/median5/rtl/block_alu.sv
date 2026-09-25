// ADIR-MEMBER packages
// alu_core_m0_pkg: the exact-arithmetic functions of mode 0 (1xblksfps0e8m0Nefp4e2m1s8)
package alu_core_m0_pkg;

  // ---- m0: V = {special[1:0], sign, exp[16] (signed), sig[3]}
  //           X = {special[1:0], sign, exp[16] (signed), sig[10], sticky}
  localparam int m0_SW = 3, m0_EW = 16, m0_XW = 10;
  localparam int m0_VW = 22, m0_XT = 30;
  function automatic [21:0] m0_mkv(input [1:0] sp, input s, input signed [15:0] e, input [2:0] sig);
    m0_mkv = {sp, s, e, sig};
  endfunction
  function automatic [29:0] m0_mkx(input [1:0] sp, input s, input signed [15:0] e, input [9:0] sig, input st);
    m0_mkx = {sp, s, e, sig, st};
  endfunction
  function automatic [29:0] m0_x(input [21:0] v);   // widen V to X
    m0_x = {v[21:21-1], v[21-2], v[21-3 -: 16], {{(10-3){1'b0}}, v[2:0]}, 1'b0};
  endfunction
  // normalize: leading one at bit XW-1 (zero stays zero)
  function automatic [29:0] m0_norm(input [29:0] x);
    logic [9:0] s; logic signed [15:0] e; integer k;
    s = x[10:1]; e = x[10+16:10+1];
    if (s != 0) begin
      for (k = 8; k >= 1; k = k / 2) begin
        if (k < 10) begin
          if (s[9 -: 1] == 1'b0 && (s >> (10 - k)) == 0) begin
            s = s << k; e = e - k;
          end
        end
      end
    end
    m0_norm = {x[29:29-1], x[29-2], e, s, x[0]};
  endfunction

  function automatic m0_rup(input [2:0] rnd, input s, input inexact, input [10:0] rest, input [10:0] halfv,
                             input st, input lsb, input [10+8:0] fint, input [7:0] word);
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
    logic signed [15:0] ea, eb, d; logic [10:0] ms, mb, r; logic st, stb; integer sh;
    na = m0_norm(a); nb = m0_norm(b);
    spa = na[29:29-1]; spb = nb[29:29-1];
    sa = na[29-2]; sb = nb[29-2] ^ sub;
    if (spa == 2'd1 || spb == 2'd1) m0_add = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 && spb == 2'd2) m0_add = (sa == sb) ? m0_mkx(2'd2, sa, 0, 0, 1'b0) : m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m0_add = m0_mkx(2'd2, sa, 0, 0, 1'b0);
    else if (spb == 2'd2) m0_add = m0_mkx(2'd2, sb, 0, 0, 1'b0);
    else if (na[10:1] == 0 && !na[0]) m0_add = {nb[29:29-1], sb, nb[29-3:0]};
    else if (nb[10:1] == 0 && !nb[0]) m0_add = na;
    else begin
      ea = na[10+16:10+1]; eb = nb[10+16:10+1];
      // order by magnitude (both normalized): larger exponent, then sig
      if (ea > eb || (ea == eb && na[10:1] >= nb[10:1])) begin big = na; sml = nb; sw = 1'b0; end
      else begin big = nb; sml = na; sw = 1'b1; end
      d = big[10+16:10+1] - sml[10+16:10+1];
      ms = {1'b0, sml[10:1]}; stb = sml[0];
      if (d > 10 + 1) begin stb = stb | (ms != 0); ms = 0; end
      else begin
        for (sh = 0; sh < 10 + 2; sh = sh + 1) begin
          if (sh < d) begin stb = stb | ms[0]; ms = ms >> 1; end
        end
      end
      mb = {1'b0, big[10:1]}; st = big[0] | stb;
      if ((sw ? sb : sa) == (sw ? sa : sb)) begin
        r = mb + ms;
        sr = sw ? sb : sa;
      end else begin
        // subtract: the sticky of the smaller operand borrows one lsb
        r = mb - ms - (stb ? 1'b1 : 1'b0);
        sr = sw ? sb : sa;
        if (r == 0 && !st) sr = 1'b0;
      end
      if (r[10]) begin st = st | r[0]; r = r >> 1; m0_add = m0_mkx(2'd0, sr, big[10+16:10+1] + 1, r[9:0], st); end
      else m0_add = m0_mkx(2'd0, sr, big[10+16:10+1], r[9:0], st);
    end
  endfunction
  function automatic [29:0] m0_mul(input [29:0] a, input [29:0] b);
    logic [29:0] na, nb; logic [1:0] spa, spb; logic s; logic [2*10-1:0] pr; logic st; integer k;
    na = m0_norm(a); nb = m0_norm(b);
    spa = na[29:29-1]; spb = nb[29:29-1]; s = na[29-2] ^ nb[29-2];
    if (spa == 2'd1 || spb == 2'd1) m0_mul = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 || spb == 2'd2) begin
      if ((spa == 2'd0 && na[10:1] == 0 && !na[0]) || (spb == 2'd0 && nb[10:1] == 0 && !nb[0]))
        m0_mul = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
      else m0_mul = m0_mkx(2'd2, s, 0, 0, 1'b0);
    end else begin
      pr = na[10:1] * nb[10:1];
      st = na[0] | nb[0];
      // keep the top XW bits of the product, the rest folds into sticky
      st = st | (pr[9:0] != 0);
      m0_mul = m0_mkx(2'd0, s, na[10+16:10+1] + nb[10+16:10+1] + 10, pr[2*10-1:10], st);
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
  function automatic [2*10+1:0] m0_udiv(input [9:0] a, input [9:0] dv);
    logic [10+1:0] r; logic [10:0] q; logic ge; integer i;
    r = {2'b0, a}; q = 0;
    for (i = 10; i >= 0; i = i - 1) begin
      ge = (r >= {2'b0, dv});
      r = ge ? r - {2'b0, dv} : r;
      q = {q[9:0], ge};
      if (i > 0) r = {r[10:0], 1'b0};
    end
    m0_udiv = {q, r[10:0]};
  endfunction
  // the exact product: {special[1:0], sign, exp[EW], sig[2XW]} (no sticky)
  function automatic [2*10+16+2:0] m0_mulx(input [29:0] a, input [29:0] b);
    logic [29:0] na, nb; logic [1:0] spa, spb, sp; logic s; logic [2*10-1:0] pr;
    na = m0_norm(a); nb = m0_norm(b);
    pr = na[10:1] * nb[10:1];
    spa = na[29:29-1]; spb = nb[29:29-1]; s = na[29-2] ^ nb[29-2];
    if (spa == 2'd1 || spb == 2'd1) sp = 2'd1;
    else if (spa == 2'd2 || spb == 2'd2)
      sp = ((spa == 2'd0 && na[10:1] == 0) || (spb == 2'd0 && nb[10:1] == 0)) ? 2'd1 : 2'd2;
    else sp = 2'd0;
    m0_mulx = {sp, s, na[10+16:10+1] + nb[10+16:10+1], pr};
  endfunction
  function automatic [29:0] m0_div(input [29:0] a, input [29:0] b);
    logic [29:0] na, nb; logic [1:0] spa, spb; logic s; logic [2*10+1:0] qr; logic [10:0] q, r;
    na = m0_norm(a); nb = m0_norm(b);
    spa = na[29:29-1]; spb = nb[29:29-1]; s = na[29-2] ^ nb[29-2];
    if (spa == 2'd1 || spb == 2'd1) m0_div = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 && spb == 2'd2) m0_div = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m0_div = m0_mkx(2'd2, s, 0, 0, 1'b0);
    else if (spb == 2'd2) m0_div = m0_mkx(2'd0, s, 0, 0, 1'b0);
    else if (nb[10:1] == 0 && !nb[0]) begin
      if (na[10:1] == 0 && !na[0]) m0_div = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
      else m0_div = m0_mkx(2'd2, s, 0, 0, 1'b0);
    end else if (na[10:1] == 0 && !na[0]) m0_div = m0_mkx(2'd0, s, 0, 0, 1'b0);
    else begin
      qr = m0_udiv(na[10:1], nb[10:1]);     // both normalized: nonzero finite
      q = qr[2*10+1:10+1]; r = qr[10:0];
      // q < 2^(XW+1): drop one bit when it carries
      if (q[10]) m0_div = m0_mkx(2'd0, s, na[10+16:10+1] - nb[10+16:10+1] - 10 + 1, q[10:1], (r != 0) | q[0] | na[0] | nb[0]);
      else m0_div = m0_mkx(2'd0, s, na[10+16:10+1] - nb[10+16:10+1] - 10, q[9:0], (r != 0) | na[0] | nb[0]);
    end
  endfunction
  function automatic [29:0] m0_sqrt(input [29:0] a);
    logic [29:0] na; logic [1:0] spa; logic signed [15:0] e; logic [10:0] m; logic [2*10+3:0] rad;
    logic [10+2:0] rem, trial; logic [10:0] root; logic ge; integer i;
    na = m0_norm(a); spa = na[29:29-1];
    if (spa == 2'd1) m0_sqrt = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m0_sqrt = na[29-2] ? m0_mkx(2'd1, 1'b0, 0, 0, 1'b0) : na;
    else if (na[10:1] == 0 && !na[0]) m0_sqrt = na;
    else if (na[29-2]) m0_sqrt = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else begin
      e = na[10+16:10+1];
      // value = m * 2^e with e even; radicand = m * 2^(2K): root = sqrt(m) * 2^K, XW+1 bits
      if (e[0]) begin m = {na[10:1], 1'b0}; e = e - 1; end
      else m = {1'b0, na[10:1]};
      rad = {{(10+3){1'b0}}, m} << 10;
      rem = 0; root = 0;
      for (i = 10; i >= 0; i = i - 1) begin
        rem = {rem[10:0], rad[2*i +: 2]};
        trial = {root, 2'b01};
        ge = (rem >= trial);                  // unconditional assignments, as in udiv
        rem = ge ? rem - trial : rem;
        root = {root[9:0], ge};
      end
      m0_sqrt = m0_mkx(2'd0, 1'b0, (e >>> 1) - 5 + 1, root[10:1], (rem != 0) | root[0] | na[0]);
    end
  endfunction
  // X ordering treats NaN as unordered and compares finite values by sign and magnitude
  function automatic m0_lt(input [29:0] a, input [29:0] b);
    logic [29:0] na, nb; logic za, zb, sa, sb, mag_lt; logic signed [15:0] ea, eb;
    na = m0_norm(a); nb = m0_norm(b);
    za = (na[10:1] == 0) && !na[0]; zb = (nb[10:1] == 0) && !nb[0];
    sa = na[29-2] && !za; sb = nb[29-2] && !zb;
    if (na[29:29-1] == 2'd1 || nb[29:29-1] == 2'd1) m0_lt = 1'b0;
    else if (na[29:29-1] == 2'd2 || nb[29:29-1] == 2'd2) begin
      if (na[29:29-1] == 2'd2 && nb[29:29-1] == 2'd2) m0_lt = na[29-2] && !nb[29-2];
      else if (na[29:29-1] == 2'd2) m0_lt = na[29-2];
      else m0_lt = !nb[29-2];
    end else if (za && zb) m0_lt = 1'b0;
    else if (sa != sb) m0_lt = sa;
    else begin
      ea = na[10+16:10+1]; eb = nb[10+16:10+1];
      if (za) mag_lt = 1'b1; else if (zb) mag_lt = 1'b0;
      else mag_lt = (ea < eb) || (ea == eb && (na[10:1] < nb[10:1] || (na[10:1] == nb[10:1] && !na[0] && nb[0])));
      m0_lt = sa ? !mag_lt && !(za && zb) && !m0_eq(na, nb) : mag_lt;
    end
  endfunction
  function automatic m0_eq(input [29:0] a, input [29:0] b);
    logic [29:0] na, nb; logic za, zb;
    na = m0_norm(a); nb = m0_norm(b);
    za = (na[10:1] == 0) && !na[0]; zb = (nb[10:1] == 0) && !nb[0];
    if (na[29:29-1] == 2'd1 || nb[29:29-1] == 2'd1) m0_eq = 1'b0;
    else if (na[29:29-1] == 2'd2 || nb[29:29-1] == 2'd2)
      m0_eq = (na[29:29-1] == nb[29:29-1]) && (na[29-2] == nb[29-2]);
    else if (za || zb) m0_eq = za && zb;
    else m0_eq = (na[29-2] == nb[29-2]) && (na[10+16:10+1] == nb[10+16:10+1]) && (na[10:1] == nb[10:1]) && (na[0] == nb[0]);
  endfunction

  // fp4e2m1 pattern -> V (bit VW = denormal-read flag returned beside)
  function automatic [22:0] m0_unpack_s_e(input [3:0] b, input daz);
    logic [1:0] e; logic [0:0] m; logic [2:0] sig; logic signed [15:0] ex; logic den, s;
    e = b[2:1]; m = b[0:0]; s = b[3]; den = 1'b0; sig = 0; ex = 0;
    if (1'b0) m0_unpack_s_e = {1'b0, m0_mkv(2'd1, 1'b0, 0, 0)};
    else if (1'b0) m0_unpack_s_e = {1'b0, m0_mkv(2'd2, s, 0, 0)};
    else begin
    if (e == 0) begin sig = {{(3-1){1'b0}}, m}; ex = -1; if (m != 0) den = 1'b1; if (daz && m != 0) sig = 0; end
    else begin sig = {{(3-1-1){1'b0}}, 1'b1, m}; ex = e - 2; end
      m0_unpack_s_e = {den, m0_mkv(2'd0, s, ex, sig)};
    end
  endfunction

  // fps0e8m0N pattern -> V (bit VW = denormal-read flag returned beside)
  function automatic [22:0] m0_unpack_s_s(input [7:0] b, input daz);
    logic [7:0] e; logic [0:0] m; logic [2:0] sig; logic signed [15:0] ex; logic den, s;
    e = b[7:0]; m = 1'b0; s = 1'b0; den = 1'b0; sig = 0; ex = 0;
    if ((e == 8'd255)) m0_unpack_s_s = {1'b0, m0_mkv(2'd1, 1'b0, 0, 0)};
    else if (1'b0) m0_unpack_s_s = {1'b0, m0_mkv(2'd2, s, 0, 0)};
    else begin
    sig = 1; ex = e - 127;
      m0_unpack_s_s = {den, m0_mkv(2'd0, s, ex, sig)};
    end
  endfunction

  function automatic [183:0] m0_unpack_s(input [39:0] b, input daz);
    logic [22:0] ve, vs; logic [22:0] vo; integer i; logic [2:0] se, ss; logic signed [15:0] ee, es;
    vs = m0_unpack_s_s(b[32 +: 8], 1'b0);
    ss = vs[2:0]; es = vs[21-3 -: 16];
    for (i = 0; i < 8; i = i + 1) begin
      ve = m0_unpack_s_e(b[i*4 +: 4], daz);
      se = ve[2:0]; ee = ve[21-3 -: 16];
      if (ve[21:21-1] != 2'd0) vo = ve;
      else vo = {ve[22], m0_mkv(2'd0, ve[21-2], ee + es, se * ss)};
      m0_unpack_s[i*23 +: 23] = vo;
    end
  endfunction

  // X -> blksfps0e8m0Nefp4e2m1s8_e (fp4e2m1): sign(1) exp 2 man 1, top field 3, max finite 3'd7
  function automatic [10+4-1:0] m0_pack_blksfps0e8m0Nefp4e2m1s8_e(input [29:0] x0, input [2:0] rnd, input [7:0] word, input ftz);
    logic [29:0] x; logic [1:0] sp; logic s; logic signed [15:0] e, eu, biased; logic [9:0] sig;
    logic st, inexact, up, upn, half_eq, gt_half, tiny, ovf, unf, carry_n, to_inf; integer sh, shn, sht;
    logic [10:0] keep, rest, keepn, restn, halfv, halfn; logic [10+8:0] fint, fintn; logic [10-1:0] fl;
    logic [4+16:0] code; logic [4:0] mag; logic [4-1:0] outb;
    x = m0_norm(x0); sp = x[29:29-1]; s = x[29-2] & 1; sig = x[10:1]; st = x[0]; e = x[10+16:10+1];
    fl = 0; outb = 0;
    if (sp == 2'd1) begin fl[5] = 1'b1; outb = 4'd0; end
    else if (sp == 2'd2) begin
      outb = {s, 3'd7}; if (!0) begin fl[4] = 1'b1; fl[2] = 1'b1; end
    end else if (sig == 0 && !st) begin outb = 1 ? 0 : {s, {3{1'b0}}}; end
    else begin
      if (sig == 0) begin sig = 1 << 9; e = e - (2*10-1); end // normalize the lone sticky's tiny value
      eu = e + 9;                 // exponent of the leading one
      biased = eu + 1;
      shn = 10 - 1 - 1;           // bits dropped at the normal precision
      sh = (biased >= 1) ? shn : shn + (1 - biased);
      sht = sh;
      if (sh > 10 + 1) sh = 10 + 1;
      keep = {1'b0, sig} >> sh; rest = {1'b0, sig} & ((sh > 10) ? {(10+1){1'b1}} : ({1'b0, {10{1'b1}}} >> (10 - sh)));
      halfv = (sh == 0) ? 0 : ({{10{1'b0}}, 1'b1} << (sh - 1));
      keepn = {1'b0, sig} >> shn; restn = {1'b0, sig} & ({1'b0, {10{1'b1}}} >> (10 - shn));
      halfn = (shn == 0) ? 0 : ({{10{1'b0}}, 1'b1} << (shn - 1));
      inexact = (rest != 0) | st;
      fint = (sht - 8 > 10) ? 0 : (sht >= 8) ? (rest >> (sht - 8)) : (rest << (8 - sht));
      fintn = (shn >= 8) ? (restn >> (shn - 8)) : (restn << (8 - shn));
      up = m0_rup(rnd, s, inexact, rest, halfv, st, keep[0], fint, word);
      upn = m0_rup(rnd, s, (restn != 0) | st, restn, halfn, st, keepn[0], fintn, word);
      carry_n = ((keepn + upn) == ({{10{1'b0}}, 1'b1} << (1 + 1)));
      mag = keep + up;
      if (biased < 1) biased = 0;
      code = (biased < 1) ? mag : ((biased << 1) + mag - ({{(4+16){1'b0}}, 1'b1} << 1));
      tiny = 0 ? (eu < 0) : ((eu < 0) && !(eu == 0 - 1 && carry_n) && !(eu + 1 == 0 && carry_n));
      ovf = (code > 3'd7);
      if (ovf) begin
        to_inf = 0 && (rnd == 3'd0 || (rnd == 3'd3 && !s) || (rnd == 3'd2 && s) || rnd == 3'd5 || (rnd == 3'd4 && (eu > 2 || up)));
        outb = to_inf ? {s, 3'd7} : {s, 3'd7};
        fl[2] = 1'b1; fl[4] = 1'b1;
      end else begin
        outb = {s, code[2:0]};
        if (inexact) fl[4] = 1'b1;
        if (tiny && inexact) fl[3] = 1'b1;
        if (ftz && code[3-1:1] == 0 && code[0:0] != 0) begin
          outb = {s, {3{1'b0}}}; fl[4] = 1'b1; fl[3] = 1'b1;
        end

      end
    end
    m0_pack_blksfps0e8m0Nefp4e2m1s8_e = {fl, outb};
  endfunction

  // X -> blksfps0e8m0Nefp4e2m1s8_s (fps0e8m0N): exponent-only, top field 254
  function automatic [10+8-1:0] m0_pack_blksfps0e8m0Nefp4e2m1s8_s(input [29:0] x0, input [2:0] rnd, input [7:0] word, input ftz);
    logic [29:0] x; logic [1:0] sp; logic signed [15:0] e, eu, code; logic [9:0] sig, frac; logic s, st, inexact, up, gt_half, half_eq;
    logic [10+8:0] fint; logic [10-1:0] fl; logic [8-1:0] outb;
    x = m0_norm(x0); sp = x[29:29-1]; s = x[29-2] & 0; sig = x[10:1]; st = x[0]; e = x[10+16:10+1];
    fl = 0; outb = 0;
    if (sp == 2'd1) begin fl[5] = 1'b1; outb = 8'd255; end
    else if (sp == 2'd2) begin outb = 8'd254; if (!0) begin fl[4] = 1'b1; fl[2] = 1'b1; end end
    else if (sig == 0 && !st) begin outb = 0; fl[4] = 1'b1; end
    else begin
      if (sig == 0) begin sig = 1 << 9; e = e - (2*10-1); end
      eu = e + 9;
      frac = sig & {1'b0, {(10-1){1'b1}}};
      inexact = (frac != 0) | st;
      gt_half = frac > ({{(10-1){1'b0}}, 1'b1} << (10 - 2)) || (frac == ({{(10-1){1'b0}}, 1'b1} << (10 - 2)) && st);
      half_eq = (frac == ({{(10-1){1'b0}}, 1'b1} << (10 - 2))) && !st;
      fint = (10 - 1 >= 8) ? ({{(8+1){1'b0}}, frac} >> (10 - 1 - 8)) : ({{(8+1){1'b0}}, frac} << (8 - 10 + 1));
      case (rnd)
        3'd0: up = gt_half || (half_eq && ((eu + 127) & 1));
        3'd1: up = 1'b0;
        3'd2: up = s && inexact;
        3'd3: up = !s && inexact;
        3'd4: up = inexact && (0 ? (fint >= word) : (fint > word));
        default: up = inexact;
      endcase
      code = eu + 127 + up;
      if (code < 0) begin outb = 8'd0; fl[4] = 1'b1; end
      else if (code > 254) begin
        outb = (0 && (rnd == 3'd0 || (rnd == 3'd3 && !s) || (rnd == 3'd2 && s) || rnd == 3'd5 || rnd == 3'd4)) ? 8'd254 : 8'd254;
        fl[4] = 1'b1; fl[2] = 1'b1;
      end else begin
        outb = code[7:0];
        if (inexact) fl[4] = 1'b1;
        if (inexact && code == 254) fl[2] = 1'b1;
      end
    end
    m0_pack_blksfps0e8m0Nefp4e2m1s8_s = {fl, outb};
  endfunction

  // fps0e8m0N pattern -> V (bit VW = denormal-read flag returned beside)
  function automatic [22:0] m0_unpack_blksfps0e8m0Nefp4e2m1s8_sd(input [7:0] b, input daz);
    logic [7:0] e; logic [0:0] m; logic [2:0] sig; logic signed [15:0] ex; logic den, s;
    e = b[7:0]; m = 1'b0; s = 1'b0; den = 1'b0; sig = 0; ex = 0;
    if ((e == 8'd255)) m0_unpack_blksfps0e8m0Nefp4e2m1s8_sd = {1'b0, m0_mkv(2'd1, 1'b0, 0, 0)};
    else if (1'b0) m0_unpack_blksfps0e8m0Nefp4e2m1s8_sd = {1'b0, m0_mkv(2'd2, s, 0, 0)};
    else begin
    sig = 1; ex = e - 127;
      m0_unpack_blksfps0e8m0Nefp4e2m1s8_sd = {den, m0_mkv(2'd0, s, ex, sig)};
    end
  endfunction

  // section 2.6 quantizer into blksfps0e8m0Nefp4e2m1s8
  function automatic [119:0] m0_quant_blksfps0e8m0Nefp4e2m1s8(input [239:0] xs, input [2:0] rnd, input [63:0] words, input ftz);
    logic [29:0] x, nx, amax, xe, sq; logic have; logic signed [15:0] eu, emx, es; logic [9:0] sm; integer i;
    logic [7:0] sb; logic [22:0] vs; logic [10+8-1:0] ps; logic [10+4-1:0] pe;
    logic [39:0] blk; logic [79:0] fls; logic [10-1:0] f; logic sat, nz;
    have = 1'b0; emx = 0; sm = 0; amax = 0; blk = 0; fls = 0;
    for (i = 0; i < 8; i = i + 1) begin
      nx = m0_norm(xs[i*30 +: 30]);
      if (nx[29:29-1] == 2'd0 && (nx[10:1] != 0) && !(0 && nx[29-2])) begin
        eu = nx[10+16:10+1] + 9;
        if (!have || eu > emx || (eu == emx && nx[10:1] > sm)) begin have = 1'b1; emx = eu; sm = nx[10:1]; amax = {2'd0, 1'b0, nx[10+16:0]}; end
      end
    end
    if (1) begin
      if (!have) sb = 0;
      else begin
        es = emx - 2 + 127;
        sb = (es < 0) ? 0 : (es > 254) ? 254 : es;
      end
    end else begin
      if (!have) sb = 8'd0;
      else begin
        ps = m0_pack_blksfps0e8m0Nefp4e2m1s8_s(m0_div(amax, m0_mkx(2'd0, 1'b0, -7, 10'd768, 1'b0)), 0 ? 3'd3 : 3'd0, 0, 1'b0);
        sb = ps[7:0];
        if (sb == 0) sb = 8'd0;
        else if (sb > 8'd254) sb = 8'd254;
      end
    end
    vs = m0_unpack_blksfps0e8m0Nefp4e2m1s8_sd(sb, 1'b0);
    for (i = 0; i < 8; i = i + 1) begin
      x = xs[i*30 +: 30]; f = 0;
      if (0 && x[29-2] &&
          (x[29:29-1] == 2'd2 || (x[29:29-1] == 2'd0 && (x[10:1] != 0 || x[0])))) begin
        f[0] = 1'b1;
        if (0) begin blk[i*4 +: 4] = 4'd0; f[5] = 1'b1; end
        else begin blk[i*4 +: 4] = 0 ? 0 : 4'd7; f[4] = 1'b1; end
      end else if (x[29:29-1] == 2'd1) begin
        f[0] = 1'b1;
        if (0) begin blk[i*4 +: 4] = 4'd0; f[5] = 1'b1; end
        else begin blk[i*4 +: 4] = 0 ? 0 : 4'd7; f[4] = 1'b1; end
      end else if (x[29:29-1] == 2'd2) begin
        f[2] = 1'b1;
        if (0 && !(0 && 0)) begin blk[i*4 +: 4] = 4'd0; f[5] = 1'b1; end
        else if (0 && 0) blk[i*4 +: 4] = 4'd0 | ((x[29-2] && 1) ? (4'd1 << 3) : 0);
        else if (0) begin blk[i*4 +: 4] = 0; f[4] = 1'b1; end
        else begin blk[i*4 +: 4] = x[29-2] ? 4'd15 : 4'd7; f[4] = 1'b1; end
      end else begin
        // x / scale
        if (1) xe = {x[29:29-2], x[10+16:10+1] - vs[21-3 -: 16], x[10:0]};
        else xe = m0_div(x, m0_x(vs[21:0]));
        sat = 1'b0;
        if (1 && !0) begin
          // saturate at the element's largest finite magnitude
          if (m0_lt(m0_mkx(2'd0, 1'b0, -7, 10'd768, 1'b0), {2'd0, 1'b0, xe[10+16:0]})) sat = 1'b1;
        end
        if (sat) begin
          blk[i*4 +: 4] = 4'd7 | ((xe[29-2] && 1) ? (4'd1 << 3) : 0);
          f[2] = 1'b1; f[4] = 1'b1;
        end else begin
          pe = m0_pack_blksfps0e8m0Nefp4e2m1s8_e(xe, rnd, words[i*8 +: 8], ftz);
          blk[i*4 +: 4] = pe[3:0];
          f = f | pe[10+4-1:4];
          if (0) f[0] = 1'b0;
        end
      end
      fls[i*10 +: 10] = f;
    end
    blk[32 +: 8] = sb;
    m0_quant_blksfps0e8m0Nefp4e2m1s8 = {fls, blk};
  endfunction

  function automatic [29:0] m0_family_operand(input [29:0] value);
    logic [29:0] normalized;
    logic signed [15:0] exponent;
    logic [9:0] significand;
    normalized = m0_norm(value);
    exponent = $signed(normalized[26:11]) + 16'sd7;
    significand = normalized[10:1] >> 7;
    m0_family_operand = {normalized[29:27], exponent, significand, normalized[0]};
  endfunction
endpackage

// alu_core_m1_pkg: the exact-arithmetic functions of mode 1 (8xfp8e4m3)
package alu_core_m1_pkg;

  // ---- m1: V = {special[1:0], sign, exp[12] (signed), sig[4]}
  //           X = {special[1:0], sign, exp[12] (signed), sig[12], sticky}
  localparam int m1_SW = 4, m1_EW = 12, m1_XW = 12;
  localparam int m1_VW = 19, m1_XT = 28;
  function automatic [18:0] m1_mkv(input [1:0] sp, input s, input signed [11:0] e, input [3:0] sig);
    m1_mkv = {sp, s, e, sig};
  endfunction
  function automatic [27:0] m1_mkx(input [1:0] sp, input s, input signed [11:0] e, input [11:0] sig, input st);
    m1_mkx = {sp, s, e, sig, st};
  endfunction
  function automatic [27:0] m1_x(input [18:0] v);   // widen V to X
    m1_x = {v[18:18-1], v[18-2], v[18-3 -: 12], {{(12-4){1'b0}}, v[3:0]}, 1'b0};
  endfunction
  // normalize: leading one at bit XW-1 (zero stays zero)
  function automatic [27:0] m1_norm(input [27:0] x);
    logic [11:0] s; logic signed [11:0] e; integer k;
    s = x[12:1]; e = x[12+12:12+1];
    if (s != 0) begin
      for (k = 8; k >= 1; k = k / 2) begin
        if (k < 12) begin
          if (s[11 -: 1] == 1'b0 && (s >> (12 - k)) == 0) begin
            s = s << k; e = e - k;
          end
        end
      end
    end
    m1_norm = {x[27:27-1], x[27-2], e, s, x[0]};
  endfunction

  function automatic m1_rup(input [2:0] rnd, input s, input inexact, input [12:0] rest, input [12:0] halfv,
                             input st, input lsb, input [12+8:0] fint, input [7:0] word);
    logic gt_half, half_eq;
    gt_half = rest > halfv; half_eq = (rest == halfv) && (halfv != 0);
    case (rnd)
      3'd0: m1_rup = gt_half || (half_eq && (st || lsb));
      3'd1: m1_rup = 1'b0;
      3'd2: m1_rup = inexact && s;
      3'd3: m1_rup = inexact && !s;
      3'd4: m1_rup = inexact && (0 ? (fint >= word) : (fint > word));
      default: m1_rup = inexact;   // 5: away from zero
    endcase
  endfunction

  // a +/- b on X (normalized inputs); specials: nan wins, inf-inf = nan
  function automatic [27:0] m1_add(input [27:0] a, input [27:0] b, input sub);
    logic [27:0] na, nb, big, sml; logic [1:0] spa, spb; logic sa, sb, sr, sw;
    logic signed [11:0] ea, eb, d; logic [12:0] ms, mb, r; logic st, stb; integer sh;
    na = m1_norm(a); nb = m1_norm(b);
    spa = na[27:27-1]; spb = nb[27:27-1];
    sa = na[27-2]; sb = nb[27-2] ^ sub;
    if (spa == 2'd1 || spb == 2'd1) m1_add = m1_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 && spb == 2'd2) m1_add = (sa == sb) ? m1_mkx(2'd2, sa, 0, 0, 1'b0) : m1_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m1_add = m1_mkx(2'd2, sa, 0, 0, 1'b0);
    else if (spb == 2'd2) m1_add = m1_mkx(2'd2, sb, 0, 0, 1'b0);
    else if (na[12:1] == 0 && !na[0]) m1_add = {nb[27:27-1], sb, nb[27-3:0]};
    else if (nb[12:1] == 0 && !nb[0]) m1_add = na;
    else begin
      ea = na[12+12:12+1]; eb = nb[12+12:12+1];
      // order by magnitude (both normalized): larger exponent, then sig
      if (ea > eb || (ea == eb && na[12:1] >= nb[12:1])) begin big = na; sml = nb; sw = 1'b0; end
      else begin big = nb; sml = na; sw = 1'b1; end
      d = big[12+12:12+1] - sml[12+12:12+1];
      ms = {1'b0, sml[12:1]}; stb = sml[0];
      if (d > 12 + 1) begin stb = stb | (ms != 0); ms = 0; end
      else begin
        for (sh = 0; sh < 12 + 2; sh = sh + 1) begin
          if (sh < d) begin stb = stb | ms[0]; ms = ms >> 1; end
        end
      end
      mb = {1'b0, big[12:1]}; st = big[0] | stb;
      if ((sw ? sb : sa) == (sw ? sa : sb)) begin
        r = mb + ms;
        sr = sw ? sb : sa;
      end else begin
        // subtract: the sticky of the smaller operand borrows one lsb
        r = mb - ms - (stb ? 1'b1 : 1'b0);
        sr = sw ? sb : sa;
        if (r == 0 && !st) sr = 1'b0;
      end
      if (r[12]) begin st = st | r[0]; r = r >> 1; m1_add = m1_mkx(2'd0, sr, big[12+12:12+1] + 1, r[11:0], st); end
      else m1_add = m1_mkx(2'd0, sr, big[12+12:12+1], r[11:0], st);
    end
  endfunction
  function automatic [27:0] m1_mul(input [27:0] a, input [27:0] b);
    logic [27:0] na, nb; logic [1:0] spa, spb; logic s; logic [2*12-1:0] pr; logic st; integer k;
    na = m1_norm(a); nb = m1_norm(b);
    spa = na[27:27-1]; spb = nb[27:27-1]; s = na[27-2] ^ nb[27-2];
    if (spa == 2'd1 || spb == 2'd1) m1_mul = m1_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 || spb == 2'd2) begin
      if ((spa == 2'd0 && na[12:1] == 0 && !na[0]) || (spb == 2'd0 && nb[12:1] == 0 && !nb[0]))
        m1_mul = m1_mkx(2'd1, 1'b0, 0, 0, 1'b0);
      else m1_mul = m1_mkx(2'd2, s, 0, 0, 1'b0);
    end else begin
      pr = na[12:1] * nb[12:1];
      st = na[0] | nb[0];
      // keep the top XW bits of the product, the rest folds into sticky
      st = st | (pr[11:0] != 0);
      m1_mul = m1_mkx(2'd0, s, na[12+12:12+1] + nb[12+12:12+1] + 12, pr[2*12-1:12], st);
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
  function automatic [2*12+1:0] m1_udiv(input [11:0] a, input [11:0] dv);
    logic [12+1:0] r; logic [12:0] q; logic ge; integer i;
    r = {2'b0, a}; q = 0;
    for (i = 12; i >= 0; i = i - 1) begin
      ge = (r >= {2'b0, dv});
      r = ge ? r - {2'b0, dv} : r;
      q = {q[11:0], ge};
      if (i > 0) r = {r[12:0], 1'b0};
    end
    m1_udiv = {q, r[12:0]};
  endfunction
  // the exact product: {special[1:0], sign, exp[EW], sig[2XW]} (no sticky)
  function automatic [2*12+12+2:0] m1_mulx(input [27:0] a, input [27:0] b);
    logic [27:0] na, nb; logic [1:0] spa, spb, sp; logic s; logic [2*12-1:0] pr;
    na = m1_norm(a); nb = m1_norm(b);
    pr = na[12:1] * nb[12:1];
    spa = na[27:27-1]; spb = nb[27:27-1]; s = na[27-2] ^ nb[27-2];
    if (spa == 2'd1 || spb == 2'd1) sp = 2'd1;
    else if (spa == 2'd2 || spb == 2'd2)
      sp = ((spa == 2'd0 && na[12:1] == 0) || (spb == 2'd0 && nb[12:1] == 0)) ? 2'd1 : 2'd2;
    else sp = 2'd0;
    m1_mulx = {sp, s, na[12+12:12+1] + nb[12+12:12+1], pr};
  endfunction
  function automatic [27:0] m1_div(input [27:0] a, input [27:0] b);
    logic [27:0] na, nb; logic [1:0] spa, spb; logic s; logic [2*12+1:0] qr; logic [12:0] q, r;
    na = m1_norm(a); nb = m1_norm(b);
    spa = na[27:27-1]; spb = nb[27:27-1]; s = na[27-2] ^ nb[27-2];
    if (spa == 2'd1 || spb == 2'd1) m1_div = m1_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 && spb == 2'd2) m1_div = m1_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m1_div = m1_mkx(2'd2, s, 0, 0, 1'b0);
    else if (spb == 2'd2) m1_div = m1_mkx(2'd0, s, 0, 0, 1'b0);
    else if (nb[12:1] == 0 && !nb[0]) begin
      if (na[12:1] == 0 && !na[0]) m1_div = m1_mkx(2'd1, 1'b0, 0, 0, 1'b0);
      else m1_div = m1_mkx(2'd2, s, 0, 0, 1'b0);
    end else if (na[12:1] == 0 && !na[0]) m1_div = m1_mkx(2'd0, s, 0, 0, 1'b0);
    else begin
      qr = m1_udiv(na[12:1], nb[12:1]);     // both normalized: nonzero finite
      q = qr[2*12+1:12+1]; r = qr[12:0];
      // q < 2^(XW+1): drop one bit when it carries
      if (q[12]) m1_div = m1_mkx(2'd0, s, na[12+12:12+1] - nb[12+12:12+1] - 12 + 1, q[12:1], (r != 0) | q[0] | na[0] | nb[0]);
      else m1_div = m1_mkx(2'd0, s, na[12+12:12+1] - nb[12+12:12+1] - 12, q[11:0], (r != 0) | na[0] | nb[0]);
    end
  endfunction
  function automatic [27:0] m1_sqrt(input [27:0] a);
    logic [27:0] na; logic [1:0] spa; logic signed [11:0] e; logic [12:0] m; logic [2*12+3:0] rad;
    logic [12+2:0] rem, trial; logic [12:0] root; logic ge; integer i;
    na = m1_norm(a); spa = na[27:27-1];
    if (spa == 2'd1) m1_sqrt = m1_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m1_sqrt = na[27-2] ? m1_mkx(2'd1, 1'b0, 0, 0, 1'b0) : na;
    else if (na[12:1] == 0 && !na[0]) m1_sqrt = na;
    else if (na[27-2]) m1_sqrt = m1_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else begin
      e = na[12+12:12+1];
      // value = m * 2^e with e even; radicand = m * 2^(2K): root = sqrt(m) * 2^K, XW+1 bits
      if (e[0]) begin m = {na[12:1], 1'b0}; e = e - 1; end
      else m = {1'b0, na[12:1]};
      rad = {{(12+3){1'b0}}, m} << 12;
      rem = 0; root = 0;
      for (i = 12; i >= 0; i = i - 1) begin
        rem = {rem[12:0], rad[2*i +: 2]};
        trial = {root, 2'b01};
        ge = (rem >= trial);                  // unconditional assignments, as in udiv
        rem = ge ? rem - trial : rem;
        root = {root[11:0], ge};
      end
      m1_sqrt = m1_mkx(2'd0, 1'b0, (e >>> 1) - 6 + 1, root[12:1], (rem != 0) | root[0] | na[0]);
    end
  endfunction
  // X ordering treats NaN as unordered and compares finite values by sign and magnitude
  function automatic m1_lt(input [27:0] a, input [27:0] b);
    logic [27:0] na, nb; logic za, zb, sa, sb, mag_lt; logic signed [11:0] ea, eb;
    na = m1_norm(a); nb = m1_norm(b);
    za = (na[12:1] == 0) && !na[0]; zb = (nb[12:1] == 0) && !nb[0];
    sa = na[27-2] && !za; sb = nb[27-2] && !zb;
    if (na[27:27-1] == 2'd1 || nb[27:27-1] == 2'd1) m1_lt = 1'b0;
    else if (na[27:27-1] == 2'd2 || nb[27:27-1] == 2'd2) begin
      if (na[27:27-1] == 2'd2 && nb[27:27-1] == 2'd2) m1_lt = na[27-2] && !nb[27-2];
      else if (na[27:27-1] == 2'd2) m1_lt = na[27-2];
      else m1_lt = !nb[27-2];
    end else if (za && zb) m1_lt = 1'b0;
    else if (sa != sb) m1_lt = sa;
    else begin
      ea = na[12+12:12+1]; eb = nb[12+12:12+1];
      if (za) mag_lt = 1'b1; else if (zb) mag_lt = 1'b0;
      else mag_lt = (ea < eb) || (ea == eb && (na[12:1] < nb[12:1] || (na[12:1] == nb[12:1] && !na[0] && nb[0])));
      m1_lt = sa ? !mag_lt && !(za && zb) && !m1_eq(na, nb) : mag_lt;
    end
  endfunction
  function automatic m1_eq(input [27:0] a, input [27:0] b);
    logic [27:0] na, nb; logic za, zb;
    na = m1_norm(a); nb = m1_norm(b);
    za = (na[12:1] == 0) && !na[0]; zb = (nb[12:1] == 0) && !nb[0];
    if (na[27:27-1] == 2'd1 || nb[27:27-1] == 2'd1) m1_eq = 1'b0;
    else if (na[27:27-1] == 2'd2 || nb[27:27-1] == 2'd2)
      m1_eq = (na[27:27-1] == nb[27:27-1]) && (na[27-2] == nb[27-2]);
    else if (za || zb) m1_eq = za && zb;
    else m1_eq = (na[27-2] == nb[27-2]) && (na[12+12:12+1] == nb[12+12:12+1]) && (na[12:1] == nb[12:1]) && (na[0] == nb[0]);
  endfunction

  // fp8e4m3 pattern -> V (bit VW = denormal-read flag returned beside)
  function automatic [19:0] m1_unpack_s(input [7:0] b, input daz);
    logic [3:0] e; logic [2:0] m; logic [3:0] sig; logic signed [11:0] ex; logic den, s;
    e = b[6:3]; m = b[2:0]; s = b[7]; den = 1'b0; sig = 0; ex = 0;
    if ((e == 4'd15 && m == {3{1'b1}})) m1_unpack_s = {1'b0, m1_mkv(2'd1, 1'b0, 0, 0)};
    else if (1'b0) m1_unpack_s = {1'b0, m1_mkv(2'd2, s, 0, 0)};
    else begin
    if (e == 0) begin sig = {{(4-3){1'b0}}, m}; ex = -9; if (m != 0) den = 1'b1; if (daz && m != 0) sig = 0; end
    else begin sig = {{(4-3-1){1'b0}}, 1'b1, m}; ex = e - 10; end
      m1_unpack_s = {den, m1_mkv(2'd0, s, ex, sig)};
    end
  endfunction

  // X -> fp8e4m3 (fp8e4m3): sign(1) exp 4 man 3, top field 15, max finite 7'd126
  function automatic [10+8-1:0] m1_pack_fp8e4m3(input [27:0] x0, input [2:0] rnd, input [7:0] word, input ftz);
    logic [27:0] x; logic [1:0] sp; logic s; logic signed [11:0] e, eu, biased; logic [11:0] sig;
    logic st, inexact, up, upn, half_eq, gt_half, tiny, ovf, unf, carry_n, to_inf; integer sh, shn, sht;
    logic [12:0] keep, rest, keepn, restn, halfv, halfn; logic [12+8:0] fint, fintn; logic [10-1:0] fl;
    logic [8+12:0] code; logic [8:0] mag; logic [8-1:0] outb;
    x = m1_norm(x0); sp = x[27:27-1]; s = x[27-2] & 1; sig = x[12:1]; st = x[0]; e = x[12+12:12+1];
    fl = 0; outb = 0;
    if (sp == 2'd1) begin fl[5] = 1'b1; outb = 8'd127; end
    else if (sp == 2'd2) begin
      outb = {s, 7'd126}; if (!0) begin fl[4] = 1'b1; fl[2] = 1'b1; end
    end else if (sig == 0 && !st) begin outb = 1 ? 0 : {s, {7{1'b0}}}; end
    else begin
      if (sig == 0) begin sig = 1 << 11; e = e - (2*12-1); end // normalize the lone sticky's tiny value
      eu = e + 11;                 // exponent of the leading one
      biased = eu + 7;
      shn = 12 - 1 - 3;           // bits dropped at the normal precision
      sh = (biased >= 1) ? shn : shn + (1 - biased);
      sht = sh;
      if (sh > 12 + 1) sh = 12 + 1;
      keep = {1'b0, sig} >> sh; rest = {1'b0, sig} & ((sh > 12) ? {(12+1){1'b1}} : ({1'b0, {12{1'b1}}} >> (12 - sh)));
      halfv = (sh == 0) ? 0 : ({{12{1'b0}}, 1'b1} << (sh - 1));
      keepn = {1'b0, sig} >> shn; restn = {1'b0, sig} & ({1'b0, {12{1'b1}}} >> (12 - shn));
      halfn = (shn == 0) ? 0 : ({{12{1'b0}}, 1'b1} << (shn - 1));
      inexact = (rest != 0) | st;
      fint = (sht - 8 > 12) ? 0 : (sht >= 8) ? (rest >> (sht - 8)) : (rest << (8 - sht));
      fintn = (shn >= 8) ? (restn >> (shn - 8)) : (restn << (8 - shn));
      up = m1_rup(rnd, s, inexact, rest, halfv, st, keep[0], fint, word);
      upn = m1_rup(rnd, s, (restn != 0) | st, restn, halfn, st, keepn[0], fintn, word);
      carry_n = ((keepn + upn) == ({{12{1'b0}}, 1'b1} << (3 + 1)));
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
    m1_pack_fp8e4m3 = {fl, outb};
  endfunction
endpackage
// ADIR-MEMBER top
// EVOLVE-BLOCK-START
// ADIR-DECL v1
// STRUCTURE m0.l0.fp_adder kind=fp_adder slot=fp_adder mode=0 lane=0 width=40 format=blksfps0e8m0Nefp4e2m1s8 ops=fadd sv=alu_core_u_m0_l0_fp_adder
// STRUCTURE m0.l0.quantizer kind=quantizer slot=- mode=0 lane=0 width=40 format=blksfps0e8m0Nefp4e2m1s8 ops=fadd,fmul
// STRUCTURE m0.l0.fp_multiplier kind=fp_multiplier slot=fp_multiplier mode=0 lane=0 width=40 format=blksfps0e8m0Nefp4e2m1s8 ops=fmul sv=alu_core_u_m0_l0_fp_multiplier
// STRUCTURE m1.l0.fp_adder kind=fp_adder slot=fp_adder mode=1 lane=0 width=8 format=fp8e4m3 ops=fadd sv=alu_core_u_m1_l0_fp_adder
// STRUCTURE m1.l1.fp_adder kind=fp_adder slot=fp_adder mode=1 lane=1 width=8 format=fp8e4m3 ops=fadd sv=alu_core_u_m1_l1_fp_adder
// STRUCTURE m1.l2.fp_adder kind=fp_adder slot=fp_adder mode=1 lane=2 width=8 format=fp8e4m3 ops=fadd sv=alu_core_u_m1_l2_fp_adder
// STRUCTURE m1.l3.fp_adder kind=fp_adder slot=fp_adder mode=1 lane=3 width=8 format=fp8e4m3 ops=fadd sv=alu_core_u_m1_l3_fp_adder
// STRUCTURE m1.l4.fp_adder kind=fp_adder slot=fp_adder mode=1 lane=4 width=8 format=fp8e4m3 ops=fadd sv=alu_core_u_m1_l4_fp_adder
// STRUCTURE m1.l5.fp_adder kind=fp_adder slot=fp_adder mode=1 lane=5 width=8 format=fp8e4m3 ops=fadd sv=alu_core_u_m1_l5_fp_adder
// STRUCTURE m1.l6.fp_adder kind=fp_adder slot=fp_adder mode=1 lane=6 width=8 format=fp8e4m3 ops=fadd sv=alu_core_u_m1_l6_fp_adder
// STRUCTURE m1.l7.fp_adder kind=fp_adder slot=fp_adder mode=1 lane=7 width=8 format=fp8e4m3 ops=fadd sv=alu_core_u_m1_l7_fp_adder
// STRUCTURE m1.l0.unpacker kind=unpacker slot=unpacker mode=1 lane=0 width=8 format=fp8e4m3 ops=fadd,fmul sv=alu_core_u_m1_l0_unpacker
// STRUCTURE m1.l0.rounder kind=rounder slot=rounder mode=1 lane=0 width=8 format=fp8e4m3 ops=fadd,fmul sv=alu_core_u_m1_l0_rounder
// STRUCTURE m1.l0.fp_fma kind=fp_fma slot=fp_fma mode=1 lane=0 width=8 format=fp8e4m3 ops=fadd,fmul
// STRUCTURE m1.l1.unpacker kind=unpacker slot=unpacker mode=1 lane=1 width=8 format=fp8e4m3 ops=fadd,fmul sv=alu_core_u_m1_l1_unpacker
// STRUCTURE m1.l1.rounder kind=rounder slot=rounder mode=1 lane=1 width=8 format=fp8e4m3 ops=fadd,fmul sv=alu_core_u_m1_l1_rounder
// STRUCTURE m1.l1.fp_fma kind=fp_fma slot=fp_fma mode=1 lane=1 width=8 format=fp8e4m3 ops=fadd,fmul
// STRUCTURE m1.l2.unpacker kind=unpacker slot=unpacker mode=1 lane=2 width=8 format=fp8e4m3 ops=fadd,fmul sv=alu_core_u_m1_l2_unpacker
// STRUCTURE m1.l2.rounder kind=rounder slot=rounder mode=1 lane=2 width=8 format=fp8e4m3 ops=fadd,fmul sv=alu_core_u_m1_l2_rounder
// STRUCTURE m1.l2.fp_fma kind=fp_fma slot=fp_fma mode=1 lane=2 width=8 format=fp8e4m3 ops=fadd,fmul
// STRUCTURE m1.l3.unpacker kind=unpacker slot=unpacker mode=1 lane=3 width=8 format=fp8e4m3 ops=fadd,fmul sv=alu_core_u_m1_l3_unpacker
// STRUCTURE m1.l3.rounder kind=rounder slot=rounder mode=1 lane=3 width=8 format=fp8e4m3 ops=fadd,fmul sv=alu_core_u_m1_l3_rounder
// STRUCTURE m1.l3.fp_fma kind=fp_fma slot=fp_fma mode=1 lane=3 width=8 format=fp8e4m3 ops=fadd,fmul
// STRUCTURE m1.l4.unpacker kind=unpacker slot=unpacker mode=1 lane=4 width=8 format=fp8e4m3 ops=fadd,fmul sv=alu_core_u_m1_l4_unpacker
// STRUCTURE m1.l4.rounder kind=rounder slot=rounder mode=1 lane=4 width=8 format=fp8e4m3 ops=fadd,fmul sv=alu_core_u_m1_l4_rounder
// STRUCTURE m1.l4.fp_fma kind=fp_fma slot=fp_fma mode=1 lane=4 width=8 format=fp8e4m3 ops=fadd,fmul
// STRUCTURE m1.l5.unpacker kind=unpacker slot=unpacker mode=1 lane=5 width=8 format=fp8e4m3 ops=fadd,fmul sv=alu_core_u_m1_l5_unpacker
// STRUCTURE m1.l5.rounder kind=rounder slot=rounder mode=1 lane=5 width=8 format=fp8e4m3 ops=fadd,fmul sv=alu_core_u_m1_l5_rounder
// STRUCTURE m1.l5.fp_fma kind=fp_fma slot=fp_fma mode=1 lane=5 width=8 format=fp8e4m3 ops=fadd,fmul
// STRUCTURE m1.l6.unpacker kind=unpacker slot=unpacker mode=1 lane=6 width=8 format=fp8e4m3 ops=fadd,fmul sv=alu_core_u_m1_l6_unpacker
// STRUCTURE m1.l6.rounder kind=rounder slot=rounder mode=1 lane=6 width=8 format=fp8e4m3 ops=fadd,fmul sv=alu_core_u_m1_l6_rounder
// STRUCTURE m1.l6.fp_fma kind=fp_fma slot=fp_fma mode=1 lane=6 width=8 format=fp8e4m3 ops=fadd,fmul
// STRUCTURE m1.l7.unpacker kind=unpacker slot=unpacker mode=1 lane=7 width=8 format=fp8e4m3 ops=fadd,fmul sv=alu_core_u_m1_l7_unpacker
// STRUCTURE m1.l7.rounder kind=rounder slot=rounder mode=1 lane=7 width=8 format=fp8e4m3 ops=fadd,fmul sv=alu_core_u_m1_l7_rounder
// STRUCTURE m1.l7.fp_fma kind=fp_fma slot=fp_fma mode=1 lane=7 width=8 format=fp8e4m3 ops=fadd,fmul
// STRUCTURE m1.l0.fp_multiplier kind=fp_multiplier slot=fp_multiplier mode=1 lane=0 width=8 format=fp8e4m3 ops=fmul sv=alu_core_u_m1_l0_fp_multiplier
// STRUCTURE m1.l1.fp_multiplier kind=fp_multiplier slot=fp_multiplier mode=1 lane=1 width=8 format=fp8e4m3 ops=fmul sv=alu_core_u_m1_l1_fp_multiplier
// STRUCTURE m1.l2.fp_multiplier kind=fp_multiplier slot=fp_multiplier mode=1 lane=2 width=8 format=fp8e4m3 ops=fmul sv=alu_core_u_m1_l2_fp_multiplier
// STRUCTURE m1.l3.fp_multiplier kind=fp_multiplier slot=fp_multiplier mode=1 lane=3 width=8 format=fp8e4m3 ops=fmul sv=alu_core_u_m1_l3_fp_multiplier
// STRUCTURE m1.l4.fp_multiplier kind=fp_multiplier slot=fp_multiplier mode=1 lane=4 width=8 format=fp8e4m3 ops=fmul sv=alu_core_u_m1_l4_fp_multiplier
// STRUCTURE m1.l5.fp_multiplier kind=fp_multiplier slot=fp_multiplier mode=1 lane=5 width=8 format=fp8e4m3 ops=fmul sv=alu_core_u_m1_l5_fp_multiplier
// STRUCTURE m1.l6.fp_multiplier kind=fp_multiplier slot=fp_multiplier mode=1 lane=6 width=8 format=fp8e4m3 ops=fmul sv=alu_core_u_m1_l6_fp_multiplier
// STRUCTURE m1.l7.fp_multiplier kind=fp_multiplier slot=fp_multiplier mode=1 lane=7 width=8 format=fp8e4m3 ops=fmul sv=alu_core_u_m1_l7_fp_multiplier
// ADIR-END
module alu_core (
  input  logic [63:0] a,
  input  logic [63:0] b,
  input  logic [0:0] op,
  input  logic [0:0] mode,
  output logic [63:0] y
);
  // alu_core: behavioral reference derived from the instance (modes 1xblksfps0e8m0Nefp4e2m1s8, 8xfp8e4m3; ops fadd, fmul). Every (mode, op) pair computes the verify layer's exact semantics.
  // HIERARCHY: 34 physical structure modules instantiated by alu_core, built from 6 lane modules (one per mode and kind, parameter LANE) and 2 packages of engine functions (one per mode); a float mode's datapath is split into an unpacker (the xa/xb/den buses), the arithmetic and converter structures (unrounded results on the x bus) and a rounder (y and the flags); 0 misc lane modules and 0 block-conversion group modules
  // UNIT m0.l0.fp_adder module=alu_core_u_m0_l0_fp_adder kind=fp_adder members=m0.l0.fp_adder
  // UNIT m0.l0.fp_multiplier module=alu_core_u_m0_l0_fp_multiplier kind=fp_multiplier members=m0.l0.fp_multiplier
  // UNIT m1.l0.fp_adder module=alu_core_u_m1_l0_fp_adder kind=fp_adder members=m1.l0.fp_adder
  // UNIT m1.l1.fp_adder module=alu_core_u_m1_l1_fp_adder kind=fp_adder members=m1.l1.fp_adder
  // UNIT m1.l2.fp_adder module=alu_core_u_m1_l2_fp_adder kind=fp_adder members=m1.l2.fp_adder
  // UNIT m1.l3.fp_adder module=alu_core_u_m1_l3_fp_adder kind=fp_adder members=m1.l3.fp_adder
  // UNIT m1.l4.fp_adder module=alu_core_u_m1_l4_fp_adder kind=fp_adder members=m1.l4.fp_adder
  // UNIT m1.l5.fp_adder module=alu_core_u_m1_l5_fp_adder kind=fp_adder members=m1.l5.fp_adder
  // UNIT m1.l6.fp_adder module=alu_core_u_m1_l6_fp_adder kind=fp_adder members=m1.l6.fp_adder
  // UNIT m1.l7.fp_adder module=alu_core_u_m1_l7_fp_adder kind=fp_adder members=m1.l7.fp_adder
  // UNIT m1.l0.unpacker module=alu_core_u_m1_l0_unpacker kind=unpacker members=m1.l0.unpacker
  // UNIT m1.l0.rounder module=alu_core_u_m1_l0_rounder kind=rounder members=m1.l0.rounder
  // UNIT m1.l1.unpacker module=alu_core_u_m1_l1_unpacker kind=unpacker members=m1.l1.unpacker
  // UNIT m1.l1.rounder module=alu_core_u_m1_l1_rounder kind=rounder members=m1.l1.rounder
  // UNIT m1.l2.unpacker module=alu_core_u_m1_l2_unpacker kind=unpacker members=m1.l2.unpacker
  // UNIT m1.l2.rounder module=alu_core_u_m1_l2_rounder kind=rounder members=m1.l2.rounder
  // UNIT m1.l3.unpacker module=alu_core_u_m1_l3_unpacker kind=unpacker members=m1.l3.unpacker
  // UNIT m1.l3.rounder module=alu_core_u_m1_l3_rounder kind=rounder members=m1.l3.rounder
  // UNIT m1.l4.unpacker module=alu_core_u_m1_l4_unpacker kind=unpacker members=m1.l4.unpacker
  // UNIT m1.l4.rounder module=alu_core_u_m1_l4_rounder kind=rounder members=m1.l4.rounder
  // UNIT m1.l5.unpacker module=alu_core_u_m1_l5_unpacker kind=unpacker members=m1.l5.unpacker
  // UNIT m1.l5.rounder module=alu_core_u_m1_l5_rounder kind=rounder members=m1.l5.rounder
  // UNIT m1.l6.unpacker module=alu_core_u_m1_l6_unpacker kind=unpacker members=m1.l6.unpacker
  // UNIT m1.l6.rounder module=alu_core_u_m1_l6_rounder kind=rounder members=m1.l6.rounder
  // UNIT m1.l7.unpacker module=alu_core_u_m1_l7_unpacker kind=unpacker members=m1.l7.unpacker
  // UNIT m1.l7.rounder module=alu_core_u_m1_l7_rounder kind=rounder members=m1.l7.rounder
  // UNIT m1.l0.fp_multiplier module=alu_core_u_m1_l0_fp_multiplier kind=fp_multiplier members=m1.l0.fp_multiplier
  // UNIT m1.l1.fp_multiplier module=alu_core_u_m1_l1_fp_multiplier kind=fp_multiplier members=m1.l1.fp_multiplier
  // UNIT m1.l2.fp_multiplier module=alu_core_u_m1_l2_fp_multiplier kind=fp_multiplier members=m1.l2.fp_multiplier
  // UNIT m1.l3.fp_multiplier module=alu_core_u_m1_l3_fp_multiplier kind=fp_multiplier members=m1.l3.fp_multiplier
  // UNIT m1.l4.fp_multiplier module=alu_core_u_m1_l4_fp_multiplier kind=fp_multiplier members=m1.l4.fp_multiplier
  // UNIT m1.l5.fp_multiplier module=alu_core_u_m1_l5_fp_multiplier kind=fp_multiplier members=m1.l5.fp_multiplier
  // UNIT m1.l6.fp_multiplier module=alu_core_u_m1_l6_fp_multiplier kind=fp_multiplier members=m1.l6.fp_multiplier
  // UNIT m1.l7.fp_multiplier module=alu_core_u_m1_l7_fp_multiplier kind=fp_multiplier members=m1.l7.fp_multiplier
  // // STRUCTURE m0.l0.fp_adder kind=fp_adder slot=fp_adder mode=0 lane=0 width=40 format=blksfps0e8m0Nefp4e2m1s8 ops=fadd sv=alu_core_u_m0_l0_fp_adder
  // // STRUCTURE m0.l0.quantizer kind=quantizer slot=- mode=0 lane=0 width=40 format=blksfps0e8m0Nefp4e2m1s8 ops=fadd,fmul
  // // STRUCTURE m0.l0.fp_multiplier kind=fp_multiplier slot=fp_multiplier mode=0 lane=0 width=40 format=blksfps0e8m0Nefp4e2m1s8 ops=fmul sv=alu_core_u_m0_l0_fp_multiplier
  // // STRUCTURE m1.l0.fp_adder kind=fp_adder slot=fp_adder mode=1 lane=0 width=8 format=fp8e4m3 ops=fadd sv=alu_core_u_m1_l0_fp_adder
  // // STRUCTURE m1.l1.fp_adder kind=fp_adder slot=fp_adder mode=1 lane=1 width=8 format=fp8e4m3 ops=fadd sv=alu_core_u_m1_l1_fp_adder
  // // STRUCTURE m1.l2.fp_adder kind=fp_adder slot=fp_adder mode=1 lane=2 width=8 format=fp8e4m3 ops=fadd sv=alu_core_u_m1_l2_fp_adder
  // // STRUCTURE m1.l3.fp_adder kind=fp_adder slot=fp_adder mode=1 lane=3 width=8 format=fp8e4m3 ops=fadd sv=alu_core_u_m1_l3_fp_adder
  // // STRUCTURE m1.l4.fp_adder kind=fp_adder slot=fp_adder mode=1 lane=4 width=8 format=fp8e4m3 ops=fadd sv=alu_core_u_m1_l4_fp_adder
  // // STRUCTURE m1.l5.fp_adder kind=fp_adder slot=fp_adder mode=1 lane=5 width=8 format=fp8e4m3 ops=fadd sv=alu_core_u_m1_l5_fp_adder
  // // STRUCTURE m1.l6.fp_adder kind=fp_adder slot=fp_adder mode=1 lane=6 width=8 format=fp8e4m3 ops=fadd sv=alu_core_u_m1_l6_fp_adder
  // // STRUCTURE m1.l7.fp_adder kind=fp_adder slot=fp_adder mode=1 lane=7 width=8 format=fp8e4m3 ops=fadd sv=alu_core_u_m1_l7_fp_adder
  // // STRUCTURE m1.l0.unpacker kind=unpacker slot=unpacker mode=1 lane=0 width=8 format=fp8e4m3 ops=fadd,fmul sv=alu_core_u_m1_l0_unpacker
  // // STRUCTURE m1.l0.rounder kind=rounder slot=rounder mode=1 lane=0 width=8 format=fp8e4m3 ops=fadd,fmul sv=alu_core_u_m1_l0_rounder
  // // STRUCTURE m1.l0.fp_fma kind=fp_fma slot=fp_fma mode=1 lane=0 width=8 format=fp8e4m3 ops=fadd,fmul
  // // STRUCTURE m1.l1.unpacker kind=unpacker slot=unpacker mode=1 lane=1 width=8 format=fp8e4m3 ops=fadd,fmul sv=alu_core_u_m1_l1_unpacker
  // // STRUCTURE m1.l1.rounder kind=rounder slot=rounder mode=1 lane=1 width=8 format=fp8e4m3 ops=fadd,fmul sv=alu_core_u_m1_l1_rounder
  // // STRUCTURE m1.l1.fp_fma kind=fp_fma slot=fp_fma mode=1 lane=1 width=8 format=fp8e4m3 ops=fadd,fmul
  // // STRUCTURE m1.l2.unpacker kind=unpacker slot=unpacker mode=1 lane=2 width=8 format=fp8e4m3 ops=fadd,fmul sv=alu_core_u_m1_l2_unpacker
  // // STRUCTURE m1.l2.rounder kind=rounder slot=rounder mode=1 lane=2 width=8 format=fp8e4m3 ops=fadd,fmul sv=alu_core_u_m1_l2_rounder
  // // STRUCTURE m1.l2.fp_fma kind=fp_fma slot=fp_fma mode=1 lane=2 width=8 format=fp8e4m3 ops=fadd,fmul
  // // STRUCTURE m1.l3.unpacker kind=unpacker slot=unpacker mode=1 lane=3 width=8 format=fp8e4m3 ops=fadd,fmul sv=alu_core_u_m1_l3_unpacker
  // // STRUCTURE m1.l3.rounder kind=rounder slot=rounder mode=1 lane=3 width=8 format=fp8e4m3 ops=fadd,fmul sv=alu_core_u_m1_l3_rounder
  // // STRUCTURE m1.l3.fp_fma kind=fp_fma slot=fp_fma mode=1 lane=3 width=8 format=fp8e4m3 ops=fadd,fmul
  // // STRUCTURE m1.l4.unpacker kind=unpacker slot=unpacker mode=1 lane=4 width=8 format=fp8e4m3 ops=fadd,fmul sv=alu_core_u_m1_l4_unpacker
  // // STRUCTURE m1.l4.rounder kind=rounder slot=rounder mode=1 lane=4 width=8 format=fp8e4m3 ops=fadd,fmul sv=alu_core_u_m1_l4_rounder
  // // STRUCTURE m1.l4.fp_fma kind=fp_fma slot=fp_fma mode=1 lane=4 width=8 format=fp8e4m3 ops=fadd,fmul
  // // STRUCTURE m1.l5.unpacker kind=unpacker slot=unpacker mode=1 lane=5 width=8 format=fp8e4m3 ops=fadd,fmul sv=alu_core_u_m1_l5_unpacker
  // // STRUCTURE m1.l5.rounder kind=rounder slot=rounder mode=1 lane=5 width=8 format=fp8e4m3 ops=fadd,fmul sv=alu_core_u_m1_l5_rounder
  // // STRUCTURE m1.l5.fp_fma kind=fp_fma slot=fp_fma mode=1 lane=5 width=8 format=fp8e4m3 ops=fadd,fmul
  // // STRUCTURE m1.l6.unpacker kind=unpacker slot=unpacker mode=1 lane=6 width=8 format=fp8e4m3 ops=fadd,fmul sv=alu_core_u_m1_l6_unpacker
  // // STRUCTURE m1.l6.rounder kind=rounder slot=rounder mode=1 lane=6 width=8 format=fp8e4m3 ops=fadd,fmul sv=alu_core_u_m1_l6_rounder
  // // STRUCTURE m1.l6.fp_fma kind=fp_fma slot=fp_fma mode=1 lane=6 width=8 format=fp8e4m3 ops=fadd,fmul
  // // STRUCTURE m1.l7.unpacker kind=unpacker slot=unpacker mode=1 lane=7 width=8 format=fp8e4m3 ops=fadd,fmul sv=alu_core_u_m1_l7_unpacker
  // // STRUCTURE m1.l7.rounder kind=rounder slot=rounder mode=1 lane=7 width=8 format=fp8e4m3 ops=fadd,fmul sv=alu_core_u_m1_l7_rounder
  // // STRUCTURE m1.l7.fp_fma kind=fp_fma slot=fp_fma mode=1 lane=7 width=8 format=fp8e4m3 ops=fadd,fmul
  // // STRUCTURE m1.l0.fp_multiplier kind=fp_multiplier slot=fp_multiplier mode=1 lane=0 width=8 format=fp8e4m3 ops=fmul sv=alu_core_u_m1_l0_fp_multiplier
  // // STRUCTURE m1.l1.fp_multiplier kind=fp_multiplier slot=fp_multiplier mode=1 lane=1 width=8 format=fp8e4m3 ops=fmul sv=alu_core_u_m1_l1_fp_multiplier
  // // STRUCTURE m1.l2.fp_multiplier kind=fp_multiplier slot=fp_multiplier mode=1 lane=2 width=8 format=fp8e4m3 ops=fmul sv=alu_core_u_m1_l2_fp_multiplier
  // // STRUCTURE m1.l3.fp_multiplier kind=fp_multiplier slot=fp_multiplier mode=1 lane=3 width=8 format=fp8e4m3 ops=fmul sv=alu_core_u_m1_l3_fp_multiplier
  // // STRUCTURE m1.l4.fp_multiplier kind=fp_multiplier slot=fp_multiplier mode=1 lane=4 width=8 format=fp8e4m3 ops=fmul sv=alu_core_u_m1_l4_fp_multiplier
  // // STRUCTURE m1.l5.fp_multiplier kind=fp_multiplier slot=fp_multiplier mode=1 lane=5 width=8 format=fp8e4m3 ops=fmul sv=alu_core_u_m1_l5_fp_multiplier
  // // STRUCTURE m1.l6.fp_multiplier kind=fp_multiplier slot=fp_multiplier mode=1 lane=6 width=8 format=fp8e4m3 ops=fmul sv=alu_core_u_m1_l6_fp_multiplier
  // // STRUCTURE m1.l7.fp_multiplier kind=fp_multiplier slot=fp_multiplier mode=1 lane=7 width=8 format=fp8e4m3 ops=fmul sv=alu_core_u_m1_l7_fp_multiplier
  // LIBRARY: fam_adder_ripple_carry, fam_adder_ripple_chunk, fam_count_lzd_pair_cell_binary_count_vflat_w12, fam_count_lzd_pair_cell_binary_count_vflat_w4, fam_fp_add_single_path_x12e12s4_p9d459d224988, fam_fp_mul_sig_mul_then_round_x12e12s4_pbd766efe148c, fam_fp_round_dedicated_per_op_increment_adder_fp8e4m3_x12e12s4_pd77ccc5b5c45, fam_fp_unpack_per_unit_unpack_fp8e4m3_x12e12s4_p9bfe39588414, fam_incr_prefix_and, fam_mul_behavioral_star_w4_u_pfc463c41, fam_shift_barrel_mux_tree, fam_shift_keep_mask, fam_shift_stage (chialu.targets.rtl.families: the modules of the declared families the lane modules instantiate; their text follows the generated modules)
  logic [2:0] rnd_sel;
  logic [2:0] rnd;
  logic daz;
  logic ftz;
  logic dual;
  logic [63:0] y_m0_m0_l0_fp_adder;
  logic [79:0] fl_m0_m0_l0_fp_adder;
  logic [63:0] y_m0_m0_l0_fp_multiplier;
  logic [79:0] fl_m0_m0_l0_fp_multiplier;
  logic [63:0] y_m0;
  logic [79:0] fl_m0;
  logic [63:0] y_m1_m1_l0_fp_adder;
  logic [79:0] fl_m1_m1_l0_fp_adder;
  logic [223:0] x_m1_m1_m1_l0_fp_adder;
  logic [63:0] y_m1_m1_l1_fp_adder;
  logic [79:0] fl_m1_m1_l1_fp_adder;
  logic [223:0] x_m1_m1_m1_l1_fp_adder;
  logic [63:0] y_m1_m1_l2_fp_adder;
  logic [79:0] fl_m1_m1_l2_fp_adder;
  logic [223:0] x_m1_m1_m1_l2_fp_adder;
  logic [63:0] y_m1_m1_l3_fp_adder;
  logic [79:0] fl_m1_m1_l3_fp_adder;
  logic [223:0] x_m1_m1_m1_l3_fp_adder;
  logic [63:0] y_m1_m1_l4_fp_adder;
  logic [79:0] fl_m1_m1_l4_fp_adder;
  logic [223:0] x_m1_m1_m1_l4_fp_adder;
  logic [63:0] y_m1_m1_l5_fp_adder;
  logic [79:0] fl_m1_m1_l5_fp_adder;
  logic [223:0] x_m1_m1_m1_l5_fp_adder;
  logic [63:0] y_m1_m1_l6_fp_adder;
  logic [79:0] fl_m1_m1_l6_fp_adder;
  logic [223:0] x_m1_m1_m1_l6_fp_adder;
  logic [63:0] y_m1_m1_l7_fp_adder;
  logic [79:0] fl_m1_m1_l7_fp_adder;
  logic [223:0] x_m1_m1_m1_l7_fp_adder;
  logic [223:0] xa_m1_m1_m1_l0_unpacker;
  logic [223:0] xb_m1_m1_m1_l0_unpacker;
  logic [7:0] dena_m1_m1_m1_l0_unpacker;
  logic [7:0] denb_m1_m1_m1_l0_unpacker;
  logic [63:0] y_m1_m1_l0_rounder;
  logic [79:0] fl_m1_m1_l0_rounder;
  logic [223:0] xa_m1_m1_m1_l1_unpacker;
  logic [223:0] xb_m1_m1_m1_l1_unpacker;
  logic [7:0] dena_m1_m1_m1_l1_unpacker;
  logic [7:0] denb_m1_m1_m1_l1_unpacker;
  logic [63:0] y_m1_m1_l1_rounder;
  logic [79:0] fl_m1_m1_l1_rounder;
  logic [223:0] xa_m1_m1_m1_l2_unpacker;
  logic [223:0] xb_m1_m1_m1_l2_unpacker;
  logic [7:0] dena_m1_m1_m1_l2_unpacker;
  logic [7:0] denb_m1_m1_m1_l2_unpacker;
  logic [63:0] y_m1_m1_l2_rounder;
  logic [79:0] fl_m1_m1_l2_rounder;
  logic [223:0] xa_m1_m1_m1_l3_unpacker;
  logic [223:0] xb_m1_m1_m1_l3_unpacker;
  logic [7:0] dena_m1_m1_m1_l3_unpacker;
  logic [7:0] denb_m1_m1_m1_l3_unpacker;
  logic [63:0] y_m1_m1_l3_rounder;
  logic [79:0] fl_m1_m1_l3_rounder;
  logic [223:0] xa_m1_m1_m1_l4_unpacker;
  logic [223:0] xb_m1_m1_m1_l4_unpacker;
  logic [7:0] dena_m1_m1_m1_l4_unpacker;
  logic [7:0] denb_m1_m1_m1_l4_unpacker;
  logic [63:0] y_m1_m1_l4_rounder;
  logic [79:0] fl_m1_m1_l4_rounder;
  logic [223:0] xa_m1_m1_m1_l5_unpacker;
  logic [223:0] xb_m1_m1_m1_l5_unpacker;
  logic [7:0] dena_m1_m1_m1_l5_unpacker;
  logic [7:0] denb_m1_m1_m1_l5_unpacker;
  logic [63:0] y_m1_m1_l5_rounder;
  logic [79:0] fl_m1_m1_l5_rounder;
  logic [223:0] xa_m1_m1_m1_l6_unpacker;
  logic [223:0] xb_m1_m1_m1_l6_unpacker;
  logic [7:0] dena_m1_m1_m1_l6_unpacker;
  logic [7:0] denb_m1_m1_m1_l6_unpacker;
  logic [63:0] y_m1_m1_l6_rounder;
  logic [79:0] fl_m1_m1_l6_rounder;
  logic [223:0] xa_m1_m1_m1_l7_unpacker;
  logic [223:0] xb_m1_m1_m1_l7_unpacker;
  logic [7:0] dena_m1_m1_m1_l7_unpacker;
  logic [7:0] denb_m1_m1_m1_l7_unpacker;
  logic [63:0] y_m1_m1_l7_rounder;
  logic [79:0] fl_m1_m1_l7_rounder;
  logic [63:0] y_m1_m1_l0_fp_multiplier;
  logic [79:0] fl_m1_m1_l0_fp_multiplier;
  logic [223:0] x_m1_m1_m1_l0_fp_multiplier;
  logic [63:0] y_m1_m1_l1_fp_multiplier;
  logic [79:0] fl_m1_m1_l1_fp_multiplier;
  logic [223:0] x_m1_m1_m1_l1_fp_multiplier;
  logic [63:0] y_m1_m1_l2_fp_multiplier;
  logic [79:0] fl_m1_m1_l2_fp_multiplier;
  logic [223:0] x_m1_m1_m1_l2_fp_multiplier;
  logic [63:0] y_m1_m1_l3_fp_multiplier;
  logic [79:0] fl_m1_m1_l3_fp_multiplier;
  logic [223:0] x_m1_m1_m1_l3_fp_multiplier;
  logic [63:0] y_m1_m1_l4_fp_multiplier;
  logic [79:0] fl_m1_m1_l4_fp_multiplier;
  logic [223:0] x_m1_m1_m1_l4_fp_multiplier;
  logic [63:0] y_m1_m1_l5_fp_multiplier;
  logic [79:0] fl_m1_m1_l5_fp_multiplier;
  logic [223:0] x_m1_m1_m1_l5_fp_multiplier;
  logic [63:0] y_m1_m1_l6_fp_multiplier;
  logic [79:0] fl_m1_m1_l6_fp_multiplier;
  logic [223:0] x_m1_m1_m1_l6_fp_multiplier;
  logic [63:0] y_m1_m1_l7_fp_multiplier;
  logic [79:0] fl_m1_m1_l7_fp_multiplier;
  logic [223:0] x_m1_m1_m1_l7_fp_multiplier;
  logic [63:0] y_m1;
  logic [79:0] fl_m1;
  logic [223:0] x_m1;
  logic [223:0] xa_m1;
  logic [223:0] xb_m1;
  logic [7:0] dena_m1;
  logic [7:0] denb_m1;
  logic [79:0] fl_all;
  assign rnd_sel = 3'd0;
  assign rnd = rnd_sel;
  assign daz = 1'b0;
  assign ftz = 1'b0;
  assign dual = 1'b0;
  assign y_m0 = y_m0_m0_l0_fp_adder | y_m0_m0_l0_fp_multiplier;
  assign fl_m0 = fl_m0_m0_l0_fp_adder | fl_m0_m0_l0_fp_multiplier;
  assign y_m1 = y_m1_m1_l0_fp_adder | y_m1_m1_l1_fp_adder | y_m1_m1_l2_fp_adder | y_m1_m1_l3_fp_adder | y_m1_m1_l4_fp_adder | y_m1_m1_l5_fp_adder | y_m1_m1_l6_fp_adder | y_m1_m1_l7_fp_adder | y_m1_m1_l0_rounder | y_m1_m1_l1_rounder | y_m1_m1_l2_rounder | y_m1_m1_l3_rounder | y_m1_m1_l4_rounder | y_m1_m1_l5_rounder | y_m1_m1_l6_rounder | y_m1_m1_l7_rounder | y_m1_m1_l0_fp_multiplier | y_m1_m1_l1_fp_multiplier | y_m1_m1_l2_fp_multiplier | y_m1_m1_l3_fp_multiplier | y_m1_m1_l4_fp_multiplier | y_m1_m1_l5_fp_multiplier | y_m1_m1_l6_fp_multiplier | y_m1_m1_l7_fp_multiplier;
  assign fl_m1 = fl_m1_m1_l0_fp_adder | fl_m1_m1_l1_fp_adder | fl_m1_m1_l2_fp_adder | fl_m1_m1_l3_fp_adder | fl_m1_m1_l4_fp_adder | fl_m1_m1_l5_fp_adder | fl_m1_m1_l6_fp_adder | fl_m1_m1_l7_fp_adder | fl_m1_m1_l0_rounder | fl_m1_m1_l1_rounder | fl_m1_m1_l2_rounder | fl_m1_m1_l3_rounder | fl_m1_m1_l4_rounder | fl_m1_m1_l5_rounder | fl_m1_m1_l6_rounder | fl_m1_m1_l7_rounder | fl_m1_m1_l0_fp_multiplier | fl_m1_m1_l1_fp_multiplier | fl_m1_m1_l2_fp_multiplier | fl_m1_m1_l3_fp_multiplier | fl_m1_m1_l4_fp_multiplier | fl_m1_m1_l5_fp_multiplier | fl_m1_m1_l6_fp_multiplier | fl_m1_m1_l7_fp_multiplier;
  assign x_m1 = x_m1_m1_m1_l0_fp_adder | x_m1_m1_m1_l1_fp_adder | x_m1_m1_m1_l2_fp_adder | x_m1_m1_m1_l3_fp_adder | x_m1_m1_m1_l4_fp_adder | x_m1_m1_m1_l5_fp_adder | x_m1_m1_m1_l6_fp_adder | x_m1_m1_m1_l7_fp_adder | x_m1_m1_m1_l0_fp_multiplier | x_m1_m1_m1_l1_fp_multiplier | x_m1_m1_m1_l2_fp_multiplier | x_m1_m1_m1_l3_fp_multiplier | x_m1_m1_m1_l4_fp_multiplier | x_m1_m1_m1_l5_fp_multiplier | x_m1_m1_m1_l6_fp_multiplier | x_m1_m1_m1_l7_fp_multiplier;
  assign xa_m1 = xa_m1_m1_m1_l0_unpacker | xa_m1_m1_m1_l1_unpacker | xa_m1_m1_m1_l2_unpacker | xa_m1_m1_m1_l3_unpacker | xa_m1_m1_m1_l4_unpacker | xa_m1_m1_m1_l5_unpacker | xa_m1_m1_m1_l6_unpacker | xa_m1_m1_m1_l7_unpacker;
  assign xb_m1 = xb_m1_m1_m1_l0_unpacker | xb_m1_m1_m1_l1_unpacker | xb_m1_m1_m1_l2_unpacker | xb_m1_m1_m1_l3_unpacker | xb_m1_m1_m1_l4_unpacker | xb_m1_m1_m1_l5_unpacker | xb_m1_m1_m1_l6_unpacker | xb_m1_m1_m1_l7_unpacker;
  assign dena_m1 = dena_m1_m1_m1_l0_unpacker | dena_m1_m1_m1_l1_unpacker | dena_m1_m1_m1_l2_unpacker | dena_m1_m1_m1_l3_unpacker | dena_m1_m1_m1_l4_unpacker | dena_m1_m1_m1_l5_unpacker | dena_m1_m1_m1_l6_unpacker | dena_m1_m1_m1_l7_unpacker;
  assign denb_m1 = denb_m1_m1_m1_l0_unpacker | denb_m1_m1_m1_l1_unpacker | denb_m1_m1_m1_l2_unpacker | denb_m1_m1_m1_l3_unpacker | denb_m1_m1_m1_l4_unpacker | denb_m1_m1_m1_l5_unpacker | denb_m1_m1_m1_l6_unpacker | denb_m1_m1_m1_l7_unpacker;
  alu_core_u_m0_l0_fp_adder u_m0_l0_fp_adder (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_m0_l0_fp_adder), .fl_m0(fl_m0_m0_l0_fp_adder));
  alu_core_u_m0_l0_fp_multiplier u_m0_l0_fp_multiplier (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_m0_l0_fp_multiplier), .fl_m0(fl_m0_m0_l0_fp_multiplier));
  alu_core_u_m1_l0_fp_adder u_m1_l0_fp_adder (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l0_fp_adder), .fl_m1(fl_m1_m1_l0_fp_adder), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1_m1_m1_l0_fp_adder));
  alu_core_u_m1_l1_fp_adder u_m1_l1_fp_adder (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l1_fp_adder), .fl_m1(fl_m1_m1_l1_fp_adder), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1_m1_m1_l1_fp_adder));
  alu_core_u_m1_l2_fp_adder u_m1_l2_fp_adder (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l2_fp_adder), .fl_m1(fl_m1_m1_l2_fp_adder), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1_m1_m1_l2_fp_adder));
  alu_core_u_m1_l3_fp_adder u_m1_l3_fp_adder (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l3_fp_adder), .fl_m1(fl_m1_m1_l3_fp_adder), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1_m1_m1_l3_fp_adder));
  alu_core_u_m1_l4_fp_adder u_m1_l4_fp_adder (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l4_fp_adder), .fl_m1(fl_m1_m1_l4_fp_adder), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1_m1_m1_l4_fp_adder));
  alu_core_u_m1_l5_fp_adder u_m1_l5_fp_adder (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l5_fp_adder), .fl_m1(fl_m1_m1_l5_fp_adder), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1_m1_m1_l5_fp_adder));
  alu_core_u_m1_l6_fp_adder u_m1_l6_fp_adder (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l6_fp_adder), .fl_m1(fl_m1_m1_l6_fp_adder), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1_m1_m1_l6_fp_adder));
  alu_core_u_m1_l7_fp_adder u_m1_l7_fp_adder (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l7_fp_adder), .fl_m1(fl_m1_m1_l7_fp_adder), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1_m1_m1_l7_fp_adder));
  alu_core_u_m1_l0_unpacker u_m1_l0_unpacker (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .xa_m1(xa_m1_m1_m1_l0_unpacker), .xb_m1(xb_m1_m1_m1_l0_unpacker), .dena_m1(dena_m1_m1_m1_l0_unpacker), .denb_m1(denb_m1_m1_m1_l0_unpacker));
  alu_core_u_m1_l0_rounder u_m1_l0_rounder (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l0_rounder), .fl_m1(fl_m1_m1_l0_rounder), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1));
  alu_core_u_m1_l1_unpacker u_m1_l1_unpacker (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .xa_m1(xa_m1_m1_m1_l1_unpacker), .xb_m1(xb_m1_m1_m1_l1_unpacker), .dena_m1(dena_m1_m1_m1_l1_unpacker), .denb_m1(denb_m1_m1_m1_l1_unpacker));
  alu_core_u_m1_l1_rounder u_m1_l1_rounder (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l1_rounder), .fl_m1(fl_m1_m1_l1_rounder), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1));
  alu_core_u_m1_l2_unpacker u_m1_l2_unpacker (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .xa_m1(xa_m1_m1_m1_l2_unpacker), .xb_m1(xb_m1_m1_m1_l2_unpacker), .dena_m1(dena_m1_m1_m1_l2_unpacker), .denb_m1(denb_m1_m1_m1_l2_unpacker));
  alu_core_u_m1_l2_rounder u_m1_l2_rounder (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l2_rounder), .fl_m1(fl_m1_m1_l2_rounder), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1));
  alu_core_u_m1_l3_unpacker u_m1_l3_unpacker (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .xa_m1(xa_m1_m1_m1_l3_unpacker), .xb_m1(xb_m1_m1_m1_l3_unpacker), .dena_m1(dena_m1_m1_m1_l3_unpacker), .denb_m1(denb_m1_m1_m1_l3_unpacker));
  alu_core_u_m1_l3_rounder u_m1_l3_rounder (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l3_rounder), .fl_m1(fl_m1_m1_l3_rounder), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1));
  alu_core_u_m1_l4_unpacker u_m1_l4_unpacker (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .xa_m1(xa_m1_m1_m1_l4_unpacker), .xb_m1(xb_m1_m1_m1_l4_unpacker), .dena_m1(dena_m1_m1_m1_l4_unpacker), .denb_m1(denb_m1_m1_m1_l4_unpacker));
  alu_core_u_m1_l4_rounder u_m1_l4_rounder (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l4_rounder), .fl_m1(fl_m1_m1_l4_rounder), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1));
  alu_core_u_m1_l5_unpacker u_m1_l5_unpacker (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .xa_m1(xa_m1_m1_m1_l5_unpacker), .xb_m1(xb_m1_m1_m1_l5_unpacker), .dena_m1(dena_m1_m1_m1_l5_unpacker), .denb_m1(denb_m1_m1_m1_l5_unpacker));
  alu_core_u_m1_l5_rounder u_m1_l5_rounder (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l5_rounder), .fl_m1(fl_m1_m1_l5_rounder), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1));
  alu_core_u_m1_l6_unpacker u_m1_l6_unpacker (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .xa_m1(xa_m1_m1_m1_l6_unpacker), .xb_m1(xb_m1_m1_m1_l6_unpacker), .dena_m1(dena_m1_m1_m1_l6_unpacker), .denb_m1(denb_m1_m1_m1_l6_unpacker));
  alu_core_u_m1_l6_rounder u_m1_l6_rounder (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l6_rounder), .fl_m1(fl_m1_m1_l6_rounder), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1));
  alu_core_u_m1_l7_unpacker u_m1_l7_unpacker (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .xa_m1(xa_m1_m1_m1_l7_unpacker), .xb_m1(xb_m1_m1_m1_l7_unpacker), .dena_m1(dena_m1_m1_m1_l7_unpacker), .denb_m1(denb_m1_m1_m1_l7_unpacker));
  alu_core_u_m1_l7_rounder u_m1_l7_rounder (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l7_rounder), .fl_m1(fl_m1_m1_l7_rounder), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1));
  alu_core_u_m1_l0_fp_multiplier u_m1_l0_fp_multiplier (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l0_fp_multiplier), .fl_m1(fl_m1_m1_l0_fp_multiplier), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1_m1_m1_l0_fp_multiplier));
  alu_core_u_m1_l1_fp_multiplier u_m1_l1_fp_multiplier (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l1_fp_multiplier), .fl_m1(fl_m1_m1_l1_fp_multiplier), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1_m1_m1_l1_fp_multiplier));
  alu_core_u_m1_l2_fp_multiplier u_m1_l2_fp_multiplier (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l2_fp_multiplier), .fl_m1(fl_m1_m1_l2_fp_multiplier), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1_m1_m1_l2_fp_multiplier));
  alu_core_u_m1_l3_fp_multiplier u_m1_l3_fp_multiplier (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l3_fp_multiplier), .fl_m1(fl_m1_m1_l3_fp_multiplier), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1_m1_m1_l3_fp_multiplier));
  alu_core_u_m1_l4_fp_multiplier u_m1_l4_fp_multiplier (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l4_fp_multiplier), .fl_m1(fl_m1_m1_l4_fp_multiplier), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1_m1_m1_l4_fp_multiplier));
  alu_core_u_m1_l5_fp_multiplier u_m1_l5_fp_multiplier (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l5_fp_multiplier), .fl_m1(fl_m1_m1_l5_fp_multiplier), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1_m1_m1_l5_fp_multiplier));
  alu_core_u_m1_l6_fp_multiplier u_m1_l6_fp_multiplier (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l6_fp_multiplier), .fl_m1(fl_m1_m1_l6_fp_multiplier), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1_m1_m1_l6_fp_multiplier));
  alu_core_u_m1_l7_fp_multiplier u_m1_l7_fp_multiplier (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l7_fp_multiplier), .fl_m1(fl_m1_m1_l7_fp_multiplier), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1_m1_m1_l7_fp_multiplier));
  always_comb begin
    case (mode)
      1'd0: begin y = y_m0; fl_all = fl_m0; end
      1'd1: begin y = y_m1; fl_all = fl_m1; end
      default: begin y = '0; fl_all = '0; end
    endcase
  end
endmodule
// EVOLVE-BLOCK-END

module alu_core_m0_fp_adder #(parameter int LANE = 0) (
  input  logic [63:0] a,
  input  logic [63:0] b,
  input  logic [0:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [63:0] y_m0,
  output logic [79:0] fl_m0
);
  // alu_core_m0_fp_adder: lane LANE of mode 0 (blksfps0e8m0Nefp4e2m1s8) for the fp_adder ops fadd; the result buses are the mode's, with only this lane's bits written
  import alu_core_m0_pkg::*;
  logic d_m0;
  logic [39:0] m0_aLANE;
  logic [39:0] m0_bLANE;
  logic [183:0] m0_uaLANE;
  logic [183:0] m0_ubLANE;
  logic [29:0] m0_xa [0:7];
  logic m0_dena [0:7];
  logic [29:0] m0_xb [0:7];
  logic m0_denb [0:7];
  logic [239:0] m0_o0q0_LANE_xs;
  logic [119:0] m0_o0q0_LANE;
  logic [79:0] m0_o0q0_LANE_pf;
  logic [29:0] m0_o0q0_LANE_x0;
  logic [29:0] m0_o0q0_LANE_x1;
  logic [29:0] m0_o0q0_LANE_x2;
  logic [29:0] m0_o0q0_LANE_x3;
  logic [29:0] m0_o0q0_LANE_x4;
  logic [29:0] m0_o0q0_LANE_x5;
  logic [29:0] m0_o0q0_LANE_x6;
  logic [29:0] m0_o0q0_LANE_x7;
  assign m0_aLANE = a[(LANE*40) +: 40];
  assign m0_bLANE = b[(LANE*40) +: 40];
  assign m0_uaLANE = m0_unpack_s(m0_aLANE, daz);
  assign m0_ubLANE = m0_unpack_s(m0_bLANE, daz);
  assign m0_xa[((LANE*8)+0)] = m0_x(m0_uaLANE[0 +: 22]);
  assign m0_dena[((LANE*8)+0)] = m0_uaLANE[22];
  assign m0_xb[((LANE*8)+0)] = m0_x(m0_ubLANE[0 +: 22]);
  assign m0_denb[((LANE*8)+0)] = m0_ubLANE[22];
  assign m0_xa[((LANE*8)+1)] = m0_x(m0_uaLANE[23 +: 22]);
  assign m0_dena[((LANE*8)+1)] = m0_uaLANE[45];
  assign m0_xb[((LANE*8)+1)] = m0_x(m0_ubLANE[23 +: 22]);
  assign m0_denb[((LANE*8)+1)] = m0_ubLANE[45];
  assign m0_xa[((LANE*8)+2)] = m0_x(m0_uaLANE[46 +: 22]);
  assign m0_dena[((LANE*8)+2)] = m0_uaLANE[68];
  assign m0_xb[((LANE*8)+2)] = m0_x(m0_ubLANE[46 +: 22]);
  assign m0_denb[((LANE*8)+2)] = m0_ubLANE[68];
  assign m0_xa[((LANE*8)+3)] = m0_x(m0_uaLANE[69 +: 22]);
  assign m0_dena[((LANE*8)+3)] = m0_uaLANE[91];
  assign m0_xb[((LANE*8)+3)] = m0_x(m0_ubLANE[69 +: 22]);
  assign m0_denb[((LANE*8)+3)] = m0_ubLANE[91];
  assign m0_xa[((LANE*8)+4)] = m0_x(m0_uaLANE[92 +: 22]);
  assign m0_dena[((LANE*8)+4)] = m0_uaLANE[114];
  assign m0_xb[((LANE*8)+4)] = m0_x(m0_ubLANE[92 +: 22]);
  assign m0_denb[((LANE*8)+4)] = m0_ubLANE[114];
  assign m0_xa[((LANE*8)+5)] = m0_x(m0_uaLANE[115 +: 22]);
  assign m0_dena[((LANE*8)+5)] = m0_uaLANE[137];
  assign m0_xb[((LANE*8)+5)] = m0_x(m0_ubLANE[115 +: 22]);
  assign m0_denb[((LANE*8)+5)] = m0_ubLANE[137];
  assign m0_xa[((LANE*8)+6)] = m0_x(m0_uaLANE[138 +: 22]);
  assign m0_dena[((LANE*8)+6)] = m0_uaLANE[160];
  assign m0_xb[((LANE*8)+6)] = m0_x(m0_ubLANE[138 +: 22]);
  assign m0_denb[((LANE*8)+6)] = m0_ubLANE[160];
  assign m0_xa[((LANE*8)+7)] = m0_x(m0_uaLANE[161 +: 22]);
  assign m0_dena[((LANE*8)+7)] = m0_uaLANE[183];
  assign m0_xb[((LANE*8)+7)] = m0_x(m0_ubLANE[161 +: 22]);
  assign m0_denb[((LANE*8)+7)] = m0_ubLANE[183];
  always_comb begin
    y_m0 = '0; d_m0 = '0; fl_m0 = '0;
    m0_o0q0_LANE_xs = 'x; m0_o0q0_LANE = 'x; m0_o0q0_LANE_pf = 'x; m0_o0q0_LANE_x0 = 'x; m0_o0q0_LANE_x1 = 'x; m0_o0q0_LANE_x2 = 'x;
    m0_o0q0_LANE_x3 = 'x; m0_o0q0_LANE_x4 = 'x; m0_o0q0_LANE_x5 = 'x; m0_o0q0_LANE_x6 = 'x; m0_o0q0_LANE_x7 = 'x;
    case (op)
      1'd0: begin
        m0_o0q0_LANE_pf = 0;
        m0_o0q0_LANE_x0 = m0_add(m0_xa[((LANE*8)+0)], m0_xb[((LANE*8)+0)], 1'b0);
        m0_o0q0_LANE_xs[0 +: 30] = { m0_o0q0_LANE_x0[29:28], (m0_o0q0_LANE_x0[29:28] == 2'd0 && m0_o0q0_LANE_x0[10:0] == 0) ? (((m0_xa[((LANE*8)+0)][29:28] == 2'd0 && m0_xa[((LANE*8)+0)][10:0] == 0) && (m0_xb[((LANE*8)+0)][29:28] == 2'd0 && m0_xb[((LANE*8)+0)][10:0] == 0)) ? ((rnd == 3'd2) ? (m0_xa[((LANE*8)+0)][27] | (m0_xb[((LANE*8)+0)][27] ^ 1'b0)) : (m0_xa[((LANE*8)+0)][27] & (m0_xb[((LANE*8)+0)][27] ^ 1'b0))) : ((rnd == 3'd2) ? 1'b1 : 1'b0)) : m0_o0q0_LANE_x0[27], m0_o0q0_LANE_x0[26:0] };
        m0_o0q0_LANE_pf[0 +: 10] = ((m0_dena[((LANE*8)+0)] | m0_denb[((LANE*8)+0)]) ? (10'd1 << 6) : 10'd0) | (1'b0 || 1'b0 || ((m0_o0q0_LANE_xs[28 +: 2] == 2'd1) && !((m0_xa[((LANE*8)+0)][29:28] == 2'd1) || (m0_xb[((LANE*8)+0)][29:28] == 2'd1))) ? (10'd1 << 0) : 10'd0);
        m0_o0q0_LANE_x1 = m0_add(m0_xa[((LANE*8)+1)], m0_xb[((LANE*8)+1)], 1'b0);
        m0_o0q0_LANE_xs[30 +: 30] = { m0_o0q0_LANE_x1[29:28], (m0_o0q0_LANE_x1[29:28] == 2'd0 && m0_o0q0_LANE_x1[10:0] == 0) ? (((m0_xa[((LANE*8)+1)][29:28] == 2'd0 && m0_xa[((LANE*8)+1)][10:0] == 0) && (m0_xb[((LANE*8)+1)][29:28] == 2'd0 && m0_xb[((LANE*8)+1)][10:0] == 0)) ? ((rnd == 3'd2) ? (m0_xa[((LANE*8)+1)][27] | (m0_xb[((LANE*8)+1)][27] ^ 1'b0)) : (m0_xa[((LANE*8)+1)][27] & (m0_xb[((LANE*8)+1)][27] ^ 1'b0))) : ((rnd == 3'd2) ? 1'b1 : 1'b0)) : m0_o0q0_LANE_x1[27], m0_o0q0_LANE_x1[26:0] };
        m0_o0q0_LANE_pf[10 +: 10] = ((m0_dena[((LANE*8)+1)] | m0_denb[((LANE*8)+1)]) ? (10'd1 << 6) : 10'd0) | (1'b0 || 1'b0 || ((m0_o0q0_LANE_xs[58 +: 2] == 2'd1) && !((m0_xa[((LANE*8)+1)][29:28] == 2'd1) || (m0_xb[((LANE*8)+1)][29:28] == 2'd1))) ? (10'd1 << 0) : 10'd0);
        m0_o0q0_LANE_x2 = m0_add(m0_xa[((LANE*8)+2)], m0_xb[((LANE*8)+2)], 1'b0);
        m0_o0q0_LANE_xs[60 +: 30] = { m0_o0q0_LANE_x2[29:28], (m0_o0q0_LANE_x2[29:28] == 2'd0 && m0_o0q0_LANE_x2[10:0] == 0) ? (((m0_xa[((LANE*8)+2)][29:28] == 2'd0 && m0_xa[((LANE*8)+2)][10:0] == 0) && (m0_xb[((LANE*8)+2)][29:28] == 2'd0 && m0_xb[((LANE*8)+2)][10:0] == 0)) ? ((rnd == 3'd2) ? (m0_xa[((LANE*8)+2)][27] | (m0_xb[((LANE*8)+2)][27] ^ 1'b0)) : (m0_xa[((LANE*8)+2)][27] & (m0_xb[((LANE*8)+2)][27] ^ 1'b0))) : ((rnd == 3'd2) ? 1'b1 : 1'b0)) : m0_o0q0_LANE_x2[27], m0_o0q0_LANE_x2[26:0] };
        m0_o0q0_LANE_pf[20 +: 10] = ((m0_dena[((LANE*8)+2)] | m0_denb[((LANE*8)+2)]) ? (10'd1 << 6) : 10'd0) | (1'b0 || 1'b0 || ((m0_o0q0_LANE_xs[88 +: 2] == 2'd1) && !((m0_xa[((LANE*8)+2)][29:28] == 2'd1) || (m0_xb[((LANE*8)+2)][29:28] == 2'd1))) ? (10'd1 << 0) : 10'd0);
        m0_o0q0_LANE_x3 = m0_add(m0_xa[((LANE*8)+3)], m0_xb[((LANE*8)+3)], 1'b0);
        m0_o0q0_LANE_xs[90 +: 30] = { m0_o0q0_LANE_x3[29:28], (m0_o0q0_LANE_x3[29:28] == 2'd0 && m0_o0q0_LANE_x3[10:0] == 0) ? (((m0_xa[((LANE*8)+3)][29:28] == 2'd0 && m0_xa[((LANE*8)+3)][10:0] == 0) && (m0_xb[((LANE*8)+3)][29:28] == 2'd0 && m0_xb[((LANE*8)+3)][10:0] == 0)) ? ((rnd == 3'd2) ? (m0_xa[((LANE*8)+3)][27] | (m0_xb[((LANE*8)+3)][27] ^ 1'b0)) : (m0_xa[((LANE*8)+3)][27] & (m0_xb[((LANE*8)+3)][27] ^ 1'b0))) : ((rnd == 3'd2) ? 1'b1 : 1'b0)) : m0_o0q0_LANE_x3[27], m0_o0q0_LANE_x3[26:0] };
        m0_o0q0_LANE_pf[30 +: 10] = ((m0_dena[((LANE*8)+3)] | m0_denb[((LANE*8)+3)]) ? (10'd1 << 6) : 10'd0) | (1'b0 || 1'b0 || ((m0_o0q0_LANE_xs[118 +: 2] == 2'd1) && !((m0_xa[((LANE*8)+3)][29:28] == 2'd1) || (m0_xb[((LANE*8)+3)][29:28] == 2'd1))) ? (10'd1 << 0) : 10'd0);
        m0_o0q0_LANE_x4 = m0_add(m0_xa[((LANE*8)+4)], m0_xb[((LANE*8)+4)], 1'b0);
        m0_o0q0_LANE_xs[120 +: 30] = { m0_o0q0_LANE_x4[29:28], (m0_o0q0_LANE_x4[29:28] == 2'd0 && m0_o0q0_LANE_x4[10:0] == 0) ? (((m0_xa[((LANE*8)+4)][29:28] == 2'd0 && m0_xa[((LANE*8)+4)][10:0] == 0) && (m0_xb[((LANE*8)+4)][29:28] == 2'd0 && m0_xb[((LANE*8)+4)][10:0] == 0)) ? ((rnd == 3'd2) ? (m0_xa[((LANE*8)+4)][27] | (m0_xb[((LANE*8)+4)][27] ^ 1'b0)) : (m0_xa[((LANE*8)+4)][27] & (m0_xb[((LANE*8)+4)][27] ^ 1'b0))) : ((rnd == 3'd2) ? 1'b1 : 1'b0)) : m0_o0q0_LANE_x4[27], m0_o0q0_LANE_x4[26:0] };
        m0_o0q0_LANE_pf[40 +: 10] = ((m0_dena[((LANE*8)+4)] | m0_denb[((LANE*8)+4)]) ? (10'd1 << 6) : 10'd0) | (1'b0 || 1'b0 || ((m0_o0q0_LANE_xs[148 +: 2] == 2'd1) && !((m0_xa[((LANE*8)+4)][29:28] == 2'd1) || (m0_xb[((LANE*8)+4)][29:28] == 2'd1))) ? (10'd1 << 0) : 10'd0);
        m0_o0q0_LANE_x5 = m0_add(m0_xa[((LANE*8)+5)], m0_xb[((LANE*8)+5)], 1'b0);
        m0_o0q0_LANE_xs[150 +: 30] = { m0_o0q0_LANE_x5[29:28], (m0_o0q0_LANE_x5[29:28] == 2'd0 && m0_o0q0_LANE_x5[10:0] == 0) ? (((m0_xa[((LANE*8)+5)][29:28] == 2'd0 && m0_xa[((LANE*8)+5)][10:0] == 0) && (m0_xb[((LANE*8)+5)][29:28] == 2'd0 && m0_xb[((LANE*8)+5)][10:0] == 0)) ? ((rnd == 3'd2) ? (m0_xa[((LANE*8)+5)][27] | (m0_xb[((LANE*8)+5)][27] ^ 1'b0)) : (m0_xa[((LANE*8)+5)][27] & (m0_xb[((LANE*8)+5)][27] ^ 1'b0))) : ((rnd == 3'd2) ? 1'b1 : 1'b0)) : m0_o0q0_LANE_x5[27], m0_o0q0_LANE_x5[26:0] };
        m0_o0q0_LANE_pf[50 +: 10] = ((m0_dena[((LANE*8)+5)] | m0_denb[((LANE*8)+5)]) ? (10'd1 << 6) : 10'd0) | (1'b0 || 1'b0 || ((m0_o0q0_LANE_xs[178 +: 2] == 2'd1) && !((m0_xa[((LANE*8)+5)][29:28] == 2'd1) || (m0_xb[((LANE*8)+5)][29:28] == 2'd1))) ? (10'd1 << 0) : 10'd0);
        m0_o0q0_LANE_x6 = m0_add(m0_xa[((LANE*8)+6)], m0_xb[((LANE*8)+6)], 1'b0);
        m0_o0q0_LANE_xs[180 +: 30] = { m0_o0q0_LANE_x6[29:28], (m0_o0q0_LANE_x6[29:28] == 2'd0 && m0_o0q0_LANE_x6[10:0] == 0) ? (((m0_xa[((LANE*8)+6)][29:28] == 2'd0 && m0_xa[((LANE*8)+6)][10:0] == 0) && (m0_xb[((LANE*8)+6)][29:28] == 2'd0 && m0_xb[((LANE*8)+6)][10:0] == 0)) ? ((rnd == 3'd2) ? (m0_xa[((LANE*8)+6)][27] | (m0_xb[((LANE*8)+6)][27] ^ 1'b0)) : (m0_xa[((LANE*8)+6)][27] & (m0_xb[((LANE*8)+6)][27] ^ 1'b0))) : ((rnd == 3'd2) ? 1'b1 : 1'b0)) : m0_o0q0_LANE_x6[27], m0_o0q0_LANE_x6[26:0] };
        m0_o0q0_LANE_pf[60 +: 10] = ((m0_dena[((LANE*8)+6)] | m0_denb[((LANE*8)+6)]) ? (10'd1 << 6) : 10'd0) | (1'b0 || 1'b0 || ((m0_o0q0_LANE_xs[208 +: 2] == 2'd1) && !((m0_xa[((LANE*8)+6)][29:28] == 2'd1) || (m0_xb[((LANE*8)+6)][29:28] == 2'd1))) ? (10'd1 << 0) : 10'd0);
        m0_o0q0_LANE_x7 = m0_add(m0_xa[((LANE*8)+7)], m0_xb[((LANE*8)+7)], 1'b0);
        m0_o0q0_LANE_xs[210 +: 30] = { m0_o0q0_LANE_x7[29:28], (m0_o0q0_LANE_x7[29:28] == 2'd0 && m0_o0q0_LANE_x7[10:0] == 0) ? (((m0_xa[((LANE*8)+7)][29:28] == 2'd0 && m0_xa[((LANE*8)+7)][10:0] == 0) && (m0_xb[((LANE*8)+7)][29:28] == 2'd0 && m0_xb[((LANE*8)+7)][10:0] == 0)) ? ((rnd == 3'd2) ? (m0_xa[((LANE*8)+7)][27] | (m0_xb[((LANE*8)+7)][27] ^ 1'b0)) : (m0_xa[((LANE*8)+7)][27] & (m0_xb[((LANE*8)+7)][27] ^ 1'b0))) : ((rnd == 3'd2) ? 1'b1 : 1'b0)) : m0_o0q0_LANE_x7[27], m0_o0q0_LANE_x7[26:0] };
        m0_o0q0_LANE_pf[70 +: 10] = ((m0_dena[((LANE*8)+7)] | m0_denb[((LANE*8)+7)]) ? (10'd1 << 6) : 10'd0) | (1'b0 || 1'b0 || ((m0_o0q0_LANE_xs[238 +: 2] == 2'd1) && !((m0_xa[((LANE*8)+7)][29:28] == 2'd1) || (m0_xb[((LANE*8)+7)][29:28] == 2'd1))) ? (10'd1 << 0) : 10'd0);
        m0_o0q0_LANE = m0_quant_blksfps0e8m0Nefp4e2m1s8(m0_o0q0_LANE_xs, rnd, 64'd0, ftz);
        y_m0[((LANE*40)+0) +: 40] = m0_o0q0_LANE[39:0];
        y_m0[((LANE*40)+0) +: 4] = (m0_o0q0_LANE_xs[0 +: 11] == 0 && m0_o0q0_LANE_xs[28 +: 2] == 0) ? {m0_o0q0_LANE_xs[27], 3'd0} : m0_o0q0_LANE[0 +: 4];
        fl_m0[((0+(LANE*8))+0)*10 +: 10] = (m0_o0q0_LANE_pf[0 +: 10] | m0_o0q0_LANE[40 +: 10]);
        y_m0[((LANE*40)+4) +: 4] = (m0_o0q0_LANE_xs[30 +: 11] == 0 && m0_o0q0_LANE_xs[58 +: 2] == 0) ? {m0_o0q0_LANE_xs[57], 3'd0} : m0_o0q0_LANE[4 +: 4];
        fl_m0[((0+(LANE*8))+1)*10 +: 10] = (m0_o0q0_LANE_pf[10 +: 10] | m0_o0q0_LANE[50 +: 10]);
        y_m0[((LANE*40)+8) +: 4] = (m0_o0q0_LANE_xs[60 +: 11] == 0 && m0_o0q0_LANE_xs[88 +: 2] == 0) ? {m0_o0q0_LANE_xs[87], 3'd0} : m0_o0q0_LANE[8 +: 4];
        fl_m0[((0+(LANE*8))+2)*10 +: 10] = (m0_o0q0_LANE_pf[20 +: 10] | m0_o0q0_LANE[60 +: 10]);
        y_m0[((LANE*40)+12) +: 4] = (m0_o0q0_LANE_xs[90 +: 11] == 0 && m0_o0q0_LANE_xs[118 +: 2] == 0) ? {m0_o0q0_LANE_xs[117], 3'd0} : m0_o0q0_LANE[12 +: 4];
        fl_m0[((0+(LANE*8))+3)*10 +: 10] = (m0_o0q0_LANE_pf[30 +: 10] | m0_o0q0_LANE[70 +: 10]);
        y_m0[((LANE*40)+16) +: 4] = (m0_o0q0_LANE_xs[120 +: 11] == 0 && m0_o0q0_LANE_xs[148 +: 2] == 0) ? {m0_o0q0_LANE_xs[147], 3'd0} : m0_o0q0_LANE[16 +: 4];
        fl_m0[((0+(LANE*8))+4)*10 +: 10] = (m0_o0q0_LANE_pf[40 +: 10] | m0_o0q0_LANE[80 +: 10]);
        y_m0[((LANE*40)+20) +: 4] = (m0_o0q0_LANE_xs[150 +: 11] == 0 && m0_o0q0_LANE_xs[178 +: 2] == 0) ? {m0_o0q0_LANE_xs[177], 3'd0} : m0_o0q0_LANE[20 +: 4];
        fl_m0[((0+(LANE*8))+5)*10 +: 10] = (m0_o0q0_LANE_pf[50 +: 10] | m0_o0q0_LANE[90 +: 10]);
        y_m0[((LANE*40)+24) +: 4] = (m0_o0q0_LANE_xs[180 +: 11] == 0 && m0_o0q0_LANE_xs[208 +: 2] == 0) ? {m0_o0q0_LANE_xs[207], 3'd0} : m0_o0q0_LANE[24 +: 4];
        fl_m0[((0+(LANE*8))+6)*10 +: 10] = (m0_o0q0_LANE_pf[60 +: 10] | m0_o0q0_LANE[100 +: 10]);
        y_m0[((LANE*40)+28) +: 4] = (m0_o0q0_LANE_xs[210 +: 11] == 0 && m0_o0q0_LANE_xs[238 +: 2] == 0) ? {m0_o0q0_LANE_xs[237], 3'd0} : m0_o0q0_LANE[28 +: 4];
        fl_m0[((0+(LANE*8))+7)*10 +: 10] = (m0_o0q0_LANE_pf[70 +: 10] | m0_o0q0_LANE[110 +: 10]);
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m0_fp_multiplier #(parameter int LANE = 0) (
  input  logic [63:0] a,
  input  logic [63:0] b,
  input  logic [0:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [63:0] y_m0,
  output logic [79:0] fl_m0
);
  // alu_core_m0_fp_multiplier: lane LANE of mode 0 (blksfps0e8m0Nefp4e2m1s8) for the fp_multiplier ops fmul; the result buses are the mode's, with only this lane's bits written
  import alu_core_m0_pkg::*;
  logic d_m0;
  logic [39:0] m0_aLANE;
  logic [39:0] m0_bLANE;
  logic [183:0] m0_uaLANE;
  logic [183:0] m0_ubLANE;
  logic [29:0] m0_xa [0:7];
  logic m0_dena [0:7];
  logic [29:0] m0_xb [0:7];
  logic m0_denb [0:7];
  logic [239:0] m0_o1q0_LANE_xs;
  logic [119:0] m0_o1q0_LANE;
  logic [79:0] m0_o1q0_LANE_pf;
  logic [29:0] m0_o1q0_LANE_x0;
  logic [29:0] m0_o1q0_LANE_x1;
  logic [29:0] m0_o1q0_LANE_x2;
  logic [29:0] m0_o1q0_LANE_x3;
  logic [29:0] m0_o1q0_LANE_x4;
  logic [29:0] m0_o1q0_LANE_x5;
  logic [29:0] m0_o1q0_LANE_x6;
  logic [29:0] m0_o1q0_LANE_x7;
  assign m0_aLANE = a[(LANE*40) +: 40];
  assign m0_bLANE = b[(LANE*40) +: 40];
  assign m0_uaLANE = m0_unpack_s(m0_aLANE, daz);
  assign m0_ubLANE = m0_unpack_s(m0_bLANE, daz);
  assign m0_xa[((LANE*8)+0)] = m0_x(m0_uaLANE[0 +: 22]);
  assign m0_dena[((LANE*8)+0)] = m0_uaLANE[22];
  assign m0_xb[((LANE*8)+0)] = m0_x(m0_ubLANE[0 +: 22]);
  assign m0_denb[((LANE*8)+0)] = m0_ubLANE[22];
  assign m0_xa[((LANE*8)+1)] = m0_x(m0_uaLANE[23 +: 22]);
  assign m0_dena[((LANE*8)+1)] = m0_uaLANE[45];
  assign m0_xb[((LANE*8)+1)] = m0_x(m0_ubLANE[23 +: 22]);
  assign m0_denb[((LANE*8)+1)] = m0_ubLANE[45];
  assign m0_xa[((LANE*8)+2)] = m0_x(m0_uaLANE[46 +: 22]);
  assign m0_dena[((LANE*8)+2)] = m0_uaLANE[68];
  assign m0_xb[((LANE*8)+2)] = m0_x(m0_ubLANE[46 +: 22]);
  assign m0_denb[((LANE*8)+2)] = m0_ubLANE[68];
  assign m0_xa[((LANE*8)+3)] = m0_x(m0_uaLANE[69 +: 22]);
  assign m0_dena[((LANE*8)+3)] = m0_uaLANE[91];
  assign m0_xb[((LANE*8)+3)] = m0_x(m0_ubLANE[69 +: 22]);
  assign m0_denb[((LANE*8)+3)] = m0_ubLANE[91];
  assign m0_xa[((LANE*8)+4)] = m0_x(m0_uaLANE[92 +: 22]);
  assign m0_dena[((LANE*8)+4)] = m0_uaLANE[114];
  assign m0_xb[((LANE*8)+4)] = m0_x(m0_ubLANE[92 +: 22]);
  assign m0_denb[((LANE*8)+4)] = m0_ubLANE[114];
  assign m0_xa[((LANE*8)+5)] = m0_x(m0_uaLANE[115 +: 22]);
  assign m0_dena[((LANE*8)+5)] = m0_uaLANE[137];
  assign m0_xb[((LANE*8)+5)] = m0_x(m0_ubLANE[115 +: 22]);
  assign m0_denb[((LANE*8)+5)] = m0_ubLANE[137];
  assign m0_xa[((LANE*8)+6)] = m0_x(m0_uaLANE[138 +: 22]);
  assign m0_dena[((LANE*8)+6)] = m0_uaLANE[160];
  assign m0_xb[((LANE*8)+6)] = m0_x(m0_ubLANE[138 +: 22]);
  assign m0_denb[((LANE*8)+6)] = m0_ubLANE[160];
  assign m0_xa[((LANE*8)+7)] = m0_x(m0_uaLANE[161 +: 22]);
  assign m0_dena[((LANE*8)+7)] = m0_uaLANE[183];
  assign m0_xb[((LANE*8)+7)] = m0_x(m0_ubLANE[161 +: 22]);
  assign m0_denb[((LANE*8)+7)] = m0_ubLANE[183];
  always_comb begin
    y_m0 = '0; d_m0 = '0; fl_m0 = '0;
    m0_o1q0_LANE_xs = 'x; m0_o1q0_LANE = 'x; m0_o1q0_LANE_pf = 'x; m0_o1q0_LANE_x0 = 'x; m0_o1q0_LANE_x1 = 'x; m0_o1q0_LANE_x2 = 'x;
    m0_o1q0_LANE_x3 = 'x; m0_o1q0_LANE_x4 = 'x; m0_o1q0_LANE_x5 = 'x; m0_o1q0_LANE_x6 = 'x; m0_o1q0_LANE_x7 = 'x;
    case (op)
      1'd1: begin
        m0_o1q0_LANE_pf = 0;
        m0_o1q0_LANE_x0 = m0_mul(m0_xa[((LANE*8)+0)], m0_xb[((LANE*8)+0)]);
        m0_o1q0_LANE_xs[0 +: 30] = { m0_o1q0_LANE_x0[29:28], (m0_o1q0_LANE_x0[29:28] == 2'd0 && m0_o1q0_LANE_x0[10:0] == 0) ? (m0_xa[((LANE*8)+0)][27] ^ m0_xb[((LANE*8)+0)][27]) : m0_o1q0_LANE_x0[27], m0_o1q0_LANE_x0[26:0] };
        m0_o1q0_LANE_pf[0 +: 10] = ((m0_dena[((LANE*8)+0)] | m0_denb[((LANE*8)+0)]) ? (10'd1 << 6) : 10'd0) | (1'b0 || 1'b0 || ((m0_o1q0_LANE_xs[28 +: 2] == 2'd1) && !((m0_xa[((LANE*8)+0)][29:28] == 2'd1) || (m0_xb[((LANE*8)+0)][29:28] == 2'd1))) ? (10'd1 << 0) : 10'd0);
        m0_o1q0_LANE_x1 = m0_mul(m0_xa[((LANE*8)+1)], m0_xb[((LANE*8)+1)]);
        m0_o1q0_LANE_xs[30 +: 30] = { m0_o1q0_LANE_x1[29:28], (m0_o1q0_LANE_x1[29:28] == 2'd0 && m0_o1q0_LANE_x1[10:0] == 0) ? (m0_xa[((LANE*8)+1)][27] ^ m0_xb[((LANE*8)+1)][27]) : m0_o1q0_LANE_x1[27], m0_o1q0_LANE_x1[26:0] };
        m0_o1q0_LANE_pf[10 +: 10] = ((m0_dena[((LANE*8)+1)] | m0_denb[((LANE*8)+1)]) ? (10'd1 << 6) : 10'd0) | (1'b0 || 1'b0 || ((m0_o1q0_LANE_xs[58 +: 2] == 2'd1) && !((m0_xa[((LANE*8)+1)][29:28] == 2'd1) || (m0_xb[((LANE*8)+1)][29:28] == 2'd1))) ? (10'd1 << 0) : 10'd0);
        m0_o1q0_LANE_x2 = m0_mul(m0_xa[((LANE*8)+2)], m0_xb[((LANE*8)+2)]);
        m0_o1q0_LANE_xs[60 +: 30] = { m0_o1q0_LANE_x2[29:28], (m0_o1q0_LANE_x2[29:28] == 2'd0 && m0_o1q0_LANE_x2[10:0] == 0) ? (m0_xa[((LANE*8)+2)][27] ^ m0_xb[((LANE*8)+2)][27]) : m0_o1q0_LANE_x2[27], m0_o1q0_LANE_x2[26:0] };
        m0_o1q0_LANE_pf[20 +: 10] = ((m0_dena[((LANE*8)+2)] | m0_denb[((LANE*8)+2)]) ? (10'd1 << 6) : 10'd0) | (1'b0 || 1'b0 || ((m0_o1q0_LANE_xs[88 +: 2] == 2'd1) && !((m0_xa[((LANE*8)+2)][29:28] == 2'd1) || (m0_xb[((LANE*8)+2)][29:28] == 2'd1))) ? (10'd1 << 0) : 10'd0);
        m0_o1q0_LANE_x3 = m0_mul(m0_xa[((LANE*8)+3)], m0_xb[((LANE*8)+3)]);
        m0_o1q0_LANE_xs[90 +: 30] = { m0_o1q0_LANE_x3[29:28], (m0_o1q0_LANE_x3[29:28] == 2'd0 && m0_o1q0_LANE_x3[10:0] == 0) ? (m0_xa[((LANE*8)+3)][27] ^ m0_xb[((LANE*8)+3)][27]) : m0_o1q0_LANE_x3[27], m0_o1q0_LANE_x3[26:0] };
        m0_o1q0_LANE_pf[30 +: 10] = ((m0_dena[((LANE*8)+3)] | m0_denb[((LANE*8)+3)]) ? (10'd1 << 6) : 10'd0) | (1'b0 || 1'b0 || ((m0_o1q0_LANE_xs[118 +: 2] == 2'd1) && !((m0_xa[((LANE*8)+3)][29:28] == 2'd1) || (m0_xb[((LANE*8)+3)][29:28] == 2'd1))) ? (10'd1 << 0) : 10'd0);
        m0_o1q0_LANE_x4 = m0_mul(m0_xa[((LANE*8)+4)], m0_xb[((LANE*8)+4)]);
        m0_o1q0_LANE_xs[120 +: 30] = { m0_o1q0_LANE_x4[29:28], (m0_o1q0_LANE_x4[29:28] == 2'd0 && m0_o1q0_LANE_x4[10:0] == 0) ? (m0_xa[((LANE*8)+4)][27] ^ m0_xb[((LANE*8)+4)][27]) : m0_o1q0_LANE_x4[27], m0_o1q0_LANE_x4[26:0] };
        m0_o1q0_LANE_pf[40 +: 10] = ((m0_dena[((LANE*8)+4)] | m0_denb[((LANE*8)+4)]) ? (10'd1 << 6) : 10'd0) | (1'b0 || 1'b0 || ((m0_o1q0_LANE_xs[148 +: 2] == 2'd1) && !((m0_xa[((LANE*8)+4)][29:28] == 2'd1) || (m0_xb[((LANE*8)+4)][29:28] == 2'd1))) ? (10'd1 << 0) : 10'd0);
        m0_o1q0_LANE_x5 = m0_mul(m0_xa[((LANE*8)+5)], m0_xb[((LANE*8)+5)]);
        m0_o1q0_LANE_xs[150 +: 30] = { m0_o1q0_LANE_x5[29:28], (m0_o1q0_LANE_x5[29:28] == 2'd0 && m0_o1q0_LANE_x5[10:0] == 0) ? (m0_xa[((LANE*8)+5)][27] ^ m0_xb[((LANE*8)+5)][27]) : m0_o1q0_LANE_x5[27], m0_o1q0_LANE_x5[26:0] };
        m0_o1q0_LANE_pf[50 +: 10] = ((m0_dena[((LANE*8)+5)] | m0_denb[((LANE*8)+5)]) ? (10'd1 << 6) : 10'd0) | (1'b0 || 1'b0 || ((m0_o1q0_LANE_xs[178 +: 2] == 2'd1) && !((m0_xa[((LANE*8)+5)][29:28] == 2'd1) || (m0_xb[((LANE*8)+5)][29:28] == 2'd1))) ? (10'd1 << 0) : 10'd0);
        m0_o1q0_LANE_x6 = m0_mul(m0_xa[((LANE*8)+6)], m0_xb[((LANE*8)+6)]);
        m0_o1q0_LANE_xs[180 +: 30] = { m0_o1q0_LANE_x6[29:28], (m0_o1q0_LANE_x6[29:28] == 2'd0 && m0_o1q0_LANE_x6[10:0] == 0) ? (m0_xa[((LANE*8)+6)][27] ^ m0_xb[((LANE*8)+6)][27]) : m0_o1q0_LANE_x6[27], m0_o1q0_LANE_x6[26:0] };
        m0_o1q0_LANE_pf[60 +: 10] = ((m0_dena[((LANE*8)+6)] | m0_denb[((LANE*8)+6)]) ? (10'd1 << 6) : 10'd0) | (1'b0 || 1'b0 || ((m0_o1q0_LANE_xs[208 +: 2] == 2'd1) && !((m0_xa[((LANE*8)+6)][29:28] == 2'd1) || (m0_xb[((LANE*8)+6)][29:28] == 2'd1))) ? (10'd1 << 0) : 10'd0);
        m0_o1q0_LANE_x7 = m0_mul(m0_xa[((LANE*8)+7)], m0_xb[((LANE*8)+7)]);
        m0_o1q0_LANE_xs[210 +: 30] = { m0_o1q0_LANE_x7[29:28], (m0_o1q0_LANE_x7[29:28] == 2'd0 && m0_o1q0_LANE_x7[10:0] == 0) ? (m0_xa[((LANE*8)+7)][27] ^ m0_xb[((LANE*8)+7)][27]) : m0_o1q0_LANE_x7[27], m0_o1q0_LANE_x7[26:0] };
        m0_o1q0_LANE_pf[70 +: 10] = ((m0_dena[((LANE*8)+7)] | m0_denb[((LANE*8)+7)]) ? (10'd1 << 6) : 10'd0) | (1'b0 || 1'b0 || ((m0_o1q0_LANE_xs[238 +: 2] == 2'd1) && !((m0_xa[((LANE*8)+7)][29:28] == 2'd1) || (m0_xb[((LANE*8)+7)][29:28] == 2'd1))) ? (10'd1 << 0) : 10'd0);
        m0_o1q0_LANE = m0_quant_blksfps0e8m0Nefp4e2m1s8(m0_o1q0_LANE_xs, rnd, 64'd0, ftz);
        y_m0[((LANE*40)+0) +: 40] = m0_o1q0_LANE[39:0];
        y_m0[((LANE*40)+0) +: 4] = (m0_o1q0_LANE_xs[0 +: 11] == 0 && m0_o1q0_LANE_xs[28 +: 2] == 0) ? {m0_o1q0_LANE_xs[27], 3'd0} : m0_o1q0_LANE[0 +: 4];
        fl_m0[((0+(LANE*8))+0)*10 +: 10] = (m0_o1q0_LANE_pf[0 +: 10] | m0_o1q0_LANE[40 +: 10]);
        y_m0[((LANE*40)+4) +: 4] = (m0_o1q0_LANE_xs[30 +: 11] == 0 && m0_o1q0_LANE_xs[58 +: 2] == 0) ? {m0_o1q0_LANE_xs[57], 3'd0} : m0_o1q0_LANE[4 +: 4];
        fl_m0[((0+(LANE*8))+1)*10 +: 10] = (m0_o1q0_LANE_pf[10 +: 10] | m0_o1q0_LANE[50 +: 10]);
        y_m0[((LANE*40)+8) +: 4] = (m0_o1q0_LANE_xs[60 +: 11] == 0 && m0_o1q0_LANE_xs[88 +: 2] == 0) ? {m0_o1q0_LANE_xs[87], 3'd0} : m0_o1q0_LANE[8 +: 4];
        fl_m0[((0+(LANE*8))+2)*10 +: 10] = (m0_o1q0_LANE_pf[20 +: 10] | m0_o1q0_LANE[60 +: 10]);
        y_m0[((LANE*40)+12) +: 4] = (m0_o1q0_LANE_xs[90 +: 11] == 0 && m0_o1q0_LANE_xs[118 +: 2] == 0) ? {m0_o1q0_LANE_xs[117], 3'd0} : m0_o1q0_LANE[12 +: 4];
        fl_m0[((0+(LANE*8))+3)*10 +: 10] = (m0_o1q0_LANE_pf[30 +: 10] | m0_o1q0_LANE[70 +: 10]);
        y_m0[((LANE*40)+16) +: 4] = (m0_o1q0_LANE_xs[120 +: 11] == 0 && m0_o1q0_LANE_xs[148 +: 2] == 0) ? {m0_o1q0_LANE_xs[147], 3'd0} : m0_o1q0_LANE[16 +: 4];
        fl_m0[((0+(LANE*8))+4)*10 +: 10] = (m0_o1q0_LANE_pf[40 +: 10] | m0_o1q0_LANE[80 +: 10]);
        y_m0[((LANE*40)+20) +: 4] = (m0_o1q0_LANE_xs[150 +: 11] == 0 && m0_o1q0_LANE_xs[178 +: 2] == 0) ? {m0_o1q0_LANE_xs[177], 3'd0} : m0_o1q0_LANE[20 +: 4];
        fl_m0[((0+(LANE*8))+5)*10 +: 10] = (m0_o1q0_LANE_pf[50 +: 10] | m0_o1q0_LANE[90 +: 10]);
        y_m0[((LANE*40)+24) +: 4] = (m0_o1q0_LANE_xs[180 +: 11] == 0 && m0_o1q0_LANE_xs[208 +: 2] == 0) ? {m0_o1q0_LANE_xs[207], 3'd0} : m0_o1q0_LANE[24 +: 4];
        fl_m0[((0+(LANE*8))+6)*10 +: 10] = (m0_o1q0_LANE_pf[60 +: 10] | m0_o1q0_LANE[100 +: 10]);
        y_m0[((LANE*40)+28) +: 4] = (m0_o1q0_LANE_xs[210 +: 11] == 0 && m0_o1q0_LANE_xs[238 +: 2] == 0) ? {m0_o1q0_LANE_xs[237], 3'd0} : m0_o1q0_LANE[28 +: 4];
        fl_m0[((0+(LANE*8))+7)*10 +: 10] = (m0_o1q0_LANE_pf[70 +: 10] | m0_o1q0_LANE[110 +: 10]);
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m1_fp_adder #(parameter int LANE = 0) (
  input  logic [63:0] a,
  input  logic [63:0] b,
  input  logic [0:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [63:0] y_m1,
  output logic [79:0] fl_m1,
  input  logic [223:0] xa_m1,
  input  logic [223:0] xb_m1,
  input  logic [7:0] dena_m1,
  input  logic [7:0] denb_m1,
  output logic [223:0] x_m1
);
  // alu_core_m1_fp_adder: lane LANE of mode 1 (fp8e4m3) for the fp_adder ops fadd; the result buses are the mode's, with only this lane's bits written
  import alu_core_m1_pkg::*;
  logic d_m1;
  logic [7:0] m1_aLANE;
  logic [7:0] m1_bLANE;
  logic [19:0] m1_uaLANE;
  logic [19:0] m1_ubLANE;
  logic [27:0] m1_xa [0:7];
  logic m1_dena [0:7];
  logic [27:0] m1_xb [0:7];
  logic m1_denb [0:7];
  logic [27:0] m1_fa_xaLANE;
  logic [27:0] m1_fa_xbLANE;
  logic m1_fa_subLANE;
  logic [27:0] m1_fa_yLANE;
  logic [17:0] m1_o0t0_LANE;
  logic [27:0] m1_o0t0_LANE_x;
  logic [27:0] m1_o0t0_LANE_z;
  assign m1_aLANE = a[(LANE*8) +: 8];
  assign m1_bLANE = b[(LANE*8) +: 8];
  // structure core.unpacker.m1: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp8e4m3_x12e12s4_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp8e4m3_x12e12s4_p9bfe39588414 u_m1_unpack_aLANE (.b(m1_aLANE), .daz(daz), .u(m1_uaLANE));
  // structure core.unpacker.m1: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp8e4m3_x12e12s4_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp8e4m3_x12e12s4_p9bfe39588414 u_m1_unpack_bLANE (.b(m1_bLANE), .daz(daz), .u(m1_ubLANE));
  assign m1_xa[LANE] = m1_x(m1_uaLANE[18:0]);
  assign m1_dena[LANE] = m1_uaLANE[19];
  assign m1_xb[LANE] = m1_x(m1_ubLANE[18:0]);
  assign m1_denb[LANE] = m1_ubLANE[19];
  // structure core.fp_adder.m1: family single_path realized by the library module fam_fp_add_single_path_x12e12s4_p9d459d224988
  fam_fp_add_single_path_x12e12s4_p9d459d224988 u_m1_faddLANE (.xa(m1_fa_xaLANE), .xb(m1_fa_xbLANE), .sub(m1_fa_subLANE), .y(m1_fa_yLANE));
  always_comb begin
    y_m1 = '0; d_m1 = '0; fl_m1 = '0;
    m1_fa_xaLANE = 'x; m1_fa_xbLANE = 'x; m1_fa_subLANE = 'x; m1_o0t0_LANE = 'x; m1_o0t0_LANE_x = 'x; m1_o0t0_LANE_z = 'x;
    x_m1 = '0;
    case (op)
      1'd0: begin
        m1_fa_xaLANE = m1_xa[LANE]; m1_fa_xbLANE = m1_xb[LANE]; m1_fa_subLANE = 1'b0; m1_o0t0_LANE_x = m1_fa_yLANE;
        m1_o0t0_LANE_z = { m1_o0t0_LANE_x[27:26], (m1_o0t0_LANE_x[27:26] == 2'd0 && m1_o0t0_LANE_x[12:0] == 0) ? (((m1_xa[LANE][27:26] == 2'd0 && m1_xa[LANE][12:0] == 0) && (m1_xb[LANE][27:26] == 2'd0 && m1_xb[LANE][12:0] == 0)) ? ((rnd == 3'd2) ? (m1_aLANE[7] | (m1_bLANE[7] ^ 1'b0)) : (m1_aLANE[7] & (m1_bLANE[7] ^ 1'b0))) : ((rnd == 3'd2) ? 1'b1 : 1'b0)) : m1_o0t0_LANE_x[25], m1_o0t0_LANE_x[24:0] };
        x_m1[LANE*28 +: 28] = m1_o0t0_LANE_z;
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m1_fp_multiplier #(parameter int LANE = 0) (
  input  logic [63:0] a,
  input  logic [63:0] b,
  input  logic [0:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [63:0] y_m1,
  output logic [79:0] fl_m1,
  input  logic [223:0] xa_m1,
  input  logic [223:0] xb_m1,
  input  logic [7:0] dena_m1,
  input  logic [7:0] denb_m1,
  output logic [223:0] x_m1
);
  // alu_core_m1_fp_multiplier: lane LANE of mode 1 (fp8e4m3) for the fp_multiplier ops fmul; the result buses are the mode's, with only this lane's bits written
  import alu_core_m1_pkg::*;
  logic d_m1;
  logic [7:0] m1_aLANE;
  logic [7:0] m1_bLANE;
  logic [19:0] m1_uaLANE;
  logic [19:0] m1_ubLANE;
  logic [27:0] m1_xa [0:7];
  logic m1_dena [0:7];
  logic [27:0] m1_xb [0:7];
  logic m1_denb [0:7];
  logic [27:0] m1_fm_xaLANE;
  logic [27:0] m1_fm_xbLANE;
  logic [27:0] m1_fm_yLANE;
  logic [17:0] m1_o1t0_LANE;
  logic [27:0] m1_o1t0_LANE_x;
  logic [27:0] m1_o1t0_LANE_z;
  assign m1_aLANE = a[(LANE*8) +: 8];
  assign m1_bLANE = b[(LANE*8) +: 8];
  // structure core.unpacker.m1: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp8e4m3_x12e12s4_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp8e4m3_x12e12s4_p9bfe39588414 u_m1_unpack_aLANE (.b(m1_aLANE), .daz(daz), .u(m1_uaLANE));
  // structure core.unpacker.m1: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp8e4m3_x12e12s4_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp8e4m3_x12e12s4_p9bfe39588414 u_m1_unpack_bLANE (.b(m1_bLANE), .daz(daz), .u(m1_ubLANE));
  assign m1_xa[LANE] = m1_x(m1_uaLANE[18:0]);
  assign m1_dena[LANE] = m1_uaLANE[19];
  assign m1_xb[LANE] = m1_x(m1_ubLANE[18:0]);
  assign m1_denb[LANE] = m1_ubLANE[19];
  // structure core.fp_multiplier.m1: family sig_mul_then_round realized by the library module fam_fp_mul_sig_mul_then_round_x12e12s4_pbd766efe148c
  fam_fp_mul_sig_mul_then_round_x12e12s4_pbd766efe148c u_m1_fmulLANE (.xa(m1_fm_xaLANE), .xb(m1_fm_xbLANE), .y(m1_fm_yLANE));
  always_comb begin
    y_m1 = '0; d_m1 = '0; fl_m1 = '0;
    m1_fm_xaLANE = 'x; m1_fm_xbLANE = 'x; m1_o1t0_LANE = 'x; m1_o1t0_LANE_x = 'x; m1_o1t0_LANE_z = 'x;
    x_m1 = '0;
    case (op)
      1'd1: begin
        m1_fm_xaLANE = m1_xa[LANE]; m1_fm_xbLANE = m1_xb[LANE]; m1_o1t0_LANE_x = m1_fm_yLANE;
        m1_o1t0_LANE_z = { m1_o1t0_LANE_x[27:26], (m1_o1t0_LANE_x[27:26] == 2'd0 && m1_o1t0_LANE_x[12:0] == 0) ? (m1_aLANE[7] ^ m1_bLANE[7]) : m1_o1t0_LANE_x[25], m1_o1t0_LANE_x[24:0] };
        x_m1[LANE*28 +: 28] = m1_o1t0_LANE_z;
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m1_rounder #(parameter int LANE = 0) (
  input  logic [63:0] a,
  input  logic [63:0] b,
  input  logic [0:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [63:0] y_m1,
  output logic [79:0] fl_m1,
  input  logic [223:0] xa_m1,
  input  logic [223:0] xb_m1,
  input  logic [7:0] dena_m1,
  input  logic [7:0] denb_m1,
  input  logic [223:0] x_m1
);
  // alu_core_m1_rounder: lane LANE of mode 1 (fp8e4m3) for the rounder ops fadd, fmul; the result buses are the mode's, with only this lane's bits written
  import alu_core_m1_pkg::*;
  logic d_m1;
  logic [7:0] m1_aLANE;
  logic [7:0] m1_bLANE;
  logic [19:0] m1_uaLANE;
  logic [19:0] m1_ubLANE;
  logic [27:0] m1_xa [0:7];
  logic m1_dena [0:7];
  logic [27:0] m1_xb [0:7];
  logic m1_denb [0:7];
  logic [27:0] m1_rd_xLANE_fadd;
  logic [7:0] m1_rd_wLANE_fadd;
  logic [9:0] m1_rd_flLANE_fadd;
  logic [7:0] m1_rd_bLANE_fadd;
  logic [27:0] m1_rd_xLANE_fmul;
  logic [7:0] m1_rd_wLANE_fmul;
  logic [9:0] m1_rd_flLANE_fmul;
  logic [7:0] m1_rd_bLANE_fmul;
  logic [17:0] m1_o0t0_LANE;
  logic [27:0] m1_o0t0_LANE_x;
  logic [27:0] m1_o0t0_LANE_z;
  logic [17:0] m1_o1t0_LANE;
  logic [27:0] m1_o1t0_LANE_x;
  logic [27:0] m1_o1t0_LANE_z;
  assign m1_aLANE = a[(LANE*8) +: 8];
  assign m1_bLANE = b[(LANE*8) +: 8];
  // structure core.unpacker.m1: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp8e4m3_x12e12s4_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp8e4m3_x12e12s4_p9bfe39588414 u_m1_unpack_aLANE (.b(m1_aLANE), .daz(daz), .u(m1_uaLANE));
  // structure core.unpacker.m1: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp8e4m3_x12e12s4_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp8e4m3_x12e12s4_p9bfe39588414 u_m1_unpack_bLANE (.b(m1_bLANE), .daz(daz), .u(m1_ubLANE));
  assign m1_xa[LANE] = m1_x(m1_uaLANE[18:0]);
  assign m1_dena[LANE] = m1_uaLANE[19];
  assign m1_xb[LANE] = m1_x(m1_ubLANE[18:0]);
  assign m1_denb[LANE] = m1_ubLANE[19];
  // structure core.rounder.m1: family dedicated_per_op realized by the library module fam_fp_round_dedicated_per_op_increment_adder_fp8e4m3_x12e12s4_pd77ccc5b5c45 (fadd)
  fam_fp_round_dedicated_per_op_increment_adder_fp8e4m3_x12e12s4_pd77ccc5b5c45 u_m1_roundLANE_fadd (.x(m1_rd_xLANE_fadd), .rnd(rnd), .word(m1_rd_wLANE_fadd), .ftz(ftz), .fl(m1_rd_flLANE_fadd), .bits(m1_rd_bLANE_fadd));
  // structure core.rounder.m1: family dedicated_per_op realized by the library module fam_fp_round_dedicated_per_op_increment_adder_fp8e4m3_x12e12s4_pd77ccc5b5c45 (fmul)
  fam_fp_round_dedicated_per_op_increment_adder_fp8e4m3_x12e12s4_pd77ccc5b5c45 u_m1_roundLANE_fmul (.x(m1_rd_xLANE_fmul), .rnd(rnd), .word(m1_rd_wLANE_fmul), .ftz(ftz), .fl(m1_rd_flLANE_fmul), .bits(m1_rd_bLANE_fmul));
  always_comb begin
    y_m1 = '0; d_m1 = '0; fl_m1 = '0;
    m1_rd_xLANE_fadd = 'x; m1_rd_wLANE_fadd = 'x; m1_rd_xLANE_fmul = 'x; m1_rd_wLANE_fmul = 'x; m1_o0t0_LANE = 'x; m1_o0t0_LANE_x = 'x;
    m1_o0t0_LANE_z = 'x; m1_o1t0_LANE = 'x; m1_o1t0_LANE_x = 'x; m1_o1t0_LANE_z = 'x;
    case (op)
      1'd0: begin
        m1_o0t0_LANE_z = x_m1[LANE*28 +: 28];
        m1_rd_xLANE_fadd = m1_o0t0_LANE_z; m1_rd_wLANE_fadd = 8'd0; m1_o0t0_LANE = {m1_rd_flLANE_fadd, m1_rd_bLANE_fadd};
        y_m1[((LANE*8)+0) +: 8] = (m1_o0t0_LANE_z[27:26] == 2'd1) ? (((m1_xa[LANE][27:26] == 2'd1) || (m1_xb[LANE][27:26] == 2'd1)) ? 8'd127 : 8'd127) : ((m1_o0t0_LANE_z[27:26] == 2'd0 && m1_o0t0_LANE_z[12:0] == 0) ? {m1_o0t0_LANE_z[25], 7'd0} : m1_o0t0_LANE[7:0]);
        fl_m1[(0+LANE)*10 +: 10] = (((m1_xa[LANE][27:26] == 2'd1) || (m1_xb[LANE][27:26] == 2'd1)) ? (((10'd1 << 5) | (1'b0 || 1'b0 ? (10'd1 << 0) : 10'd0)) | (m1_dena[LANE] | m1_denb[LANE] ? (10'd1 << 6) : 10'd0)) : (m1_o0t0_LANE[17:8] | ((1'b0 || 1'b0 || ((m1_o0t0_LANE_z[27:26] == 2'd1) && !((m1_xa[LANE][27:26] == 2'd1) || (m1_xb[LANE][27:26] == 2'd1)))) ? (10'd1 << 0) : 10'd0) | (m1_dena[LANE] | m1_denb[LANE] ? (10'd1 << 6) : 10'd0)));
      end
      1'd1: begin
        m1_o1t0_LANE_z = x_m1[LANE*28 +: 28];
        m1_rd_xLANE_fmul = m1_o1t0_LANE_z; m1_rd_wLANE_fmul = 8'd0; m1_o1t0_LANE = {m1_rd_flLANE_fmul, m1_rd_bLANE_fmul};
        y_m1[((LANE*8)+0) +: 8] = (m1_o1t0_LANE_z[27:26] == 2'd1) ? (((m1_xa[LANE][27:26] == 2'd1) || (m1_xb[LANE][27:26] == 2'd1)) ? 8'd127 : 8'd127) : ((m1_o1t0_LANE_z[27:26] == 2'd0 && m1_o1t0_LANE_z[12:0] == 0) ? {m1_o1t0_LANE_z[25], 7'd0} : m1_o1t0_LANE[7:0]);
        fl_m1[(0+LANE)*10 +: 10] = (((m1_xa[LANE][27:26] == 2'd1) || (m1_xb[LANE][27:26] == 2'd1)) ? (((10'd1 << 5) | (1'b0 || 1'b0 ? (10'd1 << 0) : 10'd0)) | (m1_dena[LANE] | m1_denb[LANE] ? (10'd1 << 6) : 10'd0)) : (m1_o1t0_LANE[17:8] | ((1'b0 || 1'b0 || ((m1_o1t0_LANE_z[27:26] == 2'd1) && !((m1_xa[LANE][27:26] == 2'd1) || (m1_xb[LANE][27:26] == 2'd1)))) ? (10'd1 << 0) : 10'd0) | (m1_dena[LANE] | m1_denb[LANE] ? (10'd1 << 6) : 10'd0)));
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m1_unpacker #(parameter int LANE = 0) (
  input  logic [63:0] a,
  input  logic [63:0] b,
  input  logic [0:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [223:0] xa_m1,
  output logic [223:0] xb_m1,
  output logic [7:0] dena_m1,
  output logic [7:0] denb_m1
);
  // alu_core_m1_unpacker: lane LANE of mode 1 (fp8e4m3) for the unpacker ops ; the result buses are the mode's, with only this lane's bits written
  import alu_core_m1_pkg::*;
  logic [63:0] y_m1;
  logic d_m1;
  logic [79:0] fl_m1;
  logic [7:0] m1_aLANE;
  logic [7:0] m1_bLANE;
  logic [19:0] m1_uaLANE;
  logic [19:0] m1_ubLANE;
  logic [27:0] m1_xa [0:7];
  logic m1_dena [0:7];
  logic [27:0] m1_xb [0:7];
  logic m1_denb [0:7];
  assign m1_aLANE = a[(LANE*8) +: 8];
  assign m1_bLANE = b[(LANE*8) +: 8];
  // structure core.unpacker.m1: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp8e4m3_x12e12s4_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp8e4m3_x12e12s4_p9bfe39588414 u_m1_unpack_aLANE (.b(m1_aLANE), .daz(daz), .u(m1_uaLANE));
  // structure core.unpacker.m1: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp8e4m3_x12e12s4_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp8e4m3_x12e12s4_p9bfe39588414 u_m1_unpack_bLANE (.b(m1_bLANE), .daz(daz), .u(m1_ubLANE));
  assign m1_xa[LANE] = m1_x(m1_uaLANE[18:0]);
  assign m1_dena[LANE] = m1_uaLANE[19];
  assign m1_xb[LANE] = m1_x(m1_ubLANE[18:0]);
  assign m1_denb[LANE] = m1_ubLANE[19];
  always_comb begin
    xa_m1 = '0; dena_m1 = '0; xb_m1 = '0; denb_m1 = '0;
    xa_m1[LANE*28 +: 28] = m1_xa[LANE];
    dena_m1[LANE] = m1_dena[LANE];
    xb_m1[LANE*28 +: 28] = m1_xb[LANE];
    denb_m1[LANE] = m1_denb[LANE];
  end
endmodule
// ADIR-MEMBER m0_l0_fp_adder
// EVOLVE-BLOCK-START
module alu_core_u_m0_l0_fp_adder (
  input  logic [63:0] a,
  input  logic [63:0] b,
  input  logic [0:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [63:0] y_m0,
  output logic [79:0] fl_m0
);
  // alu_core_u_m0_l0_fp_adder: physical structure `m0.l0.fp_adder` (kind fp_adder, slot fp_adder); realizes m0.l0.fp_adder: fp_adder, mode 0 lane 0, blksfps0e8m0Nefp4e2m1s8, ops fadd
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [63:0] y_m0_l0;
  logic [79:0] fl_m0_l0;
  alu_core_m0_fp_adder #(.LANE(0)) u_m0_l0 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_l0), .fl_m0(fl_m0_l0));
  assign y_m0 = y_m0_l0;
  assign fl_m0 = fl_m0_l0;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m0_l0_fp_multiplier
// EVOLVE-BLOCK-START
module alu_core_u_m0_l0_fp_multiplier (
  input  logic [63:0] a,
  input  logic [63:0] b,
  input  logic [0:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [63:0] y_m0,
  output logic [79:0] fl_m0
);
  // alu_core_u_m0_l0_fp_multiplier: physical structure `m0.l0.fp_multiplier` (kind fp_multiplier, slot fp_multiplier); realizes m0.l0.fp_multiplier: fp_multiplier, mode 0 lane 0, blksfps0e8m0Nefp4e2m1s8, ops fmul
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [63:0] y_m0_l0;
  logic [79:0] fl_m0_l0;
  alu_core_m0_fp_multiplier #(.LANE(0)) u_m0_l0 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_l0), .fl_m0(fl_m0_l0));
  assign y_m0 = y_m0_l0;
  assign fl_m0 = fl_m0_l0;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l0_fp_adder
// EVOLVE-BLOCK-START
module alu_core_u_m1_l0_fp_adder (
  input  logic [63:0] a,
  input  logic [63:0] b,
  input  logic [0:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [63:0] y_m1,
  output logic [79:0] fl_m1,
  input  logic [223:0] xa_m1,
  input  logic [223:0] xb_m1,
  input  logic [7:0] dena_m1,
  input  logic [7:0] denb_m1,
  output logic [223:0] x_m1
);
  // alu_core_u_m1_l0_fp_adder: physical structure `m1.l0.fp_adder` (kind fp_adder, slot fp_adder); realizes m1.l0.fp_adder: fp_adder, mode 1 lane 0, fp8e4m3, ops fadd
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [63:0] y_m1_l0;
  logic [79:0] fl_m1_l0;
  logic [223:0] x_m1_l0;
  alu_core_m1_fp_adder #(.LANE(0)) u_m1_l0 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_l0), .fl_m1(fl_m1_l0), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1_l0));
  assign y_m1 = y_m1_l0;
  assign fl_m1 = fl_m1_l0;
  assign x_m1 = x_m1_l0;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l1_fp_adder
// EVOLVE-BLOCK-START
module alu_core_u_m1_l1_fp_adder (
  input  logic [63:0] a,
  input  logic [63:0] b,
  input  logic [0:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [63:0] y_m1,
  output logic [79:0] fl_m1,
  input  logic [223:0] xa_m1,
  input  logic [223:0] xb_m1,
  input  logic [7:0] dena_m1,
  input  logic [7:0] denb_m1,
  output logic [223:0] x_m1
);
  // alu_core_u_m1_l1_fp_adder: physical structure `m1.l1.fp_adder` (kind fp_adder, slot fp_adder); realizes m1.l1.fp_adder: fp_adder, mode 1 lane 1, fp8e4m3, ops fadd
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [63:0] y_m1_l1;
  logic [79:0] fl_m1_l1;
  logic [223:0] x_m1_l1;
  alu_core_m1_fp_adder #(.LANE(1)) u_m1_l1 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_l1), .fl_m1(fl_m1_l1), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1_l1));
  assign y_m1 = y_m1_l1;
  assign fl_m1 = fl_m1_l1;
  assign x_m1 = x_m1_l1;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l2_fp_adder
// EVOLVE-BLOCK-START
module alu_core_u_m1_l2_fp_adder (
  input  logic [63:0] a,
  input  logic [63:0] b,
  input  logic [0:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [63:0] y_m1,
  output logic [79:0] fl_m1,
  input  logic [223:0] xa_m1,
  input  logic [223:0] xb_m1,
  input  logic [7:0] dena_m1,
  input  logic [7:0] denb_m1,
  output logic [223:0] x_m1
);
  // alu_core_u_m1_l2_fp_adder: physical structure `m1.l2.fp_adder` (kind fp_adder, slot fp_adder); realizes m1.l2.fp_adder: fp_adder, mode 1 lane 2, fp8e4m3, ops fadd
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [63:0] y_m1_l2;
  logic [79:0] fl_m1_l2;
  logic [223:0] x_m1_l2;
  alu_core_m1_fp_adder #(.LANE(2)) u_m1_l2 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_l2), .fl_m1(fl_m1_l2), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1_l2));
  assign y_m1 = y_m1_l2;
  assign fl_m1 = fl_m1_l2;
  assign x_m1 = x_m1_l2;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l3_fp_adder
// EVOLVE-BLOCK-START
module alu_core_u_m1_l3_fp_adder (
  input  logic [63:0] a,
  input  logic [63:0] b,
  input  logic [0:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [63:0] y_m1,
  output logic [79:0] fl_m1,
  input  logic [223:0] xa_m1,
  input  logic [223:0] xb_m1,
  input  logic [7:0] dena_m1,
  input  logic [7:0] denb_m1,
  output logic [223:0] x_m1
);
  // alu_core_u_m1_l3_fp_adder: physical structure `m1.l3.fp_adder` (kind fp_adder, slot fp_adder); realizes m1.l3.fp_adder: fp_adder, mode 1 lane 3, fp8e4m3, ops fadd
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [63:0] y_m1_l3;
  logic [79:0] fl_m1_l3;
  logic [223:0] x_m1_l3;
  alu_core_m1_fp_adder #(.LANE(3)) u_m1_l3 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_l3), .fl_m1(fl_m1_l3), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1_l3));
  assign y_m1 = y_m1_l3;
  assign fl_m1 = fl_m1_l3;
  assign x_m1 = x_m1_l3;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l4_fp_adder
// EVOLVE-BLOCK-START
module alu_core_u_m1_l4_fp_adder (
  input  logic [63:0] a,
  input  logic [63:0] b,
  input  logic [0:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [63:0] y_m1,
  output logic [79:0] fl_m1,
  input  logic [223:0] xa_m1,
  input  logic [223:0] xb_m1,
  input  logic [7:0] dena_m1,
  input  logic [7:0] denb_m1,
  output logic [223:0] x_m1
);
  // alu_core_u_m1_l4_fp_adder: physical structure `m1.l4.fp_adder` (kind fp_adder, slot fp_adder); realizes m1.l4.fp_adder: fp_adder, mode 1 lane 4, fp8e4m3, ops fadd
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [63:0] y_m1_l4;
  logic [79:0] fl_m1_l4;
  logic [223:0] x_m1_l4;
  alu_core_m1_fp_adder #(.LANE(4)) u_m1_l4 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_l4), .fl_m1(fl_m1_l4), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1_l4));
  assign y_m1 = y_m1_l4;
  assign fl_m1 = fl_m1_l4;
  assign x_m1 = x_m1_l4;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l5_fp_adder
// EVOLVE-BLOCK-START
module alu_core_u_m1_l5_fp_adder (
  input  logic [63:0] a,
  input  logic [63:0] b,
  input  logic [0:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [63:0] y_m1,
  output logic [79:0] fl_m1,
  input  logic [223:0] xa_m1,
  input  logic [223:0] xb_m1,
  input  logic [7:0] dena_m1,
  input  logic [7:0] denb_m1,
  output logic [223:0] x_m1
);
  // alu_core_u_m1_l5_fp_adder: physical structure `m1.l5.fp_adder` (kind fp_adder, slot fp_adder); realizes m1.l5.fp_adder: fp_adder, mode 1 lane 5, fp8e4m3, ops fadd
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [63:0] y_m1_l5;
  logic [79:0] fl_m1_l5;
  logic [223:0] x_m1_l5;
  alu_core_m1_fp_adder #(.LANE(5)) u_m1_l5 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_l5), .fl_m1(fl_m1_l5), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1_l5));
  assign y_m1 = y_m1_l5;
  assign fl_m1 = fl_m1_l5;
  assign x_m1 = x_m1_l5;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l6_fp_adder
// EVOLVE-BLOCK-START
module alu_core_u_m1_l6_fp_adder (
  input  logic [63:0] a,
  input  logic [63:0] b,
  input  logic [0:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [63:0] y_m1,
  output logic [79:0] fl_m1,
  input  logic [223:0] xa_m1,
  input  logic [223:0] xb_m1,
  input  logic [7:0] dena_m1,
  input  logic [7:0] denb_m1,
  output logic [223:0] x_m1
);
  // alu_core_u_m1_l6_fp_adder: physical structure `m1.l6.fp_adder` (kind fp_adder, slot fp_adder); realizes m1.l6.fp_adder: fp_adder, mode 1 lane 6, fp8e4m3, ops fadd
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [63:0] y_m1_l6;
  logic [79:0] fl_m1_l6;
  logic [223:0] x_m1_l6;
  alu_core_m1_fp_adder #(.LANE(6)) u_m1_l6 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_l6), .fl_m1(fl_m1_l6), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1_l6));
  assign y_m1 = y_m1_l6;
  assign fl_m1 = fl_m1_l6;
  assign x_m1 = x_m1_l6;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l7_fp_adder
// EVOLVE-BLOCK-START
module alu_core_u_m1_l7_fp_adder (
  input  logic [63:0] a,
  input  logic [63:0] b,
  input  logic [0:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [63:0] y_m1,
  output logic [79:0] fl_m1,
  input  logic [223:0] xa_m1,
  input  logic [223:0] xb_m1,
  input  logic [7:0] dena_m1,
  input  logic [7:0] denb_m1,
  output logic [223:0] x_m1
);
  // alu_core_u_m1_l7_fp_adder: physical structure `m1.l7.fp_adder` (kind fp_adder, slot fp_adder); realizes m1.l7.fp_adder: fp_adder, mode 1 lane 7, fp8e4m3, ops fadd
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [63:0] y_m1_l7;
  logic [79:0] fl_m1_l7;
  logic [223:0] x_m1_l7;
  alu_core_m1_fp_adder #(.LANE(7)) u_m1_l7 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_l7), .fl_m1(fl_m1_l7), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1_l7));
  assign y_m1 = y_m1_l7;
  assign fl_m1 = fl_m1_l7;
  assign x_m1 = x_m1_l7;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l0_unpacker
// EVOLVE-BLOCK-START
module alu_core_u_m1_l0_unpacker (
  input  logic [63:0] a,
  input  logic [63:0] b,
  input  logic [0:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [223:0] xa_m1,
  output logic [223:0] xb_m1,
  output logic [7:0] dena_m1,
  output logic [7:0] denb_m1
);
  // alu_core_u_m1_l0_unpacker: physical structure `m1.l0.unpacker` (kind unpacker, slot unpacker); realizes m1.l0.unpacker: unpacker, mode 1 lane 0, fp8e4m3, ops fadd, fmul
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [223:0] xa_m1_l0;
  logic [223:0] xb_m1_l0;
  logic [7:0] dena_m1_l0;
  logic [7:0] denb_m1_l0;
  alu_core_m1_unpacker #(.LANE(0)) u_m1_l0 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .xa_m1(xa_m1_l0), .xb_m1(xb_m1_l0), .dena_m1(dena_m1_l0), .denb_m1(denb_m1_l0));
  assign xa_m1 = xa_m1_l0;
  assign xb_m1 = xb_m1_l0;
  assign dena_m1 = dena_m1_l0;
  assign denb_m1 = denb_m1_l0;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l0_rounder
// EVOLVE-BLOCK-START
module alu_core_u_m1_l0_rounder (
  input  logic [63:0] a,
  input  logic [63:0] b,
  input  logic [0:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [63:0] y_m1,
  output logic [79:0] fl_m1,
  input  logic [223:0] xa_m1,
  input  logic [223:0] xb_m1,
  input  logic [7:0] dena_m1,
  input  logic [7:0] denb_m1,
  input  logic [223:0] x_m1
);
  // alu_core_u_m1_l0_rounder: physical structure `m1.l0.rounder` (kind rounder, slot rounder); realizes m1.l0.rounder: rounder, mode 1 lane 0, fp8e4m3, ops fadd, fmul
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [63:0] y_m1_l0;
  logic [79:0] fl_m1_l0;
  alu_core_m1_rounder #(.LANE(0)) u_m1_l0 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_l0), .fl_m1(fl_m1_l0), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1));
  assign y_m1 = y_m1_l0;
  assign fl_m1 = fl_m1_l0;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l0_fp_fma
// m1.l0.fp_fma: realized inline in the top (member top)
// ADIR-MEMBER m1_l1_unpacker
// EVOLVE-BLOCK-START
module alu_core_u_m1_l1_unpacker (
  input  logic [63:0] a,
  input  logic [63:0] b,
  input  logic [0:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [223:0] xa_m1,
  output logic [223:0] xb_m1,
  output logic [7:0] dena_m1,
  output logic [7:0] denb_m1
);
  // alu_core_u_m1_l1_unpacker: physical structure `m1.l1.unpacker` (kind unpacker, slot unpacker); realizes m1.l1.unpacker: unpacker, mode 1 lane 1, fp8e4m3, ops fadd, fmul
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [223:0] xa_m1_l1;
  logic [223:0] xb_m1_l1;
  logic [7:0] dena_m1_l1;
  logic [7:0] denb_m1_l1;
  alu_core_m1_unpacker #(.LANE(1)) u_m1_l1 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .xa_m1(xa_m1_l1), .xb_m1(xb_m1_l1), .dena_m1(dena_m1_l1), .denb_m1(denb_m1_l1));
  assign xa_m1 = xa_m1_l1;
  assign xb_m1 = xb_m1_l1;
  assign dena_m1 = dena_m1_l1;
  assign denb_m1 = denb_m1_l1;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l1_rounder
// EVOLVE-BLOCK-START
module alu_core_u_m1_l1_rounder (
  input  logic [63:0] a,
  input  logic [63:0] b,
  input  logic [0:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [63:0] y_m1,
  output logic [79:0] fl_m1,
  input  logic [223:0] xa_m1,
  input  logic [223:0] xb_m1,
  input  logic [7:0] dena_m1,
  input  logic [7:0] denb_m1,
  input  logic [223:0] x_m1
);
  // alu_core_u_m1_l1_rounder: physical structure `m1.l1.rounder` (kind rounder, slot rounder); realizes m1.l1.rounder: rounder, mode 1 lane 1, fp8e4m3, ops fadd, fmul
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [63:0] y_m1_l1;
  logic [79:0] fl_m1_l1;
  alu_core_m1_rounder #(.LANE(1)) u_m1_l1 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_l1), .fl_m1(fl_m1_l1), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1));
  assign y_m1 = y_m1_l1;
  assign fl_m1 = fl_m1_l1;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l1_fp_fma
// m1.l1.fp_fma: realized inline in the top (member top)
// ADIR-MEMBER m1_l2_unpacker
// EVOLVE-BLOCK-START
module alu_core_u_m1_l2_unpacker (
  input  logic [63:0] a,
  input  logic [63:0] b,
  input  logic [0:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [223:0] xa_m1,
  output logic [223:0] xb_m1,
  output logic [7:0] dena_m1,
  output logic [7:0] denb_m1
);
  // alu_core_u_m1_l2_unpacker: physical structure `m1.l2.unpacker` (kind unpacker, slot unpacker); realizes m1.l2.unpacker: unpacker, mode 1 lane 2, fp8e4m3, ops fadd, fmul
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [223:0] xa_m1_l2;
  logic [223:0] xb_m1_l2;
  logic [7:0] dena_m1_l2;
  logic [7:0] denb_m1_l2;
  alu_core_m1_unpacker #(.LANE(2)) u_m1_l2 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .xa_m1(xa_m1_l2), .xb_m1(xb_m1_l2), .dena_m1(dena_m1_l2), .denb_m1(denb_m1_l2));
  assign xa_m1 = xa_m1_l2;
  assign xb_m1 = xb_m1_l2;
  assign dena_m1 = dena_m1_l2;
  assign denb_m1 = denb_m1_l2;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l2_rounder
// EVOLVE-BLOCK-START
module alu_core_u_m1_l2_rounder (
  input  logic [63:0] a,
  input  logic [63:0] b,
  input  logic [0:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [63:0] y_m1,
  output logic [79:0] fl_m1,
  input  logic [223:0] xa_m1,
  input  logic [223:0] xb_m1,
  input  logic [7:0] dena_m1,
  input  logic [7:0] denb_m1,
  input  logic [223:0] x_m1
);
  // alu_core_u_m1_l2_rounder: physical structure `m1.l2.rounder` (kind rounder, slot rounder); realizes m1.l2.rounder: rounder, mode 1 lane 2, fp8e4m3, ops fadd, fmul
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [63:0] y_m1_l2;
  logic [79:0] fl_m1_l2;
  alu_core_m1_rounder #(.LANE(2)) u_m1_l2 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_l2), .fl_m1(fl_m1_l2), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1));
  assign y_m1 = y_m1_l2;
  assign fl_m1 = fl_m1_l2;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l2_fp_fma
// m1.l2.fp_fma: realized inline in the top (member top)
// ADIR-MEMBER m1_l3_unpacker
// EVOLVE-BLOCK-START
module alu_core_u_m1_l3_unpacker (
  input  logic [63:0] a,
  input  logic [63:0] b,
  input  logic [0:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [223:0] xa_m1,
  output logic [223:0] xb_m1,
  output logic [7:0] dena_m1,
  output logic [7:0] denb_m1
);
  // alu_core_u_m1_l3_unpacker: physical structure `m1.l3.unpacker` (kind unpacker, slot unpacker); realizes m1.l3.unpacker: unpacker, mode 1 lane 3, fp8e4m3, ops fadd, fmul
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [223:0] xa_m1_l3;
  logic [223:0] xb_m1_l3;
  logic [7:0] dena_m1_l3;
  logic [7:0] denb_m1_l3;
  alu_core_m1_unpacker #(.LANE(3)) u_m1_l3 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .xa_m1(xa_m1_l3), .xb_m1(xb_m1_l3), .dena_m1(dena_m1_l3), .denb_m1(denb_m1_l3));
  assign xa_m1 = xa_m1_l3;
  assign xb_m1 = xb_m1_l3;
  assign dena_m1 = dena_m1_l3;
  assign denb_m1 = denb_m1_l3;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l3_rounder
// EVOLVE-BLOCK-START
module alu_core_u_m1_l3_rounder (
  input  logic [63:0] a,
  input  logic [63:0] b,
  input  logic [0:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [63:0] y_m1,
  output logic [79:0] fl_m1,
  input  logic [223:0] xa_m1,
  input  logic [223:0] xb_m1,
  input  logic [7:0] dena_m1,
  input  logic [7:0] denb_m1,
  input  logic [223:0] x_m1
);
  // alu_core_u_m1_l3_rounder: physical structure `m1.l3.rounder` (kind rounder, slot rounder); realizes m1.l3.rounder: rounder, mode 1 lane 3, fp8e4m3, ops fadd, fmul
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [63:0] y_m1_l3;
  logic [79:0] fl_m1_l3;
  alu_core_m1_rounder #(.LANE(3)) u_m1_l3 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_l3), .fl_m1(fl_m1_l3), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1));
  assign y_m1 = y_m1_l3;
  assign fl_m1 = fl_m1_l3;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l3_fp_fma
// m1.l3.fp_fma: realized inline in the top (member top)
// ADIR-MEMBER m1_l4_unpacker
// EVOLVE-BLOCK-START
module alu_core_u_m1_l4_unpacker (
  input  logic [63:0] a,
  input  logic [63:0] b,
  input  logic [0:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [223:0] xa_m1,
  output logic [223:0] xb_m1,
  output logic [7:0] dena_m1,
  output logic [7:0] denb_m1
);
  // alu_core_u_m1_l4_unpacker: physical structure `m1.l4.unpacker` (kind unpacker, slot unpacker); realizes m1.l4.unpacker: unpacker, mode 1 lane 4, fp8e4m3, ops fadd, fmul
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [223:0] xa_m1_l4;
  logic [223:0] xb_m1_l4;
  logic [7:0] dena_m1_l4;
  logic [7:0] denb_m1_l4;
  alu_core_m1_unpacker #(.LANE(4)) u_m1_l4 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .xa_m1(xa_m1_l4), .xb_m1(xb_m1_l4), .dena_m1(dena_m1_l4), .denb_m1(denb_m1_l4));
  assign xa_m1 = xa_m1_l4;
  assign xb_m1 = xb_m1_l4;
  assign dena_m1 = dena_m1_l4;
  assign denb_m1 = denb_m1_l4;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l4_rounder
// EVOLVE-BLOCK-START
module alu_core_u_m1_l4_rounder (
  input  logic [63:0] a,
  input  logic [63:0] b,
  input  logic [0:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [63:0] y_m1,
  output logic [79:0] fl_m1,
  input  logic [223:0] xa_m1,
  input  logic [223:0] xb_m1,
  input  logic [7:0] dena_m1,
  input  logic [7:0] denb_m1,
  input  logic [223:0] x_m1
);
  // alu_core_u_m1_l4_rounder: physical structure `m1.l4.rounder` (kind rounder, slot rounder); realizes m1.l4.rounder: rounder, mode 1 lane 4, fp8e4m3, ops fadd, fmul
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [63:0] y_m1_l4;
  logic [79:0] fl_m1_l4;
  alu_core_m1_rounder #(.LANE(4)) u_m1_l4 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_l4), .fl_m1(fl_m1_l4), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1));
  assign y_m1 = y_m1_l4;
  assign fl_m1 = fl_m1_l4;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l4_fp_fma
// m1.l4.fp_fma: realized inline in the top (member top)
// ADIR-MEMBER m1_l5_unpacker
// EVOLVE-BLOCK-START
module alu_core_u_m1_l5_unpacker (
  input  logic [63:0] a,
  input  logic [63:0] b,
  input  logic [0:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [223:0] xa_m1,
  output logic [223:0] xb_m1,
  output logic [7:0] dena_m1,
  output logic [7:0] denb_m1
);
  // alu_core_u_m1_l5_unpacker: physical structure `m1.l5.unpacker` (kind unpacker, slot unpacker); realizes m1.l5.unpacker: unpacker, mode 1 lane 5, fp8e4m3, ops fadd, fmul
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [223:0] xa_m1_l5;
  logic [223:0] xb_m1_l5;
  logic [7:0] dena_m1_l5;
  logic [7:0] denb_m1_l5;
  alu_core_m1_unpacker #(.LANE(5)) u_m1_l5 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .xa_m1(xa_m1_l5), .xb_m1(xb_m1_l5), .dena_m1(dena_m1_l5), .denb_m1(denb_m1_l5));
  assign xa_m1 = xa_m1_l5;
  assign xb_m1 = xb_m1_l5;
  assign dena_m1 = dena_m1_l5;
  assign denb_m1 = denb_m1_l5;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l5_rounder
// EVOLVE-BLOCK-START
module alu_core_u_m1_l5_rounder (
  input  logic [63:0] a,
  input  logic [63:0] b,
  input  logic [0:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [63:0] y_m1,
  output logic [79:0] fl_m1,
  input  logic [223:0] xa_m1,
  input  logic [223:0] xb_m1,
  input  logic [7:0] dena_m1,
  input  logic [7:0] denb_m1,
  input  logic [223:0] x_m1
);
  // alu_core_u_m1_l5_rounder: physical structure `m1.l5.rounder` (kind rounder, slot rounder); realizes m1.l5.rounder: rounder, mode 1 lane 5, fp8e4m3, ops fadd, fmul
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [63:0] y_m1_l5;
  logic [79:0] fl_m1_l5;
  alu_core_m1_rounder #(.LANE(5)) u_m1_l5 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_l5), .fl_m1(fl_m1_l5), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1));
  assign y_m1 = y_m1_l5;
  assign fl_m1 = fl_m1_l5;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l5_fp_fma
// m1.l5.fp_fma: realized inline in the top (member top)
// ADIR-MEMBER m1_l6_unpacker
// EVOLVE-BLOCK-START
module alu_core_u_m1_l6_unpacker (
  input  logic [63:0] a,
  input  logic [63:0] b,
  input  logic [0:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [223:0] xa_m1,
  output logic [223:0] xb_m1,
  output logic [7:0] dena_m1,
  output logic [7:0] denb_m1
);
  // alu_core_u_m1_l6_unpacker: physical structure `m1.l6.unpacker` (kind unpacker, slot unpacker); realizes m1.l6.unpacker: unpacker, mode 1 lane 6, fp8e4m3, ops fadd, fmul
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [223:0] xa_m1_l6;
  logic [223:0] xb_m1_l6;
  logic [7:0] dena_m1_l6;
  logic [7:0] denb_m1_l6;
  alu_core_m1_unpacker #(.LANE(6)) u_m1_l6 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .xa_m1(xa_m1_l6), .xb_m1(xb_m1_l6), .dena_m1(dena_m1_l6), .denb_m1(denb_m1_l6));
  assign xa_m1 = xa_m1_l6;
  assign xb_m1 = xb_m1_l6;
  assign dena_m1 = dena_m1_l6;
  assign denb_m1 = denb_m1_l6;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l6_rounder
// EVOLVE-BLOCK-START
module alu_core_u_m1_l6_rounder (
  input  logic [63:0] a,
  input  logic [63:0] b,
  input  logic [0:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [63:0] y_m1,
  output logic [79:0] fl_m1,
  input  logic [223:0] xa_m1,
  input  logic [223:0] xb_m1,
  input  logic [7:0] dena_m1,
  input  logic [7:0] denb_m1,
  input  logic [223:0] x_m1
);
  // alu_core_u_m1_l6_rounder: physical structure `m1.l6.rounder` (kind rounder, slot rounder); realizes m1.l6.rounder: rounder, mode 1 lane 6, fp8e4m3, ops fadd, fmul
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [63:0] y_m1_l6;
  logic [79:0] fl_m1_l6;
  alu_core_m1_rounder #(.LANE(6)) u_m1_l6 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_l6), .fl_m1(fl_m1_l6), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1));
  assign y_m1 = y_m1_l6;
  assign fl_m1 = fl_m1_l6;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l6_fp_fma
// m1.l6.fp_fma: realized inline in the top (member top)
// ADIR-MEMBER m1_l7_unpacker
// EVOLVE-BLOCK-START
module alu_core_u_m1_l7_unpacker (
  input  logic [63:0] a,
  input  logic [63:0] b,
  input  logic [0:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [223:0] xa_m1,
  output logic [223:0] xb_m1,
  output logic [7:0] dena_m1,
  output logic [7:0] denb_m1
);
  // alu_core_u_m1_l7_unpacker: physical structure `m1.l7.unpacker` (kind unpacker, slot unpacker); realizes m1.l7.unpacker: unpacker, mode 1 lane 7, fp8e4m3, ops fadd, fmul
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [223:0] xa_m1_l7;
  logic [223:0] xb_m1_l7;
  logic [7:0] dena_m1_l7;
  logic [7:0] denb_m1_l7;
  alu_core_m1_unpacker #(.LANE(7)) u_m1_l7 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .xa_m1(xa_m1_l7), .xb_m1(xb_m1_l7), .dena_m1(dena_m1_l7), .denb_m1(denb_m1_l7));
  assign xa_m1 = xa_m1_l7;
  assign xb_m1 = xb_m1_l7;
  assign dena_m1 = dena_m1_l7;
  assign denb_m1 = denb_m1_l7;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l7_rounder
// EVOLVE-BLOCK-START
module alu_core_u_m1_l7_rounder (
  input  logic [63:0] a,
  input  logic [63:0] b,
  input  logic [0:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [63:0] y_m1,
  output logic [79:0] fl_m1,
  input  logic [223:0] xa_m1,
  input  logic [223:0] xb_m1,
  input  logic [7:0] dena_m1,
  input  logic [7:0] denb_m1,
  input  logic [223:0] x_m1
);
  // alu_core_u_m1_l7_rounder: physical structure `m1.l7.rounder` (kind rounder, slot rounder); realizes m1.l7.rounder: rounder, mode 1 lane 7, fp8e4m3, ops fadd, fmul
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [63:0] y_m1_l7;
  logic [79:0] fl_m1_l7;
  alu_core_m1_rounder #(.LANE(7)) u_m1_l7 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_l7), .fl_m1(fl_m1_l7), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1));
  assign y_m1 = y_m1_l7;
  assign fl_m1 = fl_m1_l7;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l7_fp_fma
// m1.l7.fp_fma: realized inline in the top (member top)
// ADIR-MEMBER m1_l0_fp_multiplier
// EVOLVE-BLOCK-START
module alu_core_u_m1_l0_fp_multiplier (
  input  logic [63:0] a,
  input  logic [63:0] b,
  input  logic [0:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [63:0] y_m1,
  output logic [79:0] fl_m1,
  input  logic [223:0] xa_m1,
  input  logic [223:0] xb_m1,
  input  logic [7:0] dena_m1,
  input  logic [7:0] denb_m1,
  output logic [223:0] x_m1
);
  // alu_core_u_m1_l0_fp_multiplier: physical structure `m1.l0.fp_multiplier` (kind fp_multiplier, slot fp_multiplier); realizes m1.l0.fp_multiplier: fp_multiplier, mode 1 lane 0, fp8e4m3, ops fmul
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [63:0] y_m1_l0;
  logic [79:0] fl_m1_l0;
  logic [223:0] x_m1_l0;
  alu_core_m1_fp_multiplier #(.LANE(0)) u_m1_l0 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_l0), .fl_m1(fl_m1_l0), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1_l0));
  assign y_m1 = y_m1_l0;
  assign fl_m1 = fl_m1_l0;
  assign x_m1 = x_m1_l0;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l1_fp_multiplier
// EVOLVE-BLOCK-START
module alu_core_u_m1_l1_fp_multiplier (
  input  logic [63:0] a,
  input  logic [63:0] b,
  input  logic [0:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [63:0] y_m1,
  output logic [79:0] fl_m1,
  input  logic [223:0] xa_m1,
  input  logic [223:0] xb_m1,
  input  logic [7:0] dena_m1,
  input  logic [7:0] denb_m1,
  output logic [223:0] x_m1
);
  // alu_core_u_m1_l1_fp_multiplier: physical structure `m1.l1.fp_multiplier` (kind fp_multiplier, slot fp_multiplier); realizes m1.l1.fp_multiplier: fp_multiplier, mode 1 lane 1, fp8e4m3, ops fmul
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [63:0] y_m1_l1;
  logic [79:0] fl_m1_l1;
  logic [223:0] x_m1_l1;
  alu_core_m1_fp_multiplier #(.LANE(1)) u_m1_l1 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_l1), .fl_m1(fl_m1_l1), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1_l1));
  assign y_m1 = y_m1_l1;
  assign fl_m1 = fl_m1_l1;
  assign x_m1 = x_m1_l1;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l2_fp_multiplier
// EVOLVE-BLOCK-START
module alu_core_u_m1_l2_fp_multiplier (
  input  logic [63:0] a,
  input  logic [63:0] b,
  input  logic [0:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [63:0] y_m1,
  output logic [79:0] fl_m1,
  input  logic [223:0] xa_m1,
  input  logic [223:0] xb_m1,
  input  logic [7:0] dena_m1,
  input  logic [7:0] denb_m1,
  output logic [223:0] x_m1
);
  // alu_core_u_m1_l2_fp_multiplier: physical structure `m1.l2.fp_multiplier` (kind fp_multiplier, slot fp_multiplier); realizes m1.l2.fp_multiplier: fp_multiplier, mode 1 lane 2, fp8e4m3, ops fmul
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [63:0] y_m1_l2;
  logic [79:0] fl_m1_l2;
  logic [223:0] x_m1_l2;
  alu_core_m1_fp_multiplier #(.LANE(2)) u_m1_l2 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_l2), .fl_m1(fl_m1_l2), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1_l2));
  assign y_m1 = y_m1_l2;
  assign fl_m1 = fl_m1_l2;
  assign x_m1 = x_m1_l2;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l3_fp_multiplier
// EVOLVE-BLOCK-START
module alu_core_u_m1_l3_fp_multiplier (
  input  logic [63:0] a,
  input  logic [63:0] b,
  input  logic [0:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [63:0] y_m1,
  output logic [79:0] fl_m1,
  input  logic [223:0] xa_m1,
  input  logic [223:0] xb_m1,
  input  logic [7:0] dena_m1,
  input  logic [7:0] denb_m1,
  output logic [223:0] x_m1
);
  // alu_core_u_m1_l3_fp_multiplier: physical structure `m1.l3.fp_multiplier` (kind fp_multiplier, slot fp_multiplier); realizes m1.l3.fp_multiplier: fp_multiplier, mode 1 lane 3, fp8e4m3, ops fmul
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [63:0] y_m1_l3;
  logic [79:0] fl_m1_l3;
  logic [223:0] x_m1_l3;
  alu_core_m1_fp_multiplier #(.LANE(3)) u_m1_l3 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_l3), .fl_m1(fl_m1_l3), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1_l3));
  assign y_m1 = y_m1_l3;
  assign fl_m1 = fl_m1_l3;
  assign x_m1 = x_m1_l3;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l4_fp_multiplier
// EVOLVE-BLOCK-START
module alu_core_u_m1_l4_fp_multiplier (
  input  logic [63:0] a,
  input  logic [63:0] b,
  input  logic [0:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [63:0] y_m1,
  output logic [79:0] fl_m1,
  input  logic [223:0] xa_m1,
  input  logic [223:0] xb_m1,
  input  logic [7:0] dena_m1,
  input  logic [7:0] denb_m1,
  output logic [223:0] x_m1
);
  // alu_core_u_m1_l4_fp_multiplier: physical structure `m1.l4.fp_multiplier` (kind fp_multiplier, slot fp_multiplier); realizes m1.l4.fp_multiplier: fp_multiplier, mode 1 lane 4, fp8e4m3, ops fmul
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [63:0] y_m1_l4;
  logic [79:0] fl_m1_l4;
  logic [223:0] x_m1_l4;
  alu_core_m1_fp_multiplier #(.LANE(4)) u_m1_l4 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_l4), .fl_m1(fl_m1_l4), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1_l4));
  assign y_m1 = y_m1_l4;
  assign fl_m1 = fl_m1_l4;
  assign x_m1 = x_m1_l4;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l5_fp_multiplier
// EVOLVE-BLOCK-START
module alu_core_u_m1_l5_fp_multiplier (
  input  logic [63:0] a,
  input  logic [63:0] b,
  input  logic [0:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [63:0] y_m1,
  output logic [79:0] fl_m1,
  input  logic [223:0] xa_m1,
  input  logic [223:0] xb_m1,
  input  logic [7:0] dena_m1,
  input  logic [7:0] denb_m1,
  output logic [223:0] x_m1
);
  // alu_core_u_m1_l5_fp_multiplier: physical structure `m1.l5.fp_multiplier` (kind fp_multiplier, slot fp_multiplier); realizes m1.l5.fp_multiplier: fp_multiplier, mode 1 lane 5, fp8e4m3, ops fmul
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [63:0] y_m1_l5;
  logic [79:0] fl_m1_l5;
  logic [223:0] x_m1_l5;
  alu_core_m1_fp_multiplier #(.LANE(5)) u_m1_l5 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_l5), .fl_m1(fl_m1_l5), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1_l5));
  assign y_m1 = y_m1_l5;
  assign fl_m1 = fl_m1_l5;
  assign x_m1 = x_m1_l5;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l6_fp_multiplier
// EVOLVE-BLOCK-START
module alu_core_u_m1_l6_fp_multiplier (
  input  logic [63:0] a,
  input  logic [63:0] b,
  input  logic [0:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [63:0] y_m1,
  output logic [79:0] fl_m1,
  input  logic [223:0] xa_m1,
  input  logic [223:0] xb_m1,
  input  logic [7:0] dena_m1,
  input  logic [7:0] denb_m1,
  output logic [223:0] x_m1
);
  // alu_core_u_m1_l6_fp_multiplier: physical structure `m1.l6.fp_multiplier` (kind fp_multiplier, slot fp_multiplier); realizes m1.l6.fp_multiplier: fp_multiplier, mode 1 lane 6, fp8e4m3, ops fmul
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [63:0] y_m1_l6;
  logic [79:0] fl_m1_l6;
  logic [223:0] x_m1_l6;
  alu_core_m1_fp_multiplier #(.LANE(6)) u_m1_l6 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_l6), .fl_m1(fl_m1_l6), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1_l6));
  assign y_m1 = y_m1_l6;
  assign fl_m1 = fl_m1_l6;
  assign x_m1 = x_m1_l6;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l7_fp_multiplier
// EVOLVE-BLOCK-START
module alu_core_u_m1_l7_fp_multiplier (
  input  logic [63:0] a,
  input  logic [63:0] b,
  input  logic [0:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [63:0] y_m1,
  output logic [79:0] fl_m1,
  input  logic [223:0] xa_m1,
  input  logic [223:0] xb_m1,
  input  logic [7:0] dena_m1,
  input  logic [7:0] denb_m1,
  output logic [223:0] x_m1
);
  // alu_core_u_m1_l7_fp_multiplier: physical structure `m1.l7.fp_multiplier` (kind fp_multiplier, slot fp_multiplier); realizes m1.l7.fp_multiplier: fp_multiplier, mode 1 lane 7, fp8e4m3, ops fmul
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [63:0] y_m1_l7;
  logic [79:0] fl_m1_l7;
  logic [223:0] x_m1_l7;
  alu_core_m1_fp_multiplier #(.LANE(7)) u_m1_l7 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_l7), .fl_m1(fl_m1_l7), .xa_m1(xa_m1), .xb_m1(xb_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .x_m1(x_m1_l7));
  assign y_m1 = y_m1_l7;
  assign fl_m1 = fl_m1_l7;
  assign x_m1 = x_m1_l7;
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


// lzd_cell_tree (pair_cell, binary_count, valid flags flat): the leading zeros of a 12-bit word
module fam_count_lzd_pair_cell_binary_count_vflat_w12 (input logic [11:0] a, output logic [3:0] n);
  logic v0_0; assign v0_0 = a[11] | a[10];
  logic p0_0; assign p0_0 = ~a[11];
  logic v0_1; assign v0_1 = a[9] | a[8];
  logic p0_1; assign p0_1 = ~a[9];
  logic v0_2; assign v0_2 = a[7] | a[6];
  logic p0_2; assign p0_2 = ~a[7];
  logic v0_3; assign v0_3 = a[5] | a[4];
  logic p0_3; assign p0_3 = ~a[5];
  logic v0_4; assign v0_4 = a[3] | a[2];
  logic p0_4; assign p0_4 = ~a[3];
  logic v0_5; assign v0_5 = a[1] | a[0];
  logic p0_5; assign p0_5 = ~a[1];
  logic v0_6; assign v0_6 = 1'b0 | 1'b0;
  logic p0_6; assign p0_6 = ~1'b0;
  logic v0_7; assign v0_7 = 1'b0 | 1'b0;
  logic p0_7; assign p0_7 = ~1'b0;
  logic v1_0; assign v1_0 = a[11] | a[10] | a[9] | a[8];
  logic [1:0] p1_0; assign p1_0 = v0_0 ? {1'b0, p0_0} : {1'b1, p0_1};
  logic v1_1; assign v1_1 = a[7] | a[6] | a[5] | a[4];
  logic [1:0] p1_1; assign p1_1 = v0_2 ? {1'b0, p0_2} : {1'b1, p0_3};
  logic v1_2; assign v1_2 = a[3] | a[2] | a[1] | a[0];
  logic [1:0] p1_2; assign p1_2 = v0_4 ? {1'b0, p0_4} : {1'b1, p0_5};
  logic v1_3; assign v1_3 = 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [1:0] p1_3; assign p1_3 = v0_6 ? {1'b0, p0_6} : {1'b1, p0_7};
  logic v2_0; assign v2_0 = a[11] | a[10] | a[9] | a[8] | a[7] | a[6] | a[5] | a[4];
  logic [2:0] p2_0; assign p2_0 = v1_0 ? {1'b0, p1_0} : {1'b1, p1_1};
  logic v2_1; assign v2_1 = a[3] | a[2] | a[1] | a[0] | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [2:0] p2_1; assign p2_1 = v1_2 ? {1'b0, p1_2} : {1'b1, p1_3};
  logic v3_0; assign v3_0 = a[11] | a[10] | a[9] | a[8] | a[7] | a[6] | a[5] | a[4] | a[3] | a[2] | a[1] | a[0] | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [3:0] p3_0; assign p3_0 = v2_0 ? {1'b0, p2_0} : {1'b1, p2_1};
  assign n = v3_0 ? p3_0 : 4'd12;
endmodule



// lzd_cell_tree (pair_cell, binary_count, valid flags flat): the leading zeros of a 4-bit word
module fam_count_lzd_pair_cell_binary_count_vflat_w4 (input logic [3:0] a, output logic [2:0] n);
  logic v0_0; assign v0_0 = a[3] | a[2];
  logic p0_0; assign p0_0 = ~a[3];
  logic v0_1; assign v0_1 = a[1] | a[0];
  logic p0_1; assign p0_1 = ~a[1];
  logic v1_0; assign v1_0 = a[3] | a[2] | a[1] | a[0];
  logic [1:0] p1_0; assign p1_0 = v0_0 ? {1'b0, p0_0} : {1'b1, p0_1};
  assign n = v1_0 ? {1'd0, p1_0} : 3'd4;
endmodule


// fp significand adder (single_path): 1 path; operands ordered by magnitude before one shifter; align full_align on a barrel_mux_tree shifter, sticky by or_tree_shifted_out; significand adder ripple_carry; leading zeros by lza (lzd_cell_tree, single_indicator); normalize coarse_fine on a barrel_mux_tree shifter; exponent path on ripple_carry adders; subnormals as stored; window of 8 guard bits below the larger operand's lsb (the significands are the unpacker's: 4 stored bits)
module fam_fp_add_single_path_x12e12s4_p9d459d224988 (
  input logic [27:0] xa,
  input logic [27:0] xb,
  input logic sub,
  output logic [27:0] y
);
  logic [1:0] a_sp; assign a_sp = xa[27:26];
  logic a_s; assign a_s = xa[25];
  logic signed [11:0] a_e; assign a_e = $signed(xa[24:13]);
  logic [11:0] a_sig; assign a_sig = xa[12:1];
  logic a_st; assign a_st = xa[0];
  logic a_z; assign a_z = (a_sp == 2'd0) && (a_sig == 0) && !a_st;
  logic [27:0] xbs; assign xbs = {xb[27:26], xb[25] ^ sub, xb[24:0]};
  logic [1:0] b_sp; assign b_sp = xbs[27:26];
  logic b_s; assign b_s = xbs[25];
  logic signed [11:0] b_e; assign b_e = $signed(xbs[24:13]);
  logic [11:0] b_sig; assign b_sig = xbs[12:1];
  logic b_st; assign b_st = xbs[0];
  logic b_z; assign b_z = (b_sp == 2'd0) && (b_sig == 0) && !b_st;
  logic signed [12:0] eax; assign eax = $signed({a_e[11], a_e});
  logic signed [12:0] ebx; assign ebx = $signed({b_e[11], b_e});
  logic [12:0] d_nb; assign d_nb = ~(ebx);
  logic signed [12:0] d;
  // the exponent difference
  fam_adder_ripple_carry #(.W(13), .CHUNK(1), .FORM(0)) u1 (.a(eax), .b(d_nb), .cin(1'b1), .s(d), .cout());
  logic signed [12:0] zero_x; assign zero_x = 13'sd0;
  logic [12:0] dn_nb; assign dn_nb = ~(d);
  logic signed [12:0] dn;
  // the difference negated
  fam_adder_ripple_carry #(.W(13), .CHUNK(1), .FORM(0)) u2 (.a(zero_x), .b(dn_nb), .cin(1'b1), .s(dn), .cout());
  logic a_big; assign a_big = (d > 0) || (d == 0 && a_sig >= b_sig);
  logic [12:0] dabs; assign dabs = a_big ? d : dn;
  logic signed [11:0] e_big; assign e_big = a_big ? a_e : b_e;
  logic s_big; assign s_big = a_big ? a_s : b_s;
  logic eff_sub; assign eff_sub = a_s ^ b_s;
  logic [11:0] big_sig; assign big_sig = a_big ? a_sig : b_sig;
  logic [11:0] sml_sig; assign sml_sig = a_big ? b_sig : a_sig;
  logic big_st; assign big_st = a_big ? a_st : b_st;
  logic sml_st; assign sml_st = a_big ? b_st : a_st;
  logic [12:0] mb; assign mb = {1'b0, big_sig[3:0], 8'd0};
  logic [12:0] ms0; assign ms0 = {1'b0, sml_sig[3:0], 8'd0};
  logic far_f; assign far_f = 1'b1 && (dabs > 12);
  logic [3:0] amt_f; assign amt_f = (!(1'b1) || far_f) ? 4'd0 : dabs[3:0];
  logic [12:0] mssh_f;
  logic stk0_f;
  // align: the operand shifted right by the exponent difference
  fam_shift_barrel_mux_tree #(.W(13), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u3 (.a(ms0), .amt(amt_f), .op(3'd1), .y(mssh_f), .sticky());
  assign stk0_f = |(ms0 & ((3'd1 == 3'd0) ? ~({13{1'b1}} >> amt_f) : ~({13{1'b1}} << amt_f)));
  logic [12:0] m_f; assign m_f = far_f ? 13'd0 : mssh_f;
  logic stk_f; assign stk_f = far_f ? (sml_sig != 0) : stk0_f;
  logic stb_f; assign stb_f = sml_st | stk_f;
  logic [12:0] ms_f; assign ms_f = m_f;
  logic [12:0] bop_f; assign bop_f = eff_sub ? ~ms_f : ms_f;
  logic cin_f; assign cin_f = eff_sub ? ~stb_f : 1'b0;
  logic co_f;
  logic [12:0] r_f;
  // add: the significand adder (ripple_carry)
  fam_adder_ripple_carry #(.W(13), .CHUNK(1), .FORM(0)) u4 (.a(mb), .b(bop_f), .cin(cin_f), .s(r_f), .cout(co_f));
  logic st_f; assign st_f = big_st | stb_f;
  logic ovf_f; assign ovf_f = r_f[12];
  logic [11:0] sig0_f; assign sig0_f = ovf_f ? r_f[12:1] : r_f[11:0];
  logic st0_f; assign st0_f = st_f | (ovf_f & r_f[0]);
  logic signed [11:0] e0n_f_c; assign e0n_f_c = -12'sd8;
  logic signed [11:0] e0n_f;
  // normalize: the window's exponent origin
  fam_adder_ripple_carry #(.W(12), .CHUNK(1), .FORM(0)) u5 (.a(e_big), .b(e0n_f_c), .cin(1'b0), .s(e0n_f), .cout());
  logic signed [11:0] e0o_f_c; assign e0o_f_c = -12'sd7;
  logic signed [11:0] e0o_f;
  // normalize: the window's exponent origin after a carry out
  fam_adder_ripple_carry #(.W(12), .CHUNK(1), .FORM(0)) u6 (.a(e_big), .b(e0o_f_c), .cin(1'b0), .s(e0o_f), .cout());
  logic signed [11:0] e0_f; assign e0_f = ovf_f ? e0o_f : e0n_f;
  logic [12:0] t_f0; assign t_f0 = mb ^ bop_f;
  logic [12:0] g_f0; assign g_f0 = mb & bop_f;
  logic [12:0] z_f0; assign z_f0 = ~mb & ~bop_f;
  logic [12:0] f_f0;
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
  assign f_f0[12] = (1'b0 & ((g_f0[12] & ~z_f0[11]) | (z_f0[12] & ~g_f0[11]))) | (~1'b0 & ((z_f0[12] & ~z_f0[11]) | (g_f0[12] & ~g_f0[11])));
  logic [11:0] fw_f0; assign fw_f0 = ovf_f ? f_f0[12:1] : f_f0[11:0];
  logic [11:0] fws_f; assign fws_f = fw_f0;
  logic [3:0] lzp_f;
  // normalize: leading zeros of the indicator string
  fam_count_lzd_pair_cell_binary_count_vflat_w12 u7 (.a(fws_f), .n(lzp_f));
  logic [3:0] lzs_f; assign lzs_f = (!eff_sub || fws_f == 0) ? 4'd0 : lzp_f[3:0];
  logic fz_f; assign fz_f = fws_f == 0;
  logic [3:0] cshift_f; assign cshift_f = {lzs_f[3:2], 2'd0};
  logic [3:0] fshift_f; assign fshift_f = {{(4-2){1'b0}}, lzs_f[1:0]};
  logic [11:0] sigc_f;
  // normalize: the coarse normalize stage (multiples of 4)
  fam_shift_barrel_mux_tree #(.W(12), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u8 (.a(sig0_f), .amt(cshift_f), .op(3'd0), .y(sigc_f), .sticky());
  logic [11:0] sign_f;
  // normalize: the fine normalize stage
  fam_shift_barrel_mux_tree #(.W(12), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u9 (.a(sigc_f), .amt(fshift_f), .op(3'd0), .y(sign_f), .sticky());
  logic signed [11:0] lzx_f; assign lzx_f = $signed({{(12-4){1'b0}}, lzs_f});
  logic [11:0] en_f_nb; assign en_f_nb = ~(lzx_f);
  logic signed [11:0] en_f;
  // normalize: the exponent lowered by the normalize count
  fam_adder_ripple_carry #(.W(12), .CHUNK(1), .FORM(0)) u10 (.a(e0_f), .b(en_f_nb), .cin(1'b1), .s(en_f), .cout());
  logic fix_f; assign fix_f = ~sign_f[11] && (sign_f != 0);
  logic [11:0] sigf_f; assign sigf_f = fix_f ? {sign_f[10:0], 1'b0} : sign_f;
  logic signed [11:0] enm_f_c; assign enm_f_c = -12'sd1;
  logic signed [11:0] enm_f;
  // normalize: the exponent of the corrected position
  fam_adder_ripple_carry #(.W(12), .CHUNK(1), .FORM(0)) u11 (.a(en_f), .b(enm_f_c), .cin(1'b0), .s(enm_f), .cout());
  logic signed [11:0] ef_f; assign ef_f = fix_f ? enm_f : en_f;
  logic zero_f; assign zero_f = (sigf_f == 0) && !st0_f;
  logic sr_f; assign sr_f = zero_f ? 1'b0 : s_big;
  logic [27:0] y_f; assign y_f = {2'd0, sr_f, ef_f, sigf_f, st0_f};
  logic both_inf; assign both_inf = (a_sp == 2'd2) && (b_sp == 2'd2);
  logic [27:0] y_sp; assign y_sp = (a_sp == 2'd1 || b_sp == 2'd1) ? {2'd1, 1'b0, 12'sd0, 12'd0, 1'b0} : both_inf ? ((a_s == b_s) ? {2'd2, a_s, 12'sd0, 12'd0, 1'b0} : {2'd1, 1'b0, 12'sd0, 12'd0, 1'b0}) : (a_sp == 2'd2) ? {2'd2, a_s, 12'sd0, 12'd0, 1'b0} : (b_sp == 2'd2) ? {2'd2, b_s, 12'sd0, 12'd0, 1'b0} : a_z ? xbs : b_z ? xa : y_f;
  assign y = y_sp;
endmodule

// fp significand multiplier (sig_mul_then_round): behavioral_star over the 4-bit significands, the exact product in the X field, the exponent sum on a ripple_carry adder
module fam_fp_mul_sig_mul_then_round_x12e12s4_pbd766efe148c (
  input logic [27:0] xa,
  input logic [27:0] xb,
  output logic [27:0] y
);
  logic [1:0] a_sp; assign a_sp = xa[27:26];
  logic a_s; assign a_s = xa[25];
  logic signed [11:0] a_e; assign a_e = $signed(xa[24:13]);
  logic [11:0] a_sig; assign a_sig = xa[12:1];
  logic a_st; assign a_st = xa[0];
  logic a_z; assign a_z = (a_sp == 2'd0) && (a_sig == 0) && !a_st;
  logic [1:0] b_sp; assign b_sp = xb[27:26];
  logic b_s; assign b_s = xb[25];
  logic signed [11:0] b_e; assign b_e = $signed(xb[24:13]);
  logic [11:0] b_sig; assign b_sig = xb[12:1];
  logic b_st; assign b_st = xb[0];
  logic b_z; assign b_z = (b_sp == 2'd0) && (b_sig == 0) && !b_st;
  logic s; assign s = a_s ^ b_s;
  logic [3:0] sa; assign sa = a_sig[3:0];
  logic [3:0] sb; assign sb = b_sig[3:0];
  logic [7:0] p;
  // the significand product (behavioral_star)
  fam_mul_behavioral_star_w4_u_pfc463c41 u1 (.a(sa), .b(sb), .p(p));
  logic signed [11:0] e;
  // the exponent sum
  fam_adder_ripple_carry #(.W(12), .CHUNK(1), .FORM(0)) u2 (.a(a_e), .b(b_e), .cin(1'b0), .s(e), .cout());
  logic st; assign st = a_st | b_st;
  logic [27:0] y_fin; assign y_fin = {2'd0, s, e, {{(12-8){1'b0}}, p}, st};
  logic [27:0] y_sp; assign y_sp = (a_sp == 2'd1 || b_sp == 2'd1) ? {2'd1, 1'b0, 12'sd0, 12'd0, 1'b0} : (a_sp == 2'd2 || b_sp == 2'd2) ? (((a_sp == 2'd0 && a_z) || (b_sp == 2'd0 && b_z)) ? {2'd1, 1'b0, 12'sd0, 12'd0, 1'b0} : {2'd2, s, 12'sd0, 12'd0, 1'b0}) : y_fin;
  assign y = y_sp;
endmodule

// fp rounder (dedicated_per_op, rounding increment_adder, leading zeros lzd_cell_tree, shifts barrel_mux_tree, exponent ripple_carry / prefix_and_incrementer): X -> fp8e4m3 pattern and flags
module fam_fp_round_dedicated_per_op_increment_adder_fp8e4m3_x12e12s4_pd77ccc5b5c45 (
  input logic [27:0] x,
  input logic [2:0] rnd,
  input logic [7:0] word,
  input logic ftz,
  output logic [9:0] fl,
  output logic [7:0] bits
);
  logic [1:0] x_sp; assign x_sp = x[27:26];
  logic x_s; assign x_s = x[25];
  logic signed [11:0] x_e; assign x_e = $signed(x[24:13]);
  logic [11:0] x_sig; assign x_sig = x[12:1];
  logic x_st; assign x_st = x[0];
  logic x_z; assign x_z = (x_sp == 2'd0) && (x_sig == 0) && !x_st;
  logic s; assign s = x_s & 1'd1;
  logic lone; assign lone = (x_sig == 0) && x_st;
  logic [11:0] sig_in; assign sig_in = lone ? 12'd1 : x_sig;
  logic signed [11:0] e_lone_c; assign e_lone_c = -12'sd12;
  logic signed [11:0] e_lone;
  // the exponent of a lone sticky's unit
  fam_adder_ripple_carry #(.W(12), .CHUNK(1), .FORM(0)) u1 (.a(x_e), .b(e_lone_c), .cin(1'b0), .s(e_lone), .cout());
  logic signed [11:0] e_in; assign e_in = lone ? e_lone : x_e;
  logic [3:0] lz;
  // the normalizer's leading-zero count
  fam_count_lzd_pair_cell_binary_count_vflat_w12 u2 (.a(sig_in), .n(lz));
  logic [3:0] lzs; assign lzs = (sig_in == 0) ? 4'd0 : lz[3:0];
  logic [11:0] sig;
  // the normalizer's left shift
  fam_shift_barrel_mux_tree #(.W(12), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u3 (.a(sig_in), .amt(lzs), .op(3'd0), .y(sig), .sticky());
  logic signed [11:0] lzx; assign lzx = $signed({{(12-4){1'b0}}, lzs});
  logic [11:0] e_nb; assign e_nb = ~(lzx);
  logic signed [11:0] e;
  // the exponent lowered by the normalize count
  fam_adder_ripple_carry #(.W(12), .CHUNK(1), .FORM(0)) u4 (.a(e_in), .b(e_nb), .cin(1'b1), .s(e), .cout());
  logic normal; assign normal = e >= -12'sd17;
  logic signed [12:0] shc; assign shc = -13'sd9;
  logic signed [12:0] ex; assign ex = $signed({e[11], e});
  logic [12:0] shsub_nb; assign shsub_nb = ~(ex);
  logic signed [12:0] shsub;
  // the subnormal result's extra right shift
  fam_adder_ripple_carry #(.W(13), .CHUNK(1), .FORM(0)) u5 (.a(shc), .b(shsub_nb), .cin(1'b1), .s(shsub), .cout());
  logic signed [12:0] sht; assign sht = normal ? 13'sd8 : shsub;
  logic signed [12:0] sh; assign sh = (sht > 13'sd13) ? 13'sd13 : sht;
  logic [3:0] sha; assign sha = sh[3:0];
  logic [12:0] sigw; assign sigw = {1'b0, sig};
  logic [3:0] shk; assign shk = (sh > 13'sd12) ? 4'd12 : sha;
  logic [12:0] keep;
  // the right shift to the kept bits
  fam_shift_barrel_mux_tree #(.W(13), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u6 (.a(sigw), .amt(shk), .op(3'd1), .y(keep), .sticky());
  // the mask of the dropped positions
  logic [12:0] restmask;
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
  logic [12:0] rest; assign rest = sigw & restmask;
  // the half position (one below the kept lsb)
  logic [12:0] halfv;
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
  logic [12:0] keepn; assign keepn = sigw >> 8;
  logic [12:0] restn; assign restn = sigw & ({1'b0, {12{1'b1}}} >> 4);
  logic [12:0] halfn; assign halfn = {12'd0, 1'b1} << 7;
  logic inexact; assign inexact = (rest != 0) | x_st;
  logic [20:0] restw; assign restw = {rest, 8'd0};
  logic [4:0] fsh; assign fsh = sht[4:0];
  logic [20:0] fint0;
  // the dropped bits aligned to the stochastic word
  fam_shift_barrel_mux_tree #(.W(21), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u7 (.a(restw), .amt(fsh), .op(3'd1), .y(fint0), .sticky());
  logic [20:0] fint; assign fint = (sht > 13'sd20) ? 21'd0 : fint0;
  logic [20:0] fintn; assign fintn = restn >> 0;
  logic gt_half; assign gt_half = rest > halfv;
  logic half_eq; assign half_eq = (rest == halfv) && (halfv != 0);
  logic up; assign up = (rnd == 3'd0) ? (gt_half || (half_eq && (x_st || keep[0]))) : (rnd == 3'd1) ? 1'b0 : (rnd == 3'd2) ? (inexact && s) : (rnd == 3'd3) ? (inexact && !s) : (rnd == 3'd4) ? (inexact && (0 ? (fint >= word) : (fint > word))) : inexact;
  logic gt_halfn; assign gt_halfn = restn > halfn;
  logic half_eqn; assign half_eqn = (restn == halfn) && (halfn != 0);
  logic upn; assign upn = (rnd == 3'd0) ? (gt_halfn || (half_eqn && (x_st || keepn[0]))) : (rnd == 3'd1) ? 1'b0 : (rnd == 3'd2) ? (((restn != 0) | x_st) && s) : (rnd == 3'd3) ? (((restn != 0) | x_st) && !s) : (rnd == 3'd4) ? (((restn != 0) | x_st) && (0 ? (fintn >= word) : (fintn > word))) : ((restn != 0) | x_st);
  logic rounded; assign rounded = x_sp == 2'd3;
  logic upr; assign upr = rounded ? 1'b0 : up;
  logic inexact_r; assign inexact_r = rounded | inexact;
  logic carry_n; assign carry_n = upn && (&keepn[3:0]);
  logic [12:0] mag;
  logic [12:0] mag0;
  // the rounding increment (prefix_and_incrementer)
  fam_incr_prefix_and #(.W(13), .STRUCTURE(0), .B(4), .TOPO(0)) u8 (.a(keep), .cin(upr), .s(mag0), .cout());
  assign mag = mag0;
  logic signed [11:0] bfield_c; assign bfield_c = 12'sd18;
  logic signed [11:0] bfield;
  // the biased exponent field
  fam_adder_ripple_carry #(.W(12), .CHUNK(1), .FORM(0)) u9 (.a(e), .b(bfield_c), .cin(1'b0), .s(bfield), .cout());
  logic [11:0] bfu; assign bfu = bfield;
  logic [11:0] efield;
  // the exponent field incremented on a rounding carry (prefix_and_incrementer)
  fam_incr_prefix_and #(.W(12), .STRUCTURE(0), .B(4), .TOPO(0)) u10 (.a(bfu), .cin(mag[4]), .s(efield), .cout());
  logic [20:0] code; assign code = normal ? {{(21-12-3){1'b0}}, efield, mag[2:0]} : {{(21-13){1'b0}}, mag};
  logic tiny; assign tiny = (e < -12'sd17) && !(e == -12'sd18 && carry_n) && !(e == -12'sd18 && carry_n);
  logic ovf; assign ovf = code > 21'd126;
  logic to_inf; assign to_inf = 0 && (rnd == 3'd0 || (rnd == 3'd3 && !s) || (rnd == 3'd2 && s) || rnd == 3'd5 || (rnd == 3'd4 && (e > -12'sd3 || up)));
  logic ftz_hit; assign ftz_hit = ftz && code[6:3] == 0 && (code[2:0] != 0);
  logic is_zero; assign is_zero = (x_sig == 0) && (!x_st || rounded);
  logic tiny_r; assign tiny_r = rounded ? x_st : tiny;
  logic [9:0] fl_fin; assign fl_fin = ovf ? ((1 << 2) | (1 << 4)) : ((inexact_r ? (1 << 4) : 0) | ((tiny_r && inexact_r) ? (1 << 3) : 0) | (ftz_hit ? ((1 << 4) | (1 << 3)) : 0));
  logic [7:0] bits_fin; assign bits_fin = ovf ? (to_inf ? {s, 7'd126} : {s, 7'd126}) : (ftz_hit ? {s, 7'd0} : {s, code[6:0]});
  logic [9:0] fl_zero; assign fl_zero = rounded ? ((1 << 4) | (1 << 3)) : 10'd0;
  assign fl = (x_sp == 2'd1) ? (1 << 5) : (x_sp == 2'd2) ? ((1 << 4) | (1 << 2)) : is_zero ? fl_zero : fl_fin;
  assign bits = (x_sp == 2'd1) ? 8'd127 : (x_sp == 2'd2) ? {s, 7'd126} : is_zero ? (rounded ? {s, 7'd0} : 8'd0) : bits_fin;
endmodule

// fp unpacker (per_unit_unpack): fp8e4m3 pattern -> V; the fields split, the specials decoded, the hidden one restored, a subnormal normalized in the unpacker
module fam_fp_unpack_per_unit_unpack_fp8e4m3_x12e12s4_p9bfe39588414 (
  input logic [7:0] b,
  input logic daz,
  output logic [19:0] u
);
  logic [3:0] e; assign e = b[6:3];
  logic [2:0] mant; assign mant = b[2:0];
  logic s; assign s = b[7];
  logic nan; assign nan = (e == 4'd15 && mant == {3{1'b1}});
  logic inf; assign inf = 1'b0;
  logic sub_; assign sub_ = (e == 0);
  logic den; assign den = sub_ && (mant != 0);
  logic [3:0] sig0; assign sig0 = sub_ ? {{(4-3){1'b0}}, mant} : {{(4-3-1){1'b0}}, 1'b1, mant};
  logic [3:0] sig1; assign sig1 = (sub_ && daz) ? 4'd0 : sig0;
  logic signed [11:0] ex0; assign ex0 = sub_ ? -12'sd9 : $signed({{(12-4){1'b0}}, e}) - 12'sd10;
  logic [2:0] lz;
  // the subnormal's leading-zero count
  fam_count_lzd_pair_cell_binary_count_vflat_w4 u1 (.a(sig1), .n(lz));
  logic [1:0] lzs; assign lzs = (sig1 == 0) ? 2'd0 : lz[1:0];
  logic [3:0] sign;
  // the subnormal normalized
  fam_shift_barrel_mux_tree #(.W(4), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u2 (.a(sig1), .amt(lzs), .op(3'd0), .y(sign), .sticky());
  logic signed [11:0] exn; assign exn = ex0 - $signed({{(12-3){1'b0}}, lz});
  logic [18:0] v_nan; assign v_nan = {2'd1, 1'b0, 12'sd0, 4'd0};
  logic [18:0] v_inf; assign v_inf = {2'd2, s, 12'sd0, 4'd0};
  logic [18:0] v_fin; assign v_fin = {2'd0, s, exn, sign};
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
module fam_mul_behavioral_star_w4_u_pfc463c41 (input logic [3:0] a, input logic [3:0] b, output logic [7:0] p);
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
