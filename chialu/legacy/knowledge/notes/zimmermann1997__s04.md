---
handle: zimmermann1997#s04
parent: zimmermann1997
citation: Binary Adder Architectures for Cell-Based VLSI and their Synthesis
chapter: Basic Addition Principles and Structures
pdf_pages: 20-39
status: ok
kind: thesis_chapter
unit_classes: [BINARY_ALU]
formats: [binary]
authority: thesis
pages_read: 20 / 20
---

## summary
The chapter defines single-bit, carry-propagate, carry-save, multi-operand, and prefix addition structures. It classifies serial-prefix, group-prefix, tree-prefix, bit-level, and block-level speed-up schemes and compares their abstract area/delay/fan-out/interconnect properties. It also defines carry-skip, carry-select, and carry-increment blocks as compound structures built from partial carry-propagate adders.

## families
### ripple_carry  (role: defines)
mechanism: Full-adders are connected in series so each carry-out supplies the next higher bit’s carry-in; the serial-prefix algorithm performs the corresponding carry propagation.   # p.23, p.36
choices:
  full_adder_cell: UNKNOWN   # p.22
  carry_polarity_alternation: UNKNOWN   # p.36
new_choices:
  none
slots:
  none
parameters: n-bit operands; arbitrary partial-CPA group widths in block-level concatenation   # p.23, p.37
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay growth | linear with operand word length | abstract delay | abstract | none | serial carry propagation | p.24 |
| hardware complexity | O(n) | full-adder structures | abstract | none | direct bit-level implementation | p.36 |
| delay complexity | O(n) | abstract delay | abstract | none | direct bit-level implementation | p.36 |
errors_and_checks: none
conditions: The structure has minimum combinational hardware and is the slowest direct adder structure; it is also used as the partial CPA inside larger structures.   # p.36

### carry_lookahead  (role: defines)
mechanism: Carries are precomputed with generate/propagate equations. Traditional structures compute 4-bit group carries in parallel and arrange several groups linearly or hierarchically; the chapter identifies this construction as a parallel-prefix variant.   # p.36
choices:
  group_size: 4   # p.36
  levels: UNKNOWN   # p.36
  intergroup_carry: lookahead   # p.36
  block_sizing: uniform   # p.36
new_choices:
  none
slots:
  none
parameters: 4-bit groups; larger word lengths use linear or hierarchical group arrangements   # p.36
results:
| metric | value | unit | technology / device | baseline | condition | page |
| hardware complexity | O(n log n) | abstract area | abstract | ripple_carry | parallel carry computation | p.36 |
| delay complexity | O(log n) | abstract delay | abstract | ripple_carry | all primary signal paths | p.36 |
errors_and_checks: none
conditions: The scheme speeds all input-to-output paths and permits an area/speed trade-off through the selected prefix algorithm.   # p.36, p.39

### carry_skip  (role: defines)
mechanism: A partial CPA computes its ordinary carry-out and group propagate. A multiplexer selects either the computed carry-out or the incoming carry, breaking the activated carry-in-to-carry-out path through the partial CPA.   # p.37
choices:
  block_width: UNKNOWN   # p.37
  block_sizing: UNKNOWN   # p.39
  skip_levels: 1   # p.37
  skip_gate: mux   # p.37
new_choices:
  redundancy_form: redundant | duplicated_carry_chain_irredundant — distinguishes the false-path implementation from the duplicated-chain implementation   # p.38
slots:
  block_adder: UNKNOWN   # p.37
parameters: arbitrary partial CPA; one group-propagate signal and one 2-to-1 carry multiplexer per block   # p.37
results:
| metric | value | unit | technology / device | baseline | condition | page |
| carry propagation delay | constant | abstract delay | abstract | ripple_carry | carry-in to block carry-out | p.37 |
| redundant-version overhead | group-propagate logic and one multiplexer | abstract hardware | abstract | partial CPA | redundant skip block | p.38 |
| irredundant-version overhead | double carry chain | abstract hardware | abstract | redundant carry_skip | duplicated-chain form | p.38 |
errors_and_checks: The redundant implementation contains an unsensitizable longest path and redundant faults; a non-working skip mechanism requires additional detection capability.   # p.38
conditions: An OR-gate replacement accelerates only 0-to-1 carry transitions and is limited to precharged implementations such as dynamic logic.   # p.38

