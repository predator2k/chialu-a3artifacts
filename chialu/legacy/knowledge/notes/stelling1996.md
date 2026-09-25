---
handle: stelling1996
citation: P. F. Stelling, V. G. Oklobdzija, "Design Strategies for Optimal Hybrid Final Adders in a Parallel Multiplier", Journal of VLSI Signal Processing, vol. 14, no. 3, pp. 321-331, 1996
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary_integer]
authority: incremental
pages_read: 321-331 / 11
---

## summary
The paper constructs hybrid final adders for the known rise-plateau-fall bit-arrival profile produced by a parallel multiplier's TDM partial-product reduction tree. The optimized 62-bit design for a 32 × 32-bit multiplier combines ripple-carry/one-level carry-skip/carry-select blocks and reaches 20.25 equivalent XOR delays. # p.321-p.329

## families
### ripple_carry  (role: instantiates)
mechanism: A ripple-carry block propagates its carry through consecutive full-adder positions. The optimized hybrid uses a ripple-carry block where early input arrivals hide the ripple delay, including the low-order portion of the 62-bit final adder. # p.323-p.325
choices:
new_choices:
  none
slots:
  none
parameters: smallest block = (3,2)-adder; carry propagation = 1 XOR delay per position; final-adder width = 62 bits for 32 × 32-bit multiplication # p.322-p.325
results:
| metric | value | unit | technology / device | baseline | condition | page |
|---|---:|---|---|---|---|---|
| latest sum delay | 23.75 | equivalent XOR delays | UNKNOWN; 1996 | 25.75 equivalent XOR delays for the uniform-input-optimized one-level carry-skip design | hybrid ripple-carry/one-level carry-skip design on the Latest-Earliest TDM profile | p.325 |
errors_and_checks: exact binary addition; no fault checker or approximation is reported # p.321-p.323
conditions: Ripple-carry suffices for a block when its internal/generate/propagate/assimilate delays do not exceed the next input arrival time. # p.324
evidence: §2, §2.1, Observation 1, Fig. 3

### carry_skip  (role: extends)
mechanism: One-level carry-skip blocks use ripple propagation within each block and a NAND/NOR skip path between blocks. The paper derives internal-carry/carry-generate/carry-propagate/carry-assimilate delay functions and necessary/sufficient conditions for selecting block boundaries under nonuniform arrivals. # p.324-p.325
choices:
  skip_levels: 1 # p.324-p.325
  skip_gate: and_or_bypass # p.324
new_choices:
  arrival_profile_block_sizing: delay_bound_search — block boundaries are selected from known per-bit arrival times and searched against a latest-output delay bound # p.325
slots:
  block_adder: ripple_carry # p.324-p.325
parameters: 62-bit adder; NAND/NOR ≈ 0.5 XOR delays; interblock generated/skip carry combination adds 0.75 XOR delay # p.322, p.324-p.325
results:
| metric | value | unit | technology / device | baseline | condition | page |
|---|---:|---|---|---|---|---|
| latest sum delay | 15.75 | equivalent XOR delays | UNKNOWN; 1996 | none | optimal 62-bit one-level carry-skip adder with uniform input arrivals | p.325 |
| latest sum delay | 25.75 | equivalent XOR delays | UNKNOWN; 1996 | 15.75 equivalent XOR delays on uniform arrivals | the same uniform-input-optimized design applied to the Latest-Earliest TDM profile | p.325 |
| latest sum delay | 23.75 | equivalent XOR delays | UNKNOWN; 1996 | 25.75 equivalent XOR delays | arrival-profile-optimized hybrid ripple-carry/one-level carry-skip design | p.325 |
| delay improvement | almost 8 | % | UNKNOWN; 1996 | uniform-input-optimized one-level carry-skip design applied to the TDM profile | 32 × 32-bit multiplier final adder | p.325 |
errors_and_checks: exact binary addition; no fault checker or approximation is reported # p.321-p.323
conditions: A carry-skip block in the optimal hybrid requires its incoming carry to arrive later than the block's latest data input plus 1 XOR delay. # p.324 The optimization prefers fewer/simpler blocks when equal delay is obtained. # p.322, p.325
evidence: §2.1, Observations 2-4, Figs. 2-3

### carry_select  (role: extends)
mechanism: One carry-select block consumes precomputed alternative sums/carry-outs from immediate subblocks and selects them with the arriving carry. The delay model includes select-line delay, data-line delay, output loading, and nested subblock delays. # p.326-p.329
choices:
  block_sizing: delay_profile_optimized [outside domain] # p.328-p.329
