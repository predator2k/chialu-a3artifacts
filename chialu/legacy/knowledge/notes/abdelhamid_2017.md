---
handle: abdelhamid_2017
citation: Garner, "The Residue Number System", IRE Transactions on Electronic Computers, 1959
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_DOT_ACC]
formats: [rns32, int28, int6, int32, fp6, fp32]
authority: incremental
pages_read: 1-5 / 5
---

## summary
The document applies a four-channel residue number system to neural-network multiplication/accumulation and implements modular adders, multipliers, input conversion, comparison, and ReLU blocks in LP65nm CMOS (pp.1-4). The document reports block-level synthesis estimates, SVHN test errors, and an analytical RNS energy break-even point rather than an integrated end-to-end accelerator result (p.4).

## families
### rns_channel_arithmetic  (role: instantiates)
mechanism: Each integer is represented by four residues over the conjugate moduli set `{2^n±1, 2^(n+1)±1}`. Addition and multiplication execute independently in each channel. Modulo multiplication circularly folds partial products into the channel width and reduces them with a modulo carry-save tree before a modulo adder produces the nonredundant product (pp.1,3).
choices:
  modulus_form: {pow2_minus_1, pow2_plus_1}   # pp.1,3
  channel_width_n: 7   # p.1
  pow2_plus_1_encoding: diminished_one   # p.3
  multiplier_reduction: csa_with_periodic_folding   # p.3
new_choices:
  moduli_set: `{2^n±1, 2^(n+1)±1}` — selects the heterogeneous four-channel conjugate-moduli system   # p.1
slots:
  modular_adder: end_around_carry [modulus={mod_2n_minus_1, mod_2n_plus_1_diminished_one}]   # p.3
parameters: `n=7`; channel storage widths `7+8+8+9=32 bits`; representational range `[0,357886635]`, described as a 28-bit unsigned-integer range   # p.1
results:
| metric | value | unit | technology / device | baseline | condition | page |
| power | 1.56 | mW | commercial LP65nm CMOS, 2017 | Multiplier32: 3.04 mW | MultiplierRNS at 250 MHz | p.4 |
| frequency | 250 | MHz | commercial LP65nm CMOS, 2017 | Multiplier32: 250 MHz | MultiplierRNS | p.4 |
| slack | 95.4 | ps | commercial LP65nm CMOS, 2017 | Multiplier32: 7.1 ps | MultiplierRNS at 250 MHz | p.4 |
| power | 2.6 | mW | commercial LP65nm CMOS, 2017 | UNKNOWN | ConvertToRNS at 250 MHz | p.4 |
| frequency | 250 | MHz | commercial LP65nm CMOS, 2017 | UNKNOWN | ConvertToRNS | p.4 |
| slack | 1.1 | ps | commercial LP65nm CMOS, 2017 | UNKNOWN | ConvertToRNS at 250 MHz | p.4 |
errors_and_checks: none
conditions: Residue channels eliminate carry propagation between moduli, but operations are restricted to positive integers within the fixed modulus range (pp.1-2). Conversion incurs substantial arithmetic overhead, so the proposed inference flow avoids output conversion by selecting the maximum output in RNS (p.2).
evidence: §2.1, §2.2, §4, §5, §6.1; Table 2; Figures 2-3 (pp.1-4)

### end_around_carry  (role: instantiates)
mechanism: Modulo `2^n−1` addition feeds the binary adder carry-out back as an increment. Modulo `2^n+1` addition uses diminished-1 operands or an output correction. A parallel-prefix carry network propagates the carry in four levels, followed by modulus-dependent end-around correction using `cout` or its complement (p.3).
choices:
  modulus: {mod_2n_minus_1, mod_2n_plus_1_diminished_one}   # p.3
new_choices:
  none
slots:
  none
parameters: `n=7`; four carry-propagation levels in the illustrated modulo `2^7−1` adder   # p.3
results:
| metric | value | unit | technology / device | baseline | condition | page |
| power | 1.18 | mW | commercial LP65nm CMOS, 2017 | Adder32: 1.05 mW | AdderRNS at 625 MHz | p.4 |
| frequency | 625 | MHz | commercial LP65nm CMOS, 2017 | Adder32: 625 MHz | AdderRNS | p.4 |
| slack | 17.6 | ps | commercial LP65nm CMOS, 2017 | Adder32: 15.9 ps | AdderRNS at 625 MHz | p.4 |
errors_and_checks: none
conditions: The correction polarity depends on whether the designated modulus is `2^n−1` or `2^n+1` (p.3).
evidence: §5.1; Figure 2; Table 2 (pp.3-4)

### rns_scaling_comparison  (role: extends)
mechanism: Unsigned comparison subtracts `B` from `A` modulo the odd dynamic range `M`. The wrapped and unwrapped differences have different parity, so combinational reconstruction of the RNS number’s parity determines ordering. A trimmed half-comparator fixes the threshold at `M/2` for ReLU, while the full comparator selects the maximum final-layer output (p.2).
choices:
  operation: compare   # p.2
  method: parity_of_modular_difference [outside domain]   # p.2
  exactness: exact   # p.2
