---
handle: oberman_1999
citation: Oberman, "Floating Point Division and Square Root Algorithms and Implementation in the AMD-K7 Microprocessor", 14th IEEE Symposium on Computer Arithmetic, 1999
actual_citation: Stuart Oberman, Greg Favor, and Fred Weber, "AMD 3DNow! Technology: Architecture and Implementations", IEEE Micro, 1999
status: mismatch
kind: paper
unit_classes: [BINARY_ALU, VEC_SFU, VEC_DOT_ACC]
formats: [fp32, int32, int16, int8]
authority: incremental
pages_read: 37-48 / 12
---

## summary
The document defines 3DNow! packed-fp32 instructions and describes their AMD-K6-2/AMD-K7 implementations, including two-path addition, shared floating-point/integer multiplication, and table-based reciprocal/reciprocal-square-root approximation (pp.37-45). Newton-Raphson instructions refine the approximations, with full-precision reciprocal and reciprocal-square-root sequences producing results within one ulp of correct rounding (pp.40-41).

## families
### two_path  (role: instantiates)
mechanism: Two fp32 adders divide computation between a Far path and a Near path. The Far path handles effective additions, non-near effective subtractions, comparisons, min/max, and floating-point-to-integer conversions. The Near path handles the remaining operations. The partition limits each computation to at most one full-length shifter, while a compound adder produces sum and sum + 1 for rounding selection.
choices:
  close_path_trigger: exp_diff_and_effective_sub   # p.43
new_choices:
  auxiliary_operation_overlay: comparisons/min-max/conversion — reuses the two arithmetic paths without additional resources   # p.43
slots:
  sig_adder: UNKNOWN   # p.43
  round: compound_adder_select   # p.43
  subnormal: flush_to_zero_mode   # p.38
  far_align: full_align   # p.43
parameters: two packed fp32 lanes; two physical 32-bit single-precision adders   # pp.38,43
results:
| metric | value | unit | technology / device | baseline | condition | page |
| latency | 2 | cycles | 0.25-micron, five-metal CMOS with local interconnect / AMD-K6-2 / 1998 | UNKNOWN | PFADD; fully pipelined | p.42 |
| initiation interval | 1 | cycle | 0.25-micron, five-metal CMOS with local interconnect / AMD-K6-2 / 1998 | UNKNOWN | one packed floating-point add can start per cycle | p.42 |
| latency | 4 | cycles | UNKNOWN / AMD-K7 / 1999 | UNKNOWN | 3DNow! PFADD | p.45 |
| throughput interval | 1 | cycle | UNKNOWN / AMD-K7 / 1999 | UNKNOWN | 3DNow! PFADD | p.45 |
errors_and_checks: Arithmetic uses round-to-nearest-even; inputs/results below the minimum normal value flush to zero; infinities/NaNs and exceptions/status flags are unsupported   # p.38
conditions: The Near path is limited to operations excluded from the Far-path classification; the document gives no numeric path threshold   # p.43
evidence: “Floating-point adder,” Figure 3, and Table 3, pp.42-45

### booth_recoded_parallel  (role: instantiates)
mechanism: Each 32-bit multiplier generates 17 partial products with the document’s “Booth-2 encoding.” A binary tree of 4-2 compressors reduces the partial products to two. Two rows of (3,2) counters add rounding constants before two independent carry-propagate adders form overflow and non-overflow candidates.
choices:
  booth_radix: 2 [outside domain]   # pp.43-44
new_choices:
  none
slots:
  reduction: compressor_4_2_tree   # pp.43-44
  hard_multiple_adder: UNKNOWN   # pp.43-44
