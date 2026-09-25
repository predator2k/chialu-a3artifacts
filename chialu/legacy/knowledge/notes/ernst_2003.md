---
handle: ernst_2003
citation: D. Ernst, N. S. Kim, S. Das, et al., "Razor: A Low-Power Pipeline Based on Circuit-Level Timing Speculation", Proc. MICRO-36, pp. 7-18, 2003
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, other]
formats: [int18, int64]
authority: landmark
pages_read: 12 / 12
---

## summary
Razor detects pipeline timing errors by comparing a main flip-flop sample with a delayed shadow-latch sample, then restores the correct value and recovers the pipeline. The mechanism permits dynamic voltage scaling below the conventional critical voltage while maintaining a small nonzero timing-error rate. A 0.18 µm Alpha prototype, an FPGA multiplier, and a modeled 64-bit Kogge-Stone adder establish the energy/recovery tradeoffs. # pp.7-18

## families
### time_redundancy  (role: proposes)
mechanism: Each delay-critical flip-flop is paired with a shadow latch clocked by a delayed clock. A comparator detects disagreement between the aggressive main sample and the shadow sample, whose timing is guaranteed under worst-case subcritical conditions. The shadow value replaces a failed main value. Global clock gating or a counterflow flush/bubble mechanism prevents incorrect state from committing. Metastability detection treats an indeterminate main sample as an error; an ambiguous error signal raises panic and restarts the pipeline at a safe voltage. # pp.8-11
choices:
  transform: time_shifted_sample   # pp.7-8
  iterations: 2   # pp.7-8
  correction: true   # pp.8-11
new_choices:
  sample_structure: main_flip_flop_plus_shadow_latch — selects the aggressive and guaranteed-correct samples   # pp.8-9
  recovery_mechanism: global_clock_gating_or_counterflow_pipeline — selects the pipeline repair method   # pp.10-11
  metastability_response: detect_restore_or_panic_restart — defines recovery from metastable data/error signals   # pp.9-10
  voltage_control: proportional_error_rate_feedback — adjusts Vdd from Eref minus Esample   # pp.11-12
slots:
  none
parameters: 64-bit Alpha; 200 MHz; 1.8 V to 1.2 V; 2.5 nS delayed clock; 192 Razor flip-flops of 2408; 2498 delay buffers; one-cycle local restoration penalty; target error rate 1.5% in DVS simulation   # pp.8,12,16
results:
| metric | value | unit | technology / device | baseline | condition | page |
| error-free pipeline power | 425 | mW | 0.18 µm; 2003 | non-Razor architecture | 1.8 V, 200 MHz | p.12 |
| total Razor power overhead | 3.1 | % | 0.18 µm; 2003 | non-Razor architecture | error-free operation | p.12 |
| delay-buffer power overhead | 12.2 | mW | 0.18 µm; 2003 | without short-path buffers | error-free operation | p.12 |
| standard flip-flop energy | 49 / 95 | fJ | 0.18 µm; 2003 | none | switching / static | p.12 |
| Razor flip-flop energy | 60 / 160 | fJ | 0.18 µm; 2003 | standard flip-flop | switching / static | p.12 |
| Razor flip-flop recovery energy | 210 | fJ per error event | 0.18 µm; 2003 | none | per affected flip-flop | p.12 |
| pipeline recovery energy | 189 | pJ per error event | 0.18 µm; 2003 | none | Alpha prototype | p.12 |
| recovery power overhead | 1 | % | 0.18 µm; 2003 | error-free operation | 10% error rate; excludes flushed-instruction re-execution | p.13 |
| multiplier energy reduction | 22 | % | Xilinx XC2V250-F456-5; 2003 | zero-margin point | 1.36 V, 90 MHz, 27 C, 1.3% error | p.14 |
| multiplier energy reduction | 30 | % | Xilinx XC2V250-F456-5; 2003 | safety-margin point | 1.36 V, 90 MHz, 27 C, 1.3% error | p.14 |
| multiplier energy reduction | 35 | % | Xilinx XC2V250-F456-5; 2003 | environmental-margin point | 1.36 V, 90 MHz, 27 C, 1.3% error | p.14 |
| fixed-voltage adder energy reduction | 42.4 | % average | TSMC 0.18 µm model; 2003 | non-Razor adder at 1.8 V | 11 SPEC2000 benchmarks, energy-optimal Vdd | p.15 |
| fixed-voltage pipeline throughput reduction | 2.49 | % maximum | TSMC 0.18 µm model; 2003 | non-speculative pipeline | energy-optimal Vdd | p.16 |
| dynamic-voltage adder energy reduction | 41.0 | % average | TSMC 0.18 µm model; 2003 | non-Razor adder at 1.8 V | 1.5% target error rate | p.17 |
| dynamic-voltage IPC reduction | 5.88 | % maximum | TSMC 0.18 µm model; 2003 | non-speculative pipeline | gcc benchmark | p.17 |
errors_and_checks: The shadow-latch setup time is guaranteed at the minimum allowed voltage. Detected delay/metastability errors restore the shadow value. A metastable error signal can cause a panic flush/restart; its probability is described as negligible but is not quantified. No detection-coverage or false-alarm rate is reported. # pp.8-10
conditions: Razor applies only to monitored combinational datapaths in this work; SRAM/control recovery remains future work. Short paths must exceed tdelay + thold, so added buffers trade power against voltage-scaling range. The prototype validates timing only down to 1.2 V. Recovery control must meet timing at the worst-case subcritical voltage. # pp.9-11,16
evidence: Abstract; §§2-3.5; Figures 1-9 and 11-13; Tables 1-2; pp.7-17

