---
family: parity_prediction_multiplier
pin: {recoding: none}
---
# none

Parity prediction over an unrecoded multiplier: AND gates generate the
partial products, which enter a Braun array or a Wallace full-adder and
half-adder network whose cells use redundant carries, and the parity of
those carries combines with the operand parities to predict the product
parity. The fault-secure argument is cellular, so a ripple final adder
keeps it, while a carry-lookahead final adder needs redundant carries
and a double-rail checker of its own.

This is the pick when the multiplier has no Booth recoding to protect,
since it needs no decoder duplication and no sign-extension
restructuring, and the choice of cell sets the cost: independent
redundant-carry cells cost about 75 to 80 percent extra area on a Braun
array in 1.0 um CMOS, shared-propagate cells about 47 percent at a
longer worst-case parity path, and delay overhead shrinks as width
grows. It covers modeled single faults in cells and AND gates;
primary-input faults need input checking where a zero partial-product
parity would mask an operand fault. The Booth-recoded sibling is the
alternative once radix-4 recoding is already in the datapath.

The generated checker realizes this variant (`checker.recoding: none`): an AND array of rows, the sign row of a two's complement operand weighing minus 2^(w-1).

## references

nicolaidis_1997 -> M. Nicolaidis, R. O. Duarte, S. Manich, J. Figueras, "Fault-Secure Parity Prediction Arithmetic Operators", IEEE Design & Test of Computers, vol. 14, pp. 60-71, 1997
