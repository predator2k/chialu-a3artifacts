---
handle: parhami_1993
citation: Parhami, "On the Implementation of Arithmetic Support Functions for Generalized Signed-Digit Number Systems", IEEE Transactions on Computers, 1993
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [generalized_signed_digit]
authority: landmark
pages_read: 6 / 6
---

## summary
The paper extends generalized signed-digit arithmetic with propagation-free/limited-propagation subtraction, borrow-free negation, zero/sign detection, and overflow handling. The algorithms cover asymmetric digit sets {-α, ..., β} in radix r and include conditions that determine when transfers can be eliminated or bounded.

## families
### generalized_signed_digit  (role: extends)
mechanism: A GSD system uses radix r and digit set {-α, -α+1, ..., β-1, β}, where α ≥ 0, β ≥ 0, and ρ = α+β+1-r is the redundancy index. Addition/subtraction decomposes each position sum/difference into a transfer digit and an interim digit. Fully propagation-free cases compute each output position independently; exceptional cases use a two-stage range estimate that limits dependence to two lower operand positions. Separate right-to-left scans perform zero/sign detection and distinguish apparent from real overflow. # p.379-383
choices:
  radix: r >= 2 [outside domain]   # p.379-380
  redundancy: minimal, intermediate, maximal   # p.379-380
  addition_scheme: carry_free, two_stage_limited_carry   # p.379-380
new_choices:
  digit_set_bounds: α >= 0, β >= 0, ρ = α+β+1-r >= 1 — specifies asymmetric GSD digit values and redundancy   # p.379
  subtraction_scheme: propagation_free, limited_propagation — selects Algorithm 1 or Algorithm 3 according to the GSD parameters   # p.379-380
slots:
  none
parameters: k-digit operands; radix r; digit set {-α, ..., β}; redundancy index ρ; propagation-free subtraction uses one local transfer stage; limited-propagation subtraction uses two stages and binary range estimate e_i ∈ {l,h}   # p.379-380
results:
| metric | value | unit | technology / device | baseline | condition | page |
| dependency for limited-propagation sum/difference digit | x_i, y_i, x_(i-1), y_(i-1), x_(i-2), y_(i-2) | operand digits | UNKNOWN | propagation-free GSD arithmetic | exceptional GSD cases | p.379 |
| transfer values for negation | 0 or 2 | distinct values | UNKNOWN | general GSD negation | 0 when α = β mod(r-1); otherwise 2 suffice | p.381 |
errors_and_checks: Arithmetic is exact; the paper supplies zero/sign tests and real-overflow detection rather than numerical-error or fault-coverage measurements. # p.382-384
conditions: Propagation-free addition/subtraction applies iff r > 2 and either ρ >= 3 or ρ = 2 with α != 1 and β != 1. # p.380 Limited-propagation addition/subtraction applies to every GSD system. # p.380 Zero has a unique k-digit all-zero representation iff k = 1, α = 0, β = 0, or max(α,β) < r. # p.382 The most significant nonzero digit gives the sign iff max(α,β) < r. # p.382 Conversion/reconversion overhead must be amortized over a long operation sequence, as in signal processing or high-precision scientific computation. # p.384
evidence: §II, Algorithms 1-5 and Theorems 1-5, pp.379-380; Table I, p.380; §III-VI, pp.381-384

## new_families
### gsd_negation  (domain: redundant: signed-digit arithmetic, closest: generalized_signed_digit, why_not: generalized_signed_digit has no choice or slot for unary sign change on asymmetric digit sets)
mechanism: Negation decomposes each position negate -y_i into transfer t_(i+1) and interim negate v_i = -y_i + r t_(i+1), followed by n_i = v_i - t_i. The operation is always borrow-free. Transfer generation disappears exactly when α = β mod(r-1); otherwise two transfer values suffice and a comparison constant C selects between them. # p.381
choices: transfer_generation: {none, two_valued}; comparison_selection: {constant_threshold}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| transfer-value count | 0 | values | UNKNOWN | two-valued transfer negation | α = β mod(r-1) | p.381 |
| transfer-value count | 2 | values | UNKNOWN | transfer-free negation | α != β mod(r-1) | p.381 |
evidence: Algorithm 5, Lemmas 4-5, Theorems 6-7, Fig. 1, and Table II, pp.381-382

### gsd_zero_sign_detection  (domain: redundant: signed-digit arithmetic, closest: generalized_signed_digit, why_not: generalized_signed_digit does not represent support circuits for interpreting redundant digit strings)
mechanism: Zero detection scans from right to left while propagating a transfer and a Boolean divisibility signal. Sign detection uses a related scan whose state records positive/zero/negative. Algorithm 9 combines both functions with a three-valued state. Transfer-skip and transfer-lookahead can accelerate the scans in the same manner as carry-skip and carry-lookahead. # p.382-383
choices: function: {zero, sign, combined}; scan: {sequential, transfer_skip, transfer_lookahead}; state: {boolean, three_valued}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| combined test-state cardinality | 3 | values | UNKNOWN | separate zero/sign scans | combined Algorithm 9 | p.383 |
evidence: Algorithms 7-9, Theorems 8-9, Tables III-IV, pp.382-383

### gsd_overflow_handling  (domain: redundant: signed-digit arithmetic, closest: generalized_signed_digit, why_not: generalized_signed_digit does not distinguish apparent overflow from representability failure)
mechanism: A nonzero outgoing transfer denotes apparent overflow, but the result may still have a k-digit representation. Algorithm 10 scans right to left to determine whether overflow is real. Algorithm 11 rewrites a nonreal-overflow result into k digits and may terminate when its correction transfer becomes zero. Hardware may instead retain a guard digit or defer handling to software. # p.383-384
choices: detection: {outgoing_transfer_only, real_overflow_scan}; recovery: {guard_digit, software_exception, correction_scan}; correction_termination: {full_scan, transfer_zero_early_stop}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| transfer magnitude bound | 1 + floor((ρ-1)/r) | digit values | UNKNOWN | unrestricted correction transfer | Algorithms 10-11 | p.383-384 |
evidence: Algorithms 10-11, Eq. (18)-(21), and Table V, pp.383-384

## space_gaps
* generalized_signed_digit lacks α/β digit-set bounds and the redundancy index ρ, which determine propagation, negation, and detection behavior. # p.379-382
* The vocabulary lacks unary GSD negation and combined zero/sign interpretation slots. # p.381-383
* The vocabulary lacks apparent-overflow detection, real-overflow testing, and redundant-result correction choices. # p.383-384

## open_questions
* The paper does not specify a transistor-level digit encoding or report technology/timing/area/power measurements.
* The paper notes conversion/reconversion overhead but does not provide converter implementations or measured costs. # p.379, p.384
