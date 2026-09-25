---
family: redundant_cordic
pin: {scale_factor_fix: branching}
---
# branching

Branching CORDIC: two conventional CORDIC modules run in parallel,
and whenever the inspected residual window cannot determine the sign
of the remaining angle, one module tries d = +1 and the other d = -1.
A later residual that is again ambiguous identifies which branch was
correct, so two modules suffice regardless of how many branchings
occur, and the direction digit never needs the zero value that would
break the constant scale factor.

It is the pick when the iteration count and the constant scale
factor of conventional CORDIC must both be kept and silicon for a
second module is available: each branch residual stays below
3 x 2^-n+1 and at least one branch remains within the conventional
tail bound, with a 3-signed-digit window reducing to a value in
[-7, 7] in the radix-2 signed-digit form. Branching only happens
when the window is undecided. Double rotation and correcting
iterations win when area is the constraint, because they keep one
datapath and pay in extensions instead of a duplicated module.

The iterations run over cycles here; the family is an exception (`redundant.EXCEPTIONS`).

## references

muller_2016 -> J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
meher_2009 -> P. K. Meher, J. Valls, T.-B. Juang, K. Sridharan, K. Maharatna, "50 Years of CORDIC: Algorithms, Architectures, and Applications", IEEE Transactions on Circuits and Systems I, vol. 56, no. 9, pp. 1893-1907, 2009
