---
handle: leon2018b
citation: V. Leon, G. Zervakis, S. Xydis, D. Soudris, K. Pekmestzi, "Walking Through the Energy-Error Pareto Frontier of Approximate Multipliers", IEEE Micro, vol. 38, no. 4, pp. 40-49, 2018
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int16, int24, int32]
authority: incremental
pages_read: 40-49 / 10
---

## summary
The article proposes PR|k,m, which combines least-significant partial-product perforation with operand rounding in signed modified-Booth multipliers. DyPR exposes k and m at runtime and uses a ROM of predetermined MRED values to select configurations. The evaluated PR configurations form the reported energy-MRED Pareto frontier against the examined approximate multipliers.

## families
### booth_recoded_parallel  (role: instantiates)
mechanism: The signed n-bit multiplier forms n/2 modified-Booth digits from consecutive multiplier bits. Each digit belongs to {0, ±1, ±2} and controls one partial product. An accurate Wallace tree accumulates the retained partial products, and a prefix adder adds the carry-save outputs. # p.42-p.43
choices:
  booth_radix: 4   # p.42
  hard_multiple_gen: none   # p.42
new_choices:
  none
slots:
  reduction: csa_reduction_tree   # p.43
  hard_multiple_adder: none
parameters: n-bit 2's-complement operands; n/2 modified-Booth digits; evaluated at n = 16, 24, 32   # p.42-p.45
results:
| metric | value | unit | technology / device | baseline | condition | page |
| --- | --- | --- | --- | --- | --- | --- |
| MRED | up to 0.017 | percent | UNKNOWN; result year 2018 | exact multiplication | n = 24, uniform inputs over the full range | p.43 |
| MRED | up to 0.000052 | percent | UNKNOWN; result year 2018 | exact multiplication | n = 32, uniform inputs over the full range | p.43 |
errors_and_checks: RED = |A × B − A × B|k,m| / |A × B|; MRED is the probability-weighted average of RED. Uniform-input analysis uses pA(A) = pB(B) = 1/2n.   # p.43
conditions: PR|k,m can replace a floating-point mantissa multiplier; the reported approximation leaves the product MSBs and exponent exact while affecting the mantissa.   # p.43
evidence: Modified-Booth equations and partial-product construction on p.42; hybrid accumulation and floating-point applicability on p.43.

### pp_perforation  (role: extends)
mechanism: Perforation omits k successive partial products starting with the least-significant partial product. The omission discards the k least-significant modified-Booth digits, corresponding to the 2k least-significant bits of B including b-1. PR|k,m combines this depth reduction with independent rounding of A. # p.42-p.43
choices:
  perforated_rows: k   # p.42
  cell: exact_and   # p.42
  correction: none   # p.42-p.43
new_choices:
  remaining_pp_width_rounding: m — selects the partial-product bit at which the remaining partial products are rounded   # p.43
slots:
  none
parameters: k ∈ [0, n/2-1); evaluated configurations include k = 1, 2, 3, 4   # p.43,p.45-p.48
results:
| metric | value | unit | technology / device | baseline | condition | page |
| --- | --- | --- | --- | --- | --- | --- |
| energy comparison | lower | qualitative | TSMC 65-nm standard cell library, 1 V; result year 2018 | PERFk at similar error | Adding rounding provides energy savings with only a slight error increase | p.46-p.47 |
errors_and_checks: Perforation can produce bounded but large errors if it is not tuned appropriately.   # p.41
conditions: Perforation reduces accumulation-tree depth, while truncation alone does not significantly reduce critical paths.   # p.41,p.43
evidence: Table 1 on p.41; “Partial Product Perforation” on p.42; comparison discussion on p.46-p.47.

### approximate_booth  (role: compares)
mechanism: The comparison includes radix-8 Booth generation with approximate 3A, radix-4 designs with inexact encoding in least-significant columns, and RADk designs that combine accurate modified-Booth encoding for the multiplicand MSBs with approximate high-radix encoding for the LSBs. # p.46
choices:
  radix: 4, 8, hybrid_high_radix   # p.46
