---
handle: eisen_2007
citation: Eisen, Ward, Tast, Mading, Leenstra, Mueller, Granito, Prasad, Whitcomb, Mansfield, "IBM POWER6 accelerators: VMX and DFU", IBM Journal of Research and Development, 2007
actual_citation: L. Eisen, J. W. Ward III, H.-W. Tast, N. Mäding, J. Leenstra, S. M. Mueller, C. Jacobi, J. Preiss, E. M. Schwarz, S. R. Carlough, "IBM POWER6 accelerators: VMX and DFU", IBM Journal of Research and Development, 2007
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_SFU, VEC_DOT_ACC, other]
formats: [int8, int16, int32, fp32, bcd, decimal32, decimal64, decimal128]
authority: landmark
pages_read: 663-683 / 21
---

## summary
The document describes the POWER6 VMX SIMD accelerator and the first commercial hardware implementation of IEEE 754R decimal floating-point formats. The VMX contains fixed-point/permute/multiply/fused-fp pipelines, while the DFU provides decimal64/decimal128 arithmetic through a shared 36-digit datapath. Both accelerators operate at more than 5 GHz with a 13 FO4 cycle time.

## families
### replicated_lanes  (role: instantiates)
mechanism: A 128-bit vector register holds sixteen 8-bit, eight 16-bit, or four 32-bit elements. Four execution subunits share two execution pipelines; fixed-point and floating-point arithmetic use four replicated 32-bit datapaths, while one 128-bit permute unit provides rearrangement. # pp.663-665, 668-670
choices:
  register_file: dedicated_simd   # pp.664-665
  rearrangement: full_permute_network   # pp.666-668
new_choices:
  none
slots:
  none
parameters: 128-bit vectors; 16x8-bit, 8x16-bit, or 4x32-bit lanes; 176 VMX instructions   # pp.663, 668
results:
| metric | value | unit | technology / device | baseline | condition | page |
| execution latency | 2 | cycles | POWER6; node UNKNOWN; 2007 | PowerPC 970 two-cycle design at a lower frequency | XS arithmetic execution, excluding result distribution | p.668 |
| permute latency | 4 | cycles | POWER6; node UNKNOWN; 2007 | UNKNOWN | one instruction can issue per cycle | p.666 |
errors_and_checks: Results are sent in program order to a recovery unit that maintains shadow processor state; the document does not report detection coverage. # pp.663-664, 674
conditions: Replication supports workloads whose elements require 8-bit, 16-bit, or 32-bit precision. # pp.663, 668
evidence: Figure 1; Table 1; VMX unit overview; ALU XS; PM.

### carry_select  (role: instantiates)
mechanism: Each 32-bit ADD macro uses a static carry-select adder with 8-bit blocks. Carry generation is shared by sum and integer-compare logic, and 8-bit portions select the intermediate sums at the start of the second cycle. # p.669
choices:
  block_sizing: uniform   # p.669
  duplication: full_duplicate   # p.669
  select_source: rippled_block_carries   # p.669
new_choices:
  none
slots:
  block_adder: carry_lookahead   # p.669
parameters: 32-bit macro; 8-bit blocks; four macros form a 128-bit SIMD datapath; two execution cycles   # pp.668-669
results:
| metric | value | unit | technology / device | baseline | condition | page |
| cycle-time target | 13 | FO4 | POWER6; node UNKNOWN; 2007 | previous PowerPC 970 implementation | two-cycle XS execution | pp.668-669 |
errors_and_checks: none
conditions: The extended carry network supports 8-bit/16-bit/32-bit signed and unsigned addition/subtraction/compare. # p.669
evidence: Figure 3; Adder section.

### barrel_mux_tree  (role: instantiates)
mechanism: Four 32-bit rotator macros perform every rotate and shift as a left rotation during cycle one, followed by range-crossing correction and masking during cycle two. The staged array rotates by 1, 2, 4, 8, and 16 bit positions. # pp.669-670
choices:
  stage_radix: 2   # p.670
  select_encoding: one_hot_decoded   # p.670
  direction_handling: amount_negation   # p.670
  stage_order: small_shift_first   # p.670
new_choices:
  none
