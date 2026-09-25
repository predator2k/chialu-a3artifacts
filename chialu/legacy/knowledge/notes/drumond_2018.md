---
handle: drumond_2018
citation: M. Drumond, T. Lin, M. Jaggi, B. Falsafi, "Training DNNs with Hybrid Block Floating Point", NeurIPS, pp. 451-461, 2018
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [fp32, fp16, bfp8, bfp12]
authority: incremental
pages_read: 1-8 / 11
---

## summary
HBFP performs DNN dot products in block floating point using fixed-point mantissa arithmetic, while other operations remain FP32. Per-dot-product exponent selection, tiled exponent sharing, wide weight storage, and stochastic output rounding let 8- and 12-bit HBFP configurations match the reported FP32 training accuracy while reaching 1 TOp/s on the prototype. # p.2, p.4-p.8

## families
### block_fp_accumulation  (role: proposes)
mechanism: HBFP converts tensors to BFP immediately before convolutions/matrix multiplications/outer products, using the largest tensor value to select a shared exponent. Mantissa dot products use fixed-point arithmetic without intermediate alignment. Tiled products are accumulated in floating point, and results return to floating point after each dot product. Persistent weights use wider BFP mantissas for FP32 weight updates, while forward/backward passes access narrow mantissas. The FPGA prototype uses wide accumulators and stochastic rounding during BFP-to-FP truncation. # p.4-p.6
choices:
  block_size: 24; 64 evaluated   # p.7
  mantissa_bits: 4; 8; 12 [outside domain]; 16 [outside domain]   # p.7
  exponent_sharing_granularity: tile   # p.5, p.7
  inter_block_accumulate: fp32   # p.4-p.5
new_choices:
  exponent_selection_timing: before_each_dot_product — A maximum-value scan selects the exponent for each conversion to BFP.   # p.2, p.5-p.6
  wide_weight_storage_bits: 16 — Weight updates retain wider mantissas while forward/backward operations use narrow mantissas.   # p.5, p.7
  output_rounding: stochastic — BFP-to-FP mantissa truncation uses Xorshift-based stochastic rounding.   # p.6
slots:
  none
