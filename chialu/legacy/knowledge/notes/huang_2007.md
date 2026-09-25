---
handle: huang_2007
citation: L. Huang, L. Shen, K. Dai, Z. Wang, "A New Architecture For Multiple-Precision Floating-Point Multiply-Add Fused Unit Design", ARITH-18, pp. 69-76, 2007
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [fp32, fp64]
authority: incremental
pages_read: 8 / 8
---

## summary
The document proposes a fully pipelined SIMD fused multiply-add unit that performs either one fp64 A×B+C operation or two parallel fp32 operations with one rounding. The synthesized design adds roughly 18% area and 9% worst-case delay over the conventional fp64 MAF baseline while retaining three-cycle latency and one-result-per-cycle throughput.

## families
### multi_precision_simd_fma  (role: proposes)
mechanism: A 64-bit datapath switches between one double-precision operation and two packed single-precision operations. Precision-dependent multiplexers segment the alignment/normalization shifters, multiplier, adder and LZA, while timing-sensitive exponent/rounding hardware is duplicated. The multiplier masks cross-lane partial products in single mode and reduces the remaining array products through a 3-2 CSA. Mantissas use two’s-complement arithmetic. A low-order CPA and upper incrementer produce the significand before two-step normalization and rounding.   # pp.3-7
choices:
  lane_split: 1x64 / 2x32 [outside domain]   # p.3
  shared_rounder: false   # p.7
new_choices:
  module_vectorization: hybrid — precision-mode multiplexers segment shareable modules, while exponent and rounding datapaths are duplicated   # pp.3-4, p.7
  mantissa_representation: twos_complement — the internal representation avoids end-around-carry adjustment during effective subtraction   # p.4
  normalization_structure: constant_then_variable — normalization uses a precision-dependent constant shift followed by a 108-bit or two 50-bit variable shifts   # pp.4,7
slots:
  align: full_align   # pp.4-5
  lza: lza   # pp.4,6-7
  cpa: UNKNOWN
  round: UNKNOWN
  multiplier: carry_save_array [signed_scheme=unsigned]   # pp.5-6
