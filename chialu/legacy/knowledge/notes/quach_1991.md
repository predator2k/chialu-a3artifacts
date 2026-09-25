---
handle: quach_1991
citation: N. Quach, M. Flynn, "Suggestions for Implementing a Fast IEEE Multiply-Add-Fused Instruction", Stanford CSL-TR-91-483, 1991
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_DOT_ACC]
formats: [fp64]
authority: incremental
pages_read: 18 / 18
---

## summary
The report studies three ways to overlap the operations of a floating-point multiply (FMPY) and a floating-point add (FADD) in one multiply-add-fused (MAF) instruction for IEEE double precision: non-overlapped (MAC, i.e. chaining), fully overlapped (Greedy, an implementation similar to the IBM RS/6000), and partially overlapped (SNAP). Against a state-of-the-art FP multiplier and two-path FP adder baseline, it compares MAF latency, FADD latency and hardware cost under a normalized CMOS delay and area model. SNAP has the lowest MAF latency, MAC the lowest FADD latency and area, and Greedy and RS/6000 sit between, with rounding for the IEEE standard as the main source of design complexity in Greedy and SNAP.

## families

### round_fused_in_reduction  (role: instantiates)
mechanism: Partial products are generated in parallel and reduced to a sum term S and a carry term C. The carry-save adders add a rounding constant r, determined by a rounding logic, before a compound adder that computes S + C + r and S + C + r + 1 simultaneously. The rounding logic selects between the two results from the lower-order bits of S and C and from the LSBs and overflow bits of the results, so only one addition step takes place. For the IEEE round-to-infinity modes r may equal 2. The bit position at which r is added is called the carry point and is bit 51 for multipliers (the MSB is bit zero).
choices:
  sticky_method: post_cpa_or_tree   # p.14 (a CLA adder sums the lower-order 53 bits of S and C for rounding)
new_choices:
  carry_point_bit: 51 — the bit position at which the rounding constant is added, known in advance for a multiplier   # p.3
slots:
  injection_adder: compound_flagged_prefix [outputs=sum_sum1, topology=modified_ling [outside domain], implementation=conditional_sum_local_sums [outside domain]]   # p.3, p.12
parameters: IEEE double precision, 53-bit significand including the hidden bit, 11-bit exponent; 53x53 partial-product reduction; 53b compound adder; carry point bit 51; r up to 2 for round-to-infinity.   # p.1, p.3
results:
| metric | value | unit | technology / device | baseline | condition | page |
| FMPY latency | 3.6T + Tw(FMPY) | T = 53b add delay | CMOS, node UNKNOWN, 1991 | — | double precision, Table 2 delays, wire delay unquantified | p.12 |
| 53x53b partial-product reduction delay | 2.0T | T = 53b add delay | CMOS, node UNKNOWN, 1991 | — | Table 2 delay assumption | p.12 |
| 3-2 carry-save add delay | 0.2T | T = 53b add delay | CMOS, node UNKNOWN, 1991 | — | Table 2 delay assumption | p.12 |
| 4-2 carry-save add delay | 0.3T | T = 53b add delay | CMOS, node UNKNOWN, 1991 | — | Table 2 delay assumption, hidden carry-in and carry-out | p.12 |
| 106b adder delay | 1.2 x 53b adder | relative | CMOS, node UNKNOWN, 1991 | 53b adder (5 complex gates) | 106b adder is 6 complex gates | p.12 |
| 159b adder delay | 1.4 x T53bAdd | relative | CMOS, node UNKNOWN, 1991 | 53b adder | 159b adder is 7 complex gates | p.12 |
errors_and_checks: The rounding precomputes all possible outcomes in parallel and selects the correct one, which assumes the outcomes are computable by a compound adder and that the carry point is known in advance.   # p.3
conditions: The study is stated to be independent of the partial-product reduction implementation, and the exponent path is omitted as not critical.   # p.2
evidence: Section 2.1, Figure 1, Table 2, Table 5.

### two_path  (role: instantiates)
mechanism: The conventional critical path is exponent subtraction (ES), alignment right shift (RS), significand addition (SA), left shift for normalization (LS) and rounding (R), where R may overflow and force an extra 1-bit right shift. The dataflow splits on the absolute exponent difference: at a difference of at most 1 the RS step reduces to a muxing step, and above 1 the result needs at most a 1-bit left shift, so the critical path is RS then SA plus R, or SA then LS, never both. The R step is combined with the SA step for the IEEE standard, a CSA adding r as determined by a rounding logic before a compound adder computing A + B + (0,1). One mux selects between the compound adder results and a second between the two paths.
choices:
  path_threshold: 1   # p.3
  close_path_trigger: exp_diff_only   # p.3
  path_select_point: late_result_mux   # p.4
