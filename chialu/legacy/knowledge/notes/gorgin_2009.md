---
handle: gorgin_2009
citation: Gorgin, Jaberipur, "Fully Redundant Decimal Arithmetic", 19th IEEE Symposium on Computer Arithmetic (ARITH-19), 2009
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [decimal_DSSD]
authority: incremental
pages_read: 145-152 / 8
---

## summary
The paper proposes fully redundant radix-10 addition/subtraction, multiplication, and division whose operands/results use the decimal septa signed digit set [–7, 7] (p.145). The DSSD adder reduces delay from 13.56 FO4 to 7.80 FO4, while the outlined parallel multiplier avoids final carry propagation and has an evaluated latency of 48.33 FO4 (pp.148, 151). The divider designs remain architectural outlines rather than synthesized implementations (pp.150-152).

## families
### redundant_decimal_addition  (role: proposes)
mechanism: Each DSSD digit is a 4-bit two’s-complement value in [–7, 7]. The adder represents the position sum as a two’s-complement carry-save number, decomposes selected operand bits into a decimal transfer/residue, and completes the digit with overlapping 2-bit/1-bit additions. Transfers do not propagate between digit positions. Subtraction complements each subtrahend digit and enforces a carry; shared logic produces a unified add/subtract slice (pp.147-148).
choices:
  digit_set: rbcd_m7_p7   # p.147
  operands_redundant: both   # pp.145-147
new_choices:
  digit_encoding: 4-bit_twos_complement — Encoding used for every DSSD digit   # p.147
  position_sum_form: two_complement_carry_save — Internal representation used to avoid an initial carry-propagating addition   # p.147
slots:
  none
parameters: digit set [–7, 7]; 4 bits/digit; adder/subtractor 9 logic levels; unified add/subtract 11 logic levels   # pp.147-148
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay | 0.87 | ns | TSMC 0.13 μm standard CMOS / 2009 | RBCD [13], 1.22 ns | DSSD new, synthesized | p.151 |
| area | 622 | UNKNOWN | TSMC 0.13 μm standard CMOS / 2009 | RBCD [13], 668 | DSSD new, synthesized | p.151 |
| delay | 2.50 | ns | TSMC 0.13 μm standard CMOS / 2009 | DSSD new | Svoboda [12], synthesized | p.151 |
| area | 781 | UNKNOWN | TSMC 0.13 μm standard CMOS / 2009 | DSSD new | Svoboda [12], synthesized | p.151 |
| delay | 1.22 | ns | TSMC 0.13 μm standard CMOS / 2009 | DSSD new | RBCD [13], synthesized | p.151 |
| area | 668 | UNKNOWN | TSMC 0.13 μm standard CMOS / 2009 | DSSD new | RBCD [13], synthesized | p.151 |
| delay | 1.39 | ns | TSMC 0.13 μm standard CMOS / 2009 | DSSD new | DSD [14], synthesized | p.151 |
| area | 2333 | UNKNOWN | TSMC 0.13 μm standard CMOS / 2009 | DSSD new | DSD [14], synthesized | p.151 |
| delay | 1.65 | ns | TSMC 0.13 μm standard CMOS / 2009 | DSSD new | DSD [30], synthesized | p.151 |
| area | 2112 | UNKNOWN | TSMC 0.13 μm standard CMOS / 2009 | DSSD new | DSD [30], synthesized | p.151 |
| logical-effort delay | 7.80 | FO4 | UNKNOWN / 2009 | RBCD [13], 13.56 FO4 | DSSD adder | pp.148, 151 |
| logical-effort delay | 9.5 | FO4 | UNKNOWN / 2009 | DSSD adder, 7.80 FO4 | unified add/subtract | p.148 |
| delay improvement | 40% | percent | TSMC 0.13 μm standard CMOS / 2009 | fastest previous design | synthesized DSSD adder | p.151 |
errors_and_checks: Exact carry-free decimal addition/subtraction within the DSSD representation; no approximation/error checker is reported   # pp.147-148
conditions: The design avoids word-wide conversion when redundant results feed later operations (p.146). DSSD requires no more than the four storage bits already required by a nonredundant decimal digit (pp.146, 151-152).
evidence: §§2.2-4, Figs. 1-4, Eqns. 4-11, Table III (pp.146-151)

