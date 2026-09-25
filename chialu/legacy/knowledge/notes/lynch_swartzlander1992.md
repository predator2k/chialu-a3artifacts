---
handle: lynch_swartzlander1992
citation: T. W. Lynch, E. E. Swartzlander Jr., "A Spanning Tree Carry Lookahead Adder", IEEE Transactions on Computers, vol. 41, no. 8, pp. 931-939, 1992.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [fp64]
authority: landmark
pages_read: 931-939 / 9
---

## summary
The paper presents the 56-bit significand adder implemented in the AMD Am29050. The design combines a four-way spanning carry-lookahead tree with uniform eight-bit carry-select blocks and produces eight-bit-boundary carries without back propagation. The 1 μm CMOS implementation has a measured add time of approximately 3.2 ns.

## families
### sparse_prefix_hybrid  (role: proposes)
mechanism: Four-bit Manchester carry-chain modules combine propagate/generate intervals in a three-level, four-way tree. Spanning cells combine overlapping intervals by using the associativity and idempotency of the fundamental carry operation. The tree directly produces carries at 0, 8, 16, 24, 32, 40, 48, and 56-bit boundaries without a back-propagation pass, and each carry selects between two precomputed eight-bit ripple-carry sums.
choices:
  log2_sparsity: 3   # p.931
  tree_topology: spanning_tree [outside domain]   # pp.933-935
  valency: 4   # pp.931, 933
  sum_block_style: carry_select   # pp.931, 935
new_choices:
  none
slots:
  sum_block: ripple_carry   # pp.935-937
parameters: 56-bit implemented significand adder; four-bit tree groups; eight-bit carry spacing; eight-bit carry-select blocks; three Manchester carry-chain levels on the critical path   # pp.931, 933, 937-938
results:
| metric | value | unit | technology / device | baseline | condition | page |
| measured add time | approximately 3.2 | ns | 1 μm CMOS, AMD Am29050; year UNKNOWN | none | rising clock edge to the most significant sum output | p.938 |
| layout area | 1.8 x 10^6 | square μm | 1 μm CMOS, AMD Am29050; year UNKNOWN | none | 56-bit implementation | p.937 |
| layout width | 450 | μm | 1 μm CMOS, AMD Am29050; year UNKNOWN | none | 24 ≤ N < 256 | p.937 |
| layout height | 4010 | μm | 1 μm CMOS, AMD Am29050; year UNKNOWN | none | 56-bit implementation | p.937 |
errors_and_checks: none
conditions: Dynamic implementation requires an idle clock phase for precharging and requires operands to be established at the beginning of evaluation.   # pp.931-932
conditions: The four-way tree was selected from simulations under the restriction that the regular tree use equal-length Manchester carry chains; mixed chain lengths could improve speed while reducing layout regularity.   # p.931
conditions: The measured design's speed is expected to remain nearly constant for 24 ≤ N < 64 in comparable CMOS technologies.   # p.938
conditions: Third and fourth tree levels fit into holes in the second level for adders up to 256 bits, so area scales directly with word size over the stated range.   # p.937
evidence: §I; §II; §III; §IV; Figs. 2, 3, 5, 6, and 7; (6), (9), (10), and (11), pp.931-938

### carry_select  (role: instantiates)
mechanism: Each uniform eight-bit section computes results for carry-in ZERO and carry-in ONE. Exclusive-OR gates form the sums, and 2:1 multiplexers select the correct result when the corresponding eight-bit-boundary carry arrives from the spanning tree.
choices:
  block_sizing: uniform   # pp.931, 935
  duplication: full_duplicate   # pp.935-937
  select_source: lookahead_tree   # pp.931, 935
new_choices:
  none
slots:
  block_adder: ripple_carry   # pp.935-937
parameters: eight-bit blocks; two precomputed carry cases; one 2:1 selection multiplexer per sum bit   # pp.931, 935-938
results:
| metric | value | unit | technology / device | baseline | condition | page |
| carry-select block width | 8 | bits | 1 μm CMOS, AMD Am29050; year UNKNOWN | Manchester carry-lookahead hybrid requiring at least 16-bit carry-select sections | spanning tree produces uniformly spaced carries | p.931 |
errors_and_checks: none
conditions: The eight-bit ripple results become ready slightly before the tree select signals, and the eight-bit multiplexers keep carry-output loading within the design target.   # p.931
evidence: §I; §III; §IV; Figs. 2 and 5, pp.931, 933-938

### manchester_carry_chain  (role: instantiates)
mechanism: One Manchester carry-chain bit implements each fundamental carry operation. Four adjacent cells form each four-bit tree module. Reduced modules remove the block-propagate chain and use an extra transistor to discharge group generate through the propagate chain, which saves four transistors and lowers internal loading when intermediate outputs are unnecessary.
choices:
  chain_segment_length: 4   # pp.932, 935
  circuit_style: dynamic   # pp.931-932
new_choices:
  none
slots:
  none
parameters: four-cell tree modules; three module levels on the 56-bit critical path; paired four-bit modules form eight-bit ripple-carry sections   # pp.932, 935-938
results:
| metric | value | unit | technology / device | baseline | condition | page |
| transistor saving | 4 | transistors | 1 μm CMOS, AMD Am29050; year UNKNOWN | basic Manchester carry-chain cell | reduced cell without intermediate outputs | p.935 |
errors_and_checks: none
conditions: The implementation discussion applies to dynamic logic, while the theoretical fundamental-carry-operation analysis applies independently of circuit implementation.   # p.932
evidence: §II; §III; §IV; Figs. 4 and 5, pp.932, 935-938

## new_families
none

## space_gaps
* `sparse_prefix_hybrid.tree_topology` lacks the `spanning_tree` value for a multiway tree that derives uniformly spaced carries from overlapping propagate/generate intervals without back propagation.   # pp.933-935

## open_questions
* The paper calls the circuits dynamic logic but does not identify the implementation specifically as `dynamic_domino`.
* The paper reports the Am29050 measurements without stating a separate year for the measured result.
