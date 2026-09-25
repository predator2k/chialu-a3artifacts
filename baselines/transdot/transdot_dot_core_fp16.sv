// The fp16 half of TransDot's DP mode, which is the mode that meets the fused
// contract, behind the one-mode `dot_core` of
// TransDot's dot-product (DP) mode behind chiALU's `dot_core` interface of
// targets/eval/vec_dot_acc_cmp.yaml: mode 0 is two fp16 products with an fp32
// addend into fp32, mode 1 is four fp8e5m2 products with an fp32 addend into
// fp32. The reference design is `transdot_fp4_fp8_fp16_fp32_fma` with
// NumPipeRegs 0, driven at TDOT_DP_FMADD, which is the operation whose decode
// in fpnew_opgroup_multifmt_slice raises dp_enable.
//
// The decode and what it costs (the report's wrapper column):
//   * operands_i[0] and [1] carry the multiplicand lanes in the slicing the
//     FMA's own lanes read: the low half, the high half and, for fp8, the two
//     quarter slices, which is the packing chiALU's `a` and `b` already use.
//   * operands_i[2] is the fp32 addend, which the FP32 slice of the same port
//     reads whole.
//   * src_fmt_i selects the term format per mode; FP8ALT is E5M2 in TransDot's
//     fork, whose FP8 is E4M3.
//   * the handshake is tied: in_valid_i and out_ready_i stand at one and the
//     valid outputs are unused. The unit is not combinational at NumPipeRegs 0:
//     one register stage between the exponent datapath and the adder updates on
//     every clock edge whatever the parameter, so the wrapper carries clk and
//     rst_n and the bench drives them (latency_cycles 1).
//   * the status output is unused: the comparison target binds `flags: []` for
//     the dot unit.
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
    .FpFmtConfig ( 7'b1010000 ),      // [0:6] = FP32, FP64, FP16, FP8, FP16ALT, FP4, FP8ALT
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
    .src_fmt_i       ( fpnew_pkg::FP16 ),
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