new_choices:
  block_count: one — the evaluated hybrids permit one carry-select block # p.325-p.329
  output_load_model: output_count_dependent — the selected block's delay includes the load from its sum/carry output lines # p.326-p.328
slots:
  none
parameters: mux delay ≈ 1 XOR from select and 0.75 XOR from data; inverting mux delay ≈ 0.5 XOR from select and 0.875 XOR from data; 30-column example d = 1.375 XOR delays; 21-column example d = 1 XOR delay # p.326-p.328
results:
| metric | value | unit | technology / device | baseline | condition | page |
|---|---:|---|---|---|---|---|
| latest sum delay | 12.125 | equivalent XOR delays | UNKNOWN; 1996 | none | optimal 62-bit ripple-carry/one-level carry-skip/one-carry-select hybrid for uniform arrivals | p.328 |
| latest sum delay | 22.625 | equivalent XOR delays | UNKNOWN; 1996 | 12.125 equivalent XOR delays on uniform arrivals | the same uniform-input-optimized design applied to the Latest-Earliest TDM profile | p.328-p.329 |
| latest sum delay | 20.25 | equivalent XOR delays | UNKNOWN; 1996 | 22.625 equivalent XOR delays | arrival-profile-optimized ripple-carry/one-level carry-skip/one-carry-select hybrid | p.329 |
| delay improvement | better than 10 | % | UNKNOWN; 1996 | uniform-input-optimized hybrid applied to the TDM profile | 32 × 32-bit multiplier final adder | p.329 |
errors_and_checks: exact binary addition; no fault checker or approximation is reported # p.321-p.323
conditions: The carry-select block begins immediately after an existing carry-skip block, which limits the placement search. # p.328 The evaluated optimized design permits only one carry-select block. # p.325-p.329
evidence: §2.2, Figs. 4-6

## new_families
### hybrid_nonuniform_arrival_final_adder  (domain: adder, closest: prefix_synthesis_nonuniform_arrival, why_not: The existing family synthesizes a prefix graph, while this paper partitions the bit range among heterogeneous ripple-carry/carry-skip/carry-select blocks without constructing a prefix graph.)
mechanism: Known per-bit arrival times drive the selection, sizing, and placement of heterogeneous carry-propagate blocks. Internal-carry/generate/propagate/assimilate delays provide lower and upper bounds on the latest sum time. A search over the delay bound and legal block boundaries produces the optimal hybrid for the permitted block set and timing model. # p.321-p.329
choices:
  arrival_profile: {rise_plateau_fall, arbitrary_known}
  block_set: {ripple_carry_carry_skip, ripple_carry_carry_skip_carry_select, extended}
  optimization_objective: {latest_sum_delay, delay_with_area_power_complexity_constraints}
  timing_basis: {equivalent_xor_delay, raw_gate_delay}
  carry_select_block_count: Int[0..n]
results:
| metric | value | unit | technology / device | baseline | condition | page |
|---|---:|---|---|---|---|---|
| latest sum delay | 23.75 | equivalent XOR delays | UNKNOWN; 1996 | 25.75 equivalent XOR delays | optimized ripple-carry/one-level carry-skip hybrid for the 32-bit Latest-Earliest TDM profile | p.325 |
| latest sum delay | 20.25 | equivalent XOR delays | UNKNOWN; 1996 | 22.625 equivalent XOR delays | optimized hybrid adding one carry-select block for the same profile | p.329 |
| estimated speed improvement | 10 | % | UNKNOWN; 1996 | commonly used CLA scheme | complete 32 × 32-bit multiplier final adder | p.329 |
evidence: abstract; §1.1; §2; §2.1; §2.2; Figs. 1-6; §3

## space_gaps
* `carry_skip.block_sizing` lacks an arrival-profile-optimized value for block boundaries selected from known per-bit arrival times. # p.325
* `carry_select.block_sizing` lacks an arrival-profile-optimized value. # p.328-p.329
* `carry_select` lacks a choice for the permitted number of carry-select blocks. # p.325-p.329
* `carry_select.slot block_adder` does not cover the heterogeneous/nested subblocks used by the paper's hybrid timing formulation. # p.326-p.329
* The adder vocabulary lacks a family for heterogeneous block synthesis under arbitrary known input-arrival profiles without requiring a prefix graph. # p.321-p.329

## open_questions
* The text does not enumerate every block boundary shown graphically in Figs. 3-5, so the exact optimized partition cannot be recovered reliably from the supplied text.
* The paper does not report a fabrication technology, implementation area, power, or measured silicon timing.
* Carry-lookahead/conditional-sum extensions are described as preliminary and incomplete, so their optimal structures/results remain UNKNOWN. # p.329
