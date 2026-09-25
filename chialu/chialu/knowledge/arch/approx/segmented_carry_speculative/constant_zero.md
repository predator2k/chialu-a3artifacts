---
family: segmented_carry_speculative
pin: {carry_in_scheme: constant_zero}
---
# constant_zero

The equal segmentation adder: the n-bit addition is divided into
parallel k-bit sub-adders whose carry inputs are fixed rather than
predicted or selected, so every inter-segment carry is dropped and the
carry path is exactly one segment. The sections need not be equal:
DSEC divides an accumulator into adders sized by the degree of
over-scaling, accumulates the ignored inter-section carries, and
repairs them in a later correction cycle.

Dropping the carry is the hardware-efficient end of the family: ESA
suits use where high error is tolerated, and segmented designs save
power and area against the carry-select designs. Carry omission
produces single-sided errors with a large bias. Against
propagate_window the segment boundary has no predictor at all, so the
error rate at equal k is the highest of the carry-in schemes, and the
correction choice decides whether that is acceptable: none for
error-tolerant DSP, or extra_cycle with accumulated carries as in
DSEC, where the segmentation pattern decides how much over-scaling
stays bounded, since 556 fails under small over-scaling while 358
remains bounded at a 50 per cent delay reduction. It is the pick for
the lowest-cost segment when the application accepts the error or an
accumulator can absorb a later correction.

## references

jiang2020 -> H. Jiang, F. J. H. Santiago, H. Mo, L. Liu, J. Han, "Approximate Arithmetic Circuits: A Survey, Characterization, and Recent Applications", Proceedings of the IEEE, vol. 108, no. 12, pp. 2108-2135, 2020
jiang2017 -> H. Jiang, C. Liu, L. Liu, F. Lombardi, J. Han, "A Review, Classification, and Comparative Evaluation of Approximate Arithmetic Circuits", ACM Journal on Emerging Technologies in Computing Systems, vol. 13, no. 4, 2017
venkatesan2011 -> R. Venkatesan, A. Agarwal, K. Roy, A. Raghunathan, "MACACO: Modeling and Analysis of Circuits for Approximate Computing", IEEE/ACM International Conference on Computer-Aided Design (ICCAD), pp. 667-673, 2011
