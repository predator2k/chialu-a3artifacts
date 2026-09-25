---
handle: vergos2002
citation: H. T. Vergos, C. Efstathiou, D. Nikolos, "Diminished-One Modulo 2^n + 1 Adder Design", IEEE Transactions on Computers, vol. 51, no. 12, pp. 1389-1399, 2002
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [diminished_one_mod_2n_plus_1]
authority: incremental
pages_read: 1389-1399 / 11
---

## summary
The paper proposes carry-lookahead and parallel-prefix methodologies for diminished-one modulo 2^n + 1 addition. The parallel-prefix design recirculates carries at every prefix level, which removes the final reentrant-carry stage and retains log2 n prefix depth. Static CMOS comparisons find carry-lookahead preferable for narrow operands and the proposed parallel-prefix adder fastest for n ≥ 8. # p.1389, pp.1394-1398

## families
### carry_lookahead  (role: extends)
mechanism: The one-level architecture substitutes the complemented carry-output equation directly into every modulo carry equation. The two-level architecture modifies each GPG subunit to produce gqj = ggj + gpj and derives cyclic equations for the BGCLA group carries. These transformations integrate the reentering carry into the carry-lookahead logic instead of adding it through a separate final stage. # pp.1392-1394
choices:
  levels: 1 or 2   # pp.1392-1394
  intergroup_carry: lookahead   # pp.1393-1394
new_choices:
  modular_carry_integration: carry_equation_association — associates the complemented reentering-carry equation with the bit or group carry equations   # pp.1392-1394
slots:
  none
parameters: n-bit operands; one-level CLA for the fastest n = 4 implementation; two-level CLA for the fastest n = 8, 16, and 32 implementations; m = ceil(n/k) groups of up to k bits   # pp.1390, 1397
results:
| metric | value | unit | technology / device | baseline | condition | page |
| --- | --- | --- | --- | --- | --- | --- |
conditions: The proposed CLA implementations are faster and smaller than LAF and KST for small n. The CLA architectures cannot match the faster of LAF and KST under the Table 4 delay constraint for n = 16 or n = 32. # pp.1397-1398
evidence: Sections 3.1-3.2; (3)-(9); Tables 3-4, pp.1392-1398

### parallel_prefix  (role: extends)
mechanism: The PPREF architecture expresses every diminished-one modulo carry as a cyclic prefix over all operand positions. Theorem 1 joins the ordinary prefix for bits i through 0 to the prefix for bits n-1 through i+1. Theorem 2 exchanges selected (g,p) inputs for (p,g), which permits the cyclic expressions to fit within log2 n binary-prefix stages. Carry information is recirculated between adjacent prefix levels instead of being distributed from one final reentrant-carry node. # pp.1394-1396
choices:
  topology: kogge_stone   # pp.1394-1396
  valency: 2   # pp.1390, 1394-1396
  node_style: and_or   # pp.1390-1391
new_choices:
  prefix_input_transform: selected_gp_swap — selected (g,p) terms become (p,g) under Theorem 2 while preserving the required generate result   # p.1395
slots:
  none
parameters: log2 n prefix stages; for an n-bit implementation, stages 1 through log2 n - 2 contain 3n/2 - 2^i operators and each of the last two stages contains n operators; evaluated at n = 4, 8, 16, and 32   # pp.1395-1397
results:
| metric | value | unit | technology / device | baseline | condition | page |
| --- | --- | --- | --- | --- | --- | --- |
| delay improvement | 19 | percent faster | 0.6 μm AMS CUB, 2-metal layer, 5.0 V; 2002 | LAF or KST diminished-one adders | average of examined cases after speed optimization | p.1397 |
| area overhead | 31 | percent more | 0.6 μm AMS CUB, 2-metal layer, 5.0 V; 2002 | LAF diminished-one adder | implementations optimized for minimum delay | p.1397 |
| area overhead | 17 | percent more | 0.6 μm AMS CUB, 2-metal layer, 5.0 V; 2002 | KST diminished-one adder | implementations optimized for minimum delay | p.1397 |
errors_and_checks: The architecture performs exact diminished-one modulo 2^n + 1 addition. A zero bit pattern is ambiguous between a valid represented result of 1 and a real result of 0; a real zero occurs for complementary inputs and is detected by the AND of the per-bit input XORs. # p.1392
conditions: PPREF is the fastest examined diminished-one architecture for n ≥ 8. Its speed advantage grows with n. Area increases when synthesis targets minimum delay, although delay-constrained synthesis produces a smaller PPREF implementation with at least LAF/KST performance in all but one examined case. # pp.1397-1398
evidence: Section 3.3; Theorems 1-2; Fig. 8; Tables 2-4, pp.1394-1398

### end_around_carry  (role: extends)
mechanism: Diminished-one modulo 2^n + 1 addition requires adding the complement of the ordinary carry output back as the carry input. The proposed prefix architecture replaces a single final feedback stage with carry recirculation at every prefix level. The proposed CLA architecture instead absorbs the complemented feedback into bit-level or group-level carry equations. # pp.1391-1396
choices:
  modulus: mod_2n_plus_1_diminished_one   # pp.1391-1392
  recirculation: cyclic_prefix_level   # pp.1394-1396
  topology: kogge_stone   # pp.1394-1396
new_choices:
  zero_output_detection: complementary_input_xor_and — distinguishes a real zero from the diminished-one encoding whose zero bit pattern represents 1   # p.1392
slots:
  none
parameters: n-bit diminished-one operands; synthesized widths n = 4, 8, 16, and 32   # p.1397
results:
| metric | value | unit | technology / device | baseline | condition | page |
| --- | --- | --- | --- | --- | --- | --- |
conditions: The modulo 2^n + 1 channel dictates addition delay in the discussed {2^n-1, 2^n, 2^n+1} RNS base. The PPREF implementation operates as fast as the fastest cited integer modulo 2^n and modulo 2^n-1 adders. # pp.1389, 1397-1398
evidence: Sections 1, 2, and 3; Figs. 7-8; Tables 2-4, pp.1389-1398

## new_families
none

## space_gaps
* `end_around_carry.recirculation` lacks a value for the CLA method that integrates the complemented carry-output equation into one-level or two-level carry-lookahead equations. # pp.1392-1394
* `end_around_carry` lacks a choice for distinguishing a real zero from the diminished-one zero-bit-pattern encoding. # p.1392
* `parallel_prefix` lacks a choice for the selected (g,p)-to-(p,g) operator-input transformation used to retain log2 n cyclic-prefix depth. # p.1395

## open_questions
* The numeric cells of Tables 2-4 are not represented in the supplied document text, so their per-width area/delay values and fastest two-level CLA group counts remain unextracted.
