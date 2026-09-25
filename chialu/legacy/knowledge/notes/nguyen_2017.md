---
handle: nguyen_2017
citation: D. Nguyen, D. Kim, J. Lee, "Double MAC: Doubling the Performance of Convolutional Neural Networks on Modern FPGAs", Design, Automation and Test in Europe (DATE), 2017
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [int4_to_int11, int16, int32, fp32]
authority: incremental
pages_read: 890-893 / 4 pages
---

## summary
Double MAC packs two reduced-width MAC operations with a shared operand into one unmodified FPGA DSP block, which provides 4 ops/cycle. # p.890
The Virtex-7 implementation doubles the MAC-array size at similar DSP utilization and improves total convolution runtime by 14% for AlexNet and 84% for VGG relative to the 8-bit fixed-point baseline. # pp.892-893

## families
### dsp48_style_slice  (role: extends)
mechanism: A 25x18-bit DSP multiplier receives two n-bit operands separated by n bits and a shared n-bit operand. One guard bit separates the product lanes. The DSP accumulator performs two MACs while carry-out and signed-multiplication corrections are accumulated outside the main lanes and applied after accumulation. # pp.890-891
choices:
  mult_shape: 25x18   # p.890
  alu_width: 48   # p.890
  simd_partition: dual_half   # p.891
new_choices:
  virtual_multiply_partition: shared_operand_packing — two reduced-width products occupy separated fields of one non-SIMD multiplier input   # pp.890-891
  deferred_lane_correction: carry_counter_and_sign_accumulator — lane overflow and signed-product corrections are accumulated separately   # p.891
slots:
  multiplier: behavioral_star   # p.890
parameters: two n-bit MAC lanes; A/B are signed; C is unsigned; one (3n+1)x n-bit multiplication; one guard bit; n <= 8 for the 25x18-bit multiplier; 48-bit DSP accumulator; 4 ops/cycle. # pp.890-891
results:
| metric | value | unit | technology / device | baseline | condition | page |
| DSP per 8-bit MAC | 0.5 | DSP | Xilinx Virtex-7 485T, 2017 | 1 DSP for fixed-point 8-bit MAC | Double MAC | p.892 |
| LUT per 8-bit MAC | 11 | LUT | Xilinx Virtex-7 485T, 2017 | 0 LUT for fixed-point 8-bit MAC | Double MAC correction logic | p.892 |
| FF per 8-bit MAC | 12 | FF | Xilinx Virtex-7 485T, 2017 | 0 FF for fixed-point 8-bit MAC | Double MAC correction logic | p.892 |
| maximum frequency | 280 | MHz | Xilinx Virtex-7 485T, Vivado 2015.2, 2017 | 280 MHz for compared implementations | optimal tile parameters | p.893 |
errors_and_checks: The packed MAC introduces no approximate addition. Accuracy loss comes from truncating feature maps/weights, and carry/sign corrections preserve the packed arithmetic result. # pp.892-893
conditions: The two multiplications must share operand C, and C must be unsigned. The output register must be at least 4n bits, packed inputs must be separated by at least n bits, and accumulation requires one guard bit. The method requires an FPGA with a similar multiplier/accumulator DSP block and does not modify the FPGA fabric. # pp.890-891
evidence: §II-A-C, Figures 1-3, Table I, Table II, pp.890-893

## new_families
### shared_operand_dsp_mac_packing  (domain: dsp: FPGA DSP blocks, closest: dsp48_style_slice, why_not: dsp48_style_slice describes the hard slice, while this mechanism creates virtual multiplication lanes through operand packing and deferred correction without native multiplier partitioning.)
mechanism: Two signed operands A/B are packed into one multiplier input with spacing between lanes and multiplied by the shared unsigned operand C. A guard bit detects lower-lane carry. A counter accumulates carry corrections, a small accumulator collects signed-product corrections, and one external post-accumulation adder/subtractor applies the final adjustment while the DSP starts new work. # pp.890-891
choices:
  packed_lanes: Int[2..2:1]   # p.890
  operand_relation: {shared_common_operand}   # p.890
  common_operand_signedness: {unsigned}   # p.890
  packed_operand_signedness: {signed, unsigned}   # pp.890-891
  guard_bits: Int[1..1:1]   # pp.890-891
  correction_timing: {deferred_post_accumulation}   # p.891
  scaling_scheme: {none, per_layer_power_of_two}   # p.892
