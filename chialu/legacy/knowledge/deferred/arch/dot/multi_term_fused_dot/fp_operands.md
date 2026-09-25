---
family: multi_term_fused_dot
pin: {term_source: fp_operands}
---
# fp_operands

Three or more normalized floating-point operands enter the fused unit
directly: the multiplier slot is empty, the significands are aligned
against one another, reduced in carry-save form, assimilated by one
adder and normalized and rounded once under all five IEEE rounding
modes. The three-operand form reuses the three-input register-file read
provisioned for the FMA, and the same alignment, sign-handling and LZA
structure serves the product-fed unit.

The fused three-term adder replaces a network of two delay-optimized
floating-point adders: at 45 nm the fp32 and fp64 designs take about 15
to 20 percent less area and power and 35 percent less latency than the
discrete pair, and the textbook prices the three-input addition at about
one third of an FMA's area. The fused unit rounds once rather than
twice, so the result is the correctly rounded sum of the three inputs.
FPADD3 at 90 nm reaches 7 percent less area than the two-adder network
under a tight timing constraint, while the network stays smaller under
relaxed timing. Sticky-bit and cancellation cases grow rapidly beyond
four inputs, so FADD4 and FADD8 are the largest implemented sizes and a
network of two-input adders takes over at larger N or where relaxed
timing and lower accuracy are acceptable.

The library realizes this choice as a pin of the generated multi_term_fused_dot module (`chialu/targets/rtl/families/dot.py`); the family card names the construction.

## references

sohn_2014 -> J. Sohn, E. E. Swartzlander, "A Fused Floating-Point Three-Term Adder", IEEE TCAS-I, vol. 61, no. 10, pp. 2842-2850, 2014
muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
tenca_2009 -> A. F. Tenca, "Multi-Operand Floating-Point Addition", ARITH-19, pp. 161-168, 2009
tao_2013 -> T. Yao, D. Gao, X. Fan, J. Nurmi, "Correctly Rounded Architectures for Floating-Point Multi-Operand Addition and Dot-Product Computation", IEEE ASAP, pp. 346-355, 2013
