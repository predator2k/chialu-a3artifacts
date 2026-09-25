---
handle: vergos_2001
citation: L. Kalampoukas, D. Nikolos, C. Efstathiou, H. T. Vergos, J. Kalamatianos, "High-Speed Parallel-Prefix Modulo 2^n - 1 Adders", IEEE Transactions on Computers, vol. 49, no. 7, 2000.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [diminished_one_mod_2n_plus_1]
authority: incremental
pages_read: 7 / 7
---

## summary
The document proposes diminished-one modulo 2^n+1 adders that recirculate carries at every parallel-prefix level rather than re-entering the final carry through an additional stage (pp.213-214). The resulting adders retain log2 n prefix levels and approach the delay of modulo 2^n and modulo 2^n−1 adders, with additional prefix hardware (pp.214, 216-217).

## families
### end_around_carry  (role: proposes)
mechanism: The carry computation wraps around within every prefix level. Theorem 2 expresses each carry as a prefix over the lower-order group and the complement of the upper-order group. Theorem 3 recursively transforms expressions that cannot fit within log2 n levels. The implementation adds wraparound prefix operators and modifies selected operators to generate complemented group terms, avoiding the final re-entry stage and its fan-out of n (pp.213-215).
choices:
  modulus: mod_2n_plus_1_diminished_one   # p.213
  recirculation: cyclic_prefix_level   # pp.213-214
  topology: kogge_stone   # pp.214-215
new_choices:
  none
slots:
  none
parameters: n-bit diminished-one operands; log2 n prefix stages; synthesized widths n=4, 8, 16, 32; worked example n=8 for modulo 257   # pp.214-216
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay model | 2 log n + 3 | elementary-gate delays | unit-gate analytical model; node UNKNOWN; 2001 | SKL/KST: 2 log n + 5 | fan-in/fan-out ignored | p.216 |
| area | 706.8 | mils2 | AMS CUB 0.6 μm, 2-metal layer, 5.0 V; 2001 | none | n=32, SKL, speed optimized | p.216 |
| delay | 5.80 | ns | AMS CUB 0.6 μm, 2-metal layer, 5.0 V; 2001 | none | n=32, SKL, worst-case process parameters | p.216 |
| area | 955.6 | mils2 | AMS CUB 0.6 μm, 2-metal layer, 5.0 V; 2001 | none | n=32, KST, speed optimized | p.216 |
| delay | 5.79 | ns | AMS CUB 0.6 μm, 2-metal layer, 5.0 V; 2001 | none | n=32, KST, worst-case process parameters | p.216 |
| area | 1356.4 | mils2 | AMS CUB 0.6 μm, 2-metal layer, 5.0 V; 2001 | SKL/KST | n=32, proposed design, speed optimized | p.216 |
| delay | 4.79 | ns | AMS CUB 0.6 μm, 2-metal layer, 5.0 V; 2001 | SKL: 5.80 ns; KST: 5.79 ns | n=32, proposed design, worst-case process parameters | p.216 |
| average delay improvement | 19% faster | percent | AMS CUB 0.6 μm, 2-metal layer, 5.0 V; 2001 | SKL or KST | examined synthesized widths | p.216 |
| average area overhead | 31% more | percent | AMS CUB 0.6 μm, 2-metal layer, 5.0 V; 2001 | SKL | fastest implementations | p.216 |
| average area overhead | 17% more | percent | AMS CUB 0.6 μm, 2-metal layer, 5.0 V; 2001 | KST | fastest implementations | p.216 |
errors_and_checks: Diminished-one addition has a double-zero output ambiguity. An erroneous zero occurs only for complementary inputs and can be detected with a simple combinational circuit; quantitative detection coverage and false-alarm behavior are not reported (p.213).
conditions: The method applies to diminished-one modulo 2^n+1 addition, where zero is unused or handled with an additional zero-indication bit (p.213). The design targets log2 n carry-computation levels so the modulo 2^n+1 channel does not limit an RNS system using moduli 2^n−1, 2^n, and 2^n+1 (pp.211, 214). The speed advantage requires additional prefix operators and complemented group-term generation (pp.214-215). Area-constrained synthesis achieves at least the fastest SKL/KST performance with smaller area except for n=32, where the synthesized result is slightly faster and slightly larger (pp.216-217).
evidence: Theorems 1-3 and Fig. 6 (pp.214-215); Tables I-IV and comparison text (pp.216-217).

## new_families
none

## space_gaps
* The vocabulary does not represent the diminished-one double-zero detector attached to a modulo 2^n+1 adder (p.213).

## open_questions
* The venue name is not present in the supplied document text.
* The supplied OCR omits or displaces several numeric cells in Tables II-IV, so only unambiguous rows and prose aggregates are extracted.
