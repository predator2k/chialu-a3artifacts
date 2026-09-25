---
family: multipath_fma
pin: {path_select_criterion: exponent_difference}
---
# exponent_difference

The path is chosen by the exponent difference d between product and
addend alone: a detector routes the operation to a near path when d
lies in a small window, {-2, -1, 0, 1} in the split-path FPMAC,
where the addend shifts by at most two bits and enters the
multiplier's CSA tree directly, and to a far path for every other d,
where alignment and normalization take their full range. Both paths
end in one shared addition-and-rounding unit, and the inactive path
can be clock- or power-gated.

Against cancellation_estimate and both, which route on the predicted
cancellation, the exponent difference is known before the multiply
finishes, so early selection deactivates the unused path and, in
Seidel's five-case design with two shared major paths, lets faster
cases return early in a variable-latency unit. Its limit is that
close effective subtraction must still be recognised inside the near
window: Seidel adds an effective-subtraction predicate to case 3, and
Quinnell folds the operation sign into the criterion. The two-path
FPMAC reports 72 critical-path logic levels against 84 for Power6 and
76 for Lang's design, with up to about 20% of the logic gateable, and
Seidel estimates 62 Nd2 against 87 for the IBM reference. In the ADIR
grammar it is `family: multipath_fma` with
`pin: {path_select_criterion: exponent_difference}`.

The window's width follows from what the criterion must cover. A
quadruple-precision two-path unit takes the close path for effective
subtraction at d of -1, 0 or 1, and at -2 when the multiplication
overflows, and SNAP splits its six cases at a difference of 2 for the
same reason, since summing the carry-save product's two vectors may
overflow.

The library realizes this choice as a pin of the generated multipath_fma module (`chialu/targets/rtl/families/dot.py`); the family card names the construction.

## references

srinivasan_2013 -> S. Srinivasan, K. Bhudiya, R. Ramanarayanan, P. S. Babu, T. Jacob, S. Mathew, R. Krishnamurthy, V. Erraguntla, "Split-Path Fused Floating Point Multiply Accumulate (FPMAC)", ARITH-21, pp. 17-24, 2013
seidel_2003 -> P.-M. Seidel, "Multiple Path IEEE Floating-Point Fused Multiply-Add", IEEE MWSCAS, 2003
quinnell_2007 -> E. Quinnell, E. E. Swartzlander, C. Lemonds, "Floating-Point Fused Multiply-Add Architectures", 41st Asilomar Conference on Signals, Systems and Computers, 2007
manolopoulos_2016 -> K. Manolopoulos, D. Reisis, V. A. Chouliaras, "An Efficient Multiple Precision Floating-Point Multiply-Add Fused Unit", Microelectronics Journal, vol. 49, 2016
quach_1991 -> N. Quach, M. Flynn, "Suggestions for Implementing a Fast IEEE Multiply-Add-Fused Instruction", Stanford CSL-TR-91-483, 1991
