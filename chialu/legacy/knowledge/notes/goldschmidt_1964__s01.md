---
handle: goldschmidt_1964#s01
parent: goldschmidt_1964
citation: Goldschmidt, "Applications of Division by Convergence", MS thesis, MIT, 1964
chapter: APPLICATIONS OF DIVISION BY CONVERGENCE
pdf_pages: 0-43
status: ok
kind: thesis_chapter
unit_classes: [BINARY_ALU]
formats: [56-bit binary floating-point fractions]
authority: thesis
pages_read: 44 / 44
---

## summary
The thesis defines floating-point division by multiplying the numerator and denominator by successive approximate reciprocals until the denominator converges quadratically toward one. # p.1, p.6-p.16
The implementation shares a signed-digit iterative multiplier between multiplication and division, completes a 56-bit multiply in 6 cycles, and completes division in 13 cycles. # p.18-p.31
The thesis bounds implementation roundoff and finds a factor-of-two division-time advantage only when the machine organization provides sufficiently fast multiplication. # p.31-p.42

## families
### goldschmidt  (role: defines)
mechanism: The divisor and dividend become denominator D and numerator N. Each iteration derives an approximate reciprocal from D and multiplies both D and N by that factor, so D approaches one and N approaches the quotient. RCK uses the two's complement of a truncated leading part of D. The generalized form chooses CK bits of the reciprocal and increases the predicted minimum leading-string length from LK to LK+CK. # p.6-p.16
choices:
  iterations: 4   # p.30-p.31
  dedicated_multiplier: false   # p.18, p.24-p.26
  internal_guard_bits: 5   # p.18, p.32-p.40
  truncated_intermediate_multiplies: true   # p.22, p.32-p.34
new_choices:
  approximate_reciprocal: {RAK, RBK, RCK, generalized_RCK} — selects the complement form and retained denominator positions used to form each convergence factor   # p.10-p.16
  reciprocal_length_CK: 6, 11, 11, 23 — selects the added predicted string length for the four refinement factors   # p.30-p.31
  numerator_denominator_concurrency: {concurrent, sequential} — determines whether the two products of each convergence step overlap   # p.8, p.24-p.25, p.41
slots:
  seed: monolithic_rom [input_bits=6, output_bits=8, function=reciprocal]   # p.15-p.17, p.24
  iter_mult: sequential_shift_add [bits_per_cycle=4, accumulator_form=carry_save]   # p.18-p.24, p.27-p.31
  final_round: UNKNOWN   # p.39-p.40
