# prefix_lzc

Leading-zero counting expressed as a parallel-prefix computation: each count bit is written as a carry-lookahead relation over the group zero flags, so the counter is built with the same generate/propagate operators, topologies and synthesis tooling as a prefix adder, and its energy and delay trade along the same continuum. The same formulation lets LZA error handling and encoding be folded into one prefix computation.

Against lzd_cell_tree the prefix form gives up the fixed 2-bit-block modularity for a choice of topology: prefix_topology sets the prefix OR network (Kogge-Stone, Sklansky or Brent-Kung), count_form takes the count as a population count of the positions above the leading one (through the counter slot's popcount) or as the lookahead-flag encoding of the leading-one flags. The recursive lookahead of the origin anticipator already had this shape: four-bit group states were combined with doubling and buffering comparable to the logarithmic adder, then ORed and encoded for a partial-decode shifter. The formulation pays where the count sits on the energy budget rather than the critical path, since the leading-zero slot is a measurable, separately optimizable fraction of FP-add energy; where the counter must be retimed or shaped to an existing prefix stage; and where the shifter wants its controls straight from the string rather than through a binary count. It is the encoder slot for both an anticipator and a post-add counter.

Pick prefix_lzc when the counter is synthesized beside a prefix adder and shares its cell library and timing model, or when a low-power adder counts after the add and the energy of the count is on the budget; lzd_cell_tree is the pick for a fixed, verifiable block structure at a known delay, such as the 64-bit detector that beat synthesized logic.

## design choices

### count_form

| member | what it selects |
| --- | --- |
| `popcount_of_complement` | the count is the population count of the positions the prefix OR leaves unmarked, through the counter slot. |
| `lookahead_flags` | the leading-one flags are encoded by one OR tree per count bit. |

### prefix_topology

| member | what it selects |
| --- | --- |
| `kogge_stone` | the prefix OR runs on the minimum-depth unit-fanout graph. |
| `sklansky` | it runs on the minimum-depth doubling-fanout graph. |
| `brent_kung` | it runs on the regular constant-track graph. |

## references

dimitrakopoulos_2008 -> G. Dimitrakopoulos, K. Galanopoulos, C. Mavrokefalidis, D. Nikolos, "Low-Power Leading-Zero Counting and Anticipation Logic for High-Speed Floating Point Units", IEEE Transactions on VLSI Systems, 2008
hokenek_cook_1990 -> E. Hokenek, R. K. Montoye, P. W. Cook, "Second-Generation RISC Floating Point with Multiply-Add Fused", IEEE Journal of Solid-State Circuits, vol. 25, no. 5, pp. 1207-1213, 1990
oklobdzija_1994 -> V. G. Oklobdzija, "An Algorithmic and Novel Design of a Leading Zero Detector Circuit: Comparison with Logic Synthesis", IEEE Transactions on VLSI Systems, 1994
