---
handle: svoboda_1969
citation: Svoboda, "Decimal Adder with Signed Digit Arithmetic", IEEE Transactions on Computers, 1969
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [decimal_signed_digit, conventional_decimal]
authority: landmark
pages_read: 4 / 4
---

## summary
The document proposes a carry-free decimal adder whose digits use the redundant set {-6,...,+6} and a 5-bit binary code Xi=3xi. The same adder converts conventional decimal numbers to signed-digit form and converts signed-digit results back through repeated filtering additions.

## families
### redundant_decimal_addition  (role: proposes)
mechanism: Each decimal position accepts two signed digits and two transfers from the preceding position. The position produces one signed result digit and independent additive/subtractive transfers for the next position, so transfers do not propagate between positions. Each signed digit xi is encoded by the 5-bit character (edcba)i with Xi=3xi for xi≥0 and Xi-31=3xi for xi<0. Binary adders and Boolean networks compute the digit and transfers. # pp.212-214
choices:
  digit_set: svoboda_signed_digit   # p.212
  operands_redundant: both   # p.213
  final_conversion: repeated_addition_filter [outside domain]   # p.215
new_choices:
  digit_encoding: five_bit_Xi_equals_3xi_mod31 — A signed decimal digit is encoded as a 5-bit character, with complementary characters negating the digit.   # pp.212-213
  transfer_form: independent_add_and_subtract — Each position emits separate +1 and -1 transfers that may coexist and cancel.   # pp.213-214
slots:
  none
parameters: decimal signed digits xi∈{-6,-5,...,+6}; 5-bit characters (edcba)i; two encodings of zero, 00000 and 11111; an n-digit conventional input uses an n+1-place signed-digit adder for possible overflow; pipeline stages/latency/II are UNKNOWN.   # pp.212-214
results:
| metric | value | unit | technology / device | baseline | condition | page |
|---|---:|---|---|---|---|---|
errors_and_checks: The addition and conversion algorithms are exact for the represented integers. Positive digit characters have even parity and negative digit characters have odd parity, but the document specifies no fault model/detection coverage/false-alarm behavior.   # p.213
conditions: Input conversion maps every conventional digit through Table III, adds the constant (4-4), and complements the result for a negative sign. The adder requires n+1 decimal places for input conversion overflow. Output conversion first adds (4-4), then repeatedly adds (0-0) until no digit equals 5; a newly produced 5 always occurs at a higher decimal order. The paper gives a descriptive block diagram rather than a synthesis procedure, technology implementation, or timing/area evaluation.   # pp.213-215
evidence: Table I and §§I-II define the signed-digit code and its properties (pp.212-213); Fig. 1, the Addition Algorithm, and Table II define the adder (pp.213-214); Tables III-IV and §§IV-V define input/output conversion (pp.214-215).

## new_families
none

## space_gaps
* `final_conversion` lacks the documented repeated-addition filtering method used to remove digits equal to 5 before table-based conventional-decimal readout.   # p.215
* `redundant_decimal_addition` lacks a `digit_encoding` choice for the 5-bit Xi=3xi modulo-31 code.   # pp.212-213
* `redundant_decimal_addition` lacks a choice for separate mutually independent positive/negative transfers.   # pp.213-214

## open_questions
* The document does not give a general upper bound on the number of repeated (0-0) additions required by output conversion.   # p.215
* The document does not report technology, area, delay, power, latency, or initiation interval.   # pp.212-215
