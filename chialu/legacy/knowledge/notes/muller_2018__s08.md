---
handle: muller_2018#s08
parent: muller_2018
citation: J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
chapter: 8 Hardware Implementation of Floating-Point Arithmetic
pdf_pages: 285-338
status: ok
kind: book_chapter
unit_classes: [BINARY_ALU, VEC_SFU, VEC_DOT_ACC, other]
formats: [IEEE 754-2008 binary, binary16, binary32, binary64, binary128, decimal DPD, BCD, parameterized FPGA floating point]
authority: textbook
pages_read: 54 / 54
---

## summary
The chapter defines the integer/fixed-point primitives used in floating-point hardware and assembles them into binary adders, multipliers, fused multiply-add units, dividers, square-root units, and accumulators. It classifies speed/area/power tradeoffs for VLSI and FPGA implementations and gives abstract area/delay bounds, pipeline depths, exact-accumulator widths, and selected implementation dimensions. It also surveys decimal arithmetic, context-specific FPGA operators, block floating point, compensated operators, and fused algebraic operators.

## families
### ripple_carry  (role: defines)
mechanism: A chain of digit adders implements paper-and-pencil addition. Each binary full adder returns a sum bit and carry bit for three inputs, with the carry propagated horizontally through all positions.
choices:
  full_adder_cell: UNKNOWN   # p.291
  carry_polarity_alternation: UNKNOWN   # p.291
new_choices:
  radix: 2, 10, or a small power of 2 or 10 — selects the digit represented by each chain stage   # p.291
slots:
  none
parameters: n digits; binary full-adder delay 2 gates   # p.291
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area | O(n) | area | abstract | UNKNOWN | n-digit carry-ripple adder | p.291 |
| delay | O(n) | time | abstract | UNKNOWN | n-digit carry-ripple adder | p.291 |
| clean CMOS full adder | 28 | transistors | CMOS | UNKNOWN | illustrative implementation | p.291 |
| compact full adder | as few as 10 | transistors | UNKNOWN | 28-transistor CMOS | limitations apply | p.291 |
errors_and_checks: none
conditions: The full-adder implementation depends on context, and smaller transistor-count cells may not support arbitrary chain lengths.   # p.291
evidence: Section <IP>; Figures 8.1–8.4

### carry_skip  (role: compares)
mechanism: Each radix-2p digit block computes generate and propagate signals independently of its carry input, then evaluates ci+1 = gi OR (pi AND ci).
choices:
  block_width: UNKNOWN   # p.292
  block_sizing: uniform   # p.292
  skip_levels: 1   # p.292
  skip_gate: and_or_bypass   # p.293
new_choices:
  digit_radix: radix-2p — determines the number of binary bits grouped into one digit block   # p.292
slots:
  block_adder: ripple_carry   # p.292
parameters: p bits per digit block   # p.292
results:
| metric | value | unit | technology / device | baseline | condition | page |
| carry propagation delay | 2 | gate delays per radix-2p digit | abstract | 2p gate delays | generate/propagate digit block | p.293 |
errors_and_checks: none
conditions: Faster carry propagation requires a larger digit-adder block, which creates an area/delay tradeoff.   # p.293
evidence: Section <IP>; Figure 8.4

### carry_save_datapath  (role: defines)
mechanism: Full adders reduce three binary operands to sum/carry vectors without horizontal carry propagation. Radix-2p partial carry-save representations generalize the construction to wide pipelined adders and accumulators.
choices:
  compressor: 3_2   # p.293
  assimilation_point: end_of_chain   # p.293
  accumulator_redundant: true   # p.293
new_choices:
  partial_carry_save_radix: radix-2p — bounds carry propagation within each digit   # p.293
slots:
  assimilator: parallel_prefix   # p.293
