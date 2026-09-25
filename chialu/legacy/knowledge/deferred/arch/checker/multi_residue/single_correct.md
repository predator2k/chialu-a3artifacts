---
family: multi_residue
pin: {code_distance: single_correct}
---
# single_correct

Two residue checkers on relatively prime moduli A and B run in
parallel with the accumulator and hold |X|A and |X|B; the syndrome
pair (|X-Y|A, |X-Z|B) then locates the error: both components nonzero
means an accumulator error e = +/-2^j whose value is read from the
syndrome table and subtracted from the output, one zero component
points at the checker on the other modulus, and a valid word gives
(0, 0). Detection becomes correction with a decoder in place of a bare
compare.

Single correction is the pick when a located error must be repaired
rather than reported, and it costs one more residue channel plus the
syndrome decoder: Rao estimates the whole processor, checkers and
corrector at no more than duplication, against triplication with
voting at three times or more. The contract is one erroneous component
at a time with e of the form +/-2^j; an error that vanishes modulo
both A and B escapes, a stuck-at fault needs diagnosis rather than a
single restore, and a located checker error is left uncorrected with
further accumulator correction inhibited until maintenance. With
general coprime moduli the correction is a table addressed by two
discrepancies, 1722 entries for a six-modulus example and 861 after
complementary-symmetry folding; at most one residue is corrected per
check and multiple residue errors can masquerade as a valid word.

The generated checker detects; code_distance is not a pin it reads, the syndrome that would locate the error is the pair of disagreeing moduli.

## references

rao_1970 -> T. R. N. Rao, "Biresidue Error-Correcting Codes for Computer Arithmetic", IEEE Transactions on Computers, vol. C-19, pp. 398-402, 1970
watson_hastings_1966 -> R. W. Watson, C. W. Hastings, "Self-Checked Computation Using Residue Arithmetic", Proceedings of the IEEE, vol. 54, no. 12, pp. 1920-1931, 1966
