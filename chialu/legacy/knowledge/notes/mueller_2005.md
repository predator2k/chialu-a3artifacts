---
handle: mueller_2005
citation: S. M. Mueller et al., "The Vector Floating-Point Unit in a Synergistic Processor Element of a CELL Processor", ARITH-17, pp. 59-67, 2005
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC, VEC_SFU]
formats: [fp32, fp64, int16, int32]
authority: landmark
pages_read: 9 / 9
---

## summary
The paper describes the floating-point unit of the Synergistic Processor Element of the 1st generation CELL processor: four 32b single-precision FMA cores (SPfpu), one 64b double-precision FMA core (DPfpu) and a 128-bit frontend, both cores built on a conventional FMA pipeline. The SPfpu reaches a 6-cycle latency at an 11FO4 cycle time by trading IEEE features (denormals forced to zero, no infinity or NaN, round-towards-zero only, non-trapping) against a shorter fraction path, a sum-addressed aligner, a compound-adder fraction adder and an exponent rounder that pre-computes its candidates. The DPfpu folds its 160-bit intermediate fractions into 2 to 3 rows to fit a 60-bit-wide floorplan, and the paper compares the SPfpu against a single-precision version of Seidel's dual-path FMA.

## families
### classic_fma  (role: instantiates)
mechanism: Both cores are conventional fused-multiply-add pipelines (p.59). The SPfpu is fully pipelined with 2 stages for aligner and multiplier, 2 for adder and LZA, and 2 for normalizer, rounder and result forwarding; the multiplier computes A*B while the aligner shifts C, a 3:2 adder compresses the aligned addend with the two partial products, the compound adder and the msb incrementer feed a result mux that also performs the first normalization shift, and the truncating backend reduces fraction rounding to a 4-port mux. The DPfpu has a 9-cycle pipeline: radix-4 Booth multiplier and sum-addressed alignment shifter in cycles 1-3, incrementer, end-around-carry adder and LZA in cycles 4-5, then a 4-cycle combined normalization shifter and rounder.
choices:
  subsume_fp_add: true — add, subtract and multiply execute as A*1+B and A*B+0 in the FMA pipe   # p.62
  negation_handling: end_around_carry — sum or absolute difference by the end-around-carry concept   # p.63, p.64
new_choices:
  flush_subnormals: true — SPfpu forces denormal operands and results to zero; DPfpu treats denormal operands as zero but computes denormal results per the standard   # p.61
  rounding_mode: round-towards-zero only (SPfpu); all four IEEE modes (DPfpu)   # p.61
  fma_operand_order: A*B+C (SPE) rather than A*C+B (PowerPC) — the operand order that removes the multiplexer from the multiplier inputs   # p.62
  subsume_integer_mac: true — 16x16b signed and unsigned integer multiply-adds and converts run as special multiply-adds after an extra formatter stage, reusing the single-precision multiplier   # p.61, p.62
  datapath_folding_rows: 2 to 3 — the wide intermediate fractions folded into rows to fit a narrow floorplan, which reshapes adder, LZA edge vector and normalization shifter   # p.64, p.65
slots:
  align: full_align — 96-bit SPfpu aligner, sum-addressed, in parallel with the multiplier; the DPfpu aligns in the same sum-addressed fashion   # p.63, p.64, p.66
  lza: lza — edge vector computed as in Hokenek-Montoye [6]; the one-position LZA error is corrected in the result mux, and in the DPfpu the folded edge vector drives two separate leading-zero counters instead of one 106-bit LZC   # p.63, p.64, p.65
  cpa: compound_flagged_prefix [outputs=sum_sum1] — a carry-look-ahead compound adder producing sum0 and sum1   # p.63
  round: none — the SPfpu truncates, so a 24b fraction incrementer is saved and rounding reduces to a 4-port result mux; the DPfpu's combined normalization/rounder is not specified further   # p.61, p.64
  norm_shifter: barrel_mux_tree — the DPfpu's third normalization stage is a standard binary barrel shifter of maximum shift 55, preceded by a select stage and a shift-by-54 stage; the SPfpu's first 25b shift is merged into the adder result mux   # p.63, p.65
  multiplier: booth_recoded_parallel [booth_radix=4] — DPfpu; the SPfpu multiplier is a full-size 24x24 whose recoding the document does not state   # p.64, p.66
