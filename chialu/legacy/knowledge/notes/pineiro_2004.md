---
handle: pineiro_2004
citation: J.-A. Pineiro, M. D. Ercegovac, J. D. Bruguera, "Algorithm and Architecture for Logarithm, Exponential, and Powering Computation", IEEE Transactions on Computers, vol. 53, no. 9, pp. 1085-1096, 2004
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [fp32, fp64, fixed32]
authority: incremental
pages_read: 1085-1096 / 12
---

## summary
The document proposes a sequential unit that overlaps high-radix digit-recurrence logarithm, left-to-right carry-free multiplication, and online high-radix exponential to compute \(X^Y\). The unit also computes logarithm/exponential independently and extends powering to \(Y=1/q\). Area/delay estimates identify radix 32 for lower area and radix 128 for higher speed. (pp.1085-1095)

## families
### digit_recurrence_exp_log  (role: extends)
mechanism: The architecture evaluates \(X^Y=2^{Y\log_2(M_x)}2^{YE_x}\). A multiplicative digit recurrence produces \(\log_2(M_x)\), an MSDF LRCF multiplier produces \(Y\log_2(M_x)\), and an online additive recurrence produces \(2^F\). Signed-digit redundancy makes iteration additions independent of precision. The first logarithm/exponential digit uses table lookup, while later digits are selected by rounding a truncated residual. The three operations overlap in a sequential datapath. (pp.1086-1091)
choices:
  radix: 8..1,024 powers of two [outside domain]   # pp.1086,1091
  normalization: multiplicative for logarithm; additive for exponential [outside domain]   # pp.1088,1090
  digit_set: signed_redundant   # pp.1088-1091
  selection: table_lookup for iteration 1; rounding_of_scaled_residual for iterations j >= 2 [outside domain]   # pp.1088,1090
new_choices:
  online_delay: 2 — input digits precede exponential output digits by two cycles   # pp.1086,1090
  operation_set: {logarithm, exponential, integer_powering, qth_root} — operations supported by the complete or extended unit   # pp.1094-1095
  stage_composition: overlapped_log_lrcf_exp — the logarithm feeds an MSDF multiplication that feeds the online exponential   # pp.1086-1087
slots:
  none
parameters: \(n=24\) for single precision; \(n=53\) for double precision; fixed-point \(n=32\) comparison; \(r=2^b\), \(8 \le r \le 1,024\); residual truncation \(t=2\); exponential online delay \(\delta=2\); \(N_l=\lceil n_l/b\rceil\); \(N_e=\lceil n_e/b\rceil\); powering latency \(N_e+(\delta+1)+1+\beta\), with \(\beta=1\) for b-bit Y and \(\beta=2\) for 2b-bit Y   # pp.1087-1091,1093
results:
| metric | value | unit | technology / device | baseline | condition | page |
| execution time | about 100 | \(\tau\) | UNKNOWN / 2004 | none | fixed-point \(n=32\), proposed powering implementation | p.1093 |
| total area | 5,964 | fa | UNKNOWN / 2004 | none | fixed-point \(n=32\), proposed powering implementation | p.1093 |
| execution time | about 100 | \(\tau\) | UNKNOWN / 2004 | 120 \(\tau\), high-radix CORDIC at \(r=128\) | fixed-point \(n=32\) comparison | pp.1093-1094 |
| total area | 5,964 | fa | UNKNOWN / 2004 | about 6,000 fa, high-radix CORDIC at \(r=128\) | fixed-point \(n=32\) comparison | pp.1093-1094 |
| execution time | about 100 | \(\tau\) | UNKNOWN / 2004 | 115 \(\tau\), high-radix CORDIC at \(r=512\) | fixed-point \(n=32\) comparison | pp.1093-1094 |
| total area | 5,964 | fa | UNKNOWN / 2004 | about 18,000 fa, high-radix CORDIC at \(r=512\) | fixed-point \(n=32\) comparison | pp.1093-1094 |
| latency reduction | 1 | cycle | UNKNOWN / 2004 | earlier \(e^{Y\ln X}\) algorithm [19], [23] | \(2^{Y\log_2 X}\) eliminates the second LRCF multiplication | pp.1087,1092 |
errors_and_checks: The accumulated error must be less than \(2^{-n-1}\) before final rounding. Stage precisions/guard bits are selected to make the final result accurate to n bits. No fault-detection mechanism or final correctly-rounded contract is reported.   # p.1087
conditions: The recurrences require \(r \ge 8\), \(t=2\), and table-based first-digit selection for convergence. Radix 128 gives the preferred high-speed point, while radix 32 gives lower area. Radices 256/512/1,024 give similar execution time to radix 128 with much greater area. Lookup-table area grows exponentially with radix. The estimates use a technology-independent approximate gate/full-adder model rather than a fabricated implementation. Integer powering accepts b-bit or 2b-bit Y; the extension \(Y=1/q\) requires reciprocal/power tables plus integer division/modulus hardware.   # pp.1088-1095
evidence: Sections 2-6; Figs. 1-8; Tables 1-7; especially recurrence descriptions on pp.1088-1090 and evaluation on pp.1091-1094.

## new_families
### left_to_right_carry_free_multiplier  (domain: mul: integer multipliers, closest: online_arithmetic_unit, why_not: the vocabulary has no MSDF multiplier that emits redundant product digits and converts them on the fly without a terminal carry-propagate adder)
mechanism: The LRCF multiplier consumes multiplier digits from most to least significant and maintains accumulated products \(w\) and \(p\). Each iteration computes \(w[j+1]=r\,fraction(w[j]+aD_{j+1})\), extracts \(K_{j+1}=integer(w[j]+aD_{j+1})\), and appends the resulting digit to \(p\). A redundant adder implements the residual recurrence. Recoding bounds the emitted digit, and on-the-fly conversion produces conventional output without a carry-propagate adder or added latency. The powering unit replaces separate multiplier/adder blocks with a multiply-add unit. (p.1089)
choices:
  digit_order: {msdf}   # p.1089
  accumulator_representation: {signed_digit, carry_save}   # p.1089
  output_conversion: {on_the_fly}   # p.1089
  multiplier_radix: {8, 16, 32, 64, 128, 256, 512, 1024}   # pp.1086,1091
  fused_multiply_add_recurrence: Bool   # p.1089
results:
| metric | value | unit | technology / device | baseline | condition | page |
| composite latency reduction | 1 | cycle | UNKNOWN / 2004 | earlier powering algorithm using two LRCF multiplications | optimized powering algorithm eliminates the second LRCF multiplication | pp.1087,1092 |
evidence: Section 3.2 and Fig. 4, p.1089; composite latency discussion on pp.1087 and 1092.

## space_gaps
* `digit_recurrence_exp_log.selection` needs a mixed schedule value for table lookup in iteration 1 followed by residual rounding in later iterations.   # pp.1088,1090
* `digit_recurrence_exp_log.radix` needs high-radix powers of two from 8 through 1,024.   # pp.1086,1091
* `digit_recurrence_exp_log` needs an intermediate-multiplier slot that can be filled by `left_to_right_carry_free_multiplier`.   # pp.1086,1089
* `digit_recurrence_exp_log` needs an operation-set choice covering independent logarithm/exponential, integer powering, and \(Y=1/q\) powering.   # pp.1094-1095

## open_questions
* The supplied text omits the numerical cells of Tables 1-3 and 6-7, so their parameter/latency values cannot be extracted without guessing.
* The document bounds pre-rounding error but does not state whether every final result is correctly rounded or faithfully rounded.