new_choices: none
slots:
  sig_adder: compound_flagged_prefix [outputs=sum_sum1]   # p.4, p.14 (the FADD of MAC needs two compound adders because of the two-path arrangement)
  exp: exponent_path   # p.3 (ES is an 11b subtraction of the exponents)
  far_align: full_align   # p.3 (53b input shifted by up to 53 bits, decoder delay included)
  near_lz: lza   # p.3 (leading-one prediction)
parameters: 53b significand, 11b exponent; T53bRS = T; TES = 0.6T; 53b LOP = 1.1T; 53b mux = 0.2T; two 53b compound adders, one 53b left shifter, one 53b LOP, one 53b CLA for rounding.   # p.12, p.15
results:
| metric | value | unit | technology / device | baseline | condition | page |
| FADD latency | 3.4T + Tw(FADD) | T = 53b add delay | CMOS, node UNKNOWN, 1991 | — | shift-add path taken as critical path | p.12 |
| 53b leading-one prediction delay | 1.1T | T = 53b add delay | CMOS, node UNKNOWN, 1991 | 53b add = T | LOP is about ten percent slower than an adder of the same length | p.12 |
errors_and_checks: none
conditions: Tw(FADD) is typically larger than Tw(FMPY) because of the two-path arrangement, so TFADD is taken equal to TFMPY.   # p.4, p.12
evidence: Section 2.2, Figure 2, Table 2, Table 5.

### bridge_fma  (role: compares)
mechanism: The FMPY and FADD critical paths are not overlapped. An indirection path between the multiplier and the adder makes the configuration multiply-add-chained (MAC), the chaining used in vector processors. Because MAF need not be supported, the adder and the multiplier are separately optimized, which avoids the additional loading an MAF implementation puts on them. The MAF latency is the sum of the FMPY and FADD latencies, and the FADD latency is the plain FADD latency.
choices:
  composition_style: cascade_mul_then_add   # p.5
  cascade_product_rounding: active_ieee_mode [outside domain]   # p.1, p.2
new_choices: none
slots:
  align: full_align   # p.3
  lza: lza   # p.3
  cpa: compound_flagged_prefix [outputs=sum_sum1]   # p.14
  round: compound_adder_select   # p.2
parameters: 53x53 Wallace tree, 53b right shifter, 53b left shifter, 53b compound adder for FADD, 53b compound adder for FMPY, 53b LOP, 53b CLA for rounding.   # p.15
results:
| metric | value | unit | technology / device | baseline | condition | page |
| hardware cost | APR + 5.5A + Aw(FADD) + Aw(FMPY) | A = 53b compound adder area | 3-metal CMOS, node UNKNOWN, 1991 | — | static implementation, Table 6 | p.15 |
| MAF latency | TFMPY + TFADD | T = 53b add delay | CMOS, node UNKNOWN, 1991 | — | Eqn (3) | p.6 |
errors_and_checks: The result is that of a sequential IEEE FMPY followed by an IEEE FADD, which is the document's definition of an IEEE-compatible MAF.   # p.1
conditions: MAC has the smallest FADD latency and the least area but the highest MAF latency of the three, so it is a reasonable strategy for applications with a high percentage of stand-alone FADDs.   # p.13, p.15
evidence: Section 3.1, Figure 3b, Table 5, Table 6, Table 7.

### classic_fma  (role: compares)
mechanism: Greedy fully overlaps the RS - Add path of FADD with the PR - Add path of FMPY, giving PR/ES/RS - Add - LS - R. The addend exponent Ec is incremented by 53 so c is only right shifted during alignment, through a 106b shifter, and shift distances beyond 106 bits are accumulated for rounding information; the RS/6000 does the same with a triple-width 159b shifter. The shifted c is added to the higher-order 53 bits of S and C in the CSAs, with c or S and C complemented according to the effective operation, and an LOP determines the normalization left shift. Rounding cannot be combined with the addition because the carry point and the normalization shifter input both depend on the shift distance, so an explicit R step follows LS.
choices:
  subsume_fp_add: true   # p.8, p.15 (the FADD latency equals the MAF latency and the FADD compound adder is shared)
  negation_handling: complement_recode   # p.6