parameters: 4 SPfpu cores of 32b, one 64b DPfpu core, 128b frontend, operand latches as 5- or 6-port mux latches (p.60); SPfpu 4-way SIMD SP and integer, DPfpu 2-way SIMD DP broken into two 64-bit operations (p.59, p.61); exponents 10b two's complement with 127 bias (p.64); DPfpu multiplier product 106 bits in carry-save folded into two rows, aligned addend 160 bits folded into ALNhi(0:52), ALNmid(53:107), ALNlo(105:160) (p.64); three instruction latencies of 6, 7 and 9 cycles (p.59, p.61).
results:
| metric | value | unit | technology / device | baseline | condition | page |
| cycle time | 11 | FO4 | IBM 90nm SOI-low-k, 2005 | — | SPE design point | p.59 |
| SP multiply-add latency | 6 | cycles | IBM 90nm SOI-low-k, 2005 | — | includes the 6FO4 global result forwarding | p.59 |
| SPfpu FMA core latency | 5.5 | cycles | IBM 90nm SOI-low-k, 2005 | — | core without the frontend | p.60 |
| convert / integer multiply / interpolate latency | 7 | cycles | IBM 90nm SOI-low-k, 2005 | 6-cycle FMA | extra formatter stage | p.61 |
| DPfpu latency | 9 | cycles | IBM 90nm SOI-low-k, 2005 | — | half-pumped | p.61 |
| DPfpu interface overhead | 4 | cycles | IBM 90nm SOI-low-k, 2005 | — | operand and result transfer to the side-placed DPfpu | p.61 |
| conventional SP FPU latency | about 100 | FO4 | UNKNOWN, 2005 | — | cited from [17]; the stated challenge is to save 40FO4 | p.59 |
| logic and latch budget | 60 | FO4 | IBM 90nm SOI-low-k, 2005 | — | after the 6FO4 forwarding | p.59 |
| latch insertion delay | 2 to 3 | FO4 | IBM 90nm SOI-low-k, 2005 | — | 20 to 30% of the 11FO4 cycle | p.60 |
| SPfpu latency saved by mux and pulsed latches | 10 to 12 | fo4 | IBM 90nm SOI-low-k, 2005 | latches without integrated mux | — | p.60 |
| max path delay difference between pipeline stages | 3 | % | IBM 90nm SOI-low-k, 2005 | — | — | p.60, p.67 |
| multiplier delay saving | 6 | FO4 | IBM 90nm SOI-low-k, 2005 | conventional block | Figure 2 | p.60 |
| LZA delay saving | 4 | FO4 | IBM 90nm SOI-low-k, 2005 | conventional block | Figure 2 | p.60 |
| normalizer delay saving | 5 | FO4 | IBM 90nm SOI-low-k, 2005 | conventional block | Figure 2 | p.60 |
| DPfpu fraction datapath width | 60 | bits | IBM 90nm SOI-low-k, 2005 | 160-bit full intermediate result | floorplan allocation, intermediates folded | p.64 |
| FPU area | 2 | mm^2 | IBM 90nm SOI-low-k, 2005 | — | four SPfpu cores, one DPfpu core, frontend | p.67 |
| max operating frequency | 5.6 | GHz | IBM 90nm SOI-low-k, 2005 | — | 1.41 V supply, 51 C | p.67 |
| SP peak performance | 44.8 | Gflops | IBM 90nm SOI-low-k, 2005 | — | — | p.67 |
errors_and_checks: The SPfpu deviates from IEEE 754-1985 on four points (p.61): denormal operands and results are forced to zero, exponent e=255 is a binade of normal numbers rather than infinity or NaN, overflow saturates to the maximum representable number, and only round-towards-zero is supported; a special exception flag is set when a denormal is forced to zero or a number in the extended range is encountered, and no trapping is supported. The DPfpu is IEEE-compliant except that denormal operands are treated as zero and NaN operands are not propagated, a generic NaN being computed whenever a NaN result occurs; it supports all four rounding modes and non-trapping exception handling (p.61). A zero addend, a zero product, or both zero are handled by a late correction that forces values into the aligner output or a true zero in the rounder (p.62). The LZA may overestimate the leading zeros by one; the SPfpu corrects it in the result mux (p.64) and the DPfpu prefixes the third shift stage's input with the LSB of the sum-high row so the leading one is not lost (p.65).
conditions: The architecture is tuned to real-time 3D graphics and multimedia streaming, whose target applications virtually only use truncation rounding and give infinity and NaN no real meaning (p.59, p.61). Single-precision operations in other rounding modes are emulated in the DPfpu by extend-to-double, double-precision operation, round-to-single, at lower performance (p.61). Divide and square root are left to software through the estimate and interpolate instructions (p.61). Integer multiplication is restricted to 16x16 bits so the single-precision multiplier can be reused without penalizing floating-point performance, and 32x32 products are composed in software (p.61). Truncation-only rounding moves the pressure onto the exponent logic, which becomes timing critical (p.61, p.64). Clock gating is applied at three levels: the whole FPU, the pipeline stages holding valid instructions, and opcode- and data-dependent gating within a stage, which disables the multiplier on add instructions and the incrementer and compound adder based on the alignment of addend and product (p.65, p.66).
evidence: Abstract, Sections 1-6, Section 8, Figures 1, 2, 6, Table 1.

