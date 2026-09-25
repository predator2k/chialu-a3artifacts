---
handle: gudovskiy_2017
citation: R. B. Lee, "Precision Architecture", IEEE Computer, vol. 22, no. 1, pp. 78-91, 1989
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [dynamic_fixed_point_8bit, int16, shiftcnn_NB_weight_index]
authority: incremental
pages_read: 1-9 / 9
---

## summary
ShiftCNN replaces CNN weight multiplications with shifts/additions by representing each weight as a sum of signed powers of two and precomputing the possible products for each input. The evaluated N=2, B=4 FPGA pipeline uses 2.5× fewer resources and 4× less dynamic power than a conventional 8-bit fixed-point implementation. ImageNet accuracy drops remain within 1% for the reported N=2, B=4 convolutional-layer configurations.

## families
### approximate_mac_nn  (role: proposes)
mechanism: Each quantized weight is the sum of N entries selected from signed power-of-two codebooks Cn. Algorithm 1 greedily quantizes normalized weights without retraining. ShiftCNN replaces each product with a right shift/sign flip and accumulates N selected terms. # p.3-5
choices:
  multiplier_source: power_of_two_codebook [outside domain]   # p.3-5
  precision_scaling: none   # p.3-6
  retraining: false   # p.1, p.6
new_choices:
  weight_codebook: sum_of_N_signed_power_of_two_sets — Defines each weight using N indexed codebook entries.   # p.3
slots:
  none
parameters: N codebooks; B-bit index per codebook; M=2^B-1 combinations; evaluated N={1,2,3}, B=4; N=8, B=3 represents 8-bit fixed point   # p.3, p.6-7
results:
| metric | value | unit | technology / device | baseline | condition | page |
| top-1 accuracy decrease | 35.39 | % | UNKNOWN; 2017 | 32-bit SqueezeNet | N=1, B=4 | p.6 |
| top-5 accuracy decrease | 35.09 | % | UNKNOWN; 2017 | 32-bit SqueezeNet | N=1, B=4 | p.6 |
| top-1 accuracy decrease | 1.01 | % | UNKNOWN; 2017 | 32-bit SqueezeNet | N=2, B=4 | p.6 |
| top-5 accuracy decrease | 0.71 | % | UNKNOWN; 2017 | 32-bit SqueezeNet | N=2, B=4 | p.6 |
| top-1 accuracy decrease | 0.01 | % | UNKNOWN; 2017 | 32-bit SqueezeNet | N=3, B=4 | p.6 |
| top-5 accuracy decrease | 0.01 | % | UNKNOWN; 2017 | 32-bit SqueezeNet | N=3, B=4 | p.6 |
| top-1 accuracy decrease | 11.26 | % | UNKNOWN; 2017 | 32-bit GoogleNet | N=1, B=4 | p.6 |
| top-5 accuracy decrease | 7.36 | % | UNKNOWN; 2017 | 32-bit GoogleNet | N=1, B=4 | p.6 |
| top-1 accuracy decrease | 0.39 | % | UNKNOWN; 2017 | 32-bit GoogleNet | N=2, B=4 | p.6 |
| top-5 accuracy decrease | 0.29 | % | UNKNOWN; 2017 | 32-bit GoogleNet | N=2, B=4 | p.6 |
| top-1 accuracy decrease | 0.05 | % | UNKNOWN; 2017 | 32-bit GoogleNet | N=3, B=4 | p.6 |
| top-5 accuracy decrease | 0.09 | % | UNKNOWN; 2017 | 32-bit GoogleNet | N=3, B=4 | p.6 |
| top-1 accuracy decrease | 40.17 | % | UNKNOWN; 2017 | 32-bit ResNet-18 | N=1, B=4 | p.6 |
| top-5 accuracy decrease | 39.11 | % | UNKNOWN; 2017 | 32-bit ResNet-18 | N=1, B=4 | p.6 |
| top-1 accuracy decrease | 0.54 | % | UNKNOWN; 2017 | 32-bit ResNet-18 | N=2, B=4; convolution only | p.6 |
| top-5 accuracy decrease | 0.34 | % | UNKNOWN; 2017 | 32-bit ResNet-18 | N=2, B=4; convolution only | p.6 |
| top-1 accuracy decrease | 3.21 | % | UNKNOWN; 2017 | 32-bit ResNet-18 | N=2, B=4; batch normalization/scaling quantized | p.6 |
| top-5 accuracy decrease | 2.05 | % | UNKNOWN; 2017 | 32-bit ResNet-18 | N=2, B=4; batch normalization/scaling quantized | p.6 |
| top-1 accuracy decrease | 0.03 | % | UNKNOWN; 2017 | 32-bit ResNet-18 | N=3, B=4; convolution only | p.6 |
| top-5 accuracy decrease | 0.12 | % | UNKNOWN; 2017 | 32-bit ResNet-18 | N=3, B=4; convolution only | p.6 |
| top-1 accuracy decrease | 0.29 | % | UNKNOWN; 2017 | 32-bit ResNet-50 | N=3, B=4; convolution only | p.6 |
| top-5 accuracy decrease | 0.15 | % | UNKNOWN; 2017 | 32-bit ResNet-50 | N=3, B=4; convolution only | p.6 |
errors_and_checks: Table 1 reports classification-accuracy loss rather than arithmetic error; N=2, B=4 convolution-only variants lose 0.39%-1.01% top-1 accuracy, while N=3, B=4 variants lose at most 0.29%. GoogleNet N=2 and N=3 probability errors have nearly zero bias.   # p.6-7
conditions: B>4 provides no significant accuracy improvement when N>1. N=1, B=4 performs poorly without retraining. Quantized batch-normalization/scaling weights may require N>2 because their distributions are broader/asymmetric.   # p.6-7
evidence: Algorithm 1 and Figure 1, p.3-4; Table 1, p.6; Figure 4, p.7

