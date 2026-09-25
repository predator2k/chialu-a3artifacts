---
handle: kidambi1996
citation: S. S. Kidambi, F. El-Guibaly, A. Antoniou, "Area-Efficient Multipliers for Digital Signal Processing Applications", IEEE Transactions on Circuits and Systems II, vol. 43, no. 2, pp. 90-95, 1996
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [sign-magnitude fixed-point, two's-complement fixed-point]
authority: incremental
pages_read: 90-95 / 6
---

## summary
The paper proposes an N×N parallel multiplier that produces an N-bit product while omitting about half of the partial-product adder cells and biasing retained cells from a probabilistic error estimate (p.90-93). The method covers sign-magnitude and two's-complement multiplication and gives zero mean error with variance Q²/16 for the stated biased case (p.92-94). A 16×16 application in a second-order digital filter gives better signal-to-noise ratio than a standard multiplier rounded to 16 most-significant bits (p.93-94).

## families
### truncated_fixed_width  (role: proposes)
mechanism: The multiplier omits the array cells that generate the discarded N least-significant product bits. Output carries from cells on the truncation diagonal estimate the omitted contribution. The integer part I of the normalized expected error is inserted as a fixed bias through retained diagonal adder inputs, so the bias requires no separate hardware. Half adders are replaced by full adders when more than one bias bit is required. The same construction is applied to a positive-partial-product two's-complement array (p.91-93).
choices:
  correction_scheme: probabilistic_bias [outside domain]   # p.90, p.92-93
  output_rounding: truncate   # p.90-91
new_choices:
  operand_representation: sign_magnitude_and_twos_complement — the partial-product encoding covered by the construction   # p.90, p.93
  bias_injection: retained_diagonal_adder_inputs — the location where I is added without separate bias hardware   # p.92-93
slots:
  kept_tree: csa_reduction_tree   # p.90-93
parameters: N×N inputs; N-bit product; even N in the derivation; 8×8 circuit examples; N=8, 16, and 32 area ratios; 16×16 filter experiment; Q=2^-N   # p.90-94
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area ratio Atm/Afm | 0.52 | dimensionless | UNKNOWN; result year 1996 | full parallel multiplier | N=8, ξ=0.45, φ=0.09 | p.93 |
| area ratio Atm/Afm | 0.51 | dimensionless | UNKNOWN; result year 1996 | full parallel multiplier | N=16, ξ=0.45, φ=0.09 | p.93 |
| area ratio Atm/Afm | 0.5 | dimensionless | UNKNOWN; result year 1996 | full parallel multiplier | N=32, ξ=0.45, φ=0.09 | p.93 |
| normalized expected error E | 1.25 | dimensionless | UNKNOWN; result year 1996 | unbiased truncated multiplier | 8×8 sign-magnitude multiplier; bias I=1 | p.93 |
| mean error | zero | product value | UNKNOWN; result year 1996 | biased truncated multiplier | E=I+0.25 and bias=IQ | p.92 |
| error variance | Q²/16 | product-error variance | UNKNOWN; result year 1996 | biased truncated multiplier | error is -0.25Q or 0.25Q with equal probability | p.92 |
| standard-multiplier error variance | Q²/8 | product-error variance | UNKNOWN; result year 1996 | standard N×N multiplier | result truncated to N bits | p.92 |
| standard-multiplier error variance | Q²/12 | product-error variance | UNKNOWN; result year 1996 | standard N×N multiplier | result rounded to N bits | p.92 |
errors_and_checks: The error estimate sums the expected output carries from diagonal cells, weighted by Q=2^-N. The analysis treats diagonal carry bits as independent random variables. For E=I+0.25, bias IQ gives errors of -0.25Q and 0.25Q with equal probability, zero mean, and variance Q²/16 (p.91-92). No runtime checker or fault model is provided.
conditions: The design targets fixed-point DSP cases in which two N-bit values are multiplied and the 2N-bit result is quantized to N bits (p.90). The probability model assigns each operand bit probability pm of being one and each bit product probability pm² (p.91). The reported area ratios are analytical and assume Ah=ξAf, Aa=φAf, ξ=0.45, and φ=0.09 rather than a stated technology or layout (p.93). The filter comparison uses a 16×16 multiplier in a second-order Butterworth GIC wave digital filter; the standard multiplier output is rounded to its 16 most-significant bits (p.93-94). Nonadditive multiplicative modules are suggested to increase speed, but no delay result is reported (p.93).
evidence: Sections II-VII; Figs. 1-6 and 8; equations (4)-(19), especially the error derivation in equations (10)-(13) and area derivation in equations (14)-(16) (p.90-94).

## new_families
none

## space_gaps
* `correction_scheme` lacks a probabilistic expected-error bias value computed from truncation-diagonal carry probabilities (p.91-93).
* `truncated_fixed_width` lacks an operand-representation choice covering sign-magnitude and Baugh-Wooley-style two's-complement arrays (p.90, p.93).
* `truncated_fixed_width` lacks a bias-injection choice for adding the correction through retained diagonal half-adder/full-adder inputs (p.92-93).

## open_questions
* The value of pm used to produce the error-statistics plots in Figs. 4 and 6 is not stated in the supplied text (p.91-94).
* The paper reports analytical cell-area ratios rather than a technology-specific implementation, so delay/power/device results remain UNKNOWN (p.93).
* The paper states that nonadditive multiplicative modules can increase speed but gives no selected module structure or measured speedup (p.93).
