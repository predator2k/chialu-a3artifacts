---
handle: mittal2016
citation: S. Mittal, "A Survey of Techniques for Approximate Computing", ACM Computing Surveys, vol. 48, no. 4, 2016
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_SFU, VEC_DOT_ACC, other]
formats: [int, fp]
authority: survey
pages_read: 34 / 34
---

## summary
The survey classifies approximate-computing techniques across software, architecture, circuits, memory, CPUs, GPUs and FPGAs. Its arithmetic evidence covers segmented inexact adders, inaccurate multiplier cells, quality-function-driven logic synthesis and neural transcendental-function accelerators. The survey emphasizes configurable quality/efficiency tradeoffs, output monitoring and worst-case error bounds.

## families
### segmented_carry_speculative  (role: analyzes)
mechanism: Kahng and Kang divide an N-bit adder into N/k - 1 sub-adders, each 2k bits wide, and avoid the full carry chain. A required carry can make every sub-adder output except the last incorrect. Changing k controls the accuracy/clock-period/dynamic-power tradeoff. Chippa et al. instead segment an adder into smaller adders and adaptively control carry propagation across segmentation points under voltage scaling, with a correction circuit to reduce ignored-carry errors. # p.17, p.18
choices:
  sub_adder_width: 2k [outside domain]   # p.17
  correction: error_reduction_stage   # p.18
new_choices:
  segmentation_control: adaptive_voltage_dependent — carry propagation across segmentation points is controlled according to voltage scaling.   # p.18
slots:
  sub_adder: UNKNOWN   # p.17
parameters: N-bit adder; N/k - 1 sub-adders; each sub-adder is 2k bits; k controls accuracy.   # p.17
results: none reported numerically for the adder alone
errors_and_checks: A propagated carry makes all sub-adder outputs except the last incorrect in the Kahng-Kang design; increasing k raises the probability of a correct result. The Chippa design uses a correction circuit for errors from ignored carries.   # p.17, p.18
conditions: Increasing k also increases dynamic power and minimum clock period. # p.17 Cross-layer approximation provides larger improvement than approximation at one level, so the survey does not attribute the reported system energy savings to the segmented adder alone. # p.18
evidence: §4.7, p.17; §4.8, p.18

### pp_perforation  (role: analyzes)
mechanism: Kulkarni et al. replace an exact 2x2 multiplier cell with an underdesigned cell that maps 11₂ × 11₂ to 111₂ rather than 1001₂. Larger multipliers are assembled by adding shifted partial products from exact and inaccurate 2x2 cells. An enhanced version detects the error magnitude and adds it to the inexact result. # p.17
choices:
  cell: kulkarni_2x2_inaccurate   # p.17
  correction: detected_error_magnitude_addition [outside domain]   # p.17
new_choices:
  block_selection: exact_or_inexact — selects accurate and inaccurate 2x2 blocks within a larger multiplier.   # p.17
slots:
  cpa: UNKNOWN   # p.17
parameters: 2x2 base multiplier; arbitrary larger widths through shifted partial products.   # p.17
results:
| metric | value | unit | technology / device | baseline | condition | page |
| correct outputs | 15 out of 16 | input combinations | UNKNOWN | exact 2x2 multiplier | underdesigned 2x2 cell | p.17 |
| area reduction | by half | area | UNKNOWN | exact 2x2 multiplier | underdesigned 2x2 cell | p.17 |
errors_and_checks: The sole inaccurate input maps 3₁₀ × 3₁₀ to 7₁₀ rather than 9₁₀. The enhanced design detects the error magnitude and adds it to recover the exact output.   # p.17
conditions: Mixing exact and inaccurate 2x2 blocks trades error rate against power saving. # p.17 Error-intolerant applications require the enhanced correction design. # p.17
evidence: §4.7, p.17

### approximate_logic_synthesis  (role: analyzes)
mechanism: SALSA begins with an RTL circuit and a quality function such as relative error. The quality function identifies input/output cases in which an inexact output does not violate the QoR requirement. Conventional don't-care synthesis simplifies the logic for each output bit, and the inexact circuit model is updated after every iteration. # p.17
choices:
  method: qf_substitution   # p.17
  error_constraint: relative_error [outside domain]   # p.17
new_choices:
  optimization_granularity: output_bit — analysis and simplification proceed iteratively for each output bit.   # p.17
slots:
  none
parameters: RTL input; user-supplied QoR metric; iterative output-bit optimization.   # p.17
results: none reported numerically
errors_and_checks: The quality function tests whether the circuit meets the QoR requirement; relative error is given as an example metric.   # p.17
conditions: The method applies to adders/multipliers and larger circuits such as DCT/butterfly/FIR designs. # p.17 Strategies that accelerate the analysis are required for large circuits. # p.17
evidence: §4.7, p.17; Venkataramani et al. reference, p.34

## new_families
### neural_network_transcendental_approximator  (domain: sfu, closest: single_poly, why_not: the function is represented by a trained multilayer perceptron rather than a polynomial/table/recurrence family)
mechanism: Eldridge et al. approximate cos, sin, exp, log and pow with MLP neural-network accelerators. A three-stage internal neuron pipeline performs weight-input multiplication and accumulation. Training covers a limited input interval, such as [0, π/4] for sin, and mathematical identities extend evaluation to other inputs. # p.20
choices: function_set: {cos, sin, exp, log, pow}; training_domain: bounded_interval; range_extension: mathematical_identities; neuron_pipeline_stages: Int[1..5:1]
results:
| metric | value | unit | technology / device | baseline | condition | page |
| energy-delay-product improvement | two orders of magnitude | improvement | UNKNOWN | conventional glibc implementation | neural-network transcendental accelerator | p.20 |
evidence: §4.10, p.20

## space_gaps
* `segmented_carry_speculative.sub_adder_width` cannot express the symbolic 2k width or its relationship to N/k - 1 sub-adders. # p.17
* `pp_perforation.correction` lacks detected-error-magnitude addition for restoring an exact result. # p.17
* `approximate_logic_synthesis.error_constraint` lacks a generic user-defined quality function/relative-error constraint. # p.17
* The SFU vocabulary lacks trained neural-network approximators for transcendental functions. # p.20

## open_questions
* The document presents provisional ACM metadata with “20xx,” 2015 and placeholder volume/article fields, while the supplied citation identifies the final 2016 publication.
* Most quantitative claims summarize cited primary studies without their technology nodes, so the missing nodes must remain `UNKNOWN`.
* The survey does not specify whether the exact/inexact 2x2-cell selection or the Kahng-Kang k parameter can change at runtime.
