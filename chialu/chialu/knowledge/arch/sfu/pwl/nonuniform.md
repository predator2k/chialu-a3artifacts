---
family: pwl
pin: {segmentation: nonuniform}
---
# nonuniform

Segments sized to the curvature: breakpoints are placed where the
function bends, the segmenter compares the input with them, seven
parallel subtractors and a priority encoder for eight segments, a
cascade of power-of-two address ranges, or a comparator tree, and the
selected index reads the segment's slope and intercept. PLAC chooses
each segment as the widest window that meets a per-segment error bound
by bisection, with nonoverlapping discrete endpoints.

It is the pick for highly nonlinear functions with exponential
behaviour, where it gives the largest segment-count saving:
sqrt(-ln x) takes 59 segments for 8 output bits, and the
error-flattened PLAC segmentation of log2(1+x) needs one segment fewer
than a hand segmentation for 2.8 percent less area at equal delay in
65 nm, and up to 35 percent less than earlier designs. The costs are
the breakpoint comparators or address cascade in place of a wire split
and the endpoint storage, which grows with the segment count, so for a
gently curved function such as cos(2 pi x) uniform segmentation is
almost as good. The PLAN sigmoid keeps eight nonuniform segments whose
slopes are powers of two, so the multiply disappears as well.

The library's module for pwl realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

lee_2003 -> D.-U. Lee, W. Luk, J. Villasenor, P. Y. K. Cheung, "Non-Uniform Segmentation for Hardware Function Evaluation", Field-Programmable Logic and Applications (FPL), LNCS 2778, pp. 796-807, 2003
dong_2020 -> H. Dong, M. Wang, Y. Luo, M. Zheng, M. An, Y. Ha, H. Pan, "PLAC: Piecewise Linear Approximation Computation for All Nonlinear Unary Functions", IEEE Transactions on Very Large Scale Integration (VLSI) Systems, vol. 28, no. 9, pp. 2014-2027, 2020
koca_2025 -> N. A. Koca, A. T. Do, C. H. Chang, "Accuracy-Preserving Layer Normalization Approximations for Efficient Transformer Hardware Accelerators", IEEE International Symposium on Circuits and Systems (ISCAS), pp. 1-5, 2025
amin_1997 -> H. Amin, K. M. Curtis, B. R. Hayes-Gill, "Piecewise Linear Approximation Applied to Nonlinear Function of a Neural Network", IEE Proceedings - Circuits, Devices and Systems, vol. 144, no. 6, pp. 313-317, 1997
