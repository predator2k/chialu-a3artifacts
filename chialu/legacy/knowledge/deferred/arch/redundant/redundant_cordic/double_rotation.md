---
family: redundant_cordic
pin: {scale_factor_fix: double_rotation}
---
# double_rotation

The constant-scale method that pairs subrotations: X, Y and Z are
held in redundant binary digits {-1, 0, 1}, and each iteration
implements a negative rotation, a non-rotation or a positive rotation
as two rotation-extensions selected from three digit pairs, so
exactly two extensions occur for every input angle and the scale
factor K1 is constant and folded into X0. The direction is selected
from the three most significant digits of the previous Z.

It is the pick when the iteration count must stay at n and no
runtime scale computation or result correction is acceptable: the
result satisfies |X - cos| < 2^-n and |Y - sin| < 2^-n before
rounding, with a combinational depth proportional to n against n^2
for ripple-carry CORDIC at the same gate order. The price is two
microrotations per iteration and more complex iteration equations,
which is why correcting iterations are preferred when extra rotations
every m steps cost less than doubling every step, and branching when
area for a second module is cheaper than the paired extensions. In
the later half of the iterations the third operand can be dropped
about half the time.

The iterations run over cycles here; the family is an exception (`redundant.EXCEPTIONS`).

## references

takagi_1991 -> N. Takagi, T. Asada, S. Yajima, "Redundant CORDIC Methods with a Constant Scale Factor for Sine and Cosine Computation", IEEE Transactions on Computers, vol. 40, no. 9, pp. 989-995, 1991
meher_2009 -> P. K. Meher, J. Valls, T.-B. Juang, K. Sridharan, K. Maharatna, "50 Years of CORDIC: Algorithms, Architectures, and Applications", IEEE Transactions on Circuits and Systems I, vol. 56, no. 9, pp. 1893-1907, 2009
