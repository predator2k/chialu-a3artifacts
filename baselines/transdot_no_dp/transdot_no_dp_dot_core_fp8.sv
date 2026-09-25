// TransDot's no-DP SIMD FMA computing the fp8e5m2 dot product of Table B as a
// cascade of four fused multiply-adds behind the one-mode `dot_core` of
// targets/eval/vec_dot_acc_cmp_fp8.yaml:
// d = fma(a3, b3, fma(a2, b2, fma(a1, b1, fma(a0, b0, c)))), every stage
// fp8e5m2 x fp8e5m2 + fp32 -> fp32. The unit is `transdot_fp16_fp32_fma_simd`
// (see transdot_no_dp_dot_core_fp16.sv), NumPipeRegs 0, op FMADD, src_fmt
// FP8ALT (E5M2 in TransDot's fork; its FP8 is E4M3), src2_fmt and dst_fmt
// FP32, simd_enable 0. FpFmtConfig enables FP32 and FP8ALT alone.
//
// The contract is chiALU's `sequential` one (an fp8 product is exact in fp32,
// so rounding the product plus addend once per stage rounds after every
// term). Element k of `a` and `b` sits at bits [8k +: 8] and enters stage k in
// the low byte of operands 0 and 1; the addend chains through the stages.
module dot_core (
  input  logic [31:0] a,
  input  logic [31:0] b,
  input  logic [31:0] c,
  output logic [31:0] d
);
  localparam fpnew_pkg::fmt_logic_t FMTS = 7'b1000001;   // [0:6] = FP32, FP64, FP16, FP8, FP16ALT, FP4, FP8ALT
  logic [4:0][31:0] acc;
  assign acc[0] = c;
  assign d = acc[4];

  for (genvar k = 0; k < 4; k++) begin : g_stage
    logic [2:0][31:0] ops;
    assign ops[0] = {24'b0, a[8*k +: 8]};
    assign ops[1] = {24'b0, b[8*k +: 8]};
    assign ops[2] = acc[k];
    fpnew_pkg::status_t st;
    logic ext, tag, msk, aux, ov, ir, bz;
    transdot_fp16_fp32_fma_simd #(
      .FpFmtConfig ( FMTS ), .NumPipeRegs ( 0 ), .PipeConfig ( fpnew_pkg::BEFORE ),
      .TagType ( logic ), .AuxType ( logic )
    ) u_stage (
      .clk_i ( 1'b0 ), .rst_ni ( 1'b1 ),
      .operands_i ( ops ), .is_boxed_i ( '1 ), .rnd_mode_i ( fpnew_pkg::RNE ),
      .op_i ( fpnew_pkg::FMADD ), .op_mod_i ( 1'b0 ),
      .src_fmt_i ( fpnew_pkg::FP8ALT ), .src2_fmt_i ( fpnew_pkg::FP32 ), .dst_fmt_i ( fpnew_pkg::FP32 ),
      .tag_i ( 1'b0 ), .mask_i ( 1'b1 ), .aux_i ( 1'b0 ), .simd_enable_i ( 1'b0 ),
      .in_valid_i ( 1'b1 ), .in_ready_o ( ir ), .flush_i ( 1'b0 ),
      .result_o ( acc[k+1] ), .status_o ( st ), .extension_bit_o ( ext ),
      .tag_o ( tag ), .mask_o ( msk ), .aux_o ( aux ),
      .out_valid_o ( ov ), .out_ready_i ( 1'b1 ), .busy_o ( bz ), .reg_ena_i ( '0 )
    );
  end
endmodule
