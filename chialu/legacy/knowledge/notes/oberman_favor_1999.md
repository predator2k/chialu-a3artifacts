---
handle: oberman_favor_1999
citation: S. Oberman, G. Favor, F. Weber, "AMD 3DNow! Technology: Architecture and Implementations", IEEE Micro, vol. 19, no. 2, pp. 37-48, 1999.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_SFU, VEC_DOT_ACC]
formats: [fp32, int16, int32]
authority: landmark
pages_read: 37-48 / 12
---

## summary
The paper defines the packed-fp32 3DNow! instruction architecture and describes its AMD-K6-2/AMD-K6-III/AMD-K7 implementations. The arithmetic hardware uses two-path floating-point adders, Booth-encoded compressor-tree multipliers with rounding integrated into reduction, and table-interpolated reciprocal/reciprocal-square-root estimates refined by pipelined Newton-Raphson instructions. PFACC and two-lane SIMD execution support dot-product-style multimedia kernels.

## families
### replicated_lanes  (role: instantiates)
mechanism: A 64-bit MMX register holds two IEEE-compatible 32-bit floating-point values, and most 3DNow! instructions apply the same operation independently to both halves (p.38). The AMD-K6 multimedia unit has X/Y execution pipelines with per-pipeline MMX ALUs and shared SIMD add/multiply/approximation/shifter resources (p.42). The AMD-K7 places 3DNow!/MMX/x87 execution in a shared floating-point coprocessor (p.44).
choices:
  register_file: AMD-K6-2/AMD-K6-III=dedicated_simd; AMD-K7=fp_shared   # p.42, p.44
  rearrangement: pack_unpack   # p.37, p.39
new_choices:
  element_format: 2x32-bit IEEE-compatible single precision — defines the packed lane format   # p.38
  horizontal_accumulate: PFACC — adds the two halves of each source operand into two destination sums   # p.39
slots:
  none
parameters: 2 fp32 lanes per 64-bit register; 2 execution pipelines in AMD-K6-2/AMD-K6-III; up to 2 multimedia instructions issued per cycle   # p.38, p.42
results:
| metric | value | unit | technology / device | baseline | condition | page |
| peak throughput | 4 | floating-point operations/cycle | AMD-K6-2, 0.25-micron five-metal CMOS, year 1998 | none | one two-lane PFADD and one two-lane PFMUL initiated together | p.42 |
| instruction latency | 2 | cycles | AMD-K6-2, 0.25-micron five-metal CMOS, year 1998 | none | all 3DNow! instructions | p.42 |
errors_and_checks: Inputs/results below the minimum normal number are flushed to zero; infinities/NaNs are unsupported; numeric overflow returns a properly signed maximum representable normal number.   # p.38
conditions: Existing MMX registers avoid new architectural state and operating-system context support (p.39). Scalar operations use packed instructions with the unused high 32 bits ignored (p.39).
evidence: “3DNow! architecture,” pp.38-39; Figures 2-3 and “AMD-K6 microprocessors,” pp.41-42.

### two_path  (role: instantiates)
mechanism: Each SIMD lane uses Far/Near computational paths. The Far path handles effective addition, non-near effective subtraction, comparisons, min/max, and floating-point-to-integer conversion; the Near path handles the remaining operations (p.43). The partition ensures that a computation encounters at most one full-length shifter (p.43).
choices:
  close_path_trigger: exp_diff_and_effective_sub   # p.43
new_choices:
  none
slots:
  round: compound_adder_select   # p.43
  subnormal: flush_to_zero_mode   # p.38
parameters: 2 parallel 32-bit single-precision adders; K6 latency 2 cycles and II 1 cycle; K7 PFADD latency 4 cycles and throughput 1 instruction/cycle   # p.42, p.43, p.45
results:
| metric | value | unit | technology / device | baseline | condition | page |
| PFADD latency | 2 | cycles | AMD-K6-2, 0.25-micron five-metal CMOS, year 1998 | none | fully pipelined 3DNow! implementation | p.42 |
| PFADD latency | 4 | cycles | AMD-K7, node UNKNOWN, year 1999 | none | AMD-K7 multimedia instruction | p.45 |
| PFADD throughput | 1 | instruction/cycle | AMD-K7, node UNKNOWN, year 1999 | none | AMD-K7 multimedia instruction | p.45 |
errors_and_checks: none
conditions: The two-path partition reduces latency by limiting each computation to one full-length shifter (p.43). Comparisons/conversions/min/max reuse the paths without additional resources (p.43).
evidence: “Floating-point adder,” p.43; Table 3, p.45.

