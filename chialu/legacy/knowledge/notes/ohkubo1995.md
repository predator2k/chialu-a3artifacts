---
handle: ohkubo1995
citation: N. Ohkubo, M. Suzuki, T. Shinbo, T. Yamanaka, A. Shimizu, K. Sasaki, Y. Nakagome, "A 4.4-ns CMOS 54x54-b Multiplier Using Pass-Transistor Multiplexer", IEEE Journal of Solid-State Circuits, vol. 30, 1995
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [fp64]
authority: incremental
pages_read: 4 / 4 (pp.599-602)
---

## summary
The document implements a 54 X 54-b multiplier for double-precision mantissa multiplication using Booth partial-product generation, a four-stage Wallace tree of proposed pass-transistor 4-2 compressors, and a 108-bit conditional carry-selection CLA. The fabricated 0.25-pm CMOS macro achieves a 4.4 ns multiplication time at 2.5 V. # p.599-p.602

## families
### booth_recoded_parallel  (role: instantiates)
mechanism: Booth's algorithm halves the number of partial products. A Wallace tree sums the partial products without carry propagation, and a conditional carry-selection adder combines the two resulting 108-bit operands. # p.599
choices:
new_choices:
  none
slots:
  reduction: compressor_4_2_tree # p.599
  hard_multiple_adder: UNKNOWN
parameters: 54 X 54-b operands; 108-bit final addition; four Wallace-tree addition stages # p.599
results:
| metric | value | unit | technology / device | baseline | condition | page |
| multiplication time | 4.4 | ns | triple-metal 0.25-pm CMOS / 1994 | 5.1 ns estimated full-adder-based circuit | 2.5 V power supply | p.600, p.602 |
| multiplication-time improvement | 14 | % | triple-metal 0.25-pm CMOS / 1994 | estimated full-adder-based circuit | pass-transistor-multiplexer circuits | p.600, p.602 |
| active area | 3.77 X 3.41 | mm | triple-metal 0.25-pm CMOS / 1994 | none | 54 X 54-b multiplier | p.600, p.602 |
| transistor count | 100,200 | transistors | triple-metal 0.25-pm CMOS / 1994 | none | active macro | p.600, p.602 |
errors_and_checks: none
conditions: The multiplier targets the mantissa multiplication of two IEEE double-precision numbers. # p.599
evidence: Architecture, Fig. 1, Fabrication, Evaluation, Table 2, Figs. 8-10, pp.599-602

### compressor_4_2_tree  (role: proposes)
mechanism: Each 4-2 compressor has five inputs and three outputs. The compressor connects CO to the next compressor's Ci, while CO does not depend on Ci, so four partial products are added without propagating carry to the higher bit. The proposed circuit exploits parallelism to reduce the critical path from four gate stages in the two-full-adder construction to three gate stages. # p.599-p.601
choices:
new_choices:
  cell_circuit: pass_transistor_multiplexer — identifies the circuit used for the compressor multiplexers # p.599-p.601
  critical_path_gate_stages: 3 — identifies the proposed compressor's logic depth # p.600-p.601
slots:
  none
parameters: 4-2 compressor; five inputs; three outputs; four Wallace-tree addition stages # p.599-p.601
results:
| metric | value | unit | technology / device | baseline | condition | page |
| propagation-delay reduction | 18 | % | 0.25-pm CMOS / 1994 | full-adder-based 4-2 compressor circuit | simulated proposed three-gate-stage circuit | p.600-p.601 |
errors_and_checks: none
conditions: The speed advantage depends on pass-transistor multiplexers reducing the number of critical-path gate stages. # p.599-p.600
evidence: Architecture, Circuit and Layout Design, Figs. 2-5, pp.599-601

### carry_lookahead  (role: extends)
mechanism: The final adder uses the conditional carry-selection look-ahead scheme with pass-transistor multiplexers. A 4-bit CLA formed from three multiplexers is modified into an 8-bit CLA for the full 108-bit adder. Parallelism gives the 8-bit CLA four critical-path gate stages, while the carry path avoids series-connected pass transistors. # p.600
choices:
  group_size: 8 # p.600
  intergroup_carry: select # p.600
new_choices:
  circuit_style: pass_transistor_multiplexer — identifies the circuit technology used for the CLA # p.600
slots:
  none
parameters: 8-bit CLA groups; 108-bit final adder; four critical-path gate stages; 1.52 ns addition time # p.600
results:
| metric | value | unit | technology / device | baseline | condition | page |
| addition time | 1.52 | ns | 0.25-pm CMOS / 1994 | none | 108-bit final adder | p.600 |
errors_and_checks: none
conditions: The design avoids series-connected pass transistors in the carry-propagation path. # p.600
evidence: Circuit and Layout Design, Fig. 6, p.600

## new_families
none

## space_gaps
* `compressor_4_2_tree` appears as a slot value but lacks declared choices for compressor circuit topology, cell circuit, and critical-path depth; the proposed three-stage pass-transistor compressor distinguishes these properties. # p.599-p.601
* `carry_lookahead` lacks a circuit-style value for pass-transistor multiplexers. # p.600

## open_questions
* The document states that Booth's algorithm halves the partial products but does not state the Booth radix. # p.599
* The document does not specify the sign-extension or negative-partial-product encoding. # p.599
* The document does not describe how the 8-bit CLA groups are connected across the full 108-bit final adder. # p.600
