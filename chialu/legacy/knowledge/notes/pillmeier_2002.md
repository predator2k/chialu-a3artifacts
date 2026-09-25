---
handle: pillmeier_2002
citation: M. R. Pillmeier, M. J. Schulte, E. G. Walters III, "Design Alternatives for Barrel Shifters", Proc. SPIE 4791, Advanced Signal Processing Algorithms, Architectures, and Implementations XII, 2002
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int8, int16, int32, int64, int128]
authority: incremental
pages_read: 436-447 / 12
---

## summary
The paper presents and compares four single-cycle barrel shifters that share hardware for six logical/arithmetic shift and rotate operations. The mask-based data-reversal design has the lowest delay at every tested width, while either data-reversal design has the lowest area depending on width. # p.436, p.445-446

## families
### barrel_mux_tree  (role: compares)
mechanism: An n-bit logarithmic shifter uses log2(n) binary multiplexor stages controlled by individual bits of the shift amount. The four compared designs support both directions through input/output data reversal, the two's complement of the shift amount, or the one's complement plus a one-bit rotate stage. Mask-based variants use a rotator and generated masks to form logical/arithmetic shifts and calculate zero/overflow flags. # p.437-444
choices:
  stage_radix: 2   # p.437-438
  select_encoding: binary   # p.437-438
  direction_handling: data_reversal; amount_negation   # p.439, p.443-444
  stage_order: large_shift_first   # p.438
new_choices:
  structure: {mux_based_data_reversal, mask_based_data_reversal, mask_based_twos_complement, mask_based_ones_complement} — selects the bidirectional shift/rotate construction   # p.439-444
  flag_generation: {post_result_zero_parallel_overflow, parallel_masked} — selects whether zero waits for the result or is calculated with masks in parallel   # p.439-443
  amount_transform: {none, twos_complement, ones_complement_plus_one_bit_rotate} — selects the left-operation shift-amount transformation   # p.443-444
