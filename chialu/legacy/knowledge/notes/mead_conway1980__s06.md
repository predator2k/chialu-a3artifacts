---
handle: mead_conway1980#s06
parent: mead_conway1980
citation: C. Mead, L. Conway, "Introduction to VLSI Systems", Addison-Wesley, 1980.
chapter: Chapter 5: The Design of a Data Processing Engine
pdf_pages: 192-257
status: ok
kind: book_chapter
unit_classes: [BINARY_ALU]
formats: [16-bit binary]
authority: textbook
pages_read: 66 / 66
---

## summary
The chapter defines the 16-bit OM2 datapath, including a precharged Manchester carry chain, programmable ALU logic, and a single-stage crossbar barrel shifter. The chapter provides transistor-delay estimates for the carry chain and a functional specification of the complete machine. The chapter also instantiates a 16-iteration shift-and-add multiplication program.

## families
### manchester_carry_chain  (role: instantiates)
mechanism: Each bit uses a pass transistor to propagate carry, a transistor to kill carry by grounding carry-out, and a precharge transistor that charges carry-out during the ALU null period. The precharged chain avoids propagating a slow high signal through pass transistors. Doubly inverting buffers replace the direct pass-chain connection every fourth stage.
choices:
  chain_segment_length: 4   # p.203
  circuit_style: dynamic   # p.195
  variable_skip: UNKNOWN   # p.195
new_choices:
  precharge_phase: ALU null period — precharges carry nodes before evaluation   # p.195
slots:
  none
parameters: 16-bit ALU; buffering after every 4 stages; n=4 within each unbuffered segment   # p.203, p.230
results:
| metric | value | unit | technology / device | baseline | condition | page |
| carry-stage capacitance | ~4.5 | pass-transistor gate capacitances | abstract | none | metal and diffusion occupy ~15 and ~8 times the gate area, with capacitances per area of ~0.1 and 0.2 times gate capacitance | p.230 |
| unbuffered pass-chain delay | ~n² | transistor transit times | abstract | transistor transit time | n pass-transistor stages | p.230 |
| 4-bit carry-chain delay | ~4.5*16T = 72τ | transistor transit times | abstract | none | n=4 | p.230 |
| double-inverter buffer delay | ~30τ | transistor transit times | abstract | none | inverter ratio k is ~8 with stray capacitance included | p.230 |
| carry time per 4-bit block | ~100 | transistor transit times | abstract | none | four Manchester stages plus the double-inverter buffer | p.230 |
| Phase 1 time | ~50T | transistor transit times | abstract | none | OM2 clock estimate | p.230 |
| Phase 2 time | ~400τ | transistor transit times | abstract | none | four buffered 4-bit carry blocks | p.230 |
| minimum clock period | ~450τ | transistor transit times | abstract | none | complete OM2 cycle | p.230 |
| transistor transit time | ~0.3 | ns | MOS / node UNKNOWN, 1978 | none | technology estimate for 1978 | p.230 |
| minimum clock period | ~135 | ns | MOS / node UNKNOWN, 1978 | none | τ~0.3 ns | p.230 |
errors_and_checks: Kill and propagate must not both be high; the functional specification marks the resulting carry as undefined.   # p.253
conditions: Look-ahead schemes were rejected because simulations showed considerable complexity without much performance gain.   # p.195
conditions: The Manchester chain propagates low carry signals quickly but is particularly limited when propagating high carry signals in MOS technology.   # p.195
conditions: Precharging during the null period avoids slow high-signal propagation through pass transistors.   # p.195
evidence: Section “The Arithmetic Logic Unit”; Figures 2, 3, 6, and 6a; OM2 functional specification and ISP description.

### sequential_shift_add  (role: instantiates)
mechanism: The multiplication program shifts X left by one bit, shifts the partial result Z left by one bit, and conditionally adds Y when the removed most-significant bit of X is 1. The controller repeats the instruction sequence until 16 iterations have completed.
choices:
  bits_per_cycle: 1   # p.243
  accumulator_form: carry_propagate   # p.243
  string_skipping: UNKNOWN   # p.243
new_choices:
  conditional_add_control: shifted_operand_msb — the removed MSB controls the multiply-step addition   # p.243
slots:
  step_adder: manchester_carry_chain [chain_segment_length=4, circuit_style=dynamic]   # p.195, p.243
parameters: 16-bit operands; 16 iterations   # p.243
results:
| metric | value | unit | technology / device | baseline | condition | page |
| iteration count | 16 | iterations | abstract | none | 16-bit integer multiplication | p.243 |
errors_and_checks: none
conditions: The controller counter signals completion after 16 iterations.   # p.243
conditions: The conditional multiply operation adds Y without a microcode branch when the shifted-out bit is 1.   # p.238, p.243
evidence: “Programming Examples”; Figures 6a through 6d.

## taxonomy
* Arithmetic-logic carry schemes   # p.195
  * Look-ahead schemes evaluated and rejected -> carry_lookahead   # p.195
  * Manchester-type pass-transistor carry chain -> manchester_carry_chain   # p.195
    * Precharged carry nodes -> manchester_carry_chain   # p.195
    * Double-inverter buffering every fourth stage -> manchester_carry_chain   # p.203
