# bipartite_rom

A reciprocal table split into two halves whose outputs are combined in
borrow-save form. The normalized input 1 <= x < 2 is partitioned into
high, middle, and low fields; the high and middle fields index a
positive-part table P, the high and low fields index a negative-part
table N, and the reciprocal is P - N held as separate positive and
negative parts. The redundant output is fused with the multiplier that
follows: the low-order guard bits are rounded while the borrow-save
value is recoded directly into radix-4 or radix-8 Booth digits, so no
carry-completion addition is needed. The two tables together are a
fraction of the size of one conventional table at the same fidelity.

The input, output, and guard bit counts set compression against
fidelity. The construction balances the segment spreads inside each
high-field block, rounds P downward and N to nearest, and guarantees a
faithful result, which means less than one ulp from the infinitely
precise reciprocal of the infinitely precise input, for tables with two
more input bits than output bits and at least six output bits. Below
about eight output bits an optimal bipartite table can match the
conventional optimal ROM exactly at about 2x compression; from ten
output bits upward, optimal tables with near-half-width indices become
difficult or impossible to construct, so the two input guard bits
preserve faithfulness rather than exact agreement, and the compression
against the smallest faithful conventional ROM grows from about 4x to
16x as the output width goes from 10 to 16 bits. Over that range about
91.5% of results are round-to-nearest and the maximum error rises from
0.826 to 0.919 ulp.

The family is feed-forward, one lookup deep, and its accuracy contract
is faithful rather than correctly rounded. It wins as the seed for
multiplier-based division, where a wider seed removes dependent
multiply cycles and the consumer is a multiplier that accepts a
redundant, Booth-recoded input at negligible extra logic; it loses that
advantage wherever the output must be assimilated to a nonredundant
value first. Against a conventional ROM the gain is small at four to
nine input bits and large above ten. Adding a further table partition
or folding the table on its symmetry are the space's routes to more
compression.

The seed instantiates the library's generated divider for this family
(`chialu/targets/rtl/families/div.py`: a value table over the two leading index parts and a slope table over the leading and trailing parts, summed through the `sum_adder` family; the error evaluated per finest cell). `python3 -m chialu.targets.rtl.families.div --width 32 --family <family> --pins k=v,...` emits it for a rewrite (`--sqrt` for the square root).

## references

dassarma_1995 -> Das Sarma, Matula, "Faithful Bipartite ROM Reciprocal Tables", 12th IEEE Symposium on Computer Arithmetic, 1995
oberman_1997 -> Oberman, Flynn, "Division Algorithms and Implementations", IEEE Transactions on Computers, 1997
