---
family: approximate_compressor_tree
pin: {compressor: strollo_extended}
---
# strollo_extended

The stacker-derived compressor: three simplified Boolean terms are
derived from a four-input stacker and the lowest-probability stacker
term is omitted, which gives a cell that is not input symmetric, so
partial products are assigned to x1 to x4 by their probabilities. It
is evaluated in the column-bounded C-N form, the whole-matrix C-FULL
form, and a Hybrid tree that places a low-power cell in the
low-weight columns and this cell in the high-weight columns.

The extended cell is the pick on the high-precision Pareto frontier
of the column-bounded trees, where it sits with the Lin and Ha cells,
and its Hybrid tree is the pick for signed operands: 45.3 percent
power saving at an NMED near 1.1e-2 for a signed 16-bit full-matrix
multiplier in TSMC 28 nm, against about 8.5 percent for the
column-bounded 8x8 design alone. It is one of the three cells that
keep MRED below 0.01 for both unsigned widths under full-matrix
approximation, and the Momeni-class cells are the siblings when a
larger power reduction outweighs the accuracy loss.

## references

strollo2020 -> A. G. M. Strollo, E. Napoli, D. De Caro, N. Petra, G. Di Meo, "Comparison and Extension of Approximate 4-2 Compressors for Low-Power Approximate Multipliers", IEEE Transactions on Circuits and Systems I, vol. 67, no. 9, pp. 3021-3034, 2020
