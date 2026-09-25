---
handle: pashaeifar2018
citation: M. Pashaeifar, M. Kamal, A. Afzali-Kusha, M. Pedram, "Approximate Reverse Carry Propagate Adder for Energy-Efficient DSP Applications", IEEE Transactions on VLSI Systems, vol. 26, no. 11, pp. 2530-2541, 2018
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary_integer_8_to_32_bit]
authority: incremental
pages_read: 12 / 12
---

## summary
The paper proposes reverse carry propagate full-adder cells whose carry travels from the most significant bit toward the least significant bit. Three cell variants form complete approximate adders or hybrid adders with an exact most-significant part and tunable approximate-part width. The implementations are evaluated in 45-nm CMOS and in FIR/JPEG DCT applications.

## families
### lower_part_approximate  (role: extends)
mechanism: An RCPFA receives Ai, Bi, the reverse carry Ci+1, and a forecast Fi, then produces Si, Ci, and Fi+1. Carry propagates from higher-significance cells toward lower-significance cells, so the weight of an unfinished carry decreases along the propagation path. A hybrid adder joins an exact forward-carry MSB section to an RCPA LSB section; the forecast Fk supplies the joining-point carry. RCPFA-I uses an operand bit as F, RCPFA-II uses Ai AND Bi, and RCPFA-III uses Ai OR Bi. # p.2–3, p.7
choices:
  lower_width: 3–12 bits in the 16-bit study; 16 bits in the principal 32-bit comparison [outside domain]   # p.7–8
  lower_cell: reverse_carry_rcpa   # p.2–3
  carry_to_upper: msb_and for RCPFA-II; operand_bit for RCPFA-I [outside domain]; carry_alive_or for RCPFA-III [outside domain]   # p.3, p.7
new_choices:
  forecast_signal: {operand_bit, carry_generate, carry_alive} — selects the auxiliary signal used to resolve the reverse-carry cell outputs   # p.3
slots:
  upper_adder: ripple_carry   # p.7
