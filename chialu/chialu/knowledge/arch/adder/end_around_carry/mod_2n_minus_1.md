---
family: end_around_carry
pin: {modulus: mod_2n_minus_1}
---
# mod_2n_minus_1

The ones'-complement adder: the carry out of the most significant
position, whose weight 2^n has residue +1, returns to the least
significant position as a direct, uninverted increment. The sum
2^n-1 itself is all ones and must also reduce to zero, so the adder
either keeps a double representation of zero, which is tested as zero
by branch logic, or adds a group-propagate condition that forces the
single-zero form.

This modulus is the pick for ones'-complement significand datapaths,
for the minus-one channels of an RNS base, for checksums and for
residue generators and predictors of the form 2^a-1, where the mod-15
checker of the STAR computer is the earliest instance and 16-nm GPU
residue predictors the latest. It is cheaper than the
mod_2n_plus_1_diminished_one sibling because the feedback needs no
inversion, no representation converters and no false-zero check; the
cost it does carry is the second traversal, which a cyclic prefix
level absorbs, and the dual zero, which either the software or a
single-zero correction absorbs.

## references

richards_1955 -> Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
zimmermann1999 -> R. Zimmermann, "Efficient VLSI Implementation of Modulo (2^n +/- 1) Addition and Multiplication", 14th IEEE Symposium on Computer Arithmetic (ARITH-14), 1999
burgess2002 -> N. Burgess, "The Flagged Prefix Adder and its Applications in Integer Arithmetic", Journal of VLSI Signal Processing, vol. 31, no. 3, pp. 263-271, 2002.
avizienis_gilley_1971 -> A. Avizienis, G. C. Gilley, F. P. Mathur, D. A. Rennels, J. A. Rohr, D. K. Rubin, "The STAR (Self-Testing And Repairing) Computer: An Investigation of the Theory and Practice of Fault-Tolerant Computer Design", IEEE Transactions on Computers, vol. C-20, no. 11, 1971
sullivan_2018 -> M. B. Sullivan, S. K. S. Hari, B. Zimmer, T. Tsai, S. W. Keckler, "SwapCodes: Error Codes for Hardware-Software Cooperative GPU Pipeline Error Detection", Proc. MICRO-51, pp. 762-774, 2018
