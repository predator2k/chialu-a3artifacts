---
handle: makino_1996
citation: Makino, Nakase, Suzuki, Morinaka, Shinohara, Mashiko, "An 8.8-ns 54x54-bit Multiplier with High Speed Redundant Binary Architecture", IEEE Journal of Solid-State Circuits, 1996
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int54]
authority: landmark
pages_read: 713–783 / 11
---

## summary
The paper proposes a 54 × 54-bit two's-complement multiplier that generates redundant-binary partial products without added conversion hardware, reduces them through a binary tree of improved redundant-binary adders, and converts the final result through a multiplexer carry network. # p.713–720
The fabricated 0.5-µm CMOS chip reports an 8.8 ns multiplication time at 3.3 V. # p.720–722

## families
### redundant_binary_multiplier  (role: proposes)
mechanism: Two adjacent normal-binary partial products form one redundant-binary partial product by inverting one partial product and adding the negative digit (0, 1). Improved RBA1 cells reduce pairs of redundant-binary numbers in a four-stage binary Wallace tree without continuous carry propagation. The final (F+, F−) result is converted to normal binary by increasingly sized carry-select groups whose propagation paths contain multiplexers rather than generate/propagate logic. # p.714–720
choices:
  rb_encoding: plus_minus_pair   # p.714–716
  booth_radix: second-order Booth [outside domain]   # p.719
  rbnb_converter: carry_select   # p.717–719
new_choices:
  rbpp_generation: paired_nb_invert_plus_negative_digit — two normal-binary partial products form one RB partial product without additional conversion hardware   # p.714
  rba_cell_circuit: inverter_2nand_transmission_gate — RBA1 excludes NOR/complex gates and series transmission-gate paths   # p.715–717
  converter_grouping: increasing_group_width — carry-select group widths increase by one to equalize critical-path multiplexer counts   # p.718
slots:
  final_converter: carry_select   # p.717–719
parameters: 54 × 54-bit operands; 108-bit product; 27 Booth partial products; 15 RB partial products; four RBA stages; final RB digits partitioned into 4, 8, 16, and 80 digits; 12 multiplexer stages on the critical path of the 80-bit converter   # p.719–720
results:
| metric | value | unit | technology / device | baseline | condition | page |
| multiplication time | 8.8 | ns | 0.5-µm CMOS, triple-level metal / 1996 | none | measured at 3.3 V | p.721 |
| simulated multiplication time | 8.8 | ns | 0.5-µm CMOS model / 1996 | none | extracted critical path at 3.3 V | p.720 |
| RBPP generation delay | 2.3 | ns | 0.5-µm CMOS model / 1996 | none | input buffer, Booth encoder, and selector included | p.720 |
| Wallace-tree delay | 3.8 | ns | 0.5-µm CMOS model / 1996 | none | four RBA stages | p.720 |
| RB-to-NB conversion delay | 2.7 | ns | 0.5-µm CMOS model / 1996 | none | 80-bit conversion | p.720 |
| RBA1 delay | 0.89 | ns | 0.5-µm CMOS model / 1996 | RBA2 1.11 ns; RBA3 1.36 ns; NBA1 1.20 ns; NBA2 1.04 ns | fan-out 1 and 0.5-mm interconnection | p.717 |
| active area | 3.05 × 3.08 | mm² | 0.5-µm CMOS, triple-level metal / 1996 | none | pad area excluded from density calculation | p.720–721 |
| transistor count | 78,800 | transistors | 0.5-µm CMOS, triple-level metal / 1996 | 81,600 [3]; 82,500 [4]; 100,200 [5] | 54 × 54-bit multipliers | p.720 |
| transistor density | 8.4 | k/mm² | 0.5-µm CMOS, triple-level metal / 1996 | none | active area | p.720–721 |
| power dissipation | 216 | mW | 0.5-µm CMOS, triple-level metal / 1996 | none | measured at 40 MHz and 3.3 V | p.721 |
| power dissipation | 540 | mW | 0.5-µm CMOS, triple-level metal / 1996 | conventional multiplier [3] | estimated at 100 MHz and 3.3 V; 38% reduction | p.721 |
| speed improvement | more than 12 | % | 0.5-µm CMOS, triple-level metal / 1996 | conventional multiplier [3] | 54 × 54-bit multiplication | p.722 |
errors_and_checks: The circuit computes an exact 108-bit two's-complement product. More than ten thousand functional patterns, including the stated critical pattern, were tested; the paper reports no concurrent error-detection mechanism. # p.720–721
conditions: RBA1 requires each (1, 1) digit state to be converted to (0, 0) before the Wallace tree, which adds one 2-NAND stage with 150 ps delay. # p.716 CONV1 has the fastest delay and lowest transistor count among the compared converters/adders for word lengths greater than 16 bits. # p.719 The no-extra-hardware RBPP generation method applies to multiple-number summation and is not limited to Booth multipliers. # p.714
evidence: §II and Figs. 1–5 establish the RB encoding/RBA/converter; Tables II–IV compare the components; §III and Figs. 6–7 establish the multiplier organization/timing; §IV, Figs. 8–11, and Tables V–VI report silicon results. # p.714–721

## new_families
none

## space_gaps
* `redundant_binary_multiplier.booth_radix` lacks a value that preserves the paper's term “second-order Booth” without mapping it to a numeric radix. # p.719
* `redundant_binary_multiplier` lacks choices for RB partial-product formation, RBA cell circuit style, and converter grouping. # p.714–719

## open_questions
* The document calls its recoding “second-order Booth's algorithm” and states that it halves the partial-product count, but the document does not name the corresponding numeric `booth_radix`; the merge pass must not choose between `2` and `4`. # p.719
