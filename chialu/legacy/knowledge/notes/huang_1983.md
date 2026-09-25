---
handle: huang_1983
citation: Huang, "A Fully Parallel Mixed-Radix Conversion Algorithm for Residue Number Applications", IEEE Transactions on Computers, 1983
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [rns]
authority: incremental
pages_read: 5 / 5
---

## summary
The document proposes a fully parallel, pipelined conversion from residue representations to mixed-radix digits using lookup tables and parallel modular-adder networks. The implementation converts an RNS with up to 15 moduli in two clock cycles and reports 50 ns conversion time for a 150-bit RNS using ECL components. # p.398, p.400

## families
### rns_reverse_converter  (role: proposes)
mechanism: Each residue \(x_i\) addresses tables that produce the nonzero mixed-radix digits of an orthogonal projection \(X_i\). The resulting triangular digit array is summed concurrently by column modulo \(p_k\). Each column uses a balanced adder tree, comparators/subtractors, and a carry from the preceding column inserted at the final adder level. Table lookup and column summation form two pipelined stages, so intermodulus communication is delayed until the parallel arithmetic finishes. # p.399, p.400
choices:
  algorithm: mixed_radix   # p.399
  moduli_count: 15   # p.400
  implementation: table_plus_parallel_adder_network [outside domain]   # p.400
new_choices:
  conversion_schedule: fully_parallel_two_stage — all mixed-radix columns are computed concurrently after one parallel table-lookup stage   # p.400, p.401
slots:
  none
parameters: n pairwise-relatively-prime moduli; b-bit residue words; up to n=15 and b=10 in the ECL example; n(n+1)/2 tables of size 2^b × b; adder-tree depth ⌈log2(k+1)⌉ for column k; two pipeline stages/two clock cycles; 25 ns clock in the reported implementation example   # p.399, p.400
results:
| metric | value | unit | technology / device | baseline | condition | page |
| conversion latency | t_T + (⌈log2(n+1)⌉ + 1)t_A | time | UNKNOWN / 1983 | (n−1)(t_T+t_A), Szabo-Tanaka | n-moduli RNS | p.400 |
| conversion latency | 2 | clock cycles | off-the-shelf ECL / 1983 | n−1 clock cycles, Szabo-Tanaka | up to 15 moduli | p.400 |
| conversion time | 50 | ns | ECL F100180 adders and MC10415A RAM / 1983 | 350 ns, Szabo-Tanaka | 15 moduli, 10-bit word per modulus, 150-bit dynamic range, 25 ns clock | p.400 |
| throughput rate | 40 | MHz | ECL F100180 adders and MC10415A RAM / 1983 | 40 MHz, Szabo-Tanaka | 15 moduli, 10-bit word per modulus, 25 ns clock | p.400 |
| adder time | 4 | ns | two 6-bit ECL F100180 fast adders / 1983 | none | 10-bit addition | p.400 |
| table access time | 20 | ns | 1K × 1 MC10415A RAM / 1983 | none | 10-bit table lookup | p.400 |
| lookup tables | n(n+1)/2 | tables | UNKNOWN / 1983 | n(n−1)/2 tables, Szabo-Tanaka | proposed tables are 2^b × b; baseline tables are 2^(b+1) × b | p.399, p.400 |
| latches | n(n+1)/2 | latches | UNKNOWN / 1983 | n(n+1)/2−1 latches, Szabo-Tanaka | n-moduli converter | p.399, p.400 |
| adder-network adders | n(n+1)/2 | adders | UNKNOWN / 1983 | n(n−1)/2 b-bit adders, Szabo-Tanaka | n-moduli converter | p.399, p.400 |
| comparator/subtractors | n | comparator/subtractors | UNKNOWN / 1983 | UNKNOWN, Szabo-Tanaka | one per mixed-radix column | p.400 |
errors_and_checks: The conversion is presented as exact; the document reports no approximation error, fault model, detection coverage, false-alarm behavior, or alias rate. # p.399, p.400
conditions: The moduli \(p_i\) must be pairwise relatively prime. # p.399 The carry treatment assumes practical applications satisfy 2^b > n. # p.400 The two-cycle result for up to 15 moduli assumes that the parallel column-summation time is about equal to the table-lookup time. # p.400 The design adds n tables and n comparator/subtractors relative to Szabo-Tanaka, while each proposed table has half the capacity and the total table-bit requirement is lower. # p.400, p.402 The converted digits support residue-to-binary decoding/sign determination/magnitude comparison/overflow detection. # p.402
evidence: Section III and equations (2)-(6), pp.399-400; Figs. 2-3, pp.401; hardware and timing summaries, pp.399-400; Section V, p.402.

## new_families
none

## space_gaps
* `rns_reverse_converter.implementation` needs a `table_plus_parallel_adder_network` value because the conversion depends on both residue-indexed tables and modular adder trees. # p.400
* `rns_reverse_converter` lacks a conversion-schedule choice distinguishing the classical stage-parallel recurrence from fully parallel column processing. # p.399, p.400

## open_questions
* The document does not specify a semiconductor process or technology node for the ECL components.
* The document does not state the exact adder architecture used inside the ECL F100180 components.
