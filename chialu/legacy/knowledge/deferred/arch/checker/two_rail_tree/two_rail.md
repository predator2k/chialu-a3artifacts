---
family: two_rail_tree
pin: {input_code: two_rail}
---
# two_rail

The two-rail checker: every input is a complementary bit pair, and a
module produces a complementary output pair if and only if each of its
input pairs is complementary, so an output of 00 or 11 flags either a
non-code input or a fault inside the checker. A multilevel realization
interconnects x-pair modules as a tree over m input pairs, with
[(m-1)/(x-1)] modules and [log_x m] levels, and the tree is totally
self-checking for all single and unidirectional multiple faults.

The tree beats an arbitrary-width two-level AND-OR checker once the
pair count is large, and each x-pair module is exhaustively tested by
its 2^x code words; the static-CMOS cell additionally covers stuck-at
lines, bridging, breaks and stuck-on/stuck-open transistors. Two-rail
is the pick when the checked signals already arrive as complementary
pairs: a residue checker compares a predicted residue with the
complemented output residue, a carry-checking adder reuses the
checker's outputs as complementary carry-parity signals, and a
fault-secure Booth multiplier checks duplicated decoder outputs with
trees of two-variable cells, provided every cell sees all four code
words during normal operation. A 2-pair cell costs eight transistors
in 0.5 um CMOS, but checkers above four input pairs carry too much
overhead for a carry-select adder. The m_out_of_n sibling needs a
code-disjoint translator front end instead.

The generated checker realizes this variant (`checker.comparator.family: two_rail_tree`): the compared words arrive as the pairs (p_i, ~q_i).

## references

lala_2001 -> P. K. Lala, "Self-Checking and Fault-Tolerant Digital Design", Morgan Kaufmann, 2001
nicolaidis_2003 -> M. Nicolaidis, "Carry Checking/Parity Prediction Adders and ALUs", IEEE Transactions on VLSI Systems, vol. 11, no. 1, pp. 121-128, 2003
nicolaidis_duarte_1999 -> M. Nicolaidis, R. O. Duarte, "Fault-Secure Parity Prediction Booth Multipliers", IEEE Design & Test of Computers, vol. 16, no. 3, pp. 90-101, 1999
vasudevan_2007 -> D. P. Vasudevan, P. K. Lala, J. P. Parkerson, "Self-Checking Carry-Select Adder Design Based on Two-Rail Encoding", IEEE Transactions on Circuits and Systems I, vol. 54, pp. 2696-2705, 2007
