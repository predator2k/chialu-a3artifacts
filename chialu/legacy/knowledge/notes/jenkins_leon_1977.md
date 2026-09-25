---
handle: jenkins_leon_1977
citation: Jenkins, Leon, "The Use of Residue Number Systems in the Design of Finite Impulse Response Digital Filters", IEEE Transactions on Circuits and Systems, 1977
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [int8, int10, residue_integer]
authority: landmark
pages_read: 11 / 11
---

## summary
The paper implements FIR multiplication/addition in parallel residue channels and proposes a ROM/adder-shifter Chinese Remainder Theorem decoder. A 64th-order dual-bandpass filter comparison reports speed/package/power tradeoffs for two RNS structures, two conventional structures, and a bit-slice structure.

## families
### rns_channel_arithmetic  (role: instantiates)
mechanism: Pairwise modular addition and multiplication operate independently across relatively-prime residue channels. Small-modulus multiplication uses complete tables in ROM/FPLA, while simultaneous channel processing increases throughput. The main filter uses moduli {16,13,11,9,7}. # p.193, p.197
choices:
  modulus_form: {pow2, generic} [outside domain]   # p.197
  channel_width_n: 4   # p.197
  multiplier_reduction: rom   # p.193, p.197
new_choices:
  moduli_set_composition: pairwise_relatively_prime_small_moduli — selects heterogeneous channel moduli to meet the dynamic range with small tables   # p.192, p.197
slots:
  none
parameters: main filter moduli {16,13,11,9,7}; dynamic range 17.1 bits; each modulus requires at most 4 bits; multiplication tables (256 X4)-bit PROM, with (64X4)-bit sufficient for mod 7   # p.197
results:
| metric | value | unit | technology / device | baseline | condition | page |
| --- | --- | --- | --- | --- | --- | --- |
| residue multiplication table access | 30 | ns | Signetics 82827 PROM / 1977 | none | (256 X4)-bit PROM | p.198 |
| residue addition table access | 30 | ns | Signetics 82827 PROM / 1977 | none | addition tables stored in the same PROM type | p.198 |
errors_and_checks: Integer addition/multiplication is roundoff-free when the result remains within the RNS dynamic range; overflow loses the most significant information. # p.192-p.193
conditions: Small-modulus channels reduce table storage and permit parallel computation, but encoding/decoding hardware and longer total wordlength add overhead. # p.193
evidence: §II.B; Fig. 1; §V

### rns_reverse_converter  (role: proposes)
mechanism: A constructive Chinese Remainder Theorem translation premultiplies fixed inverse factors into the stored filter coefficients. Output residue bits address a ROM function F(l), and a mod-M adder-shifter shifts and accumulates the retrieved values. A modified modulus permits scaled/quantized decoding with shorter ROM and accumulator words. # p.194-p.196
choices:
  algorithm: crt   # p.194
  implementation: rom_plus_adder_shifter [outside domain]   # p.194
new_choices:
  output_scaling: {full_precision, modulus_scaled_quantized} — selects exact decoding or decoding scaled by a chosen modulus with bounded quantization error   # p.195-p.196
slots:
  none
parameters: typical translation uses 4 memory addresses, 3 shifts, and 3 additions; numerical example uses P={19,23,29,31}; scaled example divides by 31   # p.194-p.196
results:
| metric | value | unit | technology / device | baseline | condition | page |
| --- | --- | --- | --- | --- | --- | --- |
| stored output-function precision | 16 | bits | UNKNOWN / 1977 | scaled decoder | full-precision decoding | p.196 |
| accumulator wordlength | 18 | bits | UNKNOWN / 1977 | scaled decoder | full-precision decoding | p.196 |
| stored output-function precision | 12 | bits | UNKNOWN / 1977 | full-precision decoder | scale factor 31 | p.196 |
| accumulator wordlength | 14 | bits | UNKNOWN / 1977 | full-precision decoder | scale factor 31 | p.196 |
errors_and_checks: Full decoding reproduces the direct full-precision result. The scaled numerical example reports |δ|<5.806 and produces -67 from the full result -2107 after scaling by 31. # p.196
conditions: Scaled decoding is valid when quantization does not cross the positive/negative boundary; the scaled range must be large enough for the filter dynamic range. # p.195
evidence: §III; Theorems 1-2; Fig. 3; §IV

### rns_dsp_datapath  (role: proposes)
mechanism: FIR coefficients and samples are encoded per residue channel, and each channel performs its convolution with stored modular multiplication/addition tables. Case 1 encodes before the circulating delay memories. Case 2 moves the encoding PROMs after the memories to reduce packages at a lower data rate. # p.197-p.199
choices:
  kernel: fir   # p.191, p.197
  scaling_placement: output_only   # p.194-p.196
