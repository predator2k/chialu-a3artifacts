---
handle: murillo_2020
citation: R. Murillo, A. A. Del Barrio, G. Botella, "Customized Posit Adders and Multipliers Using the FloPoCo Core Generator", IEEE International Symposium on Circuits and Systems (ISCAS), 2020
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [posit8_0, posit16_1, posit32_2]
authority: incremental
pages_read: 5 / 5
---

## summary
The paper proposes parameterized posit adder/subtractor and multiplier generators for FloPoCo 5.0, including configurations with es = 0. The shared decoder uses an integrated LZOC+Shift, while the encoder performs round-to-nearest-even. Synthesized 65 nm results show lower area/energy than the cited posit-unit baselines, with increased adder delay relative to [17].

## families
### posit_adder_multiplier  (role: proposes)
mechanism: Both units decode each posit into sign/regime/exponent/fraction fields, operate on the decoded fields, and encode a correctly rounded posit result. The decoder converts negative inputs to absolute values with 2’s complement and uses one LZOC+Shift to count and remove either leading zeros or leading ones. Addition orders operands, aligns the smaller fraction, adds or subtracts, normalizes with LZC+Shift, and adjusts the scale. Multiplication multiplies the decoded fractions, normalizes the product, and adds the operand scales plus the fraction-overflow bit.
choices:
  es_bits: 0, 1, 2   # p.1, p.4
  regime_decode: lzc_plus_shifter   # p.2
  internal_representation: sign_magnitude   # p.2–p.4
  approximation: none   # p.3–p.4
new_choices:
  operation: {add_subtract, multiply} — selects the generated posit functional unit   # p.2–p.4
  regime_counter: integrated_lzoc_shift — counts and shifts either leading-zero or leading-one regimes in one component   # p.2
  output_rounding: round_to_nearest_even — uses LSB/Guard/Round/Sticky bits for unbiased rounding   # p.3
  generator_configuration: any_n_es_including_es_0 — FloPoCo generates synthesizable VHDL for parameterized n/es configurations   # p.1–p.2
