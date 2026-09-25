---
family: multi_residue
pin: {moduli_set: low_cost_2a_minus_1}
---
# low_cost_2a_minus_1

Moduli of the form A = 2^a - 1 and B = 2^b - 1, checked with
one's-complement arithmetic on an n-bit register whose length each
modulus width divides. Unique syndromes for every accumulator error
+/-2^j need n <= lcm(a, b), and n = ab when a and b are coprime and
both moduli divide 2^n - 1; the worked example A = 7, B = 15 covers a
12-bit register with 24 distinct syndromes for the errors +/-2^j.

The low-cost set is the pick when the checkers must stay small and
the protected operations are ADD, COMPLEMENT, SHIFT, LOAD and ROTATE
on a fixed-width accumulator: Rao builds it on the earlier separate
residue checker, whose single A = 3 channel already cost 30 to 40
percent of the checked part, and the residue operations run apart
from and in parallel with the arithmetic unit at practically no loss
of speed. The constraint is the register length, which must be a
common multiple of the modulus widths and no more than lcm(a, b) for
unique syndromes. General coprime moduli remove that coupling and
suit table-driven correction over many residues, at the price of
tables whose size grows about as (MR)^l / l! with the number l of
corrected residues.

The generated checker realizes this variant: the moduli 3, 7 and 31 (`checker.moduli_count`).

## references

rao_1970 -> T. R. N. Rao, "Biresidue Error-Correcting Codes for Computer Arithmetic", IEEE Transactions on Computers, vol. C-19, pp. 398-402, 1970
watson_hastings_1966 -> R. W. Watson, C. W. Hastings, "Self-Checked Computation Using Residue Arithmetic", Proceedings of the IEEE, vol. 54, no. 12, pp. 1920-1931, 1966
