---
handle: wang_2007b
citation: Wang, Schulte, "Decimal Floating-Point Adder and Multifunction Unit with Injection-Based Rounding", 18th IEEE Symposium on Computer Arithmetic (ARITH-18), 2007
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [decimal32, decimal64, decimal128]
authority: incremental
pages_read: pp.3–18 / 16 pages
---

## summary
The document proposes an IEEE P754 decimal floating-point divider using a piecewise-linear reciprocal approximation, modified Newton–Raphson iteration, remainder-based rounding, and a sequential decimal multiplier (pp.6–13). A synthesized decimal64 implementation has a 0.69 ns critical path and takes 150 cycles with its one-digit-per-cycle multiplier (pp.13–14).

## families
### decimal_newton  (role: proposes)
mechanism: The divider normalizes DPD operands into BCD, obtains an initial reciprocal by multiplying a table coefficient by a nine's-complement-modified divisor, and performs reduced-precision Newton–Raphson iterations. Each iteration replaces subtraction with nine's complementation and keeps the reciprocal below the exact value. A final multiplication produces an adjusted quotient, and a remainder-sign/zero test selects the correctly rounded result (pp.6–10).
choices:
  operation: divide   # p.6
  seed_digits: 3   # pp.13–14
  iterations: 3   # p.14
new_choices:
  intermediate_precision: iteration-dependent — Early multiplications use reduced precision while preserving digit doubling.   # p.8
slots:
  seed: operand_modification_multiply   # pp.6–7
  final_round: back_multiply_remainder   # pp.9–10
parameters: decimal64; 64-bit storage; 16-digit significand; k=3; m=3; 20-digit sequential multiplier; one multiplier digit per cycle; 150-cycle division latency   # pp.13–14
results:
| metric | value | unit | technology / device | baseline | condition | page |
| critical-path delay | 0.69 | ns | LSI Logic Gflx-P 0.11 micron standard-cell library; 2007 | none | nominal conditions, 1.2 V, optimized for delay | p.13 |
| estimated logic area | 450877 | um² | LSI Logic Gflx-P 0.11 micron standard-cell library; 2007 | none | lookup table excluded | p.14 |
| division latency | 150 | cycles | LSI Logic Gflx-P 0.11 micron standard-cell library; 2007 | none | decimal64, k=3, 20-digit sequential multiplier, one digit/cycle | p.13 |
| division latency | 37 | cycles | UNKNOWN; 2007 | none | decimal64, k=3, three-cycle parallel multiplier | p.14 |
| latency reduction | about 32% | percent | UNKNOWN; 2007 | one-digit-per-cycle multiplier | decimal64, two multiplier digits/cycle | p.14 |
errors_and_checks: The iterations continue until |εRm| < 10^(-n-2), with εRm < 0. The rounding procedure supports RNE/RNA/RPI/RMI/RTZ plus RNT/RAZ and selects Q″T, Q″T+10^(-n), or Q″T−10^(-n) using the guard digit, quotient LSD, remainder sign/zero status, result sign, and rounding mode (pp.8–10).
conditions: The method more than doubles the number of accurate reciprocal digits per iteration, which favors large operands over one-digit-per-iteration decimal recurrence (pp.4, 8). Divider latency depends strongly on multiplier latency, and the multiplier-containing Block 2 occupies 64% of the reported logic area (p.14). Increasing k from 3 to 4 reduces decimal64 iterations from three to two but increases lookup memory from 2.5 KB to 54 Kbytes (p.14).
evidence: §§3–5; Tables 3–4; Figures 2–7; pp.6–15

### operand_modification_multiply  (role: extends)
mechanism: The normalized divisor is split into k leading digits XM and remaining digits XL. A DPD-indexed table supplies C0=1/(XM+5×10^(-k-1))², while operand modification retains XM and takes the nine's complement of selected XL digits. Multiplication of C0 by the modified operand produces a truncated reciprocal approximation below 1/X (pp.6–7).
choices:
new_choices:
  input_digits: k (implementation: 3) — The leading decimal digits index the coefficient table.   # pp.6, 13
  coefficient_digits: 2k — The table stores the most significant decimal digits of C0.   # p.7
  coefficient_encoding: DPD — DPD encoding reduces the coefficient-table memory.   # p.7
  operand_modification: nine_complement — Selected less-significant divisor digits are complemented before multiplication.   # pp.6–7
slots:
  none
