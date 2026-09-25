---
handle: vazquez_2014
citation: Vazquez, Antelo, Bruguera, "Fast Radix-10 Multiplication Using Redundant BCD Codes", IEEE Transactions on Computers, 2014
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [bcd, decimal64, decimal128]
authority: incremental
pages_read: 14 / 14
---

## summary
The paper proposes a combinational radix-10 BCD multiplier that generates signed partial products in redundant XS-3, recodes them to ODDS, and reduces them with binary carry-save hardware (pp.1-4). Synthesized 16 × 16-digit and 34 × 34-digit implementations support Decimal64 and Decimal128 significand widths (pp.10-12).

## families
### parallel_decimal_multiplication  (role: proposes)
mechanism: A signed-digit radix-10 recoder maps each multiplier digit to [-5,5]. Carry-free logic precomputes 0X through 5X in XS-3; bit inversion produces negative multiples. A constant correction recodes the XS-3 partial products to ODDS. A binary CSA/compressor tree reduces the ODDS rows, concurrent carry counting supplies the decimal ×6 correction, and a BCD carry-propagate adder converts the final two words to a nonredundant product (pp.2-10).
choices:
  multiplier_recoding: sd_radix10_m5_p5   # pp.2,4
  internal_digit_code: xs3_odds   # pp.2-4
  pp_generation: precomputed_multiples_mux   # pp.4-5
new_choices:
  multiplicand_multiple_set: 0X_to_5X — identifies the positive XS-3 multiples selected after signed-digit recoding   # pp.4-5
  xs3_odds_conversion: constant_correction_in_reduction_tree — records how XS-3 partial products become ODDS digits   # pp.6-7
slots:
  reduction_tree: csa_tree   # pp.4,7-10
  final_adder: bcd_direct_addition [outside slot domain]   # pp.5,10
parameters: 16 × 16 and 34 × 34 decimal digits; d+1 partial products; 17:2 CSA with m=14 for d=16; 35:2 CSA with m=31 for d=34; combinational latency 1 cycle; throughput 1 multiplication/cycle   # pp.4,9-12
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay | 41.5 | FO4 | 90nm CMOS standard-cell / 2014 | 53 × 53-bit Booth radix-4: 31.1 FO4 | proposed 16 × 16-digit combinational multiplier | p.12 |
| area | 44200 | NAND2 | 90nm CMOS standard-cell / 2014 | 53 × 53-bit Booth radix-4: 34000 NAND2 | proposed 16 × 16-digit combinational multiplier | p.12 |
| delay | 56 | FO4 | 90nm CMOS standard-cell / 2014 | 53 × 53-bit Booth radix-4: 31.1 FO4 | proposed 34 × 34-digit combinational multiplier | p.12 |
| area | 120600 | NAND2 | 90nm CMOS standard-cell / 2014 | 53 × 53-bit Booth radix-4: 34000 NAND2 | proposed 34 × 34-digit combinational multiplier | p.12 |
| area improvement | 20-35% | less area | 90nm CMOS standard-cell / 2014 | fastest compared BCD implementations at a given target delay | 16 × 16-digit multiplier area-delay space | p.13 |
| latency ratio | about 7 | times faster | 90nm CMOS standard-cell / 2014 | sequential implementation [9] | proposed 16 × 16-digit multiplier | p.13 |
| area ratio | 2.5 | times more area | 90nm CMOS standard-cell / 2014 | sequential implementation [9] | proposed 16 × 16-digit multiplier | p.13 |
errors_and_checks: Exact BCD integer/fixed-point product; RTL models were functionally verified with comprehensive random test vectors, but no coverage count is reported   # pp.4,11
conditions: XS-3 permits constant-time 3X generation and bit-inversion negation; ODDS permits binary CSA reduction without invalid-code correction (pp.2-4). The fully parallel Decimal128 implementation has high area/power, so the paper considers a sequential commercial implementation more realistic (p.13).
evidence: Fig. 1 and Sections 3-6 (pp.4-10); Tables 4-5 and Figs. 9-10 (pp.11-13).

