# multipartite

Table-with-addition evaluation that generalizes the bipartite
decomposition to three or more tables read in parallel and summed:
the input word is split into an MSB subword A, which addresses a
table of initial values, and an LSB subword B partitioned into m
subwords B_i, each of which together with a possibly narrower
subword C_i of A addresses a symmetric table of offsets holding a
constant-slope correction. An adder tree sums the initial value and
the m offsets with g guard bits, and the output may stay redundant
when a multiplier consumes it. The order-1
construction on 2p+1 equal k-bit parts yields p+1 tables; the
tripartite case uses five parts and three tables.

The table count trades storage against arithmetic: every added
offset table shrinks the stored bits, but adds adder inputs, XOR and
sign-extension hardware, so the gain diminishes and can reverse, and
a 24-bit sine stops improving beyond five offset tables. Against the
symmetric bipartite and STAM designs the enumerated decomposition,
which selects the subword partition, per-table slope precision and
guard bits jointly, stores up to 50 percent fewer bits. The input
and output widths set where the family applies: it is the pick from
about 8 to 16 bits of precision, practical to 24 bits on a Virtex-II
and economical below 20, and multiplier-based piecewise polynomials
take over above about 20 bits, because the order-1 method replaces a
few multiplications with many additions and does not scale past
single precision. A hierarchical form applies the decomposition
again to the initial-value table, at two levels, and cuts a 16-bit
reciprocal from 14,592 to 11,392 table bits and a 24-bit sine from
74,022 to 60,635 µm² in TSMC 90 nm with a shorter delay.

The accuracy contract is faithful rounding, a total error below one
ulp so the result is one of the two nearest fixed-point values,
verified by exhaustive check after table quantization; the slope
choice equalizes the four endpoint errors of each interval, and
nonmonotonicities at interval boundaries are bounded by that ulp.
The construction assumes a monotonic function with a monotonic
derivative after range reduction, so an infinite derivative, as for
the square root at zero, needs interval splitting or another
method. The guard-bit count is set from the approximation and
rounding error budget.

The seed instantiates the library's generated divider for this family
(`chialu/targets/rtl/families/div.py`: one value table and `tables` - 1 slope tables over the finer index parts, summed through `sum_adder`). `python3 -m chialu.targets.rtl.families.div --width 32 --family <family> --pins k=v,...` emits it for a rewrite (`--sqrt` for the square root).

## references

muller_2016 -> J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
muller_1999 -> J.-M. Muller, "A Few Results on Table-Based Methods", Reliable Computing, vol. 5, no. 3, pp. 279-288, 1999
dedinechin_2005 -> de Dinechin, Tisserand, "Multipartite Table Methods", IEEE Transactions on Computers, 2005
hsiao_2017 -> S.-F. Hsiao, C.-S. Wen, Y.-H. Chen, K.-C. Huang, "Hierarchical Multipartite Function Evaluation", IEEE Transactions on Computers, vol. 66, no. 1, pp. 89-99, 2017
