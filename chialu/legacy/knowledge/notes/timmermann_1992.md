---
handle: timmermann_1992
citation: D. Timmermann, H. Hahn, B. J. Hosticka, "Low Latency Time CORDIC Algorithms", IEEE Transactions on Computers, vol. 41, no. 8, pp. 1010-1015, 1992
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [redundant_binary, carry_save]
authority: incremental
pages_read: 6 / 6
---

## summary
The paper proposes constant-scale-factor, parallel direction-prediction, termination, and modified-Booth methods that reduce CORDIC latency and hardware for redundant array/pipeline implementations (pp.1010-1014). The prediction-based methods apply to rotation mode and report latency reductions of about 30% to 60% relative to a conventional carry-save CORDIC array (p.1014).

## families
### cordic  (role: extends)
mechanism: The prediction scheme recodes the binary bits of the residual angle z into signed rotation directions in parallel instead of determining each direction after the preceding iteration. Circular/hyperbolic prediction applies the recoding over bounded iteration intervals and repeats the final iteration to correct the bounded approximation error. A generalized termination method replaces the second half of rotation iterations with two parallel multiplications. Modified Booth recoding ensures that each direction pair contains at least one zero, so paired iterations suppress redundant forward/reverse rotations (pp.1011-1014).
choices:
  mode: rotation   # pp.1011-1014
  coordinate_set: unified   # pp.1010-1012
  topology: unrolled_pipelined   # pp.1010, 1012
  scale_compensation: constant_multiplier   # p.1014
  angle_recoding: true   # pp.1013-1014
new_choices:
  direction_generation: parallel_residual_recoding — rotation directions are generated in parallel from the bits of z   # pp.1011-1012
  late_iteration_replacement: generalized_termination — the second half of rotation iterations is replaced by two parallel multiplications   # p.1013
  direction_recoding: modified_booth — adjacent directions are recoded so each pair contains at least one zero   # pp.1013-1014
slots:
  none
parameters: n-bit precision; approximately n conventional iterations; prediction intervals j through 3j+1; about log_3(n)-1 redundant-to-binary conversions; illustrated architecture has n=39-bit accuracy   # pp.1010, 1012
results:
| metric | value | unit | technology / device | baseline | condition | page |
| latency | 2[n + log_3(n) - 1] + log_2(n) | full-adder delay τ | UNKNOWN (1992) | conventional carry-save array: 3n + log_2(n) τ | prediction architecture; scale-factor compensation excluded | p.1013 |
| latency reduction | about 30 | % | UNKNOWN (1992) | fastest conventional carry-save CORDIC array known to the authors | prediction algorithm; scale-factor compensation excluded | p.1014 |
| speedup | 60 | % | UNKNOWN (1992) | fastest conventional carry-save CORDIC array known to the authors | prediction plus termination; scale-factor compensation excluded | p.1014 |
| speedup | 50 | % | UNKNOWN (1992) | fastest conventional carry-save CORDIC array known to the authors | prediction plus modified Booth encoding; scale-factor compensation excluded | p.1014 |
| chip-area saving | up to 25 | % | UNKNOWN (1992) | conventional carry-save CORDIC realization | parallelized methods | p.1014 |
errors_and_checks: For circular/hyperbolic prediction, repetition of iteration k corrects the bounded prediction error and guarantees k leading zeros when the error is at most 2^-S(m,k)   # p.1012
conditions: Parallel direction prediction applies only to rotation mode; the paper leaves extension to vectoring mode for future work (pp.1013-1014). The x/y recurrences remain sequential because direct parallelization would require matrix multipliers rather than shifts/additions (pp.1012-1013). The reported Fig. 2 comparison excludes scale-factor compensation and accepts reduced layout regularity (p.1014).
evidence: Sections III-IV; Tables I-IV; Figs. 1-2; pp.1011-1014

### redundant_high_radix_cordic  (role: extends)
mechanism: The constant-scale-factor method permits a zero rotation direction when MSD inspection cannot choose a sign. A zero direction triggers an iteration-dependent increase or decrease in vector length during the middle iterations and freezes the vector during sufficiently late iterations. These operations retain a data-independent scale factor within n-bit accuracy. The implementation uses redundant additions, hard-wired shifts, and a multiplexer; the illustrated prediction architecture uses 4-to-2 cells in the x/y paths and 3-to-2 adders in the z path (pp.1010-1012).
choices:
  residual_arithmetic: carry_save   # pp.1010-1012
  radix: 2   # p.1010
  scale_handling: zero_direction_length_adjustment [outside domain]   # p.1011
new_choices:
  zero_direction_handling: iteration_dependent_length_adjustment — σ_i=0 changes vector length in middle iterations and freezes the vector in late iterations while preserving a constant scale factor   # p.1011
slots:
  none
parameters: p inspected MSDs with p much less than n; p should not exceed about four or five digits; regular iterations for 0 through (n-3)/4; length-adjusting iterations through (n+1)/2; about (9n-3)/8 iterations   # pp.1010-1011
results:
| metric | value | unit | technology / device | baseline | condition | page |
| iterations | (9n-3)/8 | iterations | UNKNOWN (1992) | at least 3n/2 iterations | constant-scale-factor redundant CORDIC using the earlier method for the first (n-3)/4 iterations | p.1011 |
| latency | (9n-3)/4 | full-adder delay τ | UNKNOWN (1992) | 3n τ | constant-scale-factor redundant CORDIC | p.1011 |
| speedup | about 25 | % | UNKNOWN (1992) | redundant constant-scale-factor method without the proposed length adjustment | constant-scale-factor method | p.1011 |
| chip-area saving | about 25 | % | UNKNOWN (1992) | redundant constant-scale-factor method without the proposed length adjustment | constant-scale-factor method | p.1011 |
errors_and_checks: The late-iteration scale-factor simplifications hold within n-bit machine accuracy   # p.1011
conditions: MSD inspection should remain faster than the redundant iteration addition, so p should not exceed about four or five digits (p.1011). The method targets spatial-array or pipelined implementations (p.1010).
evidence: Section II; Fig. 1; pp.1010-1012

## new_families
none

## space_gaps
* The cordic family lacks a direction-generation choice for sequential sign selection versus parallel residual recoding (pp.1011-1012).
* The cordic family lacks a late-iteration termination/replacement choice for parallel multiplication (p.1013).
* The redundant_high_radix_cordic scale_handling domain lacks iteration-dependent vector-length adjustment for zero rotation directions (p.1011).

## open_questions
* The paper does not quantify the multiplier area required by the generalized termination method.
* Fig. 2 does not include scale-factor compensation, so total compensated latency is not reported for the plotted methods (p.1014).
