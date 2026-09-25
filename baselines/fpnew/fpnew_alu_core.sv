// The FPnew (CVFPU) reference design behind chiALU's `alu_core` interface
// of targets/eval/fp_alu_cmp.yaml: modes 1 x fp16, 1 x bf16 (FP16ALT),
// 2 x fp8e5m2 (FP8, vectorial); ops fadd, fsub, fmul, fmin, fmax, fcmp;
// rounding_sel over RNE, RTZ, RDN, RUP; one flag word for the whole
// operation in the order invalid, overflow, underflow, inexact, which is
// the target's flag_scope: per_operation.
//
// Design point FPNEW_ADDMUL (a `define): MERGED, one multi-format FMA for
// the three formats, or PARALLEL, one FMA slice per format. NONCOMP is
// PARALLEL in every point (FPnew offers no merged NONCOMP).
//
// The decode and what it costs (the report's wrapper column):
//   * ADD takes FPnew's operands 1 and 2, MUL 0 and 1, so operand 1 is a
//     mux between `a` and `b`; op_mod gives fsub.
//   * fmin / fmax are MINMAX under RNE / RTZ; FPnew's minimumNumber /
//     maximumNumber is chiALU's `minmax_nan: number`.
//   * fcmp returns {gt, eq, lt}; FPnew's CMP returns one relation per
//     operation, so a second fpnew_top with NONCOMP alone computes EQ
//     beside the main instance's LT, and gt is neither, nor unordered;
//     the unordered test (a NaN operand) is decoded here. chiALU's fcmp
//     is a quiet comparison (invalid on a signalling NaN alone), which is
//     the EQ instance's NV; the LT instance's NV (any NaN) is not used.
//   * For the vectorial fp8 mode FPnew reports one status for both
//     lanes (the OR). The comparison target binds flag_scope:
//     per_operation, which is that convention, so the wrapper drives the
//     one word the interface carries.
`ifndef FPNEW_ADDMUL
`define FPNEW_ADDMUL MERGED
`endif

module alu_core (
  input  logic [15:0] a,
  input  logic [15:0] b,
  input  logic [2:0]  op,            // 0 fadd, 1 fsub, 2 fmul, 3 fmin, 4 fmax, 5 fcmp
  input  logic [1:0]  mode,          // 0 fp16, 1 bf16, 2 two fp8e5m2 lanes
  input  logic [1:0]  rounding_sel,  // 0 RNE, 1 RTZ, 2 RDN, 3 RUP
  output logic [15:0] y,
  output logic [3:0]  flags
);
  localparam fpnew_pkg::fpu_features_t FEATURES = '{
    Width:         16,
    EnableVectors: 1'b1,
    EnableNanBox:  1'b0,
    FpFmtMask:     5'b00111,   // FP16, FP8, FP16ALT (indices 2, 3, 4)
    IntFmtMask:    4'b0000
  };
  localparam fpnew_pkg::fpu_implementation_t IMPL = '{
    PipeRegs:   '{default: 0},
    UnitTypes:  '{'{fpnew_pkg::DISABLED, fpnew_pkg::DISABLED, fpnew_pkg::`FPNEW_ADDMUL, fpnew_pkg::`FPNEW_ADDMUL, fpnew_pkg::`FPNEW_ADDMUL}, // ADDMUL
                  '{default: fpnew_pkg::DISABLED},                                                                                             // DIVSQRT
                  '{fpnew_pkg::DISABLED, fpnew_pkg::DISABLED, fpnew_pkg::PARALLEL, fpnew_pkg::PARALLEL, fpnew_pkg::PARALLEL},                 // NONCOMP
                  '{default: fpnew_pkg::DISABLED}},                                                                                            // CONV
    PipeConfig: fpnew_pkg::BEFORE
  };
  localparam fpnew_pkg::fpu_implementation_t IMPL_CMP = '{
    PipeRegs:   '{default: 0},
    UnitTypes:  '{'{default: fpnew_pkg::DISABLED},
                  '{default: fpnew_pkg::DISABLED},
                  '{fpnew_pkg::DISABLED, fpnew_pkg::DISABLED, fpnew_pkg::PARALLEL, fpnew_pkg::PARALLEL, fpnew_pkg::PARALLEL},
                  '{default: fpnew_pkg::DISABLED}},
    PipeConfig: fpnew_pkg::BEFORE
  };

  // ---- decode
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
      default: fmt = fpnew_pkg::FP8;
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
    else                      begin fpu_op = fpnew_pkg::CMP;    fpu_rnd = fpnew_pkg::RTZ;  end  // LT
  end

  logic [2:0][15:0] operands;
  assign operands[0] = a;                       // MUL / MINMAX / CMP operand A
  assign operands[1] = (is_add | is_sub) ? a : b; // ADD's first addend, else operand B
  assign operands[2] = b;                       // ADD's second addend

  // ---- the FPU
  logic [15:0]        res_main, res_eq;
  fpnew_pkg::status_t st_main, st_eq;
  logic               unused_ready, unused_valid, unused_busy, unused_early, unused_tag;
  logic               unused_ready2, unused_valid2, unused_busy2, unused_early2, unused_tag2;

  fpnew_top #(
    .Features       (FEATURES),
    .Implementation (IMPL),
    .DivSqrtSel     (fpnew_pkg::THMULTI),
    .TagType        (logic),
    .TrueSIMDClass  (0),
    .EnableSIMDMask (0)
  ) u_fpu (
    .clk_i          (1'b0),
    .rst_ni         (1'b1),
    .operands_i     (operands),
    .rnd_mode_i     (fpu_rnd),
    .op_i           (fpu_op),
    .op_mod_i       (fpu_mod),
    .src_fmt_i      (fmt),
    .dst_fmt_i      (fmt),
    .int_fmt_i      (fpnew_pkg::INT8),
    .vectorial_op_i (vec),
    .tag_i          (1'b0),
    .simd_mask_i    ('1),
    .in_valid_i     (1'b1),
    .in_ready_o     (unused_ready),
    .flush_i        (1'b0),
    .result_o       (res_main),
    .status_o       (st_main),
    .tag_o          (unused_tag),
    .out_valid_o    (unused_valid),
    .out_ready_i    (1'b1),
    .busy_o         (unused_busy),
    .early_valid_o  (unused_early)
  );

  // the second relation of fcmp: EQ (CMP under RDN), NONCOMP alone
  fpnew_top #(
    .Features       (FEATURES),
    .Implementation (IMPL_CMP),
    .DivSqrtSel     (fpnew_pkg::THMULTI),
    .TagType        (logic),
    .TrueSIMDClass  (0),
    .EnableSIMDMask (0)
  ) u_cmp_eq (
    .clk_i          (1'b0),
    .rst_ni         (1'b1),
    .operands_i     (operands),
    .rnd_mode_i     (fpnew_pkg::RDN),
    .op_i           (fpnew_pkg::CMP),
    .op_mod_i       (1'b0),
    .src_fmt_i      (fmt),
    .dst_fmt_i      (fmt),
    .int_fmt_i      (fpnew_pkg::INT8),
    .vectorial_op_i (vec),
    .tag_i          (1'b0),
    .simd_mask_i    ('1),
    .in_valid_i     (is_cmp),
    .in_ready_o     (unused_ready2),
    .flush_i        (1'b0),
    .result_o       (res_eq),
    .status_o       (st_eq),
    .tag_o          (unused_tag2),
    .out_valid_o    (unused_valid2),
    .out_ready_i    (1'b1),
    .busy_o         (unused_busy2),
    .early_valid_o  (unused_early2)
  );

  // ---- unordered (a NaN operand) per lane, for fcmp's gt
  function automatic logic is_nan16(input logic [15:0] x, input logic bf);
    // fp16: exponent [14:10], mantissa [9:0]; bf16: exponent [14:7], mantissa [6:0]
    is_nan16 = bf ? (&x[14:7] && |x[6:0]) : (&x[14:10] && |x[9:0]);
  endfunction
  function automatic logic is_nan8(input logic [7:0] x);
    // fp8e5m2: exponent [6:2], mantissa [1:0]
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

  // ---- results
  // fcmp is a quiet comparison: its invalid flag is the EQ instance's (NV on a signalling NaN alone),
  // not the LT instance's, which FPnew makes a signalling comparison (NV on any NaN)
  logic [3:0] fl_main;   // invalid, overflow, underflow, inexact
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
    flags = fl_main;
  end
endmodule
