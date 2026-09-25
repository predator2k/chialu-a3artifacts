---
handle: hauck2000
citation: S. Hauck, M. M. Hosler, T. W. Fry, "High-Performance Carry Chains for FPGAs", IEEE Transactions on VLSI Systems, vol. 8, no. 2, pp. 138-147, 2000.
actual_citation: S. Hauck, M. M. Hosler, T. W. Fry, "High-Performance Carry Chains for FPGAs", FPGA '98, Monterey, CA, USA, 1998.
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int32]
authority: incremental
pages_read: 223-233 / 11
---

## summary
The document adapts ripple, Carry Select, Variable Block, Carry Lookahead, and Brent-Kung carry structures to FPGA cells that support kill/propagate/inverse-propagate/generate states. A laid-out 32-bit Brent-Kung implementation has 6.1 ns carry delay versus 23.4 ns for the basic FPGA ripple chain, with estimated total-chip area increases of 8.5% for Chimaera and 1.18% for a general-purpose FPGA.

## families
### fpga_carry_chain  (role: extends)
mechanism: A dedicated unidirectional carry resource spans each FPGA row and connects one carry position to each logic cell. LUT outputs encode Cout for Cin=1 and Cin=0, which supports kill, propagate, inverse propagate, and generate. Identical LUT outputs break the resource into independent chains at arbitrary positions. The fast-carry element can contain optimized ripple, Carry Select, Variable Block, or Brent-Kung logic while a bypass mux preserves ordinary 3-LUT operation. # pp.224-226, 232
choices:
  chain_segment_length: 32   # p.229
new_choices:
  cell_state_set: kill_propagate_inverse_propagate_generate — states supported by each configurable carry cell   # p.224
  placement: one_unidirectional_chain_per_row — physical organization of the dedicated resource   # p.232
slots:
  none
parameters: carry computations up to 32 bits in the evaluation; arbitrary contiguous subsequences; one chain per FPGA row   # pp.229, 232
results:
| metric | value | unit | technology / device | baseline | condition | page |
| 32-bit carry speedup | 3.8 | times faster | 0.6 micron process (1998) | basic ripple carry | Brent-Kung implementation | p.231 |
| total-chip area increase | 8.5 | % | Chimaera FPGA estimate (1998) | basic ripple carry | Brent-Kung replacement | p.231 |
| total-chip area increase | 1.18 | % | general-purpose FPGA estimate (1998) | basic ripple carry | Brent-Kung replacement; Table 2 | p.231 |
errors_and_checks: none
conditions: The architecture must support carry computations that start/end at arbitrary positions and must retain inverse propagation for parity and other non-adder functions. Short carries can favor ripple logic, while the extra fast-carry logic slightly increases non-carry LUT delay. # pp.224, 226, 230-232
evidence: Table 1; Figures 2, 8, and 11; Tables 2 and 3; “Using the Carry Chain.”

### ripple_carry  (role: extends)
mechanism: The basic cell places two muxes on each carry stage. The optimized cell moves the decision to enter the carry chain away from the repeated path, so intermediate stages contain one fewer mux while preserving an optional initial carry input. The preferred variant has delay 2*n+1 with an initial carry and 2*n when the first cell bypasses mux 1. # p.225
choices:
new_choices:
  fpga_cell_variant: basic_or_optimized_mux_cell — selects the original or shortened configurable carry path   # p.225
slots:
  none
parameters: n-bit carry chain; evaluated at 32 bits   # pp.225, 231
results:
| metric | value | unit | technology / device | baseline | condition | page |
| modeled delay | 3n-2 | gate delays | unit-gate model (1998) | none | basic n-cell ripple chain | p.225 |
| modeled delay | 2n+1 | gate delays | unit-gate model (1998) | basic ripple | preferred optimized chain with initial carry | p.225 |
| modeled delay | 2n | gate delays | unit-gate model (1998) | basic ripple | preferred optimized chain without initial carry | p.225 |
| 32-bit delay | 23.4 | ns | 0.6 micron process (1998) | none | basic ripple carry | p.232 |
| 32-bit delay | 18.7 | ns | 0.6 micron process (1998) | basic ripple carry | optimized ripple | p.232 |
| 3-LUT delay | 1.6 | ns | 0.6 micron process (1998) | none | basic ripple; non-carry f(X,Y,Z) | p.232 |
| 3-LUT delay | 2.5 | ns | 0.6 micron process (1998) | basic ripple carry | optimized ripple; non-carry f(X,Y,Z) | p.232 |
| layout area | 171368 | square lambda | 0.6 micron process (1998) | none | basic ripple carry | p.231 |
| layout area | 394953 | square lambda | 0.6 micron process (1998) | basic ripple carry | optimized ripple | p.231 |
errors_and_checks: none
conditions: The optimized Figure 2a circuit cannot accept Z as an initial carry without an extra cell. The preferred Figure 2b circuit preserves that function at one additional modeled gate delay. # p.225
evidence: Figure 2; Table 2; Table 3; “Optimized Ripple Carry Cell.”

