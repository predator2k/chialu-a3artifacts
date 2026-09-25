---
family: inverse_residue
pin: {inverse_on: both_channels}
---
# both_channels

The two-dimensional inverse residue code: the inverse byte residue
modulo 2^b - 1 of the operand is stored in a check byte, and a second
inverse residue modulo 2^(k+1) - 1, formed across the bit lines of the k
data bytes, is stored as a check line, so a byte syndrome and a line
syndrome are computed for every word. The two syndromes together locate
a single-bit error and test a hypothesised stuck-on-one or stuck-on-zero
line against the predicted error count.

Both channels are the pick when correction, and not only detection, is
required from a low-cost arithmetic code: every single-bit error is
correctable from its unique byte/line indication, all bidirectional
errors confined to one line and all double errors on any two bits are
detected, and very nearly all single-line unidirectional errors are
corrected, in the example with b = 4, seven data bytes and moduli 15 and
255 under byte-serial arithmetic. The price is a second check field,
separate independent carry-forming circuits for the line residue
prediction because shared carries cause common-mode errors, and residual
holes: rotated syndromes can match several lines, three adjacent stuck
lines can reproduce a single-line syndrome and mis-correct, and
rectangle-corner quadruple errors escape both checks.

The generated checker carries the inverse on the check channel alone; inverse_on is not a pin it reads.

## references

avizienis_1985 -> A. Avizienis, "Arithmetic Algorithms for Operands Encoded in Two-Dimensional Low-Cost Arithmetic Error Codes", Proc. ARITH-7, pp. 285-292, 1985
