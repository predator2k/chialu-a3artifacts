---
family: segmented_carry_speculative
pin: {carry_in_scheme: propagate_window}
---
# propagate_window

Each sub-adder's carry-in is predicted from a window of k preceding
operand bits rather than from the full lower chain: the ACA's
overlapping 2k-bit submodules each emit k result bits and share k
operand bits with their neighbour, the ETAII carry generator reads
only the preceding block, and GeAr generalises both with L=R+P
sub-adders that commit R result bits from P prediction bits. The
prediction fails only for a propagate chain longer than the window,
which bounds the carry path.

The window sets the error rate against the clock: the 16-bit ACA in
TSMC 65GP passes 55.3, 82.8, 94.0 and 98.1 per cent of random cycles
at k=2, 3, 4 and 5 with minimum periods from 180 to 230 ps. Errors
from a missed carry are single-sided and carry a large bias, and
ETAII, ACAA and SCSA have identical error characteristics at equal k.
Predicting from two preceding block carry-outs with a skip mux fails
only for chains longer than 2k and reaches 0.18 per cent error rate
at n=16, k=4. Against carry_select_speculation, which duplicates
paths, propagate_window is the segmented, power- and area-saving
scheme; against constant_zero it buys a predictor for a far lower
error rate. It is the pick when the error rate at the affordable
window is tolerable or a correction choice follows.

## references

kahng_kang2012 -> A. B. Kahng, S. Kang, "Accuracy-Configurable Adder for Approximate Arithmetic Designs", 49th Design Automation Conference (DAC), pp. 820-825, 2012
shafique2015 -> M. Shafique, W. Ahmad, R. Hafiz, J. Henkel, "A Low Latency Generic Accuracy Configurable Adder", 52nd Design Automation Conference (DAC), 2015
kim2013 -> Y. Kim, Y. Zhang, P. Li, "An Energy Efficient Approximate Adder with Carry Skip for Error Resilient Neuromorphic VLSI Systems", IEEE/ACM International Conference on Computer-Aided Design (ICCAD), pp. 130-137, 2013
jiang2017 -> H. Jiang, C. Liu, L. Liu, F. Lombardi, J. Han, "A Review, Classification, and Comparative Evaluation of Approximate Arithmetic Circuits", ACM Journal on Emerging Technologies in Computing Systems, vol. 13, no. 4, 2017
jiang2020 -> H. Jiang, F. J. H. Santiago, H. Mo, L. Liu, J. Han, "Approximate Arithmetic Circuits: A Survey, Characterization, and Recent Applications", Proceedings of the IEEE, vol. 108, no. 12, pp. 2108-2135, 2020
