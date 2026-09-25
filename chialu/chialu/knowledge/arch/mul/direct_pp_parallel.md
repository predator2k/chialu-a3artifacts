# direct_pp_parallel

Parallel multiplication without recoding: each multiplier bit selects 0
or the multiplicand M with one AND gate per partial-product bit, so an
n by n product forms n rows of n dots (16 rows and 256 dots at 16x16),
or pairs of multiplier bits select from {0, M, 2M, 3M}, halve the rows
and need a carry-propagate preaddition for 3M. Signed operands use the
Baugh-Wooley terms, and the rows go to the reduction slot, a Wallace or
Dadda counter tree or a 4:2 compressor tree, whose sum/carry pair
either passes the final CPA or leaves the unit for later assimilation.

group_bits trades selection logic against rows: one bit keeps the
selector to one AND gate per bit, and two bits halve the partial
products at the cost of an N-bit carry-propagate addition on the setup
path through the hard_multiple_adder slot. An analytic model counted in
CSA cell areas and CSA delays charges the one-bit form 1.125n^2 - 1.938n
at log1.5 n - 1.34 and the two-bit form 0.688n^2 + 0.563n - 4 at
1.29 log1.5 n - 1.92, so the two-bit grouping saves about as much area as
radix-16 Booth recoding and costs more delay than radix-8 Booth recoding. signed_scheme decides how
the sign rows are absorbed; the Baugh-Wooley form keeps every
coefficient positive, so the matrix reduces like an unsigned one.
Programmable ALU-type cells driven by multiplier-bit pairs can merge partial-product formation with the first addition level (the 1974 ECL build of that scheme settled in 45 ns at 12x12), a cell-library fusion rather than a netlist choice; and a tree's sum/carry pair may leave a unit redundant, as inside a DSP block or a fused dot product where four such trees feed one assimilation, which the dot unit's fused families do while the multiplier slot assimilates.

Against booth_recoded_parallel the family spends more rows (n rather
than ceil(n/2) at radix 4) but needs no encoder, no negative rows and
no sign-extension constants, so it is the pick for small widths,
unsigned operands and hosts that already carry a reduction tree; the
recoded family wins once the row count dominates the tree depth.
Against carry_save_array it trades the regular O(n) array for a
logarithmic-depth tree with irregular interconnections; the reduction
slot is what separates the two. An 8-bit instance with a Wallace tree
and a 16-bit ripple-carry final adder puts the critical path through
that adder, which makes its behaviour under frequency over-scaling
gradual. The datapath is feed-forward.

## the library's module

The seed instantiates the library's generated multiplier for this family
(`chialu/targets/rtl/families/mul.py`: the AND array with the Baugh-Wooley terms or sign-extended rows for two's complement, or 2-bit groups selecting 0, a, 2a or 3a with 3a through the `hard_multiple_adder` slot); the reduction and the final adder follow the `reduction.*` choices (the counter tree in five geometries over 3:2, 4:2, 5:2 or 7:3 counters, the compressor tree over 4:2, 5:2, 7:3 or stacking 6:3 cells, or the tiled CPA tree of `tile_adder` instances; any adder family for the final add, or the arrival-driven regions of `hybrid_arrival_driven`). `python3 -m chialu.targets.rtl.families.mul
--width 32 --family direct_pp_parallel --signed --sv mul32.sv` emits it for a rewrite.

## design choices

### signed_scheme

| member | what it selects |
| --- | --- |
| `baugh_wooley` | the Baugh-Wooley correction terms handle the signs inside the matrix. |
| `sign_extension` | the rows are sign-extended instead. |

## references

bewick1994 -> G. W. Bewick, "Fast Multiplication: Algorithms and Implementation", PhD dissertation, Stanford University, CSL-TR-94-617, 1994
blankenship1974 -> P. E. Blankenship, "Comments on 'A Two's Complement Parallel Array Multiplication Algorithm'", IEEE Transactions on Computers, 1974
boutros_2018 -> A. Boutros, S. Yazdanshenas, V. Betz, "Embracing Diversity: Enhanced DSP Blocks for Low-Precision Deep Learning on FPGAs", International Conference on Field Programmable Logic and Applications (FPL), 2018
galal_2013 -> S. Galal, O. Shacham, J. S. Brunhaver, J. Pu, A. Vassiliev, M. Horowitz, "FPU Generator for Design Space Exploration", ARITH-21, 2013
sohn_2016 -> J. Sohn, E. E. Swartzlander, "A Fused Floating-Point Four-Term Dot Product Unit", IEEE TCAS-I, vol. 63, no. 3, pp. 370-378, 2016
venkatesan2011 -> R. Venkatesan, A. Agarwal, K. Roy, A. Raghunathan, "MACACO: Modeling and Analysis of Circuits for Approximate Computing", IEEE/ACM International Conference on Computer-Aided Design (ICCAD), pp. 667-673, 2011
wallace1964 -> Wallace, "A Suggestion for a Fast Multiplier", IEEE Transactions on Electronic Computers, 1964
