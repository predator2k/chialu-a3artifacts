---
family: self_timed_variable_latency
pin: {mechanism: result_cache}
---
# result_cache

A quotient or reciprocal cache probed when a division issues: a hit
supplies the stored value and halts the divider, and a miss lets the
divider run and fills the entry with the completed value. A quotient
cache keys on both operands and holds about 160 bits per
double-precision entry; a reciprocal cache keys on the divisor alone,
holds about 108 bits per entry, and still needs the final multiply by
the dividend.

It is the pick where the operand stream repeats divisors or operand
pairs and the base divider is slow enough that a hit is worth the
lookup, which is what a reciprocal cache exploits at the smaller
entry. cached_value and cache_associativity size the array: a
reciprocal entry is narrower and hits on any dividend, a quotient entry
skips the final multiply, and direct-mapped is the cheaper lookup
against the fully associative one. Unlike the self-timed ring,
speculation and early termination, the mechanism changes nothing in
the recurrence and sits in front of it, so a hit saves the whole
divide and a miss costs the base divider plus the fill.

## references

oberman_1997 -> Oberman, Flynn, "Division Algorithms and Implementations", IEEE Transactions on Computers, 1997
