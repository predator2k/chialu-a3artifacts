---
handle: grohoski_1990
citation: G. F. Grohoski, "Machine Organization of the IBM RISC System/6000 Processor", IBM Journal of Research and Development, vol. 34, no. 1, pp. 37-58, 1990
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [ieee_floating_point]
authority: landmark
pages_read: 37-58 / 22
---

## summary
The document describes the IBM RISC System/6000 machine organization and instantiates a two-cycle pipelined floating-point multiply-add unit. Register renaming and fixed-point/floating-point synchronization overlap memory operations with arithmetic while preserving precise interrupts. The document defers the multiply-add arithmetic dataflow to a companion paper.

## families
### classic_fma  (role: instantiates)
mechanism: The FPU contains a pipelined multiply-add unit. FMA accepts four register operands, multiplies the second and third operands, adds the fourth operand, and stores the result in the first operand. # p.39 FPE1 and FPE2 form the first and second/final multiply-add execution cycles. # p.40 Register renaming permits floating-point loads to overlap earlier arithmetic operations. # pp.49-53 The arithmetic dataflow itself is deferred to a companion paper. # pp.41,58
choices:
  pipeline_depth: 2   # p.40
new_choices:
  none
slots:
  none
parameters: four register operands; two execution cycles; pipelined operation; IEEE floating-point format with precision UNKNOWN   # pp.39-40,56
results:
| metric | value | unit | technology / device | baseline | condition | page |
| FMA execution latency | 2 | cycles | AMERICA; VLSI CMOS; node UNKNOWN; year UNKNOWN | none | FPE1 followed by final stage FPE2 | p.40 |
| arithmetic result throughput | 2 | floating-point results/cycle | AMERICA; VLSI CMOS; node UNKNOWN; year UNKNOWN | none | 2D graphics loop; pipeline 100% busy; one multiply and one add | p.41 |
| arithmetic-pipeline utilization | 100% | busy | AMERICA; VLSI CMOS; node UNKNOWN; year UNKNOWN | none | 2D graphics inner loop; finite cache effects ignored | p.41 |
| inner-loop performance | 50 | MFLOPS | AMERICA; VLSI CMOS; node UNKNOWN; year UNKNOWN | none | 2D graphics inner loop at a 40-ns clock cycle; finite cache effects ignored | p.41 |
| inner-loop performance | 28 | MFLOP rate | IBM RS/6000; node UNKNOWN; year UNKNOWN | AMERICA at 50 MFLOPS | Same 2D graphics code; implementation problems reduced throughput | p.41 |
| loop-iteration latency | 7 | cycles | IBM RS/6000; node UNKNOWN; year UNKNOWN | AMERICA at 4 cycles | 2D graphics example; IEEE-format store handling sends stores through floating-point decode | p.57 |
| LINPACK performance | approximately 11 | MFLOPS | IBM RS/6000; node UNKNOWN; year UNKNOWN | none | LINPACK benchmarks | p.37 |
| LINPACK performance | nearly 11 | MFLOPS | IBM RS/6000; node UNKNOWN; year UNKNOWN | AMERICA potential approximately 15 MFLOPS | IEEE-format implementation after floating-point control changes | p.57 |
errors_and_checks: The document states that the RS/6000 uses IEEE floating-point arithmetic format, but it reports no precision/rounding/ulp/error contract. # pp.56,58
conditions: The reported two-results-per-cycle throughput requires the shown loop to keep the floating-point pipeline 100% busy. # p.41 Fixed-point/floating-point synchronization adds two stages before floating-point execution without delaying arithmetic instructions that await cache data. # p.47 IEEE-format normalization forces floating-point stores through the decoder, which reduces peak loop performance. # pp.56-57
evidence: FMA semantics on p.39; pipeline stages in Figure 2 and its definitions on pp.40-41; synchronization in Figure 5 and discussion on pp.47-49; register renaming in Figure 6/Table 1 and discussion on pp.49-53; implementation changes and performance comparison on pp.56-57.

## new_families
none

## space_gaps
* none

## open_questions
* The document does not identify the floating-point precision, significand multiplier, final CPA, alignment/LZA structure, negation handling, or rounding implementation; those details are deferred to the companion floating-point-unit paper. # pp.37,41,58
* The document does not state whether the multiply-add performs one IEEE rounding or separate multiply/add roundings. # pp.39,56
