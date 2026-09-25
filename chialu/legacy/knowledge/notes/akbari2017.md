---
handle: akbari2017
citation: O. Akbari, M. Kamal, A. Afzali-Kusha, M. Pedram, "Dual-Quality 4:2 Compressors for Utilizing in Dynamic Accuracy Configurable Multipliers", IEEE Transactions on VLSI Systems, vol. 25, no. 4, pp. 1352-1361, 2017
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [8-bit integer, 16-bit integer, 32-bit integer]
authority: incremental
pages_read: 10 / 10
---

## summary
The paper proposes four dual-quality 4:2 compressors that switch dynamically between exact and approximate modes in parallel Dadda multipliers. The approximate mode reduces delay/power at the cost of accuracy, while the exact mode activates supplementary circuitry. Evaluation covers 8-, 16-, and 32-bit multipliers in 45-nm standard CMOS and three image-processing applications.

## families
### approximate_compressor_tree  (role: proposes)
mechanism: Four DQ4:2C cells combine an approximate part with supplementary exact-mode circuitry. Approximate mode activates only the approximate part and power-gates the supplementary part; exact mode reuses most approximate circuitry and activates the supplementary part. DQ4:2C1 connects carry* to x4, sum* to x1, and omits Cout. DQ4:2C2 additionally connects Cout to x3. DQ4:2C3 improves sum* accuracy, while DQ4:2C4 improves carry* accuracy. Dadda reduction trees use each cell type or a mixed arrangement with DQ4:2C1 in low-significance positions and DQ4:2C4 in high-significance positions. # pp.3-4
choices:
  compressor: akbari_dual_quality   # pp.3-4
  error_recovery: none   # pp.1-3
  dual_quality_runtime: true   # pp.1,3
new_choices:
  mode_implementation: approximate_part_plus_supplementary_part — exact mode activates supplementary circuitry while approximate mode power-gates it   # p.3
  compressor_variant: {DQ4:2C1, DQ4:2C2, DQ4:2C3, DQ4:2C4, DQ4:2Cmixed} — selects the accuracy/delay/power tradeoff and placement mixture   # pp.3-4
slots:
  cpa: UNKNOWN   # pp.4-6
parameters: 8-, 16-, and 32-bit Dadda multipliers; two runtime accuracy modes; DQ4:2Cmixed uses DQ4:2C1 in the LSB part and DQ4:2C4 in the MSB part   # pp.4-6
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay reduction | 46 | % | 45-nm standard CMOS / 2017 | recently suggested approximate compressors | average, 32-bit Dadda multiplier, approximate mode | p.9 |
| power reduction | 68 | % | 45-nm standard CMOS / 2017 | recently suggested approximate compressors | average, 32-bit Dadda multiplier, approximate mode | p.9 |
| NED reduction | about 33 | % | 45-nm standard CMOS / 2017 | state-of-the-art compressor-based approximate multipliers | average, 32-bit Dadda multiplier | p.9 |
| delay reduction | 49.3 | % | 45-nm standard CMOS / 2017 | exact Dadda multiplier | average of proposed 32-bit approximate Dadda multipliers | p.6 |
| area reduction | 68 | % | 45-nm standard CMOS / 2017 | exact Dadda multiplier | average of proposed 32-bit approximate Dadda multipliers | p.6 |
| power reduction | 83.7 | % | 45-nm standard CMOS / 2017 | exact Dadda multiplier | average of proposed 32-bit approximate Dadda multipliers | p.6 |
| energy reduction | 90 | % | 45-nm standard CMOS / 2017 | exact Dadda multiplier | average of proposed 32-bit approximate Dadda multipliers | p.6 |
| EDP reduction | 93.8 | % | 45-nm standard CMOS / 2017 | exact Dadda multiplier | average of proposed 32-bit approximate Dadda multipliers | p.6 |
| mode-transition time | 22–26 | ps | 45-nm standard CMOS / 2017 | none | HSpice simulation across the four compressor types; outputs invalid during transition | p.7 |
errors_and_checks: DQ4:2C1 and DQ4:2C2 each have a 62.5% compressor error rate; DQ4:2C2 has lower relative error than DQ4:2C1. DQ4:2C3 has a 50% error rate, and DQ4:2C4 has a 31.25% error rate. Multiplier accuracy is evaluated with MED/MRED/NED/correct-output count using exhaustive 8-bit inputs and 1 million uniform-random inputs for 16- and 32-bit cases. No error detector or recovery unit is included. # pp.3-5
conditions: Approximate operation applies to error-resilient multimedia/machine-learning/signal-processing workloads. Higher-accuracy noncompressor multipliers such as U-ROBA/SSM8/DRUM6 generally lose in delay/power/energy against the proposed designs. Exact operation has small overhead relative to a conventional exact multiplier because tristate output isolation remains present. # pp.1,5-7
evidence: §III, Figs. 3-8, Tables I-IV, §IV, §V.A-B, and §VI.

### accuracy_configurable  (role: instantiates)
mechanism: The configurable multiplier changes accuracy/power/speed at runtime by distributing mode control to dual-quality compressors. Exact mode activates supplementary compressor logic; approximate mode power-gates that logic. A demonstrated power-management policy switches DQ4:2Cmixed multiplication to approximate mode when multiplication power exceeds 400 mW. # pp.3,8-9
choices:
  mode_count: 2   # pp.1,3
  reconfig_grain: compressor_cell [outside domain]   # pp.1,3
  error_detection: false   # pp.1-3
  power_gate_unused: true   # p.3
new_choices:
  switching_policy: power_threshold — the demonstration switches modes when multiplication power exceeds 400 mW   # p.8
slots:
  none
parameters: exact/approximate modes; 400 mW demonstrated switching threshold; 25 Hall_Monitor frames multiplied by the Moon image   # p.8
results:
| metric | value | unit | technology / device | baseline | condition | page |
| power reduction | about 68 | % | 45-nm standard CMOS / 2017 | exact operating mode | average approximate-mode power for the DQ4:2Cmixed video demonstration | p.9 |
errors_and_checks: Output values are invalid during the 22–26 ps mode transition. Image quality is measured with MSSIM; the demonstrated frame differences are described as not easily distinguishable. # pp.7-9
conditions: Runtime mode switching supports changing quality-of-service or power constraints. Approximation is limited to applications that tolerate outputs near the exact result. # pp.1,8-9
evidence: Figs. 10-11 and §V.C.

## new_families
none

## space_gaps
* `accuracy_configurable.reconfig_grain` lacks a value for compressor-cell switching; this paper configures multiplier accuracy through runtime-switchable 4:2 compressors. # pp.1,3
* `approximate_compressor_tree` lacks choices for the approximate/supplementary partition and per-region mixing of compressor variants. # pp.3-4

## open_questions
* The accepted-manuscript tables do not expose legible cell-level numerical values in the supplied text, so individual Table I-IV and Table V-VII entries remain unrecorded.
* The final carry-propagate adder topology used by the evaluated Dadda multipliers is not identified.
