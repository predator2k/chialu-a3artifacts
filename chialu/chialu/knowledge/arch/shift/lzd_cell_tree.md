# lzd_cell_tree

Leading-zero count as a tree of cells: the input is cut into 2-bit or 4-bit groups, each emitting a valid bit V (not all zero) and a position field P; every level above ORs the two valid bits and uses the left group's valid bit to select and concatenate the position field, so a level-i node returns an (i + 1)-bit count for 2^i bits, with log2 N levels from pairs or log2 N - 1 from nibbles. The carry-lookahead formulation instead builds a binary OR tree of progressively reduced strings and computes each weighted count bit with an independent single-output lookahead tree over those strings. Area is O(n) and delay O(log n). Feed-forward; the count drives the normalize shifter.

block_primitive trades tree depth against cell fan-in. Nibble or byte groups cut the hierarchy by a factor of two or three and suit ECL or BiCMOS, which tolerates the higher fan-in and fan-out; pair cells keep fan-in and fan-out low and regular, and an algorithmic pair-cell design beat logic synthesis by 12% to 56% in speed and 14.5% to 35% in layout area in 0.6-µm CMOS. A 63-bit nibble-cell detector on a CPA output is built coarse to fine in three levels, sixteen 4-bit circuits, then four 16-bit circuits, then one 64-bit circuit, and only that time-critical instance is drawn by hand while the same unit's other detectors come from synthesis. A detector on the critical path is not shared with prenormalization of denormalized source operands, because the 2:1 mux that sharing needs costs timing, so a second detector serves them. A stage-resized rectangular layout drives a 1.0-pF load faster than the regular one but loses unloaded because of its input capacitance. output_form decides whether the tree emits a binary count or one-hot shift controls that drive the normalizer stages directly and skip the binary-count round trip, and valid_flag_propagation carries the all-zero indication up the tree rather than reading it from a flat OR per node, which a zero-result detect and a saturating shift need. The carry-lookahead formulation, which limits fanout to 2 and reaches 6.6 FO4 for 64 bits in 130-nm static CMOS with 10% to 49% less energy than earlier counters at equal delay, is the prefix_lzc family's lookahead_flags form. The prefix-OR monotonic-string form, which encodes the single transition of a zeros-then-ones string, wins where wide OR and AND are fast, and on an FPGA the fast-carry logic hides that wide OR inside the shifter for inputs up to about 30 bits, which is what fuse_count_with_normalize_shifter exploits.

The contract is exact: a detector works on the completed result, so unlike the anticipator that convert_lzd_to_lza produces it has no one-position error to correct. The all-zero flag falls out of the OR tree and the count is don't-care for an all-zero input. The same cell structure serves leading-one detection with a different two-bit cell, which subnormal normalization and posit negative regimes need, and a posit decoder runs one counter for both polarities by inverting the operand and combines 4-bit chunk counts through a conditional adder tree.

## design choices

### block_primitive

| member | what it selects |
| --- | --- |
| `pair_cell` | the leaves take two bits each. |
| `nibble_cell` | the leaves take four bits each, which halves the tree's depth. |

### output_form

| member | what it selects |
| --- | --- |
| `binary_count` | the root's position is the count. |
| `one_hot_shift_controls` | a one-hot leading-one vector, which a one-hot shifter takes directly, encoded to the count. |

## references

muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
oklobdzija_1994 -> V. G. Oklobdzija, "An Algorithmic and Novel Design of a Leading Zero Detector Circuit: Comparison with Logic Synthesis", IEEE Transactions on VLSI Systems, vol. 2, no. 1, pp. 124-128, 1994
schmookler_2001 -> M. S. Schmookler, K. J. Nowka, "Leading Zero Anticipation and Detection — A Comparison of Methods", Proc. ARITH-15, pp. 7-12, 2001
dimitrakopoulos_2008 -> G. Dimitrakopoulos et al., "Low-Power Leading-Zero Counting and Anticipation Logic for High-Speed Floating Point Units", IEEE Transactions on VLSI Systems, vol. 16, no. 7, 2008
podobas_2018 -> A. Podobas, S. Matsuoka, "Hardware Implementation of POSITs and Their Application in FPGAs", IEEE International Parallel and Distributed Processing Symposium Workshops (IPDPSW), 2018
jaiswal_2018 -> M. K. Jaiswal, H. K.-H. So, "Universal Number Posit Arithmetic Generator on FPGA", Design, Automation and Test in Europe (DATE), 2018
jessani_1996 -> R. M. Jessani, C. H. Olson, "The Floating-Point Unit of the PowerPC 603e Microprocessor", IBM Journal of Research and Development, vol. 40, no. 5, 1996
