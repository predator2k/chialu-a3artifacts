---
id: mod_2s_minus_1_fold
tier: word
applies_to: [checker, adder, redundant]
preserves: bit_exact
check: tb
effect: area-, delay-
sources: [seander_bithacks, piestrak_1994, lipetz_schwarz_2011]
---
# Modulo 2^s-1 by digit folding

pattern: a divider or wide subtractor for `v % (2^s - 1)`

rewrite: sum the s-bit digits of v (2^s = 1 mod 2^s-1), fold the carries end-around, canonicalize the two representations of zero: a CSA tree of s-bit digits with end-around carry, which is the residue generator of a mod-2^s-1 checker

when: residue checkers (mod 3/7/15), ones'-complement addition, checksums; the end-around carry adder is the same structure