parameters: n-bit RCPA; RCPFA-I has 26 transistors; RCPFA-II/RCPFA-III have 16 transistors plus a four-transistor forecast generator; 8/12/16/20/24-bit accuracy studies; 16-bit hybrids with 3–12 approximate bits; 32-bit hybrids; 45-nm NanGate CMOS, 1 V, 25 °C; 10 000 uniformly distributed inputs at 100 MHz for energy comparison   # p.3, p.6–8
results:
| metric | value | unit | technology / device | baseline | condition | page |
| static power, RCPFA-II | 55 | % smaller | 45-nm NanGate CMOS; 2018 | exact FA | cell comparison | p.7 |
| static power, RCPFA-III | 19 | % smaller | 45-nm NanGate CMOS; 2018 | exact FA | cell comparison | p.7 |
| dynamic energy, RCPFA-II | 70 | % smaller | 45-nm NanGate CMOS; 2018 | exact FA | cell comparison | p.7 |
| dynamic energy, RCPFA-III | 56 | % smaller | 45-nm NanGate CMOS; 2018 | exact FA | cell comparison | p.7 |
| carry propagation delay, RCPFA-II | 38 | % smaller | 45-nm NanGate CMOS; 2018 | exact FA | cell comparison | p.7 |
| carry propagation delay, RCPFA-III | 29 | % smaller | 45-nm NanGate CMOS; 2018 | exact FA | cell comparison | p.7 |
| carry-to-sum delay, RCPFA-II | 70 | % smaller | 45-nm NanGate CMOS; 2018 | exact FA | cell comparison | p.7 |
| carry-to-sum delay, RCPFA-III | 60 | % smaller | 45-nm NanGate CMOS; 2018 | exact FA | cell comparison | p.7 |
| transistor count, RCPFA-II/RCPFA-III | 29 | % smaller | 45-nm NanGate CMOS; 2018 | exact FA | cell comparison | p.7 |
| exact 32-bit RCA energy | 136.7 | fJ | 45-nm NanGate CMOS; 2018 | none | normalization reference | p.8 |
| exact 32-bit RCA delay | 5.3 | ns | 45-nm NanGate CMOS; 2018 | none | normalization reference | p.8 |
| exact 32-bit RCA transistor count | 896 | transistors | 45-nm NanGate CMOS; 2018 | none | normalization reference | p.8 |
| hybrid delay improvement | 27 | % average | 45-nm NanGate CMOS; 2018 | studied approximate adders | proposed RCPFA hybrids | p.11 |
| hybrid energy improvement | 6 | % average | 45-nm NanGate CMOS; 2018 | studied approximate adders | proposed RCPFA hybrids | p.11 |
| hybrid EDP improvement | 31 | % average | 45-nm NanGate CMOS; 2018 | studied approximate adders | proposed RCPFA hybrids | p.11 |
| RCPFA-II energy | 2.5 | % higher | 45-nm NanGate CMOS; 2018 | LOA | 32-bit hybrid, 16-bit approximate part | p.8 |
| RCPFA-II EDP | 0.7 | % higher | 45-nm NanGate CMOS; 2018 | LOA | 32-bit hybrid, 16-bit approximate part | p.8 |
| RCPFA-II FoC | 65 | % smaller on average | 45-nm NanGate CMOS; 2018 | other studied approximate structures | 32-bit hybrid | p.8 |
| RCPFA-III FoC | 61 | % smaller on average | 45-nm NanGate CMOS; 2018 | other studied approximate structures | 32-bit hybrid | p.8 |
| FIR energy saving | 26 | % | 45-nm NanGate CMOS model; 2018 | exact FIR, 87.5 dBfs | 17 dBfs SNR loss | p.9 |
| FIR energy saving | 39 | % | 45-nm NanGate CMOS model; 2018 | exact FIR, 87.5 dBfs | 33 dBfs SNR loss | p.9 |
| JPEG DCT energy saving | 60 | % | 45-nm NanGate CMOS model; 2018 | exact DCT | RCPFA-II, widths (6, 9, 16, 30) | p.10 |
errors_and_checks: RCPFA-I has approximately zero analytical mean error. For an 8-bit exhaustive comparison, RCPFA-II has the lowest ER/MED/maximum ED/error variance, while RCPFA-III has the lowest MRED. Across the selected 8/12/16/20/24-bit comparisons, RCPFA-II has the lowest MRED and normalized MED. A 16-bit RCPA hybrid with eight approximate bits has MRED = 0.005, equal to four-bit truncation. The analysis assumes independent errors in individual FAs and excludes concurrent errors in two or more FAs. No fault-detection mechanism is provided. # p.5–7
conditions: Approximation applies to error-tolerant DSP workloads. RCPFA-I gives the smallest hybrid delay when the 32-bit approximate section is smaller than 16 bits, while RCPFA-II gives the smallest delay for larger approximate sections and the smallest power/energy/EDP across the studied widths. RCPFA-II/RCPFA-III MRED remains almost constant as the clock period is reduced; at 78% of exact-RCA critical-path delay, the exact RCA has larger MRED than the RCPFAs. Hybrid critical-path delay decreases while the exact section dominates, then increases after the reverse-carry section becomes dominant. # p.6–8
evidence: §III and Figs. 2–4 define the cells; §IV, Table II, and Figs. 5–7 establish error behavior; §V-A, Tables IV–V, and Figs. 8–10 establish circuit results; §V-B/§V-C and Figs. 11–14 establish application results.

## new_families
none

## space_gaps
* `carry_to_upper` lacks `operand_bit` and `carry_alive_or`, which are the RCPFA-I/RCPFA-III forecast mechanisms. # p.3
* `lower_width` excludes several explicitly evaluated widths, including 3/5/6/7/9/10/11 bits. # p.7, p.10
* The vocabulary has no cell-variant choice for the three forecast-generation mechanisms within `reverse_carry_rcpa`. # p.3

## open_questions
* Table II values are not legible in the supplied text, so the numerical ER/MED/maximum-ED/MRED/variance results cannot be recorded.
* The paper does not specify signed versus unsigned operand interpretation for the generic adder evaluations.
