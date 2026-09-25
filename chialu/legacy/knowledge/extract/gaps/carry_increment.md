# carry_increment: proposed changes to the space

* `intergroup_carry` value for a fast carry chain (CCC/CR network) — the FPGA CAI propagates block carries through the device's fast-carry-chain network rather than a rippled operator chain or a lookahead tree [pasca_2011#s06]
* `increment_levels` range extended past 2 — CIA-3L and log2 n-level carry-increment structures are studied and help above 64 bits [zimmermann1997#s05]
* choice `speculative_carry_generation: {duplicate_add, comparison_and_zero_carry_add}` — CAI replaces the duplicated one-carry sum with a comparison Xk >= not(Yk) against the zero-carry sum, halving stored speculative-sum registers [pasca_2011#s06]
* parameter `max_black_nodes_per_bit_position` — bounded-node prefix structures constrain the black nodes per bit column and recover size-optimal graphs for difficult timing profiles [zimmermann1997#s07]