### barrel_mux_tree  (role: extends)
mechanism: The alignment shifter consists of the exponent selection, an adder-decoder block that computes the decoded shift amount, four mux stages, and the bypass and control logic for special operands and shift saturation. A 4:2 carry-save adder compresses ea, eb, ec and the design constant K into a carry-save pair (s,t). Instead of a 7-bit adder followed by a decoder, a sum-addressed decoder partitions s and t into 2-bit segments, computes for each segment the unary decode of s'+t' ignoring the carry-in through kill/propagate/generate signals and simple AOI functions, computes the group carries in a parallel carry network, and applies each group carry by rotating the decoded select signals left one bit position with a 2-port mux. The last stage is a 6-port mux latch that performs the wide shift, recomplements the addend on an effective subtraction and merges the bypass result.
choices:
  stage_radix: 4 — three radix-4 stages (0/1/2/3, 0/4/8/12, 0/16/32/48) and a shift-64 stage   # p.63
  select_encoding: one_hot_decoded — hot-1 mux select signals   # p.63
  stage_order: small_shift_first   # p.63
  sticky_collect: true — the aligner emits sticky(0:23) to the adder's sticky logic   # p.63
new_choices:
  shift_amount_source: sum_addressed_decode — the hot-1 selects are decoded directly from the carry-save shift-amount pair, so the 7-bit shift-amount adder is off the critical path   # p.63
slots: none
parameters: 96-bit SPfpu aligner (p.66); 7-bit shift amount (p.63); shift amount sha = ea + eb - ec + K for multiply-add and ea + '0' - eb + K for add type, the latter also expressible as ea + eb - 2eb + K (p.62); aligner outputs fraction(0:24), fraction(25:72), sticky(0:23) (p.63); DPfpu aligner output 160 bits in three rows (p.64).
results:
| metric | value | unit | technology / device | baseline | condition | page |
| aligner delay | 21 | FO4 | IBM 90nm SOI-low-k, 2005 | — | with the sum-addressed decode, tuned circuits and the fast mux latch | p.63 |
| aligner delay saving | 10 | FO4 | IBM 90nm SOI-low-k, 2005 | conventional aligner | Figure 2 | p.60 |
errors_and_checks: none
conditions: The shift amount computation is on the critical path of most aligner designs, which is what the sum-addressed decode removes (p.63). The exponent muxing for the two operand orders is done in parallel to the 3:2 compression of ea, eb, K, so it adds no delay (p.62, p.63). The exponent check runs in parallel to the aligner and is off the critical path (p.62).
evidence: Section 4.2, Figure 3, Section 4.1.2, Figure 2.

### compound_flagged_prefix  (role: instantiates)
mechanism: The fraction adder computes the sum or absolute difference of x and y with the end-around-carry concept: eac is the carry-out of x + !y, and r is x+y for add, x+!y+1 for subtract with eac=1, and !(x+!y) for subtract with eac=0. A 3:2 adder compresses the main part of the aligned addend with the two partial products and passes the result to a carry-look-ahead compound adder producing sum0 and sum1 = sum0+1. The msb bits I(0:24) of the addend go to an incrementer computing I and I+1, both recomplemented on an effective subtraction, and the adder carry-out selects I0 or I1. An extra carry-only network speeds up cout, and the adder control pre-computes two sets of select signals for cout = 0 and 1. The exponent rounder uses an 8-bit 3:2 compressor and a 10-bit 3-way compound adder producing e, e+1 and e+2.
choices:
  outputs: sum_sum1 for the fraction adder; the 10-bit exponent adder produces sum, sum+1 and sum+2 [outside domain]   # p.63, p.64
  topology: carry-look-ahead [outside domain] — "carry-look-ahead compound adder"; in the DPfpu the carry-lookahead structure was rebalanced for the different wire delays caused by the folding   # p.63, p.65
new_choices:
  precomputed_select_sets: 2 — the control pre-computes select signals for both values of the adder carry-out and chooses between them before controlling the result mux   # p.63
