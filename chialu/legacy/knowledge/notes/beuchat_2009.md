---
handle: beuchat_2009
citation: Y. Wang, "Residue-to-Binary Converters Based on New Chinese Remainder Theorems", IEEE Transactions on Circuits and Systems II, 2000
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [rns]
authority: incremental
pages_read: 4 / 4
---

## summary
The document proves that Wang’s New CRT I residue-to-binary conversion is a rewriting of the second form of the Chinese Remainder Theorem previously sketched by Hitz and Kaltofen (p.3–4). The document also shows that explicitly computing Wang’s constants \(k_i\) is unnecessary because the required constants depend only on the modulus set (p.3).

## families
### rns_reverse_converter  (role: analyzes)
mechanism: New CRT I reconstructs \(X\) from residues \(x_i\) through a weighted mixed-radix expression using constants \(k_i\). Algebraic expansion shows that its coefficients are the mixed-radix representations of \(s_i|1/s_i|_{P_i}\), so the method is the second form of the CRT rather than a distinct conversion algorithm. The constants can be precomputed directly from the moduli without first computing \(k_i\) (p.3).
choices:
  algorithm: new_crt_i   # p.3
new_choices:
  none
slots:
  none
parameters: \(n\) pairwise relatively prime moduli \(P_1,\ldots,P_n\); worked examples use \(P_1=11\), \(P_2=13\), \(P_3=17\), and \(P_1=2^n\), \(P_2=2^n+1\), \(P_3=2^n-1\)   # p.1–4
results:
| metric | value | unit | technology / device | baseline | condition | page |
| Huang conversion storage | \(n(n+1)/2-1\) | tables | UNKNOWN / 1983 | constructive CRT | Convert the \(X_i\) values from RNS to MRS | p.1, p.4 |
| Hitz–Kaltofen input processing | \(n\) | modular multipliers | UNKNOWN / 1995 | Huang algorithm | Compute \(x_i|1/s_i|_{P_i}\) with precomputed constants | p.2, p.4 |
| Hitz–Kaltofen MRS evaluation | \(n(n+1)/2-1\) | multiplications | UNKNOWN / 1995 | Huang algorithm | Evaluate the products with the MRS digits of \(s_i\) | p.2, p.4 |
| Hitz–Kaltofen constant storage | \(n(n+1)/2\) | numbers | UNKNOWN / 1995 | Huang stores MRS digits for all numbers in \(\mathbb Z/M\mathbb Z\) | Store only the MRS digits of \(s_i\) or \(s_i|1/s_i|_{P_i}\) | p.2, p.4 |
errors_and_checks: The reconstruction is exact for \(X\in\mathbb Z/M\mathbb Z\); no fault model, detection coverage, false-alarm behavior, or alias rate is reported.   # p.1–3
conditions: The constructive CRT requires multiplication by the large \(s_i\) constants and modulo-\(M\) operations (p.1). Mixed Radix Conversion is strictly sequential (p.1). Huang’s algorithm avoids modulo-\(M\) operations but requires \(n(n+1)/2-1\) tables (p.1–2). The second-form CRT uses constants \(s_i|1/s_i|_{P_i}\) that are larger than \(s_i\), which produces larger carries (p.2). New CRT I provides no distinct algorithmic mechanism because it rewrites the second-form CRT, and computing \(k_i\) is unnecessary because the coefficients depend only on the modulus set (p.3–4).
evidence: §I and Equation (1), p.1; §§II–III and Equation (2), p.1–2; §IV and Equations (3)–(5), p.3–4; §V, p.4

## new_families
none

## space_gaps
* none

## open_questions
* The document reports no technology, delay, area, power, or implemented converter measurements; the speed/area improvement attributed to Wang et al. [7] is not quantified in this document (p.3).
