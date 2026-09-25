---
family: bf16_fma_datapath
pin: {rounding_mode: round_to_odd}
---
# round_to_odd

Round-Odd as the only rounding mode of the BF16 dot product: the
FP25 pair sum that rounds to FP32 and the FP32 accumulate both use
it, so the datapath drops the four IEEE-mandated modes and their
selection logic, alongside flush-to-zero subnormals, default NaN and
no exception flags. Burgess
reports an RO-only BFDOT2 about 25 percent smaller than one with all
four IEEE modes, and about 15 percent more saved when subnormals are
flushed instead of processed in hardware.

Round-Odd is the pick when area is the target and the accumulation is
long: it is unbiased, although each rounding carries about twice the
error of round-to-nearest, which showed as about 1 ulp more over 1000
trials of 18432 FP25 values accumulated into FP32, mitigated by 0.1
ulp when the values are first added in pairs. On extracted DeepSpeech
data 99.9676 percent of final BF16 results were identical to the
round-to-nearest forward order, 0.0309 percent differed by one bit
and 0.0009 percent by two, and Inception, ResNet and DeepSpeech
inference scores matched round-to-nearest to within 0.00002. Rare
late cancellation can expose a larger relative error in the final
BF16 result. Round-to-nearest-even remains the mode of the BF16
training study that reports parity with FP32 on GEMM with FP32
accumulation.

The library realizes this choice as a pin of the generated bf16_fma_datapath module (`chialu/targets/rtl/families/dot.py`); the family card names the construction.

## references

burgess_2019 -> N. Burgess, J. Milanovic, N. Stephens, K. Monachopoulos, D. Mansell, "Bfloat16 Processing for Neural Networks", ARITH-26, pp. 88-91, 2019
kalamkar_2019 -> D. Kalamkar, D. Mudigere, N. Mellempudi, D. Das, K. Banerjee, et al., "A Study of BFLOAT16 for Deep Learning Training", arXiv:1905.12322, 2019
