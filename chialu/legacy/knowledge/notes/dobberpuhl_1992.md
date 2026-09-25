---
handle: dobberpuhl_1992
citation: D. W. Dobberpuhl, et al., "A 200-MHz 64-b Dual-Issue CMOS Microprocessor", IEEE Journal of Solid-State Circuits, vol. 27, no. 11, pp. 1555-1567, 1992.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, other]
formats: [int8, int16, int32, int64, fp32, fp64, vax32, vax64]
authority: landmark
pages_read: 13 / 13
---

## summary
The document describes a 200-MHz commercial 64-b processor containing a single-cycle hybrid carry-select adder, a pipelined radix-8 floating-point multiplier, and a nonpipelined single-bit-per-cycle divider. The floating-point unit accepts IEEE/VAX 32- and 64-b formats and returns one result per cycle except for division. # p.1557

## families
### sig_mul_then_round  (role: instantiates)
mechanism: The floating-point pipeline formats operands in cycle 4, generates the 3 x multiplicand, performs radix-8 array multiplication in cycles 5 and 6, and performs final addition and rounding in parallel in cycles 7 and 8. The selected result returns to the register file in cycle 9. # p.1557
choices: none
new_choices: none
slots:
  sig_mul: booth_recoded_parallel [booth_radix=8, hard_multiple_gen=cpa_precompute]   # p.1557
  round: compound_adder_select [final addition and rounding are parallel before result selection]   # p.1557
  exp: exponent_path   # p.1557
parameters: fp32/fp64 and VAX 32-/64-b formats; six-cycle latency with register-write bypass; II=1 cycle   # p.1557
results:
| metric | value | unit | technology / device | baseline | condition | page |
| floating-point latency | 6 | cycles | 0.75-µm 3.3-V n-well CMOS (1992) | none | register-write-data bypass allowed | p.1557 |
| initiation interval | 1 | cycle | 0.75-µm 3.3-V n-well CMOS (1992) | none | all floating-point operations except division | p.1557 |
| peak floating-point rate | 200 | MFLOPS | 0.75-µm 3.3-V n-well CMOS (1992) | none | complete CPU at 200 MHz | p.1555 |
errors_and_checks: IEEE and VAX standard rounding modes are supported; no numerical error bound, fault model, or checker is reported. # p.1557
conditions: All 32- and 64-b floating-point operations except division have the same timing. Division uses a separate nonpipelined unit. # p.1557
evidence: §IV and Fig. 3(b), p.1557

### booth_recoded_parallel  (role: instantiates)
mechanism: A radix-8 pipelined array multiplier handles both single- and double-precision multiplication. A first-stage adder generates the 3 x multiplicand before the array multiplication. # p.1557
choices:
  booth_radix: 8   # p.1557
  hard_multiple_gen: cpa_precompute   # p.1557
new_choices:
  pipeline_structure: pipelined_array — identifies the explicitly pipelined array organization   # p.1557
slots: none
parameters: single- and double-precision floating point; 3 x multiplicand generation in cycle 4; array multiplication in cycles 5 and 6   # p.1557
results:
| metric | value | unit | technology / device | baseline | condition | page |
| multiplication array time | 2 | cycles | 0.75-µm 3.3-V n-well CMOS (1992) | none | radix-8 array phase only | p.1557 |
| result throughput | 1 | 64-b result/cycle | 0.75-µm 3.3-V n-well CMOS (1992) | none | fully pipelined floating-point unit | p.1557 |
errors_and_checks: No multiplier error bound, fault model, or checker is reported. # p.1557
conditions: The reported timing includes separate 3 x generation before the array and parallel final addition/rounding after the array. # p.1557
evidence: §IV and Fig. 3(b), p.1557

