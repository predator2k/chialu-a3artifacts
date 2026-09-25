---
family: approximate_compressor
pin: {technique: underdesigned_pp_block}
---
# underdesigned_pp_block

A partial-product block with a simplified truth table: an unsigned 9
by 9 multiplier is partitioned into nine 3 by 3 multipliers whose
shifted 6-bit partial results are summed, and the approximate 3 by 3
block changes six of its 64 truth-table outputs to simplify its four
output functions. Signed operation wraps the unsigned core: the
operand signs are extracted, the operands are converted to 2's
complement, the unsigned product is formed, and the sign XOR
conditionally complements the result.

The underdesigned block trades a bounded per-tile error for
cell-level savings: the 3 by 3 tile has an error distance below 8, an
error rate of 9.375 percent and a mean error distance of 0.5, and in
the ASAP-7nm library it cuts area by 31 percent, power by 37 percent
and delay by 42 percent against the exact 3 by 3 multiplier. At the
application level a 20-order adaptive FIR filter loses 1.03 dB of
SNR, LeNet on MNIST loses no accuracy and AlexNet on CIFAR10 loses
0.31 percent; no worst-case 9 by 9 error bound is given, errors are smaller for small operands because
the 9 by 9 error distribution is nonuniform, and DNN retraining can
compensate. It is the pick for a multiplier already tiled into small
partial-product blocks in an error-tolerant pipeline; the
configurable error-recovery tree instead keeps an exact final adder
and a tunable error.

## references

dai_2021 -> H. Dai, Z. Liu, S. Lu, H. Zhou, S. Rasoulinezhad, P. H. W. Leong, "APIR-DSP: An Approximate PIR-DSP Architecture for Error-Tolerant Applications", International Conference on Field-Programmable Technology (ICFPT), 2021
