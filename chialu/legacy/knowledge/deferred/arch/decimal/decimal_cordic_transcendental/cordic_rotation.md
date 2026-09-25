---
family: decimal_cordic_transcendental
pin: {recurrence: cordic_rotation}
---
# cordic_rotation

A radix-10 CORDIC whose elementary angles come from the 5221 decimal
code, so each decimal digit is four bit-weighted rotations of weights
1, 5, 2, 2 and the x/y updates need only x5 and x2 scaling; one angle
sequence serves circular and hyperbolic coordinates in rotation and
vectoring modes with a constant scale factor. Floating-point operation
starts at a variable index J from the reduced argument exponent, and
fast termination replaces about half the rotations by a multiply-add
or divide-add.

CORDIC rotation is the pick for a Decimal128 unit that already has a
decimal fixed-point multiplier and divider and no room for a fully
parallel decimal multiplier: on a Power6/Z10-class DFPU it delivers
sin, cos and exp in 328 cycles, atan and ln in 375 to 378 and sqrt in
292 with fast termination, 4.2 to 5.4 times a 70-cycle Decimal128
multiply, against about 560 or 880 cycles for table-driven
polynomials, with 14 Kbits of constants where radix-10 BKM needs
about 380. Accuracy is one ulp with m = p + 1 iterations and p + 3
fractional digits. The nonredundant BCD datapath spends 4 cycles per
iteration and 562 cycles without termination; the carry-save version
costs 5. Meggitt's pseudo-division recurrence instead carries a
separate modifier schedule per function and runs at about three
multiply times per function on a repeated-addition machine.

The family's space is opened by no unit template; the variant is documented for the knowledge base alone.

## references

vazquez_2009b -> Vazquez, Villalba, Antelo, "Computation of Decimal Transcendental Functions Using the CORDIC Algorithm", 19th IEEE Symposium on Computer Arithmetic (ARITH-19), 2009
meggitt_1962 -> J. E. Meggitt, "Pseudo Division and Pseudo Multiplication Processes", IBM Journal of Research and Development, vol. 6, no. 2, pp. 210-226, 1962
