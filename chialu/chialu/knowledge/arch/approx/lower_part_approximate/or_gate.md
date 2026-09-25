---
family: lower_part_approximate
pin: {lower_cell: or_gate}
---
# or_gate

The lower-part OR adder (LOA): every lower sum bit is the bitwise OR
of the two operand bits, with no carry inside the lower part, and an
AND of the two most significant lower input bits supplies the carry
into the exact upper adder. The lower part therefore has no
propagation path, and the error probability depends only on the
lower width rather than on the word length.

The OR cell is the cheapest lower cell, at about 0.2 of a full-adder
cell's power per bit against 0.8 to 0.95 for the mirror-adder cells,
and it has the highest power-saving to normalized-error ratio of the
compared designs. Its error is symmetric and nearly unbiased with a
slightly negative mean, its worst case 2^(m-1), its rate 1 - (3/4)^m,
so it suits accumulation where average bias matters and the
logarithmic multipliers that need a cheap mantissa adder. It loses to
truncation on raw power, to the mirror and inexact cells when a
shaped per-cell error is needed, and to any exact lower part when
error frequency rather than magnitude is the constraint.

## references

mahdiani2010 -> H. R. Mahdiani, A. Ahmadi, S. M. Fakhraie, C. Lucas, "Bio-Inspired Imprecise Computational Blocks for Efficient VLSI Implementation of Soft-Computing Applications", IEEE Transactions on Circuits and Systems I, vol. 57, no. 4, pp. 850-862, 2010
liang2013 -> J. Liang, J. Han, F. Lombardi, "New Metrics for the Reliability of Approximate and Probabilistic Adders", IEEE Transactions on Computers, vol. 62, no. 9, pp. 1760-1771, 2013
jiang2017 -> H. Jiang, C. Liu, L. Liu, F. Lombardi, J. Han, "A Review, Classification, and Comparative Evaluation of Approximate Arithmetic Circuits", ACM Journal on Emerging Technologies in Computing Systems, vol. 13, no. 4, 2017
liu2018 -> W. Liu, J. Xu, D. Wang, C. Wang, P. Montuschi, F. Lombardi, "Design and Evaluation of Approximate Logarithmic Multipliers for Low Power Error-Tolerant Applications", IEEE Transactions on Circuits and Systems I, vol. 65, no. 9, pp. 2856-2868, 2018
jiang2020 -> H. Jiang, F. J. H. Santiago, H. Mo, L. Liu, J. Han, "Approximate Arithmetic Circuits: A Survey, Characterization, and Recent Applications", Proceedings of the IEEE, vol. 108, no. 12, pp. 2108-2135, 2020
