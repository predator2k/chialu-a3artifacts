---
family: approximate_compressor_tree
pin: {error_recovery: configurable_recovery}
---
# configurable_recovery

Error correction attached to the inexact tree: the 4x4 base block's
4:2 counter maps the all-ones input to 10 rather than 100 (a 2:1
multiplexer replaces an XOR), so the block errs only when both 4-bit
operands are all ones, and an error-detection-and-correction stage
detects that case with an AND gate and repairs product bits 5 and 6
with OR/NOR gates. Larger multipliers combine the blocks recursively and
finish with a speculative adder whose correction takes an extra
cycle.

Configurable recovery is the pick when the error rate must be
tunable after the fact rather than fixed by the cell: the recursive
multipliers average 9.8 percent less delay and 10.74 percent less
power than the exact Wallace multiplier over 4 to 32 bits in TSMC
0.18 um at error rates from 0.2 to 13.76 percent, and the survey
classes it with the configurable error-accumulation stages that sum
error bits with OR gates or adders. The recovery logic costs area and
a cycle on the final adder, and its multiplier has 44 percent higher
PDP than the encoded-compressor design at the same MRED, so a fixed
accuracy target picks no recovery.

## references

lin2013 -> C.-H. Lin, I.-C. Lin, "High Accuracy Approximate Multiplier with Error Correction", IEEE International Conference on Computer Design (ICCD), pp. 33-38, 2013
jiang2020 -> H. Jiang, F. J. H. Santiago, H. Mo, L. Liu, J. Han, "Approximate Arithmetic Circuits: A Survey, Characterization, and Recent Applications", Proceedings of the IEEE, vol. 108, no. 12, pp. 2108-2135, 2020
ansari2018 -> M. S. Ansari, H. Jiang, B. F. Cockburn, J. Han, "Low-Power Approximate Multipliers Using Encoded Partial Products and Approximate Compressors", IEEE Journal on Emerging and Selected Topics in Circuits and Systems, vol. 8, no. 3, pp. 404-416, 2018
