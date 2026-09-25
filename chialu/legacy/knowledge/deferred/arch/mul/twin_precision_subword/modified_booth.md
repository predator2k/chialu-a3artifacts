---
family: twin_precision_subword
pin: {base_scheme: modified_booth}
---
# modified_booth

Twin precision over a radix-4 Booth-recoded matrix: the recoding and
sign-extension patterns change with the mode, two extra inputs enter
the reduction tree, and mode-dependent multiplicand multiplexing and
masking rearrange the partial products so the lanes do not overlap;
carry kills at the lane boundaries segment the common tree and final
adder, so one carry-killed structure serves every mode without
mode-specific subtrees or a final result multiplexer.

The recoded matrix is smaller, so the area overhead of adding
subword modes is about 3% at 32 bits in 65 nm against 11% for
baugh_wooley, and shared segmentation scales better than a shared
subtree as width and mode count grow. The costs are more complex mode
control and worse delay and power than the Baugh-Wooley form, and
the zero-region mapping that avoids boundary carry logic altogether
is unavailable because it applies only to non-Booth matrices. It is
the pick when the full-width multiplier is Booth-recoded already, as
in a vector MAC with 8- to 64-bit lanes, and area rather than mode
switching cost dominates.

## references

sjalander2009 -> M. Sjalander, P. Larsson-Edefors, "Multiplication Acceleration Through Twin Precision", IEEE Transactions on Very Large Scale Integration (VLSI) Systems, vol. 17, no. 9, pp. 1233-1246, 2009
danysh_2005 -> A. Danysh, D. Tan, "Architecture and Implementation of a Vector/SIMD Multiply-Accumulate Unit", IEEE Transactions on Computers, vol. 54, no. 3, pp. 284-293, 2005
krithivasan2003 -> S. Krithivasan, M. J. Schulte, "Multiplier Architectures for Media Processing", 37th Asilomar Conference on Signals, Systems and Computers, pp. 2193-2197, 2003