parameters: arbitrary n and radix β   # p.293
results:
| metric | value | unit | technology / device | baseline | condition | page |
| carry-save area | O(n) | area | abstract | UNKNOWN | three binary operands | p.293 |
| carry-save delay | O(1) | time | abstract | O(n) ripple | redundant output retained | p.293 |
errors_and_checks: Conversion to standard representation requires carry propagation.   # p.293
conditions: Carry-save form is useful when many operands are accumulated before one final conversion.   # p.293
evidence: Section <IP>; Figures 8.5–8.6

### parallel_prefix  (role: defines)
mechanism: Associative generate/propagate pairs combine over consecutive bit ranges. A parallel-prefix tree computes every Gi:0 and Pi:0 in logarithmic time, after which each sum bit is produced in constant time.
choices:
  topology: kogge_stone   # p.294
  valency: UNKNOWN   # p.294
  log2_sparsity: UNKNOWN   # p.294
  fanout_cap: UNKNOWN   # p.295
  wire_track_budget: UNKNOWN   # p.295
  node_style: and_or   # p.294
new_choices:
  none
slots:
  none
parameters: n-bit operands   # p.294
results:
| metric | value | unit | technology / device | baseline | condition | page |
| fast-adder delay | O(log n) | time | abstract | O(n) ripple | standard binary result | p.293 |
| fast-adder area | O(n log n) | area | abstract | O(n) ripple | standard binary result | p.293 |
| family delay range | O(log n) to O(n) | time | abstract | UNKNOWN | prefix-tree tradeoff | p.294 |
| family area range | O(n log n) to O(n) | area | abstract | UNKNOWN | prefix-tree tradeoff | p.294 |
errors_and_checks: none
conditions: Theoretical Kogge-Stone variants may be impractical in submicrometer VLSI because of fanout/wire-routing constraints.   # p.295
evidence: Section <IP>

### compound_flagged_prefix  (role: defines)
mechanism: Available prefix generate/propagate signals support simultaneous computation of A+B and A+B+1 with linear extra hardware and constant extra delay.
choices:
  outputs: sum_sum1   # p.295
  implementation: UNKNOWN   # p.295
  topology: UNKNOWN   # p.295
  late_carry_in: true   # p.295
new_choices:
  absolute_subtraction_output: supported — a related construction selects A−B or B−A from the subtraction sign   # p.295
slots:
  none
parameters: n-bit operands   # p.295
results:
| metric | value | unit | technology / device | baseline | condition | page |
| additional hardware | O(n) | area | abstract | A+B prefix adder | also compute A+B+1 | p.295 |
| additional delay | O(1) | time | abstract | A+B prefix adder | also compute A+B+1 | p.295 |
errors_and_checks: none
conditions: The dual result supports floating-point rounding because the rounded significand is often either a sum or its successor.   # p.295
evidence: Section <IP>

### carry_select  (role: instantiates)
mechanism: Two candidate carry outcomes are computed and selected after the carry becomes known.
choices:
  block_sizing: UNKNOWN   # p.295
  duplication: full_duplicate   # p.295
  select_source: rippled_block_carries   # p.295
new_choices:
  none
slots:
  block_adder: ripple_carry   # p.295
parameters: additions up to 64 bits on the described FPGA class   # p.295
results:
| metric | value | unit | technology / device | baseline | condition | page |
| operating frequency | peak practical frequency | UNKNOWN | high-end FPGA | logarithmic adder | additions up to 64 bits | p.295 |
errors_and_checks: none
conditions: FPGA fast-carry circuitry makes logarithmic adders irrelevant up to very large widths; carry-select reaches the practical peak frequency through 64 bits.   # p.295
evidence: Section <IP>; Figure 8.7

### booth_recoded_parallel  (role: defines)
mechanism: Modified Booth recoding rewrites one operand as radix-4 digits in {−2,−1,0,1,2}. Partial products then require AND rows, sign handling, and shifts rather than a carry-propagating computation of 3X.
choices:
  booth_radix: 4   # p.297
  hard_multiple_gen: none   # p.297
  sign_extension: UNKNOWN   # p.298
  negative_pp_encoding: UNKNOWN   # p.298