slots: none
parameters: n = 8, 16, 32, 64, or 128 bits; B = log2(n) bits; shifts/rotates complete in one cycle; operations are shift right logical/arithmetic, rotate right, shift left logical/arithmetic, and rotate left   # p.436-437, p.444
results:
| metric | value | unit | technology / device | baseline | condition | page |
| area | 1308 | equivalent gates | IBM CU-11 0.11 micron CMOS standard-cell library, copper interconnect (2002) | none | mux-based data-reversal, 8-bit, delay-optimized synthesis | p.445 |
| area | 2731 | equivalent gates | IBM CU-11 0.11 micron CMOS standard-cell library, copper interconnect (2002) | none | mux-based data-reversal, 16-bit, delay-optimized synthesis | p.445 |
| area | 6416 | equivalent gates | IBM CU-11 0.11 micron CMOS standard-cell library, copper interconnect (2002) | none | mux-based data-reversal, 32-bit, delay-optimized synthesis | p.445 |
| area | 14242 | equivalent gates | IBM CU-11 0.11 micron CMOS standard-cell library, copper interconnect (2002) | none | mux-based data-reversal, 64-bit, delay-optimized synthesis | p.445 |
| area | 30990 | equivalent gates | IBM CU-11 0.11 micron CMOS standard-cell library, copper interconnect (2002) | none | mux-based data-reversal, 128-bit, delay-optimized synthesis | p.445 |
| area | 1226 | equivalent gates | IBM CU-11 0.11 micron CMOS standard-cell library, copper interconnect (2002) | none | mask-based data-reversal, 8-bit, delay-optimized synthesis | p.445 |
| area | 3180 | equivalent gates | IBM CU-11 0.11 micron CMOS standard-cell library, copper interconnect (2002) | none | mask-based data-reversal, 16-bit, delay-optimized synthesis | p.445 |
| area | 6141 | equivalent gates | IBM CU-11 0.11 micron CMOS standard-cell library, copper interconnect (2002) | none | mask-based data-reversal, 32-bit, delay-optimized synthesis | p.445 |
| area | 14488 | equivalent gates | IBM CU-11 0.11 micron CMOS standard-cell library, copper interconnect (2002) | none | mask-based data-reversal, 64-bit, delay-optimized synthesis | p.445 |
| area | 31424 | equivalent gates | IBM CU-11 0.11 micron CMOS standard-cell library, copper interconnect (2002) | none | mask-based data-reversal, 128-bit, delay-optimized synthesis | p.445 |
| area | 1958 | equivalent gates | IBM CU-11 0.11 micron CMOS standard-cell library, copper interconnect (2002) | none | mask-based two's complement, 8-bit, delay-optimized synthesis | p.445 |
| area | 3908 | equivalent gates | IBM CU-11 0.11 micron CMOS standard-cell library, copper interconnect (2002) | none | mask-based two's complement, 16-bit, delay-optimized synthesis | p.445 |
| area | 8827 | equivalent gates | IBM CU-11 0.11 micron CMOS standard-cell library, copper interconnect (2002) | none | mask-based two's complement, 32-bit, delay-optimized synthesis | p.445 |
| area | 17657 | equivalent gates | IBM CU-11 0.11 micron CMOS standard-cell library, copper interconnect (2002) | none | mask-based two's complement, 64-bit, delay-optimized synthesis | p.445 |
| area | 36592 | equivalent gates | IBM CU-11 0.11 micron CMOS standard-cell library, copper interconnect (2002) | none | mask-based two's complement, 128-bit, delay-optimized synthesis | p.445 |
| area | 1926 | equivalent gates | IBM CU-11 0.11 micron CMOS standard-cell library, copper interconnect (2002) | none | mask-based one's complement, 8-bit, delay-optimized synthesis | p.445 |
| area | 4507 | equivalent gates | IBM CU-11 0.11 micron CMOS standard-cell library, copper interconnect (2002) | none | mask-based one's complement, 16-bit, delay-optimized synthesis | p.445 |
| area | 9825 | equivalent gates | IBM CU-11 0.11 micron CMOS standard-cell library, copper interconnect (2002) | none | mask-based one's complement, 32-bit, delay-optimized synthesis | p.445 |
| area | 20247 | equivalent gates | IBM CU-11 0.11 micron CMOS standard-cell library, copper interconnect (2002) | none | mask-based one's complement, 64-bit, delay-optimized synthesis | p.445 |
| area | 40453 | equivalent gates | IBM CU-11 0.11 micron CMOS standard-cell library, copper interconnect (2002) | none | mask-based one's complement, 128-bit, delay-optimized synthesis | p.445 |
| worst-case delay | 0.68 | nanoseconds | IBM CU-11 0.11 micron CMOS standard-cell library, copper interconnect (2002) | none | mux-based data-reversal, 8-bit, delay-optimized synthesis | p.446 |
| worst-case delay | 0.83 | nanoseconds | IBM CU-11 0.11 micron CMOS standard-cell library, copper interconnect (2002) | none | mux-based data-reversal, 16-bit, delay-optimized synthesis | p.446 |
| worst-case delay | 1.08 | nanoseconds | IBM CU-11 0.11 micron CMOS standard-cell library, copper interconnect (2002) | none | mux-based data-reversal, 32-bit, delay-optimized synthesis | p.446 |
| worst-case delay | 1.30 | nanoseconds | IBM CU-11 0.11 micron CMOS standard-cell library, copper interconnect (2002) | none | mux-based data-reversal, 64-bit, delay-optimized synthesis | p.446 |
| worst-case delay | 1.46 | nanoseconds | IBM CU-11 0.11 micron CMOS standard-cell library, copper interconnect (2002) | none | mux-based data-reversal, 128-bit, delay-optimized synthesis | p.446 |
| worst-case delay | 0.61 | nanoseconds | IBM CU-11 0.11 micron CMOS standard-cell library, copper interconnect (2002) | none | mask-based data-reversal, 8-bit, delay-optimized synthesis | p.446 |
| worst-case delay | 0.75 | nanoseconds | IBM CU-11 0.11 micron CMOS standard-cell library, copper interconnect (2002) | none | mask-based data-reversal, 16-bit, delay-optimized synthesis | p.446 |
| worst-case delay | 0.94 | nanoseconds | IBM CU-11 0.11 micron CMOS standard-cell library, copper interconnect (2002) | none | mask-based data-reversal, 32-bit, delay-optimized synthesis | p.446 |
| worst-case delay | 1.06 | nanoseconds | IBM CU-11 0.11 micron CMOS standard-cell library, copper interconnect (2002) | none | mask-based data-reversal, 64-bit, delay-optimized synthesis | p.446 |
| worst-case delay | 1.27 | nanoseconds | IBM CU-11 0.11 micron CMOS standard-cell library, copper interconnect (2002) | none | mask-based data-reversal, 128-bit, delay-optimized synthesis | p.446 |
| worst-case delay | 0.89 | nanoseconds | IBM CU-11 0.11 micron CMOS standard-cell library, copper interconnect (2002) | none | mask-based two's complement, 8-bit, delay-optimized synthesis | p.446 |
| worst-case delay | 1.03 | nanoseconds | IBM CU-11 0.11 micron CMOS standard-cell library, copper interconnect (2002) | none | mask-based two's complement, 16-bit, delay-optimized synthesis | p.446 |
| worst-case delay | 1.19 | nanoseconds | IBM CU-11 0.11 micron CMOS standard-cell library, copper interconnect (2002) | none | mask-based two's complement, 32-bit, delay-optimized synthesis | p.446 |
| worst-case delay | 1.41 | nanoseconds | IBM CU-11 0.11 micron CMOS standard-cell library, copper interconnect (2002) | none | mask-based two's complement, 64-bit, delay-optimized synthesis | p.446 |
| worst-case delay | 1.67 | nanoseconds | IBM CU-11 0.11 micron CMOS standard-cell library, copper interconnect (2002) | none | mask-based two's complement, 128-bit, delay-optimized synthesis | p.446 |
| worst-case delay | 0.86 | nanoseconds | IBM CU-11 0.11 micron CMOS standard-cell library, copper interconnect (2002) | none | mask-based one's complement, 8-bit, delay-optimized synthesis | p.446 |
| worst-case delay | 1.08 | nanoseconds | IBM CU-11 0.11 micron CMOS standard-cell library, copper interconnect (2002) | none | mask-based one's complement, 16-bit, delay-optimized synthesis | p.446 |
| worst-case delay | 1.22 | nanoseconds | IBM CU-11 0.11 micron CMOS standard-cell library, copper interconnect (2002) | none | mask-based one's complement, 32-bit, delay-optimized synthesis | p.446 |
| worst-case delay | 1.44 | nanoseconds | IBM CU-11 0.11 micron CMOS standard-cell library, copper interconnect (2002) | none | mask-based one's complement, 64-bit, delay-optimized synthesis | p.446 |
| worst-case delay | 1.74 | nanoseconds | IBM CU-11 0.11 micron CMOS standard-cell library, copper interconnect (2002) | none | mask-based one's complement, 128-bit, delay-optimized synthesis | p.446 |
errors_and_checks: Structural VHDL simulations verified functionality. Overflow is detected for shift-left-arithmetic when shifted-out bits differ from the sign bit; zero detection NORs the unmasked result bits. The paper reports no detection-coverage or false-alarm measurements. # p.439, p.441-444
conditions: Mask-based data reversal has the lowest delay at every tested width because zero/overflow detection runs in parallel with rotation and no shift/rotate-selection multiplexor delay is added. Either data-reversal design has the lowest area depending on operand width. The synthesized area grows as O(nlog(n)) and delay grows as O(log(n)). # p.445-446
evidence: §3.1-3.5, Figures 1-11, Tables 3-4, pp.437-446

## new_families
none

## space_gaps
* barrel_mux_tree lacks a structure choice for mux/mask-based data reversal and complement-based bidirectional designs. # p.439-444
* barrel_mux_tree lacks a choice for parallel zero/overflow flag generation. # p.439-443
* direction_handling: amount_negation does not distinguish two's-complement amount generation from one's-complement generation plus a one-bit rotate stage. # p.443-444

## open_questions
* The paper does not report placed-and-routed measurements, power, clock frequency, or interconnect effects beyond using copper interconnect.
* The paper does not identify the exact standard-cell composition represented by one equivalent gate.
