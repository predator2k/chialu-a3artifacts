---
family: carry_skip
pin: {block_sizing: dp_optimized}
---
# dp_optimized

Block and level boundaries chosen by a dynamic program rather than by a
geometric profile: each candidate configuration carries a tuple of
internal, generate, assimilate and skip path delays, configurations
grow by appending a block or a stage, and dominated tuples are pruned,
so the result is minimum delay for any nonnegative delay functions
rather than for constant ripple and skip costs. The
same search extends recursively to multilevel skip structures with no
fixed level count.

dp_optimized sizing is the pick when the delay model is not the
textbook one: size-dependent skip delay, group-propagate setup time
charged to the generate path, or Manchester blocks whose ripple delay
is quadratic in block length. Under Turrini's constant-skip model it
reproduces his optimal sizes, so it gives nothing over
trapezoidal_variable there, and its worst-case time and space are
exponential, though the expected runtime is polynomial. The optima it
finds for two or more levels are highly irregular, which trades layout
regularity for delay; Turrini's tree-building program handles 128 bits
and four or more levels in under a second of VAX CPU time, and his
fabricated 32-bit two-level ECL adder came from it.

## references

chan1992 -> P. K. Chan, M. D. F. Schlag, C. D. Thomborson, V. G. Oklobdzija, "Delay Optimization of Carry-Skip Adders and Block Carry-Lookahead Adders Using Multidimensional Dynamic Programming", IEEE Transactions on Computers, vol. 41, no. 8, pp. 920-930, 1992.
turrini1989 -> S. Turrini, "Optimal Group Distribution in Carry-Skip Adders", 9th IEEE Symposium on Computer Arithmetic (ARITH-9), pp. 96-103, 1989.
chan_schlag1990 -> P. K. Chan, M. D. F. Schlag, "Analysis and Design of CMOS Manchester Adders with Variable Carry-Skip", IEEE Transactions on Computers, vol. 39, no. 8, pp. 983-992, 1990.
zimmermann1997 -> R. Zimmermann, "Binary Adder Architectures for Cell-Based VLSI and their Synthesis", PhD thesis, Diss. ETH No. 12480, ETH Zurich, 1997.