### carry_select  (role: defines)
mechanism: Two partial CPAs precompute the results for carry-in 0 and carry-in 1. The late carry-in selects the sum bits and carry-out through 2-to-1 multiplexers.   # p.38
choices:
  block_sizing: UNKNOWN   # p.39
  duplication: full_duplicate   # p.38
  select_source: rippled_block_carries   # p.39
new_choices:
  none
slots:
  block_adder: UNKNOWN   # p.38
parameters: two CPAs and one 2-to-1 multiplexer for every sum bit and the carry-out   # p.38
results:
| metric | value | unit | technology / device | baseline | condition | page |
| carry-input processing delay | constant | abstract delay | abstract | ripple_carry | both sum and carry outputs | p.38 |
| hardware overhead | double CPA and multiplexers | abstract hardware | abstract | ripple_carry | full precomputation | p.38 |
errors_and_checks: none
conditions: The scheme handles a late carry-in quickly but incurs high hardware overhead.   # p.38

### conditional_sum  (role: taxonomizes)
mechanism: Figure 3.1 classifies the conditional-sum adder as a carry-propagate-adder structure, but this chapter supplies no recurrence or circuit description.   # p.21
choices:
  base_block_width: UNKNOWN   # p.21
  mux_style: UNKNOWN   # p.21
  selection_radix: UNKNOWN   # p.21
new_choices:
  none
slots:
  none
parameters: UNKNOWN   # p.21
results:
| metric | value | unit | technology / device | baseline | condition | page |
| classification | carry-propagate adder | category | abstract | none | overview only | p.21 |
errors_and_checks: none
conditions: No design or performance conclusion is established beyond the classification.   # p.21
evidence: Figure 3.1

### carry_increment  (role: defines)
mechanism: A partial CPA precomputes only the carry-in-0 result. A constant-time incrementer conditionally adds one, while the block carry-out is formed from the CPA carry-out, group propagate, and incoming carry.   # p.38
choices:
  block_width: UNKNOWN   # p.38
  block_sizing: variable_ramp   # p.39
  intergroup_carry: rippled   # p.39
  increment_levels: UNKNOWN   # p.39
new_choices:
  none
slots:
  block_adder: UNKNOWN   # p.38
  increment_stage: prefix_and_incrementer [structure=UNKNOWN]   # p.38
parameters: one partial CPA, one incrementer, group-propagate logic, and one carry operator per block   # p.38
results:
| metric | value | unit | technology / device | baseline | condition | page |
| carry-input processing delay | constant | abstract delay | abstract | ripple_carry | sum and carry outputs | p.38 |
| hardware overhead | medium | abstract hardware | abstract | carry_select | one precomputed result plus incrementer | p.38 |
errors_and_checks: none
conditions: The incrementer is much cheaper than the second CPA and selection circuitry of carry-select, and some CPA/incrementer logic can be merged.   # p.38

### parallel_prefix  (role: taxonomizes)
mechanism: An associative binary operator combines prefix variables in serial, group-parallel, or tree-parallel graphs. Binary addition uses either generate/propagate pairs or the two possible carry values; preprocessing forms bit variables and postprocessing forms sums.   # p.27-p.35
choices:
  topology: sklansky | brent_kung | kogge_stone | han_carlson   # p.29-p.30
  valency: 2   # p.27-p.28
  log2_sparsity: UNKNOWN   # p.27-p.35
  fanout_cap: topology-dependent: sklansky unbounded [outside domain] | brent_kung log2 n or 3 [outside domain] | kogge_stone 2 | han_carlson 2   # p.29-p.30
  wire_track_budget: UNKNOWN   # p.28-p.32
  node_style: and_or   # p.35
new_choices:
  algorithm_class: serial_prefix | group_prefix | tree_prefix — selects the chapter’s top-level prefix classification   # p.28
  group_sizing: fixed | variable — selects equal or increasing group widths   # p.29-p.32
  parallel_levels: 1 | 2 | multilevel | maximum — selects the number of group-prefix levels   # p.29-p.32
  prefix_encoding: generate_propagate | carry_select — selects the prefix-variable representation   # p.33-p.35
  carry_in_processing: extra_prefix_level | special_3_input_operator | slow_postprocess — selects carry-in treatment   # p.33-p.35
slots:
  none