slots:
  none
parameters: four 32-bit macros; 128-bit datapath; two execution cycles   # pp.669-670
results:
| metric | value | unit | technology / device | baseline | condition | page |
| execution latency | 2 | cycles | POWER6; node UNKNOWN; 2007 | separate per-width logarithmic arrays | SIMD rotate/shift | pp.669-670 |
errors_and_checks: none
conditions: Range-crossing correction is required for 16-bit and 32-bit elements; 8-bit elements require only masking. # p.670
evidence: Figure 4; Rotator section.

### booth_recoded_parallel  (role: instantiates)
mechanism: The VFU significand multiplier uses radix-4 Booth encoding, produces 14 partial products, and reduces them through three levels of 4:2 compressors. Two less-critical partial products bypass the first compressor level and provide late denormal-input correction. # p.672
choices:
  booth_radix: 4   # p.672
  hard_multiple_gen: none   # p.672
new_choices:
  none
slots:
  reduction: compressor_4_2_tree   # p.672
parameters: fp32 significands; 14 partial products; three 4:2-compressor levels   # p.672
results:
| metric | value | unit | technology / device | baseline | condition | page |
| SIMD width | 4x32 | bits | POWER6; node UNKNOWN; 2007 | UNKNOWN | VFU fused multiply-add | p.670 |
errors_and_checks: The late partial product corrects multiplication when an operand is denormal. # p.672
conditions: The added fourteenth partial product enables full-speed denormal handling without data-dependent stalls. # pp.671-672
evidence: Multiplier correction; Figure 6.

### classic_fma  (role: instantiates)
mechanism: Four fp32 lanes execute A*C+B in a fused datapath. Addition is represented as A*1+B; the aligned addend and Booth product enter an end-around-carry adder, leading-sign anticipation, normalization, and one terminal rounder. # pp.670-674
choices:
  subsume_fp_add: true   # p.672
  negation_handling: end_around_carry   # p.672
  pipeline_depth: 6.5 [outside domain]   # pp.670, 673
new_choices:
  none
slots:
  align: full_align   # pp.672-673
  lza: lza   # pp.673-674
  cpa: end_around_carry   # p.672
  round: increment_adder   # p.673
  multiplier: booth_recoded_parallel [booth_radix=4]   # p.672
parameters: 4x32-bit fp32; 6.5-cycle pipeline; seven-cycle dependent back-to-back issue latency; 13 FO4 cycle time   # pp.670, 673
results:
| metric | value | unit | technology / device | baseline | condition | page |
| pipeline latency | 6.5 | cycles | POWER6; node UNKNOWN; 2007 | POWER6 BFU six-cycle back-to-back issue | fully pipelined VFU | pp.670, 673 |
| dependent issue latency | 7 | cycles | POWER6; node UNKNOWN; 2007 | POWER6 BFU six cycles | no data-dependent forwarding stalls | p.673 |
errors_and_checks: Java mode supports round-to-nearest-even and full-speed denormals; non-Java mode forces denormal operands/results to zero. Traps and exception collection are unsupported. # pp.671-672
conditions: The VMX interface forbids data-dependent stalls/rejects/traps, which excludes the BFU early-forwarding scheme and requires regular-pipeline corner-case handling. # pp.671, 673
evidence: VFU sections; Figure 6.

### bcd_direct_addition  (role: instantiates)
mechanism: Replicated four-digit groups contain conditional digit adders for A+B, A+B+1, A+B+6, and A+B+7. Each group first produces sum and sum+1 candidates; the following cycle determines group carry and selects the result. # pp.678-679
choices:
  digit_code: bcd8421   # pp.678-679
  correction_placement: presum_plus6   # p.678
  carry_scheme: carry_select [outside domain]   # pp.678-679
new_choices:
  none
slots:
  digit_adder: carry_select   # p.678
parameters: reconfigurable one 36-digit or two 18-digit adders; groups 4/4/4/4/2 per half; two-cycle latency; II=1   # pp.678-679
results:
| metric | value | unit | technology / device | baseline | condition | page |
| adder latency | 2 | cycles | POWER6; node UNKNOWN; 2007 | four decimal digits per 13 FO4 cycle | 36-digit datapath | pp.678-679 |
errors_and_checks: none
conditions: The p+2 width supplies guard/round digits for decimal64 and decimal128. # p.679
evidence: Figure 7; Hardware implementation.

