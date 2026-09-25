---
family: svoboda_tung
pin: {msd_recoding: two_digit_recode}
---
# two_digit_recode

New Svoboda-Tung (NST) keeps the recurrence R^(j+1) = bR^j − q_(j+1)Y
with a redundant signed-digit residual and a nonredundant divisor
prescaled into [1, 1 + δ), and takes the quotient digit as the leading
residual digit after a conditional recode of the two most significant
residual digits r1 r2 into r1a r2a that preserves b·r1a + r2a =
b·r1 + r2. The recode removes the overflow compensation of Tung's
original selection-free scheme, so no divisor multiple is compared
against the residual.

Against msd_recoding none, which is Tung's scheme with a minimally
redundant digit set and a divisor prescaled to 1 + e so that a wrong
trial digit is compensated one step later, the recode trades a
two-digit recoding cell for that compensation and opens the residual
digit set D<b.α> and the threshold β as design points: the radix-4
points MRMR, MROR, MRmr and mr differ in prescaling latency (3, 3, 3
and 2 cycles) and in the residual bits the selection observes (8, 6,
8 and 6). The mr point avoids non-power-of-two divisor multiples and
is reported 1.19x faster than MROR and 1.44x faster than prescaled
regular radix-4 division in an analytical W = 53 model. It is the
pick for a prescaled divider that may return KR rather than R as its
final residual. In the ADIR grammar it is `family: svoboda_tung` with
`pin: {msd_recoding: two_digit_recode}`.

## references

montalvo_1998 -> Montalvo, Parhi, Guyot, "New Svoboda-Tung Division", IEEE Transactions on Computers, 1998
tung_1968 -> Tung, "A Division Algorithm for Signed-Digit Arithmetic", IEEE Transactions on Computers, 1968
