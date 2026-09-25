---
family: fp8_training_datapath
pin: {op_shape: dot2_accumulate}
---
# dot2_accumulate

The hfp8 FMMA instruction forms two fp8 products and adds them with an
addend: the three terms are aligned to the exponent of the larger
product, the smaller product is shifted by the computed product-exponent
difference, and the fp16 result leaves through the adder shared with the
fp16 path. Both hfp8 formats first convert to one unified fp9 internal
representation, so a single multiplier and alignment structure serves
the forward E4M3 and the backward E5M2 operands.

The two-product shape doubles the fp8 work per issue over a scalar FMA
on the same adder: the 7 nm four-core AI chip reports 2x the fp16-mode
performance at the same power in hfp8 mode, with the fp16 path's adder
reused rather than duplicated. The rounding of the two-product sum
before the fp16 result is not stated, so the value is registered here
rather than on the fused multi-term dot, whose single-rounding contract
the disclosure does not establish. The scalar shape is the baseline of
one product per cycle; the bf16 datapath carries the same op_shape axis
with a dot4 form. Chunk-based accumulation and the fp16 or fp32
accumulate precision are unchanged by the shape, and the
unified_internal_format flag records the fp9 container.

The library realizes this choice as a pin of the generated fp8_training_datapath module (`chialu/targets/rtl/families/dot.py`); the family card names the construction.

## references

agrawal_2021 -> A. Agrawal, S. K. Lee, J. Silberman, et al., "A 7nm 4-Core AI Chip with 25.6TFLOPS Hybrid FP8 Training, 102.4TOPS INT4 Inference and Workload-Aware Throttling", IEEE ISSCC, 2021
