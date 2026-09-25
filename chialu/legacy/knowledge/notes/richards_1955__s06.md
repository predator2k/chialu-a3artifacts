---
handle: richards_1955#s06
parent: richards_1955
citation: Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
chapter: BINARY MULTIPLICATION AND DIVISION
pdf_pages: 147-187
status: ok
kind: book_chapter
unit_classes: [BINARY_ALU, other]
formats: [unsigned binary, true-form signed binary, ones-complement binary, twos-complement binary, fixed-point binary]
authority: textbook
pages_read: 41 / 41
---

## summary
The chapter classifies simultaneous/parallel-accumulation/serial/serial-parallel multiplication and restoring/nonrestoring/nonperforming division. It settles their shifting, storage, signed-operation, remainder, and rounding mechanisms and compares equipment or operation counts in abstract terms.   # p.149, p.151, p.163, p.166, p.180, p.181, p.182, p.185

## families
### carry_save_array  (role: defines)
mechanism: A simultaneous multiplier gates the multiplicand with every multiplier digit to form all partial products, then combines the partial products through parallel arrangements of half adders and full adders. Steady input signals produce a steady product after switching transients disappear.   # p.149
choices:
  signed_scheme: unsigned   # p.149
  rows_per_pipeline_stage: UNKNOWN   # p.149
new_choices:
  partial_product_combination: paired_parallel_adders | successive_addition | columnwise_half_full_adders — selects the staged arrangement used to sum partial products   # p.149, p.151
slots:
  cpa: UNKNOWN   # p.149
parameters: 4 binary digits by 4 binary digits in the illustrated circuit; useful-sized factors are stated as 16 binary digits or larger   # p.149, p.151
results:
| metric | value | unit | technology / device | baseline | condition | page |
|---|---:|---|---|---|---|---|
| maximum product width | sum of the numbers of digits in the factors | binary digits | abstract | factor widths | any radix | p.149 |
| speed classification | fastest multiplier known | qualitative | abstract | other described multiplier methods | speed is of extreme importance | p.151 |
errors_and_checks: none
conditions: The simultaneous multiplier requires a very large amount of equipment for useful factor widths. The maximum conceivable signal path gives a conservative multiplication-time bound, but no simple general method determines the actual maximum path.   # p.151
evidence: Table 5-1; Figs. 5-1; simultaneous-multiplier discussion   # p.147, p.149, p.150, p.151

### sequential_shift_add  (role: taxonomizes)
mechanism: Multiplication by accumulation repeatedly adds the multiplicand under control of successive multiplier digits. A parallel implementation shifts either the multiplicand relative to the accumulator or the accumulated sum; the shifting-accumulator form determines one final product digit after each partial-product entry. An asynchronous form sends each completed sum digit directly to the next lower accumulator position and senses completion to start another operation.   # p.151, p.152, p.154, p.159, p.161
choices:
  bits_per_cycle: 1   # p.154
  accumulator_form: carry_propagate   # p.151
  string_skipping: UNKNOWN   # p.151
new_choices:
  shifted_quantity: multiplicand | accumulated_sum — selects the shifted operand   # p.152, p.154
  multiplier_in_low_accumulator_orders: true — stores and discards multiplier digits during right shifts   # p.155
  control_timing: synchronous | asynchronous_completion — selects fixed sequencing or completion-trigger initiation   # p.159, p.161
  fused_add_and_shift: true — sends each sum digit directly to the next lower accumulator order   # p.159
slots:
  step_adder: UNKNOWN   # p.151
