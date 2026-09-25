---
id: mod_2s_plus_1_diminished_one
tier: word
applies_to: [checker, adder, redundant]
preserves: bit_exact
check: tb
effect: area-
sources: [vergos_2001, kalampoukas2000]
---
# Modulo 2^s+1 in diminished-one form

pattern: a subtractor-based reduction mod 2^s+1

rewrite: represent x as x-1, add with the inverted end-around carry (the `diminished-one` adder), handle the zero case separately

when: mod 2^n+1 channels in RNS and Fermat transforms; the checker moduli 2^s+1
