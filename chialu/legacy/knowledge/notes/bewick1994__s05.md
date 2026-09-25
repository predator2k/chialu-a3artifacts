---
handle: bewick1994#s05
parent: bewick1994
citation: G. W. Bewick, "Fast Multiplication: Algorithms and Implementation", PhD dissertation, Stanford University, CSL-TR-94-617, 1994
chapter: Implementing Multipliers
pdf_pages: 82-109
status: ok
kind: thesis_chapter
unit_classes: [BINARY_ALU]
formats: [binary integer]
authority: thesis
pages_read: 28 / 28
---

## summary
The chapter defines an automated, wire-aware generator for partial-product placement and carry-save summation networks. The generator reduces partial products to two operands with CSAs/HAs, applies physical area/delay/power optimizations, and emits placement/routing data for a final carry-propagate adder. The chapter analyzes an aligned linear-array alternative and the placement implications of Booth-generated partial products without redefining their arithmetic algorithms.

## families
### carry_save_array  (role: analyzes)
mechanism: An alternate physical organization aligns partial-product rows so selects run horizontally and multiplicand bits run vertically. Outputs of different arithmetic weights share routing channels and must be unscrambled while the next partial product is summed, which the chapter identifies with linear arrays.   # p.89, p.93
choices:
  signed_scheme: UNKNOWN   # p.93
  rows_per_pipeline_stage: UNKNOWN   # p.93
new_choices:
  partial_product_alignment: aligned_rows — aligns multiplicand bits vertically and leaves mixed arithmetic weights in each routing channel   # p.89, p.93
slots:
  cpa: UNKNOWN   # p.93
parameters: multiplicand length N; approximately N routing channels   # p.93
results:
| metric | value | unit | technology / device | baseline | condition | page |
| routing channels | approximately N | routing channels | abstract | about 2N for the generator's initial arrangement | aligned partial products | p.93 |
| area | comparable | area | abstract | diagonal multiplicand-routing arrangement | aligned partial products | p.93 |
| performance | comparable | performance | abstract | diagonal multiplicand-routing arrangement | aligned partial products | p.93 |
errors_and_checks: none
conditions: The aligned organization requires output unscrambling and about as much extra wiring as routing multiplicand bits diagonally. The generator rejects this organization because longer partial-product output wiring affects N2 wires rather than N multiplicand wires and because mixed arithmetic weights complicate CSA placement.   # p.93
evidence: Section 4.3.1; Figure 4.11   # p.89, p.93

### booth_recoded_parallel  (role: analyzes)
mechanism: The chapter states only a placement consequence of “Booth 2 or higher” partial-product generation: one multiplicand bit may need to reach multiplexers in two adjacent columns, so selector-cell feedthroughs remain necessary. The arithmetic recoding mechanism is referred to Chapter 2 and is not restated here.   # p.89
choices:
  booth_radix: UNKNOWN   # p.89
  hard_multiple_gen: UNKNOWN   # p.89
  sign_extension: UNKNOWN   # p.89
  negative_pp_encoding: UNKNOWN   # p.89
new_choices:
  none
slots:
  reduction: UNKNOWN   # p.89
  hard_multiple_adder: UNKNOWN   # p.89
parameters: “Booth 2 or higher” in the chapter's terminology   # p.89
results:
| metric | value | unit | technology / device | baseline | condition | page |
| adjacent-column reach | 2 | columns | abstract | UNKNOWN | Booth 2 or higher partial-product layout | p.89 |
errors_and_checks: none
conditions: The chapter establishes only the need for adjacent-column feedthroughs in the discussed aligned layout; it does not settle the corresponding vocabulary radix or other Booth choices.   # p.89
evidence: Section 4.3.1, “Multiplexer Alignment”   # p.89

## taxonomy
Multiplier implementation   # p.85
  Partial-product generator
    Shifted rows; multiplicand bits routed diagonally; equal-weight outputs share a routing channel -> unmapped   # p.85, p.88, p.90
    Aligned rows; multiplicand bits routed vertically; outputs unscrambled during summation
      Linear array -> carry_save_array   # p.89, p.93
      Booth 2 or higher with adjacent-column feedthroughs -> booth_recoded_parallel   # p.89
  Summation network
    Wallace tree or related carry-propagate-free scheme -> csa_reduction_tree   # p.82, p.85
      CSA greedy placement by fastest available path -> csa_reduction_tree   # p.94-p.96
      CSA placement with first-counter half adders -> csa_reduction_tree   # p.96-p.100
  Final carry-propagate adder
    Family unspecified -> unmapped   # p.85, p.86, p.103
  Layout optimizations
    Tree folding -> csa_reduction_tree   # p.100-p.103
    Embedded CSAs -> csa_reduction_tree   # p.103-p.104
    Wire-crossing elimination -> csa_reduction_tree   # p.105-p.106
    Differential wiring -> csa_reduction_tree   # p.106-p.107
    Emitter-follower elimination -> csa_reduction_tree   # p.107
    Power ramping -> csa_reduction_tree   # p.107-p.108

