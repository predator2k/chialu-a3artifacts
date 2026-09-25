---
handle: schmookler_1968
citation: Schmookler, "High-Speed Binary-to-Decimal Conversion", IEEE Transactions on Computers, 1968
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [binary_fixed_point, binary_floating_point, bcd]
authority: landmark
pages_read: 506-508 / 3
---

## summary
The document proposes binary-to-BCD conversion by scaling a binary value to a fraction and iteratively multiplying it by 10, 100, or 1000. Shift/add constant multiplication produces one to three decimal digits per operation, while hardware compensation preserves exact fixed-point integer conversion.

## families
### binary_decimal_conversion  (role: proposes)
mechanism: A binary number is scaled to a fraction and repeatedly multiplied by a power of ten. The integer portion from each iteration supplies the next decimal digit or digit group, while the fractional portion feeds the next iteration. Multiplication by 10 uses shifted 8f and 2f operands with one addition. Multiplication by 100 or 1000 uses multiple shifted terms; a carry-save adder places those terms before the main adder so one iteration still takes one operation time. Binary overflow groups are decoded to radix 100 and then radix 10 for BCD output. # pp.506-507
choices:
  direction: bin_to_dec   # p.506
  structure: constant_multiply   # pp.506-507
  digits_per_step: 1 for ×10, 2 for ×100, or 3 for ×1000   # pp.506-507
new_choices:
  intermediate_radix: {10, 100, 1000} — selects the power of ten multiplied per iteration and the number of decimal digits developed   # pp.506-507
  carry_save_front_end: Bool — allows the shifted terms for ×100 or ×1000 to enter the main adder within one operation time   # p.507
  overflow_decoder_radix: {10, 100_then_10} — selects direct digit extraction or staged decoding of binary overflow groups   # p.507
  exact_integer_compensation: Bool — adds a hardware correction for scaling/truncation errors before retaining the decimal integer   # p.508
slots: none
parameters: ×10 produces 1 digit per operation; ×100 produces 2 digits per operation with a carry-save adder; ×1000 produces 3 digits per operation with a carry-save adder; the ×1000 decoder takes 2 operation times after the last overflow; the ×100 decoder takes 1 operation time; the exact-integer example uses a 12-bit fixed-point word, retains 16 product/adder bits, and develops 4 decimal digits   # pp.506-508
results:
| metric | value | unit | technology / device | baseline | condition | page |
| conversion rate | 1 | decimal digit/operation | UNKNOWN | repeated doubling at 1 bit/operation | multiplication by 10 using 8f+2f | p.506 |
| speed improvement | more than 3 | times | UNKNOWN | Couleur doubling method | multiplication by 10 | p.506 |
| conversion rate | 3 | decimal digits/operation | UNKNOWN | multiplication by 10 | multiplication by 1000 with a carry-save adder | p.507 |
| speed improvement | 3 | times | UNKNOWN | multiplication by 10 | multiplication by 1000 with a carry-save adder | p.507 |
| speed improvement | nearly 10 | times | UNKNOWN | Couleur doubling method | multiplication by 1000 with a carry-save adder | p.507 |
| conversion rate | 2 | decimal digits/operation | UNKNOWN | multiplication by 10 | multiplication by 100 with a carry-save adder | p.507 |
| speed improvement | 2 | times | UNKNOWN | multiplication by 10 | multiplication by 100 with a carry-save adder | p.507 |
| decoder circuitry | about one-third | circuitry | UNKNOWN | multiplication-by-1000 decoder | multiplication-by-100 decoder | p.507 |
| decoder latency | 2 | operation times | UNKNOWN | UNKNOWN | radix-100 then radix-10 decoding for multiplication by 1000 | p.507 |
| decoder latency | 1 | operation time | UNKNOWN | UNKNOWN | multiplication-by-100 decoder | p.507 |
| maximum product-truncation error | -0.15 | decimal integer units | UNKNOWN | 12-bit truncation gives -2.44 | 16 product bits retained in the four-digit example | p.508 |
| adder-extension error | 0 | decimal integer units | UNKNOWN | 12-bit adder range 0 to -0.488 | adder extended by 4 bits | p.508 |
| total uncorrected error | -0.15 to +0.68 | decimal integer units | UNKNOWN | UNKNOWN | 12-bit/four-digit example using scaling constant 1678 | p.508 |
| corrected final error | +0.09 < Ef < +0.92 | decimal integer units | UNKNOWN | uncorrected range -0.15 to +0.68 | correction 0010 added to the low-order 4 bits of the 16-bit fraction | p.508 |
errors_and_checks: Exact fixed-point conversion requires the total scaling/truncation/adder error to remain within an interval that cannot change the retained integer. In the worked example, extending the product and adder to 16 bits and adding correction 0010 changes the error range to +0.09 < Ef < +0.92, so the retained four-digit integer is correct. No fault-detection mechanism is reported.   # p.508
conditions: Multiplication by 1000 reaches three digits per operation only when a carry-save adder combines the shifted operands before the main adder. Multiplication by 100 is useful when decoder circuitry must be reduced or the word length is fairly short. Conversion-only acceleration is not worthwhile when scaling/rounding/unpacking/leading-zero suppression/editing dominate total time, and peripheral-processor conversion need only match attached printer speed.   # pp.507-508
evidence: “Binary-to-Decimal Conversion Theory” and “Binary-to-Decimal Converters,” pp.506-507; Figs. 1-3, p.507; “Integer Conversion,” pp.507-508; “Improving the Overall Problem,” p.508.

## new_families
none

## space_gaps
* `binary_decimal_conversion` lacks an `intermediate_radix` choice for the document’s ×10/×100/×1000 alternatives.   # pp.506-507
* `binary_decimal_conversion` lacks a carry-save-front-end choice or slot for combining three shifted constant-multiple terms in one operation time.   # p.507
* `binary_decimal_conversion` lacks choices for overflow-group decoding structure and decoder latency.   # p.507
* `binary_decimal_conversion` lacks an exact-integer scaling/truncation compensation choice.   # p.508

## open_questions
* The document names a carry-save adder but does not specify its compressor organization or circuit implementation.   # p.507
* The document does not report a technology node, device, area, power, clock period, or absolute conversion latency.   # pp.506-508
