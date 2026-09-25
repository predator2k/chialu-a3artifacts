// TransDot's no-DP SIMD FMA computing the fp16 dot product of Table B as a
// cascade of fused multiply-adds behind the one-mode `dot_core` of
// targets/eval/vec_dot_acc_cmp_fp16.yaml: d = fma(a1, b1, fma(a0, b0, c)),
// every operand of a stage read as fp16 x fp16 + fp32 -> fp32. The unit is
// `transdot_fp16_fp32_fma_simd` (src/transdot_no_dp/transdot_fp16_fp32_fma_simd_base.sv,
// the fork's "best" no-DP design and the ADDMUL unit of its fpnew_top under
// `SIMD_ENABLE`), instantiated directly as transdot_dot_core_fp16.sv
// instantiates the DP unit, with NumPipeRegs 0, op FMADD, src_fmt FP16 for
// the multiplicands, src2_fmt and dst_fmt FP32 for the addend and the result,
// simd_enable 0 (the scalar mixed-precision path). FpFmtConfig enables FP32
// and FP16 alone.
//
// The contract: each stage rounds its exact product plus addend once to
// fp32, so the cascade rounds after every term. Since an fp16 product is
// exact in fp32, this is chiALU's `sequential` contract (docs/formats-and-
// options.md, section 6): every product rounded to format_d, then c and the
// products added in element order with a rounding each.
//
// The decode and what it costs (the report's wrapper column): element k of
// `a` and `b` sits at bits [16k +: 16] and enters stage k in the low half of
// operands 0 and 1 (the slice the scalar path reads); the addend of stage 0
// is c and of stage k the previous stage's result. The handshake is tied and
// the status outputs are unused (`flags: []`).
module dot_core (
  input  logic [31:0] a,
  input  logic [31:0] b,
  input  logic [31:0] c,
  output logic [31:0] d
);
  localparam fpnew_pkg::fmt_logic_t FMTS = 7'b1010000;   // [0:6] = FP32, FP64, FP16, FP8, FP16ALT, FP4, FP8ALT
  logic [31:0] acc0;

  logic [2:0][31:0] ops0, ops1;
  assign ops0[0] = {16'b0, a[15:0]};
  assign ops0[1] = {16'b0, b[15:0]};
  assign ops0[2] = c;
  assign ops1[0] = {16'b0, a[31:16]};
  assign ops1[1] = {16'b0, b[31:16]};
  assign ops1[2] = acc0;

  fpnew_pkg::status_t st0, st1;
  logic ext0, ext1, tag0, tag1, msk0, msk1, aux0, aux1, ov0, ov1, ir0, ir1, bz0, bz1;

  transdot_fp16_fp32_fma_simd #(
    .FpFmtConfig ( FMTS ), .NumPipeRegs ( 0 ), .PipeConfig ( fpnew_pkg::BEFORE ),
    .TagType ( logic ), .AuxType ( logic )
  ) u_stage0 (
    .clk_i ( 1'b0 ), .rst_ni ( 1'b1 ),
    .operands_i ( ops0 ), .is_boxed_i ( '1 ), .rnd_mode_i ( fpnew_pkg::RNE ),
    .op_i ( fpnew_pkg::FMADD ), .op_mod_i ( 1'b0 ),
    .src_fmt_i ( fpnew_pkg::FP16 ), .src2_fmt_i ( fpnew_pkg::FP32 ), .dst_fmt_i ( fpnew_pkg::FP32 ),
    .tag_i ( 1'b0 ), .mask_i ( 1'b1 ), .aux_i ( 1'b0 ), .simd_enable_i ( 1'b0 ),
    .in_valid_i ( 1'b1 ), .in_ready_o ( ir0 ), .flush_i ( 1'b0 ),
    .result_o ( acc0 ), .status_o ( st0 ), .extension_bit_o ( ext0 ),
    .tag_o ( tag0 ), .mask_o ( msk0 ), .aux_o ( aux0 ),
    .out_valid_o ( ov0 ), .out_ready_i ( 1'b1 ), .busy_o ( bz0 ), .reg_ena_i ( '0 )
  );

  transdot_fp16_fp32_fma_simd #(
    .FpFmtConfig ( FMTS ), .NumPipeRegs ( 0 ), .PipeConfig ( fpnew_pkg::BEFORE ),
    .TagType ( logic ), .AuxType ( logic )
  ) u_stage1 (
    .clk_i ( 1'b0 ), .rst_ni ( 1'b1 ),
    .operands_i ( ops1 ), .is_boxed_i ( '1 ), .rnd_mode_i ( fpnew_pkg::RNE ),
    .op_i ( fpnew_pkg::FMADD ), .op_mod_i ( 1'b0 ),
    .src_fmt_i ( fpnew_pkg::FP16 ), .src2_fmt_i ( fpnew_pkg::FP32 ), .dst_fmt_i ( fpnew_pkg::FP32 ),
    .tag_i ( 1'b0 ), .mask_i ( 1'b1 ), .aux_i ( 1'b0 ), .simd_enable_i ( 1'b0 ),
    .in_valid_i ( 1'b1 ), .in_ready_o ( ir1 ), .flush_i ( 1'b0 ),
    .result_o ( d ), .status_o ( st1 ), .extension_bit_o ( ext1 ),
    .tag_o ( tag1 ), .mask_o ( msk1 ), .aux_o ( aux1 ),
    .out_valid_o ( ov1 ), .out_ready_i ( 1'b1 ), .busy_o ( bz1 ), .reg_ena_i ( '0 )
  );
endmodule
