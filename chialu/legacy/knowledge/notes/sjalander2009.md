---
handle: sjalander2009
citation: M. Sjalander, P. Larsson-Edefors, "Multiplication Acceleration Through Twin Precision", IEEE Transactions on Very Large Scale Integration (VLSI) Systems, vol. 17, no. 9, pp. 1233-1246, 2009
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int8, int16, int32, int48, int64]
authority: landmark
pages_read: 14 / 14
---

## summary
The document proposes twin precision, which partitions one integer multiplier to execute either one full-width multiplication or concurrent narrow-width multiplications. Implemented Baugh–Wooley and modified-Booth variants reduce narrow-operation power/energy and enable a lightweight packed-SIMD processor extension.

## families
### twin_precision_subword  (role: proposes)
mechanism: Unused regions of one partial-product matrix are reassigned to independent narrow multiplications. Control gates force intervening partial products to zero, so the existing reduction tree and final adder produce separate LSP/MSP results without cross-partition carry. Signed Baugh–Wooley operation requires selectable partial-product inversions/sign bits, while modified-Booth operation requires mode-dependent recoding/sign-extension patterns and two additional reduction-tree inputs. # pp.1234-1239
choices:
  partition: halves   # pp.1235-1239
  base_scheme: {baugh_wooley, modified_booth}   # pp.1236-1239
  per_lane_signed: true   # pp.1236-1239
new_choices:
  operation_modes: {full_width, single_half_width, two_half_width_parallel} — selectable uses of the shared multiplier   # p.1235
  partial_product_isolation: control_gated_zeroing — unused partial products are forced to zero   # pp.1235,1238
slots:
  lane_cpa: parallel_prefix [topology=kogge_stone]   # p.1239