parameters: one partial-product entry and shift per multiplier digit; accumulating orders equal multiplicand digits plus one in the shifting-accumulator arrangement   # p.154
results:
| metric | value | unit | technology / device | baseline | condition | page |
|---|---:|---|---|---|---|---|
| multiplicand-shifter “and” switches | product of multiplicand and multiplier digit counts | switches | abstract | direct parallel shifting | Fig. 5-2(a) | p.152 |
| multiplicand-shifter “or” inputs | approximately the same product | input lines | abstract | direct parallel shifting | Fig. 5-2(a) | p.152 |
| accumulating orders when shifting multiplicand | sum of multiplicand and multiplier digit counts | orders | abstract | shifting accumulator | parallel operation | p.154 |
| accumulating orders when shifting accumulated sum | multiplicand digit count plus one | orders | abstract | shifted multiplicand | parallel operation | p.154 |
| shifter equipment scaling when shifting accumulated sum | proportional to sum of operand digit counts | components | abstract | product scaling for shifted multiplicand | large operands | p.155 |
errors_and_checks: none
conditions: Shifting the accumulated sum requires less shifting equipment for large factors. Asynchronous operations may overlap, with trigger resolution time limiting their spacing.   # p.155, p.161
evidence: Figs. 5-2 through 5-8 and parallel/asynchronous multiplication discussions   # p.152, p.153, p.154, p.159, p.160

### serial_serial_parallel  (role: taxonomizes)
mechanism: A fully serial multiplier circulates multiplier/multiplicand/partial-product digits through delay storage and a serial adder. A serial-parallel multiplier presents one factor serially and gates a parallel factor into delayed full-adder stages. Grouped variants select precomputed multiples and process two or more binary digits together.   # p.163, p.165, p.166, p.168, p.169
choices:
  serial_operands: both   # p.163
  serial_operands: one   # p.166
  digit_size_bits: 1   # p.166
  digit_size_bits: 2   # p.168
  digit_size_bits: 3   # p.169
  digit_size_bits: 4   # p.169
  end_reconfigure_to_ripple: UNKNOWN   # p.166
new_choices:
  multiplier_grouping_only: true | false — distinguishes multiplier-only grouping from grouping both factors   # p.168, p.169
  precomputed_multiple_limit: 3M | 7M — selects the largest generated multiplicand multiple   # p.168, p.169
slots:
  none
parameters: four delay-storage devices of n time units in the fully serial arrangement; illustrated serial example uses n = 4   # p.163
results:
| metric | value | unit | technology / device | baseline | condition | page |
|---|---:|---|---|---|---|---|
| serial multiplication storage | 4 | delay units of n time units each | abstract | UNKNOWN | fully serial arrangement | p.163 |
| serial example completion | T20 | time | abstract | start at T0 | n = 4 | p.166 |
| serial-parallel multiplication time | time required to transmit the product serially | digit periods | abstract | product width | one factor serial | p.167 |
| serial-parallel equipment dependence | multiplicand digit count; independent of multiplier digit count | qualitative | abstract | fully parallel implementation | Fig. 5-10 | p.167 |
| grouped-pair accumulation adders | less than half the number of multiplier digits | full adders | abstract | one adder per multiplier position | many multiplier digits | p.168 |
| grouped-pair equipment trade | each alternate full adder for a nine-diode switching circuit | components | abstract | ungrouped serial-parallel multiplier | many multiplier digits | p.168 |
| grouped-digit speed increase | factor equal to the number of digits in each group | factor | abstract | ungrouped serial-parallel multiplier | both factors grouped | p.171 |
errors_and_checks: none
conditions: Multiplier-only groups larger than two require increasingly complex selectors, so their equipment saving is questionable. Grouping both factors increases speed but requires substantial generation/selection equipment.   # p.169, p.171
evidence: Figs. 5-9 through 5-13 and serial/serial-parallel discussions   # p.163, p.164, p.166, p.168, p.169, p.170

### restoring_nonrestoring  (role: taxonomizes)
mechanism: Binary division forms quotient digits through successive shifted subtractions of the divisor. Restoring division adds the divisor back after a negative remainder. Nonrestoring division shifts the divisor and reverses the next operation instead of restoring immediately. Nonperforming division compares first and stores a difference only when subtraction remains nonnegative.   # p.178, p.180, p.181, p.182, p.183
choices:
  style: restoring   # p.180
  style: nonrestoring   # p.181
  style: nonperforming   # p.182
  bits_per_cycle: 1   # p.180
  shift_over_zeros: UNKNOWN   # p.180
new_choices:
  initial_magnitude_test: subtract_shifted_divisor — verifies that the divisor is large enough relative to the dividend   # p.179
  final_remainder_policy: discard | restore | reconstruct — selects treatment after quotient generation   # p.181, p.183
