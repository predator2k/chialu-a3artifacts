---
handle: rowen_1988
citation: C. Rowen, M. Johnson, P. Ries, "The MIPS R3010 Floating-Point Coprocessor", IEEE Micro, vol. 8, no. 3, pp. 53-62, 1988.
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [fp32, fp64, int32]
authority: landmark
pages_read: 53-62 / 10
---

## summary
The R3010 is a hardwired IEEE floating-point coprocessor with independent add, multiply, divide, and register units that can execute concurrently (pp.53, 56-59). The multiplier uses Booth encoding and carry-save iteration, while the divider uses radix-4 redundant SRT division with two iterations per cycle (pp.57-58). A shared add unit performs final carry propagation and IEEE rounding for multiplication and division (pp.56-58).

## families
### srt_high_radix  (role: instantiates)
mechanism: The divide unit uses radix-4 redundant nonrestoring SRT division with quotient digits 2, 1, 0, -1, and -2. Mantissa partial remainders remain in carry-save form. A fast 9-bit carry-propagate adder reduces the most significant remainder pieces, and a lookup-table PLA uses that sum and divisor bits to select the next quotient digit. Two iterations execute per cycle. (pp.57-58)
choices:
  radix: 4   # pp.57-58
new_choices:
  quotient_digit_set: {-2, -1, 0, 1, 2} — redundant symbols used to encode the quotient   # pp.57-58
slots:
  digit_select: qds_table   # p.57
parameters: 9 partial-remainder bits examined; two iterations per cycle; 4 quotient bits per cycle; 12-cycle single-precision divide; 19-cycle double-precision divide   # pp.57-58
results:
| metric | value | unit | technology / device | baseline | condition | page |
| quotient production rate | 4 | bits per cycle | 1988 R3010; double-metal CMOS; 1.6 pm average lithographic features; transistor lengths below 1 pm | UNKNOWN | radix-4 redundant SRT | pp.57-59 |
| register-to-register divide latency | 19 | cycles | 1988 R3010; double-metal CMOS; 1.6 pm average lithographic features; transistor lengths below 1 pm | MC68882: 78 cycles | double precision | p.54 |
| memory-to-register divide latency | 21 | cycles | 1988 R3010; double-metal CMOS; 1.6 pm average lithographic features; transistor lengths below 1 pm | MC68882: 78 cycles | double precision; zero wait states/cache misses | p.54 |
errors_and_checks: A nonzero final remainder causes guard/round/sticky adjustments and IEEE status flags such as Inexact; the quotient then receives final carry propagation and IEEE rounding in the add unit.   # p.57
conditions: Carry-save partial remainders avoid full-width carry propagation during each iteration, but quotient selection requires a 9-bit carry-propagate adder and lookup-table PLA.   # p.57
evidence: “Implementation of the Divide Unit” box, pp.57; divide-unit description and Figure 3, pp.57-58; Tables 1-2, p.54.

### sig_div_then_round  (role: instantiates)
mechanism: The divide unit produces a redundant quotient and partial remainder in carry-save form. The add unit performs final carry propagation, guard/round/sticky adjustment, and IEEE rounding. (pp.57-58)
choices:
new_choices:
  none
slots:
  sig_div: srt_high_radix [radix=4]   # pp.57-58
parameters: fp32 latency 12 cycles; fp64 latency 19 cycles   # pp.54, 57
results:
| metric | value | unit | technology / device | baseline | condition | page |
| divide latency | 12 | cycles | 1988 R3010; double-metal CMOS; 1.6 pm average lithographic features; transistor lengths below 1 pm | UNKNOWN | single precision; total operation latency | pp.54, 57 |
| divide latency | 19 | cycles | 1988 R3010; double-metal CMOS; 1.6 pm average lithographic features; transistor lengths below 1 pm | UNKNOWN | double precision; total operation latency | pp.54, 57 |
errors_and_checks: Final quotient adjustment uses guard, round, and sticky information; a nonzero remainder sets IEEE status flags, including Inexact.   # p.57
conditions: Multiply and divide share the add unit’s exponent datapath and rounding function, so the control unit schedules operations to prevent simultaneous demand for those resources.   # p.58
evidence: “Implementation of the Divide Unit” box, p.57; Figures 3-4 and scheduling description, pp.58-59.

