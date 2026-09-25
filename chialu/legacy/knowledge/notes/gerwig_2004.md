---
handle: gerwig_2004
citation: G. Gerwig, H. Wetter, E. M. Schwarz, J. Haess, C. A. Krygowski, B. M. Fleischer, M. Kroener, "The IBM eServer z990 Floating-Point Unit", IBM Journal of Research and Development, 2004
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [hfp32, hfp64, hfp128, fp32, fp64, fp128, int32, int64, int128]
authority: landmark
pages_read: 12 / 12
---

## summary
The IBM z990 FPU combines binary/hexadecimal floating-point formats in a five-stage fused multiply-add dataflow with one multiply-add per cycle. A separate 116-bit SRT engine performs radix-4 division, radix-2 square root, and variable-iteration integer division. The implementation handles most denormalized inputs/results without pipeline stalls.

## families
### classic_fma  (role: proposes)
mechanism: The main fraction dataflow aligns the addend while a radix-4 Booth multiplier reduces the product, adds both in E3, counts leading zeros, normalizes in E4, and rounds in E5. Separate internal BFP/HFP representations accommodate their different exponent biases. Feedback paths forward normalizer/rounder/results to reduce dependency stalls. # p.313–316
choices:
  pipeline_depth: 5   # p.313–314
new_choices:
  internal_format_policy: separate BFP/HFP representations with their own biases — permits both architectures without conversion cycles   # p.313
  denormal_input_handling: late Booth-term correction plus late aligner selection — handles denormalized inputs without stalls   # p.314–315
slots:
  align: full_align   # p.313–315
  lza: lzc_after_add   # p.313, p.315
  round: compound_adder_select   # p.315–316
  multiplier: booth_recoded_parallel [booth_radix=4]   # p.313–314
parameters: 56-bit A/B/C registers; 176-bit aligned dataflow; 116-bit adder/normalizer/rounder; five execution stages; II=1 multiply-add/cycle   # p.313–315, p.319–320
results:
| metric | value | unit | technology / device | baseline | condition | page |
| throughput | 1 | multiply-add operation per cycle | IBM 0.13-µm CMOS SOI / z990 / 2004 | none | fused multiply-add | p.311, p.320 |
| latency | 5 | cycles | IBM 0.13-µm CMOS SOI / z990 / 2004 | none | fused multiply-add | p.320 |
| FPU area | 3.76 | mm² | IBM 0.13-µm CMOS SOI / z990 / 2004 | none | complete FPU | p.319 |
| clock frequency | 1.2 | GHz | IBM 0.13-µm CMOS SOI / z990 / 2004 | none | 1.15 V, 50°C | p.319 |
errors_and_checks: BFP rounding uses the LSB/round/sticky bits and the architectural rounding mode; no numerical-error result is reported. One unmasked-underflow case with denormalized addend/product invokes a millicode exception handler. # p.315–316
conditions: Most denormalized inputs/results remain in the normal flow. The exceptional case already requires an architectural underflow exception. # p.314–315
evidence: Figure 2 and pipeline-stage description, p.313–314; Figure 3 and rounding description, p.315–316; physical implementation, p.319; summary, p.320.

### booth_recoded_parallel  (role: instantiates)
mechanism: A 56 × 56-bit radix-4 Booth multiplier produces 29 partial products. Four 3:2-counter stages reduce 30 inputs to eight in E1, and four more stages plus one 3:2 stage reduce the tree before the main addition. A late correction term repairs an assumed implied unit bit when a denormalized multiplicand is detected. # p.313–315
choices:
  booth_radix: 4   # p.314
  hard_multiple_gen: none   # p.314
new_choices:
  denormal_correction_entry: late counter-tree term — corrects the multiplicand implied unit bit within E1   # p.314–315
slots:
  reduction: csa_reduction_tree   # p.313–314
parameters: 56 × 56 bits; 29 partial products; eight counter-tree levels   # p.314
results:
| metric | value | unit | technology / device | baseline | condition | page |
| partial products | 29 | rows | IBM 0.13-µm CMOS SOI / z990 / 2004 | none | 56 × 56-bit radix-4 Booth encoding | p.314 |
errors_and_checks: none
conditions: The late correction term does not significantly increase multiplier delay. # p.314
evidence: Figure 2, p.313; multiplier description/equations, p.314–315.

### srt_high_radix  (role: instantiates)
mechanism: The 116-bit divider uses radix-4 SRT with a maximally redundant quotient digit set {-3,-2,-1,0,+1,+2,+3}. The partial remainder remains in sum/carry form because a full-width CPA does not fit the cycle. The quotient digit splits into signed multiples of 1D and 2D selected from five partial-remainder bits and two divisor bits. # p.315–318
choices:
  radix: 4   # p.315–316
  digit_redundancy: maximal   # p.316
new_choices:
  carry_storage_granularity: one carry bit per four sum bits — reduces remainder-register latches/area/power   # p.316, p.318
slots:
  digit_select: qds_table   # p.316–317
