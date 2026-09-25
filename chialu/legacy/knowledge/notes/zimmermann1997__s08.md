---
handle: zimmermann1997#s08
parent: zimmermann1997
citation: zimmermann1997 — Binary Adder Architectures for Cell-Based VLSI and their Synthesis
chapter: VLSI Aspects of Adders
pdf_pages: 92-102
status: ok
kind: thesis_chapter
unit_classes: [BINARY_ALU]
formats: [binary]
authority: thesis
pages_read: 11 / 11
---

## summary
The chapter establishes verification, transistor-level implementation, layout, library-cell, pipelining, and FPGA considerations for binary adders. It gives measured results for a custom 32-bit Sklansky adder and Xilinx XC6216 ripple-carry/carry-increment implementations, while warning that implementation results are comparable only under the same conditions and technology. # p.92, p.94, p.96, p.102

## families
### parallel_prefix  (role: extends)
mechanism: Prefix computation is implemented as staged preprocessing, prefix levels, and post-processing. AOI/OAI and NAND/NOR gates alternate signal polarity in standard-cell implementations; transistor-level implementations can use complementary CMOS or pass-gate multiplexers. Sklansky structures support buffering, folding, and fine-grained pipelining; Brent-Kung supports medium-grained pipelining. # p.95, p.96, p.97, p.98, p.99
choices:
  topology: sklansky; brent_kung   # p.96, p.100
  valency: UNKNOWN   # p.96
  log2_sparsity: UNKNOWN   # p.96
  fanout_cap: UNKNOWN   # p.96
  wire_track_budget: UNKNOWN   # p.97
  node_style: aoi_oai_alternating; multiplexer [outside domain]   # p.96, p.101
new_choices:
  fanout_decoupling: one_buffer_level — high-fanout nodes are removed from the critical path by one buffer level   # p.96
  layout_folding: unfolded | folded — antisymmetric halves are overlaid to fill white-node locations   # p.97
  pipeline_granularity: fine | medium — registers are placed between selected prefix stages   # p.99, p.100
slots:
  none
parameters: 32-bit custom implementation; 16-bit pipelining examples   # p.96, p.99, p.100
results:
| metric | value | unit | technology / device | baseline | condition | page |
| test-vector count | 4n + 4 | vectors | abstract | UNKNOWN | operand word length n; synthesized AOI- or multiplexer-based prefix adders | p.93 |
| fault coverage | 100 | % | abstract | UNKNOWN | gate/node fault models, except some hard-to-detect connection faults | p.93 |
| transistor count | 1 607 | transistors | 0.5 µm process | UNKNOWN | 32-bit buffered Sklansky | p.96 |
| worst-case delay | 4.14 | ns | 0.5 µm process | UNKNOWN | 2.8 V, 110 °C, 100 MHz; 32-bit buffered Sklansky | p.96 |
| average power dissipation | 7.5 | mW | 0.5 µm process | UNKNOWN | worst-case conditions, 100 MHz; 32-bit buffered Sklansky | p.96 |
| unused Sklansky node locations | half | structure area | abstract | unfolded Sklansky | regular layout before folding | p.97 |
| logic depth per stage | two | unit gates | abstract | UNKNOWN | preprocessing, prefix, and post-processing stages | p.99 |
| internal signals | up to three | signals per bit position | abstract | UNKNOWN | prefix-computation stage before register reduction | p.99 |
| register-growth order | logarithmically | pipeline registers | abstract | pipelined serial-prefix/CLA structure grows linearly | increasing word length | p.100 |
| FPGA pitch penalty | 50% more | area | Xilinx XC6216-style fine-grained FPGA | two-cell pitch | three intermediate signals require pitch increase from two to three cells | p.102 |
errors_and_checks: The regular test bench covers 100% of gate/stuck-0/1/open-0/1 faults under the stated models, except some hard-to-detect connection faults. Prefix adders contain no logic redundancy and are described as completely testable. # p.92, p.93
conditions: Sklansky gives the fastest cell-based starting architecture and permits high-fanout buffering, but its regular unfolded layout wastes half of the node locations. Folding improves density but reverses and interleaves high-order bits, which suits macro-cells better than bus-oriented datapaths. Prefix pipelining is regular and fine-grained, but large internal signal counts increase register area. Parallel-prefix structures are inefficient on the examined fine-grained FPGA because routing three intermediate signals per bit increases pitch or requires secondary long wires. # p.96, p.97, p.99, p.102
evidence: Sections 7.1, 7.2.5, 7.3, 7.4, 7.5, and 7.6; Table 7.1; Figures 7.3–7.5 and 7.9–7.11.

