---
family: softmax_layernorm
pin: {normalization_division: true_divider}
---
# true_divider

The straightforward normalization: each exponential is divided by the
accumulated sum in a hardware divider, which in the design on file is a
32-bit shift-and-subtract unit that produces the quotient over several
cycles in a multi-cycle pipeline, with no maximum subtraction in front
of the exponential. The reference form the alternatives are measured
against uses N dividers, one per output, and a critical path of inner
product, adder tree, exponential and division.

A true divider is the pick when the vector is short or the throughput
target is low enough that one shared sequential divider suffices and its
exactness is worth more than its latency: the EFSHA design on a Zynq
UltraScale+ ZCU106 takes 646 LUTs and 467 registers at 265 MHz for 0.73
Gbps, the fewest LUTs and the highest throughput per LUT, 1.1 Mbps/LUT,
of the compared designs, while its absolute throughput is below two of
them because the multi-cycle pipelining of the EXP and DIV modules
trades cycles for resources. It loses once outputs are many: the
log-domain sibling replaces N dividers with one LOG unit and 2N
subtractors, and the reciprocal-multiply sibling with one
piecewise-linear reciprocal and N multipliers.

The library's module for softmax_layernorm realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

hussain_2021 -> M. A. Hussain, T.-H. Tsai, "An Efficient and Fast Softmax Hardware Architecture (EFSHA) for Deep Neural Networks", IEEE International Conference on Artificial Intelligence Circuits and Systems (AICAS), pp. 1-4, 2021
yuan_2016 -> B. Yuan, "Efficient Hardware Architecture of Softmax Layer in Deep Neural Network", IEEE International System-on-Chip Conference (SOCC), pp. 323-326, 2016
