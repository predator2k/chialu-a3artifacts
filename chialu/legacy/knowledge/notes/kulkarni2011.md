---
handle: kulkarni2011
citation: P. Kulkarni, P. Gupta, M. Ercegovac, "Trading Accuracy for Power with an Underdesigned Multiplier Architecture", 24th International Conference on VLSI Design, pp. 346-351, 2011
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: ["2-bit binary", "4-bit binary", "8-bit binary", "12-bit binary", "16-bit binary"]
authority: incremental
pages_read: 6 / 6
---

## summary
The paper builds approximate multipliers from modified 2x2 multiplier cells whose 3*3 output is 111 rather than 1001. Larger multipliers use the cells for partial-product generation while retaining an accurate, synthesis-optimized adder tree. Selective accurate-cell substitution tunes the power/error tradeoff, and a residual correction path provides an accurate operating mode.

## families
### pp_perforation  (role: proposes)
mechanism: The modified 2x2 cell is correct for fifteen of sixteen inputs and produces 7 instead of 9 for input 3*3. Larger multipliers partition both operands into 2-bit groups, generate partial products with these cells, shift the partial products, and combine them through an accurate adder network. Replacing selected inaccurate cells with accurate cells reduces error at the cost of power savings. An optional decoder derives the error amount from the input vector, and a residual adder adds that amount to recover the accurate product.
choices:
  cell: kulkarni_2x2_inaccurate   # p.347
  correction: error_correction_vector   # pp.350-351
new_choices:
  cell_substitution: selectable inaccurate/accurate 2x2 blocks — tunes the power/error point by replacing individual cells   # p.347
  error_injection_location: partial_products — distinguishes the proposal from the evaluated inaccurate-adder-tree alternative   # p.349
slots:
  none
