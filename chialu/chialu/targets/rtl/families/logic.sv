// The logic family library: the bitwise gate row of lane_replicated_gates and wide_gate_row.
//   fam_logic_gate_row #(W, NOT_VIA_XOR) (input [W-1:0] a, b, input [1:0] op, output [W-1:0] y)
//   op: 0 and, 1 or, 2 xor, 3 not (of a)
// NOT_VIA_XOR = 1 forms the not as a xor with ones, so the row is three gate types and a
// two-way operand select instead of four gate types under a four-way result mux.
module fam_logic_gate_row #(parameter int W = 16, parameter int NOT_VIA_XOR = 0)
  (input logic [W-1:0] a, input logic [W-1:0] b, input logic [1:0] op, output logic [W-1:0] y);
  generate
    if (NOT_VIA_XOR) begin : via_xor
      logic [W-1:0] bx;
      assign bx = (op == 2'd3) ? {W{1'b1}} : b;
      assign y = (op == 2'd0) ? (a & b) : (op == 2'd1) ? (a | b) : (a ^ bx);
    end else begin : plain
      assign y = (op == 2'd0) ? (a & b) : (op == 2'd1) ? (a | b) : (op == 2'd2) ? (a ^ b) : ~a;
    end
  endgenerate
endmodule
