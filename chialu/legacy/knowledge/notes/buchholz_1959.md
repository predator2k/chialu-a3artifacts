---
handle: buchholz_1959
citation: Buchholz, "Fingers or Fists? (The Choice of Decimal or Binary Representation)", Communications of the ACM, 1959
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, other]
formats: [binary, decimal, binary-coded decimal, alphanumeric]
authority: landmark
pages_read: 9 / 9 (pp.3-11)
---

## summary
The paper compares binary/decimal representation and concludes that high-performance general-purpose computers benefit from binary addressing, binary floating-point arithmetic, decimal data arithmetic, and dedicated conversion instructions. # pp.3,11
The paper also quantifies representation efficiency and explains a table-based translation between two decimal digit codes. # pp.5-9

## families
### binary_decimal_conversion  (role: instantiates)
mechanism: IBM STRETCH provides dedicated binary-decimal conversion instructions so decimal input/output can use the high-speed binary arithmetic unit without requiring all data arithmetic to use binary representation. The paper does not disclose the conversion recurrence or circuit structure. # p.11
choices:
  direction: both   # p.11
new_choices:
  none
slots:
  none
parameters: widths, digits per step, structure, latency cycles, and II are UNKNOWN   # p.11
results: none
errors_and_checks: none
conditions: Conversion time may be negligible when extensive computation operates on little input/output data, but conversion can become a major burden when few arithmetic operations process large volumes of decimal input/output. # pp.4,7
evidence: Abstract; §§3,10, pp.3,7,11

### decimal_encoding_codec  (role: compares)
mechanism: The paper compares a 5-bit 2-out-of-5 decimal digit code with a 4-bit code using 0001 through 1001 for digits 1 through 9 and 1010 for 0. Translation uses the incoming 5-bit code as an index into a 32-entry table containing the corresponding 4-bit code or 1111 for an invalid input. # pp.8-9
choices:
  significand_encoding: {2-out-of-5, 4-bit codes 0001 to 1001 and 1010 for 0} [outside domain]   # p.8
new_choices:
  translation_method: table_lookup — selects a stored output code by using the input code as an address offset   # pp.8-9
slots:
  none
parameters: input code 5 bits; output code 4 bits; table 32 entries; example memory word 64 bits; output cells 4 bits   # pp.8-9
results:
| metric | value | unit | technology / device | baseline | condition | page |
| decimal digit code width | 5 | bits | UNKNOWN; 1959 | 4-bit code | 2-out-of-5 code | p.8 |
| decimal digit code width | 4 | bits | UNKNOWN; 1959 | 5-bit 2-out-of-5 code | codes 0001-1001 and 1010 | p.8 |
errors_and_checks: The 2-out-of-5 code permits checking for single and common multiple errors. An invalid 5-bit input selects 1111, which is not a valid output digit code. # pp.8-9
conditions: Direct table translation depends on accepting any input bit pattern as an address. Decimal addressing makes fine-grained table cells impractical because higher address digits advance by ten rather than by powers of two. # p.9
evidence: Figure 2 and §§6-7, pp.8-9

## new_families
### dual_base_arithmetic_system  (domain: decimal: decimal misc, closest: commercial_decimal_fpu, why_not: commercial_decimal_fpu does not represent the paper's division of binary addressing/floating-point work, decimal data arithmetic, and conversion across separate units)
mechanism: IBM STRETCH combines binary addressing with a binary arithmetic unit for address manipulation and high-speed floating-point arithmetic. A separate decimal arithmetic unit operates directly on binary-coded decimal or alphanumeric data, while dedicated conversion instructions connect decimal input/output with binary computation. # pp.7,11
choices:
  address_base: {binary, decimal}   # pp.8-11
  arithmetic_unit_composition: {binary_only, decimal_only, separate_binary_and_decimal}   # pp.7,11
  decimal_handling: {conversion_only, direct_decimal_unit, both}   # pp.7,11
results:
| metric | value | unit | technology / device | baseline | condition | page |
| decimal storage/switching requirement | 1.204 | times | UNKNOWN; 1959 | binary representation | minimum 4-bit decimal digit code at equal information content | p.5 |
| theoretical decimal storage efficiency | 83 | % | UNKNOWN; 1959 | full bit utilization | 4-bit decimal digit code | p.5 |
| binary representation efficiency | 90 | % | UNKNOWN; 1959 | information content | N = 150, 8-bit representation | p.5 |
| decimal representation efficiency | 60 | % | UNKNOWN; 1959 | information content | N = 150, 3 decimal digits or 12 bits | p.5 |
| decimal efficiency relative to binary | 67 | % | UNKNOWN; 1959 | binary representation | N = 150 | p.5 |
| binary speed advantage | at least 20.4 | % | UNKNOWN; 1959 | corresponding decimal computer | storage devices limited by bit transmission rate | p.7 |
| decimal scaling-step coarseness | 3.3 | times | UNKNOWN; 1959 | binary power-of-two shifting | shifting by powers of ten | p.7 |
| decimal inherent performance loss | at least 20 to 40 | % | UNKNOWN; 1959 | binary number system | overall analytical comparison | p.11 |
evidence: Abstract; §§1-3,5-7,10; Figures 1a-1b; pp.3-11

## space_gaps
* decimal_encoding_codec.significand_encoding lacks the 2-out-of-5 code and the 4-bit 0001-1001/1010 digit code. # p.8
* decimal_encoding_codec lacks a choice for table-based translation and invalid-code signaling. # pp.8-9
* The vocabulary lacks a family for a system containing separate binary/decimal arithmetic units joined by dedicated conversion instructions. # pp.7,11

## open_questions
* The paper does not identify the circuitry, algorithm, widths, or latency of the IBM STRETCH conversion instructions. # p.11
* The paper does not identify the decimal digit code or adder structure used by the IBM STRETCH decimal arithmetic unit. # p.11