new_choices:
  none
slots:
  none
parameters: R8ABM1; R8ABM1-15; R4ABM1-k7; R4ABM2-k7; RAD64; RAD256; RAD1024   # p.46-p.48
results:
| metric | value | unit | technology / device | baseline | condition | page |
| --- | --- | --- | --- | --- | --- | --- |
| MRED | 0.28 | percent | TSMC 65-nm standard cell library, 1 V; result year 2018 | exact CMB | RAD256 | p.47 |
errors_and_checks: R4ABM1 generates its least-significant partial products more accurately than R4ABM2.   # p.46
conditions: The radix designs have small errors but worse energy consumption and delay than comparable PR configurations; PR|2,4 has lower energy and MRED than RAD256.   # p.46-p.47
evidence: State-of-the-art descriptions on p.46; Table 2 and Figure 5 on p.47-p.48.

### truncated_fixed_width  (role: compares)
mechanism: TMCk truncates k least-significant columns of the partial-product tree and adds correction terms to reduce the resulting error. # p.46
choices:
  correction: constant   # p.46,p.48
  target: multiplier   # p.46
new_choices:
  none
slots:
  none
parameters: TMC8 and TMC15   # p.47-p.48
results:
| metric | value | unit | technology / device | baseline | condition | page |
| --- | --- | --- | --- | --- | --- | --- |
errors_and_checks: none
conditions: Truncation eliminates least-significant partial-product columns but does not significantly reduce critical paths.   # p.41
evidence: Table 1 on p.41; comparison description on p.46; Figure 5 on p.48.

### dynamic_segment  (role: compares)
mechanism: DRUM6 selects a 6-bit segment beginning at the leading one of each operand and sets the least-significant bit of each truncated operand to one. # p.46
choices:
  segment_width: 6   # p.46
  segment_select: dynamic_leading_one   # p.46
  unbiasing: lsb_set_to_one   # p.46
new_choices:
  none
slots:
  none
parameters: DRUM6   # p.46
results:
| metric | value | unit | technology / device | baseline | condition | page |
| --- | --- | --- | --- | --- | --- | --- |
errors_and_checks: none
conditions: DRUM6 provides energy savings but has large standalone-circuit error and worse delay than the accurate CMB.   # p.47
evidence: Comparison description on p.46; Table 2 and Figure 5 on p.47-p.48.

### operand_rounding  (role: compares)
mechanism: RoBA rounds operands to the nearest power of two and implements multiplication in segments with shift operations. # p.46
choices:
  rounding: nearest_pow2   # p.46
new_choices:
  none
slots:
  none
parameters: RoBA   # p.46
results:
| metric | value | unit | technology / device | baseline | condition | page |
| --- | --- | --- | --- | --- | --- | --- |
errors_and_checks: none
conditions: RoBA provides energy savings but has large standalone-circuit error and worse delay than the accurate CMB.   # p.47
evidence: Comparison description on p.46; Table 2 and Figure 5 on p.47-p.48.

### error_analysis_quality  (role: analyzes)
mechanism: The evaluation uses MRED for circuit and FIR/matrix-multiplication accuracy, PRED for the probability that RED is below 2 percent, and false-edge detection percentage for the Sobel benchmark. # p.43,p.45-p.46
choices:
  metric: mred   # p.43
  model: monte_carlo   # p.45
  composition_across_blocks: true   # p.45-p.46
new_choices:
  pred_threshold: RED < 2 percent — probability that an individual relative error is below the stated threshold   # p.46
  false_edges_detected: percentage — Sobel output-quality metric   # p.45
slots:
  none
