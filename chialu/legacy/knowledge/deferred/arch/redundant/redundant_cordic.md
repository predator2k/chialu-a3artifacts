# redundant_cordic

CORDIC whose micro-rotation additions run in carry-save or
signed-digit form, so no carry propagates inside an iteration and the
rotation direction is read from a few most significant digits of the
residual angle. The estimate cannot always decide the sign, so the
direction digit set becomes {-1, 0, 1}, and a zero rotation breaks
the constant scale factor; the family is defined by the repair: double
rotation performs two rotation-extensions per iteration, correcting
iterations add an extra rotation every m steps, forced-sigma designs
forbid the zero digit and replicate angle elements so a wrong
direction is counterbalanced later, and branching runs two modules
on both directions in parallel.

The scale-factor fix trades iterations against digits inspected and
area. Double rotation keeps K constant with two microrotations per
iteration and more complex iteration equations, and needs n
iterations for a 2^-n result; correcting iterations perform one
extension per step plus one every m steps over n+1 iterations, where
a larger m means fewer extra rotations but m+2 inspected digits;
branching keeps the conventional iteration count but doubles the
datapath, since two modules suffice for any number of branchings and
a 3-digit window decides when to branch; forced sigma replicates
about every second angle-sequence element when 3 or 4 leading digits
are inspected. Allowing the zero digit without a fix makes the factor
angle-dependent, and the angle CORDIC of Ercegovac and Lang then
computes K on-line by a square recurrence and square root and divides
the results.

The internal representation is carry-save or borrow-save; the
signed-digit form reads the sign from the first non-zero leading
digit and reduces a 3-digit window to a value in [-7, 7]. All
reported designs are radix 2. A combinational unfolding has depth
proportional to n against n^2 with ripple adders, at the same
n^2 gate count.

The family is fixed-iteration and wins in unfolded or pipelined
high-throughput rotation, where the estimated speedup over the
carry-propagate recurrence is 4 to 6 and triangularization runs in
3n+3 cycles for about 4.5x over conventional CORDIC; an 18-stage
carry-save rotate-mode chip reaches 30 MHz on 60 mm2 in 1.5 um CMOS.
It loses to conventional CORDIC when area dominates, since every fix
costs extensions, digits or a second module, and to the plain
recurrence at small n where a ripple adder is fast enough.

The family's defining structure iterates rotations over cycles (the SFU's cordic families realize the unrolled rotations), so the library has no combinational module for it; a core that declares it stays behavioral and the family is listed as an exception (`redundant.EXCEPTIONS`).

## references

muller_2016 -> J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
takagi_1991 -> N. Takagi, T. Asada, S. Yajima, "Redundant CORDIC Methods with a Constant Scale Factor for Sine and Cosine Computation", IEEE Transactions on Computers, vol. 40, no. 9, pp. 989-995, 1991
ercegovac_lang_1990 -> Ercegovac, Lang, "Redundant and On-Line CORDIC: Application to Matrix Triangularization and SVD", IEEE Transactions on Computers, 1990
meher_2009 -> P. K. Meher, J. Valls, T.-B. Juang, K. Sridharan, K. Maharatna, "50 Years of CORDIC: Algorithms, Architectures, and Applications", IEEE Transactions on Circuits and Systems I, vol. 56, no. 9, pp. 1893-1907, 2009
noll_1991 -> Noll, "Carry-Save Architectures for High-Speed Digital Signal Processing", Journal of VLSI Signal Processing, 1991
