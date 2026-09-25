// dot_core: behavioral reference derived from the instance (chialu.VecDotAcc, fused contract). Every mode computes the verify layer's exact semantics.
// core.family: multi_term_fused_dot (normalize_before_add=False, term_source=products, alignment_strategy=pairwise_difference_reuse, sign_handling=dual_reduction_positive_pair_select, rounding_contract=correctly_rounded, window_bits=76, normalization_deferral=final_only, align.family=full_align, lza.family=lzc_after_add, norm_shifter.family=barrel_mux_tree, round.family=increment_adder, reduction.family=linear_chain, cpa.family=ripple_carry, multiplier.family=segmented_grid, align.shifter.family=barrel_mux_tree, align.shifter.stage_radix=2, align.shifter.select_encoding=binary, align.shifter.stage_order=small_shift_first, align.shifter.direction_handling=mirrored_datapath, align.shifter.sticky_collect=False, lza.counter.family=lzd_cell_tree, lza.counter.block_primitive=pair_cell, lza.counter.output_form=binary_count, lza.counter.valid_flag_propagation=False, norm_shifter.stage_radix=2, norm_shifter.select_encoding=binary, norm_shifter.stage_order=small_shift_first, norm_shifter.direction_handling=mirrored_datapath, norm_shifter.sticky_collect=False, round.incrementer.family=prefix_and_incrementer, round.incrementer.structure=ripple_and_chain, cpa.full_adder_logic=generate_propagate, cpa.chunk_width_bits=1, multiplier.recursion_depth=1, multiplier.seg_w=6, multiplier.num_seg=4, multiplier.segment_shape=square, multiplier.merge_form=shift_add_tree, multiplier.segment.family=direct_pp_parallel, multiplier.merge_adder.family=ripple_carry, multiplier.merge_tree.family=csa_reduction_tree, multiplier.segment.group_bits=1, multiplier.segment.signed_scheme=baugh_wooley, multiplier.segment.reduction.family=csa_reduction_tree, multiplier.segment.hard_multiple_adder.family=ripple_carry, multiplier.segment.reduction.geometry=dadda, multiplier.segment.reduction.counter_kind=3_2, multiplier.segment.reduction.cpa.family=uniform, multiplier.segment.reduction.cpa.adder.family=ripple_carry, multiplier.segment.reduction.cpa.adder.full_adder_logic=generate_propagate, multiplier.segment.reduction.cpa.adder.chunk_width_bits=1, multiplier.segment.hard_multiple_adder.full_adder_logic=generate_propagate, multiplier.segment.hard_multiple_adder.chunk_width_bits=1, multiplier.merge_adder.full_adder_logic=generate_propagate, multiplier.merge_adder.chunk_width_bits=1, multiplier.merge_tree.geometry=dadda, multiplier.merge_tree.counter_kind=3_2, multiplier.merge_tree.cpa.family=uniform, multiplier.merge_tree.cpa.adder.family=ripple_carry, multiplier.merge_tree.cpa.adder.full_adder_logic=generate_propagate, multiplier.merge_tree.cpa.adder.chunk_width_bits=1)
// mode 0: family multi_term_fused_dot realized by the library module fam_dot_multi_term_fused_dot_n4_s3c24_a281lm149_x52e16s24_09ac12ad8924 (fused contract)
// LIBRARY: fam_adder_ripple_carry, fam_adder_ripple_chunk, fam_count_lzd_pair_cell_binary_count_vflat_w76, fam_count_lzd_pair_cell_binary_count_vprop_w52, fam_dot_multi_term_fused_dot_n4_s3c24_a281lm149_x52e16s24_09ac12ad8924, fam_fp_round_dedicated_per_op_increment_adder_fp32_x52e16s24_pe0f43f9cf852, fam_incr_prefix_and, fam_mul_direct_dadda_3_2_w2_u_p53f52f94, fam_mul_segmented_grid_w3_u_p0fd7e5f0, fam_prefix_sklansky_w76, fam_prefix_sklansky_w77, fam_shift_barrel_mux_tree, fam_shift_keep_mask, fam_shift_stage (chialu.targets.rtl.families: the modules the core instantiates; their text follows the core)
// EVOLVE-BLOCK-START
// ADIR-DECL v1
// ADIR-END
module dot_core (
  input  logic [31:0] a,
  input  logic [31:0] b,
  input  logic [31:0] c,
  output logic [31:0] d
);
  logic [2:0] rnd_sel; assign rnd_sel = 3'd0;
  logic [2:0] rnd; assign rnd = rnd_sel;
  logic daz; assign daz = 1'b0;
  logic ftz; assign ftz = 1'b0;

  // ---- m0: V = {special[1:0], sign, exp[16] (signed), sig[24]}
  //           X = {special[1:0], sign, exp[16] (signed), sig[52], sticky}
  localparam int m0_SW = 24, m0_EW = 16, m0_XW = 52;
  localparam int m0_VW = 43, m0_XT = 72;
  function automatic [42:0] m0_mkv(input [1:0] sp, input s, input signed [15:0] e, input [23:0] sig);
    m0_mkv = {sp, s, e, sig};
  endfunction
  function automatic [71:0] m0_mkx(input [1:0] sp, input s, input signed [15:0] e, input [51:0] sig, input st);
    m0_mkx = {sp, s, e, sig, st};
  endfunction
  function automatic [71:0] m0_x(input [42:0] v);   // widen V to X
    m0_x = {v[42:42-1], v[42-2], v[42-3 -: 16], {{(52-24){1'b0}}, v[23:0]}, 1'b0};
  endfunction
  // normalize: leading one at bit XW-1 (zero stays zero)
  function automatic [71:0] m0_norm(input [71:0] x);
    logic [51:0] s; logic signed [15:0] e; integer k;
    s = x[52:1]; e = x[52+16:52+1];
    if (s != 0) begin
      for (k = 32; k >= 1; k = k / 2) begin
        if (k < 52) begin
          if (s[51 -: 1] == 1'b0 && (s >> (52 - k)) == 0) begin
            s = s << k; e = e - k;
          end
        end
      end
    end
    m0_norm = {x[71:71-1], x[71-2], e, s, x[0]};
  endfunction

  function automatic m0_rup(input [2:0] rnd, input s, input inexact, input [52:0] rest, input [52:0] halfv,
                             input st, input lsb, input [52+8:0] fint, input [7:0] word);
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
  function automatic [71:0] m0_add(input [71:0] a, input [71:0] b, input sub);
    logic [71:0] na, nb, big, sml; logic [1:0] spa, spb; logic sa, sb, sr, sw;
    logic signed [15:0] ea, eb, d; logic [52:0] ms, mb, r; logic st, stb; integer sh;
    na = m0_norm(a); nb = m0_norm(b);
    spa = na[71:71-1]; spb = nb[71:71-1];
    sa = na[71-2]; sb = nb[71-2] ^ sub;
    if (spa == 2'd1 || spb == 2'd1) m0_add = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 && spb == 2'd2) m0_add = (sa == sb) ? m0_mkx(2'd2, sa, 0, 0, 1'b0) : m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m0_add = m0_mkx(2'd2, sa, 0, 0, 1'b0);
    else if (spb == 2'd2) m0_add = m0_mkx(2'd2, sb, 0, 0, 1'b0);
    else if (na[52:1] == 0 && !na[0]) m0_add = {nb[71:71-1], sb, nb[71-3:0]};
    else if (nb[52:1] == 0 && !nb[0]) m0_add = na;
    else begin
      ea = na[52+16:52+1]; eb = nb[52+16:52+1];
      // order by magnitude (both normalized): larger exponent, then sig
      if (ea > eb || (ea == eb && na[52:1] >= nb[52:1])) begin big = na; sml = nb; sw = 1'b0; end
      else begin big = nb; sml = na; sw = 1'b1; end
      d = big[52+16:52+1] - sml[52+16:52+1];
      ms = {1'b0, sml[52:1]}; stb = sml[0];
      if (d > 52 + 1) begin stb = stb | (ms != 0); ms = 0; end
      else begin
        for (sh = 0; sh < 52 + 2; sh = sh + 1) begin
          if (sh < d) begin stb = stb | ms[0]; ms = ms >> 1; end
        end
      end
      mb = {1'b0, big[52:1]}; st = big[0] | stb;
      if ((sw ? sb : sa) == (sw ? sa : sb)) begin
        r = mb + ms;
        sr = sw ? sb : sa;
      end else begin
        // subtract: the sticky of the smaller operand borrows one lsb
        r = mb - ms - (stb ? 1'b1 : 1'b0);
        sr = sw ? sb : sa;
        if (r == 0 && !st) sr = 1'b0;
      end
      if (r[52]) begin st = st | r[0]; r = r >> 1; m0_add = m0_mkx(2'd0, sr, big[52+16:52+1] + 1, r[51:0], st); end
      else m0_add = m0_mkx(2'd0, sr, big[52+16:52+1], r[51:0], st);
    end
  endfunction
  function automatic [71:0] m0_mul(input [71:0] a, input [71:0] b);
    logic [71:0] na, nb; logic [1:0] spa, spb; logic s; logic [2*52-1:0] pr; logic st; integer k;
    na = m0_norm(a); nb = m0_norm(b);
    spa = na[71:71-1]; spb = nb[71:71-1]; s = na[71-2] ^ nb[71-2];
    if (spa == 2'd1 || spb == 2'd1) m0_mul = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 || spb == 2'd2) begin
      if ((spa == 2'd0 && na[52:1] == 0 && !na[0]) || (spb == 2'd0 && nb[52:1] == 0 && !nb[0]))
        m0_mul = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
      else m0_mul = m0_mkx(2'd2, s, 0, 0, 1'b0);
    end else begin
      pr = na[52:1] * nb[52:1];
      st = na[0] | nb[0];
      // keep the top XW bits of the product, the rest folds into sticky
      st = st | (pr[51:0] != 0);
      m0_mul = m0_mkx(2'd0, s, na[52+16:52+1] + nb[52+16:52+1] + 52, pr[2*52-1:52], st);
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
  function automatic [2*52+1:0] m0_udiv(input [51:0] a, input [51:0] dv);
    logic [52+1:0] r; logic [52:0] q; logic ge; integer i;
    r = {2'b0, a}; q = 0;
    for (i = 52; i >= 0; i = i - 1) begin
      ge = (r >= {2'b0, dv});
      r = ge ? r - {2'b0, dv} : r;
      q = {q[51:0], ge};
      if (i > 0) r = {r[52:0], 1'b0};
    end
    m0_udiv = {q, r[52:0]};
  endfunction
  // the exact product: {special[1:0], sign, exp[EW], sig[2XW]} (no sticky)
  function automatic [2*52+16+2:0] m0_mulx(input [71:0] a, input [71:0] b);
    logic [71:0] na, nb; logic [1:0] spa, spb, sp; logic s; logic [2*52-1:0] pr;
    na = m0_norm(a); nb = m0_norm(b);
    pr = na[52:1] * nb[52:1];
    spa = na[71:71-1]; spb = nb[71:71-1]; s = na[71-2] ^ nb[71-2];
    if (spa == 2'd1 || spb == 2'd1) sp = 2'd1;
    else if (spa == 2'd2 || spb == 2'd2)
      sp = ((spa == 2'd0 && na[52:1] == 0) || (spb == 2'd0 && nb[52:1] == 0)) ? 2'd1 : 2'd2;
    else sp = 2'd0;
    m0_mulx = {sp, s, na[52+16:52+1] + nb[52+16:52+1], pr};
  endfunction
  function automatic [71:0] m0_div(input [71:0] a, input [71:0] b);
    logic [71:0] na, nb; logic [1:0] spa, spb; logic s; logic [2*52+1:0] qr; logic [52:0] q, r;
    na = m0_norm(a); nb = m0_norm(b);
    spa = na[71:71-1]; spb = nb[71:71-1]; s = na[71-2] ^ nb[71-2];
    if (spa == 2'd1 || spb == 2'd1) m0_div = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2 && spb == 2'd2) m0_div = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m0_div = m0_mkx(2'd2, s, 0, 0, 1'b0);
    else if (spb == 2'd2) m0_div = m0_mkx(2'd0, s, 0, 0, 1'b0);
    else if (nb[52:1] == 0 && !nb[0]) begin
      if (na[52:1] == 0 && !na[0]) m0_div = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
      else m0_div = m0_mkx(2'd2, s, 0, 0, 1'b0);
    end else if (na[52:1] == 0 && !na[0]) m0_div = m0_mkx(2'd0, s, 0, 0, 1'b0);
    else begin
      qr = m0_udiv(na[52:1], nb[52:1]);     // both normalized: nonzero finite
      q = qr[2*52+1:52+1]; r = qr[52:0];
      // q < 2^(XW+1): drop one bit when it carries
      if (q[52]) m0_div = m0_mkx(2'd0, s, na[52+16:52+1] - nb[52+16:52+1] - 52 + 1, q[52:1], (r != 0) | q[0] | na[0] | nb[0]);
      else m0_div = m0_mkx(2'd0, s, na[52+16:52+1] - nb[52+16:52+1] - 52, q[51:0], (r != 0) | na[0] | nb[0]);
    end
  endfunction
  function automatic [71:0] m0_sqrt(input [71:0] a);
    logic [71:0] na; logic [1:0] spa; logic signed [15:0] e; logic [52:0] m; logic [2*52+3:0] rad;
    logic [52+2:0] rem, trial; logic [52:0] root; logic ge; integer i;
    na = m0_norm(a); spa = na[71:71-1];
    if (spa == 2'd1) m0_sqrt = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (spa == 2'd2) m0_sqrt = na[71-2] ? m0_mkx(2'd1, 1'b0, 0, 0, 1'b0) : na;
    else if (na[52:1] == 0 && !na[0]) m0_sqrt = na;
    else if (na[71-2]) m0_sqrt = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else begin
      e = na[52+16:52+1];
      // value = m * 2^e with e even; radicand = m * 2^(2K): root = sqrt(m) * 2^K, XW+1 bits
      if (e[0]) begin m = {na[52:1], 1'b0}; e = e - 1; end
      else m = {1'b0, na[52:1]};
      rad = {{(52+3){1'b0}}, m} << 52;
      rem = 0; root = 0;
      for (i = 52; i >= 0; i = i - 1) begin
        rem = {rem[52:0], rad[2*i +: 2]};
        trial = {root, 2'b01};
        ge = (rem >= trial);                  // unconditional assignments, as in udiv
        rem = ge ? rem - trial : rem;
        root = {root[51:0], ge};
      end
      m0_sqrt = m0_mkx(2'd0, 1'b0, (e >>> 1) - 26 + 1, root[52:1], (rem != 0) | root[0] | na[0]);
    end
  endfunction
  // X ordering treats NaN as unordered and compares finite values by sign and magnitude
  function automatic m0_lt(input [71:0] a, input [71:0] b);
    logic [71:0] na, nb; logic za, zb, sa, sb, mag_lt; logic signed [15:0] ea, eb;
    na = m0_norm(a); nb = m0_norm(b);
    za = (na[52:1] == 0) && !na[0]; zb = (nb[52:1] == 0) && !nb[0];
    sa = na[71-2] && !za; sb = nb[71-2] && !zb;
    if (na[71:71-1] == 2'd1 || nb[71:71-1] == 2'd1) m0_lt = 1'b0;
    else if (na[71:71-1] == 2'd2 || nb[71:71-1] == 2'd2) begin
      if (na[71:71-1] == 2'd2 && nb[71:71-1] == 2'd2) m0_lt = na[71-2] && !nb[71-2];
      else if (na[71:71-1] == 2'd2) m0_lt = na[71-2];
      else m0_lt = !nb[71-2];
    end else if (za && zb) m0_lt = 1'b0;
    else if (sa != sb) m0_lt = sa;
    else begin
      ea = na[52+16:52+1]; eb = nb[52+16:52+1];
      if (za) mag_lt = 1'b1; else if (zb) mag_lt = 1'b0;
      else mag_lt = (ea < eb) || (ea == eb && (na[52:1] < nb[52:1] || (na[52:1] == nb[52:1] && !na[0] && nb[0])));
      m0_lt = sa ? !mag_lt && !(za && zb) && !m0_eq(na, nb) : mag_lt;
    end
  endfunction
  function automatic m0_eq(input [71:0] a, input [71:0] b);
    logic [71:0] na, nb; logic za, zb;
    na = m0_norm(a); nb = m0_norm(b);
    za = (na[52:1] == 0) && !na[0]; zb = (nb[52:1] == 0) && !nb[0];
    if (na[71:71-1] == 2'd1 || nb[71:71-1] == 2'd1) m0_eq = 1'b0;
    else if (na[71:71-1] == 2'd2 || nb[71:71-1] == 2'd2)
      m0_eq = (na[71:71-1] == nb[71:71-1]) && (na[71-2] == nb[71-2]);
    else if (za || zb) m0_eq = za && zb;
    else m0_eq = (na[71-2] == nb[71-2]) && (na[52+16:52+1] == nb[52+16:52+1]) && (na[52:1] == nb[52:1]) && (na[0] == nb[0]);
  endfunction

  // fp8e5m2 pattern -> V (bit VW = denormal-read flag returned beside)
  function automatic [43:0] m0_unpack_ab(input [7:0] b, input daz);
    logic [4:0] e; logic [1:0] m; logic [23:0] sig; logic signed [15:0] ex; logic den, s;
    e = b[6:2]; m = b[1:0]; s = b[7]; den = 1'b0; sig = 0; ex = 0;
    if ((e == 5'd31 && m != 0)) m0_unpack_ab = {1'b0, m0_mkv(2'd1, 1'b0, 0, 0)};
    else if ((e == 5'd31 && m == 0)) m0_unpack_ab = {1'b0, m0_mkv(2'd2, s, 0, 0)};
    else begin
    if (e == 0) begin sig = {{(24-2){1'b0}}, m}; ex = -16; if (m != 0) den = 1'b1; if (daz && m != 0) sig = 0; end
    else begin sig = {{(24-2-1){1'b0}}, 1'b1, m}; ex = e - 17; end
      m0_unpack_ab = {den, m0_mkv(2'd0, s, ex, sig)};
    end
  endfunction

  // fp32 pattern -> V (bit VW = denormal-read flag returned beside)
  function automatic [43:0] m0_unpack_c(input [31:0] b, input daz);
    logic [7:0] e; logic [22:0] m; logic [23:0] sig; logic signed [15:0] ex; logic den, s;
    e = b[30:23]; m = b[22:0]; s = b[31]; den = 1'b0; sig = 0; ex = 0;
    if ((e == 8'd255 && m != 0)) m0_unpack_c = {1'b0, m0_mkv(2'd1, 1'b0, 0, 0)};
    else if ((e == 8'd255 && m == 0)) m0_unpack_c = {1'b0, m0_mkv(2'd2, s, 0, 0)};
    else begin
    if (e == 0) begin sig = {{(24-23){1'b0}}, m}; ex = -149; if (m != 0) den = 1'b1; if (daz && m != 0) sig = 0; end
    else begin sig = {{(24-23-1){1'b0}}, 1'b1, m}; ex = e - 150; end
      m0_unpack_c = {den, m0_mkv(2'd0, s, ex, sig)};
    end
  endfunction

  // X -> d (fp32): sign(1) exp 8 man 23, top field 254, max finite 31'd2139095039
  function automatic [10+32-1:0] m0_pack_d(input [71:0] x0, input [2:0] rnd, input [7:0] word, input ftz);
    logic [71:0] x; logic [1:0] sp; logic s; logic signed [15:0] e, eu, biased; logic [51:0] sig;
    logic st, inexact, up, upn, half_eq, gt_half, tiny, ovf, unf, carry_n, to_inf; integer sh, shn, sht;
    logic [52:0] keep, rest, keepn, restn, halfv, halfn; logic [52+8:0] fint, fintn; logic [10-1:0] fl;
    logic [32+16:0] code; logic [32:0] mag; logic [32-1:0] outb;
    x = m0_norm(x0); sp = x[71:71-1]; s = x[71-2] & 1; sig = x[52:1]; st = x[0]; e = x[52+16:52+1];
    fl = 0; outb = 0;
    if (sp == 2'd1) begin fl[5] = 1'b1; outb = 32'd2143289344; end
    else if (sp == 2'd2) begin
      outb = {s, 31'd2139095040}; if (!1) begin fl[4] = 1'b1; fl[2] = 1'b1; end
    end else if (sig == 0 && !st) begin outb = 0 ? 0 : {s, {31{1'b0}}}; end
    else begin
      if (sig == 0) begin sig = 1 << 51; e = e - (2*52-1); end // normalize the lone sticky's tiny value
      eu = e + 51;                 // exponent of the leading one
      biased = eu + 127;
      shn = 52 - 1 - 23;           // bits dropped at the normal precision
      sh = (biased >= 1) ? shn : shn + (1 - biased);
      sht = sh;
      if (sh > 52 + 1) sh = 52 + 1;
      keep = {1'b0, sig} >> sh; rest = {1'b0, sig} & ((sh > 52) ? {(52+1){1'b1}} : ({1'b0, {52{1'b1}}} >> (52 - sh)));
      halfv = (sh == 0) ? 0 : ({{52{1'b0}}, 1'b1} << (sh - 1));
      keepn = {1'b0, sig} >> shn; restn = {1'b0, sig} & ({1'b0, {52{1'b1}}} >> (52 - shn));
      halfn = (shn == 0) ? 0 : ({{52{1'b0}}, 1'b1} << (shn - 1));
      inexact = (rest != 0) | st;
      fint = (sht - 8 > 52) ? 0 : (sht >= 8) ? (rest >> (sht - 8)) : (rest << (8 - sht));
      fintn = (shn >= 8) ? (restn >> (shn - 8)) : (restn << (8 - shn));
      up = m0_rup(rnd, s, inexact, rest, halfv, st, keep[0], fint, word);
      upn = m0_rup(rnd, s, (restn != 0) | st, restn, halfn, st, keepn[0], fintn, word);
      carry_n = ((keepn + upn) == ({{52{1'b0}}, 1'b1} << (23 + 1)));
      mag = keep + up;
      if (biased < 1) biased = 0;
      code = (biased < 1) ? mag : ((biased << 23) + mag - ({{(32+16){1'b0}}, 1'b1} << 23));
      tiny = 0 ? (eu < -126) : ((eu < -126) && !(eu == -126 - 1 && carry_n) && !(eu + 127 == 0 && carry_n));
      ovf = (code > 31'd2139095039);
      if (ovf) begin
        to_inf = 1 && (rnd == 3'd0 || (rnd == 3'd3 && !s) || (rnd == 3'd2 && s) || rnd == 3'd5 || (rnd == 3'd4 && (eu > 127 || up)));
        outb = to_inf ? {s, 31'd2139095040} : {s, 31'd2139095039};
        fl[2] = 1'b1; fl[4] = 1'b1;
      end else begin
        outb = {s, code[30:0]};
        if (inexact) fl[4] = 1'b1;
        if (tiny && inexact) fl[3] = 1'b1;
        if (ftz && code[31-1:23] == 0 && code[22:0] != 0) begin
          outb = {s, {31{1'b0}}}; fl[4] = 1'b1; fl[3] = 1'b1;
        end

      end
    end
    m0_pack_d = {fl, outb};
  endfunction


  function automatic [71:0] m0_acc2x(input signed [280:0] acc);
    logic s; logic [280:0] mag; logic signed [15:0] ex; integer k; logic st;
    s = acc < 0; mag = s ? -acc : acc; ex = -149 + 229;
    if (mag == 0) m0_acc2x = m0_mkx(2'd0, 1'b0, 0, 0, 1'b0);
    else begin
      for (k = 256; k >= 1; k = k / 2) begin
        if (k < 281) begin
          if ((mag >> (281 - k)) == 0) begin mag = mag << k; ex = ex - k; end
        end
      end
      st = (mag[228:0] != 0);
      m0_acc2x = m0_mkx(2'd0, s, ex, mag[280:229], st);
    end
  endfunction

  function automatic signed [280:0] m0_term(input s, input signed [15:0] ex, input [103:0] sig2);
    logic [280:0] t; logic signed [16:0] sh;
    sh = ex - (-149);
    if (sh >= 0) t = {{(281-2*52){1'b0}}, sig2} << sh;
    else t = {{(281-2*52){1'b0}}, sig2} >> (-sh);
    m0_term = s ? -$signed(t) : $signed(t);
  endfunction
  function automatic signed [280:0] m0_termx(input [71:0] x);
    logic [280:0] t; logic signed [16:0] sh;
    sh = $signed(x[68:53]) - (-149);
    if (sh >= 0) t = {{(281-52){1'b0}}, x[52:1]} << sh;
    else t = {{(281-52){1'b0}}, x[52:1]} >> (-sh);
    m0_termx = x[69] ? -$signed(t) : $signed(t);
  endfunction
  logic [31:0] d_m0;
  logic [9:0] fl_m0;
  logic [43:0] m0_ua0;
  assign m0_ua0 = m0_unpack_ab(a[0 +: 8], daz);
  logic [71:0] m0_xa0; logic m0_dena0;
  assign m0_xa0 = m0_x(m0_ua0[42:0]);
  assign m0_dena0 = m0_ua0[43];
  logic [43:0] m0_ua1;
  assign m0_ua1 = m0_unpack_ab(a[8 +: 8], daz);
  logic [71:0] m0_xa1; logic m0_dena1;
  assign m0_xa1 = m0_x(m0_ua1[42:0]);
  assign m0_dena1 = m0_ua1[43];
  logic [43:0] m0_ua2;
  assign m0_ua2 = m0_unpack_ab(a[16 +: 8], daz);
  logic [71:0] m0_xa2; logic m0_dena2;
  assign m0_xa2 = m0_x(m0_ua2[42:0]);
  assign m0_dena2 = m0_ua2[43];
  logic [43:0] m0_ua3;
  assign m0_ua3 = m0_unpack_ab(a[24 +: 8], daz);
  logic [71:0] m0_xa3; logic m0_dena3;
  assign m0_xa3 = m0_x(m0_ua3[42:0]);
  assign m0_dena3 = m0_ua3[43];
  logic [43:0] m0_ub0;
  assign m0_ub0 = m0_unpack_ab(b[0 +: 8], daz);
  logic [71:0] m0_xb0; logic m0_denb0;
  assign m0_xb0 = m0_x(m0_ub0[42:0]);
  assign m0_denb0 = m0_ub0[43];
  logic [43:0] m0_ub1;
  assign m0_ub1 = m0_unpack_ab(b[8 +: 8], daz);
  logic [71:0] m0_xb1; logic m0_denb1;
  assign m0_xb1 = m0_x(m0_ub1[42:0]);
  assign m0_denb1 = m0_ub1[43];
  logic [43:0] m0_ub2;
  assign m0_ub2 = m0_unpack_ab(b[16 +: 8], daz);
  logic [71:0] m0_xb2; logic m0_denb2;
  assign m0_xb2 = m0_x(m0_ub2[42:0]);
  assign m0_denb2 = m0_ub2[43];
  logic [43:0] m0_ub3;
  assign m0_ub3 = m0_unpack_ab(b[24 +: 8], daz);
  logic [71:0] m0_xb3; logic m0_denb3;
  assign m0_xb3 = m0_x(m0_ub3[42:0]);
  assign m0_denb3 = m0_ub3[43];
  logic [43:0] m0_uc0;
  assign m0_uc0 = m0_unpack_c(c[0 +: 32], daz);
  logic [71:0] m0_xc0; logic m0_denc0;
  assign m0_xc0 = m0_x(m0_uc0[42:0]);
  assign m0_denc0 = m0_uc0[43];
  logic signed [280:0] m0_acc0;
  logic [1:0] m0_sp0; logic m0_inf_s0, m0_nan0, m0_inv0, m0_den0, m0_allneg0, m0_anynz0;
  logic [287:0] m0_lxa0, m0_lxb0;
  assign m0_lxa0[0 +: 72] = m0_xa0; assign m0_lxb0[0 +: 72] = m0_xb0;
  assign m0_lxa0[72 +: 72] = m0_xa1; assign m0_lxb0[72 +: 72] = m0_xb1;
  assign m0_lxa0[144 +: 72] = m0_xa2; assign m0_lxb0[144 +: 72] = m0_xb2;
  assign m0_lxa0[216 +: 72] = m0_xa3; assign m0_lxb0[216 +: 72] = m0_xb3;
  logic [9:0] m0_lfl0;
  logic [71:0] m0_ly0;
  // core.family multi_term_fused_dot: output group 0 realized by the library module fam_dot_multi_term_fused_dot_n4_s3c24_a281lm149_x52e16s24_09ac12ad8924
  fam_dot_multi_term_fused_dot_n4_s3c24_a281lm149_x52e16s24_09ac12ad8924 u_m0_dot0 (.xa(m0_lxa0), .xb(m0_lxb0), .xc(m0_xc0), .fl(m0_lfl0), .y(m0_ly0));
  logic [71:0] m0_xr0; logic [41:0] m0_pk0;
  logic [9:0] m0_rfl0; logic [31:0] m0_rbits0;
  // the round component (increment_adder) of core.family multi_term_fused_dot: the library rounder packs d
  fam_fp_round_dedicated_per_op_increment_adder_fp32_x52e16s24_pe0f43f9cf852 u_m0_round0 (.x(m0_xr0), .rnd(rnd), .word(8'd0), .ftz(ftz), .fl(m0_rfl0), .bits(m0_rbits0));
  always_comb begin
    d_m0 = '0; fl_m0 = '0;
    m0_nan0 = 1'b0; m0_inv0 = 1'b0; m0_inf_s0 = 1'b0; m0_sp0 = 2'd0; m0_allneg0 = 1'b1; m0_anynz0 = 1'b0;
    m0_den0 = m0_dena0 | m0_denb0 | m0_dena1 | m0_denb1 | m0_dena2 | m0_denb2 | m0_dena3 | m0_denb3 | m0_denc0;
    if (m0_xa0[71:70] == 2'd1 || m0_xb0[71:70] == 2'd1 || ((m0_xa0[71:70] == 2'd2 || m0_xb0[71:70] == 2'd2) && ((m0_xa0[71:70] == 2'd0 && m0_xa0[52:1] == 0) || (m0_xb0[71:70] == 2'd0 && m0_xb0[52:1] == 0)))) begin m0_nan0 = 1'b1; m0_inv0 = m0_inv0 | !(m0_xa0[71:70] == 2'd1 || m0_xb0[71:70] == 2'd1); end
    else if (m0_xa0[71:70] == 2'd2 || m0_xb0[71:70] == 2'd2) begin if (m0_sp0 == 2'd2 && m0_inf_s0 != (m0_xa0[69] ^ m0_xb0[69])) begin m0_nan0 = 1'b1; m0_inv0 = 1'b1; end m0_sp0 = 2'd2; m0_inf_s0 = (m0_xa0[69] ^ m0_xb0[69]); end
    else begin if (!(m0_xa0[71:70] == 2'd0 && m0_xa0[52:1] == 0) && !(m0_xb0[71:70] == 2'd0 && m0_xb0[52:1] == 0)) m0_anynz0 = 1'b1; if (!(m0_xa0[69] ^ m0_xb0[69])) m0_allneg0 = 1'b0; end
    if (m0_xa1[71:70] == 2'd1 || m0_xb1[71:70] == 2'd1 || ((m0_xa1[71:70] == 2'd2 || m0_xb1[71:70] == 2'd2) && ((m0_xa1[71:70] == 2'd0 && m0_xa1[52:1] == 0) || (m0_xb1[71:70] == 2'd0 && m0_xb1[52:1] == 0)))) begin m0_nan0 = 1'b1; m0_inv0 = m0_inv0 | !(m0_xa1[71:70] == 2'd1 || m0_xb1[71:70] == 2'd1); end
    else if (m0_xa1[71:70] == 2'd2 || m0_xb1[71:70] == 2'd2) begin if (m0_sp0 == 2'd2 && m0_inf_s0 != (m0_xa1[69] ^ m0_xb1[69])) begin m0_nan0 = 1'b1; m0_inv0 = 1'b1; end m0_sp0 = 2'd2; m0_inf_s0 = (m0_xa1[69] ^ m0_xb1[69]); end
    else begin if (!(m0_xa1[71:70] == 2'd0 && m0_xa1[52:1] == 0) && !(m0_xb1[71:70] == 2'd0 && m0_xb1[52:1] == 0)) m0_anynz0 = 1'b1; if (!(m0_xa1[69] ^ m0_xb1[69])) m0_allneg0 = 1'b0; end
    if (m0_xa2[71:70] == 2'd1 || m0_xb2[71:70] == 2'd1 || ((m0_xa2[71:70] == 2'd2 || m0_xb2[71:70] == 2'd2) && ((m0_xa2[71:70] == 2'd0 && m0_xa2[52:1] == 0) || (m0_xb2[71:70] == 2'd0 && m0_xb2[52:1] == 0)))) begin m0_nan0 = 1'b1; m0_inv0 = m0_inv0 | !(m0_xa2[71:70] == 2'd1 || m0_xb2[71:70] == 2'd1); end
    else if (m0_xa2[71:70] == 2'd2 || m0_xb2[71:70] == 2'd2) begin if (m0_sp0 == 2'd2 && m0_inf_s0 != (m0_xa2[69] ^ m0_xb2[69])) begin m0_nan0 = 1'b1; m0_inv0 = 1'b1; end m0_sp0 = 2'd2; m0_inf_s0 = (m0_xa2[69] ^ m0_xb2[69]); end
    else begin if (!(m0_xa2[71:70] == 2'd0 && m0_xa2[52:1] == 0) && !(m0_xb2[71:70] == 2'd0 && m0_xb2[52:1] == 0)) m0_anynz0 = 1'b1; if (!(m0_xa2[69] ^ m0_xb2[69])) m0_allneg0 = 1'b0; end
    if (m0_xa3[71:70] == 2'd1 || m0_xb3[71:70] == 2'd1 || ((m0_xa3[71:70] == 2'd2 || m0_xb3[71:70] == 2'd2) && ((m0_xa3[71:70] == 2'd0 && m0_xa3[52:1] == 0) || (m0_xb3[71:70] == 2'd0 && m0_xb3[52:1] == 0)))) begin m0_nan0 = 1'b1; m0_inv0 = m0_inv0 | !(m0_xa3[71:70] == 2'd1 || m0_xb3[71:70] == 2'd1); end
    else if (m0_xa3[71:70] == 2'd2 || m0_xb3[71:70] == 2'd2) begin if (m0_sp0 == 2'd2 && m0_inf_s0 != (m0_xa3[69] ^ m0_xb3[69])) begin m0_nan0 = 1'b1; m0_inv0 = 1'b1; end m0_sp0 = 2'd2; m0_inf_s0 = (m0_xa3[69] ^ m0_xb3[69]); end
    else begin if (!(m0_xa3[71:70] == 2'd0 && m0_xa3[52:1] == 0) && !(m0_xb3[71:70] == 2'd0 && m0_xb3[52:1] == 0)) m0_anynz0 = 1'b1; if (!(m0_xa3[69] ^ m0_xb3[69])) m0_allneg0 = 1'b0; end
    m0_acc0 = m0_termx(m0_ly0);
    if (m0_xc0[71:70] == 2'd1) m0_nan0 = 1'b1;
    else if (m0_xc0[71:70] == 2'd2) begin if (m0_sp0 == 2'd2 && m0_inf_s0 != m0_xc0[69]) begin m0_nan0 = 1'b1; m0_inv0 = 1'b1; end m0_sp0 = 2'd2; m0_inf_s0 = m0_xc0[69]; end
    else begin if (m0_xc0[52:1] != 0) m0_anynz0 = 1'b1; if (!m0_xc0[69]) m0_allneg0 = 1'b0; end
    if (((m0_xc0[71:70] == 2'd1) && !c[22])) m0_inv0 = 1'b1;
    if (((m0_xa0[71:70] == 2'd1) && !a[1]) || ((m0_xb0[71:70] == 2'd1) && !b[1])) m0_inv0 = 1'b1;
    if (((m0_xa1[71:70] == 2'd1) && !a[9]) || ((m0_xb1[71:70] == 2'd1) && !b[9])) m0_inv0 = 1'b1;
    if (((m0_xa2[71:70] == 2'd1) && !a[17]) || ((m0_xb2[71:70] == 2'd1) && !b[17])) m0_inv0 = 1'b1;
    if (((m0_xa3[71:70] == 2'd1) && !a[25]) || ((m0_xb3[71:70] == 2'd1) && !b[25])) m0_inv0 = 1'b1;
    if (m0_nan0) m0_xr0 = m0_mkx(2'd1, 1'b0, 0, 0, 1'b0);
    else if (m0_sp0 == 2'd2) m0_xr0 = m0_mkx(2'd2, m0_inf_s0, 0, 0, 1'b0);
    else begin m0_xr0 = m0_ly0; if (m0_ly0[71:70] == 2'd0 && m0_ly0[52:1] == 0 && !m0_ly0[0]) m0_xr0[69] = (m0_allneg0 || (rnd == 3'd2 && m0_anynz0)); end
    m0_pk0 = {m0_rfl0, m0_rbits0};
    d_m0[0 +: 32] = m0_pk0[31:0];
    fl_m0[0*10 +: 10] = m0_pk0[41:32] | (m0_inv0 ? (10'd1 << 0) : 10'd0) | (m0_den0 ? (10'd1 << 6) : 10'd0) | ((m0_nan0 || m0_sp0 == 2'd2) ? 10'd0 : m0_lfl0);
  end
  logic [9:0] fl_all;
  assign d = d_m0;
  assign fl_all = fl_m0;
endmodule
// EVOLVE-BLOCK-END
// ---- the family library modules the core instantiates (chialu/targets/rtl/families; fixed text, replaced by editing the instances)
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




// lzd_cell_tree (pair_cell, binary_count, valid flags flat): the leading zeros of a 76-bit word
module fam_count_lzd_pair_cell_binary_count_vflat_w76 (input logic [75:0] a, output logic [6:0] n);
  logic v0_0; assign v0_0 = a[75] | a[74];
  logic p0_0; assign p0_0 = ~a[75];
  logic v0_1; assign v0_1 = a[73] | a[72];
  logic p0_1; assign p0_1 = ~a[73];
  logic v0_2; assign v0_2 = a[71] | a[70];
  logic p0_2; assign p0_2 = ~a[71];
  logic v0_3; assign v0_3 = a[69] | a[68];
  logic p0_3; assign p0_3 = ~a[69];
  logic v0_4; assign v0_4 = a[67] | a[66];
  logic p0_4; assign p0_4 = ~a[67];
  logic v0_5; assign v0_5 = a[65] | a[64];
  logic p0_5; assign p0_5 = ~a[65];
  logic v0_6; assign v0_6 = a[63] | a[62];
  logic p0_6; assign p0_6 = ~a[63];
  logic v0_7; assign v0_7 = a[61] | a[60];
  logic p0_7; assign p0_7 = ~a[61];
  logic v0_8; assign v0_8 = a[59] | a[58];
  logic p0_8; assign p0_8 = ~a[59];
  logic v0_9; assign v0_9 = a[57] | a[56];
  logic p0_9; assign p0_9 = ~a[57];
  logic v0_10; assign v0_10 = a[55] | a[54];
  logic p0_10; assign p0_10 = ~a[55];
  logic v0_11; assign v0_11 = a[53] | a[52];
  logic p0_11; assign p0_11 = ~a[53];
  logic v0_12; assign v0_12 = a[51] | a[50];
  logic p0_12; assign p0_12 = ~a[51];
  logic v0_13; assign v0_13 = a[49] | a[48];
  logic p0_13; assign p0_13 = ~a[49];
  logic v0_14; assign v0_14 = a[47] | a[46];
  logic p0_14; assign p0_14 = ~a[47];
  logic v0_15; assign v0_15 = a[45] | a[44];
  logic p0_15; assign p0_15 = ~a[45];
  logic v0_16; assign v0_16 = a[43] | a[42];
  logic p0_16; assign p0_16 = ~a[43];
  logic v0_17; assign v0_17 = a[41] | a[40];
  logic p0_17; assign p0_17 = ~a[41];
  logic v0_18; assign v0_18 = a[39] | a[38];
  logic p0_18; assign p0_18 = ~a[39];
  logic v0_19; assign v0_19 = a[37] | a[36];
  logic p0_19; assign p0_19 = ~a[37];
  logic v0_20; assign v0_20 = a[35] | a[34];
  logic p0_20; assign p0_20 = ~a[35];
  logic v0_21; assign v0_21 = a[33] | a[32];
  logic p0_21; assign p0_21 = ~a[33];
  logic v0_22; assign v0_22 = a[31] | a[30];
  logic p0_22; assign p0_22 = ~a[31];
  logic v0_23; assign v0_23 = a[29] | a[28];
  logic p0_23; assign p0_23 = ~a[29];
  logic v0_24; assign v0_24 = a[27] | a[26];
  logic p0_24; assign p0_24 = ~a[27];
  logic v0_25; assign v0_25 = a[25] | a[24];
  logic p0_25; assign p0_25 = ~a[25];
  logic v0_26; assign v0_26 = a[23] | a[22];
  logic p0_26; assign p0_26 = ~a[23];
  logic v0_27; assign v0_27 = a[21] | a[20];
  logic p0_27; assign p0_27 = ~a[21];
  logic v0_28; assign v0_28 = a[19] | a[18];
  logic p0_28; assign p0_28 = ~a[19];
  logic v0_29; assign v0_29 = a[17] | a[16];
  logic p0_29; assign p0_29 = ~a[17];
  logic v0_30; assign v0_30 = a[15] | a[14];
  logic p0_30; assign p0_30 = ~a[15];
  logic v0_31; assign v0_31 = a[13] | a[12];
  logic p0_31; assign p0_31 = ~a[13];
  logic v0_32; assign v0_32 = a[11] | a[10];
  logic p0_32; assign p0_32 = ~a[11];
  logic v0_33; assign v0_33 = a[9] | a[8];
  logic p0_33; assign p0_33 = ~a[9];
  logic v0_34; assign v0_34 = a[7] | a[6];
  logic p0_34; assign p0_34 = ~a[7];
  logic v0_35; assign v0_35 = a[5] | a[4];
  logic p0_35; assign p0_35 = ~a[5];
  logic v0_36; assign v0_36 = a[3] | a[2];
  logic p0_36; assign p0_36 = ~a[3];
  logic v0_37; assign v0_37 = a[1] | a[0];
  logic p0_37; assign p0_37 = ~a[1];
  logic v0_38; assign v0_38 = 1'b0 | 1'b0;
  logic p0_38; assign p0_38 = ~1'b0;
  logic v0_39; assign v0_39 = 1'b0 | 1'b0;
  logic p0_39; assign p0_39 = ~1'b0;
  logic v0_40; assign v0_40 = 1'b0 | 1'b0;
  logic p0_40; assign p0_40 = ~1'b0;
  logic v0_41; assign v0_41 = 1'b0 | 1'b0;
  logic p0_41; assign p0_41 = ~1'b0;
  logic v0_42; assign v0_42 = 1'b0 | 1'b0;
  logic p0_42; assign p0_42 = ~1'b0;
  logic v0_43; assign v0_43 = 1'b0 | 1'b0;
  logic p0_43; assign p0_43 = ~1'b0;
  logic v0_44; assign v0_44 = 1'b0 | 1'b0;
  logic p0_44; assign p0_44 = ~1'b0;
  logic v0_45; assign v0_45 = 1'b0 | 1'b0;
  logic p0_45; assign p0_45 = ~1'b0;
  logic v0_46; assign v0_46 = 1'b0 | 1'b0;
  logic p0_46; assign p0_46 = ~1'b0;
  logic v0_47; assign v0_47 = 1'b0 | 1'b0;
  logic p0_47; assign p0_47 = ~1'b0;
  logic v0_48; assign v0_48 = 1'b0 | 1'b0;
  logic p0_48; assign p0_48 = ~1'b0;
  logic v0_49; assign v0_49 = 1'b0 | 1'b0;
  logic p0_49; assign p0_49 = ~1'b0;
  logic v0_50; assign v0_50 = 1'b0 | 1'b0;
  logic p0_50; assign p0_50 = ~1'b0;
  logic v0_51; assign v0_51 = 1'b0 | 1'b0;
  logic p0_51; assign p0_51 = ~1'b0;
  logic v0_52; assign v0_52 = 1'b0 | 1'b0;
  logic p0_52; assign p0_52 = ~1'b0;
  logic v0_53; assign v0_53 = 1'b0 | 1'b0;
  logic p0_53; assign p0_53 = ~1'b0;
  logic v0_54; assign v0_54 = 1'b0 | 1'b0;
  logic p0_54; assign p0_54 = ~1'b0;
  logic v0_55; assign v0_55 = 1'b0 | 1'b0;
  logic p0_55; assign p0_55 = ~1'b0;
  logic v0_56; assign v0_56 = 1'b0 | 1'b0;
  logic p0_56; assign p0_56 = ~1'b0;
  logic v0_57; assign v0_57 = 1'b0 | 1'b0;
  logic p0_57; assign p0_57 = ~1'b0;
  logic v0_58; assign v0_58 = 1'b0 | 1'b0;
  logic p0_58; assign p0_58 = ~1'b0;
  logic v0_59; assign v0_59 = 1'b0 | 1'b0;
  logic p0_59; assign p0_59 = ~1'b0;
  logic v0_60; assign v0_60 = 1'b0 | 1'b0;
  logic p0_60; assign p0_60 = ~1'b0;
  logic v0_61; assign v0_61 = 1'b0 | 1'b0;
  logic p0_61; assign p0_61 = ~1'b0;
  logic v0_62; assign v0_62 = 1'b0 | 1'b0;
  logic p0_62; assign p0_62 = ~1'b0;
  logic v0_63; assign v0_63 = 1'b0 | 1'b0;
  logic p0_63; assign p0_63 = ~1'b0;
  logic v1_0; assign v1_0 = a[75] | a[74] | a[73] | a[72];
  logic [1:0] p1_0; assign p1_0 = v0_0 ? {1'b0, p0_0} : {1'b1, p0_1};
  logic v1_1; assign v1_1 = a[71] | a[70] | a[69] | a[68];
  logic [1:0] p1_1; assign p1_1 = v0_2 ? {1'b0, p0_2} : {1'b1, p0_3};
  logic v1_2; assign v1_2 = a[67] | a[66] | a[65] | a[64];
  logic [1:0] p1_2; assign p1_2 = v0_4 ? {1'b0, p0_4} : {1'b1, p0_5};
  logic v1_3; assign v1_3 = a[63] | a[62] | a[61] | a[60];
  logic [1:0] p1_3; assign p1_3 = v0_6 ? {1'b0, p0_6} : {1'b1, p0_7};
  logic v1_4; assign v1_4 = a[59] | a[58] | a[57] | a[56];
  logic [1:0] p1_4; assign p1_4 = v0_8 ? {1'b0, p0_8} : {1'b1, p0_9};
  logic v1_5; assign v1_5 = a[55] | a[54] | a[53] | a[52];
  logic [1:0] p1_5; assign p1_5 = v0_10 ? {1'b0, p0_10} : {1'b1, p0_11};
  logic v1_6; assign v1_6 = a[51] | a[50] | a[49] | a[48];
  logic [1:0] p1_6; assign p1_6 = v0_12 ? {1'b0, p0_12} : {1'b1, p0_13};
  logic v1_7; assign v1_7 = a[47] | a[46] | a[45] | a[44];
  logic [1:0] p1_7; assign p1_7 = v0_14 ? {1'b0, p0_14} : {1'b1, p0_15};
  logic v1_8; assign v1_8 = a[43] | a[42] | a[41] | a[40];
  logic [1:0] p1_8; assign p1_8 = v0_16 ? {1'b0, p0_16} : {1'b1, p0_17};
  logic v1_9; assign v1_9 = a[39] | a[38] | a[37] | a[36];
  logic [1:0] p1_9; assign p1_9 = v0_18 ? {1'b0, p0_18} : {1'b1, p0_19};
  logic v1_10; assign v1_10 = a[35] | a[34] | a[33] | a[32];
  logic [1:0] p1_10; assign p1_10 = v0_20 ? {1'b0, p0_20} : {1'b1, p0_21};
  logic v1_11; assign v1_11 = a[31] | a[30] | a[29] | a[28];
  logic [1:0] p1_11; assign p1_11 = v0_22 ? {1'b0, p0_22} : {1'b1, p0_23};
  logic v1_12; assign v1_12 = a[27] | a[26] | a[25] | a[24];
  logic [1:0] p1_12; assign p1_12 = v0_24 ? {1'b0, p0_24} : {1'b1, p0_25};
  logic v1_13; assign v1_13 = a[23] | a[22] | a[21] | a[20];
  logic [1:0] p1_13; assign p1_13 = v0_26 ? {1'b0, p0_26} : {1'b1, p0_27};
  logic v1_14; assign v1_14 = a[19] | a[18] | a[17] | a[16];
  logic [1:0] p1_14; assign p1_14 = v0_28 ? {1'b0, p0_28} : {1'b1, p0_29};
  logic v1_15; assign v1_15 = a[15] | a[14] | a[13] | a[12];
  logic [1:0] p1_15; assign p1_15 = v0_30 ? {1'b0, p0_30} : {1'b1, p0_31};
  logic v1_16; assign v1_16 = a[11] | a[10] | a[9] | a[8];
  logic [1:0] p1_16; assign p1_16 = v0_32 ? {1'b0, p0_32} : {1'b1, p0_33};
  logic v1_17; assign v1_17 = a[7] | a[6] | a[5] | a[4];
  logic [1:0] p1_17; assign p1_17 = v0_34 ? {1'b0, p0_34} : {1'b1, p0_35};
  logic v1_18; assign v1_18 = a[3] | a[2] | a[1] | a[0];
  logic [1:0] p1_18; assign p1_18 = v0_36 ? {1'b0, p0_36} : {1'b1, p0_37};
  logic v1_19; assign v1_19 = 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [1:0] p1_19; assign p1_19 = v0_38 ? {1'b0, p0_38} : {1'b1, p0_39};
  logic v1_20; assign v1_20 = 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [1:0] p1_20; assign p1_20 = v0_40 ? {1'b0, p0_40} : {1'b1, p0_41};
  logic v1_21; assign v1_21 = 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [1:0] p1_21; assign p1_21 = v0_42 ? {1'b0, p0_42} : {1'b1, p0_43};
  logic v1_22; assign v1_22 = 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [1:0] p1_22; assign p1_22 = v0_44 ? {1'b0, p0_44} : {1'b1, p0_45};
  logic v1_23; assign v1_23 = 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [1:0] p1_23; assign p1_23 = v0_46 ? {1'b0, p0_46} : {1'b1, p0_47};
  logic v1_24; assign v1_24 = 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [1:0] p1_24; assign p1_24 = v0_48 ? {1'b0, p0_48} : {1'b1, p0_49};
  logic v1_25; assign v1_25 = 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [1:0] p1_25; assign p1_25 = v0_50 ? {1'b0, p0_50} : {1'b1, p0_51};
  logic v1_26; assign v1_26 = 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [1:0] p1_26; assign p1_26 = v0_52 ? {1'b0, p0_52} : {1'b1, p0_53};
  logic v1_27; assign v1_27 = 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [1:0] p1_27; assign p1_27 = v0_54 ? {1'b0, p0_54} : {1'b1, p0_55};
  logic v1_28; assign v1_28 = 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [1:0] p1_28; assign p1_28 = v0_56 ? {1'b0, p0_56} : {1'b1, p0_57};
  logic v1_29; assign v1_29 = 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [1:0] p1_29; assign p1_29 = v0_58 ? {1'b0, p0_58} : {1'b1, p0_59};
  logic v1_30; assign v1_30 = 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [1:0] p1_30; assign p1_30 = v0_60 ? {1'b0, p0_60} : {1'b1, p0_61};
  logic v1_31; assign v1_31 = 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [1:0] p1_31; assign p1_31 = v0_62 ? {1'b0, p0_62} : {1'b1, p0_63};
  logic v2_0; assign v2_0 = a[75] | a[74] | a[73] | a[72] | a[71] | a[70] | a[69] | a[68];
  logic [2:0] p2_0; assign p2_0 = v1_0 ? {1'b0, p1_0} : {1'b1, p1_1};
  logic v2_1; assign v2_1 = a[67] | a[66] | a[65] | a[64] | a[63] | a[62] | a[61] | a[60];
  logic [2:0] p2_1; assign p2_1 = v1_2 ? {1'b0, p1_2} : {1'b1, p1_3};
  logic v2_2; assign v2_2 = a[59] | a[58] | a[57] | a[56] | a[55] | a[54] | a[53] | a[52];
  logic [2:0] p2_2; assign p2_2 = v1_4 ? {1'b0, p1_4} : {1'b1, p1_5};
  logic v2_3; assign v2_3 = a[51] | a[50] | a[49] | a[48] | a[47] | a[46] | a[45] | a[44];
  logic [2:0] p2_3; assign p2_3 = v1_6 ? {1'b0, p1_6} : {1'b1, p1_7};
  logic v2_4; assign v2_4 = a[43] | a[42] | a[41] | a[40] | a[39] | a[38] | a[37] | a[36];
  logic [2:0] p2_4; assign p2_4 = v1_8 ? {1'b0, p1_8} : {1'b1, p1_9};
  logic v2_5; assign v2_5 = a[35] | a[34] | a[33] | a[32] | a[31] | a[30] | a[29] | a[28];
  logic [2:0] p2_5; assign p2_5 = v1_10 ? {1'b0, p1_10} : {1'b1, p1_11};
  logic v2_6; assign v2_6 = a[27] | a[26] | a[25] | a[24] | a[23] | a[22] | a[21] | a[20];
  logic [2:0] p2_6; assign p2_6 = v1_12 ? {1'b0, p1_12} : {1'b1, p1_13};
  logic v2_7; assign v2_7 = a[19] | a[18] | a[17] | a[16] | a[15] | a[14] | a[13] | a[12];
  logic [2:0] p2_7; assign p2_7 = v1_14 ? {1'b0, p1_14} : {1'b1, p1_15};
  logic v2_8; assign v2_8 = a[11] | a[10] | a[9] | a[8] | a[7] | a[6] | a[5] | a[4];
  logic [2:0] p2_8; assign p2_8 = v1_16 ? {1'b0, p1_16} : {1'b1, p1_17};
  logic v2_9; assign v2_9 = a[3] | a[2] | a[1] | a[0] | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [2:0] p2_9; assign p2_9 = v1_18 ? {1'b0, p1_18} : {1'b1, p1_19};
  logic v2_10; assign v2_10 = 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [2:0] p2_10; assign p2_10 = v1_20 ? {1'b0, p1_20} : {1'b1, p1_21};
  logic v2_11; assign v2_11 = 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [2:0] p2_11; assign p2_11 = v1_22 ? {1'b0, p1_22} : {1'b1, p1_23};
  logic v2_12; assign v2_12 = 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [2:0] p2_12; assign p2_12 = v1_24 ? {1'b0, p1_24} : {1'b1, p1_25};
  logic v2_13; assign v2_13 = 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [2:0] p2_13; assign p2_13 = v1_26 ? {1'b0, p1_26} : {1'b1, p1_27};
  logic v2_14; assign v2_14 = 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [2:0] p2_14; assign p2_14 = v1_28 ? {1'b0, p1_28} : {1'b1, p1_29};
  logic v2_15; assign v2_15 = 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [2:0] p2_15; assign p2_15 = v1_30 ? {1'b0, p1_30} : {1'b1, p1_31};
  logic v3_0; assign v3_0 = a[75] | a[74] | a[73] | a[72] | a[71] | a[70] | a[69] | a[68] | a[67] | a[66] | a[65] | a[64] | a[63] | a[62] | a[61] | a[60];
  logic [3:0] p3_0; assign p3_0 = v2_0 ? {1'b0, p2_0} : {1'b1, p2_1};
  logic v3_1; assign v3_1 = a[59] | a[58] | a[57] | a[56] | a[55] | a[54] | a[53] | a[52] | a[51] | a[50] | a[49] | a[48] | a[47] | a[46] | a[45] | a[44];
  logic [3:0] p3_1; assign p3_1 = v2_2 ? {1'b0, p2_2} : {1'b1, p2_3};
  logic v3_2; assign v3_2 = a[43] | a[42] | a[41] | a[40] | a[39] | a[38] | a[37] | a[36] | a[35] | a[34] | a[33] | a[32] | a[31] | a[30] | a[29] | a[28];
  logic [3:0] p3_2; assign p3_2 = v2_4 ? {1'b0, p2_4} : {1'b1, p2_5};
  logic v3_3; assign v3_3 = a[27] | a[26] | a[25] | a[24] | a[23] | a[22] | a[21] | a[20] | a[19] | a[18] | a[17] | a[16] | a[15] | a[14] | a[13] | a[12];
  logic [3:0] p3_3; assign p3_3 = v2_6 ? {1'b0, p2_6} : {1'b1, p2_7};
  logic v3_4; assign v3_4 = a[11] | a[10] | a[9] | a[8] | a[7] | a[6] | a[5] | a[4] | a[3] | a[2] | a[1] | a[0] | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [3:0] p3_4; assign p3_4 = v2_8 ? {1'b0, p2_8} : {1'b1, p2_9};
  logic v3_5; assign v3_5 = 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [3:0] p3_5; assign p3_5 = v2_10 ? {1'b0, p2_10} : {1'b1, p2_11};
  logic v3_6; assign v3_6 = 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [3:0] p3_6; assign p3_6 = v2_12 ? {1'b0, p2_12} : {1'b1, p2_13};
  logic v3_7; assign v3_7 = 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [3:0] p3_7; assign p3_7 = v2_14 ? {1'b0, p2_14} : {1'b1, p2_15};
  logic v4_0; assign v4_0 = a[75] | a[74] | a[73] | a[72] | a[71] | a[70] | a[69] | a[68] | a[67] | a[66] | a[65] | a[64] | a[63] | a[62] | a[61] | a[60] | a[59] | a[58] | a[57] | a[56] | a[55] | a[54] | a[53] | a[52] | a[51] | a[50] | a[49] | a[48] | a[47] | a[46] | a[45] | a[44];
  logic [4:0] p4_0; assign p4_0 = v3_0 ? {1'b0, p3_0} : {1'b1, p3_1};
  logic v4_1; assign v4_1 = a[43] | a[42] | a[41] | a[40] | a[39] | a[38] | a[37] | a[36] | a[35] | a[34] | a[33] | a[32] | a[31] | a[30] | a[29] | a[28] | a[27] | a[26] | a[25] | a[24] | a[23] | a[22] | a[21] | a[20] | a[19] | a[18] | a[17] | a[16] | a[15] | a[14] | a[13] | a[12];
  logic [4:0] p4_1; assign p4_1 = v3_2 ? {1'b0, p3_2} : {1'b1, p3_3};
  logic v4_2; assign v4_2 = a[11] | a[10] | a[9] | a[8] | a[7] | a[6] | a[5] | a[4] | a[3] | a[2] | a[1] | a[0] | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [4:0] p4_2; assign p4_2 = v3_4 ? {1'b0, p3_4} : {1'b1, p3_5};
  logic v4_3; assign v4_3 = 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [4:0] p4_3; assign p4_3 = v3_6 ? {1'b0, p3_6} : {1'b1, p3_7};
  logic v5_0; assign v5_0 = a[75] | a[74] | a[73] | a[72] | a[71] | a[70] | a[69] | a[68] | a[67] | a[66] | a[65] | a[64] | a[63] | a[62] | a[61] | a[60] | a[59] | a[58] | a[57] | a[56] | a[55] | a[54] | a[53] | a[52] | a[51] | a[50] | a[49] | a[48] | a[47] | a[46] | a[45] | a[44] | a[43] | a[42] | a[41] | a[40] | a[39] | a[38] | a[37] | a[36] | a[35] | a[34] | a[33] | a[32] | a[31] | a[30] | a[29] | a[28] | a[27] | a[26] | a[25] | a[24] | a[23] | a[22] | a[21] | a[20] | a[19] | a[18] | a[17] | a[16] | a[15] | a[14] | a[13] | a[12];
  logic [5:0] p5_0; assign p5_0 = v4_0 ? {1'b0, p4_0} : {1'b1, p4_1};
  logic v5_1; assign v5_1 = a[11] | a[10] | a[9] | a[8] | a[7] | a[6] | a[5] | a[4] | a[3] | a[2] | a[1] | a[0] | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [5:0] p5_1; assign p5_1 = v4_2 ? {1'b0, p4_2} : {1'b1, p4_3};
  logic v6_0; assign v6_0 = a[75] | a[74] | a[73] | a[72] | a[71] | a[70] | a[69] | a[68] | a[67] | a[66] | a[65] | a[64] | a[63] | a[62] | a[61] | a[60] | a[59] | a[58] | a[57] | a[56] | a[55] | a[54] | a[53] | a[52] | a[51] | a[50] | a[49] | a[48] | a[47] | a[46] | a[45] | a[44] | a[43] | a[42] | a[41] | a[40] | a[39] | a[38] | a[37] | a[36] | a[35] | a[34] | a[33] | a[32] | a[31] | a[30] | a[29] | a[28] | a[27] | a[26] | a[25] | a[24] | a[23] | a[22] | a[21] | a[20] | a[19] | a[18] | a[17] | a[16] | a[15] | a[14] | a[13] | a[12] | a[11] | a[10] | a[9] | a[8] | a[7] | a[6] | a[5] | a[4] | a[3] | a[2] | a[1] | a[0] | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0 | 1'b0;
  logic [6:0] p6_0; assign p6_0 = v5_0 ? {1'b0, p5_0} : {1'b1, p5_1};
  assign n = v6_0 ? p6_0 : 7'd76;
endmodule



// lzd_cell_tree (pair_cell, binary_count, valid flags propagated): the leading zeros of a 52-bit word
module fam_count_lzd_pair_cell_binary_count_vprop_w52 (input logic [51:0] a, output logic [5:0] n);
  logic v0_0; assign v0_0 = a[51] | a[50];
  logic p0_0; assign p0_0 = ~a[51];
  logic v0_1; assign v0_1 = a[49] | a[48];
  logic p0_1; assign p0_1 = ~a[49];
  logic v0_2; assign v0_2 = a[47] | a[46];
  logic p0_2; assign p0_2 = ~a[47];
  logic v0_3; assign v0_3 = a[45] | a[44];
  logic p0_3; assign p0_3 = ~a[45];
  logic v0_4; assign v0_4 = a[43] | a[42];
  logic p0_4; assign p0_4 = ~a[43];
  logic v0_5; assign v0_5 = a[41] | a[40];
  logic p0_5; assign p0_5 = ~a[41];
  logic v0_6; assign v0_6 = a[39] | a[38];
  logic p0_6; assign p0_6 = ~a[39];
  logic v0_7; assign v0_7 = a[37] | a[36];
  logic p0_7; assign p0_7 = ~a[37];
  logic v0_8; assign v0_8 = a[35] | a[34];
  logic p0_8; assign p0_8 = ~a[35];
  logic v0_9; assign v0_9 = a[33] | a[32];
  logic p0_9; assign p0_9 = ~a[33];
  logic v0_10; assign v0_10 = a[31] | a[30];
  logic p0_10; assign p0_10 = ~a[31];
  logic v0_11; assign v0_11 = a[29] | a[28];
  logic p0_11; assign p0_11 = ~a[29];
  logic v0_12; assign v0_12 = a[27] | a[26];
  logic p0_12; assign p0_12 = ~a[27];
  logic v0_13; assign v0_13 = a[25] | a[24];
  logic p0_13; assign p0_13 = ~a[25];
  logic v0_14; assign v0_14 = a[23] | a[22];
  logic p0_14; assign p0_14 = ~a[23];
  logic v0_15; assign v0_15 = a[21] | a[20];
  logic p0_15; assign p0_15 = ~a[21];
  logic v0_16; assign v0_16 = a[19] | a[18];
  logic p0_16; assign p0_16 = ~a[19];
  logic v0_17; assign v0_17 = a[17] | a[16];
  logic p0_17; assign p0_17 = ~a[17];
  logic v0_18; assign v0_18 = a[15] | a[14];
  logic p0_18; assign p0_18 = ~a[15];
  logic v0_19; assign v0_19 = a[13] | a[12];
  logic p0_19; assign p0_19 = ~a[13];
  logic v0_20; assign v0_20 = a[11] | a[10];
  logic p0_20; assign p0_20 = ~a[11];
  logic v0_21; assign v0_21 = a[9] | a[8];
  logic p0_21; assign p0_21 = ~a[9];
  logic v0_22; assign v0_22 = a[7] | a[6];
  logic p0_22; assign p0_22 = ~a[7];
  logic v0_23; assign v0_23 = a[5] | a[4];
  logic p0_23; assign p0_23 = ~a[5];
  logic v0_24; assign v0_24 = a[3] | a[2];
  logic p0_24; assign p0_24 = ~a[3];
  logic v0_25; assign v0_25 = a[1] | a[0];
  logic p0_25; assign p0_25 = ~a[1];
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
  logic v1_0; assign v1_0 = v0_0 | v0_1;
  logic [1:0] p1_0; assign p1_0 = v0_0 ? {1'b0, p0_0} : {1'b1, p0_1};
  logic v1_1; assign v1_1 = v0_2 | v0_3;
  logic [1:0] p1_1; assign p1_1 = v0_2 ? {1'b0, p0_2} : {1'b1, p0_3};
  logic v1_2; assign v1_2 = v0_4 | v0_5;
  logic [1:0] p1_2; assign p1_2 = v0_4 ? {1'b0, p0_4} : {1'b1, p0_5};
  logic v1_3; assign v1_3 = v0_6 | v0_7;
  logic [1:0] p1_3; assign p1_3 = v0_6 ? {1'b0, p0_6} : {1'b1, p0_7};
  logic v1_4; assign v1_4 = v0_8 | v0_9;
  logic [1:0] p1_4; assign p1_4 = v0_8 ? {1'b0, p0_8} : {1'b1, p0_9};
  logic v1_5; assign v1_5 = v0_10 | v0_11;
  logic [1:0] p1_5; assign p1_5 = v0_10 ? {1'b0, p0_10} : {1'b1, p0_11};
  logic v1_6; assign v1_6 = v0_12 | v0_13;
  logic [1:0] p1_6; assign p1_6 = v0_12 ? {1'b0, p0_12} : {1'b1, p0_13};
  logic v1_7; assign v1_7 = v0_14 | v0_15;
  logic [1:0] p1_7; assign p1_7 = v0_14 ? {1'b0, p0_14} : {1'b1, p0_15};
  logic v1_8; assign v1_8 = v0_16 | v0_17;
  logic [1:0] p1_8; assign p1_8 = v0_16 ? {1'b0, p0_16} : {1'b1, p0_17};
  logic v1_9; assign v1_9 = v0_18 | v0_19;
  logic [1:0] p1_9; assign p1_9 = v0_18 ? {1'b0, p0_18} : {1'b1, p0_19};
  logic v1_10; assign v1_10 = v0_20 | v0_21;
  logic [1:0] p1_10; assign p1_10 = v0_20 ? {1'b0, p0_20} : {1'b1, p0_21};
  logic v1_11; assign v1_11 = v0_22 | v0_23;
  logic [1:0] p1_11; assign p1_11 = v0_22 ? {1'b0, p0_22} : {1'b1, p0_23};
  logic v1_12; assign v1_12 = v0_24 | v0_25;
  logic [1:0] p1_12; assign p1_12 = v0_24 ? {1'b0, p0_24} : {1'b1, p0_25};
  logic v1_13; assign v1_13 = v0_26 | v0_27;
  logic [1:0] p1_13; assign p1_13 = v0_26 ? {1'b0, p0_26} : {1'b1, p0_27};
  logic v1_14; assign v1_14 = v0_28 | v0_29;
  logic [1:0] p1_14; assign p1_14 = v0_28 ? {1'b0, p0_28} : {1'b1, p0_29};
  logic v1_15; assign v1_15 = v0_30 | v0_31;
  logic [1:0] p1_15; assign p1_15 = v0_30 ? {1'b0, p0_30} : {1'b1, p0_31};
  logic v2_0; assign v2_0 = v1_0 | v1_1;
  logic [2:0] p2_0; assign p2_0 = v1_0 ? {1'b0, p1_0} : {1'b1, p1_1};
  logic v2_1; assign v2_1 = v1_2 | v1_3;
  logic [2:0] p2_1; assign p2_1 = v1_2 ? {1'b0, p1_2} : {1'b1, p1_3};
  logic v2_2; assign v2_2 = v1_4 | v1_5;
  logic [2:0] p2_2; assign p2_2 = v1_4 ? {1'b0, p1_4} : {1'b1, p1_5};
  logic v2_3; assign v2_3 = v1_6 | v1_7;
  logic [2:0] p2_3; assign p2_3 = v1_6 ? {1'b0, p1_6} : {1'b1, p1_7};
  logic v2_4; assign v2_4 = v1_8 | v1_9;
  logic [2:0] p2_4; assign p2_4 = v1_8 ? {1'b0, p1_8} : {1'b1, p1_9};
  logic v2_5; assign v2_5 = v1_10 | v1_11;
  logic [2:0] p2_5; assign p2_5 = v1_10 ? {1'b0, p1_10} : {1'b1, p1_11};
  logic v2_6; assign v2_6 = v1_12 | v1_13;
  logic [2:0] p2_6; assign p2_6 = v1_12 ? {1'b0, p1_12} : {1'b1, p1_13};
  logic v2_7; assign v2_7 = v1_14 | v1_15;
  logic [2:0] p2_7; assign p2_7 = v1_14 ? {1'b0, p1_14} : {1'b1, p1_15};
  logic v3_0; assign v3_0 = v2_0 | v2_1;
  logic [3:0] p3_0; assign p3_0 = v2_0 ? {1'b0, p2_0} : {1'b1, p2_1};
  logic v3_1; assign v3_1 = v2_2 | v2_3;
  logic [3:0] p3_1; assign p3_1 = v2_2 ? {1'b0, p2_2} : {1'b1, p2_3};
  logic v3_2; assign v3_2 = v2_4 | v2_5;
  logic [3:0] p3_2; assign p3_2 = v2_4 ? {1'b0, p2_4} : {1'b1, p2_5};
  logic v3_3; assign v3_3 = v2_6 | v2_7;
  logic [3:0] p3_3; assign p3_3 = v2_6 ? {1'b0, p2_6} : {1'b1, p2_7};
  logic v4_0; assign v4_0 = v3_0 | v3_1;
  logic [4:0] p4_0; assign p4_0 = v3_0 ? {1'b0, p3_0} : {1'b1, p3_1};
  logic v4_1; assign v4_1 = v3_2 | v3_3;
  logic [4:0] p4_1; assign p4_1 = v3_2 ? {1'b0, p3_2} : {1'b1, p3_3};
  logic v5_0; assign v5_0 = v4_0 | v4_1;
  logic [5:0] p5_0; assign p5_0 = v4_0 ? {1'b0, p4_0} : {1'b1, p4_1};
  assign n = v5_0 ? p5_0 : 6'd52;
endmodule


// dot-accumulate (multi_term_fused_dot) for 4 products of 3-bit significands and a 24-bit c on the engine geometry x52e16s24: 4 unrounded products aligned by pairwise_difference_reuse, sign handling dual, one normalize; meets the fused contract out of a 76-bit window: the bits below it reach the rounding through a sticky
module fam_dot_multi_term_fused_dot_n4_s3c24_a281lm149_x52e16s24_09ac12ad8924 (
  input logic [287:0] xa,
  input logic [287:0] xb,
  input logic [71:0] xc,
  output logic [71:0] y,
  output logic [9:0] fl
);
  logic [71:0] xa0; assign xa0 = xa[0 +: 72];
  logic [71:0] xb0; assign xb0 = xb[0 +: 72];
  logic [1:0] a0_sp; assign a0_sp = xa0[71:70];
  logic a0_s; assign a0_s = xa0[69];
  logic signed [15:0] a0_e; assign a0_e = $signed(xa0[68:53]);
  logic [51:0] a0_sig; assign a0_sig = xa0[52:1];
  logic a0_st; assign a0_st = xa0[0];
  logic a0_z; assign a0_z = (a0_sp == 2'd0) && (a0_sig == 0) && !a0_st;
  logic [1:0] b0_sp; assign b0_sp = xb0[71:70];
  logic b0_s; assign b0_s = xb0[69];
  logic signed [15:0] b0_e; assign b0_e = $signed(xb0[68:53]);
  logic [51:0] b0_sig; assign b0_sig = xb0[52:1];
  logic b0_st; assign b0_st = xb0[0];
  logic b0_z; assign b0_z = (b0_sp == 2'd0) && (b0_sig == 0) && !b0_st;
  logic [2:0] sa0; assign sa0 = a0_sig[2:0];
  logic [2:0] sb0; assign sb0 = b0_sig[2:0];
  logic signed [18:0] e0; assign e0 = $signed({{3{a0_e[15]}}, a0_e}) + $signed({{3{b0_e[15]}}, b0_e});
  logic s0; assign s0 = a0_s ^ b0_s;
  logic [71:0] xa1; assign xa1 = xa[72 +: 72];
  logic [71:0] xb1; assign xb1 = xb[72 +: 72];
  logic [1:0] a1_sp; assign a1_sp = xa1[71:70];
  logic a1_s; assign a1_s = xa1[69];
  logic signed [15:0] a1_e; assign a1_e = $signed(xa1[68:53]);
  logic [51:0] a1_sig; assign a1_sig = xa1[52:1];
  logic a1_st; assign a1_st = xa1[0];
  logic a1_z; assign a1_z = (a1_sp == 2'd0) && (a1_sig == 0) && !a1_st;
  logic [1:0] b1_sp; assign b1_sp = xb1[71:70];
  logic b1_s; assign b1_s = xb1[69];
  logic signed [15:0] b1_e; assign b1_e = $signed(xb1[68:53]);
  logic [51:0] b1_sig; assign b1_sig = xb1[52:1];
  logic b1_st; assign b1_st = xb1[0];
  logic b1_z; assign b1_z = (b1_sp == 2'd0) && (b1_sig == 0) && !b1_st;
  logic [2:0] sa1; assign sa1 = a1_sig[2:0];
  logic [2:0] sb1; assign sb1 = b1_sig[2:0];
  logic signed [18:0] e1; assign e1 = $signed({{3{a1_e[15]}}, a1_e}) + $signed({{3{b1_e[15]}}, b1_e});
  logic s1; assign s1 = a1_s ^ b1_s;
  logic [71:0] xa2; assign xa2 = xa[144 +: 72];
  logic [71:0] xb2; assign xb2 = xb[144 +: 72];
  logic [1:0] a2_sp; assign a2_sp = xa2[71:70];
  logic a2_s; assign a2_s = xa2[69];
  logic signed [15:0] a2_e; assign a2_e = $signed(xa2[68:53]);
  logic [51:0] a2_sig; assign a2_sig = xa2[52:1];
  logic a2_st; assign a2_st = xa2[0];
  logic a2_z; assign a2_z = (a2_sp == 2'd0) && (a2_sig == 0) && !a2_st;
  logic [1:0] b2_sp; assign b2_sp = xb2[71:70];
  logic b2_s; assign b2_s = xb2[69];
  logic signed [15:0] b2_e; assign b2_e = $signed(xb2[68:53]);
  logic [51:0] b2_sig; assign b2_sig = xb2[52:1];
  logic b2_st; assign b2_st = xb2[0];
  logic b2_z; assign b2_z = (b2_sp == 2'd0) && (b2_sig == 0) && !b2_st;
  logic [2:0] sa2; assign sa2 = a2_sig[2:0];
  logic [2:0] sb2; assign sb2 = b2_sig[2:0];
  logic signed [18:0] e2; assign e2 = $signed({{3{a2_e[15]}}, a2_e}) + $signed({{3{b2_e[15]}}, b2_e});
  logic s2; assign s2 = a2_s ^ b2_s;
  logic [71:0] xa3; assign xa3 = xa[216 +: 72];
  logic [71:0] xb3; assign xb3 = xb[216 +: 72];
  logic [1:0] a3_sp; assign a3_sp = xa3[71:70];
  logic a3_s; assign a3_s = xa3[69];
  logic signed [15:0] a3_e; assign a3_e = $signed(xa3[68:53]);
  logic [51:0] a3_sig; assign a3_sig = xa3[52:1];
  logic a3_st; assign a3_st = xa3[0];
  logic a3_z; assign a3_z = (a3_sp == 2'd0) && (a3_sig == 0) && !a3_st;
  logic [1:0] b3_sp; assign b3_sp = xb3[71:70];
  logic b3_s; assign b3_s = xb3[69];
  logic signed [15:0] b3_e; assign b3_e = $signed(xb3[68:53]);
  logic [51:0] b3_sig; assign b3_sig = xb3[52:1];
  logic b3_st; assign b3_st = xb3[0];
  logic b3_z; assign b3_z = (b3_sp == 2'd0) && (b3_sig == 0) && !b3_st;
  logic [2:0] sa3; assign sa3 = a3_sig[2:0];
  logic [2:0] sb3; assign sb3 = b3_sig[2:0];
  logic signed [18:0] e3; assign e3 = $signed({{3{a3_e[15]}}, a3_e}) + $signed({{3{b3_e[15]}}, b3_e});
  logic s3; assign s3 = a3_s ^ b3_s;
  logic [1:0] c_sp; assign c_sp = xc[71:70];
  logic c_s; assign c_s = xc[69];
  logic signed [15:0] c_e; assign c_e = $signed(xc[68:53]);
  logic [51:0] c_sig; assign c_sig = xc[52:1];
  logic c_st; assign c_st = xc[0];
  logic c_z; assign c_z = (c_sp == 2'd0) && (c_sig == 0) && !c_st;
  logic [23:0] sc; assign sc = c_sig[23:0];
  logic signed [18:0] ec; assign ec = $signed({{3{c_e[15]}}, c_e});
  logic [5:0] p0;
  // product 0: the significand multiplier (segmented_grid)
  fam_mul_segmented_grid_w3_u_p0fd7e5f0 u1 (.a(sa0), .b(sb0), .p(p0));
  logic [5:0] p1;
  // product 1: the significand multiplier (segmented_grid)
  fam_mul_segmented_grid_w3_u_p0fd7e5f0 u2 (.a(sa1), .b(sb1), .p(p1));
  logic [5:0] p2;
  // product 2: the significand multiplier (segmented_grid)
  fam_mul_segmented_grid_w3_u_p0fd7e5f0 u3 (.a(sa2), .b(sb2), .p(p2));
  logic [5:0] p3;
  // product 3: the significand multiplier (segmented_grid)
  fam_mul_segmented_grid_w3_u_p0fd7e5f0 u4 (.a(sa3), .b(sb3), .p(p3));
  logic signed [18:0] active_e0; assign active_e0 = (p0 == 0) ? -19'sd131072 : e0;
  logic signed [18:0] active_e1; assign active_e1 = (p1 == 0) ? -19'sd131072 : e1;
  logic signed [18:0] active_e2; assign active_e2 = (p2 == 0) ? -19'sd131072 : e2;
  logic signed [18:0] active_e3; assign active_e3 = (p3 == 0) ? -19'sd131072 : e3;
  logic signed [18:0] active_e4; assign active_e4 = (sc == 0) ? -19'sd131072 : ec;
  logic signed [18:0] d0_1; assign d0_1 = active_e0 - active_e1;
  logic signed [18:0] d0_2; assign d0_2 = active_e0 - active_e2;
  logic signed [18:0] d0_3; assign d0_3 = active_e0 - active_e3;
  logic signed [18:0] d0_4; assign d0_4 = active_e0 - active_e4;
  logic signed [18:0] d1_2; assign d1_2 = active_e1 - active_e2;
  logic signed [18:0] d1_3; assign d1_3 = active_e1 - active_e3;
  logic signed [18:0] d1_4; assign d1_4 = active_e1 - active_e4;
  logic signed [18:0] d2_3; assign d2_3 = active_e2 - active_e3;
  logic signed [18:0] d2_4; assign d2_4 = active_e2 - active_e4;
  logic signed [18:0] d3_4; assign d3_4 = active_e3 - active_e4;
  logic ismax0; assign ismax0 = (d0_1 >= 0) && (d0_2 >= 0) && (d0_3 >= 0) && (d0_4 >= 0);
  logic ismax1; assign ismax1 = ((-d0_1) > 0) && (d1_2 >= 0) && (d1_3 >= 0) && (d1_4 >= 0);
  logic ismax2; assign ismax2 = ((-d0_2) > 0) && ((-d1_2) > 0) && (d2_3 >= 0) && (d2_4 >= 0);
  logic ismax3; assign ismax3 = ((-d0_3) > 0) && ((-d1_3) > 0) && ((-d2_3) > 0) && (d3_4 >= 0);
  logic ismax4; assign ismax4 = ((-d0_4) > 0) && ((-d1_4) > 0) && ((-d2_4) > 0) && ((-d3_4) > 0);
  logic signed [18:0] emax; assign emax = ismax0 ? active_e0 : ismax1 ? active_e1 : ismax2 ? active_e2 : ismax3 ? active_e3 : ismax4 ? active_e4 : active_e0;
  logic signed [18:0] dist0; assign dist0 = ismax0 ? 19'sd0 : ismax1 ? (-d0_1) : ismax2 ? (-d0_2) : ismax3 ? (-d0_3) : ismax4 ? (-d0_4) : 19'sd0;
  logic signed [18:0] dist1; assign dist1 = ismax0 ? d0_1 : ismax1 ? 19'sd0 : ismax2 ? (-d1_2) : ismax3 ? (-d1_3) : ismax4 ? (-d1_4) : 19'sd0;
  logic signed [18:0] dist2; assign dist2 = ismax0 ? d0_2 : ismax1 ? d1_2 : ismax2 ? 19'sd0 : ismax3 ? (-d2_3) : ismax4 ? (-d2_4) : 19'sd0;
  logic signed [18:0] dist3; assign dist3 = ismax0 ? d0_3 : ismax1 ? d1_3 : ismax2 ? d2_3 : ismax3 ? 19'sd0 : ismax4 ? (-d3_4) : 19'sd0;
  logic signed [18:0] dist4; assign dist4 = ismax0 ? d0_4 : ismax1 ? d1_4 : ismax2 ? d2_4 : ismax3 ? d3_4 : ismax4 ? 19'sd0 : 19'sd0;
  logic [75:0] w0_0; assign w0_0 = {{(76-6){1'b0}}, p0} << 48;
  logic w0_far; assign w0_far = dist0 >= 76;
  logic [6:0] w0_am; assign w0_am = w0_far ? 7'd0 : dist0[6:0];
  logic [75:0] w0_sh;
  // term 0: right shift to the window at the largest exponent
  fam_shift_barrel_mux_tree #(.W(76), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u5 (.a(w0_0), .amt(w0_am), .op(3'd1), .y(w0_sh), .sticky());
  logic [75:0] w0_u; assign w0_u = w0_far ? 76'd0 : w0_sh;
  logic [75:0] w0_mk; assign w0_mk = w0_far ? {76{1'b1}} : ~({76{1'b1}} << w0_am);
  logic w0_st; assign w0_st = |(w0_0 & w0_mk);
  logic [75:0] w1_0; assign w1_0 = {{(76-6){1'b0}}, p1} << 48;
  logic w1_far; assign w1_far = dist1 >= 76;
  logic [6:0] w1_am; assign w1_am = w1_far ? 7'd0 : dist1[6:0];
  logic [75:0] w1_sh;
  // term 1: right shift to the window at the largest exponent
  fam_shift_barrel_mux_tree #(.W(76), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u6 (.a(w1_0), .amt(w1_am), .op(3'd1), .y(w1_sh), .sticky());
  logic [75:0] w1_u; assign w1_u = w1_far ? 76'd0 : w1_sh;
  logic [75:0] w1_mk; assign w1_mk = w1_far ? {76{1'b1}} : ~({76{1'b1}} << w1_am);
  logic w1_st; assign w1_st = |(w1_0 & w1_mk);
  logic [75:0] w2_0; assign w2_0 = {{(76-6){1'b0}}, p2} << 48;
  logic w2_far; assign w2_far = dist2 >= 76;
  logic [6:0] w2_am; assign w2_am = w2_far ? 7'd0 : dist2[6:0];
  logic [75:0] w2_sh;
  // term 2: right shift to the window at the largest exponent
  fam_shift_barrel_mux_tree #(.W(76), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u7 (.a(w2_0), .amt(w2_am), .op(3'd1), .y(w2_sh), .sticky());
  logic [75:0] w2_u; assign w2_u = w2_far ? 76'd0 : w2_sh;
  logic [75:0] w2_mk; assign w2_mk = w2_far ? {76{1'b1}} : ~({76{1'b1}} << w2_am);
  logic w2_st; assign w2_st = |(w2_0 & w2_mk);
  logic [75:0] w3_0; assign w3_0 = {{(76-6){1'b0}}, p3} << 48;
  logic w3_far; assign w3_far = dist3 >= 76;
  logic [6:0] w3_am; assign w3_am = w3_far ? 7'd0 : dist3[6:0];
  logic [75:0] w3_sh;
  // term 3: right shift to the window at the largest exponent
  fam_shift_barrel_mux_tree #(.W(76), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u8 (.a(w3_0), .amt(w3_am), .op(3'd1), .y(w3_sh), .sticky());
  logic [75:0] w3_u; assign w3_u = w3_far ? 76'd0 : w3_sh;
  logic [75:0] w3_mk; assign w3_mk = w3_far ? {76{1'b1}} : ~({76{1'b1}} << w3_am);
  logic w3_st; assign w3_st = |(w3_0 & w3_mk);
  logic [75:0] w4_0; assign w4_0 = {{(76-24){1'b0}}, sc} << 48;
  logic w4_far; assign w4_far = dist4 >= 76;
  logic [6:0] w4_am; assign w4_am = w4_far ? 7'd0 : dist4[6:0];
  logic [75:0] w4_sh;
  // term 4: right shift to the window at the largest exponent
  fam_shift_barrel_mux_tree #(.W(76), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u9 (.a(w4_0), .amt(w4_am), .op(3'd1), .y(w4_sh), .sticky());
  logic [75:0] w4_u; assign w4_u = w4_far ? 76'd0 : w4_sh;
  logic [75:0] w4_mk; assign w4_mk = w4_far ? {76{1'b1}} : ~({76{1'b1}} << w4_am);
  logic w4_st; assign w4_st = |(w4_0 & w4_mk);
  logic signed [18:0] wlo; assign wlo = emax - 19'sd48;
  logic [75:0] vp0; assign vp0 = s0 ? 76'd0 : w0_u;
  logic [75:0] vp1; assign vp1 = s1 ? 76'd0 : w1_u;
  logic [75:0] vp2; assign vp2 = s2 ? 76'd0 : w2_u;
  logic [75:0] vp3; assign vp3 = s3 ? 76'd0 : w3_u;
  logic [75:0] vp4; assign vp4 = c_s ? 76'd0 : w4_u;
  logic [75:0] vn0; assign vn0 = s0 ? w0_u : 76'd0;
  logic [75:0] vn1; assign vn1 = s1 ? w1_u : 76'd0;
  logic [75:0] vn2; assign vn2 = s2 ? w2_u : 76'd0;
  logic [75:0] vn3; assign vn3 = s3 ? w3_u : 76'd0;
  logic [75:0] vn4; assign vn4 = c_s ? w4_u : 76'd0;
  logic [75:0] sump_c0;
  logic sump_c0_co;
  // the positive terms' reduction: chain adder 0 (parallel_prefix)
  fam_prefix_sklansky_w76 u10 (.a(vp0), .b(vp1), .cin(1'b0), .s(sump_c0), .cout(sump_c0_co));
  logic [75:0] sump_c1;
  logic sump_c1_co;
  // the positive terms' reduction: chain adder 1 (parallel_prefix)
  fam_prefix_sklansky_w76 u11 (.a(sump_c0), .b(vp2), .cin(1'b0), .s(sump_c1), .cout(sump_c1_co));
  logic [75:0] sump_c2;
  logic sump_c2_co;
  // the positive terms' reduction: chain adder 2 (parallel_prefix)
  fam_prefix_sklansky_w76 u12 (.a(sump_c1), .b(vp3), .cin(1'b0), .s(sump_c2), .cout(sump_c2_co));
  logic [75:0] sump_c3;
  logic sump_c3_co;
  // the positive terms' reduction: chain adder 3 (parallel_prefix)
  fam_prefix_sklansky_w76 u13 (.a(sump_c2), .b(vp4), .cin(1'b0), .s(sump_c3), .cout(sump_c3_co));
  logic [75:0] sumn_c0;
  logic sumn_c0_co;
  // the negative terms' reduction: chain adder 0 (parallel_prefix)
  fam_prefix_sklansky_w76 u14 (.a(vn0), .b(vn1), .cin(1'b0), .s(sumn_c0), .cout(sumn_c0_co));
  logic [75:0] sumn_c1;
  logic sumn_c1_co;
  // the negative terms' reduction: chain adder 1 (parallel_prefix)
  fam_prefix_sklansky_w76 u15 (.a(sumn_c0), .b(vn2), .cin(1'b0), .s(sumn_c1), .cout(sumn_c1_co));
  logic [75:0] sumn_c2;
  logic sumn_c2_co;
  // the negative terms' reduction: chain adder 2 (parallel_prefix)
  fam_prefix_sklansky_w76 u16 (.a(sumn_c1), .b(vn3), .cin(1'b0), .s(sumn_c2), .cout(sumn_c2_co));
  logic [75:0] sumn_c3;
  logic sumn_c3_co;
  // the negative terms' reduction: chain adder 3 (parallel_prefix)
  fam_prefix_sklansky_w76 u17 (.a(sumn_c2), .b(vn4), .cin(1'b0), .s(sumn_c3), .cout(sumn_c3_co));
  logic [76:0] dual_p; assign dual_p = {1'b0, sump_c3};
  logic [76:0] dual_n; assign dual_n = {1'b0, sumn_c3};
  logic [76:0] dual_np; assign dual_np = ~dual_p;
  logic [76:0] dual_nn; assign dual_nn = ~dual_n;
  logic signed [76:0] pmn;
  logic signed [76:0] nmp;
  logic pmn_co;
  // the positive-minus-negative CPA
  fam_prefix_sklansky_w77 u18 (.a(dual_p), .b(dual_nn), .cin(1'b1), .s(pmn), .cout(pmn_co));
  logic nmp_co;
  // the negative-minus-positive CPA
  fam_prefix_sklansky_w77 u19 (.a(dual_n), .b(dual_np), .cin(1'b1), .s(nmp), .cout(nmp_co));
  logic negr; assign negr = pmn[76];
  logic [75:0] magr; assign magr = negr ? nmp[75:0] : pmn[75:0];
  logic [75:0] sumd; assign sumd = negr ? (~magr + 76'd1) : magr;
  logic [75:0] dual_lza_n; assign dual_lza_n = ~sumn_c3;
  logic nt_borrow; assign nt_borrow = (w0_st & s0) | (w1_st & s1) | (w2_st & s2) | (w3_st & s3) | (w4_st & c_s);
  logic [75:0] nt_addend; assign nt_addend = {{76{1'b1}}} ^ {{(76-1){1'b0}}, nt_borrow};
  logic [75:0] tot_adj;
  logic tot_adj_co;
  // the sticky borrow correction
  fam_prefix_sklansky_w76 u20 (.a(sumd), .b(nt_addend), .cin(1'b1), .s(tot_adj), .cout(tot_adj_co));
  logic o_neg; assign o_neg = tot_adj[75];
  logic [75:0] o_mag; assign o_mag = o_neg ? (~tot_adj + {{(76-1){1'b0}}, !(w0_st | w1_st | w2_st | w3_st | w4_st)}) : tot_adj;
  logic [6:0] o_lzc;
  // o: the leading-zero count of the magnitude
  fam_count_lzd_pair_cell_binary_count_vflat_w76 u21 (.a(o_mag), .n(o_lzc));
  logic [6:0] o_lzs; assign o_lzs = (o_mag == 0) ? 7'd0 : o_lzc[6:0];
  logic [7:0] o_lz; assign o_lz = {1'b0, o_lzs};
  logic [75:0] o_nm;
  // o: the normalize shifter
  fam_shift_barrel_mux_tree #(.W(76), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(0), .ORDER(0), .STICKY(0)) u22 (.a(o_mag), .amt(o_lzs), .op(3'd0), .y(o_nm), .sticky());
  logic [51:0] o_sig; assign o_sig = o_nm[75:24];
  logic o_st; assign o_st = (|o_nm[23:0]) | w0_st | w1_st | w2_st | w3_st | w4_st;
  logic signed [18:0] o_e0; assign o_e0 = wlo + 19'sd24 - $signed({{(19-8){1'b0}}, o_lz});
  logic signed [15:0] o_e; assign o_e = o_e0[15:0];
  logic o_zero; assign o_zero = (o_mag == 0) && !(w0_st | w1_st | w2_st | w3_st | w4_st);
  logic [71:0] y_o; assign y_o = o_zero ? {2'd0, 1'b0, 16'sd0, 52'd0, 1'b0} : {2'd0, o_neg, o_e, o_sig, o_st};
  assign y = y_o;
  assign fl = ((w0_st | w1_st | w2_st | w3_st | w4_st) ? 10'd16 : 10'd0);
endmodule

// fp rounder (dedicated_per_op, rounding increment_adder, leading zeros lzd_cell_tree, shifts barrel_mux_tree, exponent ripple_carry / prefix_and_incrementer): X -> fp32 pattern and flags
module fam_fp_round_dedicated_per_op_increment_adder_fp32_x52e16s24_pe0f43f9cf852 (
  input logic [71:0] x,
  input logic [2:0] rnd,
  input logic [7:0] word,
  input logic ftz,
  output logic [9:0] fl,
  output logic [31:0] bits
);
  logic [1:0] x_sp; assign x_sp = x[71:70];
  logic x_s; assign x_s = x[69];
  logic signed [15:0] x_e; assign x_e = $signed(x[68:53]);
  logic [51:0] x_sig; assign x_sig = x[52:1];
  logic x_st; assign x_st = x[0];
  logic x_z; assign x_z = (x_sp == 2'd0) && (x_sig == 0) && !x_st;
  logic s; assign s = x_s & 1'd1;
  logic lone; assign lone = (x_sig == 0) && x_st;
  logic [51:0] sig_in; assign sig_in = lone ? 52'd1 : x_sig;
  logic signed [15:0] e_lone_c; assign e_lone_c = -16'sd52;
  logic signed [15:0] e_lone;
  // the exponent of a lone sticky's unit
  fam_adder_ripple_carry #(.W(16), .CHUNK(1), .FORM(0)) u1 (.a(x_e), .b(e_lone_c), .cin(1'b0), .s(e_lone), .cout());
  logic signed [15:0] e_in; assign e_in = lone ? e_lone : x_e;
  logic [5:0] lz;
  // the normalizer's leading-zero count
  fam_count_lzd_pair_cell_binary_count_vprop_w52 u2 (.a(sig_in), .n(lz));
  logic [5:0] lzs; assign lzs = (sig_in == 0) ? 6'd0 : lz[5:0];
  logic [51:0] sig;
  // the normalizer's left shift
  fam_shift_barrel_mux_tree #(.W(52), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(1), .ORDER(0), .STICKY(0)) u3 (.a(sig_in), .amt(lzs), .op(3'd0), .y(sig), .sticky());
  logic signed [15:0] lzx; assign lzx = $signed({{(16-6){1'b0}}, lzs});
  logic [15:0] e_nb; assign e_nb = ~(lzx);
  logic signed [15:0] e;
  // the exponent lowered by the normalize count
  fam_adder_ripple_carry #(.W(16), .CHUNK(1), .FORM(0)) u4 (.a(e_in), .b(e_nb), .cin(1'b1), .s(e), .cout());
  logic normal; assign normal = e >= -16'sd177;
  logic signed [16:0] shc; assign shc = -17'sd149;
  logic signed [16:0] ex; assign ex = $signed({e[15], e});
  logic [16:0] shsub_nb; assign shsub_nb = ~(ex);
  logic signed [16:0] shsub;
  // the subnormal result's extra right shift
  fam_adder_ripple_carry #(.W(17), .CHUNK(1), .FORM(0)) u5 (.a(shc), .b(shsub_nb), .cin(1'b1), .s(shsub), .cout());
  logic signed [16:0] sht; assign sht = normal ? 17'sd28 : shsub;
  logic signed [16:0] sh; assign sh = (sht > 17'sd53) ? 17'sd53 : sht;
  logic [5:0] sha; assign sha = sh[5:0];
  logic [52:0] sigw; assign sigw = {1'b0, sig};
  logic [5:0] shk; assign shk = (sh > 17'sd52) ? 6'd52 : sha;
  logic [52:0] keep;
  // the right shift to the kept bits
  fam_shift_barrel_mux_tree #(.W(53), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(1), .ORDER(0), .STICKY(0)) u6 (.a(sigw), .amt(shk), .op(3'd1), .y(keep), .sticky());
  // the mask of the dropped positions
  logic [52:0] restmask;
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
  assign restmask[39] = (sha > 39);
  assign restmask[40] = (sha > 40);
  assign restmask[41] = (sha > 41);
  assign restmask[42] = (sha > 42);
  assign restmask[43] = (sha > 43);
  assign restmask[44] = (sha > 44);
  assign restmask[45] = (sha > 45);
  assign restmask[46] = (sha > 46);
  assign restmask[47] = (sha > 47);
  assign restmask[48] = (sha > 48);
  assign restmask[49] = (sha > 49);
  assign restmask[50] = (sha > 50);
  assign restmask[51] = (sha > 51);
  assign restmask[52] = (sha > 52);
  logic [52:0] rest; assign rest = sigw & restmask;
  // the half position (one below the kept lsb)
  logic [52:0] halfv;
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
  assign halfv[39] = (sha == 40);
  assign halfv[40] = (sha == 41);
  assign halfv[41] = (sha == 42);
  assign halfv[42] = (sha == 43);
  assign halfv[43] = (sha == 44);
  assign halfv[44] = (sha == 45);
  assign halfv[45] = (sha == 46);
  assign halfv[46] = (sha == 47);
  assign halfv[47] = (sha == 48);
  assign halfv[48] = (sha == 49);
  assign halfv[49] = (sha == 50);
  assign halfv[50] = (sha == 51);
  assign halfv[51] = (sha == 52);
  assign halfv[52] = (sha == 53);
  logic [52:0] keepn; assign keepn = sigw >> 28;
  logic [52:0] restn; assign restn = sigw & ({1'b0, {52{1'b1}}} >> 24);
  logic [52:0] halfn; assign halfn = {52'd0, 1'b1} << 27;
  logic inexact; assign inexact = (rest != 0) | x_st;
  logic [60:0] restw; assign restw = {rest, 8'd0};
  logic [5:0] fsh; assign fsh = sht[5:0];
  logic [60:0] fint0;
  // the dropped bits aligned to the stochastic word
  fam_shift_barrel_mux_tree #(.W(61), .RADIX_LOG2(1), .ONE_HOT(0), .DIR(1), .ORDER(0), .STICKY(0)) u7 (.a(restw), .amt(fsh), .op(3'd1), .y(fint0), .sticky());
  logic [60:0] fint; assign fint = (sht > 17'sd60) ? 61'd0 : fint0;
  logic [60:0] fintn; assign fintn = restn >> 20;
  logic gt_half; assign gt_half = rest > halfv;
  logic half_eq; assign half_eq = (rest == halfv) && (halfv != 0);
  logic up; assign up = (rnd == 3'd0) ? (gt_half || (half_eq && (x_st || keep[0]))) : (rnd == 3'd1) ? 1'b0 : (rnd == 3'd2) ? (inexact && s) : (rnd == 3'd3) ? (inexact && !s) : (rnd == 3'd4) ? (inexact && (0 ? (fint >= word) : (fint > word))) : inexact;
  logic gt_halfn; assign gt_halfn = restn > halfn;
  logic half_eqn; assign half_eqn = (restn == halfn) && (halfn != 0);
  logic upn; assign upn = (rnd == 3'd0) ? (gt_halfn || (half_eqn && (x_st || keepn[0]))) : (rnd == 3'd1) ? 1'b0 : (rnd == 3'd2) ? (((restn != 0) | x_st) && s) : (rnd == 3'd3) ? (((restn != 0) | x_st) && !s) : (rnd == 3'd4) ? (((restn != 0) | x_st) && (0 ? (fintn >= word) : (fintn > word))) : ((restn != 0) | x_st);
  logic rounded; assign rounded = x_sp == 2'd3;
  logic upr; assign upr = rounded ? 1'b0 : up;
  logic inexact_r; assign inexact_r = rounded | inexact;
  logic carry_n; assign carry_n = upn && (&keepn[23:0]);
  logic [52:0] mag;
  logic [52:0] mag0;
  // the rounding increment (prefix_and_incrementer)
  fam_incr_prefix_and #(.W(53), .STRUCTURE(0), .B(4), .TOPO(0)) u8 (.a(keep), .cin(upr), .s(mag0), .cout());
  assign mag = mag0;
  logic signed [15:0] bfield_c; assign bfield_c = 16'sd178;
  logic signed [15:0] bfield;
  // the biased exponent field
  fam_adder_ripple_carry #(.W(16), .CHUNK(1), .FORM(0)) u9 (.a(e), .b(bfield_c), .cin(1'b0), .s(bfield), .cout());
  logic [15:0] bfu; assign bfu = bfield;
  logic [15:0] efield;
  // the exponent field incremented on a rounding carry (prefix_and_incrementer)
  fam_incr_prefix_and #(.W(16), .STRUCTURE(1), .B(4), .TOPO(0)) u10 (.a(bfu), .cin(mag[24]), .s(efield), .cout());
  logic [53:0] code; assign code = normal ? {{(54-16-23){1'b0}}, efield, mag[22:0]} : {{(54-53){1'b0}}, mag};
  logic tiny; assign tiny = (e < -16'sd177) && !(e == -16'sd178 && carry_n) && !(e == -16'sd178 && carry_n);
  logic ovf; assign ovf = code > 54'd2139095039;
  logic to_inf; assign to_inf = 1 && (rnd == 3'd0 || (rnd == 3'd3 && !s) || (rnd == 3'd2 && s) || rnd == 3'd5 || (rnd == 3'd4 && (e > 16'sd76 || up)));
  logic ftz_hit; assign ftz_hit = ftz && code[30:23] == 0 && (code[22:0] != 0);
  logic is_zero; assign is_zero = (x_sig == 0) && (!x_st || rounded);
  logic tiny_r; assign tiny_r = rounded ? x_st : tiny;
  logic [9:0] fl_fin; assign fl_fin = ovf ? ((1 << 2) | (1 << 4)) : ((inexact_r ? (1 << 4) : 0) | ((tiny_r && inexact_r) ? (1 << 3) : 0) | (ftz_hit ? ((1 << 4) | (1 << 3)) : 0));
  logic [31:0] bits_fin; assign bits_fin = ovf ? (to_inf ? {s, 31'd2139095040} : {s, 31'd2139095039}) : (ftz_hit ? {s, 31'd0} : {s, code[30:0]});
  logic [9:0] fl_zero; assign fl_zero = rounded ? ((1 << 4) | (1 << 3)) : 10'd0;
  assign fl = (x_sp == 2'd1) ? (1 << 5) : (x_sp == 2'd2) ? 0 : is_zero ? fl_zero : fl_fin;
  assign bits = (x_sp == 2'd1) ? 32'd2143289344 : (x_sp == 2'd2) ? {s, 31'd2139095040} : is_zero ? {s, 31'd0} : bits_fin;
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



module fam_mul_direct_dadda_3_2_w2_u_p53f52f94 (input logic [1:0] a, input logic [1:0] b, output logic [3:0] p);
  // direct_pp_parallel: {'pp_bits': 4, 'full_adders': 0, 'half_adders': 0, 'cells': 0, 'tree_depth': 0}
  logic pp0, pp1, pp2, pp3;
  assign pp0 = (a[0] & b[0]);
  assign pp1 = (a[0] & b[1]);
  assign pp2 = (a[1] & b[0]);
  assign pp3 = (a[1] & b[1]);
  logic [3:0] row_s, row_c;
  assign row_s = {1'b0, pp3, pp1, pp0};
  assign row_c = {1'b0, 1'b0, pp2, 1'b0};
  fam_adder_ripple_carry #(.W(4), .CHUNK(1), .FORM(0)) u_cpa (.a(row_s), .b(row_c), .cin(1'b0), .s(p), .cout());
endmodule


// segmented_grid (square, depth 1): 2 x 2 segment products of 2 x 2 bits (direct_pp_parallel) merged by shift_add_tree (merge adder ripple_carry)
module fam_mul_segmented_grid_w3_u_p0fd7e5f0 (input logic [2:0] a, input logic [2:0] b, output logic [5:0] p);
  logic [3:0] ae; assign ae = {{(4-3){1'b0}}, a};
  logic [3:0] be; assign be = {{(4-3){1'b0}}, b};
  logic [1:0] sa00; assign sa00 = ae[1:0];
  logic [1:0] sb00; assign sb00 = be[1:0];
  logic [3:0] sp00;
  // segment product (0, 0) (direct_pp_parallel)
  fam_mul_direct_dadda_3_2_w2_u_p53f52f94 u1 (.a(sa00), .b(sb00), .p(sp00));
  logic [1:0] sa01; assign sa01 = ae[1:0];
  logic [1:0] sb01; assign sb01 = be[3:2];
  logic [3:0] sp01;
  // segment product (0, 1) (direct_pp_parallel)
  fam_mul_direct_dadda_3_2_w2_u_p53f52f94 u2 (.a(sa01), .b(sb01), .p(sp01));
  logic [1:0] sa10; assign sa10 = ae[3:2];
  logic [1:0] sb10; assign sb10 = be[1:0];
  logic [3:0] sp10;
  // segment product (1, 0) (direct_pp_parallel)
  fam_mul_direct_dadda_3_2_w2_u_p53f52f94 u3 (.a(sa10), .b(sb10), .p(sp10));
  logic [1:0] sa11; assign sa11 = ae[3:2];
  logic [1:0] sb11; assign sb11 = be[3:2];
  logic [3:0] sp11;
  // segment product (1, 1) (direct_pp_parallel)
  fam_mul_direct_dadda_3_2_w2_u_p53f52f94 u4 (.a(sa11), .b(sb11), .p(sp11));
  logic [9:0] t_sp00; assign t_sp00 = {{(10-4){1'b0}}, sp00} << 0;
  logic [9:0] t_sp01; assign t_sp01 = {{(10-4){1'b0}}, sp01} << 2;
  logic [9:0] t_sp10; assign t_sp10 = {{(10-4){1'b0}}, sp10} << 2;
  logic [9:0] t_sp11; assign t_sp11 = {{(10-4){1'b0}}, sp11} << 4;
  logic [10:0] tr0;
  // merge tree adder 0
  fam_adder_ripple_carry #(.W(10), .CHUNK(1), .FORM(0)) u5 (.a(t_sp00), .b(t_sp01), .cin(1'b0), .s(tr0[9:0]), .cout(tr0[10]));
  logic [10:0] tr1;
  // merge tree adder 1
  fam_adder_ripple_carry #(.W(10), .CHUNK(1), .FORM(0)) u6 (.a(t_sp10), .b(t_sp11), .cin(1'b0), .s(tr1[9:0]), .cout(tr1[10]));
  logic [10:0] tr2;
  // merge tree adder 2
  fam_adder_ripple_carry #(.W(10), .CHUNK(1), .FORM(0)) u7 (.a(tr0[9:0]), .b(tr1[9:0]), .cin(1'b0), .s(tr2[9:0]), .cout(tr2[10]));
  logic [9:0] full; assign full = tr2[9:0];
  assign p = full[5:0];
endmodule





// segmented_grid (square, depth 1): 2 x 2 segment products of 2 x 2 bits (direct_pp_parallel) merged by shift_add_tree (merge adder ripple_carry)





// segmented_grid (square, depth 1): 2 x 2 segment products of 2 x 2 bits (direct_pp_parallel) merged by shift_add_tree (merge adder ripple_carry)





// segmented_grid (square, depth 1): 2 x 2 segment products of 2 x 2 bits (direct_pp_parallel) merged by shift_add_tree (merge adder ripple_carry)





module fam_prefix_sklansky_w76 (input logic [75:0] a, input logic [75:0] b, input logic cin,
  output logic [75:0] s, output logic cout);
  // prefix graph: {'n': 76, 'levels': 7, 'size': 224, 'fanout': 32, 'tracks': 1, 'exact_split': True, 'valency': 2}
  logic [75:0] gi, pi_, ti;
  assign gi = a & b;
  assign pi_ = a ^ b;
  assign ti = a | b;
  logic [75:0] g0, p0;
  assign g0 = {gi[75:1], gi[0] | (pi_[0] & cin)};
  assign p0 = pi_;
  logic G_0_1, G_2_3, P_2_3, G_4_5, P_4_5, G_6_7, P_6_7, G_8_9, P_8_9, G_10_11, P_10_11, G_12_13, P_12_13, G_14_15, P_14_15, G_16_17, P_16_17, G_18_19, P_18_19, G_20_21, P_20_21, G_22_23, P_22_23, G_24_25, P_24_25, G_26_27, P_26_27, G_28_29, P_28_29, G_30_31, P_30_31, G_32_33, P_32_33, G_34_35, P_34_35, G_36_37, P_36_37, G_38_39, P_38_39, G_40_41, P_40_41, G_42_43, P_42_43, G_44_45, P_44_45, G_46_47, P_46_47, G_48_49, P_48_49, G_50_51, P_50_51, G_52_53, P_52_53, G_54_55, P_54_55, G_56_57, P_56_57, G_58_59, P_58_59, G_60_61, P_60_61, G_62_63, P_62_63, G_64_65, P_64_65, G_66_67, P_66_67, G_68_69, P_68_69, G_70_71, P_70_71, G_72_73, P_72_73, G_74_75, P_74_75, G_0_2, G_0_3, G_4_6, P_4_6, G_4_7, P_4_7, G_8_10, P_8_10, G_8_11, P_8_11, G_12_14, P_12_14, G_12_15, P_12_15, G_16_18, P_16_18, G_16_19, P_16_19, G_20_22, P_20_22, G_20_23, P_20_23, G_24_26, P_24_26, G_24_27, P_24_27, G_28_30, P_28_30, G_28_31, P_28_31, G_32_34, P_32_34, G_32_35, P_32_35, G_36_38, P_36_38, G_36_39, P_36_39, G_40_42, P_40_42, G_40_43, P_40_43, G_44_46, P_44_46, G_44_47, P_44_47, G_48_50, P_48_50, G_48_51, P_48_51, G_52_54, P_52_54, G_52_55, P_52_55, G_56_58, P_56_58, G_56_59, P_56_59, G_60_62, P_60_62, G_60_63, P_60_63, G_64_66, P_64_66, G_64_67, P_64_67, G_68_70, P_68_70, G_68_71, P_68_71, G_72_74, P_72_74, G_72_75, P_72_75, G_0_4, G_0_5, G_0_6, G_0_7, G_8_12, P_8_12, G_8_13, P_8_13, G_8_14, P_8_14, G_8_15, P_8_15, G_16_20, P_16_20, G_16_21, P_16_21, G_16_22, P_16_22, G_16_23, P_16_23, G_24_28, P_24_28, G_24_29, P_24_29, G_24_30, P_24_30, G_24_31, P_24_31, G_32_36, P_32_36, G_32_37, P_32_37, G_32_38, P_32_38, G_32_39, P_32_39, G_40_44, P_40_44, G_40_45, P_40_45, G_40_46, P_40_46, G_40_47, P_40_47, G_48_52, P_48_52, G_48_53, P_48_53, G_48_54, P_48_54, G_48_55, P_48_55, G_56_60, P_56_60, G_56_61, P_56_61, G_56_62, P_56_62, G_56_63, P_56_63, G_64_68, P_64_68, G_64_69, P_64_69, G_64_70, P_64_70, G_64_71, P_64_71, G_0_8, G_0_9, G_0_10, G_0_11, G_0_12, G_0_13, G_0_14, G_0_15, G_16_24, P_16_24, G_16_25, P_16_25, G_16_26, P_16_26, G_16_27, P_16_27, G_16_28, P_16_28, G_16_29, P_16_29, G_16_30, P_16_30, G_16_31, P_16_31, G_32_40, P_32_40, G_32_41, P_32_41, G_32_42, P_32_42, G_32_43, P_32_43, G_32_44, P_32_44, G_32_45, P_32_45, G_32_46, P_32_46, G_32_47, P_32_47, G_48_56, P_48_56, G_48_57, P_48_57, G_48_58, P_48_58, G_48_59, P_48_59, G_48_60, P_48_60, G_48_61, P_48_61, G_48_62, P_48_62, G_48_63, P_48_63, G_64_72, P_64_72, G_64_73, P_64_73, G_64_74, P_64_74, G_64_75, P_64_75, G_0_16, G_0_17, G_0_18, G_0_19, G_0_20, G_0_21, G_0_22, G_0_23, G_0_24, G_0_25, G_0_26, G_0_27, G_0_28, G_0_29, G_0_30, G_0_31, G_32_48, P_32_48, G_32_49, P_32_49, G_32_50, P_32_50, G_32_51, P_32_51, G_32_52, P_32_52, G_32_53, P_32_53, G_32_54, P_32_54, G_32_55, P_32_55, G_32_56, P_32_56, G_32_57, P_32_57, G_32_58, P_32_58, G_32_59, P_32_59, G_32_60, P_32_60, G_32_61, P_32_61, G_32_62, P_32_62, G_32_63, P_32_63, G_0_32, G_0_33, G_0_34, G_0_35, G_0_36, G_0_37, G_0_38, G_0_39, G_0_40, G_0_41, G_0_42, G_0_43, G_0_44, G_0_45, G_0_46, G_0_47, G_0_48, G_0_49, G_0_50, G_0_51, G_0_52, G_0_53, G_0_54, G_0_55, G_0_56, G_0_57, G_0_58, G_0_59, G_0_60, G_0_61, G_0_62, G_0_63, G_0_64, G_0_65, G_0_66, G_0_67, G_0_68, G_0_69, G_0_70, G_0_71, G_0_72, G_0_73, G_0_74, G_0_75;
  assign G_0_1 = g0[1] | (p0[1] & g0[0]);
  assign G_2_3 = g0[3] | (p0[3] & g0[2]);
  assign P_2_3 = p0[3] & p0[2];
  assign G_4_5 = g0[5] | (p0[5] & g0[4]);
  assign P_4_5 = p0[5] & p0[4];
  assign G_6_7 = g0[7] | (p0[7] & g0[6]);
  assign P_6_7 = p0[7] & p0[6];
  assign G_8_9 = g0[9] | (p0[9] & g0[8]);
  assign P_8_9 = p0[9] & p0[8];
  assign G_10_11 = g0[11] | (p0[11] & g0[10]);
  assign P_10_11 = p0[11] & p0[10];
  assign G_12_13 = g0[13] | (p0[13] & g0[12]);
  assign P_12_13 = p0[13] & p0[12];
  assign G_14_15 = g0[15] | (p0[15] & g0[14]);
  assign P_14_15 = p0[15] & p0[14];
  assign G_16_17 = g0[17] | (p0[17] & g0[16]);
  assign P_16_17 = p0[17] & p0[16];
  assign G_18_19 = g0[19] | (p0[19] & g0[18]);
  assign P_18_19 = p0[19] & p0[18];
  assign G_20_21 = g0[21] | (p0[21] & g0[20]);
  assign P_20_21 = p0[21] & p0[20];
  assign G_22_23 = g0[23] | (p0[23] & g0[22]);
  assign P_22_23 = p0[23] & p0[22];
  assign G_24_25 = g0[25] | (p0[25] & g0[24]);
  assign P_24_25 = p0[25] & p0[24];
  assign G_26_27 = g0[27] | (p0[27] & g0[26]);
  assign P_26_27 = p0[27] & p0[26];
  assign G_28_29 = g0[29] | (p0[29] & g0[28]);
  assign P_28_29 = p0[29] & p0[28];
  assign G_30_31 = g0[31] | (p0[31] & g0[30]);
  assign P_30_31 = p0[31] & p0[30];
  assign G_32_33 = g0[33] | (p0[33] & g0[32]);
  assign P_32_33 = p0[33] & p0[32];
  assign G_34_35 = g0[35] | (p0[35] & g0[34]);
  assign P_34_35 = p0[35] & p0[34];
  assign G_36_37 = g0[37] | (p0[37] & g0[36]);
  assign P_36_37 = p0[37] & p0[36];
  assign G_38_39 = g0[39] | (p0[39] & g0[38]);
  assign P_38_39 = p0[39] & p0[38];
  assign G_40_41 = g0[41] | (p0[41] & g0[40]);
  assign P_40_41 = p0[41] & p0[40];
  assign G_42_43 = g0[43] | (p0[43] & g0[42]);
  assign P_42_43 = p0[43] & p0[42];
  assign G_44_45 = g0[45] | (p0[45] & g0[44]);
  assign P_44_45 = p0[45] & p0[44];
  assign G_46_47 = g0[47] | (p0[47] & g0[46]);
  assign P_46_47 = p0[47] & p0[46];
  assign G_48_49 = g0[49] | (p0[49] & g0[48]);
  assign P_48_49 = p0[49] & p0[48];
  assign G_50_51 = g0[51] | (p0[51] & g0[50]);
  assign P_50_51 = p0[51] & p0[50];
  assign G_52_53 = g0[53] | (p0[53] & g0[52]);
  assign P_52_53 = p0[53] & p0[52];
  assign G_54_55 = g0[55] | (p0[55] & g0[54]);
  assign P_54_55 = p0[55] & p0[54];
  assign G_56_57 = g0[57] | (p0[57] & g0[56]);
  assign P_56_57 = p0[57] & p0[56];
  assign G_58_59 = g0[59] | (p0[59] & g0[58]);
  assign P_58_59 = p0[59] & p0[58];
  assign G_60_61 = g0[61] | (p0[61] & g0[60]);
  assign P_60_61 = p0[61] & p0[60];
  assign G_62_63 = g0[63] | (p0[63] & g0[62]);
  assign P_62_63 = p0[63] & p0[62];
  assign G_64_65 = g0[65] | (p0[65] & g0[64]);
  assign P_64_65 = p0[65] & p0[64];
  assign G_66_67 = g0[67] | (p0[67] & g0[66]);
  assign P_66_67 = p0[67] & p0[66];
  assign G_68_69 = g0[69] | (p0[69] & g0[68]);
  assign P_68_69 = p0[69] & p0[68];
  assign G_70_71 = g0[71] | (p0[71] & g0[70]);
  assign P_70_71 = p0[71] & p0[70];
  assign G_72_73 = g0[73] | (p0[73] & g0[72]);
  assign P_72_73 = p0[73] & p0[72];
  assign G_74_75 = g0[75] | (p0[75] & g0[74]);
  assign P_74_75 = p0[75] & p0[74];
  assign G_0_2 = g0[2] | (p0[2] & G_0_1);
  assign G_0_3 = G_2_3 | (P_2_3 & G_0_1);
  assign G_4_6 = g0[6] | (p0[6] & G_4_5);
  assign P_4_6 = p0[6] & P_4_5;
  assign G_4_7 = G_6_7 | (P_6_7 & G_4_5);
  assign P_4_7 = P_6_7 & P_4_5;
  assign G_8_10 = g0[10] | (p0[10] & G_8_9);
  assign P_8_10 = p0[10] & P_8_9;
  assign G_8_11 = G_10_11 | (P_10_11 & G_8_9);
  assign P_8_11 = P_10_11 & P_8_9;
  assign G_12_14 = g0[14] | (p0[14] & G_12_13);
  assign P_12_14 = p0[14] & P_12_13;
  assign G_12_15 = G_14_15 | (P_14_15 & G_12_13);
  assign P_12_15 = P_14_15 & P_12_13;
  assign G_16_18 = g0[18] | (p0[18] & G_16_17);
  assign P_16_18 = p0[18] & P_16_17;
  assign G_16_19 = G_18_19 | (P_18_19 & G_16_17);
  assign P_16_19 = P_18_19 & P_16_17;
  assign G_20_22 = g0[22] | (p0[22] & G_20_21);
  assign P_20_22 = p0[22] & P_20_21;
  assign G_20_23 = G_22_23 | (P_22_23 & G_20_21);
  assign P_20_23 = P_22_23 & P_20_21;
  assign G_24_26 = g0[26] | (p0[26] & G_24_25);
  assign P_24_26 = p0[26] & P_24_25;
  assign G_24_27 = G_26_27 | (P_26_27 & G_24_25);
  assign P_24_27 = P_26_27 & P_24_25;
  assign G_28_30 = g0[30] | (p0[30] & G_28_29);
  assign P_28_30 = p0[30] & P_28_29;
  assign G_28_31 = G_30_31 | (P_30_31 & G_28_29);
  assign P_28_31 = P_30_31 & P_28_29;
  assign G_32_34 = g0[34] | (p0[34] & G_32_33);
  assign P_32_34 = p0[34] & P_32_33;
  assign G_32_35 = G_34_35 | (P_34_35 & G_32_33);
  assign P_32_35 = P_34_35 & P_32_33;
  assign G_36_38 = g0[38] | (p0[38] & G_36_37);
  assign P_36_38 = p0[38] & P_36_37;
  assign G_36_39 = G_38_39 | (P_38_39 & G_36_37);
  assign P_36_39 = P_38_39 & P_36_37;
  assign G_40_42 = g0[42] | (p0[42] & G_40_41);
  assign P_40_42 = p0[42] & P_40_41;
  assign G_40_43 = G_42_43 | (P_42_43 & G_40_41);
  assign P_40_43 = P_42_43 & P_40_41;
  assign G_44_46 = g0[46] | (p0[46] & G_44_45);
  assign P_44_46 = p0[46] & P_44_45;
  assign G_44_47 = G_46_47 | (P_46_47 & G_44_45);
  assign P_44_47 = P_46_47 & P_44_45;
  assign G_48_50 = g0[50] | (p0[50] & G_48_49);
  assign P_48_50 = p0[50] & P_48_49;
  assign G_48_51 = G_50_51 | (P_50_51 & G_48_49);
  assign P_48_51 = P_50_51 & P_48_49;
  assign G_52_54 = g0[54] | (p0[54] & G_52_53);
  assign P_52_54 = p0[54] & P_52_53;
  assign G_52_55 = G_54_55 | (P_54_55 & G_52_53);
  assign P_52_55 = P_54_55 & P_52_53;
  assign G_56_58 = g0[58] | (p0[58] & G_56_57);
  assign P_56_58 = p0[58] & P_56_57;
  assign G_56_59 = G_58_59 | (P_58_59 & G_56_57);
  assign P_56_59 = P_58_59 & P_56_57;
  assign G_60_62 = g0[62] | (p0[62] & G_60_61);
  assign P_60_62 = p0[62] & P_60_61;
  assign G_60_63 = G_62_63 | (P_62_63 & G_60_61);
  assign P_60_63 = P_62_63 & P_60_61;
  assign G_64_66 = g0[66] | (p0[66] & G_64_65);
  assign P_64_66 = p0[66] & P_64_65;
  assign G_64_67 = G_66_67 | (P_66_67 & G_64_65);
  assign P_64_67 = P_66_67 & P_64_65;
  assign G_68_70 = g0[70] | (p0[70] & G_68_69);
  assign P_68_70 = p0[70] & P_68_69;
  assign G_68_71 = G_70_71 | (P_70_71 & G_68_69);
  assign P_68_71 = P_70_71 & P_68_69;
  assign G_72_74 = g0[74] | (p0[74] & G_72_73);
  assign P_72_74 = p0[74] & P_72_73;
  assign G_72_75 = G_74_75 | (P_74_75 & G_72_73);
  assign P_72_75 = P_74_75 & P_72_73;
  assign G_0_4 = g0[4] | (p0[4] & G_0_3);
  assign G_0_5 = G_4_5 | (P_4_5 & G_0_3);
  assign G_0_6 = G_4_6 | (P_4_6 & G_0_3);
  assign G_0_7 = G_4_7 | (P_4_7 & G_0_3);
  assign G_8_12 = g0[12] | (p0[12] & G_8_11);
  assign P_8_12 = p0[12] & P_8_11;
  assign G_8_13 = G_12_13 | (P_12_13 & G_8_11);
  assign P_8_13 = P_12_13 & P_8_11;
  assign G_8_14 = G_12_14 | (P_12_14 & G_8_11);
  assign P_8_14 = P_12_14 & P_8_11;
  assign G_8_15 = G_12_15 | (P_12_15 & G_8_11);
  assign P_8_15 = P_12_15 & P_8_11;
  assign G_16_20 = g0[20] | (p0[20] & G_16_19);
  assign P_16_20 = p0[20] & P_16_19;
  assign G_16_21 = G_20_21 | (P_20_21 & G_16_19);
  assign P_16_21 = P_20_21 & P_16_19;
  assign G_16_22 = G_20_22 | (P_20_22 & G_16_19);
  assign P_16_22 = P_20_22 & P_16_19;
  assign G_16_23 = G_20_23 | (P_20_23 & G_16_19);
  assign P_16_23 = P_20_23 & P_16_19;
  assign G_24_28 = g0[28] | (p0[28] & G_24_27);
  assign P_24_28 = p0[28] & P_24_27;
  assign G_24_29 = G_28_29 | (P_28_29 & G_24_27);
  assign P_24_29 = P_28_29 & P_24_27;
  assign G_24_30 = G_28_30 | (P_28_30 & G_24_27);
  assign P_24_30 = P_28_30 & P_24_27;
  assign G_24_31 = G_28_31 | (P_28_31 & G_24_27);
  assign P_24_31 = P_28_31 & P_24_27;
  assign G_32_36 = g0[36] | (p0[36] & G_32_35);
  assign P_32_36 = p0[36] & P_32_35;
  assign G_32_37 = G_36_37 | (P_36_37 & G_32_35);
  assign P_32_37 = P_36_37 & P_32_35;
  assign G_32_38 = G_36_38 | (P_36_38 & G_32_35);
  assign P_32_38 = P_36_38 & P_32_35;
  assign G_32_39 = G_36_39 | (P_36_39 & G_32_35);
  assign P_32_39 = P_36_39 & P_32_35;
  assign G_40_44 = g0[44] | (p0[44] & G_40_43);
  assign P_40_44 = p0[44] & P_40_43;
  assign G_40_45 = G_44_45 | (P_44_45 & G_40_43);
  assign P_40_45 = P_44_45 & P_40_43;
  assign G_40_46 = G_44_46 | (P_44_46 & G_40_43);
  assign P_40_46 = P_44_46 & P_40_43;
  assign G_40_47 = G_44_47 | (P_44_47 & G_40_43);
  assign P_40_47 = P_44_47 & P_40_43;
  assign G_48_52 = g0[52] | (p0[52] & G_48_51);
  assign P_48_52 = p0[52] & P_48_51;
  assign G_48_53 = G_52_53 | (P_52_53 & G_48_51);
  assign P_48_53 = P_52_53 & P_48_51;
  assign G_48_54 = G_52_54 | (P_52_54 & G_48_51);
  assign P_48_54 = P_52_54 & P_48_51;
  assign G_48_55 = G_52_55 | (P_52_55 & G_48_51);
  assign P_48_55 = P_52_55 & P_48_51;
  assign G_56_60 = g0[60] | (p0[60] & G_56_59);
  assign P_56_60 = p0[60] & P_56_59;
  assign G_56_61 = G_60_61 | (P_60_61 & G_56_59);
  assign P_56_61 = P_60_61 & P_56_59;
  assign G_56_62 = G_60_62 | (P_60_62 & G_56_59);
  assign P_56_62 = P_60_62 & P_56_59;
  assign G_56_63 = G_60_63 | (P_60_63 & G_56_59);
  assign P_56_63 = P_60_63 & P_56_59;
  assign G_64_68 = g0[68] | (p0[68] & G_64_67);
  assign P_64_68 = p0[68] & P_64_67;
  assign G_64_69 = G_68_69 | (P_68_69 & G_64_67);
  assign P_64_69 = P_68_69 & P_64_67;
  assign G_64_70 = G_68_70 | (P_68_70 & G_64_67);
  assign P_64_70 = P_68_70 & P_64_67;
  assign G_64_71 = G_68_71 | (P_68_71 & G_64_67);
  assign P_64_71 = P_68_71 & P_64_67;
  assign G_0_8 = g0[8] | (p0[8] & G_0_7);
  assign G_0_9 = G_8_9 | (P_8_9 & G_0_7);
  assign G_0_10 = G_8_10 | (P_8_10 & G_0_7);
  assign G_0_11 = G_8_11 | (P_8_11 & G_0_7);
  assign G_0_12 = G_8_12 | (P_8_12 & G_0_7);
  assign G_0_13 = G_8_13 | (P_8_13 & G_0_7);
  assign G_0_14 = G_8_14 | (P_8_14 & G_0_7);
  assign G_0_15 = G_8_15 | (P_8_15 & G_0_7);
  assign G_16_24 = g0[24] | (p0[24] & G_16_23);
  assign P_16_24 = p0[24] & P_16_23;
  assign G_16_25 = G_24_25 | (P_24_25 & G_16_23);
  assign P_16_25 = P_24_25 & P_16_23;
  assign G_16_26 = G_24_26 | (P_24_26 & G_16_23);
  assign P_16_26 = P_24_26 & P_16_23;
  assign G_16_27 = G_24_27 | (P_24_27 & G_16_23);
  assign P_16_27 = P_24_27 & P_16_23;
  assign G_16_28 = G_24_28 | (P_24_28 & G_16_23);
  assign P_16_28 = P_24_28 & P_16_23;
  assign G_16_29 = G_24_29 | (P_24_29 & G_16_23);
  assign P_16_29 = P_24_29 & P_16_23;
  assign G_16_30 = G_24_30 | (P_24_30 & G_16_23);
  assign P_16_30 = P_24_30 & P_16_23;
  assign G_16_31 = G_24_31 | (P_24_31 & G_16_23);
  assign P_16_31 = P_24_31 & P_16_23;
  assign G_32_40 = g0[40] | (p0[40] & G_32_39);
  assign P_32_40 = p0[40] & P_32_39;
  assign G_32_41 = G_40_41 | (P_40_41 & G_32_39);
  assign P_32_41 = P_40_41 & P_32_39;
  assign G_32_42 = G_40_42 | (P_40_42 & G_32_39);
  assign P_32_42 = P_40_42 & P_32_39;
  assign G_32_43 = G_40_43 | (P_40_43 & G_32_39);
  assign P_32_43 = P_40_43 & P_32_39;
  assign G_32_44 = G_40_44 | (P_40_44 & G_32_39);
  assign P_32_44 = P_40_44 & P_32_39;
  assign G_32_45 = G_40_45 | (P_40_45 & G_32_39);
  assign P_32_45 = P_40_45 & P_32_39;
  assign G_32_46 = G_40_46 | (P_40_46 & G_32_39);
  assign P_32_46 = P_40_46 & P_32_39;
  assign G_32_47 = G_40_47 | (P_40_47 & G_32_39);
  assign P_32_47 = P_40_47 & P_32_39;
  assign G_48_56 = g0[56] | (p0[56] & G_48_55);
  assign P_48_56 = p0[56] & P_48_55;
  assign G_48_57 = G_56_57 | (P_56_57 & G_48_55);
  assign P_48_57 = P_56_57 & P_48_55;
  assign G_48_58 = G_56_58 | (P_56_58 & G_48_55);
  assign P_48_58 = P_56_58 & P_48_55;
  assign G_48_59 = G_56_59 | (P_56_59 & G_48_55);
  assign P_48_59 = P_56_59 & P_48_55;
  assign G_48_60 = G_56_60 | (P_56_60 & G_48_55);
  assign P_48_60 = P_56_60 & P_48_55;
  assign G_48_61 = G_56_61 | (P_56_61 & G_48_55);
  assign P_48_61 = P_56_61 & P_48_55;
  assign G_48_62 = G_56_62 | (P_56_62 & G_48_55);
  assign P_48_62 = P_56_62 & P_48_55;
  assign G_48_63 = G_56_63 | (P_56_63 & G_48_55);
  assign P_48_63 = P_56_63 & P_48_55;
  assign G_64_72 = g0[72] | (p0[72] & G_64_71);
  assign P_64_72 = p0[72] & P_64_71;
  assign G_64_73 = G_72_73 | (P_72_73 & G_64_71);
  assign P_64_73 = P_72_73 & P_64_71;
  assign G_64_74 = G_72_74 | (P_72_74 & G_64_71);
  assign P_64_74 = P_72_74 & P_64_71;
  assign G_64_75 = G_72_75 | (P_72_75 & G_64_71);
  assign P_64_75 = P_72_75 & P_64_71;
  assign G_0_16 = g0[16] | (p0[16] & G_0_15);
  assign G_0_17 = G_16_17 | (P_16_17 & G_0_15);
  assign G_0_18 = G_16_18 | (P_16_18 & G_0_15);
  assign G_0_19 = G_16_19 | (P_16_19 & G_0_15);
  assign G_0_20 = G_16_20 | (P_16_20 & G_0_15);
  assign G_0_21 = G_16_21 | (P_16_21 & G_0_15);
  assign G_0_22 = G_16_22 | (P_16_22 & G_0_15);
  assign G_0_23 = G_16_23 | (P_16_23 & G_0_15);
  assign G_0_24 = G_16_24 | (P_16_24 & G_0_15);
  assign G_0_25 = G_16_25 | (P_16_25 & G_0_15);
  assign G_0_26 = G_16_26 | (P_16_26 & G_0_15);
  assign G_0_27 = G_16_27 | (P_16_27 & G_0_15);
  assign G_0_28 = G_16_28 | (P_16_28 & G_0_15);
  assign G_0_29 = G_16_29 | (P_16_29 & G_0_15);
  assign G_0_30 = G_16_30 | (P_16_30 & G_0_15);
  assign G_0_31 = G_16_31 | (P_16_31 & G_0_15);
  assign G_32_48 = g0[48] | (p0[48] & G_32_47);
  assign P_32_48 = p0[48] & P_32_47;
  assign G_32_49 = G_48_49 | (P_48_49 & G_32_47);
  assign P_32_49 = P_48_49 & P_32_47;
  assign G_32_50 = G_48_50 | (P_48_50 & G_32_47);
  assign P_32_50 = P_48_50 & P_32_47;
  assign G_32_51 = G_48_51 | (P_48_51 & G_32_47);
  assign P_32_51 = P_48_51 & P_32_47;
  assign G_32_52 = G_48_52 | (P_48_52 & G_32_47);
  assign P_32_52 = P_48_52 & P_32_47;
  assign G_32_53 = G_48_53 | (P_48_53 & G_32_47);
  assign P_32_53 = P_48_53 & P_32_47;
  assign G_32_54 = G_48_54 | (P_48_54 & G_32_47);
  assign P_32_54 = P_48_54 & P_32_47;
  assign G_32_55 = G_48_55 | (P_48_55 & G_32_47);
  assign P_32_55 = P_48_55 & P_32_47;
  assign G_32_56 = G_48_56 | (P_48_56 & G_32_47);
  assign P_32_56 = P_48_56 & P_32_47;
  assign G_32_57 = G_48_57 | (P_48_57 & G_32_47);
  assign P_32_57 = P_48_57 & P_32_47;
  assign G_32_58 = G_48_58 | (P_48_58 & G_32_47);
  assign P_32_58 = P_48_58 & P_32_47;
  assign G_32_59 = G_48_59 | (P_48_59 & G_32_47);
  assign P_32_59 = P_48_59 & P_32_47;
  assign G_32_60 = G_48_60 | (P_48_60 & G_32_47);
  assign P_32_60 = P_48_60 & P_32_47;
  assign G_32_61 = G_48_61 | (P_48_61 & G_32_47);
  assign P_32_61 = P_48_61 & P_32_47;
  assign G_32_62 = G_48_62 | (P_48_62 & G_32_47);
  assign P_32_62 = P_48_62 & P_32_47;
  assign G_32_63 = G_48_63 | (P_48_63 & G_32_47);
  assign P_32_63 = P_48_63 & P_32_47;
  assign G_0_32 = g0[32] | (p0[32] & G_0_31);
  assign G_0_33 = G_32_33 | (P_32_33 & G_0_31);
  assign G_0_34 = G_32_34 | (P_32_34 & G_0_31);
  assign G_0_35 = G_32_35 | (P_32_35 & G_0_31);
  assign G_0_36 = G_32_36 | (P_32_36 & G_0_31);
  assign G_0_37 = G_32_37 | (P_32_37 & G_0_31);
  assign G_0_38 = G_32_38 | (P_32_38 & G_0_31);
  assign G_0_39 = G_32_39 | (P_32_39 & G_0_31);
  assign G_0_40 = G_32_40 | (P_32_40 & G_0_31);
  assign G_0_41 = G_32_41 | (P_32_41 & G_0_31);
  assign G_0_42 = G_32_42 | (P_32_42 & G_0_31);
  assign G_0_43 = G_32_43 | (P_32_43 & G_0_31);
  assign G_0_44 = G_32_44 | (P_32_44 & G_0_31);
  assign G_0_45 = G_32_45 | (P_32_45 & G_0_31);
  assign G_0_46 = G_32_46 | (P_32_46 & G_0_31);
  assign G_0_47 = G_32_47 | (P_32_47 & G_0_31);
  assign G_0_48 = G_32_48 | (P_32_48 & G_0_31);
  assign G_0_49 = G_32_49 | (P_32_49 & G_0_31);
  assign G_0_50 = G_32_50 | (P_32_50 & G_0_31);
  assign G_0_51 = G_32_51 | (P_32_51 & G_0_31);
  assign G_0_52 = G_32_52 | (P_32_52 & G_0_31);
  assign G_0_53 = G_32_53 | (P_32_53 & G_0_31);
  assign G_0_54 = G_32_54 | (P_32_54 & G_0_31);
  assign G_0_55 = G_32_55 | (P_32_55 & G_0_31);
  assign G_0_56 = G_32_56 | (P_32_56 & G_0_31);
  assign G_0_57 = G_32_57 | (P_32_57 & G_0_31);
  assign G_0_58 = G_32_58 | (P_32_58 & G_0_31);
  assign G_0_59 = G_32_59 | (P_32_59 & G_0_31);
  assign G_0_60 = G_32_60 | (P_32_60 & G_0_31);
  assign G_0_61 = G_32_61 | (P_32_61 & G_0_31);
  assign G_0_62 = G_32_62 | (P_32_62 & G_0_31);
  assign G_0_63 = G_32_63 | (P_32_63 & G_0_31);
  assign G_0_64 = g0[64] | (p0[64] & G_0_63);
  assign G_0_65 = G_64_65 | (P_64_65 & G_0_63);
  assign G_0_66 = G_64_66 | (P_64_66 & G_0_63);
  assign G_0_67 = G_64_67 | (P_64_67 & G_0_63);
  assign G_0_68 = G_64_68 | (P_64_68 & G_0_63);
  assign G_0_69 = G_64_69 | (P_64_69 & G_0_63);
  assign G_0_70 = G_64_70 | (P_64_70 & G_0_63);
  assign G_0_71 = G_64_71 | (P_64_71 & G_0_63);
  assign G_0_72 = G_64_72 | (P_64_72 & G_0_63);
  assign G_0_73 = G_64_73 | (P_64_73 & G_0_63);
  assign G_0_74 = G_64_74 | (P_64_74 & G_0_63);
  assign G_0_75 = G_64_75 | (P_64_75 & G_0_63);
  logic [76:0] c;
  assign c[0] = cin;
  assign c[1] = g0[0];
  assign c[2] = G_0_1;
  assign c[3] = G_0_2;
  assign c[4] = G_0_3;
  assign c[5] = G_0_4;
  assign c[6] = G_0_5;
  assign c[7] = G_0_6;
  assign c[8] = G_0_7;
  assign c[9] = G_0_8;
  assign c[10] = G_0_9;
  assign c[11] = G_0_10;
  assign c[12] = G_0_11;
  assign c[13] = G_0_12;
  assign c[14] = G_0_13;
  assign c[15] = G_0_14;
  assign c[16] = G_0_15;
  assign c[17] = G_0_16;
  assign c[18] = G_0_17;
  assign c[19] = G_0_18;
  assign c[20] = G_0_19;
  assign c[21] = G_0_20;
  assign c[22] = G_0_21;
  assign c[23] = G_0_22;
  assign c[24] = G_0_23;
  assign c[25] = G_0_24;
  assign c[26] = G_0_25;
  assign c[27] = G_0_26;
  assign c[28] = G_0_27;
  assign c[29] = G_0_28;
  assign c[30] = G_0_29;
  assign c[31] = G_0_30;
  assign c[32] = G_0_31;
  assign c[33] = G_0_32;
  assign c[34] = G_0_33;
  assign c[35] = G_0_34;
  assign c[36] = G_0_35;
  assign c[37] = G_0_36;
  assign c[38] = G_0_37;
  assign c[39] = G_0_38;
  assign c[40] = G_0_39;
  assign c[41] = G_0_40;
  assign c[42] = G_0_41;
  assign c[43] = G_0_42;
  assign c[44] = G_0_43;
  assign c[45] = G_0_44;
  assign c[46] = G_0_45;
  assign c[47] = G_0_46;
  assign c[48] = G_0_47;
  assign c[49] = G_0_48;
  assign c[50] = G_0_49;
  assign c[51] = G_0_50;
  assign c[52] = G_0_51;
  assign c[53] = G_0_52;
  assign c[54] = G_0_53;
  assign c[55] = G_0_54;
  assign c[56] = G_0_55;
  assign c[57] = G_0_56;
  assign c[58] = G_0_57;
  assign c[59] = G_0_58;
  assign c[60] = G_0_59;
  assign c[61] = G_0_60;
  assign c[62] = G_0_61;
  assign c[63] = G_0_62;
  assign c[64] = G_0_63;
  assign c[65] = G_0_64;
  assign c[66] = G_0_65;
  assign c[67] = G_0_66;
  assign c[68] = G_0_67;
  assign c[69] = G_0_68;
  assign c[70] = G_0_69;
  assign c[71] = G_0_70;
  assign c[72] = G_0_71;
  assign c[73] = G_0_72;
  assign c[74] = G_0_73;
  assign c[75] = G_0_74;
  assign c[76] = G_0_75;
  assign s = pi_ ^ c[75:0];
  assign cout = c[76];
endmodule









module fam_prefix_sklansky_w77 (input logic [76:0] a, input logic [76:0] b, input logic cin,
  output logic [76:0] s, output logic cout);
  // prefix graph: {'n': 77, 'levels': 7, 'size': 227, 'fanout': 32, 'tracks': 1, 'exact_split': True, 'valency': 2}
  logic [76:0] gi, pi_, ti;
  assign gi = a & b;
  assign pi_ = a ^ b;
  assign ti = a | b;
  logic [76:0] g0, p0;
  assign g0 = {gi[76:1], gi[0] | (pi_[0] & cin)};
  assign p0 = pi_;
  logic G_0_1, G_2_3, P_2_3, G_4_5, P_4_5, G_6_7, P_6_7, G_8_9, P_8_9, G_10_11, P_10_11, G_12_13, P_12_13, G_14_15, P_14_15, G_16_17, P_16_17, G_18_19, P_18_19, G_20_21, P_20_21, G_22_23, P_22_23, G_24_25, P_24_25, G_26_27, P_26_27, G_28_29, P_28_29, G_30_31, P_30_31, G_32_33, P_32_33, G_34_35, P_34_35, G_36_37, P_36_37, G_38_39, P_38_39, G_40_41, P_40_41, G_42_43, P_42_43, G_44_45, P_44_45, G_46_47, P_46_47, G_48_49, P_48_49, G_50_51, P_50_51, G_52_53, P_52_53, G_54_55, P_54_55, G_56_57, P_56_57, G_58_59, P_58_59, G_60_61, P_60_61, G_62_63, P_62_63, G_64_65, P_64_65, G_66_67, P_66_67, G_68_69, P_68_69, G_70_71, P_70_71, G_72_73, P_72_73, G_74_75, P_74_75, G_0_2, G_0_3, G_4_6, P_4_6, G_4_7, P_4_7, G_8_10, P_8_10, G_8_11, P_8_11, G_12_14, P_12_14, G_12_15, P_12_15, G_16_18, P_16_18, G_16_19, P_16_19, G_20_22, P_20_22, G_20_23, P_20_23, G_24_26, P_24_26, G_24_27, P_24_27, G_28_30, P_28_30, G_28_31, P_28_31, G_32_34, P_32_34, G_32_35, P_32_35, G_36_38, P_36_38, G_36_39, P_36_39, G_40_42, P_40_42, G_40_43, P_40_43, G_44_46, P_44_46, G_44_47, P_44_47, G_48_50, P_48_50, G_48_51, P_48_51, G_52_54, P_52_54, G_52_55, P_52_55, G_56_58, P_56_58, G_56_59, P_56_59, G_60_62, P_60_62, G_60_63, P_60_63, G_64_66, P_64_66, G_64_67, P_64_67, G_68_70, P_68_70, G_68_71, P_68_71, G_72_74, P_72_74, G_72_75, P_72_75, G_0_4, G_0_5, G_0_6, G_0_7, G_8_12, P_8_12, G_8_13, P_8_13, G_8_14, P_8_14, G_8_15, P_8_15, G_16_20, P_16_20, G_16_21, P_16_21, G_16_22, P_16_22, G_16_23, P_16_23, G_24_28, P_24_28, G_24_29, P_24_29, G_24_30, P_24_30, G_24_31, P_24_31, G_32_36, P_32_36, G_32_37, P_32_37, G_32_38, P_32_38, G_32_39, P_32_39, G_40_44, P_40_44, G_40_45, P_40_45, G_40_46, P_40_46, G_40_47, P_40_47, G_48_52, P_48_52, G_48_53, P_48_53, G_48_54, P_48_54, G_48_55, P_48_55, G_56_60, P_56_60, G_56_61, P_56_61, G_56_62, P_56_62, G_56_63, P_56_63, G_64_68, P_64_68, G_64_69, P_64_69, G_64_70, P_64_70, G_64_71, P_64_71, G_72_76, P_72_76, G_0_8, G_0_9, G_0_10, G_0_11, G_0_12, G_0_13, G_0_14, G_0_15, G_16_24, P_16_24, G_16_25, P_16_25, G_16_26, P_16_26, G_16_27, P_16_27, G_16_28, P_16_28, G_16_29, P_16_29, G_16_30, P_16_30, G_16_31, P_16_31, G_32_40, P_32_40, G_32_41, P_32_41, G_32_42, P_32_42, G_32_43, P_32_43, G_32_44, P_32_44, G_32_45, P_32_45, G_32_46, P_32_46, G_32_47, P_32_47, G_48_56, P_48_56, G_48_57, P_48_57, G_48_58, P_48_58, G_48_59, P_48_59, G_48_60, P_48_60, G_48_61, P_48_61, G_48_62, P_48_62, G_48_63, P_48_63, G_64_72, P_64_72, G_64_73, P_64_73, G_64_74, P_64_74, G_64_75, P_64_75, G_64_76, P_64_76, G_0_16, G_0_17, G_0_18, G_0_19, G_0_20, G_0_21, G_0_22, G_0_23, G_0_24, G_0_25, G_0_26, G_0_27, G_0_28, G_0_29, G_0_30, G_0_31, G_32_48, P_32_48, G_32_49, P_32_49, G_32_50, P_32_50, G_32_51, P_32_51, G_32_52, P_32_52, G_32_53, P_32_53, G_32_54, P_32_54, G_32_55, P_32_55, G_32_56, P_32_56, G_32_57, P_32_57, G_32_58, P_32_58, G_32_59, P_32_59, G_32_60, P_32_60, G_32_61, P_32_61, G_32_62, P_32_62, G_32_63, P_32_63, G_0_32, G_0_33, G_0_34, G_0_35, G_0_36, G_0_37, G_0_38, G_0_39, G_0_40, G_0_41, G_0_42, G_0_43, G_0_44, G_0_45, G_0_46, G_0_47, G_0_48, G_0_49, G_0_50, G_0_51, G_0_52, G_0_53, G_0_54, G_0_55, G_0_56, G_0_57, G_0_58, G_0_59, G_0_60, G_0_61, G_0_62, G_0_63, G_0_64, G_0_65, G_0_66, G_0_67, G_0_68, G_0_69, G_0_70, G_0_71, G_0_72, G_0_73, G_0_74, G_0_75, G_0_76;
  assign G_0_1 = g0[1] | (p0[1] & g0[0]);
  assign G_2_3 = g0[3] | (p0[3] & g0[2]);
  assign P_2_3 = p0[3] & p0[2];
  assign G_4_5 = g0[5] | (p0[5] & g0[4]);
  assign P_4_5 = p0[5] & p0[4];
  assign G_6_7 = g0[7] | (p0[7] & g0[6]);
  assign P_6_7 = p0[7] & p0[6];
  assign G_8_9 = g0[9] | (p0[9] & g0[8]);
  assign P_8_9 = p0[9] & p0[8];
  assign G_10_11 = g0[11] | (p0[11] & g0[10]);
  assign P_10_11 = p0[11] & p0[10];
  assign G_12_13 = g0[13] | (p0[13] & g0[12]);
  assign P_12_13 = p0[13] & p0[12];
  assign G_14_15 = g0[15] | (p0[15] & g0[14]);
  assign P_14_15 = p0[15] & p0[14];
  assign G_16_17 = g0[17] | (p0[17] & g0[16]);
  assign P_16_17 = p0[17] & p0[16];
  assign G_18_19 = g0[19] | (p0[19] & g0[18]);
  assign P_18_19 = p0[19] & p0[18];
  assign G_20_21 = g0[21] | (p0[21] & g0[20]);
  assign P_20_21 = p0[21] & p0[20];
  assign G_22_23 = g0[23] | (p0[23] & g0[22]);
  assign P_22_23 = p0[23] & p0[22];
  assign G_24_25 = g0[25] | (p0[25] & g0[24]);
  assign P_24_25 = p0[25] & p0[24];
  assign G_26_27 = g0[27] | (p0[27] & g0[26]);
  assign P_26_27 = p0[27] & p0[26];
  assign G_28_29 = g0[29] | (p0[29] & g0[28]);
  assign P_28_29 = p0[29] & p0[28];
  assign G_30_31 = g0[31] | (p0[31] & g0[30]);
  assign P_30_31 = p0[31] & p0[30];
  assign G_32_33 = g0[33] | (p0[33] & g0[32]);
  assign P_32_33 = p0[33] & p0[32];
  assign G_34_35 = g0[35] | (p0[35] & g0[34]);
  assign P_34_35 = p0[35] & p0[34];
  assign G_36_37 = g0[37] | (p0[37] & g0[36]);
  assign P_36_37 = p0[37] & p0[36];
  assign G_38_39 = g0[39] | (p0[39] & g0[38]);
  assign P_38_39 = p0[39] & p0[38];
  assign G_40_41 = g0[41] | (p0[41] & g0[40]);
  assign P_40_41 = p0[41] & p0[40];
  assign G_42_43 = g0[43] | (p0[43] & g0[42]);
  assign P_42_43 = p0[43] & p0[42];
  assign G_44_45 = g0[45] | (p0[45] & g0[44]);
  assign P_44_45 = p0[45] & p0[44];
  assign G_46_47 = g0[47] | (p0[47] & g0[46]);
  assign P_46_47 = p0[47] & p0[46];
  assign G_48_49 = g0[49] | (p0[49] & g0[48]);
  assign P_48_49 = p0[49] & p0[48];
  assign G_50_51 = g0[51] | (p0[51] & g0[50]);
  assign P_50_51 = p0[51] & p0[50];
  assign G_52_53 = g0[53] | (p0[53] & g0[52]);
  assign P_52_53 = p0[53] & p0[52];
  assign G_54_55 = g0[55] | (p0[55] & g0[54]);
  assign P_54_55 = p0[55] & p0[54];
  assign G_56_57 = g0[57] | (p0[57] & g0[56]);
  assign P_56_57 = p0[57] & p0[56];
  assign G_58_59 = g0[59] | (p0[59] & g0[58]);
  assign P_58_59 = p0[59] & p0[58];
  assign G_60_61 = g0[61] | (p0[61] & g0[60]);
  assign P_60_61 = p0[61] & p0[60];
  assign G_62_63 = g0[63] | (p0[63] & g0[62]);
  assign P_62_63 = p0[63] & p0[62];
  assign G_64_65 = g0[65] | (p0[65] & g0[64]);
  assign P_64_65 = p0[65] & p0[64];
  assign G_66_67 = g0[67] | (p0[67] & g0[66]);
  assign P_66_67 = p0[67] & p0[66];
  assign G_68_69 = g0[69] | (p0[69] & g0[68]);
  assign P_68_69 = p0[69] & p0[68];
  assign G_70_71 = g0[71] | (p0[71] & g0[70]);
  assign P_70_71 = p0[71] & p0[70];
  assign G_72_73 = g0[73] | (p0[73] & g0[72]);
  assign P_72_73 = p0[73] & p0[72];
  assign G_74_75 = g0[75] | (p0[75] & g0[74]);
  assign P_74_75 = p0[75] & p0[74];
  assign G_0_2 = g0[2] | (p0[2] & G_0_1);
  assign G_0_3 = G_2_3 | (P_2_3 & G_0_1);
  assign G_4_6 = g0[6] | (p0[6] & G_4_5);
  assign P_4_6 = p0[6] & P_4_5;
  assign G_4_7 = G_6_7 | (P_6_7 & G_4_5);
  assign P_4_7 = P_6_7 & P_4_5;
  assign G_8_10 = g0[10] | (p0[10] & G_8_9);
  assign P_8_10 = p0[10] & P_8_9;
  assign G_8_11 = G_10_11 | (P_10_11 & G_8_9);
  assign P_8_11 = P_10_11 & P_8_9;
  assign G_12_14 = g0[14] | (p0[14] & G_12_13);
  assign P_12_14 = p0[14] & P_12_13;
  assign G_12_15 = G_14_15 | (P_14_15 & G_12_13);
  assign P_12_15 = P_14_15 & P_12_13;
  assign G_16_18 = g0[18] | (p0[18] & G_16_17);
  assign P_16_18 = p0[18] & P_16_17;
  assign G_16_19 = G_18_19 | (P_18_19 & G_16_17);
  assign P_16_19 = P_18_19 & P_16_17;
  assign G_20_22 = g0[22] | (p0[22] & G_20_21);
  assign P_20_22 = p0[22] & P_20_21;
  assign G_20_23 = G_22_23 | (P_22_23 & G_20_21);
  assign P_20_23 = P_22_23 & P_20_21;
  assign G_24_26 = g0[26] | (p0[26] & G_24_25);
  assign P_24_26 = p0[26] & P_24_25;
  assign G_24_27 = G_26_27 | (P_26_27 & G_24_25);
  assign P_24_27 = P_26_27 & P_24_25;
  assign G_28_30 = g0[30] | (p0[30] & G_28_29);
  assign P_28_30 = p0[30] & P_28_29;
  assign G_28_31 = G_30_31 | (P_30_31 & G_28_29);
  assign P_28_31 = P_30_31 & P_28_29;
  assign G_32_34 = g0[34] | (p0[34] & G_32_33);
  assign P_32_34 = p0[34] & P_32_33;
  assign G_32_35 = G_34_35 | (P_34_35 & G_32_33);
  assign P_32_35 = P_34_35 & P_32_33;
  assign G_36_38 = g0[38] | (p0[38] & G_36_37);
  assign P_36_38 = p0[38] & P_36_37;
  assign G_36_39 = G_38_39 | (P_38_39 & G_36_37);
  assign P_36_39 = P_38_39 & P_36_37;
  assign G_40_42 = g0[42] | (p0[42] & G_40_41);
  assign P_40_42 = p0[42] & P_40_41;
  assign G_40_43 = G_42_43 | (P_42_43 & G_40_41);
  assign P_40_43 = P_42_43 & P_40_41;
  assign G_44_46 = g0[46] | (p0[46] & G_44_45);
  assign P_44_46 = p0[46] & P_44_45;
  assign G_44_47 = G_46_47 | (P_46_47 & G_44_45);
  assign P_44_47 = P_46_47 & P_44_45;
  assign G_48_50 = g0[50] | (p0[50] & G_48_49);
  assign P_48_50 = p0[50] & P_48_49;
  assign G_48_51 = G_50_51 | (P_50_51 & G_48_49);
  assign P_48_51 = P_50_51 & P_48_49;
  assign G_52_54 = g0[54] | (p0[54] & G_52_53);
  assign P_52_54 = p0[54] & P_52_53;
  assign G_52_55 = G_54_55 | (P_54_55 & G_52_53);
  assign P_52_55 = P_54_55 & P_52_53;
  assign G_56_58 = g0[58] | (p0[58] & G_56_57);
  assign P_56_58 = p0[58] & P_56_57;
  assign G_56_59 = G_58_59 | (P_58_59 & G_56_57);
  assign P_56_59 = P_58_59 & P_56_57;
  assign G_60_62 = g0[62] | (p0[62] & G_60_61);
  assign P_60_62 = p0[62] & P_60_61;
  assign G_60_63 = G_62_63 | (P_62_63 & G_60_61);
  assign P_60_63 = P_62_63 & P_60_61;
  assign G_64_66 = g0[66] | (p0[66] & G_64_65);
  assign P_64_66 = p0[66] & P_64_65;
  assign G_64_67 = G_66_67 | (P_66_67 & G_64_65);
  assign P_64_67 = P_66_67 & P_64_65;
  assign G_68_70 = g0[70] | (p0[70] & G_68_69);
  assign P_68_70 = p0[70] & P_68_69;
  assign G_68_71 = G_70_71 | (P_70_71 & G_68_69);
  assign P_68_71 = P_70_71 & P_68_69;
  assign G_72_74 = g0[74] | (p0[74] & G_72_73);
  assign P_72_74 = p0[74] & P_72_73;
  assign G_72_75 = G_74_75 | (P_74_75 & G_72_73);
  assign P_72_75 = P_74_75 & P_72_73;
  assign G_0_4 = g0[4] | (p0[4] & G_0_3);
  assign G_0_5 = G_4_5 | (P_4_5 & G_0_3);
  assign G_0_6 = G_4_6 | (P_4_6 & G_0_3);
  assign G_0_7 = G_4_7 | (P_4_7 & G_0_3);
  assign G_8_12 = g0[12] | (p0[12] & G_8_11);
  assign P_8_12 = p0[12] & P_8_11;
  assign G_8_13 = G_12_13 | (P_12_13 & G_8_11);
  assign P_8_13 = P_12_13 & P_8_11;
  assign G_8_14 = G_12_14 | (P_12_14 & G_8_11);
  assign P_8_14 = P_12_14 & P_8_11;
  assign G_8_15 = G_12_15 | (P_12_15 & G_8_11);
  assign P_8_15 = P_12_15 & P_8_11;
  assign G_16_20 = g0[20] | (p0[20] & G_16_19);
  assign P_16_20 = p0[20] & P_16_19;
  assign G_16_21 = G_20_21 | (P_20_21 & G_16_19);
  assign P_16_21 = P_20_21 & P_16_19;
  assign G_16_22 = G_20_22 | (P_20_22 & G_16_19);
  assign P_16_22 = P_20_22 & P_16_19;
  assign G_16_23 = G_20_23 | (P_20_23 & G_16_19);
  assign P_16_23 = P_20_23 & P_16_19;
  assign G_24_28 = g0[28] | (p0[28] & G_24_27);
  assign P_24_28 = p0[28] & P_24_27;
  assign G_24_29 = G_28_29 | (P_28_29 & G_24_27);
  assign P_24_29 = P_28_29 & P_24_27;
  assign G_24_30 = G_28_30 | (P_28_30 & G_24_27);
  assign P_24_30 = P_28_30 & P_24_27;
  assign G_24_31 = G_28_31 | (P_28_31 & G_24_27);
  assign P_24_31 = P_28_31 & P_24_27;
  assign G_32_36 = g0[36] | (p0[36] & G_32_35);
  assign P_32_36 = p0[36] & P_32_35;
  assign G_32_37 = G_36_37 | (P_36_37 & G_32_35);
  assign P_32_37 = P_36_37 & P_32_35;
  assign G_32_38 = G_36_38 | (P_36_38 & G_32_35);
  assign P_32_38 = P_36_38 & P_32_35;
  assign G_32_39 = G_36_39 | (P_36_39 & G_32_35);
  assign P_32_39 = P_36_39 & P_32_35;
  assign G_40_44 = g0[44] | (p0[44] & G_40_43);
  assign P_40_44 = p0[44] & P_40_43;
  assign G_40_45 = G_44_45 | (P_44_45 & G_40_43);
  assign P_40_45 = P_44_45 & P_40_43;
  assign G_40_46 = G_44_46 | (P_44_46 & G_40_43);
  assign P_40_46 = P_44_46 & P_40_43;
  assign G_40_47 = G_44_47 | (P_44_47 & G_40_43);
  assign P_40_47 = P_44_47 & P_40_43;
  assign G_48_52 = g0[52] | (p0[52] & G_48_51);
  assign P_48_52 = p0[52] & P_48_51;
  assign G_48_53 = G_52_53 | (P_52_53 & G_48_51);
  assign P_48_53 = P_52_53 & P_48_51;
  assign G_48_54 = G_52_54 | (P_52_54 & G_48_51);
  assign P_48_54 = P_52_54 & P_48_51;
  assign G_48_55 = G_52_55 | (P_52_55 & G_48_51);
  assign P_48_55 = P_52_55 & P_48_51;
  assign G_56_60 = g0[60] | (p0[60] & G_56_59);
  assign P_56_60 = p0[60] & P_56_59;
  assign G_56_61 = G_60_61 | (P_60_61 & G_56_59);
  assign P_56_61 = P_60_61 & P_56_59;
  assign G_56_62 = G_60_62 | (P_60_62 & G_56_59);
  assign P_56_62 = P_60_62 & P_56_59;
  assign G_56_63 = G_60_63 | (P_60_63 & G_56_59);
  assign P_56_63 = P_60_63 & P_56_59;
  assign G_64_68 = g0[68] | (p0[68] & G_64_67);
  assign P_64_68 = p0[68] & P_64_67;
  assign G_64_69 = G_68_69 | (P_68_69 & G_64_67);
  assign P_64_69 = P_68_69 & P_64_67;
  assign G_64_70 = G_68_70 | (P_68_70 & G_64_67);
  assign P_64_70 = P_68_70 & P_64_67;
  assign G_64_71 = G_68_71 | (P_68_71 & G_64_67);
  assign P_64_71 = P_68_71 & P_64_67;
  assign G_72_76 = g0[76] | (p0[76] & G_72_75);
  assign P_72_76 = p0[76] & P_72_75;
  assign G_0_8 = g0[8] | (p0[8] & G_0_7);
  assign G_0_9 = G_8_9 | (P_8_9 & G_0_7);
  assign G_0_10 = G_8_10 | (P_8_10 & G_0_7);
  assign G_0_11 = G_8_11 | (P_8_11 & G_0_7);
  assign G_0_12 = G_8_12 | (P_8_12 & G_0_7);
  assign G_0_13 = G_8_13 | (P_8_13 & G_0_7);
  assign G_0_14 = G_8_14 | (P_8_14 & G_0_7);
  assign G_0_15 = G_8_15 | (P_8_15 & G_0_7);
  assign G_16_24 = g0[24] | (p0[24] & G_16_23);
  assign P_16_24 = p0[24] & P_16_23;
  assign G_16_25 = G_24_25 | (P_24_25 & G_16_23);
  assign P_16_25 = P_24_25 & P_16_23;
  assign G_16_26 = G_24_26 | (P_24_26 & G_16_23);
  assign P_16_26 = P_24_26 & P_16_23;
  assign G_16_27 = G_24_27 | (P_24_27 & G_16_23);
  assign P_16_27 = P_24_27 & P_16_23;
  assign G_16_28 = G_24_28 | (P_24_28 & G_16_23);
  assign P_16_28 = P_24_28 & P_16_23;
  assign G_16_29 = G_24_29 | (P_24_29 & G_16_23);
  assign P_16_29 = P_24_29 & P_16_23;
  assign G_16_30 = G_24_30 | (P_24_30 & G_16_23);
  assign P_16_30 = P_24_30 & P_16_23;
  assign G_16_31 = G_24_31 | (P_24_31 & G_16_23);
  assign P_16_31 = P_24_31 & P_16_23;
  assign G_32_40 = g0[40] | (p0[40] & G_32_39);
  assign P_32_40 = p0[40] & P_32_39;
  assign G_32_41 = G_40_41 | (P_40_41 & G_32_39);
  assign P_32_41 = P_40_41 & P_32_39;
  assign G_32_42 = G_40_42 | (P_40_42 & G_32_39);
  assign P_32_42 = P_40_42 & P_32_39;
  assign G_32_43 = G_40_43 | (P_40_43 & G_32_39);
  assign P_32_43 = P_40_43 & P_32_39;
  assign G_32_44 = G_40_44 | (P_40_44 & G_32_39);
  assign P_32_44 = P_40_44 & P_32_39;
  assign G_32_45 = G_40_45 | (P_40_45 & G_32_39);
  assign P_32_45 = P_40_45 & P_32_39;
  assign G_32_46 = G_40_46 | (P_40_46 & G_32_39);
  assign P_32_46 = P_40_46 & P_32_39;
  assign G_32_47 = G_40_47 | (P_40_47 & G_32_39);
  assign P_32_47 = P_40_47 & P_32_39;
  assign G_48_56 = g0[56] | (p0[56] & G_48_55);
  assign P_48_56 = p0[56] & P_48_55;
  assign G_48_57 = G_56_57 | (P_56_57 & G_48_55);
  assign P_48_57 = P_56_57 & P_48_55;
  assign G_48_58 = G_56_58 | (P_56_58 & G_48_55);
  assign P_48_58 = P_56_58 & P_48_55;
  assign G_48_59 = G_56_59 | (P_56_59 & G_48_55);
  assign P_48_59 = P_56_59 & P_48_55;
  assign G_48_60 = G_56_60 | (P_56_60 & G_48_55);
  assign P_48_60 = P_56_60 & P_48_55;
  assign G_48_61 = G_56_61 | (P_56_61 & G_48_55);
  assign P_48_61 = P_56_61 & P_48_55;
  assign G_48_62 = G_56_62 | (P_56_62 & G_48_55);
  assign P_48_62 = P_56_62 & P_48_55;
  assign G_48_63 = G_56_63 | (P_56_63 & G_48_55);
  assign P_48_63 = P_56_63 & P_48_55;
  assign G_64_72 = g0[72] | (p0[72] & G_64_71);
  assign P_64_72 = p0[72] & P_64_71;
  assign G_64_73 = G_72_73 | (P_72_73 & G_64_71);
  assign P_64_73 = P_72_73 & P_64_71;
  assign G_64_74 = G_72_74 | (P_72_74 & G_64_71);
  assign P_64_74 = P_72_74 & P_64_71;
  assign G_64_75 = G_72_75 | (P_72_75 & G_64_71);
  assign P_64_75 = P_72_75 & P_64_71;
  assign G_64_76 = G_72_76 | (P_72_76 & G_64_71);
  assign P_64_76 = P_72_76 & P_64_71;
  assign G_0_16 = g0[16] | (p0[16] & G_0_15);
  assign G_0_17 = G_16_17 | (P_16_17 & G_0_15);
  assign G_0_18 = G_16_18 | (P_16_18 & G_0_15);
  assign G_0_19 = G_16_19 | (P_16_19 & G_0_15);
  assign G_0_20 = G_16_20 | (P_16_20 & G_0_15);
  assign G_0_21 = G_16_21 | (P_16_21 & G_0_15);
  assign G_0_22 = G_16_22 | (P_16_22 & G_0_15);
  assign G_0_23 = G_16_23 | (P_16_23 & G_0_15);
  assign G_0_24 = G_16_24 | (P_16_24 & G_0_15);
  assign G_0_25 = G_16_25 | (P_16_25 & G_0_15);
  assign G_0_26 = G_16_26 | (P_16_26 & G_0_15);
  assign G_0_27 = G_16_27 | (P_16_27 & G_0_15);
  assign G_0_28 = G_16_28 | (P_16_28 & G_0_15);
  assign G_0_29 = G_16_29 | (P_16_29 & G_0_15);
  assign G_0_30 = G_16_30 | (P_16_30 & G_0_15);
  assign G_0_31 = G_16_31 | (P_16_31 & G_0_15);
  assign G_32_48 = g0[48] | (p0[48] & G_32_47);
  assign P_32_48 = p0[48] & P_32_47;
  assign G_32_49 = G_48_49 | (P_48_49 & G_32_47);
  assign P_32_49 = P_48_49 & P_32_47;
  assign G_32_50 = G_48_50 | (P_48_50 & G_32_47);
  assign P_32_50 = P_48_50 & P_32_47;
  assign G_32_51 = G_48_51 | (P_48_51 & G_32_47);
  assign P_32_51 = P_48_51 & P_32_47;
  assign G_32_52 = G_48_52 | (P_48_52 & G_32_47);
  assign P_32_52 = P_48_52 & P_32_47;
  assign G_32_53 = G_48_53 | (P_48_53 & G_32_47);
  assign P_32_53 = P_48_53 & P_32_47;
  assign G_32_54 = G_48_54 | (P_48_54 & G_32_47);
  assign P_32_54 = P_48_54 & P_32_47;
  assign G_32_55 = G_48_55 | (P_48_55 & G_32_47);
  assign P_32_55 = P_48_55 & P_32_47;
  assign G_32_56 = G_48_56 | (P_48_56 & G_32_47);
  assign P_32_56 = P_48_56 & P_32_47;
  assign G_32_57 = G_48_57 | (P_48_57 & G_32_47);
  assign P_32_57 = P_48_57 & P_32_47;
  assign G_32_58 = G_48_58 | (P_48_58 & G_32_47);
  assign P_32_58 = P_48_58 & P_32_47;
  assign G_32_59 = G_48_59 | (P_48_59 & G_32_47);
  assign P_32_59 = P_48_59 & P_32_47;
  assign G_32_60 = G_48_60 | (P_48_60 & G_32_47);
  assign P_32_60 = P_48_60 & P_32_47;
  assign G_32_61 = G_48_61 | (P_48_61 & G_32_47);
  assign P_32_61 = P_48_61 & P_32_47;
  assign G_32_62 = G_48_62 | (P_48_62 & G_32_47);
  assign P_32_62 = P_48_62 & P_32_47;
  assign G_32_63 = G_48_63 | (P_48_63 & G_32_47);
  assign P_32_63 = P_48_63 & P_32_47;
  assign G_0_32 = g0[32] | (p0[32] & G_0_31);
  assign G_0_33 = G_32_33 | (P_32_33 & G_0_31);
  assign G_0_34 = G_32_34 | (P_32_34 & G_0_31);
  assign G_0_35 = G_32_35 | (P_32_35 & G_0_31);
  assign G_0_36 = G_32_36 | (P_32_36 & G_0_31);
  assign G_0_37 = G_32_37 | (P_32_37 & G_0_31);
  assign G_0_38 = G_32_38 | (P_32_38 & G_0_31);
  assign G_0_39 = G_32_39 | (P_32_39 & G_0_31);
  assign G_0_40 = G_32_40 | (P_32_40 & G_0_31);
  assign G_0_41 = G_32_41 | (P_32_41 & G_0_31);
  assign G_0_42 = G_32_42 | (P_32_42 & G_0_31);
  assign G_0_43 = G_32_43 | (P_32_43 & G_0_31);
  assign G_0_44 = G_32_44 | (P_32_44 & G_0_31);
  assign G_0_45 = G_32_45 | (P_32_45 & G_0_31);
  assign G_0_46 = G_32_46 | (P_32_46 & G_0_31);
  assign G_0_47 = G_32_47 | (P_32_47 & G_0_31);
  assign G_0_48 = G_32_48 | (P_32_48 & G_0_31);
  assign G_0_49 = G_32_49 | (P_32_49 & G_0_31);
  assign G_0_50 = G_32_50 | (P_32_50 & G_0_31);
  assign G_0_51 = G_32_51 | (P_32_51 & G_0_31);
  assign G_0_52 = G_32_52 | (P_32_52 & G_0_31);
  assign G_0_53 = G_32_53 | (P_32_53 & G_0_31);
  assign G_0_54 = G_32_54 | (P_32_54 & G_0_31);
  assign G_0_55 = G_32_55 | (P_32_55 & G_0_31);
  assign G_0_56 = G_32_56 | (P_32_56 & G_0_31);
  assign G_0_57 = G_32_57 | (P_32_57 & G_0_31);
  assign G_0_58 = G_32_58 | (P_32_58 & G_0_31);
  assign G_0_59 = G_32_59 | (P_32_59 & G_0_31);
  assign G_0_60 = G_32_60 | (P_32_60 & G_0_31);
  assign G_0_61 = G_32_61 | (P_32_61 & G_0_31);
  assign G_0_62 = G_32_62 | (P_32_62 & G_0_31);
  assign G_0_63 = G_32_63 | (P_32_63 & G_0_31);
  assign G_0_64 = g0[64] | (p0[64] & G_0_63);
  assign G_0_65 = G_64_65 | (P_64_65 & G_0_63);
  assign G_0_66 = G_64_66 | (P_64_66 & G_0_63);
  assign G_0_67 = G_64_67 | (P_64_67 & G_0_63);
  assign G_0_68 = G_64_68 | (P_64_68 & G_0_63);
  assign G_0_69 = G_64_69 | (P_64_69 & G_0_63);
  assign G_0_70 = G_64_70 | (P_64_70 & G_0_63);
  assign G_0_71 = G_64_71 | (P_64_71 & G_0_63);
  assign G_0_72 = G_64_72 | (P_64_72 & G_0_63);
  assign G_0_73 = G_64_73 | (P_64_73 & G_0_63);
  assign G_0_74 = G_64_74 | (P_64_74 & G_0_63);
  assign G_0_75 = G_64_75 | (P_64_75 & G_0_63);
  assign G_0_76 = G_64_76 | (P_64_76 & G_0_63);
  logic [77:0] c;
  assign c[0] = cin;
  assign c[1] = g0[0];
  assign c[2] = G_0_1;
  assign c[3] = G_0_2;
  assign c[4] = G_0_3;
  assign c[5] = G_0_4;
  assign c[6] = G_0_5;
  assign c[7] = G_0_6;
  assign c[8] = G_0_7;
  assign c[9] = G_0_8;
  assign c[10] = G_0_9;
  assign c[11] = G_0_10;
  assign c[12] = G_0_11;
  assign c[13] = G_0_12;
  assign c[14] = G_0_13;
  assign c[15] = G_0_14;
  assign c[16] = G_0_15;
  assign c[17] = G_0_16;
  assign c[18] = G_0_17;
  assign c[19] = G_0_18;
  assign c[20] = G_0_19;
  assign c[21] = G_0_20;
  assign c[22] = G_0_21;
  assign c[23] = G_0_22;
  assign c[24] = G_0_23;
  assign c[25] = G_0_24;
  assign c[26] = G_0_25;
  assign c[27] = G_0_26;
  assign c[28] = G_0_27;
  assign c[29] = G_0_28;
  assign c[30] = G_0_29;
  assign c[31] = G_0_30;
  assign c[32] = G_0_31;
  assign c[33] = G_0_32;
  assign c[34] = G_0_33;
  assign c[35] = G_0_34;
  assign c[36] = G_0_35;
  assign c[37] = G_0_36;
  assign c[38] = G_0_37;
  assign c[39] = G_0_38;
  assign c[40] = G_0_39;
  assign c[41] = G_0_40;
  assign c[42] = G_0_41;
  assign c[43] = G_0_42;
  assign c[44] = G_0_43;
  assign c[45] = G_0_44;
  assign c[46] = G_0_45;
  assign c[47] = G_0_46;
  assign c[48] = G_0_47;
  assign c[49] = G_0_48;
  assign c[50] = G_0_49;
  assign c[51] = G_0_50;
  assign c[52] = G_0_51;
  assign c[53] = G_0_52;
  assign c[54] = G_0_53;
  assign c[55] = G_0_54;
  assign c[56] = G_0_55;
  assign c[57] = G_0_56;
  assign c[58] = G_0_57;
  assign c[59] = G_0_58;
  assign c[60] = G_0_59;
  assign c[61] = G_0_60;
  assign c[62] = G_0_61;
  assign c[63] = G_0_62;
  assign c[64] = G_0_63;
  assign c[65] = G_0_64;
  assign c[66] = G_0_65;
  assign c[67] = G_0_66;
  assign c[68] = G_0_67;
  assign c[69] = G_0_68;
  assign c[70] = G_0_69;
  assign c[71] = G_0_70;
  assign c[72] = G_0_71;
  assign c[73] = G_0_72;
  assign c[74] = G_0_73;
  assign c[75] = G_0_74;
  assign c[76] = G_0_75;
  assign c[77] = G_0_76;
  assign s = pi_ ^ c[76:0];
  assign cout = c[77];
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

