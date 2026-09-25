---
handle: crespo_2022
citation: L. Crespo, P. Tomás, N. Roma, N. Neves, "Unified Posit/IEEE-754 Vector MAC Unit for Transprecision Computing", IEEE Transactions on Circuits and Systems II: Express Briefs, 2022
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [posit8, posit16, posit32, fp8_e4m3, fp16, fp32]
authority: incremental
pages_read: 2478-2482 / 5
---

## summary
The document proposes a fully pipelined 32-bit vector MAC datapath that supports Posit and IEEE-754 formats, runtime precision selection, SIMD execution, inter-format operations, and conversion. The design limits the quire to 128 bits and pairs it with a scale factor, which reduces the cost of higher-precision posit operation while preserving exact accumulation for standard 8-bit posits. A 28nm ASIC implementation uses 50% less area and 2.9× less power than the compared multi-unit transprecision setup.

## families
### posit_ieee_interop  (role: extends)
mechanism: Posit and IEEE-754 operands are decoded into shared sign, scale-factor, and fraction vectors using the internal form (−1)^s × 2^sf × 1.f. Each operand format and the output format are configured independently, so the shared arithmetic datapath performs mixed-format operations and conversions. Posit decoding includes sign-conditioned 2’s complementation, regime run-length decoding, and runtime exponent extraction; IEEE-754 decoding extracts fields and removes the configured bias. Format-specific encoding and exception handling follow the shared arithmetic stages. (pp.2479-2481)
choices:
  interop_style: unified_dual_format_datapath   # pp.2479-2480
  conversion_direction: bidirectional   # p.2480
  quire_present: true   # pp.2479-2480
new_choices:
  runtime_configurable_posit_es: true — the posit exponent size is selected at runtime   # p.2479
  per_operand_format_selection: true — Va, Vb, Vc, and Vr formats are independently configured   # p.2480
slots: none
parameters: 32/16/8-bit Posit and IEEE-754 elements; custom 8-bit IEEE-like format has 4 exponent bits and 3 mantissa bits   # p.2479
results: none
errors_and_checks: IEEE-754 encoding handles subnormals and selects rounded result/zero/infinity/canonical NaN from generated flags; the document gives no numeric ulp or error-rate result.   # p.2481
conditions: Posit support provides configurable low-precision dynamic range, while IEEE-754 support preserves compatibility with the established standard.   # pp.2478,2482
evidence: §II-A-B; §III-A-B; Figs. 1-3

### multi_precision_simd_fma  (role: extends)
mechanism: One 32-bit SIMD datapath executes addition, subtraction, multiplication, fused multiply-add, and multiply-accumulate operations. Runtime gating partitions the arithmetic into one 32-bit lane, two 16-bit lanes, or four 8-bit lanes. Six pipeline stages perform Decode, Multiply, Quire Scale, Quire Accumulate, Normalize, and Encode. (pp.2479-2481)
choices:
  lane_split: 1x32 / 2x16 / 4x8 [outside domain]   # pp.2479-2480
new_choices:
  supported_format_pair: posit_and_ieee754 — every precision mode shares both format datapaths   # pp.2479-2480
slots:
  lza: lzc_after_add   # p.2481
  multiplier: booth_recoded_parallel [booth_radix=4]   # p.2480
parameters: 32-bit datapath; 1x32-bit, 2x16-bit, or 4x8-bit operation; 6 pipeline stages; target frequency 667 MHz   # pp.2480-2481
results:
| metric | value | unit | technology / device | baseline | condition | page |
| chip area | 50 | % less | UMC 28nm standard-cell ASIC, 2022 | fixed Posit MAC combination with 4x8-bit + 2x16-bit + 1x32-bit MACs | same multiple-precision functionality | p.2482 |
| power consumption | 2.9 | × less | UMC 28nm standard-cell ASIC, 2022 | fixed Posit MAC combination with 4x8-bit + 2x16-bit + 1x32-bit MACs | same multiple-precision functionality | p.2482 |
| chip area | 30 | % increase | UMC 28nm standard-cell ASIC, 2022 | reference 32-bit Posit MAC with fixed es=2 and 512-bit quire | unified format and variable-precision VMAC | p.2481 |
errors_and_checks: Operation was validated with vectors from the Sigmoid Numbers Julia library and TestFloat; no numeric error bound, fault model, coverage, or false-alarm result is reported.   # p.2481
conditions: Lower precision enables parallel lanes by activating only the required arithmetic resources.   # pp.2479-2480 The comparisons with VFMA/VMULT use DeepScaleTool estimates because the source implementations use 90nm rather than 28nm technology.   # pp.2481-2482
evidence: §III-A-B; §IV; Figs. 1-2; Tables I-III; §V

