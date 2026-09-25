# compressor_4_2_tree

Partial-product reduction as a binary tree of 4:2 modules: each cell takes four equal-weight bits plus a lateral carry-in and emits a sum and two carries, with the lateral carry-out independent of the carry-in, so four rows collapse to two per level without horizontal propagation and n rows need log2(n/2) levels of xor-bounded depth. Four levels reduce the 27 radix-4 Booth rows of a 54x54 multiplier in about 12 XOR delays, and the repeating cell makes the tree as layout-regular as an array.

compressor_kind trades cell complexity against level count: 4:2 is two chained full adders whose delay beats two 3:2 levels, 5:2 packs dense columns, and 7:3 and stacking_6_3 remove more bits per cell with counters built by symmetric bit stacking rather than xor chains. The circuit style is where the reported speed lives: a pass-transistor multiplexer cell cuts the critical path from four gate stages to three (18% at 0.25 um), N-channel pass-transistor cells gave 1.2 ns per level at 0.5 um, and XOR-XNOR/mux decompositions with full-swing feedback run down to 0.6 V; CPL and DPL need about twice the interconnect, so wiring capacitance limits them in large trees. Regular seven-row subblocks with recurring wire shifters cut design time to a quarter of a hand-built Wallace tree and raised layout density by 70%. Registers between levels are a later version's pipelined tree; an iterative multiplier keeps a small pipelined 4:2 partial tree with a 4:2 carry-save accumulator, and production FMAs mix 4:2 and 3:2 rows across cycle boundaries and route late rows (denormal corrections) past the first level.

Pick this tree over csa_reduction_tree when regularity, pipelining and a fixed cell library matter more than the last counter: a Wallace or Dadda counter tree is irregular and TDM wire ordering beats any fixed geometry on delay, while the 4:2 tree hands the cpa slot a more uniform arrival profile.

## design choices

### compressor_kind

| member | what it selects |
| --- | --- |
| `4_2` | 4:2 compressors. |
| `5_2` | 5:2 compressors. |
| `7_3` | 7:3 compressors. |
| `stacking_6_3` | a 6:3 bit-stacking cell, which sorts the column's ones before counting them. |

## references

goto1992 -> G. Goto, T. Sato, M. Nakajima, T. Sukemura, "A 54x54-b Regularly Structured Tree Multiplier", IEEE Journal of Solid-State Circuits, vol. 27, 1992
ohkubo1995 -> N. Ohkubo, M. Suzuki, T. Shinbo, T. Yamanaka, A. Shimizu, K. Sasaki, Y. Nakagome, "A 4.4-ns CMOS 54x54-b Multiplier Using Pass-Transistor Multiplexer", IEEE Journal of Solid-State Circuits, vol. 30, 1995
mori1991 -> J. Mori, M. Nagamatsu, M. Hirano, S. Tanaka, M. Noda, Y. Toyoshima, K. Hashimoto, H. Hayashida, K. Maeguchi, "A 10 ns 54x54-b Parallel Structured Full Array Multiplier with 0.5-um CMOS Technology", IEEE Journal of Solid-State Circuits, vol. 26, 1991
chang2004 -> C.-H. Chang, J. Gu, M. Zhang, "Ultra Low-Voltage Low-Power CMOS 4-2 and 5-2 Compressors for Fast Arithmetic Circuits", IEEE Transactions on Circuits and Systems I, vol. 51, 2004
weinberger1981 -> A. Weinberger, "4:2 Carry-Save Adder Module", IBM Technical Disclosure Bulletin, vol. 23, no. 8, pp. 3811-3814, 1981
santoro1989 -> M. R. Santoro, M. A. Horowitz, "SPIM: A Pipelined 64x64-bit Iterative Multiplier", IEEE Journal of Solid-State Circuits, vol. 24, no. 2, pp. 487-493, 1989
fritz2017 -> C. Fritz, A. T. Fam, "Fast Binary Counters Based on Symmetric Stacking", IEEE Transactions on Very Large Scale Integration (VLSI) Systems, vol. 25, 2017
