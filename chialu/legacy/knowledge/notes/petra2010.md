---
handle: petra2010
citation: N. Petra, D. De Caro, V. Garofalo, E. Napoli, A. G. M. Strollo, "Truncated Binary Multipliers with Variable Correction and Minimum Mean Square Error", IEEE Transactions on Circuits and Systems I, vol. 57, no. 6, pp. 1312-1325, 2010
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [signed_binary, unsigned_binary]
authority: incremental
pages_read: 1312-1325 / 14
---

## summary
The paper derives a closed-form quadratic compensation function that minimizes the mean-square error of variable-correction truncated binary multipliers. The paper also proposes a quantized linear approximation that integrates into the partial-product matrix and reports synthesized/test-chip/MAC results in 0.18 μm technology. (p.1312, pp.1317-1323)

## families
### truncated_fixed_width  (role: proposes)
mechanism: The multiplier discards the LSPminor partial products while retaining the MSP and h LSPmajor columns. A compensation function of the Input Correction partial products estimates the discarded sum. The minimum-mean-square-error function is a quadratic form of the Input Correction bits, while the implemented approximation is a quantized linear combination whose terms are repositioned in the partial-product matrix before carry-save reduction and final carry propagation. (pp.1312-1319)
choices:
  correction_scheme: variable_mmse   # pp.1316-1318
  output_rounding: truncate   # pp.1314-1315
new_choices:
  compensation_form: {optimal_quadratic, linear_quantized} — selects the analytical MMSE function or its hardware-oriented first-order approximation   # pp.1317-1319
slots:
  kept_tree: csa_reduction_tree   # p.1319
parameters: n-bit × n-bit multiplication with n-bit output; synthesized word lengths n=8 to 16; h controls retained LSPmajor columns; signed/unsigned operation; signed 16-bit test chip; pipeline stages/latency/II UNKNOWN   # pp.1312, 1318-1319, 1322
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area reduction | 42 | % | 0.18 μm / year UNKNOWN | full-rounded multiplier | synthesis; exact n/h condition is missing from the supplied text | p.1319 |
| power reduction | 47 | % | 0.18 μm / year UNKNOWN | full-rounded multiplier | synthesis; exact n/h condition is missing from the supplied text | p.1319 |
| area reduction | about 44 | % | UMC 0.18 μm, six metal levels / year UNKNOWN | full-rounded multiplier | signed 16-bit test chip; exact h is missing from the supplied text | p.1322 |
| power dissipation | halved | relative | UMC 0.18 μm, six metal levels / year UNKNOWN | full-rounded multiplier | signed 16-bit test chip; exact h is missing from the supplied text | p.1322 |
| speed increase | 13 | % | UMC 0.18 μm, six metal levels / year UNKNOWN | full-rounded multiplier | signed 16-bit test chip; exact h is missing from the supplied text | p.1322 |
| area reduction | 43 | % | 0.18 μm / year UNKNOWN | full-width MAC | 100-tap low-pass FIR, 16-bit signed fractional data, 250 MHz target; exact h is missing from the supplied text | p.1323 |
| power reduction | 42 | % | 0.18 μm / year UNKNOWN | full-width MAC | 100-tap low-pass FIR, 16-bit signed fractional data, 250 MHz target; error comparable to the full-rounded multiplier; exact h is missing from the supplied text | p.1323 |
errors_and_checks: The optimal compensation function minimizes mean-square error under independent/uniform input-bit assumptions. The error model separates erasing error from output-truncation error; the full-rounded reference error is bounded by LSB/2. The paper reports mean/mean-square errors in Table III, but the table cells are absent from the supplied text. Fault checking is none.   # pp.1312, 1314-1317, 1321
conditions: The statistical derivation assumes independent operand bits with probability 1/2. The quadratic optimum requires a number of terms on the order of n², which makes direct hardware implementation difficult. The linear approximation reduces hardware complexity, and coefficient quantization trades accuracy against complexity. Increasing h reduces mean/mean-square error and increases hardware complexity. Signed and signed/unsigned variants require modified Input Correction definitions when the retained-column condition identified in Section VII applies.   # pp.1314, 1317-1318, 1320
evidence: Sections III-VII and (37)-(58) derive the error model/optimal quadratic function/linear quantization; Figs. 7-8 and Section VIII define the signed implementation; Tables I/III, Figs. 9-10, and Sections VIII-B/C compare implementations; Fig. 11/Table IV report the chip; Fig. 12/Table V report the FIR MAC. (pp.1314-1323)

## new_families
none

## space_gaps
* `truncated_fixed_width` lacks a `final_cpa` slot, although the implementation explicitly uses a Kogge-Stone `parallel_prefix` carry-propagate adder after the reduction tree. (p.1319)
* `compensation_form` should distinguish the exact quadratic MMSE function from the quantized linear implementation because the two forms have different complexity/accuracy properties. (pp.1317-1319)

## open_questions
* The numeric cells of Tables I/III/IV/V are absent from the supplied text, so their absolute area/power/delay/error values must be recovered from the original PDF.
* Missing mathematical symbols obscure the exact allowed range of h and the n/h conditions attached to several narrative results.
