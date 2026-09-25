---
handle: sjalander_2004
citation: M. Sjalander, H. Eriksson, P. Larsson-Edefors, "An Efficient Twin-Precision Multiplier", Proc. IEEE ICCD, pp. 30-33, 2004
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int16, int8]
authority: incremental
pages_read: 4 / 4
---

## summary
The document proposes a twin-precision tree multiplier that performs one N-bit, one N/2-bit, or two parallel N/2-bit multiplications. A signed 16-bit implementation supports one or two signed 8-bit products by partitioning/gating the partial-product matrix and adapting the final adder. # p.1–p.4

## families
### twin_precision_subword  (role: proposes)
mechanism: The N-bit partial products are partitioned between least-significant and most-significant halves of a regular-connectivity reduction tree. Three-input AND gates and two mode-control signals force unused partial products to zero. N/2-bit partial products are placed lower in the tree to shorten their paths. Signed operation uses Baugh-Wooley inversion/correction logic, including NAND-XOR partial-product generation, product-MSB XOR gates, correction ones, and an extra half-adder level for the most-significant N/2-bit product. # p.2–p.3
choices:
  partition: halves   # p.1–p.2
  base_scheme: baugh_wooley   # p.2–p.3
  per_lane_signed: true   # p.3–p.4
new_choices:
  operating_modes: {one_N, one_N_over_2, two_N_over_2} — selects full precision, single reduced precision, or two parallel reduced-precision products   # p.1–p.2
  inactive_partial_product_control: force_zero — gates unused partial products to suppress switching   # p.2, p.4
slots:
  lane_cpa: sparse_prefix_hybrid   # p.3–p.4
parameters: N-bit full-width operands; N/2-bit subword operands; evaluated as one 16-bit, one 8-bit, or two parallel 8-bit signed multiplications; 31-bit final adder; 500 MHz power stimulus; 1.2 V; 25 °C; 50 random input vectors   # p.1, p.3–p.4
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay | 1.52 | normalized | 0.13-µm, 2004 | conventional 8-bit multiplier = 1.0 | 16-bit mode | p.4 |
| power | 4.10 | normalized | 0.13-µm, 2004 | conventional 8-bit multiplier = 1.0 | 16-bit mode | p.4 |
| delay | 9.0% | larger | 0.13-µm, 2004 | conventional 16-bit multiplier | 16-bit mode | p.4 |
| power | 0.9% | larger | 0.13-µm, 2004 | conventional 16-bit multiplier | 16-bit mode | p.4 |
| delay | 1.29 | normalized | 0.13-µm, 2004 | conventional 8-bit multiplier = 1.0 | two parallel 8-bit multiplications | p.4 |
| power | 2.34 | normalized | 0.13-µm, 2004 | conventional 8-bit multiplier = 1.0 | two parallel 8-bit multiplications | p.4 |
| delay | 29.0% | larger | 0.13-µm, 2004 | conventional 8-bit multiplier | two parallel 8-bit multiplications | p.4 |
| power | 16.9% | larger | 0.13-µm, 2004 | conventional 8-bit multipliers | two parallel 8-bit multiplications | p.4 |
| delay | -7.5% | relative | 0.13-µm, 2004 | conventional 16-bit multiplier | two parallel 8-bit multiplications | p.4 |
| power | -42.4% | relative | 0.13-µm, 2004 | conventional 16-bit multiplier | two parallel 8-bit multiplications | p.4 |
| delay | 1.18 | normalized | 0.13-µm, 2004 | conventional 8-bit multiplier = 1.0 | single 8-bit mode | p.4 |
| power | 1.13 | normalized | 0.13-µm, 2004 | conventional 8-bit multiplier = 1.0 | single 8-bit mode | p.4 |
| delay | 18.2% | larger | 0.13-µm, 2004 | conventional 8-bit multiplier | single 8-bit mode | p.4 |
| power | 13.3% | larger | 0.13-µm, 2004 | conventional 8-bit multiplier | single 8-bit mode | p.4 |
| delay | -15.3% | relative | 0.13-µm, 2004 | conventional 16-bit multiplier | single 8-bit mode | p.4 |
| power | -72.1% | relative | 0.13-µm, 2004 | conventional 16-bit multiplier | single 8-bit mode | p.4 |
| transistor count | 8% | higher | 0.13-µm, 2004 | conventional 16-bit multiplier | 16-bit twin-precision implementation | p.4 |
errors_and_checks: Exact signed multiplication is supported with Baugh-Wooley logic; no arithmetic-error or fault-detection evaluation is reported. # p.2–p.4
conditions: The design targets precision-flexible low-power/SIMD operation. Single 8-bit mode holds about two thirds of the multiplier tree at constant zero. The most-significant 8-bit lane has a longer tree/final-adder path than the least-significant lane. Multiplexers that move partial products farther down the tree were rejected because they significantly increase full-width delay. Control-signal distribution power was excluded, and negligible control power assumes modes persist for longer durations. Sleep-mode techniques were not investigated. # p.2, p.4
evidence: §2 and Figures 1–4, p.1–p.3; §3 and Figure 5, p.3; §4 and Tables 1–2, p.3–p.4; §5, p.4

## new_families
none

## space_gaps
* twin_precision_subword lacks a choice for the supported operating-mode set `{one_N, one_N_over_2, two_N_over_2}`. # p.1–p.2
* twin_precision_subword lacks a choice for forcing unused partial products to zero through gated partial-product generation. # p.2, p.4
* twin_precision_subword lacks a reduction-tree slot or choice for the regular-connectivity tree used here. # p.2

## open_questions
* The document calls the adapted final adder a sparse-tree carry-lookahead scheme but does not state its precise topology, sparsity, valency, or fanout. # p.3
* Table 2 does not state explicitly whether the 2x8-bit power comparison against the 8-bit reference uses one or two conventional 8-bit multipliers as its baseline. # p.4
* Modified Booth was evaluated but omitted for space, so its twin-precision implementation details and results remain unknown. # p.2
