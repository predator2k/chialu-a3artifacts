---
handle: santoro1989
citation: M. R. Santoro, M. A. Horowitz, "SPIM: A Pipelined 64x64-bit Iterative Multiplier", IEEE Journal of Solid-State Circuits, vol. 24, no. 2, pp. 487-493, 1989
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [64x64-bit fractional, 80-bit floating-point mantissa]
authority: landmark
pages_read: 487-493 / 487-493
---

## summary
SPIM uses a pipelined partial tree of 4 : 2 adders and a 4 : 2 carry-save accumulator to reuse one-fourth of the post-Booth reduction tree across iterations. The fabricated 64 X 64-bit multiplier initiates one multiply every four cycles and has a reported total latency under 120 ns.

## families
### iterative_reuse  (role: proposes)
mechanism: Modified Booth encoding reduces the operation to 32 partial products. An eight-input pipelined 4 : 2 partial tree reduces eight partial products per cycle, while a 4 : 2 carry-save accumulator shifts and accumulates preceding outputs. Each tree pipe stage contains one 4 : 2 adder implemented as two CSA cells. Seven array cycles complete a multiply, and overlapping operations give a four-cycle initiation interval.   # pp.488-492
choices:
  instantiated_fraction: quarter   # p.490
  iteration_pipeline_overlap: true   # p.492
new_choices:
  partial_product_recoding: modified Booth — halves the number of partial products   # pp.488-490
  partial_products_per_cycle: 8 — sets the instantiated partial-tree width   # p.490
  local_clocking: stoppable on-chip ring oscillator — matches the fast internal pipeline and stops after array completion   # p.491
slots:
  partial_tree: compressor_4_2_tree   # pp.489-490
parameters: 64 X 64-bit operands; 32 Booth-coded partial products; 16 multiplier bits encoded per cycle; eight-input tree; one 4 : 2 adder/two CSA cells per pipe stage; seven array cycles; four-cycle II; 16-bit accumulator shift   # pp.490-492
results:
| metric | value | unit | technology / device | baseline | condition | page |
| --- | --- | --- | --- | --- | --- | --- |
| internal clock frequency | 85 | MHz | 1.6-µm CMOS; 1989 | none | room temperature | p.493 |
| flowthrough latency | 118.4 | ns | 1.6-µm CMOS; 1989 | none | 6 ns simulated startup + 82.4 ns measured array time + 30 ns simulated cpadd | p.492 |
| reported latency | under 120 | ns | 1.6-µm CMOS; 1989 | none | 64 X 64-bit fractional multiply | pp.492-493 |
| initiation interval | 47 | ns | 1.6-µm CMOS; 1989 | none | one multiply every four cycles at 85 MHz | pp.492-493 |
| throughput | in excess of 20-million | 80-bit floating-point multiplies per second | 1.6-µm CMOS; 1989 | none | maximum pipelined rate | pp.492-493 |
| core size | 3.8 X 6.5 | mm | 1.6-µm CMOS; 1989 | none | fabricated core | pp.487,493 |
| array size | 2.9 X 5.3 | mm | 1.6-µm CMOS; 1989 | none | fabricated array | p.493 |
| transistor count | 41 000 | transistors | 1.6-µm CMOS; 1989 | none | complete SPIM core | pp.487,493 |
| active current | 72 | mA | 1.6-µm CMOS; 1989 | none | average at 85 MHz | pp.492-493 |
| standby current | 10 | mA | 1.6-µm CMOS; 1989 | none | stopped array clock | pp.492-493 |
| tested frequency range | 85.4 to 88.6 | MHz | 1.6-µm CMOS; 1989 | none | 24.5°C and 4.9 V | p.492 |
errors_and_checks: none
conditions: Small latch delays and a clock matched to the CSA combinational delay are required for an iterative structure to approach full-array throughput and latency.   # p.488
conditions: The eight-input tree is selected as the reported area/speed tradeoff after comparing two-, four-, and eight-input partial trees.   # p.490
conditions: The testing equipment accurately measures only array time, so startup time and carry-propagate-addition time come from simulation.   # p.492
evidence: §§II-VII; Figs. 6-12; Table II; test results on pp.492-493

### carry_save_datapath  (role: instantiates)
mechanism: The D block retains the iterative result as sum/carry outputs. A 4 : 2 adder uses two inputs for the preceding shifted outputs and two inputs for the current tree outputs, so accumulation avoids carry propagation until the final conversion.   # pp.489-490
choices:
  compressor: 4_2   # pp.489-490
  assimilation_point: end_of_chain   # pp.490,492
  accumulator_redundant: true   # pp.489-490
new_choices:
  alignment_shift: fixed 16-bit right shift — aligns the previous partial sum with the current partial products   # p.490
slots:
  assimilator: UNKNOWN   # pp.490,492
parameters: one accumulator pipe stage; 16-bit hard-wired right shift; final carry-propagate addition simulated at 30 ns   # pp.489-492
results:
| metric | value | unit | technology / device | baseline | condition | page |
| --- | --- | --- | --- | --- | --- | --- |
| relative speed | almost twice | speed | UNKNOWN; 1989 | conventional partial piped array | single 4 : 2 adder plus carry-save accumulator; roughly equal hardware | p.489 |
errors_and_checks: none
conditions: The carry-save accumulator adds one pipe stage and avoids carry propagation during iterative accumulation.   # p.489
evidence: Fig. 6 and accompanying discussion on p.489; SPIM datapath in Fig. 9 on p.490

## new_families
### compressor_4_2_tree  (domain: mul, closest: iterative_reuse, why_not: the vocabulary names compressor_4_2_tree as a slot target but declares no corresponding family or choices)
mechanism: A 4 : 2 adder reduces four same-weight tree inputs to two next-level outputs. Its carry-out cannot depend on the adjacent slice carry-in, which prevents ripple carry. SPIM implements each 4 : 2 adder with two CSA cells and combines the adders into a regular binary-shaped reduction tree. Partial trees of two, four, and eight inputs expose an area/latency tradeoff.   # pp.488-490
choices: tree_inputs: {2, 4, 8}; implementation: {direct_truth_table, two_csa_cells}; tree_extent: {partial, full}; carry_save_accumulator: Bool; pipeline_interval_csa_cells: {2}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| --- | --- | --- | --- | --- | --- | --- |
| relative speed | almost three times | speed | UNKNOWN; 1989 | two-input partial tree | eight-input tree for a 64 X 64-bit Booth-encoded multiply | p.490 |
| relative size | one-fourth | full-array size | UNKNOWN; 1989 | full array | eight-input tree; size counts CSA cells and excludes latch/wiring area | p.490 |
| full-array speed advantage | 15 | percent | UNKNOWN; 1989 | two-row iterative structure | architectural CSA-delay model | p.490 |
evidence: Figs. 4-8 and architectural analysis on pp.488-490

## space_gaps
* `compressor_4_2_tree` needs a declared family because existing slots reference it and this paper fixes its cell implementation/tree width/pipelining choices.   # pp.488-490
* `iterative_reuse` lacks choices for partial-product recoding, partial-tree input count, and local pipeline clocking.   # pp.488-491

## open_questions
* The final carry-propagate adder architecture is not identified.   # pp.490,492
* The exact modified-Booth sign-extension and negative-partial-product encoding are not specified.   # pp.488,490
