# mixed_degree

Segment-indexed polynomial evaluation in which the polynomial degree
is chosen per segment rather than fixed over the whole range: flat
regions such as saturation tails hold a constant, gently curved
regions a line, and knees of concentrated curvature a quadratic or
cubic up to the maximum degree. The segmenter decodes the segment
index, from address-bit slicing on uniform segments to a
power-of-two cascade, a hierarchy, or a range-addressable table on
nonuniform ones, and the evaluator datapath is sized by the maximum
degree, so a lower-degree segment leaves its higher coefficient
terms unused while sharing the same multipliers and adders.

The maximum degree trades multiplier count and latency against
segment count: raising the degree shrinks the coefficient table, and
segment-indexed minimax polynomials of degree 1 to 3 whose
coefficients are jointly wordlength-optimized under an explicit error
budget give faithful or exactly rounded fixed-point evaluation with
minimal ROM and multiplier width. The segmenter trades decoder logic
against segment count: boundaries that follow local curvature instead
of uniform spacing cut the segment count by orders of magnitude for
functions with concentrated nonlinearity, so log- and sqrt-like
functions drop from thousands to tens of segments, and a two-level
hierarchy with a uniform outer level and a power-of-two inner level
lets an automatic tool pick the scheme per function and precision.
The evaluator slot decides whether the highest-degree segment runs
Horner steps, parallel powers with a squarer and fused accumulation,
or multiplier-free shift-add coefficients.

The family wins on functions whose curvature is concentrated: sigmoid
and tanh, with odd symmetry and saturation tails, are served by a
three-segment piecewise-linear core plus saturation with shift-only
slopes, or by second-order segments with power-of-two coefficients,
and the network trains through the approximation, so the error
target is the learning dynamics rather than ulps. It loses to a
uniform-degree piecewise polynomial when curvature is even across the
range, because the per-segment degree buys nothing and the decoder
costs remain. The contract is faithful or exact rounding when the
coefficient set is optimized jointly against the error budget, and
looser where training absorbs the error. Execution is feed-forward.

The seed instantiates the library's generated module for this family (`chialu/targets/rtl/families/sfu.py`: 16 segments whose degree varies per segment up to `max_degree`). `python3 -m chialu.targets.rtl.families.sfu --function <fn> --format <format> --family mixed_degree --pins k=v,...` emits the module with its modeled error for a rewrite.

## references

strollo_2011 -> A. G. M. Strollo, D. De Caro, N. Petra, "Elementary Functions Hardware Implementation Using Constrained Piecewise-Polynomial Approximations", IEEE Transactions on Computers, vol. 60, no. 3, pp. 418-432, 2011
decaro_2017 -> D. De Caro, E. Napoli, D. Esposito, G. Castellano, N. Petra, A. G. M. Strollo, "Minimizing Coefficients Wordlength for Piecewise-Polynomial Hardware Function Evaluation With Exact or Faithful Rounding", IEEE Transactions on Circuits and Systems I, vol. 64, no. 5, pp. 1187-1200, 2017
lee_2003 -> D.-U. Lee, W. Luk, J. Villasenor, P. Y. K. Cheung, "Non-Uniform Segmentation for Hardware Function Evaluation", Field-Programmable Logic and Applications (FPL), LNCS 2778, pp. 796-807, 2003
lee_2009 -> D.-U. Lee, R. C. C. Cheung, W. Luk, J. D. Villasenor, "Hierarchical Segmentation for Hardware Function Evaluation", IEEE Transactions on Very Large Scale Integration (VLSI) Systems, vol. 17, no. 1, pp. 103-116, 2009
amin_1997 -> H. Amin, K. M. Curtis, B. R. Hayes-Gill, "Piecewise Linear Approximation Applied to Nonlinear Function of a Neural Network", IEE Proceedings - Circuits, Devices and Systems, vol. 144, no. 6, pp. 313-317, 1997
zhang_1996 -> M. Zhang, S. Vassiliadis, J. G. Delgado-Frias, "Sigmoid Generators for Neural Computing Using Piecewise Approximations", IEEE Transactions on Computers, vol. 45, no. 9, pp. 1045-1049, 1996
