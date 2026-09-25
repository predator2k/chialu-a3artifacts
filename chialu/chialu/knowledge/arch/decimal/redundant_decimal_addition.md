# redundant_decimal_addition

Carry-free decimal addition on a redundant digit set: each position
takes two digits plus a transfer from the position below, forms a
position sum, splits it into a transfer digit in {-1, 0, 1} for the
next position and an interim digit, and adds the incoming transfer to
the interim digit, so no carry travels beyond the adjacent position
and addition time is independent of digit count. The digit set fixes
the code: Svoboda's signed digits in a 5-bit character, RBCD digits in
[-7, 7] as 4-bit two's-complement codes, maximally redundant [-9, 9]
digits as binary signed-digit vectors, or overloaded digits that use
every 4-bit pattern from 0 to 15. A final conversion returns the
result to BCD.

The digit set trades storage and slice logic against conversion. The
[-7, 7] set fits the four bits a BCD digit already uses and negates by
two's complement; the original slice is two 4-bit binary adders with
two correction PLAs and runs in a constant 18 gate delays where an
n-digit BCD adder needs 7n, and the DSSD form of the same set, which
keeps the position sum as a two's-complement carry-save number,
reaches 7.80 FO4 against 13.56 FO4 for RBCD and is 40% faster than the
fastest prior design in 0.13 um. The maximally redundant set makes
BCD-to-redundant conversion free but leaves conversion back to BCD as
a carry-generating step. The overloaded set defers the +6 correction
to the next iteration and cleans up to BCD only on exit, at 8 logic
levels per iterative stage against 10 for decimal 4:2 compression.

Making only one operand redundant fits the recurrences the family
serves: divisor multiples and secondary multiples arrive in BCD, the
BCD operand converts at no delay, and a slice whose second operand is
zero drops its first adder level. Final conversion through a
carry-propagate adder is the price of the representation, and it makes
a single isolated addition no faster than BCD; the family wins only
when repeated arithmetic stays redundant so the conversion is paid
once, which is why it lives inside multiplier reduction trees,
division recurrences, FMA alignment paths, and accumulators. The
arithmetic is exact and the execution is feed-forward.

The seed instantiates the library's generated decimal adder for this family (`chialu/targets/rtl/families/decimal.py`: the operands recoded into the digit set (Svoboda's -6..6, RBCD -7..7, the maximally redundant -9..9 or the overloaded 0..15), one or both operands redundant, the carry-free two-step addition of interim digits and transfers, the final conversion to BCD by a carry-propagate borrow chain or by the two-candidate digit select over a borrow prefix (`final_conversion`)). `python3 -m chialu.targets.rtl.families.decimal --digits 4 --kind adder --family redundant_decimal_addition` emits it for a rewrite.

## design choices

### complement_generation

| member | what it selects |
| --- | --- |
| `subtract_from_power` | the nines' complement of a digit as the subtraction 9 - d. |
| `nines_digitwise_plus_one` | the same complement as a bit formula over the digit's four bits. |
| `trailing_zero_scan` | the tens' complement directly, the first nonzero digit found by a prefix scan. |

### final_conversion

| member | what it selects |
| --- | --- |
| `carry_propagate_adder` | the positive digits less the negative ones through a borrow chain. |
| `on_the_fly` | the digit and the digit less one are kept as a pair and selected by a borrow prefix, so no borrow ripples. |

## references

svoboda_1969 -> Svoboda, "Decimal Adder with Signed Digit Arithmetic", IEEE Transactions on Computers, 1969
shirazi_1989 -> Shirazi, Yun, Zhang, "RBCD: Redundant Binary Coded Decimal Adder", IEE Proceedings E - Computers and Digital Techniques, 1989
gorgin_2009 -> Gorgin, Jaberipur, "Fully Redundant Decimal Arithmetic", 19th IEEE Symposium on Computer Arithmetic (ARITH-19), 2009
kenney_2004 -> Kenney, Schulte, Erle, "A High-Frequency Decimal Multiplier", IEEE International Conference on Computer Design (ICCD), 2004
nikmehr_2006 -> Nikmehr, Phillips, Lim, "Fast Decimal Floating-Point Division", IEEE Transactions on Very Large Scale Integration (VLSI) Systems, 2006
han_2016 -> Han, Zhang, Ko, "Decimal Floating-Point Fused Multiply-Add with Redundant Internal Encodings", IET Computers & Digital Techniques, 2016