parameters: 200,000 randomly generated inputs for the 32-tap FIR and 3x3 tiled matrix multiplication; 16-bit image for Sobel   # p.45
results:
| metric | value | unit | technology / device | baseline | condition | page |
| --- | --- | --- | --- | --- | --- | --- |
errors_and_checks: Uniform distributions stress the complete input range; narrower distributions produce more biased MRED values.   # p.43
conditions: FIR output error is larger than matrix-multiplication and Sobel error because each FIR output depends on preceding outputs and propagates error.   # p.46
evidence: Error analysis on p.43; application setup on p.45; Table 2 metric definitions on p.46-p.47.

## new_families
### hybrid_partial_product_perforation_rounding  (domain: approx: approximate multipliers, closest: pp_perforation, why_not: pp_perforation represents omitted rows but not independent rounding that reduces the width of every retained partial product)
mechanism: PR|k,m omits k least-significant modified-Booth partial products and rounds A at bit m before generating the remaining partial products. The rounded value discards the m-1 least-significant bits and adds am-1 to Am. XOR transformations Am* = Am ⊕ am-1 and s*j = sj ⊕ am-1 reuse the conventional modified-Booth generator with one additional XOR-2 gate in the encoder. DyPR gates operand bits with 2n multiplexers and selects k/m from a ROM indexed by permitted MRED. # p.42-p.44
choices:
  perforated_partial_products: Int[0..n/2-1)   # p.43
  rounding_bit_m: Int[0..n-1)   # p.43
  configuration_time: {design_time, runtime}   # p.44
  error_bound_rom: Bool   # p.44
results:
| metric | value | unit | technology / device | baseline | condition | page |
| --- | --- | --- | --- | --- | --- | --- |
| energy saving | up to 69 | percent | TSMC 65-nm standard cell library, 1 V; result year 2018 | accurate designs | design-time PR, n = 16 | p.40,p.45 |
| area saving | up to 64 | percent | TSMC 65-nm standard cell library, 1 V; result year 2018 | accurate designs | design-time PR, n = 16 | p.40,p.45 |
| energy saving | up to 47 | percent | TSMC 65-nm standard cell library, 1 V; result year 2018 | accurate design | runtime DyPR, n = 16 | p.40,p.45 |
| application energy reduction | 42.64 | percent | TSMC 65-nm standard cell library, 1 V; result year 2018 | accurate multiplier | PR|2,2, PR|3,6, and PR|4,6 across FIR/matrix/Sobel evaluations | p.45-p.46 |
| application area reduction | 39.24 | percent | TSMC 65-nm standard cell library, 1 V; result year 2018 | accurate multiplier | PR|2,2, PR|3,6, and PR|4,6 across FIR/matrix/Sobel evaluations | p.45-p.46 |
| application delay reduction | 11.98 | percent | TSMC 65-nm standard cell library, 1 V; result year 2018 | accurate multiplier | PR|2,2, PR|3,6, and PR|4,6 across FIR/matrix/Sobel evaluations | p.45-p.46 |
| MRED | 0.23 | percent | TSMC 65-nm standard cell library, 1 V; result year 2018 | exact CMB | PR|2,4; RAD256 comparison value is 0.28 percent | p.47 |
evidence: Proposed multiplier on p.42-p.43; runtime circuit and ROM on p.44; experimental setup on p.45; Figures 4-5 and Table 2 on p.46-p.48.

## space_gaps
* `pp_perforation` lacks a choice for rounding the width of every retained partial product, which is independently controlled by m in PR|k,m.   # p.43
* `accuracy_configurable` lacks a reconfiguration grain that combines partial-product-row perforation with operand-width rounding.   # p.44
* `csa_reduction_tree` is accepted by slots but has no declared family block for the accurate Wallace tree used here.   # p.43
* `error_analysis_quality` lacks PRED and false-edge-detection metrics used in the comparison and Sobel evaluation.   # p.45-p.46

## open_questions
* Table 2 is embedded without legible cell values in the supplied document text, so its per-design delay/area/energy/MRED/PRED numbers remain untranscribed.
* The printed upper-bound notation for k and m uses half-open expressions `k ∈ [0, n/2-1)` and `m ∈ [0, n-1)`, which should not be converted to integer endpoint bounds without checking the typeset equations.
