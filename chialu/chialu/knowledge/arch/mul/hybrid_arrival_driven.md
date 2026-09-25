# hybrid_arrival_driven

A final carry-propagate adder segmented by the reduction tree's bit-arrival profile: low-order columns, whose bits leave the tree early, use a slow ripple adder; middle columns a carry-lookahead or conditional-sum block; the late high-order columns a carry-select block that has the whole tree delay to precompute both outcomes. The result beats any uniform CPA on the same tree, because a uniformly fast adder wastes its speed on bits that are already waiting.

region_count and region_adder_mix set the segmentation and the adder kind per segment (ripple, skip, variable-block skip, lookahead or select, the mix's sequence repeated over the regions); arrival_model decides whether the boundaries come from a uniform assumption or from a measured (or TDM-generated) tree profile, which is the case the systematic three-region ripple/CLA/select construction was built for. Because the tree's placement itself shifts the profile (wire lengths, asymmetric counter inputs, unequal Booth arrival), the adder is designed after the tree, and joint optimization of both carries provable optimality results; optimizing either alone leaves delay on the table. Production 54x54 multipliers already combined carry-lookahead and carry-select structures in the final adder, and a multiple-level conditional-sum final adder over a TDM tree cut total delay by about 8%.

Choose it over uniform whenever the tree is arrival-skewed and the adder is on the critical path; uniform stays the pick when the CPA is shared with another datapath, when the profile is flat (array multipliers, pipelined trees with a register before the adder), or when a single synthesized prefix adder is simpler to verify.

## design choices

### arrival_model

| member | what it selects |
| --- | --- |
| `uniform` | every column is assumed to arrive at the same time. |
| `measured_tree_profile` | the arrival profile is measured from the reduction tree's own column depths. |

### boundary_search

| member | what it selects |
| --- | --- |
| `arrival_profile_intersection` | the region boundaries sit where the arrival profile crosses evenly spaced thresholds. |
| `delay_bound_boundary_enumeration` | the boundaries are enumerated against a delay bound instead. |

### region_adder_mix

| member | what it selects |
| --- | --- |
| `ripple_then_select` | a ripple region then a carry-select one. |
| `ripple_cla_select` | ripple, carry-lookahead and carry-select regions in that order. |
| `uniform_cla` | carry-lookahead throughout. |
| `ripple_skip` | a ripple region then a carry-skip one. |
| `ripple_skip_select` | ripple, carry-skip and carry-select regions. |
| `vba_select_cla_select_vba` | variable-block carry-skip regions at both ends around carry-select and carry-lookahead regions. |

## references

oklobdzija1995 -> V. G. Oklobdzija, D. Villeger, "Improving Multiplier Design by Using Improved Column Compression Tree and Optimized Final Adder in CMOS Technology", IEEE Transactions on Very Large Scale Integration (VLSI) Systems, vol. 3, 1995
stelling1996 -> P. F. Stelling, V. G. Oklobdzija, "Design Strategies for Optimal Hybrid Final Adders in a Parallel Multiplier", Journal of VLSI Signal Processing, vol. 14, no. 3, pp. 321-331, 1996
stelling1998 -> P. F. Stelling, C. U. Martel, V. G. Oklobdzija, R. Ravi, "Optimal Circuits for Parallel Multipliers", IEEE Transactions on Computers, vol. 47, no. 3, 1998
mori1991 -> J. Mori, M. Nagamatsu, M. Hirano, S. Tanaka, M. Noda, Y. Toyoshima, K. Hashimoto, H. Hayashida, K. Maeguchi, "A 10 ns 54x54-b Parallel Structured Full Array Multiplier with 0.5-um CMOS Technology", IEEE Journal of Solid-State Circuits, vol. 26, 1991
yehjen2000 -> W.-C. Yeh, C.-W. Jen, "High-Speed Booth Encoded Parallel Multiplier Design", IEEE Transactions on Computers, vol. 49, no. 7, pp. 692-701, 2000
