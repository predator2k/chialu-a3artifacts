---
handle: dadda_1983
citation: Dadda, "Some Schemes for Parallel Multipliers", Alta Frequenza, 1965
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [unsigned_binary]
authority: survey
pages_read: 8 / 8
---

## summary
The document proposes and compares serial-input binary multipliers composed of an array generator and a parallel-counter summator (pp.52-56). The schemes generate partial products by rows/diagonals or columns and emit the product serially, or emit its most-significant half in parallel (pp.52-56).

## families
### serial_serial_parallel  (role: extends)
mechanism: Both unsigned operands arrive least-significant bit first, with equal-weight bits arriving simultaneously. An array generator produces either each new row and diagonal of the partial-product array or the bits belonging to one or two columns. A summator built from parallel counters accumulates these elements and emits product bits with minimum delay after the corresponding operand bits arrive (pp.52-56).
choices:
  serial_operands: both   # p.52
  digit_size_bits: 1   # p.52
new_choices:
  array_generation: [subarray_rows_diagonals, column_wise] — selects how available partial-product elements are generated   # pp.53-55
  partial_sum_representation: [single_binary, two_binary_numbers, three_binary_numbers] — selects carry-propagate or redundant summator state   # pp.53-54
  product_output_form: [serial_single_output, stack_outputs, serial_lsb_parallel_msb] — selects where and when product bits appear   # pp.53-56
  input_register_style: [shift, stack, modified_stack] — selects operand storage in the array generator   # pp.53-55
  columns_per_step: [1, 2] — selects whether the generator supplies one or two partial-product columns per step   # pp.54-55
slots:
  none
parameters: n-bit natural binary operands; equal operand lengths; one bit per operand per input step; least-significant bit first; synchronous equal-weight input bits; examples include n=4 and n=15   # pp.52,54-55
results:
| metric | value | unit | technology / device | baseline | condition | page |
| array-generator outputs | 4n-4 | outputs | UNKNOWN / 1983 | β/γ generators | α generator with fixed output weights | p.57 |
| array-generator AND gates | n² | gates | UNKNOWN / 1983 | β/γ generators | α generator | p.57 |
| array-generator OR gates | 2(n-2) | gates | UNKNOWN / 1983 | β/γ generators | α generator | p.57 |
| array-generator outputs | 2n-1 | outputs | UNKNOWN / 1983 | α generator | β generator; weights multiplied by four each step | p.57 |
| array-generator AND gates | 2n-1 | gates | UNKNOWN / 1983 | α generator | β generator | p.57 |
| array-generator outputs | 2n-1 | outputs | UNKNOWN / 1983 | α generator | γ generator; weights multiplied by two each step | p.57 |
| array-generator AND gates | 2n-1 | gates | UNKNOWN / 1983 | α generator | γ generator | p.57 |
| maximum operand width | 5 | bits | UNKNOWN / 1983 | UNKNOWN | serial-column summator with s=3 counter outputs | p.54 |
| maximum operand width | 12 | bits | UNKNOWN / 1983 | UNKNOWN | serial-column summator with s=4 counter outputs | p.54 |
| maximum operand width | 12 | bits | UNKNOWN / 1983 | UNKNOWN | double-column summator using (15;4) and (14;4) counters | p.55 |
errors_and_checks: none
conditions: Serial multipliers require less silicon area than fully parallel multipliers but operate more slowly (p.52). Subarray schemes with feedback have larger delays and generally resist pipelining (pp.55-56). A pipelined parallel counter applies to the Fig. 13b column-wise scheme because that scheme does not feed partial sums or carries back through the counter stages (p.56). The preferred scheme depends on counter implementation/technology/routing/silicon area (p.56). The schemes assume equal operand lengths, although the document states that unequal lengths can be supported (p.56).
evidence: §§2-6; Figs. 1-16; Table I, pp.52-59

### carry_save_datapath  (role: instantiates)
mechanism: Faster summators avoid carry propagation by retaining each partial sum S_j as two or three equivalent binary numbers. Networks of (3;2), (4;3), and (5;3) parallel counters reduce the new row/diagonal and retained state while product bits are emitted. Two-number schemes use two cascaded (3;2) stages, while three-number schemes use one stage of (4;3)/(5;3) counters (pp.53-54).
choices:
  compressor: [3_2, 5_3]   # pp.53-54
  accumulator_redundant: true   # p.54
new_choices:
  redundant_rows: [2, 3] — number of equivalent binary words retained for S_j   # pp.53-54
  feedback_form: [partial_sum, carry] — state returned to the next serial multiplication step   # pp.54-56
slots:
  assimilator: none   # pp.53-56
parameters: two or three retained binary words; (3;2), (4;3), and (5;3) counters; one product bit may be emitted per summator step   # pp.53-56
results:
| metric | value | unit | technology / device | baseline | condition | page |
| Tsu | 2Tfa | delay | UNKNOWN / 1983 | single-word summator | Fig. 9 two-word schemes | p.56 |
| Tsu | T(5;3) | delay | UNKNOWN / 1983 | single-word summator | Fig. 10 three-word schemes | p.56 |
| T(5;3) | 3Tfa | delay | UNKNOWN / 1983 | UNKNOWN | implementation using three full adders | p.56 |
| Tcl | < Tsett + Tfa | delay | UNKNOWN / 1983 | unpipelined counter | pipelined counter built from full-adder stages; inequality copied as printed | p.56 |
| incremental hardware per operand bit | 2 | full adders | UNKNOWN / 1983 | preceding width | Fig. 9c for widths above n=4 | p.54 |
errors_and_checks: none
conditions: Two-word and three-word state avoids carry propagation in the summator (pp.53-54). Three-word state requires more memory elements but one counter stage, whereas two-word state requires two cascaded (3;2) stages (p.54). The speed/cost choice depends on the implementation technology (p.54).
evidence: §3, §5; Figs. 8-11; Table I, pp.53-57

## new_families
none

## space_gaps
* serial_serial_parallel lacks an array-generation choice covering subarray rows/diagonals versus column-wise generation (pp.53-55).
* serial_serial_parallel lacks a summator slot that can be filled by carry_save_datapath or a carry-propagate parallel adder (pp.53-56).
* serial_serial_parallel lacks a product-output choice covering serial/stack/serial-low-parallel-high forms (pp.53-56).

## open_questions
* The provided document text identifies IEEE and 1983 but does not print the venue name.
* The document does not specify a semiconductor technology, clock frequency, area, power, or measured implementation delay.
* The OCR of Table I obscures several labels/counts, so unambiguous generator counts were extracted while ambiguous entries remain unset.
