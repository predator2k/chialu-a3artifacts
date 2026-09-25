---
handle: thompson_2004
citation: Thompson, Karra, Schulte, "A 64-bit Decimal Floating-Point Adder", IEEE Computer Society Annual Symposium on VLSI (ISVLSI), 2004
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [decimal64, bcd, excess-3]
authority: landmark
pages_read: 2 / 2
---

## summary
The paper presents a draft IEEE-754-compliant decimal floating-point adder for addition/subtraction on 64-bit operands with 16-digit significands. §1 The datapath aligns BCD significands, converts them to excess-3, performs a 76-bit binary addition with parallel flag generation, corrects the result, and rounds and re-encodes it. §2 A five-stage implementation has an estimated area of 0.199 mm2 and critical-path delay of 0.98 ns in a 0.11 micron CMOS standard cell library. §3

## families
### decimal_fp_addition  (role: proposes)
mechanism: The operands are unpacked into signs, 10-bit biased binary exponents, and 16-digit BCD significands, then ordered by exponent and aligned to a common exponent. §2 The significands are converted to excess-3, conditionally inverted for subtraction, and passed through a 76-bit binary adder with parallel flag generation. §2 A correction unit uses the flags/effective operation/digit carry-outs before shifting, rounding, sign selection, and IEEE-754 decimal encoding. §2
choices:
  format: decimal64   # §1
new_choices:
  internal_digit_encoding: excess-3 — encoding used for significand addition and correction   # §2
  correction_basis: flags_effective_operation_digit_carry_outs — signals controlling post-addition correction   # §2
slots:
  significand_adder: bcd_direct_addition [digit_code=excess3]   # §2
parameters: 64-bit operands; 16-digit significands; 10-bit biased binary exponents; 76-bit binary adder; pipeline depth 1 to 5; one complete result per cycle   # §1, §2, §3
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area | 0.148 | mm2 | LSI Logic’s Gflxp 0.11 micron CMOS standard cell library; 2004 | none | pipeline depth 1; optimized for delay | §3 |
| critical path delay | 3.83 | ns. | LSI Logic’s Gflxp 0.11 micron CMOS standard cell library; 2004 | none | pipeline depth 1; no pipelining | §3 |
| latency | 3.83 | ns. | LSI Logic’s Gflxp 0.11 micron CMOS standard cell library; 2004 | none | pipeline depth 1 | §3 |
| area | 0.154 | mm2 | LSI Logic’s Gflxp 0.11 micron CMOS standard cell library; 2004 | none | pipeline depth 2; optimized for delay | §3 |
| critical path delay | 2.10 | ns. | LSI Logic’s Gflxp 0.11 micron CMOS standard cell library; 2004 | none | pipeline depth 2 | §3 |
| latency | 4.20 | ns. | LSI Logic’s Gflxp 0.11 micron CMOS standard cell library; 2004 | none | pipeline depth 2 | §3 |
| area | 0.169 | mm2 | LSI Logic’s Gflxp 0.11 micron CMOS standard cell library; 2004 | none | pipeline depth 3; optimized for delay | §3 |
| critical path delay | 1.46 | ns. | LSI Logic’s Gflxp 0.11 micron CMOS standard cell library; 2004 | none | pipeline depth 3 | §3 |
| latency | 4.38 | ns. | LSI Logic’s Gflxp 0.11 micron CMOS standard cell library; 2004 | none | pipeline depth 3 | §3 |
| area | 0.174 | mm2 | LSI Logic’s Gflxp 0.11 micron CMOS standard cell library; 2004 | none | pipeline depth 4; optimized for delay | §3 |
| critical path delay | 1.17 | ns. | LSI Logic’s Gflxp 0.11 micron CMOS standard cell library; 2004 | none | pipeline depth 4 | §3 |
| latency | 4.68 | ns. | LSI Logic’s Gflxp 0.11 micron CMOS standard cell library; 2004 | none | pipeline depth 4 | §3 |
| area | 0.199 | mm2 | LSI Logic’s Gflxp 0.11 micron CMOS standard cell library; 2004 | none | pipeline depth 5; optimized for delay | §3 |
| critical path delay | 0.98 | ns. | LSI Logic’s Gflxp 0.11 micron CMOS standard cell library; 2004 | none | pipeline depth 5 | §3 |
| latency | 4.90 | ns. | LSI Logic’s Gflxp 0.11 micron CMOS standard cell library; 2004 | none | pipeline depth 5 | §3 |
errors_and_checks: The design claims compliance with the current draft revision of IEEE-754 and was functionally tested on corner cases and over one million pseudo-random test cases; no numerical error bound or coverage result is reported.   # §1, §3
conditions: Pipeline depth can be selected to match system cycle time, with greater depth increasing area/latency while reducing critical-path delay. §2, §3 The design supports 64-bit decimal floating-point addition/subtraction and is stated to be extendable to 32-bit and 128-bit formats. §1
evidence: §1; §2 and Figure 1; §3 and Table 1; §4

