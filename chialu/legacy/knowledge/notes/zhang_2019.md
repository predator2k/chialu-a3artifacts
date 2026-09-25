---
handle: zhang_2019
citation: H. Zhang, J. He, S.-B. Ko, "Efficient Posit Multiply-Accumulate Unit Generator for Deep Learning Applications", IEEE International Symposium on Circuits and Systems (ISCAS), 2019
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [posit8, posit16, posit32, fp8, fp16, fp32]
authority: incremental
pages_read: 5 / 5
---

## summary
The document proposes a parameterized posit multiply-accumulate generator that emits combinational Verilog for arbitrary total bitwidth `nb` and exponent bitwidth `es` (p.1). The architecture fuses multiplication and addition before one round-to-nearest-even operation and presents a five-stage pipeline implementation (p.1, p.2, p.4). Synthesis compares 8-bit/16-bit/32-bit posit and floating-point MACs in STM-28nm technology (p.4).

## families
### classic_fma  (role: extends)
mechanism: Posit operands A/B/C are unpacked into sign/effective exponent/mantissa components. A/B mantissas are multiplied while C is aligned to the product. A 3-to-2 carry-save adder injects the low part of aligned C into the product, followed by a carry-propagate adder and a high-part incrementer. An LZA predicts normalization distance, with a possible one-bit error corrected in the normalization shifter. The result is normalized, repacked into posit regime/exponent/fraction fields, and rounded once to nearest even. The generated unit is combinational; a five-stage pipeline partition is also presented (p.2-p.4).
choices:
  pipeline_depth: 5   # p.2, p.4
new_choices:
  posit_parameterization: nb, es — parameterizes every datapath width and the posit extraction/packing logic   # p.1-p.2
slots:
  align: full_align   # p.2-p.3
  lza: lza   # p.2-p.3
  cpa: carry_select   # p.2
  multiplier: booth_recoded_parallel [booth_radix=4]   # p.2
