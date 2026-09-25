---
handle: dedinechin_2019b
citation: F. de Dinechin, L. Forget, J.-M. Muller, Y. Uguen, "Posits: The Good, the Bad and the Ugly", Conference for Next Generation Arithmetic (CoNGA), 2019
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_SFU, VEC_DOT_ACC]
formats: [posit8_0, posit16_1, posit32_2, posit64_3, fp16, fp32, fp64]
authority: survey
pages_read: 10 / 10
---

## summary
The paper analyzes posit arithmetic properties, standalone posit operators, quire hardware, and posit/IEEE conversion hardware. Posit addition retains several accuracy-enhancing properties, while posit multiplication loses exact-product properties and variable relative precision complicates numerical analysis (§3–5, pp.3–7). FPGA synthesis supports using posits as storage formats with wider IEEE arithmetic between boundary converters (pp.8–9).

## families
### posit_adder_multiplier  (role: analyzes)
mechanism: A standalone posit operator decodes each operand into a custom floating-point representation, performs one unrounded custom floating-point operation, and converts the exact intermediate result back to a posit with the only rounding step. The custom representation may use simpler exponent/significand encodings, redundant significands, and no subnormal handling. Leading-digit counters and shifts in the converters replace IEEE special-case overhead, while the wider internal significand increases multiplier cost.
choices:
  es_bits: Posit8=0, Posit16=1, Posit32=2, Posit64=3   # pp.2,7
  regime_decode: lzc_plus_shifter   # pp.7–8
  approximation: none   # pp.7–8
new_choices:
  operator_structure: decode_custom_fp_encode — operands are decoded to a custom FP format around the arithmetic core   # pp.7–8
  internal_rounding: output_converter_only — rounding is removed from the arithmetic core and performed once during FP-to-posit conversion   # p.7
slots:
  sig_datapath: UNKNOWN
parameters: Posit8/16/32/64; custom FP (wE,wF)=(4,5)/(6,12)/(8,27)/(10,58); standalone add/mul/div/sqrt architecture discussed   # pp.7–8
results: none
errors_and_checks: The posit standard mandates correctly rounded results; the standalone structure performs one rounding in the output converter (pp.2,7).
conditions: Posit and IEEE-float operators have comparable area and latency at similar implementation effort, according to the cited comparison (p.7). Posit multiplication pays for a slightly wider internal format (p.7). Hardware speculation or dual-path adder structures can reduce latency at increased hardware cost (p.7).
evidence: §6.1; Table 2; Figure 2

### posit_quire_mac  (role: analyzes)
mechanism: The quire is a Kulisch-like exact accumulator for sums and differences of exact posit products. The interchange format is wide, and quire-to-posit conversion requires leading-digit counting/shifting across half the quire plus a comparably wide XOR for correct rounding. High-frequency accumulation may retain delayed carries in a redundant representation, which adds carry-propagation work before conversion.
choices:
  quire_width_bits: Posit8=32 [outside domain], Posit16=128, Posit32=512, Posit64=2048 [outside domain]   # p.7
  op_set: fused_ops_general   # p.8
new_choices:
  none
slots:
  none
parameters: wq=32/128/512/2048 bits; wl=16/64/256/1024 bits; wr=12/72/332/1429 bits for Posit8/16/32/64; one-cycle pipelined product accumulation is possible   # pp.7–8
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area | more than 4x | relative area | FPGA, device UNKNOWN, 2019 | posit adder plus posit multiplier | sum of two Posit32 products in hardware quire | p.8 |
| latency | more than 8x | relative latency | FPGA, device UNKNOWN, 2019 | posit adder plus posit multiplier | sum of two Posit32 products in hardware quire | p.8 |
errors_and_checks: The fused-operation contract is an exact sum/difference of exact products followed by posit rounding (p.8).
conditions: Large dot products can amortize a few cycles of conversion latency (p.8). Small sums of products/range reduction/polynomial evaluation may favor other accuracy-enhancing techniques because quire conversion is wide and costly (p.8).
evidence: §6.2; Table 2

### posit_ieee_interop  (role: proposes)
mechanism: Posits serve as storage formats and are decoded at memory boundaries into wider IEEE formats for internal computation. Posit8/Posit16 map exactly into FP32, and Posit32 maps exactly into FP64. Boundary conversion retains posit memory-density benefits while permitting established IEEE arithmetic and libraries.
choices:
  interop_style: boundary_converters   # p.9
  conversion_direction: bidirectional   # p.9
  quire_present: false   # p.9
new_choices:
  none
slots:
  none
