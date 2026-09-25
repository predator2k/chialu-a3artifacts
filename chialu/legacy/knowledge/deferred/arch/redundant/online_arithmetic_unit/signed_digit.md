---
family: online_arithmetic_unit
pin: {residual_form: signed_digit}
---
# signed_digit

The residual is kept as a signed-digit word and updated by carry-free
or limited-carry signed-digit adders, single-digit multipliers and
concatenation, so each step is invariant in time. The result digit
is read from the leading residual digits: rounding sign(w) floor(|w|
+ 1/2) in the multiplier, comparison of the three leading digits
with truncated constants in the square root, or a fitter that maps
three leading digits to two with a limiter and sign detector in the
DNN engine.

It is the pick when the whole datapath stays signed-digit, so that
negation is a wire swap, subtractors reuse adder gates and
fixed-latency-one primitives compose in a nearest-neighbour digit
pipeline, as in the base-4 digit-pipelined system and the
programmable radix-2 add/multiply/divide unit for 600-digit numbers.
Its costs are two bits per residual digit and the sign-detection
logic that keeps a redundant residual in range; against carry_save a
preliminary analysis found no clear difference, so the choice
follows the surrounding arithmetic.

The unit streams digits over cycles; the family is an exception (`redundant.EXCEPTIONS`).

## references

trivedi_1977 -> Trivedi, Ercegovac, "On-Line Algorithms for Division and Multiplication", IEEE Transactions on Computers, 1977
oklobdzija_1982 -> Oklobdzija, Ercegovac, "An On-Line Square Root Algorithm", IEEE Transactions on Computers, 1982
irwin_owens_1987 -> Irwin, Owens, "Digit-Pipelined Arithmetic as Illustrated by the Paste-Up System: A Tutorial", IEEE Computer, 1987
guyot_1989 -> Guyot, Herreros, Muller, "JANUS, an On-Line Multiplier/Divider for Manipulating Large Numbers", 9th IEEE Symposium on Computer Arithmetic, 1989
moghaddasi_2024 -> Moghaddasi, Jaberipur, Javaheri, Nam, "RNPE: An MSDF and Redundant Number System-Based DNN Accelerator Engine", IEEE Access, 2024
