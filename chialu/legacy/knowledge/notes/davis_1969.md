---
handle: davis_1969
citation: R. L. Davis, "The ILLIAC IV Processing Element", IEEE Transactions on Computers, vol. C-18, no. 9, pp. 800-816, 1969
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [64-bit floating point, 32-bit floating point, 64-bit unsigned, 8-bit unsigned]
authority: landmark
pages_read: 800-816 / 17
---

## summary
The document describes the arithmetic datapath of the 256-PE ILLIAC IV, including its carry-look-ahead adder, radix-4 barrel switch, recoded carry-save multiplier, and nonperforming divider. Lock-step synchronous execution favors fixed-latency algorithms and excludes data-dependent shifting over zero/one strings. The PE supports 64-bit operations and two 32-bit floating-point operations with sign-and-magnitude mantissas.

## families
### replicated_lanes  (role: instantiates)
mechanism: ILLIAC IV contains 256 identical PE-memory combinations divided into four arrays of 64. Each array executes one broadcast instruction stream in lock-step, while full-word neighbor connections support routing among PE positions. Each PE contains five 64-bit data registers and local arithmetic/shift logic. # p.800, p.802
choices:
  register_file: dedicated_simd   # p.802-p.803
  rearrangement: nearest_neighbor_routing [outside domain]   # p.800
new_choices:
  routing_neighbors: {k+1, k-1, k+8, k-8} — the directly connected PE positions, with selectable end-around connections   # p.800
slots:
  none
parameters: 256 PEs; four arrays of 64 PEs; five 64-bit data registers per PE; two concurrent 32-bit words supported   # p.800, p.802, p.815
results:
| metric | value | unit | technology / device | baseline | condition | page |
| PE count | 256 | PE | ECL / ILLIAC IV PE; 1969 | none | full four-quadrant system | p.800 |
conditions: Lock-step execution makes the slowest PE determine operation time, so variable-shift multiplication/division provides little statistical advantage. # p.812, p.813-p.814
evidence: Abstract; §I; §II-A; §III-D; §III-E; §IV.

### barrel_mux_tree  (role: instantiates)
mechanism: The 64-bit right-shifting end-around barrel switch passes parallel data through three gate-matrix levels. The levels select displacements of 0/16/32/48, 0/4/8/12, and 0/1/2/3 positions. Left shifts use the radix complement of the shift count, while gating inserts zeros for left/right end-off shifts. # p.803, p.808
choices:
  stage_radix: 4   # p.808
  direction_handling: amount_negation   # p.808
  stage_order: large_shift_first   # p.808
new_choices:
  levels: 3 — the number of displacement-gate levels   # p.808
slots:
  none
parameters: 64-bit input/output; three levels; four displacement choices per level; left/right and end-off/end-around modes   # p.803, p.808
results:
| metric | value | unit | technology / device | baseline | condition | page |
| shift latency | 1 | clock period | ECL / ILLIAC IV PE; 1969 | none | generalized register shifting | p.803 |
conditions: The physical arrangement minimizes board types and intralevel wiring at the cost of more complicated interlevel wiring. # p.808
evidence: §II-A.1 “Shifting”; §II-B.2; Figs. 9-10.

### carry_lookahead  (role: instantiates)
mechanism: Each bit produces generate/transmit signals for four-bit group look-aheads. Four groups feed each section look-ahead, and four sections form the 64-bit adder. Section generates/transmits create section input carries; group carries then create bit carries. Section controls can force or inhibit carries for subtraction and end-around-carry control. # p.803-p.805
choices:
  group_size: 4   # p.803-p.805
  levels: 3   # p.803
  intergroup_carry: lookahead   # p.803-p.805
  block_sizing: uniform   # p.803-p.805
new_choices:
  none
slots:
  none
parameters: 64 bits; 4 bits/group; 4 groups/section; 4 sections; three look-ahead levels   # p.803-p.805
results:
| metric | value | unit | technology / device | baseline | condition | page |
| addition latency | 1 | clock period | ECL / ILLIAC IV PE; 1969 | none | 64-bit sum | p.803 |
| design clock period | 50 | ns | ECL / ILLIAC IV PE; 1969 | none | PE design goal | p.803 |
| gate delay | 1.5 to 5.5 | ns per gate | ECL / ILLIAC IV PE; 1969 | none | depends on loading/circuit configuration | p.804 |
conditions: The same adder can operate as a carry-propagating adder or carry-save adder. # p.803
evidence: §II-A.1 “Adding and multiplying”; §II-B.1; Figs. 7-8.

