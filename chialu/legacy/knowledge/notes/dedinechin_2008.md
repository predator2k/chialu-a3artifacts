---
handle: dedinechin_2008
citation: F. de Dinechin, B. Pasca, O. Cret, R. Tudoran, "An FPGA-Specific Approach to Floating-Point Accumulation and Sum-of-Products", IEEE FPT, pp. 33-40, 2008
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [parameterized_fp, FP(7,16), fp32, fp64]
authority: incremental
pages_read: 33-40 / 8
---

## summary
The paper proposes an application-specific floating-point accumulator that keeps the running sum in a wide fixed-point register, which removes alignment/normalization shifts from the feedback loop. A partial carry-save variant divides carry propagation into configurable k-bit chunks. An exact unrounded multiplier feeding the accumulator produces a sum-of-products unit with one final normalization/rounding step.

## families
### streaming_accurate_accumulator  (role: proposes)
mechanism: Each floating-point summand is shifted into an application-bounded fixed-point window and accumulated as a two's-complement value. The feedback loop contains only fixed-point addition; input alignment and final leading-zero count/shift/round operations remain outside the loop. MSBA prevents accumulator overflow, LSBA controls accumulated truncation error, and MaxMSBX bounds the input shifter.
choices:
  approach: shifted_fixed_point_window   # p.34
  window_bits: 63   # p.38
  in_loop_normalization: false   # p.34
new_choices:
  msb_position: MSBA — highest accumulator bit, selected to bound the final sum   # p.35
  lsb_position: LSBA — lowest accumulator bit and accuracy/area control   # pp.35,37-38
  maximum_input_msb: MaxMSBX — highest expected summand bit and input-shifter bound   # p.35
  overflow_indicators: input_overflow/input_underflow/accumulator_overflow — sticky validity outputs   # pp.35,38
slots:
  cpa: fpga_carry_chain   # p.34
parameters: wE/wF parameterized; wA = MSBA−LSBA+1 in Fig. 4; case study MSBA=24, MaxMSBX=8, LSBA=−38, wA=63 bits; synthesized FP(7,16)/SP/FP(10,37)/DP configurations; accumulator II=1   # pp.35,38
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area / latency / frequency | 129 / 8 / 472 | slices / cycles / MHz | Virtex-4 -12, ISE10.1 (2008) | CoreGen: 304 slices + 1 DSP, 12 cycles @ 359 MHz | FP(7,16), MaxMSBX=1 | p.37 |
| area / latency / frequency | 176 / 9 / 484 | slices / cycles / MHz | Virtex-4 -12, ISE10.1 (2008) | same CoreGen row | FP(7,16), MaxMSBX=MSBA | p.37 |
| area / latency / frequency | 165 / 8 / 434 | slices / cycles / MHz | Virtex-4 -12, ISE10.1 (2008) | CoreGen: 317 slices + 4 DSP, 16 cycles @ 450 MHz | SP, MaxMSBX=1 | p.37 |
| area / latency / frequency | 229 / 9 / 434 | slices / cycles / MHz | Virtex-4 -12, ISE10.1 (2008) | same CoreGen row | SP, MaxMSBX=MSBA | p.37 |
| area / latency / frequency | 295 / 10 / 428 | slices / cycles / MHz | Virtex-4 -12, ISE10.1 (2008) | CoreGen: 631 slices + 1 DSP, 14 cycles @ 457 MHz | FP(10,37), MaxMSBX=1 | p.37 |
| area / latency / frequency | 399 / 11 / 428 | slices / cycles / MHz | Virtex-4 -12, ISE10.1 (2008) | same CoreGen row | FP(10,37), MaxMSBX=MSBA | p.37 |
| area / latency / frequency | 375 / 11 / 414 | slices / cycles / MHz | Virtex-4 -12, ISE10.1 (2008) | CoreGen: 771 slices + 3 DSP, 15 cycles @ 366 MHz | DP, MaxMSBX=1 | p.37 |
| area / latency / frequency | 516 / 12 / 416 | slices / cycles / MHz | Virtex-4 -12, ISE10.1 (2008) | same CoreGen row | DP, MaxMSBX=MSBA | p.37 |
| accuracy / area / latency | 2.0·10−16 / 247 / 10 @ 454 MHz | relative error / slices / cycles | Virtex-4 -12 (2008) | SP FP adder: 1.2·10−3, 317 slices + 4 DSP, 16 @ 450 MHz; DP FP adder: 2.8·10−15, 771 slices + 3 DSP, 15 @ 366 MHz | 20,000,000 SP summands from case study | p.38 |
| relative error | 1.05e−07; 1.07e−08; 1.07e−09; −3.57e−09 | relative error | UNKNOWN (2008) | FP adder: −5.76e−05; −2.74e−04; −4.31e−04; −0.738 | FP(7,16), 32-bit accumulator; unif[0,1], sum sizes 1000/10,000/100,000/1,000,000 | p.38 |
| relative error | 1.40e−04; 2.36e−04; −2.73e−04; −4.47e−05 | relative error | UNKNOWN (2008) | FP adder: −1.59e−05; −3.04e−04; 2.54e−03; 3.18e−03 | FP(7,16), 32-bit accumulator; unif[−1,1], same sum sizes | p.38 |
errors_and_checks: Inputs whose LSB is at or above LSBA are accumulated exactly; otherwise each addition has error at most 2^(LSBA−1), giving a stated worst-case n-fold bound over n terms. Post-normalization to FP(7,16) has relative rounding error at most 2^−17 ≈ 0.76·10^−5. Sticky input-overflow/input-underflow/accumulator-overflow bits support a posteriori validity checking.   # pp.37-38
conditions: Application bounds or profiling must provide MSBA/MaxMSBX/LSBA. The design benefits accumulations whose running sum is needed every cycle or whose FP-adder recurrence cannot be interleaved. A post-normalizer may be omitted, shared among N accumulators, or run at 1/N frequency when only occasional results are required. All synthesis results precede place-and-route.   # pp.34-37
evidence: Figures 3-4; §§3.1-3.2, 3.4-3.5, 4.1-4.3; Tables 1-4, pp.34-38.

