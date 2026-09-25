---
handle: suzuki_1996
citation: H. Suzuki, H. Morinaka, H. Makino, Y. Nakase, K. Mashiko, T. Sumi, "Leading-Zero Anticipatory Logic for High-Speed Floating Point Addition", IEEE Journal of Solid-State Circuits, 1996
actual_citation: H. Suzuki, Y. Nakase, H. Makino, H. Morinaka, K. Mashiko, "Leading-zero Anticipatory Logic for High-speed Floating Point Addition", IEEE 1995 Custom Integrated Circuits Conference, 1995
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: ["IEEE 754 binary floating-point"]
authority: incremental
pages_read: 589-592 / 4
---

## summary
The document proposes leading-zero anticipatory logic that pre-decodes the normalization shift concurrently with significand addition and performs normalization shifting in parallel with rounding. A five-stage 56-bit FADD core fabricated in 0.5μm triple-metal CMOS operates at 160MHz with a reported 1.8% transistor-count penalty.

## families
### single_path  (role: instantiates)
mechanism: A five-stage FADD pipeline compares exponents, swaps and aligns significands, forms an absolute significand result, performs 56-bit addition concurrently with leading-zero pre-decoding, and then performs normalization shifting concurrently with rounding. A final small shift and exponent increment correct the possible one-bit anticipation error and the shift caused by rounding. # pp.589-592
choices:
  pipeline_depth: 5   # p.591
  post_round_renorm: true   # pp.591-592
new_choices:
  none
slots:
  sig_adder: UNKNOWN   # p.591
  round: increment_adder   # p.591
  exp: exponent_path   # pp.591-592
  subnormal: UNKNOWN   # pp.589-592
  align: full_align   # pp.589-591
  norm: coarse_fine   # pp.589, 591-592
parameters: 56-bit significand addition; five execution-pipeline stages; one result per pipeline cycle after filling   # pp.591-592
results:
| metric | value | unit | technology / device | baseline | condition | page |
| clock rate | 160 | MHz | 0.5μm triple-metal CMOS (1995) | none | VDD = 3.3V; room temperature | p.592 |
| cycle time | 6.1 | ns | 0.5μm triple-metal CMOS (1995) | none | VDD = 3.3V; room temperature | p.592 |
| clock rate | 125 | MHz | 0.5μm triple-metal CMOS (1995) | none | VDD = 2.5V | p.592 |
| transistor count | 54k | transistors | 0.5μm triple-metal CMOS (1995) | none | complete FADD core | p.592 |
| die size | 3.5X3.6 | mm | 0.5μm triple-metal CMOS (1995) | none | complete chip | p.592 |
| active area | 2.5X3.5 | mm | 0.5μm triple-metal CMOS (1995) | none | FADD core | p.592 |
errors_and_checks: The anticipated leading-bit position is correct or one bit larger than the sum’s leading-bit position; the final small shifter compensates the one-bit error. # pp.590-592
conditions: Close subtraction makes post-addition leading-zero counting and normalization a dominant delay, so concurrent anticipation reduces the FADD path. The third-stage 56-bit adder limits the cycle time because the LZA logic and LZ counter complete sooner, so the anticipation adds no reported speed penalty. # pp.589, 592
evidence: Fig. 1 and architecture description, pp.589-590; Fig. 4 and pipeline-stage description, pp.591-592; Table 1 and Fig. 6, p.592.

## new_families
### lza  (domain: shift: bit counting, closest: lzd_cell_tree, why_not: lza predicts the normalization position from the adder inputs before the sum exists and permits a bounded one-bit over-anticipation, whereas lzd_cell_tree counts leading zeros from available result bits.)
mechanism: The LZA receives the aligned significands after operand-order selection and complement preparation. Each bit produces an anticipation signal from equality of the two current input bits and the OR of the next-lower input bits. The bitwise signals feed a leading-zero counter before significand addition completes. The prediction can precede the true leading bit by one position, so a small later shifter corrects the result. Sign-bit extension also supplies an unshift indication for positive addition. # pp.590-591
choices:
  prediction_source: {aligned_significands_before_sum}
  prediction_error: {exact_or_one_bit_early}
  correction_placement: {post_round_small_shift}
  circuit_style: {conventional_cmos}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| LZA circuit size | 884 | transistors | 0.5μm triple-metal CMOS (1995) | none | 56-bit FADD implementation | p.592 |
| LZ counter size | 696 | transistors | 0.5μm triple-metal CMOS (1995) | none | 56-bit FADD implementation | p.592 |
| total anticipation size | 2122 | transistors | 0.5μm triple-metal CMOS (1995) | conventional leading-zero comparator requiring 12226 transistors for 114-bit data | includes the small correction shifter; reported as 1/3 of the conventional circuit | p.592 |
| transistor-count penalty | 1.8 | % | 0.5μm triple-metal CMOS (1995) | complete FADD | LZA/LZ counter/correction implementation | p.592 |
| per-bit LZA size | 16 | transistors | 0.5μm triple-metal CMOS (1995) | none | three gate stages using conventional CMOS gates | p.591 |
evidence: Boolean expression and examples in Fig. 2, p.590; CMOS implementation in Fig. 3, p.591; area/delay discussion, pp.591-592.

## space_gaps
* The FP near-leading-zero slots name `lza`, but the vocabulary lacks an `lza` family that records operand-based prediction, bounded one-bit over-anticipation, and correction placement. # pp.590-592
* The `single_path` family lacks a choice for overlapping normalization shifting with rounding. # pp.589-592

## open_questions
* The document specifies a 56-bit significand adder but does not identify the supported IEEE 754 precision or precisions.
* The document does not identify the 56-bit significand adder topology or circuit family.
* The document does not state subnormal handling, supported rounding modes, or exception behavior.
