---
id: exponent_difference_once
tier: structural
applies_to: [fp]
preserves: bit_exact
check: tb
effect: area-, delay-
sources: [muller_2018]
---
# Compute the exponent difference once

pattern: two subtractions `ea - eb` and `eb - ea` plus a comparator for the swap

rewrite: one subtraction; its sign selects the swap and its magnitude (conditionally complemented) is the shift amount

when: FP add/sub alignment; the two-path adder's near/far decision uses the same difference