results:
| metric | value | unit | technology / device | baseline | condition | page |
| operation throughput | 4 | ops/cycle | Xilinx Virtex-7 485T, 2017 | ordinary DSP MAC | two simultaneous multiply-add operations | p.890 |
| AlexNet total runtime | 1.63 | ms | Xilinx Virtex-7 485T, 2017 | 1.86 ms, 8-bit fixed-point | all convolution layers, 280 MHz, 9 GB/s | p.892 |
| AlexNet power | 5.78 | W | Xilinx Virtex-7 485T, 2017 | 4.35 W, 8-bit fixed-point | all convolution layers | p.892 |
| AlexNet energy | 9.42 | J | Xilinx Virtex-7 485T, 2017 | 8.10 J, 8-bit fixed-point | all convolution layers | p.892 |
| VGG total runtime | 15.07 | ms | Xilinx Virtex-7 485T, 2017 | 27.67 ms, 8-bit fixed-point | all convolution layers, 280 MHz, 9 GB/s | p.892 |
| VGG power | 7.85 | W | Xilinx Virtex-7 485T, 2017 | 5.81 W, 8-bit fixed-point | all convolution layers | p.892 |
| VGG energy | 118.39 | J | Xilinx Virtex-7 485T, 2017 | 160.79 J, 8-bit fixed-point | all convolution layers | p.892 |
| AlexNet DSP usage | 73 | % | Xilinx Virtex-7 485T, 2017 | 73%, 8-bit fixed-point | Double MAC tile (64,64) | p.893 |
| AlexNet LUT usage | 16.98 | % | Xilinx Virtex-7 485T, 2017 | 1.12%, 8-bit fixed-point | Double MAC tile (64,64) | p.893 |
| AlexNet FF usage | 8.88 | % | Xilinx Virtex-7 485T, 2017 | 0.32%, 8-bit fixed-point | Double MAC tile (64,64) | p.893 |
| VGG DSP usage | 73 | % | Xilinx Virtex-7 485T, 2017 | 80%, 8-bit fixed-point | Double MAC tile (64,64) | p.893 |
| VGG LUT usage | 16.98 | % | Xilinx Virtex-7 485T, 2017 | 1.23%, 8-bit fixed-point | Double MAC tile (64,64) | p.893 |
| VGG FF usage | 8.88 | % | Xilinx Virtex-7 485T, 2017 | 0.35%, 8-bit fixed-point | Double MAC tile (64,64) | p.893 |
| output-quality degradation | less than 1 | % top-5 accuracy | Xilinx Virtex-7 485T, 2017 | floating-point network quality | 8-bit quantization with per-layer power-of-two scaling | p.893 |
evidence: §II-A-E, §III-A-D, Figures 1-4, Tables I-IV, pp.890-893

## space_gaps
* dsp48_style_slice lacks a choice for virtual multiplication-lane packing that requires a shared operand rather than native independent SIMD products. # pp.890-891
* The DSP vocabulary lacks slots for deferred carry/sign-correction accumulators and the post-accumulation adjustment adder. # p.891
* The DSP vocabulary lacks per-layer power-of-two operand scaling as a precision-recovery choice for reduced-width CNN MACs. # pp.892-893

## open_questions
* The text names DSP48E1 on p.890 and DSP48E on p.891, so the exact primitive designation is inconsistent.
* The document does not establish whether a signed common operand C can be supported. # pp.890-891
* Figure 4 does not print exact quality values for each tested width from 4 through 11 bits. # p.893
