---
handle: esposito2018
citation: D. Esposito, A. G. M. Strollo, E. Napoli, D. De Caro, N. Petra, "Approximate Multipliers Based on New Approximate Compressors", IEEE Transactions on Circuits and Systems I, vol. 65, no. 12, pp. 4169-4182, 2018
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [unsigned_int8, unsigned_int12, unsigned_int16, unsigned_int20, signed_int8, signed_int12, signed_int16, signed_int20]
authority: incremental
pages_read: 14 / 14
---

## summary
The paper proposes XOR-less approximate compressors and a column-allocation algorithm for approximate binary multipliers. Four multiplier versions trade one/two approximate reduction steps and full/truncated partial-product matrices against error, delay, area and power. Applications include Gaussian image filtering and 16-bit fixed-point LMS filtering. # p.4169-4170, p.4175-4181

## families
### approximate_compressor_tree  (role: proposes)
mechanism: A j-input compressor produces ceil(j/2) outputs with the same weight as its inputs and no carry outputs. AND/OR recoding exposes low-probability terms containing three partial products, which are discarded under the assumption of independent uniformly distributed operand bits. The allocation algorithm maximally compresses the n least-significant columns, inserts only enough approximate compression in more-significant columns to reach the next target height, and avoids approximate 2/1 compressors where possible. # p.4170-4176
choices:
  compressor: esposito_unbiased   # p.4170-4174
  error_recovery: none   # p.4170-4176
new_choices:
  compressor_arity: {2/1, 3/2, 4/2, 5/3, 6/3, composed_7/4_to_20/10} — input/output arity of the approximate compressor   # p.4171-4174
  reduction_steps_approximated: {1, 2} — number of initial partial-product reduction steps using approximate compressors   # p.4176
  allocation_policy: error_aware_column_height_algorithm — maximally compresses the LSP and minimizes approximate compressors in the MSP   # p.4175-4176
slots:
  cpa: parallel_prefix [topology=kogge_stone]   # p.4177
parameters: 8 × 8, 12 × 12, 16 × 16 and 20 × 20 signed/unsigned binary multipliers; four versions named 1StepFull, 2StepsFull, 1StepTrunc and 2StepsTrunc   # p.4176-4179
results:
| metric | value | unit | technology / device | baseline | condition | page |
| error probability / mean error | 1/16 / 1/16 | probability / arithmetic error | UNKNOWN / 2018 | exact sum | approximate 2/1 compressor; independent uniform operand bits | p.4171 |
| error probability / mean error | 1/64 / 1/64 | probability / arithmetic error | UNKNOWN / 2018 | exact sum | approximate 3/2 compressor; independent uniform operand bits | p.4171 |
| error probability / mean error | 13/256 / 14/256 | probability / arithmetic error | UNKNOWN / 2018 | exact sum | approximate 4/2 compressor; independent uniform operand bits | p.4172 |
| error probability / mean error | 43/1024 / 44/1024 | probability / arithmetic error | UNKNOWN / 2018 | exact sum | approximate 5/3 compressor; independent uniform operand bits | p.4172 |
| error probability / mean error | 316/4096 / 336/4096 | probability / arithmetic error | UNKNOWN / 2018 | exact sum | approximate 6/3 compressor; independent uniform operand bits | p.4173 |
| error probability / mean error | 31/256 / 34/256 | probability / arithmetic error | UNKNOWN / 2018 | exact sum | approximate 4/2 compressor with one complemented partial product | p.4174 |
| average delay improvement | about 9% | delay improvement | TSMC 40 nm / 2018 | exact multiplier | 1StepFull; average over four operand sizes | p.4177 |
| average area improvement | about 32% | area improvement | TSMC 40 nm / 2018 | exact multiplier | 1StepFull; average over four operand sizes | p.4177 |
| average power reduction | about 23% | power reduction | TSMC 40 nm / 2018 | exact multiplier | 1StepFull; average over four operand sizes | p.4177 |
| SSIM reduction / power saving | 0.68% / 37% | image quality / power | TSMC 40 nm / 2018 | exact multiplier | 1StepFull Gaussian smoothing | p.4179 |
| stop-band attenuation / system power saving | 60.7dB / 4% | attenuation / power | TSMC 40 nm / 2018 | exact LMS implementation: 60.3dB | 16-bit signed 1StepFull LMS filter | p.4180 |
| stop-band attenuation / system power saving | 61.6dB / 26% | attenuation / power | TSMC 40 nm / 2018 | exact LMS implementation: 60.3dB | 16-bit signed 1StepTrunc LMS filter | p.4180 |
errors_and_checks: Compressor errors under-estimate the exact sum; multiplier error is E = YEXACT − YAPPROX. Multiplier ER/ME/NoEB values use Monte Carlo simulation with 1% relative error and 99% confidence. # p.4171-4174, p.4178
conditions: The probability model assumes uniformly and independently distributed operand bits, giving P(pi)=1/4 and P(qi)=3/4 for complemented partial products. # p.4170, p.4174 Signed multiplication slightly reduces NoEB for the proposed designs. # p.4178-4179 Booth-encoded partial products have different probabilities, so ad-hoc compressors require further investigation. # p.4181
evidence: Sections III-IV; Tables I-IX; Algorithm 1; Figs. 2-9; Sections V-VI; Tables X-XII; Figs. 10-15.

