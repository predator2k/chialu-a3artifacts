---
family: restoring_nonrestoring
pin: {style: restoring}
---
# restoring

Shift-and-subtract with a trial subtraction at every quotient
position: the divisor is subtracted from the shifted partial
remainder, a nonnegative result is kept with quotient bit 1, and a
negative result is undone by adding the divisor back before the next
shift, so the register always holds the true partial remainder. Tocher
counts n trial subtractions plus an average of n/2 restoring
additions, about 3/2 n addition times against n for nonrestoring.

Restoring is the pick where simplicity and a valid remainder at every
step matter more than cycle count: the backtracking is simple in
radix 2, and recomputation makes it undesirable at higher radices. The
S/390 G5 uses a nonpipelined restoring radix-2 recurrence only for
extended operands, 135 execution cycles, while short and long operands
use Goldschmidt. Kim's integer baseline unrolls k restoring steps per
cycle, each with an N-bit carry-propagate adder on the critical path:
at XLEN=64 in 28 nm, k=1 costs 2.44 kum2 and 0.18 ns per step and k=8
costs 8.79 kum2 and 1.10 ns. Against nonperforming it spends the
restore addition that a compare-and-select avoids, and under lock-step
scheduling true restoring needs twice the iterative clocks; against
nonrestoring it keeps one more register. In the ADIR grammar it is
`family: restoring_nonrestoring` with `pin: {style: restoring}`.

## references

tocher_1958 -> Tocher, "Techniques of Multiplication and Division for Automatic Binary Computers", Quarterly Journal of Mechanics and Applied Mathematics, 1958
muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
richards_1955 -> Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
schwarz_1999 -> E. M. Schwarz and C. A. Krygowski, "The S/390 G5 Floating-Point Unit", IBM Journal of Research and Development, 1999
kim_2025 -> Kim, Parry, Harris, Turek, Maiuolo, Thompson, Stine, "Shared Recurrence Floating-Point Divide/Sqrt and Integer Divide/Remainder With Early Termination", IEEE Transactions on Computers, 2025
