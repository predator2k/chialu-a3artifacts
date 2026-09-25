# inverse_residue

Concurrent error detection by a residue check byte stored in inverted
form: the check channel carries m - |N|_m, the modular complement of
the operand's residue (mod 15 in a four-bit byte on 28 data bits in
the STAR computer), so the complete data/check word is congruent to
zero modulo m and one residue computation over the whole coded word
validates it, rather than a comparison of separately generated
results. The main processor computes in two's complement while a
modulo 2^a - 1 check processor tracks the inverse residue; the two
run independently except that a discarded main-processor carry-out
increments the check sum by one.

The inversion is what separates the family from a direct residue
check. A valid word has residue zero, so a check channel stuck at a
plausible constant still yields a nonzero syndrome, and the checker
can sit on the data bus and validate a word while it is transmitted.
The code replaced the AN code in STAR because it is separable and
accommodates two's-complement, multiple-precision, and floating-point
arithmetic, and STAR applied it to numeric operands and instruction
addresses alike. Two's-complement main arithmetic costs one coupling
between the channels, which is the discarded-carry correction; a
single fault that falsely asserts or inhibits that signal leaves a
2^j discrepancy that the check still reports, so the coupling does not
open a hole.

Modulus sets check width against escape. A one-dimensional inverse
residue over b-bit bytes misses a one-byte unidirectional error that
flips an all-zero byte to all ones (or back) with probability 1/2^b,
and raising the modulus buys coverage with a wider check byte.
Applying the inverse residue on both channels makes the code
two-dimensional: a byte residue modulo 2^b - 1 and a line residue
modulo 2^(k+1) - 1 across k data bytes give two syndromes that locate
every single-bit error and correct very nearly all single-line
unidirectional errors. The price is separate carry-forming circuits
for the line prediction, because shared carries cause common-mode
errors, plus ambiguity when rotated syndromes match several lines,
mis-correction for three adjacent stuck lines, and rectangle-corner
quadruple errors that escape both checks. Execution is feed-forward.
The family is chosen when one separable code must protect storage,
transfer, and arithmetic together; reverting to direct residue is the
fallback when a stuck check channel is not a concern.

The generated checker (`chialu/targets/rtl/alu_checker.py`) realizes this family: the residue prediction carried as M - r on the check channel, the coded sum compared with zero through the comparator slot.

## references

avizienis_gilley_1971 -> A. Avizienis, G. C. Gilley, F. P. Mathur, D. A. Rennels, J. A. Rohr, D. K. Rubin, "The STAR (Self-Testing And Repairing) Computer: An Investigation of the Theory and Practice of Fault-Tolerant Computer Design", IEEE Transactions on Computers, vol. C-20, no. 11, 1971
avizienis_1973 -> A. Avizienis, "Arithmetic Algorithms for Error-Coded Operands", IEEE Transactions on Computers, vol. C-22, pp. 567-572, 1973
avizienis_1985 -> A. Avizienis, "Arithmetic Algorithms for Operands Encoded in Two-Dimensional Low-Cost Arithmetic Error Codes", Proc. ARITH-7, pp. 285-292, 1985
