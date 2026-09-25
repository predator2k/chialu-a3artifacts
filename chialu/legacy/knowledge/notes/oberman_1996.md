---
handle: oberman_1996
citation: S. F. Oberman and M. J. Flynn, "A Variable Latency Pipelined Floating-Point Adder", Euro-Par'96 Parallel Processing (LNCS 1124), Springer, 1996
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [fp64]
authority: landmark
pages_read: 183-192 / 10
---

## summary
The paper proposes a pipelined IEEE double-precision floating-point adder whose CLOSE-path operations can complete in one or two cycles while FAR-path operations complete in three cycles. SPECfp92 operand simulation reports an average latency as low as 2.25 cycles and a speedup of 1.33 over a fixed three-cycle Two Path adder, while maintaining one-cycle throughput. # p.187-192

## families
### variable_latency  (role: proposes)
mechanism: Both CLOSE and FAR paths begin speculatively in the first cycle. The exponent difference selects the path: FAR operations finish in three cycles, while CLOSE operations can finish in two cycles. Effective CLOSE-path additions and subtractions requiring only a small normalization shift can finish in one cycle. Early exponent and significand leading-one predictors notify the scheduler of the expected completion class, while collision logic pipes an early result into a later stage when the result bus is occupied. # p.187-190
choices:
  latency_classes: 3  # p.188-189
  case_detect: exponent_diff_predecode  # p.189-190
  worst_case_cycles: 3  # p.188
new_choices:
  short_shift_limit_bits: {0, 1, 2} — maximum CLOSE-path subtraction normalization shift permitted for first-cycle completion  # p.188, p.191
  collision_policy: pipe_to_later_stage — preserves FIFO result ordering when multiple stages can drive the result bus  # p.188-189
slots:
  round: compound_adder_select  # p.186-187
  align: full_align  # p.184-186
parameters: IEEE double precision; 64-bit operands; 1-bit sign; 11-bit biased exponent; 52-bit stored significand plus one hidden bit; three pipeline stages maximum; one-cycle initiation interval; subs0/subs1/subs2 short-shift variants  # p.184, p.186-191
results:
| metric | value | unit | technology / device | baseline | condition | page |
| average latency | 2.57 | cycles | UNKNOWN / 1996 | fixed three-cycle Two Path adder with combined rounding | Two Cycle variant; SPECfp92 | p.190-191 |
| average-latency speedup | 1.17 | speedup | UNKNOWN / 1996 | fixed three-cycle Two Path adder with combined rounding | Two Cycle variant; SPECfp92 | p.190-191 |
| average latency | 2.37 | cycles | UNKNOWN / 1996 | fixed three-cycle Two Path adder with combined rounding | adds variant; first-cycle CLOSE-path effective additions; SPECfp92 | p.191 |
| average-latency speedup | 1.27 | speedup | UNKNOWN / 1996 | fixed three-cycle Two Path adder with combined rounding | adds variant; SPECfp92 | p.191 |
| average latency | 2.25 | cycles | UNKNOWN / 1996 | fixed three-cycle Two Path adder with combined rounding | subs2 variant; first-cycle shifts up to 2 bits; SPECfp92 | p.191 |
| average-latency speedup | 1.33 | speedup | UNKNOWN / 1996 | fixed three-cycle Two Path adder with combined rounding | subs2 variant; SPECfp92 | p.191 |
| throughput | 1 | cycle | UNKNOWN / 1996 | fixed three-cycle Two Path adder with combined rounding | result collisions pipe earlier results into later stages | p.188-189 |
errors_and_checks: IEEE rounding is retained. Round-to-nearest uses precomputed sum and sum+1; directed round-to-positive/round-to-minus-infinity additionally require sum+2 to handle overflow followed by a one-bit right normalization shift. # p.186-187
conditions: Dynamic instruction scheduling with out-of-order completion is required to exploit reduced latency. # p.184 Dynamic SPECfp92 traces place 43% of operations on the CLOSE path and 57% on the FAR path. # p.190 CLOSE-path operations comprise 20% effective additions and 23% effective subtractions. # p.190-191 Result-bus collisions increase some early-result latencies to three cycles without reducing throughput. # p.188-189 One-cycle scheduling requires early completion prediction in less than 8 gate delays, or about half a cycle. # p.189-190
evidence: §3.1-3.2, Fig. 2, §4, Fig. 3, Fig. 4, pp.187-191

### two_path  (role: instantiates)
mechanism: The significand datapath separates CLOSE operations with exponent difference d less than or equal to 1 from FAR operations with d greater than 1. Operand swapping makes conversion and rounding additions mutually exclusive. The CLOSE path handles cancellation normalization, while the FAR path handles full alignment. Leading-one prediction proceeds in parallel with significand addition. Compound adders precompute sum/sum+1 so final rounding becomes result selection. # p.185-187
choices:
  path_threshold: 1  # p.185
  close_path_trigger: exp_diff_only  # p.185
  path_select_point: early_exponent_compare  # p.185-188
new_choices:
  none
slots:
  round: compound_adder_select  # p.186-187
  far_align: full_align  # p.185-186
  near_lz: lza  # p.185
parameters: IEEE double precision; CLOSE when d is less than or equal to 1; FAR when d is greater than 1; three pipeline stages with combined rounding; one-cycle initiation interval  # p.184-187
results:
| metric | value | unit | technology / device | baseline | condition | page |
| fixed latency | 3 | cycles | UNKNOWN / 1996 | UNKNOWN | Two Path adder with combined rounding in a high-speed processor | p.186-187 |
| throughput | 1 | cycle | UNKNOWN / 1996 | UNKNOWN | pipelined implementation | p.185-187 |
errors_and_checks: Round-to-nearest precomputes sum and sum+1. Round-to-positive and round-to-minus-infinity require sum+2, implemented with a half-adder row above the FAR-path significand adder. # p.186-187
conditions: The two-path structure requires an additional significand adder and a final path-select multiplexor. # p.185 Combined rounding reduces the pipeline from four stages to three, but both path adders must produce sum and sum+1. # p.186-187
evidence: §2.2-2.4 and Fig. 1, pp.185-187

## new_families
none

## space_gaps
* `variable_latency` lacks a `near_lz` or early-completion-predictor slot for the exponent and significand leading-one predictors used to classify one-cycle results. # p.189-190
* `variable_latency` lacks choices for the first-cycle normalization-shift limit and result-bus collision policy. # p.188-191

## open_questions
* The paper does not identify the circuit family or topology of the compound significand adders.
* The paper does not report technology node, area, power, clock frequency, or absolute delay.
* The reported average latencies do not state whether modeled result-bus collisions are included.