parameters: n-bit examples use binary operators and 16-bit graphs; exact formulas assume n is a power of 2   # p.28
results:
| metric | value | unit | technology / device | baseline | condition | page |
| serial-prefix operations | n-1 | binary operations | abstract | none | minimum-operation serial algorithm | p.28 |
| serial-prefix delay | n-1 | binary-operator delays | abstract | none | serial algorithm | p.28 |
| unoptimized-tree delay | log2 n | binary-operator delays | abstract | serial-prefix | separate output trees | p.29 |
| unoptimized-tree hardware | O(n^2) | binary operations | abstract | serial-prefix | separate output trees | p.29 |
| merged-tree hardware | O(n log n) or O(n) | binary operations | abstract | unoptimized tree | shared subexpressions | p.29 |
| Sklansky depth | log2 n | binary-operator delays | abstract | serial-prefix | minimal-depth tree | p.29-p.30 |
| Sklansky maximum fan-out | n/2 | loads | abstract | serial-prefix | highest-distribution nodes | p.29-p.30 |
| Sklansky interconnect | log2 n | wire tracks | abstract | serial-prefix | tiled graph | p.29-p.30 |
| Brent-Kung depth | 2 log2 n - 2 | binary-operator delays | abstract | Sklansky | bounded-fan-out tree | p.29-p.30 |
| Brent-Kung black nodes | 2n - log2 n - 2 | nodes | abstract | Sklansky | bounded-fan-out tree | p.29-p.30 |
| Kogge-Stone depth | log2 n | binary-operator delays | abstract | serial-prefix | minimal-depth tree | p.29-p.30 |
| Kogge-Stone maximum fan-out | 2 | loads | abstract | Sklansky | bounded-fan-out tree | p.29-p.30 |
errors_and_checks: none
conditions: Sklansky trades unbounded fan-out for minimum depth and few tracks; Kogge-Stone trades node/interconnect growth for minimum depth and fan-out 2; Brent-Kung and Han-Carlson are slower but more area-efficient.   # p.29

### carry_save_datapath  (role: defines)
mechanism: A carry-save adder emits sum and carry vectors instead of propagating carries. Multi-operand structures arrange full-adders or compressors as regular arrays or trees and assimilate the two final vectors with a carry-propagate adder.   # p.24-p.27
choices:
  compressor: 3_2 | 4_2   # p.24-p.27
  assimilation_point: end_of_chain   # p.24-p.27
  accumulator_redundant: true   # p.24, p.27
new_choices:
  reduction_topology: array | tree — selects the regular carry-save array or Wallace-tree arrangement   # p.25-p.27
slots:
  assimilator: UNKNOWN   # p.25-p.27
parameters: three operands for one CSA; m operands for arrays/trees; (m,2)-compressors forward m-3 intermediate carries   # p.24-p.26
results:
| metric | value | unit | technology / device | baseline | condition | page |
| CSA delay | constant, independent of n | abstract delay | abstract | carry-propagate addition | one three-operand CSA stage | p.24 |
| compressor delay | O(log m) | abstract delay | abstract | linear counter arrangement | tree-structured (m,2)-compressor | p.25 |
| final-adder replacement | one RCA replaced | adder count | abstract | CSA array with RCA | fast array-adder speed-up | p.25 |
errors_and_checks: none
conditions: A CSA array has balanced arrivals at the final CPA, so replacing only that CPA yields substantial speed-up; a CPA array has staggered arrivals and requires every constituent RCA to be replaced for comparable acceleration.   # p.24-p.25
evidence: Sections 3.3-3.4; Figures 3.7-3.13

## taxonomy
* 1-bit adders   # p.20-p.23
  * half-adder / (2,2)-counter -> binary_counter_compressor   # p.21-p.22
  * full-adder / (3,2)-counter -> binary_counter_compressor   # p.21-p.23
  * (m,k)-counter -> binary_counter_compressor   # p.20-p.23
  * (m,2)-compressor -> binary_counter_compressor   # p.22, p.25-p.26
* carry-propagate adders   # p.21, p.23
  * ripple-carry adder -> ripple_carry   # p.23
  * carry-skip adder -> carry_skip   # p.21, p.37-p.38
    * redundant carry-skip -> carry_skip   # p.37-p.38
    * irredundant duplicated-chain carry-skip -> carry_skip   # p.38
  * carry-select adder -> carry_select   # p.21, p.38
  * carry-increment adder -> carry_increment   # p.21, p.38
  * carry-lookahead adder -> carry_lookahead   # p.21, p.36
  * parallel-prefix adder -> parallel_prefix   # p.21, p.27-p.35
  * conditional-sum adder -> conditional_sum   # p.21
* carry-save and multi-operand adders   # p.21, p.24-p.27
  * three-operand CSA -> carry_save_datapath   # p.24
  * CSA array plus final CPA -> carry_save_datapath   # p.24-p.26
  * Wallace/compressor tree plus final CPA -> carry_save_datapath   # p.26-p.27