### manchester_carry_chain  (role: analyzes)
mechanism: The Manchester chain computes a series of carry signals in ripple-carry fashion from generate, propagate, and kill signals. The transistor-level chain uses three transistors per bit, while kill generation requires additional logic. Series length is limited by the number of transistors connected in series. # p.95
choices:
  chain_segment_length: 4   # p.95
  circuit_style: UNKNOWN   # p.95
  variable_skip: UNKNOWN   # p.95
new_choices:
  none
slots:
  none
parameters: typically 4-bit chain segments   # p.95
results:
| metric | value | unit | technology / device | baseline | condition | page |
| carry-chain cost | three | transistors per bit position | abstract | two gates per bit in the cell-based recurrence | kill-generation logic excluded | p.95 |
errors_and_checks: none
conditions: The Manchester chain is area-efficient for short ripple chains and intermediate non-critical carries. Long series-transistor chains require implementation-level simulation or measurement for reliable comparison. # p.95, p.96
evidence: Sections 7.2.3–7.2.4; Figure 7.1.

### ripple_carry  (role: compares)
mechanism: The FPGA implementation is a series of full-adders placed in regular bit slices. Each full-adder needs three logic cells but occupies a 2 by 2 region for regularity. Custom transistor-level full-adder circuits can improve area/delay over decompositions into simple gates. # p.95, p.98, p.102
choices:
  full_adder_cell: UNKNOWN   # p.95
  carry_polarity_alternation: UNKNOWN   # p.102
new_choices:
  none
slots:
  none
parameters: 4-, 8-, 16-, and 32-bit implementations; 4 logic cells per bit   # p.102
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area, 4-bit | 16 | logic cells | Xilinx XC6216 | CIA-1L: 24 logic cells | static timing verification | p.102 |
| delay, 4-bit | 16.2 | ns | Xilinx XC6216 | CIA-1L: 19.4 ns | static timing verification | p.102 |
| area, 8-bit | 32 | logic cells | Xilinx XC6216 | CIA-1L: 48 logic cells | static timing verification | p.102 |
| delay, 8-bit | 29.1 | ns | Xilinx XC6216 | CIA-1L: 25.7 ns | static timing verification | p.102 |
| area, 16-bit | 64 | logic cells | Xilinx XC6216 | CIA-1L: 96 logic cells | static timing verification | p.102 |
| delay, 16-bit | 54.9 | ns | Xilinx XC6216 | CIA-1L: 34.1 ns | static timing verification | p.102 |
| area, 32-bit | 128 | logic cells | Xilinx XC6216 | CIA-1L: 192 logic cells | static timing verification | p.102 |
| delay, 32-bit | 106.5 | ns | Xilinx XC6216 | CIA-1L: 44.7 ns | static timing verification | p.102 |
errors_and_checks: none
conditions: Ripple carry is the low-speed, low-wiring option for fine-grained FPGAs. Dedicated fast-carry logic makes ripple carry the best coarse-grained-FPGA choice for all but very large word lengths. # p.101, p.102
evidence: Sections 7.2.3, 7.4.2, and 7.6; Table 7.2.

### carry_increment  (role: instantiates)
mechanism: The one-level carry-increment FPGA adder uses three six-cell slice types. Long wires propagate block carries; two slice types differ only in whether the carry-out connects to a long wire. # p.102
choices:
  block_width: UNKNOWN   # p.102
  block_sizing: UNKNOWN   # p.102
  intergroup_carry: UNKNOWN   # p.102
  increment_levels: 1   # p.102
new_choices:
  none
slots:
  none
parameters: 4-, 8-, 16-, and 32-bit implementations; 6 logic cells per bit   # p.102
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area, 4-bit | 24 | logic cells | Xilinx XC6216 | RCA: 16 logic cells | static timing verification | p.102 |
| delay, 4-bit | 19.4 | ns | Xilinx XC6216 | RCA: 16.2 ns | static timing verification | p.102 |
| area, 8-bit | 48 | logic cells | Xilinx XC6216 | RCA: 32 logic cells | static timing verification | p.102 |
| delay, 8-bit | 25.7 | ns | Xilinx XC6216 | RCA: 29.1 ns | static timing verification | p.102 |
| area, 16-bit | 96 | logic cells | Xilinx XC6216 | RCA: 64 logic cells | static timing verification | p.102 |
| delay, 16-bit | 34.1 | ns | Xilinx XC6216 | RCA: 54.9 ns | static timing verification | p.102 |
| area, 32-bit | 192 | logic cells | Xilinx XC6216 | RCA: 128 logic cells | static timing verification | p.102 |
| delay, 32-bit | 44.7 | ns | Xilinx XC6216 | RCA: 106.5 ns | static timing verification | p.102 |
errors_and_checks: none
conditions: One-level carry increment is the high-speed choice among the examined fine-grained-FPGA structures. Two-level carry increment has more complex wiring. Routability is placement-sensitive; only two bit-slice placements were routable without increasing pitch. # p.102
evidence: Sections 7.3 and 7.6; Figures 7.7–7.8 and 7.14; Table 7.2.