## primary_sources
none

## new_families
### csa_reduction_tree  (domain: mul: integer multipliers, closest: carry_save_array, why_not: carry_save_array denotes a regular 2-D array, while this mechanism constructs a placement-aware Wallace-related reduction tree with nonuniform CSA/HA connectivity.)
mechanism: Partial-product bits are reduced to two operands with 3-input CSAs and selected HAs. A greedy placement algorithm repeatedly chooses the fastest unwired output, connects it to the CSA input with the longest input delay, and adds two slower same-weight signals that do not increase the CSA output time. Virtual wires model the eventual route to the final CPA. Half adders break ripple-like counter chains. Tree folding, CSA embedding, wire-crossing elimination, differential wiring, emitter-follower elimination, and power ramping optimize physical area/delay/power.   # p.94-p.108
choices:
  counter_set: {csa_only, csa_and_ha}   # p.94-p.100
  placement_policy: {greedy_fastest_path}   # p.95-p.96
  arrival_aware: Bool   # p.84-p.85, p.95-p.96
  wire_length_aware: Bool   # p.84-p.85, p.94-p.96
  tree_folding: Bool   # p.100-p.103
  embedded_csa: Bool   # p.103-p.104
  wire_crossing_elimination: Bool   # p.105-p.106
  differential_wiring: {none, critical_path_selective}   # p.106-p.107
  emitter_follower_elimination: Bool   # p.107
  power_ramping: Bool   # p.107-p.108
results:
| metric | value | unit | technology / device | baseline | condition | page |
| routing-channel reduction | almost half | required routing channels | abstract | unfolded shifted-row layout | tree folding | p.103 |
| embedded-CSA routing use | 2 | routing tracks | abstract | 3 routing tracks | CSA moved between its source outputs | p.103-p.104 |
| crossing-elimination saving | 2 | routing tracks per crossing | abstract | crossing retained | equal weight, no critical-path increase, no cycle | p.105-p.106 |
| driving-gate delay | halved | gate delay | differential ECL; node/year UNKNOWN | single-ended ECL | complementary second wire | p.106 |
| wire delay | halved | wire delay | differential ECL; node/year UNKNOWN | single-ended ECL | complementary second wire | p.106 |
| follower minimum current | about 1/4 | maximum follower current | ECL; node/year UNKNOWN | maximum follower current | noise-margin-limited power ramping | p.108 |
| gate-current-source resistor limit | about 10KΩ | resistance | ECL; node/year UNKNOWN | UNKNOWN | practical layout-area limit | p.108 |
| gate minimum-to-maximum current ratio | about 1/4 | ratio | ECL; node/year UNKNOWN | maximum gate current | resistor-area-limited power ramping | p.108 |
| short-wire range | length ≤ 2mm | wire length | ECL; node/year UNKNOWN | UNKNOWN | delay inversely proportional to available current | p.107 |
evidence: Sections 4.2-4.4; Figures 4.2, 4.12-4.20   # p.84-p.108

## space_gaps
* `csa_reduction_tree` is referenced elsewhere in the vocabulary as a component-slot value but lacks a family definition for the chapter's Wallace-related, placement-aware CSA/HA network.   # p.82, p.85, p.94-p.100
* `csa_reduction_tree` needs choices for half-adder insertion, arrival-aware placement, wire-aware placement, folding, CSA embedding, and crossing elimination.   # p.84-p.85, p.94-p.106
* Physical implementation choices for differential critical-path wiring, emitter-follower elimination, and current ramping are absent from the multiplier vocabulary.   # p.106-p.108

## open_questions
* The chapter does not enumerate the supported partial-product algorithms because their definitions occur in Chapter 2.   # p.82
* The phrase “Booth 2 or higher” does not establish which `booth_radix` vocabulary value applies.   # p.89
* The final carry-propagate-adder family is unspecified.   # p.85, p.103
* The technology-specific CSA/HA timing tables, metal pitches, cell geometry, and HSPICE-derived delay constants are not printed.   # p.82, p.84-p.85
* The HA observations assume equal input/output delays and ignore wire/fanout effects, so the chapter treats them as placement heuristics rather than guarantees for real circuitry.   # p.96-p.100
