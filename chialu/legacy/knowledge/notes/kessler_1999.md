---
handle: kessler_1999
citation: R. E. Kessler, "The Alpha 21264 Microprocessor", IEEE Micro, 1999
actual_citation: same
status: out_of_scope
kind: paper
unit_classes: [BINARY_ALU]
formats: [fp32, fp64]
authority: landmark
pages_read: 24-36 / 13
---

## summary
The article describes the Alpha 21264 processor and identifies its floating-point add/multiply/divide/square-root units, fully pipelined integer multiplier, and combined integer population-count/leading-trailing-zero-count unit (p.30). Table 2 reports issue-to-consumer latencies of 7 cycles for integer multiply, 3 cycles for MVI/PLZ, 4 cycles each for floating-point add/multiply, 12 s-p/15 d-p cycles for divide, and 15 s-p/30 d-p cycles for square root (p.31). The article does not disclose the arithmetic recurrences, encodings, adder topologies, reduction trees, rounding paths, or bit-count structures needed to assign a registry family (p.30; p.31).

## families
none

## new_families
none

## space_gaps
none

## open_questions
* The floating-point adder's path structure/significand adder/normalization/rounding implementation is unspecified (p.30; p.31).
* The floating-point multiplier/divider/square-root architectures and the integer multiplier/PLZ structures are unspecified (p.30; p.31).
