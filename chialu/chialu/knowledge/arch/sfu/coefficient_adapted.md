# coefficient_adapted

Polynomial evaluation after a one-time coefficient adaptation: the
polynomial is transformed offline into a shift c and factor parameters
alpha_i and beta_i, and evaluated as y = x + c, w = y^2, then a nested
sequence of factors in w - alpha_i, so a degree-n polynomial costs at
most ceil(n/2) + 2 multiplications and n additions, against n
multiplications and n additions for Horner's rule.

The scheme trades offline work for multiplications: the adapted
parameters come from solving nonlinear coefficient equations once per
polynomial, and the saving appears only at sufficiently high degree,
6 multiplications against Horner's 8 at degree 8. It is a rearranged
feed-forward evaluator, so it fills the evaluator slot of single_poly,
piecewise_poly, lut_plus_poly and mixed_degree beside horner, estrin,
parallel_monomial and factored. It declares no design choices of its
own; the degree, the basis, the coefficient encoding and the guard
bits come from the family that owns the slot.

It is the pick when the datapath is multiplier-bound and the degree is
high enough for the count to drop, for instance one polynomial of high
degree over the reduced domain. horner keeps the minimum operation
count at low degree, where the adaptation saves nothing; estrin buys
depth rather than operation count; shift_add_coeff removes the
multipliers altogether where the coefficients can be quantized to
powers of two; and factored is the single-rectangular-multiplier
rearrangement of the second-order case.

The library realizes this evaluator inside the segmented-polynomial engine (`chialu/targets/rtl/families/sfu.py`: Knuth's adapted forms for degrees 3 and 4 with the per-segment constants in tables; the other degrees fall back to Horner).

## references

muller_2016 -> J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