### decimal_fp_addition  (role: instantiates)
mechanism: Three concurrent cases handle equal exponents, left alignment to the smaller exponent, or shifts of both operands. Results remain unnormalized except for a possible one-digit right shift, and rounding reuses the adder on a second pass. # pp.679-680
choices:
  alignment: full_shifter   # pp.679-680
  rounding: second_pass_adder [outside domain]   # p.679
  format: decimal64 and decimal128 [outside domain]   # pp.675-677
new_choices:
  none
slots:
  significand_adder: bcd_direct_addition   # pp.678-680
parameters: 16-digit decimal64 and 34-digit decimal128 precision; variable latency   # pp.676-680
results:
| metric | value | unit | technology / device | baseline | condition | page |
| execution time | 9 to 13 | cycles | POWER6; node UNKNOWN; 2007 | UNKNOWN | case 1, decimal64 add/sub | p.680 |
| execution time | 11 to 15 | cycles | POWER6; node UNKNOWN; 2007 | UNKNOWN | case 1, decimal128 add/sub | p.680 |
| execution time | 11 to 15 | cycles | POWER6; node UNKNOWN; 2007 | UNKNOWN | case 2, decimal64 add/sub | p.680 |
| execution time | 13 to 17 | cycles | POWER6; node UNKNOWN; 2007 | UNKNOWN | case 2, decimal128 add/sub | p.680 |
| execution time | 13 to 17 | cycles | POWER6; node UNKNOWN; 2007 | UNKNOWN | case 3, decimal64 add/sub | p.680 |
| execution time | 15 to 19 | cycles | POWER6; node UNKNOWN; 2007 | UNKNOWN | case 3, decimal128 add/sub | p.680 |
errors_and_checks: The result is rounded to the operation’s preferred quantum using one of eight decimal rounding modes. # pp.676-679
conditions: Case 3 is required when exponent difference exceeds the leading-zero count because a 2p-digit adder is considered prohibitive for 34 digits. # p.680
evidence: Addition section; Table 4.

### iterative_decimal_multiplication  (role: instantiates)
mechanism: Decimal coefficient multiplication serially generates easy multiples and accumulates shifted partial products. Decimal64 pairs adjacent digits so the split adder alternates multiple generation and accumulation; decimal128 processes one digit through the two-cycle adder per iteration. # p.680
choices:
  multiple_set: easy_2x_4x_5x   # p.680
  multiplier_digit_recoding: none   # p.680
  digits_per_cycle: 2   # p.680
new_choices:
  none
slots:
  accumulator: linear_chain   # p.680
  final_adder: carry_select   # pp.678-680
parameters: decimal64 execution 19+N cycles; decimal128 execution 21+2N cycles; N excludes leading zeros   # p.680
results:
| metric | value | unit | technology / device | baseline | condition | page |
| execution time | 19+N | cycles | POWER6; node UNKNOWN; 2007 | UNKNOWN | decimal64 multiplication | p.680 |
| execution time | 21+2N | cycles | POWER6; node UNKNOWN; 2007 | UNKNOWN | decimal128 multiplication | p.680 |
errors_and_checks: IEEE decimal rounding follows accumulation; no numeric-error result is reported. # pp.676-680
conditions: Interleaving multiple generation with accumulation avoids additional iteration latency. # p.680
evidence: Multiplication section; Table 4.

### decimal_digit_recurrence  (role: instantiates)
mechanism: Prescaled nonrestoring division selects each quotient digit from the most significant partial-remainder digit. Each iteration selects a digit, forms a divisor multiple, and computes the next remainder; quotient digits use {-5 to +5} and are adjusted on the fly. # pp.680-681
choices:
  quotient_digit_set: minimally_redundant_m5_p5   # p.681
  digit_split: none   # pp.680-681
  divisor_prescaling: true   # p.681
new_choices:
  selection_method: most_significant_digit_extract — prescaling removes a general quotient-selection table from the iteration   # p.681