parameters: 32 × 32-bit multiplier; 17 partial products; two execution cycles in AMD-K6-2   # pp.43-44
results:
| metric | value | unit | technology / device | baseline | condition | page |
| latency | 2 | cycles | 0.25-micron, five-metal CMOS with local interconnect / AMD-K6-2 / 1998 | UNKNOWN | 3DNow! multiply; fully pipelined | p.42 |
| latency | 4 | cycles | UNKNOWN / AMD-K7 / 1999 | UNKNOWN | 3DNow! PFMUL | p.45 |
| throughput interval | 1 | cycle | UNKNOWN / AMD-K7 / 1999 | UNKNOWN | 3DNow! PFMUL | p.45 |
errors_and_checks: none
conditions: AMD-K6-2 shares the multiplier between MMX/3DNow! operations; AMD-K7 uses a dedicated MMX multiplier and incorporates 3DNow! multiplication into the x87 multiplier   # pp.42,44
evidence: Figure 4 and “Multiplier,” pp.43-44; Table 3, p.45

### twin_precision_subword  (role: instantiates)
mechanism: Each 32 × 32-bit multiplier accepts either one pair of fp32 operands with 24-bit significands or two pairs of 16-bit integer operands. Packed-integer alignment sign-extends the high product and zeros the cross-product region.
choices:
  partition: halves   # pp.43-44
new_choices:
  none
slots:
  lane_cpa: UNKNOWN   # pp.43-44
parameters: one 24 × 24-bit significand product or two concurrent 16 × 16-bit integer products per multiplier   # pp.43-44
results:
| metric | value | unit | technology / device | baseline | condition | page |
| latency | 3 | cycles | UNKNOWN / AMD-K7 / 1999 | UNKNOWN | MMX MUL | p.45 |
| throughput interval | 1 | cycle | UNKNOWN / AMD-K7 / 1999 | UNKNOWN | MMX MUL | p.45 |
errors_and_checks: PMULHRW supplies packed 16-bit integer multiplication with rounding; no numeric error bound is stated   # p.38
conditions: The document does not state whether signed/unsigned behavior is independently selectable per lane   # pp.38,43-44
evidence: Figure 4 and “Multiplier,” pp.43-44; Table 3, p.45

### round_fused_in_reduction  (role: instantiates)
mechanism: Rounding constants enter the partial-product reduction through two rows of (3,2) counters. The reduction retains candidates for overflow and no overflow, two carry-propagate adders assimilate them in the second cycle, and an overflow signal selects the final fp32 result.
choices:
  none
new_choices:
  none
slots:
  sig_mul: booth_recoded_parallel [booth_radix=2 [outside domain]]   # pp.43-44
  exp: UNKNOWN   # pp.43-44
  subnormal: flush_to_zero_mode   # p.38
parameters: two candidate carry-save results; two final 64-bit carry-propagate adders; 32-bit final result   # p.43
results:
| metric | value | unit | technology / device | baseline | condition | page |
| latency | 2 | cycles | 0.25-micron, five-metal CMOS with local interconnect / AMD-K6-2 / 1998 | UNKNOWN | packed fp32 PFMUL; fully pipelined | p.42 |
errors_and_checks: Arithmetic uses round-to-nearest-even; underflowed inputs/results flush to zero and overflow returns a properly signed maximum normal number   # p.38
conditions: The reported organization supports both floating-point and packed-integer multiplication, so the rounding path is active only for operations that require it   # pp.38,43-44
evidence: Figure 4 and “Multiplier,” pp.43-44

### compressed_lut  (role: instantiates)
mechanism: A compressed interpolation unit selects reciprocal or reciprocal-square-root estimates from separate pairs of p/q tables. The p and q values are read in parallel, added, and appended to a leading 1. The design replaces a direct-table implementation requiring more than 670 Kbits.
choices:
  none
new_choices:
  function_table_pairing: separate reciprocal and reciprocal-square-root pairs — selects a dedicated p/q pair for each function   # p.44
slots:
  none
parameters: reciprocal tables recip-rom-p/recip-rom-q with 1,024 entries each; reciprocal-square-root tables sqrt-rom-p/sqrt-rom-q with 2,048 entries each; p entries 16 bits; q entries 7 bits; combined sum 16 bits   # p.44
results:
| metric | value | unit | technology / device | baseline | condition | page |
| latency | 3 | cycles | UNKNOWN / AMD-K7 / 1999 | UNKNOWN | PFRCP | p.45 |
| throughput interval | 1 | cycle | UNKNOWN / AMD-K7 / 1999 | UNKNOWN | PFRCP | p.45 |
errors_and_checks: PFRCP returns a replicated 14-bit reciprocal approximation; PFRSQRT returns a replicated 15-bit reciprocal-square-root approximation; the implementation requirement is more than 14 accurate bits   # pp.40,44
conditions: The initial approximation is scalar and replicated into both packed lanes because applications commonly reuse one reciprocal/reciprocal-square-root value   # p.40
evidence: “Reciprocal and reciprocal square root instructions,” pp.40-41; “Approximation unit,” p.44; Table 3, p.45

