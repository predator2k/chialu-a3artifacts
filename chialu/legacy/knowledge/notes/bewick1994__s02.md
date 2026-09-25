---
handle: bewick1994#s02
parent: bewick1994
citation: G. W. Bewick, "Fast Multiplication: Algorithms and Implementation", PhD dissertation, Stanford University, CSL-TR-94-617, 1994
chapter: Introduction
pdf_pages: 15-26
status: ok
kind: thesis_chapter
unit_classes: [BINARY_ALU]
formats: [binary]
authority: thesis
pages_read: 12 / 12
---

## summary
The chapter classifies binary multipliers as iterative, unrolled linear-array, parallel-adder-tree, Wallace-tree, and binary 4-2-counter implementations. The chapter selects a fully parallel CSA tree in ECL because registers are expensive and CSAs are efficient in that technology. The chapter establishes latency, hardware, interconnection, and regularity tradeoffs without specifying operand width, signed encoding, or final-adder design.

## families
### sequential_shift_add  (role: defines)
mechanism: A partial-product generator feeds one partial product per cycle to an adder-accumulator, while a hard-wired right shift updates the product state. Adding N partial products requires N clock cycles.
choices:
  bits_per_cycle: 1   # p.19
  accumulator_form: carry_propagate   # p.22
  string_skipping: UNKNOWN   # p.19
new_choices:
  clocking_source: {system_clock, multiplied_clock, self_clocked} — The multiplier can use the system clock or require faster multiplied/self-generated timing.   # p.19
slots:
  step_adder: UNKNOWN   # p.19
parameters: N partial products; N clock cycles   # p.19
results:
| metric | value | unit | technology / device | baseline | condition | page |
| latency | N | clock cycles | abstract | none | addition of N partial products | p.19 |
errors_and_checks: none
conditions: The architecture is relatively slow because it processes one partial product per clock cycle (p.19). The system clock is normally slower than the architecture's maximum clock rate, so minimum delay requires a clock multiplier or self-clocking hardware (p.19). ECL register area/power discourages this registered iterative structure (p.23).
evidence: Section 1.3.1; Figure 1.3; Section 1.4

### carry_save_array  (role: analyzes)
mechanism: A carry-save adder, also called a full adder or 3-2 counter, converts three operands into two without carry propagation. Recursive application reduces any number of partial products to two numbers, after which one carry-propagate addition produces the product. The method applies to linear arrays as well as trees.
choices:
  signed_scheme: UNKNOWN   # p.22
  rows_per_pipeline_stage: UNKNOWN   # p.22
new_choices:
  counter_primitive: {full_adder, 3-2_counter} — The chapter treats these names as equivalent CSA primitives.   # p.22
slots:
  cpa: UNKNOWN   # p.22
parameters: 3 input operands reduced to 2 output operands; one final carry-propagate addition   # p.22
results:
| metric | value | unit | technology / device | baseline | condition | page |
| counter reduction | 3 to 2 | operands | abstract | carry-propagate addition | one CSA row | p.22 |
| carry-propagate additions during recursive reduction | 0 | additions | abstract | carry-propagate array/tree | before final assimilation | p.22 |
| final carry-propagate additions | 1 | addition | abstract | none | reduction from two numbers to the final product | p.22 |
| CSA current requirement | 2 | tail (gate) currents per CSA | ECL | none | ECL implementation | p.23 |
| higher-order counter area/power advantage | no advantage | qualitative | ECL | CSA | 4-2, 5-5-4, or 7-3 blocks | p.23 |
errors_and_checks: none
conditions: ECL permits efficient CSA implementation (p.23). The thesis therefore considers CSA-based architectures exclusively (p.25). Automated placement/wiring is used to handle direct-CSA wiring complexity (p.25).
evidence: Section 1.3.4; Figure 1.6; Section 1.4

## taxonomy
* Technology options   # p.16-p.19
  * CMOS -> unmapped   # p.16
  * BiCMOS -> unmapped   # p.17
  * ECL -> unmapped   # p.17-p.19
    * Differential ECL -> unmapped   # p.18-p.19
* Multiplication architectures   # p.19-p.23
  * Iterative -> sequential_shift_add   # p.19
  * Linear arrays -> unmapped   # p.20
    * Partially unrolled loop -> unmapped   # p.20
    * Completely unrolled full linear array -> unmapped   # p.20
  * Parallel addition trees -> unmapped   # p.20-p.22
    * Carry-propagate-adder tree -> unmapped   # p.20-p.22
    * Wallace tree using CSAs -> unmapped   # p.22
    * Binary tree using 4-2 counters -> unmapped   # p.23
* CSA application shapes   # p.22
  * CSA linear array -> carry_save_array   # p.22
  * CSA tree -> unmapped   # p.22

