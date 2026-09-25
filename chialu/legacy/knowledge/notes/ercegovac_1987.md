---
handle: ercegovac_1987
citation: Ercegovac, Lang, "On-the-Fly Conversion of Redundant into Conventional Representations", IEEE Transactions on Computers, 1987
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [signed_digit, twos_complement]
authority: landmark
pages_read: 3 / 3
---

## summary
The document presents an exact on-the-fly conversion from redundant signed-digit results to conventional range-complement representations. The conversion runs concurrently with MSD-first digit generation in SRT division/square root and on-line arithmetic, with precision-independent delay roughly equal to two logic levels plus register shift/load time.

## families
### generalized_signed_digit  (role: extends)
mechanism: The conversion maintains conditional forms A[k] and B[k], where B[k] = A[k] - r^-k. Each incoming signed digit selects and extends one form without carry propagation, and the final conventional result is A[m]. The radix-2 algorithm is generalized to radix r, and a radix-4 implementation uses two shift/load registers with appended binary digits.
choices:
  radix: 2, 4   # pp.895-897
  digit_encoding: sign_magnitude   # p.897
  final_conversion: on_the_fly   # pp.895-897
new_choices:
  none
slots:
  none
parameters: radix 2; general radix r with digits pi ∈ {-a, ..., 0, ..., a}, r/2 ≤ |a| < r; radix-4 minimally redundant digits {-2, -1, 0, 1, 2}; two shift/load registers A and B; one input digit processed per step   # pp.895-897
results:
| metric | value | unit | technology / device | baseline | condition | page |
| step delay | roughly equal to two logic levels plus a register shift/load time | delay | UNKNOWN / 1987 | conventional conversion using a carry-propagate adder | digit-by-digit conversion | p.897 |
| precision dependence | independent of the working precision | delay scaling | UNKNOWN / 1987 | UNKNOWN | digit-by-digit conversion | p.897 |
errors_and_checks: The recurrence is proved to produce the equivalent conventional representation; no numerical error, fault model, detection coverage, false-alarm behavior, or alias rate is reported.   # pp.895-897
conditions: The input digits must be generated serially from most significant to least significant. The input must be normalized for the stated initial conditions. The method applies to nonrestoring division/square root and on-line algorithms. The generalized radix-r implementation requires a one-digit adder to compute r - |pk+1| - 1.   # pp.895-897
evidence: §I; §II equations (1)-(4.6), proof, and examples; §III radix-r recurrence; §IV, Fig. 1, and Table I; §V.

## new_families
### on_the_fly_redundant_conversion  (domain: redundant: online arithmetic, closest: generalized_signed_digit, why_not: generalized_signed_digit names an arithmetic representation and addition scheme rather than the standalone digit-by-digit converter established here)
mechanism: Two conditional conventional forms are maintained while redundant digits arrive MSD first. A[k] represents the current result, and B[k] represents A[k] minus one unit in the current digit position. Each incoming digit selects one form, appends a digit, and optionally loads the other register, which avoids carry propagation across the accumulated result. The final output is A[m].
choices: input_order: {msd_first} # p.895; conditional_forms: {two_forms_A_B} # pp.895-896; input_radix: {2, general_r} # pp.895-897; output_representation: {range_complement} # pp.895-897; register_structure: {dual_shift_load} # pp.896-897
results:
| metric | value | unit | technology / device | baseline | condition | page |
| step delay | roughly equal to two logic levels plus a register shift/load time | delay | UNKNOWN / 1987 | carry-propagate-adder conversion | conversion concurrent with digit generation | p.897 |
evidence: §I; §II equations (1)-(4.6) and Fig. 1; §III; §IV and Table I; §V.

## space_gaps
* A component family for MSD-first on-the-fly redundant-to-conventional conversion is absent, although the document gives a recurrence and dual-register implementation for radix 2/general r. # pp.895-897
* Division/square-root and online-arithmetic families lack a final-converter slot that can name the on-the-fly conversion mechanism. # pp.895, 897

## open_questions
* The document does not report an implementation technology, area, power, clock frequency, or measured latency.
* The radix-r section does not provide a complete gate-level implementation beyond requiring a one-digit adder.
