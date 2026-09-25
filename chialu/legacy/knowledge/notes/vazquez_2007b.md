---
handle: vazquez_2007b
citation: Vazquez, Antelo, Montuschi, "A New Family of High-Performance Parallel Decimal Multipliers", 18th IEEE Symposium on Computer Arithmetic (ARITH-18), 2007
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [decimal64]
authority: incremental
pages_read: 280-287 / 8 pages
---

## summary
The document proposes a radix-10 SRT decimal floating-point divider that produces one signed quotient digit per iteration. The architecture uses BCD-5211 operands, parallel constant-comparison digit selection, and one customized decimal carry-propagate adder for divisor-multiple generation/residual updates/final conversion/rounding.

## families
### decimal_digit_recurrence  (role: proposes)
mechanism: The recurrence is w[i+1] = 10w[i] − qi+1d with the minimally redundant quotient set {−5,...,5}. The residual remains in non-redundant 10's-complement form because one decimal carry-propagate adder performs each residual update. Quotient selection runs in parallel from truncated estimates of 100w[i−1] and −10qid. The initialization selects x/20 or x/2 from the sign of x−d, and the final cycles assimilate the residual and compute round(Q*−10S)n.
choices:
  quotient_digit_set: minimally_redundant_m5_p5   # p.280
  digit_split: none   # p.280
new_choices:
  operand_digit_code: bcd5211 — coding used for the decimal operands and carry-save selection inputs   # p.281-282
  residual_representation: nonredundant_10s_complement — the shared carry-propagate adder keeps w[i] non-redundant   # p.280-281
  selection_estimate_truncation: binary_bit — estimates may end at any binary position inside a decimal digit   # p.282
  selection_constant_generation: arithmetic — truncated divisor multiples generate constants without a lookup table   # p.282-283
slots:
  digit_select: constant_comparison_qds [outside domain] [comparators=10, constant_source=arithmetic_multiple_generation]   # p.282,p.285
parameters: radix 10; one quotient digit per iteration; Decimal64 n=16 digits; l=70 bits; n+2 quotient digits; n+5 cycles; 21 cycles for n=16   # p.280-284
results:
| metric | value | unit | technology / device | baseline | condition | page |
| cycle time | 25.3 | FO4 | UNKNOWN (result year 2007) | Ref. [8]/Ref. [10] | Decimal64, 16 digits | p.286 |
| cycles per division | 21 | cycles | UNKNOWN (result year 2007) | Ref. [8]/Ref. [10] | Decimal64, 16 digits | p.286 |
| latency | 531 | FO4 | UNKNOWN (result year 2007) | Ref. [8]/Ref. [10] | Decimal64, 16 digits | p.287 |
| area | 10500 | NAND2 | UNKNOWN (result year 2007) | Ref. [8]/Ref. [10] | Decimal64, 70-bit datapath | p.286-287 |
| Ref. [8] cycle time | 26.8 | FO4 | UNKNOWN (result year 2007) | Proposed | delay re-estimated with the paper's model | p.287 |
| Ref. [8] cycles per division | 20 | cycles | UNKNOWN (result year 2007) | Proposed | Decimal64 | p.287 |
| Ref. [8] latency | 536 | FO4 | UNKNOWN (result year 2007) | Proposed | Decimal64 | p.287 |
| Ref. [8] area | 13500 | NAND2 | UNKNOWN (result year 2007) | Proposed | complexity supplied by Ref. [8] authors | p.287 |
| Ref. [10] cycle time | 35.8 | FO4 | UNKNOWN (result year 2006) | Proposed | Decimal128 implementation | p.287 |
| Ref. [10] cycles per division | 19 | cycles | UNKNOWN (result year 2006) | Proposed | comparison table | p.287 |
| Ref. [10] latency | 680 | FO4 | UNKNOWN (result year 2006) | Proposed | comparison table | p.287 |
| Ref. [10] area | 22600 | NAND2 | UNKNOWN (result year 2006) | Proposed | Decimal128 area extrapolated assuming linear scaling | p.287 |
| Ref. [5] cycle time | ≈22 | FO4 | Itanium 2 @ 1.4 GHz (result year 2007) | Proposed | software Decimal64 division | p.287 |
| Ref. [5] cycles per division | 294 | cycles | Itanium 2 @ 1.4 GHz (result year 2007) | Proposed | software Decimal64 division | p.287 |
| Ref. [5] latency | 6468 | FO4 | Itanium 2 @ 1.4 GHz (result year 2007) | Proposed | software Decimal64 division | p.287 |
errors_and_checks: The quotient uses guard/round digits, the residual sign, a sticky bit, the rounding mode, and a conditional +1 ulp increment; no numerical error bound is reported.   # p.281,p.284
conditions: Operands require normalization before the described significand datapath. The logical-effort evaluation includes gate loading/buffering but excludes wire delay. The Ref. [10] area comparison assumes optimistic linear scaling from Decimal128.   # p.281,p.286-287
evidence: §2-§3, Figs. 1-4, Tables 1-2, p.280-287