### partitioned_carry_chain  (role: instantiates)
mechanism: Eight-bit byte gating interrupts carry propagation for byte operations. The two 32-bit floating-point words use independently protected register halves and overlap adder/shift-network work, while 64-bit mode joins the halves. # p.803, p.810
choices:
  boundary_mechanism: carry_kill_gate   # p.803
new_choices:
  lane_widths: {8, 32, 64} — supported arithmetic partitions or word widths   # p.802-p.803
slots:
  base_adder: carry_lookahead [group_size=4, levels=3]   # p.803
parameters: eight 8-bit byte partitions; two 32-bit floating-point words; one 64-bit word   # p.802-p.803
results:
| metric | value | unit | technology / device | baseline | condition | page |
| processor-count scaling | 2 | 32-bit words per PE | ECL / ILLIAC IV PE; 1969 | one 64-bit word | little increase in execution time | p.815 |
conditions: The 32-bit inner/outer operations share resources and are scheduled at different clock times. # p.810
evidence: §II-A.1; Table II; §IV.

### booth_recoded_parallel  (role: instantiates)
mechanism: Multiplier bits are recoded pairwise from the least-significant end into digits {-1,0,1,2}. Eight multiplier bits are recoded per clock, and selected shifted/complemented multiplicands enter a four-layer carry-save path. A -1 digit complements the 48 operand bits and sets the extension/free-carry inputs to ones to form the required two's complement. # p.812-p.813
choices:
  booth_radix: 4   # p.812
  hard_multiple_gen: none   # p.812
  negative_pp_encoding: twos_complement_row   # p.813
new_choices:
  recoded_bits_per_cycle: 8 — multiplier bits decoded during each iteration   # p.803, p.812-p.813
slots:
  reduction: csa_reduction_tree   # p.803, p.813
parameters: 48-bit mantissas; recoded digits {-1,0,1,2}; T1-T9 sequence; eight multiplier bits per iteration   # p.812-p.813
results:
| metric | value | unit | technology / device | baseline | condition | page |
| unrounded multiplication latency | 9 | clock times | ECL / ILLIAC IV PE; 1969 | none | 64-bit floating-point design goal | p.803 |
| unrounded multiplication latency | 450 | ns | ECL / ILLIAC IV PE; 1969 | none | 64-bit floating-point design goal | p.803 |
conditions: Fixed-shift recoding is selected because lock-step execution loses the average-time benefit of multiplier-string skipping. # p.811-p.812
evidence: §III-D; Table IV; Figs. 12-13.

### carry_save_datapath  (role: instantiates)
mechanism: The most significant 56 partial-product bits remain separated into sum/carry outputs across multiplication iterations. Each iteration propagates only the least-significant eight-bit carry, while the final cycle assimilates all 56 remaining sum/carry bits with the CPA. # p.812-p.813
choices:
  compressor: 3_2   # p.803, p.813
  assimilation_point: end_of_chain   # p.813
  accumulator_redundant: true   # p.812-p.813
new_choices:
  partial_assimilation_width: 8 — carry propagation performed during each iteration   # p.812-p.813
slots:
  assimilator: carry_lookahead [group_size=4, levels=3]   # p.803, p.813
parameters: 56-bit partial sum/carry state; 8-bit per-iteration assimilation; 56-bit final assimilation   # p.812-p.813
results:
| metric | value | unit | technology / device | baseline | condition | page |
| partial carry propagation | 8 | bits per iteration | ECL / ILLIAC IV PE; 1969 | full carry propagation | multiplication iterations | p.812-p.813 |
conditions: The 48-bit multiplicand enters a 56-bit carry-save path, so eight extension inputs are zero for digits 0/1/2 and one for digit -1. # p.813
evidence: §III-D.2; Fig. 13.

