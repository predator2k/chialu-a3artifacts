---
handle: hsiao_2014
citation: S.-F. Hsiao, C.-S. Wen, P.-H. Wu, "Compression of Lookup Table for Piecewise Polynomial Function Evaluation", Euromicro Conference on Digital System Design (DSD), pp. 279-284, 2014
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_SFU]
formats: [fixed16, fixed24]
authority: incremental
pages_read: 279-284 / 6 pages
---

## summary
The paper proposes a lossless compression method for the zero-order coefficient table in piecewise polynomial function evaluators. The method stores one representative coefficient per group and a narrow table of differences, reducing T0 storage by up to 18.8% in the reported experiments without changing the original error.

## families
### compressed_lut  (role: proposes)
mechanism: The original zero-order coefficient table T0^(a,w) is decomposed into T0new^(a′,w) and T0diff^(a,w′). T0new stores one representative value near the midpoint of each group of 2^(a-a′) contiguous entries. T0diff stores the difference between each original entry and its group representative. The original coefficient is recovered by addition, while w′ is usually smaller than w. An exhaustive search over a′ minimizes 2^a′×w + 2^a×w′. # p.281-282
choices:
new_choices:
  decomposition: representative_plus_difference — one full-width representative per group plus per-entry narrow differences # p.281
  representative_selection: near_group_midpoint — the stored initial value is selected near the midpoint of each group # p.282
  compression_contract: lossless — addition of T0new and T0diff completely recovers T0 # p.281, p.283
  optimization_objective: minimum_total_table_bits — all a′ values are searched using 2^a′×w + 2^a×w′ # p.282
slots: none
parameters: T0^(a,w), T0new^(a′,w), T0diff^(a,w′), a′=a-s, groups of 2^s entries; tested at 16-bit and 24-bit accuracy with degree-one and degree-two PPA # p.281-284
results:
| metric | value | unit | technology / device | baseline | condition | page |
| T0 storage | 4,160 | bits | UNKNOWN / 2014 | 5,120 bits | RCP, uniform, 16-bit, degree 1; saving 18.8% | p.284 |
| T0 storage | 3,432 | bits | UNKNOWN / 2014 | 3,712 bits | RCP, uniform, 24-bit, degree 2; saving 7.5% | p.284 |
| T0 storage | 2,208 | bits | UNKNOWN / 2014 | 2,560 bits | SIN, uniform, 16-bit, degree 1; saving 13.8% | p.284 |
| T0 storage | 3,432 | bits | UNKNOWN / 2014 | 3,712 bits | SIN, uniform, 24-bit, degree 2; saving 7.5% | p.284 |
| T0 storage | 2,472 | bits | UNKNOWN / 2014 | 2,688 bits | POW2, uniform, 16-bit, degree 1; saving 8.0% | p.284 |
| T0 storage | 1,912 | bits | UNKNOWN / 2014 | 1,920 bits | POW2, uniform, 24-bit, degree 2; saving 0.4% | p.284 |
| T0 storage | 2,918 | bits | UNKNOWN / 2014 | 3,220 bits | RCP, non-uniform, 16-bit, degree 1; saving 9.4% | p.284 |
| T0 storage | 3,054 | bits | UNKNOWN / 2014 | 3,240 bits | RCP, non-uniform, 24-bit, degree 2; saving 5.7% | p.284 |
| T0 storage | 1,890 | bits | UNKNOWN / 2014 | 2,200 bits | SIN, non-uniform, 16-bit, degree 1; saving 14% | p.284 |
| T0 storage | 3,110 | bits | UNKNOWN / 2014 | 3,300 bits | SIN, non-uniform, 24-bit, degree 2; saving 5.8% | p.284 |
| T0 storage | 2,472 | bits | UNKNOWN / 2014 | 2,688 bits | POW2, non-uniform, 16-bit, degree 1; saving 8.0% | p.284 |
| T0 storage | 1,912 | bits | UNKNOWN / 2014 | 1,920 bits | POW2, non-uniform, 24-bit, degree 2; saving 0.4% | p.284 |
| T0 storage | 141,824 | bits | UNKNOWN / 2014 | 172,032 bits | special function from [8], uniform, 16-bit, degree 1; saving 17.6% | p.284 |
| T0 storage | 815,104 | bits | UNKNOWN / 2014 | 983,040 bits | special function from [8], uniform, 24-bit, degree 2; saving 17.1% | p.284 |
| T0 storage | 23,942 | bits | UNKNOWN / 2014 | 26,580 bits | special function from [8], non-uniform, 16-bit, degree 1; saving 9.9% | p.284 |
| T0 storage | 31,872 | bits | UNKNOWN / 2014 | 32,310 bits | special function from [8], non-uniform, 24-bit, degree 2; saving 1.4% | p.284 |
errors_and_checks: The decomposition introduces no additional error or rounding error because T0 is completely recovered; the original PPA error requirement remains applicable. # p.281, p.283
conditions: Compression is effective when T0 has wider entries than T1/T2 and adjacent T0 coefficients have differences representable with w′<w. The extra input to the final multi-operand adder has negligible reported worst-case-delay impact because the critical path includes the squarer/multiplier/final adder. Savings are only 0.4% for 24-bit POW2. # p.281, p.283-284
evidence: §III-IV; Fig. 3-7; Tables 1 and 3-5, p.281-284

