---
handle: efstathiou2004
citation: C. Efstathiou, H. T. Vergos, D. Nikolos, "Fast Parallel-Prefix Modulo 2^n + 1 Adders", IEEE Transactions on Computers, 2004
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [normal_binary_unsigned]
authority: incremental
pages_read: 1211-1216 / 6
---

## summary
The paper proposes PPFCI and TPP architectures for exact modulo 2^n + 1 addition with normal-binary operands. PPFCI uses a parallel-prefix adder plus a fast carry-increment stage, while TPP recirculates the carry within the existing prefix levels. Full-static CMOS comparisons report lower latency and area than the architecture of [22]. (pp.1211-1216)

## families
### end_around_carry  (role: proposes)
mechanism: PPFCI computes M = X + Y + 2^n - 1 with a CSA and an n-bit parallel-prefix adder. A modified carry-increment row accepts the conditional correction through its carry input. An AND gate produces c0, the remaining increment operators use c0, and rn is produced as cn AND Pn AND s0. (pp.1212-1213)
choices:
  modulus: mod_2n_plus_1_normal_binary [outside domain]   # pp.1212-1213
  recirculation: carry_increment_stage [outside domain]   # p.1213
  topology: ladner_fischer   # p.1214
new_choices:
  operand_representation: normal_binary — identifies the representation used for residues, including ordinary handling of zero   # pp.1211, 1214
slots:
  none
parameters: X and Y are (n + 1)-bit numbers in [0, 2^n + 1); evaluated at n = 4, 8, and 16; one CSA, one n-bit parallel-prefix carry unit, and one carry-increment stage   # pp.1212-1214
results:
| metric | value | unit | technology / device | baseline | condition | page |
| execution latency | 2 × log2 n + 9 | gate delays | unit-gate model [29]; 2004 | fastest modulo 2^n and modulo 2^n - 1 adders: 2 × log2 n + 3 gate delays | normal-binary modulo 2^n + 1 addition | p.1215 |
errors_and_checks: Theorem 1 establishes exact |X + Y|_(2^n+1) for X,Y in [0, 2^n + 1); no error-detection mechanism is reported.   # p.1212
conditions: PPFCI uses one carry-computation unit, whereas [22] uses two serial CLA units, so PPFCI is faster and the advantage increases with n. PPFCI is slower than TPP because PPFCI adds one prefix level and imposes increased fan-out on the reentering carry.   # p.1214
evidence: Theorem 1 and §3.1; Figs. 1-2; §4; Tables 1-2; pp.1212-1215

### end_around_carry  (role: proposes)
mechanism: TPP eliminates the separate carry-increment stage by recirculating the reentering carry at each existing prefix level. Transformed cyclic prefix equations compute every carry within log2 n levels. The last level uses n - 1 prefix operators, and the preceding levels use 3n/2 - 2^i operators. (pp.1213-1214)
choices:
  modulus: mod_2n_plus_1_normal_binary [outside domain]   # pp.1212-1214
  recirculation: cyclic_prefix_level   # pp.1213-1214
new_choices:
  operand_representation: normal_binary — identifies the representation used without diminished-one converters or special zero handling   # p.1214
slots:
  none
parameters: X and Y are (n + 1)-bit numbers in [0, 2^n + 1); evaluated at n = 4, 8, and 16; log2 n prefix levels; modulo 257 example uses n = 8 and three prefix levels   # pp.1212, 1214
results:
| metric | value | unit | technology / device | baseline | condition | page |
| total prefix operators | 3/2 n(log2 n - 1) + 1 | prefix operators | architectural analysis; 2004 | UNKNOWN | TPP carry-computation structure | p.1214 |
| prefix depth | log2 n | prefix levels | architectural analysis; 2004 | PPFCI: one additional prefix level | transformed TPP equations | pp.1213-1214 |
| execution latency | 2 × log2 n + 6 | gate delays | unit-gate model [29]; 2004 | fastest modulo 2^n and modulo 2^n - 1 adders: 2 × log2 n + 3 gate delays | normal-binary modulo 2^n + 1 addition | p.1215 |
errors_and_checks: Theorem 1 establishes exact |X + Y|_(2^n+1) for X,Y in [0, 2^n + 1); no error-detection mechanism is reported.   # p.1212
conditions: TPP has one fewer prefix level than PPFCI and avoids PPFCI's reentering-carry fan-out, so its speed advantage increases with n. TPP avoids the normal/diminished-one converters and special zero treatment required by diminished-one adders.   # p.1214
evidence: §3.2; Theorem 2; Example 1; Fig. 3; §4; Tables 1-2; pp.1213-1215

## new_families
none

## space_gaps
* `end_around_carry.modulus` lacks a value for modulo 2^n + 1 arithmetic with normal-binary operands.   # pp.1211-1214
* `end_around_carry.recirculation` lacks the PPFCI value `carry_increment_stage`.   # p.1213
* `end_around_carry` lacks an operand-representation choice distinguishing normal binary from diminished-one representation.   # pp.1211, 1214

## open_questions
* The numerical entries in Tables 1 and 2 are not legible in the supplied document text, so the UMC-VST 25 delay/area values for n = 4, 8, and 16 require inspection of the source PDF.   # p.1215
* The paper names the Ladner-Fischer topology for PPFCI but does not identify a vocabulary topology for TPP.   # pp.1213-1214
