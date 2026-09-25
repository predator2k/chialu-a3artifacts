---
handle: silberman_1998
citation: J. Silberman, et al., "A 1.0-GHz Single-Issue 64-Bit PowerPC Integer Processor Using Dynamic Logic", IEEE Journal of Solid-State Circuits, vol. 33, no. 11, pp. 1600-1608, 1998.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int64]
authority: landmark
pages_read: 1600-1608 / 9
---

## summary
The document presents a 64-bit PowerPC integer processor whose fixed-point unit combines Kogge–Stone addition with rotate-mask-and-merge operations in one dynamic circuit and achieves 550-ps delay. The processor operates at 1.0 GHz in 0.25-μm CMOS and executes core integer operations in one cycle. # p.1600, p.1604-p.1606

## families
### parallel_prefix  (role: extends)
mechanism: The fixed-point unit derives its adder from the Kogge–Stone parallel-prefix algorithm. The first stage forms bit propagate/generate signals, and merge stages form carries for every bit. The implemented 64-bit network computes group propagates and bitwise generates in a staggered arrangement, allowing carry calculation and sum production within four dynamic gates. # p.1604-p.1605
choices:
  topology: kogge_stone   # p.1604
new_choices:
  circuit_style: cascaded_reset_dynamic — delayed reset permits footless complex gates, while the clock resets the final stage to stretch its output pulse   # p.1602-p.1605
slots:
  none
parameters: 64-bit; 4-bit merge groups; four dynamic gates through the adder; single-cycle execution   # p.1604-p.1605
results:
| metric | value | unit | technology / device | baseline | condition | page |
| fixed-point-unit delay | 550 | ps | 0.25-μm CMOS / 64-bit fixed-point unit / 1998 | UNKNOWN | Addition/rotation/logical execution unit | p.1604 |
| demonstrated operating frequency | 1 | GHz | 0.25-μm CMOS / 64-bit fixed-point unit / 1998 | UNKNOWN | Measured global clock, carry-out, and inverted sum waveforms | p.1605 |
errors_and_checks: none reported
conditions: Low fan-out and uniform cell size support high speed. The staggered group-propagate/bit-generate calculation reduces NFET stack height and permits carry and sum production in the same dynamic stage. # p.1604-p.1605
evidence: §III.B; Figs. 5-7, p.1604-p.1605

### barrel_mux_tree  (role: extends)
mechanism: The logarithmic rotation network uses the same merge-stage wiring as the parallel-prefix adder. Added select-controlled devices let each dynamic merge cell compute a propagate function or select one of two rotation inputs. The implemented unit performs rotation in 4-bit groups. # p.1604-p.1605
choices:
  stage_radix: 4   # p.1604-p.1605
  select_encoding: one_hot_decoded   # p.1604
new_choices:
  arithmetic_network_sharing: addition_rotation — the shifter reuses the adder merge devices and wires   # p.1604
slots:
  none
parameters: 64-bit; 4-bit groups; selectors s0 and s1 are applied exclusively   # p.1604-p.1605
results:
| metric | value | unit | technology / device | baseline | condition | page |
| fixed-point-unit delay | 550 | ps | 0.25-μm CMOS / merged adder-rotator / 1998 | separate adder and rotator with result mux | Combined arithmetic/rotation/logical unit | p.1604 |
errors_and_checks: none reported
conditions: A full rotator requires additional left-to-right wires and modifications to the input and sum stages. Sharing the network removes an explicit result mux and saves devices/wires. # p.1604
evidence: §III.B; Figs. 5-6, p.1604-p.1605

### masked_merged  (role: instantiates)
mechanism: The fixed-point unit executes rotate-mask-and-merge instructions with rotation and addition sharing one merge network. Mask generation runs in parallel with data rotation, and the selected operation reaches the common macro output without a separate adder-versus-rotator result mux. # p.1604-p.1605
choices:
new_choices:
  none
slots:
  rotator: barrel_mux_tree [stage_radix=4, select_encoding=one_hot_decoded]   # p.1604-p.1605
parameters: 64-bit; single-cycle rotate-mask-and-merge operations   # p.1600, p.1604-p.1605
results:
| metric | value | unit | technology / device | baseline | condition | page |
| fixed-point-unit delay | 550 | ps | 0.25-μm CMOS / merged fixed-point unit / 1998 | UNKNOWN | Arithmetic/rotate-mask-and-merge/logical operations | p.1604 |
errors_and_checks: none reported
conditions: Mask generation occurs in parallel with rotation. Extra cross-direction wires are required to implement the full rotator. # p.1604-p.1605
evidence: §III.B; Figs. 5-6, p.1604-p.1605

### dedicated_magnitude_comparator  (role: instantiates)
mechanism: A separate compare unit determines greater-than, less-than, or equal condition codes. For recording arithmetic instructions, the compare unit determines the relation of the result to zero in parallel with result production by the fixed-point unit. # p.1601
choices:
new_choices:
  parallel_record_condition_generation: enabled — condition codes for recording arithmetic operations are generated beside the arithmetic datapath   # p.1601
slots:
  none
parameters: 64-bit operands; single-cycle execution   # p.1600-p.1601
results:
| metric | value | unit | technology / device | baseline | condition | page |
| execution latency | 1 | cycle | 0.25-μm CMOS / compare unit / 1998 | UNKNOWN | Explicit compare operations | p.1601 |
errors_and_checks: none reported
conditions: Parallel comparison avoids waiting for the arithmetic result, which reduces delay in resolving dependent conditional branches. # p.1601
evidence: §II.A, p.1601

## new_families
### carry_propagation_free_address_decode  (domain: adder: carry-propagate adders, closest: carry_save_datapath, why_not: The nonunique sum representation drives a memory decoder directly rather than being assimilated by a carry-propagate adder.)
mechanism: A single dynamic gate combines the low 12 bits of two operands into a nonunique carry-propagation-free sum. The upper six output bits drive a self-strobing NOR row decoder, while the remaining bits participate in column selection and alignment. Combining the redundant adder with the decoder addresses the memory location corresponding to the exact operand sum without conventional carry propagation. # p.1605-p.1606
choices: sum_representation: {nonunique_redundant}; decoder_integration: {direct}; circuit_style: {single_dynamic_gate}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| load/store processor cycle time | 1.15 | ns | 0.25-μm CMOS / 4-Kbyte data cache path / 1998 | UNKNOWN | 25 C, 1.95 V; programs include load/store instructions and data-cache output loading | p.1600 |
evidence: §III.C; Fig. 8, p.1605-p.1606

## space_gaps
* `parallel_prefix.node_style` lacks the delayed/cascaded-reset dynamic style used for the Kogge–Stone network. # p.1602-p.1605
* The vocabulary lacks a choice or slot expressing physical sharing of a prefix-adder merge network with a logarithmic rotator. # p.1604-p.1605
* The adder vocabulary lacks a carry-propagation-free address generator whose redundant output is consumed directly by a decoder. # p.1605-p.1606
* The comparator vocabulary lacks parallel condition-code generation for recording arithmetic operations. # p.1601

## open_questions
* The document does not specify the exact redundant encoding used by the carry-propagation-free address adder.
* The document does not specify the mask-generator or final merge circuit used for rotate-mask-and-merge.
* The detailed compare-unit circuit is deferred to reference [6], so its comparator structure is UNKNOWN.