slots:
  none
parameters: four cycles per iteration; 12-cycle prescaling; 90-entry by 8-bit PLA; one extra iteration for common-case correct rounding   # p.681
results:
| metric | value | unit | technology / device | baseline | condition | page |
| execution time | 82 | cycles | POWER6; node UNKNOWN; 2007 | UNKNOWN | decimal64 division common case | pp.680-681 |
| execution time | 154 | cycles | POWER6; node UNKNOWN; 2007 | UNKNOWN | decimal128 division common case | pp.680-681 |
errors_and_checks: Correct rounding of the common inexact case uses one iteration beyond target precision. # p.681
conditions: The divisor must be prescaled to greater than 1 and strictly less than 1.11. # p.681
evidence: Division section; Table 4.

### decimal_encoding_codec  (role: instantiates)
mechanism: Architectural significands are stored as DPD, expanded to BCD inside the DFU for arithmetic, and compressed back to DPD for register storage. Three BCD digits map to one 10-bit declet. # pp.675-679
choices:
  significand_encoding: dpd   # pp.675-676
  codec_placement: inside_operation   # pp.678-679
new_choices:
  none
slots:
  none
parameters: two DPD-to-BCD expanders; one BCD-to-DPD compressor; three logic-gate conversion levels   # pp.675, 679
results:
| metric | value | unit | technology / device | baseline | condition | page |
| encoding efficiency | greater than 97.6% | percent | POWER6; node UNKNOWN; 2007 | BCD 62.5% | DPD, 1,000 of 1,024 encodings used | p.675 |
errors_and_checks: none
conditions: DPD is selected for fast conversion to BCD-oriented databases and compact register storage. # pp.675-676
evidence: Architecture; Formats; Hardware implementation.

### commercial_decimal_fpu  (role: instantiates)
mechanism: A hardware DFU implements decimal64/decimal128 arithmetic and decimal32 conversion while reusing the binary floating-point register file. Its reconfigurable 36-digit datapath supplies decimal addition, iterative multiplication, nonrestoring division, rotation, and DPD/BCD conversion. # pp.675-681
choices:
  implementation: hardware_dfu   # pp.675, 681
  datapath_width_digits: 36   # pp.678-679
  shared_with_binary_fpu: true   # pp.676-679
new_choices:
  none
slots:
  significand_adder: bcd_direct_addition   # pp.678-680
  multiplier: iterative_decimal_multiplication   # p.680
  divider: decimal_digit_recurrence   # pp.680-681
parameters: decimal64/decimal128 arithmetic; decimal32 conversion; 54 instructions; 36-digit datapath   # pp.663, 676-679
results:
| metric | value | unit | technology / device | baseline | condition | page |
| clock frequency | more than 5 | GHz | POWER6; node UNKNOWN; 2007 | software decimal implementation | VMX and DFU accelerators | p.681 |
| cycle time | 13 | FO4 | POWER6; node UNKNOWN; 2007 | UNKNOWN | VMX and DFU accelerators | p.681 |
errors_and_checks: Eight decimal rounding modes and FPSCR class/exception state are supported; subnormal-class detection may add cycles. # pp.677, 679
conditions: Register-file/load-store reuse minimizes DFU area, assuming binary and decimal floating-point workloads seldom execute simultaneously. # pp.676, 681
evidence: DFU architecture; Figure 7; Table 4; Summary.

## new_families
none

## space_gaps
* `replicated_lanes` lacks the document’s `4x32` floating-point lane arrangement as a declared rearrangement or lane-width value. # pp.663, 670
* `bcd_direct_addition.carry_scheme` lacks the implemented four-digit sum/sum+1 carry-select organization. # pp.678-679
* `decimal_fp_addition.rounding` lacks second-pass reuse of the significand adder. # p.679
* `decimal_digit_recurrence` lacks a digit-selection value for direct most-significant-digit extraction after prescaling. # p.681

## open_questions
* The document calls the VFU “fully pipelined” while reporting seven-cycle back-to-back issuing; it does not state a general one-instruction-per-cycle initiation interval explicitly.
* The document does not identify the semiconductor technology node or report area/power measurements.