### carry_select  (role: extends)
mechanism: The FPGA chain is divided into ripple blocks that precompute Cout for Cin=1 and Cin=0. Output muxes select the appropriate result after the preceding block supplies the actual carry. Block lengths increase toward higher positions so speculative ripple computations finish when their select carries arrive. # pp.226-227
choices:
  duplication: full_duplicate   # p.226
  select_source: rippled_block_carries   # pp.226-227
new_choices:
  inverse_propagate_support: true — both configurable carry polarities remain supported   # p.226
slots:
  block_adder: ripple_carry   # pp.226-227
parameters: initial 2-cell ripple block; subsequent illustrated blocks cover cells 2-3, 4-6, 7-10, and 11-15   # pp.226-227
results:
| metric | value | unit | technology / device | baseline | condition | page |
| reported numeric result | UNKNOWN | UNKNOWN | unit-gate model (1998) | basic ripple carry | Figure 8 plots Carry Select without tabulated values | p.230 |
errors_and_checks: none
conditions: Carry Select removes dependence on the preceding carry during block computation but duplicates the block carry logic and adds result-selection muxes. # p.226
evidence: Figure 3; “Carry Select”; Figure 8.

### carry_skip  (role: extends)
mechanism: The paper’s Variable Block structure groups ripple cells and bypasses a block when every cell is in propagate or inverse-propagate mode. An XOR reduction determines whether the bypassed Cin must be inverted. Block widths grow and then shrink to balance bypass/ripple paths. # pp.227-228
choices:
  block_sizing: trapezoidal_variable   # p.228
  skip_gate: mux   # p.227
new_choices:
  inverse_propagate_parity: xor_reduction — determines whether a bypassed carry is inverted   # pp.227-228
slots:
  block_adder: ripple_carry   # p.227
parameters: 32-bit block schedule 2,2,4,5,7,5,4,2,1; first/last blocks are simple ripple blocks   # p.228
results:
| metric | value | unit | technology / device | baseline | condition | page |
| reported numeric result | UNKNOWN | UNKNOWN | unit-gate model (1998) | basic ripple carry | Figure 8 plots Variable Block without tabulated values | p.230 |
errors_and_checks: none
conditions: The bypass applies only when every cell is in propagate/inverse-propagate mode; otherwise the ordinary ripple output is selected. # p.227
evidence: Figure 4; “Variable Block”; Figure 8.

### parallel_prefix  (role: extends)
mechanism: Two-input concatenation boxes recursively combine each interval’s Cout functions for Cin=1 and Cin=0. A full Brent-Kung hierarchy halves the unresolved carry-chain length at each level, after which muxes produce individual carries. Truncated Carry Lookahead variants apply fewer concatenation levels and ripple between the resulting groups. # pp.228-230
choices:
  topology: brent_kung   # pp.228-229
  valency: 2   # pp.228-229
new_choices:
  concatenation_levels: full_or_truncated — selects a complete Brent-Kung hierarchy or an N-level lookahead followed by ripple   # p.229
  carry_state_encoding: cout_if_cin_1_and_cout_if_cin_0 — preserves inverse propagation in configurable cells   # p.228
slots:
  none
parameters: 16-bit structures illustrated; 32-bit implementation evaluated; full 32-bit hierarchy described as four concatenation levels   # pp.228-231
results:
| metric | value | unit | technology / device | baseline | condition | page |
| 32-bit delay | 6.1 | ns | 0.6 micron process (1998) | 23.4 ns basic ripple | Brent-Kung | p.232 |
| 3-LUT delay | 2.1 | ns | 0.6 micron process (1998) | 1.6 ns basic ripple | Brent-Kung bypassed for non-carry f(X,Y,Z) | p.232 |
| layout area | 1622070 | square lambda | 0.6 micron process (1998) | 171368 square lambda basic ripple | Brent-Kung | p.231 |
errors_and_checks: none
conditions: Brent-Kung is best in the unit-delay comparison for carry lengths of four bits or more, while basic ripple is best at two bits. Truncated lookahead variants give modest short-distance improvements but perform worse on long carries. # p.230
evidence: Figures 5-10; Tables 2 and 3; “Carry Lookahead and Brent-Kung”; “Carry Chain Performance”; “Layout Results.”

## new_families
none

## space_gaps
* `fpga_carry_chain` lacks choices for four-state kill/propagate/inverse-propagate/generate encoding and arbitrary in-row chain breaks. # pp.224, 232
* `parallel_prefix.node_style` lacks the mux-based dual-Cout concatenation boxes used to preserve inverse propagation. # pp.228-229
* `ripple_carry.full_adder_cell` cannot name the configurable 2-LUT/3-LUT/mux FPGA cell used here. # pp.223-225
* `carry_skip` lacks a choice for inverse-propagate parity on the bypass path. # pp.227-228

## open_questions
* The document does not report exact Figure 8/Figure 9 delays for Carry Select, Variable Block, or truncated Carry Lookahead variants.
* The document identifies a 0.6 micron process but does not name the foundry or process variant.
