---
handle: schwarz_2009
citation: Schwarz, Kapernick, Cowlishaw, "Decimal Floating-Point Support on the IBM System z10 Processor", IBM Journal of Research and Development, 2009
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [decimal32, decimal64, decimal128, packed_bcd]
authority: landmark
pages_read: 10 / 10
---

## summary
The paper describes the IBM System z10 hardware decimal floating-point unit, which supports IEEE 754-2008 decimal floating point and traditional z/Architecture decimal fixed point. The shared decimal dataflow contains DPD/BCD codecs, a pipelined 36-digit adder, digit-serial multiplication, prescaled radix-10 division, and residue-3 checking.

## families
### commercial_decimal_fpu  (role: instantiates)
mechanism: The separate DFU derives from the POWER6 DFU and adds interfaces/controls for z/Architecture decimal fixed-point instructions. A 144-bit significand dataflow shares a two-cycle 36-digit adder across decimal floating-point and fixed-point operations; floating-point operations add DPD expansion/compression, alignment, rounding, and exception processing. # p.4:2, p.4:6
choices:
  implementation: hardware_dfu  # p.4:2
  datapath_width_digits: 36  # p.4:2
  shared_with_binary_fpu: false  # p.4:6
new_choices:
  decimal_operation_set: dfp_and_decimal_fixed — whether one DFU supports both IEEE DFP and traditional decimal fixed-point instructions  # p.4:2
slots:
  significand_adder: bcd_direct_addition [digit_code=bcd8421]  # p.4:2–4:3
  multiplier: iterative_decimal_multiplication [multiple_set=double_quintuple_only, digits_per_cycle=1]  # p.4:3–4:4
  divider: decimal_digit_recurrence [quotient_digit_set=nonredundant_0_9, divisor_prescaling=true]  # p.4:4
parameters: 144-bit significand dataflow; 36-digit adder divisible into two 18-digit adders; adder latency 2 cycles and II 1; 54 DFP instructions, 13 decimal fixed-point instructions, and 4 hardware-assist instructions  # p.4:2
results:
| metric | value | unit | technology / device | baseline | condition | page |
| adder latency | 2 | cycles | IBM System z10; node UNKNOWN; 2009 | UNKNOWN | one 36-digit or two 18-digit modes | p.4:2 |
| adder throughput | 1 | add/cycle | IBM System z10; node UNKNOWN; 2009 | UNKNOWN | pipelined operation | p.4:2 |
errors_and_checks: Parity checks interfaces with other units, and residue-3 checking protects the significand dataflow from transient failures; quantitative coverage and false-alarm behavior are not reported. # p.4:3
conditions: The dedicated DFU places decimal macros together but incurs communication delay to central core units. # p.4:4
evidence: Figure 1 and “Decimal floating-point unit hardware,” “Basic DFU dataflow,” and “Overview of z10 DFP hardware,” p.4:2–4:6.

### decimal_fp_addition  (role: instantiates)
mechanism: Addition separates execution into equal-exponent, shift-larger-operand-only, and shift-both-operands cases. Operands expand from DPD to BCD, pass through the two-cycle decimal adder, undergo optional alignment/normalization/rounding, and compress back to DPD. # p.4:3
choices:
  alignment: full_shifter  # p.4:2–4:3
  format: decimal64, decimal128 [outside domain]  # p.4:2
new_choices:
  none
slots:
  significand_adder: bcd_direct_addition [digit_code=bcd8421]  # p.4:2–4:3
parameters: 16-digit and 34-digit arithmetic formats; equal-exponent basic sequence uses 4 internal execution cycles before dispatch-overlap constraints  # p.4:2–4:3, p.4:5
results:
| metric | value | unit | technology / device | baseline | condition | page |
| floating-point add/subtract latency | 12–28 | cycles | IBM System z10; node UNKNOWN; 2009 | UNKNOWN | double-word operands | p.4:6 |
| floating-point add/subtract latency | 16–31 | cycles | IBM System z10; node UNKNOWN; 2009 | UNKNOWN | quadword operands | p.4:6 |
errors_and_checks: Rounding adds 1 at the least-significant decimal digit; underflow/overflow and carryout can extend execution. # p.4:3, p.4:5–4:6
conditions: Equal exponents, most-significant-digit sum below 9, and nonsubnormal inputs enable the common-case early-end path; back-to-back operations still have a minimum latency of 12 cycles because the dispatch unit requires eight-cycle advance notice. # p.4:5
evidence: “DFP addition,” “DFP addition case 1,” and Table 1, p.4:3, p.4:5–4:6.

### bcd_direct_addition  (role: instantiates)
mechanism: The BCD adder operates either as one 36-digit unit or as two independent 18-digit units. Decimal fixed-point addition loads packed-BCD operands, aligns and zeroes the sign digit, performs magnitude addition/subtraction, and may post-complement the result. # p.4:2, p.4:5
choices:
  digit_code: bcd8421  # p.4:2–4:3
new_choices:
  none
slots:
  none
parameters: 36 digits or 2 × 18 digits; latency 2 cycles; II 1; fixed-point operands up to 31 digits plus sign  # p.4:2, p.4:4
results:
| metric | value | unit | technology / device | baseline | condition | page |
| fixed-point add/subtract latency | 7 | cycles | IBM System z10; node UNKNOWN; 2009 | UNKNOWN | operands of 8 bytes or less | p.4:5–4:6 |
| fixed-point add/subtract latency | 9 | cycles | IBM System z10; node UNKNOWN; 2009 | UNKNOWN | operands longer than 8 bytes | p.4:5–4:6 |
errors_and_checks: none
conditions: Fixed-point addition omits DPD expansion/compression and floating-point rounding cycles. # p.4:5
evidence: “Basic DFU dataflow,” “Decimal fixed-point operations,” and Table 1, p.4:2, p.4:4–4:6.

