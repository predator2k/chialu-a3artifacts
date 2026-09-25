---
family: lut_plus_poly
pin: {breakpoint_placement: gal_accurate_points}
---
# gal_accurate_points

Gal's accurate tables: each breakpoint X_i is moved to a nearby
machine number chosen so the tabulated function value, or the
dominant polynomial coefficient, carries a run of at
least 11 zeros or ones after bit 53, so the table's representation
error vanishes at target precision without extended arithmetic. The
argument is reduced, the nearest perturbed point is selected, one or
more accurate table values are read, and a minimax polynomial in
h = x - X_i supplies the correction.

Accurate points buy near-correct rounding from working-precision
arithmetic: the library is correctly rounded on more than 99.7
percent of tested arguments with a stated bound of 1 ulp and measured
maxima from 0.504 to 0.543 ulp, and the RS/6000 exponential with 256
such points settles 1023 of 1024 cases in a single pass, the rest
falling to a rare higher-precision fallback. Against uniform
breakpoints the costs are an expensive search per function and per
table, nearest-point indexing in place of top-bit decoding, and no
guarantee of correct rounding without wider intermediate precision.
It is the pick for a software library at target precision with a
small number of functions; hardware and multi-function coefficient
stores keep uniform placement.

The library's module for lut_plus_poly realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

gal_1991 -> S. Gal, B. Bachelis, "An Accurate Elementary Mathematical Library for the IEEE Floating Point Standard", ACM Transactions on Mathematical Software, vol. 17, no. 1, pp. 26-45, 1991
markstein_1990 -> Markstein, "Computation of Elementary Functions on the IBM RISC System/6000 Processor", IBM Journal of Research and Development, 1990
muller_2016 -> J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
