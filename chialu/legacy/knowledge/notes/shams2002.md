---
handle: shams2002
citation: A. M. Shams, T. K. Darwish, M. A. Bayoumi, "Performance Analysis of Low-Power 1-Bit CMOS Full Adder Cells", IEEE Transactions on VLSI Systems, vol. 10, no. 1, pp. 20-29, 2002.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary_1bit]
authority: incremental
pages_read: 20-29 / 10
---

## summary
The paper decomposes a 1-bit CMOS full-adder cell into XOR/XNOR-generation, sum-generation, and carry-generation modules, then constructs and compares twenty module combinations. Simulations in latch-bounded and four-cell cascade structures show that the lowest-power, lowest-delay, and strongest-driving cells differ with the surrounding circuit.

## families
### ripple_carry  (role: instantiates)
mechanism: A four-cell cascade evaluates full-adder cells under the driving requirements of regular multipliers and binary adders. Buffers drive the first cell and load the last cell; intermediate buffers restore weak sum and carry signals for cells using pass devices or transmission gates. # p.26, p.28
choices:
new_choices:
  intercell_buffering: none | every_other_cell — weak sum and carry outputs can be restored between alternate cells. # p.27-28
slots:
  full_adder_cell: hybrid_pass [modular XOR/XNOR, sum, and transmission-gate carry circuits] # p.22-25
parameters: 4 cascaded 1-bit cells; buffers after every other cell where required; 3.3 Volts supply. # p.26-28
results:
| metric | value | unit | technology / device | baseline | condition | page |
| buffer overhead for Fig. 6(b)/(d) sum output | 2 | transistors per cell | 0.35-µm CMOS (2002) | unbuffered cell | buffer after every other cell | p.28 |
| buffer overhead for carry output | 2 | transistors per cell | 0.35-µm CMOS (2002) | unbuffered cell | buffer after every other cell | p.28 |
errors_and_checks: The cells implement the exact Boolean sum and carry functions; no fault-detection mechanism is evaluated. # p.21-22
conditions: Latches restore weak or incomplete-swing outputs in pipelined structures, so strong cell-level drive is unnecessary there. Cascaded structures require clean outputs and favor buffered cells; DB has the lowest reported cascade power, while EC has the lowest reported cascade delay. Intermediate buffers consume less power than the major transistor sizing required by the tested pass-device cells. # p.26-28
evidence: Fig. 11 and Sections VI-B–VI-D, p.26-28; Tables VI-VIII, p.28.

## new_families
### modular_cmos_full_adder_cell  (domain: adder, closest: ripple_carry, why_not: ripple_carry describes carry propagation across bits but does not represent the paper's transistor-level module composition and output-drive choices.)
mechanism: The cell is divided into a first module that produces the half-sum and its complement, a second module that produces sum, and a third four-transistor multiplexer module that produces carry. Five first-module circuits and four second-module circuits form twenty cells with the common carry module. The circuits combine transmission gates, transmission-function logic, low-transistor-count XOR/XNOR gates, and optional inverter-buffered outputs. # p.22-25
choices:
  xor_xnor_generation: {xor_then_invert, simultaneous_xor_xnor} — whether the first module derives the complement through an inverter or generates both signals together. # p.22
  sum_generation: {four_transistor_xnor_plus_inverter, transmission_function_xor, transmission_function_xnor_plus_inverter, five_transistor_xor} — the four evaluated second-module circuits. # p.24
  carry_generation: {four_transistor_mux} — the adopted carry module selects an operand or carry input using the half-sum. # p.24
  output_drive: {unbuffered, inverter_buffered, intermediate_buffers} — the drive-strength alternatives evaluated or discussed. # p.24, p.27-28
  sizing_objective: {minimum_power_delay_product} — critical-path transistors are sized iteratively until the power-delay product ceases to improve. # p.22-23, p.26
results:
| metric | value | unit | technology / device | baseline | condition | page |
| candidate-cell transistor count | 14-20 | transistors | 0.35-µm CMOS (2002) | none | twenty module-composed cells | p.25 |
| TG-CMOS transistor count | 20 | transistors | 0.35-µm CMOS (2002) | none | standard reference cell | p.21 |
| TFA transistor count | 16 | transistors | 0.35-µm CMOS (2002) | none | standard reference cell | p.21 |
| 14T transistor count | 14 | transistors | 0.35-µm CMOS (2002) | none | standard reference cell | p.21 |
| CMOS transistor count | 28 | transistors | 0.35-µm CMOS (2002) | none | standard reference cell | p.21 |
| CPL transistor count | 32 | transistors | 0.35-µm CMOS (2002) | none | standard reference cell | p.21 |
| DB power reduction | 14 | % less power | 0.35-µm CMOS (2002) | 14T/CB | latch-bounded first circuit, 3.3 Volts | p.26 |
| DB power reduction | 15 | % less power | 0.35-µm CMOS (2002) | TFA/BB | latch-bounded first circuit, 3.3 Volts | p.26 |
| DB power reduction | 25 | % less power | 0.35-µm CMOS (2002) | TG-CMOS | latch-bounded first circuit, 3.3 Volts | p.26 |
| ED speed improvement | 13 | % faster | 0.35-µm CMOS (2002) | 14T/CB | latch-bounded first circuit, 3.3 Volts | p.26 |
| ED speed improvement | 17 | % faster | 0.35-µm CMOS (2002) | TFA/BB | latch-bounded first circuit, 3.3 Volts | p.26 |
| ED speed improvement | 26 | % faster | 0.35-µm CMOS (2002) | TG-CMOS | latch-bounded first circuit, 3.3 Volts | p.26 |
| cells with lower power | 2 | cells | 0.35-µm CMOS (2002) | 14T/CB | latch-bounded first circuit | p.26 |
| cells with lower power | 3 | cells | 0.35-µm CMOS (2002) | TFA/BB | latch-bounded first circuit | p.26 |
| cells with lower power | 7 | cells | 0.35-µm CMOS (2002) | TG-CMOS | latch-bounded first circuit | p.26 |
| cells with lower delay | 6 | cells | 0.35-µm CMOS (2002) | 14T/CB | latch-bounded first circuit | p.26 |
| cells with lower delay | 8 | cells | 0.35-µm CMOS (2002) | TFA/BB | latch-bounded first circuit | p.26 |
| cells with lower delay | 9 | cells | 0.35-µm CMOS (2002) | TG-CMOS | latch-bounded first circuit | p.26 |
| cells with lower power-delay product | 2 | cells | 0.35-µm CMOS (2002) | 14T/CB | latch-bounded first circuit | p.27 |
| cells with lower power-delay product | 6 | cells | 0.35-µm CMOS (2002) | TFA/BB | latch-bounded first circuit | p.27 |
| cells with lower power-delay product | 9 | cells | 0.35-µm CMOS (2002) | TG-CMOS | latch-bounded first circuit | p.27 |
evidence: Sections III-VII, p.21-29; Figs. 2-12; Tables I-VIII.

## space_gaps
* The `full_adder_cell` slot lacks `complementary_pass_logic`, which is the document's classification of the 32-transistor CPL reference cell. # p.21
* The vocabulary lacks choices for XOR/XNOR generation, sum-output buffering, carry-output buffering, transistor sizing, and surrounding load structure, although these choices change the reported cell ranking. # p.22-28
* The slot values `transmission_gate`, `transmission_function`, and `hybrid_pass` need corresponding component-family definitions to represent the compared cell circuits precisely. # p.21-25

## open_questions
* The supplied extraction does not expose the numeric entries in Tables I-V and VII-VIII, so the absolute power, delay, power-delay-product, and area results remain UNKNOWN.
