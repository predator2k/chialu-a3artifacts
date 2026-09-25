---
family: rns_montgomery_crypto
pin: {base_extension: kawamura_approximate}
---
# kawamura_approximate

The Cox-Rower extension: the recursive base extension accumulates
truncated q-bit estimates of xi_i/2^r in the Cox unit, a 7-bit adder
for q = 7, with an offset alpha, while the n Rowers compute the
residue outputs in parallel as modular multiply-accumulates. The
first extension runs with alpha = 0 and returns t or t+B, either of
which keeps the Montgomery congruence, and the second with alpha
above 0 is error-free under the theorem's bounds 4N/(1-Delta) <= B
and 2N/(1-alpha) <= A.

The approximate extension is the pick for parallel hardware with one
Rower per channel: 33 Rowers of 32 bits give an estimated 890 kbit/s
of 1024-bit exponentiation at 100 MHz with 32 bytes of RAM and 970
bytes of ROM per Rower, and the elliptic-curve coprocessor runs 13
reductions per ladder bit on 5- or 6-stage Rower pipelines with 16
registers per channel, reaching 0.32 ms per 160-bit scalar
multiplication on Stratix II. Its costs are the gcd and range
preconditions and a result below 2N rather than N; the mixed-radix
extension is the sibling for a nearest-neighbour ring, and iterated
approximations when the extension may be off by one base product.

The kernel is not an ALU op; the family is an exception (`redundant.EXCEPTIONS`).

## references

kawamura_2000 -> Kawamura, Koike, Sano, Shimbo, "Cox-Rower Architecture for Fast Parallel Montgomery Multiplication", EUROCRYPT (LNCS 1807), 2000
guillermin_2010 -> Guillermin, "A High Speed Coprocessor for Elliptic Curve Scalar Multiplications over F_p", CHES (LNCS 6225), 2010
