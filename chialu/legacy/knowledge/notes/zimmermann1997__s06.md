---
handle: zimmermann1997#s06
parent: zimmermann1997
citation: zimmermann1997 — Binary Adder Architectures for Cell-Based VLSI and their Synthesis
chapter: Special Adders
pdf_pages: 63-72
status: ok
kind: thesis_chapter
unit_classes: [BINARY_ALU]
formats: [binary, unsigned, 2's complement, 1's complement, modulo 2^n-1, modulo 2^n+1 diminished-one]
authority: thesis
pages_read: 10 / 10
---

## summary
The chapter adapts parallel-prefix adders for flag generation, late carry-in, unequal timing profiles, modulo arithmetic, partitioned word lengths, subtraction, incrementation, and comparison. It establishes that prefix structures permit these customizations with small logic changes and records their abstract delay/area costs. It analyzes hand-optimized structures rather than the automatic synthesis deferred to Chapter 6.

## families
### parallel_prefix  (role: extends)
mechanism: An additional prefix level or a final operator row processes a late carry-in, while mixed serial/parallel regions trade area against delay under relaxed timing constraints. The last prefix stage can instead act as an incrementer controlled by an earlier carry-out. Sklansky and Brent-Kung graphs support partitioning through inserted generate/propagate controls.
choices:
  topology: sklansky | brent_kung   # p.71, p.72
  valency: UNKNOWN   # p.63
  log2_sparsity: UNKNOWN   # p.63
  fanout_cap: UNKNOWN   # p.64
  wire_track_budget: UNKNOWN   # p.63
  node_style: and_or   # p.64
new_choices:
  late_input_carry: final_operator_row — adds a prefix row for constant carry-in-to-output delay   # p.64
  serial_parallel_mix: lower_parallel_upper_serial — trades area against delay   # p.65
slots:
  none
parameters: general n-bit structures; figures illustrate 16-bit adders   # p.64, p.66
results:
| metric | value | unit | technology / device | baseline | condition | page |
| carry-out lead over sum | 2 | gate delays | abstract | final sum | ordinary parallel-prefix carry flag | p.63 |
| overall delay increase | 2 | gate delays | abstract | prefix adder without final carry row | fastest late input-carry processing | p.64 |
| carry-in fan-out growth | linear with word length | scaling | abstract | UNKNOWN | final operator row | p.64 |
| relaxed-timing area/delay | compromise between serial-prefix and parallel-prefix extremes | qualitative | abstract | serial-prefix and parallel-prefix | mixed prefix structure | p.65 |
errors_and_checks: none
conditions: The late-carry row provides constant logical carry-in propagation, but physical delay increases with the linearly growing carry-in fan-out.   # p.64
evidence: Sections 5.1–5.3; Figures 5.1–5.2.

### prefix_synthesis_nonuniform_arrival  (role: analyzes)
mechanism: Prefix graphs are shaped to compensate for arbitrary input arrival and output required-time profiles. Serial-prefix regions serve positions whose timing already tolerates ripple propagation, while parallel-prefix regions accelerate late or critical positions. The multiplier-final-adder example divides the graph into serial, parallel, and extended optimized regions.
choices:
  arrival_profile: lsb_late | msb_late | multiplier_vee   # p.65
  search_method: hand_optimized [outside domain]   # p.65
  fanout_cap: UNKNOWN   # p.65
  region_hybridization: true   # p.65
new_choices:
  output_required_profile: lsb_early | msb_early — required times may vary by bit position   # p.65
slots:
  none
parameters: 16-bit example graphs   # p.66, p.67
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area and delay | considerably decreased | qualitative | abstract | graph optimized for equal arrival times | late intermediate bits from a Wallace-tree multiplier | p.65 |
errors_and_checks: none
conditions: Each optimal graph depends on the exact arrival/required-time profile, and fan-out/delay/gate-count trade-offs were excluded from the hand optimization.   # p.65, p.66
evidence: Section 5.4; Figures 5.3–5.6.

### end_around_carry  (role: instantiates)
mechanism: Carry-out feeds the carry-in logic for modulo 2^n-1 or modulo 2^n+1 addition. A fast prefix structure breaks the direct carry-in-to-carry-out path and uses its last prefix stage as a carry-controlled incrementer. Modulo 2^n-1 supports single- or double-representation of zero; modulo 2^n+1 uses diminished-one representation and an inverted feedback condition.
choices:
  modulus: mod_2n_minus_1 | mod_2n_plus_1_diminished_one   # p.68, p.69
  recirculation: cyclic_prefix_level   # p.68
  topology: UNKNOWN   # p.68
