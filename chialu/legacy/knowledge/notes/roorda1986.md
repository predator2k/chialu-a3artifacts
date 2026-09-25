---
handle: roorda1986
citation: M. Roorda, "Method to Reduce the Sign Bit Extension in a Multiplier That Uses the Modified Booth Algorithm", Electronics Letters, vol. 22, 1986
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int4, int6, int8]
authority: incremental
pages_read: 2 / 2
---

## summary
The document replaces redundant sign-extension bits in modified-Booth partial products with constants and sign-dependent bits, which reduces the full-adder array. The reported 4x4/6x6/8x8 implementations use 10/21/36 full adders rather than 14/30/52. # p.1062

## families
### booth_recoded_parallel  (role: extends)
mechanism: The multiplier examines three multiplier bits at a time to generate signed partial products. Conventional sign extension repeats each partial product's sign bit across the higher positions. The proposed identities replace those repeated bits with fixed ones and the complemented sign bit, while correction bits are added at the partial products' least-significant positions. The resulting partial-product array omits full adders whose inputs were determined by the redundant sign extension. # pp.1061-1062
choices:
  booth_radix: 4   # p.1061
  sign_extension: roorda_compact   # p.1062
  negative_pp_encoding: ones_complement_plus_neg_bit   # p.1062
new_choices:
  none
slots:
  reduction: csa_reduction_tree   # pp.1061-1062
parameters: Signed 2-complement 4x4 example; array sizes also reported for 6x6 and 8x8 multipliers; three multiplier bits are analyzed at a time.   # pp.1061-1062
results:
| metric | value | unit | technology / device | baseline | condition | page |
| full-adder count | 10 | full adders | UNKNOWN / 1986 | Normal MBA: 14 full adders | 4x4 multiplier | p.1062 |
| full-adder count | 21 | full adders | UNKNOWN / 1986 | Normal MBA: 30 full adders | 6x6 multiplier | p.1062 |
| full-adder count | 36 | full adders | UNKNOWN / 1986 | Normal MBA: 52 full adders | 8x8 multiplier | p.1062 |
errors_and_checks: The transformation preserves correct 2-complement partial-product summation; no numerical-error metric, fault model, or checker is reported.   # pp.1061-1062
conditions: The method applies when partial-product summation requires sign-bit extension. The document states that the method extends to other multiplier widths and to sign-extension cases outside the modified Booth algorithm. Timing/area/power and implementation technology are not reported.   # p.1062
evidence: Description and eqns. 1-4 on pp.1061-1062; Figs. 1-4 and Table 1 on p.1062.

## new_families
none

## space_gaps
* none

## open_questions
* The document does not specify a fabrication technology or report delay/physical area/power for either array.   # p.1062
* The document does not provide a general closed-form full-adder count for arbitrary operand width.   # p.1062
