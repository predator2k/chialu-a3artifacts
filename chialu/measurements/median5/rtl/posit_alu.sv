// ADIR-MEMBER packages
// alu_core_m0_pkg: the exact-arithmetic functions of mode 0 (1xposit16_1)
package alu_core_m0_pkg;

  // ---- m0: V = {special[1:0], sign, exp[11] (signed), sig[16]}
  //           X = {special[1:0], sign, exp[11] (signed), sig[36], sticky}
  localparam int m0_SW = 16, m0_EW = 11, m0_XW = 36;
  localparam int m0_VW = 30, m0_XT = 51;
  function automatic [29:0] m0_mkv(input [1:0] sp, input s, input signed [10:0] e, input [15:0] sig);
    m0_mkv = {sp, s, e, sig};
  endfunction
  function automatic [50:0] m0_mkx(input [1:0] sp, input s, input signed [10:0] e, input [35:0] sig, input st);
    m0_mkx = {sp, s, e, sig, st};
  endfunction
  function automatic [50:0] m0_x(input [29:0] v);   // widen V to X
    m0_x = {v[29:29-1], v[29-2], v[29-3 -: 11], {{(36-16){1'b0}}, v[15:0]}, 1'b0};
  endfunction
  // normalize: leading one at bit XW-1 (zero stays zero)
  function automatic [50:0] m0_norm(input [50:0] x);
    logic [35:0] s; logic signed [10:0] e; integer k;
    s = x[36:1]; e = x[36+11:36+1];
    if (s != 0) begin
      for (k = 32; k >= 1; k = k / 2) begin
        if (k < 36) begin
          if (s[35 -: 1] == 1'b0 && (s >> (36 - k)) == 0) begin
            s = s << k; e = e - k;
          end
        end
      end
    end
    m0_norm = {x[50:50-1], x[50-2], e, s, x[0]};
  endfunction

  function automatic m0_rup(input [2:0] rnd, input s, input inexact, input [36:0] rest, input [36:0] halfv,
                             input st, input lsb, input [36+8:0] fint, input [7:0] word);
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
  function automatic [50:0] m0_add(input [50:0] a, input [50:0] b, input sub);
    logic [50:0] na, nb, big, sml; logic [1:0] spa, spb; logic sa, sb, sr, sw;
    logic signed [10:0] ea, eb, d; logic [36:0] ms, mb, r; logic st, stb; integer sh;
    na = m0_norm(a); nb = m0_norm(b);
    spa = na[50:50-1]; spb = nb[50:50-1];
    sa = na[50-2]; sb = nb[50-2] ^ sub;
    if (spa == 2'd1 || spb == 2'd1) m0_add = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 && spb == 2'd2) m0_add = (sa == sb) ? m0_mkx(2'd2, sa, 0, 0, 1'b0) : m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m0_add = m0_mkx(2'd2, sa, 0, 0, 1'b0);
    else if (spb == 2'd2) m0_add = m0_mkx(2'd2, sb, 0, 0, 1'b0);
    else if (na[36:1] == 0 && !na[0]) m0_add = {nb[50:50-1], sb, nb[50-3:0]};
    else if (nb[36:1] == 0 && !nb[0]) m0_add = na;
    else begin
      ea = na[36+11:36+1]; eb = nb[36+11:36+1];
      // order by magnitude (both normalized): larger exponent, then sig
      if (ea > eb || (ea == eb && na[36:1] >= nb[36:1])) begin big = na; sml = nb; sw = 1'b0; end
      else begin big = nb; sml = na; sw = 1'b1; end
      d = big[36+11:36+1] - sml[36+11:36+1];
      ms = {1'b0, sml[36:1]}; stb = sml[0];
      if (d > 36 + 1) begin stb = stb | (ms != 0); ms = 0; end
      else begin
        for (sh = 0; sh < 36 + 2; sh = sh + 1) begin
          if (sh < d) begin stb = stb | ms[0]; ms = ms >> 1; end
        end
      end
      mb = {1'b0, big[36:1]}; st = big[0] | stb;
      if ((sw ? sb : sa) == (sw ? sa : sb)) begin
        r = mb + ms;
        sr = sw ? sb : sa;
      end else begin
        // subtract: the sticky of the smaller operand borrows one lsb
        r = mb - ms - (stb ? 1'b1 : 1'b0);
        sr = sw ? sb : sa;
        if (r == 0 && !st) sr = 1'b0;
      end
      if (r[36]) begin st = st | r[0]; r = r >> 1; m0_add = m0_mkx(2'd0, sr, big[36+11:36+1] + 1, r[35:0], st); end
      else m0_add = m0_mkx(2'd0, sr, big[36+11:36+1], r[35:0], st);
    end
  endfunction
  function automatic [50:0] m0_mul(input [50:0] a, input [50:0] b);
    logic [50:0] na, nb; logic [1:0] spa, spb; logic s; logic [2*36-1:0] pr; logic st; integer k;
    na = m0_norm(a); nb = m0_norm(b);
    spa = na[50:50-1]; spb = nb[50:50-1]; s = na[50-2] ^ nb[50-2];
    if (spa == 2'd1 || spb == 2'd1) m0_mul = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 || spb == 2'd2) begin
      if ((spa == 2'd0 && na[36:1] == 0 && !na[0]) || (spb == 2'd0 && nb[36:1] == 0 && !nb[0]))
        m0_mul = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
      else m0_mul = m0_mkx(2'd2, s, 0, 0, 1'b0);
    end else begin
      pr = na[36:1] * nb[36:1];
      st = na[0] | nb[0];
      // keep the top XW bits of the product, the rest folds into sticky
      st = st | (pr[35:0] != 0);
      m0_mul = m0_mkx(2'd0, s, na[36+11:36+1] + nb[36+11:36+1] + 36, pr[2*36-1:36], st);
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
  function automatic [2*36+1:0] m0_udiv(input [35:0] a, input [35:0] dv);
    logic [36+1:0] r; logic [36:0] q; logic ge; integer i;
    r = {2'b0, a}; q = 0;
    for (i = 36; i >= 0; i = i - 1) begin
      ge = (r >= {2'b0, dv});
      r = ge ? r - {2'b0, dv} : r;
      q = {q[35:0], ge};
      if (i > 0) r = {r[36:0], 1'b0};
    end
    m0_udiv = {q, r[36:0]};
  endfunction
  // the exact product: {special[1:0], sign, exp[EW], sig[2XW]} (no sticky)
  function automatic [2*36+11+2:0] m0_mulx(input [50:0] a, input [50:0] b);
    logic [50:0] na, nb; logic [1:0] spa, spb, sp; logic s; logic [2*36-1:0] pr;
    na = m0_norm(a); nb = m0_norm(b);
    pr = na[36:1] * nb[36:1];
    spa = na[50:50-1]; spb = nb[50:50-1]; s = na[50-2] ^ nb[50-2];
    if (spa == 2'd1 || spb == 2'd1) sp = 2'd1;
    else if (spa == 2'd2 || spb == 2'd2)
      sp = ((spa == 2'd0 && na[36:1] == 0) || (spb == 2'd0 && nb[36:1] == 0)) ? 2'd1 : 2'd2;
    else sp = 2'd0;
    m0_mulx = {sp, s, na[36+11:36+1] + nb[36+11:36+1], pr};
  endfunction
  function automatic [50:0] m0_div(input [50:0] a, input [50:0] b);
    logic [50:0] na, nb; logic [1:0] spa, spb; logic s; logic [2*36+1:0] qr; logic [36:0] q, r;
    na = m0_norm(a); nb = m0_norm(b);
    spa = na[50:50-1]; spb = nb[50:50-1]; s = na[50-2] ^ nb[50-2];
    if (spa == 2'd1 || spb == 2'd1) m0_div = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 && spb == 2'd2) m0_div = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m0_div = m0_mkx(2'd2, s, 0, 0, 1'b0);
    else if (spb == 2'd2) m0_div = m0_mkx(2'd0, s, 0, 0, 1'b0);
    else if (nb[36:1] == 0 && !nb[0]) begin
      if (na[36:1] == 0 && !na[0]) m0_div = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
      else m0_div = m0_mkx(2'd2, s, 0, 0, 1'b0);
    end else if (na[36:1] == 0 && !na[0]) m0_div = m0_mkx(2'd0, s, 0, 0, 1'b0);
    else begin
      qr = m0_udiv(na[36:1], nb[36:1]);     // both normalized: nonzero finite
      q = qr[2*36+1:36+1]; r = qr[36:0];
      // q < 2^(XW+1): drop one bit when it carries
      if (q[36]) m0_div = m0_mkx(2'd0, s, na[36+11:36+1] - nb[36+11:36+1] - 36 + 1, q[36:1], (r != 0) | q[0] | na[0] | nb[0]);
      else m0_div = m0_mkx(2'd0, s, na[36+11:36+1] - nb[36+11:36+1] - 36, q[35:0], (r != 0) | na[0] | nb[0]);
    end
  endfunction
  function automatic [50:0] m0_sqrt(input [50:0] a);
    logic [50:0] na; logic [1:0] spa; logic signed [10:0] e; logic [36:0] m; logic [2*36+3:0] rad;
    logic [36+2:0] rem, trial; logic [36:0] root; logic ge; integer i;
    na = m0_norm(a); spa = na[50:50-1];
    if (spa == 2'd1) m0_sqrt = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m0_sqrt = na[50-2] ? m0_mkx(2'd1, 1'b0, 0, 0, 1'b0) : na;
    else if (na[36:1] == 0 && !na[0]) m0_sqrt = na;
    else if (na[50-2]) m0_sqrt = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else begin
      e = na[36+11:36+1];
      // value = m * 2^e with e even; radicand = m * 2^(2K): root = sqrt(m) * 2^K, XW+1 bits
      if (e[0]) begin m = {na[36:1], 1'b0}; e = e - 1; end
      else m = {1'b0, na[36:1]};
      rad = {{(36+3){1'b0}}, m} << 36;
      rem = 0; root = 0;
      for (i = 36; i >= 0; i = i - 1) begin
        rem = {rem[36:0], rad[2*i +: 2]};
        trial = {root, 2'b01};
        ge = (rem >= trial);                  // unconditional assignments, as in udiv
        rem = ge ? rem - trial : rem;
        root = {root[35:0], ge};
      end
      m0_sqrt = m0_mkx(2'd0, 1'b0, (e >>> 1) - 18 + 1, root[36:1], (rem != 0) | root[0] | na[0]);
    end
  endfunction
  // X ordering treats NaN as unordered and compares finite values by sign and magnitude
  function automatic m0_lt(input [50:0] a, input [50:0] b);
    logic [50:0] na, nb; logic za, zb, sa, sb, mag_lt; logic signed [10:0] ea, eb;
    na = m0_norm(a); nb = m0_norm(b);
    za = (na[36:1] == 0) && !na[0]; zb = (nb[36:1] == 0) && !nb[0];
    sa = na[50-2] && !za; sb = nb[50-2] && !zb;
    if (na[50:50-1] == 2'd1 || nb[50:50-1] == 2'd1) m0_lt = 1'b0;
    else if (na[50:50-1] == 2'd2 || nb[50:50-1] == 2'd2) begin
      if (na[50:50-1] == 2'd2 && nb[50:50-1] == 2'd2) m0_lt = na[50-2] && !nb[50-2];
      else if (na[50:50-1] == 2'd2) m0_lt = na[50-2];
      else m0_lt = !nb[50-2];
    end else if (za && zb) m0_lt = 1'b0;
    else if (sa != sb) m0_lt = sa;
    else begin
      ea = na[36+11:36+1]; eb = nb[36+11:36+1];
      if (za) mag_lt = 1'b1; else if (zb) mag_lt = 1'b0;
      else mag_lt = (ea < eb) || (ea == eb && (na[36:1] < nb[36:1] || (na[36:1] == nb[36:1] && !na[0] && nb[0])));
      m0_lt = sa ? !mag_lt && !(za && zb) && !m0_eq(na, nb) : mag_lt;
    end
  endfunction
  function automatic m0_eq(input [50:0] a, input [50:0] b);
    logic [50:0] na, nb; logic za, zb;
    na = m0_norm(a); nb = m0_norm(b);
    za = (na[36:1] == 0) && !na[0]; zb = (nb[36:1] == 0) && !nb[0];
    if (na[50:50-1] == 2'd1 || nb[50:50-1] == 2'd1) m0_eq = 1'b0;
    else if (na[50:50-1] == 2'd2 || nb[50:50-1] == 2'd2)
      m0_eq = (na[50:50-1] == nb[50:50-1]) && (na[50-2] == nb[50-2]);
    else if (za || zb) m0_eq = za && zb;
    else m0_eq = (na[50-2] == nb[50-2]) && (na[36+11:36+1] == nb[36+11:36+1]) && (na[36:1] == nb[36:1]) && (na[0] == nb[0]);
  endfunction

  // posit16_1 pattern -> V
  function automatic [30:0] m0_unpack_s(input [15:0] b, input daz);
    logic s; logic [15:0] mag; logic [14:0] body; logic first, done; integer run, i, rest_bits, e_bits, f_bits;
    logic signed [10:0] k, ex; logic [0:0] e; logic [15:0] f; logic [15:0] sig;
    s = b[15];
    if (b == 0) m0_unpack_s = {1'b0, m0_mkv(2'd0, 1'b0, 0, 0)};
    else if (b == {1'b1, {15{1'b0}}}) m0_unpack_s = {1'b0, m0_mkv(2'd1, 1'b0, 0, 0)};
    else begin
      mag = s ? (~b + 1'b1) : b;
      body = mag[14:0];
      first = body[14]; run = 0; done = 1'b0;
      for (i = 14; i >= 0; i = i - 1) begin
        if (!done) begin
          if (body[i] == first) run = run + 1; else done = 1'b1;
        end
      end
      k = first ? run - 1 : -run;
      rest_bits = 15 - run - 1;
      if (rest_bits < 0) rest_bits = 0;
      e_bits = (rest_bits < 1) ? rest_bits : 1;
      f_bits = rest_bits - 1; if (f_bits < 0) f_bits = 0;
      e = 0;
      if (e_bits > 0) e = (body >> (rest_bits - e_bits)) & ((1 << e_bits) - 1);
      e = e << (1 - e_bits);
      f = (f_bits > 0) ? (body & ((1 << f_bits) - 1)) : 0;
      // value = 2^(k*2^es + e) * (1 + f / 2^f_bits): sig has the hidden one at bit n-1
      sig = ({{(16-16){1'b0}}, 1'b1, {15{1'b0}}}) | (f << (15 - f_bits));
      ex = (k <<< 1) + e - 15;
      m0_unpack_s = {1'b0, m0_mkv(2'd0, s, ex, sig)};
    end
  endfunction

  // X -> posit16_1: frozen pattern rounding modes, clamped to maxpos/minpos
  function automatic [10+16-1:0] m0_pack_posit16_1(input [50:0] x0, input [2:0] rnd, input [7:0] word, input ftz);
    logic [50:0] x; logic [1:0] sp; logic s; logic signed [10:0] e, eu, k; logic [35:0] sig; logic st;
    logic [54:0] r; logic [14:0] topb; logic [54:0] dropped, halfv; integer rl, pos, i;
    logic [0:0] elow; logic [15:0] mag; logic clamp_hi, clamp_lo, up, inexact; logic [10-1:0] fl;
    x = m0_norm(x0); sp = x[50:50-1]; s = x[50-2]; sig = x[36:1]; st = x[0]; e = x[36+11:36+1];
    fl = 0; mag = 0; clamp_hi = 1'b0; clamp_lo = 1'b0; inexact = 1'b0;
    if (sp != 2'd0) begin fl[5] = 1'b1; m0_pack_posit16_1 = {fl, {1'b1, {15{1'b0}}}}; end
    else if (sig == 0 && !st) m0_pack_posit16_1 = {fl, {16{1'b0}}};
    else begin
      if (sig == 0) begin sig = 1; e = e - 36; end
      eu = e + 35;
      k = eu >>> 1;
      elow = eu & ((1 << 1) - 1);
      if (k > 14) clamp_hi = 1'b1;
      else if (k < -(14)) clamp_lo = 1'b1;
      if (clamp_hi) begin mag = {1'b0, {15{1'b1}}}; inexact = 1'b1; fl[2] = 1'b1; end
      else if (clamp_lo) begin mag = 1; inexact = 1'b1; fl[3] = 1'b1; end
      else begin
        // regime, then es bits, then the fraction (sig below its leading one), then sticky
        r = 0; pos = 55;
        if (k >= 0) begin rl = k + 2; for (i = 0; i < 16; i = i + 1) if (i < k + 1) begin pos = pos - 1; r[pos] = 1'b1; end
                    pos = pos - 1; r[pos] = 1'b0; end
        else begin rl = -k + 1; for (i = 0; i < 16; i = i + 1) if (i < -k) begin pos = pos - 1; r[pos] = 1'b0; end
                    pos = pos - 1; r[pos] = 1'b1; end
        for (i = 1 - 1; i >= 0; i = i - 1) begin pos = pos - 1; r[pos] = elow[i]; end
        for (i = 36 - 2; i >= 0; i = i - 1) begin pos = pos - 1; r[pos] = sig[i]; end
        r[0] = st;
        topb = r[54 -: 15];
        dropped = r & ((1 << (55 - 15)) - 1);
        halfv = 1 << (55 - 15 - 1);
        inexact = (dropped != 0);
        case (rnd)
          3'd1, 3'd2: up = inexact && s;
          3'd3: up = inexact && !s;
          default: up = (dropped > halfv) || (dropped == halfv && topb[0]);
        endcase
        mag = {1'b0, topb} + up;
        if (mag[15]) begin mag = {1'b0, {15{1'b1}}}; fl[2] = 1'b1; end
        if (k == 14 && inexact) fl[2] = 1'b1;
        if (mag == 0) begin mag = 1; fl[3] = 1'b1; end
      end
      if (inexact) fl[4] = 1'b1;
      m0_pack_posit16_1 = {fl, s ? (~mag + 1'b1) : mag};
    end
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
// STRUCTURE m0.l0.fp_adder kind=fp_adder slot=fp_adder mode=0 lane=0 width=16 format=posit16_1 ops=fadd sv=alu_core_u_m0_l0_fp_adder
// STRUCTURE m0.l0.posit_unit kind=posit_unit slot=posit_unit mode=0 lane=0 width=16 format=posit16_1 ops=fadd,fmul,fmin
// STRUCTURE m0.l0.fp_multiplier kind=fp_multiplier slot=fp_multiplier mode=0 lane=0 width=16 format=posit16_1 ops=fmul sv=alu_core_u_m0_l0_fp_multiplier
// STRUCTURE m0.l0.fp_comparator kind=fp_comparator slot=fp_comparator mode=0 lane=0 width=16 format=posit16_1 ops=fmin sv=alu_core_u_m0_l0_fp_comparator
// STRUCTURE m1.l0.adder kind=adder slot=adder mode=1 lane=0 width=8 format=int8_twos_complement ops=add sv=alu_core_u_m1_l0_adder
// STRUCTURE m1.l1.adder kind=adder slot=adder mode=1 lane=1 width=8 format=int8_twos_complement ops=add sv=alu_core_u_m1_l1_adder
// STRUCTURE m1.l0.multiplier kind=multiplier slot=multiplier mode=1 lane=0 width=8 format=int8_twos_complement ops=mul sv=alu_core_u_m1_l0_multiplier
// STRUCTURE m1.l1.multiplier kind=multiplier slot=multiplier mode=1 lane=1 width=8 format=int8_twos_complement ops=mul sv=alu_core_u_m1_l1_multiplier
// STRUCTURE m1.l0.comparator kind=comparator slot=comparator mode=1 lane=0 width=8 format=int8_twos_complement ops=min sv=alu_core_u_m1_l0_comparator
// STRUCTURE m1.l1.comparator kind=comparator slot=comparator mode=1 lane=1 width=8 format=int8_twos_complement ops=min sv=alu_core_u_m1_l1_comparator
// ADIR-END
module alu_core (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [0:0] mode,
  output logic [15:0] y
);
  // alu_core: behavioral reference derived from the instance (modes 1xposit16_1, 2xint8_twos_complement; ops add, mul, min, fadd, fmul, fmin). Every (mode, op) pair computes the verify layer's exact semantics.
  // HIERARCHY: 9 physical structure modules instantiated by alu_core, built from 6 lane modules (one per mode and kind, parameter LANE) and 2 packages of engine functions (one per mode); a float mode's datapath is split into an unpacker (the xa/xb/den buses), the arithmetic and converter structures (unrounded results on the x bus) and a rounder (y and the flags); 0 misc lane modules and 0 block-conversion group modules
  // UNIT m0.l0.fp_adder module=alu_core_u_m0_l0_fp_adder kind=fp_adder members=m0.l0.fp_adder
  // UNIT m0.l0.fp_multiplier module=alu_core_u_m0_l0_fp_multiplier kind=fp_multiplier members=m0.l0.fp_multiplier
  // UNIT m0.l0.fp_comparator module=alu_core_u_m0_l0_fp_comparator kind=fp_comparator members=m0.l0.fp_comparator
  // UNIT m1.l0.adder module=alu_core_u_m1_l0_adder kind=adder members=m1.l0.adder
  // UNIT m1.l1.adder module=alu_core_u_m1_l1_adder kind=adder members=m1.l1.adder
  // UNIT m1.l0.multiplier module=alu_core_u_m1_l0_multiplier kind=multiplier members=m1.l0.multiplier
  // UNIT m1.l1.multiplier module=alu_core_u_m1_l1_multiplier kind=multiplier members=m1.l1.multiplier
  // UNIT m1.l0.comparator module=alu_core_u_m1_l0_comparator kind=comparator members=m1.l0.comparator
  // UNIT m1.l1.comparator module=alu_core_u_m1_l1_comparator kind=comparator members=m1.l1.comparator
  // // STRUCTURE m0.l0.fp_adder kind=fp_adder slot=fp_adder mode=0 lane=0 width=16 format=posit16_1 ops=fadd sv=alu_core_u_m0_l0_fp_adder
  // // STRUCTURE m0.l0.posit_unit kind=posit_unit slot=posit_unit mode=0 lane=0 width=16 format=posit16_1 ops=fadd,fmul,fmin
  // // STRUCTURE m0.l0.fp_multiplier kind=fp_multiplier slot=fp_multiplier mode=0 lane=0 width=16 format=posit16_1 ops=fmul sv=alu_core_u_m0_l0_fp_multiplier
  // // STRUCTURE m0.l0.fp_comparator kind=fp_comparator slot=fp_comparator mode=0 lane=0 width=16 format=posit16_1 ops=fmin sv=alu_core_u_m0_l0_fp_comparator
  // // STRUCTURE m1.l0.adder kind=adder slot=adder mode=1 lane=0 width=8 format=int8_twos_complement ops=add sv=alu_core_u_m1_l0_adder
  // // STRUCTURE m1.l1.adder kind=adder slot=adder mode=1 lane=1 width=8 format=int8_twos_complement ops=add sv=alu_core_u_m1_l1_adder
  // // STRUCTURE m1.l0.multiplier kind=multiplier slot=multiplier mode=1 lane=0 width=8 format=int8_twos_complement ops=mul sv=alu_core_u_m1_l0_multiplier
  // // STRUCTURE m1.l1.multiplier kind=multiplier slot=multiplier mode=1 lane=1 width=8 format=int8_twos_complement ops=mul sv=alu_core_u_m1_l1_multiplier
  // // STRUCTURE m1.l0.comparator kind=comparator slot=comparator mode=1 lane=0 width=8 format=int8_twos_complement ops=min sv=alu_core_u_m1_l0_comparator
  // // STRUCTURE m1.l1.comparator kind=comparator slot=comparator mode=1 lane=1 width=8 format=int8_twos_complement ops=min sv=alu_core_u_m1_l1_comparator
  // LIBRARY: fam_add_partitioned_w16_8_carry_kill_gate_0cc88441ac18, fam_adder_ripple_carry, fam_adder_ripple_chunk, fam_cmp_prefix_comparator, fam_count_lzd_pair_cell_binary_count_vflat_w15, fam_count_lzd_pair_cell_binary_count_vflat_w36, fam_fp_add_single_path_x36e11s16_p9d459d224988, fam_fp_cmp_integer_compare_on_bits_x36e11s16_pa61fc99a71d5, fam_fp_mul_sig_mul_then_round_x36e11s16_pbd766efe148c, fam_incr_prefix_and, fam_mul_behavioral_star_w16_u_pfc463c41, fam_mul_behavioral_star_w8_s, fam_posit_decode_posit_adder_multiplier_lzc_plus_shifter_sign_magnitude_posit16_1_x36e11s16_14e320560f9f, fam_posit_encode_posit_adder_multiplier_sign_magnitude_posit16_1_x36e11s16_14e320560f9f, fam_shift_barrel_mux_tree, fam_shift_keep_mask, fam_shift_stage (chialu.targets.rtl.families: the modules of the declared families the lane modules instantiate; their text follows the generated modules)
  logic [2:0] rnd_sel;
  logic [2:0] rnd;
  logic daz;
  logic ftz;
  logic dual;
  logic [15:0] y_m0_m0_l0_fp_adder;
  logic [19:0] fl_m0_m0_l0_fp_adder;
  logic [15:0] y_m0_m0_l0_fp_multiplier;
  logic [19:0] fl_m0_m0_l0_fp_multiplier;
  logic [15:0] y_m0_m0_l0_fp_comparator;
  logic [19:0] fl_m0_m0_l0_fp_comparator;
  logic [15:0] y_m0;
  logic [19:0] fl_m0;
  logic [15:0] y_m1_m1_l0_adder;
  logic [19:0] fl_m1_m1_l0_adder;
  logic [15:0] y_m1_m1_l1_adder;
  logic [19:0] fl_m1_m1_l1_adder;
  logic [15:0] y_m1_m1_l0_multiplier;
  logic [19:0] fl_m1_m1_l0_multiplier;
  logic [15:0] y_m1_m1_l1_multiplier;
  logic [19:0] fl_m1_m1_l1_multiplier;
  logic [15:0] y_m1_m1_l0_comparator;
  logic [19:0] fl_m1_m1_l0_comparator;
  logic [15:0] y_m1_m1_l1_comparator;
  logic [19:0] fl_m1_m1_l1_comparator;
  logic [15:0] y_m1;
  logic [19:0] fl_m1;
  logic [19:0] fl_all;
  assign rnd_sel = 3'd0;
  assign rnd = rnd_sel;
  assign daz = 1'b0;
  assign ftz = 1'b0;
  assign dual = 1'b0;
  assign y_m0 = y_m0_m0_l0_fp_adder | y_m0_m0_l0_fp_multiplier | y_m0_m0_l0_fp_comparator;
  assign fl_m0 = fl_m0_m0_l0_fp_adder | fl_m0_m0_l0_fp_multiplier | fl_m0_m0_l0_fp_comparator;
  assign y_m1 = y_m1_m1_l0_adder | y_m1_m1_l1_adder | y_m1_m1_l0_multiplier | y_m1_m1_l1_multiplier | y_m1_m1_l0_comparator | y_m1_m1_l1_comparator;
  assign fl_m1 = fl_m1_m1_l0_adder | fl_m1_m1_l1_adder | fl_m1_m1_l0_multiplier | fl_m1_m1_l1_multiplier | fl_m1_m1_l0_comparator | fl_m1_m1_l1_comparator;
  alu_core_u_m0_l0_fp_adder u_m0_l0_fp_adder (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_m0_l0_fp_adder), .fl_m0(fl_m0_m0_l0_fp_adder));
  alu_core_u_m0_l0_fp_multiplier u_m0_l0_fp_multiplier (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_m0_l0_fp_multiplier), .fl_m0(fl_m0_m0_l0_fp_multiplier));
  alu_core_u_m0_l0_fp_comparator u_m0_l0_fp_comparator (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_m0_l0_fp_comparator), .fl_m0(fl_m0_m0_l0_fp_comparator));
  alu_core_u_m1_l0_adder u_m1_l0_adder (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l0_adder), .fl_m1(fl_m1_m1_l0_adder));
  alu_core_u_m1_l1_adder u_m1_l1_adder (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l1_adder), .fl_m1(fl_m1_m1_l1_adder));
  alu_core_u_m1_l0_multiplier u_m1_l0_multiplier (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l0_multiplier), .fl_m1(fl_m1_m1_l0_multiplier));
  alu_core_u_m1_l1_multiplier u_m1_l1_multiplier (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l1_multiplier), .fl_m1(fl_m1_m1_l1_multiplier));
  alu_core_u_m1_l0_comparator u_m1_l0_comparator (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l0_comparator), .fl_m1(fl_m1_m1_l0_comparator));
  alu_core_u_m1_l1_comparator u_m1_l1_comparator (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_m1_l1_comparator), .fl_m1(fl_m1_m1_l1_comparator));
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
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m0,
  output logic [19:0] fl_m0
);
  // alu_core_m0_fp_adder: lane LANE of mode 0 (posit16_1) for the fp_adder ops fadd; the result buses are the mode's, with only this lane's bits written
  import alu_core_m0_pkg::*;
  logic d_m0;
  logic [15:0] m0_aLANE;
  logic [15:0] m0_bLANE;
  logic [30:0] m0_uaLANE;
  logic [30:0] m0_ubLANE;
  logic [50:0] m0_xa [0:0];
  logic m0_dena [0:0];
  logic [50:0] m0_xb [0:0];
  logic m0_denb [0:0];
  logic [50:0] m0_pe_xLANE;
  logic [7:0] m0_pe_wLANE;
  logic [9:0] m0_pe_flLANE;
  logic [15:0] m0_pe_bLANE;
  logic [50:0] m0_fa_xaLANE;
  logic [50:0] m0_fa_xbLANE;
  logic m0_fa_subLANE;
  logic [50:0] m0_fa_yLANE;
  logic [25:0] m0_o3t0_LANE;
  logic [50:0] m0_o3t0_LANE_x;
  assign m0_aLANE = a[(LANE*16) +: 16];
  assign m0_bLANE = b[(LANE*16) +: 16];
  // structure core.posit_unit.m0: family posit_adder_multiplier realized by the library module fam_posit_decode_posit_adder_multiplier_lzc_plus_shifter_sign_magnitude_posit16_1_x36e11s16_14e320560f9f (the decoder)
  fam_posit_decode_posit_adder_multiplier_lzc_plus_shifter_sign_magnitude_posit16_1_x36e11s16_14e320560f9f u_m0_unpack_aLANE (.b(m0_aLANE), .daz(daz), .u(m0_uaLANE));
  // structure core.posit_unit.m0: family posit_adder_multiplier realized by the library module fam_posit_decode_posit_adder_multiplier_lzc_plus_shifter_sign_magnitude_posit16_1_x36e11s16_14e320560f9f (the decoder)
  fam_posit_decode_posit_adder_multiplier_lzc_plus_shifter_sign_magnitude_posit16_1_x36e11s16_14e320560f9f u_m0_unpack_bLANE (.b(m0_bLANE), .daz(daz), .u(m0_ubLANE));
  assign m0_xa[LANE] = m0_x(m0_uaLANE[29:0]);
  assign m0_dena[LANE] = m0_uaLANE[30];
  assign m0_xb[LANE] = m0_x(m0_ubLANE[29:0]);
  assign m0_denb[LANE] = m0_ubLANE[30];
  // structure core.posit_unit.m0: family posit_adder_multiplier realized by the library module fam_posit_encode_posit_adder_multiplier_sign_magnitude_posit16_1_x36e11s16_14e320560f9f (the encoder)
  fam_posit_encode_posit_adder_multiplier_sign_magnitude_posit16_1_x36e11s16_14e320560f9f u_m0_pencLANE (.x(m0_pe_xLANE), .rnd(rnd), .word(m0_pe_wLANE), .ftz(ftz), .fl(m0_pe_flLANE), .bits(m0_pe_bLANE));
  // structure core.fp_adder.m0: family single_path realized by the library module fam_fp_add_single_path_x36e11s16_p9d459d224988
  fam_fp_add_single_path_x36e11s16_p9d459d224988 u_m0_faddLANE (.xa(m0_fa_xaLANE), .xb(m0_fa_xbLANE), .sub(m0_fa_subLANE), .y(m0_fa_yLANE));
  always_comb begin
    y_m0 = '0; d_m0 = '0; fl_m0 = '0;
    m0_pe_xLANE = 'x; m0_pe_wLANE = 'x; m0_fa_xaLANE = 'x; m0_fa_xbLANE = 'x; m0_fa_subLANE = 'x; m0_o3t0_LANE = 'x;
    m0_o3t0_LANE_x = 'x;
    case (op)
      3'd3: begin
        m0_fa_xaLANE = m0_xa[LANE]; m0_fa_xbLANE = m0_xb[LANE]; m0_fa_subLANE = 1'b0; m0_o3t0_LANE_x = m0_fa_yLANE;
        m0_pe_xLANE = m0_o3t0_LANE_x; m0_pe_wLANE = 8'd0; m0_o3t0_LANE = {m0_pe_flLANE, m0_pe_bLANE};
        y_m0[((LANE*16)+0) +: 16] = m0_o3t0_LANE[15:0];
        fl_m0[(0+LANE)*10 +: 10] = m0_o3t0_LANE[25:16] | ((m0_xa[LANE][50:49] == 2'd1) || (m0_xb[LANE][50:49] == 2'd1) ? (10'd1 << 0) : 10'd0);
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m0_fp_comparator #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m0,
  output logic [19:0] fl_m0
);
  // alu_core_m0_fp_comparator: lane LANE of mode 0 (posit16_1) for the fp_comparator ops fmin; the result buses are the mode's, with only this lane's bits written
  import alu_core_m0_pkg::*;
  logic d_m0;
  logic [15:0] m0_aLANE;
  logic [15:0] m0_bLANE;
  logic [30:0] m0_uaLANE;
  logic [30:0] m0_ubLANE;
  logic [50:0] m0_xa [0:0];
  logic m0_dena [0:0];
  logic [50:0] m0_xb [0:0];
  logic m0_denb [0:0];
  logic [50:0] m0_pe_xLANE;
  logic [7:0] m0_pe_wLANE;
  logic [9:0] m0_pe_flLANE;
  logic [15:0] m0_pe_bLANE;
  logic [50:0] m0_fc_xaLANE;
  logic [50:0] m0_fc_xbLANE;
  logic m0_fc_ltLANE;
  logic m0_fc_eqLANE;
  assign m0_aLANE = a[(LANE*16) +: 16];
  assign m0_bLANE = b[(LANE*16) +: 16];
  // structure core.posit_unit.m0: family posit_adder_multiplier realized by the library module fam_posit_decode_posit_adder_multiplier_lzc_plus_shifter_sign_magnitude_posit16_1_x36e11s16_14e320560f9f (the decoder)
  fam_posit_decode_posit_adder_multiplier_lzc_plus_shifter_sign_magnitude_posit16_1_x36e11s16_14e320560f9f u_m0_unpack_aLANE (.b(m0_aLANE), .daz(daz), .u(m0_uaLANE));
  // structure core.posit_unit.m0: family posit_adder_multiplier realized by the library module fam_posit_decode_posit_adder_multiplier_lzc_plus_shifter_sign_magnitude_posit16_1_x36e11s16_14e320560f9f (the decoder)
  fam_posit_decode_posit_adder_multiplier_lzc_plus_shifter_sign_magnitude_posit16_1_x36e11s16_14e320560f9f u_m0_unpack_bLANE (.b(m0_bLANE), .daz(daz), .u(m0_ubLANE));
  assign m0_xa[LANE] = m0_x(m0_uaLANE[29:0]);
  assign m0_dena[LANE] = m0_uaLANE[30];
  assign m0_xb[LANE] = m0_x(m0_ubLANE[29:0]);
  assign m0_denb[LANE] = m0_ubLANE[30];
  // structure core.posit_unit.m0: family posit_adder_multiplier realized by the library module fam_posit_encode_posit_adder_multiplier_sign_magnitude_posit16_1_x36e11s16_14e320560f9f (the encoder)
  fam_posit_encode_posit_adder_multiplier_sign_magnitude_posit16_1_x36e11s16_14e320560f9f u_m0_pencLANE (.x(m0_pe_xLANE), .rnd(rnd), .word(m0_pe_wLANE), .ftz(ftz), .fl(m0_pe_flLANE), .bits(m0_pe_bLANE));
  // structure core.fp_comparator.m0: family integer_compare_on_bits realized by the library module fam_fp_cmp_integer_compare_on_bits_x36e11s16_pa61fc99a71d5
  fam_fp_cmp_integer_compare_on_bits_x36e11s16_pa61fc99a71d5 u_m0_fcmpLANE (.xa(m0_fc_xaLANE), .xb(m0_fc_xbLANE), .lt(m0_fc_ltLANE), .eq(m0_fc_eqLANE));
  always_comb begin
    y_m0 = '0; d_m0 = '0; fl_m0 = '0;
    m0_pe_xLANE = 'x; m0_pe_wLANE = 'x; m0_fc_xaLANE = 'x; m0_fc_xbLANE = 'x;
    case (op)
      3'd5: begin
        m0_fc_xaLANE = m0_xa[LANE]; m0_fc_xbLANE = m0_xb[LANE];
        y_m0[((LANE*16)+0) +: 16] = (((m0_xa[LANE][50:49] == 2'd1) || (m0_xb[LANE][50:49] == 2'd1)) ? (($signed(m0_aLANE) <= $signed(m0_bLANE))) : (m0_fc_ltLANE || m0_fc_eqLANE)) ? m0_aLANE : m0_bLANE;
        fl_m0[(0+LANE)*10 +: 10] = 10'd0;
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m0_fp_multiplier #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m0,
  output logic [19:0] fl_m0
);
  // alu_core_m0_fp_multiplier: lane LANE of mode 0 (posit16_1) for the fp_multiplier ops fmul; the result buses are the mode's, with only this lane's bits written
  import alu_core_m0_pkg::*;
  logic d_m0;
  logic [15:0] m0_aLANE;
  logic [15:0] m0_bLANE;
  logic [30:0] m0_uaLANE;
  logic [30:0] m0_ubLANE;
  logic [50:0] m0_xa [0:0];
  logic m0_dena [0:0];
  logic [50:0] m0_xb [0:0];
  logic m0_denb [0:0];
  logic [50:0] m0_pe_xLANE;
  logic [7:0] m0_pe_wLANE;
  logic [9:0] m0_pe_flLANE;
  logic [15:0] m0_pe_bLANE;
  logic [50:0] m0_fm_xaLANE;
  logic [50:0] m0_fm_xbLANE;
  logic [50:0] m0_fm_yLANE;
  logic [25:0] m0_o4t0_LANE;
  logic [50:0] m0_o4t0_LANE_x;
  assign m0_aLANE = a[(LANE*16) +: 16];
  assign m0_bLANE = b[(LANE*16) +: 16];
  // structure core.posit_unit.m0: family posit_adder_multiplier realized by the library module fam_posit_decode_posit_adder_multiplier_lzc_plus_shifter_sign_magnitude_posit16_1_x36e11s16_14e320560f9f (the decoder)
  fam_posit_decode_posit_adder_multiplier_lzc_plus_shifter_sign_magnitude_posit16_1_x36e11s16_14e320560f9f u_m0_unpack_aLANE (.b(m0_aLANE), .daz(daz), .u(m0_uaLANE));
  // structure core.posit_unit.m0: family posit_adder_multiplier realized by the library module fam_posit_decode_posit_adder_multiplier_lzc_plus_shifter_sign_magnitude_posit16_1_x36e11s16_14e320560f9f (the decoder)
  fam_posit_decode_posit_adder_multiplier_lzc_plus_shifter_sign_magnitude_posit16_1_x36e11s16_14e320560f9f u_m0_unpack_bLANE (.b(m0_bLANE), .daz(daz), .u(m0_ubLANE));
  assign m0_xa[LANE] = m0_x(m0_uaLANE[29:0]);
  assign m0_dena[LANE] = m0_uaLANE[30];
  assign m0_xb[LANE] = m0_x(m0_ubLANE[29:0]);
  assign m0_denb[LANE] = m0_ubLANE[30];
  // structure core.posit_unit.m0: family posit_adder_multiplier realized by the library module fam_posit_encode_posit_adder_multiplier_sign_magnitude_posit16_1_x36e11s16_14e320560f9f (the encoder)
  fam_posit_encode_posit_adder_multiplier_sign_magnitude_posit16_1_x36e11s16_14e320560f9f u_m0_pencLANE (.x(m0_pe_xLANE), .rnd(rnd), .word(m0_pe_wLANE), .ftz(ftz), .fl(m0_pe_flLANE), .bits(m0_pe_bLANE));
  // structure core.fp_multiplier.m0: family sig_mul_then_round realized by the library module fam_fp_mul_sig_mul_then_round_x36e11s16_pbd766efe148c
  fam_fp_mul_sig_mul_then_round_x36e11s16_pbd766efe148c u_m0_fmulLANE (.xa(m0_fm_xaLANE), .xb(m0_fm_xbLANE), .y(m0_fm_yLANE));
  always_comb begin
    y_m0 = '0; d_m0 = '0; fl_m0 = '0;
    m0_pe_xLANE = 'x; m0_pe_wLANE = 'x; m0_fm_xaLANE = 'x; m0_fm_xbLANE = 'x; m0_o4t0_LANE = 'x; m0_o4t0_LANE_x = 'x;
    case (op)
      3'd4: begin
        m0_fm_xaLANE = m0_xa[LANE]; m0_fm_xbLANE = m0_xb[LANE]; m0_o4t0_LANE_x = m0_fm_yLANE;
        m0_pe_xLANE = m0_o4t0_LANE_x; m0_pe_wLANE = 8'd0; m0_o4t0_LANE = {m0_pe_flLANE, m0_pe_bLANE};
        y_m0[((LANE*16)+0) +: 16] = m0_o4t0_LANE[15:0];
        fl_m0[(0+LANE)*10 +: 10] = m0_o4t0_LANE[25:16] | ((m0_xa[LANE][50:49] == 2'd1) || (m0_xb[LANE][50:49] == 2'd1) ? (10'd1 << 0) : 10'd0);
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m1_adder_sh #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m1,
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
      3'd0: begin
        pc_a_m1[(LANE)*8 +: 8] = m1_aLANE; pc_b_m1[(LANE)*8 +: 8] = m1_bLANE; pc_cin_m1[(LANE)*1] = 1'b0;
        m1_o0ex0_LANE = $signed({(m1_aLANE[7] ^ m1_bLANE[7] ^ m1_add_coutLANE), m1_add_sLANE});
        y_m1[((LANE*8)+0) +: 8] = m1_wrap(m1_o0ex0_LANE);
        fl_m1[(0+LANE)*10 +: 10] = (((m1_aLANE[7] ^ m1_bLANE[7] ^ m1_add_coutLANE) ^ m1_add_sLANE[7]) ? (10'd1 << 8) : 10'd0) | (((m1_aLANE[7] ^ m1_bLANE[7] ^ m1_add_coutLANE) ^ m1_add_sLANE[7]) ? (10'd1 << 2) : 10'd0) | (m1_add_coutLANE ? (10'd1 << 7) : 10'd0);
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m1_comparator #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m1,
  output logic [19:0] fl_m1
);
  // alu_core_m1_comparator: lane LANE of mode 1 (int8_twos_complement) for the comparator ops min; the result buses are the mode's, with only this lane's bits written
  import alu_core_m1_pkg::*;
  logic d_m1;
  logic [7:0] m1_aLANE;
  logic [7:0] m1_bLANE;
  logic [33:0] m1_xa [0:1];
  logic [33:0] m1_xb [0:1];
  logic signed [8:0] m1_vaLANE;
  logic signed [8:0] m1_vbLANE;
  logic [7:0] m1_cmp_aLANE;
  logic [7:0] m1_cmp_bLANE;
  logic m1_cmp_ltLANE;
  logic m1_cmp_eqLANE;
  logic signed [18:0] m1_o2ex0_LANE;
  assign m1_aLANE = a[(LANE*8) +: 8];
  assign m1_bLANE = b[(LANE*8) +: 8];
  assign m1_xa[LANE] = m1_x(m1_unpack_s(m1_aLANE, 1'b0));
  assign m1_xb[LANE] = m1_x(m1_unpack_s(m1_bLANE, 1'b0));
  assign m1_vaLANE = {m1_aLANE[7], m1_aLANE};
  assign m1_vbLANE = {m1_bLANE[7], m1_bLANE};
  // structure core.comparator.m1: family prefix_comparator realized by the library module fam_cmp_prefix_comparator
  fam_cmp_prefix_comparator #(.W(8), .SIGNED(1), .STRUCTURE(0), .RADIX(2)) u_m1_cmpLANE (.a(m1_cmp_aLANE), .b(m1_cmp_bLANE), .lt(m1_cmp_ltLANE), .eq(m1_cmp_eqLANE));
  always_comb begin
    y_m1 = '0; d_m1 = '0; fl_m1 = '0;
    m1_cmp_aLANE = 'x; m1_cmp_bLANE = 'x; m1_o2ex0_LANE = 'x;
    case (op)
      3'd2: begin
        m1_cmp_aLANE = m1_aLANE; m1_cmp_bLANE = m1_bLANE;
        y_m1[((LANE*8)+0) +: 8] = (m1_cmp_ltLANE | m1_cmp_eqLANE) ? m1_aLANE : m1_bLANE;
      end
      default: ;
    endcase
  end
endmodule

module alu_core_m1_multiplier #(parameter int LANE = 0) (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m1,
  output logic [19:0] fl_m1
);
  // alu_core_m1_multiplier: lane LANE of mode 1 (int8_twos_complement) for the multiplier ops mul; the result buses are the mode's, with only this lane's bits written
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
  assign m1_aLANE = a[(LANE*8) +: 8];
  assign m1_bLANE = b[(LANE*8) +: 8];
  assign m1_xa[LANE] = m1_x(m1_unpack_s(m1_aLANE, 1'b0));
  assign m1_xb[LANE] = m1_x(m1_unpack_s(m1_bLANE, 1'b0));
  assign m1_vaLANE = {m1_aLANE[7], m1_aLANE};
  assign m1_vbLANE = {m1_bLANE[7], m1_bLANE};
  // structure core.multiplier.m1: family behavioral_star realized by the library module fam_mul_behavioral_star_w8_s
  fam_mul_behavioral_star_w8_s u_m1_mulLANE (.a(m1_mul_aLANE), .b(m1_mul_bLANE), .p(m1_mul_pLANE));
  always_comb begin
    y_m1 = '0; d_m1 = '0; fl_m1 = '0;
    m1_mul_aLANE = 'x; m1_mul_bLANE = 'x; m1_o1ex0_LANE = 'x;
    case (op)
      3'd1: begin
        m1_mul_aLANE = m1_aLANE; m1_mul_bLANE = m1_bLANE;
        m1_o1ex0_LANE = $signed({{3{m1_mul_pLANE[15]}}, m1_mul_pLANE});
        y_m1[((LANE*8)+0) +: 8] = m1_wrap(m1_o1ex0_LANE);
        fl_m1[(0+LANE)*10 +: 10] = (m1_o1ex0_LANE > 19'sd127 || m1_o1ex0_LANE < -19'sd128 ? (10'd1 << 8) : 10'd0) | (m1_o1ex0_LANE > 19'sd127 || m1_o1ex0_LANE < -19'sd128 ? (10'd1 << 2) : 10'd0);
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
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m0,
  output logic [19:0] fl_m0
);
  // alu_core_u_m0_l0_fp_adder: physical structure `m0.l0.fp_adder` (kind fp_adder, slot fp_adder); realizes m0.l0.fp_adder: fp_adder, mode 0 lane 0, posit16_1, ops fadd
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [15:0] y_m0_l0;
  logic [19:0] fl_m0_l0;
  alu_core_m0_fp_adder #(.LANE(0)) u_m0_l0 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_l0), .fl_m0(fl_m0_l0));
  assign y_m0 = y_m0_l0;
  assign fl_m0 = fl_m0_l0;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m0_l0_fp_multiplier
// EVOLVE-BLOCK-START
module alu_core_u_m0_l0_fp_multiplier (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m0,
  output logic [19:0] fl_m0
);
  // alu_core_u_m0_l0_fp_multiplier: physical structure `m0.l0.fp_multiplier` (kind fp_multiplier, slot fp_multiplier); realizes m0.l0.fp_multiplier: fp_multiplier, mode 0 lane 0, posit16_1, ops fmul
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [15:0] y_m0_l0;
  logic [19:0] fl_m0_l0;
  alu_core_m0_fp_multiplier #(.LANE(0)) u_m0_l0 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_l0), .fl_m0(fl_m0_l0));
  assign y_m0 = y_m0_l0;
  assign fl_m0 = fl_m0_l0;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m0_l0_fp_comparator
// EVOLVE-BLOCK-START
module alu_core_u_m0_l0_fp_comparator (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m0,
  output logic [19:0] fl_m0
);
  // alu_core_u_m0_l0_fp_comparator: physical structure `m0.l0.fp_comparator` (kind fp_comparator, slot fp_comparator); realizes m0.l0.fp_comparator: fp_comparator, mode 0 lane 0, posit16_1, ops fmin
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [15:0] y_m0_l0;
  logic [19:0] fl_m0_l0;
  alu_core_m0_fp_comparator #(.LANE(0)) u_m0_l0 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m0(y_m0_l0), .fl_m0(fl_m0_l0));
  assign y_m0 = y_m0_l0;
  assign fl_m0 = fl_m0_l0;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l0_adder
// EVOLVE-BLOCK-START
module alu_core_u_m1_l0_adder (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m1,
  output logic [19:0] fl_m1
);
  // alu_core_u_m1_l0_adder: physical structure `m1.l0.adder` (kind adder, slot adder); realizes m1.l0.adder: adder, mode 1 lane 0, int8_twos_complement, ops add
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [15:0] pc_a_m1;
  logic [15:0] pc_b_m1;
  logic [1:0] pc_cin_m1;
  logic [15:0] pc_s_m1;
  logic [1:0] pc_co_m1;
  logic [15:0] y_m1_l0;
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
  fam_add_partitioned_w16_8_carry_kill_gate_0cc88441ac18 u_part (.a(pc_a), .b(pc_b), .cin(pc_cin), .sel(pc_sel), .s(pc_s), .cout(pc_co));
  assign pc_s_m1 = pc_s;
  assign pc_co_m1 = pc_co;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l1_adder
// EVOLVE-BLOCK-START
module alu_core_u_m1_l1_adder (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m1,
  output logic [19:0] fl_m1
);
  // alu_core_u_m1_l1_adder: physical structure `m1.l1.adder` (kind adder, slot adder); realizes m1.l1.adder: adder, mode 1 lane 1, int8_twos_complement, ops add
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [15:0] pc_a_m1;
  logic [15:0] pc_b_m1;
  logic [1:0] pc_cin_m1;
  logic [15:0] pc_s_m1;
  logic [1:0] pc_co_m1;
  logic [15:0] y_m1_l1;
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
  fam_add_partitioned_w16_8_carry_kill_gate_0cc88441ac18 u_part (.a(pc_a), .b(pc_b), .cin(pc_cin), .sel(pc_sel), .s(pc_s), .cout(pc_co));
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
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m1,
  output logic [19:0] fl_m1
);
  // alu_core_u_m1_l0_multiplier: physical structure `m1.l0.multiplier` (kind multiplier, slot multiplier); realizes m1.l0.multiplier: multiplier, mode 1 lane 0, int8_twos_complement, ops mul
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [15:0] y_m1_l0;
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
  input  logic [2:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m1,
  output logic [19:0] fl_m1
);
  // alu_core_u_m1_l1_multiplier: physical structure `m1.l1.multiplier` (kind multiplier, slot multiplier); realizes m1.l1.multiplier: multiplier, mode 1 lane 1, int8_twos_complement, ops mul
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [15:0] y_m1_l1;
  logic [19:0] fl_m1_l1;
  alu_core_m1_multiplier #(.LANE(1)) u_m1_l1 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_l1), .fl_m1(fl_m1_l1));
  assign y_m1 = y_m1_l1;
  assign fl_m1 = fl_m1_l1;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l0_comparator
// EVOLVE-BLOCK-START
module alu_core_u_m1_l0_comparator (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m1,
  output logic [19:0] fl_m1
);
  // alu_core_u_m1_l0_comparator: physical structure `m1.l0.comparator` (kind comparator, slot comparator); realizes m1.l0.comparator: comparator, mode 1 lane 0, int8_twos_complement, ops min
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [15:0] y_m1_l0;
  logic [19:0] fl_m1_l0;
  alu_core_m1_comparator #(.LANE(0)) u_m1_l0 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_l0), .fl_m1(fl_m1_l0));
  assign y_m1 = y_m1_l0;
  assign fl_m1 = fl_m1_l0;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER m1_l1_comparator
// EVOLVE-BLOCK-START
module alu_core_u_m1_l1_comparator (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0] op,
  input  logic [0:0] mode,
  input  logic [2:0] rnd,
  input  logic [0:0] daz,
  input  logic [0:0] ftz,
  input  logic [0:0] dual,
  output logic [15:0] y_m1,
  output logic [19:0] fl_m1
);
  // alu_core_u_m1_l1_comparator: physical structure `m1.l1.comparator` (kind comparator, slot comparator); realizes m1.l1.comparator: comparator, mode 1 lane 1, int8_twos_complement, ops min
  // the seed's body: one instance of the lane module per lane, defined outside the mutable regions; the lane module instantiates the family library's module of the declared family where the library has one (a comment names it) and is behavioral otherwise; a rewrite replaces these instances with the family's logic inside this module, keeps the module's name and ports, and may share one datapath among the lanes
  logic [15:0] y_m1_l1;
  logic [19:0] fl_m1_l1;
  alu_core_m1_comparator #(.LANE(1)) u_m1_l1 (.a(a), .b(b), .op(op), .mode(mode), .rnd(rnd), .daz(daz), .ftz(ftz), .dual(dual), .y_m1(y_m1_l1), .fl_m1(fl_m1_l1));
  assign y_m1 = y_m1_l1;
  assign fl_m1 = fl_m1_l1;
endmodule
// EVOLVE-BLOCK-END
// ADIR-MEMBER library
// ---- the family library modules the lane modules instantiate (chialu/targets/rtl/families; fixed text, replaced by editing the instances)
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



// lzd_cell_tree (pair_cell, binary_count, valid flags flat): the leading zeros of a 15-bit word
module fam_count_lzd_pair_cell_binary_count_vflat_w15 (input logic [14:0] a, output logic [3:0] n);
  logic v0_0; assign v0_0 = a[14] | a[13];
  logic p0_0; assign p0_0 = ~a[14];
  logic v0_1; assign v0_1 = a[12] | a[11];
  logic p0_1; assign p0_1 = ~a[12];
  logic v0_2; assign v0_2 = a[10] | a[9];
  logic p0_2; assign p0_2 = ~a[10];
  logic v0_3; assign v0_3 = a[8] | a[7];
  logic p0_3; assign p0_3 = ~a[8];
  logic v0_4; assign v0_4 = a[6] | a[5];
  logic p0_4; assign p0_4 = ~a[6];
  logic v0_5; assign v0_5 = a[4] | a[3];
  logic p0_5; assign p0_5 = ~a[4];
  logic v0_6; assign v0_6 = a[2] | a[1];
  logic p0_6; assign p0_6 = ~a[2];
  logic v0_7; assign v0_7 = a[0] | 1'b0;
  logic p0_7; assign p0_7 = ~a[0];
  logic v1_0; assign v1_0 = a[14] | a[13] | a[12] | a[11];
  logic [1:0] p1_0; assign p1_0 = v0_0 ? {1'b0, p0_0} : {1'b1, p0_1};
  logic v1_1; assign v1_1 = a[10] | a[9] | a[8] | a[7];
  logic [1:0] p1_1; assign p1_1 = v0_2 ? {1'b0, p0_2} : {1'b1, p0_3};
  logic v1_2; assign v1_2 = a[6] | a[5] | a[4] | a[3];
  logic [1:0] p1_2; assign p1_2 = v0_4 ? {1'b0, p0_4} : {1'b1, p0_5};
  logic v1_3; assign v1_3 = a[2] | a[1] | a[0] | 1'b0;
  logic [1:0] p1_3; assign p1_3 = v0_6 ? {1'b0, p0_6} : {1'b1, p0_7};
  logic v2_0; assign v2_0 = a[14] | a[13] | a[12] | a[11] | a[10] | a[9] | a[8] | a[7];
  logic [2:0] p2_0; assign p2_0 = v1_0 ? {1'b0, p1_0} : {1'b1, p1_1};
  logic v2_1; assign v2_1 = a[6] | a[5] | a[4] | a[3] | a[2] | a[1] | a[0] | 1'b0;
  logic [2:0] p2_1; assign p2_1 = v1_2 ? {1'b0, p1_2} : {1'b1, p1_3};
  logic v3_0; assign v3_0 = a[14] | a[13] | a[12] | a[11] | a[10] | a[9] | a[8] | a[7] | a[6] | a[5] | a[4] | a[3] | a[2] | a[1] | a[0] | 1'b0;
  logic [3:0] p3_0; assign p3_0 = v2_0 ? {1'b0, p2_0} : {1'b1, p2_1};
  assign n = v3_0 ? p3_0 : 4'd15;
endmodule



// lzd_cell_tree (pair_cell, binary_count, valid flags flat): the leading zeros of a 36-bit word
module fam_count_lzd_pair_cell_binary_count_vflat_w36 (input logic [35:0] a, output logic [5:0] n);
  logic v0_0; assign v0_0 = a[35] | a[34];
  logic p0_0; assign p0_0 = ~a[35];
  logic v0_1; assign v0_1 = a[33] | a[32];
  logic p0_1; assign p0_1 = ~a[33];
  logic v0_2; assign v0_2 = a[31] | a[30];
  logic p0_2; assign p0_2 = ~a[31];
  logic v0_3; assign v0_3 = a[29] | a[28];
  logic p0_3; assign p0_3 = ~a[29];
  logic v0_4; assign v0_4 = a[27] | a[26];
  logic p0_4; assign p0_4 = ~a[27];
  logic v0_5; assign v0_5 = a[25] | a[24];
  logic p0_5; assign p0_5 = ~a[25];
  logic v0_6; assign v0_6 = a[23] | a[22];
  logic p0_6; assign p0_6 = ~a[23];
  logic v0_7; assign v0_7 = a[21] | a[20];
  logic p0_7; assign p0_7 = ~a[21];
  logic v0_8; assign v0_8 = a[19] | a[18];
  logic p0_8; assign p0_8 = ~a[19];
  logic v0_9; assign v0_9 = a[17] | a[16];
  logic p0_9; assign p0_9 = ~a[17];
  logic v0_10; assign v0_10 = a[15] | a[14];
  logic p0_10; assign p0_10 = ~a[15];
  logic v0_11; assign v0_11 = a[13] | a[12];
  logic p0_11; assign p0_11 = ~a[13];
  logic v0_12; assign v0_12 = a[11] | a[10];
  logic p0_12; assign p0_12 = ~a[11];
  logic v0_13; assign v0_13 = a[9] | a[8];
  logic p0_13; assign p0_13 = ~a[9];
  logic v0_14; assign v0_14 = a[7] | a[6];
  logic p0_14; assign p0_14 = ~a[7];
  logic v0_15; assign v0_15 = a[5] | a[4];
  logic p0_15; assign p0_15 = ~a[5];
  logic v0_16; assign v0_16 = a[3] | a[2];
  logic p0_16; assign p0_16 = ~a[3];
  logic v0_17; assign v0_17 = a[1] | a[0];
  logic p0_17; assign p0_17 = ~a[1];
  logic v0_18; assign v0_18 = 1'b0 | 1'b0;
  logic p0_18; assign p0_18 = ~1'b0;
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
  logic v1_0; assign v1_0 = a[35] | a[34] | a[33] | a[32];
  logic [1:0] p1_0; assign p1_0 = v0_0 ? {1'b0, p0_0} : {1'b1, p0_1};
  logic v1_1; assign v1_1 = a[31] | a[30] | a[29] | a[28];
  logic [1:0] p1_1; assign p1_1 = v0_2 ? {1'b0, p0_2} : {1'b1, p0_3};
  logic v1_2; assign v1_2 = a[27] | a[26] | a[25] | a[24];
  logic [1:0] p1_2; assign p1_2 = v0_4 ? {1'b0, p0_4} : {1'b1, p0_5};
  logic v1_3; assign v1_3 = a[23] | a[22] | a[21] | a[20];
  logic [1:0] p1_3; assign p1_3 = v0_6 ? {1'b0, p0_6} : {1'b1, p0_7};
  logic v1_4; assign v1_4 = a[19] | a[18] | a[17] | a[16];
  logic [1:0] p1_4; assign p1_4 = v0_8 ? {1'b0, p0_8} : {1'b1, p0_9};
  logic v1_5; assign v1_5 = a[15] | a[14] | a[13] | a[12];
  logic [1:0] p1_5; assign p1_5 = v0_10 ? {1'b0, p0_10} : {1'b1, p0_11};
  logic v1_6; assign v1_6 = a[11] | a[10] | a[9] | a[8];
  logic [1:0] p1_6; assign p1_6 = v0_12 ? {1'b0, p0_12} : {1'b1, p0_13};
  logic v1_7; assign v1_7 = a[7] | a[6] | a[5] | a[4];
  logic [1:0] p1_7; assign p1_7 = v0_14 ? {1'b0, p0_14} : {1'b1, p0_15};
  logic v1_8; assign v1_8 = a[3] | a[2] | a[1] | a[0];
  logic [1:0] p1_8; assign p1_8 = v0_16 ? {1'b0, p0_16} : {1'b1, p0_17};
  logic v1_9; assign v1_9 = 1'b0 | 1'b0 | 1'b0 | 1'b0;
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
  logic v2_0; assign v2_0 = a[35] | a[34] | a[33] | a[32] | a[31] | a[30] | a[29] | a[28];
  logic [2:0] p2_0; assign p2_0 = v1_0 ? {1'b0, p1_0} : {1'b1, p1_1};
  logic v2_1; assign v2_1 = a[27] | a[26] | a[25] | a[24] | a[23] | a[22] | a[21] | a[20];
  logic [2:0] p2_1; assign p2_1 = v1_2 ? {1'b0, p1_2} : {1'b1, p1_3};
  logic v2_2; assign v2_2 = a[19] | a[18] | a[17] | a[16] | a[15] | a[14] | a[13] | a[12];
  logic [2:0] p2_2; assign p2_2 = v1_4 ? {1'b0, p1_4} : {1'b1, p1_5};
  logic v2_3; assign v2_3 = a[11] | a[10] | a[9] | a[8] | a[7] | a[6] | a[5] | a[4];
  logic [2:0] p2_3; assign p2_3 = v1_6 ? {1'b0, p1_6} : {1'b1, p1_7};
  logic v2_4; assign v2_4 = a[3] | a[2] | a[1] | a[0] | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [2:0] p2_4; assign p2_4 = v1_8 ? {1'b0, p1_8} : {1'b1, p1_9};
  logic v2_5; assign v2_5 = 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [2:0] p2_5; assign p2_5 = v1_10 ? {1'b0, p1_10} : {1'b1, p1_11};
  logic v2_6; assign v2_6 = 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [2:0] p2_6; assign p2_6 = v1_12 ? {1'b0, p1_12} : {1'b1, p1_13};
  logic v2_7; assign v2_7 = 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [2:0] p2_7; assign p2_7 = v1_14 ? {1'b0, p1_14} : {1'b1, p1_15};
  logic v3_0; assign v3_0 = a[35] | a[34] | a[33] | a[32] | a[31] | a[30] | a[29] | a[28] | a[27] | a[26] | a[25] | a[24] | a[23] | a[22] | a[21] | a[20];
  logic [3:0] p3_0; assign p3_0 = v2_0 ? {1'b0, p2_0} : {1'b1, p2_1};
  logic v3_1; assign v3_1 = a[19] | a[18] | a[17] | a[16] | a[15] | a[14] | a[13] | a[12] | a[11] | a[10] | a[9] | a[8] | a[7] | a[6] | a[5] | a[4];
  logic [3:0] p3_1; assign p3_1 = v2_2 ? {1'b0, p2_2} : {1'b1, p2_3};
  logic v3_2; assign v3_2 = a[3] | a[2] | a[1] | a[0] | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [3:0] p3_2; assign p3_2 = v2_4 ? {1'b0, p2_4} : {1'b1, p2_5};
  logic v3_3; assign v3_3 = 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [3:0] p3_3; assign p3_3 = v2_6 ? {1'b0, p2_6} : {1'b1, p2_7};
  logic v4_0; assign v4_0 = a[35] | a[34] | a[33] | a[32] | a[31] | a[30] | a[29] | a[28] | a[27] | a[26] | a[25] | a[24] | a[23] | a[22] | a[21] | a[20] | a[19] | a[18] | a[17] | a[16] | a[15] | a[14] | a[13] | a[12] | a[11] | a[10] | a[9] | a[8] | a[7] | a[6] | a[5] | a[4];
  logic [4:0] p4_0; assign p4_0 = v3_0 ? {1'b0, p3_0} : {1'b1, p3_1};
  logic v4_1; assign v4_1 = a[3] | a[2] | a[1] | a[0] | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [4:0] p4_1; assign p4_1 = v3_2 ? {1'b0, p3_2} : {1'b1, p3_3};
  logic v5_0; assign v5_0 = a[35] | a[34] | a[33] | a[32] | a[31] | a[30] | a[29] | a[28] | a[27] | a[26] | a[25] | a[24] | a[23] | a[22] | a[21] | a[20] | a[19] | a[18] | a[17] | a[16] | a[15] | a[14] | a[13] | a[12] | a[11] | a[10] | a[9] | a[8] | a[7] | a[6] | a[5] | a[4] | a[3] | a[2] | a[1] | a[0] | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [5:0] p5_0; assign p5_0 = v4_0 ? {1'b0, p4_0} : {1'b1, p4_1};
  assign n = v5_0 ? p5_0 : 6'd36;
endmodule


// fp significand adder (single_path): 1 path; operands ordered by magnitude before one shifter; align full_align on a barrel_mux_tree shifter, sticky by or_tree_shifted_out; significand adder ripple_carry; leading zeros by lza (lzd_cell_tree, single_indicator); normalize coarse_fine on a barrel_mux_tree shifter; exponent path on ripple_carry adders; subnormals as stored; window of 20 guard bits below the larger operand's lsb (the significands are the unpacker's: 16 stored bits)
module fam_fp_add_single_path_x36e11s16_p9d459d224988 (
  input logic [50:0] xa,
  input logic [50:0] xb,
  input logic sub,
  output logic [50:0] y
);
  logic [1:0] a_sp; assign a_sp = xa[50:49];
  logic a_s; assign a_s = xa[48];
  logic signed [10:0] a_e; assign a_e = $signed(xa[47:37]);
  logic [35:0] a_sig; assign a_sig = xa[36:1];
  logic a_st; assign a_st = xa[0];
  logic a_z; assign a_z = (a_sp == 2'd0) && (a_sig == 0) && !a_st;
  logic [50:0] xbs; assign xbs = {xb[50:49], xb[48] ^ sub, xb[47:0]};
  logic [1:0] b_sp; assign b_sp = xbs[50:49];
  logic b_s; assign b_s = xbs[48];
  logic signed [10:0] b_e; assign b_e = $signed(xbs[47:37]);
  logic [35:0] b_sig; assign b_sig = xbs[36:1];
  logic b_st; assign b_st = xbs[0];
  logic b_z; assign b_z = (b_sp == 2'd0) && (b_sig == 0) && !b_st;
  logic signed [11:0] eax; assign eax = $signed({a_e[10], a_e});
  logic signed [11:0] ebx; assign ebx = $signed({b_e[10], b_e});
  logic [11:0] d_nb; assign d_nb = ~(ebx);
  logic signed [11:0] d;
  // the exponent difference
  fam_adder_ripple_carry #(.W(12), .CHUNK(1), .FORM(0)) u1 (.a(eax), .b(d_nb), .cin(1'b1), .s(d), .cout());
  logic signed [11:0] zero_x; assign zero_x = 12'sd0;
  logic [11:0] dn_nb; assign dn_nb = ~(d);
  logic signed [11:0] dn;
  // the difference negated
  fam_adder_ripple_carry #(.W(12), .CHUNK(1), .FORM(0)) u2 (.a(zero_x), .b(dn_nb), .cin(1'b1), .s(dn), .cout());
  logic a_big; assign a_big = (d > 0) || (d == 0 && a_sig >= b_sig);
  logic [11:0] dabs; assign dabs = a_big ? d : dn;
  logic signed [10:0] e_big; assign e_big = a_big ? a_e : b_e;
  logic s_big; assign s_big = a_big ? a_s : b_s;
  logic eff_sub; assign eff_sub = a_s ^ b_s;
  logic [35:0] big_sig; assign big_sig = a_big ? a_sig : b_sig;
  logic [35:0] sml_sig; assign sml_sig = a_big ? b_sig : a_sig;
  logic big_st; assign big_st = a_big ? a_st : b_st;
  logic sml_st; assign sml_st = a_big ? b_st : a_st;
  logic [36:0] mb; assign mb = {1'b0, big_sig[15:0], 20'd0};
  logic [36:0] ms0; assign ms0 = {1'b0, sml_sig[15:0], 20'd0};
  logic far_f; assign far_f = 1'b1 && (dabs > 36);
  logic [5:0] amt_f; assign amt_f = (!(1'b1) || far_f) ? 6'd0 : dabs[5:0];
  logic [36:0] mssh_f;
  logic stk0_f;
  // align: the operand shifted right by the exponent difference
  fam_shift_barrel_mux_tree #(.W(37), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u3 (.a(ms0), .amt(amt_f), .op(3'd1), .y(mssh_f), .sticky());
  assign stk0_f = |(ms0 & ((3'd1 == 3'd0) ? ~({37{1'b1}} >> amt_f) : ~({37{1'b1}} << amt_f)));
  logic [36:0] m_f; assign m_f = far_f ? 37'd0 : mssh_f;
  logic stk_f; assign stk_f = far_f ? (sml_sig != 0) : stk0_f;
  logic stb_f; assign stb_f = sml_st | stk_f;
  logic [36:0] ms_f; assign ms_f = m_f;
  logic [36:0] bop_f; assign bop_f = eff_sub ? ~ms_f : ms_f;
  logic cin_f; assign cin_f = eff_sub ? ~stb_f : 1'b0;
  logic co_f;
  logic [36:0] r_f;
  // add: the significand adder (ripple_carry)
  fam_adder_ripple_carry #(.W(37), .CHUNK(1), .FORM(0)) u4 (.a(mb), .b(bop_f), .cin(cin_f), .s(r_f), .cout(co_f));
  logic st_f; assign st_f = big_st | stb_f;
  logic ovf_f; assign ovf_f = r_f[36];
  logic [35:0] sig0_f; assign sig0_f = ovf_f ? r_f[36:1] : r_f[35:0];
  logic st0_f; assign st0_f = st_f | (ovf_f & r_f[0]);
  logic signed [10:0] e0n_f_c; assign e0n_f_c = -11'sd20;
  logic signed [10:0] e0n_f;
  // normalize: the window's exponent origin
  fam_adder_ripple_carry #(.W(11), .CHUNK(1), .FORM(0)) u5 (.a(e_big), .b(e0n_f_c), .cin(1'b0), .s(e0n_f), .cout());
  logic signed [10:0] e0o_f_c; assign e0o_f_c = -11'sd19;
  logic signed [10:0] e0o_f;
  // normalize: the window's exponent origin after a carry out
  fam_adder_ripple_carry #(.W(11), .CHUNK(1), .FORM(0)) u6 (.a(e_big), .b(e0o_f_c), .cin(1'b0), .s(e0o_f), .cout());
  logic signed [10:0] e0_f; assign e0_f = ovf_f ? e0o_f : e0n_f;
  logic [36:0] t_f0; assign t_f0 = mb ^ bop_f;
  logic [36:0] g_f0; assign g_f0 = mb & bop_f;
  logic [36:0] z_f0; assign z_f0 = ~mb & ~bop_f;
  logic [36:0] f_f0;
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
  assign f_f0[36] = (1'b0 & ((g_f0[36] & ~z_f0[35]) | (z_f0[36] & ~g_f0[35]))) | (~1'b0 & ((z_f0[36] & ~z_f0[35]) | (g_f0[36] & ~g_f0[35])));
  logic [35:0] fw_f0; assign fw_f0 = ovf_f ? f_f0[36:1] : f_f0[35:0];
  logic [35:0] fws_f; assign fws_f = fw_f0;
  logic [5:0] lzp_f;
  // normalize: leading zeros of the indicator string
  fam_count_lzd_pair_cell_binary_count_vflat_w36 u7 (.a(fws_f), .n(lzp_f));
  logic [5:0] lzs_f; assign lzs_f = (!eff_sub || fws_f == 0) ? 6'd0 : lzp_f[5:0];
  logic fz_f; assign fz_f = fws_f == 0;
  logic [5:0] cshift_f; assign cshift_f = {lzs_f[5:2], 2'd0};
  logic [5:0] fshift_f; assign fshift_f = {{(6-2){1'b0}}, lzs_f[1:0]};
  logic [35:0] sigc_f;
  // normalize: the coarse normalize stage (multiples of 4)
  fam_shift_barrel_mux_tree #(.W(36), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u8 (.a(sig0_f), .amt(cshift_f), .op(3'd0), .y(sigc_f), .sticky());
  logic [35:0] sign_f;
  // normalize: the fine normalize stage
  fam_shift_barrel_mux_tree #(.W(36), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u9 (.a(sigc_f), .amt(fshift_f), .op(3'd0), .y(sign_f), .sticky());
  logic signed [10:0] lzx_f; assign lzx_f = $signed({{(11-6){1'b0}}, lzs_f});
  logic [10:0] en_f_nb; assign en_f_nb = ~(lzx_f);
  logic signed [10:0] en_f;
  // normalize: the exponent lowered by the normalize count
  fam_adder_ripple_carry #(.W(11), .CHUNK(1), .FORM(0)) u10 (.a(e0_f), .b(en_f_nb), .cin(1'b1), .s(en_f), .cout());
  logic fix_f; assign fix_f = ~sign_f[35] && (sign_f != 0);
  logic [35:0] sigf_f; assign sigf_f = fix_f ? {sign_f[34:0], 1'b0} : sign_f;
  logic signed [10:0] enm_f_c; assign enm_f_c = -11'sd1;
  logic signed [10:0] enm_f;
  // normalize: the exponent of the corrected position
  fam_adder_ripple_carry #(.W(11), .CHUNK(1), .FORM(0)) u11 (.a(en_f), .b(enm_f_c), .cin(1'b0), .s(enm_f), .cout());
  logic signed [10:0] ef_f; assign ef_f = fix_f ? enm_f : en_f;
  logic zero_f; assign zero_f = (sigf_f == 0) && !st0_f;
  logic sr_f; assign sr_f = zero_f ? 1'b0 : s_big;
  logic [50:0] y_f; assign y_f = {2'd0, sr_f, ef_f, sigf_f, st0_f};
  logic both_inf; assign both_inf = (a_sp == 2'd2) && (b_sp == 2'd2);
  logic [50:0] y_sp; assign y_sp = (a_sp == 2'd1 || b_sp == 2'd1) ? {2'd1, 1'b0, 11'sd0, 36'd0, 1'b0} : both_inf ? ((a_s == b_s) ? {2'd2, a_s, 11'sd0, 36'd0, 1'b0} : {2'd1, 1'b0, 11'sd0, 36'd0, 1'b0}) : (a_sp == 2'd2) ? {2'd2, a_s, 11'sd0, 36'd0, 1'b0} : (b_sp == 2'd2) ? {2'd2, b_s, 11'sd0, 36'd0, 1'b0} : a_z ? xbs : b_z ? xa : y_f;
  assign y = y_sp;
endmodule

// fp comparator (integer_compare_on_bits, prefix_comparator)
module fam_fp_cmp_integer_compare_on_bits_x36e11s16_pa61fc99a71d5 (
  input logic [50:0] xa,
  input logic [50:0] xb,
  output logic lt,
  output logic eq
);
  logic [1:0] a_sp; assign a_sp = xa[50:49];
  logic a_s; assign a_s = xa[48];
  logic signed [10:0] a_e; assign a_e = $signed(xa[47:37]);
  logic [35:0] a_sig; assign a_sig = xa[36:1];
  logic a_st; assign a_st = xa[0];
  logic a_z; assign a_z = (a_sp == 2'd0) && (a_sig == 0) && !a_st;
  logic [1:0] b_sp; assign b_sp = xb[50:49];
  logic b_s; assign b_s = xb[48];
  logic signed [10:0] b_e; assign b_e = $signed(xb[47:37]);
  logic [35:0] b_sig; assign b_sig = xb[36:1];
  logic b_st; assign b_st = xb[0];
  logic b_z; assign b_z = (b_sp == 2'd0) && (b_sig == 0) && !b_st;
  logic sa; assign sa = a_s && !a_z;
  logic sb; assign sb = b_s && !b_z;
  logic [10:0] aeu; assign aeu = {~a_e[10], a_e[9:0]};
  logic [10:0] beu; assign beu = {~b_e[10], b_e[9:0]};
  logic [47:0] ma; assign ma = {aeu, a_sig, a_st};
  logic [47:0] mb; assign mb = {beu, b_sig, b_st};
  logic mlt;
  logic meq;
  // the magnitude words compared as integers (prefix_comparator)
  fam_cmp_prefix_comparator #(.W(48), .SIGNED(0), .STRUCTURE(0), .RADIX(2)) u1 (.a(ma), .b(mb), .lt(mlt), .eq(meq));
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


// fp significand multiplier (sig_mul_then_round): behavioral_star over the 16-bit significands, the exact product in the X field, the exponent sum on a ripple_carry adder
module fam_fp_mul_sig_mul_then_round_x36e11s16_pbd766efe148c (
  input logic [50:0] xa,
  input logic [50:0] xb,
  output logic [50:0] y
);
  logic [1:0] a_sp; assign a_sp = xa[50:49];
  logic a_s; assign a_s = xa[48];
  logic signed [10:0] a_e; assign a_e = $signed(xa[47:37]);
  logic [35:0] a_sig; assign a_sig = xa[36:1];
  logic a_st; assign a_st = xa[0];
  logic a_z; assign a_z = (a_sp == 2'd0) && (a_sig == 0) && !a_st;
  logic [1:0] b_sp; assign b_sp = xb[50:49];
  logic b_s; assign b_s = xb[48];
  logic signed [10:0] b_e; assign b_e = $signed(xb[47:37]);
  logic [35:0] b_sig; assign b_sig = xb[36:1];
  logic b_st; assign b_st = xb[0];
  logic b_z; assign b_z = (b_sp == 2'd0) && (b_sig == 0) && !b_st;
  logic s; assign s = a_s ^ b_s;
  logic [15:0] sa; assign sa = a_sig[15:0];
  logic [15:0] sb; assign sb = b_sig[15:0];
  logic [31:0] p;
  // the significand product (behavioral_star)
  fam_mul_behavioral_star_w16_u_pfc463c41 u1 (.a(sa), .b(sb), .p(p));
  logic signed [10:0] e;
  // the exponent sum
  fam_adder_ripple_carry #(.W(11), .CHUNK(1), .FORM(0)) u2 (.a(a_e), .b(b_e), .cin(1'b0), .s(e), .cout());
  logic st; assign st = a_st | b_st;
  logic [50:0] y_fin; assign y_fin = {2'd0, s, e, {{(36-32){1'b0}}, p}, st};
  logic [50:0] y_sp; assign y_sp = (a_sp == 2'd1 || b_sp == 2'd1) ? {2'd1, 1'b0, 11'sd0, 36'd0, 1'b0} : (a_sp == 2'd2 || b_sp == 2'd2) ? (((a_sp == 2'd0 && a_z) || (b_sp == 2'd0 && b_z)) ? {2'd1, 1'b0, 11'sd0, 36'd0, 1'b0} : {2'd2, s, 11'sd0, 36'd0, 1'b0}) : y_fin;
  assign y = y_sp;
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
module fam_mul_behavioral_star_w16_u_pfc463c41 (input logic [15:0] a, input logic [15:0] b, output logic [31:0] p);
  assign p = a * b;
endmodule


// behavioral_star: p = a * b, the structure left to synthesis
module fam_mul_behavioral_star_w8_s (input logic [7:0] a, input logic [7:0] b, output logic [15:0] p);
  assign p = $signed(a) * $signed(b);
endmodule


// posit decoder (posit_adder_multiplier): posit16_1 pattern -> V; regime by lzc_plus_shifter, internal representation sign_magnitude; operator_set add_mul; daz has no effect (posits have no subnormals)
module fam_posit_decode_posit_adder_multiplier_lzc_plus_shifter_sign_magnitude_posit16_1_x36e11s16_14e320560f9f (
  input logic [15:0] b,
  input logic daz,
  output logic [30:0] u
);
  logic s; assign s = b[15];
  logic zero; assign zero = b == 16'd0;
  logic nar; assign nar = b == {1'b1, {15{1'b0}}};
  logic [15:0] bx; assign bx = b ^ {16{s}};
  logic [15:0] mag;
  // the magnitude: a negative pattern two's-complemented (the sign carried separately)
  fam_incr_prefix_and #(.W(16), .STRUCTURE(1), .B(4), .TOPO(0)) u1 (.a(bx), .cin(s), .s(mag), .cout());
  logic [14:0] body; assign body = mag[14:0];
  logic first; assign first = body[14];
  logic [14:0] t; assign t = body ^ {15{first}};
  logic [3:0] run;
  logic [14:0] rest;
  logic [3:0] lz;
  // the regime run: the leading zeros of the body xored with its first bit
  fam_count_lzd_pair_cell_binary_count_vflat_w15 u2 (.a(t), .n(lz));
  assign run = lz[3:0];
  logic [3:0] sha; assign sha = run[3:0] + 4'd1;
  logic [14:0] rest0;
  // the body shifted past the run and its terminator
  fam_shift_barrel_mux_tree #(.W(15), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u3 (.a(body), .amt(sha), .op(3'd0), .y(rest0), .sticky());
  assign rest = (({1'b0, run} + 5'd1) >= 5'd15) ? 15'd0 : rest0;
  logic ef; assign ef = rest[14:14];
  logic [14:0] fw; assign fw = {rest[13:0], {1{1'b0}}};
  logic signed [4:0] k; assign k = first ? ($signed({1'b0, run}) - 5'sd1) : -$signed({1'b0, run});
  logic signed [5:0] sc; assign sc = ($signed({{1{k[4]}}, k}) <<< 1) + $signed({{5{1'b0}}, ef});
  logic [15:0] sig_n;
  logic signed [10:0] ex;
  assign sig_n = {1'b1, fw};
  assign ex = $signed({{5{sc[5]}}, sc}) - 11'sd15;
  logic [15:0] sig; assign sig = sig_n;
  logic [29:0] v_zero; assign v_zero = {2'd0, 1'b0, 11'sd0, 16'd0};
  logic [29:0] v_nar; assign v_nar = {2'd1, 1'b0, 11'sd0, 16'd0};
  logic [29:0] v_fin; assign v_fin = {2'd0, s, ex, sig};
  assign u = zero ? {1'b0, v_zero} : nar ? {1'b0, v_nar} : {1'b0, v_fin};
endmodule

// posit encoder (posit_adder_multiplier): X -> posit16_1 pattern and flags; internal representation sign_magnitude: the magnitude rounded to nearest even, the pattern negated last; operator_set add_mul; rounding follows the frozen Python pattern rules
module fam_posit_encode_posit_adder_multiplier_sign_magnitude_posit16_1_x36e11s16_14e320560f9f (
  input logic [50:0] x,
  input logic [2:0] rnd,
  input logic [7:0] word,
  input logic ftz,
  output logic [9:0] fl,
  output logic [15:0] bits
);
  logic [1:0] x_sp; assign x_sp = x[50:49];
  logic x_s; assign x_s = x[48];
  logic signed [10:0] x_e; assign x_e = $signed(x[47:37]);
  logic [35:0] x_sig; assign x_sig = x[36:1];
  logic x_st; assign x_st = x[0];
  logic x_z; assign x_z = (x_sp == 2'd0) && (x_sig == 0) && !x_st;
  logic s; assign s = x_s;
  logic nar_in; assign nar_in = x_sp != 2'd0;
  logic is_zero; assign is_zero = (x_sig == 36'd0) && !x_st;
  logic lone; assign lone = (x_sig == 36'd0) && x_st;
  logic [35:0] sig_in; assign sig_in = lone ? 36'd1 : x_sig;
  logic signed [10:0] e_in; assign e_in = lone ? (x_e - 11'sd1) : x_e;
  logic [5:0] lz;
  // the normalizer's leading-zero count
  fam_count_lzd_pair_cell_binary_count_vflat_w36 u1 (.a(sig_in), .n(lz));
  logic [5:0] lzs; assign lzs = (sig_in == 36'd0) ? 6'd0 : lz[5:0];
  logic [35:0] sig;
  // the normalizer's left shift
  fam_shift_barrel_mux_tree #(.W(36), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u2 (.a(sig_in), .amt(lzs), .op(3'd0), .y(sig), .sticky());
  logic signed [10:0] e; assign e = e_in - $signed({{(11-6){1'b0}}, lzs});
  logic signed [10:0] eu; assign eu = e + 11'sd35;
  logic signed [10:0] k; assign k = eu >>> 1;
  logic elow; assign elow = eu[0:0];
  logic clamp_hi; assign clamp_hi = k > 11'sd14;
  logic clamp_lo; assign clamp_lo = k < -11'sd14;
  logic clamp; assign clamp = clamp_hi | clamp_lo;
  logic ovf_k; assign ovf_k = k == 11'sd14;
  logic [35:0] fldm; assign fldm = {elow, sig[34:0]};
  logic [35:0] fld; assign fld = fldm;
  logic signed [10:0] kp; assign kp = k;
  logic [10:0] kabs; assign kabs = (kp < 0) ? -kp : kp;
  logic [5:0] rl; assign rl = (kp >= 0) ? (kabs[5:0] + 6'd2) : (kabs[5:0] + 6'd1);
  logic [54:0] reg_hi; assign reg_hi = (kp >= 0) ? ~({55{1'b1}} >> (kabs + 1)) : ({{54{1'b0}}, 1'b1} << (54 - kabs));
  logic [54:0] fld_top; assign fld_top = {fld, {19{1'b0}}};
  logic [54:0] fld_sh;
  // the exponent and fraction fields shifted below the regime
  fam_shift_barrel_mux_tree #(.W(55), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u3 (.a(fld_top), .amt(rl), .op(3'd1), .y(fld_sh), .sticky());
  logic [54:0] r; assign r = reg_hi | fld_sh | {{54{1'b0}}, x_st};
  logic [14:0] topb; assign topb = r[54:40];
  logic guard; assign guard = r[39];
  logic rest_nz; assign rest_nz = r[38:0] != 39'd0;
  logic inexact; assign inexact = guard | rest_nz;
  logic nearest_up; assign nearest_up = guard & (rest_nz | topb[0]);
  logic up; assign up = (rnd == 3'd1 || rnd == 3'd2) ? (inexact & s) : (rnd == 3'd3) ? (inexact & !s) : nearest_up;
  logic [15:0] pt0; assign pt0 = {1'b0, topb};
  logic [15:0] pt;
  // the rounding increment
  fam_incr_prefix_and #(.W(16), .STRUCTURE(1), .B(4), .TOPO(0)) u4 (.a(pt0), .cin(up), .s(pt), .cout());
  logic ovf1; assign ovf1 = pt[15];
  logic unf1; assign unf1 = pt == 16'd0;
  logic [15:0] mag; assign mag = clamp_hi ? 16'd32767 : clamp_lo ? 16'd1 : ovf1 ? 16'd32767 : unf1 ? 16'd1 : pt;
  logic [15:0] magx; assign magx = mag ^ {16{s}};
  logic [15:0] res;
  // the sign applied last: a negative result's pattern negated
  fam_incr_prefix_and #(.W(16), .STRUCTURE(1), .B(4), .TOPO(0)) u5 (.a(magx), .cin(s), .s(res), .cout());
  logic inex_f; assign inex_f = clamp | inexact;
  logic ovf_f; assign ovf_f = clamp_hi | (!clamp & (ovf1 | (ovf_k & inexact)));
  logic unf_f; assign unf_f = clamp_lo | (!clamp & unf1);
  logic [9:0] fl_fin; assign fl_fin = (inex_f ? (10'd1 << 4) : 10'd0) | (ovf_f ? (10'd1 << 2) : 10'd0) | (unf_f ? (10'd1 << 3) : 10'd0);
  assign fl = nar_in ? (10'd1 << 5) : is_zero ? 10'd0 : fl_fin;
  assign bits = nar_in ? {1'b1, {15{1'b0}}} : is_zero ? 16'd0 : res;
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