* Shifter structures   # p.209
  * Single-bit right-left shifter integrated with the ALU input multiplexer -> unmapped   # p.209
  * Multibit shifter composed from repeated single shifts -> unmapped   # p.209
  * Fully general n-by-n crossbar switch -> unmapped   # p.209, p.212
  * Crossbar wired for a one-of-n barrel-shift constant -> unmapped   # p.209, p.212
  * Split-wire, two-bus crossbar extracting a word across the A/B boundary -> unmapped   # p.211, p.213
* One-of-n shift-control decoders   # p.216
  * NOR-form decoder -> unmapped   # p.216, p.218
  * NAND-form decoder -> unmapped   # p.216, p.218
  * Complementary decoder -> unmapped   # p.220
* Programmed multiplication   # p.243
  * One-bit-per-iteration conditional shift-and-add -> sequential_shift_add   # p.243

## primary_sources
* Ivan Sutherland, UNKNOWN — sharing a microcode wire between ALU-function and ALU-input-selection bits on opposite phases   # p.208
* Ivan Sutherland, UNKNOWN — complementary one-of-n decoder form   # p.220

## new_families
### single_stage_crossbar_barrel_shifter  (domain: shift: shifters, closest: barrel_mux_tree, why_not: The chapter uses one crossbar plane rather than a logarithmic tree of mux stages.)
mechanism: An n-by-n grid of pass transistors connects every input bit position to every output position. Arbitrary crossbar control uses n2 bits, while barrel-shift wiring connects crosspoints diagonally and selects one diagonal with a one-of-n shift constant. OM2 splits each vertical path between the A and B buses, concatenating two 16-bit buses and selecting a continuous 16-bit output window.
choices:
  crosspoint_control: {arbitrary_n2, diagonal_one_hot_n}   # p.209
  input_form: {single_n_bit_bus, split_two_bus_2n_window}   # p.209, p.211
  output_precharge: Bool   # p.209
  literal_port: Bool   # p.211
  decoder_form: {nor, nand, complementary}   # p.216, p.220
results:
| metric | value | unit | technology / device | baseline | condition | page |
| repeated single-shift delay | n2 | delay | abstract | single-stage crossbar | multibit shift assembled from single-bit shifts | p.209 |
| arbitrary crossbar control | n2 | control bits | abstract | simple barrel-shift wiring | every input may connect to every output | p.209 |
| simple barrel-shift control | n | one-hot wires | abstract | arbitrary crossbar control | one and only one shift-constant wire is high | p.209 |
| input span | 32 | bits | abstract | 16-bit single bus | A and B buses concatenated | p.235 |
| output window | 16 | bits | abstract | none | OM2 shifter | p.235 |
evidence: Figures 12 through 21; “Barrel Shifter”; OM2 “Shifter” specification, pp.209-220 and p.235.

### programmable_pkr_alu  (domain: adder: carry-propagate adders, closest: manchester_carry_chain, why_not: The Manchester family covers the carry network but not the programmable P/K/R truth-table fabric that defines the complete ALU function.)
mechanism: Two four-control function blocks decode A/B combinations to produce carry-propagate and carry-kill signals. A third four-control function block combines propagate and carry-in to produce the result. The 12 P/K/R bits leave the ALU operation set programmable, while conditional controls modify selected truth-table entries according to the flag bit.
choices:
  propagate_function: 4-bit truth table over A/B   # p.200, p.236
  kill_function: 4-bit truth table over A/B   # p.200, p.236
  result_function: 4-bit truth table over propagate/carry-in   # p.200, p.236
  carry_in_source: {0, flag, 1, complemented_flag}   # p.241
  conditional_operation: {unconditional, multiply_step, divide_step, and_or}   # p.241
results:
| metric | value | unit | technology / device | baseline | condition | page |
| functions per two-input function block | sixteen | logic functions | abstract | none | four decoded input combinations controlled independently | p.200 |
| ALU function-control width | 12 | bits | abstract | none | four P, four K, and four R controls | p.200 |
| flag-dependent conditional operation | one | cycle | abstract | controller branch to two separate instructions | multiply/divide/And-Or conditional operation | p.241 |
evidence: Figures 4 through 7; OM2 ALU and programming specification, pp.200-204 and pp.236-243.

## space_gaps
* `barrel_mux_tree` lacks the chapter’s single-stage crossbar topology and one-of-n diagonal selection.   # p.209
* The shifter vocabulary lacks split vertical wires that concatenate two buses for cross-word field extraction.   # p.211
* The ALU vocabulary lacks independently programmed P/K/R truth-table blocks around a carry chain.   # p.200

## open_questions
* The cited “reference 4, chapter 1” for the Manchester carry chain is not identified in this chapter’s reference list.   # p.195, p.253
* The fabrication process and node underlying τ~0.3 ns and the ~135 ns clock estimate are not reported.   # p.230
