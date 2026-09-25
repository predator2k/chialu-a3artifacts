---
handle: gigliotti_2004
citation: P. Gigliotti, "Implementing Barrel Shifters Using Multipliers", Xilinx Application Note XAPP195, 2004
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [8-bit binary, 32-bit binary]
authority: incremental
pages_read: 1-4 / 4
---

## summary
The application note implements an 8-bit rotating barrel shifter with one Virtex-II MULT18X18 and composes multiplier-based shifters into single-cycle and four-cycle 32-bit designs. The single-cycle design reduces configurable-logic use from 64 CLBs to nine CLBs while consuming four embedded multipliers.

## families
### fpga_mapped  (role: proposes)
mechanism: An 8-bit input is multiplied by a one-hot power-of-two value in a MULT18X18, which produces the requested rotation in one clock cycle. The single-cycle 32-bit design divides the input into four bytes, performs fine shifts with four multiplier shifters, and performs bulk byte reordering with thirty-two 4-to-1 multiplexers. The four-cycle design reuses one multiplier shifter, input multiplexers, output registers with clock enables, and a state machine. # p.1, p.3-4
choices:
  mapping: dsp_multiplier   # p.1
new_choices:
  execution_schedule: {single_cycle_parallel, four_cycle_time_multiplexed} — whether four multiplier shifters operate in parallel or one multiplier shifter is reused across bytes   # p.3-4
  shift_function: rotate — bits shifted from the MSB end return at the LSB end   # p.1
slots:
  none
parameters: 8-bit shifter: one MULT18X18, one-hot SHIFT[7:0], single clock cycle; 32-bit single-cycle shifter: four 8-bit multiplier shifters, thirty-two 4-to-1 multiplexers, two processing stages, S[2:0] for fine shifting and S[4:3] for bulk shifting; 32-bit four-cycle shifter: one MULT18X18 and two 8-bit 4 x 1 MUXs. # p.1, p.3-4
results:
| metric | value | unit | technology / device | baseline | condition | page |
| multiplier count | 1 | MULT18X18 | Virtex-II / 2004 | traditional 8-bit design: 16 slices / four CLBs | 8-bit barrel shifter | p.1 |
| configurable-logic use | 9 | CLBs | Virtex-II / 2004 | traditional 32-bit design: 64 CLBs | single-cycle 32-bit design, plus four multipliers | p.4 |
| multiplier count | 4 | multipliers | Virtex-II / 2004 | traditional 32-bit design: 64 CLBs | single-cycle 32-bit design | p.4 |
| one-hot encoder use | 8 | LUTs | Virtex-II / 2004 | none | single-cycle 32-bit multiplier design; implemented in one CLB | p.4 |
| output multiplexer use | 8 | CLBs | Virtex-II / 2004 | none | thirty-two 4-by-1 multiplexers in the single-cycle 32-bit design | p.4 |
| latency | 4 | clock cycles | Virtex-II / 2004 | single-cycle 32-bit multiplier design | reused one-MULT18X18 design | p.4 |
| multiplier count | 1 | MULT18X18 | Virtex-II / 2004 | single-cycle design: four MULT18X18 | four-cycle 32-bit design | p.3-4 |
errors_and_checks: none
conditions: The multiplier control must be one-hot encoded, with each asserted bit selecting multiplication by a power of two. # p.1 The single-cycle 32-bit design uses the three least-significant shift bits for fine shifting and the two most-significant shift bits for bulk shifting. # p.3 The multiplier implementation saves configurable-logic area but loses placement flexibility because the barrel shifters are locked to multiplier locations. # p.4 The four-cycle design trades latency for lower hardware use. # p.4
evidence: Summary and Eight-bit Barrel Shifter, Figures 2-4, Single-Cycle 32-Bit Barrel Shifter, Four-Cycle 32-bit Barrel Shifter, and Conclusion, p.1-4.

### barrel_mux_tree  (role: compares)
mechanism: The traditional rotating barrel shifter feeds an N-bit word into N, N-bit-wide multiplexers so any input bit can reach any output position in one clock cycle. The documented 8-bit implementation uses eight 8-to-1 multiplexers and eight flip-flops, while the 32-bit implementation uses thirty-two 32-to-1 multiplexers. # p.1, p.3
choices:
new_choices:
  shift_function: rotate — bits shifted from the MSB end return at the LSB end   # p.1
slots:
  none
parameters: N=8 or 32 bits; single clock cycle; eight 8-to-1 multiplexers for 8 bits; thirty-two 32-to-1 multiplexers for 32 bits. # p.1, p.3
results:
| metric | value | unit | technology / device | baseline | condition | page |
| multiplexer logic | 16 | slices | Virtex-II / 2004 | none | eight-bit traditional barrel shifter | p.1 |
| multiplexer logic | 4 | CLBs | Virtex-II / 2004 | none | eight-bit traditional barrel shifter; output registers can be absorbed into the multiplexer CLBs | p.1 |
| multiplexer logic | 64 | CLBs | Virtex-II / 2004 | multiplier method: nine CLBs and four multipliers | single-cycle 32-bit traditional barrel shifter | p.3-4 |
errors_and_checks: none
conditions: The traditional implementation provides a single-cycle rotation through N N-to-1 multiplexers. # p.1 The conclusion states that certain designs favor the traditional approach but does not identify those designs. # p.4
evidence: Introduction and Eight-bit Barrel Shifter, Figure 1, Single-Cycle 32-Bit Barrel Shifter, and Conclusion, p.1-4.

## new_families
none

## space_gaps
* `fpga_mapped` lacks an execution-schedule choice for parallel single-cycle use versus multicycle reuse of one embedded multiplier. # p.3-4
* The shifter families lack a shift-function choice that distinguishes the documented bit rotation from logical or arithmetic shifting. # p.1

## open_questions
* The document reports no clock frequency, combinational delay, power, or complete resource count for the four-cycle design.
* The document does not explain which design conditions make the traditional 32-to-1 multiplexer implementation more appropriate.
