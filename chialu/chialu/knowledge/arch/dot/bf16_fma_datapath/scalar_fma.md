---
family: bf16_fma_datapath
pin: {op_shape: scalar_fma}
---
# scalar_fma

A conventional FP32 fused multiply-add that accepts BF16 operands as
shortened FP32 values: the 8-bit significands multiply into a 16-bit
product that is exact whenever its exponent stays in range, and the
24-bit FP32 accumulator preserves the whole product before the add.
Because BF16 keeps the FP32 exponent range the multiplier shrinks to
an 8-bit array, and repeated invocations over the BF16 components of
a split FP32 value compute partial inner products for higher
precision.

The scalar shape is the pick when a BF16 product must land in an
existing FMA pipeline or when multi-word composition is the goal:
Henry, Tang and Heinecke represent an FP32 value by one, two or three
BF16 components and accumulate the partial inner products between
components in FP32, with a first-order multiplier area of 64 units
against 576 for FP32, roughly 10 times smaller, and a projected 8 to
32 times FP32 throughput on systolic hardware. The reported numbers
are projections, since no bare-metal BF16 hardware was available to
measure. The dot2 shape instead pairs two products in an FP25 adder
before the FP32 accumulate, which reduces accumulator latency and
accumulated rounding error, but fixes the non-IEEE handling of BFDOT
in the datapath.

The library realizes this choice as a pin of the generated bf16_fma_datapath module (`chialu/targets/rtl/families/dot.py`); the family card names the construction.

## references

henry_2019 -> G. Henry, P. T. P. Tang, A. Heinecke, "Leveraging the bfloat16 Artificial Intelligence Datatype For Higher-Precision Computations", ARITH-26, pp. 69-76, 2019
burgess_2019 -> N. Burgess, J. Milanovic, N. Stephens, K. Monachopoulos, D. Mansell, "Bfloat16 Processing for Neural Networks", ARITH-26, pp. 88-91, 2019
