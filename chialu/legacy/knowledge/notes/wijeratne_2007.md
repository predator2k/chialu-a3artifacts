---
handle: wijeratne_2007
citation: S. B. Wijeratne, et al., "A 9-GHz 65-nm Intel Pentium 4 Processor Integer Execution Unit", IEEE Journal of Solid-State Circuits, vol. 42, no. 1, pp. 26-37, 2007.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int8, int16, int32, int64]
authority: landmark
pages_read: 26-37 / 12
---

## summary
The document presents a measured 65-nm Pentium 4 integer execution unit that operates above 9 GHz using a two-frequency domino clocking scheme and redesigned ALU/AGU arithmetic blocks (pp.26-36). The arithmetic designs include a sparse radix-2 carry tree, 4-bit conditional-sum blocks, carry-killed subword modes, and a carry-save AGU with sparse completion (pp.31-33).

## families
### sparse_prefix_hybrid  (role: proposes)
mechanism: Each 32-bit ALU adder generates every fourth carry with a sparse radix-2 carry-merge tree. An initial propagate/generate stage and five carry-merge stages form the critical tree, while 4-bit conditional-sum generators compute both carry-in cases on a noncritical side path. Each generated carry selects the corresponding conditional sum. The 64-bit ALU comprises two discrete 32-bit datapaths with one-FCLK communication latency between them (pp.31-32).
choices:
  log2_sparsity: 2   # p.31
  valency: 2   # p.31
  sum_block_style: conditional_sum   # p.31
new_choices:
  node_style: dual_rail_domino_static — the critical sparse tree uses dual-rail domino while noncritical circuitry uses energy-efficient ripple carry-merge logic   # pp.31-32
slots:
  sum_block: ripple_carry [carry_polarity_alternation=UNKNOWN]   # p.31
parameters: 32-bit blocks; two blocks per 64-bit ALU; every fourth carry; one PG stage; five carry-merge stages; two FCLK cycles per ADD/SUB; FCLK throughput   # pp.31-32
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay reduction | 20% | % | 65-nm CMOS / 2007 | reference Kogge–Stone implementation | equal energy | p.31 |
| normalized dynamic-power reduction | 51% | % | 65-nm CMOS / 2007 | previous LVS adder | same process/voltage comparison with efficient clock gating | p.32 |
| area increase | 5% | % | 65-nm CMOS / 2007 | 90-nm LVS-adder footprint scaled to 65 nm | sparse-tree adder | p.32 |
| wiring-complexity reduction | 80% | % | 65-nm CMOS / 2007 | traditional Kogge–Stone approach | sparse carry tree | p.31 |
errors_and_checks: none
conditions: The sparse tree moves 60% of carry-merge paths to a noncritical side path and reduces P/G fanout by 33%/50% per stage (p.31). Domino/static gates scale better at lower voltages than the previous pass-transistor Manchester carry chains (p.32).
evidence: §VIII; Figs. 13-14; pp.31-32.

### conditional_sum  (role: instantiates)
mechanism: Each noncritical 4-bit block computes sums for assumed carry inputs of 0 and 1. A generated one-in-four carry selects the correct result through a 2:1 multiplexer (p.31).
choices:
  base_block_width: 4   # p.31
  selection_radix: 2   # p.31
new_choices:
  none
slots:
  none
parameters: 4-bit blocks; two assumed carry inputs; 2:1 result selection   # p.31
results:
| metric | value | unit | technology / device | baseline | condition | page |
| transistor-size reduction | 60% | % | 65-nm CMOS / 2007 | critical sparse-tree section | noncritical conditional-sum generator | p.31 |
errors_and_checks: none
conditions: The conditional computation is off the performance-setting carry path, which permits ripple carry-merge logic and smaller transistors (p.31).
evidence: §VIII; Fig. 14; p.31.

### partitioned_carry_chain  (role: instantiates)
mechanism: Carry-kill circuits are incorporated into the sparse carry-merge tree to partition the ALU for 8-bit and 16-bit operation without changing the full-width critical path (p.31).
choices:
  boundary_mechanism: carry_kill_gate   # p.31
  per_lane_flags: UNKNOWN   # p.31
new_choices:
  none
slots:
  base_adder: sparse_prefix_hybrid [log2_sparsity=2, valency=2]   # p.31
parameters: 8-bit and 16-bit subword modes within 32-bit ALU blocks   # p.31
results:
| metric | value | unit | technology / device | baseline | condition | page |
| performance impact | 0 | reported impact | 65-nm CMOS / 2007 | full-width sparse-tree operation | carry-kill circuits incorporated into tree | p.31 |
errors_and_checks: none
conditions: The paper reports no performance impact from adding the carry-kill circuits (p.31).
evidence: §VIII; p.31.

### carry_save_datapath  (role: instantiates)
mechanism: The AGU merges base/index/displacement/segment-base operands into a carry-save result with a 4:2 compressor. A sparse-tree completion adder then forms the linear address. The lower and upper portions are partitioned to support addressing modes, and additional ripple chains derive group P/G signals for a merged segment-base subtraction (pp.32-33).
choices:
  compressor: 4_2   # p.32
  assimilation_point: end_of_chain   # p.32
  accumulator_redundant: false   # p.32