slots:
  residual_adder: UNKNOWN   # p.184
parameters: one quotient digit per shifted divisor position   # p.180
results:
| metric | value | unit | technology / device | baseline | condition | page |
|---|---:|---|---|---|---|---|
| nonrestoring arithmetic work | one addition or subtraction per quotient digit | operations | abstract | restoring division | final remainder discarded | p.181 |
| quotient value | largest multiple of the divisor equal to or less than the dividend | quotient | abstract | exact ratio | finite generated width | p.183 |
| reconstructed remainder | dividend minus unrounded quotient times divisor | arithmetic expression | abstract | retained hardware remainder | remainder needed occasionally | p.183 |
errors_and_checks: A finite quotient may be inexact when the remainder is nonzero; additional quotient digits increase accuracy, after which the remainder is discarded or stored separately.   # p.183
conditions: Nonrestoring division is attractive when the remainder is discarded, but final-remainder recovery may require addition or subtraction and complicates the divider. A simultaneous divider requires so many adders/subtracters/switches that it is considered only in rare cases.   # p.181, p.184
evidence: division examples and physical-divider discussion   # p.178, p.180, p.181, p.182, p.183, p.184, p.185

### newton_raphson  (role: analyzes)
mechanism: The reciprocal iteration uses the binary recurrence bK+1 = bK(10 - xbK), where successive bK values approximate 1/x. Division follows by multiplying the reciprocal by the dividend.   # p.177
choices:
  iterations: UNKNOWN   # p.177
  dedicated_multiplier: UNKNOWN   # p.177
  internal_guard_bits: UNKNOWN   # p.177
new_choices:
  none
slots:
  seed: UNKNOWN   # p.177
  iter_mult: UNKNOWN   # p.177
  final_round: UNKNOWN   # p.177
parameters: initial approximation b0 lies between 0 and 10/x   # p.177
results:
| metric | value | unit | technology / device | baseline | condition | page |
|---|---:|---|---|---|---|---|
| significant-digit growth | roughly doubled after each application | significant digits | abstract | preceding approximation | reasonable initial approximation | p.177 |
errors_and_checks: none
conditions: The iteration permits omission of a hardware dividing unit when division frequency/speed/programming requirements allow reciprocal calculation through addition/subtraction/multiplication.   # p.177
evidence: reciprocal-iteration discussion   # p.177

## taxonomy
* Binary multiplication   # p.147
  * simultaneous multiplier -> carry_save_array   # p.149
  * multiplication by accumulation   # p.151
    * parallel, shift multiplicand -> sequential_shift_add   # p.152
    * parallel, shift accumulated sum -> sequential_shift_add   # p.154
    * high-speed asynchronous add-and-shift -> sequential_shift_add   # p.159
    * fully serial delay-storage multiplier -> serial_serial_parallel   # p.163
  * serial-parallel multiplier   # p.166
    * one-bit serial factor -> serial_serial_parallel   # p.166
    * multiplier digits grouped by 2 -> serial_serial_parallel   # p.168
    * both factors grouped by 2, 3, 4, or more -> serial_serial_parallel   # p.169
  * expanded-accuracy multiplication by operand partitioning -> unmapped programming method   # p.171
  * negative-factor multiplication   # p.172
    * true-form/sign comparison -> sequential_shift_add   # p.172
    * twos-complement corrective terms -> sequential_shift_add   # p.172
    * adjacent multiplier-digit add/subtract recoding -> adjacent_bit_recoded_multiplier   # p.175
* Binary division   # p.177
  * reciprocal iteration   # p.177
    * second order -> newton_raphson   # p.177
    * third order -> higher_order_reciprocal_iteration   # p.177
  * negative-remainder handling   # p.180
    * subtract then add back -> restoring_nonrestoring   # p.180
    * shifted add/subtract without immediate restoration -> restoring_nonrestoring   # p.181
    * compare before conditional subtraction -> restoring_nonrestoring   # p.182
  * result rounding   # p.185
    * add one in highest discarded order -> binary_result_rounding   # p.186
    * force lowest retained digit to 1 -> binary_result_rounding   # p.186
    * conditionally increment lowest retained digit -> binary_result_rounding   # p.186
    * randomly add 0 or 1 -> binary_result_rounding   # p.187