parameters: Dot-product mantissas are 4/8/12/16 bits in the design-space study; selected configurations use 8- or 12-bit arithmetic, 16-bit weight storage, and 24 × 24 tiles. The prototype uses 8-bit multiply-and-add units, 8-bit activation mantissas, 8-bit activation exponents, wide accumulators, and a 200MHz clock.   # p.6-p.8
results:
| metric | value | unit | technology / device | baseline | condition | page |
| test error | 25.12 | % | UNKNOWN / 2018 | FP32: 26.07% | CIFAR-100, RN-50, hbfp8_16, tile 24 | p.7 |
| test error | 25.10 | % | UNKNOWN / 2018 | FP32: 26.07% | CIFAR-100, RN-50, hbfp12_16, tile 24 | p.7 |
| test error | 20.78 | % | UNKNOWN / 2018 | FP32: 20.35% | CIFAR-100, WRN-28-10, hbfp8_16, tile 24 | p.7 |
| test error | 20.78 | % | UNKNOWN / 2018 | FP32: 20.35% | CIFAR-100, WRN-28-10, hbfp12_16, tile 24 | p.7 |
| test error | 26.27 | % | UNKNOWN / 2018 | FP32: 26.03% | CIFAR-100, DN-40, hbfp8_16, tile 24 | p.7 |
| test error | 25.82 | % | UNKNOWN / 2018 | FP32: 26.03% | CIFAR-100, DN-40, hbfp12_16, tile 24 | p.7 |
| test error | 1.98 | % | UNKNOWN / 2018 | FP32: 1.89% | SVHN, RN-50, hbfp8_16, tile 24 | p.7 |
| test error | 1.96 | % | UNKNOWN / 2018 | FP32: 1.89% | SVHN, RN-50, hbfp12_16, tile 24 | p.7 |
| test error | 1.98 | % | UNKNOWN / 2018 | FP32: 2.00% | SVHN, WRN-16-8, hbfp8_16, tile 24 | p.7 |
| test error | 1.94 | % | UNKNOWN / 2018 | FP32: 2.00% | SVHN, WRN-16-8, hbfp12_16, tile 24 | p.7 |
| test error | 1.79 | % | UNKNOWN / 2018 | FP32: 1.80% | SVHN, DN-40, hbfp8_16, tile 24 | p.7 |
| test error | 1.85 | % | UNKNOWN / 2018 | FP32: 1.80% | SVHN, DN-40, hbfp12_16, tile 24 | p.7 |
| test error | 23.88 | % | UNKNOWN / 2018 | FP32: 23.64% | ImageNet, RN-50, hbfp8_16, tile 24 | p.7 |
| test error | 23.58 | % | UNKNOWN / 2018 | FP32: 23.64% | ImageNet, RN-50, hbfp12_16, tile 24 | p.7 |
| validation perplexity | 61.86 | perplexity | UNKNOWN / 2018 | FP32: 61.31 | LSTM-PTB, hbfp8_16, tile 24 | p.7 |
| validation perplexity | 61.35 | perplexity | UNKNOWN / 2018 | FP32: 61.31 | LSTM-PTB, hbfp12_16, tile 24 | p.7 |
| forward/backward bandwidth reduction | up to 4× | relative | UNKNOWN / 2018 | FP32 | 8-bit mantissas | p.7 |
| throughput | 1 | TOp/s | Stratix V 5SGSD5 / 2018 | none | 8-bit multiply-and-add units at 200MHz | p.8 |
| throughput improvement | 8.5× | relative | Stratix V 5SGSD5 / 2018 | FP16 multiply-and-add accelerator on the same FPGA | 8-bit HBFP prototype | p.8 |
| activation-unit resources | less than 10 | % | Stratix V 5SGSD5 / 2018 | total FPGA resources | Floating-point activation units | p.8 |
| conversion-unit resources | less than 1 | % | Stratix V 5SGSD5 / 2018 | total FPGA resources | FP-to-BFP/BFP-to-FP units | p.8 |
| conversion performance overhead | 0 | performance overhead | Stratix V 5SGSD5 / 2018 | accelerator without conversion overhead | Conversion units | p.8 |
| model compression | 2× | relative | UNKNOWN / 2018 | FP32 | BFP-FP training | p.8 |
errors_and_checks: No arithmetic error bound is reported. The empirical accuracy contract is FP32-matching validation behavior across the tested image/language models; 4-bit mantissas increase error by 4.1%, while tile sizes 24 × 24 and 64 × 64 remain within 0.5% of FP32.   # p.7
conditions: Dot products tolerate BFP input loss only when exponents avoid saturation because large terms dominate the reduction. Other operations remain floating point because arbitrary value distributions and frequent realignment can make general BFP inaccurate or costly. Tiling adds one floating-point operation per 2 × N operations for an N × N tile. The prototype stores weights/activations on-chip and is a proof of concept rather than a full system evaluation.   # p.5-p.6
evidence: §4, §4.1, §4.2, §5.1, §5.3, §6; Eq. 2; Fig. 2-Fig. 3; Table 2-Table 3, p.4-p.8

## new_families
none

## space_gaps
* `block_fp_accumulation.mantissa_bits` excludes the evaluated 12- and 16-bit mantissas. # p.7
* `block_fp_accumulation` lacks a wide-weight-storage choice for the reported 16-bit persistent weight mantissas. # p.5, p.7
* `block_fp_accumulation` lacks exponent-selection timing and BFP-to-FP rounding choices, which distinguish per-dot-product maximum-exponent selection and stochastic truncation. # p.5-p.6

## open_questions
* The paper does not specify the fixed-point multiplier/reduction-tree microarchitecture or accumulator width. # p.6
* The paper does not state whether the FPGA throughput estimate includes off-chip storage or conversion of externally stored tensors; the prototype stores weights and activations on-chip. # p.6-p.8
