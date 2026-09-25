---
family: pwl
pin: {slope_encoding: signed_po2_pair}
---
# signed_po2_pair

Each slope the signed sum of two powers of two: the product with the
local coordinate becomes two shifts and one addition or subtraction,
so the evaluator is shift-add hardware with better constants than a
single power of two. Combet's four-interval log2(1+x) corrections,
Juang's two-region logarithm with slopes coupled by symmetric inverse
geometry, and Cardarilli's two-line reciprocal on [1, 2) with slopes
-0.625 and -0.3125 are the form.

It is the pick when a multiplierless evaluator must meet a stated
error: four equal segments cut the log2 error range from 0.086 to
0.014, a factor of about six over Mitchell's straight line, the
two-region converter reaches an error range of 0.045 in 2.8 ns and
5,586 square micrometres in 0.13 um, and the reciprocal stays within
2^-5 over its domain. It sits between power_of_two, which drops the
second shift and the accuracy, and canonical signed digit, whose more
accurate constants cost more shift-add terms; against plain slopes it
trades the multiplier for constants fixed at design time. More
segments halve the error again but add decision and correction
hardware.

The library's module for pwl realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

combet1965 -> M. Combet, H. Van Zonneveld, L. Verbeek, "Computation of the Base Two Logarithm of Binary Numbers", IEEE Transactions on Electronic Computers, vol. EC-14, no. 6, pp. 863-867, 1965
juang_2009 -> T.-B. Juang, S.-H. Chen, H.-J. Cheng, "A Lower Error and ROM-Free Logarithmic Converter for Digital Signal Processing Applications", IEEE Transactions on Circuits and Systems II, vol. 56, no. 12, pp. 931-935, 2009
cardarilli_2021 -> G. C. Cardarilli, L. Di Nunzio, R. Fazzolari, D. Giardino, A. Nannarelli, M. Re, S. Spano, "A Pseudo-Softmax Function for Hardware-Based High Speed Image Classification", Scientific Reports, vol. 11, 2021
