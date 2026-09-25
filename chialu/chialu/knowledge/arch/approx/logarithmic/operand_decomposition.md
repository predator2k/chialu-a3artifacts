---
family: logarithmic
pin: {correction: operand_decomposition}
---
# operand_decomposition

The operand pair is decomposed into pairs whose
fractional-logarithm sums produce fewer carryovers, each pair goes
through the base Mitchell multiplication, and the partial results are
summed; no correction term is added to the logarithm sum itself. The
decomposition can precede a separate correction: OD-DA applies a
two-region divided approximation, OD-TCV adds one of 64 table values
to each logarithm sum, and OD-MEC applies Mitchell's product
correction to each decomposed multiplication.

Decomposition alone brings the average error from 3.88 to 2.1 per cent
on 32-bit random operands and raises the share of products within 1
per cent from 21 to 45 per cent, but it does not generally reduce the
maximum possible error. Of the composed forms, OD-DA has the lowest
correction overhead while OD-TCV and OD-MEC reach the lowest average
error, about 0.02 to 0.03 per cent in 0.7 um CMOS. Small convolution
weights can zero one decomposed operand, so only one Mitchell
multiplication is then needed. It is the pick for DSP work judged on
average error with a single-pass datapath; iterative_residual also
reduces the worst case but at cascaded hardware, and
near_zero_bias_coefficients targets the bias rather than the average
magnitude.

## references

mahalingam2006 -> V. Mahalingam, N. Ranganathan, "Improving Accuracy in Mitchell's Logarithmic Multiplication Using Operand Decomposition", IEEE Transactions on Computers, vol. 55, no. 12, pp. 1523-1535, 2006
