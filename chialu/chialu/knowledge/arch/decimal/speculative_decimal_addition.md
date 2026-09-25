# speculative_decimal_addition

BCD addition whose critical path is one binary carry network: the +6
digit correction, the IEEE rounding increment, or both are speculated
before the carry is known. Corrected and uncorrected digit sums are
precomputed and the carry network selects among them per digit, so the
+/-6 correction runs in parallel with the binary addition; or a binary
3:2 carry-save pre-correction adds the decimal bias conditionally, a
compound adder returns S and S+2, and digitwise post-correction plus
direct rounding logic pick the correctly rounded sign-magnitude BCD
result with no second carry propagation. Injection rounding adds a
mode- and sign-dependent value at the round/sticky positions before
the add, so most rounding becomes truncation.

The speculation target sets how much of the rounding path joins the
add. Digit correction alone yields a one-cycle 16-digit adder for
addition, subtraction and comparison in 0.18 um CMOS, with subtraction
precomputing a -6 candidate. Speculating both correction and rounding
gives the full IEEE 754-2008 significand adder at 26.1 FO4 and 3580
NAND2 for Decimal64 in a logical-effort model, against 1.16x the delay
and 1.25x the area for the injection-based design, and the rounding
modification adds a small constant delay independent of digit count.

Recovery decides where the speculation is repaired. Dual-path select
chooses among precomputed candidates: four per digit in the z900
adder, or the injection at digit p or p+1 in the z196 end-around-carry
adder, which evaluates the subtract magnitude without an operand
compare and selects after the most-significant digit resolves
carry-out or cancellation. A late correction stage instead applies the
injection correction through flags the prefix network already
produces; the trailing-nine flag stages sit off the critical path and
add about 14% to a Kogge-Stone network in 0.11 um CMOS.

The carry network is a plain binary prefix tree, a sparse tree with
conditional digit sums, a compound flagged prefix adder producing S
and S+2, or a carry-select adder for end-around carry. Correct
rounding in every IEEE mode is the contract: ties-to-even clears the
LSB on an exact halfway case, discarded nonzero digits raise Inexact,
and rounding is suppressed for an effective subtraction without a
right shift because the result may be negative. The family is the
significand adder of a decimal floating-point unit; a direct BCD adder
that corrects after the carry is the cheaper choice when the
correction may follow the carry chain.

The seed instantiates the library's generated decimal adder for this family (`chialu/targets/rtl/families/decimal.py`: +6 speculated on every digit of one operand, one binary carry network over the word from the `carry_network` family, the digits corrected after the sum or both candidates of every digit selected by its carry (`recovery`); with the rounding increment as the speculation target the sum and the incremented sum come from two networks and the carry-in selects). `python3 -m chialu.targets.rtl.families.decimal --digits 4 --kind adder --family speculative_decimal_addition` emits it for a rewrite.

## design choices

### complement_generation

| member | what it selects |
| --- | --- |
| `subtract_from_power` | the nines' complement of a digit as the subtraction 9 - d. |
| `nines_digitwise_plus_one` | the same complement as a bit formula over the digit's four bits. |
| `trailing_zero_scan` | the tens' complement directly, the first nonzero digit found by a prefix scan. |

## references

vazquez_2009 -> Vazquez, Antelo, "A High-Performance Significand BCD Adder with IEEE 754-2008 Decimal Rounding", 19th IEEE Symposium on Computer Arithmetic (ARITH-19), 2009
wang_2009 -> Wang, Schulte, Thompson, Jairam, "Hardware Designs for Decimal Floating-Point Addition and Related Operations", IEEE Transactions on Computers, 2009
schwarz_2002 -> E. M. Schwarz, M. A. Check, C.-L. K. Shum, et al., "The Microarchitecture of the IBM eServer z900 Processor", IBM Journal of Research and Development, vol. 46, no. 4/5, pp. 381-395, 2002
carlough_2011 -> Carlough, Collura, Mueller, Kroener, "The IBM zEnterprise-196 Decimal Floating-Point Accelerator", 20th IEEE Symposium on Computer Arithmetic (ARITH-20), 2011
