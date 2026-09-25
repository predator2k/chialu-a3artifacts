---
family: dynamic_segment
pin: {segment_select: dynamic_leading_one_rounded}
---
# dynamic_leading_one_rounded

Each operand is factored as N = 2^k X with Y = X - 1; t bits of each Y
are retained for the additive terms, and each multiplicative Y is
rounded to an (h+1)-bit odd midpoint by keeping h bits and appending a
1. The core computes 1 + (Y_A)_t + (Y_B)_t + (Y_A)_apx (Y_B)_apx and
shifts the result by k_A + k_B; signed operands use approximate absolute
values followed by sign restoration.

It is the pick when the design must scale to wide operands at a fixed
accuracy: the core is unchanged for a given accuracy level while the
exact partial-product count grows quadratically, so the (3,7)
configuration keeps 31 of 256 partial products at 16 bits, and the
configurations average 95% energy and 85% area improvement over an
exact 32-bit Wallace multiplier in 45-nm Nangate with mean absolute
relative error between 11% and 0.3%. Accuracy depends strongly on h,
which almost halves the error per added bit, and weakly on operand
width; t beyond h+4 adds little. The error is almost normal with
near-zero mean, and the signed absolute-value unit may reduce speed.

## references

vahdat2019 -> S. Vahdat, M. Kamal, A. Afzali-Kusha, M. Pedram, "TOSAM: An Energy-Efficient Truncation- and Rounding-Based Scalable Approximate Multiplier", IEEE Transactions on VLSI Systems, vol. 27, no. 5, pp. 1161-1173, 2019
