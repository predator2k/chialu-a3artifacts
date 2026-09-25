---
handle: hilewitz_2008
citation: Y. Hilewitz, R. B. Lee, "Fast Bit Gather, Bit Scatter and Bit Permutation Instructions for Commodity Microprocessors", Journal of Signal Processing Systems, 2008
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [64_bit_word]
authority: incremental
pages_read: 145-169 / 25
---

## summary
The paper proposes pex/pdep bit gather/scatter instructions and bfly/ibfly bit-permutation instructions implemented with inverse butterfly and butterfly networks. Static versions use predecoded controls and execute in one cycle, while dynamic versions add a hardware mask decoder. Application-kernel simulation reports 1.13× to 10.04× speedup over a basic Alpha RISC ISA.

## families
### popcount_counter_tree  (role: instantiates)
mechanism: The mask decoder computes the required prefix population counts in parallel. Full adders reduce groups of three lines in a carry-shower-like network, while the overall parallel-prefix organization resembles a radix-3 Han-Carlson adder; counts are truncated modulo the rotation period required by each butterfly stage. # p.163
choices:
  counter_primitive: full_adder_3_2  # p.163
new_choices:
  output_scope: prefix_population_counts — the circuit produces counts for mask prefixes needed by all network stages  # pp.162-163
  stage_dependent_modulus: true — each count retains only the bits needed for its stage’s rotation period  # p.163
slots:
  final_adder: none
parameters: 64-bit mask example; log3(n)+2 counter stages; n/2×lg(n) decoder outputs  # pp.163-164
results: none reported separately; the counter is included in the functional-unit synthesis results below.
errors_and_checks: none
conditions: The widest population count controls the first butterfly stage, so decoder execution cannot overlap pdep data traversal through the butterfly network. # p.164
evidence: §7.1, Algorithm 1, Figs. 30-31; §7.2, Fig. 33

### barrel_mux_tree  (role: extends)
mechanism: Each LROTC block is a barrel rotator modified to complement control bits that wrap around. A 2m-bit LROTC has m+1 stages rather than the m stages of an ordinary rotator, with the final stage selecting its input or complement. # pp.163-164
choices:
new_choices:
  wrap_action: complement_on_wrap — wrapping control bits are complemented to confine the effective rotation within each output subnetwork  # pp.150-151, 163-164
slots:
  none
parameters: 2m-bit LROTC; m+1 stages; single-bit final-stage LROTC blocks are eliminated  # pp.163-164
results: none reported separately; the LROTC blocks are included in the functional-unit synthesis results below.
errors_and_checks: none
conditions: Constant-zero inputs permit logic simplification, and LROTC(“0”, b)=b eliminates the last butterfly stage’s LROTC circuits. # p.164
evidence: Facts 5-6 and Figs. 8-10, pp.150-152; §7.2 and Fig. 32, pp.163-164

## new_families
### butterfly_gather_scatter  (domain: shift, closest: barrel_mux_tree, why_not: barrel_mux_tree applies one uniform displacement, while this mechanism independently routes selected bits through multistage permutation networks)
mechanism: An n-bit pdep routes the rightmost selected data bits through an lg(n)-stage butterfly network and masks unselected outputs. An n-bit pex masks unselected inputs and routes the selected bits through an lg(n)-stage inverse butterfly network. Static operations obtain controls from application registers; loop-invariant and dynamic operations use a decoder composed of prefix population counting and LROTC blocks. A butterfly followed by an inverse butterfly forms a Beneš network capable of any n-bit permutation. # pp.147-156, 162-164
choices:
  network: {butterfly, inverse_butterfly, paired_butterfly_inverse, paired_plus_second_inverse_for_grp}  # pp.153-156
  mask_binding: {static, loop_invariant, dynamic}  # pp.154-157
  control_generation: {software_predecode, hardware_prefix_popcount_lrotc}  # pp.154-156, 162-164
  operation_set: {pex_pdep_bfly_ibfly, pex_pdep_bfly_ibfly_grp}  # pp.153-157
  control_storage: {application_registers}  # pp.153-156
