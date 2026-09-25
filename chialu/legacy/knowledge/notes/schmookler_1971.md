---
handle: schmookler_1971
citation: Schmookler, Weinberger, "High Speed Decimal Addition", IEEE Transactions on Computers, 1971
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [bcd]
authority: landmark
pages_read: 862-866 / 5 pages
---

## summary
The paper proposes direct BCD sum/carry generation and decimal carry look-ahead without an intermediate binary sum and decimal correction. The paper describes the eight-digit System/360 Model 195 decimal adder and compares its logic depth/circuitry with correction-based decimal adders and 32-bit binary adders.

## families
### bcd_direct_addition  (role: proposes)
mechanism: The adder divides each BCD digit into bit 1 and bits 8/4/2. Functions K and L generate/propagate the decimal carry, while Boolean expressions directly produce S1/S2/S4/S8 without first producing a binary sum. Digit generate/propagate functions form byte-level look-ahead signals; the implemented eight-digit adder contains four two-digit bytes and produces all sums in six logic levels or less. # pp.862-866
choices:
  digit_code: bcd8421   # p.862
  correction_placement: direct_decimal_carry_logic   # pp.862-863
  carry_scheme: digit_group_lookahead   # pp.863-866
new_choices:
  carry_grouping: two_digit_byte — An eight-bit carry group may contain two adjacent decimal digits; the paper also derives a three-digit straddle grouping.   # p.864
slots:
  digit_adder: none   # pp.862-866
parameters: eight decimal digits; four two-digit bytes; 32 operand bits; six logic levels or less; current-switch circuits with emitter-follower outputs; up to four circuit outputs per wired OR   # pp.864-866
results:
| metric | value | unit | technology / device | baseline | condition | page |
| output-sum logic depth | six or less | logic levels | System/360 Model 195 current-switch circuits; node UNKNOWN; 1971 | none | eight-digit/four-byte decimal adder | p.866 |
| K/L logic depth | two | logic levels | System/360 Model 195 current-switch circuits; node UNKNOWN; 1971 | none | equations (3a)/(3b) | p.866 |
| byte G/P availability | three | logic levels | System/360 Model 195 current-switch circuits; node UNKNOWN; 1971 | none | equations (14a)/(14b) | p.866 |
| correction delay avoided | two additional | logic levels | technology UNKNOWN; 1971 | comparable correction-based decimal adder | direct decimal addition | p.866 |
| circuitry overhead | about 18 | percent | System/360 Model 195 current-switch circuits; node UNKNOWN; 1971 | 32-bit binary adder of the same width | same number of logic levels | p.866 |
| equal-cost logic depth | six instead of five | logic levels | System/360 Model 195 current-switch circuits; node UNKNOWN; 1971 | 32-bit binary adder of the same cost | eight-digit decimal adder | p.866 |
| two-digit adder logic depth | three | logic levels | technology/device UNKNOWN; 1971 | none | another decimal adder based on the paper's principles | p.866 |
errors_and_checks: none
conditions: The Boolean simplifications assume valid standard BCD operand digits from zero through nine. # p.863 The direct design requires fewer logic circuits than comparable correction-based decimal adders, while a same-width binary adder requires less circuitry. # p.866 Decimal subtraction requires a 9's-complement generator, which the paper states adds little complexity. # p.866
evidence: Introduction and one-digit equations (1)-(10), pp.862-863; generalized-radix carry equation (11), p.863; Table I and Figs. 1-3, pp.864-865; implementation depths and comparisons, p.866.

## new_families
none

## space_gaps
* `bcd_direct_addition` lacks a carry-grouping choice for `two_digit_byte` versus `three_digit_straddle`. # p.864
* `bcd_direct_addition.slot digit_adder` cannot represent the paper's direct decimal sum network, which does not instantiate a listed binary-adder family. # pp.862-866

## open_questions
* The paper reports relative circuitry but no absolute circuit count or physical area. # p.866
* The paper mentions a three-level two-digit adder without providing its detailed implementation. # p.866
