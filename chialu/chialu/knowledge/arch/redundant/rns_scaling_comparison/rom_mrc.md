---
family: rns_scaling_comparison
pin: {method: rom_mrc}
---
# rom_mrc

Jullien's exact scaling by a factor K that is the product of S of the
N moduli: the residues are divided iteratively through multiplicative
inverses, a partial mixed-radix conversion runs over the scaled-out
channels, and the result is base-extended back into the removed
moduli. Every step is a two-input ROM lookup, and with enough parallel
tables the whole operation takes at most N lookup cycles.

ROM-driven mixed-radix scaling is the pick when the scale factor can
be chosen as a product of moduli and the result must be exact, with
round-down or round-off selected by adding a fixed half-scale
quantity first: the N = 8, S = 4 realization for an 18-bit multiplier
takes 34 packages of 8K ROM and 7 lookup cycles, and a complete 18 by
18 signed multiplier with 18-bit scaled output fits 42 ROMs and 8
cycles. Its latency is N cycles against N + n1 - S for the estimate
form, which trades exactness for fewer tables, 18 packages at N = 6,
S = 3, with an error below (S + 1)/2. Fixed scaling can lose all
precision when an unscaled result is of order M/K, and estimate-based
base extension alone is unsuitable for high-speed processing. The
redundant-modulus and diagonal-function methods address base
extension and comparison rather than scaling.

The library realizes this method as the mixed-radix digits of both operands compared from the most significant digit down (`chialu/targets/rtl/families/redundant.py`).

## references

jullien_1978 -> Jullien, "Residue Number Scaling and Other Operations Using ROM Arrays", IEEE Transactions on Computers, 1978
shenoy_kumaresan_1989 -> Shenoy, Kumaresan, "Fast Base Extension Using a Redundant Modulus in RNS", IEEE Transactions on Computers, 1989
dimauro_1993 -> Dimauro, Impedovo, Pirlo, "A New Technique for Fast Number Comparison in the Residue Number System", IEEE Transactions on Computers, 1993