parameters: input fraction 56 bits; output fraction 57 bits; internal positions 2^0 through 2^-61; L1=6, L2=12, L3=23, L4=34, L5=57; 13 divide cycles   # p.18, p.30-p.31
results:
| metric | value | unit | technology / device | baseline | condition | page |
| convergence, RAK | LK+1 = 2LK | predicted minimum string length | abstract | LK | two's complement of DK | p.10 |
| convergence, RBK | LK+1 = 2LK - 1 | predicted minimum string length | abstract | LK | one's complement of truncated 1+XK | p.11-p.12 |
| convergence, RCK | LK+1 = 2LK | predicted minimum string length | abstract | LK | two's complement of truncated 1+XK | p.13 |
| convergence, generalized RCK | LK+1 = LK + CK | predicted minimum string length | abstract | LK | CK ≤ LK | p.14-p.15 |
| naive 56-bit convergence work | six iterations or twelve multiplies | iterations / multiplies | abstract | standard division as fast as four multiply times | two numerator/denominator multiplies per iteration | p.8-p.9 |
| divide execution time | 13 | cycles | proposed multiply-divide unit | multiply execution time of 6 cycles | 56-bit fractions | p.30-p.31 |
| divide execution time | on the order of 2 | us | current technology, device UNKNOWN, 1964 | standard division at best four multiply times | proposed multiply-divide unit | p.31 |
| relative divide execution time | twice | multiply time | proposed multiply-divide unit | standard division at best four multiply times | current design | p.31 |
| high-performance speed advantage | factor of two | execution-time factor | abstract | conventional methods | numerator/denominator products use the proposed organization | p.41 |
| one-iteration multiplication error | -3 x 2^-61 ≤ E1 ≤ 0 | fraction value | abstract | exact product | truncated internal products through 2^-61 | p.33 |
| final denominator range | 1-2^-68 ≤ D5 ≤ 1+2^-57-2^-61 | fraction value | abstract | exact denominator 1 | L4=34 and C4=23 | p.37 |
| conventional result error | N0/D0-2^-56 ≤ standard result ≤ N0/D0 | fraction value | abstract | infinite-length exact quotient | high-order 56 result bits | p.40 |
| single-adder work penalty | at least 50% longer | execution time | abstract | conventional division | two multiplier bits processed per cycle | p.40 |
| concurrent convergence time | one full length multiplication plus one propagate add cycle for each iteration | time | abstract | UNKNOWN | DK and NK multiplications concurrent | p.41 |
| sequential convergence time | three halves of a full multiply time | time | abstract | UNKNOWN | DK and NK multiplications not concurrent and no per-multiply overhead | p.41 |
| serial-decimal applicability threshold | multiply time is less than two-thirds of the divide time | time ratio | abstract | restoring decimal division | serial-by-character scientific computer | p.42 |
errors_and_checks: Each truncated convergence multiplication has a negative error bounded approximately by -3 x 2^-61 and zero. The final error has contributions from incomplete convergence, denominator-induced reciprocal errors, numerator multiplication errors, and removal of positions below 2^-56. The convergence result may alter positions 2^-1 through 2^-56, whereas the standard method preserves those exact-quotient positions. # p.33-p.40
conditions: The method applies to floating-point division because it produces no remainder. The inputs are positive normalized fractions from one half through less than one. A single carry-propagate-adder organization is not competitive. Concurrent numerator/denominator multiplication enables the high-performance advantage. Fixed-point division requires separate hardware or programming. # p.6, p.40-p.42
evidence: Abstract; Part One, Theory; Division; Round Off Error; Criteria for Applicability. # p.1, p.6-p.17, p.24-p.42

### sequential_shift_add  (role: instantiates)
mechanism: An overlapping three-bit signed recoding represents every two multiplier bits by one of five multiples. Each loop pass shifts the two-register partial product right four and adds two selected multiplicand multiples with a four-input/two-output adder. A final carry-propagate addition assimilates the two partial-product registers. # p.18-p.24
choices:
  bits_per_cycle: 4   # p.20, p.22-p.24
  accumulator_form: carry_save   # p.18-p.19, p.22-p.24
  string_skipping: UNKNOWN   # p.20-p.24
new_choices:
  multiplier_recoding: overlapping_three_bit_signed — encodes each two-bit group as 0, +2^0, +2^-1, -2^0, or -2^-1   # p.20-p.21
  multiples_per_pass: 2 — adds M2K and 2^-2M(2K-1) during each loop pass   # p.22-p.23
  recirculating_adder: four_input_two_output — retains the partial product in PP1/PP2 until final assimilation   # p.18-p.19, p.22-p.24
slots:
  step_adder: UNKNOWN   # p.18-p.24
