# popcount_counter_tree

Population count as a counter tree: the N input bits are grouped and
reduced by counters, a full adder turns three equal-weight lines into
a sum of weight 1 and a carry of weight 2, reduction continues weight
by weight until one line of each weight remains, and a final adder
resolves the log2(N)+1-bit count. The CDC 6600 form converts the sixty
bits in four-bit groups into fifteen three-bit counts and adds them
two at a time through four cycles on the divide unit's adder. The tree
is the structure of a multiplier's partial-product reduction, and the
Berger check-bit generator is the same circuit.

counter_primitive sets depth and cell count. A pure full-adder network
uses N - j adders for N = 2^j - 1 inputs and lies between
log3(N-1) + log2(N) and 2 log2(N) - 1 adder delays; replacing the
upper ripple stages by ROM fast adders runs up to twice as fast for
counters under 32 inputs and is impractical past 63. A 6:3 counter
built by symmetric bit stacking, with no XOR or mux on its
seven-gate critical path, is at least 30 percent faster than existing
parallel counters in 0.5 um at the cost of crossing wires, while a 7:3
counter is only slightly faster and burns more power; a 4-to-3
first-stage counter or a LUT trades cells for a lookup. tree_shape
trades the balanced pairwise tree, which recursively joins two smaller
counters with ordinary adders and suits a modular or reused-adder
build, against Wallace-style reduction by weight with the fewest
counters, which is the least-power form at every multiplier size, and
a linear chain. The prefix counts a butterfly mask decoder needs, arranged as a
radix-3 prefix network of log3(n)+2 counter stages with each count kept
modulo its stage's rotation period, are a use the unit's op set does not
carry.

The family wins as soon as the count must be exact and wide: the 6600
counts a 60-bit word in 800 ns against 2900 ns for a divide on the
same unit, and the software form, Harley-Seal bit-sliced carry-save
adders over vector registers, runs at 0.52 cycles per 64-bit word on
AVX2 against 1.01 for the popcnt instruction once the input exceeds
4 kB. It shares its tree with the multiplier when the two are not
needed at once, and its final_adder slot takes any binary adder, from
the ripple stages of the classic counters to the lookahead adder of
the 6600.

## design choices

### counter_primitive

| member | what it selects |
| --- | --- |
| `full_adder_3_2` | full adders count the bits three at a time. |
| `compressor_4_2` | 4:2 compressors. |
| `counter_7_3` | 7:3 counters. |
| `lut_rom` | a table counts each group. |

### tree_shape

| member | what it selects |
| --- | --- |
| `balanced_tree` | the group counts join in a balanced tree of adders. |
| `wallace_style` | the columns are reduced by the primitive's cells into two rows first. |
| `linear_chain` | the group counts join in a chain of adders. |

## references

swartzlander_1973 -> E. E. Swartzlander Jr., "Parallel Counters", IEEE Transactions on Computers, vol. C-22, no. 11, pp. 1021-1024, 1973
thornton_1970 -> J. E. Thornton, "Design of a Computer: The Control Data 6600", Scott, Foresman and Co., 1970
lala_2001 -> P. K. Lala, "Self-Checking and Fault-Tolerant Digital Design", Morgan Kaufmann, 2001
fritz2017 -> C. Fritz, A. T. Fam, "Fast Binary Counters Based on Symmetric Stacking", IEEE Transactions on Very Large Scale Integration (VLSI) Systems, vol. 25, 2017
hilewitz_2008 -> Y. Hilewitz, R. B. Lee, "Fast Bit Gather, Bit Scatter and Bit Permutation Instructions for Commodity Microprocessors", Journal of Signal Processing Systems, 2008
mula_2018 -> W. Mula, N. Kurz, D. Lemire, "Faster Population Counts Using AVX2 Instructions", The Computer Journal, vol. 61, no. 1, pp. 111-120, 2018