parameters: k=3; C0 has 2k digits; R0 is truncated to 2k−1 digits; 2.5 KB lookup table   # pp.7, 13–14
results:
| metric | value | unit | technology / device | baseline | condition | page |
| guaranteed initial accuracy | at least 2k−3 | fraction digits | UNKNOWN; 2007 | none | k leading divisor digits index the table | p.7 |
errors_and_checks: The initial error satisfies −0.55×10^(-2k+3) < εR0 < 0, so the approximation remains below the exact reciprocal (p.7).
conditions: The method reads one coefficient and uses a multiplier rather than reading two coefficients and using a decimal multiply-accumulate unit (p.7).
evidence: §3.1, Equations 1–9, pp.6–8

### decimal_encoding_codec  (role: instantiates)
mechanism: IEEE P754 operands use DPD storage and are converted to BCD for internal arithmetic. Additional BCD-to-DPD and DPD-to-BCD logic surrounds the reciprocal lookup table so its address and coefficient use DPD (pp.4–5, 11).
choices:
  significand_encoding: dpd   # pp.4–5
  codec_placement: inside_operation   # p.11
new_choices:
  none
slots:
  none
parameters: three decimal digits per 10-bit DPD declet; k=3 coefficient lookup   # pp.4, 7
results:
| metric | value | unit | technology / device | baseline | condition | page |
| lookup-table size | 2.5 | KB | UNKNOWN; 2007 | 12 KB with 4-bit BCD table inputs/outputs | k=3 with DPD table encoding | p.7 |
errors_and_checks: none
conditions: Conversion around the table costs roughly two gate delays, while DPD reduces the memory requirement by more than a factor of four (p.7).
evidence: §2, §3.1, Figure 2, pp.4–7, 11

### iterative_decimal_multiplication  (role: instantiates)
mechanism: A modified version of Erle's sequential fixed-point decimal multiplier generates and accumulates partial products with decimal carry-save addition. The multiplier is reused for the initial approximation, Newton–Raphson iterations, preliminary quotient, and final remainder-related multiplication (pp.11–12).
choices:
  digits_per_cycle: 1   # p.13
new_choices:
  early_exit: true — Short multiplier operands reduce latency during the initial approximation and early iterations.   # p.12
slots:
  accumulator: csa_tree   # p.12
parameters: 20-digit multiplier; latency nmult+4 cycles; one digit processed per cycle in the synthesized divider   # pp.12–13
results:
| metric | value | unit | technology / device | baseline | condition | page |
| multiplier latency | nmult+4 | cycles | UNKNOWN; 2007 | none | nmult is the significant-digit count of the multiplier operand | p.12 |
errors_and_checks: none
conditions: A high-speed sequential or parallel decimal multiplier is required because multiplication latency controls overall divider latency (pp.12, 14).
evidence: §4, Figure 2, pp.11–14

## new_families
### decimal_incrementer_decrementer  (domain: decimal: decimal adders, closest: bcd_direct_addition, why_not: The circuit only adds or subtracts 10^(-n) and uses digit-propagate prefix logic rather than general two-operand decimal addition.)
mechanism: Each BCD digit generates an increment propagate when it equals nine and a decrement propagate when it equals zero. A mode-selected propagate signal feeds a parallel prefix tree because a carry or borrow propagates only through matching digits. The resulting carry/borrow selects the unchanged digit or its locally computed modulo-10 increment/decrement (pp.11–12).
choices: direction: {increment, decrement, both}; propagation: {ripple, parallel_prefix}; digit_code: {bcd8421}
results: none
evidence: §4.1, Equations 18–21, pp.11–12

## space_gaps
* `operand_modification_multiply` needs decimal digit-count/coefficient-encoding choices because its current bit-count choices cannot record the k-digit DPD seed method (p.7).
* `decimal_newton` needs an intermediate-precision policy choice for iteration-dependent truncation (p.8).
* `iterative_decimal_multiplication.final_adder` excludes decimal-adder families even though the instantiated multiplier uses a simplified decimal carry-propagate adder (p.12).
* The vocabulary lacks the proposed `decimal_incrementer_decrementer` used for quotient rounding (pp.11–12).

## open_questions
* The paper states that Erle's multiplier is “slightly” modified to reduce cycle time but does not specify the structural changes (p.12).
* The reported 450877 um² area excludes the lookup table, and no total area including that memory is reported (pp.13–14).
