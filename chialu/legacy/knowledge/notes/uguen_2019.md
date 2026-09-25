---
handle: uguen_2019
citation: Y. Uguen, L. Forget, F. de Dinechin, "Evaluating the Hardware Cost of the Posit Number System", International Conference on Field Programmable Logic and Applications (FPL), 2019
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_DOT_ACC]
formats: [posit8_0, posit16_1, posit32_2, posit64_3, fp16, fp32, fp64]
authority: incremental
pages_read: 106-113 / 8
---

## summary
The paper proposes a parameterized Vivado HLS library for posit addition/subtraction/multiplication and the first open-source parameterized hardware quire (p.106). The custom posit intermediate format reduces internal datapath widths while preserving round-to-nearest, ties-to-even conversion (pp.108-109). The evaluated posit32 arithmetic costs more than comparable floating-point arithmetic, while the posit32 quire has similar cost/performance to a 32-bit floating-point Kulisch accumulator (pp.111-113).

## families
### posit_adder_multiplier  (role: extends)
mechanism: Posits are decoded into a fixed-field posit intermediate format (PIF) containing a NaR flag, two's-complement significand, biased exponent, round bit, and sticky bit. The adder/subtracter uses a single path and exploits mutual exclusion between large alignment and normalization shifts to limit intermediate widths. The multiplier forms an exact signed product, normalizes it into PIF, and encodes the rounded posit (pp.108-109).
choices:
  es_bits: 0; 1; 2; 3   # p.107
  regime_decode: lzc_plus_shifter   # p.108
  internal_representation: twos_complement   # p.108
  approximation: none   # pp.109-110
new_choices:
  intermediate_format: posit_intermediate_format — fixed-width NaR/sign/exponent/implicit/fraction/round/sticky representation   # p.108
slots:
  none
parameters: N and wes parameterize the format; standard evaluations use (N,wes)=(8,0),(16,1),(32,2),(64,3), with PIF widths 14, 23, 40, and 73 bits   # p.107
results:
| metric | value | unit | technology / device | baseline | condition | page |
| adder LUT | 745 | LUT | FPGA / Zynq-7000, 2019 | [9]: 981 LUT; [10]: 1115 LUT | N=32, combinatorial | p.111 |
| adder delay | 24 | ns | FPGA / Zynq-7000, 2019 | [9]: 40 ns; [10]: 29 ns | N=32, combinatorial | p.111 |
| multiplier LUT | 469 | LUT | FPGA / Zynq-7000, 2019 | [9]: 572 LUT; [10]: 648 LUT | N=32, combinatorial | p.111 |
| multiplier DSP | 4 | DSP | FPGA / Zynq-7000, 2019 | [9]: 4 DSP; [10]: 4 DSP | N=32, combinatorial | p.111 |
| multiplier delay | 27 | ns | FPGA / Zynq-7000, 2019 | [9]: 33 ns; [10]: 27 ns | N=32, combinatorial | p.111 |
| adder LUT | 738 | LUT | FPGA / Kintex 7 xc7k160tfbg484-1, 2019 | IEEE: 425 LUT | N=32, pipelined | p.112 |
| adder registers | 811 | Reg. | FPGA / Kintex 7 xc7k160tfbg484-1, 2019 | IEEE: 375 Reg. | N=32, pipelined | p.112 |
| adder cycles | 22 | cycles | FPGA / Kintex 7 xc7k160tfbg484-1, 2019 | IEEE: 14 cycles | N=32, pipelined | p.112 |
| adder delay | 2.659 | ns | FPGA / Kintex 7 xc7k160tfbg484-1, 2019 | IEEE: 2.690 ns | N=32, pipelined | p.112 |
| multiplier LUT | 544 | LUT | FPGA / Kintex 7 xc7k160tfbg484-1, 2019 | Float: 80 LUT; Soft FP: 67 LUT | N=32, pipelined | p.112 |
| multiplier registers | 710 | Reg. | FPGA / Kintex 7 xc7k160tfbg484-1, 2019 | Float: 193 Reg.; Soft FP: 228 Reg. | N=32, pipelined | p.112 |
| multiplier DSP | 4 | DSP | FPGA / Kintex 7 xc7k160tfbg484-1, 2019 | Float: 3 DSP; Soft FP: 2 DSP | N=32, pipelined | p.112 |
| multiplier cycles | 21 | cycles | FPGA / Kintex 7 xc7k160tfbg484-1, 2019 | Float: 7 cycles; Soft FP: 9 cycles | N=32, pipelined | p.112 |
| multiplier delay | 2.421 | ns | FPGA / Kintex 7 xc7k160tfbg484-1, 2019 | Float: 2.201 ns; Soft FP: 2.193 ns | N=32, pipelined | p.112 |
errors_and_checks: The encoder rounds to nearest with ties to even; 8-bit and 16-bit standard posit implementations were tested exhaustively against SoftPosit (pp.109-110).
conditions: The single-path width contraction depends on large alignment and normalization shifts being mutually exclusive (p.109). The Stratix V posit32 multiplier comparison is affected by different DSP mappings and by synthesizing Xilinx-oriented VHDL for Intel hardware (p.111). The floating-point multiplier comparison lacks a fully IEEE-compliant baseline with subnormal support (p.111).
evidence: §II-B; §III-A-D; Figures 2-5; Tables I-IV (pp.107-112)

