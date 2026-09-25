# butterfly_network

Arbitrary bit gather, scatter and permutation through lg(n)-stage
switch networks of n/2 two-input switches per stage: a butterfly
network routes right-aligned data bits, in order, to mask-selected
positions (parallel deposit, pdep), and an inverse butterfly network
compresses the mask-selected bits, in order, and right-aligns them
(parallel extract, pex); unselected inputs or outputs are masked
outside the network, and every pdep and every pex routes without a
path conflict. A butterfly followed by an inverse butterfly is a Benes
network that realizes any n-bit permutation, and a second inverse
butterfly adds grp. Switch controls come from application registers
or a shared mask decoder.

network fixes which datapath is built: the unit's rotate runs on the
inverse butterfly or on the butterfly alone (the same stages in the
reverse order, which composes the inverse permutation), while a
butterfly alone implements every pdep and an inverse butterfly alone
every pex, neither implements the other, so pex and pdep together need
both networks, ops the unit does not carry;
the pair driven directly from three 64-bit control registers per
network gives general permutation as the bfly and ibfly instructions,
and grp needs a third network. mask_binding trades latency against
generality: controls preloaded in application registers run in one
cycle, a loop-invariant mask is decoded once by setb or setib into
those registers and reused at one cycle per use, and a dynamic mask
is decoded for every instruction at three cycles. control_generation
decides where the mask becomes switch controls: software prepares
them, or one hardware decoder built from a parallel-prefix population
counter (the prefix_popcount slot) and LROTC rotators (the
lrotc_rotator slot) translates the mask, and the decoder's rotated and
complemented controls absorb the rotations otherwise needed between
butterfly stages.

The family wins where selected bits must move independently: bit
compression and expansion, gather and scatter, and permutations that
barrel_mux_tree and funnel, which apply one uniform displacement, and
masked_merged, which rotates and merges one contiguous field, cannot
form. Static pex and pdep dominate the studied kernels and use the
smallest unit: in TSMC 90 nm standard cells the static
pex/pdep/bfly/ibfly unit is 0.76x an ALU's area at 0.96x its cycle
time, dynamic mask support raises the area to about 2.25x the ALU at
three cycles, and the grp-capable unit costs more still; kernels
speed up by 1.13x to 10.04x over the base Alpha ISA. The family loses
to masked_merged when only one contiguous field moves, since the
rotate-and-mask form is the specialization the network strictly
generalizes, and a general permutation pays configuration storage for
its control registers. Execution is feed-forward; the two- and
three-cycle forms are pipeline stages of the same datapath.

## design choices

### network

| member | what it selects |
| --- | --- |
| `inverse_butterfly` | the stages run small distance first. |
| `butterfly` | the same stages in the opposite order, which reads the complemented amount. |

## references

hilewitz_2006 -> Y. Hilewitz, R. B. Lee, "Fast Bit Compression and Expansion with Parallel Extract and Parallel Deposit Instructions", Proc. IEEE ASAP, 2006
hilewitz_2008 -> Y. Hilewitz, R. B. Lee, "Fast Bit Gather, Bit Scatter and Bit Permutation Instructions for Commodity Microprocessors", Journal of Signal Processing Systems, 2008
