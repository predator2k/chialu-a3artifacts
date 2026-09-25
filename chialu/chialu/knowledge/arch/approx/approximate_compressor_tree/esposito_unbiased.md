---
family: approximate_compressor_tree
pin: {compressor: esposito_unbiased}
---
# esposito_unbiased

Carry-free j-input compressors: a cell produces ceil(j/2) outputs
of the weight of its inputs and no carry outputs, and AND/OR
recoding exposes low-probability three-product terms, discarded
under the assumption of independent uniform operand bits.
Arities run from 2/1 through 6/3 (error probabilities 1/16, 1/64 and
13/256 for 2/1, 3/2 and 4/2), and an allocation algorithm compresses
the low columns maximally and inserts only enough approximate cells
above them to reach the next height.

The carry-free cells are the pick when the approximation must be
placed by column height rather than by a fixed region: the one-step
full version averages about 9 percent less delay, 32 percent less
area and 23 percent less power than the exact multiplier over 8- to
20-bit operands in TSMC 40 nm behind a Kogge-Stone final adder, and
the truncated version leads the power-accuracy trade in the survey
comparison. Compressor errors under-estimate the exact sum, and the
probability model assumes uniform operand bits, so Booth-encoded
partial products with different probabilities need cells of their
own; the encoded cells are the sibling for correlated inputs.

## references

esposito2018 -> D. Esposito, A. G. M. Strollo, E. Napoli, D. De Caro, N. Petra, "Approximate Multipliers Based on New Approximate Compressors", IEEE Transactions on Circuits and Systems I, vol. 65, no. 12, pp. 4169-4182, 2018
jiang2020 -> H. Jiang, F. J. H. Santiago, H. Mo, L. Liu, J. Han, "Approximate Arithmetic Circuits: A Survey, Characterization, and Recent Applications", Proceedings of the IEEE, vol. 108, no. 12, pp. 2108-2135, 2020
