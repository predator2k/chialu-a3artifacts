---
handle: jaiswal_2018
citation: M. K. Jaiswal, H. K.-H. So, "Universal Number Posit Arithmetic Generator on FPGA", Design, Automation and Test in Europe (DATE), 2018
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [parameterized_fp, posit8, posit16, posit24, posit32, posit50, posit64]
authority: incremental
pages_read: 4 / 4
---

## summary
The paper proposes parameterized Verilog generators for FP-to-posit conversion, posit-to-FP conversion, posit addition/subtraction, and posit multiplication. The implementations support runtime-varying posit regime/exponent/mantissa positions and are demonstrated on a Xilinx Virtex-6 FPGA. # p.1159, p.1162

## families
### posit_ieee_interop  (role: proposes)
mechanism: Separate boundary converters extract the source sign/exponent/regime/mantissa fields and repack them into the destination format. FP-to-posit conversion prenormalizes subnormal FP inputs, derives the posit regime and exponent from the unbiased FP exponent, and dynamically shifts a constructed regime/exponent/mantissa word. Posit-to-FP conversion uses LOD/LZD detection and dynamic shifting to remove the variable-length regime before constructing the biased FP exponent. # p.1159–1161
choices:
  interop_style: boundary_converters   # p.1159
  conversion_direction: bidirectional   # p.1159
new_choices:
  fp_subnormal_handling: pre_normalize — FP-to-posit conversion normalizes subnormal mantissas before component construction.   # p.1160
  nan_handling: excluded — NaN detection is excluded because the paper's posit format has no NaN representation.   # p.1160
slots:
  none
parameters: Posit/FP word size N; posit exponent size ES; FP exponent size E; FP bias BIAS; evaluated N = 8, 16, 24, 32, 50, 64 with E = 3, 5, 7, 8, 10, 11 respectively; single-cycle implementation.   # p.1159, p.1162
results:
| metric | value | unit | technology / device | baseline | condition | page |
| latency | 1 | cycle | Xilinx Virtex-6 FPGA / 2018 | none | parameterized FP-to-posit and posit-to-FP implementations | p.1162 |
errors_and_checks: Functional outputs are verified against the developers' Julia posit package; a numerical error or rounding-accuracy contract is UNKNOWN.   # p.1162
conditions: The converters assume FP operands at system boundaries because posit is not a defined standard in the paper's application scenario.   # p.1159
evidence: §II.A–B, Algorithms 1–3, Fig. 1, p.1159–1162

### posit_adder_multiplier  (role: proposes)
mechanism: The adder extracts both posit operands, compares their magnitudes, aligns the smaller mantissa with a dynamic right shift, performs mantissa addition/subtraction, normalizes with LOD and a dynamic left shift, recomputes the regime/exponent, and truncates during packing. The multiplier multiplies the extracted mantissas, detects a one-bit overflow, adds the combined regime/exponent values, and uses the same packing flow. Negative posits are converted to magnitude by two's complement while the sign is processed separately. # p.1160–1162
choices:
  es_bits: parameter ES, generated for any desired value [outside domain]   # p.1162
  regime_decode: lzc_plus_shifter   # p.1160–1161
  internal_representation: sign_magnitude   # p.1160–1161
new_choices:
  rounding: round_to_zero_truncation — the adder's final packed result is truncated rather than incremented.   # p.1161
slots:
  sig_datapath: UNKNOWN   # p.1161
parameters: N = 8, 16, 24, 32, 50, 64; RS = log2(N); ES varied in Figs. 1–2; single-cycle implementation; two register levels are placed at the input/output ports.   # p.1161–1162
results:
| metric | value | unit | technology / device | baseline | condition | page |
| latency | 1 | cycle | Xilinx Virtex-6 FPGA / 2018 | none | parameterized posit adder/subtractor and multiplier | p.1162 |
errors_and_checks: Functional outputs are verified against the developers' Julia posit package; the maximum error/ulp behavior of round-to-zero truncation is UNKNOWN.   # p.1161–1162
conditions: The multiplier uses logic rather than DSP48 IPs so Fig. 2 reflects logic resource variation. The input/output registers add resources that are not attributed to the arithmetic logic.   # p.1162
evidence: §II.C–D, Algorithms 4–5, Fig. 2, p.1161–1162

### barrel_mux_tree  (role: instantiates)
mechanism: A parameterized dynamic shifter contains S = log2(N) stages. Each stage uses an N-bit 2:1 multiplexer controlled by one shift-amount bit and shifts by 2^i positions. Algorithm 2 defines the left shifter, and the right shifter is generated similarly. # p.1160
choices:
  stage_radix: 2   # p.1160
  select_encoding: binary   # p.1160
  direction_handling: mirrored_datapath   # p.1160
  stage_order: small_shift_first   # p.1160
new_choices:
  none
slots:
  none
parameters: word width N; shift-amount width S = log2(N); S stages of N-bit 2:1 multiplexers.   # p.1160
results: none
errors_and_checks: none
conditions: The shifters handle runtime movement caused by variable-length posit regime fields and mantissa alignment/normalization.   # p.1160–1161
evidence: Algorithm 2 and §II.A–C, p.1160–1161

### lzd_cell_tree  (role: instantiates)
mechanism: Parameterized LOD and LZD modules use a hierarchical recursion. A two-bit block produces a valid flag and position bit; larger widths recursively process lower and upper halves and select the upper position when its valid flag is asserted. Non-power-of-two inputs are padded to the next power of two. # p.1160
choices:
  block_primitive: pair_cell   # p.1160
  formulation: hierarchical_valid_position   # p.1160
new_choices:
  detection_target: leading_zero_or_one — the same generator structure supports both LZD and LOD with different two-bit cells.   # p.1160
slots:
  none
parameters: input width N; position width S = log2(N).   # p.1160
results: none
errors_and_checks: none
conditions: LOD supports FP subnormal normalization and posit negative-regime decoding; LZD supports positive-regime decoding and adder normalization.   # p.1160–1161
evidence: Algorithm 2 and §II.A–C, p.1160–1161

## new_families
none

## space_gaps
* posit_adder_multiplier lacks a mantissa-multiplier slot even though the proposed posit multiplier contains an integer mantissa multiplier. # p.1161–1162
* posit_adder_multiplier lacks a final-rounding choice, while the proposed adder fixes round-to-zero truncation. # p.1161
* posit_adder_multiplier limits es_bits to 0–3, while the generator accepts arbitrary ES and the implementation plots include ES values above 3. # p.1162
* lzd_cell_tree lacks a choice that distinguishes leading-zero detection from the structurally matched leading-one detector used throughout this design. # p.1160

## open_questions
* The exact slice counts and period values in Figs. 1–2 are not numerically labeled in the supplied document text, so the merge pass must not estimate datapoints from the plots. # p.1162
* The paper identifies the mantissa components only as an N-bit add/sub unit and an integer multiplier, so their internal adder/multiplier families remain UNKNOWN. # p.1161–1162
