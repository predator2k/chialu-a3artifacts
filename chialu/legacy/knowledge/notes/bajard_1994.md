---
handle: bajard_1994
citation: J.-C. Bajard, S. Kla, J.-M. Muller, "BKM: A New Hardware Algorithm for Complex Elementary Functions", IEEE Transactions on Computers, vol. 43, no. 8, pp. 955-963, 1994
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [complex_radix2, signed_digit_radix2, binary_carry_save]
authority: landmark
pages_read: 146-153 / 8
---

## summary
BKM computes complex exponentials/logarithms through shift-and-add iterations that generalize CORDIC. # p.146-p.147
BKM supports redundant number systems without the CORDIC scaling-factor problem. # p.147, p.152
One or two BKM operations also compute real elementary functions, complex multiplication, rotations, vector lengths and normalization. # p.151-p.152

## families
### digit_recurrence_exp_log  (role: extends)
mechanism: BKM maintains complex variables \(L_n\) and \(E_n\). Each iteration selects \(d_n\) from nine complex digits and applies \(L_{n+1}=L_n(1+d_n2^{-n})\) and \(E_{n+1}=E_n-\ln(1+d_n2^{-n})\). E-mode selects digits so \(E_n\) approaches zero and returns \(L_1e^{E_1}\). L-mode selects digits so \(L_n\) approaches one and returns \(E_1+\ln(L_1)\). Selection examines truncated leading digits of scaled residuals. # p.147-p.150
choices:
  radix: 2   # p.147
  normalization: multiplicative   # p.147
  digit_set: signed_redundant   # p.147
  selection: rounding_of_scaled_residual   # p.149-p.150
new_choices:
  arithmetic_domain: complex — \(L_n\), \(E_n\), and \(d_n\) are complex.   # p.147
  operation_mode: {E_mode, L_mode} — E-mode computes exponentials and L-mode computes logarithms.   # p.147
  complex_digit_set: {-1, 0, 1, -i, i, 1-i, 1+i, -1-i, -1+i} — allowed values of \(d_n\).   # p.147
  selector_fraction_bits: {E_mode_real_3_imaginary_4, L_mode_real_4_imaginary_4} — retained fractional digits used for digit selection.   # p.149-p.150
  scaling_factor_required: false — BKM avoids a CORDIC scale-factor correction.   # p.147, p.152
slots:
  none
parameters: E-mode initial domain is \([-0.829802\ldots,+0.868876\ldots]+i[-0.749780\ldots,+0.749780\ldots]\). # p.149 E-mode requires approximately \(n\) iterations and \(8n\) stored constants for approximately \(n\) accurate binary digits. # p.149 L-mode convergence is proven for the trapezoid bounded by \(x=1/2\), \(x=1.3\), \(y=x/2\), and \(y=-x/2\); its bounding set enters \(\lVert z\rVert\le3/2\) at step 6. # p.150 L-mode requires \(n+1\) iterations for absolute error below \(2^{-n}\). # p.151
results:
| metric | value | unit | technology / device | baseline | condition | page |
| E-mode iteration count | approximately \(n\) | iterations | UNKNOWN / 1994 | none | approximately \(n\) accurate binary digits | p.149 |
| E-mode constant storage | \(8n\) | constants | UNKNOWN / 1994 | none | approximately \(n\) accurate binary digits | p.149 |
| L-mode iteration count | \(n+1\) | iterations | UNKNOWN / 1994 | none | absolute error less than \(2^{-n}\) | p.151 |
| iterations for \(p\) significant bits | roughly \(p\) | iterations | UNKNOWN / 1994 | CORDIC: roughly \(p\) iterations | BKM versus CORDIC | p.152 |
| stored constants for \(p\) significant bits | \(8p\) | constants | UNKNOWN / 1994 | CORDIC: \(p\) constants | constants represented by \(p\) digits | p.152 |
| constant-storage area complexity | \(O(p^2)\) | area complexity | UNKNOWN / 1994 | CORDIC: \(O(p^2)\) | \(p\)-digit constants | p.152 |
| total area complexity | \(O(n^2)\) | area complexity | UNKNOWN / 1994 | CORDIC: \(O(n^2)\) | barrel shifter supports any shift through \(n\) | p.152 |
| time complexity | \(O(p)\) | time complexity | UNKNOWN / 1994 | CORDIC: \(O(p)\) | redundant number system | p.152 |
errors_and_checks: E-mode relative error after \(n\) iterations is approximately \(2^{-n}\). # p.149 L-mode absolute error is bounded by a term equivalent to \(2^{-n+2}\), so \(n+1\) iterations give absolute error below \(2^{-n}\). # p.151 No fault-detection mechanism or coverage result is reported.
conditions: The constant-time elementary-step advantage requires a signed-digit representation; extension to binary carry-save representation is described as simple. # p.147 The proven convergence domains restrict direct E-mode/L-mode inputs, although the observed L-mode domain appears larger than the proven trapezoid. # p.150-p.151 BKM and CORDIC have the same asymptotic time/space complexities, but redundant CORDIC requires repeated iterations to retain a constant scale factor and may still require a final multiplication because that factor differs from 1. # p.152
evidence: E-mode recurrence/selection/domain in §2 and the E-mode algorithm, p.147-p.149; L-mode recurrence/selection/proof in §3 and Figs. 4-7, p.149-p.151; supported functions in §4 and Figs. 8-10, p.151-p.152; CORDIC comparison in §5, p.152.

## new_families
none

## space_gaps
* digit_recurrence_exp_log lacks an operation-mode choice for paired complex E-mode/L-mode recurrences. # p.147
* digit_recurrence_exp_log lacks a complex digit-set choice covering the nine values used by BKM. # p.147
* digit_recurrence_exp_log lacks selector-precision choices for truncated scaled-residual digit selection. # p.149-p.150
* digit_recurrence_exp_log lacks a scaling-factor requirement choice, which distinguishes BKM from redundant CORDIC. # p.147, p.152

## open_questions
* The supplied scan uses printed pages 146-153 and carries a 1993 copyright line, while the citation identifies IEEE Transactions on Computers pages 955-963 in 1994; title/authors match, but the supplied text does not resolve the pagination/copyright discrepancy. # p.146
* No circuit implementation, technology/device, clock rate, measured area, or measured power is reported. # p.146-p.153
