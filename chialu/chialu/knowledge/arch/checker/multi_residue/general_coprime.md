---
family: multi_residue
pin: {moduli_set: general_coprime}
---
# general_coprime

Any set of pairwise relatively prime moduli, with two redundant
residues recomputed at each check and compared against the stored
ones: two nonzero discrepancies address a table that returns the
index of the erroneous nonredundant residue and its modular
correction, one zero discrepancy names the other redundant residue for
replacement, and two zeros mean a consistent word. Correction can be a
discrepancy-addressed table or an explicit computation.

General moduli are the pick when the arithmetic is already a residue
number system with several channels and the checker only adds two
redundant residues; Watson and Hastings work the six-modulus set
(199, 233, 194, 239, 251, 509) with four nonredundant and two
redundant residues. The full correction table has 1722 entries, 861
after complementary-symmetry folding at some added computation time,
and only 1.3 percent of the 127749 possible redundant-residue states
are legitimate. The contract is one residue error per check; with one
redundant modulus R the undetectable fraction is 100 percent / R,
0.398 percent in the example, and correcting two or more residues by
table is impractical because table size grows about as (MR)^l / l!.
The low-cost 2^a - 1 moduli instead tie the checker to
one's-complement arithmetic on one accumulator and locate errors of
the form +/-2^j from a small syndrome set.

The generated checker takes a `moduli` list in the spec; moduli_set is not a pin it reads.

## references

watson_hastings_1966 -> R. W. Watson, C. W. Hastings, "Self-Checked Computation Using Residue Arithmetic", Proceedings of the IEEE, vol. 54, no. 12, pp. 1920-1931, 1966
rao_1970 -> T. R. N. Rao, "Biresidue Error-Correcting Codes for Computer Arithmetic", IEEE Transactions on Computers, vol. C-19, pp. 398-402, 1970
