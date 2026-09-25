---
handle: samimi_2020
citation: Samimi, Kamal, Afzali-Kusha, Pedram, "Res-DNN: A Residue Number System-Based DNN Accelerator Unit", IEEE Transactions on Circuits and Systems I, 2020
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [int8, int16, rns16, fp32]
authority: incremental
pages_read: 14 / 14
---

## summary
Res-DNN keeps intermediate DNN data/MACs/ReLU/MAX pooling in RNS and retains weights/primary inputs in BNS at main memory boundaries. The design combines modular arithmetic, base extension/scaling, compression, and a weight-local register file. Across seven CNNs, Res-DNN reports 61% less computation energy than its BNS implementation and 30% less overall energy than Eyeriss. # p.10, p.12

## families
### rns_dnn_accelerator  (role: proposes)
mechanism: A 12 × 14 PE array uses row-stationary dataflow and performs convolution/FC MACs in three independent residue channels. ReLU uses RNS sign detection, and MAX pooling uses RNS comparison, so intermediate feature maps remain in RNS. Base extension prevents arithmetic overflow, scaling restores the primary range, a LUT-free zero-oriented Huffman code reduces DRAM traffic, and a 12-byte WLL-RF caches repeatedly accessed weight rows. # p.4–p.9
choices:
  channel_width_n: 5   # p.4
  activation_handling: sign_detection_and_comparison_in_rns [outside domain]   # p.4, p.7–p.8
new_choices:
  moduli_set: {2^n−1, 2^n, 2^(n+1)−1} — selects the three RNS channels   # p.4
  overflow_control: base_extension_then_scaling — extends multiplication/addition ranges and restores 16-bit storage   # p.4–p.7
  memory_compression: zero_flag_plus_16_bit_value — encodes zero as 0 and nonzero data as 1 followed by 16 bits   # p.9
  weight_local_storage: 12_byte_WLL_RF — caches a repeatedly accessed filter row below the weight RF   # p.5
slots:
  none
parameters: 12 × 14 PEs; 8-bit BNS weights; 16-bit BNS primary inputs; 16-bit RNS intermediate data; k = 3; k′ = 6; 532/28/66-byte weight/IFmap/partial-sum RFs; 12-byte WLL-RF   # p.4–p.5, p.9–p.10
results:
| metric | value | unit | technology / device | baseline | condition | page |
| computation energy | 61% less | relative | 45 nm NanGate, 2020 | corresponding BNS implementation | seven CNNs | p.10 |
| overall energy | 30% lower average; 23%–36% | relative | 45 nm NanGate, 2020 | 8-bit-weight Eyeriss | seven CNNs | p.12 |
| PE delay | 2.1× smaller | relative | 45 nm NanGate, 2020 | BNS PE | computational core | p.10 |
| PE energy | 2.9× smaller | relative | 45 nm NanGate, 2020 | BNS PE | computational core | p.10 |
| PE EDP | 6.4× smaller | relative | 45 nm NanGate, 2020 | BNS PE | computational core | p.10 |
| PE frequency | 1.20 GHz | GHz | 45 nm NanGate, 2020 | 0.667 GHz BNS PE | pipeline implementation | p.10 |
| DRAM compression ratio | 2.14× average; 1.83×–2.55× | relative | 45 nm/CACTI, 2020 | uncompressed accesses | seven CNNs | p.11 |
| weight-RF access reduction | 80% average; 59%–90% | relative | 45 nm NanGate, 2020 | without WLL-RF | seven CNNs | p.12 |
errors_and_checks: Against fp32 inference, maximum accuracy loss is 1.15% for RNS and 0.27% for fixed-point BNS; average RNS accuracy loss is about 0.23%. No fault-detection mechanism is reported. # p.10–p.11
conditions: RNS benefits add/multiply-intensive convolution and FC layers, while comparison/sign detection/scaling require specialized hardware. The design requires extra arithmetic bits for overflow control, and selected k/k′ values trade energy against accuracy. # p.2, p.9–p.10
evidence: §III, Figures 1–9, §IV, Figures 10–17, Tables III–V, pp.4–13

### rns_channel_arithmetic  (role: extends)
mechanism: Each MAC is decomposed across modulo 2^n−1, 2^(n+x), and 2^(n+1)−1 channels. The power-of-two channel discards carry-out, while the minus-one channels use end-around-carry addition. Multipliers use radix-4 Booth partial products, CSA/4:2 reduction, and a channel-specific Sklansky merge adder. # p.5–p.6
choices:
  modulus_form: pow2_minus_1 / pow2 [outside domain]   # p.5–p.6
  channel_width_n: 5   # p.4
  multiplier_reduction: booth_modular   # p.6
new_choices:
  heterogeneous_channel_widths: 5/5/6_bits — widths of the primary three-channel representation   # p.9
slots:
  modular_adder: end_around_carry [topology=sklansky] / parallel_prefix [topology=sklansky]   # p.6
