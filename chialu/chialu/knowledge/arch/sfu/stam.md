# stam

Symmetric table addition: the input x is split into m subwords and the function is expanded to first order around the interval midpoint selected by the first two subwords, so f(x) is approximated by a table of initial values addressed by the leading subwords plus m - 1 offset tables TO_i, each addressed by the slope subword and one further subword, and the result is the sum of the table outputs. STAM is the bipartite method with the offset word decomposed into m subwords and its linear offset distributed over m symmetric tables, replacing one large offset table by several smaller ones at the cost of m - 1 further additions. Feed-forward: parallel table reads, then one multi-operand add.

tables trades memory against adders and against accumulated rounding. Each further offset table is smaller, but each carries its own rounding error, so the smaller TO_i tables need greater output precision than one large offset table would, and the multi-operand adder grows by one input per table. The first-order Taylor error fixes the split: the first two subwords must together represent about half of the input word for an error of about 2^-n. For a 24-bit sine the four-subword form takes 92 Kbytes and the five-subword form 74.5 Kbytes, and STAM and the multipartite method need similar memory at that precision.

The family's limit is the shared slope address: every TO_i is addressed by the same slope subword C, which is more precision than the lower-weight tables can use, so accuracy is wasted there. The multipartite generalization relaxes that constraint by giving each table its own slope address, and it is the neighbour to move to once the offset tables dominate. Against a single bipartite offset table, STAM wins on memory whenever the offset word is wide enough to split; against a polynomial evaluator it keeps the datapath to table reads and one adder tree, with no multiplier.

The seed instantiates the library's generated module for this family (`chialu/targets/rtl/families/sfu.py`: the symmetric table addition method with `tables` offset tables over the lower chunks, each symmetric about its chunk midpoint). `python3 -m chialu.targets.rtl.families.sfu --function <fn> --format <format> --family stam --pins k=v,...` emits the module with its modeled error for a rewrite.

## references

dedinechin_2005 -> de Dinechin, Tisserand, "Multipartite Table Methods", IEEE Transactions on Computers, 2005
muller_1999 -> J.-M. Muller, "A Few Results on Table-Based Methods", Reliable Computing, vol. 5, no. 3, pp. 279-288, 1999
