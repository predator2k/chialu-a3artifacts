---
family: generalized_signed_digit
pin: {final_conversion: on_the_fly}
---
# on_the_fly

Digit-by-digit conversion of a most-significant-first signed-digit
stream: two conditional forms are kept, Q[k] and QM[k] = Q[k] - r^-k,
and each incoming digit selects one of them and appends a digit by
concatenation and a conditional register load, so no carry or borrow
ever propagates and the final conventional result is Q[m]. The
radix-r form needs one one-digit adder for r - |p| - 1; rounding
adds a third form QP[k] = Q[k] + r^-k and selects among the three
after one extra digit.

The step costs about two logic levels plus a register shift or load
and is independent of the working precision, which makes it the pick
for division, square root and online units whose digits are produced
serially most-significant-first; it can be built as a sequential
register pair or a combinational linear array. Its limits are the
required serial order and normalized input, and the absence of a
conventional remainder, for which a carry-propagate adder is still
needed; the cpa variant is the alternative when the whole result is
available at once.

The library's signed-digit adder realizes this conversion as the unrolled Q / QM selection chain from the most significant digit down (`chialu/targets/rtl/families/redundant.py`).

## references

ercegovac_1987 -> Ercegovac, Lang, "On-the-Fly Conversion of Redundant into Conventional Representations", IEEE Transactions on Computers, 1987
ercegovac_1992 -> Ercegovac, Lang, "On-the-Fly Rounding", IEEE Transactions on Computers, 1992
ercegovac_2004 -> M. D. Ercegovac and T. Lang, "Digital Arithmetic", Morgan Kaufmann, 2004
chen2018 -> L. Chen, J. Han, W. Liu, P. Montuschi, F. Lombardi, "Design, Evaluation and Application of Approximate High-Radix Dividers", IEEE Transactions on Multi-Scale Computing Systems, vol. 4, no. 3, pp. 299-312, 2018