### carry_save_datapath  (role: extends)
mechanism: The accumulator cuts its carry propagation into k-bit chunks by inserting registers between chunks. The feedback critical path becomes one k-bit addition. Setting k=1 gives standard carry-save representation; larger k exploits FPGA carry logic while reducing register overhead. Final carries are resolved either by injecting zeroes for several cycles or by a pipelined propagation stage outside the feedback loop.
choices:
  compressor: 3_2   # p.36
  assimilation_point: end_of_chain   # p.36
  accumulator_redundant: true   # p.36
new_choices:
  carry_chunk_bits: k — carry propagation permitted within each registered chunk   # p.36
  final_resolution: zero_injection_or_pipelined_propagation — selectable redundant-to-standard conversion   # p.36
slots:
  assimilator: fpga_carry_chain   # p.36
parameters: k=4 in Fig. 5; k=1 produces standard carry-save; k=32 targets 400MHz; final zero-injection latency is ceil((MSBA−LSBA)/k) cycles   # p.36
results:
| metric | value | unit | technology / device | baseline | condition | page |
| frequency | 400 | MHz | Virtex-4 and Stratix II (2008) | 64-bit direct accumulator: more than 220 MHz on Virtex-4 -12 | k=32 partial carry-save | pp.34,36 |
| register overhead | 1/32 more | registers | current FPGAs (2008) | direct accumulator | 400MHz accumulation | p.36 |
errors_and_checks: The redundant representation requires explicit carry resolution before a standard result is observed; no numerical approximation is introduced.   # p.36
conditions: Partial carry-save is used when the native FPGA carry chain cannot reach the target frequency. Zero-injection resolution applies when only the final sum is needed; pipelined propagation applies when the running value is needed.   # p.36
evidence: Figure 5 and §3.3, p.36.

### multi_term_fused_dot  (role: proposes)
mechanism: Each significand multiplication returns every product bit without normalization or rounding. Products are shifted directly into the fixed-point accumulator, which defers normalization and rounding until the accumulated result is converted back to floating point. The accumulator may be dimensioned so that all products are accumulated exactly.
choices:
  alignment_strategy: single_wide_window   # p.39
  rounding_contract: truncated_with_guard   # pp.37-39
  normalization_deferral: final_only   # p.39
new_choices:
  product_rounding: none — the multiplier emits its complete 2+2wF-bit significand   # p.39
slots:
  align: bounded_align   # pp.35,39
parameters: exact multiplier input significand 1+wF bits; output significand 2+2wF bits; SP× with DP accumulator; DP× with 105-bit accumulator   # p.39
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area / latency / frequency | 319 + 4 / 13 / 363 | slices + DSP / cycles / MHz | Virtex-4 -12, ISE10.1 (2008) | CoreGen SP×, SP+: 484 slices + 8 DSP, 26 cycles @ 366 MHz | SP×, DP accumulator | p.39 |
| area / latency / frequency | 1441 + 9 / 23 / 279 | slices + DSP / cycles / MHz | Virtex-4 -12, ISE10.1 (2008) | CoreGen DP×, DP+: 1241 slices + 19 DSP, 37 cycles @ 366 MHz | DP×, 105-bit accumulator | p.39 |
errors_and_checks: Multiplication introduces no rounding error because every product bit is retained. Accumulation is exact when LSBA is no higher than every product LSB and MSBA prevents overflow; otherwise the accumulator error follows the LSBA bound.   # pp.37-39
conditions: The exact multiplier removes rounding/normalization logic but doubles the accumulator input-shifter width. The reported sum-of-products synthesis results are preliminary.   # p.39
evidence: §5 and Table 5, p.39.

## new_families
none

## space_gaps
* streaming_accurate_accumulator lacks MSBA/LSBA/MaxMSBX, although these three application bounds define the architecture's range, shifter size, and accuracy.   # pp.35,37-38
* carry_save_datapath lacks the partial-carry chunk length k and the zero-injection versus pipelined final-resolution choice.   # p.36
* multi_term_fused_dot lacks an explicit exact-unrounded floating-point multiplier slot/value.   # p.39

## open_questions
* Table 1 calls the designs “2wF accumulator[s]” while the accompanying transcription states MSBA=wE and LSBA=−wE; the merge pass must not resolve this notation conflict.   # pp.36-37
* The paper reports preliminary sum-of-products synthesis and states that the FloPoCo multiplier generator still requires improvement, so the results are not post-place-and-route measurements.   # pp.36,39
