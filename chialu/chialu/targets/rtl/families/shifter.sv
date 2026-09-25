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


// ---------------------------------------------------------------------- funnel
// a window of the word beside itself (a rotate), beside zeros (a left shift) or
// beside its fill (a right shift), and a W-bit slice selected at the position by
// ceil((AW + 1) / K) stages of 2^K:1 muxes (RADIX_LOG2 = K, the window mux radix).
// AMT_PRE: 1 subtract_from_n (a left operation reads the slice at W - amt of a
// 2W-bit window), 0 ones_complement_for_right (the window is 2W - 1 bits and a
// left operation reads the slice at ~amt = W - 1 - amt, which needs W a power of
// two; at another width the position is W - 1 - amt).
module fam_shift_funnel #(parameter int W = 16, parameter int RADIX_LOG2 = 1, parameter int AMT_PRE = 1, parameter int STICKY = 0)
  (input logic [W-1:0] a, input logic [$clog2(W)-1:0] amt, input logic [2:0] op, output logic [W-1:0] y, output logic sticky);
  localparam int AW = $clog2(W);
  localparam int WW = AMT_PRE ? 2 * W : 2 * W - 1;               // the window width
  localparam int PW = AW + 1;                                    // the position width
  localparam int K = (RADIX_LOG2 == 0 || RADIX_LOG2 > PW) ? PW : RADIX_LOG2;
  localparam int NS = (PW + K - 1) / K;
  wire rot = (op == 3'd3) || (op == 3'd4);
  wire left = (op == 3'd0) || (op == 3'd3);
  wire right = ~left;
  wire arith = (op == 3'd2);
  wire fill = arith & a[W-1];
  logic [W-1:0] mask;
  fam_shift_keep_mask #(.W(W), .STICKY(STICKY)) u_mask (.a(a), .amt(amt), .right(right), .rot(rot), .mask(mask), .sticky(sticky));
  logic [WW-1:0] win;
  logic [PW-1:0] pos;
  genvar s;
  generate
    if (AMT_PRE) begin : subtract
      // {hi, lo}: a left operation by k reads the slice at W - k (0 reads the low word for a
      // rotate and the high for a shift), a right one at k
      assign win = rot ? {a, a} : (left ? {a, {W{1'b0}}} : {{W{fill}}, a});
      assign pos = left ? ((amt == 0) ? {PW{1'b0}} : (W - amt)) : {1'b0, amt};
    end else begin : complement
      // a 2W - 1-bit window: a left operation by k reads the slice at W - 1 - k, which is the
      // one's complement of k when W is a power of two
      assign win = rot ? (left ? {a, a[W-1:1]} : {a[W-2:0], a}) : (left ? {a, {(W-1){1'b0}}} : {{(W-1){fill}}, a});
      if ((W & (W - 1)) == 0) begin : pow2
        assign pos = left ? {1'b0, ~amt} : {1'b0, amt};
      end else begin : other
        assign pos = left ? (W - 1 - amt) : {1'b0, amt};
      end
    end
    // the slice: the window shifted right by the position through the mux stages, the low W bits
    logic [WW-1:0] st [0:NS];
    assign st[0] = win;
    for (s = 0; s < NS; s = s + 1) begin : stage
      localparam int KB = (s * K + K <= PW) ? K : PW - s * K;
      fam_shift_stage #(.W(WW), .K(KB), .SH(s * K), .RIGHT(1), .ONE_HOT(0))
        u (.x(st[s]), .digit(pos[s*K +: KB]), .rot(1'b0), .fill(1'b0), .y(st[s+1]));
    end
    if (AMT_PRE) begin : y_sub
      assign y = (left & (amt == 0)) ? a : st[NS][W-1:0];
    end else begin : y_cpl
      assign y = st[NS][W-1:0];
    end
  endgenerate
endmodule


// ------------------------------------------------------------------ masked_merged
// a left rotator (the `rotator` slot's barrel: R_RADIX_LOG2, R_ONE_HOT, R_ORDER)
// plus a mask that turns the rotation into a shift by merging in the fill bits.
// MASKGEN: 0 thermometer_decode (one thermometer per direction, selected), 1
// two_thermometer_and (a low and a high bound thermometer ANDed), 2 lut (a table
// over the direction and the amount). MERGE: 0 and_or_merge, 1 per_bit_mux.
module fam_shift_masked_merged #(parameter int W = 16, parameter int MASKGEN = 0, parameter int MERGE = 0,
                                 parameter int R_RADIX_LOG2 = 1, parameter int R_ONE_HOT = 0, parameter int R_ORDER = 0, parameter int STICKY = 0)
  (input logic [W-1:0] a, input logic [$clog2(W)-1:0] amt, input logic [2:0] op, output logic [W-1:0] y, output logic sticky);
  localparam int AW = $clog2(W);
  localparam int K = (R_RADIX_LOG2 == 0 || R_RADIX_LOG2 > AW) ? AW : R_RADIX_LOG2;
  localparam int NS = (AW + K - 1) / K;
  wire right = (op == 3'd1) || (op == 3'd2) || (op == 3'd4);
  wire rot = (op == 3'd3) || (op == 3'd4);
  wire arith = (op == 3'd2);
  wire fill = arith & a[W-1];
  // rotate left by amt (a right operation by k is a left rotation by W - k)
  logic [AW-1:0] lamt;
  assign lamt = right ? (W - amt) : amt;
  logic [W-1:0] st [0:NS];
  assign st[0] = a;
  genvar s, i;
  logic [W-1:0] mask;                 // 1 where the rotated bit is kept
  generate
    for (s = 0; s < NS; s = s + 1) begin : stage
      localparam int G = R_ORDER ? (NS - 1 - s) : s;
      localparam int KB = (G * K + K <= AW) ? K : AW - G * K;
      fam_shift_stage #(.W(W), .K(KB), .SH(G * K), .RIGHT(0), .ONE_HOT(R_ONE_HOT))
        u (.x(st[s]), .digit(lamt[G*K +: KB]), .rot(1'b1), .fill(1'b0), .y(st[s+1]));
    end
    if (MASKGEN == 0) begin : thermo
      for (i = 0; i < W; i = i + 1) begin : mk
        assign mask[i] = right ? (i < W - amt) : (i >= amt);
      end
    end else if (MASKGEN == 1) begin : two_thermo
      // the field kept lies between a low and a high bound: [amt, W-1] for a left shift,
      // [0, W-1-amt] for a right one; each bound is a thermometer, the mask their AND. The
      // high bound is signed: a right amount at or past W (an amount code W leaves the whole
      // word when W is below a power of two) puts it below zero, and no bit is kept
      logic [AW:0] lo;
      logic signed [AW+1:0] hi;
      assign lo = right ? {(AW+1){1'b0}} : {1'b0, amt};
      assign hi = right ? ($signed(W - 1) - $signed({2'b00, amt})) : $signed(W - 1);
      logic [W-1:0] ge_lo, le_hi;
      for (i = 0; i < W; i = i + 1) begin : mk
        assign ge_lo[i] = (i >= lo);
        assign le_hi[i] = (hi >= 0) && (i <= hi);
      end
      assign mask = ge_lo & le_hi;
    end else begin : lut
      // the mask read from a table over the direction and the amount
      logic [AW:0] idx;
      assign idx = {right, amt};
      logic [W-1:0] tab [0:2*(1<<AW)-1];
      for (i = 0; i < 2 * (1 << AW); i = i + 1) begin : t
        localparam int RT = i >> AW;
        localparam int AM = i & ((1 << AW) - 1);
        genvar j;
        for (j = 0; j < W; j = j + 1) begin : bt
          assign tab[i][j] = RT ? (j < W - AM) : (j >= AM);
        end
      end
      assign mask = tab[idx];
    end
  endgenerate
  logic [W-1:0] mask_unused;
  fam_shift_keep_mask #(.W(W), .STICKY(STICKY)) u_sticky (.a(a), .amt(amt), .right(right), .rot(rot), .mask(mask_unused), .sticky(sticky));
  generate
    if (MERGE == 0) begin : and_or
      assign y = rot ? st[NS] : ((st[NS] & mask) | ({W{fill}} & ~mask));
    end else begin : per_bit
      for (i = 0; i < W; i = i + 1) begin : mx
        assign y[i] = (rot | mask[i]) ? st[NS][i] : fill;
      end
    end
  endgenerate
endmodule


// ---------------------------------------------------------------- butterfly_network
// a rotator on a switch network of lg(W) stages of W/2 two-input switches, stage
// l pairing the bits at distance D = 2^l inside every block of 2D, each switch
// under its own control. On the inverse butterfly (NETWORK = 0, small distance
// first) a rotate right by k over a 2D-block whose two halves are already
// rotated by k mod D swaps the pair (i, i+D) at the block-local index i when
// i >= D - (k mod D), and every pair when bit l of k is set (Hilewitz and Lee's
// rotation on the ibfly). The butterfly (NETWORK = 1) is the same stages in the
// reverse order, which composes the inverse permutation, so it takes the controls
// of a rotation by W - k. The shifts merge a mask as the masked family does; a
// left amount is W - amt. The network needs a power-of-two width.
module fam_shift_butterfly_network #(parameter int W = 16, parameter int NETWORK = 0, parameter int STICKY = 0)
  (input logic [W-1:0] a, input logic [$clog2(W)-1:0] amt, input logic [2:0] op, output logic [W-1:0] y, output logic sticky);
  localparam int AW = $clog2(W);
  wire right = (op == 3'd1) || (op == 3'd2) || (op == 3'd4);
  wire rot = (op == 3'd3) || (op == 3'd4);
  wire arith = (op == 3'd2);
  wire fill = arith & a[W-1];
  logic [AW-1:0] k0, k;                              // the right-rotation amount, and the controls' amount
  assign k0 = right ? amt : (W - amt);
  assign k = NETWORK ? (W - k0) : k0;
  logic [W-1:0] st [0:AW];
  assign st[0] = a;
  genvar s, i;
  generate
    for (s = 0; s < AW; s = s + 1) begin : stage
      localparam int L = NETWORK ? (AW - 1 - s) : s;   // the switch distance of this stage: 2^L
      localparam int D = 1 << L;
      logic [AW-1:0] kmod;                             // k mod D (the low L bits of k)
      if (L == 0) begin : k0_
        assign kmod = '0;
      end else begin : kl
        assign kmod = {{(AW - L){1'b0}}, k[L-1:0]};
      end
      for (i = 0; i < W; i = i + 1) begin : bit_
        localparam int J = i % (2 * D);              // the block-local index
        if (J < D) begin : sw
          // the switch of the pair (i, i+D): crossed when J >= D - (k mod D), inverted by bit L of k
          wire ctrl = ((J >= D - kmod) ^ k[L]);
          assign st[s+1][i] = ctrl ? st[s][i+D] : st[s][i];
          assign st[s+1][i+D] = ctrl ? st[s][i] : st[s][i+D];
        end
      end
    end
  endgenerate
  logic [W-1:0] mask;
  fam_shift_keep_mask #(.W(W), .STICKY(STICKY)) u_mask (.a(a), .amt(amt), .right(right), .rot(rot), .mask(mask), .sticky(sticky));
  assign y = rot ? st[AW] : ((st[AW] & mask) | ({W{fill}} & ~mask));
endmodule

