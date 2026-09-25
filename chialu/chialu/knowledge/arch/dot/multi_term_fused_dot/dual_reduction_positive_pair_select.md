---
family: multi_term_fused_dot
pin: {sign_handling: dual_reduction_positive_pair_select}
---
# dual_reduction_positive_pair_select

Two 3:2 reduction trees run in parallel on the aligned significands, one
for each sign assumption of the subtracted operands, so both the sum and
its negation exist in carry-save form before the addition; a significand
comparison decides which pair is positive and selects it, and the
selected pair proceeds to the leading-zero anticipator and the final
adder. No two's-complement inversion follows the addition, so the post-
add complement stage and its carry propagation leave the critical path.

The dual reduction is the sign-handling structure of the fused three-
term adder and of the four-term dot product: the duplicated tree costs
one extra 3:2 (or 4:2) reduction, which is small against the shifters
and the adder, and it buys the removal of the complement step that a
single-tree design needs when the result is negative. Together with
pairwise alignment, three-input leading-zero anticipation before the
addition and compound sum/sum+1 rounding, the fp32 and fp64 designs at
45 nm take about 15 to 20 percent less area and power and 35 percent
less latency than a discrete three-term adder built from delay-optimized
floating-point adders. The post-add complement is the smaller structure
where latency is not the objective, and FPADD3 complements operands
relative to one anchor operand before the addition.

The library realizes this choice as a pin of the generated multi_term_fused_dot module (`chialu/targets/rtl/families/dot.py`); the family card names the construction.

## references

sohn_2014 -> J. Sohn, E. E. Swartzlander, "A Fused Floating-Point Three-Term Adder", IEEE TCAS-I, vol. 61, no. 10, pp. 2842-2850, 2014
