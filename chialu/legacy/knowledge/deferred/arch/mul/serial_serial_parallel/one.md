---
family: serial_serial_parallel
pin: {serial_operands: one}
---
# one

The serial-parallel multiplier: one factor is held in parallel and
gated into a chain of full-adder stages while the other arrives one
bit per cycle, a carry-save add-shift unit whose equipment depends on
the multiplicand length alone. The LSDF
form first converts one operand to parallel, multiplies while
emitting the low half serially, then serializes the high half;
grouped variants select precomputed multiples up to 3M or 7M to take
several multiplier digits per step.

Serial-parallel is the pick when one operand is constant, preloaded
or already parallel and when throughput lets the three phases of
conversion, multiplication and high-half output overlap as pipeline
stages: it takes 3n cycles of t_SEL + t_CSA + t_FF for nonconstant
operands, a shorter cycle and less circuitry than serial-serial. Gnanasekaran ends the row accumulation
by switching a second adder set into an (n - 1)-bit ripple path that
resolves the stored sum and carry words, (5n - 1)t against 8nt for a
plain add-shift unit at about one third more hardware, the first
n - 1 product bits serial and the rest parallel. Grouping
the multiplier digits in pairs replaces every other full adder by a
small selector, while grouping both factors multiplies speed by the
group size at substantial generation and selection cost. Only the 1D
4-bit serial MAC stays competitive at 5 percent full-precision use.

## references

ercegovac_2004 -> M. D. Ercegovac and T. Lang, "Digital Arithmetic", Morgan Kaufmann, 2004
richards_1955 -> Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
gnanasekaran1985 -> R. Gnanasekaran, "A Fast Serial-Parallel Binary Multiplier", IEEE Transactions on Computers, vol. C-34, pp. 741-744, 1985
camus2019 -> V. Camus, L. Mei, C. Enz, M. Verhelst, "Review and Benchmarking of Precision-Scalable Multiply-Accumulate Unit Architectures for Embedded Neural-Network Processing", IEEE Journal on Emerging and Selected Topics in Circuits and Systems, vol. 9, no. 4, pp. 697-711, 2019
