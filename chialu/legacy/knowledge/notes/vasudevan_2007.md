---
handle: vasudevan_2007
citation: D. P. Vasudevan, P. K. Lala, J. P. Parkerson, "Self-Checking Carry-Select Adder Design Based on Two-Rail Encoding", IEEE Transactions on Circuits and Systems I, vol. 54, pp. 2696-2705, 2007
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary_integer]
authority: incremental
pages_read: 10 / 10
---

## summary
The paper proposes an online self-checking carry-select adder built by cascading 2-bit cells whose speculative sum pairs drive two-rail checkers through simple configuration logic. The implementation detects permanent and transient single stuck-at faults, while double-fault detection is not guaranteed.

## families
### carry_select  (role: extends)
mechanism: Each 2-bit cell duplicates a ripple-carry addition for carry-in 0 and carry-in 1. Self-checking multiplexers select the actual sums/carry and emit complementary carry outputs, while one EX-NOR and direct connections form valid complementary inputs for 2-pair two-rail checkers. Arbitrary widths are formed by cascading the 2-bit cells; intermediate cells omit the final carry multiplexer. # pp.2697-2702
choices:
  block_sizing: uniform   # pp.2701-2702
  duplication: full_duplicate   # p.2702
  select_source: rippled_block_carries   # pp.2699-2701
new_choices:
  checking_granularity: cascaded_2_bit_cells — Each 2-bit section has configuration/checking logic, with output-stage checking for propagated multiplexer faults.   # pp.2697,2700-2701
  checker_input_configuration: direct_pair_plus_exnor_pair — One speculative sum pair is directly complementary; a second complementary pair is formed with an EX-NOR.   # pp.2698-2699
  self_checking_mux_style: four_transmission_gates_plus_inverter — The multiplexer produces complementary outputs that become identical under a fault.   # p.2699
slots:
  block_adder: ripple_carry   # p.2702
parameters: 2-bit component cells; evaluated widths 4, 8, 16, 32, 64, and 128 bits; 64-bit implementation uses thirty-two 2-bit blocks and sixty-five 2-pair two-rail checkers.   # pp.2701-2703
results:
| metric | value | unit | technology / device | baseline | condition | page |
| transistor overhead | 19.51%-20.94% | % | 0.5-μm CMOS / 2007 | adders without built-in self-checking | 4-128-bit adders | p.2701 |
| area overhead | 16.07%-20.67% | % | 0.5-μm CMOS / 2007 | adders without built-in self-checking | 4-128-bit adders | p.2701 |
| layout area | 130 × 92 | μm² | 0.5-μm CMOS / 2007 | none | self-checking 2-bit adder | p.2702 |
| layout area | 2152 × 390 | μm² | 0.5-μm CMOS / 2007 | none | 64-bit self-checking carry-select adder | p.2702 |
| layout area | 2152 × 790 | μm² | 0.5-μm CMOS / 2007 | none | 128-bit self-checking carry-select adder | p.2702 |
| sum propagation delay | 4.3 | ns | 0.5-μm CMOS / 2007 | none | QuickSim II simulation of 64-bit self-checking adder | p.2703 |
| checker delay | 2.9 | ns | 0.5-μm CMOS / 2007 | none | QuickSim II simulation of 64-bit self-checking adder | p.2703 |
errors_and_checks: The design detects permanent and transient single stuck-at faults online at internal carry, sum, EX-NOR, and multiplexer nodes. Primary-input/primary-output faults are excluded, and detection of all double faults is not guaranteed. Valid checker outputs are 01/10; 00/11 signals a fault.   # pp.2697,2700,2704
conditions: Cascaded 2-bit blocks keep checker/configuration logic small and add no delay to normal addition because checking operates independently of the adder path.   # pp.2701,2703-2704
conditions: Larger delay-optimized carry-select blocks require larger multi-pair checkers and more complex configuration logic, so their area overhead can become unacceptably high.   # pp.2703-2704
conditions: The design therefore trades optimal carry-select speed for lower-overhead self-checking operation.   # p.2704
evidence: Sections II-VIII; Figs. 2, 5, 6, 9-16; Tables II and III, pp.2697-2704.

### two_rail_tree  (role: instantiates)
mechanism: A 2-pair two-rail checker receives two complementary input pairs and emits a two-rail output. Output combinations 01 and 10 are valid; 00 and 11 indicate a fault in the checked circuit or checker. The implementation uses eight transistors. # pp.2697-2698
choices:
  tree_arity: 2   # p.2697
  input_code: two_rail   # p.2697
  embedded: true   # pp.2697,2701-2702
new_choices:
  none
slots:
  none
parameters: two input pairs; two output rails; 8-transistor checker.   # pp.2697,2701
results:
| metric | value | unit | technology / device | baseline | condition | page |
| transistor count | 8 | transistors | 0.5-μm CMOS / 2007 | none | 2-pair two-rail checker | p.2701 |
| layout area | 61 × 38 | μm² | 0.5-μm CMOS / 2007 | none | 2-pair two-rail checker | p.2702 |
errors_and_checks: The checker is totally self-checking for the stated single stuck-at fault model when it receives valid complementary input pairs. A nonvalid output code indicates a fault in the circuit or checker.   # pp.2697-2698
conditions: Checkers above four input pairs require unacceptably high checker/configuration overhead for the proposed carry-select application.   # p.2703
evidence: Section II; Figs. 2-3 and 11; pp.2697-2698,2702-2703.

## new_families
none

## space_gaps
* `carry_select` lacks a checker component slot that can be filled by `two_rail_tree`.   # pp.2697-2701
* `carry_select` lacks choices for checker granularity, checker-input configuration, and a self-checking multiplexer implementation.   # pp.2697-2701

## open_questions
* Table III reports width-specific transistor counts and area overheads graphically, but the supplied text explicitly transcribes only the aggregate overhead ranges.
* The paper does not report whether the binary additions are interpreted as signed or unsigned.
