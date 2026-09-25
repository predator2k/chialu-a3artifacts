---
handle: moons2017
citation: B. Moons, R. Uytterhoeven, W. Dehaene, M. Verhelst, "DVAFS: Trading Computational Accuracy for Energy Through Dynamic-Voltage-Accuracy-Frequency-Scaling", Design, Automation and Test in Europe (DATE), pp. 488-493, 2017
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_DOT_ACC]
formats: [fixed_point_1b_to_16b]
authority: landmark
pages_read: 7 / 7
---

## summary
The paper proposes Dynamic-Voltage-Accuracy-Frequency-Scaling (DVAFS), which combines input-precision scaling, subword parallelism, voltage scaling, and frequency scaling to trade computational accuracy for energy at constant throughput. A Booth-encoded Wallace-tree multiplier and a SIMD processor are evaluated in 40nm LP LVT, and the DVAFS principle is demonstrated in the measured 28nm FDSOI Envision CNN processor.

## families
### twin_precision_subword  (role: extends)
mechanism: A 16b Booth-encoded Wallace-tree multiplier gates unused input LSBs at reduced precision and reuses inactive arithmetic cells as independent subword multipliers. The modes execute one 16b operation, two 8b operations, or four 4b operations per cycle. Increased subword parallelism permits proportional frequency reduction while maintaining word throughput. # §II.C, §III.A
choices:
  partition: quarters   # §II.C
new_choices:
  precision_mode_set: 1x16b_2x8b_4x4b — the supported full-width and subword-parallel modes   # §III.A
slots:
  none
parameters: 16b full width; 1 × 16b, 2 × 8b, and 4 × 4b modes; 500MOPS constant throughput at 500MHz, 250MHz, and 125MHz respectively   # §III.A
results:
| metric | value | unit | technology / device | baseline | condition | page |
| energy per word | 2.63 | pJ/word | 40nm LP LVT, 2017 | 2.16pJ/word non-reconfigurable 16b multiplier | 16b full-precision DVAFS multiplier | §III.A |
| full-precision energy overhead | 21 | % | 40nm LP LVT, 2017 | non-reconfigurable 16b multiplier | reconfigurability enabled | §III.A |
| supply voltage | 0.75 | V | 40nm LP LVT, 2017 | 1.1V nominal supply | 4 × 4b DVAFS at constant throughput | §III.A |
| operating frequency | 125 | MHz | 40nm LP LVT, 2017 | 500MHz at 16b | 4 × 4b DVAFS at 500MOPS | §III.A |
| energy saving | more than 95 | % | 40nm LP LVT, 2017 | non-reconfigurable 16b multiplier | 4 × 4b DVAFS processing | §III.A |
errors_and_checks: Accuracy is reduced by truncating or rounding a variable number of input bits; Figure 3b reports accuracy as RMSE but provides no tabulated RMSE values. # §II.A, §III.A
conditions: The design requires multi-mode optimization so the critical path decreases at lower precision. Constant throughput permits frequency reduction only when subword parallelism increases. # §III.A
evidence: Figure 1, Figure 2, Table I, Figure 3, §II.C, §III.A

### lane_width_gating  (role: extends)
mechanism: Precision is configured by gating unused LSBs, which reduces switching activity and shortens the active critical path. DVAS converts the resulting timing slack into lower voltage at fixed frequency. DVAFS also packs reduced-precision operations into inactive arithmetic cells, which permits frequency and system-voltage reduction at constant throughput. # §II.A–§II.C
choices:
  detection: static_mode   # §II.B
  gating: operand_isolation   # §II.B
  operation_packing: true   # §II.C
new_choices:
  voltage_scaling: precision_dependent — supply voltage follows the active precision and critical path   # §II.B
  frequency_scaling: subword_parallel_constant_throughput — frequency falls as operations per cycle increase   # §II.C
slots:
  none
parameters: multiplier precision points 16b, 12b, 8b, and 4b; processor modes 1 × 1–16b, 2 × 1–8b, and 4 × 1–4b   # Table I, §III.B
results:
| metric | value | unit | technology / device | baseline | condition | page |
| switching-activity reduction | 12.5× | relative | 40nm LP LVT, 2017 | 16b DVAS multiplier | 4b DVAS | §III.A |
| switching-activity reduction | 3.2× | relative | 40nm LP LVT, 2017 | 16b DVAFS multiplier | 4b DVAFS | §III.A |
| energy reduction | 36 | % | 40nm LP LVT, 2017 | 1.1V multiplier operation | DVAS voltage reduced to 0.9V | §III.A |
| additional energy decrease | 55 | % | 40nm LP LVT, 2017 | DVAS | DVAFS voltage reduced to 0.75V | §III.A |
errors_and_checks: none
conditions: Critical-path scaling occurs in arithmetic blocks rather than decoders/memory, so DVAS requires separate accuracy-scalable and non-accuracy-scalable power domains. DVAFS reduces frequency and voltage in the wider system, although memories may remain at fixed voltage for reliability. # §II.B–§II.C, §III.B
evidence: Equations 1–3, Figure 1, Figure 2, Table I