results:
| metric | value | unit | technology / device | baseline | condition | page |
| latency | 1 | cycle | assumed 64-bit processor model / 2008 | add instruction | static bfly/ibfly/pex/pdep with preloaded controls | p.157 |
| latency | 2 | cycles | assumed 64-bit processor model / 2008 | UNKNOWN | setib/setb hardware decode | p.157 |
| latency | 3 | cycles | assumed 64-bit processor model / 2008 | 1-cycle static form | pex.v/pdep.v/grp | p.157 |
| kernel speedup range | 1.13–10.04 | × | SimpleScalar Alpha simulation / 2008 | basic Alpha RISC ISA | application kernels | p.161 |
| mean kernel speedup | 2.29 | × | SimpleScalar Alpha simulation / 2008 | basic Alpha RISC ISA | all evaluated kernels | p.161 |
| mean kernel speedup | 1.94 | × | SimpleScalar Alpha simulation / 2008 | basic Alpha RISC ISA | rng excluded | p.161 |
| cycle time | 0.48 | ns | TSMC 90 nm standard cell library / 2008 | ALU: 0.50 ns | 64-bit static pex/pdep/bfly/ibfly unit, timing optimized | p.165 |
| area | 6.8K | NAND gate equivalent | TSMC 90 nm standard cell library / 2008 | ALU: 7.5K | 64-bit static pex/pdep/bfly/ibfly unit | p.165 |
| cycle time | 0.58 | ns | TSMC 90 nm standard cell library / 2008 | ALU: 0.50 ns | 64-bit three-stage dynamic/loop-invariant unit | p.165 |
| area | 16.9K | NAND gate equivalent | TSMC 90 nm standard cell library / 2008 | ALU: 7.5K | 64-bit three-stage dynamic/loop-invariant unit | p.165 |
| cycle time | 0.62 | ns | TSMC 90 nm standard cell library / 2008 | ALU: 0.50 ns | 64-bit unit additionally supporting grp | p.165 |
| area | 24.2K | NAND gate equivalent | TSMC 90 nm standard cell library / 2008 | ALU: 7.5K | 64-bit unit additionally supporting grp | p.165 |
errors_and_checks: Theorems 1 and 2 prove that every pdep and pex operation routes through its respective network without path conflicts, with unselected bits zeroed externally. # pp.152-153
conditions: A butterfly network cannot implement every pex, and an inverse butterfly network cannot implement every pdep, so support for both operations requires both datapaths. # p.153
conditions: Static pex/pdep dominate the studied applications and use the smallest evaluated unit; dynamic support raises latency to three cycles and area to 2.25× the reference ALU. # pp.157-158, 165-167
conditions: Loop-invariant masks permit one hardware decode into application registers followed by repeated single-cycle static operations. # pp.154-156, 167
conditions: General permutation requires bfly followed by ibfly and additional configuration storage; a 64-bit network requires three 64-bit control registers per network. # pp.147-148, 154-155
evidence: §§2.1-3.4, Figs. 1-19; Table 1; §6 and Fig. 28; §§7.1-7.3, Algorithm 1, Figs. 30-33, Tables 3-4

## space_gaps
* The shift vocabulary lacks a family for butterfly/inverse-butterfly bit permutation and masked gather/scatter networks. # pp.147-156
* popcount_counter_tree lacks a choice for producing all required prefix counts rather than one total population count. # pp.162-164
* barrel_mux_tree lacks complement-on-wrap rotation used to generate permutation-network controls. # pp.150-151, 163-164
* The vocabulary lacks component slots connecting a gather/scatter mask decoder to prefix population counting and LROTC circuits. # pp.162-164

## open_questions
* The synthesis report does not state the standard-cell process corner, voltage, temperature, or switching-activity assumptions. # pp.164-165
* The three-stage dynamic units report instruction latency but do not state initiation interval. # pp.157, 164-165
* Performance evaluation covers application kernels rather than complete applications. # pp.161, 167
