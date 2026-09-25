---
handle: bewick1994#s04
parent: bewick1994
citation: 'G. W. Bewick, "Fast Multiplication: Algorithms and Implementation", PhD dissertation, Stanford University, CSL-TR-94-617, 1994'
chapter: Adders for Multiplication
pdf_pages: 55-81
status: ok
kind: thesis_chapter
unit_classes: [BINARY_ALU]
formats: [binary]
authority: thesis
pages_read: 27 / 27
---

## summary
The chapter defines carry generate/propagate algebra and presents 64-bit conventional carry-lookahead and modified Ling adders optimized for ECL. The modified Ling adder removes one NOR-equivalent stage while retaining comparable gate count/wiring. Specialized full-length and short-length 3M generators reduce Booth 3 multiplier hardware and latency.

## families
### carry_lookahead  (role: instantiates)
mechanism: Sixteen uniform four-bit groups compute group generate/propagate signals and local carries. A two-stage global lookahead network combines the group signals with the carry-in to produce group carries and c64. Shannon expansion moves the late global carry to a fast path through each output stage.   # p.58, p.60-p.65
choices:
  group_size: 4   # p.58
  levels: 2   # p.62
  intergroup_carry: lookahead   # p.58
  block_sizing: uniform   # p.58
new_choices:
  logic_polarity: negative_data_positive_carry — A/B/S use negative logic while carry-in/carry-out use positive logic   # p.58
  circuit_mapping: ecl_nor_wire_or — group/lookahead equations are arranged for NOR gates, complex ECL gates, and wire-OR connections   # p.57, p.62
slots:
  none
parameters: 64-bit operands; 16 groups; 4 bits/group; four-bit supergroups   # p.58, p.62-p.65
results:
| metric | value | unit | technology / device | baseline | condition | page |
| critical-path depth | 4 NOR and 1 EXCLUSIVE-OR equivalent stages | logic stages | ECL | none | 64-bit CLA example | p.65 |
| global carry-lookahead depth | 2 | stages | ECL | none | group G/P to group carries | p.62 |
| maximum gate fan-in | 4 | inputs | ECL | none | second-stage carry circuits | p.65 |
| maximum wire-OR size | 5 | outputs | ECL | none | second-stage carry circuits | p.65 |
errors_and_checks: none
conditions: ECL favors the product-of-sums/NOR and wire-OR realization because its NOR/OR gates are faster, smaller, and lower-power than NAND/AND gates.   # p.57
conditions: The output stage minimizes the carry-to-output delay because the global carry normally arrives after locally computed signals.   # p.60-p.61
conditions: The ideas apply to technologies other than ECL, although the circuits are specifically tuned for ECL.   # p.81
evidence: Sections 3.1-3.2; Figures 3.1-3.6; Equations 3.1-3.13.

### conditional_sum  (role: extends)
mechanism: The chapter states that the 64-bit CLA combines elements of conventional carry-lookahead, canonic, and conditional-sum adders, but it does not identify the conditional-sum recursion or selection structure separately.   # p.65
choices:
  base_block_width: UNKNOWN   # p.65
  mux_style: UNKNOWN   # p.65
  selection_radix: UNKNOWN   # p.65
new_choices:
  none
slots:
  none
parameters: UNKNOWN   # p.65
results: none
errors_and_checks: none
conditions: The chapter does not specify which gates or connections constitute the conditional-sum contribution.   # p.65
evidence: Section 3.2.3.

### ling_prefix  (role: instantiates)
mechanism: Four-bit groups replace conventional G/P signals with Ling pseudo-carry H/I signals. H is computed directly from operand bits in one INVERT-AND-OR stage plus a wire-OR, and the existing hierarchical lookahead structure combines H/I like G/P. Each output group recovers the true carry from the returned pseudo-carry and a locally available inclusive-OR propagate signal.   # p.65, p.68-p.74
choices:
  pseudo_carry_group: 4   # p.65, p.71
  topology: UNKNOWN   # p.71-p.72
  sum_recovery: recovered_carry_shannon_output_stage [outside domain]   # p.73-p.74
  order: UNKNOWN   # p.68-p.74
new_choices:
  group_propagate_form: shifted_product_I — I uses propagate terms whose indices are shifted relative to the group range   # p.71
  mixed_signal_polarity: positive_H_negative_I — the first lookahead layer accepts positive H and negative I   # p.71-p.73
slots:
  none
