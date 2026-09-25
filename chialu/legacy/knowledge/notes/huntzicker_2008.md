---
handle: huntzicker_2008
citation: S. Huntzicker, M. Dayringer, J. Soprano, A. Weerasinghe, D. M. Harris, D. Patil, "Energy-Delay Tradeoffs in 32-bit Static Shifter Designs", Proc. IEEE ICCD, 2008
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int32]
authority: incremental
pages_read: 626-632 / 7
---

## summary
The paper compares energy-delay tradeoffs for 32-bit static barrel and funnel shifters across multiplexer valency/circuit style, supported operations, control arrival, and physical placement (pp.626-632). A folded 4-8 funnel has the lowest energy and energy-delay product, while a 5-8 barrel has the lowest delay when all five shift/rotate operations are supported (p.632).

## families
### barrel_mux_tree  (role: compares)
mechanism: The barrel architecture rotates through staged multiplexers and then masks unwanted bits for shifts. The full-function design incorporates a one-bit preshift into the first rotation stage and complements the shift amount for left shifts, which avoids an adder in the amount logic. The evaluated networks include the base 3-2-2-2-2 structure and higher-valency 3-4-4 and 5-8 structures (pp.627, 630).
choices:
  stage_radix: mixed 3-2-2-2-2 / 3-4-4 / 5-8 [outside domain]   # pp.627, 630
  direction_handling: amount_negation   # p.627
  stage_order: small_shift_first   # p.630
new_choices:
  multiplexer_circuit: {ganged_tristate, pass_transistor, fanout_splitting} — circuit implementation of each shifting multiplexer   # pp.629-630
  placement: {base, zhu_swizzling, hillebrand_swizzling} — ordering of multiplexers to alter wraparound-wire lengths   # pp.627, 631
  sizing_granularity: {uniform, uniquified} — whether multiplexers in one row share a size or long-wire drivers are upsized separately   # p.631
  operation_subset: {all_five, shifts_only, right_rotate_only} — supported combinations of ROR/ROL/LSR/LSL/ASR   # pp.626, 629
slots: none
parameters: 32-bit data; 5-bit shift amount; five operations ROR/ROL/LSR/LSL/ASR; five stages in the valency-2 form   # pp.626-627
results:
| metric | value | unit | technology / device | baseline | condition | page |
| minimum delay | 340 | ps | 90 nm, 2008 | best funnel design | 5-8 barrel, all shift types, simultaneous input arrival | p.632 |
| minimum delay | 12.6 | FO4 inverter delays | 90 nm, 2008 | best funnel design | 5-8 barrel, all shift types, simultaneous input arrival | p.632 |
| energy-delay product | 441 | pJ-ns | 90 nm, 2008 | funnel 4-8 folded at 394 pJ-ns | best barrel design | p.632 |
| energy-delay curve crossover | 360 | ps | 90 nm, 2008 | folded funnel 4-8 | barrel 5-8 has lower delay below the crossover; funnel has lower energy above it | p.632 |
errors_and_checks: none
conditions: A right-rotate-only barrel removes the preshift/mask stages and saves substantial energy/delay, while removing rotations but retaining shifts removes only two masker AND gates (p.629). Fanout-splitting lowers energy for valency-2 barrels, but higher-valency designs remain more competitive (pp.629-630, 632). Bit swizzling helps with uniform sizing, while uniquified sizing eliminates its benefit by upsizing only wraparound-wire drivers (pp.631-632).
evidence: Fig. 1 and Figs. 2-4 (p.627); Figs. 7, 9, 10 (pp.629-630); Figs. 14-15 (p.631); Fig. 17 and Conclusion (p.632).

### funnel  (role: compares)
mechanism: The funnel architecture forms a 63-bit source word from duplicated input bits, zeros, or the sign bit and selects a 32-bit window through multiplexer stages. Left shifts complement the shift amount to select the window corresponding to 31-k. The study evaluates five-stage valency-2, 2-4-4, and 4-8 networks plus naïve/folded floorplans (pp.627, 630-632).
choices:
  window_mux_radix: mixed 2-2-2-2-2 / 2-4-4 / 4-8 [outside domain]   # pp.627, 630
  input_forming: duplicate_for_rotate / sign_extend / zero_fill [outside domain]   # p.628
  amount_preprocess: ones_complement_for_left [outside domain]   # p.628