new_choices: none
slots: none
parameters: 64th-order dual-bandpass FIR; 8-bit input; 10-bit coefficients; P={16,13,11,9,7}; dynamically changeable coefficients in RAM; no linear-phase symmetry optimization   # p.197-p.198
results:
| metric | value | unit | technology / device | baseline | condition | page |
| --- | --- | --- | --- | --- | --- | --- |
| data rate | 260.4 | kHz | standard TTL IC packages / 1977 | conventional Case 3 | RNS Case 1 | p.198 |
| package count | 126 | packages | standard TTL IC packages / 1977 | conventional Case 3 | RNS Case 1 | p.198 |
| power consumption | 63.0 | W | standard TTL IC packages / 1977 | none | RNS Case 1, 500 mW per chip | p.198 |
| data rate | 173.6 | kHz | standard TTL IC packages / 1977 | conventional Case 3 | RNS Case 2 | p.199 |
| package count | 82 | packages | standard TTL IC packages / 1977 | conventional Case 3 | RNS Case 2 | p.199 |
| power consumption | 41.0 | W | standard TTL IC packages / 1977 | none | RNS Case 2 | p.199 |
| data rate | 52.43 | kHz | TTL components / 1977 | none | conventional Case 3 shift-add multiplier | p.199 |
| package count | 77 | packages | TTL components / 1977 | none | conventional Case 3 shift-add multiplier | p.199 |
| data rate | 117.48 | kHz | TTL components / 1977 | none | conventional Case 4 array multiplier | p.199 |
| package count | 137 | packages | TTL components / 1977 | none | conventional Case 4 array multiplier | p.199 |
| data rate | 744.0 | kHz | PROM/RAM IC packages / 1977 | RNS Cases 1-2 | bit-slice architecture | p.199 |
| package count | 128 | packages | PROM IC packages / 1977 | RNS Cases 1-2 | bit-slice coefficient storage | p.199 |
| package count | 200 | packages | RAM IC packages / 1977 | RNS Cases 1-2 | bit-slice coefficient storage | p.199 |
errors_and_checks: The fundamental RNS implementation produces full-precision outputs without roundoff error, subject to adequate dynamic range. # p.193, p.200
conditions: Computational efficiency improves for 20<N<100 with many small moduli. Bit-slice is faster/cheaper for low-order fixed-coefficient FIRs, while RNS becomes more attractive for high-order multiplexing/adaptive filters with changing coefficients. Encoding/decoding contributes 18-20 percent of RNS cost. # p.196, p.200
evidence: §V; Figs. 5-12; §VI

## new_families
### generalized_modular_correction_adder  (domain: redundant: residue number systems, closest: end_around_carry, why_not: end_around_carry restricts the modulus to 2^n±1, while this correction supports any modulus)
mechanism: A conventional L-bit 2’s-complement adder performs finite-field addition. Logic detects forbidden output states or overflow and adds the fixed correction C_L=2^L-p. The paper calls the correction a generalized end-around carry and states that it can be hard-wired with the adder. # p.192
choices: modulus: general_integer; overflow_detection: forbidden_state_logic; correction_constant: C_L=2^L-p   # p.192
results: none
evidence: p.192

### rns_forward_encoder  (domain: redundant: residue number systems, closest: rns_reverse_converter, why_not: rns_reverse_converter converts residues to binary rather than binary to residues)
mechanism: Each input bit addresses stored values of 2^j mod p_i, and modular adders combine the selected values into each residue digit. Segmenting the input bits across several ROMs stores partial sums and reduces the encoder to one modular addition at additional ROM cost. # p.193-p.194
choices: input_segmentation: {bitwise, multi_bit_partial_sum}; speed_cost_partition: variable_rom_segmentation   # p.193-p.194
results:
| metric | value | unit | technology / device | baseline | condition | page |
| --- | --- | --- | --- | --- | --- | --- |
| ROM count | 2L | ROMs | UNKNOWN / 1977 | bitwise encoding | t=7, two 4-bit input segments | p.194 |
| storage per ROM | 16 | words | UNKNOWN / 1977 | bitwise encoding | t=7, two-segment encoder | p.194 |
| modular additions | 1 | addition | UNKNOWN / 1977 | bitwise encoding | per residue, two-segment encoder | p.194 |
evidence: §III; Fig. 2; equations (5)-(9), p.193-p.194

## space_gaps
* rns_channel_arithmetic.modulus_form needs a mixed value for heterogeneous sets such as {16,13,11,9,7}. # p.197
* rns_channel_arithmetic.modular_adder should admit generalized_modular_correction_adder. # p.192
* rns_reverse_converter.implementation needs rom_plus_adder_shifter. # p.194
* rns_dsp_datapath needs input_encoder/output_decoder slots admitting rns_forward_encoder/rns_reverse_converter. # p.193-p.196

## open_questions
* The 17.1-bit dynamic range of {16,13,11,9,7} is below the pessimistic 18.4-bit output bound; the paper states that it is adequate for most practical situations but does not quantify overflow probability. # p.197
