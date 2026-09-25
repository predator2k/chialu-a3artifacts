---
family: carry_lookahead
pin: {intergroup_carry: ripple}
---
# ripple

Lookahead within each group only: 4-bit lookahead-carry cells compute
their internal carries in parallel, and the carry between adjacent
cells ripples, which is the linear arrangement of groups in the ETH
taxonomy. The 32-bit concurrent-error-detection adder builds each
16-bit half from four such cells and ripples the carry across the
boundary between the halves as well.

Rippled group carries are the pick when each lookahead cell must stay
independent of the others: the duplicated-half checking scheme works
only when lookahead never overlaps the boundary between the halves,
so the carry between them must ripple even though lookahead is free
inside each half. The price is a delay that grows with the number of
groups, so the variant loses to full lookahead between groups as soon
as the word is wide enough for a second level, and to a carry-select
stage when precomputed upper sums are affordable.

## references

johnson_1988 -> B. W. Johnson, J. H. Aylor, H. H. Hana, "Efficient Use of Time and Hardware Redundancy for Concurrent Error Detection in a 32-Bit VLSI Adder", IEEE Journal of Solid-State Circuits, vol. 23, no. 1, pp. 208-215, 1988
zimmermann1997 -> R. Zimmermann, "Binary Adder Architectures for Cell-Based VLSI and their Synthesis", PhD thesis, Diss. ETH No. 12480, ETH Zurich, 1997.
