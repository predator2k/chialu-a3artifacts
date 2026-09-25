// FPnew alone, the same parameters as fpnew_alu_core.sv without the decode: the
// reference design's own cost (the report's bare column). One instance; fcmp's
// second relation is wrapper cost and is not here.
`ifndef FPNEW_ADDMUL
`define FPNEW_ADDMUL MERGED
`endif
module fpnew_bare (
  input  logic [2:0][15:0]      operands_i,
  input  fpnew_pkg::roundmode_e rnd_mode_i,
  input  fpnew_pkg::operation_e op_i,
  input  logic                  op_mod_i,
  input  fpnew_pkg::fp_format_e fmt_i,
  input  logic                  vectorial_op_i,
  output logic [15:0]           result_o,
  output fpnew_pkg::status_t    status_o
);
  localparam fpnew_pkg::fpu_features_t FEATURES = '{
    Width: 16, EnableVectors: 1'b1, EnableNanBox: 1'b0, FpFmtMask: 5'b00111, IntFmtMask: 4'b0000 };
  localparam fpnew_pkg::fpu_implementation_t IMPL = '{
    PipeRegs:   '{default: 0},
    UnitTypes:  '{'{fpnew_pkg::DISABLED, fpnew_pkg::DISABLED, fpnew_pkg::`FPNEW_ADDMUL, fpnew_pkg::`FPNEW_ADDMUL, fpnew_pkg::`FPNEW_ADDMUL},
                  '{default: fpnew_pkg::DISABLED},
                  '{fpnew_pkg::DISABLED, fpnew_pkg::DISABLED, fpnew_pkg::PARALLEL, fpnew_pkg::PARALLEL, fpnew_pkg::PARALLEL},
                  '{default: fpnew_pkg::DISABLED}},
    PipeConfig: fpnew_pkg::BEFORE };
  logic unused_ready, unused_valid, unused_busy, unused_early, unused_tag;
  fpnew_top #(.Features(FEATURES), .Implementation(IMPL), .DivSqrtSel(fpnew_pkg::THMULTI), .TagType(logic),
              .TrueSIMDClass(0), .EnableSIMDMask(0)) u_fpu (
    .clk_i(1'b0), .rst_ni(1'b1), .operands_i(operands_i), .rnd_mode_i(rnd_mode_i), .op_i(op_i), .op_mod_i(op_mod_i),
    .src_fmt_i(fmt_i), .dst_fmt_i(fmt_i), .int_fmt_i(fpnew_pkg::INT8), .vectorial_op_i(vectorial_op_i), .tag_i(1'b0),
    .simd_mask_i('1), .in_valid_i(1'b1), .in_ready_o(unused_ready), .flush_i(1'b0), .result_o(result_o),
    .status_o(status_o), .tag_o(unused_tag), .out_valid_o(unused_valid), .out_ready_i(1'b1), .busy_o(unused_busy),
    .early_valid_o(unused_early));
endmodule