parameters: 116-bit dataflow; two quotient bits per cycle; quotient digits {-3..+3}; table input 5 partial-remainder bits + 2 divisor bits; 116-bit sum + 28-bit carry remainder register   # p.315–318
results:
| metric | value | unit | technology / device | baseline | condition | page |
| total latency | 30 | cycles | IBM 0.13-µm CMOS SOI / z990 / 2004 | none | IEEE short divide | p.319 |
| total latency | 39 | cycles | IBM 0.13-µm CMOS SOI / z990 / 2004 | none | IEEE long divide | p.319 |
| total latency | 82 | cycles | IBM 0.13-µm CMOS SOI / z990 / 2004 | none | IEEE extended divide | p.319 |
| pipelined latency | 25 | cycles | IBM 0.13-µm CMOS SOI / z990 / 2004 | none | IEEE short divide | p.319 |
| pipelined latency | 34 | cycles | IBM 0.13-µm CMOS SOI / z990 / 2004 | none | IEEE long divide | p.319 |
| pipelined latency | 77 | cycles | IBM 0.13-µm CMOS SOI / z990 / 2004 | none | IEEE extended divide | p.319 |
| divider area | 0.22 | mm² | IBM 0.13-µm CMOS SOI / z990 / 2004 | complete FPU area | about 6% of FPU | p.319 |
errors_and_checks: The partial remainder is exact, so rounding requires no back-multiplication. # p.312
conditions: SRT improves short/extended-format performance and permits extended width, but it requires somewhat more area and performs worse for long-format instructions. # p.312
evidence: Tables 1–2, p.319; Figures 4–5 and divider implementation, p.316–318; physical implementation, p.319.

### digit_recurrence_sqrt_combined  (role: instantiates)
mechanism: Square root reuses the divider remainder/subtractor, invert/select logic, quotient registers, and merged lookup table. The radix-2 recurrence develops one root bit per cycle with digits {-1,0,+1}; the partial remainder and root remain redundant until Qpos and Qneg are combined in the main FPU adder. # p.315–318
choices:
  radix: 2   # p.315–316
  shared_with_division: true   # p.317
  on_the_fly_conversion: false   # p.318
new_choices:
  shared_lookup_table: merged divide/square-root table — uses three partial-remainder bits for square-root selection   # p.317
slots:
  digit_select: qds_table   # p.316–317
parameters: up to 116-bit operand dataflow; one root bit per cycle; digit set {-1,0,+1}   # p.315–318
results:
| metric | value | unit | technology / device | baseline | condition | page |
errors_and_checks: none
conditions: The similar divide/square-root structures add square root with “very little additional hardware”; no square-root latency or area number is reported. # p.317
evidence: Square-root recurrence, p.316; Figures 4–5 and implementation, p.317–318.

### self_timed_variable_latency  (role: extends)
mechanism: Integer division normalizes positive operands, computes the effective quotient width from normalized dividend/divisor widths, and sets start/stop pointers so leading-zero quotient iterations are skipped. The shared SRT engine therefore executes only the required radix-4 iterations. Idle divider hardware can be clock-disabled. # p.312, p.318–319
choices:
  mechanism: early_termination   # p.318–319
  shared_int_fp_datapath: true   # p.315, p.318–319
new_choices:
  idle_clock_gating: true — divider clock is switched off when no divide executes   # p.312
slots:
  digit_select: qds_table   # p.316–319
parameters: int32/int64/int128 supported; 1–32 divide-loop cycles for the reported integer-divide path   # p.315, p.319
results:
| metric | value | unit | technology / device | baseline | condition | page |
| total latency | 30–61 | cycles | IBM 0.13-µm CMOS SOI / z990 / 2004 | fixed maximum-iteration predecessors | integer divide | p.319 |
| pipelined latency | 25–56 | cycles | IBM 0.13-µm CMOS SOI / z990 / 2004 | fixed maximum-iteration predecessors | integer divide | p.319 |
errors_and_checks: none
conditions: Integer operands must be positive and normalized before division. Performance improves when the quotient has many leading zeros. # p.318–319
evidence: Integer-divide execution and Table 2, p.318–319; SRT tradeoffs, p.312.

## new_families
none

## space_gaps
* `compound_adder_select` appears as a round-slot value but lacks a declared family; Figure 3 shows parallel incrementers and multiplexers for 24/53/113-bit rounded fractions. # p.316
* `srt_high_radix` lacks a choice for sparse carry storage, although the design stores one carry bit per four sum bits and reports latch/area/power savings. # p.318, p.320
* `classic_fma` lacks choices for dual BFP/HFP internal representations and late denormal correction. # p.313–315

## open_questions
* The paper calls the E1–E5 path five pipeline steps but also labels load/decode/writeback cycles E−1/E0/E6; the merge pass must not count those as FMA pipeline depth. # p.313–314
* The topology/circuit family of the 116-bit main carry-propagate adder is not disclosed. # p.313, p.319
* Square-root execution latency is not reported separately. # p.315–320