new_choices:
  zero_representation: single | double — selects the modulo 2^n-1 zero encoding   # p.68, p.69
slots:
  none
parameters: general n-bit equations; figures illustrate 16-bit adders   # p.68, p.69
results:
| metric | value | unit | technology / device | baseline | condition | page |
| coding logic per bit | doubled on average | logic | abstract | ordinary carry-lookahead coding | re-substituted carry-out carry-lookahead alternative | p.69 |
errors_and_checks: A normal adder feedback path can form a combinational loop and may oscillate; suitable feedback logic or removal of the carry-in-to-carry-out path avoids the loop.   # p.68
conditions: The structure applies to RNS, cryptography, and error-detection/correction codes, and it provides no independent carry input because feedback consumes the carry-in.   # p.68
evidence: Section 5.5; Figures 5.7–5.11; Equations 5.8–5.11.

### partitioned_carry_chain  (role: extends)
mechanism: A full-width adder is cut at an arbitrary bit boundary so it can perform one full-width addition or two independent smaller additions. Multiplexers replace selected crossing generate signals with the upper carry-in, while AND gates suppress corresponding propagate signals. Sklansky graphs need only the signal pair originating at the boundary except at specified critical-path cuts.
choices:
  boundary_mechanism: carry_select_mux   # p.70, p.71
  per_lane_flags: UNKNOWN   # p.70
new_choices:
  partition_count: 2 — full-width or two independent additions   # p.70
slots:
  base_adder: parallel_prefix [topology=sklansky | brent_kung]   # p.71, p.72
  saturation: UNKNOWN   # p.70
parameters: n-bit adder cut between bits k-1 and k; figures illustrate 16-bit adders   # p.70, p.72
results:
| metric | value | unit | technology / device | baseline | condition | page |
| maximum inserted multiplexers | grows with log n | multiplexers | abstract | unpartitioned prefix adder | Brent-Kung and Sklansky solution replacing all crossing generate signals | p.71 |
| hardware cost and speed degradation | very small | qualitative | abstract | unpartitioned parallel-prefix adder | selective boundary-signal replacement | p.71 |
errors_and_checks: none
conditions: A Sklansky graph can always be converted without lengthening the critical path by removing the LSB from the graph when the cut would otherwise lie on the critical path.   # p.71
evidence: Section 5.6; Figures 5.12–5.14; Equations 5.12–5.14.

### prefix_and_incrementer  (role: defines)
mechanism: Setting one adder operand to zero removes redundant logic and reduces every carry chain or prefix tree to AND gates. The same construction supports decrementers, and all prefix principles used for adders remain applicable.
choices:
  structure: prefix_and_tree   # p.72
  topology: UNKNOWN   # p.72
  dual_direction: true   # p.72
new_choices:
  none
slots:
  none
parameters: n-bit increment/decrement by one bit   # p.72
results:
| metric | value | unit | technology / device | baseline | condition | page |
| size and speed | considerably smaller and faster | qualitative | abstract | comparable adder | constant-zero second operand | p.72 |
errors_and_checks: none
conditions: Parallel-prefix structures gain more from the AND-only carry recurrence than other speed-up structures.   # p.72
evidence: Section 5.7.2.

### prefix_comparator  (role: defines)
mechanism: Subtraction supplies comparison flags. Equality is the whole-word propagate signal and magnitude greater-or-equal is the subtraction carry-out; simple logic derives the remaining ordering relations.
choices:
  function: full_ordering   # p.72
  structure: subtractor_carry_out   # p.72
  radix: UNKNOWN   # p.72
new_choices:
  equality_source: whole_word_propagate — obtains equality without the sum path   # p.72
slots:
  none
parameters: n-bit binary operands   # p.72
results:
| metric | value | unit | technology / device | baseline | condition | page |
| equality flag logic | free | additional logic | abstract | parallel-prefix adder | whole-word propagate already exists | p.72 |
| greater-or-equal flag logic | free | additional logic | abstract | binary adder | subtraction carry-out already exists | p.72 |
errors_and_checks: none
conditions: Equality uses the zero flag from A-B, while greater-or-equal uses the carry-out from A-B.   # p.72
evidence: Section 5.7.3.