### parallel_prefix  (role: analyzes)
mechanism: A 64-bit Kogge-Stone carry-prefix adder is implemented with a TSMC 0.18 µm standard-cell library. Voltage/temperature/fanout characterizations feed a C-level timing model validated against HSPICE. Random and SPEC2000 operand sequences determine the fraction of additions that miss an 870 MHz clock period as voltage falls. # p.14
choices:
  topology: kogge_stone   # p.14
new_choices:
  none
slots:
  none
parameters: 64-bit; 870 MHz; 27 C; 32,000-vector sequences; HSPICE 2001.2 validation; voltage sweep from 1.8 V to 0.6 V in 25 mV steps   # pp.14-15
results:
| metric | value | unit | technology / device | baseline | condition | page |
| timing-model error | less than 10 | % | TSMC 0.18 µm; 2003 | HSPICE 2001.2 | 50 random vectors | p.14 |
| Razor checking energy overhead | about 4.3 | % | TSMC 0.18 µm model; 2003 | adder without Razor support | latch/check circuitry | p.15 |
| recovery energy | 18 | times one addition | TSMC 0.18 µm model; 2003 | one add at 1.8 V | conservative six-cycle recovery | p.15 |
| energy reduction range | 23.7 to 64.2 | % | TSMC 0.18 µm model; 2003 | non-Razor adder at 1.8 V | energy-optimal fixed voltage across benchmarks | p.16 |
| real-input voltage advantage | nearly 400 | mV lower | TSMC 0.18 µm model; 2003 | random inputs at similar error rates | SPEC2000 program inputs | p.18 |
errors_and_checks: A timing error is a modeled addition whose delay exceeds the clock period. The model reports error rate as the fraction of failing samples; it does not report arithmetic-value corruption coverage or false alarms. # p.14
conditions: Error rate depends strongly on operand/workload data. The energy figures cover the independently voltage-scaled adder plus pipeline recovery, rather than whole-pipeline voltage scaling. # pp.14-16
evidence: §3.2, §3.4, Figures 10-12, Table 1, pp.14-16; conclusions, p.18

## new_families
none

## space_gaps
* `time_redundancy` lacks choices for main/shadow sampling structure, delayed-clock spacing, pipeline recovery, metastability handling, and error-rate voltage control. # pp.8-12
* The `comparator` slot permits only `two_rail_tree`, while Razor uses XOR comparison plus skewed-inverter metastability detection. # pp.8-10

## open_questions
* The document does not identify the internal microarchitecture of the Xilinx 18x18 multiplier block. # p.13
* The document does not quantify the residual probability of system failure from a metastable error signal. # p.10
