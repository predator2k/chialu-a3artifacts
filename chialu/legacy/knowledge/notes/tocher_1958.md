---
handle: tocher_1958
citation: Tocher, "Techniques of Multiplication and Division for Automatic Binary Computers", Quarterly Journal of Mechanics and Applied Mathematics, 1958
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary_integer, ones_complement, twos_complement]
authority: landmark
pages_read: 364-384 / 21
---

## summary
The paper develops a minimal signed-digit representation for reducing additions/subtractions in binary multiplication. The paper applies the representation to sequential/serial multipliers and a division recurrence that produces two or three quotient digits per cycle. The paper also compares restoring and non-restoring division.

## families
### generalized_signed_digit  (role: proposes)
mechanism: A binary integer is represented as a sum of signed powers with digits encoded by binary magnitude \(d_r\) and sign \(s_r\). The minimal representation places a non-zero digit only when adjacent binary digits differ and the preceding signed digit is zero, so two successive signed digits cannot both be non-zero. The encoding extends to positive/negative operands in ones' and twos' complement.
choices:
  radix: 2   # p.367-p.369
  digit_encoding: sign_magnitude   # p.367-p.369
new_choices:
  canonical_digit_rule: minimal_nonadjacent — a non-zero digit occurs when adjacent binary digits differ and the preceding signed digit is zero   # p.369-p.370
slots:
  none
parameters: signed digit set {-1, 0, 1}; three multiplier digits and the preceding d digit determine each recoded digit   # p.369-p.370
results:
| metric | value | unit | technology / device | baseline | condition | page |
| non-zero digit density | ~1/3 | digits per input digit | UNKNOWN; 1958 | ordinary binary average 1/2 | uniformly distributed long binary numbers | p.372 |
| digit-count saving | 33 per cent | digits | UNKNOWN; 1958 | ordinary binary representation | large n | p.372 |
| maximum non-zero digits | half the number of digits | digits | UNKNOWN; 1958 | ordinary binary representation | minimal representation | p.364, p.370 |
errors_and_checks: exact representation; no approximation or fault checking   # p.367-p.370
conditions: The recoder requires three multiplier digits and storage of the preceding d digit (p.370). The complement systems require the stated boundary/sign extension rules (p.378-p.381).
evidence: §§4-6 and §10, equations (14)-(16), (21), (53)-(68)

### sequential_shift_add  (role: extends)
mechanism: A multiplier and partial product circulate while one multiplier digit controls an add-and-shift or shift-only step. Zero strings can be skipped with adjustable delays. Minimal signed-digit recoding replaces additions for binary ones with additions/subtractions for non-zero signed digits and permits a double shift after every operation.
choices:
  bits_per_cycle: 1   # p.365
  accumulator_form: carry_propagate   # p.365
  string_skipping: true   # p.365-p.366
new_choices:
  multiplier_recoding: minimal_signed_digit — controls add/subtract/shift-only actions with {-1,0,1} digits   # p.366-p.370
slots:
  step_adder: UNKNOWN   # p.365-p.366
parameters: n-digit multiplier; about n cycle times for the basic design; adjustable shift distance for zero chains   # p.365
results:
| metric | value | unit | technology / device | baseline | condition | page |
| multiplication time | about n | cycle times | UNKNOWN; 1958 | original design: 2n machine cycles | simple circulating-register multiplier | p.365 |
| average multiplication time | 1/2 n | cycles | UNKNOWN; 1958 | about n cycles | zero-chain skipping; all n-digit numbers equally likely | p.366 |
| average multiplication-time reduction | 33 per cent | time | UNKNOWN; 1958 | binary non-zero-digit operation count | minimal signed-digit recoding; large n | p.372 |
errors_and_checks: exact multiplication; no fault checking   # p.365-p.372
conditions: Shift time and operand complementation must be negligible relative to addition time for operation count to approximate multiplication time (p.367). Multiple-input parallel adders are excluded because their cost is considered prohibitive (p.367).
evidence: §§2-6, especially pp.365-367 and equations (15)-(21)

### serial_serial_parallel  (role: proposes)
mechanism: A serial multiplier places p adder-subtractors in the circulating partial-product path. Each input receives fixed delayed versions of the multiplicand, while signed multiplier digits control the input gates and add/subtract functions. Adjacent multiplier positions must be paired to ensure at most one non-zero signed digit reaches each input.
choices:
  digit_size_bits: 1   # p.365-p.366
new_choices:
  input_adder_count: p — p chained adder-subtractors process several multiplier positions in one circulation   # p.366
  position_pairing: adjacent_pairs — positions 2r and 2r+1 must share an input   # p.374-p.376
  multiplier_recoding: scale_four_short_cut — paired-bit recurrence enforces at most one non-zero digit per input   # p.376-p.381