### iterative_decimal_multiplication  (role: instantiates)
mechanism: Multiplication processes one multiplier digit at a time. A doubler/quintupler produces 1×, 2×, 5×, and 10× easy multiples, and addition/subtraction forms other digit multiples. Sixteen-digit multiplication pairs partial products and alternates pair formation with running-sum accumulation; 34-digit multiplication uses the full adder on alternate cycles. # p.4:3–4:4
choices:
  multiple_set: double_quintuple_only  # p.4:3
  multiplier_digit_recoding: none  # p.4:3
  digits_per_cycle: 1  # p.4:3–4:4
new_choices:
  none
slots:
  accumulator: linear_chain  # p.4:4
parameters: 16-digit mode creates one 1 × 16-digit partial product per cycle; 34-digit mode creates one 1 × 34-digit partial product every other cycle  # p.4:4
results:
| metric | value | unit | technology / device | baseline | condition | page |
| floating-point multiplication latency | 16–55 | cycles | IBM System z10; node UNKNOWN; 2009 | UNKNOWN | double-word operands | p.4:6 |
| floating-point multiplication latency | 17–104 | cycles | IBM System z10; node UNKNOWN; 2009 | UNKNOWN | quadword operands | p.4:6 |
errors_and_checks: none
conditions: Sixteen-digit operation uses two independent 18-digit adders, while 34-digit operation retains one 36-digit adder and halves the partial-product issue rate. # p.4:3–4:4
evidence: “DFP multiplication” and Table 1, p.4:3–4:4, p.4:6.

### decimal_digit_recurrence  (role: instantiates)
mechanism: Division uses nonrestoring radix-10 recurrence after multiplying dividend/divisor by a two-digit reciprocal approximation. Prescaling constrains the divisor so the next quotient digit is the most significant partial-remainder digit. Two partial remainders let stored multiples 1–5 also produce multiples 6–9. # p.4:4
choices:
  quotient_digit_set: nonredundant_0_9  # p.4:4
  digit_split: none  # p.4:4
  divisor_prescaling: true  # p.4:4
new_choices:
  high_multiple_generation: secondary_partial_remainder — PA/PB recurrences obtain multiples 6–9 using the prior quotient guess plus or minus 1  # p.4:4
slots:
  digit_select: qds_table  # p.4:2, p.4:4
parameters: radix 10; two-digit reciprocal approximation; approximately 19 prescaling cycles; 4 cycles per quotient digit; latency approximately 19 + N × 4 cycles plus rounding  # p.4:4
results:
| metric | value | unit | technology / device | baseline | condition | page |
| floating-point division latency | 16–119 | cycles | IBM System z10; node UNKNOWN; 2009 | UNKNOWN | double-word operands | p.4:6 |
| floating-point division latency | 17–193 | cycles | IBM System z10; node UNKNOWN; 2009 | UNKNOWN | quadword operands | p.4:6 |
errors_and_checks: none
conditions: Prescaling removes repeated table consultation, but each digit still requires multiple selection and a two-cycle subtraction. # p.4:4
evidence: “DFP division” and Table 1, p.4:4, p.4:6.

### decimal_encoding_codec  (role: instantiates)
mechanism: Register/memory significands use DPD encoding. The du10to3 macro expands DPD to BCD before arithmetic, and du3x10 compresses the BCD result back to DPD before FPR writeback. # p.4:2–4:3
choices:
  significand_encoding: dpd  # p.4:2
  codec_placement: inside_operation  # p.4:3
new_choices:
  none
slots:
  none
parameters: decimal32, decimal64, and decimal128 storage formats; arithmetic only on 16-digit and 34-digit significands  # p.4:2
results: none
errors_and_checks: none
conditions: Floating-point operations require codec cycles, while packed-BCD fixed-point operations do not. # p.4:5–4:6
evidence: “Basic DFU dataflow,” “DFP addition,” and “Overview of z10 DFP hardware,” p.4:2–4:3, p.4:6.

### residue  (role: instantiates)
mechanism: Residue-3 checking protects the decimal significand dataflow against transient failures, while parity protects interfaces to other units. # p.4:3
choices:
  modulus: 3  # p.4:3
new_choices:
  none
slots:
  none
parameters: UNKNOWN
results: none
errors_and_checks: The stated fault model is transient failure in the significand dataflow; detection coverage, alias rate, comparison point, and false-alarm behavior are UNKNOWN. # p.4:3
conditions: The paper does not describe the residue generator or comparator implementation. # p.4:3
evidence: “Basic DFU dataflow,” p.4:3.

## new_families
none

## space_gaps
* `decimal_fp_addition.format` needs a set-valued domain because one implementation supports both `decimal64` and `decimal128`. # p.4:2
* `decimal_digit_recurrence` lacks a choice for the dual-partial-remainder technique used to generate quotient multiples 6–9 from stored multiples 1–5. # p.4:4
* `commercial_decimal_fpu` lacks a choice distinguishing DFP-only hardware from a shared DFP/decimal-fixed-point unit. # p.4:2

## open_questions
* The paper does not state the duaddr carry scheme or decimal-correction placement. # p.4:2–4:3
* Table 1 does not map each multiplication/division latency endpoint to a specific significant-digit count, rounding case, or exception case. # p.4:6
* The residue-3 checker’s granularity/generator/comparison point and quantitative fault coverage remain unspecified. # p.4:3
