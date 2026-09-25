---
handle: watson_1972
citation: W. J. Watson, "The TI ASC - A Highly Modular and Flexible Super Computer Architecture", Proc. AFIPS Fall Joint Computer Conference, pp. 221-228, 1972.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_DOT_ACC]
formats: [int16, int32, hexadecimal_fp32, hexadecimal_fp64]
authority: landmark
pages_read: 221-228 / 8
---

## summary
The document describes the TI ASC central processor, whose one to four pipelined arithmetic units execute scalar/vector fixed-point and hexadecimal floating-point operations (pp.223-225). Each arithmetic unit partitions receiver/exponent-subtract/align/add/normalize/multiply/accumulate/output work into stages capable of accepting outputs every 60 ns, while double-length multiplication and division require multiple cycles (p.225). The instruction set includes vector dot product and matrix multiplication, but the document does not disclose their arithmetic reduction structures (p.223).

## families
### single_path  (role: instantiates)
mechanism: Figure 7 routes floating-point addition serially through shared arithmetic-unit partitions that include a receiver register, exponent subtraction, alignment, addition, normalization, accumulation, and output. The arithmetic unit supports the same pipelined organization for scalar and vector execution (pp.224-225).
choices:
new_choices:
  none
slots:
  none
parameters: 32-bit and 64-bit hexadecimal floating-point operands; 64-bit parallel arithmetic unit; 60 ns basic cycle; one arithmetic unit per processor pipeline (pp.223-225)
results:
| metric | value | unit | technology / device | baseline | condition | page |
| pipeline throughput | 1 | result every 60 ns | UNKNOWN / TI ASC / 1972 | none | sustained vector mode, per arithmetic unit | p.224 |
errors_and_checks: none
conditions: The arithmetic unit achieves its highest sustained flow rate in vector mode (p.224). Double-length multiplication and all division operations use combinations of arithmetic-unit components and require more than one clock cycle (p.225). The document does not specify rounding, subnormal handling, adder topology, alignment structure, normalization structure, or operation latency (p.225).
evidence: Central Processor and Arithmetic Unit sections; Figures 5 and 7 (pp.223-225)

## new_families
### shared_partitioned_arithmetic_pipeline  (domain: fp/dot/mul/div/adder, closest: single_path, why_not: single_path covers floating-point addition rather than a shared multi-operation scalar/vector arithmetic pipeline)
mechanism: One arithmetic unit accompanies each memory-buffer pipeline. Eight exclusive arithmetic partitions implement receiver register, exponent subtraction, alignment, addition, normalization, multiplication, accumulation, and output functions. An operation uses selected combinations of these partitions, and each partition can provide an output every 60 ns. The processor contains one to four such pipelines, while double-length multiplication and division reuse component combinations over multiple cycles (pp.224-225).
choices: pipeline_count: Int[1..4:1]; partition_count: Int[8..8:1]; scalar_vector_reuse: Bool
results:
| metric | value | unit | technology / device | baseline | condition | page |
| basic cycle time | 60 | ns | UNKNOWN / TI ASC / 1972 | none | each arithmetic unit | p.225 |
| sustained vector throughput | 1 | result every 60 ns per AU | UNKNOWN / TI ASC / 1972 | none | highest sustained flow rate in vector mode | p.224 |
| configured vector throughput | 1 to 4 | vector results every 60 ns | UNKNOWN / TI ASC / 1972 | none | one to four execution units | p.223 |
| arithmetic width | 64 | bits | UNKNOWN / TI ASC / 1972 | none | most scalar and vector instructions | p.225 |
evidence: Central Processor and Arithmetic Unit sections; Figures 5 and 7 (pp.223-225)

## space_gaps
* The vocabulary lacks a family for operation-dependent routing through shared exponent-subtract/align/add/normalize/multiply/accumulate pipeline partitions across scalar and vector instructions (p.225).

## open_questions
* Figure 7 does not identify the adder, multiplier, aligner, normalizer, accumulator, or rounding microarchitectures (p.225).
* The document names vector dot-product and matrix-multiplication instructions without specifying product reduction, accumulation, or rounding structures (p.223).
* The document does not state the cycle counts or component schedules for double-length multiplication and division (p.225).