## primary_sources
* Wallace, year UNKNOWN — use of carry-save adders to reduce multiplier partial products without carry propagation   # p.22
* [24], [37], and [30], years UNKNOWN — regular partial-product reduction structures based on binary trees   # p.23
* Santoro, year UNKNOWN — use of 4-2 adders constructed from two CSAs   # p.23
* Weinberger, year UNKNOWN — use of 4-2 adders constructed from two CSAs   # p.23

## new_families
### unrolled_linear_multiplier  (domain: mul: integer multipliers, closest: sequential_shift_add, why_not: The architecture instantiates multiple serial adder/partial-product stages per cycle rather than reusing one stage for a fixed one-partial-product iteration.)
mechanism: Multiple partial-product generators and adders are connected in series by unrolling the iterative multiplier loop. Partial unrolling reduces multiple partial products per cycle and can match the system clock. Complete unrolling produces a combinational full linear array.
choices:
  unroll_degree: {partial, complete}   # p.20
  timing_target: {system_clock_matched, combinational}   # p.20
results:
| metric | value | unit | technology / device | baseline | condition | page |
| partial products reduced | 3 | partial products per clock | abstract | simple iterative multiplier | Figure 1.4 example | p.21 |
| hardware requirement | increases with unrolling | qualitative | abstract | simple iterative multiplier | multiple serial generators/adders | p.20 |
| clock skew/register-delay overhead | less per partial product reduced | qualitative | abstract | simple iterative multiplier | unrolled implementation | p.20 |
evidence: Section 1.3.2; Figure 1.4

### parallel_cpa_reduction_tree  (domain: mul: integer multipliers, closest: carry_save_array, why_not: The tree uses carry-propagate adders rather than a regular two-dimensional CSA array.)
mechanism: Partial products are paired and added through parallel levels of carry-propagate adders. The tree minimizes serial addition depth at the cost of more complex interconnections.
choices:
  tree_shape: {binary}   # p.20-p.21
results:
| metric | value | unit | technology / device | baseline | condition | page |
| reduction latency | proportional to log N | time | abstract | linear array | N partial products | p.20-p.22 |
| reduction latency | 3 | adder delays | abstract | none | 8 partial products | p.21 |
| hardware count | no more hardware | qualitative | abstract | linear array | same partial-product count | p.20 |
| interconnection complexity | more complex | qualitative | abstract | linear array | parallel tree | p.20-p.22 |
evidence: Section 1.3.3; Figure 1.5

### carry_save_reduction_tree  (domain: mul: integer multipliers, closest: carry_save_array, why_not: The architecture recursively reduces operands in a tree rather than arranging CSAs as a regular two-dimensional array.)
mechanism: A Wallace variant recursively applies 3-2 CSAs and has irregular interconnections. A more regular binary-tree variant uses rows of 4-2 counters, each constructible from two CSAs, but shifted partial products still introduce zeros, level-skipping bits, and unequal counter counts.
choices:
  tree_style: {wallace_3_2, binary_4_2}   # p.22-p.23
  zero_handling: {add_explicit_zeros, specialized_counters}   # p.23
results:
| metric | value | unit | technology / device | baseline | condition | page |
| final operand count | 2 | operands | abstract | original partial products | recursive CSA reduction | p.22 |
| final carry-propagate additions | 1 | addition | abstract | none | conversion to final product | p.22 |
| reduction depth | 2 | levels of 4-2 counters | abstract | none | 8 partial products | p.23-p.24 |
| first-level counter count | 9 | counters per row | abstract | none | Figure 1.7 | p.23-p.24 |
| second-level counter count | 12 | counters | abstract | 9 counters in first-level rows | Figure 1.7 | p.23-p.24 |
| layout regularity | more regular | qualitative | abstract | Wallace tree | binary 4-2 tree | p.23 |
evidence: Sections 1.3.4 and 1.4; Figures 1.6 and 1.7

## space_gaps
* `csa_reduction_tree` and `compressor_4_2_tree` occur as slot fillers in the vocabulary but lack declared family definitions and choices; the chapter distinguishes irregular Wallace CSA trees from more regular binary 4-2-counter trees (p.22-p.23).
* The vocabulary lacks a family for partially or completely unrolled linear multipliers built from serial adder/partial-product stages (p.20-p.21).
* The vocabulary lacks a family for a parallel reduction tree made from carry-propagate adders (p.20-p.22).

## open_questions
* The chapter excerpt does not supply the publication years or full identities for references [24], [30], [35], and [37].
* The chapter does not identify the carry-propagate adder styles used by the iterative, linear-array, tree, or final-assimilation stages.
* The printed statement that ECL loaded-gate delay is “between 12 and 14 the delay” of comparable CMOS gates is ambiguous and must not be converted into a ratio without checking the source typography (p.19).