new_choices:
  recoded_digit_set: {−2,−1,0,1,2} — supplies redundant signed radix-4 multiplier digits   # p.297
slots:
  reduction: csa_reduction_tree   # p.298
  hard_multiple_adder: UNKNOWN   # p.297
parameters: partial-product array (n+1) × n/2 weighted bits   # p.298
results:
| metric | value | unit | technology / device | baseline | condition | page |
| recoding area | O(n) | area | abstract | UNKNOWN | modified Booth recoding | p.297 |
| recoding delay | O(1) | time | abstract | UNKNOWN | modified Booth recoding | p.297 |
| partial-product generation delay | constant | time | abstract | UNKNOWN | Booth-recoded parallel multiplier | p.298 |
errors_and_checks: Rounding bits can be inserted into the partial-product array.   # p.298
conditions: Radix-4 recoding halves the multiplier-digit count and avoids the carry propagation required by standard radix-4 digit 3.   # p.297
evidence: Sections 8.2.3–8.2.4; Figure 8.8

### barrel_mux_tree  (role: defines)
mechanism: A barrel shifter uses one 2:1 multiplexer stage for each shift-distance bit; stage i either shifts by 2i or passes its input unchanged.
choices:
  stage_radix: 2   # p.301
  select_encoding: binary   # p.301
  direction_handling: UNKNOWN   # p.301
  stage_order: UNKNOWN   # p.301
  sticky_collect: UNKNOWN   # p.301
new_choices:
  none
slots:
  none
parameters: n-bit data; ceil(log2 n)-bit shift distance; ceil(log2 n) stages   # p.301
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area | O(n log n) | area | abstract | UNKNOWN | variable-distance barrel shift | p.301 |
| delay | O(log n) | time | abstract | UNKNOWN | variable-distance barrel shift | p.301 |
| constant-shift area | O(n) | area | abstract | variable shift | fixed distance | p.301 |
| constant-shift delay | O(1) | time | abstract | variable shift | fixed distance | p.301 |
errors_and_checks: none
conditions: Shifters perform significand alignment and normalization.   # p.300
evidence: Section 8.2.6

### lzd_cell_tree  (role: taxonomizes)
mechanism: A binary tree combines counts for adjacent groups; a level-i node returns an (i+1)-bit leading-zero count for 2i bits. An alternative converts the input by prefix OR to a monotonic string and then encodes its single transition.
choices:
  block_primitive: pair_cell   # p.301
  formulation: hierarchical_valid_position   # p.301
new_choices:
  formulation: prefix_or_monotonic [outside domain] — converts the input to zeros followed by ones before one-hot encoding   # p.302
slots:
  none
parameters: n-bit input   # p.301
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area | O(n) | area | abstract | UNKNOWN | tree-based LZC | p.301 |
| delay | O(log n) | time | abstract | UNKNOWN | tree-based LZC | p.301 |
| combined LZC/shift theoretical delay | O((log n)^2) | time | abstract | separate LZC and shifter | generic gate implementation | p.303 |
errors_and_checks: none
conditions: FPGA fast-carry logic hides the wide-OR delay inside the shifter for inputs up to roughly 30 bits.   # p.303
evidence: Sections <IP>–<IP>; Algorithms 8.1–8.2

### two_path  (role: defines)
mechanism: The close path handles effective subtraction with exponent difference at most 1 and performs subtraction/LZA/large normalization. The far path handles exponent difference at least 2 and performs large alignment, addition or subtraction, and at most two-bit prenormalization.
choices:
  path_threshold: 1   # p.306
  close_path_trigger: exp_diff_and_effective_sub   # p.306
  path_select_point: early_exponent_compare   # p.306
  shared_rounding: true   # p.307
new_choices:
  subtraction_sign_resolution: dual_difference_select — computes mx−my and my−mx concurrently, then selects the positive result   # p.307
slots:
  sig_adder: parallel_prefix   # p.308
  round: increment_adder   # p.307
  exp: exponent_path   # p.306
  subnormal: full_hardware   # p.311
  far_align: full_align   # p.306
  close_norm: single_barrel   # p.306
  near_lz: lza   # p.308