## new_families
### precomputed_codebook_convolution  (domain: dot, closest: approximate_mac_nn, why_not: approximate_mac_nn lacks the shared product-codebook precomputation/memory/multiplexer mechanism)
mechanism: ShiftALU generates all P=M+2(N-1) possible convolution terms for each input using a pass-through path, cascaded right shifts, and sign flipping. A memory buffer stores (P-1)C̄ terms. Weight indices select stored terms or zero through multiplexers, and an adder tree accumulates the selected terms plus bias. With C̄=C, the design processes the input-channel dimension concurrently. # p.5-6
choices:
  weight_terms_N: Int[1..∞] — Number of codebook terms accumulated per weight.   # p.3, p.5
  index_bits_B: Int[1..∞] — Width of each codebook index.   # p.3, p.5
  parallelization_level_Cbar: Int[1..C] — Concurrent convolution terms.   # p.5-6
  precomputed_term_storage: shift_register_array — Stores (P-1)C terms for C̄=C.   # p.6
results:
| metric | value | unit | technology / device | baseline | condition | page |
| speed-up | 260 | × | UNKNOWN; 2017 | conventional multiplication cycles | SqueezeNet | p.8 |
| speed-up | 687 | × | UNKNOWN; 2017 | conventional multiplication cycles | GoogleNet | p.8 |
| speed-up | 1090 | × | UNKNOWN; 2017 | conventional multiplication cycles | ResNet-18 | p.8 |
| LUT utilization | 4016 | LUTs | Xilinx Zynq XA7Z030; 2017 | none | ShiftCNN, 200 MHz | p.8 |
| register utilization | 2219 | FFs | Xilinx Zynq XA7Z030; 2017 | none | ShiftCNN, 200 MHz | p.8 |
| DSP utilization | 0 | DSPs | Xilinx Zynq XA7Z030; 2017 | none | ShiftCNN, 200 MHz | p.8 |
| dynamic power | 102 | mW | Xilinx Zynq XA7Z030; 2017 | multiplier DSP: 423 mW; multiplier LUT: 391 mW | N=2, B=4, C̄=128, 200 MHz | p.8 |
| resource reduction | 2.5 | × | Xilinx Zynq XA7Z030; 2017 | conventional 8-bit fixed-point pipeline | ShiftCNN | p.8 |
| dynamic-power reduction | 4 | × | Xilinx Zynq XA7Z030; 2017 | conventional 8-bit fixed-point pipeline | ShiftCNN | p.8 |
| adder-tree power share | 75 | % | Xilinx Zynq XA7Z030; 2017 | ShiftCNN total dynamic power | N=2, B=4, C̄=128 | p.8 |
| product-computation power reduction | 12 | × | Xilinx Zynq XA7Z030; 2017 | conventional product computation | ShiftCNN | p.8 |
evidence: Figures 2-3 and Algorithm 2, p.4-6; Tables 2-3, p.8

## space_gaps
* `approximate_mac_nn.multiplier_source` lacks a signed power-of-two codebook/shift implementation value. # p.3-5
* The dot vocabulary lacks shared precomputation of all products from a small weight codebook followed by indexed selection. # p.5-6
* The shifter vocabulary lacks a fixed shift-by-one cascade that exposes every intermediate shift simultaneously. # p.5, p.7

## open_questions
* The paper does not specify the adder-tree topology or adder-cell family. # p.5-6
* The FPGA technology node and detailed power-estimation activity assumptions are not reported. # p.8
