---
family: pwl
pin: {slope_encoding: power_of_two}
---
# power_of_two

Every segment slope a single power of two: the multiply by c1 becomes
a right shift by a per-segment count and the evaluation is a shift and
an add. In the PLAN sigmoid the positive-domain slopes 0.25, 0.125,
0.03125 and 0 over the breakpoints 1, 2.375 and 5 let the hardware map
input bits straight to output bits, removing the adder as well;
Alippi's integer-breakpoint sigmoid uses the integer part of the input
as both segment index and shift count.

It is the pick where a multiplier is unaffordable and the function is
an activation whose exact shape matters less than its continuity: the
direct-bit-mapping PLAN evaluates in 11 gate delays with one
multiplier and one addition removed per interpolation, and the
continuous integer-breakpoint form still permits gradient-descent
learning. The price is that the slopes are no longer free, so the fit
is set by the nearest power of two rather than by the minimax line,
and neither design reports an error bound; signed_po2_pair recovers
accuracy with a second shift term, and plain slopes with a fixed-width
MAC are the route to a stated bound.

The library's module for pwl realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

amin_1997 -> H. Amin, K. M. Curtis, B. R. Hayes-Gill, "Piecewise Linear Approximation Applied to Nonlinear Function of a Neural Network", IEE Proceedings - Circuits, Devices and Systems, vol. 144, no. 6, pp. 313-317, 1997
alippi_1991 -> C. Alippi, G. Storti-Gajani, "Simple Approximation of Sigmoidal Functions: Realistic Design of Digital Neural Networks Capable of Learning", IEEE International Symposium on Circuits and Systems (ISCAS), pp. 1505-1508, 1991
