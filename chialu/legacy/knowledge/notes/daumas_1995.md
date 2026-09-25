---
handle: daumas_1995
citation: M. Daumas, C. Mazenc, X. Merrheim, J.-M. Muller, "Modular Range Reduction: A New Algorithm for Fast and Accurate Computation of the Elementary Functions", Journal of Universal Computer Science, vol. 1, no. 3, pp. 162-175, 1995
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [fixed_point_radix2, floating_point_radix2]
authority: landmark
pages_read: 162-175 / 14
---

## summary
Modular Range Reduction computes an additive reduced argument by summing stored residues of powers of two and applying a small table-selected correction. The paper proves absolute-error bounds, gives a continued-fraction procedure for relative accuracy, and proposes cellular-array and logarithmic-time tree architectures. # p.165-173

## families
### range_reduction  (role: proposes)
mechanism: MRR stores each \(m_i \equiv 2^i \bmod C\) in \([-C/2,C/2)\). A first reduction sums the \(m_i\) selected by nonzero input bits together with the unreduced low-order portion. A truncated representation of this sum addresses a table containing \(kC\), which is subtracted to produce a reduced argument in the symmetrical or positive redundant interval. Floating-point reduction selects \(m_{\mathit{exponent}-i}\), so the accumulated fixed-point terms have similar magnitudes. # p.165-168
choices:
  method: modular_mrr   # p.165
  reduction_type: additive   # p.164-165
  worst_case_bound_proven: true   # p.166, p.169-170
new_choices:
  interval_form: {symmetrical, positive} — selects either \([-C/2-\epsilon,C/2+\epsilon]\) or \([-\epsilon,C+\epsilon]\) as the permitted reduced interval   # p.164-166
  redundancy: redundant — permits more than one valid pair \((x^*,k)\), which enables the table-based second reduction   # p.164-166
  first_reduction_architecture: {cellular_array, wallace_tree} — selects a Braun-derived cellular array or an arborescent logarithmic-time reduction tree   # p.168-169, p.171-173
  operand_recoding: {none, booth, modified_booth} — recodes the input into signed digits before residue selection   # p.169
  multiplier_hardware_sharing: Bool — permits range reduction and multiplication to use the same modified multiplier hardware   # p.168-169
slots:
  none
parameters: Fixed-point input has \(N\) integer bits and \(p\) fractional bits, with \(2^v<C\leq2^{v+1}\); the first reduction adds \(N-v+1\) terms, and the second table uses \(m=\lceil\log_2(N-v+2)\rceil+\lceil-\log_2(\epsilon)\rceil\) address bits. Example 4 uses \(N=20\), \(v=2\), 19 first-reduction terms, 8 table-address bits, and \(p+5\) stored fractional bits. Floating-point input has an \(m\)-bit mantissa, while stored residues and correction terms have \(q\) fractional bits. # p.165-169
results:
| metric | value | unit | technology / device | baseline | condition | page |
| hardwired latency | O(log(n)) | time | UNKNOWN (result year 1995) | UNKNOWN | n-bit binary input with an arborescent first-reduction architecture | p.162, p.168, p.173 |
| first-reduction term count | halved | relative term count | UNKNOWN (result year 1995) | unreencoded binary input | Booth or modified-Booth recoding gives signed digits in \(\{-1,0,1\}\) with at least half the digits zero | p.169 |
errors_and_checks: With fixed-point terms stored using \(q\) fractional bits, the absolute reduced-argument error is bounded by \(2^{-q-1}(N-v+1)\); preserving the input's \(p\)-bit absolute accuracy requires \(p+\lceil\log_2(N-v+1)\rceil\) stored fractional bits. With an \(m\)-bit floating-point mantissa, the bound is \((m+1)2^{-q-1}\). The relative-error procedure derives a minimum nonzero reduced-argument bound from continued-fraction convergents of \(C\) up to the maximum input and selects \(q\) so the absolute-error bound meets the requested relative error. # p.166, p.168-170
conditions: MRR addresses additive reduction; multiplicative reduction is excluded because the relevant logarithm/root cases can choose \(C\) as a radix power. # p.164. The algorithm assumes a redundant convergence interval whose length exceeds \(C\). # p.164-165. Trigonometric evaluation may require only \(k\bmod4\) for \(C=\pi/2\), or no information about \(k\) for \(C=2\pi\). # p.165. Multiplier-derived architectures permit hardware sharing with multiplication, while Booth recoding reduces the first-reduction term count. # p.168-169. Results close to zero require the continued-fraction sizing procedure to guarantee relative accuracy. # p.169-170
evidence: §2 and §2.1 define fixed-point MRR and prove its interval/error properties; §2.2 extends MRR to floating point; §3 and Figs. 2-4 give the cellular-array and Wallace-tree architectures; §4 derives the relative-accuracy condition. # p.164-173

## new_families
none

## space_gaps
* `range_reduction` lacks choices for interval form/redundancy, even though MRR depends on symmetrical-versus-positive redundant reduction. # p.164-166
* `range_reduction` lacks a first-reduction architecture choice or reduction-tree slot for the cellular-array/Wallace-tree alternatives. # p.168-169, p.171-173
* `range_reduction` lacks operand recoding and multiplier-hardware-sharing choices. # p.168-169

## open_questions
* The paper reports no technology node, device, measured area, power, clock rate, or implementation delay.
* The figures do not fix the carry-save/signed-digit cell encoding or the final adder topology.
