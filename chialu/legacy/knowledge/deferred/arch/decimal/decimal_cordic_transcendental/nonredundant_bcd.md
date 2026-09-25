---
family: decimal_cordic_transcendental
pin: {digit_representation: nonredundant_bcd}
---
# nonredundant_bcd

The carry-propagate form of the decimal CORDIC: x, y and z are held
as BCD words, each of the four bit-weighted rotations per decimal
digit runs through the carry-propagate iteration adder, and the
rotation direction sigma_i is read exactly from the sign of z[i] in
rotation mode or y[i] in vectoring mode. The datapath is p + 4
decimal digits wide for Decimal128 and spends 4 cycles per iteration,
562 cycles for the 140 elementary rotations without fast termination.

Nonredundant BCD is the pick when the existing DFPU adder is fast
enough for a 4-cycle iteration and the design change must stay small:
the mapping adds an angle and scale-factor lookup table,
table-to-datapath multiplexing and minor control, and the exact sign
of the control coordinate selects sigma_i without estimation. It keeps
the constant scale factor, the unified circular/hyperbolic angle
sequence, the variable start index J and fast termination, so the
Decimal128 function latencies of 292 to 378 cycles are those of this
form. The redundant decimal variant replaces the iteration adder by
decimal 3-to-2 carry-save addition and a 10-bit sign estimate, which
lengthens the iteration to 5 cycles and still needs a terminal
carry-propagate adder for conversion and rounding, so it trades one
extra cycle per iteration for simpler adder hardware.

The family's space is opened by no unit template; the variant is documented for the knowledge base alone.

## references

vazquez_2009b -> Vazquez, Villalba, Antelo, "Computation of Decimal Transcendental Functions Using the CORDIC Algorithm", 19th IEEE Symposium on Computer Arithmetic (ARITH-19), 2009
