---
handle: schwarz_2007
citation: Schwarz, Carlough, "Power6 Decimal Divide", IEEE ASAP, 2007
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [decimal64, decimal128, DPD, BCD]
authority: incremental
pages_read: 1-6 / 6
---

## summary
The paper describes the Power6 decimal floating-point divider, which combines prescaling with maximally redundant radix-10 non-restoring division. The implementation reduces quotient selection to extracting the partial remainder’s most significant digit, avoids stored divisor multiples above 5X through two parallel partial-remainder candidates, and accumulates signed quotient digits on the fly. The paper also compares the implementation with restoring and Newton-Raphson decimal division.

## families
### decimal_digit_recurrence  (role: extends)
mechanism: The divisor and dividend are prescaled so that 1.0 ≤ D′ < 1.1, which permits the most significant partial-remainder digit to select the quotient. Quotient digits are recoded from {-9,…,+9} into {-5,…,+5}. Each iteration calculates PA = P − qD′ and PB = P − (q +/− 1)D′, so multiples 6X through 9X are replaced by a 10-weighted digit and a small signed digit. Decimal on-the-fly correction converts the redundant quotient into a truncated conventional quotient.
choices:
  quotient_digit_set: minimally_redundant_m5_p5   # p.4
  digit_split: none   # p.2
  divisor_prescaling: true   # pp.2-3
new_choices:
  recurrence_style: nonrestoring — distinguishes the implemented recurrence from the restoring methods compared   # pp.1-2
  partial_remainder_candidates: two — PA and PB are calculated to eliminate divisor multiples 6X through 9X   # pp.3-4
  quotient_accumulation: decimal_on_the_fly_correction — selects q, q−1, q′, or q′+1 from quotient/partial-remainder signs   # pp.4-5
slots:
  digit_select: UNKNOWN   # pp.3-4
parameters: radix 10; 16-digit and 34-digit coefficients; 36-digit/144-bit datapath; 2-digit prescaling; 90-entry × 8-bit prescale table; 2-cycle pipelined adder; II 1 for additions; 4 cycles per quotient digit; I is target precision plus 1 iterations   # pp.1,3-5
results:
| metric | value | unit | technology / device | baseline | condition | page |
| prescale-table size | 256 | Bytes | UNKNOWN / Power6 | unprescaled quotient-selection table: 32KB | 90 entries × 8 bits, uncompressed | p.3 |
| operand-prescaling latency | 6 | cycles | UNKNOWN / Power6 | UNKNOWN | one 2-digit prescale per operand | p.3 |
| quotient-selection-table reduction | 32KB to 256 Bytes | printed sizes | UNKNOWN / Power6 | direct maximally redundant quotient selection | 2-digit divisor prescaling | pp.2-3 |
| partial-remainder iteration | 4 | cycles/digit | UNKNOWN / Power6 | one-cycle Qsel variant: 3 cycles/digit | implemented 2-cycle quotient selection | p.5 |
| total delay | 14 + 4I | cycles | UNKNOWN / Power6 | compared methods in Fig. 6 | Power6; I is result digits plus 1 | p.6 |
| decimal64 division latency | 82 | cycles | UNKNOWN / Power6 | Busaba: 207 cycles; Erle 1: 146.4 cycles; Erle 2: 127.4 cycles | 16-digit result; 5GHz 13-FO4 comparison model | p.6 |
| decimal128 division latency | 154 | cycles | UNKNOWN / Power6 | Busaba: 423 cycles; Erle 1: 294 cycles; Erle 2: 257 cycles | 34-digit result; 5GHz 13-FO4 comparison model | p.6 |
| Alt. 1 decimal64 latency | 65 | cycles | UNKNOWN / proposed variant | Power6: 82 cycles | one-cycle quotient selection; 0.25 KB table and 4 registers | p.6 |
| Alt. 1 decimal128 latency | 119 | cycles | UNKNOWN / proposed variant | Power6: 154 cycles | one-cycle quotient selection; 0.25 KB table and 4 registers | p.6 |
| Alt. 2 decimal64 latency | 48 | cycles | UNKNOWN / proposed variant | Power6: 82 cycles | redundant adder; 0.25 KB table, 9 registers, and an adder | p.6 |
| Alt. 2 decimal128 latency | 84 | cycles | UNKNOWN / proposed variant | Power6: 154 cycles | redundant adder; 0.25 KB table, 9 registers, and an adder | p.6 |
| operating frequency | exceeding 5 | GHz | UNKNOWN / Power6 | UNKNOWN | implemented Power6 divider | p.6 |
errors_and_checks: The quotient-selection error must be less than +/−1 digit. The comparison evaluates the common inexact-quotient case and calculates target precision plus 1 digit for round-to-nearest.   # pp.2,5
conditions: Decimal addition is treated as substantially more efficient than decimal multiplication, so subtractive division is favored while parallel decimal multiplication remains inefficient. The comparison assumes a 36-digit adder pipelined across 2 cycles, one data-selection cycle after carry-out, a 5GHz 13-FO4 cycle, and excludes common normalization/exponent/sign/special-number work. The 2-cycle variant requires shared-adder reuse; the faster redundant-adder variant requires more area.   # pp.1,5-6
evidence: §§2-8; Figs. 1-6, especially quotient selection in Fig. 3, dataflow in Fig. 4, iteration timing in Fig. 5, and comparison in Fig. 6.

