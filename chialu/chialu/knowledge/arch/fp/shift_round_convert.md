# shift_round_convert

Format conversion as the adder's slots re-aimed: float-to-integer
right-shifts the significand by the exponent through the align
shifter and rounds the bits that fall off, integer-to-float counts
the leading zeros, left-shifts the integer into a normalized
fraction, derives the exponent from the count and rounds where the
integer is wider than the fraction; narrowing between float formats
right-shifts and rounds (29 places from double to single) and
widening renormalizes. One shifter, one rounding stage and one
leading-one detector therefore serve every direction, either
overlaid on the addition datapath or gathered in a separate merged
conversion group.

Sharing the adder's datapath against a separate conversion group is
a sharing choice of the unit (the library's converter is the target
format's rounder over the source's internal value); it trades area
against latency and energy. Sharing the floating-point ALU costs only an integer leading-one detector,
multiplexers and control beyond the add/subtract hardware, and the
3DNow! conversions ride the adder's far path and its comparison and
rounding logic at two pipelined cycles; a separate merged conversion
group converts among every supported float format and the integers
in one cycle on a small core and two on a large one, with the
scalar casts costing 7.0 to 26.7 pJ at 22FDX and 0.8 V, more for
narrowing because the wide input datapath toggles, and its hardware
scales less than proportionally when formats are added.

The rounding modes and the overflow behavior are the mode's contract
(the engine's modes and IEEE overflow). Truncation only is what the packed conversions of 3DNow! use, at
odds with the round-to-nearest-even of their arithmetic, while the
five-mode form and the four-mode forms of the 8087 and AltiVec make
round-to-integral a directed operation; the posit core offers
nearest-even or toward-zero and needs toward-zero for its JPEG
output to match IEEE. Saturation returns the signed maximum normal
or the end of the integer range without a flag, which is the packed
and the posit choice, whereas the 8087 signals a precision exception
when the delivered result was rounded and converts every inbound
memory type to its 80-bit temporary real exactly, with the
destination precision chosen independently of the operands. The
shift_unit is bounded by the format: the 8087 shifts 0 to 63 places
in one clock with most-significant-one detection. Vector forms
convert four lanes with a scale factor per instruction or pick the
lower or upper source half when lane counts differ.

The load and store paths carry the conversion in product machines. A
single-to-double widening on load adds three exponent bits, which are
copies of the complement of the exponent's high-order bit, and pads
zeros into the low-order fraction bits; POWER7 writes the same rebias
as E' = E - 127 + 1023 = E + 896 with a 29-bit zero pad on the
fraction. A single-precision subnormal has no such pattern, so it is
either normalized at the conversion or held in a non-architected format
that carries a tag bit and an unnormalized significand. POWER7 rebiases
the subnormal's exponent to 381_16, normalizes the fraction and adjusts
the exponent by the normalization shift amount. Its register file holds
the exact architected bit pattern and gives each register a dirty flag
in place of the implied bit, where the earlier implementation held
single-precision subnormals in a 65-bit intermediate format including
that implied integer bit.

A single-precision store of a value held normalized but inside the
single denormal range needs the reverse shift, and Power4 takes it
through the multiply-add aligner rather than through the pipeline. The
store data enters the Add operand input of the multiply-add dataflow,
constants are forced into the exponents of the absent multiplier
operands so that their sum is Emin, and the aligner right-shifts the
significand by the difference of Emin and the exponent of the
normalized operand. A double-precision store of an unnormalized single
takes a prenormalization stall instead.

Reusing an adder's paths splits the conversions by direction. The
SPARC64 unit runs single-to-double and integer-to-float in the path
that holds the left shifter, which normalizes a denormal incoming
operand, and runs double-to-single and float-to-integer in the path
that holds the rounding, because the narrowing conversion needs
rounding and the float-to-integer needs an exponent-driven right shift.
That unit binds shifter to a one-hot-decoded barrel mux tree of 0/4/8/12
and 0/16/32/48 stages, and round to a compound adder selecting A+B and
A+B+2 with fill bits at the LSB and at LSB+1. Every conversion there
takes the 3-cycle add latency, except an integer-to-float that needs
rounding after the normalizing left shift, which costs one more cycle
because that path carries no rounding step. The family is feed-forward.

## the library's module

The seed instantiates the library's generated float module for this family
(`chialu/targets/rtl/families/fp.py`, value-exact against the engine: the target format's rounder over the source's internal value).
The component families (lzc, shifter, round, exp_adder, exp_incrementer) select its sub-structures
from the library.

## references

palmer_1980 -> J. F. Palmer, "The Intel 8087 Numeric Data Processor", Proc. 7th Annual Symposium on Computer Architecture, pp. 174-181, 1980.
asprey_1993 -> T. Asprey, G. S. Averill, E. DeLano, R. Mason, B. Weiner, J. Yetter, "Performance Features of the PA7100 Microprocessor", IEEE Micro, vol. 13, no. 3, pp. 22-35, 1993.
oberman_favor_1999 -> S. Oberman, G. Favor, F. Weber, "AMD 3DNow! Technology: Architecture and Implementations", IEEE Micro, vol. 19, no. 2, pp. 37-48, 1999.
diefendorff_2000 -> K. Diefendorff, P. K. Dubey, R. Hochsprung, H. Scales, "AltiVec Extension to PowerPC Accelerates Media Processing", IEEE Micro, vol. 20, no. 2, pp. 85-95, 2000
mach_2020 -> S. Mach, F. Schuiki, F. Zaruba, L. Benini, "FPnew: An Open-Source Multi-Format Floating-Point Unit Architecture for Energy-Proportional Transprecision Computing", arXiv:2007.01530, 2020
tiwari_2021 -> S. Tiwari, N. Gala, C. Rebeiro, V. Kamakoti, "PERI: A Configurable Posit Enabled RISC-V Core", ACM Transactions on Architecture and Code Optimization, 2021
schwarz_2003 -> E. M. Schwarz, M. Schmookler, S. D. Trong, "Hardware Implementations of Denormalized Numbers", 16th IEEE Symposium on Computer Arithmetic, 2003
boersma_2011 -> M. Boersma, M. Kroener, C. Layer, P. Leber, S. M. Mueller, K. Schelm, "The POWER7 Binary Floating-Point Unit", ARITH-20, 2011
naini_2001 -> A. Naini, A. Dhablania, W. James, D. Das Sarma, "1-GHz HAL SPARC64 Dual Floating Point Unit with RAS Features", ARITH-15, 2001
