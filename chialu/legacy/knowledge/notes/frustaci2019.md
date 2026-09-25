---
handle: frustaci2019
citation: F. Frustaci, S. Perri, P. Corsonello, M. Alioto, "Energy-Quality Scalable Adders Based on Nonzeroing Bit Truncation", IEEE Transactions on VLSI Systems, vol. 27, no. 4, pp. 964-968, 2019
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [uint16, int16]
authority: incremental
pages_read: 5 / 5
---

## summary
The paper proposes dynamically configurable nonzeroing bit truncation for ripple-carry adders. Complementary constants replace the truncated LSBs of the two addends, which minimizes squared error under uniformly distributed LSB subwords while suppressing switching activity in the truncated full adders.

## families
### approximate_truncated  (role: extends)
mechanism: An n-bit addition is divided into an h-bit accurate part and a k-bit truncated part. The k LSBs of the two operands are forced to complementary constant values, Ai = B̄i, which makes the summed truncation error zero-mean and maximizes PSNR. AND/OR input buffers controlled by Ctr signals force each truncated ripple stage to inputs 0 and 1, so its carry is 0 and its switching activity is suppressed. Conventional full adders remain at every bit position.
choices:
  lower_part_width: 8   # p.3
  lower_scheme: truncate_constant   # pp.1-2
  correction: none   # pp.1-2
new_choices:
  truncation_constant_relation: complementary_per_bit — relation between constants forced onto corresponding truncated operand bits   # p.2
slots:
  upper_adder: ripple_carry   # pp.1-3
parameters: n = 16; h = n-k; k = 0 to 8; k < kmax; unsigned and signed addition; 2 GHz; 1 V nominal supply   # pp.1-3
results:
| metric | value | unit | technology / device | baseline | condition | page |
| PSNR improvement | 6.7 to 8.5 | dB | 28-nm FDSOI / 2019 | zeroing bit truncation [15] | same k | p.2 |
| MED reduction | 60%–67% | % | 28-nm FDSOI / 2019 | zeroing bit truncation [15] | same k | p.2 |
| PSNR improvement | more than 20 | dB | 28-nm FDSOI / 2019 | [7] and [8] Approximation 3 | iso-energy, k = 4 to 8 | p.3 |
| MED reduction | up to 86% | % | 28-nm FDSOI / 2019 | [7] and [8] Approximation 3 | iso-energy, k = 4 to 8 | p.3 |
| energy reduction | 2X less | energy | 28-nm FDSOI / 2019 | exact 16-bit adder | k = 8 | p.3 |
| delay overhead | about 1% | delay | 28-nm FDSOI / 2019 | standard exact adder | AND/OR input buffers included | p.3 |
| area overhead | 4.5% | area | 28-nm FDSOI / 2019 | standard exact adder | AND/OR input buffers included | p.3 |
| energy reduction | up to 64% | % | 28-nm FDSOI / 2019 | reconfigurable approximate RCA [18] | voltage scaling, PSNR = 30 dB, k = 8 | p.4 |
| DCT PSNR improvement | up to 5.6 | dB | 28-nm FDSOI / 2019 | zeroing bit truncation [15] | same k and energy | p.4 |
| DCT energy reduction | 2.2X | energy | 28-nm FDSOI / 2019 | DCT with exact 16-bit adders | four 64×64 image benchmarks | p.4 |
| video DCT energy reduction | 20% | % | 28-nm FDSOI / 2019 | [9] and [16] | 2000-frame backdoor sequence; k = 2 with motion and k = 5 otherwise | p.4 |
| DCT MSSIM improvement | 12% | % | 28-nm FDSOI / 2019 | zeroing bit truncation [15] | iso-energy | p.4 |
errors_and_checks: Under uniformly distributed k-bit LSB subwords, complementary truncation constants satisfy x+y=−(2^k−1), which minimizes SSE and maximizes PSNR. The paper evaluates PSNR/MED and reports no fault-detection mechanism or formal worst-case accuracy contract.   # pp.1-2
conditions: The method targets error-tolerant multimedia/machine-learning/DSP/wireless applications. Addition requires complementary truncated bits, whereas subtraction is best with equal truncated bits and therefore favors traditional zeroing. Multiplication is excluded because its energy depends strongly on the selected constants and is deferred to future work. Signed addition produces essentially the same reported results.   # pp.1-3
evidence: §II, (1)–(3), Table I, Figs. 1–4, Table II, §IV, Figs. 5–6

### accuracy_configurable  (role: extends)
mechanism: Ctrkmax−1...Ctr0 dynamically select how many LSB stages are truncated. Setting Ctri = 1 for each i < k forces the corresponding full-adder inputs to 0 and 1, suppressing dynamic energy while retaining the same RCA and input-buffer hardware. Runtime changes in k select different energy-quality operating points.
choices:
  mode_count: 9 [outside domain]   # p.3
  reconfig_grain: truncation_width   # pp.2-3
  error_detection: false   # pp.2-3
  power_gate_unused: false   # p.2
new_choices:
  none
slots:
  none
parameters: k = 0 to 8 in the evaluated 16-bit adder; one Ctri control per truncatable bit; run-time adaptation; II not reported   # pp.2-3
results:
| metric | value | unit | technology / device | baseline | condition | page |
| energy reduction | up to 20% | % | 28-nm FDSOI / 2019 | static approximate adder [9] | same k | p.3 |
| energy reduction | up to 10% | % | 28-nm FDSOI / 2019 | static approximate adder [16] | same k | p.3 |
errors_and_checks: Configuration changes approximation quality but provides no error detection, recovery, or false-alarm mechanism.   # pp.2-3
conditions: Static approximate adders [9] and [16] provide comparable quality in some configurations but cannot adapt to changing quality targets. Voltage overscaling below the minimum 2-GHz supply introduces occasional timing violations and additional quality degradation.   # pp.3-4
evidence: Fig. 2, §III, Figs. 3–4, Table II, §IV

### ripple_carry  (role: instantiates)
mechanism: The implementation uses an n-bit ripple-carry adder because of its low energy consumption. Conventional full adders occupy all bit positions, including the dynamically truncated portion; AND/OR input buffers suppress activity in selected LSB stages without specialized cells.
choices:
  carry_polarity_alternation: UNKNOWN   # pp.1-2
new_choices:
  none
slots:
  full_adder_cell: UNKNOWN   # p.2
parameters: 16 bits; kmax = 8 in the evaluated implementation; 2 GHz; outputs loaded by minimum-drive positive-edge-triggered D flip-flops   # p.3
results: none
errors_and_checks: none
conditions: The paper selects RCA for low energy and does not compare alternative exact upper-adder microarchitectures.   # pp.1-3
evidence: §II, Fig. 2, §III

## new_families
none

## space_gaps
* `approximate_truncated` lacks a choice for complementary versus equal/zero operand constants, although this relation determines the addition/subtraction error behavior.   # pp.2-3
* `accuracy_configurable.mode_count` cannot represent the nine evaluated k settings from 0 to 8.   # p.3
* `accuracy_configurable` lacks an input-activity-suppression mechanism distinct from clock gating/power gating.   # p.2

## open_questions
* Table II values are not fully legible in the supplied text, so absolute delay/area/energy numbers are not extracted.
* The paper does not specify the transistor-level full-adder cell or carry polarity.
* The multiplication behavior of nonzeroing truncation remains future work.
