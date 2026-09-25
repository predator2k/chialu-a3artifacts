---
id: constant_multiply_csd
tier: word
applies_to: [mul, sfu, dsp]
preserves: bit_exact
check: tb
effect: area-, delay-
sources: [bewick1994, muller_2016]
---
# Constant multiply as canonical-signed-digit shift-add

pattern: a general multiplier with one constant operand

rewrite: recode the constant in canonical signed-digit form (no two adjacent non-zero digits) and implement `x * c` as a shift-add/sub tree with at most (W+1)/2 terms; share common subexpressions across several constants

when: polynomial coefficients in SFUs, filter taps, scale factors (CORDIC gain), residue generators with constant weights