### restoring_nonrestoring  (role: instantiates)
mechanism: Nonperforming division subtracts the divisor from the shifted partial remainder. A nonnegative subtraction result is accepted with quotient digit 1; a negative result selects the shifted old remainder with quotient digit 0. This selection avoids a restoring addition and generates one quotient bit per clock. # p.814
choices:
  style: nonperforming   # p.814
  bits_per_cycle: 1   # p.814
  shift_over_zeros: false   # p.813-p.814
new_choices:
  remainder_selection: subtract_result_or_old_remainder — the negative subtraction result is discarded rather than restored   # p.814
slots:
  residual_adder: carry_lookahead [group_size=4, levels=3]   # p.803, p.814
parameters: 48-bit significands; n={47,48} recurrence steps; quotient digits {0,1}; normalized divisor 1/2<d<1   # p.814
results:
| metric | value | unit | technology / device | baseline | condition | page |
| quotient generation rate | 1 | quotient bit per clock time | ECL / ILLIAC IV PE; 1969 | none | nonperforming recurrence | p.814 |
errors_and_checks: The fault bit is set for an unnormalized or zero divisor. Valid remainders depend on arithmetic mode and generally require X0<d; rounded modes do not retain a valid remainder. # p.814
conditions: The recurrence requires X0<2d and a normalized divisor; true restoring would require twice as many iterative clocks under lock-step scheduling. # p.814
evidence: §III-E; Figs. 14-16.

### single_path  (role: instantiates)
mechanism: Floating-point addition serially computes the exponent difference, saves the most significant shifted-off bit, aligns the smaller mantissa, adds/subtracts sign-and-magnitude mantissas, rounds, normalizes, and corrects the exponent. The 32-bit mode overlaps inner/outer work across the shared adder and shift network. # p.809-p.810
choices:
  post_round_renorm: true   # p.810
new_choices:
  mantissa_representation: sign_and_magnitude — the stored floating-point mantissa representation   # p.808
  subtraction_style: ones_complement_end_around — unlike-sign mantissas use one's complementation and end-around carry   # p.811
slots:
  sig_adder: carry_lookahead [group_size=4, levels=3]   # p.803, p.810
  exp: exponent_path   # p.809-p.810
  subnormal: flush_to_zero_mode   # p.809
  align: full_align   # p.803, p.809-p.810
  norm: single_barrel   # p.803, p.810
parameters: 64-bit format with 48-bit mantissa; 32-bit format with 24-bit mantissa; 5/7 clocks for unrounded/rounded 64-bit addition; 6/10 clocks for unrounded/rounded 32-bit addition   # p.803, p.808, p.810
results:
| metric | value | unit | technology / device | baseline | condition | page |
| addition latency | 5 | clock times | ECL / ILLIAC IV PE; 1969 | none | 64-bit unrounded | p.810 |
| addition latency | 7 | clock times | ECL / ILLIAC IV PE; 1969 | none | 64-bit rounded | p.810 |
| addition latency | 6 | clock times | ECL / ILLIAC IV PE; 1969 | none | 32-bit unrounded | p.810 |
| addition latency | 10 | clock times | ECL / ILLIAC IV PE; 1969 | none | 32-bit rounded | p.810 |
| unrounded addition latency | 250 | ns | ECL / ILLIAC IV PE; 1969 | none | 64-bit floating-point design goal | p.803 |
errors_and_checks: Exponent underflow clears the entire result to zero; fault reporting is programmable and sticky within an instruction. # p.809
conditions: The format is non-IEEE, uses offset exponents/sign-and-magnitude mantissas, and provides normalized/unnormalized and rounded/unrounded instruction variants. # p.808-p.809
evidence: §III-A-C; Tables I-III.

## new_families
none

## space_gaps
* `replicated_lanes.rearrangement` lacks the document's nearest-neighbor `{k+1,k-1,k+8,k-8}` routing with selectable end-around connections. # p.800
* `single_path` lacks choices for sign-and-magnitude mantissas and one's-complement end-around subtraction. # p.808, p.811
* `csa_reduction_tree` is accepted by component slots but has no declared family block, despite the document's four-layer carry-save multiplier path. # p.803, p.813

## open_questions
* The document calls the multiplier path a “quadruple layer” with the CPA acting as the fourth CSA, but it does not provide enough topology detail to classify the tree shape. # p.803
* The document states that the 32-bit multiplier follows the 64-bit design with minor modifications, but it does not report the exact 32-bit multiplication schedule. # p.813