parameters: 56-bit multiplier and multiplicand; 15 loop passes; three four-input additions per machine cycle; maximum 29 non-zero multiples; 5 iteration cycles plus 1 initialization/final-add cycle   # p.18, p.23
results:
| metric | value | unit | technology / device | baseline | condition | page |
| non-zero multiple reduction | factor of two | multiple additions | abstract | unsigned power-of-two encoding | overlapping signed recoding | p.20 |
| maximum non-zero multiples | 29 | multiples | abstract | UNKNOWN | 56-bit multiplication | p.23 |
| iteration time | 5 | cycles | proposed multiply unit | UNKNOWN | six multiples accumulated per cycle | p.23 |
| total multiply execution time | 6 | cycles | proposed multiply unit | UNKNOWN | initialization and final carry-propagate addition included | p.23 |
errors_and_checks: Bits shifted below 2^-61 are discarded. A spill adder detects whether discarded PP1/PP2 portions cause a carry into position 2^-61. # p.22
conditions: The multiplication loop supplies the fast multiply capability required by division by convergence. The final carry-propagate adder converts the two-register partial product into one product. # p.18-p.19, p.23-p.24
evidence: Figure One; Table Two; multiply recurrence; execution-time discussion. # p.19-p.24

### monolithic_rom  (role: instantiates)
mechanism: RSO is selected by inspecting the leading denominator positions. A reciprocal decoder maps denominator intervals expressed in 64ths to reciprocal ranges expressed in 256ths, producing a first factor that reduces the number of later convergence iterations. # p.15-p.17
choices:
  input_bits: 6   # p.15-p.17
  output_bits: 8   # p.16-p.17
  guard_bits: UNKNOWN   # p.15-p.17
  function: reciprocal   # p.15-p.17
new_choices:
  none
slots:
  none
parameters: denominator intervals 32 through 64 in 64ths; reciprocal ranges 256 through 504 in 256ths   # p.16-p.17
results:
| metric | value | unit | technology / device | baseline | condition | page |
| decoder coverage | 32 through 64 | 64ths | abstract | normalized denominator range | RSO selection | p.16-p.17 |
| reciprocal output range | 256 through 504 | 256ths | abstract | UNKNOWN | RSO selection | p.16-p.17 |
errors_and_checks: none
conditions: RSO is used only for the first convergence iteration and is determined from leading positions of D0. # p.15, p.24
evidence: Description of RSO; Reciprocal Decoder tables. # p.15-p.17

## taxonomy
* Division by convergence   # p.6-p.17
  * Full-denominator two's complement reciprocal, RAK -> goldschmidt   # p.10
  * Truncated one's complement reciprocal, RBK -> goldschmidt   # p.11-p.12
  * Truncated two's complement reciprocal, RCK -> goldschmidt   # p.13
  * Variable-length truncated two's complement reciprocal, generalized RCK -> goldschmidt   # p.14-p.15
  * First-iteration reciprocal decoder, RSO -> monolithic_rom   # p.15-p.17
* Multiply-divide implementation   # p.18-p.31
  * Overlapping signed recoding with a recirculating four-input/two-output adder -> sequential_shift_add   # p.18-p.24
  * Shared multiply/add execution of numerator and denominator products -> goldschmidt   # p.24-p.31
* Applicability organizations   # p.40-p.42
  * Concurrent DK/NK multiplication -> goldschmidt   # p.41
  * Sequential DK/NK multiplication -> goldschmidt   # p.41
  * Single carry-propagate-adder arithmetic unit -> goldschmidt   # p.40-p.41
  * Serial-by-character restoring-decimal machine -> goldschmidt   # p.42

## primary_sources
* T. C. Chen, 1963 — suggested reducing division execution time with an RK-type approximate reciprocal.   # p.2, p.43

## new_families
none

## space_gaps
* `sequential_shift_add` lacks choices for overlapping signed multiplier recoding, multiple additions per pass, and a recirculating four-input/two-output accumulator. # p.18-p.24
* The `goldschmidt` `final_round` slot lacks a value for truncating an extra-precision quotient without a correctly-rounded remainder test. # p.39-p.40
* The vocabulary declares `csa_reduction_tree` as a slot filler but provides no family for the chapter's four-input/two-output carry-save accumulation structure. # p.18-p.24

## open_questions
* The OCR does not preserve the printed numerical convergence-result error inequality on page 40 reliably enough to transcribe it. # p.39-p.40
* The chapter does not identify the circuit technology or device underlying the stated execution time of “on the order of 2 us.” # p.31
