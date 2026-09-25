# bf16_fma_datapath

Multiply-accumulate on bfloat16 operands, which keep the fp32 exponent and an 8-bit significand, into an fp32 accumulator. The 8-by-8-bit significand product is exact in 16 bits and representable in fp32 while its exponent stays in range, so the multiplier is an 8-bit integer multiplier and the product needs no rounding. Arm's BFDOT form computes two products per 32-bit lane, adds them in a reduced-width FP25 adder that rounds to fp32, and adds the pair sum to the accumulator in a chained rather than fused sequence, with round-to-odd, flush-to-zero subnormals, default NaNs, and no exception flags. The scalar form feeds an ordinary fp32 FMA with operands read as shortened fp32 values.

op_shape trades reuse against throughput. scalar_fma reuses the fp32 FMA unchanged. dot2_accumulate pairs the products before accumulation, which shortens accumulator latency and reduces the accumulated rounding error, and two BFDOT operations compose the 2x4 by 4x2 BFMMLA matrix operation at 16 multiplications per 128 bits of datapath per cycle; the systolic training accelerators do the same accumulation of bfloat16 matrix products into fp32 inside the array. rounding_mode and flush_subnormals buy area with accuracy: round-to-odd is unbiased but carries about twice the rounding error of round-to-nearest, roughly 1 ulp more over 18,432 accumulations, and supporting it alone rather than all four IEEE modes cuts about 25% of the block, flushing subnormals cuts about 15% more, and all the simplifications together remove 65% of a fully IEEE-compliant block. multi_word_composition splits an fp32 value into one to three bfloat16 components and computes the partial inner products in several invocations, so the same hardware reaches higher precision because each bfloat16 product is preserved exactly by the fp32 accumulator.

The accuracy contract is statistical rather than an ulp bound: training with round-to-nearest conversion matches fp32 convergence and task accuracy across image, translation, GAN, and recommender models, direct truncation costs about 0.02% recommendation accuracy, and round-to-odd inference reproduces the round-to-nearest bfloat16 result in 99.97% of DeepSpeech outputs, with rare late cancellation exposing a larger relative error. The family wins where the fp32 exponent range removes the loss scaling fp16 needs and where the mul slot can shrink to an 8-bit multiplier, about 64 against 576 area units for fp32 in a first-order estimate, with a 7-nm estimate of 0.21 pJ per multiply against 0.31 pJ for IEEE fp16. It loses where exception flags, NaN propagation, subnormals, or correctly rounded results are contractual, and for models that do not tolerate the quantization.

The seed instantiates the library's generated module for this family (`chialu/targets/rtl/families/dot.py`: the exact narrow products aligned to the largest exponent and summed with c in the exact window; the `op_shape` names the element count, `rounding_mode` is applied by the seed's rounding under the run's mode, `flush_subnormals` is the unit's daz/ftz option). `python3 -m chialu.targets.rtl.families.dot --fab <format> --fc <format> --fd <format> --n <elements> --family <family> --pins k=v,...` emits it for a rewrite.

## design choices

### op_shape

| member | what it selects |
| --- | --- |
| `scalar_fma` | one product and the addend. |
| `dot2_accumulate` | two products and the addend. |
| `dot4_accumulate` | four products and the addend; the module header records a disagreement between the shape and the mode's element count. |

### rounding_mode

| member | what it selects |
| --- | --- |
| `rne` | round to nearest, ties to even. |
| `rtz` | round toward zero. |
| `round_to_odd` | round to odd, which keeps a later rounding exact. |

## references

burgess_2019 -> N. Burgess, J. Milanovic, N. Stephens, K. Monachopoulos, D. Mansell, "Bfloat16 Processing for Neural Networks", ARITH-26, pp. 88-91, 2019
lutz_2019 -> D. R. Lutz, "ARM Floating Point 2019: Latency, Area, Power", 26th IEEE Symposium on Computer Arithmetic, 2019
henry_2019 -> G. Henry, P. T. P. Tang, A. Heinecke, "Leveraging the bfloat16 Artificial Intelligence Datatype For Higher-Precision Computations", ARITH-26, pp. 69-76, 2019
kalamkar_2019 -> D. Kalamkar, D. Mudigere, N. Mellempudi, D. Das, K. Banerjee, et al., "A Study of BFLOAT16 for Deep Learning Training", arXiv:1905.12322, 2019
norrie_2021 -> T. Norrie, N. Patil, D. H. Yoon, G. Kurian, S. Li, J. Laudon, C. Young, N. Jouppi, D. Patterson, "The Design Process for Google's Training Chips: TPUv2 and TPUv3", IEEE Micro, vol. 41, no. 2, pp. 56-63, 2021.
