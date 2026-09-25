# variable_latency

A two-path floating-point adder whose operations complete in one,
two or three cycles by operand class: both the CLOSE and the FAR path
start speculatively in the first cycle, the exponent difference
selects the path, FAR operations finish in three cycles, CLOSE
operations in two, and CLOSE-path operations that need a
normalization shift of at most a few bits finish in one. Early
exponent and leading-one predictors tell the scheduler the completion
class in under eight gate delays, and collision logic pipes an early
result into a later stage when the result bus is busy, so results
leave in FIFO order at one per cycle. Rounding stays IEEE, from a
compound adder precomputing sum and sum+1.

The execution style is variable-iteration, and the contract must
allow it: dynamic instruction scheduling with out-of-order completion
is required to turn the shorter classes into speedup, and a
fixed-latency consumer sees only the worst case. The number of
latency classes and the worst-case cycle count are set by the
underlying pipeline, which here is a three-stage two-path adder; the
one-cycle class is the one that needs the predecode, because the
completion prediction has to be ready in about half a cycle. The
case detection choice therefore decides whether the earliest class
exists at all: predecoding from the exponent difference and the
leading-one predictors makes it available, whereas detection after
the addition can only distinguish the later classes. The short-shift
limit is the knob inside the one-cycle class, since admitting
normalization shifts of up to two bits moves more effective
subtractions into it.

On SPECfp92 traces 43 percent of operations take the CLOSE path and
57 percent the FAR path, and the CLOSE operations split into 20
percent effective additions and 23 percent effective subtractions;
the average latency falls from 3 to 2.57 cycles with a two-cycle
CLOSE path, to 2.37 when first-cycle effective additions are added,
and to 2.25, a 1.33x speedup, when two-bit shifts complete in the
first cycle. Result-bus collisions push some early results back to
three cycles without reducing throughput. The slots are those of the
fixed-latency two-path adder: the significand adder, the rounding
structure, which here is compound-adder select, the exponent path,
the full alignment shifter, the normalizer and the subnormal policy;
the mutation collapse_to_fixed_latency returns to that adder when
the surrounding pipeline cannot consume early results.

## references

oberman_1996 -> S. F. Oberman and M. J. Flynn, "A Variable Latency Pipelined Floating-Point Adder", Euro-Par'96 Parallel Processing (LNCS 1124), Springer, 1996
