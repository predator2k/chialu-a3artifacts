---
handle: jiang2016
citation: H. Jiang, J. Han, F. Qiao, F. Lombardi, "Approximate Radix-8 Booth Multipliers for Low-Power and High-Performance Operation", IEEE Transactions on Computers, vol. 65, no. 8, pp. 2638-2644, 2016
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int16]
authority: incremental
pages_read: 8 / 8
---

## summary
The paper proposes signed 16 × 16 approximate radix-8 Booth multipliers that approximate the 3Y recoding adder and optionally truncate low partial-product bits. ABM1 preserves accurate partial-product accumulation, while ABM2 combines approximate recoding with 9-bit or 15-bit truncation and a Wallace tree. The designs trade accuracy for lower delay/area/power and are evaluated in a 30-tap FIR filter. p.2, p.6

## families
### lower_part_approximate  (role: extends)
mechanism: Four adjacent 2-bit additions implement the lower eight bits of Y + 2Y. Each approximate cell reduces to one 3-input XOR because Cout = yi and Si+1 = yi+1, which removes carry propagation through the approximate section. A 7-bit precise adder implements the upper section. ARA8-2C partially compensates the most significant approximate cell by conditionally flipping Si; ARA8-2R adds full recovery for that cell. p.2–p.4
choices:
  lower_width: 8   # p.3
  lower_cell: approximate_2bit_xor [outside domain]   # p.2–p.3
  carry_to_upper: duplicated_bit [outside domain]   # p.2–p.3
new_choices:
  error_handling: {none, partial_compensation, full_recovery} — correction applied to the most significant approximate 2-bit cell   # p.3–p.4
slots:
  none
parameters: signed 16-bit Y; four approximate 2-bit cells; 7-bit precise upper adder; 10 million random 16-bit inputs; 2 ns clock; 1V; 25°C   # p.3–p.4
results:
| metric | value | unit | technology / device | baseline | condition | page |
| ARA8 delay | 0.73 | ns | STM 28nm CMOS (2016) | approximate-adder set | 8 approximated bits | p.4 |
| ARA8 area | 32 | um2 | STM 28nm CMOS (2016) | approximate-adder set | 8 approximated bits | p.4 |
| ARA8 power | 18.37 | µW | STM 28nm CMOS (2016) | approximate-adder set | 8 approximated bits | p.4 |
| ARA8 PDP | 13.41 | fJ | STM 28nm CMOS (2016) | approximate-adder set | 8 approximated bits | p.4 |
| ARA8 ADP | 23.36 | um2.ns | STM 28nm CMOS (2016) | approximate-adder set | 8 approximated bits | p.4 |
| ARA8 pass rate | 31.61 | % | STM 28nm CMOS (2016) | exact 3Y | 10 million random inputs | p.4 |
| ARA8 MED | 73.41 | none | STM 28nm CMOS (2016) | exact 3Y | 10 million random inputs | p.4 |
| ARA8-2C delay | 0.73 | ns | STM 28nm CMOS (2016) | approximate-adder set | partial compensation | p.4 |
| ARA8-2C power | 20.96 | µW | STM 28nm CMOS (2016) | approximate-adder set | partial compensation | p.4 |
| ARA8-2C MED | 41.79 | none | STM 28nm CMOS (2016) | exact 3Y | partial compensation | p.4 |
| ARA8-2R delay | 0.90 | ns | STM 28nm CMOS (2016) | approximate-adder set | full recovery | p.4 |
| ARA8-2R power | 20.42 | µW | STM 28nm CMOS (2016) | approximate-adder set | full recovery | p.4 |
| ARA8-2R MED | 18.37 | none | STM 28nm CMOS (2016) | exact 3Y | full recovery | p.4 |
errors_and_checks: The isolated approximate 2-bit cell has error rate 1/4 under equiprobable inputs and produces errors of +2 or -2. ARA8 has a calculated pass rate of (1 − 1/4)^4 = 31.64%; compensation/recovery circuits detect the four erroneous input patterns locally. p.3–p.4
conditions: The approximate cells are restricted to the less significant section because using them across all 16 bits can produce a large 3Y error. ARA8/ARA8-2C/ARA8-2R have lower PDP at comparable MED than the evaluated LOA/TRCA/IPPA/ETAII alternatives. IPPA requires immediate compensation in recoding and is less efficient in this role. p.3, p.5
evidence: §2; Table 2; Figs. 3–6; Table 4; Fig. 9, p.2–p.5

