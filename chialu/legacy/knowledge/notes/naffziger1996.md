---
handle: naffziger1996
citation: S. Naffziger, "A Sub-Nanosecond 0.5 um 64 b Adder Design", IEEE International Solid-State Circuits Conference (ISSCC), pp. 362-363, 1996.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int64]
authority: landmark
pages_read: 362-363 / 2
---

## summary
The paper presents a 64b adder that combines Ling pseudo-carry equations, 4b carry lookahead, distributed Manchester carry generation, and carry-select quadrants. The dual-rail dynamic CMOS implementation reports a 0.93ns nominal data-to-sum delay, 6924 transistors, and 0.246mm2 layout area.

## families
### ling_prefix  (role: extends)
mechanism: A 4b Ling pseudo-carry H4 replaces the conventional C4 expression, with C4 recovered as H4*P3. Defining propagate as operand OR makes one term redundant, so H4 is expanded directly in the operands and generated in one fanin-4 dynamic gate. The carry chain is shifted by one bit, and a special C3 term combines with G0 to hide pseudo-carry-to-real-carry conversion. # p.362
choices:
  pseudo_carry_group: 4   # p.362
  sum_recovery: late_select_mux   # p.362
new_choices:
  circuit_style: dual_rail_dynamic_cmos — dual-rail dynamic gates provide the required fanin/dot-OR behavior   # p.362
  pseudo_carry_generation: direct_operand_expansion — H4 is generated directly from A/B operands rather than separate P/G terms   # p.362
slots:
  none
parameters: 64b; techniques stated to support widths from 13b to 112b; 4b H/I groups; four 16b quadrants; 4-gate critical path   # p.362
results:
| metric | value | unit | technology / device | baseline | condition | page |
| addition latency | <1 | ns | 0.5um CMOS; 1996 | UNKNOWN | full 64b operands-to-result path under nominal conditions; equivalent to 7 fanout-of-4 inverter delays | p.362 |
| simulated data-to-sum delay | 0.93 | ns | 0.5um CMOS; layout stated as 0.6um geometry; 1996 | UNKNOWN | nominal process and voltage; processor operating frequency confirms the simulation | p.362 |
| critical-path depth | 4 | gate delays | 0.5um CMOS; 1996 | traditional group-of-2 CLA: 8 gate delays | H4/I4 generation, C16 generation, long-carry generation, and sum select | p.362 |
| transistor count | 6924 | FETs | 0.6um geometry, 3 metal layers; 1996 | UNKNOWN | 64b sum implementation | p.362 |
| layout area | 0.246 | mm2 | 0.6um geometry, 3 metal layers; 1996 | UNKNOWN | 96x2560um layout | p.362 |
errors_and_checks: none
conditions: The circuit requires dual monotonic DCVS inputs and produces a dual monotonic sum. # p.362 The design depends on the high gain/fanin and precharged-node wired-OR capability of dynamic CMOS. # p.362 The reported delay assumes nominal process and voltage conditions. # p.362
evidence: p.362 equations for C4/H4 and direct H4 expansion; Figs. 1-5 on pp.362-363; implementation paragraph on p.362

### carry_lookahead  (role: instantiates)
mechanism: Operand-derived H4 and I4 terms represent groups of 4 bits. Four H/I groups are combined in a distributed Manchester gate to generate the carries within a 16b quadrant, and one further gate produces the long carry-select signals for the upper quadrants. # p.362
choices:
  group_size: 4   # p.362
  levels: 3   # p.362
  intergroup_carry: select   # p.362
new_choices:
  group_generate_form: ling_h_i — the hierarchy combines Ling H and I terms rather than conventional G/P terms   # p.362
slots:
  none
parameters: 4b groups; 16b quadrants; 64b total width   # p.362
results:
| metric | value | unit | technology / device | baseline | condition | page |
| conventional group-of-4 CLA depth | 5 | gate delays | UNKNOWN; 1996 | group-of-2 CLA: 8 gate delays | calculated as 1 + log4[64] + 1 | p.362 |
errors_and_checks: none
conditions: The 4b propagate terms must be calculated at least as quickly as the H4 terms so higher-level lookaheads are not delayed. # p.362
evidence: carry-lookahead equations and hierarchy on p.362; Fig. 4 on p.363

### carry_select  (role: instantiates)
mechanism: Each 16b quadrant performs a short carry ripple in parallel for both possible carry inputs. The long lookahead path supplies the final select signal, while local fanout-of-1 carries reach each sum gate just before that select. Carry selection and sum generation are fused into one final gate. # p.362
choices:
  block_sizing: uniform   # p.362
  duplication: full_duplicate   # p.362
  select_source: lookahead_tree   # p.362
new_choices:
  select_sum_fusion: fused_one_gate — the carry select and sum generation occur in a single gate   # p.362
slots:
  block_adder: manchester_carry_chain [circuit_style=dynamic]   # p.362
parameters: four 16b quadrants; two local carry values per quadrant; final select/sum gate   # p.362
results:
| metric | value | unit | technology / device | baseline | condition | page |
| critical-path sum-select stage | 1 | gate | 0.5um CMOS; 1996 | UNKNOWN | final carry selection and sum generation | p.362 |
errors_and_checks: none
conditions: The local carry ripple must finish just before the long carry-select signal reaches each sum gate. # p.362
evidence: carry-select description on p.362; carry ripple/sum-select circuits in Figs. 2-4 on p.363

### manchester_carry_chain  (role: instantiates)
mechanism: A distributed Manchester gate combines four 4b H/I groups inside each 16b quadrant. Dynamic CMOS multiple-NFET pulldown legs reproduce wired-OR behavior on a precharged node, allowing H4 and I4 to be generated directly from the operands. # p.362
choices:
  circuit_style: dynamic   # p.362
new_choices:
  group_term_inputs: ling_h_i — the distributed chain consumes Ling pseudo-generate and propagate terms   # p.362
slots:
  none
parameters: four H/I groups per 16b quadrant; fanout-of-1 local carry ripple   # p.362
results:
| metric | value | unit | technology / device | baseline | condition | page |
| local ripple depth | 4 | gates | 0.5um CMOS; 1996 | UNKNOWN | short carry ripple operating in parallel with long-carry generation | p.363 |
errors_and_checks: none
conditions: Dynamic CMOS supplies the fanin and wired-OR behavior used by the distributed Manchester implementation. # p.362
evidence: distributed Manchester equation and circuit description on p.362; Figs. 1, 2, and 4 on p.363

## new_families
none

## space_gaps
* ling_prefix lacks a circuit_style choice for the dual-rail dynamic CMOS implementation that enables direct H4 generation. # p.362
* ling_prefix lacks a pseudo_carry_generation choice distinguishing direct operand expansion from separate P/G generation. # p.362
* carry_select lacks a select_sum_fusion choice for the single-gate carry-select/sum stage. # p.362
* carry_lookahead lacks a group_generate_form choice for a hierarchy built from Ling H/I terms. # p.362

## open_questions
* The paper calls the design 0.5um CMOS but states that the layout uses 0.6um geometry; the merge pass must preserve both statements. # p.362
* The paper does not identify a named prefix topology for the Ling hierarchy. # p.362
* The paper does not state whether the four-group distributed Manchester structure represents a 4b or 16b chain_segment_length in the registry vocabulary. # p.362
