---
handle: parhami_1990
citation: Parhami, "Generalized Signed-Digit Number Systems: A Unifying Framework for Redundant Number Representations", IEEE Transactions on Computers, 1990
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, other]
formats: [radix_r_gsd, binary_signed_digit, binary_stored_carry, binary_stored_carry_or_borrow, decimal]
authority: landmark
pages_read: 89-98 / 10
---

## summary
The paper defines generalized signed-digit number systems with consecutive, potentially asymmetric digit sets and unifies ordinary signed-digit/stored-carry/stored-borrow representations within that framework (pp.89-90). The paper derives necessary and sufficient conditions for carry-free addition and proves that a two-stage limited-carry method applies to every GSD system (pp.91-95). The framework also produces stored-carry-or-borrow/stored-double-carry/redundant-decimal representations (pp.96-97).

## families
### generalized_signed_digit  (role: proposes)
mechanism: A radix-r digit uses the consecutive set {-α, -α+1, ..., β}, where α ≥ 0, β ≥ 0, and α+β+1 > r. Addition first forms p_i=x_i+y_i, selects a transfer t_{i+1}, forms w_i=p_i-rt_{i+1}, and then produces s_i=w_i+t_i. Sufficient redundancy permits transfer selection without propagation. Other systems use a binary range estimate e_i that restricts t_i before a second transfer-selection stage, which bounds carry propagation to two stages (pp.89-95).
choices:
  radix: r >= 2 [outside domain]   # pp.90,92
  redundancy: minimal or non-minimal [outside domain]   # p.90
  digit_encoding: sign_magnitude, negative_positive_flags [outside domain], or one_hot   # p.96
  addition_scheme: carry_free or two_stage_limited_carry   # pp.90,93-95
new_choices:
  digit_bounds: α >= 0, β >= 0, α+β+1 > r — defines the asymmetric consecutive digit set {-α,...,β}   # p.89
  redundancy_index: ρ=α+β+1-r — quantifies redundancy beyond a conventional radix-r digit set   # p.90
  transfer_digit_range: {-λ,...,μ} — bounds the outgoing transfer selected from each position sum   # pp.91-92
  range_estimate: {none, binary_low_high} — distinguishes carry-free addition from two-stage limited-carry addition   # pp.93-95
  representation_subclass: {OSD, SC, SB, BSD_or_BSB, SCB, BSCB, SDC, HDD} — identifies the parameterized representations unified or introduced by the framework   # pp.90,95-97
slots:
  none
parameters: digit set {-α,...,β}; redundancy index ρ=α+β+1-r; transfer range {-λ,...,μ}; carry-free transfer set has at least ceil(ρ/(r-1))+2 values; limited-carry addition uses a binary estimate e_i∈{l,h}   # pp.89-94
results:
| metric | value | unit | technology / device | baseline | condition | page |
|---|---:|---|---|---|---|---|
| minimum transfer-digit set size | ceil(ρ/(r-1))+2 | values | UNKNOWN / 1990 | UNKNOWN | carry-free GSD addition | p.92 |
| adder depth | two | full-adder levels | UNKNOWN / 1990 | UNKNOWN | two unary-encoded BSC operands | p.95 |
| representation storage | 2 | bits per digit position | UNKNOWN / 1990 | BSC representation | BSD representation | p.96 |
| adder depth | two-stage | circuit | UNKNOWN / 1990 | conventional decimal representation | HDD digit set {0,1,...,15} | p.97 |
errors_and_checks: A 1-out-of-3 BSD encoding can provide complete unidirectional-error detection with relatively low additional hardware complexity; quantitative coverage/false-alarm results are not reported (p.96).
conditions: Carry-free addition is possible exactly when r>2 and ρ≥3 if α=1 or β=1, or when r>2 and ρ≥2 otherwise (p.92). Binary range estimation makes limited-carry addition applicable to every GSD system (pp.93-95). Overlap between valid transfer selections can simplify comparison logic, including the radix-8, α=7 example (pp.91,95). Redundant representation is most effective for long computation sequences or long operands because conversion cost is amortized (pp.89,97). Larger-magnitude digits can make multiplication/division harder, so new subclasses require application-specific evaluation (p.97). The practical treatment remains incomplete for subtraction/zero detection/sign testing (p.97).
evidence: Abstract; §§I-IX; Algorithms 1-5; Lemmas 1-3; Theorems 1-5; Figs. 1-5; pp.89-97.

## new_families
none

## space_gaps
* generalized_signed_digit.radix should admit arbitrary integer radices r≥2 rather than only {2,4,8,16} (pp.90,92).
* generalized_signed_digit needs digit_bounds/redundancy_index choices because asymmetric {-α,...,β} sets and ρ determine the addition properties (pp.89-92).
* generalized_signed_digit.digit_encoding should add negative_positive_flags for the BSD (n,p) encoding (p.96).
* generalized_signed_digit needs a representation_subclass choice for SC/SB/SCB/SDC/HDD variants produced by different α/β settings (pp.90,95-97).

## open_questions
* The paper defers detailed subtraction/zero-detection/sign-test implementations to a companion paper (p.97).
* The paper reports no technology-specific area/delay/power measurements (pp.89-98).
* The suitability of SDC/HDD and other new redundant decimal systems remains application-dependent or under investigation (p.97).
