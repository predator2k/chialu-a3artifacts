---
family: end_around_carry
pin: {topology: ladner_fischer}
---
# ladner_fischer

A Ladner-Fischer prefix carry unit under a carry-save stage and a
modified carry-increment row: a CSA first forms X + Y + 2^n - 1, the
n-bit prefix unit computes the carries, and the increment row accepts
the conditional end-around correction through its carry input, with
one AND gate producing the first correction carry and the remaining
increment operators consuming it.

The topology is the pin of the normal-binary modulo 2^n+1 adder that
keeps one carry-computation unit instead of two serial lookahead
units, at 2 log2 n + 9 unit-gate delays; it loses to the
wrap-at-every-level construction, at 2 log2 n + 6, because the
increment row adds a prefix level and puts fanout on the reentering
carry. It is the pick when a separate correction row is wanted, for
example to share the prefix unit with an ordinary adder.

## references

efstathiou2004 -> C. Efstathiou, H. T. Vergos, D. Nikolos, "Fast Parallel-Prefix Modulo 2^n + 1 Adders", IEEE Transactions on Computers, 2004