### parallel_decimal_multiplication  (role: extends)
mechanism: DSSD multiplication precomputes the minimum multiple set Π = {±X, ±3X, ±4X}. Other multiples are expressed as sums of two DSSD numbers. Carry-free logic forms restricted high/low components, and a 4-level addition produces one DSSD multiple. Repeated DSSD additions reduce partial products directly to a DSSD product, so no final carry-propagating conversion is performed (pp.149-150).
choices:
  multiplier_recoding: none   # p.149
  internal_digit_code: DSSD_[–7,7]_4-bit_twos_complement [outside domain]   # pp.147, 149
  pp_generation: precomputed_multiples_mux   # p.149
new_choices:
  redundant_io: operands_partial_products_and_result — The same DSSD representation is retained throughout multiplication   # p.149
  precomputed_multiple_set: {±X, ±3X, ±4X} — Minimum set selected by the PPG network   # p.149
slots:
  reduction_tree: redundant_decimal_addition [outside slot domain]   # p.149
parameters: radix 10; DSSD operands/results; PPG 13 logic levels; PPG delay 9.33 FO4   # pp.149-150
results:
| metric | value | unit | technology / device | baseline | condition | page |
| PPG delay | 9.33 | FO4 | UNKNOWN / 2009 | none | logical-effort evaluation | p.150 |
| multiplier latency | 48.33 | FO4 | UNKNOWN / 2009 | nonredundant parallel multiplier [6], 65 FO4 | evaluated fully redundant multiplier | p.151 |
| speed improvement | 34% | percent | UNKNOWN / 2009 | nonredundant parallel multiplier [6] | evaluated fully redundant multiplier | p.151 |
errors_and_checks: Exact DSSD product is produced directly after partial-product reduction; no approximation/error checker is reported   # p.149
conditions: The architecture benefits when a redundant product remains an operand of later arithmetic because final conversion is omitted (p.149). The multiplier is evaluated analytically rather than synthesized (pp.151-152).
evidence: §5, Figs. 5-7, Tables I-II, Eqns. 12-15 (pp.149-150); §7 (p.151)

### decimal_digit_recurrence  (role: extends)
mechanism: The radix-10 subtractive divider represents dividend/divisor/quotient/partial remainders as DSSD numbers. Precomputed multiples {–7D,…,7D} feed the DSSD subtractor. A table indexed by the three divisor MSDs supplies comparison multiples, while three partial-remainder MSDs are maintained in binary carry-save form for quotient-digit selection (p.151).
choices:
  quotient_digit_set: redundant_m7_p7   # p.151
new_choices:
  redundant_io: dividend_divisor_quotient_and_remainders — All external/intermediate values remain DSSD   # p.151
slots:
  digit_select: qds_table   # p.151
parameters: radix 10; quotient digits [–7, 7]; three divisor MSDs and three partial-remainder MSDs used for selection   # p.151
results:
| metric | value | unit | technology / device | baseline | condition | page |
errors_and_checks: Exact digit-recurrence division is intended; no error checker/coverage result is reported   # p.151
conditions: The claimed latency is only expected to be no more than the nonredundant divider in [8], because quotient selection remains on a similar critical path (p.151). The divider is not synthesized (p.152).
evidence: §6.2, Eqn. 18 (p.151)

## new_families
### dssd_split_reciprocal_division  (domain: decimal: decimal dividers, closest: decimal_newton, why_not: the proposed recurrence uses a divisor split/table approximation and two multiplications rather than Newton iteration)
mechanism: The normalized DSSD divisor is split into most-/least-significant halves Dh/Dl. The design aligns –Dl with Dh without subtraction, obtains a reciprocal approximation from a table in parallel with one multiplication, and performs a final multiplication for the quotient. Negation of Dl uses parallel 4-bit two’s complementation, and both multiplications use the fully redundant DSSD multiplier (p.150).
choices: divisor_split: equal_halves; reciprocal_seed: table_lookup; operand_representation: DSSD_[–7,7]; multiplier_count: 2
results:
| metric | value | unit | technology / device | baseline | condition | page |
evidence: §6.1, Eqn. 17 (p.150)

## space_gaps
* `redundant_decimal_addition` lacks choices for 4-bit two’s-complement digit encoding and carry-save position-sum representation (p.147).
* `parallel_decimal_multiplication.reduction_tree` cannot name `redundant_decimal_addition`, although the DSSD adder performs partial-product reduction (p.149).
* `decimal_digit_recurrence` lacks a choice describing fully redundant operands/results/remainders (p.151).

## open_questions
* The multiplier’s DSSD-adder reduction topology and number of reduction levels are not specified (p.149).
* The reciprocal table size/precision and exact split-division equation parameters are not specified (p.150).
* The divider latency claim is qualitative, and multiplier/divider synthesis is deferred to future work (pp.151-152).
