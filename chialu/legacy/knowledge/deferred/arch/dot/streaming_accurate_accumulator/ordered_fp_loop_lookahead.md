---
family: streaming_accurate_accumulator
pin: {approach: ordered_fp_loop_lookahead}
---
# ordered_fp_loop_lookahead

An IEEE floating-point adder stays on the loop-carried path and the
recurrence closes in one cycle: a setup cycle analyzes the signs and
exponents of the first two operands, each iterative cycle computes the
significand result while producing the exponent early enough to analyze
that result against the next operand, and a final forwarding cycle ends
the ordered reduction, so n elements take n + 2 cycles. Clock skew
crosses the exponent and significand work inside the single cycle.

The lookahead loop is the accumulator for reductions whose order is
architecturally fixed, as in the Arm SVE ordered floating-point
reduction, where the result must equal a sequential sum and a fixed-
point window or a tree cannot be substituted. Every step rounds, so the
error contract is that of n sequential IEEE additions rather than the
exact or bounded sum of the window accumulator, and
in_loop_normalization is true. The design pays circuit effort rather
than area: the analysis of the next operand overlaps the significand
datapath, and the skewed clocking inside the loop is what lets a multi-
cycle adder deliver one dependent addition per cycle. Where the
summation order is free, the shifted window keeps only a fixed-point add
in the loop and the compensated form recovers accuracy with a standard
adder.

The library realizes this choice as a pin of the generated streaming_accurate_accumulator module (`chialu/targets/rtl/families/dot.py`); the family card names the construction.

## references

lutz_2019 -> D. R. Lutz, "ARM Floating Point 2019: Latency, Area, Power", 26th IEEE Symposium on Computer Arithmetic, 2019
