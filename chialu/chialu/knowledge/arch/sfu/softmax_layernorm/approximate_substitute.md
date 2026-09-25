---
family: softmax_layernorm
pin: {exp_evaluation: approximate_substitute}
---
# approximate_substitute

Pseudo-softmax: the function itself is replaced by 2^x_i / sum 2^x_k
over integer-quantized inputs, so every exponential is a floating-point
number with mantissa 1.0 whose exponent is the input, the denominator is
a binary adder tree of such numbers, and each output is the input minus
the sum's exponent with one shared reciprocal mantissa from a
piecewise-linear block. No exponential is evaluated anywhere and no
maximum is subtracted.

The substitute is the pick for classification outputs where the consumer
needs a positive, normalized distribution rather than the exact e-based
one: outputs remain positive, sum to one and follow a pseudo-Boltzmann
temperature 2^T, and on ten-bit ResNet-50, VGG and Inception outputs the
MSE against true softmax is one order of magnitude below a compared
approximation, 2.7 x 10^-4 on a corner test. An unpipelined INT8 unit
for ten inputs runs at 3.22 ns and 310 MHz in 90 nm, about 30% larger
than the fastest compared design at similar MSE. The caveats are a 9-bit
exponent that avoids overflow only for x <= 127 and fewer than 128
inputs, no encoding for zero, and serial input support left as future
work. It loses to the polynomial and LUT siblings when the e-based
values themselves are consumed.

The library's module for softmax_layernorm realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

cardarilli_2021 -> G. C. Cardarilli, L. Di Nunzio, R. Fazzolari, D. Giardino, A. Nannarelli, M. Re, S. Spano, "A Pseudo-Softmax Function for Hardware-Based High Speed Image Classification", Scientific Reports, vol. 11, 2021
