---
family: multi_term_fused_dot
pin: {cancellation_handling: detect_and_bypass_smallest_operand}
---
# detect_and_bypass_smallest_operand

Catastrophic cancellation among the larger operands is detected from the
internal sum and the exponent differences, and when the larger operands
cancel and the smallest operand was only partly retained in the
alignment window, the smallest operand with its sticky information is
forwarded as the result instead of the internal sum. The detector also
selects the proper result exponent, so the normalization shift never has
to recover bits that the window discarded.

The bypass is what keeps a bounded internal precision correctly rounded:
FPADD3 uses p = 2f + 5 internal bits and still delivers the perfectly
rounded result, defined as infinite-precision addition followed by one
rounding, because the only case where the window loses needed bits is
the one the detector routes around. FADDn applies the same rule when all
larger operands cancel and the sticky bit shows that the smallest
operand was incompletely retained. The combinations of sticky resolution
and cancellation grow rapidly with the operand count, which the FPADDn
paper gives as the reason practical fused adders stop at four inputs.
Without the bypass the window must span the exponent range, which is the
long-adder alternative, or the contract weakens to faithful rounding.

The library realizes this choice as a pin of the generated multi_term_fused_dot module (`chialu/targets/rtl/families/dot.py`); the family card names the construction.

## references

tenca_2009 -> A. F. Tenca, "Multi-Operand Floating-Point Addition", ARITH-19, pp. 161-168, 2009
tao_2013 -> T. Yao, D. Gao, X. Fan, J. Nurmi, "Correctly Rounded Architectures for Floating-Point Multi-Operand Addition and Dot-Product Computation", IEEE ASAP, pp. 346-355, 2013
