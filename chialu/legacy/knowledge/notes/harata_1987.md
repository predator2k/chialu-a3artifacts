---
handle: harata_1987
citation: Harata, Nakamura, Nagase, Takigawa, Takagi, "A High-Speed Multiplier Using a Redundant Binary Adder Tree", IEEE Journal of Solid-State Circuits, 1987
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int16]
authority: landmark
pages_read: pp.28–34 / 7 pages
---

## summary
The document implements a 16-bit × 16-bit two’s-complement multiplier that reduces eight modified-Booth partial products through a three-level tree of constant-time redundant binary adders. A fabricated 2.7-µm n-E/D MOS chip completes multiplication in 120 nsec, while preserving a regular cellular layout. # p.28, p.29, p.33

## families
### redundant_binary_multiplier  (role: proposes)
mechanism: A modified Booth generator produces eight partial products and converts each partial product to redundant binary form. Seven redundant binary adders reduce the partial products pairwise through a three-level binary tree. Each redundant digit uses separate positive/negative signals, so negative Booth partial products require neither an added ONE nor optional sign terms. A final 32-bit carry-lookahead converter produces the external two’s-complement result. # p.29, p.30, p.32
choices:
  rb_encoding: plus_minus_pair   # p.29, p.30
  rbnb_converter: cpa   # p.29, p.30
new_choices:
  physical_tree_layout: improved_v_binary_tree — signal flow proceeds in one direction through two repeated adder-cell patterns   # p.30, p.31
  partial_product_generation: modified_booth_to_redundant_binary — Booth partial products are generated directly in redundant binary form   # p.29
slots:
  final_converter: carry_lookahead   # p.30
parameters: 16-bit × 16-bit two’s-complement operands; eight partial products; seven redundant binary adders; three reduction levels; first/second/final adders contain 18/20/24 cells; 32-bit final converter; one multiplication per combinational propagation. # p.29, p.30
results:
| metric | value | unit | technology / device | baseline | condition | page |
| multiplication time | 120 | nsec | 2.7-µm n-E/D MOS, single-layer metal / 1987 | none | fabricated 16-bit × 16-bit multiplier, including input/output and intermediate buffers | p.31, p.33 |
| chip size | 5.8 × 6.3 | mm² | 2.7-µm n-E/D MOS, single-layer metal / 1987 | none | fabricated 16-bit × 16-bit multiplier | p.31, p.33 |
| transistor count | about 10 600 | transistors | 2.7-µm n-E/D MOS, single-layer metal / 1987 | none | fabricated 16-bit × 16-bit multiplier | p.31, p.33 |
| longest logic path | 46 | gates | 2.7-µm n-E/D MOS, single-layer metal / 1987 | none | input-to-output path | p.31, p.33 |
| intrinsic logic path | 29 | gates | 2.7-µm n-E/D MOS, single-layer metal / 1987 | none | 3 generator + 18 adder-tree + 8 converter gates | p.31 |
| redundant binary adder-tree area | about 4 × 4 | mm² | 2.7-µm n-E/D MOS, single-layer metal / 1987 | none | improved V-binary-tree layout | p.31, p.33 |
| estimated multiplication time | about 140 | ns | 2.7-µm n-E/D MOS estimate / 1987 | fabricated 16-bit × 16-bit multiplier at 120 ns | estimated 32-bit × 32-bit multiplier | p.32 |
| estimated multiplication-time increase | only 17 | percent | 2.7-µm n-E/D MOS estimate / 1987 | fabricated 16-bit × 16-bit multiplier | estimated 32-bit × 32-bit multiplier | p.32 |
| estimated transistor count | about 35000 | transistors | 2.7-µm n-E/D MOS estimate / 1987 | none | estimated 32-bit × 32-bit multiplier | p.32 |
| estimated chip size | about 10 × 11 | mm² | 2.7-µm design rule estimate / 1987 | none | estimated 32-bit × 32-bit multiplier | p.32 |
| estimated multiplication time | less than 50 | ns | 1.5-µm design rule, double-layer metal estimate / 1987 | none | estimated 32-bit × 32-bit multiplier | p.32 |
| estimated chip size | within 5.0 × 5.0 | mm² | 1.5-µm design rule, double-layer metal estimate / 1987 | none | estimated 32-bit × 32-bit multiplier | p.32 |
| intrinsic-path reduction | three times shorter | relative | NMOS comparison model / 1987 | array multiplier | 16-bit multiplier, delay assumed proportional to intrinsic logic path | p.32 |
| intrinsic-path reduction | four times shorter | relative | NMOS comparison model / 1987 | array multiplier | 32-bit multiplier, delay assumed proportional to intrinsic logic path | p.32 |
errors_and_checks: No approximation, arithmetic-error metric, or fault-detection mechanism is reported. # p.28, p.33
conditions: Multiplication time grows proportionally to log2 n because the partial products are reduced by a binary tree and the final conversion uses a tree carry-lookahead adder. # p.28, p.29 The design has regular, extensible cell placement, but it has about twice as many signal lines as conventional multipliers and requires careful wiring. # p.28, p.30 The modeled speed is similar to a Wallace-tree multiplier, while the layout has repeatability similar to an array multiplier. # p.32, p.33 The transistor count is lower than an array multiplier and higher than a Wallace-tree multiplier. # p.32
evidence: §II and Fig. 1–4, pp.28–30; §III and Fig. 5–10, pp.30–32; §IV, Tables II–III, pp.31–33.

### generalized_signed_digit  (role: instantiates)
mechanism: The internal radix-2 redundant representation uses the digit set {0,1,\bar{1}}. Addition first forms an intermediate carry and sum from same-position operand digits. A second step combines the intermediate sum with the next-lower-position carry without generating another carry, so two n-digit redundant numbers are added in constant time independent of word length. # p.29
choices:
  radix: 2   # p.29
  digit_encoding: two-signal {00→0, 01→1, 10→\bar{1}} [outside domain]   # p.30
  addition_scheme: carry_free   # p.29
  final_conversion: cpa   # p.29, p.30
new_choices:
  none
slots:
  none
parameters: digit set {0,1,\bar{1}}; two addition steps; one redundant digit represented by two signals {Xu,Xd}. # p.29, p.30
results:
| metric | value | unit | technology / device | baseline | condition | page |
| redundant-adder-tree intrinsic path | 18 | gates | 2.7-µm n-E/D MOS / 1987 | none | three-level tree in the fabricated 16-bit multiplier | p.31 |
errors_and_checks: The representation preserves exact integer values; no fault model or checker is reported. # p.29
conditions: Constant-time addition depends on retaining the redundant representation between operations. Conversion to two’s complement adds eight gates to the fabricated multiplier’s intrinsic path, while an all-redundant arithmetic system would produce the product after 21 gates. # p.31
evidence: §II-B–II-C and Table I, pp.29–30; Fig. 4 and §IV-A, pp.30–31.

## new_families
none

## space_gaps
* `booth_recoded_parallel.reduction` cannot name `redundant_binary_multiplier`, although the document reduces modified-Booth partial products with a redundant binary adder tree. # p.29
* `generalized_signed_digit.digit_encoding` lacks the document’s two-signal encoding `{00→0, 01→1, 10→\bar{1}}`. # p.30
* `redundant_binary_multiplier` lacks a physical tree-layout choice covering H/L/V/improved-V layouts, which materially affect wiring area and aspect ratio. # p.30, p.31

## open_questions
* The document names a modified Booth algorithm but does not state its radix, so `booth_radix` remains UNKNOWN.
* The numeric cells of Table II are not legible in the supplied document text, so only the comparison ratios stated in the surrounding prose are recorded.
