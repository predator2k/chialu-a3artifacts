---
handle: posch_posch_1995
citation: Posch, Posch, "Modulo Reduction in Residue Number Systems", IEEE Transactions on Parallel and Distributed Systems, 1995
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [rns_long_integer]
authority: incremental
pages_read: 449-454 / 6
---

## summary
The paper combines RNS arithmetic with Montgomery reduction and a relaxed-residuum alternative for very long modular arithmetic. The modified Montgomery algorithm accepts an off-by-one approximate base extension, which removes the correction module while preserving a bounded valid result.

## families
### rns_montgomery_crypto  (role: proposes)
mechanism: Two relatively prime RNS bases represent the product concurrently. Montgomery reduction computes the low-base residue, multiplies by the precomputed inverse of D, extends the value approximately to the second base, subtracts a multiple of D, divides exactly by the first-base product through modular inverses, and extends back. A final estimate selects a multiple TD so the output represents ab/P1 mod D and remains below D+A. The algorithm remains valid when approximate base extension returns t+P1 rather than t. # pp.451-453
choices:
  channel_width: 32   # p.453
  base_extension: iterated_approximations [outside domain]   # pp.451-453
new_choices:
  approximate_base_extension_tolerance: off_by_one_without_correction — whether reduction remains correct when base extension differs by one base product   # pp.451-453
slots:
  none
parameters: two bases RNS1={p1,...,pn} and RNS2={p(n+1),...,p(2n)}; output z=ab/P1 mod D; example uses approximately 20 processors with 32 bit words for numbers of order 2^640   # pp.451-453
results:
| metric | value | unit | technology / device | baseline | condition | page |
| reduction complexity | O(log n) | complexity | UNKNOWN; 1995 | relaxed-residuum reduction: O(log n) | n denotes the number of registers involved | p.449 |
| base extensions per reduction | 2 | base extensions | UNKNOWN; 1995 | relaxed-residuum reduction: 4 base extensions | unmodified Montgomery reduction in the two-base RNS comparison | p.451 |
| reported modified-reduction time | 5 cycles + 3 base extensions | time | UNKNOWN; 1995 | UNKNOWN | a local (ab+c) mod pi operation defines one computational cycle | p.453 |
errors_and_checks: Approximate base extension may produce t or t+P1 when Wint is correct or low by 1. The modified reduction needs no detector/correction module for this event. If ET<A/D<1/6, an uncertain final T can only produce z in [D,D+A), which remains an allowed input for subsequent modular multiplications. No hardware-fault coverage is reported. # pp.451-453
conditions: The inputs satisfy 0<=a,b<D+A, with D+A<P1<D+D/3 and A<D/6. The combined bases must represent ab, and the moduli must be pairwise relatively prime. The advantage depends on base extension dominating local modular multiplication/addition cost. # pp.451-452
evidence: Abstract; §III; Fig. 2; §IV-A-B; Fig. 3; §V, pp.449-454.

### rns_channel_arithmetic  (role: instantiates)
mechanism: Each processing element is dedicated to one relatively prime modulus pi and computes local addition/subtraction/multiplication independently. Two sets of processing elements form the bases used by reduction. A bus-coupled implementation broadcasts residue digits during base extension, while every destination processor evaluates its new residue. # pp.449-450, 453-454
choices:
  modulus_form: generic   # pp.449, 453
  channel_width_n: 32   # p.453
new_choices:
  none
slots:
  none
parameters: m processing elements in the general description; two n-modulus bases for reduction; pi chosen below 2^32 in the RSA example   # pp.450-451, 453
results:
| metric | value | unit | technology / device | baseline | condition | page |
| channel addition/subtraction/multiplication latency | constant | time | UNKNOWN; 1995 | weighted representation with carry propagation | all residue digits are computed independently | p.449 |
conditions: Addition/subtraction/multiplication parallelize without carry propagation. Comparison/sign detection/overflow detection/scaling remain expensive and require base extension. # p.449
evidence: §I; §II-A; §III; §V, pp.449-454.

### rns_scaling_comparison  (role: extends)
mechanism: Base extension reconstructs residues for additional relatively prime moduli by estimating the integer W in a Chinese-remainder expression. Limited-precision rational factors make the estimate uncertain near an integer. Conventional iterated approximation detects and corrects rare uncertainty, while the modified reduction accepts the bounded off-by-one extension directly. # pp.449-450, 451-453
choices:
  operation: base_extend   # p.449
  method: iterated_approximations [outside domain]   # pp.449-450
  exactness: approximate_bounded_uncorrected [outside domain]   # pp.451-453
new_choices:
  none
slots:
  none
parameters: extension between two bases containing n moduli each; bus-coupled processor organization   # pp.450-451
results:
| metric | value | unit | technology / device | baseline | condition | page |
| base-extension latency | n | bus cycles | UNKNOWN; 1995 | UNKNOWN | bus-coupled system broadcasts n residues | p.450 |
| base-extension latency | approximately n | cycles | UNKNOWN; 1995 | UNKNOWN | each cycle broadcasts Xi and/or computes (ab+c) mod pi | p.454 |
errors_and_checks: Conventional base extension detects rare uncertainty and uses additional approximations. The reduction-specific extension instead permits an estimate off by 1 and relies on subsequent range adjustments. # pp.450-453
conditions: The method assumes limited-precision representations of the rational CRT factors. The uncorrected approximation is valid in the modified reduction context rather than as a generally exact base-extension result. # pp.450-453
evidence: §II-A; §III; §IV; §V, pp.449-454.

## new_families
none

## space_gaps
* `rns_montgomery_crypto.base_extension` lacks `iterated_approximations`, which is the base-extension method used by the proposed reduction. # pp.450-453
* `rns_scaling_comparison.method` lacks `iterated_approximations`. # pp.449-450
* `rns_scaling_comparison.exactness` lacks a bounded approximation that the consuming algorithm tolerates without correction. # pp.451-453

## open_questions
* Fig. 2 reports two base extensions for Montgomery reduction, while §V reports “5 cycles plus 3 base extensions” for the modified implementation; the document does not explicitly reconcile the counts. # pp.451, 453
* The approximately 20 processors in the RSA example are not explicitly divided between RNS1 and RNS2, so `channel_count_per_base` remains UNKNOWN. # p.453
