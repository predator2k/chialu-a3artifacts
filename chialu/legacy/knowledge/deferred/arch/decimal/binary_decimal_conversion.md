# binary_decimal_conversion

Radix conversion by a shift-and-adjust recurrence: binary-to-decimal
shifts the source most-significant bit first through 4-bit BCD decades
and adds 3 to every decade holding 5 or more before each left shift;
decimal-to-binary shifts least-significant bit first the other way and
subtracts 3 from every decade holding 8 or more after each shift.
Decades have independent correction logic and cascade without limit.
The same recurrence unrolls into a combinational array of cells each
satisfying b+*10 + d+ = d*2 + b, or gives way to constant
multiplication: the value is scaled to a fraction and repeatedly
multiplied by a power of ten, each integer overflow yielding the next
digit group.

The structure choice trades operations per bit against hardware. The
sequential form costs four shift stages plus one correction network per
decimal digit and two operations per binary bit; fusing the test into
the shift theoretically halves that at higher complexity, direction is
fixed by wiring, and parallel loading needs per-decade disable gates.
The cell array is exact for integers once sized to the input range,
and cells that only shift or whose weight exceeds the input are
suppressed (33 cells at 13 cell delays for 16-bit integers against an
80-cell complete array); the digit code sets cell complexity, with
biquinary cells reaching n gate delays for n bits. Arrays suit small
numbers and sequential conversion wins above about 24 digits. Constant multiplication by 10
delivers one digit per operation at more than 3x the doubling speed;
x100 and x1000 deliver two or three digits per operation only with a
carry-save adder placing the shifted terms before the main adder, and
their overflow groups need a radix-100-then-10 decoder of one or two
operation times.

Digits per step is the chunk size of the iterative processor forms:
12 binary bits through three parallel tables and Horner combination by
x4096, or three decimal digits by x1000, with
leading-zero detection fixing the iteration count; four bits per cycle
through encoded decimal doublers of two gate delays each plus a 6:2
compressor accumulating three digits per iteration cuts cycles per
iteration by three, and more digits would need multiples of 10,000. A
larger chunk buys iterations with area and cycle time.

Integers convert exactly; fractions do not, and truncating the array at
level -k bounds the error by p^-k while a rounding term zeroes the
mean. Exact fixed-point integer output from the multiply form needs
extra product and adder bits plus a compensating constant. Conversion
is negligible when computation dominates I/O and a major burden when
little arithmetic touches large decimal volumes; accelerating it alone
is not worthwhile when scaling, unpacking and editing dominate. The
divide-by-10 cell also serves as the reduction stage of mixed
binary/BCD multioperand addition.

No unit template opens `decimal_misc_space`: the family belongs to a decimal floating-point unit (or a conversion between number systems) that the ALU, dot and SFU templates do not provision, so no seed declares it and the library has no module for it; the BCD ALU's decimal adders, multipliers and dividers come from `chialu/targets/rtl/families/decimal.py`.

## references

couleur_1958 -> Couleur, "BIDEC - A Binary-to-Decimal or Decimal-to-Binary Converter", IRE Transactions on Electronic Computers, 1958
nicoud_1971 -> Nicoud, "Iterative Arrays for Radix Conversion", IEEE Transactions on Computers, 1971
schmookler_1968 -> Schmookler, "High-Speed Binary-to-Decimal Conversion", IEEE Transactions on Computers, 1968
richards_1955 -> Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
busaba_2001 -> Busaba, Krygowski, Li, Schwarz, Carlough, "The IBM z900 Decimal Arithmetic Unit", 35th Asilomar Conference on Signals, Systems and Computers, 2001
carlough_2011 -> Carlough, Collura, Mueller, Kroener, "The IBM zEnterprise-196 Decimal Floating-Point Accelerator", 20th IEEE Symposium on Computer Arithmetic (ARITH-20), 2011
dadda_2007 -> Dadda, "Multioperand Parallel Decimal Adder: A Mixed Binary and BCD Approach", IEEE Transactions on Computers, 2007
buchholz_1959 -> Buchholz, "Fingers or Fists? (The Choice of Decimal or Binary Representation)", Communications of the ACM, 1959