parameters: primary dynamic range [0, 62496); multiplication width 16 + k; addition width 16 + k′   # p.4, p.9
results:
| metric | value | unit | technology / device | baseline | condition | page |
| multiplier energy | 4.62× lower | relative | 45 nm NanGate, 2020 | 8 × 16-bit BNS multiplier | 19-bit RNS multiplier | p.10 |
| multiplier delay | 2.1× lower | relative | 45 nm NanGate, 2020 | BNS multiplier | 19-bit RNS multiplier | p.10 |
| multiplier EDP | 9.72× smaller | relative | 45 nm NanGate, 2020 | BNS multiplier | 19-bit RNS multiplier | p.10 |
| adder energy | 1.08× lower | relative | 45 nm NanGate, 2020 | 22-bit BNS adder | 22-bit RNS adder | p.10 |
| adder delay | 1.05× lower | relative | 45 nm NanGate, 2020 | BNS adder | 22-bit RNS adder | p.10 |
| adder EDP | 1.11× smaller | relative | 45 nm NanGate, 2020 | BNS adder | 22-bit RNS adder | p.10 |
errors_and_checks: Arithmetic overflow is controlled through profiled range extension and scaling; no arithmetic error checker is reported. # p.9–p.10
conditions: The RNS multiplier occupies about half the BNS multiplier area, while the RNS and BNS adder areas are almost equal. # p.10
evidence: §III-B.1, Figures 2–3, Table III, pp.5–6, p.10

### rns_scaling_comparison  (role: extends)
mechanism: A simplified Szabo-Tanaka process extends 2^n to 2^(n+e) without increasing the number of moduli. Scaling reduces that channel back to 2^n using residue subtraction and right-rotate shifts. MAX comparison uses dynamic-range partition functions, while ReLU sign detection uses a simplified mixed-radix CRT expression. # p.6–p.8
choices:
  operation: scale / sign_detect / compare / base_extend [outside domain]   # p.6–p.8
new_choices:
  base_extension_method: simplified_szabo_tanaka — replaces the covered modulus without adding a channel   # p.6–p.7
  comparison_method: dynamic_range_partitioning — compares partition functions before the final residue   # p.7–p.8
  sign_method: mixed_radix_crt — implements the simplified sign expression without division   # p.8
slots:
  none
parameters: n = 5; extension modulus 2^(n+e); k = 3; k′ = 6   # p.4, p.6, p.10
results:
| metric | value | unit | technology / device | baseline | condition | page |
| BNS comparator energy | 11.8× lower | relative | 45 nm NanGate, 2020 | proposed RNS comparator | comparator operation | p.10 |
| BNS comparator area | 2.9× lower | relative | 45 nm NanGate, 2020 | proposed RNS comparator | comparator operation | p.10 |
errors_and_checks: The selected extensions yield a maximum RNS inference accuracy loss of 1.15% against fp32. # p.10–p.11
conditions: Comparison/sign detection/scaling are less efficient in RNS than add/multiply, so their overhead reduces the computation gain. # p.2, p.10
evidence: §III-B.2–§III-B.5, Figures 4–8, pp.6–8, Table III

### booth_recoded_parallel  (role: instantiates)
mechanism: Every residue-channel multiplier uses radix-4 Booth encoding. The 2^n−1 channel reduces three partial products with an n-bit CSA, the 2^(n+1)−1 channel uses an n-bit 4:2 compressor, and channel-specific Sklansky adders merge the reduced outputs. # p.6
choices:
  booth_radix: 4   # p.6
  hard_multiple_gen: none   # p.6
new_choices:
  channel_specific_reduction: CSA_or_4:2 — selects reduction hardware by residue modulus   # p.6
slots:
  reduction: csa_reduction_tree / compressor_4_2_tree   # p.6
  hard_multiple_adder: none   # p.6
parameters: n = 5; three partial products in the 2^n−1 channel   # p.6
results:
| metric | value | unit | technology / device | baseline | condition | page |
| multiplier area | about half | relative | 45 nm NanGate, 2020 | BNS multiplier | Res-DNN multiplier | p.10 |
errors_and_checks: none
conditions: The merge adder must return each result to its channel representation range. # p.6
evidence: §III-B.1, Figure 3, p.6

### end_around_carry  (role: instantiates)
mechanism: Modulo 2^n−1 and 2^(n+1)−1 additions use end-around-carry adders with Sklansky prefix cores. The same merge structure closes modular multiplication after partial-product reduction. # p.6
choices:
  modulus: mod_2n_minus_1   # p.6
  recirculation: cyclic_prefix_level   # p.6
  topology: sklansky   # p.6
new_choices:
  none
slots:
  none
parameters: illustrated as an 8-bit EAC adder; instantiated for the two minus-one channels   # p.6
results: none reported separately
errors_and_checks: none
conditions: The power-of-two channel uses a conventional Sklansky adder instead of EAC. # p.6
evidence: §III-B.1, Figures 2–3, p.6

## new_families
none

## space_gaps
* `rns_dnn_accelerator.activation_handling` lacks a value for keeping ReLU sign detection and MAX comparison in RNS. # p.4, p.7–p.8
* `rns_dnn_accelerator` lacks choices/slots for moduli-set selection, overflow extension/scaling, compression, and local memory hierarchy. # p.4–p.9
* `rns_scaling_comparison.method` lacks simplified Szabo-Tanaka base extension, dynamic-range-partition comparison, and mixed-radix CRT sign detection. # p.6–p.8
* `rns_channel_arithmetic.modulus_form` cannot express a heterogeneous multi-channel set containing both `pow2_minus_1` and `pow2`. # p.4–p.6

## open_questions
* Table III’s absolute delay/energy/area values are not recoverable from the supplied text rendering, so only narrative relative results are recorded.
* The paper profiles per-layer k/k′ values but fixes k = 3 and k′ = 6 for evaluation; the exact runtime/configuration mechanism is not stated. # p.9–p.10
