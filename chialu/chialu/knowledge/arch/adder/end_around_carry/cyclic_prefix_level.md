---
family: end_around_carry
pin: {recirculation: cyclic_prefix_level}
---
# cyclic_prefix_level

The carry-out is re-propagated inside the prefix network rather than
through a second pass: either one extra prefix level, with n added
black nodes, consumes the carry-out as a fast increment of the sum,
or the prefix equations wrap around within every level so that each
carry is a prefix over the lower-order group combined with the
upper-order group and all carries settle in log2 n levels. Both forms
break the carry-in-to-carry-out path that would otherwise form a
combinational loop.

The extra level is the cheapest form, at two unit-gate delays and
about 3n unit gates over the integer prefix adder, but it puts a
fanout of n on the reentering carry; the wrap-at-every-level form
removes that level and that fanout for about 3/2 n log n operators
and keeps a diminished-one modulo 2^n+1 channel as fast as the
fastest integer adders, which matters where that channel dictates the
RNS addition delay. The pick over select_based recirculation is a
single prefix core with no tentative sums; algorithm-generated cyclic
trees push the same idea further by distributing the cyclic carry
across repeated shifted carry chains at the cost of more long wires.

## references

zimmermann1997 -> R. Zimmermann, "Binary Adder Architectures for Cell-Based VLSI and their Synthesis", PhD thesis, Diss. ETH No. 12480, ETH Zurich, 1997.
zimmermann1999 -> R. Zimmermann, "Efficient VLSI Implementation of Modulo (2^n +/- 1) Addition and Multiplication", 14th IEEE Symposium on Computer Arithmetic (ARITH-14), 1999
vergos2002 -> H. T. Vergos, C. Efstathiou, D. Nikolos, "Diminished-One Modulo 2^n + 1 Adder Design", IEEE Transactions on Computers, vol. 51, no. 12, pp. 1389-1399, 2002
efstathiou2004 -> C. Efstathiou, H. T. Vergos, D. Nikolos, "Fast Parallel-Prefix Modulo 2^n + 1 Adders", IEEE Transactions on Computers, 2004
beaumont_smith2001 -> A. Beaumont-Smith, C.-C. Lim, "Parallel Prefix Adder Design", 15th IEEE Symposium on Computer Arithmetic (ARITH-15), pp. 218-225, 2001.
