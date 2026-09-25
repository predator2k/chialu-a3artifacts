# m_out_of_n_checker

Constant-weight code checker: the n lines of an m-out-of-n code word
(exactly m ones, n!/((n-m)!m!) code words) are partitioned into
balanced groups, and two independent subcircuits compute majority
predicates over the groups so that a code word yields 01 or 10 and a
word of lower or higher weight yields 00 or 11. A k-out-of-2k code is
checked directly in two-level or multilevel unate form; for arbitrary
m and n the majority stage first classifies valid words into a
1-out-of-Z code that a totally self-checking translator maps to
2-out-of-4 for a final two-rail pair; the 1-out-of-n case is a network
that accepts exactly one active line.

The code class sets the construction. A k-out-of-2k code needs no
translator and is self-testing with a direct sum-of-products or
product-of-sums form; an arbitrary m-out-of-n code goes through the
partition procedures, which cover (2m + 2) < n < 4m, n = 2m + 1 and
m + 2 < n < 2m separately, recurse on the inputs when n > 4m, and
dualize the checker to the (n-m)-out-of-n code when m > n/2; a
1-out-of-n code expands to any number of lines and is required where
a component-reduced biquinary adder can raise three outputs after a
fault, which an odd-count check would pass. The realization trades
depth, gate count and test set: the two-level form needs 2^k test
words where the cellular threshold array needs 2k, a translator
cascade reaches single-digit test sets for small codes, and a
pass-transistor cell or an inverter-free PLA gives a compact cell at
the cost of a fixed structure. The intermediate code names the
1-out-of-Z word the majority stage emits before translation, and the
deep-case delay style chooses between the recursive n > 4m
construction at 4 + 3k gate levels, with k = ceil(log2(n/m)) - 1, and
a flattened nine-level form. Gate polarity is a coverage decision:
only the positive-unate AND-OR form stays totally self-checking for
multiple unidirectional faults, and a NAND/NOR realization keeps
single-fault detection only.

The family wins over two_rail_tree whenever the checked outputs are
constant-weight rather than complementary pairs, since the majority
networks replace a translation to two-rail form; the balanced
partition saves 46 to 97 percent of the logic against Anderson's
realization for m = 3 to 6, in abstract gate counts, and holds the
test set to 172 of the 1820 code words at m = 4, n = 16. It loses to
two_rail_tree when pairs are already available, which is the
collapse_to_two_rail_tree move. The fault contract is that of
unordered codes: every single error and every unidirectional multiple
error on the checked lines is a non-code word, and the checker itself
is totally self-checking under the same fault class. Execution is
feed-forward.

The generated checker (`chialu/targets/rtl/alu_checker.py`) realizes this family in the comparator slot: the pair word {p, ~q} checked as a k-out-of-2k codeword by the Anderson-Metze threshold checker (a literal two-level form for k <= 5, a cellular AND/OR array otherwise or under multilevel_unate and cellular_threshold_array, 2-out-of-4 translator cells into a two-rail tree under translator_cascade); the weight compare misses a corruption that moves one bit each way, which the alias bound and the single-bit floor of the fault gate account for; code_class one_out_of_n checks every pair as a 1-out-of-2 word through the two-rail tree.

## design choices

### realization

| member | what it selects |
| --- | --- |
| `two_level_and_or` | the threshold functions are written as a literal two-level AND/OR form, which holds for k of at most 5. |
| `cellular_threshold_array` | the threshold functions are a cellular AND/OR array, which is the form that scales past k of 5. |
| `translator_cascade` | pairs of positions are checked as 2-out-of-4 words by translator cells whose two-rail outputs fold in a tree. |

## references

lala_2001 -> P. K. Lala, "Self-Checking and Fault-Tolerant Digital Design", Morgan Kaufmann, 2001
marouf_friedman_1978 -> M. A. Marouf, A. D. Friedman, "Efficient Design of Self-Checking Checker for any m-Out-of-n Code", IEEE Transactions on Computers, vol. C-27, pp. 482-490, 1978
richards_1955 -> Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
