---
handle: oklobdzija_1994
citation: V. G. Oklobdzija, "An Algorithmic and Novel Design of a Leading Zero Detector Circuit: Comparison with Logic Synthesis", IEEE Transactions on VLSI Systems, vol. 2, no. 1, pp. 124-128, 1994
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary]
authority: incremental
pages_read: 124-128 / 5
---

## summary
The paper proposes a modular leading-zero detector that recursively combines position/valid fields in a logarithmic-depth tree. Implemented 32-bit/64-bit CMOS circuits outperform synthesized equivalents in speed/area, while a 64-bit ECL implementation produces a nominal result in 200 pS.

## families
### lzd_cell_tree  (role: proposes)
mechanism: Input bits first form groups that emit a position bit P and a valid bit V. Each subsequent level ORs the two input valid bits and uses the left valid bit to select/concatenate the corresponding position field. Repeating this combination constructs the leading-zero count with log2(N) levels from 2-bit groups or log2(N)-1 levels from 4-bit groups. CMOS levels use pass-transistor multiplexers; the ECL implementation combines four preceding groups in each tree.   # p.124-126, p.128
choices:
  block_primitive: pair_cell   # p.124-126
  block_primitive: nibble_cell   # p.125-126, p.128
  formulation: hierarchical_valid_position   # p.124-126
new_choices:
  layout_shape: regular | rectangular_stage_resized — the rectangular layout enlarges cells at later tree levels while keeping circuit width constant   # p.126-127
  level_circuit_style: pass_transistor_multiplexer_cmos | wired_or_ecl_tree — the technology-specific implementation of each hierarchy level   # p.125-126, p.128
slots:
  none
parameters: CMOS prototypes include 32-bit and 64-bit LZDs; the reported size sweep extends through N=128; pair grouping gives log2(N) stages, 4-bit initial grouping gives log2(N)-1 stages, and the 64-bit ECL design uses three ECL trees with a possible two-tree implementation when its first level is integrated into the second.   # p.124, p.126-128
results:
| metric | value | unit | technology / device | baseline | condition | page |
| layout dimensions | 163 x 340 | μm | 0.6 μm CMOS, 1994 | none | 32-bit algorithmic regular layout | p.126 |
| layout dimensions | 186 x 403 | μm | 0.6 μm CMOS, 1994 | none | 32-bit logic-synthesis regular layout | p.126 |
| layout area increase | 35 | % | 0.6 μm CMOS, 1994 | algorithmic regular layout | logic-synthesis regular layout | p.126 |
| delay | 4.5 | nS | 0.6 μm CMOS, 1994 | none | 32-bit algorithmic regular layout, typical case | p.126 |
| delay | 5.8 | ns | 0.6 μm CMOS, 1994 | none | 32-bit logic-synthesis regular layout, typical case | p.126 |
| delay increase | 29 | % | 0.6 μm CMOS, 1994 | algorithmic regular layout | logic-synthesis regular layout, typical case | p.126 |
| layout dimensions | 206 x 363 | μm | 0.6 μm CMOS, 1994 | none | 32-bit algorithmic rectangular layout | p.127 |
| layout dimensions | 181 x 473 | μm | 0.6 μm CMOS, 1994 | none | 32-bit logic-synthesis rectangular layout | p.127 |
| layout area reduction | 14.5 | % | 0.6 μm CMOS, 1994 | logic-synthesis rectangular layout | algorithmic rectangular layout | p.127 |
| delay | 6.9 | nS | 0.6 μm CMOS, 1994 | none | algorithmic rectangular layout, nominal case | p.127 |
| delay | 7.7 | nS | 0.6 μm CMOS, 1994 | none | logic-synthesis rectangular layout, nominal case | p.127 |
| speed improvement | 12 | % | 0.6 μm CMOS, 1994 | logic-synthesis rectangular layout | algorithmic rectangular layout, nominal case | p.127 |
| speed improvement | 19 | % | 0.6 μm CMOS, 1994 | logic-synthesis rectangular layout | algorithmic rectangular layout, worst case; first comparison statement | p.127 |
| speed improvement | 15 | % | 0.6 μm CMOS, 1994 | regular algorithmic layout | rectangular algorithmic layout, 1.0 pF load, nominal case | p.127 |
| speed improvement | 12 | % | 0.6 μm CMOS, 1994 | regular algorithmic layout | rectangular algorithmic layout, 1.0 pF load, worst case | p.127 |
| speed loss | 10 | % | 0.6 μm CMOS, 1994 | regular algorithmic layout | rectangular algorithmic layout, no load, nominal case | p.127 |
| speed loss | 23 | % | 0.6 μm CMOS, 1994 | regular algorithmic layout | rectangular algorithmic layout, no load, worst case | p.127 |
| delay | 6.9 | nS | 0.6 μm CMOS, 1994 | none | algorithmic rectangular layout, 1.0 pF load, nominal case | p.127 |
| delay | 7.7 | nS | 0.6 μm CMOS, 1994 | none | logic-synthesis rectangular layout, 1.0 pF load, nominal case | p.127 |
| delay | 11.4 | nS | 0.6 μm CMOS, 1994 | none | algorithmic rectangular layout, 1.0 pF load, worst case | p.127 |
| delay | 13.6 | nS | 0.6 μm CMOS, 1994 | none | logic-synthesis rectangular layout, 1.0 pF load, worst case | p.127 |
| speed improvement | 12 | % | 0.6 μm CMOS, 1994 | logic-synthesis rectangular layout | algorithmic rectangular layout, 1.0 pF load, nominal case | p.127 |
| speed improvement | 15 | % | 0.6 μm CMOS, 1994 | logic-synthesis rectangular layout | algorithmic rectangular layout, 1.0 pF load, worst case; later comparison statement | p.127 |
| speed improvement range | 12%-56% | % | 0.6 μm CMOS, 1994 | logic synthesis | algorithmic implementation across reported conditions | p.127-128 |
| layout area improvement range | 14.5%-35% | % | 0.6 μm CMOS, 1994 | logic synthesis | algorithmic implementation across layout approaches | p.127-128 |
| delay | 200 | pS | UNKNOWN node; advanced Motorola BiCMOS process, 1994 | none | 64-bit ECL LZD, nominal time | p.128 |
errors_and_checks: none
conditions: The regular CMOS hierarchy maintains low/regular fan-in and fan-out and is faster under no-load/light-load conditions. The rectangular stage-resized layout wins with a 1.0 pF output load because its final stages have stronger drive, but it loses without that load because increased input capacitance offsets the drive improvement. Four-way grouping is suited to ECL/BiCMOS technologies that tolerate higher fan-in/fan-out.   # p.124-128
evidence: Algorithm and Figs. 1-3, p.124-126; simulation/layout comparisons in Tables II-V and Figs. 4-5, p.126-127; 64-bit ECL structure in Figs. 6-8, p.128.

## new_families
none

## space_gaps
* lzd_cell_tree lacks a choice for regular versus stage-resized rectangular physical organization, which changes delay according to output load.   # p.126-127
* lzd_cell_tree lacks a technology-level circuit-style choice for pass-transistor CMOS multiplexers versus wired-OR ECL trees.   # p.125-126, p.128

## open_questions
* Table III row labels and several NC/WC entries are not legible in the supplied document text, so those values cannot be associated reliably with particular detector widths.
* Page 127 first reports a 19% worst-case advantage for the rectangular algorithmic design over logic synthesis, but the later 1.0 pF comparison reports 15% from 11.4 versus 13.6 nS; the merge pass must preserve this inconsistency rather than select one value.
