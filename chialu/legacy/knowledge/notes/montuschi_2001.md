---
handle: montuschi_2001
citation: Ercegovac, Lang, Montuschi, "Very-High Radix Division with Prescaling and Selection by Rounding", IEEE Transactions on Computers, 1994
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary54, binary114]
authority: incremental
pages_read: 8 / 8
---

## summary
The document extends very-high-radix division by decomposing the effective radix as R=CB and selecting c additional quotient bits per iteration without increasing prescaling-factor complexity or iteration delay. The estimated implementation reduces area by up to 30% for 54-bit quotients and 35% for 114-bit quotients relative to unboosted VHR division at comparable execution time.

## families
### prescaled_very_high_radix  (role: extends)
mechanism: The divisor is prescaled for radix B, while the effective radix is R=CB with C=2^c. Each iteration selects the normal digit p[j+1] by rounding and concurrently selects a boosting digit s[j+1], producing q[j+1]=Cp[j+1]+s[j+1]. The residual remains in carry-save form. The s[j+1]z terms enter lower levels of an incomplete rectangular MAC tree, which overlaps their generation with rounding/recoding, multiple generation, and the first MAC levels. The final cycle postcorrects a negative residual and rounds the quotient. # pp.2-6
choices:
  bits_per_iteration: 9, 11, 14, 18 [18 outside domain]   # pp.1,7
  shared_scaling_multiplier: false   # pp.2-3
new_choices:
  boosting_radix: {4, 8} — C determines the additional quotient bits and added MAC terms   # pp.2,7
  radix_decomposition: R=CB, C=2^c, B=2^b — separates effective radix from prescaling radix   # p.2
  boosting_digit_set: -max(3C/4-1,1) <= s[j+1] <= C-1 — nonsymmetric radix-C digit set   # pp.3-4
  selection_estimate_precision: f,g,u — fractional bits of H/significant bits of E/most-significant weights of P   # pp.4-5
  scaling_factor_approximation: L-approach linear approximation — computes M for radix B   # p.7
slots:
  prescaler: none
  seed: none
