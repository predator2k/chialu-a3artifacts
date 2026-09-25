// The fp8e5m2 half of TransDot's DP mode behind the one-mode `dot_core` of
// targets/eval/vec_dot_acc_cmp_fp8.yaml: four fp8e5m2 products with an fp32
// addend into fp32. The reference design is `transdot_fp4_fp8_fp16_fp32_fma`
// with NumPipeRegs 0 (register-free under `COMBINATIONAL`, see tdot_comb.py),
// driven at TDOT_DP_FMADD with src_fmt FP8ALT, which is E5M2 in TransDot's
// fork (its FP8 is E4M3). FpFmtConfig enables FP32 and FP8ALT alone, so the
// fp16 DP hardware is not in this measurement.
//
// The decode and what it costs (the report's wrapper column):
//   * operands_i[0] and [1] carry the four fp8 lanes in the quarter slices the
//     FMA's own lanes read, which is the packing chiALU's `a` and `b` use
//     (element k at bits [8k +: 8]).
//   * operands_i[2] is the fp32 addend, which the FP32 slice reads whole.
//   * the handshake is tied: in_valid_i and out_ready_i stand at one and the
//     valid outputs are unused. clk and rst_n are unused under `COMBINATIONAL`
//     and stay on the interface as in transdot_dot_core_fp16.sv; the bench
//     leaves them unconnected.
//   * the status output is unused: the comparison target binds `flags: []`.
//
// The contract this unit computes is not the fused one: its four-term
// accumulation is windowed, and a NaN or infinity in a lane above the first
// is dropped (docs/evaluation-plan.md, section 8), so its row carries the
// `window` contract and the ulp column of Table B.
module dot_core (
  input  logic        clk,
  input  logic        rst_n,
  input  logic [31:0] a,
  input  logic [31:0] b,
  input  logic [31:0] c,
  output logic [31:0] d
);
  logic [2:0][31:0] operands;
  assign operands[0] = a;
  assign operands[1] = b;
  assign operands[2] = c;

  fpnew_pkg::status_t status;
  logic extension_bit, tag_o, mask_o, aux_o, out_valid, in_ready, busy;

  transdot_fp4_fp8_fp16_fp32_fma #(
    .FpFmtConfig ( 7'b1000001 ),      // [0:6] = FP32, FP64, FP16, FP8, FP16ALT, FP4, FP8ALT
    .NumPipeRegs ( 0 ),
    .PipeConfig  ( fpnew_pkg::BEFORE ),
    .TagType     ( logic ),
    .AuxType     ( logic )
  ) i_fma (
    .clk_i           ( clk ),
    .rst_ni          ( rst_n ),
    .operands_i      ( operands ),
    .is_boxed_i      ( '1 ),
    .rnd_mode_i      ( fpnew_pkg::RNE ),
    .op_i            ( fpnew_pkg::TDOT_DP_FMADD ),
    .op_mod_i        ( 1'b0 ),
    .src_fmt_i       ( fpnew_pkg::FP8ALT ),
    .src2_fmt_i      ( fpnew_pkg::FP32 ),
    .dst_fmt_i       ( fpnew_pkg::FP32 ),
    .int_fmt_i       ( fpnew_pkg::INT32 ),
    .tag_i           ( 1'b0 ),
    .mask_i          ( 1'b1 ),
    .aux_i           ( 1'b0 ),
    .dp_enable_i     ( 1'b1 ),
    .simd_enable_i   ( 1'b0 ),
    .fp4_enable_i    ( 1'b0 ),
    .in_valid_i      ( 1'b1 ),
    .in_ready_o      ( in_ready ),
    .flush_i         ( 1'b0 ),
    .result_o        ( d ),
    .status_o        ( status ),
    .extension_bit_o ( extension_bit ),
    .tag_o           ( tag_o ),
    .mask_o          ( mask_o ),
    .aux_o           ( aux_o ),
    .out_valid_o     ( out_valid ),
    .out_ready_i     ( 1'b1 ),
    .busy_o          ( busy )
  );
endmodule