parameters: typical binary64 pipeline depth 2, 3, or 4 cycles; reported variable latency 1 to 3 cycles   # p.312
results:
| metric | value | unit | technology / device | baseline | condition | page |
| binary64 pipeline depth | 2, 3, or 4 | cycles | UNKNOWN | UNKNOWN | cited implementations | p.312 |
| variable latency | 1 to 3 | cycles | UNKNOWN | fixed latency | operand-dependent implementation | p.312 |
| LZA error | at most 1 | bit of leading-zero count | abstract | exact post-add LZC | indicator-string anticipation | p.309 |
errors_and_checks: Subnormal addition results are exact; close-path normalization must limit the shift to ex−emin.   # p.311
conditions: The dual path removes the serial combination of large alignment and large cancellation normalization, but the full-custom close path still contains subtraction/LZC/shift unless LZA overlaps the count with subtraction.   # p.308
evidence: Sections 8.3.1–8.3.4; Figures 8.11–8.13

### sig_mul_then_round  (role: defines)
mechanism: The significand multiplier produces a product, a final incrementer applies rounding, and exponent candidates are computed in parallel with the longer significand path.
choices:
  none
new_choices:
  none
slots:
  sig_mul: booth_recoded_parallel   # p.313
  round: increment_adder   # p.313
  exp: exponent_path   # p.313
  subnormal: full_hardware   # p.318
parameters: FPGA embedded products 18×18 bits or 25×18 bits; 36×36 uses four 18×18 multipliers and adders   # p.314
results:
| metric | value | unit | technology / device | baseline | condition | page |
| 36×36 product resources | four 18×18 multipliers and a few adders | blocks | FPGA | UNKNOWN | larger significand multiplier | p.314 |
errors_and_checks: Sticky-bit generation supplies the rounding decision.   # p.313
conditions: The exponent adder may be small and slow because exponent computation overlaps the significand product.   # p.313
evidence: Sections 8.4.1–8.4.2; Figure 8.14

### round_fused_in_reduction  (role: defines)
mechanism: Rounding-mode-dependent injection bits enter the partial-product reduction tree. A compound final adder computes corrected and uncorrected high results concurrently, eliminating one full-width carry-propagating addition.
choices:
  none
new_choices:
  injection_mode: zero, nearest, or infinity — selects the injected low-order constant   # p.315
slots:
  sig_mul: booth_recoded_parallel   # p.315
  exp: exponent_path   # p.317
  subnormal: full_hardware   # p.318
parameters: one 2p-bit final adder plus a few gates   # p.316
results:
| metric | value | unit | technology / device | baseline | condition | page |
| final full-width additions | 1 | 2p-bit adders | abstract | 2 adders | rounding by injection | p.316 |
| injection delay overhead | at most 1 | gate delay | abstract | separate rounding incrementer | partial-product reduction | p.315 |
| subnormal delay overhead | one large significand shift | delay | abstract | no subnormal handling | other work hidden by compression tree | p.319 |
errors_and_checks: Round-to-nearest injection initially gives ties upward; the result LSB and sticky-bit tie detector correct it to nearest-even.   # p.316
conditions: Products in [2,4) require concurrent corrected/uncorrected high sums because the correct injection position depends on normalization.   # p.316
evidence: Sections 8.4.3–8.4.4; Figure 8.15

### classic_fma  (role: defines)
mechanism: Product compression and addend alignment run concurrently. A carry-save adder merges the product and shifted addend, a fast adder resolves the redundant result, an LZA anticipates normalization, and one terminal stage rounds.
choices:
  subsume_fp_add: true   # p.320
  negation_handling: end_around_carry or dual_adder [outside domain]   # p.320
  pipeline_depth: 3 to 7 [outside domain]   # p.320
new_choices:
  none
slots:
  align: full_align   # p.319
  lza: lza   # p.320
  cpa: parallel_prefix   # p.320
  round: increment_adder   # p.320
  multiplier: booth_recoded_parallel   # p.319