### truncated_fixed_width  (role: instantiates)
mechanism: The 1StepTrunc and 2StepsTrunc versions omit the n−1 least-significant partial-product columns. The versions combine matrix truncation with approximate compressors in one or two initial reduction steps. # p.4176
choices:
  target: multiplier   # p.4176
new_choices:
  truncated_columns: n−1 — number of least-significant partial-product columns not formed   # p.4176
slots:
  cpa: parallel_prefix [topology=kogge_stone]   # p.4177
parameters: 8 × 8, 12 × 12, 16 × 16 and 20 × 20 multipliers; 1StepTrunc and 2StepsTrunc   # p.4176
results:
| metric | value | unit | technology / device | baseline | condition | page |
| average delay improvement | about 24% | delay improvement | TSMC 40 nm / 2018 | exact multiplier | 2StepsTrunc; average over four operand sizes | p.4177 |
| average area improvement | about 76% | area improvement | TSMC 40 nm / 2018 | exact multiplier | 2StepsTrunc; average over four operand sizes | p.4177 |
| average power reduction | about 68% | power reduction | TSMC 40 nm / 2018 | exact multiplier | 2StepsTrunc; average over four operand sizes | p.4177 |
| NoEB / power dissipation | 18.2 / 2.35 | bits / μW/MHz | TSMC 40 nm / 2018 | [27] L=2: 12.97 bits / 3.34 μW/MHz | 20 × 20 1StepTrunc | p.4178 |
| NoEB / power dissipation | 10.92 / 1.90 | bits / μW/MHz | TSMC 40 nm / 2018 | [27] L=2: 12.97 bits / 3.34 μW/MHz | 20 × 20 unsigned 2StepsTrunc | p.4178 |
| NoEB | 10.67 | bits | TSMC 40 nm / 2018 | unsigned 2StepsTrunc: 10.92 bits | 20 × 20 signed 2StepsTrunc | p.4178-4179 |
| SSIM degradation / power saving | 2% / 64% | image quality / power | TSMC 40 nm / 2018 | exact multiplier | 1StepTrunc Gaussian smoothing | p.4179 |
| SSIM degradation / power saving | 8% / 77% | image quality / power | TSMC 40 nm / 2018 | exact multiplier | 2StepsTrunc Gaussian smoothing | p.4179 |
errors_and_checks: ER, ME and NoEB are evaluated against the exact multiplier; no hardware correction is reported. Mean-error compensation is applied only at system level in the LMS experiment. # p.4178, p.4180
conditions: Truncation reduces CPA size and improves electrical performance at the cost of NoEB/SSIM. # p.4177-4179
evidence: Section V; Tables X-XII; Figs. 9-12; Section VI.

### parallel_prefix  (role: instantiates)
mechanism: Every investigated multiplier uses a fast Kogge-Stone carry-propagate adder after partial-product reduction. Full-matrix approximate versions retain the conventional CPA width, while truncated versions use a smaller CPA. # p.4177-4178
choices:
  topology: kogge_stone   # p.4177
new_choices:
  none
slots:
  none
parameters: final CPA for 8 × 8, 12 × 12, 16 × 16 and 20 × 20 multipliers   # p.4176-4177
results:
| metric | value | unit | technology / device | baseline | condition | page |
| partial-product compression delay / CPA delay | 491ps / 231ps | delay | TSMC 40 nm / 2018 | exact multiplier | 12 × 12 | p.4178 |
| partial-product compression delay / CPA delay | 259ps / 291ps | delay | TSMC 40 nm / 2018 | exact multiplier | 12 × 12 2StepsFull | p.4178 |
| partial-product compression delay / CPA delay | 301ps / 237ps | delay | TSMC 40 nm / 2018 | exact multiplier | 12 × 12 2StepsTrunc | p.4178 |
errors_and_checks: none
conditions: The logarithmic CPA limits the delay benefit obtained from reducing CPA width. # p.4178
evidence: Section V-A; Table X.

## new_families
none

## space_gaps
* approximate_compressor_tree lacks compressor arity and a choice for the number of approximate reduction steps. # p.4171-4176
* approximate_compressor_tree lacks an error-aware per-column allocation-policy choice. # p.4175-4176
* truncated_fixed_width lacks a direct choice for truncating exactly n−1 partial-product columns. # p.4176
* The value esposito_unbiased conflicts with the paper's consistently under-estimating compressors, so the vocabulary label requires review. # p.4171-4174

## open_questions
* Tables X-XII contain per-size electrical/error values that are not recoverable from the supplied text rendering.
* The paper does not state whether any truncation correction is used outside the reported LMS system-level mean-error compensation.