### approximate_mac_nn  (role: instantiates)
mechanism: CNN layers use separately selected fixed-point precisions for weights and input feature maps. The DVAFS processor maps these layer modes to subword parallelism, frequency, and voltage while also exploiting weight/input sparsity. # §IV.B, §V
choices:
  multiplier_source: exact   # §II.A, §III.A
  precision_scaling: dvafs   # §IV.B, §V
  retraining: false   # §IV.B
new_choices:
  layerwise_weight_input_precision: independently_profiled — weight and input widths vary by network layer   # Figure 6, Table III
slots:
  none
parameters: LeNet-5 1–6b; AlexNet 5–9b; VGG16 2–8b or 4–7b in cited configurations; Envision modes up to 4 × 4b with 256 processing units   # §IV.B, §V
results:
| metric | value | unit | technology / device | baseline | condition | page |
| relative benchmark accuracy | 99 | % | UNKNOWN, 2017 | full-precision 32b floating point | layerwise LeNet-5/AlexNet quantization | Figure 6 |
| AlexNet energy efficiency | 1.8 | TOPS/W | Envision 28nm FDSOI, 2017 | 0.16TOPS/W non-scalable and 0.94TOPS/W DVAS-only implementations | complete AlexNet | §V |
| benchmark power range | 5.6-62 | mW | Envision 28nm FDSOI, 2017 | UNKNOWN | VGG16/AlexNet/LeNet-5 convolutional layers | Table III |
| LeNet-5 total efficiency | 3 | TOPS/W | Envision 28nm FDSOI, 2017 | UNKNOWN | complete reported convolution workload | Table III |
errors_and_checks: The selected quantization settings retain 99% relative accuracy for Figure 6 benchmarks; the paper does not report arithmetic error bounds or per-operation error distributions. # Figure 6
conditions: Required precision varies across applications, networks, and layers. Low-precision operation is applicable to fault-tolerant CNN inference, and reported 1–9b operation can incur less than 1% accuracy loss without network retraining. # §IV.B
evidence: Figure 6, Table III, §IV.B, §V

## new_families
### dynamic_voltage_accuracy_frequency_scaling  (domain: approx: approximation methods, closest: lane_width_gating, why_not: lane_width_gating lacks coordinated voltage/frequency scaling and separate power-domain behavior at constant throughput)
mechanism: DVAFS jointly changes switching activity, critical-path length, supply voltage, frequency, and subword parallelism as computational precision changes. Reduced precision gates input LSBs and shortens arithmetic paths. Subword operation reuses inactive cells to increase operations per cycle, so frequency can fall without reducing word throughput. Lower frequency and shorter paths permit lower voltage in accuracy-scalable and non-accuracy-scalable processor domains, while reliability-sensitive memories may retain a fixed supply. # §II.A–§II.C, §III.B
choices: precision_control: {input_truncation, input_rounding}; throughput_policy: {constant_frequency, constant_word_throughput}; power_domain_partition: {accuracy_nonaccuracy, accuracy_nonaccuracy_memory}; subword_modes: {1x16b_2x8b_4x4b}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| SIMD-processor energy reduction | 85 | % | 40nm LP LVT, 2017 | SW processor at 1 × 16b and 500MHz | 4 × 4b DVAFS mode | §III.B |
| peak throughput | 408 | GOPS | Envision 28nm FDSOI, 2017 | 102GOPS at 1 × 1–16b | 4 × 1–4b at 200MHz | §V |
| efficiency | 4.2 | TOPS/W | Envision 28nm FDSOI, 2017 | 0.3TOPS/W at 1 × 16b | 4 × 4b, 50MHz, 76GOPS constant throughput | §V |
| sparse-layer efficiency | more than 10 | TOPS/W | Envision 28nm FDSOI, 2017 | 0.3TOPS/W high-precision mode | sparse CONV layers in 4 × 4b mode | §V |
| power | 18 | mW | Envision 28nm FDSOI, 2017 | 300mW at 16b, 200MHz | 4 × 4b, 50MHz, 76GOPS | §V |
| improvement over DAS | 6.9× | relative | Envision 28nm FDSOI, 2017 | DAS | 4 × 4b full DVAFS at constant throughput | §V |
| improvement over DVAS | 4.1× | relative | Envision 28nm FDSOI, 2017 | DVAS | 4 × 4b full DVAFS at constant throughput | §V |
evidence: Equations 1–3, Figures 1–4, Tables I–II, Figures 7–8, Table III

## space_gaps
* `lane_width_gating` lacks choices for precision-dependent voltage, subword-dependent frequency, constant-throughput operation, and power-domain partitioning. # §II.B–§II.C
* `twin_precision_subword.partition` cannot explicitly record a design supporting full-width, halves, and quarters as concurrent runtime modes. # §III.A
* The vocabulary lacks a cross-unit DVAFS family even though `approximate_mac_nn.precision_scaling` includes `dvafs` only within an NN-specific family. # §II.C, §III

## open_questions
* The Booth radix, signed-number handling, Wallace-tree compressor cells, and final carry-propagate adder are not specified.
* Envision's 4 × 4b constant-200MHz power is 104mW in §V but 108mW in the Figure 8 caption.
* Figure 3 provides plotted RMSE/energy curves without tabulated coordinates, so the merge pass must not derive numerical points from the graph.