parameters: arbitrary Posit(nb, es); evaluated as 8-bit with es=0-4, 16-bit with es=1-5, and 32-bit with es=1-8; combinational generator output; five-stage pipeline example   # p.1, p.4
results:
| metric | value | unit | technology / device | baseline | condition | page |
| dynamic range | 2 × 10−3 to 3 × 102 | — | STM-28nm, 2019 | none | Std FP8 | p.4 |
| delay | 0.60 / 25 | ns / FO4 | STM-28nm, 2019 | none | Std FP8 | p.4 |
| area | 872 / 1817 | μm2 / NAND2 | STM-28nm, 2019 | none | Std FP8 | p.4 |
| power | 0.59 | mW | STM-28nm, 2019 | none | Std FP8 | p.4 |
| dynamic range | 1 × 10−29 to 8 × 1028 | — | STM-28nm, 2019 | Std FP8 | Posit(8,4) | p.4 |
| delay | 1.00 / 42 | ns / FO4 | STM-28nm, 2019 | Std FP8 | Posit(8,4) | p.4 |
| area | 1116 / 2325 | μm2 / NAND2 | STM-28nm, 2019 | Std FP8 | Posit(8,4) | p.4 |
| power | 0.68 | mW | STM-28nm, 2019 | Std FP8 | Posit(8,4) | p.4 |
| dynamic range | 6 × 10−8 to 7 × 104 | — | STM-28nm, 2019 | none | Std FP16 | p.4 |
| delay | 0.75 / 31 | ns / FO4 | STM-28nm, 2019 | none | Std FP16 | p.4 |
| area | 2196 / 4575 | μm2 / NAND2 | STM-28nm, 2019 | none | Std FP16 | p.4 |
| power | 1.80 | mW | STM-28nm, 2019 | none | Std FP16 | p.4 |
| dynamic range | 1 × 10−135 to 7 × 10134 | — | STM-28nm, 2019 | Std FP16 | Posit(16,5) | p.4 |
| delay | 1.30 / 54 | ns / FO4 | STM-28nm, 2019 | Std FP16 | Posit(16,5) | p.4 |
| area | 3533 / 7360 | μm2 / NAND2 | STM-28nm, 2019 | Std FP16 | Posit(16,5) | p.4 |
| power | 2.48 | mW | STM-28nm, 2019 | Std FP16 | Posit(16,5) | p.4 |
| dynamic range | 1 × 10−45 to 4 × 1038 | — | STM-28nm, 2019 | none | Std FP32 | p.4 |
| delay | 0.93 / 39 | ns / FO4 | STM-28nm, 2019 | none | Std FP32 | p.4 |
| area | 6081 / 12668 | μm2 / NAND2 | STM-28nm, 2019 | none | Std FP32 | p.4 |
| power | 5.14 | mW | STM-28nm, 2019 | none | Std FP32 | p.4 |
| dynamic range | 8 × 10−2309 to 8 × 102311 | — | STM-28nm, 2019 | Std FP32 | Posit(32,8) | p.4 |
| delay | 1.60 / 67 | ns / FO4 | STM-28nm, 2019 | Std FP32 | Posit(32,8) | p.4 |
| area | 8992 / 18733 | μm2 / NAND2 | STM-28nm, 2019 | Std FP32 | Posit(32,8) | p.4 |
| power | 7.47 | mW | STM-28nm, 2019 | Std FP32 | Posit(32,8) | p.4 |
| input-process stage delay | 0.20 | ns | STM-28nm, 2019 | none | five-stage Posit(8,0) | p.4 |
| multiply-and-align stage delay | 0.23 | ns | STM-28nm, 2019 | none | five-stage Posit(8,0) | p.4 |
| adder-and-LZA stage delay | 0.21 | ns | STM-28nm, 2019 | none | five-stage Posit(8,0) | p.4 |
| normalize-shift stage delay | 0.19 | ns | STM-28nm, 2019 | none | five-stage Posit(8,0) | p.4 |
| output-process stage delay | 0.20 | ns | STM-28nm, 2019 | none | five-stage Posit(8,0) | p.4 |
| input-process stage delay | 0.28 | ns | STM-28nm, 2019 | none | five-stage Posit(16,1) | p.4 |
| multiply-and-align stage delay | 0.31 | ns | STM-28nm, 2019 | none | five-stage Posit(16,1) | p.4 |
| adder-and-LZA stage delay | 0.24 | ns | STM-28nm, 2019 | none | five-stage Posit(16,1) | p.4 |
| normalize-shift stage delay | 0.20 | ns | STM-28nm, 2019 | none | five-stage Posit(16,1) | p.4 |
| output-process stage delay | 0.29 | ns | STM-28nm, 2019 | none | five-stage Posit(16,1) | p.4 |
| input-process stage delay | 0.34 | ns | STM-28nm, 2019 | none | five-stage Posit(32,3) | p.4 |
| multiply-and-align stage delay | 0.37 | ns | STM-28nm, 2019 | none | five-stage Posit(32,3) | p.4 |
| adder-and-LZA stage delay | 0.32 | ns | STM-28nm, 2019 | none | five-stage Posit(32,3) | p.4 |
| normalize-shift stage delay | 0.28 | ns | STM-28nm, 2019 | none | five-stage Posit(32,3) | p.4 |
| output-process stage delay | 0.35 | ns | STM-28nm, 2019 | none | five-stage Posit(32,3) | p.4 |
errors_and_checks: The output uses round to nearest even; extensive test vectors verify functionality, but no quantitative error bound or test coverage is reported. The normalization shifter corrects the possible one-bit LZA error (p.1, p.3-p.4).
conditions: Posit extraction and packing increase delay/resource consumption relative to same-width floating-point MACs (p.4). Within one total bitwidth, delay is similar across `es` values, while area/power decrease as `es` increases because the mantissa multiplier and final adder become narrower (p.4). The Posit(32,3) pipeline has a 0.37ns worst stage, reported as roughly 15 FO4 (p.4).
evidence: Fig. 2-Fig. 6 and §III (p.2-p.3); Fig. 7-Fig. 9, Table I, and Table II (p.4).

### booth_recoded_parallel  (role: instantiates)
mechanism: The `(nb − es)`-bit unsigned mantissa multiplier uses radix-4 modified Booth multiplication. Several levels of 4-to-2 carry-save adders accumulate its partial products before the product enters the fused MAC addition (p.2).
choices:
  booth_radix: 4   # p.2
new_choices:
  none
slots:
  reduction: compressor_4_2_tree   # p.2
parameters: unsigned mantissa width `(nb − es)` bits   # p.2
results:
| metric | value | unit | technology / device | baseline | condition | page |
| standalone results | UNKNOWN | UNKNOWN | UNKNOWN, 2019 | none | multiplier is measured only inside the complete MAC | p.4 |
errors_and_checks: none
conditions: The multiplier is parameterized for any required mantissa bitwidth; no standalone multiplier cost is reported (p.2, p.4).
evidence: §III-B and Fig. 2 (p.2).

## new_families
none

## space_gaps
* `classic_fma` lacks choices for posit `nb`/`es` parameterization and posit-specific extraction/packing, which this generator makes part of the fused datapath (p.1-p.3).
* The posit-unit vocabulary lacks a fused posit MAC generator alongside `posit_adder_multiplier` and `posit_quire_mac` (p.1-p.4).

## open_questions
* The exact carry-select topology/block sizing is not specified (p.2).
* The rounding hardware is described functionally as round to nearest even but is not mapped unambiguously to an existing `round` slot family (p.3).
* Fig. 7-Fig. 9 plot area/power for all `es` variants without tabulating exact point values, so those values must not be reconstructed from the plots (p.4).
