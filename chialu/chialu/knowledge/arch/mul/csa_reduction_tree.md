# csa_reduction_tree

Column compression of the partial-product matrix by (3,2) and larger counters in O(log n) levels until two rows remain for the cpa slot; hardware grows as the square of the word length while time grows logarithmically. geometry fixes the schedule: Wallace reduces every column as early as possible, Dadda as late as possible toward target heights 2,3,4,6,9,... (fewest counters, wider final adder), reduced_area reduces with full adders alone until the last stage, balanced_delay combines the earliest-arriving bits of a column first, and tdm_arrival_driven does the same under the counter's own input delays (the latest bit on the fast input) and beats any fixed geometry; the overturned-stairs tree of Mou and Jutand is a layout-regular wiring of the same counters.

counter_kind trades bits removed per cell against wiring: a (7,3) counter uses ten connections to remove four bits where a (3,2) uses five to remove one, and it leaves a free input for an aligned addend or a late denormal-correction row; long loaded Wallace wires dominate delay in CMOS, so fewer, wider counter stages win. The interconnection between levels is worth as much as the counter: routing the early outputs of one level to the slow inputs of the next and its late outputs to the next carry-in makes two consecutive levels cost 1.5 CSA delays rather than 2, and once the counters are wired that way a (7,3) tree is no faster than the balanced (3,2) tree and the balancing beats a 4:2 compressor tree. The branching order of the regular-layout trees (a fourth-order balanced-delay tree grows as O(n^1/2) and pays off only at small widths; overturned-stairs trees match Wallace speed with a simple interconnect) is a layout organization rather than a netlist choice, and at quad-precision widths, where wires are critical, relative placement driven by coordinates carried in the instance names changes the ranking and puts the overturned-stairs tree ahead, and the TDM objective of an undominated delay profile is a tree-and-adder co-design method: the library keeps the mini-max schedule, and the final adder's hybrid regions take the profile the tree hands over. Latches between levels are a later version's pipelined tree.

The counter tree is the default when the last counter and the arrival profile are worth optimizing, when free inputs must absorb correction rows, or when precision lanes are carved by resetting off-diagonal products; compressor_4_2_tree is the pick for a regular, pipelinable cell layout, and tiled_cpa_reduction_tree when short carry chains are as fast as counters. Every geometry reduces exactly; truncated and approximate trees live in the approximate families.

## design choices

### counter_kind

| member | what it selects |
| --- | --- |
| `3_2` | full adders, which the geometry below then schedules. |
| `4_2` | 4:2 counters per column. |
| `5_2` | 5:2 counters per column. |
| `7_3` | 7:3 counters per column. |

### geometry

| member | what it selects |
| --- | --- |
| `dadda` | the Dadda schedule: the minimum number of counters that still meets the height targets. |
| `wallace` | the Wallace schedule: every column reduced as far as it goes at each level. |
| `reduced_area` | the Wallace schedule without half adders, which trades a level for fewer cells. |
| `balanced_delay` | the columns' bits ordered by arrival time before they are reduced. |
| `tdm_arrival_driven` | the three-dimensional method's arrival-driven schedule over the same ordering. |

## references

wallace1964 -> Wallace, "A Suggestion for a Fast Multiplier", IEEE Transactions on Electronic Computers, 1964
dadda1965 -> L. Dadda, "Some Schemes for Parallel Multipliers", Alta Frequenza, vol. 34, pp. 349-356, 1965
mou1992 -> Z.-J. Mou, F. Jutand, "'Overturned-Stairs' Adder Trees and Multiplier Design", IEEE Transactions on Computers, vol. 41, no. 8, pp. 940-948, 1992
bickerstaff1995 -> K. C. Bickerstaff, M. J. Schulte, E. E. Swartzlander, "Parallel Reduced Area Multipliers", Journal of VLSI Signal Processing, vol. 9, no. 3, pp. 181-191, 1995
oklobdzija1996 -> V. G. Oklobdzija, D. Villeger, S. S. Liu, "A Method for Speed Optimized Partial Product Reduction and Generation of Fast Parallel Multipliers Using an Algorithmic Approach", IEEE Transactions on Computers, vol. 45, no. 3, pp. 294-306, 1996
zuras1986 -> D. Zuras, W. H. McAllister, "Balanced Delay Trees and Combinatorial Division in VLSI", IEEE Journal of Solid-State Circuits, vol. 21, 1986
hokenek_cook_1990 -> E. Hokenek, R. K. Montoye, P. W. Cook, "Second-Generation RISC Floating Point with Multiply-Add Fused", IEEE Journal of Solid-State Circuits, vol. 25, no. 5, pp. 1207-1213, 1990
yehjen2000 -> W.-C. Yeh, C.-W. Jen, "High-Speed Booth Encoded Parallel Multiplier Design", IEEE Transactions on Computers, vol. 49, no. 7, pp. 692-701, 2000
galal_2013 -> S. Galal, O. Shacham, J. S. Brunhaver, J. Pu, A. Vassiliev, M. Horowitz, "FPU Generator for Design Space Exploration", ARITH-21, 2013
