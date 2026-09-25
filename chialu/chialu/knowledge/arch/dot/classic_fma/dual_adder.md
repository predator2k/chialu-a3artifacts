---
family: classic_fma
pin: {negation_handling: dual_adder}
---
# dual_adder

The sign of the result is not resolved before the addition: two
fraction adders compute A − B and B − A in parallel on the merged
product and aligned addend, and the positive one is selected, so
neither an end-around carry nor a post-add complement lies on the
carry path. The z990 dataflow forms A × C, aligns and
complements only the addend B while the product's sum and carry
develop, merges B with a final carry-save adder, and feeds two 116-bit
adders from a 176-bit fraction dataflow.

Against end_around_carry, the dual adder removes the carry
recirculation and the conditional complement from the critical path
at the price of a second wide adder, which the z990 accepts inside a
five-stage fused binary/hexadecimal pipeline; it is the alternative
the handbook names as two parallel adders followed by sign selection.
Aligning only B avoids shifting or complementing the product's sum
and carry signals, and the aligner keeps two positions beyond the
product LSB for a rare subtraction-and-rounding case with denormal
inputs. It is the pick when adder delay dominates and area is
available; end_around_carry stays cheaper where one adder plus an
incrementer meets the cycle target, and complement_recode where a
two's-complement single-path formulation is used. In the ADIR grammar
it is `family: classic_fma` with `pin: {negation_handling: dual_adder}`.

The library realizes this choice as a pin of the generated classic_fma module (`chialu/targets/rtl/families/dot.py`); the family card names the construction.

## references

schwarz_2005 -> E. M. Schwarz, M. Schmookler, S. D. Trong, "FPU Implementations with Denormalized Numbers", IEEE Transactions on Computers, 2005
muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
