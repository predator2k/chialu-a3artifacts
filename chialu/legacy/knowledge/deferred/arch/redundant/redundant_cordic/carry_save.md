---
family: redundant_cordic
pin: {internal_representation: carry_save}
---
# carry_save

The carry-save CORDIC: coordinates and the remaining angle are kept
as sum and carry vectors, each microrotation adds or subtracts the
shifted operand with a carry-save adder and no carry propagation,
and the rotation direction is estimated from a few most significant
digits. The estimate can be wrong, so either the angle sequence is
replicated so that a later stage counterbalances the error with the
scale factor kept constant, or the direction set admits zero and the
scale factor is computed.

It is the pick for pipelined DSP rotators built from standard
carry-save adders: an 18-stage rotate-mode processor with 12
effective stages runs at 30 MHz worst case on 60 mm2 with 86,500
transistors in 1.5 um CMOS, replicating about every second angle
element when 3 or 4 leading digits are inspected. The Ercegovac-Lang
angle CORDIC uses the same representation with a one-fractional-bit
estimate and an estimated 4 to 6 speedup over the carry-propagate
recurrence. Borrow-save wins where the sign must be read from the
first non-zero digit without assimilation.

The iterations run over cycles here; the family is an exception (`redundant.EXCEPTIONS`).

## references

noll_1991 -> Noll, "Carry-Save Architectures for High-Speed Digital Signal Processing", Journal of VLSI Signal Processing, 1991
ercegovac_lang_1990 -> Ercegovac, Lang, "Redundant and On-Line CORDIC: Application to Matrix Triangularization and SVD", IEEE Transactions on Computers, 1990
meher_2009 -> P. K. Meher, J. Valls, T.-B. Juang, K. Sridharan, K. Maharatna, "50 Years of CORDIC: Algorithms, Architectures, and Applications", IEEE Transactions on Circuits and Systems I, vol. 56, no. 9, pp. 1893-1907, 2009
