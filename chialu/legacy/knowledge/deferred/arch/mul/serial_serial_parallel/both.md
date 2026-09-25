---
family: serial_serial_parallel
pin: {serial_operands: both}
---
# both

The serial-serial multiplier: both operands arrive one digit per
cycle, least significant first in the LSDF form, and the product
residual stays in two carry-save vectors while an n-position [4:2]
adder folds in the two new digit multiples each cycle and the low
product bit leaves through a serial adder. Dadda's version sums the
newly available partial-product rows and diagonals, or columns, with
parallel counters; Ienne's slice uses a (5,3) counter and emits
output from the first input cycle.

Serial-serial is the pick when both operands stream in from a serial
source and the product must start leaving before they have finished
arriving: the LSDF form takes 2n cycles of t_SEL + t_[4:2] + t_FF and
costs one n-bit [4:2] adder, five n-bit registers and the
multiple-forming gates, more circuitry and a longer cycle than the
serial-parallel form but with no input conversion phase. Ienne's
slices reach zero clock-cycle latency between corresponding input and
output bits with N - 1 slices, and continued sign extension yields an
arbitrarily long correct product. Lyon's two's-complement pipeline
accepts a new word every N bit times despite an N + K bit-time delay,
with Booth or five-level coefficient recoding and truncation that
implements a floor. The 2D bit-serial MAC costs 14 times the energy
per operation of a data-gated parallel MAC at full precision in 28 nm,
against 3.3 for 1D.

## references

ercegovac_2004 -> M. D. Ercegovac and T. Lang, "Digital Arithmetic", Morgan Kaufmann, 2004
richards_1955 -> Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
ienne1994 -> P. Ienne, M. A. Viredaz, "Bit-Serial Multipliers and Squarers", IEEE Transactions on Computers, vol. 43, no. 12, pp. 1445-1450, 1994
lyon1976 -> R. F. Lyon, "Two's Complement Pipeline Multipliers", IEEE Transactions on Communications, vol. COM-24, pp. 418-425, 1976
camus2019 -> V. Camus, L. Mei, C. Enz, M. Verhelst, "Review and Benchmarking of Precision-Scalable Multiply-Accumulate Unit Architectures for Embedded Neural-Network Processing", IEEE Journal on Emerging and Selected Topics in Circuits and Systems, vol. 9, no. 4, pp. 697-711, 2019
