# shared_across_formats

One decoder at the widest format serves every float mode; the mode selects the field boundaries. Pairs with the shared-across-formats rounder.

## the library's module

The seed instantiates the library's generated float module for this family
(`chialu/targets/rtl/families/fp.py`, value-exact against the engine: one decoder per lane of the mode (the cross-format sharing is the unit's grouping); denormal_handling in_unpack normalizes a subnormal).
The choice denormal_handling and the component families (lzc, shifter) select its sub-structures
from the library.

The form of the mode's X that the unpacked value enters, `exact` or `guard_round_sticky`, is the unit option `x_form` (docs/formats-and-options.md section 3.9); the unpacker follows the mode's geometry and makes no choice of its own there. Under `guard_round_sticky` with a separate multiplier, `denormal_handling: in_datapath` leaves the multiplier's folded product inexact for a subnormal operand, which the seed rejects at render (a deferred rule of chialu/behavior_rules.py).

## references
bruguera_1999 -> J. D. Bruguera and T. Lang, "Leading-One Prediction with Concurrent Position Correction", IEEE Transactions on Computers, 1999
burgess2005 -> N. Burgess, "Prenormalization Rounding in IEEE Floating-Point Operations Using a Flagged Prefix Adder", IEEE Transactions on VLSI Systems, 2005.