parameters: one 53×53 or two 24×24 significand products; 161-bit alignment/addition datapath; one 108-bit or two 50-bit LZA predictions; three pipeline stages; latency 3 cycles; maximum throughput 1 result per cycle   # pp.3-8
results:
| metric | value | unit | technology / device | baseline | condition | page |
| Multiply & Align area | 531947 | µm² | TSMC 0.18 micron CMOS standard cell library (2007) | none | multiple-precision MAF | p.8 |
| Multiply & Align area | 469514 | µm² | TSMC 0.18 micron CMOS standard cell library (2007) | none | double-precision MAF | p.8 |
| Multiply & Align area | 137233 | µm² | TSMC 0.18 micron CMOS standard cell library (2007) | none | single-precision MAF | p.8 |
| Add & LOP area | 107669 | µm² | TSMC 0.18 micron CMOS standard cell library (2007) | none | multiple-precision MAF | p.8 |
| Add & LOP area | 82081 | µm² | TSMC 0.18 micron CMOS standard cell library (2007) | none | double-precision MAF | p.8 |
| Add & LOP area | 35369 | µm² | TSMC 0.18 micron CMOS standard cell library (2007) | none | single-precision MAF | p.8 |
| Normalize & Round area | 68974 | µm² | TSMC 0.18 micron CMOS standard cell library (2007) | none | multiple-precision MAF | p.8 |
| Normalize & Round area | 49098 | µm² | TSMC 0.18 micron CMOS standard cell library (2007) | none | double-precision MAF | p.8 |
| Normalize & Round area | 20815 | µm² | TSMC 0.18 micron CMOS standard cell library (2007) | none | single-precision MAF | p.8 |
| Total Area | 708590 | µm² | TSMC 0.18 micron CMOS standard cell library (2007) | conventional double-precision MAF | multiple-precision MAF | p.8 |
| Total Area | 600693 | µm² | TSMC 0.18 micron CMOS standard cell library (2007) | none | double-precision MAF | p.8 |
| Total Area | 193417 | µm² | TSMC 0.18 micron CMOS standard cell library (2007) | none | single-precision MAF | p.8 |
| Multiply & Align delay | 3.40 | ns | TSMC 0.18 micron CMOS standard cell library (2007) | none | multiple-precision MAF | p.8 |
| Multiply & Align delay | 3.11 | ns | TSMC 0.18 micron CMOS standard cell library (2007) | none | double-precision MAF | p.8 |
| Multiply & Align delay | 2.56 | ns | TSMC 0.18 micron CMOS standard cell library (2007) | none | single-precision MAF | p.8 |
| Add & LOP delay | 3.34 | ns | TSMC 0.18 micron CMOS standard cell library (2007) | none | multiple-precision MAF | p.8 |
| Add & LOP delay | 3.10 | ns | TSMC 0.18 micron CMOS standard cell library (2007) | none | double-precision MAF | p.8 |
| Add & LOP delay | 2.53 | ns | TSMC 0.18 micron CMOS standard cell library (2007) | none | single-precision MAF | p.8 |
| Normalize & Round delay | 3.38 | ns | TSMC 0.18 micron CMOS standard cell library (2007) | none | multiple-precision MAF | p.8 |
| Normalize & Round delay | 3.04 | ns | TSMC 0.18 micron CMOS standard cell library (2007) | none | double-precision MAF | p.8 |
| Normalize & Round delay | 2.54 | ns | TSMC 0.18 micron CMOS standard cell library (2007) | none | single-precision MAF | p.8 |
| Worst Case Delay | 3.40 | ns | TSMC 0.18 micron CMOS standard cell library (2007) | conventional double-precision MAF | multiple-precision MAF | p.8 |
| Worst Case Delay | 3.11 | ns | TSMC 0.18 micron CMOS standard cell library (2007) | none | double-precision MAF | p.8 |
| Worst Case Delay | 2.56 | ns | TSMC 0.18 micron CMOS standard cell library (2007) | none | single-precision MAF | p.8 |
| total-area overhead | roughly 18 | % | TSMC 0.18 micron CMOS standard cell library (2007) | conventional general-purpose double-precision MAF | multiple-precision MAF | p.8 |
| worst-case-delay increase | roughly 9 | % | TSMC 0.18 micron CMOS standard cell library (2007) | conventional general-purpose double-precision MAF | multiple-precision MAF | p.8 |
| single-precision MAF area | about 32 | % | TSMC 0.18 micron CMOS standard cell library (2007) | double-precision MAF area | standalone single-precision MAF | p.8 |
| alignment-shifter overhead | about 10 | % | TSMC 0.18 micron CMOS standard cell library (2007) | usual 161-bit shifter with 1288 multiplexers | 134 additional multiplexers for dual-mode operation | p.5 |
errors_and_checks: The fused A×B+C operation has only one rounding error. The LZA prediction may have a one-bit position error, so concurrent position correction is used; no arithmetic-error bound, fault model or detection coverage is reported.   # pp.1,6-7
conditions: Algorithm 1 requires normalized A/B/C operands. The synthesis uses speed optimization at 1.8V and 25°C. Array multiplication is selected because Booth encoding requires cross-subword carry detection/suppression and adds control latency. The results are synthesis estimates rather than measured silicon.   # pp.3,5,7-8
evidence: Algorithm 1 and Figures 3-13, pp.3-7; Tables 2-4, pp.7-8

## new_families
none

## space_gaps
* `lane_split` cannot express one selectable datapath supporting both `1x64` and `2x32`; the document implements both modes.   # p.3
* `multi_precision_simd_fma` lacks a choice for the hybrid of precision-dependent segmentation and selective hardware duplication.   # pp.3-4,7
* `multi_precision_simd_fma` lacks choices for internal two’s-complement mantissas and two-step normalization.   # pp.4,7

## open_questions
* The document identifies the final significand adder only as a 106-bit CPA, so its adder family/topology is UNKNOWN.
* The document does not specify the rounder family, supported rounding modes, subnormal handling or complete exception behavior.
* The document does not report whether the synthesized area includes every omitted sign/exponent/exception block shown outside Figure 4.