slots: none
parameters: Posit⟨n, es⟩; evaluated configurations ⟨8,0⟩, ⟨16,1⟩, and ⟨32,2⟩; combinational operators; fraction multiplier inputs have width fracsize = n − es − 2 bits   # p.3–p.4
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area | 3228.48 | µm² | 65 nm target-library / 2020 | [17] | posit⟨16,1⟩ adder baseline | p.4 |
| delay | 5.34 | ns | 65 nm target-library / 2020 | [17] | posit⟨16,1⟩ adder baseline | p.4 |
| power | 1637.6 | µW | 65 nm target-library / 2020 | [17] | posit⟨16,1⟩ adder baseline | p.4 |
| energy | 8.74 | pJ | 65 nm target-library / 2020 | [17] | posit⟨16,1⟩ adder baseline | p.4 |
| area | 7615.08 | µm² | 65 nm target-library / 2020 | [17] | posit⟨32,2⟩ adder baseline | p.4 |
| delay | 7.94 | ns | 65 nm target-library / 2020 | [17] | posit⟨32,2⟩ adder baseline | p.4 |
| power | 3828.3 | µW | 65 nm target-library / 2020 | [17] | posit⟨32,2⟩ adder baseline | p.4 |
| energy | 30.4 | pJ | 65 nm target-library / 2020 | [17] | posit⟨32,2⟩ adder baseline | p.4 |
| area | 1038.6 | µm² | 65 nm target-library / 2020 | [17] | this-work posit⟨8,0⟩ adder | p.4 |
| delay | 3.9 | ns | 65 nm target-library / 2020 | [17] | this-work posit⟨8,0⟩ adder | p.4 |
| power | 489.5 | µW | 65 nm target-library / 2020 | [17] | this-work posit⟨8,0⟩ adder | p.4 |
| energy | 1.91 | pJ | 65 nm target-library / 2020 | [17] | this-work posit⟨8,0⟩ adder | p.4 |
| area | 2176.92 | µm² | 65 nm target-library / 2020 | [17] | this-work posit⟨16,1⟩ adder | p.4 |
| delay | 6.23 | ns | 65 nm target-library / 2020 | [17] | this-work posit⟨16,1⟩ adder | p.4 |
| power | 1133.1 | µW | 65 nm target-library / 2020 | [17] | this-work posit⟨16,1⟩ adder | p.4 |
| energy | 7.06 | pJ | 65 nm target-library / 2020 | [17] | this-work posit⟨16,1⟩ adder | p.4 |
| area | 4880.88 | µm² | 65 nm target-library / 2020 | [17] | this-work posit⟨32,2⟩ adder | p.4 |
| delay | 9.48 | ns | 65 nm target-library / 2020 | [17] | this-work posit⟨32,2⟩ adder | p.4 |
| power | 2811.1 | µW | 65 nm target-library / 2020 | [17] | this-work posit⟨32,2⟩ adder | p.4 |
| energy | 26.65 | pJ | 65 nm target-library / 2020 | [17] | this-work posit⟨32,2⟩ adder | p.4 |
| area | 4955.76 | µm² | 65 nm target-library / 2020 | [17] | posit⟨16,1⟩ multiplier baseline | p.4 |
| delay | 5.15 | ns | 65 nm target-library / 2020 | [17] | posit⟨16,1⟩ multiplier baseline | p.4 |
| power | 3036.6 | µW | 65 nm target-library / 2020 | [17] | posit⟨16,1⟩ multiplier baseline | p.4 |
| energy | 15.64 | pJ | 65 nm target-library / 2020 | [17] | posit⟨16,1⟩ multiplier baseline | p.4 |
| area | 15106.32 | µm² | 65 nm target-library / 2020 | [17] | posit⟨32,2⟩ multiplier baseline | p.4 |
| delay | 8.54 | ns | 65 nm target-library / 2020 | [17] | posit⟨32,2⟩ multiplier baseline | p.4 |
| power | 13027 | µW | 65 nm target-library / 2020 | [17] | posit⟨32,2⟩ multiplier baseline | p.4 |
| energy | 111.25 | pJ | 65 nm target-library / 2020 | [17] | posit⟨32,2⟩ multiplier baseline | p.4 |
| area | 1271 | µm² | 65 nm target-library / 2020 | [18] | posit⟨8,0⟩ multiplier baseline | p.4 |
| delay | 3.36 | ns | 65 nm target-library / 2020 | [18] | posit⟨8,0⟩ multiplier baseline | p.4 |
| power | 612.4 | µW | 65 nm target-library / 2020 | [18] | posit⟨8,0⟩ multiplier baseline | p.4 |
| energy | 2.06 | pJ | 65 nm target-library / 2020 | [18] | posit⟨8,0⟩ multiplier baseline | p.4 |
| area | 3865 | µm² | 65 nm target-library / 2020 | [18] | posit⟨16,1⟩ multiplier baseline | p.4 |
| delay | 6.2 | ns | 65 nm target-library / 2020 | [18] | posit⟨16,1⟩ multiplier baseline | p.4 |
| power | 2609.6 | µW | 65 nm target-library / 2020 | [18] | posit⟨16,1⟩ multiplier baseline | p.4 |
| energy | 16.18 | pJ | 65 nm target-library / 2020 | [18] | posit⟨16,1⟩ multiplier baseline | p.4 |
| area | 21894 | µm² | 65 nm target-library / 2020 | [18] | posit⟨32,2⟩ multiplier baseline | p.4 |
| delay | 9.6 | ns | 65 nm target-library / 2020 | [18] | posit⟨32,2⟩ multiplier baseline | p.4 |
| power | 13053.3 | µW | 65 nm target-library / 2020 | [18] | posit⟨32,2⟩ multiplier baseline | p.4 |
| energy | 125.31 | pJ | 65 nm target-library / 2020 | [18] | posit⟨32,2⟩ multiplier baseline | p.4 |
| area | 1032.48 | µm² | 65 nm target-library / 2020 | [17], [18] | this-work posit⟨8,0⟩ multiplier | p.4 |
| delay | 2.98 | ns | 65 nm target-library / 2020 | [17], [18] | this-work posit⟨8,0⟩ multiplier | p.4 |
| power | 558.4 | µW | 65 nm target-library / 2020 | [17], [18] | this-work posit⟨8,0⟩ multiplier | p.4 |
| energy | 1.66 | pJ | 65 nm target-library / 2020 | [17], [18] | this-work posit⟨8,0⟩ multiplier | p.4 |
| area | 3321.72 | µm² | 65 nm target-library / 2020 | [17], [18] | this-work posit⟨16,1⟩ multiplier | p.4 |
| delay | 5.64 | ns | 65 nm target-library / 2020 | [17], [18] | this-work posit⟨16,1⟩ multiplier | p.4 |
| power | 2470.9 | µW | 65 nm target-library / 2020 | [17], [18] | this-work posit⟨16,1⟩ multiplier | p.4 |
| energy | 13.94 | pJ | 65 nm target-library / 2020 | [17], [18] | this-work posit⟨16,1⟩ multiplier | p.4 |
| area | 11924.64 | µm² | 65 nm target-library / 2020 | [17], [18] | this-work posit⟨32,2⟩ multiplier | p.4 |
| delay | 8.87 | ns | 65 nm target-library / 2020 | [17], [18] | this-work posit⟨32,2⟩ multiplier | p.4 |
| power | 11926 | µW | 65 nm target-library / 2020 | [17], [18] | this-work posit⟨32,2⟩ multiplier | p.4 |
| energy | 105.78 | pJ | 65 nm target-library / 2020 | [17], [18] | this-work posit⟨32,2⟩ multiplier | p.4 |
| area reduction | up to 35.9% | % | 65 nm target-library / 2020 | state-of-the-art works | proposed adders/multipliers | p.1 |
| energy reduction | up to 30.8% | % | 65 nm target-library / 2020 | state-of-the-art works | proposed adders/multipliers | p.1 |
errors_and_checks: The encoder implements correct unbiased round-to-nearest-even using LSB, G, R, and S; zero and NaR cases are detected during decoding and emitted during encoding   # p.2–p.3
conditions: Results use Synopsys Design Compiler, a 65 nm target-library, no timing constraint, and combinational operators. FloPoCo can pipeline for a selected frequency, but pipelining is excluded because [17] lacks pipelined designs for every tested configuration. The adders reduce area by more than 32% and power by more than 26% relative to [17], while delay increases around 18%. Multipliers reduce area/power/energy around 27%/13.5%/8% relative to [17], with delay increasing by at most 9.5%; all reported metrics improve relative to [18]   # p.4
evidence: Algorithms 1–4, pp.2–4; Tables I–II and evaluation discussion, p.4

## new_families
none

## space_gaps
* posit_adder_multiplier lacks choices for operation selection, integrated LZOC+Shift regime decoding, output rounding, and support for arbitrary n/es including es = 0   # p.1–p.4
* posit_adder_multiplier lacks a multiplier slot for the integer fraction multiplier used by the posit multiplication core   # p.3–p.4
* posit_adder_multiplier.regime_decode lacks integrated_lzoc_shift, which handles both regime signs without separate detectors or operand inversion for regime normalization   # p.2

## open_questions
* The document does not identify the topology selected by FloPoCo for the fraction adder or integer fraction multiplier.
* The document describes only a “65 nm target-library” and does not identify the library or cell process.
* The document does not state the power-estimation workload, activity factors, or input distribution.
