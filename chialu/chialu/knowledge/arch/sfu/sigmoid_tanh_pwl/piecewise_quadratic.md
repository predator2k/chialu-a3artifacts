---
family: sigmoid_tanh_pwl
pin: {approximation: piecewise_quadratic}
---
# piecewise_quadratic

Second-order pieces on a sign-folded domain: the active input range is
split into two sign-selected segments, each evaluated by a quadratic
chosen to saturate with zero derivative at the range edge, and inputs
outside the range give the constant 0/1 or +/-1. With the saturation
threshold L a power of two the coefficient operations become shifts, so
each evaluation costs one multiplication, one shift and one addition, or
one multiplication plus shifts and bit-level XORs.

Piecewise quadratic is the pick when one multiplier is affordable and
the error of the shift-add lines is too high: over 10^6 points in (-8,
8) the two-segment generator reaches an average error of 7.7 x 10^-4 and
a maximum of 2.2 x 10^-2 against 6.4 x 10^-3 and 1.6 x 10^-1 for Kwan's
two-piece form, with zero lookup-table bytes and zero additions in the
sign-magnitude variant. In a bit-serial implementation with a pipelined
multiplier it takes 21 or 22 machine cycles against 33 for Kwan's.
Training behaves like the exact sigmoid, with epochs and recall rates
within a few percent, so the training_absorbs_error contract is cheap
here. It loses to the shift-add and bit-mapping siblings on area and
single-cycle latency.

The library's module for sigmoid_tanh_pwl realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

kwan_1992 -> H. K. Kwan, "Simple Sigmoid-Like Activation Function Suitable for Digital Hardware Implementation", Electronics Letters, vol. 28, pp. 1379-1380, 1992
zhang_1996 -> M. Zhang, S. Vassiliadis, J. G. Delgado-Frias, "Sigmoid Generators for Neural Computing Using Piecewise Approximations", IEEE Transactions on Computers, vol. 45, no. 9, pp. 1045-1049, 1996