### single_path  (role: instantiates)
mechanism: The posit PIF adder/subtracter aligns the smaller significand, performs signed addition, then applies leading-zero/one counting and normalization. Cancellation permits a large normalization shift only when the exponent difference and initial alignment shift are small (p.109).
choices:
  pipeline_depth: UNKNOWN
  post_round_renorm: UNKNOWN
new_choices:
  none
slots:
  sig_adder: UNKNOWN
  round: UNKNOWN
  exp: UNKNOWN
  subnormal: none [outside domain]   # p.107
  align: full_align   # p.109
  norm: coarse_fine   # p.109
parameters: internal significand signals are mostly wf+2 through wf+6 bits   # p.109
results:
| metric | value | unit | technology / device | baseline | condition | page |
| internal datapath width | wf+2 to wf+6 | bits | architecture / result year 2019 | previous implementations appear twice as wide | PIF addition intermediates | p.109 |
errors_and_checks: Round and sticky bits preserve the information required for final round-to-nearest, ties-to-even encoding (pp.108-109).
conditions: Posits have no infinity encoding and arithmetic saturates instead; 0 and NaR are special encodings (p.107).
evidence: Figure 4 and §III-D (p.109)

### posit_quire_mac  (role: proposes)
mechanism: The quire receives exact posit products, shifts each product by its exponent into a fixed-point accumulator, and adds/subtracts it with a wide adder. A sticky NaR flag avoids testing the encoded NaR value on every operation. Segmented variants limit carry propagation during accumulation, followed by final carry propagation and quire-to-PIF-to-posit conversion (pp.109-112).
choices:
  quire_width_bits: 128; 512   # pp.107,112
  organization: monolithic_register; segmented_quire [outside domain]   # pp.110-112
  op_set: fused_ops_general   # pp.106,109
new_choices:
  segment_width_bits: {32, 64} — width of independently accumulated quire segments   # pp.110-112
  nar_handling: sticky_flag — a flag is set by a NaR input and remains set through the computation   # p.110
slots:
  none
