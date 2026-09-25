---
family: redundant_cordic
pin: {scale_factor_fix: correcting_iterations}
---
# correcting_iterations

The constant-scale method with a fixed correcting schedule: one
rotation-extension is performed every step and an additional
correcting extension every m-th step, for an arbitrary integer m, so
every input angle receives the same number of extensions and the
scale factor K2 is constant and folded into X0. X, Y and Z use
redundant binary digits, the direction is selected from leading
digits of the remaining angle, and m+2 digits are inspected for the
extra rotation.

It is the pick when the per-step datapath must stay a single
extension and the extra rotations are cheap: n+1 iterations give
|X - cos| < 2^-n and |Y - sin| < 2^-n, at depth proportional to n. The
period m is the tunable: a larger m reduces the number of extra
rotations but widens the digit window inspected for direction
selection. Against double rotation it trades two extensions per step
for one plus a periodic correction and a wider window; against
branching it saves the second module. The technique adapts to
hyperbolic sine and cosine with a slight modification.

The iterations run over cycles here; the family is an exception (`redundant.EXCEPTIONS`).

## references

takagi_1991 -> N. Takagi, T. Asada, S. Yajima, "Redundant CORDIC Methods with a Constant Scale Factor for Sine and Cosine Computation", IEEE Transactions on Computers, vol. 40, no. 9, pp. 989-995, 1991
meher_2009 -> P. K. Meher, J. Valls, T.-B. Juang, K. Sridharan, K. Maharatna, "50 Years of CORDIC: Algorithms, Architectures, and Applications", IEEE Transactions on Circuits and Systems I, vol. 56, no. 9, pp. 1893-1907, 2009
