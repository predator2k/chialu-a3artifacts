---
handle: venkataramani2012
citation: S. Venkataramani, A. Sabne, V. Kozhikkottu, K. Roy, A. Raghunathan, "SALSA: Systematic Logic Synthesis of Approximate Circuits", 49th Design Automation Conference (DAC), pp. 796-801, 2012
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_DOT_ACC, other]
formats: [int8, int32]
authority: landmark
pages_read: 796-801 / 6
---

## summary
SALSA automatically synthesizes functionally approximate circuits from an exact RTL circuit and a Boolean quality constraint. SALSA converts quality-permitted behavior into Approximation Don’t Cares and applies conventional don’t-care logic optimization while preserving the specified error bound. The experiments cover adders, multipliers, a MAC, and larger signal-processing datapaths.

## families
### approximate_logic_synthesis  (role: proposes)
mechanism: A Quality Constraint Circuit combines the original circuit, the current approximate circuit, and a Q-function whose output indicates whether the quality constraint holds. SALSA computes output-specific observability don’t cares at the Q-function, expresses those Approximation Don’t Cares in terms of primary inputs, installs them as external don’t cares, and simplifies one output cone per iteration. The approximate circuit updates after every output, which preserves the invariant that Q is a tautology for all input combinations. # pp.797-799
choices:
  method: qf_substitution   # pp.797-799
  error_constraint: absolute_error_bound, relative_error_bound [outside domain]   # p.798
new_choices:
  quality_constraint_encoding: boolean_q_function — The Q-function maps original and approximate outputs to one bit that indicates compliance.   # pp.797-798
  synthesis_backend: off_the_shelf_logic_synthesis — ADCs are mapped to EXDCs for optimization by SIS or Synopsys Design Compiler.   # pp.799-800
  scalability_heuristic: equate_unapproximated_outputs, quality_function_decomposition, input_output_dependency_restriction, subset_adc_computation — The options reduce ADC-generation complexity.   # pp.799-800
slots:
  none
parameters: 32-bit RCA/KSA/CLA; 8-bit array/Wallace multipliers; 8-bit MAC with 32-bit accumulator; 8-bit SAD/EU DIST/BUT/FIR/IIR/DCT benchmarks; one iterative approximation pass per output bit; three synthesis-tool calls per iteration   # pp.799-800
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area improvement | 1.1X to 1.85X | X | IBM 45nm (2012) | original exact circuit | error-magnitude constraint less than 1% | p.800 |
| area improvement | up to 4.75X | X | IBM 45nm (2012) | original exact circuit | error-magnitude constraint up to 20% | p.800 |
| power improvement | 1.15X to 1.75X | X | IBM 45nm (2012) | original exact circuit | error-magnitude constraint less than 1% | p.800 |
| power improvement | 1.3X to 5.25X | X | IBM 45nm (2012) | original exact circuit | error-magnitude constraint up to 20% | p.800 |
| area improvement | up to 1.7X | X | IBM 45nm (2012) | original exact circuit | relative-error metric | p.800 |
| power improvement | up to 1.65X | X | IBM 45nm (2012) | original exact circuit | relative-error metric | p.800 |
| synthesis execution time | 4 minutes | minutes | AMD Opteron 6176, 2.29 GHz, 198 GB RAM (2012) | none | smaller circuits, including adders | p.801 |
| synthesis execution time | 2.5 hours | hours | AMD Opteron 6176, 2.29 GHz, 198 GB RAM (2012) | none | DCT datapath | p.801 |
errors_and_checks: The error-magnitude Q-function enforces |POorig − POapprox| ≤ K, and the relative-error Q-function enforces 1−K ≤ POapprox/POorig ≤ 1+K. SALSA preserves Q=1 for every input combination, so the specified bound is never transgressed. No fault model, alias rate, or false-alarm behavior is reported.   # pp.797-798
conditions: The quality metric must be expressible as a Boolean function of the original and approximate output bits. Exact output-by-output ADC construction preserves the quality bound. Q-function decomposition loses some optimization potential because it propagates the worst possible error across stages. Input/output dependency restriction and subset ADC computation reduce synthesis complexity for larger circuits.   # pp.798-800
evidence: §3.1-3.4, Algorithm 1, Figures 1-5, Table 1, §5-6, Figures 6-7, pp.797-801

## new_families
none

## space_gaps
* The `error_constraint` domain lacks a pointwise relative-error bound distinct from mean relative error and the document’s absolute error-magnitude bound.   # p.798
* The family lacks a choice for Boolean quality-function encoding and its correct-by-construction tautology invariant.   # pp.797-798
* The family lacks choices for ADC/EXDC transformation and output-wise iterative synthesis.   # pp.798-799
* The family lacks scalability choices for Q-function decomposition, input/output dependency restriction, and subset ADC computation.   # pp.799-800

## open_questions
* Equation 2 does not state how the relative-error Q-function handles POorig=0.
* The paper does not report per-benchmark numerical area/power values in text, and the supplied Figure 6/7 rendering does not permit reliable point extraction.
* The paper does not state signedness for the integer benchmarks.
