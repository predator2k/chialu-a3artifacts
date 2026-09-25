---
handle: anderson1967
citation: S. F. Anderson, J. G. Earle, R. E. Goldschmidt, D. M. Powers, "The IBM System/360 Model 91: Floating-Point Execution Unit", IBM Journal of Research and Development, vol. 11, no. 1, pp. 34-53, 1967
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [system360_short_32bit, system360_long_64bit]
authority: landmark
pages_read: 34-53 / 20
---

## summary
The document describes separate pipelined floating-point add and multiply/divide units that support concurrent instruction execution. The multiplier combines radix-4 recoding, an iterative carry-save tree, and a final carry-propagate addition. The divider applies quadratically convergent multiplication factors while reusing the multiplier hardware.

## families
### single_path  (role: proposes)
mechanism: The add unit merges characteristic comparison/pre-shifting, fraction addition, and post-normalization into three hardware areas. A two-stage pipeline accepts a new add-class instruction each cycle while each instruction takes two cycles. # pp.38-41
choices:
  pipeline_depth: 2   # pp.36-37
new_choices:
  operation_merging: characteristic_compare_preshift/fraction_add/post_normalize — identifies the three merged hardware areas   # pp.38-39
slots:
  sig_adder: carry_lookahead [group_size=4, levels=3, intergroup_carry=lookahead]   # p.41
  exp: exponent_path   # pp.39,41
  align: full_align   # pp.39-40
  norm: coarse_fine   # p.41
parameters: 32-bit short and 64-bit long formats; 24-bit and 56-bit fractions; two pipeline stages; latency 2 cycles; II 1 cycle   # pp.36-38
results:
| metric | value | unit | technology / device | baseline | condition | page |
| add latency | 2 | cycles | UNKNOWN / 1967 | 3 cycles for the considered conventional unit | add-class instructions | pp.35-37 |
| add initiation interval | 1 | cycle | UNKNOWN / 1967 | UNKNOWN | pipeline operation | pp.36-37 |
errors_and_checks: No numerical rounding-error contract or concurrent fault check is reported.
conditions: Operand dependencies limit concurrency, and the floating-point instruction unit limits new add inputs to one per cycle. # pp.36-37
evidence: Fig. 3; fraction-adder discussion; Figs. 6-7; pp.38-41

### carry_lookahead  (role: instantiates)
mechanism: The 56-bit fraction adder forms bit generate/propagate functions, combines four bits into each group, combines two groups into each section, and applies lookahead at bit/group/section levels. The subtraction path also supports end-around carry and true/complement result selection. # pp.40-43
choices:
  group_size: 4   # p.41
  levels: 3   # p.41
  intergroup_carry: lookahead   # p.41
  block_sizing: uniform   # p.41
new_choices:
  groups_per_section: 2 — specifies the section hierarchy above four-bit groups   # p.41
slots: none
parameters: 56 bits; 14 groups; 7 sections; 9-bit high-order sum section   # p.41
results: none
errors_and_checks: none
conditions: Circuit fan-in/fan-out limits require cascaded lookahead levels rather than one unrestricted carry expression. # p.41
evidence: carry equations; Figs. 6-7; pp.40-43

### booth_recoded_parallel  (role: instantiates)
mechanism: Overlapping groups of two new multiplier bits and one preceding bit select signed shifted multiplicand multiples. Six groups are recoded concurrently, producing six multiples that retire 12 multiplier bits per iteration. # pp.43-44
choices:
  booth_radix: 4   # pp.43-44
  hard_multiple_gen: none   # p.44
new_choices:
  parallel_recoded_groups: 6 — specifies how many recoded groups generate multiples concurrently   # p.44
slots:
  reduction: csa_reduction_tree   # p.44
parameters: 56-bit multiplier fraction; six multiples per iteration; 12 bits retired per iteration; five iterations   # p.44
results: none
errors_and_checks: none
conditions: k=2 avoids the carry-propagate multiple-generation adder required when k is greater than two. # p.44
evidence: Table 2; Figs. 8-10; pp.43-44

### iterative_reuse  (role: proposes)
mechanism: A pipelined subset of the carry-save tree processes 12 multiplier bits per pass. The partial sum/carry feedback loop surrounds only the final two carry-save adders, so its delay determines the 20-nanosecond iteration period. # pp.46-48
choices:
  instantiated_fraction: 20% [outside domain]   # p.46
  iteration_pipeline_overlap: true   # pp.46-48
new_choices:
  retired_bits_per_iteration: 12 — specifies the multiplier progress made by each reused-tree pass   # p.46
slots:
  partial_tree: csa_reduction_tree   # pp.46-48
