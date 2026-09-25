---
id: end_around_carry_adder
tier: word
applies_to: [adder, checker, redundant]
preserves: bit_exact
check: tb
effect: area-
sources: [richards_1955, vergos_2001]
---
# Ones'-complement / modular add by end-around carry

pattern: a modular reduction after a plain addition

rewrite: feed the carry-out back into the carry-in (a prefix adder with the carry recirculated as a cyclic prefix), and canonicalize the representation of zero

when: mod 2^n-1 adders, ones'-complement arithmetic, residue channels
