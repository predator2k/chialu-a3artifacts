---
family: pwl
pin: {segmentation: uniform}
---
# uniform

Segments of equal width: the leading input bits are the segment
address and the remaining bits the local coordinate, so the segmenter
is a wire split, the coefficient table is indexed directly, and the
local coordinate needs no subtraction. Combet's four equal intervals of
log2(1+x), Juang's two regions split at the first fractional bit, and
the four-segment fractional-part unit of Softermax are the form.

It is the pick whenever the function bends evenly or the decode must
cost nothing: the segment select is free, the table is dense, and for
cos(2 pi x) nonuniform segmentation saves only slightly. It loses to
nonuniform on segment count for functions with exponential behaviour,
where the same error takes many more equal segments, and eight
nonuniform segments preserve a network's accuracy where uniform
interpolation needs more breakpoints. Doubling the equal segments
roughly halves the error range at the cost of more decision and
correction hardware, and a fixed-width MAC on the local coordinate
keeps faithful rounding when its own error is folded into the bound.

The library's module for pwl realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

combet1965 -> M. Combet, H. Van Zonneveld, L. Verbeek, "Computation of the Base Two Logarithm of Binary Numbers", IEEE Transactions on Electronic Computers, vol. EC-14, no. 6, pp. 863-867, 1965
juang_2009 -> T.-B. Juang, S.-H. Chen, H.-J. Cheng, "A Lower Error and ROM-Free Logarithmic Converter for Digital Signal Processing Applications", IEEE Transactions on Circuits and Systems II, vol. 56, no. 12, pp. 931-935, 2009
decaro2013 -> D. De Caro, N. Petra, A. G. M. Strollo, F. Tessitore, E. Napoli, "Fixed-Width Multipliers and Multipliers-Accumulators with Min-Max Approximation Error", IEEE Transactions on Circuits and Systems I, vol. 60, no. 9, pp. 2375-2388, 2013
lee_2003 -> D.-U. Lee, W. Luk, J. Villasenor, P. Y. K. Cheung, "Non-Uniform Segmentation for Hardware Function Evaluation", Field-Programmable Logic and Applications (FPL), LNCS 2778, pp. 796-807, 2003
stevens_2021 -> J. R. Stevens, R. Venkatesan, S. Dai, B. Khailany, A. Raghunathan, "Softermax: Hardware/Software Co-Design of an Efficient Softmax for Transformers", ACM/IEEE Design Automation Conference (DAC), pp. 469-474, 2021
