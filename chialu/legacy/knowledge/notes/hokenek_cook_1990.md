---
handle: hokenek_cook_1990
citation: E. Hokenek and R. K. Montoye, "Leading-Zero Anticipator (LZA) in the IBM RISC System/6000 Floating-Point Execution Unit", IBM Journal of Research and Development, 1990
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC, BINARY_ALU]
formats: [fp64, hex_double]
authority: landmark
pages_read: pp.1207-1213 / 7 pages
---

## summary
The document describes a two-cycle pipelined floating-point multiply-add-fused unit that computes D = (A X B) + C with one rounding and one double-precision result per cycle. The implementation combines modified Booth multiplication, (7,3) carry-save compression, partial-decode shifters, logarithmic end-around-carry addition, and leading 0/1 anticipation.

## families
### classic_fma  (role: proposes)
mechanism: The first pipeline cycle performs multiplication/exponent calculation/product alignment in parallel, and the second performs addition/post-normalization/rounding. The addend enters a free input of the 56-b multiplier's (7,3) compression structure, so accumulation adds no stated area or cycle-time penalty. Leading 0/1 anticipation predicts the post-normalization shift from the adder operands while the addition executes. The indivisible D = (A X B) + C operation has no intermediate rounding. # pp.1207-1209
choices:
  subsume_fp_add: true   # p.1207
  negation_handling: end_around_carry   # p.1210
  pipeline_depth: 2   # pp.1207-1208
new_choices:
  addend_injection: free_7_3_counter_input — selects how C enters partial-product compression   # p.1209
slots:
  align: full_align   # pp.1207-1210
  lza: lza   # pp.1208, 1210-1211
  cpa: end_around_carry   # p.1210
  round: UNKNOWN   # p.1207
  multiplier: booth_recoded_parallel   # pp.1208-1209
parameters: double precision; 56-b multiplier supporting 53-b IEEE or 56-b HEX significands; 2 pipeline cycles; II = 1 cycle   # pp.1207, 1209
results:
| metric | value | unit | technology / device | baseline | condition | page |
| pipeline latency | 2 | cycles | 1-µm CMOS, 1990 | none | double-precision MAF | p.1207 |
| initiation throughput | 1 | double-precision result/cycle | 1-µm CMOS, 1990 | none | pipelined execution | p.1207 |
| cycle time | 40 | ns | 1-µm CMOS, 1990 | other CMOS RISC systems | worst-case conditions | pp.1207, 1211 |
| LINPACK performance | 7.4-13 | MFLOPS | IBM RISC FPU, 1990 | none | reported system range | p.1207 |
| peak execution rate | 50 | MFLOPS | IBM RISC FPU, 1990 | none | 25-MHz clock frequency | p.1211 |
| transistor count | 440 000 | transistors | 1-µm CMOS, 1990 | none | complete FPU chip | p.1207 |
| power dissipation | 4 | W | 1-µm CMOS, 1990 | none | 40-ns operation | p.1211 |
| die dimensions | 12.7 X 12.7 | mm | triple-level-metal, single-polysilicon, 1-µm CMOS, 1990 | none | complete FPU chip | p.1211 |
errors_and_checks: The fused operation incurs one rounding error and no intermediate rounding. # p.1207
conditions: The fused datapath increases the mantissa add/normalize range by 1/2 relative to a conventional multiplier/adder pair. A two-stage implementation requires a fast shifter and an LZA that overlaps post-normalization with addition. # p.1208
evidence: Abstract; §§II-III; Figs. 1-2; §IV; §V, pp.1207-1212

### booth_recoded_parallel  (role: instantiates)
mechanism: Modified Booth encoding forms partial products, and an extended Wallace carry-save tree uses (7,3) counters to reduce seven input bits to a 3-b binary sum. The 56-b organization leaves one counter input free for the aligned addend. The physical organization reduces long loaded wires and compression stages in the CMOS implementation. # pp.1208-1209
choices:
new_choices:
  reduction_counter: 7_to_3 — selects the counter arity used by the Wallace compression tree   # pp.1208-1209
slots:
  reduction: csa_reduction_tree   # pp.1208-1209
parameters: 56-b multiplier; first-stage cell has seven 4-input multiplexors and 28 control/data inputs; cell width is 36 tracks; (7,3) wiring occupies 18 transistor locations or M2 wires per cell   # pp.1209
results:
| metric | value | unit | technology / device | baseline | condition | page |
| long-wire reduction | factor of 2.5 | ratio | 1-µm CMOS, 1990 | layout without the described physical optimization | (7,3) cell | p.1209 |
| connection count | half as many | connections | 1-µm CMOS, 1990 | (3,2) adder reduction | producing the final result | p.1209 |
| compression-stage reduction | factor of 1.6 | ratio | 1-µm CMOS, 1990 | (3,2) adder stages | partial-product compression | p.1209 |
| multiplier-array area | 4 X 5 | mm | 1-µm CMOS, 1990 | none | complete multiplier array | p.1211 |
errors_and_checks: none
conditions: Long Wallace-tree wires have substantial capacitive delay in the CMOS technology, so the design minimizes significantly loaded stages and wire lengths. # pp.1208-1209
evidence: §III-A; Figs. 3-4, pp.1208-1209; §IV, p.1211

