// ADIR-MEMBER packages
// alu_core_m0_pkg: the exact-arithmetic functions of mode 0 (1xint16_twos_complement)
package alu_core_m0_pkg;

  // ---- m0: V = {special[1:0], sign, exp[8] (signed), sig[17]}
  //           X = {special[1:0], sign, exp[8] (signed), sig[38], sticky}
  localparam int m0_SW = 17, m0_EW = 8, m0_XW = 38;
  localparam int m0_VW = 28, m0_XT = 50;
  function automatic [27:0] m0_mkv(input [1:0] sp, input s, input signed [7:0] e, input [16:0] sig);
    m0_mkv = {sp, s, e, sig};
  endfunction
  function automatic [49:0] m0_mkx(input [1:0] sp, input s, input signed [7:0] e, input [37:0] sig, input st);
    m0_mkx = {sp, s, e, sig, st};
  endfunction
  function automatic [49:0] m0_x(input [27:0] v);   // widen V to X
    m0_x = {v[27:27-1], v[27-2], v[27-3 -: 8], {{(38-17){1'b0}}, v[16:0]}, 1'b0};
  endfunction
  // normalize: leading one at bit XW-1 (zero stays zero)
  function automatic [49:0] m0_norm(input [49:0] x);
    logic [37:0] s; logic signed [7:0] e; integer k;
    s = x[38:1]; e = x[38+8:38+1];
    if (s != 0) begin
      for (k = 32; k >= 1; k = k / 2) begin
        if (k < 38) begin
          if (s[37 -: 1] == 1'b0 && (s >> (38 - k)) == 0) begin
            s = s << k; e = e - k;
          end
        end
      end
    end
    m0_norm = {x[49:49-1], x[49-2], e, s, x[0]};
  endfunction

  function automatic m0_rup(input [2:0] rnd, input s, input inexact, input [38:0] rest, input [38:0] halfv,
                             input st, input lsb, input [38+8:0] fint, input [7:0] word);
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
  function automatic [49:0] m0_add(input [49:0] a, input [49:0] b, input sub);
    logic [49:0] na, nb, big, sml; logic [1:0] spa, spb; logic sa, sb, sr, sw;
    logic signed [7:0] ea, eb, d; logic [38:0] ms, mb, r; logic st, stb; integer sh;
    na = m0_norm(a); nb = m0_norm(b);
    spa = na[49:49-1]; spb = nb[49:49-1];
    sa = na[49-2]; sb = nb[49-2] ^ sub;
    if (spa == 2'd1 || spb == 2'd1) m0_add = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 && spb == 2'd2) m0_add = (sa == sb) ? m0_mkx(2'd2, sa, 0, 0, 1'b0) : m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m0_add = m0_mkx(2'd2, sa, 0, 0, 1'b0);
    else if (spb == 2'd2) m0_add = m0_mkx(2'd2, sb, 0, 0, 1'b0);
    else if (na[38:1] == 0 && !na[0]) m0_add = {nb[49:49-1], sb, nb[49-3:0]};
    else if (nb[38:1] == 0 && !nb[0]) m0_add = na;
    else begin
      ea = na[38+8:38+1]; eb = nb[38+8:38+1];
      // order by magnitude (both normalized): larger exponent, then sig
      if (ea > eb || (ea == eb && na[38:1] >= nb[38:1])) begin big = na; sml = nb; sw = 1'b0; end
      else begin big = nb; sml = na; sw = 1'b1; end
      d = big[38+8:38+1] - sml[38+8:38+1];
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
      if (r[38]) begin st = st | r[0]; r = r >> 1; m0_add = m0_mkx(2'd0, sr, big[38+8:38+1] + 1, r[37:0], st); end
      else m0_add = m0_mkx(2'd0, sr, big[38+8:38+1], r[37:0], st);
    end
  endfunction
  function automatic [49:0] m0_mul(input [49:0] a, input [49:0] b);
    logic [49:0] na, nb; logic [1:0] spa, spb; logic s; logic [2*38-1:0] pr; logic st; integer k;
    na = m0_norm(a); nb = m0_norm(b);
    spa = na[49:49-1]; spb = nb[49:49-1]; s = na[49-2] ^ nb[49-2];
    if (spa == 2'd1 || spb == 2'd1) m0_mul = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 || spb == 2'd2) begin
      if ((spa == 2'd0 && na[38:1] == 0 && !na[0]) || (spb == 2'd0 && nb[38:1] == 0 && !nb[0]))
        m0_mul = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
      else m0_mul = m0_mkx(2'd2, s, 0, 0, 1'b0);
    end else begin
      pr = na[38:1] * nb[38:1];
      st = na[0] | nb[0];
      // keep the top XW bits of the product, the rest folds into sticky
      st = st | (pr[37:0] != 0);
      m0_mul = m0_mkx(2'd0, s, na[38+8:38+1] + nb[38+8:38+1] + 38, pr[2*38-1:38], st);
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
  function automatic [2*38+1:0] m0_udiv(input [37:0] a, input [37:0] dv);
    logic [38+1:0] r; logic [38:0] q; logic ge; integer i;
    r = {2'b0, a}; q = 0;
    for (i = 38; i >= 0; i = i - 1) begin
      ge = (r >= {2'b0, dv});
      r = ge ? r - {2'b0, dv} : r;
      q = {q[37:0], ge};
      if (i > 0) r = {r[38:0], 1'b0};
    end
    m0_udiv = {q, r[38:0]};
  endfunction
  // the exact product: {special[1:0], sign, exp[EW], sig[2XW]} (no sticky)
  function automatic [2*38+8+2:0] m0_mulx(input [49:0] a, input [49:0] b);
    logic [49:0] na, nb; logic [1:0] spa, spb, sp; logic s; logic [2*38-1:0] pr;
    na = m0_norm(a); nb = m0_norm(b);
    pr = na[38:1] * nb[38:1];
    spa = na[49:49-1]; spb = nb[49:49-1]; s = na[49-2] ^ nb[49-2];
    if (spa == 2'd1 || spb == 2'd1) sp = 2'd1;
    else if (spa == 2'd2 || spb == 2'd2)
      sp = ((spa == 2'd0 && na[38:1] == 0) || (spb == 2'd0 && nb[38:1] == 0)) ? 2'd1 : 2'd2;
    else sp = 2'd0;
    m0_mulx = {sp, s, na[38+8:38+1] + nb[38+8:38+1], pr};
  endfunction
  function automatic [49:0] m0_div(input [49:0] a, input [49:0] b);
    logic [49:0] na, nb; logic [1:0] spa, spb; logic s; logic [2*38+1:0] qr; logic [38:0] q, r;
    na = m0_norm(a); nb = m0_norm(b);
    spa = na[49:49-1]; spb = nb[49:49-1]; s = na[49-2] ^ nb[49-2];
    if (spa == 2'd1 || spb == 2'd1) m0_div = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 && spb == 2'd2) m0_div = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m0_div = m0_mkx(2'd2, s, 0, 0, 1'b0);
    else if (spb == 2'd2) m0_div = m0_mkx(2'd0, s, 0, 0, 1'b0);
    else if (nb[38:1] == 0 && !nb[0]) begin
      if (na[38:1] == 0 && !na[0]) m0_div = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
      else m0_div = m0_mkx(2'd2, s, 0, 0, 1'b0);
    end else if (na[38:1] == 0 && !na[0]) m0_div = m0_mkx(2'd0, s, 0, 0, 1'b0);
    else begin
      qr = m0_udiv(na[38:1], nb[38:1]);     // both normalized: nonzero finite
      q = qr[2*38+1:38+1]; r = qr[38:0];
      // q < 2^(XW+1): drop one bit when it carries
      if (q[38]) m0_div = m0_mkx(2'd0, s, na[38+8:38+1] - nb[38+8:38+1] - 38 + 1, q[38:1], (r != 0) | q[0] | na[0] | nb[0]);
      else m0_div = m0_mkx(2'd0, s, na[38+8:38+1] - nb[38+8:38+1] - 38, q[37:0], (r != 0) | na[0] | nb[0]);
    end
  endfunction
  function automatic [49:0] m0_sqrt(input [49:0] a);
    logic [49:0] na; logic [1:0] spa; logic signed [7:0] e; logic [38:0] m; logic [2*38+3:0] rad;
    logic [38+2:0] rem, trial; logic [38:0] root; logic ge; integer i;
    na = m0_norm(a); spa = na[49:49-1];
    if (spa == 2'd1) m0_sqrt = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m0_sqrt = na[49-2] ? m0_mkx(2'd1, 1'b0, 0, 0, 1'b0) : na;
    else if (na[38:1] == 0 && !na[0]) m0_sqrt = na;
    else if (na[49-2]) m0_sqrt = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else begin
      e = na[38+8:38+1];
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
      m0_sqrt = m0_mkx(2'd0, 1'b0, (e >>> 1) - 19 + 1, root[38:1], (rem != 0) | root[0] | na[0]);
    end
  endfunction
  // X ordering treats NaN as unordered and compares finite values by sign and magnitude
  function automatic m0_lt(input [49:0] a, input [49:0] b);
    logic [49:0] na, nb; logic za, zb, sa, sb, mag_lt; logic signed [7:0] ea, eb;
    na = m0_norm(a); nb = m0_norm(b);
    za = (na[38:1] == 0) && !na[0]; zb = (nb[38:1] == 0) && !nb[0];
    sa = na[49-2] && !za; sb = nb[49-2] && !zb;
    if (na[49:49-1] == 2'd1 || nb[49:49-1] == 2'd1) m0_lt = 1'b0;
    else if (na[49:49-1] == 2'd2 || nb[49:49-1] == 2'd2) begin
      if (na[49:49-1] == 2'd2 && nb[49:49-1] == 2'd2) m0_lt = na[49-2] && !nb[49-2];
      else if (na[49:49-1] == 2'd2) m0_lt = na[49-2];
      else m0_lt = !nb[49-2];
    end else if (za && zb) m0_lt = 1'b0;
    else if (sa != sb) m0_lt = sa;
    else begin
      ea = na[38+8:38+1]; eb = nb[38+8:38+1];
      if (za) mag_lt = 1'b1; else if (zb) mag_lt = 1'b0;
      else mag_lt = (ea < eb) || (ea == eb && (na[38:1] < nb[38:1] || (na[38:1] == nb[38:1] && !na[0] && nb[0])));
      m0_lt = sa ? !mag_lt && !(za && zb) && !m0_eq(na, nb) : mag_lt;
    end
  endfunction
  function automatic m0_eq(input [49:0] a, input [49:0] b);
    logic [49:0] na, nb; logic za, zb;
    na = m0_norm(a); nb = m0_norm(b);
    za = (na[38:1] == 0) && !na[0]; zb = (nb[38:1] == 0) && !nb[0];
    if (na[49:49-1] == 2'd1 || nb[49:49-1] == 2'd1) m0_eq = 1'b0;
    else if (na[49:49-1] == 2'd2 || nb[49:49-1] == 2'd2)
      m0_eq = (na[49:49-1] == nb[49:49-1]) && (na[49-2] == nb[49-2]);
    else if (za || zb) m0_eq = za && zb;
    else m0_eq = (na[49-2] == nb[49-2]) && (na[38+8:38+1] == nb[38+8:38+1]) && (na[38:1] == nb[38:1]) && (na[0] == nb[0]);
  endfunction

  function automatic [28:0] m0_unpack_s(input [15:0] b, input daz);
    logic s; logic [15:0] mag; integer i;
    s = b[15]; mag = s ? (~b + 1'b1) : b;
    m0_unpack_s = {1'b0, m0_mkv(2'd0, s && (mag != 0), -0, {{(17-16){1'b0}}, mag})};
  endfunction

  function automatic [15:0] m0_enc(input signed [34:0] v); m0_enc = v[15:0]; endfunction
  function automatic [15:0] m0_wrap(input signed [34:0] v); m0_wrap = v[15:0]; endfunction
  function automatic [15:0] m0_sat(input signed [34:0] v);
    m0_sat = (v > 35'sd32767) ? {1'b0, {15{1'b1}}} : (v < -35'sd32768) ? {1'b1, {15{1'b0}}} : v[15:0];
  endfunction

  // round v / 2^f under rnd (the SR word applies to the fraction bits)
  function automatic signed [34:0] m0_rshift(input signed [34:0] v, input integer f, input [2:0] rnd, input [7:0] word);
    logic s; logic [34:0] mag, keep, rest, halfv; logic [43:0] fint; logic up, inexact;
    s = v < 0; mag = s ? -v : v;
    if (f <= 0) m0_rshift = v;
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
      m0_rshift = s ? -$signed(keep) : $signed(keep);
    end
  endfunction
  // the SR word of a division: floor(|r| * 2^sb / |b|)
  function automatic [7:0] m0_divfrac(input [34:0] r, input [34:0] b);
    logic [43:0] t;
    t = ({{9{1'b0}}, r} << 8) / {{9{1'b0}}, b};
    m0_divfrac = t[7:0];
  endfunction
endpackage

// alu_core_m1_pkg: the exact-arithmetic functions of mode 1 (2xint8_twos_complement)
package alu_core_m1_pkg;

  // ---- m1: V = {special[1:0], sign, exp[8] (signed), sig[9]}
  //           X = {special[1:0], sign, exp[8] (signed), sig[22], sticky}
  localparam int m1_SW = 9, m1_EW = 8, m1_XW = 22;
  localparam int m1_VW = 20, m1_XT = 34;
  function automatic [19:0] m1_mkv(input [1:0] sp, input s, input signed [7:0] e, input [8:0] sig);
    m1_mkv = {sp, s, e, sig};
  endfunction
  function automatic [33:0] m1_mkx(input [1:0] sp, input s, input signed [7:0] e, input [21:0] sig, input st);
    m1_mkx = {sp, s, e, sig, st};
  endfunction
  function automatic [33:0] m1_x(input [19:0] v);   // widen V to X
    m1_x = {v[19:19-1], v[19-2], v[19-3 -: 8], {{(22-9){1'b0}}, v[8:0]}, 1'b0};
  endfunction
  // normalize: leading one at bit XW-1 (zero stays zero)
  function automatic [33:0] m1_norm(input [33:0] x);
    logic [21:0] s; logic signed [7:0] e; integer k;
    s = x[22:1]; e = x[22+8:22+1];
    if (s != 0) begin
      for (k = 16; k >= 1; k = k / 2) begin
        if (k < 22) begin
          if (s[21 -: 1] == 1'b0 && (s >> (22 - k)) == 0) begin
            s = s << k; e = e - k;
          end
        end
      end
    end
    m1_norm = {x[33:33-1], x[33-2], e, s, x[0]};
  endfunction

  function automatic m1_rup(input [2:0] rnd, input s, input inexact, input [22:0] rest, input [22:0] halfv,
                             input st, input lsb, input [22+8:0] fint, input [7:0] word);
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
  function automatic [33:0] m1_add(input [33:0] a, input [33:0] b, input sub);
    logic [33:0] na, nb, big, sml; logic [1:0] spa, spb; logic sa, sb, sr, sw;
    logic signed [7:0] ea, eb, d; logic [22:0] ms, mb, r; logic st, stb; integer sh;
    na = m1_norm(a); nb = m1_norm(b);
    spa = na[33:33-1]; spb = nb[33:33-1];
    sa = na[33-2]; sb = nb[33-2] ^ sub;
    if (spa == 2'd1 || spb == 2'd1) m1_add = m1_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 && spb == 2'd2) m1_add = (sa == sb) ? m1_mkx(2'd2, sa, 0, 0, 1'b0) : m1_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m1_add = m1_mkx(2'd2, sa, 0, 0, 1'b0);
    else if (spb == 2'd2) m1_add = m1_mkx(2'd2, sb, 0, 0, 1'b0);
    else if (na[22:1] == 0 && !na[0]) m1_add = {nb[33:33-1], sb, nb[33-3:0]};
    else if (nb[22:1] == 0 && !nb[0]) m1_add = na;
    else begin
      ea = na[22+8:22+1]; eb = nb[22+8:22+1];
      // order by magnitude (both normalized): larger exponent, then sig
      if (ea > eb || (ea == eb && na[22:1] >= nb[22:1])) begin big = na; sml = nb; sw = 1'b0; end
      else begin big = nb; sml = na; sw = 1'b1; end
      d = big[22+8:22+1] - sml[22+8:22+1];
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
      if (r[22]) begin st = st | r[0]; r = r >> 1; m1_add = m1_mkx(2'd0, sr, big[22+8:22+1] + 1, r[21:0], st); end
      else m1_add = m1_mkx(2'd0, sr, big[22+8:22+1], r[21:0], st);
    end
  endfunction
  function automatic [33:0] m1_mul(input [33:0] a, input [33:0] b);
    logic [33:0] na, nb; logic [1:0] spa, spb; logic s; logic [2*22-1:0] pr; logic st; integer k;
    na = m1_norm(a); nb = m1_norm(b);
    spa = na[33:33-1]; spb = nb[33:33-1]; s = na[33-2] ^ nb[33-2];
    if (spa == 2'd1 || spb == 2'd1) m1_mul = m1_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 || spb == 2'd2) begin
      if ((spa == 2'd0 && na[22:1] == 0 && !na[0]) || (spb == 2'd0 && nb[22:1] == 0 && !nb[0]))
        m1_mul = m1_mkx(2'd1, 1'b0, 0, 0, 1'b0);
      else m1_mul = m1_mkx(2'd2, s, 0, 0, 1'b0);
    end else begin
      pr = na[22:1] * nb[22:1];
      st = na[0] | nb[0];
      // keep the top XW bits of the product, the rest folds into sticky
      st = st | (pr[21:0] != 0);
      m1_mul = m1_mkx(2'd0, s, na[22+8:22+1] + nb[22+8:22+1] + 22, pr[2*22-1:22], st);
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
  function automatic [2*22+1:0] m1_udiv(input [21:0] a, input [21:0] dv);
    logic [22+1:0] r; logic [22:0] q; logic ge; integer i;
    r = {2'b0, a}; q = 0;
    for (i = 22; i >= 0; i = i - 1) begin
      ge = (r >= {2'b0, dv});
      r = ge ? r - {2'b0, dv} : r;
      q = {q[21:0], ge};
      if (i > 0) r = {r[22:0], 1'b0};
    end
    m1_udiv = {q, r[22:0]};
  endfunction
  // the exact product: {special[1:0], sign, exp[EW], sig[2XW]} (no sticky)
  function automatic [2*22+8+2:0] m1_mulx(input [33:0] a, input [33:0] b);
    logic [33:0] na, nb; logic [1:0] spa, spb, sp; logic s; logic [2*22-1:0] pr;
    na = m1_norm(a); nb = m1_norm(b);
    pr = na[22:1] * nb[22:1];
    spa = na[33:33-1]; spb = nb[33:33-1]; s = na[33-2] ^ nb[33-2];
    if (spa == 2'd1 || spb == 2'd1) sp = 2'd1;
    else if (spa == 2'd2 || spb == 2'd2)
      sp = ((spa == 2'd0 && na[22:1] == 0) || (spb == 2'd0 && nb[22:1] == 0)) ? 2'd1 : 2'd2;
    else sp = 2'd0;
    m1_mulx = {sp, s, na[22+8:22+1] + nb[22+8:22+1], pr};
  endfunction
  function automatic [33:0] m1_div(input [33:0] a, input [33:0] b);
    logic [33:0] na, nb; logic [1:0] spa, spb; logic s; logic [2*22+1:0] qr; logic [22:0] q, r;
    na = m1_norm(a); nb = m1_norm(b);
    spa = na[33:33-1]; spb = nb[33:33-1]; s = na[33-2] ^ nb[33-2];
    if (spa == 2'd1 || spb == 2'd1) m1_div = m1_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 && spb == 2'd2) m1_div = m1_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m1_div = m1_mkx(2'd2, s, 0, 0, 1'b0);
    else if (spb == 2'd2) m1_div = m1_mkx(2'd0, s, 0, 0, 1'b0);
    else if (nb[22:1] == 0 && !nb[0]) begin
      if (na[22:1] == 0 && !na[0]) m1_div = m1_mkx(2'd1, 1'b0, 0, 0, 1'b0);
      else m1_div = m1_mkx(2'd2, s, 0, 0, 1'b0);
    end else if (na[22:1] == 0 && !na[0]) m1_div = m1_mkx(2'd0, s, 0, 0, 1'b0);
    else begin
      qr = m1_udiv(na[22:1], nb[22:1]);     // both normalized: nonzero finite
      q = qr[2*22+1:22+1]; r = qr[22:0];
      // q < 2^(XW+1): drop one bit when it carries
      if (q[22]) m1_div = m1_mkx(2'd0, s, na[22+8:22+1] - nb[22+8:22+1] - 22 + 1, q[22:1], (r != 0) | q[0] | na[0] | nb[0]);
      else m1_div = m1_mkx(2'd0, s, na[22+8:22+1] - nb[22+8:22+1] - 22, q[21:0], (r != 0) | na[0] | nb[0]);
    end
  endfunction
  function automatic [33:0] m1_sqrt(input [33:0] a);
    logic [33:0] na; logic [1:0] spa; logic signed [7:0] e; logic [22:0] m; logic [2*22+3:0] rad;
    logic [22+2:0] rem, trial; logic [22:0] root; logic ge; integer i;
    na = m1_norm(a); spa = na[33:33-1];
    if (spa == 2'd1) m1_sqrt = m1_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m1_sqrt = na[33-2] ? m1_mkx(2'd1, 1'b0, 0, 0, 1'b0) : na;
    else if (na[22:1] == 0 && !na[0]) m1_sqrt = na;
    else if (na[33-2]) m1_sqrt = m1_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else begin
      e = na[22+8:22+1];
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
      m1_sqrt = m1_mkx(2'd0, 1'b0, (e >>> 1) - 11 + 1, root[22:1], (rem != 0) | root[0] | na[0]);
    end
  endfunction
  // X ordering treats NaN as unordered and compares finite values by sign and magnitude
  function automatic m1_lt(input [33:0] a, input [33:0] b);
    logic [33:0] na, nb; logic za, zb, sa, sb, mag_lt; logic signed [7:0] ea, eb;
    na = m1_norm(a); nb = m1_norm(b);
    za = (na[22:1] == 0) && !na[0]; zb = (nb[22:1] == 0) && !nb[0];
    sa = na[33-2] && !za; sb = nb[33-2] && !zb;
    if (na[33:33-1] == 2'd1 || nb[33:33-1] == 2'd1) m1_lt = 1'b0;
    else if (na[33:33-1] == 2'd2 || nb[33:33-1] == 2'd2) begin
      if (na[33:33-1] == 2'd2 && nb[33:33-1] == 2'd2) m1_lt = na[33-2] && !nb[33-2];
      else if (na[33:33-1] == 2'd2) m1_lt = na[33-2];
      else m1_lt = !nb[33-2];
    end else if (za && zb) m1_lt = 1'b0;
    else if (sa != sb) m1_lt = sa;
    else begin
      ea = na[22+8:22+1]; eb = nb[22+8:22+1];
      if (za) mag_lt = 1'b1; else if (zb) mag_lt = 1'b0;
      else mag_lt = (ea < eb) || (ea == eb && (na[22:1] < nb[22:1] || (na[22:1] == nb[22:1] && !na[0] && nb[0])));
      m1_lt = sa ? !mag_lt && !(za && zb) && !m1_eq(na, nb) : mag_lt;
    end
  endfunction
  function automatic m1_eq(input [33:0] a, input [33:0] b);
    logic [33:0] na, nb; logic za, zb;
    na = m1_norm(a); nb = m1_norm(b);
    za = (na[22:1] == 0) && !na[0]; zb = (nb[22:1] == 0) && !nb[0];
    if (na[33:33-1] == 2'd1 || nb[33:33-1] == 2'd1) m1_eq = 1'b0;
    else if (na[33:33-1] == 2'd2 || nb[33:33-1] == 2'd2)
      m1_eq = (na[33:33-1] == nb[33:33-1]) && (na[33-2] == nb[33-2]);
    else if (za || zb) m1_eq = za && zb;
    else m1_eq = (na[33-2] == nb[33-2]) && (na[22+8:22+1] == nb[22+8:22+1]) && (na[22:1] == nb[22:1]) && (na[0] == nb[0]);
  endfunction

  function automatic [20:0] m1_unpack_s(input [7:0] b, input daz);
    logic s; logic [7:0] mag; integer i;
    s = b[7]; mag = s ? (~b + 1'b1) : b;
    m1_unpack_s = {1'b0, m1_mkv(2'd0, s && (mag != 0), -0, {{(9-8){1'b0}}, mag})};
  endfunction

  function automatic [7:0] m1_enc(input signed [18:0] v); m1_enc = v[7:0]; endfunction
  function automatic [7:0] m1_wrap(input signed [18:0] v); m1_wrap = v[7:0]; endfunction
  function automatic [7:0] m1_sat(input signed [18:0] v);
    m1_sat = (v > 19'sd127) ? {1'b0, {7{1'b1}}} : (v < -19'sd128) ? {1'b1, {7{1'b0}}} : v[7:0];
  endfunction

  // round v / 2^f under rnd (the SR word applies to the fraction bits)
  function automatic signed [18:0] m1_rshift(input signed [18:0] v, input integer f, input [2:0] rnd, input [7:0] word);
    logic s; logic [18:0] mag, keep, rest, halfv; logic [27:0] fint; logic up, inexact;
    s = v < 0; mag = s ? -v : v;
    if (f <= 0) m1_rshift = v;
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
      m1_rshift = s ? -$signed(keep) : $signed(keep);
    end
  endfunction
  // the SR word of a division: floor(|r| * 2^sb / |b|)
  function automatic [7:0] m1_divfrac(input [18:0] r, input [18:0] b);
    logic [27:0] t;
    t = ({{9{1'b0}}, r} << 8) / {{9{1'b0}}, b};
    m1_divfrac = t[7:0];
  endfunction
endpackage
// ADIR-MEMBER top
// EVOLVE-BLOCK-START
// ADIR-DECL v1
// STRUCTURE m0.l0.adder kind=adder slot=adder mode=0 lane=0 width=16 format=int16_twos_complement ops=add sv=alu_core_u_m0_l0_adder
// STRUCTURE m0.l0.multiplier kind=multiplier slot=multiplier mode=0 lane=0 width=16 format=int16_twos_complement ops=mul,mul_wide sv=alu_core_u_m0_l0_multiplier
// STRUCTURE m1.l0.adder kind=adder slot=adder mode=1 lane=0 width=8 format=int8_twos_complement ops=add sv=alu_core_u_m1_l0_adder
// STRUCTURE m1.l1.adder kind=adder slot=adder mode=1 lane=1 width=8 format=int8_twos_complement ops=add sv=alu_core_u_m1_l1_adder
// STRUCTURE m1.l0.multiplier kind=multiplier slot=multiplier mode=1 lane=0 width=8 format=int8_twos_complement ops=mul,mul_wide sv=alu_core_u_m1_l0_multiplier
// STRUCTURE m1.l1.multiplier kind=multiplier slot=multiplier mode=1 lane=1 width=8 format=int8_twos_complement ops=mul,mul_wide sv=alu_core_u_m1_l1_multiplier
// ADIR-END
module alu_core (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [1:0] op,
  input  logic [0:0] mode,
  output logic [31:0] y
);
  // alu_core: behavioral reference derived from the instance (modes 1xint16_twos_complement, 2xint8_twos_complement; ops add, mul, mul_wide). Every (mode, op) pair computes the verify layer's exact semantics.
  // HIERARCHY: 6 physical structure modules instantiated by alu_core, built from 4 lane modules (one per mode and kind, parameter LANE) and 2 packages of engine functions (one per mode); a float mode's datapath is split into an unpacker (the xa/xb/den buses), the arithmetic and converter structures (unrounded results on the x bus) and a rounder (y and the flags); 0 misc lane modules and 0 block-conversion group modules
  // UNIT m0.l0.adder module=alu_core_u_m0_l0_adder kind=adder members=m0.l0.adder
  // UNIT m0.l0.multiplier module=alu_core_u_m0_l0_multiplier kind=multiplier members=m0.l0.multiplier
  // UNIT m1.l0.adder module=alu_core_u_m1_l0_adder kind=adder members=m1.l0.adder
  // UNIT m1.l1.adder module=alu_core_u_m1_l1_adder kind=adder members=m1.l1.adder
  // UNIT m1.l0.multiplier module=alu_core_u_m1_l0_multiplier kind=multiplier members=m1.l0.multiplier
  // UNIT m1.l1.multiplier module=alu_core_u_m1_l1_multiplier kind=multiplier members=m1.l1.multiplier
  // // STRUCTURE m0.l0.adder kind=adder slot=adder mode=0 lane=0 width=16 format=int16_twos_complement ops=add sv=alu_core_u_m0_l0_adder
  // // STRUCTURE m0.l0.multiplier kind=multiplier slot=multiplier mode=0 lane=0 width=16 format=int16_twos_complement ops=mul,mul_wide sv=alu_core_u_m0_l0_multiplier
  // // STRUCTURE m1.l0.adder kind=adder slot=adder mode=1 lane=0 width=8 format=int8_twos_complement ops=add sv=alu_core_u_m1_l0_adder
  // // STRUCTURE m1.l1.adder kind=adder slot=adder mode=1 lane=1 width=8 format=int8_twos_complement ops=add sv=alu_core_u_m1_l1_adder
  // // STRUCTURE m1.l0.multiplier kind=multiplier slot=multiplier mode=1 lane=0 width=8 format=int8_twos_complement ops=mul,mul_wide sv=alu_core_u_m1_l0_multiplier
  // // STRUCTURE m1.l1.multiplier kind=multiplier slot=multiplier mode=1 lane=1 width=8 format=int8_twos_complement ops=mul,mul_wide sv=alu_core_u_m1_l1_multiplier
  // LIBRARY: fam_add_partitioned_w16_16_carry_kill_gate_7759ae4142ca, fam_add_partitioned_w16_8_carry_kill_gate_7759ae4142ca, fam_adder_ripple_carry, fam_adder_ripple_chunk, fam_adder_segmented_carry_speculative_w16_830447882030, fam_adder_segmented_carry_speculative_w8_830447882030, fam_mul_dynamic_segment_ax_w16_s_dd0cff2b0af2, fam_mul_dynamic_segment_ax_w8_s_dd0cff2b0af2, fam_shift_barrel_mux_tree, fam_shift_keep_mask, fam_shift_stage (chialu.targets.rtl.families: the modules of the declared families the lane modules instantiate; their text follows the generated modules)
  logic [2:0] rnd_sel;
  logic [2:0] rnd;
  logic daz;
  logic ftz;
  logic dual;
  logic [31:0] y_m0_m0_l0_adder;
  logic [19:0] fl_m0_m0_l0_adder;
  logic [31:0] y_m0_m0_l0_multiplier;
  logic [19:0] fl_m0_m0_l0_multiplier;
  logic [31:0] y_m0;
  logic [19:0] fl_m0;
  logic [31:0] y_m1_m1_l0_adder;
  logic [19:0] fl_m1_m1_l0_adder;
  logic [31:0] y_m1_m1_l1_adder;
  logic [19:0] fl_m1_m1_l1_adder;
  logic [31:0] y_m1_m1_l0_multiplier;
  logic [19:0] fl_m1_m1_l0_multiplier;
  logic [31:0] y_m1_m1_l1_multiplier;
  logic [19:0] fl_m1_m1_l1_multiplier;
  logic [31:0] y_m1;
  logic [19:0] fl_m1;
  logic [19:0] fl_all;
  assign rnd_sel = 3'd0;
  assign rnd = rnd_sel;
  assign daz = 1'b0;
  assign ftz = 1'b0;
  assign dual = 1'b0;
  assign y_m0 = y_m0_m0_l0_adder | y_m0_m0_l0_multiplier;
  assign fl_m0 = fl_m0_m0_l0_adder | fl_m0_m0_l0_multiplier;
  assign y_m1 = y_m1_m1_l0_adder | y_m1_m1_l1_adder | y_m1_m1_l0_multiplier | y_m1_m1_l1_multiplier;
  assign fl_m1 = fl_m1_m1_l0_adder | fl_m1_m1_l1_adder | fl_m1_m1_l0_multiplier | fl_m1_m1_l1_multiplier;
  alu_core_u_m0_l0_adder u_m0_l0_adder (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_m0_l0_adder), .fl_m0(fl_m0_m0_l0_adder));
  alu_core_u_m0_l0_multiplier u_m0_l0_multiplier (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_m0_l0_multiplier), .fl_m0(fl_m0_m0_l0_multiplier));
  alu_core_u_m1_l0_adder u_m1_l0_adder (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l0_adder), .fl_m1(fl_m1_m1_l0_adder));
  alu_core_u_m1_l1_adder u_m1_l1_adder (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l1_adder), .fl_m1(fl_m1_m1_l1_adder));
  alu_core_u_m1_l0_multiplier u_m1_l0_multiplier (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l0_multiplier), .fl_m1(fl_m1_m1_l0_multiplier));
  alu_core_u_m1_l1_multiplier u_m1_l1_multiplier (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l1_multiplier), .fl_m1(fl_m1_m1_l1_multiplier));
  always_comb begin
    case (mode)
      1'd0: begin y = y_m0; fl_all = fl_m0; end
      1'd1: begin y = y_m1; fl_all = fl_m1; end
      default: begin y = '0; fl_all = '0; end
    endcase
  end
endmodule
// EVOLVE-BLOCK-END

module alu_core_m0_adder_sh #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [1:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m0,
  output logic [19:0] fl_m0,
  output logic [15:0] pc_a_m0,
  output logic [15:0] pc_b_m0,
  output logic [0:0] pc_cin_m0,
  input  logic [15:0] pc_s_m0,
  input  logic [0:0] pc_co_m0
);
  // alu_core_m0_adder_sh: lane LANE of mode 0 (int16_twos_complement) for the adder ops add; the result buses are the mode's, with only this lane's bits written; the unit's shared adder serve this lane through the pc_/tp_ buses
  import alu_core_m0_pkg::*;
  logic d_m0;
  logic [15:0] m0_aLANE;
  logic [15:0] m0_bLANE;
  logic [49:0] m0_xa [0:0];
  logic [49:0] m0_xb [0:0];
  logic signed [16:0] m0_vaLANE;
  logic signed [16:0] m0_vbLANE;
  logic [15:0] m0_add_sLANE;
  logic m0_add_coutLANE;
  logic signed [34:0] m0_o0ex0_LANE;
  assign m0_aLANE = a[(LANE*16) +: 16];
  assign m0_bLANE = b[(LANE*16) +: 16];
  assign m0_xa[LANE] = m0_x(m0_unpack_s(m0_aLANE, 1'b0));
  assign m0_xb[LANE] = m0_x(m0_unpack_s(m0_bLANE, 1'b0));
  assign m0_vaLANE = {m0_aLANE[15], m0_aLANE};
  assign m0_vbLANE = {m0_bLANE[15], m0_bLANE};
  // structure core.adder.m0: the unit's shared partitioned adder (subword partitioned_carry_chain)
  assign m0_add_sLANE = pc_s_m0[(LANE)*16 +: 16];
  assign m0_add_coutLANE = pc_co_m0[(LANE+1)*1-1];
  always_comb begin
    y_m0 = '0; d_m0 = '0; fl_m0 = '0;
    m0_o0ex0_LANE = 'x;
    pc_a_m0 = '0; pc_b_m0 = '0; pc_cin_m0 = '0;
    case (op)
      2'd0: begin
        pc_a_m0[(LANE)*16 +: 16] = m0_aLANE; pc_b_m0[(LANE)*16 +: 16] = m0_bLANE; pc_cin_m0[(LANE)*1] = 1'b0;
        m0_o0ex0_LANE = $signed({(m0_aLANE[15] ^ m0_bLANE[15] ^ m0_add_coutLANE), m0_add_sLANE});
        y_m0[((LANE*16)+0) +: 16] = m0_wrap(m0_o0ex0_LANE);
        fl_m0[(0+LANE)*10 +: 10] = (((m0_aLANE[15] ^ m0_bLANE[15] ^ m0_add_coutLANE) ^ m0_add_sLANE[15]) ? (10'd1 << 8) : 10'd0) | (((m0_aLANE[15] ^ m0_bLANE[15] ^ m0_add_coutLANE) ^ m0_add_sLANE[15]) ? (10'd1 << 2) : 10'd0) | (m0_add_coutLANE ? (10'd1 << 7) : 10'd0);
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m0_multiplier #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [1:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m0,
  output logic [19:0] fl_m0
);
  // alu_core_m0_multiplier: lane LANE of mode 0 (int16_twos_complement) for the multiplier ops mul, mul_wide; the result buses are the mode's, with only this lane's bits written
  import alu_core_m0_pkg::*;
  logic d_m0;
  logic [15:0] m0_aLANE;
  logic [15:0] m0_bLANE;
  logic [49:0] m0_xa [0:0];
  logic [49:0] m0_xb [0:0];
  logic signed [16:0] m0_vaLANE;
  logic signed [16:0] m0_vbLANE;
  logic [15:0] m0_mul_aLANE;
  logic [15:0] m0_mul_bLANE;
  logic [31:0] m0_mul_pLANE;
  logic signed [34:0] m0_o1ex0_LANE;
  logic signed [34:0] m0_o2ex0_LANE;
  assign m0_aLANE = a[(LANE*16) +: 16];
  assign m0_bLANE = b[(LANE*16) +: 16];
  assign m0_xa[LANE] = m0_x(m0_unpack_s(m0_aLANE, 1'b0));
  assign m0_xb[LANE] = m0_x(m0_unpack_s(m0_bLANE, 1'b0));
  assign m0_vaLANE = {m0_aLANE[15], m0_aLANE};
  assign m0_vbLANE = {m0_bLANE[15], m0_bLANE};
  // structure core.multiplier.m0: family dynamic_segment realized by the library module fam_mul_dynamic_segment_ax_w16_s_dd0cff2b0af2
  fam_mul_dynamic_segment_ax_w16_s_dd0cff2b0af2 u_m0_mulLANE (.a(m0_mul_aLANE), .b(m0_mul_bLANE), .p(m0_mul_pLANE));
  always_comb begin
    y_m0 = '0; d_m0 = '0; fl_m0 = '0;
    m0_mul_aLANE = 'x; m0_mul_bLANE = 'x; m0_o1ex0_LANE = 'x; m0_o2ex0_LANE = 'x;
    case (op)
      2'd1: begin
        m0_mul_aLANE = m0_aLANE; m0_mul_bLANE = m0_bLANE;
        m0_o1ex0_LANE = $signed({{3{m0_mul_pLANE[31]}}, m0_mul_pLANE});
        y_m0[((LANE*16)+0) +: 16] = m0_wrap(m0_o1ex0_LANE);
        fl_m0[(0+LANE)*10 +: 10] = (m0_o1ex0_LANE > 35'sd32767 || m0_o1ex0_LANE < -35'sd32768 ? (10'd1 << 8) : 10'd0) | (m0_o1ex0_LANE > 35'sd32767 || m0_o1ex0_LANE < -35'sd32768 ? (10'd1 << 2) : 10'd0);
      end
      2'd2: begin
        m0_mul_aLANE = m0_aLANE; m0_mul_bLANE = m0_bLANE;
        m0_o2ex0_LANE = $signed({{3{m0_mul_pLANE[31]}}, m0_mul_pLANE});
        y_m0[((LANE*32)+0) +: 32] = m0_o2ex0_LANE[31:0];
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m1_adder_sh #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [1:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m1,
  output logic [19:0] fl_m1,
  output logic [15:0] pc_a_m1,
  output logic [15:0] pc_b_m1,
  output logic [1:0] pc_cin_m1,
  input  logic [15:0] pc_s_m1,
  input  logic [1:0] pc_co_m1
);
  // alu_core_m1_adder_sh: lane LANE of mode 1 (int8_twos_complement) for the adder ops add; the result buses are the mode's, with only this lane's bits written; the unit's shared adder serve this lane through the pc_/tp_ buses
  import alu_core_m1_pkg::*;
  logic d_m1;
  logic [7:0] m1_aLANE;
  logic [7:0] m1_bLANE;
  logic [33:0] m1_xa [0:1];
  logic [33:0] m1_xb [0:1];
  logic signed [8:0] m1_vaLANE;
  logic signed [8:0] m1_vbLANE;
  logic [7:0] m1_add_sLANE;
  logic m1_add_coutLANE;
  logic signed [18:0] m1_o0ex0_LANE;
  assign m1_aLANE = a[(LANE*8) +: 8];
  assign m1_bLANE = b[(LANE*8) +: 8];
  assign m1_xa[LANE] = m1_x(m1_unpack_s(m1_aLANE, 1'b0));
  assign m1_xb[LANE] = m1_x(m1_unpack_s(m1_bLANE, 1'b0));
  assign m1_vaLANE = {m1_aLANE[7], m1_aLANE};
  assign m1_vbLANE = {m1_bLANE[7], m1_bLANE};
  // structure core.adder.m1: the unit's shared partitioned adder (subword partitioned_carry_chain)
  assign m1_add_sLANE = pc_s_m1[(LANE)*8 +: 8];
  assign m1_add_coutLANE = pc_co_m1[(LANE+1)*1-1];
  always_comb begin
    y_m1 = '0; d_m1 = '0; fl_m1 = '0;
    m1_o0ex0_LANE = 'x;
    pc_a_m1 = '0; pc_b_m1 = '0; pc_cin_m1 = '0;
    case (op)
      2'd0: begin
        pc_a_m1[(LANE)*8 +: 8] = m1_aLANE; pc_b_m1[(LANE)*8 +: 8] = m1_bLANE; pc_cin_m1[(LANE)*1] = 1'b0;
        m1_o0ex0_LANE = $signed({(m1_aLANE[7] ^ m1_bLANE[7] ^ m1_add_coutLANE), m1_add_sLANE});
        y_m1[((LANE*8)+0) +: 8] = m1_wrap(m1_o0ex0_LANE);
        fl_m1[(0+LANE)*10 +: 10] = (((m1_aLANE[7] ^ m1_bLANE[7] ^ m1_add_coutLANE) ^ m1_add_sLANE[7]) ? (10'd1 << 8) : 10'd0) | (((m1_aLANE[7] ^ m1_bLANE[7] ^ m1_add_coutLANE) ^ m1_add_sLANE[7]) ? (10'd1 << 2) : 10'd0) | (m1_add_coutLANE ? (10'd1 << 7) : 10'd0);
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m1_multiplier #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [1:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m1,
  output logic [19:0] fl_m1
);
  // alu_core_m1_multiplier: lane LANE of mode 1 (int8_twos_complement) for the multiplier ops mul, mul_wide; the result buses are the mode's, with only this lane's bits written
  import alu_core_m1_pkg::*;
  logic d_m1;
  logic [7:0] m1_aLANE;
  logic [7:0] m1_bLANE;
  logic [33:0] m1_xa [0:1];
  logic [33:0] m1_xb [0:1];
  logic signed [8:0] m1_vaLANE;
  logic signed [8:0] m1_vbLANE;
  logic [7:0] m1_mul_aLANE;
  logic [7:0] m1_mul_bLANE;
  logic [15:0] m1_mul_pLANE;
  logic signed [18:0] m1_o1ex0_LANE;
  logic signed [18:0] m1_o2ex0_LANE;
  assign m1_aLANE = a[(LANE*8) +: 8];
  assign m1_bLANE = b[(LANE*8) +: 8];
  assign m1_xa[LANE] = m1_x(m1_unpack_s(m1_aLANE, 1'b0));
  assign m1_xb[LANE] = m1_x(m1_unpack_s(m1_bLANE, 1'b0));
  assign m1_vaLANE = {m1_aLANE[7], m1_aLANE};
  assign m1_vbLANE = {m1_bLANE[7], m1_bLANE};
  // structure core.multiplier.m1: family dynamic_segment realized by the library module fam_mul_dynamic_segment_ax_w8_s_dd0cff2b0af2
  fam_mul_dynamic_segment_ax_w8_s_dd0cff2b0af2 u_m1_mulLANE (.a(m1_mul_aLANE), .b(m1_mul_bLANE), .p(m1_mul_pLANE));
  always_comb begin
    y_m1 = '0; d_m1 = '0; fl_m1 = '0;
    m1_mul_aLANE = 'x; m1_mul_bLANE = 'x; m1_o1ex0_LANE = 'x; m1_o2ex0_LANE = 'x;
    case (op)
      2'd1: begin
        m1_mul_aLANE = m1_aLANE; m1_mul_bLANE = m1_bLANE;
        m1_o1ex0_LANE = $signed({{3{m1_mul_pLANE[15]}}, m1_mul_pLANE});
        y_m1[((LANE*8)+0) +: 8] = m1_wrap(m1_o1ex0_LANE);
        fl_m1[(0+LANE)*10 +: 10] = (m1_o1ex0_LANE > 19'sd127 || m1_o1ex0_LANE < -19'sd128 ? (10'd1 << 8) : 10'd0) | (m1_o1ex0_LANE > 19'sd127 || m1_o1ex0_LANE < -19'sd128 ? (10'd1 << 2) : 10'd0);
      end
      2'd2: begin
        m1_mul_aLANE = m1_aLANE; m1_mul_bLANE = m1_bLANE;
        m1_o2ex0_LANE = $signed({{3{m1_mul_pLANE[15]}}, m1_mul_pLANE});
        y_m1[((LANE*16)+0) +: 16] = m1_o2ex0_LANE[15:0];
      end
      default: ;
    endcase
  end
endmodule
// ADIR-MEMBER m0_l0_adder
// EVOLVE-BLOCK-START
module alu_core_u_m0_l0_adder (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [1:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m0,
  output logic [19:0] fl_m0
);
  // alu_core_u_m0_l0_adder: physical structure `m0.l0.adder` (kind adder, slot adder); realizes m0.l0.adder: adder, mode 0 lane 0, int16_twos_complement, ops add
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [15:0] pc_a_m0;
  logic [15:0] pc_b_m0;
  logic pc_cin_m0;
  logic [15:0] pc_s_m0;
  logic pc_co_m0;
  logic [31:0] y_m0_l0;
  logic [19:0] fl_m0_l0;
  logic [15:0] pc_a_m0_l0;
  logic [15:0] pc_b_m0_l0;
  logic pc_cin_m0_l0;
  logic pc_sel;
  logic [15:0] pc_a;
  logic [15:0] pc_b;
  logic pc_cin;
  logic [15:0] pc_s;
  logic pc_co;
  alu_core_m0_adder_sh #(.LANE(0)) u_m0_l0 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_l0), .fl_m0(fl_m0_l0), .pc_a_m0(pc_a_m0_l0), .pc_b_m0(pc_b_m0_l0), .pc_cin_m0(pc_cin_m0_l0), .pc_s_m0(pc_s_m0), .pc_co_m0(pc_co_m0));
  assign y_m0 = y_m0_l0;
  assign fl_m0 = fl_m0_l0;
  assign pc_a_m0 = pc_a_m0_l0;
  assign pc_b_m0 = pc_b_m0_l0;
  assign pc_cin_m0 = pc_cin_m0_l0;
  assign pc_sel = (mode == 1'd0) ? 1'd0 : '0;
  assign pc_a = (mode == 1'd0) ? pc_a_m0 : '0;
  assign pc_b = (mode == 1'd0) ? pc_b_m0 : '0;
  assign pc_cin = (mode == 1'd0) ? pc_cin_m0 : '0;
  // subword partitioned_carry_chain: one library adder over the whole word, its carries cut at the selected packing's lane boundaries (1 x int16_twos_complement)
  fam_add_partitioned_w16_16_carry_kill_gate_7759ae4142ca u_part (.a(pc_a), .b(pc_b), .cin(pc_cin), .sel(pc_sel), .s(pc_s), .cout(pc_co));
  assign pc_s_m0 = pc_s;
  assign pc_co_m0 = pc_co;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m0_l0_multiplier
// EVOLVE-BLOCK-START
module alu_core_u_m0_l0_multiplier (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [1:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m0,
  output logic [19:0] fl_m0
);
  // alu_core_u_m0_l0_multiplier: physical structure `m0.l0.multiplier` (kind multiplier, slot multiplier); realizes m0.l0.multiplier: multiplier, mode 0 lane 0, int16_twos_complement, ops mul, mul_wide
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [31:0] y_m0_l0;
  logic [19:0] fl_m0_l0;
  alu_core_m0_multiplier #(.LANE(0)) u_m0_l0 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_l0), .fl_m0(fl_m0_l0));
  assign y_m0 = y_m0_l0;
  assign fl_m0 = fl_m0_l0;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l0_adder
// EVOLVE-BLOCK-START
module alu_core_u_m1_l0_adder (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [1:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m1,
  output logic [19:0] fl_m1
);
  // alu_core_u_m1_l0_adder: physical structure `m1.l0.adder` (kind adder, slot adder); realizes m1.l0.adder: adder, mode 1 lane 0, int8_twos_complement, ops add
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [15:0] pc_a_m1;
  logic [15:0] pc_b_m1;
  logic [1:0] pc_cin_m1;
  logic [15:0] pc_s_m1;
  logic [1:0] pc_co_m1;
  logic [31:0] y_m1_l0;
  logic [19:0] fl_m1_l0;
  logic [15:0] pc_a_m1_l0;
  logic [15:0] pc_b_m1_l0;
  logic [1:0] pc_cin_m1_l0;
  logic pc_sel;
  logic [15:0] pc_a;
  logic [15:0] pc_b;
  logic [1:0] pc_cin;
  logic [15:0] pc_s;
  logic [1:0] pc_co;
  alu_core_m1_adder_sh #(.LANE(0)) u_m1_l0 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_l0), .fl_m1(fl_m1_l0), .pc_a_m1(pc_a_m1_l0), .pc_b_m1(pc_b_m1_l0), .pc_cin_m1(pc_cin_m1_l0), .pc_s_m1(pc_s_m1), .pc_co_m1(pc_co_m1));
  assign y_m1 = y_m1_l0;
  assign fl_m1 = fl_m1_l0;
  assign pc_a_m1 = pc_a_m1_l0;
  assign pc_b_m1 = pc_b_m1_l0;
  assign pc_cin_m1 = pc_cin_m1_l0;
  assign pc_sel = (mode == 1'd1) ? 1'd0 : '0;
  assign pc_a = (mode == 1'd1) ? pc_a_m1 : '0;
  assign pc_b = (mode == 1'd1) ? pc_b_m1 : '0;
  assign pc_cin = (mode == 1'd1) ? pc_cin_m1 : '0;
  // subword partitioned_carry_chain: one library adder over the whole word, its carries cut at the selected packing's lane boundaries (2 x int8_twos_complement)
  fam_add_partitioned_w16_8_carry_kill_gate_7759ae4142ca u_part (.a(pc_a), .b(pc_b), .cin(pc_cin), .sel(pc_sel), .s(pc_s), .cout(pc_co));
  assign pc_s_m1 = pc_s;
  assign pc_co_m1 = pc_co;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l1_adder
// EVOLVE-BLOCK-START
module alu_core_u_m1_l1_adder (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [1:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m1,
  output logic [19:0] fl_m1
);
  // alu_core_u_m1_l1_adder: physical structure `m1.l1.adder` (kind adder, slot adder); realizes m1.l1.adder: adder, mode 1 lane 1, int8_twos_complement, ops add
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [15:0] pc_a_m1;
  logic [15:0] pc_b_m1;
  logic [1:0] pc_cin_m1;
  logic [15:0] pc_s_m1;
  logic [1:0] pc_co_m1;
  logic [31:0] y_m1_l1;
  logic [19:0] fl_m1_l1;
  logic [15:0] pc_a_m1_l1;
  logic [15:0] pc_b_m1_l1;
  logic [1:0] pc_cin_m1_l1;
  logic pc_sel;
  logic [15:0] pc_a;
  logic [15:0] pc_b;
  logic [1:0] pc_cin;
  logic [15:0] pc_s;
  logic [1:0] pc_co;
  alu_core_m1_adder_sh #(.LANE(1)) u_m1_l1 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_l1), .fl_m1(fl_m1_l1), .pc_a_m1(pc_a_m1_l1), .pc_b_m1(pc_b_m1_l1), .pc_cin_m1(pc_cin_m1_l1), .pc_s_m1(pc_s_m1), .pc_co_m1(pc_co_m1));
  assign y_m1 = y_m1_l1;
  assign fl_m1 = fl_m1_l1;
  assign pc_a_m1 = pc_a_m1_l1;
  assign pc_b_m1 = pc_b_m1_l1;
  assign pc_cin_m1 = pc_cin_m1_l1;
  assign pc_sel = (mode == 1'd1) ? 1'd0 : '0;
  assign pc_a = (mode == 1'd1) ? pc_a_m1 : '0;
  assign pc_b = (mode == 1'd1) ? pc_b_m1 : '0;
  assign pc_cin = (mode == 1'd1) ? pc_cin_m1 : '0;
  // subword partitioned_carry_chain: one library adder over the whole word, its carries cut at the selected packing's lane boundaries (2 x int8_twos_complement)
  fam_add_partitioned_w16_8_carry_kill_gate_7759ae4142ca u_part (.a(pc_a), .b(pc_b), .cin(pc_cin), .sel(pc_sel), .s(pc_s), .cout(pc_co));
  assign pc_s_m1 = pc_s;
  assign pc_co_m1 = pc_co;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l0_multiplier
// EVOLVE-BLOCK-START
module alu_core_u_m1_l0_multiplier (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [1:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m1,
  output logic [19:0] fl_m1
);
  // alu_core_u_m1_l0_multiplier: physical structure `m1.l0.multiplier` (kind multiplier, slot multiplier); realizes m1.l0.multiplier: multiplier, mode 1 lane 0, int8_twos_complement, ops mul, mul_wide
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [31:0] y_m1_l0;
  logic [19:0] fl_m1_l0;
  alu_core_m1_multiplier #(.LANE(0)) u_m1_l0 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_l0), .fl_m1(fl_m1_l0));
  assign y_m1 = y_m1_l0;
  assign fl_m1 = fl_m1_l0;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l1_multiplier
// EVOLVE-BLOCK-START
module alu_core_u_m1_l1_multiplier (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [1:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [31:0] y_m1,
  output logic [19:0] fl_m1
);
  // alu_core_u_m1_l1_multiplier: physical structure `m1.l1.multiplier` (kind multiplier, slot multiplier); realizes m1.l1.multiplier: multiplier, mode 1 lane 1, int8_twos_complement, ops mul, mul_wide
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [31:0] y_m1_l1;
  logic [19:0] fl_m1_l1;
  alu_core_m1_multiplier #(.LANE(1)) u_m1_l1 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_l1), .fl_m1(fl_m1_l1));
  assign y_m1 = y_m1_l1;
  assign fl_m1 = fl_m1_l1;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER library
// ---- the family library modules the lane modules instantiate (chialu/targets/rtl/families; fixed text, replaced by editing the instances)
// partitioned_carry_chain (carry_kill_gate, segmented_carry_speculative segments of 16 bits): one adder for the lane packings 1 x 16, the carry cut at the selected mode's lane boundaries
module fam_add_partitioned_w16_16_carry_kill_gate_7759ae4142ca (input logic [15:0] a, input logic [15:0] b, input logic [0:0] cin, input logic [0:0] sel, output logic [15:0] s, output logic [0:0] cout);
  logic [1:0] c;
  assign c[0] = cin[0];
  logic co0;
  fam_adder_segmented_carry_speculative_w16_830447882030 u0 (.a(a[15:0]), .b(b[15:0]), .cin(c[0]), .s(s[15:0]), .cout(co0));
  assign cout[0] = co0;
  assign c[1] = co0;
endmodule

// partitioned_carry_chain (carry_kill_gate, segmented_carry_speculative segments of 8 bits): one adder for the lane packings 2 x 8, the carry cut at the selected mode's lane boundaries
module fam_add_partitioned_w16_8_carry_kill_gate_7759ae4142ca (input logic [15:0] a, input logic [15:0] b, input logic [1:0] cin, input logic [0:0] sel, output logic [15:0] s, output logic [1:0] cout);
  logic [2:0] c;
  assign c[0] = cin[0];
  logic co0;
  fam_adder_segmented_carry_speculative_w8_830447882030 u0 (.a(a[7:0]), .b(b[7:0]), .cin(c[0]), .s(s[7:0]), .cout(co0));
  assign cout[0] = co0;
  logic bnd1; assign bnd1 = (sel == 1'd0);
  assign c[1] = (co0 & ~bnd1) | (cin[1] & bnd1);
  logic co1;
  fam_adder_segmented_carry_speculative_w8_830447882030 u1 (.a(a[15:8]), .b(b[15:8]), .cin(c[1]), .s(s[15:8]), .cout(co1));
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

// segmented_carry_speculative: 4-bit sub-adders (ripple_carry), carry-in by constant_zero over a 0-bit window, correction none (the ArithmeticError gate governs)
module fam_adder_segmented_carry_speculative_w16_830447882030 (input logic [15:0] a, input logic [15:0] b, input logic cin, output logic [15:0] s, output logic cout);
  logic [4:0] c;
  assign c[0] = cin;
  logic [4:0] cr;
  assign cr[0] = cin;
  logic sp0; assign sp0 = cin;
  logic [3:0] s0;
  logic co0;
  // sub-adder 0
  fam_adder_ripple_carry #(.W(4), .CHUNK(1), .FORM(0)) u1 (.a(a[3:0]), .b(b[3:0]), .cin(sp0), .s(s0), .cout(co0));
  logic P0; assign P0 = &(a[3:0] ^ b[3:0]);
  logic G0; assign G0 = co0 & ~(P0 & sp0);
  assign cr[1] = G0 | (P0 & cr[0]);
  assign c[1] = co0;
  assign s[3:0] = s0;
  logic sp1; assign sp1 = 1'b0;
  logic [3:0] s1;
  logic co1;
  // sub-adder 1
  fam_adder_ripple_carry #(.W(4), .CHUNK(1), .FORM(0)) u2 (.a(a[7:4]), .b(b[7:4]), .cin(sp1), .s(s1), .cout(co1));
  logic P1; assign P1 = &(a[7:4] ^ b[7:4]);
  logic G1; assign G1 = co1 & ~(P1 & sp1);
  assign cr[2] = G1 | (P1 & cr[1]);
  assign c[2] = co1;
  assign s[7:4] = s1;
  logic sp2; assign sp2 = 1'b0;
  logic [3:0] s2;
  logic co2;
  // sub-adder 2
  fam_adder_ripple_carry #(.W(4), .CHUNK(1), .FORM(0)) u3 (.a(a[11:8]), .b(b[11:8]), .cin(sp2), .s(s2), .cout(co2));
  logic P2; assign P2 = &(a[11:8] ^ b[11:8]);
  logic G2; assign G2 = co2 & ~(P2 & sp2);
  assign cr[3] = G2 | (P2 & cr[2]);
  assign c[3] = co2;
  assign s[11:8] = s2;
  logic sp3; assign sp3 = 1'b0;
  logic [3:0] s3;
  logic co3;
  // sub-adder 3
  fam_adder_ripple_carry #(.W(4), .CHUNK(1), .FORM(0)) u4 (.a(a[15:12]), .b(b[15:12]), .cin(sp3), .s(s3), .cout(co3));
  logic P3; assign P3 = &(a[15:12] ^ b[15:12]);
  logic G3; assign G3 = co3 & ~(P3 & sp3);
  assign cr[4] = G3 | (P3 & cr[3]);
  assign c[4] = co3;
  assign s[15:12] = s3;
  assign cout = c[4];
endmodule


// segmented_carry_speculative: 4-bit sub-adders (ripple_carry), carry-in by constant_zero over a 0-bit window, correction none (the ArithmeticError gate governs)
module fam_adder_segmented_carry_speculative_w8_830447882030 (input logic [7:0] a, input logic [7:0] b, input logic cin, output logic [7:0] s, output logic cout);
  logic [2:0] c;
  assign c[0] = cin;
  logic [2:0] cr;
  assign cr[0] = cin;
  logic sp0; assign sp0 = cin;
  logic [3:0] s0;
  logic co0;
  // sub-adder 0
  fam_adder_ripple_carry #(.W(4), .CHUNK(1), .FORM(0)) u1 (.a(a[3:0]), .b(b[3:0]), .cin(sp0), .s(s0), .cout(co0));
  logic P0; assign P0 = &(a[3:0] ^ b[3:0]);
  logic G0; assign G0 = co0 & ~(P0 & sp0);
  assign cr[1] = G0 | (P0 & cr[0]);
  assign c[1] = co0;
  assign s[3:0] = s0;
  logic sp1; assign sp1 = 1'b0;
  logic [3:0] s1;
  logic co1;
  // sub-adder 1
  fam_adder_ripple_carry #(.W(4), .CHUNK(1), .FORM(0)) u2 (.a(a[7:4]), .b(b[7:4]), .cin(sp1), .s(s1), .cout(co1));
  logic P1; assign P1 = &(a[7:4] ^ b[7:4]);
  logic G1; assign G1 = co1 & ~(P1 & sp1);
  assign cr[2] = G1 | (P1 & cr[1]);
  assign c[2] = co1;
  assign s[7:4] = s1;
  assign cout = c[2];
endmodule


// dynamic_segment: a 4-bit window per operand (static_msb_or_lsb; the leading one by lzd_cell_tree, the window by barrel_mux_tree), unbiasing none, the window product by behavioral_star, the position arithmetic by ripple_carry (the ArithmeticError gate governs)
module fam_mul_dynamic_segment_ax_w16_s_dd0cff2b0af2 (input logic [15:0] a, input logic [15:0] b, output logic [31:0] p);
  logic [15:0] am; assign am = a[15] ? -a : a;
  logic [15:0] bm; assign bm = b[15] ? -b : b;
  logic [4:0] lza; assign lza = 5'd0;
  logic [15:0] sha; assign sha = am;
  logic dropa; assign dropa = (lza < 12) && (sha[11:0] != 0);
  logic ovfa; assign ovfa = 1'b0;
  logic [3:0] wina; assign wina = sha[15:12];
  logic [4:0] lzb; assign lzb = 5'd0;
  logic [15:0] shb; assign shb = bm;
  logic dropb; assign dropb = (lzb < 12) && (shb[11:0] != 0);
  logic ovfb; assign ovfb = 1'b0;
  logic [3:0] winb; assign winb = shb[15:12];
  logic [7:0] pw;
  // the window product (behavioral_star) (behavioral_star: the operator)
  assign pw = wina * winb;
  logic [41:0] pwe; assign pwe = {{(42-8){1'b0}}, pw};
  logic [7:0] lzae; assign lzae = {{(8-5){1'b0}}, lza};
  logic [7:0] lzbe; assign lzbe = {{(8-5){1'b0}}, lzb};
  logic [7:0] ovfe; assign ovfe = {{(8-2){1'b0}}, {1'b0, ovfa} + {1'b0, ovfb}};
  logic [8:0] lzsum;
  // the leading positions summed
  fam_adder_ripple_carry #(.W(8), .CHUNK(1), .FORM(0)) u1 (.a(lzae), .b(lzbe), .cin(1'b0), .s(lzsum[7:0]), .cout(lzsum[8]));
  logic [7:0] lzsl; assign lzsl = lzsum[7:0];
  logic [8:0] shs;
  logic [7:0] shs_nb; assign shs_nb = ~ovfe;
  // the rounding overflows taken off
  fam_adder_ripple_carry #(.W(8), .CHUNK(1), .FORM(0)) u2 (.a(lzsl), .b(shs_nb), .cin(1'b1), .s(shs[7:0]), .cout(shs[8]));
  logic [7:0] shift; assign shift = shs[7:0];
  logic [7:0] cst; assign cst = 8'd24;
  logic [8:0] lfs;
  logic [7:0] lfs_nb; assign lfs_nb = ~shift;
  // the distance to the product's place
  fam_adder_ripple_carry #(.W(8), .CHUNK(1), .FORM(0)) u3 (.a(cst), .b(lfs_nb), .cin(1'b1), .s(lfs[7:0]), .cout(lfs[8]));
  logic [7:0] left; assign left = lfs[7:0];
  logic [8:0] lns;
  logic [7:0] lns_nb; assign lns_nb = ~cst;
  // the same distance the other way
  fam_adder_ripple_carry #(.W(8), .CHUNK(1), .FORM(0)) u4 (.a(shift), .b(lns_nb), .cin(1'b1), .s(lns[7:0]), .cout(lns[8]));
  logic [7:0] leftm; assign leftm = left[7] ? lns[7:0] : left;
  logic lbig; assign lbig = leftm >= 42;
  logic [7:0] lam; assign lam = lbig ? 8'd0 : leftm;
  logic [41:0] fl;
  logic [5:0] fl_amt; assign fl_amt = 6'(lam);
  // the window product to its place, leftwards (barrel_mux_tree)
  fam_shift_barrel_mux_tree #(.W(42), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u5 (.a(pwe), .amt(fl_amt), .op(3'd0), .y(fl), .sticky());
  logic [41:0] fr;
  logic [5:0] fr_amt; assign fr_amt = 6'(lam);
  // the window product to its place, rightwards (barrel_mux_tree)
  fam_shift_barrel_mux_tree #(.W(42), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u6 (.a(pwe), .amt(fr_amt), .op(3'd1), .y(fr), .sticky());
  logic [41:0] full; assign full = lbig ? 42'd0 : (left[7] ? fr : fl);
  logic [31:0] pz0; assign pz0 = full[31:0];
  logic [31:0] pz; assign pz = (am == 0 || bm == 0) ? 32'd0 : pz0;
  assign p = (a[15] ^ b[15]) ? -pz : pz;
endmodule


// dynamic_segment: a 4-bit window per operand (static_msb_or_lsb; the leading one by lzd_cell_tree, the window by barrel_mux_tree), unbiasing none, the window product by behavioral_star, the position arithmetic by ripple_carry (the ArithmeticError gate governs)
module fam_mul_dynamic_segment_ax_w8_s_dd0cff2b0af2 (input logic [7:0] a, input logic [7:0] b, output logic [15:0] p);
  logic [7:0] am; assign am = a[7] ? -a : a;
  logic [7:0] bm; assign bm = b[7] ? -b : b;
  logic [3:0] lza; assign lza = 4'd0;
  logic [7:0] sha; assign sha = am;
  logic dropa; assign dropa = (lza < 4) && (sha[3:0] != 0);
  logic ovfa; assign ovfa = 1'b0;
  logic [3:0] wina; assign wina = sha[7:4];
  logic [3:0] lzb; assign lzb = 4'd0;
  logic [7:0] shb; assign shb = bm;
  logic dropb; assign dropb = (lzb < 4) && (shb[3:0] != 0);
  logic ovfb; assign ovfb = 1'b0;
  logic [3:0] winb; assign winb = shb[7:4];
  logic [7:0] pw;
  // the window product (behavioral_star) (behavioral_star: the operator)
  assign pw = wina * winb;
  logic [25:0] pwe; assign pwe = {{(26-8){1'b0}}, pw};
  logic [6:0] lzae; assign lzae = {{(7-4){1'b0}}, lza};
  logic [6:0] lzbe; assign lzbe = {{(7-4){1'b0}}, lzb};
  logic [6:0] ovfe; assign ovfe = {{(7-2){1'b0}}, {1'b0, ovfa} + {1'b0, ovfb}};
  logic [7:0] lzsum;
  // the leading positions summed
  fam_adder_ripple_carry #(.W(7), .CHUNK(1), .FORM(0)) u1 (.a(lzae), .b(lzbe), .cin(1'b0), .s(lzsum[6:0]), .cout(lzsum[7]));
  logic [6:0] lzsl; assign lzsl = lzsum[6:0];
  logic [7:0] shs;
  logic [6:0] shs_nb; assign shs_nb = ~ovfe;
  // the rounding overflows taken off
  fam_adder_ripple_carry #(.W(7), .CHUNK(1), .FORM(0)) u2 (.a(lzsl), .b(shs_nb), .cin(1'b1), .s(shs[6:0]), .cout(shs[7]));
  logic [6:0] shift; assign shift = shs[6:0];
  logic [6:0] cst; assign cst = 7'd8;
  logic [7:0] lfs;
  logic [6:0] lfs_nb; assign lfs_nb = ~shift;
  // the distance to the product's place
  fam_adder_ripple_carry #(.W(7), .CHUNK(1), .FORM(0)) u3 (.a(cst), .b(lfs_nb), .cin(1'b1), .s(lfs[6:0]), .cout(lfs[7]));
  logic [6:0] left; assign left = lfs[6:0];
  logic [7:0] lns;
  logic [6:0] lns_nb; assign lns_nb = ~cst;
  // the same distance the other way
  fam_adder_ripple_carry #(.W(7), .CHUNK(1), .FORM(0)) u4 (.a(shift), .b(lns_nb), .cin(1'b1), .s(lns[6:0]), .cout(lns[7]));
  logic [6:0] leftm; assign leftm = left[6] ? lns[6:0] : left;
  logic lbig; assign lbig = leftm >= 26;
  logic [6:0] lam; assign lam = lbig ? 7'd0 : leftm;
  logic [25:0] fl;
  logic [4:0] fl_amt; assign fl_amt = 5'(lam);
  // the window product to its place, leftwards (barrel_mux_tree)
  fam_shift_barrel_mux_tree #(.W(26), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u5 (.a(pwe), .amt(fl_amt), .op(3'd0), .y(fl), .sticky());
  logic [25:0] fr;
  logic [4:0] fr_amt; assign fr_amt = 5'(lam);
  // the window product to its place, rightwards (barrel_mux_tree)
  fam_shift_barrel_mux_tree #(.W(26), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u6 (.a(pwe), .amt(fr_amt), .op(3'd1), .y(fr), .sticky());
  logic [25:0] full; assign full = lbig ? 26'd0 : (left[6] ? fr : fl);
  logic [15:0] pz0; assign pz0 = full[15:0];
  logic [15:0] pz; assign pz = (am == 0 || bm == 0) ? 16'd0 : pz0;
  assign p = (a[7] ^ b[7]) ? -pz : pz;
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
