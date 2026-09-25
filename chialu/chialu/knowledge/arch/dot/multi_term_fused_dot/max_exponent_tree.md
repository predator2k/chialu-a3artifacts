---
family: multi_term_fused_dot
pin: {alignment_strategy: max_exponent_tree}
---
# max_exponent_tree

A comparison tree finds the largest of the N operand exponents, each
operand's shift amount is the difference between that maximum and its
own exponent, and the aligned significands enter one internal addition
of p = 2f + 5 bits followed by one normalization and rounding. The
maximum exponent is the result exponent before normalization, so the
same tree output feeds the exponent path and the sticky resolution of
the operand bits shifted out of the window.

The tree-then-subtract alignment is the serial alternative to reusing
pairwise differences: the maximum must be known before any shifter
starts, which lengthens the critical path, while the tree needs fewer
comparators and subtractors than the pairwise form. Under a relaxed
timing constraint the maximum-exponent tree is the smaller design; under
a tight constraint the pairwise design is smaller and faster. FPADD3
with either alignment produces the perfectly rounded result, defined as
infinite-precision addition followed by one rounding, and at 90 nm in
double precision takes 47,600 area units and 5.6 ns against 51,200 and
5.4 ns for a network of two delay-optimized two-operand adders. The
strategy applies to three or four operands; beyond four the sticky and
cancellation combinations grow too fast for a practical FPADDn.

The library realizes this choice as a pin of the generated multi_term_fused_dot module (`chialu/targets/rtl/families/dot.py`); the family card names the construction.

## references

tenca_2009 -> A. F. Tenca, "Multi-Operand Floating-Point Addition", ARITH-19, pp. 161-168, 2009