parameters: Posit8↔FP32, Posit16↔FP32, Posit32↔FP64; Kintex-7 xc7k160tfbg484-1; Vivado HLS/Vivado v2016.3   # p.9
results:
| metric | value | unit | technology / device | baseline | condition | page |
| Posit8-to-FP32 implementation | 25 / 28 / 0 / 5 @ 546MHz | LUTs / Reg. / DSPs / Cycles @ Freq | Kintex-7 xc7k160tfbg484-1, 2019 | FP32 operators in Table 3 | Vivado v2016.3 | p.9 |
| FP32-to-Posit8 implementation | 20 / 30 / 0 / 3 @ 508MHz | LUTs / Reg. / DSPs / Cycles @ Freq | Kintex-7 xc7k160tfbg484-1, 2019 | FP32 operators in Table 3 | Vivado v2016.3 | p.9 |
| Posit16-to-FP32 implementation | 90 / 72 / 0 / 6 @ 498MHz | LUTs / Reg. / DSPs / Cycles @ Freq | Kintex-7 xc7k160tfbg484-1, 2019 | FP32 operators in Table 3 | Vivado v2016.3 | p.9 |
| FP32-to-Posit16 implementation | 63 / 56 / 0 / 4 @ 742MHz | LUTs / Reg. / DSPs / Cycles @ Freq | Kintex-7 xc7k160tfbg484-1, 2019 | FP32 operators in Table 3 | Vivado v2016.3 | p.9 |
| FP32 ADD baseline | 367 / 618 / 0 / 12 @ 511MHz | LUTs / Reg. / DSPs / Cycles @ Freq | Kintex-7 xc7k160tfbg484-1, 2019 | none | Vivado v2016.3 | p.9 |
| FP32 MUL baseline | 83 / 193 / 3 / 8 @ 504MHz | LUTs / Reg. / DSPs / Cycles @ Freq | Kintex-7 xc7k160tfbg484-1, 2019 | none | Vivado v2016.3 | p.9 |
| FP32 DIV baseline | 798 / 1446 / 0 / 30 @ 438MHz | LUTs / Reg. / DSPs / Cycles @ Freq | Kintex-7 xc7k160tfbg484-1, 2019 | none | Vivado v2016.3 | p.9 |
| FP32 SQRT baseline | 458 / 810 / 0 / 28 @ 429MHz | LUTs / Reg. / DSPs / Cycles @ Freq | Kintex-7 xc7k160tfbg484-1, 2019 | none | Vivado v2016.3 | p.9 |
| Posit32-to-FP64 implementation | 192 / 174 / 0 / 8 @ 473MHz | LUTs / Reg. / DSPs / Cycles @ Freq | Kintex-7 xc7k160tfbg484-1, 2019 | FP64 operators in Table 3 | Vivado v2016.3 | p.9 |
| FP64-to-Posit32 implementation | 139 / 106 / 0 / 4 @ 498MHz | LUTs / Reg. / DSPs / Cycles @ Freq | Kintex-7 xc7k160tfbg484-1, 2019 | FP64 operators in Table 3 | Vivado v2016.3 | p.9 |
| FP64 ADD baseline | 654 / 1035 / 3 / 15 @ 363MHz | LUTs / Reg. / DSPs / Cycles @ Freq | Kintex-7 xc7k160tfbg484-1, 2019 | none | Vivado v2016.3 | p.9 |
| FP64 MUL baseline | 203 / 636 / 11 / 18 @ 346MHz | LUTs / Reg. / DSPs / Cycles @ Freq | Kintex-7 xc7k160tfbg484-1, 2019 | none | Vivado v2016.3 | p.9 |
| FP64 DIV baseline | 3283 / 6167 / 0 / 59 @ 367MHz | LUTs / Reg. / DSPs / Cycles @ Freq | Kintex-7 xc7k160tfbg484-1, 2019 | none | Vivado v2016.3 | p.9 |
| FP64 SQRT baseline | 1771 / 3353 / 0 / 59 @ 388MHz | LUTs / Reg. / DSPs / Cycles @ Freq | Kintex-7 xc7k160tfbg484-1, 2019 | none | Vivado v2016.3 | p.9 |
errors_and_checks: Exact input conversion does not guarantee standard posit-operation results because conversion back after IEEE computation may cause double rounding (p.9).
conditions: Converter area/latency remains below that of the wrapped FP operators and can be amortized across complete FP pipelines (p.9). FP subnormals convert to the smallest posit, while posits never decode as FP subnormals (p.9).
evidence: §6.3; Figures 3–4; Table 3

### correct_rounding_strategy  (role: analyzes)
mechanism: Correctly rounded elementary functions use a two-phase evaluation. A first evaluation carries 7 to 10 extra bits and normally rounds correctly; detected hard-to-round cases trigger a higher-precision evaluation using a higher-degree polynomial. Posit implementations can use quire evaluation, but repeated polynomial multiplication requires extracting extended values from the quire.
choices:
  strategy: ziv_two_phase_retry   # p.2
  rounding_modes_covered: nearest_only   # pp.2–3
new_choices:
  none
slots:
  none
parameters: first phase uses 7 to 10 extra bits; rare accurate phase may require about 150 bits for FP64, almost three times target precision   # p.2
results: none
errors_and_checks: The target is correct rounding; hard-to-round cases are detected before the expensive retry (p.2).
conditions: Posit8/Posit16 functions may favor tabulation (p.2). Larger formats require evaluated approximations, and quire extraction can make direct two-posit Cody-Waite-style range reduction more efficient (pp.2–3).
evidence: §2

## new_families
none

## space_gaps
* `posit_quire_mac.quire_width_bits` excludes the standard 32-bit Posit8 quire and 2048-bit Posit64 quire reported in Table 2 (p.7).
* `posit_adder_multiplier` lacks choices for the decode/custom-FP-operation/encode structure and output-only rounding used by standalone posit operators (pp.7–8).

## open_questions
* The posit standard does not completely specify the quire implementation (p.8).
* The internal custom-FP exponent/significand encodings remain implementation choices (p.7).
* Whether storage-only posit arithmetic can avoid incorrect double rounding remains unstudied (p.9).