* prefix algorithms   # p.28-p.32
  * serial-prefix -> ripple_carry   # p.28
  * parallel-prefix   # p.28
    * tree-prefix   # p.29-p.30
      * unoptimized tree-prefix -> parallel_prefix   # p.29-p.30
      * Sklansky -> parallel_prefix   # p.29-p.30
      * Brent-Kung -> parallel_prefix   # p.29-p.30
      * Kogge-Stone -> parallel_prefix   # p.29-p.30
      * Han-Carlson -> parallel_prefix   # p.29-p.30
    * group-prefix   # p.29-p.32
      * fixed-group, 1-level -> parallel_prefix   # p.29-p.32
      * fixed-group, 2-level -> parallel_prefix   # p.29-p.32
      * fixed-group, multilevel -> parallel_prefix   # p.31
      * variable-group, 1-level -> parallel_prefix   # p.31-p.32
      * variable-group, 2-level/multilevel -> parallel_prefix   # p.31-p.32
      * optimized maximum-level -> parallel_prefix   # p.31-p.32
* CPA composition   # p.39
  * linear / hierarchical -> unmapped   # p.39
  * pure / mixed -> unmapped   # p.39

## primary_sources
* Sklansky, 1960 — minimal-depth tree-prefix algorithm   # p.29
* Brent and Kung, 1982 — bounded-fan-out tree-prefix algorithm   # p.29
* Kogge and Stone, 1973 — minimal-depth, fan-out-2 tree-prefix algorithm   # p.29
* Han and Carlson, 1987 — mixed Brent-Kung/Kogge-Stone tree-prefix algorithm   # p.29

## new_families
### binary_counter_compressor  (domain: adder, closest: carry_save_datapath, why_not: carry_save_datapath describes a redundant multi-bit datapath rather than the chapter’s primitive single-column counters)
mechanism: An (m,k)-counter counts m equal-weight input bits and emits a k-bit binary sum, where k is sufficient to encode the count. Half-adders and full-adders are the (2,2) and (3,2) cases; larger counters are composed from smaller counters and may use linear or tree arrangements. An (m,2)-compressor instead emits two redundant sum bits and forwards intermediate carries to the next column.   # p.20-p.23, p.25-p.26
choices:
  counter_form: half_adder | full_adder | m_k_counter | m_2_compressor   # p.20-p.23, p.25
  arrangement: linear | tree   # p.22-p.23, p.25-p.26
  full_adder_logic: half_adder_composition | generate_propagate | direct_xor_majority | carry_select   # p.22-p.23
results:
| metric | value | unit | technology / device | baseline | condition | page |
| full-adder area | 7-9 | gates | abstract | none | illustrated full-adder circuits | p.22 |
| full-adder delay | 2-4 | gate delays | abstract | none | illustrated full-adder circuits | p.22 |
| majority-gate area | 5 | gates | abstract | none | direct full-adder carry generation | p.22 |
| majority-gate delay | 2 | gate delays | abstract | none | direct full-adder carry generation | p.22 |
| multiplexer area | 3 | gates | abstract | none | carry-select full-adder | p.22 |
| multiplexer delay | 2 | gate delays | abstract | none | carry-select full-adder | p.22 |
evidence: Sections 3.1 and 3.4.2; Figures 3.2-3.5 and 3.11-3.12

## space_gaps
* parallel_prefix lacks values for unoptimized tree-prefix and the fixed/variable group-prefix classifications.   # p.28-p.32
* parallel_prefix lacks choices for prefix encoding and carry-in processing.   # p.33-p.35
* carry_skip lacks a choice distinguishing logically redundant and duplicated-chain irredundant implementations.   # p.37-p.38
* carry_save_datapath lacks an array/tree reduction-topology choice and a slot for primitive counter/compressor cells.   # p.24-p.27
* CPA composition by linear/hierarchical and pure/mixed schemes has no direct vocabulary representation.   # p.39

## open_questions
* Several exact complexity expressions in Figures 3.14-3.26 are degraded in the supplied text extraction; values not legible enough to copy verbatim must not be reconstructed.   # p.29-p.32
* The arbitrary partial CPA used by carry_skip, carry_select, and carry_increment cannot be assigned to a specific allowed block_adder family from this chapter.   # p.37-p.38
* The chapter names conditional_sum only in the overview, so its design choices remain unsettled here.   # p.21
