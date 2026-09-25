# decimal_cordic_transcendental

Decimal shift-and-add digit recurrence for log, exp, trig, and sqrt.
The pseudo-multiply/divide form runs a repeated-subtraction pseudo
divider that emits digits q_j while a modifier register updates the
pseudo divisor after each subtraction, then a reversed repeated-addition
pseudo multiplier consumes those digits while updating the pseudo
multiplicand; modifiers and stored constants such as log(1 + 10^-j) or
atan(10^-j) select the function. The CORDIC form rotates through a
5221-coded elementary-angle sequence, four bit-weighted rotations per
decimal digit using only x5 and x2 scaling, with a constant scale
factor, in circular or hyperbolic coordinates and rotation or vectoring
mode.

The recurrence choice trades hardware sharing against latency and
range. The pseudo-multiply/divide recurrence shares its flow paths with
ordinary multiplication and division and runs under common hardware or
microprogram control, which makes it economical for small machines;
each function costs a few multiply times, leaves an error of a few
units in the last digit, and carries an argument restriction that keeps
the first pseudo-quotient digit below 10. The CORDIC recurrence serves
cos, sin, atan, sinh, cosh, atanh, exp, 10^x, ln, log10, and sqrt from
one angle sequence, and for Decimal128 one guard digit and three extra
fractional digits assure one-ulp accuracy. Fast termination replaces
about half the rotations with multiply-add or divide-add steps, so a
function takes 292 to 378 cycles on a Power6/Z10-class DFPU, which is
4.2 to 5.4 times a 70-cycle Decimal128 fixed-point multiply and well
below a table-driven polynomial on the same reduced range. The constant
store, about 14 Kbits against about 380 Kbits for radix-10 BKM, serves
every function.

The digit representation trades the iteration adder against iteration
length. Nonredundant BCD uses a carry-propagate adder per iteration and
resolves the rotation direction exactly. Redundant decimal keeps each
coordinate as two carry-save words with a decimal 3:2 adder, takes the
direction from the leading bits of the scaled control coordinate, and
relies on the redundancy of the 5221 angle sequence to survive a wrong
estimated sign without repeating an iteration; the adder is simpler but
each iteration is longer, and a terminal carry-propagate adder remains
for conversion and rounding. The angle table holds the elementary
angles and scale factors for the chosen fractional digits; mapping onto
an existing decimal FPU adds that table, its multiplexing, and minor
control, and floating point selects a variable starting index from the
reduced argument exponent.

The family is fixed-iteration and wins where a fully parallel decimal
multiplier is too costly in area and power and where many functions
share one datapath. It loses on latency to multiply-based evaluation
and wins on both cycles and storage against table-driven polynomials
for the fixed-point reduced-range portion.

No unit template opens `decimal_misc_space`: the family belongs to a decimal floating-point unit (or a conversion between number systems) that the ALU, dot and SFU templates do not provision, so no seed declares it and the library has no module for it; the BCD ALU's decimal adders, multipliers and dividers come from `chialu/targets/rtl/families/decimal.py`.

## references

meggitt_1962 -> J. E. Meggitt, "Pseudo Division and Pseudo Multiplication Processes", IBM Journal of Research and Development, vol. 6, no. 2, pp. 210-226, 1962
vazquez_2009b -> Vazquez, Villalba, Antelo, "Computation of Decimal Transcendental Functions Using the CORDIC Algorithm", 19th IEEE Symposium on Computer Arithmetic (ARITH-19), 2009