parameters: typical latency 3 to 7 cycles; POWER6 dependent latency 6 rather than 7 cycles   # p.320
results:
| metric | value | unit | technology / device | baseline | condition | page |
| pipeline latency | 3 to 7 | cycles | UNKNOWN | UNKNOWN | classic FMA | p.320 |
| dependent-operation latency | 6 | cycles | IBM POWER6 | 7 cycles | rounding deferred to next operation | p.320 |
errors_and_checks: The product retains its full precision and the combined operation rounds once.   # p.319
conditions: Correct rounding makes the datapath substantially more complex than merely adding one row to a multiplier tree.   # p.298
evidence: Section 8.5.1; Figure 8.16

### reduced_latency_fma  (role: compares)
mechanism: Alternative FMAs anticipate normalization before addition, apply rounding by injection, or bypass multiplier stages for pure addition.
choices:
  rounding_position: fused_with_cpa_dual_sum   # p.320
  normalize_before_add: true   # p.320
  add_skip_for_pure_addition: true   # p.320
new_choices:
  none
slots:
  align: full_align   # p.320
  lza: lza   # p.320
  cpa: parallel_prefix   # p.320
  round: injection   # p.320
  multiplier: booth_recoded_parallel   # p.320
parameters: UNKNOWN   # p.320
results:
| metric | value | unit | technology / device | baseline | condition | page |
| decomposed multiplier latency | 4 | cycles | abstract | monolithic 7-cycle FMA | independently usable multiplier | p.322 |
| decomposed adder latency | 4 | cycles | abstract | monolithic 7-cycle FMA | independently usable adder | p.322 |
errors_and_checks: none
conditions: A 4-cycle multiplier followed by a 4-cycle adder performs better on cited application code than a monolithic 7-cycle FMA because elementary dependent operations have shorter latency.   # p.322
evidence: Sections 8.5.2 and 8.6 introduction

### restoring_nonrestoring  (role: defines)
mechanism: Binary restoring division tentatively subtracts D from 2R. A negative result selects qj=0 and restores the shifted old remainder; otherwise qj=1 and retains the subtraction. Nonrestoring division removes one register.
choices:
  style: restoring or nonrestoring [outside domain]   # p.325
  bits_per_cycle: 1   # p.325
  shift_over_zeros: UNKNOWN   # p.325
new_choices:
  none
slots:
  residual_adder: UNKNOWN   # p.325
parameters: radix β=2   # p.325
results:
| metric | value | unit | technology / device | baseline | condition | page |
| per-iteration digit-level cost | O(n) | operations | abstract | significand multiplication | subtraction and digit-times-significand | p.325 |
errors_and_checks: A final correction is required for rounding directions other than downward.   # p.323
conditions: Restoring backtracking is simple in radix 2; recomputation makes backtracking undesirable at higher radices.   # p.325
evidence: Section 8.6.1; Algorithm 8.3

### srt_high_radix  (role: defines)
mechanism: A redundant symmetric quotient-digit set allows the digit-selection function to inspect only leading digits of the residual and divisor. Each iteration computes R(j+1)=βR(j)−qjD and emits log2 β quotient bits.
choices:
  radix: 4   # p.323
  digit_redundancy: UNKNOWN   # p.326
  overlapped_stages: UNKNOWN   # p.326
new_choices:
  quotient_digit_bound: ceil(β/2) ≤ α < β — defines qj in {−α,…,α}   # p.326
  prescaling: optional — multiplies dividend/divisor by an approximate reciprocal to simplify selection   # p.326
slots:
  digit_select: qds_table   # p.326
parameters: approximately p/k iterations for β=2k; cited radix-4 and radix-16 processor implementations   # p.326
results:
| metric | value | unit | technology / device | baseline | condition | page |
| iteration count | roughly p/k | iterations | abstract | radix-2 recurrence | β=2k | p.326 |
errors_and_checks: Redundant digit selection guarantees convergence without backtracking despite truncated residual/divisor inputs to the selector.   # p.325
conditions: Higher radix reduces iteration count but increases qjD complexity and is limited by processor cycle time.   # p.326
evidence: Sections 8.6–8.6.1; Figures 8.17; Algorithm 8.3