### barrel_mux_tree  (role: extends)
mechanism: The partial-decode or modulo shifter divides a wide shift into nested shift groups. A 160+ bit example shifts by multiples of 16, then multiples of four, then 0-3 positions. Each nested shift amount is calculated with modulo arithmetic, and fewer than 64 active data bits allow a four-way multiplexor despite the broad first-stage range. Sticky-bit generation ORs the control signals. # pp.1209-1210
choices:
  stage_radix: mixed_partial_decode [outside domain]   # pp.1209-1210
  stage_order: large_shift_first   # pp.1209-1210
  sticky_collect: true   # p.1210
new_choices:
  shift_group_steps: 16_4_1 — defines the nested partial-shift position groups   # pp.1209-1210
  amount_control: modulo_arithmetic — derives each nested stage's control amount   # p.1209
slots:
  none
parameters: example input width 160+ bit; shift groups 0-160 by 16, 0-12 by 4, and 0-3; four-way multiplexor first stage   # pp.1209-1210
results:
| metric | value | unit | technology / device | baseline | condition | page |
| shift time | 6 | ns | 1-µm CMOS, 1990 | none | after the shift amount is calculated | p.1210 |
errors_and_checks: none
conditions: The partial-shift steps/sequences/control signals are application-specific. Subdivided shift groups also support other bit manipulations. # p.1210
evidence: §III-B; Fig. 5, pp.1209-1210

### end_around_carry  (role: instantiates)
mechanism: A 114-b logarithmic adder concatenated with a 55-b incrementer operates in one's-complement form with end-around carry. A binary tree alternates true and complementary propagate/generate stages. Least-significant positions buffer the doubling carry load, which bounds stage fanout at about 3 and produces the end-around carry in one gate delay. A negative result is complemented to produce sign-magnitude output. # p.1210
choices:
new_choices:
  operand_form: ones_complement — defines the internal representation requiring end-around carry   # p.1210
slots:
  none
parameters: 114-b adder; 55-b incrementer; fanout about 3 per stage   # p.1210
results:
| metric | value | unit | technology / device | baseline | condition | page |
| end-around-carry delay | 1 | gate delay | 1-µm CMOS, 1990 | none | logarithmic buffering scheme | p.1210 |
| negative-result conversion delay | 1 | additional gate delay | 1-µm CMOS, 1990 | positive-result path | complement to sign magnitude | p.1210 |
errors_and_checks: none
conditions: Negative results require output complementation, which adds one gate delay. # p.1210
evidence: §III-C, p.1210

### lza  (role: proposes)
mechanism: The leading 0/1 anticipator consumes the adder's G/P/Z signals and predicts the post-normalization shift before carry propagation completes. Four-bit hexadecimal groups first generate ZZ/GG/PP/PZ/PG states. Recursive lookahead then combines adjacent groups with doubling/buffering comparable to the logarithmic adder. The output states are ORed and encoded for the partial-decode shifter. # pp.1210-1211
choices:
new_choices:
  input_tokens: G_P_Z — generate/propagate/zero signals shared with the carry-lookahead adder   # p.1210
  initial_group_width: 4 — number of bits processed by the first lookahead stage   # pp.1210-1211
  recursion: state_lookahead_doubling — combines ZZ/GG/PP/PZ/PG group states recursively   # p.1211
  prediction_correction: binary_normalization — corrects a possible single-position overshift   # p.1210
slots:
  none
parameters: 4-b initial groups; shift output coded as (0...7) X 16 + (0...4) X 4   # pp.1210-1211
results:
none
errors_and_checks: Unmonitored low-order bits permit a carry to cause a single-bit-position overshift, which binary normalization corrects. # p.1210
conditions: The LZA must complete in approximately log(n) time alongside the adder. The first stage uses four-bit groups because the LZA parallel cell is more complex than a carry cell. # pp.1210-1211
evidence: §III-D; Figs. 6-8; equations (1)-(10), pp.1210-1211

## new_families
none

## space_gaps
* `barrel_mux_tree.stage_radix` lacks a mixed-radix partial-decode value for the 16/4/1 modulo-shifter stages. # pp.1209-1210
* `csa_reduction_tree` lacks a declared counter-primitive choice for the document's (7,3) Wallace reduction. # pp.1208-1209
* `lza` appears as a slot filler but lacks declared choices for token encoding/group width/recursion/prediction correction. # pp.1210-1211
* `classic_fma` lacks a choice for injecting the aligned addend through an unused compression-counter input. # p.1209

## open_questions
* Table I's subunit data rows are not legible in the supplied document text, so their transistor/area/speed values remain unextracted.
* The document says “modified Booth encoding” without stating its radix, so `booth_radix` remains UNKNOWN.
* The document does not identify the rounding circuit family, so the `round` slot remains UNKNOWN.
