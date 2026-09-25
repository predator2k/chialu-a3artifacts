---
family: delay_optimized_unified
pin: {lz_count_source: exact_operands}
---
# exact_operands

Two leading-zero anticipators run on the ordered operands in the
second stage, two cycles before the addition; the third stage
left-shifts the cancellation case by that count, or right-aligns the
ordinary far case, so the fourth stage adds and injects rounding
without a post-add normalization cycle. Two final adders absorb the
anticipator's one-bit correction and accept a double-length unrounded
operand.

It is the pick when the adder pipeline is also the add stage of a
fused multiply-add and must take a 105-bit fraction, and when a fixed
four-cycle latency without a normalization cycle is wanted: the design
replaces the near path with two left shifters and two anticipators,
with equivalent timing and less area than a near/far adder, and keeps
subnormal operands and results in the normal datapath. Effective
subtractions with an exponent difference other than zero or one ignore
the anticipators. The borrow-save approximation is the sibling when
the count can arrive later on a non-critical N-path.

## references

lutz_2011 -> D. R. Lutz, "Fused Multiply-Add Microarchitecture Comprising Separate Early-Normalizing Multiply and Add Pipelines", Proc. 20th IEEE Symposium on Computer Arithmetic (ARITH-20), pp. 123-128, 2011.