### fpga_carry_chain  (role: analyzes)
mechanism: Coarse-grained FPGAs use LUT-based blocks with four or more inputs and typically add dedicated fast-carry logic because complex logic blocks have excessive depth for fast carry propagation. Vendor macros expose this carry logic to ripple-carry adders. # p.101
choices:
  chain_segment_length: UNKNOWN   # p.101
  ternary_packing: UNKNOWN   # p.101
  prefix_over_chain: UNKNOWN   # p.101
new_choices:
  none
slots:
  none
parameters: coarse-grained logic blocks have about four or more inputs   # p.101
results:
| metric | value | unit | technology / device | baseline | condition | page |
| preferred word-length range | all but very large | word lengths | coarse-grained FPGA with dedicated fast carry | adapted non-ripple architectures | vendor fast-carry macro available | p.101 |
errors_and_checks: none
conditions: Dedicated carry logic favors ripple carry on coarse-grained FPGAs. Fine-grained FPGAs without dedicated carry logic require architecture selection based on regularity, wiring, cell placement, and routability. # p.101, p.102
evidence: Sections 7.6.1–7.6.2.

## taxonomy
* Transistor-level implementation   # p.95
  * Dynamic logic -> unmapped   # p.95
  * Static logic   # p.95
    * Complementary CMOS -> parallel_prefix   # p.95, p.96
    * Pass-transistor logic -> parallel_prefix   # p.95
  * Special arithmetic circuits   # p.95
    * Carry chain or Manchester chain -> manchester_carry_chain   # p.95
    * Pass-transistor/pass-gate multiplexer structures -> parallel_prefix   # p.95
    * Full-adder circuits -> ripple_carry   # p.95
* Layout topologies   # p.97, p.98
  * Buffered Sklansky -> parallel_prefix   # p.96
  * Folded Sklansky -> parallel_prefix   # p.97
  * Folded buffered Sklansky -> parallel_prefix   # p.97
  * Serial-prefix -> ripple_carry   # p.98
  * 1-level carry-increment prefix -> carry_increment   # p.98
  * 2-level carry-increment prefix -> carry_increment   # p.98
* Pipelined structures   # p.99, p.100
  * Fine-grained Sklansky -> parallel_prefix   # p.99
  * Fine-grained serial-prefix -> ripple_carry   # p.100
  * Medium-grained Brent-Kung -> parallel_prefix   # p.100
  * Medium-grained serial-prefix with carry-lookahead stages -> unmapped   # p.100
* FPGA architectures   # p.101, p.102
  * Coarse-grained FPGA with fast-carry logic -> fpga_carry_chain   # p.101
  * Fine-grained FPGA   # p.102
    * Low speed: ripple-carry -> ripple_carry   # p.102
    * Medium speed: carry-skip -> carry_skip   # p.102
    * High speed: 1-level carry-increment -> carry_increment   # p.102

## primary_sources
* WE, 1985 — unit-transistor delay model   # p.95
* Rab, 1996 — transistor-level logic styles   # p.95
* ZG, 1996; ZF, 1997 — complementary CMOS comparison with pass-transistor logic   # p.95
* DP, 1996 — small carry-lookahead adders between registers in a pipelined ripple structure   # p.100
* Müller, 1997 — XC6216 ripple-carry and one-level carry-increment results   # p.102
* Xilinx, 1997 — XC6216 FPGA architecture   # p.102

## new_families
none

## space_gaps
* parallel_prefix.node_style lacks the multiplexer implementation explicitly discussed for transistor-level circuits and fine-grained FPGAs. # p.95, p.101
* parallel_prefix lacks choices for fanout-buffer insertion, folded layout, and pipeline-register placement. # p.96, p.97, p.99
* fpga_carry_chain lacks choices for FPGA granularity, dedicated-carry availability, placement pitch, and routing-resource constraints. # p.101, p.102

## open_questions
* The extraction text obscures several mathematical symbols and figure annotations for folded-array dimensions and pipelined-adder cycle time/area/latency/fan-out, so those values must not be reconstructed without the figures. # p.97, p.99, p.100
* The chapter does not give full author names for several citation keys, so the primary-source identities require the bibliography rather than inference. # p.95, p.96, p.100