### sig_mul_then_round  (role: instantiates)
mechanism: The multiply unit forms a carry-save significand product and returns it to the add unit. The add unit performs final carry propagation and IEEE rounding in another cycle. (pp.57-58)
choices:
new_choices:
  none
slots:
  none
parameters: two 53-bit operands; 106-bit product; most significant 56 bits retained; about 14 bits per cycle; final add-unit rounding cycle   # p.57
results:
| metric | value | unit | technology / device | baseline | condition | page |
| multiply latency | 4 | cycles | 1988 R3010; double-metal CMOS; 1.6 pm average lithographic features; transistor lengths below 1 pm | UNKNOWN | single precision; final IEEE-rounded result | p.54 |
| multiply latency | 5 | cycles | 1988 R3010; double-metal CMOS; 1.6 pm average lithographic features; transistor lengths below 1 pm | UNKNOWN | double precision; final IEEE-rounded result | p.54 |
| register-to-register multiply latency | 5 | cycles | 1988 R3010; double-metal CMOS; 1.6 pm average lithographic features; transistor lengths below 1 pm | MC68882: 46 cycles | double precision | p.54 |
errors_and_checks: The add unit produces the final IEEE-rounded multiplication result.   # pp.56-58
conditions: Five carry-save iterations fit in one cycle. Input latching, Booth encoding, sticky-bit computation, control, and result drive add about one cycle; final rounding uses another add-unit cycle.   # p.57
evidence: “Implementation of the Multiply Unit” box, p.57; Tables 1-2, p.54; Figures 3-4, pp.58-59.

## new_families
### iterative_booth_carry_save_multiplier  (domain: mul: integer multipliers, closest: sequential_shift_add, why_not: `sequential_shift_add` lacks Booth recoding, paired carry-save iteration, and multiple unrolled iterations per cycle)
mechanism: Booth-encoded multiplier bits reduce 56 shift-and-add iterations to 28. Carry-save adders remove the carry-chain delay, and paired adders process even- and odd-numbered partial products. Five carry-save iterations execute in each cycle, producing a double-precision product in carry-save form in a little less than four cycles before the add unit performs final rounding. (p.57)
choices:
  recoding: {booth_encoded}
  partial_product_pairing: {even_odd_pairs}
  accumulator_form: {carry_save}
  iterations_per_cycle: Int[1..5:1]
results:
| metric | value | unit | technology / device | baseline | condition | page |
| shift-and-add iterations | 28 | iterations | 1988 R3010; double-metal CMOS; 1.6 pm average lithographic features; transistor lengths below 1 pm | traditional algorithm: 56 iterations | Booth-encoded 56-bit mantissa multiply | p.57 |
| carry-save iteration rate | 5 | iterations per cycle | 1988 R3010; double-metal CMOS; 1.6 pm average lithographic features; transistor lengths below 1 pm | UNKNOWN | paired carry-save adders | p.57 |
| carry-save product latency | a little less than four | cycles | 1988 R3010; double-metal CMOS; 1.6 pm average lithographic features; transistor lengths below 1 pm | UNKNOWN | double-precision result before final add-unit rounding | p.57 |
evidence: “Implementation of the Multiply Unit” box, p.57.

## space_gaps
* `sig_mul_then_round.sig_mul` cannot name the document’s iterative Booth/carry-save multiplier; the slot needs the proposed `iterative_booth_carry_save_multiplier` family.   # p.57
* `srt_high_radix` lacks a choice that records the explicit quotient digit set {-2, -1, 0, 1, 2}.   # pp.57-58
* The floating-point multiply/divide families lack a slot value for a shared add unit that performs final carry propagation and IEEE rounding for both units.   # pp.56-58

## open_questions
* The document says Booth encoding reduces 56 iterations to 28 but does not name the Booth radix, so `booth_radix` must remain UNKNOWN.
* The document states that two divide iterations execute per cycle but does not identify them as `overlapped_stages`, so that choice must remain UNKNOWN.
* The multiply description refers both to a “56-bit mantissa multiply” and to two 53-bit operands whose 106-bit product retains 56 bits; the merge pass must preserve this distinction.
