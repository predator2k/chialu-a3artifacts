---
family: residue
pin: {granularity: per_stage}
---
# per_stage

Residue checks at component destinations inside the operation: in the
z196 decimal accelerator the operand and result registers carry a
modulo-9 residue, and predicted residues at each register transfer,
rotation and alignment step account for the arithmetic function,
rounding injection, rotation and digits shifted into guard and sticky
positions, partial-product storage and shifted-out digits included; a
full-instruction check spans addition, subtraction, multiplication
and conversions.

Component-level checking is what lets a residue code follow a
floating-point significand through alignment, truncated digits and
rounding, which the endpoint form must fold into one prediction or
else check the exponent, significand, interface and control paths
separately. The price is a residue on every covered register and a
predictor per component, and the modulus follows the data: Res9 for
decimal computation and Res3 for binary/decimal conversions, each
detecting single-bit errors without a reported numeric coverage. It
is the pick for a multi-stage decimal or floating-point dataflow
where the intermediate registers already exist; a single fixed-point
adder or multiplier keeps the cheaper endpoint mirror.

The generated checker checks at the endpoint (the module's outputs); a per-stage check needs the datapath's stage latches, which the seam does not carry.

## references

carlough_2011 -> Carlough, Collura, Mueller, Kroener, "The IBM zEnterprise-196 Decimal Floating-Point Accelerator", 20th IEEE Symposium on Computer Arithmetic (ARITH-20), 2011
lipetz_schwarz_2011 -> D. Lipetz, E. Schwarz, "Self Checking in Current Floating-Point Units", Proc. 20th IEEE Symposium on Computer Arithmetic (ARITH-20), pp. 73-76, 2011
