---
handle: lipetz_schwarz_2011
citation: D. Lipetz, E. Schwarz, "Self Checking in Current Floating-Point Units", Proc. 20th IEEE Symposium on Computer Arithmetic (ARITH-20), pp. 73-76, 2011
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, other]
formats: [binary_fp, decimal_fp, bcd, fixed_point_int]
authority: incremental
pages_read: 73-76 / 76
---

## summary
The paper compares duplication/parity prediction/residue checking in IBM floating-point units and proposes a hybrid modulo-9/modulo-3 residue generator for decimal and binary data. The hybrid generator recodes BCD digits into two base-3 digits and uses a one-hot pass-gate tree. The paper reports implementations from POWER6/POWER7/z10/z196 and 45 nm area comparisons.

## families
### residue  (role: extends)
mechanism: Residues are calculated independently from arithmetic inputs and compared with the result residue. Diminished-radix moduli reduce residue generation to digit summation: modulo 3 for base 4, modulo 15 for base 16, and modulo 9 for base 10 (pp.73-75). The hybrid generator decodes each BCD digit into high/low base-3 digits, merges both trees independently, defers the low-digit carry, and selects modulo 9 for BCD or modulo 3 for non-BCD input (p.75).
choices:
  modulus: 3 | 9 [outside domain] | 15   # pp.74-75
  granularity: endpoint   # p.75
  generator_style: csa_tree   # p.74
new_choices:
  input_radix: binary | decimal | binary_decimal — selects a residue compatible with the represented number system   # pp.74-75
  residue_encoding: conventional_binary | one_hot — one-hot residue values enable rotation-based addition   # p.74
  generator_implementation: counter_tree | pass_gate_mux | standard_cmos | serial_loop — circuit alternatives compared by the paper   # pp.74,76
  hybrid_mode: modulo_9_for_bcd_modulo_3_for_non_bcd — the low base-3 digit alone supplies residue 3   # p.75
slots:
  none
parameters: 64-bit comparison input; 2-bit modulo-3 output; two 2-bit modulo-9/3 outputs; two 4-bit modulo-15 outputs; z196 modulo-15 generation sums 16 hexadecimal digits with 4:2 CSAs   # pp.74,76
results:
| metric | value | unit | technology / device | baseline | condition | page |
| detection coverage | 66% | percent | UNKNOWN / UNKNOWN / UNKNOWN | totally random multiple-bit failures | residue 3 | p.75 |
| detection coverage | 88% | percent | UNKNOWN / UNKNOWN / UNKNOWN | totally random multiple-bit failures | residue 9 | p.75 |
| detection coverage | 93% | percent | UNKNOWN / UNKNOWN / UNKNOWN | totally random multiple-bit failures | residue 15 | p.75 |
| checker area | about 18% | total FPU area | UNKNOWN / POWER7 / 2010 | none | residue 15 in VSU | p.76 |
| area | 197x8.5 | um | 45 nm / z196 / 2010 | none | Res 3 t-gate; 64-bit input; 2-bit output; 18 tracks per bit | p.76 |
| area | 197x14.5 | um | 45 nm / z196 / 2010 | none | Res 3 cmos; 64-bit input; 2-bit output; 18 tracks per bit | p.76 |
| area | 197x3.75 | um | 45 nm / z196 / 2010 | none | Res 3 Serial; 64-bit input; 2-bit output; 18 tracks per bit | p.76 |
| area | 191.5x14 | um | 45 nm / z196 / 2010 | none | Res 9-3; 64-bit input; 2 – 2 bit output; 18 tracks per bit | p.76 |
| area | 158.5x10.5 | um | 45 nm / z196 / 2010 | none | Res15; 64-bit input; 2 – 4 bit output; 18 tracks per bit | p.76 |
| area | 158.5x5.9 | um | 45 nm / z196 / 2010 | none | Res 15; 64-bit input; 2 – 4 bit output; 9 tracks per bit | p.76 |
errors_and_checks: Residue checking fully detects a one-bit flip in the overall result. For random multiple-bit failures, the reported coverage is 2/3 for modulus 3, 8/9 for modulus 9, and 14/15 for modulus 15 (p.75). Addition/subtraction/multiplication/division are checked through their residue identities (p.75).
conditions: Modulo 3 checks both BCD and base-2 integers, while modulo 9 is effective for decimal data and modulo 15 gives higher multiple-bit coverage (pp.74-75). Floating-point checking must account for alignment/truncated digits/rounding/NaNs/infinities, and the exponent/significand/interface/control paths are usually checked separately (p.75). Residue checking is independent of the internal adder/multiplier design (p.75). The serial modulo-3 implementation is smallest but slowest (p.76).
evidence: §§II-VII; Figure 1; §§VIII-IX; Table I, pp.73-76

