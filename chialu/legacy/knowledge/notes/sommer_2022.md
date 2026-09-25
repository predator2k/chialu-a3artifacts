---
handle: sommer_2022
citation: J. Sommer, M. A. Özkan, O. Keszocze, J. Teich, "DSP-Packing: Squeezing Low-Precision Arithmetic into FPGA DSP Blocks", International Conference on Field-Programmable Logic and Applications (FPL), 2022
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_DOT_ACC]
formats: [int4, int6, int8, int9, int10]
authority: incremental
pages_read: 1-7 / 7
---

## summary
The paper generalizes bit-offset packing so one FPGA DSP multiplier computes an outer product of arbitrary-width integer vectors, analyzes the packing error, and proposes full/approximate correction. MR-Overpacking deliberately overlaps results and restores corrupted MSBs, which permits six int4 multiplications per DSP48E2. Addition packing maps several narrow additions onto the 48-bit accumulator with optional guard bits.

## families
### dsp48_style_slice  (role: instantiates)
mechanism: The Xilinx DSP48E2 computes `P = B × (A + D) + C + Pin` with a 27-bit preadder, an 18 × 27-bit multiplier, a 48-bit accumulator, and result-cascade ports. Packed operands enter the multiplier ports, while correction terms can enter through `C`. # p.1, p.3
choices:
  mult_shape: 27x18   # p.1
  pre_adder: true   # p.1
  alu_width: 48   # p.1
  cascade_paths: result_only   # p.2
new_choices:
  none
slots:
  none
parameters: 27-bit preadder; 18 × 27-bit multiplier; 48-bit accumulator; one packed multiplication per clock cycle   # p.1
results:
| metric | value | unit | technology / device | baseline | condition | page |
| packing capacity | 5 | 9-bit additions/DSP | Xilinx Zynq UltraScale+ MPSoC XCZU7EV-2FFVC1156; 2022 | none | three guard-bit positions remain | p.5 |
errors_and_checks: The hardware experiments exhaustively test all possible input combinations and report EP/MAE/WCE.   # p.5
conditions: The packing capacity is restricted by the DSP input/output widths and ports.   # p.2, p.6
evidence: Fig. 1, §III, §VIII

## new_families
### dsp_multiplier_packing  (domain: dsp: FPGA DSP blocks, closest: variable_precision_dsp, why_not: `variable_precision_dsp` selects native fractured widths, while this mechanism packs offset operands into one conventional hard multiplier.)
mechanism: INT-N forms two packed integers from vectors `a` and `w`; their product contains the outer product `a·wᵀ` at offsets `roff,j·|aoff|+i = aoff,i + woff,j`. Standard packing separates results with padding `δ`. Full correction applies Round-Half-Up after extraction, while approximate correction anticipates rounding from operand signs through the DSP accumulator. Overpacking uses negative `δ`, which overlaps results. MR-Overpacking calculates the contaminating product LSBs and subtracts them to restore corrupted MSBs. # p.2-p.5
choices:
  packing_mode: {int_n, overpacking, mr_overpacking}   # p.2-p.4
  padding_delta: Int[-3..3:1]   # p.2-p.6
  rounding_correction: {none, round_half_up_full, accumulator_sign_approximate}   # p.3-p.4
  overlap_correction: {none, msb_restoring}   # p.4-p.5
  element_widths: per_element_integer_widths   # p.2
  operand_signedness: {a_unsigned_w_signed}   # p.2-p.3