### newton_raphson  (role: instantiates)
mechanism: Low-latency, fully pipelined vector instructions refine PFRCP/PFRSQRT estimates instead of implementing atomic nonpipelined full-precision division/square-root instructions. Reciprocal uses PFRCP+PFRCPIT1+PFRCPIT2. Reciprocal square root uses PFRSQRT+PFMUL+PFRSQIT1+PFRCPIT2.
choices:
  none
new_choices:
  iteration_instruction_decomposition: two named refinement instructions — exposes the refinement as separately schedulable vector operations   # pp.40-41
slots:
  none
parameters: three-instruction reciprocal sequence; four-instruction reciprocal-square-root sequence; packed two-lane fp32 operation   # pp.38,40-41
results:
| metric | value | unit | technology / device | baseline | condition | page |
| correctly rounded operands | 99 | % | UNKNOWN / AMD 3DNow! / 1999 | correctly rounded to nearest | full-precision reciprocal sequence | p.41 |
| correctly rounded operands | 87 | % | UNKNOWN / AMD 3DNow! / 1999 | correctly rounded to nearest | full-precision reciprocal-square-root sequence | p.41 |
errors_and_checks: Every result that is not correctly rounded to nearest differs from the correctly rounded result by one ulp   # p.41
conditions: The sequences target cases requiring full precision; a single PFRSQRT is used when 15-bit precision suffices   # pp.40,48
evidence: Table 2 and surrounding text, pp.40-41; vector-normalization example, pp.47-48

### shift_round_convert  (role: instantiates)
mechanism: Packed int32/fp32 conversions reuse the floating-point adder’s Far path. Integer-to-floating-point and floating-point-to-integer conversions use truncation, and conversion operations are overlaid on the two-path adder hardware.
choices:
  rounding_modes: rz_only   # p.38
  reuse_add_datapath: true   # p.43
new_choices:
  none
slots:
  shift_unit: UNKNOWN   # p.43
  round: UNKNOWN   # pp.38,43
  lz: UNKNOWN   # p.43
parameters: two packed 32-bit elements; PI2FD and PF2ID instructions   # p.38
results:
| metric | value | unit | technology / device | baseline | condition | page |
| latency | 2 | cycles | 0.25-micron, five-metal CMOS with local interconnect / AMD-K6-2 / 1998 | UNKNOWN | all 3DNow! instructions, including conversions; fully pipelined | p.42 |
errors_and_checks: Conversion truncates; the document gives no conversion-specific numeric error bound   # p.38
conditions: The document does not specify conversion overflow behavior or the shift/LZ structures   # pp.38,43
evidence: Table 1, p.38; “Floating-point adder,” p.43

## new_families
none

## space_gaps
* `booth_recoded_parallel.booth_radix` lacks the document’s printed `Booth-2` value; mapping `Booth-2` to a declared radix would require interpretation beyond the document (pp.43-44).
* `compressed_lut` lacks choices for function-specific paired-table dimensions and p/q entry widths, which are explicit implementation axes in this design (p.44).
* `newton_raphson` lacks a choice describing refinement decomposed into separately issued pipeline instructions (pp.40-41).

## open_questions
* The document does not give the numeric operand-distance threshold separating Near-path and Far-path subtraction (p.43).
* The document does not identify the carry-propagate-adder topology used by the floating-point adder or multiplier (pp.43-44).
* The document does not give the interpolation equation or table-address partition used by the approximation unit (p.44).
* PFRCPIT1/PFRCPIT2 are called iteration steps, but the document does not state how many mathematical Newton-Raphson iterations they represent (pp.40-41).
