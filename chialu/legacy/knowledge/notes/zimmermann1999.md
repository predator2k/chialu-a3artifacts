---
handle: zimmermann1999
citation: R. Zimmermann, "Efficient VLSI Implementation of Modulo (2^n +/- 1) Addition and Multiplication", 14th IEEE Symposium on Computer Arithmetic (ARITH-14), 1999
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, other]
formats: [int8, int16, int32, int64]
authority: landmark
pages_read: 10 / 10
---

## summary
The paper proposes parallel-prefix end-around-carry adders and modulo-reduced multipliers for arithmetic modulo (2^n - 1) and (2^n + 1). The multipliers use end-around carry-save reduction, Wallace trees, optional Booth recoding, and one modulo final adder. A fused IDEA multiplier-adder reduces four serial carry propagations to one.

## families
### parallel_prefix  (role: instantiates)
mechanism: Generate/propagate pairs are combined by an associative prefix operator, followed by XOR sum generation. The Sklansky structure is presented as the least-depth structure, while other prefix graphs provide area-delay trade-offs.
choices:
  topology: sklansky   # p.2
  node_style: and_or   # p.2
new_choices:
  none
slots:
  none
parameters: n-bit adder; m prefix levels   # p.2
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area | 3/2 n log n + 4n | unit gates | unit-gate model / 1999 | none | ordinary integer adder | p.9 |
| delay | 2 log n + 3 | unit-gate delays | unit-gate model / 1999 | none | ordinary integer adder | p.9 |
errors_and_checks: none
conditions: Prefix graphs span area-delay trade-offs and support parameterized synthesizable VHDL generation.   # p.2
evidence: §2.1, Figs. 1–3, Table 3, pp.2,9

### end_around_carry  (role: proposes)
mechanism: An extra prefix level propagates the carry-out into the sum as a fast increment. Modulo (2^n - 1) uses direct feedback, with an optional group-propagate OR for a single zero representation. Modulo (2^n + 1) uses inverted feedback in diminished-one or normal representation.
choices:
  modulus: mod_2n_minus_1 / mod_2n_plus_1_diminished_one / mod_2n_plus_1_normal [outside domain]   # pp.3–4
  recirculation: cyclic_prefix_level   # p.3
  topology: sklansky   # pp.2–3
new_choices:
  zero_representation: {single, double, diminished_one, normal_2n_as_zero} — representation and special-case policy   # pp.4,7
slots:
  none
parameters: n-bit; one additional prefix level; n additional black nodes   # p.3
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area | 3/2 n log n + 7n | unit gates | unit-gate model / 1999 | integer 3/2 n log n + 4n | either modulus | p.9 |
| delay | 2 log n + 5 | unit-gate delays | unit-gate model / 1999 | integer 2 log n + 3 | either modulus | p.9 |
| area (8 bit) | 4365 | UNKNOWN | 0.25 μm standard-cell / 1999 | integer 4239; DW (2^n-1) 6975 | mod (2^n-1) | p.10 |
| delay (8 bit) | 0.78 | UNKNOWN | 0.25 μm standard-cell / 1999 | integer 0.52; DW (2^n-1) 0.92 | mod (2^n-1) | p.10 |
| area (16 bit) | 10611 | UNKNOWN | 0.25 μm standard-cell / 1999 | integer 7137; DW (2^n-1) 14400 | mod (2^n-1) | p.10 |
| delay (16 bit) | 0.93 | UNKNOWN | 0.25 μm standard-cell / 1999 | integer 0.71; DW (2^n-1) 1.30 | mod (2^n-1) | p.10 |
| area (32 bit) | 19269 | UNKNOWN | 0.25 μm standard-cell / 1999 | integer 15336; DW (2^n-1) 30771 | mod (2^n-1) | p.10 |
| delay (32 bit) | 1.17 | UNKNOWN | 0.25 μm standard-cell / 1999 | integer 0.93; DW (2^n-1) 1.58 | mod (2^n-1) | p.10 |
| area (64 bit) | 43452 | UNKNOWN | 0.25 μm standard-cell / 1999 | integer 34065; DW (2^n-1) 70443 | mod (2^n-1) | p.10 |
| delay (64 bit) | 1.43 | UNKNOWN | 0.25 μm standard-cell / 1999 | integer 1.14; DW (2^n-1) 1.95 | mod (2^n-1) | p.10 |
| area (8/16/32/64 bit) | 4806 / 8181 / 23706 / 45000 | UNKNOWN | 0.25 μm standard-cell / 1999 | integer 4239 / 7137 / 15336 / 34065 | mod (2^n+1) | p.10 |
| delay (8/16/32/64 bit) | 0.77 / 1.06 / 1.16 / 1.44 | UNKNOWN | 0.25 μm standard-cell / 1999 | integer 0.52 / 0.71 / 0.93 / 1.14 | mod (2^n+1) | p.10 |
errors_and_checks: Exact modular addition; no fault-detection mechanism is reported.   # pp.3–4
conditions: The normal modulo-(2^n+1) form treats 2^n separately. Diminished-one representation can require external increment/decrement conversion.   # p.4
evidence: §2.2–2.4, Fig. 4, Tables 3 and 5, pp.3–4,9–10

