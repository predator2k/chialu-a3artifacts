---
handle: duale_2007
citation: Duale, Decker, Zipperer, Aharoni, Bohizic, "Decimal Floating-Point in z9: An Implementation and Testing Perspective", IBM Journal of Research and Development, 2007
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [decimal32, decimal64, decimal128, bcd, dpd]
authority: landmark
pages_read: 11 / 11
---

## summary
System z9 implements more than 50 decimal floating-point instructions mainly in millicode, with hardware assists for register access, DPD conversion, and BCD arithmetic (p.217, pp.219-220). Long-format arithmetic takes 100 to 150 cycles for add/subtract, 150 to 200 cycles for multiply, and 350 to 400 cycles for divide (p.221).

## families
### commercial_decimal_fpu  (role: instantiates)
mechanism: System z9 executes DFP instructions mainly in millicode because the DFP standard was unfinished during processor development (p.219). Dedicated milli-ops transfer FPR values, decode/encode DPD fields, and perform register-based BCD add/subtract/multiply/divide (pp.219-220). The BCD arithmetic milli-ops reuse hardware components provided for packed fixed-point decimal instructions (p.220).
choices:
  implementation: millicode_with_assists   # p.219
new_choices:
  none
slots:
  significand_adder: UNKNOWN   # p.220
  multiplier: UNKNOWN   # p.220
  divider: UNKNOWN   # p.220
parameters: More than 50 DFP instructions; short 32-bit/7-digit, long 64-bit/16-digit, and extended 128-bit/34-digit formats; APRR/SPRR execute in 1 cycle, while MPRR/DPRR require multiple cycles (pp.217-218, p.220).
results:
| metric | value | unit | technology / device | baseline | condition | page |
| add/subtract execution time | 100 to 150 | cycles | System z9 / 2007 | pure software: 652 to 1,060 cycles | long 16-digit DFP; approximate and data-dependent | p.221 |
| multiply execution time | 150 to 200 | cycles | System z9 / 2007 | pure software: 4,285 cycles | long 16-digit DFP; approximate and data-dependent | p.221 |
| divide execution time | 350 to 400 | cycles | System z9 / 2007 | pure software: 3,617 cycles | long 16-digit DFP; approximate and data-dependent | p.221 |
| overall speedup | 10 | factor | System z9 / 2007 | pure software implementation | achieved for most tested DFP operations | p.221 |
errors_and_checks: DFP arithmetic is defined as an infinite-precision/unbounded-range intermediate followed by FPCR-selected rounding; additional digits and a sticky bit determine exactness, increment, or truncation (p.218, p.220). A common RefMod was independently cross-checked against decNumber through eDFPcalc (p.222).
conditions: Millicode does not provide full-hardware performance, and the paper projects that a pure hardware implementation could improve performance by another factor of 10 or more (p.219). Execution time depends heavily on operand data, and equal-exponent add/subtract operations use a fast path (p.221).
evidence: DFP implementation and hardware support (pp.219-220); DFP instruction execution (pp.220-221); Table 5 and Performance (p.221).

### decimal_encoding_codec  (role: instantiates)
mechanism: DFP operands reside in FPRs as DPD values and are transferred to MGRs for execution (pp.218-220). EXPDR decodes the exponent, EBCDR decodes the coefficient into BCD, CBCDR encodes a BCD coefficient, and IXPDR inserts the encoded exponent (pp.219-220). Each ten-bit DPD declet represents three decimal digits, compared with 12 bits in BCD (p.218).
choices:
  significand_encoding: dpd   # p.218
  codec_placement: inside_operation   # pp.219-220
new_choices:
  none
slots:
  none
parameters: CF is 5 bits; BXCF is 6/8/12 bits; CCF is 20/50/110 bits for short/long/extended formats; one declet is 10 bits for three decimal digits (p.218).
results:
| metric | value | unit | technology / device | baseline | condition | page |
| codec milli-op latency | 1 | cycle | System z9 / 2007 | UNKNOWN | most EXPDR/IXPDR/EBCDR/CBCDR forms | p.220 |
errors_and_checks: A declet has 1,024 bit strings for 1,000 decimal combinations, which leaves 24 redundant strings (p.218).
conditions: DPD values must normally be decoded before arithmetic and encoded again before delivery; codec milli-op variants combined with shifts/bit masks support all three DFP formats (pp.219-220).
evidence: Table 1 and DPD field descriptions (p.218); Hardware support and DFP instruction execution (pp.219-220).

## new_families
none

## space_gaps
* `commercial_decimal_fpu` lacks a codec slot for the `decimal_encoding_codec` family, although DPD-to-BCD decoding and result encoding are explicit parts of the execution path (pp.219-220).

## open_questions
* The internal microarchitectures used by APRR/SPRR/MPRR/DPRR are not disclosed, so the significand-adder/multiplier/divider slots must remain `UNKNOWN` (p.220).
* The paper does not state the physical decimal datapath width or the operation sequence used for 34-digit extended operands (pp.218-220).
