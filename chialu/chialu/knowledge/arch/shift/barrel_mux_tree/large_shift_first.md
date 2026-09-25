---
family: barrel_mux_tree
pin: {stage_order: large_shift_first}
---
# large_shift_first

The mux stages are ordered by decreasing displacement: the first level
moves the word by the coarsest multiples and the last by 0 to r-1
positions. The ILLIAC IV barrel switch selects 0/16/32/48, then
0/4/8/12, then 0/1/2/3 in three gate-matrix levels; the RS/6000
alignment shifter follows a binary preshift with coarse 16-position
shifting and a final four-position shift while collecting sticky bits,
and its 32-bit rotator makes coarse rotations of 0 to 28 by four before
shifts of 0 to 4.

The coarse-first order suits partial decoding, where separate control
groups drive the coarse and fine multiplexor stages and wiring falls
below the fully decoded and fully encoded alternatives; the 32-bit
rotator runs a 2 ns data path under a 6 ns four-stage control path,
and the 160-bit shifter completes in 6 ns after the amount is known
in 1 um CMOS (montoye_1990). In a wide alignment shifter fewer than
64 active data bits let the first stage be a four-way multiplexor
despite its broad range, and the sticky bit is formed by ORing the
control signals. The ILLIAC IV arrangement minimizes board types and
intralevel wiring at the cost of interlevel wiring (davis_1969), and
the compared logarithmic shifters take the same order
(pillmeier_2002). It is the pick for alignment and normalization
shifters with sticky collection; small_shift_first wins when a
preshift must fold into the first stage.

## references

montoye_1990 -> R. K. Montoye, E. Hokenek, S. L. Runyon, "Design of the IBM RISC System/6000 Floating-Point Execution Unit", IBM Journal of Research and Development, 1990
davis_1969 -> R. L. Davis, "The ILLIAC IV Processing Element", IEEE Transactions on Computers, vol. C-18, no. 9, pp. 800-816, 1969
pillmeier_2002 -> M. R. Pillmeier, M. J. Schulte, E. G. Walters III, "Design Alternatives for Barrel Shifters", Proc. SPIE 4791, Advanced Signal Processing Algorithms, Architectures, and Implementations XII, 2002
