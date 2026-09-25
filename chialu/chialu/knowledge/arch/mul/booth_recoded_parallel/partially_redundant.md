---
family: booth_recoded_parallel
pin: {hard_multiple_gen: partially_redundant}
---
# partially_redundant

Redundant Booth forms the hard multiple 3M with independent short
adders separated by a carry interval instead of one full-width carry-
propagate adder, so each partial product is a sparse partially
redundant number. A fixed bias K is added to every selectable multiple
and the combined biases are subtracted with a compensation constant,
so complementing the nonblank bits and adding 1 turns K+M into K-M
without filling the redundant gaps with ones.

A 16x16 Redundant Booth 3 with 4-bit adders needs 155 dots against 126
for conventional Booth 3 and a height of 7 against 6, and the bias
compensation adds a net value of zero (bewick1994). The carry interval
should be the longest that does not raise multiply latency and
relatively prime to the 3-bit shift between adjacent rows; intervals
10 to 14 are about equally acceptable, and the fastest redundant Booth
3 cuts about 25% power and 15% area against Booth 2 in the 0.6 um
BiCMOS ECL study, and improved Booth 3 hands the early low-order
hard-multiple bits to the summation-network optimizer. Redundant Booth 4 needs three hard multiples,
larger multiplexers and extra bias logic, and methods above Booth 3 do
not pay through 64 bits. The scheme is the pick when radix-8 rows are
wanted without the cpa_precompute adder on the setup path.

## references

bewick1994 -> G. W. Bewick, "Fast Multiplication: Algorithms and Implementation", PhD dissertation, Stanford University, CSL-TR-94-617, 1994