parameters: 64-bit operands; 16 four-bit Ling groups   # p.67, p.72
results:
| metric | value | unit | technology / device | baseline | condition | page |
| group pseudo-generate availability | 1 | stage earlier | ECL | conventional group G | four-bit group | p.68 |
| critical-path depth | 3 NOR and 1 EXCLUSIVE-OR stages | logic stages | ECL | 4 NOR and 1 EXCLUSIVE-OR stages | 64-bit modified Ling versus CLA | p.74 |
| gate-count difference | very close | qualitative | ECL | 64-bit CLA | modified Ling implementation | p.74 |
| wire-length difference | very close | qualitative | ECL | 64-bit CLA | modified Ling implementation | p.74 |
| adder speed | faster | qualitative | ECL | 64-bit CLA | comparable gate counts/wire lengths | p.74 |
errors_and_checks: The identity G = p+H requires inclusive-OR propagation; the exclusive-OR definition of p does not work.   # p.68
conditions: H can be produced in one stage plus a wire-OR from negative-logic operands.   # p.69
conditions: A direct one-stage G implementation would require gates with up to 5 inputs and a wire-OR joining 15 outputs.   # p.69
conditions: The unavailable complement of H and the negative-only fast I require a NOR circuit with one inverting input and one to three non-inverting inputs.   # p.71-p.74
evidence: Sections 3.3.1-3.3.4; Figures 3.7-3.11; Equations 3.14-3.20.

## taxonomy
High-performance adders   # p.55
  General-purpose adders   # p.55
    Conventional 64-bit CLA -> carry_lookahead   # p.58
    64-bit modified Ling adder -> ling_prefix   # p.65
      Four-bit H/I group logic -> ling_prefix   # p.68-p.71
      H/I group and supergroup lookahead -> ling_prefix   # p.71-p.72
      True-carry recovery for final sum -> ling_prefix   # p.73-p.74
  Specialized adders for multiple generation   # p.74-p.81
    Full-length 3M generator with seven-bit groups -> constant_times_three_adder   # p.75-p.77
    Biased short-length redundant Booth 3 generator -> constant_times_three_adder   # p.76-p.80
      Three-stage form -> constant_times_three_adder   # p.76
      Two-stage merged-output form -> constant_times_three_adder   # p.76-p.80
    Conventional carry-propagate generation of 5M/7M -> unmapped   # p.81

## primary_sources
* UNKNOWN, UNKNOWN — conventional carry-lookahead adder [38]   # p.57-p.58
* H. Ling, UNKNOWN — Ling method [16]   # p.65
* UNKNOWN, UNKNOWN — conditional-sum adders [29]   # p.65
* UNKNOWN, UNKNOWN — modified Ling final-sum construction [3], [34]   # p.74

## new_families
### constant_times_three_adder  (domain: mul: integer multipliers, closest: booth_recoded_parallel, why_not: The mechanism is a specialized carry-propagate structure for generating 3M rather than a complete recoded multiplier.)
mechanism: The generator exploits B = 2A, which simplifies each bit's generate/propagate equations and permits a seven-bit group to replace a four-bit Ling group without changing the lookahead network. A short biased redundant form merges local carry-generation gates into the output stages. Two connected sections generate a 13-bit multiple when gates are limited to four inputs.   # p.75-p.80
choices:
  output_form: {full_length_3M, biased_redundant_short_3M}   # p.75-p.76
  group_width_bits: {7}   # p.75-p.77
  short_generator_stages: {2, 3}   # p.76
  short_generator_logic: {negative_logic, positive_logic_variant}   # p.76
results:
| metric | value | unit | technology / device | baseline | condition | page |
| group width | 7 | bits | ECL | 4-bit Ling group | full-length 3M generator | p.75-p.77 |
| short-multiple latency before output merge | 3 | logic stages | ECL | none | biased short-length multiple | p.76 |
| short-multiple latency after output merge | 2 | logic stages | ECL | 3 stages | gates labeled 1 merged into output gates | p.76, p.81 |
| maximum short-multiple length | 13 | bits | ECL | none | four-input gate limit | p.76-p.80 |
| gate-count reduction | about 20% | reduction in gate count | abstract | general-purpose adder computing 3M | specialized 3M adder | p.81 |
evidence: Sections 3.4-3.5; Figures 3.12-3.16; Equations 3.21-3.22.

## space_gaps
* carry_lookahead lacks choices for signal polarity and ECL-specific NOR/wire-OR mapping.   # p.57-p.65
* ling_prefix.sum_recovery lacks the chapter's true-carry recovery followed by a Shannon-expanded output stage.   # p.73-p.74
* booth_recoded_parallel.hard_multiple_adder cannot select the specialized constant_times_three_adder established here.   # p.74-p.81

## open_questions
* The chapter does not name the topology of either hierarchical lookahead network in the vocabulary's parallel-prefix terms.   # p.62-p.65, p.71-p.72
* The chapter does not identify the precise conditional-sum elements incorporated into the CLA.   # p.65
* Citation years/authors for references [3], [16], [29], [34], and [38] are unavailable within this chapter.   # p.57-p.58, p.65, p.74
