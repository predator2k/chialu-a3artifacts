---
handle: sarwar2018
citation: S. S. Sarwar, S. Venkataramani, A. Ankit, A. Raghunathan, K. Roy, "Energy-Efficient Neural Computing with Approximate Multipliers", ACM Journal on Emerging Technologies in Computing Systems, vol. 14, no. 2, 2018
actual_citation: same
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC]
formats: [int12, int8, int4]
authority: incremental
pages_read: 23 / 23
---

## summary
The document proposes Alphabet Set Multipliers (ASMs), multiplier-less neurons, and contracted multiplier-less neurons for neural-network inference. Reduced alphabet sets constrain weights to shift-and-add-supported values, while retraining and assisted bit-precision scaling recover classification accuracy. The evaluated designs reduce neuron power/area under iso-speed conditions, although memory energy limits system-level savings.

## families
### approximate_mac_nn  (role: proposes)
mechanism: Neural-network weights are restricted to values supported by reduced alphabet sets, and the network is retrained with those constraints. Training starts without constraints, restores the converged network, and retries constrained retraining with increasing alphabet counts until the quality constraint is met. Assisted training first trains at 64-bit precision and then rounds weights/inputs to the target fixed-point width during retraining. Mixed ASMs assign larger alphabet sets only to significant concluding layers.
choices:
  multiplier_source: alphabet_set_shared   # p.5
  retraining: true   # p.9
new_choices:
  bit_precision_scaling: assisted_training — full-precision training precedes target-width rounding and retraining   # p.11
  approximation_placement: uniform_or_layer_mixed — one alphabet is used in early layers and larger sets in concluding layers   # p.18
slots:
  none
parameters: 12-, 8-, and 4-bit fixed-point weights/inputs excluding sign; alphabet counts 1, 2, and 4; sets {1}, {1,3}, and {1,3,5,7}   # pp.5,11,19
results:
| metric | value | unit | technology / device | baseline | condition | page |
| classification accuracy | 90.60 | % | UNKNOWN; 2018 | 90.71% conventional 12-bit NN | face detection, 12-bit, {1,3,5,7} | p.10 |
| classification accuracy | 90.49 | % | UNKNOWN; 2018 | 90.71% conventional 12-bit NN | face detection, 12-bit, {1} | p.10 |
| classification accuracy | 90.23 | % | UNKNOWN; 2018 | 90.66% conventional 8-bit NN | face detection, 8-bit, {1} | p.10 |
| classification accuracy | 97.33 | % | UNKNOWN; 2018 | 97.68% conventional 12-bit NN | MNIST, 12-bit, {1} | p.10 |
| classification accuracy | 97.18 | % | UNKNOWN; 2018 | 97.56% conventional 8-bit NN | MNIST, 8-bit, {1} | p.10 |
| classification accuracy | 96.31 | % | UNKNOWN; 2018 | 97.32% conventional 4-bit NN | MNIST, 4-bit, {1} | p.13 |
| maximum accuracy loss | ∼2.4 | % | UNKNOWN; 2018 | conventional neuron of equivalent precision | ANN applications, 4-bit ASM | p.15 |
errors_and_checks: Accuracy is measured as application classification accuracy; constrained retraining must satisfy K ≥ J × Q. Maximum reported loss against equivalent-precision conventional neurons is ∼0.63%, ∼0.84%, and ∼2.4% for 12-, 8-, and 4-bit ANN implementations.   # pp.9,15
conditions: Reduced alphabets rely on neural-network error resilience and constrained retraining. Four-bit precision without assisted training can fail to converge, while assisted training gives reasonable accuracy through 4 bits. CNN accuracy degrades by ∼4% for CIFAR10 and ∼7% for CIFAR100 at 4 bits even without multiplier approximation. Increasing hidden neurons to recover iso-accuracy removes the energy benefit for 12-/8-bit designs and increases energy for 4-bit designs.   # pp.6,11,15,19
evidence: Algorithm 2; Figures 7, 9, 12, 17, and 18; Tables 2, 3, and 5; §§4.3–4.7 and 6.1, 6.6–6.7

