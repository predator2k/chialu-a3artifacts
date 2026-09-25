---
handle: dimauro_1993
citation: Dimauro, Impedovo, Pirlo, "A New Technique for Fast Number Comparison in the Residue Number System", IEEE Transactions on Computers, 1993
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [rns]
authority: incremental
pages_read: 608-612 / 5
---

## summary
The paper proposes the Sum of Quotients Technique (SQT), which compares RNS numbers through a monotonic diagonal function. The improved SQT incorporates the function modulus into a nonredundant RNS and supports a flow-through lookup-table implementation.

## families
### rns_scaling_comparison  (role: proposes)
mechanism: For pairwise relatively prime moduli \(m_1,\ldots,m_n\), the technique defines \(SQ=\sum_i M_i\), where \(M_i=M/m_i\), and constants \(k_i\) derived from multiplicative inverses modulo \(SQ\). The diagonal function \(D(X)=|\sum_i k_i x_i|_{SQ}\) is monotonic over the represented integer range. Different function values determine magnitude directly; equal values are resolved by comparing corresponding residues. The improved SQT includes \(SQ\) in the RNS modulus set, derives \(X'=[X/SQ]\), applies the diagonal function to \(X'\), and uses the \(SQ\) coordinate when the reduced values are equal.   # pp.608-611
choices:
  operation: compare   # pp.608-611
  method: diagonal_function   # pp.608-611
  exactness: exact   # pp.609-611
new_choices:
  modulus_organization: {individual_moduli, grouped_virtual_moduli} — selects whether the diagonal function operates on the original residues or residues formed by grouping moduli   # p.612
  diagonal_modulus_integration: {redundant_extra_modulus, incorporated_nonredundant_modulus} — selects whether \(SQ\) is an extra redundant modulus or part of an expanded nonredundant RNS   # pp.610-611
slots: none
parameters: \(n\) pairwise relatively prime moduli; \(M=\prod_i m_i\); \(SQ=\sum_i M_i\); one \(SQ\) coordinate in the improved system; optional grouping of moduli into virtual moduli   # pp.608-612
results:
| metric | value | unit | technology / device | baseline | condition | page |
| comparison latency, first stage | 3 | operation cycles | UNKNOWN | none | Fig. 4 nonredundant SQT implementation; an operation cycle is the time required for a lookup-table operation | p.611 |
| comparison latency, second stage | n - 1 | operation cycles | UNKNOWN | none | summation modulo \(SQ\) in the Fig. 4 implementation | p.611 |
| MRC multiplication count | n(n - 1)/2 | multiplications | UNKNOWN | SQT | traditional RNS magnitude comparison | p.611 |
| MRC subtraction count | n(n - 1)/2 | subtractions | UNKNOWN | SQT | traditional RNS magnitude comparison | p.611 |
| MRC latency | 2n | operation cycles | UNKNOWN | SQT | lookup-table implementation of MRC | p.611 |
| CRT multiplication count | n | multiplications | UNKNOWN | SQT | direct CRT conversion | p.611 |
| CRT modular-addition count | n - 1 | additions modulo M | UNKNOWN | SQT | direct CRT conversion | p.611 |
| CRT multiplication latency | one | operation cycle | UNKNOWN | SQT | multiplications performed in parallel | p.611 |
| CRT addition latency | n - 1 | addition cycles | UNKNOWN | SQT | one extra adder modulo M | p.611 |
| grouped example SQ | 40808 | modulus value | UNKNOWN | ungrouped moduli \(17,29,19,23\) | original modulus set | p.612 |
| grouped example SQ' | 930 | modulus value | UNKNOWN | SQ = 40808 | virtual moduli \(493,437\) | p.612 |
| grouped SQ' relative size | less than 2.3% | of SQ | UNKNOWN | SQ = 40808 | virtual moduli \(493,437\) | p.612 |
| grouped SQ' relative size | less than 0.5% | of M | UNKNOWN | M = 215441 | virtual moduli \(493,437\) | p.612 |
errors_and_checks: Theorems 3 and 4 prove monotonic ordering and exact tie resolution by a corresponding coordinate. The improved SQT has no excluded buffer zone and reports no approximation error, fault model, detection coverage, false alarms, or alias rate.   # pp.610-612
conditions: The SQT requires pairwise relatively prime RNS moduli. The SQT avoids the iterative critical-core process and requires no redundant modulus for magnitude comparison. A large \(SQ\) can increase hardware cost when the RNS has many moduli, while grouped virtual moduli can reduce \(SQ\) but require a fast MRC within each group. Direct CRT comparison is limited by the lack of effective adders modulo a large arbitrary integer.   # pp.608,611-612
evidence: Theorems 1-4 and Figs. 1-3, pp.608-610; improved SQT procedure, pp.610-611; Fig. 4 and implementation comparison, p.611; virtual-modulus grouping example, p.612

## new_families
none

## space_gaps
* `rns_scaling_comparison` lacks a choice for incorporating the comparison modulus into the nonredundant RNS dynamic range.   # pp.610-611
* `rns_scaling_comparison` lacks a choice for grouping physical moduli into virtual moduli to reduce the diagonal-function modulus.   # p.612
* `rns_scaling_comparison` lacks a slot for the modulo-\(SQ\) summation network used by the diagonal function.   # p.611

## open_questions
* The paper permits groupings other than pairwise grouping but does not specify an optimization rule for selecting groups.   # p.612
* The paper states that fast CRT addition techniques can accelerate the second stage but does not select a specific implementation.   # p.611
