# symmetric_bipartite

A symmetric bipartite table seed: the input x is partitioned into
x0, x1, x2 and x3, only the three most significant partitions address
the two symmetric tables, and the omitted low partition x3 is replaced
by its midpoint delta3 inside the modified coefficient formulas. The
two table outputs are added to give an initial approximation of the
reciprocal, square root or reciprocal square root, and the error
bounds carry an extra term for the omitted bits, so the tables can be
sized for faithful rounding of the seed that a multiplicative
iteration then refines.

The input and output widths set the tables: an output fraction of j
bits uses k = ceil(j/3) partition bits, and shrinking the addressed
input by dropping x3 makes the tables smaller at the price of the
additional error that the midpoint replacement introduces. The guard
bits absorb that error; the modified form needs g = 3 when the
omitted partition is non-empty, one more than the original symmetric
bipartite method, and faithful rounding holds when the four error
terms sum to at most 2^-pf, for which two sufficient constraints are
given. The consumer selects the reciprocal or the reciprocal square
root from the same construction, and the same tables also supply
direct square-root approximations.

The family is feed-forward, one table pair and one addition, and is
the seed of choice when memory dominates the seed cost: it needs less
memory than the faithful bipartite reciprocal tables it is compared
against, which in turn produce borrow-save outputs that simplify the
Booth encoding of the following multiplier. Where that redundant
output matters more than table size, or where a polynomial seed of
higher accuracy removes an iteration, the neighbours win.

The seed instantiates the library's generated divider for this family
(`chialu/targets/rtl/families/div.py`: the bipartite tables with the slope table folded on the offset's sign (half the entries), the sum through `sum_adder`). `python3 -m chialu.targets.rtl.families.div --width 32 --family <family> --pins k=v,...` emits it for a rewrite (`--sqrt` for the square root).

## references

schulte_1999 -> Schulte, Stine, "Approximating Elementary Functions with Symmetric Bipartite Tables", IEEE Transactions on Computers, 1999