### approximate_booth  (role: proposes)
mechanism: Radix-8 recoding produces six signed partial products selected from −4Y, −3Y, −2Y, −Y, 0, Y, 2Y, 3Y and 4Y. The approximate lower-part adder generates 3Y, and a Wallace tree reduces the partial products. ABM1 uses ARA8-2R without truncation. ABM2 truncates 9 or 15 low partial-product bits and selects ARA8/ARA8-2C/ARA8-2R. The 15-bit variants add an average-error compensation value of 1 at bit 17. p.5–p.6
choices:
  radix: 8   # p.5
  approx_encoder_columns: 8   # p.3, p.6
  encoder: approximate_recoding_adder [outside domain]   # p.2–p.6
new_choices:
  partial_product_truncation_bits: {0, 9, 15} — number of low partial-product bits removed   # p.6
  truncation_compensation: {none, add_1_at_bit_17} — constant compensation used by 15-bit truncation variants   # p.6
  recoding_error_handling: {ARA8, ARA8-2C, ARA8-2R} — recoding-adder accuracy/hardware configuration   # p.6
slots:
  none
parameters: signed 16 × 16; radix 8; six partial products; 8 approximated recoding bits; 0/9/15 truncated bits; 4 ns clock; 1V; 25°C; 10 million random input combinations   # p.5–p.6
results:
| metric | value | unit | technology / device | baseline | condition | page |
| ABM1 delay | 2.38 | ns | STM 28nm CMOS (2016) | AcBM 2.99 ns | no truncation | p.7 |
| ABM1 area | 724 | um2 | STM 28nm CMOS (2016) | AcBM 737 um2 | no truncation | p.7 |
| ABM1 power | 363.3 | uW | STM 28nm CMOS (2016) | AcBM 371.9 uW | no truncation | p.7 |
| ABM1 PDP | 865.84 | fJ | STM 28nm CMOS (2016) | AcBM 1111.98 fJ | no truncation | p.7 |
| ABM1 NMED | 1.92 | 10−5 | STM 28nm CMOS (2016) | exact product | random inputs | p.7 |
| ABM1 pass rate | 55.937 | % | STM 28nm CMOS (2016) | exact product | random inputs | p.7 |
| ABM1 PRED | 99.77 | % | STM 28nm CMOS (2016) | RED below 2% | random inputs | p.7 |
| ABM2-C9 delay | 2.23 | ns | STM 28nm CMOS (2016) | AcBM 2.99 ns | 9-bit truncation | p.7 |
| ABM2-C9 area | 604 | um2 | STM 28nm CMOS (2016) | AcBM 737 um2 | 9-bit truncation | p.7 |
| ABM2-C9 power | 305.2 | uW | STM 28nm CMOS (2016) | AcBM 371.9 uW | 9-bit truncation | p.7 |
| ABM2-C9 PDP | 680.60 | fJ | STM 28nm CMOS (2016) | AcBM 1111.98 fJ | 9-bit truncation | p.7 |
| ABM2-C9 NMED | 4.43 | 10−5 | STM 28nm CMOS (2016) | exact product | random inputs | p.7 |
| ABM2-C9 PRED | 99.43 | % | STM 28nm CMOS (2016) | RED below 2% | random inputs | p.7 |
| ABM2-R9 delay | 2.41 | ns | STM 28nm CMOS (2016) | AcBM 2.99 ns | 9-bit truncation | p.7 |
| ABM2-R9 area | 606 | um2 | STM 28nm CMOS (2016) | AcBM 737 um2 | 9-bit truncation | p.7 |
| ABM2-R9 power | 305.5 | uW | STM 28nm CMOS (2016) | AcBM 371.9 uW | 9-bit truncation | p.7 |
| ABM2-R9 PDP | 736.26 | fJ | STM 28nm CMOS (2016) | AcBM 1111.98 fJ | 9-bit truncation | p.7 |
| ABM2-R9 NMED | 1.97 | 10−5 | STM 28nm CMOS (2016) | exact product | random inputs | p.7 |
| ABM2-R9 PRED | 99.74 | % | STM 28nm CMOS (2016) | RED below 2% | random inputs | p.7 |
| ABM2-15 delay | 2.07 | ns | STM 28nm CMOS (2016) | AcBM 2.99 ns | 15-bit truncation | p.7 |
| ABM2-15 area | 419 | um2 | STM 28nm CMOS (2016) | AcBM 737 um2 | 15-bit truncation | p.7 |
| ABM2-15 power | 206.8 | uW | STM 28nm CMOS (2016) | AcBM 371.9 uW | 15-bit truncation | p.7 |
| ABM2-15 PDP | 428.08 | fJ | STM 28nm CMOS (2016) | AcBM 1111.98 fJ | 15-bit truncation | p.7 |
| ABM2-15 NMED | 9.07 | 10−5 | STM 28nm CMOS (2016) | exact product | random inputs | p.7 |
| ABM2-15 PRED | 98.40 | % | STM 28nm CMOS (2016) | RED below 2% | random inputs | p.7 |
| ABM2-C15 delay | 2.07 | ns | STM 28nm CMOS (2016) | AcBM 2.99 ns | 15-bit truncation | p.7 |
| ABM2-C15 area | 422 | um2 | STM 28nm CMOS (2016) | AcBM 737 um2 | 15-bit truncation | p.7 |
| ABM2-C15 power | 208.1 | uW | STM 28nm CMOS (2016) | AcBM 371.9 uW | 15-bit truncation | p.7 |
| ABM2-C15 PDP | 430.77 | fJ | STM 28nm CMOS (2016) | AcBM 1111.98 fJ | 15-bit truncation | p.7 |
| ABM2-C15 NMED | 5.73 | 10−5 | STM 28nm CMOS (2016) | exact product | random inputs | p.7 |
| ABM2-C15 PRED | 98.79 | % | STM 28nm CMOS (2016) | RED below 2% | random inputs | p.7 |
| ABM2-R15 delay | 2.25 | ns | STM 28nm CMOS (2016) | AcBM 2.99 ns | 15-bit truncation | p.7 |
| ABM2-R15 area | 424 | um2 | STM 28nm CMOS (2016) | AcBM 737 um2 | 15-bit truncation | p.7 |
| ABM2-R15 power | 208.0 | uW | STM 28nm CMOS (2016) | AcBM 371.9 uW | 15-bit truncation | p.7 |
| ABM2-R15 PDP | 468.00 | fJ | STM 28nm CMOS (2016) | AcBM 1111.98 fJ | 15-bit truncation | p.7 |
| ABM2-R15 NMED | 3.41 | 10−5 | STM 28nm CMOS (2016) | exact product | random inputs | p.7 |
| ABM2-R15 PRED | 99.08 | % | STM 28nm CMOS (2016) | RED below 2% | random inputs | p.7 |
| ABM1 FIR SNRout | 27.59 | dB | STM 28nm CMOS (2016) | accurate 30.83 dB | 30-tap FIR, SNRin 3.89 dB | p.8 |
| ABM2-C9 FIR SNRout | 27.16 | dB | STM 28nm CMOS (2016) | accurate 30.83 dB | 30-tap FIR, SNRin 3.89 dB | p.8 |
| ABM2-R9 FIR SNRout | 27.15 | dB | STM 28nm CMOS (2016) | accurate 30.83 dB | 30-tap FIR, SNRin 3.89 dB | p.8 |
errors_and_checks: Accuracy is statistical rather than bounded. Table 7 reports pass rate/NMED/MAE/PRED, where PRED is the probability that RED is below 2%. Errors from approximate 3Y generation can have large magnitude when they enter a significant partial product, although the reported NMED values remain small and PRED exceeds 98% for every proposed multiplier. No fault-detection contract is provided. p.6–p.7
conditions: ABM1 improves delay by nearly 20% over AcBM. The 9-bit and 15-bit truncation configurations reduce area by roughly 18% and 43% and power by 18% and 44%, respectively. Recoding error is more significant than truncation error when no more than 9 partial-product bits are truncated. ABM1/ABM2-C9/ABM2-R9 lose about 3 dB of FIR SNRout, while greater truncation produces larger application error. p.6–p.8
evidence: §3–§5; Figs. 10–13; Tables 5–7, p.5–p.8

## new_families
none

## space_gaps
* `approximate_booth` lacks a reduction slot for the explicitly used Wallace tree. p.5–p.6
* `approximate_booth.encoder` lacks an approximate 3Y recoding-adder value that preserves a precise upper section while suppressing carry propagation in the lower section. p.2–p.3
* `lower_part_approximate.lower_cell` lacks the paper's 2-bit cell with Cout = yi, Si+1 = yi+1 and Si = Cin ⊕ yi ⊕ yi−1. p.2–p.3
* `approximate_booth` lacks partial-product truncation-width and truncation-compensation choices. p.6

## open_questions
* The paper calls the reduction structure a Wallace tree but does not state its exact counter/compressor cells. p.5
* The paper identifies the upper recoding section only as a 7-bit precise adder, so its carry-propagate family is UNKNOWN. p.3