parameters: Evaluated multiplier widths are 8, 16, 32, 48, and 64 bits; the implemented narrow lanes have width N/2; the processor case uses one 32-bit or two 16-bit operations and a two-stage multiplier pipeline.   # pp.1240-1244
results:
| metric | value | unit | technology / device | baseline | condition | page |
| full-width power overhead | 8 | % | 130-nm commercial process (2009) | conventional 16-bit Baugh–Wooley | twin-precision Baugh–Wooley | p.1240 |
| full-width power overhead | 5 | % | 130-nm commercial process (2009) | conventional 32-bit Baugh–Wooley | twin-precision Baugh–Wooley | p.1240 |
| full-width power overhead | 6 | % | 130-nm commercial process (2009) | conventional 48-bit Baugh–Wooley | twin-precision Baugh–Wooley | p.1240 |
| delay penalty | 0–150 | ps | 130-nm commercial process (2009) | conventional Baugh–Wooley | widths excluding 64 bits | p.1240 |
| full-width energy-per-operation overhead | 10 | % average | 130-nm commercial process (2009) | conventional Baugh–Wooley | N-bit operation | p.1240 |
| narrow energy-per-operation reduction | 59 | % average | 130-nm commercial process (2009) | conventional Baugh–Wooley | two concurrent N/2-bit operations | p.1240 |
| delay penalty | about 200 | ps | 65-nm commercial process (2009) | corresponding conventional multiplier | 32-bit twin-precision implementations | p.1242 |
| area overhead | 11 | % | 65-nm commercial process (2009) | conventional 32-bit Baugh–Wooley | twin-precision Baugh–Wooley | p.1242 |
| area overhead | 3 | % | 65-nm commercial process (2009) | conventional 32-bit modified-Booth | twin-precision modified-Booth | p.1242 |
| power reduction | more than 60 | % | 65-nm commercial process (2009) | conventional 32-bit Baugh–Wooley | one 16-bit operation | p.1242 |
| power-per-operation reduction | close to 70 | % | 65-nm commercial process (2009) | conventional 32-bit Baugh–Wooley | two concurrent 16-bit operations | p.1242 |
| narrow-operation break-even fraction | 15–18 | % | 65-nm commercial process (2009) | conventional Baugh–Wooley energy | signed 16-bit operations | p.1243 |
| narrow-operation break-even fraction | 5–7 | % | 130-nm commercial process (2009) | conventional Baugh–Wooley energy | signed 16-bit operations | p.1243 |
| benchmark multiplier-energy reduction | 25–28 | % average | 65-nm commercial process (2009) | conventional Baugh–Wooley | ten EEMBC benchmarks using both 16-bit modes | p.1243 |
| benchmark multiplier-energy reduction | 21–30 | % average | 130-nm commercial process (2009) | conventional Baugh–Wooley | ten EEMBC benchmarks using both 16-bit modes | p.1243 |
| processor area overhead | 6 | % | 130-nm commercial process (2009) | processor without SIMD extension | twin-precision SIMD processor | p.1244 |
| processor delay increase | 60 | ps | 130-nm commercial process (2009) | processor without SIMD extension | twin-precision SIMD processor | p.1244 |
| processor power increase | 0.09 | mW | 130-nm commercial process (2009) | processor without SIMD extension | maximum clock frequency | p.1244 |
| FFT cycle reduction | 18 | % | 130-nm processor implementation (2009) | original FFT on conventional processor | 256-point 16-bit FFT | p.1245 |
| FFT execution-time reduction | 15 | % | 130-nm processor implementation (2009) | original FFT on conventional processor | SIMD-enabled FFT | p.1245 |
| FFT energy reduction | 14 | % | 130-nm processor implementation (2009) | original FFT on conventional processor | SIMD-enabled FFT | p.1245 |
| FFT memory-access reduction | 39–43 | % | 130-nm processor implementation (2009) | unpacked execution | packed 16-bit data; memory energy excluded | p.1245 |
errors_and_checks: Multiplication is exact. Generated multipliers through 16 bits were exhaustively verified; larger multipliers were verified with one million random vectors.   # p.1239
conditions: The Baugh–Wooley/HPM implementation has simpler mode-control logic and better delay/power behavior than the modified-Booth twin-precision implementation.   # pp.1240,1245
conditions: Energy improves only when enough operations use narrow mode; the reported break-even fractions are 15%–18% in 65 nm and 5%–7% in 130 nm.   # p.1243
conditions: The 130-nm multiplier timing excludes mode-control signals, while the 65-nm and processor evaluations include their switching/buffering effects.   # pp.1239,1241,1244
evidence: Sections II–VII and IX; Figs. 3–23; Tables I–VI.

### partitioned_carry_chain  (role: instantiates)
mechanism: The processor’s 32-bit Sklansky prefix adder becomes two independent 16-bit adders by inserting one controlled AND gate in the carry-propagation path. Packed subtraction additionally injects a carry at bit position 16. # p.1244
choices:
  boundary_mechanism: carry_kill_gate   # p.1244
new_choices:
  boundary_carry_injection: true — packed subtraction inserts a carry at the lane boundary   # p.1244
slots:
  base_adder: parallel_prefix [topology=sklansky]   # p.1244
parameters: One 32-bit lane or two 16-bit lanes; supports PADD and PSUB.   # p.1244
results: none
errors_and_checks: Exact packed addition/subtraction; no fault-detection mechanism is reported.   # p.1244
conditions: Logical operations need no partition-specific hardware because they operate bitwise; shift/compare/branch SIMD instructions are not added.   # p.1243
evidence: Section IX-A–B; Fig. 26; Table III.

## new_families
none

## space_gaps
* `twin_precision_subword.partition` lacks arbitrary unequal-width partitions and more than two partitions whose combined widths do not exceed the full width. # p.1235
* `twin_precision_subword.base_scheme` lacks the unsigned array/HPM implementation demonstrated before the signed variants. # pp.1235-1236
* `twin_precision_subword` lacks a reduction-tree slot for the regular logarithmic-depth HPM tree built from 3:2 full adders. # pp.1235-1239
* `partitioned_carry_chain` lacks a choice for lane-boundary carry insertion required by packed subtraction. # p.1244

## open_questions
* The exact numeric cells of Tables I, II, IV, V, and VI are not present in the supplied text transcription, so only values repeated in prose are extracted.
