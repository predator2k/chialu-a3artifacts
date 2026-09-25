---
handle: bruguera_2023
citation: Bruguera, "Radix-64 Floating-Point Division and Square Root: Iterative and Pipelined Units", IEEE Transactions on Computers, 2023
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [half, single, double]
authority: incremental
pages_read: 2990-3001 / 12
---

## summary
The document proposes iterative and fully pipelined floating-point division/square-root units that produce 6 result bits per cycle through two cascaded radix-8 iterations. A common division/square-root iteration, inter-iteration speculation, on-the-fly conversion of the 3X partial root, and a compressed comparison-constant LUT reduce latency and hardware requirements.

## families
### digit_recurrence_sqrt_combined  (role: extends)
mechanism: Each radix-64 cycle cascades two radix-8 digit-recurrence iterations, each producing a signed digit from {-4, ..., +4}. The unit retains the remainder as positive-carry/negative-sum redundant words, calculates a truncated remainder estimate in parallel with the update, and converts the MSDF signed-digit result on the fly. Division and square root share the iteration hardware. Replicated speculative paths compute candidate updates before each digit is selected. The square-root path also converts 3X partial-root multiples on the fly. # p.2991-2999
choices:
  radix: 64   # p.2991
  shared_with_division: true   # p.2991, p.2998
  on_the_fly_conversion: true   # p.2992, p.2998
  speculation_between_subiterations: true   # p.2997-2998
new_choices:
  microarchitecture_organization: {iterative, fully_pipelined} — selects shared iteration logic or one hardware stage per digit iteration   # p.2993-2995
  radix_decomposition: two_cascaded_radix8 — constructs one radix-64 cycle from two radix-8 iterations   # p.2991, p.2997
  comparison_lut_organization: division_base_plus_square_root_offset — derives square-root constants from division constants and a 4-bit offset table   # p.2996-2997
  partial_root_3x_generation: on_the_fly_conversion — generates S3/S3M without a timing-consuming 3 × S adder   # p.2998-2999
slots:
  digit_select: qds_table   # p.2992, p.2995-2997
parameters: Radix-8 digit set {-4, -3, -2, -1, 0, +1, +2, +3, +4}; 6 divisor/partial-root MSBs address 8 comparison constants; remainder estimates are 9 bits for division and 10 bits for square root; digit-iteration counts are {2, 4, 9} for half/single/double division and {1, 4, 8} for half/single/double square root. # p.2992-2994
results:
| metric | value | unit | technology / device | baseline | condition | page |
| LUT storage | 1,938 | bits | UNKNOWN; year 2023 | 4,944 bits | Combined division-base/square-root-offset organization | p.2996 |
| LUT storage reduction | 60% | percent | UNKNOWN; year 2023 | Original 4,944-bit LUTs | Includes additional square-root constant logic | p.2996 |
| critical-path estimate | 46.33 | tFO4 | UNKNOWN; year 2023 | none | Two cascaded radix-8 iterations; Logical Effort model | p.2999 |
| result production | 6 | bits per cycle | UNKNOWN; year 2023 | none | One radix-64 iteration per cycle | p.2991 |
| area ratio | 2.5X | iterative-unit area | UNKNOWN; year 2023 | Proposed iterative unit | Proposed fully pipelined unit | p.2995, p.2999 |
| target frequency | 3.4 | GHz | UNKNOWN; year 2023 | none | Design target rather than reported silicon measurement | p.2999 |
errors_and_checks: Post-processing rounds the quotient/root and shifts a denormal division result to produce an IEEE-compliant quotient; the document reports no numerical-error bound, fault model, or detection coverage. # p.2992
conditions: The iterative organization reuses digit-iteration logic, so throughput depends on precision and denormal handling. # p.2994-2995 The pipelined organization accepts one same-precision operation every cycle, but mixed-precision operations have forbidden start cycles caused by stage collisions. # p.2995 The pipelined organization pays an area penalty because digit-iteration logic is replicated nine times. # p.2999 Static and dynamic power are not evaluated because the compared processor descriptions omit power data. # p.3000
evidence: §II equations (1)-(7), Figs. 1-7, Tables I-III, and §§III-IV, p.2991-2999.

### sig_div_then_round  (role: instantiates)
mechanism: Pre-processing unpacks operands, detects special conditions, normalizes denormals, initializes the remainder/result, and addresses the digit-selection LUT. The shared radix-64 unit then computes division or square root. Post-processing rounds the result and handles a denormal division quotient. The iterative implementation shares registers across phases, while the pipelined implementation uses V1/V2, D1-D9, and W0 stages. # p.2992-2994
choices:
new_choices:
  none
slots:
  sig_div: digit_recurrence_sqrt_combined [radix=64, shared_with_division=true]   # p.2991-2994
  subnormal: full_hardware   # p.2992-2994
parameters: Iterative division latency is mdiv + 2 through mdiv + 5 cycles, where mdiv={2, 4, 9}; iterative square-root latency is msqrt + 3 or msqrt + 4 cycles, where msqrt={1, 4, 8}; pipelined latency is m + 3 cycles, where m={2, 4, 9}. # p.2994
results:
| metric | value | unit | technology / device | baseline | condition | page |
| pipelined throughput | 1 | operation per cycle | UNKNOWN; year 2023 | Proposed iterative unit | Same precision; every operation/precision | p.2995, p.3001 |
| system area | 16% less | area | UNKNOWN; year 2023 | Two 64-bit plus two 32-bit iterative units from [2] | One proposed pipelined unit | p.3001 |
| SpecFP2017 speedup | 2.51% | percent | UNKNOWN; year 2023 | radix-8 division/square-root unit | Radix-64 unit | p.2991 |
| SpecFP2017 speedup | 1.34% | percent | UNKNOWN; year 2023 | radix-16 division/square-root unit | Radix-64 unit | p.2991 |
errors_and_checks: The unit supports normalization of denormal operands and an IEEE-compliant denormal division result; no quantitative rounding-error result is reported. # p.2992-2994
conditions: The iterative unit favors low area but has low throughput because its iteration logic is reused. # p.2990, p.3001 The pipelined unit favors cascaded division/square-root workloads and provides higher throughput at greater per-unit area. # p.2991, p.2995 The document identifies HPC/scientific workloads as latency-sensitive and machine-learning workloads as candidates for pipelined throughput. # p.2991
evidence: Figs. 1-4, Tables I-II and IV-V, and §§III, V-VII, p.2992-3001.

## new_families
none

## space_gaps
* `digit_recurrence_sqrt_combined` lacks a choice for iterative versus fully pipelined organization. # p.2993-2995
* `digit_recurrence_sqrt_combined` lacks a choice for constructing radix 64 from two cascaded radix-8 iterations. # p.2991, p.2997
* `digit_recurrence_sqrt_combined` cannot record the shared division-base/square-root-offset QDS LUT organization. # p.2996-2997
* `digit_recurrence_sqrt_combined` cannot record on-the-fly generation of the 3X partial-root multiple. # p.2998-2999

## open_questions
* The supplied text does not expose the numeric cells of Tables I-V, so only figures stated in the surrounding prose are recorded.
* The implementation technology/device is not stated.
* The circuit family used for final rounding is not identified.
