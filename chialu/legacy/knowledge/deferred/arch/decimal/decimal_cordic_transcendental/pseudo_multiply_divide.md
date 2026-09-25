---
family: decimal_cordic_transcendental
pin: {recurrence: pseudo_multiply_divide}
---
# pseudo_multiply_divide

Meggitt's decimal recurrence: a pseudo divider forms digits q_j by
repeated subtraction while a modifier register updates the pseudo
divisor after each one, and a reversed pseudo multiplier consumes
those digits by repeated addition while updating the pseudo
multiplicand. Operation-dependent modifiers (zero, the divisor, the
shifted remainder, a stored constant, the shifted pseudo multiplicand)
select log, atan, sqrt, exp, tan and square, with ordinary multiply
and divide on the same paths.

Pseudo division is the pick for a small decimal machine whose
multiplier is repeated addition, because common hardware or one
microprogram serves every function: log and atan each cost about
three multiply times including the division, exp about three, tan
four, sin or cos about seven, and a square two. Accuracy is a few
units in the last digit, below 2.5 for log and atan with shifted
modifier rounding, and 3 for exp and the square. The argument ranges
are constrained per function, y/x < 2^10 - 1 for log, positive p with
p < 10 log 2 for exp and 0 <= p <= pi/2 for tan, while atan is
unrestricted. Against the CORDIC rotation recurrence, which shares
one 5221 angle sequence and a constant scale factor across circular
and hyperbolic functions, it carries a separate modifier schedule per
function; the processes are not restricted to decimal.

The family's space is opened by no unit template; the variant is documented for the knowledge base alone.

## references

meggitt_1962 -> J. E. Meggitt, "Pseudo Division and Pseudo Multiplication Processes", IBM Journal of Research and Development, vol. 6, no. 2, pp. 210-226, 1962
vazquez_2009b -> Vazquez, Villalba, Antelo, "Computation of Decimal Transcendental Functions Using the CORDIC Algorithm", 19th IEEE Symposium on Computer Arithmetic (ARITH-19), 2009
