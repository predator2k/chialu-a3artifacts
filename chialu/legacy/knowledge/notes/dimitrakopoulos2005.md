---
handle: dimitrakopoulos2005
citation: G. Dimitrakopoulos, D. Nikolos, "High-Speed Parallel-Prefix VLSI Ling Adders", IEEE Transactions on Computers, 2005.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int8, int16, int32, int64]
authority: incremental
pages_read: 225-231 / 7
---

## summary
The paper introduces a systematic parallel-prefix formulation for Ling carries that uses separate even/odd prefix trees, one fewer total logic level, and lower fanout than traditional carry-prefix adders. Static-CMOS implementations include full-prefix and hybrid prefix/carry-select adders, with reported delay reductions from 8.8 percent to 14 percent. # p.225, p.227, p.230

## families
### ling_prefix  (role: proposes)
mechanism: Intermediate pairs `(Gi, Pi-1)` combine adjacent-bit generate/propagate terms. Separate prefix trees associate the even-indexed and odd-indexed pairs to compute `Hi` in `log2 n - 1` prefix levels. The preprocessing stage adds one logic level, while halving the number of associated terms removes two prefix logic levels. Sum cell `(4)` uses `Hi-1` to select `di` or `(di XOR pi-1)`, and an extra noncritical AND gate derives `cn-1 = pn-1 · Hn-1`. # p.226-p.228
choices:
  pseudo_carry_group: 2   # p.226-p.227
  topology: ladner_fischer [outside domain]; kogge_stone   # p.227, p.230
  sum_recovery: late_select_mux   # p.226
new_choices:
  preprocessing_pair_generation: {from_generate_propagate, direct_from_inputs} — `(Gi, Pi-1)` can be derived from `(gi, pi)` or directly with AND-OR/OR-AND gates; direct generation reduces series transistors on the critical path.   # p.227
  parity_tree_configuration: {same_topology, independently_selected} — even/odd prefix trees have no interference and may use different prefix architectures.   # p.227
  carry_input_integration: {carry_increment_stage, preprocessing_extra_bit} — `cin` is incorporated through a fast increment stage or as an extra preprocessing bit.   # p.228
slots: none
parameters: 8-bit formulation examples; 16-bit minimum-depth architectures; `log2 n - 1` prefix levels; non-power-of-two widths supported through idempotency; static CMOS.   # p.227-p.228
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay reduction | 10 to 14 | percent | 0.18 μm UMC-18; 2005 | traditional parallel-prefix carry equations | static CMOS implementations | p.225 |
| maximum delay reduction | up to 14 | percent | 0.18 μm UMC-18; 2005 | fastest tested traditional parallel-prefix architectures | minimum-delay implementations | p.225 |
| average delay reduction | 13.1 | percent | 0.18 μm UMC-18; 2005 | traditional Ladner-Fischer and Kogge-Stone adders | full-prefix adders across examined widths | p.230 |
| average delay reduction | 13.8 | percent | 0.18 μm UMC-18; 2005 | Ling adders proposed in [19] | Ladner-Fischer and Kogge-Stone structures | p.230 |
errors_and_checks: Exact binary addition is defined by equations `(3)`, `(4)`, `(12)`, and `(13)`; no fault-detection or approximation contract is reported.   # p.226-p.227
conditions: Designs are mapped under typical 1.8V/25°C conditions, recursively optimized for minimum delay, placed and routed with constant load/floorplan/pin constraints, and timed after extracted RC parasitics are back-annotated. The proposed design gains delay from one fewer total logic level and approximately half the fanout requirements.   # p.227, p.230
evidence: Sections 2.2-4; equations `(3)`-`(14)`; Figs. 3-6; Tables 1 and 3.   # p.226-p.231

### sparse_prefix_hybrid  (role: extends)
mechanism: A prefix tree computes Ling pseudo-carries at 4-bit block boundaries while modified carry-select adders concurrently compute prospective sums. Separate even/odd boundary carries select the results. Each prospective sum uses multiplexers controlled by terms formed from `(Gi, Pi-1)`, followed by a final multiplexer controlled by the incoming Ling carry. Early boundary carries are buffered to balance paths, and the critical path remains in carry computation plus one multiplexer. # p.228-p.230
choices:
  log2_sparsity: 2   # p.228-p.229
  tree_topology: kogge_stone; ladner_fischer [outside domain]   # p.228, p.230
  valency: 2   # p.229-p.230
  sum_block_style: modified_carry_select_ling [outside domain]   # p.229-p.230
new_choices:
  boundary_signal: paired_even_odd_ling_carries — each block uses the corresponding `H4k`/`H4k-1` signals rather than a single traditional carry.   # p.229
slots:
  sum_block: carry_select [outside slot domain]   # p.229-p.230
parameters: 32-bit architectural example; 4-bit modified carry-select blocks; 64-bit experimental comparison.   # p.228-p.230
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay reduction | 8.8 | percent | 0.18 μm UMC-18; 2005 | corresponding traditional hybrid adders | 64-bit adders with 4-bit carry-select blocks and Kogge-Stone/Ladner-Fischer boundary trees | p.230 |
errors_and_checks: Exact prospective sums are selected from the incoming Ling carry; no fault-detection or approximation contract is reported.   # p.229-p.230
conditions: The hybrid requires modified carry-select blocks because pseudo-carries replace real carries, even/odd positions are generated separately, and blocks receive `(Gi, Pi-1)` pairs. The method from [19] cannot implement this hybrid.   # p.229-p.230
evidence: Section 3.1; Figs. 7-9; Table 2.   # p.228-p.230

## new_families
none

## space_gaps
* `ling_prefix.topology` lacks `ladner_fischer`, which is implemented and measured as a proposed Ling-adder topology.   # p.227, p.230
* `ling_prefix` lacks a choice for independently selecting the even-tree and odd-tree topologies.   # p.227
* `sparse_prefix_hybrid.sum_block_style` lacks a modified carry-select block driven by paired even/odd Ling pseudo-carries.   # p.229-p.230
* `sparse_prefix_hybrid.sum_block` does not admit `carry_select`, although the measured hybrid uses modified carry-select blocks.   # p.229-p.230

## open_questions
* The supplied document text does not expose the numeric area/delay cells in Tables 1-3, so the absolute values and per-width results must not be reconstructed from the surrounding prose.