## new_families
### alphabet_set_multiplier  (domain: approx: approximate multipliers, closest: approximate_mac_nn, why_not: approximate_mac_nn describes application-level selection and retraining rather than the shared precomputer/select/shift/add multiplier structure)
mechanism: The multiplier decomposes a weight into 4-bit quartets. A precomputer generates input multiples for a selected alphabet set, control logic selects and shifts supported multiples, and an adder combines quartet products. Fewer than the eight exact alphabets omit weight quartets, so training maps unsupported values to nearest supported values. Computation Sharing Multiplication shares one precomputer among four parallel neuron multipliers. A one-alphabet {1} design removes the precomputer/select logic; a 4-bit version also removes the final addition.
choices: quartet_width: {4}; alphabet_set: {{1}, {1,3}, {1,3,5,7}, {1,3,5,7,9,11,13,15}}; precomputer_sharing: {private, shared}; neurons_per_precomputer: Int[1..4:1]; final_addition: Bool; unsupported_weight_handling: {nearest_supported_constrained_training}   # pp.4–6,10–13
results:
| metric | value | unit | technology / device | baseline | condition | page |
| minimum delay | 0.34 | ns | 45nm; 2018 | 0.38 ns conventional neuron | 12-bit ASM-based neuron | p.17 |
| power | 4.748 | mW | 45nm; 2018 | 6.231 mW conventional neuron | 12-bit ASM-based neuron | p.17 |
| area | 11300 | unit | 45nm; 2018 | 16904 unit conventional neuron | 12-bit ASM-based neuron | p.17 |
| minimum delay | 0.3 | ns | 45nm; 2018 | 0.31 ns conventional neuron | 8-bit ASM-based neuron | p.17 |
| power | 3.679 | mW | 45nm; 2018 | 4.958 mW conventional neuron | 8-bit ASM-based neuron | p.17 |
| area | 7507 | unit | 45nm; 2018 | 10776 unit conventional neuron | 8-bit ASM-based neuron | p.17 |
| minimum delay | 0.21 | ns | 45nm; 2018 | 0.22 ns conventional neuron | 4-bit ASM-based neuron | p.17 |
| power | 2.409 | mW | 45nm; 2018 | 2.894 mW conventional neuron | 4-bit ASM-based neuron | p.17 |
| area | 3476 | unit | 45nm; 2018 | 4784 unit conventional neuron | 4-bit ASM-based neuron | p.17 |
| power reduction | ∼33 / ∼32 / ∼25 | % | 45nm; 2018 | conventional 12-/8-/4-bit neurons | one-alphabet MAN, iso-speed | p.17 |
| area reduction | ∼33 / ∼34 / ∼27 | % | 45nm; 2018 | conventional 12-/8-/4-bit neurons | one-alphabet MAN, iso-speed | p.17 |
| system energy saving | 1 / 2.5 | % | 45nm SRAM; 2018 | conventional neuron system | large on-chip SRAM, 4-/12-bit synapses | p.20 |
| system energy saving | 4–9 | % | 45nm SRAM; 2018 | conventional neuron system | SRAM sized for compressed network | p.20 |
evidence: Figures 2, 3, 8, 10, and 11; Table 8; §§3, 4.6, 4.8–4.9, and 6.2–6.4, 6.8

## space_gaps
* approximate_mac_nn needs a multiplier slot that can be filled by alphabet_set_multiplier.   # pp.4–6
* approximate_mac_nn precision_scaling lacks assisted full-precision training followed by target-width retraining.   # p.11
* The approximate-multiplier vocabulary lacks reduced-alphabet shift/add multiplication with shared precomputation.   # pp.4–6

## open_questions
* Table 8 reports area in “unit” without defining the physical unit.
* The conventional multiplier architecture is selected by the synthesis tool under a low-power criterion and is otherwise unspecified.   # p.17
