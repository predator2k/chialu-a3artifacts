---
family: delay_optimized_unified
pin: {path_separation: nonstandard_unified_rounding}
---
# nonstandard_unified_rounding

The path split is chosen so that rounding occurs on one path only: the
R-path takes effective additions, exponent differences of magnitude at
least 2, and subtractions whose pre-shifted significand result is at
least 2, and rounds by injection in a compound sum/sum+1 prefix adder
over the binades [1,4); the N-path takes the remaining subtractions
with at most one bit of alignment and normalizes an exact difference
without rounding.

It is the pick when latency governs: the two-path fp64 adder needs 24
logic levels against 26 and 28 for adapted AMD and SUN close/far
designs, and 30.6 FO4 latency with a 15.3 FO4 cycle by Logical Effort.
The price is unconditional pre-shifts, a compound adder, and, for a
23-level option, duplicated alignment shifters. The unified
single-path form trades the near path for two left shifters and two
anticipators, with equivalent timing and less area than a near/far
adder, four cycles of latency, and support for a double-length fused
operand. The standard close/far split remains the sibling when the
datapath must stay conventional.

## references

seidel_2001 -> P.-M. Seidel and G. Even, "On the Design of Fast IEEE Floating-Point Adders", 15th IEEE Symposium on Computer Arithmetic, 2001
seidel_2004 -> P.-M. Seidel and G. Even, "Delay-Optimized Implementation of IEEE Floating-Point Addition", IEEE Transactions on Computers, 2004
lutz_2011 -> D. R. Lutz, "Fused Multiply-Add Microarchitecture Comprising Separate Early-Normalizing Multiply and Add Pipelines", Proc. 20th IEEE Symposium on Computer Arithmetic (ARITH-20), pp. 123-128, 2011.
