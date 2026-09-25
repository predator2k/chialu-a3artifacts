---
handle: cowlishaw_2002
citation: Cowlishaw, "Densely Packed Decimal Encoding", IEE Proceedings - Computers and Digital Techniques, 2002
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [bcd, decimal_fp]
authority: landmark
pages_read: 102-104 / 3
---

## summary
The document proposes densely packed decimal encoding, a lossless mapping that compresses three BCD digits into 10 bits while preserving decimal digit boundaries. The encoding supports arbitrary digit lengths through right-aligned one-digit and two-digit subsets and permits hardware conversion with Boolean logic.

## families
### decimal_encoding_codec  (role: proposes)
mechanism: Densely packed decimal partitions each BCD digit into small values 0 through 7 and large values 8 or 9, then uses an equivalent Huffman code to map three 4-bit digits into 10 bits. Indicator bits identify the eight large/small combinations. One-digit and two-digit encodings occupy the rightmost four and seven bits of the same mapping, so zero padding expands the field without re-encoding. Compression and expansion use fixed bit mappings implementable as lookup tables or Boolean gates. # pp.102-104
choices:
  significand_encoding: dpd   # pp.102-104
new_choices:
  codec_implementation: {lookup_table, boolean_logic} — selects software table lookup or hardware Boolean-gate mapping   # p.104
slots:
  none
parameters: three BCD digits / 12 input bits / 10 encoded bits; one-digit subset / 4 bits; two-digit subset / 7 bits; eight large/small digit combinations; 24 unused 10-bit values   # pp.102-104
results:
| metric | value | unit | technology / device | baseline | condition | page |
| compression density | 17% | more compact | UNKNOWN / 2002 | BCD | three decimal digits encoded in 10 bits | p.102 |
| register capacity | 33 digits plus sign and a 4-digit exponent | decimal digits | UNKNOWN / 2002 | 32 BCD digits in the same 128-bit register | compact decimal floating-point representation | p.102 |
| encoded capacity | 38 | decimal digits | UNKNOWN / 2002 | UNKNOWN | 127 encoded bits | p.102 |
| encoded capacity | 71 | decimal digits | UNKNOWN / 2002 | Chen–Ho encoding fits 69 digits in 230 of 237 available significand bits | 237 encoded bits available in a 256-bit register | pp.102-103 |
| unchanged-value range | 0 through 79 | decimal values | UNKNOWN / 2002 | Chen–Ho leaves only 0 through 7 unchanged | right-aligned encoding matches BCD | p.103 |
| unused code space | 24 | 10-bit values | UNKNOWN / 2002 | UNKNOWN | all three digits are large | p.103 |
errors_and_checks: The encoding is lossless; no arithmetic error, fault model, detection coverage, false-alarm behavior, or alias rate is reported.   # p.102
conditions: The encoding retains decimal digit boundaries, which simplifies decimal addition/subtraction/shifting/rounding and character conversion. Arbitrary-length decimal numbers are supported because one-digit and two-digit encodings are subsets of the three-digit encoding. Field expansion requires zero padding rather than re-encoding. The scheme targets compact decimal storage and manipulation where BCD accessibility matters.   # pp.102-103
evidence: Abstract; §§1-3.3; Tables 1-3, pp.102-104

## new_families
none

## space_gaps
* `decimal_encoding_codec` lacks a `codec_implementation` choice for the document's lookup-table and Boolean-logic implementations.   # p.104

## open_questions
* The document suggests that three unused code combinations may encode infinity or NaN, but it does not define such encodings.   # p.103
