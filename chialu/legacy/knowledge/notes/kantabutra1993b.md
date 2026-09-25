---
handle: kantabutra1993b
citation: V. Kantabutra, "Accelerated Two-Level Carry-Skip Adders - A Type of Very Fast Adders", IEEE Transactions on Computers, vol. 42, no. 11, pp. 1389-1393, 1993.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary60, fp64]
authority: incremental
pages_read: 1389-1393 / 5
---

## summary
The paper proposes an accelerated two-level carry-skip adder whose section sizes are bimodal while block sizes within each section are monotonic. A delay-constrained construction produces a 60-b static CMOS adder with an approximately 12.6 ns simulated delay. The extra direct carry paths make the design slightly more complex than a conventional two-level carry-skip adder.

## families
### carry_skip  (role: extends)
mechanism: The adder has an ascending low-order half and a descending high-order half. Section sizes increase toward the center and then decrease, while block sizes increase within ascending sections and decrease within descending sections. Ripple cells propagate carries inside blocks. Multiplexers bypass blocks or whole sections. Selected sections receive direct carry paths so an incoming carry avoids an otherwise critical sequence of skips and ripples. The construction starts with a two-block central nucleus and adds the largest blocks and sections that satisfy a specified carry-delay bound. # p.1389, pp.1391-1393
choices:
  block_width: variable_by_position [outside domain]   # pp.1391-1392
  block_sizing: unimodal_within_each_section [outside domain]   # pp.1389,1391
  skip_levels: 2   # p.1389
  skip_gate: mux   # p.1390
new_choices:
  section_sizing: bimodal — section widths increase toward the center in the ascending half and decrease in the descending half   # pp.1389,1391
  section_block_order: ascending_or_descending — block widths increase in low-order sections and decrease in high-order sections   # pp.1389,1391
  direct_section_paths: selected_sections — extra mux paths bypass critical portions of sections   # pp.1390,1392-1393
  optimization_method: delay_constrained_growth — a central nucleus is expanded with maximum-sized feasible blocks and sections   # pp.1391-1393
  circuit_style: static_cmos — the example uses static CMOS ripple cells and multiplexers   # pp.1389-1391
slots:
  block_adder: ripple_carry   # pp.1389-1390
parameters: 60-b operands; two carry-skip levels; 11 ns carry-delay design bound; 6-b blocks in the two-block nucleus; example block widths include 1 b, 2 b, 3 b, 4 b, 5 b, and 6 b; final-sum delay below 1.6 ns   # pp.1391-1393
results:
| metric | value | unit | technology / device | baseline | condition | page |
| simulated adder delay | approximately 12.6 | ns | 2-µm CMOS; 1993 | 66-b conventional two-level carry-skip adder in [5], 58 ns | 60-b accelerated two-level carry-skip adder; PRECISE simulation based on SPICE2G | p.1389 |
| ripple-cell carry delay | 0.8 | ns | 2-µm CMOS; 1993 | none | circuit and load configuration in Fig. 3 | p.1390 |
| regular multiplexer data delay | 1.1 | ns | 2-µm CMOS; 1993 | none | circuit and load configuration in Fig. 3; long-wire drivers can be resized to the same delay | p.1390 |
| three-input multiplexer select-circuit delay | less than 3.6 | ns | 2-µm CMOS; 1993 | 6-cell ripple delay of 0.8 × 6 ns | simulated select circuit associated with Fig. 1 | p.1391 |
| final-sum delay after most-significant carry input | less than 1.6 | ns | 2-µm CMOS; 1993 | none | simulated circuit components | p.1391 |
errors_and_checks: none
conditions: The design can exceed the speed of conventional two-level carry-skip adders but uses slightly more skip circuitry. Regular two-level adders designed by Turrini’s method may attain comparable speed. Carry-skip adders are described as smaller but not as fast as the fastest carry-lookahead adders. The wire-delay argument assumes reasonable layouts and states that metal delay should be insignificant for the presented 2-µm design and smaller technologies. # pp.1389,1393
evidence: Sections II-V; Figs. 1-6; component simulations on pp.1390-1391; construction example on pp.1391-1393.

## new_families
none

## space_gaps
* `carry_skip.block_sizing` lacks a value for monotonic block sizing within each section, which the paper distinguishes from conventional bimodal within-section sizing. # pp.1389,1391
* `carry_skip` lacks a section-sizing choice for the paper’s bimodal sequence of section widths. # pp.1389,1391
* `carry_skip` lacks a choice for direct carry paths that bypass critical portions of selected sections. # pp.1390,1392-1393
* `carry_skip` lacks a design-method choice for growth from a central nucleus under a specified delay bound. # pp.1391-1393

## open_questions
* The paper says the construction is “just about” maximal and calls the difficulty of proving the relevant exchange argument messy, so it does not establish a formal global-optimality proof for every resulting width assignment. # p.1392
* Fig. 6 contains the complete 60-b block/section layout, but the text does not enumerate every final block width independently of the figure. # pp.1392-1393
