---
handle: dadda_2007
citation: Dadda, "Multioperand Parallel Decimal Adder: A Mixed Binary and BCD Approach", IEEE Transactions on Computers, 2007
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [bcd8421]
authority: incremental
pages_read: 1320-1328 / 9
---

## summary
The paper proposes a multioperand decimal adder that reduces each equal-weight BCD column with binary carry-save compression, converts each binary column sum to decimal, aligns the resulting digits as major partial sums, and performs a final decimal addition (pp.1320-1321). The approach supports large addend counts because the number of major partial sums increases logarithmically with the number of addends (p.1324).

## families
### decimal_multioperand_addition  (role: proposes)
mechanism: Each BCD digit column is reduced independently by full-adder/half-adder compression stages and a final binary CLA. A parallel binary-to-decimal converter transforms each column sum. The converted digits are skewed by decimal weight into two, three, or four Major Partial Sums (MPSs), which are reduced when necessary and passed to a final decimal CLA (pp.1320-1326).
choices:
  reduction_style: binary_tree_then_convert   # pp.1320-1321
  compressor_arity: 3_to_2   # p.1321
  correction_placement: at_root   # pp.1320,1328
new_choices:
  none
slots:
  reduction_tree: csa_tree   # pp.1321-1322
  root_adder: carry_lookahead   # pp.1322-1323
parameters: N=4, 8, 16, and 100 evaluated; operands are eight BCD digits; two MPSs for 2 < N < 12, three for 11 < N < 112, and four for 111 < N < 1112; N=21 and n=5 illustrate the basic scheme (pp.1320-1327)
results:
| metric | value | unit | technology / device | baseline | condition | page |
| compression depth | 2 | stages | UNKNOWN; 2007 | none | N=4 column adder | p.1326 |
| full-adder count | 7 | full adders | UNKNOWN; 2007 | none | N=4 column adder | p.1326 |
| half-adder count | 1 | half adder | UNKNOWN; 2007 | none | N=4 column adder | p.1326 |
| final binary CLA depth | 4 | stages | UNKNOWN; 2007 | none | N=4 column adder | p.1326 |
| compression depth | 6 | stages | UNKNOWN; 2007 | none | N=16 column adder | p.1322 |
| full-adder count | 53 | full adders | UNKNOWN; 2007 | none | N=16 column adder | p.1322 |
| half-adder count | 3 | half adders | UNKNOWN; 2007 | none | N=16 column adder | p.1322 |
| full-adder count | 386 | full adders | UNKNOWN; 2007 | none | N=100 scheme using a few half adders | p.1322 |
| half-adder count | 2 | half adders | UNKNOWN; 2007 | none | N=100 scheme using a few half adders | p.1322 |
| full-adder count | 383 | full adders | UNKNOWN; 2007 | none | N=100 scheme using only full adders except in the last compression stage | p.1323 |
| full-adder delay | 0.20 | ns | STM 0.18 μm standard-cell library; 2007 | none | component characterization | p.1326 |
| full-adder area | 90 | μm² | STM 0.18 μm standard-cell library; 2007 | none | component characterization | p.1326 |
| half-adder delay | 0.15 | ns | STM 0.18 μm standard-cell library; 2007 | none | component characterization | p.1326 |
| half-adder area | 50 | μm² | STM 0.18 μm standard-cell library; 2007 | none | component characterization | p.1326 |
| initial binary-addition depth | 6 | stages | UNKNOWN; 2007 | 14 stages for the nonspeculative tree of [11] | N=16 | p.1328 |
errors_and_checks: The architecture computes an exact decimal sum; the paper reports no approximation error, fault model, or concurrent checker (pp.1320-1321).
conditions: The approach targets multioperand BCD addition and becomes especially applicable for a large number of addends (pp.1320,1328). The final array contains two MPSs through N=11, three through N=111, and four through N=1111 (pp.1321,1324). The final decimal-adder delay and area depend on operand length n, whereas the preceding column structures depend on N (p.1327). The paper reports that the nonspeculative comparison design has much greater area, but the binary sections are only presumed comparable (p.1328).
evidence: Sections 2, 3, 5-7; Figs. 1-4 and 8-10; Tables 1-2 (pp.1320-1328).

