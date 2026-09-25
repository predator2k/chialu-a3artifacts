---
id: carry_save_late_resolution
tier: structural
applies_to: [mul, dot, adder]
preserves: bit_exact
check: tb
effect: area-, delay-
sources: [bewick1994, muller_2018]
---
# Resolve carries once

pattern: several carry-propagate adders in sequence (accumulate, then add, then round)

rewrite: keep intermediate results in carry-save (sum, carry) form and resolve with one CPA at the end; feed the rounding increment into the same CPA

when: multiply-accumulate, multi-operand addition, FMA; a CPA in the middle of a chain is the first thing to remove
