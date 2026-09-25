---
family: an_code
pin: {decode_point: domain_exit}
---
# domain_exit

Coded operands stay coded through every functional unit and are
decoded only where they leave the arithmetic domain: the STAR
processor operates directly on 32-bit 15X operands in 4-bit bytes,
one's-complement addition supplies complementation and end-around
carry, coded multiplication forms (2^a-1)^2XY then divides by 2^a-1
with coded roundoff, and coded division premultiplies the dividend by
2^a-1 so the quotient remains coded. Partial and final results go to
an external modulo-15 checker.

Keeping the code through the domain lets one checksum accumulator,
expecting all ones after the perform-check signal, check every unit
at 100 per cent coverage of single determinate repeated-use faults
over isolated 4-bit channels. The constraints follow from the code:
A must divide 2^n-1, which every n=ka, A=2^a-1 code satisfies, the
arithmetic is one's complement, multiple-precision and floating-point
operations are relatively cumbersome, and the fixed-point range
shrinks to -1/30<X<1/30 under the simple sign/overflow algorithms.
Latency is byte-serial: 1 cycle for a clear-add, 14 to 28 cycles for
a multiply, 44 cycles for a divide. Against per_op decoding it needs
no decoder per unit but coded multiply and divide algorithms; it is
the pick when the whole datapath is built for the code.

The generated checker realizes this variant (`checker.decode_point: domain_exit`) as a comment on where the decode would sit; the checker's coded replica compares per op.

## references

avizienis_1973 -> A. Avizienis, "Arithmetic Algorithms for Error-Coded Operands", IEEE Transactions on Computers, vol. C-22, pp. 567-572, 1973
