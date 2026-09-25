---
family: popcount_counter_tree
pin: {counter_primitive: full_adder_3_2}
---
# full_adder_3_2

The (3,2) counter as the reduction primitive: each full adder takes
three lines of equal weight and returns a sum line of that weight and
a carry line of double weight, inputs are grouped three at a time, and
reduction continues weight by weight until one line per weight
remains; a counter with N = 2^j - 1 inputs uses exactly N - j full
adders, and half adders fill the incomplete groups at other sizes. The
same cell is the bit-sliced carry-save adder of the Harley-Seal
software popcount.

It is the default when the counter is built from the multiplier's
cells or from bit-sliced vector logic: delay lies between
log3(N-1) + log2(N) and 2 log2(N) - 1 full-adder delays, and in AVX2
the carry-save form runs at 0.52 cycles per 64-bit word against 1.01
for the popcnt instruction once the input exceeds 4 kB. It loses to
counter_7_3 and the 6:3 stacking counter on latency at wide inputs, by
at least 30 percent in the 0.5 um comparison, and to a ROM fast adder
in the upper stages for counters under 32 inputs, where the mixed
network runs up to twice as fast. The mask decoders that need prefix
counts keep the full adder but arrange it as a radix-3 prefix network.

## references

swartzlander_1973 -> E. E. Swartzlander Jr., "Parallel Counters", IEEE Transactions on Computers, vol. C-22, no. 11, pp. 1021-1024, 1973
mula_2018 -> W. Mula, N. Kurz, D. Lemire, "Faster Population Counts Using AVX2 Instructions", The Computer Journal, vol. 61, no. 1, pp. 111-120, 2018
hilewitz_2008 -> Y. Hilewitz, R. B. Lee, "Fast Bit Gather, Bit Scatter and Bit Permutation Instructions for Commodity Microprocessors", Journal of Signal Processing Systems, 2008
lala_2001 -> P. K. Lala, "Self-Checking and Fault-Tolerant Digital Design", Morgan Kaufmann, 2001
