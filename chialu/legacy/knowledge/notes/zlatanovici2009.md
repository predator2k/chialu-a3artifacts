---
handle: zlatanovici2009
citation: R. Zlatanovici, S. Kao, B. Nikolic, "Energy-Delay Optimization of 64-Bit Carry-Lookahead Adders With a 240 ps 90 nm CMOS Design Example", IEEE Journal of Solid-State Circuits, 2009.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int64]
authority: landmark
pages_read: 569-583 / 15 pages
---

## summary
The paper analyzes logic equations, circuit styles, carry-tree radix/lateral fanout/sparseness, and gate sizing for 64-bit carry-lookahead adders in the energy-delay space (pp.570-579). The fabricated design is a radix-4 sparse-2 Kogge-Stone tree using Ling equations and domino carry logic, measured at 240 ps and 260 mW in 90 nm CMOS at 1 V (pp.579-582).

## families
### parallel_prefix  (role: analyzes)
mechanism: Minimum-depth carry trees are described by radix and per-stage lateral fanout. Kogge-Stone limits lateral fanout by computing more carries, while Ladner-Fischer reduces gates/wires at the cost of larger critical-path loading. Knowles notation spans the intermediate trees. The optimization compares full, sparse-2, and sparse-4 variants under common loading/wiring constraints (pp.571-577).
choices:
  topology: kogge_stone, ladner_fischer, knowles_mixed   # pp.571-573
  valency: 2, 4, and mixed 4-3-3-2 [outside domain]   # pp.571,575
  log2_sparsity: 0, 1, 2   # pp.572-577
  node_style: and_or, dynamic_domino   # pp.570-575
new_choices:
  lateral_fanout_sequence: per-stage integer sequence — Knowles notation distinguishes trees from 1-1-1-1-1-1 through 32-16-8-4-2-1   # pp.571-577
  logic_family: {static_cmos, domino, compound_domino, compound_domino_stack_height_reduction} — circuit implementation independent of tree topology   # pp.571,574-575
  sizing_strategy: {grouped, flat} — gates are sized per stage/group or individually   # pp.574,577-578
slots:
  none
parameters: 64-bit; radix-2, radix-4, and mixed-radix trees; full/SP2/SP4; 24-metal-track bitslice; 27 fF input capacitance per bitslice; equal input/output loading; 100 ps maximum 10%-90% transition time   # pp.570-571
results:
| metric | value | unit | technology / device | baseline | condition | page |
| minimum achievable delay | 12.5 | FO4 | general-purpose 90 nm CMOS (2009) | none | static R2 1-1-1-1-1-1 adder | p.574 |
| delay reduction | approximately 1 | FO4 | general-purpose 90 nm CMOS (2009) | shielded compound-domino wiring | shielding load ignored and dynamic wires use double-width/double-space routing | p.575 |
| speed gain | approximately 0.2 | FO4 | general-purpose 90 nm CMOS (2009) | original wire loading | Ladner-Fischer wire loading reduced by 25% | p.576 |
| delay improvement | 3.6 | % | general-purpose 90 nm CMOS (2009) | grouped sizing | flat-sized radix-2/radix-4 Kogge-Stone trees | p.578 |
| speed increase | 18 | % | general-purpose 90 nm CMOS (2009) | grouped sizing | flat-sized radix-2 Ladner-Fischer tree | p.578 |
errors_and_checks: none
conditions: Low lateral fanout gives the highest maximum speed, while high lateral fanout gives lower minimum energy (pp.575-576). The lateral-fanout differences become negligible for SP4 trees (pp.575-576). Radix-4 is fastest under the reference 90 nm environment, while larger self-loading/wire capacitance can favor radix-2 and greater sparseness (pp.575,578-579). Static CMOS consumes less power for delay requirements longer than 12.5 FO4, while faster targets require dynamic logic (pp.574,582).
evidence: §III-A3-6, §III-B2-6, §III-C; Figs. 2-11 (pp.571-579)

### ling_prefix  (role: instantiates)
mechanism: Ling equations propagate pseudo-carry H rather than the conventional generate term. The reformulation reduces the first carry-tree gate’s transistor stack, but moves complexity into sum precomputation. The fabricated adder combines the Ling carry result with precomputed conditional sums through a final selection multiplexer (pp.571,579-580).
choices:
  topology: kogge_stone   # pp.579-582
  sum_recovery: late_select_mux   # pp.570-571,579-580
new_choices:
  none
slots:
  none
