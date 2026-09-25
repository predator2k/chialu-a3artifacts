# shared_across_formats

One rounder at the widest format's precision serves every float mode and lane; the mode selects the significand and exponent widths through a mux or a width mask. The largest sharing of the rounding logic in a multi-format unit; its delay is the widest format's.

## the library's module

The seed instantiates the library's generated float module for this family
(`chialu/targets/rtl/families/fp.py`, value-exact against the engine: one instance per lane of the mode (the cross-format sharing is the unit's grouping)).
The component families (lzc, shifter, round, exp_adder, exp_incrementer) select its sub-structures
from the library.

## the X form

The form of the mode's X, the unrounded value every producer delivers and this rounder packs, is the unit option `x_form` of `chialu.ALU` (docs/formats-and-options.md section 3.9) rather than a choice of this family: `exact` is the exact result (the multiplier's 2p-bit product and the adder's full window, an exponent of exp_bits + 8; the stochastic mode compares its dropped bits from this form), and `guard_round_sticky` is the raw form of a hardware unit (HardFloat's RawFloat, FPnew's rounding input): p + 3 significand bits with the sticky and an exponent of exp_bits + 3, which a producer folds what lies below into. The option serves float modes without conversion ops and without the stochastic mode; `round_fused_in_reduction` rounds within the product's frame and leaves the multiplier slot's menu under `guard_round_sticky` (chialu/behavior_rules.py).

## references
bruguera_1999 -> J. D. Bruguera and T. Lang, "Leading-One Prediction with Concurrent Position Correction", IEEE Transactions on Computers, 1999
burgess2005 -> N. Burgess, "Prenormalization Rounding in IEEE Floating-Point Operations Using a Flagged Prefix Adder", IEEE Transactions on VLSI Systems, 2005.
