# logarithmic_converters

Binary-to-logarithm conversion and the arithmetic built on it: the
input is written N = 2^k (1+x), the characteristic k is the position
of the leading one, the remaining bits are the mantissa x, and
log2(1+x) is approximated by x plus a correction, which may be
nothing, a per-region constant or linear term, or shift-add terms
with power-of-two constants. In a full logarithmic ALU
multiply and divide become fixed-point add and subtract of the logs,
square root a right shift, and add and subtract evaluate
F(r) = log2(1 +/- 2^r) by linear interpolation with a stored maximum
interval error scaling a correction template.

The correction and region choices trade error against hardware and
control. With no correction the straight-line approximation carries
the largest error; four region-dependent linear corrections applied
as sequential shift-adds bring a 7-bit converter to a maximum error
of 0.013, and more segments cut the error further at more hardware
and, in the sequential form, more computation time. Two symmetric
regions whose slopes are inverses, with constants that need no ROM
or multiplier, give an error range 47.7 percent below the plain
straight line and 24 percent below the earlier two-region converter,
at 2.8 ns and 5586 µm² for a 32-bit input in TSMC 0.13 µm; more
accurate constants cost more shifts unless they are recoded in
canonic signed digits. Only the top fraction bits need conversion
while the low bits pass through.

The full-ALU choice adds the addition and subtraction tables: the
32-bit European logarithmic microprocessor stores 322 kbit of ROM,
the 20-bit version 11 kbit, keeps the add and subtract error within
the 0.5 LSB-relative limit of same-width floating point, and uses a
range shifter for subtractions of nearly equal operands, which
remain less accurate than floating point because that case is exact
there. Multiplication and division then carry no rounding error, so
execution time falls to about 64 percent of a 32-bit floating-point
unit at an even add and multiply mix in 0.7-µm standard cells, and
the gain grows with the share of multiplies, divides and square roots
in the workload. The family is the pick when multiplications dominate
or when a cheap approximate logarithm feeds a logarithmic multiplier,
and it loses to floating point when additions of close operands
dominate or when the table storage exceeds the budget.

The seed instantiates the library's generated module for this family (`chialu/targets/rtl/families/sfu.py`: Mitchell's log and antilog identities with the `correction` (none, a constant per region, a piecewise-linear correction over `regions`, or the ROM-free shift-add term), `lns_full_alu` taking the reciprocal and the roots through the log domain). `python3 -m chialu.targets.rtl.families.sfu --function <fn> --format <format> --family logarithmic_converters --pins k=v,...` emits the module with its modeled error for a rewrite.

## design choices

### correction

| member | what it selects |
| --- | --- |
| `none` | Mitchell's uncorrected logarithm. |
| `constant_per_region` | one constant per region is added to the logarithm. |
| `pwl_correction` | a piecewise-linear correction is added. |
| `rom_free_shift_add` | the correction is shift-add terms rather than a table. |

## references

combet1965 -> M. Combet, H. Van Zonneveld, L. Verbeek, "Computation of the Base Two Logarithm of Binary Numbers", IEEE Transactions on Electronic Computers, vol. EC-14, no. 6, pp. 863-867, 1965
juang_2009 -> T.-B. Juang, S.-H. Chen, H.-J. Cheng, "A Lower Error and ROM-Free Logarithmic Converter for Digital Signal Processing Applications", IEEE Transactions on Circuits and Systems II, vol. 56, no. 12, pp. 931-935, 2009
coleman_2000 -> J. N. Coleman, E. I. Chester, C. I. Softley, J. Kadlec, "Arithmetic on the European Logarithmic Microprocessor", IEEE Transactions on Computers, vol. 49, no. 7, pp. 702-715, 2000