parameters: 54-bit and 114-bit quotients; C=4 or C=8; 11<=b<=18; C=4 example uses f=3, g=3, u=4 and -2<=s[j+1]<=3; residual is carry-save; total cycles include scaling, operand scaling, recurrence, postcorrection, and rounding   # pp.2,5-7
results:
| metric | value | unit | technology / device | baseline | condition | page |
| cycle time | 7.5 / 9.0 / 9.0 / 9.0 | tfa | full-adder-normalized model; result year UNKNOWN | unboosted VHR | 9 / 11 / 14 / 18 quotient bits per iteration | p.1 |
| cycles | 10 / 9 / 8 / 7 | cycles | full-adder-normalized model; result year UNKNOWN | unboosted VHR | 54-bit quotient; 9 / 11 / 14 / 18 bits per iteration | p.1 |
| execution time | 75 / 81 / 72 / 63 | tfa | full-adder-normalized model; result year UNKNOWN | unboosted VHR | 54-bit quotient; 9 / 11 / 14 / 18 bits per iteration | p.1 |
| MAC area | 520 / 710 / 740 / 970 | Afa | full-adder-normalized model; result year UNKNOWN | unboosted VHR | 9 / 11 / 14 / 18 bits per iteration | p.1 |
| prescaling-factor-module area | 130 / 220 / 470 / 1750 | Afa | full-adder-normalized model; result year UNKNOWN | unboosted VHR | 9 / 11 / 14 / 18 bits per iteration | p.1 |
| selection-function delay | 3.6 | ns | Compass Passport 0.6 μm standard-cell library; result year UNKNOWN | none | C=4, f=3, g=3, u=4 | p.7 |
| selection-function delay | less than 4 | tfa | Compass Passport 0.6 μm standard-cell library; result year UNKNOWN | 4.5tfa available overlap | C=4, f=3, g=3, u=4 | p.7 |
| selection-function size | 320 | gates | Compass Passport 0.6 μm standard-cell library; result year UNKNOWN | none | C=4, f=3, g=3, u=4 | p.7 |
| selection-function area | about 30 | Afa | Compass Passport 0.6 μm standard-cell library; result year UNKNOWN | none | C=4, f=3, g=3, u=4 | p.7 |
| MAC plus prescaler area | 2000 | Afa | full-adder-normalized model; result year UNKNOWN | VHR 2800Afa | 54-bit quotient, log2R=18, C=4, 60tfa execution time | p.7 |
| area ratio | 0.70 | ratio | full-adder-normalized model; result year UNKNOWN | unboosted VHR | 54-bit quotient, log2R=18, C=4 | p.7 |
| MAC plus prescaler area | 2100 | Afa | full-adder-normalized model; result year UNKNOWN | VHR 2400Afa | 114-bit quotient, log2R=15, C=4, 110tfa | p.7 |
| MAC plus prescaler area | 2800 | Afa | full-adder-normalized model; result year UNKNOWN | VHR 3300Afa | 114-bit quotient, log2R=17, C=4, 100tfa | p.7 |
| MAC plus prescaler area | 3600 | Afa | full-adder-normalized model; result year UNKNOWN | VHR 5400Afa | 114-bit quotient, log2R=19, C=4, 90tfa | p.7 |
| MAC plus prescaler area | 1900 / 2100 / 2900 | Afa | full-adder-normalized model; result year UNKNOWN | VHR 2400 / 3300 / 5400Afa | 114-bit quotient, C=8, log2R=15 / 17 / 19 | p.7 |
| area ratio | 0.80 / 0.65 / 0.55 | ratio | full-adder-normalized model; result year UNKNOWN | unboosted VHR | 114-bit quotient, C=8, log2R=15 / 17 / 19 | p.7 |
| normalized speedup | 4 | times | full-adder-normalized model; result year UNKNOWN | classical radix-2, 260tfa and 460Afa | 54-bit VHR+boost, C=4, 6 times baseline hardware | p.8 |
| area reduction | about 30 | % | full-adder-normalized model; result year UNKNOWN | unboosted VHR with same delay | 54-bit quotient, C=4 | p.8 |
| area reduction | 25 / 35 | % | full-adder-normalized model; result year UNKNOWN | unboosted VHR | 114-bit quotient, C=4 / C=8 | p.8 |
| execution-time reduction | 10 | % | full-adder-normalized model; result year UNKNOWN | radix-2^17 VHR, 100tfa, about 3000Afa | radix-2^19 VHR+boost, C=8, about 3000Afa | p.8 |
errors_and_checks: The recurrence maintains -(1-3/(4B)) <= w[j+1] < 1-1/(2B); the last residual controls quotient postcorrection, but no numerical error rate or fault-detection coverage is reported. # pp.2-3
conditions: Boosting avoids a cycle-time increase only when s[j+1] selection/multiple generation overlaps existing MAC work and the added terms enter unused lower-level MAC slots. The evaluated tree requires 11<=b<=18 and two available second-level slots for the non-precomputed C=4/C=8 cases. Boosting mainly saves prescaling-factor area; it is not expected to improve speed at the same effective radix when prescaling-factor calculation is not critical. # pp.6-7
evidence: Sections 2-6; Figures 1-5; Tables 1-5; equations (1)-(32).

## new_families
none

## space_gaps
* `bits_per_iteration` should include 18 because the evaluated effective-radix configurations produce 18 quotient bits per iteration. # pp.1,7
* `prescaled_very_high_radix` lacks choices for the split R=CB, boosting radix C, boosting digit set, and selection-estimate precisions f/g/u. # pp.2-5
* The `prescaler`/`seed` slots do not represent the document's L-approach linear-approximation scaling-factor module. # pp.2,7
* `prescaled_very_high_radix` lacks a slot for the carry-save rectangular MAC/reduction tree whose unused lower-level slots determine whether boosting preserves cycle time. # pp.5-7

## open_questions
* The document text does not identify its venue or publication year.
* The document estimates C=8 timing without synthesizing the C=8 selection function. # p.7
* The exact prescaling-factor precision m is implementation-dependent and is not fixed for every evaluated radix. # pp.6-7
