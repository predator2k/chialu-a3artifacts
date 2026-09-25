---
family: carry_skip
pin: {block_sizing: uniform}
---
# uniform

Equal-width blocks along the whole operand: every group has the same
number of ripple cells and one skip gate, so the worst-case carry
ripples one block, skips the rest and ripples one block again. With n
bits per block and k blocks the worst-case delay is 2n + k - 3 time
units, minimized at n near the square root of the operand width;
MacSorley's 50-bit example uses 5-bit groups for 36 logical levels
against 100 for ripple carry, at almost the same logic count.

Uniform sizing is the pick when regularity matters more than the last
delay units: the block is one repeated cell, which is why the textbook
presentation and Lehman and Burla's baseline use it. It loses to
trapezoidal_variable sizing on the same equipment, because the end
blocks are wider than the work they do requires, and to dp_optimized
sizing whenever the ripple and skip delays are not constants. Muller's
radix-2^p formulation is the same structure with p bits per digit
block: a larger block makes the per-block carry step cheaper relative
to the bits it covers but lengthens the ripple inside it, which is the
area/delay trade the block width sets.

## references

lehman_burla1961 -> M. Lehman, N. Burla, "Skip Techniques for High-Speed Carry-Propagation in Binary Arithmetic Units", IRE Transactions on Electronic Computers, vol. EC-10, pp. 691-698, 1961.
macsorley1961 -> O. L. MacSorley, "High-Speed Arithmetic in Binary Computers", Proceedings of the IRE, vol. 49, no. 1, pp. 67-91, 1961
muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
