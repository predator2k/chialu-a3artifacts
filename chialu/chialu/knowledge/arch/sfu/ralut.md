# ralut

A lookup table whose entries are addressed by input ranges rather
than by slicing address bits: an index decoder, which is a comparator
tree, a priority encoder, or a cascade of power-of-two segments, maps
the input to the segment that contains it, and the entry stored for
that segment, a value or the coefficient set of a small segment
evaluator, is read out. Segment boundaries follow the local curvature
of the function instead of uniform spacing, so the table exchanges
ROM bits for index-decode logic and the segment count falls by orders
of magnitude for functions whose nonlinearity is concentrated. The
unit is feed-forward, one decode and one read per result.

The addressing choice trades decode depth against segment freedom.
Direct address bits cost nothing to decode but force uniform
segments; a power-of-two cascade admits segments that halve or double
toward a singularity with a shallow decoder; a priority encoder or a
comparator tree admits arbitrary boundaries at the price of the
priority-propagate chain or the comparator array. The boundary search
is the other lever: greedy error-driven splitting, dynamic
programming, or analytic curvature placement, each against a maximum
absolute or maximum relative error metric, and the resulting table can
be refined by splitting the worst segment, merging adjacent
low-error segments, or retargeting the error budget per segment.

The family wins for log- and sqrt-like functions, where nonuniform
segmentation drops the count from thousands of segments to tens, and
for NN accelerators that want one function-agnostic datapath with a
per-function segment set. It loses to a uniformly addressed table
when the function is smooth, because the decoder then buys nothing,
and the crossover against polynomial degree and bipartite splitting
shifts with precision and with the fabric, since FPGA block RAM and
DSP slices price ROM and multipliers differently from an ASIC. The
segment coefficient ROM is itself compressible by the table-splitting
methods, and a two-level hierarchy with uniform outer and
power-of-two inner segments is the automated form of the same idea.

The library realizes this segmenter inside the segmented-polynomial engine (`chialu/targets/rtl/families/sfu.py`: a comparator per boundary, the index as the count of boundaries at or below the argument).

## references

lee_2003 -> D.-U. Lee, W. Luk, J. Villasenor, P. Y. K. Cheung, "Non-Uniform Segmentation for Hardware Function Evaluation", Field-Programmable Logic and Applications (FPL), LNCS 2778, pp. 796-807, 2003
lee_2009 -> D.-U. Lee, R. C. C. Cheung, W. Luk, J. D. Villasenor, "Hierarchical Segmentation for Hardware Function Evaluation", IEEE Transactions on Very Large Scale Integration (VLSI) Systems, vol. 17, no. 1, pp. 103-116, 2009
hsiao_2014 -> S.-F. Hsiao, C.-S. Wen, P.-H. Wu, "Compression of Lookup Table for Piecewise Polynomial Function Evaluation", Euromicro Conference on Digital System Design (DSD), pp. 279-284, 2014
dong_2020 -> H. Dong, M. Wang, Y. Luo, M. Zheng, M. An, Y. Ha, H. Pan, "PLAC: Piecewise Linear Approximation Computation for All Nonlinear Unary Functions", IEEE Transactions on Very Large Scale Integration (VLSI) Systems, vol. 28, no. 9, pp. 2014-2027, 2020
