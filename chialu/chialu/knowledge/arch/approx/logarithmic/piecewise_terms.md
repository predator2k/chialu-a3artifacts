---
family: logarithmic
pin: {correction: piecewise_terms}
---
# piecewise_terms

Segment correction: the fractional range is divided into regions and a
region-dependent term is added to the logarithm sum in a single pass,
so the correction stays in the logarithmic domain and needs no second
multiplication. The divided-approximation form uses two regions
selected by three mantissa bits, and the table form adds one of 64
stored values to each logarithm sum.

Basic logarithmic designs have low accuracy, and a two-stage correction
can produce low, unbiased average error. With operand decomposition
ahead of it, the two-region form reaches 0.10 to 0.17 per cent average
error against 2.45 to 2.71 per cent for divided approximation alone,
and the table form about 0.01 per cent; the two-region form has the
lower correction overhead. Against iterative_residual the segment
terms cost fixed hardware and no extra pass, and against
near_zero_bias_coefficients they reduce the average magnitude rather
than only the bias. It is the pick when a small table or region logic
fits the area budget and the datapath must stay single-pass.

## references

jiang2020 -> H. Jiang, F. J. H. Santiago, H. Mo, L. Liu, J. Han, "Approximate Arithmetic Circuits: A Survey, Characterization, and Recent Applications", Proceedings of the IEEE, vol. 108, no. 12, pp. 2108-2135, 2020
mahalingam2006 -> V. Mahalingam, N. Ranganathan, "Improving Accuracy in Mitchell's Logarithmic Multiplication Using Operand Decomposition", IEEE Transactions on Computers, vol. 55, no. 12, pp. 1523-1535, 2006
