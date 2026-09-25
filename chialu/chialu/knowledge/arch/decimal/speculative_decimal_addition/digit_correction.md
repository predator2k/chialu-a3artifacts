---
family: speculative_decimal_addition
pin: {speculation_target: digit_correction}
---
# digit_correction

The +6 digit correction is the speculated quantity: each digit's
uncorrected and corrected sums are precomputed before its carry
resolves, and the resolved carries select among the candidates, so the
correction overlaps the binary addition and the critical path is one
binary carry network. z900 keeps four candidate sums per digit for
addition and subtraction with +6 or -6; Vazquez's adder recodes
BCD-5211 into BCD-5421 and excess-3 so 4-bit binary additions yield
the decimal carries.

z900 adds, subtracts and compares 16 BCD digits in one cycle in 0.18
um CMOS without naming its carry topology. The shared 70-bit adder
computes two conditional digit sums and selects them with a 7-level
sparse prefix tree at 21.8 FO4 stage delay and 2600 NAND2, with a
late-carry network merging the optional rounding increment without
another carry pass. The rounding_increment sibling leaves the digit
correction to pre- and post-correction stages and speculates the IEEE
rounding value instead; the both sibling speculates the two together
through a compound adder. digit_correction is the pick for integer or
fixed-point decimal addition, for comparison, and for the final
addition inside a decimal multiplier, where no IEEE rounding is fused
and a plain dual_path_select recovery suffices.

## references

schwarz_2002 -> E. M. Schwarz, M. A. Check, C.-L. K. Shum, et al., "The Microarchitecture of the IBM eServer z900 Processor", IBM Journal of Research and Development, vol. 46, no. 4/5, pp. 381-395, 2002
vazquez_2009 -> Vazquez, Antelo, "A High-Performance Significand BCD Adder with IEEE 754-2008 Decimal Rounding", 19th IEEE Symposium on Computer Arithmetic (ARITH-19), 2009