### carry_select  (role: instantiates)
mechanism: The 64-b integer/FPU adder combines 8-b nMOS carry chains, a distributed 32-b long-word carry select, and local logarithmic carry select. Each propagate/kill/generate set drives two chains, one assuming carry-in and one assuming no carry. nMOS switches select the corresponding byte sums. # pp.1562-1563
choices:
  block_sizing: uniform   # p.1562
  duplication: full_duplicate   # pp.1562-1563
  select_source: nearest-neighbor byte carry-outs plus 32-b distributed lookahead [outside domain]   # pp.1562-1563
new_choices:
  block_width: 8 b — width of each duplicated carry-chain group   # p.1562
slots:
  block_adder: manchester_carry_chain [chain_segment_length=8, circuit_style=dynamic]   # pp.1562-1563
parameters: 64-b width; 8-b carry-chain groups; 32-b long-word regions; two latches on every path; single-cycle latency   # p.1562
results:
| metric | value | unit | technology / device | baseline | condition | page |
| adder latency | 1 | cycle | 0.75-µm 3.3-V n-well CMOS (1992) | none | complete 64-b integer/FPU adder | p.1562 |
| clock period | 5 | ns | 0.75-µm 3.3-V n-well CMOS (1992) | none | processor pipeline cycle containing the single-cycle ALU operation | p.1556 |
| maximum clock frequency | 200 | MHz | 0.75-µm 3.3-V n-well CMOS (1992) | none | fabricated processor | p.1555 |
errors_and_checks: No arithmetic error, fault model, or concurrent checker is reported. # pp.1562-1563
conditions: The 8-b chain width supports the architecture's byte-compare function. The distributed long-word carry select controls the upper 32-b output latch and remains outside the critical path. # pp.1562-1563
evidence: §VI-B, Fig. 12, and Fig. 13, pp.1562-1563

### manchester_carry_chain  (role: instantiates)
mechanism: Each 8-b chain uses nMOS pass devices and begins predischarged to VSS through a control formed from CLK and the kill function. Evaluation propagates through the chain without the VDD-Vt threshold delay associated with a chain precharged to VDD. Device widths taper from LSB to MSB, and ratioed inverters receive the local carry nodes. # pp.1562-1563
choices:
  chain_segment_length: 8   # p.1562
  circuit_style: dynamic   # pp.1562-1563
new_choices:
  predischarge_level: VSS — voltage to which the dynamic carry chain is predischarged   # p.1562
slots: none
parameters: 8-b chain; two chains per propagate/kill/generate set; one chain assumes carry-in and one assumes no carry   # pp.1562-1563
results:
| metric | value | unit | technology / device | baseline | condition | page |
| integrated adder latency | 1 | cycle | 0.75-µm 3.3-V n-well CMOS (1992) | none | chain used inside the complete 64-b hybrid adder | p.1562 |
errors_and_checks: No arithmetic error, fault model, or checker is reported. # pp.1562-1563
conditions: VSS predischarge avoids the threshold delay of VDD precharge. Predischarge to VDD-Vt was rejected because its noise margins were unacceptable. # p.1562
evidence: §VI-B and Fig. 13(a), pp.1562-1563

## new_families
none

## space_gaps
* `carry_select.select_source` needs a hybrid value covering nearest-neighbor block carry cascades combined with distributed long-word lookahead. # pp.1562-1563
* `carry_select` lacks an explicit `block_width` choice for the documented 8-b duplicated carry-chain groups. # p.1562
* `booth_recoded_parallel` lacks a pipeline-organization choice for the documented pipelined array. # p.1557
* The floating-point rounding slots name `compound_adder_select`, but the vocabulary provides no corresponding family definition for the documented parallel final-add/round selection. # p.1557

## open_questions
* The document does not specify the multiplier reduction-tree structure, sign-extension method, or negative-partial-product encoding. # p.1557
* The document identifies a nonpipelined, single-bit-per-cycle divider but does not state whether its recurrence is restoring, nonperforming, nonrestoring, or SRT. # p.1557
* The document does not provide enough topology detail to determine whether the “local logarithmic carry select” should also be classified as `conditional_sum`. # p.1562
* The document does not explicitly identify the floating-point adder as `single_path`, `two_path`, or `delay_optimized_unified`. # p.1557
