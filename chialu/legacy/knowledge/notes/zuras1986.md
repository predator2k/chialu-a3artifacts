---
handle: zuras1986
citation: D. Zuras, W. H. McAllister, "Balanced Delay Trees and Combinatorial Division in VLSI", IEEE Journal of Solid-State Circuits, vol. 21, 1986
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [fp64]
authority: landmark
pages_read: 814-819 / 6
---

## summary
The paper develops balanced-delay reduction trees for a 64×64 Booth-encoded multiplier and a combinatorial redundant-digit divider for an IEEE 754 floating-point chip set. The multiplier trades intermediate wires for lower finite-size delay, while the divider uses carry-save partial remainders and radix-2 digits from {−1,0,1}. # p.814, p.817-p.819

## families
### booth_recoded_parallel  (role: extends)
mechanism: The Booth-encoded multiplier replaces serially connected full-adder columns with balanced-delay trees. Two full adders form an associative primitive operating on wire pairs, which permits balanced trees of order greater than one. The implemented 64×64 multiplier connects two fourth-order trees in series. # p.817-p.818
choices:
new_choices:
  reduction_topology: balanced_delay_reduction_tree — partial-product rows are combined through an order-k delay-balanced tree rather than a ripple or Wallace layout # p.817-p.818
slots:
  reduction: balanced_delay_reduction_tree [outside domain, order=4] # p.818
parameters: 64×64 operands; two fourth-order trees; each tree has length 18; 14 full-adder delays for the complete multiplier # p.818
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay, half multiplier | 7 | full-adder delays | 1.5-µm NMOS; 1986 | 16 delays, customary layout | half of a 64×64 Booth-encoded multiplier | p.818 |
| delay, complete multiplier | 14 | full-adder delays | 1.5-µm NMOS; 1986 | 32 delays, customary layout | two balanced trees connected in series | p.818 |
| theoretical minimum delay | 8 | full-adder delays | 1.5-µm NMOS; 1986 | balanced-delay multiplier at 14 delays | Wallace tree with complex interconnect | p.818 |
| delay difference | 1 | delay | 1.5-µm NMOS; 1986 | Wallace tree | fourth-order tree of length 18 | p.818 |
errors_and_checks: none
conditions: The fourth-order multiplier has slightly greater area because each cell adds two wires, but wiring area is not dominant in the implemented circuit. # p.818 The fourth-order tree grows as O(n^1/2), which is asymptotically worse than the Wallace tree's O(log(n)), so the reported advantage applies to small multiplier sizes. # p.818
evidence: §III; Fig. 9; Fig. 10; Fig. 11; p.817-p.818

### srt_radix2  (role: proposes)
mechanism: Each unrolled stage stores the partial remainder as carry-save words S and C, so the full sum is deferred until the last stage. Three upper positions of S and C are locally summed to classify the partial remainder. The redundant quotient digit Qn belongs to {−1,0,1}, and the next remainder is 2(PRn−D), 2PRn, or 2(PRn+D). # p.818-p.819
choices:
  residual_form: carry_save # p.818
  residual_estimate_bits: 3 # p.818
new_choices:
  implementation_topology: combinatorial_array — one spatial stage implements each quotient-bit recurrence rather than reusing a clocked stage # p.818
slots:
  digit_select: qds_table # p.818-p.819
parameters: radix 2; quotient digit set {−1,0,1}; n combinatorial stages; normalized divisor/dividend in [1,2); partial remainder constrained to [−2D,2D) # p.818-p.819
results:
| metric | value | unit | technology / device | baseline | condition | page |
| time complexity | O(n) | total delay | 1.5-µm NMOS; 1986 | O(n log(n)) for stages requiring full partial-remainder resolution | n-bit combinatorial divide | p.818-p.819 |
| area complexity | O(n²) | area | 1.5-µm NMOS; 1986 | O(n² log(n)) for a full-resolution combinatorial array | n-bit combinatorial divide | p.818-p.819 |
| stage delay | O(1) | delay per stage | 1.5-µm NMOS; 1986 | O(log(n)) with full carry resolution | carry-save residual and bounded-bit quotient selection | p.818 |
errors_and_checks: The redundant digit overlap permits Qn=0 for −1<PR<1, Qn=+1 for positive partial remainders, and Qn=−1 for negative partial remainders while preserving |PR|<2D. # p.818-p.819
conditions: The method requires normalized divisor/dividend values in [1,2), a carry-save partial remainder, and quotient selection from a bounded number of upper S/C bits. # p.818 Full partial-remainder resolution is required only after the last stage. # p.818
evidence: §IV; Fig. 12; Fig. 13; p.818-p.819

## new_families
### balanced_delay_reduction_tree  (domain: mul: integer multipliers, closest: carry_save_array, why_not: carry_save_array fixes a regular two-dimensional CSA organization, while this mechanism selects an order-k topology between ripple and binary trees)
mechanism: An order-k balanced-delay tree recursively joins progressively longer lower-order subtrees when their accumulated delays match. Order 1 is a ripple chain, sufficiently high order is a binary tree, and intermediate orders trade k lateral wires against delay. Associative operations apply directly; multiplier reduction uses a paired-full-adder associative primitive. # p.814-p.818
choices: order: Int[1..∞:1] # p.815-p.816; associative_primitive: {or, and, xor, paired_full_adder} # p.817; wire_count: order # p.815-p.817
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay | 11 | unit delays | 1.5-µm NMOS; 1986 | ripple chain, 63 delays | 64 inputs, order 2, two intermediate wires | p.815 |
| delay | 7 | unit delays | 1.5-µm NMOS; 1986 | binary tree, 6 delays | 64 inputs, order 3, three intermediate wires | p.815 |
| layout area | half | binary-tree area | 1.5-µm NMOS; 1986 | order-2k binary tree | order-k tree of the same length when wire area dominates | p.815 |
| delay penalty | 1 | unit delay | 1.5-µm NMOS; 1986 | order-2k binary tree | order-k tree of the same length | p.815 |
| area–time product improvement | about 71 percent | better than baseline | 1.5-µm NMOS; 1986 | order-6 binary tree | 64-input order-3 tree | p.817 |
evidence: §II-§III; Table I; Table II; Fig. 4-Fig. 11; p.814-p.818

## space_gaps
* The `booth_recoded_parallel.reduction` slot lacks `balanced_delay_reduction_tree`, which the implemented multiplier uses. # p.817-p.818
* `srt_radix2` lacks an implementation-topology choice covering a fully unrolled combinatorial array. # p.818
* The vocabulary lacks a reusable order-k balanced-delay reduction topology for associative logic and multiplier reduction. # p.814-p.818

## open_questions
* The paper identifies the multiplier as Booth-encoded but does not state its Booth radix.
* The paper does not quantify the multiplier's area increase beyond describing it as slight.
* The paper presents the divider recurrence for n bits but does not state the implemented divider array's exact significand width.
