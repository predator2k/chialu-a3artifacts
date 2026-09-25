---
family: decimal_cordic_transcendental
pin: {digit_representation: redundant_decimal}
---
# redundant_decimal

Each coordinate is held as two decimal carry-save words and updated
with a decimal 3-to-2 adder, two shifts and two 3-to-2 additions per
x/y iteration, so no carry propagates inside the loop. The rotation
direction is taken from the leading bits of the scaled carry-save
control coordinate through a 10-bit sign detector (one sign, five
integer and four fractional bits), and the redundancy of the 5221
angle sequence absorbs a wrong estimated sign without repeating any
iteration.

The redundant form is the pick when the carry-propagate iteration
adder is the part to remove: it replaces that adder by simpler
carry-save hardware in three pipeline stages at an assumed 13 FO4
cycle, at the price of 5 cycles per iteration against 4 for the BCD
form, 1.25 times more. A 10-bit sign estimate with t = 4 fractional
bits assures convergence for circular rotation despite the bounded
wrong-sign case; the derivation is restricted to circular rotation,
the numerical error of the complete redundant floating-point unit is
not reported, and a terminal carry-propagate adder remains necessary
for conversion and rounding. The nonredundant BCD form keeps the
exact sign selection and the shorter iteration and is the source of
the reported Decimal128 function latencies.

The family's space is opened by no unit template; the variant is documented for the knowledge base alone.

## references

vazquez_2009b -> Vazquez, Villalba, Antelo, "Computation of Decimal Transcendental Functions Using the CORDIC Algorithm", 19th IEEE Symposium on Computer Arithmetic (ARITH-19), 2009