new_choices:
  merged_secondary_subtract: true — ripple chains inside conditional-sum blocks begin segment-base subtraction before linear-address completion   # p.33
slots:
  assimilator: sparse_prefix_hybrid [log2_sparsity=2, valency=2]   # pp.32-33
parameters: four source operands; lower 16-bit sparse tree with PG plus four carry-merge stages; 4-bit conditional-sum blocks; lower 16-bit domino datapath; upper 48-bit static CMOS datapath   # pp.32-33
results:
| metric | value | unit | technology / device | baseline | condition | page |
| normalized dynamic-power reduction | 59% | % | 65-nm CMOS / 2007 | 65-nm-scaled LVS lower 32-bit AGU | sparse tree/merged subtract/static upper section/clock gating | p.33 |
| area reduction | 10% | % | 65-nm CMOS / 2007 | 65-nm-scaled LVS lower 32-bit AGU | same AGU redesign | p.33 |
errors_and_checks: none
conditions: The merged subtraction avoids a redundant parallel three-input adder and produces the extra carry-out three gate delays after the lower linear address (pp.32-33).
evidence: §IX; Figs. 15-17; pp.32-33.

### barrel_mux_tree  (role: extends)
mechanism: The shifter/rotator uses three muxing stages. The first stage speculatively rotates only within byte boundaries, the second stage corrects misplaced bits by modifying its select, and the third stage also selects between the rotator and adder outputs. Limiting the first-stage span reduces critical data/select wire length and loading (pp.33-34).
choices:
new_choices:
  speculative_byte_rotate: true — first-stage rotation is restricted to an 8-bit boundary and corrected in the second mux   # p.34
  output_mux_merged_stage: true — the third stage also performs ALU output selection   # p.33
slots:
  none
parameters: 8-bit/16-bit/32-bit shift and rotate; two cascaded 32-bit circuits for 64-bit left shift; three mux stages; first-stage span at most 8 bit positions   # pp.33-34
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area increase | 30% | % | 65-nm CMOS / 2007 | scaled LVS shifter/rotator | speculative three-stage design | p.34 |
| longest-line fanout | 4 | loads | 65-nm CMOS / 2007 | 38 loads in conventional design | first-to-second-stage interconnect | p.34 |
errors_and_checks: none
conditions: The architecture trades an extra gate stage and 30% area for shorter wires/lower fanout and avoids redundant latches/muxes (p.34).
evidence: §X; Figs. 18-19; pp.33-34.

## new_families
### two_frequency_domino_execution_core  (domain: commercial_units, closest: sparse_prefix_hybrid, why_not: the clocking/circuit mechanism spans the ALU, AGU, register file, bypass network, and rotator rather than defining one arithmetic topology)
mechanism: A locally generated, dual-edge-triggered FCLK produces two pulsed clock cycles per processor clock. Each domino phase contains four gates and at most two domino stages; an SDL converts the second domino output to a full-cycle signal at selected high-RC nodes. A self-timed reset loop controls pulsewidth, and a 4-bit post-fabrication stretch control selects among 16 delay settings. The 64-bit datapath is divided into two 32-bit datapaths with half-processor-clock communication latency (pp.27-30).
choices: frequency_ratio: {2}; domino_stages_per_phase: Int[1..2:1]; gates_per_phase: {4}; pulse_delay_settings: {16}; high_rc_termination: {set_dominant_latch}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| integer-unit frequency | exceeds 9 | GHz | 65-nm Intel CMOS / 2007 | none | 1.30 V/70 C ambient | p.36 |
| integer-unit power | 10.36 | W | 65-nm Intel CMOS / 2007 | none | 9 GHz/1.3 V/70 C | p.36 |
| normalized power reduction | 3.88 | W | 65-nm Intel CMOS / 2007 | scaled 90-nm integer-unit design | same process/frequency/voltage | p.35 |
| normalized leakage-power reduction | 42% | % | 65-nm Intel CMOS / 2007 | scaled 90-nm integer-unit design | whole integer unit | p.35 |
| normalized dynamic-power reduction | 8.4% | % | 65-nm Intel CMOS / 2007 | scaled 90-nm integer-unit design | whole integer unit | p.35 |
| maximum-temperature reduction | 8 | C | 65-nm Intel CMOS / 2007 | scaled 90-nm block designs | simulated CPU thermal-density comparison | pp.35-36 |
evidence: §§III-V, XII-XIV; Figs. 3, 6, 8-10, 22-23; pp.27-36.

## space_gaps
* sparse_prefix_hybrid lacks a circuit/node-style choice for the documented dual-rail domino/static implementation (pp.31-32).
* barrel_mux_tree lacks choices for speculative stage operation/correction and merging the ALU output mux into the last shift stage (pp.33-34).
* commercial_units lacks a family for arithmetic cores driven by a locally doubled pulsed clock with bounded domino-chain depth and tunable pulsewidth (pp.28-30).

## open_questions
* The document calls the ALU tree “sparse radix-2” and compares it with Kogge–Stone, but it does not explicitly identify the sparse tree’s vocabulary topology (p.31).
* The document does not state the rotator mux radix/select encoding/stage order in the vocabulary’s terms (pp.33-34).