## taxonomy
Special adders
  Adders with flag generation
    carry flag from carry-out -> parallel_prefix   # p.63
    2's-complement overflow from adjacent carries -> prefix_flag_generation   # p.64
    zero flag for subtraction from whole-word propagate -> prefix_comparator   # p.64
    zero flag for addition/subtraction without carry propagation -> prefix_flag_generation   # p.64
    negative flag from sum MSB -> prefix_flag_generation   # p.64
  Adders for late input carry
    additional prefix level -> parallel_prefix   # p.64
    final operator row -> parallel_prefix   # p.64
  Adders with relaxed timing constraints
    mixed serial/parallel prefix -> parallel_prefix   # p.65
  Adders with non-equal bit arrival times
    late MSB/staggered MSB -> prefix_synthesis_nonuniform_arrival   # p.65
    late LSB/staggered LSB -> prefix_synthesis_nonuniform_arrival   # p.65
    late lower half/upper half/middle -> prefix_synthesis_nonuniform_arrival   # p.65
    early MSB/LSB output required times -> prefix_synthesis_nonuniform_arrival   # p.65
  Modulo adders
    modulo 2^n-1, double zero -> end_around_carry   # p.68
    modulo 2^n-1, single zero -> end_around_carry   # p.69
    modulo 2^n-1 modified carry-lookahead -> end_around_carry   # p.69
    modulo 2^n+1 diminished-one -> end_around_carry   # p.69
  Dual-size adders
    two-CPA composition -> partitioned_carry_chain   # p.70
    partitioned Sklansky prefix -> partitioned_carry_chain   # p.71
    partitioned Brent-Kung prefix -> partitioned_carry_chain   # p.71
  Related arithmetic operations
    2's-complement subtractor/adder-subtractor -> twos_complement_adder_subtractor   # p.71, p.72
    incrementer/decrementer -> prefix_and_incrementer   # p.72
    comparator -> prefix_comparator   # p.72

## primary_sources
* [CL92], 1992 — zero-flag calculation without carry propagation   # p.64
* [ENK94], 1994 — modulo 2^n-1 addition by modified carry-lookahead equations   # p.69
* [Okl94], 1994; [SO96], 1996 — Wallace-tree multiplier-final-addition arrival profile   # p.65

## new_families
### prefix_flag_generation  (domain: adder, closest: compound_flagged_prefix, why_not: compound_flagged_prefix produces alternative arithmetic results, while this mechanism produces carry/overflow/zero/negative status flags)
mechanism: Prefix carries directly supply carry and overflow flags. Whole-word propagate supplies a subtraction zero flag through an XOR/AND-tree path, while general addition/subtraction zero detection adds separate XNOR and AND logic. The negative flag is the sum MSB.
choices: flag_set: {carry, overflow, zero, negative}; zero_mode: {postsum_nor, subtraction_propagate, carry_free_add_sub}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| subtraction zero-flag overhead | log n | additional AND gates | abstract | prefix adder omitting whole-word propagate | whole-word propagate calculation | p.64 |
| overflow-flag overhead | 1 | XOR gate | abstract | prefix carries | carry-XOR formulation | p.64 |
evidence: p.63-p.64

### twos_complement_adder_subtractor  (domain: adder, closest: parallel_prefix, why_not: the selectable operand inversion and subtraction mode are not choices of any adder family)
mechanism: A subtractor complements one operand and fixes carry-in to one. A selectable adder/subtractor conditionally complements every bit of that operand with an XOR gate and uses the mode in the carry input.
choices: operation: {subtract_only, add_subtract}; complement_input: {fixed_invert, xor_controlled}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| gate-count increase | 2n | gates | abstract | arbitrary adder | selectable add/subtract | p.72 |
| delay increase | 2 | gate delays | abstract | arbitrary adder | selectable add/subtract | p.72 |
evidence: p.71-p.72

## space_gaps
* `parallel_prefix` lacks a late-input-carry/final-operator-row choice.   # p.64
* `prefix_synthesis_nonuniform_arrival.search_method` lacks the chapter's hand-optimized method.   # p.65
* `partitioned_carry_chain` lacks a partition-count/full-width-versus-dual-size choice.   # p.70
* The vocabulary lacks output required-time profiles for nonuniform prefix optimization.   # p.65

## open_questions
* The citation keys [CL92], [ENK94], [Okl94], and [SO96] cannot be expanded to author names from this chapter excerpt.
* The exact symbolic delay expressions in Section 5.2 and modulo Equations 5.8–5.11 require verification against the rendered PDF because several mathematical symbols are corrupted in the supplied text.
