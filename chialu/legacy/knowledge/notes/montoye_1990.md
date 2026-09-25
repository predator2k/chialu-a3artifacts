---
handle: montoye_1990
citation: R. K. Montoye, E. Hokenek, S. L. Runyon, "Design of the IBM RISC System/6000 Floating-Point Execution Unit", IBM Journal of Research and Development, 1990
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [fp64]
authority: landmark
pages_read: 12 / 12
---

## summary
The document describes the RS/6000 unified multiply-add-fused unit, which performs `(A × B) + C` as one operation with one rounding and a two-stage pipeline (pp.59-62). The implementation overlaps multiplication/alignment and addition/normalization through a Booth-recoded multiplier, `(7, 3)` reduction, a partially decoded shifter, a logarithmic adder, and leading-zero/one anticipation (pp.61-68). The fabricated FPU reaches 50 MFLOPS at 25 MHz (p.59).

## families
### classic_fma  (role: proposes)
mechanism: The MAF combines multiplication and addition in one unit. Multiplication and partial compression run in parallel with addend prenormalization; terminal addition runs in parallel with postnormalization. The addend shifts relative to a fixed product, and a leading-zero/one anticipator derives the normalization shift while addition proceeds. Rounding occurs once after the fused operation. One’s-complement add/increment uses an end-around carry for sign-magnitude operation.
choices:
  subsume_fp_add: true   # p.60
  negation_handling: end_around_carry   # p.61
  pipeline_depth: 2   # pp.61-62
new_choices:
  increment_return_path: addend_pipeline_or_multiplicand_pipeline — the rounding increment is performed through either pipeline according to the return path   # p.62
slots:
  align: full_align   # pp.61-62
  lza: lza   # pp.67-68
  cpa: conditional_sum   # pp.66-67
  round: injection   # p.62
  multiplier: booth_recoded_parallel   # pp.62-64
parameters: IEEE double precision; 56-bit multiplier; 160-bit alignment shifter; 53-bit incrementer; two pipeline stages; two-cycle behavior   # pp.61-66
results:
| metric | value | unit | technology / device | baseline | condition | page |
| peak execution rate | 50 | MFLOPS | RS/6000 FPU, node UNKNOWN (1990) | UNKNOWN | 25-MHz clock | p.59 |
| clock frequency | 25 | MHz | RS/6000 FPU, node UNKNOWN (1990) | UNKNOWN | peak rate 50 MFLOPS | p.59 |
| cycle time | 40 | ns | 1.2-µm gate-length CMOS / RS/6000 FPU (1990) | UNKNOWN | worst-case conditions | p.68 |
| power dissipation | 4 | W | 1.2-µm gate-length CMOS / RS/6000 FPU (1990) | UNKNOWN | operating chip | p.68 |
| die size | 12.7 × 12.7 | mm | triple-level-metal CMOS / RS/6000 FPU (1990) | UNKNOWN | complete FPU | p.68 |
errors_and_checks: The fused operation performs one rounding rather than separate multiply and add roundings; the implementation is IEEE-compatible, but no numerical ulp bound is reported (pp.60-62).
conditions: The unified unit reduces six internal connections to four and removes one adder/normalizer pair (p.60); the fused design increases adder width by 50 percent and adds one gate delay in the adder section (p.60); large-exponent-difference underflow bits affect only final rounding (p.61).
evidence: Multiply-add motivation and Figures 1-3 (pp.60-62); Dataflow Implementation (pp.62-68); chip data and summary (pp.68-69).

### booth_recoded_parallel  (role: instantiates)
mechanism: Booth recoding reduces an `N`-bit multiplication to `N/2` additions or subtractions. The 56-bit implementation combines Booth encoding with `(7, 3)` counters, which replace repeated `(3, 2)` carry-save stages to reduce long-wire stages and connectivity. A final logarithmic carry-propagate addition combines the remaining terms.
choices:
new_choices:
  reduction_counter: 7_to_3 — seven equal-weight objects produce outputs of binary weights 1, 2, and 4   # p.63
slots:
  reduction: counter_7_3_reduction_tree [outside domain]   # pp.63-64
parameters: 56-bit multiplier for a 53-bit IEEE or 56-bit HEX double-precision unit; `N/2` Booth terms; first-stage seven 4-input multiplexors; second-stage 7-input/3-output cell   # pp.62-64
results:
| metric | value | unit | technology / device | baseline | condition | page |
| multiplier area | 4 × 5 | mm | 1.2-µm CMOS / RS/6000 multiplier (1990) | UNKNOWN | complete 56-bit multiplier | p.64 |
errors_and_checks: none
conditions: The `(7, 3)` counter uses ten connections to remove four bits, while a `(3, 2)` adder uses five connections to remove one bit (p.63); the `(7, 3)` stages reduce remaining terms by `7/3` rather than `3/2`, reducing the number of long-wire stages by a factor of 2.5 (p.63).
evidence: Multiplier section and Figures 5-6 (pp.62-64).