### parity_prediction_adder  (role: analyzes)
mechanism: Addition parity is predicted independently from operand parity and carry behavior, while stored or transmitted data commonly carries one parity bit per byte (pp.73,75).
choices:
  none
new_choices:
  none
slots:
  none
parameters: one parity bit per byte   # p.75
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area | on the order of 1/3 | size of the adder | UNKNOWN / UNKNOWN / UNKNOWN | adder | addition parity-prediction circuit | p.73 |
errors_and_checks: Parity detects one or any odd number of bit flips and detects every one-bit flip within a protected byte (p.75).
conditions: Parity prediction is useful when data must be transmitted immediately with parity to a cache/register file (p.73). Residue codes can replace parity when the storage protection code is flexible (p.73).
evidence: Introduction, p.73; §VII, p.75

### duplication  (role: analyzes)
mechanism: Two execution-unit copies perform the same operation and their outputs are compared. G4/G5/G6/z900 use simultaneous copies, while z990/z9-109 delay the second copy by one cycle so the leading result can be used before checking (p.76).
choices:
  replication: 2   # p.76
  comparison_point: per_cycle   # p.76
  temporal_stagger: false | true   # p.76
new_choices:
  none
slots:
  none
parameters: one-cycle stagger for z990 and z9-109; simultaneous execution for G4/G5/G6/z900   # p.76
results:
| metric | value | unit | technology / device | baseline | condition | page |
| detection coverage | almost 100% | percent | UNKNOWN / z900 / 2000 | none | simultaneous full duplication | p.76 |
| detection coverage | almost 100% | percent | UNKNOWN / z990 / 2003 | none | second copy runs one cycle behind | p.76 |
errors_and_checks: Identical transient failures in both copies and failures in comparison hardware remain possible (p.76).
conditions: Full duplication provides high coverage but consumes substantial area/power and requires comparison before use (p.76). Skewed duplication permits use of the leading output before the delayed comparison (p.76). z10 uses duplication for the exponent dataflow because exponent errors strongly affect the result (pp.75-76).
evidence: Introduction, p.73; §§VII-VIII, pp.75-76

## new_families
none

## space_gaps
* residue.modulus lacks 9, which the paper uses for decimal arithmetic checking (pp.74-75).
* residue lacks a selectable hybrid modulo-9/modulo-3 mode for mixed BCD/base-2 units (p.75).
* residue.generator_style lacks one-hot pass-gate multiplexor trees and serial-loop generators (pp.74,76).
* residue lacks an input-radix choice that distinguishes binary/decimal/mixed-radix checking (pp.74-75).

## open_questions
* Table I reports rectangular dimensions rather than computed scalar areas, so the merge pass must not multiply the printed dimensions.
* The paper does not identify the comparator implementation used by any residue checker.
* The paper does not map either Table I Res 15 layout uniquely to the shipped z196 4:2-CSA generator.
* “Almost 100%” duplication coverage has no quantified fault model beyond common transients and comparator exposure.
