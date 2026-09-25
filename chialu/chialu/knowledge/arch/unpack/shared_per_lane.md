# shared_per_lane

One operand decoder per lane feeds every structure of the lane over an unpacked value bus (sign, exponent, significand, special-case class, denormal flag); the structures take the decoded value instead of the raw pattern.

## the library's module

The seed instantiates the library's generated float module for this family
(`chialu/targets/rtl/families/fp.py`, value-exact against the engine: one decoder per lane; denormal_handling in_unpack normalizes a subnormal).
The choice denormal_handling and the component families (lzc, shifter) select its sub-structures
from the library.

The form of the mode's X that the unpacked value enters, `exact` or `guard_round_sticky`, is the unit option `x_form` (docs/formats-and-options.md section 3.9); the unpacker follows the mode's geometry and makes no choice of its own there. Under `guard_round_sticky` with a separate multiplier, `denormal_handling: in_datapath` leaves the multiplier's folded product inexact for a subnormal operand, which the seed rejects at render (a deferred rule of chialu/behavior_rules.py).

## references
bruguera_1999 -> J. D. Bruguera and T. Lang, "Leading-One Prediction with Concurrent Position Correction", IEEE Transactions on Computers, 1999
burgess2005 -> N. Burgess, "Prenormalization Rounding in IEEE Floating-Point Operations Using a Flagged Prefix Adder", IEEE Transactions on VLSI Systems, 2005.
