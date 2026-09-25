# multi_residue

Error correction by two residue channels: a value X travels as the
triple (X, |X|_A, |X|_B) for relatively prime moduli A and B, and two
residue checkers run in parallel with the processor, maintaining the
residues of the accumulator through ADD, COMPLEMENT, SHIFT, LOAD, and
ROTATE. The syndrome pair (|X - Y|_A, |X - Z|_B) says whether the error
sits in the accumulator, in checker A, or in checker B, and each
accumulator error of the form plus or minus 2^j maps to a distinct
syndrome pair, so a decoder subtracts the located error from the
output. Low-cost moduli 2^a - 1 and 2^b - 1 give unique syndromes for
word lengths up to lcm(a, b), which is ab for coprime a and b.

The moduli set trades checker simplicity against reach. Low-cost
moduli with one's-complement arithmetic and k dividing n make the
residue checkers small, and the example pair A = 7, B = 15 covers a
12-bit register with 24 distinct syndromes. General coprime moduli, as
in a residue number system carrying two redundant residues, locate the
faulty residue through a discrepancy-addressed correction table, and
folding the table by complementary symmetry halves its entries at
increased computation time.

Code distance trades area against what is done with a mismatch. A
second residue channel promotes detection to single-error location and
correction at a total redundancy estimated as no greater than
duplicating the processor, against 30 to 40 percent for a single
mod-3 checker in the 1968 antecedent and three times or more for
triplication with voting. More moduli do not buy multiple-error
correction in practice, because the correction table grows about as
(MR)^l / l! for l simultaneous residue errors.

The contract assumes one erroneous component at a time and the
single-bit error form; an error with both residues zero is undetected,
a multiple-residue error can masquerade as a valid word or a single
residue error, the undetectable fraction is 100 percent over R for one
redundant modulus R, and the checking process itself is trusted. A
located checker error is retained and further accumulator correction
is inhibited until maintenance, and a stuck-at accumulator fault needs
diagnosis or masking rather than one restored result. The channels run
concurrently with the arithmetic unit at practically no loss of speed,
so the family wins where correction rather than detection is required
on code-preserving operations, and loses to a single residue channel
where detection suffices and to duplication where the operation mix
does not preserve the code.

The generated checker (`chialu/targets/rtl/alu_checker.py`) realizes this family: the residue check under two or three low-cost moduli (3, 7, 31), one verdict per modulus.

## references

rao_1970 -> T. R. N. Rao, "Biresidue Error-Correcting Codes for Computer Arithmetic", IEEE Transactions on Computers, vol. C-19, pp. 398-402, 1970
watson_hastings_1966 -> R. W. Watson, C. W. Hastings, "Self-Checked Computation Using Residue Arithmetic", Proceedings of the IEEE, vol. 54, no. 12, pp. 1920-1931, 1966
