---
family: rns_scaling_comparison
pin: {method: crt_fraction_estimate}
---
# crt_fraction_estimate

Each CRT summand (2/m_i)|w_i x_i|_{m_i} is stored as a binary
fraction and the summands are added with ordinary binary adders,
keeping one integer bit and discarding multiples of 2, so the leftmost
retained bit is the sign relative to M/2 after one table lookup and
one addition. The fraction width t is bounded, t >= ceil(log2(2Mn)) - 1
for even M and ceil(log2(Mn)) for odd M, so accumulated table error
cannot push a value across the sign boundary.

The fractional CRT is the pick for sign detection and for comparison
against a binary fraction of M, where full residue-to-binary
conversion would be wasted: the example moduli 11, 13, 15, 16 with
M = 34320 take 4-bit residues and a 17-bit scaled word, and the
stored-word overhead is roughly ceil(log2 n) bits over the integer
form. Truncating up keeps the accumulated error e < n 2^-t on the safe
side; truncating down or rounding can go negative at X = 0 or, for
even M, X = M/2, but those boundary values are exact. Jullien's
estimate scaling uses the same scaled metric vectors with an error
below (S + 1)/2, at fewer tables than exact ROM mixed-radix division
but less accuracy. A fractional full converter needs a multiplication
by M/2 and is unattractive unless a D/A converter absorbs it; exact
comparison of arbitrary values belongs to the diagonal function.

The library realizes this method as the fixed-point sum of the per-channel fractions, at the width that makes the estimate exact or at a narrower width whose near ties fall to the exact width (`chialu/targets/rtl/families/redundant.py`).

## references

vu_1985 -> Vu, "Efficient Implementations of the Chinese Remainder Theorem for Sign Detection and Residue Decoding", IEEE Transactions on Computers, 1985
jullien_1978 -> Jullien, "Residue Number Scaling and Other Operations Using ROM Arrays", IEEE Transactions on Computers, 1978
dimauro_1993 -> Dimauro, Impedovo, Pirlo, "A New Technique for Fast Number Comparison in the Residue Number System", IEEE Transactions on Computers, 1993