### posit_quire_mac  (role: extends)
mechanism: Fraction products and the addend are converted into a vectorized 128-bit two’s-complement fixed-point quire representation paired with scale factors. The Scale stage saturates excessive shift amounts and adjusts the scale factor. The Accumulate stage aligns selected operands by their scale factors, condenses discarded bits into a sticky vector, and either adds a new value or accumulates the saved quire value. Normalization extracts sign/scale/fraction vectors for encoding. (pp.2480-2481)
choices:
  quire_width_bits: 128   # pp.2479-2481
  op_set: fused_ops_general   # p.2480
new_choices:
  exact_accumulation_scope: posit8_es2 — exact accumulation is provided only for standard 8-bit posits with es=2   # p.2479
  external_scale_factor: true — a scale factor accompanies the fixed-size quire for wider dynamic ranges   # pp.2479-2480
slots: none
parameters: 128-bit quire; reference fixed Posit MACs use 128/256/512-bit quires for 8/16/32-bit formats with es=2   # pp.2479,2481
results: none
errors_and_checks: The 8-bit posit es=2 mode accumulates products without rounding or accuracy loss; the document gives no numeric accuracy guarantee for the scaled 16-bit or 32-bit modes.   # pp.2479-2480
conditions: The fixed 128-bit quire mitigates the critical path and hardware growth associated with 256-bit and 512-bit quires.   # pp.2479,2481
evidence: §II-B; §III-A-B; Fig. 2; §IV

### booth_recoded_parallel  (role: instantiates)
mechanism: The fraction multiplier uses a 4×4 structure of 8-bit radix-4 Booth multipliers. The structure generates 16 partial products in carry-save form and reduces them with a Wallace-tree-like network to a 64-bit value. Precision and vectorization select the required component multipliers at runtime. (p.2480)
choices:
  booth_radix: 4   # p.2480
new_choices: none
slots:
  reduction: csa_reduction_tree   # p.2480
parameters: 4×4 8-bit multiplier structure; 16 partial products; 64-bit reduced value   # p.2480
results: none
errors_and_checks: none
conditions: Lower-precision modes enable only the component multipliers required for the selected vector lanes.   # p.2480
evidence: §III-B, “Multiplication”; Fig. 2

### carry_lookahead  (role: instantiates)
mechanism: A vectorized carry-lookahead adder adds the scale-factor vectors. Configurable carry-chain breaks permit parallel additions in lower-precision vector modes. (p.2480)
choices: none
new_choices:
  lane_boundary_carry_break: true — configured lane boundaries interrupt carry propagation for SIMD scale-factor addition   # p.2480
slots: none
parameters: vectorized scale-factor addition for 32/16/8-bit modes   # p.2480
results: none
errors_and_checks: none
conditions: Carry-chain breaking is used for lower-precision parallel additions.   # p.2480
evidence: §III-B, “Multiplication”; Fig. 2

## new_families
none

## space_gaps
* multi_precision_simd_fma.lane_split lacks the document’s 1x32/2x16/4x8 lane set.   # pp.2479-2480
* posit_quire_mac lacks choices for precision-dependent exactness and an external scale factor paired with a fixed-size quire.   # pp.2479-2480
* posit_ieee_interop lacks runtime-configurable posit exponent size and independently selected operand/output formats.   # pp.2479-2480
* carry_lookahead lacks a SIMD lane-boundary carry-break choice.   # p.2480

## open_questions
* Tables I-III are present without legible cell values in the supplied document text, so their detailed area/power/latency/throughput/EDP numbers remain UNKNOWN.
* The document does not state a numeric accuracy contract for 16-bit or 32-bit posit accumulation with the scaled 128-bit quire.
* The document states that fractions are rounded during encoding but does not identify the rounding mode.
