---
family: multi_term_fused_dot
pin: {alignment_strategy: pairwise_difference_reuse}
---
# pairwise_difference_reuse

Alignment without a maximum-exponent search: the exponent differences of
every operand pair are computed in parallel (six subtractions for three
operands), their signs identify the largest exponent and the differences
themselves are the shift amounts, so the shifters start as soon as the
pairwise subtractions finish. The partial results of the difference
logic drive the shifter controls directly, and the same differences
supply the sticky-bit resolution and the cancellation detection.

The pairwise form removes the serial dependence of the tree-and-subtract
alternative, where the maximum exponent is found first and each
operand's shift is then computed from it. Under a tight timing
constraint the pairwise design is smaller and faster; under relaxed
timing the maximum-exponent tree becomes the smaller of the two. The
three-term adder built on it, with dual reduction trees, a three-input
LZA before the addition and compound sum/sum+1 rounding, takes about 15
to 20 percent less area and power and 35 percent less latency than a
discrete three-term adder at 45 nm. The number of pairwise subtractors
grows with the square of the operand count, so the strategy fits three
or four operands, and the sorted realignment-line design is the
alternative at eight.

The library realizes this choice as a pin of the generated multi_term_fused_dot module (`chialu/targets/rtl/families/dot.py`); the family card names the construction.

## references

sohn_2014 -> J. Sohn, E. E. Swartzlander, "A Fused Floating-Point Three-Term Adder", IEEE TCAS-I, vol. 61, no. 10, pp. 2842-2850, 2014
tenca_2009 -> A. F. Tenca, "Multi-Operand Floating-Point Addition", ARITH-19, pp. 161-168, 2009