parameters: 2x2 building block; evaluated widths 2, 4, 8, 12, and 16 bits; five frequency targets from F through 2F; 2F is the accurate multiplier's maximum frequency   # pp.347-348
results:
| metric | value | unit | technology / device | baseline | condition | page |
| dynamic power reduction | 45.4 | % | 45nm Nangate / 2011 | accurate synthesized multiplier | 2-bit, average across F to 2F | p.348 |
| dynamic power reduction | 36.3 | % | 45nm Nangate / 2011 | accurate synthesized multiplier | 4-bit, average across F to 2F | p.348 |
| dynamic power reduction | 41.5 | % | 45nm Nangate / 2011 | accurate synthesized multiplier | 8-bit, average across F to 2F | p.348 |
| dynamic power reduction | 31.8 | % | 45nm Nangate / 2011 | accurate synthesized multiplier | 16-bit, average across F to 2F | p.348 |
| multiplier power reduction | 25.166 | % | 45nm Nangate / 2011 | accurate multipliers | FFT, 32 multipliers, ~158K gates | p.348 |
| total power reduction | 13.98 | % | 45nm Nangate / 2011 | accurate design | FFT | p.348 |
| multiplier power reduction | 31.09 | % | 45nm Nangate / 2011 | accurate multipliers | FIR, 4 multipliers, ~1.1K gates | p.348 |
| total power reduction | 18.30 | % | 45nm Nangate / 2011 | accurate design | FIR | p.348 |
| multiplier power reduction | 28.04 | % | 45nm Nangate / 2011 | accurate multiplier | RISC, 1 multiplier, ~10K gates | p.348 |
| total power reduction | 1.51 | % | 45nm Nangate / 2011 | accurate design | RISC | p.348 |
| power reduction | 41.5 | % | 45nm Nangate / 2011 | accurate multiplier | 8-bit image-sharpening multiplication | p.349 |
| SNR | 20.365 | dB | 45nm Nangate / 2011 | accurately filtered image | image sharpening | p.349 |
| JPEG SNR reduction | 1.44 | % | 45nm Nangate / 2011 | accurate multiplier, 25.56dB | Lenna, inaccurate SNR 25.19dB | p.350 |
| JPEG SNR reduction | 1.22 | % | 45nm Nangate / 2011 | accurate multiplier, 19.55dB | Coins, inaccurate SNR 19.31dB | p.350 |
| JPEG SNR reduction | 3.79 | % | 45nm Nangate / 2011 | accurate multiplier, 37.94dB | Sand-Dunes, inaccurate SNR 36.5dB | p.350 |
| JPEG SNR reduction | 2.13 | % | 45nm Nangate / 2011 | accurate multiplier, 30.89dB | Fireman, inaccurate SNR 30.23dB | p.350 |
| average area overhead | 4.6 | % | 45nm Nangate / 2011 | uncorrected architecture | 2-bit accurate-mode extension | p.351 |
| maximum area overhead | 8.14 | % | 45nm Nangate / 2011 | uncorrected architecture | 2-bit accurate-mode extension | p.351 |
| average inaccurate-mode power overhead | 4.8 | % | 45nm Nangate / 2011 | uncorrected architecture | 2-bit accurate-mode extension | p.351 |
| maximum inaccurate-mode power overhead | 8.32 | % | 45nm Nangate / 2011 | uncorrected architecture | 2-bit accurate-mode extension | p.351 |
| average area overhead | 5.87 | % | 45nm Nangate / 2011 | uncorrected architecture | 4-bit accurate-mode extension | p.351 |
| maximum area overhead | 7.67 | % | 45nm Nangate / 2011 | uncorrected architecture | 4-bit accurate-mode extension | p.351 |
| average inaccurate-mode power overhead | 7.5 | % | 45nm Nangate / 2011 | uncorrected architecture | 4-bit accurate-mode extension | p.351 |
| maximum inaccurate-mode power overhead | 16.14 | % | 45nm Nangate / 2011 | uncorrected architecture | 4-bit accurate-mode extension | p.351 |
| average area overhead | 10.5 | % | 45nm Nangate / 2011 | uncorrected architecture | 8-bit accurate-mode extension | p.351 |
| maximum area overhead | 13.44 | % | 45nm Nangate / 2011 | uncorrected architecture | 8-bit accurate-mode extension | p.351 |
| average inaccurate-mode power overhead | 8.56 | % | 45nm Nangate / 2011 | uncorrected architecture | 8-bit accurate-mode extension | p.351 |
| maximum inaccurate-mode power overhead | 12.88 | % | 45nm Nangate / 2011 | uncorrected architecture | 8-bit accurate-mode extension | p.351 |
| average area overhead | 9.875 | % | 45nm Nangate / 2011 | uncorrected architecture | 16-bit accurate-mode extension | p.351 |
| maximum area overhead | 13.85 | % | 45nm Nangate / 2011 | uncorrected architecture | 16-bit accurate-mode extension | p.351 |
| average inaccurate-mode power overhead | 8.22 | % | 45nm Nangate / 2011 | uncorrected architecture | 16-bit accurate-mode extension | p.351 |
| maximum inaccurate-mode power overhead | 13.67 | % | 45nm Nangate / 2011 | uncorrected architecture | 16-bit accurate-mode extension | p.351 |
errors_and_checks: The 2-bit cell has error probability 1/16, error magnitude 2, and maximum error 22.22%. Table I reports error probability/mean error/maximum error as 0.0625/1.39%/22.22% at 2 bits, 0.19/2.60%/22.22% at 4 bits, 0.46/3.25%/22.22% at 8 bits, 0.675/3.31%/22.22% at 12 bits, and 0.81/3.32%/22.22% at 16 bits. The correction decoder detects erroneous input patterns and supplies their error amounts to an adder; no fault model, detection-coverage measurement, or false-alarm result is reported.   # pp.347,350
conditions: Power savings increase at higher frequency because the faster inaccurate circuit requires less aggressive gate sizing. Design-level savings are largest when multipliers consume much of total power, as in the FIR example, and small in the RISC example. The partial-product method has a better measured accuracy/power tradeoff than placing inaccurate adders in the reduction tree. The JPEG hardware tradeoff has limited benefit against coefficient reduction at high SNR, although it consumes less power at equal SNR/fixed runtime under the assumptions that the multiplier determines frequency and consumes most power. Accurate mode runs at 0.85 times the original frequency in the overhead experiment.   # pp.348-350
evidence: §II.A-D, Figs. 1-4, Table I, pp.346-347; §III.A-D, Figs. 5-7, Tables II-IV, pp.348-349; §IV, Figs. 8-10, Table V, pp.349-350; §V, Figs. 11-12, Table VI, pp.350-351

## new_families
none

## space_gaps
* pp_perforation lacks a reduction-tree/final-adder slot, although this architecture explicitly retains a fully accurate, synthesis-optimized adder network after inaccurate partial-product generation.   # pp.347-348
* pp_perforation lacks a declared cell-substitution choice for mixing accurate and inaccurate 2x2 cells to tune the error/power curve.   # p.347

## open_questions
* The paper does not enumerate the accurate-cell placements used for each point in Fig. 7.
* The synthesis tool selects and optimizes the accurate adder network, so the instantiated reduction-tree and final-adder families remain UNKNOWN.
