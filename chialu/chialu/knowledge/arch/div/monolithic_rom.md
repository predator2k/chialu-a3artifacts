# monolithic_rom

A k-bits-in, m-bits-out reciprocal table: the normalized argument in
[1, 2) is truncated to k fractional bits, which selects one of 2^k
input intervals, and the entry stores the reciprocal of that
interval's midpoint rounded to nearest at m bits. That entry
minimizes the maximum relative error over its interval, and applying
the rule to every interval gives the optimal table. Access is one
ROM or PLA read with no arithmetic. With g output guard bits the
maximum relative error is 2^-(k+1) x (1 + 1/2^(g+1)), so a k-in,
k-out table guarantees k + 0.415 bits and one, two or three guard
bits raise that to k + 0.678, k + 0.830 and k + 0.912.

input_bits is the expensive knob: storage is 2^k x m bits, so each
added address bit more than doubles the table, whereas output_bits
and guard_bits add precision at linear cost, and the guard-bit
precision series saturates toward k + 1. The reciprocal is the
function in every block on file; the same construction serves the reciprocal
square root. The entry rule can be directed rather than nearest,
guaranteeing an approximation above or below the exact reciprocal at
some precision, which iteration schemes that need a one-sided seed
error prefer.

The family is the seed of choice for Newton-Raphson and Goldschmidt
division: the 1964 convergence design decodes 6 leading denominator
bits into an 8-bit first factor to cut later iterations, and the
posit core generator reads a 2^8 x 9 table for widths through 32
bits, with higher precision bought by a larger table or one more
iteration. It loses once the required seed precision pushes k past
the point where the exponential growth is affordable: large
uncompressed tables are described as impractical and mainly useful
as benchmarks, and the bipartite and multipartite families split the
table to recover the precision at a fraction of the bits. The
accuracy contract is the proven minimax bound above; the family is
feed-forward and adds no fault detection of its own.

The seed instantiates the library's generated divider for this family
(`chialu/targets/rtl/families/div.py`: a case ROM (a module of its own) of the rounded midpoint value per input cell, `input_bits` wide with `output_bits` plus `guard_bits` output bits, its maximum relative error evaluated exactly at generation and used to size the iteration). `python3 -m chialu.targets.rtl.families.div --width 32 --family <family> --pins k=v,...` emits it for a rewrite (`--sqrt` for the square root).

## references

dassarma_1994 -> Das Sarma, Matula, "Measuring the Accuracy of ROM Reciprocal Tables", IEEE Transactions on Computers, 1994
oberman_1997 -> Oberman, Flynn, "Division Algorithms and Implementations", IEEE Transactions on Computers, 1997
goldschmidt_1964 -> Goldschmidt, "Applications of Division by Convergence", MS thesis, MIT, 1964
jaiswal_2019 -> M. K. Jaiswal, H. K.-H. So, "PACoGen: A Hardware Posit Arithmetic Core Generator", IEEE Access, 2019
