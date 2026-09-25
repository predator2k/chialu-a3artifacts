---
handle: goldstine_1946
citation: Goldstine, Goldstine, "The Electronic Numerical Integrator and Computer (ENIAC)", Mathematics of Computation, 1946
actual_citation: Goldstine and Goldstine, "The ENIAC", IEEE Annals of the History of Computing, 1996 (reprint of the 1946 paper)
status: ok
kind: paper
unit_classes: [other]
formats: [signed_decimal10, signed_decimal20]
authority: landmark
pages_read: 7 / 7
---

## summary
The document describes the ENIAC's decimal pulse arithmetic, including accumulators, digit-serial multiplication, and a combined division/square-root unit (pp.10-15). The machine normally handles signed 10-digit decimal numbers and can combine accumulators for 20-digit operations (pp.10, 14).

## families
### iterative_decimal_multiplication  (role: instantiates)
mechanism: Two argument accumulators expose their digits to product-selection circuits. Tables store the tens and units digits of the fundamental one-digit products. The multiplier emits both components through separate channels, shifts each partial product into position, and accumulates the components separately. The multiplier processes one multiplier digit per addition time and finally combines the tens and units components in one partial-product accumulator (p.14).
choices:
  multiple_set: full_1x_to_9x   # p.14
  multiplier_digit_recoding: none   # p.14
  digits_per_cycle: 1   # p.14
new_choices:
  partial_product_split: tens_and_units_tables — stores and emits the two decimal digits of each fundamental product separately   # p.14
slots:
  accumulator: decimal_pulse_accumulator [outside domain]   # p.14
  final_adder: decimal_pulse_accumulator [outside domain]   # p.14
parameters: multiplicand up to 10 digits; multiplier p has 2 to 10 digits; products may have 10 to 20 digits; four accumulators, or possibly six for 10-to-20-digit products; latency p+4 addition times   # pp.12, 14
results:
| metric | value | unit | technology / device | baseline | condition | page |
| multiplier latency | p+4 | addition times | ENIAC vacuum-tube computer, 1946 | none | signed product of a multiplicand with as many as 10 digits by a p-digit multiplier, where 2 ≤ p ≤ 10 | p.12 |
| processing rate | 1 | multiplier digit per addition time | ENIAC vacuum-tube computer, 1946 | none | partial-product generation | p.14 |
errors_and_checks: none
conditions: The multiplier requires associated accumulators for arguments and partial-product accumulation; those accumulators remain available for other work when the multiplier is idle (pp.14-15). The multiplier uses stored fundamental products rather than arithmetic generation of digit multiples (p.14).
evidence: Table 1 (p.12); “Numerical Units of the ENIAC” (pp.14-15).

## new_families
### decimal_pulse_accumulator  (domain: decimal: decimal adders, closest: bcd_direct_addition, why_not: The accumulator uses unary pulse counts and ten-stage decade ring counters rather than 4-bit digit adders with +6 correction.)
mechanism: Each decimal place is stored in a ten-stage ring counter with one active stage. A received pulse advances the corresponding counter, and a transition from 9 to 0 produces carry-over to the next counter. Eleven conductors transmit the ten decimal places and sign concurrently; digit d is encoded by d pulses. Subtraction uses complements with respect to 10^10, while a two-stage PM counter distinguishes positive numbers from their complements (pp.12-13).
choices:
  digit_storage: {ten_stage_ring_counter}   # p.12
  digit_transmission: {unary_pulse_count}   # p.12
  interdigit_carry: {ring_wrap_9_to_0}   # p.12
  subtraction_representation: {complement_mod_10_power_n}   # pp.12-13
  width_digits: {10, 20}   # pp.10, 14
results:
| metric | value | unit | technology / device | baseline | condition | page |
| addition/subtraction latency | 1/5000 | sec. | ENIAC vacuum-tube computer, 1946 | none | one accumulator operation | p.11 |
| accumulator count | 20 | accumulators | ENIAC vacuum-tube computer, 1946 | none | complete ENIAC | pp.10, 13 |
| machine vacuum-tube count | approximately 18,000 | vacuum tubes | ENIAC vacuum-tube computer, 1946 | none | complete ENIAC, not one accumulator | p.10 |
| machine relay count | 1500 | relays | ENIAC vacuum-tube computer, 1946 | none | complete ENIAC, not one accumulator | p.10 |
errors_and_checks: Neon lamps expose flip-flop states for operator inspection; the document reports no numerical detection coverage or false-alarm behavior (p.12).
conditions: One accumulator stores a signed 10-digit number, while two specially interconnected accumulators provide 20 decade counters and one PM counter (pp.13-14). An accumulator can receive or transmit during an addition time, rather than doing both (p.13).
evidence: “Synchronization” (p.11); counter/pulse representation description (pp.12-13); “Numerical Units of the ENIAC” (pp.13-14).

### successive_add_subtract_decimal_divide_sqrt  (domain: decimal: decimal dividers, closest: decimal_digit_recurrence, why_not: The unit forms each quotient digit through repeated additions/subtractions until overdraft rather than selecting a radix-10 digit through a QDS table.)
mechanism: Division repeatedly subtracts or adds the denominator to the current remainder until overdraft. The remainder is then sent to a shift accumulator, shifted one decimal place left, and returned. The quotient accumulator receives +1 or -1 components according to whether the denominator was subtracted or added. The same unit computes square roots through successive additions/subtractions of odd numbers (p.15).
choices:
  operation: {division, square_root, both}   # pp.12, 15
  quotient_generation: {repeated_add_subtract_until_overdraft}   # p.15
  remainder_shift: {one_decimal_place_left}   # p.15
  square_root_trial_sequence: {successive_odd_numbers}   # p.15
results:
| metric | value | unit | technology / device | baseline | condition | page |
| division/square-root latency | Approximately 13[p + 1] | addition times | ENIAC vacuum-tube computer, 1946 | none | p quotient digits or p digits of twice the square root; depends on argument digits | p.12 |
errors_and_checks: none
conditions: The unit operates with four accumulators holding the numerator/radicand, denominator/twice-the-square-root, quotient, and shifted remainder (p.15). Operation time depends on the argument digits (p.12).
evidence: Table 1 (p.12); “Numerical Units of the ENIAC” (p.15).

## space_gaps
* The `iterative_decimal_multiplication.accumulator` slot lacks an ordinary pulse-count decimal accumulator and a split tens/units partial-product organization (p.14).
* The `iterative_decimal_multiplication.final_adder` slot lacks a decimal accumulator family, although ENIAC combines its partial-product components in one accumulator (p.14).
* The decimal-divider vocabulary lacks repeated add/subtract quotient-digit formation and a combined odd-number square-root mode (p.15).

## open_questions
* The document does not state whether every possible one-digit product is physically stored or whether some table entries are shared (p.14).
* The OCR rendering of the divider/square-root latency formula in Table 1 is “Approximately 13[p + 1],” so the original bracket typography remains uncertain (p.12).