### binary_decimal_conversion  (role: extends)
mechanism: A Nicoud conversion cell computes S=2di+bi. The cell emits S with bo=0 when S<10 and emits S-10 with bo=1 otherwise. A linear cell array divides a binary integer by 10, producing a BCD remainder and a binary quotient; successive shorter arrays repeat the operation to generate all decimal digits (pp.1323-1324).
choices:
  direction: bin_to_dec   # pp.1323-1324
  structure: combinational_cell_array   # pp.1323-1324
new_choices:
  none
slots:
  none
parameters: converter designs cover N=2 through N=711; Fig. 7 shows designs through N=111; each design records c total cells and d critical-path cells (p.1324)
results:
| metric | value | unit | technology / device | baseline | condition | page |
| basic-cell delay | 0.12 | ns | STM 0.18 μm standard-cell library; 2007 | none | BD conversion cell | p.1326 |
| basic-cell area | 168 | μm² | STM 0.18 μm standard-cell library; 2007 | none | BD conversion cell | p.1326 |
| converter size | 2 | cells | STM 0.18 μm standard-cell library; 2007 | none | N=4 column sum | p.1326 |
| converter critical path | 2 | cells | STM 0.18 μm standard-cell library; 2007 | none | N=4 column sum | p.1326 |
errors_and_checks: Each array stage produces the exact quotient and remainder of division by 10; no fault-detection mechanism is reported (p.1323).
conditions: The three highest cells can be replaced by wires when their bits directly form the leading BCD digit (p.1323). The direct bi-to-Ao connection adds no cell delay between adjacent converter columns, so output position does not lengthen the critical path (p.1324). Each converter scheme covers an interval of N values rather than only its marked maximum (p.1324).
evidence: Section 4; Figs. 5-7; Table 1 (pp.1323-1326).

### bcd_direct_addition  (role: instantiates)
mechanism: A decimal carry-lookahead adder combines the final two MPSs. Three MPSs are first compressed into two through binary reduction and one or two BD cells, which avoids cascading two decimal adders (pp.1324-1326).
choices:
  digit_code: bcd8421   # pp.1320-1322
  carry_scheme: full_lookahead   # pp.1324,1326
new_choices:
  none
slots:
  none
parameters: eight decimal digits in the evaluated complete adders; the parallel decimal adder has one stage per digit (pp.1325-1326)
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay | 621 | ps/digit | Dynamic CMOS 0.25 μm; 2006 | You et al. decimal CLA | cited comparison design | p.1327 |
errors_and_checks: The final adder preserves exact BCD addition; no error-detection mechanism is reported (pp.1324-1326).
conditions: A direct decimal CLA suffices when the converter produces two MPSs (p.1324). Three MPSs are reduced to two because the paper considers one reduction plus one decimal CLA more convenient in cost and speed than two cascaded decimal adders (p.1324).
evidence: Sections 5-7; Figs. 8-10; Tables 1-2 (pp.1324-1328).

## new_families
none

## space_gaps
* `decimal_multioperand_addition` lacks a converter slot accepting `binary_decimal_conversion`, although binary-to-decimal conversion is a defining stage of the proposed reduction path (pp.1320,1323-1324).
* `decimal_multioperand_addition` lacks a choice describing independent equal-decimal-weight column reduction before MPS alignment (pp.1320-1321).

## open_questions
* The numerical cells of Tables 1 and 2 are absent from the supplied document text, so the reported complete-adder delay/area values for N=4, 8, 16, and 100 remain UNKNOWN (pp.1326-1327).
* The final decimal CLA's correction placement and digit-level circuit are not specified because the paper adopts an existing decimal adder (pp.1324,1326).
