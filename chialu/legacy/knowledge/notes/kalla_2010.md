---
handle: kalla_2010
citation: R. Kalla, B. Sinharoy, W. J. Starke, M. Floyd, "Power7: IBM's Next-Generation Server Processor", IEEE Micro, vol. 30, no. 2, pp. 7-15, 2010.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_DOT_ACC, other]
formats: [fp64, decimal_floating_point]
authority: landmark
pages_read: 9 / 9
---

## summary
The paper describes the commercial Power7 processor and reports its arithmetic execution-unit organization rather than circuit-level arithmetic microarchitectures. Each core contains four double-precision FPU pipelines that execute multiply-add operations, a vector unit, two fixed-point units, and a hardware decimal floating-point pipeline (p.9).

## families
### classic_fma  (role: instantiates)
mechanism: Four FPU pipelines in each Power7 core can each execute double-precision multiply-add operations (p.9). The paper does not specify whether the operation uses one fused rounding, how the addend enters the multiplier path, or how alignment/normalization/rounding are implemented (pp.7-15).
choices:
new_choices:
  none
slots:
  none
parameters: 4 double-precision FPU pipelines per core; aggregate throughput 8 flops/cycle per core; pipeline depth, latency, and II are UNKNOWN (p.9)
results:
| metric | value | unit | technology / device | baseline | condition | page |
| FPU throughput | 8 | flops/cycle per core | IBM 45-nm SOI, 2010 | none | four double-precision FPU pipelines executing multiply-add operations | p.9 |
errors_and_checks: The arithmetic accuracy/rounding contract is UNKNOWN; detected soft errors can cause pipeline flush, refetch, and reexecution (pp.9, 14).
conditions: The throughput figure applies to one core with all four double-precision FPU pipelines (p.9). The paper reports no FPU-unit latency/area/power measurements (pp.7-15).
evidence: Power7 core design; Figure 2 and accompanying execution-unit description (pp.8-9); core-recovery description (p.14).

### commercial_decimal_fpu  (role: instantiates)
mechanism: Each Power7 core contains one decimal floating-point unit pipeline. The hardware unit, first introduced in Power6, accelerates commercial applications (p.9).
choices:
  implementation: hardware_dfu   # p.9
new_choices:
  none
slots:
  none
parameters: 1 decimal floating-point pipeline per core; datapath width, latency, II, and supported decimal formats are UNKNOWN (p.9)
results: none
errors_and_checks: Decimal arithmetic accuracy/rounding and unit-specific checking are UNKNOWN (pp.7-15).
conditions: The paper identifies commercial applications as the target but provides no decimal-operation throughput, latency, area, or power results (p.9).
evidence: Power7 core design and Figure 2 (pp.8-9).

## new_families
### pipeline_flush_retry  (domain: checker, closest: time_redundancy, why_not: Recovery is triggered by a detected fault and reexecutes flushed instructions through existing out-of-order resources rather than recomputing every operation with a transformation.)
mechanism: Power7 detects most soft errors and automatically flushes, refetches, and reexecutes affected pipeline instructions (p.9). Register-error recovery uses speculative execution resources and branch redirect capability rather than a dedicated recovery unit (pp.9, 14). Repeated failure can suspend the affected threads and resume them on another processor core (p.14).
choices: none
results: none
evidence: Power7 core design (p.9); Reliability, availability, and serviceability (pp.13-14).

## space_gaps
* The checker vocabulary lacks a recovery mechanism value for detection-triggered pipeline flush/refetch/reexecution using existing out-of-order resources (pp.9, 14).
* The checker vocabulary lacks an alternate-processor recovery value for migrating suspended threads after repeated instruction retry failure (p.14).

## open_questions
* The paper does not state whether the double-precision multiply-add operation is fused or singly rounded.
* The paper does not identify the FPU multiplier/CPA/rounding families or pipeline depth.
* The paper does not identify the decimal formats, datapath width, supported operations, or decimal significand arithmetic families.
* The paper does not describe the soft-error detectors, quantitative coverage, false-alarm behavior, or arithmetic-unit-specific fault model.