parameters: standard quire width wq=N²/2; evaluated widths are 128 bits for posit16 and 512 bits for posit32; accumulation II=1; workload is 1000 sums of products   # pp.107,112
results:
| metric | value | unit | technology / device | baseline | condition | page |
| LUT | 5068 | LUT | FPGA / Kintex 7 xc7k160tfbg484-1, 2019 | none | posit32, 512-bit, unsegmented | p.112 |
| cycles | 1040 | cycles | FPGA / Kintex 7 xc7k160tfbg484-1, 2019 | Float32: 10011 cycles | 1000 products, unsegmented | p.112 |
| delay | 8.850 | ns | FPGA / Kintex 7 xc7k160tfbg484-1, 2019 | target: 3 ns | posit32, unsegmented | p.112 |
| LUT | 4394 | LUT | FPGA / Kintex 7 xc7k160tfbg484-1, 2019 | Kulisch32 S32: 4446 LUT | posit32, S32 | p.112 |
| registers | 4779 | Reg. | FPGA / Kintex 7 xc7k160tfbg484-1, 2019 | Kulisch32 S32: 5290 Reg. | posit32, S32 | p.112 |
| cycles | 1055 | cycles | FPGA / Kintex 7 xc7k160tfbg484-1, 2019 | Kulisch32 S32: 1050 cycles | 1000 products, S32 | p.112 |
| delay | 2.854 | ns | FPGA / Kintex 7 xc7k160tfbg484-1, 2019 | Kulisch32 S32: 2.875 ns | posit32, S32 | p.112 |
| LUT | 3783 | LUT | FPGA / Kintex 7 xc7k160tfbg484-1, 2019 | Kulisch32 S64: 4365 LUT | posit32, S64 | p.112 |
| cycles | 1047 | cycles | FPGA / Kintex 7 xc7k160tfbg484-1, 2019 | Kulisch32 S64: 1041 cycles | 1000 products, S64 | p.112 |
| delay | 2.961 | ns | FPGA / Kintex 7 xc7k160tfbg484-1, 2019 | Kulisch32 S64: 2.854 ns | posit32, S64 | p.112 |
errors_and_checks: The quire performs exact sums/products; final posit conversion rounds to nearest with ties to even (pp.109-111).
conditions: Segmentation is required to approach the 3 ns target because the unsegmented wide adder has a long carry-propagation delay (pp.110-112). Final carry propagation is irreducible, so conversion overhead matters for short sums/FMA-like uses but is amortized for long sums (p.112).
evidence: Figures 6-8; Tables I, V, and VI; §III-E and §IV-C (pp.107,109-112)

### kulisch_long_accumulator  (role: compares)
mechanism: A 559-bit two's-complement floating-point Kulisch accumulator is evaluated with 32-bit and 64-bit segmentation and an IEEE-compliant final conversion that rounds to nearest with ties to even (pp.111-112).
choices:
  accumulator_width_bits: 559 [outside domain]   # pp.111-112
  organization: segmented_lazy_carry   # pp.111-112
  carry_resolution: periodic_sweep   # p.112
new_choices:
  segment_width_bits: {32, 64} — accumulator carry-propagation segment size   # pp.111-112
slots:
  cpa: UNKNOWN
parameters: 559-bit accumulator; S32/S64 segmentation; 1000 products   # pp.111-112
results:
| metric | value | unit | technology / device | baseline | condition | page |
| LUT | 4446 | LUT | FPGA / Kintex 7 xc7k160tfbg484-1, 2019 | posit32 quire S32: 4394 LUT | S32, 1000 products | p.112 |
| cycles | 1050 | cycles | FPGA / Kintex 7 xc7k160tfbg484-1, 2019 | posit32 quire S32: 1055 cycles | S32, 1000 products | p.112 |
| delay | 2.875 | ns | FPGA / Kintex 7 xc7k160tfbg484-1, 2019 | posit32 quire S32: 2.854 ns | S32, 1000 products | p.112 |
errors_and_checks: The implementation was validated against MPFR simulations and uses IEEE-compliant round-to-nearest, ties-to-even conversion (p.111).
conditions: Exact accumulation uses roughly 10x more resources and reduces latency by roughly 10x versus regular floating-point accumulation for the evaluated 1000-product workload (p.112).
evidence: §IV-C and Table V (pp.111-112)

## new_families
none

## space_gaps
* posit_quire_mac lacks a `segment_width_bits` choice for the evaluated S32/S64 segmented architectures (pp.110-112).
* posit_quire_mac lacks a choice for sticky-flag versus encoded NaR handling (p.110).
* posit_adder_multiplier lacks choices for PIF field sizing and round/sticky preservation, which determine the reported internal-width reduction (pp.108-109).

## open_questions
* The paper does not identify the carry-propagate adder topology used inside the PIF operators or quire.
* The paper does not fully describe the state representation and carry protocol inside each segmented quire/Kulisch segment.
* The multiplication comparison does not include a fully IEEE-compliant floating-point baseline with subnormal support (p.111).
