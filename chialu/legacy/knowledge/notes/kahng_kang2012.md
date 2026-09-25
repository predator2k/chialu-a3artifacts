---
handle: kahng_kang2012
citation: A. B. Kahng, S. Kang, "Accuracy-Configurable Adder for Approximate Arithmetic Designs", 49th Design Automation Conference (DAC), pp. 820-825, 2012
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int8, int16, int32]
authority: landmark
pages_read: 820-825 / 6
---

## summary
The paper proposes an accuracy-configurable approximate adder that cuts carry chains and enables runtime selection between approximate and accurate operation. Error-detection/increment stages restore exact results or can be power-gated to trade accuracy for power. Implementations report up to 24.6% throughput improvement and 37.0% power reduction against a conventional CLA, and pipelined runtime configuration averages up to 35.8% power reduction under varying accuracy requirements. (pp.820-825)

## families
### segmented_carry_speculative  (role: proposes)
mechanism: An N-bit addition is divided into N/k−1 overlapping submodules. Each submodule reads 2k operand bits and emits k result bits, except the final submodule, which emits 2k bits. The overlap supplies a k-bit carry-propagation window while carry chains between result segments are cut. A segment error is detected from its carry-in and an all-one lower result; an incrementor adds compensation in an extra cycle. (pp.821-822)
choices:
  sub_adder_width: 2k [outside domain]   # p.821
  prediction_window: k [outside domain]   # p.821
  carry_in_scheme: propagate_window   # p.821
  correction: extra_cycle   # p.822
new_choices:
  overlap_width: k — number of operand bits shared by adjacent 2k-bit sub-adders   # p.821
slots:
  sub_adder: UNKNOWN   # pp.821-823
parameters: N-bit adder; k is half the carry-chain depth; evaluated at N=16 with k={2,3,4,5} and at N=32 with k=4; correction costs one additional cycle when an error is detected   # pp.821-824
results:
| metric | value | unit | technology / device | baseline | condition | page |
| min. clock period | [180, 190, 220, 230] for k=[2,3,4,5] | ps | TSMC 65GP / 2012 | conventional CLA | 16-bit ACA with recovery overhead reported separately | p.823 |
| area | [550, 990, 920, 840] for k=[2,3,4,5] | um2 | TSMC 65GP / 2012 | none | 16-bit ACA | p.823 |
| pass rate | [55.3, 82.8, 94.0, 98.1] for k=[2,3,4,5] | % | TSMC 65GP / 2012 | correct result | one million random cycles | p.823 |
| throughput improvement | [11.3, 24.6, 22.3, 21.4] for k=[2,3,4,5] | % | TSMC 65GP / 2012 | conventional CLA | includes error-recovery overhead | p.823 |
| area | 923 | um2 | TSMC 65GP / 2012 | CLA 910 um2; Lu 1356 um2; ETAI 576 um2; ETAIIM 678 um2 | 16-bit ACA, 8-bit carry-chain width | p.823 |
| min. clock period | 200 | ps | TSMC 65GP / 2012 | CLA 280 ps; Lu 210 ps; ETAI 200 ps; ETAIIM 260 ps | 16-bit comparison | p.823 |
| pass rate | 94.1 | % | TSMC 65GP / 2012 | CLA 100%; Lu 99.2%; ETAI 10.0%; ETAIIM 97.0% | 16-bit comparison | p.823 |
| area overhead for EDC | 28 | % | TSMC 65GP / 2012 | ACA without EDC | Lu 75%; ETAIIM 15% | p.823 |
| total power reduction | 37.0 | % | TSMC 65GP / 2012 | CLA | ACCamp=0.970 with voltage scaling | p.824 |
| total power reduction | 36.4 | % | TSMC 65GP / 2012 | Lu’s adder | ACCamp=0.970 with voltage scaling | p.824 |
| total power reduction | 15.9 | % | TSMC 65GP / 2012 | ETAIIM | ACCamp=0.970 with voltage scaling | p.824 |
| PSNR | 24.5 | dB | TSMC 65GP / 2012 | accurate CLA power | Gaussian smoothing with ACA consuming 50% of accurate CLA power | p.824 |
errors_and_checks: For random inputs, a sub-adder error occurs when its lower k output bits are all 1 and the following lower segment produces a carry. AND gates detect the condition, and an incrementor produces an error-free output; the variable-latency implementation stalls and uses one recovery cycle. The reported accuracy measures include pass rate, ACCamp and ACCinf.   # pp.821-823
conditions: Smaller k reduces clock period but lowers pass rate. For k<N/4, one correction stage cannot restore 100% accuracy within one clock, so multiple correction stages are required.   # pp.821-822
evidence: §2.1-2.2, Figures 2-4, Tables 1, 3 and 4, Figures 7-8 (pp.821-824)

### accuracy_configurable  (role: proposes)
mechanism: A pipeline first produces an approximate sum, then applies carry-error corrections in later stages. Each successive stage increases accuracy. Runtime modes power-gate selected later correction stages, so the same hardware provides an exact mode and several approximate modes. The two-stage design uses k=N/4; the demonstrated 32-bit design uses k=4 and four stages. (pp.822-824)
choices:
  mode_count: 4   # p.824
  reconfig_grain: correction_stage   # pp.822-824
  error_detection: true   # p.822
  power_gate_unused: true   # pp.822-824
