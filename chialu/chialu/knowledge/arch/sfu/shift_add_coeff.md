# shift_add_coeff

Multiplierless piecewise function evaluation in which every
coefficient is a sum of a few signed powers of two, so each segment's
slope, offset or correction term is applied by shifts and additions
rather than by a multiplier. A segment index decoder, from address
bits or a comparator, selects the coefficient set for the input
range; the datapath is the same shift-add network for every segment
and for every function, and only the per-function segment sets
change. The line runs from the PLAN sigmoid with its shift-only slopes,
through the second-order segments with powers-of-two coefficients of
the 1990s sigmoid generators, to the PLAC generator and the P-SFA
blending of the 2020s.

The family trades coefficient freedom for area: restricting a slope
to one or two shifts leaves an approximation error that only more
segments, odd-symmetry folding, or a nonuniform segment placement
can recover, so the segment count and the index decoder are where
the design is tuned. PLAC makes the segmentation function-agnostic,
with a comparator-based nonuniform index and a greedy error-driven
boundary search that claims a minimal segment count for a given error
target, while P-SFA blends segment outputs by the input-distribution
statistics so the error is minimized where the activations land
rather than uniformly. The same coefficient discipline appears in
the ROM-free logarithmic converters, whose region corrections use
constants decomposed into pairs of powers of two and reach errors
below one percent without any table.

It wins in activation units and logarithm converters for neural
network accelerators at 8 to 16 bits of precision, because the
network trains through the approximation and the contract is task
accuracy rather than ulps, and because a shift-add datapath costs a
few adders where a segment multiplier costs a multiplier per lane.
It loses to table-plus-polynomial and multipartite evaluators once a
faithful or correctly rounded result is required, and to a small
multiplier once the segment count needed to hold the error exceeds
what the index decoder and coefficient store save.

The library realizes this evaluator inside the segmented-polynomial engine (`chialu/targets/rtl/families/sfu.py`: the coefficients rounded to powers of two and applied as shifts, the sign from a table).

## references

alippi_1991 -> C. Alippi, G. Storti-Gajani, "Simple Approximation of Sigmoidal Functions: Realistic Design of Digital Neural Networks Capable of Learning", IEEE International Symposium on Circuits and Systems (ISCAS), pp. 1505-1508, 1991
zhang_1996 -> M. Zhang, S. Vassiliadis, J. G. Delgado-Frias, "Sigmoid Generators for Neural Computing Using Piecewise Approximations", IEEE Transactions on Computers, vol. 45, no. 9, pp. 1045-1049, 1996
amin_1997 -> H. Amin, K. M. Curtis, B. R. Hayes-Gill, "Piecewise Linear Approximation Applied to Nonlinear Function of a Neural Network", IEE Proceedings - Circuits, Devices and Systems, vol. 144, no. 6, pp. 313-317, 1997
juang_2009 -> T.-B. Juang, S.-H. Chen, H.-J. Cheng, "A Lower Error and ROM-Free Logarithmic Converter for Digital Signal Processing Applications", IEEE Transactions on Circuits and Systems II, vol. 56, no. 12, pp. 931-935, 2009
dong_2020 -> H. Dong, M. Wang, Y. Luo, M. Zheng, M. An, Y. Ha, H. Pan, "PLAC: Piecewise Linear Approximation Computation for All Nonlinear Unary Functions", IEEE Transactions on Very Large Scale Integration (VLSI) Systems, vol. 28, no. 9, pp. 2014-2027, 2020
wei_2020 -> L. Wei, J. Cai, V. Nguyen, J. Chu, K. Wen, "P-SFA: Probability Based Sigmoid Function Approximation for Low-Complexity Hardware Implementation", Microprocessors and Microsystems, vol. 76, art. 103105, 2020
