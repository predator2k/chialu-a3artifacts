---
handle: chang2004
citation: C.-H. Chang, J. Gu, M. Zhang, "Ultra Low-Voltage Low-Power CMOS 4-2 and 5-2 Compressors for Fast Arithmetic Circuits", IEEE Transactions on Circuits and Systems I, vol. 51, 2004
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary]
authority: incremental
pages_read: 13 / 13
---

## summary
The paper analyzes 4-2/5-2 compressor architectures and proposes full-swing XOR–XNOR/carry-generator circuits for ultra-low-voltage multiplier reduction trees. The paper also proposes a 5-2 architecture using one fewer module than a prior architecture. Simulations in CSM 0.18-µm CMOS compare delay/power/power-delay product from 0.6 to 3.3 V.

## families
### compressor_4_2_tree  (role: extends)
mechanism: The 4-2 compressor accepts four primary inputs and a carry from the preceding lower-significance compressor, then produces a same-weight sum and two higher-weight carries. The implemented architecture decomposes the compressor into XOR/XNOR and 2-1 MUX modules with balanced input-to-output paths. The proposed XOR–XNOR cell adds feedback PMOS–NMOS transistors to eliminate weak internal logic while preserving simultaneous complementary outputs and low-voltage operation. # p.1986–1988
choices:
new_choices:
  logic_decomposition: xor_xnor_mux — XOR/XNOR modules and carry-generating MUX modules implement the compressor # p.1987
  xor_xnor_cell: feedback_pmos_nmos_full_swing — feedback transistors eliminate weak logic for input patterns “00” and “11” # p.1988
  logic_style: {complementary_cmos, cpl, dpl, hybrid} — transistor-level styles compared for constituent modules # p.1988–1989, p.1992
  output_drive: buffered_xnor_inverter — the final XOR output uses an XNOR followed by an inverter # p.1988
slots:
  none
parameters: five inputs; three outputs; CSM 0.18-µm CMOS; 0.6 to 3.3 V; 1024 random input patterns; 10 MHz at supply voltages less than or equal to 1.0 V; 100 MHz above 1.0 V # p.1986, p.1991–1992
results:
| metric | value | unit | technology / device | baseline | condition | page |
| lowest operable supply voltage | 0.6 | V | CSM 0.18-µm CMOS | other simulated 4-2 designs | Designs 3 and 6 | p.1993 |
| Design 8 average-power overhead | 12.7 | % more | CSM 0.18-µm CMOS | Design 6 (4-2_e) | 0.6 V | p.1993 |
| Design 8 average-power overhead | 14.9 | % more | CSM 0.18-µm CMOS | Design 6 (4-2_e) | 1.0 V | p.1993 |
| Design 8 average-power overhead | 19.0 | % more | CSM 0.18-µm CMOS | Design 6 (4-2_e) | 1.8 V | p.1993 |
| Design 8 average-power overhead | 30.5 | % more | CSM 0.18-µm CMOS | Design 6 (4-2_e) | 3.3 V | p.1993 |
errors_and_checks: none
conditions: Designs 3 and 6 are the only variants of the Fig. 4 architecture reported to operate down to 0.6 V. # p.1993 CPL/DPL implementations require almost twice as many interconnecting lines, so their wiring capacitance limits competitiveness in large parallel multipliers. # p.1993
evidence: §II, Figs. 1–10, Tables I–IV, Figs. 20–21, §V; p.1986–1989, p.1992–1993, p.1996

## new_families
### compressor_5_2_tree  (domain: mul: integer multipliers, closest: compressor_4_2_tree, why_not: A 5-2 compressor has seven inputs/four outputs and exposes distinct CGEN1/CGEN2 architecture choices absent from the 4-2 mechanism.)
mechanism: The 5-2 compressor accepts five primary inputs and two lower-significance carry inputs, then produces a same-weight sum and three higher-weight outputs. The proposed architecture uses one fewer module than the compared Kwon architecture. CGEN1 is a complex gate driven only by primary inputs on the anticipated critical path, while two CGEN2 modules remain controlled by XOR–XNOR signals and accept later-arriving neighboring carries. # p.1989–1991
choices:
  architecture: {cascaded_full_adders, modified_xor_xnor, kwon, proposed_cgen1_cgen2} — compared structural decompositions # p.1989–1990
  logic_style: {complementary_cmos, cpl, dpl, hybrid} — constituent-module implementations # p.1991, p.1993–1994
  primary_carry_generator: complex_gate_primary_inputs — CGEN1 bypasses the preceding XOR–XNOR module # p.1990–1991
  secondary_carry_generator: {complementary_cmos, mux_based} — alternative CGEN2 implementations # p.1990–1991
  xor_xnor_cell: feedback_pmos_nmos_full_swing — recommended XOR–XNOR implementation for low-voltage operation # p.1991
results:
| metric | value | unit | technology / device | baseline | condition | page |
| lowest operable supply voltage | 0.6 | V | CSM 0.18-µm CMOS | other 5-2 architectures | selected proposed-cell designs | p.1993, p.1996 |
| average-power reduction | 19% to 24% | lesser power | CSM 0.18-µm CMOS | Kwon architecture | bbb configuration | p.1995 |
| average-power reduction | 20% to 25% | lesser power | CSM 0.18-µm CMOS | Fig. 13 architecture | bbb configuration | p.1995 |
| power-efficiency improvement | 27% to 48% | better | CSM 0.18-µm CMOS | Kwon architecture | ebb configuration | p.1995 |
| power-efficiency improvement | 28% to 45% | better | CSM 0.18-µm CMOS | Fig. 13 architecture | ebb configuration | p.1995 |
| average-power reduction | 25% to 28% | lesser power | CSM 0.18-µm CMOS | Kwon architecture | hybrid configuration | p.1995–1996 |
| average-power reduction | 20% to 29% | lesser power | CSM 0.18-µm CMOS | Fig. 13 architecture | hybrid configuration | p.1995–1996 |
| delay reduction | 6% to 23% | faster | CSM 0.18-µm CMOS | Kwon architecture | hybrid configuration | p.1996 |
| delay reduction | 12% to 23% | faster | CSM 0.18-µm CMOS | Fig. 13 architecture | hybrid configuration | p.1996 |
evidence: §III, Figs. 11–18, Tables V–VIII, Figs. 22–28, §V; p.1989–1996

## space_gaps
* `compressor_4_2_tree` appears as a component-slot value but lacks a declared family block and choices for logic decomposition/logic style/XOR–XNOR implementation. # p.1986–1989
* The vocabulary lacks a 5-2 exact compressor family and a reduction slot that admits it. # p.1989–1996

## open_questions
* The numeric cells of Tables II–IV and VI–VIII are not transcribed in the supplied document text, so their absolute delay/power/PDP values must not be guessed.
* Several critical-path formulas are absent from the text extraction, so the merge pass must verify their symbols from the original figures.
