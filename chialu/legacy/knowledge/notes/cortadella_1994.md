---
handle: cortadella_1994
citation: Cortadella, Lang, "High-Radix Division and Square-Root with Speculation", IEEE Transactions on Computers, 1994
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary54]
authority: landmark
pages_read: 919-931 / 13
---

## summary
The paper speculates high-radix result digits and checks the resulting residual against its required bounds, which permits a shorter cycle and correction after an incorrect speculation. Partial advance produces some quotient bits after a small speculation error rather than rolling back completely. The method supports separate or combined division/square-root units and yields a radix-512 divider that is 1.4 times faster than the fastest conventional design evaluated. # p.919, p.921, p.926

## families
### self_timed_variable_latency  (role: proposes)
mechanism: A simplified function speculates each result digit, and the recurrence immediately uses that digit. A conservative bound comparison accepts a full advance when the next residual is valid. An incorrect speculation causes incremental digit correction/rollback or a fixed partial advance when the error is small enough. The bound check overlaps speculation of the next digit, so execution requires a variable number of cycles. # p.919-p.924
choices:
  mechanism: speculation_rollback   # p.919-p.921
new_choices:
  incorrect_speculation_action: {rollback_correction, fixed_partial_advance} — selects complete correction or production of fewer bits than a full digit after an error   # p.919, p.921
  speculation_function: {reduced_input_table, reduced_output_set, approximate_arithmetic_function} — selects how quotient-digit selection is simplified   # p.922-p.923
slots:
  digit_select: qds_table   # p.922-p.923
parameters: 54-bit divider evaluations; fixed partial advance of log2(p) bits; radix-512 implementation uses p = 6 and averages 1.17 cycles/digit   # p.921, p.924-p.927
results:
| metric | value | unit | technology / device | baseline | condition | page |
| average cycles per digit | 1.14 | cycles/digit | 1-µm standard cell CMOS library; 1994 | UNKNOWN | radix 32, partial advance 3 bits, 54-bit divider | p.925 |
| delay per quotient bit | 7.8 | τ | 1-µm standard cell CMOS library; 1994 | UNKNOWN | radix 32, partial advance 3 bits, 54-bit divider | p.925 |
| average cycles per digit | 1.21 | cycles/digit | 1-µm standard cell CMOS library; 1994 | UNKNOWN | radix 64, partial advance 4 bits, 54-bit divider | p.925 |
| delay per quotient bit | 7.2 | τ | 1-µm standard cell CMOS library; 1994 | UNKNOWN | radix 64, partial advance 4 bits, 54-bit divider | p.925 |
| average cycles per digit | 1.17 | cycles/digit | 1-µm standard cell CMOS library; 1994 | UNKNOWN | radix 512, partial advance 6 bits, 54-bit divider | p.925, p.927 |
| cycle delay | 43.8 | τ | 1-µm standard cell CMOS library; 1994 | UNKNOWN | radix 512, partial advance 6 bits, 54-bit divider | p.925 |
| delay per quotient bit | 5.6 | τ | 1-µm standard cell CMOS library; 1994 | UNKNOWN | radix 512, partial advance 6 bits, 54-bit divider | p.925 |
| speedup | 1.4 | times | 1-µm standard cell CMOS library; 1994 | fastest conventional design, radix-16 with two overlapped radix-4 stages | radix-512 division with partial advance | p.926, p.931 |
| area factor | 3.4 | factor | 1-µm standard cell CMOS library; 1994 | conventional radix-2 divider | radix-512, partial advance 6 bits | p.925 |
| total area | about 10500 | two-input NAND gates | 1-µm standard cell CMOS library; 1994 | UNKNOWN | radix-512 divider including two speculation modules/comparators/quotient conversion/rounding | p.927 |
errors_and_checks: Correctness is checked conservatively by comparing truncated residual/divisor estimates against bounds. Conservative rejection can classify a correct speculation as incorrect, but an accepted residual satisfies the required bound. Incorrect digits are corrected incrementally until the residual is valid. No fault-detection coverage or numerical-error rate is reported. # p.923-p.924
conditions: Variable execution time requires system support that can use variable latency and control dependencies. Results assume uniformly distributed operands. Fan-in/fan-out capacitances are included in delay estimates, but routing is excluded. Speculation without partial advance does not beat the fastest conventional design evaluated. # p.919, p.925-p.926
evidence: Fig. 2-Fig. 9; Table II-Table V; §II-§V, p.920-p.926; Fig. 11-Fig. 13 and §VI-B, p.926-p.928

### srt_high_radix  (role: extends)
mechanism: The divider retains a signed-digit, carry-save residual recurrence but replaces exact high-radix quotient-digit selection with speculation. The radix-512 design approximates 1/d with four signed components, computes the residual product from most-significant components first, and extracts four overlapping quotient-digit components at different multiplier levels. Missing quotient values cause partial advance or correction. # p.919-p.920, p.927
choices:
  radix: 16, 32, 64 [outside domain], 512 [outside domain]   # p.925
