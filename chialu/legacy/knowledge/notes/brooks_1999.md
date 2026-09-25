---
handle: brooks_1999
citation: D. Brooks, M. Martonosi, "Dynamically Exploiting Narrow Width Operands to Improve Processor Power and Performance", Proc. HPCA-5, pp. 13-22, 1999
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int16, int64]
authority: incremental
pages_read: 10 / 10
---

## summary
The paper proposes runtime operand-width detection for clock-gating unused upper ALU bits and dynamically packing independent narrow operations into one 64-bit integer ALU. The evaluated mechanisms reduce simulated integer-unit power and increase simulated performance without compiler intervention.

## families
### lane_width_gating  (role: proposes)
mechanism: Result-producing hardware detects leading zeros, or leading ones for negative two's-complement values, and stores narrow-width tags with operands in the RUU. A 16-bit tag gates the high 48 input-latch bits and selects zeros onto the high result bits; a second threshold recognizes values requiring 33 bits or less. The same tags let issue logic pack compatible narrow operations instead of gating lanes. # pp.17-19
choices:
  detection: msb_zero_detect   # p.17
  gating: clock_gate   # p.17
  operation_packing: true   # p.19
new_choices:
  width_thresholds: {16, 33} — operand-width cutoffs controlling gated portions and result selection   # p.17
  signed_detection: {parallel_zero_and_ones_detect} — leading ones identify narrow negative two's-complement operands   # p.17
  optimization_mode: {power_gating, operation_packing} — the shared hardware performs only one optimization at a time   # p.19
  load_detection: {enabled, omitted} — load-time detection determines whether cache-sourced opportunities are recognized   # p.17
slots:
  none
parameters: 64-bit Alpha datapath; low 16 bits always active; high 48 bits selectively gated; 16-bit and 33-bit thresholds; 80-entry RUU; baseline 4-wide fetch/decode/issue/commit; four integer ALUs   # pp.15,17
results:
| metric | value | unit | technology / device | baseline | condition | page |
| integer-unit power reduction | 54.1 | % | SimpleScalar Alpha processor model, technology UNKNOWN, 1999 | 64-bit units with opcode-based clock gating | SPECint95 average; operand-based 16-bit and 33-bit gating | p.18 |
| integer-unit power reduction | 57.9 | % | SimpleScalar Alpha processor model, technology UNKNOWN, 1999 | 64-bit units with opcode-based clock gating | MediaBench average; operand-based 16-bit and 33-bit gating | p.18 |
| estimated total-processor power reduction | 5-6 | % | high-end CPU model, technology UNKNOWN, 1999 | integer unit contributes about 10% of processor power | SPECint95-like average | p.18 |
| zero-detect power | 4.2 | mW | estimated dynamic-logic model at 3.3V and 500Mhz, technology UNKNOWN, 1999 | none | 48-bit zero detection | p.18 |
| additional-mux power | 3.2 | mW | estimated dynamic-logic model at 3.3V and 500Mhz, technology UNKNOWN, 1999 | none | clock-gating result muxes | p.18 |
| missed power-saving instructions | 13.1 | % | SimpleScalar Alpha processor model, technology UNKNOWN, 1999 | detection on loads enabled | SPECint95 if load zero-detect is omitted | p.17 |
| missed power-saving instructions | 1.5 | % | SimpleScalar Alpha processor model, technology UNKNOWN, 1999 | detection on loads enabled | MediaBench if load zero-detect is omitted | p.17 |
errors_and_checks: none
conditions: Both operands must fit the selected width before upper-bit clock gating is allowed. # p.17; Detection on incoming loads is required to recognize cache-sourced opportunities. # p.17; Clock gating and operation packing cannot be used simultaneously, although one implementation can select between them. # p.19; The power estimates assume dynamic logic, relatively fast carry-lookahead adders, and multiplier power scaling linearly with operand size. # p.18; Clock-network savings are excluded because they require a chip floorplan. # p.18
evidence: §§4.1-4.4; Figures 3-7; Table 4, pp.16-19

