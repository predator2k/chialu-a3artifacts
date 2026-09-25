---
handle: oklobdzija1996
citation: V. G. Oklobdzija, D. Villeger, S. S. Liu, "A Method for Speed Optimized Partial Product Reduction and Generation of Fast Parallel Multipliers Using an Algorithmic Approach", IEEE Transactions on Computers, vol. 45, no. 3, pp. 294-306, 1996
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary integer, signedness unspecified]
authority: landmark
pages_read: 294-306 / 13
---

## summary
The document proposes Three Dimensional Minimization (TDM), which globally orders partial-product signals by arrival time and connects slow signals to fast Full Adder paths. TDM generates minimum-cell, speed-optimized parallel-multiplier reduction trees and pairs them with a region-hybrid final CPA tuned to its nonuniform input-arrival profile.

## families
none

## new_families
### three_dimensional_minimization_reduction  (domain: mul: integer multipliers, closest: carry_save_array, why_not: `carry_save_array` is a regular two-dimensional array, while TDM generates a globally timed tree with horizontal propagation between vertical slices.)
mechanism: TDM partitions the partial-product matrix into Vertical Compressor Slices (VCS). Each VCS sorts signals by arrival delay, connects the slowest selected signal to the Full Adder's fast `Cin` input, returns Sum to the current slice, and sends Carry to the next-weight slice. An even input count causes a Half Adder to be placed near partial-product generation. The process stops with three signals feeding a final Full Adder and CPA. The method minimizes vertical and inter-slice horizontal critical paths rather than the number of reduction levels. # pp.297-300
choices:
  compressor_cell: {full_adder_half_adder, general_p_q_compressor} — the primitive and every input/output path delay are technology parameters. # pp.299-301
  signal_scheduling: ascending_arrival_delay_with_slowest_on_fast_input — signals within a bit position are interchangeable and scheduled by delay. # p.299
  half_adder_placement: near_partial_product_generator_when_vcs_input_count_even — this placement gains one XOR delay in the stated timing model. # p.300
  optimization_scope: vertical_and_horizontal_paths — both within-slice and cross-slice paths are minimized. # pp.298-301
  wire_delay_model: average_folded_into_gate_delay_or_iterative_recalculation — detailed wiring is not included in the reported implementation. # p.302
parameters: Any `N × N` size; `2N - 1` delay-annotated lists; examples include `12 × 12` and `24 × 24`; LSI 100K `1μ CMOS ASIC` timing uses FA A/B-to-Sum `2 XOR delays`, Cin-to-Sum and all Carry paths `1 XOR delay`, and HA Carry paths `0.5 XOR delay`. # pp.299-301
results:
| metric | value | unit | technology / device | baseline | condition | page |
| critical-path delay | 10.5 | nS | `1μ CMOS ASIC` (1996) | 4:2 `14.0 nS`; 9:2 `13.0 nS`; Fadavi-Ardekani `11.7 nS` | 24-bit multiplier | p.303 |
| delay improvement | 33 | % | `1μ CMOS ASIC` (1996) | 4:2 design | 24-bit multiplier | p.303 |
| delay improvement | 25 | % | `1μ CMOS ASIC` (1996) | 9:2 design | 24-bit multiplier | p.303 |
| delay improvement | 11 | % | `1μ CMOS ASIC` (1996) | Fadavi-Ardekani design | 24-bit multiplier | p.303 |
| cell-count improvement | 15 | % | `1μ CMOS ASIC` (1996) | Fadavi-Ardekani design | 24-bit multiplier | p.303 |
| reduction-tree improvement | up to 30 | % | UNKNOWN (1996) | Wallace tree XOR-level delay | multiplier width varied | p.302 |
| reduction cells | 110 | cells | UNKNOWN (1996) | Dadda optimization: `110 cells` | 12-bit multiplication | p.302 |
| reduction cells | 506 | cells | UNKNOWN (1996) | Dadda optimization: `506 cells`; Fadavi-Ardekani: `582 cells` | 24-bit multiplication | p.302 |
errors_and_checks: none
conditions: The method requires input/output path delays for the chosen compressor and implementation technology. # pp.294,300-301 The general `(p,q)` extension is useful only when that compressor is faster than a Full-Adder construction in the target technology. # pp.299-301 The reported implementation folds average wire delay/loading into cell delays, while detailed layout-aware optimization may require iterative reruns. # p.302 The authors report no better structure for `N < 64` and cite a separate proof of optimality. # p.301
evidence: §§3.1-3.6; Figs. 3-9; Table 1; pp.297-303.

### arrival_profile_tuned_hybrid_cpa  (domain: adder: carry-propagate adders, closest: prefix_synthesis_nonuniform_arrival, why_not: the document partitions the CPA among VBA/CLA/CSLA structures rather than synthesizing a nonuniform prefix graph.)
mechanism: The final CPA follows the multiplier tree's nonuniform arrival profile. Region 1 follows the positive arrival-time slope with ripple carry or a Variable Block Adder (VBA). Region 2 places fast CLA or optimized CLA derivatives inside carry-select blocks. Region 3 uses available early MSB time with VBA and carry selection. Integer boundaries `S1` and `S2` are found iteratively from intersections between arrival profiles and candidate-adder delays so that selection occurs at the required time. # pp.303-304
choices:
  region_partition: {positive_slope, maximum_delay, negative_slope} — three regions are defined from the arrival profile. # pp.303-304
  positive_slope_adder: {ripple_carry, variable_block_adder} — the smallest structure matching the slope is selected. # pp.303-304
  central_adder: carry_select_with_carry_lookahead_blocks — Region 2 requires the fastest addition. # p.304
  negative_slope_adder: carry_select_with_variable_block_adder — early MSB arrival provides time before selection. # p.304
  boundary_selection: iterative_arrival_profile_intersection — integer positions `S1` and `S2` determine regional widths. # p.304
parameters: Three CPA regions; boundaries `S1`/`S2`; total delay `ΔMULT = ΔTREE + ΔADD* + ΔMUX`; a `13 × 13-bit ASIC multiplier` supplies the illustrated profiles. # pp.303-304
results: none
evidence: §4.1; Figs. 10-12; pp.303-304.

## space_gaps
* The multiplier vocabulary lacks an exact partial-product reduction family with per-input/per-output delay modeling and cross-column signal scheduling. # pp.297-302
* The adder vocabulary lacks a region-hybrid CPA whose component types and boundaries are selected from a multiplier's nonuniform arrival profile. # pp.303-304
* `carry_select.block_sizing` lacks the `arrival_profile_intersection` value used to determine `S1` and `S2`. # p.304

## open_questions
* The supplied rendering makes the individual values in Table 1 unreadable, so only Fig. 9 and prose comparison values are recorded.
* The document does not specify signed/unsigned partial-product encoding.
* The document does not report numerical `S1`/`S2` boundaries or an isolated delay/area result for the hybrid CPA.
