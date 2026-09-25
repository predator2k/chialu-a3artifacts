---
family: srt_high_radix
pin: {digit_redundancy: intermediate}
---
# intermediate

The quotient digit set lies between the minimal and maximal bounds,
from {-(1+r/2), ..., +(1+r/2)} through {-(r-2), ..., +(r-2)}, inside
the general requirement ceil(r/2) <= a < r on the largest digit. A
larger digit set reduces the residual and divisor bits the selection
must examine but requires more divisor multiples, and the intermediate
sets balance the two costs; Burgess and Williams find them the most
practicable at the higher radices.

Intermediate redundancy is the pick above radix 4, where the maximal
set's multiples become awkward and the minimal set's table becomes
large: the selection examines about 3 log2 r digits through about
6 log2 r inputs, and larger digit sets generally reduce the fractional
remainder and divisor bits f and b. Oberman and Flynn carry it with
the minimal and maximal sets as the redundancy axis of the
higher-radix designs, where radix 16 retires four bits per iteration
in 14 cycles for n = 53 against 27 at radix 4 and 18 at radix 8. More
divisor bits are preferable to more remainder bits because the divisor
is constant and off the iteration critical path, and assimilating the
redundant remainder before the table halves the ROM inputs at higher
radices. In the ADIR grammar it is `family: srt_high_radix` with
`pin: {digit_redundancy: intermediate}`.

## references

burgess_1995 -> Burgess, Williams, "Choices of Operand Truncation in the SRT Division Algorithm", IEEE Transactions on Computers, 1995
oberman_1997 -> Oberman, Flynn, "Division Algorithms and Implementations", IEEE Transactions on Computers, 1997
muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
