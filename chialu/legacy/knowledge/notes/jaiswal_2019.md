---
handle: jaiswal_2019
citation: M. K. Jaiswal, H. K.-H. So, "PACoGen: A Hardware Posit Arithmetic Core Generator", IEEE Access, 2019
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [posit(N,ES), posit8, posit16, posit32_6]
authority: incremental
pages_read: 74586-74601 / 16
---

## summary
PACoGen generates parameterized Verilog HDL for posit addition/subtraction, multiplication, and Newton-Raphson division for a supplied word size N and exponent size ES. The paper also implements pipelined posit(32,6) architectures on Virtex-7 and single-cycle generated cores on Virtex-7 and Nangate 15 nm.

## families
### posit_adder_multiplier  (role: proposes)
mechanism: Both operations extract the sign/run-length regime/exponent/variable-width mantissa, perform the core arithmetic, reconstruct the regime/exponent/mantissa sequence, and round to nearest even (pp.74588-74593). Addition aligns the smaller mantissa by the effective exponent difference, adds or subtracts the mantissas, normalizes with leading-one detection, and adjusts the combined regime/exponent (pp.74590-74592). Multiplication multiplies two unsigned mantissas and adjusts the combined exponent for product normalization (p.74593).
choices:
  es_bits: 6 [outside domain]   # p.74594
  regime_decode: ones_complement_lod_plus_dynamic_left_shift [outside domain]   # pp.74589-74590
  internal_representation: twos_complement   # pp.74589,74592
  approximation: none   # pp.74597,74601
new_choices:
  word_size_bits: parameter N — The generator accepts the posit word width independently of ES.   # pp.74588-74589
slots:
  none
parameters: arbitrary N and ES for generated cores; posit(32,6), maximum 23-bit mantissa, 5 pipeline stages for addition/subtraction, and 6 pipeline stages for multiplication   # pp.74594-74596
results:
| metric | value | unit | technology / device | baseline | condition | page |
|---|---:|---|---|---|---|---|
| adder pipeline depth | 5 | stages | Virtex-7 xc7vx330t-3ffg1157 (2019) | none | posit(32,6) | p.74594 |
| multiplier pipeline depth | 6 | stages | Virtex-7 xc7vx330t-3ffg1157 (2019) | none | posit(32,6) | p.74595 |
| 24×24 mantissa-multiplier DSP use | 1 | DSP48E | Virtex-7 xc7vx330t-3ffg1157 (2019) | none | one DSP48E plus a 24×7 multiplier | p.74596 |
errors_and_checks: Round-to-nearest-even is implemented with L/G/R/S bits (p.74592). Several million random cases were checked against the Julia posit package, and all 8-bit inputs received complete validation (p.74597).
conditions: Adder resource use changes little with ES because its major components depend mainly on N, while multiplier resource use decreases as ES increases and the mantissa narrows (p.74598). Posit field extraction/construction costs more than fixed-field FP handling, while IEEE exceptional/subnormal handling also adds FP cost (p.74600). The reported area×period product beats Chaurasiya et al. for the tested formats, but the supplied table image does not expose the numeric cells (p.74599).
evidence: Algorithms 1-9; Figs. 3-9; Tables 1-4; Sections III.A-III.B, IV.A-IV.B, and V.

### newton_raphson  (role: instantiates)
mechanism: The divider obtains a table approximation X0 of the divisor-mantissa reciprocal, applies Xi+1 = Xi × (2 − Xi ∗ D), and multiplies the final reciprocal by the dividend mantissa (pp.74593-74594). The posit wrapper subtracts the divisor regime/exponent from the dividend regime/exponent, normalizes the quotient, reconstructs the posit fields, and rounds to nearest even (pp.74593-74594).
choices:
  iterations: 2   # pp.74593,74596
  dedicated_multiplier: true   # pp.74596-74597
new_choices:
  none
slots:
  seed: monolithic_rom [input_bits=8, output_bits=9, function=reciprocal]   # pp.74593,74596
