// ADIR-DECL v1
// ADIR-END
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

// alu_core_m1_pkg: the exact-arithmetic functions of mode 1 (1xint16_unsigned)
package alu_core_m1_pkg;

  // ---- m1: V = {special[1:0], sign, exp[8] (signed), sig[17]}
  //           X = {special[1:0], sign, exp[8] (signed), sig[38], sticky}
  localparam int m1_SW = 17, m1_EW = 8, m1_XW = 38;
  localparam int m1_VW = 28, m1_XT = 50;
  function automatic [27:0] m1_mkv(input [1:0] sp, input s, input signed [7:0] e, input [16:0] sig);
    m1_mkv = {sp, s, e, sig};
  endfunction
  function automatic [49:0] m1_mkx(input [1:0] sp, input s, input signed [7:0] e, input [37:0] sig, input st);
    m1_mkx = {sp, s, e, sig, st};
  endfunction
  function automatic [49:0] m1_x(input [27:0] v);   // widen V to X
    m1_x = {v[27:27-1], v[27-2], v[27-3 -: 8], {{(38-17){1'b0}}, v[16:0]}, 1'b0};
  endfunction
  // normalize: leading one at bit XW-1 (zero stays zero)
  function automatic [49:0] m1_norm(input [49:0] x);
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
    m1_norm = {x[49:49-1], x[49-2], e, s, x[0]};
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
  function automatic [49:0] m1_add(input [49:0] a, input [49:0] b, input sub);
    logic [49:0] na, nb, big, sml; logic [1:0] spa, spb; logic sa, sb, sr, sw;
    logic signed [7:0] ea, eb, d; logic [38:0] ms, mb, r; logic st, stb; integer sh;
    na = m1_norm(a); nb = m1_norm(b);
    spa = na[49:49-1]; spb = nb[49:49-1];
    sa = na[49-2]; sb = nb[49-2] ^ sub;
    if (spa == 2'd1 || spb == 2'd1) m1_add = m1_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 && spb == 2'd2) m1_add = (sa == sb) ? m1_mkx(2'd2, sa, 0, 0, 1'b0) : m1_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m1_add = m1_mkx(2'd2, sa, 0, 0, 1'b0);
    else if (spb == 2'd2) m1_add = m1_mkx(2'd2, sb, 0, 0, 1'b0);
    else if (na[38:1] == 0 && !na[0]) m1_add = {nb[49:49-1], sb, nb[49-3:0]};
    else if (nb[38:1] == 0 && !nb[0]) m1_add = na;
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
      if (r[38]) begin st = st | r[0]; r = r >> 1; m1_add = m1_mkx(2'd0, sr, big[38+8:38+1] + 1, r[37:0], st); end
      else m1_add = m1_mkx(2'd0, sr, big[38+8:38+1], r[37:0], st);
    end
  endfunction
  function automatic [49:0] m1_mul(input [49:0] a, input [49:0] b);
    logic [49:0] na, nb; logic [1:0] spa, spb; logic s; logic [2*38-1:0] pr; logic st; integer k;
    na = m1_norm(a); nb = m1_norm(b);
    spa = na[49:49-1]; spb = nb[49:49-1]; s = na[49-2] ^ nb[49-2];
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
      m1_mul = m1_mkx(2'd0, s, na[38+8:38+1] + nb[38+8:38+1] + 38, pr[2*38-1:38], st);
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
  function automatic [2*38+8+2:0] m1_mulx(input [49:0] a, input [49:0] b);
    logic [49:0] na, nb; logic [1:0] spa, spb, sp; logic s; logic [2*38-1:0] pr;
    na = m1_norm(a); nb = m1_norm(b);
    pr = na[38:1] * nb[38:1];
    spa = na[49:49-1]; spb = nb[49:49-1]; s = na[49-2] ^ nb[49-2];
    if (spa == 2'd1 || spb == 2'd1) sp = 2'd1;
    else if (spa == 2'd2 || spb == 2'd2)
      sp = ((spa == 2'd0 && na[38:1] == 0) || (spb == 2'd0 && nb[38:1] == 0)) ? 2'd1 : 2'd2;
    else sp = 2'd0;
    m1_mulx = {sp, s, na[38+8:38+1] + nb[38+8:38+1], pr};
  endfunction
  function automatic [49:0] m1_div(input [49:0] a, input [49:0] b);
    logic [49:0] na, nb; logic [1:0] spa, spb; logic s; logic [2*38+1:0] qr; logic [38:0] q, r;
    na = m1_norm(a); nb = m1_norm(b);
    spa = na[49:49-1]; spb = nb[49:49-1]; s = na[49-2] ^ nb[49-2];
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
      if (q[38]) m1_div = m1_mkx(2'd0, s, na[38+8:38+1] - nb[38+8:38+1] - 38 + 1, q[38:1], (r != 0) | q[0] | na[0] | nb[0]);
      else m1_div = m1_mkx(2'd0, s, na[38+8:38+1] - nb[38+8:38+1] - 38, q[37:0], (r != 0) | na[0] | nb[0]);
    end
  endfunction
  function automatic [49:0] m1_sqrt(input [49:0] a);
    logic [49:0] na; logic [1:0] spa; logic signed [7:0] e; logic [38:0] m; logic [2*38+3:0] rad;
    logic [38+2:0] rem, trial; logic [38:0] root; logic ge; integer i;
    na = m1_norm(a); spa = na[49:49-1];
    if (spa == 2'd1) m1_sqrt = m1_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m1_sqrt = na[49-2] ? m1_mkx(2'd1, 1'b0, 0, 0, 1'b0) : na;
    else if (na[38:1] == 0 && !na[0]) m1_sqrt = na;
    else if (na[49-2]) m1_sqrt = m1_mkx(2'd1, 1'b0, 0, 0, 1'b0);
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
      m1_sqrt = m1_mkx(2'd0, 1'b0, (e >>> 1) - 19 + 1, root[38:1], (rem != 0) | root[0] | na[0]);
    end
  endfunction
  // X ordering treats NaN as unordered and compares finite values by sign and magnitude
  function automatic m1_lt(input [49:0] a, input [49:0] b);
    logic [49:0] na, nb; logic za, zb, sa, sb, mag_lt; logic signed [7:0] ea, eb;
    na = m1_norm(a); nb = m1_norm(b);
    za = (na[38:1] == 0) && !na[0]; zb = (nb[38:1] == 0) && !nb[0];
    sa = na[49-2] && !za; sb = nb[49-2] && !zb;
    if (na[49:49-1] == 2'd1 || nb[49:49-1] == 2'd1) m1_lt = 1'b0;
    else if (na[49:49-1] == 2'd2 || nb[49:49-1] == 2'd2) begin
      if (na[49:49-1] == 2'd2 && nb[49:49-1] == 2'd2) m1_lt = na[49-2] && !nb[49-2];
      else if (na[49:49-1] == 2'd2) m1_lt = na[49-2];
      else m1_lt = !nb[49-2];
    end else if (za && zb) m1_lt = 1'b0;
    else if (sa != sb) m1_lt = sa;
    else begin
      ea = na[38+8:38+1]; eb = nb[38+8:38+1];
      if (za) mag_lt = 1'b1; else if (zb) mag_lt = 1'b0;
      else mag_lt = (ea < eb) || (ea == eb && (na[38:1] < nb[38:1] || (na[38:1] == nb[38:1] && !na[0] && nb[0])));
      m1_lt = sa ? !mag_lt && !(za && zb) && !m1_eq(na, nb) : mag_lt;
    end
  endfunction
  function automatic m1_eq(input [49:0] a, input [49:0] b);
    logic [49:0] na, nb; logic za, zb;
    na = m1_norm(a); nb = m1_norm(b);
    za = (na[38:1] == 0) && !na[0]; zb = (nb[38:1] == 0) && !nb[0];
    if (na[49:49-1] == 2'd1 || nb[49:49-1] == 2'd1) m1_eq = 1'b0;
    else if (na[49:49-1] == 2'd2 || nb[49:49-1] == 2'd2)
      m1_eq = (na[49:49-1] == nb[49:49-1]) && (na[49-2] == nb[49-2]);
    else if (za || zb) m1_eq = za && zb;
    else m1_eq = (na[49-2] == nb[49-2]) && (na[38+8:38+1] == nb[38+8:38+1]) && (na[38:1] == nb[38:1]) && (na[0] == nb[0]);
  endfunction

  function automatic [28:0] m1_unpack_s(input [15:0] b, input daz);
    logic s; logic [15:0] mag; integer i;
    s = 1'b0; mag = b;
    m1_unpack_s = {1'b0, m1_mkv(2'd0, s && (mag != 0), -0, {{(17-16){1'b0}}, mag})};
  endfunction

  function automatic [15:0] m1_enc(input signed [34:0] v); m1_enc = v[15:0]; endfunction
  function automatic [15:0] m1_wrap(input signed [34:0] v); m1_wrap = v[15:0]; endfunction
  function automatic [15:0] m1_sat(input signed [34:0] v);
    m1_sat = (v > 35'sd65535) ? {16{1'b1}} : (v < 0) ? 16'd0 : v[15:0];
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

  // ---- m2: V = {special[1:0], sign, exp[8] (signed), sig[9]}
  //           X = {special[1:0], sign, exp[8] (signed), sig[22], sticky}
  localparam int m2_SW = 9, m2_EW = 8, m2_XW = 22;
  localparam int m2_VW = 20, m2_XT = 34;
  function automatic [19:0] m2_mkv(input [1:0] sp, input s, input signed [7:0] e, input [8:0] sig);
    m2_mkv = {sp, s, e, sig};
  endfunction
  function automatic [33:0] m2_mkx(input [1:0] sp, input s, input signed [7:0] e, input [21:0] sig, input st);
    m2_mkx = {sp, s, e, sig, st};
  endfunction
  function automatic [33:0] m2_x(input [19:0] v);   // widen V to X
    m2_x = {v[19:19-1], v[19-2], v[19-3 -: 8], {{(22-9){1'b0}}, v[8:0]}, 1'b0};
  endfunction
  // normalize: leading one at bit XW-1 (zero stays zero)
  function automatic [33:0] m2_norm(input [33:0] x);
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
    m2_norm = {x[33:33-1], x[33-2], e, s, x[0]};
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
  function automatic [33:0] m2_add(input [33:0] a, input [33:0] b, input sub);
    logic [33:0] na, nb, big, sml; logic [1:0] spa, spb; logic sa, sb, sr, sw;
    logic signed [7:0] ea, eb, d; logic [22:0] ms, mb, r; logic st, stb; integer sh;
    na = m2_norm(a); nb = m2_norm(b);
    spa = na[33:33-1]; spb = nb[33:33-1];
    sa = na[33-2]; sb = nb[33-2] ^ sub;
    if (spa == 2'd1 || spb == 2'd1) m2_add = m2_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 && spb == 2'd2) m2_add = (sa == sb) ? m2_mkx(2'd2, sa, 0, 0, 1'b0) : m2_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m2_add = m2_mkx(2'd2, sa, 0, 0, 1'b0);
    else if (spb == 2'd2) m2_add = m2_mkx(2'd2, sb, 0, 0, 1'b0);
    else if (na[22:1] == 0 && !na[0]) m2_add = {nb[33:33-1], sb, nb[33-3:0]};
    else if (nb[22:1] == 0 && !nb[0]) m2_add = na;
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
      if (r[22]) begin st = st | r[0]; r = r >> 1; m2_add = m2_mkx(2'd0, sr, big[22+8:22+1] + 1, r[21:0], st); end
      else m2_add = m2_mkx(2'd0, sr, big[22+8:22+1], r[21:0], st);
    end
  endfunction
  function automatic [33:0] m2_mul(input [33:0] a, input [33:0] b);
    logic [33:0] na, nb; logic [1:0] spa, spb; logic s; logic [2*22-1:0] pr; logic st; integer k;
    na = m2_norm(a); nb = m2_norm(b);
    spa = na[33:33-1]; spb = nb[33:33-1]; s = na[33-2] ^ nb[33-2];
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
      m2_mul = m2_mkx(2'd0, s, na[22+8:22+1] + nb[22+8:22+1] + 22, pr[2*22-1:22], st);
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
  function automatic [2*22+8+2:0] m2_mulx(input [33:0] a, input [33:0] b);
    logic [33:0] na, nb; logic [1:0] spa, spb, sp; logic s; logic [2*22-1:0] pr;
    na = m2_norm(a); nb = m2_norm(b);
    pr = na[22:1] * nb[22:1];
    spa = na[33:33-1]; spb = nb[33:33-1]; s = na[33-2] ^ nb[33-2];
    if (spa == 2'd1 || spb == 2'd1) sp = 2'd1;
    else if (spa == 2'd2 || spb == 2'd2)
      sp = ((spa == 2'd0 && na[22:1] == 0) || (spb == 2'd0 && nb[22:1] == 0)) ? 2'd1 : 2'd2;
    else sp = 2'd0;
    m2_mulx = {sp, s, na[22+8:22+1] + nb[22+8:22+1], pr};
  endfunction
  function automatic [33:0] m2_div(input [33:0] a, input [33:0] b);
    logic [33:0] na, nb; logic [1:0] spa, spb; logic s; logic [2*22+1:0] qr; logic [22:0] q, r;
    na = m2_norm(a); nb = m2_norm(b);
    spa = na[33:33-1]; spb = nb[33:33-1]; s = na[33-2] ^ nb[33-2];
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
      if (q[22]) m2_div = m2_mkx(2'd0, s, na[22+8:22+1] - nb[22+8:22+1] - 22 + 1, q[22:1], (r != 0) | q[0] | na[0] | nb[0]);
      else m2_div = m2_mkx(2'd0, s, na[22+8:22+1] - nb[22+8:22+1] - 22, q[21:0], (r != 0) | na[0] | nb[0]);
    end
  endfunction
  function automatic [33:0] m2_sqrt(input [33:0] a);
    logic [33:0] na; logic [1:0] spa; logic signed [7:0] e; logic [22:0] m; logic [2*22+3:0] rad;
    logic [22+2:0] rem, trial; logic [22:0] root; logic ge; integer i;
    na = m2_norm(a); spa = na[33:33-1];
    if (spa == 2'd1) m2_sqrt = m2_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m2_sqrt = na[33-2] ? m2_mkx(2'd1, 1'b0, 0, 0, 1'b0) : na;
    else if (na[22:1] == 0 && !na[0]) m2_sqrt = na;
    else if (na[33-2]) m2_sqrt = m2_mkx(2'd1, 1'b0, 0, 0, 1'b0);
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
      m2_sqrt = m2_mkx(2'd0, 1'b0, (e >>> 1) - 11 + 1, root[22:1], (rem != 0) | root[0] | na[0]);
    end
  endfunction
  // X ordering treats NaN as unordered and compares finite values by sign and magnitude
  function automatic m2_lt(input [33:0] a, input [33:0] b);
    logic [33:0] na, nb; logic za, zb, sa, sb, mag_lt; logic signed [7:0] ea, eb;
    na = m2_norm(a); nb = m2_norm(b);
    za = (na[22:1] == 0) && !na[0]; zb = (nb[22:1] == 0) && !nb[0];
    sa = na[33-2] && !za; sb = nb[33-2] && !zb;
    if (na[33:33-1] == 2'd1 || nb[33:33-1] == 2'd1) m2_lt = 1'b0;
    else if (na[33:33-1] == 2'd2 || nb[33:33-1] == 2'd2) begin
      if (na[33:33-1] == 2'd2 && nb[33:33-1] == 2'd2) m2_lt = na[33-2] && !nb[33-2];
      else if (na[33:33-1] == 2'd2) m2_lt = na[33-2];
      else m2_lt = !nb[33-2];
    end else if (za && zb) m2_lt = 1'b0;
    else if (sa != sb) m2_lt = sa;
    else begin
      ea = na[22+8:22+1]; eb = nb[22+8:22+1];
      if (za) mag_lt = 1'b1; else if (zb) mag_lt = 1'b0;
      else mag_lt = (ea < eb) || (ea == eb && (na[22:1] < nb[22:1] || (na[22:1] == nb[22:1] && !na[0] && nb[0])));
      m2_lt = sa ? !mag_lt && !(za && zb) && !m2_eq(na, nb) : mag_lt;
    end
  endfunction
  function automatic m2_eq(input [33:0] a, input [33:0] b);
    logic [33:0] na, nb; logic za, zb;
    na = m2_norm(a); nb = m2_norm(b);
    za = (na[22:1] == 0) && !na[0]; zb = (nb[22:1] == 0) && !nb[0];
    if (na[33:33-1] == 2'd1 || nb[33:33-1] == 2'd1) m2_eq = 1'b0;
    else if (na[33:33-1] == 2'd2 || nb[33:33-1] == 2'd2)
      m2_eq = (na[33:33-1] == nb[33:33-1]) && (na[33-2] == nb[33-2]);
    else if (za || zb) m2_eq = za && zb;
    else m2_eq = (na[33-2] == nb[33-2]) && (na[22+8:22+1] == nb[22+8:22+1]) && (na[22:1] == nb[22:1]) && (na[0] == nb[0]);
  endfunction

  function automatic [20:0] m2_unpack_s(input [7:0] b, input daz);
    logic s; logic [7:0] mag; integer i;
    s = b[7]; mag = s ? (~b + 1'b1) : b;
    m2_unpack_s = {1'b0, m2_mkv(2'd0, s && (mag != 0), -0, {{(9-8){1'b0}}, mag})};
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
module alu_core (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [4:0] op,
  input  logic [1:0] mode,
  output logic [15:0] y,
  output logic [3:0] flags
);
  // alu_core: behavioral reference derived from the instance (modes 1xint16_twos_complement, 1xint16_unsigned, 2xint8_twos_complement; ops add, sub, adc, neg, abs, add_sat, mul, mul_high, min, max, cmp, shl, shr_arith, rol, and, or, xor, not, popcount, clz, ctz). Every (mode, op) pair computes the verify layer's exact semantics.
  logic [2:0] rnd_sel;
  logic [2:0] rnd;
  logic daz;
  logic ftz;
  logic dual;
  logic [15:0] y_m0_m0_l0_adder;
  logic [19:0] fl_m0_m0_l0_adder;
  logic [15:0] y_m0_m0_l0_multiplier;
  logic [19:0] fl_m0_m0_l0_multiplier;
  logic [15:0] y_m0_m0_l0_comparator;
  logic [19:0] fl_m0_m0_l0_comparator;
  logic [15:0] y_m0_m0_l0_shifter;
  logic [19:0] fl_m0_m0_l0_shifter;
  logic [15:0] y_m0_m0_l0_logic;
  logic [19:0] fl_m0_m0_l0_logic;
  logic [15:0] y_m0_m0_l0_bitcount;
  logic [19:0] fl_m0_m0_l0_bitcount;
  logic [15:0] y_m0;
  logic [19:0] fl_m0;
  logic [15:0] y_m1_m1_l0_adder;
  logic [19:0] fl_m1_m1_l0_adder;
  logic [15:0] y_m1_m1_l0_multiplier;
  logic [19:0] fl_m1_m1_l0_multiplier;
  logic [15:0] y_m1_m1_l0_comparator;
  logic [19:0] fl_m1_m1_l0_comparator;
  logic [15:0] y_m1_m1_l0_shifter;
  logic [19:0] fl_m1_m1_l0_shifter;
  logic [15:0] y_m1_m1_l0_logic;
  logic [19:0] fl_m1_m1_l0_logic;
  logic [15:0] y_m1_m1_l0_bitcount;
  logic [19:0] fl_m1_m1_l0_bitcount;
  logic [15:0] y_m1;
  logic [19:0] fl_m1;
  logic [15:0] y_m2_m2_l0_adder;
  logic [19:0] fl_m2_m2_l0_adder;
  logic [15:0] y_m2_m2_l1_adder;
  logic [19:0] fl_m2_m2_l1_adder;
  logic [15:0] y_m2_m2_l0_multiplier;
  logic [19:0] fl_m2_m2_l0_multiplier;
  logic [15:0] y_m2_m2_l1_multiplier;
  logic [19:0] fl_m2_m2_l1_multiplier;
  logic [15:0] y_m2_m2_l0_comparator;
  logic [19:0] fl_m2_m2_l0_comparator;
  logic [15:0] y_m2_m2_l1_comparator;
  logic [19:0] fl_m2_m2_l1_comparator;
  logic [15:0] y_m2_m2_l0_shifter;
  logic [19:0] fl_m2_m2_l0_shifter;
  logic [15:0] y_m2_m2_l1_shifter;
  logic [19:0] fl_m2_m2_l1_shifter;
  logic [15:0] y_m2_m2_l0_logic;
  logic [19:0] fl_m2_m2_l0_logic;
  logic [15:0] y_m2_m2_l1_logic;
  logic [19:0] fl_m2_m2_l1_logic;
  logic [15:0] y_m2_m2_l0_bitcount;
  logic [19:0] fl_m2_m2_l0_bitcount;
  logic [15:0] y_m2_m2_l1_bitcount;
  logic [19:0] fl_m2_m2_l1_bitcount;
  logic [15:0] y_m2;
  logic [19:0] fl_m2;
  logic [19:0] fl_all;
  assign rnd_sel = 3'd0;
  assign rnd = rnd_sel;
  assign daz = 1'b0;
  assign ftz = 1'b0;
  assign dual = 1'b0;
  assign y_m0 = y_m0_m0_l0_adder | y_m0_m0_l0_multiplier | y_m0_m0_l0_comparator | y_m0_m0_l0_shifter | y_m0_m0_l0_logic | y_m0_m0_l0_bitcount;
  assign fl_m0 = fl_m0_m0_l0_adder | fl_m0_m0_l0_multiplier | fl_m0_m0_l0_comparator | fl_m0_m0_l0_shifter | fl_m0_m0_l0_logic | fl_m0_m0_l0_bitcount;
  assign y_m1 = y_m1_m1_l0_adder | y_m1_m1_l0_multiplier | y_m1_m1_l0_comparator | y_m1_m1_l0_shifter | y_m1_m1_l0_logic | y_m1_m1_l0_bitcount;
  assign fl_m1 = fl_m1_m1_l0_adder | fl_m1_m1_l0_multiplier | fl_m1_m1_l0_comparator | fl_m1_m1_l0_shifter | fl_m1_m1_l0_logic | fl_m1_m1_l0_bitcount;
  assign y_m2 = y_m2_m2_l0_adder | y_m2_m2_l1_adder | y_m2_m2_l0_multiplier | y_m2_m2_l1_multiplier | y_m2_m2_l0_comparator | y_m2_m2_l1_comparator | y_m2_m2_l0_shifter | y_m2_m2_l1_shifter | y_m2_m2_l0_logic | y_m2_m2_l1_logic | y_m2_m2_l0_bitcount | y_m2_m2_l1_bitcount;
  assign fl_m2 = fl_m2_m2_l0_adder | fl_m2_m2_l1_adder | fl_m2_m2_l0_multiplier | fl_m2_m2_l1_multiplier | fl_m2_m2_l0_comparator | fl_m2_m2_l1_comparator | fl_m2_m2_l0_shifter | fl_m2_m2_l1_shifter | fl_m2_m2_l0_logic | fl_m2_m2_l1_logic | fl_m2_m2_l0_bitcount | fl_m2_m2_l1_bitcount;
  alu_core_u_m0_l0_adder u_m0_l0_adder (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_m0_l0_adder), .fl_m0(fl_m0_m0_l0_adder));
  alu_core_u_m0_l0_multiplier u_m0_l0_multiplier (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_m0_l0_multiplier), .fl_m0(fl_m0_m0_l0_multiplier));
  alu_core_u_m0_l0_comparator u_m0_l0_comparator (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_m0_l0_comparator), .fl_m0(fl_m0_m0_l0_comparator));
  alu_core_u_m0_l0_shifter u_m0_l0_shifter (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_m0_l0_shifter), .fl_m0(fl_m0_m0_l0_shifter));
  alu_core_u_m0_l0_logic u_m0_l0_logic (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_m0_l0_logic), .fl_m0(fl_m0_m0_l0_logic));
  alu_core_u_m0_l0_bitcount u_m0_l0_bitcount (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_m0_l0_bitcount), .fl_m0(fl_m0_m0_l0_bitcount));
  alu_core_u_m1_l0_adder u_m1_l0_adder (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l0_adder), .fl_m1(fl_m1_m1_l0_adder));
  alu_core_u_m1_l0_multiplier u_m1_l0_multiplier (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l0_multiplier), .fl_m1(fl_m1_m1_l0_multiplier));
  alu_core_u_m1_l0_comparator u_m1_l0_comparator (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l0_comparator), .fl_m1(fl_m1_m1_l0_comparator));
  alu_core_u_m1_l0_shifter u_m1_l0_shifter (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l0_shifter), .fl_m1(fl_m1_m1_l0_shifter));
  alu_core_u_m1_l0_logic u_m1_l0_logic (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l0_logic), .fl_m1(fl_m1_m1_l0_logic));
  alu_core_u_m1_l0_bitcount u_m1_l0_bitcount (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l0_bitcount), .fl_m1(fl_m1_m1_l0_bitcount));
  alu_core_u_m2_l0_adder u_m2_l0_adder (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_m2_l0_adder), .fl_m2(fl_m2_m2_l0_adder));
  alu_core_u_m2_l1_adder u_m2_l1_adder (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_m2_l1_adder), .fl_m2(fl_m2_m2_l1_adder));
  alu_core_u_m2_l0_multiplier u_m2_l0_multiplier (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_m2_l0_multiplier), .fl_m2(fl_m2_m2_l0_multiplier));
  alu_core_u_m2_l1_multiplier u_m2_l1_multiplier (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_m2_l1_multiplier), .fl_m2(fl_m2_m2_l1_multiplier));
  alu_core_u_m2_l0_comparator u_m2_l0_comparator (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_m2_l0_comparator), .fl_m2(fl_m2_m2_l0_comparator));
  alu_core_u_m2_l1_comparator u_m2_l1_comparator (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_m2_l1_comparator), .fl_m2(fl_m2_m2_l1_comparator));
  alu_core_u_m2_l0_shifter u_m2_l0_shifter (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_m2_l0_shifter), .fl_m2(fl_m2_m2_l0_shifter));
  alu_core_u_m2_l1_shifter u_m2_l1_shifter (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_m2_l1_shifter), .fl_m2(fl_m2_m2_l1_shifter));
  alu_core_u_m2_l0_logic u_m2_l0_logic (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_m2_l0_logic), .fl_m2(fl_m2_m2_l0_logic));
  alu_core_u_m2_l1_logic u_m2_l1_logic (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_m2_l1_logic), .fl_m2(fl_m2_m2_l1_logic));
  alu_core_u_m2_l0_bitcount u_m2_l0_bitcount (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_m2_l0_bitcount), .fl_m2(fl_m2_m2_l0_bitcount));
  alu_core_u_m2_l1_bitcount u_m2_l1_bitcount (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_m2_l1_bitcount), .fl_m2(fl_m2_m2_l1_bitcount));
  always_comb begin
    case (mode)
      2'd0: begin y = y_m0; fl_all = fl_m0; end
      2'd1: begin y = y_m1; fl_all = fl_m1; end
      2'd2: begin y = y_m2; fl_all = fl_m2; end
      default: begin y = '0; fl_all = '0; end
    endcase
  end
  assign flags[0] = fl_all[7];
  assign flags[1] = fl_all[8];
  assign flags[2] = fl_all[17];
  assign flags[3] = fl_all[18];
endmodule

module alu_core_m0_adder_sh #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [4:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m0,
  output logic [19:0] fl_m0,
  output logic [15:0] pc_a_m0,
  output logic [15:0] pc_b_m0,
  output logic [0:0] pc_cin_m0,
  input  logic [15:0] pc_s_m0,
  input  logic [0:0] pc_co_m0
);
  // alu_core_m0_adder_sh: lane LANE of mode 0 (int16_twos_complement) for the adder ops add, sub, adc, neg, abs, add_sat; the result buses are the mode's, with only this lane's bits written; the unit's shared adder serve this lane through the pc_/tp_ buses
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
  logic signed [34:0] m0_o1ex0_LANE;
  logic signed [34:0] m0_o2ex0_LANE;
  logic signed [34:0] m0_o3ex0_LANE;
  logic signed [34:0] m0_o4ex0_LANE;
  logic signed [34:0] m0_o5ex0_LANE;
  assign m0_aLANE = a[(LANE*16) +: 16];
  assign m0_bLANE = b[(LANE*16) +: 16];
  assign m0_xa[LANE] = m0_x(m0_unpack_s(m0_aLANE, 1'b0));
  assign m0_xb[LANE] = m0_x(m0_unpack_s(m0_bLANE, 1'b0));
  assign m0_vaLANE = {m0_aLANE[15], m0_aLANE};
  assign m0_vbLANE = {m0_bLANE[15], m0_bLANE};
  assign m0_add_sLANE = pc_s_m0[(LANE)*16 +: 16];
  assign m0_add_coutLANE = pc_co_m0[(LANE+1)*1-1];
  always_comb begin
    y_m0 = '0; d_m0 = '0; fl_m0 = '0;
    m0_o0ex0_LANE = 'x; m0_o1ex0_LANE = 'x; m0_o2ex0_LANE = 'x; m0_o3ex0_LANE = 'x; m0_o4ex0_LANE = 'x; m0_o5ex0_LANE = 'x;
    pc_a_m0 = '0; pc_b_m0 = '0; pc_cin_m0 = '0;
    case (op)
      5'd0: begin
        pc_a_m0[(LANE)*16 +: 16] = m0_aLANE; pc_b_m0[(LANE)*16 +: 16] = m0_bLANE; pc_cin_m0[(LANE)*1] = 1'b0;
        m0_o0ex0_LANE = $signed({(m0_aLANE[15] ^ m0_bLANE[15] ^ m0_add_coutLANE), m0_add_sLANE});
        y_m0[((LANE*16)+0) +: 16] = m0_wrap(m0_o0ex0_LANE);
        fl_m0[(0+LANE)*10 +: 10] = (((m0_aLANE[15] ^ m0_bLANE[15] ^ m0_add_coutLANE) ^ m0_add_sLANE[15]) ? (10'd1 << 8) : 10'd0) | (((m0_aLANE[15] ^ m0_bLANE[15] ^ m0_add_coutLANE) ^ m0_add_sLANE[15]) ? (10'd1 << 2) : 10'd0) | (m0_add_coutLANE ? (10'd1 << 7) : 10'd0);
      end
      5'd1: begin
        pc_a_m0[(LANE)*16 +: 16] = m0_aLANE; pc_b_m0[(LANE)*16 +: 16] = ~m0_bLANE; pc_cin_m0[(LANE)*1] = 1'b1;
        m0_o1ex0_LANE = $signed({(m0_aLANE[15] ^ ~m0_bLANE[15] ^ m0_add_coutLANE), m0_add_sLANE});
        y_m0[((LANE*16)+0) +: 16] = m0_wrap(m0_o1ex0_LANE);
        fl_m0[(0+LANE)*10 +: 10] = (((m0_aLANE[15] ^ ~m0_bLANE[15] ^ m0_add_coutLANE) ^ m0_add_sLANE[15]) ? (10'd1 << 8) : 10'd0) | (((m0_aLANE[15] ^ ~m0_bLANE[15] ^ m0_add_coutLANE) ^ m0_add_sLANE[15]) ? (10'd1 << 2) : 10'd0) | (~m0_add_coutLANE ? (10'd1 << 7) : 10'd0);
      end
      5'd2: begin
        pc_a_m0[(LANE)*16 +: 16] = m0_aLANE; pc_b_m0[(LANE)*16 +: 16] = m0_bLANE; pc_cin_m0[(LANE)*1] = 1'b1;
        m0_o2ex0_LANE = $signed({(m0_aLANE[15] ^ m0_bLANE[15] ^ m0_add_coutLANE), m0_add_sLANE});
        y_m0[((LANE*16)+0) +: 16] = m0_wrap(m0_o2ex0_LANE);
        fl_m0[(0+LANE)*10 +: 10] = (((m0_aLANE[15] ^ m0_bLANE[15] ^ m0_add_coutLANE) ^ m0_add_sLANE[15]) ? (10'd1 << 8) : 10'd0) | (((m0_aLANE[15] ^ m0_bLANE[15] ^ m0_add_coutLANE) ^ m0_add_sLANE[15]) ? (10'd1 << 2) : 10'd0) | (m0_add_coutLANE ? (10'd1 << 7) : 10'd0);
      end
      5'd3: begin
        pc_a_m0[(LANE)*16 +: 16] = 16'd0; pc_b_m0[(LANE)*16 +: 16] = ~m0_aLANE; pc_cin_m0[(LANE)*1] = 1'b1;
        m0_o3ex0_LANE = $signed({(1'b0 ^ ~m0_aLANE[15] ^ m0_add_coutLANE), m0_add_sLANE});
        y_m0[((LANE*16)+0) +: 16] = m0_wrap(m0_o3ex0_LANE);
        fl_m0[(0+LANE)*10 +: 10] = (((1'b0 ^ ~m0_aLANE[15] ^ m0_add_coutLANE) ^ m0_add_sLANE[15]) ? (10'd1 << 8) : 10'd0) | (((1'b0 ^ ~m0_aLANE[15] ^ m0_add_coutLANE) ^ m0_add_sLANE[15]) ? (10'd1 << 2) : 10'd0) | (m0_aLANE != 0 ? (10'd1 << 7) : 10'd0);
      end
      5'd4: begin
        pc_a_m0[(LANE)*16 +: 16] = 16'd0; pc_b_m0[(LANE)*16 +: 16] = ~m0_aLANE; pc_cin_m0[(LANE)*1] = 1'b1;
        m0_o4ex0_LANE = (m0_aLANE[15] ? $signed({(1'b0 ^ ~m0_aLANE[15] ^ m0_add_coutLANE), m0_add_sLANE}) : $signed({1'b0, m0_aLANE}));
        y_m0[((LANE*16)+0) +: 16] = m0_wrap(m0_o4ex0_LANE);
        fl_m0[(0+LANE)*10 +: 10] = ((m0_aLANE[15] & ((1'b0 ^ ~m0_aLANE[15] ^ m0_add_coutLANE) ^ m0_add_sLANE[15])) ? (10'd1 << 8) : 10'd0) | ((m0_aLANE[15] & ((1'b0 ^ ~m0_aLANE[15] ^ m0_add_coutLANE) ^ m0_add_sLANE[15])) ? (10'd1 << 2) : 10'd0);
      end
      5'd5: begin
        pc_a_m0[(LANE)*16 +: 16] = m0_aLANE; pc_b_m0[(LANE)*16 +: 16] = m0_bLANE; pc_cin_m0[(LANE)*1] = 1'b0;
        m0_o5ex0_LANE = $signed({(m0_aLANE[15] ^ m0_bLANE[15] ^ m0_add_coutLANE), m0_add_sLANE});
        y_m0[((LANE*16)+0) +: 16] = m0_sat(m0_o5ex0_LANE);
        fl_m0[(0+LANE)*10 +: 10] = (((m0_aLANE[15] ^ m0_bLANE[15] ^ m0_add_coutLANE) ^ m0_add_sLANE[15]) ? (10'd1 << 8) : 10'd0) | (((m0_aLANE[15] ^ m0_bLANE[15] ^ m0_add_coutLANE) ^ m0_add_sLANE[15]) ? (10'd1 << 2) : 10'd0);
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m0_bitcount #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [4:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m0,
  output logic [19:0] fl_m0
);
  // alu_core_m0_bitcount: lane LANE of mode 0 (int16_twos_complement) for the bitcount ops popcount, clz, ctz; the result buses are the mode's, with only this lane's bits written
  import alu_core_m0_pkg::*;
  logic d_m0;
  logic [15:0] m0_aLANE;
  logic [15:0] m0_bLANE;
  logic [49:0] m0_xa [0:0];
  logic [49:0] m0_xb [0:0];
  logic signed [16:0] m0_vaLANE;
  logic signed [16:0] m0_vbLANE;
  logic [15:0] m0_popcount_aLANE;
  logic [4:0] m0_popcount_nLANE;
  logic signed [34:0] m0_o18ex0_LANE;
  logic signed [34:0] m0_o19ex0_LANE;
  logic signed [34:0] m0_o20ex0_LANE;
  assign m0_aLANE = a[(LANE*16) +: 16];
  assign m0_bLANE = b[(LANE*16) +: 16];
  assign m0_xa[LANE] = m0_x(m0_unpack_s(m0_aLANE, 1'b0));
  assign m0_xb[LANE] = m0_x(m0_unpack_s(m0_bLANE, 1'b0));
  assign m0_vaLANE = {m0_aLANE[15], m0_aLANE};
  assign m0_vbLANE = {m0_bLANE[15], m0_bLANE};
  fam_count_popcount_balanced_tree_full_adder_3_2_ripple_carry_p4180c_w16 u_m0_popcountLANE (.a(m0_popcount_aLANE), .n(m0_popcount_nLANE));
  always_comb begin
    y_m0 = '0; d_m0 = '0; fl_m0 = '0;
    m0_popcount_aLANE = 'x; m0_o18ex0_LANE = 'x; m0_o19ex0_LANE = 'x; m0_o20ex0_LANE = 'x;
    case (op)
      5'd18: begin
        m0_popcount_aLANE = m0_aLANE;
        y_m0[((LANE*16)+0) +: 16] = {{11{1'b0}}, m0_popcount_nLANE};
      end
      5'd19: begin
        y_m0[((LANE*16)+0) +: 16] = m0_aLANE[15] ? 16'd0 : m0_aLANE[14] ? 16'd1 : m0_aLANE[13] ? 16'd2 : m0_aLANE[12] ? 16'd3 : m0_aLANE[11] ? 16'd4 : m0_aLANE[10] ? 16'd5 : m0_aLANE[9] ? 16'd6 : m0_aLANE[8] ? 16'd7 : m0_aLANE[7] ? 16'd8 : m0_aLANE[6] ? 16'd9 : m0_aLANE[5] ? 16'd10 : m0_aLANE[4] ? 16'd11 : m0_aLANE[3] ? 16'd12 : m0_aLANE[2] ? 16'd13 : m0_aLANE[1] ? 16'd14 : m0_aLANE[0] ? 16'd15 : 16'd16;
      end
      5'd20: begin
        y_m0[((LANE*16)+0) +: 16] = m0_aLANE[0] ? 16'd0 : m0_aLANE[1] ? 16'd1 : m0_aLANE[2] ? 16'd2 : m0_aLANE[3] ? 16'd3 : m0_aLANE[4] ? 16'd4 : m0_aLANE[5] ? 16'd5 : m0_aLANE[6] ? 16'd6 : m0_aLANE[7] ? 16'd7 : m0_aLANE[8] ? 16'd8 : m0_aLANE[9] ? 16'd9 : m0_aLANE[10] ? 16'd10 : m0_aLANE[11] ? 16'd11 : m0_aLANE[12] ? 16'd12 : m0_aLANE[13] ? 16'd13 : m0_aLANE[14] ? 16'd14 : m0_aLANE[15] ? 16'd15 : 16'd16;
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m0_comparator #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [4:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m0,
  output logic [19:0] fl_m0
);
  // alu_core_m0_comparator: lane LANE of mode 0 (int16_twos_complement) for the comparator ops min, max, cmp; the result buses are the mode's, with only this lane's bits written
  import alu_core_m0_pkg::*;
  logic d_m0;
  logic [15:0] m0_aLANE;
  logic [15:0] m0_bLANE;
  logic [49:0] m0_xa [0:0];
  logic [49:0] m0_xb [0:0];
  logic signed [16:0] m0_vaLANE;
  logic signed [16:0] m0_vbLANE;
  logic [15:0] m0_cmp_aLANE;
  logic [15:0] m0_cmp_bLANE;
  logic m0_cmp_ltLANE;
  logic m0_cmp_eqLANE;
  logic signed [34:0] m0_o8ex0_LANE;
  logic signed [34:0] m0_o9ex0_LANE;
  logic signed [34:0] m0_o10ex0_LANE;
  assign m0_aLANE = a[(LANE*16) +: 16];
  assign m0_bLANE = b[(LANE*16) +: 16];
  assign m0_xa[LANE] = m0_x(m0_unpack_s(m0_aLANE, 1'b0));
  assign m0_xb[LANE] = m0_x(m0_unpack_s(m0_bLANE, 1'b0));
  assign m0_vaLANE = {m0_aLANE[15], m0_aLANE};
  assign m0_vbLANE = {m0_bLANE[15], m0_bLANE};
  fam_cmp_prefix_comparator #(.W(16), .SIGNED(1), .STRUCTURE(0), .RADIX(2)) u_m0_cmpLANE (.a(m0_cmp_aLANE), .b(m0_cmp_bLANE), .lt(m0_cmp_ltLANE), .eq(m0_cmp_eqLANE));
  always_comb begin
    y_m0 = '0; d_m0 = '0; fl_m0 = '0;
    m0_cmp_aLANE = 'x; m0_cmp_bLANE = 'x; m0_o8ex0_LANE = 'x; m0_o9ex0_LANE = 'x; m0_o10ex0_LANE = 'x;
    case (op)
      5'd8: begin
        m0_cmp_aLANE = m0_aLANE; m0_cmp_bLANE = m0_bLANE;
        y_m0[((LANE*16)+0) +: 16] = (m0_cmp_ltLANE | m0_cmp_eqLANE) ? m0_aLANE : m0_bLANE;
      end
      5'd9: begin
        m0_cmp_aLANE = m0_aLANE; m0_cmp_bLANE = m0_bLANE;
        y_m0[((LANE*16)+0) +: 16] = (~m0_cmp_ltLANE) ? m0_aLANE : m0_bLANE;
      end
      5'd10: begin
        m0_cmp_aLANE = m0_aLANE; m0_cmp_bLANE = m0_bLANE;
        y_m0[((LANE*16)+0) +: 16] = {{13{1'b0}}, (~m0_cmp_ltLANE & ~m0_cmp_eqLANE), m0_cmp_eqLANE, m0_cmp_ltLANE};
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m0_logic #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [4:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m0,
  output logic [19:0] fl_m0
);
  // alu_core_m0_logic: lane LANE of mode 0 (int16_twos_complement) for the logic ops and, or, xor, not; the result buses are the mode's, with only this lane's bits written
  import alu_core_m0_pkg::*;
  logic d_m0;
  logic [15:0] m0_aLANE;
  logic [15:0] m0_bLANE;
  logic [49:0] m0_xa [0:0];
  logic [49:0] m0_xb [0:0];
  logic signed [16:0] m0_vaLANE;
  logic signed [16:0] m0_vbLANE;
  logic [15:0] m0_lg_aLANE;
  logic [15:0] m0_lg_bLANE;
  logic [1:0] m0_lg_opLANE;
  logic [15:0] m0_lg_yLANE;
  logic signed [34:0] m0_o14ex0_LANE;
  logic signed [34:0] m0_o15ex0_LANE;
  logic signed [34:0] m0_o16ex0_LANE;
  logic signed [34:0] m0_o17ex0_LANE;
  assign m0_aLANE = a[(LANE*16) +: 16];
  assign m0_bLANE = b[(LANE*16) +: 16];
  assign m0_xa[LANE] = m0_x(m0_unpack_s(m0_aLANE, 1'b0));
  assign m0_xb[LANE] = m0_x(m0_unpack_s(m0_bLANE, 1'b0));
  assign m0_vaLANE = {m0_aLANE[15], m0_aLANE};
  assign m0_vbLANE = {m0_bLANE[15], m0_bLANE};
  fam_logic_gate_row #(.W(16), .NOT_VIA_XOR(0)) u_m0_logicLANE (.a(m0_lg_aLANE), .b(m0_lg_bLANE), .op(m0_lg_opLANE), .y(m0_lg_yLANE));
  always_comb begin
    y_m0 = '0; d_m0 = '0; fl_m0 = '0;
    m0_lg_aLANE = 'x; m0_lg_bLANE = 'x; m0_lg_opLANE = 'x; m0_o14ex0_LANE = 'x; m0_o15ex0_LANE = 'x; m0_o16ex0_LANE = 'x;
    m0_o17ex0_LANE = 'x;
    case (op)
      5'd14: begin
        m0_lg_aLANE = m0_aLANE; m0_lg_bLANE = m0_bLANE; m0_lg_opLANE = 2'd0;
        y_m0[((LANE*16)+0) +: 16] = m0_lg_yLANE;
      end
      5'd15: begin
        m0_lg_aLANE = m0_aLANE; m0_lg_bLANE = m0_bLANE; m0_lg_opLANE = 2'd1;
        y_m0[((LANE*16)+0) +: 16] = m0_lg_yLANE;
      end
      5'd16: begin
        m0_lg_aLANE = m0_aLANE; m0_lg_bLANE = m0_bLANE; m0_lg_opLANE = 2'd2;
        y_m0[((LANE*16)+0) +: 16] = m0_lg_yLANE;
      end
      5'd17: begin
        m0_lg_aLANE = m0_aLANE; m0_lg_bLANE = m0_bLANE; m0_lg_opLANE = 2'd3;
        y_m0[((LANE*16)+0) +: 16] = m0_lg_yLANE;
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m0_multiplier #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [4:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m0,
  output logic [19:0] fl_m0
);
  // alu_core_m0_multiplier: lane LANE of mode 0 (int16_twos_complement) for the multiplier ops mul, mul_high; the result buses are the mode's, with only this lane's bits written
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
  logic signed [34:0] m0_o6ex0_LANE;
  logic signed [34:0] m0_o7ex0_LANE;
  assign m0_aLANE = a[(LANE*16) +: 16];
  assign m0_bLANE = b[(LANE*16) +: 16];
  assign m0_xa[LANE] = m0_x(m0_unpack_s(m0_aLANE, 1'b0));
  assign m0_xb[LANE] = m0_x(m0_unpack_s(m0_bLANE, 1'b0));
  assign m0_vaLANE = {m0_aLANE[15], m0_aLANE};
  assign m0_vbLANE = {m0_bLANE[15], m0_bLANE};
  fam_mul_behavioral_star_w16_s u_m0_mulLANE (.a(m0_mul_aLANE), .b(m0_mul_bLANE), .p(m0_mul_pLANE));
  always_comb begin
    y_m0 = '0; d_m0 = '0; fl_m0 = '0;
    m0_mul_aLANE = 'x; m0_mul_bLANE = 'x; m0_o6ex0_LANE = 'x; m0_o7ex0_LANE = 'x;
    case (op)
      5'd6: begin
        m0_mul_aLANE = m0_aLANE; m0_mul_bLANE = m0_bLANE;
        m0_o6ex0_LANE = $signed({{3{m0_mul_pLANE[31]}}, m0_mul_pLANE});
        y_m0[((LANE*16)+0) +: 16] = m0_wrap(m0_o6ex0_LANE);
        fl_m0[(0+LANE)*10 +: 10] = (m0_o6ex0_LANE > 35'sd32767 || m0_o6ex0_LANE < -35'sd32768 ? (10'd1 << 8) : 10'd0) | (m0_o6ex0_LANE > 35'sd32767 || m0_o6ex0_LANE < -35'sd32768 ? (10'd1 << 2) : 10'd0);
      end
      5'd7: begin
        m0_mul_aLANE = m0_aLANE; m0_mul_bLANE = m0_bLANE;
        m0_o7ex0_LANE = $signed({{3{m0_mul_pLANE[31]}}, m0_mul_pLANE});
        y_m0[((LANE*16)+0) +: 16] = m0_wrap(m0_o7ex0_LANE >>> 16);
        fl_m0[(0+LANE)*10 +: 10] = (m0_o7ex0_LANE > 35'sd32767 || m0_o7ex0_LANE < -35'sd32768 ? (10'd1 << 8) : 10'd0) | (m0_o7ex0_LANE > 35'sd32767 || m0_o7ex0_LANE < -35'sd32768 ? (10'd1 << 2) : 10'd0);
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m0_shifter #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [4:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m0,
  output logic [19:0] fl_m0
);
  // alu_core_m0_shifter: lane LANE of mode 0 (int16_twos_complement) for the shifter ops shl, shr_arith, rol; the result buses are the mode's, with only this lane's bits written
  import alu_core_m0_pkg::*;
  logic d_m0;
  logic [15:0] m0_aLANE;
  logic [15:0] m0_bLANE;
  logic [49:0] m0_xa [0:0];
  logic [49:0] m0_xb [0:0];
  logic signed [16:0] m0_vaLANE;
  logic signed [16:0] m0_vbLANE;
  logic [15:0] m0_sh_aLANE;
  logic [3:0] m0_sh_amtLANE;
  logic [2:0] m0_sh_opLANE;
  logic [15:0] m0_sh_yLANE;
  logic signed [34:0] m0_o11ex0_LANE;
  logic signed [34:0] m0_o12ex0_LANE;
  logic signed [34:0] m0_o13ex0_LANE;
  assign m0_aLANE = a[(LANE*16) +: 16];
  assign m0_bLANE = b[(LANE*16) +: 16];
  assign m0_xa[LANE] = m0_x(m0_unpack_s(m0_aLANE, 1'b0));
  assign m0_xb[LANE] = m0_x(m0_unpack_s(m0_bLANE, 1'b0));
  assign m0_vaLANE = {m0_aLANE[15], m0_aLANE};
  assign m0_vbLANE = {m0_bLANE[15], m0_bLANE};
  fam_shift_barrel_mux_tree #(.W(16), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u_m0_shifterLANE (.a(m0_sh_aLANE), .amt(m0_sh_amtLANE), .op(m0_sh_opLANE), .y(m0_sh_yLANE), .sticky());
  always_comb begin
    y_m0 = '0; d_m0 = '0; fl_m0 = '0;
    m0_sh_aLANE = 'x; m0_sh_amtLANE = 'x; m0_sh_opLANE = 'x; m0_o11ex0_LANE = 'x; m0_o12ex0_LANE = 'x; m0_o13ex0_LANE = 'x;
    case (op)
      5'd11: begin
        m0_sh_aLANE = m0_aLANE; m0_sh_amtLANE = 4'(m0_bLANE % 16'd16); m0_sh_opLANE = 3'd0;
        y_m0[((LANE*16)+0) +: 16] = m0_sh_yLANE;
      end
      5'd12: begin
        m0_sh_aLANE = m0_aLANE; m0_sh_amtLANE = 4'(m0_bLANE % 16'd16); m0_sh_opLANE = 3'd2;
        y_m0[((LANE*16)+0) +: 16] = m0_sh_yLANE;
      end
      5'd13: begin
        m0_sh_aLANE = m0_aLANE; m0_sh_amtLANE = 4'(m0_bLANE % 16'd16); m0_sh_opLANE = 3'd3;
        y_m0[((LANE*16)+0) +: 16] = m0_sh_yLANE;
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m1_adder_sh #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [4:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m1,
  output logic [19:0] fl_m1,
  output logic [15:0] pc_a_m1,
  output logic [15:0] pc_b_m1,
  output logic [0:0] pc_cin_m1,
  input  logic [15:0] pc_s_m1,
  input  logic [0:0] pc_co_m1
);
  // alu_core_m1_adder_sh: lane LANE of mode 1 (int16_unsigned) for the adder ops add, sub, adc, neg, abs, add_sat; the result buses are the mode's, with only this lane's bits written; the unit's shared adder serve this lane through the pc_/tp_ buses
  import alu_core_m1_pkg::*;
  logic d_m1;
  logic [15:0] m1_aLANE;
  logic [15:0] m1_bLANE;
  logic [49:0] m1_xa [0:0];
  logic [49:0] m1_xb [0:0];
  logic signed [16:0] m1_vaLANE;
  logic signed [16:0] m1_vbLANE;
  logic [15:0] m1_add_sLANE;
  logic m1_add_coutLANE;
  logic signed [34:0] m1_o0ex0_LANE;
  logic signed [34:0] m1_o1ex0_LANE;
  logic signed [34:0] m1_o2ex0_LANE;
  logic signed [34:0] m1_o3ex0_LANE;
  logic signed [34:0] m1_o4ex0_LANE;
  logic signed [34:0] m1_o4sx0_LANE;
  logic signed [34:0] m1_o5ex0_LANE;
  assign m1_aLANE = a[(LANE*16) +: 16];
  assign m1_bLANE = b[(LANE*16) +: 16];
  assign m1_xa[LANE] = m1_x(m1_unpack_s(m1_aLANE, 1'b0));
  assign m1_xb[LANE] = m1_x(m1_unpack_s(m1_bLANE, 1'b0));
  assign m1_vaLANE = {1'b0, m1_aLANE};
  assign m1_vbLANE = {1'b0, m1_bLANE};
  assign m1_add_sLANE = pc_s_m1[(LANE)*16 +: 16];
  assign m1_add_coutLANE = pc_co_m1[(LANE+1)*1-1];
  always_comb begin
    y_m1 = '0; d_m1 = '0; fl_m1 = '0;
    m1_o0ex0_LANE = 'x; m1_o1ex0_LANE = 'x; m1_o2ex0_LANE = 'x; m1_o3ex0_LANE = 'x; m1_o4ex0_LANE = 'x; m1_o4sx0_LANE = 'x;
    m1_o5ex0_LANE = 'x;
    pc_a_m1 = '0; pc_b_m1 = '0; pc_cin_m1 = '0;
    case (op)
      5'd0: begin
        pc_a_m1[(LANE)*16 +: 16] = m1_aLANE; pc_b_m1[(LANE)*16 +: 16] = m1_bLANE; pc_cin_m1[(LANE)*1] = 1'b0;
        m1_o0ex0_LANE = $signed({1'b0, m1_add_coutLANE, m1_add_sLANE});
        y_m1[((LANE*16)+0) +: 16] = m1_wrap(m1_o0ex0_LANE);
        fl_m1[(0+LANE)*10 +: 10] = (m1_add_coutLANE ? (10'd1 << 2) : 10'd0) | (((m1_aLANE[15] ^ m1_bLANE[15] ^ m1_add_coutLANE) ^ m1_add_sLANE[15]) ? (10'd1 << 8) : 10'd0) | (m1_add_coutLANE ? (10'd1 << 7) : 10'd0);
      end
      5'd1: begin
        pc_a_m1[(LANE)*16 +: 16] = m1_aLANE; pc_b_m1[(LANE)*16 +: 16] = ~m1_bLANE; pc_cin_m1[(LANE)*1] = 1'b1;
        m1_o1ex0_LANE = $signed({~m1_add_coutLANE, m1_add_sLANE});
        y_m1[((LANE*16)+0) +: 16] = m1_wrap(m1_o1ex0_LANE);
        fl_m1[(0+LANE)*10 +: 10] = (~m1_add_coutLANE ? (10'd1 << 2) : 10'd0) | (((m1_aLANE[15] ^ ~m1_bLANE[15] ^ m1_add_coutLANE) ^ m1_add_sLANE[15]) ? (10'd1 << 8) : 10'd0) | (~m1_add_coutLANE ? (10'd1 << 7) : 10'd0);
      end
      5'd2: begin
        pc_a_m1[(LANE)*16 +: 16] = m1_aLANE; pc_b_m1[(LANE)*16 +: 16] = m1_bLANE; pc_cin_m1[(LANE)*1] = 1'b1;
        m1_o2ex0_LANE = $signed({1'b0, m1_add_coutLANE, m1_add_sLANE});
        y_m1[((LANE*16)+0) +: 16] = m1_wrap(m1_o2ex0_LANE);
        fl_m1[(0+LANE)*10 +: 10] = (m1_add_coutLANE ? (10'd1 << 2) : 10'd0) | (((m1_aLANE[15] ^ m1_bLANE[15] ^ m1_add_coutLANE) ^ m1_add_sLANE[15]) ? (10'd1 << 8) : 10'd0) | (m1_add_coutLANE ? (10'd1 << 7) : 10'd0);
      end
      5'd3: begin
        pc_a_m1[(LANE)*16 +: 16] = 16'd0; pc_b_m1[(LANE)*16 +: 16] = ~m1_aLANE; pc_cin_m1[(LANE)*1] = 1'b1;
        m1_o3ex0_LANE = $signed({~m1_add_coutLANE, m1_add_sLANE});
        y_m1[((LANE*16)+0) +: 16] = m1_wrap(m1_o3ex0_LANE);
        fl_m1[(0+LANE)*10 +: 10] = (~m1_add_coutLANE ? (10'd1 << 2) : 10'd0) | (((1'b0 ^ ~m1_aLANE[15] ^ m1_add_coutLANE) ^ m1_add_sLANE[15]) ? (10'd1 << 8) : 10'd0) | (m1_aLANE != 0 ? (10'd1 << 7) : 10'd0);
      end
      5'd4: begin
        m1_o4ex0_LANE = (m1_vaLANE < 0) ? -m1_vaLANE : m1_vaLANE;
        m1_o4sx0_LANE = (($signed({m1_aLANE[15], m1_aLANE}) < 0) ? -$signed({m1_aLANE[15], m1_aLANE}) : $signed({m1_aLANE[15], m1_aLANE}));
        y_m1[((LANE*16)+0) +: 16] = m1_wrap(m1_o4ex0_LANE);
        fl_m1[(0+LANE)*10 +: 10] = (m1_o4sx0_LANE > 35'sd32767 || m1_o4sx0_LANE < -35'sd32768 ? (10'd1 << 8) : 10'd0) | (m1_o4ex0_LANE > 35'sd65535 || m1_o4ex0_LANE < 0 ? (10'd1 << 2) : 10'd0);
      end
      5'd5: begin
        pc_a_m1[(LANE)*16 +: 16] = m1_aLANE; pc_b_m1[(LANE)*16 +: 16] = m1_bLANE; pc_cin_m1[(LANE)*1] = 1'b0;
        m1_o5ex0_LANE = $signed({1'b0, m1_add_coutLANE, m1_add_sLANE});
        y_m1[((LANE*16)+0) +: 16] = m1_sat(m1_o5ex0_LANE);
        fl_m1[(0+LANE)*10 +: 10] = (m1_add_coutLANE ? (10'd1 << 2) : 10'd0) | (((m1_aLANE[15] ^ m1_bLANE[15] ^ m1_add_coutLANE) ^ m1_add_sLANE[15]) ? (10'd1 << 8) : 10'd0);
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m1_bitcount #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [4:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m1,
  output logic [19:0] fl_m1
);
  // alu_core_m1_bitcount: lane LANE of mode 1 (int16_unsigned) for the bitcount ops popcount, clz, ctz; the result buses are the mode's, with only this lane's bits written
  import alu_core_m1_pkg::*;
  logic d_m1;
  logic [15:0] m1_aLANE;
  logic [15:0] m1_bLANE;
  logic [49:0] m1_xa [0:0];
  logic [49:0] m1_xb [0:0];
  logic signed [16:0] m1_vaLANE;
  logic signed [16:0] m1_vbLANE;
  logic [15:0] m1_popcount_aLANE;
  logic [4:0] m1_popcount_nLANE;
  logic signed [34:0] m1_o18ex0_LANE;
  logic signed [34:0] m1_o19ex0_LANE;
  logic signed [34:0] m1_o20ex0_LANE;
  assign m1_aLANE = a[(LANE*16) +: 16];
  assign m1_bLANE = b[(LANE*16) +: 16];
  assign m1_xa[LANE] = m1_x(m1_unpack_s(m1_aLANE, 1'b0));
  assign m1_xb[LANE] = m1_x(m1_unpack_s(m1_bLANE, 1'b0));
  assign m1_vaLANE = {1'b0, m1_aLANE};
  assign m1_vbLANE = {1'b0, m1_bLANE};
  fam_count_popcount_balanced_tree_full_adder_3_2_ripple_carry_p4180c_w16 u_m1_popcountLANE (.a(m1_popcount_aLANE), .n(m1_popcount_nLANE));
  always_comb begin
    y_m1 = '0; d_m1 = '0; fl_m1 = '0;
    m1_popcount_aLANE = 'x; m1_o18ex0_LANE = 'x; m1_o19ex0_LANE = 'x; m1_o20ex0_LANE = 'x;
    case (op)
      5'd18: begin
        m1_popcount_aLANE = m1_aLANE;
        y_m1[((LANE*16)+0) +: 16] = {{11{1'b0}}, m1_popcount_nLANE};
      end
      5'd19: begin
        y_m1[((LANE*16)+0) +: 16] = m1_aLANE[15] ? 16'd0 : m1_aLANE[14] ? 16'd1 : m1_aLANE[13] ? 16'd2 : m1_aLANE[12] ? 16'd3 : m1_aLANE[11] ? 16'd4 : m1_aLANE[10] ? 16'd5 : m1_aLANE[9] ? 16'd6 : m1_aLANE[8] ? 16'd7 : m1_aLANE[7] ? 16'd8 : m1_aLANE[6] ? 16'd9 : m1_aLANE[5] ? 16'd10 : m1_aLANE[4] ? 16'd11 : m1_aLANE[3] ? 16'd12 : m1_aLANE[2] ? 16'd13 : m1_aLANE[1] ? 16'd14 : m1_aLANE[0] ? 16'd15 : 16'd16;
      end
      5'd20: begin
        y_m1[((LANE*16)+0) +: 16] = m1_aLANE[0] ? 16'd0 : m1_aLANE[1] ? 16'd1 : m1_aLANE[2] ? 16'd2 : m1_aLANE[3] ? 16'd3 : m1_aLANE[4] ? 16'd4 : m1_aLANE[5] ? 16'd5 : m1_aLANE[6] ? 16'd6 : m1_aLANE[7] ? 16'd7 : m1_aLANE[8] ? 16'd8 : m1_aLANE[9] ? 16'd9 : m1_aLANE[10] ? 16'd10 : m1_aLANE[11] ? 16'd11 : m1_aLANE[12] ? 16'd12 : m1_aLANE[13] ? 16'd13 : m1_aLANE[14] ? 16'd14 : m1_aLANE[15] ? 16'd15 : 16'd16;
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m1_comparator #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [4:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m1,
  output logic [19:0] fl_m1
);
  // alu_core_m1_comparator: lane LANE of mode 1 (int16_unsigned) for the comparator ops min, max, cmp; the result buses are the mode's, with only this lane's bits written
  import alu_core_m1_pkg::*;
  logic d_m1;
  logic [15:0] m1_aLANE;
  logic [15:0] m1_bLANE;
  logic [49:0] m1_xa [0:0];
  logic [49:0] m1_xb [0:0];
  logic signed [16:0] m1_vaLANE;
  logic signed [16:0] m1_vbLANE;
  logic [15:0] m1_cmp_aLANE;
  logic [15:0] m1_cmp_bLANE;
  logic m1_cmp_ltLANE;
  logic m1_cmp_eqLANE;
  logic signed [34:0] m1_o8ex0_LANE;
  logic signed [34:0] m1_o9ex0_LANE;
  logic signed [34:0] m1_o10ex0_LANE;
  assign m1_aLANE = a[(LANE*16) +: 16];
  assign m1_bLANE = b[(LANE*16) +: 16];
  assign m1_xa[LANE] = m1_x(m1_unpack_s(m1_aLANE, 1'b0));
  assign m1_xb[LANE] = m1_x(m1_unpack_s(m1_bLANE, 1'b0));
  assign m1_vaLANE = {1'b0, m1_aLANE};
  assign m1_vbLANE = {1'b0, m1_bLANE};
  fam_cmp_prefix_comparator #(.W(16), .SIGNED(0), .STRUCTURE(0), .RADIX(2)) u_m1_cmpLANE (.a(m1_cmp_aLANE), .b(m1_cmp_bLANE), .lt(m1_cmp_ltLANE), .eq(m1_cmp_eqLANE));
  always_comb begin
    y_m1 = '0; d_m1 = '0; fl_m1 = '0;
    m1_cmp_aLANE = 'x; m1_cmp_bLANE = 'x; m1_o8ex0_LANE = 'x; m1_o9ex0_LANE = 'x; m1_o10ex0_LANE = 'x;
    case (op)
      5'd8: begin
        m1_cmp_aLANE = m1_aLANE; m1_cmp_bLANE = m1_bLANE;
        y_m1[((LANE*16)+0) +: 16] = (m1_cmp_ltLANE | m1_cmp_eqLANE) ? m1_aLANE : m1_bLANE;
      end
      5'd9: begin
        m1_cmp_aLANE = m1_aLANE; m1_cmp_bLANE = m1_bLANE;
        y_m1[((LANE*16)+0) +: 16] = (~m1_cmp_ltLANE) ? m1_aLANE : m1_bLANE;
      end
      5'd10: begin
        m1_cmp_aLANE = m1_aLANE; m1_cmp_bLANE = m1_bLANE;
        y_m1[((LANE*16)+0) +: 16] = {{13{1'b0}}, (~m1_cmp_ltLANE & ~m1_cmp_eqLANE), m1_cmp_eqLANE, m1_cmp_ltLANE};
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m1_logic #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [4:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m1,
  output logic [19:0] fl_m1
);
  // alu_core_m1_logic: lane LANE of mode 1 (int16_unsigned) for the logic ops and, or, xor, not; the result buses are the mode's, with only this lane's bits written
  import alu_core_m1_pkg::*;
  logic d_m1;
  logic [15:0] m1_aLANE;
  logic [15:0] m1_bLANE;
  logic [49:0] m1_xa [0:0];
  logic [49:0] m1_xb [0:0];
  logic signed [16:0] m1_vaLANE;
  logic signed [16:0] m1_vbLANE;
  logic [15:0] m1_lg_aLANE;
  logic [15:0] m1_lg_bLANE;
  logic [1:0] m1_lg_opLANE;
  logic [15:0] m1_lg_yLANE;
  logic signed [34:0] m1_o14ex0_LANE;
  logic signed [34:0] m1_o15ex0_LANE;
  logic signed [34:0] m1_o16ex0_LANE;
  logic signed [34:0] m1_o17ex0_LANE;
  assign m1_aLANE = a[(LANE*16) +: 16];
  assign m1_bLANE = b[(LANE*16) +: 16];
  assign m1_xa[LANE] = m1_x(m1_unpack_s(m1_aLANE, 1'b0));
  assign m1_xb[LANE] = m1_x(m1_unpack_s(m1_bLANE, 1'b0));
  assign m1_vaLANE = {1'b0, m1_aLANE};
  assign m1_vbLANE = {1'b0, m1_bLANE};
  fam_logic_gate_row #(.W(16), .NOT_VIA_XOR(0)) u_m1_logicLANE (.a(m1_lg_aLANE), .b(m1_lg_bLANE), .op(m1_lg_opLANE), .y(m1_lg_yLANE));
  always_comb begin
    y_m1 = '0; d_m1 = '0; fl_m1 = '0;
    m1_lg_aLANE = 'x; m1_lg_bLANE = 'x; m1_lg_opLANE = 'x; m1_o14ex0_LANE = 'x; m1_o15ex0_LANE = 'x; m1_o16ex0_LANE = 'x;
    m1_o17ex0_LANE = 'x;
    case (op)
      5'd14: begin
        m1_lg_aLANE = m1_aLANE; m1_lg_bLANE = m1_bLANE; m1_lg_opLANE = 2'd0;
        y_m1[((LANE*16)+0) +: 16] = m1_lg_yLANE;
      end
      5'd15: begin
        m1_lg_aLANE = m1_aLANE; m1_lg_bLANE = m1_bLANE; m1_lg_opLANE = 2'd1;
        y_m1[((LANE*16)+0) +: 16] = m1_lg_yLANE;
      end
      5'd16: begin
        m1_lg_aLANE = m1_aLANE; m1_lg_bLANE = m1_bLANE; m1_lg_opLANE = 2'd2;
        y_m1[((LANE*16)+0) +: 16] = m1_lg_yLANE;
      end
      5'd17: begin
        m1_lg_aLANE = m1_aLANE; m1_lg_bLANE = m1_bLANE; m1_lg_opLANE = 2'd3;
        y_m1[((LANE*16)+0) +: 16] = m1_lg_yLANE;
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m1_multiplier #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [4:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m1,
  output logic [19:0] fl_m1
);
  // alu_core_m1_multiplier: lane LANE of mode 1 (int16_unsigned) for the multiplier ops mul, mul_high; the result buses are the mode's, with only this lane's bits written
  import alu_core_m1_pkg::*;
  logic d_m1;
  logic [15:0] m1_aLANE;
  logic [15:0] m1_bLANE;
  logic [49:0] m1_xa [0:0];
  logic [49:0] m1_xb [0:0];
  logic signed [16:0] m1_vaLANE;
  logic signed [16:0] m1_vbLANE;
  logic [15:0] m1_mul_aLANE;
  logic [15:0] m1_mul_bLANE;
  logic [31:0] m1_mul_pLANE;
  logic signed [34:0] m1_o6ex0_LANE;
  logic signed [34:0] m1_o6sx0_ANE;
  logic signed [34:0] m1_o7ex0_LANE;
  logic signed [34:0] m1_o7sx0_ANE;
  assign m1_aLANE = a[(LANE*16) +: 16];
  assign m1_bLANE = b[(LANE*16) +: 16];
  assign m1_xa[LANE] = m1_x(m1_unpack_s(m1_aLANE, 1'b0));
  assign m1_xb[LANE] = m1_x(m1_unpack_s(m1_bLANE, 1'b0));
  assign m1_vaLANE = {1'b0, m1_aLANE};
  assign m1_vbLANE = {1'b0, m1_bLANE};
  fam_mul_behavioral_star_w16_u u_m1_mulLANE (.a(m1_mul_aLANE), .b(m1_mul_bLANE), .p(m1_mul_pLANE));
  always_comb begin
    y_m1 = '0; d_m1 = '0; fl_m1 = '0;
    m1_mul_aLANE = 'x; m1_mul_bLANE = 'x; m1_o6ex0_LANE = 'x; m1_o6sx0_ANE = 'x; m1_o7ex0_LANE = 'x; m1_o7sx0_ANE = 'x;
    case (op)
      5'd6: begin
        m1_mul_aLANE = m1_aLANE; m1_mul_bLANE = m1_bLANE;
        m1_o6ex0_LANE = $signed({{3{1'b0}}, m1_mul_pLANE});
        m1_o6sx0_ANE = m1_o6ex0_LANE - (m1_aLANE[15] ? ($signed(m1_vbLANE) <<< 16) : 35'sd0) - (m1_bLANE[15] ? ($signed(m1_vaLANE) <<< 16) : 35'sd0) + ((m1_aLANE[15] & m1_bLANE[15]) ? 35'sd4294967296 : 35'sd0);
        y_m1[((LANE*16)+0) +: 16] = m1_wrap(m1_o6ex0_LANE);
        fl_m1[(0+LANE)*10 +: 10] = (m1_o6sx0_ANE > 35'sd32767 || m1_o6sx0_ANE < -35'sd32768 ? (10'd1 << 8) : 10'd0) | (m1_o6ex0_LANE > 35'sd65535 || m1_o6ex0_LANE < 0 ? (10'd1 << 2) : 10'd0);
      end
      5'd7: begin
        m1_mul_aLANE = m1_aLANE; m1_mul_bLANE = m1_bLANE;
        m1_o7ex0_LANE = $signed({{3{1'b0}}, m1_mul_pLANE});
        m1_o7sx0_ANE = m1_o7ex0_LANE - (m1_aLANE[15] ? ($signed(m1_vbLANE) <<< 16) : 35'sd0) - (m1_bLANE[15] ? ($signed(m1_vaLANE) <<< 16) : 35'sd0) + ((m1_aLANE[15] & m1_bLANE[15]) ? 35'sd4294967296 : 35'sd0);
        y_m1[((LANE*16)+0) +: 16] = m1_wrap(m1_o7ex0_LANE >>> 16);
        fl_m1[(0+LANE)*10 +: 10] = (m1_o7sx0_ANE > 35'sd32767 || m1_o7sx0_ANE < -35'sd32768 ? (10'd1 << 8) : 10'd0) | (m1_o7ex0_LANE > 35'sd65535 || m1_o7ex0_LANE < 0 ? (10'd1 << 2) : 10'd0);
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m1_shifter #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [4:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m1,
  output logic [19:0] fl_m1
);
  // alu_core_m1_shifter: lane LANE of mode 1 (int16_unsigned) for the shifter ops shl, shr_arith, rol; the result buses are the mode's, with only this lane's bits written
  import alu_core_m1_pkg::*;
  logic d_m1;
  logic [15:0] m1_aLANE;
  logic [15:0] m1_bLANE;
  logic [49:0] m1_xa [0:0];
  logic [49:0] m1_xb [0:0];
  logic signed [16:0] m1_vaLANE;
  logic signed [16:0] m1_vbLANE;
  logic [15:0] m1_sh_aLANE;
  logic [3:0] m1_sh_amtLANE;
  logic [2:0] m1_sh_opLANE;
  logic [15:0] m1_sh_yLANE;
  logic signed [34:0] m1_o11ex0_LANE;
  logic signed [34:0] m1_o12ex0_LANE;
  logic signed [34:0] m1_o13ex0_LANE;
  assign m1_aLANE = a[(LANE*16) +: 16];
  assign m1_bLANE = b[(LANE*16) +: 16];
  assign m1_xa[LANE] = m1_x(m1_unpack_s(m1_aLANE, 1'b0));
  assign m1_xb[LANE] = m1_x(m1_unpack_s(m1_bLANE, 1'b0));
  assign m1_vaLANE = {1'b0, m1_aLANE};
  assign m1_vbLANE = {1'b0, m1_bLANE};
  fam_shift_barrel_mux_tree #(.W(16), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u_m1_shifterLANE (.a(m1_sh_aLANE), .amt(m1_sh_amtLANE), .op(m1_sh_opLANE), .y(m1_sh_yLANE), .sticky());
  always_comb begin
    y_m1 = '0; d_m1 = '0; fl_m1 = '0;
    m1_sh_aLANE = 'x; m1_sh_amtLANE = 'x; m1_sh_opLANE = 'x; m1_o11ex0_LANE = 'x; m1_o12ex0_LANE = 'x; m1_o13ex0_LANE = 'x;
    case (op)
      5'd11: begin
        m1_sh_aLANE = m1_aLANE; m1_sh_amtLANE = 4'(m1_bLANE % 16'd16); m1_sh_opLANE = 3'd0;
        y_m1[((LANE*16)+0) +: 16] = m1_sh_yLANE;
      end
      5'd12: begin
        m1_sh_aLANE = m1_aLANE; m1_sh_amtLANE = 4'(m1_bLANE % 16'd16); m1_sh_opLANE = 3'd2;
        y_m1[((LANE*16)+0) +: 16] = m1_sh_yLANE;
      end
      5'd13: begin
        m1_sh_aLANE = m1_aLANE; m1_sh_amtLANE = 4'(m1_bLANE % 16'd16); m1_sh_opLANE = 3'd3;
        y_m1[((LANE*16)+0) +: 16] = m1_sh_yLANE;
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m2_adder_sh #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [4:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m2,
  output logic [19:0] fl_m2,
  output logic [15:0] pc_a_m2,
  output logic [15:0] pc_b_m2,
  output logic [1:0] pc_cin_m2,
  input  logic [15:0] pc_s_m2,
  input  logic [1:0] pc_co_m2
);
  // alu_core_m2_adder_sh: lane LANE of mode 2 (int8_twos_complement) for the adder ops add, sub, adc, neg, abs, add_sat; the result buses are the mode's, with only this lane's bits written; the unit's shared adder serve this lane through the pc_/tp_ buses
  import alu_core_m2_pkg::*;
  logic d_m2;
  logic [7:0] m2_aLANE;
  logic [7:0] m2_bLANE;
  logic [33:0] m2_xa [0:1];
  logic [33:0] m2_xb [0:1];
  logic signed [8:0] m2_vaLANE;
  logic signed [8:0] m2_vbLANE;
  logic [7:0] m2_add_sLANE;
  logic m2_add_coutLANE;
  logic signed [18:0] m2_o0ex0_LANE;
  logic signed [18:0] m2_o1ex0_LANE;
  logic signed [18:0] m2_o2ex0_LANE;
  logic signed [18:0] m2_o3ex0_LANE;
  logic signed [18:0] m2_o4ex0_LANE;
  logic signed [18:0] m2_o5ex0_LANE;
  assign m2_aLANE = a[(LANE*8) +: 8];
  assign m2_bLANE = b[(LANE*8) +: 8];
  assign m2_xa[LANE] = m2_x(m2_unpack_s(m2_aLANE, 1'b0));
  assign m2_xb[LANE] = m2_x(m2_unpack_s(m2_bLANE, 1'b0));
  assign m2_vaLANE = {m2_aLANE[7], m2_aLANE};
  assign m2_vbLANE = {m2_bLANE[7], m2_bLANE};
  assign m2_add_sLANE = pc_s_m2[(LANE)*8 +: 8];
  assign m2_add_coutLANE = pc_co_m2[(LANE+1)*1-1];
  always_comb begin
    y_m2 = '0; d_m2 = '0; fl_m2 = '0;
    m2_o0ex0_LANE = 'x; m2_o1ex0_LANE = 'x; m2_o2ex0_LANE = 'x; m2_o3ex0_LANE = 'x; m2_o4ex0_LANE = 'x; m2_o5ex0_LANE = 'x;
    pc_a_m2 = '0; pc_b_m2 = '0; pc_cin_m2 = '0;
    case (op)
      5'd0: begin
        pc_a_m2[(LANE)*8 +: 8] = m2_aLANE; pc_b_m2[(LANE)*8 +: 8] = m2_bLANE; pc_cin_m2[(LANE)*1] = 1'b0;
        m2_o0ex0_LANE = $signed({(m2_aLANE[7] ^ m2_bLANE[7] ^ m2_add_coutLANE), m2_add_sLANE});
        y_m2[((LANE*8)+0) +: 8] = m2_wrap(m2_o0ex0_LANE);
        fl_m2[(0+LANE)*10 +: 10] = (((m2_aLANE[7] ^ m2_bLANE[7] ^ m2_add_coutLANE) ^ m2_add_sLANE[7]) ? (10'd1 << 8) : 10'd0) | (((m2_aLANE[7] ^ m2_bLANE[7] ^ m2_add_coutLANE) ^ m2_add_sLANE[7]) ? (10'd1 << 2) : 10'd0) | (m2_add_coutLANE ? (10'd1 << 7) : 10'd0);
      end
      5'd1: begin
        pc_a_m2[(LANE)*8 +: 8] = m2_aLANE; pc_b_m2[(LANE)*8 +: 8] = ~m2_bLANE; pc_cin_m2[(LANE)*1] = 1'b1;
        m2_o1ex0_LANE = $signed({(m2_aLANE[7] ^ ~m2_bLANE[7] ^ m2_add_coutLANE), m2_add_sLANE});
        y_m2[((LANE*8)+0) +: 8] = m2_wrap(m2_o1ex0_LANE);
        fl_m2[(0+LANE)*10 +: 10] = (((m2_aLANE[7] ^ ~m2_bLANE[7] ^ m2_add_coutLANE) ^ m2_add_sLANE[7]) ? (10'd1 << 8) : 10'd0) | (((m2_aLANE[7] ^ ~m2_bLANE[7] ^ m2_add_coutLANE) ^ m2_add_sLANE[7]) ? (10'd1 << 2) : 10'd0) | (~m2_add_coutLANE ? (10'd1 << 7) : 10'd0);
      end
      5'd2: begin
        pc_a_m2[(LANE)*8 +: 8] = m2_aLANE; pc_b_m2[(LANE)*8 +: 8] = m2_bLANE; pc_cin_m2[(LANE)*1] = 1'b1;
        m2_o2ex0_LANE = $signed({(m2_aLANE[7] ^ m2_bLANE[7] ^ m2_add_coutLANE), m2_add_sLANE});
        y_m2[((LANE*8)+0) +: 8] = m2_wrap(m2_o2ex0_LANE);
        fl_m2[(0+LANE)*10 +: 10] = (((m2_aLANE[7] ^ m2_bLANE[7] ^ m2_add_coutLANE) ^ m2_add_sLANE[7]) ? (10'd1 << 8) : 10'd0) | (((m2_aLANE[7] ^ m2_bLANE[7] ^ m2_add_coutLANE) ^ m2_add_sLANE[7]) ? (10'd1 << 2) : 10'd0) | (m2_add_coutLANE ? (10'd1 << 7) : 10'd0);
      end
      5'd3: begin
        pc_a_m2[(LANE)*8 +: 8] = 8'd0; pc_b_m2[(LANE)*8 +: 8] = ~m2_aLANE; pc_cin_m2[(LANE)*1] = 1'b1;
        m2_o3ex0_LANE = $signed({(1'b0 ^ ~m2_aLANE[7] ^ m2_add_coutLANE), m2_add_sLANE});
        y_m2[((LANE*8)+0) +: 8] = m2_wrap(m2_o3ex0_LANE);
        fl_m2[(0+LANE)*10 +: 10] = (((1'b0 ^ ~m2_aLANE[7] ^ m2_add_coutLANE) ^ m2_add_sLANE[7]) ? (10'd1 << 8) : 10'd0) | (((1'b0 ^ ~m2_aLANE[7] ^ m2_add_coutLANE) ^ m2_add_sLANE[7]) ? (10'd1 << 2) : 10'd0) | (m2_aLANE != 0 ? (10'd1 << 7) : 10'd0);
      end
      5'd4: begin
        pc_a_m2[(LANE)*8 +: 8] = 8'd0; pc_b_m2[(LANE)*8 +: 8] = ~m2_aLANE; pc_cin_m2[(LANE)*1] = 1'b1;
        m2_o4ex0_LANE = (m2_aLANE[7] ? $signed({(1'b0 ^ ~m2_aLANE[7] ^ m2_add_coutLANE), m2_add_sLANE}) : $signed({1'b0, m2_aLANE}));
        y_m2[((LANE*8)+0) +: 8] = m2_wrap(m2_o4ex0_LANE);
        fl_m2[(0+LANE)*10 +: 10] = ((m2_aLANE[7] & ((1'b0 ^ ~m2_aLANE[7] ^ m2_add_coutLANE) ^ m2_add_sLANE[7])) ? (10'd1 << 8) : 10'd0) | ((m2_aLANE[7] & ((1'b0 ^ ~m2_aLANE[7] ^ m2_add_coutLANE) ^ m2_add_sLANE[7])) ? (10'd1 << 2) : 10'd0);
      end
      5'd5: begin
        pc_a_m2[(LANE)*8 +: 8] = m2_aLANE; pc_b_m2[(LANE)*8 +: 8] = m2_bLANE; pc_cin_m2[(LANE)*1] = 1'b0;
        m2_o5ex0_LANE = $signed({(m2_aLANE[7] ^ m2_bLANE[7] ^ m2_add_coutLANE), m2_add_sLANE});
        y_m2[((LANE*8)+0) +: 8] = m2_sat(m2_o5ex0_LANE);
        fl_m2[(0+LANE)*10 +: 10] = (((m2_aLANE[7] ^ m2_bLANE[7] ^ m2_add_coutLANE) ^ m2_add_sLANE[7]) ? (10'd1 << 8) : 10'd0) | (((m2_aLANE[7] ^ m2_bLANE[7] ^ m2_add_coutLANE) ^ m2_add_sLANE[7]) ? (10'd1 << 2) : 10'd0);
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m2_bitcount #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [4:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m2,
  output logic [19:0] fl_m2
);
  // alu_core_m2_bitcount: lane LANE of mode 2 (int8_twos_complement) for the bitcount ops popcount, clz, ctz; the result buses are the mode's, with only this lane's bits written
  import alu_core_m2_pkg::*;
  logic d_m2;
  logic [7:0] m2_aLANE;
  logic [7:0] m2_bLANE;
  logic [33:0] m2_xa [0:1];
  logic [33:0] m2_xb [0:1];
  logic signed [8:0] m2_vaLANE;
  logic signed [8:0] m2_vbLANE;
  logic [7:0] m2_popcount_aLANE;
  logic [3:0] m2_popcount_nLANE;
  logic signed [18:0] m2_o18ex0_LANE;
  logic signed [18:0] m2_o19ex0_LANE;
  logic signed [18:0] m2_o20ex0_LANE;
  assign m2_aLANE = a[(LANE*8) +: 8];
  assign m2_bLANE = b[(LANE*8) +: 8];
  assign m2_xa[LANE] = m2_x(m2_unpack_s(m2_aLANE, 1'b0));
  assign m2_xb[LANE] = m2_x(m2_unpack_s(m2_bLANE, 1'b0));
  assign m2_vaLANE = {m2_aLANE[7], m2_aLANE};
  assign m2_vbLANE = {m2_bLANE[7], m2_bLANE};
  fam_count_popcount_balanced_tree_full_adder_3_2_ripple_carry_p4180c_w8 u_m2_popcountLANE (.a(m2_popcount_aLANE), .n(m2_popcount_nLANE));
  always_comb begin
    y_m2 = '0; d_m2 = '0; fl_m2 = '0;
    m2_popcount_aLANE = 'x; m2_o18ex0_LANE = 'x; m2_o19ex0_LANE = 'x; m2_o20ex0_LANE = 'x;
    case (op)
      5'd18: begin
        m2_popcount_aLANE = m2_aLANE;
        y_m2[((LANE*8)+0) +: 8] = {{4{1'b0}}, m2_popcount_nLANE};
      end
      5'd19: begin
        y_m2[((LANE*8)+0) +: 8] = m2_aLANE[7] ? 8'd0 : m2_aLANE[6] ? 8'd1 : m2_aLANE[5] ? 8'd2 : m2_aLANE[4] ? 8'd3 : m2_aLANE[3] ? 8'd4 : m2_aLANE[2] ? 8'd5 : m2_aLANE[1] ? 8'd6 : m2_aLANE[0] ? 8'd7 : 8'd8;
      end
      5'd20: begin
        y_m2[((LANE*8)+0) +: 8] = m2_aLANE[0] ? 8'd0 : m2_aLANE[1] ? 8'd1 : m2_aLANE[2] ? 8'd2 : m2_aLANE[3] ? 8'd3 : m2_aLANE[4] ? 8'd4 : m2_aLANE[5] ? 8'd5 : m2_aLANE[6] ? 8'd6 : m2_aLANE[7] ? 8'd7 : 8'd8;
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m2_comparator #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [4:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m2,
  output logic [19:0] fl_m2
);
  // alu_core_m2_comparator: lane LANE of mode 2 (int8_twos_complement) for the comparator ops min, max, cmp; the result buses are the mode's, with only this lane's bits written
  import alu_core_m2_pkg::*;
  logic d_m2;
  logic [7:0] m2_aLANE;
  logic [7:0] m2_bLANE;
  logic [33:0] m2_xa [0:1];
  logic [33:0] m2_xb [0:1];
  logic signed [8:0] m2_vaLANE;
  logic signed [8:0] m2_vbLANE;
  logic [7:0] m2_cmp_aLANE;
  logic [7:0] m2_cmp_bLANE;
  logic m2_cmp_ltLANE;
  logic m2_cmp_eqLANE;
  logic signed [18:0] m2_o8ex0_LANE;
  logic signed [18:0] m2_o9ex0_LANE;
  logic signed [18:0] m2_o10ex0_LANE;
  assign m2_aLANE = a[(LANE*8) +: 8];
  assign m2_bLANE = b[(LANE*8) +: 8];
  assign m2_xa[LANE] = m2_x(m2_unpack_s(m2_aLANE, 1'b0));
  assign m2_xb[LANE] = m2_x(m2_unpack_s(m2_bLANE, 1'b0));
  assign m2_vaLANE = {m2_aLANE[7], m2_aLANE};
  assign m2_vbLANE = {m2_bLANE[7], m2_bLANE};
  fam_cmp_prefix_comparator #(.W(8), .SIGNED(1), .STRUCTURE(0), .RADIX(2)) u_m2_cmpLANE (.a(m2_cmp_aLANE), .b(m2_cmp_bLANE), .lt(m2_cmp_ltLANE), .eq(m2_cmp_eqLANE));
  always_comb begin
    y_m2 = '0; d_m2 = '0; fl_m2 = '0;
    m2_cmp_aLANE = 'x; m2_cmp_bLANE = 'x; m2_o8ex0_LANE = 'x; m2_o9ex0_LANE = 'x; m2_o10ex0_LANE = 'x;
    case (op)
      5'd8: begin
        m2_cmp_aLANE = m2_aLANE; m2_cmp_bLANE = m2_bLANE;
        y_m2[((LANE*8)+0) +: 8] = (m2_cmp_ltLANE | m2_cmp_eqLANE) ? m2_aLANE : m2_bLANE;
      end
      5'd9: begin
        m2_cmp_aLANE = m2_aLANE; m2_cmp_bLANE = m2_bLANE;
        y_m2[((LANE*8)+0) +: 8] = (~m2_cmp_ltLANE) ? m2_aLANE : m2_bLANE;
      end
      5'd10: begin
        m2_cmp_aLANE = m2_aLANE; m2_cmp_bLANE = m2_bLANE;
        y_m2[((LANE*8)+0) +: 8] = {{5{1'b0}}, (~m2_cmp_ltLANE & ~m2_cmp_eqLANE), m2_cmp_eqLANE, m2_cmp_ltLANE};
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m2_logic #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [4:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m2,
  output logic [19:0] fl_m2
);
  // alu_core_m2_logic: lane LANE of mode 2 (int8_twos_complement) for the logic ops and, or, xor, not; the result buses are the mode's, with only this lane's bits written
  import alu_core_m2_pkg::*;
  logic d_m2;
  logic [7:0] m2_aLANE;
  logic [7:0] m2_bLANE;
  logic [33:0] m2_xa [0:1];
  logic [33:0] m2_xb [0:1];
  logic signed [8:0] m2_vaLANE;
  logic signed [8:0] m2_vbLANE;
  logic [7:0] m2_lg_aLANE;
  logic [7:0] m2_lg_bLANE;
  logic [1:0] m2_lg_opLANE;
  logic [7:0] m2_lg_yLANE;
  logic signed [18:0] m2_o14ex0_LANE;
  logic signed [18:0] m2_o15ex0_LANE;
  logic signed [18:0] m2_o16ex0_LANE;
  logic signed [18:0] m2_o17ex0_LANE;
  assign m2_aLANE = a[(LANE*8) +: 8];
  assign m2_bLANE = b[(LANE*8) +: 8];
  assign m2_xa[LANE] = m2_x(m2_unpack_s(m2_aLANE, 1'b0));
  assign m2_xb[LANE] = m2_x(m2_unpack_s(m2_bLANE, 1'b0));
  assign m2_vaLANE = {m2_aLANE[7], m2_aLANE};
  assign m2_vbLANE = {m2_bLANE[7], m2_bLANE};
  fam_logic_gate_row #(.W(8), .NOT_VIA_XOR(0)) u_m2_logicLANE (.a(m2_lg_aLANE), .b(m2_lg_bLANE), .op(m2_lg_opLANE), .y(m2_lg_yLANE));
  always_comb begin
    y_m2 = '0; d_m2 = '0; fl_m2 = '0;
    m2_lg_aLANE = 'x; m2_lg_bLANE = 'x; m2_lg_opLANE = 'x; m2_o14ex0_LANE = 'x; m2_o15ex0_LANE = 'x; m2_o16ex0_LANE = 'x;
    m2_o17ex0_LANE = 'x;
    case (op)
      5'd14: begin
        m2_lg_aLANE = m2_aLANE; m2_lg_bLANE = m2_bLANE; m2_lg_opLANE = 2'd0;
        y_m2[((LANE*8)+0) +: 8] = m2_lg_yLANE;
      end
      5'd15: begin
        m2_lg_aLANE = m2_aLANE; m2_lg_bLANE = m2_bLANE; m2_lg_opLANE = 2'd1;
        y_m2[((LANE*8)+0) +: 8] = m2_lg_yLANE;
      end
      5'd16: begin
        m2_lg_aLANE = m2_aLANE; m2_lg_bLANE = m2_bLANE; m2_lg_opLANE = 2'd2;
        y_m2[((LANE*8)+0) +: 8] = m2_lg_yLANE;
      end
      5'd17: begin
        m2_lg_aLANE = m2_aLANE; m2_lg_bLANE = m2_bLANE; m2_lg_opLANE = 2'd3;
        y_m2[((LANE*8)+0) +: 8] = m2_lg_yLANE;
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m2_multiplier #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [4:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m2,
  output logic [19:0] fl_m2
);
  // alu_core_m2_multiplier: lane LANE of mode 2 (int8_twos_complement) for the multiplier ops mul, mul_high; the result buses are the mode's, with only this lane's bits written
  import alu_core_m2_pkg::*;
  logic d_m2;
  logic [7:0] m2_aLANE;
  logic [7:0] m2_bLANE;
  logic [33:0] m2_xa [0:1];
  logic [33:0] m2_xb [0:1];
  logic signed [8:0] m2_vaLANE;
  logic signed [8:0] m2_vbLANE;
  logic [7:0] m2_mul_aLANE;
  logic [7:0] m2_mul_bLANE;
  logic [15:0] m2_mul_pLANE;
  logic signed [18:0] m2_o6ex0_LANE;
  logic signed [18:0] m2_o7ex0_LANE;
  assign m2_aLANE = a[(LANE*8) +: 8];
  assign m2_bLANE = b[(LANE*8) +: 8];
  assign m2_xa[LANE] = m2_x(m2_unpack_s(m2_aLANE, 1'b0));
  assign m2_xb[LANE] = m2_x(m2_unpack_s(m2_bLANE, 1'b0));
  assign m2_vaLANE = {m2_aLANE[7], m2_aLANE};
  assign m2_vbLANE = {m2_bLANE[7], m2_bLANE};
  fam_mul_behavioral_star_w8_s u_m2_mulLANE (.a(m2_mul_aLANE), .b(m2_mul_bLANE), .p(m2_mul_pLANE));
  always_comb begin
    y_m2 = '0; d_m2 = '0; fl_m2 = '0;
    m2_mul_aLANE = 'x; m2_mul_bLANE = 'x; m2_o6ex0_LANE = 'x; m2_o7ex0_LANE = 'x;
    case (op)
      5'd6: begin
        m2_mul_aLANE = m2_aLANE; m2_mul_bLANE = m2_bLANE;
        m2_o6ex0_LANE = $signed({{3{m2_mul_pLANE[15]}}, m2_mul_pLANE});
        y_m2[((LANE*8)+0) +: 8] = m2_wrap(m2_o6ex0_LANE);
        fl_m2[(0+LANE)*10 +: 10] = (m2_o6ex0_LANE > 19'sd127 || m2_o6ex0_LANE < -19'sd128 ? (10'd1 << 8) : 10'd0) | (m2_o6ex0_LANE > 19'sd127 || m2_o6ex0_LANE < -19'sd128 ? (10'd1 << 2) : 10'd0);
      end
      5'd7: begin
        m2_mul_aLANE = m2_aLANE; m2_mul_bLANE = m2_bLANE;
        m2_o7ex0_LANE = $signed({{3{m2_mul_pLANE[15]}}, m2_mul_pLANE});
        y_m2[((LANE*8)+0) +: 8] = m2_wrap(m2_o7ex0_LANE >>> 8);
        fl_m2[(0+LANE)*10 +: 10] = (m2_o7ex0_LANE > 19'sd127 || m2_o7ex0_LANE < -19'sd128 ? (10'd1 << 8) : 10'd0) | (m2_o7ex0_LANE > 19'sd127 || m2_o7ex0_LANE < -19'sd128 ? (10'd1 << 2) : 10'd0);
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m2_shifter #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [4:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m2,
  output logic [19:0] fl_m2
);
  // alu_core_m2_shifter: lane LANE of mode 2 (int8_twos_complement) for the shifter ops shl, shr_arith, rol; the result buses are the mode's, with only this lane's bits written
  import alu_core_m2_pkg::*;
  logic d_m2;
  logic [7:0] m2_aLANE;
  logic [7:0] m2_bLANE;
  logic [33:0] m2_xa [0:1];
  logic [33:0] m2_xb [0:1];
  logic signed [8:0] m2_vaLANE;
  logic signed [8:0] m2_vbLANE;
  logic [7:0] m2_sh_aLANE;
  logic [2:0] m2_sh_amtLANE;
  logic [2:0] m2_sh_opLANE;
  logic [7:0] m2_sh_yLANE;
  logic signed [18:0] m2_o11ex0_LANE;
  logic signed [18:0] m2_o12ex0_LANE;
  logic signed [18:0] m2_o13ex0_LANE;
  assign m2_aLANE = a[(LANE*8) +: 8];
  assign m2_bLANE = b[(LANE*8) +: 8];
  assign m2_xa[LANE] = m2_x(m2_unpack_s(m2_aLANE, 1'b0));
  assign m2_xb[LANE] = m2_x(m2_unpack_s(m2_bLANE, 1'b0));
  assign m2_vaLANE = {m2_aLANE[7], m2_aLANE};
  assign m2_vbLANE = {m2_bLANE[7], m2_bLANE};
  fam_shift_barrel_mux_tree #(.W(8), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u_m2_shifterLANE (.a(m2_sh_aLANE), .amt(m2_sh_amtLANE), .op(m2_sh_opLANE), .y(m2_sh_yLANE), .sticky());
  always_comb begin
    y_m2 = '0; d_m2 = '0; fl_m2 = '0;
    m2_sh_aLANE = 'x; m2_sh_amtLANE = 'x; m2_sh_opLANE = 'x; m2_o11ex0_LANE = 'x; m2_o12ex0_LANE = 'x; m2_o13ex0_LANE = 'x;
    case (op)
      5'd11: begin
        m2_sh_aLANE = m2_aLANE; m2_sh_amtLANE = 3'(m2_bLANE % 8'd8); m2_sh_opLANE = 3'd0;
        y_m2[((LANE*8)+0) +: 8] = m2_sh_yLANE;
      end
      5'd12: begin
        m2_sh_aLANE = m2_aLANE; m2_sh_amtLANE = 3'(m2_bLANE % 8'd8); m2_sh_opLANE = 3'd2;
        y_m2[((LANE*8)+0) +: 8] = m2_sh_yLANE;
      end
      5'd13: begin
        m2_sh_aLANE = m2_aLANE; m2_sh_amtLANE = 3'(m2_bLANE % 8'd8); m2_sh_opLANE = 3'd3;
        y_m2[((LANE*8)+0) +: 8] = m2_sh_yLANE;
      end
      default: ;
    endcase
  end
endmodule
module alu_core_u_m0_l0_adder (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [4:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m0,
  output logic [19:0] fl_m0
);
  // alu_core_u_m0_l0_adder: physical structure `m0.l0.adder` (kind adder, slot adder); realizes m0.l0.adder: adder, mode 0 lane 0, int16_twos_complement, ops add, sub, adc, neg, abs, add_sat
  logic [15:0] pc_a_m0;
  logic [15:0] pc_b_m0;
  logic pc_cin_m0;
  logic [15:0] pc_s_m0;
  logic pc_co_m0;
  logic [15:0] y_m0_l0;
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
  assign pc_sel = (mode == 2'd0) ? 1'd0 : '0;
  assign pc_a = (mode == 2'd0) ? pc_a_m0 : '0;
  assign pc_b = (mode == 2'd0) ? pc_b_m0 : '0;
  assign pc_cin = (mode == 2'd0) ? pc_cin_m0 : '0;
  // subword partitioned_carry_chain: one library adder over the whole word, its carries cut at the selected packing's lane boundaries (1 x int16_twos_complement)
  fam_add_partitioned_w16_16_carry_kill_gate_0cc88441ac18 u_part (.a(pc_a), .b(pc_b), .cin(pc_cin), .sel(pc_sel), .s(pc_s), .cout(pc_co));
  assign pc_s_m0 = pc_s;
  assign pc_co_m0 = pc_co;
endmodule
module alu_core_u_m0_l0_multiplier (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [4:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m0,
  output logic [19:0] fl_m0
);
  // alu_core_u_m0_l0_multiplier: physical structure `m0.l0.multiplier` (kind multiplier, slot multiplier); realizes m0.l0.multiplier: multiplier, mode 0 lane 0, int16_twos_complement, ops mul, mul_high
  logic [15:0] y_m0_l0;
  logic [19:0] fl_m0_l0;
  alu_core_m0_multiplier #(.LANE(0)) u_m0_l0 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_l0), .fl_m0(fl_m0_l0));
  assign y_m0 = y_m0_l0;
  assign fl_m0 = fl_m0_l0;
endmodule
module alu_core_u_m0_l0_comparator (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [4:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m0,
  output logic [19:0] fl_m0
);
  // alu_core_u_m0_l0_comparator: physical structure `m0.l0.comparator` (kind comparator, slot comparator); realizes m0.l0.comparator: comparator, mode 0 lane 0, int16_twos_complement, ops min, max, cmp
  logic [15:0] y_m0_l0;
  logic [19:0] fl_m0_l0;
  alu_core_m0_comparator #(.LANE(0)) u_m0_l0 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_l0), .fl_m0(fl_m0_l0));
  assign y_m0 = y_m0_l0;
  assign fl_m0 = fl_m0_l0;
endmodule
module alu_core_u_m0_l0_shifter (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [4:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m0,
  output logic [19:0] fl_m0
);
  // alu_core_u_m0_l0_shifter: physical structure `m0.l0.shifter` (kind shifter, slot shifter); realizes m0.l0.shifter: shifter, mode 0 lane 0, int16_twos_complement, ops shl, shr_arith, rol
  logic [15:0] y_m0_l0;
  logic [19:0] fl_m0_l0;
  alu_core_m0_shifter #(.LANE(0)) u_m0_l0 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_l0), .fl_m0(fl_m0_l0));
  assign y_m0 = y_m0_l0;
  assign fl_m0 = fl_m0_l0;
endmodule
module alu_core_u_m0_l0_logic (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [4:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m0,
  output logic [19:0] fl_m0
);
  // alu_core_u_m0_l0_logic: physical structure `m0.l0.logic` (kind logic, slot logic); realizes m0.l0.logic: logic, mode 0 lane 0, int16_twos_complement, ops and, or, xor, not
  logic [15:0] y_m0_l0;
  logic [19:0] fl_m0_l0;
  alu_core_m0_logic #(.LANE(0)) u_m0_l0 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_l0), .fl_m0(fl_m0_l0));
  assign y_m0 = y_m0_l0;
  assign fl_m0 = fl_m0_l0;
endmodule
module alu_core_u_m0_l0_bitcount (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [4:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m0,
  output logic [19:0] fl_m0
);
  // alu_core_u_m0_l0_bitcount: physical structure `m0.l0.bitcount` (kind bitcount, slot bitcount); realizes m0.l0.bitcount: bitcount, mode 0 lane 0, int16_twos_complement, ops popcount, clz, ctz
  logic [15:0] y_m0_l0;
  logic [19:0] fl_m0_l0;
  alu_core_m0_bitcount #(.LANE(0)) u_m0_l0 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_l0), .fl_m0(fl_m0_l0));
  assign y_m0 = y_m0_l0;
  assign fl_m0 = fl_m0_l0;
endmodule
module alu_core_u_m1_l0_adder (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [4:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m1,
  output logic [19:0] fl_m1
);
  // alu_core_u_m1_l0_adder: physical structure `m1.l0.adder` (kind adder, slot adder); realizes m1.l0.adder: adder, mode 1 lane 0, int16_unsigned, ops add, sub, adc, neg, abs, add_sat
  logic [15:0] pc_a_m1;
  logic [15:0] pc_b_m1;
  logic pc_cin_m1;
  logic [15:0] pc_s_m1;
  logic pc_co_m1;
  logic [15:0] y_m1_l0;
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
  // subword partitioned_carry_chain: one library adder over the whole word, its carries cut at the selected packing's lane boundaries (1 x int16_unsigned)
  fam_add_partitioned_w16_16_carry_kill_gate_0cc88441ac18 u_part (.a(pc_a), .b(pc_b), .cin(pc_cin), .sel(pc_sel), .s(pc_s), .cout(pc_co));
  assign pc_s_m1 = pc_s;
  assign pc_co_m1 = pc_co;
endmodule
module alu_core_u_m1_l0_multiplier (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [4:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m1,
  output logic [19:0] fl_m1
);
  // alu_core_u_m1_l0_multiplier: physical structure `m1.l0.multiplier` (kind multiplier, slot multiplier); realizes m1.l0.multiplier: multiplier, mode 1 lane 0, int16_unsigned, ops mul, mul_high
  logic [15:0] y_m1_l0;
  logic [19:0] fl_m1_l0;
  alu_core_m1_multiplier #(.LANE(0)) u_m1_l0 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_l0), .fl_m1(fl_m1_l0));
  assign y_m1 = y_m1_l0;
  assign fl_m1 = fl_m1_l0;
endmodule
module alu_core_u_m1_l0_comparator (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [4:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m1,
  output logic [19:0] fl_m1
);
  // alu_core_u_m1_l0_comparator: physical structure `m1.l0.comparator` (kind comparator, slot comparator); realizes m1.l0.comparator: comparator, mode 1 lane 0, int16_unsigned, ops min, max, cmp
  logic [15:0] y_m1_l0;
  logic [19:0] fl_m1_l0;
  alu_core_m1_comparator #(.LANE(0)) u_m1_l0 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_l0), .fl_m1(fl_m1_l0));
  assign y_m1 = y_m1_l0;
  assign fl_m1 = fl_m1_l0;
endmodule
module alu_core_u_m1_l0_shifter (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [4:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m1,
  output logic [19:0] fl_m1
);
  // alu_core_u_m1_l0_shifter: physical structure `m1.l0.shifter` (kind shifter, slot shifter); realizes m1.l0.shifter: shifter, mode 1 lane 0, int16_unsigned, ops shl, shr_arith, rol
  logic [15:0] y_m1_l0;
  logic [19:0] fl_m1_l0;
  alu_core_m1_shifter #(.LANE(0)) u_m1_l0 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_l0), .fl_m1(fl_m1_l0));
  assign y_m1 = y_m1_l0;
  assign fl_m1 = fl_m1_l0;
endmodule
module alu_core_u_m1_l0_logic (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [4:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m1,
  output logic [19:0] fl_m1
);
  // alu_core_u_m1_l0_logic: physical structure `m1.l0.logic` (kind logic, slot logic); realizes m1.l0.logic: logic, mode 1 lane 0, int16_unsigned, ops and, or, xor, not
  logic [15:0] y_m1_l0;
  logic [19:0] fl_m1_l0;
  alu_core_m1_logic #(.LANE(0)) u_m1_l0 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_l0), .fl_m1(fl_m1_l0));
  assign y_m1 = y_m1_l0;
  assign fl_m1 = fl_m1_l0;
endmodule
module alu_core_u_m1_l0_bitcount (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [4:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m1,
  output logic [19:0] fl_m1
);
  // alu_core_u_m1_l0_bitcount: physical structure `m1.l0.bitcount` (kind bitcount, slot bitcount); realizes m1.l0.bitcount: bitcount, mode 1 lane 0, int16_unsigned, ops popcount, clz, ctz
  logic [15:0] y_m1_l0;
  logic [19:0] fl_m1_l0;
  alu_core_m1_bitcount #(.LANE(0)) u_m1_l0 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_l0), .fl_m1(fl_m1_l0));
  assign y_m1 = y_m1_l0;
  assign fl_m1 = fl_m1_l0;
endmodule
module alu_core_u_m2_l0_adder (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [4:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m2,
  output logic [19:0] fl_m2
);
  // alu_core_u_m2_l0_adder: physical structure `m2.l0.adder` (kind adder, slot adder); realizes m2.l0.adder: adder, mode 2 lane 0, int8_twos_complement, ops add, sub, adc, neg, abs, add_sat
  logic [15:0] pc_a_m2;
  logic [15:0] pc_b_m2;
  logic [1:0] pc_cin_m2;
  logic [15:0] pc_s_m2;
  logic [1:0] pc_co_m2;
  logic [15:0] y_m2_l0;
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
module alu_core_u_m2_l1_adder (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [4:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m2,
  output logic [19:0] fl_m2
);
  // alu_core_u_m2_l1_adder: physical structure `m2.l1.adder` (kind adder, slot adder); realizes m2.l1.adder: adder, mode 2 lane 1, int8_twos_complement, ops add, sub, adc, neg, abs, add_sat
  logic [15:0] pc_a_m2;
  logic [15:0] pc_b_m2;
  logic [1:0] pc_cin_m2;
  logic [15:0] pc_s_m2;
  logic [1:0] pc_co_m2;
  logic [15:0] y_m2_l1;
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
module alu_core_u_m2_l0_multiplier (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [4:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m2,
  output logic [19:0] fl_m2
);
  // alu_core_u_m2_l0_multiplier: physical structure `m2.l0.multiplier` (kind multiplier, slot multiplier); realizes m2.l0.multiplier: multiplier, mode 2 lane 0, int8_twos_complement, ops mul, mul_high
  logic [15:0] y_m2_l0;
  logic [19:0] fl_m2_l0;
  alu_core_m2_multiplier #(.LANE(0)) u_m2_l0 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_l0), .fl_m2(fl_m2_l0));
  assign y_m2 = y_m2_l0;
  assign fl_m2 = fl_m2_l0;
endmodule
module alu_core_u_m2_l1_multiplier (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [4:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m2,
  output logic [19:0] fl_m2
);
  // alu_core_u_m2_l1_multiplier: physical structure `m2.l1.multiplier` (kind multiplier, slot multiplier); realizes m2.l1.multiplier: multiplier, mode 2 lane 1, int8_twos_complement, ops mul, mul_high
  logic [15:0] y_m2_l1;
  logic [19:0] fl_m2_l1;
  alu_core_m2_multiplier #(.LANE(1)) u_m2_l1 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_l1), .fl_m2(fl_m2_l1));
  assign y_m2 = y_m2_l1;
  assign fl_m2 = fl_m2_l1;
endmodule
module alu_core_u_m2_l0_comparator (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [4:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m2,
  output logic [19:0] fl_m2
);
  // alu_core_u_m2_l0_comparator: physical structure `m2.l0.comparator` (kind comparator, slot comparator); realizes m2.l0.comparator: comparator, mode 2 lane 0, int8_twos_complement, ops min, max, cmp
  logic [15:0] y_m2_l0;
  logic [19:0] fl_m2_l0;
  alu_core_m2_comparator #(.LANE(0)) u_m2_l0 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_l0), .fl_m2(fl_m2_l0));
  assign y_m2 = y_m2_l0;
  assign fl_m2 = fl_m2_l0;
endmodule
module alu_core_u_m2_l1_comparator (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [4:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m2,
  output logic [19:0] fl_m2
);
  // alu_core_u_m2_l1_comparator: physical structure `m2.l1.comparator` (kind comparator, slot comparator); realizes m2.l1.comparator: comparator, mode 2 lane 1, int8_twos_complement, ops min, max, cmp
  logic [15:0] y_m2_l1;
  logic [19:0] fl_m2_l1;
  alu_core_m2_comparator #(.LANE(1)) u_m2_l1 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_l1), .fl_m2(fl_m2_l1));
  assign y_m2 = y_m2_l1;
  assign fl_m2 = fl_m2_l1;
endmodule
module alu_core_u_m2_l0_shifter (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [4:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m2,
  output logic [19:0] fl_m2
);
  // alu_core_u_m2_l0_shifter: physical structure `m2.l0.shifter` (kind shifter, slot shifter); realizes m2.l0.shifter: shifter, mode 2 lane 0, int8_twos_complement, ops shl, shr_arith, rol
  logic [15:0] y_m2_l0;
  logic [19:0] fl_m2_l0;
  alu_core_m2_shifter #(.LANE(0)) u_m2_l0 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_l0), .fl_m2(fl_m2_l0));
  assign y_m2 = y_m2_l0;
  assign fl_m2 = fl_m2_l0;
endmodule
module alu_core_u_m2_l1_shifter (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [4:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m2,
  output logic [19:0] fl_m2
);
  // alu_core_u_m2_l1_shifter: physical structure `m2.l1.shifter` (kind shifter, slot shifter); realizes m2.l1.shifter: shifter, mode 2 lane 1, int8_twos_complement, ops shl, shr_arith, rol
  logic [15:0] y_m2_l1;
  logic [19:0] fl_m2_l1;
  alu_core_m2_shifter #(.LANE(1)) u_m2_l1 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_l1), .fl_m2(fl_m2_l1));
  assign y_m2 = y_m2_l1;
  assign fl_m2 = fl_m2_l1;
endmodule
module alu_core_u_m2_l0_logic (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [4:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m2,
  output logic [19:0] fl_m2
);
  // alu_core_u_m2_l0_logic: physical structure `m2.l0.logic` (kind logic, slot logic); realizes m2.l0.logic: logic, mode 2 lane 0, int8_twos_complement, ops and, or, xor, not
  logic [15:0] y_m2_l0;
  logic [19:0] fl_m2_l0;
  alu_core_m2_logic #(.LANE(0)) u_m2_l0 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_l0), .fl_m2(fl_m2_l0));
  assign y_m2 = y_m2_l0;
  assign fl_m2 = fl_m2_l0;
endmodule
module alu_core_u_m2_l1_logic (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [4:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m2,
  output logic [19:0] fl_m2
);
  // alu_core_u_m2_l1_logic: physical structure `m2.l1.logic` (kind logic, slot logic); realizes m2.l1.logic: logic, mode 2 lane 1, int8_twos_complement, ops and, or, xor, not
  logic [15:0] y_m2_l1;
  logic [19:0] fl_m2_l1;
  alu_core_m2_logic #(.LANE(1)) u_m2_l1 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_l1), .fl_m2(fl_m2_l1));
  assign y_m2 = y_m2_l1;
  assign fl_m2 = fl_m2_l1;
endmodule
module alu_core_u_m2_l0_bitcount (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [4:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m2,
  output logic [19:0] fl_m2
);
  // alu_core_u_m2_l0_bitcount: physical structure `m2.l0.bitcount` (kind bitcount, slot bitcount); realizes m2.l0.bitcount: bitcount, mode 2 lane 0, int8_twos_complement, ops popcount, clz, ctz
  logic [15:0] y_m2_l0;
  logic [19:0] fl_m2_l0;
  alu_core_m2_bitcount #(.LANE(0)) u_m2_l0 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_l0), .fl_m2(fl_m2_l0));
  assign y_m2 = y_m2_l0;
  assign fl_m2 = fl_m2_l0;
endmodule
module alu_core_u_m2_l1_bitcount (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [4:0] op,
  input  logic [1:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m2,
  output logic [19:0] fl_m2
);
  // alu_core_u_m2_l1_bitcount: physical structure `m2.l1.bitcount` (kind bitcount, slot bitcount); realizes m2.l1.bitcount: bitcount, mode 2 lane 1, int8_twos_complement, ops popcount, clz, ctz
  logic [15:0] y_m2_l1;
  logic [19:0] fl_m2_l1;
  alu_core_m2_bitcount #(.LANE(1)) u_m2_l1 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m2(y_m2_l1), .fl_m2(fl_m2_l1));
  assign y_m2 = y_m2_l1;
  assign fl_m2 = fl_m2_l1;
endmodule
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


// popcount_counter_tree (balanced_tree, full_adder_3_2, adders ripple_carry): the count of the ones of a 16-bit word
module fam_count_popcount_balanced_tree_full_adder_3_2_ripple_carry_p4180c_w16 (input logic [15:0] a, output logic [4:0] n);
  logic g0_s1; assign g0_s1 = a[0] ^ a[1] ^ a[2];
  logic g0_c2; assign g0_c2 = (a[0] & a[1]) | (a[0] & a[2]) | (a[1] & a[2]);
  logic [1:0] gc0; assign gc0 = {g0_c2, g0_s1};
  logic g1_s3; assign g1_s3 = a[3] ^ a[4] ^ a[5];
  logic g1_c4; assign g1_c4 = (a[3] & a[4]) | (a[3] & a[5]) | (a[4] & a[5]);
  logic [1:0] gc1; assign gc1 = {g1_c4, g1_s3};
  logic g2_s5; assign g2_s5 = a[6] ^ a[7] ^ a[8];
  logic g2_c6; assign g2_c6 = (a[6] & a[7]) | (a[6] & a[8]) | (a[7] & a[8]);
  logic [1:0] gc2; assign gc2 = {g2_c6, g2_s5};
  logic g3_s7; assign g3_s7 = a[9] ^ a[10] ^ a[11];
  logic g3_c8; assign g3_c8 = (a[9] & a[10]) | (a[9] & a[11]) | (a[10] & a[11]);
  logic [1:0] gc3; assign gc3 = {g3_c8, g3_s7};
  logic g4_s9; assign g4_s9 = a[12] ^ a[13] ^ a[14];
  logic g4_c10; assign g4_c10 = (a[12] & a[13]) | (a[12] & a[14]) | (a[13] & a[14]);
  logic [1:0] gc4; assign gc4 = {g4_c10, g4_s9};
  logic gc5; assign gc5 = a[15];
  logic [1:0] s1;
  logic co1;
  // count adder 1 (ripple_carry, 2 bits)
  fam_adder_ripple_carry #(.W(2), .CHUNK(1), .FORM(0)) u1 (.a(gc0), .b(gc1), .cin(1'b0), .s(s1), .cout(co1));
  logic [2:0] t1; assign t1 = {co1, s1};
  logic [1:0] s2;
  logic co2;
  // count adder 2 (ripple_carry, 2 bits)
  fam_adder_ripple_carry #(.W(2), .CHUNK(1), .FORM(0)) u2 (.a(gc2), .b(gc3), .cin(1'b0), .s(s2), .cout(co2));
  logic [2:0] t2; assign t2 = {co2, s2};
  logic [1:0] s3;
  logic co3;
  // count adder 3 (ripple_carry, 2 bits)
  fam_adder_ripple_carry #(.W(2), .CHUNK(1), .FORM(0)) u3 (.a(gc4), .b({1'd0, gc5}), .cin(1'b0), .s(s3), .cout(co3));
  logic [2:0] t3; assign t3 = {co3, s3};
  logic [2:0] s4;
  logic co4;
  // count adder 4 (ripple_carry, 3 bits)
  fam_adder_ripple_carry #(.W(3), .CHUNK(1), .FORM(0)) u4 (.a(t1), .b(t2), .cin(1'b0), .s(s4), .cout(co4));
  logic [3:0] t4; assign t4 = {co4, s4};
  logic [3:0] s5;
  logic co5;
  // count adder 5 (ripple_carry, 4 bits)
  fam_adder_ripple_carry #(.W(4), .CHUNK(1), .FORM(0)) u5 (.a(t4), .b({1'd0, t3}), .cin(1'b0), .s(s5), .cout(co5));
  logic [4:0] t5; assign t5 = {co5, s5};
  assign n = t5[4:0];
endmodule


// popcount_counter_tree (balanced_tree, full_adder_3_2, adders ripple_carry): the count of the ones of a 8-bit word
module fam_count_popcount_balanced_tree_full_adder_3_2_ripple_carry_p4180c_w8 (input logic [7:0] a, output logic [3:0] n);
  logic g0_s1; assign g0_s1 = a[0] ^ a[1] ^ a[2];
  logic g0_c2; assign g0_c2 = (a[0] & a[1]) | (a[0] & a[2]) | (a[1] & a[2]);
  logic [1:0] gc0; assign gc0 = {g0_c2, g0_s1};
  logic g1_s3; assign g1_s3 = a[3] ^ a[4] ^ a[5];
  logic g1_c4; assign g1_c4 = (a[3] & a[4]) | (a[3] & a[5]) | (a[4] & a[5]);
  logic [1:0] gc1; assign gc1 = {g1_c4, g1_s3};
  logic g2_s5; assign g2_s5 = a[6] ^ a[7];
  logic g2_c6; assign g2_c6 = a[6] & a[7];
  logic [1:0] gc2; assign gc2 = {g2_c6, g2_s5};
  logic [1:0] s1;
  logic co1;
  // count adder 1 (ripple_carry, 2 bits)
  fam_adder_ripple_carry #(.W(2), .CHUNK(1), .FORM(0)) u1 (.a(gc0), .b(gc1), .cin(1'b0), .s(s1), .cout(co1));
  logic [2:0] t1; assign t1 = {co1, s1};
  logic [2:0] s2;
  logic co2;
  // count adder 2 (ripple_carry, 3 bits)
  fam_adder_ripple_carry #(.W(3), .CHUNK(1), .FORM(0)) u2 (.a(t1), .b({1'd0, gc2}), .cin(1'b0), .s(s2), .cout(co2));
  logic [3:0] t2; assign t2 = {co2, s2};
  assign n = t2[3:0];
endmodule


// The logic family library: the bitwise gate row of lane_replicated_gates and wide_gate_row.
//   fam_logic_gate_row #(W, NOT_VIA_XOR) (input [W-1:0] a, b, input [1:0] op, output [W-1:0] y)
//   op: 0 and, 1 or, 2 xor, 3 not (of a)
// NOT_VIA_XOR = 1 forms the not as a xor with ones, so the row is three gate types and a
// two-way operand select instead of four gate types under a four-way result mux.
module fam_logic_gate_row #(parameter int W = 16, parameter int NOT_VIA_XOR = 0)
  (input logic [W-1:0] a, input logic [W-1:0] b, input logic [1:0] op, output logic [W-1:0] y);
  generate
    if (NOT_VIA_XOR) begin : via_xor
      logic [W-1:0] bx;
      assign bx = (op == 2'd3) ? {W{1'b1}} : b;
      assign y = (op == 2'd0) ? (a & b) : (op == 2'd1) ? (a | b) : (a ^ bx);
    end else begin : plain
      assign y = (op == 2'd0) ? (a & b) : (op == 2'd1) ? (a | b) : (op == 2'd2) ? (a ^ b) : ~a;
    end
  endgenerate
endmodule


// behavioral_star: p = a * b, the structure left to synthesis
module fam_mul_behavioral_star_w16_s (input logic [15:0] a, input logic [15:0] b, output logic [31:0] p);
  assign p = $signed(a) * $signed(b);
endmodule


// behavioral_star: p = a * b, the structure left to synthesis
module fam_mul_behavioral_star_w16_u (input logic [15:0] a, input logic [15:0] b, output logic [31:0] p);
  assign p = a * b;
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
