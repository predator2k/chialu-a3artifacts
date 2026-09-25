// TransDot's no-DP SIMD FMA (the fork's "best no-DP design") behind chiALU's
// `alu_core` interface of targets/eval/fp_alu_cmp.yaml, the third reference row.
// The fork branch `noregs` of predator2k/SafeDot (TransDot's fork) makes the
// feature set and the implementation parameters of `transdot_fpu_top` and adds
// ADDMUL_ONLY_NOREGS (no pipeline register, ADDMUL merged, NONCOMP parallel) and
// transdot_features_16 (FP16, FP16ALT, FP8ALT lanes in a 16-bit word). The build
// defines SIMD_ENABLE (the no-DP FMA `transdot_fp16_fp32_fma_simd`),
// TRANSDOT_NO_DP, FP8_INCLUDED and COMBINATIONAL (the multiplier without its
// registers). The decode is the FPnew wrapper's: see baselines/fpnew.
// TransDot's FP8 is E4M3 and its FP8ALT is E5M2 (index 6), the format of the
// comparison; whether the SIMD FMA serves FP8ALT lanes is what the conformance
// run decides.
module alu_core (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0]  op,            // 0 fadd, 1 fsub, 2 fmul, 3 fmin, 4 fmax, 5 fcmp
  input  logic [1:0]  mode,          // 0 fp16, 1 bf16, 2 two fp8e5m2 lanes
  input  logic [1:0]  rounding_sel,  // 0 RNE, 1 RTZ, 2 RDN, 3 RUP
  output logic [15:0] y,
  output logic [7:0]  flags
);
  localparam fpnew_pkg::fpu_implementation_t IMPL_CMP = '{
    PipeRegs:   '{default: 0},
    UnitTypes:  '{'{default: fpnew_pkg::DISABLED},
                  '{default: fpnew_pkg::DISABLED},
                  '{default: fpnew_pkg::PARALLEL},
                  '{default: fpnew_pkg::DISABLED}},
    PipeConfig: fpnew_pkg::BEFORE
  };

  logic is_add, is_sub, is_mul, is_min, is_max, is_cmp, vec;
  assign is_add = (op == 3'd0);
  assign is_sub = (op == 3'd1);
  assign is_mul = (op == 3'd2);
  assign is_min = (op == 3'd3);
  assign is_max = (op == 3'd4);
  assign is_cmp = (op == 3'd5);
  assign vec    = (mode == 2'd2);

  fpnew_pkg::fp_format_e fmt;
  always_comb begin
    unique case (mode)
      2'd0:    fmt = fpnew_pkg::FP16;
      2'd1:    fmt = fpnew_pkg::FP16ALT;
      default: fmt = fpnew_pkg::FP8ALT;
    endcase
  end

  fpnew_pkg::operation_e fpu_op;
  logic                  fpu_mod;
  fpnew_pkg::roundmode_e fpu_rnd, rnd_sel;
  always_comb begin
    unique case (rounding_sel)
      2'd0:    rnd_sel = fpnew_pkg::RNE;
      2'd1:    rnd_sel = fpnew_pkg::RTZ;
      2'd2:    rnd_sel = fpnew_pkg::RDN;
      default: rnd_sel = fpnew_pkg::RUP;
    endcase
    fpu_mod = is_sub;
    if (is_add | is_sub)      begin fpu_op = fpnew_pkg::ADD;    fpu_rnd = rnd_sel;         end
    else if (is_mul)          begin fpu_op = fpnew_pkg::MUL;    fpu_rnd = rnd_sel;         end
    else if (is_min)          begin fpu_op = fpnew_pkg::MINMAX; fpu_rnd = fpnew_pkg::RNE;  end
    else if (is_max)          begin fpu_op = fpnew_pkg::MINMAX; fpu_rnd = fpnew_pkg::RTZ;  end
    else                      begin fpu_op = fpnew_pkg::CMP;    fpu_rnd = fpnew_pkg::RTZ;  end
  end

  logic [2:0][15:0] operands;
  assign operands[0] = a;
  assign operands[1] = (is_add | is_sub) ? a : b;
  assign operands[2] = b;

  logic [15:0]        res_main, res_eq;
  fpnew_pkg::status_t st_main, st_eq;
  logic unused_ready, unused_valid, unused_busy, unused_tag;
  logic unused_ready2, unused_valid2, unused_busy2, unused_tag2;

  transdot_fpu_top #(
    .EnableSIMDMask (0),
    .Features       (fpnew_pkg::transdot_features_16),
    .Implementation (fpnew_pkg::ADDMUL_ONLY_NOREGS)
  ) u_fpu (
    .clk_i (1'b0), .rst_ni (1'b1),
    .operands_i (operands), .rnd_mode_i (fpu_rnd), .op_i (fpu_op), .op_mod_i (fpu_mod),
    .src_fmt_i (fmt), .dst_fmt_i (fmt), .int_fmt_i (fpnew_pkg::INT8), .vectorial_op_i (vec),
    .tag_i (1'b0), .simd_mask_i ('1), .in_valid_i (1'b1), .in_ready_o (unused_ready), .flush_i (1'b0),
    .result_o (res_main), .status_o (st_main), .tag_o (unused_tag), .out_valid_o (unused_valid),
    .out_ready_i (1'b1), .busy_o (unused_busy)
  );

  transdot_fpu_top #(
    .EnableSIMDMask (0),
    .Features       (fpnew_pkg::transdot_features_16),
    .Implementation (IMPL_CMP)
  ) u_cmp_eq (
    .clk_i (1'b0), .rst_ni (1'b1),
    .operands_i (operands), .rnd_mode_i (fpnew_pkg::RDN), .op_i (fpnew_pkg::CMP), .op_mod_i (1'b0),
    .src_fmt_i (fmt), .dst_fmt_i (fmt), .int_fmt_i (fpnew_pkg::INT8), .vectorial_op_i (vec),
    .tag_i (1'b0), .simd_mask_i ('1), .in_valid_i (is_cmp), .in_ready_o (unused_ready2), .flush_i (1'b0),
    .result_o (res_eq), .status_o (st_eq), .tag_o (unused_tag2), .out_valid_o (unused_valid2),
    .out_ready_i (1'b1), .busy_o (unused_busy2)
  );

  function automatic logic is_nan16(input logic [15:0] x, input logic bf);
    is_nan16 = bf ? (&x[14:7] && |x[6:0]) : (&x[14:10] && |x[9:0]);
  endfunction
  function automatic logic is_nan8(input logic [7:0] x);
    is_nan8 = (&x[6:2]) && |x[1:0];
  endfunction
  logic nan_l0, nan_l1;
  always_comb begin
    if (vec) begin
      nan_l0 = is_nan8(a[7:0]) | is_nan8(b[7:0]);
      nan_l1 = is_nan8(a[15:8]) | is_nan8(b[15:8]);
    end else begin
      nan_l0 = is_nan16(a, mode == 2'd1) | is_nan16(b, mode == 2'd1);
      nan_l1 = 1'b0;
    end
  end

  logic [3:0] fl_main;
  assign fl_main = {st_main.NX, st_main.UF, st_main.OF, is_cmp ? st_eq.NV : st_main.NV};
  // the comparison bits of each lane as continuous assigns: declared inside the always_comb and assigned
  // in one branch alone they were block-static variables, which yosys lowers to a latch and a logic loop
  logic lt0, lt1, eq0, eq1;
  assign lt0 = res_main[0], lt1 = res_main[8], eq0 = res_eq[0], eq1 = res_eq[8];
  always_comb begin
    if (is_cmp) begin
      if (vec) begin
        y = {5'b0, ~lt1 & ~eq1 & ~nan_l1, eq1, lt1, 5'b0, ~lt0 & ~eq0 & ~nan_l0, eq0, lt0};
      end else begin
        y = {13'b0, ~res_main[0] & ~res_eq[0] & ~nan_l0, res_eq[0], res_main[0]};
      end
    end else begin
      y = res_main;
    end
    flags = vec ? {fl_main, fl_main} : {4'b0, fl_main};
  end
endmodule
