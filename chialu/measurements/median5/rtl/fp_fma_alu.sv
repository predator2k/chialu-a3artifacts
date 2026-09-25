// ADIR-MEMBER packages
// alu_core_m0_pkg: the exact-arithmetic functions of mode 0 (1xfp16)
package alu_core_m0_pkg;

  // ---- m0: V = {special[1:0], sign, exp[16] (signed), sig[11]}
  //           X = {special[1:0], sign, exp[16] (signed), sig[26], sticky}
  localparam int m0_SW = 11, m0_EW = 16, m0_XW = 26;
  localparam int m0_VW = 30, m0_XT = 46;
  function automatic [29:0] m0_mkv(input [1:0] sp, input s, input signed [15:0] e, input [10:0] sig);
    m0_mkv = {sp, s, e, sig};
  endfunction
  function automatic [45:0] m0_mkx(input [1:0] sp, input s, input signed [15:0] e, input [25:0] sig, input st);
    m0_mkx = {sp, s, e, sig, st};
  endfunction
  function automatic [45:0] m0_x(input [29:0] v);   // widen V to X
    m0_x = {v[29:29-1], v[29-2], v[29-3 -: 16], {{(26-11){1'b0}}, v[10:0]}, 1'b0};
  endfunction
  // normalize: leading one at bit XW-1 (zero stays zero)
  function automatic [45:0] m0_norm(input [45:0] x);
    logic [25:0] s; logic signed [15:0] e; integer k;
    s = x[26:1]; e = x[26+16:26+1];
    if (s != 0) begin
      for (k = 16; k >= 1; k = k / 2) begin
        if (k < 26) begin
          if (s[25 -: 1] == 1'b0 && (s >> (26 - k)) == 0) begin
            s = s << k; e = e - k;
          end
        end
      end
    end
    m0_norm = {x[45:45-1], x[45-2], e, s, x[0]};
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
  function automatic [45:0] m0_add(input [45:0] a, input [45:0] b, input sub);
    logic [45:0] na, nb, big, sml; logic [1:0] spa, spb; logic sa, sb, sr, sw;
    logic signed [15:0] ea, eb, d; logic [26:0] ms, mb, r; logic st, stb; integer sh;
    na = m0_norm(a); nb = m0_norm(b);
    spa = na[45:45-1]; spb = nb[45:45-1];
    sa = na[45-2]; sb = nb[45-2] ^ sub;
    if (spa == 2'd1 || spb == 2'd1) m0_add = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 && spb == 2'd2) m0_add = (sa == sb) ? m0_mkx(2'd2, sa, 0, 0, 1'b0) : m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m0_add = m0_mkx(2'd2, sa, 0, 0, 1'b0);
    else if (spb == 2'd2) m0_add = m0_mkx(2'd2, sb, 0, 0, 1'b0);
    else if (na[26:1] == 0 && !na[0]) m0_add = {nb[45:45-1], sb, nb[45-3:0]};
    else if (nb[26:1] == 0 && !nb[0]) m0_add = na;
    else begin
      ea = na[26+16:26+1]; eb = nb[26+16:26+1];
      // order by magnitude (both normalized): larger exponent, then sig
      if (ea > eb || (ea == eb && na[26:1] >= nb[26:1])) begin big = na; sml = nb; sw = 1'b0; end
      else begin big = nb; sml = na; sw = 1'b1; end
      d = big[26+16:26+1] - sml[26+16:26+1];
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
      if (r[26]) begin st = st | r[0]; r = r >> 1; m0_add = m0_mkx(2'd0, sr, big[26+16:26+1] + 1, r[25:0], st); end
      else m0_add = m0_mkx(2'd0, sr, big[26+16:26+1], r[25:0], st);
    end
  endfunction
  function automatic [45:0] m0_mul(input [45:0] a, input [45:0] b);
    logic [45:0] na, nb; logic [1:0] spa, spb; logic s; logic [2*26-1:0] pr; logic st; integer k;
    na = m0_norm(a); nb = m0_norm(b);
    spa = na[45:45-1]; spb = nb[45:45-1]; s = na[45-2] ^ nb[45-2];
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
      m0_mul = m0_mkx(2'd0, s, na[26+16:26+1] + nb[26+16:26+1] + 26, pr[2*26-1:26], st);
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
  function automatic [2*26+16+2:0] m0_mulx(input [45:0] a, input [45:0] b);
    logic [45:0] na, nb; logic [1:0] spa, spb, sp; logic s; logic [2*26-1:0] pr;
    na = m0_norm(a); nb = m0_norm(b);
    pr = na[26:1] * nb[26:1];
    spa = na[45:45-1]; spb = nb[45:45-1]; s = na[45-2] ^ nb[45-2];
    if (spa == 2'd1 || spb == 2'd1) sp = 2'd1;
    else if (spa == 2'd2 || spb == 2'd2)
      sp = ((spa == 2'd0 && na[26:1] == 0) || (spb == 2'd0 && nb[26:1] == 0)) ? 2'd1 : 2'd2;
    else sp = 2'd0;
    m0_mulx = {sp, s, na[26+16:26+1] + nb[26+16:26+1], pr};
  endfunction
  function automatic [45:0] m0_div(input [45:0] a, input [45:0] b);
    logic [45:0] na, nb; logic [1:0] spa, spb; logic s; logic [2*26+1:0] qr; logic [26:0] q, r;
    na = m0_norm(a); nb = m0_norm(b);
    spa = na[45:45-1]; spb = nb[45:45-1]; s = na[45-2] ^ nb[45-2];
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
      if (q[26]) m0_div = m0_mkx(2'd0, s, na[26+16:26+1] - nb[26+16:26+1] - 26 + 1, q[26:1], (r != 0) | q[0] | na[0] | nb[0]);
      else m0_div = m0_mkx(2'd0, s, na[26+16:26+1] - nb[26+16:26+1] - 26, q[25:0], (r != 0) | na[0] | nb[0]);
    end
  endfunction
  function automatic [45:0] m0_sqrt(input [45:0] a);
    logic [45:0] na; logic [1:0] spa; logic signed [15:0] e; logic [26:0] m; logic [2*26+3:0] rad;
    logic [26+2:0] rem, trial; logic [26:0] root; logic ge; integer i;
    na = m0_norm(a); spa = na[45:45-1];
    if (spa == 2'd1) m0_sqrt = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m0_sqrt = na[45-2] ? m0_mkx(2'd1, 1'b0, 0, 0, 1'b0) : na;
    else if (na[26:1] == 0 && !na[0]) m0_sqrt = na;
    else if (na[45-2]) m0_sqrt = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else begin
      e = na[26+16:26+1];
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
  function automatic m0_lt(input [45:0] a, input [45:0] b);
    logic [45:0] na, nb; logic za, zb, sa, sb, mag_lt; logic signed [15:0] ea, eb;
    na = m0_norm(a); nb = m0_norm(b);
    za = (na[26:1] == 0) && !na[0]; zb = (nb[26:1] == 0) && !nb[0];
    sa = na[45-2] && !za; sb = nb[45-2] && !zb;
    if (na[45:45-1] == 2'd1 || nb[45:45-1] == 2'd1) m0_lt = 1'b0;
    else if (na[45:45-1] == 2'd2 || nb[45:45-1] == 2'd2) begin
      if (na[45:45-1] == 2'd2 && nb[45:45-1] == 2'd2) m0_lt = na[45-2] && !nb[45-2];
      else if (na[45:45-1] == 2'd2) m0_lt = na[45-2];
      else m0_lt = !nb[45-2];
    end else if (za && zb) m0_lt = 1'b0;
    else if (sa != sb) m0_lt = sa;
    else begin
      ea = na[26+16:26+1]; eb = nb[26+16:26+1];
      if (za) mag_lt = 1'b1; else if (zb) mag_lt = 1'b0;
      else mag_lt = (ea < eb) || (ea == eb && (na[26:1] < nb[26:1] || (na[26:1] == nb[26:1] && !na[0] && nb[0])));
      m0_lt = sa ? !mag_lt && !(za && zb) && !m0_eq(na, nb) : mag_lt;
    end
  endfunction
  function automatic m0_eq(input [45:0] a, input [45:0] b);
    logic [45:0] na, nb; logic za, zb;
    na = m0_norm(a); nb = m0_norm(b);
    za = (na[26:1] == 0) && !na[0]; zb = (nb[26:1] == 0) && !nb[0];
    if (na[45:45-1] == 2'd1 || nb[45:45-1] == 2'd1) m0_eq = 1'b0;
    else if (na[45:45-1] == 2'd2 || nb[45:45-1] == 2'd2)
      m0_eq = (na[45:45-1] == nb[45:45-1]) && (na[45-2] == nb[45-2]);
    else if (za || zb) m0_eq = za && zb;
    else m0_eq = (na[45-2] == nb[45-2]) && (na[26+16:26+1] == nb[26+16:26+1]) && (na[26:1] == nb[26:1]) && (na[0] == nb[0]);
  endfunction

  // the fused multiply-add (-1)^np * a * b + (-1)^nc * c, rounded once: the
  // exact 2 XW-bit product and c (its significand at the product's scale)
  // meet in a 2 XW + 2-bit frame, the smaller aligned right with a sticky,
  // and the sum or difference normalizes to the X (the top XW bits, the
  // rest sticky). The specials as IEEE 754 orders them: a NaN operand, an
  // invalid product (inf * 0), an infinite product against the opposite
  // infinite addend, an infinite product, an infinite addend. An exact zero
  // leaves with sign 0 (the caller applies the zero-sign rule); the
  // operands' own stickies fold into the result's (the ALU's unpacked
  // operands carry none).
  function automatic [45:0] m0_fma(input [45:0] a, input [45:0] b, input [45:0] c, input np, input nc);
    logic [45:0] na, nb, ncc; logic [1:0] spa, spb, spc; logic sp, sc, sr, sbig, ssml, a_zero, b_zero, c_zero, neg;
    logic signed [15:0] ea, eb, ec, ep, ecw, ebase; logic signed [16+1:0] d;
    logic [2*26-1:0] pr; logic [2*26+1:0] mp, mc, big, sml, r; logic stp, stc, stb, sts, st; integer sh, k;
    na = m0_norm(a); nb = m0_norm(b); ncc = m0_norm(c);
    spa = na[45:45-1]; spb = nb[45:45-1]; spc = ncc[45:45-1];
    sp = na[45-2] ^ nb[45-2] ^ np; sc = ncc[45-2] ^ nc;
    a_zero = (spa == 2'd0) && na[26:1] == 0 && !na[0]; b_zero = (spb == 2'd0) && nb[26:1] == 0 && !nb[0];
    c_zero = (spc == 2'd0) && ncc[26:1] == 0 && !ncc[0];
    if (spa == 2'd1 || spb == 2'd1 || spc == 2'd1) m0_fma = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if ((spa == 2'd2 && b_zero) || (spb == 2'd2 && a_zero)) m0_fma = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if ((spa == 2'd2 || spb == 2'd2) && spc == 2'd2 && sp != sc) m0_fma = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 || spb == 2'd2) m0_fma = m0_mkx(2'd2, sp, 0, 0, 1'b0);
    else if (spc == 2'd2) m0_fma = m0_mkx(2'd2, sc, 0, 0, 1'b0);
    // an exact zero product (a zero operand's exponent means nothing): the addend, with its negation
    else if (a_zero || b_zero) m0_fma = c_zero ? m0_mkx(2'd0, 1'b0, 0, 0, 1'b0) : {ncc[45:45-1], sc, ncc[45-3:0]};
    else begin
      ea = na[26+16:26+1]; eb = nb[26+16:26+1]; ec = ncc[26+16:26+1];
      pr = na[26:1] * nb[26:1]; mp = {2'b00, pr}; stp = na[0] | nb[0]; ep = ea + eb;
      mc = {2'b00, ncc[26:1], {26{1'b0}}}; stc = ncc[0]; ecw = ec - 26;
      d = $signed({{2{ep[15]}}, ep}) - $signed({{2{ecw[15]}}, ecw});
      // a zero addend (its exponent means nothing): the product stays in place
      if (c_zero) begin big = mp; sml = 0; sbig = sp; ssml = sp; stb = stp; sts = 1'b0; ebase = ep; d = 0; end
      else if (d >= 0) begin big = mp; sml = mc; sbig = sp; ssml = sc; stb = stp; sts = stc; ebase = ep; end
      else begin big = mc; sml = mp; sbig = sc; ssml = sp; stb = stc; sts = stp; ebase = ecw; d = -d; end
      if (d > 2*26 + 2) begin sts = sts | (sml != 0); sml = 0; end
      else begin
        for (sh = 0; sh < 2*26 + 3; sh = sh + 1) begin
          if (sh < d) begin sts = sts | sml[0]; sml = sml >> 1; end
        end
      end
      st = stb | sts;
      if (sbig == ssml) begin r = big + sml; sr = sbig; end
      else begin
        // the difference: the aligned smaller value's sticky borrows one lsb; the sign follows the larger magnitude
        neg = (big < sml) || (big == sml && sts);
        if (neg) begin r = sml - big; sr = ssml; end
        else begin r = big - sml - (sts ? 1'b1 : 1'b0); sr = sbig; end
      end
      if (r == 0) m0_fma = m0_mkx(2'd0, st ? sr : 1'b0, ebase, 0, st);
      else begin
        sh = 0;
        for (k = 0; k < 2*26 + 2; k = k + 1) begin
          if (!r[2*26+1]) begin r = r << 1; sh = sh + 1; end
        end
        st = st | (r[26+1:0] != 0);
        m0_fma = m0_mkx(2'd0, sr, ebase + 26 + 2 - sh, r[2*26+1:26+2], st);
      end
    end
  endfunction

  // fp16 pattern -> V (bit VW = denormal-read flag returned beside)
  function automatic [30:0] m0_unpack_s(input [15:0] b, input daz);
    logic [4:0] e; logic [9:0] m; logic [10:0] sig; logic signed [15:0] ex; logic den, s;
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
  function automatic [10+16-1:0] m0_pack_fp16(input [45:0] x0, input [2:0] rnd, input [7:0] word, input ftz);
    logic [45:0] x; logic [1:0] sp; logic s; logic signed [15:0] e, eu, biased; logic [25:0] sig;
    logic st, inexact, up, upn, half_eq, gt_half, tiny, ovf, unf, carry_n, to_inf; integer sh, shn, sht;
    logic [26:0] keep, rest, keepn, restn, halfv, halfn; logic [26+8:0] fint, fintn; logic [10-1:0] fl;
    logic [16+16:0] code; logic [16:0] mag; logic [16-1:0] outb;
    x = m0_norm(x0); sp = x[45:45-1]; s = x[45-2] & 1; sig = x[26:1]; st = x[0]; e = x[26+16:26+1];
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
      code = (biased < 1) ? mag : ((biased << 10) + mag - ({{(16+16){1'b0}}, 1'b1} << 10));
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

// alu_core_m1_pkg: the exact-arithmetic functions of mode 1 (1xbf16)
package alu_core_m1_pkg;

  // ---- m1: V = {special[1:0], sign, exp[16] (signed), sig[11]}
  //           X = {special[1:0], sign, exp[16] (signed), sig[26], sticky}
  localparam int m1_SW = 11, m1_EW = 16, m1_XW = 26;
  localparam int m1_VW = 30, m1_XT = 46;
  function automatic [29:0] m1_mkv(input [1:0] sp, input s, input signed [15:0] e, input [10:0] sig);
    m1_mkv = {sp, s, e, sig};
  endfunction
  function automatic [45:0] m1_mkx(input [1:0] sp, input s, input signed [15:0] e, input [25:0] sig, input st);
    m1_mkx = {sp, s, e, sig, st};
  endfunction
  function automatic [45:0] m1_x(input [29:0] v);   // widen V to X
    m1_x = {v[29:29-1], v[29-2], v[29-3 -: 16], {{(26-11){1'b0}}, v[10:0]}, 1'b0};
  endfunction
  // normalize: leading one at bit XW-1 (zero stays zero)
  function automatic [45:0] m1_norm(input [45:0] x);
    logic [25:0] s; logic signed [15:0] e; integer k;
    s = x[26:1]; e = x[26+16:26+1];
    if (s != 0) begin
      for (k = 16; k >= 1; k = k / 2) begin
        if (k < 26) begin
          if (s[25 -: 1] == 1'b0 && (s >> (26 - k)) == 0) begin
            s = s << k; e = e - k;
          end
        end
      end
    end
    m1_norm = {x[45:45-1], x[45-2], e, s, x[0]};
  endfunction

  function automatic m1_rup(input [2:0] rnd, input s, input inexact, input [26:0] rest, input [26:0] halfv,
                             input st, input lsb, input [26+8:0] fint, input [7:0] word);
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
  function automatic [45:0] m1_add(input [45:0] a, input [45:0] b, input sub);
    logic [45:0] na, nb, big, sml; logic [1:0] spa, spb; logic sa, sb, sr, sw;
    logic signed [15:0] ea, eb, d; logic [26:0] ms, mb, r; logic st, stb; integer sh;
    na = m1_norm(a); nb = m1_norm(b);
    spa = na[45:45-1]; spb = nb[45:45-1];
    sa = na[45-2]; sb = nb[45-2] ^ sub;
    if (spa == 2'd1 || spb == 2'd1) m1_add = m1_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 && spb == 2'd2) m1_add = (sa == sb) ? m1_mkx(2'd2, sa, 0, 0, 1'b0) : m1_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m1_add = m1_mkx(2'd2, sa, 0, 0, 1'b0);
    else if (spb == 2'd2) m1_add = m1_mkx(2'd2, sb, 0, 0, 1'b0);
    else if (na[26:1] == 0 && !na[0]) m1_add = {nb[45:45-1], sb, nb[45-3:0]};
    else if (nb[26:1] == 0 && !nb[0]) m1_add = na;
    else begin
      ea = na[26+16:26+1]; eb = nb[26+16:26+1];
      // order by magnitude (both normalized): larger exponent, then sig
      if (ea > eb || (ea == eb && na[26:1] >= nb[26:1])) begin big = na; sml = nb; sw = 1'b0; end
      else begin big = nb; sml = na; sw = 1'b1; end
      d = big[26+16:26+1] - sml[26+16:26+1];
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
      if (r[26]) begin st = st | r[0]; r = r >> 1; m1_add = m1_mkx(2'd0, sr, big[26+16:26+1] + 1, r[25:0], st); end
      else m1_add = m1_mkx(2'd0, sr, big[26+16:26+1], r[25:0], st);
    end
  endfunction
  function automatic [45:0] m1_mul(input [45:0] a, input [45:0] b);
    logic [45:0] na, nb; logic [1:0] spa, spb; logic s; logic [2*26-1:0] pr; logic st; integer k;
    na = m1_norm(a); nb = m1_norm(b);
    spa = na[45:45-1]; spb = nb[45:45-1]; s = na[45-2] ^ nb[45-2];
    if (spa == 2'd1 || spb == 2'd1) m1_mul = m1_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 || spb == 2'd2) begin
      if ((spa == 2'd0 && na[26:1] == 0 && !na[0]) || (spb == 2'd0 && nb[26:1] == 0 && !nb[0]))
        m1_mul = m1_mkx(2'd1, 1'b0, 0, 0, 1'b0);
      else m1_mul = m1_mkx(2'd2, s, 0, 0, 1'b0);
    end else begin
      pr = na[26:1] * nb[26:1];
      st = na[0] | nb[0];
      // keep the top XW bits of the product, the rest folds into sticky
      st = st | (pr[25:0] != 0);
      m1_mul = m1_mkx(2'd0, s, na[26+16:26+1] + nb[26+16:26+1] + 26, pr[2*26-1:26], st);
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
  function automatic [2*26+1:0] m1_udiv(input [25:0] a, input [25:0] dv);
    logic [26+1:0] r; logic [26:0] q; logic ge; integer i;
    r = {2'b0, a}; q = 0;
    for (i = 26; i >= 0; i = i - 1) begin
      ge = (r >= {2'b0, dv});
      r = ge ? r - {2'b0, dv} : r;
      q = {q[25:0], ge};
      if (i > 0) r = {r[26:0], 1'b0};
    end
    m1_udiv = {q, r[26:0]};
  endfunction
  // the exact product: {special[1:0], sign, exp[EW], sig[2XW]} (no sticky)
  function automatic [2*26+16+2:0] m1_mulx(input [45:0] a, input [45:0] b);
    logic [45:0] na, nb; logic [1:0] spa, spb, sp; logic s; logic [2*26-1:0] pr;
    na = m1_norm(a); nb = m1_norm(b);
    pr = na[26:1] * nb[26:1];
    spa = na[45:45-1]; spb = nb[45:45-1]; s = na[45-2] ^ nb[45-2];
    if (spa == 2'd1 || spb == 2'd1) sp = 2'd1;
    else if (spa == 2'd2 || spb == 2'd2)
      sp = ((spa == 2'd0 && na[26:1] == 0) || (spb == 2'd0 && nb[26:1] == 0)) ? 2'd1 : 2'd2;
    else sp = 2'd0;
    m1_mulx = {sp, s, na[26+16:26+1] + nb[26+16:26+1], pr};
  endfunction
  function automatic [45:0] m1_div(input [45:0] a, input [45:0] b);
    logic [45:0] na, nb; logic [1:0] spa, spb; logic s; logic [2*26+1:0] qr; logic [26:0] q, r;
    na = m1_norm(a); nb = m1_norm(b);
    spa = na[45:45-1]; spb = nb[45:45-1]; s = na[45-2] ^ nb[45-2];
    if (spa == 2'd1 || spb == 2'd1) m1_div = m1_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 && spb == 2'd2) m1_div = m1_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m1_div = m1_mkx(2'd2, s, 0, 0, 1'b0);
    else if (spb == 2'd2) m1_div = m1_mkx(2'd0, s, 0, 0, 1'b0);
    else if (nb[26:1] == 0 && !nb[0]) begin
      if (na[26:1] == 0 && !na[0]) m1_div = m1_mkx(2'd1, 1'b0, 0, 0, 1'b0);
      else m1_div = m1_mkx(2'd2, s, 0, 0, 1'b0);
    end else if (na[26:1] == 0 && !na[0]) m1_div = m1_mkx(2'd0, s, 0, 0, 1'b0);
    else begin
      qr = m1_udiv(na[26:1], nb[26:1]);     // both normalized: nonzero finite
      q = qr[2*26+1:26+1]; r = qr[26:0];
      // q < 2^(XW+1): drop one bit when it carries
      if (q[26]) m1_div = m1_mkx(2'd0, s, na[26+16:26+1] - nb[26+16:26+1] - 26 + 1, q[26:1], (r != 0) | q[0] | na[0] | nb[0]);
      else m1_div = m1_mkx(2'd0, s, na[26+16:26+1] - nb[26+16:26+1] - 26, q[25:0], (r != 0) | na[0] | nb[0]);
    end
  endfunction
  function automatic [45:0] m1_sqrt(input [45:0] a);
    logic [45:0] na; logic [1:0] spa; logic signed [15:0] e; logic [26:0] m; logic [2*26+3:0] rad;
    logic [26+2:0] rem, trial; logic [26:0] root; logic ge; integer i;
    na = m1_norm(a); spa = na[45:45-1];
    if (spa == 2'd1) m1_sqrt = m1_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m1_sqrt = na[45-2] ? m1_mkx(2'd1, 1'b0, 0, 0, 1'b0) : na;
    else if (na[26:1] == 0 && !na[0]) m1_sqrt = na;
    else if (na[45-2]) m1_sqrt = m1_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else begin
      e = na[26+16:26+1];
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
      m1_sqrt = m1_mkx(2'd0, 1'b0, (e >>> 1) - 13 + 1, root[26:1], (rem != 0) | root[0] | na[0]);
    end
  endfunction
  // X ordering treats NaN as unordered and compares finite values by sign and magnitude
  function automatic m1_lt(input [45:0] a, input [45:0] b);
    logic [45:0] na, nb; logic za, zb, sa, sb, mag_lt; logic signed [15:0] ea, eb;
    na = m1_norm(a); nb = m1_norm(b);
    za = (na[26:1] == 0) && !na[0]; zb = (nb[26:1] == 0) && !nb[0];
    sa = na[45-2] && !za; sb = nb[45-2] && !zb;
    if (na[45:45-1] == 2'd1 || nb[45:45-1] == 2'd1) m1_lt = 1'b0;
    else if (na[45:45-1] == 2'd2 || nb[45:45-1] == 2'd2) begin
      if (na[45:45-1] == 2'd2 && nb[45:45-1] == 2'd2) m1_lt = na[45-2] && !nb[45-2];
      else if (na[45:45-1] == 2'd2) m1_lt = na[45-2];
      else m1_lt = !nb[45-2];
    end else if (za && zb) m1_lt = 1'b0;
    else if (sa != sb) m1_lt = sa;
    else begin
      ea = na[26+16:26+1]; eb = nb[26+16:26+1];
      if (za) mag_lt = 1'b1; else if (zb) mag_lt = 1'b0;
      else mag_lt = (ea < eb) || (ea == eb && (na[26:1] < nb[26:1] || (na[26:1] == nb[26:1] && !na[0] && nb[0])));
      m1_lt = sa ? !mag_lt && !(za && zb) && !m1_eq(na, nb) : mag_lt;
    end
  endfunction
  function automatic m1_eq(input [45:0] a, input [45:0] b);
    logic [45:0] na, nb; logic za, zb;
    na = m1_norm(a); nb = m1_norm(b);
    za = (na[26:1] == 0) && !na[0]; zb = (nb[26:1] == 0) && !nb[0];
    if (na[45:45-1] == 2'd1 || nb[45:45-1] == 2'd1) m1_eq = 1'b0;
    else if (na[45:45-1] == 2'd2 || nb[45:45-1] == 2'd2)
      m1_eq = (na[45:45-1] == nb[45:45-1]) && (na[45-2] == nb[45-2]);
    else if (za || zb) m1_eq = za && zb;
    else m1_eq = (na[45-2] == nb[45-2]) && (na[26+16:26+1] == nb[26+16:26+1]) && (na[26:1] == nb[26:1]) && (na[0] == nb[0]);
  endfunction

  // the fused multiply-add (-1)^np * a * b + (-1)^nc * c, rounded once: the
  // exact 2 XW-bit product and c (its significand at the product's scale)
  // meet in a 2 XW + 2-bit frame, the smaller aligned right with a sticky,
  // and the sum or difference normalizes to the X (the top XW bits, the
  // rest sticky). The specials as IEEE 754 orders them: a NaN operand, an
  // invalid product (inf * 0), an infinite product against the opposite
  // infinite addend, an infinite product, an infinite addend. An exact zero
  // leaves with sign 0 (the caller applies the zero-sign rule); the
  // operands' own stickies fold into the result's (the ALU's unpacked
  // operands carry none).
  function automatic [45:0] m1_fma(input [45:0] a, input [45:0] b, input [45:0] c, input np, input nc);
    logic [45:0] na, nb, ncc; logic [1:0] spa, spb, spc; logic sp, sc, sr, sbig, ssml, a_zero, b_zero, c_zero, neg;
    logic signed [15:0] ea, eb, ec, ep, ecw, ebase; logic signed [16+1:0] d;
    logic [2*26-1:0] pr; logic [2*26+1:0] mp, mc, big, sml, r; logic stp, stc, stb, sts, st; integer sh, k;
    na = m1_norm(a); nb = m1_norm(b); ncc = m1_norm(c);
    spa = na[45:45-1]; spb = nb[45:45-1]; spc = ncc[45:45-1];
    sp = na[45-2] ^ nb[45-2] ^ np; sc = ncc[45-2] ^ nc;
    a_zero = (spa == 2'd0) && na[26:1] == 0 && !na[0]; b_zero = (spb == 2'd0) && nb[26:1] == 0 && !nb[0];
    c_zero = (spc == 2'd0) && ncc[26:1] == 0 && !ncc[0];
    if (spa == 2'd1 || spb == 2'd1 || spc == 2'd1) m1_fma = m1_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if ((spa == 2'd2 && b_zero) || (spb == 2'd2 && a_zero)) m1_fma = m1_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if ((spa == 2'd2 || spb == 2'd2) && spc == 2'd2 && sp != sc) m1_fma = m1_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 || spb == 2'd2) m1_fma = m1_mkx(2'd2, sp, 0, 0, 1'b0);
    else if (spc == 2'd2) m1_fma = m1_mkx(2'd2, sc, 0, 0, 1'b0);
    // an exact zero product (a zero operand's exponent means nothing): the addend, with its negation
    else if (a_zero || b_zero) m1_fma = c_zero ? m1_mkx(2'd0, 1'b0, 0, 0, 1'b0) : {ncc[45:45-1], sc, ncc[45-3:0]};
    else begin
      ea = na[26+16:26+1]; eb = nb[26+16:26+1]; ec = ncc[26+16:26+1];
      pr = na[26:1] * nb[26:1]; mp = {2'b00, pr}; stp = na[0] | nb[0]; ep = ea + eb;
      mc = {2'b00, ncc[26:1], {26{1'b0}}}; stc = ncc[0]; ecw = ec - 26;
      d = $signed({{2{ep[15]}}, ep}) - $signed({{2{ecw[15]}}, ecw});
      // a zero addend (its exponent means nothing): the product stays in place
      if (c_zero) begin big = mp; sml = 0; sbig = sp; ssml = sp; stb = stp; sts = 1'b0; ebase = ep; d = 0; end
      else if (d >= 0) begin big = mp; sml = mc; sbig = sp; ssml = sc; stb = stp; sts = stc; ebase = ep; end
      else begin big = mc; sml = mp; sbig = sc; ssml = sp; stb = stc; sts = stp; ebase = ecw; d = -d; end
      if (d > 2*26 + 2) begin sts = sts | (sml != 0); sml = 0; end
      else begin
        for (sh = 0; sh < 2*26 + 3; sh = sh + 1) begin
          if (sh < d) begin sts = sts | sml[0]; sml = sml >> 1; end
        end
      end
      st = stb | sts;
      if (sbig == ssml) begin r = big + sml; sr = sbig; end
      else begin
        // the difference: the aligned smaller value's sticky borrows one lsb; the sign follows the larger magnitude
        neg = (big < sml) || (big == sml && sts);
        if (neg) begin r = sml - big; sr = ssml; end
        else begin r = big - sml - (sts ? 1'b1 : 1'b0); sr = sbig; end
      end
      if (r == 0) m1_fma = m1_mkx(2'd0, st ? sr : 1'b0, ebase, 0, st);
      else begin
        sh = 0;
        for (k = 0; k < 2*26 + 2; k = k + 1) begin
          if (!r[2*26+1]) begin r = r << 1; sh = sh + 1; end
        end
        st = st | (r[26+1:0] != 0);
        m1_fma = m1_mkx(2'd0, sr, ebase + 26 + 2 - sh, r[2*26+1:26+2], st);
      end
    end
  endfunction

  // bf16 pattern -> V (bit VW = denormal-read flag returned beside)
  function automatic [30:0] m1_unpack_s(input [15:0] b, input daz);
    logic [7:0] e; logic [6:0] m; logic [10:0] sig; logic signed [15:0] ex; logic den, s;
    e = b[14:7]; m = b[6:0]; s = b[15]; den = 1'b0; sig = 0; ex = 0;
    if ((e == 8'd255 && m != 0)) m1_unpack_s = {1'b0, m1_mkv(2'd1, 1'b0, 0, 0)};
    else if ((e == 8'd255 && m == 0)) m1_unpack_s = {1'b0, m1_mkv(2'd2, s, 0, 0)};
    else begin
    if (e == 0) begin sig = {{(11-7){1'b0}}, m}; ex = -133; if (m != 0) den = 1'b1; if (daz && m != 0) sig = 0; end
    else begin sig = {{(11-7-1){1'b0}}, 1'b1, m}; ex = e - 134; end
      m1_unpack_s = {den, m1_mkv(2'd0, s, ex, sig)};
    end
  endfunction

  // X -> bf16 (bf16): sign(1) exp 8 man 7, top field 254, max finite 15'd32639
  function automatic [10+16-1:0] m1_pack_bf16(input [45:0] x0, input [2:0] rnd, input [7:0] word, input ftz);
    logic [45:0] x; logic [1:0] sp; logic s; logic signed [15:0] e, eu, biased; logic [25:0] sig;
    logic st, inexact, up, upn, half_eq, gt_half, tiny, ovf, unf, carry_n, to_inf; integer sh, shn, sht;
    logic [26:0] keep, rest, keepn, restn, halfv, halfn; logic [26+8:0] fint, fintn; logic [10-1:0] fl;
    logic [16+16:0] code; logic [16:0] mag; logic [16-1:0] outb;
    x = m1_norm(x0); sp = x[45:45-1]; s = x[45-2] & 1; sig = x[26:1]; st = x[0]; e = x[26+16:26+1];
    fl = 0; outb = 0;
    if (sp == 2'd1) begin fl[5] = 1'b1; outb = 16'd32704; end
    else if (sp == 2'd2) begin
      outb = {s, 15'd32640}; if (!1) begin fl[4] = 1'b1; fl[2] = 1'b1; end
    end else if (sig == 0 && !st) begin outb = 1 ? 0 : {s, {15{1'b0}}}; end
    else begin
      if (sig == 0) begin sig = 1 << 25; e = e - (2*26-1); end // normalize the lone sticky's tiny value
      eu = e + 25;                 // exponent of the leading one
      biased = eu + 127;
      shn = 26 - 1 - 7;           // bits dropped at the normal precision
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
      up = m1_rup(rnd, s, inexact, rest, halfv, st, keep[0], fint, word);
      upn = m1_rup(rnd, s, (restn != 0) | st, restn, halfn, st, keepn[0], fintn, word);
      carry_n = ((keepn + upn) == ({{26{1'b0}}, 1'b1} << (7 + 1)));
      mag = keep + up;
      if (biased < 1) biased = 0;
      code = (biased < 1) ? mag : ((biased << 7) + mag - ({{(16+16){1'b0}}, 1'b1} << 7));
      tiny = 0 ? (eu < -126) : ((eu < -126) && !(eu == -126 - 1 && carry_n) && !(eu + 127 == 0 && carry_n));
      ovf = (code > 15'd32639);
      if (ovf) begin
        to_inf = 1 && (rnd == 3'd0 || (rnd == 3'd3 && !s) || (rnd == 3'd2 && s) || rnd == 3'd5 || (rnd == 3'd4 && (eu > 127 || up)));
        outb = to_inf ? {s, 15'd32640} : {s, 15'd32639};
        fl[2] = 1'b1; fl[4] = 1'b1;
      end else begin
        outb = {s, code[14:0]};
        if (inexact) fl[4] = 1'b1;
        if (tiny && inexact) fl[3] = 1'b1;
        if (ftz && code[15-1:7] == 0 && code[6:0] != 0) begin
          outb = {s, {15{1'b0}}}; fl[4] = 1'b1; fl[3] = 1'b1;
        end

      end
    end
    m1_pack_bf16 = {fl, outb};
  endfunction
endpackage

// alu_core_m2_pkg: the exact-arithmetic functions of mode 2 (1xfp8e5m2)
package alu_core_m2_pkg;

  // ---- m2: V = {special[1:0], sign, exp[16] (signed), sig[11]}
  //           X = {special[1:0], sign, exp[16] (signed), sig[26], sticky}
  localparam int m2_SW = 11, m2_EW = 16, m2_XW = 26;
  localparam int m2_VW = 30, m2_XT = 46;
  function automatic [29:0] m2_mkv(input [1:0] sp, input s, input signed [15:0] e, input [10:0] sig);
    m2_mkv = {sp, s, e, sig};
  endfunction
  function automatic [45:0] m2_mkx(input [1:0] sp, input s, input signed [15:0] e, input [25:0] sig, input st);
    m2_mkx = {sp, s, e, sig, st};
  endfunction
  function automatic [45:0] m2_x(input [29:0] v);   // widen V to X
    m2_x = {v[29:29-1], v[29-2], v[29-3 -: 16], {{(26-11){1'b0}}, v[10:0]}, 1'b0};
  endfunction
  // normalize: leading one at bit XW-1 (zero stays zero)
  function automatic [45:0] m2_norm(input [45:0] x);
    logic [25:0] s; logic signed [15:0] e; integer k;
    s = x[26:1]; e = x[26+16:26+1];
    if (s != 0) begin
      for (k = 16; k >= 1; k = k / 2) begin
        if (k < 26) begin
          if (s[25 -: 1] == 1'b0 && (s >> (26 - k)) == 0) begin
            s = s << k; e = e - k;
          end
        end
      end
    end
    m2_norm = {x[45:45-1], x[45-2], e, s, x[0]};
  endfunction

  function automatic m2_rup(input [2:0] rnd, input s, input inexact, input [26:0] rest, input [26:0] halfv,
                             input st, input lsb, input [26+8:0] fint, input [7:0] word);
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
  function automatic [45:0] m2_add(input [45:0] a, input [45:0] b, input sub);
    logic [45:0] na, nb, big, sml; logic [1:0] spa, spb; logic sa, sb, sr, sw;
    logic signed [15:0] ea, eb, d; logic [26:0] ms, mb, r; logic st, stb; integer sh;
    na = m2_norm(a); nb = m2_norm(b);
    spa = na[45:45-1]; spb = nb[45:45-1];
    sa = na[45-2]; sb = nb[45-2] ^ sub;
    if (spa == 2'd1 || spb == 2'd1) m2_add = m2_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 && spb == 2'd2) m2_add = (sa == sb) ? m2_mkx(2'd2, sa, 0, 0, 1'b0) : m2_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m2_add = m2_mkx(2'd2, sa, 0, 0, 1'b0);
    else if (spb == 2'd2) m2_add = m2_mkx(2'd2, sb, 0, 0, 1'b0);
    else if (na[26:1] == 0 && !na[0]) m2_add = {nb[45:45-1], sb, nb[45-3:0]};
    else if (nb[26:1] == 0 && !nb[0]) m2_add = na;
    else begin
      ea = na[26+16:26+1]; eb = nb[26+16:26+1];
      // order by magnitude (both normalized): larger exponent, then sig
      if (ea > eb || (ea == eb && na[26:1] >= nb[26:1])) begin big = na; sml = nb; sw = 1'b0; end
      else begin big = nb; sml = na; sw = 1'b1; end
      d = big[26+16:26+1] - sml[26+16:26+1];
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
      if (r[26]) begin st = st | r[0]; r = r >> 1; m2_add = m2_mkx(2'd0, sr, big[26+16:26+1] + 1, r[25:0], st); end
      else m2_add = m2_mkx(2'd0, sr, big[26+16:26+1], r[25:0], st);
    end
  endfunction
  function automatic [45:0] m2_mul(input [45:0] a, input [45:0] b);
    logic [45:0] na, nb; logic [1:0] spa, spb; logic s; logic [2*26-1:0] pr; logic st; integer k;
    na = m2_norm(a); nb = m2_norm(b);
    spa = na[45:45-1]; spb = nb[45:45-1]; s = na[45-2] ^ nb[45-2];
    if (spa == 2'd1 || spb == 2'd1) m2_mul = m2_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 || spb == 2'd2) begin
      if ((spa == 2'd0 && na[26:1] == 0 && !na[0]) || (spb == 2'd0 && nb[26:1] == 0 && !nb[0]))
        m2_mul = m2_mkx(2'd1, 1'b0, 0, 0, 1'b0);
      else m2_mul = m2_mkx(2'd2, s, 0, 0, 1'b0);
    end else begin
      pr = na[26:1] * nb[26:1];
      st = na[0] | nb[0];
      // keep the top XW bits of the product, the rest folds into sticky
      st = st | (pr[25:0] != 0);
      m2_mul = m2_mkx(2'd0, s, na[26+16:26+1] + nb[26+16:26+1] + 26, pr[2*26-1:26], st);
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
  function automatic [2*26+1:0] m2_udiv(input [25:0] a, input [25:0] dv);
    logic [26+1:0] r; logic [26:0] q; logic ge; integer i;
    r = {2'b0, a}; q = 0;
    for (i = 26; i >= 0; i = i - 1) begin
      ge = (r >= {2'b0, dv});
      r = ge ? r - {2'b0, dv} : r;
      q = {q[25:0], ge};
      if (i > 0) r = {r[26:0], 1'b0};
    end
    m2_udiv = {q, r[26:0]};
  endfunction
  // the exact product: {special[1:0], sign, exp[EW], sig[2XW]} (no sticky)
  function automatic [2*26+16+2:0] m2_mulx(input [45:0] a, input [45:0] b);
    logic [45:0] na, nb; logic [1:0] spa, spb, sp; logic s; logic [2*26-1:0] pr;
    na = m2_norm(a); nb = m2_norm(b);
    pr = na[26:1] * nb[26:1];
    spa = na[45:45-1]; spb = nb[45:45-1]; s = na[45-2] ^ nb[45-2];
    if (spa == 2'd1 || spb == 2'd1) sp = 2'd1;
    else if (spa == 2'd2 || spb == 2'd2)
      sp = ((spa == 2'd0 && na[26:1] == 0) || (spb == 2'd0 && nb[26:1] == 0)) ? 2'd1 : 2'd2;
    else sp = 2'd0;
    m2_mulx = {sp, s, na[26+16:26+1] + nb[26+16:26+1], pr};
  endfunction
  function automatic [45:0] m2_div(input [45:0] a, input [45:0] b);
    logic [45:0] na, nb; logic [1:0] spa, spb; logic s; logic [2*26+1:0] qr; logic [26:0] q, r;
    na = m2_norm(a); nb = m2_norm(b);
    spa = na[45:45-1]; spb = nb[45:45-1]; s = na[45-2] ^ nb[45-2];
    if (spa == 2'd1 || spb == 2'd1) m2_div = m2_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 && spb == 2'd2) m2_div = m2_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m2_div = m2_mkx(2'd2, s, 0, 0, 1'b0);
    else if (spb == 2'd2) m2_div = m2_mkx(2'd0, s, 0, 0, 1'b0);
    else if (nb[26:1] == 0 && !nb[0]) begin
      if (na[26:1] == 0 && !na[0]) m2_div = m2_mkx(2'd1, 1'b0, 0, 0, 1'b0);
      else m2_div = m2_mkx(2'd2, s, 0, 0, 1'b0);
    end else if (na[26:1] == 0 && !na[0]) m2_div = m2_mkx(2'd0, s, 0, 0, 1'b0);
    else begin
      qr = m2_udiv(na[26:1], nb[26:1]);     // both normalized: nonzero finite
      q = qr[2*26+1:26+1]; r = qr[26:0];
      // q < 2^(XW+1): drop one bit when it carries
      if (q[26]) m2_div = m2_mkx(2'd0, s, na[26+16:26+1] - nb[26+16:26+1] - 26 + 1, q[26:1], (r != 0) | q[0] | na[0] | nb[0]);
      else m2_div = m2_mkx(2'd0, s, na[26+16:26+1] - nb[26+16:26+1] - 26, q[25:0], (r != 0) | na[0] | nb[0]);
    end
  endfunction
  function automatic [45:0] m2_sqrt(input [45:0] a);
    logic [45:0] na; logic [1:0] spa; logic signed [15:0] e; logic [26:0] m; logic [2*26+3:0] rad;
    logic [26+2:0] rem, trial; logic [26:0] root; logic ge; integer i;
    na = m2_norm(a); spa = na[45:45-1];
    if (spa == 2'd1) m2_sqrt = m2_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m2_sqrt = na[45-2] ? m2_mkx(2'd1, 1'b0, 0, 0, 1'b0) : na;
    else if (na[26:1] == 0 && !na[0]) m2_sqrt = na;
    else if (na[45-2]) m2_sqrt = m2_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else begin
      e = na[26+16:26+1];
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
      m2_sqrt = m2_mkx(2'd0, 1'b0, (e >>> 1) - 13 + 1, root[26:1], (rem != 0) | root[0] | na[0]);
    end
  endfunction
  // X ordering treats NaN as unordered and compares finite values by sign and magnitude
  function automatic m2_lt(input [45:0] a, input [45:0] b);
    logic [45:0] na, nb; logic za, zb, sa, sb, mag_lt; logic signed [15:0] ea, eb;
    na = m2_norm(a); nb = m2_norm(b);
    za = (na[26:1] == 0) && !na[0]; zb = (nb[26:1] == 0) && !nb[0];
    sa = na[45-2] && !za; sb = nb[45-2] && !zb;
    if (na[45:45-1] == 2'd1 || nb[45:45-1] == 2'd1) m2_lt = 1'b0;
    else if (na[45:45-1] == 2'd2 || nb[45:45-1] == 2'd2) begin
      if (na[45:45-1] == 2'd2 && nb[45:45-1] == 2'd2) m2_lt = na[45-2] && !nb[45-2];
      else if (na[45:45-1] == 2'd2) m2_lt = na[45-2];
      else m2_lt = !nb[45-2];
    end else if (za && zb) m2_lt = 1'b0;
    else if (sa != sb) m2_lt = sa;
    else begin
      ea = na[26+16:26+1]; eb = nb[26+16:26+1];
      if (za) mag_lt = 1'b1; else if (zb) mag_lt = 1'b0;
      else mag_lt = (ea < eb) || (ea == eb && (na[26:1] < nb[26:1] || (na[26:1] == nb[26:1] && !na[0] && nb[0])));
      m2_lt = sa ? !mag_lt && !(za && zb) && !m2_eq(na, nb) : mag_lt;
    end
  endfunction
  function automatic m2_eq(input [45:0] a, input [45:0] b);
    logic [45:0] na, nb; logic za, zb;
    na = m2_norm(a); nb = m2_norm(b);
    za = (na[26:1] == 0) && !na[0]; zb = (nb[26:1] == 0) && !nb[0];
    if (na[45:45-1] == 2'd1 || nb[45:45-1] == 2'd1) m2_eq = 1'b0;
    else if (na[45:45-1] == 2'd2 || nb[45:45-1] == 2'd2)
      m2_eq = (na[45:45-1] == nb[45:45-1]) && (na[45-2] == nb[45-2]);
    else if (za || zb) m2_eq = za && zb;
    else m2_eq = (na[45-2] == nb[45-2]) && (na[26+16:26+1] == nb[26+16:26+1]) && (na[26:1] == nb[26:1]) && (na[0] == nb[0]);
  endfunction

  // the fused multiply-add (-1)^np * a * b + (-1)^nc * c, rounded once: the
  // exact 2 XW-bit product and c (its significand at the product's scale)
  // meet in a 2 XW + 2-bit frame, the smaller aligned right with a sticky,
  // and the sum or difference normalizes to the X (the top XW bits, the
  // rest sticky). The specials as IEEE 754 orders them: a NaN operand, an
  // invalid product (inf * 0), an infinite product against the opposite
  // infinite addend, an infinite product, an infinite addend. An exact zero
  // leaves with sign 0 (the caller applies the zero-sign rule); the
  // operands' own stickies fold into the result's (the ALU's unpacked
  // operands carry none).
  function automatic [45:0] m2_fma(input [45:0] a, input [45:0] b, input [45:0] c, input np, input nc);
    logic [45:0] na, nb, ncc; logic [1:0] spa, spb, spc; logic sp, sc, sr, sbig, ssml, a_zero, b_zero, c_zero, neg;
    logic signed [15:0] ea, eb, ec, ep, ecw, ebase; logic signed [16+1:0] d;
    logic [2*26-1:0] pr; logic [2*26+1:0] mp, mc, big, sml, r; logic stp, stc, stb, sts, st; integer sh, k;
    na = m2_norm(a); nb = m2_norm(b); ncc = m2_norm(c);
    spa = na[45:45-1]; spb = nb[45:45-1]; spc = ncc[45:45-1];
    sp = na[45-2] ^ nb[45-2] ^ np; sc = ncc[45-2] ^ nc;
    a_zero = (spa == 2'd0) && na[26:1] == 0 && !na[0]; b_zero = (spb == 2'd0) && nb[26:1] == 0 && !nb[0];
    c_zero = (spc == 2'd0) && ncc[26:1] == 0 && !ncc[0];
    if (spa == 2'd1 || spb == 2'd1 || spc == 2'd1) m2_fma = m2_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if ((spa == 2'd2 && b_zero) || (spb == 2'd2 && a_zero)) m2_fma = m2_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if ((spa == 2'd2 || spb == 2'd2) && spc == 2'd2 && sp != sc) m2_fma = m2_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 || spb == 2'd2) m2_fma = m2_mkx(2'd2, sp, 0, 0, 1'b0);
    else if (spc == 2'd2) m2_fma = m2_mkx(2'd2, sc, 0, 0, 1'b0);
    // an exact zero product (a zero operand's exponent means nothing): the addend, with its negation
    else if (a_zero || b_zero) m2_fma = c_zero ? m2_mkx(2'd0, 1'b0, 0, 0, 1'b0) : {ncc[45:45-1], sc, ncc[45-3:0]};
    else begin
      ea = na[26+16:26+1]; eb = nb[26+16:26+1]; ec = ncc[26+16:26+1];
      pr = na[26:1] * nb[26:1]; mp = {2'b00, pr}; stp = na[0] | nb[0]; ep = ea + eb;
      mc = {2'b00, ncc[26:1], {26{1'b0}}}; stc = ncc[0]; ecw = ec - 26;
      d = $signed({{2{ep[15]}}, ep}) - $signed({{2{ecw[15]}}, ecw});
      // a zero addend (its exponent means nothing): the product stays in place
      if (c_zero) begin big = mp; sml = 0; sbig = sp; ssml = sp; stb = stp; sts = 1'b0; ebase = ep; d = 0; end
      else if (d >= 0) begin big = mp; sml = mc; sbig = sp; ssml = sc; stb = stp; sts = stc; ebase = ep; end
      else begin big = mc; sml = mp; sbig = sc; ssml = sp; stb = stc; sts = stp; ebase = ecw; d = -d; end
      if (d > 2*26 + 2) begin sts = sts | (sml != 0); sml = 0; end
      else begin
        for (sh = 0; sh < 2*26 + 3; sh = sh + 1) begin
          if (sh < d) begin sts = sts | sml[0]; sml = sml >> 1; end
        end
      end
      st = stb | sts;
      if (sbig == ssml) begin r = big + sml; sr = sbig; end
      else begin
        // the difference: the aligned smaller value's sticky borrows one lsb; the sign follows the larger magnitude
        neg = (big < sml) || (big == sml && sts);
        if (neg) begin r = sml - big; sr = ssml; end
        else begin r = big - sml - (sts ? 1'b1 : 1'b0); sr = sbig; end
      end
      if (r == 0) m2_fma = m2_mkx(2'd0, st ? sr : 1'b0, ebase, 0, st);
      else begin
        sh = 0;
        for (k = 0; k < 2*26 + 2; k = k + 1) begin
          if (!r[2*26+1]) begin r = r << 1; sh = sh + 1; end
        end
        st = st | (r[26+1:0] != 0);
        m2_fma = m2_mkx(2'd0, sr, ebase + 26 + 2 - sh, r[2*26+1:26+2], st);
      end
    end
  endfunction

  // fp8e5m2 pattern -> V (bit VW = denormal-read flag returned beside)
  function automatic [30:0] m2_unpack_s(input [7:0] b, input daz);
    logic [4:0] e; logic [1:0] m; logic [10:0] sig; logic signed [15:0] ex; logic den, s;
    e = b[6:2]; m = b[1:0]; s = b[7]; den = 1'b0; sig = 0; ex = 0;
    if ((e == 5'd31 && m != 0)) m2_unpack_s = {1'b0, m2_mkv(2'd1, 1'b0, 0, 0)};
    else if ((e == 5'd31 && m == 0)) m2_unpack_s = {1'b0, m2_mkv(2'd2, s, 0, 0)};
    else begin
    if (e == 0) begin sig = {{(11-2){1'b0}}, m}; ex = -16; if (m != 0) den = 1'b1; if (daz && m != 0) sig = 0; end
    else begin sig = {{(11-2-1){1'b0}}, 1'b1, m}; ex = e - 17; end
      m2_unpack_s = {den, m2_mkv(2'd0, s, ex, sig)};
    end
  endfunction

  // X -> fp8e5m2 (fp8e5m2): sign(1) exp 5 man 2, top field 30, max finite 7'd123
  function automatic [10+8-1:0] m2_pack_fp8e5m2(input [45:0] x0, input [2:0] rnd, input [7:0] word, input ftz);
    logic [45:0] x; logic [1:0] sp; logic s; logic signed [15:0] e, eu, biased; logic [25:0] sig;
    logic st, inexact, up, upn, half_eq, gt_half, tiny, ovf, unf, carry_n, to_inf; integer sh, shn, sht;
    logic [26:0] keep, rest, keepn, restn, halfv, halfn; logic [26+8:0] fint, fintn; logic [10-1:0] fl;
    logic [8+16:0] code; logic [8:0] mag; logic [8-1:0] outb;
    x = m2_norm(x0); sp = x[45:45-1]; s = x[45-2] & 1; sig = x[26:1]; st = x[0]; e = x[26+16:26+1];
    fl = 0; outb = 0;
    if (sp == 2'd1) begin fl[5] = 1'b1; outb = 8'd126; end
    else if (sp == 2'd2) begin
      outb = {s, 7'd124}; if (!1) begin fl[4] = 1'b1; fl[2] = 1'b1; end
    end else if (sig == 0 && !st) begin outb = 1 ? 0 : {s, {7{1'b0}}}; end
    else begin
      if (sig == 0) begin sig = 1 << 25; e = e - (2*26-1); end // normalize the lone sticky's tiny value
      eu = e + 25;                 // exponent of the leading one
      biased = eu + 15;
      shn = 26 - 1 - 2;           // bits dropped at the normal precision
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
      up = m2_rup(rnd, s, inexact, rest, halfv, st, keep[0], fint, word);
      upn = m2_rup(rnd, s, (restn != 0) | st, restn, halfn, st, keepn[0], fintn, word);
      carry_n = ((keepn + upn) == ({{26{1'b0}}, 1'b1} << (2 + 1)));
      mag = keep + up;
      if (biased < 1) biased = 0;
      code = (biased < 1) ? mag : ((biased << 2) + mag - ({{(8+16){1'b0}}, 1'b1} << 2));
      tiny = 0 ? (eu < -14) : ((eu < -14) && !(eu == -14 - 1 && carry_n) && !(eu + 15 == 0 && carry_n));
      ovf = (code > 7'd123);
      if (ovf) begin
        to_inf = 1 && (rnd == 3'd0 || (rnd == 3'd3 && !s) || (rnd == 3'd2 && s) || rnd == 3'd5 || (rnd == 3'd4 && (eu > 15 || up)));
        outb = to_inf ? {s, 7'd124} : {s, 7'd123};
        fl[2] = 1'b1; fl[4] = 1'b1;
      end else begin
        outb = {s, code[6:0]};
        if (inexact) fl[4] = 1'b1;
        if (tiny && inexact) fl[3] = 1'b1;
        if (ftz && code[7-1:2] == 0 && code[1:0] != 0) begin
          outb = {s, {7{1'b0}}}; fl[4] = 1'b1; fl[3] = 1'b1;
        end

      end
    end
    m2_pack_fp8e5m2 = {fl, outb};
  endfunction
endpackage

// alu_core_m3_pkg: the exact-arithmetic functions of mode 3 (1xfp8e4m3)
package alu_core_m3_pkg;

  // ---- m3: V = {special[1:0], sign, exp[16] (signed), sig[11]}
  //           X = {special[1:0], sign, exp[16] (signed), sig[26], sticky}
  localparam int m3_SW = 11, m3_EW = 16, m3_XW = 26;
  localparam int m3_VW = 30, m3_XT = 46;
  function automatic [29:0] m3_mkv(input [1:0] sp, input s, input signed [15:0] e, input [10:0] sig);
    m3_mkv = {sp, s, e, sig};
  endfunction
  function automatic [45:0] m3_mkx(input [1:0] sp, input s, input signed [15:0] e, input [25:0] sig, input st);
    m3_mkx = {sp, s, e, sig, st};
  endfunction
  function automatic [45:0] m3_x(input [29:0] v);   // widen V to X
    m3_x = {v[29:29-1], v[29-2], v[29-3 -: 16], {{(26-11){1'b0}}, v[10:0]}, 1'b0};
  endfunction
  // normalize: leading one at bit XW-1 (zero stays zero)
  function automatic [45:0] m3_norm(input [45:0] x);
    logic [25:0] s; logic signed [15:0] e; integer k;
    s = x[26:1]; e = x[26+16:26+1];
    if (s != 0) begin
      for (k = 16; k >= 1; k = k / 2) begin
        if (k < 26) begin
          if (s[25 -: 1] == 1'b0 && (s >> (26 - k)) == 0) begin
            s = s << k; e = e - k;
          end
        end
      end
    end
    m3_norm = {x[45:45-1], x[45-2], e, s, x[0]};
  endfunction

  function automatic m3_rup(input [2:0] rnd, input s, input inexact, input [26:0] rest, input [26:0] halfv,
                             input st, input lsb, input [26+8:0] fint, input [7:0] word);
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
  function automatic [45:0] m3_add(input [45:0] a, input [45:0] b, input sub);
    logic [45:0] na, nb, big, sml; logic [1:0] spa, spb; logic sa, sb, sr, sw;
    logic signed [15:0] ea, eb, d; logic [26:0] ms, mb, r; logic st, stb; integer sh;
    na = m3_norm(a); nb = m3_norm(b);
    spa = na[45:45-1]; spb = nb[45:45-1];
    sa = na[45-2]; sb = nb[45-2] ^ sub;
    if (spa == 2'd1 || spb == 2'd1) m3_add = m3_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 && spb == 2'd2) m3_add = (sa == sb) ? m3_mkx(2'd2, sa, 0, 0, 1'b0) : m3_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m3_add = m3_mkx(2'd2, sa, 0, 0, 1'b0);
    else if (spb == 2'd2) m3_add = m3_mkx(2'd2, sb, 0, 0, 1'b0);
    else if (na[26:1] == 0 && !na[0]) m3_add = {nb[45:45-1], sb, nb[45-3:0]};
    else if (nb[26:1] == 0 && !nb[0]) m3_add = na;
    else begin
      ea = na[26+16:26+1]; eb = nb[26+16:26+1];
      // order by magnitude (both normalized): larger exponent, then sig
      if (ea > eb || (ea == eb && na[26:1] >= nb[26:1])) begin big = na; sml = nb; sw = 1'b0; end
      else begin big = nb; sml = na; sw = 1'b1; end
      d = big[26+16:26+1] - sml[26+16:26+1];
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
      if (r[26]) begin st = st | r[0]; r = r >> 1; m3_add = m3_mkx(2'd0, sr, big[26+16:26+1] + 1, r[25:0], st); end
      else m3_add = m3_mkx(2'd0, sr, big[26+16:26+1], r[25:0], st);
    end
  endfunction
  function automatic [45:0] m3_mul(input [45:0] a, input [45:0] b);
    logic [45:0] na, nb; logic [1:0] spa, spb; logic s; logic [2*26-1:0] pr; logic st; integer k;
    na = m3_norm(a); nb = m3_norm(b);
    spa = na[45:45-1]; spb = nb[45:45-1]; s = na[45-2] ^ nb[45-2];
    if (spa == 2'd1 || spb == 2'd1) m3_mul = m3_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 || spb == 2'd2) begin
      if ((spa == 2'd0 && na[26:1] == 0 && !na[0]) || (spb == 2'd0 && nb[26:1] == 0 && !nb[0]))
        m3_mul = m3_mkx(2'd1, 1'b0, 0, 0, 1'b0);
      else m3_mul = m3_mkx(2'd2, s, 0, 0, 1'b0);
    end else begin
      pr = na[26:1] * nb[26:1];
      st = na[0] | nb[0];
      // keep the top XW bits of the product, the rest folds into sticky
      st = st | (pr[25:0] != 0);
      m3_mul = m3_mkx(2'd0, s, na[26+16:26+1] + nb[26+16:26+1] + 26, pr[2*26-1:26], st);
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
  function automatic [2*26+1:0] m3_udiv(input [25:0] a, input [25:0] dv);
    logic [26+1:0] r; logic [26:0] q; logic ge; integer i;
    r = {2'b0, a}; q = 0;
    for (i = 26; i >= 0; i = i - 1) begin
      ge = (r >= {2'b0, dv});
      r = ge ? r - {2'b0, dv} : r;
      q = {q[25:0], ge};
      if (i > 0) r = {r[26:0], 1'b0};
    end
    m3_udiv = {q, r[26:0]};
  endfunction
  // the exact product: {special[1:0], sign, exp[EW], sig[2XW]} (no sticky)
  function automatic [2*26+16+2:0] m3_mulx(input [45:0] a, input [45:0] b);
    logic [45:0] na, nb; logic [1:0] spa, spb, sp; logic s; logic [2*26-1:0] pr;
    na = m3_norm(a); nb = m3_norm(b);
    pr = na[26:1] * nb[26:1];
    spa = na[45:45-1]; spb = nb[45:45-1]; s = na[45-2] ^ nb[45-2];
    if (spa == 2'd1 || spb == 2'd1) sp = 2'd1;
    else if (spa == 2'd2 || spb == 2'd2)
      sp = ((spa == 2'd0 && na[26:1] == 0) || (spb == 2'd0 && nb[26:1] == 0)) ? 2'd1 : 2'd2;
    else sp = 2'd0;
    m3_mulx = {sp, s, na[26+16:26+1] + nb[26+16:26+1], pr};
  endfunction
  function automatic [45:0] m3_div(input [45:0] a, input [45:0] b);
    logic [45:0] na, nb; logic [1:0] spa, spb; logic s; logic [2*26+1:0] qr; logic [26:0] q, r;
    na = m3_norm(a); nb = m3_norm(b);
    spa = na[45:45-1]; spb = nb[45:45-1]; s = na[45-2] ^ nb[45-2];
    if (spa == 2'd1 || spb == 2'd1) m3_div = m3_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 && spb == 2'd2) m3_div = m3_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m3_div = m3_mkx(2'd2, s, 0, 0, 1'b0);
    else if (spb == 2'd2) m3_div = m3_mkx(2'd0, s, 0, 0, 1'b0);
    else if (nb[26:1] == 0 && !nb[0]) begin
      if (na[26:1] == 0 && !na[0]) m3_div = m3_mkx(2'd1, 1'b0, 0, 0, 1'b0);
      else m3_div = m3_mkx(2'd2, s, 0, 0, 1'b0);
    end else if (na[26:1] == 0 && !na[0]) m3_div = m3_mkx(2'd0, s, 0, 0, 1'b0);
    else begin
      qr = m3_udiv(na[26:1], nb[26:1]);     // both normalized: nonzero finite
      q = qr[2*26+1:26+1]; r = qr[26:0];
      // q < 2^(XW+1): drop one bit when it carries
      if (q[26]) m3_div = m3_mkx(2'd0, s, na[26+16:26+1] - nb[26+16:26+1] - 26 + 1, q[26:1], (r != 0) | q[0] | na[0] | nb[0]);
      else m3_div = m3_mkx(2'd0, s, na[26+16:26+1] - nb[26+16:26+1] - 26, q[25:0], (r != 0) | na[0] | nb[0]);
    end
  endfunction
  function automatic [45:0] m3_sqrt(input [45:0] a);
    logic [45:0] na; logic [1:0] spa; logic signed [15:0] e; logic [26:0] m; logic [2*26+3:0] rad;
    logic [26+2:0] rem, trial; logic [26:0] root; logic ge; integer i;
    na = m3_norm(a); spa = na[45:45-1];
    if (spa == 2'd1) m3_sqrt = m3_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m3_sqrt = na[45-2] ? m3_mkx(2'd1, 1'b0, 0, 0, 1'b0) : na;
    else if (na[26:1] == 0 && !na[0]) m3_sqrt = na;
    else if (na[45-2]) m3_sqrt = m3_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else begin
      e = na[26+16:26+1];
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
      m3_sqrt = m3_mkx(2'd0, 1'b0, (e >>> 1) - 13 + 1, root[26:1], (rem != 0) | root[0] | na[0]);
    end
  endfunction
  // X ordering treats NaN as unordered and compares finite values by sign and magnitude
  function automatic m3_lt(input [45:0] a, input [45:0] b);
    logic [45:0] na, nb; logic za, zb, sa, sb, mag_lt; logic signed [15:0] ea, eb;
    na = m3_norm(a); nb = m3_norm(b);
    za = (na[26:1] == 0) && !na[0]; zb = (nb[26:1] == 0) && !nb[0];
    sa = na[45-2] && !za; sb = nb[45-2] && !zb;
    if (na[45:45-1] == 2'd1 || nb[45:45-1] == 2'd1) m3_lt = 1'b0;
    else if (na[45:45-1] == 2'd2 || nb[45:45-1] == 2'd2) begin
      if (na[45:45-1] == 2'd2 && nb[45:45-1] == 2'd2) m3_lt = na[45-2] && !nb[45-2];
      else if (na[45:45-1] == 2'd2) m3_lt = na[45-2];
      else m3_lt = !nb[45-2];
    end else if (za && zb) m3_lt = 1'b0;
    else if (sa != sb) m3_lt = sa;
    else begin
      ea = na[26+16:26+1]; eb = nb[26+16:26+1];
      if (za) mag_lt = 1'b1; else if (zb) mag_lt = 1'b0;
      else mag_lt = (ea < eb) || (ea == eb && (na[26:1] < nb[26:1] || (na[26:1] == nb[26:1] && !na[0] && nb[0])));
      m3_lt = sa ? !mag_lt && !(za && zb) && !m3_eq(na, nb) : mag_lt;
    end
  endfunction
  function automatic m3_eq(input [45:0] a, input [45:0] b);
    logic [45:0] na, nb; logic za, zb;
    na = m3_norm(a); nb = m3_norm(b);
    za = (na[26:1] == 0) && !na[0]; zb = (nb[26:1] == 0) && !nb[0];
    if (na[45:45-1] == 2'd1 || nb[45:45-1] == 2'd1) m3_eq = 1'b0;
    else if (na[45:45-1] == 2'd2 || nb[45:45-1] == 2'd2)
      m3_eq = (na[45:45-1] == nb[45:45-1]) && (na[45-2] == nb[45-2]);
    else if (za || zb) m3_eq = za && zb;
    else m3_eq = (na[45-2] == nb[45-2]) && (na[26+16:26+1] == nb[26+16:26+1]) && (na[26:1] == nb[26:1]) && (na[0] == nb[0]);
  endfunction

  // the fused multiply-add (-1)^np * a * b + (-1)^nc * c, rounded once: the
  // exact 2 XW-bit product and c (its significand at the product's scale)
  // meet in a 2 XW + 2-bit frame, the smaller aligned right with a sticky,
  // and the sum or difference normalizes to the X (the top XW bits, the
  // rest sticky). The specials as IEEE 754 orders them: a NaN operand, an
  // invalid product (inf * 0), an infinite product against the opposite
  // infinite addend, an infinite product, an infinite addend. An exact zero
  // leaves with sign 0 (the caller applies the zero-sign rule); the
  // operands' own stickies fold into the result's (the ALU's unpacked
  // operands carry none).
  function automatic [45:0] m3_fma(input [45:0] a, input [45:0] b, input [45:0] c, input np, input nc);
    logic [45:0] na, nb, ncc; logic [1:0] spa, spb, spc; logic sp, sc, sr, sbig, ssml, a_zero, b_zero, c_zero, neg;
    logic signed [15:0] ea, eb, ec, ep, ecw, ebase; logic signed [16+1:0] d;
    logic [2*26-1:0] pr; logic [2*26+1:0] mp, mc, big, sml, r; logic stp, stc, stb, sts, st; integer sh, k;
    na = m3_norm(a); nb = m3_norm(b); ncc = m3_norm(c);
    spa = na[45:45-1]; spb = nb[45:45-1]; spc = ncc[45:45-1];
    sp = na[45-2] ^ nb[45-2] ^ np; sc = ncc[45-2] ^ nc;
    a_zero = (spa == 2'd0) && na[26:1] == 0 && !na[0]; b_zero = (spb == 2'd0) && nb[26:1] == 0 && !nb[0];
    c_zero = (spc == 2'd0) && ncc[26:1] == 0 && !ncc[0];
    if (spa == 2'd1 || spb == 2'd1 || spc == 2'd1) m3_fma = m3_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if ((spa == 2'd2 && b_zero) || (spb == 2'd2 && a_zero)) m3_fma = m3_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if ((spa == 2'd2 || spb == 2'd2) && spc == 2'd2 && sp != sc) m3_fma = m3_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 || spb == 2'd2) m3_fma = m3_mkx(2'd2, sp, 0, 0, 1'b0);
    else if (spc == 2'd2) m3_fma = m3_mkx(2'd2, sc, 0, 0, 1'b0);
    // an exact zero product (a zero operand's exponent means nothing): the addend, with its negation
    else if (a_zero || b_zero) m3_fma = c_zero ? m3_mkx(2'd0, 1'b0, 0, 0, 1'b0) : {ncc[45:45-1], sc, ncc[45-3:0]};
    else begin
      ea = na[26+16:26+1]; eb = nb[26+16:26+1]; ec = ncc[26+16:26+1];
      pr = na[26:1] * nb[26:1]; mp = {2'b00, pr}; stp = na[0] | nb[0]; ep = ea + eb;
      mc = {2'b00, ncc[26:1], {26{1'b0}}}; stc = ncc[0]; ecw = ec - 26;
      d = $signed({{2{ep[15]}}, ep}) - $signed({{2{ecw[15]}}, ecw});
      // a zero addend (its exponent means nothing): the product stays in place
      if (c_zero) begin big = mp; sml = 0; sbig = sp; ssml = sp; stb = stp; sts = 1'b0; ebase = ep; d = 0; end
      else if (d >= 0) begin big = mp; sml = mc; sbig = sp; ssml = sc; stb = stp; sts = stc; ebase = ep; end
      else begin big = mc; sml = mp; sbig = sc; ssml = sp; stb = stc; sts = stp; ebase = ecw; d = -d; end
      if (d > 2*26 + 2) begin sts = sts | (sml != 0); sml = 0; end
      else begin
        for (sh = 0; sh < 2*26 + 3; sh = sh + 1) begin
          if (sh < d) begin sts = sts | sml[0]; sml = sml >> 1; end
        end
      end
      st = stb | sts;
      if (sbig == ssml) begin r = big + sml; sr = sbig; end
      else begin
        // the difference: the aligned smaller value's sticky borrows one lsb; the sign follows the larger magnitude
        neg = (big < sml) || (big == sml && sts);
        if (neg) begin r = sml - big; sr = ssml; end
        else begin r = big - sml - (sts ? 1'b1 : 1'b0); sr = sbig; end
      end
      if (r == 0) m3_fma = m3_mkx(2'd0, st ? sr : 1'b0, ebase, 0, st);
      else begin
        sh = 0;
        for (k = 0; k < 2*26 + 2; k = k + 1) begin
          if (!r[2*26+1]) begin r = r << 1; sh = sh + 1; end
        end
        st = st | (r[26+1:0] != 0);
        m3_fma = m3_mkx(2'd0, sr, ebase + 26 + 2 - sh, r[2*26+1:26+2], st);
      end
    end
  endfunction

  // fp8e4m3 pattern -> V (bit VW = denormal-read flag returned beside)
  function automatic [30:0] m3_unpack_s(input [7:0] b, input daz);
    logic [3:0] e; logic [2:0] m; logic [10:0] sig; logic signed [15:0] ex; logic den, s;
    e = b[6:3]; m = b[2:0]; s = b[7]; den = 1'b0; sig = 0; ex = 0;
    if ((e == 4'd15 && m == {3{1'b1}})) m3_unpack_s = {1'b0, m3_mkv(2'd1, 1'b0, 0, 0)};
    else if (1'b0) m3_unpack_s = {1'b0, m3_mkv(2'd2, s, 0, 0)};
    else begin
    if (e == 0) begin sig = {{(11-3){1'b0}}, m}; ex = -9; if (m != 0) den = 1'b1; if (daz && m != 0) sig = 0; end
    else begin sig = {{(11-3-1){1'b0}}, 1'b1, m}; ex = e - 10; end
      m3_unpack_s = {den, m3_mkv(2'd0, s, ex, sig)};
    end
  endfunction

  // X -> fp8e4m3 (fp8e4m3): sign(1) exp 4 man 3, top field 15, max finite 7'd126
  function automatic [10+8-1:0] m3_pack_fp8e4m3(input [45:0] x0, input [2:0] rnd, input [7:0] word, input ftz);
    logic [45:0] x; logic [1:0] sp; logic s; logic signed [15:0] e, eu, biased; logic [25:0] sig;
    logic st, inexact, up, upn, half_eq, gt_half, tiny, ovf, unf, carry_n, to_inf; integer sh, shn, sht;
    logic [26:0] keep, rest, keepn, restn, halfv, halfn; logic [26+8:0] fint, fintn; logic [10-1:0] fl;
    logic [8+16:0] code; logic [8:0] mag; logic [8-1:0] outb;
    x = m3_norm(x0); sp = x[45:45-1]; s = x[45-2] & 1; sig = x[26:1]; st = x[0]; e = x[26+16:26+1];
    fl = 0; outb = 0;
    if (sp == 2'd1) begin fl[5] = 1'b1; outb = 8'd127; end
    else if (sp == 2'd2) begin
      outb = {s, 7'd126}; if (!0) begin fl[4] = 1'b1; fl[2] = 1'b1; end
    end else if (sig == 0 && !st) begin outb = 1 ? 0 : {s, {7{1'b0}}}; end
    else begin
      if (sig == 0) begin sig = 1 << 25; e = e - (2*26-1); end // normalize the lone sticky's tiny value
      eu = e + 25;                 // exponent of the leading one
      biased = eu + 7;
      shn = 26 - 1 - 3;           // bits dropped at the normal precision
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
      up = m3_rup(rnd, s, inexact, rest, halfv, st, keep[0], fint, word);
      upn = m3_rup(rnd, s, (restn != 0) | st, restn, halfn, st, keepn[0], fintn, word);
      carry_n = ((keepn + upn) == ({{26{1'b0}}, 1'b1} << (3 + 1)));
      mag = keep + up;
      if (biased < 1) biased = 0;
      code = (biased < 1) ? mag : ((biased << 3) + mag - ({{(8+16){1'b0}}, 1'b1} << 3));
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
    m3_pack_fp8e4m3 = {fl, outb};
  endfunction
endpackage
// ADIR-MEMBER top
// EVOLVE-BLOCK-START
// ADIR-DECL v1
// STRUCTURE m0.l0.fp_adder kind=fp_adder slot=fp_adder mode=0 lane=0 width=16 format=fp16 ops=fadd,fsub,fmadd,fmsub,fnmsub,fnmadd sv=alu_core_u_m0_l0_fp_fma group=m0.l0.fp_fma
// STRUCTURE m0.l0.unpacker kind=unpacker slot=unpacker mode=0 lane=0 width=16 format=fp16 ops=fadd,fsub,fmul,fmadd,fmsub,fnmsub,fnmadd,fmin,fmax,fcmp sv=alu_core_u_m0_l0_unpacker
// STRUCTURE m0.l0.rounder kind=rounder slot=rounder mode=0 lane=0 width=16 format=fp16 ops=fadd,fsub,fmul,fmadd,fmsub,fnmsub,fnmadd sv=alu_core_u_m0_l0_rounder
// STRUCTURE m0.l0.fp_fma kind=fp_fma slot=fp_fma mode=0 lane=0 width=16 format=fp16 ops=fadd,fsub,fmul,fmadd,fmsub,fnmsub,fnmadd sv=alu_core_u_m0_l0_fp_fma group=m0.l0.fp_fma
// STRUCTURE m0.l0.fp_multiplier kind=fp_multiplier slot=fp_multiplier mode=0 lane=0 width=16 format=fp16 ops=fmul,fmadd,fmsub,fnmsub,fnmadd sv=alu_core_u_m0_l0_fp_fma group=m0.l0.fp_fma
// STRUCTURE m0.l0.fp_comparator kind=fp_comparator slot=fp_comparator mode=0 lane=0 width=16 format=fp16 ops=fmin,fmax,fcmp sv=alu_core_u_m0_l0_fp_comparator
// STRUCTURE m1.l0.fp_adder kind=fp_adder slot=fp_adder mode=1 lane=0 width=16 format=bf16 ops=fadd,fsub,fmadd,fmsub,fnmsub,fnmadd sv=alu_core_u_m1_l0_fp_fma group=m1.l0.fp_fma
// STRUCTURE m1.l0.unpacker kind=unpacker slot=unpacker mode=1 lane=0 width=16 format=bf16 ops=fadd,fsub,fmul,fmadd,fmsub,fnmsub,fnmadd,fmin,fmax,fcmp sv=alu_core_u_m1_l0_unpacker
// STRUCTURE m1.l0.rounder kind=rounder slot=rounder mode=1 lane=0 width=16 format=bf16 ops=fadd,fsub,fmul,fmadd,fmsub,fnmsub,fnmadd sv=alu_core_u_m1_l0_rounder
// STRUCTURE m1.l0.fp_fma kind=fp_fma slot=fp_fma mode=1 lane=0 width=16 format=bf16 ops=fadd,fsub,fmul,fmadd,fmsub,fnmsub,fnmadd sv=alu_core_u_m1_l0_fp_fma group=m1.l0.fp_fma
// STRUCTURE m1.l0.fp_multiplier kind=fp_multiplier slot=fp_multiplier mode=1 lane=0 width=16 format=bf16 ops=fmul,fmadd,fmsub,fnmsub,fnmadd sv=alu_core_u_m1_l0_fp_fma group=m1.l0.fp_fma
// STRUCTURE m1.l0.fp_comparator kind=fp_comparator slot=fp_comparator mode=1 lane=0 width=16 format=bf16 ops=fmin,fmax,fcmp sv=alu_core_u_m1_l0_fp_comparator
// STRUCTURE m2.l0.fp_adder kind=fp_adder slot=fp_adder mode=2 lane=0 width=8 format=fp8e5m2 ops=fadd,fsub,fmadd,fmsub,fnmsub,fnmadd sv=alu_core_u_m2_l0_fp_fma group=m2.l0.fp_fma
// STRUCTURE m2.l0.unpacker kind=unpacker slot=unpacker mode=2 lane=0 width=8 format=fp8e5m2 ops=fadd,fsub,fmul,fmadd,fmsub,fnmsub,fnmadd,fmin,fmax,fcmp sv=alu_core_u_m2_l0_unpacker
// STRUCTURE m2.l0.rounder kind=rounder slot=rounder mode=2 lane=0 width=8 format=fp8e5m2 ops=fadd,fsub,fmul,fmadd,fmsub,fnmsub,fnmadd sv=alu_core_u_m2_l0_rounder
// STRUCTURE m2.l0.fp_fma kind=fp_fma slot=fp_fma mode=2 lane=0 width=8 format=fp8e5m2 ops=fadd,fsub,fmul,fmadd,fmsub,fnmsub,fnmadd sv=alu_core_u_m2_l0_fp_fma group=m2.l0.fp_fma
// STRUCTURE m2.l0.fp_multiplier kind=fp_multiplier slot=fp_multiplier mode=2 lane=0 width=8 format=fp8e5m2 ops=fmul,fmadd,fmsub,fnmsub,fnmadd sv=alu_core_u_m2_l0_fp_fma group=m2.l0.fp_fma
// STRUCTURE m2.l0.fp_comparator kind=fp_comparator slot=fp_comparator mode=2 lane=0 width=8 format=fp8e5m2 ops=fmin,fmax,fcmp sv=alu_core_u_m2_l0_fp_comparator
// STRUCTURE m3.l0.fp_adder kind=fp_adder slot=fp_adder mode=3 lane=0 width=8 format=fp8e4m3 ops=fadd,fsub,fmadd,fmsub,fnmsub,fnmadd sv=alu_core_u_m3_l0_fp_fma group=m3.l0.fp_fma
// STRUCTURE m3.l0.unpacker kind=unpacker slot=unpacker mode=3 lane=0 width=8 format=fp8e4m3 ops=fadd,fsub,fmul,fmadd,fmsub,fnmsub,fnmadd,fmin,fmax,fcmp sv=alu_core_u_m3_l0_unpacker
// STRUCTURE m3.l0.rounder kind=rounder slot=rounder mode=3 lane=0 width=8 format=fp8e4m3 ops=fadd,fsub,fmul,fmadd,fmsub,fnmsub,fnmadd sv=alu_core_u_m3_l0_rounder
// STRUCTURE m3.l0.fp_fma kind=fp_fma slot=fp_fma mode=3 lane=0 width=8 format=fp8e4m3 ops=fadd,fsub,fmul,fmadd,fmsub,fnmsub,fnmadd sv=alu_core_u_m3_l0_fp_fma group=m3.l0.fp_fma
// STRUCTURE m3.l0.fp_multiplier kind=fp_multiplier slot=fp_multiplier mode=3 lane=0 width=8 format=fp8e4m3 ops=fmul,fmadd,fmsub,fnmsub,fnmadd sv=alu_core_u_m3_l0_fp_fma group=m3.l0.fp_fma
// STRUCTURE m3.l0.fp_comparator kind=fp_comparator slot=fp_comparator mode=3 lane=0 width=8 format=fp8e4m3 ops=fmin,fmax,fcmp sv=alu_core_u_m3_l0_fp_comparator
// ADIR-END
module alu_core (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [15:0] c,
  input  logic [3:0] op,
  input  logic [1:0] mode,
  input  logic [1:0] rounding_sel,
  output logic [15:0] y,
  output logic [3:0] flags
);
  // alu_core: behavioral reference derived from the instance (modes 1xfp16, 1xbf16, 1xfp8e5m2, 1xfp8e4m3; ops fadd, fsub, fmul, fmadd, fmsub, fnmsub, fnmadd, fmin, fmax, fcmp). Every (mode, op) pair computes the verify layer's exact semantics.
  // HIERARCHY: 16 physical structure modules instantiated by alu_core, built from 16 lane modules (one per mode and kind, parameter LANE) and 4 packages of engine functions (one per mode); a float mode's datapath is split into an unpacker (the xa/xb/den buses), the arithmetic and converter structures (unrounded results on the x bus) and a rounder (y and the flags); 0 misc lane modules and 0 block-conversion group modules
  // UNIT m0.l0.unpacker module=alu_core_u_m0_l0_unpacker kind=unpacker members=m0.l0.unpacker
  // UNIT m0.l0.rounder module=alu_core_u_m0_l0_rounder kind=rounder members=m0.l0.rounder
  // UNIT m0.l0.fp_fma module=alu_core_u_m0_l0_fp_fma kind=fp_fma members=m0.l0.fp_fma,m0.l0.fp_multiplier,m0.l0.fp_adder
  // UNIT m0.l0.fp_comparator module=alu_core_u_m0_l0_fp_comparator kind=fp_comparator members=m0.l0.fp_comparator
  // UNIT m1.l0.unpacker module=alu_core_u_m1_l0_unpacker kind=unpacker members=m1.l0.unpacker
  // UNIT m1.l0.rounder module=alu_core_u_m1_l0_rounder kind=rounder members=m1.l0.rounder
  // UNIT m1.l0.fp_fma module=alu_core_u_m1_l0_fp_fma kind=fp_fma members=m1.l0.fp_fma,m1.l0.fp_multiplier,m1.l0.fp_adder
  // UNIT m1.l0.fp_comparator module=alu_core_u_m1_l0_fp_comparator kind=fp_comparator members=m1.l0.fp_comparator
  // UNIT m2.l0.unpacker module=alu_core_u_m2_l0_unpacker kind=unpacker members=m2.l0.unpacker
  // UNIT m2.l0.rounder module=alu_core_u_m2_l0_rounder kind=rounder members=m2.l0.rounder
  // UNIT m2.l0.fp_fma module=alu_core_u_m2_l0_fp_fma kind=fp_fma members=m2.l0.fp_fma,m2.l0.fp_multiplier,m2.l0.fp_adder
  // UNIT m2.l0.fp_comparator module=alu_core_u_m2_l0_fp_comparator kind=fp_comparator members=m2.l0.fp_comparator
  // UNIT m3.l0.unpacker module=alu_core_u_m3_l0_unpacker kind=unpacker members=m3.l0.unpacker
  // UNIT m3.l0.rounder module=alu_core_u_m3_l0_rounder kind=rounder members=m3.l0.rounder
  // UNIT m3.l0.fp_fma module=alu_core_u_m3_l0_fp_fma kind=fp_fma members=m3.l0.fp_fma,m3.l0.fp_multiplier,m3.l0.fp_adder
  // UNIT m3.l0.fp_comparator module=alu_core_u_m3_l0_fp_comparator kind=fp_comparator members=m3.l0.fp_comparator
  // // STRUCTURE m0.l0.fp_adder kind=fp_adder slot=fp_adder mode=0 lane=0 width=16 format=fp16 ops=fadd,fsub,fmadd,fmsub,fnmsub,fnmadd sv=alu_core_u_m0_l0_fp_fma
  // // STRUCTURE m0.l0.unpacker kind=unpacker slot=unpacker mode=0 lane=0 width=16 format=fp16 ops=fadd,fsub,fmul,fmadd,fmsub,fnmsub,fnmadd,fmin,fmax,fcmp sv=alu_core_u_m0_l0_unpacker
  // // STRUCTURE m0.l0.rounder kind=rounder slot=rounder mode=0 lane=0 width=16 format=fp16 ops=fadd,fsub,fmul,fmadd,fmsub,fnmsub,fnmadd sv=alu_core_u_m0_l0_rounder
  // // STRUCTURE m0.l0.fp_fma kind=fp_fma slot=fp_fma mode=0 lane=0 width=16 format=fp16 ops=fadd,fsub,fmul,fmadd,fmsub,fnmsub,fnmadd sv=alu_core_u_m0_l0_fp_fma
  // // STRUCTURE m0.l0.fp_multiplier kind=fp_multiplier slot=fp_multiplier mode=0 lane=0 width=16 format=fp16 ops=fmul,fmadd,fmsub,fnmsub,fnmadd sv=alu_core_u_m0_l0_fp_fma
  // // STRUCTURE m0.l0.fp_comparator kind=fp_comparator slot=fp_comparator mode=0 lane=0 width=16 format=fp16 ops=fmin,fmax,fcmp sv=alu_core_u_m0_l0_fp_comparator
  // // STRUCTURE m1.l0.fp_adder kind=fp_adder slot=fp_adder mode=1 lane=0 width=16 format=bf16 ops=fadd,fsub,fmadd,fmsub,fnmsub,fnmadd sv=alu_core_u_m1_l0_fp_fma
  // // STRUCTURE m1.l0.unpacker kind=unpacker slot=unpacker mode=1 lane=0 width=16 format=bf16 ops=fadd,fsub,fmul,fmadd,fmsub,fnmsub,fnmadd,fmin,fmax,fcmp sv=alu_core_u_m1_l0_unpacker
  // // STRUCTURE m1.l0.rounder kind=rounder slot=rounder mode=1 lane=0 width=16 format=bf16 ops=fadd,fsub,fmul,fmadd,fmsub,fnmsub,fnmadd sv=alu_core_u_m1_l0_rounder
  // // STRUCTURE m1.l0.fp_fma kind=fp_fma slot=fp_fma mode=1 lane=0 width=16 format=bf16 ops=fadd,fsub,fmul,fmadd,fmsub,fnmsub,fnmadd sv=alu_core_u_m1_l0_fp_fma
  // // STRUCTURE m1.l0.fp_multiplier kind=fp_multiplier slot=fp_multiplier mode=1 lane=0 width=16 format=bf16 ops=fmul,fmadd,fmsub,fnmsub,fnmadd sv=alu_core_u_m1_l0_fp_fma
  // // STRUCTURE m1.l0.fp_comparator kind=fp_comparator slot=fp_comparator mode=1 lane=0 width=16 format=bf16 ops=fmin,fmax,fcmp sv=alu_core_u_m1_l0_fp_comparator
  // // STRUCTURE m2.l0.fp_adder kind=fp_adder slot=fp_adder mode=2 lane=0 width=8 format=fp8e5m2 ops=fadd,fsub,fmadd,fmsub,fnmsub,fnmadd sv=alu_core_u_m2_l0_fp_fma
  // // STRUCTURE m2.l0.unpacker kind=unpacker slot=unpacker mode=2 lane=0 width=8 format=fp8e5m2 ops=fadd,fsub,fmul,fmadd,fmsub,fnmsub,fnmadd,fmin,fmax,fcmp sv=alu_core_u_m2_l0_unpacker
  // // STRUCTURE m2.l0.rounder kind=rounder slot=rounder mode=2 lane=0 width=8 format=fp8e5m2 ops=fadd,fsub,fmul,fmadd,fmsub,fnmsub,fnmadd sv=alu_core_u_m2_l0_rounder
  // // STRUCTURE m2.l0.fp_fma kind=fp_fma slot=fp_fma mode=2 lane=0 width=8 format=fp8e5m2 ops=fadd,fsub,fmul,fmadd,fmsub,fnmsub,fnmadd sv=alu_core_u_m2_l0_fp_fma
  // // STRUCTURE m2.l0.fp_multiplier kind=fp_multiplier slot=fp_multiplier mode=2 lane=0 width=8 format=fp8e5m2 ops=fmul,fmadd,fmsub,fnmsub,fnmadd sv=alu_core_u_m2_l0_fp_fma
  // // STRUCTURE m2.l0.fp_comparator kind=fp_comparator slot=fp_comparator mode=2 lane=0 width=8 format=fp8e5m2 ops=fmin,fmax,fcmp sv=alu_core_u_m2_l0_fp_comparator
  // // STRUCTURE m3.l0.fp_adder kind=fp_adder slot=fp_adder mode=3 lane=0 width=8 format=fp8e4m3 ops=fadd,fsub,fmadd,fmsub,fnmsub,fnmadd sv=alu_core_u_m3_l0_fp_fma
  // // STRUCTURE m3.l0.unpacker kind=unpacker slot=unpacker mode=3 lane=0 width=8 format=fp8e4m3 ops=fadd,fsub,fmul,fmadd,fmsub,fnmsub,fnmadd,fmin,fmax,fcmp sv=alu_core_u_m3_l0_unpacker
  // // STRUCTURE m3.l0.rounder kind=rounder slot=rounder mode=3 lane=0 width=8 format=fp8e4m3 ops=fadd,fsub,fmul,fmadd,fmsub,fnmsub,fnmadd sv=alu_core_u_m3_l0_rounder
  // // STRUCTURE m3.l0.fp_fma kind=fp_fma slot=fp_fma mode=3 lane=0 width=8 format=fp8e4m3 ops=fadd,fsub,fmul,fmadd,fmsub,fnmsub,fnmadd sv=alu_core_u_m3_l0_fp_fma
  // // STRUCTURE m3.l0.fp_multiplier kind=fp_multiplier slot=fp_multiplier mode=3 lane=0 width=8 format=fp8e4m3 ops=fmul,fmadd,fmsub,fnmsub,fnmadd sv=alu_core_u_m3_l0_fp_fma
  // // STRUCTURE m3.l0.fp_comparator kind=fp_comparator slot=fp_comparator mode=3 lane=0 width=8 format=fp8e4m3 ops=fmin,fmax,fcmp sv=alu_core_u_m3_l0_fp_comparator
  // LIBRARY: fam_adder_ripple_carry, fam_adder_ripple_chunk, fam_cmp_prefix_comparator, fam_count_lzd_pair_cell_binary_count_vflat_w11, fam_count_lzd_pair_cell_binary_count_vflat_w43, fam_count_lzd_pair_cell_binary_count_vflat_w44, fam_count_lzd_pair_cell_binary_count_vflat_w48, fam_dot_lza_w43_p47261b205eb3, fam_fp_cmp_integer_compare_on_bits_x26e16s11_pa61fc99a71d5, fam_fp_fma_classic_fma_x26e16s11_p0de96c130150, fam_fp_fma_core_classic_fma_x26e16s11_p82fa36d18aa0, fam_fp_fma_core_multipath_fma_x26e16s11_p1221e7100196, fam_fp_fma_core_reduced_latency_fma_x26e16s11_fp8e4m3_pddacaa615be9, fam_fp_fma_multipath_fma_x26e16s11_pcac15181ef26, fam_fp_fma_reduced_latency_fma_x26e16s11_pcb92892f976e, fam_fp_round_dedicated_per_op_increment_adder_bf16_x26e16s11_pd77ccc5b5c45_nin, fam_fp_round_dedicated_per_op_increment_adder_fp16_x26e16s11_pd77ccc5b5c45_nin, fam_fp_round_dedicated_per_op_increment_adder_fp8e4m3_x26e16s11_pd77ccc5b5c45_nin, fam_fp_round_dedicated_per_op_increment_adder_fp8e5m2_x26e16s11_pd77ccc5b5c45_nin, fam_fp_unpack_per_unit_unpack_bf16_x26e16s11_p9bfe39588414, fam_fp_unpack_per_unit_unpack_fp16_x26e16s11_p9bfe39588414, fam_fp_unpack_per_unit_unpack_fp8e4m3_x26e16s11_p9bfe39588414, fam_fp_unpack_per_unit_unpack_fp8e5m2_x26e16s11_p9bfe39588414, fam_incr_prefix_and, fam_prefix_kogge_stone_w4_flag_dual, fam_shift_barrel_mux_tree, fam_shift_keep_mask, fam_shift_stage (chialu.targets.rtl.families: the modules of the declared families the lane modules instantiate; their text follows the generated modules)
  import alu_core_m0_pkg::*;

  function automatic [45:0] alu_core_shared_operand(input [45:0] value);
    logic [45:0] n;
    logic signed [15:0] exponent;
    logic [25:0] significand;
    n = m0_norm(value);
    exponent = $signed(n[42:27]) + 16'sd15;
    significand = n[26:1] >> 15;
    alu_core_shared_operand = {n[45:43], exponent, significand, n[0]};
  endfunction
  logic [2:0] rnd_sel;
  logic [2:0] rnd;
  logic daz;
  logic ftz;
  logic dual;
  logic [45:0] xa_m0_m0_m0_l0_unpacker;
  logic [45:0] xb_m0_m0_m0_l0_unpacker;
  logic [45:0] xc_m0_m0_m0_l0_unpacker;
  logic dena_m0_m0_m0_l0_unpacker;
  logic denb_m0_m0_m0_l0_unpacker;
  logic denc_m0_m0_m0_l0_unpacker;
  logic [15:0] y_m0_m0_l0_rounder;
  logic [9:0] fl_m0_m0_l0_rounder;
  logic [15:0] y_m0_m0_l0_fp_fma;
  logic [9:0] fl_m0_m0_l0_fp_fma;
  logic [45:0] x_m0_m0_m0_l0_fp_fma;
  logic [45:0] ix_fp_fma_a_m0_m0_m0_l0_fp_fma;
  logic [45:0] ix_fp_fma_b_m0_m0_m0_l0_fp_fma;
  logic [45:0] ix_fp_fma_c_m0_m0_m0_l0_fp_fma;
  logic [2:0] ix_fp_fma_op_m0_m0_m0_l0_fp_fma;
  logic [15:0] y_m0_m0_l0_fp_comparator;
  logic [9:0] fl_m0_m0_l0_fp_comparator;
  logic [15:0] y_m0;
  logic [9:0] fl_m0;
  logic [45:0] xa_m0;
  logic [45:0] xb_m0;
  logic [45:0] xc_m0;
  logic dena_m0;
  logic denb_m0;
  logic denc_m0;
  logic [45:0] x_m0;
  logic [45:0] ix_fp_fma_a_m0;
  logic [45:0] ix_fp_fma_b_m0;
  logic [45:0] ix_fp_fma_c_m0;
  logic [2:0] ix_fp_fma_op_m0;
  logic [45:0] xa_m1_m1_m1_l0_unpacker;
  logic [45:0] xb_m1_m1_m1_l0_unpacker;
  logic [45:0] xc_m1_m1_m1_l0_unpacker;
  logic dena_m1_m1_m1_l0_unpacker;
  logic denb_m1_m1_m1_l0_unpacker;
  logic denc_m1_m1_m1_l0_unpacker;
  logic [15:0] y_m1_m1_l0_rounder;
  logic [9:0] fl_m1_m1_l0_rounder;
  logic [15:0] y_m1_m1_l0_fp_fma;
  logic [9:0] fl_m1_m1_l0_fp_fma;
  logic [45:0] x_m1_m1_m1_l0_fp_fma;
  logic [45:0] ix_fp_fma_a_m1_m1_m1_l0_fp_fma;
  logic [45:0] ix_fp_fma_b_m1_m1_m1_l0_fp_fma;
  logic [45:0] ix_fp_fma_c_m1_m1_m1_l0_fp_fma;
  logic [2:0] ix_fp_fma_op_m1_m1_m1_l0_fp_fma;
  logic [15:0] y_m1_m1_l0_fp_comparator;
  logic [9:0] fl_m1_m1_l0_fp_comparator;
  logic [15:0] y_m1;
  logic [9:0] fl_m1;
  logic [45:0] xa_m1;
  logic [45:0] xb_m1;
  logic [45:0] xc_m1;
  logic dena_m1;
  logic denb_m1;
  logic denc_m1;
  logic [45:0] x_m1;
  logic [45:0] ix_fp_fma_a_m1;
  logic [45:0] ix_fp_fma_b_m1;
  logic [45:0] ix_fp_fma_c_m1;
  logic [2:0] ix_fp_fma_op_m1;
  logic [45:0] xa_m2_m2_m2_l0_unpacker;
  logic [45:0] xb_m2_m2_m2_l0_unpacker;
  logic [45:0] xc_m2_m2_m2_l0_unpacker;
  logic dena_m2_m2_m2_l0_unpacker;
  logic denb_m2_m2_m2_l0_unpacker;
  logic denc_m2_m2_m2_l0_unpacker;
  logic [15:0] y_m2_m2_l0_rounder;
  logic [9:0] fl_m2_m2_l0_rounder;
  logic [15:0] y_m2_m2_l0_fp_fma;
  logic [9:0] fl_m2_m2_l0_fp_fma;
  logic [45:0] x_m2_m2_m2_l0_fp_fma;
  logic [15:0] y_m2_m2_l0_fp_comparator;
  logic [9:0] fl_m2_m2_l0_fp_comparator;
  logic [15:0] y_m2;
  logic [9:0] fl_m2;
  logic [45:0] xa_m2;
  logic [45:0] xb_m2;
  logic [45:0] xc_m2;
  logic dena_m2;
  logic denb_m2;
  logic denc_m2;
  logic [45:0] x_m2;
  logic [45:0] xa_m3_m3_m3_l0_unpacker;
  logic [45:0] xb_m3_m3_m3_l0_unpacker;
  logic [45:0] xc_m3_m3_m3_l0_unpacker;
  logic dena_m3_m3_m3_l0_unpacker;
  logic denb_m3_m3_m3_l0_unpacker;
  logic denc_m3_m3_m3_l0_unpacker;
  logic [15:0] y_m3_m3_l0_rounder;
  logic [9:0] fl_m3_m3_l0_rounder;
  logic [15:0] y_m3_m3_l0_fp_fma;
  logic [9:0] fl_m3_m3_l0_fp_fma;
  logic [45:0] x_m3_m3_m3_l0_fp_fma;
  logic [15:0] y_m3_m3_l0_fp_comparator;
  logic [9:0] fl_m3_m3_l0_fp_comparator;
  logic [15:0] y_m3;
  logic [9:0] fl_m3;
  logic [45:0] xa_m3;
  logic [45:0] xb_m3;
  logic [45:0] xc_m3;
  logic dena_m3;
  logic denb_m3;
  logic denc_m3;
  logic [45:0] x_m3;
  logic [45:0] iy_fp_fma_m0;
  logic [45:0] iy_fp_fma_m1;
  logic [45:0] shared_fp_fma_a_l0;
  logic [45:0] shared_fp_fma_b_l0;
  logic [45:0] shared_fp_fma_c_l0;
  logic [2:0] shared_fp_fma_op_l0;
  logic [45:0] shared_fp_fma_y_l0;
  logic [9:0] fl_all;
  always_comb begin
    case (rounding_sel)
      2'd0: rnd_sel = 3'd0;
      2'd1: rnd_sel = 3'd1;
      2'd2: rnd_sel = 3'd2;
      2'd3: rnd_sel = 3'd3;
      default: rnd_sel = 3'd0;
    endcase
  end
  assign rnd = rnd_sel;
  assign daz = 1'b0;
  assign ftz = 1'b0;
  assign dual = 1'b0;
  assign y_m0 = y_m0_m0_l0_rounder | y_m0_m0_l0_fp_fma | y_m0_m0_l0_fp_comparator;
  assign fl_m0 = fl_m0_m0_l0_rounder | fl_m0_m0_l0_fp_fma | fl_m0_m0_l0_fp_comparator;
  assign xa_m0 = xa_m0_m0_m0_l0_unpacker;
  assign xb_m0 = xb_m0_m0_m0_l0_unpacker;
  assign xc_m0 = xc_m0_m0_m0_l0_unpacker;
  assign dena_m0 = dena_m0_m0_m0_l0_unpacker;
  assign denb_m0 = denb_m0_m0_m0_l0_unpacker;
  assign denc_m0 = denc_m0_m0_m0_l0_unpacker;
  assign x_m0 = x_m0_m0_m0_l0_fp_fma;
  assign ix_fp_fma_a_m0 = ix_fp_fma_a_m0_m0_m0_l0_fp_fma;
  assign ix_fp_fma_b_m0 = ix_fp_fma_b_m0_m0_m0_l0_fp_fma;
  assign ix_fp_fma_c_m0 = ix_fp_fma_c_m0_m0_m0_l0_fp_fma;
  assign ix_fp_fma_op_m0 = ix_fp_fma_op_m0_m0_m0_l0_fp_fma;
  assign y_m1 = y_m1_m1_l0_rounder | y_m1_m1_l0_fp_fma | y_m1_m1_l0_fp_comparator;
  assign fl_m1 = fl_m1_m1_l0_rounder | fl_m1_m1_l0_fp_fma | fl_m1_m1_l0_fp_comparator;
  assign xa_m1 = xa_m1_m1_m1_l0_unpacker;
  assign xb_m1 = xb_m1_m1_m1_l0_unpacker;
  assign xc_m1 = xc_m1_m1_m1_l0_unpacker;
  assign dena_m1 = dena_m1_m1_m1_l0_unpacker;
  assign denb_m1 = denb_m1_m1_m1_l0_unpacker;
  assign denc_m1 = denc_m1_m1_m1_l0_unpacker;
  assign x_m1 = x_m1_m1_m1_l0_fp_fma;
  assign ix_fp_fma_a_m1 = ix_fp_fma_a_m1_m1_m1_l0_fp_fma;
  assign ix_fp_fma_b_m1 = ix_fp_fma_b_m1_m1_m1_l0_fp_fma;
  assign ix_fp_fma_c_m1 = ix_fp_fma_c_m1_m1_m1_l0_fp_fma;
  assign ix_fp_fma_op_m1 = ix_fp_fma_op_m1_m1_m1_l0_fp_fma;
  assign y_m2 = y_m2_m2_l0_rounder | y_m2_m2_l0_fp_fma | y_m2_m2_l0_fp_comparator;
  assign fl_m2 = fl_m2_m2_l0_rounder | fl_m2_m2_l0_fp_fma | fl_m2_m2_l0_fp_comparator;
  assign xa_m2 = xa_m2_m2_m2_l0_unpacker;
  assign xb_m2 = xb_m2_m2_m2_l0_unpacker;
  assign xc_m2 = xc_m2_m2_m2_l0_unpacker;
  assign dena_m2 = dena_m2_m2_m2_l0_unpacker;
  assign denb_m2 = denb_m2_m2_m2_l0_unpacker;
  assign denc_m2 = denc_m2_m2_m2_l0_unpacker;
  assign x_m2 = x_m2_m2_m2_l0_fp_fma;
  assign y_m3 = y_m3_m3_l0_rounder | y_m3_m3_l0_fp_fma | y_m3_m3_l0_fp_comparator;
  assign fl_m3 = fl_m3_m3_l0_rounder | fl_m3_m3_l0_fp_fma | fl_m3_m3_l0_fp_comparator;
  assign xa_m3 = xa_m3_m3_m3_l0_unpacker;
  assign xb_m3 = xb_m3_m3_m3_l0_unpacker;
  assign xc_m3 = xc_m3_m3_m3_l0_unpacker;
  assign dena_m3 = dena_m3_m3_m3_l0_unpacker;
  assign denb_m3 = denb_m3_m3_m3_l0_unpacker;
  assign denc_m3 = denc_m3_m3_m3_l0_unpacker;
  assign x_m3 = x_m3_m3_m3_l0_fp_fma;
  alu_core_u_m0_l0_unpacker u_m0_l0_unpacker (.a(a), .b(b), .c(c), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .xa_m0(xa_m0_m0_m0_l0_unpacker), .xb_m0(xb_m0_m0_m0_l0_unpacker), .xc_m0(xc_m0_m0_m0_l0_unpacker), .dena_m0(dena_m0_m0_m0_l0_unpacker), .denb_m0(denb_m0_m0_m0_l0_unpacker), .denc_m0(denc_m0_m0_m0_l0_unpacker));
  alu_core_u_m0_l0_rounder u_m0_l0_rounder (.a(a), .b(b), .c(c), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_m0_l0_rounder), .fl_m0(fl_m0_m0_l0_rounder), .xa_m0(xa_m0), .xb_m0(xb_m0), .xc_m0(xc_m0), .dena_m0(dena_m0), .denb_m0(denb_m0), .denc_m0(denc_m0), .x_m0(x_m0));
  alu_core_u_m0_l0_fp_fma u_m0_l0_fp_fma (.a(a), .b(b), .c(c), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_m0_l0_fp_fma), .fl_m0(fl_m0_m0_l0_fp_fma), .xa_m0(xa_m0), .xb_m0(xb_m0), .xc_m0(xc_m0), .dena_m0(dena_m0), .denb_m0(denb_m0), .denc_m0(denc_m0), .x_m0(x_m0_m0_m0_l0_fp_fma), .ix_fp_fma_a_m0(ix_fp_fma_a_m0_m0_m0_l0_fp_fma), .ix_fp_fma_b_m0(ix_fp_fma_b_m0_m0_m0_l0_fp_fma), .ix_fp_fma_c_m0(ix_fp_fma_c_m0_m0_m0_l0_fp_fma), .ix_fp_fma_op_m0(ix_fp_fma_op_m0_m0_m0_l0_fp_fma), .iy_fp_fma_m0(iy_fp_fma_m0));
  alu_core_u_m0_l0_fp_comparator u_m0_l0_fp_comparator (.a(a), .b(b), .c(c), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_m0_l0_fp_comparator), .fl_m0(fl_m0_m0_l0_fp_comparator), .xa_m0(xa_m0), .xb_m0(xb_m0), .xc_m0(xc_m0), .dena_m0(dena_m0), .denb_m0(denb_m0), .denc_m0(denc_m0));
  alu_core_u_m1_l0_unpacker u_m1_l0_unpacker (.a(a), .b(b), .c(c), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .xa_m1(xa_m1_m1_m1_l0_unpacker), .xb_m1(xb_m1_m1_m1_l0_unpacker), .xc_m1(xc_m1_m1_m1_l0_unpacker), .dena_m1(dena_m1_m1_m1_l0_unpacker), .denb_m1(denb_m1_m1_m1_l0_unpacker), .denc_m1(denc_m1_m1_m1_l0_unpacker));
  alu_core_u_m1_l0_rounder u_m1_l0_rounder (.a(a), .b(b), .c(c), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l0_rounder), .fl_m1(fl_m1_m1_l0_rounder), .xa_m1(xa_m1), .xb_m1(xb_m1), .xc_m1(xc_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .denc_m1(denc_m1), .x_m1(x_m1));
  alu_core_u_m1_l0_fp_fma u_m1_l0_fp_fma (.a(a), .b(b), .c(c), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l0_fp_fma), .fl_m1(fl_m1_m1_l0_fp_fma), .xa_m1(xa_m1), .xb_m1(xb_m1), .xc_m1(xc_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .denc_m1(denc_m1), .x_m1(x_m1_m1_m1_l0_fp_fma), .ix_fp_fma_a_m1(ix_fp_fma_a_m1_m1_m1_l0_fp_fma), .ix_fp_fma_b_m1(ix_fp_fma_b_m1_m1_m1_l0_fp_fma), .ix_fp_fma_c_m1(ix_fp_fma_c_m1_m1_m1_l0_fp_fma), .ix_fp_fma_op_m1(ix_fp_fma_op_m1_m1_m1_l0_fp_fma), .iy_fp_fma_m1(iy_fp_fma_m1));
  alu_core_u_m1_l0_fp_comparator u_m1_l0_fp_comparator (.a(a), .b(b), .c(c), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l0_fp_comparator), .fl_m1(fl_m1_m1_l0_fp_comparator), .xa_m1(xa_m1), .xb_m1(xb_m1), .xc_m1(xc_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .denc_m1(denc_m1));
  alu_core_u_m2_l0_unpacker u_m2_l0_unpacker (.a(a), .b(b), .c(c), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .xa_m2(xa_m2_m2_m2_l0_unpacker), .xb_m2(xb_m2_m2_m2_l0_unpacker), .xc_m2(xc_m2_m2_m2_l0_unpacker), .dena_m2(dena_m2_m2_m2_l0_unpacker), .denb_m2(denb_m2_m2_m2_l0_unpacker), .denc_m2(denc_m2_m2_m2_l0_unpacker));
  alu_core_u_m2_l0_rounder u_m2_l0_rounder (.a(a), .b(b), .c(c), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_m2_l0_rounder), .fl_m2(fl_m2_m2_l0_rounder), .xa_m2(xa_m2), .xb_m2(xb_m2), .xc_m2(xc_m2), .dena_m2(dena_m2), .denb_m2(denb_m2), .denc_m2(denc_m2), .x_m2(x_m2));
  alu_core_u_m2_l0_fp_fma u_m2_l0_fp_fma (.a(a), .b(b), .c(c), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_m2_l0_fp_fma), .fl_m2(fl_m2_m2_l0_fp_fma), .xa_m2(xa_m2), .xb_m2(xb_m2), .xc_m2(xc_m2), .dena_m2(dena_m2), .denb_m2(denb_m2), .denc_m2(denc_m2), .x_m2(x_m2_m2_m2_l0_fp_fma));
  alu_core_u_m2_l0_fp_comparator u_m2_l0_fp_comparator (.a(a), .b(b), .c(c), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_m2_l0_fp_comparator), .fl_m2(fl_m2_m2_l0_fp_comparator), .xa_m2(xa_m2), .xb_m2(xb_m2), .xc_m2(xc_m2), .dena_m2(dena_m2), .denb_m2(denb_m2), .denc_m2(denc_m2));
  alu_core_u_m3_l0_unpacker u_m3_l0_unpacker (.a(a), .b(b), .c(c), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .xa_m3(xa_m3_m3_m3_l0_unpacker), .xb_m3(xb_m3_m3_m3_l0_unpacker), .xc_m3(xc_m3_m3_m3_l0_unpacker), .dena_m3(dena_m3_m3_m3_l0_unpacker), .denb_m3(denb_m3_m3_m3_l0_unpacker), .denc_m3(denc_m3_m3_m3_l0_unpacker));
  alu_core_u_m3_l0_rounder u_m3_l0_rounder (.a(a), .b(b), .c(c), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m3(y_m3_m3_l0_rounder), .fl_m3(fl_m3_m3_l0_rounder), .xa_m3(xa_m3), .xb_m3(xb_m3), .xc_m3(xc_m3), .dena_m3(dena_m3), .denb_m3(denb_m3), .denc_m3(denc_m3), .x_m3(x_m3));
  alu_core_u_m3_l0_fp_fma u_m3_l0_fp_fma (.a(a), .b(b), .c(c), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m3(y_m3_m3_l0_fp_fma), .fl_m3(fl_m3_m3_l0_fp_fma), .xa_m3(xa_m3), .xb_m3(xb_m3), .xc_m3(xc_m3), .dena_m3(dena_m3), .denb_m3(denb_m3), .denc_m3(denc_m3), .x_m3(x_m3_m3_m3_l0_fp_fma));
  alu_core_u_m3_l0_fp_comparator u_m3_l0_fp_comparator (.a(a), .b(b), .c(c), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m3(y_m3_m3_l0_fp_comparator), .fl_m3(fl_m3_m3_l0_fp_comparator), .xa_m3(xa_m3), .xb_m3(xb_m3), .xc_m3(xc_m3), .dena_m3(dena_m3), .denb_m3(denb_m3), .denc_m3(denc_m3));
  assign shared_fp_fma_a_l0 = mode == 2'd0 ? alu_core_shared_operand(ix_fp_fma_a_m0[0 +: 46]) : mode == 2'd1 ? alu_core_shared_operand(ix_fp_fma_a_m1[0 +: 46]) : '0;
  assign shared_fp_fma_b_l0 = mode == 2'd0 ? alu_core_shared_operand(ix_fp_fma_b_m0[0 +: 46]) : mode == 2'd1 ? alu_core_shared_operand(ix_fp_fma_b_m1[0 +: 46]) : '0;
  assign shared_fp_fma_c_l0 = mode == 2'd0 ? alu_core_shared_operand(ix_fp_fma_c_m0[0 +: 46]) : mode == 2'd1 ? alu_core_shared_operand(ix_fp_fma_c_m1[0 +: 46]) : '0;
  assign shared_fp_fma_op_l0 = mode == 2'd0 ? ix_fp_fma_op_m0 : mode == 2'd1 ? ix_fp_fma_op_m1 : 3'd0;
  assign iy_fp_fma_m0[0 +: 46] = shared_fp_fma_y_l0;
  assign iy_fp_fma_m1[0 +: 46] = shared_fp_fma_y_l0;
  fam_fp_fma_classic_fma_x26e16s11_p0de96c130150 u_shared_fp_fma_l0 (.xa(shared_fp_fma_a_l0), .xb(shared_fp_fma_b_l0), .xc(shared_fp_fma_c_l0), .fop(shared_fp_fma_op_l0), .y(shared_fp_fma_y_l0));
  always_comb begin
    case (mode)
      2'd0: begin y = y_m0; fl_all = fl_m0; end
      2'd1: begin y = y_m1; fl_all = fl_m1; end
      2'd2: begin y = y_m2; fl_all = fl_m2; end
      2'd3: begin y = y_m3; fl_all = fl_m3; end
      default: begin y = '0; fl_all = '0; end
    endcase
  end
  assign flags[0] = fl_all[0];
  assign flags[1] = fl_all[2];
  assign flags[2] = fl_all[3];
  assign flags[3] = fl_all[4];
endmodule
// EVOLVE-BLOCK-END

module alu_core_m0_fp_adder_fp_fma_fp_multiplier_sh #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [15:0] c,
  input  logic [3:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m0,
  output logic [9:0] fl_m0,
  input  logic [45:0] xa_m0,
  input  logic [45:0] xb_m0,
  input  logic [45:0] xc_m0,
  input  logic [0:0] dena_m0,
  input  logic [0:0] denb_m0,
  input  logic [0:0] denc_m0,
  output logic [45:0] x_m0,
  output logic [45:0] ix_fp_fma_a_m0,
  output logic [45:0] ix_fp_fma_b_m0,
  output logic [45:0] ix_fp_fma_c_m0,
  output logic [2:0] ix_fp_fma_op_m0,
  input  logic [45:0] iy_fp_fma_m0
);
  // alu_core_m0_fp_adder_fp_fma_fp_multiplier_sh: lane LANE of mode 0 (fp16) for the fp_adder/fp_fma/fp_multiplier ops fadd, fsub, fmul, fmadd, fmsub, fnmsub, fnmadd; the result buses are the mode's, with only this lane's bits written; the unit's shared interop_fp_fma serve this lane through the pc_/tp_ buses
  import alu_core_m0_pkg::*;
  logic d_m0;
  logic [15:0] m0_aLANE;
  logic [15:0] m0_bLANE;
  logic [15:0] m0_cLANE;
  logic [30:0] m0_uaLANE;
  logic [30:0] m0_ubLANE;
  logic [30:0] m0_ucLANE;
  logic [45:0] m0_xa [0:0];
  logic m0_dena [0:0];
  logic [45:0] m0_xb [0:0];
  logic m0_denb [0:0];
  logic [45:0] m0_xc [0:0];
  logic m0_denc [0:0];
  logic [25:0] m0_o0t0_LANE;
  logic [45:0] m0_o0t0_LANE_x;
  logic [45:0] m0_o0t0_LANE_z;
  logic [25:0] m0_o1t0_LANE;
  logic [45:0] m0_o1t0_LANE_x;
  logic [45:0] m0_o1t0_LANE_z;
  logic [25:0] m0_o2t0_LANE;
  logic [45:0] m0_o2t0_LANE_x;
  logic [45:0] m0_o2t0_LANE_z;
  logic [25:0] m0_o3t0_LANE;
  logic [45:0] m0_o3t0_LANE_x;
  logic [45:0] m0_o3t0_LANE_z;
  logic [25:0] m0_o4t0_LANE;
  logic [45:0] m0_o4t0_LANE_x;
  logic [45:0] m0_o4t0_LANE_z;
  logic [25:0] m0_o5t0_LANE;
  logic [45:0] m0_o5t0_LANE_x;
  logic [45:0] m0_o5t0_LANE_z;
  logic [25:0] m0_o6t0_LANE;
  logic [45:0] m0_o6t0_LANE_x;
  logic [45:0] m0_o6t0_LANE_z;
  assign m0_aLANE = a[(LANE*16) +: 16];
  assign m0_bLANE = b[(LANE*16) +: 16];
  assign m0_cLANE = c[(LANE*16) +: 16];
  // structure core.unpacker.m0: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp16_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp16_x26e16s11_p9bfe39588414 u_m0_unpack_aLANE (.b(m0_aLANE), .daz(daz), .u(m0_uaLANE));
  // structure core.unpacker.m0: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp16_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp16_x26e16s11_p9bfe39588414 u_m0_unpack_bLANE (.b(m0_bLANE), .daz(daz), .u(m0_ubLANE));
  // structure core.unpacker.m0: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp16_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp16_x26e16s11_p9bfe39588414 u_m0_unpack_cLANE (.b(m0_cLANE), .daz(daz), .u(m0_ucLANE));
  assign m0_xa[LANE] = m0_x(m0_uaLANE[29:0]);
  assign m0_dena[LANE] = m0_uaLANE[30];
  assign m0_xb[LANE] = m0_x(m0_ubLANE[29:0]);
  assign m0_denb[LANE] = m0_ubLANE[30];
  assign m0_xc[LANE] = m0_x(m0_ucLANE[29:0]);
  assign m0_denc[LANE] = m0_ucLANE[30];
  always_comb begin
    y_m0 = '0; d_m0 = '0; fl_m0 = '0;
    m0_o0t0_LANE = 'x; m0_o0t0_LANE_x = 'x; m0_o0t0_LANE_z = 'x; m0_o1t0_LANE = 'x; m0_o1t0_LANE_x = 'x; m0_o1t0_LANE_z = 'x;
    m0_o2t0_LANE = 'x; m0_o2t0_LANE_x = 'x; m0_o2t0_LANE_z = 'x; m0_o3t0_LANE = 'x; m0_o3t0_LANE_x = 'x; m0_o3t0_LANE_z = 'x;
    m0_o4t0_LANE = 'x; m0_o4t0_LANE_x = 'x; m0_o4t0_LANE_z = 'x; m0_o5t0_LANE = 'x; m0_o5t0_LANE_x = 'x; m0_o5t0_LANE_z = 'x;
    m0_o6t0_LANE = 'x; m0_o6t0_LANE_x = 'x; m0_o6t0_LANE_z = 'x;
    ix_fp_fma_a_m0 = '0; ix_fp_fma_b_m0 = '0; ix_fp_fma_c_m0 = '0; ix_fp_fma_op_m0 = '0;
    x_m0 = '0;
    case (op)
      4'd0: begin
        ix_fp_fma_a_m0[((LANE)+0)*46 +: 46] = m0_xa[LANE]; ix_fp_fma_b_m0[((LANE)+0)*46 +: 46] = m0_xb[LANE]; ix_fp_fma_op_m0[((LANE)+0)*3 +: 3] = 3'd0; m0_o0t0_LANE_x = iy_fp_fma_m0[((LANE)+0)*46 +: 46];
        m0_o0t0_LANE_z = { m0_o0t0_LANE_x[45:44], (m0_o0t0_LANE_x[45:44] == 2'd0 && m0_o0t0_LANE_x[26:0] == 0) ? (((m0_xa[LANE][45:44] == 2'd0 && m0_xa[LANE][26:0] == 0) && (m0_xb[LANE][45:44] == 2'd0 && m0_xb[LANE][26:0] == 0)) ? ((rnd == 3'd2) ? (m0_aLANE[15] | (m0_bLANE[15] ^ 1'b0)) : (m0_aLANE[15] & (m0_bLANE[15] ^ 1'b0))) : ((rnd == 3'd2) ? 1'b1 : 1'b0)) : m0_o0t0_LANE_x[43], m0_o0t0_LANE_x[42:0] };
        x_m0[LANE*46 +: 46] = m0_o0t0_LANE_z;
      end
      4'd1: begin
        ix_fp_fma_a_m0[((LANE)+0)*46 +: 46] = m0_xa[LANE]; ix_fp_fma_b_m0[((LANE)+0)*46 +: 46] = m0_xb[LANE]; ix_fp_fma_op_m0[((LANE)+0)*3 +: 3] = 3'd1; m0_o1t0_LANE_x = iy_fp_fma_m0[((LANE)+0)*46 +: 46];
        m0_o1t0_LANE_z = { m0_o1t0_LANE_x[45:44], (m0_o1t0_LANE_x[45:44] == 2'd0 && m0_o1t0_LANE_x[26:0] == 0) ? (((m0_xa[LANE][45:44] == 2'd0 && m0_xa[LANE][26:0] == 0) && (m0_xb[LANE][45:44] == 2'd0 && m0_xb[LANE][26:0] == 0)) ? ((rnd == 3'd2) ? (m0_aLANE[15] | (m0_bLANE[15] ^ 1'b1)) : (m0_aLANE[15] & (m0_bLANE[15] ^ 1'b1))) : ((rnd == 3'd2) ? 1'b1 : 1'b0)) : m0_o1t0_LANE_x[43], m0_o1t0_LANE_x[42:0] };
        x_m0[LANE*46 +: 46] = m0_o1t0_LANE_z;
      end
      4'd2: begin
        ix_fp_fma_a_m0[((LANE)+0)*46 +: 46] = m0_xa[LANE]; ix_fp_fma_b_m0[((LANE)+0)*46 +: 46] = m0_xb[LANE]; ix_fp_fma_op_m0[((LANE)+0)*3 +: 3] = 3'd2; m0_o2t0_LANE_x = iy_fp_fma_m0[((LANE)+0)*46 +: 46];
        m0_o2t0_LANE_z = { m0_o2t0_LANE_x[45:44], (m0_o2t0_LANE_x[45:44] == 2'd0 && m0_o2t0_LANE_x[26:0] == 0) ? (m0_aLANE[15] ^ m0_bLANE[15]) : m0_o2t0_LANE_x[43], m0_o2t0_LANE_x[42:0] };
        x_m0[LANE*46 +: 46] = m0_o2t0_LANE_z;
      end
      4'd3: begin
        ix_fp_fma_a_m0[((LANE)+0)*46 +: 46] = m0_xa[LANE]; ix_fp_fma_b_m0[((LANE)+0)*46 +: 46] = m0_xb[LANE]; ix_fp_fma_c_m0[((LANE)+0)*46 +: 46] = m0_xc[LANE]; ix_fp_fma_op_m0[((LANE)+0)*3 +: 3] = 3'd3; m0_o3t0_LANE_x = iy_fp_fma_m0[((LANE)+0)*46 +: 46];
        m0_o3t0_LANE_z = { m0_o3t0_LANE_x[45:44], (m0_o3t0_LANE_x[45:44] == 2'd0 && m0_o3t0_LANE_x[26:0] == 0) ? ((((m0_xa[LANE][45:44] == 2'd0 && m0_xa[LANE][26:0] == 0) || (m0_xb[LANE][45:44] == 2'd0 && m0_xb[LANE][26:0] == 0)) && (m0_xc[LANE][45:44] == 2'd0 && m0_xc[LANE][26:0] == 0)) ? ((rnd == 3'd2) ? ((m0_aLANE[15] ^ m0_bLANE[15] ^ 1'b0) | (m0_cLANE[15] ^ 1'b0)) : ((m0_aLANE[15] ^ m0_bLANE[15] ^ 1'b0) & (m0_cLANE[15] ^ 1'b0))) : ((rnd == 3'd2) ? 1'b1 : 1'b0)) : m0_o3t0_LANE_x[43], m0_o3t0_LANE_x[42:0] };
        x_m0[LANE*46 +: 46] = m0_o3t0_LANE_z;
      end
      4'd4: begin
        ix_fp_fma_a_m0[((LANE)+0)*46 +: 46] = m0_xa[LANE]; ix_fp_fma_b_m0[((LANE)+0)*46 +: 46] = m0_xb[LANE]; ix_fp_fma_c_m0[((LANE)+0)*46 +: 46] = m0_xc[LANE]; ix_fp_fma_op_m0[((LANE)+0)*3 +: 3] = 3'd4; m0_o4t0_LANE_x = iy_fp_fma_m0[((LANE)+0)*46 +: 46];
        m0_o4t0_LANE_z = { m0_o4t0_LANE_x[45:44], (m0_o4t0_LANE_x[45:44] == 2'd0 && m0_o4t0_LANE_x[26:0] == 0) ? ((((m0_xa[LANE][45:44] == 2'd0 && m0_xa[LANE][26:0] == 0) || (m0_xb[LANE][45:44] == 2'd0 && m0_xb[LANE][26:0] == 0)) && (m0_xc[LANE][45:44] == 2'd0 && m0_xc[LANE][26:0] == 0)) ? ((rnd == 3'd2) ? ((m0_aLANE[15] ^ m0_bLANE[15] ^ 1'b0) | (m0_cLANE[15] ^ 1'b1)) : ((m0_aLANE[15] ^ m0_bLANE[15] ^ 1'b0) & (m0_cLANE[15] ^ 1'b1))) : ((rnd == 3'd2) ? 1'b1 : 1'b0)) : m0_o4t0_LANE_x[43], m0_o4t0_LANE_x[42:0] };
        x_m0[LANE*46 +: 46] = m0_o4t0_LANE_z;
      end
      4'd5: begin
        ix_fp_fma_a_m0[((LANE)+0)*46 +: 46] = m0_xa[LANE]; ix_fp_fma_b_m0[((LANE)+0)*46 +: 46] = m0_xb[LANE]; ix_fp_fma_c_m0[((LANE)+0)*46 +: 46] = m0_xc[LANE]; ix_fp_fma_op_m0[((LANE)+0)*3 +: 3] = 3'd5; m0_o5t0_LANE_x = iy_fp_fma_m0[((LANE)+0)*46 +: 46];
        m0_o5t0_LANE_z = { m0_o5t0_LANE_x[45:44], (m0_o5t0_LANE_x[45:44] == 2'd0 && m0_o5t0_LANE_x[26:0] == 0) ? ((((m0_xa[LANE][45:44] == 2'd0 && m0_xa[LANE][26:0] == 0) || (m0_xb[LANE][45:44] == 2'd0 && m0_xb[LANE][26:0] == 0)) && (m0_xc[LANE][45:44] == 2'd0 && m0_xc[LANE][26:0] == 0)) ? ((rnd == 3'd2) ? ((m0_aLANE[15] ^ m0_bLANE[15] ^ 1'b1) | (m0_cLANE[15] ^ 1'b0)) : ((m0_aLANE[15] ^ m0_bLANE[15] ^ 1'b1) & (m0_cLANE[15] ^ 1'b0))) : ((rnd == 3'd2) ? 1'b1 : 1'b0)) : m0_o5t0_LANE_x[43], m0_o5t0_LANE_x[42:0] };
        x_m0[LANE*46 +: 46] = m0_o5t0_LANE_z;
      end
      4'd6: begin
        ix_fp_fma_a_m0[((LANE)+0)*46 +: 46] = m0_xa[LANE]; ix_fp_fma_b_m0[((LANE)+0)*46 +: 46] = m0_xb[LANE]; ix_fp_fma_c_m0[((LANE)+0)*46 +: 46] = m0_xc[LANE]; ix_fp_fma_op_m0[((LANE)+0)*3 +: 3] = 3'd6; m0_o6t0_LANE_x = iy_fp_fma_m0[((LANE)+0)*46 +: 46];
        m0_o6t0_LANE_z = { m0_o6t0_LANE_x[45:44], (m0_o6t0_LANE_x[45:44] == 2'd0 && m0_o6t0_LANE_x[26:0] == 0) ? ((((m0_xa[LANE][45:44] == 2'd0 && m0_xa[LANE][26:0] == 0) || (m0_xb[LANE][45:44] == 2'd0 && m0_xb[LANE][26:0] == 0)) && (m0_xc[LANE][45:44] == 2'd0 && m0_xc[LANE][26:0] == 0)) ? ((rnd == 3'd2) ? ((m0_aLANE[15] ^ m0_bLANE[15] ^ 1'b1) | (m0_cLANE[15] ^ 1'b1)) : ((m0_aLANE[15] ^ m0_bLANE[15] ^ 1'b1) & (m0_cLANE[15] ^ 1'b1))) : ((rnd == 3'd2) ? 1'b1 : 1'b0)) : m0_o6t0_LANE_x[43], m0_o6t0_LANE_x[42:0] };
        x_m0[LANE*46 +: 46] = m0_o6t0_LANE_z;
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m0_fp_comparator #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [15:0] c,
  input  logic [3:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m0,
  output logic [9:0] fl_m0,
  input  logic [45:0] xa_m0,
  input  logic [45:0] xb_m0,
  input  logic [45:0] xc_m0,
  input  logic [0:0] dena_m0,
  input  logic [0:0] denb_m0,
  input  logic [0:0] denc_m0
);
  // alu_core_m0_fp_comparator: lane LANE of mode 0 (fp16) for the fp_comparator ops fmin, fmax, fcmp; the result buses are the mode's, with only this lane's bits written
  import alu_core_m0_pkg::*;
  logic d_m0;
  logic [15:0] m0_aLANE;
  logic [15:0] m0_bLANE;
  logic [15:0] m0_cLANE;
  logic [30:0] m0_uaLANE;
  logic [30:0] m0_ubLANE;
  logic [30:0] m0_ucLANE;
  logic [45:0] m0_xa [0:0];
  logic m0_dena [0:0];
  logic [45:0] m0_xb [0:0];
  logic m0_denb [0:0];
  logic [45:0] m0_xc [0:0];
  logic m0_denc [0:0];
  logic [45:0] m0_fc_xaLANE;
  logic [45:0] m0_fc_xbLANE;
  logic m0_fc_ltLANE;
  logic m0_fc_eqLANE;
  assign m0_aLANE = a[(LANE*16) +: 16];
  assign m0_bLANE = b[(LANE*16) +: 16];
  assign m0_cLANE = c[(LANE*16) +: 16];
  // structure core.unpacker.m0: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp16_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp16_x26e16s11_p9bfe39588414 u_m0_unpack_aLANE (.b(m0_aLANE), .daz(daz), .u(m0_uaLANE));
  // structure core.unpacker.m0: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp16_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp16_x26e16s11_p9bfe39588414 u_m0_unpack_bLANE (.b(m0_bLANE), .daz(daz), .u(m0_ubLANE));
  // structure core.unpacker.m0: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp16_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp16_x26e16s11_p9bfe39588414 u_m0_unpack_cLANE (.b(m0_cLANE), .daz(daz), .u(m0_ucLANE));
  assign m0_xa[LANE] = m0_x(m0_uaLANE[29:0]);
  assign m0_dena[LANE] = m0_uaLANE[30];
  assign m0_xb[LANE] = m0_x(m0_ubLANE[29:0]);
  assign m0_denb[LANE] = m0_ubLANE[30];
  assign m0_xc[LANE] = m0_x(m0_ucLANE[29:0]);
  assign m0_denc[LANE] = m0_ucLANE[30];
  // structure core.fp_comparator.m0: family integer_compare_on_bits realized by the library module fam_fp_cmp_integer_compare_on_bits_x26e16s11_pa61fc99a71d5
  fam_fp_cmp_integer_compare_on_bits_x26e16s11_pa61fc99a71d5 u_m0_fcmpLANE (.xa(m0_fc_xaLANE), .xb(m0_fc_xbLANE), .lt(m0_fc_ltLANE), .eq(m0_fc_eqLANE));
  always_comb begin
    y_m0 = '0; d_m0 = '0; fl_m0 = '0;
    m0_fc_xaLANE = 'x; m0_fc_xbLANE = 'x;
    case (op)
      4'd7: begin
        m0_fc_xaLANE = m0_xa[LANE]; m0_fc_xbLANE = m0_xb[LANE];
        y_m0[((LANE*16)+0) +: 16] = ((m0_xa[LANE][45:44] == 2'd1) || (m0_xb[LANE][45:44] == 2'd1)) ? (1'b0 ? ((m0_xa[LANE][45:44] == 2'd1) ? m0_aLANE : m0_bLANE) : 16'd32256) : ((((m0_xa[LANE][45:44] == 2'd0 && m0_xa[LANE][26:0] == 0) && (m0_xb[LANE][45:44] == 2'd0 && m0_xb[LANE][26:0] == 0)) ? (m0_aLANE[15] == 1'b1 || m0_aLANE[15] == m0_bLANE[15]) : (m0_fc_ltLANE || m0_fc_eqLANE)) ? m0_aLANE : m0_bLANE);
        fl_m0[(0+LANE)*10 +: 10] = (((m0_xa[LANE][45:44] == 2'd1) || (m0_xb[LANE][45:44] == 2'd1)) ? (((10'd1 << 9)) | ((((m0_xa[LANE][45:44] == 2'd1) && !m0_aLANE[9]) || ((m0_xb[LANE][45:44] == 2'd1) && !m0_bLANE[9])) ? (10'd1 << 0) : 10'd0) | ((1'b1 || ((m0_xa[LANE][45:44] == 2'd1) && (m0_xb[LANE][45:44] == 2'd1))) ? (10'd1 << 5) : 10'd0)) : 10'd0) | (m0_dena[LANE] | m0_denb[LANE] ? (10'd1 << 6) : 10'd0);
      end
      4'd8: begin
        m0_fc_xaLANE = m0_xa[LANE]; m0_fc_xbLANE = m0_xb[LANE];
        y_m0[((LANE*16)+0) +: 16] = ((m0_xa[LANE][45:44] == 2'd1) || (m0_xb[LANE][45:44] == 2'd1)) ? (1'b0 ? ((m0_xa[LANE][45:44] == 2'd1) ? m0_aLANE : m0_bLANE) : 16'd32256) : ((((m0_xa[LANE][45:44] == 2'd0 && m0_xa[LANE][26:0] == 0) && (m0_xb[LANE][45:44] == 2'd0 && m0_xb[LANE][26:0] == 0)) ? (m0_aLANE[15] == 1'b0 || m0_aLANE[15] == m0_bLANE[15]) : ((!m0_fc_ltLANE && !m0_fc_eqLANE) || m0_fc_eqLANE)) ? m0_aLANE : m0_bLANE);
        fl_m0[(0+LANE)*10 +: 10] = (((m0_xa[LANE][45:44] == 2'd1) || (m0_xb[LANE][45:44] == 2'd1)) ? (((10'd1 << 9)) | ((((m0_xa[LANE][45:44] == 2'd1) && !m0_aLANE[9]) || ((m0_xb[LANE][45:44] == 2'd1) && !m0_bLANE[9])) ? (10'd1 << 0) : 10'd0) | ((1'b1 || ((m0_xa[LANE][45:44] == 2'd1) && (m0_xb[LANE][45:44] == 2'd1))) ? (10'd1 << 5) : 10'd0)) : 10'd0) | (m0_dena[LANE] | m0_denb[LANE] ? (10'd1 << 6) : 10'd0);
      end
      4'd9: begin
        m0_fc_xaLANE = m0_xa[LANE]; m0_fc_xbLANE = m0_xb[LANE];
        y_m0[((LANE*16)+0) +: 16] = ((m0_xa[LANE][45:44] == 2'd1) || (m0_xb[LANE][45:44] == 2'd1)) ? 16'd0 : {{13{1'b0}}, ((!m0_fc_ltLANE && !m0_fc_eqLANE)), (m0_fc_eqLANE), (m0_fc_ltLANE)};
        fl_m0[(0+LANE)*10 +: 10] = ((m0_xa[LANE][45:44] == 2'd1) || (m0_xb[LANE][45:44] == 2'd1) ? (10'd1 << 9) : 10'd0) | ((((m0_xa[LANE][45:44] == 2'd1) && !m0_aLANE[9]) || ((m0_xb[LANE][45:44] == 2'd1) && !m0_bLANE[9])) ? (10'd1 << 0) : 10'd0) | (m0_dena[LANE] | m0_denb[LANE] ? (10'd1 << 6) : 10'd0);
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m0_rounder #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [15:0] c,
  input  logic [3:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m0,
  output logic [9:0] fl_m0,
  input  logic [45:0] xa_m0,
  input  logic [45:0] xb_m0,
  input  logic [45:0] xc_m0,
  input  logic [0:0] dena_m0,
  input  logic [0:0] denb_m0,
  input  logic [0:0] denc_m0,
  input  logic [45:0] x_m0
);
  // alu_core_m0_rounder: lane LANE of mode 0 (fp16) for the rounder ops fadd, fsub, fmul, fmadd, fmsub, fnmsub, fnmadd; the result buses are the mode's, with only this lane's bits written
  import alu_core_m0_pkg::*;
  logic d_m0;
  logic [15:0] m0_aLANE;
  logic [15:0] m0_bLANE;
  logic [15:0] m0_cLANE;
  logic [30:0] m0_uaLANE;
  logic [30:0] m0_ubLANE;
  logic [30:0] m0_ucLANE;
  logic [45:0] m0_xa [0:0];
  logic m0_dena [0:0];
  logic [45:0] m0_xb [0:0];
  logic m0_denb [0:0];
  logic [45:0] m0_xc [0:0];
  logic m0_denc [0:0];
  logic [45:0] m0_rd_xLANE_fadd;
  logic [7:0] m0_rd_wLANE_fadd;
  logic [9:0] m0_rd_flLANE_fadd;
  logic [15:0] m0_rd_bLANE_fadd;
  logic [45:0] m0_rd_xLANE_fmadd;
  logic [7:0] m0_rd_wLANE_fmadd;
  logic [9:0] m0_rd_flLANE_fmadd;
  logic [15:0] m0_rd_bLANE_fmadd;
  logic [45:0] m0_rd_xLANE_fmsub;
  logic [7:0] m0_rd_wLANE_fmsub;
  logic [9:0] m0_rd_flLANE_fmsub;
  logic [15:0] m0_rd_bLANE_fmsub;
  logic [45:0] m0_rd_xLANE_fmul;
  logic [7:0] m0_rd_wLANE_fmul;
  logic [9:0] m0_rd_flLANE_fmul;
  logic [15:0] m0_rd_bLANE_fmul;
  logic [45:0] m0_rd_xLANE_fnmadd;
  logic [7:0] m0_rd_wLANE_fnmadd;
  logic [9:0] m0_rd_flLANE_fnmadd;
  logic [15:0] m0_rd_bLANE_fnmadd;
  logic [45:0] m0_rd_xLANE_fnmsub;
  logic [7:0] m0_rd_wLANE_fnmsub;
  logic [9:0] m0_rd_flLANE_fnmsub;
  logic [15:0] m0_rd_bLANE_fnmsub;
  logic [45:0] m0_rd_xLANE_fsub;
  logic [7:0] m0_rd_wLANE_fsub;
  logic [9:0] m0_rd_flLANE_fsub;
  logic [15:0] m0_rd_bLANE_fsub;
  logic [25:0] m0_o0t0_LANE;
  logic [45:0] m0_o0t0_LANE_x;
  logic [45:0] m0_o0t0_LANE_z;
  logic [25:0] m0_o1t0_LANE;
  logic [45:0] m0_o1t0_LANE_x;
  logic [45:0] m0_o1t0_LANE_z;
  logic [25:0] m0_o2t0_LANE;
  logic [45:0] m0_o2t0_LANE_x;
  logic [45:0] m0_o2t0_LANE_z;
  logic [25:0] m0_o3t0_LANE;
  logic [45:0] m0_o3t0_LANE_x;
  logic [45:0] m0_o3t0_LANE_z;
  logic [25:0] m0_o4t0_LANE;
  logic [45:0] m0_o4t0_LANE_x;
  logic [45:0] m0_o4t0_LANE_z;
  logic [25:0] m0_o5t0_LANE;
  logic [45:0] m0_o5t0_LANE_x;
  logic [45:0] m0_o5t0_LANE_z;
  logic [25:0] m0_o6t0_LANE;
  logic [45:0] m0_o6t0_LANE_x;
  logic [45:0] m0_o6t0_LANE_z;
  assign m0_aLANE = a[(LANE*16) +: 16];
  assign m0_bLANE = b[(LANE*16) +: 16];
  assign m0_cLANE = c[(LANE*16) +: 16];
  // structure core.unpacker.m0: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp16_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp16_x26e16s11_p9bfe39588414 u_m0_unpack_aLANE (.b(m0_aLANE), .daz(daz), .u(m0_uaLANE));
  // structure core.unpacker.m0: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp16_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp16_x26e16s11_p9bfe39588414 u_m0_unpack_bLANE (.b(m0_bLANE), .daz(daz), .u(m0_ubLANE));
  // structure core.unpacker.m0: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp16_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp16_x26e16s11_p9bfe39588414 u_m0_unpack_cLANE (.b(m0_cLANE), .daz(daz), .u(m0_ucLANE));
  assign m0_xa[LANE] = m0_x(m0_uaLANE[29:0]);
  assign m0_dena[LANE] = m0_uaLANE[30];
  assign m0_xb[LANE] = m0_x(m0_ubLANE[29:0]);
  assign m0_denb[LANE] = m0_ubLANE[30];
  assign m0_xc[LANE] = m0_x(m0_ucLANE[29:0]);
  assign m0_denc[LANE] = m0_ucLANE[30];
  // structure core.rounder.m0: family dedicated_per_op realized by the library module fam_fp_round_dedicated_per_op_increment_adder_fp16_x26e16s11_pd77ccc5b5c45_nin (fadd)
  fam_fp_round_dedicated_per_op_increment_adder_fp16_x26e16s11_pd77ccc5b5c45_nin u_m0_roundLANE_fadd (.x(m0_rd_xLANE_fadd), .rnd(rnd), .word(m0_rd_wLANE_fadd), .ftz(ftz), .fl(m0_rd_flLANE_fadd), .bits(m0_rd_bLANE_fadd));
  // structure core.rounder.m0: family dedicated_per_op realized by the library module fam_fp_round_dedicated_per_op_increment_adder_fp16_x26e16s11_pd77ccc5b5c45_nin (fmadd)
  fam_fp_round_dedicated_per_op_increment_adder_fp16_x26e16s11_pd77ccc5b5c45_nin u_m0_roundLANE_fmadd (.x(m0_rd_xLANE_fmadd), .rnd(rnd), .word(m0_rd_wLANE_fmadd), .ftz(ftz), .fl(m0_rd_flLANE_fmadd), .bits(m0_rd_bLANE_fmadd));
  // structure core.rounder.m0: family dedicated_per_op realized by the library module fam_fp_round_dedicated_per_op_increment_adder_fp16_x26e16s11_pd77ccc5b5c45_nin (fmsub)
  fam_fp_round_dedicated_per_op_increment_adder_fp16_x26e16s11_pd77ccc5b5c45_nin u_m0_roundLANE_fmsub (.x(m0_rd_xLANE_fmsub), .rnd(rnd), .word(m0_rd_wLANE_fmsub), .ftz(ftz), .fl(m0_rd_flLANE_fmsub), .bits(m0_rd_bLANE_fmsub));
  // structure core.rounder.m0: family dedicated_per_op realized by the library module fam_fp_round_dedicated_per_op_increment_adder_fp16_x26e16s11_pd77ccc5b5c45_nin (fmul)
  fam_fp_round_dedicated_per_op_increment_adder_fp16_x26e16s11_pd77ccc5b5c45_nin u_m0_roundLANE_fmul (.x(m0_rd_xLANE_fmul), .rnd(rnd), .word(m0_rd_wLANE_fmul), .ftz(ftz), .fl(m0_rd_flLANE_fmul), .bits(m0_rd_bLANE_fmul));
  // structure core.rounder.m0: family dedicated_per_op realized by the library module fam_fp_round_dedicated_per_op_increment_adder_fp16_x26e16s11_pd77ccc5b5c45_nin (fnmadd)
  fam_fp_round_dedicated_per_op_increment_adder_fp16_x26e16s11_pd77ccc5b5c45_nin u_m0_roundLANE_fnmadd (.x(m0_rd_xLANE_fnmadd), .rnd(rnd), .word(m0_rd_wLANE_fnmadd), .ftz(ftz), .fl(m0_rd_flLANE_fnmadd), .bits(m0_rd_bLANE_fnmadd));
  // structure core.rounder.m0: family dedicated_per_op realized by the library module fam_fp_round_dedicated_per_op_increment_adder_fp16_x26e16s11_pd77ccc5b5c45_nin (fnmsub)
  fam_fp_round_dedicated_per_op_increment_adder_fp16_x26e16s11_pd77ccc5b5c45_nin u_m0_roundLANE_fnmsub (.x(m0_rd_xLANE_fnmsub), .rnd(rnd), .word(m0_rd_wLANE_fnmsub), .ftz(ftz), .fl(m0_rd_flLANE_fnmsub), .bits(m0_rd_bLANE_fnmsub));
  // structure core.rounder.m0: family dedicated_per_op realized by the library module fam_fp_round_dedicated_per_op_increment_adder_fp16_x26e16s11_pd77ccc5b5c45_nin (fsub)
  fam_fp_round_dedicated_per_op_increment_adder_fp16_x26e16s11_pd77ccc5b5c45_nin u_m0_roundLANE_fsub (.x(m0_rd_xLANE_fsub), .rnd(rnd), .word(m0_rd_wLANE_fsub), .ftz(ftz), .fl(m0_rd_flLANE_fsub), .bits(m0_rd_bLANE_fsub));
  always_comb begin
    y_m0 = '0; d_m0 = '0; fl_m0 = '0;
    m0_rd_xLANE_fadd = 'x; m0_rd_wLANE_fadd = 'x; m0_rd_xLANE_fmadd = 'x; m0_rd_wLANE_fmadd = 'x; m0_rd_xLANE_fmsub = 'x; m0_rd_wLANE_fmsub = 'x;
    m0_rd_xLANE_fmul = 'x; m0_rd_wLANE_fmul = 'x; m0_rd_xLANE_fnmadd = 'x; m0_rd_wLANE_fnmadd = 'x; m0_rd_xLANE_fnmsub = 'x; m0_rd_wLANE_fnmsub = 'x;
    m0_rd_xLANE_fsub = 'x; m0_rd_wLANE_fsub = 'x; m0_o0t0_LANE = 'x; m0_o0t0_LANE_x = 'x; m0_o0t0_LANE_z = 'x; m0_o1t0_LANE = 'x;
    m0_o1t0_LANE_x = 'x; m0_o1t0_LANE_z = 'x; m0_o2t0_LANE = 'x; m0_o2t0_LANE_x = 'x; m0_o2t0_LANE_z = 'x; m0_o3t0_LANE = 'x;
    m0_o3t0_LANE_x = 'x; m0_o3t0_LANE_z = 'x; m0_o4t0_LANE = 'x; m0_o4t0_LANE_x = 'x; m0_o4t0_LANE_z = 'x; m0_o5t0_LANE = 'x;
    m0_o5t0_LANE_x = 'x; m0_o5t0_LANE_z = 'x; m0_o6t0_LANE = 'x; m0_o6t0_LANE_x = 'x; m0_o6t0_LANE_z = 'x;
    case (op)
      4'd0: begin
        m0_o0t0_LANE_z = x_m0[LANE*46 +: 46];
        m0_rd_xLANE_fadd = m0_o0t0_LANE_z; m0_rd_wLANE_fadd = 8'd0; m0_o0t0_LANE = {m0_rd_flLANE_fadd, m0_rd_bLANE_fadd};
        y_m0[((LANE*16)+0) +: 16] = (m0_o0t0_LANE_z[45:44] == 2'd1) ? (((m0_xa[LANE][45:44] == 2'd1) || (m0_xb[LANE][45:44] == 2'd1)) ? 16'd32256 : 16'd32256) : ((m0_o0t0_LANE_z[45:44] == 2'd0 && m0_o0t0_LANE_z[26:0] == 0) ? {m0_o0t0_LANE_z[43], 15'd0} : m0_o0t0_LANE[15:0]);
        fl_m0[(0+LANE)*10 +: 10] = (((m0_xa[LANE][45:44] == 2'd1) || (m0_xb[LANE][45:44] == 2'd1)) ? (((10'd1 << 5) | (((m0_xa[LANE][45:44] == 2'd1) && !m0_aLANE[9]) || ((m0_xb[LANE][45:44] == 2'd1) && !m0_bLANE[9]) ? (10'd1 << 0) : 10'd0)) | (m0_dena[LANE] | m0_denb[LANE] ? (10'd1 << 6) : 10'd0)) : (m0_o0t0_LANE[25:16] | ((((m0_xa[LANE][45:44] == 2'd1) && !m0_aLANE[9]) || ((m0_xb[LANE][45:44] == 2'd1) && !m0_bLANE[9]) || ((m0_o0t0_LANE_z[45:44] == 2'd1) && !((m0_xa[LANE][45:44] == 2'd1) || (m0_xb[LANE][45:44] == 2'd1)))) ? (10'd1 << 0) : 10'd0) | (m0_dena[LANE] | m0_denb[LANE] ? (10'd1 << 6) : 10'd0)));
      end
      4'd1: begin
        m0_o1t0_LANE_z = x_m0[LANE*46 +: 46];
        m0_rd_xLANE_fsub = m0_o1t0_LANE_z; m0_rd_wLANE_fsub = 8'd0; m0_o1t0_LANE = {m0_rd_flLANE_fsub, m0_rd_bLANE_fsub};
        y_m0[((LANE*16)+0) +: 16] = (m0_o1t0_LANE_z[45:44] == 2'd1) ? (((m0_xa[LANE][45:44] == 2'd1) || (m0_xb[LANE][45:44] == 2'd1)) ? 16'd32256 : 16'd32256) : ((m0_o1t0_LANE_z[45:44] == 2'd0 && m0_o1t0_LANE_z[26:0] == 0) ? {m0_o1t0_LANE_z[43], 15'd0} : m0_o1t0_LANE[15:0]);
        fl_m0[(0+LANE)*10 +: 10] = (((m0_xa[LANE][45:44] == 2'd1) || (m0_xb[LANE][45:44] == 2'd1)) ? (((10'd1 << 5) | (((m0_xa[LANE][45:44] == 2'd1) && !m0_aLANE[9]) || ((m0_xb[LANE][45:44] == 2'd1) && !m0_bLANE[9]) ? (10'd1 << 0) : 10'd0)) | (m0_dena[LANE] | m0_denb[LANE] ? (10'd1 << 6) : 10'd0)) : (m0_o1t0_LANE[25:16] | ((((m0_xa[LANE][45:44] == 2'd1) && !m0_aLANE[9]) || ((m0_xb[LANE][45:44] == 2'd1) && !m0_bLANE[9]) || ((m0_o1t0_LANE_z[45:44] == 2'd1) && !((m0_xa[LANE][45:44] == 2'd1) || (m0_xb[LANE][45:44] == 2'd1)))) ? (10'd1 << 0) : 10'd0) | (m0_dena[LANE] | m0_denb[LANE] ? (10'd1 << 6) : 10'd0)));
      end
      4'd2: begin
        m0_o2t0_LANE_z = x_m0[LANE*46 +: 46];
        m0_rd_xLANE_fmul = m0_o2t0_LANE_z; m0_rd_wLANE_fmul = 8'd0; m0_o2t0_LANE = {m0_rd_flLANE_fmul, m0_rd_bLANE_fmul};
        y_m0[((LANE*16)+0) +: 16] = (m0_o2t0_LANE_z[45:44] == 2'd1) ? (((m0_xa[LANE][45:44] == 2'd1) || (m0_xb[LANE][45:44] == 2'd1)) ? 16'd32256 : 16'd32256) : ((m0_o2t0_LANE_z[45:44] == 2'd0 && m0_o2t0_LANE_z[26:0] == 0) ? {m0_o2t0_LANE_z[43], 15'd0} : m0_o2t0_LANE[15:0]);
        fl_m0[(0+LANE)*10 +: 10] = (((m0_xa[LANE][45:44] == 2'd1) || (m0_xb[LANE][45:44] == 2'd1)) ? (((10'd1 << 5) | (((m0_xa[LANE][45:44] == 2'd1) && !m0_aLANE[9]) || ((m0_xb[LANE][45:44] == 2'd1) && !m0_bLANE[9]) ? (10'd1 << 0) : 10'd0)) | (m0_dena[LANE] | m0_denb[LANE] ? (10'd1 << 6) : 10'd0)) : (m0_o2t0_LANE[25:16] | ((((m0_xa[LANE][45:44] == 2'd1) && !m0_aLANE[9]) || ((m0_xb[LANE][45:44] == 2'd1) && !m0_bLANE[9]) || ((m0_o2t0_LANE_z[45:44] == 2'd1) && !((m0_xa[LANE][45:44] == 2'd1) || (m0_xb[LANE][45:44] == 2'd1)))) ? (10'd1 << 0) : 10'd0) | (m0_dena[LANE] | m0_denb[LANE] ? (10'd1 << 6) : 10'd0)));
      end
      4'd3: begin
        m0_o3t0_LANE_z = x_m0[LANE*46 +: 46];
        m0_rd_xLANE_fmadd = m0_o3t0_LANE_z; m0_rd_wLANE_fmadd = 8'd0; m0_o3t0_LANE = {m0_rd_flLANE_fmadd, m0_rd_bLANE_fmadd};
        y_m0[((LANE*16)+0) +: 16] = (m0_o3t0_LANE_z[45:44] == 2'd1) ? (((m0_xa[LANE][45:44] == 2'd1) || (m0_xb[LANE][45:44] == 2'd1) || (m0_xc[LANE][45:44] == 2'd1)) ? 16'd32256 : 16'd32256) : ((m0_o3t0_LANE_z[45:44] == 2'd0 && m0_o3t0_LANE_z[26:0] == 0) ? {m0_o3t0_LANE_z[43], 15'd0} : m0_o3t0_LANE[15:0]);
        fl_m0[(0+LANE)*10 +: 10] = (((m0_xa[LANE][45:44] == 2'd1) || (m0_xb[LANE][45:44] == 2'd1) || (m0_xc[LANE][45:44] == 2'd1)) ? (((10'd1 << 5) | (((m0_xa[LANE][45:44] == 2'd1) && !m0_aLANE[9]) || ((m0_xb[LANE][45:44] == 2'd1) && !m0_bLANE[9]) || ((m0_xc[LANE][45:44] == 2'd1) && !m0_cLANE[9]) ? (10'd1 << 0) : 10'd0)) | (m0_dena[LANE] | m0_denb[LANE] | m0_denc[LANE] ? (10'd1 << 6) : 10'd0)) : (m0_o3t0_LANE[25:16] | ((((m0_xa[LANE][45:44] == 2'd1) && !m0_aLANE[9]) || ((m0_xb[LANE][45:44] == 2'd1) && !m0_bLANE[9]) || ((m0_xc[LANE][45:44] == 2'd1) && !m0_cLANE[9]) || ((m0_o3t0_LANE_z[45:44] == 2'd1) && !((m0_xa[LANE][45:44] == 2'd1) || (m0_xb[LANE][45:44] == 2'd1) || (m0_xc[LANE][45:44] == 2'd1)))) ? (10'd1 << 0) : 10'd0) | (m0_dena[LANE] | m0_denb[LANE] | m0_denc[LANE] ? (10'd1 << 6) : 10'd0)));
      end
      4'd4: begin
        m0_o4t0_LANE_z = x_m0[LANE*46 +: 46];
        m0_rd_xLANE_fmsub = m0_o4t0_LANE_z; m0_rd_wLANE_fmsub = 8'd0; m0_o4t0_LANE = {m0_rd_flLANE_fmsub, m0_rd_bLANE_fmsub};
        y_m0[((LANE*16)+0) +: 16] = (m0_o4t0_LANE_z[45:44] == 2'd1) ? (((m0_xa[LANE][45:44] == 2'd1) || (m0_xb[LANE][45:44] == 2'd1) || (m0_xc[LANE][45:44] == 2'd1)) ? 16'd32256 : 16'd32256) : ((m0_o4t0_LANE_z[45:44] == 2'd0 && m0_o4t0_LANE_z[26:0] == 0) ? {m0_o4t0_LANE_z[43], 15'd0} : m0_o4t0_LANE[15:0]);
        fl_m0[(0+LANE)*10 +: 10] = (((m0_xa[LANE][45:44] == 2'd1) || (m0_xb[LANE][45:44] == 2'd1) || (m0_xc[LANE][45:44] == 2'd1)) ? (((10'd1 << 5) | (((m0_xa[LANE][45:44] == 2'd1) && !m0_aLANE[9]) || ((m0_xb[LANE][45:44] == 2'd1) && !m0_bLANE[9]) || ((m0_xc[LANE][45:44] == 2'd1) && !m0_cLANE[9]) ? (10'd1 << 0) : 10'd0)) | (m0_dena[LANE] | m0_denb[LANE] | m0_denc[LANE] ? (10'd1 << 6) : 10'd0)) : (m0_o4t0_LANE[25:16] | ((((m0_xa[LANE][45:44] == 2'd1) && !m0_aLANE[9]) || ((m0_xb[LANE][45:44] == 2'd1) && !m0_bLANE[9]) || ((m0_xc[LANE][45:44] == 2'd1) && !m0_cLANE[9]) || ((m0_o4t0_LANE_z[45:44] == 2'd1) && !((m0_xa[LANE][45:44] == 2'd1) || (m0_xb[LANE][45:44] == 2'd1) || (m0_xc[LANE][45:44] == 2'd1)))) ? (10'd1 << 0) : 10'd0) | (m0_dena[LANE] | m0_denb[LANE] | m0_denc[LANE] ? (10'd1 << 6) : 10'd0)));
      end
      4'd5: begin
        m0_o5t0_LANE_z = x_m0[LANE*46 +: 46];
        m0_rd_xLANE_fnmsub = m0_o5t0_LANE_z; m0_rd_wLANE_fnmsub = 8'd0; m0_o5t0_LANE = {m0_rd_flLANE_fnmsub, m0_rd_bLANE_fnmsub};
        y_m0[((LANE*16)+0) +: 16] = (m0_o5t0_LANE_z[45:44] == 2'd1) ? (((m0_xa[LANE][45:44] == 2'd1) || (m0_xb[LANE][45:44] == 2'd1) || (m0_xc[LANE][45:44] == 2'd1)) ? 16'd32256 : 16'd32256) : ((m0_o5t0_LANE_z[45:44] == 2'd0 && m0_o5t0_LANE_z[26:0] == 0) ? {m0_o5t0_LANE_z[43], 15'd0} : m0_o5t0_LANE[15:0]);
        fl_m0[(0+LANE)*10 +: 10] = (((m0_xa[LANE][45:44] == 2'd1) || (m0_xb[LANE][45:44] == 2'd1) || (m0_xc[LANE][45:44] == 2'd1)) ? (((10'd1 << 5) | (((m0_xa[LANE][45:44] == 2'd1) && !m0_aLANE[9]) || ((m0_xb[LANE][45:44] == 2'd1) && !m0_bLANE[9]) || ((m0_xc[LANE][45:44] == 2'd1) && !m0_cLANE[9]) ? (10'd1 << 0) : 10'd0)) | (m0_dena[LANE] | m0_denb[LANE] | m0_denc[LANE] ? (10'd1 << 6) : 10'd0)) : (m0_o5t0_LANE[25:16] | ((((m0_xa[LANE][45:44] == 2'd1) && !m0_aLANE[9]) || ((m0_xb[LANE][45:44] == 2'd1) && !m0_bLANE[9]) || ((m0_xc[LANE][45:44] == 2'd1) && !m0_cLANE[9]) || ((m0_o5t0_LANE_z[45:44] == 2'd1) && !((m0_xa[LANE][45:44] == 2'd1) || (m0_xb[LANE][45:44] == 2'd1) || (m0_xc[LANE][45:44] == 2'd1)))) ? (10'd1 << 0) : 10'd0) | (m0_dena[LANE] | m0_denb[LANE] | m0_denc[LANE] ? (10'd1 << 6) : 10'd0)));
      end
      4'd6: begin
        m0_o6t0_LANE_z = x_m0[LANE*46 +: 46];
        m0_rd_xLANE_fnmadd = m0_o6t0_LANE_z; m0_rd_wLANE_fnmadd = 8'd0; m0_o6t0_LANE = {m0_rd_flLANE_fnmadd, m0_rd_bLANE_fnmadd};
        y_m0[((LANE*16)+0) +: 16] = (m0_o6t0_LANE_z[45:44] == 2'd1) ? (((m0_xa[LANE][45:44] == 2'd1) || (m0_xb[LANE][45:44] == 2'd1) || (m0_xc[LANE][45:44] == 2'd1)) ? 16'd32256 : 16'd32256) : ((m0_o6t0_LANE_z[45:44] == 2'd0 && m0_o6t0_LANE_z[26:0] == 0) ? {m0_o6t0_LANE_z[43], 15'd0} : m0_o6t0_LANE[15:0]);
        fl_m0[(0+LANE)*10 +: 10] = (((m0_xa[LANE][45:44] == 2'd1) || (m0_xb[LANE][45:44] == 2'd1) || (m0_xc[LANE][45:44] == 2'd1)) ? (((10'd1 << 5) | (((m0_xa[LANE][45:44] == 2'd1) && !m0_aLANE[9]) || ((m0_xb[LANE][45:44] == 2'd1) && !m0_bLANE[9]) || ((m0_xc[LANE][45:44] == 2'd1) && !m0_cLANE[9]) ? (10'd1 << 0) : 10'd0)) | (m0_dena[LANE] | m0_denb[LANE] | m0_denc[LANE] ? (10'd1 << 6) : 10'd0)) : (m0_o6t0_LANE[25:16] | ((((m0_xa[LANE][45:44] == 2'd1) && !m0_aLANE[9]) || ((m0_xb[LANE][45:44] == 2'd1) && !m0_bLANE[9]) || ((m0_xc[LANE][45:44] == 2'd1) && !m0_cLANE[9]) || ((m0_o6t0_LANE_z[45:44] == 2'd1) && !((m0_xa[LANE][45:44] == 2'd1) || (m0_xb[LANE][45:44] == 2'd1) || (m0_xc[LANE][45:44] == 2'd1)))) ? (10'd1 << 0) : 10'd0) | (m0_dena[LANE] | m0_denb[LANE] | m0_denc[LANE] ? (10'd1 << 6) : 10'd0)));
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m0_unpacker #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [15:0] c,
  input  logic [3:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [45:0] xa_m0,
  output logic [45:0] xb_m0,
  output logic [45:0] xc_m0,
  output logic [0:0] dena_m0,
  output logic [0:0] denb_m0,
  output logic [0:0] denc_m0
);
  // alu_core_m0_unpacker: lane LANE of mode 0 (fp16) for the unpacker ops ; the result buses are the mode's, with only this lane's bits written
  import alu_core_m0_pkg::*;
  logic [15:0] y_m0;
  logic d_m0;
  logic [9:0] fl_m0;
  logic [15:0] m0_aLANE;
  logic [15:0] m0_bLANE;
  logic [15:0] m0_cLANE;
  logic [30:0] m0_uaLANE;
  logic [30:0] m0_ubLANE;
  logic [30:0] m0_ucLANE;
  logic [45:0] m0_xa [0:0];
  logic m0_dena [0:0];
  logic [45:0] m0_xb [0:0];
  logic m0_denb [0:0];
  logic [45:0] m0_xc [0:0];
  logic m0_denc [0:0];
  assign m0_aLANE = a[(LANE*16) +: 16];
  assign m0_bLANE = b[(LANE*16) +: 16];
  assign m0_cLANE = c[(LANE*16) +: 16];
  // structure core.unpacker.m0: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp16_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp16_x26e16s11_p9bfe39588414 u_m0_unpack_aLANE (.b(m0_aLANE), .daz(daz), .u(m0_uaLANE));
  // structure core.unpacker.m0: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp16_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp16_x26e16s11_p9bfe39588414 u_m0_unpack_bLANE (.b(m0_bLANE), .daz(daz), .u(m0_ubLANE));
  // structure core.unpacker.m0: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp16_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp16_x26e16s11_p9bfe39588414 u_m0_unpack_cLANE (.b(m0_cLANE), .daz(daz), .u(m0_ucLANE));
  assign m0_xa[LANE] = m0_x(m0_uaLANE[29:0]);
  assign m0_dena[LANE] = m0_uaLANE[30];
  assign m0_xb[LANE] = m0_x(m0_ubLANE[29:0]);
  assign m0_denb[LANE] = m0_ubLANE[30];
  assign m0_xc[LANE] = m0_x(m0_ucLANE[29:0]);
  assign m0_denc[LANE] = m0_ucLANE[30];
  always_comb begin
    xa_m0 = '0; dena_m0 = '0; xb_m0 = '0; denb_m0 = '0; xc_m0 = '0; denc_m0 = '0;
    xa_m0[LANE*46 +: 46] = m0_xa[LANE];
    dena_m0[LANE] = m0_dena[LANE];
    xb_m0[LANE*46 +: 46] = m0_xb[LANE];
    denb_m0[LANE] = m0_denb[LANE];
    xc_m0[LANE*46 +: 46] = m0_xc[LANE];
    denc_m0[LANE] = m0_denc[LANE];
  end
endmodule

module alu_core_m1_fp_adder_fp_fma_fp_multiplier_sh #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [15:0] c,
  input  logic [3:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m1,
  output logic [9:0] fl_m1,
  input  logic [45:0] xa_m1,
  input  logic [45:0] xb_m1,
  input  logic [45:0] xc_m1,
  input  logic [0:0] dena_m1,
  input  logic [0:0] denb_m1,
  input  logic [0:0] denc_m1,
  output logic [45:0] x_m1,
  output logic [45:0] ix_fp_fma_a_m1,
  output logic [45:0] ix_fp_fma_b_m1,
  output logic [45:0] ix_fp_fma_c_m1,
  output logic [2:0] ix_fp_fma_op_m1,
  input  logic [45:0] iy_fp_fma_m1
);
  // alu_core_m1_fp_adder_fp_fma_fp_multiplier_sh: lane LANE of mode 1 (bf16) for the fp_adder/fp_fma/fp_multiplier ops fadd, fsub, fmul, fmadd, fmsub, fnmsub, fnmadd; the result buses are the mode's, with only this lane's bits written; the unit's shared interop_fp_fma serve this lane through the pc_/tp_ buses
  import alu_core_m1_pkg::*;
  logic d_m1;
  logic [15:0] m1_aLANE;
  logic [15:0] m1_bLANE;
  logic [15:0] m1_cLANE;
  logic [30:0] m1_uaLANE;
  logic [30:0] m1_ubLANE;
  logic [30:0] m1_ucLANE;
  logic [45:0] m1_xa [0:0];
  logic m1_dena [0:0];
  logic [45:0] m1_xb [0:0];
  logic m1_denb [0:0];
  logic [45:0] m1_xc [0:0];
  logic m1_denc [0:0];
  logic [25:0] m1_o0t0_LANE;
  logic [45:0] m1_o0t0_LANE_x;
  logic [45:0] m1_o0t0_LANE_z;
  logic [25:0] m1_o1t0_LANE;
  logic [45:0] m1_o1t0_LANE_x;
  logic [45:0] m1_o1t0_LANE_z;
  logic [25:0] m1_o2t0_LANE;
  logic [45:0] m1_o2t0_LANE_x;
  logic [45:0] m1_o2t0_LANE_z;
  logic [25:0] m1_o3t0_LANE;
  logic [45:0] m1_o3t0_LANE_x;
  logic [45:0] m1_o3t0_LANE_z;
  logic [25:0] m1_o4t0_LANE;
  logic [45:0] m1_o4t0_LANE_x;
  logic [45:0] m1_o4t0_LANE_z;
  logic [25:0] m1_o5t0_LANE;
  logic [45:0] m1_o5t0_LANE_x;
  logic [45:0] m1_o5t0_LANE_z;
  logic [25:0] m1_o6t0_LANE;
  logic [45:0] m1_o6t0_LANE_x;
  logic [45:0] m1_o6t0_LANE_z;
  assign m1_aLANE = a[(LANE*16) +: 16];
  assign m1_bLANE = b[(LANE*16) +: 16];
  assign m1_cLANE = c[(LANE*16) +: 16];
  // structure core.unpacker.m1: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_bf16_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_bf16_x26e16s11_p9bfe39588414 u_m1_unpack_aLANE (.b(m1_aLANE), .daz(daz), .u(m1_uaLANE));
  // structure core.unpacker.m1: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_bf16_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_bf16_x26e16s11_p9bfe39588414 u_m1_unpack_bLANE (.b(m1_bLANE), .daz(daz), .u(m1_ubLANE));
  // structure core.unpacker.m1: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_bf16_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_bf16_x26e16s11_p9bfe39588414 u_m1_unpack_cLANE (.b(m1_cLANE), .daz(daz), .u(m1_ucLANE));
  assign m1_xa[LANE] = m1_x(m1_uaLANE[29:0]);
  assign m1_dena[LANE] = m1_uaLANE[30];
  assign m1_xb[LANE] = m1_x(m1_ubLANE[29:0]);
  assign m1_denb[LANE] = m1_ubLANE[30];
  assign m1_xc[LANE] = m1_x(m1_ucLANE[29:0]);
  assign m1_denc[LANE] = m1_ucLANE[30];
  always_comb begin
    y_m1 = '0; d_m1 = '0; fl_m1 = '0;
    m1_o0t0_LANE = 'x; m1_o0t0_LANE_x = 'x; m1_o0t0_LANE_z = 'x; m1_o1t0_LANE = 'x; m1_o1t0_LANE_x = 'x; m1_o1t0_LANE_z = 'x;
    m1_o2t0_LANE = 'x; m1_o2t0_LANE_x = 'x; m1_o2t0_LANE_z = 'x; m1_o3t0_LANE = 'x; m1_o3t0_LANE_x = 'x; m1_o3t0_LANE_z = 'x;
    m1_o4t0_LANE = 'x; m1_o4t0_LANE_x = 'x; m1_o4t0_LANE_z = 'x; m1_o5t0_LANE = 'x; m1_o5t0_LANE_x = 'x; m1_o5t0_LANE_z = 'x;
    m1_o6t0_LANE = 'x; m1_o6t0_LANE_x = 'x; m1_o6t0_LANE_z = 'x;
    ix_fp_fma_a_m1 = '0; ix_fp_fma_b_m1 = '0; ix_fp_fma_c_m1 = '0; ix_fp_fma_op_m1 = '0;
    x_m1 = '0;
    case (op)
      4'd0: begin
        ix_fp_fma_a_m1[((LANE)+0)*46 +: 46] = m1_xa[LANE]; ix_fp_fma_b_m1[((LANE)+0)*46 +: 46] = m1_xb[LANE]; ix_fp_fma_op_m1[((LANE)+0)*3 +: 3] = 3'd0; m1_o0t0_LANE_x = iy_fp_fma_m1[((LANE)+0)*46 +: 46];
        m1_o0t0_LANE_z = { m1_o0t0_LANE_x[45:44], (m1_o0t0_LANE_x[45:44] == 2'd0 && m1_o0t0_LANE_x[26:0] == 0) ? (((m1_xa[LANE][45:44] == 2'd0 && m1_xa[LANE][26:0] == 0) && (m1_xb[LANE][45:44] == 2'd0 && m1_xb[LANE][26:0] == 0)) ? ((rnd == 3'd2) ? (m1_aLANE[15] | (m1_bLANE[15] ^ 1'b0)) : (m1_aLANE[15] & (m1_bLANE[15] ^ 1'b0))) : ((rnd == 3'd2) ? 1'b1 : 1'b0)) : m1_o0t0_LANE_x[43], m1_o0t0_LANE_x[42:0] };
        x_m1[LANE*46 +: 46] = m1_o0t0_LANE_z;
      end
      4'd1: begin
        ix_fp_fma_a_m1[((LANE)+0)*46 +: 46] = m1_xa[LANE]; ix_fp_fma_b_m1[((LANE)+0)*46 +: 46] = m1_xb[LANE]; ix_fp_fma_op_m1[((LANE)+0)*3 +: 3] = 3'd1; m1_o1t0_LANE_x = iy_fp_fma_m1[((LANE)+0)*46 +: 46];
        m1_o1t0_LANE_z = { m1_o1t0_LANE_x[45:44], (m1_o1t0_LANE_x[45:44] == 2'd0 && m1_o1t0_LANE_x[26:0] == 0) ? (((m1_xa[LANE][45:44] == 2'd0 && m1_xa[LANE][26:0] == 0) && (m1_xb[LANE][45:44] == 2'd0 && m1_xb[LANE][26:0] == 0)) ? ((rnd == 3'd2) ? (m1_aLANE[15] | (m1_bLANE[15] ^ 1'b1)) : (m1_aLANE[15] & (m1_bLANE[15] ^ 1'b1))) : ((rnd == 3'd2) ? 1'b1 : 1'b0)) : m1_o1t0_LANE_x[43], m1_o1t0_LANE_x[42:0] };
        x_m1[LANE*46 +: 46] = m1_o1t0_LANE_z;
      end
      4'd2: begin
        ix_fp_fma_a_m1[((LANE)+0)*46 +: 46] = m1_xa[LANE]; ix_fp_fma_b_m1[((LANE)+0)*46 +: 46] = m1_xb[LANE]; ix_fp_fma_op_m1[((LANE)+0)*3 +: 3] = 3'd2; m1_o2t0_LANE_x = iy_fp_fma_m1[((LANE)+0)*46 +: 46];
        m1_o2t0_LANE_z = { m1_o2t0_LANE_x[45:44], (m1_o2t0_LANE_x[45:44] == 2'd0 && m1_o2t0_LANE_x[26:0] == 0) ? (m1_aLANE[15] ^ m1_bLANE[15]) : m1_o2t0_LANE_x[43], m1_o2t0_LANE_x[42:0] };
        x_m1[LANE*46 +: 46] = m1_o2t0_LANE_z;
      end
      4'd3: begin
        ix_fp_fma_a_m1[((LANE)+0)*46 +: 46] = m1_xa[LANE]; ix_fp_fma_b_m1[((LANE)+0)*46 +: 46] = m1_xb[LANE]; ix_fp_fma_c_m1[((LANE)+0)*46 +: 46] = m1_xc[LANE]; ix_fp_fma_op_m1[((LANE)+0)*3 +: 3] = 3'd3; m1_o3t0_LANE_x = iy_fp_fma_m1[((LANE)+0)*46 +: 46];
        m1_o3t0_LANE_z = { m1_o3t0_LANE_x[45:44], (m1_o3t0_LANE_x[45:44] == 2'd0 && m1_o3t0_LANE_x[26:0] == 0) ? ((((m1_xa[LANE][45:44] == 2'd0 && m1_xa[LANE][26:0] == 0) || (m1_xb[LANE][45:44] == 2'd0 && m1_xb[LANE][26:0] == 0)) && (m1_xc[LANE][45:44] == 2'd0 && m1_xc[LANE][26:0] == 0)) ? ((rnd == 3'd2) ? ((m1_aLANE[15] ^ m1_bLANE[15] ^ 1'b0) | (m1_cLANE[15] ^ 1'b0)) : ((m1_aLANE[15] ^ m1_bLANE[15] ^ 1'b0) & (m1_cLANE[15] ^ 1'b0))) : ((rnd == 3'd2) ? 1'b1 : 1'b0)) : m1_o3t0_LANE_x[43], m1_o3t0_LANE_x[42:0] };
        x_m1[LANE*46 +: 46] = m1_o3t0_LANE_z;
      end
      4'd4: begin
        ix_fp_fma_a_m1[((LANE)+0)*46 +: 46] = m1_xa[LANE]; ix_fp_fma_b_m1[((LANE)+0)*46 +: 46] = m1_xb[LANE]; ix_fp_fma_c_m1[((LANE)+0)*46 +: 46] = m1_xc[LANE]; ix_fp_fma_op_m1[((LANE)+0)*3 +: 3] = 3'd4; m1_o4t0_LANE_x = iy_fp_fma_m1[((LANE)+0)*46 +: 46];
        m1_o4t0_LANE_z = { m1_o4t0_LANE_x[45:44], (m1_o4t0_LANE_x[45:44] == 2'd0 && m1_o4t0_LANE_x[26:0] == 0) ? ((((m1_xa[LANE][45:44] == 2'd0 && m1_xa[LANE][26:0] == 0) || (m1_xb[LANE][45:44] == 2'd0 && m1_xb[LANE][26:0] == 0)) && (m1_xc[LANE][45:44] == 2'd0 && m1_xc[LANE][26:0] == 0)) ? ((rnd == 3'd2) ? ((m1_aLANE[15] ^ m1_bLANE[15] ^ 1'b0) | (m1_cLANE[15] ^ 1'b1)) : ((m1_aLANE[15] ^ m1_bLANE[15] ^ 1'b0) & (m1_cLANE[15] ^ 1'b1))) : ((rnd == 3'd2) ? 1'b1 : 1'b0)) : m1_o4t0_LANE_x[43], m1_o4t0_LANE_x[42:0] };
        x_m1[LANE*46 +: 46] = m1_o4t0_LANE_z;
      end
      4'd5: begin
        ix_fp_fma_a_m1[((LANE)+0)*46 +: 46] = m1_xa[LANE]; ix_fp_fma_b_m1[((LANE)+0)*46 +: 46] = m1_xb[LANE]; ix_fp_fma_c_m1[((LANE)+0)*46 +: 46] = m1_xc[LANE]; ix_fp_fma_op_m1[((LANE)+0)*3 +: 3] = 3'd5; m1_o5t0_LANE_x = iy_fp_fma_m1[((LANE)+0)*46 +: 46];
        m1_o5t0_LANE_z = { m1_o5t0_LANE_x[45:44], (m1_o5t0_LANE_x[45:44] == 2'd0 && m1_o5t0_LANE_x[26:0] == 0) ? ((((m1_xa[LANE][45:44] == 2'd0 && m1_xa[LANE][26:0] == 0) || (m1_xb[LANE][45:44] == 2'd0 && m1_xb[LANE][26:0] == 0)) && (m1_xc[LANE][45:44] == 2'd0 && m1_xc[LANE][26:0] == 0)) ? ((rnd == 3'd2) ? ((m1_aLANE[15] ^ m1_bLANE[15] ^ 1'b1) | (m1_cLANE[15] ^ 1'b0)) : ((m1_aLANE[15] ^ m1_bLANE[15] ^ 1'b1) & (m1_cLANE[15] ^ 1'b0))) : ((rnd == 3'd2) ? 1'b1 : 1'b0)) : m1_o5t0_LANE_x[43], m1_o5t0_LANE_x[42:0] };
        x_m1[LANE*46 +: 46] = m1_o5t0_LANE_z;
      end
      4'd6: begin
        ix_fp_fma_a_m1[((LANE)+0)*46 +: 46] = m1_xa[LANE]; ix_fp_fma_b_m1[((LANE)+0)*46 +: 46] = m1_xb[LANE]; ix_fp_fma_c_m1[((LANE)+0)*46 +: 46] = m1_xc[LANE]; ix_fp_fma_op_m1[((LANE)+0)*3 +: 3] = 3'd6; m1_o6t0_LANE_x = iy_fp_fma_m1[((LANE)+0)*46 +: 46];
        m1_o6t0_LANE_z = { m1_o6t0_LANE_x[45:44], (m1_o6t0_LANE_x[45:44] == 2'd0 && m1_o6t0_LANE_x[26:0] == 0) ? ((((m1_xa[LANE][45:44] == 2'd0 && m1_xa[LANE][26:0] == 0) || (m1_xb[LANE][45:44] == 2'd0 && m1_xb[LANE][26:0] == 0)) && (m1_xc[LANE][45:44] == 2'd0 && m1_xc[LANE][26:0] == 0)) ? ((rnd == 3'd2) ? ((m1_aLANE[15] ^ m1_bLANE[15] ^ 1'b1) | (m1_cLANE[15] ^ 1'b1)) : ((m1_aLANE[15] ^ m1_bLANE[15] ^ 1'b1) & (m1_cLANE[15] ^ 1'b1))) : ((rnd == 3'd2) ? 1'b1 : 1'b0)) : m1_o6t0_LANE_x[43], m1_o6t0_LANE_x[42:0] };
        x_m1[LANE*46 +: 46] = m1_o6t0_LANE_z;
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m1_fp_comparator #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [15:0] c,
  input  logic [3:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m1,
  output logic [9:0] fl_m1,
  input  logic [45:0] xa_m1,
  input  logic [45:0] xb_m1,
  input  logic [45:0] xc_m1,
  input  logic [0:0] dena_m1,
  input  logic [0:0] denb_m1,
  input  logic [0:0] denc_m1
);
  // alu_core_m1_fp_comparator: lane LANE of mode 1 (bf16) for the fp_comparator ops fmin, fmax, fcmp; the result buses are the mode's, with only this lane's bits written
  import alu_core_m1_pkg::*;
  logic d_m1;
  logic [15:0] m1_aLANE;
  logic [15:0] m1_bLANE;
  logic [15:0] m1_cLANE;
  logic [30:0] m1_uaLANE;
  logic [30:0] m1_ubLANE;
  logic [30:0] m1_ucLANE;
  logic [45:0] m1_xa [0:0];
  logic m1_dena [0:0];
  logic [45:0] m1_xb [0:0];
  logic m1_denb [0:0];
  logic [45:0] m1_xc [0:0];
  logic m1_denc [0:0];
  logic [45:0] m1_fc_xaLANE;
  logic [45:0] m1_fc_xbLANE;
  logic m1_fc_ltLANE;
  logic m1_fc_eqLANE;
  assign m1_aLANE = a[(LANE*16) +: 16];
  assign m1_bLANE = b[(LANE*16) +: 16];
  assign m1_cLANE = c[(LANE*16) +: 16];
  // structure core.unpacker.m1: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_bf16_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_bf16_x26e16s11_p9bfe39588414 u_m1_unpack_aLANE (.b(m1_aLANE), .daz(daz), .u(m1_uaLANE));
  // structure core.unpacker.m1: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_bf16_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_bf16_x26e16s11_p9bfe39588414 u_m1_unpack_bLANE (.b(m1_bLANE), .daz(daz), .u(m1_ubLANE));
  // structure core.unpacker.m1: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_bf16_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_bf16_x26e16s11_p9bfe39588414 u_m1_unpack_cLANE (.b(m1_cLANE), .daz(daz), .u(m1_ucLANE));
  assign m1_xa[LANE] = m1_x(m1_uaLANE[29:0]);
  assign m1_dena[LANE] = m1_uaLANE[30];
  assign m1_xb[LANE] = m1_x(m1_ubLANE[29:0]);
  assign m1_denb[LANE] = m1_ubLANE[30];
  assign m1_xc[LANE] = m1_x(m1_ucLANE[29:0]);
  assign m1_denc[LANE] = m1_ucLANE[30];
  // structure core.fp_comparator.m1: family integer_compare_on_bits realized by the library module fam_fp_cmp_integer_compare_on_bits_x26e16s11_pa61fc99a71d5
  fam_fp_cmp_integer_compare_on_bits_x26e16s11_pa61fc99a71d5 u_m1_fcmpLANE (.xa(m1_fc_xaLANE), .xb(m1_fc_xbLANE), .lt(m1_fc_ltLANE), .eq(m1_fc_eqLANE));
  always_comb begin
    y_m1 = '0; d_m1 = '0; fl_m1 = '0;
    m1_fc_xaLANE = 'x; m1_fc_xbLANE = 'x;
    case (op)
      4'd7: begin
        m1_fc_xaLANE = m1_xa[LANE]; m1_fc_xbLANE = m1_xb[LANE];
        y_m1[((LANE*16)+0) +: 16] = ((m1_xa[LANE][45:44] == 2'd1) || (m1_xb[LANE][45:44] == 2'd1)) ? (1'b0 ? ((m1_xa[LANE][45:44] == 2'd1) ? m1_aLANE : m1_bLANE) : 16'd32704) : ((((m1_xa[LANE][45:44] == 2'd0 && m1_xa[LANE][26:0] == 0) && (m1_xb[LANE][45:44] == 2'd0 && m1_xb[LANE][26:0] == 0)) ? (m1_aLANE[15] == 1'b1 || m1_aLANE[15] == m1_bLANE[15]) : (m1_fc_ltLANE || m1_fc_eqLANE)) ? m1_aLANE : m1_bLANE);
        fl_m1[(0+LANE)*10 +: 10] = (((m1_xa[LANE][45:44] == 2'd1) || (m1_xb[LANE][45:44] == 2'd1)) ? (((10'd1 << 9)) | ((((m1_xa[LANE][45:44] == 2'd1) && !m1_aLANE[6]) || ((m1_xb[LANE][45:44] == 2'd1) && !m1_bLANE[6])) ? (10'd1 << 0) : 10'd0) | ((1'b1 || ((m1_xa[LANE][45:44] == 2'd1) && (m1_xb[LANE][45:44] == 2'd1))) ? (10'd1 << 5) : 10'd0)) : 10'd0) | (m1_dena[LANE] | m1_denb[LANE] ? (10'd1 << 6) : 10'd0);
      end
      4'd8: begin
        m1_fc_xaLANE = m1_xa[LANE]; m1_fc_xbLANE = m1_xb[LANE];
        y_m1[((LANE*16)+0) +: 16] = ((m1_xa[LANE][45:44] == 2'd1) || (m1_xb[LANE][45:44] == 2'd1)) ? (1'b0 ? ((m1_xa[LANE][45:44] == 2'd1) ? m1_aLANE : m1_bLANE) : 16'd32704) : ((((m1_xa[LANE][45:44] == 2'd0 && m1_xa[LANE][26:0] == 0) && (m1_xb[LANE][45:44] == 2'd0 && m1_xb[LANE][26:0] == 0)) ? (m1_aLANE[15] == 1'b0 || m1_aLANE[15] == m1_bLANE[15]) : ((!m1_fc_ltLANE && !m1_fc_eqLANE) || m1_fc_eqLANE)) ? m1_aLANE : m1_bLANE);
        fl_m1[(0+LANE)*10 +: 10] = (((m1_xa[LANE][45:44] == 2'd1) || (m1_xb[LANE][45:44] == 2'd1)) ? (((10'd1 << 9)) | ((((m1_xa[LANE][45:44] == 2'd1) && !m1_aLANE[6]) || ((m1_xb[LANE][45:44] == 2'd1) && !m1_bLANE[6])) ? (10'd1 << 0) : 10'd0) | ((1'b1 || ((m1_xa[LANE][45:44] == 2'd1) && (m1_xb[LANE][45:44] == 2'd1))) ? (10'd1 << 5) : 10'd0)) : 10'd0) | (m1_dena[LANE] | m1_denb[LANE] ? (10'd1 << 6) : 10'd0);
      end
      4'd9: begin
        m1_fc_xaLANE = m1_xa[LANE]; m1_fc_xbLANE = m1_xb[LANE];
        y_m1[((LANE*16)+0) +: 16] = ((m1_xa[LANE][45:44] == 2'd1) || (m1_xb[LANE][45:44] == 2'd1)) ? 16'd0 : {{13{1'b0}}, ((!m1_fc_ltLANE && !m1_fc_eqLANE)), (m1_fc_eqLANE), (m1_fc_ltLANE)};
        fl_m1[(0+LANE)*10 +: 10] = ((m1_xa[LANE][45:44] == 2'd1) || (m1_xb[LANE][45:44] == 2'd1) ? (10'd1 << 9) : 10'd0) | ((((m1_xa[LANE][45:44] == 2'd1) && !m1_aLANE[6]) || ((m1_xb[LANE][45:44] == 2'd1) && !m1_bLANE[6])) ? (10'd1 << 0) : 10'd0) | (m1_dena[LANE] | m1_denb[LANE] ? (10'd1 << 6) : 10'd0);
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m1_rounder #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [15:0] c,
  input  logic [3:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m1,
  output logic [9:0] fl_m1,
  input  logic [45:0] xa_m1,
  input  logic [45:0] xb_m1,
  input  logic [45:0] xc_m1,
  input  logic [0:0] dena_m1,
  input  logic [0:0] denb_m1,
  input  logic [0:0] denc_m1,
  input  logic [45:0] x_m1
);
  // alu_core_m1_rounder: lane LANE of mode 1 (bf16) for the rounder ops fadd, fsub, fmul, fmadd, fmsub, fnmsub, fnmadd; the result buses are the mode's, with only this lane's bits written
  import alu_core_m1_pkg::*;
  logic d_m1;
  logic [15:0] m1_aLANE;
  logic [15:0] m1_bLANE;
  logic [15:0] m1_cLANE;
  logic [30:0] m1_uaLANE;
  logic [30:0] m1_ubLANE;
  logic [30:0] m1_ucLANE;
  logic [45:0] m1_xa [0:0];
  logic m1_dena [0:0];
  logic [45:0] m1_xb [0:0];
  logic m1_denb [0:0];
  logic [45:0] m1_xc [0:0];
  logic m1_denc [0:0];
  logic [45:0] m1_rd_xLANE_fadd;
  logic [7:0] m1_rd_wLANE_fadd;
  logic [9:0] m1_rd_flLANE_fadd;
  logic [15:0] m1_rd_bLANE_fadd;
  logic [45:0] m1_rd_xLANE_fmadd;
  logic [7:0] m1_rd_wLANE_fmadd;
  logic [9:0] m1_rd_flLANE_fmadd;
  logic [15:0] m1_rd_bLANE_fmadd;
  logic [45:0] m1_rd_xLANE_fmsub;
  logic [7:0] m1_rd_wLANE_fmsub;
  logic [9:0] m1_rd_flLANE_fmsub;
  logic [15:0] m1_rd_bLANE_fmsub;
  logic [45:0] m1_rd_xLANE_fmul;
  logic [7:0] m1_rd_wLANE_fmul;
  logic [9:0] m1_rd_flLANE_fmul;
  logic [15:0] m1_rd_bLANE_fmul;
  logic [45:0] m1_rd_xLANE_fnmadd;
  logic [7:0] m1_rd_wLANE_fnmadd;
  logic [9:0] m1_rd_flLANE_fnmadd;
  logic [15:0] m1_rd_bLANE_fnmadd;
  logic [45:0] m1_rd_xLANE_fnmsub;
  logic [7:0] m1_rd_wLANE_fnmsub;
  logic [9:0] m1_rd_flLANE_fnmsub;
  logic [15:0] m1_rd_bLANE_fnmsub;
  logic [45:0] m1_rd_xLANE_fsub;
  logic [7:0] m1_rd_wLANE_fsub;
  logic [9:0] m1_rd_flLANE_fsub;
  logic [15:0] m1_rd_bLANE_fsub;
  logic [25:0] m1_o0t0_LANE;
  logic [45:0] m1_o0t0_LANE_x;
  logic [45:0] m1_o0t0_LANE_z;
  logic [25:0] m1_o1t0_LANE;
  logic [45:0] m1_o1t0_LANE_x;
  logic [45:0] m1_o1t0_LANE_z;
  logic [25:0] m1_o2t0_LANE;
  logic [45:0] m1_o2t0_LANE_x;
  logic [45:0] m1_o2t0_LANE_z;
  logic [25:0] m1_o3t0_LANE;
  logic [45:0] m1_o3t0_LANE_x;
  logic [45:0] m1_o3t0_LANE_z;
  logic [25:0] m1_o4t0_LANE;
  logic [45:0] m1_o4t0_LANE_x;
  logic [45:0] m1_o4t0_LANE_z;
  logic [25:0] m1_o5t0_LANE;
  logic [45:0] m1_o5t0_LANE_x;
  logic [45:0] m1_o5t0_LANE_z;
  logic [25:0] m1_o6t0_LANE;
  logic [45:0] m1_o6t0_LANE_x;
  logic [45:0] m1_o6t0_LANE_z;
  assign m1_aLANE = a[(LANE*16) +: 16];
  assign m1_bLANE = b[(LANE*16) +: 16];
  assign m1_cLANE = c[(LANE*16) +: 16];
  // structure core.unpacker.m1: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_bf16_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_bf16_x26e16s11_p9bfe39588414 u_m1_unpack_aLANE (.b(m1_aLANE), .daz(daz), .u(m1_uaLANE));
  // structure core.unpacker.m1: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_bf16_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_bf16_x26e16s11_p9bfe39588414 u_m1_unpack_bLANE (.b(m1_bLANE), .daz(daz), .u(m1_ubLANE));
  // structure core.unpacker.m1: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_bf16_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_bf16_x26e16s11_p9bfe39588414 u_m1_unpack_cLANE (.b(m1_cLANE), .daz(daz), .u(m1_ucLANE));
  assign m1_xa[LANE] = m1_x(m1_uaLANE[29:0]);
  assign m1_dena[LANE] = m1_uaLANE[30];
  assign m1_xb[LANE] = m1_x(m1_ubLANE[29:0]);
  assign m1_denb[LANE] = m1_ubLANE[30];
  assign m1_xc[LANE] = m1_x(m1_ucLANE[29:0]);
  assign m1_denc[LANE] = m1_ucLANE[30];
  // structure core.rounder.m1: family dedicated_per_op realized by the library module fam_fp_round_dedicated_per_op_increment_adder_bf16_x26e16s11_pd77ccc5b5c45_nin (fadd)
  fam_fp_round_dedicated_per_op_increment_adder_bf16_x26e16s11_pd77ccc5b5c45_nin u_m1_roundLANE_fadd (.x(m1_rd_xLANE_fadd), .rnd(rnd), .word(m1_rd_wLANE_fadd), .ftz(ftz), .fl(m1_rd_flLANE_fadd), .bits(m1_rd_bLANE_fadd));
  // structure core.rounder.m1: family dedicated_per_op realized by the library module fam_fp_round_dedicated_per_op_increment_adder_bf16_x26e16s11_pd77ccc5b5c45_nin (fmadd)
  fam_fp_round_dedicated_per_op_increment_adder_bf16_x26e16s11_pd77ccc5b5c45_nin u_m1_roundLANE_fmadd (.x(m1_rd_xLANE_fmadd), .rnd(rnd), .word(m1_rd_wLANE_fmadd), .ftz(ftz), .fl(m1_rd_flLANE_fmadd), .bits(m1_rd_bLANE_fmadd));
  // structure core.rounder.m1: family dedicated_per_op realized by the library module fam_fp_round_dedicated_per_op_increment_adder_bf16_x26e16s11_pd77ccc5b5c45_nin (fmsub)
  fam_fp_round_dedicated_per_op_increment_adder_bf16_x26e16s11_pd77ccc5b5c45_nin u_m1_roundLANE_fmsub (.x(m1_rd_xLANE_fmsub), .rnd(rnd), .word(m1_rd_wLANE_fmsub), .ftz(ftz), .fl(m1_rd_flLANE_fmsub), .bits(m1_rd_bLANE_fmsub));
  // structure core.rounder.m1: family dedicated_per_op realized by the library module fam_fp_round_dedicated_per_op_increment_adder_bf16_x26e16s11_pd77ccc5b5c45_nin (fmul)
  fam_fp_round_dedicated_per_op_increment_adder_bf16_x26e16s11_pd77ccc5b5c45_nin u_m1_roundLANE_fmul (.x(m1_rd_xLANE_fmul), .rnd(rnd), .word(m1_rd_wLANE_fmul), .ftz(ftz), .fl(m1_rd_flLANE_fmul), .bits(m1_rd_bLANE_fmul));
  // structure core.rounder.m1: family dedicated_per_op realized by the library module fam_fp_round_dedicated_per_op_increment_adder_bf16_x26e16s11_pd77ccc5b5c45_nin (fnmadd)
  fam_fp_round_dedicated_per_op_increment_adder_bf16_x26e16s11_pd77ccc5b5c45_nin u_m1_roundLANE_fnmadd (.x(m1_rd_xLANE_fnmadd), .rnd(rnd), .word(m1_rd_wLANE_fnmadd), .ftz(ftz), .fl(m1_rd_flLANE_fnmadd), .bits(m1_rd_bLANE_fnmadd));
  // structure core.rounder.m1: family dedicated_per_op realized by the library module fam_fp_round_dedicated_per_op_increment_adder_bf16_x26e16s11_pd77ccc5b5c45_nin (fnmsub)
  fam_fp_round_dedicated_per_op_increment_adder_bf16_x26e16s11_pd77ccc5b5c45_nin u_m1_roundLANE_fnmsub (.x(m1_rd_xLANE_fnmsub), .rnd(rnd), .word(m1_rd_wLANE_fnmsub), .ftz(ftz), .fl(m1_rd_flLANE_fnmsub), .bits(m1_rd_bLANE_fnmsub));
  // structure core.rounder.m1: family dedicated_per_op realized by the library module fam_fp_round_dedicated_per_op_increment_adder_bf16_x26e16s11_pd77ccc5b5c45_nin (fsub)
  fam_fp_round_dedicated_per_op_increment_adder_bf16_x26e16s11_pd77ccc5b5c45_nin u_m1_roundLANE_fsub (.x(m1_rd_xLANE_fsub), .rnd(rnd), .word(m1_rd_wLANE_fsub), .ftz(ftz), .fl(m1_rd_flLANE_fsub), .bits(m1_rd_bLANE_fsub));
  always_comb begin
    y_m1 = '0; d_m1 = '0; fl_m1 = '0;
    m1_rd_xLANE_fadd = 'x; m1_rd_wLANE_fadd = 'x; m1_rd_xLANE_fmadd = 'x; m1_rd_wLANE_fmadd = 'x; m1_rd_xLANE_fmsub = 'x; m1_rd_wLANE_fmsub = 'x;
    m1_rd_xLANE_fmul = 'x; m1_rd_wLANE_fmul = 'x; m1_rd_xLANE_fnmadd = 'x; m1_rd_wLANE_fnmadd = 'x; m1_rd_xLANE_fnmsub = 'x; m1_rd_wLANE_fnmsub = 'x;
    m1_rd_xLANE_fsub = 'x; m1_rd_wLANE_fsub = 'x; m1_o0t0_LANE = 'x; m1_o0t0_LANE_x = 'x; m1_o0t0_LANE_z = 'x; m1_o1t0_LANE = 'x;
    m1_o1t0_LANE_x = 'x; m1_o1t0_LANE_z = 'x; m1_o2t0_LANE = 'x; m1_o2t0_LANE_x = 'x; m1_o2t0_LANE_z = 'x; m1_o3t0_LANE = 'x;
    m1_o3t0_LANE_x = 'x; m1_o3t0_LANE_z = 'x; m1_o4t0_LANE = 'x; m1_o4t0_LANE_x = 'x; m1_o4t0_LANE_z = 'x; m1_o5t0_LANE = 'x;
    m1_o5t0_LANE_x = 'x; m1_o5t0_LANE_z = 'x; m1_o6t0_LANE = 'x; m1_o6t0_LANE_x = 'x; m1_o6t0_LANE_z = 'x;
    case (op)
      4'd0: begin
        m1_o0t0_LANE_z = x_m1[LANE*46 +: 46];
        m1_rd_xLANE_fadd = m1_o0t0_LANE_z; m1_rd_wLANE_fadd = 8'd0; m1_o0t0_LANE = {m1_rd_flLANE_fadd, m1_rd_bLANE_fadd};
        y_m1[((LANE*16)+0) +: 16] = (m1_o0t0_LANE_z[45:44] == 2'd1) ? (((m1_xa[LANE][45:44] == 2'd1) || (m1_xb[LANE][45:44] == 2'd1)) ? 16'd32704 : 16'd32704) : ((m1_o0t0_LANE_z[45:44] == 2'd0 && m1_o0t0_LANE_z[26:0] == 0) ? {m1_o0t0_LANE_z[43], 15'd0} : m1_o0t0_LANE[15:0]);
        fl_m1[(0+LANE)*10 +: 10] = (((m1_xa[LANE][45:44] == 2'd1) || (m1_xb[LANE][45:44] == 2'd1)) ? (((10'd1 << 5) | (((m1_xa[LANE][45:44] == 2'd1) && !m1_aLANE[6]) || ((m1_xb[LANE][45:44] == 2'd1) && !m1_bLANE[6]) ? (10'd1 << 0) : 10'd0)) | (m1_dena[LANE] | m1_denb[LANE] ? (10'd1 << 6) : 10'd0)) : (m1_o0t0_LANE[25:16] | ((((m1_xa[LANE][45:44] == 2'd1) && !m1_aLANE[6]) || ((m1_xb[LANE][45:44] == 2'd1) && !m1_bLANE[6]) || ((m1_o0t0_LANE_z[45:44] == 2'd1) && !((m1_xa[LANE][45:44] == 2'd1) || (m1_xb[LANE][45:44] == 2'd1)))) ? (10'd1 << 0) : 10'd0) | (m1_dena[LANE] | m1_denb[LANE] ? (10'd1 << 6) : 10'd0)));
      end
      4'd1: begin
        m1_o1t0_LANE_z = x_m1[LANE*46 +: 46];
        m1_rd_xLANE_fsub = m1_o1t0_LANE_z; m1_rd_wLANE_fsub = 8'd0; m1_o1t0_LANE = {m1_rd_flLANE_fsub, m1_rd_bLANE_fsub};
        y_m1[((LANE*16)+0) +: 16] = (m1_o1t0_LANE_z[45:44] == 2'd1) ? (((m1_xa[LANE][45:44] == 2'd1) || (m1_xb[LANE][45:44] == 2'd1)) ? 16'd32704 : 16'd32704) : ((m1_o1t0_LANE_z[45:44] == 2'd0 && m1_o1t0_LANE_z[26:0] == 0) ? {m1_o1t0_LANE_z[43], 15'd0} : m1_o1t0_LANE[15:0]);
        fl_m1[(0+LANE)*10 +: 10] = (((m1_xa[LANE][45:44] == 2'd1) || (m1_xb[LANE][45:44] == 2'd1)) ? (((10'd1 << 5) | (((m1_xa[LANE][45:44] == 2'd1) && !m1_aLANE[6]) || ((m1_xb[LANE][45:44] == 2'd1) && !m1_bLANE[6]) ? (10'd1 << 0) : 10'd0)) | (m1_dena[LANE] | m1_denb[LANE] ? (10'd1 << 6) : 10'd0)) : (m1_o1t0_LANE[25:16] | ((((m1_xa[LANE][45:44] == 2'd1) && !m1_aLANE[6]) || ((m1_xb[LANE][45:44] == 2'd1) && !m1_bLANE[6]) || ((m1_o1t0_LANE_z[45:44] == 2'd1) && !((m1_xa[LANE][45:44] == 2'd1) || (m1_xb[LANE][45:44] == 2'd1)))) ? (10'd1 << 0) : 10'd0) | (m1_dena[LANE] | m1_denb[LANE] ? (10'd1 << 6) : 10'd0)));
      end
      4'd2: begin
        m1_o2t0_LANE_z = x_m1[LANE*46 +: 46];
        m1_rd_xLANE_fmul = m1_o2t0_LANE_z; m1_rd_wLANE_fmul = 8'd0; m1_o2t0_LANE = {m1_rd_flLANE_fmul, m1_rd_bLANE_fmul};
        y_m1[((LANE*16)+0) +: 16] = (m1_o2t0_LANE_z[45:44] == 2'd1) ? (((m1_xa[LANE][45:44] == 2'd1) || (m1_xb[LANE][45:44] == 2'd1)) ? 16'd32704 : 16'd32704) : ((m1_o2t0_LANE_z[45:44] == 2'd0 && m1_o2t0_LANE_z[26:0] == 0) ? {m1_o2t0_LANE_z[43], 15'd0} : m1_o2t0_LANE[15:0]);
        fl_m1[(0+LANE)*10 +: 10] = (((m1_xa[LANE][45:44] == 2'd1) || (m1_xb[LANE][45:44] == 2'd1)) ? (((10'd1 << 5) | (((m1_xa[LANE][45:44] == 2'd1) && !m1_aLANE[6]) || ((m1_xb[LANE][45:44] == 2'd1) && !m1_bLANE[6]) ? (10'd1 << 0) : 10'd0)) | (m1_dena[LANE] | m1_denb[LANE] ? (10'd1 << 6) : 10'd0)) : (m1_o2t0_LANE[25:16] | ((((m1_xa[LANE][45:44] == 2'd1) && !m1_aLANE[6]) || ((m1_xb[LANE][45:44] == 2'd1) && !m1_bLANE[6]) || ((m1_o2t0_LANE_z[45:44] == 2'd1) && !((m1_xa[LANE][45:44] == 2'd1) || (m1_xb[LANE][45:44] == 2'd1)))) ? (10'd1 << 0) : 10'd0) | (m1_dena[LANE] | m1_denb[LANE] ? (10'd1 << 6) : 10'd0)));
      end
      4'd3: begin
        m1_o3t0_LANE_z = x_m1[LANE*46 +: 46];
        m1_rd_xLANE_fmadd = m1_o3t0_LANE_z; m1_rd_wLANE_fmadd = 8'd0; m1_o3t0_LANE = {m1_rd_flLANE_fmadd, m1_rd_bLANE_fmadd};
        y_m1[((LANE*16)+0) +: 16] = (m1_o3t0_LANE_z[45:44] == 2'd1) ? (((m1_xa[LANE][45:44] == 2'd1) || (m1_xb[LANE][45:44] == 2'd1) || (m1_xc[LANE][45:44] == 2'd1)) ? 16'd32704 : 16'd32704) : ((m1_o3t0_LANE_z[45:44] == 2'd0 && m1_o3t0_LANE_z[26:0] == 0) ? {m1_o3t0_LANE_z[43], 15'd0} : m1_o3t0_LANE[15:0]);
        fl_m1[(0+LANE)*10 +: 10] = (((m1_xa[LANE][45:44] == 2'd1) || (m1_xb[LANE][45:44] == 2'd1) || (m1_xc[LANE][45:44] == 2'd1)) ? (((10'd1 << 5) | (((m1_xa[LANE][45:44] == 2'd1) && !m1_aLANE[6]) || ((m1_xb[LANE][45:44] == 2'd1) && !m1_bLANE[6]) || ((m1_xc[LANE][45:44] == 2'd1) && !m1_cLANE[6]) ? (10'd1 << 0) : 10'd0)) | (m1_dena[LANE] | m1_denb[LANE] | m1_denc[LANE] ? (10'd1 << 6) : 10'd0)) : (m1_o3t0_LANE[25:16] | ((((m1_xa[LANE][45:44] == 2'd1) && !m1_aLANE[6]) || ((m1_xb[LANE][45:44] == 2'd1) && !m1_bLANE[6]) || ((m1_xc[LANE][45:44] == 2'd1) && !m1_cLANE[6]) || ((m1_o3t0_LANE_z[45:44] == 2'd1) && !((m1_xa[LANE][45:44] == 2'd1) || (m1_xb[LANE][45:44] == 2'd1) || (m1_xc[LANE][45:44] == 2'd1)))) ? (10'd1 << 0) : 10'd0) | (m1_dena[LANE] | m1_denb[LANE] | m1_denc[LANE] ? (10'd1 << 6) : 10'd0)));
      end
      4'd4: begin
        m1_o4t0_LANE_z = x_m1[LANE*46 +: 46];
        m1_rd_xLANE_fmsub = m1_o4t0_LANE_z; m1_rd_wLANE_fmsub = 8'd0; m1_o4t0_LANE = {m1_rd_flLANE_fmsub, m1_rd_bLANE_fmsub};
        y_m1[((LANE*16)+0) +: 16] = (m1_o4t0_LANE_z[45:44] == 2'd1) ? (((m1_xa[LANE][45:44] == 2'd1) || (m1_xb[LANE][45:44] == 2'd1) || (m1_xc[LANE][45:44] == 2'd1)) ? 16'd32704 : 16'd32704) : ((m1_o4t0_LANE_z[45:44] == 2'd0 && m1_o4t0_LANE_z[26:0] == 0) ? {m1_o4t0_LANE_z[43], 15'd0} : m1_o4t0_LANE[15:0]);
        fl_m1[(0+LANE)*10 +: 10] = (((m1_xa[LANE][45:44] == 2'd1) || (m1_xb[LANE][45:44] == 2'd1) || (m1_xc[LANE][45:44] == 2'd1)) ? (((10'd1 << 5) | (((m1_xa[LANE][45:44] == 2'd1) && !m1_aLANE[6]) || ((m1_xb[LANE][45:44] == 2'd1) && !m1_bLANE[6]) || ((m1_xc[LANE][45:44] == 2'd1) && !m1_cLANE[6]) ? (10'd1 << 0) : 10'd0)) | (m1_dena[LANE] | m1_denb[LANE] | m1_denc[LANE] ? (10'd1 << 6) : 10'd0)) : (m1_o4t0_LANE[25:16] | ((((m1_xa[LANE][45:44] == 2'd1) && !m1_aLANE[6]) || ((m1_xb[LANE][45:44] == 2'd1) && !m1_bLANE[6]) || ((m1_xc[LANE][45:44] == 2'd1) && !m1_cLANE[6]) || ((m1_o4t0_LANE_z[45:44] == 2'd1) && !((m1_xa[LANE][45:44] == 2'd1) || (m1_xb[LANE][45:44] == 2'd1) || (m1_xc[LANE][45:44] == 2'd1)))) ? (10'd1 << 0) : 10'd0) | (m1_dena[LANE] | m1_denb[LANE] | m1_denc[LANE] ? (10'd1 << 6) : 10'd0)));
      end
      4'd5: begin
        m1_o5t0_LANE_z = x_m1[LANE*46 +: 46];
        m1_rd_xLANE_fnmsub = m1_o5t0_LANE_z; m1_rd_wLANE_fnmsub = 8'd0; m1_o5t0_LANE = {m1_rd_flLANE_fnmsub, m1_rd_bLANE_fnmsub};
        y_m1[((LANE*16)+0) +: 16] = (m1_o5t0_LANE_z[45:44] == 2'd1) ? (((m1_xa[LANE][45:44] == 2'd1) || (m1_xb[LANE][45:44] == 2'd1) || (m1_xc[LANE][45:44] == 2'd1)) ? 16'd32704 : 16'd32704) : ((m1_o5t0_LANE_z[45:44] == 2'd0 && m1_o5t0_LANE_z[26:0] == 0) ? {m1_o5t0_LANE_z[43], 15'd0} : m1_o5t0_LANE[15:0]);
        fl_m1[(0+LANE)*10 +: 10] = (((m1_xa[LANE][45:44] == 2'd1) || (m1_xb[LANE][45:44] == 2'd1) || (m1_xc[LANE][45:44] == 2'd1)) ? (((10'd1 << 5) | (((m1_xa[LANE][45:44] == 2'd1) && !m1_aLANE[6]) || ((m1_xb[LANE][45:44] == 2'd1) && !m1_bLANE[6]) || ((m1_xc[LANE][45:44] == 2'd1) && !m1_cLANE[6]) ? (10'd1 << 0) : 10'd0)) | (m1_dena[LANE] | m1_denb[LANE] | m1_denc[LANE] ? (10'd1 << 6) : 10'd0)) : (m1_o5t0_LANE[25:16] | ((((m1_xa[LANE][45:44] == 2'd1) && !m1_aLANE[6]) || ((m1_xb[LANE][45:44] == 2'd1) && !m1_bLANE[6]) || ((m1_xc[LANE][45:44] == 2'd1) && !m1_cLANE[6]) || ((m1_o5t0_LANE_z[45:44] == 2'd1) && !((m1_xa[LANE][45:44] == 2'd1) || (m1_xb[LANE][45:44] == 2'd1) || (m1_xc[LANE][45:44] == 2'd1)))) ? (10'd1 << 0) : 10'd0) | (m1_dena[LANE] | m1_denb[LANE] | m1_denc[LANE] ? (10'd1 << 6) : 10'd0)));
      end
      4'd6: begin
        m1_o6t0_LANE_z = x_m1[LANE*46 +: 46];
        m1_rd_xLANE_fnmadd = m1_o6t0_LANE_z; m1_rd_wLANE_fnmadd = 8'd0; m1_o6t0_LANE = {m1_rd_flLANE_fnmadd, m1_rd_bLANE_fnmadd};
        y_m1[((LANE*16)+0) +: 16] = (m1_o6t0_LANE_z[45:44] == 2'd1) ? (((m1_xa[LANE][45:44] == 2'd1) || (m1_xb[LANE][45:44] == 2'd1) || (m1_xc[LANE][45:44] == 2'd1)) ? 16'd32704 : 16'd32704) : ((m1_o6t0_LANE_z[45:44] == 2'd0 && m1_o6t0_LANE_z[26:0] == 0) ? {m1_o6t0_LANE_z[43], 15'd0} : m1_o6t0_LANE[15:0]);
        fl_m1[(0+LANE)*10 +: 10] = (((m1_xa[LANE][45:44] == 2'd1) || (m1_xb[LANE][45:44] == 2'd1) || (m1_xc[LANE][45:44] == 2'd1)) ? (((10'd1 << 5) | (((m1_xa[LANE][45:44] == 2'd1) && !m1_aLANE[6]) || ((m1_xb[LANE][45:44] == 2'd1) && !m1_bLANE[6]) || ((m1_xc[LANE][45:44] == 2'd1) && !m1_cLANE[6]) ? (10'd1 << 0) : 10'd0)) | (m1_dena[LANE] | m1_denb[LANE] | m1_denc[LANE] ? (10'd1 << 6) : 10'd0)) : (m1_o6t0_LANE[25:16] | ((((m1_xa[LANE][45:44] == 2'd1) && !m1_aLANE[6]) || ((m1_xb[LANE][45:44] == 2'd1) && !m1_bLANE[6]) || ((m1_xc[LANE][45:44] == 2'd1) && !m1_cLANE[6]) || ((m1_o6t0_LANE_z[45:44] == 2'd1) && !((m1_xa[LANE][45:44] == 2'd1) || (m1_xb[LANE][45:44] == 2'd1) || (m1_xc[LANE][45:44] == 2'd1)))) ? (10'd1 << 0) : 10'd0) | (m1_dena[LANE] | m1_denb[LANE] | m1_denc[LANE] ? (10'd1 << 6) : 10'd0)));
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m1_unpacker #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [15:0] c,
  input  logic [3:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [45:0] xa_m1,
  output logic [45:0] xb_m1,
  output logic [45:0] xc_m1,
  output logic [0:0] dena_m1,
  output logic [0:0] denb_m1,
  output logic [0:0] denc_m1
);
  // alu_core_m1_unpacker: lane LANE of mode 1 (bf16) for the unpacker ops ; the result buses are the mode's, with only this lane's bits written
  import alu_core_m1_pkg::*;
  logic [15:0] y_m1;
  logic d_m1;
  logic [9:0] fl_m1;
  logic [15:0] m1_aLANE;
  logic [15:0] m1_bLANE;
  logic [15:0] m1_cLANE;
  logic [30:0] m1_uaLANE;
  logic [30:0] m1_ubLANE;
  logic [30:0] m1_ucLANE;
  logic [45:0] m1_xa [0:0];
  logic m1_dena [0:0];
  logic [45:0] m1_xb [0:0];
  logic m1_denb [0:0];
  logic [45:0] m1_xc [0:0];
  logic m1_denc [0:0];
  assign m1_aLANE = a[(LANE*16) +: 16];
  assign m1_bLANE = b[(LANE*16) +: 16];
  assign m1_cLANE = c[(LANE*16) +: 16];
  // structure core.unpacker.m1: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_bf16_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_bf16_x26e16s11_p9bfe39588414 u_m1_unpack_aLANE (.b(m1_aLANE), .daz(daz), .u(m1_uaLANE));
  // structure core.unpacker.m1: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_bf16_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_bf16_x26e16s11_p9bfe39588414 u_m1_unpack_bLANE (.b(m1_bLANE), .daz(daz), .u(m1_ubLANE));
  // structure core.unpacker.m1: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_bf16_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_bf16_x26e16s11_p9bfe39588414 u_m1_unpack_cLANE (.b(m1_cLANE), .daz(daz), .u(m1_ucLANE));
  assign m1_xa[LANE] = m1_x(m1_uaLANE[29:0]);
  assign m1_dena[LANE] = m1_uaLANE[30];
  assign m1_xb[LANE] = m1_x(m1_ubLANE[29:0]);
  assign m1_denb[LANE] = m1_ubLANE[30];
  assign m1_xc[LANE] = m1_x(m1_ucLANE[29:0]);
  assign m1_denc[LANE] = m1_ucLANE[30];
  always_comb begin
    xa_m1 = '0; dena_m1 = '0; xb_m1 = '0; denb_m1 = '0; xc_m1 = '0; denc_m1 = '0;
    xa_m1[LANE*46 +: 46] = m1_xa[LANE];
    dena_m1[LANE] = m1_dena[LANE];
    xb_m1[LANE*46 +: 46] = m1_xb[LANE];
    denb_m1[LANE] = m1_denb[LANE];
    xc_m1[LANE*46 +: 46] = m1_xc[LANE];
    denc_m1[LANE] = m1_denc[LANE];
  end
endmodule

module alu_core_m2_fp_adder_fp_fma_fp_multiplier #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [15:0] c,
  input  logic [3:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m2,
  output logic [9:0] fl_m2,
  input  logic [45:0] xa_m2,
  input  logic [45:0] xb_m2,
  input  logic [45:0] xc_m2,
  input  logic [0:0] dena_m2,
  input  logic [0:0] denb_m2,
  input  logic [0:0] denc_m2,
  output logic [45:0] x_m2
);
  // alu_core_m2_fp_adder_fp_fma_fp_multiplier: lane LANE of mode 2 (fp8e5m2) for the fp_adder/fp_fma/fp_multiplier ops fadd, fsub, fmul, fmadd, fmsub, fnmsub, fnmadd; the result buses are the mode's, with only this lane's bits written
  import alu_core_m2_pkg::*;
  logic d_m2;
  logic [7:0] m2_aLANE;
  logic [7:0] m2_bLANE;
  logic [7:0] m2_cLANE;
  logic [30:0] m2_uaLANE;
  logic [30:0] m2_ubLANE;
  logic [30:0] m2_ucLANE;
  logic [45:0] m2_xa [0:0];
  logic m2_dena [0:0];
  logic [45:0] m2_xb [0:0];
  logic m2_denb [0:0];
  logic [45:0] m2_xc [0:0];
  logic m2_denc [0:0];
  logic [45:0] m2_ff_xaLANE;
  logic [45:0] m2_ff_xbLANE;
  logic [45:0] m2_ff_xcLANE;
  logic [2:0] m2_ff_opLANE;
  logic [45:0] m2_ff_yLANE;
  logic [17:0] m2_o0t0_LANE;
  logic [45:0] m2_o0t0_LANE_x;
  logic [45:0] m2_o0t0_LANE_z;
  logic [17:0] m2_o1t0_LANE;
  logic [45:0] m2_o1t0_LANE_x;
  logic [45:0] m2_o1t0_LANE_z;
  logic [17:0] m2_o2t0_LANE;
  logic [45:0] m2_o2t0_LANE_x;
  logic [45:0] m2_o2t0_LANE_z;
  logic [17:0] m2_o3t0_LANE;
  logic [45:0] m2_o3t0_LANE_x;
  logic [45:0] m2_o3t0_LANE_z;
  logic [17:0] m2_o4t0_LANE;
  logic [45:0] m2_o4t0_LANE_x;
  logic [45:0] m2_o4t0_LANE_z;
  logic [17:0] m2_o5t0_LANE;
  logic [45:0] m2_o5t0_LANE_x;
  logic [45:0] m2_o5t0_LANE_z;
  logic [17:0] m2_o6t0_LANE;
  logic [45:0] m2_o6t0_LANE_x;
  logic [45:0] m2_o6t0_LANE_z;
  assign m2_aLANE = a[(LANE*8) +: 8];
  assign m2_bLANE = b[(LANE*8) +: 8];
  assign m2_cLANE = c[(LANE*8) +: 8];
  // structure core.unpacker.m2: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp8e5m2_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp8e5m2_x26e16s11_p9bfe39588414 u_m2_unpack_aLANE (.b(m2_aLANE), .daz(daz), .u(m2_uaLANE));
  // structure core.unpacker.m2: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp8e5m2_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp8e5m2_x26e16s11_p9bfe39588414 u_m2_unpack_bLANE (.b(m2_bLANE), .daz(daz), .u(m2_ubLANE));
  // structure core.unpacker.m2: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp8e5m2_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp8e5m2_x26e16s11_p9bfe39588414 u_m2_unpack_cLANE (.b(m2_cLANE), .daz(daz), .u(m2_ucLANE));
  assign m2_xa[LANE] = m2_x(m2_uaLANE[29:0]);
  assign m2_dena[LANE] = m2_uaLANE[30];
  assign m2_xb[LANE] = m2_x(m2_ubLANE[29:0]);
  assign m2_denb[LANE] = m2_ubLANE[30];
  assign m2_xc[LANE] = m2_x(m2_ucLANE[29:0]);
  assign m2_denc[LANE] = m2_ucLANE[30];
  // structure core.fp_fma.m2: family multipath_fma realized by the library module fam_fp_fma_multipath_fma_x26e16s11_pcac15181ef26; the fadd, fsub and fmul of structures core.fp_adder.m2 and core.fp_multiplier.m2, and the fused multiply-add ops, go through it
  fam_fp_fma_multipath_fma_x26e16s11_pcac15181ef26 u_m2_ffmaLANE (.xa(m2_ff_xaLANE), .xb(m2_ff_xbLANE), .xc(m2_ff_xcLANE), .fop(m2_ff_opLANE), .y(m2_ff_yLANE));
  always_comb begin
    y_m2 = '0; d_m2 = '0; fl_m2 = '0;
    m2_ff_xaLANE = 'x; m2_ff_xbLANE = 'x; m2_ff_xcLANE = 'x; m2_ff_opLANE = 'x; m2_o0t0_LANE = 'x; m2_o0t0_LANE_x = 'x;
    m2_o0t0_LANE_z = 'x; m2_o1t0_LANE = 'x; m2_o1t0_LANE_x = 'x; m2_o1t0_LANE_z = 'x; m2_o2t0_LANE = 'x; m2_o2t0_LANE_x = 'x;
    m2_o2t0_LANE_z = 'x; m2_o3t0_LANE = 'x; m2_o3t0_LANE_x = 'x; m2_o3t0_LANE_z = 'x; m2_o4t0_LANE = 'x; m2_o4t0_LANE_x = 'x;
    m2_o4t0_LANE_z = 'x; m2_o5t0_LANE = 'x; m2_o5t0_LANE_x = 'x; m2_o5t0_LANE_z = 'x; m2_o6t0_LANE = 'x; m2_o6t0_LANE_x = 'x;
    m2_o6t0_LANE_z = 'x;
    x_m2 = '0;
    case (op)
      4'd0: begin
        m2_ff_xaLANE = m2_xa[LANE]; m2_ff_xbLANE = m2_xb[LANE]; m2_ff_opLANE = 3'd0; m2_o0t0_LANE_x = m2_ff_yLANE;
        m2_o0t0_LANE_z = { m2_o0t0_LANE_x[45:44], (m2_o0t0_LANE_x[45:44] == 2'd0 && m2_o0t0_LANE_x[26:0] == 0) ? (((m2_xa[LANE][45:44] == 2'd0 && m2_xa[LANE][26:0] == 0) && (m2_xb[LANE][45:44] == 2'd0 && m2_xb[LANE][26:0] == 0)) ? ((rnd == 3'd2) ? (m2_aLANE[7] | (m2_bLANE[7] ^ 1'b0)) : (m2_aLANE[7] & (m2_bLANE[7] ^ 1'b0))) : ((rnd == 3'd2) ? 1'b1 : 1'b0)) : m2_o0t0_LANE_x[43], m2_o0t0_LANE_x[42:0] };
        x_m2[LANE*46 +: 46] = m2_o0t0_LANE_z;
      end
      4'd1: begin
        m2_ff_xaLANE = m2_xa[LANE]; m2_ff_xbLANE = m2_xb[LANE]; m2_ff_opLANE = 3'd1; m2_o1t0_LANE_x = m2_ff_yLANE;
        m2_o1t0_LANE_z = { m2_o1t0_LANE_x[45:44], (m2_o1t0_LANE_x[45:44] == 2'd0 && m2_o1t0_LANE_x[26:0] == 0) ? (((m2_xa[LANE][45:44] == 2'd0 && m2_xa[LANE][26:0] == 0) && (m2_xb[LANE][45:44] == 2'd0 && m2_xb[LANE][26:0] == 0)) ? ((rnd == 3'd2) ? (m2_aLANE[7] | (m2_bLANE[7] ^ 1'b1)) : (m2_aLANE[7] & (m2_bLANE[7] ^ 1'b1))) : ((rnd == 3'd2) ? 1'b1 : 1'b0)) : m2_o1t0_LANE_x[43], m2_o1t0_LANE_x[42:0] };
        x_m2[LANE*46 +: 46] = m2_o1t0_LANE_z;
      end
      4'd2: begin
        m2_ff_xaLANE = m2_xa[LANE]; m2_ff_xbLANE = m2_xb[LANE]; m2_ff_opLANE = 3'd2; m2_o2t0_LANE_x = m2_ff_yLANE;
        m2_o2t0_LANE_z = { m2_o2t0_LANE_x[45:44], (m2_o2t0_LANE_x[45:44] == 2'd0 && m2_o2t0_LANE_x[26:0] == 0) ? (m2_aLANE[7] ^ m2_bLANE[7]) : m2_o2t0_LANE_x[43], m2_o2t0_LANE_x[42:0] };
        x_m2[LANE*46 +: 46] = m2_o2t0_LANE_z;
      end
      4'd3: begin
        m2_ff_xaLANE = m2_xa[LANE]; m2_ff_xbLANE = m2_xb[LANE]; m2_ff_xcLANE = m2_xc[LANE]; m2_ff_opLANE = 3'd3; m2_o3t0_LANE_x = m2_ff_yLANE;
        m2_o3t0_LANE_z = { m2_o3t0_LANE_x[45:44], (m2_o3t0_LANE_x[45:44] == 2'd0 && m2_o3t0_LANE_x[26:0] == 0) ? ((((m2_xa[LANE][45:44] == 2'd0 && m2_xa[LANE][26:0] == 0) || (m2_xb[LANE][45:44] == 2'd0 && m2_xb[LANE][26:0] == 0)) && (m2_xc[LANE][45:44] == 2'd0 && m2_xc[LANE][26:0] == 0)) ? ((rnd == 3'd2) ? ((m2_aLANE[7] ^ m2_bLANE[7] ^ 1'b0) | (m2_cLANE[7] ^ 1'b0)) : ((m2_aLANE[7] ^ m2_bLANE[7] ^ 1'b0) & (m2_cLANE[7] ^ 1'b0))) : ((rnd == 3'd2) ? 1'b1 : 1'b0)) : m2_o3t0_LANE_x[43], m2_o3t0_LANE_x[42:0] };
        x_m2[LANE*46 +: 46] = m2_o3t0_LANE_z;
      end
      4'd4: begin
        m2_ff_xaLANE = m2_xa[LANE]; m2_ff_xbLANE = m2_xb[LANE]; m2_ff_xcLANE = m2_xc[LANE]; m2_ff_opLANE = 3'd4; m2_o4t0_LANE_x = m2_ff_yLANE;
        m2_o4t0_LANE_z = { m2_o4t0_LANE_x[45:44], (m2_o4t0_LANE_x[45:44] == 2'd0 && m2_o4t0_LANE_x[26:0] == 0) ? ((((m2_xa[LANE][45:44] == 2'd0 && m2_xa[LANE][26:0] == 0) || (m2_xb[LANE][45:44] == 2'd0 && m2_xb[LANE][26:0] == 0)) && (m2_xc[LANE][45:44] == 2'd0 && m2_xc[LANE][26:0] == 0)) ? ((rnd == 3'd2) ? ((m2_aLANE[7] ^ m2_bLANE[7] ^ 1'b0) | (m2_cLANE[7] ^ 1'b1)) : ((m2_aLANE[7] ^ m2_bLANE[7] ^ 1'b0) & (m2_cLANE[7] ^ 1'b1))) : ((rnd == 3'd2) ? 1'b1 : 1'b0)) : m2_o4t0_LANE_x[43], m2_o4t0_LANE_x[42:0] };
        x_m2[LANE*46 +: 46] = m2_o4t0_LANE_z;
      end
      4'd5: begin
        m2_ff_xaLANE = m2_xa[LANE]; m2_ff_xbLANE = m2_xb[LANE]; m2_ff_xcLANE = m2_xc[LANE]; m2_ff_opLANE = 3'd5; m2_o5t0_LANE_x = m2_ff_yLANE;
        m2_o5t0_LANE_z = { m2_o5t0_LANE_x[45:44], (m2_o5t0_LANE_x[45:44] == 2'd0 && m2_o5t0_LANE_x[26:0] == 0) ? ((((m2_xa[LANE][45:44] == 2'd0 && m2_xa[LANE][26:0] == 0) || (m2_xb[LANE][45:44] == 2'd0 && m2_xb[LANE][26:0] == 0)) && (m2_xc[LANE][45:44] == 2'd0 && m2_xc[LANE][26:0] == 0)) ? ((rnd == 3'd2) ? ((m2_aLANE[7] ^ m2_bLANE[7] ^ 1'b1) | (m2_cLANE[7] ^ 1'b0)) : ((m2_aLANE[7] ^ m2_bLANE[7] ^ 1'b1) & (m2_cLANE[7] ^ 1'b0))) : ((rnd == 3'd2) ? 1'b1 : 1'b0)) : m2_o5t0_LANE_x[43], m2_o5t0_LANE_x[42:0] };
        x_m2[LANE*46 +: 46] = m2_o5t0_LANE_z;
      end
      4'd6: begin
        m2_ff_xaLANE = m2_xa[LANE]; m2_ff_xbLANE = m2_xb[LANE]; m2_ff_xcLANE = m2_xc[LANE]; m2_ff_opLANE = 3'd6; m2_o6t0_LANE_x = m2_ff_yLANE;
        m2_o6t0_LANE_z = { m2_o6t0_LANE_x[45:44], (m2_o6t0_LANE_x[45:44] == 2'd0 && m2_o6t0_LANE_x[26:0] == 0) ? ((((m2_xa[LANE][45:44] == 2'd0 && m2_xa[LANE][26:0] == 0) || (m2_xb[LANE][45:44] == 2'd0 && m2_xb[LANE][26:0] == 0)) && (m2_xc[LANE][45:44] == 2'd0 && m2_xc[LANE][26:0] == 0)) ? ((rnd == 3'd2) ? ((m2_aLANE[7] ^ m2_bLANE[7] ^ 1'b1) | (m2_cLANE[7] ^ 1'b1)) : ((m2_aLANE[7] ^ m2_bLANE[7] ^ 1'b1) & (m2_cLANE[7] ^ 1'b1))) : ((rnd == 3'd2) ? 1'b1 : 1'b0)) : m2_o6t0_LANE_x[43], m2_o6t0_LANE_x[42:0] };
        x_m2[LANE*46 +: 46] = m2_o6t0_LANE_z;
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m2_fp_comparator #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [15:0] c,
  input  logic [3:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m2,
  output logic [9:0] fl_m2,
  input  logic [45:0] xa_m2,
  input  logic [45:0] xb_m2,
  input  logic [45:0] xc_m2,
  input  logic [0:0] dena_m2,
  input  logic [0:0] denb_m2,
  input  logic [0:0] denc_m2
);
  // alu_core_m2_fp_comparator: lane LANE of mode 2 (fp8e5m2) for the fp_comparator ops fmin, fmax, fcmp; the result buses are the mode's, with only this lane's bits written
  import alu_core_m2_pkg::*;
  logic d_m2;
  logic [7:0] m2_aLANE;
  logic [7:0] m2_bLANE;
  logic [7:0] m2_cLANE;
  logic [30:0] m2_uaLANE;
  logic [30:0] m2_ubLANE;
  logic [30:0] m2_ucLANE;
  logic [45:0] m2_xa [0:0];
  logic m2_dena [0:0];
  logic [45:0] m2_xb [0:0];
  logic m2_denb [0:0];
  logic [45:0] m2_xc [0:0];
  logic m2_denc [0:0];
  logic [45:0] m2_fc_xaLANE;
  logic [45:0] m2_fc_xbLANE;
  logic m2_fc_ltLANE;
  logic m2_fc_eqLANE;
  assign m2_aLANE = a[(LANE*8) +: 8];
  assign m2_bLANE = b[(LANE*8) +: 8];
  assign m2_cLANE = c[(LANE*8) +: 8];
  // structure core.unpacker.m2: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp8e5m2_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp8e5m2_x26e16s11_p9bfe39588414 u_m2_unpack_aLANE (.b(m2_aLANE), .daz(daz), .u(m2_uaLANE));
  // structure core.unpacker.m2: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp8e5m2_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp8e5m2_x26e16s11_p9bfe39588414 u_m2_unpack_bLANE (.b(m2_bLANE), .daz(daz), .u(m2_ubLANE));
  // structure core.unpacker.m2: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp8e5m2_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp8e5m2_x26e16s11_p9bfe39588414 u_m2_unpack_cLANE (.b(m2_cLANE), .daz(daz), .u(m2_ucLANE));
  assign m2_xa[LANE] = m2_x(m2_uaLANE[29:0]);
  assign m2_dena[LANE] = m2_uaLANE[30];
  assign m2_xb[LANE] = m2_x(m2_ubLANE[29:0]);
  assign m2_denb[LANE] = m2_ubLANE[30];
  assign m2_xc[LANE] = m2_x(m2_ucLANE[29:0]);
  assign m2_denc[LANE] = m2_ucLANE[30];
  // structure core.fp_comparator.m2: family integer_compare_on_bits realized by the library module fam_fp_cmp_integer_compare_on_bits_x26e16s11_pa61fc99a71d5
  fam_fp_cmp_integer_compare_on_bits_x26e16s11_pa61fc99a71d5 u_m2_fcmpLANE (.xa(m2_fc_xaLANE), .xb(m2_fc_xbLANE), .lt(m2_fc_ltLANE), .eq(m2_fc_eqLANE));
  always_comb begin
    y_m2 = '0; d_m2 = '0; fl_m2 = '0;
    m2_fc_xaLANE = 'x; m2_fc_xbLANE = 'x;
    case (op)
      4'd7: begin
        m2_fc_xaLANE = m2_xa[LANE]; m2_fc_xbLANE = m2_xb[LANE];
        y_m2[((LANE*8)+0) +: 8] = ((m2_xa[LANE][45:44] == 2'd1) || (m2_xb[LANE][45:44] == 2'd1)) ? (1'b0 ? ((m2_xa[LANE][45:44] == 2'd1) ? m2_aLANE : m2_bLANE) : 8'd126) : ((((m2_xa[LANE][45:44] == 2'd0 && m2_xa[LANE][26:0] == 0) && (m2_xb[LANE][45:44] == 2'd0 && m2_xb[LANE][26:0] == 0)) ? (m2_aLANE[7] == 1'b1 || m2_aLANE[7] == m2_bLANE[7]) : (m2_fc_ltLANE || m2_fc_eqLANE)) ? m2_aLANE : m2_bLANE);
        fl_m2[(0+LANE)*10 +: 10] = (((m2_xa[LANE][45:44] == 2'd1) || (m2_xb[LANE][45:44] == 2'd1)) ? (((10'd1 << 9)) | ((((m2_xa[LANE][45:44] == 2'd1) && !m2_aLANE[1]) || ((m2_xb[LANE][45:44] == 2'd1) && !m2_bLANE[1])) ? (10'd1 << 0) : 10'd0) | ((1'b1 || ((m2_xa[LANE][45:44] == 2'd1) && (m2_xb[LANE][45:44] == 2'd1))) ? (10'd1 << 5) : 10'd0)) : 10'd0) | (m2_dena[LANE] | m2_denb[LANE] ? (10'd1 << 6) : 10'd0);
      end
      4'd8: begin
        m2_fc_xaLANE = m2_xa[LANE]; m2_fc_xbLANE = m2_xb[LANE];
        y_m2[((LANE*8)+0) +: 8] = ((m2_xa[LANE][45:44] == 2'd1) || (m2_xb[LANE][45:44] == 2'd1)) ? (1'b0 ? ((m2_xa[LANE][45:44] == 2'd1) ? m2_aLANE : m2_bLANE) : 8'd126) : ((((m2_xa[LANE][45:44] == 2'd0 && m2_xa[LANE][26:0] == 0) && (m2_xb[LANE][45:44] == 2'd0 && m2_xb[LANE][26:0] == 0)) ? (m2_aLANE[7] == 1'b0 || m2_aLANE[7] == m2_bLANE[7]) : ((!m2_fc_ltLANE && !m2_fc_eqLANE) || m2_fc_eqLANE)) ? m2_aLANE : m2_bLANE);
        fl_m2[(0+LANE)*10 +: 10] = (((m2_xa[LANE][45:44] == 2'd1) || (m2_xb[LANE][45:44] == 2'd1)) ? (((10'd1 << 9)) | ((((m2_xa[LANE][45:44] == 2'd1) && !m2_aLANE[1]) || ((m2_xb[LANE][45:44] == 2'd1) && !m2_bLANE[1])) ? (10'd1 << 0) : 10'd0) | ((1'b1 || ((m2_xa[LANE][45:44] == 2'd1) && (m2_xb[LANE][45:44] == 2'd1))) ? (10'd1 << 5) : 10'd0)) : 10'd0) | (m2_dena[LANE] | m2_denb[LANE] ? (10'd1 << 6) : 10'd0);
      end
      4'd9: begin
        m2_fc_xaLANE = m2_xa[LANE]; m2_fc_xbLANE = m2_xb[LANE];
        y_m2[((LANE*8)+0) +: 8] = ((m2_xa[LANE][45:44] == 2'd1) || (m2_xb[LANE][45:44] == 2'd1)) ? 8'd0 : {{5{1'b0}}, ((!m2_fc_ltLANE && !m2_fc_eqLANE)), (m2_fc_eqLANE), (m2_fc_ltLANE)};
        fl_m2[(0+LANE)*10 +: 10] = ((m2_xa[LANE][45:44] == 2'd1) || (m2_xb[LANE][45:44] == 2'd1) ? (10'd1 << 9) : 10'd0) | ((((m2_xa[LANE][45:44] == 2'd1) && !m2_aLANE[1]) || ((m2_xb[LANE][45:44] == 2'd1) && !m2_bLANE[1])) ? (10'd1 << 0) : 10'd0) | (m2_dena[LANE] | m2_denb[LANE] ? (10'd1 << 6) : 10'd0);
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m2_rounder #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [15:0] c,
  input  logic [3:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m2,
  output logic [9:0] fl_m2,
  input  logic [45:0] xa_m2,
  input  logic [45:0] xb_m2,
  input  logic [45:0] xc_m2,
  input  logic [0:0] dena_m2,
  input  logic [0:0] denb_m2,
  input  logic [0:0] denc_m2,
  input  logic [45:0] x_m2
);
  // alu_core_m2_rounder: lane LANE of mode 2 (fp8e5m2) for the rounder ops fadd, fsub, fmul, fmadd, fmsub, fnmsub, fnmadd; the result buses are the mode's, with only this lane's bits written
  import alu_core_m2_pkg::*;
  logic d_m2;
  logic [7:0] m2_aLANE;
  logic [7:0] m2_bLANE;
  logic [7:0] m2_cLANE;
  logic [30:0] m2_uaLANE;
  logic [30:0] m2_ubLANE;
  logic [30:0] m2_ucLANE;
  logic [45:0] m2_xa [0:0];
  logic m2_dena [0:0];
  logic [45:0] m2_xb [0:0];
  logic m2_denb [0:0];
  logic [45:0] m2_xc [0:0];
  logic m2_denc [0:0];
  logic [45:0] m2_rd_xLANE_fadd;
  logic [7:0] m2_rd_wLANE_fadd;
  logic [9:0] m2_rd_flLANE_fadd;
  logic [7:0] m2_rd_bLANE_fadd;
  logic [45:0] m2_rd_xLANE_fmadd;
  logic [7:0] m2_rd_wLANE_fmadd;
  logic [9:0] m2_rd_flLANE_fmadd;
  logic [7:0] m2_rd_bLANE_fmadd;
  logic [45:0] m2_rd_xLANE_fmsub;
  logic [7:0] m2_rd_wLANE_fmsub;
  logic [9:0] m2_rd_flLANE_fmsub;
  logic [7:0] m2_rd_bLANE_fmsub;
  logic [45:0] m2_rd_xLANE_fmul;
  logic [7:0] m2_rd_wLANE_fmul;
  logic [9:0] m2_rd_flLANE_fmul;
  logic [7:0] m2_rd_bLANE_fmul;
  logic [45:0] m2_rd_xLANE_fnmadd;
  logic [7:0] m2_rd_wLANE_fnmadd;
  logic [9:0] m2_rd_flLANE_fnmadd;
  logic [7:0] m2_rd_bLANE_fnmadd;
  logic [45:0] m2_rd_xLANE_fnmsub;
  logic [7:0] m2_rd_wLANE_fnmsub;
  logic [9:0] m2_rd_flLANE_fnmsub;
  logic [7:0] m2_rd_bLANE_fnmsub;
  logic [45:0] m2_rd_xLANE_fsub;
  logic [7:0] m2_rd_wLANE_fsub;
  logic [9:0] m2_rd_flLANE_fsub;
  logic [7:0] m2_rd_bLANE_fsub;
  logic [17:0] m2_o0t0_LANE;
  logic [45:0] m2_o0t0_LANE_x;
  logic [45:0] m2_o0t0_LANE_z;
  logic [17:0] m2_o1t0_LANE;
  logic [45:0] m2_o1t0_LANE_x;
  logic [45:0] m2_o1t0_LANE_z;
  logic [17:0] m2_o2t0_LANE;
  logic [45:0] m2_o2t0_LANE_x;
  logic [45:0] m2_o2t0_LANE_z;
  logic [17:0] m2_o3t0_LANE;
  logic [45:0] m2_o3t0_LANE_x;
  logic [45:0] m2_o3t0_LANE_z;
  logic [17:0] m2_o4t0_LANE;
  logic [45:0] m2_o4t0_LANE_x;
  logic [45:0] m2_o4t0_LANE_z;
  logic [17:0] m2_o5t0_LANE;
  logic [45:0] m2_o5t0_LANE_x;
  logic [45:0] m2_o5t0_LANE_z;
  logic [17:0] m2_o6t0_LANE;
  logic [45:0] m2_o6t0_LANE_x;
  logic [45:0] m2_o6t0_LANE_z;
  assign m2_aLANE = a[(LANE*8) +: 8];
  assign m2_bLANE = b[(LANE*8) +: 8];
  assign m2_cLANE = c[(LANE*8) +: 8];
  // structure core.unpacker.m2: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp8e5m2_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp8e5m2_x26e16s11_p9bfe39588414 u_m2_unpack_aLANE (.b(m2_aLANE), .daz(daz), .u(m2_uaLANE));
  // structure core.unpacker.m2: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp8e5m2_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp8e5m2_x26e16s11_p9bfe39588414 u_m2_unpack_bLANE (.b(m2_bLANE), .daz(daz), .u(m2_ubLANE));
  // structure core.unpacker.m2: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp8e5m2_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp8e5m2_x26e16s11_p9bfe39588414 u_m2_unpack_cLANE (.b(m2_cLANE), .daz(daz), .u(m2_ucLANE));
  assign m2_xa[LANE] = m2_x(m2_uaLANE[29:0]);
  assign m2_dena[LANE] = m2_uaLANE[30];
  assign m2_xb[LANE] = m2_x(m2_ubLANE[29:0]);
  assign m2_denb[LANE] = m2_ubLANE[30];
  assign m2_xc[LANE] = m2_x(m2_ucLANE[29:0]);
  assign m2_denc[LANE] = m2_ucLANE[30];
  // structure core.rounder.m2: family dedicated_per_op realized by the library module fam_fp_round_dedicated_per_op_increment_adder_fp8e5m2_x26e16s11_pd77ccc5b5c45_nin (fadd)
  fam_fp_round_dedicated_per_op_increment_adder_fp8e5m2_x26e16s11_pd77ccc5b5c45_nin u_m2_roundLANE_fadd (.x(m2_rd_xLANE_fadd), .rnd(rnd), .word(m2_rd_wLANE_fadd), .ftz(ftz), .fl(m2_rd_flLANE_fadd), .bits(m2_rd_bLANE_fadd));
  // structure core.rounder.m2: family dedicated_per_op realized by the library module fam_fp_round_dedicated_per_op_increment_adder_fp8e5m2_x26e16s11_pd77ccc5b5c45_nin (fmadd)
  fam_fp_round_dedicated_per_op_increment_adder_fp8e5m2_x26e16s11_pd77ccc5b5c45_nin u_m2_roundLANE_fmadd (.x(m2_rd_xLANE_fmadd), .rnd(rnd), .word(m2_rd_wLANE_fmadd), .ftz(ftz), .fl(m2_rd_flLANE_fmadd), .bits(m2_rd_bLANE_fmadd));
  // structure core.rounder.m2: family dedicated_per_op realized by the library module fam_fp_round_dedicated_per_op_increment_adder_fp8e5m2_x26e16s11_pd77ccc5b5c45_nin (fmsub)
  fam_fp_round_dedicated_per_op_increment_adder_fp8e5m2_x26e16s11_pd77ccc5b5c45_nin u_m2_roundLANE_fmsub (.x(m2_rd_xLANE_fmsub), .rnd(rnd), .word(m2_rd_wLANE_fmsub), .ftz(ftz), .fl(m2_rd_flLANE_fmsub), .bits(m2_rd_bLANE_fmsub));
  // structure core.rounder.m2: family dedicated_per_op realized by the library module fam_fp_round_dedicated_per_op_increment_adder_fp8e5m2_x26e16s11_pd77ccc5b5c45_nin (fmul)
  fam_fp_round_dedicated_per_op_increment_adder_fp8e5m2_x26e16s11_pd77ccc5b5c45_nin u_m2_roundLANE_fmul (.x(m2_rd_xLANE_fmul), .rnd(rnd), .word(m2_rd_wLANE_fmul), .ftz(ftz), .fl(m2_rd_flLANE_fmul), .bits(m2_rd_bLANE_fmul));
  // structure core.rounder.m2: family dedicated_per_op realized by the library module fam_fp_round_dedicated_per_op_increment_adder_fp8e5m2_x26e16s11_pd77ccc5b5c45_nin (fnmadd)
  fam_fp_round_dedicated_per_op_increment_adder_fp8e5m2_x26e16s11_pd77ccc5b5c45_nin u_m2_roundLANE_fnmadd (.x(m2_rd_xLANE_fnmadd), .rnd(rnd), .word(m2_rd_wLANE_fnmadd), .ftz(ftz), .fl(m2_rd_flLANE_fnmadd), .bits(m2_rd_bLANE_fnmadd));
  // structure core.rounder.m2: family dedicated_per_op realized by the library module fam_fp_round_dedicated_per_op_increment_adder_fp8e5m2_x26e16s11_pd77ccc5b5c45_nin (fnmsub)
  fam_fp_round_dedicated_per_op_increment_adder_fp8e5m2_x26e16s11_pd77ccc5b5c45_nin u_m2_roundLANE_fnmsub (.x(m2_rd_xLANE_fnmsub), .rnd(rnd), .word(m2_rd_wLANE_fnmsub), .ftz(ftz), .fl(m2_rd_flLANE_fnmsub), .bits(m2_rd_bLANE_fnmsub));
  // structure core.rounder.m2: family dedicated_per_op realized by the library module fam_fp_round_dedicated_per_op_increment_adder_fp8e5m2_x26e16s11_pd77ccc5b5c45_nin (fsub)
  fam_fp_round_dedicated_per_op_increment_adder_fp8e5m2_x26e16s11_pd77ccc5b5c45_nin u_m2_roundLANE_fsub (.x(m2_rd_xLANE_fsub), .rnd(rnd), .word(m2_rd_wLANE_fsub), .ftz(ftz), .fl(m2_rd_flLANE_fsub), .bits(m2_rd_bLANE_fsub));
  always_comb begin
    y_m2 = '0; d_m2 = '0; fl_m2 = '0;
    m2_rd_xLANE_fadd = 'x; m2_rd_wLANE_fadd = 'x; m2_rd_xLANE_fmadd = 'x; m2_rd_wLANE_fmadd = 'x; m2_rd_xLANE_fmsub = 'x; m2_rd_wLANE_fmsub = 'x;
    m2_rd_xLANE_fmul = 'x; m2_rd_wLANE_fmul = 'x; m2_rd_xLANE_fnmadd = 'x; m2_rd_wLANE_fnmadd = 'x; m2_rd_xLANE_fnmsub = 'x; m2_rd_wLANE_fnmsub = 'x;
    m2_rd_xLANE_fsub = 'x; m2_rd_wLANE_fsub = 'x; m2_o0t0_LANE = 'x; m2_o0t0_LANE_x = 'x; m2_o0t0_LANE_z = 'x; m2_o1t0_LANE = 'x;
    m2_o1t0_LANE_x = 'x; m2_o1t0_LANE_z = 'x; m2_o2t0_LANE = 'x; m2_o2t0_LANE_x = 'x; m2_o2t0_LANE_z = 'x; m2_o3t0_LANE = 'x;
    m2_o3t0_LANE_x = 'x; m2_o3t0_LANE_z = 'x; m2_o4t0_LANE = 'x; m2_o4t0_LANE_x = 'x; m2_o4t0_LANE_z = 'x; m2_o5t0_LANE = 'x;
    m2_o5t0_LANE_x = 'x; m2_o5t0_LANE_z = 'x; m2_o6t0_LANE = 'x; m2_o6t0_LANE_x = 'x; m2_o6t0_LANE_z = 'x;
    case (op)
      4'd0: begin
        m2_o0t0_LANE_z = x_m2[LANE*46 +: 46];
        m2_rd_xLANE_fadd = m2_o0t0_LANE_z; m2_rd_wLANE_fadd = 8'd0; m2_o0t0_LANE = {m2_rd_flLANE_fadd, m2_rd_bLANE_fadd};
        y_m2[((LANE*8)+0) +: 8] = (m2_o0t0_LANE_z[45:44] == 2'd1) ? (((m2_xa[LANE][45:44] == 2'd1) || (m2_xb[LANE][45:44] == 2'd1)) ? 8'd126 : 8'd126) : ((m2_o0t0_LANE_z[45:44] == 2'd0 && m2_o0t0_LANE_z[26:0] == 0) ? {m2_o0t0_LANE_z[43], 7'd0} : m2_o0t0_LANE[7:0]);
        fl_m2[(0+LANE)*10 +: 10] = (((m2_xa[LANE][45:44] == 2'd1) || (m2_xb[LANE][45:44] == 2'd1)) ? (((10'd1 << 5) | (((m2_xa[LANE][45:44] == 2'd1) && !m2_aLANE[1]) || ((m2_xb[LANE][45:44] == 2'd1) && !m2_bLANE[1]) ? (10'd1 << 0) : 10'd0)) | (m2_dena[LANE] | m2_denb[LANE] ? (10'd1 << 6) : 10'd0)) : (m2_o0t0_LANE[17:8] | ((((m2_xa[LANE][45:44] == 2'd1) && !m2_aLANE[1]) || ((m2_xb[LANE][45:44] == 2'd1) && !m2_bLANE[1]) || ((m2_o0t0_LANE_z[45:44] == 2'd1) && !((m2_xa[LANE][45:44] == 2'd1) || (m2_xb[LANE][45:44] == 2'd1)))) ? (10'd1 << 0) : 10'd0) | (m2_dena[LANE] | m2_denb[LANE] ? (10'd1 << 6) : 10'd0)));
      end
      4'd1: begin
        m2_o1t0_LANE_z = x_m2[LANE*46 +: 46];
        m2_rd_xLANE_fsub = m2_o1t0_LANE_z; m2_rd_wLANE_fsub = 8'd0; m2_o1t0_LANE = {m2_rd_flLANE_fsub, m2_rd_bLANE_fsub};
        y_m2[((LANE*8)+0) +: 8] = (m2_o1t0_LANE_z[45:44] == 2'd1) ? (((m2_xa[LANE][45:44] == 2'd1) || (m2_xb[LANE][45:44] == 2'd1)) ? 8'd126 : 8'd126) : ((m2_o1t0_LANE_z[45:44] == 2'd0 && m2_o1t0_LANE_z[26:0] == 0) ? {m2_o1t0_LANE_z[43], 7'd0} : m2_o1t0_LANE[7:0]);
        fl_m2[(0+LANE)*10 +: 10] = (((m2_xa[LANE][45:44] == 2'd1) || (m2_xb[LANE][45:44] == 2'd1)) ? (((10'd1 << 5) | (((m2_xa[LANE][45:44] == 2'd1) && !m2_aLANE[1]) || ((m2_xb[LANE][45:44] == 2'd1) && !m2_bLANE[1]) ? (10'd1 << 0) : 10'd0)) | (m2_dena[LANE] | m2_denb[LANE] ? (10'd1 << 6) : 10'd0)) : (m2_o1t0_LANE[17:8] | ((((m2_xa[LANE][45:44] == 2'd1) && !m2_aLANE[1]) || ((m2_xb[LANE][45:44] == 2'd1) && !m2_bLANE[1]) || ((m2_o1t0_LANE_z[45:44] == 2'd1) && !((m2_xa[LANE][45:44] == 2'd1) || (m2_xb[LANE][45:44] == 2'd1)))) ? (10'd1 << 0) : 10'd0) | (m2_dena[LANE] | m2_denb[LANE] ? (10'd1 << 6) : 10'd0)));
      end
      4'd2: begin
        m2_o2t0_LANE_z = x_m2[LANE*46 +: 46];
        m2_rd_xLANE_fmul = m2_o2t0_LANE_z; m2_rd_wLANE_fmul = 8'd0; m2_o2t0_LANE = {m2_rd_flLANE_fmul, m2_rd_bLANE_fmul};
        y_m2[((LANE*8)+0) +: 8] = (m2_o2t0_LANE_z[45:44] == 2'd1) ? (((m2_xa[LANE][45:44] == 2'd1) || (m2_xb[LANE][45:44] == 2'd1)) ? 8'd126 : 8'd126) : ((m2_o2t0_LANE_z[45:44] == 2'd0 && m2_o2t0_LANE_z[26:0] == 0) ? {m2_o2t0_LANE_z[43], 7'd0} : m2_o2t0_LANE[7:0]);
        fl_m2[(0+LANE)*10 +: 10] = (((m2_xa[LANE][45:44] == 2'd1) || (m2_xb[LANE][45:44] == 2'd1)) ? (((10'd1 << 5) | (((m2_xa[LANE][45:44] == 2'd1) && !m2_aLANE[1]) || ((m2_xb[LANE][45:44] == 2'd1) && !m2_bLANE[1]) ? (10'd1 << 0) : 10'd0)) | (m2_dena[LANE] | m2_denb[LANE] ? (10'd1 << 6) : 10'd0)) : (m2_o2t0_LANE[17:8] | ((((m2_xa[LANE][45:44] == 2'd1) && !m2_aLANE[1]) || ((m2_xb[LANE][45:44] == 2'd1) && !m2_bLANE[1]) || ((m2_o2t0_LANE_z[45:44] == 2'd1) && !((m2_xa[LANE][45:44] == 2'd1) || (m2_xb[LANE][45:44] == 2'd1)))) ? (10'd1 << 0) : 10'd0) | (m2_dena[LANE] | m2_denb[LANE] ? (10'd1 << 6) : 10'd0)));
      end
      4'd3: begin
        m2_o3t0_LANE_z = x_m2[LANE*46 +: 46];
        m2_rd_xLANE_fmadd = m2_o3t0_LANE_z; m2_rd_wLANE_fmadd = 8'd0; m2_o3t0_LANE = {m2_rd_flLANE_fmadd, m2_rd_bLANE_fmadd};
        y_m2[((LANE*8)+0) +: 8] = (m2_o3t0_LANE_z[45:44] == 2'd1) ? (((m2_xa[LANE][45:44] == 2'd1) || (m2_xb[LANE][45:44] == 2'd1) || (m2_xc[LANE][45:44] == 2'd1)) ? 8'd126 : 8'd126) : ((m2_o3t0_LANE_z[45:44] == 2'd0 && m2_o3t0_LANE_z[26:0] == 0) ? {m2_o3t0_LANE_z[43], 7'd0} : m2_o3t0_LANE[7:0]);
        fl_m2[(0+LANE)*10 +: 10] = (((m2_xa[LANE][45:44] == 2'd1) || (m2_xb[LANE][45:44] == 2'd1) || (m2_xc[LANE][45:44] == 2'd1)) ? (((10'd1 << 5) | (((m2_xa[LANE][45:44] == 2'd1) && !m2_aLANE[1]) || ((m2_xb[LANE][45:44] == 2'd1) && !m2_bLANE[1]) || ((m2_xc[LANE][45:44] == 2'd1) && !m2_cLANE[1]) ? (10'd1 << 0) : 10'd0)) | (m2_dena[LANE] | m2_denb[LANE] | m2_denc[LANE] ? (10'd1 << 6) : 10'd0)) : (m2_o3t0_LANE[17:8] | ((((m2_xa[LANE][45:44] == 2'd1) && !m2_aLANE[1]) || ((m2_xb[LANE][45:44] == 2'd1) && !m2_bLANE[1]) || ((m2_xc[LANE][45:44] == 2'd1) && !m2_cLANE[1]) || ((m2_o3t0_LANE_z[45:44] == 2'd1) && !((m2_xa[LANE][45:44] == 2'd1) || (m2_xb[LANE][45:44] == 2'd1) || (m2_xc[LANE][45:44] == 2'd1)))) ? (10'd1 << 0) : 10'd0) | (m2_dena[LANE] | m2_denb[LANE] | m2_denc[LANE] ? (10'd1 << 6) : 10'd0)));
      end
      4'd4: begin
        m2_o4t0_LANE_z = x_m2[LANE*46 +: 46];
        m2_rd_xLANE_fmsub = m2_o4t0_LANE_z; m2_rd_wLANE_fmsub = 8'd0; m2_o4t0_LANE = {m2_rd_flLANE_fmsub, m2_rd_bLANE_fmsub};
        y_m2[((LANE*8)+0) +: 8] = (m2_o4t0_LANE_z[45:44] == 2'd1) ? (((m2_xa[LANE][45:44] == 2'd1) || (m2_xb[LANE][45:44] == 2'd1) || (m2_xc[LANE][45:44] == 2'd1)) ? 8'd126 : 8'd126) : ((m2_o4t0_LANE_z[45:44] == 2'd0 && m2_o4t0_LANE_z[26:0] == 0) ? {m2_o4t0_LANE_z[43], 7'd0} : m2_o4t0_LANE[7:0]);
        fl_m2[(0+LANE)*10 +: 10] = (((m2_xa[LANE][45:44] == 2'd1) || (m2_xb[LANE][45:44] == 2'd1) || (m2_xc[LANE][45:44] == 2'd1)) ? (((10'd1 << 5) | (((m2_xa[LANE][45:44] == 2'd1) && !m2_aLANE[1]) || ((m2_xb[LANE][45:44] == 2'd1) && !m2_bLANE[1]) || ((m2_xc[LANE][45:44] == 2'd1) && !m2_cLANE[1]) ? (10'd1 << 0) : 10'd0)) | (m2_dena[LANE] | m2_denb[LANE] | m2_denc[LANE] ? (10'd1 << 6) : 10'd0)) : (m2_o4t0_LANE[17:8] | ((((m2_xa[LANE][45:44] == 2'd1) && !m2_aLANE[1]) || ((m2_xb[LANE][45:44] == 2'd1) && !m2_bLANE[1]) || ((m2_xc[LANE][45:44] == 2'd1) && !m2_cLANE[1]) || ((m2_o4t0_LANE_z[45:44] == 2'd1) && !((m2_xa[LANE][45:44] == 2'd1) || (m2_xb[LANE][45:44] == 2'd1) || (m2_xc[LANE][45:44] == 2'd1)))) ? (10'd1 << 0) : 10'd0) | (m2_dena[LANE] | m2_denb[LANE] | m2_denc[LANE] ? (10'd1 << 6) : 10'd0)));
      end
      4'd5: begin
        m2_o5t0_LANE_z = x_m2[LANE*46 +: 46];
        m2_rd_xLANE_fnmsub = m2_o5t0_LANE_z; m2_rd_wLANE_fnmsub = 8'd0; m2_o5t0_LANE = {m2_rd_flLANE_fnmsub, m2_rd_bLANE_fnmsub};
        y_m2[((LANE*8)+0) +: 8] = (m2_o5t0_LANE_z[45:44] == 2'd1) ? (((m2_xa[LANE][45:44] == 2'd1) || (m2_xb[LANE][45:44] == 2'd1) || (m2_xc[LANE][45:44] == 2'd1)) ? 8'd126 : 8'd126) : ((m2_o5t0_LANE_z[45:44] == 2'd0 && m2_o5t0_LANE_z[26:0] == 0) ? {m2_o5t0_LANE_z[43], 7'd0} : m2_o5t0_LANE[7:0]);
        fl_m2[(0+LANE)*10 +: 10] = (((m2_xa[LANE][45:44] == 2'd1) || (m2_xb[LANE][45:44] == 2'd1) || (m2_xc[LANE][45:44] == 2'd1)) ? (((10'd1 << 5) | (((m2_xa[LANE][45:44] == 2'd1) && !m2_aLANE[1]) || ((m2_xb[LANE][45:44] == 2'd1) && !m2_bLANE[1]) || ((m2_xc[LANE][45:44] == 2'd1) && !m2_cLANE[1]) ? (10'd1 << 0) : 10'd0)) | (m2_dena[LANE] | m2_denb[LANE] | m2_denc[LANE] ? (10'd1 << 6) : 10'd0)) : (m2_o5t0_LANE[17:8] | ((((m2_xa[LANE][45:44] == 2'd1) && !m2_aLANE[1]) || ((m2_xb[LANE][45:44] == 2'd1) && !m2_bLANE[1]) || ((m2_xc[LANE][45:44] == 2'd1) && !m2_cLANE[1]) || ((m2_o5t0_LANE_z[45:44] == 2'd1) && !((m2_xa[LANE][45:44] == 2'd1) || (m2_xb[LANE][45:44] == 2'd1) || (m2_xc[LANE][45:44] == 2'd1)))) ? (10'd1 << 0) : 10'd0) | (m2_dena[LANE] | m2_denb[LANE] | m2_denc[LANE] ? (10'd1 << 6) : 10'd0)));
      end
      4'd6: begin
        m2_o6t0_LANE_z = x_m2[LANE*46 +: 46];
        m2_rd_xLANE_fnmadd = m2_o6t0_LANE_z; m2_rd_wLANE_fnmadd = 8'd0; m2_o6t0_LANE = {m2_rd_flLANE_fnmadd, m2_rd_bLANE_fnmadd};
        y_m2[((LANE*8)+0) +: 8] = (m2_o6t0_LANE_z[45:44] == 2'd1) ? (((m2_xa[LANE][45:44] == 2'd1) || (m2_xb[LANE][45:44] == 2'd1) || (m2_xc[LANE][45:44] == 2'd1)) ? 8'd126 : 8'd126) : ((m2_o6t0_LANE_z[45:44] == 2'd0 && m2_o6t0_LANE_z[26:0] == 0) ? {m2_o6t0_LANE_z[43], 7'd0} : m2_o6t0_LANE[7:0]);
        fl_m2[(0+LANE)*10 +: 10] = (((m2_xa[LANE][45:44] == 2'd1) || (m2_xb[LANE][45:44] == 2'd1) || (m2_xc[LANE][45:44] == 2'd1)) ? (((10'd1 << 5) | (((m2_xa[LANE][45:44] == 2'd1) && !m2_aLANE[1]) || ((m2_xb[LANE][45:44] == 2'd1) && !m2_bLANE[1]) || ((m2_xc[LANE][45:44] == 2'd1) && !m2_cLANE[1]) ? (10'd1 << 0) : 10'd0)) | (m2_dena[LANE] | m2_denb[LANE] | m2_denc[LANE] ? (10'd1 << 6) : 10'd0)) : (m2_o6t0_LANE[17:8] | ((((m2_xa[LANE][45:44] == 2'd1) && !m2_aLANE[1]) || ((m2_xb[LANE][45:44] == 2'd1) && !m2_bLANE[1]) || ((m2_xc[LANE][45:44] == 2'd1) && !m2_cLANE[1]) || ((m2_o6t0_LANE_z[45:44] == 2'd1) && !((m2_xa[LANE][45:44] == 2'd1) || (m2_xb[LANE][45:44] == 2'd1) || (m2_xc[LANE][45:44] == 2'd1)))) ? (10'd1 << 0) : 10'd0) | (m2_dena[LANE] | m2_denb[LANE] | m2_denc[LANE] ? (10'd1 << 6) : 10'd0)));
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m2_unpacker #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [15:0] c,
  input  logic [3:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [45:0] xa_m2,
  output logic [45:0] xb_m2,
  output logic [45:0] xc_m2,
  output logic [0:0] dena_m2,
  output logic [0:0] denb_m2,
  output logic [0:0] denc_m2
);
  // alu_core_m2_unpacker: lane LANE of mode 2 (fp8e5m2) for the unpacker ops ; the result buses are the mode's, with only this lane's bits written
  import alu_core_m2_pkg::*;
  logic [15:0] y_m2;
  logic d_m2;
  logic [9:0] fl_m2;
  logic [7:0] m2_aLANE;
  logic [7:0] m2_bLANE;
  logic [7:0] m2_cLANE;
  logic [30:0] m2_uaLANE;
  logic [30:0] m2_ubLANE;
  logic [30:0] m2_ucLANE;
  logic [45:0] m2_xa [0:0];
  logic m2_dena [0:0];
  logic [45:0] m2_xb [0:0];
  logic m2_denb [0:0];
  logic [45:0] m2_xc [0:0];
  logic m2_denc [0:0];
  assign m2_aLANE = a[(LANE*8) +: 8];
  assign m2_bLANE = b[(LANE*8) +: 8];
  assign m2_cLANE = c[(LANE*8) +: 8];
  // structure core.unpacker.m2: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp8e5m2_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp8e5m2_x26e16s11_p9bfe39588414 u_m2_unpack_aLANE (.b(m2_aLANE), .daz(daz), .u(m2_uaLANE));
  // structure core.unpacker.m2: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp8e5m2_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp8e5m2_x26e16s11_p9bfe39588414 u_m2_unpack_bLANE (.b(m2_bLANE), .daz(daz), .u(m2_ubLANE));
  // structure core.unpacker.m2: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp8e5m2_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp8e5m2_x26e16s11_p9bfe39588414 u_m2_unpack_cLANE (.b(m2_cLANE), .daz(daz), .u(m2_ucLANE));
  assign m2_xa[LANE] = m2_x(m2_uaLANE[29:0]);
  assign m2_dena[LANE] = m2_uaLANE[30];
  assign m2_xb[LANE] = m2_x(m2_ubLANE[29:0]);
  assign m2_denb[LANE] = m2_ubLANE[30];
  assign m2_xc[LANE] = m2_x(m2_ucLANE[29:0]);
  assign m2_denc[LANE] = m2_ucLANE[30];
  always_comb begin
    xa_m2 = '0; dena_m2 = '0; xb_m2 = '0; denb_m2 = '0; xc_m2 = '0; denc_m2 = '0;
    xa_m2[LANE*46 +: 46] = m2_xa[LANE];
    dena_m2[LANE] = m2_dena[LANE];
    xb_m2[LANE*46 +: 46] = m2_xb[LANE];
    denb_m2[LANE] = m2_denb[LANE];
    xc_m2[LANE*46 +: 46] = m2_xc[LANE];
    denc_m2[LANE] = m2_denc[LANE];
  end
endmodule

module alu_core_m3_fp_adder_fp_fma_fp_multiplier #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [15:0] c,
  input  logic [3:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m3,
  output logic [9:0] fl_m3,
  input  logic [45:0] xa_m3,
  input  logic [45:0] xb_m3,
  input  logic [45:0] xc_m3,
  input  logic [0:0] dena_m3,
  input  logic [0:0] denb_m3,
  input  logic [0:0] denc_m3,
  output logic [45:0] x_m3
);
  // alu_core_m3_fp_adder_fp_fma_fp_multiplier: lane LANE of mode 3 (fp8e4m3) for the fp_adder/fp_fma/fp_multiplier ops fadd, fsub, fmul, fmadd, fmsub, fnmsub, fnmadd; the result buses are the mode's, with only this lane's bits written
  import alu_core_m3_pkg::*;
  logic d_m3;
  logic [7:0] m3_aLANE;
  logic [7:0] m3_bLANE;
  logic [7:0] m3_cLANE;
  logic [30:0] m3_uaLANE;
  logic [30:0] m3_ubLANE;
  logic [30:0] m3_ucLANE;
  logic [45:0] m3_xa [0:0];
  logic m3_dena [0:0];
  logic [45:0] m3_xb [0:0];
  logic m3_denb [0:0];
  logic [45:0] m3_xc [0:0];
  logic m3_denc [0:0];
  logic [45:0] m3_ff_xaLANE;
  logic [45:0] m3_ff_xbLANE;
  logic [45:0] m3_ff_xcLANE;
  logic [2:0] m3_ff_opLANE;
  logic [45:0] m3_ff_yLANE;
  logic [17:0] m3_o0t0_LANE;
  logic [45:0] m3_o0t0_LANE_x;
  logic [45:0] m3_o0t0_LANE_z;
  logic [17:0] m3_o1t0_LANE;
  logic [45:0] m3_o1t0_LANE_x;
  logic [45:0] m3_o1t0_LANE_z;
  logic [17:0] m3_o2t0_LANE;
  logic [45:0] m3_o2t0_LANE_x;
  logic [45:0] m3_o2t0_LANE_z;
  logic [17:0] m3_o3t0_LANE;
  logic [45:0] m3_o3t0_LANE_x;
  logic [45:0] m3_o3t0_LANE_z;
  logic [17:0] m3_o4t0_LANE;
  logic [45:0] m3_o4t0_LANE_x;
  logic [45:0] m3_o4t0_LANE_z;
  logic [17:0] m3_o5t0_LANE;
  logic [45:0] m3_o5t0_LANE_x;
  logic [45:0] m3_o5t0_LANE_z;
  logic [17:0] m3_o6t0_LANE;
  logic [45:0] m3_o6t0_LANE_x;
  logic [45:0] m3_o6t0_LANE_z;
  assign m3_aLANE = a[(LANE*8) +: 8];
  assign m3_bLANE = b[(LANE*8) +: 8];
  assign m3_cLANE = c[(LANE*8) +: 8];
  // structure core.unpacker.m3: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp8e4m3_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp8e4m3_x26e16s11_p9bfe39588414 u_m3_unpack_aLANE (.b(m3_aLANE), .daz(daz), .u(m3_uaLANE));
  // structure core.unpacker.m3: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp8e4m3_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp8e4m3_x26e16s11_p9bfe39588414 u_m3_unpack_bLANE (.b(m3_bLANE), .daz(daz), .u(m3_ubLANE));
  // structure core.unpacker.m3: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp8e4m3_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp8e4m3_x26e16s11_p9bfe39588414 u_m3_unpack_cLANE (.b(m3_cLANE), .daz(daz), .u(m3_ucLANE));
  assign m3_xa[LANE] = m3_x(m3_uaLANE[29:0]);
  assign m3_dena[LANE] = m3_uaLANE[30];
  assign m3_xb[LANE] = m3_x(m3_ubLANE[29:0]);
  assign m3_denb[LANE] = m3_ubLANE[30];
  assign m3_xc[LANE] = m3_x(m3_ucLANE[29:0]);
  assign m3_denc[LANE] = m3_ucLANE[30];
  // structure core.fp_fma.m3: family reduced_latency_fma realized by the library module fam_fp_fma_reduced_latency_fma_x26e16s11_pcb92892f976e; the fadd, fsub and fmul of structures core.fp_adder.m3 and core.fp_multiplier.m3, and the fused multiply-add ops, go through it
  fam_fp_fma_reduced_latency_fma_x26e16s11_pcb92892f976e u_m3_ffmaLANE (.xa(m3_ff_xaLANE), .xb(m3_ff_xbLANE), .xc(m3_ff_xcLANE), .fop(m3_ff_opLANE), .rnd(rnd), .y(m3_ff_yLANE));
  always_comb begin
    y_m3 = '0; d_m3 = '0; fl_m3 = '0;
    m3_ff_xaLANE = 'x; m3_ff_xbLANE = 'x; m3_ff_xcLANE = 'x; m3_ff_opLANE = 'x; m3_o0t0_LANE = 'x; m3_o0t0_LANE_x = 'x;
    m3_o0t0_LANE_z = 'x; m3_o1t0_LANE = 'x; m3_o1t0_LANE_x = 'x; m3_o1t0_LANE_z = 'x; m3_o2t0_LANE = 'x; m3_o2t0_LANE_x = 'x;
    m3_o2t0_LANE_z = 'x; m3_o3t0_LANE = 'x; m3_o3t0_LANE_x = 'x; m3_o3t0_LANE_z = 'x; m3_o4t0_LANE = 'x; m3_o4t0_LANE_x = 'x;
    m3_o4t0_LANE_z = 'x; m3_o5t0_LANE = 'x; m3_o5t0_LANE_x = 'x; m3_o5t0_LANE_z = 'x; m3_o6t0_LANE = 'x; m3_o6t0_LANE_x = 'x;
    m3_o6t0_LANE_z = 'x;
    x_m3 = '0;
    case (op)
      4'd0: begin
        m3_ff_xaLANE = m3_xa[LANE]; m3_ff_xbLANE = m3_xb[LANE]; m3_ff_opLANE = 3'd0; m3_o0t0_LANE_x = m3_ff_yLANE;
        m3_o0t0_LANE_z = { m3_o0t0_LANE_x[45:44], (m3_o0t0_LANE_x[45:44] == 2'd0 && m3_o0t0_LANE_x[26:0] == 0) ? (((m3_xa[LANE][45:44] == 2'd0 && m3_xa[LANE][26:0] == 0) && (m3_xb[LANE][45:44] == 2'd0 && m3_xb[LANE][26:0] == 0)) ? ((rnd == 3'd2) ? (m3_aLANE[7] | (m3_bLANE[7] ^ 1'b0)) : (m3_aLANE[7] & (m3_bLANE[7] ^ 1'b0))) : ((rnd == 3'd2) ? 1'b1 : 1'b0)) : m3_o0t0_LANE_x[43], m3_o0t0_LANE_x[42:0] };
        x_m3[LANE*46 +: 46] = m3_o0t0_LANE_z;
      end
      4'd1: begin
        m3_ff_xaLANE = m3_xa[LANE]; m3_ff_xbLANE = m3_xb[LANE]; m3_ff_opLANE = 3'd1; m3_o1t0_LANE_x = m3_ff_yLANE;
        m3_o1t0_LANE_z = { m3_o1t0_LANE_x[45:44], (m3_o1t0_LANE_x[45:44] == 2'd0 && m3_o1t0_LANE_x[26:0] == 0) ? (((m3_xa[LANE][45:44] == 2'd0 && m3_xa[LANE][26:0] == 0) && (m3_xb[LANE][45:44] == 2'd0 && m3_xb[LANE][26:0] == 0)) ? ((rnd == 3'd2) ? (m3_aLANE[7] | (m3_bLANE[7] ^ 1'b1)) : (m3_aLANE[7] & (m3_bLANE[7] ^ 1'b1))) : ((rnd == 3'd2) ? 1'b1 : 1'b0)) : m3_o1t0_LANE_x[43], m3_o1t0_LANE_x[42:0] };
        x_m3[LANE*46 +: 46] = m3_o1t0_LANE_z;
      end
      4'd2: begin
        m3_ff_xaLANE = m3_xa[LANE]; m3_ff_xbLANE = m3_xb[LANE]; m3_ff_opLANE = 3'd2; m3_o2t0_LANE_x = m3_ff_yLANE;
        m3_o2t0_LANE_z = { m3_o2t0_LANE_x[45:44], (m3_o2t0_LANE_x[45:44] == 2'd0 && m3_o2t0_LANE_x[26:0] == 0) ? (m3_aLANE[7] ^ m3_bLANE[7]) : m3_o2t0_LANE_x[43], m3_o2t0_LANE_x[42:0] };
        x_m3[LANE*46 +: 46] = m3_o2t0_LANE_z;
      end
      4'd3: begin
        m3_ff_xaLANE = m3_xa[LANE]; m3_ff_xbLANE = m3_xb[LANE]; m3_ff_xcLANE = m3_xc[LANE]; m3_ff_opLANE = 3'd3; m3_o3t0_LANE_x = m3_ff_yLANE;
        m3_o3t0_LANE_z = { m3_o3t0_LANE_x[45:44], (m3_o3t0_LANE_x[45:44] == 2'd0 && m3_o3t0_LANE_x[26:0] == 0) ? ((((m3_xa[LANE][45:44] == 2'd0 && m3_xa[LANE][26:0] == 0) || (m3_xb[LANE][45:44] == 2'd0 && m3_xb[LANE][26:0] == 0)) && (m3_xc[LANE][45:44] == 2'd0 && m3_xc[LANE][26:0] == 0)) ? ((rnd == 3'd2) ? ((m3_aLANE[7] ^ m3_bLANE[7] ^ 1'b0) | (m3_cLANE[7] ^ 1'b0)) : ((m3_aLANE[7] ^ m3_bLANE[7] ^ 1'b0) & (m3_cLANE[7] ^ 1'b0))) : ((rnd == 3'd2) ? 1'b1 : 1'b0)) : m3_o3t0_LANE_x[43], m3_o3t0_LANE_x[42:0] };
        x_m3[LANE*46 +: 46] = m3_o3t0_LANE_z;
      end
      4'd4: begin
        m3_ff_xaLANE = m3_xa[LANE]; m3_ff_xbLANE = m3_xb[LANE]; m3_ff_xcLANE = m3_xc[LANE]; m3_ff_opLANE = 3'd4; m3_o4t0_LANE_x = m3_ff_yLANE;
        m3_o4t0_LANE_z = { m3_o4t0_LANE_x[45:44], (m3_o4t0_LANE_x[45:44] == 2'd0 && m3_o4t0_LANE_x[26:0] == 0) ? ((((m3_xa[LANE][45:44] == 2'd0 && m3_xa[LANE][26:0] == 0) || (m3_xb[LANE][45:44] == 2'd0 && m3_xb[LANE][26:0] == 0)) && (m3_xc[LANE][45:44] == 2'd0 && m3_xc[LANE][26:0] == 0)) ? ((rnd == 3'd2) ? ((m3_aLANE[7] ^ m3_bLANE[7] ^ 1'b0) | (m3_cLANE[7] ^ 1'b1)) : ((m3_aLANE[7] ^ m3_bLANE[7] ^ 1'b0) & (m3_cLANE[7] ^ 1'b1))) : ((rnd == 3'd2) ? 1'b1 : 1'b0)) : m3_o4t0_LANE_x[43], m3_o4t0_LANE_x[42:0] };
        x_m3[LANE*46 +: 46] = m3_o4t0_LANE_z;
      end
      4'd5: begin
        m3_ff_xaLANE = m3_xa[LANE]; m3_ff_xbLANE = m3_xb[LANE]; m3_ff_xcLANE = m3_xc[LANE]; m3_ff_opLANE = 3'd5; m3_o5t0_LANE_x = m3_ff_yLANE;
        m3_o5t0_LANE_z = { m3_o5t0_LANE_x[45:44], (m3_o5t0_LANE_x[45:44] == 2'd0 && m3_o5t0_LANE_x[26:0] == 0) ? ((((m3_xa[LANE][45:44] == 2'd0 && m3_xa[LANE][26:0] == 0) || (m3_xb[LANE][45:44] == 2'd0 && m3_xb[LANE][26:0] == 0)) && (m3_xc[LANE][45:44] == 2'd0 && m3_xc[LANE][26:0] == 0)) ? ((rnd == 3'd2) ? ((m3_aLANE[7] ^ m3_bLANE[7] ^ 1'b1) | (m3_cLANE[7] ^ 1'b0)) : ((m3_aLANE[7] ^ m3_bLANE[7] ^ 1'b1) & (m3_cLANE[7] ^ 1'b0))) : ((rnd == 3'd2) ? 1'b1 : 1'b0)) : m3_o5t0_LANE_x[43], m3_o5t0_LANE_x[42:0] };
        x_m3[LANE*46 +: 46] = m3_o5t0_LANE_z;
      end
      4'd6: begin
        m3_ff_xaLANE = m3_xa[LANE]; m3_ff_xbLANE = m3_xb[LANE]; m3_ff_xcLANE = m3_xc[LANE]; m3_ff_opLANE = 3'd6; m3_o6t0_LANE_x = m3_ff_yLANE;
        m3_o6t0_LANE_z = { m3_o6t0_LANE_x[45:44], (m3_o6t0_LANE_x[45:44] == 2'd0 && m3_o6t0_LANE_x[26:0] == 0) ? ((((m3_xa[LANE][45:44] == 2'd0 && m3_xa[LANE][26:0] == 0) || (m3_xb[LANE][45:44] == 2'd0 && m3_xb[LANE][26:0] == 0)) && (m3_xc[LANE][45:44] == 2'd0 && m3_xc[LANE][26:0] == 0)) ? ((rnd == 3'd2) ? ((m3_aLANE[7] ^ m3_bLANE[7] ^ 1'b1) | (m3_cLANE[7] ^ 1'b1)) : ((m3_aLANE[7] ^ m3_bLANE[7] ^ 1'b1) & (m3_cLANE[7] ^ 1'b1))) : ((rnd == 3'd2) ? 1'b1 : 1'b0)) : m3_o6t0_LANE_x[43], m3_o6t0_LANE_x[42:0] };
        x_m3[LANE*46 +: 46] = m3_o6t0_LANE_z;
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m3_fp_comparator #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [15:0] c,
  input  logic [3:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m3,
  output logic [9:0] fl_m3,
  input  logic [45:0] xa_m3,
  input  logic [45:0] xb_m3,
  input  logic [45:0] xc_m3,
  input  logic [0:0] dena_m3,
  input  logic [0:0] denb_m3,
  input  logic [0:0] denc_m3
);
  // alu_core_m3_fp_comparator: lane LANE of mode 3 (fp8e4m3) for the fp_comparator ops fmin, fmax, fcmp; the result buses are the mode's, with only this lane's bits written
  import alu_core_m3_pkg::*;
  logic d_m3;
  logic [7:0] m3_aLANE;
  logic [7:0] m3_bLANE;
  logic [7:0] m3_cLANE;
  logic [30:0] m3_uaLANE;
  logic [30:0] m3_ubLANE;
  logic [30:0] m3_ucLANE;
  logic [45:0] m3_xa [0:0];
  logic m3_dena [0:0];
  logic [45:0] m3_xb [0:0];
  logic m3_denb [0:0];
  logic [45:0] m3_xc [0:0];
  logic m3_denc [0:0];
  logic [45:0] m3_fc_xaLANE;
  logic [45:0] m3_fc_xbLANE;
  logic m3_fc_ltLANE;
  logic m3_fc_eqLANE;
  assign m3_aLANE = a[(LANE*8) +: 8];
  assign m3_bLANE = b[(LANE*8) +: 8];
  assign m3_cLANE = c[(LANE*8) +: 8];
  // structure core.unpacker.m3: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp8e4m3_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp8e4m3_x26e16s11_p9bfe39588414 u_m3_unpack_aLANE (.b(m3_aLANE), .daz(daz), .u(m3_uaLANE));
  // structure core.unpacker.m3: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp8e4m3_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp8e4m3_x26e16s11_p9bfe39588414 u_m3_unpack_bLANE (.b(m3_bLANE), .daz(daz), .u(m3_ubLANE));
  // structure core.unpacker.m3: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp8e4m3_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp8e4m3_x26e16s11_p9bfe39588414 u_m3_unpack_cLANE (.b(m3_cLANE), .daz(daz), .u(m3_ucLANE));
  assign m3_xa[LANE] = m3_x(m3_uaLANE[29:0]);
  assign m3_dena[LANE] = m3_uaLANE[30];
  assign m3_xb[LANE] = m3_x(m3_ubLANE[29:0]);
  assign m3_denb[LANE] = m3_ubLANE[30];
  assign m3_xc[LANE] = m3_x(m3_ucLANE[29:0]);
  assign m3_denc[LANE] = m3_ucLANE[30];
  // structure core.fp_comparator.m3: family integer_compare_on_bits realized by the library module fam_fp_cmp_integer_compare_on_bits_x26e16s11_pa61fc99a71d5
  fam_fp_cmp_integer_compare_on_bits_x26e16s11_pa61fc99a71d5 u_m3_fcmpLANE (.xa(m3_fc_xaLANE), .xb(m3_fc_xbLANE), .lt(m3_fc_ltLANE), .eq(m3_fc_eqLANE));
  always_comb begin
    y_m3 = '0; d_m3 = '0; fl_m3 = '0;
    m3_fc_xaLANE = 'x; m3_fc_xbLANE = 'x;
    case (op)
      4'd7: begin
        m3_fc_xaLANE = m3_xa[LANE]; m3_fc_xbLANE = m3_xb[LANE];
        y_m3[((LANE*8)+0) +: 8] = ((m3_xa[LANE][45:44] == 2'd1) || (m3_xb[LANE][45:44] == 2'd1)) ? (1'b0 ? ((m3_xa[LANE][45:44] == 2'd1) ? m3_aLANE : m3_bLANE) : 8'd127) : ((((m3_xa[LANE][45:44] == 2'd0 && m3_xa[LANE][26:0] == 0) && (m3_xb[LANE][45:44] == 2'd0 && m3_xb[LANE][26:0] == 0)) ? (m3_aLANE[7] == 1'b1 || m3_aLANE[7] == m3_bLANE[7]) : (m3_fc_ltLANE || m3_fc_eqLANE)) ? m3_aLANE : m3_bLANE);
        fl_m3[(0+LANE)*10 +: 10] = (((m3_xa[LANE][45:44] == 2'd1) || (m3_xb[LANE][45:44] == 2'd1)) ? (((10'd1 << 9)) | ((1'b0 || 1'b0) ? (10'd1 << 0) : 10'd0) | ((1'b1 || ((m3_xa[LANE][45:44] == 2'd1) && (m3_xb[LANE][45:44] == 2'd1))) ? (10'd1 << 5) : 10'd0)) : 10'd0) | (m3_dena[LANE] | m3_denb[LANE] ? (10'd1 << 6) : 10'd0);
      end
      4'd8: begin
        m3_fc_xaLANE = m3_xa[LANE]; m3_fc_xbLANE = m3_xb[LANE];
        y_m3[((LANE*8)+0) +: 8] = ((m3_xa[LANE][45:44] == 2'd1) || (m3_xb[LANE][45:44] == 2'd1)) ? (1'b0 ? ((m3_xa[LANE][45:44] == 2'd1) ? m3_aLANE : m3_bLANE) : 8'd127) : ((((m3_xa[LANE][45:44] == 2'd0 && m3_xa[LANE][26:0] == 0) && (m3_xb[LANE][45:44] == 2'd0 && m3_xb[LANE][26:0] == 0)) ? (m3_aLANE[7] == 1'b0 || m3_aLANE[7] == m3_bLANE[7]) : ((!m3_fc_ltLANE && !m3_fc_eqLANE) || m3_fc_eqLANE)) ? m3_aLANE : m3_bLANE);
        fl_m3[(0+LANE)*10 +: 10] = (((m3_xa[LANE][45:44] == 2'd1) || (m3_xb[LANE][45:44] == 2'd1)) ? (((10'd1 << 9)) | ((1'b0 || 1'b0) ? (10'd1 << 0) : 10'd0) | ((1'b1 || ((m3_xa[LANE][45:44] == 2'd1) && (m3_xb[LANE][45:44] == 2'd1))) ? (10'd1 << 5) : 10'd0)) : 10'd0) | (m3_dena[LANE] | m3_denb[LANE] ? (10'd1 << 6) : 10'd0);
      end
      4'd9: begin
        m3_fc_xaLANE = m3_xa[LANE]; m3_fc_xbLANE = m3_xb[LANE];
        y_m3[((LANE*8)+0) +: 8] = ((m3_xa[LANE][45:44] == 2'd1) || (m3_xb[LANE][45:44] == 2'd1)) ? 8'd0 : {{5{1'b0}}, ((!m3_fc_ltLANE && !m3_fc_eqLANE)), (m3_fc_eqLANE), (m3_fc_ltLANE)};
        fl_m3[(0+LANE)*10 +: 10] = ((m3_xa[LANE][45:44] == 2'd1) || (m3_xb[LANE][45:44] == 2'd1) ? (10'd1 << 9) : 10'd0) | ((1'b0 || 1'b0) ? (10'd1 << 0) : 10'd0) | (m3_dena[LANE] | m3_denb[LANE] ? (10'd1 << 6) : 10'd0);
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m3_rounder #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [15:0] c,
  input  logic [3:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m3,
  output logic [9:0] fl_m3,
  input  logic [45:0] xa_m3,
  input  logic [45:0] xb_m3,
  input  logic [45:0] xc_m3,
  input  logic [0:0] dena_m3,
  input  logic [0:0] denb_m3,
  input  logic [0:0] denc_m3,
  input  logic [45:0] x_m3
);
  // alu_core_m3_rounder: lane LANE of mode 3 (fp8e4m3) for the rounder ops fadd, fsub, fmul, fmadd, fmsub, fnmsub, fnmadd; the result buses are the mode's, with only this lane's bits written
  import alu_core_m3_pkg::*;
  logic d_m3;
  logic [7:0] m3_aLANE;
  logic [7:0] m3_bLANE;
  logic [7:0] m3_cLANE;
  logic [30:0] m3_uaLANE;
  logic [30:0] m3_ubLANE;
  logic [30:0] m3_ucLANE;
  logic [45:0] m3_xa [0:0];
  logic m3_dena [0:0];
  logic [45:0] m3_xb [0:0];
  logic m3_denb [0:0];
  logic [45:0] m3_xc [0:0];
  logic m3_denc [0:0];
  logic [45:0] m3_rd_xLANE_fadd;
  logic [7:0] m3_rd_wLANE_fadd;
  logic [9:0] m3_rd_flLANE_fadd;
  logic [7:0] m3_rd_bLANE_fadd;
  logic [45:0] m3_rd_xLANE_fmadd;
  logic [7:0] m3_rd_wLANE_fmadd;
  logic [9:0] m3_rd_flLANE_fmadd;
  logic [7:0] m3_rd_bLANE_fmadd;
  logic [45:0] m3_rd_xLANE_fmsub;
  logic [7:0] m3_rd_wLANE_fmsub;
  logic [9:0] m3_rd_flLANE_fmsub;
  logic [7:0] m3_rd_bLANE_fmsub;
  logic [45:0] m3_rd_xLANE_fmul;
  logic [7:0] m3_rd_wLANE_fmul;
  logic [9:0] m3_rd_flLANE_fmul;
  logic [7:0] m3_rd_bLANE_fmul;
  logic [45:0] m3_rd_xLANE_fnmadd;
  logic [7:0] m3_rd_wLANE_fnmadd;
  logic [9:0] m3_rd_flLANE_fnmadd;
  logic [7:0] m3_rd_bLANE_fnmadd;
  logic [45:0] m3_rd_xLANE_fnmsub;
  logic [7:0] m3_rd_wLANE_fnmsub;
  logic [9:0] m3_rd_flLANE_fnmsub;
  logic [7:0] m3_rd_bLANE_fnmsub;
  logic [45:0] m3_rd_xLANE_fsub;
  logic [7:0] m3_rd_wLANE_fsub;
  logic [9:0] m3_rd_flLANE_fsub;
  logic [7:0] m3_rd_bLANE_fsub;
  logic [17:0] m3_o0t0_LANE;
  logic [45:0] m3_o0t0_LANE_x;
  logic [45:0] m3_o0t0_LANE_z;
  logic [17:0] m3_o1t0_LANE;
  logic [45:0] m3_o1t0_LANE_x;
  logic [45:0] m3_o1t0_LANE_z;
  logic [17:0] m3_o2t0_LANE;
  logic [45:0] m3_o2t0_LANE_x;
  logic [45:0] m3_o2t0_LANE_z;
  logic [17:0] m3_o3t0_LANE;
  logic [45:0] m3_o3t0_LANE_x;
  logic [45:0] m3_o3t0_LANE_z;
  logic [17:0] m3_o4t0_LANE;
  logic [45:0] m3_o4t0_LANE_x;
  logic [45:0] m3_o4t0_LANE_z;
  logic [17:0] m3_o5t0_LANE;
  logic [45:0] m3_o5t0_LANE_x;
  logic [45:0] m3_o5t0_LANE_z;
  logic [17:0] m3_o6t0_LANE;
  logic [45:0] m3_o6t0_LANE_x;
  logic [45:0] m3_o6t0_LANE_z;
  assign m3_aLANE = a[(LANE*8) +: 8];
  assign m3_bLANE = b[(LANE*8) +: 8];
  assign m3_cLANE = c[(LANE*8) +: 8];
  // structure core.unpacker.m3: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp8e4m3_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp8e4m3_x26e16s11_p9bfe39588414 u_m3_unpack_aLANE (.b(m3_aLANE), .daz(daz), .u(m3_uaLANE));
  // structure core.unpacker.m3: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp8e4m3_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp8e4m3_x26e16s11_p9bfe39588414 u_m3_unpack_bLANE (.b(m3_bLANE), .daz(daz), .u(m3_ubLANE));
  // structure core.unpacker.m3: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp8e4m3_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp8e4m3_x26e16s11_p9bfe39588414 u_m3_unpack_cLANE (.b(m3_cLANE), .daz(daz), .u(m3_ucLANE));
  assign m3_xa[LANE] = m3_x(m3_uaLANE[29:0]);
  assign m3_dena[LANE] = m3_uaLANE[30];
  assign m3_xb[LANE] = m3_x(m3_ubLANE[29:0]);
  assign m3_denb[LANE] = m3_ubLANE[30];
  assign m3_xc[LANE] = m3_x(m3_ucLANE[29:0]);
  assign m3_denc[LANE] = m3_ucLANE[30];
  // structure core.rounder.m3: family dedicated_per_op realized by the library module fam_fp_round_dedicated_per_op_increment_adder_fp8e4m3_x26e16s11_pd77ccc5b5c45_nin (fadd)
  fam_fp_round_dedicated_per_op_increment_adder_fp8e4m3_x26e16s11_pd77ccc5b5c45_nin u_m3_roundLANE_fadd (.x(m3_rd_xLANE_fadd), .rnd(rnd), .word(m3_rd_wLANE_fadd), .ftz(ftz), .fl(m3_rd_flLANE_fadd), .bits(m3_rd_bLANE_fadd));
  // structure core.rounder.m3: family dedicated_per_op realized by the library module fam_fp_round_dedicated_per_op_increment_adder_fp8e4m3_x26e16s11_pd77ccc5b5c45_nin (fmadd)
  fam_fp_round_dedicated_per_op_increment_adder_fp8e4m3_x26e16s11_pd77ccc5b5c45_nin u_m3_roundLANE_fmadd (.x(m3_rd_xLANE_fmadd), .rnd(rnd), .word(m3_rd_wLANE_fmadd), .ftz(ftz), .fl(m3_rd_flLANE_fmadd), .bits(m3_rd_bLANE_fmadd));
  // structure core.rounder.m3: family dedicated_per_op realized by the library module fam_fp_round_dedicated_per_op_increment_adder_fp8e4m3_x26e16s11_pd77ccc5b5c45_nin (fmsub)
  fam_fp_round_dedicated_per_op_increment_adder_fp8e4m3_x26e16s11_pd77ccc5b5c45_nin u_m3_roundLANE_fmsub (.x(m3_rd_xLANE_fmsub), .rnd(rnd), .word(m3_rd_wLANE_fmsub), .ftz(ftz), .fl(m3_rd_flLANE_fmsub), .bits(m3_rd_bLANE_fmsub));
  // structure core.rounder.m3: family dedicated_per_op realized by the library module fam_fp_round_dedicated_per_op_increment_adder_fp8e4m3_x26e16s11_pd77ccc5b5c45_nin (fmul)
  fam_fp_round_dedicated_per_op_increment_adder_fp8e4m3_x26e16s11_pd77ccc5b5c45_nin u_m3_roundLANE_fmul (.x(m3_rd_xLANE_fmul), .rnd(rnd), .word(m3_rd_wLANE_fmul), .ftz(ftz), .fl(m3_rd_flLANE_fmul), .bits(m3_rd_bLANE_fmul));
  // structure core.rounder.m3: family dedicated_per_op realized by the library module fam_fp_round_dedicated_per_op_increment_adder_fp8e4m3_x26e16s11_pd77ccc5b5c45_nin (fnmadd)
  fam_fp_round_dedicated_per_op_increment_adder_fp8e4m3_x26e16s11_pd77ccc5b5c45_nin u_m3_roundLANE_fnmadd (.x(m3_rd_xLANE_fnmadd), .rnd(rnd), .word(m3_rd_wLANE_fnmadd), .ftz(ftz), .fl(m3_rd_flLANE_fnmadd), .bits(m3_rd_bLANE_fnmadd));
  // structure core.rounder.m3: family dedicated_per_op realized by the library module fam_fp_round_dedicated_per_op_increment_adder_fp8e4m3_x26e16s11_pd77ccc5b5c45_nin (fnmsub)
  fam_fp_round_dedicated_per_op_increment_adder_fp8e4m3_x26e16s11_pd77ccc5b5c45_nin u_m3_roundLANE_fnmsub (.x(m3_rd_xLANE_fnmsub), .rnd(rnd), .word(m3_rd_wLANE_fnmsub), .ftz(ftz), .fl(m3_rd_flLANE_fnmsub), .bits(m3_rd_bLANE_fnmsub));
  // structure core.rounder.m3: family dedicated_per_op realized by the library module fam_fp_round_dedicated_per_op_increment_adder_fp8e4m3_x26e16s11_pd77ccc5b5c45_nin (fsub)
  fam_fp_round_dedicated_per_op_increment_adder_fp8e4m3_x26e16s11_pd77ccc5b5c45_nin u_m3_roundLANE_fsub (.x(m3_rd_xLANE_fsub), .rnd(rnd), .word(m3_rd_wLANE_fsub), .ftz(ftz), .fl(m3_rd_flLANE_fsub), .bits(m3_rd_bLANE_fsub));
  always_comb begin
    y_m3 = '0; d_m3 = '0; fl_m3 = '0;
    m3_rd_xLANE_fadd = 'x; m3_rd_wLANE_fadd = 'x; m3_rd_xLANE_fmadd = 'x; m3_rd_wLANE_fmadd = 'x; m3_rd_xLANE_fmsub = 'x; m3_rd_wLANE_fmsub = 'x;
    m3_rd_xLANE_fmul = 'x; m3_rd_wLANE_fmul = 'x; m3_rd_xLANE_fnmadd = 'x; m3_rd_wLANE_fnmadd = 'x; m3_rd_xLANE_fnmsub = 'x; m3_rd_wLANE_fnmsub = 'x;
    m3_rd_xLANE_fsub = 'x; m3_rd_wLANE_fsub = 'x; m3_o0t0_LANE = 'x; m3_o0t0_LANE_x = 'x; m3_o0t0_LANE_z = 'x; m3_o1t0_LANE = 'x;
    m3_o1t0_LANE_x = 'x; m3_o1t0_LANE_z = 'x; m3_o2t0_LANE = 'x; m3_o2t0_LANE_x = 'x; m3_o2t0_LANE_z = 'x; m3_o3t0_LANE = 'x;
    m3_o3t0_LANE_x = 'x; m3_o3t0_LANE_z = 'x; m3_o4t0_LANE = 'x; m3_o4t0_LANE_x = 'x; m3_o4t0_LANE_z = 'x; m3_o5t0_LANE = 'x;
    m3_o5t0_LANE_x = 'x; m3_o5t0_LANE_z = 'x; m3_o6t0_LANE = 'x; m3_o6t0_LANE_x = 'x; m3_o6t0_LANE_z = 'x;
    case (op)
      4'd0: begin
        m3_o0t0_LANE_z = x_m3[LANE*46 +: 46];
        m3_rd_xLANE_fadd = m3_o0t0_LANE_z; m3_rd_wLANE_fadd = 8'd0; m3_o0t0_LANE = {m3_rd_flLANE_fadd, m3_rd_bLANE_fadd};
        y_m3[((LANE*8)+0) +: 8] = (m3_o0t0_LANE_z[45:44] == 2'd1) ? (((m3_xa[LANE][45:44] == 2'd1) || (m3_xb[LANE][45:44] == 2'd1)) ? 8'd127 : 8'd127) : ((m3_o0t0_LANE_z[45:44] == 2'd0 && m3_o0t0_LANE_z[26:0] == 0) ? {m3_o0t0_LANE_z[43], 7'd0} : m3_o0t0_LANE[7:0]);
        fl_m3[(0+LANE)*10 +: 10] = (((m3_xa[LANE][45:44] == 2'd1) || (m3_xb[LANE][45:44] == 2'd1)) ? (((10'd1 << 5) | (1'b0 || 1'b0 ? (10'd1 << 0) : 10'd0)) | (m3_dena[LANE] | m3_denb[LANE] ? (10'd1 << 6) : 10'd0)) : (m3_o0t0_LANE[17:8] | ((1'b0 || 1'b0 || ((m3_o0t0_LANE_z[45:44] == 2'd1) && !((m3_xa[LANE][45:44] == 2'd1) || (m3_xb[LANE][45:44] == 2'd1)))) ? (10'd1 << 0) : 10'd0) | (m3_dena[LANE] | m3_denb[LANE] ? (10'd1 << 6) : 10'd0)));
      end
      4'd1: begin
        m3_o1t0_LANE_z = x_m3[LANE*46 +: 46];
        m3_rd_xLANE_fsub = m3_o1t0_LANE_z; m3_rd_wLANE_fsub = 8'd0; m3_o1t0_LANE = {m3_rd_flLANE_fsub, m3_rd_bLANE_fsub};
        y_m3[((LANE*8)+0) +: 8] = (m3_o1t0_LANE_z[45:44] == 2'd1) ? (((m3_xa[LANE][45:44] == 2'd1) || (m3_xb[LANE][45:44] == 2'd1)) ? 8'd127 : 8'd127) : ((m3_o1t0_LANE_z[45:44] == 2'd0 && m3_o1t0_LANE_z[26:0] == 0) ? {m3_o1t0_LANE_z[43], 7'd0} : m3_o1t0_LANE[7:0]);
        fl_m3[(0+LANE)*10 +: 10] = (((m3_xa[LANE][45:44] == 2'd1) || (m3_xb[LANE][45:44] == 2'd1)) ? (((10'd1 << 5) | (1'b0 || 1'b0 ? (10'd1 << 0) : 10'd0)) | (m3_dena[LANE] | m3_denb[LANE] ? (10'd1 << 6) : 10'd0)) : (m3_o1t0_LANE[17:8] | ((1'b0 || 1'b0 || ((m3_o1t0_LANE_z[45:44] == 2'd1) && !((m3_xa[LANE][45:44] == 2'd1) || (m3_xb[LANE][45:44] == 2'd1)))) ? (10'd1 << 0) : 10'd0) | (m3_dena[LANE] | m3_denb[LANE] ? (10'd1 << 6) : 10'd0)));
      end
      4'd2: begin
        m3_o2t0_LANE_z = x_m3[LANE*46 +: 46];
        m3_rd_xLANE_fmul = m3_o2t0_LANE_z; m3_rd_wLANE_fmul = 8'd0; m3_o2t0_LANE = {m3_rd_flLANE_fmul, m3_rd_bLANE_fmul};
        y_m3[((LANE*8)+0) +: 8] = (m3_o2t0_LANE_z[45:44] == 2'd1) ? (((m3_xa[LANE][45:44] == 2'd1) || (m3_xb[LANE][45:44] == 2'd1)) ? 8'd127 : 8'd127) : ((m3_o2t0_LANE_z[45:44] == 2'd0 && m3_o2t0_LANE_z[26:0] == 0) ? {m3_o2t0_LANE_z[43], 7'd0} : m3_o2t0_LANE[7:0]);
        fl_m3[(0+LANE)*10 +: 10] = (((m3_xa[LANE][45:44] == 2'd1) || (m3_xb[LANE][45:44] == 2'd1)) ? (((10'd1 << 5) | (1'b0 || 1'b0 ? (10'd1 << 0) : 10'd0)) | (m3_dena[LANE] | m3_denb[LANE] ? (10'd1 << 6) : 10'd0)) : (m3_o2t0_LANE[17:8] | ((1'b0 || 1'b0 || ((m3_o2t0_LANE_z[45:44] == 2'd1) && !((m3_xa[LANE][45:44] == 2'd1) || (m3_xb[LANE][45:44] == 2'd1)))) ? (10'd1 << 0) : 10'd0) | (m3_dena[LANE] | m3_denb[LANE] ? (10'd1 << 6) : 10'd0)));
      end
      4'd3: begin
        m3_o3t0_LANE_z = x_m3[LANE*46 +: 46];
        m3_rd_xLANE_fmadd = m3_o3t0_LANE_z; m3_rd_wLANE_fmadd = 8'd0; m3_o3t0_LANE = {m3_rd_flLANE_fmadd, m3_rd_bLANE_fmadd};
        y_m3[((LANE*8)+0) +: 8] = (m3_o3t0_LANE_z[45:44] == 2'd1) ? (((m3_xa[LANE][45:44] == 2'd1) || (m3_xb[LANE][45:44] == 2'd1) || (m3_xc[LANE][45:44] == 2'd1)) ? 8'd127 : 8'd127) : ((m3_o3t0_LANE_z[45:44] == 2'd0 && m3_o3t0_LANE_z[26:0] == 0) ? {m3_o3t0_LANE_z[43], 7'd0} : m3_o3t0_LANE[7:0]);
        fl_m3[(0+LANE)*10 +: 10] = (((m3_xa[LANE][45:44] == 2'd1) || (m3_xb[LANE][45:44] == 2'd1) || (m3_xc[LANE][45:44] == 2'd1)) ? (((10'd1 << 5) | (1'b0 || 1'b0 || 1'b0 ? (10'd1 << 0) : 10'd0)) | (m3_dena[LANE] | m3_denb[LANE] | m3_denc[LANE] ? (10'd1 << 6) : 10'd0)) : (m3_o3t0_LANE[17:8] | ((1'b0 || 1'b0 || 1'b0 || ((m3_o3t0_LANE_z[45:44] == 2'd1) && !((m3_xa[LANE][45:44] == 2'd1) || (m3_xb[LANE][45:44] == 2'd1) || (m3_xc[LANE][45:44] == 2'd1)))) ? (10'd1 << 0) : 10'd0) | (m3_dena[LANE] | m3_denb[LANE] | m3_denc[LANE] ? (10'd1 << 6) : 10'd0)));
      end
      4'd4: begin
        m3_o4t0_LANE_z = x_m3[LANE*46 +: 46];
        m3_rd_xLANE_fmsub = m3_o4t0_LANE_z; m3_rd_wLANE_fmsub = 8'd0; m3_o4t0_LANE = {m3_rd_flLANE_fmsub, m3_rd_bLANE_fmsub};
        y_m3[((LANE*8)+0) +: 8] = (m3_o4t0_LANE_z[45:44] == 2'd1) ? (((m3_xa[LANE][45:44] == 2'd1) || (m3_xb[LANE][45:44] == 2'd1) || (m3_xc[LANE][45:44] == 2'd1)) ? 8'd127 : 8'd127) : ((m3_o4t0_LANE_z[45:44] == 2'd0 && m3_o4t0_LANE_z[26:0] == 0) ? {m3_o4t0_LANE_z[43], 7'd0} : m3_o4t0_LANE[7:0]);
        fl_m3[(0+LANE)*10 +: 10] = (((m3_xa[LANE][45:44] == 2'd1) || (m3_xb[LANE][45:44] == 2'd1) || (m3_xc[LANE][45:44] == 2'd1)) ? (((10'd1 << 5) | (1'b0 || 1'b0 || 1'b0 ? (10'd1 << 0) : 10'd0)) | (m3_dena[LANE] | m3_denb[LANE] | m3_denc[LANE] ? (10'd1 << 6) : 10'd0)) : (m3_o4t0_LANE[17:8] | ((1'b0 || 1'b0 || 1'b0 || ((m3_o4t0_LANE_z[45:44] == 2'd1) && !((m3_xa[LANE][45:44] == 2'd1) || (m3_xb[LANE][45:44] == 2'd1) || (m3_xc[LANE][45:44] == 2'd1)))) ? (10'd1 << 0) : 10'd0) | (m3_dena[LANE] | m3_denb[LANE] | m3_denc[LANE] ? (10'd1 << 6) : 10'd0)));
      end
      4'd5: begin
        m3_o5t0_LANE_z = x_m3[LANE*46 +: 46];
        m3_rd_xLANE_fnmsub = m3_o5t0_LANE_z; m3_rd_wLANE_fnmsub = 8'd0; m3_o5t0_LANE = {m3_rd_flLANE_fnmsub, m3_rd_bLANE_fnmsub};
        y_m3[((LANE*8)+0) +: 8] = (m3_o5t0_LANE_z[45:44] == 2'd1) ? (((m3_xa[LANE][45:44] == 2'd1) || (m3_xb[LANE][45:44] == 2'd1) || (m3_xc[LANE][45:44] == 2'd1)) ? 8'd127 : 8'd127) : ((m3_o5t0_LANE_z[45:44] == 2'd0 && m3_o5t0_LANE_z[26:0] == 0) ? {m3_o5t0_LANE_z[43], 7'd0} : m3_o5t0_LANE[7:0]);
        fl_m3[(0+LANE)*10 +: 10] = (((m3_xa[LANE][45:44] == 2'd1) || (m3_xb[LANE][45:44] == 2'd1) || (m3_xc[LANE][45:44] == 2'd1)) ? (((10'd1 << 5) | (1'b0 || 1'b0 || 1'b0 ? (10'd1 << 0) : 10'd0)) | (m3_dena[LANE] | m3_denb[LANE] | m3_denc[LANE] ? (10'd1 << 6) : 10'd0)) : (m3_o5t0_LANE[17:8] | ((1'b0 || 1'b0 || 1'b0 || ((m3_o5t0_LANE_z[45:44] == 2'd1) && !((m3_xa[LANE][45:44] == 2'd1) || (m3_xb[LANE][45:44] == 2'd1) || (m3_xc[LANE][45:44] == 2'd1)))) ? (10'd1 << 0) : 10'd0) | (m3_dena[LANE] | m3_denb[LANE] | m3_denc[LANE] ? (10'd1 << 6) : 10'd0)));
      end
      4'd6: begin
        m3_o6t0_LANE_z = x_m3[LANE*46 +: 46];
        m3_rd_xLANE_fnmadd = m3_o6t0_LANE_z; m3_rd_wLANE_fnmadd = 8'd0; m3_o6t0_LANE = {m3_rd_flLANE_fnmadd, m3_rd_bLANE_fnmadd};
        y_m3[((LANE*8)+0) +: 8] = (m3_o6t0_LANE_z[45:44] == 2'd1) ? (((m3_xa[LANE][45:44] == 2'd1) || (m3_xb[LANE][45:44] == 2'd1) || (m3_xc[LANE][45:44] == 2'd1)) ? 8'd127 : 8'd127) : ((m3_o6t0_LANE_z[45:44] == 2'd0 && m3_o6t0_LANE_z[26:0] == 0) ? {m3_o6t0_LANE_z[43], 7'd0} : m3_o6t0_LANE[7:0]);
        fl_m3[(0+LANE)*10 +: 10] = (((m3_xa[LANE][45:44] == 2'd1) || (m3_xb[LANE][45:44] == 2'd1) || (m3_xc[LANE][45:44] == 2'd1)) ? (((10'd1 << 5) | (1'b0 || 1'b0 || 1'b0 ? (10'd1 << 0) : 10'd0)) | (m3_dena[LANE] | m3_denb[LANE] | m3_denc[LANE] ? (10'd1 << 6) : 10'd0)) : (m3_o6t0_LANE[17:8] | ((1'b0 || 1'b0 || 1'b0 || ((m3_o6t0_LANE_z[45:44] == 2'd1) && !((m3_xa[LANE][45:44] == 2'd1) || (m3_xb[LANE][45:44] == 2'd1) || (m3_xc[LANE][45:44] == 2'd1)))) ? (10'd1 << 0) : 10'd0) | (m3_dena[LANE] | m3_denb[LANE] | m3_denc[LANE] ? (10'd1 << 6) : 10'd0)));
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m3_unpacker #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [15:0] c,
  input  logic [3:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [45:0] xa_m3,
  output logic [45:0] xb_m3,
  output logic [45:0] xc_m3,
  output logic [0:0] dena_m3,
  output logic [0:0] denb_m3,
  output logic [0:0] denc_m3
);
  // alu_core_m3_unpacker: lane LANE of mode 3 (fp8e4m3) for the unpacker ops ; the result buses are the mode's, with only this lane's bits written
  import alu_core_m3_pkg::*;
  logic [15:0] y_m3;
  logic d_m3;
  logic [9:0] fl_m3;
  logic [7:0] m3_aLANE;
  logic [7:0] m3_bLANE;
  logic [7:0] m3_cLANE;
  logic [30:0] m3_uaLANE;
  logic [30:0] m3_ubLANE;
  logic [30:0] m3_ucLANE;
  logic [45:0] m3_xa [0:0];
  logic m3_dena [0:0];
  logic [45:0] m3_xb [0:0];
  logic m3_denb [0:0];
  logic [45:0] m3_xc [0:0];
  logic m3_denc [0:0];
  assign m3_aLANE = a[(LANE*8) +: 8];
  assign m3_bLANE = b[(LANE*8) +: 8];
  assign m3_cLANE = c[(LANE*8) +: 8];
  // structure core.unpacker.m3: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp8e4m3_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp8e4m3_x26e16s11_p9bfe39588414 u_m3_unpack_aLANE (.b(m3_aLANE), .daz(daz), .u(m3_uaLANE));
  // structure core.unpacker.m3: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp8e4m3_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp8e4m3_x26e16s11_p9bfe39588414 u_m3_unpack_bLANE (.b(m3_bLANE), .daz(daz), .u(m3_ubLANE));
  // structure core.unpacker.m3: family per_unit_unpack realized by the library module fam_fp_unpack_per_unit_unpack_fp8e4m3_x26e16s11_p9bfe39588414
  fam_fp_unpack_per_unit_unpack_fp8e4m3_x26e16s11_p9bfe39588414 u_m3_unpack_cLANE (.b(m3_cLANE), .daz(daz), .u(m3_ucLANE));
  assign m3_xa[LANE] = m3_x(m3_uaLANE[29:0]);
  assign m3_dena[LANE] = m3_uaLANE[30];
  assign m3_xb[LANE] = m3_x(m3_ubLANE[29:0]);
  assign m3_denb[LANE] = m3_ubLANE[30];
  assign m3_xc[LANE] = m3_x(m3_ucLANE[29:0]);
  assign m3_denc[LANE] = m3_ucLANE[30];
  always_comb begin
    xa_m3 = '0; dena_m3 = '0; xb_m3 = '0; denb_m3 = '0; xc_m3 = '0; denc_m3 = '0;
    xa_m3[LANE*46 +: 46] = m3_xa[LANE];
    dena_m3[LANE] = m3_dena[LANE];
    xb_m3[LANE*46 +: 46] = m3_xb[LANE];
    denb_m3[LANE] = m3_denb[LANE];
    xc_m3[LANE*46 +: 46] = m3_xc[LANE];
    denc_m3[LANE] = m3_denc[LANE];
  end
endmodule
// ADIR-MEMBER m0_l0_fp_adder
// m0.l0.fp_adder: realized by the unit module in member m0_l0_fp_fma
// ADIR-MEMBER m0_l0_unpacker
// EVOLVE-BLOCK-START
module alu_core_u_m0_l0_unpacker (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [15:0] c,
  input  logic [3:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [45:0] xa_m0,
  output logic [45:0] xb_m0,
  output logic [45:0] xc_m0,
  output logic [0:0] dena_m0,
  output logic [0:0] denb_m0,
  output logic [0:0] denc_m0
);
  // alu_core_u_m0_l0_unpacker: physical structure `m0.l0.unpacker` (kind unpacker, slot unpacker); realizes m0.l0.unpacker: unpacker, mode 0 lane 0, fp16, ops fadd, fsub, fmul, fmadd, fmsub, fnmsub, fnmadd, fmin, fmax, fcmp
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [45:0] xa_m0_l0;
  logic [45:0] xb_m0_l0;
  logic [45:0] xc_m0_l0;
  logic dena_m0_l0;
  logic denb_m0_l0;
  logic denc_m0_l0;
  alu_core_m0_unpacker #(.LANE(0)) u_m0_l0 (.a(a), .b(b), .c(c), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .xa_m0(xa_m0_l0), .xb_m0(xb_m0_l0), .xc_m0(xc_m0_l0), .dena_m0(dena_m0_l0), .denb_m0(denb_m0_l0), .denc_m0(denc_m0_l0));
  assign xa_m0 = xa_m0_l0;
  assign xb_m0 = xb_m0_l0;
  assign xc_m0 = xc_m0_l0;
  assign dena_m0 = dena_m0_l0;
  assign denb_m0 = denb_m0_l0;
  assign denc_m0 = denc_m0_l0;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m0_l0_rounder
// EVOLVE-BLOCK-START
module alu_core_u_m0_l0_rounder (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [15:0] c,
  input  logic [3:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m0,
  output logic [9:0] fl_m0,
  input  logic [45:0] xa_m0,
  input  logic [45:0] xb_m0,
  input  logic [45:0] xc_m0,
  input  logic [0:0] dena_m0,
  input  logic [0:0] denb_m0,
  input  logic [0:0] denc_m0,
  input  logic [45:0] x_m0
);
  // alu_core_u_m0_l0_rounder: physical structure `m0.l0.rounder` (kind rounder, slot rounder); realizes m0.l0.rounder: rounder, mode 0 lane 0, fp16, ops fadd, fsub, fmul, fmadd, fmsub, fnmsub, fnmadd
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [15:0] y_m0_l0;
  logic [9:0] fl_m0_l0;
  alu_core_m0_rounder #(.LANE(0)) u_m0_l0 (.a(a), .b(b), .c(c), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_l0), .fl_m0(fl_m0_l0), .xa_m0(xa_m0), .xb_m0(xb_m0), .xc_m0(xc_m0), .dena_m0(dena_m0), .denb_m0(denb_m0), .denc_m0(denc_m0), .x_m0(x_m0));
  assign y_m0 = y_m0_l0;
  assign fl_m0 = fl_m0_l0;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m0_l0_fp_fma
// EVOLVE-BLOCK-START
module alu_core_u_m0_l0_fp_fma (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [15:0] c,
  input  logic [3:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m0,
  output logic [9:0] fl_m0,
  input  logic [45:0] xa_m0,
  input  logic [45:0] xb_m0,
  input  logic [45:0] xc_m0,
  input  logic [0:0] dena_m0,
  input  logic [0:0] denb_m0,
  input  logic [0:0] denc_m0,
  output logic [45:0] x_m0,
  output logic [45:0] ix_fp_fma_a_m0,
  output logic [45:0] ix_fp_fma_b_m0,
  output logic [45:0] ix_fp_fma_c_m0,
  output logic [2:0] ix_fp_fma_op_m0,
  input  logic [45:0] iy_fp_fma_m0
);
  // alu_core_u_m0_l0_fp_fma: physical structure `m0.l0.fp_fma` (kind fp_fma, slot fp_fma); realizes m0.l0.fp_fma: fp_fma, mode 0 lane 0, fp16, ops fadd, fsub, fmul, fmadd, fmsub, fnmsub, fnmadd, m0.l0.fp_multiplier: fp_multiplier, mode 0 lane 0, fp16, ops fmul, fmadd, fmsub, fnmsub, fnmadd, m0.l0.fp_adder: fp_adder, mode 0 lane 0, fp16, ops fadd, fsub, fmadd, fmsub, fnmsub, fnmadd
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [15:0] y_m0_l0;
  logic [9:0] fl_m0_l0;
  logic [45:0] x_m0_l0;
  logic [45:0] ix_fp_fma_a_m0_l0;
  logic [45:0] ix_fp_fma_b_m0_l0;
  logic [45:0] ix_fp_fma_c_m0_l0;
  logic [2:0] ix_fp_fma_op_m0_l0;
  alu_core_m0_fp_adder_fp_fma_fp_multiplier_sh #(.LANE(0)) u_m0_l0 (.a(a), .b(b), .c(c), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_l0), .fl_m0(fl_m0_l0), .xa_m0(xa_m0), .xb_m0(xb_m0), .xc_m0(xc_m0), .dena_m0(dena_m0), .denb_m0(denb_m0), .denc_m0(denc_m0), .x_m0(x_m0_l0), .ix_fp_fma_a_m0(ix_fp_fma_a_m0_l0), .ix_fp_fma_b_m0(ix_fp_fma_b_m0_l0), .ix_fp_fma_c_m0(ix_fp_fma_c_m0_l0), .ix_fp_fma_op_m0(ix_fp_fma_op_m0_l0), .iy_fp_fma_m0(iy_fp_fma_m0));
  assign y_m0 = y_m0_l0;
  assign fl_m0 = fl_m0_l0;
  assign x_m0 = x_m0_l0;
  assign ix_fp_fma_a_m0 = ix_fp_fma_a_m0_l0;
  assign ix_fp_fma_b_m0 = ix_fp_fma_b_m0_l0;
  assign ix_fp_fma_c_m0 = ix_fp_fma_c_m0_l0;
  assign ix_fp_fma_op_m0 = ix_fp_fma_op_m0_l0;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m0_l0_fp_multiplier
// m0.l0.fp_multiplier: realized by the unit module in member m0_l0_fp_fma
// ADIR-MEMBER m0_l0_fp_comparator
// EVOLVE-BLOCK-START
module alu_core_u_m0_l0_fp_comparator (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [15:0] c,
  input  logic [3:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m0,
  output logic [9:0] fl_m0,
  input  logic [45:0] xa_m0,
  input  logic [45:0] xb_m0,
  input  logic [45:0] xc_m0,
  input  logic [0:0] dena_m0,
  input  logic [0:0] denb_m0,
  input  logic [0:0] denc_m0
);
  // alu_core_u_m0_l0_fp_comparator: physical structure `m0.l0.fp_comparator` (kind fp_comparator, slot fp_comparator); realizes m0.l0.fp_comparator: fp_comparator, mode 0 lane 0, fp16, ops fmin, fmax, fcmp
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [15:0] y_m0_l0;
  logic [9:0] fl_m0_l0;
  alu_core_m0_fp_comparator #(.LANE(0)) u_m0_l0 (.a(a), .b(b), .c(c), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_l0), .fl_m0(fl_m0_l0), .xa_m0(xa_m0), .xb_m0(xb_m0), .xc_m0(xc_m0), .dena_m0(dena_m0), .denb_m0(denb_m0), .denc_m0(denc_m0));
  assign y_m0 = y_m0_l0;
  assign fl_m0 = fl_m0_l0;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l0_fp_adder
// m1.l0.fp_adder: realized by the unit module in member m1_l0_fp_fma
// ADIR-MEMBER m1_l0_unpacker
// EVOLVE-BLOCK-START
module alu_core_u_m1_l0_unpacker (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [15:0] c,
  input  logic [3:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [45:0] xa_m1,
  output logic [45:0] xb_m1,
  output logic [45:0] xc_m1,
  output logic [0:0] dena_m1,
  output logic [0:0] denb_m1,
  output logic [0:0] denc_m1
);
  // alu_core_u_m1_l0_unpacker: physical structure `m1.l0.unpacker` (kind unpacker, slot unpacker); realizes m1.l0.unpacker: unpacker, mode 1 lane 0, bf16, ops fadd, fsub, fmul, fmadd, fmsub, fnmsub, fnmadd, fmin, fmax, fcmp
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [45:0] xa_m1_l0;
  logic [45:0] xb_m1_l0;
  logic [45:0] xc_m1_l0;
  logic dena_m1_l0;
  logic denb_m1_l0;
  logic denc_m1_l0;
  alu_core_m1_unpacker #(.LANE(0)) u_m1_l0 (.a(a), .b(b), .c(c), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .xa_m1(xa_m1_l0), .xb_m1(xb_m1_l0), .xc_m1(xc_m1_l0), .dena_m1(dena_m1_l0), .denb_m1(denb_m1_l0), .denc_m1(denc_m1_l0));
  assign xa_m1 = xa_m1_l0;
  assign xb_m1 = xb_m1_l0;
  assign xc_m1 = xc_m1_l0;
  assign dena_m1 = dena_m1_l0;
  assign denb_m1 = denb_m1_l0;
  assign denc_m1 = denc_m1_l0;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l0_rounder
// EVOLVE-BLOCK-START
module alu_core_u_m1_l0_rounder (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [15:0] c,
  input  logic [3:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m1,
  output logic [9:0] fl_m1,
  input  logic [45:0] xa_m1,
  input  logic [45:0] xb_m1,
  input  logic [45:0] xc_m1,
  input  logic [0:0] dena_m1,
  input  logic [0:0] denb_m1,
  input  logic [0:0] denc_m1,
  input  logic [45:0] x_m1
);
  // alu_core_u_m1_l0_rounder: physical structure `m1.l0.rounder` (kind rounder, slot rounder); realizes m1.l0.rounder: rounder, mode 1 lane 0, bf16, ops fadd, fsub, fmul, fmadd, fmsub, fnmsub, fnmadd
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [15:0] y_m1_l0;
  logic [9:0] fl_m1_l0;
  alu_core_m1_rounder #(.LANE(0)) u_m1_l0 (.a(a), .b(b), .c(c), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_l0), .fl_m1(fl_m1_l0), .xa_m1(xa_m1), .xb_m1(xb_m1), .xc_m1(xc_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .denc_m1(denc_m1), .x_m1(x_m1));
  assign y_m1 = y_m1_l0;
  assign fl_m1 = fl_m1_l0;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l0_fp_fma
// EVOLVE-BLOCK-START
module alu_core_u_m1_l0_fp_fma (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [15:0] c,
  input  logic [3:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m1,
  output logic [9:0] fl_m1,
  input  logic [45:0] xa_m1,
  input  logic [45:0] xb_m1,
  input  logic [45:0] xc_m1,
  input  logic [0:0] dena_m1,
  input  logic [0:0] denb_m1,
  input  logic [0:0] denc_m1,
  output logic [45:0] x_m1,
  output logic [45:0] ix_fp_fma_a_m1,
  output logic [45:0] ix_fp_fma_b_m1,
  output logic [45:0] ix_fp_fma_c_m1,
  output logic [2:0] ix_fp_fma_op_m1,
  input  logic [45:0] iy_fp_fma_m1
);
  // alu_core_u_m1_l0_fp_fma: physical structure `m1.l0.fp_fma` (kind fp_fma, slot fp_fma); realizes m1.l0.fp_fma: fp_fma, mode 1 lane 0, bf16, ops fadd, fsub, fmul, fmadd, fmsub, fnmsub, fnmadd, m1.l0.fp_multiplier: fp_multiplier, mode 1 lane 0, bf16, ops fmul, fmadd, fmsub, fnmsub, fnmadd, m1.l0.fp_adder: fp_adder, mode 1 lane 0, bf16, ops fadd, fsub, fmadd, fmsub, fnmsub, fnmadd
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [15:0] y_m1_l0;
  logic [9:0] fl_m1_l0;
  logic [45:0] x_m1_l0;
  logic [45:0] ix_fp_fma_a_m1_l0;
  logic [45:0] ix_fp_fma_b_m1_l0;
  logic [45:0] ix_fp_fma_c_m1_l0;
  logic [2:0] ix_fp_fma_op_m1_l0;
  alu_core_m1_fp_adder_fp_fma_fp_multiplier_sh #(.LANE(0)) u_m1_l0 (.a(a), .b(b), .c(c), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_l0), .fl_m1(fl_m1_l0), .xa_m1(xa_m1), .xb_m1(xb_m1), .xc_m1(xc_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .denc_m1(denc_m1), .x_m1(x_m1_l0), .ix_fp_fma_a_m1(ix_fp_fma_a_m1_l0), .ix_fp_fma_b_m1(ix_fp_fma_b_m1_l0), .ix_fp_fma_c_m1(ix_fp_fma_c_m1_l0), .ix_fp_fma_op_m1(ix_fp_fma_op_m1_l0), .iy_fp_fma_m1(iy_fp_fma_m1));
  assign y_m1 = y_m1_l0;
  assign fl_m1 = fl_m1_l0;
  assign x_m1 = x_m1_l0;
  assign ix_fp_fma_a_m1 = ix_fp_fma_a_m1_l0;
  assign ix_fp_fma_b_m1 = ix_fp_fma_b_m1_l0;
  assign ix_fp_fma_c_m1 = ix_fp_fma_c_m1_l0;
  assign ix_fp_fma_op_m1 = ix_fp_fma_op_m1_l0;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l0_fp_multiplier
// m1.l0.fp_multiplier: realized by the unit module in member m1_l0_fp_fma
// ADIR-MEMBER m1_l0_fp_comparator
// EVOLVE-BLOCK-START
module alu_core_u_m1_l0_fp_comparator (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [15:0] c,
  input  logic [3:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m1,
  output logic [9:0] fl_m1,
  input  logic [45:0] xa_m1,
  input  logic [45:0] xb_m1,
  input  logic [45:0] xc_m1,
  input  logic [0:0] dena_m1,
  input  logic [0:0] denb_m1,
  input  logic [0:0] denc_m1
);
  // alu_core_u_m1_l0_fp_comparator: physical structure `m1.l0.fp_comparator` (kind fp_comparator, slot fp_comparator); realizes m1.l0.fp_comparator: fp_comparator, mode 1 lane 0, bf16, ops fmin, fmax, fcmp
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [15:0] y_m1_l0;
  logic [9:0] fl_m1_l0;
  alu_core_m1_fp_comparator #(.LANE(0)) u_m1_l0 (.a(a), .b(b), .c(c), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_l0), .fl_m1(fl_m1_l0), .xa_m1(xa_m1), .xb_m1(xb_m1), .xc_m1(xc_m1), .dena_m1(dena_m1), .denb_m1(denb_m1), .denc_m1(denc_m1));
  assign y_m1 = y_m1_l0;
  assign fl_m1 = fl_m1_l0;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m2_l0_fp_adder
// m2.l0.fp_adder: realized by the unit module in member m2_l0_fp_fma
// ADIR-MEMBER m2_l0_unpacker
// EVOLVE-BLOCK-START
module alu_core_u_m2_l0_unpacker (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [15:0] c,
  input  logic [3:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [45:0] xa_m2,
  output logic [45:0] xb_m2,
  output logic [45:0] xc_m2,
  output logic [0:0] dena_m2,
  output logic [0:0] denb_m2,
  output logic [0:0] denc_m2
);
  // alu_core_u_m2_l0_unpacker: physical structure `m2.l0.unpacker` (kind unpacker, slot unpacker); realizes m2.l0.unpacker: unpacker, mode 2 lane 0, fp8e5m2, ops fadd, fsub, fmul, fmadd, fmsub, fnmsub, fnmadd, fmin, fmax, fcmp
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [45:0] xa_m2_l0;
  logic [45:0] xb_m2_l0;
  logic [45:0] xc_m2_l0;
  logic dena_m2_l0;
  logic denb_m2_l0;
  logic denc_m2_l0;
  alu_core_m2_unpacker #(.LANE(0)) u_m2_l0 (.a(a), .b(b), .c(c), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .xa_m2(xa_m2_l0), .xb_m2(xb_m2_l0), .xc_m2(xc_m2_l0), .dena_m2(dena_m2_l0), .denb_m2(denb_m2_l0), .denc_m2(denc_m2_l0));
  assign xa_m2 = xa_m2_l0;
  assign xb_m2 = xb_m2_l0;
  assign xc_m2 = xc_m2_l0;
  assign dena_m2 = dena_m2_l0;
  assign denb_m2 = denb_m2_l0;
  assign denc_m2 = denc_m2_l0;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m2_l0_rounder
// EVOLVE-BLOCK-START
module alu_core_u_m2_l0_rounder (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [15:0] c,
  input  logic [3:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m2,
  output logic [9:0] fl_m2,
  input  logic [45:0] xa_m2,
  input  logic [45:0] xb_m2,
  input  logic [45:0] xc_m2,
  input  logic [0:0] dena_m2,
  input  logic [0:0] denb_m2,
  input  logic [0:0] denc_m2,
  input  logic [45:0] x_m2
);
  // alu_core_u_m2_l0_rounder: physical structure `m2.l0.rounder` (kind rounder, slot rounder); realizes m2.l0.rounder: rounder, mode 2 lane 0, fp8e5m2, ops fadd, fsub, fmul, fmadd, fmsub, fnmsub, fnmadd
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [15:0] y_m2_l0;
  logic [9:0] fl_m2_l0;
  alu_core_m2_rounder #(.LANE(0)) u_m2_l0 (.a(a), .b(b), .c(c), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_l0), .fl_m2(fl_m2_l0), .xa_m2(xa_m2), .xb_m2(xb_m2), .xc_m2(xc_m2), .dena_m2(dena_m2), .denb_m2(denb_m2), .denc_m2(denc_m2), .x_m2(x_m2));
  assign y_m2 = y_m2_l0;
  assign fl_m2 = fl_m2_l0;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m2_l0_fp_fma
// EVOLVE-BLOCK-START
module alu_core_u_m2_l0_fp_fma (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [15:0] c,
  input  logic [3:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m2,
  output logic [9:0] fl_m2,
  input  logic [45:0] xa_m2,
  input  logic [45:0] xb_m2,
  input  logic [45:0] xc_m2,
  input  logic [0:0] dena_m2,
  input  logic [0:0] denb_m2,
  input  logic [0:0] denc_m2,
  output logic [45:0] x_m2
);
  // alu_core_u_m2_l0_fp_fma: physical structure `m2.l0.fp_fma` (kind fp_fma, slot fp_fma); realizes m2.l0.fp_fma: fp_fma, mode 2 lane 0, fp8e5m2, ops fadd, fsub, fmul, fmadd, fmsub, fnmsub, fnmadd, m2.l0.fp_multiplier: fp_multiplier, mode 2 lane 0, fp8e5m2, ops fmul, fmadd, fmsub, fnmsub, fnmadd, m2.l0.fp_adder: fp_adder, mode 2 lane 0, fp8e5m2, ops fadd, fsub, fmadd, fmsub, fnmsub, fnmadd
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [15:0] y_m2_l0;
  logic [9:0] fl_m2_l0;
  logic [45:0] x_m2_l0;
  alu_core_m2_fp_adder_fp_fma_fp_multiplier #(.LANE(0)) u_m2_l0 (.a(a), .b(b), .c(c), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_l0), .fl_m2(fl_m2_l0), .xa_m2(xa_m2), .xb_m2(xb_m2), .xc_m2(xc_m2), .dena_m2(dena_m2), .denb_m2(denb_m2), .denc_m2(denc_m2), .x_m2(x_m2_l0));
  assign y_m2 = y_m2_l0;
  assign fl_m2 = fl_m2_l0;
  assign x_m2 = x_m2_l0;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m2_l0_fp_multiplier
// m2.l0.fp_multiplier: realized by the unit module in member m2_l0_fp_fma
// ADIR-MEMBER m2_l0_fp_comparator
// EVOLVE-BLOCK-START
module alu_core_u_m2_l0_fp_comparator (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [15:0] c,
  input  logic [3:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m2,
  output logic [9:0] fl_m2,
  input  logic [45:0] xa_m2,
  input  logic [45:0] xb_m2,
  input  logic [45:0] xc_m2,
  input  logic [0:0] dena_m2,
  input  logic [0:0] denb_m2,
  input  logic [0:0] denc_m2
);
  // alu_core_u_m2_l0_fp_comparator: physical structure `m2.l0.fp_comparator` (kind fp_comparator, slot fp_comparator); realizes m2.l0.fp_comparator: fp_comparator, mode 2 lane 0, fp8e5m2, ops fmin, fmax, fcmp
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [15:0] y_m2_l0;
  logic [9:0] fl_m2_l0;
  alu_core_m2_fp_comparator #(.LANE(0)) u_m2_l0 (.a(a), .b(b), .c(c), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_l0), .fl_m2(fl_m2_l0), .xa_m2(xa_m2), .xb_m2(xb_m2), .xc_m2(xc_m2), .dena_m2(dena_m2), .denb_m2(denb_m2), .denc_m2(denc_m2));
  assign y_m2 = y_m2_l0;
  assign fl_m2 = fl_m2_l0;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m3_l0_fp_adder
// m3.l0.fp_adder: realized by the unit module in member m3_l0_fp_fma
// ADIR-MEMBER m3_l0_unpacker
// EVOLVE-BLOCK-START
module alu_core_u_m3_l0_unpacker (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [15:0] c,
  input  logic [3:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [45:0] xa_m3,
  output logic [45:0] xb_m3,
  output logic [45:0] xc_m3,
  output logic [0:0] dena_m3,
  output logic [0:0] denb_m3,
  output logic [0:0] denc_m3
);
  // alu_core_u_m3_l0_unpacker: physical structure `m3.l0.unpacker` (kind unpacker, slot unpacker); realizes m3.l0.unpacker: unpacker, mode 3 lane 0, fp8e4m3, ops fadd, fsub, fmul, fmadd, fmsub, fnmsub, fnmadd, fmin, fmax, fcmp
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [45:0] xa_m3_l0;
  logic [45:0] xb_m3_l0;
  logic [45:0] xc_m3_l0;
  logic dena_m3_l0;
  logic denb_m3_l0;
  logic denc_m3_l0;
  alu_core_m3_unpacker #(.LANE(0)) u_m3_l0 (.a(a), .b(b), .c(c), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .xa_m3(xa_m3_l0), .xb_m3(xb_m3_l0), .xc_m3(xc_m3_l0), .dena_m3(dena_m3_l0), .denb_m3(denb_m3_l0), .denc_m3(denc_m3_l0));
  assign xa_m3 = xa_m3_l0;
  assign xb_m3 = xb_m3_l0;
  assign xc_m3 = xc_m3_l0;
  assign dena_m3 = dena_m3_l0;
  assign denb_m3 = denb_m3_l0;
  assign denc_m3 = denc_m3_l0;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m3_l0_rounder
// EVOLVE-BLOCK-START
module alu_core_u_m3_l0_rounder (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [15:0] c,
  input  logic [3:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m3,
  output logic [9:0] fl_m3,
  input  logic [45:0] xa_m3,
  input  logic [45:0] xb_m3,
  input  logic [45:0] xc_m3,
  input  logic [0:0] dena_m3,
  input  logic [0:0] denb_m3,
  input  logic [0:0] denc_m3,
  input  logic [45:0] x_m3
);
  // alu_core_u_m3_l0_rounder: physical structure `m3.l0.rounder` (kind rounder, slot rounder); realizes m3.l0.rounder: rounder, mode 3 lane 0, fp8e4m3, ops fadd, fsub, fmul, fmadd, fmsub, fnmsub, fnmadd
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [15:0] y_m3_l0;
  logic [9:0] fl_m3_l0;
  alu_core_m3_rounder #(.LANE(0)) u_m3_l0 (.a(a), .b(b), .c(c), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m3(y_m3_l0), .fl_m3(fl_m3_l0), .xa_m3(xa_m3), .xb_m3(xb_m3), .xc_m3(xc_m3), .dena_m3(dena_m3), .denb_m3(denb_m3), .denc_m3(denc_m3), .x_m3(x_m3));
  assign y_m3 = y_m3_l0;
  assign fl_m3 = fl_m3_l0;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m3_l0_fp_fma
// EVOLVE-BLOCK-START
module alu_core_u_m3_l0_fp_fma (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [15:0] c,
  input  logic [3:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m3,
  output logic [9:0] fl_m3,
  input  logic [45:0] xa_m3,
  input  logic [45:0] xb_m3,
  input  logic [45:0] xc_m3,
  input  logic [0:0] dena_m3,
  input  logic [0:0] denb_m3,
  input  logic [0:0] denc_m3,
  output logic [45:0] x_m3
);
  // alu_core_u_m3_l0_fp_fma: physical structure `m3.l0.fp_fma` (kind fp_fma, slot fp_fma); realizes m3.l0.fp_fma: fp_fma, mode 3 lane 0, fp8e4m3, ops fadd, fsub, fmul, fmadd, fmsub, fnmsub, fnmadd, m3.l0.fp_multiplier: fp_multiplier, mode 3 lane 0, fp8e4m3, ops fmul, fmadd, fmsub, fnmsub, fnmadd, m3.l0.fp_adder: fp_adder, mode 3 lane 0, fp8e4m3, ops fadd, fsub, fmadd, fmsub, fnmsub, fnmadd
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [15:0] y_m3_l0;
  logic [9:0] fl_m3_l0;
  logic [45:0] x_m3_l0;
  alu_core_m3_fp_adder_fp_fma_fp_multiplier #(.LANE(0)) u_m3_l0 (.a(a), .b(b), .c(c), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m3(y_m3_l0), .fl_m3(fl_m3_l0), .xa_m3(xa_m3), .xb_m3(xb_m3), .xc_m3(xc_m3), .dena_m3(dena_m3), .denb_m3(denb_m3), .denc_m3(denc_m3), .x_m3(x_m3_l0));
  assign y_m3 = y_m3_l0;
  assign fl_m3 = fl_m3_l0;
  assign x_m3 = x_m3_l0;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m3_l0_fp_multiplier
// m3.l0.fp_multiplier: realized by the unit module in member m3_l0_fp_fma
// ADIR-MEMBER m3_l0_fp_comparator
// EVOLVE-BLOCK-START
module alu_core_u_m3_l0_fp_comparator (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [15:0] c,
  input  logic [3:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m3,
  output logic [9:0] fl_m3,
  input  logic [45:0] xa_m3,
  input  logic [45:0] xb_m3,
  input  logic [45:0] xc_m3,
  input  logic [0:0] dena_m3,
  input  logic [0:0] denb_m3,
  input  logic [0:0] denc_m3
);
  // alu_core_u_m3_l0_fp_comparator: physical structure `m3.l0.fp_comparator` (kind fp_comparator, slot fp_comparator); realizes m3.l0.fp_comparator: fp_comparator, mode 3 lane 0, fp8e4m3, ops fmin, fmax, fcmp
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [15:0] y_m3_l0;
  logic [9:0] fl_m3_l0;
  alu_core_m3_fp_comparator #(.LANE(0)) u_m3_l0 (.a(a), .b(b), .c(c), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m3(y_m3_l0), .fl_m3(fl_m3_l0), .xa_m3(xa_m3), .xb_m3(xb_m3), .xc_m3(xc_m3), .dena_m3(dena_m3), .denb_m3(denb_m3), .denc_m3(denc_m3));
  assign y_m3 = y_m3_l0;
  assign fl_m3 = fl_m3_l0;
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



// lzd_cell_tree (pair_cell, binary_count, valid flags flat): the leading zeros of a 44-bit word

// lzd_cell_tree (pair_cell, binary_count, valid flags flat): the leading zeros of a 43-bit word
module fam_count_lzd_pair_cell_binary_count_vflat_w43 (input logic [42:0] a, output logic [5:0] n);
  logic v0_0; assign v0_0 = a[42] | a[41];
  logic p0_0; assign p0_0 = ~a[42];
  logic v0_1; assign v0_1 = a[40] | a[39];
  logic p0_1; assign p0_1 = ~a[40];
  logic v0_2; assign v0_2 = a[38] | a[37];
  logic p0_2; assign p0_2 = ~a[38];
  logic v0_3; assign v0_3 = a[36] | a[35];
  logic p0_3; assign p0_3 = ~a[36];
  logic v0_4; assign v0_4 = a[34] | a[33];
  logic p0_4; assign p0_4 = ~a[34];
  logic v0_5; assign v0_5 = a[32] | a[31];
  logic p0_5; assign p0_5 = ~a[32];
  logic v0_6; assign v0_6 = a[30] | a[29];
  logic p0_6; assign p0_6 = ~a[30];
  logic v0_7; assign v0_7 = a[28] | a[27];
  logic p0_7; assign p0_7 = ~a[28];
  logic v0_8; assign v0_8 = a[26] | a[25];
  logic p0_8; assign p0_8 = ~a[26];
  logic v0_9; assign v0_9 = a[24] | a[23];
  logic p0_9; assign p0_9 = ~a[24];
  logic v0_10; assign v0_10 = a[22] | a[21];
  logic p0_10; assign p0_10 = ~a[22];
  logic v0_11; assign v0_11 = a[20] | a[19];
  logic p0_11; assign p0_11 = ~a[20];
  logic v0_12; assign v0_12 = a[18] | a[17];
  logic p0_12; assign p0_12 = ~a[18];
  logic v0_13; assign v0_13 = a[16] | a[15];
  logic p0_13; assign p0_13 = ~a[16];
  logic v0_14; assign v0_14 = a[14] | a[13];
  logic p0_14; assign p0_14 = ~a[14];
  logic v0_15; assign v0_15 = a[12] | a[11];
  logic p0_15; assign p0_15 = ~a[12];
  logic v0_16; assign v0_16 = a[10] | a[9];
  logic p0_16; assign p0_16 = ~a[10];
  logic v0_17; assign v0_17 = a[8] | a[7];
  logic p0_17; assign p0_17 = ~a[8];
  logic v0_18; assign v0_18 = a[6] | a[5];
  logic p0_18; assign p0_18 = ~a[6];
  logic v0_19; assign v0_19 = a[4] | a[3];
  logic p0_19; assign p0_19 = ~a[4];
  logic v0_20; assign v0_20 = a[2] | a[1];
  logic p0_20; assign p0_20 = ~a[2];
  logic v0_21; assign v0_21 = a[0] | 1'b0;
  logic p0_21; assign p0_21 = ~a[0];
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
  logic v1_0; assign v1_0 = a[42] | a[41] | a[40] | a[39];
  logic [1:0] p1_0; assign p1_0 = v0_0 ? {1'b0, p0_0} : {1'b1, p0_1};
  logic v1_1; assign v1_1 = a[38] | a[37] | a[36] | a[35];
  logic [1:0] p1_1; assign p1_1 = v0_2 ? {1'b0, p0_2} : {1'b1, p0_3};
  logic v1_2; assign v1_2 = a[34] | a[33] | a[32] | a[31];
  logic [1:0] p1_2; assign p1_2 = v0_4 ? {1'b0, p0_4} : {1'b1, p0_5};
  logic v1_3; assign v1_3 = a[30] | a[29] | a[28] | a[27];
  logic [1:0] p1_3; assign p1_3 = v0_6 ? {1'b0, p0_6} : {1'b1, p0_7};
  logic v1_4; assign v1_4 = a[26] | a[25] | a[24] | a[23];
  logic [1:0] p1_4; assign p1_4 = v0_8 ? {1'b0, p0_8} : {1'b1, p0_9};
  logic v1_5; assign v1_5 = a[22] | a[21] | a[20] | a[19];
  logic [1:0] p1_5; assign p1_5 = v0_10 ? {1'b0, p0_10} : {1'b1, p0_11};
  logic v1_6; assign v1_6 = a[18] | a[17] | a[16] | a[15];
  logic [1:0] p1_6; assign p1_6 = v0_12 ? {1'b0, p0_12} : {1'b1, p0_13};
  logic v1_7; assign v1_7 = a[14] | a[13] | a[12] | a[11];
  logic [1:0] p1_7; assign p1_7 = v0_14 ? {1'b0, p0_14} : {1'b1, p0_15};
  logic v1_8; assign v1_8 = a[10] | a[9] | a[8] | a[7];
  logic [1:0] p1_8; assign p1_8 = v0_16 ? {1'b0, p0_16} : {1'b1, p0_17};
  logic v1_9; assign v1_9 = a[6] | a[5] | a[4] | a[3];
  logic [1:0] p1_9; assign p1_9 = v0_18 ? {1'b0, p0_18} : {1'b1, p0_19};
  logic v1_10; assign v1_10 = a[2] | a[1] | a[0] | 1'b0;
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
  logic v2_0; assign v2_0 = a[42] | a[41] | a[40] | a[39] | a[38] | a[37] | a[36] | a[35];
  logic [2:0] p2_0; assign p2_0 = v1_0 ? {1'b0, p1_0} : {1'b1, p1_1};
  logic v2_1; assign v2_1 = a[34] | a[33] | a[32] | a[31] | a[30] | a[29] | a[28] | a[27];
  logic [2:0] p2_1; assign p2_1 = v1_2 ? {1'b0, p1_2} : {1'b1, p1_3};
  logic v2_2; assign v2_2 = a[26] | a[25] | a[24] | a[23] | a[22] | a[21] | a[20] | a[19];
  logic [2:0] p2_2; assign p2_2 = v1_4 ? {1'b0, p1_4} : {1'b1, p1_5};
  logic v2_3; assign v2_3 = a[18] | a[17] | a[16] | a[15] | a[14] | a[13] | a[12] | a[11];
  logic [2:0] p2_3; assign p2_3 = v1_6 ? {1'b0, p1_6} : {1'b1, p1_7};
  logic v2_4; assign v2_4 = a[10] | a[9] | a[8] | a[7] | a[6] | a[5] | a[4] | a[3];
  logic [2:0] p2_4; assign p2_4 = v1_8 ? {1'b0, p1_8} : {1'b1, p1_9};
  logic v2_5; assign v2_5 = a[2] | a[1] | a[0] | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [2:0] p2_5; assign p2_5 = v1_10 ? {1'b0, p1_10} : {1'b1, p1_11};
  logic v2_6; assign v2_6 = 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [2:0] p2_6; assign p2_6 = v1_12 ? {1'b0, p1_12} : {1'b1, p1_13};
  logic v2_7; assign v2_7 = 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [2:0] p2_7; assign p2_7 = v1_14 ? {1'b0, p1_14} : {1'b1, p1_15};
  logic v3_0; assign v3_0 = a[42] | a[41] | a[40] | a[39] | a[38] | a[37] | a[36] | a[35] | a[34] | a[33] | a[32] | a[31] | a[30] | a[29] | a[28] | a[27];
  logic [3:0] p3_0; assign p3_0 = v2_0 ? {1'b0, p2_0} : {1'b1, p2_1};
  logic v3_1; assign v3_1 = a[26] | a[25] | a[24] | a[23] | a[22] | a[21] | a[20] | a[19] | a[18] | a[17] | a[16] | a[15] | a[14] | a[13] | a[12] | a[11];
  logic [3:0] p3_1; assign p3_1 = v2_2 ? {1'b0, p2_2} : {1'b1, p2_3};
  logic v3_2; assign v3_2 = a[10] | a[9] | a[8] | a[7] | a[6] | a[5] | a[4] | a[3] | a[2] | a[1] | a[0] | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [3:0] p3_2; assign p3_2 = v2_4 ? {1'b0, p2_4} : {1'b1, p2_5};
  logic v3_3; assign v3_3 = 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [3:0] p3_3; assign p3_3 = v2_6 ? {1'b0, p2_6} : {1'b1, p2_7};
  logic v4_0; assign v4_0 = a[42] | a[41] | a[40] | a[39] | a[38] | a[37] | a[36] | a[35] | a[34] | a[33] | a[32] | a[31] | a[30] | a[29] | a[28] | a[27] | a[26] | a[25] | a[24] | a[23] | a[22] | a[21] | a[20] | a[19] | a[18] | a[17] | a[16] | a[15] | a[14] | a[13] | a[12] | a[11];
  logic [4:0] p4_0; assign p4_0 = v3_0 ? {1'b0, p3_0} : {1'b1, p3_1};
  logic v4_1; assign v4_1 = a[10] | a[9] | a[8] | a[7] | a[6] | a[5] | a[4] | a[3] | a[2] | a[1] | a[0] | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [4:0] p4_1; assign p4_1 = v3_2 ? {1'b0, p3_2} : {1'b1, p3_3};
  logic v5_0; assign v5_0 = a[42] | a[41] | a[40] | a[39] | a[38] | a[37] | a[36] | a[35] | a[34] | a[33] | a[32] | a[31] | a[30] | a[29] | a[28] | a[27] | a[26] | a[25] | a[24] | a[23] | a[22] | a[21] | a[20] | a[19] | a[18] | a[17] | a[16] | a[15] | a[14] | a[13] | a[12] | a[11] | a[10] | a[9] | a[8] | a[7] | a[6] | a[5] | a[4] | a[3] | a[2] | a[1] | a[0] | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [5:0] p5_0; assign p5_0 = v4_0 ? {1'b0, p4_0} : {1'b1, p4_1};
  assign n = v5_0 ? p5_0 : 6'd43;
endmodule
// lzd_cell_tree (pair_cell, binary_count, valid flags flat): the leading zeros of a 43-bit word




// lzd_cell_tree (pair_cell, binary_count, valid flags flat): the leading zeros of a 48-bit word

// lzd_cell_tree (pair_cell, binary_count, valid flags flat): the leading zeros of a 48-bit word

// lzd_cell_tree (pair_cell, binary_count, valid flags flat): the leading zeros of a 44-bit word
module fam_count_lzd_pair_cell_binary_count_vflat_w44 (input logic [43:0] a, output logic [5:0] n);
  logic v0_0; assign v0_0 = a[43] | a[42];
  logic p0_0; assign p0_0 = ~a[43];
  logic v0_1; assign v0_1 = a[41] | a[40];
  logic p0_1; assign p0_1 = ~a[41];
  logic v0_2; assign v0_2 = a[39] | a[38];
  logic p0_2; assign p0_2 = ~a[39];
  logic v0_3; assign v0_3 = a[37] | a[36];
  logic p0_3; assign p0_3 = ~a[37];
  logic v0_4; assign v0_4 = a[35] | a[34];
  logic p0_4; assign p0_4 = ~a[35];
  logic v0_5; assign v0_5 = a[33] | a[32];
  logic p0_5; assign p0_5 = ~a[33];
  logic v0_6; assign v0_6 = a[31] | a[30];
  logic p0_6; assign p0_6 = ~a[31];
  logic v0_7; assign v0_7 = a[29] | a[28];
  logic p0_7; assign p0_7 = ~a[29];
  logic v0_8; assign v0_8 = a[27] | a[26];
  logic p0_8; assign p0_8 = ~a[27];
  logic v0_9; assign v0_9 = a[25] | a[24];
  logic p0_9; assign p0_9 = ~a[25];
  logic v0_10; assign v0_10 = a[23] | a[22];
  logic p0_10; assign p0_10 = ~a[23];
  logic v0_11; assign v0_11 = a[21] | a[20];
  logic p0_11; assign p0_11 = ~a[21];
  logic v0_12; assign v0_12 = a[19] | a[18];
  logic p0_12; assign p0_12 = ~a[19];
  logic v0_13; assign v0_13 = a[17] | a[16];
  logic p0_13; assign p0_13 = ~a[17];
  logic v0_14; assign v0_14 = a[15] | a[14];
  logic p0_14; assign p0_14 = ~a[15];
  logic v0_15; assign v0_15 = a[13] | a[12];
  logic p0_15; assign p0_15 = ~a[13];
  logic v0_16; assign v0_16 = a[11] | a[10];
  logic p0_16; assign p0_16 = ~a[11];
  logic v0_17; assign v0_17 = a[9] | a[8];
  logic p0_17; assign p0_17 = ~a[9];
  logic v0_18; assign v0_18 = a[7] | a[6];
  logic p0_18; assign p0_18 = ~a[7];
  logic v0_19; assign v0_19 = a[5] | a[4];
  logic p0_19; assign p0_19 = ~a[5];
  logic v0_20; assign v0_20 = a[3] | a[2];
  logic p0_20; assign p0_20 = ~a[3];
  logic v0_21; assign v0_21 = a[1] | a[0];
  logic p0_21; assign p0_21 = ~a[1];
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
  logic v1_0; assign v1_0 = a[43] | a[42] | a[41] | a[40];
  logic [1:0] p1_0; assign p1_0 = v0_0 ? {1'b0, p0_0} : {1'b1, p0_1};
  logic v1_1; assign v1_1 = a[39] | a[38] | a[37] | a[36];
  logic [1:0] p1_1; assign p1_1 = v0_2 ? {1'b0, p0_2} : {1'b1, p0_3};
  logic v1_2; assign v1_2 = a[35] | a[34] | a[33] | a[32];
  logic [1:0] p1_2; assign p1_2 = v0_4 ? {1'b0, p0_4} : {1'b1, p0_5};
  logic v1_3; assign v1_3 = a[31] | a[30] | a[29] | a[28];
  logic [1:0] p1_3; assign p1_3 = v0_6 ? {1'b0, p0_6} : {1'b1, p0_7};
  logic v1_4; assign v1_4 = a[27] | a[26] | a[25] | a[24];
  logic [1:0] p1_4; assign p1_4 = v0_8 ? {1'b0, p0_8} : {1'b1, p0_9};
  logic v1_5; assign v1_5 = a[23] | a[22] | a[21] | a[20];
  logic [1:0] p1_5; assign p1_5 = v0_10 ? {1'b0, p0_10} : {1'b1, p0_11};
  logic v1_6; assign v1_6 = a[19] | a[18] | a[17] | a[16];
  logic [1:0] p1_6; assign p1_6 = v0_12 ? {1'b0, p0_12} : {1'b1, p0_13};
  logic v1_7; assign v1_7 = a[15] | a[14] | a[13] | a[12];
  logic [1:0] p1_7; assign p1_7 = v0_14 ? {1'b0, p0_14} : {1'b1, p0_15};
  logic v1_8; assign v1_8 = a[11] | a[10] | a[9] | a[8];
  logic [1:0] p1_8; assign p1_8 = v0_16 ? {1'b0, p0_16} : {1'b1, p0_17};
  logic v1_9; assign v1_9 = a[7] | a[6] | a[5] | a[4];
  logic [1:0] p1_9; assign p1_9 = v0_18 ? {1'b0, p0_18} : {1'b1, p0_19};
  logic v1_10; assign v1_10 = a[3] | a[2] | a[1] | a[0];
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
  logic v2_0; assign v2_0 = a[43] | a[42] | a[41] | a[40] | a[39] | a[38] | a[37] | a[36];
  logic [2:0] p2_0; assign p2_0 = v1_0 ? {1'b0, p1_0} : {1'b1, p1_1};
  logic v2_1; assign v2_1 = a[35] | a[34] | a[33] | a[32] | a[31] | a[30] | a[29] | a[28];
  logic [2:0] p2_1; assign p2_1 = v1_2 ? {1'b0, p1_2} : {1'b1, p1_3};
  logic v2_2; assign v2_2 = a[27] | a[26] | a[25] | a[24] | a[23] | a[22] | a[21] | a[20];
  logic [2:0] p2_2; assign p2_2 = v1_4 ? {1'b0, p1_4} : {1'b1, p1_5};
  logic v2_3; assign v2_3 = a[19] | a[18] | a[17] | a[16] | a[15] | a[14] | a[13] | a[12];
  logic [2:0] p2_3; assign p2_3 = v1_6 ? {1'b0, p1_6} : {1'b1, p1_7};
  logic v2_4; assign v2_4 = a[11] | a[10] | a[9] | a[8] | a[7] | a[6] | a[5] | a[4];
  logic [2:0] p2_4; assign p2_4 = v1_8 ? {1'b0, p1_8} : {1'b1, p1_9};
  logic v2_5; assign v2_5 = a[3] | a[2] | a[1] | a[0] | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [2:0] p2_5; assign p2_5 = v1_10 ? {1'b0, p1_10} : {1'b1, p1_11};
  logic v2_6; assign v2_6 = 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [2:0] p2_6; assign p2_6 = v1_12 ? {1'b0, p1_12} : {1'b1, p1_13};
  logic v2_7; assign v2_7 = 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [2:0] p2_7; assign p2_7 = v1_14 ? {1'b0, p1_14} : {1'b1, p1_15};
  logic v3_0; assign v3_0 = a[43] | a[42] | a[41] | a[40] | a[39] | a[38] | a[37] | a[36] | a[35] | a[34] | a[33] | a[32] | a[31] | a[30] | a[29] | a[28];
  logic [3:0] p3_0; assign p3_0 = v2_0 ? {1'b0, p2_0} : {1'b1, p2_1};
  logic v3_1; assign v3_1 = a[27] | a[26] | a[25] | a[24] | a[23] | a[22] | a[21] | a[20] | a[19] | a[18] | a[17] | a[16] | a[15] | a[14] | a[13] | a[12];
  logic [3:0] p3_1; assign p3_1 = v2_2 ? {1'b0, p2_2} : {1'b1, p2_3};
  logic v3_2; assign v3_2 = a[11] | a[10] | a[9] | a[8] | a[7] | a[6] | a[5] | a[4] | a[3] | a[2] | a[1] | a[0] | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [3:0] p3_2; assign p3_2 = v2_4 ? {1'b0, p2_4} : {1'b1, p2_5};
  logic v3_3; assign v3_3 = 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [3:0] p3_3; assign p3_3 = v2_6 ? {1'b0, p2_6} : {1'b1, p2_7};
  logic v4_0; assign v4_0 = a[43] | a[42] | a[41] | a[40] | a[39] | a[38] | a[37] | a[36] | a[35] | a[34] | a[33] | a[32] | a[31] | a[30] | a[29] | a[28] | a[27] | a[26] | a[25] | a[24] | a[23] | a[22] | a[21] | a[20] | a[19] | a[18] | a[17] | a[16] | a[15] | a[14] | a[13] | a[12];
  logic [4:0] p4_0; assign p4_0 = v3_0 ? {1'b0, p3_0} : {1'b1, p3_1};
  logic v4_1; assign v4_1 = a[11] | a[10] | a[9] | a[8] | a[7] | a[6] | a[5] | a[4] | a[3] | a[2] | a[1] | a[0] | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [4:0] p4_1; assign p4_1 = v3_2 ? {1'b0, p3_2} : {1'b1, p3_3};
  logic v5_0; assign v5_0 = a[43] | a[42] | a[41] | a[40] | a[39] | a[38] | a[37] | a[36] | a[35] | a[34] | a[33] | a[32] | a[31] | a[30] | a[29] | a[28] | a[27] | a[26] | a[25] | a[24] | a[23] | a[22] | a[21] | a[20] | a[19] | a[18] | a[17] | a[16] | a[15] | a[14] | a[13] | a[12] | a[11] | a[10] | a[9] | a[8] | a[7] | a[6] | a[5] | a[4] | a[3] | a[2] | a[1] | a[0] | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [5:0] p5_0; assign p5_0 = v4_0 ? {1'b0, p4_0} : {1'b1, p4_1};
  assign n = v5_0 ? p5_0 : 6'd44;
endmodule


// lzd_cell_tree (pair_cell, binary_count, valid flags flat): the leading zeros of a 48-bit word
module fam_count_lzd_pair_cell_binary_count_vflat_w48 (input logic [47:0] a, output logic [5:0] n);
  logic v0_0; assign v0_0 = a[47] | a[46];
  logic p0_0; assign p0_0 = ~a[47];
  logic v0_1; assign v0_1 = a[45] | a[44];
  logic p0_1; assign p0_1 = ~a[45];
  logic v0_2; assign v0_2 = a[43] | a[42];
  logic p0_2; assign p0_2 = ~a[43];
  logic v0_3; assign v0_3 = a[41] | a[40];
  logic p0_3; assign p0_3 = ~a[41];
  logic v0_4; assign v0_4 = a[39] | a[38];
  logic p0_4; assign p0_4 = ~a[39];
  logic v0_5; assign v0_5 = a[37] | a[36];
  logic p0_5; assign p0_5 = ~a[37];
  logic v0_6; assign v0_6 = a[35] | a[34];
  logic p0_6; assign p0_6 = ~a[35];
  logic v0_7; assign v0_7 = a[33] | a[32];
  logic p0_7; assign p0_7 = ~a[33];
  logic v0_8; assign v0_8 = a[31] | a[30];
  logic p0_8; assign p0_8 = ~a[31];
  logic v0_9; assign v0_9 = a[29] | a[28];
  logic p0_9; assign p0_9 = ~a[29];
  logic v0_10; assign v0_10 = a[27] | a[26];
  logic p0_10; assign p0_10 = ~a[27];
  logic v0_11; assign v0_11 = a[25] | a[24];
  logic p0_11; assign p0_11 = ~a[25];
  logic v0_12; assign v0_12 = a[23] | a[22];
  logic p0_12; assign p0_12 = ~a[23];
  logic v0_13; assign v0_13 = a[21] | a[20];
  logic p0_13; assign p0_13 = ~a[21];
  logic v0_14; assign v0_14 = a[19] | a[18];
  logic p0_14; assign p0_14 = ~a[19];
  logic v0_15; assign v0_15 = a[17] | a[16];
  logic p0_15; assign p0_15 = ~a[17];
  logic v0_16; assign v0_16 = a[15] | a[14];
  logic p0_16; assign p0_16 = ~a[15];
  logic v0_17; assign v0_17 = a[13] | a[12];
  logic p0_17; assign p0_17 = ~a[13];
  logic v0_18; assign v0_18 = a[11] | a[10];
  logic p0_18; assign p0_18 = ~a[11];
  logic v0_19; assign v0_19 = a[9] | a[8];
  logic p0_19; assign p0_19 = ~a[9];
  logic v0_20; assign v0_20 = a[7] | a[6];
  logic p0_20; assign p0_20 = ~a[7];
  logic v0_21; assign v0_21 = a[5] | a[4];
  logic p0_21; assign p0_21 = ~a[5];
  logic v0_22; assign v0_22 = a[3] | a[2];
  logic p0_22; assign p0_22 = ~a[3];
  logic v0_23; assign v0_23 = a[1] | a[0];
  logic p0_23; assign p0_23 = ~a[1];
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
  logic v1_0; assign v1_0 = a[47] | a[46] | a[45] | a[44];
  logic [1:0] p1_0; assign p1_0 = v0_0 ? {1'b0, p0_0} : {1'b1, p0_1};
  logic v1_1; assign v1_1 = a[43] | a[42] | a[41] | a[40];
  logic [1:0] p1_1; assign p1_1 = v0_2 ? {1'b0, p0_2} : {1'b1, p0_3};
  logic v1_2; assign v1_2 = a[39] | a[38] | a[37] | a[36];
  logic [1:0] p1_2; assign p1_2 = v0_4 ? {1'b0, p0_4} : {1'b1, p0_5};
  logic v1_3; assign v1_3 = a[35] | a[34] | a[33] | a[32];
  logic [1:0] p1_3; assign p1_3 = v0_6 ? {1'b0, p0_6} : {1'b1, p0_7};
  logic v1_4; assign v1_4 = a[31] | a[30] | a[29] | a[28];
  logic [1:0] p1_4; assign p1_4 = v0_8 ? {1'b0, p0_8} : {1'b1, p0_9};
  logic v1_5; assign v1_5 = a[27] | a[26] | a[25] | a[24];
  logic [1:0] p1_5; assign p1_5 = v0_10 ? {1'b0, p0_10} : {1'b1, p0_11};
  logic v1_6; assign v1_6 = a[23] | a[22] | a[21] | a[20];
  logic [1:0] p1_6; assign p1_6 = v0_12 ? {1'b0, p0_12} : {1'b1, p0_13};
  logic v1_7; assign v1_7 = a[19] | a[18] | a[17] | a[16];
  logic [1:0] p1_7; assign p1_7 = v0_14 ? {1'b0, p0_14} : {1'b1, p0_15};
  logic v1_8; assign v1_8 = a[15] | a[14] | a[13] | a[12];
  logic [1:0] p1_8; assign p1_8 = v0_16 ? {1'b0, p0_16} : {1'b1, p0_17};
  logic v1_9; assign v1_9 = a[11] | a[10] | a[9] | a[8];
  logic [1:0] p1_9; assign p1_9 = v0_18 ? {1'b0, p0_18} : {1'b1, p0_19};
  logic v1_10; assign v1_10 = a[7] | a[6] | a[5] | a[4];
  logic [1:0] p1_10; assign p1_10 = v0_20 ? {1'b0, p0_20} : {1'b1, p0_21};
  logic v1_11; assign v1_11 = a[3] | a[2] | a[1] | a[0];
  logic [1:0] p1_11; assign p1_11 = v0_22 ? {1'b0, p0_22} : {1'b1, p0_23};
  logic v1_12; assign v1_12 = 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [1:0] p1_12; assign p1_12 = v0_24 ? {1'b0, p0_24} : {1'b1, p0_25};
  logic v1_13; assign v1_13 = 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [1:0] p1_13; assign p1_13 = v0_26 ? {1'b0, p0_26} : {1'b1, p0_27};
  logic v1_14; assign v1_14 = 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [1:0] p1_14; assign p1_14 = v0_28 ? {1'b0, p0_28} : {1'b1, p0_29};
  logic v1_15; assign v1_15 = 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [1:0] p1_15; assign p1_15 = v0_30 ? {1'b0, p0_30} : {1'b1, p0_31};
  logic v2_0; assign v2_0 = a[47] | a[46] | a[45] | a[44] | a[43] | a[42] | a[41] | a[40];
  logic [2:0] p2_0; assign p2_0 = v1_0 ? {1'b0, p1_0} : {1'b1, p1_1};
  logic v2_1; assign v2_1 = a[39] | a[38] | a[37] | a[36] | a[35] | a[34] | a[33] | a[32];
  logic [2:0] p2_1; assign p2_1 = v1_2 ? {1'b0, p1_2} : {1'b1, p1_3};
  logic v2_2; assign v2_2 = a[31] | a[30] | a[29] | a[28] | a[27] | a[26] | a[25] | a[24];
  logic [2:0] p2_2; assign p2_2 = v1_4 ? {1'b0, p1_4} : {1'b1, p1_5};
  logic v2_3; assign v2_3 = a[23] | a[22] | a[21] | a[20] | a[19] | a[18] | a[17] | a[16];
  logic [2:0] p2_3; assign p2_3 = v1_6 ? {1'b0, p1_6} : {1'b1, p1_7};
  logic v2_4; assign v2_4 = a[15] | a[14] | a[13] | a[12] | a[11] | a[10] | a[9] | a[8];
  logic [2:0] p2_4; assign p2_4 = v1_8 ? {1'b0, p1_8} : {1'b1, p1_9};
  logic v2_5; assign v2_5 = a[7] | a[6] | a[5] | a[4] | a[3] | a[2] | a[1] | a[0];
  logic [2:0] p2_5; assign p2_5 = v1_10 ? {1'b0, p1_10} : {1'b1, p1_11};
  logic v2_6; assign v2_6 = 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [2:0] p2_6; assign p2_6 = v1_12 ? {1'b0, p1_12} : {1'b1, p1_13};
  logic v2_7; assign v2_7 = 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [2:0] p2_7; assign p2_7 = v1_14 ? {1'b0, p1_14} : {1'b1, p1_15};
  logic v3_0; assign v3_0 = a[47] | a[46] | a[45] | a[44] | a[43] | a[42] | a[41] | a[40] | a[39] | a[38] | a[37] | a[36] | a[35] | a[34] | a[33] | a[32];
  logic [3:0] p3_0; assign p3_0 = v2_0 ? {1'b0, p2_0} : {1'b1, p2_1};
  logic v3_1; assign v3_1 = a[31] | a[30] | a[29] | a[28] | a[27] | a[26] | a[25] | a[24] | a[23] | a[22] | a[21] | a[20] | a[19] | a[18] | a[17] | a[16];
  logic [3:0] p3_1; assign p3_1 = v2_2 ? {1'b0, p2_2} : {1'b1, p2_3};
  logic v3_2; assign v3_2 = a[15] | a[14] | a[13] | a[12] | a[11] | a[10] | a[9] | a[8] | a[7] | a[6] | a[5] | a[4] | a[3] | a[2] | a[1] | a[0];
  logic [3:0] p3_2; assign p3_2 = v2_4 ? {1'b0, p2_4} : {1'b1, p2_5};
  logic v3_3; assign v3_3 = 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [3:0] p3_3; assign p3_3 = v2_6 ? {1'b0, p2_6} : {1'b1, p2_7};
  logic v4_0; assign v4_0 = a[47] | a[46] | a[45] | a[44] | a[43] | a[42] | a[41] | a[40] | a[39] | a[38] | a[37] | a[36] | a[35] | a[34] | a[33] | a[32] | a[31] | a[30] | a[29] | a[28] | a[27] | a[26] | a[25] | a[24] | a[23] | a[22] | a[21] | a[20] | a[19] | a[18] | a[17] | a[16];
  logic [4:0] p4_0; assign p4_0 = v3_0 ? {1'b0, p3_0} : {1'b1, p3_1};
  logic v4_1; assign v4_1 = a[15] | a[14] | a[13] | a[12] | a[11] | a[10] | a[9] | a[8] | a[7] | a[6] | a[5] | a[4] | a[3] | a[2] | a[1] | a[0] | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [4:0] p4_1; assign p4_1 = v3_2 ? {1'b0, p3_2} : {1'b1, p3_3};
  logic v5_0; assign v5_0 = a[47] | a[46] | a[45] | a[44] | a[43] | a[42] | a[41] | a[40] | a[39] | a[38] | a[37] | a[36] | a[35] | a[34] | a[33] | a[32] | a[31] | a[30] | a[29] | a[28] | a[27] | a[26] | a[25] | a[24] | a[23] | a[22] | a[21] | a[20] | a[19] | a[18] | a[17] | a[16] | a[15] | a[14] | a[13] | a[12] | a[11] | a[10] | a[9] | a[8] | a[7] | a[6] | a[5] | a[4] | a[3] | a[2] | a[1] | a[0] | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [5:0] p5_0; assign p5_0 = v4_0 ? {1'b0, p4_0} : {1'b1, p4_1};
  assign n = v5_0 ? p5_0 : 6'd48;
endmodule


// fp significand adder (single_path): 1 path; operands ordered by magnitude before one shifter; align full_align on a barrel_mux_tree shifter, sticky by or_tree_shifted_out; significand adder ripple_carry; leading zeros by lza (lzd_cell_tree, single_indicator); normalize single_barrel on a barrel_mux_tree shifter; exponent path on ripple_carry adders; subnormals as normalized into the wide exponent; window of 4 guard bits below the larger operand's lsb (the significands are the unpacker's: 44 stored bits)
module fam_dot_lza_w43_p47261b205eb3 (
  input logic [60:0] xa,
  input logic [60:0] xb,
  input logic sub,
  output logic [60:0] y,
  output logic predict_zero
);
  logic [1:0] a_sp; assign a_sp = xa[60:59];
  logic a_s; assign a_s = xa[58];
  logic signed [8:0] a_e; assign a_e = $signed(xa[57:49]);
  logic [47:0] a_sig; assign a_sig = xa[48:1];
  logic a_st; assign a_st = xa[0];
  logic a_z; assign a_z = (a_sp == 2'd0) && (a_sig == 0) && !a_st;
  logic [60:0] xbs; assign xbs = {xb[60:59], xb[58] ^ sub, xb[57:0]};
  logic [1:0] b_sp; assign b_sp = xbs[60:59];
  logic b_s; assign b_s = xbs[58];
  logic signed [8:0] b_e; assign b_e = $signed(xbs[57:49]);
  logic [47:0] b_sig; assign b_sig = xbs[48:1];
  logic b_st; assign b_st = xbs[0];
  logic b_z; assign b_z = (b_sp == 2'd0) && (b_sig == 0) && !b_st;
  logic [5:0] a_lz;
  // operand a: leading zeros (pseudo-normalized representation)
  fam_count_lzd_pair_cell_binary_count_vflat_w48 u1 (.a(a_sig), .n(a_lz));
  logic [5:0] a_lzs; assign a_lzs = (a_sig == 0) ? 6'd0 : a_lz[5:0];
  logic [47:0] a_nsig;
  // operand a normalized
  fam_shift_barrel_mux_tree #(.W(48), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u2 (.a(a_sig), .amt(a_lzs), .op(3'd0), .y(a_nsig), .sticky());
  logic signed [8:0] a_lzx; assign a_lzx = $signed({{(9-6){1'b0}}, a_lz});
  logic [8:0] a_ne_nb; assign a_ne_nb = ~(a_lzx);
  logic signed [8:0] a_ne;
  // operand a: the exponent lowered by the count
  fam_adder_ripple_carry #(.W(9), .CHUNK(1), .FORM(0)) u3 (.a(a_e), .b(a_ne_nb), .cin(1'b1), .s(a_ne), .cout());
  logic [5:0] b_lz;
  // operand b: leading zeros (pseudo-normalized representation)
  fam_count_lzd_pair_cell_binary_count_vflat_w48 u4 (.a(b_sig), .n(b_lz));
  logic [5:0] b_lzs; assign b_lzs = (b_sig == 0) ? 6'd0 : b_lz[5:0];
  logic [47:0] b_nsig;
  // operand b normalized
  fam_shift_barrel_mux_tree #(.W(48), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u5 (.a(b_sig), .amt(b_lzs), .op(3'd0), .y(b_nsig), .sticky());
  logic signed [8:0] b_lzx; assign b_lzx = $signed({{(9-6){1'b0}}, b_lz});
  logic [8:0] b_ne_nb; assign b_ne_nb = ~(b_lzx);
  logic signed [8:0] b_ne;
  // operand b: the exponent lowered by the count
  fam_adder_ripple_carry #(.W(9), .CHUNK(1), .FORM(0)) u6 (.a(b_e), .b(b_ne_nb), .cin(1'b1), .s(b_ne), .cout());
  logic signed [9:0] eax; assign eax = $signed({a_ne[8], a_ne});
  logic signed [9:0] ebx; assign ebx = $signed({b_ne[8], b_ne});
  logic [9:0] d_nb; assign d_nb = ~(ebx);
  logic signed [9:0] d;
  // the exponent difference
  fam_adder_ripple_carry #(.W(10), .CHUNK(1), .FORM(0)) u7 (.a(eax), .b(d_nb), .cin(1'b1), .s(d), .cout());
  logic signed [9:0] zero_x; assign zero_x = 10'sd0;
  logic [9:0] dn_nb; assign dn_nb = ~(d);
  logic signed [9:0] dn;
  // the difference negated
  fam_adder_ripple_carry #(.W(10), .CHUNK(1), .FORM(0)) u8 (.a(zero_x), .b(dn_nb), .cin(1'b1), .s(dn), .cout());
  logic a_big; assign a_big = (d > 0) || (d == 0 && a_nsig >= b_nsig);
  logic [9:0] dabs; assign dabs = a_big ? d : dn;
  logic signed [8:0] e_big; assign e_big = a_big ? a_ne : b_ne;
  logic s_big; assign s_big = a_big ? a_s : b_s;
  logic eff_sub; assign eff_sub = a_s ^ b_s;
  logic [47:0] big_sig; assign big_sig = a_big ? a_nsig : b_nsig;
  logic [47:0] sml_sig; assign sml_sig = a_big ? b_nsig : a_nsig;
  logic big_st; assign big_st = a_big ? a_st : b_st;
  logic sml_st; assign sml_st = a_big ? b_st : a_st;
  logic [48:0] mb; assign mb = {1'b0, big_sig};
  logic [48:0] ms0; assign ms0 = {1'b0, sml_sig};
  logic far_f; assign far_f = 1'b1 && (dabs > 48);
  logic [5:0] amt_f; assign amt_f = (!(1'b1) || far_f) ? 6'd0 : dabs[5:0];
  logic [48:0] mssh_f;
  logic stk0_f;
  // align: the operand shifted right by the exponent difference
  fam_shift_barrel_mux_tree #(.W(49), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(1), .ORDER(0), .STICKY(1)) u9 (.a(ms0), .amt(amt_f), .op(3'd1), .y(mssh_f), .sticky(stk0_f));
  logic [48:0] m_f; assign m_f = far_f ? 49'd0 : mssh_f;
  logic stk_f; assign stk_f = far_f ? (sml_sig != 0) : stk0_f;
  logic stb_f; assign stb_f = sml_st | stk_f;
  logic [48:0] ms_f; assign ms_f = m_f;
  logic [48:0] bop_f; assign bop_f = eff_sub ? ~ms_f : ms_f;
  logic cin_f; assign cin_f = eff_sub ? ~stb_f : 1'b0;
  logic co_f;
  logic [48:0] r_f;
  // add: the significand adder (ripple_carry)
  fam_adder_ripple_carry #(.W(49), .CHUNK(1), .FORM(0)) u10 (.a(mb), .b(bop_f), .cin(cin_f), .s(r_f), .cout(co_f));
  logic st_f; assign st_f = big_st | stb_f;
  logic ovf_f; assign ovf_f = r_f[48];
  logic [47:0] sig0_f; assign sig0_f = ovf_f ? r_f[48:1] : r_f[47:0];
  logic st0_f; assign st0_f = st_f | (ovf_f & r_f[0]);
  logic signed [8:0] e0n_f_c; assign e0n_f_c = 9'sd0;
  logic signed [8:0] e0n_f;
  // normalize: the window's exponent origin
  fam_adder_ripple_carry #(.W(9), .CHUNK(1), .FORM(0)) u11 (.a(e_big), .b(e0n_f_c), .cin(1'b0), .s(e0n_f), .cout());
  logic signed [8:0] e0o_f_c; assign e0o_f_c = 9'sd1;
  logic signed [8:0] e0o_f;
  // normalize: the window's exponent origin after a carry out
  fam_adder_ripple_carry #(.W(9), .CHUNK(1), .FORM(0)) u12 (.a(e_big), .b(e0o_f_c), .cin(1'b0), .s(e0o_f), .cout());
  logic signed [8:0] e0_f; assign e0_f = ovf_f ? e0o_f : e0n_f;
  logic [48:0] t_f0; assign t_f0 = mb ^ bop_f;
  logic [48:0] g_f0; assign g_f0 = mb & bop_f;
  logic [48:0] z_f0; assign z_f0 = ~mb & ~bop_f;
  logic [48:0] f_f0;
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
  assign f_f0[26] = (t_f0[27] & ((g_f0[26] & ~z_f0[25]) | (z_f0[26] & ~g_f0[25]))) | (~t_f0[27] & ((z_f0[26] & ~z_f0[25]) | (g_f0[26] & ~g_f0[25])));
  assign f_f0[27] = (t_f0[28] & ((g_f0[27] & ~z_f0[26]) | (z_f0[27] & ~g_f0[26]))) | (~t_f0[28] & ((z_f0[27] & ~z_f0[26]) | (g_f0[27] & ~g_f0[26])));
  assign f_f0[28] = (t_f0[29] & ((g_f0[28] & ~z_f0[27]) | (z_f0[28] & ~g_f0[27]))) | (~t_f0[29] & ((z_f0[28] & ~z_f0[27]) | (g_f0[28] & ~g_f0[27])));
  assign f_f0[29] = (t_f0[30] & ((g_f0[29] & ~z_f0[28]) | (z_f0[29] & ~g_f0[28]))) | (~t_f0[30] & ((z_f0[29] & ~z_f0[28]) | (g_f0[29] & ~g_f0[28])));
  assign f_f0[30] = (t_f0[31] & ((g_f0[30] & ~z_f0[29]) | (z_f0[30] & ~g_f0[29]))) | (~t_f0[31] & ((z_f0[30] & ~z_f0[29]) | (g_f0[30] & ~g_f0[29])));
  assign f_f0[31] = (t_f0[32] & ((g_f0[31] & ~z_f0[30]) | (z_f0[31] & ~g_f0[30]))) | (~t_f0[32] & ((z_f0[31] & ~z_f0[30]) | (g_f0[31] & ~g_f0[30])));
  assign f_f0[32] = (t_f0[33] & ((g_f0[32] & ~z_f0[31]) | (z_f0[32] & ~g_f0[31]))) | (~t_f0[33] & ((z_f0[32] & ~z_f0[31]) | (g_f0[32] & ~g_f0[31])));
  assign f_f0[33] = (t_f0[34] & ((g_f0[33] & ~z_f0[32]) | (z_f0[33] & ~g_f0[32]))) | (~t_f0[34] & ((z_f0[33] & ~z_f0[32]) | (g_f0[33] & ~g_f0[32])));
  assign f_f0[34] = (t_f0[35] & ((g_f0[34] & ~z_f0[33]) | (z_f0[34] & ~g_f0[33]))) | (~t_f0[35] & ((z_f0[34] & ~z_f0[33]) | (g_f0[34] & ~g_f0[33])));
  assign f_f0[35] = (t_f0[36] & ((g_f0[35] & ~z_f0[34]) | (z_f0[35] & ~g_f0[34]))) | (~t_f0[36] & ((z_f0[35] & ~z_f0[34]) | (g_f0[35] & ~g_f0[34])));
  assign f_f0[36] = (t_f0[37] & ((g_f0[36] & ~z_f0[35]) | (z_f0[36] & ~g_f0[35]))) | (~t_f0[37] & ((z_f0[36] & ~z_f0[35]) | (g_f0[36] & ~g_f0[35])));
  assign f_f0[37] = (t_f0[38] & ((g_f0[37] & ~z_f0[36]) | (z_f0[37] & ~g_f0[36]))) | (~t_f0[38] & ((z_f0[37] & ~z_f0[36]) | (g_f0[37] & ~g_f0[36])));
  assign f_f0[38] = (t_f0[39] & ((g_f0[38] & ~z_f0[37]) | (z_f0[38] & ~g_f0[37]))) | (~t_f0[39] & ((z_f0[38] & ~z_f0[37]) | (g_f0[38] & ~g_f0[37])));
  assign f_f0[39] = (t_f0[40] & ((g_f0[39] & ~z_f0[38]) | (z_f0[39] & ~g_f0[38]))) | (~t_f0[40] & ((z_f0[39] & ~z_f0[38]) | (g_f0[39] & ~g_f0[38])));
  assign f_f0[40] = (t_f0[41] & ((g_f0[40] & ~z_f0[39]) | (z_f0[40] & ~g_f0[39]))) | (~t_f0[41] & ((z_f0[40] & ~z_f0[39]) | (g_f0[40] & ~g_f0[39])));
  assign f_f0[41] = (t_f0[42] & ((g_f0[41] & ~z_f0[40]) | (z_f0[41] & ~g_f0[40]))) | (~t_f0[42] & ((z_f0[41] & ~z_f0[40]) | (g_f0[41] & ~g_f0[40])));
  assign f_f0[42] = (t_f0[43] & ((g_f0[42] & ~z_f0[41]) | (z_f0[42] & ~g_f0[41]))) | (~t_f0[43] & ((z_f0[42] & ~z_f0[41]) | (g_f0[42] & ~g_f0[41])));
  assign f_f0[43] = (t_f0[44] & ((g_f0[43] & ~z_f0[42]) | (z_f0[43] & ~g_f0[42]))) | (~t_f0[44] & ((z_f0[43] & ~z_f0[42]) | (g_f0[43] & ~g_f0[42])));
  assign f_f0[44] = (t_f0[45] & ((g_f0[44] & ~z_f0[43]) | (z_f0[44] & ~g_f0[43]))) | (~t_f0[45] & ((z_f0[44] & ~z_f0[43]) | (g_f0[44] & ~g_f0[43])));
  assign f_f0[45] = (t_f0[46] & ((g_f0[45] & ~z_f0[44]) | (z_f0[45] & ~g_f0[44]))) | (~t_f0[46] & ((z_f0[45] & ~z_f0[44]) | (g_f0[45] & ~g_f0[44])));
  assign f_f0[46] = (t_f0[47] & ((g_f0[46] & ~z_f0[45]) | (z_f0[46] & ~g_f0[45]))) | (~t_f0[47] & ((z_f0[46] & ~z_f0[45]) | (g_f0[46] & ~g_f0[45])));
  assign f_f0[47] = (t_f0[48] & ((g_f0[47] & ~z_f0[46]) | (z_f0[47] & ~g_f0[46]))) | (~t_f0[48] & ((z_f0[47] & ~z_f0[46]) | (g_f0[47] & ~g_f0[46])));
  assign f_f0[48] = (1'b0 & ((g_f0[48] & ~z_f0[47]) | (z_f0[48] & ~g_f0[47]))) | (~1'b0 & ((z_f0[48] & ~z_f0[47]) | (g_f0[48] & ~g_f0[47])));
  logic [47:0] fw_f0; assign fw_f0 = ovf_f ? f_f0[48:1] : f_f0[47:0];
  logic [47:0] fws_f; assign fws_f = fw_f0;
  logic [5:0] lzp_f;
  // normalize: leading zeros of the indicator string
  fam_count_lzd_pair_cell_binary_count_vflat_w48 u13 (.a(fws_f), .n(lzp_f));
  logic [5:0] lzs_f; assign lzs_f = (!eff_sub || fws_f == 0) ? 6'd0 : lzp_f[5:0];
  logic fz_f; assign fz_f = fws_f == 0;
  logic [47:0] sign_f;
  // normalize: the normalize shifter
  fam_shift_barrel_mux_tree #(.W(48), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u14 (.a(sig0_f), .amt(lzs_f), .op(3'd0), .y(sign_f), .sticky());
  logic signed [8:0] lzx_f; assign lzx_f = $signed({{(9-6){1'b0}}, lzs_f});
  logic [8:0] en_f_nb; assign en_f_nb = ~(lzx_f);
  logic signed [8:0] en_f;
  // normalize: the exponent lowered by the normalize count
  fam_adder_ripple_carry #(.W(9), .CHUNK(1), .FORM(0)) u15 (.a(e0_f), .b(en_f_nb), .cin(1'b1), .s(en_f), .cout());
  logic fix_f; assign fix_f = ~sign_f[47] && (sign_f != 0);
  logic [47:0] sigf_f; assign sigf_f = fix_f ? {sign_f[46:0], 1'b0} : sign_f;
  logic signed [8:0] enm_f_c; assign enm_f_c = -9'sd1;
  logic signed [8:0] enm_f;
  // normalize: the exponent of the corrected position
  fam_adder_ripple_carry #(.W(9), .CHUNK(1), .FORM(0)) u16 (.a(en_f), .b(enm_f_c), .cin(1'b0), .s(enm_f), .cout());
  logic signed [8:0] ef_f; assign ef_f = fix_f ? enm_f : en_f;
  logic zero_f; assign zero_f = (sigf_f == 0) && !st0_f;
  logic sr_f; assign sr_f = zero_f ? 1'b0 : s_big;
  logic [60:0] y_f; assign y_f = {2'd0, sr_f, ef_f, sigf_f, st0_f};
  logic both_inf; assign both_inf = (a_sp == 2'd2) && (b_sp == 2'd2);
  logic [60:0] y_sp; assign y_sp = (a_sp == 2'd1 || b_sp == 2'd1) ? {2'd1, 1'b0, 9'sd0, 48'd0, 1'b0} : both_inf ? ((a_s == b_s) ? {2'd2, a_s, 9'sd0, 48'd0, 1'b0} : {2'd1, 1'b0, 9'sd0, 48'd0, 1'b0}) : (a_sp == 2'd2) ? {2'd2, a_s, 9'sd0, 48'd0, 1'b0} : (b_sp == 2'd2) ? {2'd2, b_s, 9'sd0, 48'd0, 1'b0} : a_z ? xbs : b_z ? xa : y_f;
  assign y = y_sp;
  assign predict_zero = a_z ? b_z : b_z ? a_z : zero_f;
endmodule

// fp comparator (integer_compare_on_bits, prefix_comparator)
module fam_fp_cmp_integer_compare_on_bits_x26e16s11_pa61fc99a71d5 (
  input logic [45:0] xa,
  input logic [45:0] xb,
  output logic lt,
  output logic eq
);
  logic [1:0] a_sp; assign a_sp = xa[45:44];
  logic a_s; assign a_s = xa[43];
  logic signed [15:0] a_e; assign a_e = $signed(xa[42:27]);
  logic [25:0] a_sig; assign a_sig = xa[26:1];
  logic a_st; assign a_st = xa[0];
  logic a_z; assign a_z = (a_sp == 2'd0) && (a_sig == 0) && !a_st;
  logic [1:0] b_sp; assign b_sp = xb[45:44];
  logic b_s; assign b_s = xb[43];
  logic signed [15:0] b_e; assign b_e = $signed(xb[42:27]);
  logic [25:0] b_sig; assign b_sig = xb[26:1];
  logic b_st; assign b_st = xb[0];
  logic b_z; assign b_z = (b_sp == 2'd0) && (b_sig == 0) && !b_st;
  logic sa; assign sa = a_s && !a_z;
  logic sb; assign sb = b_s && !b_z;
  logic [15:0] aeu; assign aeu = {~a_e[15], a_e[14:0]};
  logic [15:0] beu; assign beu = {~b_e[15], b_e[14:0]};
  logic [42:0] ma; assign ma = {aeu, a_sig, a_st};
  logic [42:0] mb; assign mb = {beu, b_sig, b_st};
  logic mlt;
  logic meq;
  // the magnitude words compared as integers (prefix_comparator)
  fam_cmp_prefix_comparator #(.W(43), .SIGNED(0), .STRUCTURE(0), .RADIX(2)) u1 (.a(ma), .b(mb), .lt(mlt), .eq(meq));
  logic mag_lt; assign mag_lt = a_z ? 1'b1 : b_z ? 1'b0 : mlt;
  logic fin_eq; assign fin_eq = (a_z || b_z) ? (a_z && b_z) : ((a_s == b_s) && meq);
  logic fin_lt; assign fin_lt = (a_z && b_z) ? 1'b0 : (sa != sb) ? sa : (sa ? (!mag_lt && !fin_eq) : mag_lt);
  logic inf_lt; assign inf_lt = (a_sp == 2'd2 && b_sp == 2'd2) ? (a_s && !b_s) : (a_sp == 2'd2) ? a_s : !b_s;
  logic inf_eq; assign inf_eq = (a_sp == b_sp) && (a_s == b_s);
  logic any_inf; assign any_inf = (a_sp == 2'd2) || (b_sp == 2'd2);
  logic nan_any; assign nan_any = (a_sp == 2'd1) || (b_sp == 2'd1);
  assign lt = !nan_any && (any_inf ? inf_lt : fin_lt);
  assign eq = !nan_any && (any_inf ? inf_eq : fin_eq);
endmodule


// fp fused multiply-add (classic_fma): the mode's adder, its multiplier and the fused ops fmadd, fmsub, fnmsub, fnmadd through one datapath fam_fp_fma_core_classic_fma_x26e16s11_p82fa36d18aa0 under the op code fop (0 fadd, 1 fsub, 2 fmul, 3 fmadd, 4 fmsub, 5 fnmsub, 6 fnmadd): fadd is 1 * xa + xb, fmul is xa * xb + (a zero of the product's sign), a fused op negates xa for the negated product and xc for the negated addend; the window sum's negation by end_around_carry; the significand multiplier behavioral_star; the specials as the engine orders them for each op
module fam_fp_fma_classic_fma_x26e16s11_p0de96c130150 (
  input logic [45:0] xa,
  input logic [45:0] xb,
  input logic [45:0] xc,
  input logic [2:0] fop,
  output logic [45:0] y
);
  logic [1:0] a_sp; assign a_sp = xa[45:44];
  logic a_s; assign a_s = xa[43];
  logic signed [15:0] a_e; assign a_e = $signed(xa[42:27]);
  logic [25:0] a_sig; assign a_sig = xa[26:1];
  logic a_st; assign a_st = xa[0];
  logic a_z; assign a_z = (a_sp == 2'd0) && (a_sig == 0) && !a_st;
  logic [1:0] b_sp; assign b_sp = xb[45:44];
  logic b_s; assign b_s = xb[43];
  logic signed [15:0] b_e; assign b_e = $signed(xb[42:27]);
  logic [25:0] b_sig; assign b_sig = xb[26:1];
  logic b_st; assign b_st = xb[0];
  logic b_z; assign b_z = (b_sp == 2'd0) && (b_sig == 0) && !b_st;
  logic is_add; assign is_add = fop[2:1] == 2'b00;
  logic is_mul; assign is_mul = fop == 3'd2;
  logic neg_p; assign neg_p = (fop == 3'd5) || (fop == 3'd6);
  logic neg_c; assign neg_c = (fop == 3'd1) || (fop == 3'd4) || (fop == 3'd6);
  logic [45:0] xan; assign xan = {xa[45:44], xa[43] ^ neg_p, xa[42:0]};
  logic [45:0] addend; assign addend = is_add ? xb : xc;
  logic [45:0] xcn; assign xcn = {addend[45:44], addend[43] ^ neg_c, addend[42:0]};
  logic ps; assign ps = a_s ^ b_s;
  logic [45:0] fa; assign fa = is_add ? {2'd0, 1'b0, -16'sd10, 26'd1024, 1'b0} : xan;
  logic [45:0] fb; assign fb = is_add ? xa : xb;
  logic [45:0] fc; assign fc = is_mul ? {2'd0, ps, 16'sd0, 26'd0, 1'b0} : xcn;
  logic [45:0] yf;
  // the fused datapath: fc + fa * fb
  fam_fp_fma_core_classic_fma_x26e16s11_p82fa36d18aa0 u_fma (.xa(fa), .xb(fb), .xc(fc), .y(yf));
  logic [1:0] fa_sp; assign fa_sp = fa[45:44];
  logic fa_s; assign fa_s = fa[43];
  logic signed [15:0] fa_e; assign fa_e = $signed(fa[42:27]);
  logic [25:0] fa_sig; assign fa_sig = fa[26:1];
  logic fa_st; assign fa_st = fa[0];
  logic fa_z; assign fa_z = (fa_sp == 2'd0) && (fa_sig == 0) && !fa_st;
  logic [1:0] fb_sp; assign fb_sp = fb[45:44];
  logic fb_s; assign fb_s = fb[43];
  logic signed [15:0] fb_e; assign fb_e = $signed(fb[42:27]);
  logic [25:0] fb_sig; assign fb_sig = fb[26:1];
  logic fb_st; assign fb_st = fb[0];
  logic fb_z; assign fb_z = (fb_sp == 2'd0) && (fb_sig == 0) && !fb_st;
  logic [1:0] fc_sp; assign fc_sp = fc[45:44];
  logic fc_s; assign fc_s = fc[43];
  logic signed [15:0] fc_e; assign fc_e = $signed(fc[42:27]);
  logic [25:0] fc_sig; assign fc_sig = fc[26:1];
  logic fc_st; assign fc_st = fc[0];
  logic fc_z; assign fc_z = (fc_sp == 2'd0) && (fc_sig == 0) && !fc_st;
  logic p_nan; assign p_nan = (fa_sp == 2'd1) || (fb_sp == 2'd1);
  logic p_inf; assign p_inf = (fa_sp == 2'd2) || (fb_sp == 2'd2);
  logic p_inv; assign p_inv = p_inf && ((fa_sp == 2'd0 && fa_z) || (fb_sp == 2'd0 && fb_z));
  logic fps; assign fps = fa_s ^ fb_s;
  logic c_nan; assign c_nan = fc_sp == 2'd1;
  logic c_inf; assign c_inf = fc_sp == 2'd2;
  logic [45:0] y_sp; assign y_sp = (p_nan || c_nan || p_inv) ? {2'd1, 1'b0, 16'sd0, 26'd0, 1'b0} : (p_inf && c_inf && (fps != fc_s)) ? {2'd1, 1'b0, 16'sd0, 26'd0, 1'b0} : p_inf ? {2'd2, fps, 16'sd0, 26'd0, 1'b0} : c_inf ? {2'd2, fc_s, 16'sd0, 26'd0, 1'b0} : yf;
  assign y = y_sp;
endmodule


// fused multiply-add (classic_fma): the 11-bit addend aligned against the 22-bit product over a 43-bit window (7 guard bits below the product for the X's 26-bit significand; a sticky lsb holds what leaves it), the significand multiplier behavioral_star, the window adder ripple_carry, negation by end_around_carry, leading zeros by lza, one normalize; meets the fused contract
module fam_fp_fma_core_classic_fma_x26e16s11_p82fa36d18aa0 (
  input logic [45:0] xa,
  input logic [45:0] xb,
  input logic [45:0] xc,
  output logic [45:0] y
);
  logic [1:0] a_sp; assign a_sp = xa[45:44];
  logic a_s; assign a_s = xa[43];
  logic signed [15:0] a_e; assign a_e = $signed(xa[42:27]);
  logic [25:0] a_sig; assign a_sig = xa[26:1];
  logic a_st; assign a_st = xa[0];
  logic a_z; assign a_z = (a_sp == 2'd0) && (a_sig == 0) && !a_st;
  logic [1:0] b_sp; assign b_sp = xb[45:44];
  logic b_s; assign b_s = xb[43];
  logic signed [15:0] b_e; assign b_e = $signed(xb[42:27]);
  logic [25:0] b_sig; assign b_sig = xb[26:1];
  logic b_st; assign b_st = xb[0];
  logic b_z; assign b_z = (b_sp == 2'd0) && (b_sig == 0) && !b_st;
  logic [1:0] c_sp; assign c_sp = xc[45:44];
  logic c_s; assign c_s = xc[43];
  logic signed [15:0] c_e; assign c_e = $signed(xc[42:27]);
  logic [25:0] c_sig; assign c_sig = xc[26:1];
  logic c_st; assign c_st = xc[0];
  logic c_z; assign c_z = (c_sp == 2'd0) && (c_sig == 0) && !c_st;
  logic [10:0] sa0; assign sa0 = a_sig[10:0];
  logic [3:0] a_lzs; assign a_lzs = 4'd0;
  logic [10:0] sa; assign sa = sa0;
  logic signed [18:0] ea; assign ea = $signed({{3{a_e[15]}}, a_e}) - $signed({{(19-4){1'b0}}, a_lzs});
  logic [10:0] sb0; assign sb0 = b_sig[10:0];
  logic [3:0] b_lzs; assign b_lzs = 4'd0;
  logic [10:0] sb; assign sb = sb0;
  logic signed [18:0] eb; assign eb = $signed({{3{b_e[15]}}, b_e}) - $signed({{(19-4){1'b0}}, b_lzs});
  logic [21:0] p_mul;
  assign p_mul = sa * sb;
  logic pure_add; assign pure_add = !a_s && (ea == -19'sd10) && (sa == 11'd1024);
  logic [21:0] p; assign p = pure_add ? {1'b0, sb, 10'd0} : p_mul;
  logic signed [18:0] ep; assign ep = ea + eb;
  logic sp; assign sp = a_s ^ b_s;
  logic [10:0] sc0; assign sc0 = c_sig[10:0];
  logic signed [18:0] ec0; assign ec0 = $signed({{3{c_e[15]}}, c_e});
  logic [3:0] c_lzs; assign c_lzs = 4'd0;
  logic [10:0] sc; assign sc = sc0;
  logic signed [18:0] ec; assign ec = ec0 - $signed({{(19-4){1'b0}}, c_lzs});
  logic eff_sub; assign eff_sub = sp ^ c_s;
  logic signed [18:0] ep_e; assign ep_e = (p == 0) ? (ec - 19'sd24) : ep;
  logic signed [18:0] d; assign d = ec - ep_e;
  logic signed [18:0] shc0; assign shc0 = 19'sd24 - d;
  logic signed [18:0] shc; assign shc = (sc0 == 0) ? 19'sd0 : shc0;
  logic c_case; assign c_case = shc >= 0;
  logic signed [18:0] ef; assign ef = (c_case ? ep_e : (ep_e - shc)) - 19'sd7;
  logic [42:0] w0c; assign w0c = {1'b0, sc, 31'd0};
  logic [42:0] w0p; assign w0p = {{(43-22-7){1'b0}}, p, 7'd0};
  logic signed [18:0] amt0; assign amt0 = c_case ? shc : (-shc);
  logic far; assign far = amt0 >= 43;
  logic [5:0] amt; assign amt = far ? 6'd0 : amt0[5:0];
  logic [42:0] wsel; assign wsel = c_case ? w0c : w0p;
  logic [42:0] wsh;
  logic wshift_st;
  // the alignment shifter (the addend, or the product when the addend is far larger)
  fam_shift_barrel_mux_tree #(.W(43), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u1 (.a(wsel), .amt(amt), .op(3'd1), .y(wsh), .sticky());
  assign wshift_st = |(wsel & ((3'd1 == 3'd0) ? ~({43{1'b1}} >> amt) : ~({43{1'b1}} << amt)));
  logic wst; assign wst = far ? (|wsel) : wshift_st;
  logic [42:0] wal; assign wal = far ? 43'd0 : wsh;
  logic [42:0] c_al; assign c_al = c_case ? wal : w0c;
  logic [42:0] p_al; assign p_al = c_case ? w0p : wal;
  logic st_c; assign st_c = c_case ? wst : 1'b0;
  logic st_p; assign st_p = c_case ? 1'b0 : wst;
  logic [43:0] X; assign X = {p_al, st_p};
  logic [43:0] Y; assign Y = {c_al, st_c};
  logic [43:0] f_yop; assign f_yop = eff_sub ? ~Y : Y;
  logic [43:0] f_r;
  logic f_co;
  // f: X + Y, or X + ~Y (the end-around carry)
  fam_adder_ripple_carry #(.W(44), .CHUNK(1), .FORM(0)) u2 (.a(X), .b(f_yop), .cin(1'b0), .s(f_r), .cout(f_co));
  logic [43:0] f_inc;
  logic f_ico;
  // f: the end-around carry added back
  fam_incr_prefix_and #(.W(44), .STRUCTURE(1), .B(4), .TOPO(0)) u3 (.a(f_r), .cin(f_co), .s(f_inc), .cout(f_ico));
  logic f_neg; assign f_neg = eff_sub && !f_co;
  logic [43:0] f_mag; assign f_mag = eff_sub ? (f_co ? f_inc : ~f_r) : f_r;
  logic f_s; assign f_s = f_neg ? c_s : sp;
  logic [42:0] f_v; assign f_v = f_mag[43:1];
  logic f_stv; assign f_stv = f_mag[0];
  logic [1:0] f_lc; assign f_lc = f_neg ? (2'd1 + {1'b0, X[0] & f_yop[0]}) : eff_sub ? {1'b0, X[0] | f_yop[0]} : {1'b0, X[0] & f_yop[0]};
  logic [42:0] f_lx; assign f_lx = X[43:1];
  logic [42:0] f_ly; assign f_ly = f_yop[43:1];
  logic fx_neg; assign fx_neg = f_s;
  logic [42:0] fx_mag; assign fx_mag = f_v;
  logic fx_look_cin; assign fx_look_cin = f_v[0] ^ f_lx[0] ^ f_ly[0];
  logic signed [43:0] fx_look_a; assign fx_look_a = {f_lx[42], f_lx};
  logic [1:0] fx_look_adj; assign fx_look_adj = f_lc;
  logic signed [43:0] fx_look_b; assign fx_look_b = $signed({f_ly[42], f_ly}) + $signed({{(44-2){1'b0}}, fx_look_adj});
  logic [43:0] fx_look_am; assign fx_look_am = fx_look_a[43] ? -fx_look_a : fx_look_a;
  logic [5:0] fx_look_a_lz;
  // normalize a real lookahead operand
  fam_count_lzd_pair_cell_binary_count_vflat_w44 u4 (.a(fx_look_am), .n(fx_look_a_lz));
  logic [5:0] fx_look_a_count; assign fx_look_a_count = (fx_look_am == 0) ? 0 : fx_look_a_lz[5:0];
  logic [43:0] fx_look_a_normalized;
  // the lookahead operand's declared normalizer
  fam_shift_barrel_mux_tree #(.W(44), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u5 (.a(fx_look_am), .amt(fx_look_a_count), .op(3'd0), .y(fx_look_a_normalized), .sticky());
  logic signed [8:0] fx_look_a_exp; assign fx_look_a_exp = -$signed({1'b0, fx_look_a_count});
  logic [60:0] fx_look_ax; assign fx_look_ax = {2'd0, fx_look_a[43], fx_look_a_exp, 4'd0, fx_look_a_normalized, 1'b0};
  logic [43:0] fx_look_bm; assign fx_look_bm = fx_look_b[43] ? -fx_look_b : fx_look_b;
  logic [5:0] fx_look_b_lz;
  // normalize a real lookahead operand
  fam_count_lzd_pair_cell_binary_count_vflat_w44 u6 (.a(fx_look_bm), .n(fx_look_b_lz));
  logic [5:0] fx_look_b_count; assign fx_look_b_count = (fx_look_bm == 0) ? 0 : fx_look_b_lz[5:0];
  logic [43:0] fx_look_b_normalized;
  // the lookahead operand's declared normalizer
  fam_shift_barrel_mux_tree #(.W(44), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u7 (.a(fx_look_bm), .amt(fx_look_b_count), .op(3'd0), .y(fx_look_b_normalized), .sticky());
  logic signed [8:0] fx_look_b_exp; assign fx_look_b_exp = -$signed({1'b0, fx_look_b_count});
  logic [60:0] fx_look_bx; assign fx_look_bx = {2'd0, fx_look_b[43], fx_look_b_exp, 4'd0, fx_look_b_normalized, 1'b0};
  logic [60:0] fx_look_result;
  logic fx_look_zero;
  fam_dot_lza_w43_p47261b205eb3 u8 (.xa(fx_look_ax), .xb(fx_look_bx), .sub(1'b0), .y(fx_look_result), .predict_zero(fx_look_zero));
  logic signed [8:0] fx_look_exp; assign fx_look_exp = $signed(fx_look_result[57:49]);
  logic fx_look_bypass; assign fx_look_bypass = (fx_look_am == 0) || (fx_look_bm == 0);
  logic signed [8:0] fx_look_shift; assign fx_look_shift = (fx_look_bypass ? -9'sd1 : -9'sd5) - fx_look_exp;
  logic [5:0] fx_lzs; assign fx_lzs = (fx_mag == 0 || fx_look_shift < 0) ? 0 : (fx_look_shift >= 43) ? 6'd42 : fx_look_shift[5:0];
  logic [6:0] fx_lz; assign fx_lz = {1'b0, fx_lzs};
  logic [42:0] fx_nm_shifted;
  // normalize the actual reduction result by its selected lookahead shift
  fam_shift_barrel_mux_tree #(.W(43), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u9 (.a(fx_mag), .amt(fx_lzs), .op(3'd0), .y(fx_nm_shifted), .sticky());
  logic [42:0] fx_nm; assign fx_nm = fx_look_zero ? 43'd0 : fx_nm_shifted;
  logic [25:0] fx_sig; assign fx_sig = fx_nm[42:17];
  logic fx_st; assign fx_st = (|fx_nm[16:0]) | f_stv;
  logic signed [18:0] fx_e0; assign fx_e0 = ef + 19'sd17 - $signed({{(19-7){1'b0}}, fx_lz});
  logic signed [15:0] fx_e; assign fx_e = fx_e0[15:0];
  logic fx_zero; assign fx_zero = (fx_mag == 0) && !(f_stv);
  logic [45:0] y_fx; assign y_fx = fx_zero ? {2'd0, 1'b0, 16'sd0, 26'd0, 1'b0} : {2'd0, fx_neg, fx_e, fx_sig, fx_st};
  assign y = y_fx;
endmodule


// fused multiply-add (multipath_fma): the 11-bit addend aligned against the 22-bit product over a 43-bit window (7 guard bits below the product for the X's 26-bit significand; a sticky lsb holds what leaves it), the significand multiplier behavioral_star, the window adder ripple_carry, negation by end_around_carry, leading zeros by lza, 3 paths selected by exponent_difference, one normalize; meets the fused contract
module fam_fp_fma_core_multipath_fma_x26e16s11_p1221e7100196 (
  input logic [45:0] xa,
  input logic [45:0] xb,
  input logic [45:0] xc,
  output logic [45:0] y
);
  logic [1:0] a_sp; assign a_sp = xa[45:44];
  logic a_s; assign a_s = xa[43];
  logic signed [15:0] a_e; assign a_e = $signed(xa[42:27]);
  logic [25:0] a_sig; assign a_sig = xa[26:1];
  logic a_st; assign a_st = xa[0];
  logic a_z; assign a_z = (a_sp == 2'd0) && (a_sig == 0) && !a_st;
  logic [1:0] b_sp; assign b_sp = xb[45:44];
  logic b_s; assign b_s = xb[43];
  logic signed [15:0] b_e; assign b_e = $signed(xb[42:27]);
  logic [25:0] b_sig; assign b_sig = xb[26:1];
  logic b_st; assign b_st = xb[0];
  logic b_z; assign b_z = (b_sp == 2'd0) && (b_sig == 0) && !b_st;
  logic [1:0] c_sp; assign c_sp = xc[45:44];
  logic c_s; assign c_s = xc[43];
  logic signed [15:0] c_e; assign c_e = $signed(xc[42:27]);
  logic [25:0] c_sig; assign c_sig = xc[26:1];
  logic c_st; assign c_st = xc[0];
  logic c_z; assign c_z = (c_sp == 2'd0) && (c_sig == 0) && !c_st;
  logic [10:0] sa0; assign sa0 = a_sig[10:0];
  logic [3:0] a_lzs; assign a_lzs = 4'd0;
  logic [10:0] sa; assign sa = sa0;
  logic signed [18:0] ea; assign ea = $signed({{3{a_e[15]}}, a_e}) - $signed({{(19-4){1'b0}}, a_lzs});
  logic [10:0] sb0; assign sb0 = b_sig[10:0];
  logic [3:0] b_lzs; assign b_lzs = 4'd0;
  logic [10:0] sb; assign sb = sb0;
  logic signed [18:0] eb; assign eb = $signed({{3{b_e[15]}}, b_e}) - $signed({{(19-4){1'b0}}, b_lzs});
  logic [21:0] p;
  assign p = sa * sb;
  logic signed [18:0] ep; assign ep = ea + eb;
  logic sp; assign sp = a_s ^ b_s;
  logic [10:0] sc0; assign sc0 = c_sig[10:0];
  logic signed [18:0] ec0; assign ec0 = $signed({{3{c_e[15]}}, c_e});
  logic [3:0] c_lzs; assign c_lzs = 4'd0;
  logic [10:0] sc; assign sc = sc0;
  logic signed [18:0] ec; assign ec = ec0 - $signed({{(19-4){1'b0}}, c_lzs});
  logic eff_sub; assign eff_sub = sp ^ c_s;
  logic signed [18:0] ep_e; assign ep_e = (p == 0) ? (ec - 19'sd24) : ep;
  logic signed [18:0] d; assign d = ec - ep_e;
  logic signed [18:0] shc0; assign shc0 = 19'sd24 - d;
  logic signed [18:0] shc; assign shc = (sc0 == 0) ? 19'sd0 : shc0;
  logic c_case; assign c_case = shc >= 0;
  logic signed [18:0] ef; assign ef = (c_case ? ep_e : (ep_e - shc)) - 19'sd7;
  logic [42:0] w0c; assign w0c = {1'b0, sc, 31'd0};
  logic [42:0] w0p; assign w0p = {{(43-22-7){1'b0}}, p, 7'd0};
  logic signed [18:0] amt0; assign amt0 = c_case ? shc : (-shc);
  logic far; assign far = amt0 >= 43;
  logic [5:0] amt; assign amt = far ? 6'd0 : amt0[5:0];
  logic [42:0] wsel; assign wsel = c_case ? w0c : w0p;
  logic [42:0] wsh;
  logic wshift_st;
  // the alignment shifter (the addend, or the product when the addend is far larger)
  fam_shift_barrel_mux_tree #(.W(43), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u1 (.a(wsel), .amt(amt), .op(3'd1), .y(wsh), .sticky());
  assign wshift_st = |(wsel & ((3'd1 == 3'd0) ? ~({43{1'b1}} >> amt) : ~({43{1'b1}} << amt)));
  logic wst; assign wst = far ? (|wsel) : wshift_st;
  logic [42:0] wal; assign wal = far ? 43'd0 : wsh;
  logic [42:0] c_al; assign c_al = c_case ? wal : w0c;
  logic [42:0] p_al; assign p_al = c_case ? w0p : wal;
  logic st_c; assign st_c = c_case ? wst : 1'b0;
  logic st_p; assign st_p = c_case ? 1'b0 : wst;
  logic [43:0] X; assign X = {p_al, st_p};
  logic [43:0] Y; assign Y = {c_al, st_c};
  logic signed [18:0] msb_d; assign msb_d = (ec + 19'sd10) - (ep + 19'sd21);
  logic close_e; assign close_e = eff_sub && (msb_d <= 1) && (msb_d >= -1);
  logic close; assign close = close_e;
  logic [43:0] cl_yop; assign cl_yop = eff_sub ? ~Y : Y;
  logic [43:0] cl_r;
  logic cl_co;
  // cl: X + Y, or X + ~Y (the end-around carry)
  fam_adder_ripple_carry #(.W(44), .CHUNK(1), .FORM(0)) u2 (.a(X), .b(cl_yop), .cin(1'b0), .s(cl_r), .cout(cl_co));
  logic [43:0] cl_inc;
  logic cl_ico;
  // cl: the end-around carry added back
  fam_incr_prefix_and #(.W(44), .STRUCTURE(1), .B(4), .TOPO(0)) u3 (.a(cl_r), .cin(cl_co), .s(cl_inc), .cout(cl_ico));
  logic cl_neg; assign cl_neg = eff_sub && !cl_co;
  logic [43:0] cl_mag; assign cl_mag = eff_sub ? (cl_co ? cl_inc : ~cl_r) : cl_r;
  logic cl_s; assign cl_s = cl_neg ? c_s : sp;
  logic [42:0] cl_v; assign cl_v = cl_mag[43:1];
  logic cl_stv; assign cl_stv = cl_mag[0];
  logic [1:0] cl_lc; assign cl_lc = cl_neg ? (2'd1 + {1'b0, X[0] & cl_yop[0]}) : eff_sub ? {1'b0, X[0] | cl_yop[0]} : {1'b0, X[0] & cl_yop[0]};
  logic [42:0] cl_lx; assign cl_lx = X[43:1];
  logic [42:0] cl_ly; assign cl_ly = cl_yop[43:1];
  logic clx_neg; assign clx_neg = cl_s;
  logic [42:0] clx_mag; assign clx_mag = cl_v;
  logic clx_look_cin; assign clx_look_cin = cl_v[0] ^ cl_lx[0] ^ cl_ly[0];
  logic signed [43:0] clx_look_a; assign clx_look_a = {cl_lx[42], cl_lx};
  logic [1:0] clx_look_adj; assign clx_look_adj = cl_lc;
  logic signed [43:0] clx_look_b; assign clx_look_b = $signed({cl_ly[42], cl_ly}) + $signed({{(44-2){1'b0}}, clx_look_adj});
  logic [43:0] clx_look_am; assign clx_look_am = clx_look_a[43] ? -clx_look_a : clx_look_a;
  logic [5:0] clx_look_a_lz;
  // normalize a real lookahead operand
  fam_count_lzd_pair_cell_binary_count_vflat_w44 u4 (.a(clx_look_am), .n(clx_look_a_lz));
  logic [5:0] clx_look_a_count; assign clx_look_a_count = (clx_look_am == 0) ? 0 : clx_look_a_lz[5:0];
  logic [43:0] clx_look_a_normalized;
  // the lookahead operand's declared normalizer
  fam_shift_barrel_mux_tree #(.W(44), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u5 (.a(clx_look_am), .amt(clx_look_a_count), .op(3'd0), .y(clx_look_a_normalized), .sticky());
  logic signed [8:0] clx_look_a_exp; assign clx_look_a_exp = -$signed({1'b0, clx_look_a_count});
  logic [60:0] clx_look_ax; assign clx_look_ax = {2'd0, clx_look_a[43], clx_look_a_exp, 4'd0, clx_look_a_normalized, 1'b0};
  logic [43:0] clx_look_bm; assign clx_look_bm = clx_look_b[43] ? -clx_look_b : clx_look_b;
  logic [5:0] clx_look_b_lz;
  // normalize a real lookahead operand
  fam_count_lzd_pair_cell_binary_count_vflat_w44 u6 (.a(clx_look_bm), .n(clx_look_b_lz));
  logic [5:0] clx_look_b_count; assign clx_look_b_count = (clx_look_bm == 0) ? 0 : clx_look_b_lz[5:0];
  logic [43:0] clx_look_b_normalized;
  // the lookahead operand's declared normalizer
  fam_shift_barrel_mux_tree #(.W(44), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u7 (.a(clx_look_bm), .amt(clx_look_b_count), .op(3'd0), .y(clx_look_b_normalized), .sticky());
  logic signed [8:0] clx_look_b_exp; assign clx_look_b_exp = -$signed({1'b0, clx_look_b_count});
  logic [60:0] clx_look_bx; assign clx_look_bx = {2'd0, clx_look_b[43], clx_look_b_exp, 4'd0, clx_look_b_normalized, 1'b0};
  logic [60:0] clx_look_result;
  logic clx_look_zero;
  fam_dot_lza_w43_p47261b205eb3 u8 (.xa(clx_look_ax), .xb(clx_look_bx), .sub(1'b0), .y(clx_look_result), .predict_zero(clx_look_zero));
  logic signed [8:0] clx_look_exp; assign clx_look_exp = $signed(clx_look_result[57:49]);
  logic clx_look_bypass; assign clx_look_bypass = (clx_look_am == 0) || (clx_look_bm == 0);
  logic signed [8:0] clx_look_shift; assign clx_look_shift = (clx_look_bypass ? -9'sd1 : -9'sd5) - clx_look_exp;
  logic [5:0] clx_lzs; assign clx_lzs = (clx_mag == 0 || clx_look_shift < 0) ? 0 : (clx_look_shift >= 43) ? 6'd42 : clx_look_shift[5:0];
  logic [6:0] clx_lz; assign clx_lz = {1'b0, clx_lzs};
  logic [42:0] clx_nm_shifted;
  // normalize the actual reduction result by its selected lookahead shift
  fam_shift_barrel_mux_tree #(.W(43), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u9 (.a(clx_mag), .amt(clx_lzs), .op(3'd0), .y(clx_nm_shifted), .sticky());
  logic [42:0] clx_nm; assign clx_nm = clx_look_zero ? 43'd0 : clx_nm_shifted;
  logic [25:0] clx_sig; assign clx_sig = clx_nm[42:17];
  logic clx_st; assign clx_st = (|clx_nm[16:0]) | cl_stv;
  logic signed [18:0] clx_e0; assign clx_e0 = ef + 19'sd17 - $signed({{(19-7){1'b0}}, clx_lz});
  logic signed [15:0] clx_e; assign clx_e = clx_e0[15:0];
  logic clx_zero; assign clx_zero = (clx_mag == 0) && !(cl_stv);
  logic [45:0] y_clx; assign y_clx = clx_zero ? {2'd0, 1'b0, 16'sd0, 26'd0, 1'b0} : {2'd0, clx_neg, clx_e, clx_sig, clx_st};
  logic [43:0] fa_yop; assign fa_yop = eff_sub ? ~Y : Y;
  logic [43:0] fa_r;
  logic fa_co;
  // fa: X + Y, or X + ~Y (the end-around carry)
  fam_adder_ripple_carry #(.W(44), .CHUNK(1), .FORM(0)) u10 (.a(X), .b(fa_yop), .cin(1'b0), .s(fa_r), .cout(fa_co));
  logic [43:0] fa_inc;
  logic fa_ico;
  // fa: the end-around carry added back
  fam_incr_prefix_and #(.W(44), .STRUCTURE(1), .B(4), .TOPO(0)) u11 (.a(fa_r), .cin(fa_co), .s(fa_inc), .cout(fa_ico));
  logic fa_neg; assign fa_neg = eff_sub && !fa_co;
  logic [43:0] fa_mag; assign fa_mag = eff_sub ? (fa_co ? fa_inc : ~fa_r) : fa_r;
  logic fa_s; assign fa_s = fa_neg ? c_s : sp;
  logic [42:0] fa_v; assign fa_v = fa_mag[43:1];
  logic fa_stv; assign fa_stv = fa_mag[0];
  logic [1:0] fa_lc; assign fa_lc = fa_neg ? (2'd1 + {1'b0, X[0] & fa_yop[0]}) : eff_sub ? {1'b0, X[0] | fa_yop[0]} : {1'b0, X[0] & fa_yop[0]};
  logic [42:0] fa_lx; assign fa_lx = X[43:1];
  logic [42:0] fa_ly; assign fa_ly = fa_yop[43:1];
  logic fax_neg; assign fax_neg = fa_s;
  logic [42:0] fax_mag; assign fax_mag = fa_v;
  logic [5:0] fax_lzc;
  // fax: the leading-zero count of the magnitude
  fam_count_lzd_pair_cell_binary_count_vflat_w43 u12 (.a(fax_mag), .n(fax_lzc));
  logic [5:0] fax_lzs; assign fax_lzs = (fax_mag == 0) ? 6'd0 : fax_lzc[5:0];
  logic [6:0] fax_lz; assign fax_lz = {1'b0, fax_lzs};
  logic [42:0] fax_nm;
  // fax: the normalize shifter
  fam_shift_barrel_mux_tree #(.W(43), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u13 (.a(fax_mag), .amt(fax_lzs), .op(3'd0), .y(fax_nm), .sticky());
  logic [25:0] fax_sig; assign fax_sig = fax_nm[42:17];
  logic fax_st; assign fax_st = (|fax_nm[16:0]) | fa_stv;
  logic signed [18:0] fax_e0; assign fax_e0 = ef + 19'sd17 - $signed({{(19-7){1'b0}}, fax_lz});
  logic signed [15:0] fax_e; assign fax_e = fax_e0[15:0];
  logic fax_zero; assign fax_zero = (fax_mag == 0) && !(fa_stv);
  logic [45:0] y_fax; assign y_fax = fax_zero ? {2'd0, 1'b0, 16'sd0, 26'd0, 1'b0} : {2'd0, fax_neg, fax_e, fax_sig, fax_st};
  logic [43:0] fp_yop; assign fp_yop = eff_sub ? ~Y : Y;
  logic [43:0] fp_r;
  logic fp_co;
  // fp: X + Y, or X + ~Y (the end-around carry)
  fam_adder_ripple_carry #(.W(44), .CHUNK(1), .FORM(0)) u14 (.a(X), .b(fp_yop), .cin(1'b0), .s(fp_r), .cout(fp_co));
  logic [43:0] fp_inc;
  logic fp_ico;
  // fp: the end-around carry added back
  fam_incr_prefix_and #(.W(44), .STRUCTURE(1), .B(4), .TOPO(0)) u15 (.a(fp_r), .cin(fp_co), .s(fp_inc), .cout(fp_ico));
  logic fp_neg; assign fp_neg = eff_sub && !fp_co;
  logic [43:0] fp_mag; assign fp_mag = eff_sub ? (fp_co ? fp_inc : ~fp_r) : fp_r;
  logic fp_s; assign fp_s = fp_neg ? c_s : sp;
  logic [42:0] fp_v; assign fp_v = fp_mag[43:1];
  logic fp_stv; assign fp_stv = fp_mag[0];
  logic [1:0] fp_lc; assign fp_lc = fp_neg ? (2'd1 + {1'b0, X[0] & fp_yop[0]}) : eff_sub ? {1'b0, X[0] | fp_yop[0]} : {1'b0, X[0] & fp_yop[0]};
  logic [42:0] fp_lx; assign fp_lx = X[43:1];
  logic [42:0] fp_ly; assign fp_ly = fp_yop[43:1];
  logic fpx_neg; assign fpx_neg = fp_s;
  logic [42:0] fpx_mag; assign fpx_mag = fp_v;
  logic [5:0] fpx_lzc;
  // fpx: the leading-zero count of the magnitude
  fam_count_lzd_pair_cell_binary_count_vflat_w43 u16 (.a(fpx_mag), .n(fpx_lzc));
  logic [5:0] fpx_lzs; assign fpx_lzs = (fpx_mag == 0) ? 6'd0 : fpx_lzc[5:0];
  logic [6:0] fpx_lz; assign fpx_lz = {1'b0, fpx_lzs};
  logic [42:0] fpx_nm;
  // fpx: the normalize shifter
  fam_shift_barrel_mux_tree #(.W(43), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u17 (.a(fpx_mag), .amt(fpx_lzs), .op(3'd0), .y(fpx_nm), .sticky());
  logic [25:0] fpx_sig; assign fpx_sig = fpx_nm[42:17];
  logic fpx_st; assign fpx_st = (|fpx_nm[16:0]) | fp_stv;
  logic signed [18:0] fpx_e0; assign fpx_e0 = ef + 19'sd17 - $signed({{(19-7){1'b0}}, fpx_lz});
  logic signed [15:0] fpx_e; assign fpx_e = fpx_e0[15:0];
  logic fpx_zero; assign fpx_zero = (fpx_mag == 0) && !(fp_stv);
  logic [45:0] y_fpx; assign y_fpx = fpx_zero ? {2'd0, 1'b0, 16'sd0, 26'd0, 1'b0} : {2'd0, fpx_neg, fpx_e, fpx_sig, fpx_st};
  logic [45:0] y_far; assign y_far = c_case ? y_fax : y_fpx;
  logic [45:0] y_close; assign y_close = y_clx;
  logic [45:0] y_sel; assign y_sel = close ? y_close : y_far;
  assign y = y_sel;
endmodule


// fused multiply-add (reduced_latency_fma): the 11-bit addend aligned against the 22-bit product over a 43-bit window (7 guard bits below the product for the X's 26-bit significand; a sticky lsb holds what leaves it), the significand multiplier behavioral_star, the window adder ripple_carry, negation by end_around_carry, leading zeros by lza, one normalize; meets the fused contract; the rounding for 4 bits is fused into the compound adder for a normal result (it leaves with the ROUNDED code, the seed packs it through the library rounder); a subnormal, an overflow and the stochastic mode leave unrounded
module fam_fp_fma_core_reduced_latency_fma_x26e16s11_fp8e4m3_pddacaa615be9 (
  input logic [45:0] xa,
  input logic [45:0] xb,
  input logic [45:0] xc,
  input logic [2:0] rnd,
  output logic [45:0] y
);
  logic [1:0] a_sp; assign a_sp = xa[45:44];
  logic a_s; assign a_s = xa[43];
  logic signed [15:0] a_e; assign a_e = $signed(xa[42:27]);
  logic [25:0] a_sig; assign a_sig = xa[26:1];
  logic a_st; assign a_st = xa[0];
  logic a_z; assign a_z = (a_sp == 2'd0) && (a_sig == 0) && !a_st;
  logic [1:0] b_sp; assign b_sp = xb[45:44];
  logic b_s; assign b_s = xb[43];
  logic signed [15:0] b_e; assign b_e = $signed(xb[42:27]);
  logic [25:0] b_sig; assign b_sig = xb[26:1];
  logic b_st; assign b_st = xb[0];
  logic b_z; assign b_z = (b_sp == 2'd0) && (b_sig == 0) && !b_st;
  logic [1:0] c_sp; assign c_sp = xc[45:44];
  logic c_s; assign c_s = xc[43];
  logic signed [15:0] c_e; assign c_e = $signed(xc[42:27]);
  logic [25:0] c_sig; assign c_sig = xc[26:1];
  logic c_st; assign c_st = xc[0];
  logic c_z; assign c_z = (c_sp == 2'd0) && (c_sig == 0) && !c_st;
  logic [10:0] sa0; assign sa0 = a_sig[10:0];
  logic [3:0] a_lzs; assign a_lzs = 4'd0;
  logic [10:0] sa; assign sa = sa0;
  logic signed [18:0] ea; assign ea = $signed({{3{a_e[15]}}, a_e}) - $signed({{(19-4){1'b0}}, a_lzs});
  logic [10:0] sb0; assign sb0 = b_sig[10:0];
  logic [3:0] b_lzs; assign b_lzs = 4'd0;
  logic [10:0] sb; assign sb = sb0;
  logic signed [18:0] eb; assign eb = $signed({{3{b_e[15]}}, b_e}) - $signed({{(19-4){1'b0}}, b_lzs});
  logic [21:0] p;
  assign p = sa * sb;
  logic signed [18:0] ep; assign ep = ea + eb;
  logic sp; assign sp = a_s ^ b_s;
  logic [10:0] sc0; assign sc0 = c_sig[10:0];
  logic signed [18:0] ec0; assign ec0 = $signed({{3{c_e[15]}}, c_e});
  logic [3:0] c_lzs; assign c_lzs = 4'd0;
  logic [10:0] sc; assign sc = sc0;
  logic signed [18:0] ec; assign ec = ec0 - $signed({{(19-4){1'b0}}, c_lzs});
  logic eff_sub; assign eff_sub = sp ^ c_s;
  logic signed [18:0] ep_e; assign ep_e = (p == 0) ? (ec - 19'sd24) : ep;
  logic signed [18:0] d; assign d = ec - ep_e;
  logic signed [18:0] shc0; assign shc0 = 19'sd24 - d;
  logic signed [18:0] shc; assign shc = (sc0 == 0) ? 19'sd0 : shc0;
  logic c_case; assign c_case = shc >= 0;
  logic signed [18:0] ef; assign ef = (c_case ? ep_e : (ep_e - shc)) - 19'sd7;
  logic [42:0] w0c; assign w0c = {1'b0, sc, 31'd0};
  logic [42:0] w0p; assign w0p = {{(43-22-7){1'b0}}, p, 7'd0};
  logic signed [18:0] amt0; assign amt0 = c_case ? shc : (-shc);
  logic far; assign far = amt0 >= 43;
  logic [5:0] amt; assign amt = far ? 6'd0 : amt0[5:0];
  logic [42:0] wsel; assign wsel = c_case ? w0c : w0p;
  logic [42:0] wsh;
  logic wshift_st;
  // the alignment shifter (the addend, or the product when the addend is far larger)
  fam_shift_barrel_mux_tree #(.W(43), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u1 (.a(wsel), .amt(amt), .op(3'd1), .y(wsh), .sticky());
  assign wshift_st = |(wsel & ((3'd1 == 3'd0) ? ~({43{1'b1}} >> amt) : ~({43{1'b1}} << amt)));
  logic wst; assign wst = far ? (|wsel) : wshift_st;
  logic [42:0] wal; assign wal = far ? 43'd0 : wsh;
  logic [42:0] c_al; assign c_al = c_case ? wal : w0c;
  logic [42:0] p_al; assign p_al = c_case ? w0p : wal;
  logic st_c; assign st_c = c_case ? wst : 1'b0;
  logic st_p; assign st_p = c_case ? 1'b0 : wst;
  logic [43:0] X; assign X = {p_al, st_p};
  logic [43:0] Y; assign Y = {c_al, st_c};
  logic [43:0] f_yop; assign f_yop = eff_sub ? ~Y : Y;
  logic [43:0] f_r;
  logic f_co;
  // f: X + Y, or X + ~Y (the end-around carry)
  fam_adder_ripple_carry #(.W(44), .CHUNK(1), .FORM(0)) u2 (.a(X), .b(f_yop), .cin(1'b0), .s(f_r), .cout(f_co));
  logic [43:0] f_inc;
  logic f_ico;
  // f: the end-around carry added back
  fam_incr_prefix_and #(.W(44), .STRUCTURE(1), .B(4), .TOPO(0)) u3 (.a(f_r), .cin(f_co), .s(f_inc), .cout(f_ico));
  logic f_neg; assign f_neg = eff_sub && !f_co;
  logic [43:0] f_mag; assign f_mag = eff_sub ? (f_co ? f_inc : ~f_r) : f_r;
  logic f_s; assign f_s = f_neg ? c_s : sp;
  logic [42:0] f_v; assign f_v = f_mag[43:1];
  logic f_stv; assign f_stv = f_mag[0];
  logic [1:0] f_lc; assign f_lc = f_neg ? (2'd1 + {1'b0, X[0] & f_yop[0]}) : eff_sub ? {1'b0, X[0] | f_yop[0]} : {1'b0, X[0] & f_yop[0]};
  logic [42:0] f_lx; assign f_lx = X[43:1];
  logic [42:0] f_ly; assign f_ly = f_yop[43:1];
  logic fx_neg; assign fx_neg = f_s;
  logic [42:0] fx_mag; assign fx_mag = f_v;
  logic fx_look_cin; assign fx_look_cin = f_v[0] ^ f_lx[0] ^ f_ly[0];
  logic signed [43:0] fx_look_a; assign fx_look_a = {f_lx[42], f_lx};
  logic [1:0] fx_look_adj; assign fx_look_adj = f_lc;
  logic signed [43:0] fx_look_b; assign fx_look_b = $signed({f_ly[42], f_ly}) + $signed({{(44-2){1'b0}}, fx_look_adj});
  logic [43:0] fx_look_am; assign fx_look_am = fx_look_a[43] ? -fx_look_a : fx_look_a;
  logic [5:0] fx_look_a_lz;
  // normalize a real lookahead operand
  fam_count_lzd_pair_cell_binary_count_vflat_w44 u4 (.a(fx_look_am), .n(fx_look_a_lz));
  logic [5:0] fx_look_a_count; assign fx_look_a_count = (fx_look_am == 0) ? 0 : fx_look_a_lz[5:0];
  logic [43:0] fx_look_a_normalized;
  // the lookahead operand's declared normalizer
  fam_shift_barrel_mux_tree #(.W(44), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u5 (.a(fx_look_am), .amt(fx_look_a_count), .op(3'd0), .y(fx_look_a_normalized), .sticky());
  logic signed [8:0] fx_look_a_exp; assign fx_look_a_exp = -$signed({1'b0, fx_look_a_count});
  logic [60:0] fx_look_ax; assign fx_look_ax = {2'd0, fx_look_a[43], fx_look_a_exp, 4'd0, fx_look_a_normalized, 1'b0};
  logic [43:0] fx_look_bm; assign fx_look_bm = fx_look_b[43] ? -fx_look_b : fx_look_b;
  logic [5:0] fx_look_b_lz;
  // normalize a real lookahead operand
  fam_count_lzd_pair_cell_binary_count_vflat_w44 u6 (.a(fx_look_bm), .n(fx_look_b_lz));
  logic [5:0] fx_look_b_count; assign fx_look_b_count = (fx_look_bm == 0) ? 0 : fx_look_b_lz[5:0];
  logic [43:0] fx_look_b_normalized;
  // the lookahead operand's declared normalizer
  fam_shift_barrel_mux_tree #(.W(44), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u7 (.a(fx_look_bm), .amt(fx_look_b_count), .op(3'd0), .y(fx_look_b_normalized), .sticky());
  logic signed [8:0] fx_look_b_exp; assign fx_look_b_exp = -$signed({1'b0, fx_look_b_count});
  logic [60:0] fx_look_bx; assign fx_look_bx = {2'd0, fx_look_b[43], fx_look_b_exp, 4'd0, fx_look_b_normalized, 1'b0};
  logic [60:0] fx_look_result;
  logic fx_look_zero;
  fam_dot_lza_w43_p47261b205eb3 u8 (.xa(fx_look_ax), .xb(fx_look_bx), .sub(1'b0), .y(fx_look_result), .predict_zero(fx_look_zero));
  logic signed [8:0] fx_look_exp; assign fx_look_exp = $signed(fx_look_result[57:49]);
  logic fx_look_bypass; assign fx_look_bypass = (fx_look_am == 0) || (fx_look_bm == 0);
  logic signed [8:0] fx_look_shift; assign fx_look_shift = (fx_look_bypass ? -9'sd1 : -9'sd5) - fx_look_exp;
  logic [5:0] fx_lzs; assign fx_lzs = (fx_mag == 0 || fx_look_shift < 0) ? 0 : (fx_look_shift >= 43) ? 6'd42 : fx_look_shift[5:0];
  logic [6:0] fx_lz; assign fx_lz = {1'b0, fx_lzs};
  logic [42:0] fx_nm_shifted;
  // normalize the actual reduction result by its selected lookahead shift
  fam_shift_barrel_mux_tree #(.W(43), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u9 (.a(fx_mag), .amt(fx_lzs), .op(3'd0), .y(fx_nm_shifted), .sticky());
  logic [42:0] fx_nm; assign fx_nm = fx_look_zero ? 43'd0 : fx_nm_shifted;
  logic [25:0] fx_sig; assign fx_sig = fx_nm[42:17];
  logic fx_st; assign fx_st = (|fx_nm[16:0]) | f_stv;
  logic signed [18:0] fx_e0; assign fx_e0 = ef + 19'sd17 - $signed({{(19-7){1'b0}}, fx_lz});
  logic signed [15:0] fx_e; assign fx_e = fx_e0[15:0];
  logic fx_zero; assign fx_zero = (fx_mag == 0) && !(f_stv);
  logic [45:0] y_fx; assign y_fx = fx_zero ? {2'd0, 1'b0, 16'sd0, 26'd0, 1'b0} : {2'd0, fx_neg, fx_e, fx_sig, fx_st};
  logic [43:0] pd_a; assign pd_a = f_neg ? Y : X;
  logic [43:0] pd_b; assign pd_b = eff_sub ? ~(f_neg ? X : Y) : Y;
  logic [6:0] pd_cut; assign pd_cut = 7'd40 - fx_lz;
  logic signed [18:0] pd_exp; assign pd_exp = ef + 19'sd17 - $signed({1'b0, fx_lz});
  logic signed [18:0] pd_biased; assign pd_biased = pd_exp + 19'sd32;
  logic pd_eligible; assign pd_eligible = (|f_mag[43:1]) && (pd_cut >= 2) && (pd_cut <= 7'd40) && (pd_biased >= 1) && (pd_biased <= 19'sd14) && (rnd != 3'd4);
  logic [3:0] pd_k2_a; assign pd_k2_a = pd_a[5:2];
  logic [3:0] pd_k2_b; assign pd_k2_b = pd_b[5:2];
  logic pd_k2_cin; assign pd_k2_cin = pd_a[2] ^ pd_b[2] ^ f_mag[2];
  logic [3:0] pd_k2_s0;
  logic [3:0] pd_k2_s1;
  logic [3:0] pd_k2_s2;
  logic pd_k2_cout;
  logic pd_k2_cout2;
  // post-normalization compound CPA at rounding cut 2
  fam_prefix_kogge_stone_w4_flag_dual u10 (.a(pd_k2_a), .b(pd_k2_b), .cin(1'b0), .s(pd_k2_s0), .cout(pd_k2_cout), .s1(pd_k2_s1));
  // cut 2: candidate for simultaneous low carry and rounding increment
  fam_incr_prefix_and #(.W(4), .STRUCTURE(1), .B(4), .TOPO(0)) u11 (.a(pd_k2_s1), .cin(1'b1), .s(pd_k2_s2), .cout(pd_k2_cout2));
  logic [3:0] pd_k2_down; assign pd_k2_down = pd_k2_cin ? pd_k2_s1 : pd_k2_s0;
  logic [3:0] pd_k2_up; assign pd_k2_up = pd_k2_cin ? pd_k2_s2 : pd_k2_s1;
  logic pd_k2_guard; assign pd_k2_guard = f_mag[1];
  logic pd_k2_sticky; assign pd_k2_sticky = |f_mag[0:0];
  logic pd_k2_inexact; assign pd_k2_inexact = pd_k2_guard | pd_k2_sticky;
  logic pd_k2_increment; assign pd_k2_increment = (rnd == 3'd0) ? (pd_k2_guard && (pd_k2_sticky || pd_k2_down[0])) : (rnd == 3'd2) ? (pd_k2_inexact && f_s) : (rnd == 3'd3) ? (pd_k2_inexact && !f_s) : (rnd == 3'd5) ? pd_k2_inexact : 1'b0;
  logic [3:0] pd_k2_keep; assign pd_k2_keep = pd_k2_increment ? pd_k2_up : pd_k2_down;
  logic pd_k2_carry; assign pd_k2_carry = pd_k2_increment && (&pd_k2_down[3:0]);
  logic [25:0] pd_k2_sig; assign pd_k2_sig = pd_k2_carry ? (26'd1 << 25) : {pd_k2_keep[3:0], 22'd0};
  logic signed [18:0] pd_k2_ewide; assign pd_k2_ewide = pd_exp + (pd_k2_carry ? 19'sd1 : 19'sd0);
  logic signed [15:0] pd_k2_e; assign pd_k2_e = pd_k2_ewide[15:0];
  logic [1:0] pd_k2_special; assign pd_k2_special = pd_k2_inexact ? 2'd3 : 2'd0;
  logic [45:0] pd_k2_y; assign pd_k2_y = {pd_k2_special, f_s, pd_k2_e, pd_k2_sig, 1'b0};
  logic [3:0] pd_k3_a; assign pd_k3_a = pd_a[6:3];
  logic [3:0] pd_k3_b; assign pd_k3_b = pd_b[6:3];
  logic pd_k3_cin; assign pd_k3_cin = pd_a[3] ^ pd_b[3] ^ f_mag[3];
  logic [3:0] pd_k3_s0;
  logic [3:0] pd_k3_s1;
  logic [3:0] pd_k3_s2;
  logic pd_k3_cout;
  logic pd_k3_cout2;
  // post-normalization compound CPA at rounding cut 3
  fam_prefix_kogge_stone_w4_flag_dual u12 (.a(pd_k3_a), .b(pd_k3_b), .cin(1'b0), .s(pd_k3_s0), .cout(pd_k3_cout), .s1(pd_k3_s1));
  // cut 3: candidate for simultaneous low carry and rounding increment
  fam_incr_prefix_and #(.W(4), .STRUCTURE(1), .B(4), .TOPO(0)) u13 (.a(pd_k3_s1), .cin(1'b1), .s(pd_k3_s2), .cout(pd_k3_cout2));
  logic [3:0] pd_k3_down; assign pd_k3_down = pd_k3_cin ? pd_k3_s1 : pd_k3_s0;
  logic [3:0] pd_k3_up; assign pd_k3_up = pd_k3_cin ? pd_k3_s2 : pd_k3_s1;
  logic pd_k3_guard; assign pd_k3_guard = f_mag[2];
  logic pd_k3_sticky; assign pd_k3_sticky = |f_mag[1:0];
  logic pd_k3_inexact; assign pd_k3_inexact = pd_k3_guard | pd_k3_sticky;
  logic pd_k3_increment; assign pd_k3_increment = (rnd == 3'd0) ? (pd_k3_guard && (pd_k3_sticky || pd_k3_down[0])) : (rnd == 3'd2) ? (pd_k3_inexact && f_s) : (rnd == 3'd3) ? (pd_k3_inexact && !f_s) : (rnd == 3'd5) ? pd_k3_inexact : 1'b0;
  logic [3:0] pd_k3_keep; assign pd_k3_keep = pd_k3_increment ? pd_k3_up : pd_k3_down;
  logic pd_k3_carry; assign pd_k3_carry = pd_k3_increment && (&pd_k3_down[3:0]);
  logic [25:0] pd_k3_sig; assign pd_k3_sig = pd_k3_carry ? (26'd1 << 25) : {pd_k3_keep[3:0], 22'd0};
  logic signed [18:0] pd_k3_ewide; assign pd_k3_ewide = pd_exp + (pd_k3_carry ? 19'sd1 : 19'sd0);
  logic signed [15:0] pd_k3_e; assign pd_k3_e = pd_k3_ewide[15:0];
  logic [1:0] pd_k3_special; assign pd_k3_special = pd_k3_inexact ? 2'd3 : 2'd0;
  logic [45:0] pd_k3_y; assign pd_k3_y = {pd_k3_special, f_s, pd_k3_e, pd_k3_sig, 1'b0};
  logic [3:0] pd_k4_a; assign pd_k4_a = pd_a[7:4];
  logic [3:0] pd_k4_b; assign pd_k4_b = pd_b[7:4];
  logic pd_k4_cin; assign pd_k4_cin = pd_a[4] ^ pd_b[4] ^ f_mag[4];
  logic [3:0] pd_k4_s0;
  logic [3:0] pd_k4_s1;
  logic [3:0] pd_k4_s2;
  logic pd_k4_cout;
  logic pd_k4_cout2;
  // post-normalization compound CPA at rounding cut 4
  fam_prefix_kogge_stone_w4_flag_dual u14 (.a(pd_k4_a), .b(pd_k4_b), .cin(1'b0), .s(pd_k4_s0), .cout(pd_k4_cout), .s1(pd_k4_s1));
  // cut 4: candidate for simultaneous low carry and rounding increment
  fam_incr_prefix_and #(.W(4), .STRUCTURE(1), .B(4), .TOPO(0)) u15 (.a(pd_k4_s1), .cin(1'b1), .s(pd_k4_s2), .cout(pd_k4_cout2));
  logic [3:0] pd_k4_down; assign pd_k4_down = pd_k4_cin ? pd_k4_s1 : pd_k4_s0;
  logic [3:0] pd_k4_up; assign pd_k4_up = pd_k4_cin ? pd_k4_s2 : pd_k4_s1;
  logic pd_k4_guard; assign pd_k4_guard = f_mag[3];
  logic pd_k4_sticky; assign pd_k4_sticky = |f_mag[2:0];
  logic pd_k4_inexact; assign pd_k4_inexact = pd_k4_guard | pd_k4_sticky;
  logic pd_k4_increment; assign pd_k4_increment = (rnd == 3'd0) ? (pd_k4_guard && (pd_k4_sticky || pd_k4_down[0])) : (rnd == 3'd2) ? (pd_k4_inexact && f_s) : (rnd == 3'd3) ? (pd_k4_inexact && !f_s) : (rnd == 3'd5) ? pd_k4_inexact : 1'b0;
  logic [3:0] pd_k4_keep; assign pd_k4_keep = pd_k4_increment ? pd_k4_up : pd_k4_down;
  logic pd_k4_carry; assign pd_k4_carry = pd_k4_increment && (&pd_k4_down[3:0]);
  logic [25:0] pd_k4_sig; assign pd_k4_sig = pd_k4_carry ? (26'd1 << 25) : {pd_k4_keep[3:0], 22'd0};
  logic signed [18:0] pd_k4_ewide; assign pd_k4_ewide = pd_exp + (pd_k4_carry ? 19'sd1 : 19'sd0);
  logic signed [15:0] pd_k4_e; assign pd_k4_e = pd_k4_ewide[15:0];
  logic [1:0] pd_k4_special; assign pd_k4_special = pd_k4_inexact ? 2'd3 : 2'd0;
  logic [45:0] pd_k4_y; assign pd_k4_y = {pd_k4_special, f_s, pd_k4_e, pd_k4_sig, 1'b0};
  logic [3:0] pd_k5_a; assign pd_k5_a = pd_a[8:5];
  logic [3:0] pd_k5_b; assign pd_k5_b = pd_b[8:5];
  logic pd_k5_cin; assign pd_k5_cin = pd_a[5] ^ pd_b[5] ^ f_mag[5];
  logic [3:0] pd_k5_s0;
  logic [3:0] pd_k5_s1;
  logic [3:0] pd_k5_s2;
  logic pd_k5_cout;
  logic pd_k5_cout2;
  // post-normalization compound CPA at rounding cut 5
  fam_prefix_kogge_stone_w4_flag_dual u16 (.a(pd_k5_a), .b(pd_k5_b), .cin(1'b0), .s(pd_k5_s0), .cout(pd_k5_cout), .s1(pd_k5_s1));
  // cut 5: candidate for simultaneous low carry and rounding increment
  fam_incr_prefix_and #(.W(4), .STRUCTURE(1), .B(4), .TOPO(0)) u17 (.a(pd_k5_s1), .cin(1'b1), .s(pd_k5_s2), .cout(pd_k5_cout2));
  logic [3:0] pd_k5_down; assign pd_k5_down = pd_k5_cin ? pd_k5_s1 : pd_k5_s0;
  logic [3:0] pd_k5_up; assign pd_k5_up = pd_k5_cin ? pd_k5_s2 : pd_k5_s1;
  logic pd_k5_guard; assign pd_k5_guard = f_mag[4];
  logic pd_k5_sticky; assign pd_k5_sticky = |f_mag[3:0];
  logic pd_k5_inexact; assign pd_k5_inexact = pd_k5_guard | pd_k5_sticky;
  logic pd_k5_increment; assign pd_k5_increment = (rnd == 3'd0) ? (pd_k5_guard && (pd_k5_sticky || pd_k5_down[0])) : (rnd == 3'd2) ? (pd_k5_inexact && f_s) : (rnd == 3'd3) ? (pd_k5_inexact && !f_s) : (rnd == 3'd5) ? pd_k5_inexact : 1'b0;
  logic [3:0] pd_k5_keep; assign pd_k5_keep = pd_k5_increment ? pd_k5_up : pd_k5_down;
  logic pd_k5_carry; assign pd_k5_carry = pd_k5_increment && (&pd_k5_down[3:0]);
  logic [25:0] pd_k5_sig; assign pd_k5_sig = pd_k5_carry ? (26'd1 << 25) : {pd_k5_keep[3:0], 22'd0};
  logic signed [18:0] pd_k5_ewide; assign pd_k5_ewide = pd_exp + (pd_k5_carry ? 19'sd1 : 19'sd0);
  logic signed [15:0] pd_k5_e; assign pd_k5_e = pd_k5_ewide[15:0];
  logic [1:0] pd_k5_special; assign pd_k5_special = pd_k5_inexact ? 2'd3 : 2'd0;
  logic [45:0] pd_k5_y; assign pd_k5_y = {pd_k5_special, f_s, pd_k5_e, pd_k5_sig, 1'b0};
  logic [3:0] pd_k6_a; assign pd_k6_a = pd_a[9:6];
  logic [3:0] pd_k6_b; assign pd_k6_b = pd_b[9:6];
  logic pd_k6_cin; assign pd_k6_cin = pd_a[6] ^ pd_b[6] ^ f_mag[6];
  logic [3:0] pd_k6_s0;
  logic [3:0] pd_k6_s1;
  logic [3:0] pd_k6_s2;
  logic pd_k6_cout;
  logic pd_k6_cout2;
  // post-normalization compound CPA at rounding cut 6
  fam_prefix_kogge_stone_w4_flag_dual u18 (.a(pd_k6_a), .b(pd_k6_b), .cin(1'b0), .s(pd_k6_s0), .cout(pd_k6_cout), .s1(pd_k6_s1));
  // cut 6: candidate for simultaneous low carry and rounding increment
  fam_incr_prefix_and #(.W(4), .STRUCTURE(1), .B(4), .TOPO(0)) u19 (.a(pd_k6_s1), .cin(1'b1), .s(pd_k6_s2), .cout(pd_k6_cout2));
  logic [3:0] pd_k6_down; assign pd_k6_down = pd_k6_cin ? pd_k6_s1 : pd_k6_s0;
  logic [3:0] pd_k6_up; assign pd_k6_up = pd_k6_cin ? pd_k6_s2 : pd_k6_s1;
  logic pd_k6_guard; assign pd_k6_guard = f_mag[5];
  logic pd_k6_sticky; assign pd_k6_sticky = |f_mag[4:0];
  logic pd_k6_inexact; assign pd_k6_inexact = pd_k6_guard | pd_k6_sticky;
  logic pd_k6_increment; assign pd_k6_increment = (rnd == 3'd0) ? (pd_k6_guard && (pd_k6_sticky || pd_k6_down[0])) : (rnd == 3'd2) ? (pd_k6_inexact && f_s) : (rnd == 3'd3) ? (pd_k6_inexact && !f_s) : (rnd == 3'd5) ? pd_k6_inexact : 1'b0;
  logic [3:0] pd_k6_keep; assign pd_k6_keep = pd_k6_increment ? pd_k6_up : pd_k6_down;
  logic pd_k6_carry; assign pd_k6_carry = pd_k6_increment && (&pd_k6_down[3:0]);
  logic [25:0] pd_k6_sig; assign pd_k6_sig = pd_k6_carry ? (26'd1 << 25) : {pd_k6_keep[3:0], 22'd0};
  logic signed [18:0] pd_k6_ewide; assign pd_k6_ewide = pd_exp + (pd_k6_carry ? 19'sd1 : 19'sd0);
  logic signed [15:0] pd_k6_e; assign pd_k6_e = pd_k6_ewide[15:0];
  logic [1:0] pd_k6_special; assign pd_k6_special = pd_k6_inexact ? 2'd3 : 2'd0;
  logic [45:0] pd_k6_y; assign pd_k6_y = {pd_k6_special, f_s, pd_k6_e, pd_k6_sig, 1'b0};
  logic [3:0] pd_k7_a; assign pd_k7_a = pd_a[10:7];
  logic [3:0] pd_k7_b; assign pd_k7_b = pd_b[10:7];
  logic pd_k7_cin; assign pd_k7_cin = pd_a[7] ^ pd_b[7] ^ f_mag[7];
  logic [3:0] pd_k7_s0;
  logic [3:0] pd_k7_s1;
  logic [3:0] pd_k7_s2;
  logic pd_k7_cout;
  logic pd_k7_cout2;
  // post-normalization compound CPA at rounding cut 7
  fam_prefix_kogge_stone_w4_flag_dual u20 (.a(pd_k7_a), .b(pd_k7_b), .cin(1'b0), .s(pd_k7_s0), .cout(pd_k7_cout), .s1(pd_k7_s1));
  // cut 7: candidate for simultaneous low carry and rounding increment
  fam_incr_prefix_and #(.W(4), .STRUCTURE(1), .B(4), .TOPO(0)) u21 (.a(pd_k7_s1), .cin(1'b1), .s(pd_k7_s2), .cout(pd_k7_cout2));
  logic [3:0] pd_k7_down; assign pd_k7_down = pd_k7_cin ? pd_k7_s1 : pd_k7_s0;
  logic [3:0] pd_k7_up; assign pd_k7_up = pd_k7_cin ? pd_k7_s2 : pd_k7_s1;
  logic pd_k7_guard; assign pd_k7_guard = f_mag[6];
  logic pd_k7_sticky; assign pd_k7_sticky = |f_mag[5:0];
  logic pd_k7_inexact; assign pd_k7_inexact = pd_k7_guard | pd_k7_sticky;
  logic pd_k7_increment; assign pd_k7_increment = (rnd == 3'd0) ? (pd_k7_guard && (pd_k7_sticky || pd_k7_down[0])) : (rnd == 3'd2) ? (pd_k7_inexact && f_s) : (rnd == 3'd3) ? (pd_k7_inexact && !f_s) : (rnd == 3'd5) ? pd_k7_inexact : 1'b0;
  logic [3:0] pd_k7_keep; assign pd_k7_keep = pd_k7_increment ? pd_k7_up : pd_k7_down;
  logic pd_k7_carry; assign pd_k7_carry = pd_k7_increment && (&pd_k7_down[3:0]);
  logic [25:0] pd_k7_sig; assign pd_k7_sig = pd_k7_carry ? (26'd1 << 25) : {pd_k7_keep[3:0], 22'd0};
  logic signed [18:0] pd_k7_ewide; assign pd_k7_ewide = pd_exp + (pd_k7_carry ? 19'sd1 : 19'sd0);
  logic signed [15:0] pd_k7_e; assign pd_k7_e = pd_k7_ewide[15:0];
  logic [1:0] pd_k7_special; assign pd_k7_special = pd_k7_inexact ? 2'd3 : 2'd0;
  logic [45:0] pd_k7_y; assign pd_k7_y = {pd_k7_special, f_s, pd_k7_e, pd_k7_sig, 1'b0};
  logic [3:0] pd_k8_a; assign pd_k8_a = pd_a[11:8];
  logic [3:0] pd_k8_b; assign pd_k8_b = pd_b[11:8];
  logic pd_k8_cin; assign pd_k8_cin = pd_a[8] ^ pd_b[8] ^ f_mag[8];
  logic [3:0] pd_k8_s0;
  logic [3:0] pd_k8_s1;
  logic [3:0] pd_k8_s2;
  logic pd_k8_cout;
  logic pd_k8_cout2;
  // post-normalization compound CPA at rounding cut 8
  fam_prefix_kogge_stone_w4_flag_dual u22 (.a(pd_k8_a), .b(pd_k8_b), .cin(1'b0), .s(pd_k8_s0), .cout(pd_k8_cout), .s1(pd_k8_s1));
  // cut 8: candidate for simultaneous low carry and rounding increment
  fam_incr_prefix_and #(.W(4), .STRUCTURE(1), .B(4), .TOPO(0)) u23 (.a(pd_k8_s1), .cin(1'b1), .s(pd_k8_s2), .cout(pd_k8_cout2));
  logic [3:0] pd_k8_down; assign pd_k8_down = pd_k8_cin ? pd_k8_s1 : pd_k8_s0;
  logic [3:0] pd_k8_up; assign pd_k8_up = pd_k8_cin ? pd_k8_s2 : pd_k8_s1;
  logic pd_k8_guard; assign pd_k8_guard = f_mag[7];
  logic pd_k8_sticky; assign pd_k8_sticky = |f_mag[6:0];
  logic pd_k8_inexact; assign pd_k8_inexact = pd_k8_guard | pd_k8_sticky;
  logic pd_k8_increment; assign pd_k8_increment = (rnd == 3'd0) ? (pd_k8_guard && (pd_k8_sticky || pd_k8_down[0])) : (rnd == 3'd2) ? (pd_k8_inexact && f_s) : (rnd == 3'd3) ? (pd_k8_inexact && !f_s) : (rnd == 3'd5) ? pd_k8_inexact : 1'b0;
  logic [3:0] pd_k8_keep; assign pd_k8_keep = pd_k8_increment ? pd_k8_up : pd_k8_down;
  logic pd_k8_carry; assign pd_k8_carry = pd_k8_increment && (&pd_k8_down[3:0]);
  logic [25:0] pd_k8_sig; assign pd_k8_sig = pd_k8_carry ? (26'd1 << 25) : {pd_k8_keep[3:0], 22'd0};
  logic signed [18:0] pd_k8_ewide; assign pd_k8_ewide = pd_exp + (pd_k8_carry ? 19'sd1 : 19'sd0);
  logic signed [15:0] pd_k8_e; assign pd_k8_e = pd_k8_ewide[15:0];
  logic [1:0] pd_k8_special; assign pd_k8_special = pd_k8_inexact ? 2'd3 : 2'd0;
  logic [45:0] pd_k8_y; assign pd_k8_y = {pd_k8_special, f_s, pd_k8_e, pd_k8_sig, 1'b0};
  logic [3:0] pd_k9_a; assign pd_k9_a = pd_a[12:9];
  logic [3:0] pd_k9_b; assign pd_k9_b = pd_b[12:9];
  logic pd_k9_cin; assign pd_k9_cin = pd_a[9] ^ pd_b[9] ^ f_mag[9];
  logic [3:0] pd_k9_s0;
  logic [3:0] pd_k9_s1;
  logic [3:0] pd_k9_s2;
  logic pd_k9_cout;
  logic pd_k9_cout2;
  // post-normalization compound CPA at rounding cut 9
  fam_prefix_kogge_stone_w4_flag_dual u24 (.a(pd_k9_a), .b(pd_k9_b), .cin(1'b0), .s(pd_k9_s0), .cout(pd_k9_cout), .s1(pd_k9_s1));
  // cut 9: candidate for simultaneous low carry and rounding increment
  fam_incr_prefix_and #(.W(4), .STRUCTURE(1), .B(4), .TOPO(0)) u25 (.a(pd_k9_s1), .cin(1'b1), .s(pd_k9_s2), .cout(pd_k9_cout2));
  logic [3:0] pd_k9_down; assign pd_k9_down = pd_k9_cin ? pd_k9_s1 : pd_k9_s0;
  logic [3:0] pd_k9_up; assign pd_k9_up = pd_k9_cin ? pd_k9_s2 : pd_k9_s1;
  logic pd_k9_guard; assign pd_k9_guard = f_mag[8];
  logic pd_k9_sticky; assign pd_k9_sticky = |f_mag[7:0];
  logic pd_k9_inexact; assign pd_k9_inexact = pd_k9_guard | pd_k9_sticky;
  logic pd_k9_increment; assign pd_k9_increment = (rnd == 3'd0) ? (pd_k9_guard && (pd_k9_sticky || pd_k9_down[0])) : (rnd == 3'd2) ? (pd_k9_inexact && f_s) : (rnd == 3'd3) ? (pd_k9_inexact && !f_s) : (rnd == 3'd5) ? pd_k9_inexact : 1'b0;
  logic [3:0] pd_k9_keep; assign pd_k9_keep = pd_k9_increment ? pd_k9_up : pd_k9_down;
  logic pd_k9_carry; assign pd_k9_carry = pd_k9_increment && (&pd_k9_down[3:0]);
  logic [25:0] pd_k9_sig; assign pd_k9_sig = pd_k9_carry ? (26'd1 << 25) : {pd_k9_keep[3:0], 22'd0};
  logic signed [18:0] pd_k9_ewide; assign pd_k9_ewide = pd_exp + (pd_k9_carry ? 19'sd1 : 19'sd0);
  logic signed [15:0] pd_k9_e; assign pd_k9_e = pd_k9_ewide[15:0];
  logic [1:0] pd_k9_special; assign pd_k9_special = pd_k9_inexact ? 2'd3 : 2'd0;
  logic [45:0] pd_k9_y; assign pd_k9_y = {pd_k9_special, f_s, pd_k9_e, pd_k9_sig, 1'b0};
  logic [3:0] pd_k10_a; assign pd_k10_a = pd_a[13:10];
  logic [3:0] pd_k10_b; assign pd_k10_b = pd_b[13:10];
  logic pd_k10_cin; assign pd_k10_cin = pd_a[10] ^ pd_b[10] ^ f_mag[10];
  logic [3:0] pd_k10_s0;
  logic [3:0] pd_k10_s1;
  logic [3:0] pd_k10_s2;
  logic pd_k10_cout;
  logic pd_k10_cout2;
  // post-normalization compound CPA at rounding cut 10
  fam_prefix_kogge_stone_w4_flag_dual u26 (.a(pd_k10_a), .b(pd_k10_b), .cin(1'b0), .s(pd_k10_s0), .cout(pd_k10_cout), .s1(pd_k10_s1));
  // cut 10: candidate for simultaneous low carry and rounding increment
  fam_incr_prefix_and #(.W(4), .STRUCTURE(1), .B(4), .TOPO(0)) u27 (.a(pd_k10_s1), .cin(1'b1), .s(pd_k10_s2), .cout(pd_k10_cout2));
  logic [3:0] pd_k10_down; assign pd_k10_down = pd_k10_cin ? pd_k10_s1 : pd_k10_s0;
  logic [3:0] pd_k10_up; assign pd_k10_up = pd_k10_cin ? pd_k10_s2 : pd_k10_s1;
  logic pd_k10_guard; assign pd_k10_guard = f_mag[9];
  logic pd_k10_sticky; assign pd_k10_sticky = |f_mag[8:0];
  logic pd_k10_inexact; assign pd_k10_inexact = pd_k10_guard | pd_k10_sticky;
  logic pd_k10_increment; assign pd_k10_increment = (rnd == 3'd0) ? (pd_k10_guard && (pd_k10_sticky || pd_k10_down[0])) : (rnd == 3'd2) ? (pd_k10_inexact && f_s) : (rnd == 3'd3) ? (pd_k10_inexact && !f_s) : (rnd == 3'd5) ? pd_k10_inexact : 1'b0;
  logic [3:0] pd_k10_keep; assign pd_k10_keep = pd_k10_increment ? pd_k10_up : pd_k10_down;
  logic pd_k10_carry; assign pd_k10_carry = pd_k10_increment && (&pd_k10_down[3:0]);
  logic [25:0] pd_k10_sig; assign pd_k10_sig = pd_k10_carry ? (26'd1 << 25) : {pd_k10_keep[3:0], 22'd0};
  logic signed [18:0] pd_k10_ewide; assign pd_k10_ewide = pd_exp + (pd_k10_carry ? 19'sd1 : 19'sd0);
  logic signed [15:0] pd_k10_e; assign pd_k10_e = pd_k10_ewide[15:0];
  logic [1:0] pd_k10_special; assign pd_k10_special = pd_k10_inexact ? 2'd3 : 2'd0;
  logic [45:0] pd_k10_y; assign pd_k10_y = {pd_k10_special, f_s, pd_k10_e, pd_k10_sig, 1'b0};
  logic [3:0] pd_k11_a; assign pd_k11_a = pd_a[14:11];
  logic [3:0] pd_k11_b; assign pd_k11_b = pd_b[14:11];
  logic pd_k11_cin; assign pd_k11_cin = pd_a[11] ^ pd_b[11] ^ f_mag[11];
  logic [3:0] pd_k11_s0;
  logic [3:0] pd_k11_s1;
  logic [3:0] pd_k11_s2;
  logic pd_k11_cout;
  logic pd_k11_cout2;
  // post-normalization compound CPA at rounding cut 11
  fam_prefix_kogge_stone_w4_flag_dual u28 (.a(pd_k11_a), .b(pd_k11_b), .cin(1'b0), .s(pd_k11_s0), .cout(pd_k11_cout), .s1(pd_k11_s1));
  // cut 11: candidate for simultaneous low carry and rounding increment
  fam_incr_prefix_and #(.W(4), .STRUCTURE(1), .B(4), .TOPO(0)) u29 (.a(pd_k11_s1), .cin(1'b1), .s(pd_k11_s2), .cout(pd_k11_cout2));
  logic [3:0] pd_k11_down; assign pd_k11_down = pd_k11_cin ? pd_k11_s1 : pd_k11_s0;
  logic [3:0] pd_k11_up; assign pd_k11_up = pd_k11_cin ? pd_k11_s2 : pd_k11_s1;
  logic pd_k11_guard; assign pd_k11_guard = f_mag[10];
  logic pd_k11_sticky; assign pd_k11_sticky = |f_mag[9:0];
  logic pd_k11_inexact; assign pd_k11_inexact = pd_k11_guard | pd_k11_sticky;
  logic pd_k11_increment; assign pd_k11_increment = (rnd == 3'd0) ? (pd_k11_guard && (pd_k11_sticky || pd_k11_down[0])) : (rnd == 3'd2) ? (pd_k11_inexact && f_s) : (rnd == 3'd3) ? (pd_k11_inexact && !f_s) : (rnd == 3'd5) ? pd_k11_inexact : 1'b0;
  logic [3:0] pd_k11_keep; assign pd_k11_keep = pd_k11_increment ? pd_k11_up : pd_k11_down;
  logic pd_k11_carry; assign pd_k11_carry = pd_k11_increment && (&pd_k11_down[3:0]);
  logic [25:0] pd_k11_sig; assign pd_k11_sig = pd_k11_carry ? (26'd1 << 25) : {pd_k11_keep[3:0], 22'd0};
  logic signed [18:0] pd_k11_ewide; assign pd_k11_ewide = pd_exp + (pd_k11_carry ? 19'sd1 : 19'sd0);
  logic signed [15:0] pd_k11_e; assign pd_k11_e = pd_k11_ewide[15:0];
  logic [1:0] pd_k11_special; assign pd_k11_special = pd_k11_inexact ? 2'd3 : 2'd0;
  logic [45:0] pd_k11_y; assign pd_k11_y = {pd_k11_special, f_s, pd_k11_e, pd_k11_sig, 1'b0};
  logic [3:0] pd_k12_a; assign pd_k12_a = pd_a[15:12];
  logic [3:0] pd_k12_b; assign pd_k12_b = pd_b[15:12];
  logic pd_k12_cin; assign pd_k12_cin = pd_a[12] ^ pd_b[12] ^ f_mag[12];
  logic [3:0] pd_k12_s0;
  logic [3:0] pd_k12_s1;
  logic [3:0] pd_k12_s2;
  logic pd_k12_cout;
  logic pd_k12_cout2;
  // post-normalization compound CPA at rounding cut 12
  fam_prefix_kogge_stone_w4_flag_dual u30 (.a(pd_k12_a), .b(pd_k12_b), .cin(1'b0), .s(pd_k12_s0), .cout(pd_k12_cout), .s1(pd_k12_s1));
  // cut 12: candidate for simultaneous low carry and rounding increment
  fam_incr_prefix_and #(.W(4), .STRUCTURE(1), .B(4), .TOPO(0)) u31 (.a(pd_k12_s1), .cin(1'b1), .s(pd_k12_s2), .cout(pd_k12_cout2));
  logic [3:0] pd_k12_down; assign pd_k12_down = pd_k12_cin ? pd_k12_s1 : pd_k12_s0;
  logic [3:0] pd_k12_up; assign pd_k12_up = pd_k12_cin ? pd_k12_s2 : pd_k12_s1;
  logic pd_k12_guard; assign pd_k12_guard = f_mag[11];
  logic pd_k12_sticky; assign pd_k12_sticky = |f_mag[10:0];
  logic pd_k12_inexact; assign pd_k12_inexact = pd_k12_guard | pd_k12_sticky;
  logic pd_k12_increment; assign pd_k12_increment = (rnd == 3'd0) ? (pd_k12_guard && (pd_k12_sticky || pd_k12_down[0])) : (rnd == 3'd2) ? (pd_k12_inexact && f_s) : (rnd == 3'd3) ? (pd_k12_inexact && !f_s) : (rnd == 3'd5) ? pd_k12_inexact : 1'b0;
  logic [3:0] pd_k12_keep; assign pd_k12_keep = pd_k12_increment ? pd_k12_up : pd_k12_down;
  logic pd_k12_carry; assign pd_k12_carry = pd_k12_increment && (&pd_k12_down[3:0]);
  logic [25:0] pd_k12_sig; assign pd_k12_sig = pd_k12_carry ? (26'd1 << 25) : {pd_k12_keep[3:0], 22'd0};
  logic signed [18:0] pd_k12_ewide; assign pd_k12_ewide = pd_exp + (pd_k12_carry ? 19'sd1 : 19'sd0);
  logic signed [15:0] pd_k12_e; assign pd_k12_e = pd_k12_ewide[15:0];
  logic [1:0] pd_k12_special; assign pd_k12_special = pd_k12_inexact ? 2'd3 : 2'd0;
  logic [45:0] pd_k12_y; assign pd_k12_y = {pd_k12_special, f_s, pd_k12_e, pd_k12_sig, 1'b0};
  logic [3:0] pd_k13_a; assign pd_k13_a = pd_a[16:13];
  logic [3:0] pd_k13_b; assign pd_k13_b = pd_b[16:13];
  logic pd_k13_cin; assign pd_k13_cin = pd_a[13] ^ pd_b[13] ^ f_mag[13];
  logic [3:0] pd_k13_s0;
  logic [3:0] pd_k13_s1;
  logic [3:0] pd_k13_s2;
  logic pd_k13_cout;
  logic pd_k13_cout2;
  // post-normalization compound CPA at rounding cut 13
  fam_prefix_kogge_stone_w4_flag_dual u32 (.a(pd_k13_a), .b(pd_k13_b), .cin(1'b0), .s(pd_k13_s0), .cout(pd_k13_cout), .s1(pd_k13_s1));
  // cut 13: candidate for simultaneous low carry and rounding increment
  fam_incr_prefix_and #(.W(4), .STRUCTURE(1), .B(4), .TOPO(0)) u33 (.a(pd_k13_s1), .cin(1'b1), .s(pd_k13_s2), .cout(pd_k13_cout2));
  logic [3:0] pd_k13_down; assign pd_k13_down = pd_k13_cin ? pd_k13_s1 : pd_k13_s0;
  logic [3:0] pd_k13_up; assign pd_k13_up = pd_k13_cin ? pd_k13_s2 : pd_k13_s1;
  logic pd_k13_guard; assign pd_k13_guard = f_mag[12];
  logic pd_k13_sticky; assign pd_k13_sticky = |f_mag[11:0];
  logic pd_k13_inexact; assign pd_k13_inexact = pd_k13_guard | pd_k13_sticky;
  logic pd_k13_increment; assign pd_k13_increment = (rnd == 3'd0) ? (pd_k13_guard && (pd_k13_sticky || pd_k13_down[0])) : (rnd == 3'd2) ? (pd_k13_inexact && f_s) : (rnd == 3'd3) ? (pd_k13_inexact && !f_s) : (rnd == 3'd5) ? pd_k13_inexact : 1'b0;
  logic [3:0] pd_k13_keep; assign pd_k13_keep = pd_k13_increment ? pd_k13_up : pd_k13_down;
  logic pd_k13_carry; assign pd_k13_carry = pd_k13_increment && (&pd_k13_down[3:0]);
  logic [25:0] pd_k13_sig; assign pd_k13_sig = pd_k13_carry ? (26'd1 << 25) : {pd_k13_keep[3:0], 22'd0};
  logic signed [18:0] pd_k13_ewide; assign pd_k13_ewide = pd_exp + (pd_k13_carry ? 19'sd1 : 19'sd0);
  logic signed [15:0] pd_k13_e; assign pd_k13_e = pd_k13_ewide[15:0];
  logic [1:0] pd_k13_special; assign pd_k13_special = pd_k13_inexact ? 2'd3 : 2'd0;
  logic [45:0] pd_k13_y; assign pd_k13_y = {pd_k13_special, f_s, pd_k13_e, pd_k13_sig, 1'b0};
  logic [3:0] pd_k14_a; assign pd_k14_a = pd_a[17:14];
  logic [3:0] pd_k14_b; assign pd_k14_b = pd_b[17:14];
  logic pd_k14_cin; assign pd_k14_cin = pd_a[14] ^ pd_b[14] ^ f_mag[14];
  logic [3:0] pd_k14_s0;
  logic [3:0] pd_k14_s1;
  logic [3:0] pd_k14_s2;
  logic pd_k14_cout;
  logic pd_k14_cout2;
  // post-normalization compound CPA at rounding cut 14
  fam_prefix_kogge_stone_w4_flag_dual u34 (.a(pd_k14_a), .b(pd_k14_b), .cin(1'b0), .s(pd_k14_s0), .cout(pd_k14_cout), .s1(pd_k14_s1));
  // cut 14: candidate for simultaneous low carry and rounding increment
  fam_incr_prefix_and #(.W(4), .STRUCTURE(1), .B(4), .TOPO(0)) u35 (.a(pd_k14_s1), .cin(1'b1), .s(pd_k14_s2), .cout(pd_k14_cout2));
  logic [3:0] pd_k14_down; assign pd_k14_down = pd_k14_cin ? pd_k14_s1 : pd_k14_s0;
  logic [3:0] pd_k14_up; assign pd_k14_up = pd_k14_cin ? pd_k14_s2 : pd_k14_s1;
  logic pd_k14_guard; assign pd_k14_guard = f_mag[13];
  logic pd_k14_sticky; assign pd_k14_sticky = |f_mag[12:0];
  logic pd_k14_inexact; assign pd_k14_inexact = pd_k14_guard | pd_k14_sticky;
  logic pd_k14_increment; assign pd_k14_increment = (rnd == 3'd0) ? (pd_k14_guard && (pd_k14_sticky || pd_k14_down[0])) : (rnd == 3'd2) ? (pd_k14_inexact && f_s) : (rnd == 3'd3) ? (pd_k14_inexact && !f_s) : (rnd == 3'd5) ? pd_k14_inexact : 1'b0;
  logic [3:0] pd_k14_keep; assign pd_k14_keep = pd_k14_increment ? pd_k14_up : pd_k14_down;
  logic pd_k14_carry; assign pd_k14_carry = pd_k14_increment && (&pd_k14_down[3:0]);
  logic [25:0] pd_k14_sig; assign pd_k14_sig = pd_k14_carry ? (26'd1 << 25) : {pd_k14_keep[3:0], 22'd0};
  logic signed [18:0] pd_k14_ewide; assign pd_k14_ewide = pd_exp + (pd_k14_carry ? 19'sd1 : 19'sd0);
  logic signed [15:0] pd_k14_e; assign pd_k14_e = pd_k14_ewide[15:0];
  logic [1:0] pd_k14_special; assign pd_k14_special = pd_k14_inexact ? 2'd3 : 2'd0;
  logic [45:0] pd_k14_y; assign pd_k14_y = {pd_k14_special, f_s, pd_k14_e, pd_k14_sig, 1'b0};
  logic [3:0] pd_k15_a; assign pd_k15_a = pd_a[18:15];
  logic [3:0] pd_k15_b; assign pd_k15_b = pd_b[18:15];
  logic pd_k15_cin; assign pd_k15_cin = pd_a[15] ^ pd_b[15] ^ f_mag[15];
  logic [3:0] pd_k15_s0;
  logic [3:0] pd_k15_s1;
  logic [3:0] pd_k15_s2;
  logic pd_k15_cout;
  logic pd_k15_cout2;
  // post-normalization compound CPA at rounding cut 15
  fam_prefix_kogge_stone_w4_flag_dual u36 (.a(pd_k15_a), .b(pd_k15_b), .cin(1'b0), .s(pd_k15_s0), .cout(pd_k15_cout), .s1(pd_k15_s1));
  // cut 15: candidate for simultaneous low carry and rounding increment
  fam_incr_prefix_and #(.W(4), .STRUCTURE(1), .B(4), .TOPO(0)) u37 (.a(pd_k15_s1), .cin(1'b1), .s(pd_k15_s2), .cout(pd_k15_cout2));
  logic [3:0] pd_k15_down; assign pd_k15_down = pd_k15_cin ? pd_k15_s1 : pd_k15_s0;
  logic [3:0] pd_k15_up; assign pd_k15_up = pd_k15_cin ? pd_k15_s2 : pd_k15_s1;
  logic pd_k15_guard; assign pd_k15_guard = f_mag[14];
  logic pd_k15_sticky; assign pd_k15_sticky = |f_mag[13:0];
  logic pd_k15_inexact; assign pd_k15_inexact = pd_k15_guard | pd_k15_sticky;
  logic pd_k15_increment; assign pd_k15_increment = (rnd == 3'd0) ? (pd_k15_guard && (pd_k15_sticky || pd_k15_down[0])) : (rnd == 3'd2) ? (pd_k15_inexact && f_s) : (rnd == 3'd3) ? (pd_k15_inexact && !f_s) : (rnd == 3'd5) ? pd_k15_inexact : 1'b0;
  logic [3:0] pd_k15_keep; assign pd_k15_keep = pd_k15_increment ? pd_k15_up : pd_k15_down;
  logic pd_k15_carry; assign pd_k15_carry = pd_k15_increment && (&pd_k15_down[3:0]);
  logic [25:0] pd_k15_sig; assign pd_k15_sig = pd_k15_carry ? (26'd1 << 25) : {pd_k15_keep[3:0], 22'd0};
  logic signed [18:0] pd_k15_ewide; assign pd_k15_ewide = pd_exp + (pd_k15_carry ? 19'sd1 : 19'sd0);
  logic signed [15:0] pd_k15_e; assign pd_k15_e = pd_k15_ewide[15:0];
  logic [1:0] pd_k15_special; assign pd_k15_special = pd_k15_inexact ? 2'd3 : 2'd0;
  logic [45:0] pd_k15_y; assign pd_k15_y = {pd_k15_special, f_s, pd_k15_e, pd_k15_sig, 1'b0};
  logic [3:0] pd_k16_a; assign pd_k16_a = pd_a[19:16];
  logic [3:0] pd_k16_b; assign pd_k16_b = pd_b[19:16];
  logic pd_k16_cin; assign pd_k16_cin = pd_a[16] ^ pd_b[16] ^ f_mag[16];
  logic [3:0] pd_k16_s0;
  logic [3:0] pd_k16_s1;
  logic [3:0] pd_k16_s2;
  logic pd_k16_cout;
  logic pd_k16_cout2;
  // post-normalization compound CPA at rounding cut 16
  fam_prefix_kogge_stone_w4_flag_dual u38 (.a(pd_k16_a), .b(pd_k16_b), .cin(1'b0), .s(pd_k16_s0), .cout(pd_k16_cout), .s1(pd_k16_s1));
  // cut 16: candidate for simultaneous low carry and rounding increment
  fam_incr_prefix_and #(.W(4), .STRUCTURE(1), .B(4), .TOPO(0)) u39 (.a(pd_k16_s1), .cin(1'b1), .s(pd_k16_s2), .cout(pd_k16_cout2));
  logic [3:0] pd_k16_down; assign pd_k16_down = pd_k16_cin ? pd_k16_s1 : pd_k16_s0;
  logic [3:0] pd_k16_up; assign pd_k16_up = pd_k16_cin ? pd_k16_s2 : pd_k16_s1;
  logic pd_k16_guard; assign pd_k16_guard = f_mag[15];
  logic pd_k16_sticky; assign pd_k16_sticky = |f_mag[14:0];
  logic pd_k16_inexact; assign pd_k16_inexact = pd_k16_guard | pd_k16_sticky;
  logic pd_k16_increment; assign pd_k16_increment = (rnd == 3'd0) ? (pd_k16_guard && (pd_k16_sticky || pd_k16_down[0])) : (rnd == 3'd2) ? (pd_k16_inexact && f_s) : (rnd == 3'd3) ? (pd_k16_inexact && !f_s) : (rnd == 3'd5) ? pd_k16_inexact : 1'b0;
  logic [3:0] pd_k16_keep; assign pd_k16_keep = pd_k16_increment ? pd_k16_up : pd_k16_down;
  logic pd_k16_carry; assign pd_k16_carry = pd_k16_increment && (&pd_k16_down[3:0]);
  logic [25:0] pd_k16_sig; assign pd_k16_sig = pd_k16_carry ? (26'd1 << 25) : {pd_k16_keep[3:0], 22'd0};
  logic signed [18:0] pd_k16_ewide; assign pd_k16_ewide = pd_exp + (pd_k16_carry ? 19'sd1 : 19'sd0);
  logic signed [15:0] pd_k16_e; assign pd_k16_e = pd_k16_ewide[15:0];
  logic [1:0] pd_k16_special; assign pd_k16_special = pd_k16_inexact ? 2'd3 : 2'd0;
  logic [45:0] pd_k16_y; assign pd_k16_y = {pd_k16_special, f_s, pd_k16_e, pd_k16_sig, 1'b0};
  logic [3:0] pd_k17_a; assign pd_k17_a = pd_a[20:17];
  logic [3:0] pd_k17_b; assign pd_k17_b = pd_b[20:17];
  logic pd_k17_cin; assign pd_k17_cin = pd_a[17] ^ pd_b[17] ^ f_mag[17];
  logic [3:0] pd_k17_s0;
  logic [3:0] pd_k17_s1;
  logic [3:0] pd_k17_s2;
  logic pd_k17_cout;
  logic pd_k17_cout2;
  // post-normalization compound CPA at rounding cut 17
  fam_prefix_kogge_stone_w4_flag_dual u40 (.a(pd_k17_a), .b(pd_k17_b), .cin(1'b0), .s(pd_k17_s0), .cout(pd_k17_cout), .s1(pd_k17_s1));
  // cut 17: candidate for simultaneous low carry and rounding increment
  fam_incr_prefix_and #(.W(4), .STRUCTURE(1), .B(4), .TOPO(0)) u41 (.a(pd_k17_s1), .cin(1'b1), .s(pd_k17_s2), .cout(pd_k17_cout2));
  logic [3:0] pd_k17_down; assign pd_k17_down = pd_k17_cin ? pd_k17_s1 : pd_k17_s0;
  logic [3:0] pd_k17_up; assign pd_k17_up = pd_k17_cin ? pd_k17_s2 : pd_k17_s1;
  logic pd_k17_guard; assign pd_k17_guard = f_mag[16];
  logic pd_k17_sticky; assign pd_k17_sticky = |f_mag[15:0];
  logic pd_k17_inexact; assign pd_k17_inexact = pd_k17_guard | pd_k17_sticky;
  logic pd_k17_increment; assign pd_k17_increment = (rnd == 3'd0) ? (pd_k17_guard && (pd_k17_sticky || pd_k17_down[0])) : (rnd == 3'd2) ? (pd_k17_inexact && f_s) : (rnd == 3'd3) ? (pd_k17_inexact && !f_s) : (rnd == 3'd5) ? pd_k17_inexact : 1'b0;
  logic [3:0] pd_k17_keep; assign pd_k17_keep = pd_k17_increment ? pd_k17_up : pd_k17_down;
  logic pd_k17_carry; assign pd_k17_carry = pd_k17_increment && (&pd_k17_down[3:0]);
  logic [25:0] pd_k17_sig; assign pd_k17_sig = pd_k17_carry ? (26'd1 << 25) : {pd_k17_keep[3:0], 22'd0};
  logic signed [18:0] pd_k17_ewide; assign pd_k17_ewide = pd_exp + (pd_k17_carry ? 19'sd1 : 19'sd0);
  logic signed [15:0] pd_k17_e; assign pd_k17_e = pd_k17_ewide[15:0];
  logic [1:0] pd_k17_special; assign pd_k17_special = pd_k17_inexact ? 2'd3 : 2'd0;
  logic [45:0] pd_k17_y; assign pd_k17_y = {pd_k17_special, f_s, pd_k17_e, pd_k17_sig, 1'b0};
  logic [3:0] pd_k18_a; assign pd_k18_a = pd_a[21:18];
  logic [3:0] pd_k18_b; assign pd_k18_b = pd_b[21:18];
  logic pd_k18_cin; assign pd_k18_cin = pd_a[18] ^ pd_b[18] ^ f_mag[18];
  logic [3:0] pd_k18_s0;
  logic [3:0] pd_k18_s1;
  logic [3:0] pd_k18_s2;
  logic pd_k18_cout;
  logic pd_k18_cout2;
  // post-normalization compound CPA at rounding cut 18
  fam_prefix_kogge_stone_w4_flag_dual u42 (.a(pd_k18_a), .b(pd_k18_b), .cin(1'b0), .s(pd_k18_s0), .cout(pd_k18_cout), .s1(pd_k18_s1));
  // cut 18: candidate for simultaneous low carry and rounding increment
  fam_incr_prefix_and #(.W(4), .STRUCTURE(1), .B(4), .TOPO(0)) u43 (.a(pd_k18_s1), .cin(1'b1), .s(pd_k18_s2), .cout(pd_k18_cout2));
  logic [3:0] pd_k18_down; assign pd_k18_down = pd_k18_cin ? pd_k18_s1 : pd_k18_s0;
  logic [3:0] pd_k18_up; assign pd_k18_up = pd_k18_cin ? pd_k18_s2 : pd_k18_s1;
  logic pd_k18_guard; assign pd_k18_guard = f_mag[17];
  logic pd_k18_sticky; assign pd_k18_sticky = |f_mag[16:0];
  logic pd_k18_inexact; assign pd_k18_inexact = pd_k18_guard | pd_k18_sticky;
  logic pd_k18_increment; assign pd_k18_increment = (rnd == 3'd0) ? (pd_k18_guard && (pd_k18_sticky || pd_k18_down[0])) : (rnd == 3'd2) ? (pd_k18_inexact && f_s) : (rnd == 3'd3) ? (pd_k18_inexact && !f_s) : (rnd == 3'd5) ? pd_k18_inexact : 1'b0;
  logic [3:0] pd_k18_keep; assign pd_k18_keep = pd_k18_increment ? pd_k18_up : pd_k18_down;
  logic pd_k18_carry; assign pd_k18_carry = pd_k18_increment && (&pd_k18_down[3:0]);
  logic [25:0] pd_k18_sig; assign pd_k18_sig = pd_k18_carry ? (26'd1 << 25) : {pd_k18_keep[3:0], 22'd0};
  logic signed [18:0] pd_k18_ewide; assign pd_k18_ewide = pd_exp + (pd_k18_carry ? 19'sd1 : 19'sd0);
  logic signed [15:0] pd_k18_e; assign pd_k18_e = pd_k18_ewide[15:0];
  logic [1:0] pd_k18_special; assign pd_k18_special = pd_k18_inexact ? 2'd3 : 2'd0;
  logic [45:0] pd_k18_y; assign pd_k18_y = {pd_k18_special, f_s, pd_k18_e, pd_k18_sig, 1'b0};
  logic [3:0] pd_k19_a; assign pd_k19_a = pd_a[22:19];
  logic [3:0] pd_k19_b; assign pd_k19_b = pd_b[22:19];
  logic pd_k19_cin; assign pd_k19_cin = pd_a[19] ^ pd_b[19] ^ f_mag[19];
  logic [3:0] pd_k19_s0;
  logic [3:0] pd_k19_s1;
  logic [3:0] pd_k19_s2;
  logic pd_k19_cout;
  logic pd_k19_cout2;
  // post-normalization compound CPA at rounding cut 19
  fam_prefix_kogge_stone_w4_flag_dual u44 (.a(pd_k19_a), .b(pd_k19_b), .cin(1'b0), .s(pd_k19_s0), .cout(pd_k19_cout), .s1(pd_k19_s1));
  // cut 19: candidate for simultaneous low carry and rounding increment
  fam_incr_prefix_and #(.W(4), .STRUCTURE(1), .B(4), .TOPO(0)) u45 (.a(pd_k19_s1), .cin(1'b1), .s(pd_k19_s2), .cout(pd_k19_cout2));
  logic [3:0] pd_k19_down; assign pd_k19_down = pd_k19_cin ? pd_k19_s1 : pd_k19_s0;
  logic [3:0] pd_k19_up; assign pd_k19_up = pd_k19_cin ? pd_k19_s2 : pd_k19_s1;
  logic pd_k19_guard; assign pd_k19_guard = f_mag[18];
  logic pd_k19_sticky; assign pd_k19_sticky = |f_mag[17:0];
  logic pd_k19_inexact; assign pd_k19_inexact = pd_k19_guard | pd_k19_sticky;
  logic pd_k19_increment; assign pd_k19_increment = (rnd == 3'd0) ? (pd_k19_guard && (pd_k19_sticky || pd_k19_down[0])) : (rnd == 3'd2) ? (pd_k19_inexact && f_s) : (rnd == 3'd3) ? (pd_k19_inexact && !f_s) : (rnd == 3'd5) ? pd_k19_inexact : 1'b0;
  logic [3:0] pd_k19_keep; assign pd_k19_keep = pd_k19_increment ? pd_k19_up : pd_k19_down;
  logic pd_k19_carry; assign pd_k19_carry = pd_k19_increment && (&pd_k19_down[3:0]);
  logic [25:0] pd_k19_sig; assign pd_k19_sig = pd_k19_carry ? (26'd1 << 25) : {pd_k19_keep[3:0], 22'd0};
  logic signed [18:0] pd_k19_ewide; assign pd_k19_ewide = pd_exp + (pd_k19_carry ? 19'sd1 : 19'sd0);
  logic signed [15:0] pd_k19_e; assign pd_k19_e = pd_k19_ewide[15:0];
  logic [1:0] pd_k19_special; assign pd_k19_special = pd_k19_inexact ? 2'd3 : 2'd0;
  logic [45:0] pd_k19_y; assign pd_k19_y = {pd_k19_special, f_s, pd_k19_e, pd_k19_sig, 1'b0};
  logic [3:0] pd_k20_a; assign pd_k20_a = pd_a[23:20];
  logic [3:0] pd_k20_b; assign pd_k20_b = pd_b[23:20];
  logic pd_k20_cin; assign pd_k20_cin = pd_a[20] ^ pd_b[20] ^ f_mag[20];
  logic [3:0] pd_k20_s0;
  logic [3:0] pd_k20_s1;
  logic [3:0] pd_k20_s2;
  logic pd_k20_cout;
  logic pd_k20_cout2;
  // post-normalization compound CPA at rounding cut 20
  fam_prefix_kogge_stone_w4_flag_dual u46 (.a(pd_k20_a), .b(pd_k20_b), .cin(1'b0), .s(pd_k20_s0), .cout(pd_k20_cout), .s1(pd_k20_s1));
  // cut 20: candidate for simultaneous low carry and rounding increment
  fam_incr_prefix_and #(.W(4), .STRUCTURE(1), .B(4), .TOPO(0)) u47 (.a(pd_k20_s1), .cin(1'b1), .s(pd_k20_s2), .cout(pd_k20_cout2));
  logic [3:0] pd_k20_down; assign pd_k20_down = pd_k20_cin ? pd_k20_s1 : pd_k20_s0;
  logic [3:0] pd_k20_up; assign pd_k20_up = pd_k20_cin ? pd_k20_s2 : pd_k20_s1;
  logic pd_k20_guard; assign pd_k20_guard = f_mag[19];
  logic pd_k20_sticky; assign pd_k20_sticky = |f_mag[18:0];
  logic pd_k20_inexact; assign pd_k20_inexact = pd_k20_guard | pd_k20_sticky;
  logic pd_k20_increment; assign pd_k20_increment = (rnd == 3'd0) ? (pd_k20_guard && (pd_k20_sticky || pd_k20_down[0])) : (rnd == 3'd2) ? (pd_k20_inexact && f_s) : (rnd == 3'd3) ? (pd_k20_inexact && !f_s) : (rnd == 3'd5) ? pd_k20_inexact : 1'b0;
  logic [3:0] pd_k20_keep; assign pd_k20_keep = pd_k20_increment ? pd_k20_up : pd_k20_down;
  logic pd_k20_carry; assign pd_k20_carry = pd_k20_increment && (&pd_k20_down[3:0]);
  logic [25:0] pd_k20_sig; assign pd_k20_sig = pd_k20_carry ? (26'd1 << 25) : {pd_k20_keep[3:0], 22'd0};
  logic signed [18:0] pd_k20_ewide; assign pd_k20_ewide = pd_exp + (pd_k20_carry ? 19'sd1 : 19'sd0);
  logic signed [15:0] pd_k20_e; assign pd_k20_e = pd_k20_ewide[15:0];
  logic [1:0] pd_k20_special; assign pd_k20_special = pd_k20_inexact ? 2'd3 : 2'd0;
  logic [45:0] pd_k20_y; assign pd_k20_y = {pd_k20_special, f_s, pd_k20_e, pd_k20_sig, 1'b0};
  logic [3:0] pd_k21_a; assign pd_k21_a = pd_a[24:21];
  logic [3:0] pd_k21_b; assign pd_k21_b = pd_b[24:21];
  logic pd_k21_cin; assign pd_k21_cin = pd_a[21] ^ pd_b[21] ^ f_mag[21];
  logic [3:0] pd_k21_s0;
  logic [3:0] pd_k21_s1;
  logic [3:0] pd_k21_s2;
  logic pd_k21_cout;
  logic pd_k21_cout2;
  // post-normalization compound CPA at rounding cut 21
  fam_prefix_kogge_stone_w4_flag_dual u48 (.a(pd_k21_a), .b(pd_k21_b), .cin(1'b0), .s(pd_k21_s0), .cout(pd_k21_cout), .s1(pd_k21_s1));
  // cut 21: candidate for simultaneous low carry and rounding increment
  fam_incr_prefix_and #(.W(4), .STRUCTURE(1), .B(4), .TOPO(0)) u49 (.a(pd_k21_s1), .cin(1'b1), .s(pd_k21_s2), .cout(pd_k21_cout2));
  logic [3:0] pd_k21_down; assign pd_k21_down = pd_k21_cin ? pd_k21_s1 : pd_k21_s0;
  logic [3:0] pd_k21_up; assign pd_k21_up = pd_k21_cin ? pd_k21_s2 : pd_k21_s1;
  logic pd_k21_guard; assign pd_k21_guard = f_mag[20];
  logic pd_k21_sticky; assign pd_k21_sticky = |f_mag[19:0];
  logic pd_k21_inexact; assign pd_k21_inexact = pd_k21_guard | pd_k21_sticky;
  logic pd_k21_increment; assign pd_k21_increment = (rnd == 3'd0) ? (pd_k21_guard && (pd_k21_sticky || pd_k21_down[0])) : (rnd == 3'd2) ? (pd_k21_inexact && f_s) : (rnd == 3'd3) ? (pd_k21_inexact && !f_s) : (rnd == 3'd5) ? pd_k21_inexact : 1'b0;
  logic [3:0] pd_k21_keep; assign pd_k21_keep = pd_k21_increment ? pd_k21_up : pd_k21_down;
  logic pd_k21_carry; assign pd_k21_carry = pd_k21_increment && (&pd_k21_down[3:0]);
  logic [25:0] pd_k21_sig; assign pd_k21_sig = pd_k21_carry ? (26'd1 << 25) : {pd_k21_keep[3:0], 22'd0};
  logic signed [18:0] pd_k21_ewide; assign pd_k21_ewide = pd_exp + (pd_k21_carry ? 19'sd1 : 19'sd0);
  logic signed [15:0] pd_k21_e; assign pd_k21_e = pd_k21_ewide[15:0];
  logic [1:0] pd_k21_special; assign pd_k21_special = pd_k21_inexact ? 2'd3 : 2'd0;
  logic [45:0] pd_k21_y; assign pd_k21_y = {pd_k21_special, f_s, pd_k21_e, pd_k21_sig, 1'b0};
  logic [3:0] pd_k22_a; assign pd_k22_a = pd_a[25:22];
  logic [3:0] pd_k22_b; assign pd_k22_b = pd_b[25:22];
  logic pd_k22_cin; assign pd_k22_cin = pd_a[22] ^ pd_b[22] ^ f_mag[22];
  logic [3:0] pd_k22_s0;
  logic [3:0] pd_k22_s1;
  logic [3:0] pd_k22_s2;
  logic pd_k22_cout;
  logic pd_k22_cout2;
  // post-normalization compound CPA at rounding cut 22
  fam_prefix_kogge_stone_w4_flag_dual u50 (.a(pd_k22_a), .b(pd_k22_b), .cin(1'b0), .s(pd_k22_s0), .cout(pd_k22_cout), .s1(pd_k22_s1));
  // cut 22: candidate for simultaneous low carry and rounding increment
  fam_incr_prefix_and #(.W(4), .STRUCTURE(1), .B(4), .TOPO(0)) u51 (.a(pd_k22_s1), .cin(1'b1), .s(pd_k22_s2), .cout(pd_k22_cout2));
  logic [3:0] pd_k22_down; assign pd_k22_down = pd_k22_cin ? pd_k22_s1 : pd_k22_s0;
  logic [3:0] pd_k22_up; assign pd_k22_up = pd_k22_cin ? pd_k22_s2 : pd_k22_s1;
  logic pd_k22_guard; assign pd_k22_guard = f_mag[21];
  logic pd_k22_sticky; assign pd_k22_sticky = |f_mag[20:0];
  logic pd_k22_inexact; assign pd_k22_inexact = pd_k22_guard | pd_k22_sticky;
  logic pd_k22_increment; assign pd_k22_increment = (rnd == 3'd0) ? (pd_k22_guard && (pd_k22_sticky || pd_k22_down[0])) : (rnd == 3'd2) ? (pd_k22_inexact && f_s) : (rnd == 3'd3) ? (pd_k22_inexact && !f_s) : (rnd == 3'd5) ? pd_k22_inexact : 1'b0;
  logic [3:0] pd_k22_keep; assign pd_k22_keep = pd_k22_increment ? pd_k22_up : pd_k22_down;
  logic pd_k22_carry; assign pd_k22_carry = pd_k22_increment && (&pd_k22_down[3:0]);
  logic [25:0] pd_k22_sig; assign pd_k22_sig = pd_k22_carry ? (26'd1 << 25) : {pd_k22_keep[3:0], 22'd0};
  logic signed [18:0] pd_k22_ewide; assign pd_k22_ewide = pd_exp + (pd_k22_carry ? 19'sd1 : 19'sd0);
  logic signed [15:0] pd_k22_e; assign pd_k22_e = pd_k22_ewide[15:0];
  logic [1:0] pd_k22_special; assign pd_k22_special = pd_k22_inexact ? 2'd3 : 2'd0;
  logic [45:0] pd_k22_y; assign pd_k22_y = {pd_k22_special, f_s, pd_k22_e, pd_k22_sig, 1'b0};
  logic [3:0] pd_k23_a; assign pd_k23_a = pd_a[26:23];
  logic [3:0] pd_k23_b; assign pd_k23_b = pd_b[26:23];
  logic pd_k23_cin; assign pd_k23_cin = pd_a[23] ^ pd_b[23] ^ f_mag[23];
  logic [3:0] pd_k23_s0;
  logic [3:0] pd_k23_s1;
  logic [3:0] pd_k23_s2;
  logic pd_k23_cout;
  logic pd_k23_cout2;
  // post-normalization compound CPA at rounding cut 23
  fam_prefix_kogge_stone_w4_flag_dual u52 (.a(pd_k23_a), .b(pd_k23_b), .cin(1'b0), .s(pd_k23_s0), .cout(pd_k23_cout), .s1(pd_k23_s1));
  // cut 23: candidate for simultaneous low carry and rounding increment
  fam_incr_prefix_and #(.W(4), .STRUCTURE(1), .B(4), .TOPO(0)) u53 (.a(pd_k23_s1), .cin(1'b1), .s(pd_k23_s2), .cout(pd_k23_cout2));
  logic [3:0] pd_k23_down; assign pd_k23_down = pd_k23_cin ? pd_k23_s1 : pd_k23_s0;
  logic [3:0] pd_k23_up; assign pd_k23_up = pd_k23_cin ? pd_k23_s2 : pd_k23_s1;
  logic pd_k23_guard; assign pd_k23_guard = f_mag[22];
  logic pd_k23_sticky; assign pd_k23_sticky = |f_mag[21:0];
  logic pd_k23_inexact; assign pd_k23_inexact = pd_k23_guard | pd_k23_sticky;
  logic pd_k23_increment; assign pd_k23_increment = (rnd == 3'd0) ? (pd_k23_guard && (pd_k23_sticky || pd_k23_down[0])) : (rnd == 3'd2) ? (pd_k23_inexact && f_s) : (rnd == 3'd3) ? (pd_k23_inexact && !f_s) : (rnd == 3'd5) ? pd_k23_inexact : 1'b0;
  logic [3:0] pd_k23_keep; assign pd_k23_keep = pd_k23_increment ? pd_k23_up : pd_k23_down;
  logic pd_k23_carry; assign pd_k23_carry = pd_k23_increment && (&pd_k23_down[3:0]);
  logic [25:0] pd_k23_sig; assign pd_k23_sig = pd_k23_carry ? (26'd1 << 25) : {pd_k23_keep[3:0], 22'd0};
  logic signed [18:0] pd_k23_ewide; assign pd_k23_ewide = pd_exp + (pd_k23_carry ? 19'sd1 : 19'sd0);
  logic signed [15:0] pd_k23_e; assign pd_k23_e = pd_k23_ewide[15:0];
  logic [1:0] pd_k23_special; assign pd_k23_special = pd_k23_inexact ? 2'd3 : 2'd0;
  logic [45:0] pd_k23_y; assign pd_k23_y = {pd_k23_special, f_s, pd_k23_e, pd_k23_sig, 1'b0};
  logic [3:0] pd_k24_a; assign pd_k24_a = pd_a[27:24];
  logic [3:0] pd_k24_b; assign pd_k24_b = pd_b[27:24];
  logic pd_k24_cin; assign pd_k24_cin = pd_a[24] ^ pd_b[24] ^ f_mag[24];
  logic [3:0] pd_k24_s0;
  logic [3:0] pd_k24_s1;
  logic [3:0] pd_k24_s2;
  logic pd_k24_cout;
  logic pd_k24_cout2;
  // post-normalization compound CPA at rounding cut 24
  fam_prefix_kogge_stone_w4_flag_dual u54 (.a(pd_k24_a), .b(pd_k24_b), .cin(1'b0), .s(pd_k24_s0), .cout(pd_k24_cout), .s1(pd_k24_s1));
  // cut 24: candidate for simultaneous low carry and rounding increment
  fam_incr_prefix_and #(.W(4), .STRUCTURE(1), .B(4), .TOPO(0)) u55 (.a(pd_k24_s1), .cin(1'b1), .s(pd_k24_s2), .cout(pd_k24_cout2));
  logic [3:0] pd_k24_down; assign pd_k24_down = pd_k24_cin ? pd_k24_s1 : pd_k24_s0;
  logic [3:0] pd_k24_up; assign pd_k24_up = pd_k24_cin ? pd_k24_s2 : pd_k24_s1;
  logic pd_k24_guard; assign pd_k24_guard = f_mag[23];
  logic pd_k24_sticky; assign pd_k24_sticky = |f_mag[22:0];
  logic pd_k24_inexact; assign pd_k24_inexact = pd_k24_guard | pd_k24_sticky;
  logic pd_k24_increment; assign pd_k24_increment = (rnd == 3'd0) ? (pd_k24_guard && (pd_k24_sticky || pd_k24_down[0])) : (rnd == 3'd2) ? (pd_k24_inexact && f_s) : (rnd == 3'd3) ? (pd_k24_inexact && !f_s) : (rnd == 3'd5) ? pd_k24_inexact : 1'b0;
  logic [3:0] pd_k24_keep; assign pd_k24_keep = pd_k24_increment ? pd_k24_up : pd_k24_down;
  logic pd_k24_carry; assign pd_k24_carry = pd_k24_increment && (&pd_k24_down[3:0]);
  logic [25:0] pd_k24_sig; assign pd_k24_sig = pd_k24_carry ? (26'd1 << 25) : {pd_k24_keep[3:0], 22'd0};
  logic signed [18:0] pd_k24_ewide; assign pd_k24_ewide = pd_exp + (pd_k24_carry ? 19'sd1 : 19'sd0);
  logic signed [15:0] pd_k24_e; assign pd_k24_e = pd_k24_ewide[15:0];
  logic [1:0] pd_k24_special; assign pd_k24_special = pd_k24_inexact ? 2'd3 : 2'd0;
  logic [45:0] pd_k24_y; assign pd_k24_y = {pd_k24_special, f_s, pd_k24_e, pd_k24_sig, 1'b0};
  logic [3:0] pd_k25_a; assign pd_k25_a = pd_a[28:25];
  logic [3:0] pd_k25_b; assign pd_k25_b = pd_b[28:25];
  logic pd_k25_cin; assign pd_k25_cin = pd_a[25] ^ pd_b[25] ^ f_mag[25];
  logic [3:0] pd_k25_s0;
  logic [3:0] pd_k25_s1;
  logic [3:0] pd_k25_s2;
  logic pd_k25_cout;
  logic pd_k25_cout2;
  // post-normalization compound CPA at rounding cut 25
  fam_prefix_kogge_stone_w4_flag_dual u56 (.a(pd_k25_a), .b(pd_k25_b), .cin(1'b0), .s(pd_k25_s0), .cout(pd_k25_cout), .s1(pd_k25_s1));
  // cut 25: candidate for simultaneous low carry and rounding increment
  fam_incr_prefix_and #(.W(4), .STRUCTURE(1), .B(4), .TOPO(0)) u57 (.a(pd_k25_s1), .cin(1'b1), .s(pd_k25_s2), .cout(pd_k25_cout2));
  logic [3:0] pd_k25_down; assign pd_k25_down = pd_k25_cin ? pd_k25_s1 : pd_k25_s0;
  logic [3:0] pd_k25_up; assign pd_k25_up = pd_k25_cin ? pd_k25_s2 : pd_k25_s1;
  logic pd_k25_guard; assign pd_k25_guard = f_mag[24];
  logic pd_k25_sticky; assign pd_k25_sticky = |f_mag[23:0];
  logic pd_k25_inexact; assign pd_k25_inexact = pd_k25_guard | pd_k25_sticky;
  logic pd_k25_increment; assign pd_k25_increment = (rnd == 3'd0) ? (pd_k25_guard && (pd_k25_sticky || pd_k25_down[0])) : (rnd == 3'd2) ? (pd_k25_inexact && f_s) : (rnd == 3'd3) ? (pd_k25_inexact && !f_s) : (rnd == 3'd5) ? pd_k25_inexact : 1'b0;
  logic [3:0] pd_k25_keep; assign pd_k25_keep = pd_k25_increment ? pd_k25_up : pd_k25_down;
  logic pd_k25_carry; assign pd_k25_carry = pd_k25_increment && (&pd_k25_down[3:0]);
  logic [25:0] pd_k25_sig; assign pd_k25_sig = pd_k25_carry ? (26'd1 << 25) : {pd_k25_keep[3:0], 22'd0};
  logic signed [18:0] pd_k25_ewide; assign pd_k25_ewide = pd_exp + (pd_k25_carry ? 19'sd1 : 19'sd0);
  logic signed [15:0] pd_k25_e; assign pd_k25_e = pd_k25_ewide[15:0];
  logic [1:0] pd_k25_special; assign pd_k25_special = pd_k25_inexact ? 2'd3 : 2'd0;
  logic [45:0] pd_k25_y; assign pd_k25_y = {pd_k25_special, f_s, pd_k25_e, pd_k25_sig, 1'b0};
  logic [3:0] pd_k26_a; assign pd_k26_a = pd_a[29:26];
  logic [3:0] pd_k26_b; assign pd_k26_b = pd_b[29:26];
  logic pd_k26_cin; assign pd_k26_cin = pd_a[26] ^ pd_b[26] ^ f_mag[26];
  logic [3:0] pd_k26_s0;
  logic [3:0] pd_k26_s1;
  logic [3:0] pd_k26_s2;
  logic pd_k26_cout;
  logic pd_k26_cout2;
  // post-normalization compound CPA at rounding cut 26
  fam_prefix_kogge_stone_w4_flag_dual u58 (.a(pd_k26_a), .b(pd_k26_b), .cin(1'b0), .s(pd_k26_s0), .cout(pd_k26_cout), .s1(pd_k26_s1));
  // cut 26: candidate for simultaneous low carry and rounding increment
  fam_incr_prefix_and #(.W(4), .STRUCTURE(1), .B(4), .TOPO(0)) u59 (.a(pd_k26_s1), .cin(1'b1), .s(pd_k26_s2), .cout(pd_k26_cout2));
  logic [3:0] pd_k26_down; assign pd_k26_down = pd_k26_cin ? pd_k26_s1 : pd_k26_s0;
  logic [3:0] pd_k26_up; assign pd_k26_up = pd_k26_cin ? pd_k26_s2 : pd_k26_s1;
  logic pd_k26_guard; assign pd_k26_guard = f_mag[25];
  logic pd_k26_sticky; assign pd_k26_sticky = |f_mag[24:0];
  logic pd_k26_inexact; assign pd_k26_inexact = pd_k26_guard | pd_k26_sticky;
  logic pd_k26_increment; assign pd_k26_increment = (rnd == 3'd0) ? (pd_k26_guard && (pd_k26_sticky || pd_k26_down[0])) : (rnd == 3'd2) ? (pd_k26_inexact && f_s) : (rnd == 3'd3) ? (pd_k26_inexact && !f_s) : (rnd == 3'd5) ? pd_k26_inexact : 1'b0;
  logic [3:0] pd_k26_keep; assign pd_k26_keep = pd_k26_increment ? pd_k26_up : pd_k26_down;
  logic pd_k26_carry; assign pd_k26_carry = pd_k26_increment && (&pd_k26_down[3:0]);
  logic [25:0] pd_k26_sig; assign pd_k26_sig = pd_k26_carry ? (26'd1 << 25) : {pd_k26_keep[3:0], 22'd0};
  logic signed [18:0] pd_k26_ewide; assign pd_k26_ewide = pd_exp + (pd_k26_carry ? 19'sd1 : 19'sd0);
  logic signed [15:0] pd_k26_e; assign pd_k26_e = pd_k26_ewide[15:0];
  logic [1:0] pd_k26_special; assign pd_k26_special = pd_k26_inexact ? 2'd3 : 2'd0;
  logic [45:0] pd_k26_y; assign pd_k26_y = {pd_k26_special, f_s, pd_k26_e, pd_k26_sig, 1'b0};
  logic [3:0] pd_k27_a; assign pd_k27_a = pd_a[30:27];
  logic [3:0] pd_k27_b; assign pd_k27_b = pd_b[30:27];
  logic pd_k27_cin; assign pd_k27_cin = pd_a[27] ^ pd_b[27] ^ f_mag[27];
  logic [3:0] pd_k27_s0;
  logic [3:0] pd_k27_s1;
  logic [3:0] pd_k27_s2;
  logic pd_k27_cout;
  logic pd_k27_cout2;
  // post-normalization compound CPA at rounding cut 27
  fam_prefix_kogge_stone_w4_flag_dual u60 (.a(pd_k27_a), .b(pd_k27_b), .cin(1'b0), .s(pd_k27_s0), .cout(pd_k27_cout), .s1(pd_k27_s1));
  // cut 27: candidate for simultaneous low carry and rounding increment
  fam_incr_prefix_and #(.W(4), .STRUCTURE(1), .B(4), .TOPO(0)) u61 (.a(pd_k27_s1), .cin(1'b1), .s(pd_k27_s2), .cout(pd_k27_cout2));
  logic [3:0] pd_k27_down; assign pd_k27_down = pd_k27_cin ? pd_k27_s1 : pd_k27_s0;
  logic [3:0] pd_k27_up; assign pd_k27_up = pd_k27_cin ? pd_k27_s2 : pd_k27_s1;
  logic pd_k27_guard; assign pd_k27_guard = f_mag[26];
  logic pd_k27_sticky; assign pd_k27_sticky = |f_mag[25:0];
  logic pd_k27_inexact; assign pd_k27_inexact = pd_k27_guard | pd_k27_sticky;
  logic pd_k27_increment; assign pd_k27_increment = (rnd == 3'd0) ? (pd_k27_guard && (pd_k27_sticky || pd_k27_down[0])) : (rnd == 3'd2) ? (pd_k27_inexact && f_s) : (rnd == 3'd3) ? (pd_k27_inexact && !f_s) : (rnd == 3'd5) ? pd_k27_inexact : 1'b0;
  logic [3:0] pd_k27_keep; assign pd_k27_keep = pd_k27_increment ? pd_k27_up : pd_k27_down;
  logic pd_k27_carry; assign pd_k27_carry = pd_k27_increment && (&pd_k27_down[3:0]);
  logic [25:0] pd_k27_sig; assign pd_k27_sig = pd_k27_carry ? (26'd1 << 25) : {pd_k27_keep[3:0], 22'd0};
  logic signed [18:0] pd_k27_ewide; assign pd_k27_ewide = pd_exp + (pd_k27_carry ? 19'sd1 : 19'sd0);
  logic signed [15:0] pd_k27_e; assign pd_k27_e = pd_k27_ewide[15:0];
  logic [1:0] pd_k27_special; assign pd_k27_special = pd_k27_inexact ? 2'd3 : 2'd0;
  logic [45:0] pd_k27_y; assign pd_k27_y = {pd_k27_special, f_s, pd_k27_e, pd_k27_sig, 1'b0};
  logic [3:0] pd_k28_a; assign pd_k28_a = pd_a[31:28];
  logic [3:0] pd_k28_b; assign pd_k28_b = pd_b[31:28];
  logic pd_k28_cin; assign pd_k28_cin = pd_a[28] ^ pd_b[28] ^ f_mag[28];
  logic [3:0] pd_k28_s0;
  logic [3:0] pd_k28_s1;
  logic [3:0] pd_k28_s2;
  logic pd_k28_cout;
  logic pd_k28_cout2;
  // post-normalization compound CPA at rounding cut 28
  fam_prefix_kogge_stone_w4_flag_dual u62 (.a(pd_k28_a), .b(pd_k28_b), .cin(1'b0), .s(pd_k28_s0), .cout(pd_k28_cout), .s1(pd_k28_s1));
  // cut 28: candidate for simultaneous low carry and rounding increment
  fam_incr_prefix_and #(.W(4), .STRUCTURE(1), .B(4), .TOPO(0)) u63 (.a(pd_k28_s1), .cin(1'b1), .s(pd_k28_s2), .cout(pd_k28_cout2));
  logic [3:0] pd_k28_down; assign pd_k28_down = pd_k28_cin ? pd_k28_s1 : pd_k28_s0;
  logic [3:0] pd_k28_up; assign pd_k28_up = pd_k28_cin ? pd_k28_s2 : pd_k28_s1;
  logic pd_k28_guard; assign pd_k28_guard = f_mag[27];
  logic pd_k28_sticky; assign pd_k28_sticky = |f_mag[26:0];
  logic pd_k28_inexact; assign pd_k28_inexact = pd_k28_guard | pd_k28_sticky;
  logic pd_k28_increment; assign pd_k28_increment = (rnd == 3'd0) ? (pd_k28_guard && (pd_k28_sticky || pd_k28_down[0])) : (rnd == 3'd2) ? (pd_k28_inexact && f_s) : (rnd == 3'd3) ? (pd_k28_inexact && !f_s) : (rnd == 3'd5) ? pd_k28_inexact : 1'b0;
  logic [3:0] pd_k28_keep; assign pd_k28_keep = pd_k28_increment ? pd_k28_up : pd_k28_down;
  logic pd_k28_carry; assign pd_k28_carry = pd_k28_increment && (&pd_k28_down[3:0]);
  logic [25:0] pd_k28_sig; assign pd_k28_sig = pd_k28_carry ? (26'd1 << 25) : {pd_k28_keep[3:0], 22'd0};
  logic signed [18:0] pd_k28_ewide; assign pd_k28_ewide = pd_exp + (pd_k28_carry ? 19'sd1 : 19'sd0);
  logic signed [15:0] pd_k28_e; assign pd_k28_e = pd_k28_ewide[15:0];
  logic [1:0] pd_k28_special; assign pd_k28_special = pd_k28_inexact ? 2'd3 : 2'd0;
  logic [45:0] pd_k28_y; assign pd_k28_y = {pd_k28_special, f_s, pd_k28_e, pd_k28_sig, 1'b0};
  logic [3:0] pd_k29_a; assign pd_k29_a = pd_a[32:29];
  logic [3:0] pd_k29_b; assign pd_k29_b = pd_b[32:29];
  logic pd_k29_cin; assign pd_k29_cin = pd_a[29] ^ pd_b[29] ^ f_mag[29];
  logic [3:0] pd_k29_s0;
  logic [3:0] pd_k29_s1;
  logic [3:0] pd_k29_s2;
  logic pd_k29_cout;
  logic pd_k29_cout2;
  // post-normalization compound CPA at rounding cut 29
  fam_prefix_kogge_stone_w4_flag_dual u64 (.a(pd_k29_a), .b(pd_k29_b), .cin(1'b0), .s(pd_k29_s0), .cout(pd_k29_cout), .s1(pd_k29_s1));
  // cut 29: candidate for simultaneous low carry and rounding increment
  fam_incr_prefix_and #(.W(4), .STRUCTURE(1), .B(4), .TOPO(0)) u65 (.a(pd_k29_s1), .cin(1'b1), .s(pd_k29_s2), .cout(pd_k29_cout2));
  logic [3:0] pd_k29_down; assign pd_k29_down = pd_k29_cin ? pd_k29_s1 : pd_k29_s0;
  logic [3:0] pd_k29_up; assign pd_k29_up = pd_k29_cin ? pd_k29_s2 : pd_k29_s1;
  logic pd_k29_guard; assign pd_k29_guard = f_mag[28];
  logic pd_k29_sticky; assign pd_k29_sticky = |f_mag[27:0];
  logic pd_k29_inexact; assign pd_k29_inexact = pd_k29_guard | pd_k29_sticky;
  logic pd_k29_increment; assign pd_k29_increment = (rnd == 3'd0) ? (pd_k29_guard && (pd_k29_sticky || pd_k29_down[0])) : (rnd == 3'd2) ? (pd_k29_inexact && f_s) : (rnd == 3'd3) ? (pd_k29_inexact && !f_s) : (rnd == 3'd5) ? pd_k29_inexact : 1'b0;
  logic [3:0] pd_k29_keep; assign pd_k29_keep = pd_k29_increment ? pd_k29_up : pd_k29_down;
  logic pd_k29_carry; assign pd_k29_carry = pd_k29_increment && (&pd_k29_down[3:0]);
  logic [25:0] pd_k29_sig; assign pd_k29_sig = pd_k29_carry ? (26'd1 << 25) : {pd_k29_keep[3:0], 22'd0};
  logic signed [18:0] pd_k29_ewide; assign pd_k29_ewide = pd_exp + (pd_k29_carry ? 19'sd1 : 19'sd0);
  logic signed [15:0] pd_k29_e; assign pd_k29_e = pd_k29_ewide[15:0];
  logic [1:0] pd_k29_special; assign pd_k29_special = pd_k29_inexact ? 2'd3 : 2'd0;
  logic [45:0] pd_k29_y; assign pd_k29_y = {pd_k29_special, f_s, pd_k29_e, pd_k29_sig, 1'b0};
  logic [3:0] pd_k30_a; assign pd_k30_a = pd_a[33:30];
  logic [3:0] pd_k30_b; assign pd_k30_b = pd_b[33:30];
  logic pd_k30_cin; assign pd_k30_cin = pd_a[30] ^ pd_b[30] ^ f_mag[30];
  logic [3:0] pd_k30_s0;
  logic [3:0] pd_k30_s1;
  logic [3:0] pd_k30_s2;
  logic pd_k30_cout;
  logic pd_k30_cout2;
  // post-normalization compound CPA at rounding cut 30
  fam_prefix_kogge_stone_w4_flag_dual u66 (.a(pd_k30_a), .b(pd_k30_b), .cin(1'b0), .s(pd_k30_s0), .cout(pd_k30_cout), .s1(pd_k30_s1));
  // cut 30: candidate for simultaneous low carry and rounding increment
  fam_incr_prefix_and #(.W(4), .STRUCTURE(1), .B(4), .TOPO(0)) u67 (.a(pd_k30_s1), .cin(1'b1), .s(pd_k30_s2), .cout(pd_k30_cout2));
  logic [3:0] pd_k30_down; assign pd_k30_down = pd_k30_cin ? pd_k30_s1 : pd_k30_s0;
  logic [3:0] pd_k30_up; assign pd_k30_up = pd_k30_cin ? pd_k30_s2 : pd_k30_s1;
  logic pd_k30_guard; assign pd_k30_guard = f_mag[29];
  logic pd_k30_sticky; assign pd_k30_sticky = |f_mag[28:0];
  logic pd_k30_inexact; assign pd_k30_inexact = pd_k30_guard | pd_k30_sticky;
  logic pd_k30_increment; assign pd_k30_increment = (rnd == 3'd0) ? (pd_k30_guard && (pd_k30_sticky || pd_k30_down[0])) : (rnd == 3'd2) ? (pd_k30_inexact && f_s) : (rnd == 3'd3) ? (pd_k30_inexact && !f_s) : (rnd == 3'd5) ? pd_k30_inexact : 1'b0;
  logic [3:0] pd_k30_keep; assign pd_k30_keep = pd_k30_increment ? pd_k30_up : pd_k30_down;
  logic pd_k30_carry; assign pd_k30_carry = pd_k30_increment && (&pd_k30_down[3:0]);
  logic [25:0] pd_k30_sig; assign pd_k30_sig = pd_k30_carry ? (26'd1 << 25) : {pd_k30_keep[3:0], 22'd0};
  logic signed [18:0] pd_k30_ewide; assign pd_k30_ewide = pd_exp + (pd_k30_carry ? 19'sd1 : 19'sd0);
  logic signed [15:0] pd_k30_e; assign pd_k30_e = pd_k30_ewide[15:0];
  logic [1:0] pd_k30_special; assign pd_k30_special = pd_k30_inexact ? 2'd3 : 2'd0;
  logic [45:0] pd_k30_y; assign pd_k30_y = {pd_k30_special, f_s, pd_k30_e, pd_k30_sig, 1'b0};
  logic [3:0] pd_k31_a; assign pd_k31_a = pd_a[34:31];
  logic [3:0] pd_k31_b; assign pd_k31_b = pd_b[34:31];
  logic pd_k31_cin; assign pd_k31_cin = pd_a[31] ^ pd_b[31] ^ f_mag[31];
  logic [3:0] pd_k31_s0;
  logic [3:0] pd_k31_s1;
  logic [3:0] pd_k31_s2;
  logic pd_k31_cout;
  logic pd_k31_cout2;
  // post-normalization compound CPA at rounding cut 31
  fam_prefix_kogge_stone_w4_flag_dual u68 (.a(pd_k31_a), .b(pd_k31_b), .cin(1'b0), .s(pd_k31_s0), .cout(pd_k31_cout), .s1(pd_k31_s1));
  // cut 31: candidate for simultaneous low carry and rounding increment
  fam_incr_prefix_and #(.W(4), .STRUCTURE(1), .B(4), .TOPO(0)) u69 (.a(pd_k31_s1), .cin(1'b1), .s(pd_k31_s2), .cout(pd_k31_cout2));
  logic [3:0] pd_k31_down; assign pd_k31_down = pd_k31_cin ? pd_k31_s1 : pd_k31_s0;
  logic [3:0] pd_k31_up; assign pd_k31_up = pd_k31_cin ? pd_k31_s2 : pd_k31_s1;
  logic pd_k31_guard; assign pd_k31_guard = f_mag[30];
  logic pd_k31_sticky; assign pd_k31_sticky = |f_mag[29:0];
  logic pd_k31_inexact; assign pd_k31_inexact = pd_k31_guard | pd_k31_sticky;
  logic pd_k31_increment; assign pd_k31_increment = (rnd == 3'd0) ? (pd_k31_guard && (pd_k31_sticky || pd_k31_down[0])) : (rnd == 3'd2) ? (pd_k31_inexact && f_s) : (rnd == 3'd3) ? (pd_k31_inexact && !f_s) : (rnd == 3'd5) ? pd_k31_inexact : 1'b0;
  logic [3:0] pd_k31_keep; assign pd_k31_keep = pd_k31_increment ? pd_k31_up : pd_k31_down;
  logic pd_k31_carry; assign pd_k31_carry = pd_k31_increment && (&pd_k31_down[3:0]);
  logic [25:0] pd_k31_sig; assign pd_k31_sig = pd_k31_carry ? (26'd1 << 25) : {pd_k31_keep[3:0], 22'd0};
  logic signed [18:0] pd_k31_ewide; assign pd_k31_ewide = pd_exp + (pd_k31_carry ? 19'sd1 : 19'sd0);
  logic signed [15:0] pd_k31_e; assign pd_k31_e = pd_k31_ewide[15:0];
  logic [1:0] pd_k31_special; assign pd_k31_special = pd_k31_inexact ? 2'd3 : 2'd0;
  logic [45:0] pd_k31_y; assign pd_k31_y = {pd_k31_special, f_s, pd_k31_e, pd_k31_sig, 1'b0};
  logic [3:0] pd_k32_a; assign pd_k32_a = pd_a[35:32];
  logic [3:0] pd_k32_b; assign pd_k32_b = pd_b[35:32];
  logic pd_k32_cin; assign pd_k32_cin = pd_a[32] ^ pd_b[32] ^ f_mag[32];
  logic [3:0] pd_k32_s0;
  logic [3:0] pd_k32_s1;
  logic [3:0] pd_k32_s2;
  logic pd_k32_cout;
  logic pd_k32_cout2;
  // post-normalization compound CPA at rounding cut 32
  fam_prefix_kogge_stone_w4_flag_dual u70 (.a(pd_k32_a), .b(pd_k32_b), .cin(1'b0), .s(pd_k32_s0), .cout(pd_k32_cout), .s1(pd_k32_s1));
  // cut 32: candidate for simultaneous low carry and rounding increment
  fam_incr_prefix_and #(.W(4), .STRUCTURE(1), .B(4), .TOPO(0)) u71 (.a(pd_k32_s1), .cin(1'b1), .s(pd_k32_s2), .cout(pd_k32_cout2));
  logic [3:0] pd_k32_down; assign pd_k32_down = pd_k32_cin ? pd_k32_s1 : pd_k32_s0;
  logic [3:0] pd_k32_up; assign pd_k32_up = pd_k32_cin ? pd_k32_s2 : pd_k32_s1;
  logic pd_k32_guard; assign pd_k32_guard = f_mag[31];
  logic pd_k32_sticky; assign pd_k32_sticky = |f_mag[30:0];
  logic pd_k32_inexact; assign pd_k32_inexact = pd_k32_guard | pd_k32_sticky;
  logic pd_k32_increment; assign pd_k32_increment = (rnd == 3'd0) ? (pd_k32_guard && (pd_k32_sticky || pd_k32_down[0])) : (rnd == 3'd2) ? (pd_k32_inexact && f_s) : (rnd == 3'd3) ? (pd_k32_inexact && !f_s) : (rnd == 3'd5) ? pd_k32_inexact : 1'b0;
  logic [3:0] pd_k32_keep; assign pd_k32_keep = pd_k32_increment ? pd_k32_up : pd_k32_down;
  logic pd_k32_carry; assign pd_k32_carry = pd_k32_increment && (&pd_k32_down[3:0]);
  logic [25:0] pd_k32_sig; assign pd_k32_sig = pd_k32_carry ? (26'd1 << 25) : {pd_k32_keep[3:0], 22'd0};
  logic signed [18:0] pd_k32_ewide; assign pd_k32_ewide = pd_exp + (pd_k32_carry ? 19'sd1 : 19'sd0);
  logic signed [15:0] pd_k32_e; assign pd_k32_e = pd_k32_ewide[15:0];
  logic [1:0] pd_k32_special; assign pd_k32_special = pd_k32_inexact ? 2'd3 : 2'd0;
  logic [45:0] pd_k32_y; assign pd_k32_y = {pd_k32_special, f_s, pd_k32_e, pd_k32_sig, 1'b0};
  logic [3:0] pd_k33_a; assign pd_k33_a = pd_a[36:33];
  logic [3:0] pd_k33_b; assign pd_k33_b = pd_b[36:33];
  logic pd_k33_cin; assign pd_k33_cin = pd_a[33] ^ pd_b[33] ^ f_mag[33];
  logic [3:0] pd_k33_s0;
  logic [3:0] pd_k33_s1;
  logic [3:0] pd_k33_s2;
  logic pd_k33_cout;
  logic pd_k33_cout2;
  // post-normalization compound CPA at rounding cut 33
  fam_prefix_kogge_stone_w4_flag_dual u72 (.a(pd_k33_a), .b(pd_k33_b), .cin(1'b0), .s(pd_k33_s0), .cout(pd_k33_cout), .s1(pd_k33_s1));
  // cut 33: candidate for simultaneous low carry and rounding increment
  fam_incr_prefix_and #(.W(4), .STRUCTURE(1), .B(4), .TOPO(0)) u73 (.a(pd_k33_s1), .cin(1'b1), .s(pd_k33_s2), .cout(pd_k33_cout2));
  logic [3:0] pd_k33_down; assign pd_k33_down = pd_k33_cin ? pd_k33_s1 : pd_k33_s0;
  logic [3:0] pd_k33_up; assign pd_k33_up = pd_k33_cin ? pd_k33_s2 : pd_k33_s1;
  logic pd_k33_guard; assign pd_k33_guard = f_mag[32];
  logic pd_k33_sticky; assign pd_k33_sticky = |f_mag[31:0];
  logic pd_k33_inexact; assign pd_k33_inexact = pd_k33_guard | pd_k33_sticky;
  logic pd_k33_increment; assign pd_k33_increment = (rnd == 3'd0) ? (pd_k33_guard && (pd_k33_sticky || pd_k33_down[0])) : (rnd == 3'd2) ? (pd_k33_inexact && f_s) : (rnd == 3'd3) ? (pd_k33_inexact && !f_s) : (rnd == 3'd5) ? pd_k33_inexact : 1'b0;
  logic [3:0] pd_k33_keep; assign pd_k33_keep = pd_k33_increment ? pd_k33_up : pd_k33_down;
  logic pd_k33_carry; assign pd_k33_carry = pd_k33_increment && (&pd_k33_down[3:0]);
  logic [25:0] pd_k33_sig; assign pd_k33_sig = pd_k33_carry ? (26'd1 << 25) : {pd_k33_keep[3:0], 22'd0};
  logic signed [18:0] pd_k33_ewide; assign pd_k33_ewide = pd_exp + (pd_k33_carry ? 19'sd1 : 19'sd0);
  logic signed [15:0] pd_k33_e; assign pd_k33_e = pd_k33_ewide[15:0];
  logic [1:0] pd_k33_special; assign pd_k33_special = pd_k33_inexact ? 2'd3 : 2'd0;
  logic [45:0] pd_k33_y; assign pd_k33_y = {pd_k33_special, f_s, pd_k33_e, pd_k33_sig, 1'b0};
  logic [3:0] pd_k34_a; assign pd_k34_a = pd_a[37:34];
  logic [3:0] pd_k34_b; assign pd_k34_b = pd_b[37:34];
  logic pd_k34_cin; assign pd_k34_cin = pd_a[34] ^ pd_b[34] ^ f_mag[34];
  logic [3:0] pd_k34_s0;
  logic [3:0] pd_k34_s1;
  logic [3:0] pd_k34_s2;
  logic pd_k34_cout;
  logic pd_k34_cout2;
  // post-normalization compound CPA at rounding cut 34
  fam_prefix_kogge_stone_w4_flag_dual u74 (.a(pd_k34_a), .b(pd_k34_b), .cin(1'b0), .s(pd_k34_s0), .cout(pd_k34_cout), .s1(pd_k34_s1));
  // cut 34: candidate for simultaneous low carry and rounding increment
  fam_incr_prefix_and #(.W(4), .STRUCTURE(1), .B(4), .TOPO(0)) u75 (.a(pd_k34_s1), .cin(1'b1), .s(pd_k34_s2), .cout(pd_k34_cout2));
  logic [3:0] pd_k34_down; assign pd_k34_down = pd_k34_cin ? pd_k34_s1 : pd_k34_s0;
  logic [3:0] pd_k34_up; assign pd_k34_up = pd_k34_cin ? pd_k34_s2 : pd_k34_s1;
  logic pd_k34_guard; assign pd_k34_guard = f_mag[33];
  logic pd_k34_sticky; assign pd_k34_sticky = |f_mag[32:0];
  logic pd_k34_inexact; assign pd_k34_inexact = pd_k34_guard | pd_k34_sticky;
  logic pd_k34_increment; assign pd_k34_increment = (rnd == 3'd0) ? (pd_k34_guard && (pd_k34_sticky || pd_k34_down[0])) : (rnd == 3'd2) ? (pd_k34_inexact && f_s) : (rnd == 3'd3) ? (pd_k34_inexact && !f_s) : (rnd == 3'd5) ? pd_k34_inexact : 1'b0;
  logic [3:0] pd_k34_keep; assign pd_k34_keep = pd_k34_increment ? pd_k34_up : pd_k34_down;
  logic pd_k34_carry; assign pd_k34_carry = pd_k34_increment && (&pd_k34_down[3:0]);
  logic [25:0] pd_k34_sig; assign pd_k34_sig = pd_k34_carry ? (26'd1 << 25) : {pd_k34_keep[3:0], 22'd0};
  logic signed [18:0] pd_k34_ewide; assign pd_k34_ewide = pd_exp + (pd_k34_carry ? 19'sd1 : 19'sd0);
  logic signed [15:0] pd_k34_e; assign pd_k34_e = pd_k34_ewide[15:0];
  logic [1:0] pd_k34_special; assign pd_k34_special = pd_k34_inexact ? 2'd3 : 2'd0;
  logic [45:0] pd_k34_y; assign pd_k34_y = {pd_k34_special, f_s, pd_k34_e, pd_k34_sig, 1'b0};
  logic [3:0] pd_k35_a; assign pd_k35_a = pd_a[38:35];
  logic [3:0] pd_k35_b; assign pd_k35_b = pd_b[38:35];
  logic pd_k35_cin; assign pd_k35_cin = pd_a[35] ^ pd_b[35] ^ f_mag[35];
  logic [3:0] pd_k35_s0;
  logic [3:0] pd_k35_s1;
  logic [3:0] pd_k35_s2;
  logic pd_k35_cout;
  logic pd_k35_cout2;
  // post-normalization compound CPA at rounding cut 35
  fam_prefix_kogge_stone_w4_flag_dual u76 (.a(pd_k35_a), .b(pd_k35_b), .cin(1'b0), .s(pd_k35_s0), .cout(pd_k35_cout), .s1(pd_k35_s1));
  // cut 35: candidate for simultaneous low carry and rounding increment
  fam_incr_prefix_and #(.W(4), .STRUCTURE(1), .B(4), .TOPO(0)) u77 (.a(pd_k35_s1), .cin(1'b1), .s(pd_k35_s2), .cout(pd_k35_cout2));
  logic [3:0] pd_k35_down; assign pd_k35_down = pd_k35_cin ? pd_k35_s1 : pd_k35_s0;
  logic [3:0] pd_k35_up; assign pd_k35_up = pd_k35_cin ? pd_k35_s2 : pd_k35_s1;
  logic pd_k35_guard; assign pd_k35_guard = f_mag[34];
  logic pd_k35_sticky; assign pd_k35_sticky = |f_mag[33:0];
  logic pd_k35_inexact; assign pd_k35_inexact = pd_k35_guard | pd_k35_sticky;
  logic pd_k35_increment; assign pd_k35_increment = (rnd == 3'd0) ? (pd_k35_guard && (pd_k35_sticky || pd_k35_down[0])) : (rnd == 3'd2) ? (pd_k35_inexact && f_s) : (rnd == 3'd3) ? (pd_k35_inexact && !f_s) : (rnd == 3'd5) ? pd_k35_inexact : 1'b0;
  logic [3:0] pd_k35_keep; assign pd_k35_keep = pd_k35_increment ? pd_k35_up : pd_k35_down;
  logic pd_k35_carry; assign pd_k35_carry = pd_k35_increment && (&pd_k35_down[3:0]);
  logic [25:0] pd_k35_sig; assign pd_k35_sig = pd_k35_carry ? (26'd1 << 25) : {pd_k35_keep[3:0], 22'd0};
  logic signed [18:0] pd_k35_ewide; assign pd_k35_ewide = pd_exp + (pd_k35_carry ? 19'sd1 : 19'sd0);
  logic signed [15:0] pd_k35_e; assign pd_k35_e = pd_k35_ewide[15:0];
  logic [1:0] pd_k35_special; assign pd_k35_special = pd_k35_inexact ? 2'd3 : 2'd0;
  logic [45:0] pd_k35_y; assign pd_k35_y = {pd_k35_special, f_s, pd_k35_e, pd_k35_sig, 1'b0};
  logic [3:0] pd_k36_a; assign pd_k36_a = pd_a[39:36];
  logic [3:0] pd_k36_b; assign pd_k36_b = pd_b[39:36];
  logic pd_k36_cin; assign pd_k36_cin = pd_a[36] ^ pd_b[36] ^ f_mag[36];
  logic [3:0] pd_k36_s0;
  logic [3:0] pd_k36_s1;
  logic [3:0] pd_k36_s2;
  logic pd_k36_cout;
  logic pd_k36_cout2;
  // post-normalization compound CPA at rounding cut 36
  fam_prefix_kogge_stone_w4_flag_dual u78 (.a(pd_k36_a), .b(pd_k36_b), .cin(1'b0), .s(pd_k36_s0), .cout(pd_k36_cout), .s1(pd_k36_s1));
  // cut 36: candidate for simultaneous low carry and rounding increment
  fam_incr_prefix_and #(.W(4), .STRUCTURE(1), .B(4), .TOPO(0)) u79 (.a(pd_k36_s1), .cin(1'b1), .s(pd_k36_s2), .cout(pd_k36_cout2));
  logic [3:0] pd_k36_down; assign pd_k36_down = pd_k36_cin ? pd_k36_s1 : pd_k36_s0;
  logic [3:0] pd_k36_up; assign pd_k36_up = pd_k36_cin ? pd_k36_s2 : pd_k36_s1;
  logic pd_k36_guard; assign pd_k36_guard = f_mag[35];
  logic pd_k36_sticky; assign pd_k36_sticky = |f_mag[34:0];
  logic pd_k36_inexact; assign pd_k36_inexact = pd_k36_guard | pd_k36_sticky;
  logic pd_k36_increment; assign pd_k36_increment = (rnd == 3'd0) ? (pd_k36_guard && (pd_k36_sticky || pd_k36_down[0])) : (rnd == 3'd2) ? (pd_k36_inexact && f_s) : (rnd == 3'd3) ? (pd_k36_inexact && !f_s) : (rnd == 3'd5) ? pd_k36_inexact : 1'b0;
  logic [3:0] pd_k36_keep; assign pd_k36_keep = pd_k36_increment ? pd_k36_up : pd_k36_down;
  logic pd_k36_carry; assign pd_k36_carry = pd_k36_increment && (&pd_k36_down[3:0]);
  logic [25:0] pd_k36_sig; assign pd_k36_sig = pd_k36_carry ? (26'd1 << 25) : {pd_k36_keep[3:0], 22'd0};
  logic signed [18:0] pd_k36_ewide; assign pd_k36_ewide = pd_exp + (pd_k36_carry ? 19'sd1 : 19'sd0);
  logic signed [15:0] pd_k36_e; assign pd_k36_e = pd_k36_ewide[15:0];
  logic [1:0] pd_k36_special; assign pd_k36_special = pd_k36_inexact ? 2'd3 : 2'd0;
  logic [45:0] pd_k36_y; assign pd_k36_y = {pd_k36_special, f_s, pd_k36_e, pd_k36_sig, 1'b0};
  logic [3:0] pd_k37_a; assign pd_k37_a = pd_a[40:37];
  logic [3:0] pd_k37_b; assign pd_k37_b = pd_b[40:37];
  logic pd_k37_cin; assign pd_k37_cin = pd_a[37] ^ pd_b[37] ^ f_mag[37];
  logic [3:0] pd_k37_s0;
  logic [3:0] pd_k37_s1;
  logic [3:0] pd_k37_s2;
  logic pd_k37_cout;
  logic pd_k37_cout2;
  // post-normalization compound CPA at rounding cut 37
  fam_prefix_kogge_stone_w4_flag_dual u80 (.a(pd_k37_a), .b(pd_k37_b), .cin(1'b0), .s(pd_k37_s0), .cout(pd_k37_cout), .s1(pd_k37_s1));
  // cut 37: candidate for simultaneous low carry and rounding increment
  fam_incr_prefix_and #(.W(4), .STRUCTURE(1), .B(4), .TOPO(0)) u81 (.a(pd_k37_s1), .cin(1'b1), .s(pd_k37_s2), .cout(pd_k37_cout2));
  logic [3:0] pd_k37_down; assign pd_k37_down = pd_k37_cin ? pd_k37_s1 : pd_k37_s0;
  logic [3:0] pd_k37_up; assign pd_k37_up = pd_k37_cin ? pd_k37_s2 : pd_k37_s1;
  logic pd_k37_guard; assign pd_k37_guard = f_mag[36];
  logic pd_k37_sticky; assign pd_k37_sticky = |f_mag[35:0];
  logic pd_k37_inexact; assign pd_k37_inexact = pd_k37_guard | pd_k37_sticky;
  logic pd_k37_increment; assign pd_k37_increment = (rnd == 3'd0) ? (pd_k37_guard && (pd_k37_sticky || pd_k37_down[0])) : (rnd == 3'd2) ? (pd_k37_inexact && f_s) : (rnd == 3'd3) ? (pd_k37_inexact && !f_s) : (rnd == 3'd5) ? pd_k37_inexact : 1'b0;
  logic [3:0] pd_k37_keep; assign pd_k37_keep = pd_k37_increment ? pd_k37_up : pd_k37_down;
  logic pd_k37_carry; assign pd_k37_carry = pd_k37_increment && (&pd_k37_down[3:0]);
  logic [25:0] pd_k37_sig; assign pd_k37_sig = pd_k37_carry ? (26'd1 << 25) : {pd_k37_keep[3:0], 22'd0};
  logic signed [18:0] pd_k37_ewide; assign pd_k37_ewide = pd_exp + (pd_k37_carry ? 19'sd1 : 19'sd0);
  logic signed [15:0] pd_k37_e; assign pd_k37_e = pd_k37_ewide[15:0];
  logic [1:0] pd_k37_special; assign pd_k37_special = pd_k37_inexact ? 2'd3 : 2'd0;
  logic [45:0] pd_k37_y; assign pd_k37_y = {pd_k37_special, f_s, pd_k37_e, pd_k37_sig, 1'b0};
  logic [3:0] pd_k38_a; assign pd_k38_a = pd_a[41:38];
  logic [3:0] pd_k38_b; assign pd_k38_b = pd_b[41:38];
  logic pd_k38_cin; assign pd_k38_cin = pd_a[38] ^ pd_b[38] ^ f_mag[38];
  logic [3:0] pd_k38_s0;
  logic [3:0] pd_k38_s1;
  logic [3:0] pd_k38_s2;
  logic pd_k38_cout;
  logic pd_k38_cout2;
  // post-normalization compound CPA at rounding cut 38
  fam_prefix_kogge_stone_w4_flag_dual u82 (.a(pd_k38_a), .b(pd_k38_b), .cin(1'b0), .s(pd_k38_s0), .cout(pd_k38_cout), .s1(pd_k38_s1));
  // cut 38: candidate for simultaneous low carry and rounding increment
  fam_incr_prefix_and #(.W(4), .STRUCTURE(1), .B(4), .TOPO(0)) u83 (.a(pd_k38_s1), .cin(1'b1), .s(pd_k38_s2), .cout(pd_k38_cout2));
  logic [3:0] pd_k38_down; assign pd_k38_down = pd_k38_cin ? pd_k38_s1 : pd_k38_s0;
  logic [3:0] pd_k38_up; assign pd_k38_up = pd_k38_cin ? pd_k38_s2 : pd_k38_s1;
  logic pd_k38_guard; assign pd_k38_guard = f_mag[37];
  logic pd_k38_sticky; assign pd_k38_sticky = |f_mag[36:0];
  logic pd_k38_inexact; assign pd_k38_inexact = pd_k38_guard | pd_k38_sticky;
  logic pd_k38_increment; assign pd_k38_increment = (rnd == 3'd0) ? (pd_k38_guard && (pd_k38_sticky || pd_k38_down[0])) : (rnd == 3'd2) ? (pd_k38_inexact && f_s) : (rnd == 3'd3) ? (pd_k38_inexact && !f_s) : (rnd == 3'd5) ? pd_k38_inexact : 1'b0;
  logic [3:0] pd_k38_keep; assign pd_k38_keep = pd_k38_increment ? pd_k38_up : pd_k38_down;
  logic pd_k38_carry; assign pd_k38_carry = pd_k38_increment && (&pd_k38_down[3:0]);
  logic [25:0] pd_k38_sig; assign pd_k38_sig = pd_k38_carry ? (26'd1 << 25) : {pd_k38_keep[3:0], 22'd0};
  logic signed [18:0] pd_k38_ewide; assign pd_k38_ewide = pd_exp + (pd_k38_carry ? 19'sd1 : 19'sd0);
  logic signed [15:0] pd_k38_e; assign pd_k38_e = pd_k38_ewide[15:0];
  logic [1:0] pd_k38_special; assign pd_k38_special = pd_k38_inexact ? 2'd3 : 2'd0;
  logic [45:0] pd_k38_y; assign pd_k38_y = {pd_k38_special, f_s, pd_k38_e, pd_k38_sig, 1'b0};
  logic [3:0] pd_k39_a; assign pd_k39_a = pd_a[42:39];
  logic [3:0] pd_k39_b; assign pd_k39_b = pd_b[42:39];
  logic pd_k39_cin; assign pd_k39_cin = pd_a[39] ^ pd_b[39] ^ f_mag[39];
  logic [3:0] pd_k39_s0;
  logic [3:0] pd_k39_s1;
  logic [3:0] pd_k39_s2;
  logic pd_k39_cout;
  logic pd_k39_cout2;
  // post-normalization compound CPA at rounding cut 39
  fam_prefix_kogge_stone_w4_flag_dual u84 (.a(pd_k39_a), .b(pd_k39_b), .cin(1'b0), .s(pd_k39_s0), .cout(pd_k39_cout), .s1(pd_k39_s1));
  // cut 39: candidate for simultaneous low carry and rounding increment
  fam_incr_prefix_and #(.W(4), .STRUCTURE(1), .B(4), .TOPO(0)) u85 (.a(pd_k39_s1), .cin(1'b1), .s(pd_k39_s2), .cout(pd_k39_cout2));
  logic [3:0] pd_k39_down; assign pd_k39_down = pd_k39_cin ? pd_k39_s1 : pd_k39_s0;
  logic [3:0] pd_k39_up; assign pd_k39_up = pd_k39_cin ? pd_k39_s2 : pd_k39_s1;
  logic pd_k39_guard; assign pd_k39_guard = f_mag[38];
  logic pd_k39_sticky; assign pd_k39_sticky = |f_mag[37:0];
  logic pd_k39_inexact; assign pd_k39_inexact = pd_k39_guard | pd_k39_sticky;
  logic pd_k39_increment; assign pd_k39_increment = (rnd == 3'd0) ? (pd_k39_guard && (pd_k39_sticky || pd_k39_down[0])) : (rnd == 3'd2) ? (pd_k39_inexact && f_s) : (rnd == 3'd3) ? (pd_k39_inexact && !f_s) : (rnd == 3'd5) ? pd_k39_inexact : 1'b0;
  logic [3:0] pd_k39_keep; assign pd_k39_keep = pd_k39_increment ? pd_k39_up : pd_k39_down;
  logic pd_k39_carry; assign pd_k39_carry = pd_k39_increment && (&pd_k39_down[3:0]);
  logic [25:0] pd_k39_sig; assign pd_k39_sig = pd_k39_carry ? (26'd1 << 25) : {pd_k39_keep[3:0], 22'd0};
  logic signed [18:0] pd_k39_ewide; assign pd_k39_ewide = pd_exp + (pd_k39_carry ? 19'sd1 : 19'sd0);
  logic signed [15:0] pd_k39_e; assign pd_k39_e = pd_k39_ewide[15:0];
  logic [1:0] pd_k39_special; assign pd_k39_special = pd_k39_inexact ? 2'd3 : 2'd0;
  logic [45:0] pd_k39_y; assign pd_k39_y = {pd_k39_special, f_s, pd_k39_e, pd_k39_sig, 1'b0};
  logic [3:0] pd_k40_a; assign pd_k40_a = pd_a[43:40];
  logic [3:0] pd_k40_b; assign pd_k40_b = pd_b[43:40];
  logic pd_k40_cin; assign pd_k40_cin = pd_a[40] ^ pd_b[40] ^ f_mag[40];
  logic [3:0] pd_k40_s0;
  logic [3:0] pd_k40_s1;
  logic [3:0] pd_k40_s2;
  logic pd_k40_cout;
  logic pd_k40_cout2;
  // post-normalization compound CPA at rounding cut 40
  fam_prefix_kogge_stone_w4_flag_dual u86 (.a(pd_k40_a), .b(pd_k40_b), .cin(1'b0), .s(pd_k40_s0), .cout(pd_k40_cout), .s1(pd_k40_s1));
  // cut 40: candidate for simultaneous low carry and rounding increment
  fam_incr_prefix_and #(.W(4), .STRUCTURE(1), .B(4), .TOPO(0)) u87 (.a(pd_k40_s1), .cin(1'b1), .s(pd_k40_s2), .cout(pd_k40_cout2));
  logic [3:0] pd_k40_down; assign pd_k40_down = pd_k40_cin ? pd_k40_s1 : pd_k40_s0;
  logic [3:0] pd_k40_up; assign pd_k40_up = pd_k40_cin ? pd_k40_s2 : pd_k40_s1;
  logic pd_k40_guard; assign pd_k40_guard = f_mag[39];
  logic pd_k40_sticky; assign pd_k40_sticky = |f_mag[38:0];
  logic pd_k40_inexact; assign pd_k40_inexact = pd_k40_guard | pd_k40_sticky;
  logic pd_k40_increment; assign pd_k40_increment = (rnd == 3'd0) ? (pd_k40_guard && (pd_k40_sticky || pd_k40_down[0])) : (rnd == 3'd2) ? (pd_k40_inexact && f_s) : (rnd == 3'd3) ? (pd_k40_inexact && !f_s) : (rnd == 3'd5) ? pd_k40_inexact : 1'b0;
  logic [3:0] pd_k40_keep; assign pd_k40_keep = pd_k40_increment ? pd_k40_up : pd_k40_down;
  logic pd_k40_carry; assign pd_k40_carry = pd_k40_increment && (&pd_k40_down[3:0]);
  logic [25:0] pd_k40_sig; assign pd_k40_sig = pd_k40_carry ? (26'd1 << 25) : {pd_k40_keep[3:0], 22'd0};
  logic signed [18:0] pd_k40_ewide; assign pd_k40_ewide = pd_exp + (pd_k40_carry ? 19'sd1 : 19'sd0);
  logic signed [15:0] pd_k40_e; assign pd_k40_e = pd_k40_ewide[15:0];
  logic [1:0] pd_k40_special; assign pd_k40_special = pd_k40_inexact ? 2'd3 : 2'd0;
  logic [45:0] pd_k40_y; assign pd_k40_y = {pd_k40_special, f_s, pd_k40_e, pd_k40_sig, 1'b0};
  logic pd_increment; assign pd_increment = (pd_cut == 7'd2) ? pd_k2_increment : (pd_cut == 7'd3) ? pd_k3_increment : (pd_cut == 7'd4) ? pd_k4_increment : (pd_cut == 7'd5) ? pd_k5_increment : (pd_cut == 7'd6) ? pd_k6_increment : (pd_cut == 7'd7) ? pd_k7_increment : (pd_cut == 7'd8) ? pd_k8_increment : (pd_cut == 7'd9) ? pd_k9_increment : (pd_cut == 7'd10) ? pd_k10_increment : (pd_cut == 7'd11) ? pd_k11_increment : (pd_cut == 7'd12) ? pd_k12_increment : (pd_cut == 7'd13) ? pd_k13_increment : (pd_cut == 7'd14) ? pd_k14_increment : (pd_cut == 7'd15) ? pd_k15_increment : (pd_cut == 7'd16) ? pd_k16_increment : (pd_cut == 7'd17) ? pd_k17_increment : (pd_cut == 7'd18) ? pd_k18_increment : (pd_cut == 7'd19) ? pd_k19_increment : (pd_cut == 7'd20) ? pd_k20_increment : (pd_cut == 7'd21) ? pd_k21_increment : (pd_cut == 7'd22) ? pd_k22_increment : (pd_cut == 7'd23) ? pd_k23_increment : (pd_cut == 7'd24) ? pd_k24_increment : (pd_cut == 7'd25) ? pd_k25_increment : (pd_cut == 7'd26) ? pd_k26_increment : (pd_cut == 7'd27) ? pd_k27_increment : (pd_cut == 7'd28) ? pd_k28_increment : (pd_cut == 7'd29) ? pd_k29_increment : (pd_cut == 7'd30) ? pd_k30_increment : (pd_cut == 7'd31) ? pd_k31_increment : (pd_cut == 7'd32) ? pd_k32_increment : (pd_cut == 7'd33) ? pd_k33_increment : (pd_cut == 7'd34) ? pd_k34_increment : (pd_cut == 7'd35) ? pd_k35_increment : (pd_cut == 7'd36) ? pd_k36_increment : (pd_cut == 7'd37) ? pd_k37_increment : (pd_cut == 7'd38) ? pd_k38_increment : (pd_cut == 7'd39) ? pd_k39_increment : (pd_cut == 7'd40) ? pd_k40_increment : 1'b0;
  logic pd_carry; assign pd_carry = (pd_cut == 7'd2) ? pd_k2_carry : (pd_cut == 7'd3) ? pd_k3_carry : (pd_cut == 7'd4) ? pd_k4_carry : (pd_cut == 7'd5) ? pd_k5_carry : (pd_cut == 7'd6) ? pd_k6_carry : (pd_cut == 7'd7) ? pd_k7_carry : (pd_cut == 7'd8) ? pd_k8_carry : (pd_cut == 7'd9) ? pd_k9_carry : (pd_cut == 7'd10) ? pd_k10_carry : (pd_cut == 7'd11) ? pd_k11_carry : (pd_cut == 7'd12) ? pd_k12_carry : (pd_cut == 7'd13) ? pd_k13_carry : (pd_cut == 7'd14) ? pd_k14_carry : (pd_cut == 7'd15) ? pd_k15_carry : (pd_cut == 7'd16) ? pd_k16_carry : (pd_cut == 7'd17) ? pd_k17_carry : (pd_cut == 7'd18) ? pd_k18_carry : (pd_cut == 7'd19) ? pd_k19_carry : (pd_cut == 7'd20) ? pd_k20_carry : (pd_cut == 7'd21) ? pd_k21_carry : (pd_cut == 7'd22) ? pd_k22_carry : (pd_cut == 7'd23) ? pd_k23_carry : (pd_cut == 7'd24) ? pd_k24_carry : (pd_cut == 7'd25) ? pd_k25_carry : (pd_cut == 7'd26) ? pd_k26_carry : (pd_cut == 7'd27) ? pd_k27_carry : (pd_cut == 7'd28) ? pd_k28_carry : (pd_cut == 7'd29) ? pd_k29_carry : (pd_cut == 7'd30) ? pd_k30_carry : (pd_cut == 7'd31) ? pd_k31_carry : (pd_cut == 7'd32) ? pd_k32_carry : (pd_cut == 7'd33) ? pd_k33_carry : (pd_cut == 7'd34) ? pd_k34_carry : (pd_cut == 7'd35) ? pd_k35_carry : (pd_cut == 7'd36) ? pd_k36_carry : (pd_cut == 7'd37) ? pd_k37_carry : (pd_cut == 7'd38) ? pd_k38_carry : (pd_cut == 7'd39) ? pd_k39_carry : (pd_cut == 7'd40) ? pd_k40_carry : 1'b0;
  logic pd_low_carry; assign pd_low_carry = (pd_cut == 7'd2) ? pd_k2_cin : (pd_cut == 7'd3) ? pd_k3_cin : (pd_cut == 7'd4) ? pd_k4_cin : (pd_cut == 7'd5) ? pd_k5_cin : (pd_cut == 7'd6) ? pd_k6_cin : (pd_cut == 7'd7) ? pd_k7_cin : (pd_cut == 7'd8) ? pd_k8_cin : (pd_cut == 7'd9) ? pd_k9_cin : (pd_cut == 7'd10) ? pd_k10_cin : (pd_cut == 7'd11) ? pd_k11_cin : (pd_cut == 7'd12) ? pd_k12_cin : (pd_cut == 7'd13) ? pd_k13_cin : (pd_cut == 7'd14) ? pd_k14_cin : (pd_cut == 7'd15) ? pd_k15_cin : (pd_cut == 7'd16) ? pd_k16_cin : (pd_cut == 7'd17) ? pd_k17_cin : (pd_cut == 7'd18) ? pd_k18_cin : (pd_cut == 7'd19) ? pd_k19_cin : (pd_cut == 7'd20) ? pd_k20_cin : (pd_cut == 7'd21) ? pd_k21_cin : (pd_cut == 7'd22) ? pd_k22_cin : (pd_cut == 7'd23) ? pd_k23_cin : (pd_cut == 7'd24) ? pd_k24_cin : (pd_cut == 7'd25) ? pd_k25_cin : (pd_cut == 7'd26) ? pd_k26_cin : (pd_cut == 7'd27) ? pd_k27_cin : (pd_cut == 7'd28) ? pd_k28_cin : (pd_cut == 7'd29) ? pd_k29_cin : (pd_cut == 7'd30) ? pd_k30_cin : (pd_cut == 7'd31) ? pd_k31_cin : (pd_cut == 7'd32) ? pd_k32_cin : (pd_cut == 7'd33) ? pd_k33_cin : (pd_cut == 7'd34) ? pd_k34_cin : (pd_cut == 7'd35) ? pd_k35_cin : (pd_cut == 7'd36) ? pd_k36_cin : (pd_cut == 7'd37) ? pd_k37_cin : (pd_cut == 7'd38) ? pd_k38_cin : (pd_cut == 7'd39) ? pd_k39_cin : (pd_cut == 7'd40) ? pd_k40_cin : 1'b0;
  logic [45:0] pd_candidate; assign pd_candidate = (pd_cut == 7'd2) ? pd_k2_y : (pd_cut == 7'd3) ? pd_k3_y : (pd_cut == 7'd4) ? pd_k4_y : (pd_cut == 7'd5) ? pd_k5_y : (pd_cut == 7'd6) ? pd_k6_y : (pd_cut == 7'd7) ? pd_k7_y : (pd_cut == 7'd8) ? pd_k8_y : (pd_cut == 7'd9) ? pd_k9_y : (pd_cut == 7'd10) ? pd_k10_y : (pd_cut == 7'd11) ? pd_k11_y : (pd_cut == 7'd12) ? pd_k12_y : (pd_cut == 7'd13) ? pd_k13_y : (pd_cut == 7'd14) ? pd_k14_y : (pd_cut == 7'd15) ? pd_k15_y : (pd_cut == 7'd16) ? pd_k16_y : (pd_cut == 7'd17) ? pd_k17_y : (pd_cut == 7'd18) ? pd_k18_y : (pd_cut == 7'd19) ? pd_k19_y : (pd_cut == 7'd20) ? pd_k20_y : (pd_cut == 7'd21) ? pd_k21_y : (pd_cut == 7'd22) ? pd_k22_y : (pd_cut == 7'd23) ? pd_k23_y : (pd_cut == 7'd24) ? pd_k24_y : (pd_cut == 7'd25) ? pd_k25_y : (pd_cut == 7'd26) ? pd_k26_y : (pd_cut == 7'd27) ? pd_k27_y : (pd_cut == 7'd28) ? pd_k28_y : (pd_cut == 7'd29) ? pd_k29_y : (pd_cut == 7'd30) ? pd_k30_y : (pd_cut == 7'd31) ? pd_k31_y : (pd_cut == 7'd32) ? pd_k32_y : (pd_cut == 7'd33) ? pd_k33_y : (pd_cut == 7'd34) ? pd_k34_y : (pd_cut == 7'd35) ? pd_k35_y : (pd_cut == 7'd36) ? pd_k36_y : (pd_cut == 7'd37) ? pd_k37_y : (pd_cut == 7'd38) ? pd_k38_y : (pd_cut == 7'd39) ? pd_k39_y : (pd_cut == 7'd40) ? pd_k40_y : y_fx;
  logic [45:0] y_pd; assign y_pd = pd_eligible ? pd_candidate : y_fx;
  assign y = y_pd;
endmodule

// fp fused multiply-add (multipath_fma): the mode's adder, its multiplier and the fused ops fmadd, fmsub, fnmsub, fnmadd through one datapath fam_fp_fma_core_multipath_fma_x26e16s11_p1221e7100196 under the op code fop (0 fadd, 1 fsub, 2 fmul, 3 fmadd, 4 fmsub, 5 fnmsub, 6 fnmadd): fadd is 1 * xa + xb, fmul is xa * xb + (a zero of the product's sign), a fused op negates xa for the negated product and xc for the negated addend; the window sum's negation by end_around_carry; the significand multiplier behavioral_star; the specials as the engine orders them for each op
module fam_fp_fma_multipath_fma_x26e16s11_pcac15181ef26 (
  input logic [45:0] xa,
  input logic [45:0] xb,
  input logic [45:0] xc,
  input logic [2:0] fop,
  output logic [45:0] y
);
  logic [1:0] a_sp; assign a_sp = xa[45:44];
  logic a_s; assign a_s = xa[43];
  logic signed [15:0] a_e; assign a_e = $signed(xa[42:27]);
  logic [25:0] a_sig; assign a_sig = xa[26:1];
  logic a_st; assign a_st = xa[0];
  logic a_z; assign a_z = (a_sp == 2'd0) && (a_sig == 0) && !a_st;
  logic [1:0] b_sp; assign b_sp = xb[45:44];
  logic b_s; assign b_s = xb[43];
  logic signed [15:0] b_e; assign b_e = $signed(xb[42:27]);
  logic [25:0] b_sig; assign b_sig = xb[26:1];
  logic b_st; assign b_st = xb[0];
  logic b_z; assign b_z = (b_sp == 2'd0) && (b_sig == 0) && !b_st;
  logic is_add; assign is_add = fop[2:1] == 2'b00;
  logic is_mul; assign is_mul = fop == 3'd2;
  logic neg_p; assign neg_p = (fop == 3'd5) || (fop == 3'd6);
  logic neg_c; assign neg_c = (fop == 3'd1) || (fop == 3'd4) || (fop == 3'd6);
  logic [45:0] xan; assign xan = {xa[45:44], xa[43] ^ neg_p, xa[42:0]};
  logic [45:0] addend; assign addend = is_add ? xb : xc;
  logic [45:0] xcn; assign xcn = {addend[45:44], addend[43] ^ neg_c, addend[42:0]};
  logic ps; assign ps = a_s ^ b_s;
  logic [45:0] fa; assign fa = is_add ? {2'd0, 1'b0, -16'sd10, 26'd1024, 1'b0} : xan;
  logic [45:0] fb; assign fb = is_add ? xa : xb;
  logic [45:0] fc; assign fc = is_mul ? {2'd0, ps, 16'sd0, 26'd0, 1'b0} : xcn;
  logic [45:0] yf;
  // the fused datapath: fc + fa * fb
  fam_fp_fma_core_multipath_fma_x26e16s11_p1221e7100196 u_fma (.xa(fa), .xb(fb), .xc(fc), .y(yf));
  logic [1:0] fa_sp; assign fa_sp = fa[45:44];
  logic fa_s; assign fa_s = fa[43];
  logic signed [15:0] fa_e; assign fa_e = $signed(fa[42:27]);
  logic [25:0] fa_sig; assign fa_sig = fa[26:1];
  logic fa_st; assign fa_st = fa[0];
  logic fa_z; assign fa_z = (fa_sp == 2'd0) && (fa_sig == 0) && !fa_st;
  logic [1:0] fb_sp; assign fb_sp = fb[45:44];
  logic fb_s; assign fb_s = fb[43];
  logic signed [15:0] fb_e; assign fb_e = $signed(fb[42:27]);
  logic [25:0] fb_sig; assign fb_sig = fb[26:1];
  logic fb_st; assign fb_st = fb[0];
  logic fb_z; assign fb_z = (fb_sp == 2'd0) && (fb_sig == 0) && !fb_st;
  logic [1:0] fc_sp; assign fc_sp = fc[45:44];
  logic fc_s; assign fc_s = fc[43];
  logic signed [15:0] fc_e; assign fc_e = $signed(fc[42:27]);
  logic [25:0] fc_sig; assign fc_sig = fc[26:1];
  logic fc_st; assign fc_st = fc[0];
  logic fc_z; assign fc_z = (fc_sp == 2'd0) && (fc_sig == 0) && !fc_st;
  logic p_nan; assign p_nan = (fa_sp == 2'd1) || (fb_sp == 2'd1);
  logic p_inf; assign p_inf = (fa_sp == 2'd2) || (fb_sp == 2'd2);
  logic p_inv; assign p_inv = p_inf && ((fa_sp == 2'd0 && fa_z) || (fb_sp == 2'd0 && fb_z));
  logic fps; assign fps = fa_s ^ fb_s;
  logic c_nan; assign c_nan = fc_sp == 2'd1;
  logic c_inf; assign c_inf = fc_sp == 2'd2;
  logic [45:0] y_sp; assign y_sp = (p_nan || c_nan || p_inv) ? {2'd1, 1'b0, 16'sd0, 26'd0, 1'b0} : (p_inf && c_inf && (fps != fc_s)) ? {2'd1, 1'b0, 16'sd0, 26'd0, 1'b0} : p_inf ? {2'd2, fps, 16'sd0, 26'd0, 1'b0} : c_inf ? {2'd2, fc_s, 16'sd0, 26'd0, 1'b0} : yf;
  assign y = y_sp;
endmodule

// fp fused multiply-add (reduced_latency_fma): the mode's adder, its multiplier and the fused ops fmadd, fmsub, fnmsub, fnmadd through one datapath fam_fp_fma_core_reduced_latency_fma_x26e16s11_fp8e4m3_pddacaa615be9 under the op code fop (0 fadd, 1 fsub, 2 fmul, 3 fmadd, 4 fmsub, 5 fnmsub, 6 fnmadd): fadd is 1 * xa + xb, fmul is xa * xb + (a zero of the product's sign), a fused op negates xa for the negated product and xc for the negated addend; the window sum's negation by end_around_carry; the rounding for fp8e4m3 fused into the window adder's compound sum (a normal result leaves rounded, with the ROUNDED code; a subnormal, an overflow and the stochastic mode leave unrounded); the significand multiplier behavioral_star; the specials as the engine orders them for each op
module fam_fp_fma_reduced_latency_fma_x26e16s11_pcb92892f976e (
  input logic [45:0] xa,
  input logic [45:0] xb,
  input logic [45:0] xc,
  input logic [2:0] fop,
  input logic [2:0] rnd,
  output logic [45:0] y
);
  logic [1:0] a_sp; assign a_sp = xa[45:44];
  logic a_s; assign a_s = xa[43];
  logic signed [15:0] a_e; assign a_e = $signed(xa[42:27]);
  logic [25:0] a_sig; assign a_sig = xa[26:1];
  logic a_st; assign a_st = xa[0];
  logic a_z; assign a_z = (a_sp == 2'd0) && (a_sig == 0) && !a_st;
  logic [1:0] b_sp; assign b_sp = xb[45:44];
  logic b_s; assign b_s = xb[43];
  logic signed [15:0] b_e; assign b_e = $signed(xb[42:27]);
  logic [25:0] b_sig; assign b_sig = xb[26:1];
  logic b_st; assign b_st = xb[0];
  logic b_z; assign b_z = (b_sp == 2'd0) && (b_sig == 0) && !b_st;
  logic is_add; assign is_add = fop[2:1] == 2'b00;
  logic is_mul; assign is_mul = fop == 3'd2;
  logic neg_p; assign neg_p = (fop == 3'd5) || (fop == 3'd6);
  logic neg_c; assign neg_c = (fop == 3'd1) || (fop == 3'd4) || (fop == 3'd6);
  logic [45:0] xan; assign xan = {xa[45:44], xa[43] ^ neg_p, xa[42:0]};
  logic [45:0] addend; assign addend = is_add ? xb : xc;
  logic [45:0] xcn; assign xcn = {addend[45:44], addend[43] ^ neg_c, addend[42:0]};
  logic ps; assign ps = a_s ^ b_s;
  logic [45:0] fa; assign fa = is_add ? {2'd0, 1'b0, -16'sd10, 26'd1024, 1'b0} : xan;
  logic [45:0] fb; assign fb = is_add ? xa : xb;
  logic [45:0] fc; assign fc = is_mul ? {2'd0, ps, 16'sd0, 26'd0, 1'b0} : xcn;
  logic [45:0] yf;
  // the fused datapath: fc + fa * fb
  fam_fp_fma_core_reduced_latency_fma_x26e16s11_fp8e4m3_pddacaa615be9 u_fma (.xa(fa), .xb(fb), .xc(fc), .rnd(rnd), .y(yf));
  logic [1:0] fa_sp; assign fa_sp = fa[45:44];
  logic fa_s; assign fa_s = fa[43];
  logic signed [15:0] fa_e; assign fa_e = $signed(fa[42:27]);
  logic [25:0] fa_sig; assign fa_sig = fa[26:1];
  logic fa_st; assign fa_st = fa[0];
  logic fa_z; assign fa_z = (fa_sp == 2'd0) && (fa_sig == 0) && !fa_st;
  logic [1:0] fb_sp; assign fb_sp = fb[45:44];
  logic fb_s; assign fb_s = fb[43];
  logic signed [15:0] fb_e; assign fb_e = $signed(fb[42:27]);
  logic [25:0] fb_sig; assign fb_sig = fb[26:1];
  logic fb_st; assign fb_st = fb[0];
  logic fb_z; assign fb_z = (fb_sp == 2'd0) && (fb_sig == 0) && !fb_st;
  logic [1:0] fc_sp; assign fc_sp = fc[45:44];
  logic fc_s; assign fc_s = fc[43];
  logic signed [15:0] fc_e; assign fc_e = $signed(fc[42:27]);
  logic [25:0] fc_sig; assign fc_sig = fc[26:1];
  logic fc_st; assign fc_st = fc[0];
  logic fc_z; assign fc_z = (fc_sp == 2'd0) && (fc_sig == 0) && !fc_st;
  logic p_nan; assign p_nan = (fa_sp == 2'd1) || (fb_sp == 2'd1);
  logic p_inf; assign p_inf = (fa_sp == 2'd2) || (fb_sp == 2'd2);
  logic p_inv; assign p_inv = p_inf && ((fa_sp == 2'd0 && fa_z) || (fb_sp == 2'd0 && fb_z));
  logic fps; assign fps = fa_s ^ fb_s;
  logic c_nan; assign c_nan = fc_sp == 2'd1;
  logic c_inf; assign c_inf = fc_sp == 2'd2;
  logic [45:0] y_sp; assign y_sp = (p_nan || c_nan || p_inv) ? {2'd1, 1'b0, 16'sd0, 26'd0, 1'b0} : (p_inf && c_inf && (fps != fc_s)) ? {2'd1, 1'b0, 16'sd0, 26'd0, 1'b0} : p_inf ? {2'd2, fps, 16'sd0, 26'd0, 1'b0} : c_inf ? {2'd2, fc_s, 16'sd0, 26'd0, 1'b0} : yf;
  assign y = y_sp;
endmodule

// fp rounder (dedicated_per_op, rounding increment_adder, leading zeros lzd_cell_tree, shifts barrel_mux_tree, exponent ripple_carry / prefix_and_incrementer): X -> bf16 pattern and flags
module fam_fp_round_dedicated_per_op_increment_adder_bf16_x26e16s11_pd77ccc5b5c45_nin (
  input logic [45:0] x,
  input logic [2:0] rnd,
  input logic [7:0] word,
  input logic ftz,
  output logic [9:0] fl,
  output logic [15:0] bits
);
  logic [1:0] x_sp; assign x_sp = x[45:44];
  logic x_s; assign x_s = x[43];
  logic signed [15:0] x_e; assign x_e = $signed(x[42:27]);
  logic [25:0] x_sig; assign x_sig = x[26:1];
  logic x_st; assign x_st = x[0];
  logic x_z; assign x_z = (x_sp == 2'd0) && (x_sig == 0) && !x_st;
  logic s; assign s = x_s & 1'd1;
  logic lone; assign lone = (x_sig == 0) && x_st;
  logic [25:0] sig; assign sig = lone ? (26'd1 << 25) : x_sig;
  logic signed [15:0] e_lone_c; assign e_lone_c = -16'sd51;
  logic signed [15:0] e_lone;
  // the exponent of a lone sticky's unit at the top
  fam_adder_ripple_carry #(.W(16), .CHUNK(1), .FORM(0)) u1 (.a(x_e), .b(e_lone_c), .cin(1'b0), .s(e_lone), .cout());
  logic signed [15:0] e; assign e = lone ? e_lone : x_e;
  logic normal; assign normal = e >= -16'sd151;
  logic signed [16:0] shc; assign shc = -17'sd133;
  logic signed [16:0] ex; assign ex = $signed({e[15], e});
  logic [16:0] shsub_nb; assign shsub_nb = ~(ex);
  logic signed [16:0] shsub;
  // the subnormal result's extra right shift
  fam_adder_ripple_carry #(.W(17), .CHUNK(1), .FORM(0)) u2 (.a(shc), .b(shsub_nb), .cin(1'b1), .s(shsub), .cout());
  logic signed [16:0] sht; assign sht = normal ? 17'sd18 : shsub;
  logic signed [16:0] sh; assign sh = (sht > 17'sd27) ? 17'sd27 : sht;
  logic [4:0] sha; assign sha = sh[4:0];
  logic [26:0] sigw; assign sigw = {1'b0, sig};
  logic [4:0] shk; assign shk = (sh > 17'sd26) ? 5'd26 : sha;
  logic [26:0] keep;
  // the right shift to the kept bits
  fam_shift_barrel_mux_tree #(.W(27), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u3 (.a(sigw), .amt(shk), .op(3'd1), .y(keep), .sticky());
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
  logic [26:0] keepn; assign keepn = sigw >> 18;
  logic [26:0] restn; assign restn = sigw & ({1'b0, {26{1'b1}}} >> 8);
  logic [26:0] halfn; assign halfn = {26'd0, 1'b1} << 17;
  logic inexact; assign inexact = (rest != 0) | x_st;
  logic [34:0] restw; assign restw = {rest, 8'd0};
  logic [5:0] fsh; assign fsh = sht[5:0];
  logic [34:0] fint0;
  // the dropped bits aligned to the stochastic word
  fam_shift_barrel_mux_tree #(.W(35), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u4 (.a(restw), .amt(fsh), .op(3'd1), .y(fint0), .sticky());
  logic [34:0] fint; assign fint = (sht > 17'sd34) ? 35'd0 : fint0;
  logic [34:0] fintn; assign fintn = restn >> 10;
  logic gt_half; assign gt_half = rest > halfv;
  logic half_eq; assign half_eq = (rest == halfv) && (halfv != 0);
  logic up; assign up = (rnd == 3'd0) ? (gt_half || (half_eq && (x_st || keep[0]))) : (rnd == 3'd1) ? 1'b0 : (rnd == 3'd2) ? (inexact && s) : (rnd == 3'd3) ? (inexact && !s) : (rnd == 3'd4) ? (inexact && (0 ? (fint >= word) : (fint > word))) : inexact;
  logic gt_halfn; assign gt_halfn = restn > halfn;
  logic half_eqn; assign half_eqn = (restn == halfn) && (halfn != 0);
  logic upn; assign upn = (rnd == 3'd0) ? (gt_halfn || (half_eqn && (x_st || keepn[0]))) : (rnd == 3'd1) ? 1'b0 : (rnd == 3'd2) ? (((restn != 0) | x_st) && s) : (rnd == 3'd3) ? (((restn != 0) | x_st) && !s) : (rnd == 3'd4) ? (((restn != 0) | x_st) && (0 ? (fintn >= word) : (fintn > word))) : ((restn != 0) | x_st);
  logic rounded; assign rounded = x_sp == 2'd3;
  logic upr; assign upr = rounded ? 1'b0 : up;
  logic inexact_r; assign inexact_r = rounded | inexact;
  logic carry_n; assign carry_n = upn && (&keepn[7:0]);
  logic [26:0] mag;
  logic [26:0] mag0;
  // the rounding increment (prefix_and_incrementer)
  fam_incr_prefix_and #(.W(27), .STRUCTURE(0), .B(4), .TOPO(0)) u5 (.a(keep), .cin(upr), .s(mag0), .cout());
  assign mag = mag0;
  logic signed [15:0] bfield_c; assign bfield_c = 16'sd152;
  logic signed [15:0] bfield;
  // the biased exponent field
  fam_adder_ripple_carry #(.W(16), .CHUNK(1), .FORM(0)) u6 (.a(e), .b(bfield_c), .cin(1'b0), .s(bfield), .cout());
  logic [15:0] bfu; assign bfu = bfield;
  logic [15:0] efield;
  // the exponent field incremented on a rounding carry (prefix_and_incrementer)
  fam_incr_prefix_and #(.W(16), .STRUCTURE(0), .B(4), .TOPO(0)) u7 (.a(bfu), .cin(mag[8]), .s(efield), .cout());
  logic [32:0] code; assign code = normal ? {{(33-16-7){1'b0}}, efield, mag[6:0]} : {{(33-27){1'b0}}, mag};
  logic tiny; assign tiny = (e < -16'sd151) && !(e == -16'sd152 && carry_n) && !(e == -16'sd152 && carry_n);
  logic ovf; assign ovf = code > 33'd32639;
  logic to_inf; assign to_inf = 1 && (rnd == 3'd0 || (rnd == 3'd3 && !s) || (rnd == 3'd2 && s) || rnd == 3'd5 || (rnd == 3'd4 && (e > 16'sd102 || up)));
  logic ftz_hit; assign ftz_hit = ftz && code[14:7] == 0 && (code[6:0] != 0);
  logic is_zero; assign is_zero = (x_sig == 0) && (!x_st || rounded);
  logic tiny_r; assign tiny_r = rounded ? x_st : tiny;
  logic [9:0] fl_fin; assign fl_fin = ovf ? ((1 << 2) | (1 << 4)) : ((inexact_r ? (1 << 4) : 0) | ((tiny_r && inexact_r) ? (1 << 3) : 0) | (ftz_hit ? ((1 << 4) | (1 << 3)) : 0));
  logic [15:0] bits_fin; assign bits_fin = ovf ? (to_inf ? {s, 15'd32640} : {s, 15'd32639}) : (ftz_hit ? {s, 15'd0} : {s, code[14:0]});
  logic [9:0] fl_zero; assign fl_zero = rounded ? ((1 << 4) | (1 << 3)) : 10'd0;
  assign fl = (x_sp == 2'd1) ? (1 << 5) : (x_sp == 2'd2) ? 0 : is_zero ? fl_zero : fl_fin;
  assign bits = (x_sp == 2'd1) ? 16'd32704 : (x_sp == 2'd2) ? {s, 15'd32640} : is_zero ? (rounded ? {s, 15'd0} : 16'd0) : bits_fin;
endmodule


// fp rounder (dedicated_per_op, rounding increment_adder, leading zeros lzd_cell_tree, shifts barrel_mux_tree, exponent ripple_carry / prefix_and_incrementer): X -> fp16 pattern and flags
module fam_fp_round_dedicated_per_op_increment_adder_fp16_x26e16s11_pd77ccc5b5c45_nin (
  input logic [45:0] x,
  input logic [2:0] rnd,
  input logic [7:0] word,
  input logic ftz,
  output logic [9:0] fl,
  output logic [15:0] bits
);
  logic [1:0] x_sp; assign x_sp = x[45:44];
  logic x_s; assign x_s = x[43];
  logic signed [15:0] x_e; assign x_e = $signed(x[42:27]);
  logic [25:0] x_sig; assign x_sig = x[26:1];
  logic x_st; assign x_st = x[0];
  logic x_z; assign x_z = (x_sp == 2'd0) && (x_sig == 0) && !x_st;
  logic s; assign s = x_s & 1'd1;
  logic lone; assign lone = (x_sig == 0) && x_st;
  logic [25:0] sig; assign sig = lone ? (26'd1 << 25) : x_sig;
  logic signed [15:0] e_lone_c; assign e_lone_c = -16'sd51;
  logic signed [15:0] e_lone;
  // the exponent of a lone sticky's unit at the top
  fam_adder_ripple_carry #(.W(16), .CHUNK(1), .FORM(0)) u1 (.a(x_e), .b(e_lone_c), .cin(1'b0), .s(e_lone), .cout());
  logic signed [15:0] e; assign e = lone ? e_lone : x_e;
  logic normal; assign normal = e >= -16'sd39;
  logic signed [16:0] shc; assign shc = -17'sd24;
  logic signed [16:0] ex; assign ex = $signed({e[15], e});
  logic [16:0] shsub_nb; assign shsub_nb = ~(ex);
  logic signed [16:0] shsub;
  // the subnormal result's extra right shift
  fam_adder_ripple_carry #(.W(17), .CHUNK(1), .FORM(0)) u2 (.a(shc), .b(shsub_nb), .cin(1'b1), .s(shsub), .cout());
  logic signed [16:0] sht; assign sht = normal ? 17'sd15 : shsub;
  logic signed [16:0] sh; assign sh = (sht > 17'sd27) ? 17'sd27 : sht;
  logic [4:0] sha; assign sha = sh[4:0];
  logic [26:0] sigw; assign sigw = {1'b0, sig};
  logic [4:0] shk; assign shk = (sh > 17'sd26) ? 5'd26 : sha;
  logic [26:0] keep;
  // the right shift to the kept bits
  fam_shift_barrel_mux_tree #(.W(27), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u3 (.a(sigw), .amt(shk), .op(3'd1), .y(keep), .sticky());
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
  fam_shift_barrel_mux_tree #(.W(35), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u4 (.a(restw), .amt(fsh), .op(3'd1), .y(fint0), .sticky());
  logic [34:0] fint; assign fint = (sht > 17'sd34) ? 35'd0 : fint0;
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
  fam_incr_prefix_and #(.W(27), .STRUCTURE(0), .B(4), .TOPO(0)) u5 (.a(keep), .cin(upr), .s(mag0), .cout());
  assign mag = mag0;
  logic signed [15:0] bfield_c; assign bfield_c = 16'sd40;
  logic signed [15:0] bfield;
  // the biased exponent field
  fam_adder_ripple_carry #(.W(16), .CHUNK(1), .FORM(0)) u6 (.a(e), .b(bfield_c), .cin(1'b0), .s(bfield), .cout());
  logic [15:0] bfu; assign bfu = bfield;
  logic [15:0] efield;
  // the exponent field incremented on a rounding carry (prefix_and_incrementer)
  fam_incr_prefix_and #(.W(16), .STRUCTURE(0), .B(4), .TOPO(0)) u7 (.a(bfu), .cin(mag[11]), .s(efield), .cout());
  logic [32:0] code; assign code = normal ? {{(33-16-10){1'b0}}, efield, mag[9:0]} : {{(33-27){1'b0}}, mag};
  logic tiny; assign tiny = (e < -16'sd39) && !(e == -16'sd40 && carry_n) && !(e == -16'sd40 && carry_n);
  logic ovf; assign ovf = code > 33'd31743;
  logic to_inf; assign to_inf = 1 && (rnd == 3'd0 || (rnd == 3'd3 && !s) || (rnd == 3'd2 && s) || rnd == 3'd5 || (rnd == 3'd4 && (e > -16'sd10 || up)));
  logic ftz_hit; assign ftz_hit = ftz && code[14:10] == 0 && (code[9:0] != 0);
  logic is_zero; assign is_zero = (x_sig == 0) && (!x_st || rounded);
  logic tiny_r; assign tiny_r = rounded ? x_st : tiny;
  logic [9:0] fl_fin; assign fl_fin = ovf ? ((1 << 2) | (1 << 4)) : ((inexact_r ? (1 << 4) : 0) | ((tiny_r && inexact_r) ? (1 << 3) : 0) | (ftz_hit ? ((1 << 4) | (1 << 3)) : 0));
  logic [15:0] bits_fin; assign bits_fin = ovf ? (to_inf ? {s, 15'd31744} : {s, 15'd31743}) : (ftz_hit ? {s, 15'd0} : {s, code[14:0]});
  logic [9:0] fl_zero; assign fl_zero = rounded ? ((1 << 4) | (1 << 3)) : 10'd0;
  assign fl = (x_sp == 2'd1) ? (1 << 5) : (x_sp == 2'd2) ? 0 : is_zero ? fl_zero : fl_fin;
  assign bits = (x_sp == 2'd1) ? 16'd32256 : (x_sp == 2'd2) ? {s, 15'd31744} : is_zero ? (rounded ? {s, 15'd0} : 16'd0) : bits_fin;
endmodule


// fp rounder (dedicated_per_op, rounding increment_adder, leading zeros lzd_cell_tree, shifts barrel_mux_tree, exponent ripple_carry / prefix_and_incrementer): X -> fp8e4m3 pattern and flags
module fam_fp_round_dedicated_per_op_increment_adder_fp8e4m3_x26e16s11_pd77ccc5b5c45_nin (
  input logic [45:0] x,
  input logic [2:0] rnd,
  input logic [7:0] word,
  input logic ftz,
  output logic [9:0] fl,
  output logic [7:0] bits
);
  logic [1:0] x_sp; assign x_sp = x[45:44];
  logic x_s; assign x_s = x[43];
  logic signed [15:0] x_e; assign x_e = $signed(x[42:27]);
  logic [25:0] x_sig; assign x_sig = x[26:1];
  logic x_st; assign x_st = x[0];
  logic x_z; assign x_z = (x_sp == 2'd0) && (x_sig == 0) && !x_st;
  logic s; assign s = x_s & 1'd1;
  logic lone; assign lone = (x_sig == 0) && x_st;
  logic [25:0] sig; assign sig = lone ? (26'd1 << 25) : x_sig;
  logic signed [15:0] e_lone_c; assign e_lone_c = -16'sd51;
  logic signed [15:0] e_lone;
  // the exponent of a lone sticky's unit at the top
  fam_adder_ripple_carry #(.W(16), .CHUNK(1), .FORM(0)) u1 (.a(x_e), .b(e_lone_c), .cin(1'b0), .s(e_lone), .cout());
  logic signed [15:0] e; assign e = lone ? e_lone : x_e;
  logic normal; assign normal = e >= -16'sd31;
  logic signed [16:0] shc; assign shc = -17'sd9;
  logic signed [16:0] ex; assign ex = $signed({e[15], e});
  logic [16:0] shsub_nb; assign shsub_nb = ~(ex);
  logic signed [16:0] shsub;
  // the subnormal result's extra right shift
  fam_adder_ripple_carry #(.W(17), .CHUNK(1), .FORM(0)) u2 (.a(shc), .b(shsub_nb), .cin(1'b1), .s(shsub), .cout());
  logic signed [16:0] sht; assign sht = normal ? 17'sd22 : shsub;
  logic signed [16:0] sh; assign sh = (sht > 17'sd27) ? 17'sd27 : sht;
  logic [4:0] sha; assign sha = sh[4:0];
  logic [26:0] sigw; assign sigw = {1'b0, sig};
  logic [4:0] shk; assign shk = (sh > 17'sd26) ? 5'd26 : sha;
  logic [26:0] keep;
  // the right shift to the kept bits
  fam_shift_barrel_mux_tree #(.W(27), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u3 (.a(sigw), .amt(shk), .op(3'd1), .y(keep), .sticky());
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
  logic [26:0] keepn; assign keepn = sigw >> 22;
  logic [26:0] restn; assign restn = sigw & ({1'b0, {26{1'b1}}} >> 4);
  logic [26:0] halfn; assign halfn = {26'd0, 1'b1} << 21;
  logic inexact; assign inexact = (rest != 0) | x_st;
  logic [34:0] restw; assign restw = {rest, 8'd0};
  logic [5:0] fsh; assign fsh = sht[5:0];
  logic [34:0] fint0;
  // the dropped bits aligned to the stochastic word
  fam_shift_barrel_mux_tree #(.W(35), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u4 (.a(restw), .amt(fsh), .op(3'd1), .y(fint0), .sticky());
  logic [34:0] fint; assign fint = (sht > 17'sd34) ? 35'd0 : fint0;
  logic [34:0] fintn; assign fintn = restn >> 14;
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
  logic [26:0] mag;
  logic [26:0] mag0;
  // the rounding increment (prefix_and_incrementer)
  fam_incr_prefix_and #(.W(27), .STRUCTURE(0), .B(4), .TOPO(0)) u5 (.a(keep), .cin(upr), .s(mag0), .cout());
  assign mag = mag0;
  logic signed [15:0] bfield_c; assign bfield_c = 16'sd32;
  logic signed [15:0] bfield;
  // the biased exponent field
  fam_adder_ripple_carry #(.W(16), .CHUNK(1), .FORM(0)) u6 (.a(e), .b(bfield_c), .cin(1'b0), .s(bfield), .cout());
  logic [15:0] bfu; assign bfu = bfield;
  logic [15:0] efield;
  // the exponent field incremented on a rounding carry (prefix_and_incrementer)
  fam_incr_prefix_and #(.W(16), .STRUCTURE(0), .B(4), .TOPO(0)) u7 (.a(bfu), .cin(mag[4]), .s(efield), .cout());
  logic [27:0] code; assign code = normal ? {{(28-16-3){1'b0}}, efield, mag[2:0]} : {{(28-27){1'b0}}, mag};
  logic tiny; assign tiny = (e < -16'sd31) && !(e == -16'sd32 && carry_n) && !(e == -16'sd32 && carry_n);
  logic ovf; assign ovf = code > 28'd126;
  logic to_inf; assign to_inf = 0 && (rnd == 3'd0 || (rnd == 3'd3 && !s) || (rnd == 3'd2 && s) || rnd == 3'd5 || (rnd == 3'd4 && (e > -16'sd17 || up)));
  logic ftz_hit; assign ftz_hit = ftz && code[6:3] == 0 && (code[2:0] != 0);
  logic is_zero; assign is_zero = (x_sig == 0) && (!x_st || rounded);
  logic tiny_r; assign tiny_r = rounded ? x_st : tiny;
  logic [9:0] fl_fin; assign fl_fin = ovf ? ((1 << 2) | (1 << 4)) : ((inexact_r ? (1 << 4) : 0) | ((tiny_r && inexact_r) ? (1 << 3) : 0) | (ftz_hit ? ((1 << 4) | (1 << 3)) : 0));
  logic [7:0] bits_fin; assign bits_fin = ovf ? (to_inf ? {s, 7'd126} : {s, 7'd126}) : (ftz_hit ? {s, 7'd0} : {s, code[6:0]});
  logic [9:0] fl_zero; assign fl_zero = rounded ? ((1 << 4) | (1 << 3)) : 10'd0;
  assign fl = (x_sp == 2'd1) ? (1 << 5) : (x_sp == 2'd2) ? ((1 << 4) | (1 << 2)) : is_zero ? fl_zero : fl_fin;
  assign bits = (x_sp == 2'd1) ? 8'd127 : (x_sp == 2'd2) ? {s, 7'd126} : is_zero ? (rounded ? {s, 7'd0} : 8'd0) : bits_fin;
endmodule


// fp rounder (dedicated_per_op, rounding increment_adder, leading zeros lzd_cell_tree, shifts barrel_mux_tree, exponent ripple_carry / prefix_and_incrementer): X -> fp8e5m2 pattern and flags
module fam_fp_round_dedicated_per_op_increment_adder_fp8e5m2_x26e16s11_pd77ccc5b5c45_nin (
  input logic [45:0] x,
  input logic [2:0] rnd,
  input logic [7:0] word,
  input logic ftz,
  output logic [9:0] fl,
  output logic [7:0] bits
);
  logic [1:0] x_sp; assign x_sp = x[45:44];
  logic x_s; assign x_s = x[43];
  logic signed [15:0] x_e; assign x_e = $signed(x[42:27]);
  logic [25:0] x_sig; assign x_sig = x[26:1];
  logic x_st; assign x_st = x[0];
  logic x_z; assign x_z = (x_sp == 2'd0) && (x_sig == 0) && !x_st;
  logic s; assign s = x_s & 1'd1;
  logic lone; assign lone = (x_sig == 0) && x_st;
  logic [25:0] sig; assign sig = lone ? (26'd1 << 25) : x_sig;
  logic signed [15:0] e_lone_c; assign e_lone_c = -16'sd51;
  logic signed [15:0] e_lone;
  // the exponent of a lone sticky's unit at the top
  fam_adder_ripple_carry #(.W(16), .CHUNK(1), .FORM(0)) u1 (.a(x_e), .b(e_lone_c), .cin(1'b0), .s(e_lone), .cout());
  logic signed [15:0] e; assign e = lone ? e_lone : x_e;
  logic normal; assign normal = e >= -16'sd39;
  logic signed [16:0] shc; assign shc = -17'sd16;
  logic signed [16:0] ex; assign ex = $signed({e[15], e});
  logic [16:0] shsub_nb; assign shsub_nb = ~(ex);
  logic signed [16:0] shsub;
  // the subnormal result's extra right shift
  fam_adder_ripple_carry #(.W(17), .CHUNK(1), .FORM(0)) u2 (.a(shc), .b(shsub_nb), .cin(1'b1), .s(shsub), .cout());
  logic signed [16:0] sht; assign sht = normal ? 17'sd23 : shsub;
  logic signed [16:0] sh; assign sh = (sht > 17'sd27) ? 17'sd27 : sht;
  logic [4:0] sha; assign sha = sh[4:0];
  logic [26:0] sigw; assign sigw = {1'b0, sig};
  logic [4:0] shk; assign shk = (sh > 17'sd26) ? 5'd26 : sha;
  logic [26:0] keep;
  // the right shift to the kept bits
  fam_shift_barrel_mux_tree #(.W(27), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u3 (.a(sigw), .amt(shk), .op(3'd1), .y(keep), .sticky());
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
  logic [26:0] keepn; assign keepn = sigw >> 23;
  logic [26:0] restn; assign restn = sigw & ({1'b0, {26{1'b1}}} >> 3);
  logic [26:0] halfn; assign halfn = {26'd0, 1'b1} << 22;
  logic inexact; assign inexact = (rest != 0) | x_st;
  logic [34:0] restw; assign restw = {rest, 8'd0};
  logic [5:0] fsh; assign fsh = sht[5:0];
  logic [34:0] fint0;
  // the dropped bits aligned to the stochastic word
  fam_shift_barrel_mux_tree #(.W(35), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u4 (.a(restw), .amt(fsh), .op(3'd1), .y(fint0), .sticky());
  logic [34:0] fint; assign fint = (sht > 17'sd34) ? 35'd0 : fint0;
  logic [34:0] fintn; assign fintn = restn >> 15;
  logic gt_half; assign gt_half = rest > halfv;
  logic half_eq; assign half_eq = (rest == halfv) && (halfv != 0);
  logic up; assign up = (rnd == 3'd0) ? (gt_half || (half_eq && (x_st || keep[0]))) : (rnd == 3'd1) ? 1'b0 : (rnd == 3'd2) ? (inexact && s) : (rnd == 3'd3) ? (inexact && !s) : (rnd == 3'd4) ? (inexact && (0 ? (fint >= word) : (fint > word))) : inexact;
  logic gt_halfn; assign gt_halfn = restn > halfn;
  logic half_eqn; assign half_eqn = (restn == halfn) && (halfn != 0);
  logic upn; assign upn = (rnd == 3'd0) ? (gt_halfn || (half_eqn && (x_st || keepn[0]))) : (rnd == 3'd1) ? 1'b0 : (rnd == 3'd2) ? (((restn != 0) | x_st) && s) : (rnd == 3'd3) ? (((restn != 0) | x_st) && !s) : (rnd == 3'd4) ? (((restn != 0) | x_st) && (0 ? (fintn >= word) : (fintn > word))) : ((restn != 0) | x_st);
  logic rounded; assign rounded = x_sp == 2'd3;
  logic upr; assign upr = rounded ? 1'b0 : up;
  logic inexact_r; assign inexact_r = rounded | inexact;
  logic carry_n; assign carry_n = upn && (&keepn[2:0]);
  logic [26:0] mag;
  logic [26:0] mag0;
  // the rounding increment (prefix_and_incrementer)
  fam_incr_prefix_and #(.W(27), .STRUCTURE(0), .B(4), .TOPO(0)) u5 (.a(keep), .cin(upr), .s(mag0), .cout());
  assign mag = mag0;
  logic signed [15:0] bfield_c; assign bfield_c = 16'sd40;
  logic signed [15:0] bfield;
  // the biased exponent field
  fam_adder_ripple_carry #(.W(16), .CHUNK(1), .FORM(0)) u6 (.a(e), .b(bfield_c), .cin(1'b0), .s(bfield), .cout());
  logic [15:0] bfu; assign bfu = bfield;
  logic [15:0] efield;
  // the exponent field incremented on a rounding carry (prefix_and_incrementer)
  fam_incr_prefix_and #(.W(16), .STRUCTURE(0), .B(4), .TOPO(0)) u7 (.a(bfu), .cin(mag[3]), .s(efield), .cout());
  logic [27:0] code; assign code = normal ? {{(28-16-2){1'b0}}, efield, mag[1:0]} : {{(28-27){1'b0}}, mag};
  logic tiny; assign tiny = (e < -16'sd39) && !(e == -16'sd40 && carry_n) && !(e == -16'sd40 && carry_n);
  logic ovf; assign ovf = code > 28'd123;
  logic to_inf; assign to_inf = 1 && (rnd == 3'd0 || (rnd == 3'd3 && !s) || (rnd == 3'd2 && s) || rnd == 3'd5 || (rnd == 3'd4 && (e > -16'sd10 || up)));
  logic ftz_hit; assign ftz_hit = ftz && code[6:2] == 0 && (code[1:0] != 0);
  logic is_zero; assign is_zero = (x_sig == 0) && (!x_st || rounded);
  logic tiny_r; assign tiny_r = rounded ? x_st : tiny;
  logic [9:0] fl_fin; assign fl_fin = ovf ? ((1 << 2) | (1 << 4)) : ((inexact_r ? (1 << 4) : 0) | ((tiny_r && inexact_r) ? (1 << 3) : 0) | (ftz_hit ? ((1 << 4) | (1 << 3)) : 0));
  logic [7:0] bits_fin; assign bits_fin = ovf ? (to_inf ? {s, 7'd124} : {s, 7'd123}) : (ftz_hit ? {s, 7'd0} : {s, code[6:0]});
  logic [9:0] fl_zero; assign fl_zero = rounded ? ((1 << 4) | (1 << 3)) : 10'd0;
  assign fl = (x_sp == 2'd1) ? (1 << 5) : (x_sp == 2'd2) ? 0 : is_zero ? fl_zero : fl_fin;
  assign bits = (x_sp == 2'd1) ? 8'd126 : (x_sp == 2'd2) ? {s, 7'd124} : is_zero ? (rounded ? {s, 7'd0} : 8'd0) : bits_fin;
endmodule


// fp unpacker (per_unit_unpack): bf16 pattern -> V; the fields split, the specials decoded, the hidden one restored, a subnormal normalized in the unpacker
module fam_fp_unpack_per_unit_unpack_bf16_x26e16s11_p9bfe39588414 (
  input logic [15:0] b,
  input logic daz,
  output logic [30:0] u
);
  logic [7:0] e; assign e = b[14:7];
  logic [6:0] mant; assign mant = b[6:0];
  logic s; assign s = b[15];
  logic nan; assign nan = (e == 8'd255 && mant != 0);
  logic inf; assign inf = (e == 8'd255 && mant == 0);
  logic sub_; assign sub_ = (e == 0);
  logic den; assign den = sub_ && (mant != 0);
  logic [10:0] sig0; assign sig0 = sub_ ? {{(11-7){1'b0}}, mant} : {{(11-7-1){1'b0}}, 1'b1, mant};
  logic [10:0] sig1; assign sig1 = (sub_ && daz) ? 11'd0 : sig0;
  logic signed [15:0] ex0; assign ex0 = sub_ ? -16'sd133 : $signed({{(16-8){1'b0}}, e}) - 16'sd134;
  logic [3:0] lz;
  // the subnormal's leading-zero count
  fam_count_lzd_pair_cell_binary_count_vflat_w11 u1 (.a(sig1), .n(lz));
  logic [3:0] lzs; assign lzs = (sig1 == 0) ? 4'd0 : lz[3:0];
  logic [10:0] sign;
  // the subnormal normalized
  fam_shift_barrel_mux_tree #(.W(11), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u2 (.a(sig1), .amt(lzs), .op(3'd0), .y(sign), .sticky());
  logic signed [15:0] exn; assign exn = ex0 - $signed({{(16-4){1'b0}}, lz});
  logic [29:0] v_nan; assign v_nan = {2'd1, 1'b0, 16'sd0, 11'd0};
  logic [29:0] v_inf; assign v_inf = {2'd2, s, 16'sd0, 11'd0};
  logic [29:0] v_fin; assign v_fin = {2'd0, s, exn, sign};
  assign u = nan ? {1'b0, v_nan} : inf ? {1'b0, v_inf} : {den, v_fin};
endmodule

// fp unpacker (per_unit_unpack): fp16 pattern -> V; the fields split, the specials decoded, the hidden one restored, a subnormal normalized in the unpacker
module fam_fp_unpack_per_unit_unpack_fp16_x26e16s11_p9bfe39588414 (
  input logic [15:0] b,
  input logic daz,
  output logic [30:0] u
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
  logic signed [15:0] ex0; assign ex0 = sub_ ? -16'sd24 : $signed({{(16-5){1'b0}}, e}) - 16'sd25;
  logic [3:0] lz;
  // the subnormal's leading-zero count
  fam_count_lzd_pair_cell_binary_count_vflat_w11 u1 (.a(sig1), .n(lz));
  logic [3:0] lzs; assign lzs = (sig1 == 0) ? 4'd0 : lz[3:0];
  logic [10:0] sign;
  // the subnormal normalized
  fam_shift_barrel_mux_tree #(.W(11), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u2 (.a(sig1), .amt(lzs), .op(3'd0), .y(sign), .sticky());
  logic signed [15:0] exn; assign exn = ex0 - $signed({{(16-4){1'b0}}, lz});
  logic [29:0] v_nan; assign v_nan = {2'd1, 1'b0, 16'sd0, 11'd0};
  logic [29:0] v_inf; assign v_inf = {2'd2, s, 16'sd0, 11'd0};
  logic [29:0] v_fin; assign v_fin = {2'd0, s, exn, sign};
  assign u = nan ? {1'b0, v_nan} : inf ? {1'b0, v_inf} : {den, v_fin};
endmodule

// fp unpacker (per_unit_unpack): fp8e4m3 pattern -> V; the fields split, the specials decoded, the hidden one restored, a subnormal normalized in the unpacker
module fam_fp_unpack_per_unit_unpack_fp8e4m3_x26e16s11_p9bfe39588414 (
  input logic [7:0] b,
  input logic daz,
  output logic [30:0] u
);
  logic [3:0] e; assign e = b[6:3];
  logic [2:0] mant; assign mant = b[2:0];
  logic s; assign s = b[7];
  logic nan; assign nan = (e == 4'd15 && mant == {3{1'b1}});
  logic inf; assign inf = 1'b0;
  logic sub_; assign sub_ = (e == 0);
  logic den; assign den = sub_ && (mant != 0);
  logic [10:0] sig0; assign sig0 = sub_ ? {{(11-3){1'b0}}, mant} : {{(11-3-1){1'b0}}, 1'b1, mant};
  logic [10:0] sig1; assign sig1 = (sub_ && daz) ? 11'd0 : sig0;
  logic signed [15:0] ex0; assign ex0 = sub_ ? -16'sd9 : $signed({{(16-4){1'b0}}, e}) - 16'sd10;
  logic [3:0] lz;
  // the subnormal's leading-zero count
  fam_count_lzd_pair_cell_binary_count_vflat_w11 u1 (.a(sig1), .n(lz));
  logic [3:0] lzs; assign lzs = (sig1 == 0) ? 4'd0 : lz[3:0];
  logic [10:0] sign;
  // the subnormal normalized
  fam_shift_barrel_mux_tree #(.W(11), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u2 (.a(sig1), .amt(lzs), .op(3'd0), .y(sign), .sticky());
  logic signed [15:0] exn; assign exn = ex0 - $signed({{(16-4){1'b0}}, lz});
  logic [29:0] v_nan; assign v_nan = {2'd1, 1'b0, 16'sd0, 11'd0};
  logic [29:0] v_inf; assign v_inf = {2'd2, s, 16'sd0, 11'd0};
  logic [29:0] v_fin; assign v_fin = {2'd0, s, exn, sign};
  assign u = nan ? {1'b0, v_nan} : inf ? {1'b0, v_inf} : {den, v_fin};
endmodule

// fp unpacker (per_unit_unpack): fp8e5m2 pattern -> V; the fields split, the specials decoded, the hidden one restored, a subnormal normalized in the unpacker
module fam_fp_unpack_per_unit_unpack_fp8e5m2_x26e16s11_p9bfe39588414 (
  input logic [7:0] b,
  input logic daz,
  output logic [30:0] u
);
  logic [4:0] e; assign e = b[6:2];
  logic [1:0] mant; assign mant = b[1:0];
  logic s; assign s = b[7];
  logic nan; assign nan = (e == 5'd31 && mant != 0);
  logic inf; assign inf = (e == 5'd31 && mant == 0);
  logic sub_; assign sub_ = (e == 0);
  logic den; assign den = sub_ && (mant != 0);
  logic [10:0] sig0; assign sig0 = sub_ ? {{(11-2){1'b0}}, mant} : {{(11-2-1){1'b0}}, 1'b1, mant};
  logic [10:0] sig1; assign sig1 = (sub_ && daz) ? 11'd0 : sig0;
  logic signed [15:0] ex0; assign ex0 = sub_ ? -16'sd16 : $signed({{(16-5){1'b0}}, e}) - 16'sd17;
  logic [3:0] lz;
  // the subnormal's leading-zero count
  fam_count_lzd_pair_cell_binary_count_vflat_w11 u1 (.a(sig1), .n(lz));
  logic [3:0] lzs; assign lzs = (sig1 == 0) ? 4'd0 : lz[3:0];
  logic [10:0] sign;
  // the subnormal normalized
  fam_shift_barrel_mux_tree #(.W(11), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u2 (.a(sig1), .amt(lzs), .op(3'd0), .y(sign), .sticky());
  logic signed [15:0] exn; assign exn = ex0 - $signed({{(16-4){1'b0}}, lz});
  logic [29:0] v_nan; assign v_nan = {2'd1, 1'b0, 16'sd0, 11'd0};
  logic [29:0] v_inf; assign v_inf = {2'd2, s, 16'sd0, 11'd0};
  logic [29:0] v_fin; assign v_fin = {2'd0, s, exn, sign};
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



// lzd_cell_tree (pair_cell, binary_count, valid flags flat): the leading zeros of a 44-bit word

module fam_prefix_kogge_stone_w4_flag_dual (input logic [3:0] a, input logic [3:0] b, input logic cin,
  output logic [3:0] s, output logic cout, output logic [3:0] s1);
  // prefix graph: {'n': 4, 'levels': 2, 'size': 5, 'fanout': 2, 'tracks': 2, 'exact_split': True, 'valency': 2}
  logic [3:0] gi, pi_, ti;
  assign gi = a & b;
  assign pi_ = a ^ b;
  assign ti = a | b;
  logic [3:0] g0, p0;
  assign g0 = {gi[3:1], gi[0] | (pi_[0] & cin)};
  assign p0 = pi_;
  logic G_0_1, P_0_1, G_1_2, P_1_2, G_2_3, P_2_3, G_0_2, P_0_2, G_0_3, P_0_3;
  assign G_0_1 = g0[1] | (p0[1] & g0[0]);
  assign P_0_1 = p0[1] & p0[0];
  assign G_1_2 = g0[2] | (p0[2] & g0[1]);
  assign P_1_2 = p0[2] & p0[1];
  assign G_2_3 = g0[3] | (p0[3] & g0[2]);
  assign P_2_3 = p0[3] & p0[2];
  assign G_0_2 = G_1_2 | (P_1_2 & g0[0]);
  assign P_0_2 = P_1_2 & p0[0];
  assign G_0_3 = G_2_3 | (P_2_3 & G_0_1);
  assign P_0_3 = P_2_3 & P_0_1;
  logic [4:0] c;
  assign c[0] = cin;
  assign c[1] = g0[0];
  assign c[2] = G_0_1;
  assign c[3] = G_0_2;
  assign c[4] = G_0_3;
  assign s = pi_ ^ c[3:0];
  assign cout = c[4];
  logic [3:0] g1, p1;
  assign g1 = {gi[3:1], gi[0] | pi_[0]};
  assign p1 = pi_;
  logic H_0_1, H_1_2, Q_1_2, H_2_3, Q_2_3, H_0_2, H_0_3;
  assign H_0_1 = g1[1] | (p1[1] & g1[0]);
  assign H_1_2 = g1[2] | (p1[2] & g1[1]);
  assign Q_1_2 = p1[2] & p1[1];
  assign H_2_3 = g1[3] | (p1[3] & g1[2]);
  assign Q_2_3 = p1[3] & p1[2];
  assign H_0_2 = H_1_2 | (Q_1_2 & g1[0]);
  assign H_0_3 = H_2_3 | (Q_2_3 & H_0_1);
  logic [4:0] c1;
  assign c1[0] = 1'b1;
  assign c1[1] = g1[0];
  assign c1[2] = H_0_1;
  assign c1[3] = H_0_2;
  assign c1[4] = H_0_3;
  assign s1 = pi_ ^ c1[3:0];
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
