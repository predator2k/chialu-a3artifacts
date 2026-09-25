---
handle: freiman_1961
citation: Freiman, "Statistical Analysis of Certain Binary Division Algorithms", Proceedings of the IRE, 1961
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [binary_fixed_point]
authority: landmark
pages_read: p.91-p.103 / 13 pages
---

## summary
The paper applies regular Markov chains to nondeterministic nonrestoring binary division and derives steady-state averages for the quotient bits generated per iteration. It analyzes remainder normalization and selectable divisor multiples, then compares the predictions with simulations of 48-bit divisions. # p.91-p.99

## families
### restoring_nonrestoring  (role: analyzes)
mechanism: Each iteration adds or subtracts a divisor multiple from the partial remainder and then left-shifts the result until its magnitude is normalized to [0.5, 1.0). The shift length `s_j` determines how many quotient bits are generated. The multiple-divisor variant selects the available multiple closest in magnitude to the remainder. A regular Markov chain models successive remainder intervals and supplies the steady-state distribution and average shift length. # p.92-p.98
choices:
  style: nonrestoring   # p.92-p.93
  bits_per_cycle: variable 1..x_j [outside domain]   # p.93-p.94
  shift_over_zeros: true   # p.93
new_choices:
  remainder_normalization: every_iteration — each partial remainder is shifted into magnitude range [0.5, 1.0)   # p.93
  divisor_multiple_set: selectable normalized multiples — examples include `{1.0D}`, `{0.75D,1.0D,1.5D}`, and `{0.625D,1.0D,1.25D}`   # p.98-p.99
  quotient_generation_correction: add_01_and_invert_next_bit — handles a sign change after subtracting `0.75D` when only two normalization shifts apply   # p.99
slots:
  none
parameters: Positive normalized divisor/dividend; `s_j` ranges from 1 through the remaining quotient length `x_j`; simulations use 48-bit divisors/dividends, 48 quotient positions, 16 five-bit divisor prefixes, and `2^10` problems per prefix. # p.92-p.94, p.98
results:
| metric | value | unit | technology / device | baseline | condition | page |
| nominal shift average | 8/3 | quotient bits per iteration | UNKNOWN; 1961 | conventional one-bit nonrestoring | `{1.0D}`, unbounded shift, uniformly distributed normalized divisor/remainder | p.94 |
| nominal shift average | 2.66 | quotient bits per iteration | UNKNOWN; 1961 | none | `{1.0D}`, maximum shift `x=10` | p.94 |
| random-distribution shift average | 2.65 | quotient bits per iteration | UNKNOWN; 1961 | none | `D=3/5` | p.96 |
| steady-state shift average | 3.00 | quotient bits per iteration | UNKNOWN; 1961 | random-distribution value 2.65 | `D=3/5` | p.96 |
| steady-state shift average | `7D/(2-D)` | quotient bits per iteration | UNKNOWN; 1961 | none | `9/16<D<7/12` | p.96 |
| steady-state shift average | `31D/(8-3D)` | quotient bits per iteration | UNKNOWN; 1961 | none | `33/56<D<31/52` | p.96 |
| steady-state shift average | `3/(2D)` | quotient bits per iteration | UNKNOWN; 1961 | none | `17/28<D<3/4` | p.96 |
| steady-state shift average | `2D/(2D-1)` | quotient bits per iteration | UNKNOWN; 1961 | none | `3/4≤D<1` | p.96 |
| simulated first-iteration average | 2.675 | quotient bits per iteration | UNKNOWN; 1961 | nominal 2.666 | S-R-T simulation | p.98 |
| nominal shift average | 2.67 | quotient bits per iteration | UNKNOWN; 1961 | none | `{1.0D}` | p.99 |
| nominal shift average | 2.75 | quotient bits per iteration | UNKNOWN; 1961 | `{1.0D}` | `{1.0D,2.0D}` | p.99 |
| nominal shift average | 2.875 | quotient bits per iteration | UNKNOWN; 1961 | `{1.0D}` | `{0.5D,1.0D}` | p.99 |
| nominal shift average | 3.36 | quotient bits per iteration | UNKNOWN; 1961 | `{1.0D}` | `{0.75D,1.0D}` | p.99 |
| nominal shift average | 3.40 | quotient bits per iteration | UNKNOWN; 1961 | `{1.0D}` | `{0.85D,1.17D}` | p.99 |
| nominal shift average | 3.82 | quotient bits per iteration | UNKNOWN; 1961 | `{1.0D}` | `{0.75D,1.0D,1.5D}` | p.99 |
| nominal shift average | 3.87 | quotient bits per iteration | UNKNOWN; 1961 | `{1.0D}` | `{0.625D,1.0D,1.25D}` | p.99 |
| nominal shift average | 4.047 | quotient bits per iteration | UNKNOWN; 1961 | `{1.0D}` | `{0.75D,1.0D,1.25D}` | p.99 |
| simulated overall average | 2.53 | quotient bits per iteration | UNKNOWN; 1961 | nominal 2.67 | S-R-T, `2^14` random 48-bit divisions | p.99 |
| simulated overall average | 3.60 | quotient bits per iteration | UNKNOWN; 1961 | nominal 3.82 | `{0.75D,1.0D,1.5D}`, `2^14` random 48-bit divisions | p.99 |
| simulated second-iteration average | 3.80 | quotient bits per iteration | UNKNOWN; 1961 | nominal 3.82 | `{0.75D,1.0D,1.5D}` | p.99 |
| steady-state shift average | 2.67 | quotient bits per iteration | UNKNOWN; 1961 | none | `D=35/64` | p.102 |
errors_and_checks: none
conditions: The steady-state model requires enough iterations for the remainder distribution to approach steady state. # p.97, p.99 The existence construction assumes a rational divisor and a piecewise-continuous initial remainder distribution. # p.96-p.97 Normalized divisor multiples are effectively limited to `[0.5D,2.0D]`, and engineering considerations limit practical sets to two or three easily generated multiples. # p.98 The `{0.75D,1.0D,1.5D}` set is preferred over a nominally faster set because its quotient-generation correction is simpler. # p.99
evidence: Summary/Introduction and Examples 1-3, p.91-p.94; Fig. 1 and Tables I-III, p.94-p.99; Figs. 5-9, p.98-p.101; Appendices I-III and Table IV, p.101-p.103.

## new_families
none

## space_gaps
* `restoring_nonrestoring.bits_per_cycle` cannot express the variable `1..x_j` quotient bits produced by remainder normalization. # p.93-p.94
* `restoring_nonrestoring` lacks a choice for available divisor multiples, although the multiple set controls the reported iteration rate. # p.98-p.99
* `restoring_nonrestoring` lacks a choice for quotient-generation correction after a multiple subtraction and shorter-than-encoded normalization shift. # p.99

## open_questions
* The paper uses sign-plus-magnitude representation only for explanatory clarity, so the implemented residual-adder representation is not settled. # p.92
* The final Table II value for the `√(77/128)D,1.0D,√(53/32)D` multiple set is unclear in the supplied scan and conflicts with the accompanying maximum-value statement. # p.99