### partitioned_carry_chain  (role: extends)
mechanism: Issue logic combines ready instructions performing the same arithmetic/logical/shift operation when their operands carry narrow-width tags. Operand muxes place independent low 16-bit values into separate lanes of one 64-bit ALU, and the ALU stops carries at 16-bit boundaries. Four result-bus carry lines support lane overflow handling. Replay packing admits an operation with only one narrow operand, forwards the larger operand's high 48 bits, and reissues the operation at full width if a carry crosses the 16-bit boundary. # pp.19-20
choices:
  boundary_mechanism: carry_kill_gate   # p.19
new_choices:
  packing_policy: {both_operands_narrow, one_operand_narrow_with_replay} — exact packing requires two narrow operands; speculative packing permits one   # p.20
  compatibility_rule: {same_operation} — packed instructions must perform the same operation   # p.20
slots:
  none
parameters: 64-bit ALU partitioned into four 16-bit paths; four extra carry-out lines; arithmetic/logical/shift operations; multiply excluded; evaluated at decode widths 4 and 8 instructions/cycle   # pp.19-20
results:
| metric | value | unit | technology / device | baseline | condition | page |
| SPECint95 speedup | 4.3 | % | SimpleScalar Alpha processor model, technology UNKNOWN, 1999 | 4-issue/4-ALU baseline | 4-wide decode; combining branch predictor | p.20 |
| SPECint95 speedup | 7.1 | % | SimpleScalar Alpha processor model, technology UNKNOWN, 1999 | 4-issue/4-ALU baseline | 4-wide decode; perfect branch prediction | p.20 |
| MediaBench speedup | 8.0 | % | SimpleScalar Alpha processor model, technology UNKNOWN, 1999 | 4-issue/4-ALU baseline | 4-wide decode; combining branch predictor | p.20 |
| MediaBench speedup | 7.6 | % | SimpleScalar Alpha processor model, technology UNKNOWN, 1999 | 4-issue/4-ALU baseline | 4-wide decode; perfect branch prediction | p.20 |
| SPECint95 speedup | 6.2 | % | SimpleScalar Alpha processor model, technology UNKNOWN, 1999 | 4-issue/4-ALU baseline | 8-wide decode; combining branch predictor | p.21 |
| SPECint95 speedup | 9.9 | % | SimpleScalar Alpha processor model, technology UNKNOWN, 1999 | 4-issue/4-ALU baseline | 8-wide decode; perfect branch prediction | p.21 |
| MediaBench speedup | 10.4 | % | SimpleScalar Alpha processor model, technology UNKNOWN, 1999 | 4-issue/4-ALU baseline | 8-wide decode; realistic branch predictor | p.21 |
| MediaBench speedup | 10.3 | % | SimpleScalar Alpha processor model, technology UNKNOWN, 1999 | 4-issue/4-ALU baseline | 8-wide decode; perfect branch prediction | p.21 |
errors_and_checks: Replay packing detects a carry beyond the 16-bit lane, squashes the speculative execution, and reissues the instruction at full width; no numerical error is committed. # p.20
conditions: Packed instructions must be ready, must have compatible narrow-width operands, and must perform the same operation. # p.20; Replay traps are required when only one operand is narrow. # p.20; Existing multimedia muxing and segmented-carry hardware reduce datapath cost, while issue-selection complexity remains the primary cost. # p.20; The evaluated packing set excludes multiplication. # p.19
evidence: §§5.1-5.4; Figures 8-11, pp.19-21

## new_families
none

## space_gaps
* lane_width_gating lacks a width-threshold choice for the independently useful 16-bit and 33-bit detections. # p.17
* lane_width_gating detection lacks parallel leading-zero/leading-one detection for signed two's-complement operands. # p.17
* partitioned_carry_chain lacks a speculative one-narrow-operand packing policy with replay on cross-lane carry. # p.20

## open_questions
* The paper does not quantify the area or timing cost of the added tags, muxes, carry lines, and issue logic.
* The paper does not identify a fabrication technology for the simulated power estimates.
* The paper does not state how signed narrow-operation packing preserves lane semantics beyond noting added issue-logic complexity.