parameters: 64-bit; radix-4; sparse-2; three carry-tree stages shown in Fig. 14   # pp.579-581
results:
| metric | value | unit | technology / device | baseline | condition | page |
| energy-delay relation | lower delay at high speed | qualitative | general-purpose 90 nm CMOS (2009) | conventional CLA equations | carry tree is critical | p.574 |
| energy relation | lower energy for conventional CLA | qualitative | general-purpose 90 nm CMOS (2009) | Ling equations | long-delay/minimum-sized region where sum precomputation is critical | p.574 |
errors_and_checks: none
conditions: Ling equations benefit high-speed designs because reduced first-stage stack height permits a larger first gate under the same input-capacitance constraint (p.574). Ling effectiveness decreases at higher sparseness because its sum-precompute complexity grows faster (p.577).
evidence: §III-A1, §III-B1, §III-B5, §IV-A; Figs. 4, 13-15 (pp.571,574,577,579-581)

### sparse_prefix_hybrid  (role: instantiates)
mechanism: The sparse-2 tree computes only even-order carries. Each computed carry selects two precomputed sums, while odd/even sum-precompute paths use locally unrolled carry equations. Critical domino carry paths and noncritical static-CMOS precompute paths are interleaved in a bit-sliced layout (pp.573-574,579-581).
choices:
  log2_sparsity: 1   # pp.579-582
  tree_topology: kogge_stone   # pp.579-582
  valency: 4   # pp.579-582
  sum_block_style: conditional_sum   # pp.570,579-580
new_choices:
  carry_logic_family: delayed_precharge_footless_domino_with_footed_first_stage — the carry tree uses delayed-precharge domino, with footless stages where inputs are monotonic   # pp.579-580
slots:
  none
parameters: 64-bit; radix-4; SP2; 1 V nominal supply; eight adder cores; core size 417 × 75 µm²; chip size 1.6 × 1.7 mm²   # pp.579-581
results:
| metric | value | unit | technology / device | baseline | condition | page |
| frequency | 4.2 | GHz | general-purpose 90 nm bulk CMOS (2009) | none | 1 V, slowest input vector | p.580 |
| delay | 240 | ps | general-purpose 90 nm bulk CMOS (2009) | none | 1 V, slowest input vector | p.580 |
| normalized delay | approximately 7.7 | FO4 | general-purpose 90 nm bulk CMOS (2009) | none | 1 V, slowest input vector | p.580 |
| active power | 260 | mW | general-purpose 90 nm bulk CMOS (2009) | none | 1 V, maximum-power input vector; core and clock generation included | p.580 |
| leakage | 2.3 | mW | general-purpose 90 nm bulk CMOS (2009) | none | 1 V, room temperature | p.580 |
| delay | 180 | ps | general-purpose 90 nm bulk CMOS (2009) | 240 ps at 1 V | 1.3 V | p.580 |
| active power | 606 | mW | general-purpose 90 nm bulk CMOS (2009) | 260 mW at 1 V | 1.3 V | p.580 |
| leakage | 4.9 | mW | general-purpose 90 nm bulk CMOS (2009) | 2.3 mW at 1 V | 1.3 V | p.580 |
errors_and_checks: none
conditions: Sparseness reduces carry-tree gates/wires/input loading but increases output branching and sum-precompute complexity (pp.576-577). Sparse trees benefit large/high-fanout carry trees most, while SP4 can make small radix-4 or compound-domino trees slower and less energy-efficient (pp.576-577). The fabricated design uses grouped sizing and standard-threshold devices (p.579).
evidence: §III-A5, §III-B5, §III-C, §IV; Figs. 3, 8-9, 11-16 (pp.572-581)

## new_families
none

## space_gaps
* `parallel_prefix` lacks the paper’s per-stage `lateral_fanout_sequence`, which is explicitly distinct from electrical gate fanout (pp.571-573).
* `parallel_prefix` lacks `logic_family` values for compound domino and compound domino with stack-height reduction (pp.571,574-575).
* `parallel_prefix` lacks the independent `sizing_strategy` choice `{grouped, flat}` (pp.574,577-578).
* Technology/environment choices for wire-capacitance ratio, self-loading ratio, bitslice height, and input-capacitance limit determine the optimal topology but are absent from the family vocabulary (pp.578-579).
* `sparse_prefix_hybrid.slot sum_block` cannot name the document’s conditional-sum precompute/select block, although `sum_block_style` includes `conditional_sum` (pp.570,573-574,579-580).

## open_questions
* The implementation text names an `R4: 1-1-1-1-1-1 SP2` tree on p.579, while Fig. 14 identifies the fabricated tree as `radix-4 1-1-1 sparse-2`; the merge pass must not choose between these descriptions.