slots: none
parameters: adder inputs carry(0:47) and sum(0:48) from the multiplier, fraction(25:72) from the aligner, I(0:24) from the aligner msbs, sticky(0:23) (p.63); outputs add_result(0:24) and add_result(25:47) (p.63); 48-bit carry tree on the SPfpu adder critical path, which runs through a full adder, the carry tree and a 2-port mux (p.66, p.67); exponent path ex(0:7), ey(0:7), ez(2:9) into an 8b 3:2 compressor and a 10b 3-way compound adder (p.64); er0 = e1 + !lz and er1 = e2 + !lz (p.64).
results:
| metric | value | unit | technology / device | baseline | condition | page |
| incrementer and adder delay saving | 4 | FO4 | IBM 90nm SOI-low-k, 2005 | conventional block | Figure 2 | p.60 |
| exponent rounder delay saving | 15 | FO4 | IBM 90nm SOI-low-k, 2005 | conventional block | Figure 2 | p.60 |
| normalizer and rounder stage improvement target | 15 to 20 | FO4 | IBM 90nm SOI-low-k, 2005 | conventional backend | required to meet the performance target | p.64 |
errors_and_checks: Overflow is detected by checking the 2 msb of er0 and er1 for '01', underflow by the sign of the decremented exponent, with er0 < 1 equivalent to sign(e + !lz) and er1 < 1 equivalent to sign(e1 + !lz) = sign(er0); Zero is UNF or fracZero or specialZero (p.64).
conditions: The computation of the select signals from cout is the critical path of any fraction adder (p.63). Pre-computing e, e+1 and e+2 in the earlier pipeline stages means none of the exponent rounder's adders and checkers requires a carry-in (p.64). The selection of sum0, sum1, !sum0 and of I0, I1 is combined with the first normalizer stage in 5-port mux latches, so the muxing delay is hidden by the latch insertion delay (p.63). The msb bits I only matter when the addend exponent exceeds the product exponent (p.63).
evidence: Sections 4.3, 4.4, 5, Figures 4, 5, Figure 2.

### pwl  (role: instantiates)
mechanism: The SPE defines the lookup and the interpolate step of the divide and square-root estimates as separate instructions. Two estimate instructions for 1/A and 1/sqrt|A| return a base and a slope value stored together in the fraction field of the result. That result is fed into an interpolate instruction which increases the precision of the estimate by linear approximation, and the interpolated result can be refined further by a Newton-Raphson step exploiting the FMA instruction. The estimate instructions execute in the fixed point unit and the interpolate instruction in the SPfpu, where it is one of the instructions that pass through the extra formatter stage.
choices: none
new_choices:
  estimate_interpolate_instruction_split: true — the table lookup and the linear interpolation are separate ISA instructions, with base and slope packed into the fraction field of the estimate result   # p.61
slots: none
parameters: functions 1/A and 1/sqrt|A|; interpolate instruction latency 7 cycles through the formatter stage (p.60, p.61).
results: none reported
errors_and_checks: The document states no accuracy figure for the estimate, the interpolate step or the Newton-Raphson refinement.
conditions: Estimate instructions composed of a lookup and an interpolate step in one instruction tend to have a longer latency than the standard FMA instruction when implemented with reasonable overhead (p.61). Splitting them lets software pipelining exploit the hardware and lets the estimate alone serve where low precision suffices, which is also why the SPE supports no atomic divide instruction (p.61).
evidence: Section 3.1, Section 3.

### multipath_fma  (role: compares)
mechanism: Seidel's designs adapt Farmwald's dual path algorithm for addition to fused-multiply-add. Depending on the alignment of addend and product, five cases are distinguished and implemented with different latencies. In the far-out path the addend is so much larger than the product that the fractions do not overlap, which is the fastest case. In the near path addend and product have roughly the same exponent and an effective subtraction can cause massive cancellation. A fixed-latency variant uses two parallel data paths, one implementing the four faster cases and one the slow near path.
choices:
  path_count: 5 cases in the variable-latency design, 2 parallel data paths in the fixed-latency design   # p.66
  path_select_criterion: exponent_difference — the alignment of addend and product   # p.66