### piecewise_poly  (role: extends)
mechanism: The evaluator partitions the input interval into uniform or non-uniform segments and stores quantized per-segment coefficients for degree-one or degree-two polynomials. Uniform segmentation indexes coefficients with the input MSBs. Non-uniform segmentation uses address remapping and may bypass MSBs into the local polynomial argument. The proposed compression changes only T0 storage and adds one input to the final multi-operand adder. # p.279-283
choices:
  degree: 1, 2 # p.279-280, p.282-284
  basis: minimax_remez # p.282-283
  rounding_contract: total_error_below_1_ulp [outside domain] # p.280, p.282
new_choices:
  zero_order_coefficient_compression: representative_plus_difference — T0 is replaced by losslessly recombined T0new/T0diff tables # p.281-283
slots:
  segmenter: uniform_high_bit_decode # p.280
  segmenter: nonuniform # p.280-283
parameters: RCP 1/x on [1,2], SIN on [0,π/4], and POW2 2^x on [0,1]; 16-bit and 24-bit accuracy; degree 1 and degree 2; total error εtotal=εapx+εq+εtr+εrnd<2^-n # p.280, p.282
results:
| metric | value | unit | technology / device | baseline | condition | page |
| coefficient wordlengths | 26, 16, 10 | bits | UNKNOWN / 2014 | none | 24-bit reciprocal, degree 2, p̂0/p̂1/p̂2; T0 is 50% of total table size | p.281 |
errors_and_checks: The stated accuracy contract is εtotal<1 ulp, with approximation/quantization/truncation/rounding errors budgeted separately. # p.280
conditions: Degree-one approximation is reported as preferable for the tested 16-bit cases, while degree-two approximation is reported as more suitable for 24-bit cases. Non-uniform segmentation benefits highly nonlinear functions but gives no additional saving over uniform segmentation for POW2. # p.283
evidence: §II, §IV-V; Fig. 1-2 and 6-10; Tables 2-5, p.279-284

## new_families
none

## space_gaps
* piecewise_poly lacks a coefficient-table slot through which compressed_lut could fill T0 storage. # p.281-283
* compressed_lut lacks choices for representative-plus-difference decomposition, representative selection, losslessness, and table-bit optimization. # p.281-282

## open_questions
* The implementation technology/device and circuit area/power are not reported.
* The SIN optimization example is internally inconsistent: Table 1 minimizes SIN storage at a′=3 with 128 original entries, while the accompanying text states a=8 and groups of 16 entries, which imply a′=4. # p.282