### carry_save_datapath  (role: extends)
mechanism: Carry outputs from each compressor level are wrapped into the next level’s low-order carry inputs. Direct feedback implements modulo (2^n - 1), while inverted feedback implements modulo (2^n + 1). Linear arrays favor regularity and trees favor speed.
choices:
  compressor: 3_2   # p.4
  assimilation_point: end_of_chain   # pp.5–6
  accumulator_redundant: true   # pp.4–6
new_choices:
  end_around_feedback: {direct, inverted} — selects the two modular recurrences   # p.4
slots:
  assimilator: end_around_carry   # pp.5–6
parameters: m operands; m-2 carry-save adders; linear or tree (m,2)-compressors; constant cell delay   # pp.4–5
results:
| metric | value | unit | technology / device | baseline | condition | page |
| none | UNKNOWN | UNKNOWN | UNKNOWN / 1999 | none | no standalone quantitative result | p.5 |
errors_and_checks: Exact redundant modular summation.   # pp.4–5
conditions: Tree structures are faster and less regular; cell-based implementation makes the regularity loss negligible.   # pp.5–6
evidence: §2.5, Figs. 5–6, pp.4–5

### rns_channel_arithmetic  (role: extends)
mechanism: Rotated modulo-reduced partial products are accumulated by an end-around carry-save tree and resolved by one modulo carry-propagate adder. The modulo-(2^n+1) design adds constant/correction terms and a 2^n special-case correction unit.
choices:
  modulus_form: pow2_minus_1 / pow2_plus_1 [outside domain]   # pp.6–8
  pow2_plus_1_encoding: normal / diminished_one [outside domain]   # pp.7–8
  multiplier_reduction: csa_with_periodic_folding   # pp.6–8
new_choices:
  partial_product_recoding: {none, booth_bit_pair} — controls partial-product count   # pp.6,8
slots:
  modular_adder: end_around_carry   # pp.6–8
parameters: 8/16/32-bit implementations; n partial products without Booth; n/2+1 with Booth; Wallace tree; one final modulo adder   # pp.6,8–10
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area (8/16/32 bit) | 16740 / 60894 / 233127 | UNKNOWN | 0.25 μm standard-cell / 1999 | integer 16668 / 61542 / 237564 | mod (2^n-1), no Booth | p.10 |
| delay (8/16/32 bit) | 2.54 / 3.51 / 4.83 | UNKNOWN | 0.25 μm standard-cell / 1999 | integer 2.32 / 3.33 / 4.51 | mod (2^n-1), no Booth | p.10 |
| area (8/16/32 bit) | 20232 / 66213 / 236574 | UNKNOWN | 0.25 μm standard-cell / 1999 | integer 16668 / 61542 / 237564 | mod (2^n+1), no Booth | p.10 |
| delay (8/16/32 bit) | 2.47 / 3.60 / 4.76 | UNKNOWN | 0.25 μm standard-cell / 1999 | integer 2.32 / 3.33 / 4.51 | mod (2^n+1), no Booth | p.10 |
errors_and_checks: The Booth correction terms were exhaustively verified in a circuit implementation.   # p.8
conditions: Wallace trees are recommended. Booth recoding halves the partial-product count but does not always reduce cell-based area or tree delay.   # p.6
evidence: §3.1–3.4, Figs. 7–8, Tables 1–2,6, pp.6–8,10

## new_families
### modulo_multiplier_adder  (domain: dot, closest: fused_csa, why_not: fused_csa lacks dual modular outputs and cross-modulus carry correction)
mechanism: The IDEA unit injects addend A into the modulo-(2^n+1) multiplier’s redundant product before final propagation. Parallel final adders produce the modulo-(2^n+1) product and modulo-2^n sum, with the product adder’s inverted carry-out correcting both paths.
choices: outputs: {product_and_sum}; fusion_point: {before_final_adder}; final_adders: {parallel_dual}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area (8/16/32 bit) | 23256 / 74835 / 258858 | UNKNOWN | 0.25 μm standard-cell / 1999 | mod multiplier 20232 / 66213 / 236574 | mod (2^n+1)+ | p.10 |
| delay (8/16/32 bit) | 2.91 / 3.95 / 5.02 | UNKNOWN | 0.25 μm standard-cell / 1999 | mod multiplier 2.47 / 3.60 / 4.76 | mod (2^n+1)+ | p.10 |
| throughput | 720 | Mbit/s | 0.25 μm standard-cell / 1999 | standard-component composition | 100 MHz IDEA cipher engine | p.10 |
evidence: §4, Fig. 9, Tables 4 and 6, pp.8–10

## space_gaps
* `end_around_carry.modulus` lacks a value for modulo (2^n + 1) with normal representation.   # pp.4,7
* `carry_save_datapath` lacks direct/inverted end-around feedback as a declared choice.   # pp.4–5
* No existing family represents a fused modular multiplier with separate product and post-addition outputs.   # pp.8–9

## open_questions
* The exact prefix topology used for every synthesized custom unit is not stated; Sklansky is shown as the least-depth example.   # pp.2,9
* Table 5 and Table 6 do not print area/delay units in the supplied document text.   # p.10
* The standard-cell multiplier results exclude Booth recoding, so the paper gives no quantitative Booth implementation result.   # pp.9–10
