---
id: popcount_csa_tree
tier: word
applies_to: [shift, checker, adder]
preserves: bit_exact
check: tb
effect: area-, delay-
sources: [seander_bithacks, richards_1955]
---
# Popcount as a compressor tree

pattern: a chain of adders or an adder tree over the bits

rewrite: the SWAR form `v = v - ((v>>1) & 0x5555...); v = (v & 0x3333...) + ((v>>2) & 0x3333...); ...` is, in hardware, a tree of 3:2 / 7:3 counters: pair the bits into full adders, then add the 2-bit sums, doubling widths each level

when: popcount ops, parity/weight checkers, Berger/m-out-of-n checkers, majority vote
