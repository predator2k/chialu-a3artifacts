---
family: sigmoid_tanh_pwl
pin: {approximation: probability_weighted_pwl}
---
# probability_weighted_pwl

Piecewise-linear segments allocated by input probability: the folded
positive axis is split into a near-linear region [0, 2.2), a saturation
region [2.2, 5) and a constant region beyond 5, and each region's
segment count follows the probability that a layer's neuron values fall
there, with widths set by the second derivative. Each segment computes x
/ 2^n + b through a decoder, a shifter or multiplexer and an adder;
three precomputed functions cover low, middle and high region-I
probabilities.

The probability-weighted form is the pick when the network is fixed and
inference accuracy, rather than uniform approximation error, is the
target: it deliberately allows more error in low-probability regions to
lower it where values concentrate, and with 12 segments reaches 0.0125
maximum and 0.0042 average absolute error over [-5, 5] while MNIST
accuracy comes out at 97.46% for a DNN and 99.02% for a CNN against
97.37% and 98.96% with the exact sigmoid, with weights trained on the
original function. On an Artix-7 it costs 140 LUTs, 23 flip-flops, no
DSP, 6 mW and 9.856 ns, on par with the fixed-segment designs it is
compared to. The price is a per-layer function choice derived from
profiling, and recognition accuracy does not track global error
monotonically, so the segment count is chosen by experiment.

The library's module for sigmoid_tanh_pwl realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

wei_2020 -> L. Wei, J. Cai, V. Nguyen, J. Chu, K. Wen, "P-SFA: Probability Based Sigmoid Function Approximation for Low-Complexity Hardware Implementation", Microprocessors and Microsystems, vol. 76, art. 103105, 2020
