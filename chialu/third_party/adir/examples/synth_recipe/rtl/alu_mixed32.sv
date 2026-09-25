// alu_mixed32: a 32-bit combinational ALU with an integer add/sub, the
// bitwise ops, shifts, a 16 x 16 -> 32 multiply, the comparisons and
// min/max. The block under synthesis for the synth_recipe example.
module alu_mixed32 (
    input  logic [31:0] a,
    input  logic [31:0] b,
    input  logic [3:0]  op,
    output logic [31:0] y,
    output logic        zero,
    output logic        ovf
);
    logic [32:0] sum, diff;
    logic [31:0] prod;
    logic        lt_s, lt_u;

    assign sum  = {1'b0, a} + {1'b0, b};
    assign diff = {1'b0, a} - {1'b0, b};
    assign prod = a[15:0] * b[15:0];
    assign lt_s = $signed(a) < $signed(b);
    assign lt_u = a < b;

    always_comb begin
        ovf = 1'b0;
        case (op)
            4'd0:  begin y = sum[31:0];  ovf = (a[31] == b[31]) && (sum[31] != a[31]); end
            4'd1:  begin y = diff[31:0]; ovf = (a[31] != b[31]) && (diff[31] != a[31]); end
            4'd2:  y = a & b;
            4'd3:  y = a | b;
            4'd4:  y = a ^ b;
            4'd5:  y = a << b[4:0];
            4'd6:  y = a >> b[4:0];
            4'd7:  y = $signed(a) >>> b[4:0];
            4'd8:  y = prod;
            4'd9:  y = {31'b0, lt_s};
            4'd10: y = {31'b0, lt_u};
            4'd11: y = lt_s ? a : b;
            4'd12: y = lt_s ? b : a;
            4'd13: y = ~(a | b);
            4'd14: y = {a[15:0], a[31:16]};
            default: y = 32'b0;
        endcase
    end

    assign zero = (y == 32'b0);
endmodule
