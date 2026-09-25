---
handle: ebrahimi2020
citation: F. Ebrahimi-Azandaryani, O. Akbari, M. Kamal, A. Afzali-Kusha, M. Pedram, "Block-Based Carry Speculative Approximate Adder for Energy-Efficient Applications", IEEE Transactions on Circuits and Systems II, vol. 67, no. 1, pp. 137-141, 2020
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int8, int16, int32]
authority: incremental
pages_read: 1-5 / 5
---

## summary
The document proposes BCSA, which partitions an adder into non-overlapping parallel blocks and speculates each block carry from signals in the current/next blocks. BCSAERU adds an error-recovery unit that improves accuracy without extending the critical path. The evaluated variants trade block size/ERU overhead against ER/NMED/MRED, delay, energy, area, and image-processing quality. # p.1, p.3-p.5

## families
### segmented_carry_speculative  (role: proposes)
mechanism: BCSA uses ⌈n/l⌉ parallel l-bit summation blocks containing a sub-adder, Carry Predictor, and Select unit. The Select unit chooses between a speculated carry and the preceding sub-adder carry. The predictor uses operand signals from the current/next blocks, so the worst-case carry path spans two blocks and the average path is close to one block. BCSAERU repairs the first sum bit in the case where an incorrect speculative carry would affect that bit; the ERU is outside the critical path. # p.2-p.3
choices:
  sub_adder_width: {2 [outside domain], 4, 6, 8, 12, 16}   # p.3-p.4
  carry_in_scheme: carry_select_speculation   # p.2-p.3
  correction: {none, error_reduction_stage}   # p.3
new_choices:
  prediction_scope: current_and_next_block — identifies the blocks whose operand signals determine a speculative carry   # p.2
slots:
  sub_adder: {ripple_carry, carry_lookahead, parallel_prefix [topology=kogge_stone]}   # p.2
