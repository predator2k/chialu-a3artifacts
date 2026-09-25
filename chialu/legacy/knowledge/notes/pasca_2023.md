---
handle: pasca_2023
citation: B. Pasca, M. Langhammer, "Extracting Low-Precision Floating-Point Adders from Embedded Hard FP DSP Blocks on FPGAs", 30th IEEE Symposium on Computer Arithmetic (ARITH), 2023
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [fp16]
authority: incremental
pages_read: 5 / 5
---

## summary
The paper extracts correctly rounded fp16 adders from Agilex reduced-precision DSP modes and from SP hard FP DSP Blocks available in Agilex/Arria 10/Stratix 10 devices. The Agilex-specific mapping uses one DSP Block with no extra logic, while the generic SP mapping uses one DSP Block and 26 ALMs on Stratix 10. Both architectures flush input/output subnormals to zero.

## families
### hard_fp_dsp  (role: instantiates)
mechanism: The Agilex DSP Block contains two low-precision FP multipliers, a low-precision adder, and a subsequent SP adder. Its HP mode accepts four binary16 multiplier inputs, correctly rounds the products and sum, flushes subnormals, and converts the low-precision sum to SP before the SP addition. Arria 10/Stratix 10/Agilex DSP Blocks also provide an SP multiply-add mode that flushes subnormals. # pp.1-2
choices:
  fp_format: fp16_fp32   # pp.1-2
new_choices:
  reduced_precision_modes: {bfloat16, HP, bfloat16+} — selects the low-precision multiplier/adder format inside the Agilex DSP Block   # p.1
  subnormal_behavior: flush_input_and_output — controls the hard block’s treatment of subnormals   # pp.1-2
slots:
  none
parameters: two HP multipliers; one HP adder; one subsequent SP adder; four 16-bit binary16 multiplier inputs   # pp.1-2
results: none
errors_and_checks: Products and the HP sum are correctly rounded; subnormal inputs and outputs are flushed to zero.   # pp.1-2
conditions: The reduced-precision sum-of-products mode is Agilex-specific, while the SP multiply-add mode is available on Arria 10/Stratix 10/Agilex.   # pp.1-3
evidence: §II, Fig. 1, pp.1-2

## new_families
### embedded_dsp_fp_adder_extraction  (domain: dsp: FPGA DSP blocks, closest: hard_fp_dsp, why_not: hard_fp_dsp describes the embedded operator, while this mechanism remaps constants/exponents/fractions to extract a standalone lower-precision adder.)
mechanism: The Agilex-specific architecture maps a+b onto (a·1+b·1)+(-0), which preserves the sign of a zero result, extracts D[22:13] as the fp16 fraction, and forms the exponent from expD[7] concatenated with expD[3:0]. The generic architecture maps fp16 exponents into the top of the SP range with LUT1, performs SP addition, rounds the fraction to fp16, and reverses the exponent mapping with a 64-element LUT6. # pp.2-4
choices:
  source_dsp_mode: {low_precision_sum_of_products, single_precision_add} — selects the embedded operation used to realize addition   # pp.2-4
  exponent_conversion: {xor_fix, bit_concatenation, lut_remap} — selects the logic used to translate the output exponent   # pp.2-4
  accuracy_contract: {correctly_rounded_rne, faithful} — selects the stated output-accuracy target   # p.1
  subnormal_handling: {flush_to_zero} — selects the supported treatment of input/output subnormals   # p.1
results:
| metric | value | unit | technology / device | baseline | condition | page |
| ALMs | 5 | ALMs | Agilex, fastest speed grade / 2023 | Logic: 152 ALMs | Proposed-A1; target 500MHz, -1 | p.4 |
| DSPs | 1 | DSPs | Agilex, fastest speed grade / 2023 | Logic: 0 DSPs | Proposed-A1; target 500MHz, -1 | p.4 |
| Latency | 5 | UNKNOWN | Agilex, fastest speed grade / 2023 | Logic: 11 | Proposed-A1; target 500MHz, -1 | p.4 |
| Ratio | 147 | ALMs/DSP | Agilex, fastest speed grade / 2023 | Logic-only implementation | Proposed-A1 | p.4 |
| ALMs | 0 | ALMs | Agilex, fastest speed grade / 2023 | Logic: 152 ALMs | Proposed-A2; target 500MHz, -1 | p.4 |
| DSPs | 1 | DSPs | Agilex, fastest speed grade / 2023 | Logic: 0 DSPs | Proposed-A2; target 500MHz, -1 | p.4 |
| Latency | 5 | UNKNOWN | Agilex, fastest speed grade / 2023 | Logic: 11 | Proposed-A2; target 500MHz, -1 | p.4 |
| Ratio | 152 | ALMs/DSP | Agilex, fastest speed grade / 2023 | Logic-only implementation | Proposed-A2 | p.4 |
| ALMs | 26 | ALMs | Stratix 10, fastest speed grade / 2023 | Logic: 200 ALMs | Proposed-B; target 500MHz, -1 | p.4 |
| DSPs | 1 | DSPs | Stratix 10, fastest speed grade / 2023 | Logic: 0 DSPs | Proposed-B; target 500MHz, -1 | p.4 |
| Latency | 6 | UNKNOWN | Stratix 10, fastest speed grade / 2023 | Logic: 16 | Proposed-B; target 500MHz, -1 | p.4 |
| Ratio | 174 | ALMs/DSP | Stratix 10, fastest speed grade / 2023 | Logic-only implementation | Proposed-B | p.4 |
| FFT ALMs | 2183 | ALMs | Agilex / 2023 | Old: 8116 ALMs | 8K FFT using Proposed-A2 | p.4 |
| FFT M20K | 46 | M20K | Agilex / 2023 | Old: 62 M20K | 8K FFT using Proposed-A2 | p.4 |
| FFT DSPs | 44 | DSPs | Agilex / 2023 | Old: 12 DSPs | 8K FFT using Proposed-A2 | p.4 |
| FFT trade ratio | approximately 187 | ALMs per DSP | Agilex / 2023 | Old 8K FFT | 32 additional DSPs | pp.4-5 |
evidence: Figs. 2-4, Algorithms 1-2, Tables I-IV, §§III-IV, pp.2-5

## space_gaps
* `hard_fp_dsp.fp_format` lacks separate values for the Agilex `HP`, `bfloat16`, and `bfloat16+` reduced-precision modes. # p.1
* Floating-point adder `sig_adder` slots cannot name an embedded hard FP DSP Block as their implementation. # pp.2-4
* The vocabulary lacks choices for constant-operand DSP extraction and exponent remapping by bit selection/XOR/LUTs. # pp.2-4

## open_questions
* The paper states both correctly rounded RNE and faithful-rounding goals, but the architecture figures/results do not identify separate faithful-rounding configurations. # pp.1-4
* Table III labels its latency column only as `Latency`, so its unit is not explicit. # p.4
* Exact Agilex and Stratix 10 device part numbers are not reported. # p.4