new_choices:
  digit_selection_mode: {table_speculation, arithmetic_approximation} — chooses a reduced table for radix 16 or an approximate reciprocal-product function for radix 512   # p.925-p.927
  generated_digit_subset: Bool — permits omission of quotient values to reduce recurrence adders and selection delay   # p.923, p.927
slots:
  digit_select: qds_table   # p.920, p.922-p.923
parameters: radix-16 speculation uses a = 12; radix-512 speculation generates four overlapping digit components; radix-512 partial advance is 6 bits; quotient width is 54 bits   # p.924-p.927
results:
| metric | value | unit | technology / device | baseline | condition | page |
| total delay | 28.8 | τ | 1-µm standard cell CMOS library; 1994 | UNKNOWN | radix-16 speculation without partial advance | p.926 |
| total area | 4900 | cell area | 1-µm standard cell CMOS library; 1994 | UNKNOWN | radix-16 speculation without partial advance | p.926 |
errors_and_checks: The result is exact because residual-bound checks and repeated correction preserve convergence. The paper reports speculation probabilities, including 0.91/0.86/0.77 for selected reduced-input functions, rather than output numerical error. # p.923-p.924
conditions: High radix reduces iteration count only when simplified digit speculation compensates for selection complexity. Radix-512 arithmetic selection without partial advance provides no significant speed improvement, while partial advance reduces the error penalty. # p.925-p.926
evidence: Table II-Table VI; Fig. 10-Fig. 14; §III-§VI, p.922-p.929

### digit_recurrence_sqrt_combined  (role: extends)
mechanism: The combined unit shares result-digit speculation and residual hardware between division and square root. A retimed square-root recurrence postpones subtraction of the result-digit square term until the next cycle, which preserves the divider clock period. Initial square-root iterations use direct operand estimation and double-cycle updates until the postponed term no longer affects the truncated residual used for checking. # p.927-p.930
choices:
  radix: 512 [outside domain]   # p.930
  shared_with_division: true   # p.929-p.930
  on_the_fly_conversion: true   # p.927
new_choices:
  sqrt_recurrence_timing: {direct, retimed_postponed_square_term} — selects whether the result-dependent square term is subtracted in the current or next cycle   # p.929-p.930
slots:
  digit_select: qds_table   # p.927-p.930
parameters: radix 512; 8 operand bits produce an 8-bit initial result estimate; double-cycle iterations continue until 9 result bits are obtained; division averages 1.17 cycles/digit and square root averages 1.6 cycles/digit   # p.930
results:
| metric | value | unit | technology / device | baseline | condition | page |
| average cycles per digit | 1.6 | cycles/digit | 1-µm standard cell CMOS library; 1994 | division at 1.17 cycles/digit | retimed radix-512 combined division/square-root unit | p.930 |
| average cycles per digit | 1.3 | cycles/digit | 1-µm standard cell CMOS library; 1994 | UNKNOWN | hypothetical square-root unit without the retimed recurrence and with a longer cycle | p.930 |
| execution-time ratio | about 1.4 | times | 1-µm standard cell CMOS library; 1994 | division in the combined unit | square root, including double cycles and higher speculation-error rate | p.931 |
| division speed degradation | 0 | UNKNOWN | 1-µm standard cell CMOS library; 1994 | radix-512 division-only implementation | combined division/square-root hardware using retiming | p.930-p.931 |
errors_and_checks: Square-root correctness uses conservative residual-bound comparisons. Early iterations update the retimed residual before comparison so the postponed square term cannot invalidate acceptance. # p.929-p.930
conditions: The retimed design favors workloads in which division is more frequent than square root. The added square-root hardware does not lengthen the division critical path, but square root requires more cycles. # p.929-p.931
evidence: §VII, Fig. 15, p.927-p.930; §VIII, p.931

## new_families
none

## space_gaps
* `srt_high_radix.radix` should consider 64 and 512 because implemented speculative designs use both values. # p.925
* `digit_recurrence_sqrt_combined.radix` should consider 512 because the combined implementation uses radix 512. # p.930
* `self_timed_variable_latency` lacks choices for rollback-only versus fixed partial advance and for the speculation-function structure. # p.919, p.921-p.923
* `digit_recurrence_sqrt_combined` lacks a choice for retiming the result-dependent square term into the next cycle. # p.929-p.930

## open_questions
* Table IV reports normalized delay values using τ, but the document does not state a direct conversion from every reported τ value to ns.
* The paper evaluates normalized fractions and a 54-bit quotient, but it does not identify an integer or IEEE floating-point format.
