# bcd_direct_addition

Decimal addition on 4-bit coded digits: each position adds two
digits and a decimal carry-in, and because the binary sum of 8421
digits is correct only up to 9, the position either adds a
corrective 6 after the binary sum when a decimal carry emerges, adds
6 to one operand before the binary sum so that any digit sum above
15 produces the decimal carry directly, or forms the sum bits and
the decimal generate/propagate terms straight from the operand bits
without a binary sum at all. The digit carries then ripple, combine
through byte-level lookahead, or come from a Kogge-Stone network
over digit generate/propagate signals, and the sum digit is selected
one level behind its carry.

The digit code fixes the correction: 8421 corrects by 0 or 6 and is
the code of every shipping unit and of the converters that finish
decimal multipliers, excess-3 corrects by 3 or 13 and lets a 76-bit
binary adder with parallel flag generation carry the addition, and
both codes bypass a digit whose uncarried sum is 9 with one AND and
one OR. Correction placement trades logic levels against candidate
sums: correcting after the binary sum in a shared binary/decimal
adder costs two additional logic levels, adding 6 before the carry
network overlaps correction with carry at the price of four
candidate sums per digit (A+B, A+B+1, A+B+6, A+B+7) or a pre- and
post-correction pair, and direct decimal carry logic avoids the
correction levels at about 18 percent more circuitry than a 32-bit
binary adder of the same depth. The carry scheme sets the
width-dependent delay: rippled digit carries, two-digit byte
lookahead that delivers all sums of an eight-digit adder in six logic
levels or less, or full lookahead through a prefix network, where a
64-bit BCD adder takes 1.40 ns and 1422 gates against 11.03 ns and
955 gates for the conventional rippled and corrected form in TSMC
0.18 um. The digit adder slot names the binary cell inside each
position, and is empty when the direct logic forms the sum itself.

The family is the final assimilation of parallel and iterative
decimal multipliers, whose reduction trees deliver radix-10
carry-save digits, and the significand adder of decimal
floating-point adders and fused multiply-adders, where a 32-digit
converter takes 0.40 ns and 10,000 um2 in 90 nm. A dedicated
decimal adder approaches binary-adder cost and performance, while a
shared binary/decimal adder pays the correction levels and BCD
itself costs 20.4 percent more storage and datapath than binary of
the same range. The result is exact for valid BCD digits 0 through
9; subtraction needs the nine's complement with carry-in 1 or the
fifteen's complement pre-correction.

The seed instantiates the library's generated decimal adder for this family (`chialu/targets/rtl/families/decimal.py`: 4-bit digit adders from the binary adder library (`digit_adder`), the +6 correction before or after the digit sum or a decimal carry from the digit's generate and propagate (`correction_placement`), the carries rippled, looked ahead per four-digit group or over the word (`carry_scheme`), BCD 8421 or excess-3 digits (`digit_code`), the subtraction by the tens' complement, by the nines' complement with the end-around carry or by a separate borrow chain (`subtraction`), the complement digits by 9 - d, by the digitwise formula or by the trailing-zero scan (`complement_generation`)). `python3 -m chialu.targets.rtl.families.decimal --digits 4 --kind adder --family bcd_direct_addition --pins k=v,...` emits it for a rewrite.

## design choices

### complement_generation

| member | what it selects |
| --- | --- |
| `subtract_from_power` | the nines' complement of a digit as the subtraction 9 - d. |
| `nines_digitwise_plus_one` | the same complement as a bit formula over the digit's four bits, which costs no subtractor. |
| `trailing_zero_scan` | the tens' complement directly: a prefix scan finds the first nonzero digit, which is complemented to 10 - d while the digits above take 9 - d and the zeros below stay, so no carry enters the low digit. |

### subtraction

| member | what it selects |
| --- | --- |
| `tens_complement_discard_carry` | a - b as a plus the nines' complement of b with a carry into the low digit, the carry out of the top digit discarded. |
| `nines_complement_end_around_carry` | the same complement with the top carry recirculated into the low digit instead of a carry-in. |
| `direct_borrow_subtracter` | a borrow chain of its own beside the adder, so the subtraction does not pass through a complement. |

## realization

| claim | pins | the module header matches |
| --- | --- | --- |
| the digit adders carry a +6 correction whose placement the module states | - | `correction presum_plus6|correction \w+, carries` |

## references

schmookler_1971 -> Schmookler, Weinberger, "High Speed Decimal Addition", IEEE Transactions on Computers, 1971
richards_1955 -> Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
schmookler_1972 -> Schmookler, "Considerations in the Design of a High Speed Decimal Unit", 2nd IEEE Symposium on Computer Arithmetic (ARITH-2), 1972
bayrakci_2007 -> Bayrakci, Akkas, "Reduced Delay BCD Adder", IEEE ASAP, 2007
schwarz_2002 -> E. M. Schwarz, M. A. Check, C.-L. K. Shum, et al., "The Microarchitecture of the IBM eServer z900 Processor", IBM Journal of Research and Development, vol. 46, no. 4/5, pp. 381-395, 2002
busaba_2001 -> Busaba, Krygowski, Li, Schwarz, Carlough, "The IBM z900 Decimal Arithmetic Unit", 35th Asilomar Conference on Signals, Systems and Computers, 2001
lang_2006 -> Lang, Nannarelli, "A Radix-10 Combinational Multiplier", 40th Asilomar Conference on Signals, Systems and Computers, 2006
vazquez_2014 -> Vazquez, Antelo, Bruguera, "Fast Radix-10 Multiplication Using Redundant BCD Codes", IEEE Transactions on Computers, 2014
