---
family: m_out_of_n_checker
pin: {code_class: arbitrary_m_out_of_n}
---
# arbitrary_m_out_of_n

The Marouf-Friedman checker for any m-out-of-n code: the input bits
are partitioned into balanced sets, positive-unate majority functions
classify valid words into a 1-out-of-Z code, and a totally
self-checking translator maps that code to 2-out-of-4 for the final
checker. Separate procedures cover (2m + 2) < n < 4m, n = 2m + 1,
n > 4m and m + 2 < n < 2m; the n > 4m case recurses on the inputs,
and m > n/2 dualizes the checker to the (n-m)-out-of-n code.

The construction saves 46 to 97 percent of the logic and 75 to 97
percent of the gate inputs against Anderson's realization for m = 3
to 6, in abstract gate counts, and needs 172 of the 1820 code words
as a test set at m = 4, n = 16. The recursive n > 4m form costs
4 + 3k gate levels with k = ceil(log2(n/m)) - 1, and a modified
nine-level form flattens it. Only the positive-unate AND-OR
realization keeps coverage of multiple unidirectional faults; an
inverting NAND/NOR form keeps single faults only. A translator
cascade in the textbook form reaches test sets of 9 and 7 words for
2-out-of-6 and 2-out-of-5. It is the pick when n differs from 2m;
k_out_of_2k drops the translator, and one_out_of_n covers m = 1,
which this construction excludes.

The generated checker treats this variant as the k-out-of-2k check over the pair word (n = 2k, m = k), because the compared words are binary.

## references

marouf_friedman_1978 -> M. A. Marouf, A. D. Friedman, "Efficient Design of Self-Checking Checker for any m-Out-of-n Code", IEEE Transactions on Computers, vol. C-27, pp. 482-490, 1978
lala_2001 -> P. K. Lala, "Self-Checking and Fault-Tolerant Digital Design", Morgan Kaufmann, 2001
