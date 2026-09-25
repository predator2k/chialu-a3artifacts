# sig_mul_then_round

Floating-point multiplication as an exact significand product followed
by a short tail: the p-digit significands multiply to a 2p-digit
product, the exponents add and rebias on a parallel path that can be
small and slow, the product of normalized operands needs at most a
one-digit normalization shift, and the result is rounded from the
retained upper bits plus guard, round, and sticky bits from the
discarded lower half. The low
n - 2 product bits influence the result only through their carry into
the retained n + 2 bits, so the final carry-propagate adder need not
resolve them, and the rounder either increments the truncated product
or selects between precomputed sum and sum + 1.

The rounder is the main choice. Incrementing after the carry-propagate
addition is the simplest form and suits software or moderate-speed
hardware, but its two serial carry-propagate additions limit
high-performance use. Compound selection computes sum and sum + 1 in
parallel with the final addition and picks by the rounding bits,
the form the shipping units use at one result per cycle. Among the fast organizations, a
prediction-bit scheme reaches 14 logic levels when post-normalization
precedes round selection, the rounding-table scheme takes 16 and is
the easiest to prove correct, and early injection reaches 12 but
plants a constant in the reduction tree, which the other two avoid.
Sticky generation is the hidden cost: a direct OR over the discarded
half waits for the low product, counting operand trailing zeros runs
in parallel but needs priority encoders, and injecting -1 into the
summation network with a forced carry-in derives sticky from
low-order group propagate/generate signals without computing the low
bits.

The significand multiplier slot ranges from a radix-8 Booth array
with a precomputed 3x multiple over two pipeline cycles, through an
area-constrained Wallace variant recovered by dynamic full adders, to
an iterative carry-save array retiring about 14 bits per cycle whose
final addition and rounding borrow a cycle of the add unit, and a
sign-digit array traversed twice for double precision to trade array
area for throughput. Subnormal products are the rounder's: the engine's X carries the exact
product with a wide exponent, so the leading-zero count and the right
shift before rounding sit in the rounder (product normalization lets
the count overlap the multiply); a trap to software and flush-to-zero
are system and mode properties; binary
format conversion and rounding can double the latency of a unit
tuned for a simpler format. An approximate variant swaps the
significand multiplier for a logarithmic one and drops rounding and
subnormals, buying order-of-magnitude area and power at fp32 for a
bounded relative error of under 25 percent, so the contract becomes
statistical. When an FMA is present the standalone multiply sends its
unrounded sum/carry pair to a rounder the fused path bypasses.

A denormal operand reaches the array without its implied one, and the
correction stays off the critical path. One form separates the partial
products that depend on the implied one, loc1 and loc2, from the
remaining partial products P', so a 53-bit direct multiplication
carries 52 rows for P' plus those two. A counter tree commonly has a few inputs
with delayed arrival times, so the correction terms wait there while
the exponent is examined for all zeros to decide the implied bit, at
one additional 3:2 counter per term, which is small against the counter
tree's area. The zSeries radix-4 Booth multiplier instead subtracts a
leading-zero correction term lzc1 = -Y*x0 from the partial-product
array. Correcting the W1 Booth digit before its partial product is
generated is the third form: W1(y0=0) and W1(y0=1) are computed in
parallel and multiplexed once y0 is known, which adds no
partial-product row and leaves only the multiplicand's implied bit to
correct.

The shipped units divide the tail differently. The SPARC64 multiplier
runs a 60 x 60 array, wider than the significand because the division
and square-root iterations need that width for correctly rounded
IEEE-754 results. It assimilates the redundant product in a group
carry-lookahead adder with carry select, whose carry-in comes from
separate carry-out logic over the low-order 60 bits. Its sticky tree
runs on the redundant sum and carry bits with the propagate and kill
signals of that carry-out logic, in parallel with the assimilation
rather than after it. Rounding there selects among four precomputed
sums, first on the carry-in bit and then on the overflow bit, the round
bit, the sticky bit and the rounding mode, which puts the multiply at 4
cycles in 0.15 um CMOS. The z13 runs a binary quad multiply as several
passes through one shared dataflow: the radix-4 Booth product's 113-bit
significand is assimilated by the compound adder, the shifter block
then applies the corrections for subnormal operands and subnormal
results, and the rounding follows as an injection in a further pass.
Execution is feed-forward.

## the library's module

The seed instantiates the library's generated float module for this family
(`chialu/targets/rtl/families/fp.py`, value-exact against the engine: the library multiplier of the sig_mul family over the stored significands).
The component families (sig_mul, exp_adder) select its sub-structures
from the library.

## references

muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
bewick1994 -> G. W. Bewick, "Fast Multiplication: Algorithms and Implementation", PhD dissertation, Stanford University, CSL-TR-94-617, 1994
santoro_1989 -> M. R. Santoro, G. Bewick, M. A. Horowitz, "Rounding Algorithms for IEEE Multipliers", 9th IEEE Symposium on Computer Arithmetic, 1989
even_2000 -> G. Even and P.-M. Seidel, "A Comparison of Three Rounding Algorithms for IEEE Floating-Point Multiplication", IEEE Transactions on Computers, 2000
schwarz_1999 -> E. M. Schwarz and C. A. Krygowski, "The S/390 G5 Floating-Point Unit", IBM Journal of Research and Development, 1999
dobberpuhl_1992 -> D. W. Dobberpuhl, et al., "A 200-MHz 64-b Dual-Issue CMOS Microprocessor", IEEE Journal of Solid-State Circuits, vol. 27, no. 11, pp. 1555-1567, 1992.
rowen_1988 -> C. Rowen, M. Johnson, P. Ries, "The MIPS R3010 Floating-Point Coprocessor", IEEE Micro, vol. 8, no. 3, pp. 53-62, 1988.
saadat2018 -> H. Saadat, H. Bokhari, S. Parameswaran, "Minimally Biased Multipliers for Approximate Integer and Floating-Point Multiplication", IEEE Transactions on Computer-Aided Design, vol. 37, no. 11, pp. 2623-2635, 2018
schwarz_2003 -> E. M. Schwarz, M. Schmookler, S. D. Trong, "Hardware Implementations of Denormalized Numbers", 16th IEEE Symposium on Computer Arithmetic, 2003
naini_2001 -> A. Naini, A. Dhablania, W. James, D. Das Sarma, "1-GHz HAL SPARC64 Dual Floating Point Unit with RAS Features", ARITH-15, 2001
lichtenau_2016 -> C. Lichtenau, S. Carlough, S. M. Mueller, "Quad Precision Floating Point on the IBM z13", ARITH-23, 2016
