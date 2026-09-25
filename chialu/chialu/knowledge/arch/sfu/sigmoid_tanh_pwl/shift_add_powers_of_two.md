---
family: sigmoid_tanh_pwl
pin: {approximation: shift_add_powers_of_two}
---
# shift_add_powers_of_two

Piecewise-linear segments whose slopes, or whose breakpoint ordinates,
are powers of two: the sigmoid is folded about its midpoint, |x| is
classified into a few ranges, and each range evaluates a line by shifts
and additions only, so the datapath is a decoder, a shifter and an adder
with no multiplier. The Alippi form places breakpoints at consecutive
integers and picks power-of-two function values; PLAN uses four ranges
with slopes 1/4, 1/8, 1/32 and 0 and saturates beyond |x| = 5.

The power-of-two form is the pick when the activation must cost a few
dozen logic cells and one cycle: on an EP2A15 FPGA the A-law, Alippi and
PLAN approximations take 36, 36 and 39 logic elements at 58.6, 64.2 and
75.8 MHz, with maximum absolute errors of 4.90%, 1.89% and 1.89% and
average errors of 2.47%, 0.87% and 0.59% over [-8, 8). Both original
schemes keep a first derivative, so generalized-delta-rule learning
still works, though PLAN's gradient sits slightly below the sigmoid's
between 2.375 and 5 and lengthens convergence. PLAN collapses further
into direct Boolean bit mappings, 11 gate delays after the input
complement, which is the step toward the bit-level-mapping sibling; the
piecewise-quadratic sibling buys lower error with one multiplication.

The library's module for sigmoid_tanh_pwl realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

alippi_1991 -> C. Alippi, G. Storti-Gajani, "Simple Approximation of Sigmoidal Functions: Realistic Design of Digital Neural Networks Capable of Learning", IEEE International Symposium on Circuits and Systems (ISCAS), pp. 1505-1508, 1991
amin_1997 -> H. Amin, K. M. Curtis, B. R. Hayes-Gill, "Piecewise Linear Approximation Applied to Nonlinear Function of a Neural Network", IEE Proceedings - Circuits, Devices and Systems, vol. 144, no. 6, pp. 313-317, 1997
tommiska_2003 -> M. T. Tommiska, "Efficient Digital Implementation of the Sigmoid Function for Reprogrammable Logic", IEE Proceedings - Computers and Digital Techniques, vol. 150, no. 6, pp. 403-411, 2003
