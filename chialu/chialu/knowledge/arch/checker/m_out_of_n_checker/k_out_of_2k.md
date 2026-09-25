---
family: m_out_of_n_checker
pin: {code_class: k_out_of_2k}
---
# k_out_of_2k

The Anderson-Metze checker: a k-out-of-2k input is split into two
equal k-bit groups A and B, and two independent subcircuits compute
majority predicates over the groups so that code inputs map to (0,1)
or (1,0) and noncode inputs to (0,0) or (1,1). Each predicate is
realized two-level or as a recursively decomposed multilevel
AND-OR/OR-AND network; no translator stage is needed because the two
groups already hold k bits each.

The fault model is one or more lines stuck at 0 or 1, and a
noninverting AND/OR realization is totally self-checking for single
and unidirectional multiple faults because a fault cannot raise an
erroneous 1 and an erroneous 0 at once; NAND/NOR realizations detect
all single faults but not every unidirectional fault. Self-testing
with a direct sum-of-products or product-of-sums form holds only when
n = 2m and both groups hold m bits. Merging alternating levels
reaches a minimum depth of three gate levels at the cost of fan-in,
and the diagnostic test set stays at 2^k code words while the
majority functions remain explicit, rising to C(2k,k) once they are
multiplied out. k_out_of_2k is the pick when the code is balanced;
arbitrary_m_out_of_n adds the translator front end for other
weights, and the two_rail_tree family is simpler whenever
complementary pairs are already available.

The generated checker realizes this variant (`checker.comparator.code_class: k_out_of_2k`) over the pair word {p, ~q}.

## references

anderson_metze_1973 -> D. A. Anderson, G. Metze, "Design of Totally Self-Checking Check Circuits for m-Out-of-n Codes", IEEE Transactions on Computers, vol. C-22, no. 3, pp. 263-269, 1973
lala_2001 -> P. K. Lala, "Self-Checking and Fault-Tolerant Digital Design", Morgan Kaufmann, 2001