parameters: five accumulating iterations; 20 nanoseconds per iteration; temporary storage at the recoder/multiple gates/CSA-C/CSA-E/CSA-F   # pp.46-48
results:
| metric | value | unit | technology / device | baseline | condition | page |
| multiplier latency | 3 | cycles | UNKNOWN / 1967 | 7 cycles | complete multiply | pp.35-37 |
| iterative hardware | 20% | of full-tree hardware | UNKNOWN / 1967 | 28-CSA two-cycle tree | 20-nanosecond iteration | p.46 |
| iterative loop time | 8 | clock periods | UNKNOWN / 1967 | 20 clock periods with output-to-input feedback | five inputs | pp.47-48 |
| loop-time reduction | factor of 2.5 | ratio | UNKNOWN / 1967 | output-to-input feedback | accumulating output loop | p.48 |
| iteration repetition rate | 50 | Mc/sec | UNKNOWN / 1967 | UNKNOWN | pipelined iterative hardware | p.34 |
errors_and_checks: none
conditions: Temporary-storage placement must satisfy the stated short-path/long-path/gate-width timing relation. # p.48
evidence: Figs. 12-16; pp.46-48

### carry_save_datapath  (role: instantiates)
mechanism: Three-input carry-save adders emit separate sum/carry operands without local carry propagation. The tree reduces six generated multiples to two operands, preserves the partial product in carry-save form across iterations, and assimilates it once in the final carry-propagate adder. # pp.44-45
choices:
  compressor: 3_2   # p.44
  assimilation_point: end_of_chain   # pp.44-45
  accumulator_redundant: true   # p.44
new_choices: none
slots:
  assimilator: carry_lookahead [group_size=4, levels=3]   # p.45
parameters: six tree inputs reduced to sum/carry; 12-bit right shift per iteration; five iterations   # pp.44-45
results: none
errors_and_checks: none
conditions: Carry-save addition applies because several operands are added successively, while final carry assimilation remains necessary to form the product. # p.44
evidence: Figs. 10-11; pp.44-45

### goldschmidt  (role: proposes)
mechanism: Each factor multiplies both denominator and numerator, causing the denominator to converge quadratically to one and the numerator to converge to the quotient. The initial factor comes from a seven-bit table lookup; later factors are truncated complements of the preceding denominator. Numerator and denominator multiplies overlap in the shared divide loop. # pp.49-52
choices:
  iterations: 5 [outside domain]   # pp.51-52
  truncated_intermediate_multiplies: true   # pp.50-51
new_choices:
  numerator_denominator_overlap: true — permits two multiplies to occupy opposite halves of the divide loop   # p.52
  factor_precision_schedule: 10/7/9/9/32 bits — records the changing multiplier lengths   # pp.50-52
slots:
  seed: monolithic_rom [input_bits=7, output_bits=10, function=reciprocal]   # p.50
  iter_mult: iterative_reuse [instantiated_fraction=20% [outside domain]]   # pp.49-52
parameters: 56-bit long fraction; first table address 7 bits; five divide iterations; final factor 32 bits   # pp.49-52
results:
| metric | value | unit | technology / device | baseline | condition | page |
| divide latency | 12 | cycles | UNKNOWN / 1967 | 18 cycles | floating-point divide | pp.36-37 |
errors_and_checks: The long-precision process converges the denominator to unity within the desired accuracy, but no ulp/error bound or rounding proof is reported. # p.51
conditions: The divisor is bit-normalized, the dividend is shifted correspondingly, and truncated factors may make convergence approach unity from above or below. # pp.49-50
evidence: Table 3; Figs. 17-18; pp.49-52

## new_families
### instruction_oriented_concurrent_fpu  (domain: fp: floating-point execution units, closest: single_path, why_not: The mechanism partitions instruction classes across autonomous units and reservation stations rather than defining one arithmetic datapath.)
mechanism: Separate add and multiply/divide units execute instruction classes concurrently. Reservation stations collect operands before unit access, while pipelining provides concurrency among instructions and within multiply/divide execution. The organization sustains a burst issue rate of one instruction per cycle without duplicating complete floating-point execution units. # pp.34-37,52-53
choices:
  unit_partition: {add_and_multiply_divide}
  add_reservation_stations: Int[3..3:1]
  multiply_divide_reservation_stations: Int[2..2:1]
  issue_interval_cycles: Int[1..1:1]
results:
| metric | value | unit | technology / device | baseline | condition | page |
| instruction burst issue interval | 1 | cycle | UNKNOWN / 1967 | UNKNOWN | processor instruction issue | pp.34-35 |
| add latency | 2 | cycles | UNKNOWN / 1967 | 3 cycles | add-class instructions | pp.35-37 |
| multiply latency | 3 | cycles | UNKNOWN / 1967 | 7 cycles | multiply | pp.35-37 |
| divide latency | 12 | cycles | UNKNOWN / 1967 | 18 cycles | divide | pp.36-37 |
evidence: Figs. 1-2; general design considerations; conclusions; pp.34-37,52-53

## space_gaps
* `iterative_reuse.instantiated_fraction` needs a numeric-percentage value because the implemented subset is 20% of the full tree. # p.46
* `goldschmidt` lacks choices for numerator/denominator overlap and changing factor precision. # pp.50-52
* `end_around_carry.modulus` cannot express the document's floating-point subtraction/sign-correction use. # pp.39,41

## open_questions
* The document does not identify the exact technology/device for the reported timing and cycle results.
* The document does not state a numerical rounding contract for add/multiply/divide results.
* The relationship between the 20-nanosecond multiplier iteration period and the reported processor-cycle latencies is not stated explicitly.
