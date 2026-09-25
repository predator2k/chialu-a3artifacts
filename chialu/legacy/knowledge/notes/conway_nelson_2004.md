---
handle: conway_nelson_2004
citation: Conway, Nelson, "Improved RNS FIR Filter Architectures", IEEE Transactions on Circuits and Systems II, 2004
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [rns, twos_complement]
authority: incremental
pages_read: 26-28 / 3
---

## summary
The paper proposes a transpose RNS FIR architecture using any pairwise relatively prime set of moduli of the forms 2^n−1, 2^n, and 2^n+1. # p.26
A delay-aware algorithm constructs carry-save trees for each modulus and supports exhaustive modulus-set selection by stage area-delay product. # pp.26-28
For a 16-tap filter with a 20–40 b dynamic range, the selected sets provide a reported 35% to 60% area-delay-product gain over equivalent 2’s-complement stages. # p.28

## families
### rns_channel_arithmetic  (role: extends)
mechanism: Independent channels use pairwise relatively prime moduli of the forms 2^n−1, 2^n, and 2^n+1. Modulo-2^n operations require no reduction. Higher-weight partial-product bits in the other channels fold into low columns; modulo 2^n+1 multiplication feeds back one inverted bit per product term. A modified carry-save-tree algorithm incorporates this feedback and combines constant terms. # pp.26-27
choices:
  modulus_form: "{pow2_minus_1, pow2, pow2_plus_1} [outside domain]"   # p.26
  channel_width_n: "3–8 [outside domain]"   # p.26
  multiplier_reduction: csa_with_periodic_folding   # pp.26-27
new_choices:
  modulus_set_selection: exhaustive_minimum_area_delay_product — selects a pairwise relatively prime modulus combination from per-modulus stage costs   # pp.26-28
  modulus_set_cardinality: unrestricted — any number satisfying the dynamic-range requirement, rather than only the common three-modulus set   # p.28
slots:
  modular_adder: UNKNOWN   # p.27
parameters: Moduli of 3 to 8 bits are searched; example set {5, 7, 17, 31, 32, 33}. # p.26
results: none reported separately from the FIR-stage results.
errors_and_checks: none
conditions: Every selected modulus is pairwise relatively prime. # pp.26,28 The modulus set must satisfy the required dynamic range. # pp.27-28 The restricted forms permit single-bit folding or no reduction, whereas general moduli are outside the proposed architecture. # p.26
evidence: Section II; Figs. 1-2; Tables I-II; Section III Tables IV and VI.

### carry_save_datapath  (role: instantiates)
mechanism: Each transpose stage places multiplier partial-product bits and the carry-save number from the previous stage into one carry-save tree. The construction algorithm accounts for distinct full-adder input-to-output delays and is modified for the feedback required by 2^n±1 moduli. Full adders/half adders implement the evaluated trees, although the method also permits 4-2 compressors or other counters. # pp.26-27
choices:
  compressor: 3_2   # pp.26-27
  assimilation_point: end_of_chain   # p.27
  accumulator_redundant: true   # pp.26-27
new_choices:
  tree_construction: delay_aware_algorithmic — minimizes the critical path using the different delays through each tree component   # p.26
slots:
  assimilator: UNKNOWN   # p.27
parameters: FA area 2 units; HA area 1 unit; one FF bit area 2 units; delay measured in XOR gate delays. # p.26
results: none reported separately from the complete transpose stages.
errors_and_checks: none
conditions: The tree generator must incorporate wrapped feedback bits and accumulated constants for 2^n±1 channels. # pp.26-27
evidence: Section II-A; Figs. 1-2; Tables I-II.

### rns_dsp_datapath  (role: proposes)
mechanism: A transpose FIR filter performs each channel’s multiply-accumulate sequence with a modulo carry-save tree. Delay elements retain the carry-save result between stages. Per-modulus area/delay costs drive exhaustive selection of the restricted modulus set for the filter’s required dynamic range. Binary-to-RNS conversion is simplified for these moduli; the paper cites a separate output-conversion architecture. # pp.26-28
choices:
  kernel: fir   # pp.26-28
new_choices:
  filter_structure: transpose — each stage combines its product terms with the carry-save value from the preceding stage   # p.26
  modulus_cost_objective: stage_area_delay_product — the modulus set minimizes the area-delay product of one transpose FIR stage   # pp.26-28
slots:
  none
parameters: 16-tap comparison; 20–40 b dynamic ranges; 40-b range permits accumulation of 256 16×16 multiplications. # pp.27-28
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area-delay-product gain | 35% to 60% | % | UNKNOWN; result year 2004 | equivalent 2’s-complement stage | 16-tap filter; dynamic range 20–40 b | p.28 |
| baseline delay disadvantage | 50% | slower | UNKNOWN; result year 2004 | proposed RNS stage | best Table IV case | p.28 |
| baseline area disadvantage | 20% | greater area | UNKNOWN; result year 2004 | proposed RNS stage | best Table IV case | p.28 |
| area | 578 | units | UNKNOWN; result year 2004 | 2’s-complement MAC: 597 units | RNS MAC; 40-b range; 16×16 products | p.28 |
| delay | 7 | XOR delays | UNKNOWN; result year 2004 | 2’s-complement MAC: 9 XOR delays | RNS MAC; 40-b range; 16×16 products | p.28 |
| area reduction | 33% | less area | UNKNOWN; result year 2004 | common three-modulus set | 24-b dynamic-range stage | p.28 |
| speed improvement | 30% | faster | UNKNOWN; result year 2004 | common three-modulus set | 24-b dynamic-range stage | p.28 |
errors_and_checks: none
conditions: The comparison uses an equivalent 2’s-complement transpose stage with Booth encoding and an optimized adder tree. # p.27 The reported gains apply to restricted-modulus sets selected for the specified dynamic range. # pp.27-28 The paper focuses on dedicated RNS filters and presents the 16×16 MAC case only as an alternative-use comparison. # p.28
evidence: Sections II-III; Tables III-VI; Conclusion.

## new_families
none

## space_gaps
* rns_channel_arithmetic lacks a heterogeneous `modulus_set` choice for combining pow2_minus_1/pow2/pow2_plus_1 channels in one datapath. # pp.26,28
* rns_channel_arithmetic lacks choices for modulus-set cardinality and cost-driven exhaustive selection. # pp.26-28
* rns_dsp_datapath lacks a reduction/accumulator slot for the carry_save_datapath used inside each channel. # pp.26-27
* rns_dsp_datapath lacks a transpose/direct filter-structure choice. # p.26

## open_questions
* The exact numerical entries and modulus sets in Tables I-VI are not recoverable from the supplied document transcription.
* The operand width associated with the “best result” in Table IV is unreadable, so the note does not infer it.
* Table V identifies a 0.7-μm CMOS synthesis process, but its numerical area/time entries are unreadable in the supplied text.
