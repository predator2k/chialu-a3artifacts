# bipartite_rom: proposed changes to the space

* choice input_partition (high_middle_low) with P/N table dimensions — the split of the input into high/middle/low fields and the sizes of the positive and negative tables determine storage growth. [dassarma_1995]
* choice output_representation {borrow_save, direct_booth_recoded} — the reciprocal is held as separate positive/negative parts and may be fused straight into radix-4 or radix-8 Booth digits without carry completion. [dassarma_1995, oberman_1997]
* choice fidelity_target {faithful, optimal} — faithful means less than one ulp, while optimal additionally matches the midpoint reciprocal table, and the two targets need different constructions. [dassarma_1995]
* input_bits range extended to 18 — the general construction uses (j+2)-bits-in tables up to 18 input bits, beyond the current 16. [dassarma_1995]
