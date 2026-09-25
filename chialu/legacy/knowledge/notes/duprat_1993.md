---
handle: duprat_1993
citation: J. Duprat, J.-M. Muller, "The CORDIC Algorithm: New Results for Fast VLSI Implementation", IEEE Transactions on Computers, vol. 42, no. 2, pp. 168-178, 1993
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [binary_signed_digit]
authority: landmark
pages_read: 168-178 / 11
---

## summary
The paper proposes branching CORDIC, which performs two signed-digit CORDIC rotations in parallel when the residual sign is uncertain and retains a constant normalization factor. The paper derives an MSDF on-line sine/cosine implementation with on-line delay 5.

## families
### redundant_high_radix_cordic  (role: proposes)
mechanism: Binary signed-digit residuals permit constant-time additions, but their signs may require examining many digits. Branching CORDIC examines a fixed residual prefix and, when the sign remains uncertain, evaluates rotations for both \(d_n=+1\) and \(d_n=-1\) in parallel. A later sign evaluation retains or copies the valid computation. At most two computations remain active, all rotation digits stay in \(\{-1,+1\}\), and the normalization factor remains constant. # p.169-173
choices:
  residual_arithmetic: signed_digit   # p.169
  radix: 2   # p.168-170
  scale_handling: branching   # p.170-173
new_choices:
  digit_selection_inspection_digits: 3 — number of residual digit positions examined by the practical `eval` function   # p.170, p.172-173
slots:
  none
parameters: two parallel conventional CORDIC modules; `eval(z_n)` returns `{-1,0,1}`; practical residual inspection `p = 3`; rotation digits `d_n ∈ {-1,+1}`   # p.170-173
results: none
errors_and_checks: Theorem 1 proves that at step \(i\), at least one branch has \(|z_i|\leq\sum_{k=i}^{\infty}\arctan 2^{-k}\leq2^{-i+1}\), while both branches have \(|z_i|\leq3\cdot2^{-i+1}\).   # p.171-173
conditions: The method retains a constant scale factor without repeated iterations, while Takagi/Asada/Yajima methods require more complicated or repeated iterations.   # p.169-170
conditions: The method requires two conventional CORDIC iterations in parallel and therefore consumes more silicon area than classical methods.   # p.170, p.177
conditions: Carry-save representation is possible after a slight modification, but the developed algorithm uses binary signed-digit representation.   # p.168-169
evidence: §II-B, §III-A-B, Algorithm `branching-CORDIC`, Fig. 1, Fig. 2, Theorem 1, Lemma 1, Table III, p.169-173

### online_arithmetic_unit  (role: instantiates)
mechanism: The rotation angle enters most-significant digit first and contributes one new digit to each residual update. Two branching CORDIC modules generate sine/cosine approximations. A digitization stage examines a bounded portion of each approximation and emits one signed output digit per iteration. Averaging the two module outputs improves the error bound and reduces the on-line delay from 6 to 5. # p.173-177
choices:
  radix: 2   # p.174
  online_delay: 5   # p.177
  digit_set: maximally_redundant   # p.169, p.176-177
  residual_form: signed_digit   # p.169, p.174
new_choices:
  output_combination: average_both_modules — selects averaging rather than digitizing one module’s output   # p.176-177
  residual_eval_digits: 4 — digit positions examined by the on-line residual `eval` function   # p.174
  digitization_inspection_digits: 5 — least-significant digit positions of `K` used by the digitization decision   # p.177
slots:
  none
parameters: sine/cosine; angle input MSDF; signed-digit output MSDF; \(x_0=1/K\); \(y_0=0\); one result digit per iteration after the on-line delay   # p.173-177
results:
| metric | value | unit | technology / device | baseline | condition | page |
| on-line delay | 6 | digits | UNKNOWN / 1993 | UNKNOWN | digitization uses one module’s output | p.177 |
| on-line delay | 5 | digits | UNKNOWN / 1993 | one-module output: 6 digits | digitization uses the average of both module outputs | p.177 |
| sine/cosine absolute-error bound | \(<2^{-n+3}\) | dimensionless | UNKNOWN / 1993 | UNKNOWN | either module’s output after iteration \(n\) | p.176 |
| sine/cosine absolute-error bound | \(<2^{-n+2}\) | dimensionless | UNKNOWN / 1993 | either-module bound \(<2^{-n+3}\) | average of both module outputs after iteration \(n\) | p.176 |
errors_and_checks: Theorem 3 bounds either module’s sine/cosine error by \(2^{-n+3}\). Theorem 4 bounds the averaged outputs by \(2^{-n+2}\). The digitization proof converts these approximation bounds into a valid signed-digit output stream.   # p.176-177
conditions: The presented on-line architecture computes sine/cosine only; \(x_0=1/K\) and \(y_0=0\) are internal constants.   # p.173-174
conditions: The single-module error derivation assumes \(|\theta|\leq1\), while the averaged cosine derivation states \(\theta\in[-\pi/2,\pi/2]\).   # p.175-176
evidence: §IV-A-D, Algorithm `On-line branching-CORDIC`, Theorems 2-4, Digitization Algorithm, Fig. 3, p.173-177

## new_families
none

## space_gaps
* `redundant_high_radix_cordic` lacks a residual-inspection-width choice, although the fixed number of inspected digits determines constant-time digit selection.   # p.170, p.172-174
* `online_arithmetic_unit` lacks an output-combination choice, although single-module and averaged-module outputs produce different error bounds and on-line delays.   # p.176-177

## open_questions
* The paper does not specify a fabrication technology/device or report silicon area, clock period, power, or measured latency.
* The paper states that carry-save representation needs a slight modification but does not specify that modification or its on-line delay.   # p.168-169
* The paper does not settle whether a physical implementation unfolds the iterations or reuses each CORDIC module sequentially.