parameters: n = 8, 16, or 32 bits; l studied from 2 to 16 bits; hardware plots use l = 2, 4, 6, 8, 12, and 16; worst-case carry path = 2l bits; average carry path ≈ l bits; accuracy simulation uses 65,536 samples for 8-bit and 10 million samples for 16-/32-bit adders. # p.2-p.4
results:
| metric | value | unit | technology / device | baseline | condition | page |
| ER/NMED/MRED at l=2;4;8 | 12.42/607/621; 1.37/137/136; 0/0/0 | % / ×10^-4 / ×10^-4 | 15nm FinFET NanGate, 2020 | exact sum | HABA, n=8 | p.4 |
| ER/NMED/MRED at l=2;4;8 | 33.77/608/623; 4.29/155/157; 0.10/10/10 | % / ×10^-4 / ×10^-4 | 15nm FinFET NanGate, 2020 | exact sum | HABA, n=16 | p.4 |
| ER/NMED/MRED at l=2;4;8 | 51.23/625/644; 9.18/156/158; 0.29/10/10 | % / ×10^-4 / ×10^-4 | 15nm FinFET NanGate, 2020 | exact sum | HABA, n=32 | p.4 |
| ER/NMED/MRED at l=2;4;8 | 12.41/151/155; 1.36/9/9; 0/0/0 | % / ×10^-4 / ×10^-4 | 15nm FinFET NanGate, 2020 | exact sum | HABAERU, n=8 | p.4 |
| ER/NMED/MRED at l=2;4;8 | 33.77/154/157; 4.28/10/10; 0.1/0.04/0.04 | % / ×10^-4 / ×10^-4 | 15nm FinFET NanGate, 2020 | exact sum | HABAERU, n=16 | p.4 |
| ER/NMED/MRED at l=2;4;8 | 51.21/156/161; 9.17/10/10; 0.29/0.04/0.04 | % / ×10^-4 / ×10^-4 | 15nm FinFET NanGate, 2020 | exact sum | HABAERU, n=32 | p.4 |
| ER/NMED/MRED at l=2;4;8 | 30.06/605/707; 5.47/68/93; 0/0/0 | % / ×10^-4 / ×10^-4 | 15nm FinFET NanGate, 2020 | exact sum | GeAr, n=8 | p.4 |
| ER/NMED/MRED at l=2;4;8 | 61.77/625/730; 16.72/156/190; 0.68/10/12 | % / ×10^-4 / ×10^-4 | 15nm FinFET NanGate, 2020 | exact sum | GeAr, n=16 | p.4 |
| ER/NMED/MRED at l=2;4;8 | 65.37/625/730; 32.18/156/190; 2.25/10/12 | % / ×10^-4 / ×10^-4 | 15nm FinFET NanGate, 2020 | exact sum | GeAr, n=32 | p.4 |
| ER/NMED/MRED at l=2;4;8 | 15.54/606/646; 2.34/137/147; 0/0/0 | % / ×10^-4 / ×10^-4 | 15nm FinFET NanGate, 2020 | exact sum | RAP-CLA, n=8 | p.4 |
| ER/NMED/MRED at l=2;4;8 | 36.45/626/670; 8.54/129/154; 0.34/10/11 | % / ×10^-4 / ×10^-4 | 15nm FinFET NanGate, 2020 | exact sum | RAP-CLA, n=16 | p.4 |
| ER/NMED/MRED at l=2;4;8 | 55.71/625/670; 17.17/130/154; 1.12/10/11 | % / ×10^-4 / ×10^-4 | 15nm FinFET NanGate, 2020 | exact sum | RAP-CLA, n=32 | p.4 |
| ER/NMED/MRED at l=2;4;8 | 14.43/379/484; 5.46/68/93; 0/0/0 | % / ×10^-4 / ×10^-4 | 15nm FinFET NanGate, 2020 | exact sum | SARA, n=8 | p.4 |
| ER/NMED/MRED at l=2;4;8 | 35.05/417/531; 16.75/83/112; 6.09/5/7 | % / ×10^-4 / ×10^-4 | 15nm FinFET NanGate, 2020 | exact sum | SARA, n=16 | p.4 |
| ER/NMED/MRED at l=2;4;8 | 65.44/563/589; 35.88/83/112; 17.45/5/7 | % / ×10^-4 / ×10^-4 | 15nm FinFET NanGate, 2020 | exact sum | SARA, n=32 | p.4 |
| ER/NMED/MRED at l=2;4;8 | 18.73/167/185; 0/0/0; 0/0/0 | % / ×10^-4 / ×10^-4 | 15nm FinFET NanGate, 2020 | exact sum | BCSAERU, n=8 | p.4 |
| ER/NMED/MRED at l=2;4;8 | 47.86/172/190; 5.89/20/26; 0/0/0 | % / ×10^-4 / ×10^-4 | 15nm FinFET NanGate, 2020 | exact sum | BCSAERU, n=16 | p.4 |
| ER/NMED/MRED at l=2;4;8 | 74.66/172/189; 16.66/20/26; 0.39/0.1/0.07 | % / ×10^-4 / ×10^-4 | 15nm FinFET NanGate, 2020 | exact sum | BCSAERU, n=32 | p.4 |
| ER/NMED/MRED at l=2;4;8 | 27.47/395/428; 5.46/34/52; 0/0/0 | % / ×10^-4 / ×10^-4 | 15nm FinFET NanGate, 2020 | exact sum | BCSA, n=8 | p.4 |
| ER/NMED/MRED at l=2;4;8 | 60.98/417/554; 21.15/56/81; 6.20/2/3 | % / ×10^-4 / ×10^-4 | 15nm FinFET NanGate, 2020 | exact sum | BCSA, n=16 | p.4 |
| ER/NMED/MRED at l=2;4;8 | 87.62/417/554; 45.94/55/81; 18.04/3/4 | % / ×10^-4 / ×10^-4 | 15nm FinFET NanGate, 2020 | exact sum | BCSA, n=32 | p.4 |
| power overhead | about 3 | % | 15nm FinFET NanGate, 2020 | BCSA without ERU | ERU enabled | p.3 |
| area overhead | about 2 | % | 15nm FinFET NanGate, 2020 | BCSA without ERU | ERU enabled | p.3 |
| average delay increase | 5 / 7 | % | 15nm FinFET NanGate, 2020 | GeAr | BCSA / BCSAERU | p.4 |
| average energy increase | 4 / 5 | % | 15nm FinFET NanGate, 2020 | GeAr | BCSA / BCSAERU | p.4 |
| average area increase | 12 / 15 | % | 15nm FinFET NanGate, 2020 | SARA | BCSA / BCSAERU | p.4 |
| EDP reduction | 68 best; 13 worst | % | 15nm FinFET NanGate, 2020 | exact CLA | BCSA; MRED cost 0.055 best / 1e-6 worst | p.4 |
| cost-function improvement | about 50 | % | 15nm FinFET NanGate, 2020 | recently proposed approximate adders | energy/delay/area/output-quality cost function | p.1, p.5 |
| energy-efficiency gain | 14.4 | % | 15nm FinFET NanGate, 2020 | exact CLA | BCSA in sharpening/smoothing applications | p.4 |
| performance gain | 20 | % | 15nm FinFET NanGate, 2020 | exact CLA | BCSA in sharpening/smoothing applications | p.4 |
errors_and_checks: Accuracy is measured by ER/NMED/MRED against exact addition; no worst-case error bound is established. For n=8 and l=4, 94.5%/94.5%/100%/100%/100% of erroneous BCSA outputs have RED ≤5%/10%/20%/50%/100%; BCSAERU reports 100% at every threshold. The ERU detects the third carry-selection case and repairs the first sum bit, but no formal detection-coverage or false-alarm result is reported. # p.3-p.4
conditions: Predictor probabilities assume uniformly distributed zero/one operand bits. Larger blocks increase accuracy. BCSA targets error-resilient multimedia/image-processing/DSP/machine-learning applications. Hardware results use 15nm FinFET NanGate at 0.8V/25°C with up to 10M random stimuli; application multiplications remain exact and dominate much of the energy/delay. # p.1, p.3-p.4
evidence: §III, equations (7)-(11), Figs. 1-3, Tables I-II, §IV, Figs. 4-5, and conclusion. # p.2-p.5

## new_families
none

## space_gaps
* `segmented_carry_speculative.sub_adder_width` excludes the tested 2-bit block size. # p.3-p.4
* `segmented_carry_speculative` lacks a choice for prediction scope across the current/next blocks. # p.2

## open_questions
* The exact sub-adder family used for each reported synthesis point is not identified in the prose.
* Absolute delay/energy/area values in Fig. 4 are not recoverable from the supplied document text, so the merge pass must not derive them from the plotted image.