new_choices:
  correction_depth: Int[1..4:1] — number of enabled pipeline correction stages   # pp.822-824
slots:
  none
parameters: two-stage implementations at N={8,16,32} with k=N/4; four-stage implementation at N=32, k=4; mode-1 enables every stage and modes 2-4 successively gate later stages   # pp.824-825
results:
| metric | value | unit | technology / device | baseline | condition | page |
| approximate-pipelined area | [576, 1171, 2420] for N=[8,16,32] | um2 | TSMC 65GP / 2012 | conventional [459,1082,2252] um2 | accurate mode, two stages | p.824 |
| approximate-pipelined clock period | [0.312, 0.358, 0.414] for N=[8,16,32] | ns | TSMC 65GP / 2012 | conventional [0.313,0.357,0.404] ns | accurate mode at 1.0V | p.824 |
| approximate-pipelined total power | [0.564, 1.669, 2.914] for N=[8,16,32] | mW | TSMC 65GP / 2012 | conventional [0.557,1.558,2.860] mW | accurate mode at 2.5GHz with voltage scaling | p.824 |
| total power | [5.962, 4.683, 3.691, 2.588] for modes=[1,2,3,4] | mW | TSMC 65GP / 2012 | conventional pipelined adder | 32-bit, four-stage ACA | p.824 |
| power reduction | [-11.5, 12.4, 31.0, 51.6] for modes=[1,2,3,4] | % | TSMC 65GP / 2012 | conventional pipelined adder | 32-bit, four-stage ACA | p.824 |
| ACCamp maximum | [1.000, 0.998, 0.991, 0.983] for modes=[1,2,3,4] | unitless | TSMC 65GP / 2012 | exact result | one million random cycles | p.824 |
| ACCinf maximum | [1.000, 0.960, 0.925, 0.900] for modes=[1,2,3,4] | unitless | TSMC 65GP / 2012 | exact result | one million random cycles | p.824 |
| power reduction | up to 44.5; 30.0 average | % | TSMC 65GP / 2012 | conventional pipelined adder | SPEC 2006; accuracy uniformly varies over 0.99≤ACCamp≤1.00 | p.825 |
| power reduction | up to 47.1; 35.8 average | % | TSMC 65GP / 2012 | conventional pipelined adder | SPEC 2006; accuracy uniformly varies over 0.95≤ACCinf≤1.00 | p.825 |
errors_and_checks: Mode-1 is exact. Modes 2-4 omit progressively more correction stages and therefore permit residual errors; random-pattern maxima are reported with ACCamp/ACCinf, and per-benchmark results show input-dependent accuracy.   # pp.824-825
conditions: Accurate mode consumes 11.5% more power than the conventional four-stage adder because recovery circuits remain present. Approximate modes save power by gating correction stages. Real SPEC patterns produce different accuracy by benchmark and higher accuracy than random patterns in the reported experiments.   # pp.824-825
evidence: §2.3, §3.5, Figures 5-6 and 9-10, Tables 5-7 (pp.822-825)

### error_analysis_quality  (role: extends)
mechanism: ACCamp measures amplitude accuracy as 1−|Rc−Re|/Rc. ACCinf measures information accuracy as 1−Be/Bw, where Be is the number of erroneous bits and Bw is the data width. Average metric values over the simulation combine error rate and error significance. (p.823)
choices:
  metric: ACCamp / ACCinf [outside domain]   # p.823
  model: monte_carlo   # pp.822-825
new_choices:
  data_semantics: {amplitude, information} — selects numerical-difference or Hamming-distance accuracy   # p.823
slots:
  none
parameters: one million random cycles and operand traces from ADD instructions in eight SPEC 2006 benchmarks   # pp.822,824-825
results:
| metric | value | unit | technology / device | baseline | condition | page |
| ACCamp maximum | 0.997 | unitless | TSMC 65GP / 2012 | CLA 1.000; Lu 0.998; ETAI 0.999; ETAIIM 0.999 | 16-bit comparison | p.823 |
| ACCinf maximum | 0.993 | unitless | TSMC 65GP / 2012 | CLA 1.000; Lu 0.999; ETAI 0.694; ETAIIM 0.996 | 16-bit comparison | p.823 |
errors_and_checks: ACCamp captures error amplitude, while ACCinf captures Hamming distance. Pass rate separately records the proportion of exactly correct outputs.   # p.823
conditions: ACCamp is intended for amplitude data such as image/sound samples. ACCinf is intended for information data where the number of incorrect bits matters.   # p.823
evidence: §3.2, Tables 2 and 4 (p.823)

## new_families
none

## space_gaps
* `segmented_carry_speculative.sub_adder_width` and `prediction_window` need symbolic parameter values such as 2k and k, because the proposed architecture defines widths relationally rather than as one fixed integer. (p.821)
* `error_analysis_quality.metric` lacks ACCamp and ACCinf, which the paper defines for amplitude error and bit-error significance. (p.823)
* `accuracy_configurable` lacks a correction-depth choice for selecting how many pipelined error-correction stages remain active. (pp.822-824)

## open_questions
* The paper does not identify the synthesized structure used inside each ACA sub-adder, so `sub_adder` remains UNKNOWN.
* Figure 7 states a fixed clock period of 0.25ns, while the accompanying text states 0.30ns. (p.823)
* ACCamp is defined using division by Rc, but the paper does not state how Rc=0 is handled. (p.823)
