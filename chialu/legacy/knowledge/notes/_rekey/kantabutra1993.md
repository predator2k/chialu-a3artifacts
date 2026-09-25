---
handle: kantabutra1993
citation: V. Kantabutra, "Designing Optimum One-Level Carry-Skip Adders", IEEE Transactions on Computers, vol. 42, no. 6, pp. 759-764, 1993.
actual_citation: Vitit Kantabutra, "Accelerated Two-Level Carry-Skip Adders—A Type of Very Fast Adders", IEEE Transactions on Computers, vol. 42, no. 11, pp. 1389-1393, 1993.
status: mismatch
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary60, fp64_mantissa]
authority: incremental
pages_read: 5 / 5
---

## summary
The document proposes an accelerated two-level carry-skip adder whose section sizes are bimodal while block sizes within each section are unimodal. A 60-b static CMOS instance has an approximately 12.6 ns simulated delay in 2-μm technology. (pp.1389-1393)

## families
### carry_skip  (role: extends)
mechanism: The adder partitions bit positions into blocks and groups disjoint blocks into sections. The less-significant ascending half uses increasingly large sections whose blocks also increase toward the center; the more-significant descending half reverses both orders. Multiplexers provide block/section skip paths, including extra direct paths that prevent incoming carries from traversing an unfavorable sequence of blocks. A constructive search grows the largest adder satisfying a specified carry-delay bound from two equal central blocks. (pp.1389-1393)
choices:
  block_sizing: sectionwise_unimodal [outside domain]   # pp.1389-1391
  skip_levels: 2   # pp.1389-1391
  skip_gate: mux   # pp.1390-1392
new_choices:
  section_sizing: bimodal — sections grow toward the middle and shrink toward the ends   # pp.1389,1391
  block_order_within_section: ascending_or_descending — blocks increase in the ascending half and decrease in the descending half   # pp.1390-1391
  direct_section_paths: true — extra paths bypass unfavorable block sequences within selected sections   # pp.1390,1392-1393
slots:
  block_adder: ripple_carry   # pp.1389-1390
parameters: 60-b operands; 2-μm static CMOS; two carry-skip levels; 11 ns carry-delay design bound; less than 1.6 ns final-sum delay; approximately 12.6 ns total simulated delay   # pp.1389-1393
results:
| metric | value | unit | technology / device | baseline | condition | page |
| simulated total delay | approximately 12.6 | ns | 2-μm CMOS / 1993 | 66-b adder in [5]: 58 ns | 60-b adder | p.1389 |
| ripple-cell carry delay | 0.8 | ns | 2-μm CMOS / 1993 | none | simulated low-level component | p.1390 |
| regular-sized mux delay | 1.1 | ns | 2-μm CMOS / 1993 | none | simulated mux data path | p.1390 |
| three-input mux select-circuit delay | less than 3.6 | ns | 2-μm CMOS / 1993 | six-cell ripple delay: 0.8 × 6 ns | simulated select circuit | p.1391 |
| final-sum delay after most-significant carry input | less than 1.6 | ns | 2-μm CMOS / 1993 | none | simulated components | p.1391 |
| nucleus carry delay | 10.7 | ns | 2-μm CMOS / 1993 | specified limit: 11 ns | two 6-b central blocks | p.1391 |
errors_and_checks: none
conditions: The accelerated design can exceed the speed of conventional two-level carry-skip adders at the cost of slightly more skip circuitry. (pp.1389-1390) An anonymous referee reports that regular-style two-level adders designed with Turrini’s method can attain comparable speeds. (p.1389) The wire-delay argument assumes reasonable layouts and states that metal delay is unlikely to be significant in 2-μm technology or smaller technologies; selected section-end muxes may require slightly larger transistors. (p.1393)
evidence: Abstract; §§I-IV; Figs. 1-6; component simulations in §III-C and §III-D; long-wire discussion in §V, pp.1389-1393.

## new_families
none

## space_gaps
* `carry_skip.block_sizing` lacks a value for blocks that are unimodal within separately sized sections. (pp.1389-1391)
* `carry_skip` lacks a section-sizing choice for the bimodal distribution of section widths. (pp.1389,1391)
* `carry_skip` lacks a choice for extra direct carry paths across selected portions of a section. (pp.1390,1392-1393)

## open_questions
* The document calls the constructed 60-b adder “just about” maximal for the delay bound because unequal central blocks are not formally excluded, so exact global optimality is not established. (p.1392)
* The document does not report area, power, transistor count, layout area, or fabricated-silicon measurements.