## primary_sources
none

## new_families
### adjacent_bit_recoded_multiplier  (domain: mul: integer multipliers, closest: sequential_shift_add, why_not: the existing Booth-recoded family excludes radix-2 adjacent-bit recoding and assumes parallel partial-product reduction)
mechanism: Each multiplier digit is examined with its next lower-order digit. A 10 transition subtracts the multiplicand, a 01 transition adds it, and equal adjacent digits perform neither operation. Sign digits participate as the highest-order digits, so the same process handles positive and negative twos-complement factors.   # p.175, p.176
choices: transition_action: {10_subtract, 01_add, equal_no_operation}; signed_representation: {twos_complement}
results:
| metric | value | unit | technology / device | baseline | condition | page |
|---|---:|---|---|---|---|---|
| recoding inspection window | 2 | adjacent multiplier digits | abstract | one multiplier digit | each multiplication step | p.175 |
evidence: p.175, p.176

### higher_order_reciprocal_iteration  (domain: div: dividers / square root, closest: newton_raphson, why_not: the chapter distinguishes a third-order recurrence from the second-order reciprocal recurrence)
mechanism: The recurrence bK+1 = bK:[11(1 - xbK) + (xbK)10] forms successive reciprocal approximations using addition/subtraction/multiplication. Division multiplies the resulting reciprocal by the dividend.   # p.177
choices: order: {3}; initial_approximation_interval: {0_to_10_over_x}
results:
| metric | value | unit | technology / device | baseline | condition | page |
|---|---:|---|---|---|---|---|
| significant-digit growth | roughly tripled after each application | significant digits | abstract | preceding approximation | reasonable initial approximation | p.177 |
evidence: p.177

### binary_result_rounding  (domain: other, closest: shift_round_convert, why_not: shift_round_convert covers format conversion rather than multiplier/divider result rounding)
mechanism: A product or quotient is shortened by incrementing from the highest discarded order, forcing the lowest retained digit to 1, conditionally incrementing that retained digit, or adding a random 0/1 at the retained boundary. Complement representations require direction-sensitive handling.   # p.185, p.186, p.187
choices: method: {discarded_bit_increment, force_retained_lsb_one, conditional_retained_lsb_increment, random_retained_lsb_increment}; negative_handling: {convert_to_true, ones_complement_subtract}
results:
| metric | value | unit | technology / device | baseline | condition | page |
|---|---:|---|---|---|---|---|
| force-one maximum error | twice as great as the discarded-bit increment method | error | abstract | discarded-bit increment | force retained LSB to 1 | p.186 |
| random method error range | 00001111 too low to 00010000 too high | binary quantity | abstract | exact result | illustrated retained width | p.187 |
errors_and_checks: The force-one procedure aims for equal probability above/below the exact result but can never produce zero. Random increment makes computations difficult or impossible to repeat exactly.   # p.186, p.187
evidence: p.185, p.186, p.187

## space_gaps
* sequential_shift_add lacks a shift-register/storage slot for direct static, intermediate-storage, dynamic-pulse, delay-line, cathode-ray-tube, and magnetic-drum implementations.   # p.156, p.157, p.158, p.162, p.163
* carry_save_array lacks the chapter's partial-product combination choice among paired, successive, and columnwise half/full-adder arrangements.   # p.149, p.151
* The multiplier vocabulary lacks adjacent-bit radix-2 signed recoding.   # p.175, p.176
* The divider vocabulary lacks the stated third-order reciprocal iteration.   # p.177
* The vocabulary lacks binary multiplier/divider result-rounding mechanisms.   # p.185, p.186, p.187

## open_questions
* The chapter gives no general method for determining the actual maximum path through an arbitrary-width simultaneous multiplier.   # p.151
* The chapter suspects that a divider corresponding closely to the serial-parallel multiplier is impossible but gives no proof.   # p.185
* The nonrestoring final-remainder correction may require addition or subtraction, and the chapter does not give a general selection rule.   # p.181
