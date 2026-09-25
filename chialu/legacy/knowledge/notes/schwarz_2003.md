---
handle: schwarz_2003
citation: E. M. Schwarz, M. Schmookler, S. D. Trong, "Hardware Implementations of Denormalized Numbers", 16th IEEE Symposium on Computer Arithmetic, 2003
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_DOT_ACC]
formats: [fp32, fp64, fp128, double_extended80, ia64_82bit]
authority: survey
pages_read: full document text / UNKNOWN
---

## summary
The paper summarizes hardware techniques for denormalized operands and denormalized results in a floating-point unit, covering register-file tagging, the exponent-difference correction in the adder, implied-bit correction terms in the multiplier, shift-amount correction in the fused multiply-add, denormalization of an underflowed intermediate result, and prevention of denormalization by bounding the normalizer shift. Most techniques are attributed to filed or pending patents. Section 9 is a case study of the Power4 FPU, which combines tag bits, prenormalization of all operands and a two-cycle back-end stall to keep denormal execution in hardware.

## families
### single_path  (role: analyzes)
mechanism: Floating-point addition is an exponent comparison and difference calculation, alignment, conditional complementation, addition of significands, normalization and rounding. With denormal input the exponent difference is off by one, so implementations compute D, D-1 and D+1, and a late detection of operands equal to denormals selects between the exponent differences; D = A_e - B_e + z with z in {-1,0,+1}. An alternative adds a stage to the aligner that performs a late correction shift based on which operand is denormal. The implied ones of the significands are not critical: one significand is shifted by the aligner while the other is not needed until the carry-propagate addition, so the significand is easily corrected for an implied bit.
choices:
  subnormal_representation: as_stored   # §4 (the denormal enters the dataflow unnormalized and the implied bit is corrected at the significand input)
  operand_order: swap_before_shift   # §6 (the usual method compares the operand exponents and shifts the operand with the smaller exponent to the right)
new_choices:
  denormal_exponent_correction: enum['parallel_difference_select', 'late_aligner_correction_stage'] — whether the denormal correction is a late select among D, D-1, D+1 or an extra aligner stage   # §4
slots:
  exp: exponent_path [D, D-1, D+1 computed in parallel]   # §4
  align: full_align   # §4
  sig_adder: UNKNOWN
  norm: UNKNOWN
  lz: UNKNOWN
parameters: single, double and quad formats, biases 127, 1023 and 16383, Emin -126, -1022 and -16382; 53-bit double significand   # §1, §6
results: none reported for the adder   # §4
errors_and_checks: none
conditions: the exponent difference drives the aligner and is timing critical, so the denormal detection must be late and the selection cheap; the implied-bit correction is off the critical path   # §4
evidence: §1, §4, §6

### sig_mul_then_round  (role: analyzes)
mechanism: Floating-point multiplication is a Booth decode, partial product generation, a counter tree, a carry-propagate addition, normalization and rounding. Williams separates the partial products that depend on an implied one, loc1 and loc2, from the remaining partial products P'; a 53-bit direct (non-Booth) multiplication has 52 partial products for P' plus loc1 and loc2. A counter tree commonly has a few inputs with delayed arrival times and some counter designs are tapered, so the two correction terms can be delayed while the exponent is examined for all zeros to decide the implied bit. The zSeries Booth radix-4 multiplier instead subtracts leading-zero correction terms (lzc1 = -Y*x0) from the partial-product array, or corrects the W1 Booth digit before generating its partial product by computing W1(y0=0) and W1(y0=1) in parallel and multiplexing after y0 is known.
choices:
  slot-level only (see slots)
new_choices:
  implied_bit_correction: enum['late_partial_product_terms', 'subtracted_leading_zero_terms', 'booth_digit_precompute_mux'] — how a denormal operand's missing implied one is corrected inside the partial-product array   # §5
slots:
  sig_mul: direct_pp_parallel [group_bits=1]   # §5 (53-bit non-Booth, 52 PP rows plus loc1 and loc2)
  sig_mul: booth_recoded_parallel [booth_radix=4]   # §5 (the next zSeries FPU)
  exp_adder: UNKNOWN
parameters: 53-bit significand; Booth radix-4 digit set W_j in {-2,-1,0,+1,+2}; 1 or 2 correction terms   # §5
results:
| metric | value | unit | technology / device | baseline | condition | page |
| added counters for denormal correction | 1 or 2 | 3:2 counters | UNKNOWN node, 2003 | multiplier without implied-bit correction | one additional 3:2 counter per added correction term, small against the overall counter tree area | §5 |
errors_and_checks: none
conditions: non-timing-critical where the counter tree can accept more rows without adding stages; the Booth-digit precompute needs a delayed partial product but adds no partial-product row, and then only one correction term is needed for the multiplicand's implied bit   # §5
evidence: §5

