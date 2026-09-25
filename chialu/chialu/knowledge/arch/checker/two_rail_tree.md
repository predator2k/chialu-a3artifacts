# two_rail_tree

The totally self-checking comparator: a two-rail checker cell takes
complementary input pairs and produces a complementary output pair if
and only if every input pair is complementary, so an output of 00 or 11
flags a non-code input or a fault inside the checker. A tree of
x-pair modules checks m pairs with about (m-1)/(x-1) modules in log_x m
levels, which beats a flat two-level AND-OR form for many pairs. The
tree is totally self-checking for all single and
unidirectional multiple faults, and the static-CMOS cell (eight
transistors per 2-pair cell) also covers stuck-at, bridging, break
and stuck-on/stuck-open transistor faults. Its structure corresponds
one-to-one with a parity tree.

Tree arity trades levels against testability: an x-pair module needs
all 2^x code words applied during normal operation to stay
self-testing, so a wider module removes levels but demands more input
combinations at every cell, and above four pairs the checker cost
becomes unacceptable in the carry-select application. The input code
sets the front end. Two-rail inputs feed the tree directly; a
k-out-of-2k code is checked by two independent subcircuits computing
majority predicates over two equal input groups, in sum-of-products,
product-of-sums or merged alternating-level form, where merging saves
gates and levels at the cost of fan-in and a multiplied-out two-level
form needs all C(2k,k) code words as tests instead of 2^k. An arbitrary
m-out-of-n code first passes through a code-disjoint translator to
k-out-of-2k; NAND/NOR realizations miss some unidirectional faults,
and 1-out-of-3 and 1-out-of-7 checkers remain unsolved.

The embedded form exploits the parity-tree correspondence: the checker
outputs of a carry-checked adder are the complementary carry-parity
signals, so the separate parity generator disappears, and in a
parity-predicted Booth multiplier one checker output supplies the
parity of the duplicated decoder signals while both outputs flag
discrepancies. Embedding brings a self-testing obligation: every cell
must see all four valid combinations in normal operation, so
consecutive decoder signals that cannot take every combination are
split into odd-position and even-position checker sections. Residue
coding alone does not make a Booth multiplier fault-secure; the
decoders must be duplicated and checked, and that overhead falls from
about 65% at 8x8 to about 12% at 64x64 in 1.0-micron CMOS.

The family is the comparator behind residue, Berger and carry-checked
datapaths whenever the compared signals are already in a two-rail or
unidirectional code; where a checker only needs equality of two plain
words, a voter, or a metastability detector, its self-checking
guarantee is not the property being bought.

The generated checker (`chialu/targets/rtl/alu_checker.py`) realizes this family in the comparator slot (`checker.comparator.family`): the pairs (p_i, ~q_i) of every predicted and computed word, and of the duplicated outputs and their copies, through a tree of two-rail cells with tree_arity pairs per node, check_err = the root pair is not alternating; fail_safe_lockout and the state-element realization need a state element the combinational checker lacks, and the input codes other than two_rail a translator it does not build.

## references

lala_2001 -> P. K. Lala, "Self-Checking and Fault-Tolerant Digital Design", Morgan Kaufmann, 2001
anderson_metze_1973 -> D. A. Anderson, G. Metze, "Design of Totally Self-Checking Check Circuits for m-Out-of-n Codes", IEEE Transactions on Computers, vol. C-22, no. 3, pp. 263-269, 1973
nicolaidis_2003 -> M. Nicolaidis, "Carry Checking/Parity Prediction Adders and ALUs", IEEE Transactions on VLSI Systems, vol. 11, no. 1, pp. 121-128, 2003
nicolaidis_duarte_1999 -> M. Nicolaidis, R. O. Duarte, "Fault-Secure Parity Prediction Booth Multipliers", IEEE Design & Test of Computers, vol. 16, no. 3, pp. 90-101, 1999
vasudevan_2007 -> D. P. Vasudevan, P. K. Lala, J. P. Parkerson, "Self-Checking Carry-Select Adder Design Based on Two-Rail Encoding", IEEE Transactions on Circuits and Systems I, vol. 54, pp. 2696-2705, 2007
