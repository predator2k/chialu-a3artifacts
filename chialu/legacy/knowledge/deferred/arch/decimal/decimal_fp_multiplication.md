# decimal_fp_multiplication

IEEE 754 decimal multiplication with one rounding and no addend: the
DPD operands are decoded to BCD significands, a fixed-point decimal
multiplier forms the 32-digit product while the sign and exponent are
generated in parallel and the operand leading-zero counts estimate
the left shift and result exponent, the product is shifted, split
into a truncated field and a fraction, the sticky is generated, the
result is rounded by selecting the truncated significand or its
increment, exceptions are handled, and the result is encoded to DPD.
The core is an iterative decimal multiplier at 25 cycles for
decimal64 or a parallel tree pipelined to one result per cycle.

The significand multiplier slot fixes the execution style: an
iterative core runs one multiplier digit per cycle under fixed
iteration and generates the sticky on the fly during accumulation,
while a parallel core ORs the shifted-out digits after the final
carry-propagate adder. Sticky generation follows that split.
Subnormal handling trades latency against hardware: the iterative
core extends its iterations for gradual underflow, from 25 to 43
cycles, while the parallel core traps to software or adds a
bidirectional shifter. The rounding choice places the increment
either inside a decimal compound adder that yields the truncated
significand and its increment at once, from which the mode selects,
or in an incrementer followed by the select; the rounding adder slot
holds that adder. Pipeline stages span combinational through 12; the
reported parallel design selects 12 stages, and area is not monotonic
in depth.

Against the iterative core, the 11-stage parallel design cuts latency
from 25 to 11 cycles and raises throughput from one product every 21
cycles to one per cycle, at 371% of the sequential area in 0.11 um.
The family wins for a throughput-bound decimal64 multiply stream and
loses to the iterative core where area rules. The shift estimate from
the operand leading-zero counts, formed in parallel with the
multiply, keeps the post-product path to one shift and one rounding
in both forms. Against decimal_fma the unit has no addend alignment
and no merged tree, so the shift and exponent come from the operand
leading-zero counts alone.

No unit template opens `decimal_misc_space`: the family belongs to a decimal floating-point unit (or a conversion between number systems) that the ALU, dot and SFU templates do not provision, so no seed declares it and the library has no module for it; the BCD ALU's decimal adders, multipliers and dividers come from `chialu/targets/rtl/families/decimal.py`.

## references

erle_2009 -> Erle, Hickmann, Schulte, "Decimal Floating-Point Multiplication", IEEE Transactions on Computers, 2009
hickmann_2007 -> Hickmann, Krioukov, Schulte, Erle, "A Parallel IEEE P754 Decimal Floating-Point Multiplier", IEEE International Conference on Computer Design (ICCD), 2007