new_choices: none
slots: none
parameters: near-case single-precision fraction data path = a full-size 24x24 multiplier with an extra term for the aligned addend, a 50-bit adder with integrated rounding function, a re-complement stage, a 50-bit normalization shifter, and the result mux with select logic that performs the post-normalization and merges special results and the second path's result (p.66); two full-size multipliers and adders overall (p.67).
results:
| metric | value | unit | technology / device | baseline | condition | page |
| far-out path latency | one third of the slow near path | ratio | UNKNOWN, 2005 | near path | fractions of addend and product do not overlap | p.66 |
| single-precision FPU area increase | about 50 | % | UNKNOWN, 2005 | SPfpu | two full-size multipliers and adders; the increase is larger for a double-precision design | p.67 |
| operand distribution and result collection delay | 5 | fo4 | UNKNOWN, 2005 | single data path | operands distributed to two data paths and results collected | p.67 |
| core latency vs SPfpu | about the same delay in logic levels | — | UNKNOWN, 2005 | SPfpu | after the SPfpu exponent-rounding and result-selection optimizations are applied to both | p.67 |
errors_and_checks: The dual-path design supports all four rounding modes at the same latency (p.67).
conditions: The variable-latency design suits processors that can benefit from a variable-latency FPU, such as out-of-order processors, while the fixed-latency variant suits in-order designs such as the SPE (p.66). The area overhead increases FPU power, results in a non-trivial placement problem and adds wire and transfer delay, which the paper judges unacceptable for a replicated multi-core building block (p.67).
evidence: Section 7.

### reduced_latency_fma  (role: compares)
mechanism: Lang and Bruguera [11] and Seidel [19] derive from the common FMA design by merging the addition and the rounding of the fraction, which reduces latency. Both focus on the fraction data path of a double precision multiply-add with normalized operands. The dual-path design uses an adder with integrated rounder, which requires extra hardware and latency for the leading-zero prediction.
choices:
  rounding_position: fused_with_cpa_dual_sum   # p.66
new_choices: none
slots: none
parameters: 50-bit adder with integrated rounding in the single-precision near path (p.66).
results:
| metric | value | unit | technology / device | baseline | condition | page |
| logic levels | fewer for Seidel's designs than for Lang and Bruguera's | levels | UNKNOWN, 2005 | Lang-Bruguera design | as shown in [19] | p.66 |
errors_and_checks: none
conditions: In the SPfpu the exponent rounding dominates the delay of the normalization-round stage of a single-precision FPU once the fraction rounding is removed, and the same effect is expected in a single-precision dual-path design that merges the fraction rounding with the adder; applying the SPfpu's exponent-rounding and result-selection optimizations makes the two normalization-round stages equally fast (p.66). Both cited designs assume normalized operands (p.66).
evidence: Section 7.

## new_families
none

## space_gaps
* `classic_fma` has no choice for subnormal handling or for which rounding modes the unit supports, although the SPfpu (flush to zero, round-towards-zero only) and the DPfpu (denormal results computed, all four modes) differ on exactly that; `bf16_fma_datapath` already declares `flush_subnormals` and `rounding_mode`   # p.61
* `classic_fma` has no choice for the operand order of the fused multiply-add (A*B+C versus A*C+B), which the document identifies as what removes the multiplexer from the multiplier inputs   # p.62
* `classic_fma` has no choice for reusing the FMA core for integer multiply-add through an extra formatter stage at one more cycle of latency   # p.61, p.62
* `classic_fma` has no choice for folding the wide intermediate fraction into 2 to 3 rows, which here changes the adder's carry-lookahead balancing, the LZA edge vector computation and the normalization shifter's stages   # p.64, p.65
* `barrel_mux_tree` has no choice for the shift-amount source, so the sum-addressed decode that removes the shift-amount CPA from the critical path cannot be recorded   # p.63
* `compound_flagged_prefix`'s `outputs` domain has no value for a compound adder producing sum, sum+1 and sum+2   # p.64
* `compound_flagged_prefix`'s `topology` domain lists only prefix topologies, so a carry-look-ahead compound adder has no value   # p.63
* no `lza` choice records a per-row split of the leading-zero count (two smaller LZCs over the folded edge rows instead of one 106-bit LZC)   # p.65
* no vocabulary choice records opcode- and data-dependent clock gating of the multiplier, incrementer and compound adder inside a pipeline stage   # p.66

## open_questions
* The SPfpu multiplier's recoding is not stated; Booth recoding appears only in a general timing argument (p.62) and the multiplier is called a "full size 24x24" (p.66).
* The SPfpu normalizer and rounder structure beyond the first 25b shift stage and the 4-port result mux is attributed to highly customized circuits and physical design rather than described (p.62, p.64).
* Whether the DPfpu's 4-cycle combined normalization shifter and rounder rounds by injection, by an increment or by selection is not stated (p.61, p.64).
* The estimate instructions' table size, segment count, slope format and accuracy are not given, and the estimates execute in the fixed point unit rather than in this FPU (p.61).
* The paper does not report separate area or power figures for the SPfpu core, the DPfpu core and the frontend inside the 2mm^2 total (p.67).