### bcd_direct_addition  (role: instantiates)
mechanism: Aligned standard-BCD significands are converted to excess-3 before addition. §2 Subtraction conditionally inverts the appropriate operand, while the sticky bit is expanded into a 4-bit digit. §2 A 76-bit binary adder produces the sum while flag bits are generated in parallel, and a following unit corrects the sum from the flags/effective operation/digit carry-outs. §2
choices:
  digit_code: excess3   # §2
new_choices:
  correction_control: flags_effective_operation_digit_carry_outs — control inputs used by the correction unit   # §2
slots:
  digit_adder: UNKNOWN   # §2
parameters: 16-digit significands; 76-bit binary adder; 4-bit expanded sticky digit   # §2
results:
| metric | value | unit | technology / device | baseline | condition | page |
| none | UNKNOWN | UNKNOWN | UNKNOWN; 2004 | none | no isolated significand-adder result reported | §3 |
errors_and_checks: none
conditions: The correction follows the binary addition, and a corrected result exceeding sixteen digits is shifted and rounded. §2
evidence: §2 and Figure 1

### decimal_encoding_codec  (role: instantiates)
mechanism: Each IEEE-754 decimal operand is decoded inside the operation into a sign, a 10-bit biased binary exponent, and a 16-digit BCD significand. §2 The arithmetic path converts BCD to excess-3, and the final path converts the corrected excess-3 result to IEEE-754 decimal encoding. §2
choices:
  codec_placement: inside_operation   # §2
new_choices:
  internal_arithmetic_encoding: excess-3 — transient digit encoding used between operand decoding and result encoding   # §2
slots:
  none
parameters: 64-bit IEEE-754 decimal operands; 10-bit exponent; 16-digit BCD significand   # §1, §2
results:
| metric | value | unit | technology / device | baseline | condition | page |
| none | UNKNOWN | UNKNOWN | UNKNOWN; 2004 | none | no isolated codec result reported | §3 |
errors_and_checks: none
conditions: The document does not identify the specific IEEE-754 decimal interchange encoding used at the input/output boundary. §2
evidence: §2 and Figure 1

### parallel_prefix  (role: compares)
mechanism: A 64-bit Kogge-Stone binary adder is synthesized under the same design constraints and standard cell library as the decimal floating-point adder for an area/delay comparison. §3
choices:
  topology: kogge_stone   # §3
new_choices:
  none
slots:
  none
parameters: 64-bit binary adder   # §3
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area | 0.063 | mm2 | LSI Logic’s Gflxp 0.11 micron CMOS standard cell library; 2004 | none | same design constraints and standard cell library | §3 |
| critical path delay | 0.60 | ns | LSI Logic’s Gflxp 0.11 micron CMOS standard cell library; 2004 | none | same design constraints and standard cell library | §3 |
errors_and_checks: none
conditions: The Kogge-Stone result is for a binary adder rather than a decimal floating-point adder, so the comparison does not hold functionality constant. §3
evidence: §3, text preceding Table 1

## new_families
none

## space_gaps
* `decimal_fp_addition` lacks a choice for the excess-3 internal significand encoding used by this design. §2
* `decimal_fp_addition` lacks a choice for correction controlled jointly by flags/effective operation/digit carry-outs. §2
* `decimal_encoding_codec` lacks a choice for a transient internal arithmetic encoding distinct from the interchange encoding. §2

## open_questions
* The document does not specify the topology/circuit style of the 76-bit binary adder. §2
* The document does not identify the exact IEEE-754 decimal interchange encoding at the input/output boundary. §2
* The document defers detailed significand-alignment and result-correction techniques to its extended version. §1
* The document does not report pipeline-register locations for pipeline depths 2 through 5. §2, §3
