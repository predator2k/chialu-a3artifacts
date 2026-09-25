---
family: piecewise_poly
pin: {coefficient_optimization: rounded_remez}
---
# rounded_remez

The real-valued minimax polynomial of each subinterval, computed by
Remez, is rounded coefficient by coefficient to the stored format and
used as is: Muller's sine example divides [0, pi/4] into 1, 2 or 4
equal subintervals and tabulates the degree needed for 10^-8, 6, 5
and 4, with the degree-4 absolute error between 0.367 and 0.472 x
10^-8 across the four pieces.

Rounding is the pick for a software table or a first hardware cut,
where smaller subintervals trade coefficient storage for lower degree
and less computation and the subdomain boundaries need care to keep
monotonicity; large software tables raise the cache-miss probability.
It is the baseline the joint searches measure against: Pasca's
generator follows Remez with a constrained fpminimax and a search over
neighbouring coefficient constraints and FPGA memory sweet spots,
Strollo and De Caro's constrained pairs cut ROM 30 to 50 percent at
the same accuracy, and De Caro's integer linear program shrinks
segment counts by 4 to 8 times for exact rounding. Chebyshev series
with exhaustive adjustment is the other route to exact results.

The library's module for piecewise_poly realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

muller_2016 -> J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
pasca_2011 -> B. Pasca, "High-Performance Floating-Point Computing on Reconfigurable Circuits", PhD thesis, ENS Lyon, 2011
strollo_2011 -> A. G. M. Strollo, D. De Caro, N. Petra, "Elementary Functions Hardware Implementation Using Constrained Piecewise-Polynomial Approximations", IEEE Transactions on Computers, vol. 60, no. 3, pp. 418-432, 2011
decaro_2017 -> D. De Caro, E. Napoli, D. Esposito, G. Castellano, N. Petra, A. G. M. Strollo, "Minimizing Coefficients Wordlength for Piecewise-Polynomial Hardware Function Evaluation With Exact or Faithful Rounding", IEEE Transactions on Circuits and Systems I, vol. 64, no. 5, pp. 1187-1200, 2017