### kulisch_long_accumulator  (role: analyzes)
mechanism: Exact 2p-bit products are aligned into a fixed-point accumulator wide enough to cover every product exponent. No intermediate rounding occurs; conversion to floating point performs one final rounding.
choices:
  accumulator_width_bits: format-dependent: 80, 554, 4,196, or 65,756 [outside domain]   # p.328
  organization: UNKNOWN   # p.328
  carry_resolution: UNKNOWN   # p.328
new_choices:
  overflow_margin_bits: at least 60 — protects sums of up to 2^60 products from intermediate overflow   # p.328
slots:
  cpa: UNKNOWN   # p.328
parameters: width formula 2emax−2emin+2p bits   # p.328
results:
| metric | value | unit | technology / device | baseline | condition | page |
| minimum accumulator width | 80 | bits | abstract | UNKNOWN | binary16 | p.328 |
| minimum accumulator width | 554 | bits | abstract | UNKNOWN | binary32 | p.328 |
| minimum accumulator width | 4,196 | bits | abstract | UNKNOWN | binary64 | p.328 |
| minimum accumulator width | 65,756 | bits | abstract | UNKNOWN | binary128 | p.328 |
| overflow protection | 60 | additional bits | abstract | minimum exact width | up to 2^60 products | p.328 |
errors_and_checks: Accumulation is exact until the single conversion back to the destination format; that conversion may overflow or underflow.   # p.328
conditions: Large area, product alignment, and long carry propagation impede GHz-rate implementations, while binary16 makes the accumulator barely larger than an FMA.   # p.328
evidence: Section 8.7.2; Table 8.1

### streaming_accurate_accumulator  (role: instantiates)
mechanism: Inputs are aligned into an application-sized fixed-point window. The loop contains only fixed-point accumulation; normalization is removed from the recurrence and performed separately after accumulation.
choices:
  approach: shifted_fixed_point_window   # p.334
  window_bits: 63   # p.336
  in_loop_normalization: false   # p.334
new_choices:
  accumulator_bounds: MSBA and LSBA — select the fixed-point window and accuracy/overflow range   # p.335
  maximum_input_weight: MaxMSBX — reduces input-shifter width when summands are bounded   # p.335
slots:
  cpa: fpga_carry_chain   # p.334
parameters: wA=MSBA−LSBA+1; example MSBA=24, MaxMSBX=8, LSBA=−38, wA=63 bits   # p.336
results:
| metric | value | unit | technology / device | baseline | condition | page |
| example accumulator width | 63 | bits | FPGA | floating-point iterative accumulator | profiled binary32 coil-inductance summation | p.336 |
| FPGA adder latency | 6 to 12 | cycles | FPGA | processor 3 to 5 cycles | high-frequency floating-point accumulation | p.333 |
errors_and_checks: The window is exact if its LSB covers every input bit and its MSB prevents overflow; profiling alone does not prove the example exact.   # p.334
conditions: Application-specific bounds allow a smaller accumulator than a generic Kulisch register, and LSBA controls the accuracy/area tradeoff.   # p.336
evidence: Sections 8.8.3–<IP>; Figures 8.19–8.21; Example 8.2

### block_fp_accumulation  (role: defines)
mechanism: All vector significands are aligned once to the largest exponent, after which constant multiplication and accumulation use fixed-point arithmetic with one final normalization.
choices:
  block_size: UNKNOWN   # p.337
  mantissa_bits: UNKNOWN   # p.337
  exponent_sharing_granularity: block   # p.337
  inter_block_accumulate: wide_fixed_point   # p.337
new_choices:
  none
slots:
  mul: UNKNOWN   # p.337
  reduction: linear_chain   # p.337
