---
family: single_poly
pin: {basis: chebyshev}
---
# chebyshev

The orthogonal-projection polynomial: the function is expanded in
Chebyshev polynomials over the reduced interval and truncated at the
chosen degree, which is the least-squares approximation under the
Chebyshev weight and needs no iteration, only the projection integrals.
Its error is spread across the interval rather than concentrated at one
end, and for elementary functions it trails the minimax polynomial of
the same degree by at most one bit.

Chebyshev is the pick when a near-minimax polynomial is wanted without
running the Remez iteration, or as the starting point that Remez
refines: at degree 2 for exp on [-1, 1] the maximum error is 0.050
against 0.045 for minimax, 0.081 for the Legendre projection and 0.218
for Taylor, and the one-bit gap to minimax holds across the elementary
functions, though for a non-smooth target such as |x| the gap widens to
0.2122 against 0.125. In coefficient-constrained synthesis the Chebyshev
bound also yields a candidate set, simpler to derive but usually far
larger than the polytope method's, 330 candidates against 1 in one
example. It loses to minimax only by that last bit and to Taylor only
when the interval is tiny.

The library's module for single_poly realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

muller_2016 -> J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
brisebarre_2006 -> N. Brisebarre, J.-M. Muller, A. Tisserand, "Computing Machine-Efficient Polynomial Approximations", ACM Transactions on Mathematical Software, vol. 32, no. 2, pp. 236-256, 2006
