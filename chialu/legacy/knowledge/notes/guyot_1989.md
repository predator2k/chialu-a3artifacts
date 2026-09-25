---
handle: guyot_1989
citation: Guyot, Herreros, Muller, "JANUS, an On-Line Multiplier/Divider for Manipulating Large Numbers", 9th IEEE Symposium on Computer Arithmetic, 1989
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [radix-2 signed binary digit]
authority: incremental
pages_read: 106-111 / 6
---

## summary
JANUS is a digit-serial, most-significant-digit-first unit for addition/subtraction/multiplication/division/remainder on operands of up to 600 decimal digits. The implementation uses radix-2 signed binary digits, carry-free local addition, replicated multiplier slices, and quotient selection from four nonredundant leading partial-remainder digits.

## families
### generalized_signed_digit  (role: instantiates)
mechanism: Each digit belongs to {-1,0,1} and is represented by a negative/positive bit pair. Swapping or complementing the pair changes its sign, which permits subtractors to reuse adder gates. The two-input parallel adder limits carry propagation to two positions, while PPM cells also form a three-input carry-save adder. # p.106–107
choices:
  radix: 2   # p.106
  digit_encoding: negative_positive_bit_pair [outside domain]   # p.106
  addition_scheme: carry_free   # p.106–107
new_choices:
  zero_encoding: {(0,0), (1,1)} — the redundant bit-pair encodings permitted for zero   # p.106
slots:
  none
parameters: digit set {-1,0,1}; two bits per SBD; maximum carry propagation of two positions   # p.106–107
results:
| metric | value | unit | technology / device | baseline | condition | page |
| parallel three-input adder delay | 3 PPM boxes (i.e., 6 gates) | gates | UNKNOWN; 1989 | UNKNOWN | carry-free adder combined with the three-input carry-save adder | p.107 |
errors_and_checks: none
conditions: Radix 2 makes the product of two SBDs one SBD. # p.107
evidence: §A and §B.1; Figs. 1–3, p.106–107.

### serial_serial_parallel  (role: proposes)
mechanism: Both operands enter most-significant SBD first. Backward-running control tokens load growing operand prefixes into local latches, and identical slices combine a one-digit multiplier, a three-input serial adder, and a three-input parallel adder to emit the on-line product. # p.106–108
choices:
  serial_operands: both   # p.108
  digit_size_bits: 1   # p.106–108
new_choices:
  digit_order: msdf — both operands and results circulate most-significant digit first   # p.106
slots:
  none
parameters: radix-2 SBD operands; three-slice explanatory circuit; 64-SBD test circuit; target 2048 SBDs representing 600 decimal digits   # p.108–109
results:
| metric | value | unit | technology / device | baseline | condition | page |
| slice logic | 32 | gates | UNKNOWN; 1989 | UNKNOWN | one identical SBD multiplier slice | p.108 |
| slice transistor count | 152 | transistors | UNKNOWN; 1989 | UNKNOWN | one identical SBD multiplier slice | p.108 |
| target multiplier transistor count | a little over 300k | transistors | UNKNOWN; 1989 | UNKNOWN | 600 decimal digits / 2048 SBDs | p.108 |
| implemented test precision | 64 | SBD digits | UNKNOWN; 1989 | UNKNOWN | designed multiplier test circuit | p.109 |
errors_and_checks: exact signed-digit arithmetic is described; no numerical-error or fault-detection result is reported. # p.106–109
conditions: Additional slices extend precision without transistor resizing because each slice communicates only with neighboring slices. # p.108
evidence: §B.2; Figs. 5–6 and 10–11; Table 1, p.107–110.

### online_msdf  (role: instantiates)
mechanism: The divider implements the Ercegovac–Trivedi algorithm. The multiplier updates a signed partial remainder without carry propagation across as many as 2048 positions, while four leading slices convert the four most significant partial-remainder digits to nonredundant form and predict the next signed quotient digit. # p.108–109
choices:
  radix: 2   # p.106–109
new_choices:
  quotient_selection_width: 4 — the number of nonredundant leading partial-remainder digits used for quotient prediction   # p.108
slots:
  none
parameters: four nonredundant leading partial-remainder positions; partial remainder up to 2048 positions; one signed quotient digit selected per loop iteration   # p.108
results:
| metric | value | unit | technology / device | baseline | condition | page |
| divider size relation | slightly more complex than the divider’s multiplier | qualitative | UNKNOWN; 1989 | on-line multiplier | programmable add/subtract/multiply/divide/remainder circuit | p.109 |
errors_and_checks: exact signed-digit division is described; no numerical-error or fault-detection result is reported. # p.108–109
conditions: Startup shifts divisor digits until the four-bit known part D satisfies the printed convergence test; the comment gives 7 < divisor < 16 and 8 ≤ D < 15. # p.108
conditions: The algorithm assumes a positive divisor, and divisor/result SBDs are complemented when the divisor is negative. # p.108
evidence: §B.3; Fig. 7 and the listed division algorithm, p.108–109.

### online_arithmetic_unit  (role: proposes)
mechanism: One programmable circuit combines the on-line adder, multiplier, divider, and switches. Two input FIFOs align operands and wait for unavailable data, while a backward request token regulates the serial flow and permits shared operands in expression pipelines. # p.109
choices:
  radix: 2   # p.106
  residual_form: signed_digit   # p.106–109
new_choices:
  operation_set: {add, subtract, multiply, divide, remainder} — operations selected by the programmable unit   # p.109
  flow_control: backward_request_token — token-driven demand regulation of operand data   # p.108–109
slots:
  none
parameters: operands up to 600 decimal digits; fewer than 10 gates traversed per cycle; assumed 3 ns gate delay   # p.109
results:
| metric | value | unit | technology / device | baseline | condition | page |
| combinational depth per cycle | less than 10 | gates | UNKNOWN; 1989 | UNKNOWN | 64-digit SBD multiplier implementation | p.109 |
| assumed gate delay | 3 | ns per gate | UNKNOWN; 1989 | UNKNOWN | frequency estimate | p.109 |
| expected frequency | 30 | MHz | UNKNOWN; 1989 | UNKNOWN | derived in the document from 3 ns per gate | p.109 |
| expected throughput | 30 million | digits of result per second | UNKNOWN; 1989 | UNKNOWN | enough circuits pipelined; numbers up to 600 decimal digits | p.109 |
errors_and_checks: none
conditions: Throughput is stated to be almost independent of expression complexity when enough circuits are pipelined and operands fit within 600 decimal digits. # p.109
conditions: Input FIFOs delay operands for availability and weight alignment during addition/subtraction. # p.109
evidence: §C–D; Figs. 8–11, p.109–110.

## new_families
none

## space_gaps
* generalized_signed_digit.digit_encoding lacks the document’s explicit negative/positive two-bit SBD encoding. # p.106
* online_arithmetic_unit lacks choices for the supported operation set and token-based demand flow control. # p.109
* online_msdf lacks a choice for the four-digit nonredundant quotient-selection window. # p.108

## open_questions
* The printed formula for the SBD pair and the printed examples appear inconsistent about which member is the negative bit. # p.106
* The document does not state the divider’s numerical online delay. # p.108–109
* The document does not identify the fabrication technology or report measured silicon frequency/power/area. # p.109–110
* The 30 MHz and 30-million-digit/s figures are expectations based on a 3 ns gate delay rather than reported measurements. # p.109