slots:
  none
parameters: p adder-subtractors; p multiplier digits handled per cycle in the unreduced scheme; adjacent pairs assigned to fixed inputs   # p.365-p.366, p.376
results:
| metric | value | unit | technology / device | baseline | condition | page |
| hardware for p digits per cycle | p | adders | UNKNOWN; 1958 | one circulating adder | chained multi-input construction | p.365 |
| all-multiples alternative hardware | 2^(p-1) | adders | UNKNOWN; 1958 | p adders | precompute and select all required multiples | p.365-p.366 |
| multiplier length handled as one operation | 2p | digits | UNKNOWN; 1958 | UNKNOWN | p adders with modified-ternary encoding | p.364 |
| guaranteed representable width | 2p-1 | digits | UNKNOWN; 1958 | UNKNOWN | at most p non-zero digits; some 2p-digit values also qualify | p.374 |
errors_and_checks: exact multiplication; no fault checking   # p.364-p.381
conditions: Adjacent-pair allocation is necessary when each input may accept only one non-zero digit (p.374-p.376). The scale-four short-cut recurrence is the sign-independent scheme for twos-complement negative multipliers (p.380-p.381).
evidence: §§2 and 7-10, equations (33)-(50) and (68)

### restoring_nonrestoring  (role: compares)
mechanism: Restoring division performs a trial subtraction for each quotient position and restores negative residuals. Non-restoring division instead adds or subtracts the divisor at every position, so each quotient digit costs one addition time.
choices:
  style: restoring   # p.381
  bits_per_cycle: 1   # p.381
new_choices:
  none
slots:
  residual_adder: UNKNOWN   # p.381
parameters: n-digit operands; n trial subtractions for restoring division; n add/subtract steps for non-restoring division   # p.381
results:
| metric | value | unit | technology / device | baseline | condition | page |
| restoring division time | 3/2 n | addition times | UNKNOWN; 1958 | none | n trials plus an average of 1/2 n corrections | p.381 |
| non-restoring division time | n | addition times | UNKNOWN; 1958 | restoring: 3/2 n | every division | p.381 |
errors_and_checks: exact quotient recurrence; no fault checking   # p.381-p.382
conditions: Ordinary non-restoring division uses a non-zero signed quotient digit at every position (p.381-p.382).
evidence: §11, equations (69)-(75)

## new_families
### minimal_weight_signed_digit_division  (domain: dividers / square root, closest: restoring_nonrestoring, why_not: the recurrence permits add/subtract/no-operation digits and variable multi-digit advancement rather than one mandatory trial per quotient bit)
mechanism: The divider represents the quotient with minimal nonadjacent digits {-1,0,1}. After an addition or subtraction, the residual shifts until its magnitude first exceeds half the divisor, which determines when the next non-zero digit is generated. A serial implementation evaluates several candidate residuals in parallel and selects the correctly signed residual from inspected sign digits, producing two or three ordinary quotient digits per cycle.
choices: quotient_encoding: {minimal_signed_digit}; digits_per_cycle: {2, 3}; residual_change_threshold: {half_divisor}; candidate_generation: {parallel_add_subtract}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| quotient production | 2 | digits per cycle | UNKNOWN; 1958 | non-restoring: 1 digit per addition time | trebling adder and parallel candidate residuals | p.383-p.384 |
| quotient production | 3 | digits per cycle | UNKNOWN; 1958 | two-digit implementation | additional candidate adders | p.384 |
| two-digit candidate hardware | 1 trebling adder + 4 adder-subtractors | arithmetic units | UNKNOWN; 1958 | UNKNOWN | serial implementation | p.383-p.384 |
evidence: §11, equations (76)-(79), pp.382-384

## space_gaps
* `generalized_signed_digit` lacks a choice for canonical minimal/nonadjacent signed-digit recoding (p.369-p.370).
* `sequential_shift_add` lacks a multiplier-recoding choice for exact {-1,0,1} minimal-digit control (p.366-p.370).
* `serial_serial_parallel` lacks input-adder count and fixed multiplier-position allocation choices (p.365-p.366, p.374-p.376).
* The divider vocabulary lacks the minimal-weight signed-digit recurrence with add/subtract/no-operation actions and two/three-digit serial advancement (p.381-p.384).

## open_questions
* The paper does not identify the circuit family or topology of its ordinary adders/adder-subtractors.
* The paper does not report technology, area, power, clock period, or fabricated measurements.
* The claimed average half-width digit count for the proposed parallel-division rule is explicitly conjectural and based on a “dubious hypothesis,” so it is not a result (p.384).
