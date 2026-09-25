---
handle: chen_ho_1975
citation: Chen, Ho, "Storage-Efficient Representation of Decimal Data", Communications of the ACM, 1975
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [bcd]
authority: landmark
pages_read: p.49-p.52 / 4 pages
---

## summary
The document proposes reversible fixed-length encodings that compress two BCD digits into 7 bits and three BCD digits into 10 bits. The mappings use indicator/detail fields and require only logic, deletions, displacements, and insertions rather than arithmetic. The compression/decompression mechanism can sit between an expanded-BCD arithmetic unit and memory.

## families
### decimal_encoding_codec  (role: proposes)
mechanism: Each BCD digit is divided into a magnitude indicator and detail bits. A Huffman-coded indicator field identifies the locations of digits valued 8 or 9, while a variable-length detail field supplies their values; the two fields combine into a fixed-length code. Two digits map from 8 BCD bits to 7 bits, and three digits map from 12 BCD bits to 10 bits. Encoding and decoding use tests of the BCD indicator bits followed by permutations, deletions, insertions, and fixed fill bits. # p.50-p.52
choices:
  significand_encoding: chen_ho   # p.49-p.52
  codec_placement: arithmetic_memory_interface [outside domain]   # p.52
new_choices:
  block_digits: {2, 3} — number of BCD digits compressed independently into one fixed-length codeword   # p.49-p.52
slots:
  none
parameters: 2 BCD digits/8 input bits/7 encoded bits; 3 BCD digits/12 input bits/10 encoded bits; independent three-digit blocks for long messages   # p.49-p.52
results:
| metric | value | unit | technology / device | baseline | condition | page |
| compression ratio | 8/7 | ratio | UNKNOWN; 1975 | conventional 8-bit BCD representation of two digits | two-digit block encoded in 7 bits | p.50 |
| relative deviation from asymptotic limit | 5.088 | percent | UNKNOWN; 1975 | asymptotic compression limit | two-digit block | p.50 |
| compression ratio | 6/5 | ratio | UNKNOWN; 1975 | conventional 12-bit BCD representation of three digits | three-digit block encoded in 10 bits | p.50, p.51 |
| relative deviation from asymptotic limit | .3422 | percent | UNKNOWN; 1975 | asymptotic compression limit | three-digit block | p.50 |
| unchanged except for removal of a redundant 0 bit | 80 | percent of cases | UNKNOWN; 1975 | conventional BCD bit pattern | two-digit mapping when the second digit is small | p.51 |
| obtained from BCD by simple deletion | 64 | percent of cases | UNKNOWN; 1975 | conventional BCD bit pattern | three-digit mapping when the second and third digits are small | p.51-p.52 |
| storage saving | 20 | percent | UNKNOWN; 1975 | conventional BCD storage | compressed representation at the arithmetic-unit/memory interface | p.52 |
errors_and_checks: Both mappings are unambiguous and reversible. The two-digit mapping preserves the parity of the original BCD digits, while the three-digit mapping has no uniform parity preservation. No fault model, detection coverage, false-alarm behavior, or alias rate is reported. # p.50-p.51
conditions: The mapping targets storage rather than arithmetic performance. Expanded BCD may remain inside the arithmetic unit, with compression used at the memory interface. Independent three-digit blocks keep a long message within 0.34% of the asymptotic minimum. Variable-length encoding by deletion alone is not recommended because decoding is difficult, storage requirements are uncertain, and errors can disrupt the representation. # p.49-p.52
evidence: §2 and Table I on p.49-p.50; §3-§4, Figures 1-2, and Table II on p.50-p.51; §5, Figures 3-4, and Tables III-IV on p.51-p.52; §6 on p.52

## new_families
none

## space_gaps
* `decimal_encoding_codec` lacks a block-size choice for the document's distinct two-digit/three-digit mappings. # p.49-p.52
* `decimal_encoding_codec` lacks a parity-behavior choice: the two-digit mapping preserves parity, while the three-digit mapping does not preserve parity uniformly. # p.51
* `codec_placement` lacks `arithmetic_memory_interface`, which is the placement proposed for expanded BCD arithmetic and compressed storage. # p.52

## open_questions
* The document describes simple/fast/small mapping hardware but reports no gate count, delay, area, power, technology, or implementation measurements. # p.49, p.52
* The document does not specify whether the codec belongs at register read/write, inside an operation, or at a separate memory-controller boundary. # p.52
