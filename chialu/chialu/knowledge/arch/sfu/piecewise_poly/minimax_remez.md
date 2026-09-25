---
family: piecewise_poly
pin: {basis: minimax_remez}
---
# minimax_remez

Each subinterval gets the polynomial that minimizes the maximum
error over it, computed by Remez or, with coefficient constraints, by
Sollya's fpminimax: for sin on [0, pi/4] at 10^-8 absolute error one
polynomial needs degree 6, two equal subintervals degree 5 and four
degree 4, with the degree-4 error at 0.37 to 0.47 x 10^-8 per piece.
The FloPoCo generator splits into 2^k uniform pieces, runs fpminimax
per piece and shares one evaluator sized for the worst-case
coefficient widths.

Minimax is the default basis of the hardware generators because it
buys the lowest degree for a worst-case bound, and the joint search
over coefficient wordlengths that this family exists for starts from
it: Pineiro's quadratic interpolator, Strollo and De Caro's
constrained pairs and De Caro's integer linear program all minimize
sampled maximum error over minimax-shaped pieces. Detrey and de
Dinechin evaluate a minimax polynomial per piece with developed terms
in parallel under a faithful budget, finding degree 2 optimal up to
16 bits and degree 3 at 24. Chebyshev coefficients are the sibling
for designs that adjust coefficients exhaustively afterwards or
transform them into segment-local coordinates. Rounding a real-valued
Remez polynomial to the lattice is the rounded_remez optimization;
the constrained fpminimax plus neighbouring-width search recovers what
that rounding loses.

The library's module for piecewise_poly realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

muller_2016 -> J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
pasca_2011 -> B. Pasca, "High-Performance Floating-Point Computing on Reconfigurable Circuits", PhD thesis, ENS Lyon, 2011
detrey_2005 -> J. Detrey, F. de Dinechin, "Table-Based Polynomials for Fast Hardware Function Evaluation", IEEE International Conference on Application-Specific Systems, Architectures and Processors (ASAP), pp. 328-333, 2005
pineiro_2005 -> J.-A. Pineiro, S. F. Oberman, J.-M. Muller, J. D. Bruguera, "High-Speed Function Approximation Using a Minimax Quadratic Interpolator", IEEE Transactions on Computers, vol. 54, no. 3, pp. 304-318, 2005
strollo_2011 -> A. G. M. Strollo, D. De Caro, N. Petra, "Elementary Functions Hardware Implementation Using Constrained Piecewise-Polynomial Approximations", IEEE Transactions on Computers, vol. 60, no. 3, pp. 418-432, 2011
