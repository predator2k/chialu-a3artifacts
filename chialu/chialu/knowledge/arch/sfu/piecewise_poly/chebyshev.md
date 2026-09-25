---
family: piecewise_poly
pin: {basis: chebyshev}
---
# chebyshev

Each subinterval stores the coefficients of a truncated Chebyshev
series, which are then quantized and adjusted rather than used as
computed: Schulte and Swartzlander round them and move them in
coefficient-ulp steps until exhaustive evaluation over the 16- or
24-bit input gives exactly rounded results, Walters and Schulte
shorten and adjust them by bit-accurate simulation to a 1-ulp bound,
and Lee et al. transform them into segment-local coordinates before
MiniBit sizes the widths.

Chebyshev is the pick when the coefficients are the starting point of
an exhaustive or analytic adjustment rather than the final answer: the
adjusted 16-bit quadratic of Schulte and Swartzlander is 27 percent
slower and 95 percent larger than the unadjusted one, 65 ns and 39
square millimetres in 1-micron CMOS, which is the price of exact
rounding, and relaxing to one ulp saves 5 to 30 percent delay and 33
to 77 percent area. Walters and Schulte reach maximum errors within
about 1 ulp with truncated multipliers and squarers that drop 8 to 31
percent of the partial products, at one hour of 2.4 GHz Pentium 4
time for 24-bit optimization. The exhaustive adjustment does not scale
to large significands. Minimax is the sibling for generator flows
that constrain coefficients in the synthesis itself.

The library's module for piecewise_poly realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

schulte_1994 -> M. J. Schulte, E. E. Swartzlander, "Hardware Designs for Exactly Rounded Elementary Functions", IEEE Transactions on Computers, vol. 43, no. 8, pp. 964-973, 1994
walters2005 -> E. G. Walters, M. J. Schulte, "Efficient Function Approximation Using Truncated Multipliers and Squarers", 17th IEEE Symposium on Computer Arithmetic (ARITH-17), 2005
lee_2009 -> D.-U. Lee, R. C. C. Cheung, W. Luk, J. D. Villasenor, "Hierarchical Segmentation for Hardware Function Evaluation", IEEE Transactions on Very Large Scale Integration (VLSI) Systems, vol. 17, no. 1, pp. 103-116, 2009