### conditional_sum  (role: instantiates)
mechanism: The adder recursively partitions an `N`-bit addition into a low half and two speculative high-half additions, one for each carry-in. Carry selection doubles the number of resolved carry signals at each stage. Unused evaluation locations hold progressively larger buffers, keeping fan-out about three while retaining logarithmic delay.
choices:
  selection_radix: 2   # pp.66-67
new_choices:
  progressive_buffering: true — gate drive and load double at each stage in otherwise unused evaluation locations   # p.67
slots: none
parameters: 106+ bit adder; `N` as large as 160; 53-bit following incrementer; fan-out about three; `N log(N)` area   # pp.66-67
results:
| metric | value | unit | technology / device | baseline | condition | page |
| maximum fan-out | about 3 | fan-out | CMOS / RS/6000 adder (1990) | UNKNOWN | each recursive section | p.67 |
errors_and_checks: none
conditions: Carry-skip delay is described as significantly less competitive at 160 bits than at 32 bits (p.66); the construction targets logarithmic delay while including wiring and fan-out delays (pp.66-67).
evidence: Logarithmic adders section and Figures 9-10 (pp.66-67).

### barrel_mux_tree  (role: extends)
mechanism: The partial-decode shifter divides the shift amount between an eight-way first-stage multiplexor and a five-way second-stage multiplexor. The 32-bit rotator performs coarse rotations of `0, 4, 8, 12, 16, 20, 24, 28` followed by shifts of `0, 1, 2, 3, 4`. The 160-bit alignment shifter uses binary preshifting, coarse 16-bit-position shifting, and a final four-bit-position shift while collecting sticky bits.
choices:
  stage_radix: mixed_8_5 [outside domain]   # p.65
  direction_handling: amount_negation   # p.65
  stage_order: large_shift_first   # pp.65-66
  sticky_collect: true   # p.66
new_choices:
  decode_style: partial_decode — separate control groups drive the coarse and fine multiplexor stages   # p.65
slots: none
parameters: 32-bit bidirectional rotator; 160-bit alignment shifter; two multiplexor rows in the rotator data path   # pp.64-66
results:
| metric | value | unit | technology / device | baseline | condition | page |
| data-path delay | 2 | ns | 1-µm CMOS / 32-bit rotator (1990) | UNKNOWN | single-stage data path | p.66 |
| control-path delay | 6 | ns | 1-µm CMOS / 32-bit rotator (1990) | UNKNOWN | four-stage control path | p.66 |
| shift delay | 6 | ns | node UNKNOWN / 160-bit shifter (1990) | UNKNOWN | after shift amount is calculated; includes sticky-bit accumulation and post-complementation | p.66 |
errors_and_checks: Sticky-bit accumulation supports IEEE rounding, but no error bound is reported (p.66).
conditions: Partial decoding reduces control/data wiring relative to the fully decoded and fully encoded alternatives (pp.64-65).
evidence: Shifters section and Figures 7-8 (pp.64-66).

## new_families
### counter_7_3_reduction_tree  (domain: mul: integer multipliers, closest: carry_save_array, why_not: the vocabulary provides 3:2 carry-save and 4:2 compressor reductions but no seven-input/three-output counter tree)
mechanism: Each counter accepts seven equal-weight objects and produces three outputs with binary weights 1, 2, and 4. The tree reduces the number of remaining terms by `7/3` per stage. The implementation trades a more complex/slower cell for fewer long wires and fewer reduction stages.
choices: counter_arity: {7_to_3}; cell_implementation: {full_adder_based}; wiring_objective: {minimum_long_wire_stages}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| stage-count reduction factor | 2.5 | factor | CMOS / RS/6000 multiplier (1990) | `(3, 2)` Wallace reduction | comparison of `7/3` and `3/2` term-reduction factors | p.63 |
| multiplier area | 4 × 5 | mm | 1.2-µm CMOS / RS/6000 multiplier (1990) | UNKNOWN | Booth encoding plus `(7, 3)` reduction | p.64 |
evidence: Multiplier section, especially the `(7, 3)` comparison and Figures 5-6 (pp.63-64).

## space_gaps
* `booth_recoded_parallel.reduction` needs `counter_7_3_reduction_tree` as a slot value (pp.63-64).
* `barrel_mux_tree.stage_radix` needs mixed per-stage radices and the value 5 for the documented eight-way/five-way tree (p.65).
* `barrel_mux_tree` needs a `decode_style` choice covering partial decoding between fully decoded and fully encoded controls (pp.64-65).

## open_questions
* The text describes adder widths as 106+ bits and `N` as large as 160, while the summary calls the adder/accumulator 168 bits; the precise implemented width is not reconciled (pp.66, 69).
* The document states `N/2` Booth terms but does not name the Booth radix (pp.62-63).