new_choices: none
slots:
  align: full_align   # p.6
  lza: lza   # p.6 (106b LOP)
  cpa: compound_flagged_prefix [outputs=sum_sum1]   # p.15 (106b compound adder)
  round: increment_adder   # p.8 (53b increment, then a mux for the 1b right shift when the incremented result overflows)
parameters: Greedy: 53x53 Wallace tree, 106b right shifter, 106b left shifter, 106b compound adder, 106b LOP, 53b CLA, 53b incrementer (0.8T). RS/6000: 159b right and left shifters, 159b compound adder, 159b LOP, 53b CLA.   # p.6, p.12, p.15
results:
| metric | value | unit | technology / device | baseline | condition | page |
| hardware cost, Greedy | APR + 7A + Aw(Greedy) | A = 53b compound adder area | 3-metal CMOS, node UNKNOWN, 1991 | — | static implementation, Table 6 | p.15 |
| hardware cost, RS/6000 | APR + 8.5A + Aw(RS/6000) | A = 53b compound adder area | 3-metal CMOS, node UNKNOWN, 1991 | — | static implementation, Table 6 | p.15 |
| MAF latency, Greedy | TPR + TCSA + T106bLOP + T106bLS + TR + Tinc + TMUX + Tw(Greedy) | T = 53b add delay | CMOS, node UNKNOWN, 1991 | — | Eqn (5) | p.8 |
| FADD latency, Greedy | equal to its MAF latency | T = 53b add delay | CMOS, node UNKNOWN, 1991 | — | Eqn (6) | p.8 |
errors_and_checks: Three pieces of rounding information must be computed and combined for the IEEE modes: the 106b right shifter computes rounding information from c, the sticky bit logic sums the lower-order 53 bits of S and C, and a third piece comes from the lower-order bits of the left shifter output. The RS/6000 MAF is not IEEE compatible and forces the user to perform multiply and add separately; it trades for higher internal data precision, which facilitates elementary functions.   # p.1, p.7, p.13
conditions: Greedy is faster than RS/6000 because the higher internal precision of RS/6000 requires wider and therefore slower datapaths. Greedy trades FADD latency, hardware and rounding complexity for low MAF latency, and is recommended together with RS/6000 when rounding for the IEEE standard is not a requirement and the MAF to FADD ratio is high.   # p.13, p.15, p.16
evidence: Section 3.2, Figure 3c, Figure 4, Eqns (5)-(6), Tables 5-7.

### multipath_fma  (role: proposes)
mechanism: SNAP partially overlaps the two critical paths as PR/ES - Add/RS - LS/Add, combining only the Add step of the Add - LS path. Two 53b shifters shift S and C during MAF and the operands c and d during FADD, d being ignored during MAF; they span 106b to keep the bits shifted out and share the sticky-bit logic by a rounding mask, a string of ones followed by a string of zeros, ANDed with the lower-order shifter outputs, the mask transition point giving the carry point and the mask also producing a rounding constant of the correct weight. The multiplier side adds and rounds S and C, and its rounding constant rMul is passed to the adder-side rounding logic. A row of 4-2 CSAs reduces S, C, c and the aggregate rounding mask to two terms, summed by a compound adder.
choices:
  path_count: 2   # p.11
  path_select_criterion: exponent_difference   # p.10 (six cases on Eaxb versus Ec; the path-splitting difference is 2 rather than 1 because the summation of S and C may overflow)
new_choices: none
slots:
  align: full_align   # p.8 (two 53b shifters spanning 106b)
  lza: lza   # p.15 (53b LOP)
  cpa: compound_flagged_prefix [outputs=sum_sum1]   # p.11 (51b compound adder computing S + C + r + (0,1))
  round: compound_adder_select   # p.11 (r is added in the CSA step and the compound adder computes only the two results)
