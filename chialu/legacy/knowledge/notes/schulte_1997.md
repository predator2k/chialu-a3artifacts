---
handle: schulte_1997
citation: M. J. Schulte, J. E. Stine, "Symmetric Bipartite Tables for Accurate Function Approximation", 13th IEEE Symposium on Computer Arithmetic, pp. 175-183, 1997
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [fixed12, fixed16, fixed24, normalized_binary_fp_significand]
authority: landmark
pages_read: 175-183 / 9
---

## summary
The paper proposes the Symmetric Bipartite Table Method (SBTM), which approximates elementary functions with two parallel table lookups and exploits coefficient symmetry to halve one table. The method provides closed-form coefficients, a bounded-error construction for faithful rounding, and lower memory requirements than conventional and earlier bipartite tables. # pp.175-182

## families
### bipartite  (role: proposes)
mechanism: The input x is partitioned into x0/x1/x2. One table supplies a0(x0,x1), while a second supplies a1(x0,x2), and their outputs form a carry-save or borrow-save approximation. The coefficients derive from a two-term Taylor expansion about x0+x1+δ2, with x1 replaced by midpoint δ1 in the derivative term. Complement symmetry across the most significant bit of x2 halves the second table's word count and removes its stored sign bit. A carry-propagate adder produces a two's-complement result, or the redundant output is directly Booth encoded. # pp.176-178
choices:
  symmetric: true   # pp.178-179
new_choices:
  input_partition: n0/n1/n2 — allocates input bits among x0, x1, and x2 table indices   # p.176
  guard_bits: g=2 or g=3 — controls coefficient-rounding error and table word widths in the demonstrated constructions   # pp.177-178,182
  output_form: twos_complement_cpa | carry_save_or_borrow_save_for_booth — selects final CPA conversion or direct Booth encoding   # pp.175-176
slots:
  none
parameters: Input width n=n0+n1+n2; output width p may differ from n; first table 2^(n0+n1) words by p0 bits; symmetric second table 2^(n0+n2-1) words by p1-1 stored bits. The 24-bit cos(x) example uses n0=n1=n2=8, p=24, and g=2. The faithful reciprocal construction uses j+2 input bits, j output bits, and g=3. # pp.176,178,182
results:
| metric | value | unit | technology / device | baseline | condition | page |
| memory compression | 5.6 to 15.3 | times less memory | UNKNOWN; 1997 | standard table lookup | 12-bit operands; range across evaluated functions | p.179 |
| memory compression | 15.0 to 41.7 | times less memory | UNKNOWN; 1997 | standard table lookup | 16-bit operands; range across evaluated functions | p.179 |
| memory compression | 99.1 to 273.9 | times less memory | UNKNOWN; 1997 | standard table lookup | 24-bit operands; range across evaluated functions | p.179 |
| second-table storage | 2^15 words by 9 bits | table dimensions | UNKNOWN; 1997 | nonsymmetric 2^16-word by 10-bit a1 table | 24-bit cos(x), n0=n1=n2=8, g=2 | p.178 |
| memory compression | 2.5 to 5.2 | times less memory | UNKNOWN; 1997 | 3-block method of [9] | 24-bit 1/x, ln(x), log2(x), and 2^x approximations; maximum error less than 2^-25 | pp.181-182 |
| reciprocal-table memory | 61,440 | bits | UNKNOWN; 1997 | 81,920 bits for method [10] | j=15, k=5 reciprocal approximation | p.182 |
| reciprocal-table memory reduction | 25 | % | UNKNOWN; 1997 | method [10] | j=15, k=5 reciprocal approximation | p.182 |
| symmetric-table reduction | 2 | factor | UNKNOWN; 1997 | nonsymmetric bipartite second table | conditional address/output complementation for a1(x0,x2) | pp.178,182 |
errors_and_checks: The accuracy contract is faithful rounding: the true value and approximation differ by at most one ulp. Four bounded errors cover Taylor truncation, derivative-term substitution, coefficient rounding, and final-result rounding; their sum must be at most 2^-pf. Generated tables were exhaustively tested over all possible inputs for the stated operand widths. # pp.177-181
conditions: The method applies to differentiable functions and can accommodate domains outside 0≤x<1 by accounting for known input bits. # pp.178-179 The memory benefit depends on |f''(ξ2)|, so 1/x and log2(x) obtain lower compression than √x, 2^x, and the evaluated trigonometric functions. # p.179 The design adds a CPA or Booth encoder after the parallel lookups, and symmetry adds conditional exclusive-or logic. # pp.175-176,178 The comparison method in [10] permits easier Booth encoding and avoids the symmetry logic, while SBTM uses less memory and supports a wider function set. # p.182
evidence: Equations 1 and 4-18; Figures 2-4; Tables 1-7; Sections 2-4, pp.176-182.

## new_families
none

## space_gaps
* The `bipartite` family lacks an output-combiner slot for a carry-propagate adder or direct Booth encoder, although this selection changes the delivered representation and downstream hardware. # pp.175-176
* The `bipartite` family lacks input-partition and guard-bit choices for n0/n1/n2/g, although these parameters determine table dimensions and the faithful-rounding bound. # pp.176-178
* The `bipartite` family lacks an accuracy-contract choice for faithful rounding within one ulp. # pp.177-178

## open_questions
* The carry-propagate adder topology is unspecified. # pp.175-176
* The paper reports no implementation technology, area, power, or measured access/critical-path delay.
