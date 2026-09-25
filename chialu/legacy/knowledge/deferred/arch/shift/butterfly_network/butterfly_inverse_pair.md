---
family: butterfly_network
pin: {network: butterfly_inverse_pair}
---
# butterfly_inverse_pair

A butterfly network followed by an inverse butterfly network, which
together form a Benes network: the butterfly carries every pdep and
the inverse butterfly every pex, and the pair driven directly from
its control registers, as bfly and ibfly, realizes any n-bit
permutation. Each network has lg(n) stages of n/2 two-input switches,
and a 64-bit network takes three 64-bit control registers.

It is the pick when pex and pdep are both required, since a butterfly
cannot implement every pex and an inverse butterfly cannot implement
every pdep, and it is the smallest configuration that also gives
general permutation: with static controls the pex/pdep/bfly/ibfly
unit is 0.76x an ALU's area at 0.96x its cycle time in TSMC 90 nm
standard cells, and the three-stage variable-mask form is about 2.2x
the ALU's area. A single butterfly or inverse butterfly serves a
pdep-only or pex-only unit, and grp needs a second inverse butterfly
and the largest unit. The permutation pays configuration storage for
its control registers beyond what a mask decoder supplies.

## references

hilewitz_2006 -> Y. Hilewitz, R. B. Lee, "Fast Bit Compression and Expansion with Parallel Extract and Parallel Deposit Instructions", Proc. IEEE ASAP, 2006
hilewitz_2008 -> Y. Hilewitz, R. B. Lee, "Fast Bit Gather, Bit Scatter and Bit Permutation Instructions for Commodity Microprocessors", Journal of Signal Processing Systems, 2008
