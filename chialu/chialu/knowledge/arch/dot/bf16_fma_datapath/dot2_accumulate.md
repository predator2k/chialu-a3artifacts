---
family: bf16_fma_datapath
pin: {op_shape: dot2_accumulate}
---
# dot2_accumulate

Arm's BFDOT: each 32-bit lane forms two BF16 products with 8-bit
integer multipliers, whose 16-bit significand products are exact,
adds the pair in a reduced-area FP25 adder that rounds to FP32, and
adds that pair sum to an FP32 accumulator. The operation is chained
rather than fused, uses Round-Odd, flushes subnormal inputs and
results to zero, returns a default NaN and raises no IEEE flags;
BFMMLA composes two BFDOTs into a 2x4 by 4x2 matrix multiply into a
2x2 binary32 result.

The pair-sum shape is the pick for inference and training vector
units where accumulator latency and area matter more than IEEE
behaviour: pairing the products before accumulation shortens the
accumulator loop and reduces accumulated rounding error by about 0.1
ulp on average, the tiny multiplications and the binary32 accumulation
each take about half a cycle, and BFMMLA reaches 16 bfloat16
multiplications per 128 bits of datapath per cycle. With every
simplification the block is 65 percent smaller than a fully IEEE
compliant one. Inference accuracy on Inception, ResNet and DeepSpeech
matches BF16 round-to-nearest to within 0.00002. The scalar FMA shape
instead feeds BF16 operands as shortened FP32 values through a
standard FMA, which keeps the product exact but accumulates one
product per operation.

The library realizes this choice as a pin of the generated bf16_fma_datapath module (`chialu/targets/rtl/families/dot.py`); the family card names the construction.

## references

burgess_2019 -> N. Burgess, J. Milanovic, N. Stephens, K. Monachopoulos, D. Mansell, "Bfloat16 Processing for Neural Networks", ARITH-26, pp. 88-91, 2019
lutz_2019 -> D. R. Lutz, "ARM Floating Point 2019: Latency, Area, Power", 26th IEEE Symposium on Computer Arithmetic, 2019
henry_2019 -> G. Henry, P. T. P. Tang, A. Heinecke, "Leveraging the bfloat16 Artificial Intelligence Datatype For Higher-Precision Computations", ARITH-26, pp. 69-76, 2019
