---
handle: decaro2013
citation: D. De Caro, N. Petra, A. G. M. Strollo, F. Tessitore, E. Napoli, "Fixed-Width Multipliers and Multipliers-Accumulators with Min-Max Approximation Error", IEEE Transactions on Circuits and Systems I, vol. 60, no. 9, pp. 2375-2388, 2013
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_DOT_ACC, VEC_SFU]
formats: [unsigned_fractional_n_bit, signed_fractional_n_bit, signed_unsigned_fractional_n_bit]
authority: incremental
pages_read: 14 / 14
---

## summary
The paper develops fixed-width multipliers/MACs whose linear compensation functions minimize maximum absolute error rather than an average error metric (pp.2375-2383). The implementation discards partial-product columns and uses quantized compensation coefficients derived through mixed-integer linear programming (pp.2376-2383). A 9×9 fixed-width MAC demonstrates faithful piecewise-linear function evaluation (p.2384).

## families
### truncated_fixed_width  (role: extends)
mechanism: The multiplier retains the most-significant partial-product region, divides the discarded region into LSPmajor/LSPminor, and forms an input-correction vector from the leftmost LSPminor column. A compensation function estimates the unformed terms and rounding error. The practical function is a quantized linear combination of input-correction terms, with coefficients selected to minimize MAE. The MAC variant also truncates low addend bits and therefore requires different coefficients. Signed/signed-unsigned variants transform the unsigned coefficients while preserving the error performance (pp.2376-2383).
choices:
  correction: min_max   # pp.2378-2383
  target: multiplier   # pp.2375-2381
new_choices:
  target_extension: multiplier_accumulator — applies truncation and min-max compensation to a MAC addend/product matrix   # pp.2382-2383
  coefficient_quantization: integer_or_fractional_bits — constrains linear compensation coefficients to multiples of 2^-q   # p.2378
  compensation_implementation: {standard_ppm, auxiliary_tree, auxiliary_tree_signed_digit} — realizes repeated weighted correction terms in the partial-product matrix   # pp.2384-2385
slots:
  none
parameters: n×n operands and n-bit approximate product; LSPmajor width is a design parameter; coefficient precision q; demonstrated 9×9 MAC; unsigned/signed/signed-unsigned operation   # pp.2375-2378, pp.2383-2384
results:
| metric | value | unit | technology / device | baseline | condition | page |
| MAE | 1.0625 | LSB | UNKNOWN / 2013 | optimal-compensation lower bound | 6-bit multiplier example | p.2378 |
| MAE reduction | 20–30 | % | UNKNOWN / 2013 | King et al./Van et al./Petra et al./Kuang et al. | Table I multiplier comparison | p.2380 |
| MAE reduction | 10–20 | % | UNKNOWN / 2013 | 1.5-bit and 2-bit multipliers of Petra et al. [20] | Table I multiplier comparison | p.2380 |
| MAC MAE | 0.742 | LSB | UNKNOWN / 2013 | none | 9×9 MAC used for faithful function interpolation | p.2384 |
errors_and_checks: MAE is the maximum absolute difference from the rounded full-width result; the optimal LUT compensation gives a lower bound for any fixed-width multiplier, while the quantized linear function approaches that bound (pp.2377-2380). Signed/signed-unsigned coefficient transformations give the same error performance as unsigned circuits (p.2383).
conditions: The analysis covers non-Booth fixed-width multipliers; Booth/multiplexer-based architectures are outside the study (p.2376). Inputs are initially unsigned fractional values in [0,1), with signed/signed-unsigned extensions supplied later (pp.2376, 2383). The optimal compensation LUT is considered impractical, so the implemented design uses a quantized linear function (p.2378). The 65 nm implementations use 1.0 V/standard-VT devices and report area/power/delay similar to previous fixed-width designs while reducing MAE (pp.2385-2386).
evidence: Sections II-VI and VIII; Figs. 1-11 and 14-15; Tables I-V; pp.2376-2386.

### parallel_prefix  (role: instantiates)
mechanism: A Brent-Kung parallel-prefix carry-propagate adder follows the modified carry-save reduction tree in every implemented multiplier (p.2385).
choices:
  topology: brent_kung   # p.2385
new_choices:
  none
slots:
  none
parameters: terminal CPA after the multiplier/auxiliary reduction trees   # p.2385
results:
| metric | value | unit | technology / device | baseline | condition | page |
errors_and_checks: none
conditions: The paper fixes Brent-Kung for the evaluated implementations but does not compare prefix topologies (p.2385).
evidence: Section VIII, p.2385.

### pwl  (role: instantiates)
mechanism: The interval is divided into equal subintervals, leading input bits address tables containing intercept/slope coefficients, and the remaining input bits form the local coordinate. A fixed-width MAC evaluates the first-order polynomial, so its MAE contributes directly to the total approximation-error bound (p.2384).
choices:
  segmentation: uniform   # p.2384
new_choices:
  none
slots:
  segmenter: uniform_high_bit_decode   # p.2384
parameters: 17-bit input/output; 9×9 fixed-width MAC; target is faithful rounding within 1 LSB   # p.2384
results:
| metric | value | unit | technology / device | baseline | condition | page |
| maximum interpolation error | 0.937 | LSB | VHDL simulation / 2013 | calculated error bound | example function on [0,1] | p.2384 |
errors_and_checks: Faithful rounding is guaranteed by combining the starting approximation/coefficient error with the MAC MAE; simulation reports a maximum error of 0.937 LSB (p.2384).
conditions: The application targets low-precision elementary-function evaluation using piecewise-linear approximation (p.2384).
evidence: Section VII; Figs. 12-13; p.2384.

## new_families
none

## space_gaps
* `truncated_fixed_width` needs slots for the carry-save reduction structure and terminal CPA because both are explicit implementation components (pp.2384-2385).
* `truncated_fixed_width` needs coefficient-quantization and auxiliary-tree realization choices because both affect accuracy/hardware cost (pp.2378-2379, 2384-2385).
* `pwl` needs an evaluator slot that can name the fixed-width MAC used for `c0+c1u` (p.2384).

## open_questions
* Several mathematical symbols/parameter values and the numeric cells of Tables I-V are not recoverable from the supplied text extraction, so their exact configurations/results must not be guessed.