### decimal_multioperand_addition  (role: extends)
mechanism: Each ODDS digit column is reduced by a regular binary CSA tree. A counter computes the number Wi of binary carry-outs crossing the 4-bit digit boundary, and Wi × 6 corrects the difference between binary weight 16 and decimal weight 10. Binary and decimal compressor stages reduce the corrected result to BCD operand B and excess-6 BCD operand A (pp.7-10).
choices:
  reduction_style: binary_csa_with_concurrent_carry_count_correction [outside domain]   # pp.7-8
  compressor_arity: higher   # pp.7-10
  correction_placement: at_root   # pp.7-9
new_choices:
  correction_evaluation: concurrent_carry_count — counts interdigit binary carries while the CSA tree reduces operands   # pp.7-8
slots:
  reduction_tree: csa_tree   # pp.7-10
  root_adder: bcd_direct_addition [outside slot domain]   # pp.9-10
parameters: arbitrary input count at the architectural level; maximum column heights 17 and 35 for Decimal64 and Decimal128; one correction digit for Decimal64 and two for Decimal128   # pp.4,8-10
results:
| metric | value | unit | technology / device | baseline | condition | page |
| PPR-tree delay | 25.5 | FO4 | technology-independent LE model / 2014 | none | 16 × 16-digit multiplier | p.11 |
| PPR-tree area | 11700 | NAND2 | technology-independent LE model / 2014 | none | 16 × 16-digit multiplier | p.11 |
| PPR-tree delay | 32.3 | FO4 | technology-independent LE model / 2014 | none | 34 × 34-digit multiplier | p.11 |
| PPR-tree area | 50000 | NAND2 | technology-independent LE model / 2014 | none | 34 × 34-digit multiplier | p.11 |
errors_and_checks: Exact decimal correction is T = 6 × ΣWi × 10^i   # p.8
conditions: Binary arithmetic applies within ODDS digit bounds; every carry crossing a 4-bit digit boundary requires a ×6 correction (pp.4,7-8). Counter size and ×6 implementation depend on column height and decimal precision (pp.8-10).
evidence: Section 5, Figs. 5-8, and Equations (14)-(22) (pp.7-10).

### bcd_direct_addition  (role: instantiates)
mechanism: The final 2d-digit BCD Quaternary Tree adder computes decimal carries with a prefix tree. Each digit computes conditional sums for carry-in 0 and 1 outside the critical path, subtracts 6 when the conditional carry is one, and selects the result with a final 2:1 multiplexer level (p.10).
choices:
  digit_code: bcd8421   # pp.4-5,10
  correction_placement: direct_decimal_carry_logic   # p.10
  carry_scheme: full_lookahead   # p.10
new_choices:
  binary_topology: hybrid_parallel_prefix_carry_select — identifies the final BCD Quaternary Tree structure   # pp.5,10
slots:
  digit_adder: UNKNOWN
parameters: 32 digits for Decimal64; 68 digits for Decimal128; two conditional 4-bit digit sums per position   # pp.5,10
results:
| metric | value | unit | technology / device | baseline | condition | page |
| decimal-adder delay | 11.5 | FO4 | technology-independent LE model / 2014 | none | 32-digit final adder | p.11 |
| decimal-adder area | 2400 | NAND2 | technology-independent LE model / 2014 | none | 32-digit final adder | p.11 |
| decimal-adder delay | 13.6 | FO4 | technology-independent LE model / 2014 | none | 68-digit final adder | p.11 |
| decimal-adder area | 4600 | NAND2 | technology-independent LE model / 2014 | none | 68-digit final adder | p.11 |
errors_and_checks: Exact conversion from excess-6 BCD operand A and BCD operand B to a nonredundant BCD product   # pp.5,10
conditions: Each input digit sum must remain in [0,18], and operand A is supplied in excess-6 to simplify decimal-carry generation (pp.5,9).
evidence: Section 6 and Fig. 1 (pp.4-5,10); Table 4 (p.11).

## new_families
none

## space_gaps
* The `parallel_decimal_multiplication.final_adder` slot excludes decimal-adder families, although the implemented final converter is `bcd_direct_addition` (pp.5,10).
* `decimal_multioperand_addition.reduction_style` lacks binary CSA reduction with concurrent carry-count correction (pp.7-10).

## open_questions
* The paper does not identify the binary prefix topology selected for the final BCD Quaternary Tree adder (p.10).
* The synthesis comparison does not report power or energy for the proposed implementations (pp.11-13).
