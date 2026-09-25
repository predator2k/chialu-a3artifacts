---
handle: narayanamoorthy2015
citation: S. Narayanamoorthy, H. A. Moghaddam, Z. Liu, T. Park, N. S. Kim, "Energy-Efficient Approximate Multiplication for Digital Signal Processing and Classification Applications", IEEE Transactions on VLSI Systems, vol. 23, no. 6, pp. 1180-1184, 2015
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int16, fixed_point]
authority: incremental
pages_read: 1-5 / 5
---

## summary
The document proposes the static segment method (SSM), which multiplies selected m-bit segments of two n-bit fixed-point operands using an m × m multiplier. SSM limits segment starts to two or three fixed positions, replacing the leading-one detectors/shifters of the dynamic segment method (DSM) with OR gates/multiplexers. A 16×16 ESSM8×8 achieves 99% average computational accuracy and consumes 42% of the precise multiplier's energy/op. # p.1-p.4

## families
### dynamic_segment  (role: extends)
mechanism: SSM selects an m-bit segment containing the leading one from each n-bit operand. Each segment starts at one of two fixed positions, or three positions when m = n/2 in enhanced SSM (ESSM). Two-position SSM uses (n–m)-input OR gates and m-bit 2-to-1 multiplexers for selection, followed by a 2n-bit 3-to-1 multiplexer that places the 2m-bit product using shifts of 0, n–m, or 2(n–m). A repeatedly used coefficient can be preprocessed and stored with its selection information, removing one input OR gate and multiplexer. # p.2-p.3
choices:
  segment_width: 8, 10, or 12   # p.2-p.4
  segment_select: static_msb_or_lsb   # p.2
  runtime_width_scaling: false   # p.1-p.2
new_choices:
  possible_start_positions: {2, 3} — Number of fixed positions from which an m-bit segment can start.   # p.2-p.3
  fixed_coefficient_preprocessing: Bool — Preselects and stores the segment of a repeatedly used coefficient.   # p.2-p.3
slots:
  none