### round_fused_in_reduction  (role: instantiates)
mechanism: The multiplier adds a rounding constant to the two reduced partial products through two rows of (3,2) counters during cycle 1. Two independent carry-propagate adders then form overflow/no-overflow candidates during cycle 2, and an overflow signal selects the final 32-bit result (p.44).
choices:
  none
new_choices:
  overflow_candidate_generation: dual_cpa — forms overflow/no-overflow rounded candidates in parallel   # p.44
slots:
  sig_mul: booth_recoded_parallel [booth_radix=Booth-2 encoding [outside domain]]   # p.44
  subnormal: flush_to_zero_mode   # p.38
parameters: 2-cycle K6 implementation; two candidate carry-propagate adders; 32-bit final result   # p.44
results:
| metric | value | unit | technology / device | baseline | condition | page |
| PFMUL latency | 2 | cycles | AMD-K6-2, 0.25-micron five-metal CMOS, year 1998 | none | fully pipelined 3DNow! implementation | p.42 |
| PFMUL latency | 4 | cycles | AMD-K7, node UNKNOWN, year 1999 | none | AMD-K7 multimedia instruction | p.45 |
| PFMUL throughput | 1 | instruction/cycle | AMD-K7, node UNKNOWN, year 1999 | none | AMD-K7 multimedia instruction | p.45 |
errors_and_checks: Arithmetic operations use round-to-nearest-even.   # p.38
conditions: The same multiplier supports fp32 multiplication, packed int16 multiplication, and reciprocal/reciprocal-square-root iteration instructions (p.43).
evidence: Figure 4 and “Multiplier,” pp.43-44; Table 3, p.45.

### booth_recoded_parallel  (role: instantiates)
mechanism: Each 32×32-bit multiplier generates 17 partial products with “Booth-2 encoding.” A binary tree of 4-2 compressors reduces the partial products to two before rounding and carry assimilation (p.44).
choices:
  booth_radix: Booth-2 encoding [outside domain]   # p.44
new_choices:
  dual_format_alignment: fp32_or_2xint16 — selects one 24-bit-significand fp32 product or two packed int16 products   # p.43
slots:
  reduction: compressor_4_2_tree   # p.44
parameters: 32×32-bit core; 24-bit fp32 significands; two packed 16-bit integer operand pairs; 17 partial products   # p.43, p.44
results:
| metric | value | unit | technology / device | baseline | condition | page |
| partial products | 17 | partial products | AMD-K6-2, 0.25-micron five-metal CMOS, year 1998 | none | 32-bit multiplier using Booth-2 encoding | p.44 |
errors_and_checks: none
conditions: Data alignment permits the multiplier hardware to serve either fp32 or packed int16 operations (p.43).
evidence: Figure 4 and “Multiplier,” pp.43-44.

### compressed_lut  (role: instantiates)
mechanism: The approximation unit replaces prohibitively large direct lookup tables with simplified interpolation. Reciprocal and reciprocal-square-root estimates each use parallel p/q tables; their outputs are added, and the 16-bit sum is prefixed with a leading 1 (p.44).
choices:
  none
new_choices:
  table_pairing: parallel_p_q — two tables jointly form each estimate   # p.44
  table_widths: p=16 bits, q=7 bits — widths of the parallel table outputs   # p.44
slots:
  none
parameters: reciprocal tables recip-rom-p/recip-rom-q with 1,024 entries each; reciprocal-square-root tables sqrt-rom-p/sqrt-rom-q with 2,048 entries each   # p.44
results:
| metric | value | unit | technology / device | baseline | condition | page |
| PFRCP estimate precision | 14 | bits | AMD-K6-2, 0.25-micron five-metal CMOS, year 1998 | full-precision reciprocal | replicated initial approximation | p.40 |
| PFRSQRT estimate precision | 15 | bits | AMD-K6-2, 0.25-micron five-metal CMOS, year 1998 | full-precision reciprocal square root | replicated initial approximation | p.40 |
| direct-table size | more than 670 | Kbits | device UNKNOWN, node UNKNOWN, year 1999 | compressed interpolated tables | naive direct lookup for more than 14-bit accuracy | p.44 |
errors_and_checks: PFRCP/PFRSQRT must return more than 14 accurate bits according to the implementation discussion.   # p.44
conditions: The compressed implementation is selected because a naive direct lookup would exceed 670 Kbits (p.44). A single 15-bit PFRSQRT result is sufficient for lighting calculations that do not require full 24-bit accuracy (p.48).
evidence: “Reciprocal and reciprocal square root instructions,” pp.40-41; “Approximation unit,” p.44.

