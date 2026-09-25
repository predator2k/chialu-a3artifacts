---
handle: antelo_1997
citation: E. Antelo, J. Villalba, J. D. Bruguera, E. L. Zapata, "High Performance Rotation Architectures Based on the Radix-4 CORDIC Algorithm", IEEE Transactions on Computers, vol. 46, no. 8, pp. 855-870, 1997
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [fixed_point]
authority: incremental
pages_read: 855-870 / 16
---

## summary
The paper proposes a full radix-4 CORDIC algorithm for circular-coordinate rotation, with an iteration-independent selection function and angle-dependent scale-factor compensation. The paper implements word-serial, unfolded/pipelined, and known-angle architectures using carry-save or nonredundant arithmetic. # p.855-856

## families
### redundant_high_radix_cordic  (role: extends)
mechanism: Each microrotation uses σi ∈ {-2, -1, 0, 1, 2} and powers-of-four shifts. Overlapping selection intervals permit σi to be selected after assimilating five bits for i = 0 or six bits for i > 0. The nonconstant scale factor is evaluated from an initial table plus shift/add approximations and is applied through radix-4 linear CORDIC multiplication. Later pipelined stages obtain all remaining σi values in parallel by recoding wp into signed-digit radix-4. # p.856-863
choices:
  residual_arithmetic: carry_save / conventional_cpa   # p.860, p.862
  radix: 4   # p.856
  scale_handling: table_plus_shift_add_then_linear_cordic_multiplication [outside domain]   # p.859-863
new_choices:
  architecture: {word_serial, unfolded_pipelined, application_specific} — implementation organization   # p.860, p.862-865
  zero_skipping: Bool — skips the next cycle when σi+1 = 0 and predicts σi+2 in parallel   # p.860-861
  angle_source: {runtime, known_beforehand} — known angles permit stored σi sequences and removal of the w path   # p.863-865
slots:
  none
parameters: σi ∈ {-2, -1, 0, 1, 2}; n/2 radix-4 microrotations for n-bit precision; selection assimilates 5 bits at i = 0 and 6 bits at i > 0; pipelined prediction begins at p = ⌈n/6⌉; evaluated precisions are 16, 24, 32, and 64 bits.   # p.856, p.858-859, p.863, p.866-869
results:
| metric | value | unit | technology / device | baseline | condition | page |
| microrotation reduction | 50 | percent | UNKNOWN / 1997 | radix-2 | Same precision; per-microrotation complexity remains similar. | p.856 |
| microrotation reduction | 33 | percent | UNKNOWN / 1997 | mixed radix-2/radix-4 | Same precision. | p.856 |
| scale-factor range | 1.0 to 2.52 | ratio | UNKNOWN / 1997 | radix-2 K approximately 1.64 | Full radix-4 circular rotation. | p.856 |
| scale-factor table size | 27 × 32 | bits | UNKNOWN / 1997 | direct 3^(n/4+1) × n-bit table | n = 32; three-term series approximation. | p.860 |
| average iterations | 12.16 / 18.58 / 24.97 | iterations | UNKNOWN / 1997 | 11.6 / 17.5 / 23.49 optimal | 16 / 24 / 32-bit word-serial rotation plus scale compensation with zero skipping. | p.860 |
| average iteration reduction | 20 | percent | UNKNOWN / 1997 | no zero skipping | Word-serial rotation plus scale compensation; estimated average is 4n/5 iterations. | p.860, p.862 |
| gate-count ratio | 0.5 | ratio | UNKNOWN / 1997 | radix-4 CSA = 1 | n = 32 radix-4 CCLA word-serial design; first-order gate model. | p.867 |
| gate-level ratio | 1.3 | ratio | UNKNOWN / 1997 | radix-4 CSA = 1 | n = 32 radix-4 CCLA word-serial design; first-order delay model. | p.867 |
| gate-count ratio | 0.3 | ratio | UNKNOWN / 1997 | radix-4 CSA = 1 | n = 32 radix-2 CCLA word-serial design; first-order gate model. | p.867 |
| gate-level ratio | 2.2 | ratio | UNKNOWN / 1997 | radix-4 CSA = 1 | n = 32 radix-2 CCLA word-serial design; first-order delay model. | p.867 |
| nonpipelined latency | 8n + tconv | tg | UNKNOWN / 1997 | Timmermann: 7n + tconv + 10(log2(n) - 1) | Unfolded radix-4 CSA design; scale-factor compensation latency is excluded. | p.868 |
| nonpipelined CCLA latency | 11n / 14n / 15n | tg | UNKNOWN / 1997 | radix-2 CCLA: 17n / 23n / 25n | n = 16 / 16 < n ≤ 32 / 32 < n ≤ 64; scale-factor compensation latency is excluded. | p.868 |
| pipeline latency | 2n/3 + 4 | stages | UNKNOWN / 1997 | Dawid: 3n + 2 | Radix-4 CSA design. | p.868 |
| pipeline cycle | 21 | tg | UNKNOWN / 1997 | Dawid: 13 tg | Radix-4 CSA design. | p.868 |
| pipeline filling time | 546 | tg | UNKNOWN / 1997 | Dawid: 1,274 tg | n = 32 radix-4 CSA design. | p.869 |
| pipeline latency | n/2 + 1 | stages | UNKNOWN / 1997 | radix-2 CCLA: n | Radix-4 CCLA design. | p.868 |
| pipeline filling time | 629 | tg | UNKNOWN / 1997 | radix-2 CCLA: 1,024 tg | n = 32. | p.869 |
| application-specific average iterations | 4.9 / 10.24 | iterations | UNKNOWN / 1997 | optimal decomposition | 16 / 32-bit precision over 8,000 angles uniformly distributed between 0 and π/2; averages are five percent above optimal. | p.869 |
| iteration advantage | 0.5 | iterations | UNKNOWN / 1997 | Hu and Naganathan radix-2 recoding | Application-specific average; the baseline needs one extra iteration on average over [π/4, π/2). | p.869 |
errors_and_checks: General-purpose selection guarantees n-bit precision after n/2 radix-4 iterations, with the residual bound in (22). The known-angle interval split guarantees n + 1-bit precision after n/2 iterations, with |z_(n/2-1)| ≤ tan^-1(2^-n). No fault-detection results are reported.   # p.859, p.864
conditions: Radix-4 is limited to circular coordinates in rotation mode in the proposed algorithm. # p.855-856 The general-purpose convergence range becomes [-π, π] through an initial π/2 rotation. # p.861, p.868 The scale factor depends on the rotation angle and must be computed for each angle. # p.856, p.859 Known-angle applications remove the w path and permit stored, zero-rich σi decompositions. # p.863-865 The evaluation uses gate-count/gate-level models rather than implemented circuit simulations, excludes table cost from the word-serial gate comparison, and omits scale-factor-compensation latency from the unfolded comparison. # p.866, p.868
evidence: Abstract; §§2.1-2.4; §§3.1-3.3; Fig. 4; Figs. 6-10; Tables 1-3; §§4.1-4.3.

## new_families
none

## space_gaps
* `redundant_high_radix_cordic.scale_handling` lacks the paper's angle-dependent table/shift-add evaluation followed by linear-CORDIC multiplication. # p.859-863
* `redundant_high_radix_cordic` lacks a component slot for the scale-factor compensator, which this design fills with a radix-4 linear-coordinate CORDIC multiplier. # p.860-863

## open_questions
* Table 3 gives the radix-4 CSA pipeline latency as 2n/3 + 4 stages, while the accompanying prose gives 2n/3 + 3 stages. # p.868-869