### speculative_decimal_addition  (role: extends)
mechanism: The shared 70-bit decimal adder recodes BCD-5211 inputs into BCD-5421 and BCD-5421-excess3. Four-bit binary additions then produce decimal carries, while two conditional digit sums are computed in parallel and selected by a sparse prefix carry tree. A late-carry network merges the optional rounding increment without another carry-propagation pass.
choices:
  speculation_target: digit_correction   # p.284-285
  recovery: dual_path_select   # p.285
  fused_ieee_rounding: true   # p.284-285
new_choices:
  digit_code_path: bcd5211_to_bcd5421_excess3_to_bcd5211 — input/internal/output coding sequence   # p.284-285
slots:
  carry_network: parallel_prefix [topology=q_t [outside domain], valency=4]   # p.284-285
parameters: 70-bit datapath; 16 decimal digits; 7 levels of sparse prefix logic; conditional +1 ulp increment   # p.282,p.284-286
results:
| metric | value | unit | technology / device | baseline | condition | page |
| adder datapath area | 2600 | NAND2 | UNKNOWN (result year 2007) | none | Table 1 logical-effort model | p.286 |
| adder datapath stage delay | 21.8 | FO4 | UNKNOWN (result year 2007) | none | wire delay excluded | p.286 |
errors_and_checks: No fault-checking mechanism or numerical error metric is reported.   # p.284-286
conditions: Decimal carries equal binary carries at decimal positions after the excess-3 recoding. BCD-5421 is used internally because conversion to/from BCD-5211 is simpler than conversion through BCD-8421.   # p.284
evidence: §3.2, Fig. 3, Table 1, p.284-286

### parallel_prefix  (role: instantiates)
mechanism: A quaternary sparse prefix tree computes decimal carry groups for the customized decimal adder. Sum digits are precomputed while the seven-level carry tree evaluates, and the resulting carries select the corresponding BCD-5211 digit sums.
choices:
  topology: q_t [outside domain]   # p.284
  valency: 4   # p.284
new_choices: none
slots: none
parameters: 7 logic levels; 70-bit decimal adder   # p.284-286
results:
| metric | value | unit | technology / device | baseline | condition | page |
| prefix-based decimal adder area | 2600 | NAND2 | UNKNOWN (result year 2007) | none | complete adder datapath | p.286 |
| prefix-based decimal adder stage delay | 21.8 | FO4 | UNKNOWN (result year 2007) | none | logical-effort estimate without wire delay | p.286 |
errors_and_checks: none
conditions: The prefix tree carries operate across decimal digit positions whose local carry signals are derived through BCD-5421/excess-3 recoding.   # p.284-285
evidence: §3.2, Fig. 3, Table 1, p.284-286

## new_families
### constant_comparison_qds  (domain: dividers / square root, closest: qds_table, why_not: the selection constants are generated arithmetically and tested by parallel comparators rather than stored in a QDS lookup table)
mechanism: Ten decimal comparators test a truncated two-word residual estimate against selection constants m−4 through m5. Each comparator uses a binary 3:2 carry-save reduction, BCD recoding, a prefix carry network, and a sign detector. A decoder converts the comparison vector into sign(qi+1), |qi+1| in one-hot form, and qi+1* in BCD-5211.
choices:
  constant_source: {arithmetic_multiple_generation, rom}
  estimate_cut: {binary_bit, decimal_digit}
  comparator_count: Int[10..10:1]
results:
| metric | value | unit | technology / device | baseline | condition | page |
| selection-function area | 3200 | NAND2 | UNKNOWN (result year 2007) | none | ten parallel decimal comparators | p.286 |
| selection-function stage delay | 22.3 | FO4 | UNKNOWN (result year 2007) | none | critical-path component before mux/latch | p.286 |
evidence: §2.2, §3.3, Figs. 2(b)/4, Table 1, p.282-286

## space_gaps
* `decimal_digit_recurrence.slot digit_select` needs a constant-comparison implementation in addition to `qds_table`.   # p.282,p.285
* `parallel_prefix.topology` lacks the quaternary Q-T sparse topology used by the decimal carry network.   # p.284
* `speculative_decimal_addition` lacks choices for BCD-5211/BCD-5421/excess-3 internal coding.   # p.284-285
* `decimal_digit_recurrence` lacks residual-representation/operand-coding/bit-level-estimation choices established by this design.   # p.280-282

## open_questions
* The exact IEEE-754R rounding modes supported by the rounding logic are not enumerated.   # p.284
* No fabrication technology or synthesized standard-cell library is identified for the logical-effort estimates.   # p.286