### newton_raphson  (role: instantiates)
mechanism: Fully pipelined Newton-Raphson iteration instructions refine PFRCP/PFRSQRT initial estimates rather than using atomic long-latency division or square-root instructions. The reciprocal sequence uses PFRCP, PFRCPIT1, and PFRCPIT2; the reciprocal-square-root sequence adds PFMUL and PFRSQIT1 before PFRCPIT2 (pp.40-41).
choices:
  none
new_choices:
  function_set: reciprocal_and_reciprocal_sqrt — identifies the refined functions   # pp.40-41
slots:
  none
parameters: reciprocal sequence PFRCP+PFRCPIT1+PFRCPIT2; reciprocal-square-root sequence PFRSQRT+PFMUL+PFRSQIT1+PFRCPIT2; fully pipelined   # pp.40-41
results:
| metric | value | unit | technology / device | baseline | condition | page |
| correctly rounded operands | 99 | % | AMD 3DNow!, node UNKNOWN, year 1999 | correctly rounded reciprocal | full-precision reciprocal sequence | p.41 |
| correctly rounded operands | 87 | % | AMD 3DNow!, node UNKNOWN, year 1999 | correctly rounded reciprocal square root | full-precision reciprocal-square-root sequence | p.41 |
| PFRCP latency | 3 | cycles | AMD-K7, node UNKNOWN, year 1999 | none | initial reciprocal approximation | p.45 |
| PFRCP throughput | 1 | instruction/cycle | AMD-K7, node UNKNOWN, year 1999 | none | initial reciprocal approximation | p.45 |
errors_and_checks: Any sequence result not correctly rounded to nearest differs from the correctly rounded result by one unit in the last place.   # p.41
conditions: Reciprocal multiplication replaces direct division, and reciprocal-square-root multiplication replaces direct square root (p.40). The iteration sequences are used when the initial 14/15-bit estimates are insufficient (pp.40-41).
evidence: “Reciprocal and reciprocal square root instructions,” pp.40-41; Table 2, p.41; Table 3, p.45.

### shift_round_convert  (role: instantiates)
mechanism: PI2FD/PF2ID convert two packed 32-bit values between integer and fp32 formats. Conversion operations reuse the floating-point adder’s Far path and available comparison/rounding hardware (p.43).
choices:
  rounding_modes: rz_only   # p.38
  overflow_behavior: saturate   # p.38
  reuse_add_datapath: true   # p.43
new_choices:
  none
slots:
  subnormal: flush_to_zero_mode   # p.38
parameters: packed 2×int32 to 2×fp32 and packed 2×fp32 to 2×int32; conversions use truncation   # p.38
results:
| metric | value | unit | technology / device | baseline | condition | page |
| conversion latency | 2 | cycles | AMD-K6-2, 0.25-micron five-metal CMOS, year 1998 | none | all 3DNow! instructions fully pipelined | p.42 |
errors_and_checks: Numeric overflow produces a properly signed maximum representable normal number; subnormal inputs/results flush to zero.   # p.38
conditions: Conversion operations use truncation rather than the arithmetic instructions’ round-to-nearest-even mode (p.38).
evidence: Table 1 and data-format description, p.38; “Floating-point adder,” p.43.

## new_families
none

## space_gaps
* `replicated_lanes` lacks choices for floating-point element format and horizontal accumulation, which distinguish the 2×fp32/PFACC organization (pp.38-39).
* `compressed_lut` lacks table-pairing/table-size/table-width choices needed to represent the p/q interpolation implementation (p.44).
* `sfu:newton_raphson` lacks a function-set choice for reciprocal versus reciprocal-square-root refinement (pp.40-41).
* `booth_recoded_parallel.booth_radix` does not admit the document’s literal value “Booth-2 encoding” (p.44).

## open_questions
* The document does not state whether “Booth-2 encoding” corresponds to a vocabulary radix value, so the merge pass must not map it to radix 4 (p.44).
* PFRCP is called a 14-bit approximation on p.40, while the implementation discussion says each estimate must be accurate to more than 14 bits on p.44.
* The numeric threshold separating near and far effective subtractions is not reported (p.43).
* The AMD-K7 technology node is not reported in the document.
