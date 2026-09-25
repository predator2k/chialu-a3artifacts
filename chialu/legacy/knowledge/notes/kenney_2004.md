---
handle: kenney_2004
citation: Kenney, Schulte, Erle, "A High-Frequency Decimal Multiplier", IEEE International Conference on Computer Design (ICCD), 2004
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [bcd]
authority: incremental
pages_read: 5 / 5
---

## summary
The paper proposes an iterative BCD multiplier that stores intermediate products as overloaded decimal digits with values from 0₁₆ through F₁₆. The representation permits a two-stage iterative adder and synthesized clock frequencies near 2 GHz for 8/16/34-digit operands. # p.1, p.2, p.5

## families
### iterative_decimal_multiplication  (role: proposes)
mechanism: Each iteration selects two secondary multiples whose sum equals the multiplicand times one BCD multiplier digit. A two-stage overloaded decimal adder combines those multiples with an intermediate product represented by base-10 digits whose 4-bit values may range from 0₁₆ through F₁₆. Per-digit clean-up logic converts outgoing and final intermediate digits back to BCD before the simplified decimal carry-propagate addition. # p.2–p.4
choices:
  multiple_set: easy_2x_4x_5x   # p.2
  multiplier_digit_recoding: none   # p.2
  digits_per_cycle: 1   # p.1, p.2
new_choices:
  intermediate_product_representation: overloaded_decimal_0_to_15 — Intermediate base-10 digits admit every 4-bit value from 0₁₆ through F₁₆.   # p.2
slots:
  accumulator: none
  final_adder: none
parameters: 8/16/34-digit BCD operands; n iterations; two-stage overloaded decimal adder; four-stage 1-digit clean-up block; two-stage final decimal carry-propagate addition; latency (n + 8) cycles; initiation interval (n + 1) cycles   # p.1, p.3–p.5
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay | 0.49 | ns | LSI Logic gflxp 0.11 micron CMOS standard cell library (2004) | none | 8-digit operands, optimized for delay | p.5 |
| frequency | 2.04 | GHz | LSI Logic gflxp 0.11 micron CMOS standard cell library (2004) | none | 8-digit operands, optimized for delay | p.5 |
| area | 0.093 | mm² | LSI Logic gflxp 0.11 micron CMOS standard cell library (2004) | none | 8-digit operands, optimized for delay | p.5 |
| delay | 0.50 | ns | LSI Logic gflxp 0.11 micron CMOS standard cell library (2004) | none | 16-digit operands, optimized for delay | p.5 |
| frequency | 2.00 | GHz | LSI Logic gflxp 0.11 micron CMOS standard cell library (2004) | none | 16-digit operands, optimized for delay | p.5 |
| area | 0.199 | mm² | LSI Logic gflxp 0.11 micron CMOS standard cell library (2004) | none | 16-digit operands, optimized for delay | p.5 |
| delay | 0.51 | ns | LSI Logic gflxp 0.11 micron CMOS standard cell library (2004) | none | 34-digit operands, optimized for delay | p.5 |
| frequency | 1.96 | GHz | LSI Logic gflxp 0.11 micron CMOS standard cell library (2004) | none | 34-digit operands, optimized for delay | p.5 |
| area | 0.373 | mm² | LSI Logic gflxp 0.11 micron CMOS standard cell library (2004) | none | 34-digit operands, optimized for delay | p.5 |
| delay | 0.58 | ns | LSI Logic gflxp 0.11 micron CMOS standard cell library (2004) | none | 34-digit decimal carry-save multiplier [4], optimized for delay | p.5 |
| frequency | 1.72 | GHz | LSI Logic gflxp 0.11 micron CMOS standard cell library (2004) | none | 34-digit decimal carry-save multiplier [4], optimized for delay | p.5 |
| area | 0.210 | mm² | LSI Logic gflxp 0.11 micron CMOS standard cell library (2004) | none | 34-digit decimal carry-save multiplier [4], optimized for delay | p.5 |
| clock-frequency improvement | 14 | % | LSI Logic gflxp 0.11 micron CMOS standard cell library (2004) | decimal carry-save addition [4] | 34-digit operands, both designs optimized for delay | p.5 |
| area increase | 77 | % | LSI Logic gflxp 0.11 micron CMOS standard cell library (2004) | decimal carry-save addition [4] | 34-digit operands; increase attributed to clean-up blocks | p.5 |
errors_and_checks: none
conditions: Delay changes little with operand width because increased width primarily raises fanout. The critical path is the overloaded adder’s first stage and contains eight logic levels. The 14% frequency improvement requires 77% more area than the decimal carry-save design because the clean-up blocks merge and correct two intermediate products. # p.5
evidence: §3, Figures 1–3, §4, Tables 1–2, p.2–p.5

### redundant_decimal_addition  (role: instantiates)
mechanism: The overloaded representation treats every 4-bit pattern from 0₁₆ through F₁₆ as a base-10 digit. The first adder stage conditionally adds six to BCD secondary-multiple digits according to carry-outs from the previous iteration, then applies a 4-bit binary carry-save adder. The second stage compresses the resulting sum/carry with a 4-bit binary carry-propagate adder. Clean-up blocks add six to overloaded digits in the A₁₆-through-F₁₆ range to restore BCD. # p.2–p.4
choices:
  digit_set: overloaded_0_15   # p.2
  operands_redundant: one   # p.3
  final_conversion: carry_propagate_adder   # p.4
new_choices:
  correction_schedule: deferred_to_next_iteration_and_cleanup — A carry representing sixteen causes the +6 correction to be applied during the next iteration, while outgoing/final digits receive separate BCD clean-up.   # p.3, p.4
slots:
  none
parameters: two-stage overloaded decimal adder; one 4-bit binary CSA in stage one; one 4-bit binary CPA in stage two; four-stage 1-digit clean-up block; n-digit intermediate-product clean-up array   # p.3, p.4
results:
| metric | value | unit | technology / device | baseline | condition | page |
| iterative-stage critical path | 8 | logic levels | LSI Logic gflxp 0.11 micron CMOS standard cell library (2004) | decimal 4:2 compression with ten logic levels [4] | first stage of overloaded decimal adder | p.2, p.5 |
errors_and_checks: none
conditions: The representation reduces iterative correction overhead because correction occurs only after a 4-bit digit exceeds fifteen. Every overloaded digit leaving the iterative structure and every remaining intermediate digit must be converted back to BCD before final output. # p.2–p.4
evidence: §3, Figures 1–3, p.2–p.4

## new_families
none

## space_gaps
* `iterative_decimal_multiplication` lacks a choice for the intermediate-product digit representation, which this design fixes as overloaded 0₁₆-through-F₁₆ digits. # p.2
* `iterative_decimal_multiplication.accumulator` cannot name `redundant_decimal_addition`, although the proposed iterative accumulator uses overloaded redundant decimal digits. # p.2–p.4
* `iterative_decimal_multiplication.final_adder` cannot name `bcd_direct_addition`, although the design finishes with a simplified decimal carry-propagate adder. # p.4
* `redundant_decimal_addition` lacks a correction-schedule choice for next-iteration +6 correction and separate output/final clean-up. # p.3, p.4

## open_questions
* The paper delegates the simplified final decimal carry-propagate adder’s detailed carry/correction structure to reference [4], so its `bcd_direct_addition` choice values remain UNKNOWN. # p.2, p.4
* The paper reports no numerical accuracy/error contract because it presents exact BCD multiplication rather than an approximate design. # p.1–p.5
