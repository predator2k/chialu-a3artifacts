---
handle: hickmann_2007
citation: Hickmann, Krioukov, Schulte, Erle, "A Parallel IEEE P754 Decimal Floating-Point Multiplier", IEEE International Conference on Computer Design (ICCD), 2007
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [decimal64]
authority: landmark
pages_read: 296-303 / 8
---

## summary
The paper presents a fully parallel IEEE P754 decimal64 floating-point multiplier with parallel significand multiplication, early shift calculation, rounding, and exception handling (p.296-298). An 11-stage implementation has 11-cycle latency and one-result-per-cycle throughput, compared with 25-cycle latency and one result every 21 cycles for the sequential baseline (p.296, p.302-303).

## families
### parallel_decimal_multiplication  (role: extends)
mechanism: The fixed-point core generates BCD-4221 encodings of the 1x through 5x multiplicand multiples, uses signed-digit recoding to select 16 positive or negative partial products in parallel, and adds a corrective 1x partial product when the multiplier MSD exceeds 5. A modified binary CSA tree reduces the partial products to BCD-8421 carry/sum vectors, followed by a direct decimal carry-propagate adder (p.298).
choices:
  multiplier_recoding: sd_radix10_m5_p5   # p.298
  internal_digit_code: bcd4221   # p.298
  pp_generation: precomputed_multiples_mux   # p.298
new_choices:
  output_digit_code: bcd8421 — encoding used for the CSA carry/sum and 32-digit product   # p.298
slots:
  reduction_tree: csa_tree   # p.298
  final_adder: bcd_direct_addition [digit_code=bcd8421, carry_scheme=full_lookahead]   # p.298
parameters: two 16-digit integer significands; 16 parallel partial products; 32-digit BCD result; multiples {1x...5x}   # p.298
results: none
errors_and_checks: More than 500,000 random fixed-point cases, including hand-picked corner cases, were simulated (p.302).
conditions: The BCD-4221 encoding permits all 16 binary patterns as valid decimal values, so a slightly modified binary CSA tree can reduce the partial products (p.298).
evidence: §3.1, Figure 1, Table 3 (p.297-298, p.302)

### bcd_direct_addition  (role: instantiates)
mechanism: A high-speed direct decimal carry-propagate adder combines the BCD-8421 carry and partial-sum vectors from the CSA tree. A Kogge-Stone network produces carries between decimal digits (p.298).
choices:
  digit_code: bcd8421   # p.298
  correction_placement: direct_decimal_carry_logic   # p.298
  carry_scheme: full_lookahead   # p.298
new_choices:
  none
slots:
  digit_adder: parallel_prefix [topology=kogge_stone]   # p.298
parameters: 32 decimal digits   # p.298
results: none
errors_and_checks: none
conditions: The direct decimal adder operates after the partial products have been reduced to BCD-8421 carry/sum vectors (p.298).
evidence: §3.1 (p.298)

### parallel_prefix  (role: instantiates)
mechanism: The terminal direct decimal carry-propagate adder uses a Kogge-Stone network to produce carries between decimal digits (p.298).
choices:
  topology: kogge_stone   # p.298
new_choices:
  none
slots:
  none
parameters: 32 decimal digits; other topology parameters UNKNOWN   # p.298
results: none
errors_and_checks: none
conditions: The network carries decimal-digit carry signals rather than being described as a standalone binary adder (p.298).
evidence: §3.1 (p.298)

### decimal_encoding_codec  (role: instantiates)
mechanism: Each IEEE P754 decimal64 operand is decoded from DPD into a sign, exponent, flags, and a BCD significand before multiplication. The rounded BCD result is re-encoded into DPD and assembled into IEEE P754 format (p.297-298).
choices:
  significand_encoding: dpd   # p.297-298
  codec_placement: inside_operation   # p.297-298
new_choices:
  none
slots:
  none
parameters: decimal64; p=16 digits; unbiased exponent range [−383, 384]; bias 398   # p.297
results: none
errors_and_checks: none
conditions: The design accepts and produces IEEE P754 decimal64 values with DPD-encoded significands (p.297-298).
evidence: §2, §3, Figure 1 (p.297-298)