parameters: fixed-point accumulator slightly wider than the input significands   # p.337
results:
| metric | value | unit | technology / device | baseline | condition | page |
| intermediate normalizations | 0 | normalization shifts | abstract | standard floating-point operators | after initial block alignment | p.337 |
errors_and_checks: Initial alignment loses information, but a wider fixed-point accumulator typically improves accuracy over standard operators.   # p.337
conditions: The method applies when a floating-point vector is multiplied by a constant vector, including filters and Fourier transforms.   # p.337
evidence: Section 8.8.4

## taxonomy
* Integer/fixed-point primitives   # p.290
  * Addition
    * Carry-ripple addition -> ripple_carry   # p.291
    * Radix-2p carry-skip addition -> carry_skip   # p.292
    * Carry-save/partial carry-save addition -> carry_save_datapath   # p.293
    * Fast parallel-prefix addition -> parallel_prefix   # p.294
    * Compound sum/sum+1 addition -> compound_flagged_prefix   # p.295
    * Carry-select addition -> carry_select   # p.295
  * Multiplication
    * Modified Booth recoding -> booth_recoded_parallel   # p.297
    * CSA/compressor reduction tree -> csa_reduction_tree [unmapped]   # p.298
    * Fast final addition -> parallel_prefix   # p.298
  * Shifting
    * Variable barrel shift -> barrel_mux_tree   # p.301
    * Constant shift -> unmapped   # p.301
  * Leading-zero counting
    * Tree-based counter -> lzd_cell_tree   # p.301
    * Monotonic-string conversion -> lzd_cell_tree   # p.302
    * Combined FPGA count/shift -> unmapped   # p.302
* Binary floating-point addition   # p.305
  * Single serial datapath -> single_path   # p.308
  * Close/far dual path -> two_path   # p.306
    * Post-add exact LZC -> lzc_after_add   # p.308
    * Leading-zero anticipation -> lza   # p.308
* Binary floating-point multiplication   # p.313
  * Product then increment rounding -> sig_mul_then_round   # p.313
  * Rounding injection in reduction -> round_fused_in_reduction   # p.315
* Binary fused multiply-add   # p.319
  * Classic single path -> classic_fma   # p.319
  * Multipath implementation -> multipath_fma   # p.320
  * Normalize-before-add/injection implementation -> reduced_latency_fma   # p.320
  * Bridge implementation -> bridge_fma   # p.320
  * Decomposed multiplier-plus-adder pipeline -> bridge_fma   # p.322
* Division and square root   # p.322
  * Digit recurrence
    * Restoring/nonrestoring binary division -> restoring_nonrestoring   # p.325
    * SRT division -> srt_radix2 or srt_high_radix   # p.325
    * Decimal SRT -> decimal_digit_recurrence   # p.326
  * Newton–Raphson based -> newton_raphson   # p.322
  * Polynomial based -> unmapped   # p.322
* Large summation   # p.327
  * Exact wide accumulation -> kulisch_long_accumulator   # p.328
  * Adder tree -> pairwise_tree   # p.333
  * Application-specific fixed-point window -> streaming_accurate_accumulator   # p.334
  * Block floating point -> block_fp_accumulation   # p.337
* More fused operators   # p.327
  * Fused three-input sum -> unmapped   # p.327
  * Combined sum and difference -> unmapped   # p.327
  * Fused sum of two products -> fused_two_term_dot   # p.327
  * Fused sum of squares -> fused_two_term_dot   # p.327
* Hardware compensated operations   # p.329
  * Residual-register 2Sum/2Mult -> unmapped   # p.329
  * Dedicated 2Sum operator -> unmapped   # p.330

