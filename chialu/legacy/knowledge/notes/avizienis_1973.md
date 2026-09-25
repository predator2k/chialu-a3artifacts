---
handle: avizienis_1973
citation: A. Avizienis, "Arithmetic Algorithms for Error-Coded Operands", IEEE Transactions on Computers, vol. C-22, pp. 567-572, 1973
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, other]
formats: [binary_fixed_point, AN_code, inverse_residue_code]
authority: landmark
pages_read: 567-572 / 6
---

## summary
The document gives addition, complementation, multiplication, division, roundoff, multiply-by-\(2^a-1\), and divide-by-\(2^a-1\) algorithms for AN-coded operands with \(A=2^a-1\) (pp.567-568). The document presents a constructed byte-serial radix-16 STAR processor using \(A=15\), then proves that a modulo-15 inverse-residue checker can support two's-complement arithmetic without a single erroneous carry-correction signal masking the associated arithmetic error (pp.568-571).

## families
### an_code  (role: instantiates)
mechanism: An uncoded operand \(X\) is represented as \(AX\), where the low-cost check modulus is \(A=2^a-1\) and the coded word length is \(ka\) bits. The STAR processor operates directly on 32-bit \(15X\) operands in 4-bit bytes. One's-complement addition supplies complementation and end-around carry. Coded multiplication forms \((2^a-1)^2XY\), divides by \(2^a-1\), and applies coded roundoff. Coded division first multiplies the dividend by \(2^a-1\) so that the quotient remains coded (pp.567-570).
choices:
  A: 15   # p.568
  code_distance: d2_detect   # p.568
  decode_point: domain_exit   # pp.568-570
new_choices:
  check_modulus_form: 2^a-1 — restricts the low-cost AN code to a Mersenne check modulus   # pp.567-568
  arithmetic_representation: ones_complement — enables complementable \(AX\) operands when \(2^n-1=AM\)   # pp.567-569
  processing_granularity_bits: 4 — moves coded operands and partial results byte-serially   # pp.568-569
  result_check_schedule: partial_and_final — sends partial/final arithmetic results to the external checker   # pp.569-570
slots:
  comparator: UNKNOWN   # p.569
parameters: \(A=15\); \(a=4\); 28-bit operand precision; 32-bit coded operands; radix 16; 4-bit data lines; three 8-byte shift registers; 10 byte times per processor cycle; eight multiply/divide steps; final results 8 bytes   # pp.568-570
results:
| metric | value | unit | technology / device | baseline | condition | page |
| fault-detection coverage | 100 | percent | JPL STAR processor; technology UNKNOWN; year UNKNOWN | none | single determinate repeated-use faults; 4-bit byte transmission/addition; coded operands up to 56 bits | p.568 |
| clear-add latency | 1 | cycle | JPL STAR processor; technology UNKNOWN; year UNKNOWN | none | 32-bit coded operand | p.569 |
| add/subtract latency without end-around carry | 1 | cycle | JPL STAR processor; technology UNKNOWN; year UNKNOWN | none | byte-serial operation | p.569 |
| multiplication latency | 14 to 28 | cycles | JPL STAR processor; technology UNKNOWN; year UNKNOWN | none | nonzero operands; depends on nonzero recoded multiplier digits | p.570 |
| multiplication latency for zero operand | 2 | cycles | JPL STAR processor; technology UNKNOWN; year UNKNOWN | none | zero detected on arrival | p.570 |
| division latency | 44 | cycles | JPL STAR processor; technology UNKNOWN; year UNKNOWN | none | nonzero operands; eight radix-16 quotient steps | p.570 |
errors_and_checks: A modulo-15 adder/accumulator expects the all-ones checksum after the perform-check signal; any other checksum issues a fault warning. The stated coverage is 100 percent for single determinate repeated-use faults under the processor's isolated 4-bit channels (pp.568-569).
conditions: Complementable AN coding requires \(A\) to divide \(2^n-1\); all \(n=ka\), \(A=2^a-1\) codes meet this condition (pp.567-568). AN coding requires one's-complement arithmetic and makes multiple-precision/floating-point operations relatively cumbersome (p.570). The experimental fixed-point placement gives \(-1/30<X<1/30\), while \(-1<X<1\) is unavailable with the stated simple sign/overflow algorithms (p.569).
evidence: Section II and Examples 1-3 (pp.567-568); Section III and Figs. 1-2 (pp.568-570); Appendix (pp.571-572).

### inverse_residue  (role: extends)
mechanism: The inverse-residue representation attaches \(X''=A-(A\mid X)\) to the uncoded main operand \(X\). A two's-complement main processor and a modulo-\(2^a-1\) check processor operate separately, except that a discarded main-processor carry-out increments the inverse-residue sum by one. The paper analyzes both erroneous assertion and erroneous inhibition of this correction signal and shows that the remaining \(2^j\) or \(-2^j\) discrepancy still causes disagreement between the main result and check result (pp.567, 570-571).
choices:
  modulus: 15   # p.571
  inverse_on: check_channel   # p.567
new_choices:
  main_arithmetic_representation: twos_complement — replaces the AN processor's one's-complement arithmetic   # pp.570-571
  carry_out_correction: increment_check_sum_modulo_2a_minus_1 — compensates for a discarded \(2^n\) carry in the main processor   # p.571
slots:
  comparator: UNKNOWN   # p.571
parameters: \(A=2^a-1\); \(n=ka\); demonstrated examples use \(A=15\) and 8-bit main operands   # p.571
results:
| metric | value | unit | technology / device | baseline | condition | page |
| fault-detection coverage for erroneous correction signal | 100 | percent | proposed inverse-residue processor; technology UNKNOWN; year UNKNOWN | none | single error either asserts or inhibits the discarded-carry correction signal under \(A=2^a-1,\ n=ka\) | p.571 |
errors_and_checks: The proof covers a fault that falsely asserts \(C_n=1\) and a fault that suppresses a required \(C_n=1\). Each case leaves a noncompensated error that makes the main result disagree with the inverse-residue check result (p.571).
conditions: Main/check processor independence is modified by the carry-out correction signal. The proof applies to \(A=2^a-1\) and \(n=ka\) (p.571).
evidence: Introduction's code definition (p.567); Section IV, Fig. 3, Cases 1-2, and Examples 4-5 (pp.570-571).

## new_families
none

## space_gaps
* `an_code` lacks choices for check-modulus form, one's-complement/two's-complement representation, byte granularity, and partial-result checking, although these choices determine the presented processor structure (pp.567-570).
* The `an_code` and `inverse_residue` comparator slots admit only `two_rail_tree`, while the document uses a modulo-15 checksum accumulator and equality test (pp.569, 571).
* `inverse_residue` lacks the discarded-carry correction policy required for two's-complement main arithmetic (p.571).
* The vocabulary lacks a checker-family slot that describes whether arithmetic remains encoded throughout the datapath or uses a separate main/check processor pair (pp.567, 571).

## open_questions
* The paper does not state the implementation technology or construction year of the experimental STAR AN-code processor.
* The paper states that the inverse-residue processor was selected as a replacement design, but it does not report whether the presented inverse-residue processor was constructed (pp.570-571).
* The paper does not quantify coverage for multiple simultaneous faults, transient faults, or faults outside the isolated repeated-use model.