parameters: 0 iterations when mantissa width is at most 8 bits, 1 iteration for up to 16-bit posits, and 2 iterations for up to 32-bit posits; posit(32,6) uses a 9-stage mantissa divider and a 12-stage complete divider   # pp.74593,74596
results:
| metric | value | unit | technology / device | baseline | condition | page |
|---|---:|---|---|---|---|---|
| complete divider pipeline depth | 12 | stages | Virtex-7 xc7vx330t-3ffg1157 (2019) | none | posit(32,6), 2 NR iterations | p.74596 |
| mantissa-divider pipeline depth | 9 | stages | Virtex-7 xc7vx330t-3ffg1157 (2019) | none | 6 stages for NR refinement plus 3 for final multiplication | p.74596 |
| mantissa-divider DSP use | 5 | DSP48 | Virtex-7 xc7vx330t-3ffg1157 (2019) | none | posit(32,6), 2 NR iterations | p.74597 |
errors_and_checks: The paper says each NR iteration doubles the correct reciprocal bits and that the selected iteration counts achieve the required precision, but it gives no maximum-ulp bound (p.74593). Generated units received random and exhaustive 8-bit validation (p.74597).
conditions: Designs wider than 32 bits require a larger seed table unless additional NR iterations reduce the required table width (p.74594). Multiplicative division offers lower latency at added hardware cost compared with digit recurrence (p.74600).
evidence: Algorithms 10-11; Figs. 10-14; Tables 1 and 5; Sections III.C, IV.C, and V.

### monolithic_rom  (role: instantiates)
mechanism: Eight leading divisor-mantissa bits address a reciprocal table whose 9-bit output supplies the initial Newton-Raphson approximation (pp.74593,74596).
choices:
  input_bits: 8   # pp.74593,74596
  output_bits: 9   # pp.74593,74596
  function: reciprocal   # pp.74593,74596
new_choices:
  none
slots:
  none
parameters: 2^8 × 9 lookup table for posit widths through 32 bits   # pp.74593,74596
results: none reported separately
errors_and_checks: none reported separately
conditions: Higher precision needs a larger table or more Newton-Raphson iterations (p.74594).
evidence: Algorithm 11 and Section IV.C, pp.74593-74596.

### barrel_mux_tree  (role: instantiates)
mechanism: Parameterized dynamic left/right shifters use log2(N) binary-controlled 2:1-multiplexer stages for shifts of 1, 2, 4, and successive powers of two (p.74590). The shifters remove regime bits, align mantissas, normalize results, and position the reconstructed regime (pp.74590-74592).
choices:
  stage_radix: 2   # p.74590
  select_encoding: binary   # p.74590
  direction_handling: mirrored_datapath   # pp.74590-74591
  stage_order: small_shift_first   # p.74590
  sticky_collect: true   # p.74592
new_choices:
  none
slots:
  none
parameters: N-bit data, S=log2(N) shift-control bits, and one N-bit 2:1 mux level per shift-control bit   # p.74590
results: none reported separately
errors_and_checks: none
conditions: The posit extraction shifter operates on N−1 bits, while alignment and normalization widths depend on the available mantissa width (pp.74590-74591).
evidence: Algorithms 3 and 5; Figs. 4 and 6; pp.74589-74592.

## new_families
### posit_divider  (domain: dsp: posit units, closest: posit_adder_multiplier, why_not: posit_adder_multiplier covers posit addition/multiplication but has no posit-division mechanism or divider slot)
mechanism: The unit extracts variable-position posit fields, divides the mantissas with a parameterized Newton-Raphson reciprocal, subtracts the divisor regime/exponent from the dividend regime/exponent, normalizes the quotient, reconstructs the posit encoding, and applies round-to-nearest-even (pp.74593-74594).
choices: word_size_bits: positive integer; es_bits: nonnegative integer; mantissa_division: {newton_raphson}; iterations: Int[0..3:1]
results:
| metric | value | unit | technology / device | baseline | condition | page |
|---|---:|---|---|---|---|---|
| pipeline depth | 12 | stages | Virtex-7 xc7vx330t-3ffg1157 (2019) | none | posit(32,6), 2 NR iterations | p.74596 |
evidence: Algorithms 10-11; Figs. 10-14; Section III.C and IV.C, pp.74593-74597.

## space_gaps
* `posit_adder_multiplier.es_bits` excludes the demonstrated ES=6 and the generator’s arbitrary ES parameter (pp.74588,74594).
* `posit_adder_multiplier` lacks a `word_size_bits` choice even though N is an independent generator parameter (pp.74588-74589).
* The posit-unit vocabulary lacks a posit divider wrapper and a slot for its division family (pp.74593-74597).
* `newton_raphson.iter_mult` cannot name the explicitly instantiated DSP48E-based multiplier construction (pp.74596-74597).

## open_questions
* The paper does not identify the carry-propagate topology used by the mantissa add/sub units (pp.74591,74594).
* The paper does not state a maximum-ulp or maximum-absolute-error bound for Newton-Raphson division (pp.74593-74594).
* Numeric cells in Figs. 15-16 and Tables 1-6 are not recoverable from the supplied text, so their LUT/FF/frequency/period/area/power values are excluded (pp.74598-74600).