### classic_fma  (role: analyzes)
mechanism: The fused multiply-add computes A*C + B or A*C - B with the AC product unrounded before the addition. B is the only operand aligned and complemented, and its alignment is to any position up to a little over 53 bits greater than the AC product or to the least significant bit of the product; the alignment of B runs at the same time as the product is developed and is merged with the product in the final carry-save adder. Add and Subtract set C to 1.0 and Multiply sets B to zero. With a denormal addend the significand is corrected before the aligner while the exponent correction is timing critical and will probably require multiple adders: D = B_e - A_e - C_e + bias + z with z in {-2,-1,0,+1}, and z = -2 need not be considered because the product severely underflows.
choices:
  subsume_fp_add: true   # §6
  negation_handling: UNKNOWN
new_choices:
  denormal_operand_handling: enum['in_dataflow_correction', 'prenormalize_with_stall', 'trap_to_software'] — Power3 and Power4 prenormalize input denormals, the latest zSeries traps on the disjoint case   # §6, §9
  prenormalization_scope: enum['special_cases_only', 'all_operands'] — Power3 prenormalizes the addend only for the difficult cases, Power4 prenormalizes all operands for single and double precision instructions   # §9
slots:
  align: full_align   # §6
  lza: lza [108-bit LZA and normalizer in a multiply-add]   # §9
  multiplier: direct_pp_parallel | booth_recoded_parallel [booth_radix=4]   # §5
  cpa: UNKNOWN
  round: UNKNOWN
  norm_shifter: UNKNOWN
parameters: 53-bit double significand; alignment range a little over 53 bits above the product down to the product lsb; 108-bit LZA and normalizer; Power4 internal exponent of 13 bits with two bits added, three tag bits plus an integer bit per FPR; denormal result re-sent to the normalizer aligned 65 bit positions to the right   # §6, §9
results:
| metric | value | unit | technology / device | baseline | condition | page |
| added cycles per additional denormal operand | 3 | cycles | Power4 FPU, UNKNOWN node, 2003 | normalized-operand execution | multiply-add with up to three denormal operands, prenormalization stalls pipelined | §9 |
| back-end stall length | 2 | cycles | Power4 FPU, UNKNOWN node, 2003 | no stall | unusual result: large normalization shift, denormal result, or exponent rebias for trapped underflow or overflow | §9 |
| LZA and normalizer width | 108 | bits | UNKNOWN node, 2003 | — | multiply-add that avoids the back-end stall (Power3); the Power4 stall allows the LZA and normalizer to be much smaller | §9 |
| internal exponent width | 13 | bits | Power4 FPU, UNKNOWN node, 2003 | architected double exponent | two internal exponent bits added, carried in the FPRs and produced by all arithmetic results | §9 |
| tag and integer bits per FPR | 3 tag bits + 1 integer bit | bits | Power4 FPU, UNKNOWN node, 2003 | untagged FPR | exponent all zeros, exponent all ones and fraction all zeros determined while transmitting data from cache | §9 |
| denormal-result realignment | 65 | bit positions right | Power4 FPU, UNKNOWN node, 2003 | — | the result is normalized but not rounded on the first pass, then sent back to the normalizer during the stall, the low-order intermediate exponent bits giving the shift amount | §9 |
| software denormal execution time | tens of thousands | cycles | UNKNOWN, 2003 | hardware handling | designs that force denormals to software | Abstract |
errors_and_checks: none
conditions: the disjoint case, which is a denormalized addend with a product smaller than the addend's least significant bit, cannot produce 53 bits of significance because the dataflow concatenates the addend with a couple of guard bits to the product, so it is handled by prenormalization or by a trap   # §6. Prenormalization of a double gives an intermediate exponent below Emin and needs another exponent bit; the two added bits also allow the product of two denormals with the underflow trap enabled and avoid ambiguity in the alignment shift count wrapping past zero or all ones   # §9. A prenormalization stall in stage 1 is stopped while a previous instruction runs a back-end stall   # §9
evidence: §6, §9

### lza  (role: extends)
mechanism: Denormalization is prevented by stopping the normalizer from shifting past the radix point of a denormalized result. Urano compares the shift amount for a denormal result with the leading-zero-anticipator shift amount and selects the least; Gorshtein and Khlobystov create both shift amounts in parallel and use two units, one supporting the normalized dataflow with limited shifts and a slow one supporting the maximum shift amounts; Grushin and Vlasenko reduce the comparison and selection of the lesser shift amount into one equation. Naffziger and Beraha force the LZA bit corresponding to the most significant bit position of a denormal to one, decoding the maximum shift amount in parallel. Bjorksten, Mikan and Schmookler (Power3) OR a monotonic denormal mask into the monotonic LZA vector before encoding the shift amount; the paper's variant is M = V_i + U_i and Shift = LZD(M). Handlogten (PowerPC A50) ORs the denormal vector into both the carry and sum inputs of the LZA.
choices: none of the vocabulary's choices for this family are visible in the prompt
new_choices:
  denormal_shift_bound: enum['compare_and_select_lesser', 'force_lza_bit', 'or_denormal_mask_into_lza_vector', 'or_denormal_mask_into_lza_inputs'] — where the bound on the normalization shift is injected   # §8
