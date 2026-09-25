---
family: nonuniform
pin: {addressing: comparator_tree}
---
# comparator_tree

Segment addressing over arbitrary breakpoints: the input is compared
against the stored boundaries and the comparison results are encoded
into the segment index, so any set of endpoints the boundary search
produces can be used directly. The piecewise-linear generator feeds
it segments whose endpoints are distinct discrete input points found
by a bisection window, and the sigmoid approximator's input decoder
selects the slope and offset of each interval the same way.

It is the pick when the boundary search is free to place endpoints
anywhere, as the bisection and curvature methods do, and the segment
count is small enough that one comparator per boundary is
affordable, which is the case for the 12- to 16-segment activation
functions. It loses to power_of_two_cascade when the segment count
is large or the boundaries can be snapped to a power-of-two grid,
since the cascade's leading-digit detection costs far less than a
tree of wide comparators.

The library's module for nonuniform realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

dong_2020 -> H. Dong, M. Wang, Y. Luo, M. Zheng, M. An, Y. Ha, H. Pan, "PLAC: Piecewise Linear Approximation Computation for All Nonlinear Unary Functions", IEEE Transactions on Very Large Scale Integration (VLSI) Systems, vol. 28, no. 9, pp. 2014-2027, 2020
wei_2020 -> L. Wei, J. Cai, V. Nguyen, J. Chu, K. Wen, "P-SFA: Probability Based Sigmoid Function Approximation for Low-Complexity Hardware Implementation", Microprocessors and Microsystems, vol. 76, art. 103105, 2020
