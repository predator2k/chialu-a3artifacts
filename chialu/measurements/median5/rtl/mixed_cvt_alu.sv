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

  // X -> int8_twos_complement (width 8, 0 fraction bits): rounded and saturated
  function automatic [10+8-1:0] m0_pack_int8_twos_complement(input [42:0] x0, input [2:0] rnd, input [7:0] word, input ftz);
    logic [42:0] x; logic [1:0] sp; logic s, st, inexact, up, neg, big; logic signed [12:0] e, pe; logic [25:0] sig;
    logic [26:0] keep, rest, halfv; logic [26+8:0] fint; integer sh, sht, i; logic [26+10:0] wide, t; logic [10-1:0] fl; logic [7:0] outb;
    x = m0_norm(x0); sp = x[42:42-1]; s = x[42-2]; sig = x[26:1]; st = x[0]; e = x[26+13:26+1];
    fl = 0; outb = 0; neg = 1'b0; t = 0; big = 1'b0; up = 1'b0; inexact = 1'b0;
    if (sp == 2'd1) begin fl[0] = 1'b1; t = (0 == 1) ? 37'd127 : (0 == 2) ? 37'd128 : 0; neg = (0 == 2) && 1'b1; end
    else if (sp == 2'd2) begin fl[0] = 1'b1; neg = s; t = s ? 37'd128 : 37'd127; end
    else if (sig == 0 && !st) t = 0;
    else begin
      if (sig == 0) begin sig = 1; e = e - 26; end
      pe = e + 0;                  // weight of sig's lsb in units of the target lsb
      if (pe >= 0) begin
        if (pe > 10) big = 1'b1;
        else begin wide = {{(10+1){1'b0}}, sig} << pe; t = wide; end
        inexact = st;
        keep = 0; rest = 0; halfv = 0;
        up = m0_rup(rnd, s, st, {(26+1){1'b0}}, {(26+1){1'b0}}, st, t[0], 0, word);
        t = t + up;
      end else begin
        sh = -pe; sht = sh; if (sh > 26 + 1) sh = 26 + 1;
        keep = {1'b0, sig} >> sh; rest = {1'b0, sig} & ((sh > 26) ? {(26+1){1'b1}} : ({1'b0, {26{1'b1}}} >> (26 - sh)));
        halfv = ({{26{1'b0}}, 1'b1} << (sh - 1));
        inexact = (rest != 0) | st;
        fint = (sht - 8 > 26) ? 0 : (sht >= 8) ? (rest >> (sht - 8)) : (rest << (8 - sht));
        up = m0_rup(rnd, s, inexact, rest, halfv, st, keep[0], fint, word);
        t = keep + up;
      end
      neg = s && (t != 0 || big);
      if (inexact) fl[4] = 1'b1;
      if (big || (neg && t > 37'd128) || (!neg && t > 37'd127)) begin
        fl[2] = 1'b1; fl[4] = 1'b1; fl[0] = 1'b1;
        t = neg ? 37'd128 : 37'd127;
      end
      if (1'b0 && neg) begin t = 0; neg = 1'b0; end
    end
    outb = neg ? (~t[7:0] + 1'b1) : t[7:0];
    m0_pack_int8_twos_complement = {fl, outb};
  endfunction

  // X -> fxs1i7f8 (width 16, 8 fraction bits): rounded and saturated
  function automatic [10+16-1:0] m0_pack_fxs1i7f8(input [42:0] x0, input [2:0] rnd, input [7:0] word, input ftz);
    logic [42:0] x; logic [1:0] sp; logic s, st, inexact, up, neg, big; logic signed [12:0] e, pe; logic [25:0] sig;
    logic [26:0] keep, rest, halfv; logic [26+8:0] fint; integer sh, sht, i; logic [26+18:0] wide, t; logic [10-1:0] fl; logic [15:0] outb;
    x = m0_norm(x0); sp = x[42:42-1]; s = x[42-2]; sig = x[26:1]; st = x[0]; e = x[26+13:26+1];
    fl = 0; outb = 0; neg = 1'b0; t = 0; big = 1'b0; up = 1'b0; inexact = 1'b0;
    if (sp == 2'd1) begin fl[0] = 1'b1; t = (0 == 1) ? 45'd32767 : (0 == 2) ? 45'd32768 : 0; neg = (0 == 2) && 1'b1; end
    else if (sp == 2'd2) begin fl[0] = 1'b1; neg = s; t = s ? 45'd32768 : 45'd32767; end
    else if (sig == 0 && !st) t = 0;
    else begin
      if (sig == 0) begin sig = 1; e = e - 26; end
      pe = e + 8;                  // weight of sig's lsb in units of the target lsb
      if (pe >= 0) begin
        if (pe > 18) big = 1'b1;
        else begin wide = {{(18+1){1'b0}}, sig} << pe; t = wide; end
        inexact = st;
        keep = 0; rest = 0; halfv = 0;
        up = m0_rup(rnd, s, st, {(26+1){1'b0}}, {(26+1){1'b0}}, st, t[0], 0, word);
        t = t + up;
      end else begin
        sh = -pe; sht = sh; if (sh > 26 + 1) sh = 26 + 1;
        keep = {1'b0, sig} >> sh; rest = {1'b0, sig} & ((sh > 26) ? {(26+1){1'b1}} : ({1'b0, {26{1'b1}}} >> (26 - sh)));
        halfv = ({{26{1'b0}}, 1'b1} << (sh - 1));
        inexact = (rest != 0) | st;
        fint = (sht - 8 > 26) ? 0 : (sht >= 8) ? (rest >> (sht - 8)) : (rest << (8 - sht));
        up = m0_rup(rnd, s, inexact, rest, halfv, st, keep[0], fint, word);
        t = keep + up;
      end
      neg = s && (t != 0 || big);
      if (inexact) fl[4] = 1'b1;
      if (big || (neg && t > 45'd32768) || (!neg && t > 45'd32767)) begin
        fl[2] = 1'b1; fl[4] = 1'b1; fl[0] = 1'b1;
        t = neg ? 45'd32768 : 45'd32767;
      end
      if (1'b0 && neg) begin t = 0; neg = 1'b0; end
    end
    outb = neg ? (~t[15:0] + 1'b1) : t[15:0];
    m0_pack_fxs1i7f8 = {fl, outb};
  endfunction
endpackage

// alu_core_m1_pkg: the exact-arithmetic functions of mode 1 (1xint16_twos_complement)
package alu_core_m1_pkg;

  // ---- m1: V = {special[1:0], sign, exp[13] (signed), sig[17]}
  //           X = {special[1:0], sign, exp[13] (signed), sig[38], sticky}
  localparam int m1_SW = 17, m1_EW = 13, m1_XW = 38;
  localparam int m1_VW = 33, m1_XT = 55;
  function automatic [32:0] m1_mkv(input [1:0] sp, input s, input signed [12:0] e, input [16:0] sig);
    m1_mkv = {sp, s, e, sig};
  endfunction
  function automatic [54:0] m1_mkx(input [1:0] sp, input s, input signed [12:0] e, input [37:0] sig, input st);
    m1_mkx = {sp, s, e, sig, st};
  endfunction
  function automatic [54:0] m1_x(input [32:0] v);   // widen V to X
    m1_x = {v[32:32-1], v[32-2], v[32-3 -: 13], {{(38-17){1'b0}}, v[16:0]}, 1'b0};
  endfunction
  // normalize: leading one at bit XW-1 (zero stays zero)
  function automatic [54:0] m1_norm(input [54:0] x);
    logic [37:0] s; logic signed [12:0] e; integer k;
    s = x[38:1]; e = x[38+13:38+1];
    if (s != 0) begin
      for (k = 32; k >= 1; k = k / 2) begin
        if (k < 38) begin
          if (s[37 -: 1] == 1'b0 && (s >> (38 - k)) == 0) begin
            s = s << k; e = e - k;
          end
        end
      end
    end
    m1_norm = {x[54:54-1], x[54-2], e, s, x[0]};
  endfunction

  function automatic m1_rup(input [2:0] rnd, input s, input inexact, input [38:0] rest, input [38:0] halfv,
                             input st, input lsb, input [38+8:0] fint, input [7:0] word);
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
  function automatic [54:0] m1_add(input [54:0] a, input [54:0] b, input sub);
    logic [54:0] na, nb, big, sml; logic [1:0] spa, spb; logic sa, sb, sr, sw;
    logic signed [12:0] ea, eb, d; logic [38:0] ms, mb, r; logic st, stb; integer sh;
    na = m1_norm(a); nb = m1_norm(b);
    spa = na[54:54-1]; spb = nb[54:54-1];
    sa = na[54-2]; sb = nb[54-2] ^ sub;
    if (spa == 2'd1 || spb == 2'd1) m1_add = m1_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 && spb == 2'd2) m1_add = (sa == sb) ? m1_mkx(2'd2, sa, 0, 0, 1'b0) : m1_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m1_add = m1_mkx(2'd2, sa, 0, 0, 1'b0);
    else if (spb == 2'd2) m1_add = m1_mkx(2'd2, sb, 0, 0, 1'b0);
    else if (na[38:1] == 0 && !na[0]) m1_add = {nb[54:54-1], sb, nb[54-3:0]};
    else if (nb[38:1] == 0 && !nb[0]) m1_add = na;
    else begin
      ea = na[38+13:38+1]; eb = nb[38+13:38+1];
      // order by magnitude (both normalized): larger exponent, then sig
      if (ea > eb || (ea == eb && na[38:1] >= nb[38:1])) begin big = na; sml = nb; sw = 1'b0; end
      else begin big = nb; sml = na; sw = 1'b1; end
      d = big[38+13:38+1] - sml[38+13:38+1];
      ms = {1'b0, sml[38:1]}; stb = sml[0];
      if (d > 38 + 1) begin stb = stb | (ms != 0); ms = 0; end
      else begin
        for (sh = 0; sh < 38 + 2; sh = sh + 1) begin
          if (sh < d) begin stb = stb | ms[0]; ms = ms >> 1; end
        end
      end
      mb = {1'b0, big[38:1]}; st = big[0] | stb;
      if ((sw ? sb : sa) == (sw ? sa : sb)) begin
        r = mb + ms;
        sr = sw ? sb : sa;
      end else begin
        // subtract: the sticky of the smaller operand borrows one lsb
        r = mb - ms - (stb ? 1'b1 : 1'b0);
        sr = sw ? sb : sa;
        if (r == 0 && !st) sr = 1'b0;
      end
      if (r[38]) begin st = st | r[0]; r = r >> 1; m1_add = m1_mkx(2'd0, sr, big[38+13:38+1] + 1, r[37:0], st); end
      else m1_add = m1_mkx(2'd0, sr, big[38+13:38+1], r[37:0], st);
    end
  endfunction
  function automatic [54:0] m1_mul(input [54:0] a, input [54:0] b);
    logic [54:0] na, nb; logic [1:0] spa, spb; logic s; logic [2*38-1:0] pr; logic st; integer k;
    na = m1_norm(a); nb = m1_norm(b);
    spa = na[54:54-1]; spb = nb[54:54-1]; s = na[54-2] ^ nb[54-2];
    if (spa == 2'd1 || spb == 2'd1) m1_mul = m1_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 || spb == 2'd2) begin
      if ((spa == 2'd0 && na[38:1] == 0 && !na[0]) || (spb == 2'd0 && nb[38:1] == 0 && !nb[0]))
        m1_mul = m1_mkx(2'd1, 1'b0, 0, 0, 1'b0);
      else m1_mul = m1_mkx(2'd2, s, 0, 0, 1'b0);
    end else begin
      pr = na[38:1] * nb[38:1];
      st = na[0] | nb[0];
      // keep the top XW bits of the product, the rest folds into sticky
      st = st | (pr[37:0] != 0);
      m1_mul = m1_mkx(2'd0, s, na[38+13:38+1] + nb[38+13:38+1] + 38, pr[2*38-1:38], st);
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
  function automatic [2*38+1:0] m1_udiv(input [37:0] a, input [37:0] dv);
    logic [38+1:0] r; logic [38:0] q; logic ge; integer i;
    r = {2'b0, a}; q = 0;
    for (i = 38; i >= 0; i = i - 1) begin
      ge = (r >= {2'b0, dv});
      r = ge ? r - {2'b0, dv} : r;
      q = {q[37:0], ge};
      if (i > 0) r = {r[38:0], 1'b0};
    end
    m1_udiv = {q, r[38:0]};
  endfunction
  // the exact product: {special[1:0], sign, exp[EW], sig[2XW]} (no sticky)
  function automatic [2*38+13+2:0] m1_mulx(input [54:0] a, input [54:0] b);
    logic [54:0] na, nb; logic [1:0] spa, spb, sp; logic s; logic [2*38-1:0] pr;
    na = m1_norm(a); nb = m1_norm(b);
    pr = na[38:1] * nb[38:1];
    spa = na[54:54-1]; spb = nb[54:54-1]; s = na[54-2] ^ nb[54-2];
    if (spa == 2'd1 || spb == 2'd1) sp = 2'd1;
    else if (spa == 2'd2 || spb == 2'd2)
      sp = ((spa == 2'd0 && na[38:1] == 0) || (spb == 2'd0 && nb[38:1] == 0)) ? 2'd1 : 2'd2;
    else sp = 2'd0;
    m1_mulx = {sp, s, na[38+13:38+1] + nb[38+13:38+1], pr};
  endfunction
  function automatic [54:0] m1_div(input [54:0] a, input [54:0] b);
    logic [54:0] na, nb; logic [1:0] spa, spb; logic s; logic [2*38+1:0] qr; logic [38:0] q, r;
    na = m1_norm(a); nb = m1_norm(b);
    spa = na[54:54-1]; spb = nb[54:54-1]; s = na[54-2] ^ nb[54-2];
    if (spa == 2'd1 || spb == 2'd1) m1_div = m1_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 && spb == 2'd2) m1_div = m1_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m1_div = m1_mkx(2'd2, s, 0, 0, 1'b0);
    else if (spb == 2'd2) m1_div = m1_mkx(2'd0, s, 0, 0, 1'b0);
    else if (nb[38:1] == 0 && !nb[0]) begin
      if (na[38:1] == 0 && !na[0]) m1_div = m1_mkx(2'd1, 1'b0, 0, 0, 1'b0);
      else m1_div = m1_mkx(2'd2, s, 0, 0, 1'b0);
    end else if (na[38:1] == 0 && !na[0]) m1_div = m1_mkx(2'd0, s, 0, 0, 1'b0);
    else begin
      qr = m1_udiv(na[38:1], nb[38:1]);     // both normalized: nonzero finite
      q = qr[2*38+1:38+1]; r = qr[38:0];
      // q < 2^(XW+1): drop one bit when it carries
      if (q[38]) m1_div = m1_mkx(2'd0, s, na[38+13:38+1] - nb[38+13:38+1] - 38 + 1, q[38:1], (r != 0) | q[0] | na[0] | nb[0]);
      else m1_div = m1_mkx(2'd0, s, na[38+13:38+1] - nb[38+13:38+1] - 38, q[37:0], (r != 0) | na[0] | nb[0]);
    end
  endfunction
  function automatic [54:0] m1_sqrt(input [54:0] a);
    logic [54:0] na; logic [1:0] spa; logic signed [12:0] e; logic [38:0] m; logic [2*38+3:0] rad;
    logic [38+2:0] rem, trial; logic [38:0] root; logic ge; integer i;
    na = m1_norm(a); spa = na[54:54-1];
    if (spa == 2'd1) m1_sqrt = m1_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m1_sqrt = na[54-2] ? m1_mkx(2'd1, 1'b0, 0, 0, 1'b0) : na;
    else if (na[38:1] == 0 && !na[0]) m1_sqrt = na;
    else if (na[54-2]) m1_sqrt = m1_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else begin
      e = na[38+13:38+1];
      // value = m * 2^e with e even; radicand = m * 2^(2K): root = sqrt(m) * 2^K, XW+1 bits
      if (e[0]) begin m = {na[38:1], 1'b0}; e = e - 1; end
      else m = {1'b0, na[38:1]};
      rad = {{(38+3){1'b0}}, m} << 38;
      rem = 0; root = 0;
      for (i = 38; i >= 0; i = i - 1) begin
        rem = {rem[38:0], rad[2*i +: 2]};
        trial = {root, 2'b01};
        ge = (rem >= trial);                  // unconditional assignments, as in udiv
        rem = ge ? rem - trial : rem;
        root = {root[37:0], ge};
      end
      m1_sqrt = m1_mkx(2'd0, 1'b0, (e >>> 1) - 19 + 1, root[38:1], (rem != 0) | root[0] | na[0]);
    end
  endfunction
  // X ordering treats NaN as unordered and compares finite values by sign and magnitude
  function automatic m1_lt(input [54:0] a, input [54:0] b);
    logic [54:0] na, nb; logic za, zb, sa, sb, mag_lt; logic signed [12:0] ea, eb;
    na = m1_norm(a); nb = m1_norm(b);
    za = (na[38:1] == 0) && !na[0]; zb = (nb[38:1] == 0) && !nb[0];
    sa = na[54-2] && !za; sb = nb[54-2] && !zb;
    if (na[54:54-1] == 2'd1 || nb[54:54-1] == 2'd1) m1_lt = 1'b0;
    else if (na[54:54-1] == 2'd2 || nb[54:54-1] == 2'd2) begin
      if (na[54:54-1] == 2'd2 && nb[54:54-1] == 2'd2) m1_lt = na[54-2] && !nb[54-2];
      else if (na[54:54-1] == 2'd2) m1_lt = na[54-2];
      else m1_lt = !nb[54-2];
    end else if (za && zb) m1_lt = 1'b0;
    else if (sa != sb) m1_lt = sa;
    else begin
      ea = na[38+13:38+1]; eb = nb[38+13:38+1];
      if (za) mag_lt = 1'b1; else if (zb) mag_lt = 1'b0;
      else mag_lt = (ea < eb) || (ea == eb && (na[38:1] < nb[38:1] || (na[38:1] == nb[38:1] && !na[0] && nb[0])));
      m1_lt = sa ? !mag_lt && !(za && zb) && !m1_eq(na, nb) : mag_lt;
    end
  endfunction
  function automatic m1_eq(input [54:0] a, input [54:0] b);
    logic [54:0] na, nb; logic za, zb;
    na = m1_norm(a); nb = m1_norm(b);
    za = (na[38:1] == 0) && !na[0]; zb = (nb[38:1] == 0) && !nb[0];
    if (na[54:54-1] == 2'd1 || nb[54:54-1] == 2'd1) m1_eq = 1'b0;
    else if (na[54:54-1] == 2'd2 || nb[54:54-1] == 2'd2)
      m1_eq = (na[54:54-1] == nb[54:54-1]) && (na[54-2] == nb[54-2]);
    else if (za || zb) m1_eq = za && zb;
    else m1_eq = (na[54-2] == nb[54-2]) && (na[38+13:38+1] == nb[38+13:38+1]) && (na[38:1] == nb[38:1]) && (na[0] == nb[0]);
  endfunction

  function automatic [33:0] m1_unpack_s(input [15:0] b, input daz);
    logic s; logic [15:0] mag; integer i;
    s = b[15]; mag = s ? (~b + 1'b1) : b;
    m1_unpack_s = {1'b0, m1_mkv(2'd0, s && (mag != 0), -0, {{(17-16){1'b0}}, mag})};
  endfunction

  // X -> int8_twos_complement (width 8, 0 fraction bits): rounded and saturated
  function automatic [10+8-1:0] m1_pack_int8_twos_complement(input [54:0] x0, input [2:0] rnd, input [7:0] word, input ftz);
    logic [54:0] x; logic [1:0] sp; logic s, st, inexact, up, neg, big; logic signed [12:0] e, pe; logic [37:0] sig;
    logic [38:0] keep, rest, halfv; logic [38+8:0] fint; integer sh, sht, i; logic [38+10:0] wide, t; logic [10-1:0] fl; logic [7:0] outb;
    x = m1_norm(x0); sp = x[54:54-1]; s = x[54-2]; sig = x[38:1]; st = x[0]; e = x[38+13:38+1];
    fl = 0; outb = 0; neg = 1'b0; t = 0; big = 1'b0; up = 1'b0; inexact = 1'b0;
    if (sp == 2'd1) begin fl[0] = 1'b1; t = (0 == 1) ? 49'd127 : (0 == 2) ? 49'd128 : 0; neg = (0 == 2) && 1'b1; end
    else if (sp == 2'd2) begin fl[0] = 1'b1; neg = s; t = s ? 49'd128 : 49'd127; end
    else if (sig == 0 && !st) t = 0;
    else begin
      if (sig == 0) begin sig = 1; e = e - 38; end
      pe = e + 0;                  // weight of sig's lsb in units of the target lsb
      if (pe >= 0) begin
        if (pe > 10) big = 1'b1;
        else begin wide = {{(10+1){1'b0}}, sig} << pe; t = wide; end
        inexact = st;
        keep = 0; rest = 0; halfv = 0;
        up = m1_rup(rnd, s, st, {(38+1){1'b0}}, {(38+1){1'b0}}, st, t[0], 0, word);
        t = t + up;
      end else begin
        sh = -pe; sht = sh; if (sh > 38 + 1) sh = 38 + 1;
        keep = {1'b0, sig} >> sh; rest = {1'b0, sig} & ((sh > 38) ? {(38+1){1'b1}} : ({1'b0, {38{1'b1}}} >> (38 - sh)));
        halfv = ({{38{1'b0}}, 1'b1} << (sh - 1));
        inexact = (rest != 0) | st;
        fint = (sht - 8 > 38) ? 0 : (sht >= 8) ? (rest >> (sht - 8)) : (rest << (8 - sht));
        up = m1_rup(rnd, s, inexact, rest, halfv, st, keep[0], fint, word);
        t = keep + up;
      end
      neg = s && (t != 0 || big);
      if (inexact) fl[4] = 1'b1;
      if (big || (neg && t > 49'd128) || (!neg && t > 49'd127)) begin
        fl[2] = 1'b1; fl[4] = 1'b1; fl[0] = 1'b1;
        t = neg ? 49'd128 : 49'd127;
      end
      if (1'b0 && neg) begin t = 0; neg = 1'b0; end
    end
    outb = neg ? (~t[7:0] + 1'b1) : t[7:0];
    m1_pack_int8_twos_complement = {fl, outb};
  endfunction

  // X -> fp16 (fp16): sign(1) exp 5 man 10, top field 30, max finite 15'd31743
  function automatic [10+16-1:0] m1_pack_fp16(input [54:0] x0, input [2:0] rnd, input [7:0] word, input ftz);
    logic [54:0] x; logic [1:0] sp; logic s; logic signed [12:0] e, eu, biased; logic [37:0] sig;
    logic st, inexact, up, upn, half_eq, gt_half, tiny, ovf, unf, carry_n, to_inf; integer sh, shn, sht;
    logic [38:0] keep, rest, keepn, restn, halfv, halfn; logic [38+8:0] fint, fintn; logic [10-1:0] fl;
    logic [16+13:0] code; logic [16:0] mag; logic [16-1:0] outb;
    x = m1_norm(x0); sp = x[54:54-1]; s = x[54-2] & 1; sig = x[38:1]; st = x[0]; e = x[38+13:38+1];
    fl = 0; outb = 0;
    if (sp == 2'd1) begin fl[5] = 1'b1; outb = 16'd32256; end
    else if (sp == 2'd2) begin
      outb = {s, 15'd31744}; if (!1) begin fl[4] = 1'b1; fl[2] = 1'b1; end
    end else if (sig == 0 && !st) begin outb = 1 ? 0 : {s, {15{1'b0}}}; end
    else begin
      if (sig == 0) begin sig = 1 << 37; e = e - (2*38-1); end // normalize the lone sticky's tiny value
      eu = e + 37;                 // exponent of the leading one
      biased = eu + 15;
      shn = 38 - 1 - 10;           // bits dropped at the normal precision
      sh = (biased >= 1) ? shn : shn + (1 - biased);
      sht = sh;
      if (sh > 38 + 1) sh = 38 + 1;
      keep = {1'b0, sig} >> sh; rest = {1'b0, sig} & ((sh > 38) ? {(38+1){1'b1}} : ({1'b0, {38{1'b1}}} >> (38 - sh)));
      halfv = (sh == 0) ? 0 : ({{38{1'b0}}, 1'b1} << (sh - 1));
      keepn = {1'b0, sig} >> shn; restn = {1'b0, sig} & ({1'b0, {38{1'b1}}} >> (38 - shn));
      halfn = (shn == 0) ? 0 : ({{38{1'b0}}, 1'b1} << (shn - 1));
      inexact = (rest != 0) | st;
      fint = (sht - 8 > 38) ? 0 : (sht >= 8) ? (rest >> (sht - 8)) : (rest << (8 - sht));
      fintn = (shn >= 8) ? (restn >> (shn - 8)) : (restn << (8 - shn));
      up = m1_rup(rnd, s, inexact, rest, halfv, st, keep[0], fint, word);
      upn = m1_rup(rnd, s, (restn != 0) | st, restn, halfn, st, keepn[0], fintn, word);
      carry_n = ((keepn + upn) == ({{38{1'b0}}, 1'b1} << (10 + 1)));
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
    m1_pack_fp16 = {fl, outb};
  endfunction

  // X -> fxs1i7f8 (width 16, 8 fraction bits): rounded and saturated
  function automatic [10+16-1:0] m1_pack_fxs1i7f8(input [54:0] x0, input [2:0] rnd, input [7:0] word, input ftz);
    logic [54:0] x; logic [1:0] sp; logic s, st, inexact, up, neg, big; logic signed [12:0] e, pe; logic [37:0] sig;
    logic [38:0] keep, rest, halfv; logic [38+8:0] fint; integer sh, sht, i; logic [38+18:0] wide, t; logic [10-1:0] fl; logic [15:0] outb;
    x = m1_norm(x0); sp = x[54:54-1]; s = x[54-2]; sig = x[38:1]; st = x[0]; e = x[38+13:38+1];
    fl = 0; outb = 0; neg = 1'b0; t = 0; big = 1'b0; up = 1'b0; inexact = 1'b0;
    if (sp == 2'd1) begin fl[0] = 1'b1; t = (0 == 1) ? 57'd32767 : (0 == 2) ? 57'd32768 : 0; neg = (0 == 2) && 1'b1; end
    else if (sp == 2'd2) begin fl[0] = 1'b1; neg = s; t = s ? 57'd32768 : 57'd32767; end
    else if (sig == 0 && !st) t = 0;
    else begin
      if (sig == 0) begin sig = 1; e = e - 38; end
      pe = e + 8;                  // weight of sig's lsb in units of the target lsb
      if (pe >= 0) begin
        if (pe > 18) big = 1'b1;
        else begin wide = {{(18+1){1'b0}}, sig} << pe; t = wide; end
        inexact = st;
        keep = 0; rest = 0; halfv = 0;
        up = m1_rup(rnd, s, st, {(38+1){1'b0}}, {(38+1){1'b0}}, st, t[0], 0, word);
        t = t + up;
      end else begin
        sh = -pe; sht = sh; if (sh > 38 + 1) sh = 38 + 1;
        keep = {1'b0, sig} >> sh; rest = {1'b0, sig} & ((sh > 38) ? {(38+1){1'b1}} : ({1'b0, {38{1'b1}}} >> (38 - sh)));
        halfv = ({{38{1'b0}}, 1'b1} << (sh - 1));
        inexact = (rest != 0) | st;
        fint = (sht - 8 > 38) ? 0 : (sht >= 8) ? (rest >> (sht - 8)) : (rest << (8 - sht));
        up = m1_rup(rnd, s, inexact, rest, halfv, st, keep[0], fint, word);
        t = keep + up;
      end
      neg = s && (t != 0 || big);
      if (inexact) fl[4] = 1'b1;
      if (big || (neg && t > 57'd32768) || (!neg && t > 57'd32767)) begin
        fl[2] = 1'b1; fl[4] = 1'b1; fl[0] = 1'b1;
        t = neg ? 57'd32768 : 57'd32767;
      end
      if (1'b0 && neg) begin t = 0; neg = 1'b0; end
    end
    outb = neg ? (~t[15:0] + 1'b1) : t[15:0];
    m1_pack_fxs1i7f8 = {fl, outb};
  endfunction

  function automatic [15:0] m1_enc(input signed [34:0] v); m1_enc = v[15:0]; endfunction
  function automatic [15:0] m1_wrap(input signed [34:0] v); m1_wrap = v[15:0]; endfunction
  function automatic [15:0] m1_sat(input signed [34:0] v);
    m1_sat = (v > 35'sd32767) ? {1'b0, {15{1'b1}}} : (v < -35'sd32768) ? {1'b1, {15{1'b0}}} : v[15:0];
  endfunction

  // round v / 2^f under rnd (the SR word applies to the fraction bits)
  function automatic signed [34:0] m1_rshift(input signed [34:0] v, input integer f, input [2:0] rnd, input [7:0] word);
    logic s; logic [34:0] mag, keep, rest, halfv; logic [43:0] fint; logic up, inexact;
    s = v < 0; mag = s ? -v : v;
    if (f <= 0) m1_rshift = v;
    else begin
      keep = mag >> f; rest = mag & (((35'd1) << f) - 1); halfv = (35'd1) << (f - 1);
      inexact = rest != 0;
      fint = (f >= 8) ? (rest >> (f - 8)) : (rest << (8 - f));
      case (rnd)
        3'd0: up = (rest > halfv) || (rest == halfv && keep[0]);
        3'd1: up = 1'b0;
        3'd2: up = inexact && s;
        3'd3: up = inexact && !s;
        3'd4: up = inexact && (0 ? (fint >= word) : (fint > word));
        default: up = inexact;
      endcase
      keep = keep + up;
      m1_rshift = s ? -$signed(keep) : $signed(keep);
    end
  endfunction
  // the SR word of a division: floor(|r| * 2^sb / |b|)
  function automatic [7:0] m1_divfrac(input [34:0] r, input [34:0] b);
    logic [43:0] t;
    t = ({{9{1'b0}}, r} << 8) / {{9{1'b0}}, b};
    m1_divfrac = t[7:0];
  endfunction
endpackage

// alu_core_m2_pkg: the exact-arithmetic functions of mode 2 (2xint8_twos_complement)
package alu_core_m2_pkg;

  // ---- m2: V = {special[1:0], sign, exp[13] (signed), sig[9]}
  //           X = {special[1:0], sign, exp[13] (signed), sig[22], sticky}
  localparam int m2_SW = 9, m2_EW = 13, m2_XW = 22;
  localparam int m2_VW = 25, m2_XT = 39;
  function automatic [24:0] m2_mkv(input [1:0] sp, input s, input signed [12:0] e, input [8:0] sig);
    m2_mkv = {sp, s, e, sig};
  endfunction
  function automatic [38:0] m2_mkx(input [1:0] sp, input s, input signed [12:0] e, input [21:0] sig, input st);
    m2_mkx = {sp, s, e, sig, st};
  endfunction
  function automatic [38:0] m2_x(input [24:0] v);   // widen V to X
    m2_x = {v[24:24-1], v[24-2], v[24-3 -: 13], {{(22-9){1'b0}}, v[8:0]}, 1'b0};
  endfunction
  // normalize: leading one at bit XW-1 (zero stays zero)
  function automatic [38:0] m2_norm(input [38:0] x);
    logic [21:0] s; logic signed [12:0] e; integer k;
    s = x[22:1]; e = x[22+13:22+1];
    if (s != 0) begin
      for (k = 16; k >= 1; k = k / 2) begin
        if (k < 22) begin
          if (s[21 -: 1] == 1'b0 && (s >> (22 - k)) == 0) begin
            s = s << k; e = e - k;
          end
        end
      end
    end
    m2_norm = {x[38:38-1], x[38-2], e, s, x[0]};
  endfunction

  function automatic m2_rup(input [2:0] rnd, input s, input inexact, input [22:0] rest, input [22:0] halfv,
                             input st, input lsb, input [22+8:0] fint, input [7:0] word);
    logic gt_half, half_eq;
    gt_half = rest > halfv; half_eq = (rest == halfv) && (halfv != 0);
    case (rnd)
      3'd0: m2_rup = gt_half || (half_eq && (st || lsb));
      3'd1: m2_rup = 1'b0;
      3'd2: m2_rup = inexact && s;
      3'd3: m2_rup = inexact && !s;
      3'd4: m2_rup = inexact && (0 ? (fint >= word) : (fint > word));
      default: m2_rup = inexact;   // 5: away from zero
    endcase
  endfunction

  // a +/- b on X (normalized inputs); specials: nan wins, inf-inf = nan
  function automatic [38:0] m2_add(input [38:0] a, input [38:0] b, input sub);
    logic [38:0] na, nb, big, sml; logic [1:0] spa, spb; logic sa, sb, sr, sw;
    logic signed [12:0] ea, eb, d; logic [22:0] ms, mb, r; logic st, stb; integer sh;
    na = m2_norm(a); nb = m2_norm(b);
    spa = na[38:38-1]; spb = nb[38:38-1];
    sa = na[38-2]; sb = nb[38-2] ^ sub;
    if (spa == 2'd1 || spb == 2'd1) m2_add = m2_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 && spb == 2'd2) m2_add = (sa == sb) ? m2_mkx(2'd2, sa, 0, 0, 1'b0) : m2_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m2_add = m2_mkx(2'd2, sa, 0, 0, 1'b0);
    else if (spb == 2'd2) m2_add = m2_mkx(2'd2, sb, 0, 0, 1'b0);
    else if (na[22:1] == 0 && !na[0]) m2_add = {nb[38:38-1], sb, nb[38-3:0]};
    else if (nb[22:1] == 0 && !nb[0]) m2_add = na;
    else begin
      ea = na[22+13:22+1]; eb = nb[22+13:22+1];
      // order by magnitude (both normalized): larger exponent, then sig
      if (ea > eb || (ea == eb && na[22:1] >= nb[22:1])) begin big = na; sml = nb; sw = 1'b0; end
      else begin big = nb; sml = na; sw = 1'b1; end
      d = big[22+13:22+1] - sml[22+13:22+1];
      ms = {1'b0, sml[22:1]}; stb = sml[0];
      if (d > 22 + 1) begin stb = stb | (ms != 0); ms = 0; end
      else begin
        for (sh = 0; sh < 22 + 2; sh = sh + 1) begin
          if (sh < d) begin stb = stb | ms[0]; ms = ms >> 1; end
        end
      end
      mb = {1'b0, big[22:1]}; st = big[0] | stb;
      if ((sw ? sb : sa) == (sw ? sa : sb)) begin
        r = mb + ms;
        sr = sw ? sb : sa;
      end else begin
        // subtract: the sticky of the smaller operand borrows one lsb
        r = mb - ms - (stb ? 1'b1 : 1'b0);
        sr = sw ? sb : sa;
        if (r == 0 && !st) sr = 1'b0;
      end
      if (r[22]) begin st = st | r[0]; r = r >> 1; m2_add = m2_mkx(2'd0, sr, big[22+13:22+1] + 1, r[21:0], st); end
      else m2_add = m2_mkx(2'd0, sr, big[22+13:22+1], r[21:0], st);
    end
  endfunction
  function automatic [38:0] m2_mul(input [38:0] a, input [38:0] b);
    logic [38:0] na, nb; logic [1:0] spa, spb; logic s; logic [2*22-1:0] pr; logic st; integer k;
    na = m2_norm(a); nb = m2_norm(b);
    spa = na[38:38-1]; spb = nb[38:38-1]; s = na[38-2] ^ nb[38-2];
    if (spa == 2'd1 || spb == 2'd1) m2_mul = m2_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 || spb == 2'd2) begin
      if ((spa == 2'd0 && na[22:1] == 0 && !na[0]) || (spb == 2'd0 && nb[22:1] == 0 && !nb[0]))
        m2_mul = m2_mkx(2'd1, 1'b0, 0, 0, 1'b0);
      else m2_mul = m2_mkx(2'd2, s, 0, 0, 1'b0);
    end else begin
      pr = na[22:1] * nb[22:1];
      st = na[0] | nb[0];
      // keep the top XW bits of the product, the rest folds into sticky
      st = st | (pr[21:0] != 0);
      m2_mul = m2_mkx(2'd0, s, na[22+13:22+1] + nb[22+13:22+1] + 22, pr[2*22-1:22], st);
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
  function automatic [2*22+1:0] m2_udiv(input [21:0] a, input [21:0] dv);
    logic [22+1:0] r; logic [22:0] q; logic ge; integer i;
    r = {2'b0, a}; q = 0;
    for (i = 22; i >= 0; i = i - 1) begin
      ge = (r >= {2'b0, dv});
      r = ge ? r - {2'b0, dv} : r;
      q = {q[21:0], ge};
      if (i > 0) r = {r[22:0], 1'b0};
    end
    m2_udiv = {q, r[22:0]};
  endfunction
  // the exact product: {special[1:0], sign, exp[EW], sig[2XW]} (no sticky)
  function automatic [2*22+13+2:0] m2_mulx(input [38:0] a, input [38:0] b);
    logic [38:0] na, nb; logic [1:0] spa, spb, sp; logic s; logic [2*22-1:0] pr;
    na = m2_norm(a); nb = m2_norm(b);
    pr = na[22:1] * nb[22:1];
    spa = na[38:38-1]; spb = nb[38:38-1]; s = na[38-2] ^ nb[38-2];
    if (spa == 2'd1 || spb == 2'd1) sp = 2'd1;
    else if (spa == 2'd2 || spb == 2'd2)
      sp = ((spa == 2'd0 && na[22:1] == 0) || (spb == 2'd0 && nb[22:1] == 0)) ? 2'd1 : 2'd2;
    else sp = 2'd0;
    m2_mulx = {sp, s, na[22+13:22+1] + nb[22+13:22+1], pr};
  endfunction
  function automatic [38:0] m2_div(input [38:0] a, input [38:0] b);
    logic [38:0] na, nb; logic [1:0] spa, spb; logic s; logic [2*22+1:0] qr; logic [22:0] q, r;
    na = m2_norm(a); nb = m2_norm(b);
    spa = na[38:38-1]; spb = nb[38:38-1]; s = na[38-2] ^ nb[38-2];
    if (spa == 2'd1 || spb == 2'd1) m2_div = m2_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 && spb == 2'd2) m2_div = m2_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m2_div = m2_mkx(2'd2, s, 0, 0, 1'b0);
    else if (spb == 2'd2) m2_div = m2_mkx(2'd0, s, 0, 0, 1'b0);
    else if (nb[22:1] == 0 && !nb[0]) begin
      if (na[22:1] == 0 && !na[0]) m2_div = m2_mkx(2'd1, 1'b0, 0, 0, 1'b0);
      else m2_div = m2_mkx(2'd2, s, 0, 0, 1'b0);
    end else if (na[22:1] == 0 && !na[0]) m2_div = m2_mkx(2'd0, s, 0, 0, 1'b0);
    else begin
      qr = m2_udiv(na[22:1], nb[22:1]);     // both normalized: nonzero finite
      q = qr[2*22+1:22+1]; r = qr[22:0];
      // q < 2^(XW+1): drop one bit when it carries
      if (q[22]) m2_div = m2_mkx(2'd0, s, na[22+13:22+1] - nb[22+13:22+1] - 22 + 1, q[22:1], (r != 0) | q[0] | na[0] | nb[0]);
      else m2_div = m2_mkx(2'd0, s, na[22+13:22+1] - nb[22+13:22+1] - 22, q[21:0], (r != 0) | na[0] | nb[0]);
    end
  endfunction
  function automatic [38:0] m2_sqrt(input [38:0] a);
    logic [38:0] na; logic [1:0] spa; logic signed [12:0] e; logic [22:0] m; logic [2*22+3:0] rad;
    logic [22+2:0] rem, trial; logic [22:0] root; logic ge; integer i;
    na = m2_norm(a); spa = na[38:38-1];
    if (spa == 2'd1) m2_sqrt = m2_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m2_sqrt = na[38-2] ? m2_mkx(2'd1, 1'b0, 0, 0, 1'b0) : na;
    else if (na[22:1] == 0 && !na[0]) m2_sqrt = na;
    else if (na[38-2]) m2_sqrt = m2_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else begin
      e = na[22+13:22+1];
      // value = m * 2^e with e even; radicand = m * 2^(2K): root = sqrt(m) * 2^K, XW+1 bits
      if (e[0]) begin m = {na[22:1], 1'b0}; e = e - 1; end
      else m = {1'b0, na[22:1]};
      rad = {{(22+3){1'b0}}, m} << 22;
      rem = 0; root = 0;
      for (i = 22; i >= 0; i = i - 1) begin
        rem = {rem[22:0], rad[2*i +: 2]};
        trial = {root, 2'b01};
        ge = (rem >= trial);                  // unconditional assignments, as in udiv
        rem = ge ? rem - trial : rem;
        root = {root[21:0], ge};
      end
      m2_sqrt = m2_mkx(2'd0, 1'b0, (e >>> 1) - 11 + 1, root[22:1], (rem != 0) | root[0] | na[0]);
    end
  endfunction
  // X ordering treats NaN as unordered and compares finite values by sign and magnitude
  function automatic m2_lt(input [38:0] a, input [38:0] b);
    logic [38:0] na, nb; logic za, zb, sa, sb, mag_lt; logic signed [12:0] ea, eb;
    na = m2_norm(a); nb = m2_norm(b);
    za = (na[22:1] == 0) && !na[0]; zb = (nb[22:1] == 0) && !nb[0];
    sa = na[38-2] && !za; sb = nb[38-2] && !zb;
    if (na[38:38-1] == 2'd1 || nb[38:38-1] == 2'd1) m2_lt = 1'b0;
    else if (na[38:38-1] == 2'd2 || nb[38:38-1] == 2'd2) begin
      if (na[38:38-1] == 2'd2 && nb[38:38-1] == 2'd2) m2_lt = na[38-2] && !nb[38-2];
      else if (na[38:38-1] == 2'd2) m2_lt = na[38-2];
      else m2_lt = !nb[38-2];
    end else if (za && zb) m2_lt = 1'b0;
    else if (sa != sb) m2_lt = sa;
    else begin
      ea = na[22+13:22+1]; eb = nb[22+13:22+1];
      if (za) mag_lt = 1'b1; else if (zb) mag_lt = 1'b0;
      else mag_lt = (ea < eb) || (ea == eb && (na[22:1] < nb[22:1] || (na[22:1] == nb[22:1] && !na[0] && nb[0])));
      m2_lt = sa ? !mag_lt && !(za && zb) && !m2_eq(na, nb) : mag_lt;
    end
  endfunction
  function automatic m2_eq(input [38:0] a, input [38:0] b);
    logic [38:0] na, nb; logic za, zb;
    na = m2_norm(a); nb = m2_norm(b);
    za = (na[22:1] == 0) && !na[0]; zb = (nb[22:1] == 0) && !nb[0];
    if (na[38:38-1] == 2'd1 || nb[38:38-1] == 2'd1) m2_eq = 1'b0;
    else if (na[38:38-1] == 2'd2 || nb[38:38-1] == 2'd2)
      m2_eq = (na[38:38-1] == nb[38:38-1]) && (na[38-2] == nb[38-2]);
    else if (za || zb) m2_eq = za && zb;
    else m2_eq = (na[38-2] == nb[38-2]) && (na[22+13:22+1] == nb[22+13:22+1]) && (na[22:1] == nb[22:1]) && (na[0] == nb[0]);
  endfunction

  function automatic [25:0] m2_unpack_s(input [7:0] b, input daz);
    logic s; logic [7:0] mag; integer i;
    s = b[7]; mag = s ? (~b + 1'b1) : b;
    m2_unpack_s = {1'b0, m2_mkv(2'd0, s && (mag != 0), -0, {{(9-8){1'b0}}, mag})};
  endfunction

  // X -> int8_twos_complement (width 8, 0 fraction bits): rounded and saturated
  function automatic [10+8-1:0] m2_pack_int8_twos_complement(input [38:0] x0, input [2:0] rnd, input [7:0] word, input ftz);
    logic [38:0] x; logic [1:0] sp; logic s, st, inexact, up, neg, big; logic signed [12:0] e, pe; logic [21:0] sig;
    logic [22:0] keep, rest, halfv; logic [22+8:0] fint; integer sh, sht, i; logic [22+10:0] wide, t; logic [10-1:0] fl; logic [7:0] outb;
    x = m2_norm(x0); sp = x[38:38-1]; s = x[38-2]; sig = x[22:1]; st = x[0]; e = x[22+13:22+1];
    fl = 0; outb = 0; neg = 1'b0; t = 0; big = 1'b0; up = 1'b0; inexact = 1'b0;
    if (sp == 2'd1) begin fl[0] = 1'b1; t = (0 == 1) ? 33'd127 : (0 == 2) ? 33'd128 : 0; neg = (0 == 2) && 1'b1; end
    else if (sp == 2'd2) begin fl[0] = 1'b1; neg = s; t = s ? 33'd128 : 33'd127; end
    else if (sig == 0 && !st) t = 0;
    else begin
      if (sig == 0) begin sig = 1; e = e - 22; end
      pe = e + 0;                  // weight of sig's lsb in units of the target lsb
      if (pe >= 0) begin
        if (pe > 10) big = 1'b1;
        else begin wide = {{(10+1){1'b0}}, sig} << pe; t = wide; end
        inexact = st;
        keep = 0; rest = 0; halfv = 0;
        up = m2_rup(rnd, s, st, {(22+1){1'b0}}, {(22+1){1'b0}}, st, t[0], 0, word);
        t = t + up;
      end else begin
        sh = -pe; sht = sh; if (sh > 22 + 1) sh = 22 + 1;
        keep = {1'b0, sig} >> sh; rest = {1'b0, sig} & ((sh > 22) ? {(22+1){1'b1}} : ({1'b0, {22{1'b1}}} >> (22 - sh)));
        halfv = ({{22{1'b0}}, 1'b1} << (sh - 1));
        inexact = (rest != 0) | st;
        fint = (sht - 8 > 22) ? 0 : (sht >= 8) ? (rest >> (sht - 8)) : (rest << (8 - sht));
        up = m2_rup(rnd, s, inexact, rest, halfv, st, keep[0], fint, word);
        t = keep + up;
      end
      neg = s && (t != 0 || big);
      if (inexact) fl[4] = 1'b1;
      if (big || (neg && t > 33'd128) || (!neg && t > 33'd127)) begin
        fl[2] = 1'b1; fl[4] = 1'b1; fl[0] = 1'b1;
        t = neg ? 33'd128 : 33'd127;
      end
      if (1'b0 && neg) begin t = 0; neg = 1'b0; end
    end
    outb = neg ? (~t[7:0] + 1'b1) : t[7:0];
    m2_pack_int8_twos_complement = {fl, outb};
  endfunction

  // X -> fp16 (fp16): sign(1) exp 5 man 10, top field 30, max finite 15'd31743
  function automatic [10+16-1:0] m2_pack_fp16(input [38:0] x0, input [2:0] rnd, input [7:0] word, input ftz);
    logic [38:0] x; logic [1:0] sp; logic s; logic signed [12:0] e, eu, biased; logic [21:0] sig;
    logic st, inexact, up, upn, half_eq, gt_half, tiny, ovf, unf, carry_n, to_inf; integer sh, shn, sht;
    logic [22:0] keep, rest, keepn, restn, halfv, halfn; logic [22+8:0] fint, fintn; logic [10-1:0] fl;
    logic [16+13:0] code; logic [16:0] mag; logic [16-1:0] outb;
    x = m2_norm(x0); sp = x[38:38-1]; s = x[38-2] & 1; sig = x[22:1]; st = x[0]; e = x[22+13:22+1];
    fl = 0; outb = 0;
    if (sp == 2'd1) begin fl[5] = 1'b1; outb = 16'd32256; end
    else if (sp == 2'd2) begin
      outb = {s, 15'd31744}; if (!1) begin fl[4] = 1'b1; fl[2] = 1'b1; end
    end else if (sig == 0 && !st) begin outb = 1 ? 0 : {s, {15{1'b0}}}; end
    else begin
      if (sig == 0) begin sig = 1 << 21; e = e - (2*22-1); end // normalize the lone sticky's tiny value
      eu = e + 21;                 // exponent of the leading one
      biased = eu + 15;
      shn = 22 - 1 - 10;           // bits dropped at the normal precision
      sh = (biased >= 1) ? shn : shn + (1 - biased);
      sht = sh;
      if (sh > 22 + 1) sh = 22 + 1;
      keep = {1'b0, sig} >> sh; rest = {1'b0, sig} & ((sh > 22) ? {(22+1){1'b1}} : ({1'b0, {22{1'b1}}} >> (22 - sh)));
      halfv = (sh == 0) ? 0 : ({{22{1'b0}}, 1'b1} << (sh - 1));
      keepn = {1'b0, sig} >> shn; restn = {1'b0, sig} & ({1'b0, {22{1'b1}}} >> (22 - shn));
      halfn = (shn == 0) ? 0 : ({{22{1'b0}}, 1'b1} << (shn - 1));
      inexact = (rest != 0) | st;
      fint = (sht - 8 > 22) ? 0 : (sht >= 8) ? (rest >> (sht - 8)) : (rest << (8 - sht));
      fintn = (shn >= 8) ? (restn >> (shn - 8)) : (restn << (8 - shn));
      up = m2_rup(rnd, s, inexact, rest, halfv, st, keep[0], fint, word);
      upn = m2_rup(rnd, s, (restn != 0) | st, restn, halfn, st, keepn[0], fintn, word);
      carry_n = ((keepn + upn) == ({{22{1'b0}}, 1'b1} << (10 + 1)));
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
    m2_pack_fp16 = {fl, outb};
  endfunction

  // X -> fxs1i7f8 (width 16, 8 fraction bits): rounded and saturated
  function automatic [10+16-1:0] m2_pack_fxs1i7f8(input [38:0] x0, input [2:0] rnd, input [7:0] word, input ftz);
    logic [38:0] x; logic [1:0] sp; logic s, st, inexact, up, neg, big; logic signed [12:0] e, pe; logic [21:0] sig;
    logic [22:0] keep, rest, halfv; logic [22+8:0] fint; integer sh, sht, i; logic [22+18:0] wide, t; logic [10-1:0] fl; logic [15:0] outb;
    x = m2_norm(x0); sp = x[38:38-1]; s = x[38-2]; sig = x[22:1]; st = x[0]; e = x[22+13:22+1];
    fl = 0; outb = 0; neg = 1'b0; t = 0; big = 1'b0; up = 1'b0; inexact = 1'b0;
    if (sp == 2'd1) begin fl[0] = 1'b1; t = (0 == 1) ? 41'd32767 : (0 == 2) ? 41'd32768 : 0; neg = (0 == 2) && 1'b1; end
    else if (sp == 2'd2) begin fl[0] = 1'b1; neg = s; t = s ? 41'd32768 : 41'd32767; end
    else if (sig == 0 && !st) t = 0;
    else begin
      if (sig == 0) begin sig = 1; e = e - 22; end
      pe = e + 8;                  // weight of sig's lsb in units of the target lsb
      if (pe >= 0) begin
        if (pe > 18) big = 1'b1;
        else begin wide = {{(18+1){1'b0}}, sig} << pe; t = wide; end
        inexact = st;
        keep = 0; rest = 0; halfv = 0;
        up = m2_rup(rnd, s, st, {(22+1){1'b0}}, {(22+1){1'b0}}, st, t[0], 0, word);
        t = t + up;
      end else begin
        sh = -pe; sht = sh; if (sh > 22 + 1) sh = 22 + 1;
        keep = {1'b0, sig} >> sh; rest = {1'b0, sig} & ((sh > 22) ? {(22+1){1'b1}} : ({1'b0, {22{1'b1}}} >> (22 - sh)));
        halfv = ({{22{1'b0}}, 1'b1} << (sh - 1));
        inexact = (rest != 0) | st;
        fint = (sht - 8 > 22) ? 0 : (sht >= 8) ? (rest >> (sht - 8)) : (rest << (8 - sht));
        up = m2_rup(rnd, s, inexact, rest, halfv, st, keep[0], fint, word);
        t = keep + up;
      end
      neg = s && (t != 0 || big);
      if (inexact) fl[4] = 1'b1;
      if (big || (neg && t > 41'd32768) || (!neg && t > 41'd32767)) begin
        fl[2] = 1'b1; fl[4] = 1'b1; fl[0] = 1'b1;
        t = neg ? 41'd32768 : 41'd32767;
      end
      if (1'b0 && neg) begin t = 0; neg = 1'b0; end
    end
    outb = neg ? (~t[15:0] + 1'b1) : t[15:0];
    m2_pack_fxs1i7f8 = {fl, outb};
  endfunction

  function automatic [7:0] m2_enc(input signed [18:0] v); m2_enc = v[7:0]; endfunction
  function automatic [7:0] m2_wrap(input signed [18:0] v); m2_wrap = v[7:0]; endfunction
  function automatic [7:0] m2_sat(input signed [18:0] v);
    m2_sat = (v > 19'sd127) ? {1'b0, {7{1'b1}}} : (v < -19'sd128) ? {1'b1, {7{1'b0}}} : v[7:0];
  endfunction

  // round v / 2^f under rnd (the SR word applies to the fraction bits)
  function automatic signed [18:0] m2_rshift(input signed [18:0] v, input integer f, input [2:0] rnd, input [7:0] word);
    logic s; logic [18:0] mag, keep, rest, halfv; logic [27:0] fint; logic up, inexact;
    s = v < 0; mag = s ? -v : v;
    if (f <= 0) m2_rshift = v;
    else begin
      keep = mag >> f; rest = mag & (((19'd1) << f) - 1); halfv = (19'd1) << (f - 1);
      inexact = rest != 0;
      fint = (f >= 8) ? (rest >> (f - 8)) : (rest << (8 - f));
      case (rnd)
        3'd0: up = (rest > halfv) || (rest == halfv && keep[0]);
        3'd1: up = 1'b0;
        3'd2: up = inexact && s;
        3'd3: up = inexact && !s;
        3'd4: up = inexact && (0 ? (fint >= word) : (fint > word));
        default: up = inexact;
      endcase
      keep = keep + up;
      m2_rshift = s ? -$signed(keep) : $signed(keep);
    end
  endfunction
  // the SR word of a division: floor(|r| * 2^sb / |b|)
  function automatic [7:0] m2_divfrac(input [18:0] r, input [18:0] b);
    logic [27:0] t;
    t = ({{9{1'b0}}, r} << 8) / {{9{1'b0}}, b};
    m2_divfrac = t[7:0];
  endfunction
endpackage

// alu_core_m3_pkg: the exact-arithmetic functions of mode 3 (1xfxs1i7f8)
package alu_core_m3_pkg;

  // ---- m3: V = {special[1:0], sign, exp[13] (signed), sig[17]}
  //           X = {special[1:0], sign, exp[13] (signed), sig[38], sticky}
  localparam int m3_SW = 17, m3_EW = 13, m3_XW = 38;
  localparam int m3_VW = 33, m3_XT = 55;
  function automatic [32:0] m3_mkv(input [1:0] sp, input s, input signed [12:0] e, input [16:0] sig);
    m3_mkv = {sp, s, e, sig};
  endfunction
  function automatic [54:0] m3_mkx(input [1:0] sp, input s, input signed [12:0] e, input [37:0] sig, input st);
    m3_mkx = {sp, s, e, sig, st};
  endfunction
  function automatic [54:0] m3_x(input [32:0] v);   // widen V to X
    m3_x = {v[32:32-1], v[32-2], v[32-3 -: 13], {{(38-17){1'b0}}, v[16:0]}, 1'b0};
  endfunction
  // normalize: leading one at bit XW-1 (zero stays zero)
  function automatic [54:0] m3_norm(input [54:0] x);
    logic [37:0] s; logic signed [12:0] e; integer k;
    s = x[38:1]; e = x[38+13:38+1];
    if (s != 0) begin
      for (k = 32; k >= 1; k = k / 2) begin
        if (k < 38) begin
          if (s[37 -: 1] == 1'b0 && (s >> (38 - k)) == 0) begin
            s = s << k; e = e - k;
          end
        end
      end
    end
    m3_norm = {x[54:54-1], x[54-2], e, s, x[0]};
  endfunction

  function automatic m3_rup(input [2:0] rnd, input s, input inexact, input [38:0] rest, input [38:0] halfv,
                             input st, input lsb, input [38+8:0] fint, input [7:0] word);
    logic gt_half, half_eq;
    gt_half = rest > halfv; half_eq = (rest == halfv) && (halfv != 0);
    case (rnd)
      3'd0: m3_rup = gt_half || (half_eq && (st || lsb));
      3'd1: m3_rup = 1'b0;
      3'd2: m3_rup = inexact && s;
      3'd3: m3_rup = inexact && !s;
      3'd4: m3_rup = inexact && (0 ? (fint >= word) : (fint > word));
      default: m3_rup = inexact;   // 5: away from zero
    endcase
  endfunction

  // a +/- b on X (normalized inputs); specials: nan wins, inf-inf = nan
  function automatic [54:0] m3_add(input [54:0] a, input [54:0] b, input sub);
    logic [54:0] na, nb, big, sml; logic [1:0] spa, spb; logic sa, sb, sr, sw;
    logic signed [12:0] ea, eb, d; logic [38:0] ms, mb, r; logic st, stb; integer sh;
    na = m3_norm(a); nb = m3_norm(b);
    spa = na[54:54-1]; spb = nb[54:54-1];
    sa = na[54-2]; sb = nb[54-2] ^ sub;
    if (spa == 2'd1 || spb == 2'd1) m3_add = m3_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 && spb == 2'd2) m3_add = (sa == sb) ? m3_mkx(2'd2, sa, 0, 0, 1'b0) : m3_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m3_add = m3_mkx(2'd2, sa, 0, 0, 1'b0);
    else if (spb == 2'd2) m3_add = m3_mkx(2'd2, sb, 0, 0, 1'b0);
    else if (na[38:1] == 0 && !na[0]) m3_add = {nb[54:54-1], sb, nb[54-3:0]};
    else if (nb[38:1] == 0 && !nb[0]) m3_add = na;
    else begin
      ea = na[38+13:38+1]; eb = nb[38+13:38+1];
      // order by magnitude (both normalized): larger exponent, then sig
      if (ea > eb || (ea == eb && na[38:1] >= nb[38:1])) begin big = na; sml = nb; sw = 1'b0; end
      else begin big = nb; sml = na; sw = 1'b1; end
      d = big[38+13:38+1] - sml[38+13:38+1];
      ms = {1'b0, sml[38:1]}; stb = sml[0];
      if (d > 38 + 1) begin stb = stb | (ms != 0); ms = 0; end
      else begin
        for (sh = 0; sh < 38 + 2; sh = sh + 1) begin
          if (sh < d) begin stb = stb | ms[0]; ms = ms >> 1; end
        end
      end
      mb = {1'b0, big[38:1]}; st = big[0] | stb;
      if ((sw ? sb : sa) == (sw ? sa : sb)) begin
        r = mb + ms;
        sr = sw ? sb : sa;
      end else begin
        // subtract: the sticky of the smaller operand borrows one lsb
        r = mb - ms - (stb ? 1'b1 : 1'b0);
        sr = sw ? sb : sa;
        if (r == 0 && !st) sr = 1'b0;
      end
      if (r[38]) begin st = st | r[0]; r = r >> 1; m3_add = m3_mkx(2'd0, sr, big[38+13:38+1] + 1, r[37:0], st); end
      else m3_add = m3_mkx(2'd0, sr, big[38+13:38+1], r[37:0], st);
    end
  endfunction
  function automatic [54:0] m3_mul(input [54:0] a, input [54:0] b);
    logic [54:0] na, nb; logic [1:0] spa, spb; logic s; logic [2*38-1:0] pr; logic st; integer k;
    na = m3_norm(a); nb = m3_norm(b);
    spa = na[54:54-1]; spb = nb[54:54-1]; s = na[54-2] ^ nb[54-2];
    if (spa == 2'd1 || spb == 2'd1) m3_mul = m3_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 || spb == 2'd2) begin
      if ((spa == 2'd0 && na[38:1] == 0 && !na[0]) || (spb == 2'd0 && nb[38:1] == 0 && !nb[0]))
        m3_mul = m3_mkx(2'd1, 1'b0, 0, 0, 1'b0);
      else m3_mul = m3_mkx(2'd2, s, 0, 0, 1'b0);
    end else begin
      pr = na[38:1] * nb[38:1];
      st = na[0] | nb[0];
      // keep the top XW bits of the product, the rest folds into sticky
      st = st | (pr[37:0] != 0);
      m3_mul = m3_mkx(2'd0, s, na[38+13:38+1] + nb[38+13:38+1] + 38, pr[2*38-1:38], st);
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
  function automatic [2*38+1:0] m3_udiv(input [37:0] a, input [37:0] dv);
    logic [38+1:0] r; logic [38:0] q; logic ge; integer i;
    r = {2'b0, a}; q = 0;
    for (i = 38; i >= 0; i = i - 1) begin
      ge = (r >= {2'b0, dv});
      r = ge ? r - {2'b0, dv} : r;
      q = {q[37:0], ge};
      if (i > 0) r = {r[38:0], 1'b0};
    end
    m3_udiv = {q, r[38:0]};
  endfunction
  // the exact product: {special[1:0], sign, exp[EW], sig[2XW]} (no sticky)
  function automatic [2*38+13+2:0] m3_mulx(input [54:0] a, input [54:0] b);
    logic [54:0] na, nb; logic [1:0] spa, spb, sp; logic s; logic [2*38-1:0] pr;
    na = m3_norm(a); nb = m3_norm(b);
    pr = na[38:1] * nb[38:1];
    spa = na[54:54-1]; spb = nb[54:54-1]; s = na[54-2] ^ nb[54-2];
    if (spa == 2'd1 || spb == 2'd1) sp = 2'd1;
    else if (spa == 2'd2 || spb == 2'd2)
      sp = ((spa == 2'd0 && na[38:1] == 0) || (spb == 2'd0 && nb[38:1] == 0)) ? 2'd1 : 2'd2;
    else sp = 2'd0;
    m3_mulx = {sp, s, na[38+13:38+1] + nb[38+13:38+1], pr};
  endfunction
  function automatic [54:0] m3_div(input [54:0] a, input [54:0] b);
    logic [54:0] na, nb; logic [1:0] spa, spb; logic s; logic [2*38+1:0] qr; logic [38:0] q, r;
    na = m3_norm(a); nb = m3_norm(b);
    spa = na[54:54-1]; spb = nb[54:54-1]; s = na[54-2] ^ nb[54-2];
    if (spa == 2'd1 || spb == 2'd1) m3_div = m3_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 && spb == 2'd2) m3_div = m3_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m3_div = m3_mkx(2'd2, s, 0, 0, 1'b0);
    else if (spb == 2'd2) m3_div = m3_mkx(2'd0, s, 0, 0, 1'b0);
    else if (nb[38:1] == 0 && !nb[0]) begin
      if (na[38:1] == 0 && !na[0]) m3_div = m3_mkx(2'd1, 1'b0, 0, 0, 1'b0);
      else m3_div = m3_mkx(2'd2, s, 0, 0, 1'b0);
    end else if (na[38:1] == 0 && !na[0]) m3_div = m3_mkx(2'd0, s, 0, 0, 1'b0);
    else begin
      qr = m3_udiv(na[38:1], nb[38:1]);     // both normalized: nonzero finite
      q = qr[2*38+1:38+1]; r = qr[38:0];
      // q < 2^(XW+1): drop one bit when it carries
      if (q[38]) m3_div = m3_mkx(2'd0, s, na[38+13:38+1] - nb[38+13:38+1] - 38 + 1, q[38:1], (r != 0) | q[0] | na[0] | nb[0]);
      else m3_div = m3_mkx(2'd0, s, na[38+13:38+1] - nb[38+13:38+1] - 38, q[37:0], (r != 0) | na[0] | nb[0]);
    end
  endfunction
  function automatic [54:0] m3_sqrt(input [54:0] a);
    logic [54:0] na; logic [1:0] spa; logic signed [12:0] e; logic [38:0] m; logic [2*38+3:0] rad;
    logic [38+2:0] rem, trial; logic [38:0] root; logic ge; integer i;
    na = m3_norm(a); spa = na[54:54-1];
    if (spa == 2'd1) m3_sqrt = m3_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m3_sqrt = na[54-2] ? m3_mkx(2'd1, 1'b0, 0, 0, 1'b0) : na;
    else if (na[38:1] == 0 && !na[0]) m3_sqrt = na;
    else if (na[54-2]) m3_sqrt = m3_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else begin
      e = na[38+13:38+1];
      // value = m * 2^e with e even; radicand = m * 2^(2K): root = sqrt(m) * 2^K, XW+1 bits
      if (e[0]) begin m = {na[38:1], 1'b0}; e = e - 1; end
      else m = {1'b0, na[38:1]};
      rad = {{(38+3){1'b0}}, m} << 38;
      rem = 0; root = 0;
      for (i = 38; i >= 0; i = i - 1) begin
        rem = {rem[38:0], rad[2*i +: 2]};
        trial = {root, 2'b01};
        ge = (rem >= trial);                  // unconditional assignments, as in udiv
        rem = ge ? rem - trial : rem;
        root = {root[37:0], ge};
      end
      m3_sqrt = m3_mkx(2'd0, 1'b0, (e >>> 1) - 19 + 1, root[38:1], (rem != 0) | root[0] | na[0]);
    end
  endfunction
  // X ordering treats NaN as unordered and compares finite values by sign and magnitude
  function automatic m3_lt(input [54:0] a, input [54:0] b);
    logic [54:0] na, nb; logic za, zb, sa, sb, mag_lt; logic signed [12:0] ea, eb;
    na = m3_norm(a); nb = m3_norm(b);
    za = (na[38:1] == 0) && !na[0]; zb = (nb[38:1] == 0) && !nb[0];
    sa = na[54-2] && !za; sb = nb[54-2] && !zb;
    if (na[54:54-1] == 2'd1 || nb[54:54-1] == 2'd1) m3_lt = 1'b0;
    else if (na[54:54-1] == 2'd2 || nb[54:54-1] == 2'd2) begin
      if (na[54:54-1] == 2'd2 && nb[54:54-1] == 2'd2) m3_lt = na[54-2] && !nb[54-2];
      else if (na[54:54-1] == 2'd2) m3_lt = na[54-2];
      else m3_lt = !nb[54-2];
    end else if (za && zb) m3_lt = 1'b0;
    else if (sa != sb) m3_lt = sa;
    else begin
      ea = na[38+13:38+1]; eb = nb[38+13:38+1];
      if (za) mag_lt = 1'b1; else if (zb) mag_lt = 1'b0;
      else mag_lt = (ea < eb) || (ea == eb && (na[38:1] < nb[38:1] || (na[38:1] == nb[38:1] && !na[0] && nb[0])));
      m3_lt = sa ? !mag_lt && !(za && zb) && !m3_eq(na, nb) : mag_lt;
    end
  endfunction
  function automatic m3_eq(input [54:0] a, input [54:0] b);
    logic [54:0] na, nb; logic za, zb;
    na = m3_norm(a); nb = m3_norm(b);
    za = (na[38:1] == 0) && !na[0]; zb = (nb[38:1] == 0) && !nb[0];
    if (na[54:54-1] == 2'd1 || nb[54:54-1] == 2'd1) m3_eq = 1'b0;
    else if (na[54:54-1] == 2'd2 || nb[54:54-1] == 2'd2)
      m3_eq = (na[54:54-1] == nb[54:54-1]) && (na[54-2] == nb[54-2]);
    else if (za || zb) m3_eq = za && zb;
    else m3_eq = (na[54-2] == nb[54-2]) && (na[38+13:38+1] == nb[38+13:38+1]) && (na[38:1] == nb[38:1]) && (na[0] == nb[0]);
  endfunction

  function automatic [33:0] m3_unpack_s(input [15:0] b, input daz);
    logic s; logic [15:0] mag; integer i;
    s = b[15]; mag = s ? (~b + 1'b1) : b;
    m3_unpack_s = {1'b0, m3_mkv(2'd0, s && (mag != 0), -8, {{(17-16){1'b0}}, mag})};
  endfunction

  // X -> int8_twos_complement (width 8, 0 fraction bits): rounded and saturated
  function automatic [10+8-1:0] m3_pack_int8_twos_complement(input [54:0] x0, input [2:0] rnd, input [7:0] word, input ftz);
    logic [54:0] x; logic [1:0] sp; logic s, st, inexact, up, neg, big; logic signed [12:0] e, pe; logic [37:0] sig;
    logic [38:0] keep, rest, halfv; logic [38+8:0] fint; integer sh, sht, i; logic [38+10:0] wide, t; logic [10-1:0] fl; logic [7:0] outb;
    x = m3_norm(x0); sp = x[54:54-1]; s = x[54-2]; sig = x[38:1]; st = x[0]; e = x[38+13:38+1];
    fl = 0; outb = 0; neg = 1'b0; t = 0; big = 1'b0; up = 1'b0; inexact = 1'b0;
    if (sp == 2'd1) begin fl[0] = 1'b1; t = (0 == 1) ? 49'd127 : (0 == 2) ? 49'd128 : 0; neg = (0 == 2) && 1'b1; end
    else if (sp == 2'd2) begin fl[0] = 1'b1; neg = s; t = s ? 49'd128 : 49'd127; end
    else if (sig == 0 && !st) t = 0;
    else begin
      if (sig == 0) begin sig = 1; e = e - 38; end
      pe = e + 0;                  // weight of sig's lsb in units of the target lsb
      if (pe >= 0) begin
        if (pe > 10) big = 1'b1;
        else begin wide = {{(10+1){1'b0}}, sig} << pe; t = wide; end
        inexact = st;
        keep = 0; rest = 0; halfv = 0;
        up = m3_rup(rnd, s, st, {(38+1){1'b0}}, {(38+1){1'b0}}, st, t[0], 0, word);
        t = t + up;
      end else begin
        sh = -pe; sht = sh; if (sh > 38 + 1) sh = 38 + 1;
        keep = {1'b0, sig} >> sh; rest = {1'b0, sig} & ((sh > 38) ? {(38+1){1'b1}} : ({1'b0, {38{1'b1}}} >> (38 - sh)));
        halfv = ({{38{1'b0}}, 1'b1} << (sh - 1));
        inexact = (rest != 0) | st;
        fint = (sht - 8 > 38) ? 0 : (sht >= 8) ? (rest >> (sht - 8)) : (rest << (8 - sht));
        up = m3_rup(rnd, s, inexact, rest, halfv, st, keep[0], fint, word);
        t = keep + up;
      end
      neg = s && (t != 0 || big);
      if (inexact) fl[4] = 1'b1;
      if (big || (neg && t > 49'd128) || (!neg && t > 49'd127)) begin
        fl[2] = 1'b1; fl[4] = 1'b1; fl[0] = 1'b1;
        t = neg ? 49'd128 : 49'd127;
      end
      if (1'b0 && neg) begin t = 0; neg = 1'b0; end
    end
    outb = neg ? (~t[7:0] + 1'b1) : t[7:0];
    m3_pack_int8_twos_complement = {fl, outb};
  endfunction

  // X -> fp16 (fp16): sign(1) exp 5 man 10, top field 30, max finite 15'd31743
  function automatic [10+16-1:0] m3_pack_fp16(input [54:0] x0, input [2:0] rnd, input [7:0] word, input ftz);
    logic [54:0] x; logic [1:0] sp; logic s; logic signed [12:0] e, eu, biased; logic [37:0] sig;
    logic st, inexact, up, upn, half_eq, gt_half, tiny, ovf, unf, carry_n, to_inf; integer sh, shn, sht;
    logic [38:0] keep, rest, keepn, restn, halfv, halfn; logic [38+8:0] fint, fintn; logic [10-1:0] fl;
    logic [16+13:0] code; logic [16:0] mag; logic [16-1:0] outb;
    x = m3_norm(x0); sp = x[54:54-1]; s = x[54-2] & 1; sig = x[38:1]; st = x[0]; e = x[38+13:38+1];
    fl = 0; outb = 0;
    if (sp == 2'd1) begin fl[5] = 1'b1; outb = 16'd32256; end
    else if (sp == 2'd2) begin
      outb = {s, 15'd31744}; if (!1) begin fl[4] = 1'b1; fl[2] = 1'b1; end
    end else if (sig == 0 && !st) begin outb = 1 ? 0 : {s, {15{1'b0}}}; end
    else begin
      if (sig == 0) begin sig = 1 << 37; e = e - (2*38-1); end // normalize the lone sticky's tiny value
      eu = e + 37;                 // exponent of the leading one
      biased = eu + 15;
      shn = 38 - 1 - 10;           // bits dropped at the normal precision
      sh = (biased >= 1) ? shn : shn + (1 - biased);
      sht = sh;
      if (sh > 38 + 1) sh = 38 + 1;
      keep = {1'b0, sig} >> sh; rest = {1'b0, sig} & ((sh > 38) ? {(38+1){1'b1}} : ({1'b0, {38{1'b1}}} >> (38 - sh)));
      halfv = (sh == 0) ? 0 : ({{38{1'b0}}, 1'b1} << (sh - 1));
      keepn = {1'b0, sig} >> shn; restn = {1'b0, sig} & ({1'b0, {38{1'b1}}} >> (38 - shn));
      halfn = (shn == 0) ? 0 : ({{38{1'b0}}, 1'b1} << (shn - 1));
      inexact = (rest != 0) | st;
      fint = (sht - 8 > 38) ? 0 : (sht >= 8) ? (rest >> (sht - 8)) : (rest << (8 - sht));
      fintn = (shn >= 8) ? (restn >> (shn - 8)) : (restn << (8 - shn));
      up = m3_rup(rnd, s, inexact, rest, halfv, st, keep[0], fint, word);
      upn = m3_rup(rnd, s, (restn != 0) | st, restn, halfn, st, keepn[0], fintn, word);
      carry_n = ((keepn + upn) == ({{38{1'b0}}, 1'b1} << (10 + 1)));
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
    m3_pack_fp16 = {fl, outb};
  endfunction

  // X -> fxs1i7f8 (width 16, 8 fraction bits): rounded and saturated
  function automatic [10+16-1:0] m3_pack_fxs1i7f8(input [54:0] x0, input [2:0] rnd, input [7:0] word, input ftz);
    logic [54:0] x; logic [1:0] sp; logic s, st, inexact, up, neg, big; logic signed [12:0] e, pe; logic [37:0] sig;
    logic [38:0] keep, rest, halfv; logic [38+8:0] fint; integer sh, sht, i; logic [38+18:0] wide, t; logic [10-1:0] fl; logic [15:0] outb;
    x = m3_norm(x0); sp = x[54:54-1]; s = x[54-2]; sig = x[38:1]; st = x[0]; e = x[38+13:38+1];
    fl = 0; outb = 0; neg = 1'b0; t = 0; big = 1'b0; up = 1'b0; inexact = 1'b0;
    if (sp == 2'd1) begin fl[0] = 1'b1; t = (0 == 1) ? 57'd32767 : (0 == 2) ? 57'd32768 : 0; neg = (0 == 2) && 1'b1; end
    else if (sp == 2'd2) begin fl[0] = 1'b1; neg = s; t = s ? 57'd32768 : 57'd32767; end
    else if (sig == 0 && !st) t = 0;
    else begin
      if (sig == 0) begin sig = 1; e = e - 38; end
      pe = e + 8;                  // weight of sig's lsb in units of the target lsb
      if (pe >= 0) begin
        if (pe > 18) big = 1'b1;
        else begin wide = {{(18+1){1'b0}}, sig} << pe; t = wide; end
        inexact = st;
        keep = 0; rest = 0; halfv = 0;
        up = m3_rup(rnd, s, st, {(38+1){1'b0}}, {(38+1){1'b0}}, st, t[0], 0, word);
        t = t + up;
      end else begin
        sh = -pe; sht = sh; if (sh > 38 + 1) sh = 38 + 1;
        keep = {1'b0, sig} >> sh; rest = {1'b0, sig} & ((sh > 38) ? {(38+1){1'b1}} : ({1'b0, {38{1'b1}}} >> (38 - sh)));
        halfv = ({{38{1'b0}}, 1'b1} << (sh - 1));
        inexact = (rest != 0) | st;
        fint = (sht - 8 > 38) ? 0 : (sht >= 8) ? (rest >> (sht - 8)) : (rest << (8 - sht));
        up = m3_rup(rnd, s, inexact, rest, halfv, st, keep[0], fint, word);
        t = keep + up;
      end
      neg = s && (t != 0 || big);
      if (inexact) fl[4] = 1'b1;
      if (big || (neg && t > 57'd32768) || (!neg && t > 57'd32767)) begin
        fl[2] = 1'b1; fl[4] = 1'b1; fl[0] = 1'b1;
        t = neg ? 57'd32768 : 57'd32767;
      end
      if (1'b0 && neg) begin t = 0; neg = 1'b0; end
    end
    outb = neg ? (~t[15:0] + 1'b1) : t[15:0];
    m3_pack_fxs1i7f8 = {fl, outb};
  endfunction

  function automatic [15:0] m3_enc(input signed [34:0] v); m3_enc = v[15:0]; endfunction
  function automatic [15:0] m3_wrap(input signed [34:0] v); m3_wrap = v[15:0]; endfunction
  function automatic [15:0] m3_sat(input signed [34:0] v);
    m3_sat = (v > 35'sd32767) ? {1'b0, {15{1'b1}}} : (v < -35'sd32768) ? {1'b1, {15{1'b0}}} : v[15:0];
  endfunction

  // round v / 2^f under rnd (the SR word applies to the fraction bits)
  function automatic signed [34:0] m3_rshift(input signed [34:0] v, input integer f, input [2:0] rnd, input [7:0] word);
    logic s; logic [34:0] mag, keep, rest, halfv; logic [43:0] fint; logic up, inexact;
    s = v < 0; mag = s ? -v : v;
    if (f <= 0) m3_rshift = v;
    else begin
      keep = mag >> f; rest = mag & (((35'd1) << f) - 1); halfv = (35'd1) << (f - 1);
      inexact = rest != 0;
      fint = (f >= 8) ? (rest >> (f - 8)) : (rest << (8 - f));
      case (rnd)
        3'd0: up = (rest > halfv) || (rest == halfv && keep[0]);
        3'd1: up = 1'b0;
        3'd2: up = inexact && s;
        3'd3: up = inexact && !s;
        3'd4: up = inexact && (0 ? (fint >= word) : (fint > word));
        default: up = inexact;
      endcase
      keep = keep + up;
      m3_rshift = s ? -$signed(keep) : $signed(keep);
    end
  endfunction
  // the SR word of a division: floor(|r| * 2^sb / |b|)
  function automatic [7:0] m3_divfrac(input [34:0] r, input [34:0] b);
    logic [43:0] t;
    t = ({{9{1'b0}}, r} << 8) / {{9{1'b0}}, b};
    m3_divfrac = t[7:0];
  endfunction
endpackage
// ADIR-MEMBER top
// EVOLVE-BLOCK-START
// ADIR-DECL v1
// STRUCTURE m0.l0.fp_adder kind=fp_adder slot=fp_adder mode=0 lane=0 width=16 format=fp16 ops=fadd sv=alu_core_u_m0_l0_fp_adder
// STRUCTURE m0.l0.unpacker kind=unpacker slot=unpacker mode=0 lane=0 width=16 format=fp16 ops=fadd,fmul,cvt(int8),cvt(fp16),cvt(fxs1i7f8) sv=alu_core_u_m0_l0_unpacker
// STRUCTURE m0.l0.rounder kind=rounder slot=rounder mode=0 lane=0 width=16 format=fp16 ops=fadd,fmul,cvt(int8),cvt(fp16),cvt(fxs1i7f8) sv=alu_core_u_m0_l0_rounder
// STRUCTURE m0.l0.fp_fma kind=fp_fma slot=fp_fma mode=0 lane=0 width=16 format=fp16 ops=fadd,fmul
// STRUCTURE m0.l0.fp_multiplier kind=fp_multiplier slot=fp_multiplier mode=0 lane=0 width=16 format=fp16 ops=fmul sv=alu_core_u_m0_l0_fp_multiplier
// STRUCTURE m0.l0.converter.int8_twos_complement kind=converter slot=converter mode=0 lane=0 width=16 format=fp16 ops=cvt(int8) target=int8_twos_complement sv=alu_core_u_m0_l0_converter_int8_twos_complement
// STRUCTURE m0.l0.converter.fp16 kind=converter slot=converter mode=0 lane=0 width=16 format=fp16 ops=cvt(fp16) target=fp16 sv=alu_core_u_m0_l0_converter_fp16
// STRUCTURE m0.l0.converter.fxs1i7f8 kind=converter slot=converter mode=0 lane=0 width=16 format=fp16 ops=cvt(fxs1i7f8) target=fxs1i7f8 sv=alu_core_u_m0_l0_converter_fxs1i7f8
// STRUCTURE m1.l0.adder kind=adder slot=adder mode=1 lane=0 width=16 format=int16_twos_complement ops=add sv=alu_core_u_m1_l0_adder
// STRUCTURE m1.l0.multiplier kind=multiplier slot=multiplier mode=1 lane=0 width=16 format=int16_twos_complement ops=mul sv=alu_core_u_m1_l0_multiplier
// STRUCTURE m1.l0.comparator kind=comparator slot=comparator mode=1 lane=0 width=16 format=int16_twos_complement ops=min sv=alu_core_u_m1_l0_comparator
// STRUCTURE m1.l0.converter.int8_twos_complement kind=converter slot=converter mode=1 lane=0 width=16 format=int16_twos_complement ops=cvt(int8) target=int8_twos_complement sv=alu_core_u_m1_l0_converter_int8_twos_complement
// STRUCTURE m1.l0.converter.fp16 kind=converter slot=converter mode=1 lane=0 width=16 format=int16_twos_complement ops=cvt(fp16) target=fp16 sv=alu_core_u_m1_l0_converter_fp16
// STRUCTURE m1.l0.converter.fxs1i7f8 kind=converter slot=converter mode=1 lane=0 width=16 format=int16_twos_complement ops=cvt(fxs1i7f8) target=fxs1i7f8 sv=alu_core_u_m1_l0_converter_fxs1i7f8
// STRUCTURE m2.l0.adder kind=adder slot=adder mode=2 lane=0 width=8 format=int8_twos_complement ops=add sv=alu_core_u_m2_l0_adder
// STRUCTURE m2.l1.adder kind=adder slot=adder mode=2 lane=1 width=8 format=int8_twos_complement ops=add sv=alu_core_u_m2_l1_adder
// STRUCTURE m2.l0.multiplier kind=multiplier slot=multiplier mode=2 lane=0 width=8 format=int8_twos_complement ops=mul sv=alu_core_u_m2_l0_multiplier
// STRUCTURE m2.l1.multiplier kind=multiplier slot=multiplier mode=2 lane=1 width=8 format=int8_twos_complement ops=mul sv=alu_core_u_m2_l1_multiplier
// STRUCTURE m2.l0.comparator kind=comparator slot=comparator mode=2 lane=0 width=8 format=int8_twos_complement ops=min sv=alu_core_u_m2_l0_comparator
// STRUCTURE m2.l1.comparator kind=comparator slot=comparator mode=2 lane=1 width=8 format=int8_twos_complement ops=min sv=alu_core_u_m2_l1_comparator
// STRUCTURE m2.l0.converter.int8_twos_complement kind=converter slot=converter mode=2 lane=0 width=8 format=int8_twos_complement ops=cvt(int8) target=int8_twos_complement sv=alu_core_u_m2_l0_converter_int8_twos_complement
// STRUCTURE m2.l1.converter.int8_twos_complement kind=converter slot=converter mode=2 lane=1 width=8 format=int8_twos_complement ops=cvt(int8) target=int8_twos_complement sv=alu_core_u_m2_l1_converter_int8_twos_complement
// STRUCTURE m2.l0.converter.fp16 kind=converter slot=converter mode=2 lane=0 width=8 format=int8_twos_complement ops=cvt(fp16) target=fp16 sv=alu_core_u_m2_l0_converter_fp16
// STRUCTURE m2.l1.converter.fp16 kind=converter slot=converter mode=2 lane=1 width=8 format=int8_twos_complement ops=cvt(fp16) target=fp16 sv=alu_core_u_m2_l1_converter_fp16
// STRUCTURE m2.l0.converter.fxs1i7f8 kind=converter slot=converter mode=2 lane=0 width=8 format=int8_twos_complement ops=cvt(fxs1i7f8) target=fxs1i7f8 sv=alu_core_u_m2_l0_converter_fxs1i7f8
// STRUCTURE m2.l1.converter.fxs1i7f8 kind=converter slot=converter mode=2 lane=1 width=8 format=int8_twos_complement ops=cvt(fxs1i7f8) target=fxs1i7f8 sv=alu_core_u_m2_l1_converter_fxs1i7f8
// STRUCTURE m3.l0.adder kind=adder slot=adder mode=3 lane=0 width=16 format=fxs1i7f8 ops=add sv=alu_core_u_m3_l0_adder
// STRUCTURE m3.l0.multiplier kind=multiplier slot=multiplier mode=3 lane=0 width=16 format=fxs1i7f8 ops=mul sv=alu_core_u_m3_l0_multiplier
// STRUCTURE m3.l0.comparator kind=comparator slot=comparator mode=3 lane=0 width=16 format=fxs1i7f8 ops=min sv=alu_core_u_m3_l0_comparator
// STRUCTURE m3.l0.converter.int8_twos_complement kind=converter slot=converter mode=3 lane=0 width=16 format=fxs1i7f8 ops=cvt(int8) target=int8_twos_complement sv=alu_core_u_m3_l0_converter_int8_twos_complement
// STRUCTURE m3.l0.converter.fp16 kind=converter slot=converter mode=3 lane=0 width=16 format=fxs1i7f8 ops=cvt(fp16) target=fp16 sv=alu_core_u_m3_l0_converter_fp16
// STRUCTURE m3.l0.converter.fxs1i7f8 kind=converter slot=converter mode=3 lane=0 width=16 format=fxs1i7f8 ops=cvt(fxs1i7f8) target=fxs1i7f8 sv=alu_core_u_m3_l0_converter_fxs1i7f8
// ADIR-END
module alu_core (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [1:0] mode,
  output logic [31:0] y
);
  // alu_core: behavioral reference derived from the instance (modes 1xfp16, 1xint16_twos_complement, 2xint8_twos_complement, 1xfxs1i7f8; ops add, mul, min, fadd, fmul, cvt(int8), cvt(fp16), cvt(fxs1i7f8)). Every (mode, op) pair computes the verify layer's exact semantics.
  // HIERARCHY: 31 physical structure modules instantiated by alu_core, built from 17 lane modules (one per mode and kind, parameter LANE) and 4 packages of engine functions (one per mode); a float mode's datapath is split into an unpacker (the xa/xb/den buses), the arithmetic and converter structures (unrounded results on the x bus) and a rounder (y and the flags); 0 misc lane modules and 0 block-conversion group modules
  // UNIT m0.l0.fp_adder module=alu_core_u_m0_l0_fp_adder kind=fp_adder members=m0.l0.fp_adder
  // UNIT m0.l0.unpacker module=alu_core_u_m0_l0_unpacker kind=unpacker members=m0.l0.unpacker
  // UNIT m0.l0.rounder module=alu_core_u_m0_l0_rounder kind=rounder members=m0.l0.rounder
  // UNIT m0.l0.fp_multiplier module=alu_core_u_m0_l0_fp_multiplier kind=fp_multiplier members=m0.l0.fp_multiplier
  // UNIT m0.l0.converter.int8_twos_complement module=alu_core_u_m0_l0_converter_int8_twos_complement kind=converter members=m0.l0.converter.int8_twos_complement
  // UNIT m0.l0.converter.fp16 module=alu_core_u_m0_l0_converter_fp16 kind=converter members=m0.l0.converter.fp16
  // UNIT m0.l0.converter.fxs1i7f8 module=alu_core_u_m0_l0_converter_fxs1i7f8 kind=converter members=m0.l0.converter.fxs1i7f8
  // UNIT m1.l0.adder module=alu_core_u_m1_l0_adder kind=adder members=m1.l0.adder
  // UNIT m1.l0.multiplier module=alu_core_u_m1_l0_multiplier kind=multiplier members=m1.l0.multiplier
  // UNIT m1.l0.comparator module=alu_core_u_m1_l0_comparator kind=comparator members=m1.l0.comparator
  // UNIT m1.l0.converter.int8_twos_complement module=alu_core_u_m1_l0_converter_int8_twos_complement kind=converter members=m1.l0.converter.int8_twos_complement
  // UNIT m1.l0.converter.fp16 module=alu_core_u_m1_l0_converter_fp16 kind=converter members=m1.l0.converter.fp16
  // UNIT m1.l0.converter.fxs1i7f8 module=alu_core_u_m1_l0_converter_fxs1i7f8 kind=converter members=m1.l0.converter.fxs1i7f8
  // UNIT m2.l0.adder module=alu_core_u_m2_l0_adder kind=adder members=m2.l0.adder
  // UNIT m2.l1.adder module=alu_core_u_m2_l1_adder kind=adder members=m2.l1.adder
  // UNIT m2.l0.multiplier module=alu_core_u_m2_l0_multiplier kind=multiplier members=m2.l0.multiplier
  // UNIT m2.l1.multiplier module=alu_core_u_m2_l1_multiplier kind=multiplier members=m2.l1.multiplier
  // UNIT m2.l0.comparator module=alu_core_u_m2_l0_comparator kind=comparator members=m2.l0.comparator
  // UNIT m2.l1.comparator module=alu_core_u_m2_l1_comparator kind=comparator members=m2.l1.comparator
  // UNIT m2.l0.converter.int8_twos_complement module=alu_core_u_m2_l0_converter_int8_twos_complement kind=converter members=m2.l0.converter.int8_twos_complement
  // UNIT m2.l1.converter.int8_twos_complement module=alu_core_u_m2_l1_converter_int8_twos_complement kind=converter members=m2.l1.converter.int8_twos_complement
  // UNIT m2.l0.converter.fp16 module=alu_core_u_m2_l0_converter_fp16 kind=converter members=m2.l0.converter.fp16
  // UNIT m2.l1.converter.fp16 module=alu_core_u_m2_l1_converter_fp16 kind=converter members=m2.l1.converter.fp16
  // UNIT m2.l0.converter.fxs1i7f8 module=alu_core_u_m2_l0_converter_fxs1i7f8 kind=converter members=m2.l0.converter.fxs1i7f8
  // UNIT m2.l1.converter.fxs1i7f8 module=alu_core_u_m2_l1_converter_fxs1i7f8 kind=converter members=m2.l1.converter.fxs1i7f8
  // UNIT m3.l0.adder module=alu_core_u_m3_l0_adder kind=adder members=m3.l0.adder
  // UNIT m3.l0.multiplier module=alu_core_u_m3_l0_multiplier kind=multiplier members=m3.l0.multiplier
  // UNIT m3.l0.comparator module=alu_core_u_m3_l0_comparator kind=comparator members=m3.l0.comparator
  // UNIT m3.l0.converter.int8_twos_complement module=alu_core_u_m3_l0_converter_int8_twos_complement kind=converter members=m3.l0.converter.int8_twos_complement
  // UNIT m3.l0.converter.fp16 module=alu_core_u_m3_l0_converter_fp16 kind=converter members=m3.l0.converter.fp16
  // UNIT m3.l0.converter.fxs1i7f8 module=alu_core_u_m3_l0_converter_fxs1i7f8 kind=converter members=m3.l0.converter.fxs1i7f8
  // // STRUCTURE m0.l0.fp_adder kind=fp_adder slot=fp_adder mode=0 lane=0 width=16 format=fp16 ops=fadd sv=alu_core_u_m0_l0_fp_adder
  // // STRUCTURE m0.l0.unpacker kind=unpacker slot=unpacker mode=0 lane=0 width=16 format=fp16 ops=fadd,fmul,cvt(int8),cvt(fp16),cvt(fxs1i7f8) sv=alu_core_u_m0_l0_unpacker
  // // STRUCTURE m0.l0.rounder kind=rounder slot=rounder mode=0 lane=0 width=16 format=fp16 ops=fadd,fmul,cvt(int8),cvt(fp16),cvt(fxs1i7f8) sv=alu_core_u_m0_l0_rounder
  // // STRUCTURE m0.l0.fp_fma kind=fp_fma slot=fp_fma mode=0 lane=0 width=16 format=fp16 ops=fadd,fmul
  // // STRUCTURE m0.l0.fp_multiplier kind=fp_multiplier slot=fp_multiplier mode=0 lane=0 width=16 format=fp16 ops=fmul sv=alu_core_u_m0_l0_fp_multiplier
  // // STRUCTURE m0.l0.converter.int8_twos_complement kind=converter slot=converter mode=0 lane=0 width=16 format=fp16 ops=cvt(int8) target=int8_twos_complement sv=alu_core_u_m0_l0_converter_int8_twos_complement
  // // STRUCTURE m0.l0.converter.fp16 kind=converter slot=converter mode=0 lane=0 width=16 format=fp16 ops=cvt(fp16) target=fp16 sv=alu_core_u_m0_l0_converter_fp16
  // // STRUCTURE m0.l0.converter.fxs1i7f8 kind=converter slot=converter mode=0 lane=0 width=16 format=fp16 ops=cvt(fxs1i7f8) target=fxs1i7f8 sv=alu_core_u_m0_l0_converter_fxs1i7f8
  // // STRUCTURE m1.l0.adder kind=adder slot=adder mode=1 lane=0 width=16 format=int16_twos_complement ops=add sv=alu_core_u_m1_l0_adder
  // // STRUCTURE m1.l0.multiplier kind=multiplier slot=multiplier mode=1 lane=0 width=16 format=int16_twos_complement ops=mul sv=alu_core_u_m1_l0_multiplier
  // // STRUCTURE m1.l0.comparator kind=comparator slot=comparator mode=1 lane=0 width=16 format=int16_twos_complement ops=min sv=alu_core_u_m1_l0_comparator
  // // STRUCTURE m1.l0.converter.int8_twos_complement kind=converter slot=converter mode=1 lane=0 width=16 format=int16_twos_complement ops=cvt(int8) target=int8_twos_complement sv=alu_core_u_m1_l0_converter_int8_twos_complement
  // // STRUCTURE m1.l0.converter.fp16 kind=converter slot=converter mode=1 lane=0 width=16 format=int16_twos_complement ops=cvt(fp16) target=fp16 sv=alu_core_u_m1_l0_converter_fp16
  // // STRUCTURE m1.l0.converter.fxs1i7f8 kind=converter slot=converter mode=1 lane=0 width=16 format=int16_twos_complement ops=cvt(fxs1i7f8) target=fxs1i7f8 sv=alu_core_u_m1_l0_converter_fxs1i7f8
  // // STRUCTURE m2.l0.adder kind=adder slot=adder mode=2 lane=0 width=8 format=int8_twos_complement ops=add sv=alu_core_u_m2_l0_adder
  // // STRUCTURE m2.l1.adder kind=adder slot=adder mode=2 lane=1 width=8 format=int8_twos_complement ops=add sv=alu_core_u_m2_l1_adder
  // // STRUCTURE m2.l0.multiplier kind=multiplier slot=multiplier mode=2 lane=0 width=8 format=int8_twos_complement ops=mul sv=alu_core_u_m2_l0_multiplier
  // // STRUCTURE m2.l1.multiplier kind=multiplier slot=multiplier mode=2 lane=1 width=8 format=int8_twos_complement ops=mul sv=alu_core_u_m2_l1_multiplier
  // // STRUCTURE m2.l0.comparator kind=comparator slot=comparator mode=2 lane=0 width=8 format=int8_twos_complement ops=min sv=alu_core_u_m2_l0_comparator
  // // STRUCTURE m2.l1.comparator kind=comparator slot=comparator mode=2 lane=1 width=8 format=int8_twos_complement ops=min sv=alu_core_u_m2_l1_comparator
  // // STRUCTURE m2.l0.converter.int8_twos_complement kind=converter slot=converter mode=2 lane=0 width=8 format=int8_twos_complement ops=cvt(int8) target=int8_twos_complement sv=alu_core_u_m2_l0_converter_int8_twos_complement
  // // STRUCTURE m2.l1.converter.int8_twos_complement kind=converter slot=converter mode=2 lane=1 width=8 format=int8_twos_complement ops=cvt(int8) target=int8_twos_complement sv=alu_core_u_m2_l1_converter_int8_twos_complement
  // // STRUCTURE m2.l0.converter.fp16 kind=converter slot=converter mode=2 lane=0 width=8 format=int8_twos_complement ops=cvt(fp16) target=fp16 sv=alu_core_u_m2_l0_converter_fp16
  // // STRUCTURE m2.l1.converter.fp16 kind=converter slot=converter mode=2 lane=1 width=8 format=int8_twos_complement ops=cvt(fp16) target=fp16 sv=alu_core_u_m2_l1_converter_fp16
  // // STRUCTURE m2.l0.converter.fxs1i7f8 kind=converter slot=converter mode=2 lane=0 width=8 format=int8_twos_complement ops=cvt(fxs1i7f8) target=fxs1i7f8 sv=alu_core_u_m2_l0_converter_fxs1i7f8
  // // STRUCTURE m2.l1.converter.fxs1i7f8 kind=converter slot=converter mode=2 lane=1 width=8 format=int8_twos_complement ops=cvt(fxs1i7f8) target=fxs1i7f8 sv=alu_core_u_m2_l1_converter_fxs1i7f8
  // // STRUCTURE m3.l0.adder kind=adder slot=adder mode=3 lane=0 width=16 format=fxs1i7f8 ops=add sv=alu_core_u_m3_l0_adder
  // // STRUCTURE m3.l0.multiplier kind=multiplier slot=multiplier mode=3 lane=0 width=16 format=fxs1i7f8 ops=mul sv=alu_core_u_m3_l0_multiplier
  // // STRUCTURE m3.l0.comparator kind=comparator slot=comparator mode=3 lane=0 width=16 format=fxs1i7f8 ops=min sv=alu_core_u_m3_l0_comparator
  // // STRUCTURE m3.l0.converter.int8_twos_complement kind=converter slot=converter mode=3 lane=0 width=16 format=fxs1i7f8 ops=cvt(int8) target=int8_twos_complement sv=alu_core_u_m3_l0_converter_int8_twos_complement
  // // STRUCTURE m3.l0.converter.fp16 kind=converter slot=converter mode=3 lane=0 width=16 format=fxs1i7f8 ops=cvt(fp16) target=fp16 sv=alu_core_u_m3_l0_converter_fp16
  // // STRUCTURE m3.l0.converter.fxs1i7f8 kind=converter slot=converter mode=3 lane=0 width=16 format=fxs1i7f8 ops=cvt(fxs1i7f8) target=fxs1i7f8 sv=alu_core_u_m3_l0_converter_fxs1i7f8
  // LIBRARY: fam_add_partitioned_w16_16_carry_kill_gate_0cc88441ac18, fam_add_partitioned_w16_8_carry_kill_gate_0cc88441ac18, fam_adder_ripple_carry, fam_adder_ripple_chunk, fam_cmp_prefix_comparator, fam_count_lzd_pair_cell_binary_count_vflat_w11, fam_count_lzd_pair_cell_binary_count_vflat_w22, fam_count_lzd_pair_cell_binary_count_vflat_w26, fam_count_lzd_pair_cell_binary_count_vflat_w38, fam_fp_add_single_path_x26e13s11_p9d459d224988, fam_fp_mul_sig_mul_then_round_x26e13s11_pbd766efe148c, fam_fp_round_dedicated_per_op_increment_adder_fp16_x26e13s11_pd77ccc5b5c45, fam_fp_round_shift_round_convert_increment_adder_fp16_x26e13s11_pd77ccc5b5c45, fam_fp_unpack_per_unit_unpack_fp16_x26e13s11_p9bfe39588414, fam_incr_prefix_and, fam_int_cvt_shift_round_convert_fp16_x22e13s9, fam_int_cvt_shift_round_convert_fp16_x38e13s17, fam_int_cvt_shift_round_convert_fxs1i7f8_x22e13s9, fam_int_cvt_shift_round_convert_fxs1i7f8_x38e13s17, fam_int_cvt_shift_round_convert_int8_twos_complement_x22e13s9, fam_int_cvt_shift_round_convert_int8_twos_complement_x38e13s17, fam_int_round_fxs1i7f8_x26e13s11_pd77ccc5b5c45, fam_int_round_int8_twos_complement_x26e13s11_pd77ccc5b5c45, fam_mul_behavioral_star_w11_u_pfc463c41, fam_mul_behavioral_star_w16_s, fam_mul_behavioral_star_w8_s, fam_shift_barrel_mux_tree, fam_shift_keep_mask, fam_shift_stage (chialu.targets.rtl.families: the modules of the declared families the lane modules instantiate; their text follows the generated modules)
  logic [2:0] rnd_sel;
  logic [2:0] rnd;
  logic daz;
  logic ftz;
  logic dual;
  logic [31:0] y_m0_m0_l0_fp_adder;
  logic [19:0] fl_m0_m0_l0_fp_adder;
  logic [42:0] x_m0_m0_m0_l0_fp_adder;
  logic [42:0] xa_m0_m0_m0_l0_unpacker;
  logic [42:0] xb_m0_m0_m0_l0_unpacker;
  logic dena_m0_m0_m0_l0_unpacker;
  logic denb_m0_m0_m0_l0_unpacker;
  logic [31:0] y_m0_m0_l0_rounder;
  logic [19:0] fl_m0_m0_l0_rounder;
  logic [31:0] y_m0_m0_l0_fp_multiplier;
  logic [19:0] fl_m0_m0_l0_fp_multiplier;
  logic [42:0] x_m0_m0_m0_l0_fp_multiplier;
  logic [31:0] y_m0_m0_l0_converter_int8_twos_complement;
  logic [19:0] fl_m0_m0_l0_converter_int8_twos_complement;
  logic [42:0] x_m0_m0_m0_l0_converter_int8_twos_complement;
  logic [31:0] y_m0_m0_l0_converter_fp16;
  logic [19:0] fl_m0_m0_l0_converter_fp16;
  logic [42:0] x_m0_m0_m0_l0_converter_fp16;
  logic [31:0] y_m0_m0_l0_converter_fxs1i7f8;
  logic [19:0] fl_m0_m0_l0_converter_fxs1i7f8;
  logic [42:0] x_m0_m0_m0_l0_converter_fxs1i7f8;
  logic [31:0] y_m0;
  logic [19:0] fl_m0;
  logic [42:0] x_m0;
  logic [42:0] xa_m0;
  logic [42:0] xb_m0;
  logic dena_m0;
  logic denb_m0;
  logic [31:0] y_m1_m1_l0_adder;
  logic [19:0] fl_m1_m1_l0_adder;
  logic [31:0] y_m1_m1_l0_multiplier;
  logic [19:0] fl_m1_m1_l0_multiplier;
  logic [31:0] y_m1_m1_l0_comparator;
  logic [19:0] fl_m1_m1_l0_comparator;
  logic [31:0] y_m1_m1_l0_converter_int8_twos_complement;
  logic [19:0] fl_m1_m1_l0_converter_int8_twos_complement;
  logic [31:0] y_m1_m1_l0_converter_fp16;
  logic [19:0] fl_m1_m1_l0_converter_fp16;
  logic [31:0] y_m1_m1_l0_converter_fxs1i7f8;
  logic [19:0] fl_m1_m1_l0_converter_fxs1i7f8;
  logic [31:0] y_m1;
  logic [19:0] fl_m1;
  logic [31:0] y_m2_m2_l0_adder;
  logic [19:0] fl_m2_m2_l0_adder;
  logic [31:0] y_m2_m2_l1_adder;
  logic [19:0] fl_m2_m2_l1_adder;
  logic [31:0] y_m2_m2_l0_multiplier;
  logic [19:0] fl_m2_m2_l0_multiplier;
  logic [31:0] y_m2_m2_l1_multiplier;
  logic [19:0] fl_m2_m2_l1_multiplier;
  logic [31:0] y_m2_m2_l0_comparator;
  logic [19:0] fl_m2_m2_l0_comparator;
  logic [31:0] y_m2_m2_l1_comparator;
  logic [19:0] fl_m2_m2_l1_comparator;
  logic [31:0] y_m2_m2_l0_converter_int8_twos_complement;
  logic [19:0] fl_m2_m2_l0_converter_int8_twos_complement;
  logic [31:0] y_m2_m2_l1_converter_int8_twos_complement;
  logic [19:0] fl_m2_m2_l1_converter_int8_twos_complement;
  logic [31:0] y_m2_m2_l0_converter_fp16;
  logic [19:0] fl_m2_m2_l0_converter_fp16;
  logic [31:0] y_m2_m2_l1_converter_fp16;
  logic [19:0] fl_m2_m2_l1_converter_fp16;
  logic [31:0] y_m2_m2_l0_converter_fxs1i7f8;
  logic [19:0] fl_m2_m2_l0_converter_fxs1i7f8;
  logic [31:0] y_m2_m2_l1_converter_fxs1i7f8;
  logic [19:0] fl_m2_m2_l1_converter_fxs1i7f8;
  logic [31:0] y_m2;
  logic [19:0] fl_m2;
  logic [31:0] y_m3_m3_l0_adder;
  logic [19:0] fl_m3_m3_l0_adder;
  logic [31:0] y_m3_m3_l0_multiplier;
  logic [19:0] fl_m3_m3_l0_multiplier;
  logic [31:0] y_m3_m3_l0_comparator;
  logic [19:0] fl_m3_m3_l0_comparator;
  logic [31:0] y_m3_m3_l0_converter_int8_twos_complement;
  logic [19:0] fl_m3_m3_l0_converter_int8_twos_complement;
  logic [31:0] y_m3_m3_l0_converter_fp16;
  logic [19:0] fl_m3_m3_l0_converter_fp16;
  logic [31:0] y_m3_m3_l0_converter_fxs1i7f8;
  logic [19:0] fl_m3_m3_l0_converter_fxs1i7f8;
  logic [31:0] y_m3;
  logic [19:0] fl_m3;
  logic [19:0] fl_all;
  assign rnd_sel = 3'd0;
  assign rnd = rnd_sel;
  assign daz = 1'b0;
  assign ftz = 1'b0;
  assign dual = 1'b0;
  assign y_m0 = y_m0_m0_l0_fp_adder | y_m0_m0_l0_rounder | y_m0_m0_l0_fp_multiplier | y_m0_m0_l0_converter_int8_twos_complement | y_m0_m0_l0_converter_fp16 | y_m0_m0_l0_converter_fxs1i7f8;
  assign fl_m0 = fl_m0_m0_l0_fp_adder | fl_m0_m0_l0_rounder | fl_m0_m0_l0_fp_multiplier | fl_m0_m0_l0_converter_int8_twos_complement | fl_m0_m0_l0_converter_fp16 | fl_m0_m0_l0_converter_fxs1i7f8;
  assign x_m0 = x_m0_m0_m0_l0_fp_adder | x_m0_m0_m0_l0_fp_multiplier | x_m0_m0_m0_l0_converter_int8_twos_complement | x_m0_m0_m0_l0_converter_fp16 | x_m0_m0_m0_l0_converter_fxs1i7f8;
  assign xa_m0 = xa_m0_m0_m0_l0_unpacker;
  assign xb_m0 = xb_m0_m0_m0_l0_unpacker;
  assign dena_m0 = dena_m0_m0_m0_l0_unpacker;
  assign denb_m0 = denb_m0_m0_m0_l0_unpacker;
  assign y_m1 = y_m1_m1_l0_adder | y_m1_m1_l0_multiplier | y_m1_m1_l0_comparator | y_m1_m1_l0_converter_int8_twos_complement | y_m1_m1_l0_converter_fp16 | y_m1_m1_l0_converter_fxs1i7f8;
  assign fl_m1 = fl_m1_m1_l0_adder | fl_m1_m1_l0_multiplier | fl_m1_m1_l0_comparator | fl_m1_m1_l0_converter_int8_twos_complement | fl_m1_m1_l0_converter_fp16 | fl_m1_m1_l0_converter_fxs1i7f8;
  assign y_m2 = y_m2_m2_l0_adder | y_m2_m2_l1_adder | y_m2_m2_l0_multiplier | y_m2_m2_l1_multiplier | y_m2_m2_l0_comparator | y_m2_m2_l1_comparator | y_m2_m2_l0_converter_int8_twos_complement | y_m2_m2_l1_converter_int8_twos_complement | y_m2_m2_l0_converter_fp16 | y_m2_m2_l1_converter_fp16 | y_m2_m2_l0_converter_fxs1i7f8 | y_m2_m2_l1_converter_fxs1i7f8;
  assign fl_m2 = fl_m2_m2_l0_adder | fl_m2_m2_l1_adder | fl_m2_m2_l0_multiplier | fl_m2_m2_l1_multiplier | fl_m2_m2_l0_comparator | fl_m2_m2_l1_comparator | fl_m2_m2_l0_converter_int8_twos_complement | fl_m2_m2_l1_converter_int8_twos_complement | fl_m2_m2_l0_converter_fp16 | fl_m2_m2_l1_converter_fp16 | fl_m2_m2_l0_converter_fxs1i7f8 | fl_m2_m2_l1_converter_fxs1i7f8;
  assign y_m3 = y_m3_m3_l0_adder | y_m3_m3_l0_multiplier | y_m3_m3_l0_comparator | y_m3_m3_l0_converter_int8_twos_complement | y_m3_m3_l0_converter_fp16 | y_m3_m3_l0_converter_fxs1i7f8;
  assign fl_m3 = fl_m3_m3_l0_adder | fl_m3_m3_l0_multiplier | fl_m3_m3_l0_comparator | fl_m3_m3_l0_converter_int8_twos_complement | fl_m3_m3_l0_converter_fp16 | fl_m3_m3_l0_converter_fxs1i7f8;
  alu_core_u_m0_l0_fp_adder u_m0_l0_fp_adder (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_m0_l0_fp_adder), .fl_m0(fl_m0_m0_l0_fp_adder), .xa_m0(xa_m0), .xb_m0(xb_m0), .dena_m0(dena_m0), .denb_m0(denb_m0), .x_m0(x_m0_m0_m0_l0_fp_adder));
  alu_core_u_m0_l0_unpacker u_m0_l0_unpacker (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .xa_m0(xa_m0_m0_m0_l0_unpacker), .xb_m0(xb_m0_m0_m0_l0_unpacker), .dena_m0(dena_m0_m0_m0_l0_unpacker), .denb_m0(denb_m0_m0_m0_l0_unpacker));
  alu_core_u_m0_l0_rounder u_m0_l0_rounder (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_m0_l0_rounder), .fl_m0(fl_m0_m0_l0_rounder), .xa_m0(xa_m0), .xb_m0(xb_m0), .dena_m0(dena_m0), .denb_m0(denb_m0), .x_m0(x_m0));
  alu_core_u_m0_l0_fp_multiplier u_m0_l0_fp_multiplier (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_m0_l0_fp_multiplier), .fl_m0(fl_m0_m0_l0_fp_multiplier), .xa_m0(xa_m0), .xb_m0(xb_m0), .dena_m0(dena_m0), .denb_m0(denb_m0), .x_m0(x_m0_m0_m0_l0_fp_multiplier));
  alu_core_u_m0_l0_converter_int8_twos_complement u_m0_l0_converter_int8_twos_complement (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_m0_l0_converter_int8_twos_complement), .fl_m0(fl_m0_m0_l0_converter_int8_twos_complement), .xa_m0(xa_m0), .xb_m0(xb_m0), .dena_m0(dena_m0), .denb_m0(denb_m0), .x_m0(x_m0_m0_m0_l0_converter_int8_twos_complement));
  alu_core_u_m0_l0_converter_fp16 u_m0_l0_converter_fp16 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_m0_l0_converter_fp16), .fl_m0(fl_m0_m0_l0_converter_fp16), .xa_m0(xa_m0), .xb_m0(xb_m0), .dena_m0(dena_m0), .denb_m0(denb_m0), .x_m0(x_m0_m0_m0_l0_converter_fp16));
  alu_core_u_m0_l0_converter_fxs1i7f8 u_m0_l0_converter_fxs1i7f8 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_m0_l0_converter_fxs1i7f8), .fl_m0(fl_m0_m0_l0_converter_fxs1i7f8), .xa_m0(xa_m0), .xb_m0(xb_m0), .dena_m0(dena_m0), .denb_m0(denb_m0), .x_m0(x_m0_m0_m0_l0_converter_fxs1i7f8));
  alu_core_u_m1_l0_adder u_m1_l0_adder (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l0_adder), .fl_m1(fl_m1_m1_l0_adder));
  alu_core_u_m1_l0_multiplier u_m1_l0_multiplier (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l0_multiplier), .fl_m1(fl_m1_m1_l0_multiplier));
  alu_core_u_m1_l0_comparator u_m1_l0_comparator (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l0_comparator), .fl_m1(fl_m1_m1_l0_comparator));
  alu_core_u_m1_l0_converter_int8_twos_complement u_m1_l0_converter_int8_twos_complement (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l0_converter_int8_twos_complement), .fl_m1(fl_m1_m1_l0_converter_int8_twos_complement));
  alu_core_u_m1_l0_converter_fp16 u_m1_l0_converter_fp16 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l0_converter_fp16), .fl_m1(fl_m1_m1_l0_converter_fp16));
  alu_core_u_m1_l0_converter_fxs1i7f8 u_m1_l0_converter_fxs1i7f8 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l0_converter_fxs1i7f8), .fl_m1(fl_m1_m1_l0_converter_fxs1i7f8));
  alu_core_u_m2_l0_adder u_m2_l0_adder (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_m2_l0_adder), .fl_m2(fl_m2_m2_l0_adder));
  alu_core_u_m2_l1_adder u_m2_l1_adder (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_m2_l1_adder), .fl_m2(fl_m2_m2_l1_adder));
  alu_core_u_m2_l0_multiplier u_m2_l0_multiplier (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_m2_l0_multiplier), .fl_m2(fl_m2_m2_l0_multiplier));
  alu_core_u_m2_l1_multiplier u_m2_l1_multiplier (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_m2_l1_multiplier), .fl_m2(fl_m2_m2_l1_multiplier));
  alu_core_u_m2_l0_comparator u_m2_l0_comparator (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_m2_l0_comparator), .fl_m2(fl_m2_m2_l0_comparator));
  alu_core_u_m2_l1_comparator u_m2_l1_comparator (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_m2_l1_comparator), .fl_m2(fl_m2_m2_l1_comparator));
  alu_core_u_m2_l0_converter_int8_twos_complement u_m2_l0_converter_int8_twos_complement (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_m2_l0_converter_int8_twos_complement), .fl_m2(fl_m2_m2_l0_converter_int8_twos_complement));
  alu_core_u_m2_l1_converter_int8_twos_complement u_m2_l1_converter_int8_twos_complement (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_m2_l1_converter_int8_twos_complement), .fl_m2(fl_m2_m2_l1_converter_int8_twos_complement));
  alu_core_u_m2_l0_converter_fp16 u_m2_l0_converter_fp16 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_m2_l0_converter_fp16), .fl_m2(fl_m2_m2_l0_converter_fp16));
  alu_core_u_m2_l1_converter_fp16 u_m2_l1_converter_fp16 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_m2_l1_converter_fp16), .fl_m2(fl_m2_m2_l1_converter_fp16));
  alu_core_u_m2_l0_converter_fxs1i7f8 u_m2_l0_converter_fxs1i7f8 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_m2_l0_converter_fxs1i7f8), .fl_m2(fl_m2_m2_l0_converter_fxs1i7f8));
  alu_core_u_m2_l1_converter_fxs1i7f8 u_m2_l1_converter_fxs1i7f8 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_m2_l1_converter_fxs1i7f8), .fl_m2(fl_m2_m2_l1_converter_fxs1i7f8));
  alu_core_u_m3_l0_adder u_m3_l0_adder (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m3(y_m3_m3_l0_adder), .fl_m3(fl_m3_m3_l0_adder));
  alu_core_u_m3_l0_multiplier u_m3_l0_multiplier (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m3(y_m3_m3_l0_multiplier), .fl_m3(fl_m3_m3_l0_multiplier));
  alu_core_u_m3_l0_comparator u_m3_l0_comparator (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m3(y_m3_m3_l0_comparator), .fl_m3(fl_m3_m3_l0_comparator));
  alu_core_u_m3_l0_converter_int8_twos_complement u_m3_l0_converter_int8_twos_complement (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m3(y_m3_m3_l0_converter_int8_twos_complement), .fl_m3(fl_m3_m3_l0_converter_int8_twos_complement));
  alu_core_u_m3_l0_converter_fp16 u_m3_l0_converter_fp16 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m3(y_m3_m3_l0_converter_fp16), .fl_m3(fl_m3_m3_l0_converter_fp16));
  alu_core_u_m3_l0_converter_fxs1i7f8 u_m3_l0_converter_fxs1i7f8 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m3(y_m3_m3_l0_converter_fxs1i7f8), .fl_m3(fl_m3_m3_l0_converter_fxs1i7f8));
  always_comb begin
    case (mode)
      2'd0: begin y = y_m0; fl_all = fl_m0; end
      2'd1: begin y = y_m1; fl_all = fl_m1; end
      2'd2: begin y = y_m2; fl_all = fl_m2; end
      2'd3: begin y = y_m3; fl_all = fl_m3; end
      default: begin y = '0; fl_all = '0; end
    endcase
  end
endmodule
// EVOLVE-BLOCK-END

module alu_core_m0_converter #(parameter int LANE = 0, parameter int TGT = -1) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m0,
  output logic [19:0] fl_m0,
  input  logic [42:0] xa_m0,
  input  logic [42:0] xb_m0,
  input  logic [0:0] dena_m0,
  input  logic [0:0] denb_m0,
  output logic [42:0] x_m0
);
  // alu_core_m0_converter: lane LANE of mode 0 (fp16) for the converter ops cvt(int8), cvt(fp16), cvt(fxs1i7f8); the result buses are the mode's, with only this lane's bits written
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
    y_m0 = '0; d_m0 = '0; fl_m0 = '0;
    x_m0 = '0;
    case (op)
      3'd5: begin
        if (TGT == -1 || TGT == 5) begin
          x_m0[LANE*43 +: 43] = m0_xa[LANE];
        end
      end
      3'd6: begin
        if (TGT == -1 || TGT == 6) begin
          x_m0[LANE*43 +: 43] = m0_xa[LANE];
        end
      end
      3'd7: begin
        if (TGT == -1 || TGT == 7) begin
          x_m0[LANE*43 +: 43] = m0_xa[LANE];
        end
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m0_fp_adder #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m0,
  output logic [19:0] fl_m0,
  input  logic [42:0] xa_m0,
  input  logic [42:0] xb_m0,
  input  logic [0:0] dena_m0,
  input  logic [0:0] denb_m0,
  output logic [42:0] x_m0
);
  // alu_core_m0_fp_adder: lane LANE of mode 0 (fp16) for the fp_adder ops fadd; the result buses are the mode's, with only this lane's bits written
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
  logic [25:0] m0_o3t0_LANE;
  logic [42:0] m0_o3t0_LANE_x;
  logic [42:0] m0_o3t0_LANE_z;
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
    m0_fa_xaLANE = 'x; m0_fa_xbLANE = 'x; m0_fa_subLANE = 'x; m0_o3t0_LANE = 'x; m0_o3t0_LANE_x = 'x; m0_o3t0_LANE_z = 'x;
    x_m0 = '0;
    case (op)
      3'd3: begin
        m0_fa_xaLANE = m0_xa[LANE]; m0_fa_xbLANE = m0_xb[LANE]; m0_fa_subLANE = 1'b0; m0_o3t0_LANE_x = m0_fa_yLANE;
        m0_o3t0_LANE_z = { m0_o3t0_LANE_x[42:41], (m0_o3t0_LANE_x[42:41] == 2'd0 && m0_o3t0_LANE_x[26:0] == 0) ? (((m0_xa[LANE][42:41] == 2'd0 && m0_xa[LANE][26:0] == 0) && (m0_xb[LANE][42:41] == 2'd0 && m0_xb[LANE][26:0] == 0)) ? ((rnd == 3'd2) ? (m0_aLANE[15] | (m0_bLANE[15] ^ 1'b0)) : (m0_aLANE[15] & (m0_bLANE[15] ^ 1'b0))) : ((rnd == 3'd2) ? 1'b1 : 1'b0)) : m0_o3t0_LANE_x[40], m0_o3t0_LANE_x[39:0] };
        x_m0[LANE*43 +: 43] = m0_o3t0_LANE_z;
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m0_fp_multiplier #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m0,
  output logic [19:0] fl_m0,
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
  logic [25:0] m0_o4t0_LANE;
  logic [42:0] m0_o4t0_LANE_x;
  logic [42:0] m0_o4t0_LANE_z;
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
    m0_fm_xaLANE = 'x; m0_fm_xbLANE = 'x; m0_o4t0_LANE = 'x; m0_o4t0_LANE_x = 'x; m0_o4t0_LANE_z = 'x;
    x_m0 = '0;
    case (op)
      3'd4: begin
        m0_fm_xaLANE = m0_xa[LANE]; m0_fm_xbLANE = m0_xb[LANE]; m0_o4t0_LANE_x = m0_fm_yLANE;
        m0_o4t0_LANE_z = { m0_o4t0_LANE_x[42:41], (m0_o4t0_LANE_x[42:41] == 2'd0 && m0_o4t0_LANE_x[26:0] == 0) ? (m0_aLANE[15] ^ m0_bLANE[15]) : m0_o4t0_LANE_x[40], m0_o4t0_LANE_x[39:0] };
        x_m0[LANE*43 +: 43] = m0_o4t0_LANE_z;
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m0_rounder #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m0,
  output logic [19:0] fl_m0,
  input  logic [42:0] xa_m0,
  input  logic [42:0] xb_m0,
  input  logic [0:0] dena_m0,
  input  logic [0:0] denb_m0,
  input  logic [42:0] x_m0
);
  // alu_core_m0_rounder: lane LANE of mode 0 (fp16) for the rounder ops fadd, fmul, cvt(int8), cvt(fp16), cvt(fxs1i7f8); the result buses are the mode's, with only this lane's bits written
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
  logic [42:0] m0_cv_xLANE_fp16;
  logic [7:0] m0_cv_wLANE_fp16;
  logic [9:0] m0_cv_flLANE_fp16;
  logic [15:0] m0_cv_bLANE_fp16;
  logic [42:0] m0_cv_xLANE_int8_twos_complement;
  logic [7:0] m0_cv_wLANE_int8_twos_complement;
  logic [9:0] m0_cv_flLANE_int8_twos_complement;
  logic [7:0] m0_cv_bLANE_int8_twos_complement;
  logic [42:0] m0_cv_xLANE_fxs1i7f8;
  logic [7:0] m0_cv_wLANE_fxs1i7f8;
  logic [9:0] m0_cv_flLANE_fxs1i7f8;
  logic [15:0] m0_cv_bLANE_fxs1i7f8;
  logic [25:0] m0_o3t0_LANE;
  logic [42:0] m0_o3t0_LANE_x;
  logic [42:0] m0_o3t0_LANE_z;
  logic [25:0] m0_o4t0_LANE;
  logic [42:0] m0_o4t0_LANE_x;
  logic [42:0] m0_o4t0_LANE_z;
  logic [42:0] m0_o5x0_LANE_0;
  logic [17:0] m0_o5c0_LANE_0;
  logic [42:0] m0_o6x0_LANE_0;
  logic [25:0] m0_o6c0_LANE_0;
  logic [42:0] m0_o7x0_LANE_0;
  logic [25:0] m0_o7c0_LANE_0;
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
  // structure core.converter.m0.fp16: family shift_round_convert realized by the library module fam_fp_round_shift_round_convert_increment_adder_fp16_x26e13s11_pd77ccc5b5c45
  fam_fp_round_shift_round_convert_increment_adder_fp16_x26e13s11_pd77ccc5b5c45 u_m0_cvtLANE_fp16 (.x(m0_cv_xLANE_fp16), .rnd(rnd), .word(m0_cv_wLANE_fp16), .ftz(ftz), .fl(m0_cv_flLANE_fp16), .bits(m0_cv_bLANE_fp16));
  // structure core.converter.m0.int8_twos_complement: family shift_round_convert realized by the library module fam_int_round_int8_twos_complement_x26e13s11_pd77ccc5b5c45
  fam_int_round_int8_twos_complement_x26e13s11_pd77ccc5b5c45 u_m0_cvtLANE_int8_twos_complement (.x(m0_cv_xLANE_int8_twos_complement), .rnd(rnd), .word(m0_cv_wLANE_int8_twos_complement), .ftz(ftz), .fl(m0_cv_flLANE_int8_twos_complement), .bits(m0_cv_bLANE_int8_twos_complement));
  // structure core.converter.m0.fxs1i7f8: family shift_round_convert realized by the library module fam_int_round_fxs1i7f8_x26e13s11_pd77ccc5b5c45
  fam_int_round_fxs1i7f8_x26e13s11_pd77ccc5b5c45 u_m0_cvtLANE_fxs1i7f8 (.x(m0_cv_xLANE_fxs1i7f8), .rnd(rnd), .word(m0_cv_wLANE_fxs1i7f8), .ftz(ftz), .fl(m0_cv_flLANE_fxs1i7f8), .bits(m0_cv_bLANE_fxs1i7f8));
  always_comb begin
    y_m0 = '0; d_m0 = '0; fl_m0 = '0;
    m0_rd_xLANE_fadd = 'x; m0_rd_wLANE_fadd = 'x; m0_rd_xLANE_fmul = 'x; m0_rd_wLANE_fmul = 'x; m0_cv_xLANE_fp16 = 'x; m0_cv_wLANE_fp16 = 'x;
    m0_cv_xLANE_int8_twos_complement = 'x; m0_cv_wLANE_int8_twos_complement = 'x; m0_cv_xLANE_fxs1i7f8 = 'x; m0_cv_wLANE_fxs1i7f8 = 'x; m0_o3t0_LANE = 'x; m0_o3t0_LANE_x = 'x;
    m0_o3t0_LANE_z = 'x; m0_o4t0_LANE = 'x; m0_o4t0_LANE_x = 'x; m0_o4t0_LANE_z = 'x; m0_o5x0_LANE_0 = 'x; m0_o5c0_LANE_0 = 'x;
    m0_o6x0_LANE_0 = 'x; m0_o6c0_LANE_0 = 'x; m0_o7x0_LANE_0 = 'x; m0_o7c0_LANE_0 = 'x;
    case (op)
      3'd3: begin
        m0_o3t0_LANE_z = x_m0[LANE*43 +: 43];
        m0_rd_xLANE_fadd = m0_o3t0_LANE_z; m0_rd_wLANE_fadd = 8'd0; m0_o3t0_LANE = {m0_rd_flLANE_fadd, m0_rd_bLANE_fadd};
        y_m0[((LANE*16)+0) +: 16] = (m0_o3t0_LANE_z[42:41] == 2'd1) ? (((m0_xa[LANE][42:41] == 2'd1) || (m0_xb[LANE][42:41] == 2'd1)) ? 16'd32256 : 16'd32256) : ((m0_o3t0_LANE_z[42:41] == 2'd0 && m0_o3t0_LANE_z[26:0] == 0) ? {m0_o3t0_LANE_z[40], 15'd0} : m0_o3t0_LANE[15:0]);
        fl_m0[(0+LANE)*10 +: 10] = (((m0_xa[LANE][42:41] == 2'd1) || (m0_xb[LANE][42:41] == 2'd1)) ? (((10'd1 << 5) | (((m0_xa[LANE][42:41] == 2'd1) && !m0_aLANE[9]) || ((m0_xb[LANE][42:41] == 2'd1) && !m0_bLANE[9]) ? (10'd1 << 0) : 10'd0)) | (m0_dena[LANE] | m0_denb[LANE] ? (10'd1 << 6) : 10'd0)) : (m0_o3t0_LANE[25:16] | ((((m0_xa[LANE][42:41] == 2'd1) && !m0_aLANE[9]) || ((m0_xb[LANE][42:41] == 2'd1) && !m0_bLANE[9]) || ((m0_o3t0_LANE_z[42:41] == 2'd1) && !((m0_xa[LANE][42:41] == 2'd1) || (m0_xb[LANE][42:41] == 2'd1)))) ? (10'd1 << 0) : 10'd0) | (m0_dena[LANE] | m0_denb[LANE] ? (10'd1 << 6) : 10'd0)));
      end
      3'd4: begin
        m0_o4t0_LANE_z = x_m0[LANE*43 +: 43];
        m0_rd_xLANE_fmul = m0_o4t0_LANE_z; m0_rd_wLANE_fmul = 8'd0; m0_o4t0_LANE = {m0_rd_flLANE_fmul, m0_rd_bLANE_fmul};
        y_m0[((LANE*16)+0) +: 16] = (m0_o4t0_LANE_z[42:41] == 2'd1) ? (((m0_xa[LANE][42:41] == 2'd1) || (m0_xb[LANE][42:41] == 2'd1)) ? 16'd32256 : 16'd32256) : ((m0_o4t0_LANE_z[42:41] == 2'd0 && m0_o4t0_LANE_z[26:0] == 0) ? {m0_o4t0_LANE_z[40], 15'd0} : m0_o4t0_LANE[15:0]);
        fl_m0[(0+LANE)*10 +: 10] = (((m0_xa[LANE][42:41] == 2'd1) || (m0_xb[LANE][42:41] == 2'd1)) ? (((10'd1 << 5) | (((m0_xa[LANE][42:41] == 2'd1) && !m0_aLANE[9]) || ((m0_xb[LANE][42:41] == 2'd1) && !m0_bLANE[9]) ? (10'd1 << 0) : 10'd0)) | (m0_dena[LANE] | m0_denb[LANE] ? (10'd1 << 6) : 10'd0)) : (m0_o4t0_LANE[25:16] | ((((m0_xa[LANE][42:41] == 2'd1) && !m0_aLANE[9]) || ((m0_xb[LANE][42:41] == 2'd1) && !m0_bLANE[9]) || ((m0_o4t0_LANE_z[42:41] == 2'd1) && !((m0_xa[LANE][42:41] == 2'd1) || (m0_xb[LANE][42:41] == 2'd1)))) ? (10'd1 << 0) : 10'd0) | (m0_dena[LANE] | m0_denb[LANE] ? (10'd1 << 6) : 10'd0)));
      end
      3'd5: begin
        m0_o5x0_LANE_0 = x_m0[LANE*43 +: 43];
        m0_cv_xLANE_int8_twos_complement = m0_o5x0_LANE_0; m0_cv_wLANE_int8_twos_complement = 8'd0; m0_o5c0_LANE_0 = {m0_cv_flLANE_int8_twos_complement, m0_cv_bLANE_int8_twos_complement};
        y_m0[((LANE*8)+0) +: 8] = m0_o5c0_LANE_0[7:0];
        fl_m0[(0+LANE)*10 +: 10] = m0_o5c0_LANE_0[17:8] | (m0_dena[LANE] ? (10'd1 << 6) : 10'd0);
      end
      3'd6: begin
        m0_o6x0_LANE_0 = x_m0[LANE*43 +: 43];
        m0_cv_xLANE_fp16 = m0_o6x0_LANE_0; m0_cv_wLANE_fp16 = 8'd0; m0_o6c0_LANE_0 = {m0_cv_flLANE_fp16, m0_cv_bLANE_fp16};
        y_m0[((LANE*16)+0) +: 16] = ((m0_o6x0_LANE_0[42:41] == 2'd0 && m0_o6x0_LANE_0[26:0] == 0) ? {m0_o6x0_LANE_0[40], 15'd0} : m0_o6c0_LANE_0[15:0]);
        fl_m0[(0+LANE)*10 +: 10] = m0_o6c0_LANE_0[25:16] | (((m0_o6x0_LANE_0[42:41] == 2'd1) && !m0_aLANE[9]) ? (10'd1 << 0) : 10'd0) | (m0_dena[LANE] ? (10'd1 << 6) : 10'd0);
      end
      3'd7: begin
        m0_o7x0_LANE_0 = x_m0[LANE*43 +: 43];
        m0_cv_xLANE_fxs1i7f8 = m0_o7x0_LANE_0; m0_cv_wLANE_fxs1i7f8 = 8'd0; m0_o7c0_LANE_0 = {m0_cv_flLANE_fxs1i7f8, m0_cv_bLANE_fxs1i7f8};
        y_m0[((LANE*16)+0) +: 16] = m0_o7c0_LANE_0[15:0];
        fl_m0[(0+LANE)*10 +: 10] = m0_o7c0_LANE_0[25:16] | (m0_dena[LANE] ? (10'd1 << 6) : 10'd0);
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m0_unpacker #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [1:0] mode,
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
  logic [31:0] y_m0;
  logic d_m0;
  logic [19:0] fl_m0;
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

module alu_core_m1_adder_sh #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m1,
  output logic [19:0] fl_m1,
  output logic [15:0] pc_a_m1,
  output logic [15:0] pc_b_m1,
  output logic [0:0] pc_cin_m1,
  input  logic [15:0] pc_s_m1,
  input  logic [0:0] pc_co_m1
);
  // alu_core_m1_adder_sh: lane LANE of mode 1 (int16_twos_complement) for the adder ops add; the result buses are the mode's, with only this lane's bits written; the unit's shared adder serve this lane through the pc_/tp_ buses
  import alu_core_m1_pkg::*;
  logic d_m1;
  logic [15:0] m1_aLANE;
  logic [15:0] m1_bLANE;
  logic [54:0] m1_xa [0:0];
  logic [54:0] m1_xb [0:0];
  logic signed [16:0] m1_vaLANE;
  logic signed [16:0] m1_vbLANE;
  logic [15:0] m1_add_sLANE;
  logic m1_add_coutLANE;
  logic signed [34:0] m1_o0ex0_LANE;
  assign m1_aLANE = a[(LANE*16) +: 16];
  assign m1_bLANE = b[(LANE*16) +: 16];
  assign m1_xa[LANE] = m1_x(m1_unpack_s(m1_aLANE, 1'b0));
  assign m1_xb[LANE] = m1_x(m1_unpack_s(m1_bLANE, 1'b0));
  assign m1_vaLANE = {m1_aLANE[15], m1_aLANE};
  assign m1_vbLANE = {m1_bLANE[15], m1_bLANE};
  // structure core.adder.m1: the unit's shared partitioned adder (subword partitioned_carry_chain)
  assign m1_add_sLANE = pc_s_m1[(LANE)*16 +: 16];
  assign m1_add_coutLANE = pc_co_m1[(LANE+1)*1-1];
  always_comb begin
    y_m1 = '0; d_m1 = '0; fl_m1 = '0;
    m1_o0ex0_LANE = 'x;
    pc_a_m1 = '0; pc_b_m1 = '0; pc_cin_m1 = '0;
    case (op)
      3'd0: begin
        pc_a_m1[(LANE)*16 +: 16] = m1_aLANE; pc_b_m1[(LANE)*16 +: 16] = m1_bLANE; pc_cin_m1[(LANE)*1] = 1'b0;
        m1_o0ex0_LANE = $signed({(m1_aLANE[15] ^ m1_bLANE[15] ^ m1_add_coutLANE), m1_add_sLANE});
        y_m1[((LANE*16)+0) +: 16] = m1_wrap(m1_o0ex0_LANE);
        fl_m1[(0+LANE)*10 +: 10] = (((m1_aLANE[15] ^ m1_bLANE[15] ^ m1_add_coutLANE) ^ m1_add_sLANE[15]) ? (10'd1 << 8) : 10'd0) | (((m1_aLANE[15] ^ m1_bLANE[15] ^ m1_add_coutLANE) ^ m1_add_sLANE[15]) ? (10'd1 << 2) : 10'd0) | (m1_add_coutLANE ? (10'd1 << 7) : 10'd0);
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m1_comparator #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m1,
  output logic [19:0] fl_m1
);
  // alu_core_m1_comparator: lane LANE of mode 1 (int16_twos_complement) for the comparator ops min; the result buses are the mode's, with only this lane's bits written
  import alu_core_m1_pkg::*;
  logic d_m1;
  logic [15:0] m1_aLANE;
  logic [15:0] m1_bLANE;
  logic [54:0] m1_xa [0:0];
  logic [54:0] m1_xb [0:0];
  logic signed [16:0] m1_vaLANE;
  logic signed [16:0] m1_vbLANE;
  logic [15:0] m1_cmp_aLANE;
  logic [15:0] m1_cmp_bLANE;
  logic m1_cmp_ltLANE;
  logic m1_cmp_eqLANE;
  logic signed [34:0] m1_o2ex0_LANE;
  assign m1_aLANE = a[(LANE*16) +: 16];
  assign m1_bLANE = b[(LANE*16) +: 16];
  assign m1_xa[LANE] = m1_x(m1_unpack_s(m1_aLANE, 1'b0));
  assign m1_xb[LANE] = m1_x(m1_unpack_s(m1_bLANE, 1'b0));
  assign m1_vaLANE = {m1_aLANE[15], m1_aLANE};
  assign m1_vbLANE = {m1_bLANE[15], m1_bLANE};
  // structure core.comparator.m1: family prefix_comparator realized by the library module fam_cmp_prefix_comparator
  fam_cmp_prefix_comparator #(.W(16), .SIGNED(1), .STRUCTURE(0), .RADIX(2)) u_m1_cmpLANE (.a(m1_cmp_aLANE), .b(m1_cmp_bLANE), .lt(m1_cmp_ltLANE), .eq(m1_cmp_eqLANE));
  always_comb begin
    y_m1 = '0; d_m1 = '0; fl_m1 = '0;
    m1_cmp_aLANE = 'x; m1_cmp_bLANE = 'x; m1_o2ex0_LANE = 'x;
    case (op)
      3'd2: begin
        m1_cmp_aLANE = m1_aLANE; m1_cmp_bLANE = m1_bLANE;
        y_m1[((LANE*16)+0) +: 16] = (m1_cmp_ltLANE | m1_cmp_eqLANE) ? m1_aLANE : m1_bLANE;
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m1_converter #(parameter int LANE = 0, parameter int TGT = -1) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m1,
  output logic [19:0] fl_m1
);
  // alu_core_m1_converter: lane LANE of mode 1 (int16_twos_complement) for the converter ops cvt(int8), cvt(fp16), cvt(fxs1i7f8); the result buses are the mode's, with only this lane's bits written
  import alu_core_m1_pkg::*;
  logic d_m1;
  logic [15:0] m1_aLANE;
  logic [15:0] m1_bLANE;
  logic [54:0] m1_xa [0:0];
  logic [54:0] m1_xb [0:0];
  logic signed [16:0] m1_vaLANE;
  logic signed [16:0] m1_vbLANE;
  logic [54:0] m1_cv_xLANE_fp16;
  logic [7:0] m1_cv_wordLANE_fp16;
  logic [9:0] m1_cv_flLANE_fp16;
  logic [15:0] m1_cv_bitsLANE_fp16;
  logic [54:0] m1_cv_xLANE_fxs1i7f8;
  logic [7:0] m1_cv_wordLANE_fxs1i7f8;
  logic [9:0] m1_cv_flLANE_fxs1i7f8;
  logic [15:0] m1_cv_bitsLANE_fxs1i7f8;
  logic [54:0] m1_cv_xLANE_int8_twos_complement;
  logic [7:0] m1_cv_wordLANE_int8_twos_complement;
  logic [9:0] m1_cv_flLANE_int8_twos_complement;
  logic [7:0] m1_cv_bitsLANE_int8_twos_complement;
  logic [17:0] m1_o5c0_LANE;
  logic [25:0] m1_o6c0_LANE;
  logic [25:0] m1_o7c0_LANE;
  assign m1_aLANE = a[(LANE*16) +: 16];
  assign m1_bLANE = b[(LANE*16) +: 16];
  assign m1_xa[LANE] = m1_x(m1_unpack_s(m1_aLANE, 1'b0));
  assign m1_xb[LANE] = m1_x(m1_unpack_s(m1_bLANE, 1'b0));
  assign m1_vaLANE = {m1_aLANE[15], m1_aLANE};
  assign m1_vbLANE = {m1_bLANE[15], m1_bLANE};
  // structure core.converter.m1.fp16: family shift_round_convert
  fam_int_cvt_shift_round_convert_fp16_x38e13s17 u_m1_cvtLANE_fp16 (.x(m1_cv_xLANE_fp16), .rnd(rnd), .word(m1_cv_wordLANE_fp16), .ftz(ftz), .fl(m1_cv_flLANE_fp16), .bits(m1_cv_bitsLANE_fp16));
  // structure core.converter.m1.fxs1i7f8: family shift_round_convert
  fam_int_cvt_shift_round_convert_fxs1i7f8_x38e13s17 u_m1_cvtLANE_fxs1i7f8 (.x(m1_cv_xLANE_fxs1i7f8), .rnd(rnd), .word(m1_cv_wordLANE_fxs1i7f8), .ftz(ftz), .fl(m1_cv_flLANE_fxs1i7f8), .bits(m1_cv_bitsLANE_fxs1i7f8));
  // structure core.converter.m1.int8_twos_complement: family shift_round_convert
  fam_int_cvt_shift_round_convert_int8_twos_complement_x38e13s17 u_m1_cvtLANE_int8_twos_complement (.x(m1_cv_xLANE_int8_twos_complement), .rnd(rnd), .word(m1_cv_wordLANE_int8_twos_complement), .ftz(ftz), .fl(m1_cv_flLANE_int8_twos_complement), .bits(m1_cv_bitsLANE_int8_twos_complement));
  always_comb begin
    y_m1 = '0; d_m1 = '0; fl_m1 = '0;
    m1_cv_xLANE_fp16 = 'x; m1_cv_wordLANE_fp16 = 'x; m1_cv_xLANE_fxs1i7f8 = 'x; m1_cv_wordLANE_fxs1i7f8 = 'x; m1_cv_xLANE_int8_twos_complement = 'x; m1_cv_wordLANE_int8_twos_complement = 'x;
    m1_o5c0_LANE = 'x; m1_o6c0_LANE = 'x; m1_o7c0_LANE = 'x;
    case (op)
      3'd5: begin
        if (TGT == -1 || TGT == 5) begin
          m1_cv_xLANE_int8_twos_complement = m1_xa[LANE]; m1_cv_wordLANE_int8_twos_complement = 8'd0; m1_o5c0_LANE = {m1_cv_flLANE_int8_twos_complement, m1_cv_bitsLANE_int8_twos_complement};
          y_m1[((LANE*8)+0) +: 8] = m1_o5c0_LANE[7:0];
          fl_m1[(0+LANE)*10 +: 10] = m1_o5c0_LANE[17:8];
        end
      end
      3'd6: begin
        if (TGT == -1 || TGT == 6) begin
          m1_cv_xLANE_fp16 = m1_xa[LANE]; m1_cv_wordLANE_fp16 = 8'd0; m1_o6c0_LANE = {m1_cv_flLANE_fp16, m1_cv_bitsLANE_fp16};
          y_m1[((LANE*16)+0) +: 16] = m1_o6c0_LANE[15:0];
          fl_m1[(0+LANE)*10 +: 10] = m1_o6c0_LANE[25:16];
        end
      end
      3'd7: begin
        if (TGT == -1 || TGT == 7) begin
          m1_cv_xLANE_fxs1i7f8 = m1_xa[LANE]; m1_cv_wordLANE_fxs1i7f8 = 8'd0; m1_o7c0_LANE = {m1_cv_flLANE_fxs1i7f8, m1_cv_bitsLANE_fxs1i7f8};
          y_m1[((LANE*16)+0) +: 16] = m1_o7c0_LANE[15:0];
          fl_m1[(0+LANE)*10 +: 10] = m1_o7c0_LANE[25:16];
        end
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m1_multiplier #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m1,
  output logic [19:0] fl_m1
);
  // alu_core_m1_multiplier: lane LANE of mode 1 (int16_twos_complement) for the multiplier ops mul; the result buses are the mode's, with only this lane's bits written
  import alu_core_m1_pkg::*;
  logic d_m1;
  logic [15:0] m1_aLANE;
  logic [15:0] m1_bLANE;
  logic [54:0] m1_xa [0:0];
  logic [54:0] m1_xb [0:0];
  logic signed [16:0] m1_vaLANE;
  logic signed [16:0] m1_vbLANE;
  logic [15:0] m1_mul_aLANE;
  logic [15:0] m1_mul_bLANE;
  logic [31:0] m1_mul_pLANE;
  logic signed [34:0] m1_o1ex0_LANE;
  assign m1_aLANE = a[(LANE*16) +: 16];
  assign m1_bLANE = b[(LANE*16) +: 16];
  assign m1_xa[LANE] = m1_x(m1_unpack_s(m1_aLANE, 1'b0));
  assign m1_xb[LANE] = m1_x(m1_unpack_s(m1_bLANE, 1'b0));
  assign m1_vaLANE = {m1_aLANE[15], m1_aLANE};
  assign m1_vbLANE = {m1_bLANE[15], m1_bLANE};
  // structure core.multiplier.m1: family behavioral_star realized by the library module fam_mul_behavioral_star_w16_s
  fam_mul_behavioral_star_w16_s u_m1_mulLANE (.a(m1_mul_aLANE), .b(m1_mul_bLANE), .p(m1_mul_pLANE));
  always_comb begin
    y_m1 = '0; d_m1 = '0; fl_m1 = '0;
    m1_mul_aLANE = 'x; m1_mul_bLANE = 'x; m1_o1ex0_LANE = 'x;
    case (op)
      3'd1: begin
        m1_mul_aLANE = m1_aLANE; m1_mul_bLANE = m1_bLANE;
        m1_o1ex0_LANE = $signed({{3{m1_mul_pLANE[31]}}, m1_mul_pLANE});
        y_m1[((LANE*16)+0) +: 16] = m1_wrap(m1_o1ex0_LANE);
        fl_m1[(0+LANE)*10 +: 10] = (m1_o1ex0_LANE > 35'sd32767 || m1_o1ex0_LANE < -35'sd32768 ? (10'd1 << 8) : 10'd0) | (m1_o1ex0_LANE > 35'sd32767 || m1_o1ex0_LANE < -35'sd32768 ? (10'd1 << 2) : 10'd0);
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m2_adder_sh #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m2,
  output logic [19:0] fl_m2,
  output logic [15:0] pc_a_m2,
  output logic [15:0] pc_b_m2,
  output logic [1:0] pc_cin_m2,
  input  logic [15:0] pc_s_m2,
  input  logic [1:0] pc_co_m2
);
  // alu_core_m2_adder_sh: lane LANE of mode 2 (int8_twos_complement) for the adder ops add; the result buses are the mode's, with only this lane's bits written; the unit's shared adder serve this lane through the pc_/tp_ buses
  import alu_core_m2_pkg::*;
  logic d_m2;
  logic [7:0] m2_aLANE;
  logic [7:0] m2_bLANE;
  logic [38:0] m2_xa [0:1];
  logic [38:0] m2_xb [0:1];
  logic signed [8:0] m2_vaLANE;
  logic signed [8:0] m2_vbLANE;
  logic [7:0] m2_add_sLANE;
  logic m2_add_coutLANE;
  logic signed [18:0] m2_o0ex0_LANE;
  assign m2_aLANE = a[(LANE*8) +: 8];
  assign m2_bLANE = b[(LANE*8) +: 8];
  assign m2_xa[LANE] = m2_x(m2_unpack_s(m2_aLANE, 1'b0));
  assign m2_xb[LANE] = m2_x(m2_unpack_s(m2_bLANE, 1'b0));
  assign m2_vaLANE = {m2_aLANE[7], m2_aLANE};
  assign m2_vbLANE = {m2_bLANE[7], m2_bLANE};
  // structure core.adder.m2: the unit's shared partitioned adder (subword partitioned_carry_chain)
  assign m2_add_sLANE = pc_s_m2[(LANE)*8 +: 8];
  assign m2_add_coutLANE = pc_co_m2[(LANE+1)*1-1];
  always_comb begin
    y_m2 = '0; d_m2 = '0; fl_m2 = '0;
    m2_o0ex0_LANE = 'x;
    pc_a_m2 = '0; pc_b_m2 = '0; pc_cin_m2 = '0;
    case (op)
      3'd0: begin
        pc_a_m2[(LANE)*8 +: 8] = m2_aLANE; pc_b_m2[(LANE)*8 +: 8] = m2_bLANE; pc_cin_m2[(LANE)*1] = 1'b0;
        m2_o0ex0_LANE = $signed({(m2_aLANE[7] ^ m2_bLANE[7] ^ m2_add_coutLANE), m2_add_sLANE});
        y_m2[((LANE*8)+0) +: 8] = m2_wrap(m2_o0ex0_LANE);
        fl_m2[(0+LANE)*10 +: 10] = (((m2_aLANE[7] ^ m2_bLANE[7] ^ m2_add_coutLANE) ^ m2_add_sLANE[7]) ? (10'd1 << 8) : 10'd0) | (((m2_aLANE[7] ^ m2_bLANE[7] ^ m2_add_coutLANE) ^ m2_add_sLANE[7]) ? (10'd1 << 2) : 10'd0) | (m2_add_coutLANE ? (10'd1 << 7) : 10'd0);
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m2_comparator #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m2,
  output logic [19:0] fl_m2
);
  // alu_core_m2_comparator: lane LANE of mode 2 (int8_twos_complement) for the comparator ops min; the result buses are the mode's, with only this lane's bits written
  import alu_core_m2_pkg::*;
  logic d_m2;
  logic [7:0] m2_aLANE;
  logic [7:0] m2_bLANE;
  logic [38:0] m2_xa [0:1];
  logic [38:0] m2_xb [0:1];
  logic signed [8:0] m2_vaLANE;
  logic signed [8:0] m2_vbLANE;
  logic [7:0] m2_cmp_aLANE;
  logic [7:0] m2_cmp_bLANE;
  logic m2_cmp_ltLANE;
  logic m2_cmp_eqLANE;
  logic signed [18:0] m2_o2ex0_LANE;
  assign m2_aLANE = a[(LANE*8) +: 8];
  assign m2_bLANE = b[(LANE*8) +: 8];
  assign m2_xa[LANE] = m2_x(m2_unpack_s(m2_aLANE, 1'b0));
  assign m2_xb[LANE] = m2_x(m2_unpack_s(m2_bLANE, 1'b0));
  assign m2_vaLANE = {m2_aLANE[7], m2_aLANE};
  assign m2_vbLANE = {m2_bLANE[7], m2_bLANE};
  // structure core.comparator.m2: family prefix_comparator realized by the library module fam_cmp_prefix_comparator
  fam_cmp_prefix_comparator #(.W(8), .SIGNED(1), .STRUCTURE(0), .RADIX(2)) u_m2_cmpLANE (.a(m2_cmp_aLANE), .b(m2_cmp_bLANE), .lt(m2_cmp_ltLANE), .eq(m2_cmp_eqLANE));
  always_comb begin
    y_m2 = '0; d_m2 = '0; fl_m2 = '0;
    m2_cmp_aLANE = 'x; m2_cmp_bLANE = 'x; m2_o2ex0_LANE = 'x;
    case (op)
      3'd2: begin
        m2_cmp_aLANE = m2_aLANE; m2_cmp_bLANE = m2_bLANE;
        y_m2[((LANE*8)+0) +: 8] = (m2_cmp_ltLANE | m2_cmp_eqLANE) ? m2_aLANE : m2_bLANE;
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m2_converter #(parameter int LANE = 0, parameter int TGT = -1) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m2,
  output logic [19:0] fl_m2
);
  // alu_core_m2_converter: lane LANE of mode 2 (int8_twos_complement) for the converter ops cvt(int8), cvt(fp16), cvt(fxs1i7f8); the result buses are the mode's, with only this lane's bits written
  import alu_core_m2_pkg::*;
  logic d_m2;
  logic [7:0] m2_aLANE;
  logic [7:0] m2_bLANE;
  logic [38:0] m2_xa [0:1];
  logic [38:0] m2_xb [0:1];
  logic signed [8:0] m2_vaLANE;
  logic signed [8:0] m2_vbLANE;
  logic [38:0] m2_cv_xLANE_fp16;
  logic [7:0] m2_cv_wordLANE_fp16;
  logic [9:0] m2_cv_flLANE_fp16;
  logic [15:0] m2_cv_bitsLANE_fp16;
  logic [38:0] m2_cv_xLANE_fxs1i7f8;
  logic [7:0] m2_cv_wordLANE_fxs1i7f8;
  logic [9:0] m2_cv_flLANE_fxs1i7f8;
  logic [15:0] m2_cv_bitsLANE_fxs1i7f8;
  logic [38:0] m2_cv_xLANE_int8_twos_complement;
  logic [7:0] m2_cv_wordLANE_int8_twos_complement;
  logic [9:0] m2_cv_flLANE_int8_twos_complement;
  logic [7:0] m2_cv_bitsLANE_int8_twos_complement;
  logic [17:0] m2_o5c0_LANE;
  logic [25:0] m2_o6c0_LANE;
  logic [25:0] m2_o7c0_LANE;
  assign m2_aLANE = a[(LANE*8) +: 8];
  assign m2_bLANE = b[(LANE*8) +: 8];
  assign m2_xa[LANE] = m2_x(m2_unpack_s(m2_aLANE, 1'b0));
  assign m2_xb[LANE] = m2_x(m2_unpack_s(m2_bLANE, 1'b0));
  assign m2_vaLANE = {m2_aLANE[7], m2_aLANE};
  assign m2_vbLANE = {m2_bLANE[7], m2_bLANE};
  // structure core.converter.m2.fp16: family shift_round_convert
  fam_int_cvt_shift_round_convert_fp16_x22e13s9 u_m2_cvtLANE_fp16 (.x(m2_cv_xLANE_fp16), .rnd(rnd), .word(m2_cv_wordLANE_fp16), .ftz(ftz), .fl(m2_cv_flLANE_fp16), .bits(m2_cv_bitsLANE_fp16));
  // structure core.converter.m2.fxs1i7f8: family shift_round_convert
  fam_int_cvt_shift_round_convert_fxs1i7f8_x22e13s9 u_m2_cvtLANE_fxs1i7f8 (.x(m2_cv_xLANE_fxs1i7f8), .rnd(rnd), .word(m2_cv_wordLANE_fxs1i7f8), .ftz(ftz), .fl(m2_cv_flLANE_fxs1i7f8), .bits(m2_cv_bitsLANE_fxs1i7f8));
  // structure core.converter.m2.int8_twos_complement: family shift_round_convert
  fam_int_cvt_shift_round_convert_int8_twos_complement_x22e13s9 u_m2_cvtLANE_int8_twos_complement (.x(m2_cv_xLANE_int8_twos_complement), .rnd(rnd), .word(m2_cv_wordLANE_int8_twos_complement), .ftz(ftz), .fl(m2_cv_flLANE_int8_twos_complement), .bits(m2_cv_bitsLANE_int8_twos_complement));
  always_comb begin
    y_m2 = '0; d_m2 = '0; fl_m2 = '0;
    m2_cv_xLANE_fp16 = 'x; m2_cv_wordLANE_fp16 = 'x; m2_cv_xLANE_fxs1i7f8 = 'x; m2_cv_wordLANE_fxs1i7f8 = 'x; m2_cv_xLANE_int8_twos_complement = 'x; m2_cv_wordLANE_int8_twos_complement = 'x;
    m2_o5c0_LANE = 'x; m2_o6c0_LANE = 'x; m2_o7c0_LANE = 'x;
    case (op)
      3'd5: begin
        if (TGT == -1 || TGT == 5) begin
          m2_cv_xLANE_int8_twos_complement = m2_xa[LANE]; m2_cv_wordLANE_int8_twos_complement = 8'd0; m2_o5c0_LANE = {m2_cv_flLANE_int8_twos_complement, m2_cv_bitsLANE_int8_twos_complement};
          y_m2[((LANE*8)+0) +: 8] = m2_o5c0_LANE[7:0];
          fl_m2[(0+LANE)*10 +: 10] = m2_o5c0_LANE[17:8];
        end
      end
      3'd6: begin
        if (TGT == -1 || TGT == 6) begin
          m2_cv_xLANE_fp16 = m2_xa[LANE]; m2_cv_wordLANE_fp16 = 8'd0; m2_o6c0_LANE = {m2_cv_flLANE_fp16, m2_cv_bitsLANE_fp16};
          y_m2[((LANE*16)+0) +: 16] = m2_o6c0_LANE[15:0];
          fl_m2[(0+LANE)*10 +: 10] = m2_o6c0_LANE[25:16];
        end
      end
      3'd7: begin
        if (TGT == -1 || TGT == 7) begin
          m2_cv_xLANE_fxs1i7f8 = m2_xa[LANE]; m2_cv_wordLANE_fxs1i7f8 = 8'd0; m2_o7c0_LANE = {m2_cv_flLANE_fxs1i7f8, m2_cv_bitsLANE_fxs1i7f8};
          y_m2[((LANE*16)+0) +: 16] = m2_o7c0_LANE[15:0];
          fl_m2[(0+LANE)*10 +: 10] = m2_o7c0_LANE[25:16];
        end
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m2_multiplier #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m2,
  output logic [19:0] fl_m2
);
  // alu_core_m2_multiplier: lane LANE of mode 2 (int8_twos_complement) for the multiplier ops mul; the result buses are the mode's, with only this lane's bits written
  import alu_core_m2_pkg::*;
  logic d_m2;
  logic [7:0] m2_aLANE;
  logic [7:0] m2_bLANE;
  logic [38:0] m2_xa [0:1];
  logic [38:0] m2_xb [0:1];
  logic signed [8:0] m2_vaLANE;
  logic signed [8:0] m2_vbLANE;
  logic [7:0] m2_mul_aLANE;
  logic [7:0] m2_mul_bLANE;
  logic [15:0] m2_mul_pLANE;
  logic signed [18:0] m2_o1ex0_LANE;
  assign m2_aLANE = a[(LANE*8) +: 8];
  assign m2_bLANE = b[(LANE*8) +: 8];
  assign m2_xa[LANE] = m2_x(m2_unpack_s(m2_aLANE, 1'b0));
  assign m2_xb[LANE] = m2_x(m2_unpack_s(m2_bLANE, 1'b0));
  assign m2_vaLANE = {m2_aLANE[7], m2_aLANE};
  assign m2_vbLANE = {m2_bLANE[7], m2_bLANE};
  // structure core.multiplier.m2: family behavioral_star realized by the library module fam_mul_behavioral_star_w8_s
  fam_mul_behavioral_star_w8_s u_m2_mulLANE (.a(m2_mul_aLANE), .b(m2_mul_bLANE), .p(m2_mul_pLANE));
  always_comb begin
    y_m2 = '0; d_m2 = '0; fl_m2 = '0;
    m2_mul_aLANE = 'x; m2_mul_bLANE = 'x; m2_o1ex0_LANE = 'x;
    case (op)
      3'd1: begin
        m2_mul_aLANE = m2_aLANE; m2_mul_bLANE = m2_bLANE;
        m2_o1ex0_LANE = $signed({{3{m2_mul_pLANE[15]}}, m2_mul_pLANE});
        y_m2[((LANE*8)+0) +: 8] = m2_wrap(m2_o1ex0_LANE);
        fl_m2[(0+LANE)*10 +: 10] = (m2_o1ex0_LANE > 19'sd127 || m2_o1ex0_LANE < -19'sd128 ? (10'd1 << 8) : 10'd0) | (m2_o1ex0_LANE > 19'sd127 || m2_o1ex0_LANE < -19'sd128 ? (10'd1 << 2) : 10'd0);
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m3_adder_sh #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m3,
  output logic [19:0] fl_m3,
  output logic [15:0] pc_a_m3,
  output logic [15:0] pc_b_m3,
  output logic [0:0] pc_cin_m3,
  input  logic [15:0] pc_s_m3,
  input  logic [0:0] pc_co_m3
);
  // alu_core_m3_adder_sh: lane LANE of mode 3 (fxs1i7f8) for the adder ops add; the result buses are the mode's, with only this lane's bits written; the unit's shared adder serve this lane through the pc_/tp_ buses
  import alu_core_m3_pkg::*;
  logic d_m3;
  logic [15:0] m3_aLANE;
  logic [15:0] m3_bLANE;
  logic [54:0] m3_xa [0:0];
  logic [54:0] m3_xb [0:0];
  logic signed [16:0] m3_vaLANE;
  logic signed [16:0] m3_vbLANE;
  logic [15:0] m3_add_sLANE;
  logic m3_add_coutLANE;
  logic signed [34:0] m3_o0ex0_LANE;
  assign m3_aLANE = a[(LANE*16) +: 16];
  assign m3_bLANE = b[(LANE*16) +: 16];
  assign m3_xa[LANE] = m3_x(m3_unpack_s(m3_aLANE, 1'b0));
  assign m3_xb[LANE] = m3_x(m3_unpack_s(m3_bLANE, 1'b0));
  assign m3_vaLANE = {m3_aLANE[15], m3_aLANE};
  assign m3_vbLANE = {m3_bLANE[15], m3_bLANE};
  // structure core.adder.m3: the unit's shared partitioned adder (subword partitioned_carry_chain)
  assign m3_add_sLANE = pc_s_m3[(LANE)*16 +: 16];
  assign m3_add_coutLANE = pc_co_m3[(LANE+1)*1-1];
  always_comb begin
    y_m3 = '0; d_m3 = '0; fl_m3 = '0;
    m3_o0ex0_LANE = 'x;
    pc_a_m3 = '0; pc_b_m3 = '0; pc_cin_m3 = '0;
    case (op)
      3'd0: begin
        pc_a_m3[(LANE)*16 +: 16] = m3_aLANE; pc_b_m3[(LANE)*16 +: 16] = m3_bLANE; pc_cin_m3[(LANE)*1] = 1'b0;
        m3_o0ex0_LANE = $signed({(m3_aLANE[15] ^ m3_bLANE[15] ^ m3_add_coutLANE), m3_add_sLANE});
        y_m3[((LANE*16)+0) +: 16] = m3_wrap(m3_o0ex0_LANE);
        fl_m3[(0+LANE)*10 +: 10] = (((m3_aLANE[15] ^ m3_bLANE[15] ^ m3_add_coutLANE) ^ m3_add_sLANE[15]) ? (10'd1 << 8) : 10'd0) | (((m3_aLANE[15] ^ m3_bLANE[15] ^ m3_add_coutLANE) ^ m3_add_sLANE[15]) ? (10'd1 << 2) : 10'd0) | (m3_add_coutLANE ? (10'd1 << 7) : 10'd0);
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m3_comparator #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m3,
  output logic [19:0] fl_m3
);
  // alu_core_m3_comparator: lane LANE of mode 3 (fxs1i7f8) for the comparator ops min; the result buses are the mode's, with only this lane's bits written
  import alu_core_m3_pkg::*;
  logic d_m3;
  logic [15:0] m3_aLANE;
  logic [15:0] m3_bLANE;
  logic [54:0] m3_xa [0:0];
  logic [54:0] m3_xb [0:0];
  logic signed [16:0] m3_vaLANE;
  logic signed [16:0] m3_vbLANE;
  logic [15:0] m3_cmp_aLANE;
  logic [15:0] m3_cmp_bLANE;
  logic m3_cmp_ltLANE;
  logic m3_cmp_eqLANE;
  logic signed [34:0] m3_o2ex0_LANE;
  assign m3_aLANE = a[(LANE*16) +: 16];
  assign m3_bLANE = b[(LANE*16) +: 16];
  assign m3_xa[LANE] = m3_x(m3_unpack_s(m3_aLANE, 1'b0));
  assign m3_xb[LANE] = m3_x(m3_unpack_s(m3_bLANE, 1'b0));
  assign m3_vaLANE = {m3_aLANE[15], m3_aLANE};
  assign m3_vbLANE = {m3_bLANE[15], m3_bLANE};
  // structure core.comparator.m3: family prefix_comparator realized by the library module fam_cmp_prefix_comparator
  fam_cmp_prefix_comparator #(.W(16), .SIGNED(1), .STRUCTURE(0), .RADIX(2)) u_m3_cmpLANE (.a(m3_cmp_aLANE), .b(m3_cmp_bLANE), .lt(m3_cmp_ltLANE), .eq(m3_cmp_eqLANE));
  always_comb begin
    y_m3 = '0; d_m3 = '0; fl_m3 = '0;
    m3_cmp_aLANE = 'x; m3_cmp_bLANE = 'x; m3_o2ex0_LANE = 'x;
    case (op)
      3'd2: begin
        m3_cmp_aLANE = m3_aLANE; m3_cmp_bLANE = m3_bLANE;
        y_m3[((LANE*16)+0) +: 16] = (m3_cmp_ltLANE | m3_cmp_eqLANE) ? m3_aLANE : m3_bLANE;
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m3_converter #(parameter int LANE = 0, parameter int TGT = -1) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m3,
  output logic [19:0] fl_m3
);
  // alu_core_m3_converter: lane LANE of mode 3 (fxs1i7f8) for the converter ops cvt(int8), cvt(fp16), cvt(fxs1i7f8); the result buses are the mode's, with only this lane's bits written
  import alu_core_m3_pkg::*;
  logic d_m3;
  logic [15:0] m3_aLANE;
  logic [15:0] m3_bLANE;
  logic [54:0] m3_xa [0:0];
  logic [54:0] m3_xb [0:0];
  logic signed [16:0] m3_vaLANE;
  logic signed [16:0] m3_vbLANE;
  logic [54:0] m3_cv_xLANE_fp16;
  logic [7:0] m3_cv_wordLANE_fp16;
  logic [9:0] m3_cv_flLANE_fp16;
  logic [15:0] m3_cv_bitsLANE_fp16;
  logic [54:0] m3_cv_xLANE_fxs1i7f8;
  logic [7:0] m3_cv_wordLANE_fxs1i7f8;
  logic [9:0] m3_cv_flLANE_fxs1i7f8;
  logic [15:0] m3_cv_bitsLANE_fxs1i7f8;
  logic [54:0] m3_cv_xLANE_int8_twos_complement;
  logic [7:0] m3_cv_wordLANE_int8_twos_complement;
  logic [9:0] m3_cv_flLANE_int8_twos_complement;
  logic [7:0] m3_cv_bitsLANE_int8_twos_complement;
  logic [17:0] m3_o5c0_LANE;
  logic [25:0] m3_o6c0_LANE;
  logic [25:0] m3_o7c0_LANE;
  assign m3_aLANE = a[(LANE*16) +: 16];
  assign m3_bLANE = b[(LANE*16) +: 16];
  assign m3_xa[LANE] = m3_x(m3_unpack_s(m3_aLANE, 1'b0));
  assign m3_xb[LANE] = m3_x(m3_unpack_s(m3_bLANE, 1'b0));
  assign m3_vaLANE = {m3_aLANE[15], m3_aLANE};
  assign m3_vbLANE = {m3_bLANE[15], m3_bLANE};
  // structure core.converter.m3.fp16: family shift_round_convert
  fam_int_cvt_shift_round_convert_fp16_x38e13s17 u_m3_cvtLANE_fp16 (.x(m3_cv_xLANE_fp16), .rnd(rnd), .word(m3_cv_wordLANE_fp16), .ftz(ftz), .fl(m3_cv_flLANE_fp16), .bits(m3_cv_bitsLANE_fp16));
  // structure core.converter.m3.fxs1i7f8: family shift_round_convert
  fam_int_cvt_shift_round_convert_fxs1i7f8_x38e13s17 u_m3_cvtLANE_fxs1i7f8 (.x(m3_cv_xLANE_fxs1i7f8), .rnd(rnd), .word(m3_cv_wordLANE_fxs1i7f8), .ftz(ftz), .fl(m3_cv_flLANE_fxs1i7f8), .bits(m3_cv_bitsLANE_fxs1i7f8));
  // structure core.converter.m3.int8_twos_complement: family shift_round_convert
  fam_int_cvt_shift_round_convert_int8_twos_complement_x38e13s17 u_m3_cvtLANE_int8_twos_complement (.x(m3_cv_xLANE_int8_twos_complement), .rnd(rnd), .word(m3_cv_wordLANE_int8_twos_complement), .ftz(ftz), .fl(m3_cv_flLANE_int8_twos_complement), .bits(m3_cv_bitsLANE_int8_twos_complement));
  always_comb begin
    y_m3 = '0; d_m3 = '0; fl_m3 = '0;
    m3_cv_xLANE_fp16 = 'x; m3_cv_wordLANE_fp16 = 'x; m3_cv_xLANE_fxs1i7f8 = 'x; m3_cv_wordLANE_fxs1i7f8 = 'x; m3_cv_xLANE_int8_twos_complement = 'x; m3_cv_wordLANE_int8_twos_complement = 'x;
    m3_o5c0_LANE = 'x; m3_o6c0_LANE = 'x; m3_o7c0_LANE = 'x;
    case (op)
      3'd5: begin
        if (TGT == -1 || TGT == 5) begin
          m3_cv_xLANE_int8_twos_complement = m3_xa[LANE]; m3_cv_wordLANE_int8_twos_complement = 8'd0; m3_o5c0_LANE = {m3_cv_flLANE_int8_twos_complement, m3_cv_bitsLANE_int8_twos_complement};
          y_m3[((LANE*8)+0) +: 8] = m3_o5c0_LANE[7:0];
          fl_m3[(0+LANE)*10 +: 10] = m3_o5c0_LANE[17:8];
        end
      end
      3'd6: begin
        if (TGT == -1 || TGT == 6) begin
          m3_cv_xLANE_fp16 = m3_xa[LANE]; m3_cv_wordLANE_fp16 = 8'd0; m3_o6c0_LANE = {m3_cv_flLANE_fp16, m3_cv_bitsLANE_fp16};
          y_m3[((LANE*16)+0) +: 16] = m3_o6c0_LANE[15:0];
          fl_m3[(0+LANE)*10 +: 10] = m3_o6c0_LANE[25:16];
        end
      end
      3'd7: begin
        if (TGT == -1 || TGT == 7) begin
          m3_cv_xLANE_fxs1i7f8 = m3_xa[LANE]; m3_cv_wordLANE_fxs1i7f8 = 8'd0; m3_o7c0_LANE = {m3_cv_flLANE_fxs1i7f8, m3_cv_bitsLANE_fxs1i7f8};
          y_m3[((LANE*16)+0) +: 16] = m3_o7c0_LANE[15:0];
          fl_m3[(0+LANE)*10 +: 10] = m3_o7c0_LANE[25:16];
        end
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m3_multiplier #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m3,
  output logic [19:0] fl_m3
);
  // alu_core_m3_multiplier: lane LANE of mode 3 (fxs1i7f8) for the multiplier ops mul; the result buses are the mode's, with only this lane's bits written
  import alu_core_m3_pkg::*;
  logic d_m3;
  logic [15:0] m3_aLANE;
  logic [15:0] m3_bLANE;
  logic [54:0] m3_xa [0:0];
  logic [54:0] m3_xb [0:0];
  logic signed [16:0] m3_vaLANE;
  logic signed [16:0] m3_vbLANE;
  logic [15:0] m3_mul_aLANE;
  logic [15:0] m3_mul_bLANE;
  logic [31:0] m3_mul_pLANE;
  logic signed [34:0] m3_o1ex0_LANE;
  logic signed [34:0] m3_o1pr0_LANE;
  assign m3_aLANE = a[(LANE*16) +: 16];
  assign m3_bLANE = b[(LANE*16) +: 16];
  assign m3_xa[LANE] = m3_x(m3_unpack_s(m3_aLANE, 1'b0));
  assign m3_xb[LANE] = m3_x(m3_unpack_s(m3_bLANE, 1'b0));
  assign m3_vaLANE = {m3_aLANE[15], m3_aLANE};
  assign m3_vbLANE = {m3_bLANE[15], m3_bLANE};
  // structure core.multiplier.m3: family behavioral_star realized by the library module fam_mul_behavioral_star_w16_s
  fam_mul_behavioral_star_w16_s u_m3_mulLANE (.a(m3_mul_aLANE), .b(m3_mul_bLANE), .p(m3_mul_pLANE));
  always_comb begin
    y_m3 = '0; d_m3 = '0; fl_m3 = '0;
    m3_mul_aLANE = 'x; m3_mul_bLANE = 'x; m3_o1ex0_LANE = 'x; m3_o1pr0_LANE = 'x;
    case (op)
      3'd1: begin
        m3_mul_aLANE = m3_aLANE; m3_mul_bLANE = m3_bLANE;
        m3_o1ex0_LANE = $signed({{3{m3_mul_pLANE[31]}}, m3_mul_pLANE});
        m3_o1pr0_LANE = m3_o1ex0_LANE;
        m3_o1ex0_LANE = m3_rshift(m3_o1pr0_LANE, 8, rnd, 8'd0);
        y_m3[((LANE*16)+0) +: 16] = m3_wrap(m3_o1ex0_LANE);
        fl_m3[(0+LANE)*10 +: 10] = (m3_o1ex0_LANE > 35'sd32767 || m3_o1ex0_LANE < -35'sd32768 ? (10'd1 << 8) : 10'd0) | (m3_o1ex0_LANE > 35'sd32767 || m3_o1ex0_LANE < -35'sd32768 ? (10'd1 << 2) : 10'd0) | (m3_rshift(m3_o1pr0_LANE, 8, 3'd1, 0) * 35'sd256 != m3_o1pr0_LANE ? (10'd1 << 4) : 10'd0) | ((m3_o1ex0_LANE > 35'sd32767 || m3_o1ex0_LANE < -35'sd32768) ? ((10'd1 << 2) | (10'd1 << 4)) : 10'd0);
      end
      default: ;
    endcase
  end
endmodule
// ADIR-MEMBER m0_l0_fp_adder
// EVOLVE-BLOCK-START
module alu_core_u_m0_l0_fp_adder (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m0,
  output logic [19:0] fl_m0,
  input  logic [42:0] xa_m0,
  input  logic [42:0] xb_m0,
  input  logic [0:0] dena_m0,
  input  logic [0:0] denb_m0,
  output logic [42:0] x_m0
);
  // alu_core_u_m0_l0_fp_adder: physical structure `m0.l0.fp_adder` (kind fp_adder, slot fp_adder); realizes m0.l0.fp_adder: fp_adder, mode 0 lane 0, fp16, ops fadd
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [31:0] y_m0_l0;
  logic [19:0] fl_m0_l0;
  logic [42:0] x_m0_l0;
  alu_core_m0_fp_adder #(.LANE(0)) u_m0_l0 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_l0), .fl_m0(fl_m0_l0), .xa_m0(xa_m0), .xb_m0(xb_m0), .dena_m0(dena_m0), .denb_m0(denb_m0), .x_m0(x_m0_l0));
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
  input  logic [2:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [42:0] xa_m0,
  output logic [42:0] xb_m0,
  output logic [0:0] dena_m0,
  output logic [0:0] denb_m0
);
  // alu_core_u_m0_l0_unpacker: physical structure `m0.l0.unpacker` (kind unpacker, slot unpacker); realizes m0.l0.unpacker: unpacker, mode 0 lane 0, fp16, ops fadd, fmul, cvt(int8), cvt(fp16), cvt(fxs1i7f8)
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [42:0] xa_m0_l0;
  logic [42:0] xb_m0_l0;
  logic dena_m0_l0;
  logic denb_m0_l0;
  alu_core_m0_unpacker #(.LANE(0)) u_m0_l0 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .xa_m0(xa_m0_l0), .xb_m0(xb_m0_l0), .dena_m0(dena_m0_l0), .denb_m0(denb_m0_l0));
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
  input  logic [2:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m0,
  output logic [19:0] fl_m0,
  input  logic [42:0] xa_m0,
  input  logic [42:0] xb_m0,
  input  logic [0:0] dena_m0,
  input  logic [0:0] denb_m0,
  input  logic [42:0] x_m0
);
  // alu_core_u_m0_l0_rounder: physical structure `m0.l0.rounder` (kind rounder, slot rounder); realizes m0.l0.rounder: rounder, mode 0 lane 0, fp16, ops fadd, fmul, cvt(int8), cvt(fp16), cvt(fxs1i7f8)
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [31:0] y_m0_l0;
  logic [19:0] fl_m0_l0;
  alu_core_m0_rounder #(.LANE(0)) u_m0_l0 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_l0), .fl_m0(fl_m0_l0), .xa_m0(xa_m0), .xb_m0(xb_m0), .dena_m0(dena_m0), .denb_m0(denb_m0), .x_m0(x_m0));
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
  input  logic [2:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m0,
  output logic [19:0] fl_m0,
  input  logic [42:0] xa_m0,
  input  logic [42:0] xb_m0,
  input  logic [0:0] dena_m0,
  input  logic [0:0] denb_m0,
  output logic [42:0] x_m0
);
  // alu_core_u_m0_l0_fp_multiplier: physical structure `m0.l0.fp_multiplier` (kind fp_multiplier, slot fp_multiplier); realizes m0.l0.fp_multiplier: fp_multiplier, mode 0 lane 0, fp16, ops fmul
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [31:0] y_m0_l0;
  logic [19:0] fl_m0_l0;
  logic [42:0] x_m0_l0;
  alu_core_m0_fp_multiplier #(.LANE(0)) u_m0_l0 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_l0), .fl_m0(fl_m0_l0), .xa_m0(xa_m0), .xb_m0(xb_m0), .dena_m0(dena_m0), .denb_m0(denb_m0), .x_m0(x_m0_l0));
  assign y_m0 = y_m0_l0;
  assign fl_m0 = fl_m0_l0;
  assign x_m0 = x_m0_l0;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m0_l0_converter_int8_twos_complement
// EVOLVE-BLOCK-START
module alu_core_u_m0_l0_converter_int8_twos_complement (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m0,
  output logic [19:0] fl_m0,
  input  logic [42:0] xa_m0,
  input  logic [42:0] xb_m0,
  input  logic [0:0] dena_m0,
  input  logic [0:0] denb_m0,
  output logic [42:0] x_m0
);
  // alu_core_u_m0_l0_converter_int8_twos_complement: physical structure `m0.l0.converter.int8_twos_complement` (kind converter, slot converter); realizes m0.l0.converter.int8_twos_complement: converter, mode 0 lane 0, fp16 -> int8_twos_complement, ops cvt(int8)
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [31:0] y_m0_l0_t5;
  logic [19:0] fl_m0_l0_t5;
  logic [42:0] x_m0_l0_t5;
  alu_core_m0_converter #(.LANE(0), .TGT(5)) u_m0_l0_t5 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_l0_t5), .fl_m0(fl_m0_l0_t5), .xa_m0(xa_m0), .xb_m0(xb_m0), .dena_m0(dena_m0), .denb_m0(denb_m0), .x_m0(x_m0_l0_t5));
  assign y_m0 = y_m0_l0_t5;
  assign fl_m0 = fl_m0_l0_t5;
  assign x_m0 = x_m0_l0_t5;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m0_l0_converter_fp16
// EVOLVE-BLOCK-START
module alu_core_u_m0_l0_converter_fp16 (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m0,
  output logic [19:0] fl_m0,
  input  logic [42:0] xa_m0,
  input  logic [42:0] xb_m0,
  input  logic [0:0] dena_m0,
  input  logic [0:0] denb_m0,
  output logic [42:0] x_m0
);
  // alu_core_u_m0_l0_converter_fp16: physical structure `m0.l0.converter.fp16` (kind converter, slot converter); realizes m0.l0.converter.fp16: converter, mode 0 lane 0, fp16 -> fp16, ops cvt(fp16)
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [31:0] y_m0_l0_t6;
  logic [19:0] fl_m0_l0_t6;
  logic [42:0] x_m0_l0_t6;
  alu_core_m0_converter #(.LANE(0), .TGT(6)) u_m0_l0_t6 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_l0_t6), .fl_m0(fl_m0_l0_t6), .xa_m0(xa_m0), .xb_m0(xb_m0), .dena_m0(dena_m0), .denb_m0(denb_m0), .x_m0(x_m0_l0_t6));
  assign y_m0 = y_m0_l0_t6;
  assign fl_m0 = fl_m0_l0_t6;
  assign x_m0 = x_m0_l0_t6;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m0_l0_converter_fxs1i7f8
// EVOLVE-BLOCK-START
module alu_core_u_m0_l0_converter_fxs1i7f8 (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m0,
  output logic [19:0] fl_m0,
  input  logic [42:0] xa_m0,
  input  logic [42:0] xb_m0,
  input  logic [0:0] dena_m0,
  input  logic [0:0] denb_m0,
  output logic [42:0] x_m0
);
  // alu_core_u_m0_l0_converter_fxs1i7f8: physical structure `m0.l0.converter.fxs1i7f8` (kind converter, slot converter); realizes m0.l0.converter.fxs1i7f8: converter, mode 0 lane 0, fp16 -> fxs1i7f8, ops cvt(fxs1i7f8)
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [31:0] y_m0_l0_t7;
  logic [19:0] fl_m0_l0_t7;
  logic [42:0] x_m0_l0_t7;
  alu_core_m0_converter #(.LANE(0), .TGT(7)) u_m0_l0_t7 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_l0_t7), .fl_m0(fl_m0_l0_t7), .xa_m0(xa_m0), .xb_m0(xb_m0), .dena_m0(dena_m0), .denb_m0(denb_m0), .x_m0(x_m0_l0_t7));
  assign y_m0 = y_m0_l0_t7;
  assign fl_m0 = fl_m0_l0_t7;
  assign x_m0 = x_m0_l0_t7;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l0_adder
// EVOLVE-BLOCK-START
module alu_core_u_m1_l0_adder (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m1,
  output logic [19:0] fl_m1
);
  // alu_core_u_m1_l0_adder: physical structure `m1.l0.adder` (kind adder, slot adder); realizes m1.l0.adder: adder, mode 1 lane 0, int16_twos_complement, ops add
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [15:0] pc_a_m1;
  logic [15:0] pc_b_m1;
  logic pc_cin_m1;
  logic [15:0] pc_s_m1;
  logic pc_co_m1;
  logic [31:0] y_m1_l0;
  logic [19:0] fl_m1_l0;
  logic [15:0] pc_a_m1_l0;
  logic [15:0] pc_b_m1_l0;
  logic pc_cin_m1_l0;
  logic pc_sel;
  logic [15:0] pc_a;
  logic [15:0] pc_b;
  logic pc_cin;
  logic [15:0] pc_s;
  logic pc_co;
  alu_core_m1_adder_sh #(.LANE(0)) u_m1_l0 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_l0), .fl_m1(fl_m1_l0), .pc_a_m1(pc_a_m1_l0), .pc_b_m1(pc_b_m1_l0), .pc_cin_m1(pc_cin_m1_l0), .pc_s_m1(pc_s_m1), .pc_co_m1(pc_co_m1));
  assign y_m1 = y_m1_l0;
  assign fl_m1 = fl_m1_l0;
  assign pc_a_m1 = pc_a_m1_l0;
  assign pc_b_m1 = pc_b_m1_l0;
  assign pc_cin_m1 = pc_cin_m1_l0;
  assign pc_sel = (mode == 2'd1) ? 1'd0 : '0;
  assign pc_a = (mode == 2'd1) ? pc_a_m1 : '0;
  assign pc_b = (mode == 2'd1) ? pc_b_m1 : '0;
  assign pc_cin = (mode == 2'd1) ? pc_cin_m1 : '0;
  // subword partitioned_carry_chain: one library adder over the whole word, its carries cut at the selected packing's lane boundaries (1 x int16_twos_complement)
  fam_add_partitioned_w16_16_carry_kill_gate_0cc88441ac18 u_part (.a(pc_a), .b(pc_b), .cin(pc_cin), .sel(pc_sel), .s(pc_s), .cout(pc_co));
  assign pc_s_m1 = pc_s;
  assign pc_co_m1 = pc_co;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l0_multiplier
// EVOLVE-BLOCK-START
module alu_core_u_m1_l0_multiplier (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m1,
  output logic [19:0] fl_m1
);
  // alu_core_u_m1_l0_multiplier: physical structure `m1.l0.multiplier` (kind multiplier, slot multiplier); realizes m1.l0.multiplier: multiplier, mode 1 lane 0, int16_twos_complement, ops mul
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [31:0] y_m1_l0;
  logic [19:0] fl_m1_l0;
  alu_core_m1_multiplier #(.LANE(0)) u_m1_l0 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_l0), .fl_m1(fl_m1_l0));
  assign y_m1 = y_m1_l0;
  assign fl_m1 = fl_m1_l0;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l0_comparator
// EVOLVE-BLOCK-START
module alu_core_u_m1_l0_comparator (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m1,
  output logic [19:0] fl_m1
);
  // alu_core_u_m1_l0_comparator: physical structure `m1.l0.comparator` (kind comparator, slot comparator); realizes m1.l0.comparator: comparator, mode 1 lane 0, int16_twos_complement, ops min
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [31:0] y_m1_l0;
  logic [19:0] fl_m1_l0;
  alu_core_m1_comparator #(.LANE(0)) u_m1_l0 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_l0), .fl_m1(fl_m1_l0));
  assign y_m1 = y_m1_l0;
  assign fl_m1 = fl_m1_l0;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l0_converter_int8_twos_complement
// EVOLVE-BLOCK-START
module alu_core_u_m1_l0_converter_int8_twos_complement (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m1,
  output logic [19:0] fl_m1
);
  // alu_core_u_m1_l0_converter_int8_twos_complement: physical structure `m1.l0.converter.int8_twos_complement` (kind converter, slot converter); realizes m1.l0.converter.int8_twos_complement: converter, mode 1 lane 0, int16_twos_complement -> int8_twos_complement, ops cvt(int8)
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [31:0] y_m1_l0_t5;
  logic [19:0] fl_m1_l0_t5;
  alu_core_m1_converter #(.LANE(0), .TGT(5)) u_m1_l0_t5 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_l0_t5), .fl_m1(fl_m1_l0_t5));
  assign y_m1 = y_m1_l0_t5;
  assign fl_m1 = fl_m1_l0_t5;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l0_converter_fp16
// EVOLVE-BLOCK-START
module alu_core_u_m1_l0_converter_fp16 (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m1,
  output logic [19:0] fl_m1
);
  // alu_core_u_m1_l0_converter_fp16: physical structure `m1.l0.converter.fp16` (kind converter, slot converter); realizes m1.l0.converter.fp16: converter, mode 1 lane 0, int16_twos_complement -> fp16, ops cvt(fp16)
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [31:0] y_m1_l0_t6;
  logic [19:0] fl_m1_l0_t6;
  alu_core_m1_converter #(.LANE(0), .TGT(6)) u_m1_l0_t6 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_l0_t6), .fl_m1(fl_m1_l0_t6));
  assign y_m1 = y_m1_l0_t6;
  assign fl_m1 = fl_m1_l0_t6;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l0_converter_fxs1i7f8
// EVOLVE-BLOCK-START
module alu_core_u_m1_l0_converter_fxs1i7f8 (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m1,
  output logic [19:0] fl_m1
);
  // alu_core_u_m1_l0_converter_fxs1i7f8: physical structure `m1.l0.converter.fxs1i7f8` (kind converter, slot converter); realizes m1.l0.converter.fxs1i7f8: converter, mode 1 lane 0, int16_twos_complement -> fxs1i7f8, ops cvt(fxs1i7f8)
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [31:0] y_m1_l0_t7;
  logic [19:0] fl_m1_l0_t7;
  alu_core_m1_converter #(.LANE(0), .TGT(7)) u_m1_l0_t7 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_l0_t7), .fl_m1(fl_m1_l0_t7));
  assign y_m1 = y_m1_l0_t7;
  assign fl_m1 = fl_m1_l0_t7;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m2_l0_adder
// EVOLVE-BLOCK-START
module alu_core_u_m2_l0_adder (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m2,
  output logic [19:0] fl_m2
);
  // alu_core_u_m2_l0_adder: physical structure `m2.l0.adder` (kind adder, slot adder); realizes m2.l0.adder: adder, mode 2 lane 0, int8_twos_complement, ops add
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [15:0] pc_a_m2;
  logic [15:0] pc_b_m2;
  logic [1:0] pc_cin_m2;
  logic [15:0] pc_s_m2;
  logic [1:0] pc_co_m2;
  logic [31:0] y_m2_l0;
  logic [19:0] fl_m2_l0;
  logic [15:0] pc_a_m2_l0;
  logic [15:0] pc_b_m2_l0;
  logic [1:0] pc_cin_m2_l0;
  logic pc_sel;
  logic [15:0] pc_a;
  logic [15:0] pc_b;
  logic [1:0] pc_cin;
  logic [15:0] pc_s;
  logic [1:0] pc_co;
  alu_core_m2_adder_sh #(.LANE(0)) u_m2_l0 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_l0), .fl_m2(fl_m2_l0), .pc_a_m2(pc_a_m2_l0), .pc_b_m2(pc_b_m2_l0), .pc_cin_m2(pc_cin_m2_l0), .pc_s_m2(pc_s_m2), .pc_co_m2(pc_co_m2));
  assign y_m2 = y_m2_l0;
  assign fl_m2 = fl_m2_l0;
  assign pc_a_m2 = pc_a_m2_l0;
  assign pc_b_m2 = pc_b_m2_l0;
  assign pc_cin_m2 = pc_cin_m2_l0;
  assign pc_sel = (mode == 2'd2) ? 1'd0 : '0;
  assign pc_a = (mode == 2'd2) ? pc_a_m2 : '0;
  assign pc_b = (mode == 2'd2) ? pc_b_m2 : '0;
  assign pc_cin = (mode == 2'd2) ? pc_cin_m2 : '0;
  // subword partitioned_carry_chain: one library adder over the whole word, its carries cut at the selected packing's lane boundaries (2 x int8_twos_complement)
  fam_add_partitioned_w16_8_carry_kill_gate_0cc88441ac18 u_part (.a(pc_a), .b(pc_b), .cin(pc_cin), .sel(pc_sel), .s(pc_s), .cout(pc_co));
  assign pc_s_m2 = pc_s;
  assign pc_co_m2 = pc_co;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m2_l1_adder
// EVOLVE-BLOCK-START
module alu_core_u_m2_l1_adder (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m2,
  output logic [19:0] fl_m2
);
  // alu_core_u_m2_l1_adder: physical structure `m2.l1.adder` (kind adder, slot adder); realizes m2.l1.adder: adder, mode 2 lane 1, int8_twos_complement, ops add
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [15:0] pc_a_m2;
  logic [15:0] pc_b_m2;
  logic [1:0] pc_cin_m2;
  logic [15:0] pc_s_m2;
  logic [1:0] pc_co_m2;
  logic [31:0] y_m2_l1;
  logic [19:0] fl_m2_l1;
  logic [15:0] pc_a_m2_l1;
  logic [15:0] pc_b_m2_l1;
  logic [1:0] pc_cin_m2_l1;
  logic pc_sel;
  logic [15:0] pc_a;
  logic [15:0] pc_b;
  logic [1:0] pc_cin;
  logic [15:0] pc_s;
  logic [1:0] pc_co;
  alu_core_m2_adder_sh #(.LANE(1)) u_m2_l1 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_l1), .fl_m2(fl_m2_l1), .pc_a_m2(pc_a_m2_l1), .pc_b_m2(pc_b_m2_l1), .pc_cin_m2(pc_cin_m2_l1), .pc_s_m2(pc_s_m2), .pc_co_m2(pc_co_m2));
  assign y_m2 = y_m2_l1;
  assign fl_m2 = fl_m2_l1;
  assign pc_a_m2 = pc_a_m2_l1;
  assign pc_b_m2 = pc_b_m2_l1;
  assign pc_cin_m2 = pc_cin_m2_l1;
  assign pc_sel = (mode == 2'd2) ? 1'd0 : '0;
  assign pc_a = (mode == 2'd2) ? pc_a_m2 : '0;
  assign pc_b = (mode == 2'd2) ? pc_b_m2 : '0;
  assign pc_cin = (mode == 2'd2) ? pc_cin_m2 : '0;
  // subword partitioned_carry_chain: one library adder over the whole word, its carries cut at the selected packing's lane boundaries (2 x int8_twos_complement)
  fam_add_partitioned_w16_8_carry_kill_gate_0cc88441ac18 u_part (.a(pc_a), .b(pc_b), .cin(pc_cin), .sel(pc_sel), .s(pc_s), .cout(pc_co));
  assign pc_s_m2 = pc_s;
  assign pc_co_m2 = pc_co;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m2_l0_multiplier
// EVOLVE-BLOCK-START
module alu_core_u_m2_l0_multiplier (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m2,
  output logic [19:0] fl_m2
);
  // alu_core_u_m2_l0_multiplier: physical structure `m2.l0.multiplier` (kind multiplier, slot multiplier); realizes m2.l0.multiplier: multiplier, mode 2 lane 0, int8_twos_complement, ops mul
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [31:0] y_m2_l0;
  logic [19:0] fl_m2_l0;
  alu_core_m2_multiplier #(.LANE(0)) u_m2_l0 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_l0), .fl_m2(fl_m2_l0));
  assign y_m2 = y_m2_l0;
  assign fl_m2 = fl_m2_l0;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m2_l1_multiplier
// EVOLVE-BLOCK-START
module alu_core_u_m2_l1_multiplier (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m2,
  output logic [19:0] fl_m2
);
  // alu_core_u_m2_l1_multiplier: physical structure `m2.l1.multiplier` (kind multiplier, slot multiplier); realizes m2.l1.multiplier: multiplier, mode 2 lane 1, int8_twos_complement, ops mul
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [31:0] y_m2_l1;
  logic [19:0] fl_m2_l1;
  alu_core_m2_multiplier #(.LANE(1)) u_m2_l1 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_l1), .fl_m2(fl_m2_l1));
  assign y_m2 = y_m2_l1;
  assign fl_m2 = fl_m2_l1;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m2_l0_comparator
// EVOLVE-BLOCK-START
module alu_core_u_m2_l0_comparator (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m2,
  output logic [19:0] fl_m2
);
  // alu_core_u_m2_l0_comparator: physical structure `m2.l0.comparator` (kind comparator, slot comparator); realizes m2.l0.comparator: comparator, mode 2 lane 0, int8_twos_complement, ops min
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [31:0] y_m2_l0;
  logic [19:0] fl_m2_l0;
  alu_core_m2_comparator #(.LANE(0)) u_m2_l0 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_l0), .fl_m2(fl_m2_l0));
  assign y_m2 = y_m2_l0;
  assign fl_m2 = fl_m2_l0;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m2_l1_comparator
// EVOLVE-BLOCK-START
module alu_core_u_m2_l1_comparator (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m2,
  output logic [19:0] fl_m2
);
  // alu_core_u_m2_l1_comparator: physical structure `m2.l1.comparator` (kind comparator, slot comparator); realizes m2.l1.comparator: comparator, mode 2 lane 1, int8_twos_complement, ops min
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [31:0] y_m2_l1;
  logic [19:0] fl_m2_l1;
  alu_core_m2_comparator #(.LANE(1)) u_m2_l1 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_l1), .fl_m2(fl_m2_l1));
  assign y_m2 = y_m2_l1;
  assign fl_m2 = fl_m2_l1;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m2_l0_converter_int8_twos_complement
// EVOLVE-BLOCK-START
module alu_core_u_m2_l0_converter_int8_twos_complement (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m2,
  output logic [19:0] fl_m2
);
  // alu_core_u_m2_l0_converter_int8_twos_complement: physical structure `m2.l0.converter.int8_twos_complement` (kind converter, slot converter); realizes m2.l0.converter.int8_twos_complement: converter, mode 2 lane 0, int8_twos_complement -> int8_twos_complement, ops cvt(int8)
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [31:0] y_m2_l0_t5;
  logic [19:0] fl_m2_l0_t5;
  alu_core_m2_converter #(.LANE(0), .TGT(5)) u_m2_l0_t5 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_l0_t5), .fl_m2(fl_m2_l0_t5));
  assign y_m2 = y_m2_l0_t5;
  assign fl_m2 = fl_m2_l0_t5;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m2_l1_converter_int8_twos_complement
// EVOLVE-BLOCK-START
module alu_core_u_m2_l1_converter_int8_twos_complement (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m2,
  output logic [19:0] fl_m2
);
  // alu_core_u_m2_l1_converter_int8_twos_complement: physical structure `m2.l1.converter.int8_twos_complement` (kind converter, slot converter); realizes m2.l1.converter.int8_twos_complement: converter, mode 2 lane 1, int8_twos_complement -> int8_twos_complement, ops cvt(int8)
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [31:0] y_m2_l1_t5;
  logic [19:0] fl_m2_l1_t5;
  alu_core_m2_converter #(.LANE(1), .TGT(5)) u_m2_l1_t5 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_l1_t5), .fl_m2(fl_m2_l1_t5));
  assign y_m2 = y_m2_l1_t5;
  assign fl_m2 = fl_m2_l1_t5;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m2_l0_converter_fp16
// EVOLVE-BLOCK-START
module alu_core_u_m2_l0_converter_fp16 (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m2,
  output logic [19:0] fl_m2
);
  // alu_core_u_m2_l0_converter_fp16: physical structure `m2.l0.converter.fp16` (kind converter, slot converter); realizes m2.l0.converter.fp16: converter, mode 2 lane 0, int8_twos_complement -> fp16, ops cvt(fp16)
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [31:0] y_m2_l0_t6;
  logic [19:0] fl_m2_l0_t6;
  alu_core_m2_converter #(.LANE(0), .TGT(6)) u_m2_l0_t6 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_l0_t6), .fl_m2(fl_m2_l0_t6));
  assign y_m2 = y_m2_l0_t6;
  assign fl_m2 = fl_m2_l0_t6;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m2_l1_converter_fp16
// EVOLVE-BLOCK-START
module alu_core_u_m2_l1_converter_fp16 (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m2,
  output logic [19:0] fl_m2
);
  // alu_core_u_m2_l1_converter_fp16: physical structure `m2.l1.converter.fp16` (kind converter, slot converter); realizes m2.l1.converter.fp16: converter, mode 2 lane 1, int8_twos_complement -> fp16, ops cvt(fp16)
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [31:0] y_m2_l1_t6;
  logic [19:0] fl_m2_l1_t6;
  alu_core_m2_converter #(.LANE(1), .TGT(6)) u_m2_l1_t6 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_l1_t6), .fl_m2(fl_m2_l1_t6));
  assign y_m2 = y_m2_l1_t6;
  assign fl_m2 = fl_m2_l1_t6;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m2_l0_converter_fxs1i7f8
// EVOLVE-BLOCK-START
module alu_core_u_m2_l0_converter_fxs1i7f8 (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m2,
  output logic [19:0] fl_m2
);
  // alu_core_u_m2_l0_converter_fxs1i7f8: physical structure `m2.l0.converter.fxs1i7f8` (kind converter, slot converter); realizes m2.l0.converter.fxs1i7f8: converter, mode 2 lane 0, int8_twos_complement -> fxs1i7f8, ops cvt(fxs1i7f8)
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [31:0] y_m2_l0_t7;
  logic [19:0] fl_m2_l0_t7;
  alu_core_m2_converter #(.LANE(0), .TGT(7)) u_m2_l0_t7 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_l0_t7), .fl_m2(fl_m2_l0_t7));
  assign y_m2 = y_m2_l0_t7;
  assign fl_m2 = fl_m2_l0_t7;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m2_l1_converter_fxs1i7f8
// EVOLVE-BLOCK-START
module alu_core_u_m2_l1_converter_fxs1i7f8 (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m2,
  output logic [19:0] fl_m2
);
  // alu_core_u_m2_l1_converter_fxs1i7f8: physical structure `m2.l1.converter.fxs1i7f8` (kind converter, slot converter); realizes m2.l1.converter.fxs1i7f8: converter, mode 2 lane 1, int8_twos_complement -> fxs1i7f8, ops cvt(fxs1i7f8)
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [31:0] y_m2_l1_t7;
  logic [19:0] fl_m2_l1_t7;
  alu_core_m2_converter #(.LANE(1), .TGT(7)) u_m2_l1_t7 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_l1_t7), .fl_m2(fl_m2_l1_t7));
  assign y_m2 = y_m2_l1_t7;
  assign fl_m2 = fl_m2_l1_t7;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m3_l0_adder
// EVOLVE-BLOCK-START
module alu_core_u_m3_l0_adder (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m3,
  output logic [19:0] fl_m3
);
  // alu_core_u_m3_l0_adder: physical structure `m3.l0.adder` (kind adder, slot adder); realizes m3.l0.adder: adder, mode 3 lane 0, fxs1i7f8, ops add
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [15:0] pc_a_m3;
  logic [15:0] pc_b_m3;
  logic pc_cin_m3;
  logic [15:0] pc_s_m3;
  logic pc_co_m3;
  logic [31:0] y_m3_l0;
  logic [19:0] fl_m3_l0;
  logic [15:0] pc_a_m3_l0;
  logic [15:0] pc_b_m3_l0;
  logic pc_cin_m3_l0;
  logic pc_sel;
  logic [15:0] pc_a;
  logic [15:0] pc_b;
  logic pc_cin;
  logic [15:0] pc_s;
  logic pc_co;
  alu_core_m3_adder_sh #(.LANE(0)) u_m3_l0 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m3(y_m3_l0), .fl_m3(fl_m3_l0), .pc_a_m3(pc_a_m3_l0), .pc_b_m3(pc_b_m3_l0), .pc_cin_m3(pc_cin_m3_l0), .pc_s_m3(pc_s_m3), .pc_co_m3(pc_co_m3));
  assign y_m3 = y_m3_l0;
  assign fl_m3 = fl_m3_l0;
  assign pc_a_m3 = pc_a_m3_l0;
  assign pc_b_m3 = pc_b_m3_l0;
  assign pc_cin_m3 = pc_cin_m3_l0;
  assign pc_sel = (mode == 2'd3) ? 1'd0 : '0;
  assign pc_a = (mode == 2'd3) ? pc_a_m3 : '0;
  assign pc_b = (mode == 2'd3) ? pc_b_m3 : '0;
  assign pc_cin = (mode == 2'd3) ? pc_cin_m3 : '0;
  // subword partitioned_carry_chain: one library adder over the whole word, its carries cut at the selected packing's lane boundaries (1 x fxs1i7f8)
  fam_add_partitioned_w16_16_carry_kill_gate_0cc88441ac18 u_part (.a(pc_a), .b(pc_b), .cin(pc_cin), .sel(pc_sel), .s(pc_s), .cout(pc_co));
  assign pc_s_m3 = pc_s;
  assign pc_co_m3 = pc_co;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m3_l0_multiplier
// EVOLVE-BLOCK-START
module alu_core_u_m3_l0_multiplier (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m3,
  output logic [19:0] fl_m3
);
  // alu_core_u_m3_l0_multiplier: physical structure `m3.l0.multiplier` (kind multiplier, slot multiplier); realizes m3.l0.multiplier: multiplier, mode 3 lane 0, fxs1i7f8, ops mul
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [31:0] y_m3_l0;
  logic [19:0] fl_m3_l0;
  alu_core_m3_multiplier #(.LANE(0)) u_m3_l0 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m3(y_m3_l0), .fl_m3(fl_m3_l0));
  assign y_m3 = y_m3_l0;
  assign fl_m3 = fl_m3_l0;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m3_l0_comparator
// EVOLVE-BLOCK-START
module alu_core_u_m3_l0_comparator (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m3,
  output logic [19:0] fl_m3
);
  // alu_core_u_m3_l0_comparator: physical structure `m3.l0.comparator` (kind comparator, slot comparator); realizes m3.l0.comparator: comparator, mode 3 lane 0, fxs1i7f8, ops min
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [31:0] y_m3_l0;
  logic [19:0] fl_m3_l0;
  alu_core_m3_comparator #(.LANE(0)) u_m3_l0 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m3(y_m3_l0), .fl_m3(fl_m3_l0));
  assign y_m3 = y_m3_l0;
  assign fl_m3 = fl_m3_l0;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m3_l0_converter_int8_twos_complement
// EVOLVE-BLOCK-START
module alu_core_u_m3_l0_converter_int8_twos_complement (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m3,
  output logic [19:0] fl_m3
);
  // alu_core_u_m3_l0_converter_int8_twos_complement: physical structure `m3.l0.converter.int8_twos_complement` (kind converter, slot converter); realizes m3.l0.converter.int8_twos_complement: converter, mode 3 lane 0, fxs1i7f8 -> int8_twos_complement, ops cvt(int8)
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [31:0] y_m3_l0_t5;
  logic [19:0] fl_m3_l0_t5;
  alu_core_m3_converter #(.LANE(0), .TGT(5)) u_m3_l0_t5 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m3(y_m3_l0_t5), .fl_m3(fl_m3_l0_t5));
  assign y_m3 = y_m3_l0_t5;
  assign fl_m3 = fl_m3_l0_t5;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m3_l0_converter_fp16
// EVOLVE-BLOCK-START
module alu_core_u_m3_l0_converter_fp16 (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m3,
  output logic [19:0] fl_m3
);
  // alu_core_u_m3_l0_converter_fp16: physical structure `m3.l0.converter.fp16` (kind converter, slot converter); realizes m3.l0.converter.fp16: converter, mode 3 lane 0, fxs1i7f8 -> fp16, ops cvt(fp16)
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [31:0] y_m3_l0_t6;
  logic [19:0] fl_m3_l0_t6;
  alu_core_m3_converter #(.LANE(0), .TGT(6)) u_m3_l0_t6 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m3(y_m3_l0_t6), .fl_m3(fl_m3_l0_t6));
  assign y_m3 = y_m3_l0_t6;
  assign fl_m3 = fl_m3_l0_t6;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m3_l0_converter_fxs1i7f8
// EVOLVE-BLOCK-START
module alu_core_u_m3_l0_converter_fxs1i7f8 (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m3,
  output logic [19:0] fl_m3
);
  // alu_core_u_m3_l0_converter_fxs1i7f8: physical structure `m3.l0.converter.fxs1i7f8` (kind converter, slot converter); realizes m3.l0.converter.fxs1i7f8: converter, mode 3 lane 0, fxs1i7f8 -> fxs1i7f8, ops cvt(fxs1i7f8)
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [31:0] y_m3_l0_t7;
  logic [19:0] fl_m3_l0_t7;
  alu_core_m3_converter #(.LANE(0), .TGT(7)) u_m3_l0_t7 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m3(y_m3_l0_t7), .fl_m3(fl_m3_l0_t7));
  assign y_m3 = y_m3_l0_t7;
  assign fl_m3 = fl_m3_l0_t7;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER library
// ---- the family library modules the lane modules instantiate (chialu/targets/rtl/families; fixed text, replaced by editing the instances)
// partitioned_carry_chain (carry_kill_gate, ripple_carry segments of 16 bits): one adder for the lane packings 1 x 16, the carry cut at the selected mode's lane boundaries
module fam_add_partitioned_w16_16_carry_kill_gate_0cc88441ac18 (input logic [15:0] a, input logic [15:0] b, input logic [0:0] cin, input logic [0:0] sel, output logic [15:0] s, output logic [0:0] cout);
  logic [1:0] c;
  assign c[0] = cin[0];
  logic co0;
  fam_adder_ripple_carry #(.W(16), .CHUNK(1), .FORM(0)) u0 (.a(a[15:0]), .b(b[15:0]), .cin(c[0]), .s(s[15:0]), .cout(co0));
  assign cout[0] = co0;
  assign c[1] = co0;
endmodule


// partitioned_carry_chain (carry_kill_gate, ripple_carry segments of 8 bits): one adder for the lane packings 2 x 8, the carry cut at the selected mode's lane boundaries
module fam_add_partitioned_w16_8_carry_kill_gate_0cc88441ac18 (input logic [15:0] a, input logic [15:0] b, input logic [1:0] cin, input logic [0:0] sel, output logic [15:0] s, output logic [1:0] cout);
  logic [2:0] c;
  assign c[0] = cin[0];
  logic co0;
  fam_adder_ripple_carry #(.W(8), .CHUNK(1), .FORM(0)) u0 (.a(a[7:0]), .b(b[7:0]), .cin(c[0]), .s(s[7:0]), .cout(co0));
  assign cout[0] = co0;
  logic bnd1; assign bnd1 = (sel == 1'd0);
  assign c[1] = (co0 & ~bnd1) | (cin[1] & bnd1);
  logic co1;
  fam_adder_ripple_carry #(.W(8), .CHUNK(1), .FORM(0)) u1 (.a(a[15:8]), .b(b[15:8]), .cin(c[1]), .s(s[15:8]), .cout(co1));
  assign cout[1] = co1;
  assign c[2] = co1;
endmodule


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

// The comparator family of chiALU realized in parametric SystemVerilog:
//   fam_cmp_prefix_comparator #(W, SIGNED, STRUCTURE, RADIX) (input [W-1:0] a, b, output lt, eq)
// The subtractor form (subtractor_comparator) is generated by families/comparator.py around
// the adder of its `subtractor` slot.

// ------------------------------------------------------------ prefix_comparator
// STRUCTURE: 0 msb_first_prefix (a scan from the msb over groups of RADIX bits:
// each group gives (equal, less) flat, the groups are chained msb first), 1
// tree_reduction (a balanced tree of RADIX-ary nodes over the (equal, less)
// pairs). SIGNED flips the sign bits. RADIX is the bits a scan step groups, or
// the arity of a tree node.
module fam_cmp_prefix_comparator #(parameter int W = 16, parameter int SIGNED = 1, parameter int STRUCTURE = 0, parameter int RADIX = 2)
  (input logic [W-1:0] a, input logic [W-1:0] b, output logic lt, output logic eq);
  localparam int R = (RADIX < 2) ? 2 : RADIX;
  localparam int NG = (W + R - 1) / R;                 // the groups of R bits, group g at [g*R +: R] from the lsb
  // ceil(log_r n): the levels of an r-ary tree over n entries
  function automatic int clogr(input int n, input int r);
    int l, p;
    l = 0; p = 1;
    while (p < n) begin p = p * r; l = l + 1; end
    return l;
  endfunction
  // ceil(n / r^l): the entries of level l
  function automatic int entries(input int n, input int r, input int l);
    int m, i;
    m = n;
    for (i = 0; i < l; i = i + 1) m = (m + r - 1) / r;
    return m;
  endfunction
  logic [W-1:0] ax, bx;
  // a signed compare is an unsigned one with the sign bits inverted
  assign ax = {a[W-1] ^ (SIGNED != 0), a[W-2:0]};
  assign bx = {b[W-1] ^ (SIGNED != 0), b[W-2:0]};
  // per bit: equal, less
  logic [W-1:0] e0, l0;
  genvar i, g, l, k;
  generate
    for (i = 0; i < W; i = i + 1) begin : bit_
      assign e0[i] = (ax[i] == bx[i]);
      assign l0[i] = ~ax[i] & bx[i];
    end
    // per group of R bits (flat): equal = every bit equal; less = the first unequal bit from the top is less
    logic [NG-1:0] eg, lg;
    for (g = 0; g < NG; g = g + 1) begin : grp
      localparam int LO = g * R;
      localparam int HI = (LO + R - 1 < W - 1) ? LO + R - 1 : W - 1;
      localparam int N = HI - LO + 1;
      logic [N-1:0] ge, gl;
      assign ge = e0[HI:LO];
      assign gl = l0[HI:LO];
      assign eg[g] = &ge;
      logic [N-1:0] t;
      for (k = 0; k < N; k = k + 1) begin : tk
        // bit LO+k decides when the bits above it in the group are equal
        if (k == N - 1) begin : top
          assign t[k] = gl[k];
        end else begin : low
          assign t[k] = gl[k] & (&ge[N-1:k+1]);
        end
      end
      assign lg[g] = |t;
    end
    if (STRUCTURE == 0) begin : msb_first
      // the scan from the msb group down: e[g]: groups NG-1..g equal; ls[g]: a < b decided within them
      logic [NG:0] e, ls;
      assign e[NG] = 1'b1;
      assign ls[NG] = 1'b0;
      for (g = NG - 1; g >= 0; g = g - 1) begin : scan
        assign e[g] = e[g+1] & eg[g];
        assign ls[g] = ls[g+1] | (e[g+1] & lg[g]);
      end
      assign lt = ls[0];
      assign eq = e[0];
    end else begin : tree
      // a balanced R-ary tree over the group pairs: a node's (equal, less) from its children
      // (child c is more significant than child c-1): equal = AND of the children's equal, less =
      // OR over c of (less_c AND the children above c equal); level l holds ceil(NG / R^l) entries
      localparam int LV = (NG <= 1) ? 1 : clogr(NG, R);
      logic [NG-1:0] E [0:LV];
      logic [NG-1:0] LT [0:LV];
      assign E[0] = eg;
      assign LT[0] = lg;
      for (l = 0; l < LV; l = l + 1) begin : lvl
        localparam int MIN = entries(NG, R, l);       // the entries of the level below
        for (g = 0; g < NG; g = g + 1) begin : node
          if (g * R < MIN) begin : real_
            logic [R-1:0] ce, cl;
            for (k = 0; k < R; k = k + 1) begin : ck
              if (g * R + k < MIN) begin : in_
                assign ce[k] = E[l][g*R + k];
                assign cl[k] = LT[l][g*R + k];
              end else begin : pad
                assign ce[k] = 1'b1;
                assign cl[k] = 1'b0;
              end
            end
            assign E[l+1][g] = &ce;
            logic [R-1:0] t;
            for (k = 0; k < R; k = k + 1) begin : tk
              if (k == R - 1) begin : top
                assign t[k] = cl[k];
              end else begin : low
                assign t[k] = cl[k] & (&ce[R-1:k+1]);
              end
            end
            assign LT[l+1][g] = |t;
          end else begin : pad
            assign E[l+1][g] = 1'b1;
            assign LT[l+1][g] = 1'b0;
          end
        end
      end
      assign lt = LT[LV][0];
      assign eq = E[LV][0];
    end
  endgenerate
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



// lzd_cell_tree (pair_cell, binary_count, valid flags flat): the leading zeros of a 22-bit word
module fam_count_lzd_pair_cell_binary_count_vflat_w22 (input logic [21:0] a, output logic [4:0] n);
  logic v0_0; assign v0_0 = a[21] | a[20];
  logic p0_0; assign p0_0 = ~a[21];
  logic v0_1; assign v0_1 = a[19] | a[18];
  logic p0_1; assign p0_1 = ~a[19];
  logic v0_2; assign v0_2 = a[17] | a[16];
  logic p0_2; assign p0_2 = ~a[17];
  logic v0_3; assign v0_3 = a[15] | a[14];
  logic p0_3; assign p0_3 = ~a[15];
  logic v0_4; assign v0_4 = a[13] | a[12];
  logic p0_4; assign p0_4 = ~a[13];
  logic v0_5; assign v0_5 = a[11] | a[10];
  logic p0_5; assign p0_5 = ~a[11];
  logic v0_6; assign v0_6 = a[9] | a[8];
  logic p0_6; assign p0_6 = ~a[9];
  logic v0_7; assign v0_7 = a[7] | a[6];
  logic p0_7; assign p0_7 = ~a[7];
  logic v0_8; assign v0_8 = a[5] | a[4];
  logic p0_8; assign p0_8 = ~a[5];
  logic v0_9; assign v0_9 = a[3] | a[2];
  logic p0_9; assign p0_9 = ~a[3];
  logic v0_10; assign v0_10 = a[1] | a[0];
  logic p0_10; assign p0_10 = ~a[1];
  logic v0_11; assign v0_11 = 1'b0 | 1'b0;
  logic p0_11; assign p0_11 = ~1'b0;
  logic v0_12; assign v0_12 = 1'b0 | 1'b0;
  logic p0_12; assign p0_12 = ~1'b0;
  logic v0_13; assign v0_13 = 1'b0 | 1'b0;
  logic p0_13; assign p0_13 = ~1'b0;
  logic v0_14; assign v0_14 = 1'b0 | 1'b0;
  logic p0_14; assign p0_14 = ~1'b0;
  logic v0_15; assign v0_15 = 1'b0 | 1'b0;
  logic p0_15; assign p0_15 = ~1'b0;
  logic v1_0; assign v1_0 = a[21] | a[20] | a[19] | a[18];
  logic [1:0] p1_0; assign p1_0 = v0_0 ? {1'b0, p0_0} : {1'b1, p0_1};
  logic v1_1; assign v1_1 = a[17] | a[16] | a[15] | a[14];
  logic [1:0] p1_1; assign p1_1 = v0_2 ? {1'b0, p0_2} : {1'b1, p0_3};
  logic v1_2; assign v1_2 = a[13] | a[12] | a[11] | a[10];
  logic [1:0] p1_2; assign p1_2 = v0_4 ? {1'b0, p0_4} : {1'b1, p0_5};
  logic v1_3; assign v1_3 = a[9] | a[8] | a[7] | a[6];
  logic [1:0] p1_3; assign p1_3 = v0_6 ? {1'b0, p0_6} : {1'b1, p0_7};
  logic v1_4; assign v1_4 = a[5] | a[4] | a[3] | a[2];
  logic [1:0] p1_4; assign p1_4 = v0_8 ? {1'b0, p0_8} : {1'b1, p0_9};
  logic v1_5; assign v1_5 = a[1] | a[0] | 1'b0 | 1'b0;
  logic [1:0] p1_5; assign p1_5 = v0_10 ? {1'b0, p0_10} : {1'b1, p0_11};
  logic v1_6; assign v1_6 = 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [1:0] p1_6; assign p1_6 = v0_12 ? {1'b0, p0_12} : {1'b1, p0_13};
  logic v1_7; assign v1_7 = 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [1:0] p1_7; assign p1_7 = v0_14 ? {1'b0, p0_14} : {1'b1, p0_15};
  logic v2_0; assign v2_0 = a[21] | a[20] | a[19] | a[18] | a[17] | a[16] | a[15] | a[14];
  logic [2:0] p2_0; assign p2_0 = v1_0 ? {1'b0, p1_0} : {1'b1, p1_1};
  logic v2_1; assign v2_1 = a[13] | a[12] | a[11] | a[10] | a[9] | a[8] | a[7] | a[6];
  logic [2:0] p2_1; assign p2_1 = v1_2 ? {1'b0, p1_2} : {1'b1, p1_3};
  logic v2_2; assign v2_2 = a[5] | a[4] | a[3] | a[2] | a[1] | a[0] | 1'b0 | 1'b0;
  logic [2:0] p2_2; assign p2_2 = v1_4 ? {1'b0, p1_4} : {1'b1, p1_5};
  logic v2_3; assign v2_3 = 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [2:0] p2_3; assign p2_3 = v1_6 ? {1'b0, p1_6} : {1'b1, p1_7};
  logic v3_0; assign v3_0 = a[21] | a[20] | a[19] | a[18] | a[17] | a[16] | a[15] | a[14] | a[13] | a[12] | a[11] | a[10] | a[9] | a[8] | a[7] | a[6];
  logic [3:0] p3_0; assign p3_0 = v2_0 ? {1'b0, p2_0} : {1'b1, p2_1};
  logic v3_1; assign v3_1 = a[5] | a[4] | a[3] | a[2] | a[1] | a[0] | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [3:0] p3_1; assign p3_1 = v2_2 ? {1'b0, p2_2} : {1'b1, p2_3};
  logic v4_0; assign v4_0 = a[21] | a[20] | a[19] | a[18] | a[17] | a[16] | a[15] | a[14] | a[13] | a[12] | a[11] | a[10] | a[9] | a[8] | a[7] | a[6] | a[5] | a[4] | a[3] | a[2] | a[1] | a[0] | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [4:0] p4_0; assign p4_0 = v3_0 ? {1'b0, p3_0} : {1'b1, p3_1};
  assign n = v4_0 ? p4_0 : 5'd22;
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



// lzd_cell_tree (pair_cell, binary_count, valid flags flat): the leading zeros of a 38-bit word
module fam_count_lzd_pair_cell_binary_count_vflat_w38 (input logic [37:0] a, output logic [5:0] n);
  logic v0_0; assign v0_0 = a[37] | a[36];
  logic p0_0; assign p0_0 = ~a[37];
  logic v0_1; assign v0_1 = a[35] | a[34];
  logic p0_1; assign p0_1 = ~a[35];
  logic v0_2; assign v0_2 = a[33] | a[32];
  logic p0_2; assign p0_2 = ~a[33];
  logic v0_3; assign v0_3 = a[31] | a[30];
  logic p0_3; assign p0_3 = ~a[31];
  logic v0_4; assign v0_4 = a[29] | a[28];
  logic p0_4; assign p0_4 = ~a[29];
  logic v0_5; assign v0_5 = a[27] | a[26];
  logic p0_5; assign p0_5 = ~a[27];
  logic v0_6; assign v0_6 = a[25] | a[24];
  logic p0_6; assign p0_6 = ~a[25];
  logic v0_7; assign v0_7 = a[23] | a[22];
  logic p0_7; assign p0_7 = ~a[23];
  logic v0_8; assign v0_8 = a[21] | a[20];
  logic p0_8; assign p0_8 = ~a[21];
  logic v0_9; assign v0_9 = a[19] | a[18];
  logic p0_9; assign p0_9 = ~a[19];
  logic v0_10; assign v0_10 = a[17] | a[16];
  logic p0_10; assign p0_10 = ~a[17];
  logic v0_11; assign v0_11 = a[15] | a[14];
  logic p0_11; assign p0_11 = ~a[15];
  logic v0_12; assign v0_12 = a[13] | a[12];
  logic p0_12; assign p0_12 = ~a[13];
  logic v0_13; assign v0_13 = a[11] | a[10];
  logic p0_13; assign p0_13 = ~a[11];
  logic v0_14; assign v0_14 = a[9] | a[8];
  logic p0_14; assign p0_14 = ~a[9];
  logic v0_15; assign v0_15 = a[7] | a[6];
  logic p0_15; assign p0_15 = ~a[7];
  logic v0_16; assign v0_16 = a[5] | a[4];
  logic p0_16; assign p0_16 = ~a[5];
  logic v0_17; assign v0_17 = a[3] | a[2];
  logic p0_17; assign p0_17 = ~a[3];
  logic v0_18; assign v0_18 = a[1] | a[0];
  logic p0_18; assign p0_18 = ~a[1];
  logic v0_19; assign v0_19 = 1'b0 | 1'b0;
  logic p0_19; assign p0_19 = ~1'b0;
  logic v0_20; assign v0_20 = 1'b0 | 1'b0;
  logic p0_20; assign p0_20 = ~1'b0;
  logic v0_21; assign v0_21 = 1'b0 | 1'b0;
  logic p0_21; assign p0_21 = ~1'b0;
  logic v0_22; assign v0_22 = 1'b0 | 1'b0;
  logic p0_22; assign p0_22 = ~1'b0;
  logic v0_23; assign v0_23 = 1'b0 | 1'b0;
  logic p0_23; assign p0_23 = ~1'b0;
  logic v0_24; assign v0_24 = 1'b0 | 1'b0;
  logic p0_24; assign p0_24 = ~1'b0;
  logic v0_25; assign v0_25 = 1'b0 | 1'b0;
  logic p0_25; assign p0_25 = ~1'b0;
  logic v0_26; assign v0_26 = 1'b0 | 1'b0;
  logic p0_26; assign p0_26 = ~1'b0;
  logic v0_27; assign v0_27 = 1'b0 | 1'b0;
  logic p0_27; assign p0_27 = ~1'b0;
  logic v0_28; assign v0_28 = 1'b0 | 1'b0;
  logic p0_28; assign p0_28 = ~1'b0;
  logic v0_29; assign v0_29 = 1'b0 | 1'b0;
  logic p0_29; assign p0_29 = ~1'b0;
  logic v0_30; assign v0_30 = 1'b0 | 1'b0;
  logic p0_30; assign p0_30 = ~1'b0;
  logic v0_31; assign v0_31 = 1'b0 | 1'b0;
  logic p0_31; assign p0_31 = ~1'b0;
  logic v1_0; assign v1_0 = a[37] | a[36] | a[35] | a[34];
  logic [1:0] p1_0; assign p1_0 = v0_0 ? {1'b0, p0_0} : {1'b1, p0_1};
  logic v1_1; assign v1_1 = a[33] | a[32] | a[31] | a[30];
  logic [1:0] p1_1; assign p1_1 = v0_2 ? {1'b0, p0_2} : {1'b1, p0_3};
  logic v1_2; assign v1_2 = a[29] | a[28] | a[27] | a[26];
  logic [1:0] p1_2; assign p1_2 = v0_4 ? {1'b0, p0_4} : {1'b1, p0_5};
  logic v1_3; assign v1_3 = a[25] | a[24] | a[23] | a[22];
  logic [1:0] p1_3; assign p1_3 = v0_6 ? {1'b0, p0_6} : {1'b1, p0_7};
  logic v1_4; assign v1_4 = a[21] | a[20] | a[19] | a[18];
  logic [1:0] p1_4; assign p1_4 = v0_8 ? {1'b0, p0_8} : {1'b1, p0_9};
  logic v1_5; assign v1_5 = a[17] | a[16] | a[15] | a[14];
  logic [1:0] p1_5; assign p1_5 = v0_10 ? {1'b0, p0_10} : {1'b1, p0_11};
  logic v1_6; assign v1_6 = a[13] | a[12] | a[11] | a[10];
  logic [1:0] p1_6; assign p1_6 = v0_12 ? {1'b0, p0_12} : {1'b1, p0_13};
  logic v1_7; assign v1_7 = a[9] | a[8] | a[7] | a[6];
  logic [1:0] p1_7; assign p1_7 = v0_14 ? {1'b0, p0_14} : {1'b1, p0_15};
  logic v1_8; assign v1_8 = a[5] | a[4] | a[3] | a[2];
  logic [1:0] p1_8; assign p1_8 = v0_16 ? {1'b0, p0_16} : {1'b1, p0_17};
  logic v1_9; assign v1_9 = a[1] | a[0] | 1'b0 | 1'b0;
  logic [1:0] p1_9; assign p1_9 = v0_18 ? {1'b0, p0_18} : {1'b1, p0_19};
  logic v1_10; assign v1_10 = 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [1:0] p1_10; assign p1_10 = v0_20 ? {1'b0, p0_20} : {1'b1, p0_21};
  logic v1_11; assign v1_11 = 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [1:0] p1_11; assign p1_11 = v0_22 ? {1'b0, p0_22} : {1'b1, p0_23};
  logic v1_12; assign v1_12 = 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [1:0] p1_12; assign p1_12 = v0_24 ? {1'b0, p0_24} : {1'b1, p0_25};
  logic v1_13; assign v1_13 = 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [1:0] p1_13; assign p1_13 = v0_26 ? {1'b0, p0_26} : {1'b1, p0_27};
  logic v1_14; assign v1_14 = 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [1:0] p1_14; assign p1_14 = v0_28 ? {1'b0, p0_28} : {1'b1, p0_29};
  logic v1_15; assign v1_15 = 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [1:0] p1_15; assign p1_15 = v0_30 ? {1'b0, p0_30} : {1'b1, p0_31};
  logic v2_0; assign v2_0 = a[37] | a[36] | a[35] | a[34] | a[33] | a[32] | a[31] | a[30];
  logic [2:0] p2_0; assign p2_0 = v1_0 ? {1'b0, p1_0} : {1'b1, p1_1};
  logic v2_1; assign v2_1 = a[29] | a[28] | a[27] | a[26] | a[25] | a[24] | a[23] | a[22];
  logic [2:0] p2_1; assign p2_1 = v1_2 ? {1'b0, p1_2} : {1'b1, p1_3};
  logic v2_2; assign v2_2 = a[21] | a[20] | a[19] | a[18] | a[17] | a[16] | a[15] | a[14];
  logic [2:0] p2_2; assign p2_2 = v1_4 ? {1'b0, p1_4} : {1'b1, p1_5};
  logic v2_3; assign v2_3 = a[13] | a[12] | a[11] | a[10] | a[9] | a[8] | a[7] | a[6];
  logic [2:0] p2_3; assign p2_3 = v1_6 ? {1'b0, p1_6} : {1'b1, p1_7};
  logic v2_4; assign v2_4 = a[5] | a[4] | a[3] | a[2] | a[1] | a[0] | 1'b0 | 1'b0;
  logic [2:0] p2_4; assign p2_4 = v1_8 ? {1'b0, p1_8} : {1'b1, p1_9};
  logic v2_5; assign v2_5 = 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [2:0] p2_5; assign p2_5 = v1_10 ? {1'b0, p1_10} : {1'b1, p1_11};
  logic v2_6; assign v2_6 = 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [2:0] p2_6; assign p2_6 = v1_12 ? {1'b0, p1_12} : {1'b1, p1_13};
  logic v2_7; assign v2_7 = 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [2:0] p2_7; assign p2_7 = v1_14 ? {1'b0, p1_14} : {1'b1, p1_15};
  logic v3_0; assign v3_0 = a[37] | a[36] | a[35] | a[34] | a[33] | a[32] | a[31] | a[30] | a[29] | a[28] | a[27] | a[26] | a[25] | a[24] | a[23] | a[22];
  logic [3:0] p3_0; assign p3_0 = v2_0 ? {1'b0, p2_0} : {1'b1, p2_1};
  logic v3_1; assign v3_1 = a[21] | a[20] | a[19] | a[18] | a[17] | a[16] | a[15] | a[14] | a[13] | a[12] | a[11] | a[10] | a[9] | a[8] | a[7] | a[6];
  logic [3:0] p3_1; assign p3_1 = v2_2 ? {1'b0, p2_2} : {1'b1, p2_3};
  logic v3_2; assign v3_2 = a[5] | a[4] | a[3] | a[2] | a[1] | a[0] | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [3:0] p3_2; assign p3_2 = v2_4 ? {1'b0, p2_4} : {1'b1, p2_5};
  logic v3_3; assign v3_3 = 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [3:0] p3_3; assign p3_3 = v2_6 ? {1'b0, p2_6} : {1'b1, p2_7};
  logic v4_0; assign v4_0 = a[37] | a[36] | a[35] | a[34] | a[33] | a[32] | a[31] | a[30] | a[29] | a[28] | a[27] | a[26] | a[25] | a[24] | a[23] | a[22] | a[21] | a[20] | a[19] | a[18] | a[17] | a[16] | a[15] | a[14] | a[13] | a[12] | a[11] | a[10] | a[9] | a[8] | a[7] | a[6];
  logic [4:0] p4_0; assign p4_0 = v3_0 ? {1'b0, p3_0} : {1'b1, p3_1};
  logic v4_1; assign v4_1 = a[5] | a[4] | a[3] | a[2] | a[1] | a[0] | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [4:0] p4_1; assign p4_1 = v3_2 ? {1'b0, p3_2} : {1'b1, p3_3};
  logic v5_0; assign v5_0 = a[37] | a[36] | a[35] | a[34] | a[33] | a[32] | a[31] | a[30] | a[29] | a[28] | a[27] | a[26] | a[25] | a[24] | a[23] | a[22] | a[21] | a[20] | a[19] | a[18] | a[17] | a[16] | a[15] | a[14] | a[13] | a[12] | a[11] | a[10] | a[9] | a[8] | a[7] | a[6] | a[5] | a[4] | a[3] | a[2] | a[1] | a[0] | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [5:0] p5_0; assign p5_0 = v4_0 ? {1'b0, p4_0} : {1'b1, p4_1};
  assign n = v5_0 ? p5_0 : 6'd38;
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

// fp rounder (shift_round_convert, rounding increment_adder, leading zeros lzd_cell_tree, shifts barrel_mux_tree, exponent ripple_carry / prefix_and_incrementer): X -> fp16 pattern and flags
module fam_fp_round_shift_round_convert_increment_adder_fp16_x26e13s11_pd77ccc5b5c45 (
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


// fp rounder (shift_round_convert, rounding increment_adder, leading zeros lzd_cell_tree, shifts barrel_mux_tree, exponent ripple_carry / prefix_and_incrementer): X -> fp16 pattern and flags
module fam_int_cvt_shift_round_convert_fp16_x22e13s9 (
  input logic [38:0] x,
  input logic [2:0] rnd,
  input logic [7:0] word,
  input logic ftz,
  output logic [9:0] fl,
  output logic [15:0] bits
);
  logic [1:0] x_sp; assign x_sp = x[38:37];
  logic x_s; assign x_s = x[36];
  logic signed [12:0] x_e; assign x_e = $signed(x[35:23]);
  logic [21:0] x_sig; assign x_sig = x[22:1];
  logic x_st; assign x_st = x[0];
  logic x_z; assign x_z = (x_sp == 2'd0) && (x_sig == 0) && !x_st;
  logic s; assign s = x_s & 1'd1;
  logic lone; assign lone = (x_sig == 0) && x_st;
  logic [21:0] sig_in; assign sig_in = lone ? 22'd1 : x_sig;
  logic signed [12:0] e_lone_c; assign e_lone_c = -13'sd22;
  logic signed [12:0] e_lone;
  // the exponent of a lone sticky's unit
  fam_adder_ripple_carry #(.W(13), .CHUNK(1), .FORM(0)) u1 (.a(x_e), .b(e_lone_c), .cin(1'b0), .s(e_lone), .cout());
  logic signed [12:0] e_in; assign e_in = lone ? e_lone : x_e;
  logic [4:0] lz;
  // the normalizer's leading-zero count
  fam_count_lzd_pair_cell_binary_count_vflat_w22 u2 (.a(sig_in), .n(lz));
  logic [4:0] lzs; assign lzs = (sig_in == 0) ? 5'd0 : lz[4:0];
  logic [21:0] sig;
  // the normalizer's left shift
  fam_shift_barrel_mux_tree #(.W(22), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u3 (.a(sig_in), .amt(lzs), .op(3'd0), .y(sig), .sticky());
  logic signed [12:0] lzx; assign lzx = $signed({{(13-5){1'b0}}, lzs});
  logic [12:0] e_nb; assign e_nb = ~(lzx);
  logic signed [12:0] e;
  // the exponent lowered by the normalize count
  fam_adder_ripple_carry #(.W(13), .CHUNK(1), .FORM(0)) u4 (.a(e_in), .b(e_nb), .cin(1'b1), .s(e), .cout());
  logic normal; assign normal = e >= -13'sd35;
  logic signed [13:0] shc; assign shc = -14'sd24;
  logic signed [13:0] ex; assign ex = $signed({e[12], e});
  logic [13:0] shsub_nb; assign shsub_nb = ~(ex);
  logic signed [13:0] shsub;
  // the subnormal result's extra right shift
  fam_adder_ripple_carry #(.W(14), .CHUNK(1), .FORM(0)) u5 (.a(shc), .b(shsub_nb), .cin(1'b1), .s(shsub), .cout());
  logic signed [13:0] sht; assign sht = normal ? 14'sd11 : shsub;
  logic signed [13:0] sh; assign sh = (sht > 14'sd23) ? 14'sd23 : sht;
  logic [4:0] sha; assign sha = sh[4:0];
  logic [22:0] sigw; assign sigw = {1'b0, sig};
  logic [4:0] shk; assign shk = (sh > 14'sd22) ? 5'd22 : sha;
  logic [22:0] keep;
  // the right shift to the kept bits
  fam_shift_barrel_mux_tree #(.W(23), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u6 (.a(sigw), .amt(shk), .op(3'd1), .y(keep), .sticky());
  // the mask of the dropped positions
  logic [22:0] restmask;
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
  logic [22:0] rest; assign rest = sigw & restmask;
  // the half position (one below the kept lsb)
  logic [22:0] halfv;
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
  logic [22:0] keepn; assign keepn = sigw >> 11;
  logic [22:0] restn; assign restn = sigw & ({1'b0, {22{1'b1}}} >> 11);
  logic [22:0] halfn; assign halfn = {22'd0, 1'b1} << 10;
  logic inexact; assign inexact = (rest != 0) | x_st;
  logic [30:0] restw; assign restw = {rest, 8'd0};
  logic [4:0] fsh; assign fsh = sht[4:0];
  logic [30:0] fint0;
  // the dropped bits aligned to the stochastic word
  fam_shift_barrel_mux_tree #(.W(31), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u7 (.a(restw), .amt(fsh), .op(3'd1), .y(fint0), .sticky());
  logic [30:0] fint; assign fint = (sht > 14'sd30) ? 31'd0 : fint0;
  logic [30:0] fintn; assign fintn = restn >> 3;
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
  logic [22:0] mag;
  logic [22:0] mag0;
  // the rounding increment (prefix_and_incrementer)
  fam_incr_prefix_and #(.W(23), .STRUCTURE(0), .B(4), .TOPO(0)) u8 (.a(keep), .cin(upr), .s(mag0), .cout());
  assign mag = mag0;
  logic signed [12:0] bfield_c; assign bfield_c = 13'sd36;
  logic signed [12:0] bfield;
  // the biased exponent field
  fam_adder_ripple_carry #(.W(13), .CHUNK(1), .FORM(0)) u9 (.a(e), .b(bfield_c), .cin(1'b0), .s(bfield), .cout());
  logic [12:0] bfu; assign bfu = bfield;
  logic [12:0] efield;
  // the exponent field incremented on a rounding carry (prefix_and_incrementer)
  fam_incr_prefix_and #(.W(13), .STRUCTURE(0), .B(4), .TOPO(0)) u10 (.a(bfu), .cin(mag[11]), .s(efield), .cout());
  logic [29:0] code; assign code = normal ? {{(30-13-10){1'b0}}, efield, mag[9:0]} : {{(30-23){1'b0}}, mag};
  logic tiny; assign tiny = (e < -13'sd35) && !(e == -13'sd36 && carry_n) && !(e == -13'sd36 && carry_n);
  logic ovf; assign ovf = code > 30'd31743;
  logic to_inf; assign to_inf = 1 && (rnd == 3'd0 || (rnd == 3'd3 && !s) || (rnd == 3'd2 && s) || rnd == 3'd5 || (rnd == 3'd4 && (e > -13'sd6 || up)));
  logic ftz_hit; assign ftz_hit = ftz && code[14:10] == 0 && (code[9:0] != 0);
  logic is_zero; assign is_zero = (x_sig == 0) && (!x_st || rounded);
  logic tiny_r; assign tiny_r = rounded ? x_st : tiny;
  logic [9:0] fl_fin; assign fl_fin = ovf ? ((1 << 2) | (1 << 4)) : ((inexact_r ? (1 << 4) : 0) | ((tiny_r && inexact_r) ? (1 << 3) : 0) | (ftz_hit ? ((1 << 4) | (1 << 3)) : 0));
  logic [15:0] bits_fin; assign bits_fin = ovf ? (to_inf ? {s, 15'd31744} : {s, 15'd31743}) : (ftz_hit ? {s, 15'd0} : {s, code[14:0]});
  logic [9:0] fl_zero; assign fl_zero = rounded ? ((1 << 4) | (1 << 3)) : 10'd0;
  assign fl = (x_sp == 2'd1) ? (1 << 5) : (x_sp == 2'd2) ? 0 : is_zero ? fl_zero : fl_fin;
  assign bits = (x_sp == 2'd1) ? 16'd32256 : (x_sp == 2'd2) ? {s, 15'd31744} : is_zero ? (rounded ? {s, 15'd0} : 16'd0) : bits_fin;
endmodule

// fp rounder (shift_round_convert, rounding increment_adder, leading zeros lzd_cell_tree, shifts barrel_mux_tree, exponent ripple_carry / prefix_and_incrementer): X -> fp16 pattern and flags
module fam_int_cvt_shift_round_convert_fp16_x38e13s17 (
  input logic [54:0] x,
  input logic [2:0] rnd,
  input logic [7:0] word,
  input logic ftz,
  output logic [9:0] fl,
  output logic [15:0] bits
);
  logic [1:0] x_sp; assign x_sp = x[54:53];
  logic x_s; assign x_s = x[52];
  logic signed [12:0] x_e; assign x_e = $signed(x[51:39]);
  logic [37:0] x_sig; assign x_sig = x[38:1];
  logic x_st; assign x_st = x[0];
  logic x_z; assign x_z = (x_sp == 2'd0) && (x_sig == 0) && !x_st;
  logic s; assign s = x_s & 1'd1;
  logic lone; assign lone = (x_sig == 0) && x_st;
  logic [37:0] sig_in; assign sig_in = lone ? 38'd1 : x_sig;
  logic signed [12:0] e_lone_c; assign e_lone_c = -13'sd38;
  logic signed [12:0] e_lone;
  // the exponent of a lone sticky's unit
  fam_adder_ripple_carry #(.W(13), .CHUNK(1), .FORM(0)) u1 (.a(x_e), .b(e_lone_c), .cin(1'b0), .s(e_lone), .cout());
  logic signed [12:0] e_in; assign e_in = lone ? e_lone : x_e;
  logic [5:0] lz;
  // the normalizer's leading-zero count
  fam_count_lzd_pair_cell_binary_count_vflat_w38 u2 (.a(sig_in), .n(lz));
  logic [5:0] lzs; assign lzs = (sig_in == 0) ? 6'd0 : lz[5:0];
  logic [37:0] sig;
  // the normalizer's left shift
  fam_shift_barrel_mux_tree #(.W(38), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u3 (.a(sig_in), .amt(lzs), .op(3'd0), .y(sig), .sticky());
  logic signed [12:0] lzx; assign lzx = $signed({{(13-6){1'b0}}, lzs});
  logic [12:0] e_nb; assign e_nb = ~(lzx);
  logic signed [12:0] e;
  // the exponent lowered by the normalize count
  fam_adder_ripple_carry #(.W(13), .CHUNK(1), .FORM(0)) u4 (.a(e_in), .b(e_nb), .cin(1'b1), .s(e), .cout());
  logic normal; assign normal = e >= -13'sd51;
  logic signed [13:0] shc; assign shc = -14'sd24;
  logic signed [13:0] ex; assign ex = $signed({e[12], e});
  logic [13:0] shsub_nb; assign shsub_nb = ~(ex);
  logic signed [13:0] shsub;
  // the subnormal result's extra right shift
  fam_adder_ripple_carry #(.W(14), .CHUNK(1), .FORM(0)) u5 (.a(shc), .b(shsub_nb), .cin(1'b1), .s(shsub), .cout());
  logic signed [13:0] sht; assign sht = normal ? 14'sd27 : shsub;
  logic signed [13:0] sh; assign sh = (sht > 14'sd39) ? 14'sd39 : sht;
  logic [5:0] sha; assign sha = sh[5:0];
  logic [38:0] sigw; assign sigw = {1'b0, sig};
  logic [5:0] shk; assign shk = (sh > 14'sd38) ? 6'd38 : sha;
  logic [38:0] keep;
  // the right shift to the kept bits
  fam_shift_barrel_mux_tree #(.W(39), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u6 (.a(sigw), .amt(shk), .op(3'd1), .y(keep), .sticky());
  // the mask of the dropped positions
  logic [38:0] restmask;
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
  assign restmask[27] = (sha > 27);
  assign restmask[28] = (sha > 28);
  assign restmask[29] = (sha > 29);
  assign restmask[30] = (sha > 30);
  assign restmask[31] = (sha > 31);
  assign restmask[32] = (sha > 32);
  assign restmask[33] = (sha > 33);
  assign restmask[34] = (sha > 34);
  assign restmask[35] = (sha > 35);
  assign restmask[36] = (sha > 36);
  assign restmask[37] = (sha > 37);
  assign restmask[38] = (sha > 38);
  logic [38:0] rest; assign rest = sigw & restmask;
  // the half position (one below the kept lsb)
  logic [38:0] halfv;
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
  assign halfv[27] = (sha == 28);
  assign halfv[28] = (sha == 29);
  assign halfv[29] = (sha == 30);
  assign halfv[30] = (sha == 31);
  assign halfv[31] = (sha == 32);
  assign halfv[32] = (sha == 33);
  assign halfv[33] = (sha == 34);
  assign halfv[34] = (sha == 35);
  assign halfv[35] = (sha == 36);
  assign halfv[36] = (sha == 37);
  assign halfv[37] = (sha == 38);
  assign halfv[38] = (sha == 39);
  logic [38:0] keepn; assign keepn = sigw >> 27;
  logic [38:0] restn; assign restn = sigw & ({1'b0, {38{1'b1}}} >> 11);
  logic [38:0] halfn; assign halfn = {38'd0, 1'b1} << 26;
  logic inexact; assign inexact = (rest != 0) | x_st;
  logic [46:0] restw; assign restw = {rest, 8'd0};
  logic [5:0] fsh; assign fsh = sht[5:0];
  logic [46:0] fint0;
  // the dropped bits aligned to the stochastic word
  fam_shift_barrel_mux_tree #(.W(47), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u7 (.a(restw), .amt(fsh), .op(3'd1), .y(fint0), .sticky());
  logic [46:0] fint; assign fint = (sht > 14'sd46) ? 47'd0 : fint0;
  logic [46:0] fintn; assign fintn = restn >> 19;
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
  logic [38:0] mag;
  logic [38:0] mag0;
  // the rounding increment (prefix_and_incrementer)
  fam_incr_prefix_and #(.W(39), .STRUCTURE(0), .B(4), .TOPO(0)) u8 (.a(keep), .cin(upr), .s(mag0), .cout());
  assign mag = mag0;
  logic signed [12:0] bfield_c; assign bfield_c = 13'sd52;
  logic signed [12:0] bfield;
  // the biased exponent field
  fam_adder_ripple_carry #(.W(13), .CHUNK(1), .FORM(0)) u9 (.a(e), .b(bfield_c), .cin(1'b0), .s(bfield), .cout());
  logic [12:0] bfu; assign bfu = bfield;
  logic [12:0] efield;
  // the exponent field incremented on a rounding carry (prefix_and_incrementer)
  fam_incr_prefix_and #(.W(13), .STRUCTURE(0), .B(4), .TOPO(0)) u10 (.a(bfu), .cin(mag[11]), .s(efield), .cout());
  logic [39:0] code; assign code = normal ? {{(40-13-10){1'b0}}, efield, mag[9:0]} : {{(40-39){1'b0}}, mag};
  logic tiny; assign tiny = (e < -13'sd51) && !(e == -13'sd52 && carry_n) && !(e == -13'sd52 && carry_n);
  logic ovf; assign ovf = code > 40'd31743;
  logic to_inf; assign to_inf = 1 && (rnd == 3'd0 || (rnd == 3'd3 && !s) || (rnd == 3'd2 && s) || rnd == 3'd5 || (rnd == 3'd4 && (e > -13'sd22 || up)));
  logic ftz_hit; assign ftz_hit = ftz && code[14:10] == 0 && (code[9:0] != 0);
  logic is_zero; assign is_zero = (x_sig == 0) && (!x_st || rounded);
  logic tiny_r; assign tiny_r = rounded ? x_st : tiny;
  logic [9:0] fl_fin; assign fl_fin = ovf ? ((1 << 2) | (1 << 4)) : ((inexact_r ? (1 << 4) : 0) | ((tiny_r && inexact_r) ? (1 << 3) : 0) | (ftz_hit ? ((1 << 4) | (1 << 3)) : 0));
  logic [15:0] bits_fin; assign bits_fin = ovf ? (to_inf ? {s, 15'd31744} : {s, 15'd31743}) : (ftz_hit ? {s, 15'd0} : {s, code[14:0]});
  logic [9:0] fl_zero; assign fl_zero = rounded ? ((1 << 4) | (1 << 3)) : 10'd0;
  assign fl = (x_sp == 2'd1) ? (1 << 5) : (x_sp == 2'd2) ? 0 : is_zero ? fl_zero : fl_fin;
  assign bits = (x_sp == 2'd1) ? 16'd32256 : (x_sp == 2'd2) ? {s, 15'd31744} : is_zero ? (rounded ? {s, 15'd0} : 16'd0) : bits_fin;
endmodule

// shift_round_convert: X to fxs1i7f8, selected normalizer, shifters and rounding datapath
module fam_int_cvt_shift_round_convert_fxs1i7f8_x22e13s9 (
  input logic [38:0] x,
  input logic [2:0] rnd,
  input logic [7:0] word,
  input logic ftz,
  output logic [9:0] fl,
  output logic [15:0] bits
);
  logic [1:0] x_sp; assign x_sp = x[38:37];
  logic x_s; assign x_s = x[36];
  logic signed [12:0] x_e; assign x_e = $signed(x[35:23]);
  logic [21:0] x_sig; assign x_sig = x[22:1];
  logic x_st; assign x_st = x[0];
  logic x_z; assign x_z = (x_sp == 2'd0) && (x_sig == 0) && !x_st;
  logic lone; assign lone = x_sig == 0 && x_st;
  logic [21:0] sig_in; assign sig_in = lone ? 22'd1 : x_sig;
  logic [4:0] lz;
  // normalize the source significand
  fam_count_lzd_pair_cell_binary_count_vflat_w22 u1 (.a(sig_in), .n(lz));
  logic [4:0] lzs; assign lzs = sig_in == 0 ? 5'd0 : lz[4:0];
  logic [21:0] sig;
  // place the leading one at the normalizer output
  fam_shift_barrel_mux_tree #(.W(22), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u2 (.a(sig_in), .amt(lzs), .op(3'd0), .y(sig), .sticky());
  logic signed [13:0] xe; assign xe = {x_e[12], x_e};
  logic [13:0] lzx; assign lzx = {{9{1'b0}}, lzs};
  logic [13:0] enorm_nb; assign enorm_nb = ~(lzx);
  logic signed [13:0] enorm;
  // normalization exponent adjustment
  fam_adder_ripple_carry #(.W(14), .CHUNK(1), .FORM(0)) u3 (.a(xe), .b(enorm_nb), .cin(1'b1), .s(enorm), .cout());
  logic signed [13:0] offset; assign offset = lone ? -14'sd14 : 14'sd8;
  logic signed [13:0] pe;
  // target fractional-bit scale
  fam_adder_ripple_carry #(.W(14), .CHUNK(1), .FORM(0)) u4 (.a(enorm), .b(offset), .cin(1'b0), .s(pe), .cout());
  logic [13:0] pen; assign pen = ~pe;
  logic [13:0] negpe;
  // two's-complement right-shift distance
  fam_incr_prefix_and #(.W(14), .STRUCTURE(0), .B(4), .TOPO(0)) u5 (.a(pen), .cin(1'b1), .s(negpe), .cout());
  logic right; assign right = pe[13];
  logic [13:0] distance; assign distance = right ? negpe : pe;
  logic [5:0] amount; assign amount = distance >= 14'd41 ? 6'd40 : distance[5:0];
  logic [40:0] sigw; assign sigw = {{19{1'b0}}, sig};
  logic [40:0] aligned;
  // align to the target's fixed least-significant bit
  fam_shift_barrel_mux_tree #(.W(41), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u6 (.a(sigw), .amt(amount), .op({2'd0, right}), .y(aligned), .sticky());
  logic [40:0] keep; assign keep = right && distance >= 14'd41 ? 41'd0 : aligned;
  logic big; assign big = !right && distance > 14'd18;
  // positions discarded by the right shift
  logic [40:0] restmask0;
  assign restmask0[0] = (amount > 0);
  assign restmask0[1] = (amount > 1);
  assign restmask0[2] = (amount > 2);
  assign restmask0[3] = (amount > 3);
  assign restmask0[4] = (amount > 4);
  assign restmask0[5] = (amount > 5);
  assign restmask0[6] = (amount > 6);
  assign restmask0[7] = (amount > 7);
  assign restmask0[8] = (amount > 8);
  assign restmask0[9] = (amount > 9);
  assign restmask0[10] = (amount > 10);
  assign restmask0[11] = (amount > 11);
  assign restmask0[12] = (amount > 12);
  assign restmask0[13] = (amount > 13);
  assign restmask0[14] = (amount > 14);
  assign restmask0[15] = (amount > 15);
  assign restmask0[16] = (amount > 16);
  assign restmask0[17] = (amount > 17);
  assign restmask0[18] = (amount > 18);
  assign restmask0[19] = (amount > 19);
  assign restmask0[20] = (amount > 20);
  assign restmask0[21] = (amount > 21);
  assign restmask0[22] = (amount > 22);
  assign restmask0[23] = (amount > 23);
  assign restmask0[24] = (amount > 24);
  assign restmask0[25] = (amount > 25);
  assign restmask0[26] = (amount > 26);
  assign restmask0[27] = (amount > 27);
  assign restmask0[28] = (amount > 28);
  assign restmask0[29] = (amount > 29);
  assign restmask0[30] = (amount > 30);
  assign restmask0[31] = (amount > 31);
  assign restmask0[32] = (amount > 32);
  assign restmask0[33] = (amount > 33);
  assign restmask0[34] = (amount > 34);
  assign restmask0[35] = (amount > 35);
  assign restmask0[36] = (amount > 36);
  assign restmask0[37] = (amount > 37);
  assign restmask0[38] = (amount > 38);
  assign restmask0[39] = (amount > 39);
  assign restmask0[40] = (amount > 40);
  logic [40:0] restmask; assign restmask = !right ? 41'd0 : distance >= 14'd41 ? {41{1'b1}} : restmask0;
  logic [40:0] rest; assign rest = sigw & restmask;
  // half of the target least-significant bit
  logic [40:0] half0;
  assign half0[0] = (amount == 1);
  assign half0[1] = (amount == 2);
  assign half0[2] = (amount == 3);
  assign half0[3] = (amount == 4);
  assign half0[4] = (amount == 5);
  assign half0[5] = (amount == 6);
  assign half0[6] = (amount == 7);
  assign half0[7] = (amount == 8);
  assign half0[8] = (amount == 9);
  assign half0[9] = (amount == 10);
  assign half0[10] = (amount == 11);
  assign half0[11] = (amount == 12);
  assign half0[12] = (amount == 13);
  assign half0[13] = (amount == 14);
  assign half0[14] = (amount == 15);
  assign half0[15] = (amount == 16);
  assign half0[16] = (amount == 17);
  assign half0[17] = (amount == 18);
  assign half0[18] = (amount == 19);
  assign half0[19] = (amount == 20);
  assign half0[20] = (amount == 21);
  assign half0[21] = (amount == 22);
  assign half0[22] = (amount == 23);
  assign half0[23] = (amount == 24);
  assign half0[24] = (amount == 25);
  assign half0[25] = (amount == 26);
  assign half0[26] = (amount == 27);
  assign half0[27] = (amount == 28);
  assign half0[28] = (amount == 29);
  assign half0[29] = (amount == 30);
  assign half0[30] = (amount == 31);
  assign half0[31] = (amount == 32);
  assign half0[32] = (amount == 33);
  assign half0[33] = (amount == 34);
  assign half0[34] = (amount == 35);
  assign half0[35] = (amount == 36);
  assign half0[36] = (amount == 37);
  assign half0[37] = (amount == 38);
  assign half0[38] = (amount == 39);
  assign half0[39] = (amount == 40);
  assign half0[40] = (amount == 41);
  logic [40:0] halfv; assign halfv = !right ? 41'd0 : distance >= 14'd41 ? (41'd1 << 40) : half0;
  logic [48:0] restw; assign restw = {rest, 8'd0};
  logic [5:0] famt; assign famt = distance >= 14'd49 ? 6'd48 : distance[5:0];
  logic [48:0] fint0;
  // align discarded bits with the stochastic word
  fam_shift_barrel_mux_tree #(.W(49), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u7 (.a(restw), .amt(famt), .op(3'd1), .y(fint0), .sticky());
  logic [48:0] fint; assign fint = !right || distance >= 14'd49 ? 49'd0 : fint0;
  logic inexact; assign inexact = rest != 0 || x_st;
  logic tie; assign tie = rest == halfv && halfv != 0;
  logic up; assign up = rnd == 0 ? (rest > halfv || (tie && (x_st || keep[0]))) : rnd == 1 ? 1'b0 : rnd == 2 ? (inexact && x_s) : rnd == 3 ? (inexact && !x_s) : rnd == 4 ? (inexact && (0 ? fint >= word : fint > word)) : inexact;
  logic [40:0] incremented;
  // rounding increment
  fam_incr_prefix_and #(.W(41), .STRUCTURE(0), .B(4), .TOPO(0)) u8 (.a(keep), .cin(up), .s(incremented), .cout());
  logic [40:0] mag; assign mag = incremented;
  logic negative; assign negative = x_s && (mag != 0 || big);
  logic overflow; assign overflow = big || (negative ? mag > 41'd32768 : mag > 41'd32767);
  logic [40:0] finite; assign finite = overflow ? (negative ? 41'd32768 : 41'd32767) : mag;
  logic [40:0] t; assign t = x_sp == 1 ? 41'd0 : x_sp == 2 ? (x_s ? 41'd32768 : 41'd32767) : finite;
  logic neg; assign neg = x_sp == 1 ? 1'b0 : x_sp == 2 ? x_s : negative;
  assign bits = neg ? (~t[15:0] + 1'b1) : t[15:0];
  assign fl = x_sp != 0 ? (1 << 0) : overflow ? ((1 << 0) | (1 << 2) | (1 << 4)) : inexact ? (1 << 4) : 0;
endmodule

// shift_round_convert: X to fxs1i7f8, selected normalizer, shifters and rounding datapath
module fam_int_cvt_shift_round_convert_fxs1i7f8_x38e13s17 (
  input logic [54:0] x,
  input logic [2:0] rnd,
  input logic [7:0] word,
  input logic ftz,
  output logic [9:0] fl,
  output logic [15:0] bits
);
  logic [1:0] x_sp; assign x_sp = x[54:53];
  logic x_s; assign x_s = x[52];
  logic signed [12:0] x_e; assign x_e = $signed(x[51:39]);
  logic [37:0] x_sig; assign x_sig = x[38:1];
  logic x_st; assign x_st = x[0];
  logic x_z; assign x_z = (x_sp == 2'd0) && (x_sig == 0) && !x_st;
  logic lone; assign lone = x_sig == 0 && x_st;
  logic [37:0] sig_in; assign sig_in = lone ? 38'd1 : x_sig;
  logic [5:0] lz;
  // normalize the source significand
  fam_count_lzd_pair_cell_binary_count_vflat_w38 u1 (.a(sig_in), .n(lz));
  logic [5:0] lzs; assign lzs = sig_in == 0 ? 6'd0 : lz[5:0];
  logic [37:0] sig;
  // place the leading one at the normalizer output
  fam_shift_barrel_mux_tree #(.W(38), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u2 (.a(sig_in), .amt(lzs), .op(3'd0), .y(sig), .sticky());
  logic signed [13:0] xe; assign xe = {x_e[12], x_e};
  logic [13:0] lzx; assign lzx = {{8{1'b0}}, lzs};
  logic [13:0] enorm_nb; assign enorm_nb = ~(lzx);
  logic signed [13:0] enorm;
  // normalization exponent adjustment
  fam_adder_ripple_carry #(.W(14), .CHUNK(1), .FORM(0)) u3 (.a(xe), .b(enorm_nb), .cin(1'b1), .s(enorm), .cout());
  logic signed [13:0] offset; assign offset = lone ? -14'sd30 : 14'sd8;
  logic signed [13:0] pe;
  // target fractional-bit scale
  fam_adder_ripple_carry #(.W(14), .CHUNK(1), .FORM(0)) u4 (.a(enorm), .b(offset), .cin(1'b0), .s(pe), .cout());
  logic [13:0] pen; assign pen = ~pe;
  logic [13:0] negpe;
  // two's-complement right-shift distance
  fam_incr_prefix_and #(.W(14), .STRUCTURE(0), .B(4), .TOPO(0)) u5 (.a(pen), .cin(1'b1), .s(negpe), .cout());
  logic right; assign right = pe[13];
  logic [13:0] distance; assign distance = right ? negpe : pe;
  logic [5:0] amount; assign amount = distance >= 14'd57 ? 6'd56 : distance[5:0];
  logic [56:0] sigw; assign sigw = {{19{1'b0}}, sig};
  logic [56:0] aligned;
  // align to the target's fixed least-significant bit
  fam_shift_barrel_mux_tree #(.W(57), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u6 (.a(sigw), .amt(amount), .op({2'd0, right}), .y(aligned), .sticky());
  logic [56:0] keep; assign keep = right && distance >= 14'd57 ? 57'd0 : aligned;
  logic big; assign big = !right && distance > 14'd18;
  // positions discarded by the right shift
  logic [56:0] restmask0;
  assign restmask0[0] = (amount > 0);
  assign restmask0[1] = (amount > 1);
  assign restmask0[2] = (amount > 2);
  assign restmask0[3] = (amount > 3);
  assign restmask0[4] = (amount > 4);
  assign restmask0[5] = (amount > 5);
  assign restmask0[6] = (amount > 6);
  assign restmask0[7] = (amount > 7);
  assign restmask0[8] = (amount > 8);
  assign restmask0[9] = (amount > 9);
  assign restmask0[10] = (amount > 10);
  assign restmask0[11] = (amount > 11);
  assign restmask0[12] = (amount > 12);
  assign restmask0[13] = (amount > 13);
  assign restmask0[14] = (amount > 14);
  assign restmask0[15] = (amount > 15);
  assign restmask0[16] = (amount > 16);
  assign restmask0[17] = (amount > 17);
  assign restmask0[18] = (amount > 18);
  assign restmask0[19] = (amount > 19);
  assign restmask0[20] = (amount > 20);
  assign restmask0[21] = (amount > 21);
  assign restmask0[22] = (amount > 22);
  assign restmask0[23] = (amount > 23);
  assign restmask0[24] = (amount > 24);
  assign restmask0[25] = (amount > 25);
  assign restmask0[26] = (amount > 26);
  assign restmask0[27] = (amount > 27);
  assign restmask0[28] = (amount > 28);
  assign restmask0[29] = (amount > 29);
  assign restmask0[30] = (amount > 30);
  assign restmask0[31] = (amount > 31);
  assign restmask0[32] = (amount > 32);
  assign restmask0[33] = (amount > 33);
  assign restmask0[34] = (amount > 34);
  assign restmask0[35] = (amount > 35);
  assign restmask0[36] = (amount > 36);
  assign restmask0[37] = (amount > 37);
  assign restmask0[38] = (amount > 38);
  assign restmask0[39] = (amount > 39);
  assign restmask0[40] = (amount > 40);
  assign restmask0[41] = (amount > 41);
  assign restmask0[42] = (amount > 42);
  assign restmask0[43] = (amount > 43);
  assign restmask0[44] = (amount > 44);
  assign restmask0[45] = (amount > 45);
  assign restmask0[46] = (amount > 46);
  assign restmask0[47] = (amount > 47);
  assign restmask0[48] = (amount > 48);
  assign restmask0[49] = (amount > 49);
  assign restmask0[50] = (amount > 50);
  assign restmask0[51] = (amount > 51);
  assign restmask0[52] = (amount > 52);
  assign restmask0[53] = (amount > 53);
  assign restmask0[54] = (amount > 54);
  assign restmask0[55] = (amount > 55);
  assign restmask0[56] = (amount > 56);
  logic [56:0] restmask; assign restmask = !right ? 57'd0 : distance >= 14'd57 ? {57{1'b1}} : restmask0;
  logic [56:0] rest; assign rest = sigw & restmask;
  // half of the target least-significant bit
  logic [56:0] half0;
  assign half0[0] = (amount == 1);
  assign half0[1] = (amount == 2);
  assign half0[2] = (amount == 3);
  assign half0[3] = (amount == 4);
  assign half0[4] = (amount == 5);
  assign half0[5] = (amount == 6);
  assign half0[6] = (amount == 7);
  assign half0[7] = (amount == 8);
  assign half0[8] = (amount == 9);
  assign half0[9] = (amount == 10);
  assign half0[10] = (amount == 11);
  assign half0[11] = (amount == 12);
  assign half0[12] = (amount == 13);
  assign half0[13] = (amount == 14);
  assign half0[14] = (amount == 15);
  assign half0[15] = (amount == 16);
  assign half0[16] = (amount == 17);
  assign half0[17] = (amount == 18);
  assign half0[18] = (amount == 19);
  assign half0[19] = (amount == 20);
  assign half0[20] = (amount == 21);
  assign half0[21] = (amount == 22);
  assign half0[22] = (amount == 23);
  assign half0[23] = (amount == 24);
  assign half0[24] = (amount == 25);
  assign half0[25] = (amount == 26);
  assign half0[26] = (amount == 27);
  assign half0[27] = (amount == 28);
  assign half0[28] = (amount == 29);
  assign half0[29] = (amount == 30);
  assign half0[30] = (amount == 31);
  assign half0[31] = (amount == 32);
  assign half0[32] = (amount == 33);
  assign half0[33] = (amount == 34);
  assign half0[34] = (amount == 35);
  assign half0[35] = (amount == 36);
  assign half0[36] = (amount == 37);
  assign half0[37] = (amount == 38);
  assign half0[38] = (amount == 39);
  assign half0[39] = (amount == 40);
  assign half0[40] = (amount == 41);
  assign half0[41] = (amount == 42);
  assign half0[42] = (amount == 43);
  assign half0[43] = (amount == 44);
  assign half0[44] = (amount == 45);
  assign half0[45] = (amount == 46);
  assign half0[46] = (amount == 47);
  assign half0[47] = (amount == 48);
  assign half0[48] = (amount == 49);
  assign half0[49] = (amount == 50);
  assign half0[50] = (amount == 51);
  assign half0[51] = (amount == 52);
  assign half0[52] = (amount == 53);
  assign half0[53] = (amount == 54);
  assign half0[54] = (amount == 55);
  assign half0[55] = (amount == 56);
  assign half0[56] = (amount == 57);
  logic [56:0] halfv; assign halfv = !right ? 57'd0 : distance >= 14'd57 ? (57'd1 << 56) : half0;
  logic [64:0] restw; assign restw = {rest, 8'd0};
  logic [6:0] famt; assign famt = distance >= 14'd65 ? 7'd64 : distance[6:0];
  logic [64:0] fint0;
  // align discarded bits with the stochastic word
  fam_shift_barrel_mux_tree #(.W(65), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u7 (.a(restw), .amt(famt), .op(3'd1), .y(fint0), .sticky());
  logic [64:0] fint; assign fint = !right || distance >= 14'd65 ? 65'd0 : fint0;
  logic inexact; assign inexact = rest != 0 || x_st;
  logic tie; assign tie = rest == halfv && halfv != 0;
  logic up; assign up = rnd == 0 ? (rest > halfv || (tie && (x_st || keep[0]))) : rnd == 1 ? 1'b0 : rnd == 2 ? (inexact && x_s) : rnd == 3 ? (inexact && !x_s) : rnd == 4 ? (inexact && (0 ? fint >= word : fint > word)) : inexact;
  logic [56:0] incremented;
  // rounding increment
  fam_incr_prefix_and #(.W(57), .STRUCTURE(0), .B(4), .TOPO(0)) u8 (.a(keep), .cin(up), .s(incremented), .cout());
  logic [56:0] mag; assign mag = incremented;
  logic negative; assign negative = x_s && (mag != 0 || big);
  logic overflow; assign overflow = big || (negative ? mag > 57'd32768 : mag > 57'd32767);
  logic [56:0] finite; assign finite = overflow ? (negative ? 57'd32768 : 57'd32767) : mag;
  logic [56:0] t; assign t = x_sp == 1 ? 57'd0 : x_sp == 2 ? (x_s ? 57'd32768 : 57'd32767) : finite;
  logic neg; assign neg = x_sp == 1 ? 1'b0 : x_sp == 2 ? x_s : negative;
  assign bits = neg ? (~t[15:0] + 1'b1) : t[15:0];
  assign fl = x_sp != 0 ? (1 << 0) : overflow ? ((1 << 0) | (1 << 2) | (1 << 4)) : inexact ? (1 << 4) : 0;
endmodule

// shift_round_convert: X to int8_twos_complement, selected normalizer, shifters and rounding datapath
module fam_int_cvt_shift_round_convert_int8_twos_complement_x22e13s9 (
  input logic [38:0] x,
  input logic [2:0] rnd,
  input logic [7:0] word,
  input logic ftz,
  output logic [9:0] fl,
  output logic [7:0] bits
);
  logic [1:0] x_sp; assign x_sp = x[38:37];
  logic x_s; assign x_s = x[36];
  logic signed [12:0] x_e; assign x_e = $signed(x[35:23]);
  logic [21:0] x_sig; assign x_sig = x[22:1];
  logic x_st; assign x_st = x[0];
  logic x_z; assign x_z = (x_sp == 2'd0) && (x_sig == 0) && !x_st;
  logic lone; assign lone = x_sig == 0 && x_st;
  logic [21:0] sig_in; assign sig_in = lone ? 22'd1 : x_sig;
  logic [4:0] lz;
  // normalize the source significand
  fam_count_lzd_pair_cell_binary_count_vflat_w22 u1 (.a(sig_in), .n(lz));
  logic [4:0] lzs; assign lzs = sig_in == 0 ? 5'd0 : lz[4:0];
  logic [21:0] sig;
  // place the leading one at the normalizer output
  fam_shift_barrel_mux_tree #(.W(22), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u2 (.a(sig_in), .amt(lzs), .op(3'd0), .y(sig), .sticky());
  logic signed [13:0] xe; assign xe = {x_e[12], x_e};
  logic [13:0] lzx; assign lzx = {{9{1'b0}}, lzs};
  logic [13:0] enorm_nb; assign enorm_nb = ~(lzx);
  logic signed [13:0] enorm;
  // normalization exponent adjustment
  fam_adder_ripple_carry #(.W(14), .CHUNK(1), .FORM(0)) u3 (.a(xe), .b(enorm_nb), .cin(1'b1), .s(enorm), .cout());
  logic signed [13:0] offset; assign offset = lone ? -14'sd22 : 14'sd0;
  logic signed [13:0] pe;
  // target fractional-bit scale
  fam_adder_ripple_carry #(.W(14), .CHUNK(1), .FORM(0)) u4 (.a(enorm), .b(offset), .cin(1'b0), .s(pe), .cout());
  logic [13:0] pen; assign pen = ~pe;
  logic [13:0] negpe;
  // two's-complement right-shift distance
  fam_incr_prefix_and #(.W(14), .STRUCTURE(0), .B(4), .TOPO(0)) u5 (.a(pen), .cin(1'b1), .s(negpe), .cout());
  logic right; assign right = pe[13];
  logic [13:0] distance; assign distance = right ? negpe : pe;
  logic [5:0] amount; assign amount = distance >= 14'd33 ? 6'd32 : distance[5:0];
  logic [32:0] sigw; assign sigw = {{11{1'b0}}, sig};
  logic [32:0] aligned;
  // align to the target's fixed least-significant bit
  fam_shift_barrel_mux_tree #(.W(33), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u6 (.a(sigw), .amt(amount), .op({2'd0, right}), .y(aligned), .sticky());
  logic [32:0] keep; assign keep = right && distance >= 14'd33 ? 33'd0 : aligned;
  logic big; assign big = !right && distance > 14'd10;
  // positions discarded by the right shift
  logic [32:0] restmask0;
  assign restmask0[0] = (amount > 0);
  assign restmask0[1] = (amount > 1);
  assign restmask0[2] = (amount > 2);
  assign restmask0[3] = (amount > 3);
  assign restmask0[4] = (amount > 4);
  assign restmask0[5] = (amount > 5);
  assign restmask0[6] = (amount > 6);
  assign restmask0[7] = (amount > 7);
  assign restmask0[8] = (amount > 8);
  assign restmask0[9] = (amount > 9);
  assign restmask0[10] = (amount > 10);
  assign restmask0[11] = (amount > 11);
  assign restmask0[12] = (amount > 12);
  assign restmask0[13] = (amount > 13);
  assign restmask0[14] = (amount > 14);
  assign restmask0[15] = (amount > 15);
  assign restmask0[16] = (amount > 16);
  assign restmask0[17] = (amount > 17);
  assign restmask0[18] = (amount > 18);
  assign restmask0[19] = (amount > 19);
  assign restmask0[20] = (amount > 20);
  assign restmask0[21] = (amount > 21);
  assign restmask0[22] = (amount > 22);
  assign restmask0[23] = (amount > 23);
  assign restmask0[24] = (amount > 24);
  assign restmask0[25] = (amount > 25);
  assign restmask0[26] = (amount > 26);
  assign restmask0[27] = (amount > 27);
  assign restmask0[28] = (amount > 28);
  assign restmask0[29] = (amount > 29);
  assign restmask0[30] = (amount > 30);
  assign restmask0[31] = (amount > 31);
  assign restmask0[32] = (amount > 32);
  logic [32:0] restmask; assign restmask = !right ? 33'd0 : distance >= 14'd33 ? {33{1'b1}} : restmask0;
  logic [32:0] rest; assign rest = sigw & restmask;
  // half of the target least-significant bit
  logic [32:0] half0;
  assign half0[0] = (amount == 1);
  assign half0[1] = (amount == 2);
  assign half0[2] = (amount == 3);
  assign half0[3] = (amount == 4);
  assign half0[4] = (amount == 5);
  assign half0[5] = (amount == 6);
  assign half0[6] = (amount == 7);
  assign half0[7] = (amount == 8);
  assign half0[8] = (amount == 9);
  assign half0[9] = (amount == 10);
  assign half0[10] = (amount == 11);
  assign half0[11] = (amount == 12);
  assign half0[12] = (amount == 13);
  assign half0[13] = (amount == 14);
  assign half0[14] = (amount == 15);
  assign half0[15] = (amount == 16);
  assign half0[16] = (amount == 17);
  assign half0[17] = (amount == 18);
  assign half0[18] = (amount == 19);
  assign half0[19] = (amount == 20);
  assign half0[20] = (amount == 21);
  assign half0[21] = (amount == 22);
  assign half0[22] = (amount == 23);
  assign half0[23] = (amount == 24);
  assign half0[24] = (amount == 25);
  assign half0[25] = (amount == 26);
  assign half0[26] = (amount == 27);
  assign half0[27] = (amount == 28);
  assign half0[28] = (amount == 29);
  assign half0[29] = (amount == 30);
  assign half0[30] = (amount == 31);
  assign half0[31] = (amount == 32);
  assign half0[32] = (amount == 33);
  logic [32:0] halfv; assign halfv = !right ? 33'd0 : distance >= 14'd33 ? (33'd1 << 32) : half0;
  logic [40:0] restw; assign restw = {rest, 8'd0};
  logic [5:0] famt; assign famt = distance >= 14'd41 ? 6'd40 : distance[5:0];
  logic [40:0] fint0;
  // align discarded bits with the stochastic word
  fam_shift_barrel_mux_tree #(.W(41), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u7 (.a(restw), .amt(famt), .op(3'd1), .y(fint0), .sticky());
  logic [40:0] fint; assign fint = !right || distance >= 14'd41 ? 41'd0 : fint0;
  logic inexact; assign inexact = rest != 0 || x_st;
  logic tie; assign tie = rest == halfv && halfv != 0;
  logic up; assign up = rnd == 0 ? (rest > halfv || (tie && (x_st || keep[0]))) : rnd == 1 ? 1'b0 : rnd == 2 ? (inexact && x_s) : rnd == 3 ? (inexact && !x_s) : rnd == 4 ? (inexact && (0 ? fint >= word : fint > word)) : inexact;
  logic [32:0] incremented;
  // rounding increment
  fam_incr_prefix_and #(.W(33), .STRUCTURE(0), .B(4), .TOPO(0)) u8 (.a(keep), .cin(up), .s(incremented), .cout());
  logic [32:0] mag; assign mag = incremented;
  logic negative; assign negative = x_s && (mag != 0 || big);
  logic overflow; assign overflow = big || (negative ? mag > 33'd128 : mag > 33'd127);
  logic [32:0] finite; assign finite = overflow ? (negative ? 33'd128 : 33'd127) : mag;
  logic [32:0] t; assign t = x_sp == 1 ? 33'd0 : x_sp == 2 ? (x_s ? 33'd128 : 33'd127) : finite;
  logic neg; assign neg = x_sp == 1 ? 1'b0 : x_sp == 2 ? x_s : negative;
  assign bits = neg ? (~t[7:0] + 1'b1) : t[7:0];
  assign fl = x_sp != 0 ? (1 << 0) : overflow ? ((1 << 0) | (1 << 2) | (1 << 4)) : inexact ? (1 << 4) : 0;
endmodule

// shift_round_convert: X to int8_twos_complement, selected normalizer, shifters and rounding datapath
module fam_int_cvt_shift_round_convert_int8_twos_complement_x38e13s17 (
  input logic [54:0] x,
  input logic [2:0] rnd,
  input logic [7:0] word,
  input logic ftz,
  output logic [9:0] fl,
  output logic [7:0] bits
);
  logic [1:0] x_sp; assign x_sp = x[54:53];
  logic x_s; assign x_s = x[52];
  logic signed [12:0] x_e; assign x_e = $signed(x[51:39]);
  logic [37:0] x_sig; assign x_sig = x[38:1];
  logic x_st; assign x_st = x[0];
  logic x_z; assign x_z = (x_sp == 2'd0) && (x_sig == 0) && !x_st;
  logic lone; assign lone = x_sig == 0 && x_st;
  logic [37:0] sig_in; assign sig_in = lone ? 38'd1 : x_sig;
  logic [5:0] lz;
  // normalize the source significand
  fam_count_lzd_pair_cell_binary_count_vflat_w38 u1 (.a(sig_in), .n(lz));
  logic [5:0] lzs; assign lzs = sig_in == 0 ? 6'd0 : lz[5:0];
  logic [37:0] sig;
  // place the leading one at the normalizer output
  fam_shift_barrel_mux_tree #(.W(38), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u2 (.a(sig_in), .amt(lzs), .op(3'd0), .y(sig), .sticky());
  logic signed [13:0] xe; assign xe = {x_e[12], x_e};
  logic [13:0] lzx; assign lzx = {{8{1'b0}}, lzs};
  logic [13:0] enorm_nb; assign enorm_nb = ~(lzx);
  logic signed [13:0] enorm;
  // normalization exponent adjustment
  fam_adder_ripple_carry #(.W(14), .CHUNK(1), .FORM(0)) u3 (.a(xe), .b(enorm_nb), .cin(1'b1), .s(enorm), .cout());
  logic signed [13:0] offset; assign offset = lone ? -14'sd38 : 14'sd0;
  logic signed [13:0] pe;
  // target fractional-bit scale
  fam_adder_ripple_carry #(.W(14), .CHUNK(1), .FORM(0)) u4 (.a(enorm), .b(offset), .cin(1'b0), .s(pe), .cout());
  logic [13:0] pen; assign pen = ~pe;
  logic [13:0] negpe;
  // two's-complement right-shift distance
  fam_incr_prefix_and #(.W(14), .STRUCTURE(0), .B(4), .TOPO(0)) u5 (.a(pen), .cin(1'b1), .s(negpe), .cout());
  logic right; assign right = pe[13];
  logic [13:0] distance; assign distance = right ? negpe : pe;
  logic [5:0] amount; assign amount = distance >= 14'd49 ? 6'd48 : distance[5:0];
  logic [48:0] sigw; assign sigw = {{11{1'b0}}, sig};
  logic [48:0] aligned;
  // align to the target's fixed least-significant bit
  fam_shift_barrel_mux_tree #(.W(49), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u6 (.a(sigw), .amt(amount), .op({2'd0, right}), .y(aligned), .sticky());
  logic [48:0] keep; assign keep = right && distance >= 14'd49 ? 49'd0 : aligned;
  logic big; assign big = !right && distance > 14'd10;
  // positions discarded by the right shift
  logic [48:0] restmask0;
  assign restmask0[0] = (amount > 0);
  assign restmask0[1] = (amount > 1);
  assign restmask0[2] = (amount > 2);
  assign restmask0[3] = (amount > 3);
  assign restmask0[4] = (amount > 4);
  assign restmask0[5] = (amount > 5);
  assign restmask0[6] = (amount > 6);
  assign restmask0[7] = (amount > 7);
  assign restmask0[8] = (amount > 8);
  assign restmask0[9] = (amount > 9);
  assign restmask0[10] = (amount > 10);
  assign restmask0[11] = (amount > 11);
  assign restmask0[12] = (amount > 12);
  assign restmask0[13] = (amount > 13);
  assign restmask0[14] = (amount > 14);
  assign restmask0[15] = (amount > 15);
  assign restmask0[16] = (amount > 16);
  assign restmask0[17] = (amount > 17);
  assign restmask0[18] = (amount > 18);
  assign restmask0[19] = (amount > 19);
  assign restmask0[20] = (amount > 20);
  assign restmask0[21] = (amount > 21);
  assign restmask0[22] = (amount > 22);
  assign restmask0[23] = (amount > 23);
  assign restmask0[24] = (amount > 24);
  assign restmask0[25] = (amount > 25);
  assign restmask0[26] = (amount > 26);
  assign restmask0[27] = (amount > 27);
  assign restmask0[28] = (amount > 28);
  assign restmask0[29] = (amount > 29);
  assign restmask0[30] = (amount > 30);
  assign restmask0[31] = (amount > 31);
  assign restmask0[32] = (amount > 32);
  assign restmask0[33] = (amount > 33);
  assign restmask0[34] = (amount > 34);
  assign restmask0[35] = (amount > 35);
  assign restmask0[36] = (amount > 36);
  assign restmask0[37] = (amount > 37);
  assign restmask0[38] = (amount > 38);
  assign restmask0[39] = (amount > 39);
  assign restmask0[40] = (amount > 40);
  assign restmask0[41] = (amount > 41);
  assign restmask0[42] = (amount > 42);
  assign restmask0[43] = (amount > 43);
  assign restmask0[44] = (amount > 44);
  assign restmask0[45] = (amount > 45);
  assign restmask0[46] = (amount > 46);
  assign restmask0[47] = (amount > 47);
  assign restmask0[48] = (amount > 48);
  logic [48:0] restmask; assign restmask = !right ? 49'd0 : distance >= 14'd49 ? {49{1'b1}} : restmask0;
  logic [48:0] rest; assign rest = sigw & restmask;
  // half of the target least-significant bit
  logic [48:0] half0;
  assign half0[0] = (amount == 1);
  assign half0[1] = (amount == 2);
  assign half0[2] = (amount == 3);
  assign half0[3] = (amount == 4);
  assign half0[4] = (amount == 5);
  assign half0[5] = (amount == 6);
  assign half0[6] = (amount == 7);
  assign half0[7] = (amount == 8);
  assign half0[8] = (amount == 9);
  assign half0[9] = (amount == 10);
  assign half0[10] = (amount == 11);
  assign half0[11] = (amount == 12);
  assign half0[12] = (amount == 13);
  assign half0[13] = (amount == 14);
  assign half0[14] = (amount == 15);
  assign half0[15] = (amount == 16);
  assign half0[16] = (amount == 17);
  assign half0[17] = (amount == 18);
  assign half0[18] = (amount == 19);
  assign half0[19] = (amount == 20);
  assign half0[20] = (amount == 21);
  assign half0[21] = (amount == 22);
  assign half0[22] = (amount == 23);
  assign half0[23] = (amount == 24);
  assign half0[24] = (amount == 25);
  assign half0[25] = (amount == 26);
  assign half0[26] = (amount == 27);
  assign half0[27] = (amount == 28);
  assign half0[28] = (amount == 29);
  assign half0[29] = (amount == 30);
  assign half0[30] = (amount == 31);
  assign half0[31] = (amount == 32);
  assign half0[32] = (amount == 33);
  assign half0[33] = (amount == 34);
  assign half0[34] = (amount == 35);
  assign half0[35] = (amount == 36);
  assign half0[36] = (amount == 37);
  assign half0[37] = (amount == 38);
  assign half0[38] = (amount == 39);
  assign half0[39] = (amount == 40);
  assign half0[40] = (amount == 41);
  assign half0[41] = (amount == 42);
  assign half0[42] = (amount == 43);
  assign half0[43] = (amount == 44);
  assign half0[44] = (amount == 45);
  assign half0[45] = (amount == 46);
  assign half0[46] = (amount == 47);
  assign half0[47] = (amount == 48);
  assign half0[48] = (amount == 49);
  logic [48:0] halfv; assign halfv = !right ? 49'd0 : distance >= 14'd49 ? (49'd1 << 48) : half0;
  logic [56:0] restw; assign restw = {rest, 8'd0};
  logic [5:0] famt; assign famt = distance >= 14'd57 ? 6'd56 : distance[5:0];
  logic [56:0] fint0;
  // align discarded bits with the stochastic word
  fam_shift_barrel_mux_tree #(.W(57), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u7 (.a(restw), .amt(famt), .op(3'd1), .y(fint0), .sticky());
  logic [56:0] fint; assign fint = !right || distance >= 14'd57 ? 57'd0 : fint0;
  logic inexact; assign inexact = rest != 0 || x_st;
  logic tie; assign tie = rest == halfv && halfv != 0;
  logic up; assign up = rnd == 0 ? (rest > halfv || (tie && (x_st || keep[0]))) : rnd == 1 ? 1'b0 : rnd == 2 ? (inexact && x_s) : rnd == 3 ? (inexact && !x_s) : rnd == 4 ? (inexact && (0 ? fint >= word : fint > word)) : inexact;
  logic [48:0] incremented;
  // rounding increment
  fam_incr_prefix_and #(.W(49), .STRUCTURE(0), .B(4), .TOPO(0)) u8 (.a(keep), .cin(up), .s(incremented), .cout());
  logic [48:0] mag; assign mag = incremented;
  logic negative; assign negative = x_s && (mag != 0 || big);
  logic overflow; assign overflow = big || (negative ? mag > 49'd128 : mag > 49'd127);
  logic [48:0] finite; assign finite = overflow ? (negative ? 49'd128 : 49'd127) : mag;
  logic [48:0] t; assign t = x_sp == 1 ? 49'd0 : x_sp == 2 ? (x_s ? 49'd128 : 49'd127) : finite;
  logic neg; assign neg = x_sp == 1 ? 1'b0 : x_sp == 2 ? x_s : negative;
  assign bits = neg ? (~t[7:0] + 1'b1) : t[7:0];
  assign fl = x_sp != 0 ? (1 << 0) : overflow ? ((1 << 0) | (1 << 2) | (1 << 4)) : inexact ? (1 << 4) : 0;
endmodule

// shift_round_convert: X to fxs1i7f8, selected normalizer, shifters and rounding datapath
module fam_int_round_fxs1i7f8_x26e13s11_pd77ccc5b5c45 (
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
  logic lone; assign lone = x_sig == 0 && x_st;
  logic [25:0] sig_in; assign sig_in = lone ? 26'd1 : x_sig;
  logic [4:0] lz;
  // normalize the source significand
  fam_count_lzd_pair_cell_binary_count_vflat_w26 u1 (.a(sig_in), .n(lz));
  logic [4:0] lzs; assign lzs = sig_in == 0 ? 5'd0 : lz[4:0];
  logic [25:0] sig;
  // place the leading one at the normalizer output
  fam_shift_barrel_mux_tree #(.W(26), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u2 (.a(sig_in), .amt(lzs), .op(3'd0), .y(sig), .sticky());
  logic signed [13:0] xe; assign xe = {x_e[12], x_e};
  logic [13:0] lzx; assign lzx = {{9{1'b0}}, lzs};
  logic [13:0] enorm_nb; assign enorm_nb = ~(lzx);
  logic signed [13:0] enorm;
  // normalization exponent adjustment
  fam_adder_ripple_carry #(.W(14), .CHUNK(1), .FORM(0)) u3 (.a(xe), .b(enorm_nb), .cin(1'b1), .s(enorm), .cout());
  logic signed [13:0] offset; assign offset = lone ? -14'sd18 : 14'sd8;
  logic signed [13:0] pe;
  // target fractional-bit scale
  fam_adder_ripple_carry #(.W(14), .CHUNK(1), .FORM(0)) u4 (.a(enorm), .b(offset), .cin(1'b0), .s(pe), .cout());
  logic [13:0] pen; assign pen = ~pe;
  logic [13:0] negpe;
  // two's-complement right-shift distance
  fam_incr_prefix_and #(.W(14), .STRUCTURE(0), .B(4), .TOPO(0)) u5 (.a(pen), .cin(1'b1), .s(negpe), .cout());
  logic right; assign right = pe[13];
  logic [13:0] distance; assign distance = right ? negpe : pe;
  logic [5:0] amount; assign amount = distance >= 14'd45 ? 6'd44 : distance[5:0];
  logic [44:0] sigw; assign sigw = {{19{1'b0}}, sig};
  logic [44:0] aligned;
  // align to the target's fixed least-significant bit
  fam_shift_barrel_mux_tree #(.W(45), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u6 (.a(sigw), .amt(amount), .op({2'd0, right}), .y(aligned), .sticky());
  logic [44:0] keep; assign keep = right && distance >= 14'd45 ? 45'd0 : aligned;
  logic big; assign big = !right && distance > 14'd18;
  // positions discarded by the right shift
  logic [44:0] restmask0;
  assign restmask0[0] = (amount > 0);
  assign restmask0[1] = (amount > 1);
  assign restmask0[2] = (amount > 2);
  assign restmask0[3] = (amount > 3);
  assign restmask0[4] = (amount > 4);
  assign restmask0[5] = (amount > 5);
  assign restmask0[6] = (amount > 6);
  assign restmask0[7] = (amount > 7);
  assign restmask0[8] = (amount > 8);
  assign restmask0[9] = (amount > 9);
  assign restmask0[10] = (amount > 10);
  assign restmask0[11] = (amount > 11);
  assign restmask0[12] = (amount > 12);
  assign restmask0[13] = (amount > 13);
  assign restmask0[14] = (amount > 14);
  assign restmask0[15] = (amount > 15);
  assign restmask0[16] = (amount > 16);
  assign restmask0[17] = (amount > 17);
  assign restmask0[18] = (amount > 18);
  assign restmask0[19] = (amount > 19);
  assign restmask0[20] = (amount > 20);
  assign restmask0[21] = (amount > 21);
  assign restmask0[22] = (amount > 22);
  assign restmask0[23] = (amount > 23);
  assign restmask0[24] = (amount > 24);
  assign restmask0[25] = (amount > 25);
  assign restmask0[26] = (amount > 26);
  assign restmask0[27] = (amount > 27);
  assign restmask0[28] = (amount > 28);
  assign restmask0[29] = (amount > 29);
  assign restmask0[30] = (amount > 30);
  assign restmask0[31] = (amount > 31);
  assign restmask0[32] = (amount > 32);
  assign restmask0[33] = (amount > 33);
  assign restmask0[34] = (amount > 34);
  assign restmask0[35] = (amount > 35);
  assign restmask0[36] = (amount > 36);
  assign restmask0[37] = (amount > 37);
  assign restmask0[38] = (amount > 38);
  assign restmask0[39] = (amount > 39);
  assign restmask0[40] = (amount > 40);
  assign restmask0[41] = (amount > 41);
  assign restmask0[42] = (amount > 42);
  assign restmask0[43] = (amount > 43);
  assign restmask0[44] = (amount > 44);
  logic [44:0] restmask; assign restmask = !right ? 45'd0 : distance >= 14'd45 ? {45{1'b1}} : restmask0;
  logic [44:0] rest; assign rest = sigw & restmask;
  // half of the target least-significant bit
  logic [44:0] half0;
  assign half0[0] = (amount == 1);
  assign half0[1] = (amount == 2);
  assign half0[2] = (amount == 3);
  assign half0[3] = (amount == 4);
  assign half0[4] = (amount == 5);
  assign half0[5] = (amount == 6);
  assign half0[6] = (amount == 7);
  assign half0[7] = (amount == 8);
  assign half0[8] = (amount == 9);
  assign half0[9] = (amount == 10);
  assign half0[10] = (amount == 11);
  assign half0[11] = (amount == 12);
  assign half0[12] = (amount == 13);
  assign half0[13] = (amount == 14);
  assign half0[14] = (amount == 15);
  assign half0[15] = (amount == 16);
  assign half0[16] = (amount == 17);
  assign half0[17] = (amount == 18);
  assign half0[18] = (amount == 19);
  assign half0[19] = (amount == 20);
  assign half0[20] = (amount == 21);
  assign half0[21] = (amount == 22);
  assign half0[22] = (amount == 23);
  assign half0[23] = (amount == 24);
  assign half0[24] = (amount == 25);
  assign half0[25] = (amount == 26);
  assign half0[26] = (amount == 27);
  assign half0[27] = (amount == 28);
  assign half0[28] = (amount == 29);
  assign half0[29] = (amount == 30);
  assign half0[30] = (amount == 31);
  assign half0[31] = (amount == 32);
  assign half0[32] = (amount == 33);
  assign half0[33] = (amount == 34);
  assign half0[34] = (amount == 35);
  assign half0[35] = (amount == 36);
  assign half0[36] = (amount == 37);
  assign half0[37] = (amount == 38);
  assign half0[38] = (amount == 39);
  assign half0[39] = (amount == 40);
  assign half0[40] = (amount == 41);
  assign half0[41] = (amount == 42);
  assign half0[42] = (amount == 43);
  assign half0[43] = (amount == 44);
  assign half0[44] = (amount == 45);
  logic [44:0] halfv; assign halfv = !right ? 45'd0 : distance >= 14'd45 ? (45'd1 << 44) : half0;
  logic [52:0] restw; assign restw = {rest, 8'd0};
  logic [5:0] famt; assign famt = distance >= 14'd53 ? 6'd52 : distance[5:0];
  logic [52:0] fint0;
  // align discarded bits with the stochastic word
  fam_shift_barrel_mux_tree #(.W(53), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u7 (.a(restw), .amt(famt), .op(3'd1), .y(fint0), .sticky());
  logic [52:0] fint; assign fint = !right || distance >= 14'd53 ? 53'd0 : fint0;
  logic inexact; assign inexact = rest != 0 || x_st;
  logic tie; assign tie = rest == halfv && halfv != 0;
  logic up; assign up = rnd == 0 ? (rest > halfv || (tie && (x_st || keep[0]))) : rnd == 1 ? 1'b0 : rnd == 2 ? (inexact && x_s) : rnd == 3 ? (inexact && !x_s) : rnd == 4 ? (inexact && (0 ? fint >= word : fint > word)) : inexact;
  logic [44:0] incremented;
  // rounding increment
  fam_incr_prefix_and #(.W(45), .STRUCTURE(0), .B(4), .TOPO(0)) u8 (.a(keep), .cin(up), .s(incremented), .cout());
  logic [44:0] mag; assign mag = incremented;
  logic negative; assign negative = x_s && (mag != 0 || big);
  logic overflow; assign overflow = big || (negative ? mag > 45'd32768 : mag > 45'd32767);
  logic [44:0] finite; assign finite = overflow ? (negative ? 45'd32768 : 45'd32767) : mag;
  logic [44:0] t; assign t = x_sp == 1 ? 45'd0 : x_sp == 2 ? (x_s ? 45'd32768 : 45'd32767) : finite;
  logic neg; assign neg = x_sp == 1 ? 1'b0 : x_sp == 2 ? x_s : negative;
  assign bits = neg ? (~t[15:0] + 1'b1) : t[15:0];
  assign fl = x_sp != 0 ? (1 << 0) : overflow ? ((1 << 0) | (1 << 2) | (1 << 4)) : inexact ? (1 << 4) : 0;
endmodule

// shift_round_convert: X to int8_twos_complement, selected normalizer, shifters and rounding datapath
module fam_int_round_int8_twos_complement_x26e13s11_pd77ccc5b5c45 (
  input logic [42:0] x,
  input logic [2:0] rnd,
  input logic [7:0] word,
  input logic ftz,
  output logic [9:0] fl,
  output logic [7:0] bits
);
  logic [1:0] x_sp; assign x_sp = x[42:41];
  logic x_s; assign x_s = x[40];
  logic signed [12:0] x_e; assign x_e = $signed(x[39:27]);
  logic [25:0] x_sig; assign x_sig = x[26:1];
  logic x_st; assign x_st = x[0];
  logic x_z; assign x_z = (x_sp == 2'd0) && (x_sig == 0) && !x_st;
  logic lone; assign lone = x_sig == 0 && x_st;
  logic [25:0] sig_in; assign sig_in = lone ? 26'd1 : x_sig;
  logic [4:0] lz;
  // normalize the source significand
  fam_count_lzd_pair_cell_binary_count_vflat_w26 u1 (.a(sig_in), .n(lz));
  logic [4:0] lzs; assign lzs = sig_in == 0 ? 5'd0 : lz[4:0];
  logic [25:0] sig;
  // place the leading one at the normalizer output
  fam_shift_barrel_mux_tree #(.W(26), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u2 (.a(sig_in), .amt(lzs), .op(3'd0), .y(sig), .sticky());
  logic signed [13:0] xe; assign xe = {x_e[12], x_e};
  logic [13:0] lzx; assign lzx = {{9{1'b0}}, lzs};
  logic [13:0] enorm_nb; assign enorm_nb = ~(lzx);
  logic signed [13:0] enorm;
  // normalization exponent adjustment
  fam_adder_ripple_carry #(.W(14), .CHUNK(1), .FORM(0)) u3 (.a(xe), .b(enorm_nb), .cin(1'b1), .s(enorm), .cout());
  logic signed [13:0] offset; assign offset = lone ? -14'sd26 : 14'sd0;
  logic signed [13:0] pe;
  // target fractional-bit scale
  fam_adder_ripple_carry #(.W(14), .CHUNK(1), .FORM(0)) u4 (.a(enorm), .b(offset), .cin(1'b0), .s(pe), .cout());
  logic [13:0] pen; assign pen = ~pe;
  logic [13:0] negpe;
  // two's-complement right-shift distance
  fam_incr_prefix_and #(.W(14), .STRUCTURE(0), .B(4), .TOPO(0)) u5 (.a(pen), .cin(1'b1), .s(negpe), .cout());
  logic right; assign right = pe[13];
  logic [13:0] distance; assign distance = right ? negpe : pe;
  logic [5:0] amount; assign amount = distance >= 14'd37 ? 6'd36 : distance[5:0];
  logic [36:0] sigw; assign sigw = {{11{1'b0}}, sig};
  logic [36:0] aligned;
  // align to the target's fixed least-significant bit
  fam_shift_barrel_mux_tree #(.W(37), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u6 (.a(sigw), .amt(amount), .op({2'd0, right}), .y(aligned), .sticky());
  logic [36:0] keep; assign keep = right && distance >= 14'd37 ? 37'd0 : aligned;
  logic big; assign big = !right && distance > 14'd10;
  // positions discarded by the right shift
  logic [36:0] restmask0;
  assign restmask0[0] = (amount > 0);
  assign restmask0[1] = (amount > 1);
  assign restmask0[2] = (amount > 2);
  assign restmask0[3] = (amount > 3);
  assign restmask0[4] = (amount > 4);
  assign restmask0[5] = (amount > 5);
  assign restmask0[6] = (amount > 6);
  assign restmask0[7] = (amount > 7);
  assign restmask0[8] = (amount > 8);
  assign restmask0[9] = (amount > 9);
  assign restmask0[10] = (amount > 10);
  assign restmask0[11] = (amount > 11);
  assign restmask0[12] = (amount > 12);
  assign restmask0[13] = (amount > 13);
  assign restmask0[14] = (amount > 14);
  assign restmask0[15] = (amount > 15);
  assign restmask0[16] = (amount > 16);
  assign restmask0[17] = (amount > 17);
  assign restmask0[18] = (amount > 18);
  assign restmask0[19] = (amount > 19);
  assign restmask0[20] = (amount > 20);
  assign restmask0[21] = (amount > 21);
  assign restmask0[22] = (amount > 22);
  assign restmask0[23] = (amount > 23);
  assign restmask0[24] = (amount > 24);
  assign restmask0[25] = (amount > 25);
  assign restmask0[26] = (amount > 26);
  assign restmask0[27] = (amount > 27);
  assign restmask0[28] = (amount > 28);
  assign restmask0[29] = (amount > 29);
  assign restmask0[30] = (amount > 30);
  assign restmask0[31] = (amount > 31);
  assign restmask0[32] = (amount > 32);
  assign restmask0[33] = (amount > 33);
  assign restmask0[34] = (amount > 34);
  assign restmask0[35] = (amount > 35);
  assign restmask0[36] = (amount > 36);
  logic [36:0] restmask; assign restmask = !right ? 37'd0 : distance >= 14'd37 ? {37{1'b1}} : restmask0;
  logic [36:0] rest; assign rest = sigw & restmask;
  // half of the target least-significant bit
  logic [36:0] half0;
  assign half0[0] = (amount == 1);
  assign half0[1] = (amount == 2);
  assign half0[2] = (amount == 3);
  assign half0[3] = (amount == 4);
  assign half0[4] = (amount == 5);
  assign half0[5] = (amount == 6);
  assign half0[6] = (amount == 7);
  assign half0[7] = (amount == 8);
  assign half0[8] = (amount == 9);
  assign half0[9] = (amount == 10);
  assign half0[10] = (amount == 11);
  assign half0[11] = (amount == 12);
  assign half0[12] = (amount == 13);
  assign half0[13] = (amount == 14);
  assign half0[14] = (amount == 15);
  assign half0[15] = (amount == 16);
  assign half0[16] = (amount == 17);
  assign half0[17] = (amount == 18);
  assign half0[18] = (amount == 19);
  assign half0[19] = (amount == 20);
  assign half0[20] = (amount == 21);
  assign half0[21] = (amount == 22);
  assign half0[22] = (amount == 23);
  assign half0[23] = (amount == 24);
  assign half0[24] = (amount == 25);
  assign half0[25] = (amount == 26);
  assign half0[26] = (amount == 27);
  assign half0[27] = (amount == 28);
  assign half0[28] = (amount == 29);
  assign half0[29] = (amount == 30);
  assign half0[30] = (amount == 31);
  assign half0[31] = (amount == 32);
  assign half0[32] = (amount == 33);
  assign half0[33] = (amount == 34);
  assign half0[34] = (amount == 35);
  assign half0[35] = (amount == 36);
  assign half0[36] = (amount == 37);
  logic [36:0] halfv; assign halfv = !right ? 37'd0 : distance >= 14'd37 ? (37'd1 << 36) : half0;
  logic [44:0] restw; assign restw = {rest, 8'd0};
  logic [5:0] famt; assign famt = distance >= 14'd45 ? 6'd44 : distance[5:0];
  logic [44:0] fint0;
  // align discarded bits with the stochastic word
  fam_shift_barrel_mux_tree #(.W(45), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u7 (.a(restw), .amt(famt), .op(3'd1), .y(fint0), .sticky());
  logic [44:0] fint; assign fint = !right || distance >= 14'd45 ? 45'd0 : fint0;
  logic inexact; assign inexact = rest != 0 || x_st;
  logic tie; assign tie = rest == halfv && halfv != 0;
  logic up; assign up = rnd == 0 ? (rest > halfv || (tie && (x_st || keep[0]))) : rnd == 1 ? 1'b0 : rnd == 2 ? (inexact && x_s) : rnd == 3 ? (inexact && !x_s) : rnd == 4 ? (inexact && (0 ? fint >= word : fint > word)) : inexact;
  logic [36:0] incremented;
  // rounding increment
  fam_incr_prefix_and #(.W(37), .STRUCTURE(0), .B(4), .TOPO(0)) u8 (.a(keep), .cin(up), .s(incremented), .cout());
  logic [36:0] mag; assign mag = incremented;
  logic negative; assign negative = x_s && (mag != 0 || big);
  logic overflow; assign overflow = big || (negative ? mag > 37'd128 : mag > 37'd127);
  logic [36:0] finite; assign finite = overflow ? (negative ? 37'd128 : 37'd127) : mag;
  logic [36:0] t; assign t = x_sp == 1 ? 37'd0 : x_sp == 2 ? (x_s ? 37'd128 : 37'd127) : finite;
  logic neg; assign neg = x_sp == 1 ? 1'b0 : x_sp == 2 ? x_s : negative;
  assign bits = neg ? (~t[7:0] + 1'b1) : t[7:0];
  assign fl = x_sp != 0 ? (1 << 0) : overflow ? ((1 << 0) | (1 << 2) | (1 << 4)) : inexact ? (1 << 4) : 0;
endmodule


// behavioral_star: p = a * b, the structure left to synthesis
module fam_mul_behavioral_star_w11_u_pfc463c41 (input logic [10:0] a, input logic [10:0] b, output logic [21:0] p);
  assign p = a * b;
endmodule


// behavioral_star: p = a * b, the structure left to synthesis
module fam_mul_behavioral_star_w16_s (input logic [15:0] a, input logic [15:0] b, output logic [31:0] p);
  assign p = $signed(a) * $signed(b);
endmodule


// behavioral_star: p = a * b, the structure left to synthesis
module fam_mul_behavioral_star_w8_s (input logic [7:0] a, input logic [7:0] b, output logic [15:0] p);
  assign p = $signed(a) * $signed(b);
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