new_choices:
  multiplexer_circuit: {ganged_tristate, pass_transistor, fanout_splitting} — circuit implementation of the funneling stages   # pp.629-630
  floorplan: {naive_7_row, folded_11_row, compact_folded_8_row, folded_overhang} — placement of stages wider than the 32-bit datapath   # pp.630-632
  control_arrival: {simultaneous, shift_type_early} — arrival relationship between data and left/shift/arithmetic controls   # pp.626, 629
  operation_subset: {all_five, shifts_only, right_rotate_only} — supported combinations of ROR/ROL/LSR/LSL/ASR   # pp.626, 629
slots: none
parameters: 32-bit output selected from a 63-bit source word; five valency-2 levels in the base design; evaluated higher-valency structures 2-4-4 and 4-8   # pp.627-628, 630
results:
| metric | value | unit | technology / device | baseline | condition | page |
| knee delay | 440 | ps | 90 nm, 2008 | evaluated barrel designs | 4-8 static-multiplexer funnel | p.626 |
| knee energy | 0.9 | pJ per shift | 90 nm, 2008 | evaluated barrel designs | 4-8 static-multiplexer funnel at 440 ps | p.626 |
| minimum energy | 733 | fJ | 90 nm, 2008 | best barrel design | best funnel design, all shift types | p.632 |
| energy-delay product | 394 | pJ-ns | 90 nm, 2008 | best barrel design at 441 pJ-ns | best funnel design | p.632 |
| area saving | 25 | % | 90 nm, 2008 | folded 11-row floorplan | compact folded 8-row floorplan | p.631 |
errors_and_checks: none
conditions: Early shift-type controls shorten the funnel critical path because input generation can begin before data arrival (p.629). Shift-only operation removes two input-generator gates, while right-rotate-only operation removes the input generator but retains more early-stage multiplexers than the barrel rotator (p.629). The 11-row floorplan has the least reported energy under optimistic wire assumptions, while the 8-row floorplan is competitive and smaller (p.631). Fixed input/output loads may affect the relative positions of funnel and barrel curves (p.632).
evidence: Table 2 and Fig. 5 (p.628); Figs. 6-10 (pp.629-630); Figs. 11-13 (pp.630-631); Figs. 16-17 and Conclusion (p.632).

### masked_merged  (role: instantiates)
mechanism: The barrel shifter rotates first and applies a decoded mask afterward. A binary-to-thermometer converter generates per-bit mask information through AND gates and OR trees. The mask application uses inverting logic so the final rotating-multiplexer inverter can be removed, and the masker adds one gate to the data critical path (p.627).
choices:
  mask_generator: thermometer_decode   # p.627
  merge_style: and_or_merge   # p.627
  deposit_path: false   # pp.626-627
new_choices:
  arithmetic_fill: {zero, sign} — the mask selects logical zero fill or arithmetic sign extension   # pp.626-627
slots:
  rotator: barrel_mux_tree [stage_radix=mixed 3-2-2-2-2 / 3-4-4 / 5-8 [outside domain]]   # pp.627, 630
parameters: 32-bit mask; five full-function operations; one added gate from rotated value x_b to output y   # pp.626-627
results:
| metric | value | unit | technology / device | baseline | condition | page |
| hardware removed | 2 | AND gates | 90 nm, 2008 | full barrel masker | shifts-only barrel with rotation operations removed | p.629 |
errors_and_checks: none
conditions: The masker is required for shift operations but can be removed for a right-rotate-only barrel (p.629). Thermometer-mask nodes near both extremes have low switching activity, which requires node-specific activity factors for energy estimation (p.628).
evidence: Figs. 1, 3, and 4 (p.627); activity-factor analysis (p.628); Fig. 7 discussion (p.629).

## new_families
none

## space_gaps
* `barrel_mux_tree.stage_radix` needs mixed per-stage valency sequences such as 3-2-2-2-2, 3-4-4, and 5-8 rather than one radix for the entire network (pp.627, 630).
* `funnel.window_mux_radix` needs mixed sequences such as 2-2-2-2-2, 2-4-4, and 4-8 (pp.627, 630).
* `funnel.amount_preprocess` lacks the documented complement-for-left-shift value used to implement selection by 31-k (p.628).
* Barrel/funnel families lack circuit-style, physical-floorplan, per-device-sizing, supported-operation, and control-arrival choices that materially change their energy-delay curves (pp.626-632).

## open_questions
* The conclusion prints energy-delay products of 394 pJ-ns and 441 without restating the unit after 441; the merge pass must not reinterpret or normalize these printed values (p.632).
* The pass-transistor design with output inverters only was expected to help but could not be modeled in SCOT, so the paper reports no comparative result for that circuit (p.629).
