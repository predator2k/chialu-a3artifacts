# power_of_two

Segmentation with boundaries at powers of two: the input interval is
cut into segments whose widths halve toward the region of concentrated
curvature, so the boundaries sit at 2^-k and the segment index is the
position of the argument's leading one. A count-leading-zeros or
priority encoder decodes that index, replacing the address-bit slicing
of uniform segmentation, and the bits below the leading one address
the segment's coefficients (degree 1 to 3) in the coefficient ROM.
Functions shaped like the logarithm or the square root drop from
thousands of uniform segments to tens of power-of-two segments at the
same error budget.

The segmentation choice exchanges ROM for index-decode logic. Uniform
spacing needs no decoder but sets the segment count by the worst local
curvature; power-of-two spacing spends a leading-zero count and an
offset shift to cut the coefficient store by orders of magnitude on
functions whose nonlinearity concentrates at one end of the interval;
boundaries placed by a greedy error-driven or dynamic-programming
search reach the minimum segment count for any curvature but pay a
comparator per boundary in a comparator tree. The hierarchical form
nests a power-of-two inner split inside a uniform outer split, and an
automatic tool picks the hierarchy per function and precision, with
degree 1 or 2 inside each segment. The coefficient ROM behind the
index remains compressible by the bipartite and multipartite methods.

The segment count then follows the error metric, maximum absolute or
maximum relative, and the rounding contract, faithful or exact, is
reached by optimizing the coefficient wordlengths of all segments
jointly under the budget. The neighbours are the mutations: splitting
the worst segment or merging adjacent low-error ones moves toward
error-driven boundaries, and replacing a direct index with the
power-of-two cascade moves toward this family. Where the crossover
lies shifts with precision and fabric, since a ROM is cheap in FPGA
block RAM and a decoder is cheap in an ASIC. The oldest instance is a
piecewise-linear sigmoid over power-of-two breakpoints where training
absorbs the approximation error; the current one is a function-agnostic
piecewise-linear generator for neural accelerators that shares one
datapath across per-function segment sets.

The library realizes this segmenter inside the segmented-polynomial engine (`chialu/targets/rtl/families/sfu.py`: the leading-one position selects the segment, the bits below it are the local variable).

## references

lee_2003 -> D.-U. Lee, W. Luk, J. Villasenor, P. Y. K. Cheung, "Non-Uniform Segmentation for Hardware Function Evaluation", Field-Programmable Logic and Applications (FPL), LNCS 2778, pp. 796-807, 2003
lee_2009 -> D.-U. Lee, R. C. C. Cheung, W. Luk, J. D. Villasenor, "Hierarchical Segmentation for Hardware Function Evaluation", IEEE Transactions on Very Large Scale Integration (VLSI) Systems, vol. 17, no. 1, pp. 103-116, 2009
dong_2020 -> H. Dong, M. Wang, Y. Luo, M. Zheng, M. An, Y. Ha, H. Pan, "PLAC: Piecewise Linear Approximation Computation for All Nonlinear Unary Functions", IEEE Transactions on Very Large Scale Integration (VLSI) Systems, vol. 28, no. 9, pp. 2014-2027, 2020
hsiao_2014 -> S.-F. Hsiao, C.-S. Wen, P.-H. Wu, "Compression of Lookup Table for Piecewise Polynomial Function Evaluation", Euromicro Conference on Digital System Design (DSD), pp. 279-284, 2014
alippi_1991 -> C. Alippi, G. Storti-Gajani, "Simple Approximation of Sigmoidal Functions: Realistic Design of Digital Neural Networks Capable of Learning", IEEE International Symposium on Circuits and Systems (ISCAS), pp. 1505-1508, 1991