parameters: n = 16; m = 8, 10, or 12 for SSM/ESSM and m = 6 or 8 for DSM; two 16-b inputs; 32-b output; m ≥ n/2 for the proposed method; 2 GHz synthesis frequency; II UNKNOWN   # p.1-p.3
results:
| metric | value | unit | technology / device | baseline | condition | page |
| average computational accuracy | 99.4 | % | UNKNOWN / 2015 | precise 16×16 multiplication | 16×16 example using 8-b segments and an 8×8 multiplier | p.2 |
| average computational accuracy | 96.7 | % | TSMC 45-nm standard cell / 2015 | precise multiplier | AM, random operands | p.3 |
| average computational accuracy | 99.7 | % | TSMC 45-nm standard cell / 2015 | precise multiplier | DSM8×8, random operands | p.3 |
| average computational accuracy | 97.8 | % | TSMC 45-nm standard cell / 2015 | precise multiplier | DSM6×6, random operands | p.3 |
| average computational accuracy | 98.0 | % | TSMC 45-nm standard cell / 2015 | precise multiplier | SSM8×8, random operands | p.3 |
| average computational accuracy | 99.6 | % | TSMC 45-nm standard cell / 2015 | precise multiplier | SSM10×10, random operands | p.3 |
| average computational accuracy | 99.0 | % | TSMC 45-nm standard cell / 2015 | precise multiplier | ESSM8×8, random operands | p.3 |
| average computational accuracy | 97.1 | % | TSMC 45-nm standard cell / 2015 | precise multiplier | TRUN8×8, random operands | p.3 |
| operand pairs above 95% computational accuracy | 45 | % | TSMC 45-nm standard cell / 2015 | precise multiplier | AM, image operands | p.3 |
| operand pairs above 95% computational accuracy | 64 | % | TSMC 45-nm standard cell / 2015 | precise multiplier | SSM8×8, image operands | p.3 |
| operand pairs above 95% computational accuracy | 61 | % | TSMC 45-nm standard cell / 2015 | precise multiplier | TRUN8×8, image operands | p.3 |
| operand pairs above 95% computational accuracy | 100 | % | TSMC 45-nm standard cell / 2015 | precise multiplier | DSM8×8, image operands | p.3 |
| operand pairs above 95% computational accuracy | 98 | % | TSMC 45-nm standard cell / 2015 | precise multiplier | SSM10×10, image operands | p.3 |
| operand pairs above 95% computational accuracy | 98 | % | TSMC 45-nm standard cell / 2015 | precise multiplier | ESSM8×8, image operands | p.3 |
| average energy/op reduction | 13 | % | TSMC 45-nm standard cell / 2015 | PM | AM across four operand sets | p.3 |
| average energy/op reduction | 3 | % | TSMC 45-nm standard cell / 2015 | PM | DSM8×8 across four operand sets | p.3 |
| average energy/op reduction | 28 | % | TSMC 45-nm standard cell / 2015 | PM | DSM6×6 across four operand sets | p.3 |
| average energy/op reduction | 35 | % | TSMC 45-nm standard cell / 2015 | PM | SSM10×10 across four operand sets | p.3 |
| average energy/op reduction | 58 | % | TSMC 45-nm standard cell / 2015 | PM | ESSM8×8 across four operand sets | p.3 |
| energy/op reduction | 6 | % | TSMC 45-nm standard cell / 2015 | original ESSM8×8 | ESSM8×8 accepting a preprocessed fixed coefficient | p.3 |
| area | 62 | % of PM | TSMC 45-nm standard cell / 2015 | PM | SSM10×10, random operands | p.4 |
| energy/op | 58 | % of PM | TSMC 45-nm standard cell / 2015 | PM | SSM10×10, random operands | p.4 |
| base-multiplier share of total area | 67 | % | TSMC 45-nm standard cell / 2015 | total SSM10×10 area | 10×10 base multiplier | p.4 |
| base-multiplier share of total energy/op | 71 | % | TSMC 45-nm standard cell / 2015 | total SSM10×10 energy/op | 10×10 base multiplier | p.4 |
errors_and_checks: Computational accuracy is evaluated over random/audio/image/recognition operand sets containing billions of pairs. SSM10×10 and ESSM8×8 provide PESQ/SSIM above the stated 99% threshold for no notable perceptual difference, while TRUN8×8 degrades all three applications. No fault-detection mechanism is provided. # p.3
conditions: SSM applies to error-tolerant fixed-point DSP/classification workloads. # p.1 SSM requires m ≥ n/2 and loses some accuracy relative to PM/DSM. # p.1-p.2 ESSM adds a third segment position when m = n/2. # p.2-p.3 Fixed-coefficient preprocessing applies when one operand is stored and repeatedly reused. # p.1-p.3 DSM overhead from LODs/shifters can dominate its reduced multiplier, while SSM auxiliary logic scales linearly with m. # p.2-p.4
evidence: §II, Fig. 1-Fig. 5, §III-A-§III-D, Table I, Fig. 6-Fig. 8, and §IV, p.1-p.4

## new_families
none

## space_gaps
* The dynamic_segment family needs a slot for the base m × m multiplier; the current core_multiplier slot admits adder families rather than multiplier implementations. # p.1-p.4
* The dynamic_segment family lacks the number of permitted segment-start positions, which distinguishes two-position SSM from three-position ESSM. # p.2-p.3
* The dynamic_segment family lacks fixed-coefficient preprocessing, which removes one OR gate and one input multiplexer. # p.2-p.3

## open_questions
* Table I's numeric PESQ/SSIM entries are not legible in the supplied document text, so only the authors' stated QoC threshold and conclusions are recorded.
* Fig. 7 labels the enhanced design ESSM10×10, while the surrounding text identifies the evaluated design as ESSM8×8. # p.3