new_choices:
  comparison_threshold: {variable_operand, fixed_M_over_2} — distinguishes the full comparator from the trimmed ReLU half-comparator   # p.2
slots:
  none
parameters: four residues `(x1,x1*,x2,x2*)`; full comparator for final-layer maximum; half-comparator for threshold `M/2`   # p.2
results:
| metric | value | unit | technology / device | baseline | condition | page |
| power | 0.88 | mW | commercial LP65nm CMOS, 2017 | UNKNOWN | ReLU-RNS at 156 MHz | p.4 |
| frequency | 156 | MHz | commercial LP65nm CMOS, 2017 | UNKNOWN | ReLU-RNS | p.4 |
| slack | 109.5 | ps | commercial LP65nm CMOS, 2017 | UNKNOWN | ReLU-RNS at 156 MHz | p.4 |
| power | 1.67 | mW | commercial LP65nm CMOS, 2017 | UNKNOWN | CompareRNS at 156 MHz | p.4 |
| frequency | 156 | MHz | commercial LP65nm CMOS, 2017 | UNKNOWN | CompareRNS | p.4 |
| slack | 93.1 | ps | commercial LP65nm CMOS, 2017 | UNKNOWN | CompareRNS at 156 MHz | p.4 |
errors_and_checks: Exhaustive testing suggested that the cited Sousa circuit was incorrect for some of its approximately 3 billion inputs, so the authors modified the parity logic; no residual error rate is reported (p.2).
conditions: The parity comparison requires odd `M` and unsigned values (p.2). The half-comparator applies only to the fixed ReLU threshold `M/2` (p.2).
evidence: §2.2, §3, §6.1; Figure 1; Table 2 (pp.2,4)

### rns_dnn_accelerator  (role: proposes)
mechanism: Network weights and activations remain in the four-channel RNS representation across convolutional and fully connected layers. RNS modular multipliers/adders execute MACs, an RNS comparison implements ReLU, and a final RNS maximum returns the discrete output index without reverse conversion (pp.1-2).
choices:
  channel_width_n: 7   # p.1
  activation_handling: compare_in_rns [outside domain]   # p.2
new_choices:
  output_conversion: {reverse_convert, rns_argmax_only} — selects whether inference produces a binary value or only the winning output index   # p.2
slots:
  none
parameters: 8-layer network with 7 CNN layers and 1 FC layer; `(32,32)` and `(6,6)` weight/activation experiments; 15 training epochs; SVHN dataset   # p.4
results:
| metric | value | unit | technology / device | baseline | condition | page |
| SVHN test error | 3.95 | % | TensorFlow/Tensorpack experiment, 2017 | UNKNOWN | `(32,32)-FP` | p.4 |
| SVHN test error | 6.69 | % | TensorFlow/Tensorpack experiment, 2017 | `(32,32)-FP`: 3.95% | `(6,6)-FP` | p.4 |
| SVHN test error | 4.54 | % | TensorFlow/Tensorpack experiment, 2017 | `(32,32)-FP`: 3.95% | `(32,32)-Int` | p.4 |
| SVHN test error | 7.07 | % | TensorFlow/Tensorpack experiment, 2017 | `(32,32)-FP`: 3.95% | `(6,6)-Int` | p.4 |
| estimated break-even fan-in `X` | `>0.98` | inputs | commercial LP65nm CMOS estimates, 2017 | non-RNS MAC and ReLU | fully connected layer; memory-access costs excluded | p.4 |
errors_and_checks: The document reports empirical SVHN test error rather than a bound on arithmetic error; negative integers wrap to positive residues, and the reason for the integer-network accuracy change remains unclear (p.4).
conditions: The approach assumes positive integer weights/activations within `M`, discrete outputs, and a network form that permits final RNS argmax instead of reverse conversion (pp.2,4). The break-even estimate excludes memory-access costs and uses separate block-level energy estimates rather than an integrated implementation (p.4).
evidence: §1, §2.2, §6.2, §6.3, §7; Tables 2-3 (pp.1-4)

## new_families
none

## space_gaps
* `rns_scaling_comparison.method` lacks `parity_of_modular_difference`, which is the implemented comparison method (p.2).
* `rns_dnn_accelerator.activation_handling` lacks comparison/ReLU performed directly in RNS (p.2).
* `rns_channel_arithmetic` lacks an explicit heterogeneous conjugate-moduli-set choice for `{2^n±1, 2^(n+1)±1}` (p.1).

## open_questions
* The parallel-prefix topology used by the modulo adder is not named (p.3).
* The document does not report an integrated end-to-end RNS inference implementation; §7.1 identifies that integration as future work (p.4).
* Table 2 does not report voltage, switching activity, or per-operation energy used in the break-even calculation (p.4).
