// TestFloat vectors through chiALU's alu_core (fp16 mode): one line per
// vector, `a b expected flags` in hex as testfloat_gen writes them; the
// bench applies op/mode/rounding from plusargs, compares y and the flags
// (TestFloat's inexact 1, underflow 2, overflow 4, infinite 8, invalid 16
// against chiALU's invalid, overflow, underflow, inexact bits) and prints
// the mismatches. A NaN result matches any NaN (TestFloat's own rule
// without -checkNaNs). For the comparisons (f16_eq, f16_lt, f16_le) the
// expected value is 0 or 1 and y's {gt, eq, lt} bits are reduced to it.
`timescale 1ns/1ps
module tb;
  logic [15:0] a, b, y;
  logic [2:0] op;
  logic [1:0] mode, rounding_sel;
  logic [7:0] flags;
  alu_core dut (.a(a), .b(b), .op(op), .mode(mode), .rounding_sel(rounding_sel), .y(y), .flags(flags));

  function automatic logic is_nan16(input logic [15:0] x);
    is_nan16 = (&x[14:10]) && (|x[9:0]);
  endfunction

  initial begin
    string vec, kind;
    int fd, n, fails, opv, rnd, r, qnan_invalid, nan_other, subnormal, other;
    logic [15:0] va, vb, exp_y;
    logic [7:0] exp_fl, got_fl;
    logic ok;
    if (!$value$plusargs("vectors=%s", vec)) vec = "vectors.txt";
    if (!$value$plusargs("kind=%s", kind)) kind = "add";
    if (!$value$plusargs("rnd=%d", rnd)) rnd = 0;
    fd = $fopen(vec, "r");
    if (fd == 0) begin $display("HARNESS no vector file %s", vec); $finish; end
    n = 0; fails = 0; qnan_invalid = 0; nan_other = 0; subnormal = 0; other = 0;
    mode = 2'd0;
    rounding_sel = rnd[1:0];
    if (kind == "add") op = 3'd0;
    else if (kind == "sub") op = 3'd1;
    else if (kind == "mul") op = 3'd2;
    else op = 3'd5;   // eq, lt, le through fcmp
    while (!$feof(fd)) begin
      r = $fscanf(fd, "%h %h %h %h\n", va, vb, exp_y, exp_fl);
      if (r != 4) break;
      a = va; b = vb;
      #1;
      // TestFloat flags -> chiALU order [invalid, overflow, underflow, inexact]
      got_fl = flags;
      exp_fl = {4'b0, exp_fl[0], exp_fl[1], exp_fl[2], exp_fl[4]};
      // the comparisons carry their flags too: the quiet predicates raise invalid for a
      // signalling NaN operand alone, which is what the unit reports
      if (kind == "eq")      ok = (y[1] == exp_y[0]) && (got_fl == exp_fl);
      else if (kind == "lt") ok = (y[0] == exp_y[0]) && (got_fl == exp_fl);
      else if (kind == "le") ok = ((y[0] | y[1]) == exp_y[0]) && (got_fl == exp_fl);
      else if (is_nan16(exp_y)) ok = is_nan16(y) && (got_fl == exp_fl);
      else ok = (y == exp_y) && (got_fl == exp_fl);
      if (!ok) begin
        fails++;
        // the class of the mismatch: a quiet-NaN operand where only the invalid flag differs
        // (chiALU raises invalid on any NaN operand, IEEE 754 on a signalling one alone),
        // a NaN operand otherwise, a subnormal operand or result, or the rest
        if ((is_nan16(va) || is_nan16(vb)) && is_nan16(y) && is_nan16(exp_y) && ((got_fl ^ exp_fl) == 8'b0001) && !va[9] != is_nan16(va) && !vb[9] != is_nan16(vb))
          qnan_invalid++;
        else if (is_nan16(va) || is_nan16(vb)) nan_other++;
        else if ((va[14:10] == 0 && va[9:0] != 0) || (vb[14:10] == 0 && vb[9:0] != 0) || (exp_y[14:10] == 0 && exp_y[9:0] != 0)) subnormal++;
        else other++;
        if (fails <= 20)
          $display("MISMATCH %s a=%h b=%h expected y=%h flags=%b got y=%h flags=%b", kind, va, vb, exp_y, exp_fl[3:0], y, got_fl[3:0]);
      end
      n++;
    end
    $fclose(fd);
    $display("TESTFLOAT %s rnd=%0d vectors=%0d mismatches=%0d qnan_invalid=%0d nan_other=%0d subnormal=%0d other=%0d %s", kind, rnd, n, fails, qnan_invalid, nan_other, subnormal, other, fails == 0 ? "PASS" : "FAIL");
    $finish;
  end
endmodule
