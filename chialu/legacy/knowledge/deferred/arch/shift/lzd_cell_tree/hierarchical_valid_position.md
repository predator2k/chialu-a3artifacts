---
family: lzd_cell_tree
pin: {formulation: hierarchical_valid_position}
---
# hierarchical_valid_position

Oklobdzija's tree: adjacent input pairs each emit a valid bit V and a
position bit P, and every following level ORs the two valid bits and
uses the left one to select and concatenate the position field, so a
level-i node returns an (i + 1)-bit count for 2^i bits and the whole
count takes log2 N levels from 2-bit groups or log2 N - 1 from 4-bit
groups. Area is O(n) and delay O(log n); the same recursion with a
different two-bit cell gives a leading-one detector.

The valid/position tree is the pick for a regular, low-fan-in layout
in CMOS or for a parameterized generator: pass-transistor multiplexers
implement each level, the 32-bit algorithmic layout in 0.6-micron
CMOS is 35 percent smaller and 29 percent faster than logic synthesis,
and a stage-resized rectangular layout wins by 12 to 15 percent under
a 1.0 pF load but loses 10 to 23 percent without it. Larger groups of
4 or 8 bits cut the tree depth by two or three levels and suit
ECL/BiCMOS, where a 64-bit design reaches 200 ps. The posit regime
decoder uses the same tree over 4-bit chunks with an adder-tree count
and operand inversion so one module counts zeros or ones. The
carry-lookahead formulation instead computes each count bit from
prefix flags over an OR tree, faster and lower in energy in 130 nm,
and a monotonic-string form can win where wide OR/AND is cheap.

## references

oklobdzija_1994 -> V. G. Oklobdzija, "An Algorithmic and Novel Design of a Leading Zero Detector Circuit: Comparison with Logic Synthesis", IEEE Transactions on VLSI Systems, vol. 2, no. 1, pp. 124-128, 1994
muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
schmookler_2001 -> M. S. Schmookler, K. J. Nowka, "Leading Zero Anticipation and Detection — A Comparison of Methods", Proc. ARITH-15, pp. 7-12, 2001
jaiswal_2018 -> M. K. Jaiswal, H. K.-H. So, "Universal Number Posit Arithmetic Generator on FPGA", Design, Automation and Test in Europe (DATE), 2018
dimitrakopoulos_2008 -> G. Dimitrakopoulos et al., "Low-Power Leading-Zero Counting and Anticipation Logic for High-Speed Floating Point Units", IEEE Transactions on VLSI Systems, vol. 16, no. 7, 2008