## new_families
### decimal_fp_multiplication  (domain: decimal: decimal misc, closest: decimal_fma, why_not: decimal_fma requires a*b+c, while this mechanism implements a*b without an addend)
mechanism: Two decimal64 operands are decoded from DPD, and their 16-digit significands are multiplied by a parallel fixed-point decimal multiplier. Operand leading-zero counts estimate a left shift and exponent in parallel with multiplication. The 32-digit product is shifted, split into truncated/fractional fields, and rounded by selecting between the truncated result and its increment. Exception logic handles NaN/infinity/zero/overflow/underflow, and the result is encoded to DPD (p.297-301).
choices: pipeline_stages: Int[0..12:1]; fixed_point_core: {parallel_decimal_multiplication}; early_shift_calculation: {operand_lzd_sum}; rounding: {dual_candidate_select}; subnormal_handling: {trap_to_software, hardware_right_left_shifter}; nan_passthrough: {operand_force_one}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay / FO4 / cells / area | 4440 / 80.7 / 322,493 / 651,435 | ps / FO4 / Cells / µm2 | LSI Logic gflxp 0.11 µm CMOS / 2007 | sequential [14] | combinational | p.302 |
| delay / FO4 / cells / area | 4420 / 80.4 / 334,400 / 675,488 | ps / FO4 / Cells / µm2 | LSI Logic gflxp 0.11 µm CMOS / 2007 | sequential [14] | 1 stage | p.302 |
| delay / FO4 / cells / area | 2360 / 42.9 / 349,429 / 705,846 | ps / FO4 / Cells / µm2 | LSI Logic gflxp 0.11 µm CMOS / 2007 | sequential [14] | 2 stages | p.302 |
| delay / FO4 / cells / area | 1810 / 32.9 / 364,594 / 736,479 | ps / FO4 / Cells / µm2 | LSI Logic gflxp 0.11 µm CMOS / 2007 | sequential [14] | 3 stages | p.302 |
| delay / FO4 / cells / area | 1540 / 28.0 / 372,082 / 751,605 | ps / FO4 / Cells / µm2 | LSI Logic gflxp 0.11 µm CMOS / 2007 | sequential [14] | 4 stages | p.302 |
| delay / FO4 / cells / area | 1310 / 23.8 / 364,829 / 736,954 | ps / FO4 / Cells / µm2 | LSI Logic gflxp 0.11 µm CMOS / 2007 | sequential [14] | 5 stages | p.302 |
| delay / FO4 / cells / area | 1140 / 20.7 / 367,588 / 742,527 | ps / FO4 / Cells / µm2 | LSI Logic gflxp 0.11 µm CMOS / 2007 | sequential [14] | 6 stages | p.302 |
| delay / FO4 / cells / area | 1090 / 19.8 / 376,199 / 759,922 | ps / FO4 / Cells / µm2 | LSI Logic gflxp 0.11 µm CMOS / 2007 | sequential [14] | 7 stages | p.302 |
| delay / FO4 / cells / area | 980 / 17.8 / 399,636 / 807,264 | ps / FO4 / Cells / µm2 | LSI Logic gflxp 0.11 µm CMOS / 2007 | sequential [14] | 8 stages | p.302 |
| delay / FO4 / cells / area | 930 / 16.9 / 395,953 / 799,825 | ps / FO4 / Cells / µm2 | LSI Logic gflxp 0.11 µm CMOS / 2007 | sequential [14] | 9 stages | p.302 |
| delay / FO4 / cells / area | 880 / 16.0 / 409,156 / 826,495 | ps / FO4 / Cells / µm2 | LSI Logic gflxp 0.11 µm CMOS / 2007 | sequential [14] | 10 stages | p.302 |
| delay / FO4 / cells / area | 850 / 15.5 / 412,795 / 833,845 | ps / FO4 / Cells / µm2 | LSI Logic gflxp 0.11 µm CMOS / 2007 | sequential [14] | 11 stages | p.302 |
| delay / FO4 / cells / area | 820 / 14.9 / 427,094 / 862,729 | ps / FO4 / Cells / µm2 | LSI Logic gflxp 0.11 µm CMOS / 2007 | sequential [14] | 12 stages | p.302 |
| delay / FO4 / cells / area | 850 / 15.45 / 117,627 / 237,607 | ps / FO4 / Cells / µm2 | LSI Logic gflxp 0.11 µm CMOS / 2007 | reference [14] | sequential; 25-cycle latency; one result every 21 cycles | p.302 |
| latency | 11 | cycles | LSI Logic gflxp 0.11 µm CMOS / 2007 | 25 cycles, sequential [14] | 11-stage parallel design | p.296 |
| throughput | 1 | result per cycle | LSI Logic gflxp 0.11 µm CMOS / 2007 | one multiplication every 21 cycles, sequential [14] | 11-stage parallel design | p.296, p.302 |
| area increase | 371% | percent | LSI Logic gflxp 0.11 µm CMOS / 2007 | sequential [14] | 11-stage parallel design | p.296, p.303 |
evidence: Figure 1; §3.2-3.5; Tables 1-3; §4 (p.297-303)

## space_gaps
* The vocabulary lacks a decimal floating-point multiplication family distinct from decimal_fma (p.296-303).
* `parallel_decimal_multiplication.internal_digit_code` cannot express BCD-4221 partial products followed by BCD-8421 carry/sum outputs (p.298).
* `bcd_direct_addition` lacks a choice describing the Kogge-Stone topology of its interdigit carry network (p.298).
* A decimal floating-point multiplier needs a subnormal-handling choice for trap-to-software versus a hardware right-left barrel shifter (p.300).

## open_questions
* Table 2 labels one implementation “1 Stages”; the intended distinction from the combinational implementation is not explained (p.302).
* The stated 371% area increase is not directly reconciled with the Table 2 area values of 833,845 µm2 and 237,607 µm2 (p.302-303).
* The exact IEEE P754 draft revision used for compliance is not identified (p.296-297).