results:
| metric | value | unit | technology / device | baseline | condition | page |
| MAE / EP / WCE / LUTs / FFs | 0.37 / 37.35% / 1 / 0 / 0 | mixed | XCZU7EV-2FFVC1156; 2022 | none | Xilinx INT4; int4; four multiplications | p.6 |
| MAE / EP / WCE / LUTs / FFs | 0.00 / 0.00% / 0 / 27 / 32 | mixed | XCZU7EV-2FFVC1156; 2022 | Xilinx INT4 | full correction; int4; four multiplications | p.6 |
| MAE / EP / WCE / LUTs / FFs | 0.02 / 3.13% / 1 / 0 / 0 | mixed | XCZU7EV-2FFVC1156; 2022 | Xilinx INT4 | approximate correction; int4; four multiplications | p.6 |
| MAE / EP / WCE / LUTs / FFs | 24.27 / 49.85% / 129 / 0 / 0 | mixed | XCZU7EV-2FFVC1156; 2022 | Xilinx INT4 | Overpacking `δ = −1` | p.6 |
| MAE / EP / WCE / LUTs / FFs | 37.95 / 58.64% / 194 / 0 / 0 | mixed | XCZU7EV-2FFVC1156; 2022 | Xilinx INT4 | Overpacking `δ = −2` | p.6 |
| MAE / EP / WCE / LUTs / FFs | 45.53 / 78.26% / 228 / 0 / 0 | mixed | XCZU7EV-2FFVC1156; 2022 | Xilinx INT4 | Overpacking `δ = −3` | p.6 |
| MAE / EP / WCE / LUTs / FFs | 0.37 / 37.35% / 1 / 4 / 6 | mixed | XCZU7EV-2FFVC1156; 2022 | Xilinx INT4 | MR-Overpacking `δ = −1` | p.6 |
| MAE / EP / WCE / LUTs / FFs | 0.47 / 41.48% / 2 / 6 / 20 | mixed | XCZU7EV-2FFVC1156; 2022 | Xilinx INT4 | MR-Overpacking `δ = −2` | p.6 |
| MAE / EP / WCE / LUTs / FFs | 0.78 / 49.95% / 4 / 17 / 30 | mixed | XCZU7EV-2FFVC1156; 2022 | Xilinx INT4 | MR-Overpacking `δ = −3` | p.6 |
| packing density `ρ` | 1.13 | ratio | XCZU7EV-2FFVC1156; 2022 | none | Overpacking | p.6 |
| packing density `ρ` | 0.88 | ratio | XCZU7EV-2FFVC1156; 2022 | none | INT-N | p.6 |
| packing density `ρ` | 0.67 | ratio | XCZU7EV-2FFVC1156; 2022 | none | INT8 packing | p.6 |
| packing density `ρ` | 0.67 | ratio | XCZU7EV-2FFVC1156; 2022 | none | INT4 packing | p.6 |
| packing density `ρ` | 0.56 | ratio | XCZU7EV-2FFVC1156; 2022 | none | Huang et al. | p.6 |
| packed multiplications | 6 | int4 multiplications/DSP | XCZU7EV-2FFVC1156; 2022 | 4 with INT4 packing | MR-Overpacking; MAE = 0.37 | p.6 |
| packed multiplications | 4 | int6 multiplications/DSP | XCZU7EV-2FFVC1156; 2022 | 4 int4 multiplications | MR-Overpacking `δ = −2`; 50% precision increase | p.6 |
evidence: Eq. 4, Fig. 3-Fig. 6, Table I, Table II, Fig. 9, §IV-§VI, §VIII-§IX

### dsp_accumulator_addition_packing  (domain: dsp: FPGA DSP blocks, closest: dsp48_style_slice, why_not: `dsp48_style_slice` does not describe multiple independently extracted narrow additions or carry-isolating guard bits.)
mechanism: Several additions occupy disjoint fields of one wide accumulator addition. A carry from a lower field can corrupt only the least-significant bit of the next field, which bounds absolute error to 1. A zero guard bit between fields catches the carry and makes the adjacent packed additions exact. Mixed 9-bit/10-bit fields can consume the full 48-bit accumulator without guards. # p.5
choices:
  packed_additions: Int[2..5:1]   # p.5
  lane_width_bits: Int[8..10:1]   # p.5
  guard_between_additions: Bool   # p.5
  mixed_lane_widths: Bool   # p.5
results:
| metric | value | unit | technology / device | baseline | condition | page |
| MAE / EP / WCE / LUTs / FFs | 0.51 / 51.83% / 1 / 0 / 0 | mixed | XCZU7EV-2FFVC1156; 2022 | none | one unguarded 9-bit adder among five packed additions | p.6 |
| packing capacity | 2 and 3 | 9-bit and 10-bit additions/DSP | XCZU7EV-2FFVC1156; 2022 | none | no guard-bit space; five additions total | p.5 |
evidence: Fig. 7, Fig. 8, Table III, §VII-§VIII

## space_gaps
* The DSP vocabulary lacks an outer-product packing family with per-element widths/input offsets/result offsets and signedness constraints. # p.2
* The DSP vocabulary lacks negative-padding Overpacking and MSB-restoring correction choices. # p.3-p.5
* The DSP vocabulary lacks accumulator addition packing with optional carry-isolating guard bits. # p.5

## open_questions
* The document does not establish whether accumulator-based approximate correction can operate simultaneously with packed-result accumulation.
* The document does not report timing, power, frequency, or total DSP utilization beyond one DSP block per packing configuration.
* The document does not evaluate application-level accuracy for CNN or SNN workloads.
