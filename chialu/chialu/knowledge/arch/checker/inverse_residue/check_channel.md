---
family: inverse_residue
pin: {inverse_on: check_channel}
---
# check_channel

The one-dimensional inverse residue code: the check channel carries m -
|N|_m, the modular complement of the operand's residue, so the complete
data/check word is congruent to zero modulo m and the checker computes
one residue over the whole coded word rather than comparing separately
generated results. In STAR the check byte is 15 - |b|_15 on 28 data
bits, and the main processor computes in two's complement while a modulo
2^a - 1 check processor tracks the inverse residue.

The check-channel form is the pick when one separable code must protect
storage, transfer and arithmetic together at the cost of one check byte
per word: a valid word has residue zero, so a check channel stuck at a
plausible constant still produces a nonzero syndrome, and the checker
can sit on the data bus and validate a word during transmission.
Two's-complement main arithmetic couples the channels through one
signal, the discarded carry-out that increments the check sum, and a
single fault that falsely asserts or inhibits that signal leaves a 2^j
discrepancy the check still reports. The code misses a one-byte
unidirectional error that flips an all-zero byte to all ones with
probability 1/2^b, which is the gap the both-channels sibling closes
with a second, line-wise residue.

The generated checker realizes this variant: the check channel carries M - r.

## references

avizienis_gilley_1971 -> A. Avizienis, G. C. Gilley, F. P. Mathur, D. A. Rennels, J. A. Rohr, D. K. Rubin, "The STAR (Self-Testing And Repairing) Computer: An Investigation of the Theory and Practice of Fault-Tolerant Computer Design", IEEE Transactions on Computers, vol. C-20, no. 11, 1971
avizienis_1973 -> A. Avizienis, "Arithmetic Algorithms for Error-Coded Operands", IEEE Transactions on Computers, vol. C-22, pp. 567-572, 1973
avizienis_1985 -> A. Avizienis, "Arithmetic Algorithms for Operands Encoded in Two-Dimensional Low-Cost Arithmetic Error Codes", Proc. ARITH-7, pp. 285-292, 1985
