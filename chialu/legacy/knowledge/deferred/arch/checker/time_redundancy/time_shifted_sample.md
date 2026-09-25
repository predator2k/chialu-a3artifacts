---
family: time_redundancy
pin: {transform: time_shifted_sample}
---
# time_shifted_sample

The same signal sampled at two times rather than the same function
on two operands: Razor pairs each delay-critical flip-flop with a
shadow latch on a delayed clock, whose sample is guaranteed under
worst-case subcritical conditions, and a comparator flags disagreement with the main sample; the shadow value then
replaces the main one and clock gating or a counterflow flush keeps
wrong state from committing. Self-dual parity checking applies
complementary inputs at successive time units.

Time-shifted sampling is the pick when the fault to catch is a timing
violation from voltage or frequency scaling rather than a logic
fault: the 0.18-µm Alpha pipeline pays 3.1 percent power in
error-free operation for a 42 percent average adder energy reduction
at the energy-optimal supply, with about 1 percent recovery overhead
at a 10 percent error rate. Its costs are short-path buffers, which
trade power against scaling range, a metastable main sample that
must be treated as an error and may force a panic restart, and
coverage limited to the monitored datapaths; the self-dual form pays
100 percent time redundancy and the self-dual complement hardware.

The generated checker has no realization for this family (an exception, `alu_checker.EXCEPTIONS`): a shadow-latch sample over cycles.

## references

ernst_2003 -> D. Ernst, N. S. Kim, S. Das, et al., "Razor: A Low-Power Pipeline Based on Circuit-Level Timing Speculation", Proc. MICRO-36, pp. 7-18, 2003
lala_2001 -> P. K. Lala, "Self-Checking and Fault-Tolerant Digital Design", Morgan Kaufmann, 2001