### decimal_newton  (role: compares)
mechanism: Newton-Raphson computes Xi+1 = Xi × (2 − D × Xi), requiring two decimal multiplications and a 10s complementation per iteration. Each iteration approximately doubles the number of accurate reciprocal digits, so multiplication widths increase with the required precision. A final numerator multiplication produces the quotient, with two additional quotient digits retained for rounding.
choices:
  operation: divide   # pp.5-6
new_choices:
  iteration_precision: progressively_doubled — each multiplication uses the minimum digit width required by the current reciprocal accuracy   # p.6
slots:
  seed: UNKNOWN   # p.5
  final_round: extra_precision_quotient   # p.6
parameters: 16-digit and 34-digit results; two multiplications per iteration; two quotient guard digits; three unspecified lookup-table configurations NR1/NR2/NR3   # pp.5-6
results:
| metric | value | unit | technology / device | baseline | condition | page |
| NR1 decimal64 latency | 190 | cycles | UNKNOWN | Power6: 82 cycles | 16-digit result; comparison assumptions | p.6 |
| NR1 decimal128 latency | 312 | cycles | UNKNOWN | Power6: 154 cycles | 34-digit result; 0.5KB table | p.6 |
| NR2 decimal64 latency | 152 | cycles | UNKNOWN | Power6: 82 cycles | 16-digit result; comparison assumptions | p.6 |
| NR2 decimal128 latency | 274 | cycles | UNKNOWN | Power6: 154 cycles | 34-digit result; 12KB table | p.6 |
| NR3 decimal64 latency | 128 | cycles | UNKNOWN | Power6: 82 cycles | 16-digit result; comparison assumptions | p.6 |
| NR3 decimal128 latency | 250 | cycles | UNKNOWN | Power6: 154 cycles | 34-digit result; 256KB table | p.6 |
errors_and_checks: Two extra quotient digits are retained as guard digits for rounding.   # p.6
conditions: Performance depends on the accuracy and size of the lookup table holding the initial linear approximation. Decimal multiplication cost makes this method slower than the implemented additive scheme under the paper’s assumptions.   # pp.1,5-6
evidence: §§8; Fig. 6.

### decimal_encoding_codec  (role: instantiates)
mechanism: Two operand registers expand DPD coefficients into BCD before arithmetic. The result path compresses BCD back into DPD before the result register.
choices:
  significand_encoding: dpd   # pp.1,4
  codec_placement: at_register_read   # p.4
new_choices:
  output_codec_placement: before_result_register — the BCD-to-DPD compressor precedes the result register   # p.4
slots:
  none
parameters: two 144-bit operand registers with DPD-to-BCD expanders; one BCD-to-DPD compressor   # p.4
results:
| metric | value | unit | technology / device | baseline | condition | page |
| codec delay/area | UNKNOWN | UNKNOWN | UNKNOWN / Power6 | UNKNOWN | UNKNOWN | p.4 |
errors_and_checks: none
conditions: The divider operates on BCD coefficients from the compressed DPD decimal floating-point format.   # pp.1,4
evidence: §1; §5; Fig. 4.

### commercial_decimal_fpu  (role: instantiates)
mechanism: The Power6 Decimal Floating Point Unit contains a shared coefficient dataflow with operand/result registers, DPD/BCD codecs, a 2-cycle rotator, a 2-stage decimal/binary adder, conversion hardware, a working register, quotient correction, a prescale table, and a multiples generator. The decimal divider reuses this addition-oriented hardware.
choices:
  implementation: hardware_dfu   # pp.1,4
  datapath_width_digits: 36   # pp.3-5
slots:
  significand_adder: UNKNOWN   # pp.3-5
  multiplier: UNKNOWN   # pp.1,3
  divider: decimal_digit_recurrence   # pp.1-5
parameters: 36 decimal digits; 144-bit coefficient dataflow; 2-cycle adder; 2-cycle rotator; decimal64 and decimal128 support   # pp.1,3-5
results:
| metric | value | unit | technology / device | baseline | condition | page |
| decimal-divider additional prescale logic | 0.25 KB Tbl, 4 regs | printed hardware | UNKNOWN / Power6 | restoring methods: approx. 0 additional logic | implemented Power6 configuration | p.6 |
errors_and_checks: none
conditions: The design minimizes hardware beyond the existing decimal-addition dataflow. The shared adder prevents use of the larger redundant-adder alternative.   # pp.5-6
evidence: §§5,7-9; Figs. 4-6.

## new_families
none

## space_gaps
* `decimal_digit_recurrence` lacks a recurrence-style choice for restoring/non-restoring implementations.   # pp.1-2,5
* `decimal_digit_recurrence` lacks a direct-most-significant-digit quotient-selection value or compatible family for its `digit_select` slot.   # pp.2-4
* `decimal_digit_recurrence` lacks choices for dual partial-remainder calculation and decimal on-the-fly quotient accumulation.   # pp.3-5
* `decimal_encoding_codec.codec_placement` does not represent separate input expansion and output compression placements.   # p.4

## open_questions
* Figure 6 gives Power6/Alt. 1/Alt. 2 delays as `14 + 4I`, `14 + 3I`, and `14 + 2I`, while the preceding text gives `15 + (4*I)`, `15 + (3*I)`, and `15 + (2*I)`.   # pp.5-6
* The paper calls the chosen algorithm “maximally redundant” before later recoding quotient digits into {-5,…,+5}; the vocabulary classifies the implemented stored digit set as `minimally_redundant_m5_p5`.   # pp.1-4
* The NR1/NR2/NR3 table sizes identify lookup-table configurations but do not state their seed precision or iteration counts.   # pp.5-6