slots: none
parameters: V is an LZA vector that examines three bits in parallel from bit propagate P, bit generate G and bit zero Z terms; U is the vector of the maximum a denormal can be shifted, indexed against E_product - E_min   # §8
results: none reported   # §8
errors_and_checks: none
conditions: the mask form is simpler when the denormal vector is monotonic, which is ones in every bit from the most significant bit of a denormal   # §8
evidence: §8

### shift_round_convert  (role: instantiates)
mechanism: Converting single to double on load requires adding three exponent bits corresponding to the complement of the exponent high-order bit and padding zeros into the low-order fraction bits, but denormal data must be normalized or held in a non-architected format carrying a tag bit and an unnormalized significand. For a single precision store of a value held normalized but in the single denormal range, Power4 uses the alignment shifter instead of taking the data through the pipeline: store data uses the Add operand input of the multiply-add dataflow, constants are forced into the exponents of the absent multiplier operands so their sum is Emin, and the aligner then right-shifts the significand by the difference of Emin and the exponent of the normalized operand. A double precision store of an unnormalized single takes a prenormalization stall instead.
choices: none
new_choices: none
slots:
  shifter: UNKNOWN (the multiply-add aligner is reused, its structure is not stated)   # §9
  lzc: UNKNOWN
  round: UNKNOWN
parameters: single and double formats in 64-bit FPRs; three exponent bits added on single-to-double conversion   # §3, §9
results: none reported   # §9
errors_and_checks: none
conditions: the technique needs a multiply-add dataflow whose aligner is reachable from the store path, and constants forced into the unused multiplier exponents   # §9
evidence: §3, §9

## new_families
### denormalizing_result_shifter  (domain: fp: floating-point adders, closest: shift_round_convert, why_not: shift_round_convert covers re-aiming the rounder at another format, while this mechanism is the post-normalization right shift of an underflowed intermediate result to Emin together with the pipeline control that makes room for it)
mechanism: Once an intermediate result completes normalization and underflow is detected with the trap disabled, the result is aligned to an exponent equal to Emin and then rounded, which the paper calls denormalization. By then it is too late in the pipeline to use the normalizer, so the design either adds a denormalization unit with a large right shifter fed out of order behind a checkpoint ordering buffer, feeds the result back to an early pipeline stage when no other instruction is present and otherwise flushes the pipeline and re-issues the instruction in non-pipelined mode, stalls a following instruction out of the normalizer and feeds the normalizer output back to its input, or holds the latch feeding the rounder and right-shifts up to 4 bits per cycle until the exponent reaches Emin.
choices: placement: enum['dedicated_unit', 'pipeline_feedback_to_top', 'normalizer_output_feedback', 'small_shifter_at_rounder']; shift_per_cycle_bits: 1..64 by 1; instruction_ordering: enum['out_of_order_checkpoint_buffer', 'flush_and_reissue_nonpipelined', 'stall_until_complete']
results:
| metric | value | unit | technology / device | baseline | condition | page |
| denormalization time | up to 13 | cycles | UNKNOWN node, 1998 S/390 G5 FPU | trapping to software | 4 bits shifted right per cycle at double precision, pipeline stalled until complete | §7 |
evidence: §7

## space_gaps
* a `denormal_detection` choice on the fp adder, fp multiplier and FMA families: register-file tag bits (implied bit, exponent all zeros, exponent all ones, fraction all zeros) versus in-unit exponent decode   # §3, §9
* an `internal_exponent_width_bits` choice on the fp families or on `exponent_path`: Power4 carries 13 exponent bits, two more than the architected double exponent, to hold prenormalized operands below Emin   # §9
* a `prenormalization` choice on the fp adder and FMA families with values for no prenormalization, special cases only, and all operands   # §6, §9
* a bounded-normalization choice on the `lza` family, since the denormal shift bound is an LZA modification rather than a normalizer option   # §8
* the shift vocabulary has no iterative multi-cycle shifter: the 4-bit-per-cycle shift-and-stall denormalizer is not expressible in the single-pass shifter families   # §7

## open_questions
* The scan has no legible page numbers and the total page count is not readable, so every reference is a section reference.
* The OCR of the formulas is unreliable. The normalized and denormal value equations, the multiplier equations for loc1, loc2, X', lzc1, and the LZA equations for V_i and U_i are recorded only in the form the text shows; the exact index condition in `U_i = (i = E_product - E_min)` is UNKNOWN, and "Hmen" in §9 is read as Emin but not confirmed.
* The alignment range of the FMA addend is given only as "a little over 53 bits" greater than the product, with no exact width.
* The base length of a Power4 prenormalization stall is not stated; only the 3 additional cycles per further denormal operand are given.
* No technology node, area figure or frequency is reported anywhere in the paper, so every result row carries an UNKNOWN node.
* The paper names no counter-tree, adder or shifter structure for the Power4 FPU beyond the 108-bit LZA and normalizer, so those slots stay UNKNOWN.