parameters: 53x53 Wallace tree; two 53b shifters spanning 106b; 4-2 CSA row (0.3T); 51b compound adder; carry point at bit 51 in both paths; up to five outcomes S + C + (0,4); 53b left shifter; 53b LOP; 53b CLA.   # p.8, p.11, p.15
results:
| metric | value | unit | technology / device | baseline | condition | page |
| hardware cost, SNAP | APR + 7A + Aw(SNAP) | A = 53b compound adder area | 3-metal CMOS, node UNKNOWN, 1991 | — | static implementation, Table 6 | p.15 |
| MAF latency, SNAP | TPR + TCSA + T53bAdd + TR + TCSA(4-2) + T53bAdd + TR + 2TMUX + Tw(SNAP) | T = 53b add delay | CMOS, node UNKNOWN, 1991 | — | Eqn (7), the RS step hidden in the multiplier-side addition | p.8 |
| FADD latency, SNAP | TES + T53bRS + TCSA(4-2) + TR + 2TMUX + Tw(SNAP) | T = 53b add delay | CMOS, node UNKNOWN, 1991 | — | Eqn (8), shift-add path as critical path | p.10 |
| MAF latency ordering | SNAP < Greedy < MAC < RS/6000 | ordering | CMOS, node UNKNOWN, 1991 | MAC | Eqn (9) | p.13 |
| FADD latency ordering | MAC < SNAP < Greedy < RS/6000 | ordering | CMOS, node UNKNOWN, 1991 | MAC | Eqn (10) | p.13 |
| area ordering | MAC < Greedy < SNAP < RS/6000 | ordering | 3-metal CMOS, node UNKNOWN, 1991 | MAC | Eqn (11); ASNAP > AGreedy because Aw(SNAP) > Aw(Greedy) | p.15 |
errors_and_checks: All six exponent cases are shown to round for the IEEE standard. In the path where S and C are shifted by at least 3 bits the rounding mask contributes at most 3 x 0.0625 and the sum of S and C ranges over [0,2), so the fraction range is [0,2.1875); in the path where c is shifted by at most 2 bits, c contributes up to 0.75 and the range is [0,2.75). Both need five outcomes, S + C + (0,4), and a 51-bit compound adder. In Case 5 the overflow needed to determine rMul must be computed by a carry-lookahead tree because S and C are not yet added.   # p.10, p.11
conditions: SNAP has the lowest MAF latency and a small FADD latency increase over MAC and area increase over Greedy, paid for in wire complexity and design complexity, and Tw(SNAP) > Tw(Greedy). It is the implementation to prefer if latency is the main concern.   # p.8, p.13, p.15, p.16
evidence: Section 3.3, Section 3.3.1, Figure 3d, Figure 5, Table 1, Eqns (7)-(11), Tables 5-7.

## new_families
none

## space_gaps
* a rounding-contract choice on the FMA families: the document defines an IEEE-compatible MAF as delivering the same result as a sequential FMPY and FADD, which classic_fma, multipath_fma and bridge_fma cannot record, while the RS/6000 single-rounded MAF with higher internal precision is called not IEEE compatible   # p.1, p.13
* a carry-point choice on the rounding slot: bit 51 for a multiplier, a function of the alignment shift distance once an addend is aligned, and bit 51 again for both SNAP paths   # p.3, p.6, p.11
* a choice for the number of precomputed candidate sums the rounding selection needs: five outcomes S + C + (0,4) for SNAP against two for the multiplier   # p.3, p.11
* compound_flagged_prefix.implementation has no conditional-sum value, although the compound adder is built from the conditional-sum local sum logic that high-speed adders already use and so costs little more than a plain adder   # p.12, p.14
* compound_flagged_prefix.topology has no Ling value, although the adder propagates its global carry by a modified Ling scheme   # p.12
* a shifter span choice separate from the maximum shift distance: the latency of a shifter follows its maximum shifting distance while its area follows its span, which is why SNAP's shifters cost A106b at T53b delay   # p.14

## open_questions
* Table 3 lists the latencies of the three implementations, but its values are absent from the extracted text; only the orderings of Eqns (9) and (10) are legible   # p.13
* Table 4's item names and Table 7's symbols are partly lost in the extracted text; the legible area values are A, A, 0.5A and 0.5A   # p.14, p.16
* The document assigns leading-one prediction to the shift-add path while the left shift step belongs to the add-shift path   # p.3
* The partial-product generation is not settled: the study is stated to be independent of the PR logic while the figures label it a 53x53 Wallace tree, so Booth recoding is neither asserted nor excluded   # p.2, p.7, p.9
* Greedy performs one addition and one rounding, and the document does not show that this delivers the sequential FMPY and FADD result its definition of IEEE compatibility requires   # p.1, p.6, p.13
* Table 5's unit counts and size columns interleave in the extracted text; the sizes read as MAC 53b, Greedy 106b, SNAP 106b right shifter with 53b left shifter, and RS/6000 159b   # p.15