## primary_sources
* Kogge and Stone, year UNKNOWN — associative recurrence underlying parallel-prefix addition   # p.294
* Avizienis, year UNKNOWN — signed-digit addition using redundant digits to prevent carry propagation   # p.297
* Booth, year UNKNOWN — modified radix-4 recoding for binary multiplication   # p.297
* Wallace, year UNKNOWN — compressor-tree partial-product reduction   # p.298
* Dadda, year UNKNOWN — compressor-tree partial-product reduction   # p.298
* Schmookler and Nowka, year UNKNOWN — survey of leading-zero anticipation implementations   # p.313
* IBM RS/6000 designers, year UNKNOWN — first widely available fused multiply-add architecture   # p.319
* Sweeney, Robertson, and Tocher, year UNKNOWN — independently invented SRT division   # p.325
* Kulisch, year UNKNOWN — exact long accumulator for sums of products   # p.328
* Dieter et al., year UNKNOWN — residual register and conversion instruction for hardware 2Sum/2Mult   # p.329
* Manoukian and Constantinides, year UNKNOWN — FPGA 2Sum hardware operator   # p.330
* DeHon and Kapre, year UNKNOWN — parallel evaluation reproducing the sequential floating-point sum   # p.337

## new_families
### compensated_residual_register  (domain: dot-product / FMA / MAC, closest: streaming_accurate_accumulator, why_not: The mechanism preserves each operation's discarded residual rather than accumulating inputs in a fixed-point window.)
mechanism: A p-bit residual register captures low product or sum bits already generated for sticky-bit computation. A separate instruction normalizes the residual with the adder's LZC/shifter and accounts for whether rounding selected the truncated significand or its successor.
choices: residual_width: Int[1..p:1]; normalization: {on_demand_copy, dedicated}; supported_operation: {addition, multiplication, both}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| 2Sum/2Mult instruction count | 2 | instructions | abstract | software compensated sequence | residual-register proposal | p.330 |
| area overhead | less than 10% | area | binary32 GPU unit | classical floating-point unit | residual-register proposal | p.330 |
| dedicated 2Sum area | 50% larger | area | FPGA | standard adder | includes error-term LZC/shifter | p.330 |
| dedicated 2Sum delay | identical | delay | FPGA | standard adder | cited implementations | p.330 |
evidence: pp.329-330

### fused_three_input_add  (domain: dot-product / FMA / MAC, closest: fused_csa, why_not: The operation adds three floating-point inputs with one rounding rather than flattening integer partial products.)
mechanism: Three floating-point inputs are fused into one addition and one rounding. The operator reuses the three-input register-file capability provisioned for FMA and accelerates triple-word arithmetic.
choices: outputs: {single_rounded_sum}; input_count: {3}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area increase | one third | FMA area | abstract | FMA | support fused three-input addition | p.327 |
evidence: p.327

### combined_sum_difference  (domain: floating-point adders, closest: two_path, why_not: The mechanism produces both a+b and a−b, while existing adder families produce one result.)
mechanism: Shared floating-point addition hardware computes a+b and a−b concurrently. One close path is shared, reducing hardware relative to two independent standard adders.
choices: outputs: {sum_and_difference}; result_ports: {two}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area | smaller than two standard adders | area | abstract | two juxtaposed adders | one shared close path | p.327 |
evidence: p.327

## space_gaps
* The vocabulary references `csa_reduction_tree` and `compressor_4_2_tree` as slot fillers but declares no corresponding reduction-tree families; the chapter defines 3:2/4:2 compressor trees and Wallace/Dadda organizations.   # p.298
* `lzd_cell_tree.formulation` lacks the chapter's prefix-OR monotonic-string formulation.   # p.302
* `classic_fma.negation_handling` cannot express the chapter's explicit alternative of two parallel adders followed by sign selection.   # p.320
* Exact-accumulator widths exclude the chapter's binary16 value of 80 bits and binary128 value of 65,756 bits.   # p.328

## open_questions
* The cited bibliography is absent from the supplied chapter text, so publication years marked UNKNOWN must be recovered without guessing.
* The chapter names the Figure 8.4 generate/propagate construction a carry-skip adder, but it does not describe the vocabulary's multi-block bypass organization.
* The chapter does not identify the specific prefix topology used inside its floating-point adder, multiplier, or FMA examples.
