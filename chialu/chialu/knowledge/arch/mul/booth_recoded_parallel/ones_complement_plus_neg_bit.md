---
family: booth_recoded_parallel
pin: {negative_pp_encoding: ones_complement_plus_neg_bit}
---
# ones_complement_plus_neg_bit

A negative Booth digit selects the bitwise complement of the
multiplicand or of its one-bit shift and injects a separate 1, the Neg
or hot-one bit, at the row's least-significant position, usually
appended to the next row, so the two's complement is completed inside
the reduction tree rather than by a carry-propagating negation. The
leading ones that the complemented rows would extend are summed into
fixed constants that conditional S terms clear for positive rows.

The recoding preserves exact two's-complement arithmetic with n(n+1)/2
partial-product bits, and sign propagation turns the trapezoidal
matrix into a rectangular carry-save array (nicolaidis_duarte_1999).
The correction digits that negative digits introduce are absorbed by
the pseudo-adder tree ahead of the single carry-propagating addition
(wallace1964). The Neg bit costs a term: ignoring the highest row's
Neg term regularizes the array and saves one reduction stage in an
approximate design (liu2017), a vector recoder appends the hot ones
seln1/seln2 to the next row and restarts recoding with zeros at lane
boundaries (danysh_2005), and the summed sign-extension construction
is exactly equivalent to explicit leading-one strings (bewick1994).
A 53 by 53 array carries the hot one as b'01' concatenated to the low
end of the row two positions to its left, and makes its last row always
positive by concatenating a zero to the multiplier's most significant
bit; the half-size version of the same array, which takes two passes,
saves the hot one of the last first-pass row and re-injects it with the
first row of the second pass (jessani_1998).
The encoding is the default of the Booth 2 tree designs;
twos_complement_row is the pick only where a carry-save path already
offers free-carry inputs to a full row.

## references

nicolaidis_duarte_1999 -> M. Nicolaidis, R. O. Duarte, "Fault-Secure Parity Prediction Booth Multipliers", IEEE Design & Test of Computers, vol. 16, no. 3, pp. 90-101, 1999
wallace1964 -> Wallace, "A Suggestion for a Fast Multiplier", IEEE Transactions on Electronic Computers, 1964
liu2017 -> W. Liu, L. Qian, C. Wang, H. Jiang, J. Han, F. Lombardi, "Design of Approximate Radix-4 Booth Multipliers for Error-Tolerant Computing", IEEE Transactions on Computers, vol. 66, no. 8, pp. 1435-1441, 2017
danysh_2005 -> A. Danysh, D. Tan, "Architecture and Implementation of a Vector/SIMD Multiply-Accumulate Unit", IEEE Transactions on Computers, vol. 54, no. 3, pp. 284-293, 2005
bewick1994 -> G. W. Bewick, "Fast Multiplication: Algorithms and Implementation", PhD dissertation, Stanford University, CSL-TR-94-617, 1994
jessani_1998 -> R. M. Jessani, M. Putrino, "Comparison of Single- and Dual-Pass Multiply-Add Fused Floating-Point Units", IEEE Transactions on Computers, vol. 47, no. 9, 1998
